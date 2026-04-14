"""
TMF638 — Lifecycle state machine rules.

Validates Service lifecycle (state field) per TMF638 v4.0.0 §5.1.

Legal transitions (spec §5.1):
  feasibilityChecked → designed | terminated
  designed           → reserved | inactive | terminated
  reserved           → inactive | terminated
  inactive           → active   | terminated
  active             → inactive | terminated
  terminated         → (none — terminal)

Tested here:
  LC-001  active → inactive is accepted (200)  [valid]
  LC-002  terminated → active is rejected (422) [terminal state]
  LC-003  Same-state PATCH returns 200 (no-op)
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_LIFECYCLE, BaseRule

_SERVICE = "/tmf-api/serviceInventoryManagement/v4/service"


def _new_service(suffix: str = "") -> dict:
    return {
        "@type": "Service",
        "@baseType": "Service",
        "name": f"tmf-lint-lc-{suffix or uuid.uuid4().hex[:8]}",
        "state": "active",
        "serviceType": "technical",
    }


class TMF638ValidTransitionAccepted(BaseRule):
    """PATCH service state active→inactive returns 200.

    Source: TMF638 v4.0.0 §5.1 — active → inactive is a valid transition.
    """

    rule_id = "TMF638-LC-001"
    api = 638
    category = CATEGORY_LIFECYCLE
    description = "PATCH service state active→inactive returns 200"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_SERVICE, json=_new_service("lc001"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        sid = post_resp.json().get("id")
        if not sid:
            return self.skip("Setup POST did not return an id field")

        try:
            patch_resp = await client.patch(f"{_SERVICE}/{sid}", json={"state": "inactive"})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"PATCH active→inactive should return 200, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF638TerminalStateRejected(BaseRule):
    """PATCH service state from terminated returns 422.

    Source: TMF638 v4.0.0 §5.1 — terminated has no valid outgoing transitions.
    """

    rule_id = "TMF638-LC-002"
    api = 638
    category = CATEGORY_LIFECYCLE
    description = "PATCH service state terminated→active returns 422"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_SERVICE, json=_new_service("lc002"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        sid = post_resp.json().get("id")
        if not sid:
            return self.skip("Setup POST did not return an id field")

        # Move to terminated (valid from active).
        try:
            await client.patch(f"{_SERVICE}/{sid}", json={"state": "terminated"})
        except Exception as exc:
            return self.skip(f"Setup PATCH (→terminated) failed: {exc}")

        # Attempt to exit the terminal state.
        try:
            patch_resp = await client.patch(f"{_SERVICE}/{sid}", json={"state": "active"})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 422:
            return self.fail(
                f"PATCH terminated→active should return 422, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF638SameStateAccepted(BaseRule):
    """PATCH service state to same value returns 200 (no-op).

    Source: TMF638 v4.0.0 §5.1 — idempotent PATCH must not be rejected.
    """

    rule_id = "TMF638-LC-003"
    api = 638
    category = CATEGORY_LIFECYCLE
    description = "PATCH service state to same value returns 200 (no-op)"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        sid = ctx.get_str("tmf638:service_id")
        if not sid:
            return self.skip("No service id in context; TMF638-HTTP-001 may have failed")

        try:
            get_resp = await client.get(f"{_SERVICE}/{sid}")
        except Exception as exc:
            return self.fail(f"GET request failed: {exc}")

        if get_resp.status_code != 200:
            return self.skip(f"GET returned {get_resp.status_code}")

        current_state = get_resp.json().get("state", "active")

        try:
            patch_resp = await client.patch(f"{_SERVICE}/{sid}", json={"state": current_state})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"No-op PATCH (same state '{current_state}') should return 200, "
                f"got {patch_resp.status_code}"
            )
        return self.ok()
