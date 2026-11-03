#!/bin/sh
# pack.sh [out.zip] — package the public skill: excludes .skillignore patterns and refuses private paths / channel words.
set -e
D="$(cd "$(dirname "$0")/.." && pwd)"; OUT="${1:-$D/../obsion-motion.zip}"
BAD=$(grep -rnIE '/Users/|~/\.claude|syntx|маскот|\bOB\b' "$D" --exclude-dir=vendor --exclude=pack.sh || true)
[ -n "$BAD" ] && { echo "REFUSED: private paths or channel words found:"; echo "$BAD" | head -20; exit 1; }
cd "$D/.." && rm -f "$OUT" && zip -qr "$OUT" "$(basename "$D")" -x '*.wav' '*.mp4' '*/__pycache__/*' '*/_frames/*' '*/watch/*' '*.pyc' '*/.DS_Store' && echo "packed $OUT ($(du -h "$OUT" | cut -f1))"
