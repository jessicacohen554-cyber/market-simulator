# ercot/SCED-CT — raw (gitignored)

ERCOT MIS **NP3-965-ER "60-Day SCED Disclosure Reports"** (`reportTypeId=13052`),
`60d_SCED_Gen_Resource_Data-*` member, **scoped to the CT fleet** — the published
`Resource Type` codes `SCLE90` (simple-cycle large, ≥90 MW) and `SCGT90`
(simple-cycle gas turbine, ≥90 MW). **One Parquet per delivery DAY:**

    60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_ct_fullspan_<YYYY-MM-DD>.parquet

Per-day rather than per-month on purpose: a delivery day that never turns up in
any publication is then **visible as a missing file**, instead of being silently
absent from inside a month shard. `_processed_docs.json` records which
publication documents have already been mined so a resume skips them.

Every column of the published CSV is kept (188 in the current vintage): the
`SCED1`/`SCED2 Curve-MW1..35`/`-Price1..35` energy offer curves SCED actually
dispatched on, the QSE's `Submitted TPO-MW1..10`/`-Price1..10` three-part offer,
and the telemetry (`Telemetered Resource Status`, `HSL`/`HASL`/`HDL`/`LSL`/
`LASL`/`LDL`, `Base Point`, `Telemetered Net Output`, per-service AS
responsibilities). Rows are the raw published values — `SCED Time Stamp` is
Central **Prevailing** Time with a `Repeated Hour Flag`; consumers convert
CPT→CST via `build_ercot_hsl._prevailing_to_standard`, exactly as the
all-resource sibling corpus in `../SCED/` requires.

## Why CT-scoped, and why it exists

The ERCOT-147 §4 reopen condition (`docs/DIAGNOSIS-ercot147-ct-band-reident-2026-07-31.md`)
made its first data prerequisite a **full-span** CT extract: the CT fleet's
submitted curve is daily-repriced (intra-day variance share 0.14) and holds no
stable $ level (daily rel IQR 0.64), so the daily conduct object has to be
measured across the training span rather than sampled on the 82 selected days
the four existing day-list extracts cover. CTs are ~15 % of a delivery day's
rows (18,816 of 124,608 on a measured 2025 day), which is what makes ~700 days
affordable — 0.5 MB of Parquet per day against ~90 MB of unscoped CSV.

**Scope warning.** This directory is the CT fleet ONLY. It is deliberately NOT
placed in `../SCED/`, whose consumers (`derive_ercot_sced_offer_wall._CORPUS_DIRS`
globs `data/raw/ercot/` and `data/raw/ercot/SCED/`) read every Parquet they find
as an all-resource day. A CT-only shard on that path would silently understate
every class share computed from it. Any consumer of this directory must opt in
explicitly.

*Sharpened 2026-08-31 (ercot-248), having measured the actual mechanism:* the
corpus glob is `[0-9][0-9][0-9][0-9]-[0-1][0-9].part*.parquet` and the legacy
sample-day glob is `60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*`
rooted at `data/raw/ercot/` — so a per-day file of this directory's naming,
dropped into `../SCED/`, matches **neither** and would be invisible rather than
corrupting. The corrupting placement is the other one: a CT-scoped file at
`data/raw/ercot/` whose label begins `<year>_` **does** match the legacy glob.
Both failure modes are silent; keep this fleet in its own directory either way.

**Use the all-resource corpus unless you specifically need the CT scope.**
This extract exists because ERCOT-147 §4 needed ~700 CT days affordably, back
when the all-resource span past delivery 2024-01-09 did not exist. It does now
(`../SCED/`, restore verified 2026-08-31), it is a strict superset, and it is
the one every corpus consumer already reads.

## Coverage — and the two gaps, stated

| Span | Source | Grain |
|---|---|---|
| delivery 2022-12-31 … 2024-01-09 | `../SCED/` (ERCOT-157 owner re-upload, 315 shards) | **all resources**, all hours |
| delivery 2024-01-24 … 2025-12-31 | `../SCED/` (ercot-183 re-upload 2026-08-09; restore verified ercot-248 2026-08-31) | **all resources**, all hours |
| delivery 2024-01-24 … 2025-12-31 | this directory (ERCOT-160 fetch) | **CT only**, all hours |

> **This table was stale between 2026-08-09 and 2026-08-31, and misled a
> session.** Rows 1 and 3 were written on 2026-08-04, when CT-only genuinely
> was all that existed past delivery 2024-01-09. Five days later ercot-183
> landed the **all-resource** corpus over the identical span into `../SCED/`;
> because that payload is gitignored (BLOAT-B-5 item A2, 2026-08-15) it is
> absent from a fresh clone, so this table read as "CT-only is what there is"
> rather than "CT-only is a convenience subset". The ercot-248 charter
> inherited exactly that reading and was scoped as a new intake of a corpus
> that already existed. **Read `../SCED/README.md` before concluding anything
> about coverage past delivery 2024-01-09.**

* **Gap 1 — delivery 2024-01-10 … 2024-01-23 (14 days), UNREACHABLE on the free
  path.** It falls between the end of the committed all-resource corpus and the
  start of the MIS rolling retention window. Reported by the fetcher as
  `NOT LISTED`, never fabricated. Closing it needs the credentialed
  `data.ercot.com` archive, which is **owner-declined**
  (`docs/handoffs/ercot-as-coopt-plan-2026-07.md` §WS-E).
* **Gap 2 — delivery ≥ 2026-01-01 is NOT fetched by design.** The MIS window
  reaches ~2026-06-04, but H1-2026 is the locked-test tier (CLAUDE.md rule 22)
  and the holdout spend freeze is active. The fetcher's `--max-delivery-date`
  (default 2025-12-31) refuses those days; verified live that
  `--delivery-range 2025-12-30 2026-01-02` errors on the two 2026 days.

MIS retention is a **rolling ~2.3 years** on the free unauthenticated path
(earliest publication listed 2024-03-24 as of 2026-08-04 → earliest reachable
delivery 2024-01-24; publication = delivery + 60 days). Gap 1 therefore *grows*
over time: re-running this fetch later recovers fewer early-2024 days, never
more.

## Schema vs the all-resource corpus (measured 2026-08-04)

Compared against `../SCED/2023-03.part0000.parquet`:

* **188 columns vs 187** — the extra one is `Ancillary Service ECRS`, the
  service ERCOT introduced mid-2023. A superset, not a conflict.
* **Numeric columns are `float64` here, `str` in `../SCED/`** (e.g. `HSL`
  `197.0` vs `'54'`). This mirrors a difference that ALREADY exists in-repo
  between `../` (coerced, written by this fetcher) and `../SCED/` (raw strings,
  owner upload), and the shared consumer handles it —
  `derive_ercot_sced_offer_wall` applies `pd.to_numeric(errors="coerce")` to
  its columns on read. Any NEW consumer spanning both corpora must do the same
  rather than assume either dtype.

## Two publication quirks this intake had to handle (verified 2026-08-04)

Both were discovered by the fetch failing loudly rather than producing quiet
nonsense, and both are why the span is scanned by **publication** rather than
by delivery day:

1. **The member filename is the PUBLICATION stamp, not the delivery day.** The
   member `60d_SCED_Gen_Resource_Data-04-OCT-24.csv` inside the 2024-10-04
   publication carries `SCED Time Stamp` values of `08/05/2024` — delivery =
   publication − 60. Naming an output after the member's own filename would
   mislabel every single day by 60 days. The delivery day is therefore read
   from the file's own stamps; the filename is only ever a cheap hint.
2. **A publication day can carry more than one document, and a document more
   than one delivery day.** 2024-10-04 has both the ordinary ~10 MB daily
   document AND a ~245 MB `Supplemental_60_Day_SCED_Disclosure` holding 32
   members. Code that took "the newest document published that day" got the
   supplemental and then failed on its 32 members. Supplementals are detected
   by name, are exempt from the nominal-lag skip test, and every member they
   carry is read for its true delivery days.

## Regeneration

```bash
python scripts/data/fetch_ercot_60day_sced_gen_resource.py \
    --delivery-range 2024-01-10 2025-12-31 \
    --resource-types SCLE90 SCGT90 \
    --window-label ct_fullspan --out-dir data/raw/ercot/SCED-CT
```

Spans **resume by default** at day granularity — an interrupted run re-fetches
only the days it had not written (pass `--no-resume` to force a full re-fetch).
The run prints every delivery day it could NOT find in any listed publication,
grouped into contiguous runs, so gaps are reported rather than inferred.

**Contents are gitignored** (see `.gitignore`) — ~360 MB of Parquet, well past
what the push path carries, and deterministically re-fetchable by the command
above. Only this README and `SHA256SUMS.txt` are tracked; the manifest is the
committed provenance record for the shards, the `data/raw/pjm-zonal-lmp/`
precedent.

## Licensing

ERCOT MIS 60-day disclosure data — see `docs/data-licensing.md` §3 (same
product family as the committed `../SCED/` corpus and `../../ercot-AS/`).
