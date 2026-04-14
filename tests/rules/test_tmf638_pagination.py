"""Tests for TMF638 pagination rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_pagination import (
    TMF638LimitQueryParam,
    TMF638XTotalCountMatchesActual,
    TMF638OffsetBeyondTotalReturnsEmpty,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


def _list_resp(items: list, total: int | None = None) -> httpx.Response:
    headers = {"X-Total-Count": str(total)} if total is not None else {}
    return httpx.Response(200, json=items, headers=headers)


# ── TMF638LimitQueryParam ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"}
        )
    )
    mock_router.get(SERVICE_PATH, params={"limit": "1"}).mock(
        return_value=_list_resp([service_body()], total=5)
    )
    result = await TMF638LimitQueryParam().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"}
        )
    )
    mock_router.get(SERVICE_PATH, params={"limit": "1"}).mock(
        return_value=_list_resp([service_body(), service_body("s2")], total=5)
    )
    result = await TMF638LimitQueryParam().check(lint_client, ctx_638)
    assert not result.passed


# ── TMF638XTotalCountMatchesActual (two-request strategy) ───────────────────

@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"}
        )
    )
    # Probe (no params) reports total=4
    mock_router.get(SERVICE_PATH).mock(
        return_value=_list_resp([service_body("s0"), service_body("s1")], total=4)
    )
    # Full fetch (limit=4) returns all 4
    mock_router.get(SERVICE_PATH, params={"limit": "4"}).mock(
        return_value=_list_resp([service_body(f"s{i}") for i in range(4)], total=4)
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"}
        )
    )
    mock_router.get(SERVICE_PATH).mock(
        return_value=_list_resp([service_body()], total=4)
    )
    # limit=4 returns only 2 — header was lying
    mock_router.get(SERVICE_PATH, params={"limit": "4"}).mock(
        return_value=_list_resp([service_body("s0"), service_body("s1")], total=4)
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/s"}
        )
    )
    mock_router.get(SERVICE_PATH).mock(
        return_value=httpx.Response(200, json=[service_body()])
    )
    result = await TMF638XTotalCountMatchesActual().check(lint_client, ctx_638)
    assert not result.passed


# ── TMF638OffsetBeyondTotalReturnsEmpty ──────────────────────────────────────

@pytest.mark.asyncio
async def test_offset_beyond_empty(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_resp([], total=2)
    )
    result = await TMF638OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_resp([service_body()], total=1)
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
