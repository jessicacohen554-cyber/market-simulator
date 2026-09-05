# Scenario campaign rollup — neiso

Total is the **six-ISO modeled system**, NOT a national figure.

Outside this total: SPP, the Southeast (Southern/TVA/Duke and the rest of SERC), and the non-ISO West (the WECC balancing areas outside CAISO). The six modeled ISOs are roughly two thirds of US load; the remaining third is not modeled and is not estimated here.

## Coverage

| case | years | n_isos | isos | isos_missing |
|---|---|---|---|---|
| CARB | 1 | 1 | NEISO | ERCOT+CAISO+MISO+PJM+NYISO |
| REF | 1 | 1 | NEISO | ERCOT+CAISO+MISO+PJM+NYISO |

## Modeled-system CO2 (Mt) — six-ISO modeled system

| case | year | emissions_mt | import_co2_mt_reported | unserved_mwh |
|---|---|---|---|---|
| CARB | 2026 | 13.599 | 6.427 | 0.000 |
| REF | 2026 | 16.308 | 4.572 | 0.000 |

## CO2 delta vs `REF` (Mt)

Final campaign year **2026**; the cumulative column is the running sum of the per-year delta over every year in the campaign.

| scope | case | emissions_mt_delta | cumulative_emissions_mt_delta |
|---|---|---|---|
| NEISO | CARB | -2.709 | -2.709 |
| six-ISO modeled system | CARB | -2.709 | -2.709 |

## Side lines — reported beside the total, never inside it

1. **Import-attributed CO2.** import_co2_mt_reported is a REPORTED-ONLY disclosure line and is NEVER added into emissions_mt: the LP prices border carbon in the tranche VOM and holds import emission rates at zero so the scored total stays on the eGRID in-ISO generation basis. Tranche emission factors are the ISO's published ladder where one exists (CAISO IMPORT_TRANCHE_EF), zero for the contracted firm Hydro-Quebec seams (HQ_PhaseII, Highgate, HQ_hydro), and otherwise the CARB unspecified default 0.428 tCO2/MWh — a disclosed upper bound, not a measured seam rate.
2. **Unserved energy (MWh).** The slack column's annual energy. A case
   whose CO2 falls while unserved energy rises has not decarbonized; it
   has shed load. Read the two together, always.
3. **ISOs not modeled.** Outside this total: SPP, the Southeast (Southern/TVA/Duke and the rest of SERC), and the non-ISO West (the WECC balancing areas outside CAISO). The six modeled ISOs are roughly two thirds of US load; the remaining third is not modeled and is not estimated here.

A blank side-line cell means that run's cache was not on disk when the
rollup ran, so the line could not be reconstructed — it is never a zero.
