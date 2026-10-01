# PRECOMMIT — SPP-58: the wind gross-up the LP cannot re-curtail (build + screen)

**Session:** ercot-266, running the SPP lane. **Date:** 2026-09-10.
**Branch:** `claude/session-me7wt5`. **Lane:** SPP-DESK.
**Keeper under test:** `2026-09-09-spp-52a-fossil-offer` (bundle
`results/calibration/spp52a_fossil93`). **Nothing solved at the time of writing.**

Supersedes `PRECOMMIT-spp-58-wind-curtailment-ceiling-2026-09-09.md`, which was written
against **keeper 4** (`spp-51c-oversupply-curtailment`) before SPP-52a was promoted. That
document's object, rule-28 clearance and screen-year reasoning stand; **every number in it
has been re-measured here against the CURRENT keeper**, and its §5 gates are re-cut because
the incumbent's failing-criterion set has changed (SPP-52a closed `price_mean` and
`price_shape`). Written and pushed BEFORE any arm is solved (rule 29 `[R-SCREEN]`).

---

## 1. Why this lane, and what has changed since the 2026-09-09 PRECOMMIT

SPP reads **NOT-YET**. It is now failing on **two** criteria, not the four the predecessor
PRECOMMIT recorded — SPP-52a's authorized offer-curve level move closed `price_mean` and
`price_shape`:

| criterion | tier | status | detail |
|---|---|---|---|
| `fuelmix` (C1) | load-bearing | **FAIL** | **2024 `ST_GAS` −8.13 TWh, share −2.8 pp — the SINGLE failing row in the whole 3-year table** |
| `price_tail` (C3c) | supporting | FAIL | 0 / 4 / 2 h vs 42 / 59 / 68 h > $200 |
| C2, C3a, C3b, C4, C6, C8 | — | PASS | — |

**C3c is the only LEDGERABLE criterion, and it is now the only other one.** Under rubric
v3.3 a ledgered C3c is non-downgrading when it is the lone failure and governance passes.
**So SPP is exactly one row from CALIBRATED**, and that row is the object of this lane.
That is stated as the stake, not as a gate: nothing below is scored on whether C1-2024
passes (§5).

**Rule 28 `[R-MECH-MATRIX]` clearance.** `vre_reference_rate_curtailment_grossup` reads
**`U`** in `docs/codebase-site/data/mechanism-matrix/SPP.js` — footprint measured at zero LP
by SPP-51b, **no arm ever solved, no verdict minted**. Nothing here re-tests an `R`/`I`/`G`
cell. `vre_curtailment_oversupply_allocation` reads `K` and is armed in the keeper; §3 states
how this mechanism supersedes rather than stacks on it.

## 2. PHASE 0 — the object, re-measured on the CURRENT keeper's committed artifacts

Zero LP. `renewable_bound_provenance("SPP", y, "wind")` = **`forecast_uncurtailed`** in all
three years: the delivered EIA-930 profile grossed up by SPP's frozen measured reference
rate (**9.65 %**, source year 2025), a construction whose own stated precondition
(`data/renewables.py`) is *"real headroom, **endogenously re-curtailed**"*.

**It is not re-curtailed.** Reconstructing the keeper's own wind CF bound at HEAD from its
committed `run_config.json` and differencing against its committed
`hourly/class_hourly_<year>.parquet` dispatch:

| year | wind potential (bound) | wind dispatch | re-curtailed | **re-curtailment %** | hours at the bound |
|---|---:|---:|---:|---:|---:|
| 2023 | 114.055 TWh | 113.757 | 0.298 | **0.261 %** | 65.0 % |
| 2024 | 120.992 TWh | 120.723 | 0.270 | **0.223 %** | 97.6 % |
| 2025 | 122.255 TWh | 122.043 | 0.212 | **0.174 %** | 65.8 % |

**A 40–60× miss on the mechanism's own precondition** against the 9.65 % rate the gross-up
applies, and against SPP's own published year-specific shares (8.49 / 10.56 / 9.90 %). Note
this is measured on the keeper that ALREADY arms `vre_curtailment_oversupply_allocation`:
the water-fill moved the headroom to the low-net-load hours, and the LP took it anyway.

It lands as energy. SPP 2024, against EIA-930: wind **+11.4 TWh** (120.723 vs 109.317),
thermal short by ~12.3 TWh, of which the C1 failing row `ST_GAS` is **−8.13 TWh**.

**THE CAUSE IS WRITTEN IN THIS REPO'S OWN CODE.** `renewables.py` explains why NYISO is
kept OUT of `_UNCURTAILED_FALLBACK_ISOS`: *"a NYCA-wide annual rate exists but is the wrong
instrument — **its curtailment is locally driven and the reduced network can't re-curtail a
gross-up**"*. SPP is IN that set and its curtailment is locally driven in exactly the same
way (SPS / Texas-Panhandle and western Kansas / Oklahoma pockets). The 2-zone reduction
(`SPP-North` / `SPP-South`, one 3,400 MW link) collapses those constraints, so the LP has no
mechanism to spill wind bid in at its −$26/MWh PTC floor.

## 3. THE MECHANISM — SPP's own instance of an ERCOT-precedented structure

```
ceiling_frac(t) = 1 − depth × congestion_share(net_load_decile(t), hour_of_day(t), season(t))
```

applied to the **wind** CF upper bound on both SPP zones.
`ScenarioConfig.spp_curtailment_ceiling` (default **False**),
`spp_curtail_depth_wind` (0.288137). New code:
`scripts/data/derive_spp_curtailment_share.py`,
`market_sim.data.curtailment_share.spp_curtail_multipliers`, one guarded block each in
`scripts/run_calibration.py` (backcast leg) and `runner.py` (forecast leg).

**Rule 25 `[R-ISO-SCOPE]`: NOTHING TRANSFERS.** ERCOT's depth (0.1004), its share table and
its West/Panhandle corridor attribution stay ERCOT's. SPP enters as `U` and derives its own
parameters from its own market:

- **SHAPE — from SPP's own RTBM binding-constraint archive**
  (`data/raw/spp-binding-constraints`, landed 2026-09-08; the predecessor PRECOMMIT recorded
  it token-blocked, and **that blocker is gone** — 69 MB, 2023–2025 complete, tracked).
  Binned on the same `(net-load decile × hour-of-day × season)` axis the ERCOT reader uses,
  from measured binding incidence ONLY — never a curtailment volume, never a price, never a
  residual. **866 of 960 cells populated.**

  **Why a binding COUNT and not a binding FRACTION, decided before any depth was computed:**
  the "does anything bind this interval" union SATURATES in SPP — **91.0 %** of 2024's
  5-minute intervals carry at least one binding constraint — so a fraction share is flat and
  encodes no shape. The *number* of simultaneously binding constraints discriminates, with
  the physically right sign. Measured, share by net-load decile (0 = lowest net load =
  highest wind):

  | decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | share | **0.488** | 0.434 | 0.384 | 0.321 | 0.267 | 0.219 | 0.199 | 0.198 | 0.204 | 0.226 |

  Monotone-falling 0→7 (2.5× range) with a mild rise at 8–9 — load-driven peak congestion,
  physically real and left in rather than smoothed out. Hour-of-day peaks overnight
  (h20–h23 ≈ 0.34) and troughs at h08 (0.24): the classic SPP overnight wind-export
  signature.

  **CLOCK, and it is a real trap.** The archive's `Interval` column is SPP local time WITH
  daylight saving (GMT offset 6 h in January, 5 h in July) while the model dispatches on
  FIXED CST. Every timestamp in the derive is therefore rebuilt from `GMTIntervalEnd` at a
  constant −6 h (less the 5-minute interval width), and 29 February is dropped. This is the
  same defect repaired for SPP's LMP sidecar in commit `86e45462`; deriving off `Interval`
  would shift the whole summer half of the table by one hour.

- **LEVEL (`depth`) — from SPP's published measured curtailment MW**
  (`data/raw/spp-hsl/spp_wind_curtailment_annual.csv`, SPP MMU ASOM, both legs metered), the
  same identification ERCOT's depth uses. **ONE value across every scored year** (rule 1
  `[R-STRUCT]` condition (b) discipline applied to a derived coefficient): the
  energy-weighted value that centres all three years at once.

  | year | published share | weighted-mean share | implied depth |
  |---|---:|---:|---:|
  | 2023 | 8.49 % | 0.33104 | 0.25646 |
  | 2024 | 10.56 % | 0.33640 | 0.31391 |
  | 2025 | 9.90 % | 0.33942 | 0.29168 |
  | **pooled** | — | — | **0.288137** |

  **Reported at full magnitude, not minimised: the per-year spread is 19.9 % of the pooled
  value.** That is looser than ERCOT's "stable structural constant" claim and is not being
  dressed up as one. What IS tight is the SHAPE: the weighted-mean share moves only
  0.331 → 0.339 across three years (2.5 %), so essentially all of the spread is SPP's
  published curtailment MW moving year to year (1,097 → 1,483 → 1,382) — which is exactly how
  a depth × shape decomposition should behave, and is why one pooled depth is the honest
  choice rather than three fitted ones.

  **Zero free parameters (rule 21 `[R-DOF]`).** The table's rescale onto (0, 1] by its own
  maximum cell carries no leverage: depth is centred on the published MW *after* the rescale,
  so any monotone rescaling of the shape is absorbed exactly by depth and only the table's
  relative structure reaches the LP. Neither depth nor the incidence definition is swept
  against any gate — both were fixed before the first solve, in this document.

- **RULE 19 `[R-ONE-MECH]`, ENFORCED IN CODE.** The ceiling is the third answer to "where
  does the measured curtailment land", after the flat gross-up and SPP-51c's oversupply
  water-fill. It **REPLACES** the water-fill: `data/renewables.py` skips
  `_oversupply_uncurtailed_cf` whenever `spp_curtailment_ceiling` is armed, so the two can
  never both be live in one solve whatever a recipe asks for. The arm's basis reverts to the
  flat gross-up and the ceiling alone decides both where curtailment falls and how much of it
  binds. Measured: the swap is **energy-neutral on the basis** (annual potential identical to
  the milli-TWh in all three years — the water-fill only ever moved hours), so every TWh the
  arm removes is the ceiling's and none of it is the disarming.

- **SOLAR TAKES NO CEILING.** SPP's solar bound is `delivered_pinned` — it carries no
  gross-up headroom — so a solar ceiling would curtail energy the market actually delivered.
  The published series the depth is centred on is wind-only for 2023/2024 in any case (the
  2025 edition's total-VER basis puts solar at 0.73 % of curtailments).

## 4. SCREEN YEAR, NAMED NOW AND ON FOOTPRINT ONLY — **2024**

Rule 29(a). The mechanism's own measured driver quantity, in SPP's published data and its own
congestion archive, neither of which is a model residual:

| year | published curtailment | measured share | binding-row rate |
|---|---:|---:|---:|
| 2023 | 1,097 MW | 8.49 % | 11.91 % |
| **2024** | **1,483 MW** | **10.56 %** | **12.35 %** |
| 2025 | 1,382 MW | 9.90 % | 9.24 % |

**2024 is the largest on every leg of the mechanism's own footprint.** **DECLARED HONESTLY
AND UNCHANGED FROM THE PREDECESSOR PRECOMMIT: 2024 is also the C1 failing year, so footprint
and residual coincide. The selection basis is the footprint** — SPP's MMU published 1,483 MW
independently of this model — and had the two diverged the footprint would still have chosen.
Note the *model-side* removed-TWh is largest in 2025 (12.023 vs 11.766); that is a fleet-size
artefact and is explicitly NOT the selection basis, because it is a model quantity.

## 5. PRE-REGISTERED GATES — STOP gates, structural, none on the target residual

The screen **may kill the arm and may never promote it.** It contributes nothing to a
determination. **No gate below reads C1, C3a or any other criterion in the direction of
"did it improve"** — a screen that asks "did C1-2024 get better" is exactly the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at a time.

- **G-1 (identity, zero-LP) — ALREADY MEASURED, PASS.** Off the flag the control's renewable
  arrays reproduce exactly; the arm changes only the wind bound; the solar multiplier array
  is exactly 1.0 and solar CF is `array_equal` to the control's in all three years.
- **G-2 (reach) — the ceiling removes 8–16 TWh of the 2024 wind bound.** Below 8 the
  mechanism is inert and the arm dies; above 16 it over-reaches and the arm dies. **Pre-solve
  arithmetic: 11.766 TWh (9.72 %), bound 120.992 → 109.226 TWh.** The gate on the SOLVE is
  that realised 2024 wind DISPATCH falls by 8–16 TWh — i.e. the LP actually spends the
  ceiling instead of routing around it.
- **G-3 (allocation):** the removed wind is concentrated, not spread — the lowest-net-load
  decile carries a strictly larger share of the reduction than a flat 9.72 % cut implies. A
  flat reduction is the defect wearing a different hat and FAILS.
- **G-4 (no new forcing):** slack and dump stay exactly 0.0, and no `min_gen` floor gains
  binding hours. Displaced wind must be picked up by economic dispatch, not by forcing.
- **G-5 (no load-bearing regression):** no non-target load-bearing criterion (C2, C3a, C3b,
  C4) and no protective criterion (C6, C8) flips PASS → FAIL in 2024.

**Sealed predictions** (scored in the RESULT whatever they do, and NONE of them is a gate):

- **P1** 2024 wind dispatch lands in 108–113 TWh; `ST_GAS` rises and closes most of its
  −8.13 TWh.
- **P2** C3a-2024 moves UP (thermal displacing zero-cost wind at mid load should raise
  prices). **P2 is the prediction most likely to be wrong** — SPP-52a has just tuned the
  fossil level DOWN 7 % to land C3a at −0.61 % in 2024, so a price rise here could push C3a
  out the other side. It is stated before the solve precisely for that reason, and if it
  happens it is a FINDING, not a licence to retune the offer curve.
- **P3** C3c does not improve materially — SPP-55 adjudicated the tail a 5-minute object no
  hourly lever reaches. A large C3c move is a red flag to investigate, not a win.
- **P4** the arm is NOT automatically a keeper. A structurally-correct mechanism stays in
  even if gates regress (rule 1 `[R-STRUCT]`), and **the owner decides promotion** (rule 31
  `[R-RETAIN]`).

## 6. G-DRIFT (rule 29(b)) — recorded BEFORE the arm is solved

**The keeper's own `git_sha` `c1393878` is UNREACHABLE** — it is a solve-time sha on a branch
auto-merged and deleted, and `git fetch origin c1393878` returns "couldn't find remote ref".
Declared rather than worked around: the audit base is substituted with **`d77c184e`**, the
commit that registered the keeper's bundle on `main` ("SPP-52a: register the −7 % fossil
offer-curve level arm"), which is the earliest reachable commit that provably contains the
keeper's solve state. Diff base `d77c184e` → `origin/main` (`699be3a1`) over
`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`, **every changed file classified**:

| changed path | verdict | reason |
|---|---|---|
| `model/interchange/spec.py` | **INERT** | MISO seam ladder / import tranches re-derived on the repaired SPP clock. `IMPORT_ZONE` carries **no SPP key** and every one of SPP's 42 seam/interchange flags is `False` in the keeper recipe — the values are applied in MISO's branch, merely *anchored* to an SPP price. |
| `data/outages.py` | **INERT** | 11 plant ids added to `ST_GAS_PEAKER_PLANTS` (consumed ungated in `offer_curves.py`, so this needed a real check). All 11 are EIA-860 `Balancing Authority Code = PJM` (Joliet 9/29, Edge Moor, McKee Run, Chalk Point, Martins Creek, Montour, Eddystone, Clinch River, Yorktown, Archbald). **Zero overlap with SPP's 828 `SWPP` plants.** |
| `data/fleet/eia860.py` | **INERT** | `_PARTIAL_EXIT_WINDOW_START` 2023 → 2019 is read only under `partial_plant_exit_carry`, which is **`False`** in the keeper recipe. |
| `data/fuel/{__init__,resolve,trajectories}.py`, `data/fuel/electric_power.py`, `data/raw/reference/iso-gas-capacity-state-weights.csv` | **INERT** | all gated on `gas_electric_power_monthly_level`, default `False` and **absent** from the keeper recipe. |
| `data/fuel/basis/ercot.py` | **INERT** | ERCOT branch. |
| `config/constants.py` | **INERT** | one new **ERCOT-only** constant (`ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU`); the `NUCLEAR_MONTHLY_CF_BY_YEAR` hunks are **comment-only** (the diff text states the committed values are byte-unchanged and `--check` still passes) and touch no SPP key. |
| `config/scenarios.py` | **INERT** | three new fields — `gas_electric_power_monthly_level`, `ercot_ep_gas_basis_corroborated`, `ercot_ep_gas_basis_receipts_fallback` — **all default `False`**, none in the keeper recipe. |
| `config/solve_surface_declared.py` | **INERT** | two entries added (ERCOT + NYISO). **SPP's declared surface value is unchanged**, so the capx-D79 fingerprint does not re-key SPP. |
| `scripts/lib/holdout_policy.py`, `scripts/run_calibration{,_full}.py` | **INERT** | the `[R-HOLDOUT]` removal — authorization/harness, not solve physics. |
| `data/raw/_validation-source/MISO_2020_renewable_capacity.csv` | **INERT** | MISO. |
| `data/raw/_validation-source/{actual_lmp,calibration_reference}.json` | **NOT SOLVE PATH** | these are the BENCH. They cannot change an LP — but they DO mean the control must be **re-scored at HEAD**, which is what §7 does. |

**ALL SOLVE-PATH HUNKS ARE INERT ⇒ G-CTRL form 4 is VALID and the keeper's committed bundle
IS the control. NO CONTROL SOLVE IS SPENT.**

## 7. The control numbers, and how they are formed

The bench moved between the keeper's registration and HEAD, so the keeper's *committed*
`metrics.json` is not on the same bench as the arm will be. The control is therefore the
keeper's committed **artifacts** re-scored at HEAD — **zero LP, scorer only, in the parent**
(rule 32(a)) — and the arm is differenced against that, never against the stale printed
numbers. Both legs of every comparison in the RESULT are on one bench.

## 8. Governance

- **Rule 32 `[R-SHARD]`:** the parent solves nothing. The screen runs in ONE shard, SPP 2024,
  pinned to this PRECOMMIT's full 40-char SHA, own `--out-dir`, own branch, pushing its slim
  artifacts and a METRICS json to `results/shard-staging/spp58/2024/` per
  `docs/handoffs/SHARD-ARTIFACT-HANDOFF-BLOCK.md`, including `system.parquet`,
  `dispatch/2024_P1*.parquet` and `results/calibration/_shared/SPP/*.parquet` (the ercot-265
  correction — `render_calibration_html.build_payload` reads all three and the parent cannot
  register without them).
- **Rule 16 `[R-ALLYEARS]` / rule 29(2):** the screen bundle is a throwaway diagnostic probe,
  never registered, never a keeper, never quoted as a keeper number. If it clears, the full
  span 2023 · 2024 · 2025 is solved as three per-year shards (rule 32(b)) and composed into
  **ONE** bundle — 2024 included, re-solved rather than promoted out of the screen.
- **Rule 31 `[R-RETAIN]`:** every bundle family is `.gitignore`d at the moment it is written,
  nothing is `rm`'d, and the promotion question goes to the owner explicitly before the
  session ends.
- **Rule 22:** 2023/2024/2025 are training-tier years. `[R-HOLDOUT]` was removed 2026-09-09,
  so no marker and no `--holdout-authorized` is involved either way.
- **Rule 28:** `vre_reference_rate_curtailment_grossup` and the new
  `spp_curtailment_ceiling` cell are stamped in **SPP's own shard** in this session, whatever
  the outcome, and the new `ScenarioConfig` field gets its matrix row plus a cell line in
  every ISO shard in the same PR (duty (c)).
- **Rule 27 `[R-PUSH]`:** this session is Opus and edits `src/`; every push of a ≥300-line
  file is blob-verified.
