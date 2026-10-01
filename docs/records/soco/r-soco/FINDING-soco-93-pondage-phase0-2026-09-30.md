# FINDING — soco-93: `hydro_pondage_bound` phase 0 for SOCO (zero LP)

Lane soco-93, 2026-09-30. Owner ruling 2026-09-30 (soco-92 card "Next lane"): **"Pondage bound phase 0 (Recommended)"**.
This lane is zero-LP, for STRUCTURE (rule 1), not for C3a. Keeper unchanged: `2026-09-30-soco92-hydro-min-flow`
(`results/calibration/soco92_span`), NOT-YET 7/4/0/1/2.

## 1. Artifact (rule 21 frozen derive, rule 25 SOCO's own dams)

- **Intake:** USACE NID national export, vintage `2026-9-23`, fetched 2026-09-30 (sha256 `d2ab9d97…`, not committed).
  Committed subset `data/raw/nid/nid_soco_hydro_dams.csv`: 63 structure rows / 41 distinct NID IDs, all of the dams HILARRI v4
  links to SOCO's EHA hydro plants. Zero links are missing from NID.
- **Derived:** `data/raw/soco-hydro/soco_hydro_pondage.csv` via `scripts/data/build_hydro_pondage.py --iso SOCO`. It has
  41 plants and 3,311 MW. The subset rebuild is **byte-identical** to the national-file build.
- **Head basis:** 40/41 plants use hydraulic height. One (plant 752, 17.2 MW) uses the labelled NID-height proxy.
- **Pondage hours** (storage ÷ nameplate): median 182 h, and 8.2 % of MW holds < 24 h. The range runs from 0.2 h (752) to
  3,848 h (759).
- **Upper bound, stated:** NID `Max Storage` (not the licensed band) with η = 1.0. The bound can only be too loose.

## 2. Coverage against the keeper's hydro fleet

| | units | MW | share of hydro MW |
|---|---|---|---|
| model hydro fleet | 42–43 | 3,314–3,316 | 100 % |
| linked to a storage row | all | all | **100 %** (0 unlinked, every year) |
| RoR-flat (`hydro_ror_split`; no row by rule 19) | 14–15 | 935–937 | 28 % |
| reservoir, storage ≥ largest monthly budget (row redundant, dropped) | 12–13 | 1,422–1,550 | 43–47 % |
| **reservoir, row binds** | **15–16** | **829–957** | **25–29 %** |

Energy coverage matches MW coverage: every hydro unit's monthly budget has a storage row, or the unit is RoR-flat.

## 3. Zero-LP census on soco92_span

Instrument: `scripts/probes/_soco93_pondage_census.py`. The keeper's per-unit hourly hydro comes from the soco-92
year-shard bundles' `dispatch/<y>_P1.parquet`. Inflow is `I = measured monthly budget / hours`, taken from a
`fleet_only` rebuild of the keeper recipe. The storage needed with free spill is the cyclic running deficit, and an
hour violates when that deficit exceeds B. The CLIP is the nearest feasible dispatch that keeps the keeper's
timing. Its cut in top-20 % λ hours is an **upper bound** on what the row can move there, because the LP re-places
clipped water inside the same feasible set.

| year | bounded plant-months violated | units violating | energy clipped (TWh) | top-20 % hydro+PS: model / EIA-930 / excess (MW) | clip cut in top-20 % (MW) | share of excess |
|---|---|---|---|---|---|---|
| 2019 | 103 / 180 (57 %) | 11 | 0.19 | 2,549 / 1,637 / 913 | 59 | 6.5 % |
| 2020 | 99 / 192 (52 %) | 9 | 0.18 | 2,503 / 1,556 / 947 | 60 | 6.3 % |
| 2021 | 114 / 180 (63 %) | 12 | 0.27 | 2,251 / 1,560 / 691 | 73 | 10.6 % |
| 2022 | 105 / 180 (58 %) | 10 | 0.22 | 2,409 / 1,201 / 1,208 | 67 | 5.5 % |
| 2023 | 106 / 192 (55 %) | 11 | 0.20 | 2,023 / 1,373 / 650 | 62 | 9.5 % |
| 2024 | 120 / 179 (67 %) | 13 | 0.26 | 1,983 / 1,130 / 853 | 77 | 9.0 % |
| 2025 | 108 / 179 (60 %) | 10 | 0.19 | 2,129 / 1,419 / 710 | 69 | 9.7 % |

**Violators are the small forebays**, 84 plant-months each: plant 752 needs 552× its forebay (0.2 h), 719 needs 68×
(2.1 h), 723 needs 25× (4.9 h), and 19 needs 15× (9.4 h). The 173 MW plant 702 (126 h) is marginal at 1.03×. The keeper
banks days of water at plants that physically hold hours.

**Where the peak excess sits** (top-20 % λ mean ÷ annual mean, keeper):

| group | MW | top-20 % / average |
|---|---|---|
| redundant large reservoirs (no row) | 1,422–1,550 | 560–878 / 245–412 MW (2.1–2.8×) |
| bounded reservoirs | 829–957 | 445–682 / 200–359 MW (1.9–2.3×) |
| RoR-flat | 935–937 | flat by construction |
| pumped storage | — | 585–778 / 227–286 MW (~2.6–3.1×) |

## 4. Reading

- **The structure is real and currently violated.** The keeper breaks each small plant's physical forebay in 52–67 % of
  bounded plant-months, and 0.18–0.27 TWh/yr of its timing is infeasible. Under rule 1 that is a mechanism defect,
  whatever it does to C3a.
- **It is not a C3a lever.** Its upper-bound peak cut is 59–77 MW against a 650–1,208 MW excess (5.5–10.6 %), which is the
  same order as the min-flow floor (≤ 11 %). The excess sits in the big reservoirs, whose NID forebays hold more than a
  month (so no row is built), and in pumped storage. A daily cycle fits inside a multi-day forebay, so no volume bound
  can shape it.
- **A tighter bound would need data this repo does not hold.** That means licensed operating bands (FERC licence rule
  curves / drawdown limits) for the 12–13 large reservoirs. NID volume is an upper bound, and the licence data is not
  intaken.

## 5. Rule 17 story (for the card)

- **Driver:** each plant's measured forebay volume × head (NID), plus its own monthly EIA-923 budget as inflow.
- **Window:** every hour. It is a RESTRICTION on concentration, not a floor. Spill is unbounded, so it forces no MWh,
  moves no monthly total, and adds nothing to the C8 forced share.
- **Forecast regeneration:** NID is static (re-derived on a new vintage). Inflow is the forecast year's monthly budget,
  the array the LP already carries. There are zero DOF.
- **Rule 19:** complementary to `hydro_ror_split` (RoR-flat rows are skipped) and to `hydro_min_flow_floor` (trough vs.
  concentration). It is mutually exclusive with `hydro_cascade_coupling` (not armed for SOCO).

## 6. Build cost if ruled "build/solve"

The build follows the soco-87/92 pattern: seven year-isolated shards (rule 36) at a pinned SHA, each with the soco-92 §5
flags plus `hydro_pondage_bound`. `gen_soco60b_attestation.py` needs an explicit `--pondage-bound` opt-in (its `verify()`
rejects any hydro family beside `hydro_ror_split` except the reconciled floor). No new ScenarioConfig field is needed.
Expected: C3a moves ≤ ~0.3 pp, with no status flips expected (a pre-registration expectation, not a gate).
