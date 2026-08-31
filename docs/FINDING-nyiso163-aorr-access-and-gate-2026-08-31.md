# FINDING — nyiso-163: the Leg-2 access route VERIFIED and sharpened, the on-receipt identifiability gate BUILT AND VALIDATED, and the nyiso-97 verdict RE-CONFIRMED at in-span vintage from a public source

**Filed:** 2026-08-31, session nyiso-163. **Zero solve; committed artifacts and
public documents only.** Keeper, shard, marker, frontier, determination and
matrix all **UNTOUCHED**.

**State at session start, verified in-session, not taken on trust:**
`calibration_verdict.py --run-id 2026-08-30-nyiso-159-loss-surface` →
**NOT-YET** on exactly `{C3a-2025 −11.5 %, C3c}` (C3c is **not** lone, so the
rule-22 standing rule stays silent and both failures stand);
`audit_keepers.py --iso NYISO` → **PASS 0 failures / 0 warnings**.
`docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` is **FILED AND
UNDECIDED** (no ruling commit after `d8b0ea8`), so this session proceeds under
its §6: *"pursuing the MyNYISO stakeholder route needs no ruling and is not
gated on this card."*

**Honest expected value, stated up front.** This session does **not** move the
determination and does **not** close C3a-2025. What it changes: the owner's
access step is now one copy-paste request naming the *current* rule
identifiers; the on-receipt content test is a committed, pre-validated
executable rather than prose a future session must re-interpret under pressure;
and the nyiso-97 verdict no longer rests on a 2008 vintage.

---

## 1. WHAT WAS DELIVERED

| # | Deliverable | Artifact |
|---|---|---|
| 1 | The access request package, route re-verified | §2 below (ready-to-send block) |
| 2 | The fail-closed on-receipt gate | `scripts/probes/_nyiso163_aorr_gate.py` |
| 2b | Negative-control validation + acceptance suite | `results/calibration/_nyiso163_gate_acceptance_negcontrol.json` |
| — | *(unplanned)* first real gate application | `results/calibration/_nyiso163_gate_current_public.json` |
| 3 | The standing re-open watch | §6 below |

Fixtures: `scripts/probes/_nyiso163_aorr_control_2008.json` (negative control),
`_nyiso163_aorr_synthetic_positive.json` (discrimination control, **synthetic —
never an input**), `_nyiso163_aorr_current_public_2026.json` (real, public,
current-vintage rows).

## 2. THE ACCESS ROUTE — VERIFIED, AND MATERIALLY SHARPENED

The nyiso-161 §2 access fact **holds and is more concrete than recorded.** The
Salesforce article itself (`nyiso.my.site.com/MemberCommunity/s/article/
Process-of-creating-a-stakeholder-account-on-MyNYISO`) is a JS-rendered shell
that returns only a "CSS Error" placeholder to a non-browser fetch — it could
not be read directly — but the route was confirmed from NYISO's indexed
content and the CEII form itself.

**What the route actually is** (this corrects the nyiso-161 phrasing, which had
the CEII/NDA form as *conditional* — "if the table is CEII-classed"):

1. The **CEII/Non-Disclosure Agreement form IS the account application**, not a
   contingency. A MyNYISO account is what grants CEII access, and it is
   obtained by submitting a completed CEII Agreement + NDA to Stakeholder
   Services. Form:
   `https://www.nyiso.com/public/webdocs/markets_operations/services/customer_relations/CEII_Request_Form/CEII_Request_Form_and_NDA_complete.pdf`
2. On the form, select the **"MyNYISO.com UserID and Password"** option and
   complete the remaining sections together with the NDA.
3. **NYISO Legal reviews.** On approval the requester is directed to a link to
   apply for the MyNYISO account.
4. The account opens the secure sections **where Operating Committee, Planning
   and other documents reside** — which is the class the AORR/ARR table sits in.

**Contacts:** Stakeholder Services — `stakeholder_services@nyiso.com`,
518.356.6060. Registration support — `customer_registration@nyiso.com`,
518.356.6060 option 3.

**Eligibility confirmed:** the route is open to **stakeholders**, not only
market participants. This postdates and supersedes the nyiso-160 "cannot
produce them" answer, which was given before this was on the record.

### 2.1 THE READY-TO-SEND REQUEST

Names the INTAKE-SPEC §2 list (a)–(c) using the **current** identifiers this
session verified, plus a new item (d) that the current rules text revealed to
exist. Each item states what it must **contain** to be usable, so a partial
fetch is caught at the counter rather than after the fact.

```text
To: stakeholder_services@nyiso.com
Cc: customer_registration@nyiso.com
Subject: Stakeholder account request + document request — Applications of the
         Reliability Rules (Con Edison in-City / NYC Zone J), 2023–2025 vintage

Hello,

I am requesting a MyNYISO stakeholder account, and — once access is granted, or
by direct transmittal if that is simpler on your side — copies of four specific
documents. I am a non-market-participant stakeholder doing quantitative
research on NYISO price formation; the request is for the as-enforced local
reliability requirements for the New York City zone, for calendar years 2023
through 2025.

I understand from your Member Community documentation that the route is to
submit the CEII Request Form together with the Non-Disclosure Agreement,
selecting the "MyNYISO.com UserID and Password" option, for review by your
Legal department. Please confirm that is the correct path for this request and
whether anything further is needed from me.

WHAT I AM ASKING FOR

(a) The CURRENT-VINTAGE APPLICATIONS OF THE RELIABILITY RULES (ARR/AORR) table
    — all Con Edison and Long Island rows.
    NYISO Manual 12 (issued July 2026), Attachment B, Table B.5 states: "The
    current version of the ARR Table is posted at
    https://www.nyiso.com/reports-information", which is behind the MyNYISO
    login. NYSRC Reliability Rules & Compliance Manual V48 §1.2.8 also routes
    Applications to https://www.nyiso.com/reliability-compliance.
    Of particular interest are the Applications implementing NYSRC Reliability
    Rules G.1 (New York City System Operations) and G.2 (Loss of Gas Supply –
    New York City), i.e. the current successors of the former Manual 12
    Appendix B rows Table B.4 LRR 1–3 and ARR 37, ARR 66, ARR 28.
    TO BE USABLE, a row must state: a MW level or a minimum-number-of-units-
    online for the pocket; the eligible unit set (named units or a closed
    class); and the condition that triggers it, in terms of an observable
    quantity such as a forecast or actual load level. A row that states only
    that a requirement exists, or that defers the parameters to a Transmission
    Owner procedure, does not answer the question.

(b) Any Manual-12-linked replacement tables for the former Appendix B
    (the successors of Tables B.1–B.5), same content test as (a).

(c) The effective-date / versioning record for (a) and (b) covering 2023–2025.
    If what you can provide is a single current snapshot that postdates that
    span, please include the change history so I can establish what was in
    force during 2023, 2024 and 2025 specifically. (For the NYSRC rules layer
    I have been able to establish this from the manual's own Version History;
    I need the equivalent for the Applications layer.)

(d) The published list of dual-fuel units in the MINIMUM OIL BURN (MOB)
    program, and the applications specifying the minimum oil burn requirements
    for those units, for 2023–2025.
    NYSRC Reliability Rule G.2 R3 requires that "The NYISO shall document,
    maintain and publish the current list of dual fuel units that are part of
    the Minimum Oil Burn (MOB) program", and G.2 §D Guidelines states "There
    are applications, approved by the NYISO for implementing this Reliability
    Rule, which specify minimum oil burn requirements for select generators in
    New York City." I have not been able to locate either publicly.
    TO BE USABLE: the unit list, and for the requirements, the load or system
    condition at which minimum oil burn is invoked and which units it binds.

If any of these is classified such that it cannot be released even under the
CEII/NDA process, I would be grateful if you could say which, so that I can
record it as unavailable rather than continue looking.

Thank you very much for your help.
```

## 3. THE GATE — `scripts/probes/_nyiso163_aorr_gate.py`

An executable, **fail-closed** re-run of the nyiso-97 §4 content test, built
**before** any current-vintage rows were read, so that applying it is a genuine
application of a pre-committed test rather than one shaped around its input.
(Ordering was deliberate and is recorded here because it is the whole point:
the gate was written, validated and its acceptance artifact produced before §5
was attempted.)

**Verdict rule.** PASS iff **at least one** row passes **all seven** tests:

| test | what it enforces | source |
|---|---|---|
| T0 vintage | applicable to some part of 2023–2025; an unstated effective date FAILS | nyiso-97 §4 blocker 2; rule 14 `[R-ACCURATE]` |
| T1 zone | an NYC (Zone J) named sub-zonal pocket row | INTAKE-SPEC §2; Zone K already carries `nyiso_li_lcr_tsl` |
| T2 parameter | a numeric MW level **or** minimum-units-online | nyiso-97 §1(i) |
| T3 unit set | enumerated units or a closed, fleet-enumerable class | nyiso-97 §1(ii) |
| T4 trigger | observable to the model; an unpublished-TO-procedure dependence FAILS | nyiso-97 §1(iii), sharpened by §4 blocker 1 |
| T5 forward story | regenerates from forward drivers **and** responds to changed conditions | rule 13 `[R-MEASURED]` |
| T6 provenance | `published_document`; conduct / BPCG / make-whole / LBMP / residual / inference are hard-failed **by name** | nyiso-97 §5 re-open bar |

**Fail-closed by construction.** Every test defaults to failure. A missing
field, a null, an unparseable number, an unrecognised enum, a malformed row, an
empty input, or a test that raises is a FAIL of that test — never a skip, never
a pass, and never an abort.

**The anti-inference guard.** Each of the three quantities must carry a `quote`
that is a **verbatim substring of that row's own published text**
(whitespace-normalised). A number that does not appear in the source row cannot
pass. This is what mechanically forbids backing a parameter out of observed
unit conduct, BPCG uplift, LBMP or the C3a/C3c residual — the encoder cannot
assert a value the document does not contain, so rule 13 is enforced by the
program rather than by the diligence of a future session.

Exit status: `0` = PASS, `2` = FAIL, `3` = input unreadable (reported
distinctly so a transcription error is never misread as an adjudication).

## 4. VALIDATION — three legs, all required, all passing

`python3 scripts/probes/_nyiso163_aorr_gate.py --self-test` → **exit 0**.
Artifact: `results/calibration/_nyiso163_gate_acceptance_negcontrol.json`.

**Leg 1 — NEGATIVE CONTROL: the 2008 vintage → FAIL, as required.** The public
2008-stamped Appendix B was adjudicated NON-IDENTIFYING ON CONTENT at nyiso-97
§4. The gate fails it. Crucially it fails it **row by row for the reasons
nyiso-97 gave**, not for one blanket cause:

| row | blockers the gate returns |
|---|---|
| Table B.4 LRR 1 | T0, T2, T3, T4, T5 |
| Table B.4 LRR 2 | T0, T2, T4, T5 |
| **Table B.4 LRR 3 (min oil burn)** | **T0 only** |
| ARR 37 | T0, T2, T3, T4, T5 |
| ARR 66 | T0, T2, T4, T5 |
| ARR 28 (LIPA) | T0, T1 |

The fixture encodes each row **as generously as the published text honestly
allows** — where the source states a number or a unit list, it is encoded as a
claimed quantity with its quote. A control that withheld quantities would prove
nothing.

**LRR 3 failing on vintage ALONE is the informative result.** It is the one
2008 row carrying a load threshold, a min-units count and an enumerated unit
set, and it is blocked only by being 2008 text. That makes it the row whose
current-vintage successor is by far the most likely to clear the gate — which
is why §2.1 item (d) asks for the MOB requirements by name.

**Leg 2 — DISCRIMINATION: a synthetic identifying row → PASS.** Without this
leg, leg 1 would be worthless: a constant-FAIL function also "fails the 2008
control". The synthetic row is the 2008 LRR 3 shape with the single vintage
blocker removed and nothing else changed, so it isolates exactly that the gate
can return PASS on a row of identifying shape.

**Leg 3 — FAIL-CLOSED CONTRACT: 7/7 adversarial cases → FAIL.** Empty list,
non-list, null, non-dict row, empty row object, a fully-specified row whose
parameter is **not quotable** from its own text, and a row whose
`derivation_basis` is `residual`. None reaches PASS.

## 5. UNPLANNED, AND THE SESSION'S REAL EVIDENTIARY GAIN — the nyiso-97 verdict RE-CONFIRMED AT IN-SPAN VINTAGE FROM A PUBLIC SOURCE

Verifying the access route surfaced the **current (issued July 2026) NYISO
Manual 12**, whose Attachment B splits the former Appendix B in a way nyiso-97
did not have in front of it:

* **Table B.5 (the ARR/AORR table) → `https://www.nyiso.com/reports-information`**
  — the MyNYISO-walled location. Unchanged: Leg 2's object is still walled.
* **Table B.4 (Local Reliability Rules of the NY Transmission Owners) → the
  NYSRC Reliability Rules, Section I** — **public.** (The URL Manual 12 prints,
  `nysrc.org/NYSRCReliabilityRulesComplianceMonitoring.html`, is dead/404; the
  live successor is `nysrc.org/documents/nysrc-reliability-rules-compliance-monitoring/`.)

nyiso-97 §2 checked NYSRC for an **AORR posting** and correctly found none.
That remains true — but the **LRR half** does live there, in the *Reliability
Rules* manual, which is a different document from the one nyiso-97 looked for.

**The rows were fetched, transcribed and run through the gate**
(`scripts/probes/_nyiso163_aorr_current_public_2026.json` →
`results/calibration/_nyiso163_gate_current_public.json`). Source: **NYSRC
Reliability Rules & Compliance Manual V48 (final, 7-17-2026), Section G "Local
Area Operation"** — G.1 *New York City System Operations* and G.2 *Loss of Gas
Supply – New York City*.

**Vintage established from the source's own change history**, which is exactly
what INTAKE-SPEC §2 item (c) demands of a current snapshot: v46 (2022-06-10)
was in force at span start; **v47 (2024-06-14) changed only RR B.5 / B.1 /
Tables B-1 and B-3; v48 (2026-06-17) changed only RR A.2**; the last revision
to *any* Section-G requirement was **v42 (2018-02-09)**. The G.1/G.2 text
quoted is therefore the text in force for the whole of 2023–2025.

**GATE VERDICT: FAIL — 5 rows, 0 qualifying — and it fails on CONTENT.** Every
row clears T0 (vintage), T1 (zone) and T6 (provenance) and fails on T2/T3/T4/T5:

* **G.1 R1** *"Certain areas of the Con Edison system shall be designed and
  operated for the occurrence of a second contingency."* — materially the 2008
  LRR 1 wording. Still qualitative.
* **G.1 R2** *"Unit commitment in the New York City (NYC) zone shall be based on
  second contingency operation and consideration of the Storm Watch Procedure,
  loss of the six lines south of Millwood, and the locational requirements for
  operating reserves."* — **this is the row the winter face would need**, in
  current force, and it states no MW level, no minimum-units count, no eligible
  unit set and no observable trigger. It defers entirely to procedures.
* **G.2 §D Guidelines — the decisive row:** *"There are applications, approved
  by the NYISO for implementing this Reliability Rule, which specify minimum oil
  burn requirements for select generators in New York City."* The current public
  rules layer states **in terms** that the operative in-City parameters live in
  the **Applications**, not in the rules.

**What this settles, and what it does not.**

* **SETTLED: nyiso-97's blocker 2 no longer carries the verdict.** nyiso-97 had
  to reason partly from a 2008 vintage ("the public vintage is not the
  as-enforced rule"). We now have the public layer that **was in force across
  2023–2025**, and it fails on **blocker 1** — content — at in-span vintage.
  The identification verdict is strictly better evidenced than it was, and its
  weakest leg is retired.
* **NOT SETTLED — Leg 2 is NOT discharged.** The rules layer is **not** the
  artifact INTAKE-SPEC §2 asks for. Applications are, by NYSRC §1.2.8's own
  definition, *"operating procedures that apply to very specific system
  locations or conditions"* — the SO3-18 class. A FAIL on the rules layer is a
  FAIL on the wrong document. **Only the walled Applications table can close or
  open Leg 2**, and the gate stands ready for it unchanged.

**One judgment call surfaced rather than silently made — G.1 R3.2.**
*"A percentage of the ten (10) minute NYCA operating reserves equal to the ratio
of the NYC zone peak load to the statewide peak load shall be required to be
selected from resources located within the NYC zone."* This is the closest the
entire public layer comes to identifying, and the one place the gate's
verbatim-number requirement does real work: the row states a **derivation rule**,
not a level — no MW appears in it, and the NYCA 10-minute reserve it scales is
set by a different rule. It fails T2 and T4. A future session holding the NYCA
reserve constant **could** re-encode it as a derived parameter, and that is a
legitimate question — but note two things before anyone does: it is a
**locational reserve** requirement, **not** the in-City **commitment** formation
the winter face needs; and arming it would be a reserve lever, which rule 19
`[R-ONE-MECH]` and the closed, ledgered C3c queue forbid. **Flagged for the
owner; not adjudicated here, and nothing armed.**

**A dead end, pre-adjudicated so nobody re-walks it.** The search result
`nyiso.com/documents/20142/3035389/A-B-References-2023.pdf` looks like an
"Appendix A–B references" document. It is not: "A-B" is **Accounting and
Billing** — the *NYISO Accounting and Billing Training Reference* v1.0
(11/18/2024). It is useful for exactly one fact and barred for everything else:
it confirms **LRR I-R3 & I-R5 (Min Oil Burn) are LIVE settlement charge codes in
2023–2025** (Margin Restoration (MOB) payment, daily bill code 328; MOB charge,
daily bill code 839) — i.e. the min-oil-burn obligation is enforced today, so
its current-vintage requirement genuinely exists to be requested. But everything
it carries is the **make-whole OUTCOME**, which rule 13 and the nyiso-97 §5
re-open bar bar outright as a requirement substitute. **Do not mine it for
parameters.**

## 6. THE STANDING RE-OPEN WATCH — recorded, not re-run

nyiso-161 ran the public contingency check on 2026-08-30 (its third that day);
this session did **not** repeat that sweep. What follows is the watch itself, so
the next session checks what actually moved.

| # | nyiso-97 §5 re-open condition | the exact source that would satisfy it | last checked | by | result |
|---|---|---|---|---|---|
| 1 | NYISO/NYSRC restores a **public AORR posting at current vintage carrying actual pocket parameters** | `nyiso.com/reports-information` (Manual 12 Table B.5 target) and `nyiso.com/reliability-compliance` (NYSRC §1.2.8 target); NYSRC rule postings `nysrc.org/rule-postings/reliability-rule-revisions/` | **2026-08-31** (this session, the two NYISO URLs + the NYSRC rules layer); 2026-08-30 (NYSRC PRR postings) | nyiso-163 / nyiso-161 | **NOT SATISFIED.** Both NYISO URLs are JS-rendered shells; the reachable public layer is the NYSRC *rules*, which §5 shows fail on content. NYSRC 2026 postings are PRR 157/158/159/161 — no AORR restoration. |
| 2 | A **FERC/PSC docket publishes the as-enforced pocket MW requirements and eligible unit sets** | NY PSC docket search; nearest family NY PSC 25-E-0764 (CECONY Reliability Needs Update / Reliability Contingency Plan) | 2026-08-30 | nyiso-161 | **NOT SATISFIED** — planning-genre; fails the §2 gate on sight. |
| 3 | The **owner supplies authorized access** to the walled table AND its rows carry derivable parameters | MyNYISO stakeholder account via CEII Request Form + NDA → Stakeholder Services → Legal (§2) | **2026-08-31** — route verified and sharpened; **request not yet sent** | nyiso-163 | **OPEN — this is the live leg.** The gate (§3) is built and validated and runs on receipt. |

**New watch item added this session (not one of the three, but concrete and
cheap):** the **published MOB dual-fuel unit list** that NYSRC G.2 R3 obliges
the NYISO to publish. Not located publicly as of 2026-08-31; it is item (d) of
the request.

**Cadence.** Condition 1: quarterly, or on any Manual 12 re-issue (the current
edition is July 2026) or NYSRC RRC manual version bump (currently V48,
2026-07-17 — the Version History is the cheapest single check, §5). Condition 2:
opportunistically, on news of a CECONY in-city reliability filing; it has now
failed twice and does not merit a standing sweep. Condition 3: on the owner's
word — it is not a source to poll. **Do not re-run the full sweep more than once
per quarter absent a trigger**; three checks on 2026-08-30 and a fourth on
2026-08-31 is already past the point of diminishing returns.

## 7. WHAT THIS SESSION DID NOT DO

* **No LP solve of any year; no holdout spend.** The freeze is ACTIVE, NYISO
  holds **no** `complete` marker (withdrawn 2026-08-30, Q5-W) and is absent from
  `final`, so 2020–2022 and 2019/H1-2026 are all unauthorized. Nothing outside
  {2023, 2024, 2025} was attempted.
* **No mechanism, prereg, scalar or `ScenarioConfig` field.** A mechanism prereg
  is written only after the gate returns PASS **on real received rows from the
  Applications layer** — which has not happened. The §5 FAIL is on the rules
  layer and licenses nothing.
* **No C3c lever** (summer face stays ledgered, queue stays closed, rule 19);
  **no re-tune** of the loss-surface, hydro or seam inputs (rule 23); **no
  re-opening** of Tier-3 TTC re-grounding, the F/G topology split, the bare
  Zone-K swap, or the fuel-side iroquois flag alone.
* **No keeper, shard, marker, frontier or determination change.** Frontier
  stays {PJM, NEISO}; NYISO's re-entry to `complete` remains a new owner
  declaration once the keeper again scores CALIBRATED (the Q5-W route).
* **No touchpoint-prep re-run** (nyiso-160 proved bit-identical HEAD replay;
  nyiso-162 re-verified). **No GitHub Actions workflow.**
* **Matrix: NO cell moves.** Rule 26 duty (b) is not triggered — no mechanism
  was tested. `scuc_load_pocket_commitment` stays **G**;
  `diurnal_price_amplitude` stays **G**. Duty (c) not triggered (no new
  `ScenarioConfig` field). The §5 evidence strengthens the existing `G`
  justification rather than changing the cell.

## 8. WHERE THE LANE STANDS

The winter face of C3a-2025 remains **identification-blocked**, and the
determination remains **NOT-YET on {C3a-2025, C3c}**. What changed is that the
block is now precisely located and the response is pre-built: the operative
parameters live in the **Applications** layer, the public **rules** layer has
been checked at in-span vintage and does not carry them, the owner's access step
is one request, and the test that will adjudicate whatever comes back is
committed and validated.

If the stakeholder registration succeeds, the leg resumes at full speed. If the
gate then returns FAIL on the real Applications rows, **the leg closes with cause
a second time — and that is a legitimate outcome to be recorded unrewritten.**

---

*Evidence:* `docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`
§1/§3/§4/§5 · `docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md` §2 ·
`docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` §2/§6 ·
`docs/FINDING-nyiso-leg2-reverify-2026-08-31.md` ·
`results/calibration/FINDING-nyiso160-leg2-stop-and-tpaudit-2026-08-30.md` ·
NYISO Manual 12 (issued July 2026) Attachment B · NYSRC RRC Manual V48
(2026-07-17) §1.2.8, §G.1, §G.2, §8 Version History · NYISO Accounting and
Billing Training Reference v1.0 (2024-11-18) §10.4, §19.1 · CLAUDE.md rules 13
`[R-MEASURED]`, 14 `[R-ACCURATE]`, 19 `[R-ONE-MECH]`, 22 `[R-HOLDOUT]`, 26
`[R-MECH-MATRIX]`.
