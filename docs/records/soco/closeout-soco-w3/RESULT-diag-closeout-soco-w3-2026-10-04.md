# RESULT closeout-SOCO-w3: DIAGNOSTIC metered coal commitment state on the holdout recipe

Lane closeout-SOCO-w3, 2026-10-04. Bars: `PRECOMMIT-diag-closeout-soco-w3-2026-10-04.md`, written and pushed before
any shard launched. **DIAGNOSTIC, never promotable** (rule 13). Registered nowhere on main.

## Verdict: **PARTLY**, on the pre-registered scale

CC 2023 clears and CC 2021 does not. In both years the CC share of displacement is ≥ 0.5 (0.84 and 1.24). So holding
coal at its metered commitment state does displace CC first, but the over-run is bigger than what metered commitment
practice can realise. Commitment practice is a real part of the CC over-run but not the whole story.

## Run

| item | value |
|---|---|
| recipe | keeper `closeout_soco_3_span` + `mustrun_chp_btm_holdout=true` + `diagnostic_coal_metered_online_floor=true` (both read True in all 7 `run_config_<Y>.json`) |
| pin | `6cfad57bbf1ce96571989633e2cc8e47d4b0032a` |
| legs (one shard per year, rule 36) | 2019 `65148b1c`, 2020 `52d1009f`, 2021 `e64c15a0`, 2022 `4b0c37fa`, 2023 `32432fb2`, 2024 `feb94701`, 2025 `57feefc9` (branches `claude/closeout-soco-w3d-<Y>`, provenance only; all 7 shards archived after verification) |
| composed span | `results/calibration/closeout_soco_w3d_span` (`scripts/probes/_closeout_socow3d_compose.py`) |
| control | holdout probe `closeout_soco_w3_span` (run `2026-10-04-closeout-soco-w3-btm`) |
| bench | identical to the control's: the `classFull` parts are byte-equal to the control registration's (`c96470ec`) in 2019, 2021, 2023 and 2025. The diagnostic does not move the lockstep seam. |
| kills | none fired: slack = dump = 0 MWh in every year; arm live in every leg; recipe = control + the diagnostic |

## Class deltas, probe − control (TWh, P1)

| year | Δcoal (BIT+PRB) | zero-LP bound | realised / bound | ΔCC_REGULAR | ΔCT_PEAKER | ΔST_GAS | CC share |
|---|---|---|---|---|---|---|---|
| 2019 | +1.85 | 4.49 | 0.41 | −0.91 | −0.68 | −0.13 | 0.49 |
| 2020 | +1.47 | 2.94 | 0.50 | −0.81 | −0.45 | −0.10 | 0.56 |
| 2021 | +1.30 | 2.00 | 0.65 | −1.09 | −0.20 | −0.02 | **0.84** |
| 2022 | +0.36 | 1.78 | 0.20 | −0.25 | −0.10 | +0.00 | 0.71 |
| 2023 | +0.50 | 2.06 | 0.24 | −0.63 | +0.14 | +0.03 | **1.24** |
| 2024 | +1.43 | 2.05 | 0.70 | −0.62 | −0.65 | −0.10 | 0.44 |
| 2025 | +0.78 | 1.30 | 0.60 | −0.57 | −0.18 | −0.02 | 0.73 |

The CC share in 2023 is above 1 because CC also lost energy to a small CT_PEAKER gain. Hydro and nuclear move by less
than 0.01 TWh in every year. Source: `diag_class_deltas.csv`.

## Scored records vs the control (`calibration_verdict.determine`, rubric v3.20)

Only four records change status:

| record | control | diagnostic |
|---|---|---|
| C1 CC_REGULAR 2023 | FAIL +7.57 TWh | **PASS** +6.95 |
| C1 COAL_BIT 2019 | FAIL −7.47 TWh | **PASS** −5.43 |
| C8 forced share COAL_BIT 2024 | PASS 0.0 % | FAIL 31.4 % (the diagnostic's own forced energy, attributed to its own id, as pre-registered) |
| C8 CT_PEAKER 2025 | PASS 0.0 % | SKIPPED (immaterial, 2.0 % of load) |

- **C1 CC_REGULAR 2021:** stays FAIL, +8.63 → +7.54 TWh against a 7.10 band. Clearing it would need about −1.53 TWh;
  the diagnostic delivered −1.09.
- **C3a mean (system lambda):** 2019 +14.3 → +12.4 %, 2020 +14.5 → +13.2 %, 2022 −9.4 → −9.8 %; other years move ≤ 1 pp.
- **C3b monthly NRMSE:** 2022 0.259 → 0.261. The night-price effect does not move the 2022 caveats.
- **C3c:** not scored on the SOCO lambda (owner ruling 2026-09-28).

Full table: `diag_score.csv`.

**Mechanism-id caveat.** At the pin the diagnostic is D-2 id 28. On main it was renumbered to 29 when main's UC took
28. `legitimacy_diagnostics.py` from main therefore labels the diagnostic's forced energy "uc_schedule, no declared D-4
window" (the C8 2024 row). That energy is the diagnostic, not UC. No keeper arms UC and SOCO has no UC.

## What this means for SOCO-F1

- **CC is displaced first.** When coal is held to its metered online state, CC absorbs most of the displaced energy:
  share 0.44–0.84 in every year except 2023, where it is 1.24.
- **Commitment practice explains only part of the over-run.**
  - The LP realises only 20–70 % of the zero-LP coal bound.
  - Even with metered state pinned, 2021 CC remains 0.44 TWh over its band.
  - The residual sits elsewhere: CC heat rate and offer position against coal at the dispatched commitment, which is
    phase 0b's open item.
- **The finding is evidence, not a lever.** No keeper recipe changes. The finding is that conduct (coal commitment
  practice) carries a measurable, CC-directed share of the gap.

## Disposition

- Not promoted, and never promotable.
- The local scoring registration (`2026-10-04-closeout-soco-w3d-diag`) stays off main (E13). The bundle, registration
  and bench parts are on branch `claude/closeout-soco-w3-diag`.
- Matrix cell `diagnostic_coal_metered_online_floor` SOCO O → G: refused by rule 13 as a keeper input, tested as a
  diagnostic.
