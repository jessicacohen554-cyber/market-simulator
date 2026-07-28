# FINDING — pjm-136: **the model's PJM has no dual structure at all on any Dominion-facing boundary — it separates in 0.00 % of 26,280 hours where PJM separates in 100.00 % — and the missing mechanism is not a flow limit. It is LOSSES.** Every internal PJM link is lossless with `flow_cost = 0`, so two zones joined by an uncongested path clear at the identical dual **by construction**; PJM's own day-ahead prices carry a marginal-loss component that separates zones in **every hour without any constraint binding**, worth **$0.54 / $1.06 / $1.90 /MWh** on DOM-vs-AEP alone, on a **sign-stable** gradient (Dominion positive 12/12 months, SWMAAC 12/12, ComEd negative 12/12).

**All three measurements were run; no LP was solved for them.** Probes:
`scripts/probes/_pjm136_zonal_dual_structure.py` (M2/M3 on the twelve published
hubs — committed data only),
`scripts/probes/_pjm136_model_vs_measured_zonal.py` (M1a/M1b/M2b on all eight
model zones). Machine output: `results/probes/pjm136_zonal_dual_structure.json`,
`results/probes/pjm136_model_vs_measured_zonal.json`. Inputs are the committed
`pjm135_netpos_keeper_C` `hourly/` sidecars, the committed hub LMP file, the
committed metered zonal load, and the pjm-136 zonal LMP-component intake.

---

## §0 — the verdict in one table

| test | question | result | fires? |
|---|---|---|---|
| **M1a** what binds in the MODEL | which internal link would have to bind for Dominion's dual to move? | **NONE PRICES.** The keeper separates on `AEP_Ohio→Dominion`, `West_APS→Dominion` and `SWMAAC→Dominion` in **0.0 % of all 26,280 hours**, and (§1a, flow space) `AEP_Ohio→Dominion` is **pinned at its bound in 84–91 %** of them at a shadow price of **exactly 0.000** — bound-but-priceless, not slack. All eight zones sit at ONE dual in **96.4 / 97.6 / 97.0 %** of hours; exactly one internal link ever carries a nonzero dual (`ComEd→AEP_Ohio`, 0.35 % of 2025) | **YES — and it kills the flow-limit family** |
| **M1b** what PJM does | how often does PJM separate on those same boundaries? | **100.0 % of hours, every link, every year.** Mean max zonal spread **$16.83 / $18.06 / $29.64** against the model's **$0.29 / $0.63 / $0.97** | **YES** |
| **M2** the losses question | how much of the separation needs no binding constraint? | the loss component carries **20 / 24 / 23 %** of the mean DOM−AEP-DAYTON gap and **exceeds $1 on its own in 24 / 33 / 54 %** of hours. Per-zone deviations are **sign-stable across all 12 months** and derive to an offline acceptance of **12/12 pair-years in [0.5×, 1.5×]** (ratios 0.95–1.07) | **YES — the delta** |
| **M3** topology adequacy | can an 8-zone reduction carry Dominion's congestion, or does it live inside a zone? | **it can.** Intra-zone hub spread is **$0.25–$1.70** mean \|Δ\| inside ComEd and AEP_Ohio against an inter-zone DOM-vs-AEP **$3.02 / $3.88 / $6.57**. (EMAAC is the exception — EASTERN vs NEW JERSEY runs **$4.3–$5.0**, a real sub-zonal limitation, but it is not the Dominion defect) | **NO — does not block** |

---

## §1 — M1a: the model has no congestion on any Dominion boundary, so no flow lever can reach it

The LP is lossless with `flow_cost = 0` on every PJM link, so model price
separation **is** the statement "the path between them binds"
(`_pjm134_c2_dominion_interface.py`'s identity). Read off the keeper's own P1
duals, per model link, share of hours the two ends differ at all:

| model link | MODEL separates | MEASURED separates | measured mean Δ (2025) | of which congestion | of which **loss** |
|---|---|---|---|---|---|
| ComEd→AEP_Ohio | 0.0 / 0.2 / 0.4 % | **100.0 %** | −9.06 | −7.12 | **−1.94** |
| AEP_Ohio→ATSI | 0.0 / 0.0 / 0.0 % | **100.0 %** | −0.15 | +0.51 | −0.66 |
| **AEP_Ohio→Dominion** | **0.0 / 0.0 / 0.0 %** | **100.0 %** | **−14.34** | −12.44 | **−1.90** |
| AEP_Ohio→West_APS | 0.0 / 0.0 / 0.0 % | **100.0 %** | −1.24 | −0.39 | −0.85 |
| ATSI→Central_PA | 0.0 / 0.0 / 0.0 % | **100.0 %** | +1.85 | +1.45 | +0.41 |
| West_APS→Central_PA | 0.0 / 0.0 / 0.0 % | **100.0 %** | +2.94 | +2.34 | +0.60 |
| West_APS→SWMAAC | 0.0 / 0.0 / 0.0 % | **100.0 %** | −10.09 | −8.34 | −1.75 |
| **West_APS→Dominion** | **0.0 / 0.0 / 0.0 %** | **100.0 %** | **−13.10** | −12.05 | **−1.05** |
| Central_PA→EMAAC | 0.0 / 2.3 / 2.7 % | **100.0 %** | +1.75 | +2.65 | −0.90 |
| SWMAAC→EMAAC | 0.0 / 2.3 / 2.7 % | **100.0 %** | +14.79 | +13.33 | +1.45 |
| **SWMAAC→Dominion** | **0.0 / 0.0 / 0.0 %** | **100.0 %** | **−3.01** | −3.71 | +0.70 |

(Sign convention: `zone_a − zone_b`, so a negative entry means **Dominion is the
dearer end**.)

**This is the load-bearing result, and it settles the lever family.** pjm-134
tried tightening a Dominion-facing flow limit (AP-South) and the mesh re-routed;
pjm-135 measured the star node price-tied to every zone at max |Δ| = 0.0000 and
closed the per-border lever. M1a says why both were doomed and why any successor
in that family would be. A mechanism that separates duals **without requiring a
constraint to price** is the only kind that can reach this defect.

### §1a — the flow-space half of M1: the links are **bound-but-priceless**, not slack

The dual-space table above was read from the committed sidecars before any
solve. The charter also asked for the flow-space reading — per-link utilisation
against the hourly limit — which needs a solved bundle. Run on arm A's own
`hourly/network_<year>.parquet` (the sidecar that carries `dual` and
`limit_up`; the bundle-level `flows.parquet` carries neither):

| arm-A internal link | median utilisation | hours **at** the bound | hours with a **nonzero dual** | max \|dual\| |
|---|---|---|---|---|
| **AEP_Ohio→Dominion** | **1.000 / 1.000** | **84.44 % / 90.73 %** | **0.00 % / 0.00 %** | **0.000 / 0.000** |
| **SWMAAC→Dominion** | **1.000 / 1.000** | **68.45 % / 80.50 %** | **0.00 % / 0.00 %** | **0.000 / 0.000** |
| West_APS→Central_PA | 1.000 / 1.000 | 61.51 % / 64.35 % | 0.00 % / 0.00 % | 0.000 / 0.000 |
| ATSI→Central_PA | 0.923 / 0.807 | 38.15 % / 29.57 % | 0.00 % / 0.00 % | 0.000 / 0.000 |
| West_APS→Dominion | 0.763 / 0.627 | 33.86 % / 26.34 % | 0.00 % / 0.00 % | 0.000 / 0.000 |
| ComEd→AEP_Ohio | 0.181 / 0.379 | 0.40 % / 0.48 % | 0.00 % / **0.35 %** | 0.000 / **21.073** |

(2023 / 2025; the remaining links are lower still.)

**This corrects a natural but wrong reading of §1 — including one this session
first wrote — that the Dominion-facing constraints are "slack."** They are not.
`AEP_Ohio→Dominion` is **pinned at its limit in 84–91 % of hours**, and
`SWMAAC→Dominion` in 68–81 %. What is zero is the **shadow price**, in every
hour of every year. The constraints are *weakly* active: the optimal face
contains points where the flow is below the bound, so the LP is indifferent to
the flow's value and no rent forms. In the whole 8-zone internal network, across
26,280 hours, exactly one link ever prices — `ComEd→AEP_Ohio` in 0.35 % of 2025.

This makes the flow-limit family's failure **stronger**, not weaker. Tightening
a limit that is already ridden and still prices at exactly zero cannot produce a
gradient — the simplex simply picks a different vertex on the same face at the
same cost, which is precisely the re-routing pjm-134 observed and pjm-135
measured. The degeneracy *is* the disease, and no re-parameterisation of a flow
bound treats it.

## §2 — M1b/M2: the loss component is exactly such a mechanism, and it is measured

PJM's ex-post LMP decomposes as `LMP_i = MEC + MCC_i + MLC_i` (Manual 11 §2 /
OATT Att. K), so for any two nodes

```
LMP_i − LMP_j = (MCC_i − MCC_j) + (MLC_i − MLC_j)
```

`MCC` needs a constraint to bind. `MLC` does not — it is a network-physics
gradient present in every hour. On the published hubs (DOMINION vs AEP-DAYTON,
day-ahead):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| mean spread | **+2.713** | **+3.337** | **+5.749** |
| — congestion part | +2.167 | +2.533 | +4.414 |
| — **loss part** | **+0.547** | **+0.804** | **+1.335** |
| loss share of the mean | **20.1 %** | **24.1 %** | **23.2 %** |
| hours the **loss part alone** exceeds $1 | **24.1 %** | **32.6 %** | **54.4 %** |
| hours the loss part alone makes Dominion dearer | 78.9 % | 80.3 % | 75.5 % |

The zonal record (all 21 PJM transmission zones, load-weighted onto the eight
model zones through the canonical `_PJM_LOAD_ZONE_GROUPS` crosswalk) gives the
dimensionless deviation `dev_z = Σ MLC_z / Σ MEC` — the object a loss surface
consumes:

| model zone | 2023 | 2024 | 2025 | months positive (2023) |
|---|---|---|---|---|
| PJM_SWMAAC | **+0.0325** | **+0.0421** | **+0.0437** | 12/12 |
| PJM_Dominion | **+0.0244** | **+0.0266** | **+0.0287** | **12/12** |
| PJM_EMAAC | −0.0035 | +0.0135 | +0.0128 | 5/12 |
| PJM_West_APS | +0.0004 | +0.0057 | +0.0065 | 6/12 |
| PJM_ATSI | +0.0018 | +0.0030 | +0.0023 | 7/12 |
| PJM_Central_PA | −0.0097 | −0.0032 | −0.0063 | 2/12 |
| PJM_AEP_Ohio | +0.0070 | −0.0070 | −0.0116 | 8/12 |
| PJM_ComEd | **−0.0364** | **−0.0535** | **−0.0528** | **0/12** |

This is PJM's textbook geography: the Illinois generation pocket is upstream, the
Mid-Atlantic and Dominion load pockets are downstream. **Dominion sits at the
dear end of the gradient in every month of every year** — the exact direction the
zonal inversion needs, and it exists in the model's own topology with zero
constraints binding.

**The sign stability is the pivotal contrast with the MISO precedent.**
`miso_zonal_loss_surface` is a REJECTED PROBE in MISO (miso-76), tripped by its
own pre-registered R2 on East-2025, where the East−Indiana monthly surface flips
sign **6/6 months** and a one-way monthly mechanism could not reproduce a
near-zero measured annual net produced by offsetting congestion. PJM's
Dominion-facing gradient does not cancel: it is one-signed all 12 months, and on
the DOM-vs-AEP boundary congestion and loss **reinforce** (both positive, all
three years) rather than offset. That is a per-ISO fact about PJM's network
(rule 25 `[R-ISO-SCOPE]`), measured here from PJM's own components — not a
verdict transferred across a market boundary.

## §3 — M3: the 8-zone reduction can carry it (with one disclosed exception)

PJM publishes several hubs **inside single model zones**, which gives a direct
read on whether the separation is inter-zonal (a zonal mechanism can carry it) or
sub-zonal (no zonal granularity can — the ERCOT/MISO `internal_congestion_split`
refusal). Mean |Δ| day-ahead:

| pair | inside | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| CHICAGO vs N ILLINOIS | ComEd | 0.25 | 0.36 | 0.51 |
| CHICAGO vs CHICAGO GEN | ComEd | 0.54 | 0.92 | 1.00 |
| AEP-DAYTON vs AEP GEN | AEP_Ohio | 0.73 | 1.08 | 1.70 |
| **DOMINION vs AEP-DAYTON** | **across zones** | **3.02** | **3.88** | **6.57** |
| EASTERN vs NEW JERSEY | **EMAAC** | **4.57** | **4.33** | **5.01** |

The Dominion boundary's separation is **4–12× the intra-zone spread of the zones
on either side of it**: it is a genuine inter-zonal quantity and the reduction
can express it. **Disclosed, not fixed here:** EMAAC hides an internal spread as
large as the inter-zonal one (>$1 in 36–45 % of hours), so any EMAAC-internal
congestion is beyond this topology. That is a separate limitation, not the
Dominion defect, and it is filed rather than acted on.

## §4 — the delta this charters

`ScenarioConfig.pjm_zonal_loss_surface` (new, default off, **zero DOF**): each
bidirectional PJM-internal link splits into a one-way pair and each direction's
receiving-end energy-balance coefficient becomes `1 − eps(month)`, with

```
eps_(x→y),m = max(0, (dev_y,m − dev_x,m) / (1 + dev_y,m))
```

so an interior uncongested flow `x → y` prices the receiving zone at
`λ_y = λ_x × (1 + dev_y,m)/(1 + dev_x,m)` — **exactly** the measured
delivery-factor ratio. Transported energy consumes MWh; **prices stay LP duals**
(rule 4 `[R-DUALS]`), never a price adder. The surface is the frozen derive
`scripts/data/derive_pjm_loss_surface.py` over PJM's own published per-zone MLC
record; the only non-measured device is the 0.001 $/MWh flow tiebreak (storage-ε
class, rule 9). Realised loss fractions on the keeper topology, 2025:
**ComEd→AEP_Ohio 4.16 %**, **AEP_Ohio→Dominion 3.81 %**, West_APS→SWMAAC 3.50 %,
West_APS→Dominion 2.14 %, Dominion→SWMAAC 1.39 % — with the reverse legs at
0.00–0.29 %.

Rule 19 `[R-ONE-MECH]`: this owns the **loss** component only. The congestion
component stays with the measured interface limits and the joint EAST / AP-South
/ net-position cuts, and **nothing is applied to the external star node** —
`PJM_external` is a fictitious pricing node with no published deviation, and
inventing one would be a fitted scalar (rule 5).

It is chartered **because it is structurally correct, not because it is predicted
to close the Dominion residual** (rule 1 `[R-STRUCT]`). The pre-registration
computes, before any solve, that the mechanism's whole reach on the
`AEP_Ohio→Dominion` boundary is a ~$1.8/MWh dual lift at the 2025 mean MEC —
against a Dominion `CT_PEAKER` gap of −7.2 TWh sitting far up the offer stack.
**INERT on the CT leg of the inversion is the expected, pre-registered,
publishable outcome.** Gates, kills, the no-feedback ceiling and the named
principal risks are in
`PREREG-pjm136-zonal-loss-surface-2026-07-28.md`, committed before either arm
solved.

## §5 — DO-NOT-REDO (binding on successors)

- **Do not propose another PJM internal flow-limit lever against the Dominion
  inversion.** §1/§1a measure every Dominion-facing link separating in **0.0 % of
  26,280 hours** while `AEP_Ohio→Dominion` is **pinned at its bound in 84–91 %**
  of them at a shadow price of **exactly 0.000**. The constraints are
  bound-but-priceless, so tightening one moves the simplex to another vertex on
  the same zero-cost face instead of creating rent. This generalises pjm-134 §8
  (AP-South) and pjm-135 §7 (the star node) from "the mesh re-routes" to the
  reason it can: **no internal PJM boundary carries a nonzero dual at all**,
  except `ComEd→AEP_Ohio` in 0.35 % of 2025.
- **Do not re-open the 8-zone topology for the Dominion boundary.** §3 measures
  the DOM-vs-AEP separation at 4–12× the intra-zone spread of either neighbour:
  the reduction can carry it. (EMAAC is a *different*, disclosed sub-zonal
  limitation — a separate charter, not this one.)
- **Do not transfer MISO's `miso_zonal_loss_surface` verdict onto PJM, in either
  direction** (rule 25). MISO's R2 trip is a fact about a *cancelling* MISO
  pair-year; PJM's cell is decided by PJM's own A/B on PJM's own surface. The
  same applies in reverse: whatever PJM's result, MISO's REJECTED-PROBE verdict
  stands unless MISO re-tests it.
- **Do not sweep, scale, haircut or blend the delivery-factor surface** in
  response to any result (PREREG §4 no-feedback ceiling). It is a measured
  physical quantity, not a knob.
- Carried forward unchanged: `FINDING-pjm134` §5/§8 and `FINDING-pjm135` §7 in
  full.

**Handover leads, stated but NOT built here** (ASK-pjm134 §5 discipline):

1. **EMAAC's sub-zonal congestion** (§3): EASTERN vs NEW JERSEY runs $4.3–$5.0
   mean |Δ|, >$1 in 36–45 % of hours, *inside* one model zone. No zonal
   mechanism can reach it; it needs either a topology split or an explicit
   representation-boundary disclosure. Not a Dominion charter.
2. **The star node is lossless by construction** (§4): seam-sourced energy is
   delivered to a border zone with no loss while internally-wheeled energy pays
   one, which makes external imports *relatively* cheaper under this mechanism.
   Bounded by the pjm-135 net-position cut and the per-border envelopes, and
   pre-registered as kill K3, but it is a real representation asymmetry and it is
   disclosed rather than buried.
3. Carried from pjm-135, still open: the `_PJM_TIE_ZONE` / `INTERFACE_NEIGHBORS`
   TVA disagreement, and PJM `CC_CHP` running +42 %.
