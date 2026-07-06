#!/usr/bin/env bash
# /seo-content-writer — installer
set -e

SKILL_DIR="$HOME/.claude/skills/seo-content-writer"

echo "=== /seo-content-writer — Installer ==="
echo ""

mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/credentials"

echo "Tìm Python 3.10+..."
for py in python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    PYBIN="$py"
    break
  fi
done

if [ -z "$PYBIN" ]; then
  echo "ERROR: Cần Python 3.10+. Cài qua python.org hoặc: brew install python3"
  exit 1
fi
echo "  Dùng: $($PYBIN --version)"

if [ ! -d "$SKILL_DIR/.venv" ]; then
  echo "Tạo virtual environment..."
  "$PYBIN" -m venv "$SKILL_DIR/.venv"
fi

echo "Cài dependencies..."
"$SKILL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SKILL_DIR/.venv/bin/pip" install --quiet -r "$SKILL_DIR/requirements.txt"

echo ""
echo "=== Cài đặt hoàn tất! ==="
echo ""
echo "Bước tiếp theo:"
echo "  1. Vào GCP Console → APIs & Services → Credentials"
echo "     Tạo OAuth 2.0 Client ID (Desktop app)"
echo "     Enable: Sheets API + Docs API + Drive API"
echo "  2. Download JSON → đặt tên oauth_client.json:"
echo "     mv ~/Downloads/client_secret_*.json $SKILL_DIR/oauth_client.json"
echo "  3. Điền dữ liệu vào Google Sheet, rồi gõ /seo-content-writer"
