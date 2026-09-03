"""How much of your prompt surface can a scanner even read? -- no API key.

Every prompt-security tool starts by extracting prompts from source. That first
step is usually assumed to work. It does not always work, and the share it
misses is measurable.

A *prompt site* is a source location that supplies instruction text to a model.
The useful property is that a site is statically identifiable even when its
argument is not: `Task(description=self._build())` is unmistakably a prompt
site whose content cannot be read. So sites can be counted from source, and
each one classified by whether its text is recoverable.

Nothing here calls a model.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from spyv.bench.headroom import run_headroom_project
from spyv.bench.ladder import LEVEL_NAMES, measure_repo
from spyv.bench.scaffolding import classify_path, stratify
from spyv.bench.visibility import run_visibility

os.environ.setdefault("SPYV_OUT", "pretty")
console = Console()

TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_project")

CLASS_STYLE = {"static": "green", "partial": "yellow", "opaque": "red"}
CLASS_MEANING = {
    "static": "text is in the source; a scanner reads it",
    "partial": "literal skeleton with runtime holes; frame readable, filling not",
    "opaque": "text is not in the source here; a scanner sees nothing",
}


def main() -> None:
    title = Text()
    title.append("SPYV", style="bold #7c3aed")
    title.append(" prompt visibility", style="bold #4ee88c")
    console.print(
        Panel(
            title,
            subtitle="what a static scanner can and cannot read -- no API key",
            border_style="#7c3aed",
        )
    )

    result = run_visibility(TARGET, name=TARGET.name)
    if result.error or not result.sites:
        console.print(f"[red]No prompt sites found in {TARGET}[/red] {result.error or ''}")
        return
    metrics = result.metrics()

    console.print(
        f"\n[bold]1. Enumerate[/bold] — {len(result.sites)} prompt sites in "
        f"{result.files_scanned} Python files under [cyan]{TARGET}[/cyan]"
    )

    console.print("\n[bold]2. Classify[/bold] — can the text at each site be recovered?")
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("class")
    table.add_column("where", style="cyan")
    table.add_column("construct")
    table.add_column("text, or why not")
    for s in sorted(result.sites, key=lambda x: (x.visibility, x.file, x.line or 0)):
        detail = (s.text or "")[:44] if s.visibility != "opaque" else f"[dim]{s.reason}[/dim]"
        table.add_row(
            Text(s.visibility, style=CLASS_STYLE[s.visibility]),
            f"{Path(s.file).name}:{s.line}",
            s.construct,
            detail,
        )
    console.print(table)

    console.print()
    for cls, meaning in CLASS_MEANING.items():
        console.print(f"  [{CLASS_STYLE[cls]}]{cls:<8}[/{CLASS_STYLE[cls]}] {meaning}")

    spv_p = metrics["spv_partial"] * 100
    spv_s = metrics["spv_full"] * 100
    console.print(
        f"\n[bold]3. Score[/bold] — static prompt visibility\n"
        f"  SPV(static)  = {spv_s:.1f}%   text fully recoverable\n"
        f"  SPV(partial) = [bold]{spv_p:.1f}%[/bold]   counting skeletons as readable\n"
        f"  [red]{100 - spv_p:.1f}% of this project's prompt surface is invisible to "
        f"source reading.[/red]"
    )

    console.print("\n[bold]4. Why the opaque ones resist[/bold]")
    if metrics["opaque_reasons"]:
        for reason, n in metrics["opaque_reasons"].items():
            console.print(f"  {n} x [red]{reason}[/red]")
        head = run_headroom_project(TARGET, name=TARGET.name)
        if head.get("opaque_sites"):
            console.print(
                f"  [dim]headroom buckets: {head['buckets']}  "
                f"(would a stronger analyser reach them?)[/dim]"
            )
    else:
        console.print("  [green]none — every site was recoverable[/green]")

    console.print(
        "\n[bold]5. Would a stronger analyser help?[/bold] Five levels, each strictly "
        "stronger:"
    )
    ladder = Table(show_header=True, header_style="bold", box=None)
    ladder.add_column("level")
    ladder.add_column("adds")
    ladder.add_column("static", justify="right")
    ladder.add_column("partial", justify="right")
    ladder.add_column("opaque", justify="right")
    ladder.add_column("recoverable", justify="right")
    prev = None
    for lvl in range(5):
        c = measure_repo(TARGET, lvl)
        n = c["static"] + c["partial"] + c["opaque"]
        rate = (c["static"] + c["partial"]) / n * 100 if n else 0.0
        delta = "" if prev is None else f"  ({rate - prev:+.1f})"
        ladder.add_row(
            f"L{lvl}",
            LEVEL_NAMES[lvl] if lvl < len(LEVEL_NAMES) else "",
            str(c["static"]),
            str(c["partial"]),
            str(c["opaque"]),
            f"{rate:.1f}%{delta}",
        )
        prev = rate
    console.print(ladder)
    console.print(
        "  [dim]If the curve flattens, the residue belongs to the programs rather\n"
        "  than to the analyser. That is the point of measuring a frontier instead\n"
        "  of quoting a single number.[/dim]"
    )

    console.print("\n[bold]6. Production code or scaffolding?[/bold]")
    strat = stratify(TARGET.name, result.sites)
    sm = strat.metrics()
    for label, key in (("production", "production"), ("scaffolding", "scaffolding")):
        block = sm[key]
        if not block["sites"]:
            console.print(f"  {label:<12} no sites")
            continue
        console.print(
            f"  {label:<12} {block['sites']:>3} sites   "
            f"recoverable {block['spv_partial'] * 100:.1f}%"
        )
    share = sm["scaffolding_share"]
    console.print(
        f"  [dim]scaffolding share {share * 100:.1f}% — tests and examples write prompts as\n"
        f"  literals for readability, so pooling them flatters the figure. Grade the\n"
        f"  stratum you actually ship.[/dim]"
    )
    console.print(
        f"\n[dim]classify_path() decides the split, e.g. "
        f"tests/x.py -> {classify_path('tests/x.py')}, "
        f"src/x.py -> {classify_path('src/x.py')}[/dim]"
    )


if __name__ == "__main__":
    main()
