# Weekly forecast-invariant findings (append-only archive)

Persisted output of the weekly `forecast-invariants.yml` heavy tier — the paired
directional invariants P1–P3 (and an e2e presence marker). Before this archive
existed the weekly results were **ephemeral**: they lived only as 14-day GitHub
Actions artifacts, so a directional regression that appeared and was fixed
between two people looking left no trace (testing-audit **G9**). Now every weekly
run commits a date-stamped findings file here.

## Contract

- **Append-only.** Each run writes a NEW file `weekly-<YYYY-MM-DD>-run<N>.json`;
  no run ever overwrites or deletes an existing one. The filename is unique per
  run (date + Actions run number), so a same-day re-dispatch does not collide.
- **Machine-readable.** Each file is the JSON the paired-invariant step already
  produced (`{carbon: [...], gas_up: [...], gas_pm5: [...]}` — one row per
  invariant with `status`/`ident`/`name`/`detail`), wrapped with the run's
  `date`, `run_id`, `commit`, and an `e2e_slow_passed` marker.
- **Not a tuning channel.** These are forecast probes (rule 1): a FAIL here is a
  root-cause issue to open, never a threshold to widen. Nothing in this
  directory is read back by a solve.

## Related

- `scripts/check_forecast_invariants.py` — the P1–P3 checker these come from.
- `scripts/run_driver_battery.py` — the Tier-1 ladders that generalize P1–P3
  (their reports land in `docs/handoffs/driver-battery-<date>.{md,json}`).
- `docs/handoffs/forecast-validation-program-2026-07.md` §2 — the invariant suite.
