"""Tests for TMF639 referential integrity rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, RESOURCE_PATH, SERVICE_PATH, resource_body, service_body
from tmf_lint.rules.tmf639.r_referential import TMF639DeleteReferencedResourceReturns409


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


@pytest.mark.asyncio
async def test_delete_referenced_resource_409_pass(mock_router, lint_client, ctx):
    """Server returns 409 when deleting a resource referenced by a service."""
    rid = "ref-res-001"
    sid = "ref-svc-001"

    # POST resource → 201
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=resource_body(rid),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/{rid}"},
        )
    )
    # POST service → 201
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=service_body(sid),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/{sid}"},
        )
    )
    # DELETE resource → 409 (still referenced)
    mock_router.delete(f"{RESOURCE_PATH}/{rid}").mock(
        return_value=httpx.Response(409, json={"message": "resource is in use"})
    )

    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx)
    assert result.passed


@pytest.mark.asyncio
async def test_delete_referenced_resource_204_fail(mock_router, lint_client, ctx):
    """Server incorrectly allows deletion of a referenced resource."""
    rid = "ref-res-002"

    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=resource_body(rid),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/{rid}"},
        )
    )
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=service_body("ref-svc-002"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/ref-svc-002"},
        )
    )
    mock_router.delete(f"{RESOURCE_PATH}/{rid}").mock(
        return_value=httpx.Response(204)  # wrong — should be 409
    )

    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx)
    assert not result.passed


@pytest.mark.asyncio
async def test_skipped_when_tmf638_not_in_apis(mock_router, lint_client, ctx_639):
    """Rule is skipped when TMF638 is not in the requested API set."""
    result = await TMF639DeleteReferencedResourceReturns409().check(lint_client, ctx_639)
    assert result.skipped
