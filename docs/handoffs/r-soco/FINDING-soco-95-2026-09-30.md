# FINDING soco-95 — C3b 2022 monthly price-shape diagnosis (zero LP)

**Scope.** Zero LP: no solve, no registration, no mechanism tested, so no matrix cell moves. Keeper unchanged:
`2026-09-30-soco93-pondage-bound` (`results/calibration/soco93_span`), rubric v3.11 NOT-YET 7/4/0/2/1. The only FAIL
is C3b 2022 (monthly load-weighted price NRMSE 0.275 vs ≤ 0.20).

## Conclusion — no admissible lever; C3b 2022 is the ledgered C3a peak premium, concentrated in Elliott

1. **The whole miss is in λ's top-20 % hours.** If the model price is set to λ in those hours only, C3b 2022 reads
   **0.055**. If it is set to λ in the low-40 % hours instead, it reads 0.281 (no help). Top-20 % is the same peak
   premium soco-94 found behind C3a, and the owner ledgered that in v3.11.
2. **December (Winter Storm Elliott) is 67.5 % of the squared error; July is 19.8 %.** Over the 96 Elliott hours
   (Dec 23–26), λ averages **$406.8/MWh (max 1,657)** and the model **$86.7 (max 100.5)**. Elliott is 91 % of
   December's gap.
3. **It is shape, not level.** Level (annual bias²) is 17 % of the MSE. The shape-only NRMSE (model rescaled to the
   actual annual mean) is 0.242. Correlation is r = 0.79.
4. **The one untested measured fuel input fails both tests.** Re-pricing each setter hour at the delivered fuel price
   its own plant paid that month (EIA-923 Sch. 2) gives 2022 **0.240 (still FAIL)**. It also moves a passing year:
   2023 goes 0.095 → 0.181, the soco-94 thin-CT-receipt artefact. So it neither repairs 2022 nor leaves the other
   six years alone.
5. **Every object behind the premium is already adjudicated.** These are SE daily gas (owner "Don't buy"), CT
   start/no-load (G, refuted twice), and CT/CC incremental HR (I). Scarcity pricing is `.` by card S5 ("No ORDC, no
   scarcity seed"). Priced interchange (U) is not a 2022 lever: SOCO was a small net importer at Elliott's peak
   (EIA-930 total interchange −443 / −711 MW mean on Dec 23 / 24, min −1,650). A priced seam would also re-price
   every hour of every year. And mapping SOCO's counterparties (TVA, Duke, FPL: no LMP) to a measured neighbour
   price is a rule 14 misalignment that has not been reconciled.

**Elliott, as information (not a gate change):**

| case | C3b 2022 |
|---|---:|
| keeper as scored | **0.275** FAIL |
| model = λ in Elliott hours only (Elliott removed as a miss) | **0.158** pass |
| December dropped (11-month NRMSE) | 0.172 pass |
| Elliott the ONLY miss (every other month exact) | **0.206** FAIL by itself |
| model = λ in top-20 % λ hours | 0.055 |

Elliott is necessary and nearly sufficient for the failure. Without it, 2022's summer premium (Jun −18.3, Jul −33.2,
Aug −13.2 $/MWh, mostly CT_PEAKER-set hours) passes at 0.158.

## 1. Method

Probe: `scripts/probes/_soco95_c3b_2022.py` (new). It reuses the soco-94 `fleet_only` rebuild and setter rule
(`_soco94_year_pattern`). The model monthly price is demand-weighted from the committed `hourly/system_<y>.parquet`.
The actual is the scorer's own bench `avgLMP.rt_lw_mon`, and the scorer's `_nrmse` is used unchanged. C3b reproduces
exactly in all seven years. Counterfactuals are first order: model side only, same setter, no re-stack.

## 2. All years (so a lever can be checked against the six passing years)

| year | C3b | level share of MSE | shape-only NRMSE | r | setter at own plant-month F923 |
|---|---:|---:|---:|---:|---:|
| 2019 | 0.168 | 0.79 | 0.075 | 0.61 | 0.171 |
| 2020 | 0.175 | 0.78 | 0.089 | 0.87 | 0.181 |
| 2021 | 0.119 | 0.03 | 0.117 | 0.90 | 0.092 |
| **2022** | **0.275** | 0.17 | **0.242** | 0.79 | **0.240** |
| 2023 | 0.095 | 0.13 | 0.090 | 0.83 | **0.181** |
| 2024 | 0.180 | 0.01 | 0.177 | 0.86 | 0.143 |
| 2025 | 0.190 | 0.00 | 0.190 | 0.56 | 0.158 |

2019–20 C3b is mostly level: that is the ledgered C3a over. The other years are shape.

## 3. 2022 by month (load-weighted $/MWh; gap = model − λ, split by λ band)

| mo | model | λ | gap | low-40 % | mid | top-20 % | largest setter contribution |
|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 47.9 | 41.9 | +6.0 | +6.7 | 0.0 | −0.7 | — |
| 2 | 47.1 | 40.1 | +7.0 | +8.0 | −0.1 | −0.9 | CT_PEAKER −0.6 |
| 3 | 48.2 | 40.7 | +7.5 | +7.9 | −0.4 | 0.0 | — |
| 4 | 63.8 | 59.4 | +4.4 | +6.5 | −2.1 | 0.0 | — |
| 5 | 89.7 | 90.7 | −1.1 | +0.3 | +0.8 | −2.1 | CT_PEAKER −0.9 |
| 6 | 87.9 | 106.1 | −18.3 | +0.2 | −4.7 | −13.8 | CT_PEAKER −9.8, hydro/PS −3.9 |
| 7 | 84.3 | 117.5 | −33.2 | +0.4 | −3.8 | −29.8 | CT_PEAKER −14.4, hydro/PS −6.7, ST_GAS −6.5 |
| 8 | 99.9 | 113.0 | −13.2 | 0.0 | −0.2 | −12.9 | CT_PEAKER −5.9 |
| 9 | 85.7 | 91.0 | −5.3 | +1.3 | −0.9 | −5.8 | CT_PEAKER −2.3 |
| 10 | 61.9 | 59.9 | +2.0 | +4.5 | −2.5 | 0.0 | — |
| 11 | 54.7 | 56.8 | −2.1 | +4.2 | −4.6 | −1.7 | hydro/PS −1.7 |
| 12 | 61.5 | 122.8 | **−61.3** | +2.4 | −1.3 | −62.5 | CT_PEAKER −39.0, ST_GAS −11.5 |

The low-40 % offset (Jan–Apr, +4 to +8) is the soco-91 night CC setter (CC incremental HR, owner "Keep refused").
Its C3b reach is small: low-40 % at λ gives 0.281.

## 4. Caveat budget (measured, for the owner's card)

The ledgered caveats aggregate per criterion. SOCO carries 2 (C1, C3a) against `MAX_LEDGERED_CAVEATS = 1`. A C3b row
would make 3. All 11 registered runs were re-scored, full span plus every single year (72 verdicts), under
monkeypatched variants:

| variant | verdicts that change |
|---|---|
| budget 1 → 3 (global), C3b still FAIL | 1: SOCO 2019 alone NOT-YET → CALIBRATED-WITH-CAVEATS |
| C3b 2022 scoped row, budget 1 | 0 |
| C3b 2022 scoped row + budget 3 | 3: SOCO span, 2019, 2022 → **CALIBRATED-WITH-CAVEATS** |

**No non-SOCO verdict moves under any variant.** Outside SOCO only C3c is ledgerable, and one ledgered criterion is
the most any other ISO can carry, so a global raise and a SOCO-scoped exemption give the same numbers today. They
differ only in precedent: a global raise also relaxes the v3.1 invariant ("the budget staying at exactly 1 is the
sole numeric bound") for any future scoped row in any ISO. One implementation note: a C3b record carries
`actual = None`, so the v3.10 direction check fails closed on it. A C3b row needs its own direction semantics (NRMSE
above the band).

## 5. Records

- Probe: `scripts/probes/_soco95_c3b_2022.py` (`--out DIR` writes `c3b_<y>.json` and caches `fleet94_<y>.npz`; ~25 s
  per year).
- Keeper unchanged.

## 6. Owner rulings (decision cards, 2026-09-30) — implemented as rubric v3.12

The owner chose **"Scoped ledger row"** for C3b 2022 and **"Keep budget at 1"** for the budget.

- `SCOPED_LEDGER_ENTRIES` gains `(SOCO, 2022, price_shape, None)` with a new direction, `above_band`. The row binds
  to the record's NRMSE exceeding `PRICE_SHAPE_NRMSE_MAX` through `_SCOPED_BAND_MAX`. Every v3.10 guard is
  unchanged. `MAX_LEDGERED_CAVEATS` stays 1 and `RUBRIC_VERSION` becomes `"3.12"`. Genealogy is
  `docs/governance/rule-history.md` §25; tests are in `tests/scoring/test_calibration_verdict_scoped_ledger.py`
  (35 pass).
- **Re-scored** 72 verdicts (11 registered runs × full span + every single year) against the `origin/main` scorer.
  Only SOCO rows differ:

| scope | before (v3.11) | after (v3.12) |
|---|---|---|
| SOCO keeper, 2019–2025 | NOT-YET 7/4/0/2/1 (FAIL: price_shape) | **NOT-YET 7/4/0/3/0** (caveat budget exceeded, ledgered 3/1) |
| SOCO keeper, 2022 alone | NOT-YET (C3b FAIL) | NOT-YET (ledgered 2/1) |
| SOCO keeper, 2020 alone | CALIBRATED-WITH-CAVEATS | unchanged (reason text now reads "v3.10-v3.12") |
| every other run / year | — | byte-identical |

- Refreshed: `results/calibration/soco93_span/metrics.json` (`--write-metrics`). `build_status.py` was run for every
  ISO; in the eight non-SOCO parts only `rubric_version` moves (checked by hash with that field masked). Also
  refreshed: the SOCO registry definition and the SOCO matrix `gates` stamp.
- **SOCO is not frontier.** No criterion fails, but the determination is NOT-YET on the budget alone: 3 ledgered
  (C1 2019 COAL_BIT, C3a, C3b) against 1. It can move only through a budget ruling (declined this session) or by
  removing ledgered rows through model repair.
