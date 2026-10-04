# FINDING: ERCOT close-out w2 — §3.5 queue state and the 2019–25 CSV membership-gap reach (zero LP)

Lane `closeout-ERCOT-w2`, desk session_01ERkBTm23ZAP4CTZnJVD9Ss, 2026-10-03. Branch `claude/closeout-ercot-w2` from `main` 1e3e4177.
**Zero LP. No shard launched. No `src/` edit.** Keeper `2026-10-02-closeout-l1-coal-fuel` (bundle `results/calibration/closeout_ercot_l1_span`), rubric v3.20.

## Headline

1. **The §3.5 queue has no open step this lane can build.** Steps 0a, 0b and 1 are done. The step-2 census already ran and failed, so step 3 is not chartered. Steps 4 and 5 are on the owner's side. Step 6 is done apart from the membership gap below.
2. **One new structural defect, measured.** The ERCOT curated sheet leaves out about 1.0 GW of operable grid thermal capacity in 2019–2020: Decker Creek ST1/ST2 and DeCordova CT1–4. DeCordova (280 MW) is also missing from every later year.
3. **The static reach of fixing it points the wrong way on price.** It predicts 2019 C3a PASS→FAIL, a worse 2019 C3b, and 2024 C3b and 2022 C3a/C3b at or over their lines. Under rule 14 a worse fit after real data points to a compensating error somewhere else, so the repair is not chartered as a lever here. It is routed to the owner as an input to the Q5 "migrate later" ERCOT-CSV ruling (D-P2), together with this prediction.
4. **ERCOT stays NOT-YET.** The live FAILs at HEAD are C1 2019/20 (CC_REGULAR +9.21/+10.17 TWh, COAL_PRB −10.79/−11.85), C3b 2019/20 (0.216/0.208) and C3a 2024 (−11.3 %). R-32 rules all of them DATA-LIMITED, and their only route is the R-7 G1/G3 intake.

## 1. §3.5 queue, step by step

| # | Step | State | Evidence |
|---|---|---|---|
| 0a | R-ERCOT-24b ORDC published curve | DONE | promoted, PR #7017; carried into the l1 keeper's governance chain |
| 0b | L1 census | DONE | `../closeout/FINDING-closeout-w1-zero-lp-censuses-2026-10-02.md` §1 |
| 1 | L1 coal fuel ceiling | DONE | keeper `2026-10-02-closeout-l1-coal-fuel` (R-18 "Override + promote") |
| 2 | L2 census (NP6-86 West-import binds) | **FAILED, closed** | same FINDING §2: seam-bind cover is 0.7–14.2 % of the > $5 premium hours against a ≥ 70 % bar, with no lift over base hours. The premium is an intra-West Permian load pocket. |
| 3 | Asymmetric West import link | **NOT CHARTERED** | gated on step 2. No new evidence since 2026-10-02: R-32 ledgered the 2024 West LZ basis DATA-LIMITED and named the G1/G3 intake as its re-open. Building it now would be the refused sub-zonal split (`internal_congestion_split` G) under another name. |
| 4 | 2019–22 per-plant coal offer tables | OWNER-GATED | R-7 narrowed to G1 (NP3-965 SCED) + G3 (NP6-576-ER) by R-32. Deferred under R-17. The account-free DAM proxy failed adequacy (closeout-2 FINDING §2: 9–11 % coverage). |
| 5 | 2023 | RULED | R-6 / R-42 / R-51. The 2023 configuration exception is live and non-downgrading. |
| 6 | Hygiene | DONE except membership | closeout-2 FINDING §1 (unit_marginal present for all 7 years, no `authorized_price_tuning` owed). The CDR/COD cross-check is still DATA-BLOCKED (G8). Membership: §2 below. |

None of this lane's work tests an R/I/G matrix cell, so the ERCOT matrix shard is not edited.

## 2. The membership gap (W0 Q5 audit, read against EIA-860 and EIA-923)

Source: `docs/records/governance/closeout-2026-10/W0-census/ERCOT/fleet_census_<Y>_w0.json` → `ercot_csv_audit`. Industrial-CHP rows (52120 Freeport, 55470 Green Power 2, 50304 Shell Deer Park) are left out because the ERCOT fleet scores grid-delivered energy and treats CHP host supply separately. That leaves two grid units missing:

| Plant | Units | EIA-860 summer MW | In the curated sheet | EIA-923 net generation, GWh (2019 / 20 / 21 / 22) |
|---|---|---|---|---|
| Decker Creek 3548 (Travis, South_Central) | ST1, ST2 (gas steam) | 320, retired 2020-10; 404, retired 2022-03 | no. The sheet's 206 MW row is the four GTs only, typed CT_PEAKER | ST 653 / 657 / 630 / 73 |
| DeCordova 8063 (Hood, North) | CT1–CT4 (GT) | 280 (69–71 each) | **never** (no `git log -S` hit) | GT 23 / 22 / 61 / 79, then 113 / 53 / 70 in 2023–25 |

How the sheet hides them: ERCOT gas and coal capacity comes **only** from `custom-bin-assignments.csv`. The ERCOT branch of `build_base_fleet` drops every EIA-860 or retiree-injected gas and coal unit through `nonthermal_exclude` (`assembly.py:1853-1864`), so `partial_plant_exit_carry`, `mid_vintage_exit_carry` and `carry_operating_mothballs` are inert for ERCOT. The COD mask (`cod_ramp.generator_online_mask`) scales a CSV bin but never adds capacity beyond it.

ERCOT-146 / the ercot-188 card #5 listed "Decordova" as a mixed facility carried under another class. That is wrong: plant 8063 has never been on the sheet.

## 3. Static reach (zero LP, `data/m1_static_reach.json`)

**Estimator.** Built on the keeper's own sidecars:

- Per year, fit the load-weighted P1 price as a monotone function (PAVA) of the hour's total reserve shortfall (`reserve_family_<Y>`) over Jun–Sep.
- In every hour with a shortfall, cut the shortfall by `eff` × the added summer MW and move the price by the fitted delta. DeCordova counts in all years; Decker ST1 to 2020-09 and ST2 to 2022-02.
- Leave non-shortfall hours unchanged. The units sit above the CC stack, so the merit-order effect is ignored.
- Score with the rubric's own monthly NRMSE and annual LW mean against `bench/ERCOT/<Y>.json.gz`. The keeper column reproduces the scorer exactly (0.216 / 0.208 / +6.2 % / +2.5 % / −11.3 %).

The fitted slope pools hours with different conditions, so it probably **overstates** the effect. Treat it as a direction and an upper bracket, not a forecast.

| Year | C3a keeper | C3a eff 0.5 / 0.9 | C3b keeper | C3b eff 0.5 / 0.9 | Reading |
|---|---|---|---|---|---|
| 2019 | +6.2 % PASS | −20.2 / −32.0 % | 0.216 FAIL | 0.351 / 0.590 | C3a **PASS→FAIL**; C3b worse. The August model drops below actual: the 2019-08 scarcity actually happened with Decker online. |
| 2020 | +2.5 % PASS | −6.1 / −10.2 % | 0.208 FAIL | 0.200 / 0.228 | the target gate sits on the line in one arm and is worse in the other. Not a credible FAIL→PASS. |
| 2021 | +0.8 % | −0.2 / −1.0 % | 0.066 | 0.071 / 0.078 | inert |
| 2022 | −8.4 % PASS | −9.7 / −10.8 % | 0.178 PASS | 0.192 / 0.206 | C3a and C3b at or over the line |
| 2023 | −24.7 % (exception) | −26.7 / −28.1 % | 0.393 (exception) | 0.430 / 0.458 | worse, but inside the configuration exception |
| 2024 | −11.3 % FAIL | −11.6 / −11.8 % | 0.198 PASS | 0.201 / 0.203 | C3b **PASS→FAIL** by about 0.003 |
| 2025 | −9.2 % PASS | −9.3 % | 0.125 | 0.125 | inert |

**Verdict: NOT CHARTERED as a lever.** The charter's phase-0 bar needs the target gate (2020 C3b) to move by a stated amount toward PASS. The estimate puts it on the line at best, and it predicts PASS→FAIL flips on 2019 C3a and 2024 C3b.

This is **not** a reason to keep a measured-wrong fleet (rule 14). It means a compensating error is sitting in the 2019/2020/2022 summer price formation, and the most likely place is the shortfall-to-price slope. A run that adds the units without finding that error would be a fit regression no promotion card could carry. Two things belong together in Q5:

- the repair, carried as a supplement in its own arm, because the forecast path reads this CSV without the backcast COD mask, so a plain CSV edit would put a phantom Decker ST into every forecast year;
- the compensating-error diagnosis that comes with it.

## 4. Asks for the desk (owner-side)

1. **R-7 (G1 + G3)**, unchanged from R-32. It is the only route for C1 2019/20, C3b 2019/20 and the 2024 West basis. Every remaining FAIL routes through it.
2. **Q5 ERCOT-CSV migration (D-P2 "migrate later").** Here is the measured membership gap, with the prediction that repairing it worsens 2019 C3a / 2024 C3b on the static estimator. The owner decides whether Q5 moves up, paired with a compensating-error lane, or stays deferred. Either way, ercot-188 card #5 should be corrected: DeCordova is absent, not mis-classed.
