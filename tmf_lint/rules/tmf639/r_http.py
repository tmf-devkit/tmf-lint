"""
TMF639 — HTTP mechanics rules.

Rules in this module create baseline entities and store their IDs in the
context so that lifecycle, referential, and pagination rules can reuse them.

Context keys written:
  "tmf639:resource_id"   — str   — ID of the first resource created
  "tmf639:resource_ids"  — list  — IDs of all resources created
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import BaseRule, CATEGORY_HTTP

_BASE = "/tmf-api/resourceInventoryManagement/v4"
_RESOURCE = f"{_BASE}/resource"


def _new_resource(suffix: str = "") -> dict:
    name = f"tmf-lint-res-{suffix or uuid.uuid4().hex[:8]}"
    return {
        "@type": "Resource",
        "@baseType": "Resource",
        "name": name,
        "resourceStatus": "available",
        "category": "physical",
    }


class TMF639PostReturns201(BaseRule):
    """POST /resource returns 201 with a Location header.

    Source: TMF639 v4.0.0 §6 (createResource).
    Also stores the created resource id in context for downstream rules.
    """

    rule_id = "TMF639-HTTP-001"
    api = 639
    category = CATEGORY_HTTP
    description = "POST /resource returns 201 with Location header"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.post(_RESOURCE, json=_new_resource("http001"))
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.fail(f"Expected 201, got {resp.status_code}")
        if "Location" not in resp.headers:
            return self.fail("201 response is missing the Location header")

        data = resp.json()
        rid = data.get("id")
        if rid:
            ctx.set("tmf639:resource_id", rid)
            ctx.append("tmf639:resource_ids", rid)
        return self.ok()


class TMF639GetListReturns200(BaseRule):
    """GET /resource returns 200 with X-Total-Count header."""

    rule_id = "TMF639-HTTP-002"
    api = 639
    category = CATEGORY_HTTP
    description = "GET /resource returns 200 with X-Total-Count header"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get(_RESOURCE)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.fail(f"Expected 200, got {resp.status_code}")
        if "X-Total-Count" not in resp.headers:
            return self.fail("GET list response is missing X-Total-Count header")
        return self.ok()


class TMF639GetUnknownIdReturns404(BaseRule):
    """GET /resource/{unknown-id} returns 404."""

    rule_id = "TMF639-HTTP-003"
    api = 639
    category = CATEGORY_HTTP
    description = "GET /resource/{unknown-id} returns 404"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        fake_id = f"tmf-lint-nonexistent-{uuid.uuid4().hex}"
        try:
            resp = await client.get(f"{_RESOURCE}/{fake_id}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 404:
            return self.fail(f"Expected 404 for unknown id, got {resp.status_code}")
        return self.ok()


class TMF639DeleteReturns204(BaseRule):
    """DELETE /resource/{id} returns 204.

    Creates a fresh throwaway resource so this rule does not consume the
    shared resource_id that referential rules depend on.
    """

    rule_id = "TMF639-HTTP-004"
    api = 639
    category = CATEGORY_HTTP
    description = "DELETE /resource/{id} returns 204"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            post_resp = await client.post(_RESOURCE, json=_new_resource("http004"))
        except Exception as exc:
            return self.fail(f"Setup POST failed: {exc}")

        if post_resp.status_code != 201:
            return self.skip(f"Setup POST returned {post_resp.status_code}; cannot test DELETE")

        rid = post_resp.json().get("id")
        if not rid:
            return self.skip("Setup POST did not return an id field")

        try:
            del_resp = await client.delete(f"{_RESOURCE}/{rid}")
        except Exception as exc:
            return self.fail(f"DELETE request failed: {exc}")

        if del_resp.status_code != 204:
            return self.fail(f"Expected 204, got {del_resp.status_code}")
        return self.ok()
