# FINDING: ERCOT close-out w4, phase 0 (zero LP)

Lane `closeout-ERCOT-w4`, desk session_01ERkBTm23ZAP4CTZnJVD9Ss, 2026-10-05. This lane is stacked on the w3 cliff-split probe (`RESULT-closeout-ercot-w3-coal-cliff-split-2026-10-04.md`, PR #7197); its six legs are the control.

All readings come from the composed w3 span `results/calibration/closeout_ercot_w3_span` (keeper recipe + `coal_perplant_cliff_split`), the shared EIA-923 frame, `campd_cc_heat_rates_ERCOT.csv`, and zero-LP fleet rebuilds (`scripts/lib/bundle_fleet.reconstruct_bundle_fleet`). Scripts: `data/plant_gap.py`, `data/warm_committed_reach.py`.

## Headline

1. **The P1 startup markup inverts ERCOT's measured coal curve on the committed tranche.**
   - `model/commitment.py::compute_monthly_markup` amortizes the $100/MW coal start over each month's P0 run length and adds it to every coal `_committed` tranche in P1. The base cost is the ERCOT-144 curve level, and it is monotone.
   - In P1 the committed tranche bids above the plant's own econ tranche. Martin Lake: base $21.53, P1 median $28.55 (2019) / $31.71 (2020), against its econ $22.20. Sandy Creek: base $31.05, P1 $47.72 / $45.85, with whole months at $131, against its econlo $33.92. Parish, Coleto, Fayette and Limestone show the same pattern.
   - The code's own comment names this the "run-97b inversion" (Parish cited).
2. **The fix exists and is armed on another keeper.** `coal_warm_committed` (registered under `p1_bidcost_pass`, rule 28(c)) exempts a coal bin whose per-plant must-run floor keeps the boiler warm. It is armed on the MISO keeper and has no ERCOT cell or record. ERCOT's committed rows all carry `must_run_pct` of 12–55, so the exemption's gate is met on every plant. It enters ERCOT as `U` (rule 28: transfers are re-tested in the target ISO).
3. **It reaches the 2019/20 residual directly.** Static reach, prices held (an upper bound): coal +2.59 TWh in 2019 and +3.69 TWh in 2020. Martin Lake (+1.11 / +1.17) and Parish (+0.71 / +1.04) carry most of it, and they are the two largest 2019/20 COAL_PRB under-runners.
4. **CC_REGULAR's 2019/20 over-run is a within-class inversion against heat rate, already adjudicated (§2).** No new candidate comes from it.

## 1. Residual after the cliff split (w3 arm, model − EIA-923, TWh)

| Record | 2019 | 2020 | Plants carrying it |
|---|---|---|---|
| COAL_PRB (band ±8.0) | −9.57 | −10.85 | Martin Lake −3.23 / −6.00, Fayette −2.48 / −2.21, Sandy Creek −1.83 / −1.32, Parish −0.96 / −1.60 |
| CC_REGULAR | +8.45 (verdict) | +9.60 | §2 |

- **Martin Lake and Parish 2019/20.** Their per-year conduct is the R-32 DATA-LIMITED object. Their committed tranches carry the §3 inversion in every year, and the inversion is largest in 2019, 2020 and 2024.
- **Fayette.** Its residual sits on the `_econhi` side ($108), which is the static 2024–25 curve applied to 2019/20 (R-ERCOT-3). It is also data-limited.

## 2. CC_REGULAR: within-class inversion (no new candidate)

The over-run is not class-wide. It follows heat rate inversely and persists in every year 2019–2025:

- **Always over-run:** T H Wharton (HR 9.5; +1.4 to +2.7 TWh), Midlothian (7.7; +1.0 to +3.3), Nueces Bay, Wise County.
- **Always under-run:** the most efficient units: Freestone (6.9–7.1; −1.3 to −1.8), Guadalupe, Lamar, Odessa-Ector, Forney.
- **Why:** the committed-block level (ERCOT-139, $10.354 at the gas anchor) is heat-rate-flat. Across 43 plants (2024), the correlation of median committed mc with CAMPD heat rate is 0.06. The spread is zonal gas basis: committed medians are Houston $5.5, West $6.0, North $9.5, South_Central $11.6 and South $12.0. So inefficient Houston and West CCs bid below efficient North CCs.
- **Status:** this is R-ERCOT-19's finding. Its fix, `cc_committed_prior_year_commitment_eligibility`, was probed and not promoted (2022 CC C1 regressed), and it fails closed in 2019. Nothing here is new evidence (rule 28), so it is not re-tested.
- **Expected effect of w4:** the warm-committed coal MWh displace CC MWh in the same hours, so CC_REGULAR should come down as coal goes up.

## 3. Warm-boiler exemption: static reach by year

The method holds the w3 arm's hourly zonal prices fixed. For each hour where the zone price lies between the committed tranche's base cost and its P1 bid, it counts the committed headroom as added MWh. This is an upper bound: re-clearing lowers prices and cancels part of it.

| Year | Added coal TWh | Martin Lake | Parish | Coleto | Sandy Creek | Other |
|---|---|---|---|---|---|---|
| 2019 | +2.59 | +1.11 | +0.71 | +0.34 | +0.20 | +0.23 |
| 2020 | +3.69 | +1.17 | +1.04 | +0.27 | +0.13 | +1.08 (Fayette +0.41, Spruce +0.35, Limestone +0.25) |
| 2021 | +0.75 | +0.40 | 0.00 | +0.18 | +0.15 | +0.02 |
| 2022 | +0.83 | +0.47 | 0.00 | +0.16 | +0.20 | 0.00 |
| 2024 | +2.25 | +1.20 | +0.33 | +0.10 | +0.22 | +0.40 |
| 2025 | +0.64 | +0.42 | +0.07 | +0.08 | +0.04 | +0.03 |

- **Where it acts.** The markup is largest in years when P0 runs the committed tranche in short blocks, which is exactly when it is mispriced. 2021 and 2022 are tight years with long committed runs, so the markup is small there.
- **Oklaunion.** Plant 127's committed row sits at $126–130 in 2020–25, but it has 0 MW from 2021 on (retired 2020-09) and carries ≤ 0.02 TWh. Its reading is immaterial.
- **Risks.** 2024 C3a (−11.9 % FAIL) and C3b (0.201 FAIL) worsen as coal clears cheaper. 2025 C3a (−9.9 %, $0.03 inside the −10 % line) is at risk of flipping to FAIL.

## 4. Candidate

| # | Candidate | Matrix | Reach | Disposition |
|---|---|---|---|---|
| 1 | `coal_warm_committed` on the cliff-split recipe | `p1_bidcost_pass` sub-scalar; ERCOT `U` (MISO keeper arms it) | 2019/20 COAL_PRB and CC_REGULAR toward their bands; Martin Lake and Parish in every year | **PRECOMMIT**; no code (the flag exists at the solve base) |
| 2 | CC committed heat-rate-flat level | `cc_committed_offer_margin` K (R-ERCOT-19 sub-gate probed, not promoted) | CC_REGULAR within-class | no new evidence; not re-tested |
| 3 | 2019/20 per-plant coal conduct (Martin Lake, Parish, Fayette `_econhi`) | R-32 / R-ERCOT-3 | the data-limited half of COAL_PRB | data-limited |
