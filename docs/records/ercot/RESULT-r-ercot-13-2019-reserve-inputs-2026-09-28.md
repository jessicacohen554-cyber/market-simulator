# RESULT — R-ERCOT-13: 2019 onto the measured reserve inputs, PROMOTED; ISO still NOT-YET

**Session:** R-ERCOT-13, 2026-09-28.
**PRECOMMIT:** `docs/records/ercot/PRECOMMIT-r-ercot-13-2019-reserve-inputs-2026-09-28.md`, pinned SHA `dac2fa2c234c590920cbc944dd64c82aeaa95b72`.
**Keeper:** `2026-09-28-r-13-2019-reserve` (bundle `results/calibration/r_ercot13_span`, 2019–2025). It supersedes `2026-09-28-r-12-frontera-membership`.
**Promotion basis:** the owner's standing instruction carried in the handoff, verbatim *"Is it an improvement? Then promote"*, with the fixed PRECOMMIT §5 rule met. No decision card was needed: every scored 2019 price criterion improves, and every other year is identical.

## Headline

- **Root cause of the 2019 shed hours.** The keeper made generators carry reserve that Load Resources actually supplied in 2019, and it let cleared reserve exceed ERCOT's measured online capability.
- **Why 2019 was missed.** Both measured inputs already applied from 2020 on. 2019 was left out only because its series was "deliberately unbuilt (locked-test tier)", and that regime was removed 2026-09-09.
- **2019 improves:**
  - C3a +53.6 → **+41.4 %**;
  - C3b 1.228 → **0.874**;
  - shed 4,662 → **17 MWh**.
- **What gets worse:** the deep tail. Hours ≥ $1k rose 48 → 54 (actual 26).
- **2020–2025 are identical.** ERCOT stays NOT-YET on the train years: 2023 is under the owner hold, and 2024 fails at C3a −10.7 %.

## Per year (keeper → new keeper, P1; same scorer)

| year | C3a | C3b | C3c | C1 CC_REG | C1 COAL_PRB | LW $/MWh | shed MWh | h ≥ $1k | h > $200 (RT actual) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| **2019** | +53.6 → **+41.4 %** F | 1.228 → **0.874** F | PASS (112 → 142 h vs 106) | +9.63 F | −8.15 F | 71.50 → **65.81** | 4,662 → **17** | 48 → 54 (26) | 112 → 142 | NOT-YET |
| 2020 | +11.3 % F | 0.343 F | PASS | +9.56 F | −12.73 F | 28.27 | 0 | 5 | — | NOT-YET |
| 2021 | −0.9 % | P | CAVEAT 667/258 | P | P | — | — | — | — | CALIBRATED |
| 2022 | +1.8 % (C5a) | P | CAVEAT 97/196 | P | P | — | — | — | — | CALIBRATED |
| 2023 | −20.0 % F | 0.293 F | PASS | P | P | 52.02 | 0 | 38 | — | NOT-YET (owner hold) |
| 2024 | −10.7 % F | 0.189 | CAVEAT 13/53 | P | P | 27.83 | 0 | 1 | — | NOT-YET |
| 2025 | −9.6 % | 0.127 | CAVEAT 0/31 | skipped | +3.72 | 32.98 | 0 | 0 | — | CALIBRATED |

Rows 2020–2025 are byte-identical to the prior keeper, since the same legs were recomposed. `calibration_verdict --years` agrees for every year on both run ids.

## Attribution (diagnostic shard B, LR credit only — never promotable)

| 2019 | keeper | A: LR + cap (keeper) | B: LR only |
|---|---|---|---|
| LW $/MWh | 71.50 | 65.81 | 63.69 |
| shed MWh | 4,662 | 17 | 2,023 |
| h ≥ $1k | 48 | 54 | 46 |
| ORDC-short hours | 394 | 1,329 | 350 |

- **The LR credit** removes about half the shed and lowers the mean.
- **The RTOLCAP cap** removes the remaining shed. It also moves ~935 hours into ORDC shortfall, which is where the extra mid-band scarcity hours come from. The same signature appeared in 2022 at run252.
- **Neither shard selected A.** A was fixed in the PRECOMMIT.

## Prediction scorecard (PRECOMMIT §4)

| | predicted | measured | |
|---|---|---|---|
| P1 | shed ≤ 1,500 MWh | 17 | met |
| P2 | h ≥ $1k 20–40 | **54** | **MISSED** — the cap's ORDC shortfall hours outweigh the freed supply at the top of the tail |
| P3 | C3a +25 to +45 % | +41.4 % | met, and the caveated direction risk did not bite on the mean |
| P4 | C3b 0.5–0.9 | 0.874 | met |
| P5 | C1 moves < 1.5 TWh | 0.00 TWh on every class | met. **So lever item 2 (C1 coal/CC) is a separate object** |
| P6 | 2020–2025 unchanged | identical | met |

## Phase-0 findings routed to the next session (zero LP, evidence in PRECOMMIT §1)

1. **R1 — shed-vs-rigid-reserve penalty inversion, 2019–2021.**
   - `iso_config.voll` = $5,000 in every year, but the rigid RRS/Reg-Up step uses `ordc_voll` = $9,000 before 2022.
   - So the LP sheds firm load before it deploys RRS. ERCOT's EEA sequence is the reverse: RRS in EEA2, shed in EEA3.
   - The keeper held exactly 3,395 MW of reserve while shedding.
   - This is a structural fix, and it also touches 2021.
2. **R2 — the scored price can exceed HCAP.**
   - Energy dual at VOLL + ORDC dual + measured RTORDPA reached $12,961 against a $9,000 cap in 2019 hour 5391. Actual was $8,803 = λ $1,071 + RTORPA $2,152 + RTORDPA $5,568.
   - This is an overlay/cap composition question.
3. **R3 + R4 are probably ONE object: off-peak coal.**
   - Model coal vs EIA-930: −11.4 TWh (2019) and −15.5 TWh (2020).
   - The gap is year-round and largest in the cheapest price quintile, where the model's price is also $3–4 too high. That is the year-round median offset.
   - 2020 per-plant, model vs CAMPD gross × 0.91:
     - Martin Lake −5.9 TWh;
     - Sam Seymour −3.6;
     - W A Parish −1.8;
     - Sandy Creek −1.3.
   - **Oklaunion (ORIS 127) is absent from the 2020 fleet** although it generated 1.2 TWh gross before its 2020 retirement. This is a rule-14 membership/retirement-date candidate.
   - Coal offers stay fenced (`coal_offer_level_rebasis` R; SCED key declined). Admissible routes are availability, dated membership and commitment, not offer levels.

## Gates at HEAD

- `audit_keepers --iso ERCOT`: 0 failures, 0 warnings, after prune and status rebuild.
- `check_promotion_completeness --iso ERCOT`: OK.
- `build_status --check`: in sync.
- `stamp_config_partition --check`: OK.
- `check_mechanism_matrix --base origin/main`: OK.
- `tests/scoring/test_holdout_render_parity.py`: 12 passed.
- The parity gate is RED **locally only**, on the eight gitignored leg dirs (rule 31 correction). Every entry was verified as ignored.

## Where the bytes are (rule 34(e))

- **On `main`:** `results/calibration/r_ercot13_span` (rule-15 slim shape), plus its sidecar and run payload.
- **Legs:** local, gitignored. Provenance only (rule 33(d)):
  - 2019 arm `d667f4a8`;
  - LR-only diagnostic `5cb237e6`;
  - 2020–2025 are the R-ERCOT-12 legs (SHAs in `.gitignore`).
- **Cost:** any leg re-solve is about 17–20 min of LP.
- **Measured fact for rule 33(f):** the R-ERCOT-12 leg commits were still fetchable by full SHA after their branches were deleted. That is what made this promotion cost zero re-solves. Do not plan on it.
