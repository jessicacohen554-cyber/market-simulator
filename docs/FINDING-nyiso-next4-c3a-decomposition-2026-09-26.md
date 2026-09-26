# FINDING — NYISO-NEXT-4: the C3a 2022 / 2025 miss, decomposed. No lever qualifies; no shards launched.

Session NYISO-NEXT-4, 2026-09-26. ZERO LP (rule 32 (a)). Keeper
`2026-09-26-nyisonext3-tranche-basis-span` (bundle `results/calibration/nyisonext3_span`) at
`main` 64d5a381. Keeper unchanged. No matrix cell moves. No PRECOMMIT was written, so no G-DRIFT
or footprint was owed.

Probe: `scripts/probes/nyisonext4_c3a_decompose.py`, which writes
`results/calibration/_nyisonext4_c3a_decompose.json`. Its inputs are:

- the keeper's committed `hourly/system_<y>.parquet` and `class_band_hourly_<y>.parquet`;
- the RT bench `actual_lmp_hourly_NYISO.parquet`;
- Transco Z6 NY daily prints;
- NYISO 5-min zonal RT (the 2022 zips are in the repo; 2023–2025 were fetched from
  `mis.nyiso.com/public/csv/realtime/` into scratch and are not committed; pass them with `NYRT_DIR`).

## 1. Definitions (fixed before any number was read)

- **Miss**: Σ D_h (model_h − RT_h) / Σ D_h, where model_h is the model's load-weighted price over the
  five zones. All contributions below add up to the annual miss, in $/MWh.
- **Tail hour**: actual RT above $300.
- **Dear-gas day**: a day whose Transco Z6 NY daily print is at or above that year's p90 of daily
  prints (the nyiso-248 daily coordinate). Iroquois has no daily series in the repo.
- **Marginal proxy**: in each hour, the thermal class-band that is partially loaded and has the
  highest median model price. The sidecars carry no offers, so this is only a proxy.
- **Zonal split**: hourly, on NYISO's published zonal RT. The zonal total is larger than the system
  total because the two use different benches.

## 2. Result

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| System miss ($/MWh; % of RT mean) | **−8.02** (−10.0 %) | −0.62 | −0.39 | **−7.15** (−10.8 %) |
| Tail > $300 (load share 1.4 % / 0.8 %) | **−5.37** | −0.68 | −0.96 | **−3.93** |
| Dear-gas days (~11 % of load) | **+1.17** | −0.01 | −0.24 | **+0.51** |
| Ordinary hours | −3.82 | +0.07 | +0.81 | −3.74 |
| Top decile of actual price | −10.56 | −3.76 | −3.54 | −8.70 |
| Deciles 1–8 combined | +3.56 | +3.25 | +3.75 | +3.02 |

**By month.**

- 2022: Dec −3.21, Feb −1.75, Jan −1.08, Jun −0.70. No other month is below −0.5.
- 2025: Jun −2.08, Jan −1.46, Feb −1.46, Jul −1.46. No other month is below −0.7.
- In 2025, 95 % of the tail contribution is outside Dec–Feb (the June and July heat).

**By zone (hourly zonal RT; model vs actual mean in $/MWh).**

| zone | 2022 | 2025 | 2023 | 2024 |
|---|---|---|---|---|
| Upstate_West | **−7.55** (38.8 vs 60.6) | −2.04 | −0.84 | +0.04 |
| NYC | −1.02 (tail −2.39 / non-tail **+1.37**) | **−3.84** (tail −2.23 / non-tail −1.61) | −0.06 | −0.73 |
| Long_Island | −2.01 | −2.38 | −1.14 | −0.80 |
| Capital_Hudson | −1.44 | −1.21 | −0.12 | −0.11 |
| Lower_Hudson | −0.22 | −0.56 | 0.00 | −0.06 |

**By marginal proxy.** ST_GAS is almost never the marginal proxy: 0.2 % of load in 2022 and none in
2025. The miss sits under:

- 2022: oil −3.78, CC_CHP-peak −2.23, CT_PEAKER −1.20.
- 2025: ST_CHP-peak −3.48, oil −2.63, CT_CHP −2.45.

## 3. What the decomposition says about the three candidates

- **(b) Winter body of the curve (non-firm gas curtailment, idle ECON capacity on dear-gas days): the
  premise fails.**
  - On dear-gas days the model is ABOVE RT in both miss years (+1.17 / +0.51).
  - An input that removes gas capacity on cold or dear-gas days would raise prices exactly where the
    model is already too high.
  - The negative mass is in the > $300 tail and in ordinary winter hours, not on gas-constrained
    days.
  - The route is refused on this measurement, not on a governance ground.
- **(a) NYC steam posture at minimum load: not qualified, and no new evidence.**
  - `scuc_load_pocket_commitment` is `G`. The nyiso-97 §5 bar forbids identifying the pocket
    requirement from observed unit conduct, and the AORR intake is closed (nyiso-160 / 163b).
  - NYSRC I-R3 / I-R5 are minimum-oil-burn and fuel-security rules. They set fuel, not a unit MW
    commitment level, so they cannot supply one.
  - `nyiso_incity_commitment_obligation` is `R` (nyiso-83).
  - The decomposition also cuts against it:
    - ST_GAS is essentially never the marginal proxy, so the steam over-run is inframarginal.
    - NYC non-tail 2022 is already +$1.37 too high. A lever that lifts the NYC off-tail price moves
      2022 away from RT.
- **(c) Long Island: real, but no identified lever.**
  - Long Island is the only zone that is biased low in every year (−2.0 / −1.1 / −0.8 / −2.4 zonal).
  - It is 16–24 % of the zonal miss in 2022 and 2025.
  - The measured LI instruments are already armed: `nyiso_li_tsl_n11_security` K, `seam_flow_envelopes` K,
    `nyiso_seam_par_attribution` K and `reliability_floor_plant_exclusions` K.
  - The flat ~2,040 MW east-side import block (nyiso-225) against 1,476 MW of measured NET schedules
    sits behind nyiso-125's identification refusal, which is still load-bearing.
  - No new measured source is in hand.

## 4. The largest single 2022 object is already adjudicated

Upstate_West carries **−7.55 of −12.24 $/MWh** of the 2022 zonal miss. The detail:

- The model's price sits at $1.1–1.4 in more than 25 % of hours; the actual p25 is $28.8.
- The Capital_Hudson–Upstate_West spread exceeds $5 in 98.8 % of model hours against 70.3 % actual.

This reproduces nyiso-224 exactly: the "$1.40 upstate pin", with 84 % of the 2022 residual on this
one boundary. That cell is `nyiso_total_east_cutset_ttc` **R**. nyiso-225 closed the topology-split
successor on three independent legs, and the measured 2022 Central-East TTC (1,825 MW) is `K` under
rule 14.

This session adds an independent zonal-bench confirmation. That is **not new evidence** for any
lever, so the cell is not re-opened. The pin appears in 2022 only (2023–2025 Upstate_West is
−0.84 / +0.04 / −2.04).

## 5. Disposition

- **No lever qualifies.** No PRECOMMIT was written and no shards were launched. The keeper and every
  matrix cell are unchanged.
- **Where the C3a miss actually sits:**
  - 2022: the Upstate_West pin (**R**, closed) plus the > $300 tail. The tail is the nyiso-242 object,
    foreclosed by idle sub-gate capacity.
  - 2025: the summer tail plus a broad downstate level shortfall, largest in NYC and Long Island.
- **The next session needs new measured data, not a new mechanism.** Candidates:
  - a per-line LI tie schedule that separates Neptune, CSC and 1385;
  - the in-city commitment requirement (MyNYISO access is owner-held).
- **Reported, not fixed (other lanes):**
  - The known misfiled ISO-NE `dartmonthlylmpindex_*.csv` files under `lmp-data/NYISO`
    (register N2).
  - The 2023–2025 NYISO zonal 5-min RT files are not in the repo. They are fetchable, about 38 MB
    for three years.
