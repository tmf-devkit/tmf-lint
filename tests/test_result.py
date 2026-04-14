"""Tests for tmf_lint.result — RuleResult and LintReport."""
import pytest
from tmf_lint.result import RuleResult, LintReport, Severity


def _make_result(passed: bool, skipped: bool = False) -> RuleResult:
    return RuleResult(
        rule_id="TEST-001",
        api=638,
        category="http",
        description="test rule",
        passed=passed,
        skipped=skipped,
        message="ok" if passed else "fail reason",
    )


class TestRuleResult:
    def test_severity_pass(self):
        r = _make_result(passed=True)
        assert r.severity == Severity.PASS

    def test_severity_fail(self):
        r = _make_result(passed=False)
        assert r.severity == Severity.FAIL

    def test_severity_skip(self):
        r = _make_result(passed=False, skipped=True)
        assert r.severity == Severity.SKIP

    def test_to_dict_keys(self):
        r = _make_result(passed=True)
        d = r.to_dict()
        for key in ("rule_id", "api", "category", "description", "severity", "message"):
            assert key in d

    def test_to_dict_severity_value(self):
        assert _make_result(passed=True).to_dict()["severity"] == "pass"
        assert _make_result(passed=False).to_dict()["severity"] == "fail"
        assert _make_result(passed=False, skipped=True).to_dict()["severity"] == "skip"


class TestLintReport:
    def _make_report(self) -> LintReport:
        report = LintReport(base_url="http://localhost:8000", apis=[638, 639])
        report.results = [
            _make_result(passed=True),
            _make_result(passed=False),
            _make_result(passed=False, skipped=True),
        ]
        return report

    def test_counts(self):
        r = self._make_report()
        assert r.n_passed == 1
        assert r.n_failed == 1
        assert r.n_skipped == 1

    def test_all_passed_false_when_failures(self):
        assert not self._make_report().all_passed

    def test_all_passed_true_when_no_failures(self):
        report = LintReport(base_url="http://localhost:8000", apis=[638])
        report.results = [_make_result(passed=True)]
        assert report.all_passed

    def test_by_api_grouping(self):
        report = LintReport(base_url="http://localhost:8000", apis=[638, 639])
        report.results = [
            RuleResult("A", 638, "http", "d", True),
            RuleResult("B", 639, "http", "d", True),
            RuleResult("C", 638, "http", "d", False),
        ]
        groups = report.by_api()
        assert set(groups.keys()) == {638, 639}
        assert len(groups[638]) == 2
        assert len(groups[639]) == 1

    def test_to_dict_structure(self):
        d = self._make_report().to_dict()
        assert "base_url" in d
        assert "summary" in d
        assert d["summary"]["passed"] == 1
        assert d["summary"]["failed"] == 1
        assert d["summary"]["skipped"] == 1
        assert len(d["results"]) == 3
