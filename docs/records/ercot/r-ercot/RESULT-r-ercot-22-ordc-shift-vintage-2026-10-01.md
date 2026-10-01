# RESULT — R-ERCOT-22: the scarcity-tail sensitivity, and the PUCT 48551 ORDC shift vintage — PROMOTED; ISO stays NOT-YET

- **Promotion basis.** The owner's standing instruction (handoff, verbatim): *"Is it an improvement? Then promote"* (rules 31 / 35). No new decision card was needed.
- **Keeper:** `2026-10-01-r-22-ordc-shift`, bundle `results/calibration/r_ercot22_span`, covering 2019–2025. It supersedes `2026-10-01-r-21-lostpines-ccid`.
- **Records:**
  - PRECOMMIT: `PRECOMMIT-r-ercot-22-ordc-shift-vintage-2026-10-01.md`, pinned SHA `f4d29d72fa9839e49518453ac9dd45f6ea739734`.
  - Phase 0: `scripts/probes/_r_ercot22_ordc_shift_id.py`, which writes `r_ercot22_phase0.json`.
  - Scorecard: `r_ercot22_scorecard.json`.

## 1. Task 1 — why 365 MW of CC moved the tail (zero LP)

**The ORDC did not move. The energy dual did.** The table covers the hours the r-20 keeper priced above $200.

| Year | ΔLW | Energy-dual part | ORDC-adder part | ORDC-total family (dual / held / shortfall) |
|---|---|---|---|---|
| 2019 | −2.38 | −2.76 | +0.38 | 784.5 / 4,231 / 4,997 in both runs |
| 2023 | −3.10 | −3.28 | +0.18 | 155.2 / 4,702 / 3,223 in both runs |
| 2024 | −0.03 | −0.04 | 0.00 | identical |

- **Why the reserve side is fixed.** Reserve supply is capped at **measured** RTOLCAP/RTOFFCAP, so the ORDC reserve level is exogenous in a backcast and does not respond to fleet changes.
- **What moved.** About 280 MW of Lost Pines dispatch displaced the top of the stack: CT econ c04/c05, oil, CC_CHP peak, and the upper CC econ tranches. λ fell from roughly $1,000–1,500 to $300–900 in hours with zero slack.
- **Interpretation.** The model sits on the steep, *measured* top-of-stack offer surface (K cells `ercot_offer_surface_position_tail`, `ercot_econ_curve_top_refine`). This is a position effect, not a defect in the ORDC slope. No lever follows from it alone.

**2024 C3a −11.1 % is not an ORDC problem.**
- The whole 2024 gap sits in the energy λ of the 192 hours ERCOT priced above $100.
- In the 55 hours between $200 and $1k, the model's λ averages $67 against an actual $296.
- The model's ORDC adder is within $0.14/MWh of measured RTORPA in every 2024 price band.
- This is the closed compressed-distribution object (R-ERCOT-12/20). Nothing here is new evidence on it, so it was not re-opened.

**What phase 0 did find.** In 2019 and 2021 the model's ORDC adder runs above measured RTORPA in the actual-tight hours: +5.5 $/MWh (2019) and +22.5 $/MWh (2021), on the LW basis.

## 2. Identification and the change

The published RTORPA formula was evaluated on ERCOT's measured RTOLCAP, RTOFFCAP and λ. The ratios below are against actual RTORPA.

| Year | Keeper curve (0.5σ all year) | With the PUCT 48551 shift in force |
|---|---|---|
| **2019** | 1.64× (r 0.989) | **1.04× (r 0.997)** |
| 2020 | 1.45× | 1.43× |
| 2021 | 1.59× | 1.59× |
| 2022 | 1.08× | 1.08× |
| 2023 | 1.09× | 1.09× |
| 2024 | 0.89× | 0.89× |

**What was built:**
- `ordc_lolp_shift_sigma` joins `constants.ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`, the ercot-253 published-order table and its single seam. The value is 0.25 for 2019 and 0.5 for 2020–2025.
- **Year grain** is a declared rule-14 time-aggregation reconciliation. 2019's January–February, when 0.0 was in force, carries 0.04 % of that year's RTORPA.
- **Zero DOF.** Only 2019 moves.
- **Solve-surface pin.** ERCOT's pin advanced with a cause block. The pin also absorbs 7 unscoped rows that had landed on `main` without being pinned for ERCOT.
- **Partition stamping.** `stamp_config_partition` now treats the shift as year-driven, alongside `ordc_voll` and `ordc_mcl_mw`.

**Solves.**
- G-DRIFT `bc5069cd..9c2cdf9a` came back **ALL INERT** across 21 files.
- One shard solved **2019 only**, at the pinned SHA. Its leg is `411bc6e7b38bd1021b62c25e7d29528fd81cf623`, and the shard is archived.
- 2020–2025 reuse the r-21 legs (provenance SHAs are in the `keepers/ERCOT.json` `r_ercot22_extension`).
- `config_partition_overrides` differs from r-21 only by five default-`False` keys that the HEAD 2019 leg records. Those keys are no-ops.

## 3. Per year, keeper r-21 → r-22 (P1, `calibration_verdict --years`)

| Year | Det. | C3a | LW $/MWh | C3b | C3c h > $200 (model / actual) | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | h > $1k | slack |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **2019** | NOT-YET → NOT-YET | **+19.4 → +7.5 % (PASS)** | 55.59 → **50.03** | **0.446 → 0.231** F | 121 → 100 / 106 | +8.85 F (=) | −10.48 F (=) | +3.29 (=) | 17.6 % (=) | 39 → 30 | 0 → 0 |
| 2020 | NOT-YET (=) | +5.2 % | 26.73 | 0.221 F | 38 / 56 | +10.41 F | −11.77 F | +2.88 | 23.6 % | 3 | 0 |
| 2021 | CAL (=) | +4.2 % | 172.88 | 0.063 | 664 / 258 (ledgered) | −2.07 | −1.67 | −0.01 | 22.0 % | 122 | 3,194 MWh |
| 2022 | NOT-YET (=) | −9.3 % | 68.07 | 0.175 | 96 / 196 | −9.87 F | +5.84 | −0.94 | 29.6 % | 17 | 0 |
| 2023 hold | NOT-YET (=) | −24.2 % | 49.29 | 0.380 F | 140 / 181 | +0.65 | −2.17 | −0.76 | 18.7 % | 34 | 0 |
| 2024 | NOT-YET (=) | −11.1 % F | 27.72 | 0.197 | 12 / 53 (ledgered) | −4.28 | −0.95 | −1.20 | 15.5 % | 0 | 0 |
| 2025 | CAL (=) | −9.2 % | 33.13 | 0.126 | 0 / 31 (ledgered) | (skipped) | +3.64 | (skipped) | 21.0 % | 0 | 0 |

- (=) means byte-identical to r-21, because those legs are reused.
- The demand-weighted 2019 ORDC adder fell from $16.48 to $10.92.
- 2019 now fails only on C3b and C1 (CC_REGULAR, COAL_PRB).

## 4. Prediction scorecard (PRECOMMIT §5)

| Prediction (2019) | Outcome |
|---|---|
| Adder 10.5–12.5 | HIT (10.92) |
| LW 49.5–52.0 | HIT (50.03) |
| C3a +5 to +12 % | HIT (+7.5 %) |
| C3b 0.36–0.43, still FAIL | **MISS, favourable** (0.231, still FAIL). The adder cut the shape error far more than its share of the mean, because the r-21 2019 shape error was concentrated in adder-borne tail hours. |
| C3c 105–121 h | **MISS, low** (100 h; actual 106, ratio 0.94×) |
| h > $1k 30–38 | HIT (30) |
| C1 within ±0.3 TWh | HIT (unchanged to 0.01 TWh). The in-LP curve change did not move dispatch. |
| Slack ≤ 50 MWh | HIT (0) |
| C8 ±1 pp | HIT (=) |
| Determination NOT-YET; 2020–2025 byte-identical; ISO NOT-YET | HIT |

## 5. Promotion (rule 35)

1. **Year union before the prune**, read from both sidecars: {2019 … 2025}. The incoming keeper covers all seven years.
2. **Re-keyed in this session:**
   - `keepers/ERCOT.json`: keeper, three configs and `r_ercot22_extension`
   - `calibration-complete.json`: `keeper_rekey_2026_10_01_r22`; the marker stays withdrawn
   - `forecast/program-status.json`: ERCOT gate (a) only, keeping the `marker complete=False final=False` phrase
   - `status/ERCOT.js`
   - ERCOT matrix shard: keeper stamp and gates, plus `ercot_swcap_vintage` evidence
   - `mechanism-testing-matrix.md` §5.1
3. **Checks:**
   - `audit_keepers` between promote and prune showed only the expected E13 on r-21.
   - `prune_iso_runs --iso ERCOT --force-uncite` removed r-21's sidecar, payload and bundle. `audit_keepers` then reads 0 failures and 0 warnings.
   - `check_promotion_completeness --iso ERCOT` returns OK.

## 6. Standing state and next objects

**ISO NOT-YET:**
- 2024 forward: C3a −11.1 % (the closed compressed-distribution object).
- 2023 carve-out: owner hold on k=33.
- 2022: C1 CC_REGULAR −9.87 (coal mirror, fenced).
- 2019: C3b 0.231 and C1 (CC_REGULAR +8.85, COAL_PRB −10.48).
- 2020: C3b 0.221 and C1 (CC_REGULAR +10.41, COAL_PRB −11.77).

**Next objects:**
1. **2020/2021 ORDC adder.** The published formula still reads 1.45× / 1.59× of RTORPA with the shift in force. The candidate is ERCOT's per-year NP6-576 μ/σ tables. Those tables are not on disk, and the committed `ercot_ordc_lolp_params.csv` overstates by 2–4×. This would be a data intake.
2. **2019/2020 C1 coal/CC mirror.** It is coal conduct, which is fenced (R-ERCOT-14 routing).
3. **Task 2 (attribution of the r-21 tail move).** Not run. Task 1 showed the move is the energy dual on the measured offer surface. Splitting Lost Pines from the heat-rate identity would cost 7 shards and would not change any lever.

**Routed, unchanged:**
- Wharton CC marginal-HR estimator (card only).
- Bench display rows for 7512 / 55501 / 55545.
- Other ISOs' CC heat-rate artifacts (rule 25).
- A pre-existing failure on `main`: `tests/unit/config/test_d53_sector_gate_miso_arming.py` (stale cache-key pin). Five ISOs' solve-surface pins are also stale on `main`: CAISO, MISO, NEISO, NYISO and, until this PR, ERCOT. Those belong to their own lanes.

## 7. Where the bytes are (rule 34(e))

- **On `main`, with this PR:** `results/calibration/r_ercot22_span` (slim bundle and hourly sidecars), its registry sidecar and its run payload.
- **Legs are provenance only** (rule 33(d)). 2019 is `411bc6e7…`; 2020–2025 are the r-21 legs. A leg that is not on `main` costs a re-solve of about 20–30 minutes.

**Refs for the owner to delete** (sessions cannot delete refs, rule 33(f)):
- `claude/r-ercot22-arm-2019`
- `claude/r-ercot21-arm-{2019..2025}`
- `claude/r-ercot20-arm-{2019..2025}`
- `claude/r-ercot-21-cc2022` (merged)
