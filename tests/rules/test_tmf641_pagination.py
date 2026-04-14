"""Tests for TMF641 pagination rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_pagination import (
    TMF641LimitQueryParam,
    TMF641XTotalCountMatchesActual,
    TMF641OffsetBeyondTotalReturnsEmpty,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


def _list_resp(items: list, total: int | None = None) -> httpx.Response:
    headers = {"X-Total-Count": str(total)} if total is not None else {}
    return httpx.Response(200, json=items, headers=headers)


# ── TMF641LimitQueryParam ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"}
        )
    )
    mock_router.get(ORDER_PATH, params={"limit": "1"}).mock(
        return_value=_list_resp([order_body()], total=5)
    )
    result = await TMF641LimitQueryParam().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"}
        )
    )
    mock_router.get(ORDER_PATH, params={"limit": "1"}).mock(
        return_value=_list_resp([order_body(), order_body("o2")], total=5)
    )
    result = await TMF641LimitQueryParam().check(lint_client, ctx_641)
    assert not result.passed


# ── TMF641XTotalCountMatchesActual (two-request strategy) ───────────────────

@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"}
        )
    )
    # Probe reports total=3; returns first page of 2
    mock_router.get(ORDER_PATH).mock(
        return_value=_list_resp([order_body("o0"), order_body("o1")], total=3)
    )
    # Full fetch limit=3 returns all 3
    mock_router.get(ORDER_PATH, params={"limit": "3"}).mock(
        return_value=_list_resp([order_body(f"o{i}") for i in range(3)], total=3)
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"}
        )
    )
    mock_router.get(ORDER_PATH).mock(
        return_value=_list_resp([order_body()], total=3)
    )
    # limit=3 only returns 1 — header was lying
    mock_router.get(ORDER_PATH, params={"limit": "3"}).mock(
        return_value=_list_resp([order_body("o0")], total=3)
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"}
        )
    )
    mock_router.get(ORDER_PATH).mock(
        return_value=httpx.Response(200, json=[order_body()])
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert not result.passed


# ── TMF641OffsetBeyondTotalReturnsEmpty ──────────────────────────────────────

@pytest.mark.asyncio
async def test_offset_beyond_empty(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_resp([], total=3)
    )
    result = await TMF641OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_resp([order_body()], total=1)
    )
    result = await TMF641OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_error_code_fail(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    result = await TMF641OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_641)
    assert not result.passed
