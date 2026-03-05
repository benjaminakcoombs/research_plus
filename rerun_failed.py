"""Re-run only the failed L1 agents and slot results back into the run."""

import asyncio
import json
import logging
import time

from rich.console import Console
from rich.logging import RichHandler

from deep_research.config import Config
from deep_research.models import AgentOutput, ResearchRun
from deep_research.quality_checker import QualityChecker
from deep_research.research_runner import ResearchRunner

console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("anthropic").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


async def main():
    config = Config()
    run = ResearchRun.load(config.output_dir, "run_7070d661")

    # Find failed agents
    failed_indices = [
        i for i, o in enumerate(run.l1_outputs)
        if o.raw_output.startswith("[ERROR")
    ]

    if not failed_indices:
        console.print("[green]No failed agents to re-run![/green]")
        return

    console.print(f"Re-running {len(failed_indices)} failed agents: {[i+1 for i in failed_indices]}")

    runner = ResearchRunner(config)
    runner.total_cost = run.total_cost_usd
    checker = QualityChecker()

    for idx in failed_indices:
        prompt = run.l1_prompts[idx]
        name = run.l1_prompt_names[idx]
        task_id = f"l1_agent_{idx + 1:02d}"

        console.print(f"\n[cyan]Starting: {name} ({idx + 1}/10)[/cyan]")
        start = time.time()

        try:
            text, costs = await runner.run_research(prompt=prompt, task_id=task_id)
            elapsed = time.time() - start
            total_cost = sum(c.estimated_cost_usd for c in costs)
            search_count = sum(c.search_count for c in costs)

            console.print(
                f"[green]Complete: {name} "
                f"({elapsed:.0f}s, ${total_cost:.2f}, {search_count} searches)[/green]"
            )

            output = AgentOutput(
                agent_name=name,
                agent_type="l1",
                prompt=prompt,
                raw_output=text,
                token_count=sum(c.output_tokens for c in costs),
                search_count=search_count,
                execution_time_seconds=elapsed,
                cost_usd=total_cost,
            )
        except Exception as e:
            elapsed = time.time() - start
            console.print(f"[red]Failed again: {name} ({elapsed:.0f}s): {e}[/red]")
            output = AgentOutput(
                agent_name=name,
                agent_type="l1",
                prompt=prompt,
                raw_output=f"[ERROR: Research task failed: {e}]",
                execution_time_seconds=elapsed,
            )

        # Quality check
        qr = checker.check_l1(output.raw_output, output.agent_name)
        if not qr.passed:
            console.print(f"[yellow]Quality check failed for '{name}'[/yellow]")

        # Replace in run
        run.l1_outputs[idx] = output
        run.cost_records.extend(costs if 'costs' in dir() else [])
        run.total_cost_usd = runner.total_cost
        run.save(config.output_dir)
        console.print(f"[dim]Saved to disk[/dim]")

        # Cooldown before next
        if idx != failed_indices[-1]:
            console.print("[dim]Cooling down 10s...[/dim]")
            await asyncio.sleep(10)

    passed = sum(1 for o in run.l1_outputs if not o.raw_output.startswith("[ERROR"))
    console.print(f"\n[bold]Result: {passed}/10 agents now succeeded[/bold]")
    console.print(f"Total cost: ${run.total_cost_usd:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
