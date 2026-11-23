"""Read the client's CRM enquiry log (CSV or Google Sheet) and reconcile it with CRO conversions."""
from __future__ import annotations

import csv
from datetime import date, datetime

from common import sheets_client


def _rows_from_csv(path: str) -> list[list[str]]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.reader(f))


def _rows_from_sheet(profile: dict, cfg: dict) -> list[list[str]]:
    ws = sheets_client(profile).open_by_key(cfg["sheet_id"]).worksheet(cfg["sheet_tab"])
    return ws.get_all_values()


def load(profile: dict, path: str | None = None) -> list[dict]:
    """All CRM rows for this website, as {dt, date, country, industry, source, level, raw_industry}."""
    cfg = profile["crm"]
    rows = _rows_from_csv(path or cfg["path"]) if (path or cfg.get("source") == "csv") else _rows_from_sheet(profile, cfg)
    col = cfg["columns"]
    norm = lambda s: " ".join(str(s).split()).lower()  # noqa: E731  header cells contain line breaks
    hi = next(i for i, r in enumerate(rows) if norm(col["date"]) in map(norm, r))
    head = [norm(h) for h in rows[hi]]
    idx = {k: head.index(norm(v)) for k, v in col.items() if norm(v) in head}
    out = []
    for r in rows[hi + 1:]:
        get = lambda k: r[idx[k]].strip() if k in idx and idx[k] < len(r) else ""  # noqa: E731
        try:
            d = datetime.strptime(get("date"), cfg.get("date_format", "%m/%d/%Y")).date()
        except ValueError:
            continue  # quarter separators, blank lines
        if cfg.get("website_value") and get("website").lower() != cfg["website_value"].lower():
            continue
        if get("source") in cfg.get("exclude_sources", []):
            continue
        dt = None
        if get("time"):
            for fmt in ("%I:%M %p", "%H:%M", "%I:%M%p"):
                try:
                    dt = datetime.combine(d, datetime.strptime(get("time").upper(), fmt).time())
                    break
                except ValueError:
                    pass
        raw = get("industry")
        out.append({"date": d, "dt": dt, "country": get("country"), "source": get("source"), "level": get("level"),
                    "raw_industry": raw,
                    "industry": cfg.get("industry_map", {}).get(raw, cfg.get("industry_default", "Khác (chưa rõ)"))})
    return out


def in_range(rows: list[dict], start: date, end: date) -> list[dict]:
    return [r for r in rows if start <= r["date"] <= end]


def reconcile(crm_rows: list[dict], cro_events: list[dict], tolerance_min: int = 3) -> dict:
    """Pair CRM enquiries with CRO conversion_success events by timestamp (same timezone assumed)."""
    ev = []
    for e in cro_events:
        s = e["dateHourMinute"]
        ev.append({"dt": datetime.strptime(s, "%Y%m%d%H%M"), "country": e["country"], "landing": e.get("landingPage"),
                   "page": e.get("pagePath"), "host": e.get("hostName"), "used": False})
    matched, crm_only = [], []
    for r in sorted([x for x in crm_rows if x["dt"]], key=lambda x: x["dt"]):
        best = None
        for e in ev:
            if e["used"]:
                continue
            gap = abs((e["dt"] - r["dt"]).total_seconds()) / 60
            if gap <= tolerance_min and (best is None or gap < best[0]):
                best = (gap, e)
        if best:
            best[1]["used"] = True
            matched.append({"crm_time": r["dt"], "country": r["country"], "page": best[1]["page"]})
        else:
            crm_only.append({"crm_time": r["dt"], "country": r["country"], "source": r["source"]})
    cro_only = [{"time": e["dt"], "country": e["country"], "page": e["page"], "host": e["host"]} for e in ev if not e["used"]]
    return {"crm_total": len(crm_rows), "matched": matched, "crm_only": crm_only, "cro_only": cro_only,
            "no_time": [r for r in crm_rows if not r["dt"]]}
