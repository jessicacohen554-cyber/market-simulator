# Foresight adjudication memo — owner decision on `entry_lookahead_reprice` (2026-07-06, L-7c)

*Decision memo for the owner. The A/B is ALREADY RUN
(`foresight-ab-ercot-2026-07-06.{md,json}`, 4 arms × {high, mid} growth,
2026-2040) and plan §2.4.1 records a recommendation marked "RECOMMENDATION
ONLY, no flip" — this memo closes the adjudication loop with the
mechanism-level account of the high-growth inversion the plan flagged as an
open root cause, and puts the three dispositions in front of the owner. No
solve was run for this memo; no default is flipped in-session.*

## 1. What the A/B measured (recap, one table)

Materiality bar: |Δ cum 2030-2040 fossil CO₂| > 5% vs myopic base;
*preferred* also reduces backstop forced-build MW.

| arm | high-growth ΔCO₂ | high backstop | mid-growth ΔCO₂ | mid backstop |
|---|---:|---:|---:|---:|
| ewma (α=0.6) | +4.8% | 31.8→35.9 GW | +0.2% | 47.1→43.9 GW |
| lookahead | **+18.1%** | **31.8→91.2 GW** | **−5.8%** | 47.1→43.2 GW |
| both | +8.9% | 31.8→69.2 GW | −6.5% | 47.1→44.1 GW |

Mid growth: lookahead is material AND preferred — the designed effect
(entry pulled 15→39 GW earlier, coal down, backstop down). High growth —
the stress case the experiment was designed around — inverts everything:
economic entry collapses 101→57 GW, the backstop nearly triples, coal
+38%, CO₂ +18.1%. EWMA is immaterial on both paths (no further analysis;
`entry_price_signal_alpha` stays 1.0 as a designed probe).

## 2. WHY the high-growth path inverts — the mechanism, from the code

The two arms differ in what price series the capacity screens see
(`runner.py`):

- **Myopic base:** the realized year's LP duals **plus the post-solve ORDC
  overlay computed from solved hourly responsive headroom** —
  `reserve_headroom()` with the online/offline split (a cold slow-start
  unit is not real-time reserve), hour-specific availability (outage
  clusters intact), actual storage charge/discharge state, renewable
  headroom, and the reliability-deployment netting.
- **Lookahead arm:** `_lookahead_reprice_signal()` **replaces** that series
  outright with a static-stack pro-forma of next year's net load: each
  unit at its **time-mean** marginal cost and **time-mean** availability,
  no storage in the stack, no transmission, and an ORDC tail on
  `reserves = total_stack_capacity − net_load` — i.e. **every installed MW
  at mean availability counts as reserve**, with scarcity priced only
  where the whole stack approaches exhaustion.

That construction trades a **timing error** for a **level error**:

- The myopic signal's error is *timing* — it prices year Y's demand when
  the screen is deciding year Y+1 capacity. In mid growth this lag is the
  dominant error (scarcity hours are rare, so the coarse scarcity proxy in
  the lookahead barely matters). The lookahead deletes the lag → the
  intended result.
- The lookahead's error is *level* — its whole-stack-at-mean-availability
  reserve proxy systematically under-prices scarcity relative to the
  responsive-headroom overlay, because realized scarcity in the model
  lives exactly in the states the static stack smooths away: outage
  clusters, storage depletion, offline slow-start units. In **high growth
  the regime is permanent scarcity** (base mean price $825/MWh, P95
  $2,746), so nearly all screen revenue above cost IS the scarcity
  component — the arm swaps the revenue-bearing part of the signal for a
  low-fidelity proxy.

The diagnostic that proves the level error (rather than merely suggesting
it): the lookahead arm's mean signal is **$486/MWh vs the myopic $825** —
the pro-forma of a **strictly tighter** year (demand_{Y+1} > demand_Y)
prices ~40% *below* the realized current year. A faithful re-price of a
tighter year cannot be cheaper than the realized looser year; the gap is
the fidelity loss of the stack proxy, not information about Y+1.

Causal chain to the observed metrics: under-priced scarcity → new-entry
pro-formas (VRE capture, CT scarcity rent, storage arbitrage windows) all
undershoot → economic entry collapses 101→57 GW → the harness-enabled
adequacy backstop backfills 91 GW of gas-CT *by requirement, not
economics* (the plan §1.4 tripwire, firing at 3× base) → the VRE/storage
that never built stops displacing coal/gas-CT → coal 765→1,058 TWh, CO₂
+18.1%. Every observed number is downstream of the one signal-fidelity
defect. Component 1 of the arm (known-demand substitution in the
peak-anchored mechanisms) is NOT implicated — it was promoted
unconditionally in Stage 2 as a bug-class fix and is ON in every arm
including base.

## 3. The three dispositions

**(A) Promote `entry_lookahead_reprice` default-on.** REJECTED. It degrades
the stress case it was designed for; rule 1 forbids judging a mechanism by
its one favorable number (here, the mid-growth CO₂ move). The plan's own
guard — "check the conclusion isn't stress-case-only" — fires inverted:
the *benefit* is mid-only.

**(B) Keep default-off as a designed probe, with a named reopening
condition.** RECOMMENDED. The mechanism idea (a developer pro-forma of the
entering year) is structurally right; its current *implementation* prices
scarcity on a coarser basis than the model's own overlay. The fix is
signal fidelity, not gating: rebuild the lookahead's scarcity tail on the
same responsive-headroom construction the overlay uses (project next-year
hourly availability and storage response the way `reserve_headroom()`
counts them, or apply the overlay's own adder recomputed on projected
headroom), so the arm can never price a tighter year below the realized
one. Reopening condition: after that fix, re-run this A/B; promote only if
the mid-growth benefit survives AND high growth no longer inverts.

**(C) Condition the flag on the demand path (enable mid, disable high).**
REJECTED. A mechanism gated by the growth regime is an outcome-keyed
switch, not a market behaviour — developers do not stop running
pro-formas when growth is fast (they run them harder). It would encode
the diagnosed level error instead of fixing it, and it creates an
off-registry-flavoured channel where the "right" mechanism depends on
which scenario is being run (rules 13/23 in spirit).

## 4. Interaction with the accreditation-basis fix (same session, L-7c)

The A/B ran with the backstop ON under the OLD ERCOT accreditation basis
(`ercot-accreditation-audit-2026-07-06.md`), which overstated the firm
requirement — so every arm's absolute backstop MW is inflated, base
included. This shifts the *level* of the backstop tell, not the
between-arm comparison, and the CO₂ inversion is signal-side, not
requirement-side: the verdict direction stands. A post-fix A/B re-run is
cheap if the owner wants the backstop columns restated, but it is not
needed for the no-promote decision, and it should in any case wait for the
§3(B) fidelity fix so the re-run adjudicates the mechanism rather than
re-measuring the known defect.

## 5. Owner decision requested

- [ ] Adopt (B): `entry_lookahead_reprice` stays default-off; the §3(B)
      fidelity fix becomes the standing open item; re-run the A/B after it.
- [ ] Adopt (A) or (C) instead (states reasons; note both are recommended
      against above).

*No model defaults changed by this memo. `entry_lookahead_reprice` remains
default-off; `entry_price_signal_alpha` remains 1.0. Plan §2.4.1 remains
the run record; this memo is the adjudication. Produced 2026-07-06, lane
L-7c.*
