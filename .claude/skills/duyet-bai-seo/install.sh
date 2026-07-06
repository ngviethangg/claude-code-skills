#!/usr/bin/env bash
# /duyet-bai-seo — installer
set -e

SKILL_DIR="$HOME/.claude/skills/duyet-bai-seo"

echo "=== /duyet-bai-seo — Installer ==="
echo ""

mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/credentials"

echo "Tìm Python 3.10+..."
for py in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$py" >/dev/null 2>&1; then
    PYBIN="$py"
    break
  fi
done

if [ -z "$PYBIN" ]; then
  echo "ERROR: Cần Python 3.10+. Cài từ python.org hoặc: brew install python3"
  exit 1
fi
echo "  Dùng: $($PYBIN --version)"

if [ ! -d "$SKILL_DIR/.venv" ]; then
  echo "Tạo virtual environment..."
  "$PYBIN" -m venv "$SKILL_DIR/.venv"
fi

echo "Cài dependencies (google-api-python-client, google-auth-oauthlib)..."
"$SKILL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SKILL_DIR/.venv/bin/pip" install --quiet -r "$SKILL_DIR/requirements.txt"

echo ""
echo "=== Cài đặt hoàn tất! ==="

# OAuth client check
if [ ! -f "$SKILL_DIR/oauth_client.json" ]; then
  FALLBACK="$HOME/.claude/skills/seo-content-writer/oauth_client.json"
  if [ -f "$FALLBACK" ]; then
    echo ""
    echo "💡 Tìm thấy oauth_client.json từ seo-content-writer — script sẽ dùng tự động."
  else
    echo ""
    echo "⚠️  Chưa có oauth_client.json. Để dùng skill:"
    echo "   1. GCP Console → APIs & Services → Credentials"
    echo "   2. Tạo OAuth 2.0 Client ID (Desktop app)"
    echo "   3. Enable: Google Docs API"
    echo "   4. Download JSON → đặt vào: $SKILL_DIR/oauth_client.json"
  fi
fi

echo "Dùng: /duyet-bai-seo <outline-url> <article-url> <keyword>"
