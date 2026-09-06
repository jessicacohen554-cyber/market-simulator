# DESIGN — capx D78: decouple the capacity OFFER from the EXIT decision at the sector-gate seam — a rate-based existing unit is IN the RPM stack at its cost-based (net-ACR) price; only its exit is exempt

**Lane:** capx D78 (director r#47, pack §D78), executing **owner ruling Q53 = READING 1**
(capx ledger §3, 2026-09-06: *"a sector-1 unit MUST STILL OFFER at its cost-based price; only
its exit decision is exempt"*). Charter inputs: `FINDING-capx-d58-2026-09-06.md` §3 (the seam at
the line) and §6 (the two readings); `DESIGN-capx-d53-sector-gate-2026-09-05.md` §1.8 (the claim
D58 refutes); `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §3.2 / §3.5 (the offer identity).
**Branch:** `claude/capx-d78-sector-gate-offer-seam-d1tfcd`, fresh off `origin/main` `ba894c9c`.
**Date:** 2026-09-06. **Model:** Fable. **DATA PROFILE:** `pjm`. **Phase 0 — ZERO LP — written
and pushed BEFORE any code.** Companion: `PRECOMMIT-capx-d78-sector-gate-offer-seam-2026-09-06.md`.

**NOTHING ARMS.** No new `ScenarioConfig` field (§3.4 says why), no default flip, no override,
no parameter value. The owner decides on the PRECOMMIT §7 flip condition.

---

## 0. The design in one paragraph

D58 proved at the line that one filter, `exempt_unit_ids`, does two jobs: it removes a unit from
the **exit decision** (what the D53 sector gate was designed to do) *and*, on an ISO where the
D57 capacity-supply clearing is armed, it removes the unit's accredited MW from the **sell-offer
stack** and drops it into the $0 price-taking block `Q_0` (what nobody designed). PJM's RPM has a
**must-offer requirement** for every Existing Generation Capacity Resource, with three enumerated
exceptions, **none of which is ownership** (§1). So a regulated-utility unit belongs in the stack
at its cost-based net-ACR price exactly as a merchant unit does; what differs is only that its
exit is an IRP / rate-case outcome rather than the auction's uncleared set. The ONE change (§3):
`apply_economic_retirements` gains a second id set, **`exit_exempt_unit_ids`**, whose members
have their margin **evaluated** and their accredited MW **offered** (they flow through the margin
loop and into `_settle_capacity_supply_clearing` unchanged) but are **partitioned out of
`margins` AFTER the clearing and BEFORE either decision rule** — never decided, latched,
pipelined, counted or retired. `evolve_fleet` routes the sector-gated set to that parameter
instead of unioning it into `exempt_unit_ids`; the dated-plant and this-year-retrofit
exemptions keep their existing semantics (§4). With the gate off the new set is empty and every
byte is identical; with the gate on and no clearing armed (MISO's keeper) every decision,
ledger row and cache key is identical; with the gate on and the clearing armed (PJM) the stack
returns to the control's — which is the pre-declared identity the PRECOMMIT grades.

---

## 1. The market rule, cited (phase-0 item 1)

Source: PJM Manual 18 *PJM Capacity Market*, **Revision 62, effective 2025-12-17**, re-fetched
this session from `https://www.pjm.com/-/media/DotCom/documents/manuals/m18.ashx`, **sha256
`f188c587d5e00112e5dfa1ab84a793cb335f72bf82b23caa31c488fe8e929bfa`, 289 pp. — byte-identical to
the copy D54 §8 hashed.** Page numbers are the PDF's; printed numbers are one lower.

1. **Who must offer (the must-offer requirement).** §1.2, p.14: *"Participation is mandatory for
   resource providers with: • Available unforced capacity from Existing Generation Capacity
   Resources located within the PJM market footprint; or • Bilateral contracts for available
   unit-specific Capacity Resources that are Existing Generation Capacity Resources located
   within the PJM market footprint."* and *"Generation is treated as existing for the purpose
   of must-offer requirement and mitigation provisions when the generation is (a) in service at
   the commencement of an RPM Auction or (b) not yet in service but has cleared an RPM Auction
   for any prior Delivery Year."* §5.4.1, p.124: *"Each Existing Generation Capacity Resource
   with available capacity that is capable or can reasonably become capable of qualifying as a
   Capacity Performance Resource must submit a Capacity Performance sell offer segment."*
   Tariff basis: Attachment DD §6.6 (cited through D54 §2 item 1). **The rule keys on
   *existing* and *located in the footprint*; it does not key on ownership, rate base, sector
   or self-supply.** A rate-based IOU unit and a merchant IPP unit are the same object under it.
2. **Who may be excused.** §5.4.1, p.124–125: *"Exceptions to the capacity performance
   must-offer requirement will be permitted for a generation capacity resource which the
   Capacity Market Seller demonstrates is [a] reasonably expected to be physically incapable of
   satisfying the requirements for a Capacity Performance Generation Resource by the start of
   the Delivery Year, [b] the resource has a financially and physically firm commitment to an
   external sale of its capacity, or [c] the resource is seeking to remove Capacity Resource
   status in accordance with Section 5.4.7 of this manual."* (Timing was added as an acceptable
   reason at Rev. 5x, p.278 change log; Hybrid Resources at Rev. 52, p.274.) **Three
   exceptions, enumerated, and "my exit is decided by my regulator" is not one of them.** The
   deactivation route is exception [c]: §5.4.7, p.131, *"A Capacity Market Seller seeking to
   remove Capacity Resource status from a Generation Capacity Resource shall submit a
   preliminary and final written request to PJM and the IMM … in accordance with Tariff,
   Attachment DD, section 6.6(g)"* — preliminary by September 1 and final by December 1 before
   the BRA (p.120–121 timeline), and once removed the unit *"will be removed from the Capacity
   Resource model and no longer eligible to offer in RPM auctions"* (D54 §2 item 1, same
   section). The FRR carve-out (an FRR Entity's plan resources are outside RPM) is a
   *portfolio* election, not a unit exception, and the model's stack and requirement are
   RTO-wide on both sides (D54 §4.6) — it is not what the sector gate partitions on and it is
   not touched here.
3. **What a cost-based offer is.** §5.4.1 (Rev. 52 text carried in D54 §2 item 2): a sell offer
   *"greater than $0/MW-Day must seek a unit-specific exception request … by submitting
   Avoidable Cost Rate data … or may, at its election, utilize an offer cap based on the default
   gross Avoidable Cost Rate of the applicable resource type"*; the cap is the **net ACR** =
   gross ACR (the avoidable cost *"assuming the unit would otherwise retire"*, §5.4.4, Att DD
   §6.8) **minus** Projected PJM Market Revenues (the three-year rolling E&AS net revenue,
   §5.4.4 / Att DD §6.8(d)); default gross ACR by class in §5.4.8.4(B) (committed at
   `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv`). And **mitigation applies to
   everyone**: the RTO failed the three-pivotal-supplier test in every BRA of the window, so
   every existing resource's effective offer is `min(cap, submitted)` ≤ its net ACR (D54 §2
   item 4, the 2022/23 BRA Report p.4). This is what licenses the model's use of the cap **as**
   the offer: `offer_g = max(0, GFC_g − EAS_g) / (A_g × 365)` (D54 §3.2), and it is the same
   formula for a utility unit as for a merchant one — the ACR categories (Att DD §6.8) are
   plant-cost categories, not ownership categories.
4. **What consequence the rule has for the model, stated.** Under the current code a gated unit
   is *un-offered*; under §5.7.1 (p.146) un-offered existing MW *"shall be excluded from
   participation in any and all Incremental Auctions"* and are paid nothing — the auction's own
   treatment of a unit that silently fails to offer is *not* "cleared at $0". Modelling 34.2 GW
   of rate-based capacity as $0 price-taker supply therefore misstates the published supply
   curve in BOTH directions the rule names: it credits the units with clearing when the rule
   would have them offer at their cap (and possibly not clear), and it depresses the price the
   merchant fleet is settled at. **Reading 1 is the market rule; reading 2 (D58 §6 item 2) is
   an inference from exit economics that the tariff does not make.** The owner ruled reading 1.

**Rule 13 / 14 discipline.** The must-offer requirement, its exceptions and the ACR cap are
published market-design facts that regenerate for any forward delivery year; nothing here is a
measured outcome or a residual. The BRA record (offered / cleared / uncleared UCAP, Tables 6–7)
remains a validation observable, never a target.

---

## 2. The seam at the line, and every consumer it touches (phase-0 item 2)

### 2.1 Where the two jobs are done by one filter (HEAD `ba894c9c`)

```
evolve.py:670    exempt_unit_ids=_retrofitted_ids | _dated_exempt | _sector_exempt,
retirements.py:3225   if g.unit_id in exempt_unit_ids: continue    # the ONLY consumer inside the screen
retirements.py:3536   margins.append((g, net_revenue, going_forward_cost))   # what the skip empties
retirements.py:2861   for g, eas, gfc in margins:                  # the D57 stack is built from `margins`
retirements.py:2870       offer = max(0.0, gfc - eas) / (a_mw * 365.0)
retirements.py:2874   price_takers_mw = max(0.0, accredited_total_mw - offered_mw)   # the residual
```

`accredited_total_mw` (`:2838`) is the WHOLE fleet's ledger (`accredited_firm_capacity_mw`), so a
unit absent from `margins` is present in the census and lands in `Q_0` by subtraction. That is
D54 §3.2's rule *"every accredited MW the ledger counts enters the stack exactly once"* doing
exactly what it says — the defect is upstream, in *which* units reach `margins`.

### 2.2 Every consumer of `exempt_unit_ids`

| # | consumer | what it does today | under this design |
|---|---|---|---|
| E1 | `apply_economic_retirements`, the candidate loop `:3225` | skips the unit entirely: no margin, no offer, no detail row, no decision | **unchanged** for its remaining members (dated plants, this-year retrofits) |
| E2 | `evolve_fleet` `:670` — the ONE call site | passes the three-way union | passes `_retrofitted_ids \| _dated_exempt`; `_sector_exempt` goes to the NEW parameter |
| E3 | tests `test_capacity.py` `:5665`, `:7071`, `:7157` | the spy on the union; the direct-call test | the spy asserts the two parameters separately; the direct-call test keeps `exempt_unit_ids` for what it still means and a new test covers the new parameter |

There is no other reader: the name does not appear in `pipeline/`, `runner.py`, the harness, or
any data module (grep at HEAD).

### 2.3 Every consumer of `margins` (and of `margin_detail`)

| # | consumer | reads | under this design |
|---|---|---|---|
| M1 | `_settle_capacity_supply_clearing` `:3600` → offer stack `:2861`, settlement `:2884`, `margin_detail` capacity fields `:2895` | the FULL `margins` | **unchanged code**; now sees the gated units too, so they OFFER and are SETTLED (a cleared gated unit's `net_revenue` carries the clearing price — decision-neutral, since it never reaches a decision) |
| M2 | the `_screen_stack` revenue-side audit line `:3645` (log only, no ledger, no decision) | `margins` | reads the **decision** partition, so the MISO keeper's log line is byte-identical |
| M3 | `_apply_pipeline_retirements` `:3687` (`retirement_rule="pipeline"`): latch, candidates, admission cap, execution | `margins` + `margin_detail` by unit id | reads the **decision** partition: a gated unit is never `decided` / `entry_capped` / `re_confirmed` / `reversed` / `executed`, never in `state`, never in the floor's `new_units`; its `margin_detail` row exists but is read by nothing (rows are emitted only for decision units) |
| M4 | the legacy loop `:3708` (`retirement_rule="legacy"`) | `margins` | reads the **decision** partition: no loss-counter change for a gated unit |
| M5 | `event_sink["capacity_clearing"]` `:3613` → `evolve.py:680` ledger `capacity_clearing` (`as_ledger`: `n_offers`, `offered_mw`, `price_takers_mw`, `offer_stack`, …) | the clearing object | **records the repaired stack** — the gated units' rows appear in `offer_stack` with their cleared flag; `n_offers` / `price_takers_mw` return to the control's |
| M6 | `evolve.py:678` `entry_reserve_position = _clearing.as_price()` → the thermal-entry and storage price takers | the clearing price | sees the repaired price (the control's) |

**So the decoupling is ONE seam:** the partition point *after* M1 and *before* M2–M4. M1, M5 and
M6 change no code and read the repaired stack by construction; M2–M4 change no code and read the
decision partition; E1 is untouched; E2 routes one set to one new parameter. The stack, the
settlement, the identity `Q_0 + Σ A_g == accredited` (D54 §3.6 I1), the pipeline, the cap, the
lag, the floor and both decision rules are all untouched code.

### 2.4 The corrected identity (D54 §3.5 I2, restated under reading 1)

D54 §3.5: *"the failing set of the screen is exactly the uncleared set of the auction."* Under
the sector gate that identity is a statement about the **merchant** (screened, decision-facing)
fleet: **the screen's failing set = the uncleared set restricted to the decision partition.** A
gated unit that the auction does not clear is *uncleared and retained* — it is un-paid capacity
that stays in service by its owner's plan, which is what a rate-based uncleared unit is in RPM
(its cost recovery is the rate base, not the RCP). The quantity is observable from the ledger
(`offer_stack` rows joined to the sector map) and the FINDING reports it as **"sector-1
uncleared, retained"**; it is not a defect and not a floor — no unit is forced by it.

### 2.5 What `sector_gated_unit_ids` and the census do not change

`sector_gated_unit_ids` (`retirements.py:782`) is unchanged: same key (`plant_code`), same plant
grain, same fail-open on an absent plant, same census block `sector_gated`. The census counts
exactly the units the gate moves; what moves *where* is now the exit decision only.

---

## 3. THE MECHANISM — stated so the build has no design choices

### 3.1 The parameter

`apply_economic_retirements(..., exempt_unit_ids: frozenset[str] = frozenset(),
exit_exempt_unit_ids: frozenset[str] = frozenset(), ...)`:

- `exempt_unit_ids` — **unchanged meaning**: *out of the screen entirely* — no margin, no
  offer (a $0 price taker in `Q_0` under the clearing, by the existing residual), no decision.
  Members at HEAD: this-year CCS retrofits (W2-C) and pending dated plants (D42/D44).
- `exit_exempt_unit_ids` — **new**: *in the screen's evaluation and in the auction, out of the
  exit decision*. Its margin is computed on the identical code path; its accredited MW is
  offered at `max(0, GFC − EAS)/(A_g × 365)`; it is settled; it is then removed from `margins`
  before the decision rule. Members: the sector-gated set (D53) when `retirement_sector_gate`
  is on. A unit in both sets is treated as `exempt_unit_ids` (the stronger exemption wins; the
  loop's skip fires first).

### 3.2 The partition point

Immediately after the D57 block (`:3599–3613`) and the D74 ledger block, before `_screen_stack`:

```
if exit_exempt_unit_ids:
    margins = [m for m in margins if m[0].unit_id not in exit_exempt_unit_ids]
```

Nothing else in the function moves. `margin_detail` keeps its rows for every evaluated unit
(diagnostic; read only by decision rows). The clearing has already run on the full list and its
result is already in `event_sink`.

### 3.3 The call site

`evolve.py:670`: `exempt_unit_ids=_retrofitted_ids | _dated_exempt`,
`exit_exempt_unit_ids=_sector_exempt`. The D53 comment block above it is amended to say what
the seam now is; the `sector_gated` ledger block is unchanged.

### 3.4 No new field — this IS the gate's correct semantics (phase-0 item PHASE 1)

`retirement_sector_gate` was designed as *"a partition of who faces an exit decision"* (D53 §1.2)
and was measured on MISO as exactly that (D53 §6, four limbs met). Its reaching the offer stack on
PJM was a seam D53 *"did not build for"* (D58 §3.1), not a second declared behaviour. Reading 1
restores the field to its own definition; on every armed configuration that exists (MISO's
`miso-t1h` keeper, clearing off) it is byte-identical. A second gate would be a re-armable answer
key for a behaviour the tariff does not contain (rule 26 `[R-DELETE]` in spirit; rule 24
`[R-REGISTRY]` unviolated: no tunable changes, no new tunable appears). **No new field, no new
cache-key registration, no matrix row** — rule 28(c) is not triggered; rule 28(b) (the cell
update in PJM's shard) is.

**Cache-key consequence, stated.** Because the field is unchanged, the arm's key at HEAD is the
same key D58's arm resolved to at HEAD (`bc387828f931e0ac` full span, `d527c3299b8c00b5` screen
span — PRECOMMIT §5). That is a **same-key semantic change** for `retirement_sector_gate=True`
on a clearing-armed ISO. Its blast radius is **zero committed bundles**: D58's two screen bundles
were deleted before merge (rule 29(c)), no PJM run has ever been registered with the gate on, and
every MISO bundle with the gate on has the clearing off and is byte-identical. The
`results/cache.py` epoch ledger receives one entry saying exactly this, in the build commit.

### 3.5 Composition with D74 (the other price-taker convention on the same loop)

D74's no-default-cap convention exempts a unit **by class × delivery year** through its own
predicate, *before* `margins`, and puts it in `Q_0` at $0. That is the rule's own text — a unit
with no default cap and no ACR filing offers at $0 (§5.4.1) — so it is **correct as built and is
not this seam**. The loop order is: `exempt_unit_ids` skip → D74 class skip → margin. Under both
gates a sector-1 Steam-Oil-&-Gas unit therefore reaches the D74 branch (it no longer short-circuits
on the sector filter) and is a $0 price taker **because of its class, not its owner** — the
intended composition, and the only observable change to D74's ledger block, which occurs on no
configuration either lane has solved (D74's legs run with the sector gate off).

### 3.6 Invariants the build asserts (tests, beside `TestRetirementSectorGate`)

- **T1 off-gate byte-identity:** `exit_exempt_unit_ids=frozenset()` ⇒ every return value, every
  `event_sink` key and the cache key identical (the default).
- **T2 MISO byte-identity (clearing OFF):** on a toy fleet with a failing sector-1 unit, moving it
  from `exempt_unit_ids` to `exit_exempt_unit_ids` changes nothing in `pipeline_events`,
  `retired`, `floor_retained`, the pipeline state or the survivors (pipeline AND legacy rules).
- **T3 PJM toy-stack identity (clearing ON):** with a sector-1 unit in `exit_exempt_unit_ids`,
  `capacity_clearing.n_offers` / `offered_mw` / `price_takers_mw` / price equal the un-gated
  run's; the unit appears in `offer_stack`; it has no `pipeline_events` row; the merchant units'
  rows are identical to the un-gated run's. Against `exempt_unit_ids` the same unit is absent
  from the stack and `price_takers_mw` rises by its `A_g` (the D58 seam, reproduced on a toy).
- **T4 evolve routing:** the spy sees `exempt_unit_ids == dated ∪ retrofit` and
  `exit_exempt_unit_ids == sector` when armed; `exit_exempt_unit_ids == ∅` when off; the
  `sector_gated` census unchanged.
- **T5 uncleared-and-retained:** a gated unit whose offer exceeds the clearing price is uncleared,
  earns $0, and survives with no state entry.

### 3.7 DOF ledger — zero

No number. A unit's offer is the D54 formula on the D62/ATB bar and its own E&AS; the partition is
D53's published boolean. Nothing can be identified against a residual.

---

## 4. Is the seam reachable by any OTHER exemption channel? (phase-0 item 4)

The residual construction reaches **every** id that is in the accredited ledger and not in
`margins`. Channel by channel, with the rule:

| channel | in the fleet in the screen year? | in `margins` today? | what the rule says | decision here |
|---|---|---|---|---|
| **Step 0 confirmed exits** (`apply_confirmed_exits`, instrument-bound) and **step 1 / 1b announced & owner-filed dates** *executed this year* | **No** — removed from the fleet before step 3 (evolve steps 0–1) | n/a — absent from the census AND the stack | Exception [c] / §5.4.7: a resource whose removal of Capacity Resource status is effective for the delivery year is *"no longer eligible to offer"*. Absent is correct. | **Not reachable; correct as built.** |
| **Step 1b dated plants still PENDING** (`dated_plant_unit_ids`, D42/D44) — filed date later than the delivery year | Yes | **No** → `Q_0` at $0 | Must offer for every delivery year before the removal is effective (§1.2; D54 §4.2 states this and chose *"does not submit a price-forming offer"* as the design reading, with the bias stated: price DOWN, cleared UP, second-order in the window) | **Reachable by the identical mechanism; NOT moved by this lane.** Q53 ruled on the sector gate; D54 §4.2 is a landed, armed design reading with its own stated consequence and the D57 record measured on it; and the charter's pre-declared identities pin `price_takers_mw` to the control's, which contains this block. The fix, if the owner wants it, is one line — route `_dated_exempt` to `exit_exempt_unit_ids` — and it is **routed as a D57-family card** (D58 §6 item 4 already named it) with its magnitude reported from the arm's ledger where the record allows (§4.1). |
| **This-year CCS retrofit** (W2-C, `_retrofitted_ids`) | Yes | No → `Q_0` | A retrofitted unit is an existing resource and must offer; the model has no post-retrofit E&AS for it in the retrofit year (the incoherence W2-C names) | **Reachable; inert in every backcast / hindcast / crossover year** (below `ccs_retrofit_available_year` = 2028 by construction). Same one-line fix available; routed with the dated card, not built. |
| **D74 no-default-cap class** | Yes | No → `Q_0` | §5.4.1: no filing and no default cap ⇒ a $0 offer | **Correct as built** (§3.5); composes. |
| **Units with `_thermal_firm_mw == 0`** or no dispatch rows / no `_THERMAL_FOM` entry | Yes | No | outside the stack: nothing to offer, or not a screened class (VRE / hydro / storage enter `Q_0` on their ledger credit by design) | **Correct as built** (D54 §3.2 table). |

### 4.1 What this lane will report about the dated block, without moving it

The control's `price_takers_mw` (30,577.9 MW in 2022) is VRE + hydro + storage + imports + DR +
dated plants + retrofits. The dated component is not separable from the committed ledgers (a dated
unit has no `margins` row and the `sector_gated` block does not cover it); the FINDING will report
the **count and nameplate MW of pending dated thermal units** in the 2022 fleet from the same-HEAD
control's `announced_derates` / fleet census where that record allows, so the D57-family card
carries a size. No solve is spent on it.

---

## 5. What the design does not do (stated limits)

- It does not change any offer's *value*: the D62 published bar / ATB bar, the E&AS operand, the
  D48 accreditation basis and the VRR curve are untouched. It changes only *who is in the stack*.
- It does not model the FRR carve-out or self-supply hedges (D54 §4.6): a utility unit in an FRR
  plan is outside RPM in reality and inside the model's RTO-wide stack — as it was under D57 for
  every un-gated run. The sector attribute is not an FRR flag and is not used as one.
- It does not move the dated-plant or retrofit exemptions (§4).
- It does not change the sector gate's *exit* semantics on any ISO: what MISO measured (D53) is
  what the gate still does.

---

## 6. Rules, stated

Rule 1 `[R-STRUCT]` — the mechanism is the tariff's must-offer rule, chosen on the text (§1), and
the PRECOMMIT's gates are identities, never a band. Rule 13 / 14 — published market design,
forward-regenerating; the sign line (exits can only fall or stay under a candidate-set gate) is
restated before the solve and the D58 inversion is the defect it diagnoses. Rule 19
`[R-ONE-MECH]` — the D58 violation (one filter, two jobs) is removed: exit candidacy and capacity
offering are two declarations on two parameters, each with one consumer set (§2). Rule 21 — zero
DOF. Rule 22 — the screen and the full window are 2021–2025 hindcasts in forecast mode; no
out-of-training year is solved, scored or registered. Rule 24 / 25 — no new tunable; PJM's cell
carries PJM's own measured letter, MISO's stays. Rule 27 — every ≥300-line file (`retirements.py`,
`evolve.py`, `test_capacity.py`, the shard) is edited locally and blob-verified after push. Rule
28 — cell update in PJM's shard only (b); no new row (c not triggered). Rule 29 — phase 0 is this
document (zero LP); the screen year is D58's own, named in the PRECOMMIT from the seam's measured
footprint (34,172.4 MW and the only year the price moved), never from a residual; STOP-only
structural gates; bundles deleted before merge.

## 7. Collision register (this lane's writes)

`src/market_sim/model/capacity_evolution/retirements.py` (the signature, the docstring, the
partition line — **not** the D57 clearing function, **not** the D62 bar seam, **not** the D74
class skip, **not** the D67 requirement seam), `evolve.py` (the one call site and its comment),
`results/cache.py` (one epoch entry), `tests/unit/model/test_capacity.py`
(`TestRetirementSectorGate`), the PJM matrix shard cell, `docs/handoffs/` (this design, the
PRECOMMIT, the FINDING, `d78/` instruments, a dated cross-reference appended to D53 §1.8 and D54
§3.2 / §4.7 — never a rewrite), the capx ledger row. D74's screen has NOT landed on main at this
lane's start (its build has: `64477801`, `be313ecd`, `18213f28`, `#5114`; no FINDING, no open PR;
the ledger marks that session idle) — the hunks the hold protected are on main and the lane
rebases onto any D74 landing between legs, never dropping its hunk (PRECOMMIT §0).
