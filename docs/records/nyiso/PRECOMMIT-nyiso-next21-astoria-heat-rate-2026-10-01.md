# PRECOMMIT — NYISO-NEXT-21: Astoria's measured heat rate on the merged stack-duplicate meter — 2026-10-01

Phase 0: `docs/records/nyiso/FINDING-nyiso-next21-d4-rows-and-astoria-heat-rate-2026-10-01.md`. Fixed before any solve.

**The arm.** The keeper's recipe, byte for byte (`replay_keeper.py`, **no `--set`**), on the re-derived `campd_st_heat_rates_NYISO.csv` (sha256 `4bfe374744884196bc63912d847354ccb71090c590720f9c644163945aeda538`). Zero `ScenarioConfig` changes, zero free parameters, zero new mechanisms. The only input that moves is Astoria 8906's ST_GAS heat rate: 9.449 → 11.18–12.07 (per year), the merged CEMS meter (rule 14; rule 23 trigger = the stack-duplicate identity defect).

**Pin.** The `main` commit that carries this PRECOMMIT and the artifact (recorded in every shard prompt and in the RESULT).

## 1. G-DRIFT (keeper `git_sha` 6e0bd8b5 → pin)

Every commit touching the backcast solve path since the keeper:

| commit | change | class |
|---|---|---|
| `0b4d3b3f`, `54edd9e3` NWPP-NEXT-14 | `eia923_cc_family_heat_rates` (replaces `cc_subfloor_eia923_heat_rates`) + tranche composition | INERT: default off; the keeper carried the old flag `false` |
| `bf7c1228` R-ERCOT-20 | GT split at ERCOT plants 3469 / 7900 / 56350 (`eia860.py`, `outages.py`, reference CSVs) | INERT: ERCOT plant codes only |
| `3a7d8006`, `71c1dfbf`, `32e0c185`, `444cbdd4` PJM-NEXT-16 | PJM gas bridge, OVEC join | INERT: gated `iso == "PJM"` / default off |
| `91a525f3` soco-96 | `dual_fuel_measured_oil_burn` | INERT: default off; `skip_cells=None` path unchanged |
| `c361efe0`, `10b20574` NWPP-NEXT-15 | `coal_captive_marginal_fuel_price`, `unit_outage_dispatched_bin_live_denominator` | INERT: default off, absent from the recipe |
| `450c1b33` miso-294 | `actual_lmp.json` | INERT: only the `MISO` key changes |

All INERT. Form 4 holds: the keeper's committed bundles are the control. The arm's single LIVE input is the artifact; its footprint is measured zero-LP in all five years (FINDING §3): **4 rows per year, all Astoria ST_GAS, pmax and availability byte-identical** (`results/phase0/nyiso/_nyisonext21_g1_offer_delta.json`).

## 2. Legs (rule 36: one year-isolated shard per year, all five registered years)

At the pin:

- 2022–2025: `python3 scripts/replay_keeper.py results/calibration/nyisonext18_span --years <y> --out-dir results/calibration/nyisonext21_<y>`
- 2021: the same from `results/calibration/nyisonext18_2021`.

## 3. Gates (arm vs the keeper's committed bundles)

- **G-1 leg acceptance (shard hard stop + parent check).** `git rev-parse HEAD` = pin. The artifact's sha256 = `4bfe3747…`. The leg's `scenario_config` equals the keeper's except keys born since the keeper, at their dataclass default.
- **G-2 the repair is live.** Astoria 8906 ST_GAS P1 energy is **lower** than the keeper's in every year. (Its offer rose 12–22 % and nothing else moved; a rise would mean the LP is not responding to the input.)
- **G-3 conservation.** Per year and zone, P1 demand equals the keeper's within 0.1 GWh; P1 load-slack exceeds the keeper's by ≤ 1 GWh.
- **G-4 protective.** C6 and C8 PASS, every year.
- **G-5 conduct.** No D-4 FAIL row keyed (year, mechanism, plant) in the arm's composed `legitimacy_diagnostics.json` that is absent from the keeper's.

## 4. Promotion rule

**Promote iff G-1 to G-5 hold in all five years.** Structural (rule 1, rule 14): it replaces a selection-biased measurement with the plant's own merged meter, which eGRID corroborates (11.75). If any gate fails, the run is registered (rule 15), not promoted, and the owner is asked.

**Reported, not gating, in either direction:** C1, C2, C3a, C3b, C3c and the determination per year; Astoria, Ravenswood, Arthur Kill and NYC-steam totals vs CAMPD; D-4 rows cleared; zone load-weighted prices. A determination downgrade in any year is put to the owner before any promotion.

## 5. Prediction (recorded, not a gate)

- Astoria energy falls in every year, most in 2022–2023 (largest offer gap to Ravenswood / Arthur Kill).
- Part of it moves to Ravenswood and Arthur Kill (NYC, $34–36), part to imports and CCs; **the NYC steam total falls less than Astoria does.**
- The Astoria bridge D-4 rows (2021, 2024) should shrink or clear; the Danskammer / Saranac / Athens / Roseton rows should not move.
- Prices: NYC up by cents to low single dollars in hours Astoria was marginal; every criterion moves ≤ 0.5 pt.
