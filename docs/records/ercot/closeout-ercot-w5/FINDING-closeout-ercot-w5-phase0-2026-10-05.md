# FINDING: ERCOT close-out w5, phase 0 (zero LP): no admissible candidate on the three residual records

Lane `closeout-ERCOT-w5`, desk session_01ERkBTm23ZAP4CTZnJVD9Ss, 2026-10-05. This lane is stacked on the w4 recipe (cliff split + warm committed; `RESULT-closeout-ercot-w4-coal-warm-committed-2026-10-05.md`, PR #7202). The w4 legs are the control.

All readings come from the w4 legs (`results/calibration/closeout_ercot_w4_<Y>`), the shared EIA-923 frame, `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet` and `data/raw/ercot/ercot_<Y>_ordc_reserves_hourly.parquet`.

## Headline

The desk asked three questions. **None yields a zero-DOF, rule-admissible build, so no PRECOMMIT and no shards.**

1. **2020 COAL_PRB (−8.31 against ±8.0).** The whole residual sits on 2019–22 per-plant coal conduct, which is ledgered DATA-LIMITED (R-32, R-ERCOT-3).
2. **A heat-rate-ordered CC committed level** would contradict measured conduct. Real low-end CC offers are heat-rate-flat; the heat-rate ordering lives in commitment state (R-ERCOT-19 §2). Building it would replace measured conduct with an engineering estimate (rules 13/14). It would also move the committed band's level outside rule 1's one authorized channel.
3. **2019/20 C3b is summer energy over-pricing in mid-price afternoon hours.** The ORDC adder tracks measured RTORPA. No measured mechanism on record reaches it without an owner gate, and the one candidate on record (Q5 membership) makes 2019 C3b worse in its static reach.

## 1. 2020 COAL_PRB residual by plant (w4, model − EIA-923, TWh)

| Plant | 2019 | 2020 | Owner of the residual |
|---|---|---|---|
| Martin Lake 6146 | −2.42 | −5.17 | 2019/20 per-plant conduct, R-32 DATA-LIMITED |
| Fayette 6179 | −2.43 | −1.84 | `_econhi` at the static 2024–25 curve ($108), R-ERCOT-3 |
| Sandy Creek 56611 | −1.64 | −1.20 | econlo $33.92 / econhi $65.00 are the static 2024–25 curve levels, priced the same in 2020 ($2 gas); R-ERCOT-3 |
| Parish 3470 | −0.33 | −0.80 | 2019/20 conduct, R-32 |
| Oklaunion 127 | −0.71 | −0.20 | retired 2020-09 |
| Limestone, Spruce, Coleto | −0.39 | +0.90 | — |
| **Total** | **−7.91** | **−8.31** | |

- **Sandy Creek has no structural defect left after w4.** Its committed tranche now bids its base cost ($31.05, below econlo), and its curve is monotone except for the gas-parity `_peak` rows ($30–49, ERCOT-140), which sit below econhi. Its 2020 shortfall (CF 0.40 model vs 0.55 actual) is the price level of its 2024–25 curve applied to a $2-gas year. That is the same data-limited object as Martin Lake and Fayette.
- **The only admissible route is data:** the R-7 G1 2019–22 SCED intake (per-plant coal TPO curves for those years). That is an owner data decision.

## 2. CC committed level: why a heat-rate-ordered replacement is not admissible

- **The w4 inversion (FINDING-closeout-ercot-w4 §2):** CC_REGULAR over-runs scale with heat rate in every year. The committed-block level (ERCOT-139) is heat-rate-flat (corr 0.06 with CAMPD HR), and the spread comes from zonal gas basis.
- **The measured conduct, R-ERCOT-19 PRECOMMIT §2** (2024–25 60-Day DAM, 13 matched CC plants per year):
  - Correlation of HR with the first-segment offer price, relative to the hourly fleet median: **+0.19 / −0.16**. Real low-end offers are heat-rate-flat.
  - Correlation of HR with the DAM ON share: **−0.60 / −0.34**. The heat-rate ordering is carried by commitment, not by the offer level.
- **What a replacement would do:** a "CAMPD own-plant HR × zone gas" committed level would replace a measured offer level with an engineering construct. Rule 14 forbids reverting to an estimate. Rule 13 is not met, because the construct is not the measured quantity.
- **Rule 1:** the committed band's level is one of the authorized offer-band tuning channels (set ex ante, one value, ledgered). A per-plant structural override of that band's level is neither that channel nor a measured mechanism.
- **The admissible form is commitment state.** Its prior-year version (`cc_committed_prior_year_commitment_eligibility`) is adjudicated: probed and not promoted, because 2022 CC C1 regressed and it fails closed in 2019. A same-year online-state input would pin the model to observed commitment, which rule 13 forbids. Nothing here is new evidence for a re-test (rule 28).

## 3. 2019/20 C3b decomposition (w4)

The monthly error splits into the ORDC adder against measured RTORPA, and energy (price − adder) against (RT − RTORPA). Hourly actual, model-load-weighted.

| Year | Squared-error carrier | Total error | Adder vs RTORPA | Energy |
|---|---|---|---|---|
| 2019 | Aug (75 % of squared error) | +28.53 | +9.91 | +18.62 |
| 2019 | Jul / Sep | +8.65 / +10.52 | +0.55 / +1.87 | +8.10 / +8.65 |
| 2019 | Oct | −2.56 | +0.14 | −2.69 |
| 2020 | Aug / Jul / Jun | +11.76 / +6.73 / +5.09 | +0.63 / −0.19 / −0.03 | +11.13 / +6.91 / +5.13 |
| 2020 | Mar / Feb / Oct | −2.53 / −0.82 / −4.20 | ≤ 0.7 | −2.31 / −0.80 / −3.53 |

- **The ORDC adder matches measured RTORPA** to within about $1 in every month except August 2019, where it is +$9.9. Across all of 2019 the model's adder averages $627 over the 87 hours where it exceeds $100, against measured RTORPA $546 in those same hours; 92 hours have RTORPA above $100.
- **The C3b miss is energy.** Summer energy is over-priced by +$11.99 (2019 Jul–Sep) and +$7.84 (2020 Jun–Aug) load-weighted.
  - By actual energy band, it sits in mid-price hours: actual $25–100 against a model $44–153 (2019), and actual $15–35 against a model $25–45 (2020).
  - By time of day, it concentrates in h13–16, then h17–20.
  - The scarcity hours above $100 are slightly under-priced.
- **The only candidate on record is Q5:** the Decker Creek ST / DeCordova CT membership gap, about 1 GW of 2019/20 summer supply (w2 FINDING §2). It is owner-gated, and its w2 static reach made 2019 C3b worse (0.216 → 0.351) and 2019 C3a fail. So it is not the explanation for this over-pricing as measured. The trough record (model clearing at CC econ $16–17 while the actual clears $9–12) is adjudicated (`DIAGNOSIS-ercot-trough-price-formation`).
- **No further zero-DOF lever** reaching summer mid-merit energy in 2019/20 only is on record or found here. 2021–25 C3b pass, so a mechanism that moves the mid-merit stack in every year would have to hold those.

## 4. Disposition

| # | Question | Disposition |
|---|---|---|
| 1 | 2020 COAL_PRB −8.31 | DATA-LIMITED. Route: R-7 G1 2019–22 SCED intake (owner data decision) |
| 2 | Heat-rate-ordered CC committed level | Not admissible (rules 13/14/1). The commitment-state route is adjudicated; no new evidence |
| 3 | 2019/20 C3b | Energy over-pricing in summer mid-price afternoon hours. No admissible zero-DOF candidate; the Q5 membership arm is owner-gated and its static reach worsens 2019 C3b |

No PRECOMMIT is written and no shards are launched (rule 29: compute what can be computed without an LP first).
