"""Tests for TMF638 pagination rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_pagination import (
    TMF638LimitQueryParam,
    TMF638OffsetBeyondTotalReturnsEmpty,
    TMF638XTotalCountMatchesActual,
)


def _lr(items: list, total: int | None = None) -> httpx.Response:
    headers = {"X-Total-Count": str(total)} if total is not None else {}
    return httpx.Response(200, json=items, headers=headers)


@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body(),
                                    headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"})
    )
    mock_router.get(SERVICE_PATH, params={"limit": "1"}).mock(
        return_value=_lr([service_body()], total=5)
    )
    result = await TMF638LimitQueryParam().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body(),
                                    headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"})
    )
    mock_router.get(SERVICE_PATH, params={"limit": "1"}).mock(
        return_value=_lr([service_body(), service_body("s2")], total=5)
    )
    result = await TMF638LimitQueryParam().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_638):
    """Probe GET (no params) returns total=4; full GET?limit=4 returns 4 items → pass.

    Uses side_effect on a single route so both GETs to the same path are
    served in order — avoids the respx param-matching ambiguity where a
    no-params route also matches requests that carry params.
    """
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body(),
                                    headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"})
    )
    # call 1: probe (no params) → reports total=4, page of 2
    # call 2: full fetch (?limit=4) → returns all 4
    mock_router.get(SERVICE_PATH).mock(
        side_effect=[
            _lr([service_body("s0"), service_body("s1")], total=4),
            _lr([service_body(f"s{i}") for i in range(4)], total=4),
        ]
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_638):
    """Probe says total=4; full fetch returns only 2 → fail."""
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body(),
                                    headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"})
    )
    mock_router.get(SERVICE_PATH).mock(
        side_effect=[
            _lr([service_body("s0")], total=4),           # probe: declares 4
            _lr([service_body("s0"), service_body("s1")], total=4),  # full: only 2
        ]
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body(),
                                    headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"})
    )
    mock_router.get(SERVICE_PATH).mock(
        return_value=httpx.Response(200, json=[service_body()])  # no X-Total-Count
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_empty(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([], total=2)
    )
    result = await TMF638OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_lr([service_body()], total=1)
    )
    result = await TMF638OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_offset_beyond_error_code_fail(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=httpx.Response(400, json={"message": "bad offset"})
    )
    result = await TMF638OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_638)
    assert not result.passed
