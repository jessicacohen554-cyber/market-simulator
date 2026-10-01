# FINDING — C1 candidate 3 (overnight CC cycling): evidence measured, build direction identified, tension disclosed (no build this session)

**Session 2026-07-16 (C1 lane, chartered candidate 3). No LP. Basis: the
same-machine caiso-90 keeper repro (`caiso90_citygate_flow_date` bundle) vs
full-8760 CAMPD CEMS grids with the LA-Basin repowering ORISPL crosswalk
(CEMS 315/335/330 ↔ EIA 62115 Alamitos EC / 62116 Huntington Beach EC /
57901 El Segundo EC — without it, ~1.6 TWh/yr of the naive overnight delta
is phantom "missing" CEMS. Desert Star 55077 is in Nevada, outside the CA
extract: ~0.2-0.3 TWh/yr of model overnight CC is CEMS-uncoverable here).**

## 1. The measured overnight (hod 0-5) CC over-run

| year | CEMS TWh | model TWh | Δ | at binding min_gen floors |
|---|---|---|---|---|
| 2023 | 13.77 | 15.08 | +1.30 | — |
| 2024 | 12.65 | 14.72 | +2.07 | **0.16 TWh (mechanism 7 = RA bridge)** |
| 2025 | 11.17 | 13.70 | +2.53 | — |

≥ 92 % of the model's overnight CC is FREE economic dispatch — the RA
bridge owns almost none of the over-run on this same-machine basis (the
earlier "~a third" attribution was computed pre-crosswalk on a different
run line). Per-plant: real CAISO CCs two-shift — overnight-online 26-67 %
(Palomar 26 %, Russell City 37 %, Delta/Mountainview 53 %, Moss Landing
64 %, Otay Mesa 67 %) vs the model's 50-100 % (Moss Landing 98 %).

## 2. The hour-of-day price ladder (the lane's sharpest new fact)

Demand-weighted model λ minus actual RT (hub series), by hod block:

| year | overnight 0-5 | belly 10-14 | evening 17-21 |
|---|---|---|---|
| 2023 | +4.3 | **+13.8** | **−3.9** |
| 2024 | +2.2 | **+11.1** | **−2.9** |
| 2025 | +4.1 | **+9.1** | **−0.8** |

The C3a annual body overprice (+11.5/+15.2 %) is a BELLY phenomenon
(+$9-14/MWh at hod 10-14) partly offset by an evening UNDERPRICE
(−$1-4 at hod 17-21). The evening underprice is the price-side face of the
C1 CT under-run (the class's summer-evening trio clears in reality at
evening λ the model does not reach), and the C3c summer tail misses sit on
its extreme. The belly overprice is the known open midday/RUC-long lane
(caiso-51 next-lever list), not this lane.

## 3. Candidate 3's design fork and disclosed tension

The chartered idea ("CC min-down/cycling commitment economics — the
ERCOT-63 committed-STATE lesson in reverse") means a P1-native overnight
TWO-SHIFT screen: de-commit CC plant-nights whose P0-dual overnight margin
is below the avoided-start cost (startup-restart inequality at the model's
own P0 duals — forward-regenerating, rules 11/13). The physics gap is real:
the perfect-foresight LP rides CC through marginal overnights that real
day-ahead schedulers shut down (26-67 % measured overnight-online).

Disclosed tensions, ahead of any build (rule 1 honesty):

1. **Direction on prices:** removing overnight CC RAISES overnight λ, which
   is already +$2-4 OVER. Unless the displaced ~1.3-2.5 TWh is served by
   cheaper overnight imports (real overnight West is surplus; the model may
   under-import overnight — not yet decomposed), the fix worsens the
   overnight price residual while fixing the volume.
2. **Doctrine:** an economic de-commit screen is the archived-P2 family
   (`commitment_enabled` decommit; ARCHIVED, never a calibration option).
   A new P1-native variant is a fresh mechanism, but the design must not
   become P2-by-another-name; the ERCOT-63 precedent (bridge, not decommit;
   one DA operating day; measured state parameters) is the template that
   passed review.
3. **Who serves the night** is unmeasured: the model-vs-measured overnight
   import/CT/hydro split needs the EIA-930 overnight interchange
   decomposition before the mechanism's displaced-energy story is grounded.

## 4. Disposition

Candidate 3 stays OPEN — evidence quantified, no build this session. With
candidates 1 (caiso-91 probe: online-scoped reserve co-opt, measured inert)
and 2 (committed-tranche gate: refuted on measured conduct, no-LP) both
closed, the C1 lane state is: candidate 3 (this finding) + the two named
admissible routes — the measured DAM offer-surface intake (Panoche's
$5-10 bid wedge and the class econ rungs; own charter) and the
evening-merit λ level (the −$1-4 evening underprice, same defect as the
C3c summer remainder). Owner checkpoint before further solves.
