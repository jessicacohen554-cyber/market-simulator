# G6 — SPP / NWPP / SOCO rows transcribed into data-completeness.html (2026-10-03, branch claude/audit-rulings-2026-10)

Owner ruling 2026-10-03: transcribe the three Phase-0 data censuses into `docs/codebase-site/data-completeness.html` `#dcData` rows (F1 item 3 had left this as data entry). Only that page and this record were edited. No solve, no `uv sync`, no git write.

## Method

- Rows are the static inline `#dcData` JSON (not deploy-generated — F1 item 3). Row schema: `iso` (label; the ISO filter is a substring match on it), `cov` (nine chars, columns 2018…2025 + 2026 H1), `note`.
- Status vocabulary: `y` on disk, `p` partial, `n` missing (fetchable), `b` blocked (not fetchable, excluded from %), `x` n/a (excluded). The page had no "not audited" value, so one was added: **`u` → `?`**, excluded from the denominator (`WT.u = null`, `GLYPH.u = '?'`, `.c-u` CSS, legend text). Every cell a census is silent on reads `u`; nothing was inferred from the raw tree.
- Each row carries the census verdict for the window the census audited (2023–2025, plus 2026 H1 where the census said so) and cites `<iso>-data-audit.md §1 item N` (+ the section it points at). Where `git ls-tree` of `data/raw/` now shows files that landed after the census, the note says "on the tree post-census, not verified here" — trees listed only, no parquet read (blobless clone).
- Only datatypes the page already carries were transcribed (EIA-930, zone demand, CAMPD, AS, HSL, fuel/EIA-923, transmission/interchange, validation LMP, weather). Census items with no page section (EIA-860 fleet census, eGRID, PRM, offer caps, LTLF, planning PDFs) were not given rows.

## Rows added — SPP (docs/multi-iso/spp-data-audit.md, lane SPP-10, 2026-09-06)

| Section | Label | cov | Census citation |
|---|---|---|---|
| EIA-930 | SPP (SWPP) | `yyyyyyyyp` | §1 item 3 (+4), §3 — 2015-07-01 → 2026-05-21, 3 defective hours |
| Zone demand | SPP sub-BA (17) | `uuuuuyyyu` | §1 items 11/18 — landed by SPP-11 the census day |
| CAMPD | SPP footprint states (14) | `uuuuuyyyu` | §1 item 2, §2.4 — OK/NE/NM gap closed by SPP-11 |
| AS | SPP reserve / VRL curves | `uuuuupppu` | §1 item 15, §4 row 2 — maxima only, breakpoints → SPP-12 |
| HSL | SPP wind curtailment (aggregate) | `uuuuupppu` | §1 item 19 — MW averages, no % |
| Fuel | SPP EIA-923 fuel cost | `uuuuuyyyu` | §1 item 8 |
| Fuel | SPP EIA-923 monthly gen | `uuuuuyypu` | §1 item 9 — 2025 preliminary |
| Fuel | SPP Panhandle basis + PRB coal | `uuuuuyyyu` | §1 item 20, §4 rows 8–9 |
| Transmission | SPP N↔S transfer capability / ITP | `uuuuubbbu` | §1 item 16, §6 row 3 — OASIS blocked |
| Validation LMP | SPP system hub (N/S mean) | `uuuuuyyyu` | §1 item 5, §4 |
| Validation LMP | SPP per-hub N / S | `uuuuubbbu` | §1 item 6 (item 7 noted) |
| Weather | SPP / NWPP / SOCO zone temp | `uuuuuuuuu` | census silent (shared row) |

## Rows added — NWPP (docs/multi-iso/nwpp-data-audit.md, lane NWPP-10, 2026-09-13)

| Section | Label | cov | Census citation |
|---|---|---|---|
| EIA-930 | NWPP (17-BA BALANCE) | `uuuuuyyyu` | §1 item 4, §4.1 |
| EIA-930 | NWPP per-BA extracts | `uuuuunnnu` | §1 item 5 — absent, a derive → NWPP-11 |
| Zone demand | NWPP per-BA (17 BAs) | `uuuuuyyyu` | §1 items 4/7 (+6), §5 |
| CAMPD | NWPP footprint states | `uuuuupppu` | §1 item 10, §8 — ID/OR/UT/WA absent |
| AS | NWPP-AS | `uuuuuuuuu` | census silent (item 18 noted) |
| HSL | NWPP HSL / curtailment | `uuuuuuuuu` | census silent (item 15 noted) |
| Fuel | NWPP EIA-923 fuel cost | `uuuuupppu` | §1 item 12, §7 row 9 — coal 8 plants |
| Fuel | NWPP EIA-923 monthly gen | `uuuuuyypu` | §1 item 11 — 2025 at 0.7881, `eia923_incomplete` |
| Fuel | NWPP gas hub basis | `uuuuuuuuu` | census silent (item 16 noted) |
| Transmission | NWPP DIBA interchange | `uuuuupppu` | §1 item 9, §4.6 |
| Transmission | NWPP WECC path ratings | `uuuuunnnu` | §1 item 17, §9 — pending NWPP-12 |
| Validation LMP | NWPP | `uuuuubbbu` | §1 item 14 — no LMP published |
| Weather | (shared row above) | | |

## Rows added — SOCO (docs/multi-iso/soco-data-audit.md, lane SOCO-10, 2026-09-13)

| Section | Label | cov | Census citation |
|---|---|---|---|
| EIA-930 | SOCO | `uuuuuyyyu` | §1 item 3 (+4), §3.5/§3.6 |
| Zone demand | SOCO FERC-714 planning areas | `uuuuupppu` | §1 item 10, §6.2 — respondents got, hourly pending |
| CAMPD | SOCO footprint states | `unnnnnnnn` | §1 item 2, §2.3 — "BLOCKED, the critical path"; rendered ✗ because it is a fetch (SOCO-11), not an unfetchable source; "absent for every year" is the census's own all-years statement |
| AS | SOCO-AS | `uuuuuuuuu` | census silent |
| HSL | SOCO HSL / curtailment | `uuuuuuuuu` | census silent |
| Fuel | SOCO EIA-923 fuel cost | `uuuuuyyyp` | §1 item 8 — 2026 partial |
| Fuel | SOCO EIA-923 monthly gen | `uuuuuyypu` | §1 item 9 — 2025 preliminary |
| Fuel | SOCO delivered gas AL/GA/MS | `uuuuunnnu` | §1 item 15, §5 row 6 — pending SOCO-12 |
| Transmission | SOCO BA-to-BA interchange | `uuuuunnnu` | §1 item 11 — pending SOCO-11 |
| Validation LMP | SOCO | `uuuuubbbu` | §1 items 6/7 — no price exists, card S2 |
| Weather | (shared row above) | | |

Cells left `u` (not audited): every 2018–2022 cell and every 2026 H1 cell outside the census statements (SPP EIA-930 and SOCO EIA-923 fuel cost are the only rows with a non-`u` 2026 H1 cell; SPP EIA-930 is the only row audited back to 2018), and all nine cells of the six "census silent" rows (NWPP-AS, SOCO-AS, NWPP HSL, SOCO HSL, NWPP gas hub basis, shared weather).

## Raw-tree cross-checks (ls-tree only, no blobs read)

- `data/raw/campd-unit-level/`: OK/NE/NM 2019–2026 present (SPP item 2 closure confirmed and extended); AL/GA 2019–2026 and FL 2019–2025 present (SOCO item 2's gap has since been filled — noted in the row, not scored); ID/OR/UT/WA 2019–2026 present (NWPP item 10 gap filled since — noted, not scored).
- `data/raw/eia-930-hourly/`: `SWPP hourly.parquet` and `SOCO hourly.parquet` present (items 3); AVA/BPAT/IPCO/NWMT/PACE/PACW/PGE/PSEI per-BA files present (NWPP item 5 said absent → landed since, noted).
- `data/raw/zone-specific-demand/SPP/` 2019–2022 + 2023–2025 CSVs, `…/SOCO/` FERC-714 2019–2022 + 2023–2025 parquets; `_validation-source/actual_lmp_hourly_{SPP,zonal_SPP,NWPP,SOCO}.parquet`; `eia-930-interchange/{SWPP,SOCO,BPAT,PACE} interchange hourly.parquet` — all post-census landings, noted in the rows.
- `configs/data-profiles.yaml`: `spp`/`nwpp`/`soco` profiles exist (tokens `swpp`, `spp-`, `nwpp`, `soco`), consistent with the directory names above.

A follow-up re-census of the three ISOs against the raw tree (the 2026-07-10 method) would convert many `u`/`n` cells to `y`; that is a separate, owner-ruled census, not this transcription.

## Other page edits

- Fallback branch kept but narrowed: it no longer claims SPP/NWPP/SOCO have no audited rows; it now says every registered region has censused rows and an empty table means "Hide complete rows" hid them or a newly registered region has not been transcribed.
- JS comment (`CENSUSED_ISOS` block) and the foot note rewritten to state the two census sources and dates; the cross-ISO wildcard rows ("all 6 ISOs" etc.) still deliberately do not match the three new filters.
- Headline: 41 → 75 rows; scored denominator 359 → 443 cells; headline 67 % → 66 % (the three ISOs' `y/p/n` window cells now count; `u` does not).

## Render check

- `html.parser` tag-balance walk: no unclosed or mismatched tags; `#dcData` parses, 75 rows, every `cov` nine chars in `{y,p,n,b,x,u}`.
- Playwright: the python package is not installed, but node Playwright 1.56.1 (`/opt/node-tools/node_modules/playwright`) with chromium-1194 under `/opt/pw-browsers` loaded the file. Clicking the filter chips: SPP 12 rows / NWPP 13 / SOCO 11, each across all 9 sections; `All ISOs` 75 rows; no "No audited rows" fallback shown; no `pageerror`. The only console error is `net::ERR_CERT_AUTHORITY_INVALID` for an external stylesheet/font fetch through the sandbox proxy (not page code). Script: scratchpad `render.js`, not committed.
