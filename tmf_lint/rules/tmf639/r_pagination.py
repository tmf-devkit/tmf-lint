"""
TMF639 — Pagination rules.

Validates that GET /resource honours offset/limit query parameters and
returns an accurate X-Total-Count header.

Source: TMF Open API Design Guidelines §5.5 (pagination).

Context keys read: none (pagination tests are self-contained).
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import BaseRule, CATEGORY_PAGINATION

_RESOURCE = "/tmf-api/resourceInventoryManagement/v4/resource"
_MIN_SEED = 3  # resources we create before testing — ensures a non-empty store


async def _ensure_resources(client: LintClient, count: int) -> bool:
    """Create *count* throwaway resources; return True on success."""
    for _ in range(count):
        resp = await client.post(
            _RESOURCE,
            json={
                "@type": "Resource",
                "@baseType": "Resource",
                "name": f"tmf-lint-pag-{uuid.uuid4().hex[:8]}",
                "resourceStatus": "available",
            },
        )
        if resp.status_code != 201:
            return False
    return True


class TMF639LimitQueryParam(BaseRule):
    """GET /resource?limit=1 returns at most 1 item.

    Source: TMF Open API Design Guidelines §5.5.
    """

    rule_id = "TMF639-PAG-001"
    api = 639
    category = CATEGORY_PAGINATION
    description = "GET /resource?limit=1 returns at most 1 item"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            await _ensure_resources(client, _MIN_SEED)
            resp = await client.get(_RESOURCE, params={"limit": 1})
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(f"Expected 200, got {resp.status_code}")

        items = resp.json()
        if not isinstance(items, list):
            return self.fail("Response body is not a JSON array")
        if len(items) > 1:
            return self.fail(f"limit=1 should return ≤1 item, got {len(items)}")
        return self.ok()


class TMF639XTotalCountMatchesActual(BaseRule):
    """X-Total-Count reflects the true total; fetching limit=total returns that many items.

    Strategy: two requests.
      1. GET with no params  → read X-Total-Count (declared total, N).
      2. GET with limit=N    → verify body length == N.

    This correctly handles servers that default to a page size smaller than
    the total (e.g. tmf-mock defaults to 20 items per page).

    Source: TMF Open API Design Guidelines §5.5.
    """

    rule_id = "TMF639-PAG-002"
    api = 639
    category = CATEGORY_PAGINATION
    description = "X-Total-Count is accurate (verified by fetching limit=total)"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        # ── Step 1: discover declared total ──────────────────────────────────
        try:
            await _ensure_resources(client, _MIN_SEED)
            probe = await client.get(_RESOURCE)
        except Exception as exc:
            return self.fail(f"Probe GET failed: {exc}")

        if probe.status_code != 200:
            return self.fail(f"Probe GET returned {probe.status_code}")

        header_val = probe.headers.get("X-Total-Count")
        if header_val is None:
            return self.fail("X-Total-Count header absent on probe GET")

        try:
            total_count = int(header_val)
        except ValueError:
            return self.fail(f"X-Total-Count is not an integer: {header_val!r}")

        if total_count == 0:
            return self.fail("X-Total-Count=0 after seeding resources — unexpected")

        # ── Step 2: fetch limit=total and confirm body length matches ─────────
        try:
            full_resp = await client.get(_RESOURCE, params={"limit": total_count})
        except Exception as exc:
            return self.fail(f"Full GET (limit={total_count}) failed: {exc}")

        if full_resp.status_code != 200:
            return self.fail(
                f"GET with limit={total_count} returned {full_resp.status_code}"
            )

        items = full_resp.json()
        if not isinstance(items, list):
            return self.fail("Response body is not a JSON array")

        if len(items) != total_count:
            return self.fail(
                f"X-Total-Count={total_count} but GET?limit={total_count} "
                f"returned {len(items)} items"
            )
        return self.ok()


class TMF639OffsetBeyondTotalReturnsEmpty(BaseRule):
    """GET /resource?offset={huge} returns 200 with an empty array, not an error.

    Source: TMF Open API Design Guidelines §5.5.
    """

    rule_id = "TMF639-PAG-003"
    api = 639
    category = CATEGORY_PAGINATION
    description = "GET /resource?offset=999999 returns 200 with empty array"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get(_RESOURCE, params={"offset": 999_999, "limit": 10})
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(
                f"offset beyond total should return 200, got {resp.status_code}"
            )

        items = resp.json()
        if not isinstance(items, list):
            return self.fail("Response body is not a JSON array")
        if len(items) != 0:
            return self.fail(
                f"offset beyond total should return empty array, got {len(items)} items"
            )
        return self.ok()
