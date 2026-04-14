"""
TMF638 — Mandatory fields rules.

Required fields per TMF638 v4.0.0 §7 (Service schema): id, href, @type, @baseType.
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_MANDATORY_FIELDS, BaseRule

_SERVICE = "/tmf-api/serviceInventoryManagement/v4/service"


class TMF638PostResponseHasMandatoryFields(BaseRule):
    """POST /service response contains id, href, @type, @baseType."""

    rule_id = "TMF638-MF-001"
    api = 638
    category = CATEGORY_MANDATORY_FIELDS
    description = "POST /service response body contains id, href, @type, @baseType"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        payload = {
            "@type": "Service",
            "@baseType": "Service",
            "name": f"tmf-lint-mf-{uuid.uuid4().hex[:8]}",
            "state": "active",
        }
        try:
            resp = await client.post(_SERVICE, json=payload)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.skip(f"POST returned {resp.status_code}; cannot check fields")

        data = resp.json()
        missing = [f for f in ("id", "href", "@type", "@baseType") if not data.get(f)]
        if missing:
            return self.fail(f"POST response missing required fields: {missing}")
        return self.ok()


class TMF638GetResponseHasMandatoryFields(BaseRule):
    """GET /service/{id} response contains id, href, @type, @baseType, and absolute href."""

    rule_id = "TMF638-MF-002"
    api = 638
    category = CATEGORY_MANDATORY_FIELDS
    description = "GET /service/{id} response body contains id, href, @type, @baseType"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        sid = ctx.get_str("tmf638:service_id")
        if not sid:
            return self.skip("No service id in context; TMF638-HTTP-001 may have failed")

        try:
            resp = await client.get(f"{_SERVICE}/{sid}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.skip(f"GET returned {resp.status_code}; cannot check fields")

        data = resp.json()
        missing = [f for f in ("id", "href", "@type", "@baseType") if not data.get(f)]
        if missing:
            return self.fail(f"GET response missing required fields: {missing}")

        href = data.get("href", "")
        if not href.startswith("http"):
            return self.fail(f"href is not an absolute URL: {href!r}")

        return self.ok()
