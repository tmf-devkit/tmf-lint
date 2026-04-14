"""Tests for TMF639 referential integrity rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, RESOURCE_PATH, SERVICE_PATH, resource_body, service_body
from tmf_lint.rules.tmf639.r_referential import TMF639DeleteReferencedResourceReturns409


@pytest.mark.asyncio
async def test_delete_referenced_resource_409_pass(mock_router, lint_client, ctx):
    rid, sid = "ref-res-001", "ref-svc-001"
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(rid),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/{rid}"},
        )
    )
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(sid),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/{sid}"},
        )
    )
    mock_router.delete(f"{RESOURCE_PATH}/{rid}").mock(
        return_value=httpx.Response(409, json={"message": "resource is in use"})
    )
    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx)
    assert result.passed


@pytest.mark.asyncio
async def test_delete_referenced_resource_204_fail(mock_router, lint_client, ctx):
    rid = "ref-res-002"
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(rid),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/{rid}"},
        )
    )
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body("ref-svc-002"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/ref-svc-002"},
        )
    )
    mock_router.delete(f"{RESOURCE_PATH}/{rid}").mock(
        return_value=httpx.Response(204)
    )
    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx)
    assert not result.passed


@pytest.mark.asyncio
async def test_skipped_when_tmf638_not_in_apis(mock_router, lint_client, ctx_639):
    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx_639)
    assert result.skipped
