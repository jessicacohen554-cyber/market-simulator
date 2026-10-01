# RESULT — storage dispatch & SOC vs actual (ERCOT, CAISO keepers), 2026-09-24

**Report-only. Not a calibration criterion. Zero LP.** Keeper determinations
re-scored byte-identically before/after (`calibration_verdict.py --json`).

## What already existed

Every solve since 2026-09-16 (caiso-284) writes `hourly/storage_<year>.parquet`
(charge / discharge / **SOC** per tech-hour) into the committed bundle. Both keepers
carry it for every year — so **no re-solve was needed**; the comparison is built
from committed sidecars. Gap found: the Run Explorer's EIA-930 "Storage" class
panel never rendered (no storage class in `class_hourly`), and the CAISO actual was
missing because EIA-930 folds CAISO batteries into `NG: OTH`.

## What was added

- `scripts/data/build_storage_dispatch_actuals.py` → `data/raw/storage-dispatch-actuals/`
  (CAISO Outlook batteries 2021–25 + DESR stand-alone SOC 2023–25; ERCOT EIA-930 BAT+UES).
- `scripts/lib/storage_compare.py` → per-year `storageCmp` payload block; hooked into
  `render_calibration_html.build_payload` so future registrations carry it.
- `scripts/backfill_storage_compare.py` → inserted into the two keeper payloads.
- Run Explorer → Charts tab: "Storage Dispatch — Model vs Actual" panel (month×hour
  average-day maps, 365×24 net maps + delta, SOC maps, fit/energy KPIs).

## Numbers (model / actual; net = discharge − charging)

| ISO | Year | Hourly r | Avg-day r | SOC shape r | Discharge TWh | Charging TWh | Peak dis. MW | Clock lag |
|---|---|---|---|---|---|---|---|---|
| ERCOT | 2024 (Oct–Dec, 1,681 h) | 0.698 | 0.927 | — | 0.463 / 0.456 | 0.547 / 0.604 | 5,424 / 3,785 | 0 |
| ERCOT | 2025 | 0.812 | 0.935 | — | 3.884 / 3.876 | 4.569 / 5.101 | 8,771 / 8,664 | 0 |
| CAISO | 2022 ⚠ | 0.787 | 0.910 | — | 2.374 / 2.816 | 2.793 / 1.788 | 2,664 / 2,962 | 0 |
| CAISO | 2023 | 0.836 | 0.932 | 0.579 | 3.804 / 4.466 | 4.475 / 4.574 | 4,163 / 4,781 | 0 |
| CAISO | 2024 | 0.838 | 0.904 | 0.736 | 7.066 / 8.386 | 8.334 / 9.626 | 6,915 / 7,849 | −1 |
| CAISO | 2025 | 0.862 | 0.906 | 0.787 | 10.526 / 12.479 | 12.383 / 14.401 | 9,059 / 10,707 | −1 |

⚠ CAISO 2022 source under-reports charging (discharge > charge); shape only.

## Readings (observations, not verdicts)

- **Shape is good in both ISOs** (avg-day r 0.90–0.94): charge midday, discharge at the
  evening ramp.
- **CAISO throughput is ~15% low** every clean year (2023–25), and peak discharge ~1–1.6 GW
  low. Candidate causes to check before any lever: fleet MW/MWh coverage vs the
  Outlook fleet (hybrid battery halves), the AS reservation / SOC floor, the measured
  shape anchor. Not investigated here.
- **ERCOT discharge energy matches** (3.88 vs 3.88 TWh) but model **peak charging is
  ~2.8 GW higher** than actual (8.9 vs 6.1 GW) — sharper, more concentrated charging.
  Model charging is 0.5 TWh lower → higher implied RTE than the fleet's ~76% (EIA-930
  UES may also carry auxiliary load).
- **CAISO 2024–25 best lag −1 h** (2022–23: 0). Could be a source clock change or a real
  one-hour timing offset; worth checking against DESR RTD EN before reading it as model.
- ERCOT SOC vs CAISO SOC levels are not comparable to actual (stand-alone-only actual;
  ERCOT hour-varying energy cap puts SOC up to ~4% above the sidecar's static
  `energy_cap_mwh` in some hours — the LP bound is the hourly measured-capability cap,
  the sidecar reports the nominal).

## Retrievability

All inputs committed; the panel regenerates from `main` at zero LP. Source downloads
re-fetch via the build script (~5 min).
