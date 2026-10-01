# PRECOMMIT — SOCO-15: the COD-seam cross-ISO repair (owner card S12)

**Lane:** SOCO-15 `[FABLE]` · **Date:** 2026-09-13 · **Branch:** `claude/soco-15-cod-ramp-b0080o` · **Base:** `origin/main` **33a7c9615f0dbc9aa19e58a976de29df462059d6** (the charter's pin; `main` advanced to `0c39824c` during the session — SOCO-22 rubric v3.8 and caiso-281 intake, neither touching this lane's files — and the base is deliberately left at the pin).
**Ruling:** owner card S12 (desk r#3, 2026-09-13): *"Charter a cross-ISO repair lane BEFORE SOCO-20."* SOCO-20 is blocked until this lane lands.
**Evidence base:** `docs/handoffs/FINDING-soco-10-2026-09-13.md` §2; `docs/multi-iso/soco-data-audit.md` §4.4; `docs/multi-iso/soco-addition-plan-2026-09.md` §3 card S12.
**Registered before any solve** (rule 29 `[R-SCREEN]`). The arm SHA is pinned in §7's addendum after this document is pushed; every shard prompt names that SHA and nothing else.

---

## 0. The defect, restated at the grain the LP actually has

SOCO-10 measured it by calling the code: `cod_ramp.effective_cod` ALWAYS let the plant-collapsed, capacity-weighted **mean** COD win a generator's ONLINE date; the per-unit preference existed only for RETIREMENT (the Homer City seam). Reproduced live in this session, byte-for-byte:

```
load_cod_map()[649] -> (2005, 5, None, None)   Vogtle   (units 1/2 1987-89, 3/4 2023-24)
load_cod_map()[3]   -> (1991, 3, None, None)   Barry    (coal 1950s-70s, CC 2000, A3 2023-11)
load_cod_map()[56]  -> (2023, 9, None, None)   Lowman   (greenfield: mean IS the units' date)
```

What SOCO-10 could not see from the module alone, and what changes the repair's shape: **every one of the seven registered keepers runs the CAMPD-bin fleet path** (`use_campd_bins=True`; six of them `plant_level_fleet=True`; ERCOT the curated sheet). The LP unit is therefore mostly a **(plant, group) bin**, and a bin has no `Operating Month` of its own — its `online_year` is the registry / COD-year estimate `bins_to_fleet` stamps on every tranche. Only nuclear, oil and biomass (and any thermal plant the synthesis did not bin) reach the LP as raw EIA-860 units. So "prefer the generator's own Operating Month" has an object only at the raw-unit grain; at the bin grain the measured quantity is the **monthly online-capacity fraction of the bin's own constituent units**. Both are the unit's own EIA-860 date, aggregated to the grain the LP dispatches (§3).

A second thing the loader hid: the processed `eia860_generators.parquet` carries `operating_year` but **not** `operating_month`, so `Generator.online_month` was the January default for every EIA-860 unit — a raw unit's "own" date was year-precise only. The repair bridges the month from the same vintage directory's raw operable sheet (100 % join coverage in every committed vintage directory, one null month per sheet).

## 1. Phase 0 — the census, reproduced (rule 29 clause 0)

### 1.1 SOCO-10's blast radius reproduces exactly

Root vintage `data/raw/eia-860/eia860_generator_operable.parquet`, **nameplate** basis, footprint = plant-level `Balancing Authority Code` (the processed generators parquet carries no SOCO rows, so the plant sheet's BA is the footprint for all eight), selection = units with `Operating Year` ∈ {2023, 2024, 2025} whose `load_cod_map()` plant year is earlier. Every number, plant count and unit count matches SOCO-10 §2 / audit §4.4 to the tenth of a MW:

| Footprint | SOCO-10 (MW) | reproduced (MW) | plants / units | **thermal-ramp-governed (MW)** | not governed by this seam (MW) |
|---|---:|---:|---:|---:|---:|
| SOCO | 3,040.3 | **3,040.3** | 6 / 9 | **3,040.3** | 0.0 |
| SPP | 1,127.4 | **1,127.4** | 9 / 19 | **625.4** | 502.0 |
| ERCOT | 1,091.4 | **1,091.4** | 13 / 21 | **490.2** | 601.2 |
| CAISO | 1,037.2 | **1,037.2** | 19 / 24 | **23.1** | 1,014.1 |
| MISO | 927.4 | **927.4** | 15 / 28 | **703.1** | 224.3 |
| PJM | 177.2 | **177.2** | 9 / 14 | **15.9** | 161.3 |
| NYISO | 72.9 | **72.9** | 11 / 19 | **64.2** | 8.7 |
| NEISO | 50.0 | **50.0** | 13 / 13 | **2.7** | 47.3 |

**The correction the reproduction surfaces (stated at the gate, not buried):** SOCO-10's census counted every technology. The COD ramp in `cod_ramp` governs only the thermal / nuclear / oil / biomass fleet the EIA-860 loader admits (`_map_fuel_type` ≠ None); solar, wind, hydro and storage ramp on their own vintage paths (`data.renewables`, `model.storage`), which already use each unit's own `Operating Month`. The last two columns split the blast radius accordingly. For SOCO nothing changes (all 3,040.3 MW is thermal: nuclear 2,228.0, gas_cc 774.0, gas_st 28.8, gas_ct 5.0, oil 4.5). For CAISO, PJM and NEISO the seam reaches only 1–3 % of the quoted number; SPP, ERCOT, MISO and NYISO keep 45–88 % of it. The governed MW by fuel: SPP gas_ct 608.4 / oil 17.0 · ERCOT gas_cc 244.0 / gas_ct 246.2 · MISO gas_ct 595.7 / gas_cc 97.8 / oil 8.0 / biomass 1.6 · NYISO gas_ct 42.0 / oil 22.2 · CAISO oil 20.0 / gas_ct 3.1 · PJM gas_ct 13.3 / oil 2.6 · NEISO gas_ct 2.7.

### 1.2 The defect runs in BOTH directions

The unit-grain mask diff (own `Operating Year/Month` vs the plant-collapsed date, retirement held identical in both arms, governed units only, nameplate MW × months) over the years each keeper carries shows **phantom-LATE** as well as phantom-early: a pre-existing unit at a plant whose mean is dragged past the solved year is held offline. ERCOT 2023 carries 1,815 MW-months of phantom-late against 2,348 early; PJM 2023 1,371 late against 872 early; MISO 2020 881 late. SOCO is early-only:

| year | units phantom-early | MW-months phantom-early | units phantom-late | MW-months phantom-late |
|---:|---:|---:|---:|---:|
| 2023 | 9 | 27,897.8 | 0 | 0.0 |
| 2024 | 3 | 3,392.1 | 0 | 0.0 |
| 2025 | 1 | 22.8 | 0 | 0.0 |

(SOCO 2023: Vogtle 3 Jan–Jun 6,684 + Vogtle 4 Jan–Dec 13,368 + Barry A3 Jan–Oct 7,740 + four small rows = 27,897.8 MW-months = 20.37 TWh of nameplate availability; SOCO-10's measured-CF energy equivalents are +12.979 TWh nuclear in 2023 and +2.167 TWh in 2024, plus 2.3–4.6 TWh for Barry A3.)

### 1.3 The LP-grain availability-mask diff, every registered keeper, every year (27 bundle-years, zero LP)

Each keeper's fleet was rebuilt exactly as it solved — `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` (`run_year(fleet_only=True)` from the bundle's `meta.json`) — and for every LP unit the OLD mask (pre-SOCO-15 `effective_cod`, plant map always wins the online date) and the NEW mask (`generator_online_mask`) were computed on the identical generator list, the maps read from the directory the bundle's own vintage rule resolves (SPP tracks the solve year: `vintage_2023` / `vintage_2024` / root). Δ = Σ pmax × (new − old); "+" is capacity the plant mean had wrongly held OFFLINE, "−" capacity it had wrongly held ONLINE; GWh-avail is the delta in available MWh at nameplate (an upper bound on any energy delta, since no unit runs above availability).

| ISO | year | LP units | fleet MW | units moved | MW-months → online (+) | MW-months → offline (−) | GWh-avail (+) | GWh-avail (−) | −, % of fleet-avail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| CAISO | 2023 | 1911 | 52,580 | 8 | 0.0 | -50.0 | 0.0 | -36.5 | -0.008 |
| CAISO | 2024 | 1905 | 52,533 | 7 | 0.0 | -49.8 | 0.0 | -36.3 | -0.008 |
| CAISO | 2025 | 1910 | 52,535 | 7 | 0.0 | -15.9 | 0.0 | -11.5 | -0.003 |
| ERCOT | 2021 | 2326 | 80,755 | 69 | 121.4 | -1,390.9 | 87.4 | -1,018.1 | -0.144 |
| ERCOT | 2022 | 2324 | 80,750 | 62 | 726.0 | -1,148.9 | 531.4 | -843.9 | -0.119 |
| ERCOT | 2023 | 2323 | 80,748 | 46 | 484.0 | -331.0 | 334.0 | -237.5 | -0.034 |
| ERCOT | 2024 | 2321 | 80,742 | 29 | 0.0 | -1,159.0 | 0.0 | -843.2 | -0.119 |
| ERCOT | 2025 | 2310 | 80,206 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| MISO | 2020 | 3657 | 165,289 | 64 | 607.2 | -8,183.3 | 443.3 | -5,973.5 | -0.413 |
| MISO | 2021 | 3632 | 164,441 | 55 | 27.8 | -7,626.3 | 20.4 | -5,565.4 | -0.386 |
| MISO | 2022 | 3619 | 163,569 | 39 | 0.0 | -7,090.7 | 0.0 | -5,175.5 | -0.361 |
| MISO | 2023 | 3598 | 163,384 | 20 | 0.0 | -6,909.6 | 0.0 | -5,044.0 | -0.352 |
| MISO | 2024 | 3586 | 163,231 | 18 | 0.0 | -6,335.3 | 0.0 | -4,621.3 | -0.323 |
| MISO | 2025 | 3566 | 162,070 | 12 | 0.0 | -2,685.7 | 0.0 | -1,946.7 | -0.137 |
| NEISO | 2023 | 875 | 30,820 | 2 | 0.0 | -3.7 | 0.0 | -2.6 | -0.001 |
| NEISO | 2024 | 865 | 30,794 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| NEISO | 2025 | 867 | 30,796 | 0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.000 |
| NYISO | 2022 | 873 | 47,005 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2023 | 870 | 46,534 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2024 | 867 | 46,430 | 2 | 0.0 | -37.8 | 0.0 | -27.6 | -0.007 |
| NYISO | 2025 | 867 | 46,228 | 2 | 0.0 | -22.0 | 0.0 | -16.0 | -0.004 |
| PJM | 2023 | 3650 | 210,055 | 10 | 601.3 | -23.9 | 360.8 | -17.5 | -0.001 |
| PJM | 2024 | 3656 | 210,065 | 2 | 0.0 | -21.5 | 0.0 | -15.7 | -0.001 |
| PJM | 2025 | 3659 | 210,172 | 2 | 0.0 | -8.0 | 0.0 | -5.8 | -0.000 |
| SPP | 2023 | 1124 | 58,034 | 2 | 0.0 | -33.0 | 0.0 | -24.1 | -0.005 |
| SPP | 2024 | 1138 | 57,565 | 6 | 0.0 | -48.6 | 0.0 | -35.3 | -0.007 |
| SPP | 2025 | 1192 | 60,740 | 4 | 0.0 | -2,794.9 | 0.0 | -2,027.3 | -0.381 |

Probe-side facts about the rebuild (they do not touch the generator list this diff measures): NYISO's `nyiso_li_lcr_tsl` / `nyiso_nyc_lcr_tsl` / `nyiso_seam_par_attribution` / `nyiso_seam_deliverability_envelope` and PJM's `pjm_measured_interface_limits` / `pjm_east_interface_cut` / `pjm_da_virtual_bids` / `measured_ramp_capability` read clean partitions or raw corpora not hydrated under `DATA PROFILE: code`; all are consumed in `model/interchange/*` or in `generators_to_fleet_arrays` after the fleet list is built, so they were overridden off for the fleet-only rebuild. The ERCOT keeper's `meta.json` carries `ercot_ep_gas_basis_receipts_fallback`, a ScenarioConfig field `replay_keeper.build_kwargs` does not route (it raises "not bound to solve_and_persist kwargs"); it was added to `_IGNORE` **in the probe process only** — a fuel-basis flag, no fleet effect. Both are the other lanes' plumbing, not this lane's files.

Per LP class, both directions (MW-months):

| ISO | LP class | MW-months → online (+) | MW-months → offline (−) |
|---|---|---:|---:|
| CAISO | CT_CHP | 0.0 | -0.3 |
| CAISO | CT_PEAKER | 0.0 | -34.4 |
| CAISO | oil | 0.0 | -81.0 |
| ERCOT | CC_CHP | 0.0 | -1,756.8 |
| ERCOT | CT_CHP | 0.0 | -700.0 |
| ERCOT | CT_PEAKER | 1,331.4 | -1,573.0 |
| MISO | CC_CHP | 15.0 | -1,556.6 |
| MISO | CC_REGULAR | 598.8 | 0.0 |
| MISO | CT_CHP | 8.6 | -249.8 |
| MISO | CT_PEAKER | 0.0 | -36,083.1 |
| MISO | ST_CHP | 0.0 | -189.5 |
| MISO | biomass | 12.6 | -114.2 |
| MISO | oil | 0.0 | -637.6 |
| NEISO | CT_PEAKER | 0.0 | -3.7 |
| NYISO | CT_CHP | 0.0 | -25.4 |
| NYISO | oil | 0.0 | -110.0 |
| PJM | CC_REGULAR | 601.3 | 0.0 |
| PJM | CT_CHP | 0.0 | -53.4 |
| SPP | CT_PEAKER | 0.0 | -2,813.5 |
| SPP | oil | 0.0 | -63.0 |

Top movers per ISO (the rows a lane will want to match):

| ISO | year | LP unit | class | pmax MW | old mask (Jan..Dec) | new mask | Δ MW-months |
|---|---:|---|---|---:|---|---|---:|
| CAISO | 2023 | `56134_0601` | oil | 3.0 | `111111111111` | `000000000000` | -36.0 |
| CAISO | 2024 | `56134_0601` | oil | 3.0 | `111111111111` | `000000000000` | -36.0 |
| CAISO | 2025 | `56134_0601` | oil | 3.0 | `111111111111` | `000111111111` | -9.0 |
| CAISO | 2023 | `CT_PEAKER_LA_BASIN_p56090_econc01` | CT_PEAKER | 1.1 | `111111111111` | `[0.83][0.83][0.83][0.83][0.83][0.83][0.83][0.83][0.83][0.83][0.83][0.83]` | -2.3 |
| ERCOT | 2024 | `CT_PEAKER_Houston_p65372_committed` | CT_PEAKER | 217.8 | `111111111111` | `[0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75]111` | -490.1 |
| ERCOT | 2022 | `CT_PEAKER_Houston_p65372_committed` | CT_PEAKER | 217.8 | `000000000000` | `0000000000[0.75][0.75]` | 326.7 |
| ERCOT | 2023 | `CT_PEAKER_Houston_p65372_committed` | CT_PEAKER | 217.8 | `000011111111` | `[0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75][0.75]` | 217.8 |
| ERCOT | 2021 | `CT_PEAKER_Houston_p63688_committed` | CT_PEAKER | 272.2 | `000000111111` | `000000[0.70][0.90][0.90]111` | -136.1 |
| MISO | 2020 | `CT_PEAKER_MISO-Indiana_p6137_econlo` | CT_PEAKER | 265.4 | `111111111111` | `[0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27]` | -2,317.4 |
| MISO | 2024 | `CT_PEAKER_MISO-Indiana_p6137_econlo` | CT_PEAKER | 265.4 | `111111111111` | `[0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27]` | -2,317.4 |
| MISO | 2022 | `CT_PEAKER_MISO-Indiana_p6137_econlo` | CT_PEAKER | 265.4 | `111111111111` | `[0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27]` | -2,317.4 |
| MISO | 2021 | `CT_PEAKER_MISO-Indiana_p6137_econlo` | CT_PEAKER | 265.4 | `111111111111` | `[0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27][0.27]` | -2,317.4 |
| NEISO | 2023 | `CT_PEAKER_Connecticut_p64515_econlo` | CT_PEAKER | 1.0 | `111111111111` | `001111111111` | -2.0 |
| NEISO | 2023 | `CT_PEAKER_Connecticut_p64515_econhi` | CT_PEAKER | 0.9 | `111111111111` | `001111111111` | -1.8 |
| NYISO | 2022 | `54808_DE1` | oil | 2.5 | `111111111111` | `000000000000` | -30.0 |
| NYISO | 2023 | `54808_DE1` | oil | 2.5 | `111111111111` | `000000000000` | -30.0 |
| NYISO | 2024 | `54808_DE1` | oil | 2.5 | `111111111111` | `000000000000` | -30.0 |
| NYISO | 2025 | `54808_DE1` | oil | 2.5 | `111111111111` | `000000001111` | -20.0 |
| PJM | 2023 | `CC_REGULAR_PJM_AEP_Ohio_p62949_committed` | CC_REGULAR | 883.9 | `001111111111` | `0[0.67][0.67]111111111` | 294.6 |
| PJM | 2023 | `CC_REGULAR_PJM_AEP_Ohio_p62949_peak` | CC_REGULAR | 234.5 | `001111111111` | `0[0.67][0.67]111111111` | 78.2 |
| PJM | 2023 | `CC_REGULAR_PJM_AEP_Ohio_p62949_econc01` | CC_REGULAR | 114.2 | `001111111111` | `0[0.67][0.67]111111111` | 38.1 |
| PJM | 2023 | `CC_REGULAR_PJM_AEP_Ohio_p62949_econc02` | CC_REGULAR | 114.2 | `001111111111` | `0[0.67][0.67]111111111` | 38.1 |
| SPP | 2025 | `CT_PEAKER_SPP-North_p57881_econlo` | CT_PEAKER | 350.0 | `111111111111` | `[0.33][0.33][0.33][0.45][0.45][0.73][0.73]11111` | -1,281.9 |
| SPP | 2025 | `CT_PEAKER_SPP-North_p57881_econhi` | CT_PEAKER | 315.4 | `111111111111` | `[0.33][0.33][0.33][0.45][0.45][0.73][0.73]11111` | -1,155.2 |
| SPP | 2025 | `CT_PEAKER_SPP-North_p57881_peak` | CT_PEAKER | 53.4 | `111111111111` | `[0.33][0.33][0.33][0.45][0.45][0.73][0.73]11111` | -195.6 |
| SPP | 2025 | `CT_PEAKER_SPP-North_p57881_committed` | CT_PEAKER | 44.3 | `111111111111` | `[0.33][0.33][0.33][0.45][0.45][0.73][0.73]11111` | -162.1 |

Reading the table: **MISO** moves most — 0.3–0.4 % of fleet availability every year, almost all `CT_PEAKER`; the largest single object is plant 6137's CT bin (505 MW), 73 % of whose nameplate is 2025-COD units that the plant's 1970s coal mean had online in every year 2020–2024. **SPP 2025** is the same shape (2,795 MW-months of `CT_PEAKER`). **ERCOT** is the two-direction case: plant 65372's Houston CT bin was held fully offline through Nov–Dec 2022 and then fully online from May 2023, where its units were 75 % online from Nov 2022 and 100 % only from Oct 2024. **PJM 2023** is phantom-late: plant 62949 (AEP Ohio CC, 1.4 GW) was 67 % online in Feb–Mar 2023, not offline. **CAISO, NEISO, NYISO, PJM 2024–25 and SPP 2023–24** move by single-digit MW objects — below anything a band can see.

## 2. Exit-condition evidence gathered before the solve

**(a) Cache keys byte-identical (gate G8).** No `ScenarioConfig` field, no default flip, no `results/cache.py` edit, and the solve-surface fingerprint modules (`config/solve_surface.py::SURFACE_MODULES`) are config tables untouched here. Proof: each keeper's `run_config.json` `scenario_config` was rebuilt into `ScenarioConfig(**…).cache_key()` on the pinned `origin/main` tree and on this branch — identical for all seven (`caiso bab5e9b08681e54c · ercot 0f89d4c5f45043f7 · miso b35a8f20b73a5fbf · neiso 28266b333667e16f · nyiso 7e0dc0344f297fc2 · pjm b05e09c319c2c5f5 · spp 6d6205e381e982c2`). `tests/regression/test_persisted_identity.py`: 23 pass; the one failure, `test_solve_surface_fingerprint_is_pinned[NYISO]` (210 rows vs a pin of 209), **reproduces with this lane's changes stashed on `33a7c961`** — it is pre-existing on `main` (a NYISO registry row landed without advancing the pin) and is not this lane's to move. The `SOLVE_EPOCHS` ledger is left EMPTY: appending an epoch would re-key every keeper, which the charter forbids, and the D77 precedent (owner ruling Q54 row 4) keeps a results-moving seam repair as prose.

**(b) Greenfield still ramps, both directions demonstrated.** Old module (`git show 33a7c961:src/market_sim/data/cod_ramp.py`) against the repaired resolver on the live root vintage:

```
case                                     OLD (33a7c961)   NEW (SOCO-15)
Vogtle 3 raw unit (649,'3') 2023         111111111111     000000111111
Vogtle 4 raw unit 2024                   111111111111     000111111111
Barry CC bin (3,CC_REGULAR) 2023         111111111111     [0.58]x10 11      (1,071 of 1,845 MW online until A3's November)
Lowman greenfield bin (56) 2023          000000001111     000000001111
```

`tests/unit/data/test_cod_ramp.py` (71 pass, 0 fail): `test_brownfield_unit_prefers_own_online_date_over_plant_mean`, `test_brownfield_raw_unit_ramps_on_own_month_not_plant_mean` and `test_brownfield_bin_availability_is_the_constituent_fraction` FAIL on the old seam and PASS on the new; `test_greenfield_bin_still_ramps_through_constituents` and `test_greenfield_bin_ramps_identically_with_and_without_constituents` pass on both (the [56] → `000000001111` step is produced by the constituent fraction AND by the plant-map fallback). `TestLiveCardS12Cases` pins the three measured cases on the committed vintage.

**(c) One shared seam.** `cod_ramp.generator_online_mask` is the single resolver `generators_to_fleet_arrays` calls for every ISO; no per-ISO number, no per-ISO branch, nothing fitted. The only per-ISO difference is which grain each ISO's fleet path hands it.

## 3. The repair (what changed, what did not)

* `cod_ramp.effective_cod(..., is_plant_level=False)` — a raw EIA-860 unit with a known own year (> the 2000 sentinel) keeps its OWN `(online_year, online_month)`; a plant-level object (`is_campd_bin`) keeps the plant map's; retirement resolution unchanged (own if present, else plant-collapsed).
* `cod_ramp.load_unit_cod_map()` / `_load_unit_cod_map(dir)` — `{(plant_code, fuel_type): ((nameplate, oy, om), …)}` from the SAME two parquets `_load_cod_map` reads, status `OP` only (the loader's own filter), classified with the loader's own `_map_fuel_type`; `bin_online_fraction(units, year)` — the nameplate-weighted online fraction, endpoints exact (a bin whose units all predate the year hands the LP exactly 1.0).
* `cod_ramp.generator_online_mask(...)` — raw unit → own date (0/1); bin with `(plant, BIN_GROUP_TO_FUEL[group])` constituents → fraction × the bin's retirement half; else the plant-collapsed record exactly as before. Reaches the ERCOT curated-sheet bins through the same lookup (their `Plant_Code` + `Plant_Group`).
* `fleet/arrays.py` — the COD block calls the resolver (passes `plant_group`, `is_campd_bin`); `min_gen` scales by the same mask.
* `fleet/eia860.py` — `_operating_month_by_unit(dir)` bridges each unit's `Operating Month` into `_load_fleet_from_parquet` from the same directory's operable sheet (mirror of `_chp_by_plant`); never overrides a month the parquet already carries (the retiree-channel schema has one).
* `fleet/__init__.py` — exports the two new names so `_pkg_ns()` and the tests' patch points resolve.
* `_load_cod_map` is **unchanged** (its output is the fallback and feeds `commission_year_cod_fallback` untouched). Retirement is untouched at both grains (rule 19: the partial-plant exit cohort is the one unit-grain retirement mechanism under binning). Legacy heat-rate bins (`plant_code` 0) never reach the map — unchanged. Forecast mode never enters the block — unchanged.
* Rule 28 `[R-MECH-MATRIX]`: **no `ScenarioConfig` field is added, so no matrix row is added** — this is a correctness repair of an existing default-on mechanism (`cod_ramp_enabled`), stated here explicitly as the charter asks. Rule 26: nothing deprecated is left parseable; the old preference is gone, not flagged.

## 4. Pre-registered screen gates (rule 29 — STRUCTURAL, STOP-only, never a residual)

| gate | what it asks | pass condition | measured where |
|---|---|---|---|
| G-S1 direction & order | the arm's class energy moves the way §1.3's availability delta says | per ISO-year, sign(Δ energy of each moved class) = sign(Δ MW-months of that class) wherever \|Δ MW-months\| > 100, and \|Δ energy\| ≤ Δ GWh-avail (no unit runs above availability) | arm bundle `hourly/class_hourly_<y>.parquet` vs control |
| G-S2 confinement | only §1.3's listed LP units change availability | established at phase 0 on the identical generator list (this doc); the shard re-asserts it by reporting the `COD ramp (<ISO> <year>): N unit-months masked` log line, which must be ≥ the keeper's | shard log |
| G-S3 identity | a moved object dispatches ≤ its new online fraction | for one named object per solved ISO — MISO plant 6137 CT bin in 2020 (≤ 0.27 × its pmax in every hour), SPP 2025's largest moved CT bin, ERCOT plant 65372 in 2022 (zero before November), PJM plant 62949 in Feb 2023 (≤ 0.67 × pmax) — read from `dispatch/<year>_P1.parquet` | parent, after fetch |
| G-S4 no unrelated flip | no load-bearing criterion moves PASS→FAIL in a class the seam does not touch | reported; a flip in a touched class is REPORTED AT FULL MAGNITUDE and is **not** a gate (rule 14: a worse fit after an accurate input is a discovered miscalibration elsewhere, never a reason to keep the estimate) | `metrics.json` |

Nothing above reads a residual. Bands are reported both ways in the FINDING; none of them promotes or kills the arm.

## 5. G-DRIFT — is the committed keeper a valid control? (rule 29(b), form 4)

`git diff <keeper sha> 33a7c961 -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`, every hunk classified. The clone was shallow at session start (2026-09-11 →); history was deepened and the unreachable keeper commits fetched by SHA so the audit could be run at all (that fetch pulled full packs — see §8).

| ISO | keeper sha → base | solve-path commits | classification | form 4 |
|---|---|---:|---|---|
| SPP | `760012f7` → `33a7c961` | 3 | `5e6d3224` MISO 2020/21 LMP validation reference (another ISO's artifact) INERT · `0acedb7e`/`48352ffa` nyiso-231 gas-anchor mirror, gated `gas_offer_margin_anchor_vintage` kwarg-or-field, SPP recipe `False` INERT | **VALID — keeper is the control** |
| NYISO | `0acedb7e` → `33a7c961` | 3 | `5e6d3224` INERT · `48352ffa` is the merge of the keeper's own commit (no content beyond it) INERT · `760012f7` SPP-38 re-keys EIA-860 caches on the active directory; NYISO's vintage is `None` → root dir → identical data INERT | **VALID** (bound-only, §6) |
| MISO | keeper `d0fec486` ≡ main `b3212c7f` in `src/`+`scripts/` (only docs/probes differ) → `33a7c961` | 8 | `b3212c7f` is the keeper's own commit INERT · nyiso-230 ×3 (`gas_offer_margin_zonal_anchor_vintage`, NYISO-only, absent from MISO's recipe) INERT · nyiso-231 INERT · `760012f7` INERT (vintage `None`) · `5e6d3224` INERT for the SOLVE but **LIVE for the 2020/2021 C3 price SCORES** (the keeper's metrics were scored against the previous reference) | **VALID for dispatch / fuel-mix / 2022–25 prices;** 2020–21 price criteria are not differenced against the keeper |
| PJM | `f09eddbe` → `33a7c961` | 16 (+`f46e9e32`, the former shallow graft, not drift) | `3497a1d8`/`b385f3f3`/`706aa547`/`f0316092` `unit_outage_window_hour_grain` tri-state kwarg, PJM recipe absent → `None` INERT · `26f8508b`/`3f78a824` `plant_taxonomy.classify_plant` routes prime mover `PS` to `OTHER` — an EIA-923 **scoring** classifier; the commit's own measurement: solve inputs byte-identical in all 42 scored ISO-years, hydro score population changes → INERT for dispatch, **LIVE for the hydro-class score** · miso-255 ×3 (MISO-only field) INERT · nyiso-230/231 INERT · `760012f7` INERT · `5e6d3224` INERT | **VALID for dispatch / fuel-mix / prices; hydro-class scores excluded** |
| CAISO | `b8ddf8bc` → `33a7c961` | 16 | same set as PJM, same classification | informational (bound-only, §6) |
| ERCOT | `6bc43501` (2026-09-09) → `33a7c961` | **70** | includes ERCOT-lane merges (`a1513509` ercot-uri-february-fuel), the LP memory-hygiene changes (`ee40acd2`, `eaa9d6f1`), the `[R-HOLDOUT]` removal (`b0a807a8`), FR-22 keeper-field declarations (`9be52b9e`), and the whole pjm/miso/nyiso/spp 09-09→09-11 stream | **VOID — not classifiable inside this lane's budget; a LIVE hunk cannot be excluded → a control solve is EARNED** |
| NEISO | basis `cfc66722` **on a dirty tree** (`constants.py` among the changed files) | — | a dirty-tree keeper has no auditable basis by construction | n/a (bound-only, §6) |

## 6. What is solved, what is bounded (rule 29 clause 0: an arm with a computable pre-solve gate does not reach a solve until that gate passes — and an input-inert arm never earns one)

| ISO | §1.3 input delta | decision | control |
|---|---|---|---|
| **MISO** | −5.0 to −6.0 TWh-avail every year (0.3–0.4 % of fleet availability), +0.44 in 2020 | **SOLVE the full 2020–2025 span** (one shard, two recipe groups chained) | keeper bundle `miso255_sil_keeper` (form 4) |
| **SPP** | −2.03 TWh-avail in 2025 (0.4 %); 2023/24 two oil units | **SOLVE 2023–2025** (one shard) | keeper `spp38_span` (form 4) |
| **ERCOT** | −1.02 / −0.84 / −0.24 / −0.84 and +0.09 / +0.53 / +0.33 TWh-avail 2021–24; 0 in 2025 | **SOLVE 2021–2025** (one shard, three recipe groups chained) **+ a control shard at `33a7c961`** (form 4 void) | its own control solve |
| **PJM** | +0.36 TWh-avail 2023 (one 1.4 GW CC two months earlier); −0.02/−0.01 | **SOLVE 2023–2025** (one shard) | keeper `pjm_d4_4_A` (form 4, hydro score excluded) |
| NYISO | 2 units, 37.8 MW-months/yr (≤ 0.028 TWh at 100 % CF) | **BOUND, no LP**: every scored band moves by < 0.03 TWh | — |
| CAISO | 7–8 objects, ≤ 50 MW-months/yr (≤ 0.037 TWh at 100 % CF, 0.02 % of load) | **BOUND, no LP** | — |
| NEISO | 2 objects in 2023 only, 3.7 MW-months (≤ 0.003 TWh); 2024/25 byte-identical inputs | **BOUND, no LP** | — |
| SOCO | 27,897.8 / 3,392.1 / 22.8 MW-months (no runnable SOCO config exists yet — that is SOCO-20) | **BOUND at measured CF** (SOCO-10: +12.979 TWh nuclear 2023, +2.167 TWh 2024, 2.3–4.6 TWh Barry A3) | — |

Arms are the keeper's frozen recipe replayed at the arm SHA (`scripts/replay_keeper.py <keeper> --out-dir results/calibration/soco15_<iso>_arm`), so every arm is promotable as that ISO's keeper if the owner so rules (rule 34: every shard pushes its full bundle, `dispatch/<year>_P1.parquet` included, on its own branch). The ERCOT arm and control need `ercot_ep_gas_basis_receipts_fallback` carried through `--set` (the keeper's own flag, which `replay_keeper.build_kwargs` cannot route today — the ERCOT lane's replay defect, reported, not repaired here) with the key ignored through a probe-side wrapper, never an edit under `scripts/`.

## 7. Shards (rule 32 / 33 / 34) — the parent never solves

Five shards, each ONE registrable run in ONE `--years <all>` invocation chain into ONE bundle, its own `--out-dir`, its own branch `claude/soco-15-<iso>-<arm|control>`, `source_revision` = the full arm SHA (control: `33a7c9615f0dbc9aa19e58a976de29df462059d6`), `DATA PROFILE: <iso>`, hard stops (pinned SHA; `tests/unit/data/test_cod_ramp.py` green; the seam present — `grep -c generator_online_mask src/market_sim/data/fleet/arrays.py` ≥ 1 on an arm, = 0 on the control; the keeper's config signature in `meta.json`; free disk ≥ 20 GiB before a per-plant MISO/PJM solve), the runner unmodified with no `--no-container-preflight`, budgets stated (MISO 150 min, PJM 90, ERCOT 75 each, SPP 25 — the 20-minute rule is a STOP rule: a shard approaching its budget with no artifact stops and reports), the bundle pushed with a `.gitignore` negation and a plain `git add`, and the report in numbers: `container preflight:` / `memory peak:` lines, the `COD ramp (<ISO> <year>): N unit-months masked` line per year, per-year class TWh from `hourly/class_hourly_<y>.parquet` (`mw` summed per `klass` for pass `P1` / 1e6), `metrics.json` determination and per-criterion status, the pushed commit SHA and `git ls-tree -r <sha> -- <bundle> | wc -l`. Forbidden by name: `git add -A` / `git add .`, `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, anything under `frontend/data/backcast/**`, any edit under `src/` or `scripts/`, opening a PR, deleting any result. Each shard is archived the moment its bundle is fetched, checked out and verified (rule 33); shard branches carrying a promotable bundle stay until the owner rules (rule 33(f)(3)).

**Addendum (after push): the arm SHA is `4f33476c520dbbec61f05abcfdbeb1a4b18540a4`** (commit 2 of this branch: code `9398000d` + this PRECOMMIT). Shards launched 2026-09-13 17:41–17:43 UTC, `source_revision` pinned to that SHA (the ERCOT control to `33a7c9615f0dbc9aa19e58a976de29df462059d6`):

| shard | session | branch it pushes | budget |
|---|---|---|---|
| MISO arm (6 yr, two recipe groups chained) | `session_01HmkDSXoXaGfmhGce4iqxTa` | `claude/soco-15-miso-arm` | 150 min |
| PJM arm (3 yr) | `session_01BM46YfHbT9zU28Lj45qvHm` | `claude/soco-15-pjm-arm` | 90 min |
| ERCOT arm (5 yr, three recipe groups chained) | `session_01UqvwgkpPi4HWXXdT9oXTNc` | `claude/soco-15-ercot-arm` | 75 min |
| ERCOT control (5 yr, same chain, unrepaired seam) | `session_01YbL3rhiy3njjfmcDpmShMZ` | `claude/soco-15-ercot-control` | 75 min |
| SPP arm (3 yr) | `session_01Qcn9tXLjgMAEVagdDamuyf` | `claude/soco-15-spp-arm` | 25 min |


## 8. Two things this session did that a later reader should know

1. The deep fetch that made §5 possible pulled ~15 GB of full packs into a blobless clone (the trap `docs/fast-clone.md` names); the repo was repacked with `--filter=blob:none` after a promisor remote was configured. No result was deleted (rule 31); the tool caches were.
2. Three lanes' plumbing gaps surfaced and are routed, not repaired here: `replay_keeper.build_kwargs` cannot route the ERCOT keeper's own `ercot_ep_gas_basis_receipts_fallback`; the NYISO fingerprint pin is stale on `main`; `tests/unit/data/test_caiso_st_gas_peak_measured.py::test_registry_value_matches_the_committed_artifact` fails on `main` (1.154 vs 1.166), also with this lane stashed.

## 9. Promotion (rule 31) — asked now, not at the end

Every solved arm is the ISO's keeper recipe on the repaired seam. Whether any of them becomes that ISO's keeper is the owner's call and each ISO lane's to execute (rule 35, per-ISO); this lane registers nothing, prunes nothing, and touches no keeper shard, log or matrix shard. The bundles live on the shard branches by full SHA (FINDING §retrievability) and are not deleted by this lane.
