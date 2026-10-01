# RESULT — SPP-98: CEMS→EIA split-plant remap for SPP (Stall ← Arsenal Hill). The benchmark is corrected and dispatch is byte-identical.

**Lane** SPP-98 (owner decision card "Crosswalk repair (Rec.)") · control = keeper `2026-09-28-spp-94-curtail-rows`
(`spp94_arm_span`, rule 29(b) form 4) · PRECOMMIT `docs/records/spp/PRECOMMIT-spp-98-cems-eia-remap-2026-09-28.md`, merged
at `ed8cec3fd0811ebf835cfec42184493683c2625a` before any shard launched · registered run
**`2026-09-28-spp-98-cems-remap`**, bundle `results/calibration/spp98_remap_span` (2019–2025).

## 1. What changed

Ten rows were added to `market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP` (rule 19: the existing mechanism, with the
CAISO/NYISO precedents). Every row comes from the EPA CAMD–EIA crosswalk, and every target plant is an SPP fleet member.
The material pair is J Lamar Stall (EIA 56565, 511 MW CC), whose two CTs file under Arsenal Hill's ORIS 1416.

The keeper was then replayed one year per shard (rule 36) to recover the gitignored dispatch/system artifacts. The seven
legs were composed, and `rebuild_benchmark` adopted the corrected benchmark. The parent solved nothing.

| year | leg SHA (provenance only) | shard check | identity vs keeper |
|---|---|---|---|
| 2019 | `0f246b019c803581efb1e21d44e64fff91c66ba7` | PASS | 0.0000 TWh / $0.000000 |
| 2020 | `eac5ea4377e9afef6a00a015dadbbd9abd6098cb` | PASS | 0.0000 / 0.000000 |
| 2021 | `a1009a679bbf08d5abf446e1a899849f58be56ce` | PASS | 0.0000 / 0.000000 |
| 2022 | `d92d2c0e8bd48b0a8d09013c2ed1e4a2fc79159c` | PASS | 0.0000 / 0.000000 |
| 2023 | `d8feeecdcb92a4efaacc4acd78ba33a5675c1222` | PASS | 0.0000 / 0.000000 |
| 2024 | `bbf518a8c049b7edca8860ac00b3a649bdd3e3d4` | PASS | 0.0000 / 0.000000 |
| 2025 | `232b6e8e2d37a7417934d3f88751e98291209ddd` | PASS | 0.0000 / 0.000000 |

## 2. Expectations (PRECOMMIT §4)

| # | result | holds? |
|---|---|---|
| X1 | Arsenal Hill 1416 CEMS 1.69–2.46 → 0.03–0.20 TWh (unit 5A only). Stall 56565 gains 1.62–2.28 TWh and is flagged CT-only (923 / CEMS 1.47–1.55×), so it is scored on EIA-923 monthly | yes |
| X2 | C1 ST_GAS actual −2.237 / −1.864 / −2.204 TWh in 2020 / 2021 / 2025; 0 in the other years | yes |
| X3 | CC_REGULAR actual unchanged in 2019–2024. In 2025 it rises +0.63 TWh through the scorer's fossil reconcile scale, which redistributes the removed ST_GAS across the classes; this is the scorer's own normalization, not an attribution change | yes (2019–24); 2025 moved by the reconcile, reported |
| X4 | dispatch and prices byte-identical in all 7 years; D-4 FAIL rows identical (8/8) | yes |
| X5 | none of the 8 codes is in any other ISO's benchmark membership (9 ISOs × 2019–25) | yes |

**Rule §5 → ADOPT.**

## 3. Scored effect, at full magnitude. No row flips status.

| C1 row | before | after |
|---|---|---|
| 2020 ST_GAS | −6.56 TWh (PASS) | **−4.32 TWh** (PASS) |
| 2021 ST_GAS | −5.00 TWh (PASS) | **−3.13 TWh** (PASS) |
| 2025 ST_GAS (C1 skipped that year) | −10.12 | −8.03 |

- **Train 2023–25:** CALIBRATED (lone ledgered C3c), unchanged.
- **Validation 2019–22:** NOT-YET, with the same failing rows:
  - C1 CC/coal 2021–22;
  - C3a 2019 +11.5 % and 2020 +27.8 %;
  - C3b 2020 0.348.

The dashboard's CAMPD view no longer shows Arsenal Hill ST_GAS at up to 225 % CF.

**Open, reported.** Plant 55655 (WFEC GenCo) now carries a CEMS series but has no EIA-860 nameplate in the solve
vintages. Its per-plant hourly chart falls back to npl = 1 MW; annual gates are unaffected. Arsenal Hill's contaminated
tranche row, Stall's outage windows and the WFEC nameplate are the named successor, a re-derive under the new rows
(solve-affecting). Stall's CC heat rate stays eGRID, because its CEMS is CT-only.

## 4. Retrievability (rule 34(e))

The composite `results/calibration/spp98_remap_span` (committable set), its sidecar, its run payload and the corrected
`_shared/SPP` benchmark frames land on `main` with this lane's PR. Promotion costs **zero re-solves**. The per-year legs
are gitignored in the parent, and the SHAs above are provenance only.

**Year set (rule 35(b)):** SPP's registered years are 2019–2025, on `spp-94` only. `spp-98` covers all seven.
