#!/usr/bin/env bash
# ───────────────────────────────────────────────────────────────
# L3 refresh: branch from L2, re-run L3a_select + L3a_write + L3b + L3c + L3d (PDF)
#
# Usage:
#   ./run_l3_refresh.sh                    # Both Brimstone + Fervo
#   ./run_l3_refresh.sh brimstone          # Just Brimstone
#   ./run_l3_refresh.sh fervo              # Just Fervo
# ───────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source run IDs — update these if you create new base runs
BRIMSTONE_RUN="run_523046f1"
FERVO_RUN="run_5693c63b"

FILTER="${1:-all}"

run_refresh() {
    local run_id="$1"
    local company="$2"

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║  L3 Refresh: $company"
    echo "║  Base run: $run_id"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    # Step 1: Branch from base run, restart from L3a_select through L3d (PDF)
    echo "→ Branching from $run_id (restart from L3a_select → L3d)..."
    local branch_output
    branch_output=$(python -m deep_research --branch-from "$run_id" --restart-from l3a_select --stop-after l3d 2>&1)
    echo "$branch_output"

    # Extract the new run ID from output
    local new_run_id
    new_run_id=$(echo "$branch_output" | grep -o 'SA_[^ ]*' | head -1)

    if [[ -z "$new_run_id" ]]; then
        echo "ERROR: Could not extract new run ID from branch output"
        echo "$branch_output"
        return 1
    fi

    echo ""
    echo "→ New run created: $new_run_id"

    # Step 2: Find the L3 output file
    local l3_file="outputs/${new_run_id}/l3_deep_analysis.md"
    if [[ ! -f "$l3_file" ]]; then
        # Try alternate filename
        l3_file="outputs/${new_run_id}/l3_executive_briefing.md"
    fi

    if [[ ! -f "$l3_file" ]]; then
        echo "WARNING: L3 output file not found at expected path"
        echo "  Checked: outputs/${new_run_id}/l3_deep_analysis.md"
        echo "  Check outputs/${new_run_id}/ manually"
        return 1
    fi

    # Step 3: Check for pipeline-generated PDF (L3d), fallback to standalone generator
    local safe_company
    safe_company=$(echo "$company" | tr ' ' '_')
    local timestamp
    timestamp=$(date +%Y%m%d_%H%M)
    local pipeline_pdf="outputs/${new_run_id}/l3_deep_analysis.pdf"
    local pdf_file="${safe_company}_Deep_Analysis_${timestamp}.pdf"

    if [[ -f "$pipeline_pdf" ]]; then
        echo "→ Pipeline PDF found, copying: $pdf_file"
        cp "$pipeline_pdf" "$pdf_file"
    else
        echo "→ No pipeline PDF found, generating via standalone: $pdf_file"
        python generate_pdf.py "$l3_file" "$pdf_file"
    fi

    echo ""
    echo "✓ Complete: $company"
    echo "  Run:  $new_run_id"
    echo "  MD:   $l3_file"
    echo "  PDF:  $pdf_file"
    echo ""
}

# ── Main ──
echo "L3 Refresh Script"
echo "Using L3a_select/L3a_write/L3b/L3c templates from prompts/situation_assessment/"
echo ""

if [[ "$FILTER" == "all" || "$FILTER" == "brimstone" ]]; then
    run_refresh "$BRIMSTONE_RUN" "Brimstone"
fi

if [[ "$FILTER" == "all" || "$FILTER" == "fervo" ]]; then
    run_refresh "$FERVO_RUN" "Fervo Energy"
fi

echo "Done."
