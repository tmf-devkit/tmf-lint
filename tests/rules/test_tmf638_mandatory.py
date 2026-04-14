"""Tests for TMF638 mandatory fields rules."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, SERVICE_PATH, service_body
from tmf_lint.rules.tmf638.r_mandatory_fields import (
    TMF638PostResponseHasMandatoryFields,
    TMF638GetResponseHasMandatoryFields,
)


@pytest.fixture(autouse=True)
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


# ── TMF638PostResponseHasMandatoryFields ─────────────────────────────────────

@pytest.mark.asyncio
async def test_post_all_fields_present(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"}
        )
    )
    result = await TMF638PostResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_post_missing_base_type(mock_router, lint_client, ctx_638):
    body = service_body()
    del body["@baseType"]
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"}
        )
    )
    result = await TMF638PostResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert not result.passed
    assert "@baseType" in result.message


@pytest.mark.asyncio
async def test_post_missing_id(mock_router, lint_client, ctx_638):
    body = service_body()
    del body["id"]
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=body,
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"}
        )
    )
    result = await TMF638PostResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert not result.passed


@pytest.mark.asyncio
async def test_post_non_201_skipped(mock_router, lint_client, ctx_638):
    mock_router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(503, json={"message": "unavailable"})
    )
    result = await TMF638PostResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert result.skipped


# ── TMF638GetResponseHasMandatoryFields ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_fields_present(mock_router, lint_client, ctx_638):
    ctx_638.set("tmf638:service_id", "svc-001")
    mock_router.get(f"{SERVICE_PATH}/svc-001").mock(
        return_value=httpx.Response(200, json=service_body("svc-001"))
    )
    result = await TMF638GetResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert result.passed


@pytest.mark.asyncio
async def test_get_relative_href_fails(mock_router, lint_client, ctx_638):
    ctx_638.set("tmf638:service_id", "svc-002")
    body = service_body("svc-002")
    body["href"] = "/service/svc-002"
    mock_router.get(f"{SERVICE_PATH}/svc-002").mock(
        return_value=httpx.Response(200, json=body)
    )
    result = await TMF638GetResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert not result.passed
    assert "href" in result.message


@pytest.mark.asyncio
async def test_get_skipped_without_ctx(mock_router, lint_client, ctx_638):
    result = await TMF638GetResponseHasMandatoryFields().check(lint_client, ctx_638)
    assert result.skipped
