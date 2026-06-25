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
is supplied (verified: all 92 `test_reserve_coopt`/`test_dispatch` cases pass
unchanged).

### 2. Phantom-headroom fix (P2 commitment)

A perfect-foresight LP leaves cold slow-start units idle, yet the energy-only
reserve headroom counts their full available capacity as responsive reserve — so
on acute-but-not-thin days (May 2024 8/24/26: elevated load, ample *modeled*
headroom) it cannot form co-opt scarcity. The fix is to run the multi-product
co-opt in the **P2 commitment-screened solve**: `apply_commitment_with_coal_pin`
zeroes the `availability` of decommitted idle CC/CT units, and the
shared-headroom RHS is derived from `pmax × availability`, so the idle capacity
drops out of the reserve pool. Only responsive (committed/online) capacity backs
the AS demand curves. Engage with `--commitment` alongside
`--ercot-multiproduct-as-coopt`.

> Follow-up (not yet built): offline quick-start peakers that P2 decommits also
> drop from the *all*-row Non-Spin pool. Crediting their startable capacity back
> via `reserve_headroom_extra_cap` (the param exists) would restore the offline
> Non-Spin supply through P2 — a refinement that only *reduces* firing, so its
> absence is conservative (biases toward firing, which the gate guards against
> over-firing other months).

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

| Configuration | May 8/24/26 load-wtd LMP | Aug 2024 | 2023-H2 | 2025 | Notes |
|---|---|---|---|---|---|
| overlay-off (energy-only co-opt) | _TBD_ | | | | baseline under-prices acute days |
| overlay-on (measured DAM-AS bridge) | ~$45 (target) | | | | current keeper bridge |
| **endogenous multi-product co-opt** | _TBD_ | | | | this build (overlay off) |

_Run command (all years, per-plant, dashboard bundle):_

```
python scripts/run_calibration_full.py --year 2023 2024 2025 \
  --energy-reserve-coopt --ercot-multiproduct-as-coopt --commitment \
  --out-dir results/calibration/ercot-multiproduct-as-coopt
```

Results, the dashboard registration, and the overlay-on/-off/endogenous
comparison are filled in once the all-years solve completes (CLAUDE.md #13: every
completed backcast run goes on the dashboard in the session it was produced).
