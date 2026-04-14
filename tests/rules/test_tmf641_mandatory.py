"""Tests for TMF641 mandatory fields rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_mandatory_fields import (
    TMF641GetResponseHasMandatoryFields,
    TMF641PostResponseHasMandatoryFields,
)


@pytest.mark.asyncio
async def test_post_all_fields_present(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"}
        )
    )
    result = await TMF641PostResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_post_missing_state(mock_router, lint_client, ctx_641):
    body = order_body()
    del body["state"]
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"}
        )
    )
    result = await TMF641PostResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert not result.passed
    assert "state" in result.message


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
    result = await TMF641PostResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_post_relative_href_fails(mock_router, lint_client, ctx_641):
    body = order_body()
    body["href"] = "/serviceOrder/ord-001"
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"}
        )
    )
    result = await TMF641PostResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_post_non_201_skipped(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(500, json={"message": "error"})
    )
    result = await TMF641PostResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert result.skipped


@pytest.mark.asyncio
async def test_get_all_fields_present(mock_router, lint_client, ctx_641):
    ctx_641.set("tmf641:order_id", "ord-001")
    mock_router.get(f"{ORDER_PATH}/ord-001").mock(
        return_value=httpx.Response(200, json=order_body("ord-001"))
    )
    result = await TMF641GetResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_get_skipped_without_ctx(mock_router, lint_client, ctx_641):
    result = await TMF641GetResponseHasMandatoryFields().check(lint_client, ctx_641)
    assert result.skipped
