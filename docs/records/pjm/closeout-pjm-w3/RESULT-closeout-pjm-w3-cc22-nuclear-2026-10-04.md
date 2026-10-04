# RESULT — closeout-PJM-w3: (A) own-year CC window + (B) nuclear winter-capability basis, keeper base (probes; no promotion requested)

Lane `closeout-PJM-w3` on branch `claude/closeout-pjm-w3`. Bars:
`PRECOMMIT-closeout-pjm-w3-cc22-nuclear-2026-10-04.md` plus its Addendum A, fixed before any v2 solve. Build pin
**`bc163dbc81744b13cfd82ecabd930f5fc69d70e3`** (v2). The keeper is unchanged: `2026-10-03-closeout-pjm-nuc-keeper`.

| run | probe id | transport branch | legs (one shard per year, rule 36) |
|---|---|---|---|
| (A)+(B) v2 | `2026-10-04-closeout-pjm-w3-b` | `claude/closeout-pjm-w3abv2-probe` @ `926cdab4` | 2019 `f66b2cc2`, 2020 `ec9f2488`, 2021 `5d3a53ed`, 2022 `fba5a094`, 2023 `e7062b06`, 2024 `f42a466a`, 2025 `d22351da` |
| (A)-only | `2026-10-04-closeout-pjm-w3-only` | `claude/closeout-pjm-w3a-probe` @ `e13e92c4` | 2019 `e592109a`, 2020 `a4cfb631`, 2021 `c9f2e35d`, 2022 `e60c57e7`, 2023 `8d277e3a`, 2024 `8541ca86`, 2025 `7d6fe6ef` |

Both registrations stay on their transport branches, off `main` (E13). The full per-year bundles, including
`dispatch/<year>_P1.parquet`, are on the leg branches `claude/closeout-pjm-w3abv2-<year>` / `claude/closeout-pjm-w3a-<year>`.

## Verdict

**(A)+(B) does not beat the keeper, and no promotion slot is requested.** It does what the PRECOMMIT declared and
nothing else:
- R1' passes in every year.
- The one gate flip is the declared risk: C1 CT_PEAKER 2021 goes PASS→FAIL, **−7.92 → −8.02 TWh** against ±8.00.
- CC_REGULAR 2022 stays FAIL as declared (+8.96 → +8.57).
- R2 misses by 0.01 TWh.

Failing records go from 8 to 9; PJM stays **NOT-YET**. The desk is putting the nuclear-winter result to the owner as
structure-vs-gates (measured EIA-860 winter capability against one marginal CT flip).

**(A)-only is gate-neutral.** It passes its bar in every year and flips no record; the only rows that change status do so because the probe is unattested. CC_REGULAR 2022 moves +8.96 → +8.68 (still FAIL), and failing records stay at 8. It is a real rule-14/17 window-vintage repair at zero gate cost, but it does not beat the keeper, so no slot is requested. Whether it rides a future PJM keeper is the owner's call.

## (A)+(B) v2 bars

| bar | reading | result |
|---|---|---|
| R1' nuclear Δ ≥ 0, only in months whose committed CF reads 1.00, total in [0.4×, 1.05×] | +0.657 / +0.494 / +0.917 / +0.511 / +0.114 / +0.657 / +0.494 TWh (2019–25) = **0.75 / 0.76 / 0.74 / 0.70 / 0.76 / 0.73 / 0.72×**. On the model's own month clock the cap moves only in model-months 1 and 12, plus 6 in 2020 and 2 in 2021. | **PASS** |
| R2 CC_REGULAR 2022 Δ in [−1.0, −0.4] | **−0.390 TWh** | **MISS by 0.010** |
| Declared risk: C1 CT_PEAKER 2021 | −7.92 → **−8.02** (PASS→FAIL) | the declared structural consequence |
| K1 no other C1 / C3a / C3b PASS→FAIL | none | **holds** |
| K2 nuclear outside R1' | none | **holds** |

## Readings

- **Class Δ vs the keeper (TWh).**

  | year | nuclear | CC_REGULAR | COAL_BIT | CT_PEAKER | other |
  |---|---|---|---|---|---|
  | 2019 | +0.657 | −0.245 | −0.271 | −0.066 | COAL_PRB −0.026, import −0.018 |
  | 2020 | +0.494 | −0.177 | −0.205 | −0.057 | import −0.032 |
  | 2021 | +0.917 | −0.610 | −0.115 | −0.101 | import −0.059 |
  | 2022 | +0.511 | −0.390 | −0.039 | −0.057 | ST_GAS +0.011 |
  | 2023 | +0.114 | −0.682 | +0.172 | +0.171 | ST_GAS +0.062, import +0.110 |
  | 2024 | +0.657 | −0.185 | −0.188 | −0.173 | ST_GAS −0.034 |
  | 2025 | +0.494 | −0.345 | −0.039 | −0.083 | ST_GAS −0.021 |

- **Scored records.**
  - C1: CC_REGULAR 2022 +8.57 (FAIL); COAL_BIT 2019/20/21 +19.46 / +12.53 / +16.60 (FAIL).
  - C3a 2022 −16.7 % and 2025 −11.7 %; C3b 2022 0.294 and 2025 0.221 (all FAIL, unchanged).
  - Every other C1, C3a and C3b record keeps the keeper's status. Nuclear is not a scored C1/C2 class.
- **Unserved energy and legitimacy.** Unserved energy equals the keeper's in every year (500 / 0 / 0 / 0 / 0 / 1,492 / 1,085 MWh). The
  rebuilt 7-year `legitimacy_diagnostics.json` has the keeper's pass pattern: D1, D5, D9 and D10 pass; D2 and D4 fail as in the keeper. C8 (forced share)
  passes.
- **Probe-only rows.** C3c 2019/2021/2022 read FAIL and C6 reads UNATTESTED only because the unattested probe carries
  no attestation, so the keeper's ledgered C3c entries don't apply. The tail magnitudes are identical to the keeper's.
- **The "0 units re-rated" log line** is the lookahead pipeline's fleet build (`runner.py:1251`, proposed units only).
  The dispatch fleet is built once (`runner.py:2894`), re-rates 31 reactors, and serves P0 and P1.

## (A)-only bars and readings

| bar | reading | result |
|---|---|---|
| CC Δ within ±0.15 TWh of the cc22 §3 sizing | 2019 **0.000** (inert: no by-year rows; byte-identical to the keeper) · 2020 **+0.013** (sized +0.07/+0.09) · 2021 **−0.198** (−0.26/−0.34) · 2022 **−0.274** (−0.28/−0.37) · 2023 **−0.640** (−0.52/−0.67) · 2024 **+0.047** (+0.02) · 2025 **−0.148** (−0.10/−0.13) | **PASS** |
| no PASS→FAIL | none (CT_PEAKER 2021 −7.92 → −7.88) | **holds** |

- **Class Δ vs the keeper (TWh).**

  | year | CC_REGULAR | COAL_BIT | CT_PEAKER | other |
  |---|---|---|---|---|
  | 2019 | 0 | 0 | 0 | — |
  | 2020 | +0.013 | −0.032 | +0.021 | import −0.018 |
  | 2021 | −0.198 | +0.133 | +0.038 | — |
  | 2022 | −0.274 | +0.139 | +0.035 | COAL_PRB +0.016, ST_GAS +0.035, import +0.037 |
  | 2023 | −0.640 | +0.204 | +0.190 | ST_GAS +0.070, import +0.117 |
  | 2024 | +0.047 | −0.028 | 0 | import −0.014 |
  | 2025 | −0.148 | +0.038 | +0.058 | ST_GAS +0.014, import +0.024 |

- **What the released commitment hours turn into.** They go to coal and peakers about one-for-one, not to imports.
  That is why the CC 2022 gain is small (−0.27): as cc22 §3 found, the window release sits in Dominion/SWMAAC CCs
  that are already under.
- **Scored records.** C1 CC_REGULAR 2022 +8.68 and COAL_BIT 2019/20/21 +19.73 / +12.70 / +16.85 (FAIL). C3a/C3b
  2022 and 2025 are unchanged (−16.6 % / 0.293, −11.6 % / 0.222). Unserved energy and the legitimacy pass pattern equal the keeper's.
- **Attribution within (A)+(B).** In 2022 (A) alone gives CC −0.274 and (A)+(B) gives −0.390, so winter nuclear
  adds about −0.12. The CT_PEAKER 2021 flip comes from (B): (A) alone moves CT 2021 +0.04, while (A)+(B) moves it −0.10.


## Disclosed against interest

1. **v1 was killed under its own K2** (Addendum A). The v1 (A)+(B) legs 2019 `47bef37b` and 2023 `2c7d5313` are
   evidence only. The 2020, 2021, 2022 and 2024 v1 shards were **stopped, v1 killed under K2**: interrupted and
   archived before pushing anything.
2. **Benchmark re-point.** After a container OOM restart, the compose-time `shared_inputs` refs of the (A)+(B) span had no bytes behind them. The kill came in the composer's diagnostics step, while the composer parent still held its frames; the diagnostics alone peak at 5.3 GiB.
   `--restore-shared-inputs` rebuilt the keeper's own frames byte-for-byte (`campd-0789c1dbbf0d`,
   `eia923-9c2249fc7b71`, `eia930-ff910fd8cfa6`). I re-pointed the span to them with `--rebuild-benchmark`, so probe and
   keeper are scored on the same benchmark.
3. **(A)-only legs were solved at `bc163dbc`, not at the v1 pin `2c9284cb`** named in Addendum A. The only difference
   between the two is the unclipped nuclear table, which (A)-only never reads.
4. **Leap-year month clock (observation, out of lane, not repaired).** The model's `_hour_to_month_index` uses a
   365-day table. In 2020 and 2024 every measured monthly CF row from March on therefore starts one day early. This
   is pre-existing keeper behaviour; I reported it to the desk.
5. **Leg bundles carry `unit_hourly`** through the `.gitignore` negation. The registered slim bundle drops it (rule 15).

## Promotion

**None requested.** Neither run beats the keeper on the gates. Neither composed bundle is on `main`; a promotion would
first need the full-bundle compose from the leg branches. Retention (rule 31): the leg branches are transport only;
the bundles will not survive the container, and the owner rules on whether either probe is kept.
