# FINDING — R-CAISO-36 (link 18): battery crosswalk review; the census selector missed 58 battery resources

Keeper unchanged (`frontend/data/backcast/keepers/CAISO.json`). **Zero LP, no shard, no `ScenarioConfig` field, no
constant, no consumer, no matrix verdict moved.** Handoff: `docs/handoffs/r-caiso-35/HANDOFF-r-caiso-36.md`.
Owner card behind the link: R-CAISO-35 FINDING §6 point 2.

## 0. Result

| | R-CAISO-35 (as merged) | R-CAISO-36 |
|---|--:|--:|
| Census resources | 177 | **233** (+58 by the selector fix, −2 pumped hydro) |
| Crosswalk rows / accepted | 176 / 64 | 233 / **168** (83 name-token, 85 reviewed) |
| Accepted coverage of offline MW-h, R-CAISO-35 population (2023 / 24 / 25) | 18.6 / 31.0 / 18.7 % | **80.3 / 77.6 / 84.7 %** |
| Accepted coverage, corrected population | — | **79.6 / 81.7 / 85.4 %** |
| T1 crosswalk-only sensitivity, both populations | 0 h | **0 h** (does not move) |
| T1 primary, corrected population (worst year/direction) | 4 h, 0.046 % | 48 h, **0.548 %** (2023 dis): still CARRIED (≤ 1 %) |

1. **Coverage lifts from 19–31 % to 78–85 % of offline MW-h** on the population R-CAISO-35 adjudicated. Every
   unaccepted row now carries a stated reason. The rest (15–22 %) is resources that have no operable EIA-860 unit in
   a CAISO zone.
2. **The T1 crosswalk-only sensitivity does not move.** It reads 0 hours on both populations in every year and
   direction.
3. **The R-CAISO-32 census selector had a bug, and the census undercounted.** Fixing it lifts mean battery MW offline
   by 10 / 36 / 36 % (2023 / 24 / 25). T1 primary rises from 0.046 % to 0.548 % of hours. That is still under the
   pre-registered CARRIED bar (≤ 1 %). The other measures stay under their bars too: the RTM-denominator sensitivity
   reads 0.091 %, and T2 reads 0.24 % against the 1 % caveat bar. **The CARRIED reading is not re-opened, and it
   holds on the corrected census.**

## 1. Method (declared before the review, unchanged thresholds)

- **The name-token pass is unchanged.** It keeps the 0.6 threshold and the ≤ 2× capacity sanity, and it still decides
  every row the review does not cover.
- **Reviewed rows are a separate method.** They sit in the ledger `data/raw/reference/caiso-storage-crosswalk-review.csv`
  (`resource_id, plant_code, accepted, review_note`). The builder
  (`build_caiso_resource_crosswalk.py --storage`, `apply_storage_review`) overlays them, and they carry
  `match_method = reviewed`. The builder refuses three things: a ledger row outside the census, an accepted row
  without a plant, and a plant outside the EIA-860 storage operable schedule in a CAISO zone. A stale review therefore
  never applies silently.
- **Evidence per accepted row** comes from four sources:
  - the EIA-860 plant name, generator IDs and utility;
  - MW agreement, either exact or as a unit sum (e.g. Proxima 90 + 40 + 32 = 162; Daggett 3 61.5 + 60 + 12.5 + 15 = 149;
    Tahoe 1–3 = Silver Peak SP1–3, unit for unit);
  - county and zone;
  - the CAISO node prefix where it names the plant: `ETIWND` (Etiwanda), `WESCAN` (West Side Canal), `TUMBWD`
    (Tumbleweed), `ELCAJN` (El Cajon), `JOANEC` (Johanna).
- **Rejects** state why: there is no EIA-860 operable unit (Dracker, Sol Catcher, Rosamond West, Tropico, Marvel, …);
  the plant sits outside the CAISO zones (Vikings in IID, Yellow Pine II in NEVP, Townsite in WALC); or the match is
  ambiguous (the Edwards Sanborn "EdSan" family).
- **The review lookup reads EIA status `OA`/`OS` as well as `OP`.** Four accepted rows sit on `OA` plants in the Final
  2025 release: Elkhorn (after the 2025 Moss Landing fire), Orange County ES 2/3, Escondido and Silverstrand. The
  name-token pass still reads `OP` only.
- **Vistra Moss Landing:** Dallas 4 × 100 maps to BAT1 300 (retired 2025, in the retired schedule) + BAT2 100, and Plano
  350 maps to BAT3. All eight resources map to EIA plant 260.

**Known items from the handoff:**
- **Exact-MW near-misses, all accepted:** Garland, Mustang, Azalea, Gateway, Oberon 1/2 (to Oberon I/II), Desert
  Sunlight (to Sunlight Storage I/II, by first-episode date vs COD), Fifth Standard and Resurgence 1/2.
- **Wrong best-matches, rejected and remapped:** Daggett Solar 1 → Daggett 1, Daggett Solar 3 → Daggett 3, and Scarlet
  Solar 2 BESS → Scarlet II Hybrid (150 MW).

**The review also corrects seven name-token-accepted rows to the right plant.** Their accepted flag is unchanged, so
coverage is not affected:
- Johanna Storage 1/2 → Hecate Johanna (the Johanna Energy Center gens are the Santa Ana Storage units);
- Lead BESS 2 → Lead BESS 2;
- McFarland Solar B / C → McFarland B / C;
- Lockhart Solar BESS 1 → Lockhart ESS;
- Sagebrush Solar 2 (80) → Sagebrush ESS.

One name-token pick is rejected: EnerSmart El Cajon → El Cajon ES. The EnerSmart plant is cancelled, and El Cajon ES is
SDG&E's unit.

## 2. The selector bug (new evidence; reported, not adjudicated)

The census selector (R-CAISO-32 Part B, reused by R-CAISO-35) used the id pattern `_(?:BT|BX|ES|BE)\d`. That pattern
matches only when the storage code sits **right after an underscore**. CAISO ids put a plant code first
(`ROMOLA_5_MPBBT1`, `RATSKE_2_WAVBT1`), so the id branch almost never fired, and selection rested on the name.

**The miss.** It covers every battery resource whose name lacks a storage token. Examples are Menifee Power Bank 1–5
(680 MW), Crimson, Tahoe 1–3, Kola 1, Marvel, Bateria del Sur, Separator, Electrolyte and Acid. It also covers hybrid
batteries that carry the solar project's name, such as McFarland Solar B Hybrid (300 MW) and Northern Orchard Solar.

**The fix in `is_battery_resource`:**
- The id pattern searches the whole final segment, and an id match is authoritative.
- Names containing "pumped" are excluded, so Lake Hodges pumped hydro no longer counts as a battery.
- The storage builder selects per episode (`load_battery_resources`) and keeps a storage-token name for scoring. This
  fixes the `RATSKE_2_WAVBT1` miss, now accepted as AVEP BESS (126 MW).

All 58 added resources are battery resources by their id code. The 176 rows R-CAISO-35 had built are byte-identical
before review.

**Corrected census** (`battery_outage_census.json`), against R-CAISO-35:

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| Offline MW mean, R-CAISO-35 → R-CAISO-36 | 1,409 → 1,554 | 1,516 → 2,066 | 2,278 → 3,102 |
| `o` mean, EIA-860 basis | 25.8 → 28.4 % | 16.6 → 22.3 % | 17.4 → 23.8 % |
| `o` max | 50.2 → 57.2 % | 30.6 → 40.6 % | 30.8 → 42.6 % |
| `o` mean, RTM-fleet basis | 21.4 → 23.6 % | 14.4 → 19.4 % | 14.5 → 19.8 % |
| Least headroom `a − e`, charge / discharge | −3.2 / −12.0 pp | +4.0 / −1.2 pp | +7.1 / −4.6 pp |
| T1 primary, hours (charge / discharge) | 1 / 48 | 0 / 3 | 0 / 7 |
| T1, RTM denominator | 0 / 8 | 0 / 0 | 0 / 0 |
| T1, crosswalk-only | 0 / 0 | 0 / 0 | 0 / 0 |
| T2, measured above available (charge / discharge) | 0 / 0.24 % | 0 / 0 | 0 / 0 |

- **Reading under the PRECOMMIT §4 bands:** the worst cell is 0.548 %, which is CARRIED. Excess MW-h is ≤ 0.09 % of
  envelope MW-h.
- **Margin:** the bar is ≤ 1 %, and the R-CAISO-35 record's "4 of 26,280 hours" is superseded by 59 hours of 26,280.
  The CARRIED reading therefore holds with less margin.
- **T2 grows with T1:** measured discharge exceeds the available share in 0.24 % of 2023 hours. The CNOG-MW vs EIA-860
  nameplate basis disagreement, the reading R-CAISO-35 §1 gave the T1 hours, therefore scales with the census too.
- **The R-CAISO-32 Part B numbers were also undercounted.** Its `o_rtm` was 21.4 / 14.4 / 14.5 %; the corrected values
  are 23.6 / 19.4 / 19.8 %. Its probe (`scripts/probes/_rcaiso32_soc_derate_reach.py`) carries its own copy of the
  pattern. It is a closed record and is not edited here.

## 3. Files

- `scripts/data/build_caiso_resource_crosswalk.py`: selector fix, `load_battery_resources`, `apply_storage_review`,
  and `load_storage_targets(statuses)`.
- `data/raw/reference/caiso-storage-crosswalk-review.csv`: the review ledger (150 rows).
- `data/raw/reference/caiso-storage-resource-eia-crosswalk.csv`: rebuilt (233 rows, column `review_note` added).
- `scripts/probes/_rcaiso35_battery_outage_census.py`: coverage split by `match_method`. The census population
  follows the fixed selector.
- `docs/records/caiso/r-caiso-36/battery_outage_census.json`: the re-run on the corrected population.
- `docs/records/caiso/r-caiso-36/crosswalk_sensitivity_r35_population.json`: the crosswalk-only sensitivity and
  coverage on the as-adjudicated 177-resource population, for three crosswalks: R-CAISO-35, R-CAISO-36 all-accepted,
  and R-CAISO-36 name-token only. The R-CAISO-35 row reproduces 18.6 / 31.0 / 18.7 %.
- Tests: `tests/iso/caiso/test_caiso_dam_outages.py`, with 3 new cases (selector prefix, per-episode name, review
  overlay).

## 4. Rules

- **Rule 13:** the crosswalk is reference data with no reader. `load_crosswalk` (the thermal overlay) is untouched.
- **Rule 19:** no consumer. CARRIED stands.
- **Rule 23:** the envelope and its derive are unchanged.
- **Rule 28:** no field, so no new cell. The CAISO shard gets evidence on `storage_measured_anchors` (K stays K).
- **Rule 14:** the review lifts measured identity, and it does not move a threshold.

## 5. Decision

Nothing to promote. The decision goes to the owner as a card (§6).

## 6. Owner ruling

Decision card, 2026-10-02:

1. **Close link 18 report-only.** The crosswalk and review ledger stay committed as reference data. There is no
   consumer, field or verdict move, and CARRIED stands on the corrected census. The matrix gets evidence only on
   `storage_measured_anchors` (CAISO K).
2. **Next link: R-CAISO-37, an EIA-860M intake for the unmatched rows.** It is zero LP. It checks whether the EIA-860M
   monthly generator inventory covers the 65 unaccepted battery resources (15–22 % of offline MW-h). It is data intake
   only, with no consumer.

Not selected:
- the R-CAISO-32 erratum note and the patch to its duplicated selector (the record stays as merged, and §2 here is the
  correction of record);
- ending the chain;
- the T2 basis study.
