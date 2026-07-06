#!/usr/bin/env bash
# /compare-content-seo-competitor — installer
set -e

SKILL_DIR="$HOME/.claude/skills/compare-content-seo-competitor"

echo "=== /compare-content-seo-competitor — Installer ==="
echo ""

mkdir -p "$SKILL_DIR/scripts"

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

echo "Cài dependencies (requests, beautifulsoup4, lxml)..."
"$SKILL_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$SKILL_DIR/.venv/bin/pip" install --quiet -r "$SKILL_DIR/requirements.txt"

echo ""
echo "=== Cài đặt hoàn tất! ==="
echo "Dùng: /compare-content-seo-competitor <brand-url> <comp1-url> <comp2-url>"
