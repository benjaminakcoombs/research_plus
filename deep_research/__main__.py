"""CLI entry point for the deep research system.

Usage:
    # Start new run, stop after L0
    python -m deep_research "Camellia Plc" --stop-after l0

    # Resume and run next layer
    python -m deep_research --resume run_abc123 --stop-after l05

    # Run the full pipeline
    python -m deep_research "Camellia Plc" --run-all

    # With context
    python -m deep_research "Camellia Plc" --context "Focus on near-term opportunities" --stop-after l0
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.table import Table

from .config import Config
from .models import LAYER_DISPLAY_NAMES, LAYER_ORDER, ResearchRun
from .orchestrator import DeepResearchOrchestrator
from .report_generator import generate_reports
from .research_runner import BudgetExceededError

console = Console()


def setup_logging(verbose: bool = False) -> None:
    """Configure logging with rich output."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    # Quiet down noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="deep_research",
        description="Multi-layered AI deep research system for strategic company analysis.",
    )

    # Positional: company name (optional if resuming)
    parser.add_argument(
        "company",
        nargs="?",
        help="Company name to research (e.g., 'Camellia Plc')",
    )

    # Mode control
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--stop-after",
        choices=LAYER_ORDER,
        help="Run through this layer then stop. Layers: l0, l05, l1, l15, l2, l3",
    )
    mode.add_argument(
        "--run-all",
        action="store_true",
        help="Run the full pipeline (all layers)",
    )

    # Resume
    parser.add_argument(
        "--resume",
        metavar="RUN_ID",
        help="Resume a previous run (e.g., run_abc12345)",
    )

    # Context
    parser.add_argument(
        "--context",
        help="Additional context for the research (e.g., 'Focus on near-term M&A opportunities')",
    )

    # Pipeline mode
    parser.add_argument(
        "--mode",
        choices=["strategic_briefing", "situation_assessment"],
        default="strategic_briefing",
        help="Pipeline mode: strategic_briefing (exec/consulting) or situation_assessment (banking/deal)",
    )

    # Situation Assessment specific inputs
    parser.add_argument(
        "--sector",
        help="Sector context for situation assessment (e.g., 'healthcare services')",
    )
    parser.add_argument(
        "--target-bank",
        help="Target bank for situation assessment (e.g., 'Perella Weinberg Partners')",
    )
    parser.add_argument(
        "--sub-sector",
        help="Sub-sector focus (e.g., 'behavioral health', 'physician practice management')",
    )

    # Configuration overrides
    parser.add_argument("--max-cost", type=float, help="Maximum cost in USD (default: 150)")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent API tasks (default: 5)")
    parser.add_argument("--research-model", help="Model for research tasks")
    parser.add_argument("--synthesis-model", help="Model for synthesis tasks")
    parser.add_argument("--search-rounds", type=int, help="Max search rounds per research task")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run L0 + L0.5 only, then estimate full pipeline cost and exit",
    )
    parser.add_argument(
        "--full-report",
        action="store_true",
        help="Include L4 full report generation (40-50 page report). Situation assessment mode only.",
    )
    parser.add_argument(
        "--format",
        choices=["markdown", "pdf", "docx", "all"],
        default="markdown",
        help="Output format (default: markdown)",
    )

    # Branching (for L3 iteration)
    parser.add_argument(
        "--branch-from",
        metavar="RUN_ID",
        help="Branch from an existing run's L2 outputs. Creates a new run with a fresh L3+. "
             "Use with --stop-after to control how far the branch runs.",
    )
    parser.add_argument(
        "--restart-from",
        choices=["l3a", "l3b", "l4a", "l4b", "l4c", "l4d"],
        default="l3a",
        help="Which layer to restart from when branching (default: l3a). Layers before this are kept.",
    )

    # Misc
    parser.add_argument("--output-dir", type=Path, help="Output directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--list-runs", action="store_true", help="List existing runs")
    parser.add_argument("--show-run", metavar="RUN_ID", help="Show status of a run")

    return parser.parse_args()


def build_config(args: argparse.Namespace) -> Config:
    """Build config from CLI arguments."""
    config = Config()

    if args.mode:
        config.pipeline_mode = args.mode
    if args.max_cost:
        config.max_total_cost_usd = args.max_cost
        config.warn_cost_usd = args.max_cost * 0.7
    if args.max_concurrent:
        config.max_concurrent_tasks = args.max_concurrent
    if args.research_model:
        config.research_model = args.research_model
    if args.synthesis_model:
        config.synthesis_model = args.synthesis_model
    if args.search_rounds:
        config.max_search_rounds = args.search_rounds
    if args.output_dir:
        config.project_root = args.output_dir.parent
    if args.format:
        config.output_format = args.format

    return config


def list_runs(config: Config) -> None:
    """List all existing runs."""
    output_dir = config.output_dir
    if not output_dir.exists():
        console.print("[dim]No runs found.[/dim]")
        return

    table = Table(title="Research Runs")
    table.add_column("Run ID", style="cyan")
    table.add_column("Company", style="green")
    table.add_column("Status", style="yellow")
    table.add_column("Cost", style="red")
    table.add_column("Created", style="dim")

    for run_dir in sorted(output_dir.iterdir()):
        state_file = run_dir / "run_state.json"
        if state_file.exists():
            try:
                run = ResearchRun.load(output_dir, run_dir.name)
                table.add_row(
                    run.id,
                    run.company_name,
                    run.status,
                    f"${run.total_cost_usd:.2f}",
                    run.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            except Exception:
                table.add_row(run_dir.name, "?", "?", "?", "?")

    console.print(table)


def show_run(config: Config, run_id: str) -> None:
    """Show detailed status of a run."""
    try:
        run = ResearchRun.load(config.output_dir, run_id)
    except FileNotFoundError:
        console.print(f"[red]Run not found: {run_id}[/red]")
        return

    console.print(Panel(f"[bold]{run.company_name}[/bold]", title=f"Run: {run.id}"))

    table = Table()
    table.add_column("Layer", style="cyan")
    table.add_column("Status", style="yellow")
    table.add_column("Details", style="dim")

    layers_info = {
        "l0": ("L0 Profile", run.l0_output is not None, f"Archetype: {run.company_archetype}" if run.company_archetype else ""),
        "l05": ("L0.5 Agent Design", run.l05_output is not None, f"{len(run.l1_prompts)} prompts" if run.l1_prompts else ""),
        "l1": ("L1 Research", len(run.l1_outputs) > 0, f"{len(run.l1_outputs)} agents" if run.l1_outputs else ""),
        "l15": ("L1.5 Consolidation", run.l15_output is not None, f"{len(run.tension_points)} tension points" if run.tension_points else ""),
        "l2": ("L2 Deep Dives", len(run.l2_outputs) > 0, f"{len(run.l2_outputs)} dives" if run.l2_outputs else ""),
        "l3a": ("L3a Synthesis Draft", run.l3a_draft is not None, ""),
        "l3b": ("L3b Final Output", run.l3b_final is not None, ""),
        "l3c": ("L3c PDF Generation", run.l3c_pdf_path is not None, run.l3c_pdf_path or ""),
        "l4a": ("L4a Report Architect", run.l4a_output is not None, f"{len(run.l4b_task_names)} tasks" if run.l4b_task_names else ""),
        "l4b": ("L4b Section Writers", len(run.l4b_outputs) > 0, f"{len(run.l4b_outputs)} sections" if run.l4b_outputs else ""),
        "l4c": ("L4c Editorial Review", run.l4c_editorial_memo is not None, ""),
        "l4d": ("L4d Final Report", run.l4_final_report is not None, ""),
    }

    for layer, (name, done, details) in layers_info.items():
        status = "[green]Complete[/green]" if done else "[dim]Pending[/dim]"
        table.add_row(name, status, details)

    console.print(table)
    console.print(f"\nTotal cost: [red]${run.total_cost_usd:.2f}[/red]")
    console.print(f"Output dir: [dim]{config.output_dir / run.id}[/dim]")

    # Show next layer
    next_layer = run.next_layer()
    if next_layer:
        console.print(f"\nNext layer: [cyan]{LAYER_DISPLAY_NAMES[next_layer]}[/cyan]")
        console.print(f"Resume with: [bold]python -m deep_research --resume {run.id} --stop-after {next_layer}[/bold]")
    else:
        console.print("\n[green]Run is complete![/green]")


def print_summary(run: ResearchRun, config: Config) -> None:
    """Print a summary after a layer completes."""
    run_dir = config.output_dir / run.id

    console.print()
    console.print(Panel(
        f"[bold green]Layer complete: {run.status}[/bold green]\n\n"
        f"Company: {run.company_name}\n"
        f"Run ID: {run.id}\n"
        f"Cost so far: ${run.total_cost_usd:.2f}\n"
        f"Output: {run_dir}",
        title="Progress",
    ))

    # Show what files were saved
    if run_dir.exists():
        files = sorted(run_dir.rglob("*.md"))
        if files:
            console.print("\n[dim]Saved files:[/dim]")
            for f in files:
                rel = f.relative_to(run_dir)
                console.print(f"  [dim]{rel}[/dim]")

    # Show L3c PDF path if it was generated
    if run.l3c_pdf_path:
        pdf_full = run_dir / run.l3c_pdf_path
        console.print(f"\n[bold green]PDF:[/bold green] {pdf_full}")

    # Show next step hint
    next_layer = run.next_layer()
    if next_layer:
        console.print(
            f"\n[cyan]Next step:[/cyan] python -m deep_research --resume {run.id} --stop-after {next_layer}"
        )
    else:
        console.print("\n[green]All layers complete! Final reports are ready.[/green]")

        # Generate reports if requested (docx only — PDF is handled by L3c)
        if config.output_format in ("docx", "all"):
            console.print(f"\nGenerating {config.output_format} reports...")
            outputs = generate_reports(run_dir, config.output_format)
            for path in outputs:
                if not path.suffix == ".md":
                    console.print(f"  Generated: {path}")


async def main_async(args: argparse.Namespace) -> int:
    """Async main entry point."""
    config = build_config(args)

    # Handle read-only commands first (no API key needed)
    if args.list_runs:
        list_runs(config)
        return 0

    if args.show_run:
        show_run(config, args.show_run)
        return 0

    # Validate config (API key required for actual runs)
    issues = config.validate()
    if issues:
        for issue in issues:
            console.print(f"[red]Config error: {issue}[/red]")
        return 1

    orchestrator = DeepResearchOrchestrator(config)

    # Determine what to run
    if getattr(args, "branch_from", None):
        # Branch from existing run — copy state up to restart point, new run ID
        import json
        import shutil
        from datetime import datetime as _dt

        try:
            parent = orchestrator.load_run(args.branch_from)
        except FileNotFoundError:
            console.print(f"[red]Run not found: {args.branch_from}[/red]")
            return 1

        # Generate readable run ID: SA_CompanyName_YYMMDDHHMM
        mode_prefix = "SA" if parent.pipeline_mode == "situation_assessment" else "SB"
        safe_company = parent.company_name.replace(" ", "").replace(",", "")[:20]
        timestamp = _dt.now().strftime("%y%m%d%H%M")
        new_id = f"{mode_prefix}_{safe_company}_{timestamp}"

        # Deep copy the run state
        state_path = config.output_dir / args.branch_from / "run_state.json"
        with open(state_path) as f:
            state = json.load(f)

        state["id"] = new_id
        state["updated_at"] = _dt.now().isoformat()

        # Determine what to clear based on restart_from
        restart = getattr(args, "restart_from", "l3a")
        clear_layers = {
            "l3a": ["l3a_draft", "l3b_final", "l4a_output", "l4a_style_guide", "l4a_outline",
                     "l4b_task_briefs", "l4b_task_names", "l4b_task_sections", "l4b_task_models",
                     "l4b_source_assignments", "l4b_outputs", "l4c_editorial_memo",
                     "l4c_global_notes", "l4c_section_notes", "l4d_outputs", "l4_final_report"],
            "l3b": ["l3b_final", "l4a_output", "l4a_style_guide", "l4a_outline",
                     "l4b_task_briefs", "l4b_task_names", "l4b_task_sections", "l4b_task_models",
                     "l4b_source_assignments", "l4b_outputs", "l4c_editorial_memo",
                     "l4c_global_notes", "l4c_section_notes", "l4d_outputs", "l4_final_report"],
            "l4a": ["l4a_output", "l4a_style_guide", "l4a_outline",
                     "l4b_task_briefs", "l4b_task_names", "l4b_task_sections", "l4b_task_models",
                     "l4b_source_assignments", "l4b_outputs", "l4c_editorial_memo",
                     "l4c_global_notes", "l4c_section_notes", "l4d_outputs", "l4_final_report"],
            "l4b": ["l4b_outputs", "l4c_editorial_memo", "l4c_global_notes",
                     "l4c_section_notes", "l4d_outputs", "l4_final_report"],
            "l4c": ["l4c_editorial_memo", "l4c_global_notes", "l4c_section_notes",
                     "l4d_outputs", "l4_final_report"],
            "l4d": ["l4d_outputs", "l4_final_report"],
        }

        # Map restart layer to the status of the previous layer
        status_before = {
            "l3a": "l2_complete", "l3b": "l3a_complete",
            "l4a": "l3b_complete", "l4b": "l4a_complete",
            "l4c": "l4b_complete", "l4d": "l4c_complete",
        }

        for field in clear_layers.get(restart, clear_layers["l3a"]):
            if field in state:
                if isinstance(state[field], list):
                    state[field] = []
                else:
                    state[field] = None

        state["status"] = status_before.get(restart, "l2_complete")
        state["current_layer"] = LAYER_ORDER[LAYER_ORDER.index(restart) - 1] if restart != "l3a" else "l2"

        # Reset cost to parent's cost at the restart point (keep L0-L2 costs)
        # Don't reset — the budget tracker uses runner.total_cost which syncs on load

        # Save new run
        new_dir = config.output_dir / new_id
        new_dir.mkdir(parents=True, exist_ok=True)
        with open(new_dir / "run_state.json", "w") as f:
            json.dump(state, f, indent=2, default=str)

        console.print(Panel(
            f"[bold]Branched: {parent.company_name}[/bold]\n"
            f"Parent: {args.branch_from}\n"
            f"New run: {new_id}\n"
            f"Restarting from: {restart}\n"
            f"Cost carried: ${state.get('total_cost_usd', 0):.2f}",
            title="Branch",
        ))

        # Now load and resume the branched run
        run = orchestrator.load_run(new_id)

    elif args.resume:
        # Resume existing run
        try:
            run = orchestrator.load_run(args.resume)
        except FileNotFoundError:
            console.print(f"[red]Run not found: {args.resume}[/red]")
            console.print(f"[dim]Looking in: {config.output_dir}[/dim]")
            return 1

        console.print(Panel(
            f"[bold]Resuming: {run.company_name}[/bold]\n"
            f"Run ID: {run.id}\n"
            f"Current status: {run.status}\n"
            f"Cost so far: ${run.total_cost_usd:.2f}",
            title="Resume",
        ))

    elif args.company:
        # New run
        run = orchestrator.create_run(
            args.company,
            args.context,
            sector=getattr(args, "sector", None),
            target_bank=getattr(args, "target_bank", None),
            sub_sector_focus=getattr(args, "sub_sector", None),
        )

        mode_label = f" [{config.pipeline_mode}]" if config.pipeline_mode != "strategic_briefing" else ""
        console.print(Panel(
            f"[bold]New research{mode_label}: {run.company_name}[/bold]\n"
            f"Run ID: {run.id}\n"
            f"Output: {config.output_dir / run.id}",
            title="Starting",
        ))

    else:
        console.print("[red]Error: Provide a company name or --resume a previous run.[/red]")
        console.print("Usage: python -m deep_research \"Company Name\" --stop-after l0")
        return 1

    # Determine stop point
    if args.run_all:
        if getattr(args, "full_report", False) and config.pipeline_mode == "situation_assessment":
            stop_after = "l4d"
        else:
            stop_after = "l3c"
    elif args.stop_after:
        stop_after = args.stop_after
    elif getattr(args, 'dry_run', False):
        stop_after = "l05"
    else:
        # Default: run the next layer only
        next_layer = run.next_layer()
        if next_layer is None:
            console.print("[green]Run is already complete.[/green]")
            show_run(config, run.id)
            return 0
        stop_after = next_layer

    # Validate that stop_after isn't behind the run's current position
    next_layer = run.next_layer()
    if next_layer and args.resume and stop_after in LAYER_ORDER:
        next_idx = LAYER_ORDER.index(next_layer)
        stop_idx = LAYER_ORDER.index(stop_after)
        if stop_idx < next_idx:
            console.print(
                f"[red]Error: Run is already past {stop_after} "
                f"(next layer: {LAYER_DISPLAY_NAMES[next_layer]}). "
                f"Cannot go backward.[/red]"
            )
            return 1

    console.print(f"[cyan]Running through: {LAYER_DISPLAY_NAMES[stop_after]}[/cyan]\n")

    # Run the pipeline
    start_time = time.time()

    try:
        run = await orchestrator.run_to(run, stop_after=stop_after)
    except BudgetExceededError as e:
        console.print(f"\n[red]Budget exceeded: {e}[/red]")
        console.print("[yellow]Partial outputs have been saved.[/yellow]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted. Saving partial outputs...[/yellow]")
        run.save(config.output_dir)
        console.print(f"Saved to: {config.output_dir / run.id}")
        return 130
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        # Try to save whatever we have
        try:
            run.save(config.output_dir)
            console.print(f"[yellow]Partial outputs saved to: {config.output_dir / run.id}[/yellow]")
        except Exception:
            pass
        raise

    elapsed = time.time() - start_time
    console.print(f"\n[dim]Elapsed: {elapsed / 60:.1f} minutes[/dim]")

    print_summary(run, config)

    # Dry-run cost estimation
    if getattr(args, 'dry_run', False):
        n_l1_agents = len(run.l1_prompts) if run.l1_prompts else 8
        l0_cost = run.total_cost_usd

        # Estimates based on observed runs
        est_l1_per_agent = 3.50  # 3 rounds × ~$1.17/round
        est_gap_fill = 14.0  # 2 agents × 3 rounds
        est_l15 = 6.0  # initial + re-consolidation
        est_l2_per_agent = 2.80  # 3 rounds × ~$0.93/round
        n_l2_agents = min(config.max_l2_agents, max(n_l1_agents, config.min_l2_agents))
        est_l3 = 8.0  # L3a + L3b (L3c is programmatic PDF generation, ~$0)
        est_quality_checks = 0.20  # Haiku checks

        est_l1_total = n_l1_agents * est_l1_per_agent
        est_l2_total = n_l2_agents * est_l2_per_agent
        est_total_low = l0_cost + est_l1_total * 0.8 + est_gap_fill * 0.8 + est_l15 * 0.8 + est_l2_total * 0.8 + est_l3 * 0.8 + est_quality_checks
        est_total_high = l0_cost + est_l1_total * 1.3 + est_gap_fill * 1.2 + est_l15 * 1.2 + est_l2_total * 1.3 + est_l3 * 1.2 + est_quality_checks

        console.print()
        console.print(Panel(
            f"[bold cyan]DRY RUN COST ESTIMATE: {run.company_name}[/bold cyan]\n\n"
            f"  L0 + L0.5 (actual):  ${l0_cost:.2f}\n"
            f"  L1 ({n_l1_agents} agents):      ${est_l1_total:.0f}  (est. ${est_l1_per_agent:.2f}/agent × 3 rounds)\n"
            f"  Gap-fill (2 agents): ${est_gap_fill:.0f}  (est.)\n"
            f"  L1.5 consolidation:  ${est_l15:.0f}  (initial + re-consolidation)\n"
            f"  L2 ({n_l2_agents} agents):      ${est_l2_total:.0f}  (est. ${est_l2_per_agent:.2f}/agent × 3 rounds)\n"
            f"  L3a + L3b synthesis: ${est_l3:.0f}\n"
            f"  Quality checks:      ${est_quality_checks:.2f}\n"
            f"  {'─' * 40}\n"
            f"  [bold]ESTIMATED TOTAL:  ${est_total_low:.0f} – ${est_total_high:.0f}[/bold]\n"
            f"  Budget:              ${config.max_total_cost_usd:.0f}  (headroom: ${config.max_total_cost_usd - est_total_high:.0f}+)\n\n"
            f"  Agent design: {n_l1_agents} L1 agents planned → {n_l2_agents} L2 agents\n"
            f"  Archetype: {run.company_archetype.value if run.company_archetype else 'unknown'}",
            title="Dry Run Estimate",
        ))

        console.print(f"\nTo run the full pipeline:")
        console.print(f"  [bold]python -m deep_research --resume {run.id} --run-all[/bold]")

    return 0


def main() -> None:
    """Main entry point."""
    args = parse_args()
    setup_logging(args.verbose)

    try:
        exit_code = asyncio.run(main_async(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        exit_code = 130
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]")
        if args.verbose:
            console.print_exception()
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
