# RESULT — NWPP-NEXT-13: CAMPD per-unit attribution, 2019–2025 (keeper #18)

PRECOMMIT: `PRECOMMIT-nwppnext13-perunit-attribution-2019-2025-2026-09-30.md`. Zero-LP findings:
`FINDING-nwppnext13-wefor-and-perunit-phase0-2026-09-30.md`.

## 1. Solve

Seven year-isolated shards at pin `f2cfda46`. Every hard stop passed: `scenario_config` differs from keeper #17 only in
`campd_per_unit_attribution`; resolved inputs name `campd-unit-outages-perunit-NWPP.csv` (sha `ff5b0644`) and
`thermal_tranches-perunit-NWPP.csv` (sha `2c502ad8`); P1 demand matches keeper #17 exactly in every year.

| year | leg commit (provenance, rule 33(d)) | P1 Δ vs keeper #17, TWh (\|Δ\| ≥ 0.1) |
|---|---|---|
| 2019 | 1e4d57b7a11e549f0b063f78e7acefece878b63e | CC_REGULAR +0.40, CT −0.19, CC_CHP −0.16 |
| 2020 | 99e56f9310c15c2405bf34c25628a09bda3c9d61 | CC_REGULAR +0.75, CT −0.37, CC_CHP −0.19, COAL_BIT −0.13 |
| 2021 | 4662e7938316327bf4b5302f6b9f0040ea43c00a | CC_REGULAR +0.79, CT −0.36, COAL_PRB −0.34 |
| 2022 | eb9a0bb23189d2020024cb05edf15ae4809df2b1 | CC_REGULAR +0.45, CT −0.37 |
| 2023 | e4f96c37bcf362362a40f32c3c28880af0ee0a2d | CC_REGULAR +0.88, COAL_PRB −0.69, CT −0.38, COAL_BIT +0.31 |
| 2024 | 139f0cfa75b62c977eb2d2f5415c016d37dbafcd | CC_REGULAR +2.11, CT −1.19, ST_GAS −0.46, CC_CHP −0.22, COAL_BIT −0.19 |
| 2025 | 17704998b5f5aa0525dab6a3dda7e122dbafbd59 | CC_REGULAR +2.17, CT −1.39, CC_CHP −0.35, ST_GAS −0.28, COAL_BIT −0.11 |

Model load-weighted LMP (unscored) falls $1.1–3.6/MWh every year. COAL_PRB falls where Jim Bridger's take-or-pay
must-run moved from the class default to its measured share (FINDING §2.4).

## 2. Verdict (rubric v3.8), per record against keeper #17

- Determination unchanged: **NOT-YET on {dispatch_corr}**, one record. Price is unscored.
- 75 of 161 records move; **0 change status**.
- C4 (the failing criterion), r: coal 2023 **0.695 → 0.662** (NRMSE 0.283 → 0.317; the FAIL deepens);
  gas 2023 0.844 → 0.771; coal 2021 0.792 → 0.764; coal 2022 0.741 → 0.721; gas 2020 0.812 → 0.799;
  coal 2024 0.739 → 0.755 and gas 2024 0.891 → 0.898 improve. Every other C4 record moves < 0.01.
- C1 (model − actual): CC_REGULAR over-dispatch grows in 2019 (+0.93 → +1.33), 2020 (+0.97 → +1.72) and 2024
  (+4.61 → +6.72 TWh); CC_REGULAR under-dispatch shrinks in 2021–23 (−2.66 → −1.87, −4.34 → −3.89, −2.25 → −1.37);
  CT_PEAKER under-dispatch grows every year (e.g. 2024 −2.01 → −3.20); COAL_PRB 2023 +4.00 → +3.31.
- C8 forced share: 0 % in every class-year, unchanged.
- Scorer note: the bench now flags Clark CC_REGULAR as CT-only-CEMS (923 net 5.9–9.4× CAMPD gross) and scores it on
  EIA-923 monthly — the CAMPD record for Clark is its peakers.

## 3. Decision

Owner card: **"Promote + prune #17"**, on structural integrity (rule 14: available ≥ generated at Clark and
Silverhawk; measured tranche rows in place of >100 % CF rows and a missing Bridger coal row), with every regression
above reported at full magnitude. Zero new DOF.

Keeper #18 is `2026-09-30-nwppnext13-per-unit-attribution`, bundle `results/calibration/nwppnext13pu_span`. Keeper #17
was pruned with `prune_iso_runs.py --iso NWPP --force-uncite`. `audit_keepers --iso NWPP` PASS;
`check_promotion_completeness --iso NWPP` OK. Year set before and after: 2019–2025.

Retrievability: the composed keeper bundle lands on `main` with this PR. The per-year legs were transport only; a leg
not on `main` is costed as a re-solve (~35–60 min each, ~200 min for 2019).

## 4. Open, for the next lane

- **C4 coal 2023 is now further from its floor (0.662).** First suspect is the new Bridger coal tranche row: it
  pools 2023–2025 against the 2025-vintage 1,049 MW coal bin although units 1–2 burned coal in 2023, and it absorbs
  Bridger's Feb–May 2023 conservation. A zero-LP decomposition (Bridger hourly model vs CEMS, 2023) is the first step.
- CT_PEAKER under-dispatch and CC_REGULAR over-dispatch in 2024–25 both widen as Clark's CC capacity comes back.
- Lever 1 (coal WEFOR relief) is blocked on a live-capacity denominator (FINDING §1.3).
