# PRECOMMIT — R-ERCOT-23: the 2021 LCAP window and the protocol price cap (`ercot_swcap_effective_hourly`)

- **Lane:** ERCOT, R-ERCOT-23 (handoff `HANDOFF-r-ercot-23.md`, Task 1).
- **Incumbent / control:** keeper `2026-10-01-r-22-ordc-shift`, bundle `results/calibration/r_ercot22_span` (2019–2025). G-CTRL form 4: the committed bundle is the control; no control solve.
- **Phase 0:** `scripts/probes/_r_ercot23_lcap_id.py` → `r_ercot23_phase0.json` (zero LP).
- Written before any solve. Every number below was fixed before the shards were launched.

## 1. What phase 0 found

The published RTORPA formula on ERCOT's own measured RTOLCAP / RTOFFCAP / λ (NP6-905-CD) was split into its two terms, using measured RTOFFPA to isolate the full-hour term.

**2021 is not a curve-parameter problem. It is the VOLL.**
- Uri (February) reproduces: formula 65.1k vs measured 58.0k $·h.
- **April–November is 8–10× over** in every month (April 13,958 vs 1,095).
- Inverting both terms over Mar–Dec gives a −1.5 to −2.2 GW offset in *both* curves at once. A μ/σ change cannot do that; a ~4.5× smaller (VOLL − λ) can.
- **Cause.** Uri crossed ERCOT's Peaker Net Margin threshold (Operating Day 2021-02-16, notice M-C021521-02). Under 16 TAC 25.505(g)(6) the SWCAP then drops to the LCAP for the rest of the year. The PUCT suspended that until its 2021-03-03 open meeting, and ERCOT moved Real-Time to LCAP for **Operating Day 2021-03-04** (notice M-B030321-01).
- The ORDC's VOLL "is set on a daily basis to be equal to the SWCAP" (ORDC OBD §2.1, every version since OBDRR015). ERCOT's 2022 Biennial ORDC Report §1.3 states it directly: *"SWCAP (and therefore VOLL) was reduced to the LCAP of $2,000/MWh from March 4, 2021, until the end of that year."*
- Measured hourly λ + adders never exceeds $1,929 after that date.

**The protocol cap.** "Protocols limit the sum of System Lambda and all Price Adders to SWCAP" (same report, §1.2). The model adds measured RTORDPA on top of its own λ + ORDC adder with no cap:
- 2021 written price reaches **$10,771**; 2019 reaches $9,656; 2023 reaches $5,025.
- Census on the r-22 keeper, hours with λ + adders > SWCAP: 2019 **2**, 2021 **47**, 2023 **1**, every other year **0**.

## 2. Identification (published RTORPA formula on measured inputs ÷ measured RTORPA)

| Year | Keeper curve | + LCAP | Diagnostic: OBD half-hour form + LCAP | Diagnostic: ERCOT Fig. 3 μ/σ + OBD form + LCAP |
|---|---|---|---|---|
| 2019 | 1.04 (r 0.997) | 1.04 | 0.99 | 0.94 |
| 2020 | 1.43 (r 0.985) | 1.43 | 1.25 | 0.85 |
| **2021** | **1.59 (r 0.876)** | **1.14 (r 0.985)** | 1.07 | 1.06 |
| 2022 | 1.08 | 1.08 | 0.92 | 0.88 |
| 2023 | 1.09 | 1.09 | 0.96 | — |
| 2024 | 0.85 | 0.85 | 0.79 | — |

**The two diagnostic columns are CARDED, not built.**
- **OBD half-hour form.** The OBD's 30-minute curve uses mean 0.5·(μ + Sσ). Our code uses μ/2 + S·0.707σ.
- **Fig. 3 μ/σ.** ERCOT's published seasonal μ (shift included) and σ: ≈640 / 1,210 MW in 2019, ≈900 / 1,210 MW in 2020–21, ≈880 / 1,280 MW in 2022. Digitized from the figure to about ±15 MW.
- **Why not built here.**
  - Both move every year, including the 2023 owner-hold year.
  - The 2023–25 values need ERCOT's 2024 report.
  - The model's 2020 adder gap is only +0.5 $/MWh LW.
- **What they show.** The 2020 1.43× is the shared 2020–21 parameter vintage, not a 2020-specific defect. 2021 Mar–Dec reads 1.41× after the LCAP, the same as 2020.

## 3. The change (zero DOF)

**`ercot_swcap_effective_hourly`**: default off, ERCOT-gated, one mechanism (rule 19). The hourly SWCAP is `results.scarcity.ercot_effective_swcap_series`, which is the year's HCAP except inside a published LCAP window. The only window is 2021, from hour 1,488 at $2,000 (`constants.ERCOT_LCAP_WINDOWS_BY_YEAR`).

That series feeds the four places ERCOT's cap binds:

| | Where | What it does |
|---|---|---|
| (a) | `pipeline.kwargs.apply_reserve_coopt` → `ordc_penalty_hour_scale` → `build_cost_vector` | Every ERCOT reserve-family penalty is linear in VOLL, so the cost block is scaled by SWCAP_t / `ordc_voll`. |
| (b) | `run_calibration.py` | Load-shed cost is min(voll, SWCAP_t). |
| (c) | `pipeline.solve._swcap_clip_level` | The offer clip is at SWCAP_t − ε. |
| (d) | `run_calibration_full._system_frame` | λ + adders ≤ SWCAP_t. Adders are trimmed in ERCOT's order: ORDC adder, then RTORDPA, then DAM-AS. λ is never trimmed. |

- Outside an LCAP window, (a)–(c) are the identity and pass no kwarg, so they are byte-identical.
- Rules 21/24: no free parameter. The inputs are one published date, one published value and one published bound.
- Registration: a new `ScenarioConfig` field with cache-key registration; the solve-surface name `ERCOT_LCAP_WINDOWS_BY_YEAR` declared (zero key moves); a matrix row plus a cell in every shard.

## 4. G-DRIFT and solve set

- **G-DRIFT.**
  - `f4d29d72..origin/main`: no file changed on the solve path (src/market_sim, run_calibration*, replay_keeper, scripts/lib, data/raw/{_validation-source,reference,ercot}).
  - R-ERCOT-22's audit `bc5069cd..9c2cdf9a` was all INERT, and its own change (2019 shift) does not touch 2021.
  - The only LIVE hunk is this flag.
- **Solve set (rule 36, one shard per year).**
  - Re-solve **2019** and **2021**: the only years where the census says the flag binds.
  - Reuse 2020, 2022, 2024 and 2025 from the keeper's legs. They have 0 binding hours, and (a)–(c) are the identity there.
  - 2023 is the carve-out on owner hold. It is not armed and not re-solved.
- **Shard command:** `replay_keeper.py results/calibration/r_ercot22_span --years <Y> --set ercot_swcap_effective_hourly=true`.

## 5. Predictions (fixed before the solve; zero-LP on the keeper, λ held)

| Quantity | 2019 | 2021 |
|---|---|---|
| Dispatch / C1 / C8 | unchanged ±0.05 TWh (only 2 capped hours; LP identical) | within ±0.5 TWh per class (only the LCAP-window reserve penalty moves) |
| LW price ($/MWh) | 50.03 → **49.7–49.9** | 172.88 → **166.5–169.0** |
| C3a | +7.5 % → **+7.0 to +7.3 %** (PASS) | +4.2 % → **+0.5 to +2.0 %** (PASS) |
| LCAP-window ORDC adder (LW contribution) | — | 4.60 → **0.8–1.3** (measured RTORPA 0.47) |
| Max system price | 9,656 → **9,000** | 10,771 → **9,000** |
| h > $1k | 30 (=) | 122 → **110–116** |
| C3c h > $200 | 100 (=) | 664 → **645–658** |
| C3b | 0.231 → 0.225–0.232 (still FAIL) | 0.063 → 0.055–0.065 |
| Slack MWh | 0 | 3,194 → 3,194 ± 50 (Uri; HCAP unchanged there) |
| Determination | NOT-YET (=) | CALIBRATED (=) |
| ISO | NOT-YET (=) | |

## 6. Promotion rule

- The change is structural and zero-DOF, so it is an improvement if 2021 moves as predicted and nothing else regresses (rule 1).
- In that case, promote under the owner's standing instruction.
- If the solve contradicts the direction of the 2021 prediction, stop and report.
