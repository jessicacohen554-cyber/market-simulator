# ERCOT NP3-965 60-Day SCED Disclosure — Gen Resource Data corpus

Full-year publication-month shards of the ERCOT MIS **NP3-965-ER "60-Day SCED
Disclosure Reports"** Gen Resource Data members (`reportTypeId=13052`): per
resource per ~5-minute SCED interval, the telemetered RT energy offer curves
(SCED1/SCED2), submitted three-part offers, telemetry (HSL/HASL/HDL/LSL/LASL/
LDL, Base Point, statuses) and AS responsibilities.

## Layout (the corpus convention)

* `YYYY-MM.partNNNN.parquet` — `YYYY-MM` is the **PUBLICATION month** on the
  MIS. NP3-965 publishes each delivery day exactly 60 days later, so a shard
  carries delivery timestamps ~2 months earlier than its filename (delivery ≈
  filename − 2). **Never trust the filename for the delivery year** — every
  consumer selects shards by a publication window and filters rows to the
  exact delivery year read from `SCED Time Stamp`
  (`derive_ercot_sced_offer_wall._sced_source_files` / `_delivery_year_rows`),
  which is what keeps validation-holdout (2022) and locked-test (2026) bleed
  rows out of training-year surfaces (CLAUDE.md rule 22).
* One part per publication day (= one delivery day, ~100–105k rows, ~4 MB);
  early-2023 months pack 2 days/part — the partitioning is size-varying and
  consumers glob `*.part*.parquet`, so part granularity is a convention, not
  a contract. Part numbering is chronological within a month and continues
  existing on-disk numbering.
* Raw 187-column all-string schema (a verbatim CSV copy: unused curve steps
  are EMPTY STRINGS, timestamps `MM/DD/YYYY HH:MM:SS` Central Prevailing Time
  with `Repeated Hour Flag`). Consumers coerce numerics and convert CPT→CST.
  Column inventory drifts at ERCOT's edge (ECRS columns appear mid-2023; some
  shards carry 188 columns) — consumers take per-shard column intersections.

## Provenance

* **Publications 2023-03 .. 2024-03 part0000-0008** (delivery-2023 window +
  Jan-2024 bleed): the 2026-08-03 owner re-upload (ERCOT-157), verified 315
  shards / 35.82M delivery-2023 rows / all 365 delivery days. The original
  2026-07-21 full-corpus upload was purged by the 2026-07-22 large-blob
  history rewrite.
* **Publications 2024-03-24 .. 2026-03-01 (+ supplemental bundles)**: the
  ercot-183 re-upload (owner card D4, 2026-08-09), fetched from the free MIS
  path by `scripts/data/fetch_ercot_sced_corpus_shards.py` — see
  `docs/handoffs/ercot-sced-2024-2025-reupload-2026-08.md` for the staging
  plan, per-month shard counts and acceptance results.

## DATA NEEDED

* Deliveries **2024-01-10..23** (publications 2024-03-10..23): aged out of the
  free MIS list before the ercot-183 fetch; the owner's local raw archive is
  the only remaining source (data.ercot.com credentialed archive is
  owner-declined).
* Deliveries **2023-01-01 .. 2022-12-31 boundary bleed** and everything
  earlier live only in the delivery-2023 window above; pre-2023 publications
  are permanently out of free retention.

Immutable raw source root: never modified in place (repo data contract).
