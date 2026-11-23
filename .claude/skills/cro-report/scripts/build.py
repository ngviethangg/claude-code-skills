"""Turn raw.json (+ CRM + competitors.json) into report.json: sections of data blocks and
narrative slots that Claude fills through narrative.json.

Usage: build.py --site SLUG --start YYYY-MM-DD --end YYYY-MM-DD [--crm PATH]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date

import crm as crm_mod
from common import (real_conversions, conv_landing, load_profile, crm_enabled, parse_date, period_dir, fint, fdec, fpct, delta, ratio, esc,
                    vn_date, short_range, month_label, classify, dump, out)

VI_COUNTRY = {"Vietnam": "Việt Nam", "United States": "Hoa Kỳ", "India": "Ấn Độ", "Japan": "Nhật Bản", "France": "Pháp",
              "Germany": "Đức", "United Kingdom": "Anh", "Australia": "Úc", "Singapore": "Singapore",
              "South Korea": "Hàn Quốc", "China": "Trung Quốc", "United Arab Emirates": "UAE", "Thailand": "Thái Lan",
              "Malaysia": "Malaysia", "Indonesia": "Indonesia", "Philippines": "Philippines", "Canada": "Canada",
              "Netherlands": "Hà Lan", "Hong Kong": "Hồng Kông", "Taiwan": "Đài Loan", "Pakistan": "Pakistan",
              "Saudi Arabia": "Ả Rập Xê Út", "Italy": "Ý", "Spain": "Tây Ban Nha", "Switzerland": "Thuỵ Sĩ"}


# ── block helpers ────────────────────────────────────────────────────────────

def cell(v, cls="", **kw):
    d = {"v": v, "cls": cls}
    d.update(kw)
    return d


def n(v, bold=False, cls=""):
    s = fint(v)
    return cell(f"<b>{s}</b>" if bold and v else s, ("n " + cls).strip())


def dl(cur, prev):
    t, c = delta(cur, prev)
    return cell(t, ("n " + c).strip())


def table(caption, sub, cols, rows, min_w=640, row_cls=None, bid=None):
    return {"type": "table", "id": bid, "caption": caption, "sub": sub, "min": min_w,
            "cols": [c if isinstance(c, dict) else {"h": c} for c in cols], "rows": rows, "row_cls": row_cls or []}


def slot(sid, kind, hint, facts=None, title=None):
    return {"type": "slot", "id": sid, "kind": kind, "hint": hint, "facts": facts or {}, "title": title}


def warn(title, items):
    return {"type": "warn", "title": title, "items": items}


def h3(text):
    return {"type": "h3", "text": text}


def code(p):
    return f"<code>{esc(p)}</code>"


def nh(n_):  # numeric header
    return {"h": n_, "cls": "n"}


# ── aggregation helpers ──────────────────────────────────────────────────────

def by(rows, key, metric):
    d = defaultdict(float)
    for r in rows:
        d[r[key]] += r[metric]
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--crm", help="CSV path (overrides profile)")
    a = ap.parse_args()
    P = load_profile(a.site)
    start, end = parse_date(a.start), parse_date(a.end)
    d = period_dir(P["slug"], start, end)
    R = json.loads((d / "raw.json").read_text())
    C, V = R["cur"], R["prev"]
    pstart, pend = parse_date(R["period"]["pstart"]), parse_date(R["period"]["pend"])
    L, Lp = month_label(end), month_label(pend)
    has_crm = crm_enabled(P)
    contact = P["contact_path"]
    home = P.get("home_path", "/")
    excl = set(P.get("excluded_landing_pages", [])) | set(P.get("bot_landing_pages", []))
    client = P["client_name"]
    rng = short_range(start, end)

    conv_c, conv_p = real_conversions(P, C["conv"]), real_conversions(P, V["conv"])
    for r in conv_c + conv_p + C["conv_quarter"]:
        r["landing"] = conv_landing(r)
    enq_land = by(conv_c, "landing", "eventCount")
    enq_land_p = by(conv_p, "landing", "eventCount")
    enq_c = by(conv_c, "country", "eventCount")
    enq_cp = by(conv_p, "country", "eventCount")
    raw_c, raw_p = sum(r["eventCount"] for r in C["conv"]), sum(r["eventCount"] for r in V["conv"])
    excluded_c = sum(r["eventCount"] for r in C["conv"]) - sum(r["eventCount"] for r in conv_c)
    enq_total, enq_total_p = sum(enq_land.values()), sum(enq_land_p.values())
    land = {r["landingPage"]: r for r in C["landing"]}
    land_p = {r["landingPage"]: r for r in V["landing"]}
    T, Tp = C["totals"], V["totals"]
    TN, TNp = C["totals_nobot"], V["totals_nobot"]

    def ptype(path):
        return classify(path, P["page_types"], {"label": P.get("page_type_default", "Trang khác")})

    def topic(path):
        return classify(path, P.get("blog_topics", []), P.get("blog_topic_default", {"label": "Khác"}))

    def group(path):
        t = ptype(path)
        return f"Blog · {topic(path)['label'].replace('Khác (', '').rstrip(')')}" if t.get("blog") else t["label"]

    # ── CRM ──
    crm_cur = crm_prev = crm_ytd = None
    recon = None
    crm_last = None
    if has_crm:
        rows = crm_mod.load(P, a.crm)
        crm_cur = crm_mod.in_range(rows, start, end)
        crm_prev = crm_mod.in_range(rows, pstart, pend)
        crm_ytd = crm_mod.in_range(rows, date(end.year, 1, 1), end)
        crm_last = max((r["date"] for r in rows if r["date"] <= end), default=None)
        recon = crm_mod.reconcile(crm_cur, conv_c)

    sections = []

    # ═ ĐỌC TRƯỚC ═
    facts0 = {"period": f"{vn_date(start)}–{vn_date(end)}", "previous": f"{vn_date(pstart)}–{vn_date(pend)}",
              "labels": [L, Lp], "bot_rule": P.get("bot_note", ""), "bot_sessions": C["bot_sessions"],
              "enquiry_raw": raw_c, "enquiry_real": enq_total, "excluded_conversions": excluded_c,
              "exclusion_rules": P.get("exclude_conversions", []),
              "enquiry_by_host": dict(by(C["conv"], "hostName", "eventCount"))}
    if has_crm:
        facts0.update({"crm_last_date": vn_date(crm_last) if crm_last else None, "crm_in_period": len(crm_cur),
                       "crm_matched_cro": len(recon["matched"]), "crm_without_cro": recon["crm_only"],
                       "cro_without_crm": recon["cro_only"]})
    sections.append({"num": "ĐỌC TRƯỚC", "title": "Lưu ý khi đọc số liệu kỳ này", "blocks": [
        slot("read_first", "warn", "3–5 điều cần biết trước khi đọc: kỳ so sánh (ghi rõ hai nhãn kỳ), quy tắc lọc bot và số phiên bị loại, "
             "dữ liệu thiếu/muộn (CRM cập nhật tới ngày nào), chênh lệch CRM–CRO nếu có, các bảng chia nhỏ không cộng bằng tổng.",
             facts0, "Những điều cần biết trước")]})

    # ═ PHẦN 1 ═
    b = []
    rows = [
        ["Sessions", T["sessions"], Tp["sessions"]], ["Users", T["totalUsers"], Tp["totalUsers"]],
        ["New users", T["newUsers"], Tp["newUsers"]], ["Pageviews", T["screenPageViews"], Tp["screenPageViews"]],
        ["Sessions (đã loại bot)", TN["sessions"], TNp["sessions"]],
    ]
    trs = [[cell(r[0]), n(r[1]), n(r[2]), dl(r[1], r[2])] for r in rows]
    for lab, x, y in (("Engagement rate", T["engagementRate"], Tp["engagementRate"]),
                      ("Engagement rate (phiên đã loại bot)", TN["engagementRate"], TNp["engagementRate"])):
        trs.append([cell(lab), cell(fpct(x), "n"), cell(fpct(y), "n"), dl(x, y)])
    trs.append([cell("Avg. session duration"), cell(f"{fint(T['averageSessionDuration'])} s", "n"),
                cell(f"{fint(Tp['averageSessionDuration'])} s", "n"), dl(T["averageSessionDuration"], Tp["averageSessionDuration"])])
    trs.append([cell("Enquiry ghi nhận (thô)"), n(raw_c), n(raw_p), dl(raw_c, raw_p)])
    trs.append([cell("<b>Enquiry trên website</b> (đã loại nội bộ &amp; staging)"), n(enq_total, True), n(enq_total_p),
                dl(enq_total, enq_total_p)])
    if has_crm:
        trs.append([cell(f"<b>Enquiry thật từ CRM</b> ({esc(P['crm']['website_value'])})"), n(len(crm_cur), True),
                    n(len(crm_prev)), dl(len(crm_cur), len(crm_prev))])
    rc = [""] * (len(trs) - (2 if has_crm else 1)) + ["tot"] * (2 if has_crm else 1)
    b.append(table("1.1 Chỉ số tổng", f"GA4 · kỳ {rng} so với kỳ {short_range(pstart, pend)}",
                   ["Chỉ số", nh(f"{L.capitalize()}"), nh(Lp.capitalize()), nh("Δ")], trs, 600, rc, "t11"))

    ints = {r["eventName"]: r for r in C["interest"]}
    ints_p = {r["eventName"]: r for r in V["interest"]}
    trs = []
    for x in P.get("interest_events", []):
        c_, p_ = ints.get(x["event"], {}), ints_p.get(x["event"], {})
        trs.append([cell(f"<b>{x['label']}</b><br><span style=\"font-size:11.5px;color:var(--muted)\">{x.get('desc', '')}</span>"),
                    cell(code(x["event"])), n(c_.get("eventCount", 0)), n(c_.get("sessions", 0)), n(p_.get("eventCount", 0)),
                    dl(c_.get("eventCount", 0), p_.get("eventCount", 0))])
    if trs:
        hs = ", ".join(P.get("hostnames", [])) or P["domain"]
        b.append(table("1.2 Các hành động thể hiện quan tâm khác trên trang",
                       f"GA4 · chỉ tính trên <code>{esc(hs)}</code> · <b>không tính vào số enquiry</b>",
                       ["Nút / hành động", "Sự kiện GA4", nh(f"Lượt {L}"), nh("Phiên"), nh(Lp.capitalize()), nh("Δ")], trs, 700))
        b.append(slot("p1_interest_notes", "warn", "2–3 ý giải thích bảng hành động: hotline/email chia theo thị trường (contact_market) "
                      "hoặc theo quốc gia người bấm, nút CTA chính nằm ở những trang nào, nhắc rằng các lượt này không cộng vào enquiry.",
                      {"detail": C["interest_detail"]}, "Cần biết về bảng hành động"))

    mk = P["markets"]
    mgrp = lambda c: mk["map"].get(c, mk["default"])  # noqa: E731
    ms, msp, me, mep, meng = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
    for r in C["country"]:
        ms[mgrp(r["country"])] += r["sessions"]; meng[mgrp(r["country"])] += r["engagedSessions"]
    for r in V["country"]:
        msp[mgrp(r["country"])] += r["sessions"]
    for c_, v_ in enq_c.items():
        me[mgrp(c_)] += v_
    for c_, v_ in enq_cp.items():
        mep[mgrp(c_)] += v_
    order = [m for m in mk["order"] if m in ms or m in me] + sorted(set(ms) - set(mk["order"]))
    order.sort(key=lambda m: (-me.get(m, 0), -ms.get(m, 0)))
    trs = [[cell(m), n(ms[m]), n(msp[m]), dl(ms[m], msp[m]), cell(fpct(ratio(meng[m], ms[m])), "n"), n(me[m], True), n(mep[m]),
            cell(fpct(ratio(me[m], ms[m]), 2), "n")] for m in order]
    b.append(table("1.3 Traffic &amp; Enquiry theo thị trường", "GA4 · đã loại bot · cách gộp quốc gia theo hồ sơ website",
                   ["Thị trường", nh(f"Phiên {L}"), nh(Lp.capitalize()), nh("Δ"), nh("Tương tác"), nh("Enquiry"), nh(Lp.capitalize()), nh("CR")],
                   trs, 720, bid="t13"))

    top = [r for r in sorted(C["landing"], key=lambda r: -r["sessions"]) if r["landingPage"] not in excl][:13]
    trs = [[cell(esc(r["landingPage"]), "u"), n(land_p.get(r["landingPage"], {}).get("sessions", 0)), n(r["sessions"]),
            dl(r["sessions"], land_p.get(r["landingPage"], {}).get("sessions", 0)), n(enq_land.get(r["landingPage"], 0), True),
            cell(fpct(ratio(enq_land.get(r["landingPage"], 0), r["sessions"]), 2), "n")] for r in top]
    b.append(table("1.4 Traffic &amp; Enquiry theo Landing Page",
                   f"GA4 · 13 trang nhiều phiên nhất kỳ này · đã loại bot và {', '.join(code(x) for x in P.get('excluded_landing_pages', []))}",
                   ["Landing page", nh(f"Sessions {Lp}"), nh(f"Sessions {L}"), nh("Δ"), nh("Enquiry"), nh("CR")], trs, 640))

    bp = P.get("blog_prefix")
    topic_stats = {}
    if bp:
        tp = defaultdict(lambda: {"posts": 0, "s": 0, "sp": 0, "tech": False})
        for r in C["landing"]:
            if r["landingPage"].startswith(bp):
                t = topic(r["landingPage"]); x = tp[t["label"]]
                x["posts"] += 1; x["s"] += r["sessions"]; x["tech"] = bool(t.get("tech"))
        for r in V["landing"]:
            if r["landingPage"].startswith(bp):
                tp[topic(r["landingPage"])["label"]]["sp"] += r["sessions"]
        topic_stats = tp
        blog_total = sum(x["s"] for x in tp.values())
        shown = sorted([k for k, x in tp.items() if x["s"] > 50], key=lambda k: (tp[k]["tech"], -tp[k]["s"]))
        cols = ["Chủ đề / Ngành", nh("Bài có phiên"), nh(f"Sessions {Lp}"), nh(f"Sessions {L}"), nh("Δ")]
        crm_by_ind = defaultdict(int)
        if has_crm:
            cols.append({"h": f"Enquiry CRM<br><i>{L}</i>", "cls": "n"})
            for r in crm_cur:
                crm_by_ind[r["industry"]] += 1
        trs, rcls = [], []
        tech_rows = [k for k in shown if tp[k]["tech"]]
        for k in shown:
            x = tp[k]
            row = [cell(f"<b>{esc(k)}</b>"), n(x["posts"]), n(x["sp"]), n(x["s"]), dl(x["s"], x["sp"])]
            if has_crm:
                ind = P["crm"].get("topic_to_industry", {}).get(k, k)
                if x["tech"]:
                    if k == tech_rows[0]:
                        row.append(cell(f"<b>{crm_by_ind.get(P['crm'].get('tech_group'), 0)}</b><br>"
                                        f"<span style=\"font-size:11px\">chung cho {len(tech_rows)} dòng</span>", "n",
                                        rowspan=len(tech_rows)))
                else:
                    row.append(n(crm_by_ind.get(ind, 0)))
            trs.append(row); rcls.append("tech" if x["tech"] else "")
        tot = [cell("<b>TỔNG các chủ đề trong bảng</b>"), n(sum(tp[k]["posts"] for k in shown)), n(sum(tp[k]["sp"] for k in shown)),
               n(sum(tp[k]["s"] for k in shown)), dl(sum(tp[k]["s"] for k in shown), sum(tp[k]["sp"] for k in shown))]
        if has_crm:
            tot.append(n(len(crm_cur)))
        trs.append(tot); rcls.append("tot")
        b.append(table(f"1.5 Bài blog {code(bp + '*')} theo chủ đề",
                       f"GA4 · chủ đề có hơn 50 phiên trong {L} - {len(shown)} chủ đề, chiếm {fint(sum(tp[k]['s'] for k in shown))} trên "
                       f"{fint(blog_total)} phiên blog · dòng nền xanh là chủ đề công nghệ không gắn ngành"
                       + (" · cột enquiry lấy từ CRM theo <b>ngành của công ty khách hàng</b>" if has_crm else ""),
                       cols, trs, 700, rcls))
        cq = real_conversions(P, C["conv_quarter"])
        qblog = sum(r["eventCount"] for r in cq if conv_landing(r).startswith(bp))
        qall = sum(r["eventCount"] for r in cq)
        b.append(slot("p1_blog_notes", "warn", "2–4 ý đọc bảng chủ đề blog: chủ đề nào tăng/giảm mạnh, "
                      + ("cột enquiry CRM là ngành của khách hàng không phải enquiry do bài tạo ra, " if has_crm else "")
                      + "blog đóng góp trực tiếp bao nhiêu enquiry.",
                      {"enquiry_since_quarter_start": qall, "of_which_landing_on_blog": qblog,
                       "quarter_start": vn_date(parse_date(C["quarter_start"]))}, "Đọc bảng chủ đề blog thế nào"))
    b.append(slot("p1_conclusion", "note", "3–4 đoạn: traffic thật tăng/giảm, enquiry website (và CRM nếu có) so kỳ trước, "
                  "thị trường nổi bật, điểm bất thường.", {"see_tables": ["t11", "t13"]}, "Kết luận"))
    b.append(slot("p1_propose", "propose", "1–3 đề xuất hành động cụ thể rút ra từ phần 1.", {}, "Đề xuất"))
    sections.append({"num": "PHẦN 1", "title": "Traffic Performance - tổng quan, thị trường, landing page, blog", "blocks": b})

    # ═ PHẦN 2 ═
    b = []
    enq_pages = sorted([p for p, v in enq_land.items() if v and p != "(not set)"], key=lambda p: -enq_land[p])
    trs = []
    for p in enq_pages:
        s_, sp_ = land.get(p, {}).get("sessions", 0), land_p.get(p, {}).get("sessions", 0)
        trs.append([cell(esc(p), "u"), n(enq_land[p], True), n(s_), n(sp_), dl(s_, sp_), cell(fpct(ratio(enq_land[p], s_), 2), "n")])
    b.append(table("2.1 Landing page nào mang enquiry - traffic vào đó có giảm không?",
                   f"GA4 + CRO engine · kỳ {rng}",
                   ["Landing page", nh("Enquiry"), nh(f"Phiên {L}"), nh(Lp.capitalize()), nh("Δ"), nh("CR")], trs, 640))
    b.append(h3("2.2 Từ khoá đưa người dùng vào các trang đã tạo enquiry"))
    b.append(warn("Phần từ khoá này là suy đoán", [
        "Search Console cho biết từ khoá nào đưa người dùng tới từng trang; CRO engine cho biết trang nào phát sinh enquiry. "
        "Ghép hai nguồn chỉ cho ra <b>mối liên hệ có khả năng xảy ra</b>.",
        "Google không cung cấp dữ liệu nối từ khoá với hành vi chuyển đổi - đây là giới hạn cấu trúc."]))
    brand = [k.lower() for k in P.get("brand_keywords", [])]
    is_brand = lambda q: any(k in q.lower() for k in brand)  # noqa: E731
    trs = []
    for p in enq_pages:
        qs = [q for q in C["gsc_page_queries"].get(p, []) if q["clicks"] > 0][:4]
        if not qs:
            trs.append([cell(esc(p), "u"), n(enq_land[p], True), cell("<i>không có từ khoá có click</i>"), cell("-", "n"),
                        cell("-", "n"), cell("", "n")])
            continue
        for i, q in enumerate(qs):
            row = [] if i else [cell(esc(p), "u", rowspan=len(qs)), n(enq_land[p], True, ) | {"rowspan": len(qs)}]
            chip = "<span class='chip c-b'>TH</span>" if is_brand(q["query"]) else "<span class='chip c-w'>PHI TH</span>"
            row += [cell(esc(q["query"])), n(q["clicks"]), cell(fdec(q["position"]), "n"), cell(chip, "n")]
            trs.append(row)
    b.append(table("Từ khoá theo từng landing page đã tạo enquiry",
                   f"Search Console {L} · tối đa 4 từ khoá nhiều click nhất mỗi trang · TH = thương hiệu",
                   ["Landing page", nh("Enquiry"), "Từ khoá", nh("Clicks"), nh("Vị trí"), nh("Loại")], trs, 700))
    b.append(slot("p2_conclusion", "note", "2–4 đoạn: trang nào mang enquiry, xu hướng traffic của chúng, tỷ trọng từ khoá thương hiệu.", {}, "Kết luận"))
    b.append(slot("p2_propose", "propose", "1–3 đề xuất.", {}, "Đề xuất"))
    sections.append({"num": "PHẦN 2", "title": "Landing Page tạo Enquiry &amp; từ khoá liên quan", "chip": "PHẦN TỪ KHOÁ LÀ SUY ĐOÁN",
                     "blocks": b})

    # ═ PHẦN 3 ═
    b = []
    to_contact = by(C["landing_to_contact"], "landingPage", "sessions")
    main_pages = [home, contact] + [p for p in enq_pages if p not in (home, contact)][:3]
    trs = []
    for p in main_pages:
        r = land.get(p)
        if not r:
            continue
        br = r["bounceRate"]
        isc = p == contact
        trs.append([cell(esc(p) + (" (trang chủ)" if p == home else ""), "u"), n(r["sessions"]), cell(fpct(br), "n dn"),
                    cell(fpct(1 - br), "n"), cell("-" if isc else fint(to_contact.get(p, 0)), "n"),
                    cell("-" if isc else fpct(ratio(to_contact.get(p, 0), r["sessions"])), "n"), n(enq_land.get(p, 0), True),
                    cell(fpct(ratio(enq_land.get(p, 0), r["sessions"]), 2), "n")])
    b.append(table("3.1 Các landing page chính - đi tiếp, rơi rớt và enquiry",
                   f"GA4 {L} · “Rời ngay” = phiên không tương tác (dưới 10 giây, 1 trang, không chuyển đổi) · "
                   f"{code(contact)} đã là trang liên hệ nên hai cột giữa để “-”",
                   ["Landing page", nh("Phiên"), nh("Rời ngay"), nh("Đi tiếp"), nh("Tới trang liên hệ"), nh("Tỷ lệ tới"), nh("Enquiry"), nh("CR")],
                   trs, 720))
    hs = land.get(home, {}).get("sessions", 0)
    nxt = [r for r in sorted(C["home_next"], key=lambda r: -r["sessions"]) if r["pagePath"] != home][:10]
    b.append(table("3.2 Sau trang chủ, người dùng đi tiếp vào đâu", f"GA4 {L} · trên {fint(hs)} phiên bắt đầu tại trang chủ",
                   ["Trang xem tiếp", nh("Phiên"), nh("% phiên từ trang chủ")],
                   [[cell(esc(r["pagePath"]), "u"), n(r["sessions"]), cell(fpct(ratio(r["sessions"], hs)), "n")] for r in nxt], 520))
    pt = defaultdict(lambda: {"urls": 0, "s": 0, "eng": 0, "pv": 0, "enq": 0})
    for r in C["landing"]:
        x = pt[ptype(r["landingPage"])["label"]]
        x["urls"] += 1; x["s"] += r["sessions"]; x["eng"] += r["engagedSessions"]; x["pv"] += r["screenPageViews"]
        x["enq"] += enq_land.get(r["landingPage"], 0)
    lost_total = sum(x["s"] - x["eng"] for x in pt.values())
    trs = [[cell(f"<b>{esc(k)}</b>"), n(x["urls"]), n(x["s"]), cell(f"<b>{fint(x['s'] - x['eng'])}</b>", "n dn"),
            cell(fpct(ratio(x["s"] - x["eng"], x["s"])), "n"), cell(fpct(ratio(x["s"] - x["eng"], lost_total)), "n"),
            cell(fdec(ratio(x["pv"], x["s"]) or 0, 2), "n"), n(x["enq"])]
           for k, x in sorted(pt.items(), key=lambda kv: -(kv[1]["s"] - kv[1]["eng"]))]
    b.append(table("3.3 Loại trang đang mất khách nhiều nhất - xếp theo số phiên mất",
                   f"GA4 {L} · gộp landing page (đã loại bot) theo loại trang · <b>Phiên mất</b> = phiên không tương tác · "
                   "<b>Trang xem TB</b> = lượt xem / phiên", ["Loại trang", nh("Số URL"), nh("Phiên vào"), nh("Phiên mất"),
                                                             nh("Tỷ lệ mất"), nh("Tỷ trọng mất"), nh("Trang xem TB"), nh("Enquiry")],
                   trs, 780, bid="t33"))
    att, att_p = enq_total + C["attempt_fail"], enq_total_p + V["attempt_fail"]
    steps = [("Phiên truy cập (đã loại bot)", TN["sessions"], TNp["sessions"], "Mẫu số"),
             (f"Chạm trang có form {code(contact)}", C["contact_sessions"], V["contact_sessions"], "Phiên có xem trang liên hệ"),
             ("Bấm nút gửi form", att, att_p, "Lượt gửi CRO ghi nhận, gồm cả lượt lỗi"),
             ("Gửi thành công", enq_total, enq_total_p, "Enquiry ghi nhận")]
    trs = []
    for i, (lab, v, vp, note) in enumerate(steps):
        rate = "100%" if i == 0 else f"{fpct(ratio(v, steps[i - 1][1]), 2 if i == 1 else 1)} của bước trên"
        rate_p = "" if i == 0 else fpct(ratio(vp, steps[i - 1][2]), 2 if i == 1 else 1)
        trs.append([cell(lab), n(v), cell(rate, "n"), cell(rate_p, "n"), cell(note)])
    b.append(table("3.4 Phễu gửi form", "Mỗi bước bắt buộc phải đi qua bước trước đó",
                   ["Bước", nh("Số lượt"), nh("Tỷ lệ đi tiếp"), nh(f"Tỷ lệ {Lp}"), "Ghi chú"], trs, 640, bid="t34"))
    b.append(slot("p3_conclusion", "note", "3–4 đoạn: nút thắt nằm ở bước nào của phễu, loại trang mất khách nhiều nhất, "
                  "trang chủ dẫn đi đâu, hiệu quả form khi đã bấm gửi.",
                  {"fail_reasons": C["fail_events"]}, "Kết luận"))
    b.append(slot("p3_propose", "propose", "2–4 đề xuất về CTA / điều hướng / form.", {}, "Đề xuất"))
    sections.append({"num": "PHẦN 3", "title": "User Journey &amp; Drop-off", "blocks": b})

    # ═ PHẦN 4 ═
    b = []
    ecl = defaultdict(list)
    for r in conv_c:
        if r["landing"] not in ecl[r["country"]]:
            ecl[r["country"]].append(r["landing"])
    ctry = sorted([c_ for c_, v_ in enq_c.items() if v_], key=lambda c_: -enq_c[c_])
    trs = [[cell(esc(c_)), n(enq_c[c_], True), cell(fpct(ratio(enq_c[c_], enq_total)), "n"),
            cell(", ".join(code(p) for p in ecl.get(c_, [])))] for c_ in ctry]
    b.append(table("4.1 Quốc gia nào tạo ra enquiry và từ trang nào", f"CRO engine · kỳ {rng} · quốc gia theo IP người gửi",
                   ["Quốc gia", nh("Enquiry"), nh("% tổng"), "Trang đã tạo enquiry"], trs, 620))
    if ctry:
        b.append(h3("4.2 Từng thị trường: loại trang mang traffic và từ khoá tương ứng"))
        b.append(warn("Cột từ khoá trong mục này là suy đoán", [
            "Search Console cho biết từ khoá nào đưa người dùng tới từng trang ở từng quốc gia; CRO engine cho biết trang nào phát sinh "
            "enquiry. Ghép hai nguồn chỉ cho ra <b>mối liên hệ có khả năng xảy ra</b>.",
            "Từ khoá <b>in đậm</b> là từ đã có click thật; từ để thường mới chỉ có lượt hiển thị."]))
        enq_cl = defaultdict(float)
        for r in conv_c:
            enq_cl[(r["country"], group(r["landing"]))] += r["eventCount"]
        for c_ in ctry:
            gs, gsp = defaultdict(int), defaultdict(int)
            for r in C["country_landing"]:
                if r["country"] == c_:
                    gs[group(r["landingPage"])] += r["sessions"]
            for r in V["country_landing"]:
                if r["country"] == c_:
                    gsp[group(r["landingPage"])] += r["sessions"]
            kw = defaultdict(list)
            for q in C["gsc_country_page_query"].get(c_, []):
                kw[group(q["page"])].append(q)
            trs = []
            for gname in sorted(gs, key=lambda k: (-enq_cl.get((c_, k), 0), -gs[k]))[:9]:
                qs = sorted(kw.get(gname, []), key=lambda q: (-q["clicks"], -q["impressions"]))
                seen, words = set(), []
                for q in qs:
                    if q["query"] in seen:
                        continue
                    seen.add(q["query"])
                    words.append(f"<b>{esc(q['query'])}</b>" if q["clicks"] else esc(q["query"]))
                    if len(words) == 4:
                        break
                e_ = enq_cl.get((c_, gname), 0)
                trs.append([cell(f"<b>{esc(gname)}</b>"), n(gs[gname]), n(gsp.get(gname, 0)), dl(gs[gname], gsp.get(gname, 0)),
                            n(e_, True), cell(fpct(ratio(e_, gs[gname]), 2), "n"),
                            {"v": " · ".join(words) or "-", "cls": "", "style": "font-size:12px"}])
            b.append(table(f"{esc(VI_COUNTRY.get(c_, c_))} - {fint(enq_c[c_])} enquiry",
                           "GA4 gộp landing page theo loại trang (blog tách theo chủ đề) · đã loại bot · từ khoá từ Search Console",
                           ["Loại trang", nh(f"Phiên {L}"), nh(Lp.capitalize()), nh("Δ"), nh("Enquiry"), nh("CR"), "Từ khoá nhiều traffic nhất"],
                           trs, 820))
    b.append(slot("p4_conclusion", "note", "2–4 đoạn: thị trường nào tạo enquiry, hiệu quả theo traffic (CR), trang nào phát sinh.",
                  {"markets_table": "t13"}, "Kết luận"))
    b.append(slot("p4_propose", "propose", "1–3 đề xuất theo thị trường.", {}, "Đề xuất"))
    sections.append({"num": "PHẦN 4", "title": "Enquiry theo thị trường &amp; truy vấn tìm kiếm", "blocks": b})

    # ═ PHẦN 5 (CRM only) ═
    if has_crm:
        b = []
        cfg = P["crm"]
        ytd, cur_i, prev_i = defaultdict(int), defaultdict(int), defaultdict(int)
        for r in crm_ytd:
            ytd[r["industry"]] += 1
        for r in crm_cur:
            cur_i[r["industry"]] += 1
        for r in crm_prev:
            prev_i[r["industry"]] += 1
        posts = defaultdict(int)
        for pth in C.get("blog_inventory", []):
            t = topic(pth)["label"]
            posts[cfg.get("topic_to_industry", {}).get(t, t)] += 1
        inds = sorted(set(ytd) | set(cfg.get("client_industries", [])), key=lambda k: (-ytd.get(k, 0), k))
        ytot = sum(ytd.values())
        trs = [[cell(f"<b>{esc(k)}</b>" if not k.startswith("Khác") else esc(k)), n(ytd.get(k, 0), True),
                cell(fpct(ratio(ytd.get(k, 0), ytot)), "n"), n(cur_i.get(k, 0)), n(prev_i.get(k, 0)), n(posts.get(k, 0))] for k in inds]
        trs.append([cell("<b>TỔNG</b>"), n(ytot, True), cell("100%", "n"), n(len(crm_cur)), n(len(crm_prev)),
                    n(len(C.get("blog_inventory", [])))])
        b.append(table("5.1 Ngành hàng của khách gửi enquiry - xếp theo tỷ trọng cả năm",
                       f"File CRM · chỉ {code(cfg['website_value'])} · {fint(ytot)} enquiry năm {end.year} tính tới "
                       f"{vn_date(crm_last) if crm_last else '-'} · nhãn ngành gộp theo hồ sơ · <b>ngành của công ty khách hàng</b>",
                       ["Ngành khách hàng", nh(f"Enquiry {end.year}"), nh("Tỷ trọng"), nh(L.capitalize()), nh(Lp.capitalize()),
                        nh("Số bài blog đã có")], trs, 680, [""] * (len(trs) - 1) + ["tot"], "t51"))
        b.append(slot("p5_notes", "warn", "2–3 ý: tỷ trọng enquiry thuộc ngành ngoài danh sách ngành mục tiêu, CRM cập nhật tới đâu.",
                      {"client_industries": cfg.get("client_industries"),
                       "outside_share": sum(v for k, v in ytd.items() if k not in cfg.get("client_industries", [])),
                       "ytd_total": ytot, "unmapped_labels": sorted({r["raw_industry"] for r in crm_ytd
                                                                    if r["raw_industry"] not in cfg.get("industry_map", {})})},
                      "Hai điều cần biết về bảng này"))
        plan = P.get("content_plan", {})
        if plan.get("enabled"):
            ap_ = plan.get("articles_by_industry", {})
            inds2 = sorted(set(inds) | set(ap_), key=lambda k: (-ytd.get(k, 0), k))
            trs = [[cell(esc(k)), n(ytd.get(k, 0), True), cell(fpct(ratio(ytd.get(k, 0), ytot)), "n"), n(cur_i.get(k, 0)),
                    n(posts.get(k, 0)), n(ap_.get(k, 0), bool(ap_.get(k)))] for k in inds2]
            b.append(table("5.2 Kế hoạch nội dung so với ngành thực sự mang enquiry",
                           f"{esc(plan.get('label', 'Kế hoạch nội dung'))} đối chiếu với {fint(ytot)} enquiry năm {end.year}",
                           ["Ngành", nh("Enquiry CRM"), nh("% enquiry"), nh("Kỳ này"), nh("Bài đang có"), nh("Bài kế hoạch")], trs, 680))
        b.append(slot("p5_conclusion", "note", "3–4 đoạn: nhóm khách lớn nhất, ngành có nhu cầu nhưng thiếu nội dung, "
                      "kế hoạch nội dung lệch với nhu cầu ở đâu.", {}, "Kết luận"))
        b.append(slot("p5_propose", "propose", "2–4 đề xuất cho kế hoạch nội dung.", {}, "Đề xuất"))
        sections.append({"num": "PHẦN 5", "title": "Ngành tạo Enquiry so với chủ đề đang làm SEO", "blocks": b})

    # ═ PHẦN GEO ═
    b = []
    ai, aip = by(C["ai"], "sessionSource", "sessions"), by(V["ai"], "sessionSource", "sessions")
    srcs = sorted(set(ai) | set(aip), key=lambda s: -ai.get(s, 0))
    trs = [[cell(esc(s)), n(ai.get(s, 0)), n(aip.get(s, 0)), dl(ai.get(s, 0), aip.get(s, 0))] for s in srcs]
    trs.append([cell("<b>Tổng kênh AI</b>"), n(sum(ai.values()), True), n(sum(aip.values())), dl(sum(ai.values()), sum(aip.values()))])
    b.append(table("Traffic đến từ nền tảng AI", "GA4 · nguồn phiên là trợ lý AI",
                   ["Nền tảng", nh(f"Phiên {L}"), nh(Lp.capitalize()), nh("Δ")], trs, 460, [""] * len(srcs) + ["tot"]))
    al = sorted(C["ai_landing"], key=lambda r: -r["sessions"])[:10]
    b.append(table("AI đang đẩy người dùng vào những trang nào", f"GA4 · {L}",
                   ["Landing page", "Nguồn", nh("Phiên"), nh("Tương tác"), nh("Thời lượng TB")],
                   [[cell(esc(r["landingPage"]), "u"), cell(esc(r["sessionSource"])), n(r["sessions"]),
                     cell(fpct(ratio(r["engagedSessions"], r["sessions"])), "n"), cell(f"{fint(r['averageSessionDuration'])} s", "n")]
                    for r in al], 560))
    b.append(slot("geo_conclusion", "note", "2–3 đoạn: xu hướng kênh AI, chất lượng phiên, đã tạo enquiry chưa.",
                  {"ai_enquiry": C["ai_enquiry"]}, "Kết luận"))
    b.append(slot("geo_propose", "propose", "1–2 đề xuất.", {}, "Đề xuất"))
    gnum = f"PHẦN {6 if has_crm else 5}"
    for blk in b:
        if blk["type"] == "table":
            blk["caption"] = f"{gnum[-1]}.{1 + [x for x in b if x['type'] == 'table'].index(blk)} " + blk["caption"]
    sections.append({"num": gnum, "title": "GEO - AI Search", "blocks": b})

    # ═ KẾT LUẬN ═
    kp = [{"label": "Phiên thật", "value": fint(TN["sessions"]), "delta": delta(TN["sessions"], TNp["sessions"])[0] + " so kỳ trước",
           "cls": delta(TN["sessions"], TNp["sessions"])[1]},
          {"label": "Enquiry website", "value": fint(enq_total), "delta": f"kỳ trước {fint(enq_total_p)}", "cls": "",
           "hl": not has_crm}]
    if has_crm:
        kp.append({"label": "Enquiry thật từ CRM", "value": fint(len(crm_cur)), "delta": f"kỳ trước {fint(len(crm_prev))}", "hl": True})
    kp.append({"label": "Chạm trang liên hệ", "value": fpct(ratio(C["contact_sessions"], TN["sessions"]), 2),
               "delta": f"kỳ trước {fpct(ratio(V['contact_sessions'], TNp['sessions']), 2)}"})
    sections.append({"num": "KẾT LUẬN", "title": f"Conclusion - bức tranh chuyển đổi kỳ {rng}", "blocks": [
        {"type": "kpis", "items": kp},
        slot("conclusion_cards", "cards", "4–6 thẻ: Tín hiệu tốt / Vấn đề / Nút thắt / Form / Thị trường / Nội dung… mỗi thẻ 1 tiêu đề, "
             "1–2 câu có số liệu, 1 câu 'Nói đơn giản'.", {}),
        slot("conclusion_summary", "note", "1 đoạn 'Tóm lại' 3–4 câu.", {}, "Tóm lại")]})

    # ═ PHỤ LỤC ═
    b = []
    if bp:
        blogs = sorted([r for r in C["landing"] if r["landingPage"].startswith(bp)], key=lambda r: -r["sessions"])[:30]
        b.append(table("Chi tiết 30 bài blog nhiều phiên nhất", "GA4 · phiên theo landing page",
                       ["Bài viết", "Chủ đề", nh(f"Sessions {Lp}"), nh(f"Sessions {L}"), nh("Δ"), nh("Tương tác"), nh("Enquiry")],
                       [[cell(esc(r["landingPage"]), "u"), cell(esc(topic(r["landingPage"])["label"])),
                         n(land_p.get(r["landingPage"], {}).get("sessions", 0)), n(r["sessions"]),
                         dl(r["sessions"], land_p.get(r["landingPage"], {}).get("sessions", 0)),
                         cell(fpct(ratio(r["engagedSessions"], r["sessions"])), "n"), n(enq_land.get(r["landingPage"], 0))]
                        for r in blogs], 780))
    lost = sorted([r for r in C["landing"] if r["sessions"] >= 40], key=lambda r: -(r["sessions"] - r["engagedSessions"]))[:14]
    b.append(table(f"Chi tiết {len(lost)} URL mất nhiều phiên nhất", f"GA4 {L} · chỉ tính trang từ 40 phiên trở lên",
                   ["Landing page", nh("Phiên vào"), nh("Phiên mất"), nh("Tỷ lệ mất"), nh("Tỷ trọng mất"), nh("Trang xem TB"), nh("Enquiry")],
                   [[cell(esc(r["landingPage"]), "u"), n(r["sessions"]), cell(f"<b>{fint(r['sessions'] - r['engagedSessions'])}</b>", "n dn"),
                     cell(fpct(ratio(r["sessions"] - r["engagedSessions"], r["sessions"])), "n"),
                     cell(fpct(ratio(r["sessions"] - r["engagedSessions"], lost_total)), "n"),
                     cell(fdec(ratio(r["screenPageViews"], r["sessions"]) or 0, 2), "n"), n(enq_land.get(r["landingPage"], 0))]
                    for r in lost], 780))
    sections.append({"num": "PHỤ LỤC", "title": "Phụ lục: Báo cáo chi tiết",
                     "sub": "Các bảng chi tiết theo từng URL, đã được gộp nhóm ở phần chính.", "blocks": b})

    # ═ COMPETITOR (Ahrefs, written by Claude into competitors.json) ═
    cp = d / "competitors.json"
    if cp.exists():
        comp = json.loads(cp.read_text())
        sections.append({"num": "PHỤ LỤC", "title": "Competitor Research", "chip": "DỮ LIỆU TỪ AHREFS",
                         "sub": comp.get("sub", ""), "blocks": comp["blocks"]})
    else:
        sections.append({"num": "PHỤ LỤC", "title": "Competitor Research", "chip": "DỮ LIỆU TỪ AHREFS", "blocks": [
            slot("competitors", "blocks", "Chưa có competitors.json — lấy số liệu Ahrefs theo SKILL.md rồi build lại.", {})]})

    report = {
        "meta": {"title": f"Báo cáo hiệu quả {client} T{end.month}", "eyebrow": f"{P.get('agency', 'SEONGON')} × {client}",
                 "h1": "Báo cáo hiệu quả SEO &amp; Chuyển đổi",
                 "lead": f"Website {esc(P['domain'])} · Kỳ báo cáo {start:%d/%m} - {vn_date(end)}, so sánh với "
                         f"{(pend - pstart).days + 1} ngày liền trước",
                 "items": [["Kỳ", f"{start:%d/%m} - {vn_date(end)}"],
                           ["Nguồn", "GA4 · Search Console · CRO Engine" + (" · CRM" if has_crm else "")],
                           ["Property", P["ga4_property_id"]], ["Phát hành", vn_date(date.today())]],
                 "brand": P.get("brand", {})},
        "sections": sections,
    }
    dump(d / "report.json", report)
    slots = [blk["id"] for s in sections for blk in s["blocks"] if blk["type"] == "slot"]
    out({"ok": True, "report": str(d / "report.json"), "narrative": str(d / "narrative.json"), "slots": slots,
         "crm": ({"in_period": len(crm_cur), "matched_cro": len(recon["matched"]), "crm_only": len(recon["crm_only"]),
                  "cro_only": len(recon["cro_only"])} if has_crm else None)})


if __name__ == "__main__":
    main()
