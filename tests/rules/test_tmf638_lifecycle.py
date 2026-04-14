"""Tests for TMF638 lifecycle rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_lifecycle import (
    TMF638ValidTransitionAccepted,
    TMF638TerminalStateRejected,
    TMF638SameStateAccepted,
)


@pytest.mark.asyncio
async def test_valid_transition_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body("lc-001"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/lc-001"},
        )
    )
    mock_router.patch(f"{SERVICE_PATH}/lc-001").mock(
        return_value=httpx.Response(200, json={**service_body("lc-001"), "state": "inactive"})
    )
    result = await TMF638ValidTransitionAccepted().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_valid_transition_server_rejects(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body("lc-002"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/lc-002"},
        )
    )
    mock_router.patch(f"{SERVICE_PATH}/lc-002").mock(
        return_value=httpx.Response(422, json={"message": "illegal"})
    )
    result = await TMF638ValidTransitionAccepted().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_terminal_state_422_pass(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body("lc-003"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/lc-003"},
        )
    )
    mock_router.patch(f"{SERVICE_PATH}/lc-003").mock(
        side_effect=[
            httpx.Response(200, json={**service_body("lc-003"), "state": "terminated"}),
            httpx.Response(422, json={"message": "terminal state"}),
        ]
    )
    result = await TMF638TerminalStateRejected().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_terminal_state_accepted_by_server_fail(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body("lc-004"),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/lc-004"},
        )
    )
    mock_router.patch(f"{SERVICE_PATH}/lc-004").mock(
        return_value=httpx.Response(200, json=service_body("lc-004"))
    )
    result = await TMF638TerminalStateRejected().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_same_state_200_pass(mock_router, lint_client, ctx_638):
    ctx_638.set("tmf638:service_id", "svc-lc-005")
    mock_router.get(f"{SERVICE_PATH}/svc-lc-005").mock(
        return_value=httpx.Response(200, json=service_body("svc-lc-005"))
    )
    mock_router.patch(f"{SERVICE_PATH}/svc-lc-005").mock(
        return_value=httpx.Response(200, json=service_body("svc-lc-005"))
    )
    result = await TMF638SameStateAccepted().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_same_state_skipped_without_ctx(mock_router, lint_client, ctx_638):
    result = await TMF638SameStateAccepted().check(lint_client, ctx_638)
    assert result.skipped
