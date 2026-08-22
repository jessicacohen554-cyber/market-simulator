# MISO M2M/CMP seam-class flowgate record

Hourly per-flowgate Market-to-Market (M2M) settlement record for MISO's two
CMP seams — MISO–PJM and MISO–SPP ("SWPP") — the public data that can name
what bound in reality on the seams (miso-174 §7 item 3; intake chartered and
executed by session miso-176, 2026-08-22). Feasibility, coverage and the
source inventory: `docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md` §2a
(EXT/seam-class congestion coverage 90/90/88 % across 2023–2025).

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

## Files

`M2M_Settlement_srw_<year>.csv.gz` — verbatim source bytes, gzipped at
rest, produced by `scripts/data/fetch_miso_m2m_flowgates.py`. **The bulk
mirrors are gitignored** (precedent: the bc_HIST mirrors two entries up in
`.gitignore`); the fetch script is the reproducibility path and this table
records each mirror's fetch-time identity:

| file | fetched | raw bytes | rows (incl. header) | sha256 (raw csv) |
|---|---|---:|---:|---|
| `M2M_Settlement_srw_2023.csv` | 2026-08-22 | 13,532,690 | 124,822 | `bcf31ce0b893b80c382490a11aadf7ca7920f30d007c6d1247687823e9b470bb` |
| `M2M_Settlement_srw_2024.csv` | 2026-08-22 | 17,685,058 | 162,395 | `9b2af9c9842503a7b9266476ab9122b12be5b41cbf5b062151e81da62dd6bc45` |
| `M2M_Settlement_srw_2025.csv` | 2026-08-22 | 19,627,450 | 181,990 | `d992560c72f35c912e18b549dc3abb4ca0ffa1ab8ef0afb4428f996be93e8383` |

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
