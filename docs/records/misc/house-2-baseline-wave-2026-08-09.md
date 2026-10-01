# HOUSE-2 — clear the pinned fast-tier baseline + the `assign_zone_by_coords` finding

**Lane:** `claude/house-2-baseline-wave-s6xhd6`, 2026-08-09, Opus (rule 27
`[R-PUSH]` model assignment honored — the lane touches `src/market_sim/`).
**Charter:** manager dispatch AF.7. Authority:
`docs/handoffs/house-1-lint-ci-2026-08-08.md` §4 (THE baseline table) and §3.5
(the branch-protection ladder); sitting record T.2 (the `assign_zone_by_coords`
finding). Base: `origin/main` @ `b5b88de`.

**Purpose:** a GREEN fast tier on main, so the required-status-check ladder can
extend past `cache-key-pin`.

---

## 0 The answer the manager is waiting on

> **YES — the fast tier is GREEN on main modulo the two excluded
> `ercot_thermal_as_endogenous` items.**

Measured at `b5b88de` + this branch, `pytest -n 2 -m "not slow and not
integration and not fulldata"`:

| | failed | passed | skipped | xfail | subtests |
|---|---|---|---|---|---|
| baseline (`b5b88de`, before this branch) | **7** | 6,534 | 20 | 1 | 389 |
| after this branch | **2** | 6,541 | 20 | 2 | 389 |

The +7 passed reconciles exactly: `test_neiso_bins` +1, `test_outages` +2 (the
repaired test plus the new second leg), `test_forecast_parity::…_resolve` +1,
and the 3 new `test_zone_assignment` PJM tests. `test_full_year` left the tier
(now `slow`) and `…exits_zero…` became the second xfail.

The two remaining are #1–#2, the chartered report-only exclusions
(`TestScreenMutualExclusion`) — ercot-181 is live on that exact surface, so
they were not touched. Nothing else in the tier is red.

---

## 1 Per-item disposition

The §4 table was measured at HOUSE-1's head; two rows had already moved by
`b5b88de`. The dispositions below are against **the set actually failing at
this branch's base**, and §3 restates the table in its post-wave state.

| # | item | disposition |
|---|---|---|
| 1 | `test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::test_derived_map_suppresses_exogenous_credit` | **EXCLUDED — untouched, still red.** Chartered report-only. |
| 2 | `…::test_exogenous_credit_keeps_unit_profitable` | **EXCLUDED — untouched, still red.** Chartered report-only. |
| 3 | `test_neiso_bins.py::…::test_committed_artifact_is_deterministic` | **FIXED** — artifact regenerated (§2.1). |
| 4 | `test_forecast_parity.py::test_all_six_keepers_resolve` | **FIXED, guard preserved** — exact-set pin, not a blanket suppression (§2.4). |
| 5 | `test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers` | **XFAIL(strict=True)** with the FR-22 citation (§2.4). |
| 6 | `test_outages.py::…::test_unknown_iso_degrades_to_empty` | **FIXED** — stale ISO choice, re-pinned to the contract (§2.2). |
| 7 | data-dictionary sync — `datatype='capacity-deliverability'` | **ALREADY REPAIRED ON MAIN** between HOUSE-1's head and `b5b88de`. Verified green, nothing done. |
| 8 | — `datatype='som-competitive-conduct'` | **ALREADY REPAIRED ON MAIN.** Verified green. |
| 9 | — `datatype='unit-outage-events'` | **ALREADY REPAIRED ON MAIN.** Verified green. |
| **NEW** | `test_integration.py::TestFullYearPerformance::test_full_year` | **FIXED** — absent from the §4 table; a full-8760 LP wall-clock test that flakes under xdist contention (§2.3). |

`tests/curation/test_data_dictionary_sync.py` at this head: **5 passed, 132
subtests passed**. The three subtests are gone from the failing set on main
itself; this lane claims no credit for them and made no dictionary edit.

### The one addition to the baseline set

`TestFullYearPerformance::test_full_year` is **not** in the §4 table but failed
at this branch's base under `-n 2`. It is pre-existing and environmental, not a
regression introduced by anything recent: it passes standalone (30.4 s) and
fails only under parallel load, because assertions (c) and (d) are wall-clock
budgets (`build_time < 3.0`, `build + solve < 30.0`) on a full-8760 LP. Under
the §4 table's own rule it would have counted as "the PR's own"; recording it
here is what stops the next lane from inheriting that mislabel.

---

## 2 What changed, and why each is model-inert

No `ScenarioConfig` field was added, so no matrix row and no cache-key
registration was required (`scripts/check_mechanism_matrix.py` → exit 0;
`cache-key-pin`'s exact pytest command → 22 passed). No solve was run, no
keeper file touched.

### 2.1 NEISO committed bin-assignment artifact (#3)

`data/raw/_processed-legacy/bin_assignments_NEISO.csv` was **stale relative to
the code**, regenerated with `scripts/export_iso_bin_assignments.py --iso
NEISO`. The whole diff is **2 rows, 1 column**:

| plant | column | committed | regenerated |
|---|---|---|---|
| 10417 Indian Orchard Plant 1 (ST_CHP) | `Plant_Avg_HR_MMBtu_MWh` | 11.5 | 10.3 |
| 68493 Central Heating Plant (ST_CHP) | `Plant_Avg_HR_MMBtu_MWh` | 9.984 | 10.3 |

**Root cause, not just a re-export.** 10.3 is
`constants.HEAT_RATE_BINS["gas_st"]["default"]` (EIA Table 8.2, natural-gas
steam ~10,300 Btu/kWh) — the fallback bin introduced by the **D-25 gas_st
taxonomy fix** (PR #3697, `d334071`, 2026-08-07). That PR is also the last
commit to touch this CSV, so the artifact was committed without a full
re-export and has disagreed with the code ever since. The two rows are the only
NEISO plants whose class-default heat rate the taxonomy change moved.

**Model-inert:** the LP never reads this column. The one solve-path reader of
the file is `data/fleet/campd_bins.py::ct_intermediate_plants`, which reads
`usecols=["Plant_Code", "Plant_Group", "Mixed_Facility"]` — all three
byte-identical across the regeneration (verified column-by-column over all 14
columns × 118 rows: `Plant_Avg_HR_MMBtu_MWh` is the *only* column that
differs). Fleet heat rates come from the code path, which already returns 10.3.
The `backcast_config.py` comments citing cap-weighted class HRs from this file
are frozen constants, unaffected.

### 2.2 Nuclear unknown-ISO degradation (#6)

`nuclear_unit_availability_series("NEISO", 2024)` no longer returns `{}` —
NEISO **has** a derived extract now (`nuclear-availability-NEISO.csv`: Millstone
2 & 3, Seabrook). The test asserted a *coverage accident*, not the contract, so
it broke the moment that intake landed. Repaired by pinning the contract
instead:

- the no-extract leg now uses a synthetic ISO name (`"NO_SUCH_ISO"`) that no
  intake can ever satisfy — the derived-extract set (CAISO, NEISO, NYISO, PJM
  today) only grows;
- a second leg was added for the other empty-dict path the docstring promises
  and nothing covered: extract present, **no rows for the year**
  (`"NEISO", 1990`), asserted alongside a positive `"NEISO", 2024`.

Test-only. `src/market_sim/data/outages.py` untouched.

### 2.3 The full-8760 perf test (NEW)

`tests/conftest.py` already carries a `_SLOW_NODEID_SUBSTRINGS` autotag list for
exactly this case — "Full-8760 LP-solving test classes that are genuinely slow
… but live in a 900+-line module. Marking them here (rather than editing that
large file) … avoids a rule-27 full-file rewrite."
`test_integration.py::TestFullYearPerformance` was simply never added to it.

This is not a suppression, it is the documented lane assignment:
`docs/testing.md` defines `slow` as "runs the model / full-8760 LP" and the
fast lane as "hermetic unit tests only". The timing budget is meaningless under
xdist contention and still runs — and still means something — in the full
(serial) lane, which is where CI's non-fast jobs execute it. Correctness
assertions (energy balance, TTC) move with it; they are duplicated by the
hermetic dispatch unit tests.

### 2.4 The two FR-22-rooted parity failures (#4–#5) — treatments and why

Both trace to the **same two fields**, armed in a keeper with **neither** a
forecast-orchestrator consumer **nor** a registry declaration — status
`UNACCOUNTED`, not `GAP`:

| field | keeper | only call site |
|---|---|---|
| `ercot_storage_as_soc_reserve` | ERCOT (ercot-167 surface) | `scripts/run_calibration.py:4371` — the **backcast** orchestrator |
| `nyiso_seam_deliverability_envelope` | NYISO (nyiso-132 posture) | `src/market_sim/data/nyiso_seam_envelope.py` |

**Neither was fixed mechanically, and neither was made to disappear.** The
charter forbids building the missing forecast mechanisms, and the obvious
"mechanical" move — filing them as `GAP` in
`scripts/lib/forecast_parity_registry.py` alongside the 8 already-filed gaps —
is **not** mechanical: choosing between `GAP`, `BACKCAST_ONLY` and
wire-it-forward is a forecast-program adjudication about whether each mechanism
has a forward analogue (rule 13 `[R-MEASURED]`). Filing them would also have
turned the dedicated `forecast-parity-guard` CI job **green**, deleting the only
live signal that these two are unadjudicated. This lane declined to do that.

Treatments, which differ because the two tests assert different things:

- **#5 `test_check_exits_zero_on_the_current_keepers`** asserts
  `cfp.main([]) == 0` — it is a *mirror inside the fast tier* of the
  `forecast-parity-guard` job's exit code. There is no way to soften it without
  reimplementing the checker. → `@pytest.mark.xfail(strict=True, reason=…)`
  citing FR-22 and
  `docs/handoffs/ffr-1e-forecast-parity-check-2026-07-31.md`. **`strict=True` is
  deliberate**: when a forecast lane clears the two fields the test XPASSes and
  fails, forcing the marker's removal instead of letting it rot into a
  permanent excuse.
- **#4 `test_all_six_keepers_resolve`** asserts *no UNACCOUNTED field in any
  ISO*. A blanket xfail here would blind the fast tier to a **third** field —
  the exact defect class FR-22 exists to catch. Instead the two known fields are
  pinned in a module-level `_FR22_OPEN_UNACCOUNTED` frozenset and the assertion
  became `unaccounted - _FR22_OPEN_UNACCOUNTED == ∅`. A new unaccounted keeper
  mechanism still reds the tier immediately, with the remedy in the message.
  Subset (not equality) so a lane clearing one of the two does not red on its
  way out.

**Net:** the fast tier is green, the guard's protective property is intact, and
the `forecast-parity-guard` CI job **stays RED on exactly these two** — which is
where the signal belongs and how a forecast lane will find it.

---

## 3 §4 baseline table, post-wave

Restated in place in `docs/handoffs/house-1-lint-ci-2026-08-08.md` §4 as a
dated addendum (the original 9-row table is preserved above it, unedited — it
is the historical measurement). The post-wave standing reference:

| # | test | status after HOUSE-2 |
|---|---|---|
| 1 | `test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion::test_derived_map_suppresses_exogenous_credit` | **STILL RED** — excluded (ercot-181 live) |
| 2 | `…::test_exogenous_credit_keeps_unit_profitable` | **STILL RED** — excluded (ercot-181 live) |
| 3 | `test_neiso_bins.py::…::test_committed_artifact_is_deterministic` | CLEARED |
| 4 | `test_forecast_parity.py::test_all_six_keepers_resolve` | CLEARED (exact-set pin) |
| 5 | `test_forecast_parity.py::test_check_exits_zero_on_the_current_keepers` | CLEARED (xfail, strict) |
| 6 | `test_outages.py::…::test_unknown_iso_degrades_to_empty` | CLEARED |
| 7–9 | `test_data_dictionary_sync.py` × 3 subtests | CLEARED on main before this lane |
| 10 | `test_integration.py::TestFullYearPerformance::test_full_year` | CLEARED (marked `slow`) |

**The new rule of the table: the fast-tier baseline on main is exactly rows 1
and 2.** Any other fast-tier failure on a PR is that PR's own.

### Still red on main, outside the fast tier (report-only, untouched)

- **`lint` job** — three items, all in files this lane did not touch, all
  belonging to other lanes:
  `ruff format --check` on `scripts/gen_caiso184_attestation.py` and
  `tests/unit/data/test_fleet.py`; `ruff check` F841 (`n_q` assigned and never
  used) at `scripts/data/derive_ercot_dam_cleared_share.py:624`. Deliberately
  not fixed — they are in-flight lanes' files and outside the chartered table;
  each is a one-line repair for its owner.
- **`forecast-parity-guard`** — red on the two §2.4 fields, **by design**
  (above).
- **`Forecast-invariant artifact audit`** — pre-existing, unexamined by this
  lane.

---

## 4 Item 2 — `assign_zone_by_coords`: consumer map, and a SPLIT outcome

The finding (sitting record T.2): `assign_zone_by_coords(lat, lon, iso)` calls
`_zone_from_location(iso, lat, lon, None, None)` — **FIPS state is always
`None`**. For PJM that means every branch of `_pjm_zone` is skipped and
`_PJM_STATE_ZONES.get(None, …)` returns the largest-load-share fallback, so
**every PJM row lands in `PJM_AEP_Ohio`**. For MISO it degrades to a two-way
`lat < 36` South/Midwest split.

### 4.1 Consumer map (the charter's gate)

Enumerated over `src/`, `scripts/`, `tests/`:

| # | consumer | mode gate | reaches PJM rules? | reaches MISO rules? |
|---|---|---|---|---|
| 1 | `data/fleet/eia860.py:2109` — `load_planned_additions` (thermal) | `runner.py:1261`, **`config.mode == "forecast"` only** | YES | YES |
| 2 | `data/fleet/eia860.py:2275` — `load_procured_vre_additions` (FFR-5E VRE limb) | `runner.py:1278`, **forecast-only AND `vre_procurement_additions_enabled` default OFF** | YES | YES |
| 3 | `data/renewables.py:1014` — `_add_proposed_capacity` | any mode, but the ISO argument is **hardcoded `"ERCOT"`** at the call | NO | NO |

**The sibling path that decides the gate.** The same coords-only branch is also
reached *without* going through the public function, at
`zone_assignment.py:892` — `_eia860_ba_zones` calls
`_zone_from_location(iso, lat, lon, None, None)` and feeds
`build_zone_lookup`, **the fleet-zoning seam every backcast keeper rides**. It
fires only for ISOs in `_EIA860_SUPPLEMENT_ISOS = {ERCOT, CAISO, NYISO, NEISO,
MISO}`. That single fact splits the item:

- **PJM is NOT in that set** (and `tests/unit/model/test_storage.py:1589`
  already pins that it stays out). Additionally, **all 1,727 PJM eGRID rows
  carry a FIPS state and coordinates** (measured), so `build_zone_lookup("PJM")`
  cannot reach the coords-only branch by either route. → **PJM is confined to
  the forecast-only limbs. Implemented.**
- **MISO IS in that set**, and the coords-only fallback is doing real work
  there: the EIA-860 supplement contributes **745 net-new plants** to
  `build_zone_lookup("MISO")` (606 forced to `MISO-Illinois`, 139 to
  `MISO-South`) that eGRID does not carry. Any real MISO coordinate rule
  redistributes those 745 across the six zones and **moves the MISO keeper's
  fleet**. → **STOPPED. Not implemented. Handed to the calibration lanes.**

### 4.2 PJM — implemented

`_pjm_zone` gains a coords-only branch. Rather than invent boundary constants
for a 13-state footprint with jagged borders (which, unlike the 1-to-6-state
ISOs in this module, no lat/lon box ladder can express), a coords-only query
**borrows the FIPS state/county of the nearest eGRID PJM plant and re-enters the
existing cited state/county/lat-lon rules** — eGRID's own authoritative
geography, with no new hand-drawn line (rule 14 `[R-ACCURATE]`: prefer the
measured datum over an estimate). Recursion is one level by construction (the
borrowed state is never `None`). A `1.0°` cap
(`_PJM_COORDS_NEIGHBOR_MAX_DEG`) keeps an out-of-footprint coordinate on the
old fallback.

Both constants are measured, not chosen:

- **Cap = 1.0°.** Nearest-neighbour spacing across the 1,727 eGRID PJM plants:
  p50 0.028°, p90 0.129°, p99 0.329°. 1.0° (~111 km N-S, ~85 km E-W at 40°N)
  clears p99 threefold and still refuses an out-of-region point.
- **Accuracy.** Leave-one-out over the same 1,727 plants (hold a plant out,
  zone it from its nearest neighbour's FIPS): **1,697/1,727 = 98.3 %**.

Measured on the live cohort this actually serves — the 371 EIA-860 PJM proposed
rows (PA 93, IL 78, VA 42, KY 37, OH 37, WV 21, NJ 21, IN 15, DE 11, MD 10,
NC 4, DC 1, MI 1):

| | agreement with the zone their real EIA-860 state implies |
|---|---|
| before (all 371 → `PJM_AEP_Ohio`) | 79/371 = **21.3 %** |
| after (nearest-eGRID-plant rule) | 356/371 = **96.0 %** |

Distribution after: `AEP_Ohio` 83, `ComEd` 76, `West_APS` 71, `Dominion` 48,
`EMAAC` 32, `Central_PA` 30, `ATSI` 19, `SWMAAC` 12 — all eight zones, versus
371/0/0/0/0/0/0/0 before.

**Keeper byte-inertness, proved two ways** (the charter's requirement):

1. **Measured.** `build_zone_lookup` hashed for all six ISOs before and after
   the edit — **byte-identical in every one**:
   ERCOT `f0491b22b0e23e97` (1,406), CAISO `5850e268d5ee23fc` (1,989),
   MISO `53dfa660b58fe03a` (2,861), NYISO `6fc003b4a052e744` (1,257),
   NEISO `38178811909d4f07` (1,561), PJM `060810369db71c84` (1,727).
2. **Pinned.** `test_pjm_coords_rule_leaves_every_iso_zone_lookup_byte_identical`
   asserts the two structural facts the inertness rests on — PJM absent from
   `_EIA860_SUPPLEMENT_ISOS`, and zero PJM eGRID rows missing a FIPS state — so
   a future edit to either cannot silently reroute a keeper through the new
   rule. Plus
   `test_pjm_coords_only_resolves_all_eight_zones` (eight real eGRID plant
   coordinates, one per zone, cross-checked against the FIPS-fed answers the
   sibling test already pins) and
   `test_pjm_coords_outside_the_footprint_keeps_the_fallback`.

**Epoch effect (the 3V precedent), for the manager's re-base tracking.** The
in-flight **FFR-5E-H / ARM3-MEASURE** artifacts were produced *before* this fix
and therefore carry the all-`PJM_AEP_Ohio` planned-additions zoning. Any PJM
forecast/hindcast artifact generated after this commit is on the new zoning and
is **not** comparable row-for-row to a pre-fix one. Stated here only — this lane
took no re-base action, per charter.

**Residual, filed not fixed (recommended to the FFR-5E lane).** The remaining
4 % is structural to a coords-only contract, and there is a strictly better
datum available *at both call sites*: the EIA-860 plant row already carries a
`State` column (`eia860.py:2081` even reads it into `norm`) and it is discarded
before the zone call. Passing it through — e.g. an optional `state=` argument on
`assign_zone_by_coords`, defaulted to `None` so every existing caller stays
byte-inert — would take PJM planned additions from 96 % to ~100 % (only PA's
Philadelphia-metro county split would still need coordinates, which the new rule
supplies). That is call-site surgery in FFR-5E-owned loaders and would change
other ISOs' forecast-only zoning too, so it is **out of this charter's scope**
and recorded here as the next step rather than taken.

### 4.3 MISO — STOPPED, escalated to the calibration lanes

Not implemented, per the charter's gate. What the owning lane needs:

- **Blast radius:** 745 plants in `build_zone_lookup("MISO")` (606 →
  `MISO-Illinois`, 139 → `MISO-South`) currently zoned by the `lat < 36`
  fallback in `_miso_zone`, feeding the MISO keeper's fleet
  (`2026-08-05-miso-132b-cc-committed`). This is a keeper-moving change and
  needs a keeper re-solve, not a housekeeping edit.
- **Why the fallback is doing so much work:** `zone_assignment.py`'s own comment
  at `_EIA860_SUPPLEMENT_ISOS` says the MISO supplement covers "28 of 1,975"
  post-eGRID-2023 plants. **Measured today it is 745 of 2,861 net-new** (2,855
  supplement rows against 2,116 eGRID MISO rows). Whatever was true when that
  comment was written, the supplement is now the primary zoning channel for a
  quarter of the MISO fleet — worth confirming before designing the fix.
- **The fix is easier than PJM's, and does not need PJM's machinery.** MISO's
  six zones are documented as *exact unions of whole states*
  (`_MISO_STATE_ZONES`, LRZ groupings). The EIA-860 plant file that
  `_eia860_ba_zones` already opens carries a `State` column it does not read —
  and `plant_state_lookup()`, in the same module, already returns
  `{plant_code: state}` from that very file. Feeding that state into
  `_miso_zone` resolves all six zones **exactly**, with no geographic
  approximation at all — the accurate-data route rule 14 `[R-ACCURATE]` prefers,
  and cheaper than PJM's nearest-plant machinery. FFR-5E §7 records the same MISO incompleteness from
  the procurement side (`docs/handoffs/ffr-5e-hindcast-arm-prereg-2026-08-09.md`
  §147, "all 51 rows collapse to" one zone).
- `tests/unit/data/test_zone_assignment.py:268–271` currently **pins the
  degraded behaviour** (`assign_zone_by_coords(46.0, -94.0, "MISO") ==
  "MISO-Illinois"` — that is Minnesota, i.e. `MISO-West`). Those three
  assertions must be re-based by whoever fixes it; they were left untouched
  here.

---

## 5 Verification record

- Fast tier (`-n 2 -m "not slow and not integration and not fulldata"`),
  baseline at `b5b88de`: 7 failed / 6,534 passed / 20 skipped / 1 xfailed /
  389 subtests passed, 619 s. After this branch: **2 failed** (the chartered
  exclusions, `TestScreenMutualExclusion`) / 6,541 passed / 20 skipped /
  2 xfailed / 389 subtests passed, 548 s.
- `scripts/check_mechanism_matrix.py` → exit 0 (only pre-existing anchor-drift
  warnings; no `ScenarioConfig` field added, so duty (c) does not apply).
- `cache-key-pin`'s exact command (`tests/regression/test_persisted_identity.py`
  + `tests/unit/config/test_cache_key_default_flip_guard.py`) → **22 passed**.
- `build_zone_lookup` hashes for all six ISOs, before vs after the
  `zone_assignment.py` edit → byte-identical (§4.2).
- `bin_assignments_NEISO.csv` regeneration diffed column-by-column: 1 of 14
  columns, 2 of 118 rows; every solve-path column unchanged (§2.1).
- `ruff format --check .` / `ruff check .` on this branch's own files: clean.
  The three pre-existing tree-wide reds are enumerated in §3 and belong to other
  lanes.
- Rule 27 `[R-PUSH]`: `zone_assignment.py`, `test_outages.py`,
  `test_zone_assignment.py` and `test_forecast_parity.py` are all ≥300 lines and
  were edited **locally with the Edit tool only** — no regenerated full-file
  content was pushed. Post-push blob verification recorded in the PR.
