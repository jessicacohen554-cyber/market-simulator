# PRECOMMIT — nyiso-226: SCREEN the NYC ST_GAS persistent-base coefficient re-basing on 2023

**Session:** nyiso-226 (parent / orchestrator) · **ISO:** NYISO · **Date:** 2026-09-10
**Keeper / control:** `2026-09-09-nyiso-221-fuelvintage-span`
(`results/calibration/nyiso_fuelvintage_A`), **UNCHANGED by this document.**
**Predecessor:** `docs/FINDING-nyiso225-topology-split-closed-2026-09-10.md` §8 —
the OUTSTANDING OWNER CALL it carried, put and answered.

**Written and pushed BEFORE any solve** (rule 29 `[R-SCREEN]`). Everything below is
measured off committed artifacts and source data at zero LP; **the parent runs no LP**
(rule 32 `[R-SHARD]`).

---

## 0. Authorization — this is an OWNER CALL that was taken, not a lane's judgement

nyiso-203 measured the defect, refused to act on it, and reported it. nyiso-225 §8 carried
it forward as *"one OWNER CALL is outstanding, and it is not a lane"*. It was put to the
owner on **2026-09-10** with the cost stated, and the ruling is:

> **Screen it on one year first.**

So this is neither a lane arming a coefficient on its own reading (nyiso-203 was right to
refuse that) nor a full-span spend. It is the exact middle course the owner named, executed
under rule 29 `[R-SCREEN]`.

**Rule 23 `[R-FROZEN-DERIVE]` has NO source-data trigger here and this document does not
claim one.** The CAMPD unit-level extract, the guard-corrected outage extract, the bin
assignments and the archived zone TMAX are all unchanged since the 2026-07-26 re-derivation.
This proceeds as a **construction repair under rule 14 `[R-ACCURATE]`** — the same class as
the capx D49/D50 seam repair — on the owner's authorization, and it is declared as such.

---

## 1. The object, and the one construction under test

The single live row of `data/raw/reference/reliability_floor_coeffs_NYISO.csv`:

```
NYISO,NYC,ST_GAS,tmax,-50.0,0.175,True,0.996,...,pro_rata
```

A −50 °C `tmax` threshold is never not met, so the limb binds in all 8,760 hours, and
`pro_rata` (`model/interchange/core.py::_apply_frac`) sets
`min_gen[r,t] = frac × pmax[r] × availability[r,t]` on **every** NYC ST_GAS unit.

**The defect (nyiso-203, reproduced here from source):** `frac` is asserted as a
**per-unit-hour capacity factor** — that is the grain `_apply_frac` applies it on — but the
identified statistic is a fleet-aggregate **DAILY-MEAN** cool-day when-available CF p25.

| basis | value |
|---|---|
| fleet-aggregate **DAILY-MEAN** p25 — as IDENTIFIED, = the frozen coefficient | **0.174847** (frozen cell 0.1750) |
| fleet-aggregate **HOURLY** p25 — the time grain it is APPLIED on | **0.166292** |
| pooled per-**UNIT**-hour p25, capacity-weighted | 0.111796 |
| pooled per-**UNIT**-hour p25, unweighted | 0.026198 |

**EXACTLY ONE of these is screened, and it is fixed ex ante:**
`floor_pct 0.1750 → 0.16629202320362052` (−4.976 %), the **time-aggregation repair alone**,
holding the population basis at the frozen fleet aggregate.

**Why not the per-unit rows, which move far more.** They are the *population* half, and for
NYC the population question is already **CLOSED NEGATIVE, twice** — nyiso-201 (membership:
Astoria 8906 is **0 of 18** zero-cells, the maximum distance from qualifying) and nyiso-203
(basis: a clean negative, sound as built). Re-opening it here would be re-testing an
adjudicated cell (rule 30(a) DO-NOT-REDO). The value below is **read off committed source,
declared in this document before the solve, and NEVER swept against the gates** — selecting
among the four rows by which one makes a criterion move is precisely the fitted-mechanism
selection rule 1 `[R-STRUCT]` forbids.

**No `ScenarioConfig` field is added.** This is an artifact edit, the same channel as
nyiso-140's Long_Island membership correction and the keeper's own 2019–2022 retiree window,
so it carries no flag and no cache-key delta. Rule 24 `[R-REGISTRY]` is satisfied by the CSV
itself being the registry.

**Rule 21 `[R-DOF]`.** Unlike nyiso-140 — where the basis-matched value (0.2666) and the
frozen one (0.2620) agreed, so the correction was membership-only at **zero** DOF — this one
**MOVES the coefficient**. It is therefore a ledgered free parameter whose identification
source is *"cool-day when-available CF p25, fleet aggregate, hourly grain, CAMPD 2023–2025 +
guard-corrected outage extract; owner ruling 2026-09-10"* — a measured source, not a residual.
It will be reported at full magnitude on any determination basis it reaches.

---

## 2. PHASE 0 — the LP-input footprint, measured (ZERO LP)

`scripts/probes/_nyiso226_nyc_base_screen_phase0.py`, record
`results/calibration/_nyiso226_nyc_base_phase0.json`. Two `run_year(fleet_only=True)`
rebuilds per year on the keeper's own `meta.json` recipe — frozen vs re-based — differenced
at the `min_gen` array. **No solve, no price, no metric, no residual was opened.**

| year | Δ`min_gen` (TWh removed) | rows touched | groups | plants | hours | ratio on every touched cell |
|---|---|---|---|---|---|---|
| **2023** | **+0.151070** | 24 / 870 | `ST_GAS` | 2490, 2500, 8906 | 8760 | 0.0497600 |
| 2024 | +0.083521 | 24 / 867 | `ST_GAS` | 2490, 2500, 8906 | 8760 | 0.0497600 |
| 2025 | +0.070144 | 24 / 867 | `ST_GAS` | 2490, 2500, 8906 | 8760 | 0.0497600 |

Three things this establishes before a single LP column is built:

1. **The identity holds exactly.** Every touched cell moves by the ratio
   `1 − 0.16629202320362052/0.175 = 0.04976003…`, min and max identical to 6 dp — which is
   the only thing a `pro_rata` coefficient change is entitled to assert.
2. **The footprint is CONFINED at the input layer.** 24 rows of ~870, all `ST_GAS`, all three
   NYC plants and no others. Nothing outside the limb's own class and zone moves.
3. **The screen year is 2023**, by a factor of 1.81× over 2024 and 2.15× over 2025.

**The screen year is named on the mechanism's OWN measured footprint and nothing else.**
It is `argmax` over years of |Δ`min_gen`| — an LP-*input* quantity computed with no metric
file open. It is **not** the year with the largest price or volume residual, which is the
choice rule 29 exists to forbid.

---

## 3. The PRE-SOLVE PREDICTION the gates test

From the control's own committed `legitimacy_diagnostics.json` D-4 `unit-conduct` rows for
`reliability_floor × ST_GAS`, 2023 (energy dispatched **at a binding floor**):

| NYC plant | binding hours | floored TWh |
|---|---|---|
| 2490 Arthur Kill | 3,247 | 0.3284 |
| 8906 Astoria | 5,551 | 0.2397 |
| 2500 Ravenswood | — (no row: never binding) | 0.0000 |
| **NYC total** | | **0.5681** |

In a binding hour dispatch *is* `min_gen`, so to first order the arm's ST_GAS energy falls by

> **0.049760 × 0.5681 TWh = 0.02827 TWh**, i.e. **0.288 %** of the control's 9.809682 TWh.

Control 2023, from the committed keeper sidecar `hourly/class_hourly_2023.parquet`:
**ST_GAS 9.809682 TWh**, system total **148.3100 TWh**.
(Total NYC floor energy 2023 = 0.151070/0.049760 = **3.0360 TWh**, of which **18.7 %** binds.)

---

## 4. THE SCREEN GATES — pre-registered, STRUCTURAL, STOP-ONLY

**None of these reads a residual, a price error, or a criterion delta as its pass condition.**
A screen that asked "did C3a improve" would be the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, done one year at a time. **These gates may kill the arm; they can never
promote it, and clearing them is not evidence the mechanism is right — only that it does what
its own arithmetic says.**

| id | gate | STOP condition |
|---|---|---|
| **S1** | **DIRECTION.** Removing a floor can only free the floored unit downward. | Arm 2023 `ST_GAS` ≥ control 9.809682 TWh, or `|Δ|` < 0.001 TWh (inert ⇒ the D-4 binding accounting that predicted the response is wrong) |
| **S2** | **MAGNITUDE.** ΔST_GAS ∈ **[−0.0848, −0.0071] TWh** — ¼× to 3× the 0.02827 first-order prediction | outside that band. Below ¼×: the mechanism is not doing what §3 says. Above 3×: the response is a redispatch cascade the mechanism does not claim. |
| **S3** | **CONFINEMENT.** (a) arm system total within 0.001 TWh of 148.3100 (energy balance — load is untouched); (b) `ST_GAS` is the largest-magnitude FALLING class; (c) no class outside `ST_GAS` falls by more than `|ΔST_GAS|` | any of (a)–(c) violated ⇒ the artifact edit reaches beyond the 24 rows §2 says it touches |
| **S4** | **NO LOAD-BEARING FLIP.** Scored **in the parent** on the arm's 2023 leg: none of C1 / C2 / C3a / C3b flips PASS → FAIL against the control | any such flip |

**S4 is a GUARD, not the screen's content, and its power is low at this magnitude** — a
0.028 TWh move on a 148 TWh system is unlikely to flip anything either way. Said plainly here
so that S4 clearing is never later quoted as evidence the change is good. **S1–S3 are the
screen.**

**Outcome routing.** All four clear ⇒ the arm has NOT been promoted and NOT been shown
beneficial; it has earned the full `--year 2023 2024 2025` span (rule 16 `[R-ALLYEARS]`), one
bundle, per-year shards. Any STOP ⇒ the arm dies here, the remaining years are never spent,
and the kill is the session's reported result.

---

## 5. G-DRIFT — the code-level drift audit (rule 29(b), ZERO LP, NO CONTROL SOLVE)

`git diff da2e7076 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
(control `nyiso_fuelvintage_A`, `git_sha` `da2e7076`). **22 files.** Every hunk on the
backcast path is **INERT for NYISO**:

| file(s) | classification |
|---|---|
| `config/scenarios.py` | six new fields (`caiso_dsw_lateevening_clean`, `spp_curtailment_ceiling`, `spp_curtail_depth_wind`, `nyiso_hub_gap_month_level`, `nyiso_total_east_cutset_ttc`, `ercot_ep_gas_basis_receipts_fallback`) — **all default-off and all VERIFIED ABSENT from the keeper recipe** (checked structurally against `meta.json`, not by eye) |
| `pipeline/ttc.py` | the NYISO cutset-envelope branch, gated `config.nyiso_total_east_cutset_ttc` — **default off, absent from the recipe**; off the flag the table selected and the log text are the pre-change ones |
| `data/fuel/hubs.py` | the NYISO `nyiso_hub_gap_month_level` gate — **default off, absent from the recipe** |
| `config/constants.py` | one NEW name, `NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH`, reachable only through the above flag. No pre-existing name changed — `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`, the only other NYISO-bearing surface in the diff, is **byte-identical** at both revisions (sha `c9864249edf74fa0`) |
| `config/solve_surface_declared.py` | two fingerprint **declarations** appended at their current values (D79 drop) — cache-key bookkeeping, not the LP |
| `data/outages.py` | 3+ **PJM** plant ids added to the ST_GAS peaker registry; **no NYISO plant** |
| `data/renewables.py`, `data/curtailment_share.py`, `runner.py` | gated `iso == "SPP"` |
| `data/fuel/basis/ercot.py` | ERCOT branch |
| `model/interchange/{__init__,caiso,spec}.py` | CAISO branch |
| `scripts/run_calibration*.py`, `scripts/lib/{holdout_policy,forecast_parity_registry,spp63_g5}.py` | SPP/CAISO CLI surface and the `[R-HOLDOUT]` removal; not solve-affecting |
| `data/raw/_validation-source/{actual_lmp,calibration_reference}.json` | **scoring**-side, and the **NYISO subtrees are byte-identical at both revisions** (compared structurally, sha `0cead87c1f10834f`; zero differing NYISO paths) — so the control's committed bands are still the bands a fresh score produces |
| `data/raw/reference/spp_curtailment_share.csv`, `MISO_2020_renewable_capacity.csv` | other ISOs' artifacts |

**ALL HUNKS INERT ⇒ G-CTRL form 4 is valid, the committed keeper bundle IS the control, and
NO CONTROL SOLVE IS SPENT.**

---

## 6. Execution (rule 32 `[R-SHARD]`)

- **The parent** does phase 0, this PRECOMMIT, the SHA pin, then gate evaluation, scoring,
  composition and the promotion question. **The parent runs no LP.**
- **One shard, one year, ≤ 20 min:** 2023, `replay_keeper.py results/calibration/nyiso_fuelvintage_A
  --years 2023 --out-dir results/calibration/nyiso226_screen_2023`, with the **CSV coefficient
  edited to 0.16629202320362052 before the solve**, pinned to this document's 40-char SHA, on
  its own branch, committing only its own bundle path.
- **The shard CAN score nothing and is not asked to.** It reports raw model prices, class TWh,
  the system total and `legitimacy_diagnostics`; **all scoring is the parent's** (rule 32(d)).
  *(Correction to the standing handoff text: `curate_lmp.py`'s `KeyError: 'MGHG'` is a **CAISO**
  file defect, and it is avoidable — pointing `curate_lmp.main()` at a raw dir containing only
  the `NYISO/` subtree curates the four NYISO partitions cleanly. The parent did exactly that
  this session and can therefore score C3a/C3b itself. No shard repairs anything.)*
- **Rule 31 `[R-RETAIN]` / rule 29(c):** `results/calibration/nyiso226_*/` is added to
  `.gitignore` in this same commit, **before** the bundle exists. That — not `rm` — is what
  discharges delete-before-merge. **Nothing is deleted until the owner has ruled on promotion.**

---

## 7. Governance

- **Rule 1 `[R-STRUCT]`** — structure decides this. The value is set ex ante from committed
  source, declared here before the solve, and never swept; the gates are structural and
  STOP-only. `authorized_price_tuning` = **NONE** (no offer-curve band multiplier is touched).
- **Rule 13 `[R-MEASURED]`** — the coefficient is a measured physical/market input with a
  forward analogue: the same cool-day when-available CF p25 regenerates for a forward year
  from that year's CAMPD vintage and responds to changed fleet conduct. No outcome is pinned.
- **Rule 14 `[R-ACCURATE]`** — the basis. The hourly-grain statistic is the accurate one for a
  coefficient applied per unit-hour; rule 14's misalignment exception cannot excuse the daily
  mean, because both are the same measurement on the same population, differing only in the
  aggregation the application already fixes.
- **Rule 16 `[R-ALLYEARS]`** — the screen bundle is a throwaway diagnostic probe. Never
  registered, never a keeper, never quoted as a keeper number; 2023 is re-solved inside the
  full bundle if the span is earned.
- **Rule 19 `[R-ONE-MECH]`** — nothing is stacked. The one coefficient is REPLACED. The NYC
  evening ramp limbs (`NYC_ST_ev`) are `enabled=False` in the keeper recipe, so the persistent
  base is the sole mechanism on this class/zone and there is no second floor to reconcile.
- **Rule 21 `[R-DOF]`** — §1: a ledgered free parameter, measured source, reported at full
  magnitude.
- **Rule 23 `[R-FROZEN-DERIVE]`** — **no source-data trigger, and none is claimed.** §0.
- **Rule 25 `[R-ISO-SCOPE]`** — NYISO's own CSV, NYISO's own data. Nothing transferred.
- **Rule 30 `[R-MECH-MATRIX]`** — no new `ScenarioConfig` field, so no new matrix row. The
  NYISO shard is re-stamped in the session that reports the screen's outcome, kill included.

