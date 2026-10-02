# RESULT — closeout PJM renewables fix (2026-10-02, zero LP)

Lane `closeout-PJM-renewables-fix`, chartered by the Backcast close-out desk.
Base `origin/main` @ `306f2c00b6268b791fb77c392c8d69a756959e76`. No LP, no
solve, no tuned value.

## Defect (from W0, confirmed here)

`data.renewables._eia860_monthly_capacity` admitted a wind/solar plant only if
`zone_assignment.build_zone_lookup` had it: eGRID 2023, plus the canonical
EIA-860 plant file for the ISOs in `_EIA860_SUPPLEMENT_ISOS`. PJM is not in that
set, so PJM-BA solar/wind that eGRID 2023 lacks was dropped. The census is W0's
`renewable_membership_306f2c00.json` (probe `scripts/probes/_w0_renewable_membership.py`
on `claude/closeout-b-w0-phase3` @ `e5cd736e`) and census 0a of
`FINDING-pjm-closeout-wave1-censuses-2026-10-02.md`.

## Fix

This is the thermal fleet's fallback, applied under the existing flag. Rule 19:
no new field and no new mechanism.

- `renewables._renewable_zone_lookup(iso, data_dir)` returns `build_zone_lookup(iso)`.
  When `fleet_zone_vintage_coords` is armed, it also adds via `setdefault` every
  plant from `zone_assignment.vintage_coords_zone_lookup(iso, data_dir)`, which
  zones plants from the coordinates in the plant file of the EIA-860 directory
  being read. A plant that is already zoned is never re-zoned. With the flag
  off, the lookup is unchanged.
- The three readers of the old lookup now share this helper, so they keep one
  membership:
  - `_eia860_monthly_capacity`
  - `wind_ptc_eligible_monthly_share`, whose docstring promises "the exact
    fleet the capacity loader distributes"
  - `_eia860_zone_solar_geometry`, which is CAISO-only in practice
- `vintage_coords_zone_lookup` gains an optional `eia860_dir`. Omitted, it
  reads the active vintage, so the thermal call site is unchanged.

## Before / after membership (`renewable_membership_fix.json`)

Probe: `scripts/probes/_pjm_renewable_membership_fix.py`. It reads each year's
`vintage_<Y>` directory, which is what a solve under
`eia860_vintage_tracks_solve_year` reads, through the loader's own helper with
the flag off and armed. The "off" column reproduces W0 exactly.

| PJM | fuel | BA footprint MW | missed off (plants) | missed armed | loader Dec MW off -> armed |
|---|---|---:|---:|---:|---:|
| 2019 | solar | 3,315.9 | 5.0 (4) | 0.0 | 3,310.9 -> 3,315.9 |
| 2020 | solar | 4,556.8 | 7.0 (5) | 0.0 | 4,549.8 -> 4,556.8 |
| 2021 | solar | 6,453.5 | 4.0 (3) | 0.0 | 6,449.5 -> 6,453.5 |
| 2022 | solar | 7,411.6 | 1.3 (1) | 0.0 | 7,410.3 -> 7,411.6 |
| 2023 | solar | 10,991.0 | 0.0 | 0.0 | 10,991.0 (identical) |
| 2024 | solar | 14,791.3 | 3,737.5 (129) | 0.0 | 11,053.8 -> 14,791.3 |
| 2025 | solar | 18,048.8 | 6,986.0 (349) | 0.0 | 11,062.8 -> 18,048.8 |
| 2019–2023 | wind | — | 0.0 | 0.0 | identical |
| 2024 | wind | 11,459.6 | 189.0 (1) | 0.0 | 11,270.6 -> 11,459.6 |
| 2025 | wind | 11,727.9 | 447.9 (3) | 0.0 | 11,280.0 -> 11,727.9 |

The armed lookup admits no MW outside the PJM BA in any year. The vintage lookup
filters on the BA code.

Zonal destination of the added year-end MW:

- 2025 solar: AEP_Ohio +3,169.1, Dominion +1,671.3, ATSI +509.4,
  West_APS +508.0, Central_PA +337.0, ComEd +330.3, SWMAAC +310.7,
  EMAAC +150.2.
- 2025 wind: ComEd +204.0 (Top Hat), Dominion +189.0 (Timbermill),
  West_APS +54.9 (Dans Mountain).

The other ISOs only change if they arm the flag, and no committed recipe does.
In every ISO-year the armed missed MW is 0.0, except SOCO 2023–25 at 0.5 MW:
plant 67241, the Massachusetts BA mis-entry, which is rejected by design.

## NYISO inertness (zero LP)

NYISO is the only other ISO that arms the flag (keeper `nyisonext26p_span` /
`_2021`). For every vintage 2019–2025, all four loader outputs are byte-identical
with the flag off and armed (sha256 digests in the JSON, `loader_outputs_identical:
true`):

- monthly wind
- monthly solar
- PTC share
- solar geometry

The reason: NYISO is in `_EIA860_SUPPLEMENT_ISOS`, and the canonical supplement
already admits every NYISO-BA plant.

## Cache key / solve surface

This is a code change. No `ScenarioConfig` field moves and no registry value in
`SURFACE_MODULES` moves, so no key moves for any ISO. That includes PJM: the PJM
solve surface does **not** re-key by itself. The change is recorded as a
same-key invalidation in the `results/cache.py` ledger (Epoch 2026-10-02), as
**prose only**, following the R-ERCOT 2026-09-24 precedent.

A `SolveEpoch` cannot be scoped to a flag state. Using `isos=("PJM",)` would
re-key every flag-off PJM bundle too, and the change does not invalidate those.

- Invalidated: PJM bundles with the flag armed. The committed one is
  `pjmnext16_A_span`, all years. Keeper bundles are files, not cache lookups,
  so the PJM lane owes a re-solve.
- Not invalidated: NYISO (proven byte-identical above) and every flag-off
  config.

If the desk wants a mechanical re-key, the change is one line appended to
`SOLVE_EPOCHS` with `isos=("PJM",)`.

## What it moves in a PJM backcast

Under `mode == "backcast"`, installed MW is the year-end sum of the monthly
array. The hourly profile for PJM is the delivered EIA-930 series normalised per
MW online (`_eia_hourly_cf_profile`). As read from the code, then:

- System renewable energy stays pinned to EIA-930.
- Installed MW rises, so per-MW CF falls.
- The zonal split of that energy follows the added plants.
- Capacity-side consumers (accreditation, capacity screens) see the measured
  fleet.

Measuring the LP effect is the PJM lane's job.

## Matrix

- Row `fleet_zone_vintage_coords`: one sentence added to its `def`, naming the
  renewables consumer.
- PJM shard: a note appended to the cell. The `K` verdict is unchanged and no
  solve was run.
- No other shard was edited.
