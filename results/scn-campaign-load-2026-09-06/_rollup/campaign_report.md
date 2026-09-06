# Scenario campaign rollup — scn-campaign-load-2026-09-06

Total is the **six-ISO modeled system**, NOT a national figure.

Outside this total: SPP, the Southeast (Southern/TVA/Duke and the rest of SERC), and the non-ISO West (the WECC balancing areas outside CAISO). The six modeled ISOs are roughly two thirds of US load; the remaining third is not modeled and is not estimated here.

## Coverage

| case | years | n_isos | isos | isos_missing |
|---|---|---|---|---|
| LOAD-HI | 5 | 6 | ERCOT+CAISO+MISO+PJM+NYISO+NEISO |  |
| LOAD-HI-ORGANIC | 5 | 4 | ERCOT+CAISO+MISO+NYISO | PJM+NEISO |
| REF | 5 | 6 | ERCOT+CAISO+MISO+PJM+NYISO+NEISO |  |

## Modeled-system CO2 (Mt) — six-ISO modeled system

| case | year | emissions_mt | import_co2_mt_reported | unserved_mwh |
|---|---|---|---|---|
| LOAD-HI | 2026 | 1129.574 | 16.983 | 2996404.572 |
| LOAD-HI | 2027 | 1250.400 | 18.626 | 73878369.450 |
| LOAD-HI | 2028 | 1334.380 | 25.335 | 243466550.774 |
| LOAD-HI | 2029 | 1426.329 | 29.401 | 399447070.752 |
| LOAD-HI | 2030 | 1529.256 | 34.841 | 645054639.677 |
| LOAD-HI-ORGANIC | 2026 | 701.988 | 10.605 | 6172398.632 |
| LOAD-HI-ORGANIC | 2027 | 768.141 | 10.507 | 78805229.839 |
| LOAD-HI-ORGANIC | 2028 | 803.155 | 11.653 | 233853905.334 |
| LOAD-HI-ORGANIC | 2029 | 846.880 | 11.582 | 374521510.669 |
| LOAD-HI-ORGANIC | 2030 | 895.528 | 13.488 | 581054804.117 |
| REF | 2026 | 1026.953 | 15.750 | 493199.485 |
| REF | 2027 | 1097.023 | 15.444 | 4850672.009 |
| REF | 2028 | 1160.045 | 18.849 | 42130357.816 |
| REF | 2029 | 1200.803 | 19.962 | 76903801.308 |
| REF | 2030 | 1277.385 | 24.510 | 130138093.197 |

## CO2 delta vs `REF` (Mt)

Final campaign year **2030**; the cumulative column is the running sum of the per-year delta over every year in the campaign.

| scope | case | emissions_mt_delta | cumulative_emissions_mt_delta |
|---|---|---|---|
| CAISO | LOAD-HI | 10.231 | 33.292 |
| CAISO | LOAD-HI-ORGANIC | 10.344 | 33.629 |
| ERCOT | LOAD-HI | 13.407 | 130.355 |
| ERCOT | LOAD-HI-ORGANIC | 13.410 | 125.728 |
| MISO | LOAD-HI | 72.862 | 246.631 |
| MISO | LOAD-HI-ORGANIC | 72.793 | 245.430 |
| NEISO | LOAD-HI | 1.408 | 4.796 |
| NYISO | LOAD-HI | 5.340 | 16.953 |
| NYISO | LOAD-HI-ORGANIC | 5.420 | 17.211 |
| PJM | LOAD-HI | 148.623 | 475.704 |
| six-ISO modeled system | LOAD-HI | 251.871 | 907.731 |
| six-ISO modeled system | LOAD-HI-ORGANIC | -381.856 | -1746.516 |

## Side lines — reported beside the total, never inside it

1. **Import-attributed CO2.** import_co2_mt_reported is a REPORTED-ONLY disclosure line and is NEVER added into emissions_mt: the LP prices border carbon in the tranche VOM and holds import emission rates at zero so the scored total stays on the eGRID in-ISO generation basis. Tranche emission factors are the ISO's published ladder where one exists (CAISO IMPORT_TRANCHE_EF), zero for the contracted firm Hydro-Quebec seams (HQ_PhaseII, Highgate, HQ_hydro), and otherwise the CARB unspecified default 0.428 tCO2/MWh — a disclosed upper bound, not a measured seam rate.
2. **Unserved energy (MWh).** The slack column's annual energy. A case
   whose CO2 falls while unserved energy rises has not decarbonized; it
   has shed load. Read the two together, always.
3. **ISOs not modeled.** Outside this total: SPP, the Southeast (Southern/TVA/Duke and the rest of SERC), and the non-ISO West (the WECC balancing areas outside CAISO). The six modeled ISOs are roughly two thirds of US load; the remaining third is not modeled and is not estimated here.

A blank side-line cell means that run's cache was not on disk when the
rollup ran, so the line could not be reconstructed — it is never a zero.
