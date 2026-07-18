# FINDING — the measured PJM offer surface (G-22 lever A) is INERT in the model's supply position

**Date:** 2026-07-12. **Probe:** `results/calibration/pjm99_offer_surface`
(pjm-98 keeper recipe + `pjm_offer_surface_conditional=True`, all 3 years, one
bundle). **Verdict: REJECTED (no-op)** — registered per rule 15; the frozen
surface does not move (rule 20 pre-committed honesty gate).

## What was built (all committed, mechanism stays)

The exact neiso-58 analogue for PJM: the measured condition-binned
top-of-curve offer surface from all 36 months of PJM DataMiner2
`energy_market_offers` (25.95M unit-hours, 3,595 units), physics-segmented
(CC-like 72.1 GW/h offered vs model CC_REGULAR 59.8 GW; fast-start CT-like
15.4 GW/h vs 26.0 GW installed), frozen into
`data/raw/_validation-source/pjm_offer_surface_condbinned.json`, posted onto
5-rung CC_REGULAR + CT_PEAKER peak-band ladders at the P1-only
`mc_bid_adjust` seam (`ScenarioConfig.pjm_offer_surface_conditional`). Top-bin
walls: CC rungs 4–5 at 6.06/14.55 × base-HR 6.372 (≈ $119/$270 at 2024 gas),
CT at 5.56/9.26 × 11.697 (≈ $186/$310) — reproducing the measured $200–500
band on ~4 GW. The mechanism engaged in every solved year ("repriced 497 gas
peak-rung rows"; tightest bin 263 h) and entered the P1 objective.

## The A/B result — byte-identical prices

Same-day rule-16 baseline (`pjm98_baseline_20260712`) vs probe:

| year | base LW mean | probe LW mean | base top-150 | probe top-150 | base max | probe max |
|---|---|---|---|---|---|---|
| 2023 | $28.47 | $28.47 | $30.7 | $30.7 | $48 | $48 |
| 2024 | $27.15 | $27.15 | $34.4 | $34.4 | $129 | $129 |
| 2025 | $37.23 | $37.23 | $44.5 | $44.5 | $81 | $81 |

Every price statistic (mean, top-150 LW, p99, max) is identical to the cent
in all three years. The repriced upper rungs dispatched 0.3 GWh (2024) / 0.0
(2025) of a 0.84/1.72 TWh peak band; band totals are unchanged — the only
diffs are degenerate-tie reshuffles among equal-priced lower rungs (max unit
annual shift ~5.5 GWh). C1/C3 metrics are therefore pjm-98's exactly.

## Why: the charter's "too-cheap top" is really a "too-deep sub-actual body"

The idle-supply audit on the SAME baseline shows the model's marginal unit at
the top-150 hours sits at $30–45, with **21–24 GW of idle thermal offered
BELOW the actual DA price** — coal p50 $28.7 (9.0 GW idle), CT_PEAKER econ
p50 $42.6 (9.2 GW), ST_GAS $42.8 (2.4 GW). The keeper's CC/CT **peak bands
(5.0×/4.0×HR ≈ $91–134) are already extramarginal there** — the LP never
dispatches them, so repricing them higher (to the measured $186–310 wall)
cannot change any dual: an LP price moves only when the *marginal* offer
moves. The surface's clamp (`ratio >= 1` vs the resolved peak) is working as
designed — rungs 1–3 hold the keeper's fitted peak height, and demand never
eats past the body into rungs 4–5.

This differs from ERCOT/NEISO, where the same mechanism landed because those
fleets are tight enough at the missed tails for the peak rungs to become
marginal. In PJM the price-capping capacity is the **$28–115 mid-curve** (the
audit's 21 GW "stack depth between model price and actual"), not the peak
band.

Cross-check against the measured curve (handoff §2, July-2024 top-150): the
measured fleet prices ~20.8 GW in the $35–83 band and clears $83 — i.e. the
real market's *cleared demand* (physical load + exports + DA reserves +
virtual demand) eats ~9–10 GW deeper into that band than the model's served
load does. The model has BOTH a cheaper mid-curve (idle coal at $28 vs
measured long-run $35–83 tail; CT econ at $42 vs measured fast-start $35–200
spread) AND a shallower DA procurement depth.

## Re-scoped levers (for the next session — diagnosis only here, rule 1)

1. **Lever A′ — measured MID-CURVE (body) surface.** The same DataMiner2
   corpus measures the full offer curves, not just tops. The model's CT econ
   bands (1.05–1.27×HR), idle coal econ/peak bands ($28–55) and ST_GAS bands
   sit well below the measured mid-curve distribution of their physics
   segments. A measured condition-binned repricing of the *econ* bands (the
   $35–200 region) attacks the capacity that actually caps the dual. Caution:
   econ-band repricing perturbs P0 run lengths (the rejected ERCOT flat-CT
   precedent) — it needs the same P1-only seam and a careful clamp design,
   and the coal side interacts with the take-or-pay/passthrough sigmoids
   (rule 19: reconcile, don't stack).
2. **Lever B — DA procurement depth** (reserves ARE small: ~3.5 GW RTO +
   ~2.6 GW MAD; but the model's DA demand also lacks the virtual/export
   depth of the real DA market). The handoff's "B is inert until A prices
   the top" had the dependency backwards: **the top-of-curve wall is inert
   until procurement depth pushes the margin into it.** B (or a measured DA
   cleared-volume basis) is a precondition, not a follow-up.
3. Lever C (2025 seam over-export ~1.8 GW) unchanged — secondary.

The pjm-99 mechanism and frozen surface STAY in the codebase (rule 1:
structurally real, measured, correctly clamped — it will bind the moment the
body/procurement is fixed and demand reaches the wall); the flag simply
remains off in the keeper line until then.

## Reproduction

- Baseline: `python scripts/replay_keeper.py results/calibration/pjm98_cc_mustrun
  --out-dir results/calibration/pjm98_baseline_20260712` (rule-16 throwaway,
  gitignored).
- Probe: `python scripts/probes/_pjm99_offer_surface_probe.py` (defaults).
- Audit: `python scripts/probes/_g22_idle_supply_audit.py
  results/calibration/pjm98_baseline_20260712 --years 2023 2024 2025`.
- Surface derive: `python scripts/data/derive_pjm_offer_surface.py` (requires the
  gitignored raw offers; `scripts/data/fetch_pjm_energy_offers.py` regenerates,
  ~40 min).
- ENV: 15 GB RAM box — the 5-rung ladder grows the PJM per-plant LP past the
  OOM line; a 10 GB swapfile (`fallocate -l 10G /swapfile && mkswap && swapon`)
  absorbs the transient post-solve peak (~15.9 GB).
