"""Tests for TMF641 HTTP rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_http import (
    TMF641DeleteReturns204,
    TMF641GetListReturns200,
    TMF641GetUnknownIdReturns404,
    TMF641PostReturns201,
)


@pytest.mark.asyncio
async def test_post_201_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"},
        )
    )
    result = await TMF641PostReturns201().check(lint_client, ctx_641)
    assert result.passed
    assert ctx_641.get_str("tmf641:order_id") == "ord-001"


@pytest.mark.asyncio
async def test_post_missing_location(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body())
    )
    result = await TMF641PostReturns201().check(lint_client, ctx_641)
    assert not result.passed
    assert "Location" in result.message


@pytest.mark.asyncio
async def test_post_missing_order_date(mock_router, lint_client, ctx_641):
    body = order_body()
    del body["orderDate"]
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"}
        )
    )
    result = await TMF641PostReturns201().check(lint_client, ctx_641)
    assert not result.passed
    assert "orderDate" in result.message


@pytest.mark.asyncio
async def test_post_wrong_status(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(200, json=order_body())
    )
    result = await TMF641PostReturns201().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_get_list_pass(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH).mock(
        return_value=httpx.Response(
            200, json=[order_body()], headers={"X-Total-Count": "1"}
        )
    )
    result = await TMF641GetListReturns200().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_get_list_missing_header(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH).mock(
        return_value=httpx.Response(200, json=[order_body()])
    )
    result = await TMF641GetListReturns200().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_get_unknown_404_pass(mock_router, lint_client, ctx_641):
    mock_router.get(url__regex=rf"{ORDER_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    result = await TMF641GetUnknownIdReturns404().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_get_unknown_200_fail(mock_router, lint_client, ctx_641):
    mock_router.get(url__regex=rf"{ORDER_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(200, json=order_body())
    )
    result = await TMF641GetUnknownIdReturns404().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_delete_204_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("del-001"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/del-001"},
        )
    )
    mock_router.delete(f"{ORDER_PATH}/del-001").mock(
        return_value=httpx.Response(204)
    )
    result = await TMF641DeleteReturns204().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_delete_wrong_status(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("del-002"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/del-002"},
        )
    )
    mock_router.delete(f"{ORDER_PATH}/del-002").mock(
        return_value=httpx.Response(200)
    )
    result = await TMF641DeleteReturns204().check(lint_client, ctx_641)
    assert not result.passed
