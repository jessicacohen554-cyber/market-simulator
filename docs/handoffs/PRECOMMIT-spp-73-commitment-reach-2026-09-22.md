# PRECOMMIT — SPP-73, lever (b) COMMITMENT REACH: why does a correct requirement price at $24?

**Zero LP. Pushed before any DA-in-tail, CAMPD-state or fleet-parameter number was read.**
Base: `origin/main` @ `f8188a1e939abef257a95a19e33f18ab7e812956`. DATA PROFILE: spp.
Charter: `docs/RESULT-xiso-stack-climb-attribution-2026-09-22.md` §10 (commitment reach ranked
first). Predecessor: `docs/handoffs/RESULT-spp-72-demand-tightness-2026-09-22.md` (demand
EXONERATED in substance; not re-opened here).

Already read before this file was written, and therefore NOT pre-registered as a finding:
- step 1 re-verification: `calibration_verdict.py --run-id 2026-09-22-spp-71-rung-ensemble` →
  NOT-YET; C3a 2020 FAIL; C3b 2020 / 2021 / 2022 = 0.267 / 0.243 / 0.208 FAIL; C3c CAVEAT
  (ledgered). Matches the brief.
- the code path of the brief's (c) (`commitment.py`, `pipeline/solve.py`), read to design M4.
- the SOURCE SURVEY of the brief's (b), read to design M3: SPP's public `historical-offers`
  product (`portal.spp.org/file-browser-api/?fsName=historical-offers`, 2014→, 90-day lag,
  masked RCodes) carries **energy price/MW pairs only** (header read from
  `2020/02/DA-ENERGY-OFFERS-202002170100.csv`: `CPTHourEnd,GMTHourEnd,RCode,MW1,Price1…MW10,Price10`)
  — no start-up, no-load, min-run or min-down field. The MMU ASOM (2023–2025 transcribed,
  `data/raw/spp-planning/transcriptions/`) publishes fuel-level FLEET AVERAGES of self-reported
  physical parameters (Figure 3-6: econ min/max, cold/hot start time, min run time, ramp) and
  aggregate make-whole $; no per-unit or per-class start-up cost.

## 1. Hour sets (reused from SPP-72 exactly)

- `H_top(y)`: top-88 hours by MEASURED `rt` in `data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`
  (finite values only, `np.argsort(-rt, kind="stable")[:88]`), on the fixed-CST model clock via
  `scripts/probes/_spp72_demand_tightness.py::model_clock_index` (imported, not re-written).
- `H_ctrl(y)`: requirement-matched control. `R` = measured thermal requirement = EIA-930 SWPP
  load + TI − wind − solar (`SWPP_region.parquet` D/TI via SPP-72's `measured_series`;
  `SWPP_fueltype.parquet` WND/SUN on the same clock, trap (f) guard: any hour > 40,000 MW WND or
  > 20,000 MW SUN is set NaN and interpolated). Percentile of `R` within year, 5-pt bins. Control
  = hours NOT in the top-10 % by `rt`, re-weighted per bin to `H_top`'s bin histogram (bins
  with no control hours dropped from both sides and counted).
- Years: all seven reported; verdicts on the rung years 2019–2022, 2020 primary.

## 2. M1 — THE DISCRIMINATOR: the DA bound (decides V1)

SPP's day-ahead market is a security-constrained **unit commitment** that clears hourly on
participants' real start-up, no-load, min-run and min-down offers and real energy offers. It
is therefore the empirical **upper bound** on what any hourly commitment representation could
price in `H_top`. It is a **generous** bound (DA also carries virtual bids, forecast load and any
DA risk premium), so a verdict that a gap is out of reach even of DA is robust.

- Model price: P1 zonal price from the committed `hourly/system_<y>.parquet`, demand-weighted
  across zones (rung bundle 2019–2022, span 2023–2025).
- Over `H_top`: `med_RT`, `med_DA`, `med_MOD`.
- **φ_y = (med_DA − med_MOD) / (med_RT − med_MOD)** — numerator and denominator reported.
- **V1 — commitment reach REAL** iff φ_2020 ≥ 0.5 AND φ ≥ 0.5 in ≥ 2 of {2019, 2021, 2022}.
  **NOT REAL** iff φ_2020 < 0.5 AND φ < 0.5 in ≥ 2 of those three. Otherwise **MIXED**.

**M1b — row reach.** Score the measured DA series AS IF IT WERE THE MODEL, with the scorer's own
arithmetic and the COMMITTED actual (`frontend/data/backcast/bench/SPP/<y>.json.gz` →
`bench.avgLMP.rt` / `rt_mon`, not recomputed): C3a = demand-weighted DA annual mean (weights =
the model's own zonal demand summed, same as the model side) vs `rt`; C3b = `_nrmse` of the
demand-weighted DA monthly means vs `rt_mon`. Robustness: equal-hour DA. For each of the four
failing rows: **DA FAILS it ⇒ UNREACHABLE by any hourly commitment representation** (a real SCUC
with measured commitment costs fails it too). DA PASSES ⇒ reachable in principle by *some*
hourly object — not necessarily commitment.

**M1c — C3a 2020 decomposition** (equal-hour, hub series): `mean(m − a)` split into the
`H_top` contribution and the rest, `(1/N)Σ_top` + `(1/N)Σ_rest`.

## 3. M2 — commitment STATE (the brief's (a))

CAMPD hourly units whose `facilityId` is an EIA-860 plant with Balancing Authority Code SWPP
(trap (d): BA first, state files second). Gas class from the plant's EIA-860 operable
generators: prime mover GT/IC → **CT**; CT/CA/CS → **CC**; ST with gas energy source → **ST_GAS**;
mixed plants take the unit's CAMPD `unitType` (combustion turbine / combined cycle / boiler).
Online = `opTime > 0`. Clock: CAMPD `date+hour` is local STANDARD time; NM/MT/WY facilities
shifted +1 h to CST, all others taken as CST (declared imperfection; ±1 h robustness read on
s2 only). Model classes: CT = CT_PEAKER (+ CT_CHP reported separately), CC = CC_REGULAR +
CC_CHP, ST_GAS = ST_GAS, from the committed `class_hourly_<y>.parquet` (P1).

Per class, per year:
- **s1**: mean gross MW over `H_top` / over `H_ctrl` → `ρ_meas`; the same from class_hourly →
  `ρ_mod`. Units-on counts reported beside MW.
- **s2**: start-into-spike share = fraction of units online in `h` that were offline in `h−1` or
  `h−2`, `H_top` vs `H_ctrl`.
- **s3**: share of the year's hours with class output > 0, measured vs model.
- **s4**: annual mean class MW, measured vs model.
- **V2 — commitment-state signature present** in a year iff `ρ_meas(CT) ≥ 1.5 × ρ_mod(CT)` AND
  `s2_top(CT) ≥ 2 × s2_ctrl(CT)`.

## 4. M3 — measured commitment parameters (the brief's (b))

From the survey above: **no published per-unit or per-class SPP start-up COST exists**; min-run
is published only as a fuel-level fleet average of self-reported parameters (2023–2025 ASOMs
on disk). The CAMPD run-length artifact (`campd_ct_run_lengths_SPP.csv`) is a measured
**outcome** of commitment, already adjudicated for its admissible use in
`tranche_startup_amortization` (R) and, as a commitment-state window, inadmissible under rule 13
(SPP-46 §4.1). **Pre-registered STOP: whatever M1/M2 show, no mechanism is proposed unless a
published, per-class, forward-reproducible start-up cost source is found in this session.**

## 5. M4 — can P0→P1 bite? (the brief's (c))

Read: `commitment.py` `_commitment_params` (a CAMPD-bin row with `min_run_hours <= 0` and no class
override returns `None` — never commitment-screened) and `compute_monthly_markup` (`startup ==
0.0 → continue` — zero markup); `pipeline/solve.py` P1 `mc_bid = mc_base + markup`. Verified on
the fleet: a `reconstruct_bundle_fleet` rebuild of rung 2020 counts SPP rows with
`startup_cost_per_mw > 0`, `min_run_hours > 0`, `min_down_hours > 0`, and `mc_bid − mc_base`.

## 6. Overall verdict rule

Commitment reach is **the cause** of the rung's price-shape failures iff **V1 REAL** AND **V2
present in 2020** AND **M3 finds a source**. Anything else ⇒ **NOT the cause**, and — the xiso
ranking's (a) reserve and (c) demand being closed for SPP — every hourly lever on that ranking is
exhausted for SPP, and C3a/C3b route to the RT-wedge object C3c already ledgers.

## 7. Predictions (scored in the RESULT, not moved)

| # | prediction | confidence |
|---|---|---|
| P1 | φ_2020 < 0.5 (DA median in 2020 `H_top` well below RT's) — expect 0.1–0.3 | high (SPP-29: DA > $200 in 0/42, 14/59, 0/68 RT-tail hours) |
| P2 | V1 = NOT REAL | high |
| P3 | DA-as-model FAILS C3a 2020, same sign as the model (DA mean > RT mean by > 10 %) | low |
| P4 | DA-as-model FAILS C3b in ≥ 2 of 2020/2021/2022 | low–moderate |
| P5 | ρ_meas(CT) > ρ_mod(CT) in 2020; V2 threshold met | coin-flip |
| P6 | measured CT annual mean MW 2020 ≤ 50 % of the model's CT_PEAKER 1,836 MW | moderate |
| P7 | M4 counts 0 / 0 / 0 and `mc_bid ≡ mc_base` for every row | high |
| P8 | M1c: the non-top hours carry > 100 % of C3a 2020's +gap (body too high, tail too low) | moderate |

**Which rows an hourly commitment lever could move, and which way (the brief's ask).** Any such
lever works by *raising* prices in the hours it tightens. C3a 2020 is a **+17.3 % OVER**-prediction,
so a tail-raising lever moves it **WORSE** by sign unless it also lowers the body — it cannot
close C3a 2020 on its own. C3b 2020–2022: direction ambiguous (spike months rise, but so does a
level already too high). C3c: expected untouched (sub-hourly wedge).

## 8. What this lane will not do

No `ScenarioConfig` field, no shard, no solve, no cell verdict change (nothing is tested; rule
28(b) not engaged) unless §6 fires — and §4's STOP makes that conditional on a source that the
survey did not find. Keeper 15 untouched; `build_dof_ledger --iso SPP --check` and
`audit_keepers --iso SPP` re-run at the end to prove it.
