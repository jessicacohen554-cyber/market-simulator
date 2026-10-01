# FINDING — F2: CAMPD outage coverage 2019–2025, every ISO (data intake + derive; zero LP)

Charter: `docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md` §5.2 (owner instruction
2026-09-24: granular CAMPD outage data for every ISO and every backcast year 2019–2025). Branch
`claude/f2-campd-outage-coverage`, cut from `origin/main` at `fd04cfda`. **No LP was run, nothing was
registered, no flag was armed or flipped, no keeper shard or `frontend/data/backcast/**` file was touched,
and no `ScenarioConfig` field was added.**

## 0. Result

- **Raw:** 42 CAMPD state-year extracts landed (141 MB). Every `campd.ISO_STATES` state now has an extract
  for every year 2019–2025.
- **Coverage:** every ISO carries std / short-coal / short-gas / partial-derate files. ERCOT's partial
  family is its own plant-grain path. Every family spans 2019–2025, with three exceptions, all explained
  in §2: the PJM partial file (2023–25 only; it does not reproduce at HEAD), and the MISO / PJM std and
  PJM short-coal files, whose 2019–25 rows exist but no longer reproduce at HEAD.
- **Byte identity:** the armed std extract reproduces 2023–2025 byte-for-byte in **7 of 9 ISOs**. The two
  that do not are **MISO** and **PJM** (§3). Their committed files were left untouched: nothing a keeper
  reads for 2023–2025 changed in any ISO.
- **One code change**, forced by the raw landing: `campd.ISO_MERIT_PANEL_STATES` pins SPP and SOCO to their
  pre-landing states (§4). Without it, the new CO / FL files would have re-identified those ISOs' layup
  classifier. With the pin, SPP short-gas 2023–25 is byte-identical again.

## 1. Raw intake (deliverable 1)

The list was **derived rather than copied from the audit**: every `ISO_STATES` state × 2019–2025 with no
extract on disk. It was then cross-checked against each ISO's fleet (`load_fleet_from_csv` +
`load_retired_within_window`, qualifying + CT classes, plant state from EIA-860):

| state | years fetched | ISO | note |
|---|---|---|---|
| AL, GA | 2019–2022 | SOCO | |
| ID, OR, UT, WA, WY | 2019–2022 | NWPP | |
| FL | 2019–2025 | SOCO | SOCO's three FL fleet plants (10416, 50250, 56522) file **no** CEMS rows in any year, so FL adds no SOCO window |
| CO | 2019–2025 | SPP (listed) | no fleet combustion unit in any ISO; landed only to complete the listed scope; inert |
| AZ | **not fetched** | — | the audit listed it for NWPP, but no ISO's fleet has a plant there (landed 2023–25 only as NWPP-47 attribution evidence) |

Fleet plants that sit outside their ISO's listed states (**not changed here, routed**):
- **ERCOT — Tenaska Kiamichi** (EIA 55501, 1,224 MW CC_REGULAR on ERCOT's bin sheet, CEMS filed under
  **OK**). `ISO_STATES["ERCOT"] = ("TX",)`, so ERCOT's outage derivation never scans it. OK extracts exist
  for every year. Adding OK would add Kiamichi windows to ERCOT 2023–2025, which would break the
  byte-identity this lane must hold, and `ISO_STATES` also feeds solve-time loaders. → **R-ERCOT**.
- **MISO — MT** (Glendive, Miles City, Lewis & Clark; 117 MW). All are CT_PEAKER, which the overlay skips,
  so this is inert.

Fetch: `scripts/data/fetch_campd_unit_level.py` (EPA CAM-API bulk files, DEMO_KEY). One HTTP 429 on CO/FL
2019 cleared on the first retry. Every file passed the fetcher's sibling-schema and single-year
assertions. The per-file rows / facilities / units table is in `data/raw/campd-unit-level/README.md`.
Nothing was blocked.

## 2. Coverage table (deliverable 3)

Cell = **windows starting that year / MW-weighted outage share (%)**. The share is
Σ(removed MW × duration h) / (family fleet MW × hours in year). Removed MW is `unit_capacity_mw`, or
`(1 − derate_factor) × unit_capacity_mw` for partial. The family fleet MW is the ISO's **snapshot** fleet +
within-window retirees in the family's groups (std: `QUALIFYING_PLANT_GROUPS`; short-coal / partial: COAL;
short-gas: `_SHORT_GAS_GROUPS`). ERCOT's fleet MW comes from the bin sheet. Because the denominator is a
snapshot rather than year-matched, compare the share within a row, not across ISOs. Files are the
ISO-resolved paths in `data/raw/`; std is each keeper's **armed** form.

| ISO | family | file | fleet MW | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ERCOT | std | `campd-unit-outages.csv` | 72,889 | 825 / 14.86 | 972 / 18.43 | 998 / 19.25 | 744 / 14.25 | 601 / 13.43 | 734 / 15.5 | 655 / 15.71 |
| ERCOT | short-coal | `campd-unit-outages-short.csv` | 13,964 | 24 / 0.92 | 21 / 0.65 | 20 / 0.86 | 30 / 0.95 | 15 / 0.63 | 27 / 1.1 | 40 / 1.84 |
| ERCOT | short-gas | `campd-unit-outages-shortgas.csv` | 56,470 | 506 / 1.46 | 460 / 1.24 | 461 / 1.21 | 452 / 1.16 | 382 / 1.11 | 397 / 1.07 | 428 / 1.43 |
| ERCOT | partial | (plant-grain campd-partial-outages-shaped.csv, ERCOT own path) | 13,964 | — | — | — | — | — | — | — |
| CAISO | std | `campd-unit-outages-CAISO.csv` | 23,355 | 576 / 20.79 | 555 / 19.76 | 603 / 20.84 | 496 / 17.7 | 584 / 19.45 | 499 / 23.15 | 670 / 28.74 |
| CAISO | short-coal | `campd-unit-outages-short-CAISO.csv` | 50 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| CAISO | short-gas | `campd-unit-outages-shortgas-CAISO.csv` | 21,343 | 398 / 3.17 | 320 / 2.76 | 296 / 2.36 | 404 / 3.07 | 402 / 3.03 | 361 / 3.24 | 435 / 4.43 |
| CAISO | partial | `campd-partial-outages-CAISO.csv` | 50 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| MISO | std | `campd-unit-outages-unitroute-MISO.csv` | 103,361 | 1223 / 23.29 | 1392 / 31.37 | 1379 / 26.02 | 1253 / 23.64 | 1210 / 26.11 | 1255 / 25.67 | 1194 / 25.12 |
| MISO | short-coal | `campd-unit-outages-short-MISO.csv` | 51,059 | 121 / 0.98 | 91 / 0.72 | 146 / 1.09 | 138 / 1.11 | 109 / 0.88 | 75 / 0.6 | 106 / 0.89 |
| MISO | short-gas | `campd-unit-outages-shortgas-MISO.csv` | 49,677 | 325 / 1.13 | 260 / 0.97 | 410 / 1.32 | 424 / 1.41 | 321 / 1.12 | 310 / 1.06 | 330 / 1.09 |
| MISO | partial | `campd-partial-outages-MISO.csv` | 51,059 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| NEISO | std | `campd-unit-outages-NEISO.csv` | 15,236 | 457 / 45.15 | 401 / 39.19 | 373 / 39.11 | 321 / 34.2 | 338 / 38.15 | 289 / 32.73 | 260 / 21.03 |
| NEISO | short-coal | `campd-unit-outages-short-NEISO.csv` | 108 | 0 / 0.0 | 0 / 0.0 | 3 / 5.62 | 0 / 0.0 | 1 / 1.75 | 0 / 0.0 | 0 / 0.0 |
| NEISO | short-gas | `campd-unit-outages-shortgas-NEISO.csv` | 14,861 | 138 / 1.96 | 115 / 1.71 | 135 / 1.95 | 134 / 2.04 | 119 / 1.69 | 99 / 1.69 | 124 / 1.81 |
| NEISO | partial | `campd-partial-outages-NEISO.csv` | 108 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| NWPP | std | `campd-unit-outages-NWPP.csv` | 24,238 | 691 / 18.36 | 708 / 22.6 | 658 / 16.34 | 731 / 19.5 | 719 / 17.99 | 790 / 19.27 | 761 / 24.77 |
| NWPP | short-coal | `campd-unit-outages-short-NWPP.csv` | 8,104 | 112 / 3.93 | 86 / 2.91 | 104 / 3.53 | 95 / 3.32 | 70 / 1.71 | 61 / 1.5 | 78 / 2.66 |
| NWPP | short-gas | `campd-unit-outages-shortgas-NWPP.csv` | 15,784 | 1603 / 7.14 | 1647 / 7.16 | 1638 / 6.31 | 1913 / 7.32 | 1114 / 4.82 | 1053 / 5.23 | 622 / 4.22 |
| NWPP | partial | `campd-partial-outages-NWPP.csv` | 8,104 | 32 / 2.52 | 31 / 2.21 | 43 / 2.45 | 18 / 0.93 | 52 / 1.97 | 37 / 1.45 | 22 / 1.16 |
| NYISO | std | `campd-unit-outages-perunitmerithour-NYISO.csv` | 22,553 | 540 / 47.05 | 519 / 48.2 | 526 / 38.1 | 512 / 41.68 | 519 / 36.81 | 461 / 37.75 | 492 / 38.8 |
| NYISO | short-coal | `campd-unit-outages-short-NYISO.csv` | 1,487 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| NYISO | short-gas | `campd-unit-outages-shortgas-NYISO.csv` | 20,620 | 149 / 0.97 | 188 / 1.32 | 146 / 1.18 | 206 / 1.8 | 136 / 0.99 | 133 / 0.95 | 169 / 1.37 |
| NYISO | partial | `campd-partial-outages-NYISO.csv` | 1,487 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 |
| PJM | std | `campd-unit-outages-PJM.csv` | 122,155 | 1255 / 24.67 | 1118 / 25.84 | 1379 / 26.41 | 1321 / 26.55 | 1372 / 29.29 | 1364 / 25.47 | 1271 / 23.76 |
| PJM | short-coal | `campd-unit-outages-short-PJM.csv` | 49,642 | 113 / 0.88 | 87 / 0.65 | 125 / 0.97 | 134 / 0.86 | 94 / 0.6 | 85 / 0.55 | 106 / 0.7 |
| PJM | short-gas | `campd-unit-outages-shortgas-PJM.csv` | 71,690 | 246 / 0.67 | 283 / 0.82 | 291 / 0.78 | 409 / 1.21 | 317 / 0.94 | 323 / 0.94 | 236 / 0.59 |
| PJM | partial | `campd-partial-outages-PJM.csv` | 49,642 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 0 / 0.0 | 43 / 1.13 | 24 / 0.61 | 9 / 0.25 |
| SOCO | std | `campd-unit-outages-perunitdark-SOCO.csv` | 34,576 | 382 / 26.95 | 312 / 31.82 | 341 / 29.3 | 296 / 25.46 | 332 / 28.37 | 356 / 27.86 | 432 / 29.03 |
| SOCO | short-coal | `campd-unit-outages-short-SOCO.csv` | 11,512 | 22 / 0.86 | 13 / 0.69 | 19 / 0.75 | 23 / 1.16 | 8 / 0.3 | 10 / 0.48 | 16 / 0.79 |
| SOCO | short-gas | `campd-unit-outages-shortgas-SOCO.csv` | 22,728 | 307 / 2.51 | 284 / 2.48 | 282 / 2.26 | 326 / 2.63 | 324 / 3.01 | 351 / 3.23 | 314 / 2.74 |
| SOCO | partial | `campd-partial-outages-SOCO.csv` | 11,512 | 7 / 0.42 | 3 / 0.15 | 10 / 1.46 | 24 / 2.02 | 5 / 0.28 | 0 / 0.0 | 7 / 0.78 |
| SPP | std | `campd-unit-outages-SPP.csv` | 42,204 | 943 / 36.83 | 932 / 38.26 | 982 / 36.9 | 946 / 34.36 | 912 / 36.54 | 939 / 35.48 | 973 / 33.14 |
| SPP | short-coal | `campd-unit-outages-short-SPP.csv` | 20,695 | 181 / 2.75 | 239 / 3.51 | 379 / 5.92 | 270 / 4.46 | 163 / 2.85 | 211 / 3.55 | 246 / 3.89 |
| SPP | short-gas | `campd-unit-outages-shortgas-SPP.csv` | 21,166 | 906 / 4.67 | 934 / 5.47 | 1160 / 7.07 | 1071 / 6.98 | 935 / 5.8 | 840 / 5.0 | 1063 / 6.12 |
| SPP | partial | `campd-partial-outages-SPP.csv` | 20,695 | 36 / 0.76 | 29 / 0.4 | 17 / 0.42 | 37 / 0.92 | 18 / 0.6 | 41 / 0.94 | 26 / 0.75 |

**Empty / short cells, explained:**
- **CAISO / NYISO short-coal and partial: 0.** Neither ISO has a coal unit passing the baseload guard
  (when-operable CF ≥ 0.55) in 2019–2025. CAISO carries 50 MW of coal; NYISO carries 1,487 MW, all of it
  retired or low-CF units such as Somerset and Cayuga.
- **NEISO short-coal and partial: ~0.** Coal is 108 MW (Merrimack), baseload in almost no year.
- **MISO partial: 0 in every year**, both committed (MISO meta: 0 rows) and at HEAD, against 51 GW of coal.
  This matches the committed file, so it is not drift. It is still implausible next to SPP / NWPP / SOCO
  producing windows, so it is flagged for **R-MISO** as an open question: MISO effectively has no
  unit-partial family.
- **PJM partial 2019–2022: none.** See §3. HEAD emits 0 windows in every year, while the committed file
  (pjm-111 era) carries 43 / 24 / 9 in 2023–25. The committed file was left untouched and not extended.
- **ERCOT partial:** ERCOT's own plant-grain `campd-partial-outages-shaped.csv` (2018–2026) is the ERCOT
  path. The unit-grain file is non-ERCOT by construction (`unit_partial_outage_csv_for_iso`).
- **NWPP short-gas** runs 1,600–1,900 windows/yr in 2019–22 against 600–1,100 in 2023–25. The merit guard
  was live every year, but the NWPP panel is thin (32–40 priced units vs 220–1,017 elsewhere), so the
  guard separates less. The count is reported as the detector's output. Whoever arms it (R-NWPP) should
  read it with that in mind.
- **Maxgen** (`campd-unit-outages-maxgen-unitroute-MISO.csv`, armed in the MISO keeper) is outside the
  four F2 families and still spans 2023–2025 only. → **R-MISO**.

## 3. 2023–2025 byte-identity proof, per ISO (deliverable 2)

Method: each family was re-derived with `scripts/data/derive_campd_unit_outages.py --years 2019..2025`, using
the same deriver and frozen constants, with each ISO's armed flags, into a scratch dir. Then, per start
year, the ordered row text of the regenerated extract was compared with the committed file's rows for
that year (`IDENTICAL` = the same lines in the same order).

**Install rule** (fixed before any comparison). A committed file was overwritten **only if** it lacked
2019–2022 rows **and** its 2023–2025 rows (and any other year it carried) regenerated byte-identically.
A file already spanning 2019–2025 (most carry 2018–2026) was **left untouched** even where HEAD drifts in
2019–2022, because rewriting it would change inputs a keeper already solves (NEISO and MISO keepers solve
2020–21). New files were written outright. Every in-place update is a pure line addition (git numstat:
0 deletions).

**Invocation recovery.** Five committed std extracts carry no `.meta.json`. Reproduction shows that ERCOT,
CAISO, NEISO, PJM and MISO-unitroute were derived **with `--merit-order-guard`**, and CAISO additionally
with `--hour-grain`. Unguarded, each regenerates the committed rows exactly *plus* extra rows, and the
extra rows per year equal the committed layup companion's counts.

| ISO | armed std extract (flags) | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | action |
|---|---|---|---|---|---|---|---|---|---|
| ERCOT | `campd-unit-outages.csv` (guard) | = | = | = | = | = | = | = | untouched (already 2018–26) |
| CAISO | `-CAISO` (guard, hour-grain) | +7 | = | = | = | = | = | = | untouched |
| MISO | `-unitroute-MISO` (mixed-gas-routing, guard) | ±23/88 | ±25/45 | ±38/51 | ±35/48 | **−22** | **−19** | **−30** | untouched — **FINDING** |
| NEISO | `-NEISO` (guard) | +18 | +20 | +4 | = | = | = | = | untouched |
| NWPP | `-NWPP` | new 691 | new 708 | new 658 | new 731 | = | = | = | **extended** |
| NYISO | `-perunitmerithour-NYISO` | = | = | = | = | = | = | = | untouched |
| PJM | `-PJM` (guard) | ±110/82 | ±58/69 | ±114/86 | ±107/33 | **−90** | **−74 +1** | **−64** | untouched — **FINDING** |
| SOCO | `-perunitdark-SOCO` (per-unit, dark) | new 382 | new 312 | new 341 | new 296 | = | = | = | **extended** (base `-SOCO` too: = on 2023–25) |
| SPP | `-SPP` | = | = | = | = | = | = | = | untouched |

(`=` identical; `±a/b` = a committed rows not regenerated / b regenerated rows not committed.)

Armed / relevant companions:

| file | 2023–25 | action |
|---|---|---|
| `short-PJM` (**armed**, PJM keeper) | **not identical** (−6+3 / −1+5 / −2) | untouched — **FINDING** |
| `shortgas-PJM` (**armed**, PJM keeper) | = (2020–22 also =) | **extended to 2019** (+246) |
| `short-MISO` (**armed**) | = (2019–22: +11/+8/+3/+8 drift) | untouched |
| `short-SPP` (**armed**) | = (2019–22 =) | untouched |
| `shortgas-SPP` + layup | = **after the §4 pin** (not identical before it) | **extended** 2019–22 |
| `partial-SPP`, `partial-SOCO`, `partial-NWPP`, `short-NWPP`, `short-SOCO`, `short-NEISO` | = | **extended** 2019–22 |
| `partial-PJM` | **not identical** (43/24/9 → 0) | untouched — **FINDING** |
| `short-CAISO`, `short-NYISO`, `partial-CAISO/-NEISO/-NYISO/-MISO` | = (all empty) | untouched |
| new: `short` (ERCOT), `shortgas` (ERCOT/CAISO/MISO/NEISO/NYISO/NWPP/SOCO) + layup companions | — | **written** (with `.meta.json`) |

**The findings (drift at HEAD, reported rather than papered over):**
1. **PJM std.** 2023/24/25 lose 90/74/64 committed windows. 79+49+31+27+24+3+2 of them are on seven
   ST_GAS plants (Edge Moor 593, Martins Creek 3148, Montour 3149, Chalk Point 1571, Joliet 29 384, Clinch
   River 3775, Eddystone 3161) that **pjm-d4-2 (2026-09-10) added to `ST_GAS_PEAKER_PLANTS`**. The deriver
   now skips them, but `outages.py` does **not** re-filter the peaker registry at load time. **The PJM keeper
   therefore still applies ~60–90 windows/yr that its own peaker registry says carry no outage overlay.**
   The rest are Montour coal (12) and Mount Storm (1). → **R-PJM** (re-derive under rule 23, citing the
   registry change, and re-solve).
2. **PJM short-coal (armed).** About 20 coal plants flip in both directions across 2019–2025 at the
   baseload-CF / in-merit edge (e.g. 2023: Brunner Island, Pleasants, Scrubgrass vs John S. Cooper, Kyger
   Creek, Mount Storm, Mt. Carmel). The file dates from pjm-111, and the fleet / EIA-860 inputs have moved
   since. → **R-PJM**.
3. **PJM unit-partial.** 76 → 0 windows at HEAD. Unarmed. → **R-PJM**.
4. **MISO unitroute (armed).** 2023/24/25 lose 22/19/30 windows: New Ulm 2001 ST_CHP (41) and Waterford
   1&2 8056 ST_GAS (30). The HEAD guard books Waterford as layup, which the committed `layup-MISO` companion
   also does, so the committed unitroute file is internally inconsistent with its own layup sibling.
   → **R-MISO**.
5. **NEISO 2019–21** (+18/+20/+4: Capitol District 50498, Pawtucket 54056, West Springfield 1642) and
   **CAISO 2019** (+7: Inland Empire 55853). These plants joined the fleet / retiree set after the extracts
   were derived. The NEISO keeper solves 2020–21. → **R-NEISO / R-CAISO**.
6. **MISO short-coal 2019–22** (+11/+8/+3/+8: E D Edwards 856, Duck Creek 6016, Erickson 1832). → **R-MISO**.

## 4. Code change — SPP / SOCO merit-panel pin

`scripts.lib.outage_detect.build_merit_order_panel` is fleet-blind over the ISO's states. Landing CO and FL
would therefore have admitted every Colorado unit into SPP's clearing-cost panel and every Florida unit
(FPL, Duke FL, TECO, …) into SOCO's. Measured before the fix: **SPP short-gas 2023–2025 moved 13 windows at
five ST_GAS / CC plants with no SPP source-data change.** This is the caiso-198 defect exactly, and it gets
the caiso-199 remedy verbatim: `ISO_MERIT_PANEL_STATES["SPP"]` = every SPP state except CO, and
`["SOCO"] = ("AL", "GA", "MS")`. Detection coverage is unchanged. There are zero free parameters: each pin
is simply the pre-landing state set. After the pin, SPP short-gas and its layup companion are byte-identical
on 2023–25, and SOCO short-gas is byte-identical to its pre-pin derivation (FL carried no effect there).
Tests: `tests/curation/test_campd.py` (`test_pinned_isos`,
`test_f2_pins_exclude_only_the_landed_detection_states`).

This is not a solve-surface change: `ISO_MERIT_PANEL_STATES` is read only by the deriver
(`merit_panel_states_for_iso`), so no keeper replay moves.

**Solve-time reach of the raw landing, checked.** `ISO_STATES` also feeds `run_calibration*`'s CAMPD
frames: the CT must-run shape under `ct_mustrun_per_plant` (off in the SOCO keeper) and the benchmark
`campd` frame. Both key on fleet plant codes downstream (the MS / TX overlap precedent), and SOCO's FL
fleet plants have no CEMS rows. `retiree_availability_caps` reads per-retiree state files, and SOCO and
NWPP have no within-window retirees (audit D3). The landing is therefore inert for every 2023–2025 keeper
input. This was checked by code path, not by replay; no LP was run.

## 5. Rule notes

- **Rule 23 `[R-FROZEN-DERIVE]`:** every re-derivation cites the audit's D5 data-completeness defect and
  the F2 raw back-fill as the data change. No constant or threshold was touched.
- **Rules 13 / 14 / 21 / 24 / 25:** all inputs are measured CEMS. There are no fitted scalars, no
  env-var knobs, and every artifact is per-ISO. Nothing is armed; arming belongs to the R-<ISO> lanes.
- **Rule 28 (c):** no `ScenarioConfig` field was added, so no matrix row is owed.
- The fetcher still demands `--holdout-intake` for 2022, a leftover of the removed `[R-HOLDOUT]`. It was
  passed as `F2`, which records the lane and authorizes nothing. The gate was not edited (out of scope).
