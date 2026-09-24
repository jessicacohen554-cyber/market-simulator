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

**Known coverage gap + fix (RD-5, 2026-07-15):** the top-level (current)
`eia860_generator_retired_and_canceled.parquet` omits two plants that
genuinely retired inside the 2021-2025 capacity-hindcast window — Indian
Point 3 (plant 8907, NY/NYISO, dropped from every sheet of the current
release) and Palisades (plant 1715, MI/MISO, moved back to the *operable*
sheet after its 2025 restart, the first US commercial restart of a retired
nuclear plant). `data/raw/_validation-source/retired_sheet_coverage_gaps.csv`
restores both rows verbatim from this repo's own already-committed earlier
vintage snapshots (`vintage_2021`, `vintage_2022`) and is unioned in by
`scripts/data/build_capacity_actuals.py` (it lives under `_validation-source/`,
not here, because `data/raw/eia-860/*.csv` is gitignored as a local-override
convention — see that file's own header). **Palisades' restart makes its
2022 retirement scoring-ambiguous** (a since-reversed exit) — see
`data/raw/_validation-source/README.md` for the full note; this repo does
not adjudicate here how a reversed retirement should score against a
hindcast (RC-0B's call), only makes the underlying EIA-860 fact available.

**The coverage gap is wider than those two plants (FFR-7A, 2026-08-06).**
Measured across the committed snapshots: of the 442 units the `vintage_2022`
retired sheet dates to 2021-2022, **106 are absent from the current release's
retired sheet** — EIA prunes older retirements from an Early Release rather
than carrying them forward. `build_capacity_actuals.py` therefore reads the
whole release series (every `vintage_<year>/` plus the current release) rather
than the current retired sheet alone, which recovers all 106 generically; the
hand-curated gap-fix file above is still required only for Palisades, whose
*latest* status is `OP`. The same series read supplies the `Status` history
that dates a retirement at physical cessation instead of its paper date
(`physical_exit_year`).

**Vintage snapshot completeness.** `vintage_2018`-`vintage_2022` carry the
full sheet set; `vintage_2023` and `vintage_2024` carry the **operable sheet
only** (no retired-and-canceled sheet) **plus `eia860_utility.parquet`**, added
2026-09-24 by NWPP-51 (`docs/handoffs/PRECOMMIT-nwpp-51-2026-09-24.md` §10).
The utility sheet was missing, so `eia860_costofservice_majority_plants` returned
an EMPTY set whenever these vintages were active. It is Schedule 1 of EIA's own
archive releases, `eia8602023.zip` (sha256 `1447e23e…9b46f`) and `eia8602024.zip`
(sha256 `0aaae048…f12b`), processed by `process_eia860.extract_all_workbooks`.
The same extraction reproduces the committed `owner`, `plant` and
`generator_operable` sheets of both dirs frame-identically, so it is the same
release. Nothing else in either dir was touched. Consumers that walk the series must
treat a missing sheet as *no observation for that year*, never as evidence a
unit was absent — the release year is simply a gap in that unit's history.

**Heat rates are vintage-matched (F1, 2026-09-24).** Every
`eia860_generators.parquet` carries a plant-level `heat_rate` (MMBtu/MWh) joined
from eGRID `PLHTRT` of the MATCHING vintage — `vintage_<Y>/` from eGRID `Y`, the
canonical 2025 Early Release from eGRID 2024 (the latest; there is no eGRID
2025), and `eia860_generator_retired_within_window.parquet` from each unit's last
operating year — with a nearest-vintage fallback (tie → earlier), so only a plant
absent from EVERY eGRID vintage 2018-2024 is left null for the loader's
`HEAT_RATE_BINS` fallback. Before F1, `vintage_2018/2019/2021/2022` carried no
`heat_rate` column and `vintage_2020` an all-null one, so a 2019-2022 backcast
priced 95-100 % of thermal MW at the asset-class table
(`docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §1 D1).
Regenerate with
`python scripts/data/process_eia860.py --rejoin-heat-rate <parquet> ...`, which
rewrites ONLY the `heat_rate` column. The same session appended the NWPP and SOCO
balancing authorities' within-window retirees the retiree parquet predated
(`--rescope-retired-window`, strictly additive; audit §1 D3).
