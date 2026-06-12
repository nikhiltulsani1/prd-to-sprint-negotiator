import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

import time
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from dotenv import load_dotenv

load_dotenv()
console = Console()


def _run_agent(label: str, description: str, fn):
    """Run one agent step with timing and error handling.

    Returns the agent output, or calls sys.exit(1) on failure so the
    caller never sees a raw stack trace.
    """
    console.print(f"[bold blue]{label}[/bold blue]  [white]{description}[/white]")
    t0 = time.time()
    try:
        result = fn()
        elapsed = time.time() - t0
        console.print(f"[dim]   done in {elapsed:.1f}s[/dim]")
        return result
    except Exception as exc:
        elapsed = time.time() - t0
        console.print(f"[bold red]   FAILED after {elapsed:.1f}s: {exc}[/bold red]")
        sys.exit(1)


@click.command()
@click.argument('prd_file')
@click.option('--sprint',     default=1,    help='Sprint number')
@click.option('--completed',  default='',   help='Comma-separated completed feature names')
@click.option('--blocked',    default='',   help='Comma-separated blocked feature names')
@click.option('--velocity',   default=1.0,  help='Velocity factor from last sprint (e.g. 0.8)')
@click.option('--output',     default=None, help='Output file path (default: sprint_N_backlog.md)')
def negotiate(prd_file, sprint, completed, blocked, velocity, output):
    """Paste a PRD. Watch 5 agents negotiate. Get a sprint backlog."""
    from agents.product_agent import ProductAgent
    from agents.engineer_agent import EngineerAgent
    from agents.qa_agent import QAAgent
    from agents.negotiator_agent import NegotiatorAgent
    from agents.output_agent import OutputAgent

    console.print(Panel(
        f"[bold white]PRD-to-Sprint Negotiator[/bold white]\n"
        f"[dim]Sprint {sprint}  |  {prd_file}  |  velocity {velocity}[/dim]",
        border_style="blue",
        padding=(0, 2),
    ))
    console.print()

    with open(prd_file, 'r', encoding='utf-8') as f:
        prd_content = f.read()

    sprint_context = {
        "sprint":     sprint,
        "completed":  [s.strip() for s in completed.split(',') if s.strip()],
        "blocked":    [s.strip() for s in blocked.split(',') if s.strip()],
        "velocity":   velocity,
        "project_name": "Project",
    }

    pipeline_start = time.time()

    product_output = _run_agent(
        "Agent 1/5:", "Product Agent  — extracting features from PRD",
        lambda: ProductAgent().run(prd_content, sprint_context),
    )
    sprint_context["project_name"] = product_output.get("project_name", "Project")

    engineer_output = _run_agent(
        "Agent 2/5:", "Engineer Agent — estimating complexity and flagging risks",
        lambda: EngineerAgent().run(product_output, sprint_context),
    )

    qa_output = _run_agent(
        "Agent 3/5:", "QA Agent       — identifying test requirements and gaps",
        lambda: QAAgent().run(product_output, engineer_output, sprint_context),
    )

    negotiated = _run_agent(
        "Agent 4/5:", "Negotiator     — resolving conflicts and fitting sprint capacity",
        lambda: NegotiatorAgent().run(product_output, engineer_output, qa_output, sprint_context),
    )

    final_output = _run_agent(
        "Agent 5/5:", "Output Agent   — formatting the sprint backlog",
        lambda: OutputAgent().run(negotiated, sprint_context),
    )

    total_time = time.time() - pipeline_start

    output_file = output or f"sprint_{sprint}_backlog.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_output)

    # summary panel
    included   = negotiated.get("included_features", [])
    excluded   = negotiated.get("excluded_features", [])
    committed  = negotiated.get("total_committed_points", 0)
    capacity   = negotiated.get("effective_capacity", int(40 * velocity))
    goal       = negotiated.get("sprint_goal", "")
    goal_short = goal[:77] + "..." if len(goal) > 80 else goal

    summary = Table.grid(padding=(0, 2))
    summary.add_column(style="dim")
    summary.add_column()
    summary.add_row("Sprint",       str(sprint))
    summary.add_row("Goal",         goal_short)
    summary.add_row("Committed",    f"{len(included)} features  /  {committed} of {capacity} pts")
    summary.add_row("Excluded",     f"{len(excluded)} features deferred")
    summary.add_row("Output",       output_file)
    summary.add_row("Total time",   f"{total_time:.1f}s")

    console.print()
    console.print(Panel(summary, title="[bold green]Sprint plan ready[/bold green]", border_style="green"))


if __name__ == '__main__':
    negotiate()
