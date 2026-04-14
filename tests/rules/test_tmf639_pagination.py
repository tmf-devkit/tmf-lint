"""Tests for TMF639 pagination rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, RESOURCE_PATH, resource_body
from tmf_lint.rules.tmf639.r_pagination import (
    TMF639LimitQueryParam,
    TMF639OffsetBeyondTotalReturnsEmpty,
    TMF639XTotalCountMatchesActual,
)


def _lr(items: list, total: int | None = None) -> httpx.Response:
    headers = {"X-Total-Count": str(total)} if total is not None else {}
    return httpx.Response(200, json=items, headers=headers)


@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH, params={"limit": "1"}).mock(
        return_value=_lr([resource_body()], total=5)
    )
    result = await TMF639LimitQueryParam().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH, params={"limit": "1"}).mock(
        return_value=_lr([resource_body(), resource_body("r2")], total=5)
    )
    result = await TMF639LimitQueryParam().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_639):
    """Probe GET returns total=3; full GET?limit=3 returns 3 items → pass.

    Uses side_effect so both calls to the same path are served in order.
    """
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH).mock(
        side_effect=[
            _lr([resource_body("r0"), resource_body("r1")], total=3),   # probe
            _lr([resource_body(f"r{i}") for i in range(3)], total=3),   # full fetch
        ]
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_639):
    """Probe says total=3; full fetch returns only 2 → fail."""
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH).mock(
        side_effect=[
            _lr([resource_body("r0")], total=3),                         # probe: declares 3
            _lr([resource_body("r0"), resource_body("r1")], total=3),    # full: only 2
        ]
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_zero_after_seed_fail(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH).mock(return_value=_lr([], total=0))
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body(),
                                    headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"})
    )
    mock_router.get(RESOURCE_PATH).mock(
        return_value=httpx.Response(200, json=[resource_body()])  # no X-Total-Count
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_empty(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([], total=3)
    )
    result = await TMF639OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([resource_body()], total=1)
    )
    result = await TMF639OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_error_code(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=httpx.Response(400, json={"message": "invalid offset"})
    )
    result = await TMF639OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_639)
    assert not result.passed
