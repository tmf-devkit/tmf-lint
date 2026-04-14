"""
TMF638 — HTTP mechanics rules.

Context keys written:
  "tmf638:service_id"   — str   — ID of the first service created
  "tmf638:service_ids"  — list  — IDs of all services created
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import BaseRule, CATEGORY_HTTP

_BASE = "/tmf-api/serviceInventoryManagement/v4"
_SERVICE = f"{_BASE}/service"


def _new_service(suffix: str = "") -> dict:
    return {
        "@type": "Service",
        "@baseType": "Service",
        "name": f"tmf-lint-svc-{suffix or uuid.uuid4().hex[:8]}",
        "state": "active",
        "serviceType": "technical",
    }


class TMF638PostReturns201(BaseRule):
    """POST /service returns 201 with a Location header.

    Source: TMF638 v4.0.0 §6 (createService).
    """

    rule_id = "TMF638-HTTP-001"
    api = 638
    category = CATEGORY_HTTP
    description = "POST /service returns 201 with Location header"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.post(_SERVICE, json=_new_service("http001"))
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.fail(f"Expected 201, got {resp.status_code}")
        if "Location" not in resp.headers:
            return self.fail("201 response is missing the Location header")

        data = resp.json()
        sid = data.get("id")
        if sid:
            ctx.set("tmf638:service_id", sid)
            ctx.append("tmf638:service_ids", sid)
        return self.ok()


class TMF638GetListReturns200(BaseRule):
    """GET /service returns 200 with X-Total-Count header."""

    rule_id = "TMF638-HTTP-002"
    api = 638
    category = CATEGORY_HTTP
    description = "GET /service returns 200 with X-Total-Count header"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get(_SERVICE)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(f"Expected 200, got {resp.status_code}")
        if "X-Total-Count" not in resp.headers:
            return self.fail("GET list response is missing X-Total-Count header")
        return self.ok()


class TMF638GetUnknownIdReturns404(BaseRule):
    """GET /service/{unknown-id} returns 404."""

    rule_id = "TMF638-HTTP-003"
    api = 638
    category = CATEGORY_HTTP
    description = "GET /service/{unknown-id} returns 404"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        fake_id = f"tmf-lint-nonexistent-{uuid.uuid4().hex}"
        try:
            resp = await client.get(f"{_SERVICE}/{fake_id}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 404:
            return self.fail(f"Expected 404 for unknown id, got {resp.status_code}")
        return self.ok()


class TMF638DeleteReturns204(BaseRule):
    """DELETE /service/{id} returns 204."""

    rule_id = "TMF638-HTTP-004"
    api = 638
    category = CATEGORY_HTTP
    description = "DELETE /service/{id} returns 204"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_SERVICE, json=_new_service("http004"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}")

        sid = post_resp.json().get("id")
        if not sid:
            return self.skip("Setup POST did not return an id field")

        try:
            del_resp = await client.delete(f"{_SERVICE}/{sid}")
        except Exception as exc:
            return self.fail(f"DELETE request failed: {exc}")

        if del_resp.status_code != 204:
            return self.fail(f"Expected 204, got {del_resp.status_code}")
        return self.ok()
