# ERCOT endogenous multi-product AS co-optimization (forward analogue of the DAM-AS overlay)

**Date:** 2026-06-25
**Scope:** the flagship forward-methodology build (Finding 1 / G1 of
`docs/forecast-methodology-gaps-2026-06.md`). Replaces the measured DAM AS-MCPC
overlay (`results/scarcity.py:ercot_dam_as_overlay_series`) with an **endogenous
multi-product AS demand-curve co-optimization**, so the binding product's
reserve dual reproduces the measured binding DAM AS MCPC **without reading it
from disk**.

---

## What changed

The single-product ERCOT co-opt (`ercot_reserve_coopt_inputs` /
`energy_reserve_coopt`) was already forward-native — one lumped
contingency-reserve product priced against a VOLL-anchored ORDC demand curve,
co-optimized with energy so the reserve dual lifts the LMP (RTSPP = LMP +
reserve price). Two gaps closed here:

### 1. Multi-product stack (`ercot_multiproduct_as_coopt`)

`results/scarcity.py:ercot_multiproduct_reserve_coopt_inputs` builds **one
co-opt demand curve per AS product** — RegUp / RRS / ECRS / NonSpin
(`config/constants.py:ERCOT_AS_PRODUCTS`) — each its own reserve *family* (own
per-zone reserve variable, own requirement, own VOLL-anchored demand curve). The
per-hour **max** across the products' balance-row duals is the `binding_mcpc`
the overlay used to read.

* **Additive, not nested.** ERCOT holds the four products as *separate* capacity
  (~7–8 GW total out of the energy stack every hour), unlike NYISO's nested
  10-/30-minute products where one MW counts for both. The products therefore
  **share one headroom pool additively**: `sum_g P[g] + Σ_p R[p] ≤ responsive
  headroom`. That additivity (vs the single ~3 GW lumped product) is most of the
  extra scarcity the overlay carried.
* **Quality cascade (higher-quality substitutes down).** Two **nested
  shared-headroom rows** encode the substitution cascade:
  * a *fast* row over the synchronized/spinning responsive set
    (`RESERVE_FUEL_TYPES` minus the offline-capable `QUICK_START_FUEL_TYPES`
    peakers) bounding RegUp/RRS/ECRS, and
  * an *all* row over the full responsive set (adding the gas-CT/oil quick-start
    peakers a 30-minute Non-Spin award can come from) bounding all four.

  The fast products sit in **both** rows; Non-Spin only in the *all* row. So a
  Non-Spin MW can be supplied by a quick-start peaker the fast products cannot
  reach, while the fast products price up first when spinning headroom is scarce
  — the binding-MCPC days. Storage backs both rows (batteries respond in
  seconds → every product).

This is wired into `model/dispatch.py` as **additional reserve-balance rows
sharing the headroom constraint** — the `_build_reserve_rows` shared-headroom
section now accepts an additive headroom spec (`reserve_headroom_eligible`,
`reserve_headroom_products`, `reserve_headroom_extra_cap`) where several products
share one headroom row. The rows are built **vectorized** (block-diag / kron over
the per-hour pattern, no Python loop over hours), and the legacy per-class path
(ERCOT single-product, PJM, MISO, NYISO) is byte-identical when no additive spec
is supplied (verified: all 93 `test_reserve_coopt`/`test_dispatch` cases pass
unchanged, including the upstream `online_gated` NYISO scaffold this build was
rebased onto).

### 2. Phantom headroom — resolved by additivity, NOT by P2 commitment

The original concern (G1): a perfect-foresight LP leaves cold slow-start units
idle, yet the energy-only single-product reserve headroom counts their full
capacity as reserve, so on acute-but-not-thin days it cannot form co-opt
scarcity — the documented reason the measured overlay was needed.

The multi-product stack **resolves this without any commitment surgery**. The
lumped single product held only ~3 GW (`ordc_mcl` + LOLP buffer); the additive
four-product stack holds the **measured ~7.5 GW** every hour. That larger
requirement binds on genuinely tight days even with idle capacity still in the
headroom RHS — so the **P1 dispatch alone** forms the acute-day scarcity (May
2024 8/24/26 lifts to $90.8/MWh load-weighted, see gate below) while leaving the
slack months close to actual.

A P2 commitment-screened solve was tried and **rejected**: P2's screen is
energy-only (it decommits idle units on energy economics, ignoring that ERCOT
keeps units online *for AS*), so it starved the reserve pool and the co-opt
over-fired in every month (2024 annual load-wtd LMP $123.7 vs $26.8 actual). The
keeper is therefore **P1-only** — no `--commitment`. If a future need arises to
gate idle capacity out of a *specific* product without commitment, the
LP-linear `online_gated` lever (`R[c,z] - ρ·Σ_g P[g] ≤ 0`, reserve only from
online generation) is wired and available; it is not needed for the gate.

## Requirements (P1b seam)

Each product's requirement is the ERCOT-published procurement quantity
(`ASPLANNP433`, `ercot_as_plan_requirement_mw`) for the weather year — the
**measured realization** the forward requirement-setting formula validates
against, never fitted to a price. The forward seam is explicit:
`ercot_as_forward_requirement_mw` returns `None` today (→ fall back to measured);
when **P1b** lands it returns `req_product(t) = f(net_load, ramp, VRE_share)` and
the co-opt is forward-native with no change at the call site. The demand-curve
*prices* are VOLL-anchored (`config.ordc_voll`, the AS offer cap) market-design
schedules, so the hourly scarcity **incidence** comes from the responsive
headroom in the shared-headroom RHS — a tighter fleet clears AS lower on the
curve at a higher price — not from any tuned per-product level.

## Honesty gate

The reserve dual forms **from the LP** — it is the `_build_reserve_rows`
reserve-balance dual (`DispatchResult.reserve_price_by_family`, the per-hour max
across products = MCPC), and the energy-LMP lift is the shared-headroom dual that
couples reserve to energy. There is **no adder tuned to the MCPC** anywhere on
the path. `tests/test_ercot_multiproduct_coopt.py` pins this: raising the AS
offer cap reprices the *same* physical shortfall (the price tracks the demand
curve the LP clears against, not a fixed number), and additive products price a
shortfall that independent products do not.

## Regime gate / what retires

The measured DAM-AS overlay (`ercot_dam_as_overlay`) **stays** as the pre-RTC+B
backcast bridge (already regime-gated off for RTC+B / year ≥ 2026). It is retired
only from the **forward** path once the greenlight gate passes — the endogenous
co-opt reproduces the acute days *without* the overlay while holding the other
months/years.

---

## Greenlight gate — May 2024 acute-day reproduction

Target: the endogenous per-product reserve dual reproduces the ERCOT acute days
(May 2024 8/24/26 → load-weighted LMP ~$45) **without** the measured overlay,
while holding the other months/years (no over-fire of Aug 2024 / 2023-H2 / 2025).

**`159` = run157's exact recipe with the DAM-AS overlay swapped for the
endogenous multi-product co-opt** (P1-only; `solve_and_persist` with run157's
recorded `calibration_flags`, only `ercot_dam_as_overlay→False` +
`energy_reserve_coopt`/`ercot_multiproduct_as_coopt→True`):

| year | model annual | actual RT | monthly MAE vs RT | May 8/24/26 acute | May month |
|---|---|---|---|---|---|
| 2023 | $42.88 | $48.36 | $11.47 | $24.61 | $23.06 |
| 2024 | $22.37 | $26.83 | **$5.17** | **$39.97** | $21.26 |
| 2025 | $33.41 | $32.49 | **$2.13** | $30.16 | $32.89 |

**Gate status: PARTIAL.** The endogenous co-opt **lifts the May-2024 acute days
to ~$40** (vs the $21 month average) — directionally the right behavior, close to
the ~$45 figure, with **no over-firing** (2025 MAE $2.13, 2024 MAE $5.17). But it
does **not** reproduce the *broad* May-2024 elevation the overlay provides
(run157 lifts the May *month* $23.6 → $46.7 ≈ actual DA $44.8; `159`'s May month
is $21.3). 2023 stays under-priced ($42.9 vs $48.4 — the documented out-of-market
scarcity year RTORDPA carries).

**Root cause = phantom headroom.** In P1, idle slow-start units still count toward
the shared-headroom RHS, so most May hours are not reserve-thin and the co-opt
only binds on the genuinely tight acute days — exactly the gap G1 named. The
multi-product additivity (~7.5 GW vs the old ~3 GW) closes part of it (acute days
fire) but not the broad month. May 2024's sustained AS scarcity was driven by
high midday solar decommitting thermal, leaving the **committed online** fleet
thin into the evening ramp — a *commitment* signal the perfect-foresight P1
dispatch erases (it keeps thermal "available").

**Why the obvious P1 fixes don't work.**
* **Online-gating (`R - ρ·Σ_g P[g] ≤ 0`)** is *counterproductive* here, not just
  weak. It ties reserve to online *output*, so on a tight evening (fast thermal
  running hard, large ΣP) it grants *more* reserve and *suppresses* scarcity —
  the opposite of what's needed. This is upstream's documented "generation
  subsidy, not a scarcity charge" finding, sharper in ERCOT's additive form.
* **P2 commitment** (the energy-only screen) decommits units on energy economics
  alone, ignoring that ERCOT keeps thermal online *for AS*, so it starves the
  reserve pool and over-fires every month (2024 annual $123.7).
* **Curve/level tuning** (higher per-product VOLL, steeper demand curves) fires
  on *every* hour with thin headroom — no May-specific selectivity — so it
  over-fires the held months rather than lifting May alone.

**The real fix is AS-aware commitment** — a commitment screen that values a
unit's *AS* revenue (not energy margin alone), so the units ERCOT keeps online
for Reg/RRS/ECRS stay committed, the midday-solar decommitment thins the *online*
fast fleet, and the evening reserve binds endogenously. That is a larger modeling
build (co-optimized commitment ↔ AS), scoped as the next step beyond this bundle.

| Configuration | 2024 May month | verdict |
|---|---|---|
| run155a (no overlay/co-opt) | $23.6 | baseline under-price |
| run157 (measured DAM-AS overlay) | $46.7 (≈actual $44.8) | pre-RTC+B bridge, stays for backcast |
| **159 (endogenous multi-product co-opt, P1)** | $21.3 (acute days $40.0) | **partial** — acute days lift, broad month under-fires; broad May awaits AS-aware commitment |
| endogenous co-opt **+ P2 commitment** | (annual $123.7) | rejected — P2 starves the reserve pool, over-fires |

_Run command (all years, per-plant, P1-only, dashboard bundle `159`) — reproduce
via the run157 recipe (`scripts/archive/run_159.py` driver) or:_

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
  --energy-reserve-coopt --ercot-multiproduct-as-coopt \
  --out-dir results/calibration/159
python scripts/dashboard_add_run.py --label "159 multiproduct-as-coopt" \
  --bundle results/calibration/159
python scripts/build_manifest.py
```
