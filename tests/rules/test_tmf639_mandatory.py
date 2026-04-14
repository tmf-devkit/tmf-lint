"""Tests for TMF639 mandatory fields rules."""
from __future__ import annotations

import pytest
import httpx

from tests.helpers import BASE_URL, RESOURCE_PATH, resource_body
from tmf_lint.rules.tmf639.r_mandatory_fields import (
    TMF639PostResponseHasMandatoryFields,
    TMF639GetResponseHasMandatoryFields,
)


@pytest.mark.asyncio
async def test_post_all_fields_present(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/res-001"}
        )
    )
    result = await TMF639PostResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_post_missing_type_field(mock_router, lint_client, ctx_639):
    body = resource_body()
    del body["@type"]
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/res-001"}
        )
    )
    result = await TMF639PostResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert not result.passed
    assert "@type" in result.message


@pytest.mark.asyncio
async def test_post_missing_href(mock_router, lint_client, ctx_639):
    body = resource_body()
    del body["href"]
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/res-001"}
        )
    )
    result = await TMF639PostResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert not result.passed


@pytest.mark.asyncio
async def test_post_non_201_skipped(mock_router, lint_client, ctx_639):
    mock_router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(500, json={"message": "internal error"})
    )
    result = await TMF639PostResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert result.skipped


@pytest.mark.asyncio
async def test_get_all_fields_present(mock_router, lint_client, ctx_639):
    ctx_639.set("tmf639:resource_id", "res-001")
    mock_router.get(f"{RESOURCE_PATH}/res-001").mock(
        return_value=httpx.Response(200, json=resource_body("res-001"))
    )
    result = await TMF639GetResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert result.passed


@pytest.mark.asyncio
async def test_get_relative_href_fails(mock_router, lint_client, ctx_639):
    ctx_639.set("tmf639:resource_id", "res-002")
    body = resource_body("res-002")
    body["href"] = "/resource/res-002"
    mock_router.get(f"{RESOURCE_PATH}/res-002").mock(
        return_value=httpx.Response(200, json=body)
    )
    result = await TMF639GetResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert not result.passed
    assert "href" in result.message


@pytest.mark.asyncio
async def test_get_skipped_without_ctx(mock_router, lint_client, ctx_639):
    result = await TMF639GetResponseHasMandatoryFields().check(lint_client, ctx_639)
    assert result.skipped
