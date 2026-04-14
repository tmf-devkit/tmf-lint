"""
TMF638 — Pagination rules.

Source: TMF Open API Design Guidelines §5.5.
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_PAGINATION, BaseRule

_SERVICE = "/tmf-api/serviceInventoryManagement/v4/service"
_MIN_SEED = 3


async def _ensure_services(client: LintClient, count: int) -> bool:
    for _ in range(count):
        resp = await client.post(
            _SERVICE,
            json={
                "@type": "Service",
                "@baseType": "Service",
                "name": f"tmf-lint-pag-{uuid.uuid4().hex[:8]}",
                "state": "active",
            },
        )
        if resp.status_code != 201:
            return False
    return True


class TMF638LimitQueryParam(BaseRule):
    """GET /service?limit=1 returns at most 1 item."""

    rule_id = "TMF638-PAG-001"
    api = 638
    category = CATEGORY_PAGINATION
    description = "GET /service?limit=1 returns at most 1 item"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            await _ensure_services(client, _MIN_SEED)
            resp = await client.get(_SERVICE, params={"limit": 1})
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


class TMF638XTotalCountMatchesActual(BaseRule):
    """X-Total-Count is accurate (verified by fetching limit=total).

    Strategy: two requests.
      1. GET with no params  → read X-Total-Count (declared total, N).
      2. GET with limit=N    → verify body length == N.

    This correctly handles servers that default to a page size smaller than
    the total (e.g. tmf-mock defaults to 20 items per page).

    Source: TMF Open API Design Guidelines §5.5.
    """

    rule_id = "TMF638-PAG-002"
    api = 638
    category = CATEGORY_PAGINATION
    description = "X-Total-Count is accurate (verified by fetching limit=total)"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        # ── Step 1: discover declared total ──────────────────────────────────
        try:
            await _ensure_services(client, _MIN_SEED)
            probe = await client.get(_SERVICE)
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
            return self.fail("X-Total-Count=0 after seeding services — unexpected")

        # ── Step 2: fetch limit=total and confirm body length matches ─────────
        try:
            full_resp = await client.get(_SERVICE, params={"limit": total_count})
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


class TMF638OffsetBeyondTotalReturnsEmpty(BaseRule):
    """GET /service?offset=999999 returns 200 with empty array."""

    rule_id = "TMF638-PAG-003"
    api = 638
    category = CATEGORY_PAGINATION
    description = "GET /service?offset=999999 returns 200 with empty array"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get(_SERVICE, params={"offset": 999_999, "limit": 10})
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(f"offset beyond total should return 200, got {resp.status_code}")

        items = resp.json()
        if not isinstance(items, list):
            return self.fail("Response body is not a JSON array")
        if len(items) != 0:
            return self.fail(
                f"offset beyond total should return empty array, got {len(items)} items"
            )
        return self.ok()
