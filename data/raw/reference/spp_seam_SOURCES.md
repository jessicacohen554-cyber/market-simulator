# `spp_seam_*.csv` — SOURCES

Lane **SPP-33** (`docs/handoffs/FINDING-spp-33-2026-09-07.md`), plan
`docs/multi-iso/spp-addition-plan-2026-09.md` §5 row SPP-33. **Derive only —
these files arm nothing.** The three `INTERFACE_NEIGHBORS["SPP"]` blocks stay
default-off and their `hr_by_year` stays `None` in
`src/market_sim/model/interchange/spec.py` until lane **SPP-51** acts on these
numbers. SPP-33 does not edit `spec.py`, MISO's SPP seam, or `ScenarioConfig`.

| File | What it is |
|---|---|
| `spp_seam_hr_by_year.csv` | Per (neighbour, year, run ∈ {rt, da}): the measured-anchored `hr_by_year` for `INTERFACE_NEIGHBORS["SPP"]`, with **every operand** of the formula (anchor mean, Henry Hub, gas basis, delivered gas, shape convexity `K`), plus what the registered flat `marginal_heat_rate` constructs and its error against the measured mean |
| `spp_seam_hr_elasticity.csv` | The forward gas-elastic `(hr_phys, hr_adder)` fit per neighbour + the flat / elastic / measured forward-skill table, with `fit_r2` and `hr_phys_sign_ok` reported so a degenerate 3-point fit cannot be read as an identified elasticity |
| `spp_seam_diba_duration.csv` | EIA-930 SWPP net-interchange **duration-curve summary**, per DIBA per year (11 percentiles, export/import hour split, net/export/import TWh), 2023–2025 |
| `spp_seam_limit_binding.csv` | Each registered `interface_limit_mw` against the measured DIBA series — how many hours the limit would bind, and the headroom ratio |
| `spp_seam_tieflow_crosscheck.csv` | SPP's OWN 1-minute tie flows (`../spp-planning/TieFlows_Sep2025.csv`, SPP-14) against the EIA-930 DIBA series over their 673-hour overlap — the **sign/magnitude sanity check only**; no parameter is derived from it |

## Sign convention (carried on every `spp_seam_diba_duration.csv` row)

EIA-930 BA-to-BA net interchange: **`mw > 0` = SWPP EXPORTS to the DIBA;
`mw < 0` = SWPP IMPORTS from it.** Confirmed against SPP's own meter —
correlation +0.9936…+1.0000 and mean differences ≤ 10.3 MW on all five
compared seams, signs agreeing on every one (`spp_seam_tieflow_crosscheck.csv`).

## Inputs (all committed; nothing fetched)

| Input | Used for |
|---|---|
| `../_validation-source/actual_lmp_hourly_zonal_MISO.parquet`, rows `zone ∈ {MISO-West, MISO-South}` | the **MISO** seam anchor, as SPP-20 registered it |
| `../_validation-source/actual_lmp_hourly_SPP.parquet` | the **AECI** anchor — a declared PROXY (AECI publishes no LMP) |
| `../_validation-source/actual_lmp_hourly_ERCOT.parquet` | the **ERCOT** seam anchor |
| `../eia-930-interchange/SWPP interchange hourly.parquet` (SPP-11; widened 2019–2025 by SPP-15) | the DIBA duration curves and the limit-binding table |
| `../eia-930-hourly/SWPP hourly.parquet` + the neighbour BA extracts | `neighbor_load_shape` (all three seams are `load_shape_exponent=1.0`, so `K = 1.0` exactly) |
| `../spp-planning/TieFlows_Sep2025.csv` (SPP-14) | the sanity check only |
| `constants.HENRY_HUB_TRAJECTORIES["mid"]`, `constants.GAS_BASIS_DIFFERENTIAL` | the delivered-gas operand, via `data.neighbor_price.neighbor_gas_price` |

Three impossible prints inside 2023–2025, documented in
`../eia-930-interchange/README.md`, are **excluded and counted** (never
silently dropped) in `spp_seam_diba_duration.csv`
(`hours_excluded_impossible`): `SPC` 2024-07-19 00:00 (+9,967 MW) and
2025-11-19 15:00 (−57,499 MW); `WACM` 2025-06-21 05:00 (+32,974 MW). **None
is on a registered seam**, so the MISO / AECI / ERCO rows are untouched by the
exclusion. The `MISO` −5,377 MW print at 2024-01-14 08:00 is Winter Storm
Heather and is **retained** — the seam really did carry it.

## Formulae — the committed producers', unchanged

* `hr_by_year` — `scripts/data/derive_neighbor_hr_by_year.py::derive`:
  `HR[y] = mean_anchor_LMP[y] / (neighbor_gas_price(nb, y) × K[y])`, with
  `K[y] = mean(neighbor_load_shape(nb, y, 8760)[0])`.
* elasticity — `scripts/data/derive_neighbor_hr_elasticity.py::derive`: OLS of
  `mean_anchor_LMP[y] / K[y]` on `neighbor_gas_price(nb, y)`.

## Regeneration — and why the committed producer does not do it

**The producers cannot reach these anchors at HEAD.** Both resolve the anchor
through `_NEIGHBOR_LMP_ISO`, which maps neighbour `"MISO"` to the MISO
**system** file (`actual_lmp_hourly_MISO.parquet`) rather than the zonal anchor
SPP-20 registered, and carries no `"AECI"` / `"ERCOT"` key at all — so
`--iso SPP` silently emits **one** row, for the wrong MISO anchor, and drops
the other two seams entirely. This is the defect SPP-20 R-7 flagged. Repairing
it is a change to a producer SPP-33 does not own, so it is **ROUTED to
SPP-DESK, not made** (FINDING-spp-33 §2 and §6 item R1).

Until that lands, these files regenerate from the **complete producer listing
in `docs/handoffs/FINDING-spp-33-2026-09-07.md` §A**, which substitutes only
the anchor resolver and is otherwise the two producers' own arithmetic.
