# RESULT — SPP-72, card R-bf (demand leg of the stack-climb defect): DEMAND IS NOT THE CAUSE

**Zero LP.** Pre-registration: `docs/handoffs/PRECOMMIT-spp-72-demand-tightness-2026-09-22.md`,
pushed at `a5478fab` before any tightness number was read. Base `aaaaeb61`. Probe:
`scripts/probes/_spp72_demand_tightness.py`; output `results/calibration/_spp72_demand_tightness_phase0.json`.
Charter: `docs/RESULT-xiso-stack-climb-attribution-2026-09-22.md` §10, lever (c). This is the
first time demand has been measured for this question in any ISO.

---

## 0. Headline

- **In the hours SPP's real market priced highest, the model serves exactly the load and net
  exports the market served.** The LP's gross `demand` array equals measured EIA-930 SWPP load +
  measured net exports, **max |diff| 7.3e-12 MW in all 8,760 hours of all seven years.** The
  thermal requirement after wind and solar has the **same median percentile as measured to
  0.01 pt** in every year.
- **Those hours are mostly not high-load hours, in reality or in the model.** The median
  measured-load percentile of the market's top-1 % price hours is **65.8 in 2020** and 66–94
  across years. Only **20 %** of 2020's top-price hours fall in the top load decile.
- **So demand cannot be why the stack isn't climbed.** The model reaches the right requirement
  and still prices it at a median **$23.72**, where the market's median was **$144.4** (2020).
  The residual routes to **lever (b), commitment reach**, and to the RT/DA wedge SPP-29
  identified.
- **The pre-registered lane verdict was NOT met, and I am not moving the threshold.** 2020 and
  2022 are EXONERATED. **2021 is INCONCLUSIVE (Δ +5.6 against a ±5 band).** §3 decomposes that
  gap: all of it is the measured Uri net import. The only lever it could open is
  `priced_interchange`, which is already **R** for SPP (SPP-51).

## 1. The four failing rows, re-verified

`calibration_verdict.py --run-id 2026-09-22-spp-71-rung-ensemble` → NOT-YET. C3a 2020 **+17.3 %**.
C3b 2020 / 2021 / 2022 **0.267 / 0.243 / 0.208**. Matches the brief.

## 2. The pre-registered test (top-1 % = 88 hours by measured RT price; percentile within own year)

| year | median p_meas (load) | median p_mod (LP demand) | **Δ** | verdict | mean net export in those hours, MW |
|---|---:|---:|---:|---|---:|
| 2019 | 70.8 | 68.0 | +2.8 | EXONERATED | −261 |
| **2020** | **65.8** | **62.3** | **+3.5** | **EXONERATED** | −494 |
| **2021** | **88.1** | **82.5** | **+5.6** | **INCONCLUSIVE** | **−3,398** |
| **2022** | **80.3** | **79.6** | **+0.7** | **EXONERATED** | −258 |
| 2023 | 68.5 | 69.0 | −0.5 | EXONERATED | −414 |
| 2024 | 93.8 | 92.2 | +1.6 | EXONERATED | −1,639 |
| 2025 | 72.6 | 72.0 | +0.6 | EXONERATED | −230 |

Top-10 % robustness read (876 h): Δ = +1.7 / +3.7 / +4.8 / +0.6 / +2.1 / +1.1 / +2.6. Every year
is inside ±5.

Absolute MW, for completeness. Mean measured load vs LP demand in the 2020 top hours is
32,071 vs 31,577 MW, a difference of −494 MW. That is exactly the net-import term.

## 3. Decomposition: every Δ is the net-interchange term

The sidecar's `demand` is the gross array `load + net exports`. The LP's balance row is that
minus must-run (`run_calibration.py:3078-3082`), which is only 12 monthly constants of
142–272 MW (biomass + OTHER). Netting it out moves `p_mod` by **≤ 0.1 pt in every year** (2020:
62.3 → 62.2), so no verdict changes. In every year, the median percentile of measured `load + TI` equals `p_mod` exactly. So each Δ
above is **SPP importing in its high-price hours**, and nothing else: no clock error, no zonal
split, no scaling.

- **2021 = Winter Storm Uri.** Net import averaged **3,398 MW** across the top-88 set. The model
  correctly does not ask SPP's own fleet to serve imported MW. That is correct accounting of a
  measured quantity, not a shaved input.
- The only way this term could be a *model* defect is if SPP's imports responded to price
  (flow-follows-spread). **That is `priced_interchange`, already adjudicated R for SPP**
  (SPP-51: SPP↔MISO sign agreement 0.42–0.50 against a 0.55 bar, corr ≈ 0; the seam is
  scheduled/JOA flow). Rule 28(a): nothing here is new evidence against that verdict.

## 4. Post-hoc descriptive (declared as such; does not move §2)

Median percentile inside each year's market top-1 % hours:

| year | measured load | measured net load (load − wind − solar) | measured thermal requirement (load + TI − wind − solar) | **model thermal requirement** (demand − dispatched VRE) | model price, median | actual RT, median |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 70.8 | 79.6 | 79.9 | **79.9** | 25.00 | 209.9 |
| **2020** | 65.8 | 77.4 | 74.5 | **74.5** | **23.72** | **144.4** |
| 2021 | 88.1 | 94.1 | 88.5 | **88.5** | 196.42 | 1,062.6 |
| 2022 | 80.3 | 87.2 | 85.6 | **85.6** | 60.10 | 279.7 |
| 2023 | 68.5 | 75.8 | 75.9 | **75.9** | 31.46 | 193.7 |
| 2024 | 93.8 | 95.5 | 95.5 | **95.5** | 36.02 | 222.7 |
| 2025 | 72.6 | 80.6 | 78.6 | **78.6** | 36.64 | 246.3 |

The model and measured thermal requirements match because the model's wind availability equals
measured wind output in **86 % (2020) / 94 % (2024)** of these hours, and solar in 99–100 %.
Even net of VRE, the market's top-price hours sit at a median 74th–96th percentile. Reality
climbed the stack at a middling requirement, and the model, given the **same** requirement,
does not.

## 5. Trap (e) — alignment, verified three ways

1. **Bit identity with an independent file on an independent clock.** Measured load and TI come
   from `SWPP_region.parquet` (not the loader's `SWPP hourly.parquet`). `period` is hour-ending
   UTC; slot k = `Y-01-01 06:00 UTC + k h` with CST Feb 29 dropped. `max |demand − (load+TI)|` =
   **7.28e-12 MW, 0 hours > 1 MW**, all seven years, including the second half of 2020 and 2024.
2. **Lag scan per half-year:** argmax at lag 0 in both halves of every year (r 0.984–0.992). The
   ±24 h lag in H2 drops r to 0.89–0.95.
3. **Named-event landmark:** the top 2021 RT hour maps to slot 1110 = **2021-02-16 06:00 CST**,
   the start of SPP's Uri EEA3 load shed. The top 2024 hour maps to 2024-01-14 11:00 CST, the
   January cold snap.

**2024 benchmark seam** (slots 1410–1415, price and demand 24 h apart): none are in `H_2024`, so
nothing was excluded.

## 6. Predictions, scored honestly

| # | prediction | outcome |
|---|---|---|
| P1 | every year EXONERATED, \|Δ\| ≤ 3 | **MISS.** 5 of 7 within 3 pts. 2020 is +3.5. 2021 is +5.6, INCONCLUSIVE. The risk I named (imports in tight hours) is exactly what happened. |
| P2 | lag 0 in both halves; peak hour within 1 h | Lag leg **HIT**. **Peak-hour leg MISSED as written** in 5 of 7 years (2020/2022/2023/2024/2025, up to 384 h apart). Diagnosed: the model's peak equals the `load + TI` peak in all 7 years, and demand ≡ load + TI to 7e-12 MW. So I specified the wrong check, and the clock is fine. |
| P3 | median p_meas in [75, 95] | **MISS in 4 of 7** (70.8 / 65.8 / 68.5 / 72.6). The tail is *less* of a load event than I expected. |
| P4 | no seam hour in `H_2024` | **HIT.** |

## 7. What this does and does not establish

- **Establishes:** the LP's demand input is faithful to measured load, hour by hour, in the
  market's high-price hours, and so is its thermal requirement after VRE. **No demand lever
  can close C3a 2020 or C3b 2020–2022.** The failure is in how a correct requirement is
  *priced*.
- **Does not establish** that commitment reach is the cause. It removes the competitor.
  Commitment reach (lever b) is now the only surviving candidate on the xiso ranking: reserve
  (a) is closed (SPP-55, `energy_reserve_coopt` = I), and the offer-curve family is closed by
  construction. SPP's fossil fleet carries `min_down_hours = min_run_hours =
  startup_cost_per_mw = 0` on every unit (SPP-71 §8). That is where the next card points.
- **Does not** propose, arm or add anything. No `ScenarioConfig` field, no matrix cell verdict
  change (no mechanism was tested; rule 28(b) is not engaged), keeper 15 untouched,
  `build_dof_ledger --iso SPP --check spp71_ensemble_span` → `free_parameters current`.
- Rule 25: this measurement is SPP's alone. Other ISOs' demand legs stay unmeasured. The probe
  generalises by swapping the BA and bundle.
- Every number here is model-SELECTION evidence (`[R-HOLDOUT]` removed 2026-09-09).

## 8. Cost and retrievability

0 LP minutes, no shards, no bundles written. Everything reproduces from `main` with
`uv run python scripts/probes/_spp72_demand_tightness.py --out <json>`. Nothing needs promoting.
