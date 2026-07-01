# PP-07 — Tests

**Upstream:** all. **Targets:** `tests/`.
**Status:** minimal done (`test_intake`, `test_resources`, `test_lp_trivial`,
`test_sweep`).

## Principle

Trivial cases first (1 gen, 1 zone, 24 hours), then scale — the market-sim testing
rule. Keep CI **data-free**: default to synthetic profiles; gate any real-data
test behind `@pytest.mark.integration` with a skip when files are absent.

## Coverage to build out

- **config** — validation, `with_overrides`, config-file load (PP-00).
- **intake** — multi-facility/multi-ISO aggregation, growth models, calendar
  validation, missing-hour policy (PP-01).
- **resources** — cost conversion (both representations), sensitivity, caps/floors,
  per-ISO caps, eligibility (PP-02).
- **profiles** — CF bounds, storage-zero rows, synthetic annual means; vendored
  real profiles behind an integration marker (PP-03).
- **lp** — trivial hand-computed optimum; energy-balance feasibility; SOC
  cyclicity; cap binding; premium/matching constraint correctness; hydro budget
  (PP-04).
- **sweep** — monotonic frontier (matching ↑ with premium cap); Mode B duality;
  infeasible-setpoint handling (PP-05).
- **outputs** — Parquet round-trip, schema, new metric columns, summary (PP-06).

## Acceptance

`pytest tests/ -q` green without external data; integration tests skip cleanly
when raw data is absent. Add a `pytest -m "not integration"` CI target.
