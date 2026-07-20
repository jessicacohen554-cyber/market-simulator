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

- `daily/cnog-YYYYMMDD.xlsx` — the immutable daily snapshots, 2023-01-01 ..
  2025-12-31 (the rule-22 training window; no out-of-training year fetched).
- `missing-days.txt` — trade dates whose report 404s at the source (real
  publication gaps, e.g. 2024-12-31); coverage gaps keep the CAMPD fallback
  in the loader per the owner directive.
- `caiso-dam-outage-windows.parquet` — DERIVED consolidation (one row per
  outage-MRID episode: min start / max end across the daily snapshots, an
  episode never seen closed taking its last snapshot day's end-of-day) —
  `scripts/data/curate_caiso_dam_outages.py`.

**Fetch:** `scripts/data/fetch_caiso_dam_outages.py` (resumable; skips
files already present).

**Intended consumer (rule 14 — prefer measured over inferred):** the
backcast outage overlay, with unit-level DAM-before-CAMPD precedence —
the published outage schedule replaces the CAMPD emissions-gap inference
where a resource is covered, and the CAMPD windows
(`data/raw/campd-unit-outages-CAISO.csv`) remain the fallback for
units/periods the DAM reports don't cover. The RESOURCE ID → ORIS
(facility_id, plant_group) crosswalk and the gated loader precedence are
the remaining intake stages (see the caiso-104 handoff).

**Licensing note:** CAISO's redistribution terms are unclear/conditional —
see `docs/data-licensing.md` §6 (same posture as `caiso-curtailment`).
