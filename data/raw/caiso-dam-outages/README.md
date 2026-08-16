# caiso-dam-outages — raw (`daily/*.xlsx` gitignored)

> **Payload posture.** The 1,094 `daily/cnog-YYYYMMDD.xlsx` snapshots
> (155.0 MiB) are **gitignored and no longer tracked at tip** — BLOAT-B-2
> corpus conversion, `docs/bloat-removal-plan-2026-08.md` §4.4 item B4. The
> DERIVED `caiso-dam-outage-windows.parquet` that every runtime consumer reads
> **stays tracked**, as do `missing-days.txt`, `loader-wiring.patch`, this
> README and `SHA256SUMS.txt`. See **Recovery / re-fetch** below.

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

- `daily/cnog-YYYYMMDD.xlsx` — the immutable daily snapshots, **gitignored**
  (their bytes are pinned by `SHA256SUMS.txt`). The fetch
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
  `scripts/data/curate_caiso_dam_outages.py`. **Tracked**: this is the only
  artifact any runtime consumer reads, so it is the one that must survive the
  payload conversion.
- `SHA256SUMS.txt` — the provenance record for the gitignored dailies: sha256 +
  byte size of all 1,094 snapshots as of the pin sha below. A re-fetch is
  verifiable against it.

**Fetch:** `scripts/data/fetch_caiso_dam_outages.py [START END]` (resumable;
skips files already present). For the full available series run
`fetch_caiso_dam_outages.py 2021-06-18 <today>`.

**Reproduce the pipeline:**

```
python scripts/data/fetch_caiso_dam_outages.py 2021-06-18 <today>   # daily/ xlsx
python scripts/data/curate_caiso_dam_outages.py                     # windows parquet
python scripts/data/build_caiso_resource_crosswalk.py              # reviewable crosswalk
```

## Recovery / re-fetch — getting the dailies back

Two routes; both end at bytes verifiable against `SHA256SUMS.txt`.

1. **Restore from git history — DEAD since the 2026-08-16 history rewrite**
   (`cleanup-large-blobs.yml` run #18 / 31955205445, owner decision;
   `docs/FINDING-history-rewrite-2026-08-16.md`). The pin
   `315a24524a851566c3d32cc88668fa32dcbd1d74` no longer resolves, and its
   rewritten twin `94b9cda540b8`'s tree no longer contains `daily/` (verified
   2026-08-16) — the 1,094 snapshot blobs were stripped. `git restore
   --source=<pin>` cannot recover them from this repository. `SHA256SUMS.txt`
   remains the identity record: any recovered set is verified against it.

2. **Re-fetch from CAISO — now the PRIMARY route (regenerates, does not
   guarantee byte identity).**

   ```
   python scripts/data/fetch_caiso_dam_outages.py 2021-06-18 <today>
   cd data/raw/caiso-dam-outages && sha256sum -c <(awk '$1 !~ /^#/ && NF>=3 {s=$1; $1=$2=""; sub(/^ +/,""); print s "  " $0}' SHA256SUMS.txt)
   ```

   **Retention risk, stated:** the CAISO library's retention is *observed, not
   contractual* — there is no longer a repository backstop behind it. A
   snapshot day CAISO stops serving is unrecoverable except through GitHub's
   `refs/pull/*` retention of the pre-rewrite trees (incidental, unadvertised,
   no guarantee — e.g. `git fetch origin refs/pull/3956/head`).
   `missing-days.txt` plus the sha manifest make any re-fetch auditable
   against what was actually held.

Verifying the manifest is also how you confirm a restore succeeded before
re-deriving. Then re-run `curate_caiso_dam_outages.py` only if the parquet
needs rebuilding — the committed parquet already reflects these exact bytes.

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
