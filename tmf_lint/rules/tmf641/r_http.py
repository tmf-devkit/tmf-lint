"""
TMF641 — HTTP mechanics rules.

Context keys written:
  "tmf641:order_id"   — str  — ID of the first order created
  "tmf641:order_ids"  — list — IDs of all orders created
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import BaseRule, CATEGORY_HTTP

_BASE = "/tmf-api/serviceOrdering/v4"
_ORDER = f"{_BASE}/serviceOrder"


def _new_order(suffix: str = "") -> dict:
    """Minimal valid ServiceOrder payload."""
    return {
        "@type": "ServiceOrder",
        "@baseType": "ServiceOrder",
        "description": f"tmf-lint-order-{suffix or uuid.uuid4().hex[:8]}",
        "orderItem": [
            {
                "@type": "ServiceOrderItem",
                "id": "1",
                "action": "add",
                "service": {
                    "@type": "Service",
                    "serviceSpecification": {
                        "@type": "ServiceSpecificationRef",
                        "id": f"spec-lint-{uuid.uuid4().hex[:8]}",
                        "name": "LintTestSpec",
                    },
                },
            }
        ],
    }


class TMF641PostReturns201(BaseRule):
    """POST /serviceOrder returns 201 with Location header and orderDate.

    Source: TMF641 v4.0.0 §6 (createServiceOrder).
    """

    rule_id = "TMF641-HTTP-001"
    api = 641
    category = CATEGORY_HTTP
    description = "POST /serviceOrder returns 201 with Location header and orderDate"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.post(_ORDER, json=_new_order("http001"))
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.fail(f"Expected 201, got {resp.status_code}")
        if "Location" not in resp.headers:
            return self.fail("201 response is missing the Location header")

        data = resp.json()
        if not data.get("orderDate"):
            return self.fail("POST response missing orderDate field")

        oid = data.get("id")
        if oid:
            ctx.set("tmf641:order_id", oid)
            ctx.append("tmf641:order_ids", oid)
        return self.ok()


class TMF641GetListReturns200(BaseRule):
    """GET /serviceOrder returns 200 with X-Total-Count header."""

    rule_id = "TMF641-HTTP-002"
    api = 641
    category = CATEGORY_HTTP
    description = "GET /serviceOrder returns 200 with X-Total-Count header"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get(_ORDER)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(f"Expected 200, got {resp.status_code}")
        if "X-Total-Count" not in resp.headers:
            return self.fail("GET list response is missing X-Total-Count header")
        return self.ok()


class TMF641GetUnknownIdReturns404(BaseRule):
    """GET /serviceOrder/{unknown-id} returns 404."""

    rule_id = "TMF641-HTTP-003"
    api = 641
    category = CATEGORY_HTTP
    description = "GET /serviceOrder/{unknown-id} returns 404"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        fake_id = f"tmf-lint-nonexistent-{uuid.uuid4().hex}"
        try:
            resp = await client.get(f"{_ORDER}/{fake_id}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 404:
            return self.fail(f"Expected 404 for unknown id, got {resp.status_code}")
        return self.ok()


class TMF641DeleteReturns204(BaseRule):
    """DELETE /serviceOrder/{id} returns 204."""

    rule_id = "TMF641-HTTP-004"
    api = 641
    category = CATEGORY_HTTP
    description = "DELETE /serviceOrder/{id} returns 204"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_ORDER, json=_new_order("http004"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        oid = post_resp.json().get("id")
        if not oid:
            return self.skip("Setup POST did not return an id field")

        try:
            del_resp = await client.delete(f"{_ORDER}/{oid}")
        except Exception as exc:
            return self.fail(f"DELETE request failed: {exc}")

        if del_resp.status_code != 204:
            return self.fail(f"Expected 204, got {del_resp.status_code}")
        return self.ok()
