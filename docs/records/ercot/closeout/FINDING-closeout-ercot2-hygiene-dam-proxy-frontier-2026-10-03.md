# FINDING: ERCOT closeout-2 — keeper hygiene (W4), the R-25 DAM-proxy census, and the data-limited frontier (zero LP)

Lane `closeout-ERCOT-2`, desk session_01ALecU5Wjde4tkbLrnMExT9. Written 2026-10-03. **Zero LP; no shard launched.**
Keeper `2026-10-02-closeout-l1-coal-fuel` (bundle `results/calibration/closeout_ercot_l1_span`, 2019–2025; legs 2019 from l1 and 2020–25 from l1b at `106d6bb7`).
PRECOMMIT (readings fixed before any number): `PRECOMMIT-closeout-ercot2-dam-proxy-census-2026-10-03.md`, pushed at `77569e89`.
Probe: `scripts/probes/_ercot_closeout2_dam_proxy_census.py`. Outputs: `data/dam_proxy_{coverage,levels}.csv`, `data/dam_proxy_summary.json`.

## Headline

| Step | Reading |
|---|---|
| 1. W4 hygiene | `unit_marginal_<Y>.parquet` present for all 7 years: **nothing to backfill**. `authorized_price_tuning`: **absent, correctly**, on the CAISO precedent (closeout-C RESULT §2 "W4 hygiene"). The 2023 configuration exception is **live and applied**: the 2023 carve-out scope reads CALIBRATED with 2 off-budget caveats. |
| 2. DAM-proxy census | **P1 FAIL.** The 60-Day DAM curves are not an adequate proxy for the SCED TPO construction. They cover only **9.4–11.0 %** of the coal fleet's ON HSL-hours. 5 of 10 plants, W A Parish among them, submit no DAM curve in any ON hour. Where curves exist, the fleet bias is +$8.08 (2023) and −$10.35 (2024–25) against the SCED basis. **P2 INDETERMINATE**: slope −0.70 $/MWh per $/MMBtu, t = −0.45. The window gives no evidence that 2019/20 coal offers were lower. |
| 3. Frontier | Two DRAFT data-limited ledger rows (§3), for the owner card. **The R-7 intake must be scoped to NP3-965 SCED (G1), not NP3-966 DAM (G2).** The exceptions ledger is not edited. |

## 1. Hygiene (rule 15 / W4)

| Check | Finding | Action |
|---|---|---|
| `hourly/unit_marginal_<Y>.parquet`, 2019–2025 | All 7 present (22.6–32.2 MB). The L1 promotion carried them. | None. A backfill costs nothing, because none is needed. |
| `governance.authorized_price_tuning` | **Key absent.** All four governance assertions are true, so C6 passes without a declaration. The `offer_curve_by_group` bands are two-valued: the forward config 2024–25 differs from the 2023 carve-out / 2019–22 config in every `peak` / `phys_peak` / `peak_ladder` (×33, `ercot_offer_swcap_clip`). They are pre-2026-09-05 residual-identified rows already in the DOF ledger (`free_parameters`, identification `residual`, ≥165 solves). No record shows ERCOT using the post-2026-09-05 rule-1 channel. | **No edit**, on the closeout-C CAISO precedent. A declaration would assert `set_ex_ante` / `not_swept` facts no record supports. It would also fail rule 1(b): `years_held` must cover the run's whole scored span, and the bands are two-valued. Flag for the desk: if the owner ever wants ERCOT's bands under the channel, the declaration needs a per-partition `years_held` reading of rule 1(b). That is a rubric question, not hygiene. |
| 2023 configuration-exception caveat (R-6, rubric v3.14) | Live in `calibration_verdict.py` (`CONFIG_EXCEPTION_ENTRIES`, keyed `("ERCOT", 2023, price_mean/price_shape)`). It binds to the 2023 leg's recipe through `year_scenario_configs` (`ercot_offer_swcap_clip: true`). In `frontend/data/backcast/status/ERCOT.js` the carve-out-2023 scope reads **CALIBRATED**, with the reason "2 owner-signed configuration-exception caveat(s) … 2023 C3a −24.7 % … IMM counterfactual ≈ $35 … C3b NRMSE 0.393". `iso_determination` takes its worst-of over the three partition scopes (forward NOT-YET on C3a 2024; carve-out-2023 CALIBRATED; validation 2019–22 NOT-YET on C1/C3b 2019/20). | None. The top-level `keeper.caveats.configuration_exception` list is empty because it renders the forward scope, so it is not a defect. |

## 2. R-25 DAM-proxy census

**Definition.** The DAM proxy is gap G2 of `SHARD-ERCOT-closeout-research-2026-10-02.md` §6. It is the NP3-966 60-Day DAM Gen Resource `QSE submitted Curve-MW/Price1..10`, read as the "cheaper proxy" for G1: the NP3-965 SCED `Submitted TPO` curves behind `coal_perplant_offer_level` (ERCOT-144 static, from 2024–25 SCED) and the ercot-168 2023 year table. The keeper prices 2019–22 coal at the static 2024–25 levels (R-ERCOT-3 §2).

**On-disk window.**
- **DAM:** delivery 2022-09 → 2026-06. Oct 2023 has one day only. The census uses 2022–2025.
- **SCED corpus:** delivery 2023 plus January 2024 only (publications 2023-03..2024-03). Delivery 2024–25 SCED is not on disk at tip, apart from the 2025 tail-day extract.
- **Nothing for 2019–2021, from either product.**

### 2.1 Coverage (decisive)

Coverage is the share of ON hours with any DAM curve, and the offered curve MW (above LSL) as a share of ON HSL-hours.

| Plant | Class | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| W A Parish | PRB | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Limestone | PRB | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Martin Lake | PRB | 0.65 / 0.00 | 0.89 / 0.00 | 0.91 / 0.00 | 0.89 / 0.00 (15 MW sliver per unit) |
| Coleto Creek | PRB | 0.56 / 0.00 | 0.85 / 0.00 | 0.96 / 0.00 | 0.90 / 0.00 (15 MW sliver) |
| Fayette | PRB | 0.75 / 0.23 | 0.72 / 0.25 | 0.61 / 0.20 | 0.59 / 0.20 |
| Sandy Creek | PRB | 0.88 / 0.11 | 0.77 / 0.13 | 0.93 / 0.13 | 0.93 / 0.13 |
| JK Spruce | PRB | 0.96 / 0.95 | 0.98 / 0.85 | 1.00 / 0.98 | 0.99 / 0.83 |
| Oak Grove, San Miguel, Major Oak | LIG | 0 / 0 (San Miguel 2024: 5 % of hours, 15 MW) | | | |
| **Fleet offered-MW share** | | **0.094** | **0.105** | **0.110** | **0.100** |

Coal owners mostly self-schedule in the DAM. Of the four plants that carry the 2019/20 COAL_PRB miss (Parish, Fayette, Martin Lake, Sandy Creek; R-ERCOT-3 §1), Parish offers nothing, Martin Lake offers a 15 MW sliver, and Fayette and Sandy Creek offer 13–25 %. The DAM disclosure cannot measure the committed/econ capacity windows that the ercot-144/168 construction prices.

### 2.2 P1: level bias where curves exist (pre-fixed threshold max($1, 0.25·Δ\*) = $1.00, and ≥ 8 plants within ±$2)

| Comparison | Fleet bias (MW-weighted) | Plants within ±$2 | Reading |
|---|---|---|---|
| (a) DAM 2023 vs the ercot-168 2023 table | **+$8.08** | 2 of 7 | FAIL |
| (b) DAM 2024–25 vs the keeper static curve | **−$10.35** | 3 of 11 | FAIL |

- The only plant with full coverage is JK Spruce. Its DAM level sits **$4.65–14.34 below** SCED in every year.
- Limestone and Parish appear in (a) only through curves submitted in non-ON hours.
- The plants inside ±$2 are the 15 MW slivers (Martin Lake, Coleto).
- **P1 FAIL.** A 2019–22 G2 intake would not identify coal conduct at the keeper's grain. **G1 (SCED) stays the only route** (R-ERCOT-3 §4 (1)).

### 2.3 Q2: what the intake would have to show (Δ\*, static lower bound from the keeper's own P1 `unit_marginal`)

COAL_PRB committed/econ headroom that clears for a uniform downward offer shift Δ, on the keeper's zonal P1 prices:

| Year | +1 $ | +2 $ | +3 $ | +4 $ | +5 $ | Δ\* to close the pre-fixed miss | Supplementary: Δ to enter the ±8 TWh band (keeper miss −10.79 / −11.85) |
|---|---|---|---|---|---|---|---|
| 2019 | 3.86 | 7.45 | 10.25 | 12.84 | 14.59 TWh | **$3.13** (10.5 TWh) | $0.50 (2.79 TWh) |
| 2020 | 3.23 | 6.22 | 9.21 | 12.43 | 14.99 TWh | **$3.78** (11.8 TWh) | $1.13 (3.85 TWh) |

These are static lower bounds: displaced CC lowers prices, so a real solve needs more. The supplementary column was not pre-fixed and gates nothing. It shows that the C1 PRB band is within reach of a modest conduct difference, if 2019/20 conduct really was lower.

### 2.4 P2 / Q3: direction from the window

- **Regression:** plant fixed effects, MW-weighted, on plant-year DAM levels (5 plants with ≥ 3 years, 20 plant-years). The slope is **−0.70 $/MWh per $/MMBtu, se 1.57, t = −0.45**.
- **Fleet DAM level by year:** 26.0 / 33.8 / 25.8 / 14.9 for 2022 / 2023 / 2024 / 2025. This is composition-driven: Fayette's offered MW moves from 1,066 to 673.
- **Implied 2019/20 shift:** +$0.21 / +$0.58, upward.
- **Pre-fixed reading: P2 INDETERMINATE** (|t| < 2). The window is fuel-invariant at DAM grain.
- **SCED cross-check (keeper's own SCED curves).** The PRB levels move **+$1.56/MWh MW-weighted** (mean absolute $2.5) from the 2023 table to the static 2024–25 curves, across nearly the same gas (HH 2.54 vs 2.86). Year-to-year conduct moves in the measured window are about the size of the band-entry Δ, but they carry no sign that tracks gas. The 2019/20 sign is therefore **unidentified ex ante**.

### 2.5 C3b 2019/20 (0.216 / 0.208, band ≤ 0.20; direction only, not gated)

The summer over-price that carries 61–73 % of the SSE is coupled to the coal under-run: CC and CT sit on the margin in summer (SHARD-ERCOT research §2). A real downward coal conduct shift would lower summer prices and move C3b toward the band. Its size cannot be estimated without an LP.

### 2.6 What the 2019–22 intake would buy

- **G2 (DAM) buys nothing for coal conduct.** About 10 % coverage, no Parish, slivers at Martin Lake and Coleto.
- **G1 (NP3-965 SCED) is the only instrument** with the construction's grain. It would turn the 2019/20 coal rows from "priced at 2024–25 conduct" into measured. The C1 PRB band needs a static ≥ $0.5 (2019) / ≥ $1.1 (2020) downward conduct difference; full closure needs ≥ $3.1 / ≥ $3.8.
- **The direction is unidentified on the evidence on disk.** The intake is a measurement, not a predicted fix. If 2019/20 SCED conduct reads at or above 2024–25, the rows stay NOT-YET as measured. That would be an honest close, and it re-points the miss at fuel or commitment, not conduct.
- **R-7 should be narrowed to G1** (NP3-965 2019-01 → 2022-12 Gen Resource, the 10 coal resources' TPO columns) plus G3 (NP6-576-ER).

**DO-NOT-REDO respected.** No L2 West rating, no `coal_offer_level_rebasis` (R), no sub-zonal split, no ORDC retune, no `coal_fuel_inventory` arm. No owner download (R-17).

## 3. DRAFT data-limited ledger rows (for the owner card; NOT entered in the exceptions ledger)

Form follows `docs/calibration-log/pjm.md` "PJM close-out — 2026-10-02 — Winter Storm Elliott".

```markdown
## ERCOT close-out — 2026-10-0X — 2019/2020 coal offer conduct and the 2024 intra-zone LZ basis closed as DATA-LIMITED residuals (zero LP)

- **Owner ruling:** <card verbatim> (relayed by the close-out desk).
- **Ledger row A:** C1 COAL_PRB / CC_REGULAR 2019, 2020 (−10.79 / −11.85 and +9.21 / +10.17 TWh) and C3b 2019, 2020 (0.216 / 0.208) — coal offer conduct. **DATA-LIMITED.**
  - Reason: the keeper prices 2019–22 coal committed/econ tranches at the 2024–25 ERCOT-144 SCED curves because no 2019–22 SCED TPO disclosure is on disk (R-ERCOT-3 §2). At 2020's HH $2.03 that puts 4.6 GW of coal above the CC p75.
  - Reason: the licence-free DAM proxy (NP3-966) cannot stand in. It covers 9.4–11.0 % of coal ON HSL-hours, W A Parish never offers, and the bias is +$8.08 / −$10.35 against SCED (closeout-2 FINDING §2, P1 FAIL). The on-disk window shows no fuel-indexed conduct (t = −0.45), so the 2019/20 sign is unidentified.
  - Reason: re-coupling offers to fuel is `coal_offer_level_rebasis` (R, wrong sign); reusing 2023 curves is per-year fitting (rule 1(b)).
  - **Re-open** on the R-7 intake narrowed to NP3-965 60-Day SCED Gen Resource 2019-01 → 2022-12 (the 10 coal resources' TPO columns). It feeds `coal_perplant_offer_curves_yearly` by the frozen ercot-168 derive (rule 23), zero DOF. Bar: static ≥ $0.5 / $1.1 lower conduct enters the C1 band; ≥ $3.1 / $3.8 closes it.
- **Ledger row B:** C3a 2024 (−11.3 %) — intra-zone load-zone basis. **DATA-LIMITED.**
  - Reason: the actual LZ_WEST premium over the hub is +$1.30/MWh system-LW in 2024 (2,847 h > $5). The model prints West ≡ North, because it has no sub-zonal West topology.
  - Reason: the L2 census (closeout W1 FINDING §2) shows the premium is a Permian load pocket. Seam binds show no lift, 67–85 % of the premium mass sits in intra-West-only hours, and HB_WEST carries 2–27 %. A zonal import rating cannot reproduce it, and the sub-zonal split is ERCOT-117 (G).
  - Reason: the remainder of the 2024 gap is the ECRS artificial-shortage cost the IMM puts at "almost $1 billion" (≈ $2.16/MWh). That belongs to the regime the carve-out caveat covers for 2023, and 2024 has no such exception.
  - **Re-open** on a public sub-zonal (Permian) driver that ERCOT-117 would admit, or on a rubric ruling extending R-6's configuration-exception logic to the 2024 ECRS-deployment months.
- **Records:** `docs/records/ercot/closeout/FINDING-closeout-ercot2-hygiene-dam-proxy-frontier-2026-10-03.md`, `FINDING-closeout-w1-zero-lp-censuses-2026-10-02.md` §2, `docs/records/ercot/FINDING-r-ercot-3-coal-2019-2020-2026-09-25.md`.
```

**Owner card (to the desk), options with recommendation first:**
1. **(Recommended)** Accept rows A and B as DATA-LIMITED. Narrow R-7 to G1 (SCED) + G3, still deferred under R-17. ERCOT stays NOT-YET, with an honest frontier: 2019/20 and 2024 are each data-limited, with a named re-open.
2. Accept row A only. Keep 2024 open for a rubric ruling on the ECRS-deployment months (an R-6-style extension).
3. Re-open R-7 now (owner download of G1). The intake is a measurement and its sign is unidentified.

Prior R named for the card: `coal_offer_level_rebasis` (R, ERCOT-132/135/143) and `internal_congestion_split` (G, ERCOT-117).

## 4. Matrix

`coal_perplant_offer_level` (ERCOT shard) stays **K**. A census note is appended: DAM-proxy P1 FAIL, G1 is the only admissible 2019–22 source.
