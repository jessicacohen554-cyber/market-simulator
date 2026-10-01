# RESULT — NWPP-NEXT-12: Boardman membership repair, 2019–2025 (keeper #17)

PRECOMMIT: `PRECOMMIT-nwppnext12-boardman-membership-2019-2025-2026-09-29.md`. Zero-LP findings:
`FINDING-nwppnext12-layup-guard-and-coal-availability-2026-09-29.md`.

## 1. Solve

Seven year-isolated shards at pin `0b1d2cfe`. Every hard stop passed:
- `scenario_config` differs from keeper #16 only in `unit_outage_membership_repair`, plus new default-off fields;
- resolved inputs name the `-memberrepair-NWPP` file at sha `386a64d3`;
- P1 demand matches keeper #16 to 0.001 TWh in every year.

| year | leg commit (provenance, rule 33(d)) | vs keeper #16 |
|---|---|---|
| 2019 | 5450179e1a3750ce039eb7c4aae3613e0bdf8e25 | max \|Δ class\| 0.076 TWh; Boardman annual 1.908 (unchanged, fuel budget), Mar 15–Jul 1 now 0 |
| 2020 | 63c0d7a4a68623e356bd93c20a4420dde0876443 | COAL_PRB −0.337, CC_REGULAR +0.219, CT +0.049 TWh; Boardman 2.23 → 1.91 TWh |
| 2021 | a1080ac8ade95be59da975f8a26721045e21a866 | byte-identical (0.0 TWh, 0.0 $/MWh) |
| 2022 | 7569ec7a3ef18e4132e9a90da3d0578339ffb1b9 | byte-identical |
| 2023 | adc7a2933a985e10d43979b284d48b6a4f8385c1 | byte-identical |
| 2024 | a8d1d8ff9d0c2263e9724eb4b43141f735645e59 | byte-identical |
| 2025 | 008511829d908c6d6b91ab9bd96853f91238612e | byte-identical |

Boardman 2020, monthly mean MW, arm vs CEMS gross: Jan 518/506, Feb 214/213, Mar 167/192, Apr–Jun 0/0,
Jul 348/297, Aug 567/497, Sep 566/514, Oct 217/160, Nov–Dec 0/0. EIA-923 annual: 1.63 TWh.

## 2. Verdict (rubric v3.8), per record against keeper #16

- Determination unchanged: **NOT-YET on {dispatch_corr}**, one record, C4 coal 2023 r 0.695. Price is unscored.
- 20 of 161 records move, all in 2019–2020, and no status changes:
  - C4 gas 2019 r 0.750 → 0.735, 2020 0.830 → 0.812 (**regressions**, PASS)
  - C4 coal 2019 0.733 → 0.734, 2020 0.772 → 0.769
  - C1 COAL_PRB 2020 +1.40 → +1.28 pp; 2019 +1.94 → +1.93 pp
  - C1 CC_REGULAR 2020 +0.18 → +0.26 pp; CT_PEAKER 2019 −0.63 → −0.65 pp

## 3. Decision

Owner card: **"Promote + prune #16"**. The basis is rule 14 (a measured availability event now honoured), with zero
DOF. Keeper #17 is `2026-09-29-nwppnext12-boardman-membership`, bundle `results/calibration/nwppnext12mr_span`.
Keeper #16 was pruned with `prune_iso_runs.py --iso NWPP --force-uncite`. `audit_keepers --iso NWPP` PASS, and
`check_promotion_completeness --iso NWPP` OK. Year set before and after: 2019–2025.

Retrievability: the composed keeper bundle lands on `main` with this PR. The per-year legs were transport only; a leg
not on `main` is costed as a re-solve (~40–60 min each, ~150 min for 2019).
