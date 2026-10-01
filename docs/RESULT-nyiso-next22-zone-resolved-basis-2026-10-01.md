# RESULT — NYISO-NEXT-22: NYISO C3a/C3b actual is now zone-resolved (zero LP)

```
LANE      : NYISO-NEXT-22 (owner ruling 2026-10-01, card "Basis": "Adopt for NYISO now")
PRECOMMIT : docs/PRECOMMIT-nyiso-next22-zone-resolved-basis-2026-10-01.md (b597e949, pushed before any change)
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021 stamped), unchanged
LP        : none. No shard launched.
```

## 1. Phase 0 — where the 2021 "over-price" lived

The handoff's lead item was the 2021 C3a level (+10.4 %). A zone × month × hour-band decomposition against the
NYISO 5-minute zonal RT archive (`scripts/probes/nyisonext22_c3a_phase0.py`) found that, **on a zone-resolved
actual, 2021 is only ~+3-4 %**. The scored +10.4 % came mostly from the benchmark basis:

- NYISO's `rt_lw` was the **hub** (simple mean of the 11 internal zones) × measured **system** demand.
- The model side of C3a is zone-demand-weighted.
- The hub gives upstate zones A–E 5/11 of the weight; they carry ~35 % of load and are the cheapest zones.
  So the hub sat $1.3–5.2/MWh below the like-for-like actual in every year 2018–2025.

This is the rubric v2.4 definition ("zone-resolved where a zonal archive exists") not yet applied to NYISO —
the same gap miso-294 closed for MISO the same day.

## 2. What changed

1. New `scripts/data/derive_nyiso_zonal_lmp.py` → `data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet`
   (2018–2025, `year, hour, zone, rt, da`), from `derive_actual_lmp.nyiso_zone_hourly` (no new construction).
   Check: the same frame's hub × system demand reproduces all 16 committed hub `rt_lw`/`da_lw` values exactly.
2. `derive_actual_lmp.ZONAL_LW_SOURCES` gains `NYISO` (identity zone map). No other ISO.
3. `actual_lmp.json`: NYISO 2018–2025 `*_lw` fields + `src_lw` retrofitted. Every non-NYISO block and every
   NYISO legacy field byte-identical (checked).
4. Bench `NYISO/{2021..2025}.json.gz` `avgLMP` surgically patched (miso-292 method; round-trip asserted;
   `check_bench_freshness --iso NYISO`: **0 STALE**).
5. Both runs re-scored (`metrics.json`), holdout stamp refreshed, sidecar text corrected (audit E5), status
   rebuilt. `tests/curation/test_lw_zonal_registry.py`: 5 pass. `audit_keepers --iso NYISO`: PASS (E14 clear).

## 3. Numbers — every PRECOMMIT value reproduced exactly

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `rt_lw` hub (before) | 38.14 | 26.10 | 20.58 | 39.26 | 81.12 | 32.25 | 38.12 | 66.43 |
| `rt_lw` zone-resolved | 40.46 | 27.61 | 21.90 | 42.15 | 86.28 | 33.92 | 39.57 | 69.23 |

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| C3a hub → zone | +10.4 F → **+2.9 P** | +3.8 → −2.4 | +6.5 → +1.2 | −0.3 → −4.0 | −7.9 → **−11.6 F** |
| C3b hub → zone | 0.155 → 0.108 | 0.161 → 0.155 | 0.138 → 0.122 | 0.118 → 0.113 | 0.143 → 0.181 |

**Determinations:** `-2021` NOT-YET → **CALIBRATED**. Span CALIBRATED → **NOT-YET** (C3a 2025; C3c 2022–2025 is
no longer a lone failure, so it stands as FAIL). **ISO: NOT-YET** (unchanged).

## 4. Reading

- **Against interest:** the basis was ruled after the in-memory numbers were seen, as for MISO. It does not clear
  the ISO; it moves the failure from 2021 to 2025.
- **The residual is spatial.** On the zone basis the model prices Upstate_West too high (2021 $40.8 vs $29.9;
  2022 $78.9 vs $60.6) and Long Island too low (2021 $47.3 vs $62.3; 2022 $90.2 vs $107.9). The upstate half is
  the ledgered CENTRAL EAST object (`nyiso_fg_split` R; owner ruling stands).
- **C3a 2025 (−11.6 %)** is downstate afternoon/evening and the top actual-price decile (−$10.0 of the −$8.0
  miss), with oil-marginal hours $141 vs $172. That is the item-2 object (dual-fuel cap measured, tail ledgered
  under C3c), now load-bearing.
- No mechanism cell moves.

## 5. Retrievability

No solve; nothing on shard disk. All artifacts are in this PR. The RT/DA zonal zips are gitignored and
regenerable (`fetch_nyiso_zonal_lmp.py`). **Gotcha:** a `--kind da` fetch rewrites the `NYISO_zonal_hourly.zip`
container with only the requested months — always stage the full 2018–2025 range.
