# RESULT — NWPP-NEXT-3: the plant-basis demand anchor (framing 2), 2019–2025 → KEEPER #10

**Run:** `2026-09-25-nwppnext3-plant-basis`, bundle `results/calibration/nwppnext3_span`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-nwppnext3-plant-basis-2019-2025-2026-09-25.md`.
**Control:** keeper #9 `2026-09-25-nwppnext2h-cascade-2019`, committed bundle (G-DRIFT form 4, PRECOMMIT §4).
**Solved by:** seven year-isolated shards at pin `dad798cd` (rule 36). The parent session ran no LP.
**Status: PROMOTED** to NWPP keeper #10 on the owner's standing ruling: structure improves and no criterion
regresses. Keeper #9 was pruned (rule 35); `audit_keepers --iso NWPP` PASSES.

## 1. Determination

- **NOT-YET on {dispatch_corr} only.** The keeper read NOT-YET on {fuelmix, dispatch_corr}.
- C1, C2, C6 and C8 PASS. Price is UNSCORED (rubric v3.8).
- No criterion moves from PASS to FAIL in any year.

| Year | C1 CC_REGULAR (TWh vs bench): keeper → arm | C4 coal r: keeper → arm | C4 gas r: keeper → arm |
|---|---|---|---|
| 2019 | +0.40 → +3.16 | 0.765 → 0.759 | 0.762 → 0.759 |
| 2020 | +2.46 → +6.84 | **0.691 FAIL → 0.718 PASS** | 0.846 → 0.864 |
| 2021 | −6.63 → −2.38 | 0.740 → 0.747 | 0.840 → 0.850 |
| 2022 | **−11.23 FAIL → −7.36 PASS** | 0.772 → 0.769 | 0.863 → 0.885 |
| 2023 | **−8.32 FAIL → −2.57 PASS** | 0.671 → 0.683 (FAIL) | 0.833 → 0.854 |
| 2024 | −2.57 → +3.90 | 0.622 → 0.617 (FAIL) | 0.889 → 0.891 |
| 2025 | −0.92 → +5.79 (C1 skipped, preliminary vintage) | 0.687 → 0.689 (FAIL) | 0.860 → 0.866 |

**Every hard stop passed in every leg.**
- Flags and offer sha `6a13731e…` as specified.
- `hydro_backfill_year` null for 2019–2022 and 2024 for 2023–2025.
- P1 demand equals the PRECOMMIT's zero-LP arm demand to 0.001 TWh in all seven years. This proves the arm is live.

## 2. Costs, reported at full magnitude

**Unserved load (P1 slack, GWh) rises in every year:**

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| keeper | 22.5 | 113.3 | 72.8 | 40.7 | 5.7 | 12.8 | 0.2 |
| arm | 33.4 | 193.7 | 110.1 | 73.4 | 21.3 | 45.7 | 8.8 |

The added requirement peaks at +0.7 to +4.3 GW in the hourly max. Shed concentrates in SNV (2024: 31.5 of 45.7 GWh).
Existing tight hours get tighter. That points at zonal import capability or SNV capacity, not at the anchor.

**The gas family flips from short to long in 2020, 2024 and 2025:**
- CC_REGULAR reads +6.84 (2020), +3.90 (2024) and +5.79 (2025).
- CT_PEAKER reads +3.95 in 2025.
- All are inside C1's bands. 2025 is skipped as a preliminary vintage.

**Coal stays long in 2021–2023** (COAL_BIT + COAL_PRB about +7.7 / +13.5 / +9.3 TWh). The anchor raises the total
requirement. It does not change merit order, so coal-versus-gas displacement is a separate defect and is not
absorbed here.

## 3. What the anchor is, and the rule-13 proximity

- It is one default-off field, `nwpp_demand_plant_basis`, NWPP only, with zero free parameters.
- Per EIA-930 fuel family it moves the served requirement's annual energy onto the grid-delivered EIA-923 plant
  total (`data/raw/reference/nwpp_plant_basis_energy.csv`, derived from the committed bench parts), on the family's
  own EIA-930 hourly shape.
- Wind and solar are untouched. On the preliminary 2025 vintage only coal and gas are anchored.
- Total generation therefore lands near the benchmark total **by construction**. The C1 pass is **not** evidence of
  skill on the total; it is the removal of a basis mismatch the owner ruled should be removed.
- The class, zonal and hourly split remain the LP's, and the class rows (CC_REGULAR, coal) are where skill is still
  measured.

## 4. Retrievability (rule 34(e))

- The keeper's slim bundle (JSON plus `hourly/`), its registry sidecar and its run payload land on `main` with this
  lane's PR.
- The per-year legs, including `dispatch/`, are gitignored on local disk.
- Leg SHAs are provenance only (rule 33(d)): 2019 `296c691d`, 2020 `65a76ba1`, 2021 `012d64e4`, 2022 `49cdb456`,
  2023 `7714f2fd`, 2024 `361ffa45`, 2025 `73efc3f4`.
- All eight shard sessions are archived; the first 2020 shard never started and was relaunched.
- **Leftover shard branches for the owner to delete** (a session cannot delete refs, rule 33(f)):
  `claude/nwppnext3-{2019..2025}`.

## 5. What is next (lever queue, §5.9)

1. **C4 coal amplitude, 2023–2025.** This is now the only failing criterion. Model coal intra-day swing is about
   0.2× actual. Start with a unit-level ramp and commitment census against CAMPD for Bridger, Huntington and Hunter
   (FINDING-nwpp-48).
2. **Standby (SB) unit admission.** Fredonia and Sun Peak are 598 MW of CT the benchmark counts. This is now
   relevant to the SNV shed as well.
3. **SNV unserved load** under the higher requirement: diagnose import limits versus capacity (zero LP first).
