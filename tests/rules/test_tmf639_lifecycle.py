"""Tests for TMF639 lifecycle rules."""
from __future__ import annotations

import httpx
import pytest

from tests.helpers import BASE_URL, RESOURCE_PATH, resource_body
from tmf_lint.rules.tmf639.r_lifecycle import (
    TMF639InvalidTransitionRejected,
    TMF639SameStateAccepted,
    TMF639ValidTransitionAccepted,
)


@pytest.mark.asyncio
async def test_valid_transition_pass(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body("lc-001"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/lc-001"},
        )
    )
    suspended_body = {**resource_body("lc-001"), "resourceStatus": "suspended"}
    mock_router.patch(f"{RESOURCE_PATH}/lc-001").mock(
        return_value=httpx.Response(200, json=suspended_body)
    )
    result = await TMF639ValidTransitionAccepted().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_valid_transition_rejected_by_server(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body("lc-002"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/lc-002"},
        )
    )
    mock_router.patch(f"{RESOURCE_PATH}/lc-002").mock(
        return_value=httpx.Response(422, json={"message": "illegal transition"})
    )
    result = await TMF639ValidTransitionAccepted().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_invalid_transition_422_pass(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body("lc-003"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/lc-003"},
        )
    )
    suspended_body = {**resource_body("lc-003"), "resourceStatus": "suspended"}
    mock_router.patch(f"{RESOURCE_PATH}/lc-003").mock(
        side_effect=[
            httpx.Response(200, json=suspended_body),
            httpx.Response(422, json={"message": "illegal transition"}),
        ]
    )
    result = await TMF639InvalidTransitionRejected().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_invalid_transition_accepted_by_server_fail(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body("lc-004"),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/lc-004"},
        )
    )
    mock_router.patch(f"{RESOURCE_PATH}/lc-004").mock(
        return_value=httpx.Response(200, json=resource_body("lc-004"))
    )
    result = await TMF639InvalidTransitionRejected().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_same_state_200_pass(mock_router, lint_client, ctx_639):
    ctx_639.set("tmf639:resource_id", "res-lc-005")
    mock_router.get(f"{RESOURCE_PATH}/res-lc-005").mock(
        return_value=httpx.Response(200, json=resource_body("res-lc-005"))
    )
    mock_router.patch(f"{RESOURCE_PATH}/res-lc-005").mock(
        return_value=httpx.Response(200, json=resource_body("res-lc-005"))
    )
    result = await TMF639SameStateAccepted().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_same_state_skips_without_ctx(mock_router, lint_client, ctx_639):
    result = await TMF639SameStateAccepted().check(lint_client, ctx_639)
    assert result.skipped
