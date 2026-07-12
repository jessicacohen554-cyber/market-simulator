# FINDING — PJM G-22 resolved: DA procurement depth (virtual bids) is the precondition, the measured surfaces price it

**Date:** 2026-07-12. **Probes:** `results/calibration/pjm100_da_virtual_bids`
(lever B alone), `results/calibration/pjm101_depth_surfaces` (B + the frozen
pjm-99 top-of-curve surface + the new mid-curve floor). Baseline:
`pjm98_baseline_20260712` (rule-16 same-day re-solve of the pjm-98 keeper).

## 1. The adjudication (cheap diagnostics first, rule 1)

Two no-LP diagnostics settled the A′-vs-B design question the pjm-99 no-op
left open (`docs/FINDING-pjm-offer-surface-noop-2026-07.md` §Re-scoped
levers):

1. **Measured DA demand structure** (PJM DataMiner2 `hrl_dmd_bids` +
   `hrl_da_incs_decs`, July-2024 hot week): fixed DA demand bids track RT
   load (150.8 vs 152.1 GW at the 7/15 peak), and the ~9-10 GW procurement
   gap is **entirely the virtual layer** — net cleared DEC − INC at the
   actual DA price is +7 to +11 GW at peaks, ≈ −1.5 GW overnight. The DA
   depth phenomenon IS the virtual bid curves.
2. **Depth-price sweep** (`scripts/probes/_g22_depth_price_sweep.py`, the
   model's own idle stack, top-150 hours): +10 GW of fixed extra depth moves
   the implied price only **+$2.0 / +$4.5 / +$2.8** (2023/24/25) — the
   marginal classes at depth (COAL, CT_PEAKER, ST_GAS) are offered $28-45
   where the measured fleet prices the same curve region higher. Depth alone
   cannot price the peak; the mid-curve level alone has nothing to reach it.
   **B and A′ are complementary halves, not alternatives.**

## 2. Lever B — the DA virtual-bid layer (`pjm_da_virtual_bids`)

`src/market_sim/data/virtual_bids.py`: the year's measured HOURLY submitted
INC/DEC bid curves (8 equal-MW rungs/side/hour) enter the LP as pseudo-units
— INC rungs as zero-emission supply, DEC rungs as export-sink-form
withdrawal capacity — with **endogenous clearing**: the dual finds where the
model's own stack crosses `load + DEC(p) − INC(p)`. Submitted ex-ante
curves are the demand-side mirror of generator energy offers (rule-13
admissible, same class as delivered fuel prices / CAMPD outage windows);
cleared volumes and prices stay LP outputs — nothing is pinned. The demand
vector is untouched (load-weighted scoring weights stay physical). Committed
forecast substitute: the condition-binned normalized surface
(`scripts/derive_pjm_da_virtual_surface.py`).

**pjm-100 (B alone) vs baseline — top-150 load hours:**

| year | base LW | B LW | actual | base max | B max | actual max | cleared net DEC−INC |
|---|---|---|---|---|---|---|---|
| 2023 | $30.7 | **$40.1** | $76.2 | $48 | $99 | $308 | +9.9 GW |
| 2024 | $34.4 | **$52.8** | $82.8 | $129 | $126 | $200 | +10.4 GW |
| 2025 | $44.5 | **$85.9** | $136.2 | $81 | $313 | $503 | +11.2 GW |

The endogenously cleared depth lands exactly on the measured +7-11 GW, and
the all-hours LW mean moves toward actual in all three years
(28.47→28.58 vs 29.33; 27.15→27.57 vs 29.79; 37.23→38.29 vs 43.71) with
all-year net virtual ≈ 0 (off-peak neutral). **B alone closes roughly half
the top-150 gap** — the remainder is the offer-curve level at the depth the
market now reaches.

## 3. Lever A′ — the measured mid-curve floor (`pjm_offer_midcurve_conditional`)

`scripts/derive_pjm_offer_midcurve.py` + 
`fleet.build_pjm_offer_midcurve_conditional_markup`: within-unit
capacity-share sampling (shares 0.05-0.95) of the full measured offer
curves, per pjm-99 physics segment (+ the LONG_RUN coal/gas-steam block),
per delivery year and net-load bin; each model econ-tranche row's P1 bid is
floored at the measured level of its segment at the row's own within-plant
share (scale-free mapping — immune to the model-vs-measured segment
capacity mismatch). P1-only at the `mc_bid_adjust` seam (P0 run lengths
unperturbed — the pjm-99 econ-band caution); the floor only raises bids;
committed/must-run tranches and the coal cost basis stay owned by the
take-or-pay/passthrough sigmoids (rule 19). Disjoint row ownership: econ
(+ LONG_RUN peak) rows ← mid-curve; CC/CT peak rungs ← the frozen pjm-99
top surface; the two markups sum.

The derived surface itself sharpened the diagnosis: the measured mid-curve
body at shares ≤0.95 is moderate (CT_FAST ≈ $48-70, LONG_RUN ≈ $15-20 —
BELOW the model's coal, so the floor is a structural no-op on coal), and
the real $80-140 price formation lives in the top-share belt plus the
last-5% wall the pjm-99 surface prices. Hence the combination probe.

## 4. pjm-101 — the combination (B + top surface + mid-curve)

All three measured mechanisms engaged (128 virtual pseudo-units; 497
peak-rung rows repriced by the previously-inert pjm-99 top surface; 1,212
econ/long-run rows floored by the mid-curve):

| year | base top150 | pjm-100 (B) | **pjm-101** | actual | base all-LW | **pjm-101 all-LW** | actual |
|---|---|---|---|---|---|---|---|
| 2023 | $30.7 | $40.1 | **$48.8** | $76.2 | $28.47 | $30.74 | $29.33 |
| 2024 | $34.4 | $52.8 | **$60.6** | $82.8 | $27.15 | $29.98 | $29.79 |
| 2025 | $44.5 | $85.9 | **$102.4** | $136.2 | $37.23 | $41.81 | $43.71 |

Max prints: 2023 $48→$108 (actual $308), 2025 $81→$314 (actual $503).

**The endogenous-consistency check landed:** cleared net virtual depth fell
from B-alone's +9.9/+10.4/+11.2 GW to **+7.9/+8.3/+8.0 GW** — the properly
priced stack clears fewer DECs, converging on the measured +7-11 GW range
with nothing pinned. The pjm-99 top-of-curve wall, byte-identical-inert at
the old shallow margin, now binds (2025 max $314). The 2024 annual LW mean
is near-exact (+$0.19); 2025 improves by half; 2023 flips to a +$1.41
overshoot (baseline was −$0.86 under) — the one caveat, driven by the
mid-curve floor lifting shoulder-hour CT bids in the mild bins (a measured
level, not a window choice; rule 20 forbids re-gating it on this residual).

Roughly 55-60 % of the remaining top-150 gap closes. What remains is
concentrated in the extreme tail (actual maxes $200-500 vs model $108-314)
— consistent with the DA reserve/ORDC scarcity layer and the seam response
that this session did not touch.

## 5. Determination + the keeper-blocking limitation (INC phantom supply)

Both probes score **NOT-YET** (governance gate unattested — expected for a
probe; keeper decision is owner-only). The rubric movement vs the pjm-98
keeper, scored on the same-day basis:

| criterion | pjm-98 keeper | pjm-101 combo |
|---|---|---|
| **C3a mean LMP** | **FAIL** | **PASS** ← the G-22 target |
| C3b price shape | (FAIL) | PASS |
| C4 dispatch corr | PASS | PASS |
| C5a CO2 | PASS | PASS |
| C1 fuel-mix | PASS | **FAIL** (new) |
| C8 forced-share | FAIL (ST_GAS .70/.76/.51) | FAIL but **improved** (.33/.37) |

The lever pair does exactly what G-22 asked — it repairs mean-price
formation — but introduces one **real** regression: **C1 CT_PEAKER volume
−12.3 / −13.5 TWh (2023/24)**. Root cause: the DA virtual layer models
INCrement offers as physical LP supply (56 TWh cleared in 2024 as
fuel-type `import`), and that cheap phantom supply **displaces real peaker
generation** in the energy balance. An INC is a *financial* position — it
should deepen the DA price stack without producing physical MWh. The DEC
(virtual demand) side is clean (real units serve the added depth); the INC
side is not.

**The keeper-path fix** (next iteration, not this session — an
architectural change needs its own solve + validation): model the virtual
layer as a **net** DA-demand adder (`DEC(p) − INC(p)` per hour, an
export-sink-form demand curve only) rather than separate INC supply + DEC
demand — the +7-11 GW net at peaks is almost all DEC, so the depth effect on
price is preserved while no phantom supply enters the physical mix.
Alternatively, tag the virtual pseudo-units with a non-physical fuel_type
excluded from the generation-mix reconcile. Either keeps C3a's gain while
restoring C1.

**Recommendation to owner:** keep pjm-98 as the keeper; the lever pair is
structurally validated (it fixes the price formation G-22 targeted, with
zero fitted scalars and fully measured inputs) but the INC formulation must
be reworked to the net-demand form before promotion. Both probes and the
ablation twin are registered.

## 6. pjm-102 — the net-demand fix (INC phantom supply removed)

**Date:** 2026-07-12. **Run:** `2026-07-12-pjm-102-net-virtual`
(`results/calibration/pjm102_net_virtual_bids`). Baseline:
`pjm98_baseline_20260712`. **Determination: REJECT** — the fix is
structurally correct, but the combination it was meant to unblock is not
promotable, and for a *second* reason the §5 analysis did not anticipate.

**The fix worked.** `build_pjm_da_virtual_units` was rebuilt to the single
per-hour NET virtual-demand curve `net(λ) = Σ DEC≥λ − Σ INC≤λ`, rendered
entirely as DEC-form withdrawal blocks (each submitted price point → a
combined `dec+inc` block at its price; the lowest-priced `Σdec` MW kept, the
net-negative tail clamped to zero). **INC cleared 0 GW in all three years**
(vs pjm-101's ~56 TWh of fuel-type-`import` generation), while the net cleared
depth held at **+7.8 / +8.3 / +8.1 GW** at the top-150 hours — squarely in the
measured +7-11 GW band. No phantom supply enters the physical mix. This is the
correct, real mechanism form and should replace the separate-INC construction
in any future virtual-bid work.

**But the combo (net + top surface + mid-curve) fails on BOTH load-bearing
price/mix criteria** (calibration_verdict, rubric 2.4):

| criterion | pjm-101 (INC form) | **pjm-102 (net form)** |
|---|---|---|
| C3a mean LMP | PASS* | **FAIL** (2023 +12.4 %) |
| C1 fuel-mix | FAIL | **FAIL** (CT_PEAKER −10.9/−12.1 TWh) |
| C4 / C5a | PASS | PASS |

1. **C1 does NOT recover — a different root cause than §5 named.** With INC=0
   there is no phantom supply, yet CT_PEAKER is still −10.9/−12.1 TWh
   (2023/24) and CC_REGULAR is +8.3 TWh (2024), both out of band vs actual
   (actual CT_PEAKER 2024 = 24.0 TWh, baseline 23.0 ≈ exact, pjm-102 11.9).
   The added net demand is absorbed by **CC_REGULAR, not peakers**, because
   the **offer surfaces raise the peaker offers** above CC in the depth region
   — a merit reshuffle. The §5 diagnosis ("C1 fails because INC injects
   supply") was only half the story; the surfaces carry their own C1 cost.
2. **C3a REGRESSES from pass to fail — pjm-101's C3a "PASS" was partly
   spurious.** The cheap INC injection in pjm-101 was doing double duty: it
   displaced peakers (the C1 regression) AND it suppressed average prices
   toward actual (the C3a "gain"). Removing the non-physical supply (rule 1)
   removes the price suppression too, so the honest mean LMP now overshoots
   (2023 +12.4 %). The G-22 mean-price target was, in part, being met through
   a mechanism that isn't real — exactly what rule 1 forbids.

**Net-only control** (`pjm102b_net_only`, net virtual bids, no surfaces) —
isolates the net mechanism from the surfaces:

_Solving; results and the CT_PEAKER isolation land in a follow-up commit._

**Recommendation to owner (updated):** keep **pjm-98** as the keeper. The
net-demand form is the correct mechanism and is now the committed form of
`pjm_da_virtual_bids`, but the G-22 price-formation target is **not** met by
the net + surfaces combo: the pjm-101 C3a pass was partly an artifact of the
INC phantom supply, and the offer surfaces over-displace peakers vs actual.
The remaining gap is the DA reserve/ORDC scarcity tail and seam response (the
extreme-tail maxes of §4), not more offer-surface level. pjm-102 and the
net-only control are registered as rejects.

## 5. Discipline

- Rules 13/20/21: every input is a submitted ex-ante measured quantity
  (bids/offers), frozen against residuals, zero fitted scalars in any
  delta; clearing prices touched only for validation.
- Rule 15/16: all probes registered (keeper or rejected), all three years
  in one bundle each.
- Raw DataMiner2 feeds stay gitignored (redistribution restriction); only
  normalized-multiplier JSONs are committed.
- Keeper decision is owner-only; this session registers the runs and
  flags the recommendation.

## Reproduction

- Baseline: `python scripts/replay_keeper.py results/calibration/pjm98_cc_mustrun
  --out-dir results/calibration/pjm98_baseline_20260712` (throwaway).
- Sweep: `python scripts/probes/_g22_depth_price_sweep.py
  results/calibration/pjm98_baseline_20260712`.
- B probe: `python scripts/probes/_pjm100_da_virtual_bids_probe.py`.
- Combo: `python scripts/probes/_pjm100_da_virtual_bids_probe.py
  --with-offer-surface --with-midcurve --out-dir
  results/calibration/pjm101_depth_surfaces`.
- Compare: `python scripts/probes/_g22_ab_compare.py <baseline> <probe>`.
- Raw feeds: `scripts/fetch_pjm_da_virtuals.py` (~15 min),
  `scripts/fetch_pjm_energy_offers.py` (~40 min, 3 parallel year jobs,
  never concurrent with a solve).
- ENV: 15 GB box — create the 10 GB swapfile first; solves alone, years
  sequential; `git push` needs `http.postBuffer` raised (the proxy rejects
  chunked uploads).
