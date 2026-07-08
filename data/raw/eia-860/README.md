# eia-860 — raw

EIA Form 860 annual fleet-registry release, several vintages:

- Top level: `eia860_*.parquet` (generators, plant, owner, utility,
  energy-storage {operable,proposed,retired_and_canceled},
  multifuel {operable,proposed,retired}, solar/wind {operable,retired},
  environmental association/equipment schedules) — the current (2025 Early
  Release) snapshot.
- `vintage_2018/`, `vintage_2019/`, `vintage_2020/`, `vintage_2021/`,
  `vintage_2022/`, `vintage_2023/`, `vintage_2024/` — the same schema at an
  earlier EIA-860 release vintage, used for forecast-validation hindcasts
  that need the fleet as it was known at a past point in time (see
  `docs/hindcast-reports/`). 2018/2019/2021/2022 landed 2026-07-08 (data
  register intake, `docs/data-register-2026-07.md`) to close the pre-2020
  vintage gap; no 2026 vintage exists yet (EIA has not published the
  calendar-2025 annual release).

**Source:** EIA Form 860 (`eia8602024.zip`, `eia860<year>.zip` archive
releases), public domain — see `docs/data-licensing.md` §1.

**Regeneration:**
- `python scripts/process_eia860.py --zip data/raw/eia-860/eia8602024.zip --out-dir data/raw/eia-860`
  — processes the official EIA-860 release ZIP into the parquet set above;
  point `--zip`/`--out-dir` at an older release + `vintage_<year>` to add a
  new vintage snapshot (matching the `vintage_2023`/`vintage_2024` file set).
- `scripts/fetch_eia860.py` is an alternate EIA API v2 route
  (`electricity/operating-generator-capacity`) producing
  `generators_us.csv`/`generators_<BA>.csv`/`metadata.json` — not the naming
  convention currently on disk here, but available if the API route is
  preferred over the bulk ZIP.

**Consumers:** `scripts/curate_fleet.py` (the authoritative unit-grain
spine — vintage-agnostic schema), `scripts/curate_confirmed_retirements.py`,
`scripts/curate_winter_fuel_inventory.py`, `scripts/derive_pjm_rggi_zone_share.py`,
`scripts/derive_lcr_membership.py`, `scripts/build_eia860_chp_by_year.py`,
`scripts/run_capacity_hindcast.py`.
