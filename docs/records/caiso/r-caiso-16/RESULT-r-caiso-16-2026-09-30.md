# RESULT R-CAISO-16 — interchange lag (2026-09-30)

**Outcome:** PROMOTED on structure, under the rule pre-registered in `PRECOMMIT-r-caiso-16-2026-09-30.md` §6.
- New keeper `2026-09-30-caiso-r16-tiontime` (bundle `rcaiso16_A_span`, 2022–25).
- Fold `2026-09-30-caiso-r16-tiontime-touchpoints` (bundle `rcaiso16_A_tp_2019_2021`, 2019–21).
- Outgoing `2026-09-29-caiso-r15-clockfull` and its fold are pruned (rule 35).

## Finding
- The per-DIBA feed is on the true clock, so census rows #2 and #3 close with nothing to build.
- The late window registered for the "generation" family is right for NG, but wrong for `Total interchange`.
  - OASIS TAC: NG +1 h / TI 0 h gives R² 0.979 in 2024, vs 0.701 when TI is also shifted.
  - The counterparty legs agree.
- The armed repair was therefore shifting TI 1 h early at two places: the frame seam and the caiso-80 demand term.
- Owner card: "Narrow the repair". Details are in PRECOMMIT §1–2.

## Decision rule check (PRECOMMIT §6)
| Condition | Result |
|---|---|
| 1. 2022–25 CALIBRATED | **Met.** Single ledgered C3c 2024 (0 h vs 35 h), same as the incumbent |
| 2. TI repair complete | **Met.** All 7 shards passed the hard stop (TI field 0) |
| 3. 2019–22 reproduce the incumbent | **Met.** max \|Δ class TWh\| = 0.0000 in 2019, 2020, 2021 and 2022 |

## Reported (not criteria)
| Year | C3a model (actual) | C3b | C4 gas r / NRMSE | Max \|Δ class TWh\| vs r15 |
|---|---|---|---|---|
| 2022 | 91.74 (84.49), unchanged | 0.107 | 0.896 / 0.262 | 0.0000 |
| 2023 | 57.58 → 57.59 (54.17) | 0.107 | 0.901/0.248 → 0.902/0.247 | 0.016 (CT_PEAKER) |
| 2024 | 36.47 → 36.28 (34.65) | 0.116 → 0.112 | 0.915/0.249 → 0.916/0.247 | 0.124 (CC_REGULAR) |
| 2025 | 36.81 → 36.70 (34.42) | 0.096 → 0.094 | 0.879/0.290 → 0.880/0.288 | 0.075 (import) |

- Fold 2019–21: NOT-YET, with the same three degraded criteria as before (fuelmix, price_mean, dispatch_corr). Reported only (rule 30(c)).
- Governance: the DOF ledger is 9 entries / 6 residual, carried unchanged.

## Retrievability (rule 34(e))
- The keeper and fold bundles are committed on `main` in this lane's PR.
- The per-year legs `rcaiso16_A_{Y}` are local and gitignored. Shard branches `claude/r-caiso-16-A-{Y}` carry them in transit only; that is provenance, not a recovery route.
- Leg SHAs: 2019 `c24839b0459868872cf2b9187ef1127f45665f3f`, 2020 `4fcba679835ee24f79679373c2937dad287ce658`, 2021 `0bee3fb8309dd81472c46c08d03e4f6a8ae97df3`, 2022 `cdef086cf0352135fafc1d95c91096ee45948955`, 2023 `c186df17a95ba25594ca970fd6136ecfd95512e6`, 2024 `d4b933ff3b720315162d58af27abffd265560f9e`, 2025 `dc7849971bc3128ee467d931830a66748b1b9cfc`.

## Process note
- `prune_iso_runs.py --iso CAISO` keeps only the keeper plus `--keep` ids. Run without `--keep`, it also pruned the freshly stamped fold.
- The fold was re-composed from its legs at zero LP and re-registered with the same determination. `audit_keepers --iso CAISO` then read 0 failures.
- Successor lanes: pass `--keep <fold id>` to the prune.

## Open
- On the TAC regression, 2019–21 (outside any registered window) prefer NG −1 h over (0,0). R² is ≤ 0.83, so the evidence is weak and may be a TAC-file clock artifact. Recorded, not built.
- The evening under-price, carried from earlier lanes.
