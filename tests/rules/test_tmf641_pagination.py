"""Tests for TMF641 pagination rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_pagination import (
    TMF641LimitQueryParam,
    TMF641XTotalCountMatchesActual,
    TMF641OffsetBeyondTotalReturnsEmpty,
)


def _lr(items: list, total: int | None = None) -> httpx.Response:
    headers = {"X-Total-Count": str(total)} if total is not None else {}
    return httpx.Response(200, json=items, headers=headers)


@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body(),
                                    headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"})
    )
    mock_router.get(ORDER_PATH, params={"limit": "1"}).mock(
        return_value=_lr([order_body()], total=5)
    )
    result = await TMF641LimitQueryParam().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body(),
                                    headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"})
    )
    mock_router.get(ORDER_PATH, params={"limit": "1"}).mock(
        return_value=_lr([order_body(), order_body("o2")], total=5)
    )
    result = await TMF641LimitQueryParam().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_641):
    """Probe GET returns total=3; full GET?limit=3 returns 3 items → pass.

    Uses side_effect so both calls to the same path are served in order.
    """
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body(),
                                    headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"})
    )
    mock_router.get(ORDER_PATH).mock(
        side_effect=[
            _lr([order_body("o0"), order_body("o1")], total=3),   # probe
            _lr([order_body(f"o{i}") for i in range(3)], total=3), # full fetch
        ]
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_641):
    """Probe says total=3; full fetch returns only 1 → fail."""
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body(),
                                    headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"})
    )
    mock_router.get(ORDER_PATH).mock(
        side_effect=[
            _lr([order_body()], total=3),       # probe: declares 3
            _lr([order_body("o0")], total=3),   # full: only 1
        ]
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(201, json=order_body(),
                                    headers={"Location": f"{BASE_URL}{ORDER_PATH}/o"})
    )
    mock_router.get(ORDER_PATH).mock(
        return_value=httpx.Response(200, json=[order_body()])  # no X-Total-Count
    )
    result = await TMF641XTotalCountMatchesActual().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_empty(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([], total=3)
    )
    result = await TMF641OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_641):
    mock_router.get(ORDER_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([order_body()], total=1)
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
