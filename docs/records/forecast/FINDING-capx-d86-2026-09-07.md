# FINDING — capx D86: the D79 solve-surface guards, repaired and demonstrated non-vacuous

**Lane:** capx D86 · **Date:** 2026-09-07 · **HEAD:** `ad78cc3e` · **ZERO LP.**
**Scope:** `tests/unit/results/test_cache_solve_surface.py` only. No `src/` change, no
`solve_surface_declared.py` change, no conftest change, no registration, no marker, no arm.

## Step 3 — the non-vacuity table (the deliverable)

Each test's SUBJECT was broken in a real source file, the single test run, and the exact
pre-mutation bytes written back. Harness: `scratchpad/mutate.py` + `mutate2.py` (restore verified
byte-for-byte, `git status` clean-except-the-test-file at start and end).

| Test | What I broke | Result |
|---|---|---|
| `test_sidecar_is_written_beside_the_config` | `surface_stamp` hardcodes `"moved": {}` — the stamp lies about the moved rows (M5) | **RED** |
| `test_sidecar_and_config_agree` | the sidecar is stamped for a fixed ISO, not the config's (M3) | **RED** |
| `test_sidecar_is_rewritten_when_the_surface_moves` | the stamp's `fingerprint` frozen to a constant (M4′) | **RED** |
| `test_sidecar_is_rewritten_when_the_surface_moves` | the stamp's `moved` list emptied (M4″) | **RED** |
| `test_a_bundle_solved_on_S1_is_not_addressed_on_S2` | moved rows never enter `cache_key()` — `if moved_surface:` → `if False:` in `scenarios.py` (M1) | **RED** |
| `test_another_isos_key_is_untouched_by_a_MISO_row` | the ISO projection ignored: every ISO reads MISO's rows (M2′) | **RED** |
| `test_the_surface_actually_reaches_the_key_in_this_file` | the `solve_surface_live` opt-out dropped (M6) | **RED** |

Two first-attempt mutations stayed green and were **my mutation's fault, not the test's** — both
re-run and RED above. They are recorded because one of them exposed a real coverage gap (§4):

| First attempt | Why it was a no-op |
|---|---|
| M2: `moved_rows` reads `surface_rows(None)` | `surface_rows(None)` does not contain the by-ISO table at all (`DEMAND_GROWTH_RATES in surface_rows(None)` is `False`), so the mutant *removed* rows instead of leaking them across ISOs. Replaced by M2′. |
| M4: sidecar written only `if not exists` | the two saves land in **different bundle directories** (`bcaf6043b8bfea74` vs `13afdf6f728e5336` — the key moved, which is the point), so no pre-existing sidecar is ever encountered. See §4. |

### The decisive measurement for defect B

With the ISO projection genuinely broken (M2′), the same test, same mutation:

| Test file state | Result |
|---|---|
| **WITH** the opt-out (this PR) | **RED** — the assertion is load-bearing |
| **WITHOUT** the opt-out (as on `main`) | **GREEN** — vacuous; it cannot detect the break |

That is defect B stated as a measurement rather than an inference: on `main` the rule 25
`[R-ISO-SCOPE]` per-ISO isolation assertion was satisfied trivially, because a stubbed
`moved_rows` cannot move *any* ISO's key.

## 1. Step 0 — the stop gate, reproduced at my HEAD

Outside pytest, at `ad78cc3e`, mutating `constants.DEMAND_GROWTH_RATES["MISO"]` then
`solve_surface.reset_caches()`:

| Quantity | Value |
|---|---|
| `ScenarioConfig(iso="MISO").cache_key()` on S1 | `bcaf6043b8bfea74` |
| the same key on S2 | `13afdf6f728e5336` |
| `moved_rows("MISO")` on S2 | `{'DEMAND_GROWTH_RATES': '6744aaed2256cf46'}` |
| key after the `finally` revert | `bcaf6043b8bfea74` (restored) |

Identical to the capx director's measurement at `60f244e3`. **The mechanism works; the object of
repair is its guards.** The two live moves are as the charter states and were not touched:
`moved_rows("ERCOT") = {'NUCLEAR_MONTHLY_CF_BY_YEAR': '00a8e8726fd0edd6'}` (ercot-253) and
`moved_rows("CAISO") = {'NUCLEAR_MONTHLY_CF_BY_YEAR': ..., 'STATE_CARBON_PRICE_BY_ISO': ...}`
(caiso-262).

Baseline inside pytest, before any edit: **2 failed, 3 passed** — exactly the charter's grading
(A red, C red, B green-and-vacuous).

## 2. The repair

**Step 1 — arm the file.** Module-level `pytestmark = pytest.mark.solve_surface_live`, in the same
form as the precedent (`tests/unit/config/test_solve_surface.py:47-49`): the two-line comment, then
the assignment. The marker was already registered at `pyproject.toml:44`; it was not re-registered.

**Step 2 — defect C repaired FORWARD.** `assertEqual(stamp["moved"], {})` was a *stale scope label*,
true when D79 landed at zero moves and false since ercot-253 added the 2021 row. It is **not**
replaced by today's ERCOT dict literal, which would go stale identically at the next ledgered move.
The stamp is now asserted against the **live** surface and the **live** ledger:

- `stamp["moved"] == S.moved_rows("ERCOT")` — the stamp is truthful;
- `stamp["epochs"] == S.applicable_epochs(config_from_disk)`;
- `stamp["rows"] == len(S.surface_rows("ERCOT"))`;
- every name in `stamp["moved"]` is a key of `LEDGERED_SURFACE_MOVES_BY_ISO["ERCOT"]` — **an
  unledgered move still fails here**, so this is not a weakening.

The ledger is **imported, never copied**, from `tests/regression/test_persisted_identity.py`, which
owns it (lazy import inside the test; ~0.7 s, and it names the owning module in a comment).

**Step 4 — the marker's removal is now loud.** `test_the_surface_actually_reaches_the_key_in_this_file`
asserts `scenarios.moved_rows is S.moved_rows` and the same for `applicable_epochs`. `scenarios`
binds both names at import (`from ... import`, `scenarios.py:41`), so those module attributes are
exactly what `cache_key()` calls at `scenarios.py:18545-18548` and exactly what the fixture patches.
Step 1 alone does not prevent the recurrence — a marker can vanish with no red. This fails for the
whole file at once instead of one silent vacuity at a time.

## 3. What was NOT touched

- `src/market_sim/config/solve_surface_declared.py` — untouched. Re-declaring a moved row would
  restore the pre-change key and re-serve the pre-change bundle (rule 26 `[R-DELETE]`).
- Anything under `src/market_sim/` — untouched. Mutations were applied and reverted byte-for-byte;
  `git status` shows only the one test file.
- `tests/conftest.py::_solve_surface_neutralized` — untouched. It is correct and it exists for a
  good reason (ercot-253's real move failed 12 field-arming pins across nine unrelated lanes). The
  repair is the **opt-out**, not the fixture.

## 4. Second finding — `test_sidecar_is_rewritten_when_the_surface_moves` does not test its docstring

Its docstring says *"Never `if not exists`: the stamp must date the bytes on disk."* It cannot
measure that. The two `_save` calls straddle a surface move, so their cache keys differ
(`bcaf6043b8bfea74` → `13afdf6f728e5336`) and they write into **different bundle directories** — no
pre-existing sidecar is ever encountered, so an `if not exists` writer passes this test unchanged
(measured: M4 green). Verified directly: `p1 == p2` is `False`.

The test is **not vacuous** — it genuinely pins that the stamp tracks the moved surface (M4′ and M4″
both RED) — but the `if not exists` regression its docstring claims to guard is **unguarded**. The
real hazard the D79 comment at `cache.py:1454-1455` names is a surface that moves *between two years
of one run*, where the key is the same and the bundle dir **is** the same; that is a different
scenario from the one this test builds.

**Not repaired here** — out of this charter's scope (it needs a new same-key test, not a repair of an
existing one), and reported rather than papered over. Suggested successor: save twice at the same key
with a mutated `git_sha`/epoch, or assert the sidecar's mtime/bytes change on a second same-key save.

## 5. Exit state

| Gate | Result |
|---|---|
| `tests/unit/results/test_cache_solve_surface.py` | **6 passed** |
| `scripts/check_key_provenance.py` | ok — unchanged |
| `scripts/audit_keepers.py --check` | PASS: 0 failures, 0 warnings — unchanged |
| `tests/regression/test_persisted_identity.py` | 24 passed — unchanged |
| `ruff check` / `ruff format --check` | clean / already formatted |
| diff | 1 file, +47 −2 |

### The A/B that proves the change is strictly additive

`tests/unit tests/scoring tests/regression`, identical command, run twice — once with this file at
`origin/main`, once with the repair. Nothing else differed.

| Run | Result |
|---|---|
| baseline (`origin/main`'s copy of the file) | **57 failed**, 7002 passed, 51 skipped, 1 xfailed |
| repaired (this branch) | **55 failed**, 7005 passed, 51 skipped, 1 xfailed |

Set difference on the FAILED ids:

- **Fixed (2):** `test_a_bundle_solved_on_S1_is_not_addressed_on_S2`,
  `test_sidecar_is_written_beside_the_config` — exactly defects A and C.
- **Newly broken: 0.**
- **Unchanged: 55.**

The +3 passes are the 2 repaired tests plus the step-4 marker guard.

### Still red, and NOT mine (fixed none)

**55 tests are red on `main` and stay red — none is D86's**, and none is in this file. The charter
named four of them; the full set is larger, so it is inventoried here rather than left implied. Data
is fully hydrated (6.1 G under `data/raw`), so these are not hydration artifacts.

| File | Count | Note |
|---|---|---|
| `tests/unit/model/test_d62_published_going_forward_bar.py` | 15 | capx D62's lane |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | 12 | capx D74's lane |
| `tests/scoring/test_golden_manifest_provenance.py` | 7 | |
| `tests/regression/test_soundness.py` | 6 | `TestEndToEnd` |
| `tests/unit/results/test_export.py` | 4 | |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | |
| `tests/scoring/test_forecast_parity.py` | 2 | charter-named: miso-233 arms three `miso_seam_neighbour_*` fields with no `forecast_parity_registry` declaration — MISO's lane |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | charter-named: registry 1.166 vs artifact 1.154 — CAISO's lane |
| `tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none` | 1 | charter-named: SPP now has an RPS floor, so `get_rps_target("SPP", 2030)` is `0.0`, not `None` |
| `tests/scoring/test_registration_marker_gate.py` | 1 | |
| `tests/scoring/test_gate_a_provenance.py` | 1 | |
| `tests/scoring/test_backcast_artifacts.py` | 1 | |
