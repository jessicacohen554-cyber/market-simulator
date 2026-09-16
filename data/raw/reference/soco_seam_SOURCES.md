# `soco_seam_*.csv` — SOURCES

Lane **SOCO-33** (`docs/handoffs/FINDING-soco-33-2026-09-16.md`), plan
`docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-33, owner card S4.
**Derive only — these files arm nothing.** The eight
`INTERFACE_NEIGHBORS["SOCO"]` blocks stay default-off and their
`hr_by_year` / `marginal_heat_rate` stay exactly as SOCO-20 registered them in
`src/market_sim/model/interchange/spec.py` until lane **SOCO-56** acts on these
numbers. SOCO-33 does not edit `spec.py`, any neighbour's side of any seam
(rule 25 — TVA's, MISO-South's and the Southeastern utilities' objects are
theirs), `ScenarioConfig`, or either committed producer script.

**Card S4 as ruled**: the first keeper's seam representation is the **served,
measured EIA-930 `Total interchange`** schedule, which SOCO-20 already wired
(`eia930.envelopes.soco_net_interchange` in `_SCALAR_INTERCHANGE_ISOS`).
`soco_seam_served_schedule.csv` is that served array's verification; the other
four files are the **priced-seam** inputs a later lane would need, derived now
and armed later.

| File | What it is |
|---|---|
| `soco_seam_served_schedule.csv` | The **card S4 keeper input**: `soco_net_interchange(year)` on the model's 8760 clock against the sum of the nine DIBA legs on the local clock — net / export / import TWh, export-hour share and the MW envelope. **The lane's first sanity check: SOCO must come out a net EXPORTER in every year, and it does** (+10.156 / +10.807 / +13.032 TWh served) |
| `soco_seam_hr_by_year.csv` | Per (neighbour, year, run ∈ {rt, da}): the measured-anchored `hr_by_year` candidate with **every operand** (anchor mean, Henry Hub, gas basis, delivered gas, shape convexity `K`), plus what the registered flat `marginal_heat_rate` constructs and its error. `anchor_status` is `DERIVED` for the one anchorable seam and `NO_ANCHOR …` for the seven that are not — **reported, never silently skipped** (the SPP-51 discipline) |
| `soco_seam_hr_elasticity.csv` | The forward gas-elastic `(hr_phys, hr_adder)` fit + the flat / elastic / measured forward-skill table, with `n_points`, `fit_r2` and `hr_phys_sign_ok` reported so a **3-point, 2-parameter** fit cannot be read as an identified elasticity |
| `soco_seam_diba_duration.csv` | EIA-930 SOCO net-interchange **duration-curve summary**, per DIBA per year (11 percentiles, export/import hour split, net/export/import TWh, NaN and impossible-print counts), 2023–2025, all nine DIBAs including the unregistered `SEPA` |
| `soco_seam_limit_binding.csv` | Each registered `interface_limit_mw` against the measured DIBA series — hours over the limit, headroom ratio, and **the energy arming at that limit would refuse** (`energy_clipped_by_limit_twh`). This is the quantification of the rule-14 misalignment `spec.py` states qualitatively for all eight blocks |

## Sign convention (carried on every duration and served row)

EIA-930 BA-to-BA net interchange: **`mw > 0` = SOCO EXPORTS to the DIBA;
`mw < 0` = SOCO IMPORTS from it.** The served scalar column uses the same
convention (`mw > 0` = SOCO net export).

**Stated explicitly because SOCO's footprint spans two timezones (gate G19),
and verified rather than asserted.** The interchange product's `local_time`
and the `SOCO hourly.parquet` `Local time` are both **`America/Chicago`**, the
key SOCO-10 established and SOCO-20 registered — confirmed here by a shift
test on the 26,294 joined hours: the sum of the nine legs equals the BA book's
`Total interchange` **exactly in 24,100 hours (91.7 %, r = +0.9985) at zero
shift**, collapsing to 54 / 52 hours (0.2 %, r = +0.955) at ∓1 h. Mean of both
series is **+1,293 MW — positive, i.e. net export**, which is the sign check.
The served array itself is built from the extract's `UTC time` onto the
model's non-leap 8760 clock (`_eia930_net_interchange`), so the two clocks in
`soco_seam_served_schedule.csv` are named per row and their residual is
explained, not padded: 2024 differs by 0.0248 TWh, of which **0.0242 is the
dropped leap day** (2024-02-29, 24 h, 24.18 GWh — the model clock is 8,760 h,
the leg file 8,784) and 0.0007 the UTC→local re-binning; 2023 differs by
0.0012 and 2025 by 0.0064 TWh.

## The anchor resolver — and gate G17

**SOCO itself has no price series and this lane never asks for one.**
SOCO-13's verdict was NO, so no `actual_lmp_hourly_SOCO.parquet` exists; no
neighbouring hub, adjusted MISO-South series or cost-stack construction stands
in for one anywhere in these files, and none of them scores a SOCO run. Every
anchor below is the **neighbour's own realized price on the neighbour's own
side of the seam**, which is what a `NeighborInterface` prices.

| Registered seam | Anchor | Status |
|---|---|---|
| `SOCO_MISO` | `../_validation-source/actual_lmp_hourly_zonal_MISO.parquet`, rows `zone == "MISO-South"` — the anchor SOCO-20's `spec.py` block documents | **DERIVED** |
| `SOCO_TVA`, `SOCO_DUK`, `SOCO_SCEG`, `SOCO_SC`, `SOCO_FPL`, `SOCO_FPC`, `SOCO_TAL` | none — every one is a vertically-integrated, non-market BA that publishes no LMP | **NO_ANCHOR**, reported per row |

No proxy is substituted for the seven. PJM's flat 11.6 and its `(5.6, 14.2)`
affine Southeast fit are **PJM's** (rule 25) and are neither re-keyed nor
re-derived here; `spec.py` carries the 11.6 as a labelled default-off
placeholder and `soco_seam_hr_by_year.csv` reports only what that placeholder
would *construct* as a price level, with no error column, because there is
nothing measured to compare it to.

## Inputs (all committed; nothing fetched)

| Input | Used for |
|---|---|
| `../_validation-source/actual_lmp_hourly_zonal_MISO.parquet`, rows `zone == MISO-South` | the **`SOCO_MISO`** anchor, as SOCO-20 registered it |
| `../eia-930-interchange/SOCO interchange hourly.parquet` (SOCO-11) | the DIBA duration curves, the limit-binding table, the sum-of-legs leg of the served check |
| `../eia-930-hourly/SOCO hourly.parquet` (`Total interchange`) | `soco_net_interchange` — the served schedule; also the `SOCO` load shape (the registered `proxy_ba` for TVA / DUK / SCEG / SC) |
| `../eia-930-hourly/MISO hourly.parquet`, `FLA hourly.parquet` | `neighbor_load_shape` for the MISO and Florida seams |
| `constants.HENRY_HUB_TRAJECTORIES["mid"]`, `constants.GAS_BASIS_DIFFERENTIAL` | the delivered-gas operand, via `data.neighbor_price.neighbor_gas_price` |

**Zero NaN hours and zero impossible prints** on any of the nine DIBAs in any
year, so **nothing is excluded** — the screen (`|mw| > 20,000`, the class of
print SPP's book carries at +9,967 / −57,499 / +32,974 MW) is run and its
count reported (`hours_excluded_impossible = 0` on every row) rather than
assumed away. The verdict is insensitive to the threshold: the largest `|mw|`
anywhere in the SOCO book is **3,150 MW**, so any bound above ~3,200 excludes
the same zero rows. The hour counts are the true grain: 8,759 / 8,784 / 8,760, the
2023 shortfall being the DST spring-forward 02:00 local. This reproduces
SOCO-11 §4.2/§4.3 independently — every net TWh and percentile in
`soco_seam_diba_duration.csv` matches that finding's table.

**One measured gap, reported not papered over:** `FLA hourly.parquet` ends
**2025-01-31** (744 h of 2025), so the three Florida seams (`SOCO_FPL`,
`SOCO_FPC`, `SOCO_TAL` — registered `proxy_ba="FLA"`) have **no 2025 load
shape**; their 2025 rows carry a blank `shape_convexity_k` and the
`NO LOAD SHAPE` status. Nothing is substituted — SOCO's own shape is not the
neighbour's. This blocks nothing in the served-schedule keeper and is a
precondition for SOCO-56.

## Formulae — the committed producers', unchanged

* `hr_by_year` — `scripts/data/derive_neighbor_hr_by_year.py::derive`:
  `HR[y] = mean_anchor_LMP[y] / (neighbor_gas_price(nb, y) × K[y])`, with
  `K[y] = mean(neighbor_load_shape(nb, y, 8760)[0])`.
* elasticity — `scripts/data/derive_neighbor_hr_elasticity.py::derive`: OLS of
  `mean_anchor_LMP[y] / K[y]` on `neighbor_gas_price(nb, y)`.

## Regeneration — and why neither committed producer does it

**Neither producer can reach SOCO at HEAD, and they fail differently:**

* `derive_neighbor_hr_by_year.py --iso SOCO` **exits 1** —
  `SOCO: no neighbour anchor map registered in NEIGHBOR_LMP_ANCHORS`. That is
  the SPP-51 fail-closed guard working as designed; SOCO simply has no entry.
* `derive_neighbor_hr_elasticity.py --iso SOCO` **exits 0 with an empty
  table.** Its `_NEIGHBOR_LMP_ISO` is still the pre-SPP-51 **global** name map
  (`MISO`/`NYISO`/`PJM`/`SPP`), and SOCO's neighbours are named `SOCO_<DIBA>`
  deliberately (so none can share a `_HR_GAS_ELASTIC` key), so every one is
  silently `continue`-d. **A silent empty table reads as "nothing to derive"
  rather than "the producer cannot see this ISO"** — the same defect class
  SPP-51 repaired in the other producer and never here.

Repairing either is a change to a producer SOCO-33 does not own, so both are
**ROUTED to SOCO-DESK, not made** (FINDING-soco-33 §7). Until that lands these
files regenerate from the **complete producer listing in
`docs/handoffs/FINDING-soco-33-2026-09-16.md` §A**, which substitutes only the
anchor resolver and is otherwise the two producers' own arithmetic.
