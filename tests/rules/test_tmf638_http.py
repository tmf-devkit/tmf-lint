"""Tests for TMF638 HTTP rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_http import (
    TMF638PostReturns201,
    TMF638GetListReturns200,
    TMF638GetUnknownIdReturns404,
    TMF638DeleteReturns204,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


# ── TMF638PostReturns201 ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_201_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"},
        )
    )
    result = await TMF638PostReturns201().check(lint_client, ctx_638)
    assert result.passed
    assert ctx_638.get_str("tmf638:service_id") == "svc-001"


@pytest.mark.asyncio
async def test_post_missing_location(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(201, json=service_body())
    )
    result = await TMF638PostReturns201().check(lint_client, ctx_638)
    assert not result.passed
    assert "Location" in result.message


@pytest.mark.asyncio
async def test_post_wrong_status(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(200, json=service_body())
    )
    result = await TMF638PostReturns201().check(lint_client, ctx_638)
    assert not result.passed


# ── TMF638GetListReturns200 ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_list_pass(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH).mock(
        return_value=httpx.Response(
            200, json=[service_body()], headers={"X-Total-Count": "1"}
        )
    )
    result = await TMF638GetListReturns200().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_get_list_missing_header(mock_router, lint_client, ctx_638):
    mock_router.get(SERVICE_PATH).mock(
        return_value=httpx.Response(200, json=[service_body()])
    )
    result = await TMF638GetListReturns200().check(lint_client, ctx_638)
    assert not result.passed


# ── TMF638GetUnknownIdReturns404 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_unknown_404_pass(mock_router, lint_client, ctx_638):
    mock_router.get(url__regex=rf"{SERVICE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404, json={"message": "not found"})
    )
    result = await TMF638GetUnknownIdReturns404().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_get_unknown_200_fail(mock_router, lint_client, ctx_638):
    mock_router.get(url__regex=rf"{SERVICE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(200, json=service_body())
    )
    result = await TMF638GetUnknownIdReturns404().check(lint_client, ctx_638)
    assert not result.passed


# ── TMF638DeleteReturns204 ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_204_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=service_body("del-001"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/del-001"},
        )
    )
    mock_router.delete(f"{SERVICE_PATH}/del-001").mock(
        return_value=httpx.Response(204)
    )
    result = await TMF638DeleteReturns204().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_delete_wrong_status(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201,
            json=service_body("del-002"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/del-002"},
        )
    )
    mock_router.delete(f"{SERVICE_PATH}/del-002").mock(
        return_value=httpx.Response(200)
    )
    result = await TMF638DeleteReturns204().check(lint_client, ctx_638)
    assert not result.passed
