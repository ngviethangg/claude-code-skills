#!/usr/bin/env bash
# /cro-report — installer
set -e

SKILL_DIR="$HOME/.claude/skills/cro-report"
SEO_ANALYST_DIR="$HOME/.claude/skills/seo-analyst"

echo "=== /cro-report — Installer ==="
echo ""

mkdir -p "$SKILL_DIR/profiles" "$SKILL_DIR/reports"

echo "Kiểm tra skill seo-analyst (bắt buộc — cro-report dùng chung venv + token OAuth của skill này)..."
if [ ! -x "$SEO_ANALYST_DIR/.venv/bin/python" ]; then
  echo "ERROR: Chưa thấy venv tại $SEO_ANALYST_DIR/.venv"
  echo "  → Cài và cấu hình skill seo-analyst trước, rồi chạy lại install.sh này."
  exit 1
fi
echo "  OK: $("$SEO_ANALYST_DIR/.venv/bin/python" --version)"

echo "Kiểm tra gói Python cần thiết trong venv của seo-analyst..."
MISSING=""
for pkg in google.analytics.data google.analytics.admin_v1alpha googleapiclient gspread; do
  "$SEO_ANALYST_DIR/.venv/bin/python" -c "import $pkg" 2>/dev/null || MISSING="$MISSING $pkg"
done
if [ -n "$MISSING" ]; then
  echo "ERROR: venv seo-analyst thiếu gói:$MISSING"
  echo "  → cd $SEO_ANALYST_DIR && .venv/bin/pip install -r requirements.txt"
  exit 1
fi
echo "  OK: đủ google-analytics-data, google-analytics-admin, google-api-python-client, gspread"

echo ""
echo "Kiểm tra Chrome/Chromium/Edge (dùng để xuất PDF)..."
CHROME=""
for c in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
         "/Applications/Chromium.app/Contents/MacOS/Chromium" \
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"; do
  [ -x "$c" ] && CHROME="$c" && break
done
if [ -z "$CHROME" ]; then
  command -v google-chrome >/dev/null 2>&1 && CHROME="google-chrome"
fi
if [ -z "$CHROME" ]; then
  command -v chromium >/dev/null 2>&1 && CHROME="chromium"
fi
if [ -z "$CHROME" ]; then
  echo "  ⚠️  Không thấy Chrome/Chromium/Edge — bước xuất PDF (export_pdf.py) sẽ lỗi cho tới khi cài một trong các trình duyệt này."
else
  echo "  OK: $CHROME"
fi

echo ""
echo "=== Cài đặt hoàn tất! ==="
echo "Dùng: /cro-report — chọn hồ sơ website có sẵn trong profiles/, hoặc tạo hồ sơ mới từ profiles/_template.json"
