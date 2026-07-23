# FINDING — caiso-116 EXECUTE-THE-BELLY-LANE: candidate (a) (the endogenous WECC-West node) CANNOT be evening-scoped to keep the C3a guard while fixing C5a — the modeled West (EIA-930 NW+SW) net-exports only ~19 TWh/yr but CAISO imports 29-36 TWh, and L1b matched CA's import VOLUME only by over-generating that ~9-17 TWh/yr gap as gas exported at the intertie hub (the marginal, evening-price-setting unit that breaks C3a); C5a-fix and C3a-guard are COUPLED through that proxy over-export, so BOTH scopings fail by derivation — fleet-bound (thermal-shaping) under-supplies CA → over-corrects C5a AND is infeasible (the West itself net-imports ~1/4 of hours), price-temper (min-hub) under-fixes C3a; keeper 2026-07-19-caiso-102-hourfix UNCHANGED (2026-07-23)

**Derive-first gate, mechanism built-then-refuted, NO SOLVE, nothing registered.**
Keeper `2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}).
This session was chartered to EXECUTE the belly (C5a) lane by building one
pre-registered single delta — candidate (a), the caiso-114 endogenous WECC-West
node evening-scoped so the West does not set CA's evening LMP. A derive-first
pass (the discipline rule #1 mandates before committing a mechanism) uncovered a
data-scope gap the caiso-114/115 handoffs did not anticipate, which makes both
of the handoff's candidate-(a) scopings fail by derivation. The delta (a measured
West thermal-availability shape) was implemented + unit-tested, then **reverted**
because the derive shows it cannot be solved cleanly (it over-corrects C5a and is
infeasible). All numbers reproduce from committed artifacts + raw EIA-930 + the
`wecc-west-supply` clean frame via
`scripts/probes/_caiso116_endogenous_datascope_derive.py` (no LP).

---

## Headline

The caiso-114/115 handoff framed candidate (a) as **"the L1b structure with its
ONE regression (evening over-price) removed."** The derive shows the regression
is **not cleanly removable**: it is not an incidental pricing bug but the direct
consequence of a **structural data-scope gap** in the EIA-930 NW+SW endogenous
node. The node reproduces CAISO's import VOLUME (and thus the C5a fix) **only by
having the modeled West over-generate ~9-17 TWh/yr of gas beyond its real
dispatch and export it at the intertie hub** — and that fictitious hub-priced
gas, being the marginal export unit, is exactly what over-prices CA's evening and
breaks C3a. Remove the over-price and you lose the volume (and C5a); keep the
volume and you keep the over-price. **C5a-fix and C3a-guard are coupled through
the West's proxy over-export**, so both of the handoff's candidate-(a) scopings
fail:

- **fleet-bound** (cap West thermal at measured output) → under-supplies CA by
  the gap → **over-corrects C5a**, and is **infeasible** (the West itself
  net-imports ~1/4 of hours from sources the CA-only tie cannot represent);
- **price-temper** (offer the West gas at `min(MALIN, PALOVRDE)` instead of the
  tie-weighted blend) → shaves only $1-7 off the evening vs the +$4-18 break →
  **under-fixes C3a**.

This **sharpens** the caiso-115 separability claim: the belly-volume (hod 10-15)
and evening-price (hod 17-21) lanes separate in HOURS, but the *endogenous node*
re-couples them through the volume gap — L1b broke C3a not merely because it
"reset CA's evening LMP to the West hub" but because it *had to* over-export gas
at that hub to hit CA's volume. Candidate (a) is therefore **not viable for the
belly lane** until the West import scope is reconciled (below).

---

## Inv 1 — the annual data-scope gap (the load-bearing number)

Modeled West net-export capability (`wecc-west-supply` `net_export_mw` =
EIA-930 NW+SW net generation − demand) vs CAISO's measured net import (raw
EIA-930 CISO `Total interchange`):

| year | West net-export | CAISO net import | GAP | L1b net import |
|---|---|---|---|---|
| 2023 | 19.4 TWh | 28.8 TWh | **9.3 TWh** | 32.3 |
| 2024 | 18.9 TWh | 31.9 TWh | **13.0 TWh** | 31.7 |
| 2025 | 19.2 TWh | 36.0 TWh | **16.9 TWh** | 37.1 |

- The modeled West nets out a near-flat ~19 TWh/yr, but CAISO's import DEMAND
  **grows** 29→36 TWh, so the gap **widens** 9→17 TWh — CA is importing an
  increasing share from sources **outside** the modeled NW+SW aggregate (the West
  itself wheeling eastern/Baja energy through to CA, or interchange the NW+SW
  net-position does not capture).
- **L1b (`caiso110_endog_B`) matched CA's volume (32/32/37 TWh ≈ actual) only by
  over-generating the gap:** its West exported ~13-18 TWh MORE than its measured
  19 TWh net position. That fictitious surplus is West GAS priced at the measured
  intertie hub — LOW in the belly (self-limiting, the C5a fix worked) but HIGH in
  the evening, where it is the marginal unit and SETS CA's import-zone LMP
  (+$4-18/MWh, the C3a break). The over-export is a *proxy* for CA's true
  out-of-region imports; pricing that proxy at the hub (marginal) is what breaks
  C3a.

## Inv 2 — the West's exportable surplus cannot supply CA in any block

West exportable-gas surplus (`gas_mw` − gas needed for the West's own load) vs
CAISO's actual net import, by hour-of-day block (GW):

| year | block | West export-gas | CAISO net import |
|---|---|---|---|
| 2023 | belly | 0.5 | 0.7 |
| 2023 | evening | 1.8 | 3.3 |
| 2023 | night | 3.3 | 5.3 |
| 2024 | belly | 0.6 | 1.4 |
| 2024 | evening | 1.2 | 3.5 |
| 2024 | night | 3.5 | 5.5 |
| 2025 | belly | 1.2 | 1.9 |
| 2025 | evening | 0.7 | 3.9 |
| 2025 | night | 3.4 | 6.2 |

The West's exportable surplus is **almost entirely gas** (its non-gas — hydro /
nuclear / coal / VRE — is consumed by its own load) and it **tracks the tie
shape** (~0 belly, +2 evening, +4 night) but is **far below** CAISO's actual net
import in every block. The West physically cannot supply CA's imports from its
real surplus — confirming the annual gap at the diurnal grain, and explaining why
the L1b node had to give the West a huge unshaped gas nameplate (53 GW) to
over-export.

## Inv 3 — bounding the West to measured supply is INFEASIBLE (the gap bites both ways)

| year | West net-imports (net_gen < demand) | worst shortfall |
|---|---|---|
| 2023 | 22 % of hours | 7.3 GW |
| 2024 | 23 % of hours | 7.6 GW |
| 2025 | 24 % of hours | 7.3 GW |

The modeled West is itself a **net importer ~1/4 of hours** — it draws on WECC
regions outside the modeled NW+SW aggregate (and outside the single CA tie). So
the fleet-bound scoping (cap West thermal at measured output, which WOULD force
CA's own gas marginal and preserve C3a) is **infeasible**: in a quarter of hours
the West cannot serve its own load from its measured generation, and no
CA-connected backstop can represent its real (eastern) imports without a
false choice —
- price the backstop cheaply → it exports to CA and **under-prices** the evening;
- price it high → CA serves the West's shortfall over the tie (CA→West) in the
  West's own peak, **over-inflating CA gas** and re-breaking C5a.

The same ~13-18 TWh gap that over-prices the export direction makes the import
direction unrepresentable. This is a property of the DATA SCOPE (NW+SW vs CA's
true import geography), not of any tunable.

## Inv 4 — the empirical anchor: L1b fixes C5a + C3c, breaks C3a

From the committed `caiso110_endog_B/metrics.json` (the caiso-114 L1b run):

| criterion | tier | status |
|---|---|---|
| C5a CO2 vs eGRID | load-bearing | **PASS** |
| C3c price tail / scarcity | supporting | **PASS** |
| C3a mean LMP | load-bearing | **FAIL** |
| C3b price duration/shape | load-bearing | PASS |
| C4 fleet hourly dispatch correlation | supporting | FAIL |

The verdict is the coupling, empirically: the endogenous node's belly volume fix
(C5a) and evening scarcity (C3c) ride on the very over-export that breaks C3a.

## Inv 5 — the price-temper scoping (min-hub) under-fixes C3a

The caiso-114 note's option (c) — offer the West gas at `min(MALIN, PALOVRDE)`
(the marginal importer uses the cheapest deliverable corridor) instead of the
tie-capacity-weighted blend (which leans 69 % on the PALOVRDE desert-SW
scarcity path):

| year | evening BLEND | evening MIN | reduction |
|---|---|---|---|
| 2023 | $71.0 | $63.9 | −$7.1 |
| 2024 | $54.9 | $52.5 | −$2.5 |
| 2025 | $46.4 | $45.2 | −$1.2 |

`min` lowers the West's evening offer by only **$1-7**, versus the **+$4-18**
C3a break. The break is not the hub's exact level — it is the West gas *becoming
the marginal price-setter* at the hub (replacing the keeper's cheaper evening
mix). Shaving a few dollars off the hub does not stop it setting the price, so
min-hub under-fixes C3a while (via the slightly cheaper belly offer) marginally
worsening C5a. Refuted as the single delta.

---

## Decision framing — candidate (a) status and the redirect

**Candidate (a) (endogenous WECC-West node) — NOT VIABLE for the belly lane as
built.** The NW+SW aggregate is not a self-contained neighbor for CAISO: it
net-exports 19 TWh/yr while CA imports 29-36, and it net-imports ~1/4 of hours.
The node reproduces CA's volume/CO2 only by an unphysical hub-priced gas
over-export that necessarily over-prices the evening. Neither the handoff's
fleet-bound nor its price-temper scoping can separate the C5a fix from the C3a
break, by derivation. This is a DATA-SCOPE limitation, not a tuning failure —
so it will not yield to another offer-curve or availability tweak.

**The mechanism was built and reverted.** A measured West thermal-availability
shape (`caiso_wecc_west_thermal_shaped`, cap West coal/gas at `wecc-west-supply`
`coal_mw`/`gas_mw`) was implemented + unit-tested as the fleet-bound scoping
(it is the cleanest, rule-13-admissible knob — same measured-availability class
as the node's VRE/hydro shaping). The derive then showed it (a) over-corrects
C5a — bounding the West to ~19 TWh under-supplies CA's 29-36 TWh so CA runs
+9-17 TWh more gas (past the +7 % C5a gate) — and (b) is infeasible (Inv 3). It
was reverted rather than solved: a solve would require an unphysical CA-connected
backstop whose result would be uninterpretable, and rule #1 forbids reaching a
number through a mechanism that isn't real. The full design is recorded here and
is re-implementable in minutes once the data scope is reconciled.

### Redirect (caiso-117+) — reconcile the West import scope, or hand the evening to CA's own scarcity

Three routes, in preference order:

1. **Close the data-scope gap (the structural fix).** Broaden the modeled West
   beyond NW+SW to include the sources CA actually imports from (or add the
   West's own eastern/Baja import as an inframarginal price-taker into the
   `wecc-west-supply` frame), so the West's net-export capability matches CA's
   ~29-36 TWh imports. Then the L1b over-export becomes REAL (not fictitious) and
   is inframarginal (a contracted/wheeled base, not a marginal hub-priced gas),
   so CA's own gas sets the evening price — the fleet-bound scoping (`_thermal_
   shaped`) becomes both feasible and C3a-preserving. This is the honest path;
   its cost is a data-scope extension (more BAs / a reconciled import series).

2. **Do the EVENING lane first/jointly (the caiso-117 lane the handoff named).**
   Tighten CA's OWN evening scarcity — `hydro_dispatch_envelope` to a lower
   percentile / daily budget, and/or arm `caiso_firm_import_shape` — so CA's
   domestic peakers (not the West import) set the evening price. If CA's domestic
   evening clearing rises to compete with the intertie hub, the West import
   becomes inframarginal by comparison and its hub price stops setting C3a. The
   belly (endogenous) and evening (domestic scarcity) lanes are **coupled** and
   should be worked together, not separately — this session's finding refutes the
   caiso-115 hope that candidate (a)'s belly fix could be scoped in isolation.

3. **Fall back to candidate (b), belly-hour-scoped and West-physically grounded.**
   The keeper already runs `caiso_corridor_flow_limit` (p95 corridor ATC), but it
   is too loose in the belly (allows ~4.4 GW vs the West's ~1-2 GW physical belly
   export capability, Inv 2). A **belly-hour-only** cap at the West's measured
   belly deliverability (a West-side physical quantity from `wecc-west-supply`,
   NOT CA's residual flow) would fix the belly over-import (C5a) while leaving the
   evening untouched (C3a preserved by construction). Caveat: a net-export-based
   cap applied to ALL hours hits the SAME data-scope gap (under-supplies →
   over-corrects C5a), so it MUST be belly-scoped; and the percentile/level choice
   must be tied to the West's physical belly capability, not tuned to the residual
   (rule 13 / the caiso-107/109 kills).

## DO-NOT-REDO (added this session)

- **Endogenous-node fleet-bound scoping (thermal-shaping) on the NW+SW frame** —
  over-corrects C5a (Inv 1) and is infeasible (Inv 3); do not re-attempt until
  the West import scope is reconciled (redirect #1).
- **min-hub / MALIN-PALOVRDE evening blend re-weighting** — under-fixes C3a
  (Inv 5, shaves $1-7 vs the +$4-18 break); the break is marginality, not level.
- Carried from prior sessions: fixed-hub West fallback (caiso-114 KILL); belly-
  depth on any CA-price / west-surplus-QUANTITY observable (caiso-107/109);
  firm-rung offer reprice (pinned, caiso-104/109).

Full reproduction: `scripts/probes/_caiso116_endogenous_datascope_derive.py`.
