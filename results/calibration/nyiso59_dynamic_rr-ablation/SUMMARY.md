# NYISO 59 dynamic-RR — zero-forcing ablation twin (rule 21 / D-3)

The `nyiso59_dynamic_rr` recipe verbatim (keeper nyiso-56 config + measured
hourly reserve requirements, #1344 Ask-B B2+B3) with **every merchant
floor/bridge zero-forced** (`ScenarioConfig.as_zero_forcing_ablation`;
`ablation_of: nyiso59_dynamic_rr` recorded in `run_config.json`).

Floors-off prices sit **above** the main arm (2023 simple-mean 33.08 vs
29.49; 2024 35.13 vs 31.90) — the reliability floors force cheap downstate
steam-base energy at min-gen and suppress the LMP; they do not manufacture
the scarcity tail (2023 max is 1341.35 $/MWh in both arms — the tail is the
measured-requirement reserve co-opt, present with floors off). The main
arm's D-2 forced energy (ST_GAS 3.1/4.8/5.1 TWh) is what the floors buy;
both duty classes still under-run the measured actuals with floors on, so
the floors are commitment scaffolding, not the dispatch model (rule 20).

Registered beside the main run per rule 21:
`2026-07-10-nyiso-59-dynamic-rr-ablation`.
