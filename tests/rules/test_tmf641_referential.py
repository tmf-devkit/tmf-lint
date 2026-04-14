"""Tests for TMF641 referential integrity rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_referential import (
    TMF641PostOrderModifyNonExistentServiceReturns422,
)


@pytest.mark.asyncio
async def test_modify_nonexistent_service_422_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(422, json={"message": "service not found"})
    )
    result = await TMF641PostOrderModifyNonExistentServiceReturns422().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_modify_nonexistent_service_accepted_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"},
        )
    )
    result = await TMF641PostOrderModifyNonExistentServiceReturns422().check(lint_client, ctx_641)
    assert not result.passed
    assert "422" in result.message


@pytest.mark.asyncio
async def test_modify_nonexistent_service_404_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    result = await TMF641PostOrderModifyNonExistentServiceReturns422().check(lint_client, ctx_641)
    assert not result.passed
