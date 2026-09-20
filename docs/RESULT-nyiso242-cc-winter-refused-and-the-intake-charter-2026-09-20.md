# RESULT — nyiso-242 items 1 & 3: `cc_winter_capability_basis` is REFUSED on NYISO's own data, and the CAMPD identification route this session proposed is REFUTED BY ITS OWN FEASIBILITY TEST

**Session** nyiso-242 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container, no shard launched**).
**Date** 2026-09-20. **Owner instruction** (this session, verbatim): *"1 and 3"* — charter the identification intake, and measure `cc_winter_capability_basis`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, **UNCHANGED. Nothing armed, nothing registered, no `ScenarioConfig` field moves.**
**Predecessor** `docs/FINDING-nyiso242-the-2022-tail-is-not-reachable-from-price-formation-2026-09-20.md`.

> ## HEADLINE
> 1. **ITEM 3 — `cc_winter_capability_basis` `U` → `G`, refused ex ante on TWO independent legs,
>    both measured on NYISO's own published ratings and its own fleet arrays** (rule 25
>    `[R-ISO-SCOPE]`: CAISO's refusal never fills this cell, and none of CAISO's numbers were
>    carried). **REACH:** it removes **263.6 MW of 12,648 MW** of CC nameplate off-summer — **2.1 %
>    of the fleet and 5.6 % of the ~4.7 GW the tail object requires** — and it is two-directional,
>    with **15 of 40 plants GAINING** capacity. **ADMISSIBILITY:** the rule 19 `[R-ONE-MECH]`
>    double count that killed it at CAISO is present here and **bites on half the fleet** —
>    published off-summer rating headroom is **3.23 %** median against a WEFOR the keeper already
>    applies at **3.79 %** capacity-weighted, with **20 of 40 plants under water**.
> 2. **ITEM 1 — THE CHARTER I WAS ASKED TO ISSUE IS NOT THE CHARTER THAT SURVIVED THE
>    MEASUREMENT.** I proposed a CAMPD cold-hour availability census as the identification.
>    **I ran the feasibility test first, and it refutes my own design.** The identification
>    rested on "at $383/MWh every available unit is economic, so a unit metering zero was
>    unavailable". That premise fails its own discriminator: the CAMPD fleet sits at
>    **50.0 / 50.9 / 49.8 / 50.1 %** of its demonstrated ceiling in hours where the DA price
>    exceeded $300 / $200 / $150 / $100, and at **51.5 %** in anticipated RT-extreme hours against
>    **52.4 %** in surprises. **Flat across every price condition and every anticipation
>    condition.** That is a fleet coincidence factor, not a cold-snap availability signal.
> 3. **The headline number that looked decisive is therefore WITHDRAWN as an identification.**
>    4,575.8 MW believed-available-but-not-metering in the 70 winter extreme hours — which
>    matched the 4,716 MW reachability requirement to within 3 % — **is not evidence of
>    unavailability.** The match is real and it is a coincidence of two ways of measuring the same
>    unused headroom. Reported at full magnitude rather than quietly dropped, because it is
>    exactly the number a successor would otherwise rediscover and act on.
> 4. **What the charter should actually ask for is therefore NARROWER and better aimed**, and it
>    now carries a pre-registered kill test derived from a real refutation (§3.4): the source must
>    state **availability directly**, because CAMPD states **operation**, and operation cannot
>    separate "not available" from "not dispatched", "not committed day-ahead" or "held as
>    reserve".

---

## 1. ITEM 3 — `cc_winter_capability_basis`, measured on NYISO

The cell was `U` in `mechanism-matrix/NYISO.js:132` **with no evidence string at all** — the one
untested member of the NYISO winter/availability family, which is why it was worth the owner's
pick. The shared field carries an in-code refusal (`scenarios.py:15239`, *"REFUSED AT CAISO —
ARMED BY NO KEEPER, DO NOT ARM WITHOUT READING THIS"*), but rule 25 `[R-ISO-SCOPE]` means that
verdict can never fill NYISO's cell. So the caiso-185/186 test was reproduced on NYISO's fleet.

Probe `scripts/probes/nyiso242_cc_winter_capability.py` → `_nyiso242_cc_winter.json`.

### 1.1 Leg A — reach and direction

40 of the keeper's 41 CC plants carry both published EIA-860 ratings. `winter / nameplate`:

| statistic | value |
|---|---:|
| min | 0.7433 (plant 50292) |
| median | **0.9677** |
| max | 1.0824 (plant 55375) |
| plants below 1.0 | 25 |
| **plants at or above 1.0** | **15** |
| **off-summer MW removed, fleet-wide** | **263.6** |
| fleet CC nameplate | 12,648.0 |

**263.6 MW against an object that requires ~4,716 MW** (the idle sub-gate capacity measured in
the predecessor finding) — **5.6 %**. And it is a basis swap, not a haircut: 15 plants *gain*
off-summer capability, which is the wrong direction for this object. Even granting the mechanism
everything, it does not reach.

### 1.2 Leg B — admissibility, which is a precondition and not a residual

caiso-186's `G-NOCONTRA` refusal is a rule 19 `[R-ONE-MECH]` double count, stated in the field's
own comment: *"the rating headroom and the statistical WEFOR are two mechanisms doing one job,
and they must be reconciled BEFORE any published-rating capacity basis is admissible."* In a
historic backcast a CC unit's availability starts at `1 − WEFOR`, and where `wefor_residual is
None` that statistical WEFOR applies **on top of** the CAMPD outage overlay which already carries
every real outage. Nameplate headroom over the published rating silently absorbs it; remove the
headroom and the model asserts an incapability the CEMS record refutes.

The NYISO keeper carries `wefor_residual = None` and `cc_nameplate_summer_derate = True`, so the
trigger is present. **Whether it BITES was measured on NYISO's own fleet arrays** rather than
assumed from CAISO's 3.5 %:

| quantity | NYISO measured |
|---|---:|
| CC rows carrying a WEFOR floor | **238 of 238** (none reaches availability 1.0 off-summer) |
| applied WEFOR, median | 3.50 % |
| applied WEFOR, capacity-weighted | **3.79 %** |
| published off-summer rating headroom, median | **3.23 %** |
| **CC plants whose headroom is LESS than the applied WEFOR** | **20 of 40** |

The headroom does not cover the WEFOR for half the fleet. **The precondition the field's own
comment sets is not met on NYISO**, and it is not met for the same structural reason it was not
met on CAISO — which is a shared-field defect, not a transferred verdict.

### 1.3 Verdict

**`U` → `G` (governance-refused), ex ante, no solve.** Refused on reach *and* on a rule 19
precondition, either of which is sufficient. Recorded with a re-open condition: the cell becomes
live if and only if the WEFOR / rating-headroom double count is reconciled at the shared-field
level (`wefor_residual` set for the overlay-covered CC classes, or the equivalent), **and** some
object exists that 263.6 MW of two-directional off-summer basis change could plausibly move.
Neither holds today.

---

## 2. ITEM 1 — the intake charter, and the feasibility test that reshaped it

### 2.1 What I proposed, stated as I proposed it

From this session's earlier report: *"measured NYISO winter forced-outage / derate data (GADS,
the ISO's own outage postings, or a CAMPD-based cold-hour availability census) capable of setting
the magnitude from something other than the residual."* The CAMPD route was the attractive one —
the data is already in the repo, it costs nothing to acquire, and the identification design was
clean on its face:

> In an hour when the real market cleared at $300–750/MWh, every available thermal unit was
> economic. So a unit metering **zero** in CAMPD during such an hour was **unavailable**, not
> un-economic. The magnitude then comes from the ISO's own realized price and the EPA's own
> meter, never from the model's residual.

**A charter issued on that premise without testing it would have cost a session and produced
nothing.** So the premise was tested first. Probe
`scripts/probes/nyiso242_coldhour_identification.py` → `_nyiso242_coldhour_identification.json`.

### 2.2 The raw measurement, which looked conclusive

In the 70 winter hours where the actual RT hub cleared above $300 (median $383):

| | |
|---|---:|
| plants compared | 55 |
| **plants metering EXACTLY ZERO while the model believed them available** | **30** |
| their believed-available capacity | **2,779.5 MW** |
| total believed-minus-observed gap | **4,575.8 MW** |

Against the predecessor finding's requirement — **4,716 MW** of idle sub-gate capacity must
disappear for the energy dual to reach $300 — that is a **3 % match** from a completely
independent instrument. It is the kind of convergence that reads as confirmation.

It is not. §2.3 is why.

### 2.3 THE DISCRIMINATOR, and it refutes the design

A gap measured only in extreme-price hours has three candidate causes, and the raw number
separates none of them:

1. **genuine unavailability** — the mechanism;
2. **day-ahead commitment lag** — NYISO's 2022 DA tail is **10 hours against an RT tail of 101**,
   so 97 of the 101 extreme RT hours were *not* anticipated day-ahead, and a slow-start unit not
   committed in DA cannot be online for a surprise RT spike;
3. **reserve holding** — a fast-start CT meters zero *precisely because* it is available and
   being held as 10-minute reserve.

Conditioning on the **DA** price separates (1) from (2): in hours the DA market anticipated,
commitment lag cannot be the excuse. And a genuine availability signal must **deepen with price**.
Measured, as the fleet's delivered MW against its own demonstrated p999 ceiling:

| window | hours | RT median | DA median | **CAMPD % of own p999** |
|---|---:|---:|---:|---:|
| DA > $300 | 10 | 277.6 | 329.3 | **50.0 %** |
| DA > $200 | 114 | 176.1 | 236.9 | **50.9 %** |
| DA > $150 | 465 | 160.1 | 178.7 | **49.8 %** |
| DA > $100 | 1,550 | 120.3 | 128.5 | **50.1 %** |
| RT > $300, DA anticipated | 4 | 347.2 | 361.4 | 51.5 % |
| RT > $300, DA surprise | 97 | 374.5 | 162.9 | 52.4 % |
| ordinary (RT below median) | 4,380 | 42.8 | 47.6 | 32.6 % |

**Flat at ~50 % across every price condition and every anticipation condition.** It does not
deepen with price, and anticipated hours look identical to surprises. Corroborated by `opTime`:
**70.8 %** of unit-hours are full stops in the extreme hours against **77.5 %** across all 8,760 —
*more* of the fleet running when prices are high, as economics predicts, and modestly so.

**This is a fleet coincidence factor against a single-hour annual peak, not a cold-snap
availability signal.** The 4,575.8 MW is real as arithmetic and empty as an identification, and
its 3 % agreement with the reachability requirement is two ways of measuring the same unused
headroom, not two confirmations of one cause.

### 2.4 It also converges with nyiso-227, which I should have weighted more heavily at the outset

`FINDING-nyiso227-shortgas-outage-inert-2026-09-11.md` derived NYISO's whole sub-5-day CAMPD
outage family — the layer `UNIT_OUTAGE_MIN_DAYS = 5` makes invisible, i.e. exactly the cold-snap
duration — at **208.2 / 191.5 / 280.7 MW annual-mean** for 2023/24/25, peak 1,653–2,351 MW, and
measured **0 binding hours on ST_GAS** with 1,280–2,207 MW of unused headroom. Two caveats I
raised against extending it were legitimate and both are now answered: it never measured **2022**
(the year holding the events), and its screen was annual rather than conditioned on the extreme
hours. **The price-conditioned 2022 test above is the stronger version of nyiso-227's screen and
returns the same verdict.** The class split does not rescue it either — excluding ST_GAS/ST_CHP
(the scope of the `NYISO.js:121` blanket DO-NOT-REDO) still leaves 3,024 MW of gap and 2,296 MW
of zero-metered capacity, but §2.3 says that quantity identifies nothing regardless of which
class carries it.

### 2.5 THE CHARTER, as it should now be written

**Do not commission a CAMPD cold-hour availability census.** This session ran it; it does not
identify. That refutation is the charter's most useful content.

**The intake must state AVAILABILITY, not OPERATION.** CAMPD meters what ran. Every route from
"what ran" to "what could have run" passes through dispatch, commitment and reserve holding,
and §2.3 shows those dominate. Sources that state availability directly:

| source | what it states | obtainable? |
|---|---|---|
| NYISO Outage Scheduler / actual outage postings | scheduled + forced outages by unit and window | **the first thing to check** — NYISO publishes outage data; coverage and unit-level granularity are the open questions |
| NERC GADS | unit-level forced-outage events with cause codes | aggregated/confidential in general release; per-unit likely unavailable |
| NYISO SOM appendices | event-level forced-outage MW during named cold snaps | published, but aggregate — sizes the object, cannot key a per-unit derate |

**The pre-registered kill test, derived from this session's refutation, and it binds before any
solve.** Whatever source is used, the derived derate must **deepen with price**: the model's
believed-available capacity net of the new derate must fall, relative to its own ordinary-hour
level, by materially more in extreme-price hours than in ordinary ones — and by more in
DA-anticipated extreme hours than the flat ~50 % baseline above. **A derate that is flat across
price conditions is the same non-identification this session just refuted, and it is refused at
the gate rather than solved.** This is the `G-NOCONTRA`-style bar caiso-186 used, aimed at the
failure mode actually measured here.

**And the honest expected value, stated up front rather than after:** even a correctly identified
derate must remove on the order of **4.7 GW** in those hours to move the energy dual, against a
sub-5-day CAMPD family that peaks at 2.4 GW and an ST_GAS leg already closed. The charter is
worth issuing because the object is worth $5.44/MWh and nothing else reaches it — **not** because
success is likely. A successor should expect to refute rather than to arm, and should budget a
zero-LP feasibility pass before any shard, exactly as this session did.

---

## 3. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — nothing was selected on a residual. Item 3 was refused on reach and on
  a structural precondition; item 1's design was refused on its own pre-stated discriminator.
  The 4,575.8 MW that *supported* the design is reported at full magnitude alongside its
  refutation rather than dropped.
* **Rule 19 `[R-ONE-MECH]`** — item 3's refusal IS a rule 19 finding. Item 1 asked, before
  proposing anything new, whether the existing `campd_outage_windows` / `unit_outage_short_windows`
  family already owns the phenomenon; §2.4 answers that it does and that the family is measured
  near-inert.
* **Rule 25 `[R-ISO-SCOPE]`** — CAISO's `R` on `cc_winter_capability_basis` was read and **not**
  carried; every NYISO number here is derived from NYISO's own ratings, arrays and meter.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (b) discharged: `cc_winter_capability_basis` `U` → `G`
  with its citation, in this session, in NYISO's own shard. No other cell moves;
  `unit_outage_short_windows`/`_gas` stay `I` (this session corroborates them on a new year and a
  new test, which is not a verdict change).
* **Rules 21 / 24** — zero free parameters, zero new literals, no `ScenarioConfig` field touched.
* **Rules 32 / 34** — zero LP, no shard; §2.5 states why launching one would not have backed a
  promotion.
* **Rule 31 `[R-RETAIN]`** — nothing deleted; no bundles were produced.
* **Rule 15 `[R-DASHBOARD]`** — no run produced, nothing to register; the keeper's dashboard entry
  is untouched.

**Artefacts.** `scripts/probes/nyiso242_cc_winter_capability.py` → `_nyiso242_cc_winter.json`;
`scripts/probes/nyiso242_coldhour_identification.py` → `_nyiso242_coldhour_identification.json`.
Both re-runnable against the committed keeper at zero LP.
