# Changelog

All notable changes to tmf-lint are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] — 2025-04-13

First public release.

### Added

**Rule engine core**
- `BaseRule` ABC — every rule is a subclass with `rule_id`, `api`, `category`, `description`, and an async `check(client, ctx)` method
- `LintContext` — shared key-value store passed between rules in a single run; HTTP rules deposit created entity IDs so later rules can reuse them
- `LintClient` — thin async `httpx` wrapper bound to a single base URL
- `registry.py` — auto-discovers `BaseRule` subclasses by scanning `r_*.py` modules; no registration call required
- `runner.py` — async orchestrator; executes rules in category order and collects `LintReport`
- `reporter.py` — Rich-coloured human output and machine-readable JSON output
- `RuleResult` / `LintReport` dataclasses — the only types that flow between engine, runner, and reporter

**Rules — 39 rules across 5 categories for TMF638, TMF639, TMF641**

| Category | Rules per API |
|---|---|
| `http` | POST→201+Location, GET→200+X-Total-Count, GET unknown id→404, DELETE→204 |
| `mandatory-fields` | id, href, @type, @baseType present on POST and GET responses; href is absolute URL |
| `lifecycle` | Valid transitions accepted (200), illegal transitions rejected (422), terminal states locked, same-state PATCH is a no-op (200) |
| `referential` | DELETE referenced resource→409, POST with non-existent ref→422 |
| `pagination` | limit param respected, X-Total-Count accurate (verified by fetching limit=total), offset beyond total returns empty array |

**CLI**
- `tmf-lint check --url URL --apis N,N --rules CATS --format human|json --timeout N`
- `tmf-lint rules [--apis N,N]` — tabular list of all available rules
- Exit code `0` = all checks passed, `1` = one or more failures (CI/CD friendly)

**Packaging**
- PyPI: `pip install tmf-lint`
- Docker: `docker pull mchavan23/tmf-lint`
- Python 3.10, 3.11, 3.12 supported

### Known limitations

- v0.1 covers TMF638, TMF639, TMF641 only. TMF633, TMF634, TMF688 planned for v0.2.
- All POST payloads use minimal spec-compliant fields. Servers that enforce mandatory fields beyond the TMF spec (e.g. `relatedParty`, `resourceSpecification`, custom `@type` subclasses) may cause setup POSTs to fail, which causes dependent rules to skip gracefully. See README for details.
- No `--fixtures` support yet (v0.2). Point tmf-lint at [tmf-mock](https://github.com/tmf-devkit/tmf-mock) for a clean baseline run.

---

[0.1.0]: https://github.com/tmf-devkit/tmf-lint/releases/tag/v0.1.0
