# FINDING — capx D100: `__solve_epochs__` modelled in the key-provenance census — `check_key_provenance` EXIT 1 → 0

Lane capx D100 · Fable · ZERO LP · DATA PROFILE code · branch `claude/capx-d100-solve-epochs`
off `origin/main` `792e55adc69ceba868317577c635eb6c1f6f470a` (the charter pinned `d7ff7c20`, which this
clone does not hold; `792e55ad` is the `main` tip the container cloned). Charter: capx director ledger
refresh #69.

## 1. The defect

D98 (PR #6722) built the Q71 recorded-surface construction while `solve_surface.SOLVE_EPOCHS` was empty
and asserted on it (`key_provenance.py::census`, `assert not SOLVE_EPOCHS`) and refused any stamp whose
`epochs` field was non-empty. The closeout-W0 lane has since registered three backcast-scoped epochs
(`2026-10-02c` MISO/NEISO/NWPP/PJM/SOCO, `2026-10-02d` MISO/NWPP/PJM/SOCO, `2026-10-02e` SPP), so
`ScenarioConfig.cache_key()` now appends `__solve_epochs__` for every covered config and the census
died before reporting: `uv run python scripts/check_key_provenance.py` → `AssertionError: SOLVE_EPOCHS
is non-empty: model __solve_epochs__ before trusting key_live_surface`, EXIT 1.

## 2. The model adopted

* **Live key.** `head_key(payload, surface=True)` appends the live `__solve_epochs__` list exactly as
  `cache_key` does: `live_epochs(payload)` runs the public `solve_surface.applicable_epochs` (mode +
  ISO + reach-year scope) over the recorded payload's own `mode` / `iso` / `end_year` literals, so an
  old payload is scoped as the config it recorded would be. The assertion is deleted (rule 26).
* **Recorded stamp.** `recorded_surface_stamp` accepts `epochs` as a list of id strings (absent reads
  empty; anything else is a malformed stamp and the construction does not apply). `head_key(...,
  epochs=<recorded list>)` hashes under it; `surface=True` and `epochs` are exclusive.
* **Verdict.** `surface_recorded_verdict` hashes the row under its stamp's `moved` block AND recorded
  `epochs`. Not the recorded literal → `no_reproduce` (a failure, never a pass-through). Reproduces and
  the recorded epochs equal the live covering set → `surface-recorded` (unchanged, Q71). Reproduces but
  the recorded set differs from the covering set → the new class **`solve-epoch-moved`**: a designed
  re-key (the bundle solved before, or outside, an epoch whose scope now covers it), REPORTED on its own
  line, exempt from `G1_UNKNOWN`, `G2_STALE` when listed, never `unclassified`. Every other
  classification path (recipes, Q66 lag, G3–G6) is untouched.
* **Census record.** Each row carries `covering_epochs` and `recorded_epochs`; the summary carries a
  `solve_epochs` block and the script prints an `epochs:` line.

## 3. The census, before and after (`uv run python scripts/check_key_provenance.py`, fetch on)

| state | result | exit |
|---|---|---|
| `792e55ad` | `AssertionError` in `census()`, no census line | 1 |
| this PR | `224 committed run configs: 171 reproduce, 20 have no key, 33 mismatch` — `16 KNOWN, 10 LAG, 7 SURFACE-RECORDED, 0 SOLVE-EPOCH-MOVED, 0 UNKNOWN` | 0 |

Epochs line: `6 record(s) fall in a live SOLVE_EPOCHS scope, 0 carry epochs in their committed stamp; of
the in-scope records 0 reproduce under the live key and 0 under their recorded stamp once epochs are
modelled; 0 solve-epoch-moved`. The six in-scope records (backcast bundles of the W0 ISOs) all predate the
epochs and reproduce AT DECLARATION — D79's designed re-key, now counted in `validated_at_declaration_only`
(171) rather than crashing the census. No committed stamp records a non-empty epoch list yet; the first
post-W0 solve will, and this census reads it. `--no-fetch` also exits 0 (10 `G1_LAG_UNVERIFIED` warnings,
ancestry undecidable in a shallow clone, as before).

## 4. Tests (`tests/regression/test_key_provenance_exceptions.py`, offline, fast tier)

`test_d100_record_in_scope_reproduces_only_with_the_epoch_id` (a) · `test_d100_record_outside_every_scope_reproduces_with_no_epochs` (b) ·
`test_d100_stale_recorded_epoch_set_is_classified_not_unclassified` (c, both drift directions + listed entry is `G2_STALE`) ·
`test_d100_malformed_stamp_epochs_cannot_be_used`. Each pins a synthetic epoch onto `SOLVE_EPOCHS` through
the module attribute the public `applicable_epochs` reads. `pytest -m "not slow and not integration and not
fulldata" tests/regression/test_key_provenance_exceptions.py tests/unit/config/test_solve_surface.py
tests/unit/config/test_f1_backcast_heat_rate_vintage_defaults.py`: 150 passed. `ruff check` / `ruff format
--check` clean on the three touched Python files.
