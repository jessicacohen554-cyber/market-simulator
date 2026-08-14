> Status: FOR A FUTURE OWNER SITTING — NOTHING IS DECIDED, BUILT, OR EXECUTED HERE.

# DECISION CARD — ercot-200: regime-conditioned identification of the L-SCAR screen rent term — can market DESIGN do what tightness could not, and is it rule-13-admissible?

**Session ercot-200 `[FABLE]` (REGIME-CARD executor lane, re-dispatch b),
2026-08-14, branch `claude/ercot-scar-regime-card`, assembled at origin/main
`5bf5f13`, REBASED onto origin/main `315a2452` (see §0.1 — two sibling lanes
stopped in between and the card body was corrected to match).** Authority: the **L-SCAR V0-FAIL adjudication, SIGNED by the owner
2026-08-14, item (ii)** (`docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`,
V0-FAIL ADJUDICATION block, on main at `fb6d08d` via PR #3931; dispatch: pack
`docs/handoffs/ercot-scar-workstream-pack-2026-08.md` §2.10, re-dispatched
cycle 10): *"assembly of a REGIME-CONDITIONING decision card IS AUTHORIZED —
doc-only: it argues the admissibility of conditioning the rent on market DESIGN
(ORDC vintage / ECRS / SWCAP / RTC+B) for a FUTURE owner sitting; it builds
nothing; zero measured forward-regime anchors exist until the 2026 SOM
(~mid-2027), and the card must say so."*

**DOC-ONLY, declared:** no `ScenarioConfig` field, no matrix row or cell edit
(a card is a read — the ercot-182/189/196 precedent, recorded in §6), no LP, no
solve, no year solved or scored (rule 22), no model input touched (rule 13), no
keeper/registry/bench contact, no run registered. One new measurement artifact:
the read-only probe `scripts/probes/ercot200_regime_partition.py` (output
`results/calibration/ercot200_regime_partition.json`), which reads exactly one
committed input — the ercot-195 anchor intake — and **reads no tightness
variable anywhere** (V0 is the DO-NOT-REDO adjudication for the tightness
instrument; nothing here re-fits, re-scores, or re-argues it).

**Shorthand governance (re-checked at the rebase onto `315a2452`):** this
session claims **ercot-200**, which is free on refreshed main — 198 is the
merged T-3b audit, 201 the L2-BUILD stop, 202 the T-1 finding, and 199 is
free and unclaimed. Main's forward pointer (**ercot-203**) is left exactly as
main set it; this session's entry appends after it in session order.
**TWO standing collisions on main are recorded here, and NOTHING is
renamed:** **ercot-196** — consumed by BOTH the shape decision card
(`DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md`) and the rule-18
grain PRECOMMIT (`PRECOMMIT-ercot196-rule18-grain-successor-2026-08-14.md`,
PR #3933, claimed from a stale log read) — and **ercot-202**, consumed by
BOTH the owner-sitting record (re-keyed from ercot-197 on main) and the T-1
non-viability finding. Recorded per the ercot-193 file-order convention.

---

## 0. THE BOARD

Card letters U and V are skipped to avoid glyph collisions (the matrix's `U`
= untested; the charter's V0–V3 gates); this is **card W**.

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **W** | Which route (if any) does the regime-conditioning instrument take: W-0 wait-for-data / W-1 assemble-and-hold / W-2 attempt identification now / W-3 a structurally different instrument? | blocks no other lane — but see §0.1: the two lanes that were in flight at assembly have BOTH since stopped, so W is now the only open route to frontier rank 2 | **W-0 WAIT-FOR-DATA, with W-1's design-attribution assembly as its cheap read-only companion; W-2 refused ex ante on the computable gate arithmetic (§3); W-3 recorded VACANT — the committed record supports no structurally different instrument today** |

### 0.1 LANE-CONTEXT CORRECTION — applied at the rebase onto main `315a2452`

This card was assembled at main `5bf5f13`, when two sibling lanes were in
flight. **Both have since stopped on main, and both stops are load-bearing
for how the owner should read this board:**

* **L-2 IS DEAD** (`docs/FINDING-ercot201-l2-e1-dispersion-phase0-stop-2026-08-14.md`,
  log ercot-201): the chartered E1 dispersion surface is **superseded** on
  main by FFR-8B/FFR-9A, and its identification route is **barred by an
  adjudicated prior stop** (FFR-8B §4 / AG.1). Phase 0 stopped; nothing was
  built, nothing solved. The adjudication's item (i) charter is therefore
  discharged-by-impossibility, not by delivery.
* **T-1 IS NON-VIABLE ON PREMISE** (`docs/FINDING-ercot202-t1-nonviable-2026-08-14.md`,
  log ercot-202): `gas_hh_monthly_shape` was **already armed** on the run192
  keeper, so the signed A/B had no control arm to express; it was cancelled
  before any solve, with no lever substituted.

**The consequence, stated plainly because it is the owner's real question:**
the L-SCAR charter §1 defect — the screen's measured **~50–70 $/kW-yr**
merchant-revenue understatement, with retention resting on the measured
non-monotone admission cap (D-20(a)) — now has **NO live lane against it**.
Frontier rank 2 stays OPEN (adjudication item (iii) declined the L-0
disclosure row) with **zero executors**. This does not change W-0's
arithmetic (§3 is unaffected — it reads only the committed anchors), and it
does not make W-2 any more feasible; it **sharpens** what W-0 is asking the
owner to accept: a genuine wait, not a wait behind other work. §5 W-0(c) and
W-3 are corrected accordingly.

One signable card. §§1–4 are the evidence; §5 is the option board.

---

## 1. THE OBJECT

The ercot-195 finding (`docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`)
proved the SOM merchant-rent series 2019–2025 is a **regime series, not a
tightness series**: no function of any candidate measured-tightness variable
can pass the pre-registered V0 gate (best form 4/14 folds vs 14/14 required; a
model-free bound puts $94–$330 of irreducible error on near-tied tightness
pairs against a $15 fold tolerance; ex-Uri is WORSE, 2/14). The monitor's own
attributions carry the alternative conditioning variable: 2021 = Winter Storm
Uri under the then-$9,000 SWCAP; 2022 = *"primarily due to the ORDC changes
implemented at the beginning of the year"*; 2023 = ECRS at **50 % of the
year's net revenue** by the monitor's own number.

The authorized question is therefore: **can a screen-side rent term
`R_f(design_regime)` be identified by conditioning on market DESIGN — ORDC
curve vintage / ECRS existence / SWCAP level / RTC+B — rather than tightness,
and is that rule-13-admissible?** The V0 adjudication is the DO-NOT-REDO
record for the tightness instrument: this card never re-fits or re-argues
tightness conditioning, in any regime subset. (A within-regime tightness term
is re-fitting tightness conditioning on subsets and is refused here by name.)

What such a term would be for is unchanged from the charter: the screen's
measured ~50–70 $/kW-yr-class-year merchant-revenue understatement (charter
§1), with the §2.2 shape (`term_f = max(0, R_f(·) − S_f)`), the §2.4
subtraction sunset, and the §4 must-nots binding verbatim.

## 2. THE REGIME PARTITION, FROM COMMITTED ARTIFACTS ONLY

### 2.1 The seven anchors, regime-attributed (all on disk, `data/raw/som-competitive-conduct/`, each row source_doc+source_page)

| vintage | CT mid $/kW-yr | CC mid | design regime (published boundary) | monitor's own attribution |
|---|---|---|---|---|
| 2019 | 127.0 | 151.5 | pre-2022 ORDC, SWCAP $9,000 | — |
| 2020 | 39.0 | 51.0 | pre-2022 ORDC, SWCAP $9,000 | — |
| 2021 | 700.0 | 800.0 | pre-2022 ORDC, SWCAP $9,000 | **Uri** (monitor ex-Uri counterfactual: CT 60–78, CC 81–105 — published, on disk) |
| 2022 | 165.0 | 203.5 | ORDC widened at start of year, SWCAP $5,000 | *"primarily due to the ORDC changes"* (2022 SOM p.108) |
| 2023 | 240.5 | 250.0 | ECRS era (launched 2023-06) | **ECRS = 50 % of net revenue**; *"absent ECRS … very close to their respective CONE values"* (2023 SOM p.108; CONE 80–130) |
| 2024 | 68.0 | 89.0 | ECRS era, normalised | normalised (2024 SOM p.119) |
| 2025 | 52.59 | 82.96 | ECRS era, normalised; regime ENDS in-year | normalised (2025 SOM p.125); RTC+B go-live 2025-12-05 |
| 2026+ | **none** | **none** | **RTC+B** (`results/scarcity.py::_RTCB_FIRST_FULL_YEAR = 2026`) | **zero measured anchors until the 2026 SOM publishes (~mid-2027)** |

The partition itself is an analyst choice over published design facts, and at
least two cuts are defensible — the probe emits both:

- **Coarse (4 measured-era regimes):** {2019–2021} / {2022} / {2023–2025} /
  {2026+ forward}. Anchors per regime: 3 / 1 / 3 / **0**.
- **Fine (5):** splits the ECRS era at the monitor's own seam (2023 = half-ECRS
  launch year; 2024–2025 = normalised). Anchors per regime: 3 / 1 / 1 / 2 /
  **0**.

Cut finer still (the 2019 and 2020 ORDC parameter shifts, the mid-2024 ECRS
procurement changes) and every regime is a singleton. That degeneracy is not a
technicality; it is §3's central structural fact.

### 2.2 The ercot-198 audit as regime evidence

`FINDING-ercot198-t3b-adder-overlay-audit-2026-08-14.md` (T-3b, **MERGED to
main at the rebase**, PR #3944) sharpens the regime read with
settled published data: the pre-RTC+B design's **only two** energy-settlement
price adders are the published **RTORPA** and **RTORDPA** ("The current ERCOT
market design features two distinct price adders", 2024 SOM p.43), together
worth 0.477 $/MWh demand-weighted in 2024 and 0.410 in 2025 (Feb-2025 alone
+1.50), **and both were retired at the RTC+B go-live 2025-12-05** — the
committed telemetry series honestly END there. The design's scarcity-pricing
plumbing is therefore a measured, committed, regime-keyed object — and it is
precisely the object the 2026+ design REPLACES. Evidence FOR the regime read
of history; evidence AGAINST any claim that the measured regimes extrapolate
forward.

## 3. THE IDENTIFICATION QUESTION — confronted, with the arithmetic on the table

### 3.1 What a V0-analogue gate would have to be

The honest analogue of the charter's V0, pre-stated: **leave-one-vintage-out
across the anchors, predictions formed from same-regime anchors only, the same
bar (±25 % or ±15 $/kW-yr, whichever is larger, CT and CC, EVERY fold), plus a
forward-transfer clause for the RTC+B regime.** Nothing weaker deserves the V0
name: cross-regime pooling smuggles in either a tightness term (refused,
DO-NOT-REDO) or an uncited prior.

### 3.2 What the committed anchors do to that gate (probe output, `results/calibration/ercot200_regime_partition.json`)

| cut | regime | n | ex-ante gate verdict |
|---|---|---|---|
| coarse | pre-2022 ORDC ($9k SWCAP) | 3 | **FAILS for ANY regime-only R_f** — 2019 vs 2020: rent gap $88 (CT), irreducible ≥ $44 vs $15 tolerance; Uri pairs ≥ $286–$374 |
| coarse | 2022 ORDC-widened | 1 | **UNTESTABLE** — singleton: leave-one-out leaves zero same-regime anchors |
| coarse | ECRS era 2023–2025 | 3 | **FAILS for ANY regime-only R_f** — 2023 vs 2024/2025: irreducible ≥ $80–$94 vs $15–$22 tolerance |
| coarse | RTC+B 2026+ | **0** | **NO ANCHORS** until the 2026 SOM (~mid-2027) |
| fine | ECRS launch 2023 | 1 | **UNTESTABLE** — singleton |
| fine | ECRS normalised 2024–2025 | 2 | within the bar (irreducible $7.70 CT / $3.02 CC vs $15 / $20.74) — the ONE coherent measured regime |
| fine | (others) | — | as above |

Three structural facts, none repairable by fitting technique:

1. **Singleton regimes are untestable by construction.** With one anchor, the
   held-out vintage's regime has no other anchor to predict from; the "fit" is
   the anchor itself — a level pin wearing a date. The coarse cut has one
   singleton; the fine cut has two; a finer cut has only singletons.
2. **The multi-anchor regimes fail the same model-free bound that killed
   tightness — except one.** Any function of regime alone must assign
   near-equal predictions to same-regime years, so its best-case error on a
   within-regime pair is half the rent gap. Pre-2022: 2019 vs 2020 pay 127 vs
   39 $/kW-yr **under an identical design** (and, per FINDING-ercot195, at
   measured tightness within 1.7 % — cited, not recomputed) → irreducible
   ≥ $44 vs a $15 tolerance, for ANY regime-keyed function. The monitor's own
   design-stripping does not rescue it: ex-Uri 2021 (69 CT) inserted into the
   regime still leaves the 2019-vs-2020 pair untouched. ECRS-era coarse:
   2023 vs 2024 irreducible ≥ $86 (CT). **Only {2024, 2025} coheres** —
   irreducible $7.70/$3.02, inside the bar — and it is 2 anchors deep.
3. **The partition dilemma.** Coarsen the cut and within-regime variance
   exceeds the tolerance by 3–25×; refine the cut until every regime coheres
   and every regime is 1–2 anchors — a lookup table of history, i.e. the
   re-labelled level pin of §4's counter-argument. There is no intermediate
   cut on this data that yields ≥ 3-anchor regimes that pass. **The dilemma is
   a property of 7 anchors spanning ~4 design regimes, not of any fitting
   choice.**

### 3.3 The forward regime, stated without softening

Every forward screen year (≥ 2026) is RTC+B. The regime variable **does not
vary within the applicable horizon**, and the RTC+B regime has **zero measured
anchors until the 2026 SOM publishes (~mid-2027)**. Consequences:

- **No leave-one-out discipline of any strength can exist for the forward
  regime today.** One anchor (mid-2027) makes the forward level *quotable but
  unfoldable*; the earliest fold-testable RTC+B read is **two vintages in,
  ~mid-2028** (2026 + 2027 SOMs) — and that is a 2-anchor regime, the same
  thinness {2024, 2025} has now.
- The charter already pre-registered the trigger (§2.5, verbatim): *"the
  first RTC+B-era SOM vintage re-derives R_f with a regime term (or a
  post-2026 segment); the citation is the new vintage, never a residual."*
  The wait is not new governance; it is the governance already signed.
- **The honest answer to the authorized question is therefore: assemble now
  (cheaply, read-only), identify only after the 2026 SOM lands — and say
  plainly that what becomes identifiable then is an RTC+B-era LEVEL from
  within-regime anchors, not a cross-regime relation.** The measured history
  (2019–2025) cannot validate a forward RTC+B number under any admissible
  gate; it can only bound plausibility (the normalised-era 52–89 $/kW-yr band
  is the design-adjacent comparator the record offers, with the regime-change
  caveat cutting both ways).

## 4. RULE-13 ADMISSIBILITY, ARGUED BOTH WAYS (the §2.6 pattern — the adjudication is the OWNER'S)

### 4.1 What distinguishes a regime-keyed measured relation from the refused row-4 scalar

Re-scoring the charter §2.6's four owner-signed properties for a
design-conditioned term:

1. **Never touches the price object** — unchanged; the term stays a labelled
   screen revenue line. HOLDS by construction.
2. **Conditioned, regenerates forward** — the conditioning variable is
   *exogenous and calendar-known* (RTC+B go-live is a tariff fact; SWCAP is a
   PUCT rule; ECRS existence is a market rule; none is a model output or a
   residual). A 2035 screen year KNOWS its design regime without solving
   anything. In this one respect regime conditioning is *cleaner* than
   tightness: the driver cannot inherit model error.
3. **Identification measured-vs-measured** — SOM rent vs published design
   regime, both coordinates published; no model quantity in the fit. HOLDS in
   form; §3 says whether it holds in content.
4. **Subtraction-reconciled sunset** — the S_f construction carries over
   unchanged; a future in-model formation improvement still drives the term
   to zero. HOLDS by construction.

Further for: the regime read is not an invention — it is the monitor's OWN
causal account (three of seven vintages attributed by name), the V0 finding's
own diagnosis, and the ercot-198 audit's measured plumbing. Conditioning on
the variable the data actually exhibits is the opposite of ignoring the data.

### 4.2 The honest counter — why this may be the refused knob wearing a date

1. **Regime dummies with 1–2 anchors each are a re-labelled level pin.** "Add
   $X in the ECRS era" is *"add $X"* with a date range attached — FFR-6A
   verdict row 4's refused *"scalar uplift/offset … (any 'add $X', 'scale to
   SOM/actuals')"* — and §3.2's dilemma shows the identification cannot rise
   above that on this data: every coherent regime is 1–2 anchors.
2. **Forward, the conditioning variable is a constant.** Every applicable
   screen year is RTC+B, so within the horizon the term never varies with
   anything — not fleet, not load, not weather. Property 2's "responds to
   changed conditions" (rule 13's own test, charter §2.3) fails **in content**:
   a thin 2035 fleet and a long 2035 fleet get the same rent term. The
   tightness instrument, whatever its failure, at least attempted condition
   response; the regime instrument abandons it. (Restoring response via a
   within-regime tightness term is refused by name — V0 DO-NOT-REDO.)
3. **The within-regime variance is the term's own error bar.** 2019 vs 2020:
   $88/kW-yr apart under one design at near-identical measured tightness. The
   committed record offers NO admissible variable that explains it — which
   means a regime-level term carries O($40+) of irreducible error against a
   ~50–70 $/kW-yr target: the error is the size of the object.
4. **The forward number would be anchored on zero points until mid-2027** —
   any RTC+B value chosen before then is exactly "a level chosen without
   conditioning content", the FINDING-ercot195 §5 phrase for what the gate
   refused to ship.

### 4.3 Where that leaves the question

The FOR case is real (exogenous driver, measured-vs-measured form, sunset
intact) and the AGAINST case is real (level-pin adjacency at 1–2 anchors per
regime, forward constancy, unexplained within-regime variance). What tips it
is §3's arithmetic: **admissibility-in-form cannot be cashed into an
identified object today.** The owner can sign the distinction only when there
is something identifiable to which it applies — which is after the RTC+B
regime has measured anchors. That is why the board below routes to
wait-for-data rather than to a live admissibility signature now: **an
admissibility ruling on an unidentifiable object would be a signature with
nothing under it.** The adjudication remains the owner's; this card supplies
the evidence, both ways, and takes no step.

## 5. CARD W — THE OPTION BOARD

**(W-0) WAIT-FOR-DATA — do nothing until the first RTC+B-era SOM vintage
lands. RECOMMENDED.** (a) *What is waited FOR, named:* the **2026 SOM
(~mid-2027)** — the first measured RTC+B anchor; the charter §2.5 re-derive
trigger is **already pre-registered** and fires on exactly that vintage ("the
citation is the new vintage, never a residual"). Two vintages (~mid-2028)
make the forward regime fold-testable at {2024,2025}-class thinness.
(b) *Admissibility:* trivially clean — nothing is built, nothing argued into
the model. (c) *Reach bound:* $0.00/kW-yr now, honestly; the screen keeps the
charter §1 understatement, disclosed at L-0-adjacent magnitude but NOT entered
as a `readiness_limits` row (adjudication item (iii): the row is NOT entered;
frontier rank 2 stays OPEN). **Corrected at the rebase (§0.1): L-2 has since
STOPPED (ercot-201) and T-1 is NON-VIABLE (ercot-202), so the
single-digit-to-~20 $/kW-yr movement this line originally credited to L-2 is
gone — the honest reach bound across the whole frontier-rank-2 lane is now
$0.00/kW-yr from every executor, not just from W-0.** That makes the wait a
real one, and the owner should read it as such.
(d) *Cost:* zero sessions; the deriver
(`scripts/data/derive_screen_scarcity_rent.py`) already stands as the
re-derive test.

**(W-1) ASSEMBLE-AND-HOLD — the design-attribution assembly, read-only, as
W-0's companion.** (a) *Driver:* the monitor's own published counterfactuals,
already transcribed and committed (2021 ex-Uri CT 60–78 / CC 81–105; 2023
ECRS share 0.5 with "absent ECRS … very close to CONE"; the ercot-198
published-adder series) — fold them into the `som-competitive-conduct`
datatype as explicit regime/attribution columns so the mid-2027 re-derive is
one command against a regime-labelled anchor table. (b) *Admissibility:* data
intake + schema documentation, unrestricted under the 2026-08-06 rule-22
clarification; NO `ScenarioConfig` field, NO parameter, nothing armable
(rules 24/26 satisfied by construction — a labelled CSV cannot be re-armed).
(c) *Reach:* $0.00/kW-yr direct; buys the future lane a clean start, the same
way the ercot-195 intake (3→7 vintages) did. (d) *Cost:* one doc/data
session, no solve; dispatchable by the manager without a sitting if the owner
signs W-0 (it executes no decision — it curates committed evidence).

**(W-2) ATTEMPT IDENTIFICATION NOW on the 4-regime / 7-anchor set — REFUSED
EX ANTE, recorded so its absence is a decision.** (a) *The gate it would
need*, stated per the dispatch: §3.1's V0-analogue (same-regime LOO, same
±25 %/±15 bar, every fold, forward-transfer clause). (b) *Its feasibility,
honestly:* **the probe already computes the outcome without spending
anything** — singleton regimes (2022; 2023 on the fine cut) are untestable;
the pre-2022 and coarse-ECRS regimes fail the model-free half-gap bound for
ANY regime-only function ($44–$374 irreducible vs $15–$22 tolerances); the
only passing regime is {2024, 2025}, n=2; the forward clause is untestable at
n=0. A formal W-2 run would reproduce `FAIL` with certainty. (c) *Reach:*
$0.00 — it cannot ship anything the gate would pass. (d) *Cost:* one wasted
session plus the risk the record acquires an "attempted, failed" entry that
invites band-widening pressure later. Refusing now on computable arithmetic
IS the V0 discipline (the lane that stopped rather than fit — A1.3's "a
correct stop, not a failed worker").

**(W-3) A STRUCTURALLY DIFFERENT INSTRUMENT — recorded VACANT on the
committed record.** Candidates checked and why each is not it: the SOM
**peaker-net-margin series** (on disk, 2025 row) is an equilibrium OUTCOME of
the same prices — conditioning on it is the outcome-import pattern rule 13
polices, with no forward analogue the model doesn't already fail to form; the
**published-adder overlay** (ercot-198) is measured and committed but is
regime PLUMBING that RTC+B retires — it cannot reach any forward year by
construction; **cross-ISO transfer** of another monitor's rent relation is
refused by rule 25; **within-regime tightness** is the dead instrument
(DO-NOT-REDO). **Corrected at the rebase (§0.1):** this option originally
pointed at **L-2 (E1 dispersion repair)** as the live structural complement
whose restoration would raise S_f and shrink any future term, exactly as the
charter's sunset intends. **L-2 stopped at Phase 0 (ercot-201) — its surface
superseded by FFR-8B/FFR-9A, its identification route barred by an
adjudicated prior stop.** W-3 is therefore vacant in the strong sense: the
committed record now supports **no** structurally different instrument AND
**no** live structural complement. Filling it needs an identification the
record does not currently contain — which is itself a finding for the
sitting, not a task this card hands anyone.

**Recommendation: W-0, with W-1 as its read-only companion; W-2 refused ex
ante; W-3 vacant.** If the evidence at the mid-2027 re-derive shows the RTC+B
regime cohering (as {2024, 2025} now does), the successor card brings the
owner a *then-identifiable* object and the §4 admissibility question becomes
signable with something under it. If the owner instead judges today that the
regime family is row-4-forbidden at any anchor depth (§4.2's case), the
honest fallback remains the charter §6 L-0 disclosure route — which
adjudication item (iii) explicitly did NOT enter, and which stays owner-only.

## 6. GOVERNANCE — DO-NOT-REDO, fences, and what this session did not touch

**Matrix cells checked before any option was named**
(`docs/mechanism-testing-matrix.md` §5.1 + the ERCOT shard
`docs/codebase-site/data/mechanism-matrix/ERCOT.js`, at `5bf5f13`, re-checked
at `315a2452` — the only ERCOT matrix edit in between is ercot-202's
`gas_monthly_actuals` NOTE correction, verdict **G** unchanged, and it touches
no cell cited below):
`ordc_scarcity_overlay` **R** (ERCOT-97 — no ORDC overlay lever is proposed;
the refusal stands); `ercot_rtordpa_overlay` **K** (read by ercot-198, read
here in citation only, changed nowhere); `capacity_screen_unified_lookahead`
fc **K** and `capacity_screen_scarcity_restoration` fc **K** (the promoted
stage-B screen posture every option leaves untouched; their FFR-6A/FFR-8A
decompositions are cited as evidence only); `storage_measured_anchors` **K**
(untouched). No `R`/`I`/`G` cell is proposed for re-test; no option drafted
would re-test one without new evidence. The L-SCAR term itself has **no
matrix row** — rule 28(c) attaches the row duty to adding a `ScenarioConfig`
field, and none exists (the FINDING-ercot195 §5 reading, unchanged here).

**Fences honored.** Doc-only: no `ScenarioConfig` field, no matrix row/cell
edit (**a card is a read** — recorded per the ercot-182/189/196 precedent),
no solve, no LP, no year solved or scored (rule 22: ERCOT holds no
`complete`/`final` marker; the probe reads a committed CSV of published SOM
tables, {2019–2025} data intake unrestricted per the 2026-08-06
clarification, and touches no model artifact), no model input touched (rule
13 — measured data entered a measured-vs-measured feasibility computation
only), no keeper/registry/bench contact (keeper stays
`2026-08-12-run192-arm-coal-peak`), no new workflow. Standing rulings cited
and honored: **Q-B FINAL** (no ERCOT C3a-2023 spend of any kind —
`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`;
2023 appears on this card only in anchor tables and citations, never as a
target); **R-A** (NOT-YET stands; no C3b-2023-targeted determination rounds —
`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`); the
**L-SCAR charter §4 must-nots bind every option drafted above** (every option
leaves dispatch prices, LP objectives, scored series, backcast artifacts, the
ORDC/reserve/co-opt reconciliation, the refused FFR-6A rows 3/4, holdout
years, and the FFR-9C/OVERRIDE-FIX seam untouched); **V0 = DO-NOT-REDO for
tightness conditioning** (no tightness variable read, fit, or argued anywhere
in this card or its probe; the 2019/2020 tightness near-tie is cited from the
committed finding). The **L-2 lane (L2-BUILD) is separate** — referenced in
§5 W-3 and §0.1, overlapped nowhere; it STOPPED at Phase 0 on main
(ercot-201) and this session neither continued nor re-opened it. The T1-EXEC
lane is likewise untouched (it closed non-viable at ercot-202; this card
substitutes no lever for it). Rule 27: session is Fable, continued under
Opus 5; files pushed ≥300 lines are blob-verified after push, on the
rebased branch as well as the original.

**Artifacts this session commits:** this card, the probe
(`scripts/probes/ercot200_regime_partition.py`), its JSON
(`results/calibration/ercot200_regime_partition.json`), and one
`docs/calibration-log/ercot.md` entry. Nothing else.
