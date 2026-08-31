#!/usr/bin/env bash
# One initial commit in a seed directory. Does not add a remote or push.
set -euo pipefail

SEED="${1:?usage: init-public-repo.sh <seed-dir>}"
cd "$SEED"

if [[ -d .git ]]; then
  echo "refusing: .git already exists in $SEED" >&2
  exit 2
fi

git init -b main
git add -A
git commit -m "$(cat <<'EOF'
Initial public seed — Agent Grinder (Option A).

Privacy-first grind cards for agent sessions. Seeded from private archive;
history and night-run logs not included.
EOF
)"

echo ""
echo "public repo ready locally: $SEED"
echo "Oscar: create GitHub repo, then:"
echo "  cd $SEED && git remote add origin <url> && git push -u origin main"
