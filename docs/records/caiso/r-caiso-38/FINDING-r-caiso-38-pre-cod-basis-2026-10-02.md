# FINDING — R-CAISO-38 (link 20): pre-COD basis note for the battery outage census

Keeper unchanged (`frontend/data/backcast/keepers/CAISO.json`). **Zero LP, no shard, no `ScenarioConfig` field, no
constant, no consumer, no matrix verdict moved.** Handoff: `docs/handoffs/r-caiso-37/HANDOFF-r-caiso-38.md`.
PRECOMMIT: `PRECOMMIT-r-caiso-38-pre-cod-basis-2026-10-02.md`. It was written before the first computation and is
committed in the same commit as this record. T1 (CARRIED, 0.548 %) is not re-opened. Everything below is a
sensitivity beside the adjudicated reading.

## 0. Result

The mismatch covers the whole census, not just 2025. It is much larger than the 142 MW link 19 saw: that figure is
only the `reviewed_eia860m` part of class A in 2025.

Each cell shows mean MW, then pp of `o_860` mean, then the share of census offline MW-h.

| Class | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **A**: accepted, plant COD after the hour's month | 204 MW · 3.44 pp · 13.1 % | 603 MW · 6.69 pp · 29.2 % | 516 MW · 4.01 pp · 16.7 % |
| — of which `reviewed_eia860m` | — | — | 4.6 % of MW-h (the link-19 142 MW) |
| **B**: accepted, plant OA in the annual Final | 140 MW · 2.72 pp · 9.0 % | 70 MW · 0.76 pp · 3.4 % | 214 MW · 1.63 pp · 6.9 % |
| **U**: unaccepted, identity unknown | 317 MW · 5.59 pp · 20.4 % | 379 MW · 4.20 pp · 18.3 % | 312 MW · 2.41 pp · 10.0 % |

U equals 1 − crosswalk coverage, as it should. It is not labelled pre-COD.

| Reading | | 2023 | 2024 | 2025 | T1 primary, worst cell | T2, worst cell |
|---|---|--:|--:|--:|--:|--:|
| **R0 adjudicated** (default output) | `o_860` mean / p99 / max | 28.4 / 48.2 / 57.2 % | 22.3 / 35.2 / 40.6 % | 23.8 / 36.1 / 42.6 % | **0.548 %** (48 h, 2023 dis) | 0.24 % |
| **R1** A+B removed | `o_860` mean / p99 / max | 22.3 / 37.4 / 47.6 % | 14.9 / 23.4 / 32.3 % | 18.1 / 28.6 / 34.1 % | **0 h** | 0 |
| **R2** A+B+U removed (upper bound) | `o_860` mean / p99 / max | 16.7 / 31.1 / 41.0 % | 10.7 / 18.7 / 22.9 % | 15.7 / 26.0 / 29.4 % | 0 h | 0 |

1. **Every T1 binding hour on the adjudicated reading is a basis artefact.** All 48 + 1 + 3 + 7 hours vanish once
   the numerator holds only plants the denominator carries. T2's 0.24 % (2023 discharge) vanishes as well. This is
   the conservative direction PRECOMMIT §3 predicted, and no cell moved the other way.
2. **The CNOG outage rate on a matched basis is lower:** 22.3 / 14.9 / 18.1 % of fleet MW (R1), against
   28.4 / 22.3 / 23.8 %. CARRIED is untouched. The adjudicated reading already sat under the bar, and it now has
   more margin.
3. **Class B is a status basis, not a COD basis.** Four accepted plants carry status `OA` in the canonical 2025
   Final, and the denominator keeps only `OP`:
   - Elkhorn BESS (62564, 182.5 MW);
   - Escondido ES (60570, 30 MW);
   - Orange County ES 2 (62497, 9 MW);
   - Silverstrand (63735, 11 MW).

   CNOG reports them offline for long stretches, Elkhorn above all. The year-end 2025 status is applied to every
   year, so this is reported, not resolved.

## 1. Method (as pre-registered)

- **Denominator membership per plant and month.** `denominator_by_plant` rebuilds `load_eia860_storage`'s filters,
  keyed by `Plant Code`:
  - canonical vintage, status `OP`, compressed air excluded;
  - `Operating Year ≤ year`, `_unit_monthly_mask`, the CAISO zone lookup.

  Gate: the per-plant sum equals `monthly_battery_fleet_mw(year)` in every month (|Δ| < 1e-6 MW). It passed in all
  three years.
- **Classes.** A resource-hour is in the denominator iff the resource is accepted and its plant has > 0 MW in that
  month.
  - **A:** the plant is an in-zone `OP` annual plant that the COD mask excludes, or a `reviewed_eia860m` plant whose
    860M COD is after the month.
  - **B:** any other accepted absence. All of it turned out to be `OA` status.
  - **U:** unaccepted.

  Resolution is the denominator's own calendar month on the EIA-930 row clock.
- **Not measured.**
  - Partial plants count as in. Example: Menifee NOVA1–5, with CODs from 2024-06 to 2025-07.
  - The CNOG Pmax vs EIA nameplate gap is not measured. Example: Northern Orchard, 150 vs 92 MW.
  - Outages inside a plant's COD month count as in.
  - All three make R1 an under-correction, not an over-correction.
- **Code.** `scripts/probes/_rcaiso35_battery_outage_census.py --pre-cod-basis` adds a `pre_cod_basis` block. Without
  the flag the output is **byte-identical** to the committed `docs/records/caiso/r-caiso-37/battery_outage_census.json`
  (checked with `cmp`). Output: `battery_outage_census_pre_cod.json`. Each class lists its top 10 resources by MW-h.

## 2. Largest contributors to class A

- **2025:**
  - Bellefield (500 MW, COD 2025-12, CNOG from 2025-06);
  - Nighthawk and Hummingbird (860M, COD 2026);
  - Northern Orchard (COD 2025-07);
  - Pome (COD 2025-10);
  - Silver Peak / Tahoe (COD 2025-06, CNOG from 2024-11).
- **2024:**
  - McFarland B (COD 2024-12);
  - Northern Orchard;
  - Menifee (from 2024-06).
- **2023:**
  - Sanborn 3 (COD 2023-10);
  - McFarland A (COD 2023-12);
  - Oberon (COD 2023-09).

The pattern is the same throughout: CAISO models the resource, and CNOG reports it as curtailed during
commissioning, months before the EIA operating month.

## 3. Rules

- **Rule 13:** no measured value is pinned or consumed.
- **Rule 14:** the adjudicated basis is unchanged, and the matched basis is reported beside it.
- **Rule 19:** no consumer, and CARRIED stands.
- **Rule 23:** the envelope and its derive are unchanged.
- **Rule 24:** no tunable; the flag only adds a report block.
- **Rule 28:** no field, so no new cell. The CAISO shard gets evidence on `storage_measured_anchors` (K stays K).

## 4. Decision

Nothing to promote.

## 5. Owner ruling

Decision card, 2026-10-02:

1. **Close link 20 report-only.**
   - The `--pre-cod-basis` flag, the PRECOMMIT and this record merge.
   - The sensitivity sits beside the adjudicated reading, and CARRIED stands.
   - Matrix: evidence only on `storage_measured_anchors` (CAISO K).
2. **End the battery chain.** No R-CAISO-39 is launched. CAISO returns to the closeout-CAISO lane
   (`docs/mechanism-testing-matrix.md` §5.2).

Not selected:
- restating the matched-basis outage rate as the reference figure;
- an OA-status basis note;
- a matched-basis census rebuild.
