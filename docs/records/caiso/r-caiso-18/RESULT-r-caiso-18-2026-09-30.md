# RESULT R-CAISO-18 — fold CC_REGULAR over-dispatch 2019–21 (2026-09-30)

**Outcome:** a measured-input root cause was found. It was built, solved in 7 shards and **PROMOTED on structure** under
the rule pre-registered in `PRECOMMIT-r-caiso-18-2026-09-30.md` §6.
- New keeper: `2026-09-30-caiso-r18-dswgas`, bundle `rcaiso18_A_span`, 2022–25.
- Fold: `2026-09-30-caiso-r18-dswgas-touchpoints`, bundle `rcaiso18_A_tp_2019_2021`, 2019–21.
- Pruned under rule 35: `2026-09-30-caiso-r17-earlyclock` and its fold.
- Year set: 2019–2025 before and after.

## Finding (PRECOMMIT §1–2)
- The CC excess is DSW import the model does not buy. Nothing else explains it: benchmark basis, demand, hydro,
  solar/wind and fleet are all ruled out.
- Mechanism: 2019–20 have no OASIS intertie print, and neither does Jan–Apr 2021. The DSW gas blocks therefore sit on the
  static Tier-3 ladder ($68 / $110), and at those offers they barely run.
- The measured-gas formula was blocked because EIA withholds AZ/OR N3045 for 2019–21. Rebuilding it from the same
  EIA-923 plant receipts reproduces N3045 where it prints (AZ r 0.980, OR r 0.975).
- The resulting 2019–20 Palo Verde level ($28 / $30) lies inside the formula's own out-of-sample error against ICE. The
  ladder lies $15–35 above ICE.

## Decision rule check (PRECOMMIT §6)
| Condition | Result |
|---|---|
| (a) 2022–25 reproduce the incumbent and stay CALIBRATED | **Met.** Max \|Δ class TWh\| = 0.0000 and max \|Δ price\| = 0.00 in every leg; single ledgered C3c 2024 |
| (b) The repair is complete: every leg shows the §4 hard-stop values, and 2019–21 log the per-hub pricing | **Met.** All 7 shards passed |
| Backstop: \|DSW error\| grows in any fold year | **Not triggered.** DSW stays below EIA-930 in every year |

## Reported: the fold (rule 30(c), not gated)

| | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| C1 CC_REGULAR vs EIA-923, TWh | +23.1 → **+14.5** | +25.3 → **+22.4** | +10.5 → +10.7 |
| DSW import, TWh (EIA-930) | 21.3 → 31.4 (44.7) | 17.4 → 21.3 (42.0) | 29.7 → 29.9 (40.9) |
| SP15 mean price, $/MWh | 41.4 → 38.4 | 35.9 → 34.8 | 54.4 → 54.5 |
| C4 gas r / NRMSE | 0.892/0.564 → 0.870/**0.454** | 0.902/0.514 → 0.889/**0.470** | 0.853/0.354 → 0.847/0.369 |

- The fold stays NOT-YET on the same three criteria (C1 CC_REGULAR, C3a 2021 +12.5 %, C4).
- **The repair is partial.** The formula hub plus wheel plus carbon clears near the model's own λ, so the DSW blocks run
  only part of the time. 2021 was already mostly on measured prints.

## The span (2022–25): unchanged
- C3a 91.72 / 57.59 / 36.28 / 36.70 vs actual 84.49 / 54.17 / 34.65 / 34.42.
- C3b 0.107 / 0.107 / 0.112 / 0.094.
- C4 gas NRMSE 0.252 / 0.247 / 0.247 / 0.288.
- C3c 2024: 0 h vs 35 h (ledgered).

## Retrievability (rule 34(e))
- The keeper and fold bundles are committed on `main` in this lane's PR.
- The per-year legs `rcaiso18_A_{Y}` are local and gitignored.
- Leg SHAs (provenance only, rule 33(d)):

  | Year | Leg SHA |
  |---|---|
  | 2019 | `6520a15a5de65234f4be9039cffc9cc6cf107296` |
  | 2020 | `3806ac8b9e4ec04791c28a61f88b9abb14846053` |
  | 2021 | `4e21440caf66a26043a62ed92d1be91bc9658ac0` |
  | 2022 | `f08c57c5d88d14f66ea51b61a3ef7e9746752f85` |
  | 2023 | `296095aa3bfc366d44a987d5cedbe72b9a2f05c6` |
  | 2024 | `41a2cc9063d7c5462b6ae27c51599670c6b6a6aa` |
  | 2025 | `9f5a93d5150ab5e7697acf1d553a4d7988854c89` |

## Operational notes
- Two shards (2019, 2024) failed at start on the account weekly limit and were relaunched.
- The first 2025 shard stopped itself at the 25-min budget during write-out. The solve takes about 44 min, so it was
  relaunched with a 50-min budget. **Future CAISO 2025 shards need a budget of at least 50 min.**

## Open
- The fold's residual DSW deficit (13 / 21 / 11 TWh) and the CC excess.
- The evening under-price, carried from earlier lanes.
