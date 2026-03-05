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

    # Configuration overrides
    parser.add_argument("--max-cost", type=float, help="Maximum cost in USD (default: 150)")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent API tasks (default: 5)")
    parser.add_argument("--research-model", help="Model for research tasks")
    parser.add_argument("--synthesis-model", help="Model for synthesis tasks")
    parser.add_argument("--search-rounds", type=int, help="Max search rounds per research task")
    parser.add_argument(
        "--format",
        choices=["markdown", "pdf", "docx", "all"],
        default="markdown",
        help="Output format (default: markdown)",
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
        "l3": ("L3 Final Report", run.l3_executive_briefing is not None, ""),
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

    # Show next step hint
    next_layer = run.next_layer()
    if next_layer:
        console.print(
            f"\n[cyan]Next step:[/cyan] python -m deep_research --resume {run.id} --stop-after {next_layer}"
        )
    else:
        console.print("\n[green]All layers complete! Final reports are ready.[/green]")

        # Generate reports if requested
        if config.output_format != "markdown":
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
    if args.resume:
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
        run = orchestrator.create_run(args.company, args.context)

        console.print(Panel(
            f"[bold]New research: {run.company_name}[/bold]\n"
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
        stop_after = "l3"
    elif args.stop_after:
        stop_after = args.stop_after
    else:
        # Default: run the next layer only
        next_layer = run.next_layer()
        if next_layer is None:
            console.print("[green]Run is already complete.[/green]")
            show_run(config, run.id)
            return 0
        stop_after = next_layer

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
