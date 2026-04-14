"""Tests for tmf_lint.runner — async orchestration."""
from __future__ import annotations

import pytest
import respx
import httpx

from tests.conftest import BASE_URL, SERVICE_PATH, RESOURCE_PATH, ORDER_PATH
from tmf_lint.runner import run


def _stub_all_apis(router: respx.MockRouter) -> None:
    """Mount minimal stub responses for all three APIs so every rule passes."""
    from tests.conftest import service_body, resource_body, order_body

    # ── TMF638 Service ──────────────────────────────────────────────────────
    router.post(SERVICE_PATH).mock(
        return_value=httpx.Response(
            201, json=service_body(),
            headers={"Location": f"{BASE_URL}{SERVICE_PATH}/svc-001"}
        )
    )
    router.get(SERVICE_PATH).mock(
        return_value=httpx.Response(
            200, json=[service_body()], headers={"X-Total-Count": "1"}
        )
    )
    router.get(f"{SERVICE_PATH}/svc-001").mock(
        return_value=httpx.Response(200, json=service_body())
    )
    router.get(url__regex=rf"{SERVICE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404)
    )
    router.delete(url__regex=rf"{SERVICE_PATH}/.*").mock(
        return_value=httpx.Response(204)
    )
    router.patch(url__regex=rf"{SERVICE_PATH}/.*").mock(
        return_value=httpx.Response(200, json=service_body())
    )

    # ── TMF639 Resource ─────────────────────────────────────────────────────
    router.post(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            201, json=resource_body(),
            headers={"Location": f"{BASE_URL}{RESOURCE_PATH}/res-001"}
        )
    )
    router.get(RESOURCE_PATH).mock(
        return_value=httpx.Response(
            200, json=[resource_body()], headers={"X-Total-Count": "1"}
        )
    )
    router.get(f"{RESOURCE_PATH}/res-001").mock(
        return_value=httpx.Response(200, json=resource_body())
    )
    router.get(url__regex=rf"{RESOURCE_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404)
    )
    router.delete(url__regex=rf"{RESOURCE_PATH}/.*").mock(
        return_value=httpx.Response(204)
    )
    router.patch(url__regex=rf"{RESOURCE_PATH}/.*").mock(
        return_value=httpx.Response(200, json=resource_body())
    )

    # ── TMF641 Order ────────────────────────────────────────────────────────
    router.post(ORDER_PATH).mock(
        return_value=httpx.Response(
            201, json=order_body(),
            headers={"Location": f"{BASE_URL}{ORDER_PATH}/ord-001"}
        )
    )
    router.get(ORDER_PATH).mock(
        return_value=httpx.Response(
            200, json=[order_body()], headers={"X-Total-Count": "1"}
        )
    )
    router.get(f"{ORDER_PATH}/ord-001").mock(
        return_value=httpx.Response(200, json=order_body())
    )
    router.get(url__regex=rf"{ORDER_PATH}/tmf-lint-nonexistent-.*").mock(
        return_value=httpx.Response(404)
    )
    router.delete(url__regex=rf"{ORDER_PATH}/.*").mock(
        return_value=httpx.Response(204)
    )
    router.patch(url__regex=rf"{ORDER_PATH}/.*").mock(
        return_value=httpx.Response(200, json=order_body())
    )


class TestRunner:
    def test_run_returns_lint_report(self):
        with respx.MockRouter(assert_all_called=False) as router:
            _stub_all_apis(router)
            report = run(base_url=BASE_URL, apis=[638, 639, 641])

        assert report.base_url == BASE_URL
        assert set(report.apis) == {638, 639, 641}
        assert len(report.results) > 0

    def test_run_api_filter(self):
        with respx.MockRouter(assert_all_called=False) as router:
            _stub_all_apis(router)
            report = run(base_url=BASE_URL, apis=[638])

        api_set = {r.api for r in report.results}
        assert api_set == {638}

    def test_run_category_filter(self):
        with respx.MockRouter(assert_all_called=False) as router:
            _stub_all_apis(router)
            report = run(base_url=BASE_URL, apis=[638, 639, 641], categories=["http"])

        cat_set = {r.category for r in report.results}
        assert cat_set == {"http"}

    def test_run_report_has_results_for_each_api(self):
        with respx.MockRouter(assert_all_called=False) as router:
            _stub_all_apis(router)
            report = run(base_url=BASE_URL, apis=[638, 639, 641])

        by_api = report.by_api()
        assert 638 in by_api
        assert 639 in by_api
        assert 641 in by_api
