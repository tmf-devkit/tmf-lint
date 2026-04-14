"""
TMF641 — Mandatory fields rules.

Required fields per TMF641 v4.0.0 §7 (ServiceOrder schema):
  id, href, @type, @baseType, orderDate, state
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_MANDATORY_FIELDS, BaseRule

_ORDER = "/tmf-api/serviceOrdering/v4/serviceOrder"

_MF001_DESC = (
    "POST /serviceOrder response body contains"
    " id, href, @type, @baseType, orderDate, state"
)


class TMF641PostResponseHasMandatoryFields(BaseRule):
    """POST /serviceOrder response contains id, href, @type, @baseType, orderDate, state."""

    rule_id = "TMF641-MF-001"
    api = 641
    category = CATEGORY_MANDATORY_FIELDS
    description = _MF001_DESC

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        payload = {
            "@type": "ServiceOrder",
            "@baseType": "ServiceOrder",
            "description": f"tmf-lint-mf-{uuid.uuid4().hex[:8]}",
            "orderItem": [
                {
                    "@type": "ServiceOrderItem",
                    "id": "1",
                    "action": "add",
                    "service": {
                        "@type": "Service",
                        "serviceSpecification": {
                            "@type": "ServiceSpecificationRef",
                            "id": f"spec-{uuid.uuid4().hex[:8]}",
                            "name": "LintMFSpec",
                        },
                    },
                }
            ],
        }
        try:
            resp = await client.post(_ORDER, json=payload)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 201:
            return self.skip(f"POST returned {resp.status_code}; cannot check fields")

        data = resp.json()
        required = ("id", "href", "@type", "@baseType", "orderDate", "state")
        missing = [f for f in required if not data.get(f)]
        if missing:
            return self.fail(f"POST response missing required fields: {missing}")

        href = data.get("href", "")
        if not href.startswith("http"):
            return self.fail(f"href is not an absolute URL: {href!r}")

        return self.ok()


class TMF641GetResponseHasMandatoryFields(BaseRule):
    """GET /serviceOrder/{id} response contains id, href, @type, @baseType."""

    rule_id = "TMF641-MF-002"
    api = 641
    category = CATEGORY_MANDATORY_FIELDS
    description = "GET /serviceOrder/{id} response body contains id, href, @type, @baseType"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        oid = ctx.get_str("tmf641:order_id")
        if not oid:
            return self.skip("No order id in context; TMF641-HTTP-001 may have failed")

        try:
            resp = await client.get(f"{_ORDER}/{oid}")
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 200:
            return self.skip(f"GET returned {resp.status_code}; cannot check fields")

        data = resp.json()
        missing = [f for f in ("id", "href", "@type", "@baseType") if not data.get(f)]
        if missing:
            return self.fail(f"GET response missing required fields: {missing}")
        return self.ok()
