# FINDING — R-ERCOT-9: the 2023 gap is energy-offer price formation, not tightness; ERCOT zonal actuals repaired to the standard clock

**Session:** R-ERCOT-9, 2026-09-27. **Keeper (unchanged):** `2026-09-27-r-8-fusco` (bundle `results/calibration/r_ercot8_fusco_span`). **Zero LP** — no solve, no shard, no mechanism tested, no matrix cell moved (rule 28(b) not engaged). Superseded-keeper hourlies read from git history at `f41f4eb5^` (`r_ercot5_hourgrain_span`).

Probes (all zero-LP, committed):
- `scripts/probes/_r_ercot9_2023_tight_hours.py` — tight / lost-hour decomposition.
- `scripts/probes/_r_ercot9_rt_hour_alignment.py` — hour-alignment audit of the scored actuals.
- `scripts/probes/_r_ercot9_dam_top_offer.py` — measured 2023 DAM top-of-curve offers.

## Headline

1. **The 2023 C3a/C3b gap is in the energy-offer component of tight hours.** It is not physical tightness, and it is not the reserve/ORDC adder.
2. **No new structural, rule-13-admissible mechanism exists for it.** The lever that moves it is the carve-out's peak-band level (k = 33). That level was swept against the gates by ercot-235/236 on a fleet missing Jack Fusco. It is the rules 1/13 authorized channel only on a fresh owner declaration. Measured offers do not support raising it.
3. **Side repair (rule 14): the ERCOT zonal actual series was on the wrong clock.** It sat on the prevailing clock during daylight saving time, one hour late against the model in ~65 % of hours, in every year 2018–2026. The derive is fixed and re-derived.
   - Scored `rt_lw` moves by −0.35 to +0.70 $/MWh.
   - It enters the keeper's scores at its next registration; the committed payload still carries the old basis.
   - It makes 2023 C3a slightly worse: est. −19.8 → −20.6 %.

## 1. Tight hours (2023, standard clock)

In the 62 hours with actual load-weighted RT ≥ $1,000:

| quantity | measured | model (keeper) |
|---|---|---|
| price | $2,389 | $1,343 |
| energy component | λ $2,284 | price − ORDC adder $1,142 |
| ORDC / reliability adders | RTORPA $68 + RTORDPA $53 | ORDC adder $201 |
| reserve headroom | PRC 5,215 MW | ORDC-total held ≈ 3,850 MW (at measured λ ≥ $1k hours) |

- The model is physically **tighter** than the market and its ORDC adder is already **higher**. Measured scarcity was ~96 % energy-offer (λ) formed.
- Measured λ reaches $1k+ at PRC 4–5 GW. The model needs held reserves ≤ ~4 GW to price above $1k.

Where the 2023 gap sits, by actual price band ($/MWh of the annual mean):

| actual band | hours | gap |
|---|---|---|
| < $200 | 8,571 | **+0.72** |
| $200–1k | 127 | −2.31 |
| $1k–3k | 44 | −4.26 |
| ≥ $3k | 18 | −3.14 |

The body is fine. The LZ congestion basis (FINDING-r-ercot-6 §2) is not the 2023 object.

## 2. The 22 hours Fusco removed

- **Inputs:** demand and storage are identical. The class delta is Fusco (CC_REGULAR +374 MW) against CT_PEAKER −325 and CC_CHP −114. Reserve duals and `reserve_price` are unchanged.
- **Price:** it falls about 2:1, for example $1,395 → $689 and $1,615 → $943.
- **Mechanism:** in those hours every CC_REGULAR and CT_PEAKER peak tranche dispatches **0 MW** of energy, because it is held for AS. The energy price is set by whichever **CHP peak tranche** is marginal:
  - before Fusco, CC_CHP peak (123.684× ≈ $1.4k), partly loaded;
  - after Fusco, CT_CHP peak (43.56× ≈ $0.65k).
- **Conclusion:** 2023 tight-hour prices are a staircase of k-scaled band steps. One 676 MW plant moves the marginal step. The carve-out's C3a was resting on the missing plant.

## 3. The authorized channel, measured

- The carve-out's peak bands are exactly the forward bands × 33: 151.008 = 4.576·33, 433.95 = 13.15·33, 123.684 = 3.748·33, 43.56 = 1.32·33.
- k was selected by sweeping against the gates (ercot-235 grid → ercot-236 k33), before the 2026-09-05 amendment's condition (c).
- Measured Aug-2023 HE15–20 DAM submitted curves, price at the top of each resource's curve:

| resource type | median | p75 |
|---|---|---|
| CCGT90 | $24 | $146 |
| SCGT90 | $45 | — |
| CCLE90 | $41 | — |
| GSREH | $43 | $999 |

- **$4,550–5,000** offers are HYDRO, PWRSTR (storage) and GSNONR.
- Caveat: few rows carry DAM energy curves (n = 12–403 per type), so this is indicative, not a derivation.
- **So:** a measured re-anchor of the gas peak bands would lower them, not raise them. This agrees with the standing C3c ledger (ercot-161: storage offers made the ≥ $500 stack). k = 33 on gas tranches stands in for conduct that sat elsewhere in the market.

## 4. Clock repair (rule 14)

**Defect.** `scripts/data/derive_ercot_zonal_lmp.py` placed ERCOT's prevailing-clock hour labels straight onto the 8760 index. The sibling hub series (`derive_actual_lmp._ercot_hubavg`) shifts them to standard time with `_PrevailingShift`.

Measured before the fix:
- July, zonal `HB_HUBAVG[t+1]` vs hub `[t]`: corr = **1.000** in every year 2018–2026. At shift 0: 0.40–0.87.
- January: aligned.
- The model's solar centroid is 12.6–13.1 h in every month, so the model is on the standard clock.

**Fix.** The same `_PrevailingShift` helper, with the Repeated Hour Flag, is now used for RTM and DAM.
- After re-derivation, zonal `HB_HUBAVG` equals the hub series to ≤ $0.0005 in every year.
- January is byte-unchanged.

**Solve impact: none.** The parquet's only solve consumer is `derive_reliability_deployment.py`, whose overlay is off in the keeper.

**Scoring impact.** `actual_lmp.json` ERCOT `*_lw` fields were re-derived for 2019–2025; 2018 was left as committed and no other ISO was touched.

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| rt_lw before → after | 46.90 → 46.55 | 25.50 → 25.40 | 165.53 → 165.95 | 74.44 → 75.08 | 64.32 → 65.02 | 30.99 → 31.17 | 36.29 → 36.50 |

- 2023–2025 move by the clock alone.
- 2019–2022 also absorb pre-existing staleness of the committed JSON against the committed parquet and demand (e.g. 2019: −0.07 clock, −0.28 stale).
- Estimated C3a at the next re-render, with keeper LW unchanged: 2023 −20.6 %, 2024 −8.8 %, 2025 −9.2 %, 2019 +27.0 %. No determination flips.
- Checks run: tests `tests/curation/test_curate_validation.py` and `tests/scoring/test_calibration_verdict*.py` pass (197). `audit_keepers --check` shows 0 failures and the same 14 warnings before and after.

## 5. Routed

1. **Owner decision** on the 2023 carve-out level — decision card in this session.
2. **Validation years** (lower priority):
   - 2019/2020 COAL_PRB C1 shortfall;
   - 2022 CC_REGULAR C1;
   - the Decker Creek 3548 retirement seam.
3. **Not ERCOT's to fix:**
   - Fusco is double-counted in MISO (MISO lane, rule 25);
   - `build_ercot_dam_resource_crosswalk.py` drops the coal rows at HEAD (COAL-SUB);
   - 25 base-red fast-tier tests on main.

## 6. Owner ruling (decision card, 2026-09-27)

Verbatim answer: **"Hold k=33, work validation (Recommended)"**.

- The keeper and the carve-out's `offer_curve_by_group` stay unchanged. No re-declaration, and no sweep.
- 2023 stays NOT-YET at full magnitude, so ERCOT stays NOT-YET.
- The next lane works the physical validation-year items:
  - 2019/2020 COAL_PRB C1 shortfall;
  - 2022 CC_REGULAR C1;
  - the Decker Creek 3548 retirement seam.
