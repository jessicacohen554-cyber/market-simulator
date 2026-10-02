# RESULT: closeout W0 denominator fix (desk ruling D-1), 2026-10-02

Lane `closeout-W0-denominator-fix`, chartered by the Backcast close-out desk. **Zero LP.** Base `origin/main`
eec4eb5c. Evidence for this note is in `W0-denominator-fix/`.

## 1. Defect

With `unit_outage_dispatched_bin_denominator` on (the W0 backcast default), the unit-outage derate denominator
of a `(plant_code, plant_group)` bin is the LP roster's `pmax` sum. That roster includes exit cohorts which
`partial_plant_exit_carry` or `mid_vintage_exit_carry` carries for only part of the year. The COD ramp takes
such a cohort offline after its EIA-860 retirement month, but its `pmax` stayed in the denominator for the
whole year. Each later month's measured derate on the survivors was therefore divided by capacity the LP no
longer carried. The PR #7043 SOCO attribution found the case: Scherer 6257 in 2022, where unit 4 (891 MW) retired
2022-01. Neither field causes this alone; it is the interaction of the two.

## 2. Fix (no new field; rule 19)

- `outages.lp_bin_capacity_index(..., exit_year=)`. For every bin that holds an exit cohort with
  `ret_year == exit_year` and `ret_month < 12`, the roster also carries
  `((plant_code, plant_group, "monthly"), (12 MW))`, the capacity online in each month.
  - The full-year entry is unchanged. It equals the January value exactly.
  - A bin with no in-year partial exit gets no monthly entry, so its roster is byte-identical.
- `outages._dispatched_denominator_hourly` maps that entry to hours on the COD ramp's month grain
  (`fleet.models._hour_to_month_index`).
  - CHP groups are excepted, as in `_dispatched_denominator`.
  - A month whose roster is 0 (the whole bin retired, e.g. Wansley 6052) keeps the full-year value. The LP
    carries nothing there, and this avoids dividing by zero.
- `_unit_outage_factors_from_events` (std / short / partial / lay-up) and `unit_outage_maxgen_derate_factors`
  divide such a bin hour by hour.
  - The per-unit-clip path is covered.
  - Dated routing (`exit_cohort_repair`, PJM-NEXT-8) is left alone, because it already gives the cohort and the
    survivors their own denominators.
- `outages.dispatched_bin_exit_year(config, year)` gates the change. It returns the year only when the companion
  is on, `mode == "backcast"` and `cod_ramp_enabled`, which is exactly when the LP masks the cohort. Outside
  those conditions the cohort is carried all year, its full-year `pmax` is the right denominator, and the roster
  is the incumbent one.
- Threaded at every roster site the companion reaches: `fleet/arrays.py` (the overlay roster and the mustrun
  lay-up roster), `fleet/floors.py` (drag lay-up) and `scripts/run_calibration.py` (reliability-floor lay-up).
  - The miso-273 screened-coal share still reads the full-year scalar. It is a scalar per bin, and the charter
    scopes it out.

**Zero free parameters.** The months come from each cohort's own stamped EIA-860 retirement month.

**Out of scope.** These belong to other mechanisms:
- cohorts retired before the solve year, which is the default-off live sub-gate's job (NWPP-NEXT-15);
- fractional in-year COD ramps of new builds.

## 3. Scherer 6257, 2022 (soco96 recipe at W0 posture, zero LP)

`probe_scherer_2022.py`. "Units 1–3" are the non-cohort rows (2,580 MW). The unit-4 cohort is 860 MW of LP pmax.

| Posture | Units 1–3 Jan | Units 1–3 Feb–Dec | Units 1–3 year | Scherer available TWh |
|---|---|---|---|---|
| W0, before fix | 0.7882 | **0.6161** | 0.6307 | **14.759** |
| W0, after fix | 0.7882 | **0.5189** | 0.5418 | **12.750** |
| W0 without the cohort (`partial_plant_exit_carry` off) | 0.7593 | 0.5189 | 0.5394 | 12.190 |
| W0 with the companion off | 0.7593 | 0.5189 | 0.5394 | 12.676 |

**Feb–Dec after the fix equals the no-cohort build bit for bit** (0.5189360962149309). January includes the
cohort (300 MW out of 3,440 MW). The fix removes −2.009 TWh of the +2.49 TWh the attribution found. What remains
(+0.56 TWh against the no-cohort build) is unit 4's own January energy plus the January dilution, both of which
are correct. For reference, EIA-923 2022 coal output at Scherer is 7.29 TWh.

## 4. Byte-inertness and scope (zero LP, before = `origin/main` eec4eb5c, after = this branch)

`probe_inert_sweep.py` → `inert_sweep.json`. Each build is the keeper recipe at W0 posture. It hashes
`availability`, `pmax`, `pmin` and `min_gen`. PJM runs with `pjm_da_virtual_bids` off, because its input is not
in this checkout and it sits downstream of the fleet.

| ISO (bundle) | Byte-identical years | Moved years (Δ available energy, TWh) |
|---|---|---|
| NEISO (`neiso119_span`) | **2019–2025, all seven** (2019 has no in-year exit; the others have monthly bins that no outage row reaches) | none |
| NWPP (`nwppnext16c_span`) | 2019, 2021–2025 | 2020: Colstrip 6076 COAL −0.199 |
| SOCO (`soco96_span`) | 2019–2021, 2023–2025 | 2022: Scherer 6257 COAL −2.009 |
| PJM (`pjmnext16_A_span`) | 2021–2025 | 2019: 3149 COAL −0.0003; 2020: 2866 COAL −0.096 |
| MISO (`miso280_span`) | 2019, 2022, 2025 | 2020: 976 −0.033; 2021: 6085 −0.347, 994 −0.196; 2023: 994 −0.152; 2024: 4041 −0.757, 8056 ST_GAS −0.507, 992 −0.001 |

- **Every ISO-year with no in-year partial exit cohort is byte-identical**: NEISO 2019, NWPP 2019/2021/2025,
  SOCO 2020/2024/2025.
- In every moved year, `rowdiff.txt` checks each changed availability row. Each one belongs to a bin with a
  monthly entry, and changes only from that bin's first short month on. No January hour moved.
- MISO 2021 and 2023 also move `min_gen` on three MISO-Indiana coal rows outside those bins:
  - 2021: −1.29 GWh in total;
  - 2023: −0.04 GWh in total.
  - These rows are in the same zone as the moved 994 and 6085 bins. The change is the zonal floor allocation
    following the moved availability, which is second order.
- Every move lowers available energy, as expected: the fix only ever shrinks a denominator.

## 5. Cache key

Epoch **2026-10-02c** is the first `solve_surface.SolveEpoch`.
- Scope: `modes=("backcast",)`, `isos=("MISO", "NEISO", "NWPP", "PJM", "SOCO")`, the ISOs where the companion is
  live (W0 RESULT §4).
- It is ledgered in `results/cache.py`.
- NEISO is re-keyed conservatively, although its keeper recipe is byte-identical.
- The default (ERCOT forecast) key is unmoved.

## 6. Matrix and tests

- **Matrix.** A citation is appended to the `unit_outage_dispatched_bin_denominator` row note in
  `docs/codebase-site/data/mechanism-matrix.js`. No verdict changes.
- **Tests.** `tests/unit/data/test_unit_outage_dispatched_bin_exit_year.py` (20) covers the trivial case first:
  one plant with survivors A (600 MW) and an exit cohort B (400 MW) that leaves after January.
  - A's Feb–Dec derate is unchanged from the no-B case, with and without per-unit clip.
  - January includes B.
  - MW removed equals MW out in every hour.
  - Roster byte-identity without an in-year partial exit: December, prior-year and later-year cohorts.
  - CHP exclusion, the whole-bin cohort, and the accessor gates.
- **Solve-surface tests.** Updated for the first declared epoch.
