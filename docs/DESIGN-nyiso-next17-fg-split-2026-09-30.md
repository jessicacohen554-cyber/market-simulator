# DESIGN — NYISO-NEXT-17: the F/G re-partition (`nyiso_fg_split`) — 2026-09-30

- **Session:** NYISO-NEXT-17 (orchestrator; zero LP in this container).
- **Owner decision card (this session):** "Build design A anyway".
- **Probe:** `scripts/probes/nyisonext17_phase0.py` (zone × month and CENTRAL EAST regime decomposition of the keeper's committed bundles).

## 1. What 2021 C3a is (phase 0, zero LP)

Keeper `2026-09-30-nyisonext16-winter-spread-span` plus the stamped 2021 run. Load-weighted $/MWh.

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| model LW | 43.61 | 83.23 | 34.01 | 37.70 | 60.73 |
| RT LW (C3a actual) | 39.26 | 81.12 | 32.25 | 38.12 | 66.43 |
| Upstate_West contribution vs measured DA | **+3.94** | +6.66 | +1.77 | +0.21 | −0.68 |
| … of which in CE ≥ 0.85 hours | **+3.45** | +4.94 | +1.41 | −0.01 | +0.16 |
| CE ≥ 0.85 of posted limit, % of hours | 72.6 | 59.0 | 41.1 | 11.5 | 14.3 |
| CE ≥ 0.85 hours: Capital − Upstate spread, measured / model | 19.5 / 2.2 | 49.6 / 5.0 | 18.5 / 1.8 | 23.4 / 3.9 | 39.1 / 6.4 |

- 2021's +4.35 $/MWh over RT is about 80 % Upstate_West in hours the market's CENTRAL EAST (E → F) was loaded.
- The model moves the right volume east. Its link averages 3,618 MW against 3,677 MW of measured TOTAL EAST. But the link binds in only 17.6 % of hours, so Upstate_West couples to Capital.
- When CE binds, the measured price structure is F > G ≈ H. Zone G (HUD VL) sits 4–15 $/MWh **below** F. The step is at E → F, not at the F+G boundary.

## 2. Designs considered (zero-LP pre-checks)

| Design | Pre-check | Result |
|---|---|---|
| A. Split F from G; G joins Lower_Hudson; CE on UW→F, non-CE TOTAL EAST on UW→G–I | The transport cut is CE posted + non-CE p90: 4,407 MW mean in 2021, against today's 4,378 MW | **Not tighter.** Built on owner instruction. |
| B. A plus a regression shift-factor flowgate | CE ~ TE + F/G net injections: R² 0.76 → 0.81, RMSE ~220 MW (≈10 % of the limit) | Fails ex ante. |
| C. One link, cap = CE posted + mean non-CE flow in CE-binding hours | At cap in 56 % of CE-binding hours vs 1.2 % of slack hours. Measured TE exceeds the cap in 28 % of 2021–22 hours. | Not chosen. |

**Stated before any solve:** under A the Upstate cut is about as loose as today, so a large 2021 C3a move is **not** expected. What A changes is where power lands (CE into F, the rest into G–I) and the zone membership the prices score against. Capital_Hudson is already scored against CAPITL alone, and Lower_Hudson against HUD VL + MILLWD + DUNWOD (`derive_actual_lmp.py`). So today's model carries G's load and plants in a zone scored as F only, and the split removes that mismatch.

## 3. Construction (`ScenarioConfig.nyiso_fg_split`, default off; requires `nyiso_total_east_cutset_ttc`)

Armed per solve through `config.topology_variant.set_nyiso_fg_split` at the `run_calibration.run_year` and `run_calibration_full.solve_and_persist` seams. The forecast orchestrator clears it, and `run_year` refuses it in forecast mode.

| Object | Base | Armed | Source |
|---|---|---|---|
| County → zone | G counties → Capital_Hudson | G → Lower_Hudson; lat fallback boundary 41.4 → 42.05 N | `zone_assignment.NYISO_HUDSON_VALLEY_COUNTIES` (129 plants move, incl. Roseton, Danskammer, Bowline, CPV Valley, Cricket Valley) |
| Hourly zone load | A–K groups, G → CH | G → LH; parsed from the raw A–K file | `eia930.zonal_shares.nyiso_load_zone_groups` |
| SCR/EDRP | G → CH | G → LH | `nyiso_demand_response.nyiso_zone_to_model` |
| Market solar | artifact by model zone | `nyiso-market-solar-capacity-fgsplit.csv` (same registry; no G market PV in 2022–25, so the values are identical) | `derive_nyiso_market_solar.py --fg-split` |
| PAR landings | Ramapo, South Mahwah → CH | → LH (both ZONE G by NYISO's own citation) | `nyiso_par_attribution.interface_zone` |
| Border links | CH 1,600 | CH 600 (NE AC) + LH 1,000 (Ramapo); same total | `interchange.spec.NYISO_IMPORT_NODE_LINKS_FG_SPLIT` |
| Unattributed pooled link | n/a (every link attributed) | capped at 0 both ways (CH once the NE row rides its own node) | `nyiso_par_attributed_ttc_hourly` |
| Floor limbs | CH ST_GAS | → LH (F has 0 MW gas steam; zone p95 tmax 31.1 C on both series) | `iso_configs.remap_nyiso_fg_split_floor_specs` |
| UW → CH | TOTAL EAST p90 envelope | posted CENT EAST DAM TTC (`NYISO_INTERFACE_TTC_BY_MONTH`) | `pipeline.ttc.apply_iso_monthly_ttc` |
| UW → LH (new) | — | p90 of measured TE − CE per month (`NYISO_TE_NONCE_ENVELOPE_BY_MONTH`) | `derive_nyiso_te_nonce_envelope.py` |
| CH → LH | UPNY-SENY 5,150 static | same (now the F → G boundary; it does not bind) | — |

- **Zero free parameters.** Every value is a posted limit, a measured p90 (inherited construction) or a published zone letter.
- **Declared misalignments (rule 14):**
  - The non-CE TOTAL EAST paths are assigned to G on the interface definitions; the posting does not attribute them to a zone.
  - The NE AC tie (New Scotland F / Pleasant Valley G) stays on Capital_Hudson, with the landing `nyiso_ne_ac_node` uses.
  - G takes Lower_Hudson's weather station (White Plains).
- **Unaffected by construction:**
  - Gas basis: Capital_Hudson and Lower_Hudson are both on Iroquois Z2 at 3.9046.
  - Reserves: SENY = Lower_Hudson + NYC + Long_Island now equals NYISO's G–K.
  - The loss surface is per zone pair.

## 4. Zero-LP pre-flight (fleet-only rebuild of the keeper recipe, 2023)

`scripts/probes/nyisonext17_fleet_check.py 2023` rebuilds through the sanctioned `replay_keeper.run_year_kwargs` path twice (control, arm). No LP.

| zone | demand GWh, control → arm | thermal MW, control → arm |
|---|---|---|
| Upstate_West | 51,174.4 → 51,174.4 | 11,917.9 → 11,917.9 |
| Capital_Hudson | 20,108.8 → 11,094.1 | 8,584.3 → 3,705.5 |
| Lower_Hudson | 8,097.3 → 17,112.0 | 99.8 → 4,978.6 |
| NYC / Long_Island | unchanged | unchanged |
| **NYCA total** | **147,048.9 → 147,048.9** | **42,955.0 → 42,955.0** |

- The totals are conserved exactly; 9,014.7 GWh of load and 4,878.8 MW of thermal move from F+G to G+H+I.
- Links (armed): the base four, plus `Upstate_West>Lower_Hudson`. The border links go from CH 1,600 to CH 600 + LH 1,000.

## 5. Tests

`tests/iso/nyiso/test_nyiso_fg_split.py` covers:

- the default being byte-identical;
- the requirement on the cutset flag;
- the cache key;
- the topology;
- every membership map;
- border-capability conservation;
- the floor remap;
- the two upstate legs replacing the envelope.

The whole NYISO suite also passes.
