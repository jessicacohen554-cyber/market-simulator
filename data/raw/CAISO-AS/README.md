# CAISO-AS — DAM ancillary services: requirements (AS_REQ), clearing prices (PRC_AS), results (AS_RESULTS)

Fetched 2026-07-10 by `scripts/fetch_caiso_oasis.py --datasets asreq --years 2023 2024 2025`
(CAISO OASIS `SingleZip?queryname=AS_REQ&market_run_id=DAM&version=1&anc_type=ALL&anc_region=ALL`,
adaptive ≤25-day windows, resumable). Coverage verified complete: every day 2023-01-01 →
2025-12-31 (1,096 days), 44 window CSVs, **since extended to 2018-2022 + H1-2026** (15/15/14/15/15
window files for 2018-2022, 8 for H1-2026; `docs/holdout-data-equivalency-register-2026-07.md`
§CAISO). `AS_REQ` carries **no** OASIS retention limit, unlike `PRC_LMP`.

*(This paragraph formerly read "**Train years only** (CLAUDE.md rule 22 — no 2022, no H1-2026)".
That was already false of the files on disk, and it misstates the rule: rule 22 `[R-HOLDOUT]` as
amended 2026-08-06 holds out the **SCORE, never the DATA** — "an input is either the best measured
representation of a physical/market quantity or it is not, and if it is, it belongs in **every**
year". Intake needs no marker and no per-window authorization; what stays gated is solving, scoring
or registering an out-of-training year.)*

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

## asresults — DAM ancillary-service market results (OASIS AS_RESULTS)

Content section for the series the Q2/Q3-2020 extensions introduced (it had been registered
in `scripts/data/fetch_caiso_oasis.py` but marked "not yet fetched in bulk" until 2026-09-07).

Hourly procured MW per AS region and product. `XML_DATA_ITEM`
`{SP,NS,RU,RD,RMU,RMD}_{TOT,SPROC,PROC}_MW` plus `_TOT_CST_PRC` — i.e. total procurement
(market + self), self-provided, and market-procured legs carried separately. Purpose: the
measured TOTAL-procurement denominator across all resource types. The battery-held award
itself comes from the Daily Energy Storage Report intake (`data/raw/storage-as-awards`), so
this series is the battery-share denominator and the eventual measured replacement for the
`as_reserve_formula` scaffold. Same `ANC_REGION` nesting as `asprc` above.

## Q3-2020 extension (caiso-oasis-q3-2020, 2026-09-07)

Fetched 2026-09-07 by `scripts/data/fetch_caiso_oasis.py --datasets asresults asprc_ru
asprc_rd asprc_sr asprc_nr --years 2020 --start-date 2020-07-01 --end-date 2020-10-01`,
4 windows per series. Extends the Q2-2020 chain above to **2020-04-01 → 2020-10-01
contiguous** for `asresults` and all four `asprc_*` products.

**The DST head-window note above bit this range too, and the Q2 chain is what repairs it.**
2020-07-01 came back HE2–HE24 (23 h) in all five series, exactly as that note predicts for
the first trade date of a PDT-month range. No head window was fetched for it, because the
Q2 lane's own tail window (`*_ALL_20200615_20200701.csv`) already carries 2020-07-01 **HE1**
and nothing else — the "invisible inside a contiguous chain" case. **Verified across the
rebase**, per series: Q2-tail tail-day = 2020-07-01, hours = [1]; Q3 first day = 2020-07-01,
hours = HE2–HE24. Read the two together and Q3 is 2,208/2,208 (day, hour) pairs, 92 days ×
24 h. Read the Q3 files ALONE and 2020-07-01 is short one hour — so any consumer that globs
only the Q3 windows must be checked against this.

Row counts as fetched: `asresults` 229,632; each `asprc_*` 13,248; 6 AS regions throughout.
The trailing `2020-10-01` rows are the same one-hour spill the DST note describes (HE1 only,
from the exclusive end bound) and are the head hour for whatever range opens Q4.

`asreq` and `load` were NOT re-fetched for Q3: `asreq` already carried the contiguous
2019-12-27 → 2021-01-05 chain, and
`data/raw/zone-specific-demand/CAISO/CAISO_tac_load_hourly_2020.csv` already covered Q3.
Re-running `asreq` at Q3-aligned window boundaries would additionally have written
overlapping duplicate files, since the fetch script's skip check keys on the exact
`{start}_{end}` filename, not on day coverage.

## Q4-2020 extension (caiso-oasis-q4-2020, 2026-09-07)

Fetched 2026-09-07 by `scripts/data/fetch_caiso_oasis.py --datasets asresults asprc_ru asprc_rd
asprc_sr asprc_nr --years 2020 --start-date 2020-10-01 --end-date 2021-01-01`, 4 windows per
series. Extends the chain above to **2020-04-01 → 2021-01-01 contiguous** for `asresults` and all
four `asprc_*` products, closing the year from April.

**The DST head-window case again, and again the chain repairs it — read this before adding files.**
2020-10-01 comes back HE2–HE24 (23 h) in the Q4 windows alone, exactly as the note above predicts
for the first trade date of a PDT-month range. **No head window is committed for it**: the Q3
lane's tail window (`*_ALL_20200914_20201001.csv`) already carries 2020-10-01 **HE1** and a
complete 2020-09-30, so the hour is present in the chain. Verified per series across the rebase.
A `--start-date 2020-09-30 --end-date 2020-10-01` head window WAS fetched here before the Q3 lane
landed, found to be fully contained in that Q3 tail, and **deleted rather than committed** — the
same call the Q2 lane made on its duplicate `asreq` re-fetch, and for the same reason: overlapping
windows are duplicate rows the skip check cannot see, because it keys on the exact
`{start}_{end}` filename rather than on day coverage.

Read together with the Q3 tail, Q4 is **2,209 of 2,209 (day, hour) pairs** — 92 days × 24 h, plus
the legitimate 25th hour of **2020-11-01, the DST fall-back day**. Read the Q4 files ALONE and
2020-10-01 is short one hour, so any consumer that globs only the Q4 windows must be checked
against this, exactly as for Q3. Row counts as fetched: `asresults` 229,632; each `asprc_*`
13,248; 6 AS regions throughout. The end bound is exclusive and January is PST, so there is no
spill day past 2020-12-31.

**A verification trap worth recording, because it defeats the obvious check.** Both a total-row
count and a distinct-(day, hour) count PASS on this range even with 2020-10-01 missing its HE1:
the short day and the 25-hour November fall-back day cancel EXACTLY, giving 92 × 24 × 104 rows and
2,208 pairs — both matching a naive expectation. Only a per-day hour-count histogram surfaces the
gap. **Never verify a CAISO window range by totals alone.** Histogram the hours per day and expect
25 on the November fall-back day, 23 on the March spring-forward day, and 23 on the first trade
date of any range opened in a PDT month.

`asreq` and `load` were NOT re-fetched for Q4, for the reasons the Q3 section gives: `asreq`
already carries the contiguous 2019-12-27 → 2021-01-05 chain, and
`CAISO_tac_load_hourly_2020.csv` already covers Q4 in full.

**Why there are no 2020 LMPs beside these** — governed by the Q2 section's measurement: the
`GroupZip` bulk endpoint has its own retention boundary at 2021-04-27, so 2020 hub / DLAP prices
are unobtainable from OASIS by **any** endpoint. Re-probed independently here at 2020-10-01:
`PRC_LMP` and `PRC_INTVL_LMP` both return `ERR_CODE 1000`. Note this **contradicts**
`docs/holdout-data-equivalency-register-2026-07.md` §CAISO N-CA-1, which still advises the
hand-downloaded GRP bulk zip as the route to aged-out history; that advice predates the
bulk-endpoint measurement and holds only back to 2021-04-27.

**Size:** `asresults` is ~8.4 MB per 25-day window (~31 MB per quarter) — these raws are committed
as-is, since `postprocess_oasis_downloads.py` folds only the LMP and TAC-load series into hourly
aggregates and never touches `CAISO-AS`. Q2+Q3+Q4 2020 together are ~93 MB; extending `asresults`
across all of 2018-2022 at this grain would add roughly 500 MB, so fold it to an hourly aggregate
before going wider.

## Coverage by year

| series | 2020 | 2021 | 2022 | 2023–2025 |
| --- | --- | --- | --- | --- |
| `asreq` | full year (2019-12-27 → 2021-01-05) | **full year** (365/365) | 2022-01-15 → 2022-03-06 only | complete |
| `asprc_{ru,rd,sr,nr}` | **Q2+Q3+Q4** (2020-04-01 → 2021-01-01) | **Q1** (2021-01-01 → 2021-04-01) | — | complete |
| `asresults` | **Q2+Q3+Q4** (2020-04-01 → 2021-01-01) | **Q1** (2021-01-01 → 2021-04-01) | — | — |

Nothing in any of these extensions has been solved, folded, derived or scored.

## Q1-2021 extension (caiso-264, 2026-09-07)

Fetched 2026-09-07 by `scripts/data/fetch_caiso_oasis.py --datasets asresults asprc_ru
asprc_rd asprc_sr asprc_nr --years 2021 --end-date 2021-04-01`. Coverage **verified
complete: 2,159 of 2,159 (day, hour) pairs** — 89 × 24 h plus the 23-hour DST
spring-forward day 2021-03-14 (CAISO skips `OPR_HR 3`) — for `asresults` and all four
`asprc_*` products. No head-window loss: Q1 is PST throughout, so
`fetch_caiso_oasis.UTC_OFFSET_HOURS = 8` puts the first request instant at local
midnight and `2021-01-01 HE1` is present; the range's single tail spill is
`2021-04-01 HE1`, exactly as the DST note above describes.

`asreq` already carried Q1-2021 in full (the 2020-12-11 → 2021-01-05 window bridges
Jan 1–4), so its re-fetch was a pure duplicate — **112,320 overlapping (day, hour,
region, product, item) keys, 0 value mismatches, 0 keys not already present** — and the
four redundant windows were deleted rather than committed, as caiso-263 did for Q2-2020.
The zero-mismatch cross-check is also an independent confirmation that OASIS serves this
vintage reproducibly.

Companion in the same session: `CAISO_tac_load_hourly_2021.csv` gained **MWD-TAC** for
Q1 (2,160 rows added, 0 removed, 0 changed in place), closing part of the caiso-175 gap
— MWD was added to `postprocess_oasis_downloads.CAISO_TACS` on 2026-08-05 but only the
2023–2025 aggregates were rebuilt, so 2019–2022 still carry five areas and
`load_zonal_shares` re-apportions MWD's ~126–172 MW pro rata across the other four
(rule 14 `[R-ACCURATE]`). **2019, 2020 and 2022 remain five-area and are still open.**

**No LMPs accompany this intake, and none can.** The GroupZip boundary was
**re-measured in this session** and is unchanged at **2021-04-27** (`DAM_LMP_GRP` v12:
2021-03-31 and 2021-04-26 → 3,018-byte "No data returned"; 2021-04-27 → 9.85 MB,
2021-04-28 → 9.90 MB), so all of Q1-2021 sits before it on both the GroupZip and the
per-node `SingleZip` endpoints. Details: `data/raw/lmp-data/CAISO/README.md`.

Scope note as in the Q2-2020 section: intake only. Nothing here was solved, folded into
a clean datatype, derived or scored (rule 22 `[R-HOLDOUT]` — what is held out is the
score, never the data).
