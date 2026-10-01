# PRECOMMIT — miso-294 Part A: MISO C3a/C3b actual becomes ZONE-RESOLVED (zero LP)

```
LANE      : miso-294 (owner ruling "Basis: Adopt for MISO now", DESIGN-miso293 §8, 2026-10-01)
KEEPER    : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span), unchanged
LP        : none
WRITTEN   : before any code change, retrofit or re-score
```

## 1. What changes

The MISO `avgLMP.{rt,da}_lw` / `{rt,da}_lw_mon` / `src_lw` fields in
`data/raw/_validation-source/actual_lmp.json` (2019–2025) move from the single-hub construction
(INDIANA.HUB × measured system demand) to the rubric v2.4 **zone-resolved** construction ERCOT
already uses: per model zone, that zone's hub series from
`actual_lmp_hourly_zonal_MISO.parquet` (multi-hub zones = simple mean of member hubs, e.g.
MISO-South = mean of ARKANSAS/LOUISIANA/MS/TEXAS), weighted by that zone's measured demand
(`eia_loader.load_demand`), then zone-demand-weighted across zones. **MISO-Plains** (no hub) uses
the declared MINN.HUB + ILLINOIS.HUB mean proxy (`scripts/report_miso_zonal_gates.py`,
`derive_miso_hub_lmp.py` D6). Applies to every year 2019–2025 whatever the result.

## 2. Implementation seam

- `scripts/data/derive_actual_lmp.py::_lw_fields` — the ERCOT `if iso == "ERCOT"` branch is
  replaced by a per-ISO **zonal-source registry** (`ZONAL_LW_SOURCES`: parquet name, series-key
  column, model-zone → series map). ERCOT's entry carries `ERCOT_MODEL_ZONE_TO_LZ` unchanged;
  MISO's entry derives its zone → hubs map from the archive's own `zone` column plus the Plains
  proxy. `src_lw` comes from the registry entry. ISOs not in the registry keep the system-hub
  branch untouched.
- **Scope guard:** only ERCOT and MISO are in the registry. No other ISO is widened (the cross-ISO
  question is not ruled). Proof of non-regression: `--lw-retrofit` for ERCOT re-run into the JSON
  and the ERCOT block byte-compared before/after; every non-MISO block byte-identical.
- Bench: surgical patch of `frontend/data/backcast/bench/MISO/<year>.json.gz` `bench.avgLMP`
  (the four numeric keys, plus `src_lw` if present in the part), miso-292 method: same writer
  settings (`json.dumps`, gzip 9, mtime 0), round-trip assert of original bytes, decoded part
  minus the patched keys equal to the original, `meta.builderFingerprint` untouched. No bench
  regeneration (miso-266 hazard).

## 3. Predicted fields (DESIGN-miso293 §5 probe output, Plains proxied)

| year | rt_lw now | rt_lw predicted | da_lw predicted |
|---|---:|---:|---:|
| 2019 | 27.15 | **25.67** | 26.20 |
| 2020 | 22.99 | **21.97** | 22.21 |
| 2021 | 40.63 | **39.23** | 40.43 |
| 2022 | 73.45 | **63.25** (scored Jan–Oct mask: 63.21) | 63.70 |
| 2023 | 32.85 | **30.19** | 31.00 |
| 2024 | 32.30 | **29.28** | 29.67 |
| 2025 | 45.46 | **42.12** | 42.68 |

## 4. Predicted verdict rows (keeper re-score)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C3a | +8.7 % P | **+11.6 % F** | −5.6 % P | −5.1 % P | +8.4 % P | +5.1 % P | −1.1 % P |
| C3b NRMSE | 0.114 P | 0.165 P | **0.201 F** | 0.122 P | 0.104 P | 0.101 P | 0.083 P |

Flips: C3a 2020 PASS→FAIL, C3a 2022 FAIL→PASS, C3b 2022 FAIL→PASS. Full span NOT-YET on
{C1 ST_GAS 2019, C3a 2020, C3b 2021}. Train tier 2023–2025 stays CALIBRATED (C3c ledgered).
Any mismatch is reported at full magnitude; nothing is adjusted to match.
