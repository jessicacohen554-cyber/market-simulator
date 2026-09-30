# RESULT R-CAISO-17 — pre-2022 EIA-930 CISO clock scan (2026-09-30)

**Outcome:** (b), a window exists. It was built, solved in 7 shards and PROMOTED on structure, under the rule
pre-registered in `PRECOMMIT-r-caiso-17-2026-09-30.md` §5.
- New keeper: `2026-09-30-caiso-r17-earlyclock`, bundle `rcaiso17_A_span`, 2022–25.
- Fold: `2026-09-30-caiso-r17-earlyclock-touchpoints`, bundle `rcaiso17_A_tp_2019_2021`, 2019–21.
- Pruned under rule 35: the outgoing `2026-09-30-caiso-r16-tiontime` and its fold.
- Year set: 2019–2025 before and after.

## Finding (PRECOMMIT §1–2)
- From the first fuel row (2018-07) through local 2022-06-13, the EIA-930 CISO `NG:` cells and `Net generation` are
  stamped **about 1 h EARLY**. `Demand` and `Total interchange` are on the true clock.
- Three references agree:
  - CAISO Outlook, 5-minute data: lag −1 in 36 of 36 months;
  - EPA CEMS gas: −1 in every month to 2022-05, then 0;
  - the solar centroid.
- The OASIS TAC clock was verified first: lag 0 against the Outlook supply sum, and no DST artifact. That refutes
  hypothesis (ii) of the R-CAISO-16 §7 lead, a TAC-file artifact.
- The 2022-06-14/15 publisher shift that opened the Demand late window also closed this one.
- **The lead is ≈ 45 min, not 60.** The whole-hour, zero-parameter re-stamp leaves a residual of ≈ +15 min, down from
  −45 min. By solar centroid the error goes from ≈ −0.6 h to ≈ +0.35 h. A fractional form was not built.

## Decision rule check (PRECOMMIT §5)
| Condition | Result |
|---|---|
| (a) 2022–25 CALIBRATED, with at most the single C3c | **Met.** Single ledgered C3c 2024 (0 h vs 35 h) |
| (b) The repair is complete: pre-measured counts in every leg, and 2023–25 reproduce the incumbent | **Met.** All 7 shards passed hard stop 2. 2023–25 max \|Δ class TWh\| = 0.0000 |

## Reported (not criteria)

The span, 2022–25:

| Year | C3a model (actual) | C3b | C4 gas r / NRMSE |
|---|---|---|---|
| 2022 | 91.74 → 91.72 (84.49) | 0.107 | 0.896 / 0.262 → **0.904 / 0.252** |
| 2023 | 57.59 (54.17) | 0.107 | 0.902 / 0.247, unchanged |
| 2024 | 36.28 (34.65) | 0.112 | 0.916 / 0.247, unchanged |
| 2025 | 36.70 (34.42) | 0.094 | 0.880 / 0.288, unchanged |

The fold, 2019–21, is NOT-YET, with the same three criteria as before (rule 30(c), reported only):

| Year | C1 CC_REGULAR vs actual | C4 gas r / NRMSE | Other |
|---|---|---|---|
| 2019 | +23.1 TWh (unchanged) | 0.882 / 0.570 → 0.892 / 0.564 | C3a, C3b and C3c not scoreable (no reference) |
| 2020 | +25.3 TWh (unchanged) | 0.879 / 0.529 → 0.902 / 0.514 | C3a, C3b and C3c not scoreable (no reference) |
| 2021 | +10.5 TWh (unchanged) | 0.816 / 0.383 → 0.853 / 0.354 | C3a +12.5 % (57.22 vs 50.87); C3c 87 → 89 h vs 27 h |

The delivered solar JJAS centroid moves 11.3 → 12.3 h in 2019–21. The fold's binding problem is CC_REGULAR volume,
not clock.

## Retrievability (rule 34(e))
- The keeper and fold bundles are committed on `main` in this lane's PR.
- The per-year legs `rcaiso17_A_{Y}` are local and gitignored.
- Leg SHAs (provenance only, rule 33(d)):

  | Year | Leg SHA |
  |---|---|
  | 2019 | `3101bb74092eda99c45f37ad7f8601c265c9277e` |
  | 2020 | `0eda8f1b141be4c4a3bbbd54728fa621ec96f429` |
  | 2021 | `3e9d26821c05c079b02db4f592018e321c3738e8` |
  | 2022 | `aa9982b2c066252bda08fe598803f446fe785af2` |
  | 2023 | `ce212930baf72460b8db316316fcf17bd31de5d7` |
  | 2024 | `ba75dcaf4af68a6dc0092bf44e298cb41ca4b5f3` |
  | 2025 | `c2c5b410eb6d1b7f5bda89c15efb0e92e90178f4` |

## Open
- Fold CC_REGULAR over-dispatch in 2019–21: +23 / +25 / +10 TWh.
- The sub-hour (fractional) clock form: a measured 0.75/0.25 split. It is not built because it would add a parameter.
- The evening under-price, carried from earlier lanes.
