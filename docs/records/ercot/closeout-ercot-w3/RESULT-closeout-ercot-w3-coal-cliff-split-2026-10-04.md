# RESULT: ERCOT coal per-plant econ cliff split (`coal_perplant_cliff_split`)

Lane `closeout-ERCOT-w3`, 2026-10-04. Scores the probe precommitted in `PRECOMMIT-closeout-ercot-w3-coal-cliff-split-2026-10-04.md`.

**All six kills pass.** One criterion-year changes status: 2024 C3b goes PASS → FAIL (0.198 → 0.201). That was one of the two price risks the PRECOMMIT declared. The ISO determination reads NOT-YET for both the keeper and the arm. Under the decision rule (PRECOMMIT §5, rule 1), the arm is **recommended for promotion**, and the owner's ruling is requested. The matrix cell is now `O`.

## 1. Provenance

| Year | Leg | Commit (full SHA) | Parent |
|---|---|---|---|
| 2019 | `claude/closeout-ercot-w3-2019` | `1f1749cd4d4e87727967f05fc5ad4b004a7ca49d` | `1283e27f…` |
| 2020 | `claude/closeout-ercot-w3-2020` | `5dfe9993eb84460c3e0aa06009178b2d2e445472` | `1283e27f…` |
| 2021 | `claude/closeout-ercot-w3-2021` | `86f959b5cf4d9d2e98671d4a25d2a966c0ffd6e8` | `1283e27f…` |
| 2022 | `claude/closeout-ercot-w3-2022` | `619b33d73554ddc552ec6b9f0a369838ada1352a` | `1283e27f…` |
| 2023 | keeper leg `closeout_ercot_l1b_2023` | `2e5d93a24222e75b04b802ddff85b945de1699ca` | (not solved; byte-identical to the keeper) |
| 2024 | `claude/closeout-ercot-w3-2024` | `0c68a782b483e249c3318d4341194dcf0a01495b` | `1283e27f…` |
| 2025 | `claude/closeout-ercot-w3-2025` | `3cfdad4f20228cc88f9c6ef98b0e02bd15507aac` | `1283e27f…` |

- **Leg contents.** Each leg pushed its full bundle: 19 files, including `dispatch/<Y>_P1.parquet` and `floors/<Y>_P1.npz`.
- **Verification before archiving.** The parent checked `git ls-tree` on every leg and pulled the bytes before archiving its shard (rules 33/34). All six shards are archived.
- **Solve revision.** The shards ran at `1283e27fe4427157af54157cc67478d7b8601281`. That is the solve base `35ef9a1e` (keeper pin `106d6bb7` + the lane's default-off code) plus one data-only commit carrying the keeper bundle `closeout_ercot_l1_span` as the replay recipe (68 files, no code). G-DRIFT against the keeper legs is therefore the PRECOMMIT §2 diff alone.
- **Compose.** `scripts/probes/_closeout_ercot_w3_compose_span.py` builds `results/calibration/closeout_ercot_w3_span` at zero LP. It starts from the keeper `closeout_ercot_l1_span` and swaps in the six armed years. 2023 is checked sha-identical to the keeper. The config partition is re-stamped, and `legitimacy_diagnostics.json` is regenerated over all seven years.
- **Registration.** The span was registered in session as probe `2026-10-02-closeout-w3-coal-cliff`. The registration is kept off `main`: `audit_keepers` E13 refuses a non-keeper run that is stamped to no keeper (the ECRS-strip precedent). The composite rebuilds at zero LP from the legs above.
- **Scorecard.** `data/w3_scorecard.json`, produced by `scripts/probes/_r_ercot24_scorecard.py` (span-restricted `calibration_verdict` per year, keeper vs arm).

## 2. Kills (pre-registered; all PASS)

| Kill | Reading | Verdict |
|---|---|---|
| K1 recipe | In every leg, `scenario_config` equals the keeper's `run_config_<Y>.json` except `coal_perplant_cliff_split: true`. Checked by hand and again at compose time. | PASS |
| K2 shed | Slack is unchanged in every year: 2021 = 3,012.6 MWh, every other year 0. | PASS |
| K3 inert | Fayette's `_econlo` row is present in all six legs. Fayette TWh: +1.38 / +1.24 / +1.37 / +0.79 / +1.22 / +1.47 (2019/20/21/22/24/25). Every year is ≥ 0.5. | PASS |
| K4 C1 / governance | No C1 PASS → FAIL in any class-year. C6 governance and C8 forced share PASS. | PASS |
| K5 target | The 2019 + 2020 COAL_PRB miss shrinks by 2.22 TWh (−10.79 → −9.57, −11.85 → −10.85); the bar was ≥ 1.0. | PASS |
| K6 D-4 | No new D-4 family. Failures go from 115 to 114, all standing keeper families. D-1, D-2 and D-5 still pass. | PASS |

## 3. Pre-fixed readings vs outcome

| Record | Keeper | Predicted | Arm | Call |
|---|---|---|---|---|
| C1 2019 CC_REGULAR | +9.21 F | +7.4 … +8.4 (flip to PASS at the centre) | **+8.45 F** | **missed**: 0.05 outside the range, no flip |
| C1 2019 COAL_PRB | −10.79 F | −8.9 … −9.8 F | −9.57 F | hit |
| C1 2020 CC_REGULAR | +10.17 F | +8.5 … +9.4 F | +9.60 F | missed high by 0.2 |
| C1 2020 COAL_PRB | −11.85 F | −10.0 … −10.9 F | −10.85 F | hit (edge) |
| Fayette gap closure | — | ≥ 0.8 TWh every year | 0.79 to 1.47 | **missed in 2022** (0.79) |
| C3a 2024 | −11.3 % F | −11.4 … −12.3 % F | −11.9 % F | hit |
| C3a 2025 | −9.2 % P | −9.3 … −10.1 % (flip risk) | −9.9 % P | hit; no flip |
| C3a 2019 / 2020 | +6.2 / +2.5 % | lower by 0.5–1.7 pt | +5.9 / +1.9 % | 2019 lower by 0.3 pt (just under the range); 2020 hit |
| C3b 2019 / 2020 | 0.216 / 0.208 F | ±0.01 | 0.217 / 0.209 F | hit |
| C3b 2024 | 0.198 P | 0.195 … 0.205 (flip risk) | **0.201 F** | inside the range; **the declared flip occurred** |
| C3a/C3b 2021, 2022 | PASS | stay PASS; 2022 C3a no worse than −9.3 % | +0.7 % / 0.066; −8.4 % / 0.178 | hit |
| C1 other class-years | PASS | stay PASS; COAL_PRB 2021/22/24/25 up ≤ +2.5 TWh | +1.42 / +0.84 / +1.07 / +1.46 | hit |

Coal energy moves by +1.20 / +0.96 / +1.41 / +0.83 / +1.06 / +1.45 TWh. Almost all of it is Fayette. Limestone gives back 0.2 TWh in 2019 and 2024, and Sandy Creek gains up to 0.14 TWh. Load-weighted price falls by $0.02 to $0.23/MWh.

## 4. The one status flip (2024 C3b)

- **The flip.** 2024 shape NRMSE moves from 0.198 to 0.201 against a 0.20 tolerance. 2024 C3a was already a FAIL (−11.3 → −11.9 %).
- **Effect on the determination.** None: the forward scope was already NOT-YET on 2024 C3a.
- **Likely cause (read from the direction of the move, not decomposed hour by hour).** Cheaper coal econ capacity (Fayette's $17 side) now clears in shoulder hours. Those hours were already under-priced, so the low end of the 2024 price shape sags further. This is the same under-pricing the keeper carries in 2024 C3a. The split does not create it; the split exposes it. The open structural owner remains the 2024 price-level shortfall (closeout plan §3.ERCOT).
- **Rule 1 and the offer bands.** Rule 1 keeps the structurally real mechanism. No offer band was touched to recover the shape.

## 5. Recommendation and promotion cost

- **Recommendation: promote** (rule 1, PRECOMMIT §5). The arm prices each coal econ tranche on its own side of the measured curve step, where the keeper averages across the step. That is strictly more faithful to the admitted ERCOT-144 conduct. It adds zero parameters and no floor.
- **Fit.** It closes 2.2 TWh of the 2019/20 COAL_PRB miss and ~1.2 TWh/yr of the Fayette gap. Its one cost is a 0.003 NRMSE move across the 2024 C3b line.
- **Promotion command.** `scripts/promote_keeper.py` on the composed span. The keeper store (~199 MB of committed sidecars) swaps six years of `hourly/` files for the arm's. 2023 is unchanged. The attestation carries forward the keeper's exceptions ledger, including the R-6 2023 configuration exceptions, unchanged.
- **Ledgers.** The DOF ledger is unchanged. No caveat is added: 2024 C3b becomes an undocumented FAIL in a scope that is already NOT-YET.
- **Where the bytes are.** Each bundle is on its leg branch at the SHAs in §1. Nothing is on `main` until promotion. The local composite will not survive this container.

## 6. Owner question

Promote `closeout_ercot_w3_span` as the ERCOT keeper, accepting the 2024 C3b PASS → FAIL (0.198 → 0.201)? Or hold it at `O`?
