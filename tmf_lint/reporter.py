"""
tmf-lint — Output formatters.

Two formats are supported:

* **human** (default) — coloured Rich terminal output matching the design
  in the project spec.
* **json** — compact JSON written to stdout; suitable for CI/CD parsing.

Both formatters receive a ``LintReport`` and write to stdout.
"""
from __future__ import annotations

import json
import sys

from rich.console import Console
from rich.text import Text

from tmf_lint.result import LintReport, RuleResult, Severity

# API number → human-readable name
_API_NAMES: dict[int, str] = {
    638: "TMF638 Service Inventory",
    639: "TMF639 Resource Inventory",
    641: "TMF641 Service Ordering",
}

# Severity → Rich colour
_SEVERITY_COLOUR: dict[Severity, str] = {
    Severity.PASS: "green",
    Severity.FAIL: "red",
    Severity.SKIP: "yellow",
}

# Severity → terminal glyph
_SEVERITY_GLYPH: dict[Severity, str] = {
    Severity.PASS: "✅",
    Severity.FAIL: "❌",
    Severity.SKIP: "⏭ ",
}


def _rule_line(result: RuleResult) -> Text:
    """Build a single Rich ``Text`` line for one rule result."""
    glyph = _SEVERITY_GLYPH[result.severity]
    colour = _SEVERITY_COLOUR[result.severity]
    text = Text()
    text.append(f"  {glyph} ", style=colour)
    text.append(result.description)
    if result.message:
        text.append(f" — {result.message}", style="dim")
    return text


def print_human(report: LintReport, *, console: Console | None = None) -> None:
    """Print a coloured human-readable report to the terminal.

    Args:
        report:  The completed lint report.
        console: Optional Rich ``Console`` to write to (defaults to stdout).
    """
    con = console or Console()

    # ── Header ────────────────────────────────────────────────────────────────
    version_line = "tmf-lint — TMF API conformance checker"
    api_names = ", ".join(f"TMF{a}" for a in sorted(report.apis))
    con.print(f"\n[bold cyan]{version_line}[/bold cyan]")
    con.print(f"Checking [underline]{report.base_url}[/underline] against {api_names}…\n")

    # ── Per-API results ───────────────────────────────────────────────────────
    for api, results in report.by_api().items():
        api_label = _API_NAMES.get(api, f"TMF{api}")
        con.print(f"[bold]{api_label}[/bold]")
        for r in results:
            con.print(_rule_line(r))
        con.print()

    # ── Summary ───────────────────────────────────────────────────────────────
    colour = "green" if report.all_passed else "red"
    summary = (
        f"[{colour}]Summary: {report.n_passed} passed, "
        f"{report.n_failed} failed"
    )
    if report.n_skipped:
        summary += f", {report.n_skipped} skipped"
    summary += f"[/{colour}]"
    con.print(summary)

    exit_code = 0 if report.all_passed else 1
    con.print(f"Exit code: {exit_code}\n")


def print_json(report: LintReport) -> None:
    """Print a machine-readable JSON report to stdout.

    Args:
        report: The completed lint report.
    """
    sys.stdout.write(json.dumps(report.to_dict(), indent=2))
    sys.stdout.write("\n")
