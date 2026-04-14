"""
tmf-lint — BaseRule and category constants.

Every lint rule is a subclass of ``BaseRule``.  The rule engine discovers
subclasses automatically via ``tmf_lint.rules.registry``; adding a new rule
means creating a new class — no registration call required.

Rule lifecycle
──────────────
1.  The runner instantiates each rule once per run.
2.  It calls ``rule.check(client, ctx)`` and stores the returned ``RuleResult``.
3.  Rules may read from *ctx* (to use IDs created by earlier rules) and may
    write to *ctx* (to leave IDs for later rules).  Rules must never raise —
    they should catch exceptions and return ``self.fail(...)`` instead.

Category constants
──────────────────
Use these constants in rule class attributes and ``--rules`` filter values.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult

# ── Category identifiers (also used as --rules filter values) ─────────────────

CATEGORY_HTTP = "http"
CATEGORY_MANDATORY_FIELDS = "mandatory-fields"
CATEGORY_LIFECYCLE = "lifecycle"
CATEGORY_REFERENTIAL = "referential"
CATEGORY_PAGINATION = "pagination"

# Execution order: HTTP rules create data that later categories consume.
CATEGORY_ORDER: list[str] = [
    CATEGORY_HTTP,
    CATEGORY_MANDATORY_FIELDS,
    CATEGORY_LIFECYCLE,
    CATEGORY_REFERENTIAL,
    CATEGORY_PAGINATION,
]


class BaseRule(ABC):
    """Abstract base class for all tmf-lint rules.

    Subclasses must declare four class attributes::

        rule_id     = "TMF639-HTTP-001"
        api         = 639
        category    = CATEGORY_HTTP
        description = "POST /resource returns 201 with Location header"

    And implement one coroutine::

        async def check(self, client: LintClient, ctx: LintContext) -> RuleResult: ...
    """

    rule_id: str
    api: int
    category: str
    description: str

    # ── Result factory helpers ───────────────────────────────────────────────

    def ok(self, message: str = "") -> RuleResult:
        """Return a passing result."""
        return RuleResult(
            rule_id=self.rule_id,
            api=self.api,
            category=self.category,
            description=self.description,
            passed=True,
            message=message,
        )

    def fail(self, message: str) -> RuleResult:
        """Return a failing result with a human-readable *message*."""
        return RuleResult(
            rule_id=self.rule_id,
            api=self.api,
            category=self.category,
            description=self.description,
            passed=False,
            message=message,
        )

    def skip(self, reason: str) -> RuleResult:
        """Return a skipped result, e.g. when a prerequisite rule failed."""
        return RuleResult(
            rule_id=self.rule_id,
            api=self.api,
            category=self.category,
            description=self.description,
            passed=False,
            skipped=True,
            message=reason,
        )

    # ── Abstract interface ───────────────────────────────────────────────────

    @abstractmethod
    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        """Execute this rule and return a single ``RuleResult``.

        Implementations must never raise — catch all exceptions and return
        ``self.fail(str(exc))`` so the runner can continue with other rules.
        """
        ...
