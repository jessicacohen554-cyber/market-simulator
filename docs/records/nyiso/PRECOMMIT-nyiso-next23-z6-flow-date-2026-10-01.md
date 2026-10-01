# PRECOMMIT — NYISO-NEXT-23: place NYISO's Transco Z6 NY daily prints on their gas flow day — 2026-10-01

Phase 0: `docs/records/nyiso/FINDING-nyiso-next23-c3a-2025-phase0-2026-10-01.md`. Fixed before any solve.

**The arm.** The keeper's recipe (`replay_keeper.py`), plus **one** override:
`--set nyiso_gas_flow_date=true`. That is a new field, default off, with zero free parameters. It
re-dates both NYISO Z6 consumers onto the flow-date staircase (`hubs.nyiso_transco_z6_flow_daily`):
- the hub daily shape, still exactly mean-preserving per month;
- the downstate CT delivered index, with the LDC adder unchanged.

The case is rule 14 on the source convention. The EIA daily is a next-day delivery index, and Friday's
print prices the weekend package. It is not the residual: the direction of any criterion is evidence
for nothing (rule 1). This is a **first test**. nyiso-242 §4.2 refuted a *uniform* ±k-day shift that
kept the interpolation, which is not this construction; no matrix cell was ever adjudicated.

**Pin.** The `main` commit carrying this PRECOMMIT and the field (recorded in every shard prompt and in
the RESULT).

## 1. G-DRIFT (keeper `git_sha` fdc41f36 → pin)

150 solve-path files changed. Of those, **130 are comment- or docstring-only**: their AST is identical
once docstrings are stripped, mostly from the cleanup-C docs reorg. Of the 20 remaining, 11 change only
string literals: moved doc paths inside messages. The rest:

| change | class |
|---|---|
| `constants.ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR` gains `ordc_lolp_shift_sigma` (R-ERCOT-22) | INERT: read at `backcast_config.py:1353` only `if iso.upper() == "ERCOT"` |
| `cc_mustrun_conduct_window` (PJM-NEXT-17), `fleet.campd_bins.cc_conduct_profile` | INERT: default off, absent from the keeper's recipe; the only caller is gated on the flag |
| `spp_mmu_offer_unavailability` (SPP-106), `fleet/arrays.py` MMU bands, `paths.SPP_MMU_*` | INERT: default off, `iso == "SPP"` |
| `ferc714.Ferc714LambdaRespondent` (soco-97) | INERT: SOCO reported-only intake |
| `forecast_parity_registry.py`, `topscoped_encode.py`, `record_lanes.py`, `clean_profiles.py` | INERT: scoring/governance/regeneration tooling, not on the LP path |
| `reference/custom-bin-assignments.csv`, `master-plant-registry.csv` | INERT: one row, ERCOT plant 55154 (Lost Pines) |
| `_validation-source/actual_lmp.json` (NYISO key), `actual_lmp_hourly_zonal_NYISO.parquet` | INERT for the solve: NEXT-22's scoring basis, read by the scorer only |
| solve-surface rows (`moved_rows("NYISO")`: 7 names) | see §1a |

**§1a. Solve surface — MEASURED, zero moved values.** Seven NYISO rows differ from their frozen
*declarations* (main's known-red pin), but `surface_rows("NYISO")` evaluated at the keeper's SHA
(fdc41f36, git worktree) and at HEAD gives **228 = 228 rows, 0 values different**. The keeper solved on
exactly the surface the pin carries. INERT.

**All hunks INERT.** Form 4: the keeper's committed bundles (`nyisonext21_span`, `nyisonext21_2021`) are the control.

## 2. Footprint (zero LP, measured: fleet rebuilt with the flag off and on, all five years)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| gas units whose fuel price moves | 448 | 458 | 446 | 442 | 451 |
| pmax / availability / demand | identical | identical | identical | identical | identical |
| max \|Δ monthly mean\| over moved units ($/MMBtu) | 0.03 | 0.23 | 0.06 | 0.12 | 0.17 |
| max \|Δ cell\| ($/MMBtu) | 13.2 | 37.2 | 59.2 | 19.1 | 98.1 |

The monthly mean moves at all only through the CT index, which is a level, and the dual-fuel cap
applied afterwards. The hub shape is mean-preserving by construction (unit test).

## 3. Legs (rule 36: one year-isolated shard per year, all five registered years)

- 2022–2025: `python3 scripts/replay_keeper.py results/calibration/nyisonext21_span --years <y> --out-dir results/calibration/nyisonext23_<y> --set nyiso_gas_flow_date=true`
- 2021: the same from `results/calibration/nyisonext21_2021`.

## 4. Gates (arm vs the keeper's committed bundles)

- **G-1 leg acceptance** (shard hard stop + parent check). `git rev-parse HEAD` = pin. The leg's
  `scenario_config` equals the keeper's except `nyiso_gas_flow_date: true` and keys born since the
  keeper, at their dataclass default.
- **G-2 the repair is live.** In 2025 the NYC P1 mean price on Fri 2025-01-17 is **lower** than the
  keeper's. That day loses the $97.90 print it never flowed on.
- **G-3 conservation.** Per year and zone, P1 demand equals the keeper's within 0.1 GWh. P1 load-slack
  exceeds the keeper's by ≤ 1 GWh.
- **G-4 protective.** C6 and C8 PASS, every year.
- **G-5 conduct.** The arm's composed `legitimacy_diagnostics.json` has no D-4 FAIL row, keyed
  (year, mechanism, plant), that is absent from the keeper's.

## 5. Promotion rule

**Promote iff G-1 to G-5 hold in all five years.** The basis is structural (rules 1 and 14): it
corrects the calendar semantics of a measured input. If any gate fails, the run is registered
(rule 15), not promoted, and the owner is asked.

**Reported, not gating, in either direction:** C1, C2, C3a, C3b, C3c and the determination per year;
zone load-weighted prices; winter vs summer split of the C3a/C3b change. A determination downgrade in
any year goes to the owner before any promotion.

## 6. Prediction (recorded, not a gate)

- **C3b improves most in winter-heavy years (2022 first).** The daily gas factor's correlation with
  NYC DA rises in all five years in phase 0.
- **C3a 2025 moves by less than 1 pt, in either direction, and stays FAIL.** Monthly means are
  preserved, and the January cold days stay pinned at the dual-fuel oil cap (FINDING §2b, the
  successor item).
- **No change** to summer, the RT scarcity spikes or C3c.
