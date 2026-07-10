# FINDING — caiso-71: the measured LOCATIONAL AS requirement is ex-ante INERT; the SP26 must-procure floor is an order of magnitude too small to force SoCal gas online (2026-07-10)

**Successor to** `FINDING-caiso70-bridge-decrowding-negative-2026-07-10.md`
(read it first). caiso-70 closed the RA-bridge de-crowding lane (negative) and
scoped probe #2: the award→energy commitment-posture channel
(`caiso_commitment_posture`), shown **ex-ante inert on the SYSTEM-wide BAL-002
requirement** because un-postured free reserve supply covers it several times
over — so "the binding driver must be locational." This finding tests that
locational hypothesis against the newly-fetched measured requirement, and
**refutes it ex-ante on magnitude**: the locational floor is ~15× smaller than
SoCal's own un-postured supply. No solve was burned (the caiso-70 method — the
mechanism's own driver evidence decides it, CLAUDE.md rule 1).

## What the honesty check found (the cheap arithmetic before the solve)

The handoff's step-3 gate: can the measured SP26/NP26 regional minima be served
for free by IN-REGION un-postured supply? Intercepting the real CAISO 2024
fleet at `get_reserve_design` (fleet fully built, LP not solved;
`scripts/probes/_caiso71_honesty_check.py`) gives the reserve-eligible 10-minute
**deliverable** ramp (availability-scaled) per Path-26 region, split by whether
providing reserve is free (offline fast-start CT/oil + hydro governor ramp) or
costs a commitment (postured CC/ST):

| region | fast-start (free, offline-capable) | of which non-hydro CT/oil | hydro (free) | postured (needs a start) | TOTAL | measured evening minimum (spin+nonspin) | FREE ÷ need |
|---|---:|---:|---:|---:|---:|---:|---:|
| **SP26** (LA_BASIN, SDGE, SP15_rest) | 4,275 MW | 3,777 MW | 498 MW | 2,664 MW | 6,939 MW | **318 MW** (63 + 255) | **15.0×** |
| **NP26** (NP15, ZP26) | 9,624 MW | 3,554 MW | 6,071 MW | 2,449 MW | 12,073 MW | 318 MW | 49.4× |

Measured DAM AS_REQ regional minima (`data/raw/CAISO-AS`, evening peak h17-21):
SP26 spin ≈ 56-63 MW, non-spin ≈ 249-258 MW; annual means 2023/24/25 spin
71.6/56.3/57.1, non-spin 214.4/225.2/228.5. NP26 minima are within a few MW of
SP26. The regional **MAX** (anti-concentration cap) rows are a uniform **0
sentinel** for every SP26/NP26 spin/non-spin product — CAISO publishes no
regional cap, so only the MIN floor is a usable locational driver.

**Conclusion — inert on two independent counts:**

1. **Free supply dwarfs the floor.** SoCal's offline fast-start CT/oil alone
   (3,777 MW) covers the entire SP26 spin+non-spin floor ~12×; adding hydro the
   un-postured free pool is 15×. The LP never pays a CC start + min-load ride to
   provide reserve a peaker provides for free — the caiso-59/62/70 inertness,
   now at the locational level.
2. **The one slice a sync-split would rescue is 63 MW.** The structural leak the
   pivot targets is offline fast-start CT back-**spinning** (spin must be
   synchronized). But the SP26 **spin** floor is only ~63 MW; sync-scoping it to
   P0-online units cannot force an incremental start when SoCal already commits
   multiple GW of CC every evening (≥63 MW of online headroom is always
   present). The non-spin floor (255 MW) is legitimately servable by offline
   fast-start CT and needs no synchronization. So the P0-online sync-scoping
   route the handoff scoped would **also** be inert — the requirement is simply
   too small, and no dispatch.py extension changes that.

**Magnitude vs the target.** The miss being chased is the CT_PEAKER energy gap
(model ~0.9 TWh vs actual **4.56 / 5.24 / 3.09 TWh**, evening-loaded). Even if
the entire 318 MW SP26 floor were force-committed every evening hour
(~5 h × 365) it is ≈ 0.6 TWh/yr — one-eighth of the gap — and it does **not**
force even that, because SoCal supply covers it 15×. A measured locational AS
requirement of this size cannot be the missing-CT driver.

## The three questions (owner, this session)

**1. Do we need more zonal granularity?** Not for *this* mechanism — the total
measured locational floor is tiny regardless of how finely Path 26 is sliced, so
a finer AS region would carry an even smaller number. Granularity matters for a
**different** driver: the CT gap is a *local-reliability / intra-basin
congestion* phenomenon, and our reduced 6-zone network collapses the LA Basin's
internal transmission-constrained pockets (the CAISO LCR local-capacity
sub-areas) into one node. Units that run in reality because a **local** line/pocket
is binding — not because system or regional reserve is short — never see that
constraint in our topology, so the LP leaves them idle on merit. The promising
granularity is **transmission/local-capacity** resolution inside SP15/LA_BASIN
(and an explicit local-capacity / RMR commitment), not finer AS regions.

**2. What do other models do?** Production CAISO reproductions (CAISO's own
production-cost studies, Aurora/PLEXOS nodal builds, EIA/S&P) get SoCal peaker
dispatch from mechanisms our system-AS layer doesn't contain:
- **Nodal or fine-zonal transmission** with the LA-Basin/San-Diego
  local-capacity constraints enforced, so pocket units commit for **local**
  reliability regardless of system economics.
- **RMR / local-capacity procurement** — specific gas units held online by
  contract/backstop (a commitment floor with a *local* driver, not an energy
  merit call).
- **RUC / RA must-offer at a locational level** and **FRP** (flexible ramping)
  for the intra-hour net-load ramp the DA LP doesn't see.
The consensus: CAISO CT energy is **locally-committed** (congestion pockets +
local RA/RMR + ramp), *not* driven by system/regional reserve MW — exactly what
the 318 MW floor here confirms from the other side.

**3. Why are we so off on CAISO?** The residual signature —
CT_PEAKER 0.9 vs 4.6/5.2/3.1 TWh; hrs>$200 model **540/0/0** vs actual
**21/35/8**; evening belly over-priced (C3a) — points to one root cause, not a
missing reserve product: **the model prices SYSTEM-wide scarcity where reality
has LOCAL scarcity.** In 2023 the system co-opt manufactures a spurious 540-hour
tail; in 2024/25 it produces none, while the actual tail is a handful of
**local** congestion hours the reduced network cannot form. The evening CC/CT
commitment posture is likewise a *local/RA* obligation (reality commits
+1.9/+1.2/+0.3 GW more evening CC than merit) that no system or regional-AS
mechanism reproduces. The gap is structural-topological (intra-basin congestion
+ local-capacity commitment), and it is why every system-level lever — the RA
bridge, the system co-opt, and now the measured regional-AS floor — has moved
CT_PEAKER essentially not at all.

## What was built (kept, default-off — correct structure per rule 1)

A real, forward-regenerable **locational** reserve requirement now exists in the
model, ready for a materially larger local constraint to populate:

- **Intake** `data/raw/CAISO-AS` (OASIS DAM AS_REQ, 2023-2025, min+max per
  region×product) + loader `market_sim/data/caiso_as_requirements.py`
  (rule-13-admissible measured series; the MAX-is-0-sentinel documented).
- **Mechanism** `reserve_config._caiso_locational_as_families` +
  `ScenarioConfig.caiso_locational_as_families` (default off): zone-masked
  SP26/NP26 spin/non-spin `ReserveFamily`s from the measured minima, pricing at
  the same published tariff curves. Composes with the pergen pools and the
  commitment posture; zero fitted parameters. Verified to build a valid 6-family
  design (`scripts/probes/_caiso71_families_check.py`); tested
  (`tests/test_caiso_locational_as.py`).

It is **INERT and NOT in any keeper** — shipped because it is the structurally
correct representation of a locational AS requirement (rule 1: build the right
structure even when it does not move the residual), not because it helps the
fit. No solve was run and nothing is registered on the dashboard (there is no
completed run to register; the inertness is established ex-ante, as caiso-70
established the system-wide case).

## Consequences for the probe queue

- ~~System-wide commitment posture~~ — inert ex-ante (caiso-70).
- ~~Locational AS requirement (SP26/NP26 minima)~~ — **inert ex-ante (this
  finding): the measured floor is 15× under SoCal's free supply.**
- **Live lead:** the CT gap is a **local-reliability** problem. The next build
  is intra-LA-Basin transmission/local-capacity resolution + an explicit
  local-capacity/RMR commitment driver (a *local* floor with a window and a
  forward story, rule 12) — the mechanism class the production models use and
  the only one whose magnitude can reach the 3.7-4.4 TWh/yr CT gap. AS-side and
  system-reserve levers are closed.
