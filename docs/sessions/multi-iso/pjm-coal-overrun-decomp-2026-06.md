# PJM coal over-run — probe #0 decomposition + lever audit (2026-06)

**Date:** 2026-06-22. **Keeper:** `results/calibration/pjm_38` (dashboard
`pjm 38 outage regate`), reproduced byte-faithfully this session (coal-tot resid
+17.3 / +13.9 / +22.8%, COAL_BIT +16.8 / +13.4 / +21.9%, gas +4.9 / +5.7 / +3.7%,
net-export +69 / +65 / +204%, LMP −1.1 / −11.4 / −19.3%, 11 in-tolerance fails —
matches the handoff). **Status: negative result.** Neither proposed coal lever
(A export seam, B marginal coal offer) is the structurally-faithful fix; the
over-run is downstream of PJM's *own* suppressed model LMP, a gas-marginal /
missing-afternoon-scarcity price-formation problem, not coal cost or the seam.

Probes (no new keeper):
`scripts/probes/_pjm_coal_decomp.py` (#0, no solve) +
`scripts/validate_neighbor_price.py` (seam audit, no solve) +
`scripts/probes/_pjm_coalbit_passthrough_run.py` (#2, 2024 one-year solve).

## Probe #0 — the over-run is EXPORT-driven, and the export rides cheap base coal

Within the model, load is fixed, so `Σ(Δfuel) == Δnet-export` exactly. Model−actual
(TWh):

| year | Δcoal | Δgas | Δnet-export | export/thermal | coal over: base vs marginal |
|---|---|---|---|---|---|
| 2023 | +20.99 | +16.96 | +27.64 | 73% | 93% base (mustrun+committed), 7% econ/peak |
| 2024 | +17.04 | +20.07 | +21.30 | 57% | 94% base, 6% marginal |
| 2025 | +33.30 | +13.09 | +36.62 | 79% | 92% base, 8% marginal |

- **Both coal AND gas are over** while nuclear/wind/solar match (±2 TWh). So the
  extra coal is **not displacing domestic gas** — coal *and* gas both rise to feed
  a 3×-too-large net export (model 54–68 TWh/yr vs measured 18–40). The over-run
  leaves PJM.
- The coal over is **~92–94% in the take-or-pay BASE tranches** (must-run +
  committed), only 6–8% in the marginal econ/peak band. A base-coal over-run
  cannot be removed by re-pricing the marginal tranche.
- In export-heavy (top-tercile) hours the LMP is **below** the annual mean
  ($26 / $24 / $29 vs $27 / $25 / $33) while coal runs at 17–21 GW: cheap base
  coal floods the stack and exports at a suppressed price. `corr(coal MW, LMP)`
  +0.75–0.79 (coal follows price/load); `corr(coal MW, net-export)` ≈ 0.

## Lever A (export seam) — REFUTED: the seam is sound; the over-export is a
## symptom of PJM's own low LMP

`scripts/validate_neighbor_price.py` scores the forecast-grade seam against
measured data **using PJM's ACTUAL LMP** (isolating the seam from the model's
price suppression):

| year | actual PJM LMP | neighbor agg | measured export-share | seam predicted | dir hit-rate |
|---|---|---|---|---|---|
| 2023 | $28.44 | $35.72 | 0.98 | 0.78 | 0.79 |
| 2024 | $29.53 | $31.11 | 0.96 | 0.64 | 0.66 |
| 2025 | $42.89 | $40.28 | 0.95 | 0.58 | 0.59 |

- PJM is a **structural net exporter in 95–98% of hours** in reality (+40 / +33 /
  +18 TWh). Fed PJM's *actual* LMP, the spread-based seam **under-predicts** export
  (predicted export-share < measured; hit-rate 0.59–0.79) — it is **not
  over-aggressive**. In 2025 actual PJM ($42.89) is *above* the neighbor aggregate
  ($40.28), so on actual prices the seam would barely export.
- The model over-exports 3× **only because its own LMP is ~$8–10 too low**
  ($33 model vs $42.89 actual, 2025). The suppressed PJM price inflates the
  export spread, which pulls cheap base coal across the border.
- Therefore tightening the seam (raising the hurdle / lowering the neighbor heat
  rates) would be **un-anchored curve-fitting to the net-MWh target** on a
  validated-sound construction, **and** it would pull PJM demand down and push the
  already-too-low LMP *further* under actual. Lever A is rejected.

## Lever B (marginal coal offer) — measured room exists but is structurally
## BOUNDED; cannot clean the gate

Anchor check (2024, measured): delivered bituminous cost **$3.03/MMBtu**
(EIA-923, qty-wtd, 16 reporting plants). The model's COAL_BIT **sole-marginal**
clearing LMP is **~$29** (p50 $29.4) — an implied heat rate ~9.6 before VOM,
*below* the physical ~10.5 BIT heat rate. So the marginal coal offer does bid
~$6–7/MWh under its full delivered variable cost (the `coal_bit_passthrough_floor`
= 0.76 discount). There is honest, measured-anchored room to raise it.

But probe #0 bounds the effect: coal is the **SOLE price-setter in only
2.6 / 8.6 / 5.1%** of load-weighted zone-hours (gas is co-marginal in ~50% and
the sole setter in ~36–43%). Where gas is co-marginal it simply refills at the
same price when coal is raised, so the LMP does **not** move; and the over is
~92% take-or-pay base, which the guardrails keep cheap.

**Probe #2 (2024, `coal_bit_passthrough_floor` 0.76→1.0 — full measured
delivered-cost passthrough on the above-must-run tranches, base untouched):**

| 2024 metric | keeper (floor 0.76) | probe (floor 1.0) |
|---|---|---|
| COAL_BIT | +13.4% **FAIL** | +1.6% **PASS** |
| coal-tot | +13.9% **FAIL** | +3.6% **PASS** |
| gas | +5.7% FAIL | +7.8% **FAIL (worse)** |
| net-export (info) | +65.2% | +50.2% |
| LMP (info) | −11.4% | −9.6% (+$0.5) |
| in-tolerance fails | 5 | 2 |

The full-cost passthrough backs **~13 TWh** of committed/marginal coal out of the
stack (COAL_BIT and coal-tot flip to PASS), but **~7 TWh of it is replaced by
domestic gas** (gas over *deepens*, +5.7→+7.8%), net export falls only ~5 TWh
(+65→+50%), and the LMP lifts just **+$0.5** (still −9.6%). It is a **coal→gas
relabel**, not a fix: the dominant over-export and LMP-under are essentially
intact, exactly as probe #0 predicted (coal sole price-setter ~9% of 2024
zone-hours; gas refills at the same price). The fewer "fails" is a fuel-mix
reshuffle that deepens the gas miss, not a structural improvement — and
floor=1.0 strips the deliberate take-or-pay discount off the *committed* base
(which real plants hold through cheap gas), so it is not clearly more faithful.
**Not promotable** (does not gate clean; not the structural fix).

## Reading & recommendation

The coal over-run and over-export are **one defect, and it is upstream of coal
cost**: PJM's modeled LMP clears ~$8–10 below actual, which (a) inflates the
export spread → 3× over-export, dragging cheap base coal up, and (b) is itself
the dashboard LMP miss. The price is set by **gas** in ~90% of hours (gas
co-marginal/sole), so the suppression is a **gas-marginal / missing
afternoon-scarcity** problem — the empty $75–200 regime documented in
`pjm-lmp-residual.md` — not a coal-cost or seam fault.

- **Do not** tighten the export seam (lever A): un-anchored on a validated-sound
  construction and worsens the LMP-under.
- **Lever B** has a small measured-anchored bite (full delivered-cost passthrough
  on the marginal/committed coal), but it is structurally bounded (see probe #2)
  and cannot remove a base-driven, export-driven over-run. Not promotable as the
  coal-over fix on its own.
- **The frontier is price formation** (gas-marginal offer body / reserve-scarcity
  pricing — the parked `pjm-reserve-ordc` / `derive_dam_offer_hrmults` lever C):
  lift PJM's afternoon clearing price toward actual and the export spread —
  hence the over-export and the cheap-coal-over — collapses with it. That is the
  next structurally-honest lever, not coal cost.

## Reproduce

```bash
# keeper (one year each, MEMORY: one at a time — 2 concurrent OOMs a 15 GB box;
# do NOT run pandas probes while a solve is live)
python scripts/probes/_pjm_retiree_run.py 2023 results/calibration/pjm_38_y2023
python scripts/probes/_pjm_retiree_run.py 2024 results/calibration/pjm_38_y2024
python scripts/probes/_pjm_retiree_run.py 2025 results/calibration/pjm_38_y2025
python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_38 \
    results/calibration/pjm_38_y202{3,4,5}
python scripts/probes/_pjm_score.py pjm_38

# decomposition + seam audit (no solve)
python scripts/probes/_pjm_coal_decomp.py pjm_38
python scripts/validate_neighbor_price.py --iso PJM --years 2023 2024 2025

# lever-B probe (one year)
python scripts/probes/_pjm_coalbit_passthrough_run.py 2024 results/calibration/pjm_b1_2024
python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_b1 results/calibration/pjm_b1_2024
python scripts/probes/_pjm_score.py pjm_b1
```
