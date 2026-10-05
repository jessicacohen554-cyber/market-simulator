# RESULT: ERCOT coal warm-boiler committed band (`coal_warm_committed`) on the cliff-split recipe

Lane `closeout-ERCOT-w4`, 2026-10-05. Scores the probe precommitted in `PRECOMMIT-closeout-ercot-w4-coal-warm-committed-2026-10-05.md` (pushed at `62fcbbf4` before launch).

**All six kills pass.** Against the w3 control, three C1 records flip FAIL → PASS and nothing regresses:

- 2019 CC_REGULAR: +8.45 → +7.28
- 2019 COAL_PRB: −9.57 → −7.91
- 2020 CC_REGULAR: +9.60 → +7.93

The declared 2025 C3a risk did not materialize. The ISO determination stays NOT-YET on records this arm does not own: 2019/20 C3b, 2020 COAL_PRB, and 2024 C3a/C3b.

**Recommendation: promote cliff split + warm committed as one recipe** (rule 1, PRECOMMIT §5). It supersedes the w3 recommendation.

## 1. Provenance

| Year | Leg | Commit (full SHA) | Parent |
|---|---|---|---|
| 2019 | `claude/closeout-ercot-w4-2019` | `0258cdc434f2245e00b57ee06ac48ccfb352e85e` | `1283e27f…` |
| 2020 | `claude/closeout-ercot-w4-2020` | `07989f762c524b35db1fc742b60b2cd3fdf9637f` | `1283e27f…` |
| 2021 | `claude/closeout-ercot-w4-2021` | `51103a8c78bcba09c191133dd12bcb23b92dbd1e` | `1283e27f…` |
| 2022 | `claude/closeout-ercot-w4-2022` | `c3d5dee6afe652c71aa925c65735e4aeb35e278e` | `1283e27f…` |
| 2023 | keeper leg `closeout_ercot_l1b_2023` | `2e5d93a24222e75b04b802ddff85b945de1699ca` | (not solved; byte-identical to the keeper) |
| 2024 | `claude/closeout-ercot-w4-2024` | `d6090d4c0d456988253fc4ef32428c451f332f4b` | `1283e27f…` |
| 2025 | `claude/closeout-ercot-w4-2025` | `7dcf235b7810959520b2ba395ad6c50029c063fd` | `1283e27f…` |

- **Legs:** each pushed its full 19-file bundle, including `dispatch/<Y>_P1.parquet`. The parent checked each with `git ls-tree`, pulled the bytes and checked K1 before archiving; all six shards are archived.
- **Solve revision:** `1283e27fe4427157af54157cc67478d7b8601281`, the same as the w3 control legs. No code was added.
- **Compose:** `scripts/probes/_closeout_ercot_w4_compose_span.py` → `results/calibration/closeout_ercot_w4_span`. It works at zero LP, rebuilds the diagnostics over all seven years and re-stamps the partition.
- **Registration:** in session as probe `2026-10-02-closeout-w4-coal-warm`, kept off `main` (E13).
- **Scorecard:** `data/w4_scorecard.json` (w3 vs w4, span-restricted `calibration_verdict` per year).

## 2. Kills (pre-registered; all PASS)

| Kill | Reading | Verdict |
|---|---|---|
| K1 recipe | Every leg equals the keeper's `run_config_<Y>` plus `coal_perplant_cliff_split` and `coal_warm_committed`, nothing else. Checked at fetch and at compose. | PASS |
| K2 shed | Slack is identical to w3: 2021 = 3,012.6 MWh, every other year 0. | PASS |
| K3 inert | Martin Lake's `_committed` P1 median is $21.53, equal to its base cost, in every leg. Coal moves +1.60 (2019) / +2.41 (2020) TWh. | PASS |
| K4 C1 / governance | No C1 PASS → FAIL against w3 or the keeper. C6 governance and C8 forced share PASS. | PASS |
| K5 target | The 2019 + 2020 COAL_PRB miss shrinks by 4.20 TWh against w3 (−9.57 → −7.91, −10.85 → −8.31); the bar was ≥ 1.5. | PASS |
| K6 D-4 | No new D-4 family; 114 failures, the same set as w3. D-1, D-2 and D-5 pass. | PASS |

## 3. Pre-fixed readings vs outcome (w3 → w4)

| Record | w3 | Predicted | w4 | Call |
|---|---|---|---|---|
| Coal energy 2019 / 2020 | — | +1.6 … +2.3 / +2.2 … +3.3 | +1.60 / +2.41 | hit (2019 at the low edge) |
| C1 2019 COAL_PRB | −9.57 F | −7.3 … −8.0 (flip expected) | **−7.91 P** | hit; **FAIL → PASS** |
| C1 2020 COAL_PRB | −10.85 F | −7.8 … −8.9 (centre −8.3) | −8.31 F | hit (centre) |
| C1 2019 CC_REGULAR | +8.45 F | +6.4 … +7.5 (flip expected) | **+7.28 P** | hit; **FAIL → PASS** |
| C1 2020 CC_REGULAR | +9.60 F | +6.6 … +8.3 (flip expected) | **+7.93 P** | hit; **FAIL → PASS** |
| Martin Lake TWh 2019 / 2020 / 2024 | — | each ≥ +0.6 | +0.81 / +0.83 / +0.97 | hit |
| C1 COAL_PRB 2021 / 2022 / 2024 / 2025 | −0.59 / −0.54 / +0.10 / +2.33 | each moves ≤ +1.6 | −0.15 / −0.62 / **+1.83** / +2.32 | **2024 missed** (+1.73 vs ≤ +1.6); all stay PASS |
| C1 CC_REGULAR 2022 / 2024 | −4.45 / −4.93 | no worse than −5.5 / −6.8 | −4.32 / −5.87 | hit |
| C3a 2019 / 2020 | +5.9 / +1.9 % | lower by 0.3–1.0 pt | +5.4 / +0.6 % | 2019 hit; **2020 missed** (−1.3 pt); both PASS |
| C3a 2021 / 2022 | +0.7 / −8.4 % | ≤ −0.3 / −8.5 … −8.9 | +0.6 / −8.5 % | hit |
| C3a 2024 | −11.9 % F | −12.2 … −12.9 % | −12.7 % F | hit |
| C3a 2025 | −9.9 % P | −10.0 … −10.3 % (flip risk) | −9.9 % P | **missed in the arm's favour**: 2025 is near-inert (coal −0.01 TWh); no flip |
| C3b 2024 | 0.201 F | 0.201 … 0.206 | 0.206 F | hit (edge) |
| C3b 2019 / 2020 | 0.217 / 0.209 F | ±0.01 | 0.217 / 0.208 F | hit |
| C3b 2021 / 2022 / 2025 | PASS | stay PASS | 0.066 / 0.177 / 0.129 | hit |

- **Coal by plant (w3 → w4, TWh):** Martin Lake +0.81 / +0.83 / +0.31 / +0.97 (2019/20/21/24); Parish +0.63 / +0.80 / 0 / +0.27; Sandy Creek +0.12 to +0.21 in 2019/20/21/24; 2025 moves no plant by ≥ 0.05.
- **CC_REGULAR plants:** −1.17 / −1.67 / −0.34 / −0.95 (2019/20/21/24), so coal displaces CC for 55–79 % of its added MWh. ST_GAS C1 falls by 0.23 / 0.44 TWh in 2019/20; the rest of the offset is not decomposed here.
- **Load-weighted price falls:** −$0.22 (2019), −$0.34 (2020), −$0.07 (2021), −$0.02 (2022), −$0.25 (2024), −$0.01 (2025) per MWh.

## 4. Against the keeper

Combining w3 and w4, the keeper → arm changes are:

- **Three C1 PASSes gained:** 2019 CC_REGULAR, 2019 COAL_PRB, 2020 CC_REGULAR.
- **One price-shape record lost:** 2024 C3b PASS → FAIL, 0.198 → 0.206. That is w3's declared flip, deepened by 0.005 here.
- **Its cause** is unchanged (w3 RESULT §4): cheaper coal lands in May and August 2024, months the keeper already under-prices (C3a −11.3 % → −12.7 %).
- **Determination:** NOT-YET in all three runs.

## 5. Recommendation and promotion cost

- **Recommendation: promote `closeout_ercot_w4_span`** (cliff split + warm committed; rule 1, PRECOMMIT §5).
- **Why it is more faithful:**
  - It removes a cold-start charge from warm boilers. The flag gates on each unit's own `must_run_pct` (rule 18).
  - That restores the measured monotone curve order on every coal plant.
  - It closes three of the seven failing C1 records.
- **Costs:** zero parameters and no floor. Its only cost is 2024 C3b, already flipped by w3, moving a further 0.005.
- **Promotion command:** `scripts/promote_keeper.py` on the composed span. Six years of `hourly/` sidecars swap, 2023 is unchanged, the exceptions ledger carries forward unchanged and the DOF ledger is unchanged.
- **Where the bytes are:** the leg branches at the SHAs in §1. The composite rebuilds at zero LP and will not survive this container.

## 6. Owner question

Promote `closeout_ercot_w4_span` as the ERCOT keeper: three C1 FAIL → PASS, accepting the 2024 C3b PASS → FAIL (0.198 → 0.206)? Or hold it at `O`?
