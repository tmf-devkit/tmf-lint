"""
TMF639 — Mandatory fields rules.

Validates that response bodies include all fields that the TMF639 v4.0.0 spec
marks as required for Resource entities.

Required fields per spec §7 (Resource schema):
  id, href, @type, @baseType

Context keys read: "tmf639:resource_id"
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_MANDATORY_FIELDS, BaseRule

_BASE = "/tmf-api/resourceInventoryManagement/v4"
_RESOURCE = f"{_BASE}/resource"


class TMF639PostResponseHasMandatoryFields(BaseRule):
    """POST /resource response contains id, href, @type, @baseType."""

    rule_id = "TMF639-MF-001"
    api = 639
    category = CATEGORY_MANDATORY_FIELDS
    description = "POST /resource response body contains id, href, @type, @baseType"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        payload = {
            "@type": "Resource",
            "@baseType": "Resource",
            "name": f"tmf-lint-mf-{uuid.uuid4().hex[:8]}",
            "resourceStatus": "available",
        }
        try:
            resp = await client.post(_RESOURCE, json=payload)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.skip(f"POST returned {resp.status_code}; cannot check fields")

        data = resp.json()
        missing = [f for f in ("id", "href", "@type", "@baseType") if not data.get(f)]
        if missing:
            return self.fail(f"POST response missing required fields: {missing}")
        return self.ok()


class TMF639GetResponseHasMandatoryFields(BaseRule):
    """GET /resource/{id} response contains id, href, @type, @baseType."""

    rule_id = "TMF639-MF-002"
    api = 639
    category = CATEGORY_MANDATORY_FIELDS
    description = "GET /resource/{id} response body contains id, href, @type, @baseType"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        rid = ctx.get_str("tmf639:resource_id")
        if not rid:
            return self.skip("No resource id in context; TMF639-HTTP-001 may have failed")

        try:
            resp = await client.get(f"{_RESOURCE}/{rid}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.skip(f"GET returned {resp.status_code}; cannot check fields")

        data = resp.json()
        missing = [f for f in ("id", "href", "@type", "@baseType") if not data.get(f)]
        if missing:
            return self.fail(f"GET response missing required fields: {missing}")

        # href must be a valid absolute URL
        href = data.get("href", "")
        if not href.startswith("http"):
            return self.fail(f"href is not an absolute URL: {href!r}")

        return self.ok()
