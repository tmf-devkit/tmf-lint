"""
TMF639 — Lifecycle state machine rules.

Validates that the server enforces the Resource lifecycle (resourceStatus)
defined in TMF639 v4.0.0 §5.1.

Legal transitions (from statemachine.py / spec §5.1):
  available  → reserved | standby | alarm | suspended
  reserved   → available | suspended
  standby    → available | suspended
  alarm      → available | suspended
  suspended  → available       ← only one allowed target
  unknown    → available | standby | alarm | suspended

Illegal (tested here):
  suspended  → alarm            (suspended can only go to available)
  available  → available        (same-state PATCH should succeed as a no-op)

Terminal states: none for resourceStatus (unlike service/order).

Context keys read: "tmf639:resource_id"
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_LIFECYCLE, BaseRule

_BASE = "/tmf-api/resourceInventoryManagement/v4"
_RESOURCE = f"{_BASE}/resource"


def _new_resource(suffix: str = "") -> dict:
    return {
        "@type": "Resource",
        "@baseType": "Resource",
        "name": f"tmf-lint-lc-{suffix or uuid.uuid4().hex[:8]}",
        "resourceStatus": "available",
        "category": "physical",
    }


class TMF639ValidTransitionAccepted(BaseRule):
    """PATCH available→suspended is accepted (200).

    Source: TMF639 v4.0.0 §5.1 — available is a valid source for suspended.
    """

    rule_id = "TMF639-LC-001"
    api = 639
    category = CATEGORY_LIFECYCLE
    description = "PATCH resourceStatus available→suspended returns 200"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_RESOURCE, json=_new_resource("lc001"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        rid = post_resp.json().get("id")
        if not rid:
            return self.skip("Setup POST did not return an id field")

        try:
            patch_resp = await client.patch(
                f"{_RESOURCE}/{rid}",
                json={"resourceStatus": "suspended"},
            )
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"PATCH available→suspended should return 200, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF639InvalidTransitionRejected(BaseRule):
    """PATCH suspended→alarm is rejected (422).

    Source: TMF639 v4.0.0 §5.1 — suspended can only transition to available.
    """

    rule_id = "TMF639-LC-002"
    api = 639
    category = CATEGORY_LIFECYCLE
    description = "PATCH resourceStatus suspended→alarm returns 422"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        # Create a resource already in 'suspended' state.
        try:
            post_resp = await client.post(_RESOURCE, json=_new_resource("lc002"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        rid = post_resp.json().get("id")
        if not rid:
            return self.skip("Setup POST did not return an id field")

        # First move to suspended (valid).
        try:
            await client.patch(f"{_RESOURCE}/{rid}", json={"resourceStatus": "suspended"})
        except Exception as exc:
            return self.skip(f"Setup PATCH (→suspended) failed: {exc}")

        # Now try the illegal transition: suspended → alarm.
        try:
            patch_resp = await client.patch(
                f"{_RESOURCE}/{rid}",
                json={"resourceStatus": "alarm"},
            )
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 422:
            return self.fail(
                f"PATCH suspended→alarm should return 422, got {patch_resp.status_code}"
            )
        return self.ok()


class TMF639SameStateAccepted(BaseRule):
    """PATCH to the current state (no-op) returns 200.

    Source: TMF639 v4.0.0 §5.1 — idempotent PATCH must not be rejected.
    """

    rule_id = "TMF639-LC-003"
    api = 639
    category = CATEGORY_LIFECYCLE
    description = "PATCH resourceStatus to same state returns 200 (no-op)"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        rid = ctx.get_str("tmf639:resource_id")
        if not rid:
            return self.skip("No resource id in context; TMF639-HTTP-001 may have failed")

        # Read current state.
        try:
            get_resp = await client.get(f"{_RESOURCE}/{rid}")
        except Exception as exc:
            return self.fail(f"GET request failed: {exc}")

        if get_resp.status_code != 200:
            return self.skip(f"GET returned {get_resp.status_code}")

        current_status = get_resp.json().get("resourceStatus", "available")

        try:
            patch_resp = await client.patch(
                f"{_RESOURCE}/{rid}",
                json={"resourceStatus": current_status},
            )
        except Exception as exc:
            return self.fail(f"PATCH request failed: {exc}")

        if patch_resp.status_code != 200:
            return self.fail(
                f"No-op PATCH (same state '{current_status}') should return 200, "
                f"got {patch_resp.status_code}"
            )
        return self.ok()
