"""
tmf-lint — LintContext.

A single LintContext instance is created per `tmf-lint check` run and passed to
every rule in turn.  Rules use it to:

  * Read configuration (base_url, which APIs are enabled, category filter).
  * Share discovered entity IDs so later rules can reuse them without making
    redundant POST requests.  For example, the HTTP-001 rule POSTs a resource
    and stores its id; the lifecycle and pagination rules read that id instead
    of creating their own.

Convention for context keys
────────────────────────────
  "tmf638:service_id"      — str  — first service created during the run
  "tmf638:service_ids"     — list[str]
  "tmf639:resource_id"     — str  — first resource created during the run
  "tmf639:resource_ids"    — list[str]
  "tmf641:order_id"        — str  — first service order created
  "tmf641:order_ids"       — list[str]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LintContext:
    """Shared mutable state passed between rules for a single lint run."""

    base_url: str
    apis: list[int]
    rule_filter: list[str] | None = None
    """If set, only rules whose *category* appears in this list are executed."""

    _store: dict[str, Any] = field(default_factory=dict)

    # ── Store helpers ────────────────────────────────────────────────────────

    def set(self, key: str, value: Any) -> None:
        """Store an arbitrary value under *key*."""
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Return the stored value for *key*, or *default* if absent."""
        return self._store.get(key, default)

    def has(self, key: str) -> bool:
        """Return True if *key* is present in the store."""
        return key in self._store

    # ── Convenience typed accessors ──────────────────────────────────────────

    def get_str(self, key: str) -> str | None:
        """Return a stored string, or None."""
        v = self._store.get(key)
        return v if isinstance(v, str) else None

    def get_list(self, key: str) -> list:
        """Return a stored list, or an empty list."""
        v = self._store.get(key, [])
        return v if isinstance(v, list) else []

    def append(self, key: str, value: Any) -> None:
        """Append *value* to a stored list, creating it if absent."""
        lst = self.get_list(key)
        lst.append(value)
        self._store[key] = lst
