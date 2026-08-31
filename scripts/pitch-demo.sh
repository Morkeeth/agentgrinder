#!/usr/bin/env bash
# Agent Grinder — 2-minute pitch demo script. Run from repo root.
set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "=== AGENT GRINDER pitch demo ==="
echo ""

echo "1/6 flex — your agents on this machine"
python3 -m agentgrinder flex
echo ""

echo "2/6 vibe — meme label (no streaks)"
python3 -m agentgrinder vibe
echo ""

echo "3/6 roast — honest shape clowning"
python3 -m agentgrinder roast
echo ""

echo "4/6 grind card — latest session (opens browser)"
python3 -m agentgrinder grind --harness auto --no-rank -o /tmp/pitch-grind.html
echo "   -> /tmp/pitch-grind.html"
echo ""

echo "5/6 share card — claim-your-handle + vibe + roast"
python3 -m agentgrinder share --harness auto --vibe --roast --no-open -o /tmp/pitch-share.html
echo "   -> /tmp/pitch-share.html"
echo ""

echo "6/6 rig card — stack for friends"
python3 -m agentgrinder rig --share-names --no-open -o /tmp/pitch-rig.html
echo "   -> /tmp/pitch-rig.html"
echo ""

echo "Optional: heist card (rig ACK)"
echo "  python3 -m agentgrinder heist oscar --thief friend -o /tmp/pitch-heist.html"
echo ""
echo "Web path: open site → /?onboard → grind --push → /?explore"
echo "Pitch doc: docs/PITCH-2026-09-01.md"
echo ""
