# NYISO Aug/Sep-2023 LMP overrun & Dec-2024/Jan-2025 underrun — diagnosis + fix probes (2026-07-17)

Session branch `claude/lmp-nyiso-overrun-underrun-qvv26u`. Baseline keeper
`2026-07-13-nyiso-62-cc-hr` (bundle `results/calibration/nyiso62_cc_hr_regate`).
All probes solved in-session, 3 years/bundle (rule 16), scored on P1.

## 1. The two signals (model − actual, DA monthly, demand-weighted)

| target | baseline Δ | detail |
|---|---|---|
| **SUMMER** Aug+Sep 2023 (mean) | **+10.9** | Aug +14.6 ($41.5 vs 26.8), Sep +7.2; concentrated in NYC afternoon peak HE15–18 (HE17 RT +$46). NYC afternoon LMP median $37 but MEAN $111 → ~18 excess scarcity spikes (ORDC hours>$200: model 28 vs actual 10). |
| **WINTER** Dec24+Jan25+Feb25 (mean) | **−16.0** | Dec 2024 −18.1 ($49 vs 67), Jan 2025 −18.4 ($97 vs 115), Feb 2025 −11.6. ORDC hours>$200 UNDER-fire: 2024 3 vs 12, 2025 25 vs 42. |

Both partially offset in the annual mean (2023 +1.2, 2024 −2.0, 2025 −2.0), so C3a
passes on the keeper; the errors are in the monthly *shape*.

## 2. Root causes (5-avenue read-only diagnostic + confirmatory probes)

**SUMMER = reserve co-optimization (ORDC) OVER-FIRING on the tightest afternoon hours.**
- NOT load (measured EIA-930, understated 26.75 vs ~30 GW peak → would push prices *down*), NOT peaker fuel (peakers on cheap $1.45/MMBtu summer gas, *under*-dispatched), NOT imports (4,350 MW cap unbound — imports only ~2,057 MW at summer peak), NOT ST_GAS *volume* (see S1 below).
- The overrun is the ORDC scarcity adder on the ~18 excess >$200 spike hours (reserve supply is marginally short at summer afternoon peak; the measured reserve requirement is correct and flat/summer-dipping, so it is a *supply* tightness, largely the NYCA system tier).
- A compounding, genuine construction defect: the NYISO ORDC shortfall-step **widths** are built from the *static published* requirement while the balance RHS enforces the larger *measured* requirement (`nyiso_dynamic_reserve_requirements`). For SENY (downstate, ⊃ NYC) measured ≈1,600 (max 1,800) vs static 1,300, so the demand curve is ~23% too steep and saturates at reserve=300 MW instead of 0 — over-pricing downstate summer reserve shortfalls. The published RCPF penalties are requirement-INDEPENDENT (`penalties[k]=max_pen·(k+1)/n_ramp`), so only the widths carry the level; the fix is a construction-consistency correction (the `nyiso_dynamic_reserve_requirements` docstring already *claims* the steps "translate with the requirement" — the code did not).

**WINTER = the monthly-flat oil-parity cap holds the cold-day peaks down.**
- The gas hub overlay ALREADY spikes cold days correctly (2025 winter max **$84.97/MMBtu**; Transco Z6 NY hit $97.9 on 1/17/2025) — gas granularity is NOT the problem.
- On cold days gas ≫ oil, so ~313 dual-fuel tranches (16.5 GW) switch to oil at the **monthly-flat EIA-923 parity (~$18.8/MMBtu Jan-25)**; 120 of 744 Jan-25 hours clear on this flat cap, so the polar-vortex peak cannot form. NOT reserves (winter has slack), NOT load. The whole-month LEVEL underrun (esp. Dec-24, gentle-spike month) is the downstate hub winter level.

## 3. Probes run (all 3 years, P1)

| config | 36-mo MAE | RMSE | Aug+Sep23 | winter (Dec24/Jan25/Feb25) | verdict |
|---|---|---|---|---|---|
| baseline (keeper repro) | 4.33 | 6.36 | +10.9 | −16.0 | reference |
| **S1** `gas_st_netload_drag` (NYISO-derived) | 4.48 | 6.59 | +11.2 | −17.3 | **REJECTED** — worse |
| **S2** `nyiso_ordc_measured_step_span` | **4.22** | **6.20** | **+9.2** | −16.0 | clean summer win |
| **W1** `nyiso_iroquois_winter_spread` | 4.38 | 6.14 | +9.8 | **−4.4** | winter fix |
| **S2+W1** combined | 4.31 | **6.00** | **+8.1** | **−4.4** | addresses both |

- **S1 (rejected):** swapping the NYC/LI ST_GAS temperature reliability-floor (evening ramp forces steam to 0.63–0.83 of capacity in HE14–21 vs measured CAMPD CF 0.11–0.17) onto the measured net-load drag (slope 0.02923, int −0.2965, cap 0.29 from `derive_nyiso_st_gas_netload_drag.py`) cut the summer ST_GAS forcing to ~0.29 but left the summer LMP UNCHANGED (+10.9→+11.2) and reserve_price $55.4→$55.8. **Proves ST_GAS volume is not the summer price-setter; the overrun is reserve-scarcity-driven.** (Kept off.)
- **S2 (clean structural win):** widths from the measured requirement span (see §4). NYC Aug/Sep HE15–18 reserve adder $55.4→$41.3, LMP $111→$97; summer +10.9→+9.2; **zero fuel-mix change** (pure price mechanism); winter untouched. The residual +9.2 is the NYCA-tier supply tightness (measured==static, so unaffected by the SENY width fix) — a deeper reserve-supply gap.
- **W1 (winter fix):** the measured Iroquois–Transco winter spread reconciled by the Algonquin scarcity signal (existing flag, replaces the "flat committed" construction — rule-11 measured > estimate). Winter −16.0→−4.4 (Dec-24 −18.1→−0.7, Jan-25 −18.4→−14.0, Feb-25 −11.6→+1.5), RMSE 6.36→6.14. Cost: it is annual-mean-preserving, so it robs summer-2025 and over-raises Dec-2025 (+6.6→+18.9, amplifying a pre-existing Dec-25 over-price) and shifts ~1–1.6 TWh (CC_REGULAR↑, ST_GAS↓) in 2025.

## 4. The S2 fix (`nyiso_ordc_measured_step_span`, gated default-OFF)

Two-line-of-logic change in `reserve_config._nyiso_design` + one ScenarioConfig
field. When on (NYISO + `energy_reserve_coopt` + dynamic requirements), each
dynamic family's ORDC step widths are built from `max(measured requirement)`
instead of the static published MW. No-op where measured==static (NYCA, East,
NYC). Byte-identical when off. `tests/test_reserve_config.py` 94/94 pass.

The exact diff is committed alongside this doc as
`docs/handoffs/nyiso-ordc-measured-step-span.patch` (`git apply` it; the local
session tree already carries it). A cleaner keeper implementation would make the
widths **hourly** `(n_steps, T) = requirement[t]/n_ramp` (dispatch
`build_variable_bounds` currently validates `(n_steps,)` only) — the static
per-family max is a correct-at-peak approximation that reduces the over-fire
where it binds.

```diff
@@ reserve_config._nyiso_design @@
-        p, w = nyiso_rcpf_product_shortfall_steps(req, crit, pen, n_ramp=n_ramp)
+        step_req = req
+        if name in dynamic_req and getattr(
+            config, "nyiso_ordc_measured_step_span", False
+        ):
+            step_req = max(float(np.max(dynamic_req[name])), float(req))
+        p, w = nyiso_rcpf_product_shortfall_steps(step_req, crit, pen, n_ramp=n_ramp)
```

## 5. Combined (S2+W1) criteria — NO load-bearing regression

Official scorer on `results/calibration/nyiso_probe_combined_s2w1`
(registered locally as `2026-07-17-nyiso-63-ordc-span`):

| criterion | tier | verdict |
|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** |
| C2 system volume | load-bearing | **PASS** |
| C3a mean LMP | load-bearing | **PASS** |
| C3b price duration/shape | load-bearing | **PASS** |
| C4 dispatch correlation | supporting | **PASS** |
| C7 diurnal shape (D-1) | protective | PASS (ST_GAS r 0.96/0.956/0.967) |
| C8 forced-energy share (D-2) | protective | grounded-above-budget PASS (D-1+D-4 pass, same category as keeper) |
| C5a CO2 vs eGRID | load-bearing | CAVEAT (commercial band, == keeper) |
| C3c price tail (RT) | supporting | ledgered CAVEAT (needs attestation; == keeper) |
| C6 governance | protective | UNATTESTED (probe has no attestation) |

Every load-bearing (C1–C4) and protective (C7/C8) criterion holds — the combined
config **fixes both targets without regressing the calibration**. C6/C3c-ledger
are attestation-dependent promotion artifacts, not model regressions.

## 6. Disposition & follow-ups (owner-gated — NYISO is frontier/calibration-complete)

- **S2 is a rule-1 correctness fix** (most-faithful, MAE↓, RMSE↓, zero fuel-mix move, no side effects) — recommend adopting; promote via leave-one-year-out (rule 22) + attestation, owner-only keeper swap.
- **W1 fixes the requested Dec-24/Jan-25 winter underrun** strongly (measured mechanism), with a documented Dec-2025 over-shoot that is the discovered next residual (a pre-existing 2025-winter over-price the spread amplifies).
- **Summer residual (+8–9):** the NYCA-tier reserve *supply* tightness at afternoon peak — the model lacks the DR/import operating-reserve providers NYISO clears (SCR/EDRP ~1 GW). A reserve-provider build, its own charter; a reserve-penalty knob would be residual-fitting (rule 12/13) and is refused.
- **Winter residual (Jan-25 −14):** the flat oil-parity cap. The clean lever is a **daily oil parity** from a measured NY Harbor No.2 / ULSD daily spot (mean-preserving to the EIA-923 monthly) — NOT on disk; a small data intake + `dual_fuel_oil_price_series` (fuel.py) shaping. Documented for follow-up.
- Bundle dashboard registration + `keepers.json` are NOT edited here (frontier ISO, owner decision). Reproduce: apply the patch, then `replay_keeper.py results/calibration/nyiso62_cc_hr_regate --set nyiso_ordc_measured_step_span=true --set nyiso_iroquois_winter_spread=true`.
