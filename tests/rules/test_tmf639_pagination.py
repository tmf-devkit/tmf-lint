"""Tests for TMF639 pagination rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, RESOURCE_PATH, resource_body
from tmf_lint.rules.tmf639.r_pagination import (
    TMF639LimitQueryParam,
    TMF639XTotalCountMatchesActual,
    TMF639OffsetBeyondTotalReturnsEmpty,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


def _list_response(items: list, total: int | None = None) -> httpx.Response:
    headers = {}
    if total is not None:
        headers["X-Total-Count"] = str(total)
    return httpx.Response(200, json=items, headers=headers)


# ── TMF639LimitQueryParam ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_limit_respected(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    mock_router.get(RESOURCE_PATH, params={"limit": "1"}).mock(
        return_value=_list_response([resource_body()], total=5)
    )
    result = await TMF639LimitQueryParam().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_limit_not_respected(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    mock_router.get(RESOURCE_PATH, params={"limit": "1"}).mock(
        return_value=_list_response([resource_body(), resource_body("r2")], total=5)
    )
    result = await TMF639LimitQueryParam().check(lint_client, ctx_639)
    assert not result.passed


# ── TMF639XTotalCountMatchesActual ───────────────────────────────────────────
# Two-request strategy: probe GET (no params) → then GET?limit=N

@pytest.mark.asyncio
async def test_total_count_accurate_pass(mock_router, lint_client, ctx_639):
    """Probe says total=3; fetching limit=3 returns 3 items → pass."""
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    # Probe response (no params) — reports total=3, returns first page of 2
    mock_router.get(RESOURCE_PATH).mock(
        return_value=_list_response(
            [resource_body("r0"), resource_body("r1")], total=3
        )
    )
    # Full fetch (limit=3) — returns all 3
    mock_router.get(RESOURCE_PATH, params={"limit": "3"}).mock(
        return_value=_list_response(
            [resource_body(f"r{i}") for i in range(3)], total=3
        )
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_total_count_inaccurate_fail(mock_router, lint_client, ctx_639):
    """Probe says total=3; fetching limit=3 only returns 2 → fail."""
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    mock_router.get(RESOURCE_PATH).mock(
        return_value=_list_response([resource_body("r0")], total=3)
    )
    mock_router.get(RESOURCE_PATH, params={"limit": "3"}).mock(
        return_value=_list_response(
            [resource_body("r0"), resource_body("r1")], total=3  # only 2, not 3
        )
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_zero_after_seed_fail(mock_router, lint_client, ctx_639):
    """X-Total-Count=0 after seeding is unexpected → fail."""
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    mock_router.get(RESOURCE_PATH).mock(
        return_value=_list_response([], total=0)
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_total_count_missing_header_fail(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/r"}
        )
    )
    mock_router.get(RESOURCE_PATH).mock(
        return_value=httpx.Response(200, json=[resource_body()])  # no header
    )
    result = await TMF639XTotalCountMatchesActual().check(lint_client, ctx_639)
    assert not result.passed


# ── TMF639OffsetBeyondTotalReturnsEmpty ──────────────────────────────────────

@pytest.mark.asyncio
async def test_offset_beyond_returns_empty(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_response([], total=3)
    )
    result = await TMF639OffsetBeyondTotalReturnsEmpty().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_offset_beyond_returns_items_fail(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH, params={"offset": "999999", "limit": "10"}).mock(
        return_value=_list_response([resource_body()], total=1)
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
