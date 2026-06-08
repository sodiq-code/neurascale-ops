#!/usr/bin/env bash
# NeuroScale Ops — Full Demo Run Script
# Runs the complete incident response pipeline against all demo scenarios.
# For hackathon judges: this shows the end-to-end UiPath Maestro flow.
#
# Usage:
#   ./scripts/demo_run.sh                 # All scenarios
#   ./scripts/demo_run.sh oomkill         # Single scenario
#   ./scripts/demo_run.sh --interactive   # Prompt for approval
#   OPENAI_API_KEY=sk-... ./scripts/demo_run.sh  # With real GPT-4o-mini

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$SCRIPT_DIR")"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  NeuroScale Ops — AI Incident Response Demo                  ║"
echo "║  UiPath AgentHack 2026 · Track 1: Maestro Case               ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# ── Check Python ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Install Python 3.11+."
  exit 1
fi

# ── Install deps if needed ────────────────────────────────────────────────────
if [ ! -d "$ROOT/.venv" ]; then
  echo "📦 Setting up virtual environment..."
  python3 -m venv "$ROOT/.venv"
  source "$ROOT/.venv/bin/activate"
  pip install -q -r "$ROOT/requirements.txt"
else
  source "$ROOT/.venv/bin/activate"
fi

# ── Load .env if present ──────────────────────────────────────────────────────
if [ -f "$ROOT/.env" ]; then
  echo "🔑 Loading .env..."
  export $(grep -v '^#' "$ROOT/.env" | xargs)
fi

# ── Run pipeline ──────────────────────────────────────────────────────────────
cd "$ROOT"
SCENARIO="${1:-all}"
INTERACTIVE="${2:-}"

echo "🚀 Starting pipeline — Scenario: $SCENARIO"
echo ""

if [ "$SCENARIO" = "all" ]; then
  python3 main.py --scenario all --output /tmp/neurascale-ops-results.json
  echo ""
  echo "✅ All scenarios complete. Results: /tmp/neurascale-ops-results.json"
else
  python3 main.py --scenario "$SCENARIO" ${INTERACTIVE:+--interactive}
fi

echo ""
echo "📊 Launch dashboard with:"
echo "   streamlit run dashboard/app.py"
echo ""
