import click
from rich.console import Console
from dotenv import load_dotenv

load_dotenv()
console = Console()

@click.command()
@click.argument('prd_file')
@click.option('--sprint', default=1, help='Sprint number')
@click.option('--completed', default='', help='Comma-separated completed stories')
@click.option('--blocked', default='', help='Comma-separated blocked stories')
@click.option('--velocity', default=1.0, help='Velocity factor from last sprint')
def negotiate(prd_file, sprint, completed, blocked, velocity):
    """Paste a PRD. Watch 5 agents negotiate. Get a sprint backlog."""
    from agents.product_agent import ProductAgent
    from agents.engineer_agent import EngineerAgent
    from agents.qa_agent import QAAgent
    from agents.negotiator_agent import NegotiatorAgent
    from agents.output_agent import OutputAgent

    console.print(f"[bold blue]PRD-to-Sprint Negotiator[/bold blue]")
    console.print(f"[dim]Sprint {sprint} | File: {prd_file}[/dim]\n")

    # Read PRD
    with open(prd_file, 'r') as f:
        prd_content = f.read()

    # Sprint context
    sprint_context = {
        "sprint": sprint,
        "completed": [s.strip() for s in completed.split(',') if s.strip()],
        "blocked": [s.strip() for s in blocked.split(',') if s.strip()],
        "velocity": velocity
    }

    # Run pipeline
    console.print("[bold]Agent 1/5:[/bold] Product Agent analyzing PRD...")
    product_output = ProductAgent().run(prd_content, sprint_context)

    console.print("[bold]Agent 2/5:[/bold] Engineer Agent estimating complexity...")
    engineer_output = EngineerAgent().run(product_output, sprint_context)

    console.print("[bold]Agent 3/5:[/bold] QA Agent reviewing requirements...")
    qa_output = QAAgent().run(product_output, engineer_output, sprint_context)

    console.print("[bold]Agent 4/5:[/bold] Negotiator Agent resolving conflicts...")
    negotiated = NegotiatorAgent().run(
        product_output, engineer_output, qa_output, sprint_context
    )

    console.print("[bold]Agent 5/5:[/bold] Output Agent formatting backlog...")
    final_output = OutputAgent().run(negotiated, sprint_context)

    # Save output
    output_file = f"sprint_{sprint}_backlog.md"
    with open(output_file, 'w') as f:
        f.write(final_output)

    console.print(f"\n[bold green]✓ Sprint {sprint} backlog ready:[/bold green] {output_file}")
    console.print(f"[dim]Open {output_file} to see your backlog.[/dim]")

if __name__ == '__main__':
    negotiate()
