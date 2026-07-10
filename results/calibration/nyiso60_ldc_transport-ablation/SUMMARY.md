# NYISO 60 LDC-transport — zero-forcing ablation twin (rule 21 / D-3)

The `nyiso60_ldc_transport` recipe verbatim (keeper nyiso-59 config + the
G-13 per-zone daily LDC-transport delivered-gas index,
`nyiso_downstate_ct_gas_daily`) with **every merchant floor/bridge
zero-forced** (`ScenarioConfig.as_zero_forcing_ablation`;
`ablation_of: nyiso60_ldc_transport` recorded in `run_config.json`).

Floors-off prices sit **above** the main arm (simple-mean 32.20 vs 29.05 in
2023, 35.07 vs 31.96 in 2024, 60.09 vs 54.08 in 2025) — the reliability
floors force cheap downstate steam-base energy at min-gen and suppress the
LMP; they do not manufacture the scarcity tail (the 2023 tail max
$2,000/MWh is present in both arms — the tail is the measured-requirement
reserve co-opt plus the measured daily delivered gas, present with floors
off). The main arm's D-2 forced energy (ST_GAS 3.3/4.8/4.9 TWh at
`reliability_floor`) is what the floors buy; the duty classes still
under-run the measured actuals with floors on, so the floors are commitment
scaffolding, not the dispatch model (rule 20).

Registered beside the main run per rule 21:
`2026-07-10-nyiso-60-ldc-transport-ablation`.
