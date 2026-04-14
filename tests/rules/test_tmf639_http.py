"""Tests for TMF639 HTTP rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, RESOURCE_PATH, resource_body
from tmf_lint.rules.tmf639.r_http import (
    TMF639PostReturns201,
    TMF639GetListReturns200,
    TMF639GetUnknownIdReturns404,
    TMF639DeleteReturns204,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


# ── TMF639PostReturns201 ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_201_pass(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/res-001"},
        )
    )
    result = await TMF639PostReturns201().check(lint_client, ctx_639)
    assert result.passed
    assert ctx_639.get_str("tmf639:resource_id") == "res-001"


@pytest.mark.asyncio
async def test_post_201_missing_location(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(201, json=resource_body())
    )
    result = await TMF639PostReturns201().check(lint_client, ctx_639)
    assert not result.passed
    assert "Location" in result.message


@pytest.mark.asyncio
async def test_post_201_wrong_status(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(200, json=resource_body())
    )
    result = await TMF639PostReturns201().check(lint_client, ctx_639)
    assert not result.passed


# ── TMF639GetListReturns200 ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_list_200_pass(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            200,
            json=[resource_body()],
            headers={"X-Total-Count": "1"},
        )
    )
    result = await TMF639GetListReturns200().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_get_list_missing_header(mock_router, lint_client, ctx_639):
    mock_router.get(RESOURCE_PATH).mock(
        return_value=httpx.Response(200, json=[resource_body()])
    )
    result = await TMF639GetListReturns200().check(lint_client, ctx_639)
    assert not result.passed
    assert "X-Total-Count" in result.message


# ── TMF639GetUnknownIdReturns404 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_unknown_404_pass(mock_router, lint_client, ctx_639):
    mock_router.get(url__regex=rf"{RESOURCE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    result = await TMF639GetUnknownIdReturns404().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_get_unknown_returns_200_fail(mock_router, lint_client, ctx_639):
    mock_router.get(url__regex=rf"{RESOURCE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(200, json=resource_body())
    )
    result = await TMF639GetUnknownIdReturns404().check(lint_client, ctx_639)
    assert not result.passed


# ── TMF639DeleteReturns204 ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_204_pass(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=resource_body("del-001"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/del-001"},
        )
    )
    mock_router.delete(f"{RESOURCE_PATH}/del-001").mock(
        return_value=httpx.Response(204)
    )
    result = await TMF639DeleteReturns204().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_delete_wrong_status(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=resource_body("del-002"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/del-002"},
        )
    )
    mock_router.delete(f"{RESOURCE_PATH}/del-002").mock(
        return_value=httpx.Response(200)
    )
    result = await TMF639DeleteReturns204().check(lint_client, ctx_639)
    assert not result.passed
