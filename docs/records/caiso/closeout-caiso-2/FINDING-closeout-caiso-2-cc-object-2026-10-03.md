# FINDING closeout-CAISO-2: the 2019–21 CC_REGULAR object, and the C3c-2021 window (2026-10-03, zero LP)

Lane charter: desk `session_01ALecU5Wjde4tkbLrnMExT9`, 2026-10-03. Keeper `2026-10-02-closeout-caiso-w1-arm2`
(bundle `results/calibration/closeout_caiso_w1_a2_span`, 2019–2025). Computed at `origin/main` `792e55ad`; rebased onto `31f6af11` (no change to the keeper bundle, the CAISO bench parts, the render reconcile or the verdict). **Zero LP:** no
shard was launched, no run was registered, and the keeper is unchanged.

Probes (committed beside this record, outputs in `_cc_object.json`):
- `scripts/probes/_closeout_caiso_2_cc_object.py`: step 1. It reads the keeper's committed P1 sidecars, its three
  hash-verified shared benchmark frames (`run_calibration_full.py --restore-shared-inputs`: eia923 / campd / eia930
  all "verified" against `meta.json`), the committed bench parts, and EIA-930 CISO hourly Demand.
- `scripts/probes/_closeout_caiso_2_c3c_window.py`: step 2.

The current keeper scores CC_REGULAR **+10.19 / +16.45 / +8.11 TWh** (2019/20/21). The charter's +10.75 / +17.55 /
+10.17 are R-CAISO-20's numbers. The probe sums `class_hourly`, which is 0.09 TWh above the verdict's grid-delivered
model in 2019, so the tables below use the probe's internally consistent totals.

## Headline

| | 2019 | 2020 | 2021 | 2022 (pass, control) |
|---|--:|--:|--:|--:|
| scored miss (model − `classFull`) | +10.28 | +16.58 | +8.12 | +1.02 |
| **bench**: `classFull` vs the plant-level EIA-923 grid record | **4.59** (×0.887) | 3.03 (×0.935) | 1.53 (×0.970) | 0.03 |
| model − plant-level EIA-923 | +5.69 | +13.56 | +6.59 | +0.99 |
| (b) net imports, model − EIA-930 | −1.50 | **−10.76** | **−7.27** | +4.29 |
| (d) demand, model − EIA-930 Demand | +3.13 | −1.86 | −1.80 | −4.13 |
| (b) other gas classes, net | −2.39 | −1.66 | +1.81 | −0.84 |
| (b) hydro + nuclear + VRE + geo/bio | +1.15 | +2.55 | +1.63 | +3.75 |
| (a1) above seasonal demonstrated capability | 2.10 | 0.64 | 0.51 | 0.29 |
| (c) RA bridge forced CC energy (D-2) | 3.96 | 3.71 | 3.90 | 3.74 |

**Pre-fixed bar (charter):** a lever is admissible only if one model-side bucket carries ≥ 60 % of the scored miss.
- **2019: no bucket clears.** The largest piece is the bench basis (45 %), which is a benchmark ruling and not a
  lever. The largest model-side bucket is demand (30 %).
- **2020 and 2021 clear only on imports** (65 % / 90 %). That is the DSW volume, which stays data-limited under R-16.
- **Step 3 does not fire.** No PRECOMMIT, no shards.

One owner card does follow, and it is benchmark-only (§2).

## 1. The bench component: the 2019–21 C1 actual sits below two measured sources

`classFull.CC_REGULAR` for 2019–21 is not the EIA-923 record. `render_calibration_html.reconcile_vintage_classes`
scales every fossil class by one factor to a target. The target is the EIA-930 gas + coal + oil cell minus the
geothermal + biomass fold-in deflation (`benchmark_semantics.gas_foldin_deflation`, F = 923 OTHER + biomass − 930
Other), capped at the CEMS anchor. The probe reproduces the committed `classFull` exactly in 2019–21.

| TWh | 2019 | 2020 | 2021 | 2022 |
|---|--:|--:|--:|--:|
| reconcile factor on every fossil class | 0.887 | 0.935 | 0.970 | none (in band) |
| gas family: scored / EIA-923 grid / CEMS anchor (`fossil_cems_grid`) | 51.17 / 57.68 / 59.12 | 59.34 / 63.51 / 64.78 | 65.44 / 67.48 / 68.72 | 68.02 / 68.06 / 69.95 |
| SOCO-60 fold test: 930 gas − 923 gas FULL (CHP host incl.) | **−3.71** | **−0.45** | **+1.05** | +4.54 |
| … the fold F it would have to hold | 14.76 | 15.07 | 14.48 | 13.39 |
| 930 gas − 923 gas grid | +7.57 | +10.23 | +11.81 | +14.73 |

Readings:
- **EIA-923 grid and CEMS agree within 2.5 % in every fold year.** That is two independent metered sources. The
  reconciled target sits **11–13 % below both** in 2019 and 3–5 % below in 2021. This is the same evidence standard
  caiso-121 used to move the CAISO NG-cell onset to 2023.
- **On SOCO-60's own test, CAISO 2019–21 refute the fold the same way SOCO does.** The rule is "a fold of F TWh makes
  930 gas exceed the 923 gas classes by ~F", with the 923 side FULL (CHP host included). CAISO's 930 gas sits at or
  below 923 FULL in 2019–20 and +1.05 TWh above it in 2021, against an F of about 15 TWh.
- On the grid basis the room is 7.6–11.8 TWh. That is still short of F, and the CEMS anchor rules on level.
- The model's demand input (caiso-80 Option A) removes the whole NG cell and then adds the geo/biomass energy
  back as its own term, so physically it does not depend on where 930 put that energy.
  - **Correction (implementation check):** that term is computed by calling the same
    `gas_foldin_deflation`. Adding CAISO to `EIA930_GAS_FOLD_REFUTED` alone would zero the term on any re-derive of
    `derive_caiso_supply_consistent_demand.py`, which would drop about 14 TWh of demand.
  - The committed demand artifacts do not move (rule 23).
  - The derive must first be decoupled to compute `max(0, 923 OTHER + biomass − 930 Other)` directly, which is the
    same value. That is part of the implementation, not a separate ruling.

**What-if, zero LP** (bench parts patched in the working tree, verdict re-run, `git checkout` restored them; this is
`EIA930_GAS_FOLD_REFUTED` ∪ {CAISO}, with the CEMS cap still in force):

| Record | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| C1 CC_REGULAR | +10.19 → **+5.60** FAIL | +16.45 → **+13.43** FAIL | +8.11 → **+6.58** FAIL |
| C1 CC_CHP / CT_PEAKER / ST_GAS | pass → pass | pass → pass | pass → pass |

- 2022–25 are untouched: 2022–24 are in band, and the CEMS cap governs 2025.
- C2, C3, C4, C6 and C8 do not move.
- The determination stays **NOT-YET**.
- This is the routed R-CAISO-5 §6 / R-CAISO-6 "Routed 2" question, now with the SOCO-60 test on CAISO's own data.

## 2. Model-side buckets

**(a) Capability.** Per plant, the ceiling is the p99.9 of its CEMS net hourly levelled to EIA-923 monthly.
- Model energy above the seasonal ceiling (a1) is 2.10 / 0.64 / 0.51 TWh.
- Above a monthly ceiling (a2) it is 2.38 / 1.14 / 0.94. That is an upper bound: it also counts outages and
  economic part-load months.
- The 2019 figure is 20 % of the scored miss. Seasonal capability is adjudicated R (cc_winter_capability_basis
  caiso-186, cc_capacity_reconcile caiso-185), so this is not re-opened.

**(b) Displaced classes** (CISO energy balance; actual = EIA-923 levelled on CEMS shape, EIA-930 for imports, VRE and
nuclear, and EIA-930 hydro shape at EIA-923 level).
- 2019 over-run hours (6,026): CC +9.07, imports −6.67, CT_CHP −1.59, ST_GAS −0.93, CT_PEAKER +1.20.
- Annual 2019: imports −1.50, other gas −2.39 (CT_CHP −2.29 and ST_GAS −1.07, against CC_CHP +0.60 and CT_PEAKER
  +0.42), VRE / hydro / geo +1.15.
- The CT_CHP and ST_GAS under-run appears in every year including the passing 2022 (−1.08 / −1.00). It is not a fold
  object.
- 2020–21: imports dominate (§ headline). 0b already measured the DSW −15.1 / −10.2 and PNW +3.8 / +2.2.

**(c) RA must-offer bridge.**
- The bridge forces 3.96 TWh of CC_REGULAR in 2019 against 3.74 in the passing 2022. Its year-specific share of the
  2019 excess is ≤ 0.23 TWh (2 %). Even total removal would be ≤ 39 % of the scored miss, before re-dispatch.
- The CPUC 2019 RA Report has committed RA at 30.9–47.6 GW a month, and gas is about two-thirds of IOU / CCA / ESP RA
  capacity (CPUC, *2019 Resource Adequacy Report*, March 2021; *State of the RA Market*, Sept 2019).
- The bridge's mean forced CC energy is 452 MW, an order of magnitude inside the gas RA shown. The bridge is not
  over-holding against RA showings.

**(d) Demand.**
- The model is +3.13 TWh over the EIA-930 Demand cell in 2019, but −1.86 / −1.80 / −4.13 in 2020–22.
- Against the actual supply sum it is +2.08 / +2.79 / +1.59 / +3.79 every year, including the passing 2022.
- The series is the owner-signed caiso-80 Option A construction. No lever.

**2020 and 2021 net of the measured import gap:**
- 2020: +16.58 − 10.76 = **+5.82**. Of that, the bench is 3.03 (52 %); the rest is VRE / hydro +2.3 against other
  gas −1.7 and demand.
- 2021: +8.12 − 7.27 = **+0.85**, inside the ±4.77 band.
- On the corrected bench (§1) the import gap alone exceeds the 2021 miss and leaves 2020 at +2.67, also inside the
  band. **The 2020–21 CC object is the DSW import volume.** 2019 on the corrected bench is +5.60, of which imports
  are 1.50, demand 3.13 and other gas 2.39.

## 3. C3c 2021: reference-window mismatch (amendment case for the desk)

The **RT reference window** is the set of hours where `actual_lmp_hourly_CAISO.parquet` carries an RT price. For 2021
that starts at hour 2,783 (2021-04-26 23:00) and covers 5,713 hours (65.2 %), because OASIS GroupZip serves nothing
earlier and R-16 refused the paid history.

The scorer (`_tail_hours`) counts the model over all 8,760 hours and the actual over the covered hours only. All 88
model tail hours (keeper arm 2) fall on 2021-02-13…17, which is Winter Storm Uri. The model is pricing the measured
$39–44/MMBtu citygate print (0d). That is outside the window.

Census (`_c3c_window.py`) of every partially covered scored ISO-year at its keeper:

| ISO-year | RT coverage | model, all hours | **model, RT hours** | actual RT | status effect of masking |
|---|--:|--:|--:|--:|---|
| **CAISO 2021** | 0.652 | 88 | **0** | 27 | over-fire 3.26× → **under-fire 0 vs 27** (C3c-2024 class) |
| CAISO 2023 | 0.995 (Jan 4 & 11 missing) | 67 | 51 | 47 | PASS → PASS (1.43× → 1.09×) |
| MISO 2022 | 0.863 | 0 | 0 | 116 | none |
| SPP 2019–25 | 0.999 | 0 / 0 / 374 / 0… | identical | | none |

Every other scored ISO-year has full coverage. **The defect is live only in CAISO 2021**, and it moves the CAISO 2023
count without changing its status.

**The honest reading of C3c 2021:** model 0 vs actual 27 on like-for-like hours. That is an under-fire on the
summer/autumn evening events, the same model class as the ledgered C3c 2024 (0 vs 35 h, import-parity scarcity the LP
does not price). The Uri hours are a reference gap, not tail evidence.

## 4. Matrix and DO-NOT-REDO

No mechanism was tested, so no CAISO cell moves. The (a) and (c) readings sit under existing adjudications:
caiso-185/186 (R), gas_commitment_bridge (K) and caiso-276. No DO-NOT-REDO item was re-run: no topology, export
sink, two-settlement, CC must-run, CC winter capability, `caiso_ra_min_load_frac` re-derive, OASIS fetch, link-15 or
`zonal_gas_basis` work.
