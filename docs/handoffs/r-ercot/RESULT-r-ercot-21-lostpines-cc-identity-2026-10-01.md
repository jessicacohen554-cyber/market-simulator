# RESULT — R-ERCOT-21: Lost Pines 1 non-CHP + EIA-923 identity CC heat rates — PROMOTED; ISO stays NOT-YET

- **Owner decision cards, answers verbatim:**
  - *"Build A+B, one arm (Recommended)"* (build)
  - *"Promote (Recommended)"* (promotion)
- **Keeper:** `2026-10-01-r-21-lostpines-ccid` (bundle `results/calibration/r_ercot21_span`, 2019–2025). It supersedes `2026-09-30-r-20-gt-split`.
- **Records:**
  - Phase 0: `FINDING-r-ercot-21-2022-cc-and-wharton-hr-2026-10-01.md`
  - PRECOMMIT: `PRECOMMIT-r-ercot-21-lostpines-cc-identity-2026-10-01.md` (pinned SHA `bc5069cdbebb179f1331232a2121f008ca9c0088`)
  - Scorecard: `r_ercot21_scorecard.json`

## What changed (rule 14; recipe byte-equal; zero DOF)

1. **Lost Pines 1 (55154) is not a cogen.** EIA-860 gives it Sector 1 (LCRA), FERC cogeneration status N, and a 2×1 (2 × 202.5 MW CT + 204 MW CA).
   - The sheet carried a CHP tuple (`Pct_Must_Run 60`). That held 365 MW out of the LP as host steam, and the bench netted 60 % of the plant's EIA-923 output out as BTM (1.88 TWh in 2022).
   - The row now carries the modal 2×1 F-class CC_REGULAR tuple.
2. **`campd_cc_heat_rates_ERCOT.csv` is regenerated at HEAD.**
   - The committed artifact pre-dated R-CAISO-2/3.
   - The EIA-923 CC-prime-mover identity now prices 47 `steam_not_metered` rows (derive: one new refusal key) and 14 `gross_below_net` rows.
   - Jack Fusco is kept by an ERCOT solve-fleet supplement in the derive.
   - Notable moves: T H Wharton CC 11.84 → 9.27 (2022) and 10.43 → 9.55 (2024); Cedar Bayou 4 6.53 → 7.53 (2024).

## Per year, keeper r-20 → r-21 (P1, `calibration_verdict --years`)

| Year | Determination | C3a | LW $/MWh | C3b | C3c h>$200 (model/actual) | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | h > $1k |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 val | NOT-YET → NOT-YET | +25.7 → +19.4 % | 58.51 → 55.59 | 0.566 → 0.446 F | 123 → 121 / 106 | +8.03 → +8.85 F | −9.05 → −10.48 F | +3.67 → +3.29 | 16.7 → 17.6 % | 41 → 39 |
| 2020 val | NOT-YET → NOT-YET | +7.1 → +5.2 % | 27.20 → 26.73 | 0.236 → 0.221 F | 39 → 38 / 56 | +10.81 → +10.41 F | −11.04 → −11.77 F | +3.19 → +2.88 | 22.5 → 23.6 % | 3 → 3 |
| 2021 val | CAL → CAL | +5.1 → +4.2 % | 174.46 → 172.88 | 0.073 → 0.063 | 668 → 664 / 258 (ledgered) | −1.78 → −2.07 | −1.41 → −1.67 | +0.27 → −0.01 | 20.9 → 22.0 % | 123 → 122 |
| 2022 val | NOT-YET → NOT-YET | −7.7 → −9.3 % | 69.28 → 68.07 | 0.160 → 0.175 | 101 → 96 / 196 | **−8.83 → −9.87 F** | +5.99 → +5.84 | −0.67 → −0.94 | 28.3 → 29.6 % | 19 → 17 |
| 2023 hold | NOT-YET → NOT-YET | **−18.5 → −24.2 %** | 53.01 → 49.29 | **0.270 → 0.380** | 160 → 140 / 181 | +1.53 → +0.65 | −1.72 → −2.17 | −0.49 → −0.76 | 18.1 → 18.7 % | 38 → 34 |
| 2024 | **CAL → NOT-YET** | **−9.9 → −11.1 %** | 28.10 → 27.72 | 0.188 → 0.197 | 14 → 12 / 53 (ledgered) | −3.79 → −4.28 | −0.56 → −0.95 | −0.87 → −1.20 | 14.9 → 15.5 % | 0 → 0 |
| 2025 | CAL → CAL | −8.2 → −9.2 % | 33.51 → 33.13 | 0.119 → 0.126 | 0 → 0 / 31 (ledgered) | (skipped) | +3.81 → +3.64 | (skipped) | 20.0 → 21.0 % | 0 → 0 |

- The C1 band is ±8.00 TWh.
- Slack is 0 in every year except 2021 (5,325 → 3,194 MWh).
- **The 2022 C1 gap widens because the bench rose more than the model.** The bench CC_REGULAR rises by the 1.88 TWh of Lost Pines it no longer nets out. Model CC_REGULAR rises only +0.83 TWh: Lost Pines +1.72 and Wharton +1.01, while other CCs are displaced −1.9.

**Where the price fell.** Contribution to the ΔLW, binned by the r-20 hourly price:

| Year | ΔLW | From hours > $200 |
|---|---|---|
| 2019 | −2.92 | −2.38 (82 %) |
| 2023 | −3.73 | −3.10 (83 %) |
| 2024 | −0.38 | spread across the < $100 bands |

**The 365 MW lands in the scarcity tail.** In the years that carry one, the model's tail is steep in reserve margin.

## Prediction scorecard (PRECOMMIT §5)

| Prediction | Outcome |
|---|---|
| 2022 C1 CC_REGULAR −8.4 to −7.4 | **MISS**, worse (−9.87). I under-weighted the bench's +1.88 against displacement inside CC. |
| 2024 C3a −10.5 to −9.9 % (likely flip) | **MISS**, worse (−11.1 %); the flip itself was predicted |
| 2025 C3a −8.8 to −8.2 % | **MISS**, worse (−9.2 %) |
| 2023 C3a −19.2 to −18.5 % | **MISS**, much worse (−24.2 %) |
| 2019 / 2020 / 2021 C3a | **MISS**, all lower than the bands (+19.4 / +5.2 / +4.2 %) |
| LW −0.1 to −0.6 $/MWh | **MISS** in 2019 / 2021 / 2022 / 2023 (−2.92 / −1.58 / −1.21 / −3.73); HIT in 2020 / 2024 / 2025 |
| COAL_PRB −0.2 to −0.8 TWh/yr | HIT except 2019 (−1.43) |
| C3b ±0.02 | **MISS** in 2019 (−0.12, favourable) and 2023 (+0.11) |
| C8 ±1.5 pp | HIT (+0.6 to +1.3) |
| Lost Pines model +1.5 to +2.2 TWh | HIT (+1.72 / +1.58) |
| Wharton CC 2024 3.3–3.8 TWh | HIT (3.31) |
| h > $1k ±2 | HIT except 2023 (−4) |
| Slack ±200 MWh | **MISS** in 2021 (−2,131) |

**The lesson:** the PRECOMMIT priced the capacity as a mid-merit shift. In the scarcity years it moved the tail.

## Standing state and next objects

**ISO NOT-YET:**
- 2023 carve-out: owner hold, k=33, now further out.
- 2024 forward: C3a −11.1 %.
- 2022 / 2019 / 2020 validation misses, all downgrading under rule 30(c).

**Next objects:**
1. **Why 365 MW of CC moves the 2019/2023 tail by ~$2.4–3.1/MWh.** The scarcity-tail supply representation in tight hours: reserve-supply cap, ORDC adder, the online-capacity envelope. This must be zero-LP on the committed hourlies, which now carry both sides (r-20 in git history at `dfbbf599`, r-21 on main).
2. **The 2022 CC under-run.** It is unchanged in kind: coal offer conduct (Martin Lake overnight cycling), which is fenced. The owner data decision on 2019–22 SCED stays CLOSED.
3. **Wharton CC over-run** (3.31 vs 0.56 TWh in 2024). The class marginal-HR curve sits on a 1974 CC, and no measured per-plant substitute exists (`steam_not_metered`).
4. **The attribution between the two corrections is not split.** That would cost 7 more shards.
5. **Routed:**
   - The bench per-plant display omits 7512 / 55501 / 55545.
   - The other ISOs' CC artifacts are stale against the deriver (only CAISO carries the identity column). Each ISO's lane regenerates its own (rule 25). CAISO's 24 `steam_not_metered` rows will move at its next regeneration.

## Promotion (rule 35)

1. **Year union before the prune** (both sidecars): {2019 … 2025}. The incoming keeper covers all seven.
2. **Re-keyed:**
   - `keepers/ERCOT.json` (three configs + `r_ercot21_extension`)
   - `calibration-complete.json` (`keeper_rekey_2026_10_01_r21`; marker stays withdrawn)
   - `forecast/program-status.json`, ERCOT gate (a) only
   - `status/ERCOT.js`
   - ERCOT matrix shard (keeper/gates + `measured_cc_heat_rates` evidence)
   - `mechanism-testing-matrix.md` §5.1
3. **Checks:**
   - `audit_keepers` between promotion and prune: only the expected E13, on r-20.
   - `prune_iso_runs --iso ERCOT --force-uncite` removed r-20 (sidecar, payload, bundle). Afterwards `audit_keepers` reads 0/0.
   - `check_promotion_completeness --iso ERCOT` OK.

## Where the bytes are (rule 34(e))

- **On `main` with the promotion:** `results/calibration/r_ercot21_span` (slim bundle with hourly sidecars), its registry sidecar and its run payload.
- **Legs:** provenance only (rule 33(d)). All seven shards are archived. A leg not on `main` costs a re-solve (~20–30 min each).

| Year | Commit |
|---|---|
| 2019 | `2f6dfbe92c9948014d768eba9ddd99da8bf684a5` |
| 2020 | `b46b4648192a3439cd8fd697630185e15f008a60` |
| 2021 | `f814688bd7f5047ac507a2ee0a5ba7c971f64f20` |
| 2022 | `99f30001c1eb636fca962ba8121dd3899e4fc8f6` |
| 2023 | `800185e92def528ae03875f8cd9fcc220a9d1394` |
| 2024 | `ed48f1a828ebef701dfc2ccd4bfc196363ad6875` |
| 2025 | `53f820576ad13d7d7ee83467e5a96768c3020d1d` |

**Refs for the owner to delete** (sessions cannot delete refs, rule 33(f)):
- `claude/r-ercot21-arm-{2019..2025}`
- `claude/r-ercot20-arm-{2019..2025}`
- `claude/r-ercot-20-c3a-decomp` (merged)
- The `claude/r-ercot19*` refs listed in the R-ERCOT-21 handoff are already gone.
