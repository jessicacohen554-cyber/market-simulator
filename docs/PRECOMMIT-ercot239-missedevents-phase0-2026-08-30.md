# PRECOMMIT — ercot-239 (2026-08-30): Phase-0 DRIVER characterization of the 14-hour missed-event family — ZERO-SOLVE, measurement only, NO lever, NO gate change

**Session ercot-239, branch `claude/ercot-239-residual-queue-lbkvbf`.**
Charter: the post-two-config residual-queue handoff's priority 1 — the
14-hour missed-event family (FINDING-ercot237 §3 leg U1 + corner hour
h4578; §7 owner-visible queue item 1). The handoff precommits this round as
Phase-0: *"precommitted Phase-0 characterization of the 14 hours' drivers
(CAMPD outage windows, net-load ramps, tie flows) BEFORE any lever."* This
precommit is pushed and blob-verified BEFORE any measurement is computed
(ercot-224/225/237 Phase-0 precedent). On-queue per rule 26 duty (a): the
population is FINDING-ercot237 §7 candidate object 1, whose stated prior is
an **availability / outage / net-load-ramp REPRESENTATION object, not an
offer-curve one** — this round measures exactly that attribution.

Keeper structure resolved fresh at dispatch (unchanged from ercot-238):
FORWARD KEEPER `2026-08-25-234-eastex-identity` (2024–2025) + 2023
CARVE-OUT `2026-08-25-236-swcap-clip-k33` (CALIBRATED, zero caveats;
bundle `results/calibration/ercot236_k33_clip`). The family is a
2023-carve-out-lane object; NEITHER config is touched this round.

## 1. Population and the V-0 identity gate (hard assert, run first)

Series constructions byte-identical to the ercot-237 probe
(`scripts/probes/ercot237_bandswap_phase0.py`):

* **Model series** — keeper sidecar
  `results/calibration/ercot236_k33_clip/hourly/system_2023.parquet`,
  P1 rows, per-hour demand-weighted zonal `price` (Σ price·demand /
  Σ demand), reindexed to 8760, NaN → 0. h = positional hour-of-year
  index 0–8759; hod = h mod 24.
* **Actual series** —
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`,
  `year == 2023`, sorted by `hour`, column `rt`, first 8760 values.

**Population** = {h : model < $200 AND actual ≥ $500} — the union of the
ercot-237 `lt_200|500_1000` cell (13 h) and `lt_200|ge_1000` cell (1 h,
h4578).

**V-0:** the recomputed population must be EXACTLY the 14 hours named in
the committed record — {h2058, h2971, h4623, h4626, h5369, h5484, h5777,
h5943, h5945, h6399, h7001, h7145, h7480} ∪ {h4578} — and list-identical
to the committed `results/calibration/ercot237_bandswap_phase0.json`
cell-hour lists. Any mismatch STOPS the probe (no result recorded) and is
an Amendment (§5), never worked around.

## 2. What is measured (all zero-solve; committed artifacts + raw measured inputs only)

The probe (`scripts/probes/ercot239_missedevents_phase0.py`, writes
`results/calibration/ercot239_missedevents_phase0.json`) computes, per
event hour and against fixed peer framings:

* **M-1 — actual-side driver panel** (EIA-930 wide extract
  `data/raw/eia-930-hourly/ERCO hourly.parquet`, the repo's own local-hour
  convention: `Local date` + `Hour` hour-ending rows of 2023, the
  convention of `src/market_sim/data/eia930/frames.py`): `Demand`,
  `NG: WND`, `NG: SUN`, actual net load = Demand − WND − SUN; 1-h and 3-h
  net-load ramps (NL[h] − NL[h−1], NL[h] − NL[h−3]); `Total interchange`
  and the DC-tie counterparty columns (`CEN`, `CFE`, `SWPP`). Each
  quantity's percentile within (a) all 2023 hours and (b) the month ×
  hod±1 peer set.
* **M-2 — model-side state at the same hours:** system sidecar (ISO
  demand = Σ zones, demand-weighted / min / max zonal price, slack, dump,
  `reserve_price`, `ordc_adder`); `reserve_family_2023.parquet` (per
  family: dual, requirement_mw, held_mw, shortfall_mw);
  `class_hourly_2023.parquet` (aggregate thermal MW, wind MW, solar MW —
  class taxonomy read from the sidecar's own `klass` values);
  `storage_2023.parquet` (net discharge). Plus: model thermal dispatch's
  percentile within its own month (how deep into the stack the model
  was).
* **M-3 — net-load gap decomposition:** model demand vs actual Demand;
  model wind vs actual WND; model solar vs actual SUN; model net load
  (demand − wind − solar dispatch) vs actual net load; the per-hour gap
  and its three components in MW. (Model wind/solar dispatch ≈ the CF
  bound in these hours since model prices are $35–167 — curtailment is
  visible in `dump` and reported.)
* **M-4 — availability / outage leg:**
  * (i) **Overlay-eligible outage MW** covering each event hour's date:
    `data/raw/campd-unit-outages.csv` rows with `duration_days ≥ 5`
    (`UNIT_OUTAGE_MIN_DAYS`, `src/market_sim/data/outages.py`), summed
    `unit_capacity_mw` — an APPROXIMATION to what the solve derates
    (date-grain, before fleet matching), labelled as such; its percentile
    within the year's daily distribution.
  * (ii) **All-duration hourly-grain CAMPD outage events** covering the
    hour: `data/raw/ercot-outages.csv` (not consumed by the engine —
    measured diagnostic reference), event count and MW where a
    (oris_code, unit) → `unit_capacity_mw` join against
    `campd-unit-outages.csv` lands; join coverage reported.
  * (iii) The **short/non-overlay component** = (ii) members whose
    duration < 5 days — the outage MW the overlay construction cannot
    carry, in exactly these hours.
* **M-5 — driver attribution table** with FIXED ex-ante thresholds; every
  driver that fires is reported (hours may carry several):
  * **NET-LOAD-GAP hour:** actual net load − model net load ≥ 1,500 MW;
    sub-attributed to its largest component (demand / wind / solar gap).
  * **RAMP hour:** actual 3-h net-load ramp ≥ p90 of that month's 3-h
    ramp distribution (all hours of the month).
  * **OUTAGE hour:** all-duration joined outage MW (M-4 ii) ≥ p90 of the
    year's hourly distribution of the same construction, OR short-outage
    MW (M-4 iii) ≥ 1,000 MW.
  * **TIE hour:** actual net exports ≥ 300 MW during the event hour
    (sign convention read from the source and stated in the JSON).
  * **UNATTRIBUTED:** none fire — reported as such, never force-fitted
    (kill K-2).

## 3. Declared priors (graded in the FINDING; never selection criteria)

* **P1 — not near-misses:** in all 14 hours the model shows zero reserve
  shortfall and every reserve-family dual ≤ $5/MWh — the model is
  structurally far from scarcity, not one band low. (Basis: model $35–175
  with the ≥$1,000 surface already placed elsewhere in August.)
* **P2 — ramp family:** ≥ 8 of 14 are RAMP hours under M-5. (Basis: hod
  12–19 concentration and 1–2 h spike shape read as net-load-ramp
  scarcity, which a perfect-foresight LP with no ramp constraint cannot
  price at ANY net-load level — the finding's stated structural prior.)
* **P3 — ties immaterial:** ≤ 3 of 14 hours show net exports ≥ 300 MW.
  (Basis: ERCOT DC ties are ~1.2 GW total against a 70+ GW system.)
* **P4 — net-load gap real but secondary:** ≥ 5 of 14 are NET-LOAD-GAP
  hours, and where the gap fires, wind (model wind > actual WND) is the
  largest component in the majority. (Basis: shoulder-season events are
  low-wind events; the model's CF input and EIA-930 can diverge
  hour-by-hour.)
* **P5 — outage-season exposure:** ≥ 5 of the 10 non-August members fall
  in overlay-eligible outage windows at ≥ p75 of the year's daily outage
  MW. (Basis: Mar/May/Oct/Nov membership is planned-outage season.)

## 4. What this round may and may not do

* MAY: read committed sidecars, committed actuals, and raw measured
  inputs; compute the measurements above; record them in the results JSON
  + a FINDING doc; grade the priors; classify the 14 hours; name candidate
  objects for the owner-visible queue.
* MAY NOT: solve anything; edit any gate, config, offer curve, overlay,
  or mechanism; stamp any matrix cell (no mechanism is tested); arm a
  lever. **K-3: whatever the attribution shows, any lever is a NEW
  precommitted round** — under this session's handoff a lever round is in
  scope for the session, but it gets its own pushed precommit with its
  own kills before any lever work starts, and any keeper-structure
  consequence goes to the owner (ESCALATE, never self-adopt).
* Registration: no run is produced, so rule 15 does not trigger; the
  deliverable is the committed probe + JSON + FINDING + calibration-log
  entry (ercot-237 zero-solve precedent).
* Years touched ⊂ {2023}; no `--holdout-authorized`; no marker; ERCOT
  surfaces only (rule 25).

## 5. Amendment protocol

Any deviation from §1–§2's constructions discovered mid-round (a V-0
membership mismatch, a source column absent, a join that cannot be made)
is recorded as an Amendment to this precommit BEFORE any further
measurement, pushed, and the FINDING cites it — never silently absorbed.
