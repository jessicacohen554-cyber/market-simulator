# FINDING — nyiso-107: the NYISO hydro miss is an INPUT truncation, not a hydrology signal or a mechanism gap — and NYISO is the only material-hydro ISO running unrepaired

**Session:** nyiso-107. **Keeper under test:** `2026-07-31-nyiso105-chp-heat-rates`
(bundle `results/calibration/nyiso105_chpheatrate_B`, CALIBRATED-WITH-CAVEATS,
0 FAILs, 1 ledgered caveat C3c). **Frozen HEAD:** `3bfca72`.
**Solves run: ZERO.** Scope Item B closed on measurement alone — the
nyiso-93/94/95/97/99/101/105/106 pattern. Owner decisions taken in-session are
recorded in §F.

Scope Item B asked a specific question and it has a specific answer, but the
answer is not the one the question anticipated (§B). What replaced it is a
larger, exactly-quantified defect on the **other side of the seam** (§C), and a
**provable kill** of the lever the item existed to size (§D).

---

## §A — What Item B was, and the two premises it carried

nyiso-106 re-framed `hydro_budget_nameplate_aware` before it was ever sized: the
lever's apparent NYISO target — hydro **+1.3 / +1.3 / −12.7 %** on a 26.5 TWh
class, "a miss ENTIRELY in 2025" — is measured **across a benchmark-basis
switch**. 2023/2024 actuals (28.031 / 27.465 TWh) are EIA-923; the 2025 actual
(24.104) is the EIA-930 swap `_backfill_renewables_eia930` applies because the
2025 923 vintage is a preliminary release. Item B's instruction: put all three
years on ONE basis and report how much of the −12.7 % survives. "If little does,
the lever is dead ex-ante and that is a full no-solve result."

Both premises were checked. **The basis switch is real** — reproduced exactly
from the committed data:

| year | vintage completeness | EIA-923 raw | EIA-930 `NG: WAT` | 923/930 | **as scored** | branch |
|---|---|---|---|---|---|---|
| 2023 | 1.0495 | 28.0312 | 26.8365 | 1.0445 | **28.0312** | raw 923 |
| 2024 | 1.0370 | 27.4654 | 26.7777 | 1.0257 | **27.4654** | raw 923 |
| 2025 | 0.8850 | 20.5582 | 24.1039 | **0.8529** | **24.1039** | **930 swap** |

The swap fires in 2025 and only in 2025, because only there does the raw 923
class total fall below `_EIA923_RENEWABLE_COMPLETENESS_FRACTION` (0.90) of the
EIA-930 series. Model hydro, decoded from the committed keeper payload, is
**28.3833 / 27.8294 / 21.0482 TWh**, reproducing the scope's +1.26 / +1.33 /
−12.68 % exactly.

---

## §B — The scoped question, answered: the miss survives EVERY consistent basis

| benchmark basis | 2023 | 2024 | 2025 |
|---|---|---|---|
| as scored (mixed 923 / 923 / 930) | +1.26 % | +1.33 % | **−12.68 %** |
| **all EIA-930** | +5.76 % | +3.93 % | **−12.68 %** |
| **all EIA-923, carry-corrected** | +1.26 % | +1.33 % | **−13.41 %** |

**Item B's stated kill condition is not met.** Putting all three years on one
basis does not dissolve the −12.7 %; on the all-930 basis it is bit-unchanged
(2025 was already there) and 2023/2024 get *worse*, and on the carry-corrected
923 basis it grows slightly. The single-year shape is **not** a coverage
artifact of the benchmark.

That is because the benchmark is the *repaired* side. Which raises the question
Item B did not ask.

---

## §C — The real defect: the model is FED the truncated vintage and SCORED against the repaired one

`_load_hydro_generation` → `load_hydro_budget` builds the LP's hydro fleet and
its monthly energy budget from EIA-923 prime-mover `HY`. The NYISO keeper
carries `hydro_backfill_year = None` and `hydro_eia930_monthly = False`
(read from its committed `meta.json`), so **nothing repairs the input side**:

| year | HY plants in EIA-923 | LP hydro units | **LP budget TWh** | max MW | model dispatch TWh |
|---|---|---|---|---|---|
| 2023 | 157 | 154 | 28.4033 | 4,647.5 | 28.3833 |
| 2024 | 150 | 147 | 27.8750 | 4,587.1 | 27.8294 |
| **2025** | **4** | **3** | **21.0482** | 3,343.0 | **21.0482** |

Three facts, each measured:

1. **The 2025 LP hydro fleet is 3 plants**, against 147 the year before —
   a 2.0 % plant retention. Max MW collapses 4,587 → 3,343.
2. **The model dispatches its budget exactly**: 21.0482 TWh dispatched against
   a 21.0482 TWh budget, equal to four decimals. Hydro is energy-limited at
   MC 0, so with 3,343 MW of headroom it spends the whole budget.
3. **The scored −12.68 % IS the input truncation**, arithmetically:
   `21.0482 / 24.1039 − 1 = −12.68 %`. There is no dispatch behaviour in it.

This is the same one-sided-repair family as nyiso-106's solar (§A) and `OTHER`
(§E) findings, **inverted**. There the model was *injected* at the carried-forward
level and *scored* against the raw truncated vintage; here it is *fed* the raw
truncated vintage and *scored* against the repaired level. Same seam, opposite
side.

### C.1 The benchmark is right — independently falsified

NYISO MIS **P-63 Real-Time Fuel Mix** publishes **Hydro** as its own category
(unlike solar, which forced nyiso-106 into a night-baseline/daylight-bulge
decomposition). So NYISO's own market telemetry is a direct, EIA-independent
instrument on the level:

| year | **P-63 Hydro** | EIA-930 `NG: WAT` | P-63 vs 930 | EIA-923 raw |
|---|---|---|---|---|
| 2023 | 27.1845 | 26.8365 | **+1.30 %** | 28.0312 |
| 2024 | 26.9763 | 26.7777 | **+0.74 %** | 27.4654 |
| 2025 | **24.2489** | **24.1039** | **+0.60 %** | **20.5582** |

Two fully independent instruments agree to within **1.3 / 0.7 / 0.6 %** in every
year. **NY hydro genuinely fell ~10 % in 2025** (P-63 26.98 → 24.25; 930 26.78 →
24.10) — that is real hydrology and the benchmark captures it. The number that
is wrong is the **EIA-923 raw 20.5582**, which sits 15 % below both instruments.
The 2025 benchmark is **not** the artifact; the 2025 **input** is.

### C.2 NYIS `NG: WAT` carries no pumped-storage fold — the `.` cell is correct

Before any successor pins a level to `NG: WAT`, the MISO/PJM question must be
asked (rule 14): NYIS files **no `NG: PS` column** (series present: COL, NG,
NUC, OIL, OTH, SUN, WAT, WND), the same surface condition as the two listed BAs.

| year | `NG: WAT` | EIA-923 `HY` | ratio |
|---|---|---|---|
| 2023 | 26.8365 | 28.4033 | **0.9448** |
| 2024 | 26.7777 | 27.8750 | **0.9606** |
| 2025 | 24.1039 | 21.0482 | 1.1452 *(inverted by truncation — not quotable)* |

NYIS `NG: WAT` runs **below** 923 `HY` in both complete years — the opposite of
the MISO/PJM fold signature (+13.5 / +18.5 % and +72.1 / +78.5 %). NYIS PS is
additionally **net negative** in EIA-923 (−0.372 / −0.410 / −0.490 TWh, 2 plants),
so pumping is netted, not folded in gross. **NYISO's absence from
`EIA930_PS_FOLDED_INTO_WAT` is confirmed**, and the `hydro_level_923_hy` screen's
`.` for NYISO stands — including its recorded warning that the 2025 inversion is
pure truncation and must never be re-run on a preliminary vintage.

### C.3 NYISO is the ONLY material-hydro ISO running unrepaired

2025 hydro plant retention in the LP, and each keeper's repair posture:

| ISO | 2024 → 2025 units | retention | 2025 budget TWh | `--hydro-backfill-year` | `--hydro-eia930-monthly` |
|---|---|---|---|---|---|
| ERCOT | 12 → 1 | 8.3 % | 0.017 | None | False |
| CAISO | 160 → 26 | 16.2 % | 12.319 | **2024** | **True** |
| PJM | 72 → 10 | 13.9 % | 2.290 | **2024** | **True** *(pin internally refused, PS fold)* |
| MISO | 160 → 14 | 8.8 % | 0.970 | **2024** | **True** *(pin internally refused, PS fold)* |
| **NYISO** | **147 → 3** | **2.0 %** | **21.048** | **None** | **False** |
| NEISO | 166 → 5 | 3.0 % | 0.091 | **2024** | **True** |

The truncation is universal — every ISO's 2025 EIA-923 hydro vintage is an early
release. **Four of the six keepers arm the repair; NYISO does not.** The only
other unrepaired keeper is ERCOT, whose hydro is 0.017–0.463 TWh/yr (immaterial,
~0.1 % of load). **NYISO is the sole ISO where a material hydro class —
26.5 TWh/yr, ~18 % of NYISO load — runs on an unrepaired truncated input.** This
is not an exotic gap; it is a standard recipe element every other hydro-material
ISO already carries.

---

## §D — The lever itself: `hydro_budget_nameplate_aware` is PROVABLY INERT at NYISO

**Structurally.** `load_hydro_budget` encloses the entire nameplate-aware branch
in `if monthly_target_mwh is not None:` (`data/hydro.py:724`, allocator at
:732–748). `build_hydro_fleet` sets `target = None` (:1084) unless
`eia930_monthly` or `forecast_budget` is set. The keeper carries both `False`, so
`nameplate_aware_target` is **never read**. Its own docstring says so:
*"Ignored when `monthly_target_mwh` is `None`."*

**Empirically.** Building the NYISO hydro fleet at exactly the keeper's settings,
flag off vs on:

| year | units | budget TWh | energy sha (off / on) | pmax sha (off / on) |
|---|---|---|---|---|
| 2023 | 154 | 28.4033 | `939797e1d578cee7` / `939797e1d578cee7` | `b7302477b07be95e` / same |
| 2024 | 147 | 27.8750 | `0e15d6a2cde4e79d` / `0e15d6a2cde4e79d` | `b382890fab610a7a` / same |
| 2025 | 3 | 21.0482 | `860247dfee9bd600` / `860247dfee9bd600` | `17334f1462619707` / same |

**BIT-IDENTICAL in every year.** Arming the flag alone would have solved a
bit-identical control and burned two multi-year invocations to measure zero.

**And it stays trivial even after its prerequisite lands.** Once a target exists,
the allocator does measurable but negligible work:

| prerequisite state | clipped plant-months | re-allocated | % of budget | physically unattainable |
|---|---|---|---|---|
| with `--hydro-backfill-year 2024` | 10 | 3,683.8 MWh | **0.015 %** | 0 |
| without the backfill (3 plants) | 4 | 196,793.1 MWh | 0.818 % | 0 |

It never changes the annual total (24.0625 TWh with and without) — it only shifts
energy *within* months. The 0.818 % figure is not a signal either: it is the
allocator papering over 24.06 TWh being assigned to 3 plants at an absurd 82 %
capacity factor, i.e. the same defect §C describes.

**Cell `U → I`.** This is the nyiso-105 item-6 pattern exactly: *the arm is the
pair, not the flag*, and the queue's own suggested single-flag arm was a no-op by
construction. It is also the third ISO to reach `I` for the same structural
reason (MISO at miso-109, PJM at pjm-143): **any ISO with no level target gets
`I` by construction.**

---

## §E — The successor, chartered not armed

The repair is already built, already validated, and already armed in four
keepers. Its measured effect at NYISO, applied to all three years:

| year | bare (KEEPER) | `--hydro-backfill-year 2024` + `--hydro-eia930-monthly` | Δ TWh |
|---|---|---|---|
| 2023 | 154 units / 28.4033 | 155 units / 26.8365 | **−1.5668** |
| 2024 | 147 units / 27.8750 | 147 units / 26.7463 | **−1.1287** |
| 2025 | **3 units / 21.0482** | **147 units / 24.0625** | **+3.0143** |

Two things must be pre-registered before that becomes an arm, and neither is
settled here:

1. **It moves all three years, not just 2025.** The flag is passed verbatim to
   every year in the run, so 2023/2024 take the 930 level too. Against the
   as-scored benchmark that reads −4.26 / −2.62 / −0.17 % — trading a
   2025-only miss for a 2023/2024 one. The genuinely consistent design puts
   input *and* benchmark on the same basis; picking which basis is the
   pre-registration's job.
2. **A 930 level pin makes the hydro VOLUME statistic near-tautological.** With
   the budget pinned to the same `NG: WAT` series the class is scored against,
   the volume error goes to −0.17 % by construction. That is admissible under
   rule 13 — an inflow/water-availability budget is a physical input that
   regenerates forward through `forecast_monthly_hydro` — but it means the
   hydro *volume* number stops measuring skill and becomes plumbing. The
   dispatch **shape** (C7 diurnal, hourly r) remains a free model output and is
   where the skill claim would have to live. A successor must say this out loud
   rather than bank the −0.17 % as an improvement.

Both PJM and MISO take the backfill **without** the pin (their `NG: WAT` pin is
internally refused for the PS fold), which is a third live option — it restores
147 plants and keeps input and units on the same 923 `HY` population, at the cost
of a +7.9 % 2025 overshoot (25.9944 vs 24.1039).

**OWNER DECISION (in-session): report and charter, do not arm here.** The pair
changes the keeper's hydro input in all three years and deserves its own
pre-registered A/B with a same-HEAD control, not a tail-end ride on a no-solve
session.

---

## §F — What this changes on the record

* **Scope Item B — CLOSED, no solve.** Its stated kill condition (*"if little of
  the −12.7 % survives one basis, the lever is dead"*) is **not met** — the miss
  survives every consistent benchmark basis. The lever dies anyway, for a better
  and provable reason (§D).
* **`hydro_budget_nameplate_aware` NYISO `U → I`**, bit-identical on the keeper
  config in all three years, structurally *and* empirically.
* **The −12.7 % is re-attributed** from "a hydro-dispatch miss" to "an
  unrepaired truncated input", quantified to four decimals, with the benchmark
  independently falsified as *correct* by NYISO P-63.
* **NEW cross-ISO fact:** NYISO is the only material-hydro ISO whose keeper runs
  unrepaired. Named successor, chartered, not armed.
* **`hydro_level_923_hy` NYISO `.` re-confirmed** on an independent measurement
  (§C.2), including the 2025-inversion trap.
* **Item A (matrix §5.5 item 11b, the cross-ISO `OTHER` basis asymmetry) was put
  to the owner and DEFERRED** — it stays chartered for a cross-ISO session
  rather than being edited from a NYISO lane. NYISO's `OTHER` 2025 +11.4 %
  remains barred from sizing or judging any mechanism.
* **Rule 28 guard extended** (cross-ISO infrastructure, §G).
* **No mechanism armed**; no `ScenarioConfig` field added; no keeper changed; no
  caveat slot spent; **zero fitted parameters**; C3c untouched and its closed
  queue stays closed. No dashboard registration — no bundle was produced.

---

## §G — Found in passing and FIXED: the matrix keeper-stamp guard was blind

Rule 28 requires the promoting session to re-stamp `MECH_MATRIX.keepers[ISO]`
when a keeper changes, but `check_mechanism_matrix.py` never compared that header
against the authoritative shard `frontend/data/backcast/keepers/<ISO>.json`. Three
ISOs had drifted simultaneously and all three passed CI (nyiso-105 missed its
stamp — repaired by nyiso-106 at `988dd47`, merged as PR #3222; ERCOT and CAISO
still read 2026-07-29 ids after 2026-07-31 promotions).

The guard now compares them, with a deliberate warn/fail split:

* **Pre-existing drift WARNS** — it belongs to the owning ISO's lane, not to
  whichever PR runs next. Verified: `--base origin/main` reports ERCOT and CAISO
  and exits **0**, so main stays green and neither drift is fixed from this lane.
* **A PR that itself moves a keeper shard without re-stamping FAILS** — exactly
  the duty rule 28 states. Verified end-to-end on a throwaway commit touching
  `keepers/ERCOT.json`: ERCOT escalated to `::error`, CAISO stayed `::warning`,
  exit **1**.

6 tests added (`tests/unit/config/test_mechanism_matrix_keeper_stamp.py`), all
pass; the guard stays stdlib-only.

---

Evidence in-repo: `scripts/probes/_nyiso107_hydro_basis_audit.py`;
`results/calibration/_nyiso107_hydro_basis_audit.json`.
