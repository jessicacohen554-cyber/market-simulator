# MISO M2M/CMP seam-class flowgate record

Hourly per-flowgate Market-to-Market (M2M) settlement record for MISO's two
CMP seams — MISO–PJM and MISO–SPP ("SWPP") — the public data that can name
what bound in reality on the seams (miso-174 §7 item 3; intake chartered and
executed by session miso-176, 2026-08-22). Feasibility, coverage and the
source inventory: `docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md` §2a
(EXT/seam-class congestion coverage 90/90/88 % across 2023–2025).

> **Payload posture: TRACKED.** The three annual mirrors (~5.4 MB gzipped
> total) are committed at tip since 2026-08-30 (owner card ruling, director
> sitting: `scripts/regenerate_clean.py` ran 50/51 because this was the one
> datatype with no raw mirror under `data/raw` — full from-source
> reproducibility restored). This supersedes the intake-time posture
> (miso-176 gitignored the mirrors on the bc_HIST precedent, leaving
> `scripts/data/fetch_miso_m2m_flowgates.py` as the only recovery route);
> the fetch script is now the re-fetch/verification path, not the sole
> reproducibility path. `SHA256SUMS.txt` records the committed files'
> identity. Intake genealogy:
> `docs/handoffs/miso-m2m-flowgates-raw-mirror-2026-08.md`.

## Source

Public annual market-report consolidations, no auth (same channel as the
bc_HIST congestion layer):

    https://docs.misoenergy.org/marketreports/M2M_Settlement_srw_YYYY.csv

One row per (flowgate, hour) while the flowgate is under M2M coordination —
a missing (flowgate, hour) means "not in M2M coordination that hour", not
missing data. Every hour of the year carries rows for some flowgates.
Columns: `HOUR_ENDING, FLOWGATE_ID, MONITORING_RTO, CP_RTO, FLOWGATE_NAME,
MISO_SHADOW_PRICE, MISO_MKT_FLOW, MISO_FFE, CP_SHADOW_PRICE, CP_MKT_FLOW,
CP_FFE, MISO_CREDIT, CP_CREDIT`.

Semantics (verified over the 2023–2025 mirrors at fetch):

- **Timestamps are hour-ENDING labels 1..24 on MISO market time** (EST,
  UTC-5 fixed year-round, no DST): HE 24 is posted as `24:00:00`, every day
  carries the full 24 labels (8,760/8,784 distinct hours per year — no DST
  gap/dup, which is what pins the fixed-offset clock).
- The `MISO_*` columns are always MISO's own quantities; the `CP_*` columns
  are the counterparty (non-MISO) RTO's. On neighbour-monitored rows
  (`MONITORING_RTO` ∈ {PJM, SWPP}, `CP_RTO` = MISO) the source zero-fills
  `CP_MKT_FLOW`/`CP_FFE` — the neighbour's own flow/entitlement is not
  carried; its shadow price is.
- `MONITORING_RTO` = "NO RTO" is a small transitional class (~30–460
  rows/yr) with NaNs in several numeric columns.
- ~82–86 % of rows carry zero shadow prices on both sides: the M2M
  coordination window extends beyond the binding hours.

## Files & provenance

`M2M_Settlement_srw_<year>.csv.gz` — verbatim source bytes, gzipped at rest
with a **deterministic container** (mtime=0, empty filename field), produced
by `scripts/data/fetch_miso_m2m_flowgates.py`. Deterministic gzip means a
refetch of an unchanged source file reproduces the committed mirror
byte-for-byte, so `SHA256SUMS.txt` (committed `.csv.gz` identity) verifies
in either direction; the table below is the **source** identity — sha256 of
the raw (uncompressed) CSV as published:

| file | fetched | raw bytes | rows (incl. header) | sha256 (raw csv) |
|---|---|---:|---:|---|
| `M2M_Settlement_srw_2023.csv` | 2026-08-22 | 13,532,690 | 124,822 | `bcf31ce0b893b80c382490a11aadf7ca7920f30d007c6d1247687823e9b470bb` |
| `M2M_Settlement_srw_2024.csv` | 2026-08-22 | 17,685,058 | 162,395 | `9b2af9c9842503a7b9266476ab9122b12be5b41cbf5b062151e81da62dd6bc45` |
| `M2M_Settlement_srw_2025.csv` | 2026-08-22 | 19,627,450 | 181,990 | `d992560c72f35c912e18b549dc3abb4ca0ffa1ab8ef0afb4428f996be93e8383` |

Re-verified 2026-08-30 at commit time: all three URLs refetched; raw-csv
sha256/bytes/rows **identical** to the 2026-08-22 fetch (MISO has not
restated any file), and the committed mirrors' decompressed contents match
this table (`zcat <f> | sha256sum`).

## Re-fetch

    PYTHONPATH=src python3 scripts/data/fetch_miso_m2m_flowgates.py [--years 2023 2024 2025] [--force]

Years outside the 2023–2025 train window additionally need
`--allow-out-of-train` with session-logged owner authorization (CLAUDE.md
rule 22 `[R-HOLDOUT]`). After a `--force` refetch, `git diff` clean means
the source is byte-stable; a dirty diff means MISO restated the file —
treat that as an intake event (verify, update this table and
`SHA256SUMS.txt`, and record the restatement), never a silent overwrite.

Curated to `data/clean` by `scripts/data/curate_miso_m2m_flowgates.py`
(schema `data/dictionary/schema/miso-m2m-flowgates.schema.yaml`).

## Rule-13 line (fixed at intake)

The **FFE** (Firm Flow Entitlement) columns are a CMP market-design
quantity — admissible IN KIND as a model input, subject to rule 17's
window/driver/forward-story test in whatever mechanism would consume them.
The **shadow price, market flow and credit** columns are the ANSWER class —
when/how hard a coordinated flowgate binds and what actually flowed are
dispatch outcomes; validation/diagnosis ONLY, never a solve input.

## DATA NEEDED (documented, deliberately not mirrored)

The wider M2M/CMP family from miso-77 §2a stays un-mirrored until a charter
needs it:

- `M2M_FFE_YYYY_MM_DD.CSV` — daily hourly-row FFE for the FULL coordinated
  flowgate universe (764–1,084 flowgates; ~1.2–2.0 MB/day, ~1,095 files for
  the train window). The settlement record above already carries FFE for
  every M2M-coordinated flowgate-hour; the daily files add entitlements for
  flowgates OUTSIDE coordination windows.
- `Allocation_on_MISO_Flowgates_YYYY_MM_DD.csv` — daily per-entity
  allocations whose "Allocation to Rating Percentage" implies total
  flowgate ratings (the admissible rating series).
- `M2M_Flowgates_as_of_YYYYMMDD.CSV` — flowgate registry snapshots
  (NERC ID → monitoring RTO + description; the settlement file carries the
  same fields per row).
- OASIS statics (`AFC_FG_RATINGS_TRM_CBM.pdf`, coordinated-flowgates PDF) —
  OATI-hosted behind the private webCARES CA; fetch notes in miso-77 §6.
