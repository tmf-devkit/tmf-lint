"""
tmf-lint — Rule registry.

Discovers all ``BaseRule`` subclasses by importing every ``r_*.py`` module
inside the three API sub-packages.  No explicit registration is required —
dropping a new file into ``tmf_lint/rules/tmf{N}/`` is sufficient.

Usage::

    from tmf_lint.rules.registry import load_rules

    rules = load_rules(apis=[638, 639, 641], categories=None)
"""
from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType

from tmf_lint.rules.base import BaseRule, CATEGORY_ORDER

# Map API numbers to their sub-package names.
_API_PACKAGES: dict[int, str] = {
    638: "tmf_lint.rules.tmf638",
    639: "tmf_lint.rules.tmf639",
    641: "tmf_lint.rules.tmf641",
}


def _import_rule_modules(api: int) -> list[ModuleType]:
    """Import all ``r_*.py`` modules inside the package for *api*."""
    pkg_name = _API_PACKAGES[api]
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return []

    modules: list[ModuleType] = []
    for _finder, modname, _ispkg in pkgutil.iter_modules(pkg.__path__):
        if modname.startswith("r_"):
            modules.append(importlib.import_module(f"{pkg_name}.{modname}"))
    return modules


def _collect_subclasses(module: ModuleType) -> list[type[BaseRule]]:
    """Return all concrete ``BaseRule`` subclasses defined in *module*."""
    found: list[type[BaseRule]] = []
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseRule)
            and obj is not BaseRule
            and not getattr(obj, "__abstractmethods__", None)
        ):
            found.append(obj)
    return found


def load_rules(
    apis: list[int],
    categories: list[str] | None = None,
) -> list[BaseRule]:
    """Return instantiated rules for the requested *apis*, ordered by category.

    Args:
        apis:       API numbers to include (e.g. ``[638, 639, 641]``).
        categories: If supplied, only rules whose category is in this list are
                    returned.  Pass ``None`` to include all categories.

    Returns:
        A list of ``BaseRule`` instances sorted by (api, category order, rule_id).
    """
    rules: list[BaseRule] = []

    for api in apis:
        if api not in _API_PACKAGES:
            continue
        for module in _import_rule_modules(api):
            for cls in _collect_subclasses(module):
                if categories is None or cls.category in categories:
                    rules.append(cls())

    def _sort_key(rule: BaseRule) -> tuple[int, int, str]:
        try:
            cat_order = CATEGORY_ORDER.index(rule.category)
        except ValueError:
            cat_order = 99
        return (rule.api, cat_order, rule.rule_id)

    rules.sort(key=_sort_key)
    return rules


def list_all_rules(apis: list[int] | None = None) -> list[BaseRule]:
    """Return all known rules, optionally filtered by *apis*."""
    target_apis = apis if apis is not None else list(_API_PACKAGES)
    return load_rules(apis=target_apis, categories=None)
