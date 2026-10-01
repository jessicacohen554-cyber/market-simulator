# FINDING — R-ERCOT-6: the window × partial double count re-measured, and the train-tier under-price (zero LP)

**Session:** R-ERCOT-6, 2026-09-26.
**Keeper:** `2026-09-25-r-5-hour-grain` (bundle `results/calibration/r_ercot5_hourgrain_span`, 2019–2025). Precondition checked on `main`: `keepers/ERCOT.json` names it.
**LP spent:** none. Every number comes from 28 instrumented `fleet_only` rebuilds of the keeper recipe (7 years × 4 variants), CAMPD unit-level CEMS, the keeper's committed hourly sidecars, and the committed zonal RT benchmark.

## Headline

- ERCOT stays **CALIBRATED** on the train tier. Nothing here touches the keeper.
- **Step 1.** Against the current keeper, the ercot-174 unit-scoped composition (matrix **R**) lifts coal capability **3.7–6.4 TWh/yr**. **1.0–3.7 TWh/yr** of that lift fills capability sitting below the plant's own same-hour CEMS output. It cuts that below-CEMS coal gap by 60–79 % in every year (e.g. 2023 1.73 → 0.69 TWh). The rest of the lift (1.7–3.1 TWh/yr) is above CEMS: capability that the same-hour CEMS record neither confirms nor contradicts.
- **The price-side reach is small.** In the train years' scarcity hours the lift is 70 MW (2023, 59 h) and 485 MW (2024, 2 h); 2025 has no P1 scarcity hours. Over each year's top-100 price hours it is 97 / 238 / 154 MW.
- **One of the three new-evidence premises holds only in part.** Coal is short of actual in 2023 (−2.40 TWh) and 2024 (−1.93 TWh). It is **over** actual in 2022 (+4.78) and 2025 (+1.23). The in-merit lift in 2025 is 3.34 TWh and in 2022 3.68 TWh, so the arm can add coal where coal is already high.
- **Finer-grain-wins** (the unit-exact window alone at a shared-unit hour) adds 0.5–2.0 TWh/yr more coal lift than the unit-scoped min(), and **most of that increment is above CEMS** (2023: +2.04 TWh lift, +0.21 of it below CEMS). It is the weaker construction.
- **A latent seam in the R arm, measured immaterial:** the shared-unit mask reads the DAY-grain window file while the keeper's window factor is HOUR-grain. Aligning it moves coal lift by ≤ 0.012 TWh/yr. It must still be fixed before any arm, for consistency.
- **Step 2.** The train-tier under-price is **mostly the actual load-zone congestion basis, not a supply-stack object.** Scored against the hub on the same weights, the keeper reads −4.0 % / +1.6 % / +0.4 % (2023/24/25). The actual LZ-over-hub basis is +2.35 / +2.21 / +2.65 $/MWh, i.e. 48 % / 126 % / 106 % of the C3a gap. The model's loaded zones are near copper-plate (2023 annual zone means all $47.30), while the actual West LZ averages $59.44 / $35.73 / $42.18. The rest is the 2023 scarcity tail and a flattened price distribution: the model overprices hours whose actual is below $30 and underprices the $40–$200 shoulder.

## 1. The double count, re-measured (Step 1)

Probe: `scripts/probes/_r_ercot5_availability_census.py`, repointed at `r_ercot5_hourgrain_span` (new `--bundle` / `--variant` options), and `scripts/probes/_r_ercot6_unitscoped_seam.py` (the A-vs-variant comparer). Full table, all three classes and all variants: `docs/handoffs/r-ercot/r_ercot6_unitscoped_seam.txt`.

Definitions, all TWh unless marked:
- **lift** = Σ pmax × (final availability, arm − keeper).
- **≤ CEMS** = the part of the lift that fills capability below the plant's own same-hour CEMS net output (unit-grain routing as in R-ERCOT-5 §2); **above** = the remainder.
- **gap A → B** = coal capability below own CEMS, keeper → arm.
- **in-merit** = lift in hours the tranche's mean `mc_base` is below the keeper's P1 load-weighted price. It is an upper bound on the energy the lift can add.
- **scar MW** = mean lift over the keeper's P1 hours above $1,000 or with slack; **top-100 MW** = mean lift over the year's 100 highest-price hours.

### Variant B — `ercot_dam_availability_event_cap_unit_scoped=true`, as coded (the R arm), coal

| year | lift | ≤ CEMS | above | gap A → B | in-merit | scar MW (h) | top-100 MW | PRB / lignite lift | keeper coal vs actual |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | 5.13 | 2.72 | 2.41 | 3.83 → 1.11 | 3.43 | 76 (53) | 67 | 4.60 / 0.53 | −14.03 |
| 2020 | 4.21 | 1.58 | 2.62 | 2.21 → 0.63 | 1.89 | 0 (5) | 157 | 4.09 / 0.12 | −16.96 |
| 2021 | 6.41 | 3.70 | 2.71 | 4.67 → 0.97 | 5.47 | 443 (123) | 442 | 5.88 / 0.52 | −3.35 |
| 2022 | 4.26 | 2.52 | 1.74 | 3.30 → 0.79 | 3.68 | 277 (18) | 211 | 3.87 / 0.39 | **+4.78** |
| **2023** | 3.67 | 1.04 | 2.62 | 1.73 → 0.69 | 1.84 | 70 (59) | 97 | 3.59 / 0.08 | −2.40 |
| **2024** | 5.04 | 1.96 | 3.08 | 2.75 → 0.79 | 2.99 | 485 (2) | 238 | 4.52 / 0.53 | −1.93 |
| **2025** | 4.23 | 2.15 | 2.08 | 2.86 → 0.71 | 3.34 | — (0) | 154 | 3.69 / 0.54 | **+1.23** |

- The lift is **PRB-concentrated** (87–98 %).
- CC_REGULAR also lifts, by 0.58–1.81 TWh/yr (0.35–0.97 of it ≤ CEMS). ST_GAS does not move.
- Keeper coal vs actual comes from the keeper's run payload (all-coal `fuelRows`, model − actual, TWh).
- Against the R-ERCOT-5 census (run on the r-4 keeper): coal lift is within 0.1 TWh in every year, and the below-CEMS gaps are 0.30–0.44 TWh lower here because the hour-grain keeper already removed that part.

### Variant Bh — B with the shared-unit mask at the window's hour grain

- `outages.unit_outage_active_units` calls `unit_outage_csv_for_iso(iso)` with no `hour_grain`. Under the R-ERCOT-5 keeper it therefore builds the shared-unit mask from the **day-grain** windows, while the window factor it composes with (`unit_outage_derate_factors(..., hour_grain=True)`) is **hour-grain**. Its own docstring ("the two layers adopt the optional hour grain together or not at all") has been false since R-ERCOT-5.
- **Measured:** aligning the mask changes coal lift by ≤ 0.012 TWh/yr and CC by ≤ 0.004. So it is immaterial, but any arm of this field should thread `hour_grain` through first, so the construction is the one it claims to be.

### Variant C — finer-grain-wins, coal

At a shared-unit hour the unit-exact window ceiling stands alone, instead of `min(window, plateau)`.

| year | lift | ≤ CEMS | above | gap A → C | increment over B (lift / ≤ CEMS) |
|---|---|---|---|---|---|
| 2019 | 6.25 | 2.99 | 3.26 | 3.83 → 0.84 | +1.12 / +0.27 |
| 2020 | 5.32 | 1.69 | 3.63 | 2.21 → 0.52 | +1.11 / +0.11 |
| 2021 | 7.38 | 3.80 | 3.58 | 4.67 → 0.87 | +0.98 / +0.10 |
| 2022 | 4.58 | 2.52 | 2.06 | 3.30 → 0.78 | +0.33 / +0.01 |
| 2023 | 5.70 | 1.26 | 4.45 | 1.73 → 0.48 | +2.04 / +0.21 |
| 2024 | 5.78 | 2.01 | 3.77 | 2.75 → 0.74 | +0.74 / +0.05 |
| 2025 | 4.78 | 2.24 | 2.53 | 2.86 → 0.62 | +0.54 / +0.09 |

- The increment is **76–98 % above CEMS**. The plateau that finer-grain-wins drops at a shared hour carries other units' partial downtime at the same plant, and it is dropping that too.
- **Recommendation between the two: B (the ercot-174 min()), not C.**

### Reading, against the three new-evidence premises

- **(a) The partial layer has been repaired twice (shaped K, day-guard K): holds.** The R verdict was reached against a layer both repairs have since changed. Even so, the double count still leaves 1.7–4.7 TWh/yr of coal capability below the plants' own same-hour output.
- **(b) G-COAL148 never scored against CEMS: holds.** The table above is that score. About half the lift is demonstrably below-CEMS capability; the other half is not contradicted.
- **(c) Coal is short of actual in the train years: holds for 2023/2024, and not for 2025 or 2022.** The 2026-08 flood concern was over-dispatch, and the in-merit lift (1.8–3.3 TWh in train years) is comparable to or larger than the train-year coal shortfalls. The arm may overshoot in 2024 and 2025. That is the risk a re-test would measure.
- **Price direction:** the lift adds cheap supply, so it can only lower prices or leave them flat. The train years already read cheap (C3a −5.6 to −7.5 %). By rule 1 that does not decide the arm, but a re-test should expect C3a to move away from actual, not toward it.

## 2. The train-tier under-price (Step 2)

Probes `scripts/probes/_r_ercot6_c3a_zonal.py` and `_r_ercot6_c3a_basis.py`. They reproduce the official C3a exactly: 2023 59.47 vs 64.32 (−7.5 %), 2024 29.24 vs 30.99 (−5.6 %), 2025 33.79 vs 36.29 (−6.9 %). Full output: `docs/handoffs/r-ercot/r_ercot6_c3a_decomp.txt` and `r_ercot6_c3a_basis.txt`.

### The benchmark is zonal, and the gap is mostly its congestion basis

- ERCOT's `rt_lw` scores each model zone against its own LZ settlement price (`derive_actual_lmp._lw_fields`, `ERCOT_MODEL_ZONE_TO_LZ`). Other ISOs use the system hub.
- The table below keeps those exact weights and swaps in the HB_HUBAVG series.

| year | model | actual LZ (gated) | actual hub, same weights | LZ basis over hub | basis share of the gap |
|---|---|---|---|---|---|
| 2021 | 169.90 | 165.95 (+2.4 %) | 162.92 (+4.3 %) | +3.03 | (model over) |
| 2022 | 68.45 | 74.94 (−8.7 %) | 71.76 (−4.6 %) | +3.18 | 49 % |
| **2023** | 59.47 | 64.32 (**−7.5 %**) | 61.97 (−4.0 %) | +2.35 | **48 %** |
| **2024** | 29.24 | 30.99 (**−5.6 %**) | 28.78 (+1.6 %) | +2.21 | **126 %** |
| **2025** | 33.79 | 36.29 (**−6.9 %**) | 33.64 (+0.4 %) | +2.65 | **106 %** |

(The 2022 row uses the zonal reconstruction and reads −8.7 % against the registered −8.1 %; it is shown for the basis only.)

**By zone** (gap contribution in $/MWh; model mean vs actual LZ mean):

| year | West | South_Central | Houston | North | South |
|---|---|---|---|---|---|
| 2023 | −1.59 (47.30 vs 59.44) | −1.32 | −0.98 | −1.08 | +0.24 |
| 2024 | −1.14 (27.56 vs 35.73) | −0.52 | 0.00 | +0.27 | −0.39 |
| 2025 | −1.36 (32.83 vs 42.18) | −0.78 | −0.18 | −0.09 | −0.08 |

- The model's loaded zones clear at one price almost everywhere: the annual zone means are equal to the cent.
- The actual West LZ carries a premium of $8–12/MWh.
- ERCOT prices no losses, so an LZ-over-hub basis is congestion.

### Body vs tail

Both sides capped at $200:

| year | gap | body ≤ $200 | tail > $200 | tail > $1,000 |
|---|---|---|---|---|
| 2023 | −4.84 | +0.83 | **−5.67** | −3.19 |
| 2024 | −1.75 | +0.48 | −2.23 | −0.44 |
| 2025 | −2.50 | **−1.29** | −1.21 | −0.22 |

- **2023 is a tail year.** The actual > $1k zone-hours (370) average $2,374 against the model's $1,609 in the same hours; the June and September scarcity months carry −1.65 and −1.24 $/MWh.
- **2024 and 2025 are shape years.** Inside the body the model is too flat:
  - It **over**prices hours whose actual is below $30: +4.80 (2024) and +4.03 (2025) $/MWh.
  - It **under**prices the $40–$200 actual shoulder: −3.44 (2024) and −4.88 (2025) $/MWh. In 2025's $100–200 actual hours the model averages $63.
  - LW quantiles for 2025: model p10/p90 20.9 / 47.8 against actual 13.1 / 63.7.
- Month structure is diffuse (no month beyond ±0.6 $/MWh in 2024/2025), so there is no seasonal object.

### Which structural object is left

1. **The sub-zonal LZ congestion basis (West / South_Central).** It is the largest single component in every train year and the whole of the 2024/2025 miss.
   - The zonal route is **closed**: the ERCOT-117 adjudication (`DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §10) found the corridor interfaces already at their measured limits, and the congestion forms on 138 kV single elements that no zone split reaches. Do not re-open the topology split.
   - The one named route is the **WP-B nodal layer**, a data-intake job that needs a station → area crosswalk the repo does not have.
   - It is **not** a price-tuning object. Rule 1(b)/(c) authorizes only year-invariant band multipliers, and those move all zones together, so they cannot produce a zonal basis. A multiplier sized to this gap would be the fitted adder rule 1 forbids.
2. **The flattened body.** Troughs sit too high and the shoulder too low: the spread compression the trough lane already adjudicated (§§7–9, closed on the offer side). It is reported here and needs no new lever.
3. **The 2023 scarcity depth.** It is the C3c model-class object (ORDC depth); 2023 hour counts pass (177 vs 181 h > $200).

**No multiplier is tuned against any of these** (rule 1(b)/(c)).

## 3. What this asks of the owner

- **Re-opening `ercot_dam_availability_event_cap_unit_scoped` (R) needs your leave.** The zero-LP case is §1: a real, below-own-CEMS double count of 1.0–3.7 TWh/yr of coal capability, removed at 60–79 %.
- The costs, stated plainly:
  - The arm lowers prices in train years that already read cheap.
  - Its in-merit lift exceeds the coal shortfall in 2024 and 2025, and 2025 coal is already over actual.
  - Its price reach in scarcity hours is small.
- If armed, the construction is **B with the hour-grain mask fix** (not finer-grain-wins).
- The cost is seven one-year shards (~15–20 min of LP each) against sealed per-year predictions.

## 4. Small open items (proposed, not done)

- **Decker Creek (3548):** the bin sheet carries only the 206 MW CT row. EIA-860 lists the plant in ERCO / TRE (Travis). The steam units 1–2 (≈565 MW net shortfall vs CEMS, 2019–2021) need a vintage-bounded ST_GAS row.
- **Jack Fusco / Brazos Valley (55357):**
  - EIA-860 2024 lists NERC region **TRE**, county **Fort Bend** (the Houston load zone), and BA **MISO**. The BA field is inconsistent with the other two.
  - A cited crosswalk is needed before any action, e.g. ERCOT's resource registration or the CDR unit list.
- **Hidalgo (bin 55545) and Arthur Von Rosenberg (7512):** both sit in the bin sheet with `ERCOT_Zone = Unknown` and a NaN heat rate (1,126 MW at `BIN_GROUP_HR_DEFAULT`). EIA-860 places them in Hidalgo County (South) and Bexar County (South_Central). The 7762 ↔ 55545 id mismatch is the CAMPD facility id vs the EIA plant code, and it needs the crosswalk row.
- **`scripts/data/derive_campd_unit_outages.py` non-ERCOT branch** still reads raw `g.plant_group`, so coal windows cannot be re-derived for other ISOs after COAL-SUB. This is reported to those lanes, not fixed here (rule 25).
