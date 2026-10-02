# eia-860 — raw

EIA Form 860 annual fleet-registry release, several vintages:

- Top level: `eia860_*.parquet` (generators, plant, owner, utility,
  energy-storage {operable,proposed,retired_and_canceled},
  multifuel {operable,proposed,retired}, solar/wind {operable,retired},
  environmental association/equipment schedules) — the current snapshot:
  **the Final 2025 release since 2026-10-02** (owner ruling "replace the early
  release snapshot"; previously the 2025 Early Release).
- `vintage_2018/`, `vintage_2019/`, `vintage_2020/`, `vintage_2021/`,
  `vintage_2022/`, `vintage_2023/`, `vintage_2024/`, `vintage_2025/` — the same schema at an
  earlier EIA-860 release vintage, used for forecast-validation hindcasts
  that need the fleet as it was known at a past point in time (see
  `docs/hindcast-reports/`). 2018/2019/2021/2022 landed 2026-07-08 (data
  register intake, `docs/data-register-2026-07.md`) to close the pre-2020
  vintage gap; `vintage_2025/` is the Final 2025 release (added 2026-10-02, see below).

**Source:** EIA Form 860 (`eia8602025.zip` Final for the top level and `vintage_2025/`; `eia860<year>.zip` archive
releases for the other vintages), public domain — see `docs/data-licensing.md` §1.

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

**2026-10-02 — the vintage set is complete and `vintage_2025/` (Final) exists.**
Lane `claude/backcast-calibration-plan-753xwl` (closeout W0, owner instruction
"you can get EIA 860 … yourself"):

- `vintage_2023/` and `vintage_2024/` now carry the FULL sheet set (31 files each):
  the 20 missing sheets (every `*_retired_and_canceled`, `multifuel_proposed` and
  the 15 environmental schedules) were extracted by `process_eia860.extract_all_workbooks`
  from the archive releases `eia8602023.zip` (sha256
  `1447e23e608bea1523961542a90eb93ea86715067a37f211282541461049b46f`) and `eia8602024.zip`
  (`0aaae04812cd4ab87a3e346bdf93848a3cc15053fd4dc2a4cf82d2aeac95f12b`),
  `https://www.eia.gov/electricity/data/eia860/archive/xls/`. Every PREVIOUSLY committed
  file in both directories was verified frame-identical against the fresh extraction
  and left untouched (the committed `eia860_generators.parquet` keeps its 14-column
  F1 form; a fresh derive would add `planned_retirement_month`). Consequence at
  load time: `fleet.eia860._mid_vintage_exit_rows` now reads each vintage's OWN
  Retired-and-Canceled sheet for 2023/2024 solves instead of the pruned Early-Release
  fallback (`_mid_vintage_exit_rows_from_window`) — a data change, no code change.
- `vintage_2025/` is the **Final 2025** release `eia8602025.zip` (EIA release date
  2026-09-10; sha256 `2b27929d26cc1da9ad6a530da1cac6718cd8496098ee560c4d47cfffd96d08ba`,
  `https://www.eia.gov/electricity/data/eia860/xls/eia8602025.zip`), full 31-file set,
  processed by `scripts/data/process_eia860.py --zip … --out-dir data/raw/eia-860/vintage_2025`
  (eGRID 2024 heat rate joined at derive time: 44.0 % of rows carry one, same as the
  canonical 44.3 %). Under `eia860_vintage_tracks_solve_year` every 2025 BACKCAST now
  reads this directory instead of falling through to the Early Release; the committed
  2025 keeper legs were solved on the ER (G-DRIFT LIVE for 2025, every ISO). Per-ISO
  OP census Final vs ER: ERCOT +0.08 GW, CAISO +0.09, PJM −0.77, MISO +0.08, NYISO +0.01,
  NEISO +0.11, SPP −0.09, NWPP −0.02, SOCO −0.08 (nameplate). Retired sheet rows with
  Retirement Year 2023/2024/2025: 329 / 278 / 206.
- **The top level is the Final 2025 release too (owner ruling 2026-10-02, audit Q3).**
  Every top-level parquet was re-derived from `eia8602025.zip` with
  `process_eia860.py --zip … --out-dir data/raw/eia-860` (the within-window retiree
  parquet was left as extended above). Measured against the Early-Release tables it
  replaced, `eia860_generators.parquet`: 22,443 → 22,581 rows; 18 ER rows absent from
  the Final (822 MW — Astoria 8906 gen 4 387 MW `OS`, Beaver Creek 65019 ×3, International
  Paper Savanna 50398, US Magnesium 58191, Fall River Solar 64968 …), 156 Final rows absent
  from the ER (570 MW, PJM 251 / CISO 110 / ISNE 106 / MISO 74); among shared rows 13
  nameplate, 12 net-summer, 23 planned-retirement-year, 8 status and 16 energy-source
  revisions; no balancing-authority or prime-mover change. All EIA revisions — no
  hand-admitted row existed on the canonical table to lose. Consequence: every forecast
  run and every backcast year without a `vintage_<Y>/` directory now reads the Final;
  cache keys move through the solve-surface fingerprint. Not regenerated here (they read
  the zip series, not this snapshot): `_processed-legacy/eia860_chp_by_year.parquet`
  (still carries the ER as its 2025 member) and `_validation-source/capacity_actuals_*`
  (forecast scoring; `build_capacity_actuals.py` walks every vintage plus the current
  release and will pick the Final up on its next run).
- `eia860_generator_retired_within_window.parquet` was EXTENDED (`--retired-only
  --retired-window-from vintage_2023 vintage_2024 vintage_2025 --retired-extend
  --retired-until-year 2023`): 1,187 → 1,221 rows; +34 units / 167 MW, all with
  retirement years 2020–2022 (SOCO 59 MW, MISO 49, SWPP 26, ERCO 12); every pre-existing
  row byte-stable. The 2023–2025 retirements the new sheets also carry (113 units) were
  deliberately NOT added: `tests/unit/data/test_retiree_window_extension.py` pins the
  ≥ 2023 subset of this artifact (adding rows there would re-key every keeper's
  canonical-path fleet), and the 2023–2025 retiree gap stays the separately routed item
  of `docs/FINDING-xiso-fuelvintage-retiree-window-2026-09-09.md` §2 — which the
  year-matched vintages now cover for backcasts anyway (each vintage's own retired sheet).
- EIA-860M (monthly) now lives beside this store at `data/raw/eia-860m/` (forecast-only layer).

**Vintage snapshot completeness (history).** `vintage_2018`-`vintage_2022` carry the
full sheet set; until 2026-10-02 `vintage_2023` and `vintage_2024` carried the **operable sheet
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

## W0 settlement (2026-10-02, owner ruling R-2 — closeout-B)

**E.6 — membership at LOAD time.** Every `eia860_generators.parquet` (top level
and `vintage_2018 … vintage_2025`) is **unfiltered**: it carries every US
balancing authority plus a `nerc_region` column (the plant sheet's `NERC
Region`). Regenerated additively from each directory's own committed sheets by
`scripts/data/process_eia860.py --unfilter-in-place <dir> …` (rule 23 trigger
(d), a program-scope change): every previously committed row survives
value-for-value in place; 4,616–5,337 non-program rows were appended per
directory. Region membership is decided by
`market_sim.data.fleet.models.generator_footprint_mask` (BA code + NWPP's
NERC=WECC key) and `program_footprint_mask`, so registering a BA needs no
re-derive. Verified zero-diff: the W0 fleet census of MISO 2023, NWPP 2023,
SOCO 2021, SPP 2019 is identical before/after, and NWPP 2023's 19 LP fleet
arrays + `mc_base` hash identically. A fresh `--zip` build now writes the
unfiltered table directly.

**E.9 — freeze (rule 23 form).** EIA-860 inputs re-derive ONLY on (a) an EIA
Final release (each September; an Early Release is never a vintage of record),
(b) an 860M month in the forecast base year (forecast layer only), (c) a
crosswalk release (EPA CAMD-EIA / PUDL), (d) a program-scope change (BA / plant
registry). The commit cites the release. Every bundle's `solve_surface.json`
records `eia860_vintages: {directory: sha256}` for each EIA-860 directory the
run read (`config/solve_surface.py::eia860_vintage_digests`), so a re-keyed
keeper is attributed to a data change, never to a residual. Next scheduled
re-derive: the Final 2026 release (Sept 2027).

**E.2 — vintage diffs.** Unit-level changes between consecutive Final releases
(COD, ratings, status, technology) are written to
`docs/records/governance/closeout-2026-10/W0-census/vintage_diffs/<Y>_<Y+1>.csv`
by `scripts/data/derive_eia860_vintage_diffs.py`; the solved year's own vintage
always wins.
