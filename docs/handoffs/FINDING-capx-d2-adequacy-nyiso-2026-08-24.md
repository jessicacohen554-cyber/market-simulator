# FINDING — NYISO FC-1 / I7 base-year adequacy miss: adjudicated root cause

**Session:** capx D-2 ADEQUACY NYISO (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-24 · **Branch:** `claude/capx-d2-adequacy-nyiso-yxv6v0`
**Charter:** root-cause and fix NYISO's FC-1 I7 base-year adequacy miss in the model's
capacity **accounting**, never by relaxing the invariant.

---

## 0. Headline

**The named suspect was already fixed, and the residual is not a capacity-evolution
defect at all.**

1. The ~1.8 GW that closed between FF-2D and FFR-3A-2 is **FFR-1C hydro accreditation**,
   worth **1,763.3 MW**. Reproduced to the digit: the pre-hydro ledger is **30,322.2 MW**,
   which *is* the board's stale "firm 30.3 GW" figure.
2. The residual **35.7 MW (2026)** is a **base-year snapshot** result. **The base year
   runs no capacity evolution at all** — `evolve_fleet` is skipped when `fleet is None`
   — so there is **no adequacy backstop, no retirement screen and no entry** in 2026.
   No capacity mechanism can respond to it, by construction.
3. Forks 2 (fleet-snapshot vintage) and 3 (requirement mismatch) are **both CLOSED** on
   evidence — see §3.
4. The one provable remaining gap is **fork 1, but not hydro**: the accredited ledger
   credits **zero external firm capacity** for NYISO, while ERCOT/PJM/CAISO/NEISO all
   carry an `ADEQUACY_EXTERNAL_TIE_FIRM_MW` entry and the model itself floors **900 MW
   of always-on HQ firm import** in NYISO dispatch.

**No fix that closes I7 was shipped, deliberately.** Closing (4) honestly requires a
*published* NYISO external-capacity accreditation, which this session could not source
from primary documents. Per the charter — *"if the honest fix leaves I7 failing, that is
the finding — report it; do not tune to the invariant"* — that is the finding. §6 states
exactly what intake would close it.

---

## 1. The live record, reproduced exactly

`frontend/data/forecast/ff-verdicts.json::nyiso-t1f` (FFR-3A-2 @ `8ba59281`):

> FAIL `['I7']`: 2026: accredited firm 32085 < requirement 32121 MW;
> 2027: accredited firm 32339 < requirement 32390 MW

The FFR-3A-2 bundles are gitignored, but the **committed** FFR-1C NYISO base-year ledger
(`results/ffr1c/after-nyiso/NYISO/cfde2bf55b3a06d9/evolution_2026.json`) reproduces the
2026 leg exactly:

| quantity | value | source |
|---|---:|---|
| `peak_demand_mw` | 29,750.971 | ledger |
| `reserve_margin` | 0.078469 | ledger |
| accredited firm = peak × (1 + rm) | **32,085.5 MW** | verdict says 32085 ✓ |
| requirement = peak × 1.244 × 0.8679 | **32,121.2 MW** | verdict says 32121 ✓ |
| **shortfall** | **35.7 MW (0.111 %)** | verdict says 36 ✓ |

*(The two runs carry **different** resolved cache keys — FFR-1C `cfde2bf55b3a06d9` vs
T1-F `2bd878d87848785c` — yet their 2026 ledgers agree to the digit. That is itself
corroboration of §4a: with no evolution in the base year, the accredited ledger depends
only on the base-fleet snapshot and the pools, so the flags that separate the two
postures cannot move it.)*

`resolve_adequacy_requirement_mw` takes the **fallback** branch for NYISO
(`FORECAST_POOL_REQUIREMENT_BY_ISO` holds **PJM only**), so the requirement factor is
`(1 + IRM 0.244) × icap_to_ucap 0.8679 = 1.0796676`. The I12 WARN band (floor 8.0 %,
out 7.8 %) is the same two numbers restated as a margin: `1.0796676 − 1 = 7.967 %` vs
`rm = 7.847 %`.

---

## 2. What closed the 1.8 GW — FFR-1C hydro accreditation, measured

`modelled_hydro_nameplate_mw("NYISO", …)` = **4,587.1 MW**, credited at the published
NYISO CAF `HYDRO_ACCREDITATION_CREDIT_BY_ISO["NYISO"] = 0.3844`:

```
FF-2D firm (hydro uncredited)  = 30,322.2 MW   <- the board's stale "30.3 GW"
+ FFR-1C hydro credit          =  1,763.3 MW   (4,587.1 x 0.3844)
= FFR-3A-2 accredited firm     = 32,085.5 MW
  requirement                  = 32,121.2 MW
  RESIDUAL                     =     35.7 MW
```

The full ledger reconciles to the same total, so nothing else is unaccounted for:

| class | basis | MW |
|---|---|---:|
| thermal (persistent fleet, 30,249.0 MW nameplate) | UCAP `1 − eford` | 28,427.9 |
| wind pool 2,400 | credit 0.1684 | 404.2 |
| solar pool 1,500 | credit 0.1224 | 183.6 |
| storage | pre-dilution firm | 1,306.5 |
| hydro 4,587.1 | CAF 0.3844 | 1,763.3 |
| **external firm import** | **absent** | **0.0** |
| **total** | | **32,085.5** |

The persistent fleet is **thermal-only** (`gas_cc` 11,199.0 · `gas_st` 9,372.5 ·
`nuclear` 3,325.9 · `gas_ct` 3,053.6 · `oil` 2,905.5 · `biomass` 392.4) — confirming the
documented ledger structure: hydro, VRE pools, storage and imports all enter from
outside the fleet, and imports enter at zero.

---

## 3. Fork adjudication

### Fork 2 — fleet snapshot vintage: **CLOSED, not reproduced**

open_frontier #6 feared the hydro fleet "silently drops ~3.3 GW past the last EIA-923
vintage." **It does not.** `modelled_hydro_nameplate_mw` clamps the census year to
`EIA923_LATEST_FINAL_VINTAGE` (2024), so every forecast year resolves the full
final-release census:

| year | 2026 | 2027 | 2030 | 2040 | 2050 | `None` |
|---|---:|---:|---:|---:|---:|---:|
| nameplate MW | 4,587.1 | 4,587.1 | 4,587.1 | 4,587.1 | 4,587.1 | 4,587.1 |

The clamp is the thing that prevents the feared drop, and it was previously **unguarded
by any test**. This session adds that guard (§5).

### Fork 3 — requirement mismatch: **CLOSED, requirement verified against source**

Both requirement inputs check out against their published sources:

* **IRM 0.244** — NYSRC 2025-2026 IRM Final Base Case. Independently corroborated by the
  repo's own capacity-deliverability intake:
  `data/raw/capacity-deliverability/nyiso/nyiso.csv` carries
  `NYISO,2025/2026,annual,NYCA,rto,system_requirement,,0.244` from
  `2025-2026-LCR-Report-Clean.pdf` p.2. ✓
* **ICAP→UCAP 0.8679** = `1 − 0.1321` NYCA translation ("Derate") factor, NYSRC
  2025-2026 IRM Study Technical Appendices, Appendix D §D.1.1 Table D.2 — the
  **most-recently-realized** (CY 2024-2025) value, intaken as
  `icap_ucap_translation_factor` rows in
  `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv`. ✓

**The mixed vintage is deliberate and owner-ratified, not a defect.** Pairing a
2025-2026 IRM with a CY 2024-2025 derate factor is **FF-3D Option B** (NYCA-wide static
proxy), *owner-selected 2026-07-18* over the recommended Option A, with the lag disclosed
verbatim in the constant's own citation block. The series is rising (0.083 → 0.132 over
2020-21 → 2024-25) and NYSRC publishes only realized values, so there is no 2025-2026
factor to pair.

> ⚠ **A trap worth naming.** A translation factor of **0.1331** — one year of drift on a
> series moving ≈ 0.012/yr — would close I7 exactly. That is precisely why it must not be
> touched: re-deriving a measured-behaviour parameter because a residual moved is
> forbidden by rule 23 `[R-FROZEN-DERIVE]` and rule 13 `[R-MEASURED]`. **The requirement
> side is correct as specified and was left alone.**

### Fork 1 — accreditation accounting: **the winner, but the named suspect is spent**

Hydro (the charter's named suspect, lanes FF-1C / CR-3.1) is **already credited** and
accounts for the *entire* 1.8 GW closure. What remains is a different member of the same
defect class — §4.

---

## 4. Root cause

### 4a. Why no mechanism closes it — the base year runs no capacity evolution

`src/market_sim/runner.py:1645-1665`:

```python
if fleet is None:
    # First year: build the base fleet. …
    fleet = build_base_fleet(…)
    # First year has no evolution: the ledger records the base fleet
    # snapshot only (fleet_by_fuel before == after, no events).
else:
    … evolve_fleet(…)          # steps 0-6, incl. the reserve-margin backstop
```

Confirmed empirically on the committed 2026 ledger: `fleet_by_fuel_before ==
fleet_by_fuel_after` is **True**, and `thermal_additions`, `retirements`,
`renewable_additions`, `storage_additions` are **all empty**, with
`entry_decided_mw_by_tech = None`.

So the reserve-margin adequacy backstop — step 6 of `evolve_fleet`, default-ON for
capacity-market ISOs — **never runs in the base year**. I7's 2026 leg is therefore a
statement about the *base-fleet accredited ledger versus the requirement*, not about
capacity-evolution behaviour.

**This is structurally correct and must not be "fixed."** 2026's iron is already built;
force-building into the base year would manufacture capacity that does not exist, which
rules 1 `[R-STRUCT]` and 21 `[R-DOF]` forbid. The consequence is simply that **I7's
base-year leg grades the input data, and only the input data can move it.**

### 4b. The provable accounting gap — NYISO external firm capacity is credited at zero

`ADEQUACY_EXTERNAL_TIE_FIRM_MW` (`config/capacity_market.py:2526`) credits the firm
import capacity each ISO's own RA ledger counts:

| ISO | MW | citation |
|---|---:|---|
| ERCOT | 817.0 | Dec-2025 CDR, non-synchronous ties |
| PJM | 1,281.7 | 2026/2027 BRA Report Table 7, cleared import UCAP |
| CAISO | 3,371.0 | DMM 2024 Table 15.6 RA Imports |
| NEISO | 567.0 | FCA 17 cleared imports (NY/QC/NB) |
| **NYISO** | **— absent —** | **none** |

NYISO belongs in this registry on the registry's own stated logic, and its absence is a
gap rather than a decision:

* NYISO's model topology has **no import zone** (`Upstate_West, Capital_Hudson,
  Lower_Hudson, NYC, Long_Island`), so external firm capacity is **entirely absent from
  the model's persistent fleet** — verified in §2, where imports contribute 0.0 MW.
* Yet the model **does** carry NYISO firm imports in *dispatch*:
  `IMPORT_TRANCHES["NYISO"]` spans 6,385 MW, and
  `NYISO_FIRM_IMPORT_FLOOR_FRAC = {"HQ_hydro": 1.0, "IESO_Ontario": 0.0}` floors the
  **900 MW HQ (Châteauguay/Cedars) firm baseload as must-flow in every hour** —
  "firm, long-term scheduled hydro/nuclear baseload that flows regardless of NY's hourly
  price" (`model/interchange/nyiso.py:541-556`).
* NYISO's own ICAP construction counts external capacity resources as supply toward the
  same IRM the model's requirement is built from.

So dispatch relies on firm imports that the adequacy ledger credits at zero — **exactly
the case-(b) asymmetry FF-2B closed for CAISO and NEISO on 2026-07-19, with NYISO
skipped.**

---

## 5. What was shipped

**Test only — no solve-affecting change.**

`tests/unit/model/test_hydro_accreditation.py` gains
`TestForecastVintageClampIsStable` (3 tests): a hermetic, **year-sensitive** guard that
the forecast hydro basis never falls off the EIA-923 vintage cliff. The patched loader
serves the full census at or before the final vintage and a partial
(large-reporters-only) census after it, so the test cannot pass trivially.

**Mutation-verified:** deleting the `min(int(year), EIA923_LATEST_FINAL_VINTAGE)` clamp
fails 6 assertions across 2 of the 3 tests; source restored byte-clean (empty
`git diff`). Suite: **14 passed, 18 subtests passed**.

This closes open_frontier #6 with a regression guard rather than an assertion.

---

## 6. What would close I7 honestly — bounded intake, NOT taken here

Add NYISO to `ADEQUACY_EXTERNAL_TIE_FIRM_MW` at its **published** external-capacity
accreditation, on the FF-2B construction already used for CAISO/NEISO/PJM.

**Why this session did not ship a number.** The obvious in-repo candidate — the model's
own 900 MW HQ firm base — is documented in `scripts/data/derive_nyiso_import_tranches.py`
as *"kept at the ladder's established value so the floor is unchanged"*, i.e. an
**inherited ladder constant, not a published RA accreditation**. Every peer entry in the
registry carries a hard primary citation (BRA Table 7, DMM Table 15.6, FCA-17). Shipping
900 MW — or any derate of it — on a weaker basis would violate rule 5 `[R-NO-MAGIC]` and
rule 13 `[R-MEASURED]`, and it would land in the one place where a wrong number is
invisible: an invariant it happens to clear.

**The intake needed** (unrestricted — data intake needs no marker, rule 22):

* **Primary source:** NYISO Gold Book (Load & Capacity Data Report), external-capacity /
  UDR capacity table, and/or the NYISO ICAP spot-auction external-supplier capacity.
  The 2023-2026 editions are **gitignored payloads not on disk**; the re-fetch URL
  pattern is verified in `data/raw/NYISO/README.md`
  (`https://www.nyiso.com/documents/20142/2226333/<year>-Gold-Book-Public.pdf`), with
  `SHA256SUMS.txt` as the identity record. Note `pypdf` is **not** a project dependency.
* **Basis discipline:** the value must be external capacity **NYISO's own ICAP ledger
  counts**, on the model's UCAP requirement basis, vintage-matched to the 2026 base year
  — never the Simultaneous Import Limit (4,350 MW), which is a deliverability *limit*,
  the exact error CAISO's entry explicitly rejects ("NOT the Maximum Import
  Capability … crediting it would overstate").

**Expected effect, stated in advance so it cannot be back-fitted:** any real value is
**O(10²–10³) MW against a 36 MW gap**, i.e. it should clear I7 by one to two orders of
magnitude. *That overshoot is the evidence the input is honest rather than tuned* — a
number that landed just above 36 MW would be the suspicious one (rule 21 `[R-DOF]`).

---

## 7. Two further defects found — routed to the director, NOT changed here

Both were found while tracing the backstop. Both are real; both have **cross-ISO blast
radius**, which the charter's deconfliction clause routes to the director rather than
this lane.

### D-1 · The I7 checker and the model resolve **different requirements** for PJM

`scripts/check_forecast_invariants.py:465` calls
`resolve_adequacy_requirement_mw(run.config, run.iso, peak)` — **without `year`** — while
the model's backstop (`adequacy.py:471`) calls it **with `year`**. `year=None` forces the
fallback branch, so for the one ISO with a published FPR:

| | factor | source |
|---|---:|---|
| model builds to | 0.9170 | published 2026/2027 FPR |
| checker grades at | 0.90699 | fallback `(1+0.178) × 0.7699` |

**The same `year` drop repeats at line 628**, where the I12 reserve-margin band derives
its requirement-implied floor — so both I7 and I12 grade PJM on the fallback basis.

The checker is currently **~1.1 % lenient for PJM**, and `check_i7_reliability_floor`'s
own docstring promises the opposite: *"Checker and model now measure the same quantity,
so the adequacy backstop … satisfies I7 honestly rather than by coincidence."* Inert for
NYISO (no FPR). **Fixing it makes I7 stricter — it is not a relaxation — but it moves
PJM's registered FC-1 verdict**, so it belongs to a scorer/governance round.

### D-2 · The backstop sizes on a different EFORd than the unit it builds

`apply_reserve_margin_build` sizes its build with the class constant
`EFORD["gas_ct"] = 0.06`, but `_make_new_generator` sets no `eford` for plain fossil
techs, so the new unit takes the `Generator` default **0.05** and the ledger accredits it
at 0.95. The backstop therefore **over-delivers ≈ 1 %** of every gap it closes, and the
two sides disagree about the same unit — a rule 19 `[R-ONE-MECH]` one-basis violation.

Blast radius: `eford` also feeds dispatch availability
(`data/fleet/arrays.py:263`, `(1.0 - gen.eford) * base`), and `_make_new_generator`
special-cases `eford` for nuclear/hydrogen/CCS/geothermal but not `gas_ct` (0.06) or
`coal` (0.08). So every economically-built CT and coal unit in **every ISO and both
modes** currently carries the wrong forced-outage rate. **Solve-affecting and
backcast-reachable** ⇒ handed back, not touched (NYISO's backcast lane is CALIBRATED and
its frontier was owner-ratified 2026-08-23).

*(A third, benign inconsistency: the backstop's `accredited_firm_capacity_mw` call omits
`year=year`, unlike the diagnostic `firm_clean_accredited_mw` beside it. Inert for
forecast years — both clamp to the 2024 vintage — but it would diverge in a pre-2024
hindcast. Bundled into D-2's routing.)*

---

## 8. Open item — 2027 was not isolated

2026 is fully explained. **2027's 51 MW was not measured**, because no solve was run
(§9). In 2027 `evolve_fleet` *does* run, so the backstop fires; arithmetic on the
verdict's own numbers suggests it is bounded by the BLK-10 `entry_rate_limits`
growth-ladder rather than by the queue cap (NYISO's is 4 GW, far above the need), which
would make the residual a **deliberate deficit carried forward** — structural, not a
convergence bug. **This is inference, not measurement**, and is flagged as such.

---

## 9. Governance

* **Rule 28 `[R-MECH-MATRIX]` — no shard edit required, and none made.** Checked §5.5
  NYISO (frontier ratified 2026-08-23, lane quiet). This work is **off-queue**, on the
  charter's own pre-authorized ground: an FC-1 invariant repair chartered by the FF
  program, not a backcast calibration lever. **No mechanism was tested** — no solve, no
  flag armed, no `ScenarioConfig` field added — so duties (b) and (c) do not trigger.
* **Rule 22 `[R-HOLDOUT]`** — no backcast year solved, scored or registered. The only
  run artifact read is a committed **2026 forecast-mode** ledger. Freeze not implicated.
* **Rule 13 `[R-MEASURED]`** — no measured outcome fed back; the one input that *would*
  have closed I7 by adjustment (the NYCA translation factor) was identified and
  deliberately left untouched (§3).
* **Deconfliction** — no backcast keeper shard, `status/*.js`, `calibration-complete.json`,
  offer curve or commitment bridge touched. The two cross-ISO defects are reported, not
  changed.
* **No forecast run registered.** No solve-affecting change was shipped, so the
  FFR-3A-2 leg remains the current valid measurement of I7 and a re-run would reproduce
  it identically. Registering a duplicate would add no information. **I7's honest state
  is unchanged: FAIL, 35.7 MW (2026) / 51 MW (2027)** — and §4a explains why no
  mechanism in the model can move the 2026 leg.

---

## 10. Recommendation

1. **Route the NYISO external-capacity intake (§6)** — the single change that closes
   FC-1 for NYISO honestly. Bounded: one registry row, one citation, one re-solve.
2. **Route D-1 (§7)** to a scorer/governance round — it changes PJM's FC-1 verdict.
3. **Route D-2 (§7)** to a lane authorized for cross-ISO solve-affecting changes.
4. **Do not** treat I7's 2026 leg as a capacity-evolution failure in the D7 re-score. It
   grades the base-fleet ledger, which no mechanism in the model can move.
