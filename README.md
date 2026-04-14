# tmf-lint

[![CI](https://github.com/tmf-devkit/tmf-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/tmf-devkit/tmf-lint/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/tmf-lint)](https://pypi.org/project/tmf-lint/)
[![Python](https://img.shields.io/pypi/pyversions/tmf-lint)](https://pypi.org/project/tmf-lint/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

**Runtime conformance checker for TMForum Open API implementations.**

tmf-lint points at a running TMF API server and validates its *behaviour* against the TMForum Open API v4.0.0 spec. Think ESLint for TMF APIs — not a Swagger/OAS linter (TMFValidator does that), but a live HTTP behaviour validator.

Part of the [TMF DevKit](https://github.com/tmf-devkit) open-source toolchain.

---

## Quick start

```bash
pip install tmf-lint

# Option A — use tmf-mock as the target (recommended for a clean baseline)
pip install tmf-mock
tmf-mock start --apis 638,639,641

# Option B — point at your own server
# (read the "Target server requirements" section below first)

# Run all conformance checks
tmf-lint check --url http://localhost:8000 --apis 638,639,641
```

---

## What it checks

39 rules across 5 categories for TMF638, TMF639, and TMF641.

| Category | What is validated |
|---|---|
| `http` | POST→201 with Location header, GET list→200 with X-Total-Count, GET unknown id→404, DELETE→204 |
| `mandatory-fields` | `id`, `href`, `@type`, `@baseType` present on every response; `href` is an absolute URL |
| `lifecycle` | Valid state transitions accepted (200), illegal transitions rejected (422), terminal states locked, same-state PATCH is a no-op (200) |
| `referential` | DELETE a resource referenced by a service→409, POST with a non-existent reference→422 |
| `pagination` | `limit` param respected, `X-Total-Count` accurate (verified by fetching `limit=total`), `offset` beyond total returns empty array not an error |

---

## CLI reference

```bash
# Check all rules against all three supported APIs
tmf-lint check --url http://myserver:8080 --apis 638,639,641

# Check only specific rule categories
tmf-lint check --url http://myserver:8080 --apis 638 --rules http,lifecycle

# JSON output for CI/CD pipelines
tmf-lint check --url http://myserver:8080 --format json

# List all available rules
tmf-lint rules

# Filter rule list by API
tmf-lint rules --apis 639

# Show version
tmf-lint --version
```

Exit code `0` = all checks passed. Exit code `1` = one or more failures.

---

## Target server requirements

tmf-lint **creates, modifies, and deletes real data** on the server it checks.
It sends minimal spec-compliant payloads (only fields defined in the TMF v4.0.0 schema).

**Always point tmf-lint at a test or mock instance — never at production.**

### If your server enforces fields beyond the TMF spec

Some implementations require fields that the spec marks as optional — for example `relatedParty`, `resourceSpecification`, a specific `@type` subclass, or a valid `serviceSpecification` reference. If a setup POST is rejected because of a missing field, the rule that depends on it will **skip** gracefully (you will see ⏭ in the output) rather than crash. You will not get a false failure, but you will not get a pass signal either.

In that case the recommended approach for v0.1 is to run tmf-lint against [tmf-mock](https://github.com/tmf-devkit/tmf-mock) first to establish a clean baseline, then use the results to understand which rules your server needs to satisfy. A `--fixtures` option (v0.2) will allow you to supply custom POST payloads for your specific implementation.

### URL base path

tmf-lint expects the standard TMForum base paths:

| API | Path |
|---|---|
| TMF638 | `/tmf-api/serviceInventoryManagement/v4/service` |
| TMF639 | `/tmf-api/resourceInventoryManagement/v4/resource` |
| TMF641 | `/tmf-api/serviceOrdering/v4/serviceOrder` |

---

## Docker

```bash
# Run against a local server
docker run --rm --network host mchavan23/tmf-lint \
  check --url http://localhost:8000 --apis 638,639,641

# JSON output
docker run --rm --network host mchavan23/tmf-lint \
  check --url http://localhost:8000 --format json
```

---

## CI/CD integration

```yaml
# GitHub Actions example
- name: TMF API conformance check
  run: |
    pip install tmf-lint
    tmf-lint check --url http://localhost:8000 --apis 638,639,641 --format json \
      | tee tmf-lint-report.json
    # exit code 1 if any rule fails — fails the build automatically
```

---

## Programmatic use

```python
from tmf_lint.runner import run

report = run(base_url="http://localhost:8000", apis=[638, 639, 641])
print(f"Passed: {report.n_passed}  Failed: {report.n_failed}  Skipped: {report.n_skipped}")

for result in report.results:
    if not result.passed and not result.skipped:
        print(f"  FAIL [{result.rule_id}] {result.description}")
        print(f"       {result.message}")
```

---

## Adding a new rule

The rule engine auto-discovers subclasses — no registration call is needed.

1. Create `tmf_lint/rules/tmf{N}/r_mycheck.py`
2. Subclass `BaseRule` and set four class attributes
3. Implement `async def check(self, client, ctx) -> RuleResult`

```python
from tmf_lint.rules.base import BaseRule, CATEGORY_HTTP
from tmf_lint.client import LintClient
from tmf_lint.context import LintContext
from tmf_lint.result import RuleResult

class TMF639MyNewRule(BaseRule):
    rule_id    = "TMF639-HTTP-005"
    api        = 639
    category   = CATEGORY_HTTP
    description = "GET /resource supports ?fields= projection"

    async def check(self, client: LintClient, ctx: LintContext) -> RuleResult:
        try:
            resp = await client.get("/tmf-api/resourceInventoryManagement/v4/resource",
                                    params={"fields": "id,name"})
        except Exception as exc:
            return self.fail(str(exc))

        if resp.status_code != 200:
            return self.fail(f"Expected 200, got {resp.status_code}")
        return self.ok()
```

See `tmf_lint/rules/tmf639/r_http.py` for a complete worked example.

---

## Development

```bash
git clone https://github.com/tmf-devkit/tmf-lint
cd tmf-lint

# Windows
python -m venv .venv && .venv\Scripts\activate
# macOS / Linux
python -m venv .venv && source .venv/bin/activate

pip install -e ".[dev]"
pytest                  # all tests, no live server needed
ruff check tmf_lint     # lint
```

---

## Related projects

| Project | Purpose |
|---|---|
| [tmf-mock](https://github.com/tmf-devkit/tmf-mock) | Smart TMF mock server — the recommended test target for tmf-lint |
| [TMFValidator](https://github.com/tmforum-rand/TMFValidator) | OAS/Swagger schema linter — validates the API definition, not runtime behaviour |

---

## Roadmap

| Version | Planned additions |
|---|---|
| v0.2 | `--fixtures` for custom POST payloads per implementation, TMF633 Service Catalog, TMF634 Resource Catalog |
| v0.3 | TMF688 event notification validation (requires separate listener architecture) |

---

## License

Apache 2.0 © Manoj Chavan
