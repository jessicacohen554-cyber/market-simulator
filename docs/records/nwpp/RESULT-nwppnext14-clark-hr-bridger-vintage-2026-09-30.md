# RESULT — NWPP-NEXT-14: EIA-923 CC-family heat rate (Clark) + per-unit fuel-split tranches (Bridger) → keeper #19

PRECOMMIT: `PRECOMMIT-nwppnext14-clark-hr-bridger-vintage-2019-2025-2026-09-30.md`. Zero-LP findings:
`FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md`.

## 1. Solve

Seven year-isolated shards at pin `54edd9e3`. Every hard stop passed:
- `scenario_config` differs from keeper #18 only in `eia923_cc_family_heat_rates` and `campd_unit_fuel_split`, plus
  fields added on `main` since, which are absent in #18 and False here.
- `resolved_inputs.thermal_tranches` is `thermal_tranches-perunit-fuelsplit-NWPP.csv` in every year.
- P1 demand matches keeper #18 exactly in every year.
- 2019 took 8,018 s of LP time (P0 3,187 s + P1 4,832 s).

| year | leg commit (provenance only, rule 33(d)) | Clark 2322 CC TWh (#18 → arm; EIA-923) |
|---|---|---|
| 2019 | cd4ceba85ac600ec07475d017991d2dddd961ba8 | 3.69 → 0.625; 0.447 |
| 2020 | d3498dec9fece60c5744e352caab846a1f313f5f | 3.69 → 1.210; 0.561 |
| 2021 | cb9d7e61f7c1b1b3fe8d5466ad3386ec2af96fc6 | 3.69 → 0.583; 0.700 |
| 2022 | 7e75c2694e2058c4ba269b586c9ddaab97b09bd8 | 3.69 → 0.446; 0.770 |
| 2023 | ab503a6037c6d9f93628af85042365e84b3ae254 | 3.69 → 0.413; 0.433 |
| 2024 | 36e0ea7c304d8928457fa66ff7a589e99c4ddb43 | 3.69 → 1.112; 0.862 |
| 2025 | f589faf2ae89682417d9001ef6e6b42f5e140f79 | 3.69 → 0.973; 0.664 |

Clark CC is now within its measured range in every year. Most of its 2.5–3.3 TWh/yr went to other CC plants, so the
CC_REGULAR class moves only −0.17 to −0.53 TWh; CT_PEAKER picks up +0.10 to +0.34 TWh.

## 2. Verdict (rubric v3.8), per record against keeper #18

- Determination unchanged: **NOT-YET on {dispatch_corr}**, one record: **C4 coal 2023 r 0.662 → 0.670** (NRMSE 0.317).
  Price is unscored.
- 75 of 161 records move; **0 change status**.
- C1 (model − actual, TWh), improvements:
  - CC_REGULAR 2019 +1.33 → +1.03, 2020 +1.71 → +1.50, 2024 +6.72 → +6.27, 2025 +8.00 → +7.47.
  - CT_PEAKER 2019 −2.01 → −1.91, 2020 −0.64 → −0.48, 2021 −2.53 → −2.32, 2022 −1.70 → −1.60, 2023 −4.45 → −4.25,
    2024 −3.20 → −2.98.
  - CC_CHP and ST_GAS shrink slightly every year.
- **Regressions, at full magnitude:**
  - C1 CC_REGULAR 2021 −1.87 → −2.15, 2022 −3.89 → −4.06, 2023 −1.37 → −1.84.
  - C1 CT_PEAKER 2025 +2.48 → +2.81.
  - C1 COAL_BIT 2023 +5.04 → +5.20.
  - C4 coal 2020 0.767 → 0.764, 2021 0.764 → 0.763, 2022 0.721 → 0.719, 2024 0.755 → 0.745.
  - C4 gas 2024 0.898 → 0.896.
- C4 improvements: coal 2019 0.726 → 0.728, coal 2023 0.662 → 0.670; gas 2019 0.729 → 0.733, 2020 0.799 → 0.811,
  2021 0.844 → 0.848, 2023 0.771 → 0.780.
- C8 forced share: 0 % in every class-year.

## 3. Decision

Owner card: **"Promote + prune #18"**, on structural integrity (rule 14): Clark's impossible heat rate and Bridger's
vintage-static coal row are repaired, with zero new DOF. Every regression above is reported.

- Keeper #19 is `2026-09-30-nwppnext14-clark-hr-bridger`, bundle `results/calibration/nwppnext14_span`.
- Keeper #18 was pruned with `prune_iso_runs.py --iso NWPP --force-uncite`.
- `audit_keepers --iso NWPP` PASS; `check_promotion_completeness --iso NWPP` OK.
- `check_forecast_parity`: both new fields classify as wired, NWPP UNACCOUNTED 0.
- Year set before and after: 2019–2025.

Retrievability: the composed keeper bundle lands on `main` with this PR. The per-year legs were transport only, and a
leg not on `main` is costed as a re-solve (~35–60 min each, ~135 min for 2019).

## 3a. Reconciliation with the parallel NEXT-14 lane (PR #6935)

Two sessions ran the same handoff. The other built `cc_subfloor_eia923_heat_rates` (Clark, the same EIA-923 CC rate)
and `campd_per_unit_vintage_denominator` (per-unit rows on each year's own EIA-860 vintage nameplate; also repairs North
Valmy), merged them, and could not solve (nesting limit). Owner card **"Keep #19; retire dup Clark field"**:

- `cc_subfloor_eia923_heat_rates` is **DELETED** (rules 19 / 26): field, cache-key entry, seam, test, matrix row and
  cells.
- Its `EGRID_CC_HR_PHYSICAL_FLOOR` constant moved back into `data/fleet/eia860.py`. In `config/constants.py` it had
  added a solve-surface row and turned `test_persisted_identity` red on `main` for five ISOs; the move restores every
  pin, with no value moved.
- `campd_per_unit_vintage_denominator` stays default-off as NEXT-15's replacement candidate for the fuel-split
  composition. The selector now **refuses** arming it beside `campd_unit_fuel_split` (rule 19).
- The other lane's `PRECOMMIT-nwppnext14-vintage-denominator-*` and `docs/records/nwpp/nwppnext14/shards/*` arm the deleted
  field. They are **stale and must not be launched**.
- Re-scored on `main`'s rubric v3.13: same determination, same single FAIL record.

## 4. Open, for the next lane

1. **C4 coal 2023 (0.670) is Jim Bridger's offer** (FINDING-nwppnext14 §1).
   - Bridger's delivered-cost offer ($38–51/MWh) idles it Jun–Oct.
   - The LP spends its soft take floor in dear-gas Q1.
   - Next: identify, from public PacifiCorp / Idaho Power filings, whether Bridger Coal Company's cost splits into
     fixed and variable parts (owner card "Both"). Never a tuned passthrough (rules 1, 13).
2. **Lever 3 (coal WEFOR relief).** Owner card "New sub-gate, default off":
   - build a live-capacity denominator as a NEW field, leaving miso-266's flag and MISO's keeper byte-identical;
   - then arm it with the WEFOR relief.
3. **CC_REGULAR under-dispatch 2021–2023 grew**, and 2024–25 over-dispatch is still +6.3 / +7.5 TWh (PASS). A zero-LP
   per-plant decomposition of where Clark's energy went is the first step.
