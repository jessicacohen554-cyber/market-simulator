# PRECOMMIT — R-SOCO-B: repair SOCO's BA boundary + the 2019 interchange sign, re-solve SOCO 2019–2025

Base: `claude/r-soco-b-base` @ `b5e3b91458654b27e675594e6e15efe91df56b49` (PR #6585 R-SOCO, promoted keeper
`2026-09-24-r-soco-corrected-inputs` 2023–2025, merged with PR #6589 I-SOCO 2019–2022 inputs). Branch
`claude/r-soco-b`. Written before any shard is launched. Phase 0 is zero LP; the parent solves nothing (rule 32(a)).

Owner rulings 2026-09-25 (verbatim "Yes" to the parent's recommendations):
**(A)** repair EIA's sign-inverted SOCO 2019 `Total interchange`, never touching the raw file;
**(B)** PowerSouth (EIA BA `AEC`) joined the SOCO BA on 2021-09-01 — its plants come INTO the SOCO fleet from
that date, so supply matches the load EIA-930 measures.
A third defect of the same class, found by the parent and in scope here: the vintage LP fleet carries the former
Gulf Power plants in 2019–2023 although EIA-930's SOCO demand never included them (R-SOCO RESULT, "Found after
promotion").

## 0. Summary

- **Three repairs, zero free parameters, zero new `ScenarioConfig` fields.** Every value is the publisher's own
  record, measured here, with a citation comment at the registry.
- **Years solved: 2019, 2020, 2021, 2022, 2023, 2024, 2025**, one shard per year (rules 34(c), 36).
- **Recipe = the promoted keeper's recipe, unchanged**, replayed on the repaired code. The offer-curve bands are
  unchanged (all 1.0; SOCO has no price reference and no `authorized_price_tuning`).
- **Only SOCO moves.** Every other region's cache keys are unchanged and its fleet loaders are byte-identical (§4).

## 1. The repairs

| id | what | where | registry |
|---|---|---|---|
| R1 | Negate EIA's published SOCO `Total interchange` inside its sign-inverted window, at every raw-extract read seam, so the served schedule, the demand balance screen (`S = NG − TI`) and the hourly interchange benchmark all see EIA's own sign. The raw file is untouched. | `data/eia930/frames.py::_repair_inverted_interchange` (called by `_eia_hourly_frame_raw`, the gap-filled reconstruction, and `actuals.load_eia_hourly_benchmark`) | `constants.EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC = {"SOCO": (("2019-01-01 07:00", "2019-09-11 05:00"),)}` |
| R2 | The existing `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` partition (plants the CURRENT EIA-860 codes to another BA leave SOCO) now also applies to the LP fleet. The recode helper moved to `src` so both seams read one function (rule 19). | `data/ba_membership.py::drop_current_ba_recoded_rows`, applied in `fleet/eia860.py` at the operable loader, the within-window retiree channel and the mothball re-carry; `run_calibration_full._eia860_current_ba_recoded` is now an alias | `ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE` (value unchanged, `{"SOCO": True}`) |
| R3 | PowerSouth joins on 2021-09-01. **Fleet:** the fleet loader admits the joining BA's rows from the join year; in the join year a month mask (the COD-ramp construction, applied right after the COD ramp in `fleet.arrays`) keeps them offline Jan–Aug, with `min_gen` scaled the same way. Before 2021 nothing is admitted; after 2021 the vintages code them SOCO. **Benchmark:** `_iso_plant_ids(iso, year)` drops them before 2021 (eGRID-2023's base codes them SOCO in every year); `_eia923_frame` zeroes their Jan–Aug 2021 months and re-sums their annual. The must-run injection reads the same frame. | `data/ba_membership.py::{joining_ba_codes, ba_join_first_month}`; `fleet/eia860.py::_load_fleet_from_parquet`; `fleet/arrays.py`; `run_calibration_full._iso_plant_ids` / `_eia923_frame` | `constants.ISO_BA_JOINS = {"SOCO": {"AEC": (2021, 9)}}` |

**R3 data.** The processed `vintage_2021/eia860_generators.parquet` was filtered to modelled BAs at build time, so
it carried no `AEC` rows. They were appended by the construction the SPP rescope uses, from that vintage's own
committed operable and plant sheets, with the F1 year-matched eGRID-2021 heat-rate join:
`python3 scripts/data/process_eia860.py --rescope-from-parquet data/raw/eia-860/vintage_2021 --admit-ba AEC`.
The new `--admit-ba` appends ONLY the named BA. The result: 19,727 → 19,750 rows (+23 `AEC`), and every committed
row is frame-identical (`assert_frame_equal` on the first 19,727 rows; dtypes equal). The 23 rows are McWilliams
533 (653 MW CT/CA, HR 7.157), McIntosh 7063 (676 MW GT + the 110 MW CAES unit, HR 11.227), Gantt 53 and Point A 55
hydro (8.2 MW) and Springhill 56522 LFG (4.8 MW). Vintages 2019/2020 are not touched: nothing reads `AEC` rows
before the join year. `AEC` is NOT registered in `BA_CODE_TO_ISO`.

### 1.1 Measurements behind the registries (re-verified; the parent's numbers are reproduced or reconciled)

- **R1 window.** Local-year 2019 in `SOCO hourly.parquet` runs UTC 2019-01-01 07:00 → 2020-01-01 06:00, 8,760 rows.
  In each of the **6,071** hours from the first row through UTC 2019-09-11 05:00, `TI == −(NG − D)` within 1 MW.
  No hour there matches the correct sign alone. Two hours sit within 1 MW of zero and satisfy both signs. From
  UTC 2019-09-11 06:00 on, 2,664 of 2,689 hours satisfy `TI == NG − D` and the other 25 are NaN. *(The parent
  counted 6,066 hours. The window edges agree exactly. The hour count here is every row of the file inside the
  window.)* The nine DIBA legs agree: inside the window corr(TI, Σlegs) = −1.0000 and median |TI + Σlegs| = 0 MW
  (TI −4.114 TWh vs legs +4.114 TWh); after it median |TI − Σlegs| = 0 MW. After the repair, the served 2019
  schedule satisfies `TI = NG − D` within 1 MW in all 8,735 hours where the three are present. The **annual moves
  −1.582 → +6.645 TWh** (legs: +6.640).
- **R1 does not move demand.** The SOCO 2019 demand series is byte-identical with and without the repair, because
  the balance screen flags no hour either way. The recorded dropout stays as it is (rule 23, no new screen
  constant; the precedent is `demand.py::_load_soco_hourly_demand`): hour 7149 reads **6,913 MW**, right after
  hour 7148 at **35,329 MW**. The two are an adjacent spike/dropout pair whose mean (~21.1 GW) matches its
  neighbours (20–22 GW). It is reported, not repaired.
- **R2 set.** `current_ba_recoded_plants("SOCO")` against the vintage fleets removes Crist 641, Lansing Smith 643,
  Pea Ridge 7715, Perdido 57502 and Santa Rosa 55242 (2019–2021). Solar 63754 / 64757 / 65036 are not LP thermal
  units: SOCO solar is the delivered EIA-930 `NG: SUN` profile, already on the 930 boundary.
- **R3 plants.** The `AEC` interchange leg stops at 2021-09-01 00:00. Vintages 2019–2021 code {53, 55, 56, 533,
  6192, 7063, 56522, 64469} `AEC` (2019 lacks 64469); 2022+ code them `SOCO`. EIA-923's own `ba_code` agrees
  (AEC 2018–2021, SOCO 2022+).

## 2. Registered years (rules 34(c) / 35(b))

The registry holds one SOCO sidecar, the keeper `2026-09-24-r-soco-corrected-inputs` (2023, 2024, 2025). No run is
folded to it. **Union = {2023, 2024, 2025}.** This batch solves 2019–2025, a superset.

## 3. Phase-0 census (zero LP; `scripts/probes/_rsocob_phase0.py`, JSONs in `rsocob_phase0/`)

The keeper recipe (`rsoco_corrected_inputs_span/meta.json` → `replay_keeper.run_year_kwargs`) with
`fleet_only=True`. `pre` = this branch with the three repairs neutralised in-process (the windows / joins emptied,
the fleet recode drop an identity). That is the base-SHA behaviour: with the joins empty, the appended `AEC` rows
are filtered out by the BA code. `post` = this branch.

| year | EIA-860 | Gulf LP MW | PowerSouth LP MW / avail TWh | ST_GAS MW | CT_PEAKER MW | CC_REGULAR MW | COAL MW | served interchange TWh | EIA-923 PowerSouth TWh in the benchmark frame |
|---|---|---|---|---|---|---|---|---|---|
| 2019 | vintage_2019 | 1,826.6 → **0** | 8.2 / 0.018 → 8.2 / **0** | 3,141 | 9,362 → 9,350 | 17,503 → 16,648 | 15,074 → **14,150** | **−1.582 → +6.645** | **5.227 → 0** |
| 2020 | vintage_2020 | 1,826.6 → **0** | 8.2 / 0.018 → 8.2 / **0** | 3,141 | 9,354 → 9,342 | 17,480 → 16,624 | 15,072 → **14,148** | 4.762 | **4.898 → 0** |
| 2021 | vintage_2021 | 2,760.8 → **0** | 8.2 / 0.018 → **1,355.0 / 3.489** | 4,065 → **3,141** | 10,295 → 10,037 | 17,474 → 17,272 | 14,116 | 6.429 | **4.636 → 1.416** |
| 2022 | vintage_2022 | 2,524.9 → **0** | 1,355.0 / 9.274 (unchanged) | 4,065 → **3,141** | 10,326 → 9,379 | 17,889 → 17,269 | 11,512 | 3.923 | 4.742 (unchanged) |
| 2023 | vintage_2023 | 2,524.9 → **0** | 2,013.9 / 10.424 (unchanged) | 4,065 → **3,141** | 10,824 → 9,877 | 19,292 → 18,672 | 11,512 | 10.156 | 5.647 (unchanged) |
| 2024 | vintage_2024 | 0 | 1,882.0 (unchanged) | 3,141 | 9,646 | 18,663 | 11,512 | 10.807 | 7.626 (unchanged) |
| 2025 | canonical | 0 | 1,882.0 (unchanged) | 3,261 | 9,640 | 18,653 | 15,159 | 13.032 | 8.024 (unchanged) |

Readings:
- **Gulf.** In 2019–2020 the vintage fleet carried Crist 641 as **924 MW COAL**, Lansing Smith 643 620 MW CC
  (+32 MW non-thermal), Santa Rosa 55242 236 MW CC, Pea Ridge 12 MW and Perdido 3 MW, with 14.60 TWh of
  availability energy. In 2021–2023 Crist is 924 MW ST_GAS + 934 MW CT, the gas-converted plant. **2023: 2,524.9 MW**,
  which reproduces the parent's 2,525 MW. 2024 and 2025 are identical in every census field, pre = post.
- **PowerSouth in 2021.** 15 units, 1,355.0 MW: McWilliams 654.1 MW CC_REGULAR, McIntosh 688.0 MW CT_PEAKER,
  hydro 8.2, LFG 4.8. Availability energy by month (GWh): **0 in Jan–Aug**, then 820.1 / 886.0 / 857.4 / 925.9
  (Sep–Dec). **Class and zone attribution needs no new construction.** The rows go through the same
  `_rows_to_generators` / eGRID zone lookup as the 2022 vintage, where the same plants are coded SOCO, and the
  2021 class MW equals 2022's (654.1 / 688.0). This is why the PRECOMMIT did not stop for an attribution decision.
- **PowerSouth hydro in 2019–2020** (Gantt 53 + Point A 55, 8.2 MW) enters the LP hydro fleet through the
  keeper's inherited `hydro_backfill_year=2024`, which carries plants that reported in 2024 but not in the solve
  year. Pre-repair it held 0.018 TWh of availability. The join mask now keeps it offline in the years before the
  join, which is the same boundary rule. In Sep–Dec 2021 it is admitted, but EIA-923 books its 2021 energy under
  `AEC`, so its budget is ~0. That is ≤ 0.01 TWh and is stated here, not engineered.
- **Benchmark.** The EIA-923 membership frame loses PowerSouth's 5.227 / 4.898 TWh in 2019 / 2020 (CC_REGULAR
  −3.56 / −4.16, CT_PEAKER −0.67 / −0.38, 2019 COAL_BIT −0.95 = Lowman) and its Jan–Aug 2021 energy
  (4.636 → 1.416 TWh). 2022–2025 are unchanged. The Gulf plants were already out of the benchmark (SOCO-60), so
  the fleet now matches it.
- **Demand.** Demand-with-interchange moves only in 2019, by +8.228 TWh (236.869 → 245.097), which is R1. Every
  other year is identical.

## 4. Proof that only SOCO moves

- **Cache keys** (`ScenarioConfig(iso=X, mode=backcast|forecast).cache_key()`, base `b5e3b914` vs this branch):
  ERCOT, CAISO, MISO, PJM, NYISO, NEISO, SPP and NWPP are all **identical**. SOCO moves (backcast
  `da3db329c35ce465` → `4aa2a934b68eaf00`).
- **Solve surface** (`solve_surface_register.py --diff b5e3b914`): 310 → 312 names, **0 values moved**. The two new
  tables are declared at their inert SOCO values (`()` / `{}`), so their live rows sit off the declaration **for
  SOCO only** (`moved_rows`). Every other ISO's `moved_rows` is unchanged. This is the soco60b precedent.
- **Fleet loaders on the data change** (`load_fleet_from_csv(X, vintage_2021, year=2021)` with and without the 23
  `AEC` rows, all measured heat-rate flags on): ERCOT 1,116, CAISO 804, MISO 2,017, PJM 2,124, NYISO 510,
  NEISO 452, SPP 988 and NWPP 448 generators, **hash-identical** each. SOCO 386 → 404.
- **Code paths.** Every helper returns its input (the same object) for a region neither registry names:
  `drop_current_ba_recoded_rows`, `_repair_inverted_interchange`, `joining_ba_codes`, `ba_join_first_month`. The
  arrays block and the `_eia923_frame` gate are no-ops on an empty map. This is pinned by
  `tests/unit/data/test_ba_membership.py` and `test_eia930_interchange_sign_window.py`.
- **Tests.** 432 passed across the fleet, COD-ramp, demand, balance-screen, membership, solve-surface, F1-default
  and vintage-keying files, including the two new files. `check_cache_key_registration.py`: ok (312 surface names,
  all declared). `test_persisted_identity.py::test_solve_surface_fingerprint_is_pinned` fails for all six pinned
  ISOs **at the base SHA too, with digests identical to this branch**. That is pre-existing (pjm-h22's
  `RGGI_MEMBER_STATES_BY_YEAR` rows, see the R-SOCO RESULT) and not this lane's move.

## 5. G-DRIFT (rule 29(b)) — keeper legs `455e0021` vs the base `b5e3b914`

`git diff 455e0021 b5e3b914 -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference`: 15 files. Every hunk was already classified in the R-SOCO RESULT
addenda:

| hunk | class for SOCO |
|---|---|
| R-NEISO `fleet/arrays.py`, `fleet/eia860.py`, `outages.py` (`coal_scope`, `_mid_vintage_exit_rows_from_window`) | INERT: both gas and coal scopes are armed (byte-identical call), and `mid_vintage_exit_carry` is False |
| R-ERCOT `fleet/campd_bins.py`, `run_calibration.py` threading, `scripts/lib/key_provenance.py` | INERT: `use_campd_bins and iso == "ERCOT"` only, plus provenance tooling |
| `results/cache.py` | prose |
| I-SOCO `calibration_reference.json` SOCO blocks + `SOCO_2019…2022_renewable_capacity.csv` | 2023–2025 blocks byte-identical (I-SOCO §2); the 2019–2022 blocks are the new years' own scoring references (LIVE for those years only, with no control) |
| NWPP renewable-capacity CSVs / NWPP reference rows | INERT (another region) |
| I-SOCO data outside the audited paths (hourly extract, FERC-714, interchange, gas, hub, solar shape) | every 2023–2025 row byte-identical (I-SOCO §2) |

On top of that base, this lane's own hunks are **R1** (inert for 2020–2025 by window), **R2** (LIVE in 2019–2023,
inert in 2024/2025 per the census) and **R3** (LIVE in 2019–2021, inert in 2022–2025 per the census). **So the
2024 and 2025 legs must reproduce the keeper's legs.** That is E2 below, and it is the audit's own test.

## 6. The recipe (the solve)

One shard per year (rule 36), replaying the committed keeper composite on this PRECOMMIT's pinned SHA:

```
uv sync
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. uv run python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. uv run python scripts/data/curate_demand_profile.py
uv run python scripts/replay_keeper.py results/calibration/rsoco_corrected_inputs_span --years <Y> \
  --out-dir results/calibration/rsocob_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true \
  --note "R-SOCO-B <Y>: R-SOCO keeper recipe on the repaired SOCO BA boundary (R1 2019 interchange sign, R2 Gulf plants out of the LP fleet, R3 PowerSouth AEC from 2021-09-01); multipliers unchanged"
```

These are the same five `--set` flags the keeper's meta records (R-SOCO PRECOMMIT §5). Inherited unchanged from
the keeper: `measured_{ct,coal,st,cc}_heat_rates`, `egrid_family_heat_rates`, `campd_dark_unit_year_windows`,
`gas_basis_differential_measured_by_year`, `hydro_eia930_monthly`, `hydro_backfill_year=2024`, and every
`offer_curve_by_group` band at 1.0.

**Per-leg hard stops:** `git rev-parse HEAD` equals the pinned SHA. `run_config.json`'s `scenario_config` shows
the five `--set` fields and the inherited measured / dark-unit fields True. `solve_surface.moved` names
`EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC` and `ISO_BA_JOINS`. Every band is 1.0. `environment.packages`
equals the keeper's (`highspy 1.14.0, numpy 2.4.6, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, scipy
1.17.1`). `dispatch/<Y>_P1.parquet` is present.

**Parent seam (rule 32(d)):** fetch and verify each leg (config signature; the pinned SHA; the repairs visible:
Gulf units absent from `dispatch/<Y>_P1_fleet.parquet` in 2019–2023; PowerSouth units present in 2021 and zero in
Jan–Aug; 2019 demand-with-interchange = 245.097 TWh). Compose seven legs with
`scripts/probes/rsocob_compose_span.py`, then re-span the shared benchmark frames, run
`legitimacy_diagnostics.py`, `build_dof_ledger.py --iso SOCO`, `gen_soco60b_attestation.py
--declared-inert-moved RGGI_MEMBER_STATES_BY_YEAR` (the two new names are LIVE, not inert: they are this lane's
declared delta and are attested by `gen_rsoco_attestation.py`), `gen_rsoco_attestation.py`, and
`dashboard_add_run.py --no-prune`.

## 7. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1 (2023, R2).** Removing 2,525 MW of Gulf capacity (ST_GAS −924, CT −946, CC −620 MW) from a run that
  over-produced CT_PEAKER (+2.13 pp) and under-produced ST_GAS (−2.12 pp): CT_PEAKER energy falls, ST_GAS energy
  falls or holds, and the remaining CC_REGULAR / coal fill it. 2023 unserved may rise from 0.
- **E2 (2024, 2025).** These legs reproduce the keeper's committed legs. The bar is |Δ class TWh| ≤ 0.01 on every
  class and identical unserved MWh (rule 36 year isolation, replay determinism env). A larger move falsifies the
  G-DRIFT of §5 and is reported as a finding, not absorbed.
- **E3 (2019, R1).** SOCO must serve +8.228 TWh more than an unrepaired 2019 would. In-region generation is
  ≈ demand + 6.645 TWh net export.
- **E4 (2021, R3).** PowerSouth units dispatch 0 MWh in Jan–Aug and a positive total in Sep–Dec.
- **E5.** C3a/b/c stay UNSCORABLE in every year (no SOCO price). C6 PASS.

## 8. Promotion recommendation rule (fixed now)

This is an owner-ruled input/boundary correction plus a year-span extension. The re-solve is recommended as the
SOCO keeper **iff all seven legs solve cleanly with the posture verified and the three repairs visibly active
(§6), and E2 holds (or its deviation is fully explained by an identified code path)**, **whatever the C1–C8 gates
do** in 2019–2023. Rule 14: a gate regression after correcting the boundary is a root-cause lead, never a reason
to keep the wrong boundary. Every gate move is reported at full magnitude. The owner decides (rule 31). If
promoted, rule 35 prunes `2026-09-24-r-soco-corrected-inputs`. The incoming run covers the union
{2023, 2024, 2025} and adds 2019–2022.

## 9. Routed, not done here

- The 2019 hour-7148/7149 demand spike/dropout pair: recorded (§1.1), not repaired (rule 23 posture).
- PowerSouth's 2021 hydro budget is booked under `AEC` in EIA-923 (≤ 0.01 TWh; §3).
- The EPA↔EIA facility-ID crosswalk (Dahlberg / Hartwell) remains routed, from R-SOCO §5.
- `test_persisted_identity` surface pins: pre-existing (§4), for the lane that moved `RGGI_MEMBER_STATES_BY_YEAR`.

## Addendum — rebase onto `main` @ `6edbeb61` (G-DRIFT, rule 29(b))

The lane was rebased onto `main` after #6585 (R-SOCO) and #6589 (I-SOCO) merged there under rebased SHAs. The
seven legs were solved at the pinned `f2a5412e` (base `b5e3b914`); that pin stays as their provenance. Between
`b5e3b914` and `6edbeb61`, `git diff` over the §5 paths touches 14 files, and every hunk is INERT for SOCO:

| hunk | reason |
|---|---|
| i-caiso `data/eia930/caiso_hydro_backfill.py` + `frames._repair_measured_gaps` | `MEASURED_GAP_SOURCES` registers `CISO` only; returns the frame object unchanged for `SOCO`. The one rebase conflict: both helpers kept side by side, and each read seam applies R1 first and the gap repair last, as before. |
| `constants.NUCLEAR_MONTHLY_CF_BY_YEAR` (CAISO 2019–21), `fuel_trajectories` (CAISO / PJM carbon rows), `capacity_market` (PJM RGGI), `interchange/spec.py` (MISO / PJM seam ladders) | other regions' rows; `solve_surface_register.py --diff b5e3b914 origin/main` moves only `RGGI_MEMBER_STATES_BY_YEAR` for SOCO, already declared inert (no SOCO state is a RGGI member) |
| `scenarios.py` `COAL_SIGMOID_DEFAULTS` (MISO rows) | MISO only |
| `run_calibration.py` fleet_only return gains `iso_config` | the `fleet_only` exit only; never reached by a solve |
| `paths.CAISO_OUTLOOK_FUELSOURCE_DIR`; `_validation-source` CAISO / MISO LMP files | CAISO / MISO only |

No re-solve is owed. The legs stand at the rebased head.
