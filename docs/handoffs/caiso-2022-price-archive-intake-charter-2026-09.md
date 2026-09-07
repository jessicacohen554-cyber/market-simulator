# CAISO 2022 hourly price archive — SOURCE ADJUDICATED, load chartered (caiso-261, 2026-09-06)

**Owner decision (card, 2026-09-06): "Fund an hourly price archive" — source
adjudication first, rule-14 alignment adjudicated, and only then charter the
load.** This document is that adjudication and that charter. **Nothing was
loaded, folded, derived or scored; no 2022 model output exists.** Rule 22:
CAISO now holds the `complete` marker (validation tier), so a 2022 rung is
authorizable once the inputs exist; this document prepares inputs only.

## §1 — The gap (caiso-259 §1 H-2/H-3)

The OASIS **per-node** API (`SingleZip?queryname=PRC_LMP` / `PRC_INTVL_LMP`)
has a ~39-month retention window that aged past 2022 in 2026 (boundary
2023-04-22 on 2026-08-04). Re-probed 2026-09-06: `PRC_LMP DAM
TH_SP15_GEN-APND 2022-06-01` → HTTP 200 with a 648-byte "no data" XML;
the same query for 2024-06-01 → data. The measured 2022 hub LMPs
(`actual_lmp_hourly_CAISO.parquet`, C3a/C3b/C3c basis) and the 2022
intertie hub series (`wecc_intertie_lmp_hourly_CAISO.parquet`, the
caiso-87/93/94 injector input) were therefore unfetchable — H-2 / H-3.

## §2 — THE SOURCE: the same publisher's bulk endpoint still serves 2022

**OASIS `GroupZip` all-node bulk archives are NOT subject to the per-node
retention.** Measured 2026-09-06 through the session proxy:

| request | result |
|---|---|
| `GroupZip?groupid=DAM_LMP_GRP&startdatetime=20220601T07:00-0000&version=1&resultformat=6` | **HTTP 200, 12.3 MB zip** (`Content-Disposition: 20220601_20220601_DAM_LMP_GRP_N_N_v1_csv.zip`), two component CSVs (`PRC_LMP_DAM_LMP`, `PRC_LMP_DAM_MCE`, ~62 MB each), every node; **TH_NP15/TH_SP15/TH_ZP26 (72 rows = 3 hubs × 24 h), MALIN_5_N101, PALOVRDE_5_N101, PALOVRDE_ASR-APND, BPAT_MALIN-APND, DLAP_PGAE/SCE/SDGE/VEA-APND all present** |
| `GroupZip?groupid=RTM_LMP_GRP&startdatetime=20220601T07:00-0000&…` | **HTTP 200, 7.5 MB zip**, one component `PRC_INTVL_LMP_RTM_01_v1.csv` (138 MB): **ONE operating hour per request** (OPR_HR 01, 12 five-minute intervals × 4 LMP types × ~16.6k nodes); TH_SP15 present (48 rows) |

This is exactly the route `scripts/data/fold_caiso_oasis_grp_zips.py` was
built for ("the only route to history that has aged out of the OASIS API's
~39-month retention"), used to fill the 2023-01-01..03-09 hole; its `NODES`
already keep the three hubs, the WECC intertie nodes (`INTERTIE_NODES`)
and the four DLAPs, and its window fold handles the RTM hour-group zips
("group-numbered zips (RTM hour groups) append into the same day window").
The downstream pipeline is unchanged: `postprocess_oasis_downloads.py`
folds `dam_grp_*` / `rtm_grp_*` windows into
`CAISO_dam_hourly_2022.csv` / `CAISO_rtm_hourly_2022.csv`, and
`derive_actual_lmp.py` load-weights the hubs (`CAISO_HUB_WEIGHTS`) into
the scored system price.

## §3 — Rule-14 alignment: EXACT, no reconciliation needed

Same publisher (CAISO OASIS), same reports (`PRC_LMP` DAM hourly,
`PRC_INTVL_LMP` RTM 5-minute averaged to the hour), same nodes, same
components (LMP = MCE + MCC + MCL; the intertie builder drops MGHG), same
hub weights, same clock handling. The 2022 series enters through the
identical fold → postprocess → derive chain the 2023–2025 series came
through, so **there is no aggregation, boundary or basis difference to
reconcile** — the rule-14 misalignment exception is not engaged. Third-party
archives (gridstatus.io — 403 to this environment; ISO-DART; the daily
EIA/ICE indices) are NOT needed and are rejected in favour of the primary
source (rule 14 `[R-ACCURATE]`).

## §4 — THE LOAD, sized (not executed)

| half | requests | transfer | time at ≥ 6 s/request (OASIS AUP throttle) | disk |
|---|--:|--:|--:|---|
| **DAM 2022** (`DAM_LMP_GRP`, 1 request/day) | 365 | ≈ 4.4 GB | **≈ 1 h** | extract-and-discard per day (each zip is dropped after its window CSV is written; the kept windows are a few MB) |
| **RTM 2022** (`RTM_LMP_GRP`, 1 request/**hour**) | 8,760 | ≈ 65 GB | **≈ 24 h** (5 s download + 6 s spacing) | same |

The scored C3a / C3b / C3c basis is the **RT** hourly hub price (rubric
v2.7, RT everywhere), and C3b/C3c use the DA count only as a diagnostic;
the intertie injector needs **DAM**. So DAM alone buys **H-3** (the 2022
import structure) and the DA diagnostic row; **H-2 (the scored price)
needs RTM.** A 15-minute `RTPD` substitute would be a basis change and is
refused (rule 14).

Steps, for the lane that executes it (Opus/Fable — it touches
`scripts/data/`):
1. A small `fetch_caiso_oasis_grp.py` (or a `--grp` mode on
   `fetch_caiso_oasis.py`): for each 2022 trade date, `GroupZip` DAM (and,
   if funded, the 24 RTM hour groups), saved under the `Content-Disposition`
   filename into `data/raw/lmp-data/CAISO/` so `_GRP_NAME` matches; sleep
   ≥ 6 s; back off on 429/403; detect the "Acceptable Use Policy" HTML
   body; **run `fold_caiso_oasis_grp_zips.py` incrementally and delete each
   zip after its window exists** (20 GB disk allowance).
2. `postprocess_oasis_downloads.py` → `CAISO_dam_hourly_2022.csv` /
   `CAISO_rtm_hourly_2022.csv`; `derive_actual_lmp.py` (the
   `CAISO_MIN_HOURS = 6500` guard must pass on a full year).
3. **Intertie parquet for 2022**: `fetch_caiso_intertie_lmp.py` reads the
   per-node API only (`_fetch_node_year`); extend it (or add a sibling) to
   build the 2022 MALIN / PALOVRDE rows from the folded `dam_grp_*` windows,
   summing MCE + MCC + MCL exactly as its docstring specifies, onto the
   dense 8760 local calendar. Byte-identity assertion on the 2023–2025 rows
   before any write.
4. Then, and only then, `derive_actual_tail.py` (marker-gated; CAISO now in
   `complete`) emits the 2022 tail row, the H-1 demand artifact is built
   (its own PRECOMMIT), S-1 (2022 CARB allowance prices) / S-2 (DMM 2022
   RA-import row) / S-4 (NRC 2022 windows) are prepared, S-3 (static clean
   depths — derivable now that H-3 lands) is derived, and the rung runs
   under `--holdout-authorized` on the frozen caiso-260 recipe, stamped to
   the keeper (rule 30(a)).

## §5 — Owner decision needed before the load runs

DAM only (~1 h; buys H-3 and the DA diagnostic; C3a/C3b/C3c still SKIPPED
in 2022) — or DAM + RTM (~1 day of background fetching; buys the scored
price) — and whether to run it in this session or a fresh one.

## §6 — Owner decision (card, 2026-09-06): "DAM now, RTM in a fresh session" — EXECUTED (DAM)

* **Source verification, strongest form:** a GroupZip re-download of the
  2023-01-01 DAM v12 archive reproduces the byte-pinned manifest line in
  `data/raw/lmp-data/CAISO/SHA256SUMS.txt` **sha256-identical** (`6523fedd…`).
  The README's "Re-fetchability: NONE" claim is corrected in place.
* **Fetcher landed:** `scripts/data/fetch_caiso_oasis_grp.py` (GroupZip per
  trade date, version 12 for DAM / 3 for RTM, local-midnight-in-UTC start,
  Content-Disposition filename, AUP-throttle detection, extract-and-discard
  through `fold_caiso_oasis_grp_zips.fold`, resumable, JSON summary).
* **Intertie builder extended:** `fetch_caiso_intertie_lmp.py
  --from-grp-windows` builds the MALIN / PALOVRDE delivered LMP from the
  folded windows with the same `_to_hourly_nodal_lmp` construction; existing
  (year, hub) rows are never touched (row-identity asserted before commit).
* **The 2022 DAM crawl ran in session caiso-261**; its result (dates fetched /
  missing, the aggregate written, the intertie rows) is in the caiso-261
  closing addendum of `docs/calibration-log/caiso.md`.
* **RTM 2022 → a fresh session** on this charter: size the hour-group
  delivery first (`RTM_LMP_GRP` at `version=3` was 7 groups/day in the
  tracked Jan-2023 zips; at `version=1` one operating hour per request), then
  crawl with `--market rtm`, fold, `postprocess_oasis_downloads.py`,
  `derive_actual_lmp.py` (RT + DA), `derive_actual_tail.py`.

**RESULT (2026-09-07):** DAM 2022 crawled 365 / 365, 0 missing, 1.56 h; `CAISO_dam_hourly_2022.csv` (87,600 rows, 10 nodes) and the 2022 MALIN / PALOVRDE rows in `wecc_intertie_lmp_hourly_CAISO.parquet` committed; 2023–2026 inputs byte-/row-identical. H-3 is CLOSED. H-2 (RT) waits on the RTM crawl — fresh session.
