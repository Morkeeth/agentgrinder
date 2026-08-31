#!/usr/bin/env bash
# Copy manifest-filtered tracked files (no .git) into OUT_DIR; refuse on real leaks.
# Never touches network, never git init, never deletes source.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?usage: seed-clean.sh <output-dir>}"

if [[ -e "$OUT" && -n "$(ls -A "$OUT" 2>/dev/null || true)" ]]; then
  echo "refusing: output dir exists and is not empty: $OUT" >&2
  echo "remove it or pick another path" >&2
  exit 2
fi

mkdir -p "$OUT"
cd "$ROOT"

FILES=()
while IFS= read -r f; do
  [[ -n "$f" ]] && FILES+=("$f")
done < <(git ls-files | python3 "$ROOT/scripts/seed-manifest.py")
echo "copying ${#FILES[@]} manifest files -> $OUT (from $(git ls-files | wc -l | tr -d ' ') tracked)"

for f in "${FILES[@]}"; do
  mkdir -p "$OUT/$(dirname "$f")"
  cp "$f" "$OUT/$f"
done

echo "running privacy control on cards (html)..."
LEAKS=0
HTML_FILES=()
for f in "${FILES[@]}"; do
  case "$f" in
    *.html|*.htm|*.svg) HTML_FILES+=("$OUT/$f") ;;
  esac
done

if ((${#HTML_FILES[@]})); then
  if ! python3 -m agentgrinder privacycheck "${HTML_FILES[@]}"; then
    LEAKS=$((LEAKS + 1))
  fi
fi

echo "running full directory audit (DOC-GLOB allowed)..."
if ! python3 "$ROOT/scripts/privacy-audit.py" "$OUT"; then
  echo "" >&2
  echo "seed-clean REFUSED: DIRTY files in seed (see audit above)" >&2
  exit 1
fi

if ((LEAKS > 0)); then
  echo "seed-clean REFUSED: card privacycheck found leaks" >&2
  exit 1
fi

echo ""
echo "seed-clean OK: $OUT ($(find "$OUT" -type f | wc -l | tr -d ' ') files)"
echo "next: bash scripts/init-public-repo.sh $OUT"
