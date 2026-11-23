"""Pull every GA4 / Search Console number the report needs into raw.json.

Usage: collect.py --site SLUG [--start YYYY-MM-DD --end YYYY-MM-DD]
Writes reports/<slug>/<start>-<end>/raw.json and prints its path.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta

from google.analytics.data_v1beta.types import (RunReportRequest, Dimension, Metric, DateRange,
                                                FilterExpression, FilterExpressionList, Filter)

from common import (SKILL_DIR, real_conversions, conv_landing, load_profile, default_period, previous_period, parse_date, period_dir,
                    ga4_client, gsc_service, dump, out)


# ── GA4 filter builders ──────────────────────────────────────────────────────

def f_in(field, values):
    return FilterExpression(filter=Filter(field_name=field, in_list_filter=Filter.InListFilter(values=list(values))))


def f_eq(field, value):
    return FilterExpression(filter=Filter(field_name=field, string_filter=Filter.StringFilter(
        match_type=Filter.StringFilter.MatchType.EXACT, value=value)))


def f_re(field, pattern):
    return FilterExpression(filter=Filter(field_name=field, string_filter=Filter.StringFilter(
        match_type=Filter.StringFilter.MatchType.FULL_REGEXP, value=pattern, case_sensitive=False)))


def f_and(*fs):
    fs = [f for f in fs if f is not None]
    if not fs:
        return None
    return fs[0] if len(fs) == 1 else FilterExpression(and_group=FilterExpressionList(expressions=fs))


def f_not(f):
    return FilterExpression(not_expression=f)


class GA4:
    def __init__(self, profile):
        self.c = ga4_client(profile)
        self.prop = f"properties/{profile['ga4_property_id']}"

    def q(self, dims, mets, start, end, flt=None, limit=100000, order_metric=None):
        req = RunReportRequest(property=self.prop, dimensions=[Dimension(name=d) for d in dims],
                               metrics=[Metric(name=m) for m in mets],
                               date_ranges=[DateRange(start_date=f"{start:%Y-%m-%d}", end_date=f"{end:%Y-%m-%d}")],
                               limit=limit)
        if flt is not None:
            req.dimension_filter = flt
        rows = []
        for r in self.c.run_report(req).rows:
            row = {d: v.value for d, v in zip(dims, r.dimension_values)}
            for m, v in zip(mets, r.metric_values):
                x = float(v.value)
                row[m] = int(x) if x.is_integer() else x
            rows.append(row)
        return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    P = load_profile(a.site)
    start, end = (parse_date(a.start), parse_date(a.end)) if a.start else default_period(P)
    pstart, pend = previous_period(start, end, P.get("period", {}).get("compare_days"))
    g = GA4(P)
    hosts = P.get("hostnames") or []
    host_f = f_in("hostName", hosts) if hosts else None
    bot = P.get("bot_landing_pages") or []
    nobot = f_not(f_in("landingPage", bot)) if bot else None
    contact = P["contact_path"]
    ev = lambda name: f_eq("eventName", name)  # noqa: E731
    periods = {"cur": (start, end), "prev": (pstart, pend)}
    R: dict = {"site": P["slug"], "period": {"start": start, "end": end, "pstart": pstart, "pend": pend}}

    for k, (s, e) in periods.items():
        D = R[k] = {}
        D["totals"] = g.q([], ["sessions", "totalUsers", "newUsers", "screenPageViews", "engagementRate",
                               "averageSessionDuration", "engagedSessions"], s, e)[0]
        D["totals_nobot"] = g.q([], ["sessions", "engagementRate", "engagedSessions"], s, e, nobot)[0] if nobot else D["totals"]
        D["bot_sessions"] = sum(r["sessions"] for r in g.q(["landingPage"], ["sessions"], s, e, f_in("landingPage", bot))) if bot else 0
        D["conv"] = g.q(["dateHourMinute", "country", "landingPage", "customEvent:cro_landing_page", "pagePath", "hostName"],
                        ["eventCount"], s, e, ev("conversion_success"))
        D["attempt_fail"] = sum(r["eventCount"] for r in g.q(["eventName"], ["eventCount"], s, e,
                                                               f_and(ev("conversion_attempt_failed"), host_f)))
        evs = [x["event"] for x in P.get("interest_events", [])]
        D["interest"] = g.q(["eventName"], ["eventCount", "sessions"], s, e, f_and(f_in("eventName", evs), host_f)) if evs else []
        D["country"] = g.q(["country"], ["sessions", "engagedSessions"], s, e, nobot)
        D["landing"] = g.q(["landingPage"], ["sessions", "engagedSessions", "screenPageViews", "bounceRate"], s, e, nobot)
        D["landing_to_contact"] = g.q(["landingPage"], ["sessions"], s, e, f_and(f_eq("pagePath", contact), nobot))
        D["contact_sessions"] = sum(r["sessions"] for r in g.q(["pagePath"], ["sessions"], s, e,
                                                               f_and(f_eq("pagePath", contact), nobot)))
        D["ai"] = g.q(["sessionSource"], ["sessions", "engagedSessions", "averageSessionDuration"], s, e,
                      f_re("sessionSource", f".*({P['ai_sources_regex']}).*"))

    C = R["cur"]
    C["fail_events"] = g.q(["dateHourMinute", "country", "pagePath", "hostName", "customEvent:cro_fail_reason"],
                           ["eventCount"], start, end, f_and(ev("conversion_attempt_failed"), host_f))
    C["home_next"] = g.q(["pagePath"], ["sessions"], start, end, f_eq("landingPage", P.get("home_path", "/")))
    C["ai_landing"] = g.q(["landingPage", "sessionSource"], ["sessions", "engagedSessions", "averageSessionDuration"],
                          start, end, f_re("sessionSource", f".*({P['ai_sources_regex']}).*"))
    C["ai_enquiry"] = g.q(["sessionSource"], ["eventCount"], start, end,
                          f_and(ev("conversion_success"), host_f, f_re("sessionSource", f".*({P['ai_sources_regex']}).*")))
    # interest-event breakdowns (labels, country, page)
    C["interest_detail"] = {}
    for x in P.get("interest_events", []):
        d = {"country": g.q(["country"], ["eventCount"], start, end, f_and(ev(x["event"]), host_f))}
        if x.get("breakdown"):
            try:
                d["label"] = g.q([f"customEvent:{x['breakdown']}"], ["eventCount"], start, end, f_and(ev(x["event"]), host_f))
            except Exception as e:  # noqa: BLE001  dimension not registered
                d["label_error"] = str(e)[:160]
        if x["event"] == P.get("cta_event"):
            d["page"] = g.q(["pagePath"], ["eventCount"], start, end, f_and(ev(x["event"]), host_f))
        C["interest_detail"][x["event"]] = d
    # blog inventory: every blog URL with a view in the last 12 months
    bp = P.get("blog_prefix")
    if bp:
        C["blog_inventory"] = [r["pagePath"] for r in g.q(["pagePath"], ["screenPageViews"], end - timedelta(days=365), end,
                                                          f_re("pagePath", re.escape(bp) + ".+"))]
    # enquiries since quarter start by landing page (blog share)
    qs = date(end.year, 3 * ((end.month - 1) // 3) + 1, 1)
    C["quarter_start"] = qs
    C["conv_quarter"] = g.q(["dateHourMinute", "country", "landingPage", "customEvent:cro_landing_page", "pagePath", "hostName"],
                            ["eventCount"], qs, end, ev("conversion_success"))
    # per-country landing sessions for countries that produced enquiries
    real = real_conversions(P, C["conv"])
    enq_countries = sorted({r["country"] for r in real})
    for k, (s, e) in periods.items():
        R[k]["country_landing"] = g.q(["country", "landingPage"], ["sessions"], s, e,
                                      f_and(f_in("country", enq_countries), nobot)) if enq_countries else []
    cid = g.q(["country", "countryId"], ["sessions"], start, end, f_in("country", enq_countries)) if enq_countries else []
    iso = json.loads((SKILL_DIR / "assets/iso2_to_iso3.json").read_text())
    C["country_iso3"] = {r["country"]: iso.get(r["countryId"], "") for r in cid}

    # ── Search Console ──
    gsc = gsc_service(P)
    site = P["gsc_site_url"]
    base = site.rstrip("/") if site.startswith("http") else "https://" + P["domain"]

    def gq(body):
        return gsc.searchanalytics().query(siteUrl=site, body=body).execute().get("rows", [])

    sd, ed = f"{start:%Y-%m-%d}", f"{end:%Y-%m-%d}"
    enq_pages = sorted({conv_landing(r) for r in real} - {"(not set)"})
    C["gsc_page_queries"] = {}
    for p in enq_pages:
        rows = gq({"startDate": sd, "endDate": ed, "dimensions": ["query"], "rowLimit": 50,
                   "dimensionFilterGroups": [{"filters": [{"dimension": "page", "operator": "equals",
                                                           "expression": base + p}]}]})
        C["gsc_page_queries"][p] = [{"query": r["keys"][0], "clicks": r["clicks"], "impressions": r["impressions"],
                                     "position": r["position"]} for r in rows]
    C["gsc_country_page_query"] = {}
    for cname, c3 in C["country_iso3"].items():
        if not c3:
            continue
        rows = gq({"startDate": sd, "endDate": ed, "dimensions": ["page", "query"], "rowLimit": 5000,
                   "dimensionFilterGroups": [{"filters": [{"dimension": "country", "operator": "equals", "expression": c3}]}]})
        C["gsc_country_page_query"][cname] = [{"page": r["keys"][0].replace(base, "") or "/", "query": r["keys"][1],
                                               "clicks": r["clicks"], "impressions": r["impressions"]} for r in rows]

    d = period_dir(P["slug"], start, end)
    dump(d / "raw.json", R)
    out({"ok": True, "raw": str(d / "raw.json"), "period": [start, end], "previous": [pstart, pend]})


if __name__ == "__main__":
    main()
