# ERCOT 2023 summer scarcity-tail miss — RE / AS-ECRS / zonal-deliverability attribution (the ERCOT-98 lane)

**Session 2026-07-23. Keeper under test: `2026-07-22-ercot97-plant-grain-fullspan`
(NOT-YET by design; C3a −27.9 %, C3b 0.545, C3c out of band). Charter (owner handoff):
with the owner-uploaded 2023 NP6 GEO HSL data in the repo, test the three named suspects
for the 2023 summer scarcity miss — RE over-credit, AS/ECRS holdout, and West/Panhandle
deliverability — measured-comparison first (rules 1/11/13), then re-solve the keeper on
the accurate input (rule 16).**

**Verdict in one line: all three chartered suspects are REFUTED as owners of the 2023
tail miss — the model's physical balance at the missed hours is faithful to within ~1 GW
per component and reality priced NO reserve scarcity there (RTORPA p50 $1.0, PRC p50
5,765 MW) — the 135 missed hours are OFFER-driven SCED λ ($500–5,000 on the bid stack
with 5–9 GW of responsive capability standing), so the residual belongs to the
offer-formation family (the ercot57 §4 successor), not to inputs. Two real
measured-input misalignments were found and fixed on the way (the NP6 HSL swap itself,
and a 1-hour CPT→CST clock defect in the AS-plan requirement loader).**

## 0. Baseline (committed keeper sidecars vs committed actuals)

2023 actual RT tail (HB_BUSAVG hourly > $200; `frontend/data/backcast/tail/actual_tail.json`,
landed with PR #2801): **181 h** (DA 311 h). Keeper model (demand-weighted zonal price):
**51 h** — 46 of the actual 181 caught, **135 missed**, 5 phantom (all June). Model mean
hub $38.84. Missed hours by month: Aug **71**, Sep 22, Jul 11, Jun 7, shoulder 24;
by hour-of-day: 13–19 CST dominate (87 of 135). Top missed days are the early-August
heat wave — Aug 10 (8 h, the annual peak-load day), Aug 4 (7), Aug 7/8/11 (5 each) —
plus Jun 16 (5) and Sep 5/24 (4 each).

## 1. The three chartered suspects, each against measured data

### 1a. RE over-credit — REFUTED (the accurate data goes the other way)

The owner-uploaded NP6 GEO reports (NP4-742 wind / NP4-745 solar, 12 months each,
`data/raw/ercot-hsl/np6/2023/`) are now the 2023 HSL source (`build_ercot_hsl.py`
auto-prefers NP6; delivered totals match EIA-930 to −0.3 % wind / +0.03 % solar, so the
loader's footprint reconciliation is a **no-op** for every year). Solar's +13.7 % vs
EIA-923 is a 930-vs-923 scope difference (ERCOT BA telemetry vs plant survey), not an
NP6 over-count — the model's demand/renewables system of record is EIA-930, which NP6
matches.

At the 135 missed hours the keeper's RE dispatch runs **1,683 MW UNDER** the EIA-930
actual RE (model 15,092 vs actual 16,775 MW mean) — the reconciled-UMass shape
under-credited exactly there, and the NP6 swap *raises* model RE at those hours. There
is no system-wide RE over-credit to remove; the honest input adds cheap supply at the
missed hours (rule 11: kept anyway).

### 1b. AS/ECRS holdout — requirement level FAITHFUL (re-confirmed); a 1-hour clock
defect found and fixed; "under-hold" refuted as the tail owner

* **Level.** The multi-product co-opt's requirement is the measured AS plan
  (`ercot_as_plan_requirement_mw`, ASPLANNP433) minus the measured LR-RRS credit
  (~790–820 MW) and measured battery AS-award credit (~0.9–2.2 GW at the named
  evenings) — the ercot57 §2b verification stands. The 2023-09-06 "doubled plan"
  appearance in the raw archive is exact duplicate rows (the archive carries the first
  ~6 days of each month twice; the loader's mean over duplicates is correct). ERCOT's
  real plan is month×hod-stable (8/17 ≡ 8/30 in the raw data), so the loader's
  month-day-hod mapping is faithful.
* **Clock defect (fixed this session).** The loader placed CPT `(DeliveryDate,
  HourEnding)` labels directly on the fixed-CST fleet clock — one hour late for the
  entire DST window, misplacing the evening reserve step-down (ECRS 2,809→1,972 MW
  across the August evening) by an hour through every summer scarcity season. Same
  defect class as the NP6 HSL builder's fixed `_prevailing_to_standard` lag. Fixed in
  `results/scarcity.py` (DSTFlag-disambiguated CPT→CST; winter byte-identical, levels
  unchanged; feeds all four product families + the ECRS path).
* **Under-hold refuted as tail owner.** At the 135 missed hours measured RTORPA p50 =
  **$1.0** (max < $260, zero hours > $1,000) and PRC p50 = **5,765 MW** — reality's
  ORDC priced *no* scarcity at the missed hours. Holding more AS in the model would
  manufacture reserve scarcity reality did not have (a rule-1 violation), not recover
  the real tail. (At the 46 caught hours RTORPA p50 is $56 — the deep ORDC events the
  model does form.)

### 1c. West/Panhandle deliverability — REFUTED at the event evenings, by two
independent measurements

* **Prices.** Actual RT zonal spreads at the named event evenings are ≈ zero — LZ_WEST
  and HB_PAN clear AT or ABOVE LZ_HOUSTON on 8/17 and 9/6 (e.g. 8/17 HE20: LZ_WEST
  $5,223 vs LZ_HOUSTON $5,007; 8/30 HE20 uniform $4,843 across every LZ and hub), i.e.
  the real events were system-wide (ORDC/λ) with **no West/Panhandle separation**.
  Across all Jul 23–Sep 7 hours the actual LZ spread is p50 $4.6 / p90 $53.5; the
  model's zonal spread on the 181 tail hours is p50 $0 / max $69 — both effectively
  copperplate at the tail hours, consistently.
* **Physics (the new zonal HSL).** The NP4-742 GEO per-region series (built this
  session) shows West+Panhandle wind delivered its **full COP potential** at the event
  evenings: curtailment 0 MW on 8/17 h16–19, ≤7 MW on 8/30, ≤488 MW on 9/6 — the wind
  was not stuck behind the export interfaces at the peaks. (Jul–Sep evening W+P share
  of ERCOT wind is 57.9 %, so the zonal series remains the load-bearing input for the
  West topology/curtailment lanes — just not for this tail.)

## 2. Where the 135 hours actually live — offer-driven λ, the G-22/ercot57-§4 family

Per-component balance at the missed hours (mean MW, model vs EIA-930): gas −305,
coal +432, nuclear −13, RE −1,683, demand −704 (model-under; ERCOT native load runs
~830–940 MW above the EIA-930-derived model demand at the named evenings while annual
totals match +0.05 %). Every physical input is faithful to within ~1–1.7 GW — and the
1.7 GW RE term goes the *loosening* direction when corrected.

Reality at those hours: hourly-mean SCED λ explains the RT price in 124/135 (λ >
0.8×RT; λ+RTORPA covers 133/135), RTORPA ≈ $0, PRC 4.6–9 GW. The market cleared
$500–5,000 **on the offer stack** — the August heat-wave bid wall — while the model
clears its cost-based mid-stack at ~$83–117 (its conditional offer surface
(`ercot_offer_surface_conditional`, live in the keeper) reprices only the gas
*peak-band* rungs in the top net-load bins, and the model's deep cheap mid-stack means
those rungs are never marginal at these hours). The owner of the residual is therefore
**offer formation at high net load** — the same channel ercot57 §4 named for
event-day depth ("post-fix, depth on true event days must come from the measured offer
surface, the structurally right channel") — with the standing caveat that an hourly
perfect-foresight LP structurally smooths the intra-hour 5-minute SCED dynamics that
contribute to the hourly means on some of these days.

**Pre-registered for the successor lane** (no mechanism change this session, rule 1):
extend the *measured* offer-surface representation so the cleared-offer wall the 60-Day
disclosure shows on those days can become marginal — candidates: widen the repriced
band below the peak rungs at the top net-load bins (measured cleared-share basis, not a
fitted level), and/or the measured DA-boundary formation family (G-22). A room-pin to
measured RTOLCAP stays forbidden (ERCOT-79 pre-registration); any fitted adder tuned to
this residual is rule-13 inadmissible.

## 3. Fixes landed this session (all measured-input alignment, rule 11)

1. **2023 HSL: UMass → published NP6 GEO** (`data/raw/ercot-hsl/ercot_2023_hsl_hourly.parquet`
   rebuilt; wind 108.01 TWh delivered / 114.04 potential, solar 31.88 / 34.25).
2. **Zonal HSL sidecars** (`ercot_<year>_hsl_zonal_hourly.parquet`, 2023–2025): new
   builder capability (`--zonal-only`), long format per (fuel, region), COP-HSL
   semantics documented, partial coverage kept NaN, sum-of-regions = 1.0000 of
   system-wide where a vocabulary is complete. Diagnostics input (this doc §1c); not
   yet a dispatch input.
3. **AS-plan CPT→CST clock fix** (`results/scarcity.py::ercot_as_plan_requirement_mw`).
4. `actual_tail.json` note path fix (data unchanged — the tail itself landed via PR
   #2801, so C3c now scores on re-scored bundles).

## 4. Runs

* **`ercot98_np6_hsl_fullspan`** — full-span 2023–2025 re-solve of the byte-faithful
  ercot97 keeper config on the two corrected inputs (no config deltas; replayed via
  `replay_keeper.py --years 2023 2024 2025`). Registered on the backcast dashboard;
  see the ERCOT-98 calibration-log entry for scores and disposition. 2024/2025 inputs
  are unchanged by both fixes except the AS-plan clock (DST window), so year-over-year
  deltas isolate cleanly: the 2023 delta carries NP6+clock, 2024/2025 deltas carry
  clock only.

## 5. Refuted suspects recorded so they are not re-run

* System-wide RE over-credit (accurate NP6 raises RE at the missed hours; model was
  *under*, not over).
* AS/ECRS requirement level (measured-faithful; duplicate-row artifact explained).
* AS under-hold as tail owner (reality: RTORPA ≈ $0 at every missed hour).
* West/Panhandle deliverability at the 2023 event evenings (real zonal spreads ≈ 0;
  real W+P curtailment ≈ 0 at the peaks — both the price and the physics say
  deliverable).
* Demand level as sole owner (−0.9 GW at named evenings is real but a minor term; the
  model's balance is otherwise faithful while the price gap is 5–50×).
