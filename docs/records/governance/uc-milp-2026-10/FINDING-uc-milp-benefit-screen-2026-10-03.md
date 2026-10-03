# FINDING — UC-0 benefit screen: which ISO-years a MILP unit-commitment stage would move (zero LP)

**Lane:** UC-0 · **Session:** `session_013gHAT8qbNZwry6tA92gYNq` (Fable) · **Date:** 2026-10-03 · **Branch:** `claude/ucmilp-0-benefit-screen-tx8t` off `origin/main` `cd7382f5`.
**Pre-declaration:** `PREDECL-uc-milp-benefit-screen-2026-10-03.md` (same directory; pushed and blob-verified `5b496292` before any number below existed). Every threshold, the ranking rule and the selection rule are GATESPEC §1 verbatim; the open-clause readings R-a..R-j and the physics table are the PREDECL's. Nothing was moved after the numbers came in.
**Instrument:** `scripts/probes/_ucmilp_benefit_screen.py` → `results/phase0/xiso/_ucmilp_benefit_screen.json` (committed beside this file). Zero LP. Inputs: the nine committed keeper bundles (PREDECL table), `data/raw` actuals, the committed bench CEMS series. Runtime ≈ 25 min on the container.
**Data profile:** `code` + keeper bundles; the container carried the full `data/raw` tree, so no `hydrate_data.py` call was needed. Subtrees read: `_validation-source` (RT prices), `campd-unit-level` (no-load regression), `_processed-legacy` (CAMPD derives, EIA-923 costs), `PJM-AS`, `MISO-AS`, `spp-or-mcp`, `NYISO-AS`, `CAISO-AS`, `ercot`/`ercot-AS` (AS clearing prices).

## 0. The answer

| | |
|---|---|
| **Selection (GATESPEC §1 rule, applied as declared)** | targets **SPP 2020**, **PJM 2022**, **SPP 2019**; controls **NEISO 2023**, **NYISO 2024** |
| rankable failing cells | 15 (of 61 board cells; 55 scoreable) |
| eligible failing cells | 14 — the eligibility bar (S2 ≥ 1.0 TWh or M4 gap ≥ 0.20) excludes only NWPP 2024 |
| the screen did **not** fail (GATESPEC §2) | but see §2 F1–F3: the primary score is not discriminating and two of the three selected targets fail their price gate in the direction a UC moves *away* from |

**Three findings the desk needs before UC-1 is chartered.**

1. **The trough residual is model-wide, not failing-year-specific (F1).** The lower-tercile error is positive (model above actual RT) in all 55 scoreable cells, controls included: NEISO 2023 +$9.9/MWh, NYISO 2024 +$6.7/MWh — the same magnitude as the targets' +$13–14. S1 therefore ranks failing cells by a feature every cell shares. The UC's hypothesized price effect (thermal held online at min-load depresses troughs) points the right way everywhere, but the calibrated ISOs pass C3a only because their upper tercile is *negative* and offsets the trough excess. Their C3a headroom is tight: NEISO 2023 sits at −3.0 % (−$2.7/MWh of annual mean to the −10 % band edge), NYISO 2024 at −0.8 %. A UC that removes half the targets' trough excess (−$7 on a third of the hours ≈ −$2.3 on the annual mean) would consume nearly all of NEISO's headroom if it acted the same way there. The UC-2 control bar (no flip, |ΔC3a| ≤ 1 pp) is the binding risk, not a formality.
2. **Two of the three selected targets fail C3a in the "model low" direction (F2).** PJM 2022 (model −16.7 %, upper tercile −$35), and — among the next in rank — PJM 2025 (−11.6 %), SPP 2024 (−11.2 %), SOCO 2022, ERCOT 2023/2024, NWPP 2023/2024, MISO 2021 (C3b with upper −$23). Lowering trough prices worsens every one of those C3a readings; only their C3b (shape) and the low-price count ratio (M3: model has 0–15 % of the actual ≤ $15 hours in PJM/SPP) can improve. The cells whose failing C3a is **model-high** (a trough fix helps the gate) are SPP 2019 (+12.2 %), SPP 2020 (+27.7 %), MISO 2020 (+10.2 %), CAISO 2021 (+12.6 %, 50 % RT coverage) and the two ERCOT C3b-only years. The declared rule selects by |S1| regardless of direction; the UC-1 PRECOMMIT must therefore fix PJM 2022's target reading on C3b and the ≤ $15-hour ratio, never on C3a, or the desk may rule to substitute the next model-high cell (MISO 2020, rank 14) — a ruling, not something this lane does.
3. **The DP bound says the *added* commitment is small and the *removed* is uninterpretable at fixed prices (F6).** Added energy (DP on, keeper off) is ≤ 0.9 TWh in 53 of 61 cells (MISO 2021–22 coal/ST_GAS 4–7 TWh is the exception); the DP decommits tens of TWh everywhere because the keeper's P1 offers leave the LP's own marginal tranches zero rent by duality, so any positive no-load cost switches them off — a fixed-price artifact (and a double count: the P1 `mc` already carries the amortized start markup the UC would zero). The honest reading is the SPP-102 one: a UC with these physics would add little energy at the keeper's prices; what it changes is *which* units are on and at what price they are offered. The 36-h form is further flawed for coal: with UT = 36 h > the window, the rolling DP never sees a start pay back (coal removed 38 TWh in SPP 2019 h36 vs 22 PF) — an engine design flag for UC-1 (E2: look-ahead must cover the longest UT in the integer set, or coal starts need a longer horizon rule).

Everything else the charter asked for is below: the board (§1), the per-ISO-year readings (§2–3), the rule-19 census (§4), the DOF draft (§5), the ASSESSMENT §6 confirm/refute (§6), the data gaps (§7), the log entry (§8).

## 1. The board (GATESPEC §6.2)

Cell = **S1 / S2** with S1 in thousand $·h (sign: `+` model above actual RT in the lower tercile — every cell), S2 in TWh; `[gates; E]` = failing gates per PREDECL R-a (`ok` none, `n/s` unscoreable) and eligibility (`E` eligible, `x` not). Bold = failing cell. M6 = integer clusters (slow-start plants) and their peak available MW in the first year.

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | M6 clusters (MW) |
|---|---|---|---|---|---|---|---|---|
| ERCOT | **13.9+ / 10.2** [C3b;E] | **15.6+ / 9.8** [C3b;E] | 94.4+ / 11.2 [ok;E] | 44.3+ / 11.0 [ok;E] | **20.5+ / 9.8** [C3a,C3b;E] | **23.2+ / 8.3** [C3a;E] | 22.7+ / 8.7 [ok;E] | 73 (59.7 GW) |
| PJM | 15.5+ / 3.1 [ok;E] | 17.8+ / 3.7 [ok;E] | 24.0+ / 3.9 [ok;E] | **41.0+ / 3.2** [C3a,C3b;E] | 29.1+ / 4.2 [ok;E] | 29.4+ / 2.5 [ok;E] | **32.5+ / 2.4** [C3a,C3b;E] | 155 (106.0 GW) |
| CAISO | — / 2.0 [n/s;E] | — / 2.0 [n/s;E] | **22.5+ / 1.9** [C3a;E] | 46.4+ / 2.3 [ok;E] | 34.2+ / 2.2 [ok;E] | 28.5+ / 2.0 [ok;E] | 22.3+ / 2.2 [ok;E] | 32 (17.2 GW) |
| NYISO | — | — | 35.2+ / 1.5 [ok;E] | 67.3+ / 0.7 [ok;E] | 27.7+ / 1.1 [ok;E] | 19.5+ / 0.7 [ok;x] | 25.8+ / 0.5 [ok;E] | 32 (14.5 GW) |
| NEISO | 30.8+ / 2.8 [ok;E] | 19.7+ / 4.8 [ok;E] | 32.6+ / 2.8 [ok;E] | 75.7+ / 1.8 [ok;E] | 29.1+ / 1.5 [ok;E] | 29.9+ / 1.4 [ok;E] | 46.4+ / 1.6 [ok;E] | 37 (16.4 GW) |
| MISO | 13.9+ / 9.6 [ok;E] | **14.9+ / 9.3** [C3a;E] | **21.4+ / 10.5** [C3b;E] | 16.6+ / 9.0 [ok;E] | 17.4+ / 4.1 [ok;E] | 15.6+ / 3.4 [ok;E] | 24.5+ / 4.4 [ok;E] | 159 (90.4 GW) |
| SPP | **38.4+ / 2.9** [C3a;E] | **41.6+ / 3.3** [C3a,C3b;E] | 43.1+ / 5.5 [ok;E] | 29.6+ / 6.3 [ok;E] | 28.3+ / 4.7 [ok;E] | **31.4+ / 4.5** [C3a,C3b;E] | 37.3+ / 4.9 [ok;E] | 86 (38.2 GW) |
| SOCO | 17.5+ / 3.1 [ok;E] | 13.2+ / 2.4 [ok;E] | 11.0+ / 4.1 [ok;E] | **31.0+ / 4.6** [C3a,C3b;E] | 15.5+ / 1.6 [ok;E] | 16.2+ / 1.7 [ok;E] | 19.6+ / 2.6 [ok;E] | 31 (35.8 GW) |
| NWPP | — / 1.1 [n/s;E] | — / 1.4 [n/s;E] | — / 1.9 [n/s;E] | — / 2.6 [n/s;E] | **18.1+ / 1.7** [C3b;E] | **24.1+ / 0.8** [C3a,C3b;x] | 26.2+ / 1.9 [ok;E] | 45 (22.6 GW) |

**Ranking (every rankable cell, by S1 then S2 then M1):**
| rank | ISO-year | S1 $·h | sign | S2 TWh | M1 TWh | M4 gap | gates | eligible |
|---|---|---|---|---|---|---|---|---|
| 1 | SPP 2020 | 41647 | model high | 3.32 | 1.71 | 0.918 | C3a,C3b | True |
| 2 | PJM 2022 | 40991 | model high | 3.18 | 1.42 | 0.413 | C3a,C3b | True |
| 3 | SPP 2019 | 38410 | model high | 2.94 | 1.01 | 0.909 | C3a | True |
| 4 | PJM 2025 | 32482 | model high | 2.44 | 1.61 | 0.220 | C3a,C3b | True |
| 5 | SPP 2024 | 31405 | model high | 4.54 | 2.55 | 0.363 | C3a,C3b | True |
| 6 | SOCO 2022 | 31033 | model high | 4.64 | 1.29 | — | C3a,C3b | True |
| 7 | NWPP 2024 | 24144 | model high | 0.80 | 1.21 | — | C3a,C3b | False |
| 8 | ERCOT 2024 | 23188 | model high | 8.32 | 5.09 | 0.739 | C3a | True |
| 9 | CAISO 2021 | 22465 | model high | 1.89 | 8.53 | 0.321 | C3a | True |
| 10 | MISO 2021 | 21378 | model high | 10.51 | 4.67 | — | C3b | True |
| 11 | ERCOT 2023 | 20470 | model high | 9.80 | 4.92 | 0.972 | C3a,C3b | True |
| 12 | NWPP 2023 | 18127 | model high | 1.69 | 1.48 | — | C3b | True |
| 13 | ERCOT 2020 | 15620 | model high | 9.83 | 5.47 | 0.975 | C3b | True |
| 14 | MISO 2020 | 14854 | model high | 9.35 | 3.58 | — | C3a | True |
| 15 | ERCOT 2019 | 13859 | model high | 10.21 | 4.23 | 0.957 | C3b | True |
Probe output: selection {'targets': [['SPP', 2020], ['PJM', 2022], ['SPP', 2019]], 'controls': [['NEISO', 2023], ['NYISO', 2024]], 'eligible_failing_cells': 14, 'rankable_cells': 15, 'fallback_highest_s1': []}



**Selection by the declared rule:** targets SPP 2020 (S1 41.6 k, S2 3.3, M4 gap 0.92), PJM 2022 (41.0 k, 3.2, 0.41), SPP 2019 (38.4 k, 2.9, 0.91); controls NEISO 2023, NYISO 2024. Ties: none within 1 %. Fallback (GATESPEC §2) not triggered.

## 2. Readings of the metrics across the board

| # | Reading | Evidence (JSON keys `isos.<ISO>.years.<y>.*`) |
|---|---|---|
| F1 | **M3 lower-tercile error positive in 55/55 scoreable cells**, +$3.8 to +$32/MWh; controls +$6.7 (NYISO 2024) and +$9.9 (NEISO 2023). The model under-produces low-price hours everywhere: model/actual count of ≤ $15 hours is 0.00–0.04 in PJM, MISO, NYISO and SOCO, 0.00–0.43 in NEISO, 0.03–0.44 in SPP, 0.00–0.36 in ERCOT, 0.53–0.70 in CAISO. Negative hours: ratio ≤ 0.11 outside CAISO/SPP 2022+. | `m3.lower_mean_err`, `m3.ratio_le15`, `m3.ratio_neg` |
| F2 | **Direction of the failing C3a** (model/actual − 1): model-high SPP 2019 +12.2 %, SPP 2020 +27.7 %, MISO 2020 +10.2 %, CAISO 2021 +12.6 %; model-low PJM 2022 −16.7 %, PJM 2025 −11.6 %, SPP 2024 −11.2 %, SOCO 2022 −13.7 %, ERCOT 2023 −24.7 %, ERCOT 2024 −11.3 %, NWPP 2024 −25.3 %. C3b-only: ERCOT 2019/2020 (+6.1 %/+2.5 %), MISO 2021 (−8.4 %), NWPP 2023 (−3.2 %). | `gates.c3a_model/actual` |
| F3 | **S2 ≥ 1.0 TWh in 57/61 cells** — the eligibility bar does not discriminate at the keeper's grain. Composition differs: ERCOT S2 ≈ 8–11 TWh is 74–96 % M2(b) (keeper CC online at ≤ 0.67 × available cap while CEMS is off: the `gas_commitment_bridge` + committed tranche holding CC that the real fleet shut down; 9.3 TWh in 2019); MISO 2019–22 (9–10.5 TWh) is 53–75 % M2(b), of which coal PRB/BIT/lignite 3.7–6.6 TWh; SPP, PJM, SOCO are balanced 1–3 TWh each side; NYISO, NWPP, CAISO are mostly M2(a) (CEMS online at part load, model off — 1.0–2.5 TWh). | `classes.<g>.m2a_twh / m2b_twh` |
| F4 | **M1 cycling** — where no floor holds CC the model cycles it 1.3–2.6× more than CEMS (CAISO 8,700 vs 3,289 starts in 2021; MISO 2,893 vs 1,902; SPP 2,073 vs 1,211; NEISO 2,822 vs 2,267; NYISO 1,605 vs 740); where a floor holds it the model under-cycles (ERCOT CC 491 vs 3,070). Energy inside on-runs shorter than UT is ≤ 2 % of class energy except CAISO CC (8.4 TWh, 14.6 % — the bridge's P0 runs are short) and ERCOT ST_GAS (29.5 %). | `m1_starts_model/cems`, `m1_short_on_twh` |
| F5 | **M4 reserve dormancy** — model reserve MCP < $1 in 96–100 % of hours in every ISO with a reference; actual dormancy: SPP 8–9 % (2019–20) → 64–67 % (2024–25), ERCOT 0–1 % (2019–23), MISO 35–49 % (2023–25), CAISO 28–69 %, PJM 56–87 %, NYISO 68–85 %. Gap ≥ 0.20 in SPP (all years), ERCOT (all), CAISO (all with a reference), MISO 2023–25, PJM 2020–22/2024–25, NYISO 2022/2025. | `m4.*` |
| F6 | **M5 DP bound** — added (DP on, keeper off) ≤ 0.9 TWh in 53/61 cells; MISO 2021 4.3 TWh and 2022 6.7 TWh (coal PRB/BIT and ST_GAS at 2022 gas prices). Precision of added low-price hours against CEMS: SPP ST_GAS 0.64–0.79, SPP CC 0.43–0.47, ERCOT CC 0.34, MISO CC 0.22, CAISO CC 0.00. Removed 10–84 TWh per ISO-year (see §0 item 3 for why it is not a bound). h36 removes more than PF wherever UT > 24 h (coal, NREL ST_GAS 24 h). | `m5.pf / m5.h36` |
| F7 | **No-load regression** (B0 construction): 55–356 CAMPD units per ISO-year, 73–99 % fitted, R² median 0.96–0.99; plants without a fit take the class mean per MW (worst: PJM 2019 COAL_BIT 18 plants, SPP ST_GAS 12 of 32). | `noload_fit`, `classes.<g>.noload_fallback_plants` |
| F8 | **M6 clusters** (integers per 36-h window = clusters × 36): PJM 155 (106 GW; 5,580), MISO 159 (90 GW; 5,724), SPP 86 (38 GW), ERCOT 73 (60 GW), NWPP 45, NEISO 37, CAISO 32, NYISO 32, SOCO 31. Plant-level clusters; unit-count clusters would be 2–4× more. | `classes.<g>.m6_*` |

## 3. Per-ISO-year detail (one block per ISO; per-class rows for the first failing year, else 2023)

Columns: M3 lower-tercile mean error (hours), mid/upper tercile error, model/actual count ratios, M4 model/actual dormant share (coverage), M2(a)/M2(b), M1 short-run TWh, starts model/CEMS, M5 perfect-foresight and 36-h Δ with added/removed, no-load fit. "Δ" in M5 also carries in-merit output differences where both schedules are on, so added/removed are the clean terms.


### ERCOT (2026-10-02-closeout-l1-coal-fuel) committed_pct plants 0
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 4.75 (2921) | 3.5/3.1 | 0.14 (219/1558) | 0.04 | 0.96/0.00 (1.00) | 0.37 / 9.84 | 4.23 | 2663/4121 | -30.5 (0.3/35.5) | -54.4 (0.23/56.8) | 203/197 (0.97) |
| 2020 | 5.35 (2921) | 3.6/-1.1 | 0.36 (1175/3276) | 0.00 | 0.98/0.00 (1.00) | 0.65 / 9.18 | 5.47 | 4529/4479 | -35.4 (0.5/42.1) | -61.7 (0.26/65.0) | 201/188 (0.98) |
| 2021 | 32.33 (2920) | 17.7/-32.3 | 0.01 (10/1171) | 0.02 | 0.97/0.00 (1.00) | 2.69 / 8.54 | 4.12 | 5993/4938 | -38.4 (0.9/44.0) | -54.0 (0.58/57.7) | 199/190 (0.97) |
| 2022 | 15.18 (2920) | 5.9/-22.4 | 0.00 (3/693) | 0.02 | 0.97/0.01 (1.00) | 1.50 / 9.52 | 2.53 | 3751/4995 | -46.5 (0.4/55.7) | -54.3 (0.26/62.4) | 200/190 (0.98) |
| 2023 | 7.01 (2920) | 3.9/-34.8 | 0.15 (298/1988) | 0.29 | 0.98/0.01 (0.75) | 1.01 / 8.80 | 4.92 | 4422/3672 | -41.4 (0.3/44.4) | -60.4 (0.23/62.1) | 191/189 (0.98) |
| 2024 | 7.94 (2921) | 4.4/-14.1 | 0.34 (890/2660) | 0.07 | 0.99/0.26 (0.83) | 1.51 / 6.81 | 5.09 | 4749/3060 | -37.0 (0.3/39.0) | -53.4 (0.18/54.5) | 192/188 (0.98) |
| 2025 | 7.78 (2920) | 4.3/-12.8 | 0.26 (300/1154) | 0.02 | 1.00/0.52 (0.84) | 2.22 / 6.44 | 4.30 | 4648/3581 | -30.8 (0.2/37.0) | -42.8 (0.14/47.6) | 192/185 (0.98) |

per-class (year = first failing year or 2023):
| class (2019) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 43 (37) | 141.9 | 50/8/6/0.57 | 0.05 (0.000) | 491/3070 | 0.07 / 9.34 | 3.16 | -14.4 0.07/17.7 | -25.21 | -26.3 | 0.34 |
| COAL_LIGNITE | 3 (3) | 16.3 | 100/36/16/0.40 | 0.03 (0.002) | 53/23 | 0.03 / 0.00 | 0.09 | -1.0 0.00/1.3 | +0.14 | -1.3 | 1.00 |
| COAL_PRB | 8 (8) | 50.5 | 100/36/16/0.40 | 0.02 (0.000) | 87/17 | 0.00 / 0.04 | 0.01 | -8.7 0.00/10.0 | -7.59 | -19.6 | — |
| ST_GAS | 19 (15) | 14.0 | 35/24/8/0.12 | 4.14 (0.295) | 2032/1011 | 0.27 / 0.46 | 1.55 | -6.4 0.27/6.4 | -1.13 | -7.1 | 0.33 |

### PJM (2026-10-03-closeout-pjm-nuc-keeper) committed_pct plants 188
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 5.31 (2920) | 4.2/-4.6 | 0.00 (0/615) | 0.00 | 1.00/0.81 (1.00) | 1.64 / 1.47 | 1.79 | 5514/3043 | -82.2 (0.3/83.2) | -133.0 (0.03/133.3) | 356/267 (0.97) |
| 2020 | 6.09 (2920) | 4.9/-2.3 | 0.04 (98/2272) | 0.00 | 1.00/0.70 (1.00) | 1.76 / 1.96 | 2.62 | 6184/3360 | -69.9 (0.3/71.0) | -119.6 (0.02/119.8) | 328/272 (0.97) |
| 2021 | 8.22 (2920) | 6.1/-9.4 | 0.00 (0/91) | 0.00 | 1.00/0.56 (1.00) | 1.86 / 2.01 | 2.10 | 5437/4091 | -76.2 (0.2/76.5) | -109.9 (0.00/109.9) | 323/271 (0.97) |
| 2022 | 14.04 (2920) | 8.7/-35.2 | 0.00 (0/31) | 0.00 | 1.00/0.59 (1.00) | 1.52 / 1.66 | 1.42 | 4361/4109 | -67.6 (0.2/67.8) | -80.4 (0.07/80.4) | 321/277 (0.97) |
| 2023 | 9.95 (2920) | 5.8/-8.8 | 0.00 (0/769) | 0.00 | 1.00/0.87 (1.00) | 2.32 / 1.85 | 1.51 | 4711/3301 | -83.9 (0.1/84.3) | -106.8 (0.00/107.2) | 308/266 (0.97) |
| 2024 | 10.07 (2920) | 5.7/-12.8 | 0.00 (0/1334) | 0.00 | 1.00/0.78 (1.00) | 1.13 / 1.39 | 1.54 | 4185/3170 | -53.9 (0.1/54.3) | -84.3 (0.03/84.6) | 297/262 (0.96) |
| 2025 | 11.12 (2920) | 7.8/-20.2 | 0.00 (0/156) | — | 1.00/0.78 (1.00) | 1.11 / 1.33 | 1.61 | 3445/2934 | -39.3 (0.1/39.2) | -55.6 (0.01/55.6) | 295/269 (0.97) |

per-class (year = first failing year or 2023):
| class (2022) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 70 (70) | 305.2 | 50/11/6/0.44 | 0.84 (0.003) | 3319/3146 | 1.33 / 1.17 | 4.94 | -59.2 0.17/59.4 | -11.96 | -68.1 | — |
| COAL_BIT | 44 (37) | 149.7 | 100/36/16/0.40 | 0.37 (0.003) | 305/316 | 0.03 / 0.39 | 1.42 | -1.9 0.03/2.0 | -0.48 | -4.7 | — |
| COAL_PRB | 4 (4) | 12.0 | 100/36/16/0.40 | 0.01 (0.001) | 20/36 | 0.00 / 0.01 | 0.11 | -0.9 0.00/0.8 | -0.02 | -1.7 | — |
| COAL_WC | 11 (11) | 6.5 | 100/36/16/0.40 | 0.00 (0.001) | 44/191 | 0.00 / 0.00 | 0.06 | -0.1 0.00/0.1 | -0.00 | -0.3 | — |
| ST_GAS | 12 (11) | 8.5 | 35/11/8/0.13 | 0.20 (0.024) | 673/420 | 0.17 / 0.09 | 1.46 | -5.4 0.00/5.4 | -0.56 | -5.6 | — |

### CAISO (2026-10-02-closeout-caiso-w1-arm2) committed_pct plants 83
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | — (—) | —/— | — (—/—) | — | —/— (—) | 0.71 / 1.32 | 6.49 | 7554/2841 | -22.5 (0.3/22.7) | -25.7 (0.16/25.9) | 71/68 (0.98) |
| 2020 | — (—) | —/— | — (—/—) | — | 1.00/0.28 (0.76) | 0.58 / 1.42 | 8.19 | 8363/3319 | -20.5 (0.5/21.0) | -28.6 (0.25/28.9) | 70/68 (0.98) |
| 2021 | 11.79 (1905) | 9.5/-0.5 | 0.53 (134/254) | 0.61 | 1.00/0.68 (0.50) | 0.60 / 1.29 | 8.53 | 8899/3466 | -22.4 (0.5/22.9) | -23.5 (0.46/24.0) | 68/66 (0.98) |
| 2022 | 15.89 (2920) | 11.9/-1.0 | 0.70 (439/624) | 0.80 | —/— (—) | 0.81 / 1.46 | 10.34 | 10158/3772 | -29.4 (0.2/29.6) | -29.9 (0.18/30.1) | 70/68 (0.98) |
| 2023 | 11.76 (2904) | 5.7/-7.0 | 0.60 (626/1035) | 0.75 | 1.00/0.51 (1.00) | 1.15 / 1.09 | 7.49 | 9593/3573 | -22.6 (0.6/23.2) | -23.7 (0.55/24.2) | 70/68 (0.98) |
| 2024 | 9.77 (2920) | 3.7/-6.5 | 0.64 (1024/1607) | 0.77 | 1.00/0.69 (1.00) | 0.67 / 1.29 | 7.30 | 9882/2919 | -26.0 (0.5/26.5) | -28.1 (0.37/28.5) | 67/59 (0.97) |
| 2025 | 7.63 (2920) | 3.1/-6.4 | 0.65 (869/1328) | 0.91 | 1.00/0.61 (1.00) | 0.68 / 1.57 | 6.34 | 9328/2842 | -31.0 (0.2/31.2) | -32.3 (0.17/32.4) | 67/56 (0.96) |

per-class (year = first failing year or 2023):
| class (2021) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 28 (25) | 57.3 | 50/13/6/0.26 | 8.37 (0.146) | 8700/3289 | 0.44 / 1.29 | 4.57 | -22.2 0.51/22.8 | -3.02 | -23.3 | 0.00 |
| COAL_BIT | 1 (0) | 0.1 | 100/36/16/0.40 | 0.00 (0.000) | 0/0 | 0.00 / 0.00 | 0.00 | +0.0 0.00/0.0 | +0.00 | +0.0 | — |
| ST_GAS | 4 (4) | 0.2 | 35/10/8/0.10 | 0.16 (1.000) | 199/177 | 0.17 / 0.00 | 1.06 | -0.2 0.00/0.2 | -0.00 | -0.2 | — |

### NYISO (2026-10-02-w0-nyiso) committed_pct plants 63
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2021 | 12.05 (2920) | 8.4/-3.8 | 0.00 (0/689) | 0.00 | 1.00/0.85 (1.00) | 0.70 / 0.82 | 1.23 | 2019/978 | -13.4 (0.1/13.4) | -15.8 (0.02/15.8) | 95/73 (0.98) |
| 2022 | 23.04 (2920) | 17.1/-18.9 | 0.00 (0/50) | 0.00 | 1.00/0.79 (1.00) | 0.54 / 0.14 | 0.76 | 1573/926 | -11.1 (0.0/10.9) | -11.6 (0.01/11.4) | 89/71 (0.99) |
| 2023 | 9.48 (2920) | 6.2/-5.8 | 0.00 (0/450) | 0.00 | 1.00/0.83 (1.00) | 0.65 / 0.48 | 2.35 | 2594/926 | -16.0 (0.1/16.0) | -18.1 (0.05/18.0) | 88/73 (0.97) |
| 2024 | 6.68 (2920) | 4.1/-5.5 | 0.00 (0/171) | 0.00 | 1.00/0.83 (1.00) | 0.53 / 0.13 | 1.34 | 2499/811 | -10.7 (0.1/10.3) | -13.8 (0.04/13.6) | 88/72 (0.98) |
| 2025 | 8.85 (2920) | 3.7/-14.3 | 0.00 (0/136) | 0.00 | 1.00/0.68 (1.00) | 0.44 / 0.10 | 0.93 | 2257/1014 | -11.9 (0.0/11.5) | -13.8 (0.03/13.4) | 85/76 (0.98) |

per-class (year = first failing year or 2023):
| class (2023) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 21 (20) | 31.8 | 50/21/6/0.52 | 1.51 (0.047) | 1605/740 | 0.29 / 0.07 | 1.80 | -7.9 0.11/8.0 | -0.32 | -9.4 | — |
| ST_GAS | 11 (11) | 11.6 | 35/13/8/0.24 | 0.84 (0.073) | 989/186 | 0.37 / 0.41 | 1.43 | -8.1 0.03/8.0 | -0.64 | -8.6 | — |

### NEISO (2026-10-02-w0-neiso) committed_pct plants 43
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 10.56 (2920) | 6.4/-7.5 | 0.35 (264/754) | 0.00 | —/— (—) | 0.41 / 2.35 | 0.55 | 3674/2905 | -28.5 (0.2/29.4) | -34.9 (0.04/35.3) | 66/58 (0.97) |
| 2020 | 6.75 (2922) | 4.0/-8.7 | 0.02 (47/2326) | 0.00 | —/— (—) | 0.42 / 4.34 | 0.56 | 2927/2307 | -27.9 (0.0/28.6) | -35.6 (0.00/35.9) | 67/57 (0.97) |
| 2021 | 11.15 (2920) | 8.3/-10.7 | 0.01 (1/154) | 0.03 | —/— (—) | 0.43 / 2.39 | 0.84 | 3353/2640 | -30.7 (0.0/31.6) | -36.1 (0.01/36.3) | 65/59 (0.97) |
| 2022 | 25.92 (2920) | 12.3/-22.6 | 0.00 (0/92) | 0.00 | —/— (—) | 0.34 / 1.46 | 0.47 | 3051/2736 | -27.8 (0.5/29.3) | -31.3 (0.50/32.3) | 60/59 (0.97) |
| 2023 | 9.95 (2920) | 7.0/-15.4 | 0.43 (171/400) | 0.00 | —/— (—) | 0.77 / 0.72 | 0.86 | 3290/2325 | -27.0 (0.0/27.5) | -34.8 (0.01/35.0) | 59/58 (0.98) |
| 2024 | 10.21 (2924) | 6.7/-11.1 | 0.00 (0/184) | 0.00 | —/— (—) | 0.74 / 0.63 | 0.73 | 3137/2126 | -19.0 (0.0/19.4) | -24.5 (0.00/24.8) | 59/56 (0.98) |
| 2025 | 15.90 (2920) | 7.4/-8.9 | 0.00 (0/150) | 0.00 | —/— (—) | 0.80 / 0.81 | 0.60 | 2667/2225 | -17.4 (0.0/18.2) | -21.6 (0.00/22.2) | 55/53 (0.98) |

per-class (year = first failing year or 2023):
| class (2023) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 30 (29) | 52.4 | 50/8/6/0.52 | 0.58 (0.011) | 2822/2267 | 0.69 / 0.69 | 1.92 | -26.7 0.00/27.2 | -4.29 | -34.5 | — |
| COAL_BIT | 1 (1) | 0.5 | 100/36/16/0.40 | 0.04 (0.079) | 28/6 | 0.05 / 0.01 | 0.04 | -0.0 0.01/0.0 | -0.01 | -0.1 | — |
| ST_GAS | 5 (2) | 0.3 | 35/24/8/0.12 | 0.24 (0.756) | 440/52 | 0.03 / 0.01 | 0.11 | -0.3 0.00/0.3 | -0.01 | -0.3 | — |

### MISO (2026-10-03-closeout-miso-nuc-r) committed_pct plants 198
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 4.76 (2920) | 4.1/-7.4 | 0.00 (0/231) | — | —/— (—) | 2.40 / 7.23 | 2.78 | 5657/2647 | -62.1 (1.5/69.1) | -80.6 (1.20/88.1) | 313/266 (0.97) |
| 2020 | 5.08 (2925) | 4.4/-5.0 | 0.01 (8/1021) | 0.00 | —/— (—) | 2.80 / 6.54 | 3.58 | 6709/2765 | -49.9 (2.0/54.6) | -70.4 (1.61/75.2) | 302/261 (0.97) |
| 2021 | 7.31 (2923) | 3.0/-23.4 | 0.00 (0/38) | — | —/— (—) | 3.90 / 6.60 | 4.67 | 6064/3215 | -27.3 (4.3/59.3) | -47.8 (3.34/78.1) | 292/258 (0.97) |
| 2022 | 6.58 (2520) | -4.2/-41.4 | 0.00 (0/19) | 0.00 | —/— (—) | 4.22 / 4.80 | 3.85 | 5444/3722 | +26.7 (6.7/46.8) | +17.8 (6.54/54.1) | 281/251 (0.97) |
| 2023 | 5.97 (2920) | 4.4/-12.6 | 0.00 (0/241) | 0.00 | 1.00/0.35 (1.00) | 2.46 / 1.64 | 3.15 | 5604/2730 | -41.5 (1.1/44.8) | -58.3 (0.57/61.3) | 264/235 (0.97) |
| 2024 | 5.34 (2923) | 3.9/-14.5 | 0.01 (6/597) | 0.00 | 1.00/0.41 (1.00) | 1.89 / 1.55 | 3.39 | 5001/2486 | -36.1 (1.1/37.2) | -52.1 (0.72/53.2) | 268/231 (0.97) |
| 2025 | 8.40 (2920) | 5.2/-24.1 | 0.00 (0/58) | — | 1.00/0.49 (1.00) | 3.07 / 1.31 | 3.04 | 5235/2365 | -16.7 (1.9/34.4) | -28.6 (1.68/46.0) | 257/224 (0.97) |

per-class (year = first failing year or 2023):
| class (2020) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 43 (39) | 105.9 | 50/14/6/0.32 | 0.86 (0.008) | 2893/1902 | 0.81 / 0.52 | 6.49 | -12.6 0.52/14.1 | -5.98 | -22.1 | 0.22 |
| COAL_BIT | 28 (18) | 61.7 | 100/36/16/0.40 | 1.00 (0.016) | 485/123 | 0.35 / 0.83 | 1.11 | -5.5 1.15/7.9 | -4.67 | -8.8 | 1.00 |
| COAL_LIGNITE | 5 (4) | 9.7 | 100/36/16/0.40 | 0.00 (0.000) | 5/28 | 0.00 / 1.64 | 0.04 | -2.8 0.00/2.8 | -2.38 | -2.8 | — |
| COAL_PRB | 51 (38) | 123.8 | 100/36/16/0.40 | 1.28 (0.010) | 903/332 | 0.48 / 3.18 | 1.88 | -13.9 0.36/16.7 | -11.25 | -19.1 | 1.00 |
| ST_GAS | 29 (20) | 28.2 | 35/9/8/0.11 | 0.44 (0.016) | 2423/380 | 1.16 / 0.38 | 4.48 | -15.0 0.01/13.2 | -0.91 | -17.5 | — |

### SPP (2026-10-03-closeout-spp-nuc-keeper) committed_pct plants 105
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 13.16 (2918) | 5.4/-11.8 | 0.03 (75/2980) | 0.04 | 1.00/0.09 (1.00) | 1.20 / 1.74 | 1.01 | 3020/2836 | -46.8 (0.3/44.5) | -69.5 (0.03/69.0) | 169/155 (0.98) |
| 2020 | 14.27 (2918) | 5.4/-7.4 | 0.15 (597/3978) | 0.11 | 1.00/0.08 (1.00) | 1.32 / 2.00 | 1.71 | 2970/2752 | -47.4 (0.3/45.6) | -70.2 (0.05/69.8) | 165/141 (0.98) |
| 2021 | 14.76 (2918) | 14.3/-27.8 | 0.23 (666/2958) | 0.44 | 1.00/0.20 (1.00) | 2.93 / 2.55 | 6.23 | 3947/2872 | -28.8 (0.4/28.2) | -40.2 (0.06/39.5) | 159/142 (0.98) |
| 2022 | 10.14 (2918) | 6.3/-31.4 | 0.44 (934/2119) | 0.73 | 1.00/0.26 (1.00) | 3.93 / 2.37 | 8.01 | 4735/3000 | -25.1 (0.3/25.0) | -28.9 (0.19/28.7) | 159/144 (0.98) |
| 2023 | 9.70 (2918) | 4.7/-17.0 | 0.28 (756/2665) | 0.62 | 1.00/0.48 (1.00) | 2.70 / 2.03 | 2.76 | 4030/2946 | -42.1 (0.4/41.4) | -58.7 (0.09/58.5) | 158/144 (0.99) |
| 2024 | 10.77 (2916) | 4.5/-20.6 | 0.34 (1132/3353) | 0.61 | 1.00/0.64 (1.00) | 2.36 / 2.18 | 2.55 | 3781/2682 | -37.9 (0.3/37.8) | -55.7 (0.11/55.6) | 153/140 (0.98) |
| 2025 | 12.78 (2918) | 6.3/-21.2 | 0.29 (778/2634) | 0.60 | 1.00/0.67 (1.00) | 2.88 / 2.07 | 3.39 | 3578/2775 | -29.6 (0.4/29.9) | -44.6 (0.11/44.6) | 154/142 (0.98) |

per-class (year = first failing year or 2023):
| class (2019) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 20 (19) | 44.8 | 50/15/8/0.21 | 0.93 (0.021) | 2073/1211 | 0.54 / 0.90 | 2.83 | -11.8 0.25/12.2 | -1.46 | -16.2 | 0.43 |
| COAL_LIGNITE | 3 (3) | 10.6 | 100/36/16/0.40 | 0.00 (0.000) | 8/15 | 0.00 / 0.02 | 0.04 | -2.9 0.00/2.8 | -1.34 | -6.2 | — |
| COAL_PRB | 28 (23) | 73.0 | 100/36/16/0.40 | 0.04 (0.001) | 77/259 | 0.00 / 0.41 | 0.41 | -24.2 0.00/21.7 | -9.60 | -37.7 | 0.00 |
| ST_GAS | 35 (29) | 13.1 | 35/5/8/0.09 | 0.04 (0.003) | 862/1351 | 0.66 / 0.41 | 2.96 | -7.8 0.02/7.8 | -2.11 | -9.4 | 0.64 |

### SOCO (2026-10-03-closeout-soco-3-coalpile) committed_pct plants 49
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 5.97 (2922) | 3.0/-0.6 | 0.00 (0/189) | — | —/— (—) | 1.61 / 1.47 | 3.23 | 1830/358 | -39.4 (0.4/38.2) | -47.7 (0.14/46.5) | 103/88 (0.96) |
| 2020 | 4.49 (2928) | 3.4/-1.2 | 0.06 (86/1494) | — | —/— (—) | 1.58 / 0.85 | 1.86 | 1876/412 | -37.2 (0.4/36.7) | -55.0 (0.13/54.7) | 95/80 (0.97) |
| 2021 | 3.77 (2922) | 1.6/-11.2 | — (0/0) | — | —/— (—) | 2.26 / 1.82 | 1.89 | 2547/545 | -35.8 (0.5/35.7) | -53.9 (0.14/53.7) | 102/86 (0.97) |
| 2022 | 10.63 (2920) | 1.9/-34.6 | — (0/0) | — | —/— (—) | 2.13 / 2.52 | 1.29 | 2647/428 | -27.9 (0.4/32.1) | -35.0 (0.23/38.8) | 102/94 (0.97) |
| 2023 | 5.30 (2926) | 3.2/-6.1 | 0.00 (0/100) | — | —/— (—) | 0.78 / 0.83 | 1.45 | 1443/373 | -34.2 (0.3/33.8) | -49.8 (0.10/49.8) | 91/80 (0.97) |
| 2024 | 5.52 (2925) | 1.4/-8.6 | 0.03 (37/1102) | — | —/— (—) | 1.10 / 0.64 | 1.30 | 1643/293 | -33.0 (0.9/33.9) | -51.6 (0.37/52.0) | 91/87 (0.97) |
| 2025 | 6.70 (2922) | 3.5/-10.7 | — (0/0) | — | —/— (—) | 1.87 / 0.70 | 1.98 | 2926/261 | -30.2 (1.0/31.3) | -43.8 (0.47/44.4) | 91/80 (0.97) |

per-class (year = first failing year or 2023):
| class (2022) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 17 (17) | 95.7 | 50/8/6/0.52 | 0.43 (0.004) | 2228/251 | 1.55 / 0.09 | 8.30 | -21.7 0.35/22.2 | -1.99 | -25.7 | — |
| COAL_BIT | 2 (2) | 9.9 | 100/36/16/0.40 | 0.09 (0.009) | 18/17 | 0.04 / 0.00 | 0.33 | -1.7 0.07/1.8 | -0.96 | -2.8 | — |
| COAL_PRB | 4 (4) | 41.6 | 100/36/16/0.40 | 0.00 (0.000) | 1/103 | 0.00 / 0.01 | 0.10 | +3.3 0.00/0.1 | -1.23 | +2.2 | — |
| ST_GAS | 7 (6) | 17.4 | 35/24/8/0.12 | 0.77 (0.044) | 400/57 | 0.54 / 2.42 | 2.31 | -7.9 0.00/8.0 | -4.47 | -8.8 | — |

### NWPP (2026-10-03-nwpp-next-25-served) committed_pct plants 52
| year | M3 lower err $/MWh (h) | mid/upper err | ratio ≤$15 | ratio <$0 | M4 model/actual dormant (cov) | M2a / M2b TWh | M1 short-on TWh | starts model/CEMS | M5pf Δ (add/rem) TWh | M5h36 Δ (add/rem) | NL fit units/fitted (R²) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | — (—) | —/— | — (—/—) | — | —/— (—) | 1.03 / 0.04 | 1.70 | 2528/1299 | -44.7 (0.3/44.4) | -54.9 (0.19/54.9) | 109/104 (0.97) |
| 2020 | — (—) | —/— | — (—/—) | — | —/— (—) | 1.22 / 0.14 | 0.87 | 2763/1484 | -55.9 (0.4/56.0) | -63.9 (0.24/64.1) | 108/103 (0.97) |
| 2021 | — (—) | —/— | — (—/—) | — | —/— (—) | 1.84 / 0.10 | 1.05 | 3688/1381 | -33.8 (0.4/34.8) | -40.2 (0.31/40.7) | 107/100 (0.97) |
| 2022 | — (—) | —/— | — (—/—) | — | —/— (—) | 2.51 / 0.08 | 1.46 | 3922/1907 | -20.0 (0.3/22.3) | -22.7 (0.30/24.7) | 106/102 (0.96) |
| 2023 | 10.58 (1713) | 2.9/-17.3 | 0.00 (0/112) | 0.00 | —/— (—) | 1.55 / 0.14 | 1.48 | 3080/1566 | -26.3 (0.6/26.7) | -30.4 (0.52/30.9) | 106/86 (0.98) |
| 2024 | 8.27 (2920) | -1.2/-34.6 | 0.03 (31/1080) | 0.00 | —/— (—) | 0.65 / 0.14 | 1.21 | 2927/1737 | -35.4 (0.5/34.9) | -41.0 (0.38/41.1) | 106/84 (0.97) |
| 2025 | 8.97 (2920) | 0.3/-8.9 | 0.00 (0/754) | 0.00 | —/— (—) | 1.61 / 0.28 | 1.33 | 3628/1683 | -38.0 (0.6/38.6) | -43.6 (0.44/44.2) | 105/77 (0.98) |

per-class (year = first failing year or 2023):
| class (2023) | plants (CEMS) | class TWh | physics S/UT/DT/mlf | M1 short-on TWh (share) | starts m/c | M2a / M2b | CEMS-on-model-off TWh | M5pf Δ add/rem | DP minload Δ | M5h36 Δ | prec. added-low pf |
|---|---|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 25 (23) | 57.5 | 50/8/6/0.52 | 0.98 (0.017) | 2648/1084 | 1.39 / 0.08 | 11.96 | -11.0 0.38/11.5 | -0.24 | -12.6 | — |
| COAL_BIT | 6 (5) | 19.2 | 100/36/16/0.40 | 0.24 (0.013) | 90/18 | 0.09 / 0.01 | 0.52 | -4.8 0.12/4.9 | -1.68 | -6.8 | 1.00 |
| COAL_LIGNITE | 1 (0) | 0.0 | 100/36/16/0.40 | 0.00 (0.000) | 0/0 | 0.00 / 0.00 | 0.00 | -0.0 0.00/0.0 | +0.00 | -0.0 | — |
| COAL_PRB | 9 (7) | 28.0 | 100/36/16/0.40 | 0.16 (0.006) | 132/99 | 0.01 / 0.05 | 0.16 | -10.4 0.06/10.2 | -1.75 | -10.9 | 1.00 |
| COAL_WC | 2 (1) | 0.4 | 100/36/16/0.40 | 0.04 (0.117) | 113/15 | 0.00 / 0.00 | 0.19 | -0.1 0.01/0.1 | -0.03 | -0.1 | — |
| ST_GAS | 2 (2) | 0.1 | 35/24/8/0.12 | 0.06 (1.000) | 97/350 | 0.06 / 0.00 | 0.68 | -0.1 0.00/0.1 | +0.00 | -0.1 | — |


## 4. Rule-19 census per ISO (task 3) — what binds on slow-start energy today, and what the UC would replace

Source: each keeper's committed `legitimacy_diagnostics.json` D-2 rows (summed over the registered years; `share` = forced ÷ class TWh) and the keeper `run_config.json` arms. "Replace" = the UC's commitment decision is the same object the mechanism approximates (rule 19: one mechanism per phenomenon; the stacked field is refused at validation). "Stays" = a physical or contractual obligation the UC does not model. "Hard case" = a conduct-derived floor the owner must rule on (card D-5).

| ISO | mechanism binding on CC / coal / ST_GAS (forced TWh over the span, share of class) | UC reading | recommended D-5 substitution set |
|---|---|---|---|
| **ERCOT** | `gas_commitment_bridge` CC 10.98 (1.1 %) · `reliability_floor` CC 0.75 (0.1 %) · `coal_min_config` LIG 7.51 (6.7 %), PRB 23.94 (7.2 %) · `st_netload_drag` ST_GAS 19.94 (20.6 %) | bridge → **replace** (the UC chooses the commitment the bridge detects from P0); `coal_min_config` → **hard case**: a measured minimum-configuration floor (one unit of a multi-unit station online) — a UC with integer unit counts per plant expresses exactly this *if* `n_c` is the unit count and the floor becomes `mlf·p̄·u`; otherwise it stays; `st_netload_drag` → **hard case**: a conduct-shaped part-load drag with a declared window, not a commitment decision; replace only if the UC's no-load/min-up schedule reproduces the ST_GAS online hours (M2 census below says how far it is); `reliability_floor` (RUC analog) stays | `ercot_gas_commitment_bridge=False`; `ercot_coal_min_config_floor` → owner ruling; drags unchanged in the first A/B |
| **PJM** | `cc_mustrun_per_plant` CC 92.86 (4.4 %) · `reliability_floor` CC 0.61, COAL_* 1.5 · `coal_mustrun` BIT 6.42 (0.6 %), PRB 1.69 (3.6 %), WC 0.43 · `st_netload_drag` ST_GAS 7.44 (13.3 %) · `chp_steam` WC 0.21 | `cc_mustrun_per_plant` → **replace** (a per-plant measured online floor on merchant CC — the commitment state itself); `coal_mustrun` → **stays** as the D2-exempt take-or-pay/measured floor unless the owner rules it conduct (closeout-PJM-decommit R-55 adjudicated the decommit forms); `reliability_floor` stays; `st_netload_drag` hard case as ERCOT | `cc_mustrun_per_plant=False` (+ `cc_committed_per_plant` markup zeroed on integer clusters); coal floors unchanged pending R-55 |
| **MISO** | `st_gas_mustrun_per_plant` ST_GAS 30.61 (21.7 %) · `reliability_floor` COAL_*/ST_GAS 5.7 (≤ 0.8 %) | `st_gas_mustrun_per_plant` → **hard case**: measured per-plant p25 online level (conduct scope `mustrun_layup_window_mask`, `st_gas_mustrun_oom_level`) — it is a commitment-state object (a boiler held online) that a UC with no-load and 9-h min-up would *choose* in the hours it pays; replace only on D-5 ruling with the M2 census as evidence; `miso_gas_ecomin_online_floor` is **not armed** in this keeper (no row); `reliability_floor` stays | `miso_commitment_posture` stays off (rule 19, already); `st_gas_mustrun_per_plant` → owner ruling |
| **SPP** | `coal_mustrun` LIG 9.41 (15.3 %), PRB 37.33 (7.2 %) · `st_gas_mustrun_per_plant` ST_GAS 17.6 (20.9 %) | `coal_mustrun` → **hard case** (self-commit conduct, ASSESSMENT §6: "36 % of 2020 energy self-committed"; D2-exempt); `st_gas_mustrun_per_plant` as MISO; `spp_gas_commitment_bridge` / `spp_commitment_posture` **not armed** in this keeper (no D-2 row) | nothing to switch off at validation; both floors → owner ruling with the M5 decommit bound as the evidence |
| **CAISO** | `ra_mustoffer_bridge` CC 28.66 (8.2 %) | **replace** — the bridge detects P0 runs and floors them; the UC chooses them (ASSESSMENT §6 "form change") | `caiso_ra_mustoffer=False` (+ `caiso_ra_startup_bridge`, `caiso_ra_bridge_decommit`, `caiso_ra_startup_trajectory` fall with it) |
| **SOCO** | `st_gas_mustrun_per_plant` ST_GAS 14.05 (40.3 %) · `soco_gas_st_campaign_commitment` 1.21 (3.5 %) | `soco_gas_st_campaign_commitment` → **replace** (a seasonal commitment campaign is a commitment decision); `st_gas_mustrun_per_plant` hard case as MISO; coal take-or-pay (`coal_fuel_inventory_take_floor`) **stays** (contract, R-45/R-54) | `soco_gas_st_campaign_commitment=False`; mustrun → owner ruling |
| **NWPP** | none on slow classes | the queue's "coal commitment bridge by parameters" row is exactly the UC; nothing to replace | none |
| **NEISO** | `reliability_floor` CC 3.14 (0.9 %) · `winter_fuelsec_mustrun` COAL_BIT 0.03 (2020) | both stay (reliability / fuel-security obligations); control ISO | none (control) |
| **NYISO** | `nyiso_gas_commitment_bridge` CC 1.05 (0.6 %), ST_GAS 0.17 (0.3 %) · `reliability_floor` ST_GAS 7.17 (13.8 %) | bridge → **replace** at validation (rule 19); `reliability_floor` stays; control ISO | `nyiso_gas_commitment_bridge=False` (with its `nyiso_gas_bridge_*` legs) |

Physical floors present in every ISO and untouched: `nuclear_mustrun`, `chp_steam`, `hydro_min_flow`, `hydro_ror_flat`, `firm_import` (D2-exempt or non-thermal).

## 5. DOF ledger draft (task 4) — one row per UC parameter class

| parameter class | fields (UC-1 names, plan §6) | identification source (today) | rule-13 forward story | DOF status |
|---|---|---|---|---|
| start cost $/MW per class | `uc_start_cost` table (constants) | NREL/SR-5500-55433 class table (`BIN_STARTUP_COST_PER_MW`: CC 50, ST 35, coal 100; `CC_COMMITMENT_PARAMS` by heat rate 24–64); cross-check PJM `energy-offers` hot/cold start | engineering property of the unit class, reproduced for any forward year from the same table | measured/published; 0 free |
| no-load $/h | `uc_noload_source` (CAMPD regression · class fallback) | per-unit OLS intercept of CAMPD `heatInput` on `grossLoad` × delivered fuel (EIA-923); this screen: 141/165 SPP units fitted, R² median 0.98 (per-ISO stats in the JSON) | the intercept is a unit property; forward years re-price it with the forward fuel path (same construction as forward emission rates) | measured; 0 free; class fallback share reported |
| min-load fraction (plant) | `mlf` in `uc` params (from `thermal_tranches_<ISO>.csv` / plant-basis derives) | CAMPD loading-when-on p5 per plant; ISO class values where absent; WWSIS-2 where no derive | unit property; frozen derive (rule 23), re-derived only on CAMPD update | measured; 0 free |
| min-up / min-down h | UT/DT per class (constants + ISO derives) | ISO CAMPD plant-basis run-length p25 (SPP/PJM/MISO/CAISO), NYISO bridge values, SPP ASOM min-down, NREL tables elsewhere | published/measured physics | measured/published; 0 free |
| integer set | `uc_integer_scope` (E1: min-down > 2 h or start ≥ $30/MW) | the posture gate inverted (rule 18) | physics predicate | 0 free |
| window / look-ahead | `uc_window_hours` 24, `uc_lookahead_hours` 12 | DA SCUC horizon (`DA_COMMITMENT_HORIZON_HOURS` = 24, CAISO tariff §31.3) + the plan's declared look-ahead | market design constant | declared; **note the M5 h36 finding below** (coal UT 36 h > window) |
| MIP gap / time limit | `uc_mip_rel_gap` 1e-3, `uc_window_time_limit_s` | solver tolerances, set on the ladder's wall table — never on a gate | numerical | declared; 0 free |
| boundary mode | `uc_boundary_mode` | P0's SOC / cascade levels (plan §5) | the LP's own state | declared |
| pricing treatment of integer clusters | markup zeroed on integer clusters; uplift sidecar | owner card D-3 | design choice, not a fit | owner ruling |

No row is identified on a residual. The only tuned object the UC touches is the rule-1 band multiplier, which it *zeroes* on integer clusters rather than re-fitting (plan §1).


## 6. ASSESSMENT §6 readings — confirmed or refuted by the screen

| Record reading | Screen | Verdict |
|---|---|---|
| SPP 2019/2020: body over-price, thermal online at sub-cost in troughs; primary target | lower tercile +$13–14 on 2,918 h, the two largest rankable S1; model has 3–15 % of the actual ≤ $15 hours and 4–11 % of the negative hours; M4 gap 0.91–0.92 | **confirmed** — rank 1 and 3 |
| MISO 2020 low-load margin, reserve dormancy; primary target for reserve pricing | lower +$5.1 (S1 14.9 k, rank 14); C3a model-high +10.2 % so a trough fix helps; M4 unmeasurable 2019–22 (MISO purged the ASM files), gap 0.51–0.65 in 2023–25 | **confirmed in direction, weak in magnitude**; not selected by the rule |
| PJM 2020/2022 commitment-cost representation | 2020 now passes C3a on main (not rankable); 2022 rank 2 by S1 but C3a model-low −16.7 % with upper tercile −$35 (the gas-price/scarcity era) — a trough fix cannot close it; C3b 0.293 and the zero ≤ $15 hours (0 of 31) can move | **partly refuted**: selected, but the gate it can help is C3b, not C3a |
| ERCOT 2019/2020 coal vs CC through troughs | lower +$4.7–5.3 only (S1 13.9–15.6 k, ranks 13/15); but M2(b) 9.2–9.8 TWh of CC held online while CEMS is off and model CC starts 491 vs 3,070 — the bridge over-holds | **refuted as a price target; confirmed as a commitment-form target** (replace the bridge) |
| ERCOT 2023 thinness hypothesis | C3a −24.7 % model-low with upper −$35; lower +$7; the reserve family ercot_ordc_total is dormant 98 % vs actual 1 % | **not price-shaped at the trough**; the M4 gap (0.97) is the only UC-addressable reading — scarcity side |
| CAISO 2019–21 bridge replacement | 2021 rank 9 (S1 22.5 k on 50 % RT coverage); CC starts 8,700 vs 3,289 and 14.6 % of CC energy in sub-UT runs — the bridge cycles P0 runs the real fleet does not | **confirmed as a form change**; price unscoreable 2019–20 |
| NWPP coal commitment bridge by parameters | 2023 C3b fail, 2024 ineligible (S2 0.8); M2(a) 1.0–2.5 TWh of CEMS part-load online the model misses; no AS reference | **confirmed as a form question**, not a ranked target |
| SOCO contract conduct, not UC | 2022 rank 6, model-low −13.7 % with upper −$35; CC starts 2,228 vs 251 | **confirmed** — not UC-shaped |
| NEISO / NYISO controls | lower +$9.9 / +$6.7; NYISO 2024 ineligible (S2 0.66); NEISO C3a headroom −3.0 % | **controls stand; the no-flip bar is tight (F1)** |

## 7. Data the screen could not read (named, with the subtree)

| ISO | gap | effect |
|---|---|---|
| NEISO | `data/raw/NEISO-AS/reserve-prices/rzpd_final_*.csv` — gitignored, not on disk | M4 n/a all years |
| MISO | `data/raw/MISO-AS/asm_rtmcp_zonal_<2019–2022>` — purged at source (README) | M4 n/a 2019–2022 |
| CAISO | `actual_lmp_hourly_CAISO.parquet` has no 2019–2020 and 34.8 % NaN in 2021; `CAISO-AS/asprc_sr` starts 2020-03-31 and 2022 is absent | M3 n/a 2019–20, 2021 on 1,905 h; M4 n/a 2019, 2022 |
| NWPP | RT reference 2023–25 only (June-2023 start); no AS market | M3 n/a 2019–22; M4 n/a |
| SOCO | no AS market (system-lambda price reference only) | M4 n/a |
| ERCOT | RRS MCPC from the 60-day disclosures: coverage 0.75–0.84 in 2023–25 (publication lag), 1.00 in 2019–22 | M4 on available hours |
| all | `dispatch/<y>_P1.parquet` is gitignored at tip; the committed `hourly/unit_marginal_<y>.parquet` slim layer carries the same `mw`/`cap_mw`/`mc` and was used | none |

## 8. Log entry (for the desk, ≤ 5 lines)

- 2026-10-03 · UC-0 `session_013gHAT8qbNZwry6tA92gYNq` (Fable) · branch `claude/ucmilp-0-benefit-screen-tx8t` off main `cd7382f5` · zero LP · PREDECL `5b496292` pushed before numbers · board 9 × 7 published (61 cells, 55 scoreable, 15 rankable, 14 eligible) · **selection: SPP 2020, PJM 2022, SPP 2019 + controls NEISO 2023, NYISO 2024** · flags for D-5/UC-1 PRECOMMIT: lower-tercile excess is model-wide (controls +$7–10; NEISO C3a headroom −3.0 %), PJM 2022's C3a is model-low (target reading must be C3b / ≤ $15-hour ratio), 36-h window < coal UT (engine look-ahead rule), M5 removal side not a bound · rule-19 census and DOF draft in §4–5 · no plan/ledger/matrix edits.
