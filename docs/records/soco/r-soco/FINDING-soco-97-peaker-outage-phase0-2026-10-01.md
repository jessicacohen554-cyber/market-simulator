# FINDING soco-97 — phase 0 (zero-LP): a SOCO peaker-outage window with a price-independent driver (option c)

Keeper: `2026-09-30-soco96-measured-oil-burn`, bundle `results/calibration/soco96_span`. No LP was run.
Inputs: the committed `hourly/` sidecars; a `fleet_only` rebuild of the 2022 keeper recipe (`_soco94_year_pattern.rebuild`,
which carries every outage layer the keeper applies); FERC-714 λ on the bench's dense CST 8760 (`_soco91.lambda_cst`);
bench `avgLMP.rt_lw` / `rt_lw_mon`; CAMPD unit-level hourly `{AL,GA,MS,FL}_2022`; EIA-930 SOCO; NOAA GHCN daily TMIN
(ATL / BHM / MOB, fetched); the FERC–NERC Elliott inquiry report (fetched,
`ferc.gov/sites/default/files/2024-02/24_Winter-Storm_Elliot_0207_UPDATE.pdf`). Scratch scripts: session scratchpad only.

## Verdict: FEASIBLE BUT REACH INSUFFICIENT. Do not build.

- The only Southern-specific outage quantity with an external, price-independent source is FERC–NERC's: **913 MW
  unplanned at the start of Dec 23 + 1,390 MW incremental by 06:00 Dec 24 = 2.3 GW**.
- Applied flat over all 96 Elliott hours (generous), 2.3 GW moves **C3a 2022 from −12.04 % to −11.6 %/−11.7 %** and
  **C3b from 0.266 to 0.252–0.256**. Neither row clears.
- No flat MW value clears either row. The largest derate that avoids shortage is 4,359 MW (the minimum headroom in
  Elliott), and it reaches **at best −10.7 % / 0.228**. Above that, the LP sheds load at SOCO VOLL **$61,900**.
  At 6 GW that is 18 shortage hours and C3a +227 %.
- Matching λ needs an outage that is **shaped hour by hour**, a mean of 5.6 GW and up to 11.8 GW. Even that cannot
  reach the 23 hours where λ is above the whole stack. The only thing that supplies that shape is CEMS, which is
  the answer key rule 13 forbids.

## 1. Decomposing the 2022 gap

The scorer's definitions:
- **C3a** is the load-weighted annual mean (model, weighted by model demand) against bench `rt_lw`. The band is ±10 %.
- **C3b** is `_nrmse` over 12 demand-weighted monthly means against bench `rt_lw_mon`, which is RMSE ÷ mean(actual).
  The band is ≤ 0.20.

Both reproduce exactly: model $71.22 vs bench $80.97 gives **−12.04 %**, and **C3b = 0.2656**.

Each row below is set to λ. The other rows stay as the model has them.

| slice (TMIN = 3-station mean) | hours | gap contrib $/MWh | share of gap | P | λ | set to λ: C3a / C3b |
|---|---:|---:|---:|---:|---:|---|
| Elliott Dec 23–26 (TMIN 12–20 °F) | 96 | −4.37 | 45 % | 103.5 | 406.8 | **−6.65 % / 0.157** |
| other days TMIN ≤ 25 °F (Jan 23 only) | 24 | +0.02 | 0 % | 46.9 | 41.6 | −12.07 % / 0.266 |
| other days TMIN 26–32 °F | 768 | −0.25 | 3 % | 52.9 | 55.5 | −11.74 % / 0.251 |
| Jun–Aug | 2,208 | −6.39 | 65 % | 90.6 | 112.2 | −4.16 % / 0.221 |
| rest of year | 5,664 | +1.23 | −13 % | 63.8 | 61.7 | −13.56 % / 0.258 |
| **total** | 8,760 | **−9.75** | | 71.2 | 81.0 | |

The table below groups λ by quantile. The "ex-Elliott" column is the same contribution with the Elliott hours
removed.

| λ quantile bin | hours | contrib | ex-Elliott | mean P | mean λ |
|---|---:|---:|---:|---:|---:|
| ≤ p20 | 1,752 | +1.60 | +1.60 | 43.6 | 34.2 |
| p20–40 | 1,752 | +1.67 | +1.66 | 54.1 | 44.8 |
| p40–60 | 1,752 | +0.64 | +0.62 | 64.7 | 61.0 |
| p60–80 | 1,752 | −2.28 | −2.27 | 75.4 | 86.7 |
| p80–95 | 1,314 | −3.25 | −3.24 | 100.9 | 118.3 |
| p95–99 | 350 | −2.58 | −2.54 | 105.3 | 153.6 |
| > p99 ($223) | 88 | −5.54 | −1.22 | 107.1 | 501.9 |

By month, Elliott is the whole of December: Dec −4.81, Jul −3.33, Jun −1.82 and Aug −1.24. Jan–Apr is each about
+0.3 to +0.6.

- **The other cold days contribute nothing.**
- **Removing Elliott's error would close C3a 2022 only if the model priced at λ ($407 average) in all 96 hours.**
  That needs scarcity pricing, and SOCO does not have it (card S5). The rest of the gap is the ledgered summer
  peak premium.
- If the full stack is reached in every hour with no ORDC, the result is −7.93 % / 0.169. That is the ceiling for any
  quantity mechanism, and §2 shows a real window cannot reach it.

## 2. Quantity needed (greedy re-stack from the rebuilt 2022 offer stack)

Assumptions:
- Every unit's `mc_base` and its availability-scaled cap for each hour come from the rebuild. Hydro is excluded.
- Non-hydro served load Q = the sum of the keeper's `class_hourly` output for the fleet classes. Hydro, storage,
  imports and floors are held at the keeper's values.
- The marginal price is the merit-order mc at Q.
- The baseline greedy price in Elliott averages $102.9, against the LP's $100.0.

| Elliott quantity | value |
|---|---:|
| mean λ / model P / stack top (oil) | $384.7 / $100.0 / $479.6 |
| hours with λ above the whole stack | **23 of 96 (24 %)** |
| non-hydro Q / available non-hydro capacity | 32.5 / 42.6 GW |
| headroom: mean / min | 10.0 / **4.36 GW** |
| unavailability needed to put the marginal unit at λ (73 reachable hours): mean / p50 / max | **5.6 / 6.8 / 11.8 GW** |
| needed in the 23 above-stack hours | > headroom (7.7 GW mean), so the LP sheds load at VOLL |
| idle in Elliott: CT_PEAKER / ST_GAS / oil | 6.7 / 1.2 / 1.4 GW (8.45 GW CT available, 1.77 dispatched) |

Each row below applies a flat derate X across all 96 Elliott hours and reads C3a and C3b after the re-stack.

| flat derate X | pool | shortage h | C3a | C3b |
|---|---|---:|---:|---:|
| 913 (FERC standing unplanned) | all thermal | 0 | −11.84 % | 0.260 |
| 1,390 (FERC incremental) | CT / ST_GAS / oil | 0 | −11.79 % | 0.258 |
| 2,303 (FERC sum) | all thermal | 0 | −11.58 % | 0.252 |
| 4,000 | all thermal | 0 | −10.92 % | 0.234 |
| **4,359 (max with no shortage)** | all thermal / CT only | 0 | **−10.69 % / −10.91 %** | **0.228 / 0.233** |
| 6,000 | any | 18 | +227 % (VOLL) | 8.4 |

## 3. Candidate price-independent drivers

Network fetch works: NOAA and the FERC PDF both downloaded. The FERC HTML landing pages return 403.

| driver | Southern MW in Elliott | price/CEMS-independent | rule 13 forward test | rule 19 overlap | reach |
|---|---|---|---|---|---|
| **(a) FERC–NERC Elliott inquiry** | Yes. Fig. 23: Southern planned 3,022 → 2,486 MW and unplanned 758 → **913 MW** (Dec 21 → Dec 23). Text p.~45: **+500 MW gas/oil 00–02 h, +890 MW gas/CC 02–06 h Dec 24 = 1,390 MW**. EEA1 at 02:00 and EEA2 at 06:25 Dec 24, with 1,000 MW emergency energy from FPL. No hourly series, no unit list. | Yes | **Fails.** It is a one-off post-event report with no forward analogue. It is usable only as a calibration target for (b). | Partial. The planned 2.5 GW is already in the CAMPD / EIA-860 layers, and some of the unplanned may be too. | ≤ 2.3 GW: −11.6 % / 0.252 |
| **(b) temperature-conditioned forced-outage hazard** (NOAA TMIN → FOR by technology, from GADS-based literature, e.g. Murphy et al.) | Indirect only. A hazard calibrated to Southern's own Elliott experience (2.3 GW out of ~45 GW fossil ≈ 5 %) gives about 2.3 GW. The event-wide 13 % (90.5 GW of EI resources) would give about 5.5 GW, but that is not Southern's figure (rule 14 misalignment). | Yes | **Passes in principle**: it regenerates from forward weather and responds to conditions. GADS unit data is not public; the published curves were not fetched or verified here. | **Yes.** It stacks on the CAMPD per-unit / short / partial windows, so those would have to be reconciled or replaced, not stacked on. | Southern-calibrated: about −11.6 % / 0.25. Event-wide: shortage at $61.9k. |
| **(c) ambient CT capability derate** | **Wrong sign.** CT output rises in cold, dense air, so Elliott at 12–20 °F raises capability. The existing `temp_dependent_derate` is off, and `cc_winter_capability_basis` is closed at ~0 reach. | Yes | Passes | Duplicates the `temp_dependent_derate` / `cc_winter_capability_basis` family | **0 or negative** |

## 4. What CAMPD and the model already make dark in Elliott

- **Model availability already removes more than FERC reports.** Non-hydro fleet capacity at full availability is
  49.4 GW, and the model has 42.6 GW available in Elliott. That is **6.9 GW dark**: CC 3.0, CT 1.2, ST_GAS 1.2,
  coal 1.15 and oil 0.03 GW. FERC puts Southern's total unavailable at 3.4 GW at the start of Dec 23, plus 1.39 GW
  incremental, for about 4.8 GW. The model fleet and the BA's 57.9 GW installed have different scopes.
- **No SOCO CAMPD artifact carries a CT_PEAKER window that overlaps Elliott.**
  - Overlapping windows by artifact: `perunitdark` 5.5 GW (CC 3.05, coal 1.84), `shortgas` 1.2 GW (CC), `partial`
    0.95 GW (coal), and `short`, `layup`, `e923` and `perunit` all 0.
  - The deriver requires `min_inmerit_hours` ≥ 6 and `min_outage_days` ≥ 1, so an hour-scale trip or failure to
    start is invisible by construction.
- **CEMS against model availability, plant level, Elliott.** Covered plants hold 89 % of CT capacity.
  - CT_PEAKER: the model has 7.5 GW available at covered plants. CEMS gross is 5.4 GW. In the 69 hours with
    λ > $200, **3.7 GW of model-available CT sits at plants that are fully dark in CEMS**, and available minus
    CEMS is 5.1 GW.
  - Oil: 0.24 GW dark in the same hours.
  - For CC, coal and ST_GAS, CEMS gross exceeds model availability (CC 16.7 vs 14.4 GW). Gross-vs-net and
    plant-vs-BA scope make that comparison unusable as a darkness measure for those classes.
- **Answer to the owner's question.** Yes, the model's ~10 GW headroom is mostly idle CT_PEAKER capacity the model
  treats as available, and up to about 3.7–5.1 GW of it was dark in CEMS at high λ. Two limits apply:
  - **CEMS darkness does not establish cause.** The only external, cause-attributed Southern figure is FERC's
    2.3 GW.
  - **Even all 5.1 GW, applied flat, falls at or past the 4.36 GW shortage cliff.** It either fails to clear the
    rows or sheds load at VOLL.

## 5. Verdict and what a build would need

**Feasible, but the reach is insufficient.**

- **Reach bounds.** The admissible driver (FERC 2.3 GW, or hazard (b) calibrated to it) reaches **C3a 2022 −11.6 %
  and C3b 0.252**. Neither clears.
- **The ceiling of any flat window.** It is **−10.7 % / 0.228**. Every quantity mechanism together cannot beat
  **−7.9 % / 0.169**, and reaching that needs CEMS-shaped hourly MW, which is inadmissible.
- **What the gap is.** λ in Elliott reflects EEA2 operation: emergency purchases from FPL, plus 23 hours priced above
  every own-fleet offer. This is a scarcity and emergency-purchase price, not missing own-fleet outages. It sits
  behind card S5 ("No ORDC, no scarcity seed").
- **What a build would need anyway:**
  1. a NOAA-driven, technology-specific forced-outage hazard with published, verified parameters, registered in
     `ScenarioConfig`;
  2. reconciliation that **replaces** the CAMPD short / partial windows in cold hours rather than stacking on them
     (rule 19);
  3. a rule 17 window (TMIN below a cited threshold), driver and forward story;
  4. a guard against the 4.36 GW VOLL cliff ($61,900);
  5. a mechanism-matrix row.

  Even then the expected reach is about 0.4 pt on C3a and 0.014 on C3b.
