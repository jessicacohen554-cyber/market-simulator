# Capacity hindcast — ERCOT 2021→2025 (realized fuel)

_Generated 2026-08-24 · W2-P5 · plan §1.4 · bundle `results/hindcast/ercot-2021-2025-realized-t1h-disarm/ERCOT/2eab21467a4214c7`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 2.294 | 0.0 | -100% | ❌ FAIL |
| unit recall >300MW | 0 units | 0 matched | n/a | — |
| false-retire (GW) | — | 0.0 | 0% of model | ✅ PASS |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **—** (0/0). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **0 of 2** target rows >=300 MW — recall **n/a** (never 0/N): no target exit >= 300 MW is reachable by an admissible channel on this run's fleet basis — reported n/a, never 0/N (D-24).

**Unreachable exits — NON-GATED diagnostic** (5 rows, 2 of them >=300 MW and therefore out of the denominator). Nothing here bands:

| unit | MW | fuel | exit | driver | why unreachable | gated |
|---|--:|---|--:|---|---|:--|
| `56611_S01` Sandy Creek 1 | 1008.0 | coal | 2025 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 73.41 vs bar 58.5 $/kW-yr in 2024 (unit_net), bar-invariant), and no confirmed-registry instrument exists | yes |
| `3548_2` Decker Creek 2 | 405.0 | gas_st | 2022 | not margin-driven (exit decode); no confirmed-registry instrument exists | not_in_fleet_basis — ABSENT (3548 carries only CT8, CT_PEAKER 206.0 MW) — no screen can retire capacity the run's fleet never carried | yes |
| `3612_2` V H Braunig 2 | 252.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-2 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 63.35 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-2, 2024-03-13) post-dates the vintage cutoff 2020-12-31 | no (below size threshold) |
| `3612_1` V H Braunig 1 | 225.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-1 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 69.74 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-1, 2024-03-13) post-dates the vintage cutoff 2020-12-31 | no (below size threshold) |
| `52120_G-66` Freeport Energy G-66 | 119.0 | gas_cc | 2023 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 176.44 vs bar 30.0 $/kW-yr in 2022 (class_proxy), bar-invariant), and no confirmed-registry instrument exists | no (below size threshold) |

_Evidence, per unit: FFR-7C §2.2 (per-unit margin table) / §2.4 (fleet-basis facts) — docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md; `data/raw/confirmed-retirements/ercot.csv`. Excludes only on positive, cited evidence; a unit with no evidence either way stays in the member set._

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.019 | 0.0 | -100% |
| coal | 1.008 | 0.0 | -100% |
| gas_cc | 0.271 | 0.0 | -100% |
| gas_ct | 0.102 | 0.0 | -100% |
| gas_st | 0.888 | 0.0 | -100% |
| oil | 0.005 | 0.0 | -100% |

## Additions (cumulative 2021→2025) — **decision basis**

_Attribution basis: **decision** (owner decision D-9(ii), signed 2026-08-04 (sitting Addendum K.2)). Scored on the DECISION basis (D-9(ii)). Additions verdicts on this basis are NOT comparable to any additions verdict committed before 2026-08-04, which were scored on the COD basis — the metric means something different. Retirements-side comparability is unaffected. See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md._

Basis effect — decided in-window with COD **after** the window (invisible under the COD basis): `{'solar': 8.0, 'gas_cc': 3.0, 'gas_ct': 1.0}`; commissioned in-window from a **pre-window** decision (dropped under the decision basis): `none` (GW).

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 12.663 | 1.442 | -89% | ❌ FAIL | -20.2 |
| solar | 25.08 | 19.987 | -20% | ❌ FAIL | -8.2 |
| gas_cc | 0.244 | 9.0 | +3588% | ❌ FAIL | +16.2 |
| gas_ct | 3.692 | 5.571 | +51% | ❌ FAIL | +3.7 |
| storage | 13.691 | 18.0 | +32% | ❌ FAIL | +8.6 |

COD-basis comparison (**not** the graded instrument; model total 42.0 GW vs decision-basis 54.0 GW):

| tech | model GW (COD) | model GW (decision) | band (COD) |
|---|--:|--:|:--|
| wind | 1.442 | 1.442 | ❌ FAIL |
| solar | 11.987 | 19.987 | ❌ FAIL |
| gas_cc | 6.0 | 9.0 | ❌ FAIL |
| gas_ct | 4.571 | 5.571 | ❌ FAIL |
| storage | 18.0 | 18.0 | ❌ FAIL |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 167.6 | 191.4 | -12% | (report-only) |
| 2024 | 153.8 | 191.3 | -20% | (report-only) |
| 2025 | 186.4 | 193.6 | -4% | ✅ PASS |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
