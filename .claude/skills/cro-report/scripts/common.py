"""Shared helpers for cro-report: profiles, periods, Google clients, formatting.

Runs on the seo-analyst virtualenv (GA4 Data/Admin + Search Console + Sheets),
reusing that skill's per-site OAuth tokens.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILES_DIR = SKILL_DIR / "profiles"
REPORTS_DIR = SKILL_DIR / "reports"
SEO_ANALYST_DIR = Path.home() / ".claude/skills/seo-analyst"

sys.path.insert(0, str(SEO_ANALYST_DIR / "scripts"))


# ── profile ──────────────────────────────────────────────────────────────────

def load_profile(slug: str) -> dict:
    p = PROFILES_DIR / f"{slug}.json"
    if not p.exists():
        avail = ", ".join(sorted(x.stem for x in PROFILES_DIR.glob("*.json") if not x.stem.startswith("_")))
        raise SystemExit(json.dumps({"ok": False, "error": f"Không có hồ sơ '{slug}'. Có sẵn: {avail or '(chưa có)'}"},
                                    ensure_ascii=False))
    return json.loads(p.read_text())


def crm_enabled(profile: dict) -> bool:
    return bool(profile.get("crm", {}).get("enabled"))


# ── periods ──────────────────────────────────────────────────────────────────

def default_period(profile: dict, today: date | None = None) -> tuple[date, date]:
    """Latest complete reporting window: start_day of last month → end_day of this month."""
    today = today or date.today()
    sd = profile.get("period", {}).get("start_day", 1)
    ed = profile.get("period", {}).get("end_day", 0)
    if not ed:  # calendar month: previous full month
        end = today.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end
    end = today.replace(day=ed) if today.day > ed else (today.replace(day=1) - timedelta(days=1)).replace(day=ed)
    start = (end.replace(day=1) - timedelta(days=1)).replace(day=sd)
    return start, end


def previous_period(start: date, end: date, days: int | None = None) -> tuple[date, date]:
    """The window right before `start`: `days` long (profile period.compare_days), else as long as the period."""
    n = days or (end - start).days + 1
    pend = start - timedelta(days=1)
    return pend - timedelta(days=n - 1), pend


def period_dir(slug: str, start: date, end: date) -> Path:
    d = REPORTS_DIR / slug / f"{start:%Y%m%d}-{end:%Y%m%d}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


# ── Google clients ───────────────────────────────────────────────────────────

def _creds(profile: dict):
    from config import credentials_path  # seo-analyst
    from auth import load_credentials    # seo-analyst
    return load_credentials(credentials_path(profile["seo_analyst_profile"]))


def ga4_client(profile: dict):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient(credentials=_creds(profile))


def ga4_admin(profile: dict):
    from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient
    return AnalyticsAdminServiceClient(credentials=_creds(profile))


def gsc_service(profile: dict):
    from googleapiclient.discovery import build
    return build("searchconsole", "v1", credentials=_creds(profile), cache_discovery=False)


def sheets_client(profile: dict):
    import gspread
    return gspread.authorize(_creds(profile))


# ── formatting (vi-VN) ───────────────────────────────────────────────────────

def fint(v) -> str:
    if v is None or v == "":
        return "-"
    return f"{int(round(v)):,}".replace(",", ".")


def fdec(v, nd=1) -> str:
    if v is None:
        return "-"
    s = f"{v:,.{nd}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


def fpct(v, nd=1) -> str:
    """v is a ratio (0.123 → 12,3%)."""
    return "-" if v is None else fdec(v * 100, nd) + "%"


def delta(cur, prev) -> tuple[str, str]:
    """(text, css class) for the Δ column."""
    if not prev:
        return "-", ""
    d = (cur - prev) / prev
    txt = ("+" if d > 0 else "") + fdec(d * 100, 1) + "%"
    return txt, ("up" if d > 0 else "dn" if d < 0 else "")


def ratio(a, b):
    return (a / b) if b else None


def esc(s) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def vn_date(d: date) -> str:
    return f"{d:%d/%m/%Y}"


def short_range(a: date, b: date) -> str:
    return f"{a:%d/%m}–{b:%d/%m}"


def month_label(end: date) -> str:
    return f"kỳ tháng {end.month}"


def classify(path: str, rules: list[dict], default):
    for r in rules:
        if re.search(r["match"], path, flags=re.I):
            return r
    return default


def conv_landing(row: dict) -> str:
    """Landing page of a conversion: the CRO engine's own first-page label, GA4's landingPage as fallback."""
    v = row.get("customEvent:cro_landing_page") or ""
    return v if v and v != "(not set)" else row.get("landingPage", "(not set)")


def real_conversions(profile: dict, rows: list[dict]) -> list[dict]:
    """conversion_success rows on production hostnames, minus the profile's internal/QA exclusions."""
    hosts = set(profile.get("hostnames") or [])
    excl = profile.get("exclude_conversions", [])
    keep = []
    for r in rows:
        if hosts and r.get("hostName") not in hosts:
            continue
        ymd = r["dateHourMinute"][:8]
        ymd = f"{ymd[:4]}-{ymd[4:6]}-{ymd[6:]}"
        if any(x.get("from", "0000") <= ymd <= x.get("to", "9999") and (not x.get("country") or x["country"] == r["country"])
               for x in excl):
            continue
        keep.append(r)
    return keep


def dump(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=str))


def out(obj, code: int = 0):
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))
    sys.exit(code)
