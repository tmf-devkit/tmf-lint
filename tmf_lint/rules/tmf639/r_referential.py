"""
TMF639 — Referential integrity rules.

Validates that the server correctly enforces cross-resource references.

Rules:
  REF-001  DELETE a resource that is referenced by a service returns 409.
           Requires TMF638 to also be enabled (skips otherwise).
  REF-002  POST resource with a non-existent resourceRelationship target
           returns 422 (if the server validates inbound refs — optional,
           so this is skipped when the server returns 201).

Context keys read:
  "tmf639:resource_id"   — resource to attempt deletion of
  "tmf638:service_id"    — service that references the resource (written here)
"""
from __future__ import annotations

import uuid

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult
from tmf_lint.rules.base import CATEGORY_REFERENTIAL, BaseRule

_RESOURCE = "/tmf-api/resourceInventoryManagement/v4/resource"
_SERVICE = "/tmf-api/serviceInventoryManagement/v4/service"


class TMF639DeleteReferencedResourceReturns409(BaseRule):
    """DELETE a resource that is referenced by a service returns 409.

    Source: TMF639 v4.0.0 §6 (deleteResource) — implementations SHOULD
    reject deletion of in-use resources.

    Skipped when TMF638 is not in the requested API set, because a service
    must be created to establish the reference.
    """

    rule_id = "TMF639-REF-001"
    api = 639
    category = CATEGORY_REFERENTIAL
    description = "DELETE resource referenced by a service returns 409"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        if 638 not in ctx.apis:
            return self.skip("TMF638 not in requested APIs; cross-API referential check skipped")

        # Create a fresh resource specifically for this test.
        try:
            post_res = await client.post(
                _RESOURCE,
                json={
                    "@type": "Resource",
                    "@baseType": "Resource",
                    "name": f"tmf-lint-ref-res-{uuid.uuid4().hex[:8]}",
                    "resourceStatus": "available",
                },
            )
        except Exception as exc:
            return self.fail(f"Setup POST /resource failed: {exc}")

        if post_res.status_code != 201:
            return self.skip(f"Setup POST /resource returned {post_res.status_code}")

        rid = post_res.json().get("id")
        if not rid:
            return self.skip("Setup POST /resource did not return an id")

        # Create a service that holds a supportingResource reference.
        try:
            post_svc = await client.post(
                _SERVICE,
                json={
                    "@type": "Service",
                    "@baseType": "Service",
                    "name": f"tmf-lint-ref-svc-{uuid.uuid4().hex[:8]}",
                    "state": "active",
                    "supportingResource": [
                        {"id": rid, "@type": "ResourceRef", "@referredType": "Resource"}
                    ],
                },
            )
        except Exception as exc:
            return self.fail(f"Setup POST /service failed: {exc}")

        if post_svc.status_code != 201:
            return self.skip(
                f"Setup POST /service returned {post_svc.status_code}; "
                "cannot test referential integrity"
            )

        # Store the service id so the TMF638 referential rule can clean up.
        svc_id = post_svc.json().get("id")
        if svc_id:
            ctx.set("tmf638:ref_service_id", svc_id)

        # Now attempt to delete the referenced resource — expect 409.
        try:
            del_resp = await client.delete(f"{_RESOURCE}/{rid}")
        except Exception as exc:
            return self.fail(f"DELETE /resource/{rid} failed: {exc}")

        if del_resp.status_code != 409:
            return self.fail(
                f"DELETE of referenced resource should return 409, got {del_resp.status_code}"
            )
        return self.ok()
