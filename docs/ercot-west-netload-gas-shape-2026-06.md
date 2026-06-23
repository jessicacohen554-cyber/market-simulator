# ERCOT West/Permian CT over-run: net-load-indexed Waha gas basis (2026-06, WIP)

**Status: mechanism built, parameterization in progress. NOT yet a keeper.**
Branch `claude/ercot-run154-delivered-gas-*`.

## What changed vs the run153 framing

The run152/153 handoff claimed the 100%-spot Permian peakers "genuinely see ~$0
Waha gas, so the fix is peaker economics not gas price." That is **wrong twice
over**, and this branch corrects both:

1. **Delivered ≠ hub.** The model priced West/Panhandle gas off the Waha *trading
   hub* (wellhead pooling point, ~$0/MMBtu in 2024, negative ~42% of days) while
   every other ERCOT zone is priced off EIA-923 *delivered* receipts. A power
   plant pays delivered (burner-tip) gas, not the wellhead pool.
2. **The per-plant contract haircut (run153) was backwards.** It scaled each
   unit's hub basis by its EIA-923 *spot share*, so the 100%-**spot** units
   (Permian Basin 3494, Laredo 3439) kept the *full* Waha collapse (→ $0 → ran
   baseload) while the 100%-**contract** unit (Ector County 58471) lost the
   discount entirely (→ ~$2.3 gas → idled). "100% spot" is a contract *type*, not
   a *price* — spot gas is still delivered (transport + as-burned). Dropping the
   haircut and pricing all West units on one delivered basis fixes **both**
   directions.

`oil_primary_bin_fuel` (Lever A) is also enabled: Morgan Creek (3492) is an
EIA-860 Petroleum-Liquids/DFO peaker the bin sheet routed through gas CT_PEAKER;
repricing it on distillate idles it correctly (model 0 vs real 26 ✓). Lever A
alone, with the run153 haircut, brought CT_PEAKER aggregate to +3.8% — but the
operating-shape gate still failed (Permian/Laredo baseload, Ector idle): the
right *number* through a wrong *mechanism*.

## The structural mechanism (this branch's contribution)

A scalar floor (`ercot_gas_delivered_floor_basis`) closes the over-run but is a
chosen number, and a *single* annual scalar prices a West **peaker** (burns only
in high-net-load scarcity hours, when Waha is firm) on the same ~$0 annual-mean
gas as a West baseload **CC** (burns all hours incl. the cheap collapse). That
collapses the heat-rate spread and floats the peakers.

**`ercot_west_netload_gas_shape`** (new) makes the West/Panhandle Waha basis a
per-hour function of **system net-load** (`load − wind − solar`) — the same
weather/demand driver the ST_GAS reliability drag keys off — because the Waha hub
is anti-correlated with demand (collapses at low-demand oversupply, firms at high
demand). It adds a **mean-zero** net-load shape on top of the annual zonal basis
(so the measured annual Waha basis is preserved, only redistributed across
hours), amplitude pinned so the high-demand hours reach
`ercot_west_gas_firm_basis` (the firm Waha delivered level a peaker pays in the
scarcity hours it runs). The peaker/CC split then falls out of *when each unit
runs*, not a per-unit number or a chosen floor.

- Code: `market_sim/data/fuel.py::apply_ercot_west_netload_gas_shape`,
  config `ScenarioConfig.ercot_west_netload_gas_shape` /
  `ercot_west_gas_firm_basis`, wired in `run_calibration.py` after
  `apply_ercot_zonal_gas_basis` (passing the LP-served net-load), env
  `ERCOT_WEST_NETLOAD_GAS=1` / `ERCOT_WEST_GAS_FIRM_BASIS=<f>`.
- Forward-reproducible & condition-responsive (net-load = a load forecast + a VRE
  build; more VRE lowers net-load and shifts the curve), measured-anchored
  (annual Waha basis + firm Waha level) — admissibility #10/#12.

## Probe results (2024, matched run153 recipe + Lever A, no haircut)

| variant | West gas | CT_PEAKER | CC_REGULAR | COAL_PRB | notes |
|---|---|---|---|---|---|
| Lever A + run153 haircut | spot $0 | 8.52 (+3.8%) | 150.6 (+3.5%) | 42.8 (−2.1%) | wrong shape (Permian/Laredo baseload, Ector idle) |
| + uniform floor −0.50 | $1.61 all hrs | 5.52 (−32.8%) | 146.9 (+2.7%) | 44.5 (+1.9%) | overshoots; Permian under (242) |
| + uniform floor −0.72 | $1.39 all hrs | 6.41 (−21.9%) | 148.8 (+2.4%) | 44.4 (+1.6%) | Permian/Ector/CCs ✓, within ±2.3 TWh band; CT low |
| **+ net-load shape, firm −0.50 @ p95** | annual $0.48, firm $1.69 | **10.92 (+33.1%)** | **146.0 (+0.4%)** | **43.4 (−0.6%)** | shape FIXED CC/coal; CT over — firm regime too narrow |

EIA-930 2024: CT_PEAKER 8.21, CC_REGULAR 145.41, COAL_PRB 43.68. C1 band ≈ ±2.3
TWh (0.5% of annual gen) per class.

The net-load shape **fixed the CC/coal collateral damage** (CC +0.4%, coal −0.6%,
both near-perfect — the West CCs now run on cheaper shoulder gas and stop
over-displacing). But CT is +33% because firm Waha is reached only at p95 (top
5%), so Permian (2649 vs 456), Laredo (1864 vs 52), Ector (2456 vs 642) still see
cheap gas in the mid-merit hours they run.

## Next step (the parameterization fix)

Widen the firm regime to cover the demand hours peakers actually run, grounded on
the **measured negative-day frequency** (Waha negative ~42% of days in 2024 →
the top ~58% of net-load hours are firm). Two clean options:

1. **Lower the firm-anchor percentile** `_WEST_GAS_FIRM_NETLOAD_PCTILE` from 95 to
   ≈ the measured firm fraction (e.g. p42, so everything above the 42nd net-load
   percentile is at/above firm). Clamp the linear at `firm_basis` above the anchor
   so high hours don't over-firm.
2. **Two-regime (step) form keyed on the measured collapse frequency**: bottom
   `collapse_freq` of net-load hours → deep collapsed basis; top
   `(1−collapse_freq)` → `firm_basis`; `deep` solved from the annual-mean
   constraint (`collapse_freq·deep + (1−collapse_freq)·firm = annual_measured`).
   For 2024: `0.42·deep + 0.58·(−0.50) = −2.19 → deep = −4.52`.

Per-year collapse frequencies needed (2023/2024/2025); 2024 = 42% (CSV note).
2023 Waha annual +$1.82 (few negative days), 2025 ~$1.15 (~39 negative days per
NGI). Derive cleanly or source the daily Waha negative-day counts.

**Lone residual to report (not fit):** Laredo (3439) real CF 3% but model runs it
hard at the *same* gas Permian matches on → its model heat rate is too low; a
per-unit data issue, not zonal-gas. Plant 7325 (Houston) real 860 vs model 6 — a
pre-existing non-West CT under-runner, out of scope.

## Reference floor run (−0.72, for comparison only — NOT a keeper)

`results/calibration/ercot_run154_delivered_gas` is a 3-yr solve on the uniform
floor −0.72 (CT within ±2.3 TWh band all years but ~−1.7 TWh low, structurally a
chosen scalar). Superseded by the net-load shape; do not register.
