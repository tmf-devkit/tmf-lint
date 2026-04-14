"""
Shared pytest fixtures for tmf-lint tests.
Constants and body helpers live in tests/helpers.py.
"""
from __future__ import annotations

import pytest
import respx

from tests.helpers import BASE_URL
from tmf_lint.client import LintClient
from tmf_lint.context import LintContext


@pytest.fixture
def mock_router():
    with respx.MockRouter(assert_all_called=False) as router:
        yield router


@pytest.fixture
def lint_client(mock_router):
    return LintClient(base_url=BASE_URL)


@pytest.fixture
def ctx():
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
