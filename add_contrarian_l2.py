"""Generate and run additional contrarian/lateral L2 agents, append to existing run, re-run L3."""

import asyncio
import logging
import re
import time

from rich.console import Console
from rich.logging import RichHandler

from deep_research.config import Config
from deep_research.context_manager import assemble_l3_input, count_tokens
from deep_research.models import AgentOutput, ResearchRun
from deep_research.prompt_builder import PromptBuilder
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

N_CONTRARIAN_AGENTS = 3

CONTRARIAN_GENERATION_PROMPT = """You are a research architect generating ONLY contrarian, lateral, and genuinely surprising deep research prompts for {COMPANY_NAME}.

You have access to the L1.5 consolidation from a comprehensive research project. The project has already investigated conventional strategic questions thoroughly (competitive landscape, regulatory, supply chain, installer channels, geographic expansion, financial engineering, etc.). Those are DONE. Do NOT generate prompts that overlap with conventional analysis.

Your job is to generate exactly {N_AGENTS} research prompts that investigate ideas an industry insider would say "I never would have thought of that." Each prompt will be run by an independent deep research agent with full web access.

L1.5 CONSOLIDATION (for context on company assets, capabilities, and position):

{L15_OUTPUT}

---

WHAT WE ALREADY HAVE L2 DEEP DIVES ON (do NOT duplicate):

{EXISTING_L2_TOPICS}

---

GENERATE {N_AGENTS} PROMPTS. Each one MUST be one of these types:

1. **CROSS-INDUSTRY TRANSPLANT**: A business model or revenue stream that works in a completely different industry, applied to this company's specific assets. Name the source industry, the source company, and what exactly they did. Then hypothesize how it would work here. Example: "Rolls-Royce sells 'power by the hour' instead of jet engines. Could {COMPANY_NAME} sell 'energy resilience as a service' instead of batteries, using the same TotalCare model?"

2. **ASSET REPURPOSING**: Take a specific asset the company owns (installed hardware fleet, data stream, manufacturing facility, software platform, customer relationships, certifications) and propose using it for something nobody in the industry is doing. Example: "Gridshare processes 40 billion data points monthly. Could that consumption data be packaged as a predictive analytics product for property insurers pricing climate risk?"

3. **BUSINESS MODEL INVERSION**: What if the company flipped its model? Gave away the hardware and charged for the service? Became a buyer instead of a seller? Targeted the opposite customer segment? Example: "What if Lunar became a data center backup power provider, using its battery + Gridshare stack to sell UPS-as-a-service to edge computing facilities instead of homeowners?"

4. **NON-OBVIOUS CUSTOMER SEGMENT**: Who would benefit from this company's capabilities that nobody is currently targeting? Think beyond residential and C&I. Example: "Could Lunar's modular battery + smart panel system serve cannabis grow operations, which have extreme energy costs and unreliable grid access?"

5. **PLATFORM PLAY**: If the company controls an installed base, a network, or a data stream — what could be built on top of it that goes beyond the current product category?

For each prompt, follow this format:

L2 AGENT {N}: {DESCRIPTIVE TITLE}
SOURCE: LATERAL — {type from above}
PRIORITY: High

```
You are a {EXPERT_PERSONA} investigating a specific non-obvious strategic hypothesis about {COMPANY_NAME}.

CONTEXT:
{2-3 paragraphs of relevant facts from the L1.5 consolidation}

HYPOTHESIS TO INVESTIGATE:
{Specific, concrete hypothesis — not vague}

SPECIFIC RESEARCH QUESTIONS:
1. {Primary validation question}
2. {Cross-industry comparable — who has done something like this in ANY industry?}
3. {Market sizing — how big is the addressable opportunity?}
4. {Feasibility — what capabilities are needed, does the company have them?}
5. {Failure modes — what would make this not work?}

RESEARCH GUIDANCE:
- {Specific sources, companies, and databases to investigate}
- {Named cross-industry comparables to research}

OUTPUT FORMAT:
1. EVIDENCE FOR THE HYPOTHESIS
2. EVIDENCE AGAINST THE HYPOTHESIS
3. COMPARABLE EXAMPLES (prioritize cross-industry)
4. FEASIBILITY ASSESSMENT
5. MAGNITUDE ESTIMATE
6. CONFIDENCE ASSESSMENT
7. CITATIONS
```

QUALITY REQUIREMENTS:
- Each prompt must be 400-800 words and SELF-CONTAINED
- Each must name SPECIFIC cross-industry comparables to research
- Each must be concrete enough that a researcher knows exactly what to search for
- NONE should overlap with the existing L2 topics listed above
- The "I never would have thought of that" test must pass for each one
"""


def parse_l2_prompts(gen_output: str) -> tuple[list[str], list[str]]:
    """Parse L2 prompts from generation output."""
    prompts = []
    names = []

    agent_pattern = re.compile(
        r"L2\s+AGENT\s+(\d+)\s*:\s*(.+?)(?:\n|$)",
        re.IGNORECASE,
    )
    code_blocks = re.findall(r"```(?:\w*\n)?(.*?)```", gen_output, re.DOTALL)
    agent_matches = list(agent_pattern.finditer(gen_output))

    if code_blocks and agent_matches:
        for match in agent_matches:
            name = match.group(2).strip().rstrip("*").strip()
            pos = match.end()

            next_block = None
            for block in code_blocks:
                block_pos = gen_output.find(block, pos - 100)
                if block_pos >= pos - 100:
                    next_block = block.strip()
                    break

            if next_block and len(next_block) > 100:
                prompts.append(next_block)
                names.append(name)

    # Fallback
    if len(prompts) < 2 and len(code_blocks) >= 2:
        prompts = []
        names = []
        for i, block in enumerate(code_blocks):
            block = block.strip()
            if len(block) > 100:
                prompts.append(block)
                names.append(f"Contrarian L2 Agent {i + 1}")

    logger.info(f"Parsed {len(prompts)} contrarian L2 prompts")
    return prompts, names


async def main(run_id: str, n_agents: int = N_CONTRARIAN_AGENTS) -> None:
    config = Config()
    run = ResearchRun.load(config.output_dir, run_id)

    console.print(f"\n[bold]Adding {n_agents} contrarian L2 agents to {run_id}[/bold]")
    console.print(f"Existing L2 agents: {len(run.l2_outputs)}")
    console.print(f"Current cost: ${run.total_cost_usd:.2f}\n")

    runner = ResearchRunner(config)
    runner.total_cost = run.total_cost_usd

    # Build the existing L2 topics list so we don't duplicate
    existing_topics = "\n".join(
        f"- {o.agent_name}" for o in run.l2_outputs
    )

    # Build the generation prompt
    gen_prompt = CONTRARIAN_GENERATION_PROMPT.replace(
        "{COMPANY_NAME}", run.company_name
    ).replace(
        "{N_AGENTS}", str(n_agents)
    ).replace(
        "{L15_OUTPUT}", run.l15_output or ""
    ).replace(
        "{EXISTING_L2_TOPICS}", existing_topics
    )

    # Step 1: Generate contrarian prompts using Opus
    logger.info("Generating contrarian L2 prompts with Opus...")
    gen_text, gen_costs = await runner.run_synthesis(
        gen_prompt,
        task_id="contrarian_l2_generation",
    )
    run.cost_records.extend(gen_costs)
    run.total_cost_usd = runner.total_cost

    prompts, names = parse_l2_prompts(gen_text)

    if not prompts:
        console.print("[red]Failed to parse any prompts from generation output[/red]")
        console.print(gen_text[:2000])
        return

    # Save the prompts for inspection
    for i, (prompt, name) in enumerate(zip(prompts, names)):
        idx = len(run.l2_prompts) + 1
        run.l2_prompts.append(prompt)
        run.l2_prompt_names.append(name)

    run.save(config.output_dir)
    console.print(f"\n[green]Generated {len(prompts)} contrarian prompts:[/green]")
    for name in names:
        console.print(f"  • {name}")

    # Step 2: Run each contrarian agent sequentially
    console.print(f"\n[bold]Running {len(prompts)} contrarian agents...[/bold]\n")
    cooldown = 10

    for i, (prompt, name) in enumerate(zip(prompts, names)):
        agent_num = len(run.l2_outputs) + 1
        task_id = f"l2_contrarian_{i + 1:02d}"

        if i > 0:
            logger.info(f"  [{task_id}] Cooling down {cooldown}s...")
            await asyncio.sleep(cooldown)

        logger.info(f"  [{task_id}] Starting: {name} ({i + 1}/{len(prompts)})")
        start = time.time()

        try:
            text, costs = await runner.run_research(prompt=prompt, task_id=task_id)
            elapsed = time.time() - start
            total_cost = sum(c.estimated_cost_usd for c in costs)
            search_count = sum(c.search_count for c in costs)

            logger.info(
                f"  [{task_id}] Complete: {name} "
                f"({elapsed:.0f}s, ${total_cost:.2f}, {search_count} searches)"
            )

            output = AgentOutput(
                agent_name=name,
                agent_type="l2",
                prompt=prompt,
                raw_output=text,
                token_count=sum(c.output_tokens for c in costs),
                search_count=search_count,
                execution_time_seconds=elapsed,
                cost_usd=total_cost,
            )
        except Exception as e:
            elapsed = time.time() - start
            logger.error(f"  [{task_id}] Failed: {name} ({elapsed:.0f}s): {e}")
            output = AgentOutput(
                agent_name=name,
                agent_type="l2",
                prompt=prompt,
                raw_output=f"[ERROR: Research task failed: {e}]",
                execution_time_seconds=elapsed,
            )

        run.l2_outputs.append(output)
        run.cost_records.extend(costs)
        run.total_cost_usd = runner.total_cost
        run.save(config.output_dir)
        logger.info(f"  [{task_id}] Saved to disk ({agent_num} total L2 agents)")

    # Step 3: Re-run L3 synthesis (L3a + L3b) with expanded corpus
    console.print(f"\n[bold]Re-running L3a synthesis with {len(run.l2_outputs)} L2 agents...[/bold]\n")

    prompt_builder = PromptBuilder(config)

    # L3a: synthesis draft
    l3a_prompt = prompt_builder.build_l3a(
        company_name=run.company_name,
        run=run,
    )
    token_count = count_tokens(l3a_prompt)
    logger.info(f"[L3a] Input size: {token_count} tokens")

    l3a_text, l3a_costs = await runner.run_synthesis(
        l3a_prompt,
        task_id="l3a_synthesis_v2",
        model=config.synthesis_model,
    )
    run.cost_records.extend(l3a_costs)
    run.total_cost_usd = runner.total_cost
    run.l3a_draft = l3a_text
    run.save(config.output_dir)

    console.print(f"\n[bold]Re-running L3b refinement...[/bold]\n")

    # L3b: refinement to final output
    l3b_prompt = prompt_builder.build_l3b(
        company_name=run.company_name,
        run=run,
        l3a_output=l3a_text,
    )
    token_count = count_tokens(l3b_prompt)
    logger.info(f"[L3b] Input size: {token_count} tokens")

    l3b_text, l3b_costs = await runner.run_synthesis(
        l3b_prompt,
        task_id="l3b_refinement_v2",
        model=config.synthesis_model,
    )
    run.cost_records.extend(l3b_costs)
    run.total_cost_usd = runner.total_cost

    checker = QualityChecker()
    qr = checker.check_l3(l3b_text, pipeline_mode=config.pipeline_mode)
    run.quality_reports.append(qr)

    run.l3b_final = l3b_text
    run.status = "complete"
    run.save(config.output_dir)

    console.print(f"\n[bold green]Done![/bold green]")
    console.print(f"Total L2 agents: {len(run.l2_outputs)} ({len(prompts)} contrarian added)")
    console.print(f"L3 quality: {'PASS' if qr.passed else 'FAIL'} ({qr.pass_rate:.0%})")
    console.print(f"Total cost: ${run.total_cost_usd:.2f}")
    console.print(f"Output: {config.output_dir / run_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Add contrarian L2 agents to an existing run and re-run L3."
    )
    parser.add_argument("run_id", help="The run ID to extend (e.g. run_7070d661)")
    parser.add_argument(
        "--count", type=int, default=N_CONTRARIAN_AGENTS,
        help=f"Number of contrarian agents to add (default: {N_CONTRARIAN_AGENTS})",
    )
    args = parser.parse_args()
    asyncio.run(main(args.run_id, n_agents=args.count))
