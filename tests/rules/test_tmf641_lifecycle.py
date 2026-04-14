"""Tests for TMF641 lifecycle rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, ORDER_PATH, order_body
from tmf_lint.rules.tmf641.r_lifecycle import (
    TMF641SameStateAccepted,
    TMF641TerminalStateRejected,
    TMF641ValidTransitionAccepted,
)


@pytest.mark.asyncio
async def test_valid_transition_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("lc-001"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/lc-001"},
        )
    )
    mock_router.patch(f"{ORDER_PATH}/lc-001").mock(
        return_value=httpx.Response(200, json={**order_body("lc-001"), "state": "inProgress"})
    )
    result = await TMF641ValidTransitionAccepted().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_valid_transition_wrong_initial_state_skipped(mock_router, lint_client, ctx_641):
    body = order_body("lc-002")
    body["state"] = "inProgress"
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/lc-002"},
        )
    )
    result = await TMF641ValidTransitionAccepted().check(lint_client, ctx_641)
    assert result.skipped


@pytest.mark.asyncio
async def test_valid_transition_server_rejects(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("lc-003"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/lc-003"},
        )
    )
    mock_router.patch(f"{ORDER_PATH}/lc-003").mock(
        return_value=httpx.Response(422, json={"message": "illegal transition"})
    )
    result = await TMF641ValidTransitionAccepted().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_terminal_state_422_pass(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("lc-004"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/lc-004"},
        )
    )
    mock_router.patch(f"{ORDER_PATH}/lc-004").mock(
        side_effect=[
            httpx.Response(200, json={**order_body("lc-004"), "state": "inProgress"}),
            httpx.Response(200, json={**order_body("lc-004"), "state": "completed"}),
            httpx.Response(422, json={"message": "terminal state"}),
        ]
    )
    result = await TMF641TerminalStateRejected().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_terminal_state_accepted_by_server_fail(mock_router, lint_client, ctx_641):
    mock_router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body("lc-005"),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/lc-005"},
        )
    )
    mock_router.patch(f"{ORDER_PATH}/lc-005").mock(
        return_value=httpx.Response(200, json=order_body("lc-005"))
    )
    result = await TMF641TerminalStateRejected().check(lint_client, ctx_641)
    assert not result.passed


@pytest.mark.asyncio
async def test_same_state_200_pass(mock_router, lint_client, ctx_641):
    ctx_641.set("tmf641:order_id", "ord-lc-006")
    mock_router.get(f"{ORDER_PATH}/ord-lc-006").mock(
        return_value=httpx.Response(200, json=order_body("ord-lc-006"))
    )
    mock_router.patch(f"{ORDER_PATH}/ord-lc-006").mock(
        return_value=httpx.Response(200, json=order_body("ord-lc-006"))
    )
    result = await TMF641SameStateAccepted().check(lint_client, ctx_641)
    assert result.passed


@pytest.mark.asyncio
async def test_same_state_skipped_without_ctx(mock_router, lint_client, ctx_641):
    result = await TMF641SameStateAccepted().check(lint_client, ctx_641)
    assert result.skipped
