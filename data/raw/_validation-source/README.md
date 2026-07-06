# _validation-source — raw

Calibration/validation benchmark targets — a heterogeneous set of "what
actually happened" series the backcast is scored against. Leading `_` marks
it as not yet migrated to the `data/clean` curation seam (`data/README.md`).

| File(s) | Producing script | Source |
|---|---|---|
| `wecc_intertie_lmp_hourly_CAISO.parquet` | `scripts/fetch_caiso_intertie_lmp.py` | CAISO OASIS `PRC_LMP` DAM query at Malin/Palo Verde intertie scheduling points |
| `actual_lmp_hourly_{MISO,...}.parquet`, Carolinas FERC-714 proxy | `scripts/fetch_neighbor_lmp.py` | `docs.misoenergy.org/marketreports/<date>_{rt_lmp_final,da_expost_lmp}.csv`; FERC Form 714 Part II Schedule 6 |
| `actual_lmp_hourly_zonal_MISO.parquet` | `scripts/derive_miso_hub_lmp.py` | reduces `data/raw/lmp-data/MISO/` hub stagings |
| `calibration_reference.json`, per-year `*_renewable_capacity.csv` | `scripts/build_calibration_reference.py` | EIA-860 |
| `actual_lmp_hourly_ERCOT.parquet` (etc.) | `scripts/derive_actual_lmp.py` | per-ISO LMP sources under `data/raw/lmp-data/` |
| `actual_lmp_zonal_ERCOT.parquet` | `scripts/build_ercot_hsl.py` / ERCOT zonal derivation | ERCOT settlement-point data |
| `pjm_border_lmp_hourly_MISO.parquet` | `scripts/build_pjm_border_lmp_miso.py` | PJM/MISO seam LMP |
| `ct_deployment_floor_{CAISO,ERCOT,NEISO,NYISO,PJM}.parquet`, `reliability_deployment_floor_ERCOT.parquet` | `scripts/derive_reliability_deployment.py` / `scripts/derive_ct_deployment.py` | model-side derived reliability-deployment floors |
| `offer_curve_dam_hrmults*.json`, `offer_curve_deltas_*.json` | `scripts/derive_dam_offer_hrmults.py` | ERCOT DAM offer archives |
| `ercot_ordc_lolp_params.csv`, `pjm_ordc_curve.csv`, `cf_emd_baseline_ERCOT.json` | model-side derived reference curves | — |
| `capacity_actuals_{ercot,pjm}.csv`, `actual_as_reserve_NYISO.parquet` | validation reconciliation inputs | EIA-860/923 |

`scripts/curate_validation.py` is the reconciler that reads only the
already-materialized artifacts here (EIA-860 renewable capacity, EIA-923
by-fuel generation, eGRID 2023 emissions, EIA-930 demand totals, Henry Hub
gas price, historical DA LMP) into the `validation` clean datatype — it does
not fetch anything itself.

**Known gap:** `NYISO_2024_renewable_capacity.csv` is absent (2023 and 2025
are present) — a hole in the per-year series, not yet backfilled.

**Regeneration:** each file regenerates from its listed script and the raw
sources those scripts already cite; none of this directory's content is
hand-entered.
