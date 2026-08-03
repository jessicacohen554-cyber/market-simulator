# PREREG pjm-148 — CHP host-steam holdout at PJM (`chp_btm_pct` / `chp_grid_pmin_mw` / `chp_steam` floor level)

**Committed and pushed BEFORE any measurement that decides a verdict** (the
pjm-144/146/147 protocol; the pjm-131 precedent for a no-LP screen). Keeper
under test: **`2026-08-03-pjm-147b-chp-heat`** (CALIBRATED 9/9, C1 16/16 ·
free 12/12, zero FAILs, zero caveats).

Charter lineage: `FINDING-pjm147-measured-chp-heat-rates-2026-08-03.md` §8 —
the named successor lane, reached independently of nyiso-105 from PJM's own
data (rule 25 `[R-ISO-SCOPE]`: NYISO's framing transfers nothing).

## 1. The defect this lane inherits

PJM CC_CHP runs over its measured actual on the grid-delivered basis C1 scores:

| year | model (keeper) | actual | miss |
|---|---|---|---|
| 2023 | 8.606 | 6.115 | **+2.491 TWh** |
| 2024 | 8.071 | 7.283 | +0.788 TWh |
| 2025 | 6.835 | 6.445 | +0.390 TWh |

pjm-147 measured the **offer** (eGRID's own steam-credited-rate add-back, and
it retired a hand factor). The residual is therefore a **quantity** question:
the host-steam holdout (`chp_btm_pct`, a grid-capacity pull-out) and the
`chp_steam` floor level (`chp_grid_pmin_mw`).

## 2. The direction constraint, declared before anything is measured

This is the single most important pre-commitment in this document, because it
is what stops a gap-shaped parameter from being reachable at all.

**PJM CC_CHP is OVER its actual in all three years.** Therefore:

* A **floor** (`chp_grid_pmin_mw` / `chp_steam`) can only push a class **UP**.
  Raising it, or newly creating one, is **wrong-signed** against a class
  already over. Any floor-*raising* mechanism is **DEAD ON DIRECTION**
  regardless of how well identified it is — including a WP-3 `steam_level_cf`
  derivation, which is a `max(level, p2)` swap and therefore raises by
  construction.
* Only a floor **reduction** or a grid-capacity **reduction** (a larger BTM
  holdout) can close the gap — and each requires its own mechanism to actually
  **bind**, which Q1/Q2 below test.
* **The neiso-71 kill applies verbatim**: a floor or share whose *size* is set
  by the 2.49 TWh gap is a fitted parameter, forbidden by rules 21 `[R-DOF]` /
  24 `[R-REGISTRY]`. **If the only identification available is gap-shaped, this
  session REFUSES and says so.** That is a complete outcome, not a failure.

## 3. Pre-registered screen (no LP spent; unmet-means-dead)

Every threshold below is fixed here and is never moved to chase a result.
Q2's threshold is **inherited unchanged** from pjm-131's committed charter.

| id | question | measurement | DEAD rule |
|---|---|---|---|
| **Q1** | Does the CC_CHP host-steam floor **bind** on the current keeper? | (a) committed D-2 `chp_steam` forced share for CC_CHP, all 3 yr; (b) an **independent** hourly reconstruction: share of CC_CHP class-hours where P1 dispatch ≤ (1 + tol) × the summed grid-facing floor, tol = 1 % | DEAD — "lowering an inert floor is a no-op" — if (a) < 1 % **and** (b) < 5 % in every year |
| **Q2** | Is CC_CHP **capacity-bound**, so a BTM pull-out could bind? | κ = share of CC_CHP P1 energy in hours at ≥ 99 % of hour-varying available grid capacity, all 3 yr (pjm-131's statistic, re-measured on the CURRENT keeper) | **REFUTED as a capacity/BTM lever** if κ ≤ 0.20 in every year (pjm-131 threshold, unchanged) |
| **Q3** | Does a **valid measured** per-plant BTM share exist for PJM? | re-audit the `chp-btm-share` artifact after curation: degeneracy rate (`btm_share == 1.0`), and CC_CHP capacity coverage | DEAD if degeneracy ≥ 90 % of PJM rows **or** covered CC_CHP capacity < 50 % of class nameplate |
| **Q4** | Is any **non-gap-shaped** identification available for a floor *change*? | must name a source-grounded statistic derivable from PJM's own CAMPD/EIA-923, state its **direction before computing it**, and clear the neiso-73 CAMPD-gross contamination check | DEAD if the only reachable number is sized by the residual, or if its direction is floor-raising (§2) |

**Screen verdict rule.** If **Q1 DEAD and Q2 REFUTED and Q3 DEAD**, the lane
has no admissible arm: the floor does not bind (so it cannot be relaxed), the
capacity cap does not bind (so the holdout cannot bite), and no measured share
exists to swap in. → **REFUSE, spend no LP**, register nothing, and write the
finding. Stamp the matrix cells accordingly.

**If any branch survives**, the arm gates in §4 are already registered and the
A/B proceeds under them.

## 4. Arm gates, registered now in case the screen survives

Single-delta A/B, years 2023 2024 2025 in ONE invocation per arm, sequential
(rules 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]`), same-HEAD zero-delta control via
`scripts/probes/_pjm148_chain.sh`.

| gate | rule |
|---|---|
| **K0** wiring liveness, PRE-SOLVE | the repriced/refloored population is non-empty, moves identically in all 3 yr, and leaks into **zero** out-of-scope classes (the ERCOT-146 hazard, checked on PJM's own fleet per rule 25) |
| **K1** dispatch liveness | max \|Δ class-hour\| on CC_CHP > 50 MW in every year — **at the grain the mechanism claims** (a host-steam floor claims an hourly floor, so an hourly-grain move is required, not merely an annual one) |
| **K2** control integrity | control reproduces the committed keeper; strict-byte reported, drift attributed if non-zero |
| **K3** scope integrity | exactly the intended `(plant, class)` pairs move; none outside the artifact |
| **K4** sign | CC_CHP **falls** (the only admissible direction, §2) |
| **K5** **OVERSHOOT kill** (the neiso-70/71 kill, declared as the handoff requires) | CC_CHP must not cross from over- to **under**-generating in any year: \|C1 error\| must improve **and** model must stay ≥ actual. A host-steam mechanism can over-force a class as easily as a dear offer can over-release it — **crossing under is a KILL, not a win** |
| **E1a** | the mechanism's own class moves in the declared direction in all 3 yr |
| **E1b** | CC_CHP band: improvement of **0.3–2.5 TWh** in 2023 (the gap is 2.491; a move larger than the gap is by definition over-forcing) |
| **E1c** | \|C1 error\| improves on CC_CHP in every year |
| **E1d** | **C1 MAGNITUDE EXPECTATION** (pjm-147's declared gate, carried): **no C1-gated class moves > 1.5 TWh in any year.** CC_CHP is pinned/excluded from the free score, so a large move on a *gated* class is displacement, not the mechanism working |

## 5. Limitations binding this session (pjm-147 §7, inherited)

* **The CT_CHP half is NOT identified** (32.6 % of capacity, 25.1 % of its own
  metered energy), **NOT scored** (`CT_CHP ∈ FUELMIX_EXCLUDED`), and nearly
  **inert** at the seam (+0.36 %). **Not cited in either direction.**
* **CC_CHP is a PINNED class** (audit L4), excluded from the free-class score.
  This lane **cannot** move PJM's headline — `free 12/12` holds either way — and
  equally **cannot be gate-chasing**. Judged on rule 1 `[R-STRUCT]`.
* **CC_CHP/CT_CHP are exempt from BOTH C7 and C8** by explicit class list, not
  by the 2 % materiality floor. Their D-1/D-2 numbers are diagnostics, never a
  passed gate.
* **Rule 23 `[R-FROZEN-DERIVE]`: the CHP heat rate is NOT re-derived here.** It
  re-derives only on an eGRID/CAMPD source change.
* **Rule 22 `[R-HOLDOUT]`: 2023–2025 only.** `holdout-freeze.json` is ACTIVE and
  outranks PJM's `complete` marker. No year outside the training set is touched.

## 6. A premise in the handoff this session will test, not assume

The handoff describes "the `chp_steam` D-2 floor level (11.0/7.9/10.4 % of class
energy at PJM)". **That figure is not reproduced by the keeper's own committed
`legitimacy_diagnostics.json`**, which carries **no CC_CHP `chp_steam` row at
all** — in either arm, in any year. Whatever the correct provenance of
11.0/7.9/10.4, the load-bearing quantity for this lane is the *binding* status
of CC_CHP's floor, which Q1 measures directly and from two independent
directions. The discrepancy is reported in the finding either way.
