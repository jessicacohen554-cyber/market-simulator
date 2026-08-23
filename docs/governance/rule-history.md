# CLAUDE.md rule history — numbering, amendment genealogy, incident record

**Status: RECORD (living).** This file is the canonical home for the *stories*
behind `CLAUDE.md`'s Non-Negotiable Rules: how the rules are numbered and cited,
which owner amendments changed which rule and when, and the incidents that
produced a rule.

**It is not a source of norms.** Every binding sentence — every cap, gate name,
flag name, enforcement pointer and admissibility test — lives in `CLAUDE.md`.
If this file and `CLAUDE.md` ever disagree about what is *required*, `CLAUDE.md`
governs and this file is the one that is wrong.

---

## 1. How to cite a rule

Each rule carries a **stable inline ID** at its head (`[R-STRUCT]`,
`[R-VECTOR]`, … `[R-HOLDOUT]` for rule 22, `[R-PUSH]` for rule 27) *alongside*
its ordinal. Both are valid citations:

- **Prefer the ID** in new code comments, docs and handoffs — it survives any
  future insertion.
- **Ordinals are never renumbered.** Hundreds of existing citations across the
  repo say "rule N", and renumbering would silently repoint every one of them.
  A new rule is appended; a retired rule keeps its ordinal.

The IDs were added 2026-07-25 (Wave 5B of the refactor-consolidation lane) in an
additive-only commit, before any text was moved, precisely so that the slimming
commit had stable anchors to point at.

## 2. Audit numbering — "audit rule N" maps to CLAUDE.md rule N+1

`CLAUDE.md` rules **17–26** are the protective rules from
`docs/model-legitimacy-audit-2026-07.md` §8, where they are numbered **16–25**.
The offset exists because `CLAUDE.md` gained rule 16 (all-years-one-bundle,
`[R-ALLYEARS]`) *after* the audit was written. So a doc or code comment that
cites "audit rule N" maps to **rule N+1** in `CLAUDE.md`:

| audit §8 | CLAUDE.md | ID |
|---|---|---|
| rule 16 | rule 17 | `[R-FLOOR-WINDOW]` |
| rule 17 | rule 18 | `[R-PHYSICS]` |
| rule 18 | rule 19 | `[R-ONE-MECH]` |
| rule 19 | rule 20 | `[R-FORCED-BUDGET]` |
| rule 20 | rule 21 | `[R-DOF]` |
| rule 21 | rule 22 | `[R-HOLDOUT]` |
| rule 22 | rule 23 | `[R-FROZEN-DERIVE]` |
| rule 23 | rule 24 | `[R-REGISTRY]` |
| rule 24 | rule 25 | `[R-ISO-SCOPE]` |
| rule 25 | rule 26 | `[R-DELETE]` |

Older code comments predate the offset and can cite either scheme — e.g. the
rubric's C8 provenance clause refers to the no-floor-without-a-window rule as
"rule 12" (its number in a still-earlier revision) where the current file calls
it rule 17 / `[R-FLOOR-WINDOW]`. When a citation is ambiguous, resolve it by the
rule's *text*, not its number, and prefer the stable ID going forward.

Rule 22 (`[R-HOLDOUT]`) additionally supersedes the audit's original
D-6/rule-21 wording — see §4 below.

---

## 3. Rule 20 `[R-FORCED-BUDGET]` — forced-energy budget

The rule's normative text (the 15 % peaker / 30 % merchant caps, the 2 %
materiality floor, and the grounded-above-budget escalation on D-4 provenance +
D-1 shape) is in `CLAUDE.md`. Its **amendment narratives are owned by the
calibration rubric**, which is where the scorer-side definitions live:
`docs/calibration-determination-rubric.md` §C8 and §9 (version history).

- **Rubric v2.1 — owner amendments 2026-07-06.** Two changes touching this rule.
  (a) The **C8 peaker cap was raised 10 % → 15 %**, amending CLAUDE.md rule 20
  in place; the rubric records explicitly that *no external anchor exists for
  either value* — it is an owner risk-tolerance setting, logged as such.
  (b) A **materiality floor** was added to C7 *and* C8: the protective
  shape/forced-share gates score only classes whose annual energy — taken as
  `max(model, actual)` so forcing cannot self-exempt a class — is **≥ 2 % of
  total ISO load**. Smaller classes are still reported by the D-1/D-2
  diagnostics but never gated; the owner's rationale was that no structural work
  should be spent making a trivial class hit an r/CV or unforced target. This
  superseded the same-day C7-only 2.5 % cut landed by the L-15 lane
  (`f68ffed`/`29eafdf`): scope widened to C7+C8, X held at 2 % (owner-confirmed)
  so CAISO CT (2.1–2.3 % of load) and every PJM/MISO ST_GAS year stay gated.
  Effects at amendment are itemized in the rubric's v2.1 entry (ERCOT and PJM C8
  clear; NYISO CT and NEISO C7 become immaterial-skips; the caiso-42 flagship
  CAISO C7/C8 CT fails stand).

- **Rubric v2.2 — owner amendment 2026-07-07, grounded-above-budget
  escalation.** The caps and the materiality floor were left **unchanged**; what
  changed is that a material class *above* its cap is no longer an automatic
  FAIL but escalates to a conditional pass on provenance (D-4 off-window
  binding) + shape (D-1 diurnal profile). The reasoning the owner recorded:
  forcing can be legitimate past the budget when it is a real grid/RA/AS driver
  that reproduces the observed dispatch — *as much as needed* may be forced on a
  class that is structurally grounded and shape-faithful — so what the gate
  should target is forcing whose **window or shape doesn't match reality** (the
  "forcing variables are wrong" signal), not the raw share. Because every signal
  is read from the committed `legitimacy_diagnostics.json`, the change is
  scorer-only: no re-solve, no bundle regen, and existing keepers re-score in
  place, with C8 only ever *relaxing* (below-cap unchanged, above-cap gains a
  pass-path). Effect at amendment: no keeper flipped — CAISO-58's CT_PEAKER
  (`ra_mustoffer_bridge`, ~60 % forced) and NYISO-53's `reliability_floor ×
  ST_GAS` (~60 %) now FAIL with an explicit *"no declared D-4 window"* diagnosis
  instead of a flat over-cap fail, which names exactly what would ground them.

## 4. Rule 22 `[R-HOLDOUT]` — holdout tiers

The rule's normative text (the three tiers and their year assignments, the
touch-once discipline, the crossover window, the standing quarantine clauses and
the CI/`--holdout-authorized` enforcement) is in `CLAUDE.md`. Its **amendment
genealogy is owned by** `docs/handoffs/holdout-policy-memo-2026-07.md` §(e)–(f):

- **2026-07-06 — G-17 Option 2** (memo §(e)): the intake-vs-solve/score split.
  Data intake for an out-of-training period became permissible under explicit,
  session-logged owner authorization with no-LP validation, while *solve* and
  *score* stayed fully quarantined behind the calibration-complete marker. Both
  enforcement legs were already in place, so the decision cost only the rule-text
  edit.
- **2026-07-07 — three-tier split** (memo §(f)): the earlier two-window wording
  ("holdouts are 2022 + H1-2026, score once") was replaced by an explicit
  train (2023–2025) / validation (2022, iterable) / locked-test (2019 + H1-2026,
  touch-once) split, with the quarantine machinery carried over unchanged. This
  is also what supersedes the audit's original D-6/rule-21 wording.
- **2026-08-06 — the C3c standing rule** (session neiso-86, owner, verbatim: *"a
  c3c failure with all other gates passing should always be treated as a ledgered
  calibrated with caveats across all ISOs for holdout years and testing years
  going forward as a rule"*). A **lone** C3c failure with governance passing
  stopped failing a run to `NOT-YET` and became an auto-ledgered
  `CALIBRATED-WITH-CAVEATS`. Implemented as
  `calibration_verdict._apply_c3c_standing_rule` and scoped, at implementation
  time, to **out-of-training years only** — in-sample keepers kept needing an
  explicit exceptions-ledger entry.
- **2026-08-09 — extended to every year; rubric v3.2** (session
  neiso-keeper-87-control, owner, verbatim: *"make sure c3c is an acceptable
  caveat for any holdout or training year"*). Two parts:
  **(a)** the out-of-training restriction is removed, so the rule fires on
  2023–2025 as well. This resolves an ambiguity in the 2026-08-06 directive,
  whose own wording said "holdout years **and testing years**" while the
  implementation read it as validation + locked tiers only. It is not a
  loosening of the band: in-sample the identical reclassification was already
  reachable through an explicit ledger entry — the route every current keeper
  carrying a C3c caveat used — so the split governed who typed the
  justification, not what a run could claim, and since v3.1 C3c is the only
  ledgerable criterion at all.
  **(b)** a defect that had been suppressing the rule *as originally declared*
  is fixed: "lone" was measured over every scored record, including the
  REPORTED-ONLY streams the rubric demoted out of the determination (C5a `co2`,
  removed at v2.9), so an unrelated `co2` FAIL silenced it. It is now measured
  over `CRITERIA` membership. This under-fired the out-of-training years too, so
  (b) is a correction rather than part of (a).
  **Effect, measured over all 66 registered runs against a pre-change
  snapshot:** 2 determinations change, both NYISO **non-keeper** probes
  (`2026-08-06-nyiso-130-control`, `-n11-tsl`), both unlocked by (b); every
  keeper of all six ISOs is unchanged. The guards are untouched — lone failure
  only, governance must PASS, supporting-tier-only fail-closed, never
  `CALIBRATED`, single ledgerable slot still spent. Detail:
  `docs/calibration-determination-rubric.md` §9 (v3.2).
- **2026-08-17 — the ledgered caveat stops DOWNGRADING; rubric v3.3** (session
  nyiso-calibration-declaration, owner, verbatim: *"NYISO should be declared
  calibrated. C3c is an acceptable miss and shouldn't change a declaration from
  calibrated to calibrated with caveats because it's a known model limitation
  that's been ledgered"*). The standing rule's guard (d) is **split**: C3c still
  never reads `PASS` and its magnitude is still reported in full, but the
  resulting ledgered caveat no longer moves the overall determination, so an
  otherwise-clean run reads `CALIBRATED`. The clause *"the run can never read
  `CALIBRATED`"* — carried in the v3.0–v3.2 entries above and in CLAUDE.md rule
  22 guard (d) — is **withdrawn by the owner**; it is left verbatim in the prior
  entries as genealogy, annotated as superseded. Because ledgering has been
  restricted to C3c alone since v3.1, the amendment cannot reach any other
  criterion. **Everything else holds:** guards (a)–(c) entire; the ledger entry
  (or auto-entry) still required; the budgets untouched and checked first (>1
  ledgered or >0 protective is still `NOT-YET`, so the 1-slot ledgered budget is
  now the sole numeric bound on what may be carried without a downgrade); and
  every other caveat route — commercial-band misses, protective caveats,
  `SKIPPED` criteria, data-blocked years — still downgrades.
  **Effect, measured over all 26 registered runs against a pre-change
  snapshot:** 6 determinations change, all `CALIBRATED-WITH-CAVEATS →
  CALIBRATED`, of which **2 are keepers** — NYISO
  `2026-08-16-nyiso-140-layup-exclusion` (the requested ISO) and NEISO
  `2026-08-17-neiso-99-joint-p1`. The **NEISO flip is a cross-ISO consequence
  carried openly**: the scorer is one instrument and an ISO-scoped verdict rule
  would be an off-registry tuning channel in spirit (rules 24/25), so NYISO's
  determination could not be moved without moving every run of the same shape.
  No `NOT-YET` is reclassified; CAISO/ERCOT/MISO/PJM unchanged. Scorer-only —
  no re-solve, keepers re-score in place. **This does not touch the holdout
  tiers**: NYISO and NEISO both stay in `complete` only, both stay absent from
  `final`, and `holdout-freeze.json` stays ACTIVE, so no out-of-training year
  becomes spendable. Detail:
  `docs/calibration-determination-rubric.md` §9 (v3.3).
- **2026-08-17 — the first lane RESTED at `NOT-YET`** (session caiso-201, owner ruling Q1;
  record `results/calibration/caiso201-owner-ruling-2026-08-17.md`, packet
  `results/calibration/ASSESSMENT-caiso200-frontier-2026-08-17.md` §5). **No rule text
  changed** — this entry records the first time the rule's *designed* negative outcome was
  taken deliberately, so the precedent is citable. CAISO's in-model queue was exhausted **by
  measurement** (caiso-200's last named object returned +0.003 TWh of a ~0.116 TWh bound,
  measuring C1-2023 ~97 % structural), C3a genuinely failed (+12.8 %/+15.7 % vs ±10 %), and
  the 2026-08-11 ruling 5 had already DECLINED the rubric amendment that would have ledgered
  it. With both remaining C3a axes being owner-funding decisions previously declined
  (caiso-141 §G / ruling 4) or desk-refused (caiso-191 §4), the owner **accepted the resting
  state** rather than reach the band by a mechanism that is not real: the lane holds at
  `NOT-YET`, goes quiet, and re-opens only on new funded data. **The load-bearing precedent:**
  `complete` is a *merits* declaration, so an exhausted lane whose criterion genuinely fails
  rests — it does not ledger, does not lower a band, and does not declare. The `complete`
  marker stayed absent, `final` stayed moot, `holdout-freeze.json` stayed ACTIVE and no
  out-of-training year was touched, so the rule's enforcement machinery was never engaged.

## 5. Rule 27 `[R-PUSH]` — the 2026-07-15 `constants.py` truncation incident

Rule 27 exists because of one incident, and both of its halves — the
push-integrity protocol and the model-assignment restriction — are the owner's
response to it. The norms are in `CLAUDE.md`; this is the record of what
happened.

**What happened (2026-07-15).** A Sonnet session rewrote
`src/market_sim/config/constants.py` by pushing regenerated full-file content
through `mcp__github__push_files`. The model's response was clipped by its output
budget partway through the file, so the pushed blob was the *prefix* of the
intended content: the file went from **6,368 lines to 33**, and the push
succeeded — nothing in the path compares what was sent against what was on disk,
so a truncated file is indistinguishable from an intentional deletion.

**How the recovery made it worse.** Five follow-up "restore" commits tried to
rebuild the file incrementally and merged **fragments** to `main` — successively
0 / 500 / 1,020 / 1,000 lines — each one a partial file that parsed, imported,
and therefore looked plausible while silently missing thousands of lines of
constants. The failure mode is that a partial restore is *not* obviously broken;
it is a working file with missing values.

**What the owner ordered as a result.**

1. **Push-integrity protocol (all models, every session).** No bulk rewrite of an
   existing ≥300-line file from regenerated response content; edit locally and
   push the exact on-disk bytes; blob-verify (line count + content hash) after
   any `push_files` call touching a ≥300-line file, *before* doing anything else;
   never commit a placeholder, stub or partial "stage N" version of an existing
   source file, not even as a temporary restore step; a session that finds a core
   file truncated stops its own task and restores from the last good commit
   first. The binding wording is CLAUDE.md rule 27 and Git & Pushing §4.
2. **Model assignment.** Core-infrastructure scope (anything under
   `src/market_sim/`, `scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`,
   `model-methodology-spec.md`, `.github/workflows/`) is Opus or Fable, never
   Sonnet; and for the retirement-calibration lane specifically, *all* remaining
   sessions are Opus/Fable regardless of scope.

**Mechanical enforcement.** `.github/workflows/file-integrity-guard.yml` fails
any PR — and flags any push to `main` — that shrinks a core file by more than
30 % or deletes it, unless the PR carries the `intentional-shrink` label. It is
path-filtered to `src/**`, `scripts/**`, `CLAUDE.md`, `model-methodology-spec.md`
and `.github/workflows/**`, guards only files that were ≥300 lines at the base
commit, and follows renames to their destination so content must survive a move
intact. Its own header cites this incident.

**The ≥300-line deadlock, and the 2026-07-25 owner waiver.** Rule 27 forbids
pushing an existing ≥300-line file as regenerated response content, and Git &
Pushing bans `git push` outright — so for any file at or above that threshold the
two rules together left **no compliant push path**. Wave 4C hit it directly:
`retirements.py` (1,804 lines / 88,612 B) sat un-applied on `main` as a verified
patch file for exactly this reason, and the same deadlock blocks `scenarios.py`
and `runner.py`. Asked to adjudicate, the owner **waived the API-only rule for
that commit** and authorized `git push`. It succeeded — no HTTP 413 — and the
pushed blob verified byte-exact (`3a0b919e`, 1,804 lines / 88,612 B).

The waiver's reasoning, for future sessions to weigh rather than copy: rule 27
exists to prevent *truncation*, and truncation is impossible over git's
integrity-checked transport, so `git push` does not implicate the hazard rule 27
guards. The 413 that motivated the API-only rule is a function of **pack size**,
not file size — this delta was ~5 KB. That said, **the waiver was per-commit and
is not a standing exception**: the API-only rule stands as written, and a session
facing the same deadlock should surface the choice to the owner rather than
assume this precedent. What the incident establishes is that the deadlock is
real and needs a general owner decision, not that `git push` is now permitted.

---

## 6. The 2026-07-22 history rewrite — orphaned bundle `git.sha` provenance (owner decision B)

**What happened (2026-07-22).** The owner ran the `cleanup-large-blobs.yml`
workflow (run `29961034978`), which force-pushed a filtered history to every
branch: superseded `data/raw/` and `results/calibration/` blob versions were
stripped, `main`'s file manifest was machine-verified byte-identical before and
after, and **every pre-rewrite commit SHA changed**. The `git.sha` recorded in
bundle `run_config.json` / `meta.json` therefore no longer resolves for any
bundle solved before the rewrite — measured 2026-07-26 against main `10c239bf`:
**67 of 94 registered bundles**. No old-to-new SHA mapping was saved (owner
confirmed), so no remap is possible, and none is wanted.

**What is NOT affected.** Keeper replay and golden capture never resolve the
recorded SHA: `replay_keeper.py` excludes `git_sha` via `_IGNORE`, and
`capture_keeper_goldens.py` excludes it via `FIDELITY_IGNORE_KEYS` — both treat
it as provenance labeling, never a recipe input. (An earlier handoff claimed
these paths "compare against" the recorded SHA; that claim was checked at
source and is wrong.)

**What IS affected — intentionally.** The one consumer that resolves the SHA is
the `--reuse-solved` gate (`plan_reuse_solved` in
`scripts/run_calibration_full.py`), which proves code identity by running
`git diff <prior_sha> HEAD` over `src/`, `scripts/` and `data/`. An
unresolvable SHA means that proof cannot be produced, so the gate refuses reuse
and the year solves fresh. **The refusal is load-bearing and stays strict** —
no warning downgrade, no bypass flag, no timestamp or heuristic fallback: any
of those would let a bundle be reused across a genuine source change,
silently. The cost is wall-clock only (pre-rewrite bundles are re-solve-only)
and self-heals as new bundles land with resolvable SHAs. The refusal message
names this cause, and `tests/test_reuse_unresolvable_sha.py` pins
refuse-not-warn.

---

## 7. Rule 28 `[R-MECH-MATRIX]` — the cross-ISO mechanism testing matrix

Added 2026-07-27 (owner request: cross-ISO mechanism review). The trigger was a
six-ISO audit showing the calibration lanes had no shared ledger of what had
been tested where: mechanisms proven in one ISO (e.g. `pjm_da_virtual_bids`
moving C3c, `hydro_budget_nameplate_aware` transferring CAISO→PJM) were
invisible to sibling lanes, while adjudicated dead ends (the S1 shaped-floor
family, the ERCOT coal enumeration, zonal topology splits) risked being
re-tested from scratch. The rule's normative text — the matrix locations, the
seven-state cell vocabulary, and duties (a)–(d) — is in `CLAUDE.md`; the
working recipe, the ISO-similarity analysis, and the per-ISO lever queues are
`docs/mechanism-testing-matrix.md`. The canonical data file is
`docs/codebase-site/data/mechanism-matrix.js` (a `window.MECH_MATRIX` payload
rendered by the Mechanism Matrix explorer page); it was seeded from a
five-way audit of the `ScenarioConfig` inventory, the six keeper
`run_config.json`s, the per-ISO calibration logs, and the forecast program
board, against the 2026-07-27 keeper roster.

### 7.1 Owner rulings adjudicated *through* the matrix — the DO-NOT-REDO decisions

Rule 28's `G` state ("governance-refused/closed") is the matrix's record of a
mechanism the program has decided not to build. Where that decision is the
owner's, it is logged here so a successor session reads the *grounds* and not
only the letter — a `G` re-opened on the wrong grounds is the failure mode the
DO-NOT-REDO discipline exists to prevent.

- **2026-08-17 — MISO C3a-2025 closed as a model-class limit** (session
  miso-163; the mechanism is `ordc_scarcity_overlay`, MISO cell `G`). The MISO
  keeper `2026-08-16-miso-160-wefor-shape` stood at `NOT-YET` on **C3a-2025
  alone** (−12.5 % against the ±10 % bar). miso-161 exhausted the availability
  channel at admissible grain and escalated with two shapes on the record;
  miso-162's read-only recon then changed the question, and **both halves were
  put to the owner**:
  **(i)** the stated Shape-1 *data* blocker was **false** —
  `data/raw/MISO-AS/asm_rtmcp_zonal_{2023,2024,2025}.parquet` already carry
  hourly zonal RT ASM MCP by product, so an RCPF/ORDC binding-record intake
  needed **no data ask**; **(ii)** the mechanism that intake would feed was
  **already cell `G` on STRUCTURAL grounds** (`docs/multi-iso/miso-scarcity-tail-external-validation-2026-07.md`
  §1–§4: MISO's ORDC is a Monte-Carlo LOLP construct pricing 10–30 minute
  probabilistic risk a perfect-foresight hourly LP does not contain), and §1
  measures it **inert** — in the 88 actual 2025 RT>$200 hours the keeper clears
  $50 median / $83 p90 / $157 max, the reserve adder fires 2 of 88, deliverable
  reserve holds ≥11 GW against a ~4.4 GW requirement, load-shed 0 h. Chartering
  it would therefore have been a **rule-28 DO-NOT-REDO collision AND provably
  inert**.
  **The owner ruled to CLOSE THE LANE**, selecting the option put as *“Shape 2 —
  close the lane: close C3a-2025 as a model-class limit on the ERCOT C3a-2023
  (Q-B) precedent”*, against a stated alternative to charter the intake anyway.
  *(Provenance note, for honesty about the word “verbatim”: the ruling was given
  as a selection between two written shapes, not as free-form prose, so what is
  quoted above is the option text the owner selected — there is no owner
  sentence to quote beyond it. The question as put, including both halves and
  the recommendation, is reproduced in
  `results/calibration/FINDING-miso163-c3a-lane-closure-2026-08-17.md` §2–§3.)*
  The precedent is **ERCOT C3a-2023 (Q-B)**
  (`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`):
  *“STOP — ERCOT stands at NOT-YET on C3a-2023 as a model-class limit, and the
  program stops spending on it … this is a **budget decision, not a rubric
  decision**. The determination stays NOT-YET; C3a-2023 stands a MODEL MISS at
  full magnitude; no ledger text moves.”*
  **What the ruling does and does not do.** It stops MISO sessions being spent
  on C3a-2025; it does **not** touch the rubric, reclassify the criterion, or
  move any ledger text. C3a has not been ledgerable since v3.1 and this closure
  does not seek to make it so: the determination stays `NOT-YET`, the miss is
  reported at full magnitude as a `[MODEL MISS]`, and C3c remains the single
  ledgered caveat. **No solve, no promotion, no registration** — the keeper is
  unchanged and the matrix cell stays `G` (re-affirmed, not re-minted).
  **The re-opening test, narrowed by this ruling:** new evidence must defeat
  external-validation **§1–§4 specifically**. A data-availability argument is
  expressly **not** such evidence — (i) established that the data is present,
  which is precisely why it cannot carry a re-charter.
  **Companion precedent, landed the same day:** §4's CAISO entry (session
  caiso-201, owner ruling Q1) rested that lane at `NOT-YET` on the same posture
  — an in-model queue exhausted by measurement, a load-bearing criterion
  genuinely failing, and a rubric amendment that would have ledgered it already
  declined. Read together they establish the shape: **an exhausted lane whose
  load-bearing criterion genuinely fails rests or closes at `NOT-YET`; it does
  not ledger, does not lower a band, and does not declare.** The two differ only
  in what re-opens them — CAISO's on new funded data, MISO's on evidence
  defeating a specific structural finding — not in the posture taken. Surfaces:
  `docs/mechanism-testing-matrix.md` §5.4 queue header,
  `docs/calibration-log/miso.md` (miso-163),
  `docs/codebase-site/data/mechanism-matrix/MISO.js`.
  **LANE CLOSURE LIFTED BY THE OWNER, 2026-08-18** *(annotated 2026-08-23, session
  miso-178 — this entry previously read as if the closure stood)*: the owner re-opened
  the lane in writing — *"2025 miso needs to be calibrated in summer scarcity it's
  unacceptable that it doesn't"* — which, the closure being an owner ruling, only the
  owner could do (unblock condition (C) of the miso-166 gate; recorded at
  `docs/mechanism-testing-matrix.md` §5.4 header and
  `docs/calibration-log/miso.md` miso-167). **Scope of the lift: the C3a-2025 LANE
  re-opens; the `ordc_scarcity_overlay` cell stays `G`** on the untouched
  external-validation §1–§4 structural grounds, and the narrowed re-opening test above
  is unchanged — re-confirmed by measurement at miso-178
  (`FINDING-miso178-c3a2025-anatomy-and-lever-plan-2026-08-23.md` §3: the 58 RT-only
  tail hours remain out of deterministic reach, and the annual band does not need
  them).

## 8. Changes to this file

| date | change |
|---|---|
| 2026-08-17 | §4: recorded rubric **v3.3** — the owner's amendment that a ledgered C3c caveat is REPORTED but no longer DOWNGRADES the determination, withdrawing the "never `CALIBRATED`" half of CLAUDE.md rule 22 guard (d). 6 registered runs re-score `CALIBRATED-WITH-CAVEATS → CALIBRATED`, 2 of them keepers (NYISO, NEISO); holdout tiers untouched. |
| 2026-08-17 | §4: recorded the first lane RESTED at `NOT-YET` (CAISO, session caiso-201, owner ruling Q1). No rule text changed — the entry exists so the precedent that an exhausted lane with a genuinely failing load-bearing criterion *rests* rather than ledgers or declares is citable. |
| 2026-08-23 | §7.1 MISO entry annotated with the owner's 2026-08-18 LANE-CLOSURE LIFT (session miso-178): the entry previously read as if the miso-163 closure stood. Lift scope recorded — the C3a-2025 lane re-opens, the `ordc_scarcity_overlay` cell stays `G`, the narrowed re-opening test is unchanged. Decision-record annotation only; no norm touched. |
| 2026-08-17 | Added §7.1: owner rulings adjudicated through the matrix, seeded with the 2026-08-17 MISO C3a-2025 model-class closure (session miso-163, mechanism `ordc_scarcity_overlay` cell `G`). Records the ruling, its two-half basis, the ERCOT (Q-B) precedent, and the narrowed re-opening test. No norm added, reworded or dropped — rule 28's text is unchanged and this is a decision record, not a rule. |
| 2026-07-27 | Added §7: rule 28 `[R-MECH-MATRIX]` (cross-ISO mechanism testing matrix) — origin and canonical file locations. "Changes to this file" renumbered §7 → §8 (no external references cited §7). |
| 2026-07-26 | Added §6: the 2026-07-22 history rewrite orphaning pre-rewrite bundle `git.sha` provenance (owner decision B close-out) — no SHA mapping saved, replay/goldens unaffected (`git_sha` in both ignore sets), the `--reuse-solved` unresolvable-SHA refusal intentional and load-bearing. "Changes to this file" renumbered §6 → §7 (no external references cited §6). |
| 2026-07-25 | §5: recorded the ≥300-line push deadlock (rule 27 + API-only leaving no compliant path) and the owner's per-commit `git push` waiver that landed wave 4C. Per-commit, not a standing exception. |
| 2026-07-25 | Created (refactor-consolidation Wave 5B, owner decision D-6). Takes the rule-27 incident writeup and the audit N↔N+1 mapping paragraph out of `CLAUDE.md`, and indexes the rule-20 / rule-22 amendment narratives at their canonical homes. No norm was moved, reworded, or dropped. |
