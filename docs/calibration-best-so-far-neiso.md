# NEISO calibration — best config so far

> **DETERMINATION (2026-06-22, scorer): CALIBRATED-WITH-CAVEATS** for the
> registered keeper `neiso-23-outage-btm` (`python scripts/calibration_verdict.py
> --run-id 2026-06-21-neiso-23-outage-btm`; bundle
> `results/calibration/neiso_23_outage_btm`). This is the **best determination
> the rubric allows** for NEISO today: C1 fuel-mix, C2 system volume, C3a mean
> LMP, C3b price shape, C4 dispatch correlation and **C6 governance all PASS**
> (truthful attestation present), with **zero caveats and zero FAILs**. The grade
> is capped at CALIBRATED-WITH-CAVEATS solely by **three SKIPPED soft criteria**
> whose series are not in the committed payload — this is the rubric's intended
> cap ("you may not claim a *fully* calibrated ISO while its CO2 and scarcity
> tail are unscored"), not a model defect.

## The three SKIPPED soft criteria — decision: legitimately data-blocked

Each is **unavailable in the committed reporting payload**, not out of tolerance.
Surfacing them is a shared render-pipeline feature (`build_payload` would need to
emit model `co2` / `storage.throughput_twh` / non-ERCOT scarcity-`ordc` blocks
and the bench the matching eGRID / EIA-923-throughput / hourly-LMP-tail actuals),
which is a separate workstream affecting every ISO and gated by the ERCOT
byte-identity regression guard — out of scope for this BTM/attestation pass.

- **C3c price tail / scarcity** — the per-ISO tail proxy for NEISO is hours with
  zonal LMP > $300/MWh. The model hourly LMP (`system.parquet`) and the actual
  (`data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet`) both exist, but
  the `ordc.hoursGt200` payload block is emitted only on the ERCOT
  scarcity-overlay path; no NEISO overlay → SKIPPED. Data-blocked in payload.
- **C5a CO2 vs eGRID** — `build_payload` emits no model `co2` block for any ISO
  today; the eGRID NEISO actual is not threaded into the bench. SKIPPED.
- **C5b storage throughput** — `build_payload` emits no model `storage` block;
  the EIA-923/930 NEISO battery+PS throughput actual is not threaded. SKIPPED.

## Outage-cooling check (net-load outage filter) — C3a confirmed PASS

The net-load outage filter cools 2023/24 load-weighted LMP, but C3a (mean LMP vs
actual RT, ±8%) **still PASSes every year**: 2023 −4.6% (model 34.06 / actual
35.70), 2024 −1.3% (39.0 / 39.5), 2025 +5.6% (69.6 / 65.89). No caveat needed.

## Reproduce

```
python scripts/replay_keeper.py results/calibration/neiso_23_outage_btm   # byte-faithful re-solve (already keeper)
python scripts/calibration_verdict.py --run-id 2026-06-21-neiso-23-outage-btm
```
