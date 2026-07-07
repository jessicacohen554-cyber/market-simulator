# PJM 85 — commitment-scoped reserve supply (G-20b path B)

**Probe (not a keeper). Keeper stays pjm-83-srmc-reground.** Full span
2023–2025, one bundle, years sequential. Branch
`claude/pjm-g20b-path-b-w2a`. Solved on the freshly regenerated `data/clean`
tree (fresh container) — the 26,280-hour run hit the corrupted-demand fallback
**0 times** (the demand-profile clean partition was regenerated first).

## What was run

pjm-83 keeper recipe **verbatim** + the path-B reserve-supply scoping the
pjm-84 verdict demanded (`SUMMARY-g20b.md`: "PATH B REQUIRED — scope the
~39 GW deliverable cap down to the ~10 GW PJM actually has synchronized, via a
commitment-derived availability screen"):

- `pjm_reserve_commitment_scoped=True` (**new**) — the fa_p2-style availability
  mask, made P1-native (P2 is archived). The P0 base-cost run pattern defines
  each PLANT's online hours; non-fast-start reserve-eligible units (rule-18
  physics gate — plant capacity-weighted min-down > 2 h or startup ≥ $30/MW,
  the same NREL class-table thresholds `_posture_pool_params` uses) have
  availability zeroed in their plant's P0-offline hours before the single
  scored P1 solve; offline gaps shorter than the plant's min-down are bridged
  online. Fast-start units are never masked (rule 18 — an offline 10-min
  CT/oil peaker still provides non-synchronized Primary reserve, Manual 11
  sec 4.2). The `pjm_reserve_supply_cap` deliverable ramp cap is recomputed on
  the masked fleet. Mechanism at `pipeline.commitment.build_pjm_reserve_p1_prep`,
  wired at the P0→P1 seam (`pipeline.solve.run_energy_solve`).
- `measured_ramp_capability=True` (kept from pjm-84, rule 14).

Published two-step ORDC ($850/$300/+190 MW) unchanged — no breakpoint/penalty
edit (rule 11). No MIP; P1 stays the scored pass.

## Result — structurally-faithful NON-FIRE (same verdict as path A, new reason)

| metric | 2023 | 2024 | 2025 |
|---|---|---|---|
| reserve dual > 0 (h) | **0** | **0** | **0** |
| demand-wtd RTO LMP: mean $ | 28.98 | 27.24 | 37.16 |
| max LMP $ | 57.5 | 138.7 | 134.4 |
| LMP > $200 (h) — model | **0** | **0** | **0** |
| LMP > $75 (h) — model | 0 | 9 | 17 |
| measured Primary req (mean MW) | 3094 | 3422 | 3348 |
| design deliverable cap (mean MW) | 38 793 | 39 325 | 39 213 |
| **masked** deliverable cap (mean/min MW) | — | 36 842 / 29 676 | — |
| fast-start CT/oil ramp10 alone (mean/min MW) | — | 17 693 / 17 024 | — |

**The reserve requirement never binds — reserve dual $0 in all 26,280 hours**,
identical verdict to pjm-84 (path A) but for a distinct, newly-identified
reason.

## Why path B also does not fire (the mechanism, quantified)

The commitment mask works as designed — it fires (P1 cold-solves on the masked
fleet) and zeroes idle slow-start capacity — but it **cannot** thin the LP's
reserve supply below the requirement, for two compounding reasons:

1. **Idle slow capacity was already ~0 in the online supply.** The mask zeroes
   non-fast-start units whose *plant* is offline in P0. But an offline plant's
   units already contribute no *online* headroom, so removing them barely
   moves the deliverable supply: the tightest-hour online+10-min-deliverable
   measure is **2 303 MW (masked) vs 2 310 MW (unmasked)** in 2023 — a 7 MW
   difference. The mask and the online-gate are near-redundant.

2. **Fast-start ramp capability alone exceeds the requirement ~5×.** PJM's
   fast-start (10-min-startable) CT/oil fleet is rule-18-exempt from the mask —
   correctly, because it supplies non-synchronized Primary reserve (Manual 11
   sec 4.2). Its 10-min deliverable ramp alone is **17 024 MW at the tightest
   hour** vs the ~3 422 MW Primary requirement. So the LP's supply cap, even
   recomputed on the masked fleet, stays at **36 842 MW mean / 29 676 MW min** —
   ~9–11× the requirement. No commitment-scoping of the *slow* fleet can close
   that gap.

The tightest *synchronized-only* measure (online plants ∧ 10-min ramp,
excluding idle fast-start) does dip below the requirement 526–751 h/yr (min
ratio 0.62–0.69×) — but (a) that measure is the **Synchronized** sub-product
(SR ⊆ Primary), not the **Primary** requirement the model scores against;
matching a synchronized supply to a Primary requirement would be structurally
wrong (rule 1), and (b) even if forced, those hours bind at the **penalty**
step ($300–850), which **overshoots** the $75–200 opportunity-cost band the
residual actually needs — exactly the `pjm-reserve-ordc.md` finding that the
band is opportunity-cost, not shortage.

## Verdict — path A, path B both confirm the G-20 diagnosis

Reserve **supply scoping cannot price PJM's afternoon residual**, whether by the
LP-linear online-gate proxy (path A / pjm-84) or the commitment-derived
availability mask (path B / pjm-85). The blocker is not reserve structure,
memory, ramp data, *or* commitment posture — it is that:

- PJM's Primary reserve requirement (~3.4 GW) is genuinely served by the
  fleet's abundant fast-start + online 10-min-deliverable capability
  (~17 GW fast-start alone), so the published vertical ORDC never engages; and
- the $75–200 residual is the sub-shortage **opportunity-cost** reserve price,
  which requires reserve to compete with energy on the **same marginal unit**
  (the per-gen `R[g] ≤ ramp10[g]` co-opt, `pjm-81`) — memory-heavy, and the
  commitment-posture lever the owner already struck (G-20b register note).

The honest outcome is a clean $0 — no breakpoint lowered, no penalty inflated,
no headroom offset netted (rule 11). Registered as a rejected probe (rule 15).

## No dispatch distortion from the reserve mechanism (rules 1/11)

Because the reserve dual is $0, the co-opt added zero reserve redispatch — the
reserve variables sit free without competing with energy. pjm-85's energy
dispatch is therefore the pjm-83 recipe's dispatch **on the current clean-data
tree**. The class-volume deltas vs the *committed* pjm-83 bundle (CC_CHP −4,
ST_CHP −2.8 TWh) are the **demand-profile clean-partition regeneration** (the
committed pjm-83 predates it and fell back to the corrupted legacy series),
**not** path B — provable because a $0 reserve dual cannot move energy
dispatch. A clean same-tree A/B (pjm-83 recipe with the flag off) would be
byte-comparable; it was not run because the reserve non-fire is data-tree
independent.

## #1484 (CT_PEAKER C8 drag share) — no reserve product to reconcile against

Path B produced no reserve product ($0 dual), so nothing was absorbed from the
drag (rule 19 reconciliation): the CT_PEAKER drag carries exactly what it did
in pjm-83. Re-measured from the committed `legitimacy_diagnostics.json` (D-2):
CT_PEAKER `ct_netload_drag` share **9.0 % / 14.6 % / 10.3 %** (2023/24/25) —
within rounding of pjm-83's 9.2 / 14.5 / 10.2 %, all under the rubric-v2.1
15 % peaker budget (D-2 PASS). D-4 clean for the drag (0 % off-window all
years); the only D-4 miss is the identical `reliability_floor × CT_PEAKER`
2023 0.0002 TWh aggregation artifact pjm-83 already carries. #1484 is
unchanged by path B and remains owned by the memory-gated per-gen
opportunity-cost mechanism.
