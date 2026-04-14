"""
Shared pytest fixtures for tmf-lint tests.

All HTTP calls are mocked with respx — no live server is required.

Fixture hierarchy
─────────────────
  mock_transport   — respx.MockTransport used for both fixtures below
  lint_client      — LintClient wired to the mock transport
  ctx              — default LintContext (all 3 APIs, no category filter)
  ctx_638_only     — LintContext restricted to TMF638
  ctx_639_only     — LintContext restricted to TMF639
  ctx_641_only     — LintContext restricted to TMF641
"""
from __future__ import annotations

import pytest
import respx
import httpx

from tmf_lint.client import LintClient
from tmf_lint.context import LintContext

BASE_URL = "http://testserver"

# Path prefixes used by rules
SERVICE_PATH = "/tmf-api/serviceInventoryManagement/v4/service"
RESOURCE_PATH = "/tmf-api/resourceInventoryManagement/v4/resource"
ORDER_PATH = "/tmf-api/serviceOrdering/v4/serviceOrder"


@pytest.fixture
def mock_router():
    """An active respx router that intercepts all httpx requests."""
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


@pytest.fixture
def lint_client(mock_router):
    """A LintClient whose transport is fully mocked by respx."""
    # respx patches httpx globally when active, so we just create the client.
    return LintClient(base_url=BASE_URL)


@pytest.fixture
def ctx():
    """Default LintContext with all three supported APIs."""
    return LintContext(base_url=BASE_URL, apis=[638, 639, 641])


@pytest.fixture
def ctx_638():
    return LintContext(base_url=BASE_URL, apis=[638])


@pytest.fixture
def ctx_639():
    return LintContext(base_url=BASE_URL, apis=[639])


@pytest.fixture
def ctx_641():
    return LintContext(base_url=BASE_URL, apis=[641])


# ── Canned response helpers ──────────────────────────────────────────────────

def resource_body(rid: str = "res-001") -> dict:
    return {
        "id": rid,
        "href": f"{BASE_URL}/tmf-api/resourceInventoryManagement/v4/resource/{rid}",
        "@type": "Resource",
        "@baseType": "Resource",
        "name": "test-resource",
        "resourceStatus": "available",
    }


def service_body(sid: str = "svc-001") -> dict:
    return {
        "id": sid,
        "href": f"{BASE_URL}/tmf-api/serviceInventoryManagement/v4/service/{sid}",
        "@type": "Service",
        "@baseType": "Service",
        "name": "test-service",
        "state": "active",
    }


def order_body(oid: str = "ord-001") -> dict:
    return {
        "id": oid,
        "href": f"{BASE_URL}/tmf-api/serviceOrdering/v4/serviceOrder/{oid}",
        "@type": "ServiceOrder",
        "@baseType": "ServiceOrder",
        "state": "acknowledged",
        "orderDate": "2024-01-01T00:00:00Z",
        "orderItem": [],
    }
