"""Render report.json + narrative.json into the approved HTML layout.

Usage: render.py --site SLUG --start YYYY-MM-DD --end YYYY-MM-DD
Writes report.html next to report.json. Missing narrative slots render as a red "chưa có nhận định" box.
"""
from __future__ import annotations

import argparse
import json

from common import SKILL_DIR, load_profile, parse_date, period_dir, esc, out

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700;800'
         '&family=JetBrains+Mono:wght@400;500;700&display=swap">')


def mix(hex_, ratio):
    """Blend a #rrggbb colour with white (ratio = share of white)."""
    h = hex_.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    f = lambda c: round(c + (255 - c) * ratio)  # noqa: E731
    return f"#{f(r):02x}{f(g):02x}{f(b):02x}"


def css(brand: dict) -> str:
    b1, b2 = brand.get("b1", "#0573fd"), brand.get("b2", "#1ea0ff")
    b3 = brand.get("b3", b2)
    return ((SKILL_DIR / "assets/report.css").read_text()
            .replace("{b1}", b1).replace("{b2}", b2).replace("{b3}", b3)
            .replace("{bsoft}", brand.get("soft", mix(b1, .9))).replace("{btint}", brand.get("tint", mix(b1, .955))))


def td(c, tag="td"):
    if not isinstance(c, dict):
        c = {"v": c}
    attrs = ""
    if c.get("cls"):
        attrs += f' class="{c["cls"]}"'
    for k in ("rowspan", "colspan"):
        if c.get(k):
            attrs += f' {k}="{c[k]}"'
    if c.get("style"):
        attrs += f' style="{c["style"]}"'
    return f"<{tag}{attrs}>{c.get('v', '')}</{tag}>"


def r_table(b):
    head = "".join(f'<th{" class=" + chr(34) + c["cls"] + chr(34) if c.get("cls") else ""}>{c["h"]}</th>' for c in b["cols"])
    rows = []
    rc = b.get("row_cls") or []
    for i, r in enumerate(b["rows"]):
        cls = f' class="{rc[i]}"' if i < len(rc) and rc[i] else ""
        rows.append(f"<tr{cls}>" + "".join(td(c) for c in r) + "</tr>")
    sub = f" <span>{b['sub']}</span>" if b.get("sub") else ""
    return (f'<div class="tw"><table style="min-width:{b.get("min", 600)}px"><caption>{b["caption"]}{sub}</caption>'
            f"<thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def r_warn(title, items):
    return f'<div class="note warnbox"><h3>{title}</h3><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>"


def r_note(title, paras):
    return f'<div class="note"><h3>{title}</h3>' + "".join(f"<p>{p}</p>" for p in paras) + "</div>"


def r_propose(title, items):
    return f'<div class="note propose"><h3>{title or "Đề xuất"}</h3><ul>' + "".join(f"<li>{x}</li>" for x in items) + "</ul></div>"


COLORS = {"pos": "var(--pos)", "neg": "var(--neg)", "warn": "var(--warn)", "b1": "var(--b1)"}


def r_cards(items):
    out_ = []
    for c in items:
        simple = (f'<p style="font-size:12.5px;color:var(--muted);border-top:1px solid var(--rule2);padding-top:9px">'
                  f'<i>Nói đơn giản:</i> {c["simple"]}</p>') if c.get("simple") else ""
        out_.append(f'<div class="q"><div><div class="qa" style="color:{COLORS.get(c.get("color"), "var(--b1)")}">{c.get("tag", "")}</div>'
                    f'<div class="qt">{c.get("title", "")}</div></div><p>{c.get("body", "")}</p>{simple}</div>')
    return '<div class="mx">' + "".join(out_) + "</div>"


def r_kpis(items):
    return '<div class="kpis">' + "".join(
        f'<div class="kpi{" hl" if k.get("hl") else ""}"><div class="kl">{k["label"]}</div><div class="kv">{k["value"]}</div>'
        f'<div class="kd {k.get("cls", "")}">{k.get("delta", "")}</div></div>' for k in items) + "</div>"


def r_bars(b):
    """Horizontal bar chart: {title, items:[{label, value, hl?}], unit?}"""
    items = b["items"]
    mx = max((i["value"] for i in items), default=1) or 1
    rowh, top, lw, w = 34, 30, 170, 820
    hgt = top + rowh * len(items) + 10
    parts = [f'<text x="0" y="16" font-family="var(--m)" font-size="11" fill="var(--muted)" letter-spacing=".08em">'
             f'{esc(b.get("title", "")).upper()}</text>']
    for i, it in enumerate(items):
        y = top + i * rowh
        bw = (w - lw - 90) * it["value"] / mx
        fill = "var(--b1)" if it.get("hl") else "var(--b2)"
        op = "1" if it.get("hl") else ".55"
        parts.append(f'<text x="0" y="{y + 17}" font-size="13" font-weight="{700 if it.get("hl") else 500}" fill="var(--ink)">'
                     f'{esc(it["label"])}</text>'
                     f'<rect x="{lw}" y="{y + 4}" width="{bw:.1f}" height="18" rx="3" fill="{fill}" opacity="{op}"/>'
                     f'<text x="{lw + bw + 8:.1f}" y="{y + 17}" font-family="var(--m)" font-size="12" fill="var(--ink2)">'
                     f'{esc(it.get("display", it["value"]))}</text>')
    return (f'<div class="cbox"><svg viewBox="0 0 {w} {hgt}" role="img" aria-label="{esc(b.get("title", ""))}">'
            + "".join(parts) + "</svg></div>")


def r_todo(sid, hint):
    return (f'<div class="todo"><h3>Chưa có nhận định · {esc(sid)}</h3><p>{esc(hint)}</p></div>')


def r_block(b, narr):
    t = b["type"]
    if t == "table":
        return r_table(b)
    if t == "warn":
        return r_warn(b["title"], b["items"])
    if t == "note":
        return r_note(b.get("title", "Kết luận"), b.get("paras", []))
    if t == "propose":
        return r_propose(b.get("title"), b["items"])
    if t == "kpis":
        return r_kpis(b["items"])
    if t == "cards":
        return r_cards(b["items"])
    if t == "bars":
        return r_bars(b)
    if t == "h3":
        return f'<h3 style="font-size:17px;margin:4px 0 0">{b["text"]}</h3>'
    if t == "p":
        return f'<p style="font-size:13.5px">{b["html"]}</p>'
    if t == "slot":
        n = narr.get(b["id"])
        if n is None or n == {} or n == []:
            return r_todo(b["id"], b.get("hint", ""))
        if n is False or (isinstance(n, dict) and n.get("hide")):
            return ""  # explicitly removed by the user
        k = b["kind"]
        title = (n.get("title") if isinstance(n, dict) else None) or b.get("title")
        if k == "warn":
            return r_warn(title, n["items"])
        if k == "note":
            return r_note(title, n["paras"])
        if k == "propose":
            return r_propose(title, n["items"])
        if k == "cards":
            return r_cards(n["items"])
        if k == "blocks":
            return "".join(r_block(x, narr) for x in n["blocks"])
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    a = ap.parse_args()
    P = load_profile(a.site)
    d = period_dir(P["slug"], parse_date(a.start), parse_date(a.end))
    rep = json.loads((d / "report.json").read_text())
    np_ = d / "narrative.json"
    narr = json.loads(np_.read_text()) if np_.exists() else {}
    m = rep["meta"]
    hidden = set(narr.get("_hide_sections", []))

    html = [f"<!doctype html><html lang=\"vi\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" "
            f"content=\"width=device-width,initial-scale=1\"><title>{m['title']}</title>{FONTS}"
            f"<style>{css(m.get('brand', {}))}</style></head><body><div class=\"wrap\">",
            f'<header class="hero"><div class="eyebrow">{m["eyebrow"]}</div><h1>{m["h1"]}</h1><p>{m["lead"]}</p>'
            '<div class="meta">' + "".join(f"<div>{k} <b>{v}</b></div>" for k, v in m["items"]) + "</div></header>"]
    missing = []
    for s in rep["sections"]:
        if f"{s['num']}|{s['title']}" in hidden or s["title"] in hidden:
            continue
        chip = f'<span class="chip c-w">{s["chip"]}</span>' if s.get("chip") else ""
        sub = f'<p style="font-size:13.5px;color:var(--ink2);margin-top:4px">{s["sub"]}</p>' if s.get("sub") else ""
        body = []
        for b in s["blocks"]:
            if b.get("id") and b["id"] in narr.get("_hide_blocks", []):
                continue
            if b["type"] == "slot" and b["id"] not in narr:
                missing.append(b["id"])
            body.append(r_block(b, narr))
        html.append(f'<section><div class="sh"><div class="sh-l"><div class="snum">{s["num"]}</div><h2>{s["title"]}</h2>{sub}</div>'
                    f"{chip}</div>{''.join(body)}</section>")
    html.append("</div></body></html>")
    (d / "report.html").write_text("".join(html))
    out({"ok": True, "html": str(d / "report.html"), "missing_slots": missing})


if __name__ == "__main__":
    main()
