"""Tests for TMF638 referential integrity rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_referential import TMF638PostServiceWithInvalidResourceReturns422


@pytest.mark.asyncio
async def test_invalid_resource_ref_422_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(422, json={"message": "resource not found"})
    )
    result = await TMF638PostServiceWithInvalidResourceReturns422().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_invalid_resource_ref_accepted_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"},
        )
    )
    result = await TMF638PostServiceWithInvalidResourceReturns422().check(lint_client, ctx_638)
    assert not result.passed
    assert "422" in result.message


@pytest.mark.asyncio
async def test_invalid_resource_ref_500_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(500, json={"message": "internal error"})
    )
    result = await TMF638PostServiceWithInvalidResourceReturns422().check(lint_client, ctx_638)
    assert not result.passed
