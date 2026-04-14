"""
tmf-lint — Async rule runner.

The runner owns the execution loop:

1.  Instantiate a ``LintClient`` bound to the target URL.
2.  Load all rules matching the requested APIs and category filter.
3.  Execute each rule in turn; collect ``RuleResult`` objects.
4.  Return a ``LintReport``.

Rules are always executed in category order (HTTP → mandatory-fields →
lifecycle → referential → pagination) so that HTTP rules can create
entities and deposit their IDs in the context before later rules need them.
"""
from __future__ import annotations

import asyncio

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import LintReport
from tmf_lint.rules.registry import load_rules


async def run_async(
    base_url: str,
    apis: list[int],
    categories: list[str] | None = None,
    timeout: float = 30.0,
) -> LintReport:
    """Execute all applicable rules against *base_url* and return a report.

    Args:
        base_url:   Base URL of the TMF API implementation under test.
        apis:       API numbers to check (e.g. ``[638, 639, 641]``).
        categories: If set, only rules in these categories are executed.
        timeout:    Per-request HTTP timeout in seconds.

    Returns:
        A ``LintReport`` containing all rule results.
    """
    ctx = LintContext(base_url=base_url, apis=apis, rule_filter=categories)
    report = LintReport(base_url=base_url, apis=apis)
    rules = load_rules(apis=apis, categories=categories)

    async with LintClient(base_url=base_url, timeout=timeout) as client:
        for rule in rules:
            result = await rule.check(client, ctx)
            report.results.append(result)

    return report


def run(
    base_url: str,
    apis: list[int],
    categories: list[str] | None = None,
    timeout: float = 30.0,
) -> LintReport:
    """Synchronous wrapper around :func:`run_async`.

    Use this when calling tmf-lint programmatically from non-async code.
    """
    return asyncio.run(run_async(base_url, apis, categories, timeout))
