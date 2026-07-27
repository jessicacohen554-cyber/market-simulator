# NYISO C3c scarcity formation — where the missing tail is, and what it is not (nyiso-83)

**Date:** 2026-07-26 · **Session:** nyiso-83 (in-city commitment adjudication lane) ·
**Basis:** the nyiso-81 keeper's committed hourly sidecars
(`results/calibration/nyiso81_floor_rederive/hourly/system_<year>.parquet`) — **no
LP replay**, no new solve. · **Status:** partial diagnosis. It localizes the
residual and **refutes one framing**; the leading structural hypothesis is now
under test by the nyiso-83 obligation probe rather than asserted here.

## 0. The residual

C3c gates the count of hours the LP's **max zonal dual** exceeds the per-ISO
threshold (`TAIL_THRESHOLD["NYISO"] = $300`, `scripts/calibration_verdict.py`)
against the committed RT hourly actual tail. The keeper:

| year | model h > $300 | actual RT h > $300 |
|---|--:|--:|
| 2023 | 3 | 10 |
| 2024 | 0 | 12 |
| 2025 | 9 | 42 |

This is a **current-main property**, not a keeper artifact: the drifted control
(`2026-07-26-nyiso-79-control`) reproduces 3/0/9 identically. The gap widens
with the year, and 2025 is the worst cell (9 vs 42).

## 1. The tail the model *does* produce is entirely Zone K

Recomputed per zone from the keeper's own hourlies (max-zonal-dual basis, the
gated quantity):

| year | Capital_Hudson | Lower_Hudson | NYC | **Long_Island** | Upstate_West | any-zone |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 0 | 0 | 0 | **3** | 0 | 3 |
| 2024 | 0 | 0 | 0 | **0** | 0 | 0 |
| 2025 | 0 | 0 | 0 | **9** | 0 | 9 |

**Every scarcity hour the model produces is a Long Island hour.** NYC, the
Lower Hudson and upstate never clear $300 in any training year. Whatever is
missing is therefore not "a bit more of the same" — the model has no NYC/SENY
scarcity-formation channel that reaches the threshold at all.

The load-weighted price confirms the tail is compressed rather than merely
sparse — it never approaches the threshold in any year:

| year | p99 | p99.9 | max |
|---|--:|--:|--:|
| 2023 | \$59 | \$122 | \$130 |
| 2024 | \$108 | \$168 | \$174 |
| 2025 | \$173 | \$208 | \$296 |

## 2. What this evidence does NOT show — a correction worth recording

An earlier reading of the same sidecar treated the **zone-identical**
`reserve_price` column (12.5 / 28.1 / 177.3 max, identical across all five
zones *and* the external node in every year) as evidence that the locational
reserve families never bind while the NYCA families do.

**That inference is unsupported and must not be built on.** The writer
(`scripts/run_calibration_full.py`, the `system_<year>.parquet` block) computes
a single system-wide series `rp` and assigns `"reserve_price": rp` inside the
per-zone loop — the column is **broadcast by construction**, so it is identical
across zones in every run of every ISO and carries no locational information
whatsoever. The per-family duals (`DispatchResult.reserve_price_by_family`) are
**not** in the committed sidecar, so **locational binding cannot be tested from
the keeper bundle** — it needs a replay that persists them.

What the system series *does* support: the NYCA-tier curve is entered but never
deeply — 22 / 6 / 66 hours with a non-zero dual, peaking at \$12.5 / \$28.1 /
\$177.3 against published RCPF max penalties of \$750–775. So system-wide
reserve shortage is priced, mildly, and is far from the curve's deep steps.

## 3. The leading structural hypothesis (now under test, not asserted)

The candidate root cause is the one the `nyiso_synchronised_reserve` docstring
already names for the NYC peaker case: the locational reserve families draw
**idle-allowed** headroom (`sum_g P + R <= sum_g cap`), so any idle downstate
capacity satisfies a load-pocket requirement at zero cost and the RCPF never
prices. If that holds at the J/K ladder level, no amount of downstate tightness
can produce a locational shortage dual, and the only scarcity that can ever
reach the tail is the NYCA-tier one — which is exactly the shape §1 shows.

This session built the mechanism that tests it directly:
`nyiso_incity_commitment_obligation` (commit `fa9fc78`) re-classes the published
NYC + LI 10-minute families onto an **online-gated** in-pocket class, and
`nyiso_li_locational_reserve` adds the Zone-K ladder that was absent entirely.
The nyiso-83 2024 A/B probe (vs a same-HEAD zero-delta control, because the
replay environment's solver/pandas versions differ from the keeper's recorded
ones) is the test. **Its outcome — including a null result — belongs in this
document's §4 before the hypothesis is treated as settled.**

## 4. Result — the idle-headroom framing is REFUTED, and the reason is a ceiling

The nyiso-83 obligation probe (2024, vs the same-HEAD zero-delta control) settles
it. **The gate works exactly as designed — and it still cannot move C3c.**

| quantity (NYC zone, 2024) | control | probe | 
|---|--:|--:|
| reserve-dual hours > \$0 | 6 | **7,003** |
| reserve-dual mean | \$0.010 | **\$10.96** |
| reserve-dual max | \$28.1 | **\$43.8** |
| C3c hours > \$300 (any zone) | 0 | **0** |

Online-gating the published NYC + LI 10-minute families takes the locational
reserve constraint from *essentially never binding* (6 hours) to **binding in
~80 % of all hours**. So the idle-headroom diagnosis of §3 was **correct about
the binding** — idle capacity really was satisfying the load-pocket requirement
for free — and **wrong about the consequence**. The tail did not move by a
single hour.

**Why: the J/K locational demand curves are capped at \$25/MW.** The published
NYC and Long Island 10-minute and 30-minute reserve demand curves are
**\$25/MW** (Ancillary Services Manual §6.8 items 9, 10, 14, 15 — the same value
carried in `NYISO_RCPF_LOCATIONAL` and in the new LI family). A family whose
maximum penalty is \$25/MW can contribute at most ~\$25/MW of scarcity rent to
the LBMP no matter how deeply short the pocket is. The observed dual peaks at
\$43.8 precisely because the *nested* tiers ($40 SENY/NYC/LI, \$500, \$775) sit
above it — but nothing in the J/K stack approaches the \$300 gate.

**Therefore the J/K ladders are structurally incapable of producing the C3c
tail, and no further work on them can close it.** This is a ceiling, not a
calibration gap. The tail has to come from the tiers whose published penalties
are large enough to reach it — **NYCA 10-min/30-min (\$750) and 10-min spin
(\$775), and East 10-min (\$775)** — i.e. from **system- and East-tier**
reserve-supply tightness, not from load-pocket formation.

That redirects the lane. The remaining leads are the ones that act on those
tiers: the NYCA-tier reserve-supply tightness in
`nyiso-overrun-underrun-2026-07.md` §3, and the 2025 LI steam OOM commitment
growth (SOM 2025 +68 %, light-load VOLTAGE-driven, 73 days) — which is a
**commitment** driver, not a reserve-pricing one, and so would reach C3c only
indirectly by changing what is online when the NYCA/East tiers bind. Note also
that **2024 is the weakest year to test C3c on** (the keeper's own model tail is
0 there); the 2025 arm (keeper 9 h vs actual 42 h) is the informative one and is
where any successor should measure.

## 4a. Collateral result — the obligation is NOT a substitute for the floor

The same probe answers the charter's rule-19 substitution question, negatively:

| 2024 | control | probe | Δ |
|---|--:|--:|--:|
| ST_GAS TWh | 8.710 | 5.810 | **−2.900** |
| ST_GAS evening mean MW | 1,392 | 1,001 | −391 |
| ST_GAS overnight mean MW | 731 | 409 | −322 |
| ST_GAS evening/overnight ratio | 1.905 | **2.449** | +0.544 |

Dropping the eight NYC/LI `ST_GAS` floor limbs and replacing them with the
published in-pocket obligation **costs 2.9 TWh of downstate steam** — against a
2024 gap that was already −3.02 TWh, roughly doubling it. The displaced energy
goes to `CC_REGULAR` (+1.47), `CT_CHP` (+0.68), `CC_CHP` (+0.45) and
`CT_PEAKER` (+0.11), summing to +2.90 — an exact downstate ST→CC/CT merit
substitution at constant total energy.

The cause is not that the mechanism fails to bind (it binds in 80 % of hours).
It is that the obligation is written on the *pocket*, not on *steam*: its
eligible set is in-pocket steam **∪** fast-start GT (faithfully, per the
instrument), so the LP satisfies 620 MW of published requirement with the
**cheapest** in-pocket online capacity — the CTs and CCs — and lets the
expensive boilers go. The p25-derived floor forced steam *specifically*; the
published reserve requirement does not.

**Shape, however, improves**: the obligation's steam is *more*
evening-concentrated than the floor's (ev/ng 1.905 → 2.449), which is the
direction the charter's acceptance criterion #3 asks for. The mechanism is
shape-faithful and level-insufficient.

**Disposition.** This is the outcome the instrument survey flagged as most
likely: the published reserve ladder is **not** the instrument that drives
in-city steam. The real driver is the non-public Con Edison load-pocket
procedure — the one the MMU itself reports it cannot see (41–42 % of NYC
reliability commitments "unverified"). So:

- the **rule-19 substitution is refuted** — the obligation cannot replace the
  NYC/LI `ST_GAS` floor limbs, and the floor stays;
- this is **not** a rule-1 [R-STRUCT] violation. The mechanism is not being
  rejected because a residual moved the wrong way; it is being rejected as a
  *substitute* because it provably does not act on the class it was required to
  replace. Rule 19 asked for replacement-or-reconciliation, and replacement has
  now been tested and failed;
- the **published LI ladder is a separate question** (a rule-14 omission fix
  that stands on its own) and is isolated by the `nyiso83_probe_lionly_2024`
  arm rather than being judged through the substitution's failure — see §4b.

## 4b. The published LI ladder ALONE is provably inert — and that is the proof

Third arm, `nyiso_li_locational_reserve=true` with the obligation **off** (so
the floor limbs stay), 2024 vs the same control:

| quantity (2024) | control | LI-only | obligation |
|---|--:|--:|--:|
| Long_Island reserve-dual hours > \$0 | 6 | **6** | 7,003 |
| Long_Island reserve-dual max | \$28.1 | **\$28.1** | \$43.8 |
| ST_GAS TWh | 8.710 | **8.710** | 5.810 |
| C3c hours > \$300 | 0 | **0** | 0 |

Adding the published Zone-K ladder changes **nothing**: every class lands within
solver noise (≤0.004 TWh), the price series is unchanged, and the LI reserve dual
is bit-identical to the control's. The reason is exactly the §3 mechanism, now
demonstrated rather than hypothesised: **without the online gate the LI families
are idle-allowed** (`sum_g P + R <= sum_g cap`), so Zone K's idle capacity
satisfies 120 MW of 10-minute and 270/540 MW of 30-minute requirement at zero
cost, in every hour of the year. A published requirement that any idle unit can
meet for free is not a constraint.

This is the clean decomposition of the mechanism:

- **published ladder alone → inert** (families never bind);
- **+ online gate → binds in ~80 % of hours** (6 → 7,003), which is the entire
  effect, and is what makes the load-pocket requirement a real constraint;
- **but the gate's reachable price is capped at the published \$25/MW**, so the
  binding never becomes a tail (§4);
- **and the obligation's eligible set is the pocket, not steam**, so the binding
  never becomes steam commitment (§4a).

So `nyiso_li_locational_reserve` is a **correct but provably inert** rule-14
accuracy fix — the model should carry the published Zone-K requirement (it is a
real published cell that was simply missing), but carrying it changes no result
on its own. It stays default-off and is recorded here as probe-adjudicated
inert, so no successor re-runs it expecting movement.

## 4c. Resolved side question — the obligation's `rho = 1.00` is a fallback

The solve logs `rho=1.00` for the obligation class. That is **not** the fleet
average and **not** a broken computation: on a synthetic fleet with
`pmin = 250, pmax = 1000` the same code returns exactly `3.0`. `1.00` is the
documented neutral fallback taken when **no** unit satisfies
`pmin > 0 and pmax > pmin` — the case for the legacy equal-width bins NYISO
uses (`use_campd_bins` is an ERCOT default), whose tranches carry `pmin = 0`.

Consequence: the gate is still a real constraint (`R <= sum_g P` — idle capacity
backs nothing, which is the whole effect measured in §4/§4b); only the headroom
*multiplier* is neutral rather than fleet-derived. It does not affect the \$25/MW
ceiling conclusion, which is a property of the published demand curve and not of
`rho`. Both branches are pinned by `tests/test_nyiso_incity_obligation.py::
TestObligationRhoFallback` so no later reader re-diagnoses it. The same fallback
applies to the pre-existing `nyiso_synchronised_reserve` path-A family, which
shares this construction — this is inherited behaviour, not new.

## 5. Standing note for whoever picks this up

- The `reserve_price` sidecar column is **not** per-zone. Any future locational
  claim needs `reserve_price_by_family` persisted from a replay; do not repeat
  the §2 mistake.
- 2025 is where the residual concentrates (9 vs 42) and is also where the
  measured NYCA reserve dual actually bites (66 hours, \$177 peak) — a 2025-led
  diagnosis will see the most signal, but any mechanism change is still scored
  leave-one-year-out within 2023–2025 (rule 22) before promotion.
- No out-of-training year was touched: NYISO carries no calibration-complete
  marker, so 2022 / 2019 / ≤2021 / H1-2026 remain quarantined.

## 6. nyiso-84 — the NYCA/East tier is ALSO closed, and the first gate was the pin

§4 redirected the lane at "the tiers whose published penalties are large enough
to reach it — NYCA 10-min/30-min (\$750) and 10-min spin (\$775), and East
10-min (\$775)". nyiso-84 (2026-07-27) tested that redirect and closed it. Two
results, in the order they were found:

**6a. The pin.** The East ladder was incomplete — the LRR posting prints THREE
East rows (spin_10 330 MW, total_10 1,200 MW, total_30 1,200 MW) and the model
carried only the 10-minute total. But the two missing families are **not \$775
tiers**: pinned from the Ancillary Services Manual §6.8 itself (current May-2026
issue, cross-checked against the July-2019 issue and the 2023 SOM p. A-132),
items 2 and 12 — East spinning and East 30-minute — are **\$40/MW** (\$25
before the July-2021 procurement enhancements). Only item 7, the East 10-minute
total already in the model, carries \$775. The handoff's premise that the
missing East families sit "in a tier that CAN price to the gate" was exactly the
assumption its own instruction ("pin before coding") caught. The families are
added anyway as `nyiso_east_reserve_families` (rule 14 — a real published
requirement), and the ladder-only arm is **bit-identical to the control** on
tail, reserve dual and class energy: the same idle-allowed inertness §4b proved
for the LI ladder, now demonstrated at the East tier.

**6b. The mechanism.** `nyiso_spin_reserve_online` generalizes the §4 gate to
the published SPINNING families — the product-definition driver (spinning
reserve is synchronized supply; an idle peaker cannot be spinning), applied to
`nyca_10min_spin` (655 MW, **\$775**) and `east_10min_spin` (330 MW, \$40) via
the same class-2 machinery (rule 19). Four arms, all three years, vs the
same-HEAD zero-delta control (id `2026-07-27-nyiso-84-{control,east-ladder,
spin-gate,east-gate}`):

| quantity (2023/2024/2025) | control | ladder | gate | ladder+gate |
|---|--:|--:|--:|--:|
| C3c h > \$300 (any zone) | 3/0/9 | 3/0/9 | 3/0/9 | **3/0/9** |
| reserve-dual h > \$0 | 22/6/66 | 22/6/66 | 652/800/1589 | **3248/3863/5525** |
| reserve-dual max | 12.5/28.1/177.3 | same | 12.5/63.4/177.3 | 13.5/63.4/177.2 |

The gate **works** — the \$775 NYCA spin family goes from never-binding to
binding 652–1,589 hours, the composed arm to 37–63 % of all hours, and it
forces real overnight GT commitment (CT_CHP +0.2–0.3 TWh, its evening/overnight
ratio dropping below 1) — and the tail **does not move by a single hour**. The
binding explodes in *breadth*, never in *depth*: the published curves are
shortfall ramps, and the model's synchronized supply (hydro + online
quick-start output) never falls deep enough short of 655/330 MW to climb them
anywhere near \$300. The reserve-dual maximum in every arm equals the
control's own.

**Therefore the reserve-tier route to C3c is closed in full**: the J/K ladders
are \$25-ceiling-blocked (§4), the missing East families are \$40 ceilings
(6a), and the \$750–775 NYCA/East families — even online-gated — price only
shallow ramp steps (6b). No published reserve demand curve forms the missing
>\$300 tail at hourly-LP granularity. What remains for the residual (model
3/0/9 vs RT actual 10/12/42) is what the SOM's own shortage accounting points
at: **RT-interval (5-minute) physical shortage pricing** — transient
ramp/contingency shortages the hourly LP structurally cannot see — plus the
commitment-side drivers (2025 LI steam OOM growth) that change what is online
when those intervals hit. A successor lane should start from that framing, not
from the reserve ladders.

Consequence for nyiso-82: its winter-spread disposition explicitly waited on
C3c movement; C3c did not move, so the winter-spread arm stays unarmed.

Disposition of the two flags: both stay **default-off**.
`nyiso_east_reserve_families` is a correct, probe-adjudicated-inert accuracy
fix (same standing as `nyiso_li_locational_reserve`). `nyiso_spin_reserve_online`
is structurally grounded on the requirement side but its supply side inherits
the class taxonomy's quick-start scoping — real NYISO spin is substantially
online CC/steam governor headroom, which the gate excludes, so arming it forces
GT commitment reality does not show. Widening the gated class to ramp-limited
online CC/steam headroom is the prerequisite for any promotion case, and with
C3c unmoved there is no promotion case to make.
