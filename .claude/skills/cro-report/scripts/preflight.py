"""Check that a site has what the report needs before collecting data.

Usage: preflight.py --site SLUG [--start YYYY-MM-DD --end YYYY-MM-DD]

Prints JSON: {ok, blocking:[...], warnings:[...], action}
  action = "run_cro_setup"  → CRO engine / GA4 definitions missing: run /cro-setup
           "fix_access"     → OAuth/profile problem
           null             → ready
"""
from __future__ import annotations

import argparse
import json
import urllib.request

from common import (load_profile, default_period, parse_date, ga4_client, ga4_admin, out)

REQUIRED_DIMS = ["cro_conversion_id", "cro_submission_page", "cro_landing_page",
                 "cro_detection", "cro_fail_reason", "cro_trigger_type"]
OPTIONAL_DIMS = {"contact_market": "nhãn thị trường cho call / email",
                 "contact_target": "số điện thoại / email được bấm"}
CRO_EVENTS = ["conversion_success", "conversion_attempt_failed", "form_interaction"]


def check_container(profile: dict, blocking: list, warnings: list) -> None:
    gid = profile.get("gtm_public_id")
    if not gid:
        blocking.append("Hồ sơ thiếu gtm_public_id (GTM-XXXX)")
        return
    try:
        import ssl, certifi
        ctx = ssl.create_default_context(cafile=certifi.where())
        js = urllib.request.urlopen(f"https://www.googletagmanager.com/gtm.js?id={gid}", timeout=30,
                                    context=ctx).read().decode("utf-8", "ignore")
    except Exception as e:  # noqa: BLE001
        warnings.append(f"Không tải được container {gid} để kiểm tra: {e}")
        return
    if "__CRO_ENGINE_LOADED__" not in js:
        blocking.append(f"Container đang live ({gid}) chưa có tag [CRO] Journey Tracker — CRO engine chưa được publish")
        return
    if profile.get("hostnames") and "ALLOWED_HOSTS" not in js:
        warnings.append("CRO engine đang live chưa có bộ lọc hostname — conversion từ localhost/staging có thể lẫn vào số liệu "
                        "(báo cáo vẫn lọc theo hostName khi truy vấn)")
    if 'pagePath:\\"' in js or "pagePath:'" in js:
        warnings.append("CRO engine đang live còn giới hạn pagePath — form nằm ngoài trang liên hệ có thể không được đo")


def check_ga4(profile: dict, start, end, blocking: list, warnings: list, info: dict) -> None:
    prop = f"properties/{profile['ga4_property_id']}"
    admin = ga4_admin(profile)
    dims = {d.parameter_name for d in admin.list_custom_dimensions(parent=prop)}
    miss = [d for d in REQUIRED_DIMS if d not in dims]
    if miss:
        blocking.append("GA4 thiếu custom dimension CRO: " + ", ".join(miss))
    for d, why in OPTIONAL_DIMS.items():
        if d not in dims:
            warnings.append(f"GA4 chưa có dimension {d} ({why}) — bảng hotline/email chỉ chia được theo quốc gia người bấm")
    try:
        keys = {k.event_name for k in admin.list_key_events(parent=prop)}
        if "conversion_success" not in keys:
            warnings.append("conversion_success chưa được đánh dấu Key event trong GA4")
    except Exception as e:  # noqa: BLE001
        warnings.append(f"Không đọc được Key events: {e}")

    from google.analytics.data_v1beta.types import (RunReportRequest, Dimension, Metric, DateRange,
                                                    FilterExpression, Filter)
    c = ga4_client(profile)
    req = RunReportRequest(
        property=prop, dimensions=[Dimension(name="eventName"), Dimension(name="date")],
        metrics=[Metric(name="eventCount")],
        date_ranges=[DateRange(start_date=f"{start:%Y-%m-%d}", end_date=f"{end:%Y-%m-%d}")],
        dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
                                                        in_list_filter=Filter.InListFilter(values=CRO_EVENTS))),
        limit=10000)
    rows = c.run_report(req).rows
    by_ev: dict[str, int] = {}
    first = None
    for r in rows:
        ev, d = r.dimension_values[0].value, r.dimension_values[1].value
        by_ev[ev] = by_ev.get(ev, 0) + int(r.metric_values[0].value)
        first = d if first is None or d < first else first
    info["cro_events_in_period"] = by_ev
    if not by_ev:
        blocking.append(f"Không có sự kiện CRO nào ({', '.join(CRO_EVENTS)}) trong kỳ {start}–{end}")
    elif first and first > f"{start:%Y%m%d}":
        warnings.append(f"Sự kiện CRO chỉ bắt đầu có từ {first[6:]}/{first[4:6]}/{first[:4]} — số enquiry đầu kỳ bị thiếu")

    want = [e["event"] for e in profile.get("interest_events", [])]
    if want:
        req = RunReportRequest(
            property=prop, dimensions=[Dimension(name="eventName")], metrics=[Metric(name="eventCount")],
            date_ranges=[DateRange(start_date=f"{start:%Y-%m-%d}", end_date=f"{end:%Y-%m-%d}")],
            dimension_filter=FilterExpression(filter=Filter(field_name="eventName",
                                                            in_list_filter=Filter.InListFilter(values=want))))
        seen = {r.dimension_values[0].value for r in c.run_report(req).rows}
        missing = [e for e in want if e not in seen]
        if missing:
            warnings.append("Sự kiện quan tâm không có dữ liệu trong kỳ (sẽ hiện 0): " + ", ".join(missing))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--start")
    ap.add_argument("--end")
    a = ap.parse_args()
    profile = load_profile(a.site)
    start, end = (parse_date(a.start), parse_date(a.end)) if a.start else default_period(profile)

    blocking, warnings, info = [], [], {"period": [str(start), str(end)]}
    for k in ("ga4_property_id", "gsc_site_url", "seo_analyst_profile"):
        if not profile.get(k):
            blocking.append(f"Hồ sơ thiếu {k}")
    if blocking:
        out({"ok": False, "blocking": blocking, "warnings": warnings, "action": "fix_access", **info}, 1)

    try:
        check_ga4(profile, start, end, blocking, warnings, info)
    except Exception as e:  # noqa: BLE001
        out({"ok": False, "blocking": [f"Không truy cập được GA4 bằng profile seo-analyst "
                                       f"'{profile['seo_analyst_profile']}': {e}"],
             "warnings": warnings, "action": "fix_access", **info}, 1)
    check_container(profile, blocking, warnings)

    action = "run_cro_setup" if blocking else None
    out({"ok": not blocking, "blocking": blocking, "warnings": warnings, "action": action, **info},
        1 if blocking else 0)


if __name__ == "__main__":
    main()
