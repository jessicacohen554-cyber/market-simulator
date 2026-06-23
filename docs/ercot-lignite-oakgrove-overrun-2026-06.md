# ERCOT lignite ~1 TWh over-run — root cause (Oak Grove), 2026-06

**Determination: leave it (no-fit default, CLAUDE.md #1/#11).** The lignite
over-run passes the C1 in-band gate, conserves within the coal family, and every
candidate lever is a fit or a circular pin.

## Symptom

run153 (`results/calibration/ctharcut_pp_3yr`) coal-family fuel-mix, model−actual:

| year | COAL_LIGNITE Δ TWh | COAL_PRB Δ TWh | coal net |
|---:|---:|---:|---:|
| 2023 | +1.07 | −0.84 | +0.23 |
| 2024 | +1.34 | −1.07 | +0.27 |
| 2025 | +0.48 | −0.37 | +0.11 |

Lignite over-runs and PRB under-runs by nearly the same amount each year — a
**merit-order tilt that conserves inside the coal family** (so C2 system-volume
passes and C1 lignite stays in-band). Not a system-energy error; a split between
two coal sub-classes.

## It is one plant: Oak Grove (6180)

Per-plant model vs CAMPD-net (plant_hourly_fit), GWh:

| plant | 2023 Δ | 2024 Δ | 2025 Δ |
|---|---:|---:|---:|
| 6180 Oak Grove | +1255 | +872 | +576 |
| 7030 Major Oak | +100 | +261 | +131 |
| 6183 San Miguel | −159 | −182 | −154 |

San Miguel runs *under*; Major Oak is small. The lignite class delta is
essentially Oak Grove alone, running ~5–6 pp net CF hotter than reality
(2024: model ~75% net vs CAMPD ~70% net).

## Why — every measured input is already correct

Checked against the CLAUDE.md #11 "measured, forward-reproducible, not fitted"
test:

- **Heat rate** — model 9.49 vs CAMPD-measured 9.485 Btu/kWh. Correct; Oak Grove
  is a genuinely efficient 2008 supercritical unit.
- **Outages** — 2024/2025 CAMPD partial-outage plateaus are already applied
  (`data/raw/campd-partial-outages.csv`). **2023 has no detectable plateau**
  (mean CF 82.7% but daily-max hits ~1.0 on best days → diffuse economic cycling,
  not a half-unit outage). `derive_partial_outages._detect` returns `[]` for 6180
  in 2023 — nothing honest to add.
- **Fuel price** — Oak Grove is **merchant with no EIA-923 Schedule-5 coal
  receipts** (confirmed: 6180 and 7030 file none; only San Miguel 6183 reports,
  at ~$3.5/MMBtu — its own high-cost mine). So no per-plant delivered cost exists.
  It is priced at the deliberate flat `_LIGNITE_PRICE_2023_25 = $1.45/MMBtu`
  *marginal-extraction* cost (mine fixed costs sunk on a dispatch-hour basis).
  Bumping that to a delivered number would double-count sunk mine costs.
- **Max-CF ceiling** — `COAL_MAX_CF_BY_PLANT[6180] = 0.90` (a physical
  sustained-output limit). The unit runs ~75% net, below the ceiling, so it is
  not binding. Lowering it toward the observed ~0.70 annual CF would pin
  availability to the observed energy — the **forbidden circular CEMS cap** the
  retiree-cap comment explicitly warns against for the operable fleet.

**The mechanism is real.** At 9.49 HR × $1.45 lignite + $4.5 VOM ≈ **$18/MWh**,
Oak Grove sits right on the cheap-gas margin (2024 Waha-ish gas $2.19 →
efficient gas-CC ≈ $17/MWh). The LP keeps it economic a few pp more than the
real unit chooses to cycle. Each input is individually defensible; the residual
is genuine sensitivity at the lignite↔gas crossover.

## What would "fix" it — and why we don't

All remaining levers move the number by burying a residual in an input
(CLAUDE.md #11) or by pinning to actuals:

- bump the $1.45 marginal-extraction price → double-counts sunk mine cost;
- bump coal VOM (4.5) for lignite → a fit unless grounded in a citable
  lignite-vs-railed-coal O&M premium (the only *potential* non-fit path, parked
  pending a real source — not chosen by the residual);
- lower Oak Grove's CF ceiling to the observed annual CF → circular pin.

The PRB −1 TWh mirror is the same coupling viewed from the other side; it too is
in-band. No action taken; revisit only if a sourced lignite O&M premium
materialises or the gas-basis fix shifts the lignite↔gas crossover.
