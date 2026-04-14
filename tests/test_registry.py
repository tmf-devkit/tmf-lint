"""Tests for tmf_lint.rules.registry — rule auto-discovery."""
from tmf_lint.rules.registry import load_rules, list_all_rules
from tmf_lint.rules.base import BaseRule, CATEGORY_ORDER


class TestLoadRules:
    def test_returns_base_rule_instances(self):
        rules = load_rules(apis=[638, 639, 641])
        assert all(isinstance(r, BaseRule) for r in rules)

    def test_all_three_apis_present(self):
        rules = load_rules(apis=[638, 639, 641])
        apis = {r.api for r in rules}
        assert 638 in apis
        assert 639 in apis
        assert 641 in apis

    def test_api_filter_excludes_others(self):
        rules = load_rules(apis=[638])
        assert all(r.api == 638 for r in rules)

    def test_category_filter(self):
        rules = load_rules(apis=[638, 639, 641], categories=["http"])
        assert all(r.category == "http" for r in rules)

    def test_category_filter_multi(self):
        rules = load_rules(apis=[638], categories=["http", "lifecycle"])
        cats = {r.category for r in rules}
        assert cats.issubset({"http", "lifecycle"})

    def test_rules_sorted_by_category_order(self):
        rules = load_rules(apis=[638])
        cat_indices = [CATEGORY_ORDER.index(r.category) for r in rules if r.category in CATEGORY_ORDER]
        assert cat_indices == sorted(cat_indices)

    def test_rule_ids_are_unique(self):
        rules = load_rules(apis=[638, 639, 641])
        ids = [r.rule_id for r in rules]
        assert len(ids) == len(set(ids))

    def test_minimum_rule_count(self):
        # 3 APIs × 5 categories × ≥1 rule each = at least 15
        rules = load_rules(apis=[638, 639, 641])
        assert len(rules) >= 15

    def test_empty_apis_returns_nothing(self):
        rules = load_rules(apis=[])
        assert rules == []

    def test_unsupported_api_silently_skipped(self):
        # 999 is not a known API; should not crash
        rules = load_rules(apis=[999])
        assert rules == []


class TestListAllRules:
    def test_returns_non_empty(self):
        rules = list_all_rules()
        assert len(rules) > 0

    def test_api_filter(self):
        rules = list_all_rules(apis=[639])
        assert all(r.api == 639 for r in rules)
