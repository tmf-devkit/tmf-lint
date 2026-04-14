"""
TMF638 — Referential integrity rules.

REF-001  POST /service with a supportingResource referencing a non-existent
         resource returns 422.

Source: TMF638 v4.0.0 §6 (createService) — implementations SHOULD validate
inbound resource references.
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import BaseRule, CATEGORY_REFERENTIAL

_SERVICE = "/tmf-api/serviceInventoryManagement/v4/service"


class TMF638PostServiceWithInvalidResourceReturns422(BaseRule):
    """POST /service with non-existent supportingResource returns 422.

    Source: TMF638 v4.0.0 §6 (createService).
    """

    rule_id = "TMF638-REF-001"
    api = 638
    category = CATEGORY_REFERENTIAL
    description = "POST /service with non-existent supportingResource returns 422"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        fake_resource_id = f"tmf-lint-nonexistent-{uuid.uuid4().hex}"
        payload = {
            "@type": "Service",
            "@baseType": "Service",
            "name": f"tmf-lint-ref-{uuid.uuid4().hex[:8]}",
            "state": "active",
            "supportingResource": [
                {
                    "id": fake_resource_id,
                    "@type": "ResourceRef",
                    "@referredType": "Resource",
                }
            ],
        }
        try:
            resp = await client.post(_SERVICE, json=payload)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 422:
            return self.fail(
                f"POST with non-existent supportingResource should return 422, "
                f"got {resp.status_code}"
            )
        return self.ok()
