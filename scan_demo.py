from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from spyv import auto, provider, scan, terminal

load_dotenv()
console = Console()


def build_client():
    provider_name = os.getenv("SPYV_PROVIDER", "auto")
    model = os.getenv("SPYV_MODEL", "gpt-4o")
    base_url = os.getenv("SPYV_BASE_URL")
    if provider_name == "auto":
        return auto(model=model), model
    return provider(provider_name, model=model, base_url=base_url), model


def banner() -> None:
    title = Text()
    title.append("SPYV", style="bold #7c3aed")
    title.append(" scan", style="bold #4ee88c")
    console.print(Panel(title, subtitle="audit every prompt in a project", border_style="#7c3aed"))


def main() -> None:
    if not any(os.getenv(k) for k in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY")):
        console.print("[red]No API key found.[/red] Copy .env.example to .env and add your key.")
        sys.exit(1)

    target = sys.argv[1] if len(sys.argv) > 1 else str(Path(__file__).parent / "sample_project")
    client, model = build_client()

    banner()
    console.print(f"scanning: [bold]{target}[/bold]   model: [bold]{model}[/bold]\n")

    with console.status("[#7c3aed]Discovering prompts and auditing each one ...", spinner="dots"):
        report = scan(root=target, llm=client, model=model)

    terminal.render_project_report(report)

    worst = report.results[0] if report.results else None
    if worst and worst.top_fix:
        body = Text()
        body.append("Weakest prompt: ", style="bold")
        body.append(f"{worst.identifier} ({worst.file})\n")
        body.append("Fix first: ", style="bold green")
        body.append(worst.top_fix)
        console.print(Panel(body, title="do this first", border_style="#4ee88c"))


if __name__ == "__main__":
    main()
