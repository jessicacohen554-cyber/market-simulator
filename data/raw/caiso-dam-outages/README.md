# caiso-dam-outages — raw

CAISO's daily **Curtailed and Non-Operational Generator Prior Trade Date
Report** — the DAM-published unit-level outage/derate instrument
(owner-directed intake, caiso-104 session 2026-07-20): OUTAGE MRID, RESOURCE
NAME/ID, OUTAGE TYPE (FORCED/PLANNED), NATURE OF WORK, CURTAILMENT START/END
DATE TIME, CURTAILMENT MW, RESOURCE PMAX MW, NET QUALIFYING CAPACITY MW
(sheet `PREV_DAY_OUTAGES`, one xlsx per trade date, published ~08:30 PT the
following morning).

**Source:** <https://www.caiso.com/library/curtailed-and-non-operational-generator-reports>
(monthly library pages; direct file pattern
`https://www.caiso.com/documents/curtailed-non-operational-generator-prior-trade-date-report-YYYYMMDD.xlsx`).

**Layout:**

- `daily/cnog-YYYYMMDD.xlsx` — the immutable daily snapshots. The fetch
  **defaults** to 2023-01-01 .. 2025-12-31 (the rule-22 training window); pass
  explicit dates to widen it. CAISO's prior-trade-date series begins
  **2021-06-18** (nothing exists before it), so the maximum available span is
  2021-06-18 → present.
- `missing-days.txt` — trade dates whose report 404s at the source (real
  publication gaps, e.g. 2024-12-31); coverage gaps keep the CAMPD fallback
  in the loader per the owner directive.
- `caiso-dam-outage-windows.parquet` — DERIVED consolidation (one row per
  outage-MRID episode: min start / max end across the daily snapshots, an
  episode never seen closed taking its last snapshot day's end-of-day) —
  `scripts/data/curate_caiso_dam_outages.py`. Binary; regenerated from the
  daily snapshots (not carried in the committed tree — the push path can't
  transport binary; see below).

**Fetch:** `scripts/data/fetch_caiso_dam_outages.py [START END]` (resumable;
skips files already present). For the full available series run
`fetch_caiso_dam_outages.py 2021-06-18 <today>`.

**Reproduce the pipeline:**

```
python scripts/data/fetch_caiso_dam_outages.py 2021-06-18 <today>   # daily/ xlsx
python scripts/data/curate_caiso_dam_outages.py                     # windows parquet
python scripts/data/build_caiso_resource_crosswalk.py              # reviewable crosswalk
```

The derived `caiso-dam-outage-windows.parquet` and the daily xlsx are binary
and are **not committed** (the GitHub API push path used in this repo carries
only text; `git push` is disabled). They are regenerated locally by the two
scripts above — the committed, reviewable artifacts are the scripts, the loader,
and the crosswalk CSV.

**Consumer (rule 14 — prefer measured over inferred) — WIRED:** the backcast
outage overlay now applies unit-level **DAM-before-CAMPD precedence** behind
`ScenarioConfig(outage_source="historic", caiso_dam_outages=True)` (default
off). The published outage schedule replaces the CAMPD emissions-gap inference
for each CAISO thermal plant it covers; the CAMPD windows
(`data/raw/campd-unit-outages-CAISO.csv`) remain the fallback for every
plant/period the DAM reports don't reach (uncovered plants, and pre-2021-06-18
years). Wiring:

- `data/raw/reference/caiso-resource-eia-crosswalk.csv` — reviewable RESOURCE
  ID → (plant_code, plant_group) crosswalk (`build_caiso_resource_crosswalk.py`);
  only `accepted` rows enter a solve. Auto-accepts 34 exact name matches across
  29 of the 55 CAISO thermal plants; the remaining candidates await review.
- `market_sim.data.caiso_outages.caiso_dam_outage_derate_factors` — turns the
  episodes into the per-plant availability multiplier the fleet overlay consumes
  (`generators_to_fleet_arrays`).

**Activation:** the two core-file edits (the `caiso_dam_outages` ScenarioConfig
flag and the fleet overlay branch) live in `loader-wiring.patch` — apply with
`git apply data/raw/caiso-dam-outages/loader-wiring.patch` (they touch files
>300 lines that the text-only push path can't safely rewrite whole).

**Holdout note (rule 22):** the flag is default-off and no solve/scoring runs
here, so intaking the full series (incl. 2022 validation + H1-2026 locked test)
is data-only under owner authorization. Enabling the flag on a holdout year
requires the usual quarantine discipline.

**Licensing note:** CAISO's redistribution terms are unclear/conditional —
see `docs/data-licensing.md` §6 (same posture as `caiso-curtailment`).
