# NEISO condition-responsive fast-start offer surface — design note (2026-07-10)

**Branch:** `claude/neiso-winter-scarcity-charter-ac3pzu` (winter scarcity charter Limb B)
**Status:** BUILT, default-off; surface derive pending the full 2023–2025 offer
download; A/B (`neiso-58`) not yet solved.
**Reads first:** `docs/handoffs/ercot-g22-offer-surface-2026-07.md` (§5 the
honesty gate this note instantiates; §8 why the flat variant was REJECTED and
what the heterogeneity-preserving successor must do), the 2026-07-10
calibration-log entry (neiso-57: the dynamic-requirement channel engages 1 of
12 2025 tail hours; the DA tail is SUMMER-dominated in 2024/2025).

## 1. The gap

After Limb A (`2026-07-10-neiso-57-dynamic-rr`): C3c 2025 model 1h vs DA 12h
>$300 (gate [6,24] h), C5b 2025 discharge 0.827 vs 2.08 TWh. The remaining 11
actual tail hours are heat-wave evening peaks (Jun 24 ×4 more, Jul 16 ×3,
Jul 29 ×3, Dec 8 ×1) where the model's fast-start offers sit at
`heat_rate × gas + VOM` while the co-opt clears the measured requirement free —
the same "phantom sub-$200 spare" anatomy as the ERCOT G-22 wedge: the real
fleet's fast-start assets offer themselves out of the money in anticipated-
tight hours; the model's never do.

## 2. Measured identification

`data/raw/NEISO-AS/da-energy-offers/` — ISO-NE's public DA Energy Market
historical offer data (masked assets, all offer segments, Claim 10/30, unit
status). Population: PHYSICS-selected fast-start assets (Claim30 ≥ 0.9 ×
EcoMax — the whole unit deliverable in 30 minutes; ~4.1 GW, ~95 assets),
status ECONOMIC/MUST_RUN. Metric: per-asset TOP-OF-CURVE offer, expressed as
a heat-rate multiplier over the model's own NEISO gas day series (Algonquin
Citygate daily) and the model fleet's cap-weighted gas-CT heat rate, so the
multiplier round-trips through the mechanism. Driver: within-year net-load
percentile (EIA-930 ISNE Demand − WND − SUN), bins (0.80, 0.90, 0.97) — the
forward-native construction the mechanism recomputes from the model's own
load/VRE at solve time. Ladder: per bin, per-asset medians, capacity-weighted
into 5 equal-capacity quantile rungs, clamped ≥ the all-hours p50 (a loose
bin never lowers an offer). Derive: `scripts/derive_neiso_offer_surface.py`
→ `data/raw/_validation-source/neiso_offer_surface_condbinned.json`.

## 3. Mechanism (heterogeneity-preserving by construction)

`ScenarioConfig.neiso_offer_surface_conditional` (default off, NEISO-only):
the CT_PEAKER peak band splits into 5 equal-capacity rungs at the SAME
resolved height (structural no-op — P0 run lengths byte-identical), and the
P1-only markup (`data.fleet.build_neiso_offer_surface_conditional_markup`,
the shared `_conditional_surface_markup` core with the ERCOT applier)
reprices each rung to the measured bin/rung multiplier, clamped ratio ≥ 1
(loose hours byte-identical) and < 0.95 × VOLL. Within a tight hour the
lower rungs stay competitive while only the upper rungs reach the measured
wall — the exact answer to the ERCOT §8 overshoot (posting the p50 on every
row removed 3.2 GW of spare in one step).

Known scope limitation (documented, not a fit): the surface touches
CT_PEAKER only. The NEISO oil/dual-fuel peakers (no peak-band rungs; priced
at oil parity) and imports are untouched; if the A/B shows the wall forming
on the wrong resource, that is a finding, not a tuning knob.

## 4. Pre-committed honesty gate (rules 1, 11, 13, 20, 21, 25; G-22 §5)

Committed BEFORE the surface is derived or any A/B solve, so no result can
retro-justify a parameter:

1. **Parameters are the measured fast-start offer quantile ladder per
   net-load bin**, pooled 2023–2025, produced once by
   `scripts/derive_neiso_offer_surface.py` on the full download. Every number
   traces to the offer data; none is fitted to a price or volume residual.
2. **Frozen against residuals (rule 20).** The ladder re-derives only when
   the source data updates; a re-derive commit must cite the data change.
   The bin edges (0.80/0.90/0.97 — the ERCOT precedent) and the fast-start
   threshold (0.9, ISO-NE's own 30-minute concept) are pre-committed here
   and are NOT swept.
3. **If the A/B degrades the backcast, the parameters do NOT move.** Register
   the REJECTED probe (rule 15), file the finding; never retune the ladder,
   the edges, or the population to recover a metric.
4. **Volume-neutrality is a hard condition.** CT_PEAKER (and every gated
   class) TWh must not move off the measured allocation beyond the keeper's
   own deviation; a price improvement bought with volume moves FAILs.
5. **No broad elevation.** Monthly Δ vs the same-code surface-off arm must be
   ~$0 outside the anticipated-tight hours; a broad lift is disqualifying
   (the ercot33/ercot37 failure mode).
6. **No new floor (rules 17/19).** The surface only RAISES offers; it forces
   no energy. C8 forced-energy budgets must hold unchanged.
7. **No cross-ISO leakage (rule 25).** The surface JSON, flag, and clamps are
   NEISO-only; no generic fallback inherits them; ERCOT's applier is
   byte-identical (refactor covered by its existing tests).
8. **Full-span A/B registered whatever the outcome (rules 15/16):** neiso-58
   = the neiso-56 keeper recipe + `neiso_dynamic_reserve_requirements`
   (Limb A stays on — it is real structure that fires in the right event)
   + `neiso_offer_surface_conditional`, 2023–2025 one bundle per arm, plus
   the zero-forcing twin. Gates: the charter's (C3c 2025 ∈ [6,24] h with
   2023/2024 within |Δ| ≤ 10 h of DA 5 h; C5b 2025 ≥ 1.456 TWh ±30%; no
   C3a/C3b/C1 regression; C8 holds). Keeper promotion is the owner's call.

## 5. Result

(To be filled by the A/B — see the calibration-log 2026-07-10 entries.)
