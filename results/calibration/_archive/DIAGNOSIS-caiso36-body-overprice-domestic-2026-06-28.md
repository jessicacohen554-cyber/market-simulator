# CAISO 36 diagnosis — the reference-seam body over-price is DOMESTIC, not the seam shape

**Date:** 2026-06-28
**Probe:** `results/calibration/caiso36_midday_convexity` (3-yr, P1) — REJECTED
**Keeper protected:** caiso 35 (`caiso35_reference_seam`) source restored byte-for-byte.

## What was tried (the caiso 36 hypothesis)

The task hypothesis: caiso 35's CA-zone LMP over-price (+90–128% vs actual) is the
forward reference-seam price being too *smooth* midday — it never crashes like the
real Palo-Verde / Malin hub, so midday LMP and the annual mean inflate. Proposed
fix: deepen the WECC seam net-load convexity so the reference (and export) price
crashes midday.

Implemented and solved 2023–25:
- WECC_DSW `load_shape_exponent` 1.0 → 2.5
- WECC_PNW `gross` → `net`, exponent 1.0 → 1.5
- Lowered the net-corridor midday floor to a small negative (sign-safe power)
- Dropped the inflated partial-coverage 2023 `hr_by_year`; re-derived anchors

The seam price shape moved exactly as intended (DSW midday reference import
~31 → ~11; PNW ~40 → ~19, validated against the measured hub diurnal).

## Result: the body did NOT improve, and interchange regressed

| Year | CA-zone avg LMP (actual) | caiso 35 | **caiso 36** |
|------|--------------------------|----------|--------------|
| 2023 | 43.8 | 100.0 | **98.7** |
| 2024 | 33.0 |  62.8 | **69.7** |
| 2025 | 33.6 |  68.5 | **75.3** |

- 2023 hours >$200: still **744** (target ~tens).
- Interchange err: 2023 +3.56 → **+8.49 TWh**; 2024 +2.78 → **−4.95** (flipped to
  under-import); 2024 diurnal r **0.93 → 0.49**.

The deeper convex import tail makes heavy import climb an expensive curve (2024
under-imports), and the cheaper midday export price over-exports — so the seam
change is a **net regression** on the metric it was supposed to keep good.

## Root cause (dispatch evidence, 2023 P1)

CA midday (h11–14) energy balance, per-hour averages:

| | MW |
|---|---|
| CA demand (SP15+NP15+ZP26) | 23,833 |
| solar (fully dispatched, ~99% of its cap — **not** curtailed) | 10,838 |
| nuclear / wind / hydro / other / biomass | ~6,400 |
| import (capped) | 2,532 |
| **economic gas_cc (marginal)** | **6,504** |

- The marginal unit midday is **economic gas_cc**, whose marginal tranche bids
  **~89 $/MWh** (implied HR ~25 at $2.84–3.5 gas — fuel + P1 startup-amortization
  + reserve co-opt, not pure fuel).
- There is **no model midday solar surplus**: solar is fully used and CA still
  needs 6.5 GW of gas_cc, so gas — not solar, not the seam — sets the midday price.
- The model already imports **2,532 MW midday vs the measured 651 MW** (EIA-930
  net interchange), so the body is **not** import-starved; the high CA price is
  what *pulls* imports to the (forward-ATC) cap, not the cause.
- The over-price is a **level** problem at *all* hours (night ~101, midday ~89,
  evening ~114 — only a ~20 $/MWh duck curve vs the deep real one), consistent
  with a domestic gas_cc offer-curve / reserve level, not a midday seam shape.

The seam price shape is essentially irrelevant to the body because imports are
inframarginal/capped midday — the marginal price is set by the domestic gas_cc
offer stack regardless of what the import reference price is.

## Why caiso 32 (measured hub) looked better — and why the seam still can't fix it

caiso 32 (measured-hub ladder) had a lower body (74/46/51). The caiso 32→35
regression is most plausibly the **ATC change** (measured two-sided → forward
solar-derated midday cap) plus the cheaper measured midday hub price letting more
midday import displace gas_cc — NOT the price *shape* per se. But the model
already imports ~4× the measured midday volume, so recovering the body by flooding
even more midday import would be unphysical. The remaining ~30/13/17 $/MWh gap
above actual (even at caiso 32) is the domestic offer-curve level.

## Recommendation

The body over-price cannot be fixed from the seam. The real levers are domestic
and out of this task's scope:

1. **gas_cc marginal-tranche offer level** — the midday marginal CC tranche bids
   an effective HR ~25; investigate the binning top tranches + the P1 startup
   amortization markup + reserve co-optimization adder inflating midday offers.
2. **Midday solar fraction** — the model has ~10.8 GW midday solar vs CAISO's
   ~13–14 GW utility solar in 2023; check CA solar capacity / Lever-D derate /
   BTM netting so a real midday surplus can form and crash the price.
3. The forward-ATC midday solar-derate vs the measured ATC (the caiso 32→35
   delta) is worth an explicit A/B, but is secondary to (1)–(2).

caiso 36's seam-convexity approach is **not** a keeper and the source is reverted.
The probe bundle is retained as the negative-result record.
