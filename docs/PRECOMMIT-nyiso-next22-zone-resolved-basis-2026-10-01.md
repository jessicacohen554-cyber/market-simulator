# PRECOMMIT — NYISO-NEXT-22: NYISO C3a/C3b actual becomes ZONE-RESOLVED (zero LP)

```
LANE      : NYISO-NEXT-22 (owner ruling 2026-10-01, decision card "Basis": "Adopt for NYISO now")
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021 stamped), unchanged
LP        : none
WRITTEN   : before any code change, retrofit or re-score
PRECEDENT : miso-294 (docs/PRECOMMIT-miso294-zone-resolved-basis-2026-10-01.md), same construction
```

## 1. Why (phase 0, zero LP)

Rubric v2.4 defines the C3a/C3b actual as the committed hourly actual weighted by the same measured
demand the model dispatches, **zone-resolved where a zonal archive exists**. NYISO is scored on its
**hub** (simple mean of the 11 internal zones) × measured SYSTEM demand. The model side of C3a is
zone-demand-weighted. The hub gives the five upstate zones A–E 5/11 of the weight; they carry ~35 % of
load and are NYISO's cheapest zones. So the hub actual sits $1.4–5.2/MWh below a like-for-like actual
in every year 2018–2025.

NYISO's zonal archive exists: `derive_actual_lmp.nyiso_zone_hourly` already builds every model zone's
series (simple mean of its constituent NYISO zones) from the public archive
(`scripts/data/fetch_nyiso_zonal_lmp.py`). Check: its hub column × system demand reproduces every
committed NYISO `rt_lw` / `da_lw` 2018–2025 **exactly** (16/16 values).

Probes: `scripts/probes/nyisonext22_c3a_phase0.py`, `scripts/probes/nyisonext22_zone_resolved_basis.py`
(in-memory re-score; nothing written).

## 2. What changes

1. **New** `scripts/data/derive_nyiso_zonal_lmp.py` writes
   `data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet` (`year, hour, zone, rt, da`;
   per model zone, `nyiso_zone_hourly` densified with the same `_densify_std` calendar the hub parquet
   uses), 2018–2025.
2. `scripts/data/derive_actual_lmp.py`: `ZONAL_LW_SOURCES` gains a `NYISO` entry (key `zone`,
   identity zone map). No other ISO is added.
3. `actual_lmp.json`: NYISO 2018–2025 `{rt,da}_lw`, `{rt,da}_lw_mon`, `src_lw` rewritten via
   `--lw-retrofit --isos NYISO`. Every non-NYISO block byte-identical; NYISO legacy fields
   (`rt`, `da`, `*_mon`, `*_pct`, `zones`, `src`) byte-identical.
4. Bench: surgical patch of `frontend/data/backcast/bench/NYISO/{2021..2025}.json.gz`
   `bench.avgLMP` (miso-292 method: same writer settings, original bytes round-trip, decoded part minus
   the patched keys equal to the original, fingerprint untouched, no regeneration).
   `check_bench_freshness --iso NYISO` must read 0 STALE.
5. Registered runs' `metrics.json` / sidecars re-scored; `status/NYISO.js` rebuilt.

## 3. Predicted fields

| year | rt_lw now | rt_lw predicted | da_lw now | da_lw predicted |
|---|---:|---:|---:|---:|
| 2018 | 38.14 | **40.46** | 37.49 | 39.53 |
| 2019 | 26.10 | **27.61** | 26.50 | 27.92 |
| 2020 | 20.58 | **21.90** | 20.28 | 21.43 |
| 2021 | 39.26 | **42.15** | 39.02 | 41.56 |
| 2022 | 81.12 | **86.28** | 77.79 | 82.59 |
| 2023 | 32.25 | **33.92** | 32.94 | 34.40 |
| 2024 | 38.12 | **39.57** | 38.74 | 39.99 |
| 2025 | 66.43 | **69.23** | 65.30 | 67.26 |

## 4. Predicted verdict rows (keeper re-score)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| C3a | +2.9 % P | −2.4 % P | +1.2 % P | −4.0 % P | **−11.6 % F** |
| C3b NRMSE | 0.108 P | 0.155 P | 0.122 P | 0.113 P | 0.181 P |

Flips: C3a 2021 FAIL→PASS, C3a 2025 PASS→FAIL. Determinations: `-2021` NOT-YET → **CALIBRATED**;
span CALIBRATED → **NOT-YET** (C3a 2025; C3c 2022–2025 is then no longer a lone failure and stands).
**ISO: NOT-YET under both bases.** Any mismatch is reported at full magnitude; nothing is adjusted to
match.

## 5. Against interest, stated

The basis was ruled for NYISO *after* the in-memory numbers were seen, as for MISO. It does not clear
the ISO: it moves the failure from 2021 to 2025. The zone basis also exposes a spatial error the hub hid:
the model prices Upstate_West too high (2021 $40.8 vs $29.9; 2022 $78.9 vs $60.6) and Long Island too
low (2021 $47.3 vs $62.3). That object is the ledgered CENTRAL EAST / LI spread, and it goes to the next
lane's queue, not to this change.
