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
* All-string schema (a verbatim CSV copy: unused curve steps are EMPTY
  STRINGS, timestamps `MM/DD/YYYY HH:MM:SS` Central Prevailing Time with
  `Repeated Hour Flag`). Consumers coerce numerics and convert CPT→CST.
  Column inventory drifts at ERCOT's edge (ECRS columns appear mid-2023; the
  raw publications carry 187/188 columns) — consumers take per-shard column
  intersections. **Since the 2026-08-15 BLOAT-B-1 in-place slim (see
  "In-place slim" below) each shard carries the audited 108-column consumer
  union** (107 in the pre-2023-06 shards, which never had `Ancillary Service
  ECRS`) at zstd-15 — values, row counts and row order are the verbatim raw
  copy, only never-read columns were dropped. Consumers select columns
  explicitly, so every reader is unaffected.

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

## In-place slim (BLOAT-B-1, 2026-08-15) — column projection + zstd-15

Every shard in this corpus, the four loose probe-day extracts at
`data/raw/ercot/`, and the `rtcb-format-2026/` quarantine were rewritten IN
PLACE on 2026-08-15 by `scripts/data/slim_ercot_dam_disclosure.py
--sced-only` (BLOAT-B PR-1: `docs/bloat-removal-plan-2026-08.md` §3 item A1 +
§4.1 item B1a — the ERCOT-157 protocol re-run on the re-uploaded raw corpus):

* **Corpus shards**: projected to the audited 108-column consumer union (of
  the raw 187/188), zstd-15 + dictionary. The per-consumer citation registry
  is the slim script's docstring.
* **The four extracts**: projected to their own 180-column union (the frozen
  probes read SCED1/TPO/`Min Gen Cost`/`Start Up Hot Offer` columns the
  corpus consumers don't), zstd-15.
* **`rtcb-format-2026/`**: recompressed zstd-15 with NO column projection —
  the read adapter serves every native column (card D/D1), so no consumer
  subset exists to project to.

Values, row counts and row order are untouched everywhere; filenames
unchanged. Measured recovery **739.8 MiB / 21.3%** (2023 window 916.5→728.4,
2024+ window 2,180.3→1,699.3, extracts 208.6→151.6, rtcb 161.2→147.6 MiB) —
below the plan's ≈1,450 MiB estimate because the 2026-08 re-uploads landed
already zstd-compressed (the ERCOT-157 precedent ratio was measured against
SNAPPY originals) and the dropped columns are mostly empty-string curve steps
that compress to almost nothing.

Acceptance (the ERCOT-157 protocol): every consumer derive re-run over the
slimmed corpus reproduced its pre-slim output byte-identically, and the rtcb
adapter served byte-identical frames for all 27 parts — the evidence table is
in the BLOAT-B PR-1 pull request. The two `--position-tail` vintages STOP by
design on pre-existing corpus drift (their frozen 2024/25 artifacts were
derived from the extract basis before the ercot-183 corpus landed); the STOP
behaviour is identical before and after the slim.

The replaced raw bytes are hashed in the pre-slim `SHA256SUMS.txt` at commit
`971eaa3` (merged via PR #3957; extracts:
`../SHA256SUMS-60day-sced-extracts.txt` same commit) and remain recoverable
from git history: `git restore --source=971eaa3 -- data/raw/ercot/SCED/<shard>`.
Dropped columns are also re-fetchable from the MIS within its rolling
retention (`fetch_ercot_sced_corpus_shards.py` /
`fetch_ercot_60day_sced_gen_resource.py`); to re-adopt one, add it to the
KEEP registry and re-fetch or restore. The `SHA256SUMS.txt` in this directory
hashes the POST-slim bytes.

## `rtcb-format-2026/` — the RTC+B disclosure-format break (quarantined, bytes kept)

ERCOT's Real-Time Co-optimization (RTC+B) go-live changed the NP3-965 Gen
Resource member format at publications 2026-02-02 onward (deliveries
**2025-12-05..31**): `HASL`/`LASL` are REMOVED, `Telemetered Net Output `
lost its trailing space, the `Ancillary Service *` responsibility columns
became `AS Awards */AS Capability *`, and `Ramp Rate Up/Down` appeared
(193/195-column variants). `HASL` is a required read column of every corpus
consumer (`derive_ercot_sced_offer_wall` / `derive_ercot_faststart_pool` /
`sced_corpus_instruments`), so these shards CRASH the derives — the exact
defect ercot-95/97 quarantined in the Dec-3-9-2025 out-of-band upload.
Those 27 parts (`2026-02.part0002-0027`, `2026-03.part0000`) live in this
subdirectory, INVISIBLE to the consumers' non-recursive globs, bytes intact.
Deliveries 2025-12-01..04 (pubs 2026-01-30..2026-02-01) remain in the readable
pre-RTC+B format at the top level, so delivery-2025 is complete through Dec-04
plus the quarantined tail.

**The parts are now readable — through the adapter, and only through it**
(owner card D signature D1, 2026-08-11,
`docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md`; built at
`rtcb-adapter-1`). `scripts/lib/sced_rtcb_adapter.py` parses them into the
same in-memory frame contract the existing readers produce: the verbatim
all-string copy with `Telemetered Net Output` served under its canonical
trailing-space spelling and a `sced_format` = `rtcb-2026` flag on every row.
`HASL`/`LASL` are **explicitly absent, never NaN-filled** — requesting one
raises rather than inventing a telemetered quantity (rule 13 `[R-MEASURED]`) —
and the six `Ancillary Service <svc>` responsibility columns are refused under
their legacy names too: RTC+B's `AS Awards`/`AS Capability` are differently
defined (dense `0` vs sparse `''`, and RRS is disaggregated into PFR/UFR/FFR),
so mapping them back would be a construction rather than a read. They are
served under their RTC+B-native names instead.

**The quarantine subdirectory stays load-bearing and must not be flattened.**
RTC+B deliveries are calendar-**2025**, so the consumers' delivery-year row
filter does NOT exclude them, and publications 2026-02/03 fall inside
delivery-2025's shard-selection window. The non-recursive globs are the only
thing keeping them out of the delivery-2023..2025 identification paths. Never
add this subdirectory to a corpus-root tuple, and never make those globs
recursive; `sced_rtcb_adapter.assert_pre_rtcb_files` /`.assert_no_rtcb_rows`
assert the line positively, and `tests/curation/test_sced_rtcb_adapter.py`
pins it. **Every existing SCED-corpus lane stops at delivery 2025-12-04.**

## DATA NEEDED

* Deliveries **2024-01-10..23** (publications 2024-03-10..23): aged out of the
  free MIS list before the ercot-183 fetch; the owner's local raw archive is
  the only remaining source (data.ercot.com credentialed archive is
  owner-declined).
* Deliveries **2023-01-01 .. 2022-12-31 boundary bleed** and everything
  earlier live only in the delivery-2023 window above; pre-2023 publications
  are permanently out of free retention.

Immutable raw source root: never modified in place (repo data contract).
