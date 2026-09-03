"""SARIF export and CI gating — no API key.

A finding that lives in a terminal is a finding nobody acts on. SARIF 2.1.0 is
the format GitHub code scanning, Azure DevOps and most SAST viewers already
read, so spyv emits it and CI can fail the build on it.

Everything here is deterministic. The verdicts come from spyv's regex checker
tier, not from a model, so this demo runs offline and gives the same answer
every time -- which is the only kind of check that belongs in a merge gate.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

import spyv
from spyv.contracts import ProjectPromptResult, ProjectReport
from spyv.report.sarif import project_report_to_sarif, sarif_fingerprints, write_sarif

os.environ.setdefault("SPYV_OUT", "pretty")
console = Console()

TARGET = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_project")
OUT = Path("spyv.sarif")

# The gate: fail the build at this verdict or worse.
FAIL_ON = "unsafe"
RANK = {"ship": 0, "fix_first": 1, "unsafe": 2}


def deterministic_verdict(text: str) -> tuple[str, int, str | None, str | None]:
    """Grade one prompt using only the regex checkers.

    Returns (verdict, n_findings, max_severity, top_fix). An embedded credential
    is treated as unsafe because it is an exposure regardless of model opinion;
    weaker signals are fix_first.

    Note the argument order. run_checkers(system_prompt, response) scans the
    *response* and uses the prompt only for leak comparison, because its usual
    job is checking what an agent said at runtime. To scan prompt text itself we
    put the prompt in the response slot and leave the prompt slot empty.

    Passing the prompt as *both* arguments would be the tempting mistake: every
    prompt then matches the verbatim-overlap leak rule against itself, and the
    demo reports a finding on every file that was never earned.
    """
    hits = spyv.run_checkers("", text)
    if not hits:
        return "ship", 0, "info", "No deterministic finding; nothing to fix."

    order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    worst = max(hits, key=lambda h: order.get(h.severity, 0))
    verdict = "unsafe" if worst.checker == "secrets" else "fix_first"
    fix = (
        f"Remove the {worst.label} from the prompt text and read it from the "
        "environment at call time."
    )
    return verdict, len(hits), worst.severity, fix


def main() -> None:
    title = Text()
    title.append("SPYV", style="bold #7c3aed")
    title.append(" SARIF + CI gate", style="bold #4ee88c")
    console.print(
        Panel(
            title,
            subtitle="deterministic findings in the format your code scanner already reads",
            border_style="#7c3aed",
        )
    )

    prompts, files_scanned = spyv.discover(TARGET)
    console.print(
        f"\n[bold]1. Discover[/bold] — {len(prompts)} prompts across "
        f"{files_scanned} files in [cyan]{TARGET}[/cyan]"
    )

    results: list[ProjectPromptResult] = []
    for p in prompts:
        verdict, n, sev, fix = deterministic_verdict(p.system_prompt or "")
        results.append(
            ProjectPromptResult(
                file=p.file,
                line=p.line or 1,
                source_kind=p.source_kind,
                identifier=p.identifier,
                overall_score={"ship": 8.5, "fix_first": 5.0, "unsafe": 2.0}[verdict],
                overall_verdict=verdict,
                n_vulnerabilities=n,
                max_severity=sev,
                top_fix=fix,
            )
        )

    tally = {"ship": 0, "fix_first": 0, "unsafe": 0}
    for r in results:
        tally[r.overall_verdict] += 1

    report = ProjectReport(
        root=str(TARGET),
        generated_at="1970-01-01T00:00:00Z",  # fixed so the demo is byte-stable
        model_used="deterministic-checkers",
        files_scanned=files_scanned,
        prompts_found=len(prompts),
        prompts_analyzed=len(results),
        ship=tally["ship"],
        fix_first=tally["fix_first"],
        unsafe=tally["unsafe"],
        results=results,
    )

    console.print("\n[bold]2. Grade[/bold] — regex checker tier only, no model")
    table = Table(show_header=True, header_style="bold", box=None)
    table.add_column("verdict")
    table.add_column("where", style="cyan")
    table.add_column("kind")
    table.add_column("finding")
    style = {"unsafe": "bold red", "fix_first": "yellow", "ship": "green"}
    for r in sorted(results, key=lambda x: -RANK[x.overall_verdict]):
        table.add_row(
            Text(r.overall_verdict, style=style[r.overall_verdict]),
            f"{r.file}:{r.line}",
            r.source_kind,
            f"{r.n_vulnerabilities} ({r.max_severity})" if r.n_vulnerabilities else "clean",
        )
    console.print(table)

    document = project_report_to_sarif(report, tool_version=spyv.__version__)
    write_sarif(document, OUT)
    n_sarif = len(document["runs"][0]["results"])
    console.print(
        f"\n[bold]3. Export[/bold] — SARIF {document['version']} written to "
        f"[cyan]{OUT}[/cyan] ({n_sarif} results, {OUT.stat().st_size:,} bytes)"
    )
    first = json.dumps(document["runs"][0]["results"][:1], indent=2) if n_sarif else "[]"
    console.print(Syntax(first[:700], "json", theme="ansi_dark", word_wrap=True))

    prints = sarif_fingerprints(document)
    console.print(
        f"\n[bold]4. Stable fingerprints[/bold] — {len(prints)} partial fingerprints.\n"
        "  These are what let a scanner say [i]new since last run[/i] instead of\n"
        "  re-reporting the same finding on every commit."
    )

    worst = max((RANK[r.overall_verdict] for r in results), default=0)
    gate_failed = worst >= RANK[FAIL_ON]
    console.print(f"\n[bold]5. Gate[/bold] — --fail-on [cyan]{FAIL_ON}[/cyan]")
    if gate_failed:
        console.print(
            f"  [bold red]FAIL[/bold red] exit 1 — {tally['unsafe']} unsafe prompt(s). "
            "CI stops the merge."
        )
    else:
        console.print("  [bold green]PASS[/bold green] exit 0 — nothing at or above the gate.")

    console.print(
        "\n[dim]In CI: spyv scan . --sarif spyv.sarif --fail-on unsafe, then upload\n"
        "spyv.sarif with github/codeql-action/upload-sarif.[/dim]"
    )
    raise SystemExit(1 if gate_failed else 0)


if __name__ == "__main__":
    main()
