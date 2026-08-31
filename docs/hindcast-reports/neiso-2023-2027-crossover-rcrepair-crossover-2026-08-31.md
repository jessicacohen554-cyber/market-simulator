# T1-X crossover — NEISO (neiso-2023-2027-crossover-rcrepair)

_Generated 2026-08-31 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-17-neiso-99-joint-p1`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 9.456 | 0.877 | 10.78 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 8.489 | 0.696 | 12.20 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +13.3% | +3.1% | 4.27 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +5.2% | +5.7% | 0.92 | PASS |
| C3a system load-weighted mean LMP | 2025 | +21.3% | +1.7% | 12.93 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.324 | 0.088 | 3.68 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.388 | 0.159 | 2.44 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.546 | 0.054 | 10.11 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +12.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +11.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +2.7% | — | — | PASS |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 62.248 | 54.214 | +14.8% | +0.6% | 23.90 | yes |
| `gas_twh` | 2024 | 66.342 | 58.595 | +13.2% | +0.3% | 38.88 | yes |
| `gas_twh` | 2025 | 56.327 | 59.535 | +5.4% | +2.4% | 2.25 | NO — reported only |
| `coal_twh` | 2023 | 0.001 | 0.203 | +99.8% | +60.1% | 1.66 | yes |
| `coal_twh` | 2024 | 0.041 | 0.254 | +84.0% | +50.0% | 1.68 | yes |
| `coal_twh` | 2025 | 0.084 | 0.281 | +70.0% | +23.5% | 2.98 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 4.997 | 3.635 | -27% | FAIL |
| unit recall >300MW | 4 units | 2 matched | 50% | FAIL |
| thermal GW retired (vintage-consistent target, exits > 2023) | 2.926 | 3.635 | +24% | FAIL | 
| total additions | — | 4.5 GW | (actual 2.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **4 of 6** target rows >=300 MW.

**Unreachable exits — NON-GATED diagnostic** (5 rows, 2 of them >=300 MW and therefore out of the denominator). Nothing here bands:

| unit | MW | fuel | exit | driver | why unreachable | gated |
|---|--:|---|--:|---|---|:--|
| `1588_7` Mystic 7 | 617.0 | oil | 2021 | not established from committed artifacts | not_in_fleet_basis — ABSENT from every EIA-860 operable vintage >= 2021 (physically ceased 2021; present OP in vintage 2020 only) — no screen can retire capacity the run's fleet never carried | yes |
| `568_3` Bridgeport Harbor 3 | 400.0 | coal | 2021 | not established from committed artifacts | not_in_fleet_basis — ABSENT from every EIA-860 operable vintage >= 2021 (physically ceased 2021; present OP in vintage 2020 only) — no screen can retire capacity the run's fleet never carried | yes |
| `55031_CT03` Androscoggin CT03 | 54.5 | gas_ct | 2023 | not established from committed artifacts | not_in_fleet_basis — ABSENT from the OP-filtered fleet basis of vintages >= 2023 (status OS in the 2023 and 2024 operable sheets; OP through vintage 2022) — no screen can retire capacity the run's fleet never carried | no (below size threshold) |
| `55031_CT02` Androscoggin CT02 | 54.5 | gas_ct | 2023 | not established from committed artifacts | not_in_fleet_basis — ABSENT from the OP-filtered fleet basis of vintages >= 2023 (status OS in the 2023 and 2024 operable sheets; OP through vintage 2022) — no screen can retire capacity the run's fleet never carried | no (below size threshold) |
| `55031_CT01` Androscoggin CT01 | 54.5 | gas_ct | 2023 | not established from committed artifacts | not_in_fleet_basis — ABSENT from the OP-filtered fleet basis of vintages >= 2023 (status OS in the 2023 and 2024 operable sheets; OP through vintage 2022) — no screen can retire capacity the run's fleet never carried | no (below size threshold) |

_Evidence, per unit: NEISO-RC-R R3(i) per-vintage fleet-basis measurement — docs/handoffs/neiso-rc-r/exit-decode-2026-08-31.json (method header), executing FINDING-capx-neiso-rc-phase0-2026-08-30.md §6; `data/raw/confirmed-retirements/neiso.csv`. Excludes only on positive, cited evidence; a unit with no evidence either way stays in the member set._

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 23.2527 | 106.071 | True | True |
| 2027 | 22.7314 | 105.479 | True | True |
