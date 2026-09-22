# Testing

## Test groups

### Unit tests

Located in `tests/unit/`:

- `test_brand_rule_scoping.py`: global and brand-specific rule isolation.
- `test_demo_guards.py`: demo rate and daily budget behavior.
- `test_lead_scoring.py`: deterministic lead scoring.
- `test_lessons_aggregation.py`: feedback-to-lessons aggregation.
- `test_optimization_aggregation.py`: deterministic analytics aggregation.
- `test_publishing_worker.py`: publisher and worker behavior, including success and failure paths.

### Compliance regression checks

Located in `tests/compliance_regression/`:

- multilingual blocklist behavior,
- lead outreach compliance,
- brand rule behavior,
- phase 2 and phase 3 pipeline checks.

## Running tests in Compose

```bash
docker compose exec api python -m tests.unit.test_brand_rule_scoping
docker compose exec api python -m tests.unit.test_demo_guards
docker compose exec api python -m tests.unit.test_lead_scoring
docker compose exec api python -m tests.unit.test_lessons_aggregation
docker compose exec api python -m tests.unit.test_optimization_aggregation
docker compose exec api python -m tests.compliance_regression.verify_multilingual_blocklist
docker compose exec api python -m tests.compliance_regression.verify_lead_outreach
docker compose run --rm --no-deps -v "$PWD/tests:/app/tests" worker python -m tests.unit.test_publishing_worker
```

Some compliance regression tests intentionally call Gemini and consume quota. Run deterministic tests first when validating local changes.

## Validation priorities

For API or agent changes:

1. Run the nearest unit or regression test.
2. Exercise the affected route through `/docs` or `curl`.
3. Inspect `ai_runs` for model-backed changes.
4. Confirm generated records retain expected brand, language, provenance, and status fields.

For worker changes:

1. Run the publishing worker unit test.
2. Run `--health` in the intended provider mode.
3. Seed a job in simulation mode and run `--once`.
4. Verify job status and analytics rows.
