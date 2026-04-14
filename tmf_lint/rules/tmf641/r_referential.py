"""
TMF641 — Referential integrity rules.

REF-001  POST /serviceOrder with a 'modify' action referencing a non-existent
         service returns 422.

Source: TMF641 v4.0.0 §6 (createServiceOrder) — modify/remove actions must
reference an existing service.
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_REFERENTIAL, BaseRule

_ORDER = "/tmf-api/serviceOrdering/v4/serviceOrder"


class TMF641PostOrderModifyNonExistentServiceReturns422(BaseRule):
    """POST /serviceOrder with modify action on non-existent service returns 422.

    Source: TMF641 v4.0.0 §6 — 'modify' action requires an existing service.
    """

    rule_id = "TMF641-REF-001"
    api = 641
    category = CATEGORY_REFERENTIAL
    description = "POST /serviceOrder with modify on non-existent service returns 422"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        fake_service_id = f"tmf-lint-nonexistent-{uuid.uuid4().hex}"
        payload = {
            "@type": "ServiceOrder",
            "@baseType": "ServiceOrder",
            "description": f"tmf-lint-ref-{uuid.uuid4().hex[:8]}",
            "orderItem": [
                {
                    "@type": "ServiceOrderItem",
                    "id": "1",
                    "action": "modify",
                    "service": {
                        "@type": "Service",
                        "id": fake_service_id,
                        "state": "inactive",
                    },
                }
            ],
        }
        try:
            resp = await client.post(_ORDER, json=payload)
        except Exception as exc:
            return self.fail(f"Request failed: {exc}")

        if resp.status_code != 422:
            return self.fail(
                f"POST serviceOrder with modify on non-existent service should return 422, "
                f"got {resp.status_code}"
            )
        return self.ok()
