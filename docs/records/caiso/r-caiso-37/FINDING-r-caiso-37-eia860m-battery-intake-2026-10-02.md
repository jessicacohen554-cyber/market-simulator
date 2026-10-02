# FINDING — R-CAISO-37 (link 19): EIA-860M intake for the unmatched battery crosswalk rows

Keeper unchanged (`frontend/data/backcast/keepers/CAISO.json`). **Zero LP, no shard, no `ScenarioConfig` field, no
constant, no consumer, no matrix verdict moved.** Handoff: `docs/handoffs/r-caiso-36/HANDOFF-r-caiso-37.md`.
Owner card behind the link: R-CAISO-36 FINDING §6 point 2.

## 0. Result

| | R-CAISO-36 | R-CAISO-37 |
|---|--:|--:|
| Crosswalk rows / accepted | 233 / 168 | 233 / **176** |
| Accepted by `match_method` | name_token 83, reviewed 85 | name_token 83, reviewed 86, **reviewed_eia860m 7** |
| Accepted coverage of offline MW-h, 2023 / 24 / 25 | 79.6 / 81.7 / 85.4 % | 79.6 / 81.7 / **90.0 %** |
| `reviewed_eia860m` share of offline MW-h, 2023 / 24 / 25 | — | 0 / 0 / 4.6 % |
| T1 crosswalk-only sensitivity, worst cell | 0 h | **1 h, 0.011 %** (2025 discharge) |
| T1 primary (population unchanged) | 0.548 % (48 h, 2023 dis) | 0.548 %, unchanged: CARRIED |

1. **EIA-860M names 7 of the 65 unaccepted resources** (600 MW). All are batteries with an EIA COD in 2026, after the
   annual Final 2025 cut-off, so they are absent from the annual schedule. All 7 agree on MW exactly and sit in a CAISO
   zone. A further reject is overturned against the annual schedule itself (BTF Storage DIDF = Blackwell's Corner,
   2 MW), surfaced by the scan.
2. **Coverage moves only in 2025** (+4.6 pp, to 90.0 %), because all 7 resources' CNOG episodes fall in 2025. 2023 and
   2024 do not move.
3. **The T1 crosswalk-only sensitivity moves from 0 to 1 hour** (2025 discharge, 0.011 %, excess 0.0 % of envelope
   MW-h). The sensitivity's numerator grows with coverage, so this is the expected direction. It stays far inside the
   1 % bar. T1 primary does not depend on the crosswalk and does not move. **The adjudicated CARRIED reading is not
   re-opened.**
4. **New observation (reported, not adjudicated): pre-COD outages sit in the census numerator but not its
   denominator.** Every one of the 7 matched resources carries CNOG outage episodes in 2025, before its EIA COD
   (2026-03 to 2026-07). The census denominator (`monthly_battery_fleet_mw`, annual EIA-860 by COD) excludes them;
   the numerator (offline MW) includes them. In 2025 they hold 142 MW of the 3,102 MW mean offline, about
   **1.07 pp of the 23.8 % `o_860` mean**. The bias is conservative for the CARRIED test: it lowers the available
   share, so it can only add T1 hours, never hide them.

## 1. Method (declared before the matching; thresholds unchanged)

- **The source.** `data/raw/eia-860m/august_generator2026.operating.parquet` (August 2026 inventory, released
  2026-09-24; README in that directory). The scan read the `Batteries` rows in CA/NV/AZ of all four sheets (operating,
  planned, retired, canceled), then searched each of the 65 unaccepted resources by its name tokens and CAISO node
  prefix.
- **What may be accepted from it.** A ledger row with `source = eia860m` must name a plant that is all three of:
  1. a `Batteries` row of the **operating** sheet, status `OP`/`OA`/`OS` (the same set the annual review accepts);
  2. in a CAISO zone (`build_zone_lookup("CAISO")`);
  3. **absent from the annual storage schedule.** 860M is only for the units the annual release lacks. Where the
     annual carries the plant, it stays the basis.

  Planned-sheet units (status `TS`/`V`/`U`/…) are never accepted, even when the identity is exact.
- **Builder** (`scripts/data/build_caiso_resource_crosswalk.py --storage`):
  - `load_storage_targets_860m` reads the source declared as `EIA_860M_OPERATING`.
  - `apply_storage_review` gains a `source` column (`eia860` | `eia860m`; a missing column reads as `eia860`). It
    refuses an unknown source, an `eia860m` plant outside the 860M lookup, and an `eia860m` row naming a plant the
    annual schedule carries.
  - Rows from 860M carry `match_method = reviewed_eia860m`, so the census splits them out unaided.
  - The 0.6 name-token threshold and the ≤ 2× capacity sanity are untouched and still decide every unreviewed row.
- **Evidence per accepted row** (in its `review_note`): EIA plant name and ID, generator ID, MW agreement, county, BA
  and zone, the node prefix where it names the plant, and EIA COD against the first CNOG episode.

## 2. The rows

**Accepted from EIA-860M (`reviewed_eia860m`), MW exact on every row:**

| CAISO resource | EIA-860M plant (ID, gen) | MW | County / zone | EIA COD · first CNOG episode |
|---|---|--:|---|---|
| `HUMBRD_1_HMBBT1` Hummingbird Energy Storage | Hummingbird Energy Storage LLC (65395, HUMB1) | 75 | Santa Clara / NP15 | 2026-03 · 2025-02 |
| `NITHWK_1_NHSBT1` Nighthawk Storage | Nighthawk Energy Storage, LLC (65889, BESS) | 300 | San Diego / SDGE | 2026-06 · 2025-06 |
| `GOLETA_2_PAIBT2` Painter BESS | Painter Energy Storage (62729, PAIN1) | 10 | Santa Barbara / SP15 | 2026-07 · 2025-12 |
| `VENTSO_6_VENBT1` Ventasso Energy Storage | Ventasso Energy Storage, LLC (68509, VNT) | 50 | San Diego / SDGE | 2026-03 · 2025-08 |
| `TWINKL_2_ASCBTA` Aratina Solar Center 1a BESS | Aratina Solar Center 1A (68661, 64BES) | 75 | San Bernardino / SP15 | 2026-07 · 2025-10 |
| `TWINKL_2_ASCBTB` Aratina Solar Center 1b BESS | Aratina Solar Center 1B (61167, BESS) | 50 | San Bernardino / SP15 | 2026-07 · 2025-10 |
| `CHERRY_2_POMBT1` Pomegranate | Cherry (63850, BESS1; node `CHERRY`) | 40 | Kings / ZP26 | 2026-05 · 2025-11 |

For Cherry, only BESS1 (40 MW) is operating; BESS2 (110 MW) is on the planned sheet and is not counted.

**Accepted from the annual schedule (`reviewed`), surfaced by the scan:**
- `BLCKWL_6_BTFBT1` BTF Storage DIDF = Blackwell's Corner Storage Facility (66648, BLKWL), 2 = 2 MW, Kern / ZP26, node
  `BLCKWL`.
- It is OP in the annual Final 2025 (COD 2025-06), so the R-CAISO-36 "no matching EIA-860 storage plant" reject was a
  review miss.

**Identity found, not accepted (note updated):**
- **Angela BESS (20 MW):** 860M has Angela Solar Project (68854, ABESS) at 40 MW. The identity is likely (node
  `ANGELA`, Tulare), but MW disagrees, and the evidence is a single pre-COD episode.
- **Merced BESS (2.93 MW):** Merced BESS (68018, 3.0 MW) is `TS` (construction complete, not commercial), so it sits
  on the planned sheet.
- **Atlas Complex 8A (210 MW):** Atlas VIII gen ALT8A (210 MW) is `V` (under construction), on the planned sheet.
- **Baldy Mesa SP (50 MW):** 860M adds Baldy Mesa Storage (69964, 50 MW) at `V`, but CNOG episodes run from 2024-02.
  Still ambiguous against the two operating Baldy Mesa plants.
- **Sun Pond Storage 1/2 (2 × 42.5):** Sun Pond (68492, 85 MW) is in SRP, outside the CAISO zones.
- **Dateland Energy Complex Sierra (112.5):** plausibly Sierra Pinta BESS (67973, 113 MW, Yuma AZ; node `SRAPTA`), but
  it is in AZPS, outside the CAISO zones.

**Unchanged:**
- **The EdSan family (5 rows):** 860M carries the same Edwards Sanborn units with generator IDs `BESS`/`ESSB1–2`. These
  do not disambiguate, so the family stays unresolved, as the handoff required.
- **Every other reject (45 rows):** 860M (all four sheets) holds no unit beyond the annual Final. This covers Dracker,
  Sol Catcher, Rosamond West, Tropico, Marvel, Black Diamond, Bateria del Sur 2, Almasol, Vikings, Yellow Pine II,
  Townsite and others. Each note now records that check.

**Residual uncovered offline MW-h:** 20.4 / 18.3 / 10.0 % (2023 / 24 / 25).

## 3. Files

- `scripts/data/build_caiso_resource_crosswalk.py`: `EIA_860M_OPERATING`, `REVIEW_SOURCES`,
  `load_storage_targets_860m`, and the `source` column in `apply_storage_review`.
- `data/raw/reference/caiso-storage-crosswalk-review.csv`: the `source` column, 8 rows newly accepted, and the notes
  updated on every remaining reject.
- `data/raw/reference/caiso-storage-resource-eia-crosswalk.csv`: rebuilt (233 rows, 176 accepted). Exactly the 8 rows
  above change outside `review_note`.
- `data/raw/eia-860m/README.md`: the reference-identity reader is declared, and it is not a model input.
- `docs/records/caiso/r-caiso-37/battery_outage_census.json`: the re-run
  (`scripts/probes/_rcaiso35_battery_outage_census.py`, unchanged).
- Tests: `tests/iso/caiso/test_caiso_dam_outages.py::test_review_ledger_eia860m_source`. It checks the resolve, and it
  checks three refusals: an annual-source row naming an 860M-only plant, an 860M row naming an annual plant, and an
  unknown source.

## 4. Rules

- **Rule 13 / EIA-860M forecast-only posture:**
  - The crosswalk has no reader, and `load_crosswalk` (the thermal overlay) is untouched.
  - 860M names which plant a CAISO resource is. It sets no capacity, COD or status in any solve.
  - `tests/unit/data/test_vintage_selection_2025_final.py::test_eia860m_has_no_backcast_consumer` still passes: no
    `src/` file reads 860M.
- **Rule 14:** measured identity is lifted, no threshold moves, and a planned-sheet unit is never accepted.
- **Rule 19:** there is no consumer, and CARRIED stands.
- **Rule 23:** the envelope and its derive are unchanged.
- **Rule 24:** no new tunable; the source is a fixed, declared path.
- **Rule 28:** no field, so no new cell. The CAISO shard gets evidence on `storage_measured_anchors` (K stays K).

## 5. Decision

Nothing to promote. The decision goes to the owner as a card (§6).

## 6. Owner ruling

Decision card, 2026-10-02:

1. **Close link 19 report-only.** The ledger (with its `source` column), the declared EIA-860M lookup and the rebuilt
   crosswalk are merged as reference data. There is no consumer, field or verdict move, and CARRIED stands. The matrix
   gets evidence only on `storage_measured_anchors` (CAISO K).
2. **Next link: R-CAISO-38, a pre-COD basis note.** It is zero LP. It measures, across the whole census, the CNOG
   outage MW of resources that are not yet in the denominator fleet (EIA COD after the hour). It reports the bias on
   `o_860` and T1, and T1 is not re-opened (§0 point 4).

Not selected:
- the T2 basis study;
- a re-scan at the September 2026 860M;
- ending the chain.
