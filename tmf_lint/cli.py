"""
tmf-lint CLI.

Entry point: ``tmf-lint``

Commands:
  check   Run conformance checks against a live TMF API server.
  rules   List all available rules and their categories.
"""
from __future__ import annotations

import sys

import click
from rich.console import Console
from rich.table import Table

import tmf_lint
from tmf_lint.reporter import print_human, print_json
from tmf_lint.rules.base import CATEGORY_ORDER
from tmf_lint.rules.registry import list_all_rules
from tmf_lint.runner import run

_SUPPORTED_APIS = {638, 639, 641}


def _parse_apis(apis_str: str) -> list[int]:
    """Parse a comma-separated API number string, e.g. '638,639,641'."""
    result: list[int] = []
    for part in apis_str.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            n = int(part)
        except ValueError:
            raise click.BadParameter(f"'{part}' is not an integer API number")
        if n not in _SUPPORTED_APIS:
            raise click.BadParameter(
                f"TMF{n} is not supported in v0.1 (supported: "
                f"{', '.join(f'TMF{a}' for a in sorted(_SUPPORTED_APIS))})"
            )
        result.append(n)
    if not result:
        raise click.BadParameter("at least one API number is required")
    return result


def _parse_rules(rules_str: str | None) -> list[str] | None:
    """Parse a comma-separated category filter, or return None for all."""
    if not rules_str:
        return None
    categories = [r.strip() for r in rules_str.split(",") if r.strip()]
    for cat in categories:
        if cat not in CATEGORY_ORDER:
            raise click.BadParameter(
                f"Unknown rule category '{cat}'. "
                f"Valid categories: {', '.join(CATEGORY_ORDER)}"
            )
    return categories


@click.group()
@click.version_option(package_name="tmf-lint", prog_name="tmf-lint")
def main() -> None:
    """tmf-lint — Runtime conformance checker for TMForum Open API implementations."""


@main.command()
@click.option(
    "--url",
    required=True,
    help="Base URL of the TMF API server under test, e.g. http://localhost:8000",
)
@click.option(
    "--apis",
    default="638,639,641",
    show_default=True,
    help="Comma-separated TMF API numbers to check.",
)
@click.option(
    "--rules",
    default=None,
    help=(
        f"Comma-separated rule categories to run. "
        f"Default: all. Valid: {', '.join(CATEGORY_ORDER)}"
    ),
)
@click.option(
    "--format",
    "output_format",
    default="human",
    type=click.Choice(["human", "json"], case_sensitive=False),
    show_default=True,
    help="Output format.",
)
@click.option(
    "--timeout",
    default=30.0,
    show_default=True,
    type=float,
    help="Per-request HTTP timeout in seconds.",
)
def check(
    url: str,
    apis: str,
    rules: str | None,
    output_format: str,
    timeout: float,
) -> None:
    """Run conformance checks against a live TMF API server."""
    try:
        api_list = _parse_apis(apis)
        category_filter = _parse_rules(rules)
    except click.BadParameter as exc:
        raise click.UsageError(str(exc)) from exc

    report = run(
        base_url=url,
        apis=api_list,
        categories=category_filter,
        timeout=timeout,
    )

    if output_format == "json":
        print_json(report)
    else:
        print_human(report)

    sys.exit(0 if report.all_passed else 1)


@main.command("rules")
@click.option(
    "--apis",
    default=None,
    help="Filter by API numbers, e.g. '638,639'. Default: all.",
)
def list_rules(apis: str | None) -> None:
    """List all available lint rules and their categories."""
    api_filter: list[int] | None = None
    if apis:
        try:
            api_filter = _parse_apis(apis)
        except click.BadParameter as exc:
            raise click.UsageError(str(exc)) from exc

    all_rules = list_all_rules(apis=api_filter)

    console = Console()
    table = Table(
        title=f"tmf-lint v{tmf_lint.__version__} — Available Rules",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Rule ID", style="cyan", no_wrap=True)
    table.add_column("API", justify="center")
    table.add_column("Category", style="yellow")
    table.add_column("Description")

    for rule in all_rules:
        table.add_row(
            rule.rule_id,
            f"TMF{rule.api}",
            rule.category,
            rule.description,
        )

    console.print(table)
    n_apis = len({r.api for r in all_rules})
    console.print(f"\n[dim]{len(all_rules)} rules across {n_apis} API(s)[/dim]\n")
