"""
Shared test helpers — response body factories and path constants.

Imported by rule-level test files. NOT a conftest — just a plain module.
Fixtures (mock_router, lint_client, ctx_*) come from tests/conftest.py
which pytest loads automatically.
"""
from __future__ import annotations

BASE_URL = "http://testserver"

SERVICE_PATH  = "/tmf-api/serviceInventoryManagement/v4/service"
RESOURCE_PATH = "/tmf-api/resourceInventoryManagement/v4/resource"
ORDER_PATH    = "/tmf-api/serviceOrdering/v4/serviceOrder"


def resource_body(rid: str = "res-001") -> dict:
    return {
        "id": rid,
        "href": f"{BASE_URL}{RESOURCE_PATH}/{rid}",
        "@type": "Resource",
        "@baseType": "Resource",
        "name": "test-resource",
        "resourceStatus": "available",
    }


def service_body(sid: str = "svc-001") -> dict:
    return {
        "id": sid,
        "href": f"{BASE_URL}{SERVICE_PATH}/{sid}",
        "@type": "Service",
        "@baseType": "Service",
        "name": "test-service",
        "state": "active",
    }


def order_body(oid: str = "ord-001") -> dict:
    return {
        "id": oid,
        "href": f"{BASE_URL}{ORDER_PATH}/{oid}",
        "@type": "ServiceOrder",
        "@baseType": "ServiceOrder",
        "state": "acknowledged",
        "orderDate": "2024-01-01T00:00:00Z",
        "orderItem": [],
    }
