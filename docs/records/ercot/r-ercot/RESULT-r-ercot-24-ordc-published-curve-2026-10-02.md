# RESULT — R-ERCOT-24/24b: ERCOT's published ORDC curve — PROMOTED; ISO stays NOT-YET

- **Promotion basis:** owner decision card 2026-10-02, answer *"Promote (Recommended)"*. The PRECOMMIT §6 rule tripped (2022's adder moved away from measured), so it went to the owner.
- **Keeper:** `2026-10-02-r-24-ordc-published`, bundle `results/calibration/r_ercot24_span`, 2019–2025. Supersedes `2026-10-01-r-23-swcap-hourly`, which is pruned.
- **Records:** PRECOMMIT `PRECOMMIT-r-ercot-24-ordc-published-curve-2026-10-01.md` (pinned SHA `02f67d135c729345371d156cadec29bb697432d6`); phase 0 `r_ercot24_phase0.json`; scorecard `r_ercot24_scorecard.json` (`scripts/probes/_r_ercot24_scorecard.py`).
- **Sessions:** R-ERCOT-24 built the change and wrote the PRECOMMIT. R-ERCOT-24b (new chain root) solved, scored and promoted.

## 1. What changed

`ercot_ordc_published_curve` (default off; ERCOT-gated; backcast-only; zero DOF), armed on all seven legs (owner card *"All years incl. 2023 (Recommended)"*; the 2023 k=33 carve-out is untouched):
- the ORDC OBD §2.3 half-hour curve, `SLOLP = 1 − CDF(0.5·μs, 0.707·σ)`;
- ERCOT's published seasonal μ/σ (NP6-576-ER, read from Fig. 3 of the 2022/2024 Biennial ORDC Reports; declared ±15 MW reconciliation) in place of the flat μ = 0 / σ = 1,400.

Offer curves unchanged. `stamp_config_partition --check` passes; the overlays equal the keeper's except two default-off fields the r-23 legs recorded explicitly (`coal_captive_marginal_fuel_price`, `dual_fuel_measured_oil_burn`, both `false`), which every r-24 leg also carries `false`.

## 2. Per year, r-23 → r-24 (P1, `calibration_verdict --years`)

| Year | Det. | C3a | C3b | C3c h > $200 (model/actual) | ORDC adder LW (measured RTORPA) | LW $/MWh | h > $1k | C1 CC_REG | C1 COAL_PRB | C1 ST_GAS | C8 ST_GAS | slack MWh |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | NOT-YET (=) | +7.0 → +6.6 % | 0.219 → **0.228** F | 100 → 92 / 106 PASS | 10.92 → 10.81 (9.63) | 49.81 → 49.64 | 30 → 31 | +8.85 F (=) | −10.48 F (=) | +3.29 | 17.6 % | 0 |
| 2020 | NOT-YET (=) | +5.2 → **+2.5 %** | 0.221 → **0.209** F | 38 → 22 / 56, PASS → ledgered caveat | 3.17 → **2.50** (2.64) | 26.73 → 26.05 | 3 → 3 | +10.41 → +10.21 F | −11.77 → −11.83 F | +2.86 | 23.6 % | 0 |
| 2021 | CAL (=) | +1.0 → +0.7 % | 0.062 → 0.066 | 653 / 258 (ledgered) | 26.73 → 26.22 (7.32) | 167.58 → 167.09 | 113 → 112 | −1.88 | −1.66 | −0.00 | 22.0 % | 3,194 (=) |
| 2022 | NOT-YET (=) | −9.3 → −9.9 % | 0.175 → 0.181 | 96 → 94 / 196 | 6.46 → 6.11 (6.87) **away** | 68.07 → 67.65 | 17 → 17 | −9.87 → −10.07 F | +5.79 | −0.95 | 29.7 % | 0 |
| 2023 hold | NOT-YET (=) | −24.2 → −24.5 % F | 0.380 → 0.385 F | 140 → 138 / 181 | 2.64 → 2.44 (1.27) | 49.28 → 49.12 | 34 → 32 | +0.66 | −2.17 | −0.76 | 18.7 % | 0 |
| 2024 | NOT-YET (=) | −11.1 → −11.4 % F | 0.197 → 0.198 | 12 → 11 / 53 | 0.34 → 0.32 (0.24) | 27.72 → 27.63 | 0 | −4.63 | −1.04 | −1.23 | 15.6 % | 0 |
| 2025 | CAL (=) | −9.2 → −9.4 % | 0.126 | 0 / 31 | 0.00 → 0.00 (0.08) | 33.13 → 33.08 | 0 | skip | +3.63 | skip | 21.1 % | 0 |

- **ISO: NOT-YET (=).** No determination moves.
- **Legitimacy diagnostics:** D-4 FAIL rows 119 → 118 over the span, same families as the keeper (CT_PEAKER reliability floor h14–21, `st_netload_drag` 3452/3628/3491, CC `gas_commitment_bridge`); no new family.

## 3. Prediction scorecard (PRECOMMIT §5)

| Prediction | Outcome |
|---|---|
| 2019 adder 10.0–10.7; LW 49.0–49.6; C3a +5.3 to +6.6 %; h > $1k 27–30; h > $200 88–98 | **MISS** adder 10.81, **MISS** LW 49.64; HIT C3a +6.6 % (edge); **MISS** h > $1k 31; HIT 92 |
| 2020 adder 1.9–2.6; LW 25.5–26.2; C3a +0.4 to +3.1 %; h > $1k 1–3; h > $200 22–32 | HIT on all five (2.50; 26.05; +2.5 %; 3; 22) |
| 2021 adder 26.0–26.5; LW 166.6–167.4; C3a +0.4 to +0.9 %; h > $1k 110–113; h > $200 645–653 | HIT on all five (26.22; 167.09; +0.7 %; 112; 653) |
| 2022 adder 6.0–6.4; LW 67.5–67.95; C3a −9.5 to −10.1 %; h > $1k 13–17; h > $200 90–96 | HIT on all five (6.11; 67.65; −9.9 %; 17; 94) |
| 2023 adder 2.3–2.6; LW 49.0–49.25; C3a −24.3 to −24.6 %; h > $1k 30–34; h > $200 136–140 | HIT on all five (2.44; 49.12; −24.5 %; 32; 138) |
| 2024 adder 0.30–0.34; LW 27.65–27.72; C3a −11.1 to −11.3 %; h > $200 10–12 | HIT adder 0.32; **MISS** LW 27.63; **MISS** C3a −11.4 %; HIT 11 |
| 2025 adder 0.00; LW 33.13 ± 0.05; C3a −9.2 ± 0.15 % | HIT 0.00; HIT 33.08 (edge); **MISS** C3a −9.4 % |
| C1 each class ≤ ±0.3 TWh; C8 ST_GAS ≤ ±1 pp | **MISS** 2024 CC_REGULAR −0.35 TWh; every other class HIT; C8 HIT (≤ 0.1 pp) |
| C3b: 2019/2020 fall ≤ 0.02, others ±0.01 | 2020 HIT (−0.012); **MISS 2019 sign** (+0.009); others HIT |
| Slack 2021 3,194 ± 50, else 0 | HIT |
| Determinations unchanged; ISO NOT-YET | HIT |

**Reading.** 2020–2023 landed inside every band. The misses are small and one-sided: re-dispatch moved 2024/2025 prices slightly lower than the zero-LP re-pricing allowed, and 2019's adder dropped about a third as much as predicted (10.81 vs 10.0–10.7). The 2019 C3b sign miss is +0.009.

## 4. Promotion

- **PRECOMMIT §6:** the adder moved toward measured RTORPA in 2019, 2020, 2023 and 2024 but away in 2022 (6.46 → 6.11 vs 6.87). That 2022 drop was itself in the §5 prediction (6.0–6.4), and its sign is the expected Jensen sign (LESSONS). The rule says stop and ask, so the owner got a card.
- **Owner card (2026-10-02):** *"Promote (Recommended)"*.
- **Mechanics (rule 35):**
  - `dashboard_add_run.py --no-prune`, then `promote_keeper.py`; its audit stopped on the expected E13 for r-23.
  - `prune_iso_runs --iso ERCOT --force-uncite` removed r-23's three stores.
  - The `config_partition.configs` were re-pointed to the new keeper and `r_ercot24_extension` was added.
  - `audit_keepers --iso ERCOT --check`: 0 failures, 0 warnings.
  - `check_registry_payload_parity`: OK.
  - `check_mechanism_matrix --base origin/main`: OK.
  - `check_promotion_completeness` no longer exists (removed with cleanup-A, `3fa42239`); the audit and parity gates above are its successors.
- **Re-keyed:** `keepers/ERCOT.json`; `forecast/program-status.json` ERCOT gate (a) only, keeping `marker complete=False final=False`; `status/ERCOT.js`; the ERCOT matrix shard (keeper, gates, cell `ercot_ordc_published_curve` = **K**); `mechanism-testing-matrix.md` §5.1; the calibration log. ERCOT holds no `complete` entry, so `calibration-complete.json` is untouched.
- **Rule 15:** the bundle commits `hourly/unit_marginal_<year>.parquet` for all seven years (22–32 MB each).

## 5. Where the bytes are (rule 34(e))

- **On `main` with this PR:** the slim bundle `results/calibration/r_ercot24_span` (JSON, hourly sidecars, unit_marginal), the registry sidecar and the run payload.
- **Legs are provenance only** (rule 33(d)): 2019 `a22bd87c011d327781f4dea103703bcd1ad980bf`, 2020 `a467a690456255247e1b7fcf09f14a68d5e147ce`, 2021 `5806b79df855d6d4c346f9abc955f9b36b770ae5`, 2022 `03322df5fba8d5f7d2ce138d9427b2a584822677`, 2023 `457ce3620c84aec105295bd140c9652194f63d55`, 2024 `b679aeb986aac98e6463037ab196188e608d8658`, 2025 `6abb7bef0192c9e061c5ffef656fb7d2a9f52f0f`. All seven shards are archived. Recovering a leg means re-solving it, about 15–20 minutes per year.

**Refs for the owner to delete** (sessions cannot delete refs):
- `claude/r-ercot23-arm-2019`, `claude/r-ercot23-arm-2021`, `claude/r-ercot22-arm-2019`
- `claude/r-ercot-23-ordc-2021` (merged), `claude/r-ercot-24-ordc-vintage` (merged)
- `claude/r-ercot-24-2019` … `claude/r-ercot-24-2025` (seven shard branches)
- `claude/r-ercot-24b-handoff-zi0io4` once this PR merges

## 6. Open gates and routing (unchanged by this lane)

- **2024 C3a −11.4 %:** R-ERCOT-20 FINDING closed it as the compressed-distribution / tight-hour object. Reopen only with new evidence.
- **2022 C1 CC_REGULAR −10.07 TWh:** R-ERCOT-21 FINDING. The Wharton marginal-HR estimator is card-only.
- **2019/2020 C1 coal/CC mirror:** fenced coal conduct. Raise only with new admissible evidence.
- **2023 carve-out k=33:** owner hold.
- **2020 C3c:** moved PASS → ledgered caveat (38 → 22 h vs 56 actual). This is non-downgrading (rule 22); note it for the next lane.
- **Pre-existing `main` failures (not this lane's):** see the handoff list. They are unchanged here; this PR touches no `src/`.
