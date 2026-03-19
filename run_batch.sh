#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────
# Batch runner: 3 sequential deep research runs (situation assessment)
#
# Companies:  Bloom Energy, Brimstone, Fervo Energy
# Mode:       situation_assessment (banking / deal-oriented)
# Budget:     $150 per run (configurable below)
#
# Usage:
#   chmod +x run_batch.sh
#   ./run_batch.sh                    # Run all 3
#   ./run_batch.sh --dry-run          # Dry-run all 3 (L0+L0.5 only, ~$4 each)
#   ./run_batch.sh --resume           # Resume any incomplete runs
#
# Prerequisites:
#   - ANTHROPIC_API_KEY set in environment
#   - Python dependencies installed (pip install -r requirements.txt)
# ───────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Configuration ──────────────────────────────────────────────
MODE="situation_assessment"
MAX_COST=200
LOG_DIR="$SCRIPT_DIR/outputs/batch_$(date +%Y%m%d_%H%M%S)"

# Companies to research — each entry is: "Company Name|sector context|optional extra context"
COMPANIES=(
    'Bloom Energy|clean energy technology, fuel cells, distributed power|Focus on deal dynamics: Brookfield partnership, convertible note structure, SK ecoplant relationship, OBBBA regulatory tailwinds. The company has a $45B+ market cap and complex capital structure.'
    'Brimstone|industrial decarbonization, cement, building materials|Focus on: capital structure after DOE grant loss, Amazon offtake agreement, critical mineral byproduct value, strategic buyer universe (CRH, Holcim, HeidelbergCement). Private company — use SEC-adjacent sources, patent filings, state permits, and investor disclosures.'
    'Fervo Energy|geothermal energy, clean firm power, data center infrastructure|Focus on: Cape Station commercialization timeline (100MW Oct 2026), Google/Mitsui relationships, NV Energy partnership, IPO vs acquisition path, competitive moat vs conventional geothermal. Series E at $462M (Dec 2025).'
)

# ── Preflight checks ──────────────────────────────────────────
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set."
    echo "  export ANTHROPIC_API_KEY='sk-ant-...'"
    exit 1
fi

# Verify Python module can be imported
python -c "from deep_research.orchestrator import DeepResearchOrchestrator" 2>/dev/null || {
    echo "ERROR: Cannot import deep_research module."
    echo "  pip install -r requirements.txt --break-system-packages"
    exit 1
}

mkdir -p "$LOG_DIR"

# ── Parse arguments ────────────────────────────────────────────
DRY_RUN=""
RESUME_MODE=""
EXTRA_ARGS=""

for arg in "$@"; do
    case "$arg" in
        --dry-run)  DRY_RUN="--dry-run" ;;
        --resume)   RESUME_MODE="1" ;;
        --verbose)  EXTRA_ARGS="$EXTRA_ARGS --verbose" ;;
        *)          echo "Unknown argument: $arg"; exit 1 ;;
    esac
done

# ── Helper functions ───────────────────────────────────────────
run_company() {
    local idx="$1"
    local entry="$2"

    IFS='|' read -r company sector context <<< "$entry"
    company=$(echo "$company" | xargs)  # trim whitespace
    sector=$(echo "$sector" | xargs)
    context=$(echo "$context" | xargs)

    local log_file="$LOG_DIR/$(echo "$company" | tr ' ' '_' | tr '[:upper:]' '[:lower:]').log"
    local safe_name=$(echo "$company" | tr ' ' '_' | tr '[:upper:]' '[:lower:]')

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  Run $((idx+1))/${#COMPANIES[@]}: $company"
    echo "║  Mode: $MODE | Max cost: \$$MAX_COST"
    echo "║  Log: $log_file"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    local cmd_args=(
        python -m deep_research "$company"
        --mode "$MODE"
        --sector "$sector"
        --max-cost "$MAX_COST"
    )

    # Add context if provided
    if [[ -n "$context" ]]; then
        cmd_args+=(--context "$context")
    fi

    # Dry-run or full pipeline
    if [[ -n "$DRY_RUN" ]]; then
        cmd_args+=($DRY_RUN)
    else
        cmd_args+=(--run-all --full-report)
    fi

    # Add any extra args (e.g., --verbose)
    if [[ -n "$EXTRA_ARGS" ]]; then
        cmd_args+=($EXTRA_ARGS)
    fi

    echo "Command: ${cmd_args[*]}"
    echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "───────────────────────────────────────────────────────────────"

    local start_time=$(date +%s)

    # Run with tee to both console and log
    if "${cmd_args[@]}" 2>&1 | tee "$log_file"; then
        local end_time=$(date +%s)
        local elapsed=$(( (end_time - start_time) / 60 ))
        echo ""
        echo "✓ $company completed in ${elapsed}m"
        echo "  $(date '+%Y-%m-%d %H:%M:%S')" >> "$log_file"
    else
        local exit_code=$?
        local end_time=$(date +%s)
        local elapsed=$(( (end_time - start_time) / 60 ))
        echo ""
        echo "✗ $company FAILED (exit code $exit_code) after ${elapsed}m"
        echo "  Check log: $log_file"
        # Continue to next company — don't abort the batch
    fi

    # Brief pause between runs to let API rate limits reset
    if [[ -z "$DRY_RUN" ]] && (( idx + 1 < ${#COMPANIES[@]} )); then
        echo ""
        echo "  Pausing 30s before next run (rate limit headroom)..."
        sleep 30
    fi
}

resume_incomplete() {
    echo "Scanning for incomplete runs to resume..."
    echo ""

    local found=0
    for run_dir in "$SCRIPT_DIR/outputs"/run_*/; do
        [[ -d "$run_dir" ]] || continue
        local state_file="$run_dir/run_state.json"
        [[ -f "$state_file" ]] || continue

        local status=$(python -c "
import json
with open('$state_file') as f:
    d = json.load(f)
print(d.get('status', 'unknown'))
" 2>/dev/null)

        if [[ "$status" != "complete" ]]; then
            local run_id=$(basename "$run_dir")
            local company=$(python -c "
import json
with open('$state_file') as f:
    d = json.load(f)
print(d.get('company_name', 'unknown'))
" 2>/dev/null)

            echo "  Found incomplete: $run_id ($company) — status: $status"
            found=$((found + 1))

            local log_file="$LOG_DIR/resume_${run_id}.log"
            echo "  Resuming with --run-all --full-report..."

            python -m deep_research --resume "$run_id" --run-all --full-report $EXTRA_ARGS 2>&1 | tee "$log_file" || {
                echo "  ✗ Resume failed for $run_id"
            }
        fi
    done

    if [[ $found -eq 0 ]]; then
        echo "  No incomplete runs found."
    fi
}

# ── Main execution ─────────────────────────────────────────────
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Deep Research Batch Runner                                 ║"
echo "║  Companies: ${#COMPANIES[@]}                                              ║"
echo "║  Mode: $MODE                                  ║"
if [[ -n "$DRY_RUN" ]]; then
echo "║  *** DRY RUN — L0 + L0.5 only ***                          ║"
fi
echo "║  Logs: $LOG_DIR"
echo "╚══════════════════════════════════════════════════════════════╝"

batch_start=$(date +%s)

if [[ -n "$RESUME_MODE" ]]; then
    resume_incomplete
else
    for i in "${!COMPANIES[@]}"; do
        run_company "$i" "${COMPANIES[$i]}"
    done
fi

batch_end=$(date +%s)
batch_elapsed=$(( (batch_end - batch_start) / 60 ))

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "  Batch complete. Total time: ${batch_elapsed}m"
echo "  Logs: $LOG_DIR"
echo "══════════════════════════════════════════════════════════════"

# Print summary of all runs
echo ""
echo "Run summary:"
python -m deep_research --list-runs 2>/dev/null || true
