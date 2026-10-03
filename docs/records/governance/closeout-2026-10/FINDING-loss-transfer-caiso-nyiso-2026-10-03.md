# FINDING — closeout-loss-transfer: the CAISO and NYISO generation residuals are the same loss-surface double count as PJM's (ZERO LP)

**Verdict.** Both keepers carry the PJM defect exactly.

- **The residual is the dissipation.** `R = gen + import net − storage net − demand` equals `Σ ε·F` on the
  loss-surface links to ≤ 0.0024 TWh in all 12 ISO-years. The only non-zero gaps are CAISO 2019 and 2020, and
  they equal those years' dump (0.001 / 0.002 TWh).
- **Both demand rows are generator-side.** Each already contains every transmission and distribution loss, so
  the LP's dissipation is counted twice: 0.36–2.42 TWh a year in CAISO and 1.65–2.17 TWh a year in NYISO.
- **What the PJM repair (option A) would do here.** It moves no CAISO gate. In NYISO it is predicted to break
  the keeper's CALIBRATED determination:
  - **C1 ST_GAS 2021 flips PASS→FAIL**, on volume and share. ST_GAS already under-runs, and the repair deepens
    the under-run.
  - **C3a 2025** (now −7.7 %) lands at −9.5 % (slope estimator) to −11.9 % (step estimator) against ±10 %.

Nothing was built, solved, registered or promoted. No matrix shard was edited: the repair lane adds the
CAISO/NYISO `U` cells. Lane closeout-loss-transfer, owner ruling R-59 (2026-10-03): "Fix PJM first, then others
(Recommended)". Method and probe are transferred from
`docs/records/pjm/closeout-pjm-balance/FINDING-closeout-pjm-balance-2026-10-03.md` (PR #7167).

**Probe.** `scripts/probes/_closeout_loss_transfer_trace.py` writes
`results/phase0/governance/_closeout_loss_transfer_trace.json`. It reuses the PJM probe's `balance()`.
- `ε` is rebuilt exactly as `build_caiso_link_loss` / `build_nyiso_link_loss` build it, using the ISO's own
  `_caiso_internal` / `_nyiso_internal` predicate and the FSNO→NP15 row inheritance.
- Flows come from each leg's committed `flows.parquet`, read by full shard SHA. The branches are cut, but the
  commits are still fetchable.

| ISO | keeper | bundle | leg SHAs |
|---|---|---|---|
| CAISO | `2026-10-02-closeout-caiso-w1-arm2` | `results/calibration/closeout_caiso_w1_a2_span` | 2019 `1ca02579594490fff199211726b16eebcb225b65` · 2020 `07535d603a74f94f56ce1ab3bf283942ed469ac4` · 2021 `905067f84abef9f4500dc431cd4ec5da2400438b` · 2022 `3a53b2ceab09756b2d7d03424f70774a50b0ab59` · 2023 `9794740e58ffe46c6a8563d7c23ae7f6cdb981f3` · 2024 `61f6ad9322336d2a17264bce294927626976375c` · 2025 `ebeacb2b9b3555dbfffec665c07cc33a4da07e34` |
| NYISO | `2026-10-02-w0-nyiso` | `results/calibration/w0_nyiso_span` | 2021 `2bf25795eee138dd36914aa79d9e0d9db7834200` · 2022 `ae7708c1b4cfd00d510de8e57b566a17b5f3ce08` · 2023 `95ad95473c6dd2da1d9a225c71dfda1504f6bafc` · 2024 `d96a1edc87967e4140e3630f77d3580467529a20` · 2025 `8025f6d099bb9aacc600674f41cf0d9453e7ef9b` |

Both keepers arm their surface in every year: `caiso_zonal_loss_surface: true` ×7 and
`nyiso_zonal_loss_surface: true` ×5 in `run_config_<Y>.json`.

## 1. The identity closes on the committed bytes

| TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **CAISO** residual R | 0.356 | 0.363 | 0.443 | 2.420 | 0.600 | 2.236 | 2.323 |
| CAISO Σ ε·F | 0.355 | 0.361 | 0.443 | 2.420 | 0.600 | 2.236 | 2.323 |
| CAISO R − Σ ε·F | 0.001 (= dump) | 0.0024 (= dump) | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| CAISO L as % of demand | 0.16 | 0.17 | 0.20 | 1.10 | 0.29 | 1.05 | 1.13 |
| **NYISO** residual R | — | — | 2.167 | 1.926 | 1.654 | 1.889 | 1.727 |
| NYISO Σ ε·F | — | — | 2.167 | 1.926 | 1.654 | 1.889 | 1.727 |
| NYISO R − Σ ε·F | — | — | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| NYISO L as % of demand | — | — | 1.43 | 1.26 | 1.13 | 1.25 | 1.14 |

These are the bare residuals listed in the PJM FINDING §5, now decomposed. Only 3 of the 96,360 hours carry a
gap above 1 MW: the CAISO dump hours in 2019 and 2020.

**Where the loss sits.**
- **NYISO.** It sits on the north→south chain. Every month's gradient is monotone, UW < CH < LH < NYC < LI.
  - `Upstate_West>Capital_Hudson` (Central-East) carries 1.07–1.46 TWh, about two-thirds of the total.
  - `Capital_Hudson>Lower_Hudson` carries 0.40–0.53 TWh.
  - `Lower_Hudson>NYC` carries 0.11–0.18 TWh.
  - Receiving-zone split: Capital_Hudson 61–67 %, Lower_Hudson 22–28 %, NYC 7–9 %, Long Island 1–4 %.
  - The flow-weighted ε is 2.42–2.55 %.
- **CAISO.** There are two regimes, and the step between them is set by the surface, not the flows.
  - **2022, 2024 and 2025** have their own LA_BASIN and SDGE rows (`interpolated=False`). `SP15_rest>LA_BASIN`
    alone dissipates 1.44–1.67 TWh; `ZP26>NP15` (Path 15, S→N) adds 0.30–0.59 TWh.
  - **2019–2021 (pooled `year 0`) and 2023** have LA_BASIN and SDGE `interpolated=True`, equal to SP15_rest. The
    pocket links therefore carry ε = 0, and only the ZP26 links dissipate (0.36–0.60 TWh).
  - Flow on `SP15_rest>LA_BASIN` is a steady 56–62 TWh every year. The 0.4 → 2.4 TWh step is a property of
    surface coverage. This is noted, not acted on: rule 23 forbids re-deriving it against a residual.

## 2. The demand basis already includes losses, in both ISOs

**NYISO.**
- The keeper's demand is the EIA-930 `NYIS` `Demand` cell (`_load_nyiso_hourly_demand`), with
  `priced_interchange` on and `td_loss_factor = 0`. Model demand equals EIA-930 D to ≤ 0.36 TWh.
- That cell closes EIA's own identity `D = NG − TI` (TI = net export) almost exactly:

| TWh | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| EIA-930 NYIS D − (NG − TI) | 0.000 | 0.000 | 0.000 | −0.050 | −0.037 |
| model demand − EIA-930 D | +0.001 | 0.000 | −0.001 | −0.364 | +0.041 |

- NYISO's D is therefore generation at the busbar plus net tie imports: generator-side energy. All NYCA
  transmission and distribution losses are inside it.
- This is also NYISO's own load convention. Zonal integrated real-time load is computed from generation plus
  net zone-boundary interchange, not summed from customer meters.
- The LP dissipates a further 1.65–2.17 TWh a year on top of that.

**CAISO.**
- The keeper's demand is not the raw EIA-930 `CISO` D. It is the caiso-80 supply-consistent series
  (`caiso_supply_consistent_demand: true`, `_load_caiso_supply_consistent_demand`):
  `demand = 930 NetGen − NG_cell + CEMS bench-gas grid + cogen grid + geo/biomass fold-in − TI`.
- That series is generation minus net export by construction, so it is generator-side as well: the energy
  injected to serve CAISO load, losses included.
- The raw cell cannot even be used to test this. EIA-930 CISO `D − (NG − TI)` reads 10.3 / 19.6 / 5.8 / 4.9 /
  5.7 / 9.4 / 1.7 TWh (2019–2025). That is the corrupt NG cell caiso-80 documented
  (`docs/records/caiso/FINDING-caiso80-demand-basis-wedge-2026-07-13.md`), and the reason the keeper replaced it.
- Model demand − EIA-930 D reads +3.1 / −2.4 / −1.8 / −4.1 / −10.7 / −11.3 / −19.1 TWh.

**Answer.** In both ISOs the loss term double-counts, as in PJM (PJM §3(a)). The marginal-vs-average argument
(PJM §3(b)) carries over unchanged: ε is the marginal delivery-factor deviation, about 2× the average I²R loss.

## 3. Attribution, and the effect of the option-A repair

**Repair.** Each zone's P1 demand is reduced by its receiving-side share of Σ ε·F, which nets L out of the
system exactly. Only the committed P1 flows exist (the bundles carry P1 only), so the P1 flows stand in for P0.
At first order the two differ by the P0→P1 flow change.

**Peel.** Each hour's L is taken off the top of the running P1 merit order (`unit_marginal`, highest offer `mc`
first).
- **`econ` peel (headline).** It peels only units that are economically dispatched: `mc ≤ zone price + $1`.
  A unit running above its zone's dual sits on a floor (the CAISO RA must-offer bridge, the NYISO gas bridge) and
  would not back down. The priced import node may peel.
- **`pjm` variant.** It uses the PJM probe's convention (every dispatched non-nuclear, non-hydro, non-import
  unit). It is reported in the JSON. It loads floor-bound units: CT_CHP and CC_CHP in CAISO, ST_GAS
  (1.2–1.6 TWh) in NYISO.

| `econ` peel, TWh | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CAISO CC_REGULAR | 0.11 | 0.10 | 0.17 | 1.09 | 0.22 | 0.77 | 0.89 |
| CAISO import node | 0.09 | 0.07 | 0.12 | 0.66 | 0.16 | 0.61 | 0.87 |
| CAISO CT_PEAKER / CC_CHP | 0.06 / 0.06 | 0.05 / 0.10 | 0.08 / 0.05 | 0.36 / 0.18 | 0.10 / 0.06 | 0.43 / 0.31 | 0.17 / 0.28 |
| NYISO CC_REGULAR | — | — | 0.65 | 0.36 | 0.43 | 0.40 | 0.33 |
| NYISO CC_CHP | — | — | 0.56 | 0.52 | 0.42 | 0.60 | 0.46 |
| NYISO ST_GAS | — | — | 0.46 | 0.44 | 0.51 | 0.53 | 0.51 |
| NYISO CT_PEAKER | — | — | 0.36 | 0.39 | 0.06 | 0.13 | 0.26 |

**C1 re-test.**
- Each class row is re-tested with its volume minus its peel, and with the rubric's own `_gen_totals` model
  generation minus every peeled class it counts. The share leg reproduces the verdict's `share_pp` exactly
  before the change.
- The volume band is `min(max(2 % load, 3 % gen), 8)`.

**C3a: two first-order estimators.**
- **step:** the `econ` peel's mean change in the top economic offer. This is the upper end, because it ignores
  zonal separation.
- **slope:** the keeper's own load-weighted system price regressed on system demand, per month, times the hour's
  loss, then demand-weighted.

| Predicted flips | Row | Now | After repair | Verdict |
|---|---|---|---|---|
| **NYISO 2021 C1 ST_GAS** | volume / share vs ±3.76 TWh / ±3 pp | −3.44 TWh / −2.80 pp PASS | −3.90 / −3.08 **FAIL** (both legs) | **PASS→FAIL** |
| **NYISO 2025 C3a** vs RT, ±10 % | mean LMP | −7.7 % PASS | slope −9.5 % (PASS, 0.5 pt margin) / step −11.9 % **FAIL** | **at risk** |
| NYISO 2021–24 C3a | | +4.3 / −0.7 / +2.0 / −0.8 % | slope +2.7 / −2.4 / +0.7 / −2.7; step −5.5 / −5.7 / −2.3 / −5.9 | PASS holds |
| NYISO C1, all other rows | CC_REGULAR, CC_CHP, CT_PEAKER | PASS | every over-run shrinks (e.g. 2024 CC_REGULAR +2.02 → +1.62) | PASS holds |
| CAISO 2019–21 C1 CC_REGULAR (FAIL) | volume | +5.63 / +13.46 / +6.59 | +5.53 / +13.37 / +6.42 | FAIL holds, barely moves |
| CAISO 2022–25 C1 | all classes | PASS | 2024 CC_REGULAR −1.67 → −2.44 (largest move) | PASS holds |
| CAISO 2022–25 C3a | mean LMP | +8.6 / +7.6 / +6.6 / +6.0 % | slope +7.2 / +7.1 / +4.8 / +4.3; step +6.3 / +6.0 / +2.6 / +2.9 | PASS holds, improves |
| CAISO 2021 C3a | R-40 reference-coverage caveat | +12.6 % | +11.7 to +12.4 % | unchanged status |

**Reading.**
- **CAISO.** The double count is real but small where the open fails sit. In 2019–21 the pooled surface
  dissipates only 0.36–0.44 TWh, and CC_REGULAR carries 0.10–0.17 TWh of that, about 2 % of the 5.6–13.5 TWh
  over-runs. The CAISO C1 object is elsewhere. In 2022–25 the repair lowers mean LMP by $0.3–1.9/MWh, which
  helps C3a: the keeper over-prices by 6–9 %.
- **NYISO.** The keeper is CALIBRATED. Because ST_GAS and 2025 prices already sit low, removing about 1.2 % of
  load is predicted to move it out of band in at least one row: 2021 ST_GAS C1, and possibly 2025 C3a. Under
  rule 30 the ISO determination would fall CALIBRATED → NOT-YET. Under rule 1, the repair is still the
  structurally right move. Read the flip as a predicted cost for the owner's decision card, not as a reason to
  keep the double count.

**Caveat (as PJM §6).** These are first-order estimates. A re-solve reprices every hour, can reorder the gas
margin, and moves NYISO's bridge floors through the P0 seam. The ST_GAS flip margin is 0.14 TWh on volume and
0.08 pp on share. The C3a 2025 range straddles the band. Both need the full-span solve the repair lane runs
(rule 29), not this table.

## 4. For the repair lane (closeout-PJM-lossdemand) and the desk

- The option-A mechanism transfers unchanged. It needs the receiving-zone share of P0 Σ ε·F in the zone's P1
  demand row, ISO-scoped, with the CAISO/NYISO matrix cells entering as `U` (rule 28).
- In NYISO, about two-thirds of the decrement lands in Capital_Hudson. In CAISO it lands in LA_BASIN (2022/24/25)
  or in NP15/SP15_rest (other years).
- **Pre-register for NYISO** the gates this table names: C1 ST_GAS 2021 and C3a 2025.
- **CAISO** is a low-risk transfer. No predicted flip; C3a improves.
