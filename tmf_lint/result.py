"""
tmf-lint — RuleResult and LintReport data classes.

These are the only types that flow between the rule engine, runner, and reporter.
No domain logic lives here — just plain data.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    """Outcome of a single rule execution."""

    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"  # prerequisite rule failed; this rule was not attempted


@dataclass
class RuleResult:
    """Outcome of executing one rule against a live server."""

    rule_id: str
    api: int
    category: str
    description: str
    passed: bool
    skipped: bool = False
    message: str = ""

    @property
    def severity(self) -> Severity:
        """Convenience property for reporters."""
        if self.skipped:
            return Severity.SKIP
        return Severity.PASS if self.passed else Severity.FAIL

    def to_dict(self) -> dict:
        """Serialise to a plain dict (used for JSON output)."""
        return {
            "rule_id": self.rule_id,
            "api": self.api,
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "message": self.message,
        }


@dataclass
class LintReport:
    """Aggregated results from a full tmf-lint run."""

    base_url: str
    apis: list[int]
    results: list[RuleResult] = field(default_factory=list)

    # ── Computed counts ──────────────────────────────────────────────────────

    @property
    def n_passed(self) -> int:
        return sum(1 for r in self.results if r.passed and not r.skipped)

    @property
    def n_failed(self) -> int:
        return sum(1 for r in self.results if not r.passed and not r.skipped)

    @property
    def n_skipped(self) -> int:
        return sum(1 for r in self.results if r.skipped)

    @property
    def all_passed(self) -> bool:
        """True when every non-skipped rule passed."""
        return self.n_failed == 0

    # ── Grouping helpers used by reporter ────────────────────────────────────

    def by_api(self) -> dict[int, list[RuleResult]]:
        """Return results grouped by API number, preserving run order."""
        groups: dict[int, list[RuleResult]] = {}
        for r in self.results:
            groups.setdefault(r.api, []).append(r)
        return groups

    def to_dict(self) -> dict:
        """Serialise to a plain dict (used for JSON output)."""
        return {
            "base_url": self.base_url,
            "apis": self.apis,
            "summary": {
                "passed": self.n_passed,
                "failed": self.n_failed,
                "skipped": self.n_skipped,
                "total": len(self.results),
            },
            "results": [r.to_dict() for r in self.results],
        }
