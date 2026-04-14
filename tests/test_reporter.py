"""Tests for tmf_lint.reporter — human and JSON output formatters."""
from __future__ import annotations

import json
import io

import pytest
from rich.console import Console

from tmf_lint.result import LintReport, RuleResult
from tmf_lint.reporter import print_human, print_json


def _make_report(passed: int = 2, failed: int = 1, skipped: int = 0) -> LintReport:
    report = LintReport(base_url="http://localhost:8000", apis=[638, 639])
    for i in range(passed):
        report.results.append(
            RuleResult(f"PASS-{i:03}", 638, "http", f"Pass rule {i}", True)
        )
    for i in range(failed):
        report.results.append(
            RuleResult(f"FAIL-{i:03}", 639, "lifecycle", f"Fail rule {i}", False, message="bad")
        )
    for i in range(skipped):
        report.results.append(
            RuleResult(
                f"SKIP-{i:03}", 638, "referential", f"Skip rule {i}",
                False, skipped=True, message="prereq failed"
            )
        )
    return report


class TestPrintHuman:
    def _capture(self, report: LintReport) -> str:
        buf = io.StringIO()
        con = Console(file=buf, highlight=False, markup=False)
        print_human(report, console=con)
        return buf.getvalue()

    def test_contains_pass_count(self):
        out = self._capture(_make_report(passed=3, failed=0))
        assert "3" in out

    def test_contains_fail_count(self):
        out = self._capture(_make_report(passed=1, failed=2))
        assert "2" in out

    def test_contains_base_url(self):
        out = self._capture(_make_report())
        assert "localhost:8000" in out

    def test_exit_code_0_when_all_passed(self):
        out = self._capture(_make_report(passed=2, failed=0))
        assert "Exit code: 0" in out

    def test_exit_code_1_when_failures(self):
        out = self._capture(_make_report(passed=1, failed=1))
        assert "Exit code: 1" in out

    def test_shows_skipped_when_present(self):
        out = self._capture(_make_report(passed=1, failed=0, skipped=1))
        assert "skipped" in out.lower()

    def test_rule_description_in_output(self):
        out = self._capture(_make_report())
        assert "Pass rule 0" in out


class TestPrintJson:
    def _capture_json(self, report: LintReport) -> dict:
        buf = io.StringIO()
        import sys
        original_stdout = sys.stdout
        sys.stdout = buf
        try:
            print_json(report)
        finally:
            sys.stdout = original_stdout
        return json.loads(buf.getvalue())

    def test_json_has_required_keys(self):
        d = self._capture_json(_make_report())
        assert "base_url" in d
        assert "apis" in d
        assert "summary" in d
        assert "results" in d

    def test_json_summary_counts(self):
        d = self._capture_json(_make_report(passed=2, failed=1))
        assert d["summary"]["passed"] == 2
        assert d["summary"]["failed"] == 1

    def test_json_results_is_list(self):
        d = self._capture_json(_make_report())
        assert isinstance(d["results"], list)

    def test_json_each_result_has_severity(self):
        d = self._capture_json(_make_report())
        for r in d["results"]:
            assert r["severity"] in ("pass", "fail", "skip")

    def test_json_is_valid(self):
        """print_json output should be parseable JSON — no extra text."""
        buf = io.StringIO()
        import sys
        sys.stdout, orig = buf, sys.stdout
        try:
            print_json(_make_report())
        finally:
            sys.stdout = orig
        json.loads(buf.getvalue())  # raises if invalid
