# CAISO-AS — DAM ancillary-service regional requirements (OASIS AS_REQ) + clearing prices (PRC_AS)

Fetched 2026-07-10 by `scripts/fetch_caiso_oasis.py --datasets asreq --years 2023 2024 2025`
(CAISO OASIS `SingleZip?queryname=AS_REQ&market_run_id=DAM&version=1&anc_type=ALL&anc_region=ALL`,
adaptive ≤25-day windows, resumable). Coverage verified complete: every day 2023-01-01 →
2025-12-31 (1,096 days), 44 window CSVs. **Train years only** (CLAUDE.md rule 22 — no 2022, no
H1-2026).

Content: hourly MW ancillary-service requirement per **AS region** and product, DAM. Key
columns: `ANC_REGION` (`AS_CAISO`, `AS_CAISO_EXP`, `AS_NP26`, `AS_NP26_EXP`, `AS_SP26`,
`AS_SP26_EXP`), `ANC_TYPE` (`SR` spin, `NR` non-spin, `RU`/`RD` regulation, `RMU`/`RMD` on the
EXP region), `XML_DATA_ITEM` (`{SP,NS,RU,RD}_REQ_{MIN,MAX}_MW` — each region×product×hour
carries a MINIMUM row and a MAXIMUM row), `MW`, `OPR_DT`, `OPR_HR` (hour-ending, prevailing
Pacific), `INTERVALSTARTTIME_GMT`.

Semantics (CAISO BPM for Market Operations, AS region constraints): the regional **MINIMUM** is
the must-procure-within-region floor (the locational driver — SP26 ≈ south of Path 26 →
model zones LA_BASIN/SDGE/SP15_rest; NP26 → NP15/ZP26); the regional **MAXIMUM** is the
anti-concentration cap. `AS_CAISO`/`AS_CAISO_EXP` are the system totals (EXP = expanded region
including participating interties). Purpose: the measured requirement series for CAISO
sub-regional reserve families (`docs/handoffs/caiso-locational-as-mechanism-2026-07-10.md`;
caiso-70 FINDING probe-#2 redirect). Immutable raw — never modified in place; curation to
`data/clean/` goes through the data-dictionary contract.

## asprc — DAM ancillary-service clearing prices (OASIS PRC_AS)

Fetched 2026-08-25 by `scripts/data/fetch_caiso_oasis.py --datasets asprc_ru asprc_rd
asprc_sr asprc_nr --years 2023 2024 2025`
(`SingleZip?queryname=PRC_AS&market_run_id=DAM&version=1&anc_type=<RU|RD|SR|NR>&anc_region=ALL`).
**A PRC_AS request with `anc_type=ALL` is silently truncated to ONE trade day** (a 2-day ALL
window returns only day 1 — measured 2026-08-25), while a single-product request returns
complete ≤25-day windows (25 d × 24 h × 6 regions = 3,600 rows, verified) — so this series is
one file set PER PRODUCT (`asprc_{ru,rd,sr,nr}_ALL_<start>_<end>.csv`, ~44 windows each),
not the day files the ALL form would force. Train years 2023–2025.

Content: hourly `$/MW` clearing-price **contribution** per AS region and product,
`XML_DATA_ITEM` `{SP,NS,RU,RD,RMU,RMD}_CLR_PRC` (the price sits in the `MW` column — OASIS
reuses the numeric column name). The AS regions NEST, and the rows are per-constraint
shadow-price contributions, not totals: a resource's settlement ASMP is the SUM over the
regions containing it (`AS_CAISO + AS_CAISO_EXP` + its own sub-region's `AS_NP26[_EXP]` or
`AS_SP26[_EXP]` adder). Verified in-data: the sub-region rows are near-always 0 and always
small against the system row, impossible were rows totals. Purpose: the measured price leg of
the CAISO storage AS-revenue identification (D-9 value-stack lane,
`scripts/probes/caiso_storage_as_revenue_phase0.py`, joined to `data/raw/storage-as-awards/CAISO`).

## Q2-2020 extension (caiso-263, 2026-09-07)

Fetched 2026-09-07 by `scripts/data/fetch_caiso_oasis.py --datasets asresults asprc_ru
asprc_rd asprc_sr asprc_nr --years 2020 --start-date 2020-04-01 --end-date 2020-07-01`
plus a `--start-date 2020-03-31 --end-date 2020-04-01` head window (see the DST note
below). Coverage **verified complete: 2,184 of 2,184 (day, hour) pairs** — 91 days ×
24 h — for `asresults` and all four `asprc_*` products. `asreq` already carried a
contiguous 2019-12-27 → 2021-01-05 chain, so its Q2-2020 re-fetch was a pure duplicate
(0 new days, rows identical modulo the response-sequence `GROUP` column) and was
deleted rather than committed.

**The "train years only" scope stated for the 2023–2025 intakes above is SUPERSEDED**
by the 2026-08-06 owner clarification carried in rule 22 `[R-HOLDOUT]`: *what is held
out is the SCORE, never the DATA* — measured inputs are collected once and applied
consistently across every year, and data intake needs no marker or authorization. Only
solving, scoring or registering an out-of-training year is the spend. Nothing here was
solved, folded, derived or scored.

**DST head-window note (applies to EVERY window fetch in this corpus).**
`fetch_caiso_oasis.UTC_OFFSET_HOURS = 8` is PST, so in a PDT month a window's first
request instant lands at 01:00 local, not midnight: the first trade date of a fetched
range loses `OPR_HR 1` and the range spills one hour into the day after its end. Inside
a contiguous chain this is invisible (each window's missing head hour is the previous
window's tail), but it bites at the START of any range — 2020-04-01 came back with
HE2–HE24 only. Fixed here by fetching the preceding day's window; check `OPR_HR 1` of
the first day whenever a new range is opened.

**Why there are no 2020 LMPs beside these.** MEASURED 2026-09-07: the OASIS `GroupZip`
bulk endpoint has its own retention boundary at **2021-04-27** (`DAM_LMP_GRP` v12;
2021-04-26 → "No data returned"), and the per-node `SingleZip` `PRC_LMP` boundary is far
later still, so 2020 hub / DLAP prices are unobtainable from OASIS by any endpoint. The
AS reports and `SLD_FCST` carry no such window. Details:
`data/raw/lmp-data/CAISO/README.md`.
