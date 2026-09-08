# FINDING — capx D89: the 27 D62/D74 reds are ONE fixture defect, not a behaviour change

**Lane:** capx D89 · **Date:** 2026-09-08 · **HEAD:** `4e4ad90d` · **ZERO LP** (none spent, none needed).
**Authority:** owner ruling Q61 (2026-09-08, capx ledger §0be.3(b)) — "Charter D89 for capx's own 27; fix none of the other 28."
**Scope:** `tests/unit/model/test_d62_published_going_forward_bar.py`, `tests/unit/model/test_d74_no_default_cap_convention.py`, `tests/conftest.py`. No `src/` change, no default moved, no arm, no registration, no mechanism-matrix cell.

## §0 — the 27-row classification table (the deliverable)

**All 27 are (A) FIXTURE ROT. Zero (B). Zero unclassified.** Cause and action codes are defined under the table; every row carries both.

| # | Test | Failing assertion | A/B | Cause | Action |
|---|---|---|---|---|---|
| 1 | `D62::TestVintageRuleFromTheData::test_delivery_years_through_2025_26_read_the_first_column[2021]` | `published_bar_per_kw_yr("PJM", fuel, 2021)` raises before `assert got is not None` | **A** | C1 | R1 |
| 2 | `…_read_the_first_column[2022]` | same, year 2022 | **A** | C1 | R1 |
| 3 | `…_read_the_first_column[2023]` | same, year 2023 | **A** | C1 | R1 |
| 4 | `…_read_the_first_column[2024]` | same, year 2024 | **A** | C1 | R1 |
| 5 | `…_read_the_first_column[2025]` | same, year 2025 | **A** | C1 | R1 |
| 6 | `D62::TestVintageRuleFromTheData::test_delivery_years_from_2026_27_read_the_second_column[2026]` | `published_bar_per_kw_yr("PJM", fuel, 2026)` raises before `assert got is not None` | **A** | C1 | R1 |
| 7 | `…_read_the_second_column[2027]` | same, year 2027 | **A** | C1 | R1 |
| 8 | `…_read_the_second_column[2035]` | same, year 2035 | **A** | C1 | R1 |
| 9 | `…_read_the_second_column[2050]` | same, year 2050 | **A** | C1 | R1 |
| 10 | `D62::TestVintageRuleFromTheData::test_the_na_limb_is_named_not_silent` | `published_bar_per_kw_yr("PJM", "gas_st", 2023)[1] == "first_published"` — raises on the call | **A** | C1 | R1 |
| 11 | `D62::TestVintageRuleFromTheData::test_the_published_bars_are_the_d61_operand` | `resolve_going_forward_bar_per_kw_yr(cfg_armed, fuel, 2022)` raises through the armed gate | **A** | C1 | R1 |
| 12 | `D62::TestVintageRuleFromTheData::test_the_multiplier_does_not_apply_to_the_published_bar` | same resolver, armed gate, `coal`/2022 | **A** | C1 | R1 |
| 13 | `D62::TestReactiveLeg::test_reactive_is_the_published_row` | `assert None == 2199.0 ± 0.002199` (file line 236) | **A** | **C2** | R1 |
| 14 | `D62::TestReactiveLeg::test_offer_equals_exit_identity_on_a_toy_stack` | `resolve_going_forward_bar_per_kw_yr(cfg, fuel, 2022)` raises on the armed leg of the `(None, {"PJM": True})` loop | **A** | C1 | R1 |
| 15 | `D62::TestReactiveLeg::test_reactive_credit_is_once_and_only_when_armed` | `TypeError: unsupported operand type(s) for *: 'float' and 'NoneType'` at `pmax * rate` (file line 270) | **A** | **C2** | R1 |
| 16 | `D74::TestThePredicateIsTheData::test_steam_oil_and_gas_has_no_default_through_2025_26[2022]` | `no_default_cap_class("PJM", "gas_st", 2022)` raises before `is True` | **A** | C1 | R1 |
| 17 | `…_has_no_default_through_2025_26[2023]` | same, year 2023 | **A** | C1 | R1 |
| 18 | `…_has_no_default_through_2025_26[2024]` | same, year 2024 | **A** | C1 | R1 |
| 19 | `…_has_no_default_through_2025_26[2025]` | same, year 2025 | **A** | C1 | R1 |
| 20 | `D74::TestThePredicateIsTheData::test_the_class_reenters_the_screen_when_the_table_publishes[2026]` | `no_default_cap_class("PJM", "gas_st", 2026)` raises before `is False` | **A** | C1 | R1 |
| 21 | `…_reenters_the_screen…[2027]` | same, year 2027 | **A** | C1 | R1 |
| 22 | `…_reenters_the_screen…[2030]` | same, year 2030 | **A** | C1 | R1 |
| 23 | `…_reenters_the_screen…[2040]` | same, year 2040 | **A** | C1 | R1 |
| 24 | `D74::TestThePredicateIsTheData::test_every_class_with_a_published_value_is_screened[2022]` | `no_default_cap_class("PJM", "coal", 2022)` raises before `is False` | **A** | C1 | R1 |
| 25 | `…_every_class_with_a_published_value_is_screened[2025]` | same, year 2025 | **A** | C1 | R1 |
| 26 | `…_every_class_with_a_published_value_is_screened[2026]` | same, year 2026 | **A** | C1 | R1 |
| 27 | `…_every_class_with_a_published_value_is_screened[2030]` | same, year 2030 | **A** | C1 | R1 |

**Cause C1 (25 rows).** `PublishedBarUnavailable: no published avoidable-cost-rate partition for PJM` raised at `src/market_sim/data/avoidable_cost_rate.py:193`. The seam's `_read` returns `None` because `data/clean/capacity-market-avoidable-cost-rate/` — a **DERIVED, gitignored** partition — does not exist in a fresh checkout, and nothing in the test tier builds it.

**Cause C2 (2 rows).** The *same* missing partition, reached through `reactive_offset_per_mw_yr`, which **degrades to `None`** rather than raising (documented: "``None`` when the ISO has no such row"). So row 13 compares against `None` and row 15 multiplies by it. Identical root cause, different surface — recorded separately because the failing text differs and a reader diffing tracebacks would otherwise see two unexplained rows.

**Action R1 (all 27).** The class is now guarded by the two halves the dependency actually has:
`@requires_raw(PUBLISHED_ACR_RAW_CSV)` (the repo's standing idiom, `tests/helpers/base.py` — it carries the `fulldata` marker **and** skips honestly when the tracked CSV is absent) plus `@pytest.mark.usefixtures("published_acr_clean_dir")`, a new fixture in `tests/conftest.py` that **curates the tracked raw CSV through the real intake pipeline into a scratch `CLEAN_DIR`**. **Not one assertion was changed.**

### What live source each repaired assertion now reads

`data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` (tracked, 2.5 KB, PJM Manual 18 Rev 62 §5.4.8.4(B)), resolved through `scripts.lib.capacity_market_avoidable_cost_rate.raw_dir_for("PJM", paths.RAW_DIR)` — the intake's own path function, imported rather than copied — and curated by `scripts/data/curate_capacity_market_avoidable_cost_rate.py`, the production script. The literals the tests assert (coal 80/94, CC 56/113, CT 50/52, Steam Oil & Gas 64 late-only, Nuclear-Multi 445/537 $/MW-day; reactive 2199 $/MW-yr) are **PJM's published numbers**, which is what rule 21 `[R-DOF]` requires them to be — they are the guard, not a frozen build artifact, and each reconciles byte-for-byte against the CSV above. Nothing was re-frozen to today's value.

## §1 — why it is (A), stated as measurement rather than inference

Three independent checks, any one of which would have caught a (B):

1. **The mechanism path has not moved one byte since it landed.** `git diff 9d9ffacd HEAD` is **empty** for `src/market_sim/data/avoidable_cost_rate.py`, `scripts/lib/capacity_market_avoidable_cost_rate/pjm.py`, `data/raw/.../pjm.csv` and both test files. `9d9ffacd` (2026-09-06) is the commit that ADDED all five. `src/market_sim/config/capacity_market.py` did move once (capx D84, `dc96602e`) but the diff is a **pure addition** of `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO`; neither `resolve_capacity_going_forward_bar_published` nor `resolve_capacity_no_default_cap_convention` is touched.
2. **Build the missing partition, and all 27 pass unchanged.** `python scripts/data/curate_capacity_market_avoidable_cost_rate.py` (0.03 s, 16 rows) then the same pytest invocation: **53 passed, 0 failed** — every value the tests encode is produced exactly. Nothing D62 or D74 measures has changed.
3. **The repaired files pass with `data/clean` ABSENT** (moved aside; `ls -d data/clean` → no such file): **53 passed in 1.66 s**. The fixture builds what it needs, so the result no longer depends on whether some earlier session happened to run the curation script on this host.

**Consequence for D74's self-executing DO-NOT-ARM: it stands, on unmoved evidence.** The measurements the refusal rests on are exactly the assertions in `TestThePredicateIsTheData`, and every one of them reproduces to the value it was written against. No owner card is owed, because there is no (B) row to serve one for.

**Consequence for D62's landed state:** unchanged and still default-off. `capacity_going_forward_bar_published_by_iso` and `capacity_no_default_cap_convention_by_iso` remain `None` for every ISO; the four cache-neutrality tests that assert that were **green throughout** and were never part of the 27.

### The correction to D86's reading

D86's inventory recorded, of the whole 55, "Data is fully hydrated (6.1 G under `data/raw`), so these are not hydration artifacts." For these 27 that inference is **wrong, and it is why the rot survived**: `data/raw` being complete says nothing about `data/clean`, which is derived and gitignored. The `fulldata` marker means "needs the real `data/raw` tree present" — it was **necessary but not sufficient**, so on a fully-hydrated host with an unbuilt clean tree the tests failed while every guard in place said they should have been runnable. The repair makes the marker's promise true rather than merely louder.

### The pre-existing comment in `test_d74…` that pointed at this

The file already carried a block explaining that a module-level `pytestmark` skipif on `published_bar_per_kw_yr(...) is None` had been replaced by a `fulldata` marker, because the predicate "can never be None on an unbuilt checkout: every value-returning entry point in the seam raises `PublishedBarUnavailable` instead". That diagnosis was **correct and half-applied**: it freed the file's four data-free classes to run in the fast tier (a real gain, kept), but it left the data-tier class *red* rather than *deselected* outside the fast lane. The block has been updated in place to say so — it is history, not a re-litigation.

## §2 — the repair, in full

| File | Change |
|---|---|
| `tests/conftest.py` | **+46 lines**: new function-scoped `published_acr_clean_dir` fixture beside the existing `tmp_clean_dir`. Redirects `paths.CLEAN_DIR` to `tmp_path`, clears the seam's `lru_cache` on the way in **and** out, curates PJM from the real `RAW_DIR`, and fails loudly (naming the expected CSV path) if the intake produces nothing. |
| `tests/unit/model/test_d62_published_going_forward_bar.py` | `@pytest.mark.fulldata` → `@requires_raw(PUBLISHED_ACR_RAW_CSV)` + `@pytest.mark.usefixtures("published_acr_clean_dir")` on `TestVintageRuleFromTheData` and `TestReactiveLeg`. Module-level `PUBLISHED_ACR_RAW_CSV` derived from the intake's own `raw_dir_for`. **No assertion changed.** |
| `tests/unit/model/test_d74_no_default_cap_convention.py` | Same two decorators on `TestThePredicateIsTheData`; same constant; the pre-existing tier-history comment extended. **No assertion changed.** |

Nothing was skipped, xfailed, weakened or deleted. The only skip introduced is `requires_raw`'s, which fires **solely when the tracked raw CSV is genuinely absent** — verified by moving it aside: `23 passed, 30 skipped` instead of 27 hard errors, and the file restored byte-identically (`git status` clean).

### Behaviour in each lane

| Lane | Before | After |
|---|---|---|
| fast tier, `-m "not slow and not integration and not fulldata"` | 23 passed, 30 deselected | 23 passed, 30 deselected — **identical**, `requires_raw` still carries `fulldata` |
| wide command, `data/raw` hydrated, `data/clean` unbuilt | **27 failed**, 26 passed | **53 passed** |
| wide command, `data/clean` already built | 53 passed | 53 passed (now hermetic — reads a scratch tree, not the host's) |
| `data/raw` absent (a `code`-profile checkout) | 27 failed | 23 passed, **30 skipped** with a named reason |

## §3 — the wide-command counts

Command, stated per §0be doctrine — **a red inventory is only as wide as the command that produced it**:

```
uv run python -m pytest tests/unit tests/scoring tests/regression -q -rf
```

(`-rf` only adds the failed-id summary; it changes no result. Python 3.11, `uv sync` at
`uv.lock`, no `-m` marker filter and no `-n` xdist — this is the wide, unfiltered command D86
used, which is why it runs the `fulldata` tier that CI's fast lane deselects.)

run at HEAD `4e4ad90d`, `data/raw` hydrated (6.3 G), `data/clean` **absent** (the as-cloned state) in both arms.

**Both arms are measured at the SAME base.** `origin/main` advanced to `1cb976f4` during this session (25 files: docs, probes, plus miso-245's `MISO_SEAM_LADDER_BY_YEAR` reconciliation in `src/market_sim/model/interchange/spec.py`, which can plausibly move the two `test_forecast_parity` reds). The branch was deliberately **not** rebased mid-measurement — an A/B whose arms sit on different bases measures the base, not the change. The pack is two small text-only commits, so the rebase-for-pack-size reason in CLAUDE.md's Git & Pushing does not apply. A re-measurement on `1cb976f4` is the next lane's to make if it wants one; nothing here depends on it.

| Run | Result |
|---|---|
| baseline (`origin/main`'s copy of the three files) | **57 failed**, 7097 passed, 56 skipped, 1 xfailed, 539 subtests passed — 943.72 s |
| repaired (this branch) | **30 failed**, 7124 passed, 56 skipped, 1 xfailed, 539 subtests passed — 914.49 s |

Set difference on the FAILED ids:

- **Fixed: 27** — exactly the 27 rows of §0, no more and no fewer.
- **Newly broken: 0.**
- **Unchanged: 30.**

**Fixed 27, newly broken 0.** The +27 passes (7097 → 7124) are precisely the repaired tests; skipped, xfailed and subtest counts are identical across the two arms, so nothing was converted into a skip.

D86 measured **55** at `ad78cc3e`; **I measure 57 at `4e4ad90d`, and 57 is the number this lane works from.** The +2 is not a change in D86's arithmetic — its 55 were all still red and are all still in my baseline. Two NEW reds landed in between, both from capx D84 (`dc96602e`); they are §4's last two rows. The 27 D62/D74 reds are identical in both measurements, so the charter's denominator for THIS lane was exact.

## §4 — the other reds: THIRTY at my HEAD, not 28 — inventoried, not touched

Fixed none of these. **My baseline finds 30 non-D89 failures, two more than the charter's 28**, because the charter's list was copied from D86's measurement at `ad78cc3e` and two new reds have landed since. Both new ones trace to the same commit; see the sub-finding below the table.

| File / test | Count | Owning desk |
|---|---|---|
| `tests/scoring/test_golden_manifest_provenance.py` | 7 | golden-manifest provenance |
| `tests/regression/test_soundness.py` (`TestEndToEnd`) | 6 | test_soundness end-to-end |
| `tests/unit/results/test_export.py` (`TestExportScenarioJson`) | 4 | results/export |
| `tests/scoring/test_ff_readiness_battery.py` | 4 | FF readiness battery |
| `tests/scoring/test_forecast_parity.py` | 2 | **MISO** — miso-233 arms three `miso_seam_neighbour_*` fields with no `forecast_parity_registry` declaration |
| `tests/unit/data/test_caiso_st_gas_peak_measured.py` | 1 | **CAISO** — registry 1.166 vs artifact 1.154 |
| `tests/unit/model/test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none` | 1 | **SPP** — SPP now has an RPS floor, so `get_rps_target("SPP", 2030)` is `0.0`, not `None` |
| `tests/scoring/test_registration_marker_gate.py` | 1 | registration-marker gate |
| `tests/scoring/test_gate_a_provenance.py` | 1 | gate-(a) |
| `tests/scoring/test_backcast_artifacts.py` | 1 | backcast artifacts |
| **— the charter's 28 —** | **28** | |
| `tests/regression/test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned[PJM]` | 1 | **capx D84** — NEW since D86 |
| `tests/regression/test_constants_facade.py::test_moved_surface_is_complete` | 1 | **capx D84** — NEW since D86 |
| **Total at my HEAD** | **30** | |

### Sub-finding: capx D84 landed owing two guard obligations

Both new reds are caused by `dc96602e` (capx D84), which added `THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO` to `src/market_sim/config/capacity_market.py` — the one later commit on any file this lane audited, and it is a **pure addition** that touches neither D62 resolver, so D89's own classification is unaffected. What it did not do:

1. **`test_solve_surface_fingerprint_is_pinned[PJM]`** — the new table joined the D79 solve surface, so PJM's fingerprint moved `0f749d17202c32d9` (211 rows) → `f5eeaed979e6ce82` (212 rows) and the pin was not advanced. The guard's own failure text states exactly what is owed and warns against the wrong repair: *"Do NOT re-declare the row in `config/solve_surface_declared.py` — that restores the pre-change key and re-serves the pre-change bundle… advance the pin here with a dated cause block: which rows, which ISOs, what it costs."*
2. **`test_moved_surface_is_complete`** — *"`market_sim.config.capacity_market` grew names the facade does not re-export: `['THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO']`"*.

Neither is D89's to fix (charter: capx's own 27, and these are a different capx card's), and the first is a **ledger entry**, not a test edit — writing it is the D84 lane's judgement about what the move costs, which this lane has no standing to make. **Routed to capx D84.** Flagged rather than filed quietly because a moved solve-surface fingerprint means every future PJM solve keys differently from the PJM bundles already on disk — that is the D79 guard doing precisely its job, and it should not sit red unread.

An all-55 sweep was offered to the owner and marked NOT RECOMMENDED — rule 25 `[R-ISO-SCOPE]` and the §0bd cross-desk collision. That stands, and the drift from 55 to 57 is a second argument for it: the other-desk set is live, so a sweep would have been chasing a moving target.

**One diagnostic worth passing on, free.** Several of these desks may be looking at the same class of defect this lane found: a test that reads a **derived, gitignored** artifact (`data/clean/**`, a bundle, a generated dashboard part) which no fixture builds, guarded — if at all — by a marker that names a *different* prerequisite. `published_acr_clean_dir` is the pattern for that case and is now available to any test in the tree. It is offered as a pointer only; this lane repaired none of the 30 and claims nothing about them.

## §5 — routed, not acted on

**The reactive leg degrades where its siblings raise.** `reactive_offset_per_mw_yr` returns `None` on an unreadable partition, while every bar-returning entry point in the same module raises `PublishedBarUnavailable` — the module docstring's stated contract is the latter ("a missing partition here would silently restore the ATB proxy under an armed gate, i.e. a wrong answer that looks like an answer. So an ARMED gate with unreadable data raises"). It is **not exploitable today**: under an armed gate `resolve_going_forward_bar_per_kw_yr` raises first, so the screen can never reach a silently-`None` reactive credit. Changing it would change what the mechanism *does*, not what a test reads — out of scope for a zero-LP test-repair lane (rule 28 `[R-MECH-MATRIX]`), so it is **reported to the D62 desk, not changed**.

**Rule 28 disposition:** no mechanism-matrix cell moves. Nothing armed, no default changed, no verdict re-adjudicated — the repair is entirely in the test tier.

**Rule 27 `[R-PUSH]` note.** The charter stated both test files are "well over 300 lines". Measured: `test_d62…` was **276** and `test_d74…` **221** before the repair (295 and 234 after), and `tests/conftest.py` 149 → 194 — all three under the 300-line threshold, so the push-integrity protocol does not strictly bind. It was followed anyway: every edit was made locally with an anchored in-place patch, the exact on-disk bytes were pushed, and each blob was fetched back and compared on line count and SHA-256 after the push.

**Branch note.** The charter names `claude/capx-d89-d62-d74-reds`; the harness designated `claude/d89-test-failures-diagnosis-ttunic`, which is where this work landed. Same content, different branch name — flagged so the ledger can point at the right ref.
