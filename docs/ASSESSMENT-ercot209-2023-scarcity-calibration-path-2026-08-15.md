# ASSESSMENT — ercot-209: where the ERCOT backcast workstream actually is, and every route to a calibrated 2023 scarcity backcast

> Status: RECORD — for the owner. **NOTHING IS DECIDED HERE.** Doc-only: no lever,
> no solve, no year solved or scored, no run registered, no matrix cell or row
> edit, no keeper/registry/bench/rubric contact. Assembled by the session that
> picked the workstream back up on owner request ("get me to a calibrated
> backcast for 2023 scarcity"), branch
> `claude/ercot-backcast-calibration-2023-a16qu9`.

**Keeper at assembly:** `2026-08-15-ercot204-rule26-delete` (promoted ercot-205,
2026-08-15, rule-26 discharge, byte-identical to `ercot202-arm-plantphysics`).
Determination **NOT-YET**, fail set **{C3a-2023 −33.2 %, C3b-2023 NRMSE 0.604}**;
C3c the single ledgered CAVEAT ×3 (58/181, 22/53, 1/31 h > $200/MWh RT).
2024 and 2025 PASS every scored criterion (C3a −0.8 % / −7.5 %, C3b 0.135 /
0.096); C1 16/16 (free 12/12), C2, C4, C6, C8 PASS all years.

---

## 0. THE ANSWER, COMPRESSED

1. **The workstream is well past run168b — the owner's read is correct.** The
   `168b` on the HTML dashboard is the **forecast lane's frozen anchor**, not the
   backcast lane's position: the shipped hindcast
   `ercot-2021-2025-t1ff-armr-ffr5d` carries
   `score.dispatch_skill.keeper_run_id = 2026-08-05-run168b-year-curves` (the
   keeper on its 2026-08-05 ship date) and renders it on the forecast pages and
   the two crossover reports. The backcast keeper chain since then:
   run168b → ercot185-shaped-partial → run188-arm-topfine-cliff →
   run191-dam-deriver-regate → run192-arm-coal-peak → ercot202-arm-plantphysics
   → **ercot204-rule26-delete** — six promotions, log through **ercot-208**, and
   the live Pages deploy is current (last success 2026-08-15 20:28Z). §1.
2. **"A calibrated backcast for 2023 scarcity" is blocked by exactly one
   physical object** — August–September 2023 scarcity price formation — counted
   by three criteria (C3a-2023, C3b-2023, C3c-2023), adjudicated **model-class**
   (a competitive/measured-offer LP cannot form ERCOT's realized conduct tail),
   with the within-class mechanism space measured **exhausted**
   (ercot-95→208) and the caveat/ledger routes **rubric-closed and
   owner-refused** (Q-B FINAL, R-A signed, R-B not signed). §2.
3. **Four doors exist.** (A) charter the missing model class — a
   scarcity-conduct offer layer (card R's own R-C, "the only route that could
   ever flip the 2023 criteria on the merits") — starting with a cheap,
   read-only Phase-0 identifiability test; (B) an owner rubric act that ledgers
   the 2023 fails (reachable today, recommended against by the record);
   (C) the R-B reporting-text variant (NOT-YET stands, pages carry the
   one-object note); (D) hold R-A and wait for the 2026 SOM's RTC+B-era anchors
   (~mid-2027, card W). Recommendation: **A's Phase-0 now, C alongside, D as
   the fallback if Phase-0 stops; B not recommended.** Two admissible
   non-2023 mechanism charters remain live regardless (ercot-204 §A
   reserve-basis; E3 year-scoped parameters). §3–§4.

| door | what it is | changes the 2023 determination? | recommendation |
|---|---|---|---|
| **A** | New-class charter: scarcity-conduct offer layer (R-C program), Phase-0 first | Only route to PASS on the merits | **Charter Phase-0 now** (owner signature required; scopes Q-B/R-A explicitly) |
| **B** | Rubric act: widen `LEDGERABLE_CRITERIA` / raise `MAX_LEDGERED_CAVEATS` / relax tier guard | Yes — CALIBRATED-WITH-CAVEATS immediately | **Against** (card R's own reasoning; the guards are the product) |
| **C** | Reporting text: standing one-object note on the ERCOT status surfaces | No | Sign it — cheapest honest improvement in how the state reads |
| **D** | Hold R-A; revisit at the 2026 SOM (card W wait-for-data) | Not until ~mid-2027 | Default if A's Phase-0 stops |

---

## 1. WHERE THE WORKSTREAM IS (the 168b reconciliation)

- **Backcast lane (the workstream itself):** keeper
  `2026-08-15-ercot204-rule26-delete`; calibration log through ercot-208 (+ the
  salvaged ercot-200 card W append); next free shorthand ercot-209 → this
  session. The keeper's committed record is current on
  `docs/codebase-site/calibration-status.html` (`status/ERCOT.js` regenerated
  2026-08-15 17:15) and the run explorer; the Pages deploy succeeded
  2026-08-15 20:28Z, so the live site shows ercot-204. Since run168b the lane
  promoted six keepers (chain in §0.1, each under a pushed precommit and a
  direction-blind rule; the last two on legitimacy alone, byte-identical
  hourly sidecars 12/12).
- **Where "168b" still legitimately renders:** the forecast lane. The shipped
  ERCOT hindcast `frontend/data/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-shipped.json`
  (and its `-unified` sibling) stamps `keeper_run_id =
  2026-08-05-run168b-year-curves` in its dispatch-skill block — the backcast
  keeper *at the moment the hindcast was scored* (2026-08-05) — and both
  crossover reports carry it in their headers. That stamp is **frozen at ship
  time by design** (the hindcast's skill was measured against that keeper); it
  is not a claim about the backcast lane's current position. A stale browser
  cache of the status page is the only other candidate; the committed record
  rules out a stale live deploy.
- **Optional forecast-lane hygiene (not done here, out of this session's
  scope):** re-score the shipped hindcast's dispatch-skill block against the
  current keeper, or annotate `keeper_note` (the field exists and is null) with
  "anchor frozen at ship date; current backcast keeper is tracked on
  calibration-status". Either belongs to the FFR lane under its own charter.

## 2. WHY 2023 SCARCITY IS THE WHOLE BLOCKER (committed arithmetic, none of it new)

**What must move for a 2023-calibrated determination** (rubric v3.2 bars, from
the keeper's scored records):

| criterion | now | PASS bar | distance |
|---|---|---|---|
| C3a-2023 mean LMP | $42.97 vs $64.32 (−33.2 %) | ≥ $57.89 (±10 %) | +$14.92/MWh annual mean |
| C3b-2023 monthly NRMSE | 0.604 | ≤ 0.20 | Aug+Sep carry 96.2 % of squared residual |
| C3c-2023 tail hours > $200 | 58 vs actual 181 | ≥ 91 (0.5×) | +33 h of formed scarcity |

- **One object, counted three times** (card R §2, `ercot193_c3b_decomposition`):
  Aug 2023 model 117.3 vs actual 220.6 $/MWh lw; Sep 58.6 vs 109.8. Score
  Aug+Sep perfect and C3b-2023 is 0.118 — a PASS; score *everything else*
  perfect and it is 0.592 — still 3× the bar. The Jun–Sep gaps are ≈ $15.3/MWh
  of annual-mean equivalent, ~72 % of the C3a gap; the > $200 tail alone is
  ~⅔ of the C3a gap by dollars. **Any lever that avoids the Aug/Sep-2023
  scarcity object ceilings at C3b ≈ 0.59 and cannot make C3a reachable.**
- **The object is adjudicated model-class conduct, not a missing input:** the
  realized RT tail formed on ERCOT's *energy offer stack* — 0.91 of the
  1.10 GW offered ≥ $500 at the top-100 gap hours being storage (ercot-161) —
  at measured RTORPA p50 ≈ $1–5 and PRC p50 ≈ 5.8 GW (**no administrative/ORDC
  scarcity to recover**: ercot-102, ercot52 cap-dual). A competitive-offer LP
  does not form that equilibrium. The within-class space is measured exhausted:
  offer-surface family closed (ercot-181/184/188: all MW-preserving
  re-slicings ceiling at +$1.99/MWh, the real LP delivered −$0.21), coal
  levels measured and armed (ercot-168/192, C3c bit-unchanged), the
  storage-offer instrument refuted (ercot-162, discharge collapses ~74 %/yr),
  reserve/quantity families bistable or killed (ERCOT-107/108/159/97), the
  CC-offline-block premise refuted (ERCOT-163), the CC-headroom licence FAILED
  (ercot-191: L1 0.3857 vs 0.90 → Q-B automatic), SOC-reserve quantity moved
  counts by single hours (ercot-167: 58/20/0 → 61/25/3), tightness-conditioned
  rent non-identifiable (ercot-195 V0: 4/14 folds, $94–$330 irreducible vs $15
  — a regime series, not a tightness series).
- **The governance routes are closed as signed:** `LEDGERABLE_CRITERIA =
  {price_tail}` (v3.1), `MAX_LEDGERED_CAVEATS = 1` and the slot is spent by
  C3c, the v3.0 tier guard refuses model-class on load-bearing criteria
  fail-closed; **Q-B (FINAL)** — no ERCOT C3a-2023 spend of any kind; **R-A**
  (signed 2026-08-13) — NOT-YET stands as the public claim, no
  C3b-2023-targeted determination rounds; **R-B and its reporting-text variant
  NOT signed**; the ERCOT-144 four-fail exceptions-ledger publication was
  owner-REVERSED. ercot-206 (2026-08-15) re-derived the terminal state:
  *"a complete declaration is UNREACHABLE by any rule-13-admissible
  mechanism."*
- **Upshot:** within the current model class and rubric, NOT-YET is not a
  backlog position — it is the *proved ceiling*. Every route to "calibrated
  for 2023 scarcity" therefore runs through an **owner decision**, which is
  what the doors in §3 are.

## 3. THE DOORS

### Door A — charter the missing model class (card R's R-C): a scarcity-conduct offer layer. The only merits route.

**The object.** What 2023 is missing is *bidder conduct*: scarcity-hour offers
(storage foremost, thermal top-of-stack with it) priced at opportunity
cost/risk premium ($500–$3,000) rather than marginal cost, formed when the
system is tight. Card R named this route R-C: *"a scarcity-formation
representation beyond competitive/measured offers … the only route that could
ever flip the 2023 criteria on the merits"* — a **program decision** (new model
class, its own rule-1/13 adjudication), not a calibration lever.

**What a rule-13-honest build looks like (and what it must not be):**

- NOT the published-adder overlay (barred: rule 19 + rule 13 forward-analogue,
  ercot-204 §A / ercot-203b), NOT the measured storage RT surface fed verbatim
  (refuted: ercot-162 ground (c) — volume collapse), NOT across-year
  tightness-conditioned rent (V0 DO-NOT-REDO), NOT any adjudicated `R`/`I`/`G`
  cell re-test.
- A **conduct function**: scarcity-hour offer surfaces expressed as a function
  of forward-computable drivers (forecast tightness/PRC percentile, SOC/AS
  position for storage), identified from the committed 60-day disclosure
  corpora (`ercot-157` delivery-2023 + the 2024/2025 windows) at **hour grain
  across thousands of anchors within one design regime** — a different
  identification object from V0's seven across-regime annual rents. Zero
  fitted-to-residual scalars; the function regenerates for a forward year and
  responds to changed conditions, which is rule 13's admissibility test.
- **Admissibility argued both ways (the §2.6 pattern), for the owner to weigh:**
  *for* — same epistemic class as the armed measured-AS-reservation and
  committed-share constructions (measured market behaviour entering as a
  reproducible input); *against* — submitted offers are outcomes of the
  equilibrium under validation, so a function fit on 2023's own disclosures and
  scored on 2023 has answer-key character. The honest resolution is the
  Phase-0 design below (out-of-year transfer), and if it fails, the door
  closes measurably.

**Phase-0 (charterable now, read-only, no solve, no field):** an
identifiability/transfer test on committed corpora only — fit the conduct
function on 2024/2025 disclosures, test whether it reproduces the 2023
scarcity-hour offer surfaces at matched tightness percentiles (and LOYO across
2023 months), with a pre-registered mechanical STOP rule (the V0/ercot-208
discipline). Confounds to state up front: ECRS launch (Jun 2023) and ORDC
vintage differences sit inside the "one regime" assumption — card W's
thinness argument at a different grain, and precisely what the transfer test
measures. **Deliverable either way:** a measured verdict — the conduct layer
is identifiable and a Phase-1 build charter follows, or it is not and Door D
becomes the recorded floor with the exhaustion proof extended one class up.

**Signature required.** Q-B bars *any* C3a-2023 spend and R-A bars
C3b-2023-targeted rounds; both were made inside the current model class, and
card R itself names R-C as the merits route — but a Door-A charter must still
**explicitly scope/supersede Q-B and R-A for the new class** in its signature,
or the first executing session stops at its own fences. Cost: Phase-0 is one
read-only session; the program behind it (if Phase-0 passes) is multi-session
with solve costs comparable to the offer-family lanes.

### Door B — the rubric act (R-B): determination by amendment. Reachable today; recommended against.

Widening `LEDGERABLE_CRITERIA` beyond `price_tail`, raising
`MAX_LEDGERED_CAVEATS`, or admitting model-class on load-bearing criteria
would let the three 2023 records ledger as one adjudicated object →
**CALIBRATED-WITH-CAVEATS immediately**, misses still reported at full
magnitude. It is the only door that changes the public determination this
month. The record's own counter-argument stands unchanged and this assessment
does not soften it: the tier guard exists so a model −33 % off its central
intended-use quantity in a scored year cannot present as calibrated; card R
§3 called a determination bought this way "a worse public claim than the
honest NOT-YET," and the owner declined to sign R-B when it was offered. If
the owner's actual need is *a defensible public state* rather than the badge,
Door C delivers that at zero rubric cost.

### Door C — the reporting-text variant (R-B-lite). No determination change; the honest surface.

A standing note on the ERCOT status card and keeper shard: the three 2023
price-criterion misses are ONE adjudicated model-class object (Aug/Sep-2023
scarcity conduct; card R + the C3c ledger as citations), 2024/2025 pass every
scored criterion, and the determination is NOT-YET on that object alone. This
was offered at card R and not signed; it remains the cheapest act that makes
the public surface read the way the record actually is — and it is the fix
for the exact confusion that opened this session (a reader seeing a frozen
`168b` anchor and no lineage note). Doc + `build_status.py` regeneration in
one session, no rubric, no solve.

### Door D — hold R-A and wait for data (card W). The default.

Card W (ercot-200) measured design-regime identification unachievable on the
committed anchors (7 anchors, ~4 regimes) and the forward regime empty until
the **2026 SOM (~mid-2027)** publishes RTC+B-era conduct. If Door A's Phase-0
stops, this is the recorded floor: ERCOT bandwidth stays on the R-A
re-pointed queue (protective/hygiene, the 2024/2025 shape objects, standing
re-gates, forecast readiness), and the conduct question re-opens with real
anchors. No signature needed — it is the standing state.

### Independent of the doors — two live, admissible mechanism charters (not 2023-targeted; strengthen scarcity representation where it is legal to)

1. **The ercot-204 §A reserve-basis question (the senior open object,
   un-chartered, owner-side).** The armed ORDC/RTORPA counterpart is *not
   broken in 2023* (fires 42 h up to $1,920/h, all inside the published-fired
   set, RTOLCAP within 0.2 %) but reads ≈ zero across the 560/253
   published-fired hours of 2024/2025 while the model holds materially LESS
   reserve than the real system (6,955 vs 8,854 MW; 6,638 vs 9,654 MW) and its
   own ORDC-total row records shortfall in 40/4 of those hours. Where the ORDC
   pricing region sits relative to the model's reserve representation is a
   real mechanism question; landing it moves the 2024/2025 C3c counts (22/53,
   1/31) and any 2023 spillover is side-effect-reported. It does NOT reach the
   2023 58→91 gap (2023's tail was not ORDC-formed — RTORPA p50 $1–5).
2. **E3 as a year-scoped LOLP-parameter charter** (ercot-206 B0): the settled
   basis splits cleanly — flat fallback reproduces {2023, 2024}, the published
   table reproduces {2025} — so any E3 landing is a year-keyed parameter
   question under its own rules-20/23 charter, never a blanket arming
   (2023/2024 refute the table at ~2.5–2.6×).

Also open on the owner-side ledger, unchanged by this assessment: item 8's
CME/NYMEX basis-swap reopen screen (un-run), the `gas_hh_monthly_shape`
rule-28c row gap, T-3a (settlement-basis C3b scoring — a rubric question),
T-2 (behind the D2 freeze), and the frontier rank-2 re-point recommendation
(ercot-206 Phase A(3), owner-only).

## 4. RECOMMENDATION

**Sign Door A's Phase-0 + Door C together; keep Door D as the pre-registered
fallback; leave Door B unsigned.** Concretely, the next three sessions this
workstream should run, in order:

1. **CONDUCT-PHASE-0** (Door A, one session, read-only): the out-of-year
   conduct-transfer test on the committed disclosure corpora, precommit with a
   mechanical STOP rule pushed before any measurement; its verdict decides
   between the Phase-1 build charter and Door D — either way the answer is
   measured, not argued.
2. **REPORTING-TEXT-1** (Door C, one session, doc + status regen): the
   one-object note on the ERCOT surfaces, plus the forecast-lane
   `keeper_note` annotation that un-confuses the frozen `168b` anchor.
3. **RESERVE-BASIS-1** (§3 item 1, owner charter): the ercot-204 §A ORDC
   pricing-region question — the strongest admissible mechanism object on the
   board, and the one place scarcity representation can still improve without
   touching a closed ruling.

If all three run and Phase-0 passes, the program has a merits path to a
calibrated 2023 scarcity backcast with every number identified from measured
market conduct; if Phase-0 stops, the honest floor is recorded one model
class higher than today's, the 2024/2025 scarcity representation still
improves, and the public surface finally says exactly what the record says.

---

## 5. GOVERNANCE OF THIS ASSESSMENT

Doc-only read of committed artifacts (the ercot-182/189/193/196/200 card
precedent: a card is a read, not a mechanism test). Q-B FINAL and R-A cited
and honoured — no C3a-2023/C3b-2023 spend of any kind; every 2023 number
above is a committed-artifact citation (keeper attestation, card R's
decomposition, the C3c ledger), none newly scored. DO-NOT-REDO honoured: no
adjudicated `R`/`I`/`G` cell proposed for re-test; V0's across-year
tightness instrument stays dead; Door A proposes a *different object at a
different grain* and says so. Rule 22: no year solved, scored or registered;
{2023, 2024, 2025} referenced read-only; no marker sought. Rule 25: ERCOT
only. Rule 28: no matrix edit (no mechanism tested; Phase-0, if signed, adds
its own row only when a field exists). Rules 5/24: no config surface
touched. Keeper at session start and end: `2026-08-15-ercot204-rule26-delete`.
New artifacts: this assessment + one calibration-log entry (ercot-209),
nothing else.

---

## RESOLUTIONS — CARD X

> Append-only. Each item records an owner signature carried verbatim from the
> dispatch that made it. Never edit another item's lines.

**X-1 SIGNED (owner, by dispatch of CONDUCT-PHASE-0, 2026-08-16)**

> "X-1 SIGNED (owner): Phase-0 of the card-R R-C conduct-layer program is chartered as a READ-ONLY
> identifiability/transfer measurement. Q-B and R-A are SCOPED, not reopened: they continue to bar any
> competitive-offer-class C3a/C3b-2023 lever round; they do not bar this measurement, which solves nothing,
> scores no price criterion, feeds no model input, and creates no ScenarioConfig field. 2023 conduct
> surfaces appear ONLY as the transfer test's evaluation target (measured-vs-measured). The verdict is
> mechanical under a pre-registered STOP rule; a Phase-1 build charter, if any, returns to the owner as its
> own card. If Phase-0 stops, Door D (card W wait-for-data, ~mid-2027) is the recorded floor."

Executing lane: `ercot-210` (CONDUCT-PHASE-0), precommit
`docs/PRECOMMIT-ercot210-conduct-transfer-phase0-2026-08-16.md`, finding
`docs/FINDING-ercot210-conduct-transfer-phase0-2026-08-16.md`. This signature
scopes §3 Door A's Phase-0 only; §3 Door B remains unsigned, Door C unsigned,
Door D standing.
