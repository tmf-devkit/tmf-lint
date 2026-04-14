"""
TMF641 — Lifecycle state machine rules.

Validates ServiceOrder lifecycle per TMF641 v4.0.0 §5.1.

Transitions (spec §5.1):
  acknowledged → rejected | pending | held | inProgress | cancelled
  pending      → inProgress | cancelled
  held         → inProgress | cancelled
  inProgress   → completed | failed | partial | cancelled
  partial      → inProgress | cancelled
  completed    → (terminal)
  failed       → (terminal)
  rejected     → (terminal)
  cancelled    → (terminal)

Tested here:
  LC-001  acknowledged → inProgress is accepted (200)  [valid]
  LC-002  completed → inProgress is rejected (422)     [terminal]
  LC-003  Same-state PATCH returns 200 (no-op)
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_LIFECYCLE, BaseRule

_ORDER = "/tmf-api/serviceOrdering/v4/serviceOrder"


def _new_order(suffix: str = "") -> dict:
    return {
        "@type": "ServiceOrder",
        "@baseType": "ServiceOrder",
        "description": f"tmf-lint-lc-{suffix or uuid.uuid4().hex[:8]}",
        "orderItem": [
            {
                "@type": "ServiceOrderItem",
                "id": "1",
                "action": "add",
                "service": {
                    "@type": "Service",
                    "serviceSpecification": {
                        "@type": "ServiceSpecificationRef",
                        "id": f"spec-lc-{uuid.uuid4().hex[:8]}",
                        "name": "LintLCSpec",
                    },
                },
            }
        ],
    }


class TMF641ValidTransitionAccepted(BaseRule):
    """PATCH serviceOrder state acknowledged→inProgress returns 200.

    Source: TMF641 v4.0.0 §5.1.
    """

    rule_id = "TMF641-LC-001"
    api = 641
    category = CATEGORY_LIFECYCLE
    description = "PATCH serviceOrder state acknowledged→inProgress returns 200"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_ORDER, json=_new_order("lc001"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        oid = post_resp.json().get("id")
        if not oid:
            return self.skip("Setup POST did not return an id field")

        # Server sets state=acknowledged on creation — confirm before patching.
        state = post_resp.json().get("state", "acknowledged")
        if state != "acknowledged":
            return self.skip(
                f"New order has state={state!r}; expected 'acknowledged' to test this transition"
            )

        try:
            patch_resp = await client.patch(f"{_ORDER}/{oid}", json={"state": "inProgress"})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"PATCH acknowledged→inProgress should return 200, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF641TerminalStateRejected(BaseRule):
    """PATCH serviceOrder state from completed returns 422.

    Source: TMF641 v4.0.0 §5.1 — completed is a terminal state.
    """

    rule_id = "TMF641-LC-002"
    api = 641
    category = CATEGORY_LIFECYCLE
    description = "PATCH serviceOrder state completed→inProgress returns 422"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_ORDER, json=_new_order("lc002"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        oid = post_resp.json().get("id")
        if not oid:
            return self.skip("Setup POST did not return an id field")

        # Drive order to completed via acknowledged → inProgress → completed.
        for target_state in ("inProgress", "completed"):
            try:
                patch = await client.patch(f"{_ORDER}/{oid}", json={"state": target_state})
            except Exception as exc:
                return self.skip(f"Setup PATCH →{target_state} failed: {exc}")

            if patch.status_code not in (200, 422):
                return self.skip(f"Setup PATCH →{target_state} returned {patch.status_code}")

        # Now attempt to exit the terminal state.
        try:
            patch_resp = await client.patch(f"{_ORDER}/{oid}", json={"state": "inProgress"})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 422:
            return self.fail(
                f"PATCH completed→inProgress should return 422, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF641SameStateAccepted(BaseRule):
    """PATCH serviceOrder state to same value returns 200 (no-op).

    Source: TMF641 v4.0.0 §5.1 — idempotent PATCH must not be rejected.
    """

    rule_id = "TMF641-LC-003"
    api = 641
    category = CATEGORY_LIFECYCLE
    description = "PATCH serviceOrder state to same value returns 200 (no-op)"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        oid = ctx.get_str("tmf641:order_id")
        if not oid:
            return self.skip("No order id in context; TMF641-HTTP-001 may have failed")

        try:
            get_resp = await client.get(f"{_ORDER}/{oid}")
        except Exception as exc:
            return self.fail(f"GET request failed: {exc}")

        if get_resp.status_code != 200:
            return self.skip(f"GET returned {get_resp.status_code}")

        current_state = get_resp.json().get("state", "acknowledged")

        try:
            patch_resp = await client.patch(f"{_ORDER}/{oid}", json={"state": current_state})
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"No-op PATCH (same state '{current_state}') should return 200, "
                f"got {patch_resp.status_code}"
            )
        return self.ok()
