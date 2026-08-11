# FINDING — caiso-191: campaign adjudication (Wave 0C) — seven owner rulings RECORDED, the lane inventory CLOSED at five gate specs + one desk-refused lane, the caiso-187 §4 defect CURED into lane 2's spec, lane 5 adjudicated **GO WITH SCOPE RESTRICTIONS**, lane 6 adjudicated **NO CITABLE AXIS — stays a declared residual**, and Wave 2 pre-committed before any Wave-1 result exists

**READ-AND-WRITE-DOCS ONLY, executed as chartered: no code, no config, no keeper, no
status, no attestation file touched; ZERO LP solved; no matrix cell verdict moved; no
data byte written.** Keeper unchanged at **`2026-08-09-caiso-188-d1-micseam`**
(NOT-YET; C3a the sole load-bearing FAIL, +3.4 / +10.4 / +12.9 % vs ±10 %; DOF ledger
11 / 8). C3a was never read as a number to act on. 2023–2025 only; both holdout
markers untouched (owner acts).

This session is the campaign's governance keystone: it authors the acceptance gates
for every measurement lane BEFORE anyone measures, so no downstream session can shape
its own gates. The facts it verifies were checked against origin/main HEAD
`63c48a401` (the charter's `767b29c3` is an ancestor; every campaign-frame fact
re-verified at HEAD — see §6 contradictions).

## §1 — What this session wrote

| artifact | content |
|---|---|
| `caiso191-owner-rulings-2026-08-11.md` | the seven owner rulings of 2026-08-11, recorded as rulings; the CLOSED lane inventory; the exhaustion-memo charter |
| `GATESPEC-caiso192-overlay-identification-2026-08-11.md` | lane 1 — overlay mechanical-vs-economic identification (ruling 1) |
| `GATESPEC-caiso193-wefor-residual-2026-08-11.md` | lane 2 — the granted narrow arm, carrying the §2 cure of caiso-187 §4 |
| `GATESPEC-caiso193-stgas-wefor-2026-08-11.md` | lane 3 — CAISO-derived cited ST_GAS WEFOR base |
| `GATESPEC-caiso194-hydro-ror-split-2026-08-11.md` | lane 4 — `hydro_ror_split` made effective |
| `GATESPEC-caiso195-ps-physical-2026-08-11.md` | lane 5 — PS cited-physical parameters (GO, §3 below) |
| `caiso191-integration-protocol-2026-08-11.md` | Wave 2 pre-committed: ladder, control tolerance (ratified), composition rules, flip protocol, C3a-blind promotion, degenerate case |

Every gate spec embeds the campaign's direction-hazard clause verbatim, closes its
instruments against every LMP/price series, anchors every numeric band to a
published expectation, a physical-stationarity argument, or a pre-existing repo
measurement — never to the values under adjudication (21.6/26.2/31.9 % etc.) and
never to anything derived from the C3a residual — and biases every classifier
ambiguity AGAINST the C3a-favorable direction.

## §2 — The caiso-187 §4 pre-registration defect, cured (STEP 3)

**The defect, precisely:** caiso-187's PRECHECK §2 fixed the arm's value as ONE
capacity-weighted scalar over all covered classes present ({CC_REGULAR, CC_CHP,
ST_GAS} → 0.0303), while its own protective gates G-NODOUBLE/G-SCOPE ruled that a
class with `X_c = 0` gets no relief. On the measured data the two were mutually
inconsistent: the scalar would have handed ST_GAS — zero overlay coverage — a ~12 pp
capability release (0.147 → 0.0303). caiso-187 declared the inconsistency as its own
error, refused to repair its pre-registration mid-session, and escalated (Branch C).

**The cure, written into lane 2's gate spec §1:** a clean re-pre-registration
committed before any solve that (i) declares the scoped-groups form the ONLY form —
no cross-class aggregation over heterogeneous coverage, ever; (ii) declares the
protective gate DOMINANT over any formula, in advance; (iii) takes the owner-granted
values (0.0 / {CC_REGULAR, CC_CHP} / multiplier 1.0) from the frozen
`_caiso187_residual_identification.json` with no recomputation; (iv) leaves ST_GAS's
WEFOR untouched in that arm.

## §3 — Lane 5 adjudication: **GO WITH SCOPE RESTRICTIONS** (owner ruling 7's condition, discharged)

The object: per-plant pump-power ratings, durations, zone assignment for
Helms/Eastwood/Gianelli/Hyatt/Thermalito/O'Neill, and Hyatt's
primarily-conventional-release mode, all from public FERC/CEC/EIA-860 sources —
replacing the single aggregate NP15 unit with fleet-average constants.

**Fence (a) — caiso-140 §D/§G: "re-testing single-component supply additions
≤1.5 GW against C3a-2025."**

* *The case that it is breached:* the campaign's motive for touching PS at all is the
  C3a campaign; a per-plant split that reduces effective belly pumping (Hyatt's
  293 MW pump-back demoted; zone splits) is a ≤1.5 GW supply-STATE change in the
  flattering direction, launched from a campaign whose end goal is C3a closure —
  arguably the fenced re-test with the scoring moved off-ledger.
* *The case that it is not:* the fence's own words kill charters that TEST small
  supply additions **against C3a-2025** — caiso-140 closes by saying "the kill is
  instrument-agnostic arithmetic, not a verdict on any one lever's realism." Lane 5
  adds **zero MW** (G-AGG conserves the EIA-860 aggregate), claims no C3a closure,
  and its acceptance basis is citation integrity + engagement, **C3a-blind** —
  there is no "against C3a-2025" anywhere in its acceptance. It is rule-14
  provenance work of exactly the class the owner-sitting §3.4 licensed for the
  import ledger: replacing fitted/averaged values with measured ones because
  measured is better, whatever the fit does.
* *Resolution:* the fence is not breached **provided the acceptance stays
  C3a-blind**, which the gate spec hard-codes (§0, §5, §6). Not ambiguous on the
  fence's own text.

**Fence (b) — caiso-141 §G: the fabricated-shape prohibition.**

* *The case that it is breached:* Hyatt's "primarily-conventional-release mode"
  could be implemented by pulling Hyatt out of the storage block and re-allocating
  its energy into conventional hydro — which forces an hourly allocation decision,
  and ANY such allocation is §G's "assumed/fitted allocation."
* *The case that it is not:* pump ratings, durations, zone geography, and a static
  cited pump-back capability bound are time-invariant physical parameters, not
  shapes; the LP remains the unrestrained optimizer within them. caiso-141 §B itself
  records Hyatt's mode ("primarily a conventional-release plant; pump-back is the
  minority mode") — a pre-existing repo record with a public-document trail.
* *Resolution:* GO **only under the scope restriction that makes the breach
  impossible**: Hyatt stays IN the storage block, its mode expressed solely as a
  static cited parameter bound; no energy re-allocation, no time-profile input of
  any kind; a component that turns out to need a synthesized shape is dropped, and
  if inseparable the arm dies (gate spec §1, §4.2–4.3, G-NOSHAPE). With that
  restriction, nothing lane 5 does synthesizes a shape, so §G is not touched.

**Verdict: GO**, conditions embedded as gates: single bundled arm; every value cited
in the PRECHECK before solve; zones pure geography; no intake/shape synthesis of any
kind; Hyatt conservative-defaulted to full PS if its citation is not airtight;
ambiguities resolve toward MORE pumping capability (against the flattering
direction); acceptance on citation integrity + engagement, C3a-blind. The default
was NO-GO; the GO is issued because both fences, read on their own texts, are
discharged by restrictions the spec makes structural rather than by argument.

## §4 — Lane 6 desk adjudication: **NO — stays a declared residual** (STEP 6)

The 8,800 MW of uncited import spot capacities (PNW_midC 1,800 / DSW_CCGT 1,800 /
DSW_CT 2,200 / WECC_scarcity 3,000). The question: does ANY citable derivation axis
exist outside the caiso-188 §7 fences? Candidates, each to a verdict:

| axis | verdict |
|---|---|
| MIC sizing | **FENCED** (caiso-188 §7.2): an annual RA-showing allocation already spent twice (firm split + seam limit); a third use is a rule-19 double-count on a category error. The DSW ladder's 0.7–4.8 % near-match to the south MIC is recorded provenance-suggestion, not a derivation. |
| Q-Q revealed supply curve (capacity axis) | **FENCED** (caiso-188 §7.3): the inverse of the same monotone duration coupling whose price axis failed its pre-registered LOYO at 30.5 % vs a 25 % bar (caiso-83/86/86b). |
| plateau re-attribution | **FENCED** (caiso-188 §7.1): the ladder is the tightest corridor ceiling in 0 of 26,280 DSW corridor-hours; the plateau's level is the measured hub's. |
| published path ratings | **NOT A DERIVATION AXIS** (caiso-188 §3.1): they map only to the ceiling role, which the measured p95 envelope owns in 25,866 of 26,280 corridor-hours; re-grounding would be inert in ≥98.3 % of hours and would LOOSEN the bound in the 214 where the fitted depth binds. |
| EIA-930 measured flows | **ALREADY SPENT** as the corridor deliverability envelope — a second use on the same physical quantity is rule 19 again. |
| WECC path utilization / e-Tag | the same measured-flow object at coarser grain; resource-grain e-Tag data is not public. **No public instrument.** |
| the limb's LIVE role (CARB-EF breakpoint placement) | caiso-188 §3.1 verbatim: **"Nothing published maps to the live role."** |

**Disposition: the 8,800 MW stays a DECLARED residual** — an open root-cause issue
under rule 21, honestly described since the caiso-188 ledger repair
(`n_scalars: 6`), with **no build session reserved** and the root-cause issue
standing open on the ledger's own text. Any future attempt requires new evidence and
a fresh adjudication (the charter). Desk-only; no probe was run because every input
to this table is a committed measurement quoted from its FINDING.

## §5 — What Wave 2 is bound to (STEP 7, summarized; the protocol file governs)

Ladder control → +L1 → +L2 → +L3 → +L4 (→ +L5), inclusion strictly by Wave-1
structural verdicts, C3a never consulted; one mechanism per rung, all three years
per bundle; per-rung re-verification = engagement + ledger arithmetic (plus the
lane-2 premise recheck `X_c^filtered ≥ W_c`) — Wave-1 identification not
re-litigated; structural failure at composition ⇒ deterministic skip on the previous
base; criteria flips ⇒ input-side re-examination, ACCEPT-WITH-FLIP + escalate if the
input survives (rule 14); promotion C3a-blind on structural superiority (caiso-183);
the promotion attestation re-measures C3c exceptions (caiso-189 §8.3 made the rule);
zero surviving arms ⇒ null-FINDING to closeout. **Control tolerance RATIFIED:
per-year |ΔC3a| ≤ 0.1 pp and |ΔC3b| ≤ 0.005** — bit-zero is the observed CAISO norm
(caiso-184; caiso-188 G-CTRL) and is expected, but byte-identity is not the gate
because head drift is measured reality elsewhere (ercot-173/run168b); the ceiling
sits an order of magnitude below every decision margin; in-tolerance deltas are
quoted as the noise floor first; out-of-tolerance is a stop-the-line finding about
the head. The control recipe's two environment conditions (capacity-deliverability
partition materialized + `hydro_ror_split` explicitly False, both disclosed) are
fixed in protocol §3.

## §6 — Contradictions and record notes (reported, never silently resolved)

1. **HEAD advanced past the charter's verification point:** charter facts verified
   at `767b29c3`; origin/main is `63c48a401` with `767b29c3` an ancestor. Every
   campaign-frame fact was re-verified at HEAD (keeper id, NOT-YET, C3a values, DOF
   11/8, empty lever queue, `wefor_multiplier` 0.7, `hydro_ror_split` advertised
   true). No contradiction found.
2. **The caiso-189 sentinel EXISTS on origin/main** (`scripts/
   gen_caiso189_attestation.py`; PR #3854 merged), so the charter's "calibration log
   is incomplete until caiso-189 merges" clause is resolved in the licensed
   direction: this session's log/matrix appends are made directly (no LOGDRAFT
   block needed).
3. **A 2023 C3a discrepancy between two committed records:** the mechanism-matrix
   §5.2 header prints the caiso-188 keeper's C3a as "+3.7 / +10.4 / +12.9 %", while
   the caiso-189-generated attestation and the calibration log print
   **+3.4 / +10.4 / +12.9 %** (the arm's own 2023 value; +3.7 is the control's).
   Both are PASSes in 2023 and no verdict is affected. Reported for the matrix
   lane; NOT fixed here (this session moves no matrix verdict content).
4. **The keeper bundle's `metrics.json` is a pre-caiso-189 snapshot** (it still
   carries `reasons: ["governance gate UNATTESTED…"]`, fails 2, scored 7). This is
   consistent with caiso-189's repair being scorer-side on committed artifacts (the
   attestation, not the score-time snapshot); the current determination per
   `calibration_verdict.py` at HEAD is NOT-YET on C3a alone. Observed, not touched.
5. **caiso-190's `resolved_inputs` is NOT on origin/main** (no artifact found), so
   lane 4's engagement gate binds on its fallback proof (guard + log + LP-delta),
   with the caiso-190 instrument cited only if it lands before that lane solves.
6. **The charter's required-fall figures verify:** −$0.16/MWh (2024) and −$1.01/MWh
   (2025) follow by arithmetic from the caiso-189 refreshed magnitudes (38.27 vs
   34.65; 38.87 vs 34.42 → falls to the ±10 % edge of 0.155 and 1.008). The
   owner-sitting memo's 0.184/1.074 were the caiso-184-keeper values; both records
   are correct at their own scopes.
7. **The C3b 2025 watch margin (0.164/0.20)** is quoted from the campaign frame; the
   committed bundle `metrics.json` carries criterion status only, so it was not
   independently re-derivable here. Lane 4's spec therefore requires the measuring
   session to re-derive the control's C3b at full precision before reading any arm.

## §7 — Governance

Rule 1 `[R-STRUCT]` — every acceptance basis authored here is structural; C3a is
inadmissible as evidence in every spec, in both directions. Rule 13 `[R-MEASURED]` —
every gate instrument is a measured/published input; the caiso-141 wall re-affirmed
(ruling 4); no fabricated shape is licensed anywhere. Rule 14 `[R-ACCURATE]` — the
flip protocol forbids rejecting an accurate input on fit; lanes 3/5 are rule-14
provenance work, chartered as such. Rules 15/16 — no run was completed here, none
registered; every future arm is bound to full-span bundles and registration by its
spec. Rule 19 `[R-ONE-MECH]` — one mechanism per arm and per rung, hard-coded in
every spec. Rule 21 `[R-DOF]` — lane 2 targets 11/8 → 11/7 by arithmetic; lane 6's
8,800 MW stays an open root-cause issue, never re-fitted. Rule 22 `[R-HOLDOUT]` —
2023–2025 only everywhere; markers owner-only. Rule 23 `[R-FROZEN-DERIVE]` — lane 1
recites its source-defect cause; the merit-guard constants are used as shipped;
lane 4 forbids curator rule changes. Rule 24 `[R-REGISTRY]` — no new field authored
here; lane 5's parameter surface is required to register properly. Rule 25
`[R-ISO-SCOPE]` — every spec fences the other five ISOs; MISO's 0.10 and ERCOT's
0.21/0.02 are fences and explanation obligations, never evidence. Rule 27
`[R-PUSH]` — docs-only additive commits, pushed per Git & Pushing. Rule 28
`[R-MECH-MATRIX]` — no cell verdict moved (nothing tested); a §5.2 session block
records this adjudication; duty (b) obligations are written into each lane's spec.

---

## SESSION-REPORT caiso-191 campaign-adjudication

* **STATUS:** COMPLETE — all eight steps executed; docs-only, zero LP, keeper
  unchanged.
* **RULINGS RECORDED:** 7/7 (`caiso191-owner-rulings-2026-08-11.md`), plus the
  closed-inventory charter.
* **GATESPECS:** `GATESPEC-caiso192-overlay-identification-2026-08-11.md` ·
  `GATESPEC-caiso193-wefor-residual-2026-08-11.md` ·
  `GATESPEC-caiso193-stgas-wefor-2026-08-11.md` ·
  `GATESPEC-caiso194-hydro-ror-split-2026-08-11.md` ·
  `GATESPEC-caiso195-ps-physical-2026-08-11.md`.
* **§4 CURE:** the caiso-187 scalar-aggregation/G-NODOUBLE inconsistency is cured by
  a mandatory clean re-pre-registration — scoped-groups form only, protective gate
  declared dominant, owner-granted values frozen from the caiso-187 record, no
  recomputation (lane-2 spec §1).
* **LANE 5:** **GO** with scope restrictions — zero MW added and C3a-blind
  acceptance discharge the caiso-140 §G fence; Hyatt-in-storage-block as a static
  cited bound (no re-allocation, no shape) discharges caiso-141 §G.
* **LANE 6:** **NO citable derivation axis** — every candidate fenced, spent, or
  unpublished; stays a declared residual with the open root-cause issue standing;
  no build session reserved.
* **CONTROL-ε RATIFIED:** per-year |ΔC3a| ≤ 0.1 pp, |ΔC3b| ≤ 0.005; bit-zero
  expected (caiso-184/188), byte-identity deliberately not the gate (ercot-173 head
  drift); out-of-tolerance = stop-the-line.
* **FILES PUSHED + PR:** this FINDING + the rulings record + 5 GATESPECs + the
  integration protocol + `docs/calibration-log/caiso.md` append + matrix §5.2
  session block, on branch `claude/caiso-191-adjudication-gates-42mphe`, PR
  "caiso-191: campaign adjudication + gate specs".
* **CONTRADICTIONS:** four items reported (§6.3–§6.5, §6.7): the matrix-header 2023
  C3a +3.7 vs attestation +3.4; the stale pre-caiso-189 `metrics.json` snapshot;
  caiso-190 not merged (lane-4 fallback engaged); the C3b watch margin quoted but
  not independently re-derivable. None resolved silently.
* **LOGDRAFT:** NOT NEEDED — sentinel present on origin/main; log and matrix
  appended directly.
* **OPEN ITEMS / HANDOFF:** lanes 1–5 to sessions caiso-192/193/194/195 under their
  specs; Wave 2 under `caiso191-integration-protocol-2026-08-11.md`; the lane-6
  residual's root-cause issue stays open on the DOF ledger's own text; the matrix
  2023-C3a header discrepancy (§6.3) is left to the matrix lane; if C3a-2025 still
  fails after the ladder, the deliverable is an exhaustion memo, not a new lane.
