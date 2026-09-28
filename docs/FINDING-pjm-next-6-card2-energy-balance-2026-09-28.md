# FINDING — PJM-NEXT-6 card 2: the pre-2023 joint CC+coal surplus is carried by the DA virtual layer (zero LP, 2026-09-28)

Keeper `2026-09-27-pjm-next-5-shape` (`results/calibration/pjmnext5_sh_span`). Zero LP throughout.

**Bottom line.** No physical balance input (seams, demand, nuclear, hydro, wind/solar) is wrong in 2019–2022. The measured PJM DA INC/DEC curves themselves net to virtual DEMAND in 2019–22 (+5.5 / +15.1 / +14.8 / +6.8 TWh at actual DA system price) and to net supply in 2023–25. The single-settlement LP serves net DEC with physical thermal, and C1 scores that against RT physical actuals: 18 / 27 / 60 / 44 % of the 2019–22 thermal over-run. There is **no admissible measured-input lever**; the next lever is structural (rule 1) and needs an owner decision + design card.

## Part A — energy-balance decomposition


Keeper bundle: `results/calibration/pjmnext5_sh_span` (P1 hourlies, years 2019–2025). No LP was run, and nothing under `src/` was edited or committed.

## Sources
- **Model:** `hourly/class_hourly_<y>.parquet`, summed per `klass` for P1. It has pseudo-classes `import` (net seam flow; negative means export) and `VIRTUAL_INC`/`VIRTUAL_DEC` (the DA virtual-bid layer). Also `hourly/system_<y>.parquet` (`demand`, with slack and dump both 0) and `hourly/storage_<y>.parquet`.
- **Actual (C1):** `frontend/data/backcast/bench/PJM/<y>.json.gz` → `bench.classFull`. This is the input `score_fuelmix` reads (`scripts/calibration_verdict.py:1695-1790`, `cf = ybench["classFull"]`). It reproduces the card's Δ values exactly: 2019 CC_REGULAR +11.10, COAL_BIT +13.83.
- **Demand and net interchange:** EIA-930 BALANCE `data/raw/eia-930/EIA930_BALANCE_<y>_*.parquet` (PJM, Adjusted columns). Also the PJM tie-line meter `data/raw/iso-specific-transmission/PJM_<y>_import_export_act_sch_interchange.csv` (the sum of `actual_flow` over ties is the net position the seam mechanism uses) and PJM metered load `data/raw/zone-specific-demand/PJM<y>_hrl_load_metered.csv` (`mkt_region == RTO`).

## How the model represents each balance term (file:line)
- **Demand.** This is EIA-930 PJM BA `Demand` from the per-BA hourly extract: `src/market_sim/data/eia930/demand.py:809-852` (`_load_pjm_hourly_demand`), routed at `:1014-1024`. With priced interchange on, the tie-line export is not added to demand: `demand.py:1283-1284` together with `runner.py:517/1527` (`include_interchange=not import_generators`). The model's annual demand matches EIA-930 Adjusted to within ±0.1 TWh, except in leap years, where the model carries 8,760 hours against EIA's 8,784 (2020 −2.95, 2024 −2.18).
- **Seams.** These are priced import/export generators on the `PJM_external` node. Band prices come from the **measured per-year Q-Q ladder** `PJM_SEAM_LADDER_BY_YEAR` (`src/market_sim/model/interchange/spec.py:2601-2690ff`), armed by `pjm_seam_measured_ladder`. That ladder displaces the firm-export floor (`import_nodes.py:1041-1060`). Capacities are limited by per-(month × hod) p90 envelopes built from each year's own tie-line file (`pjm_seam_flow_limit` / `pjm_seam_export_limit`, `scenarios.py:19186-19220`), plus `pjm_external_net_position_cut` (`interchange/pjm.py:335`).
  - The ladder table covers **all of 2019–2025**, verified by import. 2020 was added by pjm-h11 (`spec.py` comment at 2020).
  - The neighbour-hourly sub-gate is off.
  - So the seam is **not** a fixed profile, **not** a pinned EIA-930 series, and **not** a pre-2023 fallback. It is the same measured-ladder supply curve in every year, from same-vintage per-year data.
- **Virtual bids** (`pjm_da_virtual_bids=true` in every `run_config_<y>.json`). The measured submitted DataMiner2 `hrl_da_incs_decs` curves for the solve year enter as a symmetric net rung ladder: `src/market_sim/data/virtual_bids.py:284-400`.
  - A missing month is a hard error (`:223-233`), so the keeper had raw 2019–2022 files. They are gitignored and absent in this container. The README's default fetch covers 2023–2025 only.
  - The docstring's validation that "the net at actual DA prices is ≈ 0" was measured **only for 2023/24/25** (`virtual_bids.py:49-52`, −0.6/−0.9/+1.3 TWh).
  - The frozen surface in `data/raw/_validation-source/pjm_da_virtual_surface_summary.csv` is likewise built from about 26k hours, which is 2023–25.
- **Nuclear, wind, solar, hydro:** wind and solar match actual exactly; nuclear and hydro are pinned or near-pinned (`free_class_score.pinned_classes` in metrics.json).

## Table: model − actual (TWh). The identity closes to ≤0.03 TWh in every year.

Identity: Δthermal = ΔD + ΔX_export + netDEC_virt + storLoss + L_m + U_a − (Δnuc + Δhydro + ΔVRE + Δother)
- L_m is the model's residual: generation + import + virtuals + storage − demand. These are loss terms, 2–4 TWh.
- U_a = D_a + X_a(tie) − Σ classFull. This is the actual energy that the C1-basis generation does not account for.

| year | ΔCC_REG | ΔCOAL_BIT | Δgas fam | Δcoal fam | **Δthermal** | Δnuc | Δhydro | Δother | Δdemand | export m / a | **ΔX** | **net DEC virt** | stor loss | L_m | **U_a** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | +11.10 | +13.83 | +3.10 | +12.60 | **+15.70** | −0.93 | +0.09 | +1.36 | −0.06 | 19.67 / 31.56 | −11.89 | **+2.77** | 1.46 | 2.17 | **21.77** |
| 2020 | +16.95 | +2.44 | +13.14 | +1.69 | **+14.83** | −3.70 | +0.10 | +1.44 | −2.95 | 28.37 / 41.68 | −13.31 | **+3.96** | 1.44 | 2.14 | **21.38** |
| 2021 | +7.05 | +18.83 | −1.07 | +20.35 | **+19.28** | +0.21 | +0.09 | +1.44 | +0.01 | 24.84 / 37.81 | −12.97 | **+11.49** | 1.54 | 2.69 | **18.25** |
| 2022 | +13.45 | +8.59 | +15.01 | +9.04 | **+24.05** | +1.31 | +0.08 | +1.86 | −0.07 | 22.27 / 31.77 | −9.50 | **+10.51** | 1.38 | 3.23 | **21.75** |
| 2023 | +6.14 | +0.50 | +4.35 | −0.99 | **+3.36** | −0.55 | −0.08 | +2.29 | −0.04 | 30.19 / 39.97 | −9.78 | **−4.25** | 1.56 | 2.51 | **15.05** |
| 2024 | −4.92 | +0.01 | −1.77 | −1.14 | **−2.91** | −1.78 | 0.00 | +2.22 | −2.18 | 22.02 / 32.87 | −10.85 | **−4.00** | 1.59 | 3.36 | **9.60** |
| 2025 | −10.25 | +9.80 | +2.93 | +10.59 | **+13.52** | −0.71 | −7.05* | +2.25 | +0.07 | 23.71 / 32.92 | −9.21 | **−0.68** | 1.66 | 3.88 | **12.26** |

\* 2025 classFull hydro is 15.51 TWh, against about 8.9 in every other year. This looks like a pumped-storage or basis artifact in the preliminary 2025 benchmark. Wind and solar Δ are 0 (pinned) and are omitted from the table.

Model virtual gross volumes (TWh): DEC / INC
- 2019: 11.2 / 8.5
- 2020: 12.7 / 8.7
- 2021: 15.9 / 4.4
- 2022: 20.0 / 9.5
- 2023: 12.2 / 16.4
- 2024: 15.0 / 19.0
- 2025: 17.2 / 17.9

The model is net-DEC in 2019–22 and net-INC in 2023–25.

## Answers
**(a) Net imports.** The model under-exports in **every** year: −11.9, −13.3, −13.0, −9.5, −9.8, −10.9 and −9.2 TWh against the tie-line meter.
- EIA-930 Total Interchange agrees with the tie meter to ±0.3 TWh in 2019–24. In 2025 EIA-930 reads 17.97, which is an EIA-930 defect; the tie meter reads 32.92.
- Under-exporting *lowers* the generation the model needs, so this channel works *against* the surplus. It is also flat across the split: the pre-2023 mean is −11.9 and the 2023–25 mean is −10.0.
- **Seams are not the channel.**

**(b) Nuclear.** Model − actual is −3.7 to +1.3 TWh with no pre/post pattern. **Not the channel.**

**(c) Demand.** Model demand is EIA-930 BA Demand. It is exact to ±0.1 TWh except for the leap-day truncation, which appears in 2020 and 2024 (one year on each side of the split).
- EIA-930 Demand tracks PJM metered RTO load in every month at a stable +1 TWh/month offset (losses).
- EIA-930's own balance break is in **Net Generation**, not Demand. NG − D − TI is −6.2 TWh in Jan-2019 and −5.9 TWh in Feb-2020, and ≈0 from 2021 on.
- That break distorts the C2/e930 fuel rows for 2019–20. It does not distort model demand. **Not the channel.**

**(d) Closure.** The identity closes to ≤0.03 TWh in every year (table). Pre-2023 mean Δthermal is +18.5 TWh; the 2023–25 mean is +4.7. The +13.8 TWh gap decomposes as:
- **Net virtual DEC:** +10.2 (pre +7.2, post −3.0). This is the largest pre-2023-specific model-side channel, and it peaks in exactly the two biggest-surplus years (2021 +11.5, 2022 +10.5).
- **U_a (benchmark basis):** +8.5 (pre 20.8, post 12.3).
  - 2019–20: about 9–10 TWh of U_a is the EIA-930 NG glitch, which makes true NG ≈ D + X.
  - 2021–25 (where EIA-930 fuel data is clean): U_a shrinks because classFull **gas** runs 5.8 / 16.0 / 12.7 TWh *above* EIA-930 gas in 2023–25, against −1.7 / −0.2 in 2021–22. Coal's 923-vs-930 gap is stable at 7–10 TWh.
  - This is drift in the **actual** (EIA-923 vs EIA-930) basis, not a model input.
- **Offsets:** ΔX −2.0; hydro −2.5 (2025 artifact); L_m −0.7; other −0.7; nuclear +0.2; demand ≈0.

## Verdict
The joint surplus is carried in the balance, not only in the CC-vs-coal ordering, but through none of the physical channels named in the hypothesis. Seams, nuclear, hydro, VRE and demand are uniform or near zero across the split. Two channels differ before and after 2023:
1. **The DA virtual-bid layer, the model-side channel, about 10 TWh.** It clears 2.8–11.5 TWh/yr net virtual demand in 2019–22 and net virtual supply in 2023–25. That energy has to be served by physical thermal, and it is scored against an RT-physical benchmark.
2. **Benchmark-basis drift, about 8.5 TWh.** Pre-2023 the C1 classFull basis sits ~18–22 TWh below D + X_tie; in 2023–25 it sits 10–15 TWh below. Much of the 2023–25 "calibration" comes from classFull gas moving above EIA-930 gas.

**Most likely measured, rule-14-admissible operand:** the **2019–2022 PJM DA virtual-bid curves** (`hrl_da_incs_decs`) entering through `pjm_da_virtual_bids`.
- The layer's admissibility claim ("net at actual DA prices ≈ 0") was validated only on 2023–25 (`virtual_bids.py:49-52`), and the frozen surface uses only 2023–25 hours.
- The next zero-LP test: clear the 2019–22 measured curves at the *actual* hourly DA LMP and compare with the model's +2.8 / +4.0 / +11.5 / +10.5 TWh net DEC.
  - If the measured net is also ≈0, the DEC clearing is an endogenous model-price artifact: the dual sits below DEC bids in off-peak hours.
  - If the measured net is DEC-heavy, then 2019–22 carries a real DA-over-RT depth that an RT-physical C1 cannot reward, and it is a structure question (rule 1), not an input fix.
- This needs the gitignored raw parquets, which are **not present in this container**.
- **No wrong or missing physical balance input** (seams, demand, nuclear, hydro, VRE) exists for the pre-2023 years.
- Separately, the U_a drift says the 2023–25 C1 pass is partly a benchmark-basis effect. It is worth an audit of classFull gas against EIA-930 gas for 2023–25.

## Part B — DA virtual bids cleared at actual DA prices


Probe: `scripts/probes/_pjmnext6_virtual_clearing_probe.py` (new, uncommitted). No LP was run, and nothing under `src/` was edited.

## Data
- **Fetch.** `fetch_pjm_da_virtuals.py --years 2019..2025 --feeds hrl_da_incs_decs`: all 84 months written, 0 errors, in `data/raw/pjm-da-virtuals/` (gitignored).
- **Bids.** Read with the model's own functions:
  - `virtual_bids._load_bids_frame` for the same model-clock join;
  - `_hourly_net_rungs` for the same 8-rung compression.
- **Actual DA price.** Clean `lmp` datatype, `data/clean/lmp/PJM/DAM/lmp_<y>.parquet` (12 hubs, hourly).
  - Primary basis: `energy_usd_per_mwh`. This is PJM's RTO system energy price, identical at every pnode, and matches the RTO-aggregated bid curve.
  - Sensitivity basis: the 12-hub mean total LMP, which includes congestion and losses.
  - The PJM-RTO zonal pnode (`data/raw/pjm-zonal-lmp`) covers only 2023–25 and is not present in this container.
- **Model side.** Keeper `results/calibration/pjmnext5_sh_span/hourly/`, P1.
  - `class_hourly` VIRTUAL_DEC/VIRTUAL_INC gives the keeper's cleared volumes.
  - As a check, I also re-cleared the rungs at the keeper's own zonal duals (`system_<y>`), split by load share exactly as `virtual_bids.py:343`. This reproduces the keeper to ≤0.1 TWh every year, so the clearing code is validated.
- **Published PJM cleared INC/DEC volumes** (IMM State of the Market) are **not in the repo**. Comparison (a) therefore uses gross full-curve clearing at actual prices as the proxy.
  - It is approximate: real clearing is nodal, and up-to-congestion (UTC) transactions are outside this feed.

## Year table (TWh)

| year | submitted DEC / INC | full-curve cleared DEC / INC @ actual sys price | **net @ actual sys** (on / off-pk) | net @ actual hub-mean | rung-form net @ actual | **keeper net** (DEC / INC) | re-clear @ model duals | model − actual price, on / off ($/MWh) |
|---|---|---|---|---|---|---|---|---|
| 2019 | 62.6 / 57.1 | 35.2 / 29.7 | **+5.51** (2.72 / 2.79) | +7.08 | +5.59 | **+2.77** (11.23 / 8.45) | +2.73 | −0.9 / +2.2 |
| 2020 | 78.0 / 58.7 | 41.0 / 25.9 | **+15.10** (9.56 / 5.54) | +16.33 | +15.06 | **+3.96** (12.65 / 8.69) | +3.90 | +2.3 / +4.2 |
| 2021 | 87.1 / 51.4 | 39.2 / 24.4 | **+14.80** (7.99 / 6.81) | +16.40 | +14.83 | **+11.49** (15.85 / 4.36) | +11.40 | −1.0 / +3.1 |
| 2022 | 105.7 / 70.4 | 46.4 / 39.5 | **+6.82** (3.95 / 2.88) | +11.71 | +6.80 | **+10.51** (19.96 / 9.45) | +10.45 | −10.6 / −0.4 |
| 2023 | 91.1 / 80.7 | 42.9 / 47.0 | **−4.09** | −0.82 | −4.03 | **−4.25** | −4.26 | −3.6 / +2.2 |
| 2024 | 114.2 / 97.8 | 48.1 / 55.0 | **−6.89** | −2.11 | −7.02 | **−4.00** | −4.05 | −5.5 / +1.5 |
| 2025 | 132.8 / 103.5 | 51.4 / 59.3 | **−7.92** | −0.84 | −8.06 | **−0.68** | −0.80 | −10.1 / −0.4 |

Notes:
- "Rung-form net" is the model's 8-rung representation cleared at the actual price.
- On-peak means weekday HE8–23.
- In the cleared DEC/INC column, INC means the full-curve INC cleared at that price.
- The rung-form DEC/INC columns in the probe output count only the net region: DEC 9.9/17.4/16.8/12.8 and INC 4.3/2.4/2.0/6.0 for 2019–22.

## Diagnosis
1. **The bid data itself nets to virtual demand in 2019–22.** This is not endogenous to the model.
   - At actual DA prices, the measured curves clear net DEC of **+5.5 / +15.1 / +14.8 / +6.8 TWh** on the system-price basis, or +7.1 / +16.3 / +16.4 / +11.7 on the hub-mean basis.
   - Both on-peak and off-peak are positive.
   - The sign flips to net INC in 2023–25 on both bases.
   - Submitted DEC exceeds submitted INC by 5.5, 19.3, 35.6 and 35.3 TWh in 2019–22.
2. **The model does not over-clear.** It clears *less* net DEC than actual prices imply in 2019 (2.8 vs 5.5), 2020 (4.0 vs 15.1) and 2021 (11.5 vs 14.8), because its off-peak dual sits +2–4 $/MWh *above* actual. Only 2022 is higher (10.5 vs 6.8–11.7), where the on-peak dual is $10.6 below actual.
   - A price-level fix toward actual would therefore *raise* net DEC in 2019–21.
   - **This is not a price-level defect.**
3. **It is a structural question (rule 1).** A cleared DA DEC is financially liquidated in RT: real RT physical generation serves RT load, not DA virtual demand.
   - In the single-settlement LP, physical thermal must generate the net DEC, and C1/C2 score it against RT-physical (EIA-923) generation.
   - The keeper's net DEC therefore carries 2.8 / 4.0 / 11.5 / 10.5 TWh of the 2019–22 Δthermal (+15.7 / +14.8 / +19.3 / +24.1), which is about 18 / 27 / 60 / 44 %.
   - The same defect runs with the opposite sign in 2023–24: net INC displaces about 4 TWh/yr of real physical generation.
   - Rule 1's premise for the layer ("the DA demand side is real market structure", `virtual_bids.py:8-10`) holds for **price formation**, not for **physical energy**.
4. **The admissibility claim is falsified**, both before and after 2023.
   - `virtual_bids.py:49-52` and the log line `:396-397` claim that annual net at actual DA prices is ≈ 0 (−0.6/−0.9/+1.3 for 2023/24/25).
   - For 2019–22 it is +5.5 to +15.1 TWh.
   - For 2023–25 it is ≈ 0 only on a congestion-inclusive basis (hub mean −0.8/−2.1/−0.8). On the system-energy basis it is −4.1/−6.9/−7.9.
   - The layer's premise that "net ≈ 0 so it is energy-neutral" does not hold as a construction property. It was an empirical coincidence of the years tested.
5. **Rule-14 construction check: no cross-year defect.** Each backcast year reads only its own corpus, and no scalar or scaling from 2023–25 is applied to 2019–22.
   - The glob is year-specific (`virtual_bids.py:223`), the model-clock map uses the same year's EIA-930 frame (`:263-274`), and the zone split uses that year's demand (`:343`).
   - `pjm_da_virtual_surface_path` (`scenarios.py:15087`) and the 2023–25 frozen surface are consumed by no code under `src/`: they are forecast-only and unwired.
   - The only 2023–25-only element is the *validation claim* in item 4, not the construction.

## Verdict
The 2019–22 net virtual DEC is **real in the measured bid data**, not a model price-level artifact. **There is no admissible measured-input lever.** The next lever is structural (rule 1): make the virtual layer price-forming but not physical-energy-forming against the RT-physical benchmark, for example by settling the net virtual position financially rather than serving it with physical thermal. It needs a design card before any solve.
