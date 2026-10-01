# FINDING — R-ERCOT-4: ERCOT validation-year failures (2019/2020 coal, 2021 C3b), zero LP

**Session:** R-ERCOT-4, 2026-09-25.
**Keeper:** `2026-09-25-r-ercot2-chp-off` (bundle `results/calibration/r_ercot2_chpoff_span`, 2019–2025). Precondition checked on `main`: `keepers/ERCOT.json` names it.
**LP spent:** none. Every number comes from `fleet_only` rebuilds (no solve), the keeper's committed hourly sidecars and payload, CAMPD unit-level CEMS, and EIA-930.
**Shards launched:** none. **Registered:** nothing. **Keeper, matrix verdicts and determination:** unchanged.

## Headline

- ERCOT stays **CALIBRATED** on the train tier {2023, 2024, 2025}. Nothing in this session touches it.
- **Step 0 (owner, verbatim answer):** "No — go to Steps 1–2". The 2019–2022 60-Day SCED coal disclosures will not be fetched or procured. The 2019/2020 coal shortfall therefore stays **data-blocked** on its named mechanism (FINDING-r-ercot-3 §2).
- **Step 1:** the measured PRB proxy for 2019/2020 is admissible but **not material**. No arm.
- **Step 2:** the ledgered cause of 2021 C3b is **stale**.
  - February (Uri) now carries only 22% of the squared error. **October carries 64%.**
  - October's error is a model scarcity event on Oct 20–25, 2021.
  - That event is caused by a construction defect in the **day-shaped CAMPD partial-outage layer**. The layer caps Martin Lake at 38.5% on two days when CEMS shows all three units at full load.
  - The defect is present in **every** year, the train years included.
  - It is **proposed below, not armed**. It is a construction change to a frozen derive (rule 23) that moves the train tier, so it needs the owner.

## Step 1 — measured PRB proxy for 2019/2020 (rule 14 candidate)

**Premise, confirmed.**
- `apply_coal_supply_pricing` returns early for any year outside `COAL_PRICE_PRB_BY_YEAR` (2023+) (`src/market_sim/data/fuel/coal.py`).
- So in 2020 seven of ten ERCOT coal plants keep the generic **$1.884/MMBtu**, even though the measured ERCOT PRB reporter series `_prb_monthly_actuals` has 2019/2020 rows (annual means **1.739 / 1.650**).
- Measured on the 2020 fleet-only build:
  - Fayette (6179) gets $1.488 from its own EIA-923 print.
  - San Miguel (6183) gets $2.954.
  - J K Spruce (7097) gets $1.905.
  - The other seven stay at $1.884.

**Delta, measured.** 2020 fleet-only build, with the PRB proxy extended to 2020 and lignite left at generic (no measured pre-2023 lignite series exists, and a hand 1.45 would be extrapolation):

| | rows | MW | offer delta |
|---|---|---|---|
| coal rows, fuel price changed | 20 of 40 | — | fuel −$0.234/MMBtu |
| coal rows, **offer (`mc_base`) changed** | **5** (the `_mustrun` tranche of Parish, Limestone, Martin Lake, Coleto Creek, Sandy Creek) | 1,773 | −$2.44 to −$2.67/MWh |
| committed / econ / peak tranches | unchanged | — | 0 |

- **Why the other tranches don't move:** the committed and econ levels are the ERCOT-144 per-plant SCED curves, which carry no fuel term. So the fuel correction reaches coal only through the ERCOT-137 `_mustrun` margin, as FINDING-r-ercot-3 §3 predicted.
- **Why it can't close the gap:** the 2020 shortfall sits in the 4.6 GW of econ/committed coal priced above the CC_REGULAR p75. None of that moves. Not material, so Step 3's arm condition is not met.
- 2019 has the same structure with a smaller delta (1.739 vs 1.884).
- It remains an admissible input correction a later lane may bundle with another arm. Alone, it is not worth seven shards.

**Correction to my own first measurement.**
- A first pass reported *zero* changed rows. That was a probe artifact.
- `_r_ercot3_coal_census.summarize` keys rows by `(plant_code, tranche)`, but the tranche field resolves to `None`. So the four tranches of a plant collapse onto one dict key and the diff only saw the last one.
- The table above comes from a direct per-row diff. FINDING-r-ercot-3's own conclusions do not depend on that keyed diff.

## Step 2 — 2021 C3b 0.203: the object moved from February to October

**Monthly decomposition.** Keeper payload vs the load-weighted RT actual (`score_price_shape` basis):

| month | model $/MWh | actual $/MWh | error | share of SSE |
|---|---|---|---|---|
| Feb | 1,706.95 | 1,767.07 | −60.12 | 22.0% |
| **Oct** | **154.69** | **52.31** | **+102.38** | **63.8%** |
| Jun–Aug | 57.5–69.2 | 38.1–44.2 | +19 to +28 | 10.7% |
| other 7 months | | | | 3.5% |

- NRMSE 0.2034 (gate 0.20).
- **With October exact, it scores ~0.12.**
- February alone cannot close it: the Feb error would have to fall to $55.4 from $60.1, and the daily-gas route that could do that is blocked (ercot-265).
- ercot-263's "February is 95.7% of the SSE" was true on its keeper. Later input repairs shrank February's error from −$345 to −$60, and **October is now the object.**

**October is one event.**
- The model sheds load at the $5,000 cap on **2021-10-20 13:00–18:00**: slack 208–1,743 MW, reserve price ~$11,900.
- It prices $2,600–$4,500 through Oct 21 and Oct 24–25.
- 17 hours above $1,000 contribute **$80.34** of October's equal-hour mean ($133.47; excluding them, $54.38 vs $52.31 actual).
- Demand, nuclear (2.48 GW model vs 2.53 GW EIA-930 — two units genuinely out), gas, wind and solar all sit within normal range.
- **The gap is coal.** At 15:00 on Oct 20 the model dispatches 7.97 GW. EIA-930 shows **9.7 GW net**, and CAMPD shows **11.3 GW gross**.

**Per-plant coal availability in the scarcity hours** (fleet-only 2021, `pmax × availability`) vs CAMPD gross load, 14:00–17:00:

| plant | model available MW | CAMPD gross MW | which input sets the model value |
|---|---|---|---|
| **Martin Lake 6146** | **916** (2,380 a week earlier) | **2,577** (all 3 units at ~860) | shaped partial derate **0.385** for Oct 20–22 |
| Fayette 6179 | 660 | 1,028 | unit 2 genuinely out (CEMS NaN); DAM 0.612 |
| J K Spruce 7097 | 540 | 828 | unit `**1` genuinely out; DAM 0.509 |
| Twin Oaks 7030 | 87 | 172 | U1 genuinely out; model below the surviving unit |

- The ERCOT 60-Day **DAM** disclosure has Martin Lake at **1.0** on Oct 14–25 (`ercot_thermal_dam_availability_plant_series`).
- The cut comes from `data/raw/campd-partial-outages-shaped.csv`, which outranks the DAM restore under the measured-event precedence cap.
- **CAMPD hourly, Martin Lake:**
  - Oct 19 and Oct 22: daily max 223–314 MW per unit.
  - **Oct 20 and 21: 858–874 MW per unit, from noon to 19:00.**
- The plant cycled economically through a low-price week, then ran flat-out on the two tight days. The layer forbids exactly those two days.

## The defect: the shaped partial-outage layer caps days whose own record shows full load

**Construction** (`scripts/lib/outage_detect._plateau_state` / `_detect_shaped`, ercot-185):
- Plateau membership is `running & (sm < 0.65·ref)`, where `sm` is a centered **7-day rolling median** of daily-max CF.
- The per-day derate is `f0 · sm[d] / median(sm)`.
- Both read the smoothed series, so a day whose **own** `dmax[d]` is at the ceiling is still inside the plateau and still capped. The smoothing exists to "ride through recovery blips".
- On a cycling coal plant, those "blips" are the plant's full-load days.
- The deriver states the assumption this falsifies: *"Coal is all-or-nothing per unit, and a derate cap only binds when the model wants to run above the observed ceiling, so it is safe to detect even on cyclic coal"* (`derive_partial_outages.py`). The cap binds precisely on the days the plant ran above it.
- ercot-185 repaired the same class of fault one grain up: a multi-week median imposed as an hourly ceiling (W A Parish h2827). This is its day-level residue.

**Footprint, every year.** Probe `scripts/probes/_r_ercot4_shaped_derate_footprint.py`; output `docs/handoffs/r-ercot/r_ercot4_shaped_footprint.json`. It counts plateau days whose shaped derate sits more than 0.05 below `min(1, dmax[d]/ref)`:

| year | coal plateau-days | coal days capped below own peak | Σ daily MW gap (coal) | CC days capped | worst coal day |
|---|---|---|---|---|---|
| 2019 | 754 | 72 | 18,609 | 11 | Martin Lake 04-24, 0.375 vs 0.643 |
| 2020 | 643 | 96 | 31,237 | 9 | Martin Lake 04-08, 0.566 vs 0.965 |
| 2021 | 949 | 79 | 26,680 | 8 | **Martin Lake 10-21, 0.385 vs 0.997** |
| 2022 | 686 | 71 | 20,185 | 19 | Martin Lake 06-02, 0.525 vs 0.974 |
| 2023 | 683 | 120 | 35,721 | 28 | W A Parish 03-17, 0.466 vs 0.872 |
| 2024 | 776 | 110 | 29,728 | 25 | J K Spruce 08-18, 0.417 vs 0.994 |
| 2025 | 662 | 59 | 18,521 | 37 | Martin Lake 02-27/28, 0.514 vs 1.000 |

What this footprint does and does not explain:
- **The 2019/2020 coal energy gap: no.** The gap sum is at most ~0.45–0.75 TWh/yr of coal capability, against −10.7 / −13.8 TWh. The coal energy object stays FINDING-r-ercot-3's offer-conduct question.
- **Scarcity hours: yes.** The defect concentrates exactly on the days a cycling plant ran flat-out, which are the tight days. October 2021 is the measured case.

## Proposed repair (not armed — owner decision)

**Candidate: a day-grain membership guard, zero new scalars.**
- A day whose **own** measured `dmax[d] ≥ _CEILING_FRAC · ref` is not a partial-outage day under the detector's own threshold.
- Equivalently, the shaped derate on any plateau day is floored at `min(1, dmax[d]/ref)`. A plant is never capped below what it measurably ran that day.
- Every quantity is the frozen detector's own (`_CEILING_FRAC`, `ref`, `dmax`), so rule 21's DOF ledger is unchanged.

**Whether it is admissible:**
- **Rule 13 forward story:** the partial-outage overlay is a backcast-only measured availability input, and the guard only makes it consistent with its own source.
- **Rule 23:** it is a construction repair with a PRECOMMIT, like ercot-185. It is not a re-valued parameter.

**What arming it would take:**
- Re-derive the shaped extract (`derive_partial_outages.py --emit-shaped`, years 2019–2025).
- A PRECOMMIT with sealed per-year predictions, the G-DRIFT audit, and the DOF ledger carried verbatim.
- **7 shards (one per year, rule 36)** on the keeper recipe, then compose, attest, register with `--no-prune`, and update the matrix cell `ercot_partial_outage_shaped_derate`.
- It moves the **train tier** (2023 carries the largest footprint), so the headline could move in either direction. Rule 1 says it stays in if it is right either way.

**It breaks ercot-185's SP-6 property, and says so.** The guard lifts the derate on the capped days, so `median(shaped)` is no longer `f0` and the construction is a **net lift**, not a pure re-shaping. The deriver's SP-6 assertion must be replaced by the day-grain property: `shaped(d) ≥ min(1, dmax[d]/ref)` for every plateau day. That is the reason it needs a PRECOMMIT rather than a silent re-derive.

**Scope note:** the shaped file carries ERCOT coal and CC_REGULAR rows. All 26 plants are on the ERCOT bin sheet (verified), and the file is read only under the ERCOT-gated `ercot_partial_outage_shaped_derate`. So the repair is ERCOT-only (rule 25), and ERCOT CC rows move with the coal rows (8–37 capped days/yr).

**Not done, and why.**
- The prompt's Step 3 arms only on Step 0 = YES or a material Step 1 delta; neither holds.
- This object was not in the brief, and it changes a keeper mechanism's construction across the train years.
- Arming it unasked would be the "slip in" Step 4 forbids.

## Step 4 — small open items (proposed only, untouched)

- **Hidalgo:** the bin sheet uses plant code 55545, eGRID uses ORISPL 7762. Together with Arthur Von Rosenberg (7512), 1,126 MW sit at `BIN_GROUP_HR_DEFAULT`. The fix needs a curated, cited crosswalk and has derive consequences. Not attempted.
- **The census probe's tranche-key collapse** (above) should be fixed before any later lane uses `summarize` for a row diff.
- The 4 pre-existing unit-test failures on `main` belong to other ISOs and were left alone.

## Records

- Probe: `scripts/probes/_r_ercot4_shaped_derate_footprint.py`; output `docs/handoffs/r-ercot/r_ercot4_shaped_footprint.json`.
- The Step 1 and October availability rebuilds were scratch `fleet_only` builds over `scripts/probes/_r_ercot3_coal_census.build`. Their numbers are in the tables above.
- Rule 28: no mechanism was solved. The `ercot_partial_outage_shaped_derate` cell stays **K**, with this finding appended to its evidence as an open construction defect.
