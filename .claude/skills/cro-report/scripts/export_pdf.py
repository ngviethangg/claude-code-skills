"""Export the approved report.html to an A4-landscape PDF with headless Chrome.

Usage: export_pdf.py --site SLUG --start YYYY-MM-DD --end YYYY-MM-DD [--out PATH]
Only run after the user has approved the report.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

from common import load_profile, parse_date, period_dir, out

CHROME_CANDIDATES = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                     "/Applications/Chromium.app/Contents/MacOS/Chromium",
                     "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                     shutil.which("google-chrome") or "", shutil.which("chromium") or ""]

PRINT_CSS = """<style>
@page{size:A4 landscape;margin:10mm}
@media print{html,body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
</style>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    P = load_profile(a.site)
    start, end = parse_date(a.start), parse_date(a.end)
    d = period_dir(P["slug"], start, end)
    html = (d / "report.html").read_text()
    pr = d / "report_print.html"
    pr.write_text(html.replace("</head>", PRINT_CSS + "</head>", 1))
    chrome = next((c for c in CHROME_CANDIDATES if c and Path(c).exists()), None)
    if not chrome:
        out({"ok": False, "error": "Không tìm thấy Chrome/Chromium/Edge để xuất PDF"}, 1)
    dest = Path(a.out) if a.out else Path.home() / "Downloads" / f"Bao-cao-{P['slug']}-{start:%d.%m}-{end:%d.%m.%Y}.pdf"
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={dest}", pr.as_uri()], check=True, capture_output=True, timeout=180)
    out({"ok": dest.exists(), "pdf": str(dest), "bytes": dest.stat().st_size if dest.exists() else 0})


if __name__ == "__main__":
    main()
