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

- **Rubric v3.1 — owner amendment 2026-08-06, C7 retired outright.** The
  directive's C7 half (verbatim, session-logged): *"… we should drop [C7] from
  the calibration report and declaration altogether if no other commercial
  grade model is gating or publishing on that."* The check came back empty —
  no commercial-grade comparable gates or publishes diurnal-shape accuracy
  (the rubric §8 comparables row scores C6/C7/C8 "beyond commercial practice",
  i.e. with no external anchor at all) — so the standalone C7 diurnal-shape
  gate that shared rule 20's materiality floor was **RETIRED**: dropped from
  the report AND the determination, with `score_shape` and `C7_GATED_CLASSES`
  deleted per rule 26 `[R-DELETE]` (a harder removal than the C5a/C5b/C5c
  demotions, which stayed computed and `REPORTED_ONLY`). The D-1 measurement
  itself is untouched: it stays in `legitimacy_diagnostics.json`, and rule
  20's grounded-above-budget escalation still gates on it through C8's shape
  leg — now its sole gating path (CLAUDE.md rule 20 records this in place).
  The same amendment's ledgering half (`LEDGERABLE_CRITERIA` → `{price_tail}`,
  budgets 1→0 protective / 3→1 ledgered) is rule-22-adjacent and its effects
  (the CAISO reversion) are itemized at the canonical narrative:
  `docs/calibration-determination-rubric.md` §9 (v3.1).

- **Rubric v3.5 — owner decision 2026-08-25, diurnal price amplitude added
  REPORTED-ONLY and BAND-FREE. No CLAUDE.md rule text changed** — indexed here
  because it is v3.1's disposition (gate not built, measurement kept) applied
  to *prices*, answering the owner call filed by neiso-74 and re-filed by
  xiso-1 on 2026-08-01. The owner selected **option (B)** of
  `docs/DECISION-CARD-xiso-diurnal-amplitude-rubric-2026-08.md` — *"(B) ADD IT
  AS REPORTED-ONLY — measured, published, no status, no budget"* — in the
  card's recommended band-free form. *(Per §7.1's provenance convention on the
  word "verbatim": the ruling was a selection among the card's written
  options, so what is quoted is the option text the owner signed, not
  free-form owner prose.)* The scorer gains **D-A**
  (`calibration_verdict.score_diurnal_amplitude`): the hour-of-day amplitude
  ratio, phase check and hod correlation are published on every run with **no
  band, no threshold and no verdict** — the stream is NOT in `CRITERIA`, so it
  can contribute no status, consume no caveat budget, add no reason line, and
  cannot perturb the C3c standing rule's lone-failure test (measured over
  `CRITERIA` membership since v3.2); `LEDGERABLE_CRITERIA` (`{price_tail}`)
  and `MAX_LEDGERED_CAVEATS` (1) are unchanged. **Band-free** because the
  xiso-6 sweep measured a gating criterion as vacuous below a 25 % amplitude
  floor and universal above 45 %, with no external comparable anywhere in the
  20–45 % window to anchor a band — the exact ground C7 was retired on.
  Verified determination-neutral over all 55 registered runs at amendment
  (zero determination / per-criterion / caveat diffs; pinned by
  `DiurnalAmplitudeReportedOnlyTests.test_IT_CANNOT_GATE`), and **re-verified
  2026-08-30 over the then-current six-keeper roster** (ERCOT `CALIBRATED`,
  PJM `CALIBRATED`, CAISO `NOT-YET`, NYISO `NOT-YET`, NEISO `CALIBRATED`,
  MISO `NOT-YET` — every pair identical with the measurement ablated). Two
  things the ruling deliberately does NOT do, recorded on the card stamp:
  NEISO's storage-side PS DO-NOT-REDO is not lifted (a rubric disclosure
  changes no dispatch), and the defect itself is not closed (a disclosure
  obliges no repair). Canonical narrative:
  `docs/calibration-determination-rubric.md` §9 (v3.5); cross-ISO log entry:
  `docs/calibration-log/governance.md` (2026-08-25).

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
- **2026-08-26 — the spend freeze becomes TIER-SCOPED; validation tier lifted, locked test
  stays frozen** (owner ruling, program-director sitting card 6 — the O4/O5 decision card
  `docs/audit/AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4, option (A) taken as recommended;
  verbatim: *"Close the layup charter with cause; lift the freeze for the VALIDATION tier
  (2020-2022) for ISOs holding a `complete` marker. `final` stays empty and the locked test
  stays frozen. Restores the diagnostic touchpoint loop."*). The freeze, previously a boolean
  that suspended every tier at once, gains a `scope.tiers` read by the single fail-closed
  reader `holdout_policy.frozen_tiers` (an active freeze with no parseable scope covers
  every tier — the prior shape and behaviour). Steady state after the ruling: `active: true`,
  `scope.tiers = ["locked_test"]` — 2020–2022 are governed by the `complete` marker +
  `--holdout-authorized` alone, and 2019/H1-2026 (and every fail-closed year such as 2018)
  stay frozen for every ISO, `final` marker or not. The CAMPD economic-layup charter is
  CLOSED WITH CAUSE in the same ruling (`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md`
  §10), the cause stated honestly: the detector/seam question REMAINS OPEN (post-guard CC
  envelope 14.2–36.7 %, 17/18 ISO-years above the ~10–15 % norm) and is carried explicitly
  as a documented definitional seam every keeper's availability envelope inherits — the lift
  is a decision to proceed WITH a known-open input question on the iterable tier, not a
  finding that it closed. Verified behaviourally on all three enforcement gates (55/55
  invocations, including the locked-test refusal for all six ISOs with and without the
  flag). Execution record: `docs/FINDING-holdout-governance-2026-08-26.md`.
- **2026-08-26 — locked-test scheduling gates on the validation ladder** (owner ruling,
  same sitting, card 7 — a STANDING POLICY amendment to the rule's locked-test clause,
  not a schedule and not a grant; verbatim: *"Locked test is scheduled only after an ISO
  has run its 2020-2022 touchpoints and the loop has stopped surfacing repairs. Spends the
  one-shot against the most-prepared config, which is the whole design intent."*). The
  standing precondition for any future `final` grant is therefore: an ISO becomes eligible
  to be **considered** for `final` only after (i) its 2020–2022 validation touchpoints have
  been run and (ii) the touchpoint loop has stopped surfacing repairs. **Eligibility is not
  a grant** — `final` remains an explicit owner act, per ISO, every time, and adding an ISO
  to `final` still spends the single most irreversible resource in the policy. Two
  constraints already on record are restated so this cannot be read as a green light:
  **NEISO's 2019 basis is UNREPAIRABLE** (ISO-NE migrated its newswire mid-2018 and the
  Mar–Jun recaps were never carried over — `FINDING-neiso86-gas-basis-intake-2026-08-06.md`
  §5.1) and its `final` readiness reads **NOT YET on the merits** (2019 unsolvable at HEAD;
  cannot discriminate on C3c); and **NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — `final`
  carries only its `_note`, and the 2026-08-26 ruling changes no marker. Recorded in
  CLAUDE.md rule 22's locked-test bullet, audit row O6, and
  `docs/FINDING-holdout-governance-2026-08-26.md`.
- **2026-09-06 — R-AZ: the tier marker is re-checked AT REGISTRATION** (owner ruling,
  audit-program director sitting ~00:15Z, card "Marker gate"; verbatim option taken:
  *"Re-check at registration"*). The enforcement leg carried over unchanged since
  2026-07-06 reads the marker exactly **once, at solve LAUNCH**
  (`run_calibration_full.enforce_holdout_year_gate`), so a multi-hour LP can outlive the
  authorization it started under. **The case is Z-6**
  (`docs/handoffs/holdout-2022-completeness-ercot-nyiso-2026-09-05.md` §1a): a NYISO 2022
  validation-tier solve launched legally under the D56-R `complete` marker, `main`
  withdrew that marker (nyiso-193) while the LP ran, and the run went un-registered at
  merge only because the lane applied its own discipline — nothing in the tooling would
  have stopped the sidecar. R-AZ closes that by re-asking the SAME question at the seam
  where solve years become a committed artifact: `scripts/dashboard_add_run.py`
  (`enforce_registration_marker_gate`), delegating to the new
  `holdout_policy.registration_refusals` so the tier map, the fail-closed freeze
  precedence and the marker lookup stay defined exactly once (rule 19 `[R-ONE-MECH]` in
  spirit) and the two gates can never disagree about which year needs which block.
  **Scope of the change, stated narrowly:** the launch gate's semantics are untouched;
  D-6 and `audit_keepers` are untouched; no marker, freeze, keeper shard or registered
  run is touched. **No bypass flag exists** — unlike the launch gate there is no
  `--holdout-authorized` counterpart, because a registration that fails the check is not
  a registration; the remedy is an explicit owner act restoring the marker, or the run
  stays unregistered with git history as the record (rule 15). The gate runs before the
  sidecar, the `runs/<id>.js` payload and the bench parts are written, so a refused run
  leaves nothing behind. **Measured effect on the existing record: none.** All five
  holdout-year sidecars at HEAD (`2026-09-05-neiso-2020-2021-touchpoints`,
  `-neiso-2022-touchpoint-k99`, `-pjm-2022-2021-touchpoints`,
  `-run249-2022-touchpoint-forward`, `-run250-2022-touchpoint-carveout`) are
  validation-tier runs of `complete` ISOs (NEISO / PJM / ERCOT) and replay clean through
  the new check, pinned as a test; `audit_keepers --check` and
  `check_registry_payload_parity.py` both stay at 0 failures. One asymmetry is recorded
  rather than repaired: the registration gate consults the **freeze** as well as the
  marker (fail-closed), while `legitimacy_diagnostics.run_d6_quarantine` reads the marker
  alone. It is inert today — the freeze covers the locked test, and no locked-test year
  has ever been registered — so closing it was left out of scope. Execution record:
  `docs/handoffs/FINDING-y16-register-marker-recheck-2026-09-06.md`.

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

## 8. Rule 29 `[R-SCREEN]` — screen a new config on one year before spending the full span

**Origin.** Owner rule, **2026-09-05**, given verbatim as: *"only run in calibrated years thru
new configs first then if those show calibration under new configs launch the other years instead
of wasting runs on 3 full years before we've addressed whether config actually solves the issue"*.

**The cost it addresses.** A 3-year replay on the larger ISOs is ~35–70 min of LP **per arm**, and
a properly controlled A/B spends two of them (G-CTRL form 4 is void whenever the solve path has
moved since the keeper's `git_sha`, which by 2026-09 is the normal case). Before this rule the
lane routinely spent six year-solves to learn that a mechanism did not do what its own offer
arithmetic said it would.

**The guardrail that makes it admissible.** The obvious version of this rule — "solve one year,
look at the residual, continue if it improved" — is **fitted-mechanism selection done one year at
a time**, which rule 1 `[R-STRUCT]` forbids outright, and it would additionally make the choice of
screen year a residual-driven one. The rule as written therefore fixes two things in the
PRECOMMIT, before the screen runs:

1. **the screen year** — the year the mechanism's own *measured footprint* is largest, taken from
   the zero-LP phase 0, never the year with the largest residual;
2. **the screen gate** — structural only (direction and order of magnitude of the dispatch
   response against the pre-solve delta; footprint confined to the claimed rows; the asserted
   identity; no non-target load-bearing criterion flipping PASS → FAIL). The target residual is
   **excluded from the screen gate** exactly as it is excluded from a favourable-direction arm's
   promotion basis.

**It is a STOP gate only.** A screen may kill an arm; it may never promote one, never contributes
to a determination, and its bundle is a throwaway probe.

**Interaction with rule 16 `[R-ALLYEARS]`, which is UNCHANGED.** Rule 16 already permits a
one-year solve "*only* as a throwaway diagnostic probe to isolate a single-year effect"; this rule
makes that the standard *first* step for a new config and leaves the keeper requirement exactly as
it was — the keeper bundle is still every scorable year in ONE invocation and ONE bundle, and the
screen year is re-solved inside it. The screen therefore costs one extra year-solve when it passes
and saves N−1 per arm when it fails.

**First application.** caiso-251 (the gas-offer fuel-coupling form). Its zero-LP phase 0 already
carried the step-0 gate (G-COUPLE, which would have stopped the session with no solve at all had
it failed); the rule was issued mid-session and applied to the arm from that point, with 2024
named as the screen year on the phase-0 footprint (the largest |fuel − anchor|, hence the largest
offer delta: CC econ −2.08, CT econ −8.31, CT_CHP −10.44 $/MWh) and the screen gate registered in
`PRECOMMIT-caiso251-fuel-coupling-form-2026-09-05.md` Addendum A before the screen solve started.


### 8.1 Clause (b) — no control solves; `G-DRIFT` replaces them (owner, 2026-09-05)

**Origin.** Owner rule, same day, verbatim: *"stop doing control solves wtf they're a waste of time
just use the last keeper as the control"*.

**What was actually happening.** G-CTRL form 4 — differencing an arm against the incumbent
keeper's committed numbers — was being declared VOID by a heuristic: *files under the solve path
changed since the keeper's `git_sha`, therefore the keeper's numbers are not a valid control,
therefore spend a control solve.* On a 3-year ISO that heuristic costs **35–70 min of LP per arm**
and it was firing as the normal case, because `src/market_sim` receives commits from six ISO lanes
and the forecast program continuously.

**Why the heuristic was wrong.** "Did the solve path move for THIS ISO in THIS mode" is a question
about code, and it is answerable by reading the diff. A control solve answers a strictly weaker
version of it — it shows that two numbers differ, not which line did it — and it answers it for
several thousand times the cost.

**The replacement, `G-DRIFT`.** Diff the keeper's `git_sha` against HEAD over the backcast path and
classify every changed hunk as INERT for this ISO with its reason cited, or LIVE. All INERT ⇒ form
4 is valid. A LIVE hunk is the only thing that earns a control solve, and then only for the screen
year. The audit is recorded before the arm is solved.

**First application, and it vindicated the ruling on the merits.** caiso-251 audited
`900402b → HEAD` (22 files, +2,527/−149) and found **every** hunk CAISO-backcast-inert:
capacity-market / capacity-evolution paths a `mode="backcast"` run never enters
(`capacity_market.py`, `capacity_evolution/*`, `iso_configs.py`'s `retirement_sector_gate`,
`runner.py`'s locality block behind the default-off `locality_capacity_curves`, `storage.py`'s
`locality_prices_by_zone` default `None`); MISO-only branches (`data/fuel/resolve.py`,
`basis/miso.py`, `basis/meanzero.py`'s `skip_cells`, all behind `config.iso == "MISO"` and the
default-off `miso_zonal_gas_basis_skip_923_priced`); a NYISO-only mechanism whose per-ISO artifact
CAISO does not have (`egrid_steam_collapse_heat_rates`, default off and absent from the recipe —
`egrid_steam_collapse_heat_rates_for` returns `{}` for CAISO by construction); an adaptive-pass
skip guard reachable only under `*_storage_adaptive_expectation`, both **False** on the CAISO
keeper (`run_calibration._p1_storage_cost_identical`); a return-type-only change
(`plant_prices.apply_plant_monthly_fuel_prices`, `None` → mask, "every other caller may ignore the
return"); and pure timing/diagnostics accounting (`pipeline/solve.py`, `pipeline/timing.py`,
`run_calibration._aggregate_pass_timing` — "Diagnostics only: nothing here is read by a solve").
The control solve that had been launched under the old heuristic was **killed mid-flight and its
partial bundle deleted**; the keeper is the control.


### 8.2 Clause (c) — delete before merge (owner ruling R-AV, 2026-09-05)

**Origin.** Owner ruling **R-AV**, audit-program director sitting 2026-09-05 (~23:00Z), on the
rule-29 / Class-E collision the v31 second coda routed to the owner. Verbatim: *"Delete before
merge"*. Executed by audit lane **Y-13** (`docs/handoffs/FINDING-y13-ci-plumbing-2026-09-05.md`).

**The collision it resolves** (recorded on the director board by `da99f34b`, the v31 second coda,
under "THE TWO STRUCTURAL REDS ARE UNREPAIRED … (1) Rule-22 quarantine gates — a GOVERNANCE
COLLISION, not a lane error"). Rule 29 calls a screen bundle a *"throwaway diagnostic probe — never
registered on the dashboard"*; the Class-E retention rule's point 4 (adopted 2026-08-16, enforced by
`check_registry_payload_parity.check_bundle_retention`) requires every `results/calibration/<bundle>`
dir to map to a retained sidecar or be keep-required. miso-220 committed its 2025 screen bundle
(`7ccdc4fd`, 22:22Z) exactly as rule 29 directed and, by doing so, turned the always-on parity gate
red for every PR on `main` — *"a lane that obeys rule 29 exactly turns the parity gate red BY
OBEYING IT"*. The gate's message offered three exits — register, prune, or allowlist — and rule 29
forbade the first while nothing yet said which of the other two applied.

**The ruling picks the second exit and makes it a duty.** A screen bundle, and any control bundle a
screen earns under clause (b)'s LIVE-hunk case, is `git rm`-ed from `results/calibration/` **before
the PR merges**; the PRECOMMIT/FINDING doc carries every number the session will ever cite (the
gate table with its values, the control differencing, the verdict); `check_registry_payload_parity`
is the enforcement, and an unregistered bundle dir is a **gate red, not an allowlist candidate**.
This keeps `KEEP_REQUIRED_UNMAPPED_BUNDLES` at the empty set the 2026-09-05 keeper-only prune left it
(§9) rather than re-opening it one probe at a time, and it is the same delete-not-archive discipline
rule 15 states for pruned runs and the Architecture tree states for superseded per-run scripts.

**First execution (Y-13, same day).** Two dirs pruned under the ruling, each after confirming its
numbers survive in a committed record: `miso220_nonsteamlift_screen2025` (8 tracked files — the
G-1/G-2/G-3 gate values live in the committed `results/calibration/_miso220_screen_gates.json` and
the gate definitions in `PREREG-miso220-nonsteam-offer-lift-2026-09-05.md` Addendum A; the
PREREG's own text already declared the bundle a throwaway) and `neiso_headctrl_k99` (17 tracked
files — the NEISO same-HEAD control whose worst-drift table is
`results/calibration/ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §4(i)). Parity
read 2 problems before and OK after; no sidecar, payload, keeper shard or bench part changed.


## 9. Rule 15 `[R-DASHBOARD]` — retention: top-15-per-ISO → KEEPER-ONLY (owner, 2026-09-05)

**Origin.** Owner instruction, **2026-09-05**, given in the session that executed it
(ercot-248, `docs/calibration-log/ercot.md` "## ercot-248 — 2026-09-05"), verbatim:

> *"Combine the ERCOT calibrated keeper config into one run for the run explorer html page so it
> should combine the 2023 config that is calibrated plus the 2024/2025 config into one run then
> remove all the others that aren't that keeper so it's just showing one run. Also prune all the
> other non keeper runs from there so just show the keeper for each ISO for now."*

**What it replaced.** The former retention was an **age cap**: the dashboard kept the newest 15
runs per ISO, pruning the displaced oldest at each registration (set 2026-06-21, itself superseding
a 10-run rule; PJM ran a `pjm N <keyword>` labelling convention on top of it). The cap was a
*volume* limit — it said nothing about which runs still carried meaning, so a lane's probe and
control runs survived on the site purely by being recent.

**What changed.** `CLAUDE.md` rule 15's retention sentence, and nothing else in that rule. Each
ISO's dashboard and `results/calibration/` now carry **only that ISO's designated keeper run(s)** —
a partitioned keeper's several configs included, whether composed into one registered run or kept
as the per-config runs the ISO's keeper shard names — plus any bundle still referenced by a
`results/regression-goldens/*/manifest.json` capture record or by the parity allowlist
(`check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES`). Every other run is pruned at the
next registration, through `scripts/prune_iso_runs.py`, whose citation guard (the
`calibration-complete.json` + `keepers/<ISO>.json` refusal, `--force-uncite` to override) is what
keeps a keeper-only site from leaving a governance file asserting a determination against a run
that no longer exists.

**Execution.** ercot-248 pruned 61 non-keeper runs and took every ISO's dashboard down to its
keeper. The cleanup lane (#4808, #4816) removed the matching disk residue: 18 unmapped bundles, 36
hindcast sidecars, 109 hindcast directories, and `scripts/archive/`. The deletions are consistent
with the delete-not-archive discipline `CLAUDE.md`'s Architecture tree already stated for
superseded per-run scripts — **git history is the record**.

**What did NOT change.**

- **The registration duty is untouched.** Rule 15's opening clause still binds: every completed
  run, keeper *or* rejected probe, registers on the dashboard in the session that produced it.
  Retention governs what *survives*, never whether a run is registered — a probe registers when it
  finishes and is pruned once superseded. A lane that skips registration because "it will only be
  pruned" has broken rule 15, not honoured it.
- **The rule's ordinal and ID.** It remains rule 15 `[R-DASHBOARD]`; ordinals are never renumbered
  (§1).
- **The forecast-namespace half** of rule 15, the KEEPER `hourly/` sidecar requirement, and the
  Pages-deploy generation contract.
- **No keeper, marker, matrix shard or determination** was touched by the amendment.

**Implementation lag, recorded 2026-09-05.** The keeper-only rule is the norm; the automatic
retention sweep still implements the old one. `scripts/dashboard_add_run.py` ships
`KEEP_PER_ISO = 15` and `prune_iso(..., keep=15)`, an age cap run after each registration, so the
enforced-by-code behaviour is *weaker* than the rule (it retains non-keepers up to the cap; it
never retains less than the rule requires). `scripts/prune_iso_runs.py` — the owner-directed
keeper + keep-list clear-out — is the tool that actually implements the amended rule, and is the
one rule 15 now names. Closing the gap is a calibration-desk change to `dashboard_add_run.py`, not
a governance one; the G-1 amendment lane corrected the *prose* of both scripts only.

## 10. The bench builder fingerprint — byte hash → AST hash (owner ruling R-AS, 2026-09-05)

**What the instrument is.** `scripts/lib/bench_stamp.builder_fingerprint()` stamps every
per-(ISO, year) benchmark part under `frontend/data/backcast/bench/` with a 12-hex hash of the
SOURCE of the four scripts that compute and write it (`BUILDER_SOURCES`). A part whose stamp
differs from the current one provably was not written by the builder at HEAD, so a C1 verdict
scored against it is not reproducible from the code that would produce it now.
`scripts/check_bench_freshness.py` gates on that (HARD tier) and separately REPORTS intervening
engine commits (SOFT tier, never gates). It exists because of nyiso-148 (2026-08-21): NYISO's
part went un-refreshed from 2026-08-17, regenerating it moved CC_REGULAR-2024's metered actual
by ~4 TWh, and every registered NYISO run flipped to `NOT-YET`, the keeper included. **Nothing
below weakens that guarantee** — the defect it closes was real and expensive.

**Origin.** Owner ruling **R-AS** (card M, verbatim *"Adopt Proposal A"*), **2026-09-05**,
on `docs/handoffs/FINDING-y10-bench-stamp-instrument-2026-09-05.md` — the Y-10 audit lane's
finding that the instrument's TRIGGER, not its guarantee, is mis-tuned. Executed by audit lane
Y-12. R-AS is first recorded here; no prior artifact cites it.

**The defect in the trigger.** The stamp hashed the RAW BYTES of four whole files, so **any**
edit to any byte moved it and marked all 20 committed parts STALE. Measured over the four
sources at `49647dd6`, **53.0 % of the hashed surface (84,163 of 158,714 bytes) is comments and
docstrings**, which cannot change a bench payload under any circumstances. All three fingerprint
moves of 2026-09-05 were adjudicated payload-inert and each cost a dedicated lane; the third
(`677b605a`) was a **single reworded comment line** that cost 20 artifacts a re-stamp. The
instrument had produced **zero true positives and three false alarms** — which is the failure
mode `check_bench_freshness.py`'s own docstring warns about for the SOFT tier (*"gating on them
would mark every part stale within a week and train everyone to ignore the signal"*), arriving
at the HARD tier.

**What changed.** One function body. `builder_fingerprint()` now hashes, per source in
`BUILDER_SOURCES` order, the path, then the LENGTH of `ast.dump(ast.parse(source))`, then that
dumped AST — in place of the raw bytes and their length. `ast.dump` at its defaults omits
line/column attributes, so comments, blank lines and reformatting are inert while every semantic
edit still fires. A source that will not parse falls back to its raw bytes, which is the
FAIL-SAFE direction: an unparseable builder can only OVER-fire, never under-fire.

**Why it cannot weaken the guarantee.** Two sources with identical ASTs compile to identical
behaviour, so a part written under either is byte-identical by construction. The stamp narrows to
exactly what it was ever able to promise.

**The counterfactual, computed rather than argued** (finding §3, re-measured under the shipped
construction at Python 3.11; pinned as relations by `tests/scoring/test_bench_stamp_ast.py`):

| revision | what it was | byte hash (old) | AST hash (shipped) |
|---|---|---|---|
| `dee6472c^` | — | `dbea7bf45111` | `3fabde12b672` |
| `dee6472c` | nyiso-192 CHP add-back — a real code change | `4e78c85427bb` | `96e5860ce4ec` — **MOVED, correctly** |
| `677b605a^` | — | `4e78c85427bb` | `96e5860ce4ec` |
| `677b605a` | delete-not-archive — **one comment reword** | `b2f21b9a00d3` | `96e5860ce4ec` — **UNCHANGED** |

**STATED LIMIT, not buried.** Docstrings ARE `Expr(Constant(...))` nodes in the parsed tree, so
`ast.dump` carries them and a docstring edit still moves the stamp. Only comments and whitespace
go inert. Excluding docstrings would need a tree transform — wider than the Proposal A that R-AS
adopted, and it would not reproduce the counterfactual digests above, which are the verifiable
record of what was adopted. Pinned by a test so it is a known property, not a surprise. The
finding's **Proposal B** (narrowing `BUILDER_SOURCES` to the bench-feeding paths, and dropping
`bench_stamp.py`'s self-inclusion) is **NOT adopted here** and remains open.

**The one-time re-stamp.** Changing the construction moves the fingerprint by definition, so all
20 parts read STALE the moment it lands (measured on this branch: 20 STALE, exit 1, before the
re-stamp). They were re-stamped `b2f21b9a00d3` → `4254168edcfe` **in the same PR** by the Y-8
method (`a725bfc3`) — each part loaded and rewritten through `backcast_artifacts.write_bench_part`
with its own `meta`/`bench` — so the gate is green on the head and never red on `main`. Verified
per part, 20 of 20: **payload sha256 unchanged**, `meta` identical with the stamp removed, meta
key ORDER identical. The only differing byte content is the 12-hex stamp; the ±1-byte gzip
deltas are gzip's re-encoding of those characters.

**What did NOT change.** The 12-hex digest length; the path-prefix construction; the missing-file
behaviour (an absent source still moves the fingerprint); the `BUILDER_SOURCES` membership; the
HARD/SOFT tier split and `check_bench_freshness.py` entire; `write_bench_part`'s byte-determinism
(the property that keeps concurrent registrations conflict-free). **No keeper, marker, matrix
shard, registry sidecar, bench payload or determination was touched**, and no solve was run — the
re-stamp is a relabelling, which is what the identity checks above are for.

## 11. Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` — the authorized price-tuning channel (owner ruling, 2026-09-05)

**What changed.** The registered `offer_curve_by_group` band multipliers are now an
**authorized price-tuning channel**: tuning them on price is no longer the forbidden
"fitted adder" of rule 1, and rule 13's forbidden-list gains exactly one exception.

**Why.** Rule 1's second half read *"never reach the right number through a mechanism that
isn't real (a fitted adder, a load proxy, a haircut tuned to the residual)"*, and rule 13
forbade *"adding an offset/haircut/adder tuned to the price or volume residual"*. Under
that text, session miso-218's uniform ×1.10 offer lift was rejected on two independent
grounds — (a) rule 1, a level scalar identified against a price residual is not a keeper
mechanism, and (b) it broke a load-bearing C1 cell. The owner ruled the (a) ground wrong
as a matter of design intent:

> *"We should definitely be able to fit the fossil offer curves to the price… as long as
> it's the same config across the 3 years it is fine to do. And we can keep steam gas as
> is and do 1.1x for all the rest of fossil. **The offer curve multipliers are meant to
> allow us to tune on price & adjust merit order.**"* — owner, 2026-09-05

and, on being shown that the arm's attestation could not honestly carry the keeper's
`no_fit_to_price_residuals` / `levers_trace_to_measured_input` assertions, directed that
the rule be rewritten to allow it rather than leaving rule text and practice in conflict.

**The carve-out is narrow, and every condition binds** (CLAUDE.md rule 1, (a)–(e)):
(a) the channel is the `offer_curve_by_group` band multipliers ONLY — never `phys_*`,
never `econ_low_share`/`pct_peaking`, and never a new adder, offset, haircut or proxy;
(b) **ONE config across EVERY scored year** — a per-year value is still per-year fitting;
(c) the value is set **ex ante, declared in the PREREG before the solve, and never swept
against the gates** — selecting a factor by which a criterion passes remains exactly the
fitted-mechanism selection rule 1 exists to forbid; (d) cross-class merit-order adjustment
is an INTENDED effect; (e) the run declares the channel in
`governance.authorized_price_tuning` and carries the value as a DOF-ledger free parameter
identified by the ruling.

**Rule 1's first half is UNTOUCHED.** Structure still comes first; a structurally-correct
mechanism is still never judged by the residual; a level-tuned run missing real structure
is still not a keeper. `no_pinning_to_actuals` is **never** scoped by this carve-out, and
neither is the forbidden-flag machine check.

**Enforced, not merely asserted.** `calibration_verdict.score_governance` reads
`no_fit_to_price_residuals` and `levers_trace_to_measured_input` as *scoped* — "no residual
fit outside a declared authorized channel" — only when a well-formed
`governance.authorized_price_tuning` block is present, validated by
`_authorized_tuning_finding` against conditions (a)–(c) and the scored-year set for (b).
`audit_keepers.attestation_shape_finding` mirrors it. **It fails closed at every edge**,
pinned by `tests/scoring/test_calibration_verdict.py::AuthorizedPriceTuningTests`: an
undeclared price fit still FAILs; a declaration naming another channel, omitting
`set_ex_ante` or `not_swept`, incomplete, or not covering every scored year FAILs; the
carve-out does not reach `no_pinning_to_actuals`; the forbidden-flag check is untouched;
and a clean keeper with no declaration is unaffected (verified against the live MISO
keeper — governance PASS, determination unchanged).

**Effect at amendment.** No existing keeper's determination moves: the scoping applies only
to runs carrying the new declaration, and no committed attestation has one. The first run
to use it is the miso-220 non-steam fossil lift.

**Cross-reference.** Condition (e)'s DOF-ledger half is restated from rule 21 `[R-DOF]`'s own
side by owner ruling R-AY (2026-09-06) — §13 below.

## 12. Rule 30 `[R-TOUCHPOINT-FOLD]` — a touchpoint publishes AS the keeper (owner, 2026-09-05)

> **Clause (a) was AMENDED the next day — see §14, and again the same day — see §15.** The fold and the stamp stand exactly as
> written here; what §14 removes is the *Validation Touchpoints panel* this section mandates as
> the fold's rendering, replaced by rendering a folded year as an ordinary year column. Read
> every mention of that panel below as superseded; clauses (b) and (c) are untouched.

**Origin.** Session `neiso-pjm-validation-touchpoints` re-walked NEISO's and PJM's rule-22
validation ladders on their current keepers and registered each touchpoint as its own dashboard
run. The owner rejected the shape, verbatim:

> *"the runs should all be combined with the keeper in html not separate runs… like it's the same
> config I don't need to click into multiple things to see the results wtf. Refresh and fix this
> for ERCOT too and make it a rule when touch points are run and also add them to the calibration
> status assessment. An iso can stay calibrated even if it degrades on holdout years."*

**Why the complaint is structural, not cosmetic.** A rule-22 touchpoint is by construction the
designated keeper's own frozen recipe replayed on a held-out year — the sanctioned `replay_keeper`
channel reproduces the keeper's `meta.json` kwargs and `gen_touchpoint_attestation.py` machine-
checks that zero shared keys differ. One configuration. Listing it as a separate run therefore
advertises a second configuration that does not exist, and costs the reader a click per year to
reassemble something that was never apart.

**The three duties (rule 30 a/b/c).** (a) stamp `holdout.keeper` so the Run Explorer folds the run
into its keeper — hidden from the run list, years offered in the keeper's selector, all folded
years rendered as columns of ONE combined *Validation Touchpoints* panel; deep links redirect
rather than break. (b) rebuild and commit the ISO's status part, whose **holdout ladder** is
DERIVED from the registry (never hand-authored, so it cannot go stale) and scored **per year**,
because a multi-year bundle's single determination hides a rung that passed alone — NEISO
2020+2021 is NOT-YET as a bundle and CALIBRATED on 2021. (c) a held-out year is REPORTED and never
downgrades the ISO, whose determination is the train-tier verdict alone.

**Why (c) is not a weakening.** Rule 22 already forbids quoting a validation-tier score as a
certified out-of-sample number; a result that cannot certify equally cannot decertify. The
degradation is not hidden — it is on the keeper's panel, on the status card and in the session's
assessment — it simply stops being read as a contradiction of a headline it was never scoped to
govern.

**Companion scorer amendment — rubric v3.6**, owner, same sitting, verbatim: *"c3c should be an
accepted caveat on all holdout years."* On an out-of-training year the C3c standing rule's
lone-failure condition is dropped. The guard exists to stop C3c masking a second defect *on the
years the model is certified on*; a held-out year is not a certification, and the scarcity tail is
the one criterion this model class is known not to form (already accepted in-sample). Untouched:
the band, tier and reported magnitude; the governance guard; supporting-tier fail-closed; never a
PASS; both caveat budgets (caveats aggregate per criterion, so C3c on several holdout years is
still one ledgered caveat). In-training years keep the lone-failure guard, measured over what is
still failing after the holdout reclassification. **Measured over all 13 registered runs against a
pre-change snapshot: ZERO determinations change**; PJM 2021's C3c moves FAIL → CAVEAT, dropping
that rung from four failing criteria to three.

**Scope note.** Rebuilding every ISO's status part is a deliberate cross-ISO edit, not a lane
violation: `RUBRIC_VERSION` is embedded in each part and `audit_keepers` check S1 requires them in
sync, so a rubric amendment necessarily touches all six — the same reasoning the v3.3 amendment
recorded ("the scorer is ONE instrument and an ISO-scoped verdict rule would be an off-registry
tuning channel in spirit, rules 24 / 25"). No keeper moved and no marker was re-keyed.

**Record:** `results/calibration/ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §6.

## 13. Rule 21 `[R-DOF]` — the price-tuned band multiplier is a ledgered free parameter (owner ruling R-AY, 2026-09-06)

**What changed.** Rule 21 gained a one-clause cross-reference to the rules 1/13 authorized
price-tuning channel (§11). Nothing else in rule 21 moved: every keeper still carries a DOF
ledger, every free parameter still names its identification source, and a residual that can
only be closed by a tuned value is still an open root-cause issue — with the single, named
exception the clause states.

**Why.** §11's condition (e) already required a price-tuned `offer_curve_by_group` band
multiplier to be *"carried as a free parameter in the DOF ledger (rule 21 `[R-DOF]`),
identified by the ruling rather than by a measured source"*. That requirement lived only in
rule 1's text; rule 21 itself still read, without qualification, that a residual closed by a
tuned value is an open root-cause issue — so the two rules could be read apart, and a reader
of rule 21 alone would count the authorized multiplier as an unresolved defect. The audit
program's director sitting of 2026-09-06 (~00:15Z, card "DOF / C6") ruled, choosing the
recommended option verbatim:

> *"Count them in the DOF ledger, C6 passes under the declaration."* — owner ruling **R-AY**

i.e. each price-tuned band multiplier is a ledgered free parameter with identification source
**"price residual, authorized channel (rules 1/13 amendment 2026-09-05)"**, reported at full
magnitude on the determination basis; **no gate moves**; and rule 21 gets a one-clause
cross-reference. R-AY therefore *confirms* what condition (e) already required, from the audit
rubric's side, and adds the pointer in rule 21 so the two rules cannot be read apart.

**What the clause says, and what it does not.** The clause (CLAUDE.md rule 21, appended
2026-09-06) states three things and no more: (1) the authorized multiplier IS a ledgered free
parameter whose identification source is the ruling itself, not a measured input; (2) it is
reported at full magnitude on the determination basis — the carve-out never hides a number;
(3) its presence does not, by itself, make the residual it closes an open root-cause issue,
**while every other tuned value still does**. The amendment's conditions (a)–(e) are NOT
restated in rule 21; they live in rule 1 and bind unchanged. `no_pinning_to_actuals` and the
forbidden-flag machine check remain outside the carve-out (§11).

**Enforcement is unchanged.** `calibration_verdict.score_governance` already implements
condition (e)'s declaration half: with a well-formed `governance.authorized_price_tuning`
block, `no_fit_to_price_residuals` and `levers_trace_to_measured_input` read as scoped; without
one, a false assertion still FAILs C6 (§11, "Enforced, not merely asserted"). R-AY changed no
scoring logic — the scorer's docstring gained the R-AY citation beside the rule 1 citation so a
reader sees both. The DOF-ledger half of condition (e) is NOT machine-checked: `audit_keepers`
check E8 validates only that residual-sourced ledger rows carry a `root_cause`, and
`attestation_shape_finding` mirrors the declaration check. Whether a ruling-identified ledger
row should be a distinct machine check is a calibration-desk / audit-program item, not a rule
question (`docs/handoffs/FINDING-g3-rdof-price-tuning-xref-2026-09-06.md` §4).

**The live case at amendment (verified, not adjudicated).** The MISO keeper
`2026-09-05-miso-220-nonsteam-lift` (promoted `743b3dc0`, bundle
`results/calibration/miso220_nonsteamlift_B`) carries a well-formed
`governance.authorized_price_tuning` block, sets `no_fit_to_price_residuals` and
`levers_trace_to_measured_input` to `false` deliberately (`ed07a641`), and scores C6 PASS with
determination CALIBRATED on committed artifacts. Its `free_parameters` ledger is "41/2
unchanged" (its own `attested_by` text): the ×1.10 lift is carried under the pre-existing
`offer_curve_by_group` row (identification `residual`, 92 scalars) plus the governance block's
`dof_entry` pointer — there is no distinct ledger row naming the ruling as its source. That gap
is recorded and routed in the G-3 finding; the attestation is the calibration desk's artifact
and was not edited.

## 14. Rule 30 `[R-TOUCHPOINT-FOLD]`(a) — a held-out year renders AS a year, not as a designation (owner, 2026-09-06)

**The instruction, verbatim** (owner, 2026-09-06, in session neiso-103 immediately after that
session's 2020 input-readiness finding):

> *"the formatting on the html dashboard for holdout years shouldn't be any different than the 3
> training years, it should show the results in the report view on run explorer and does not need
> a special designation."*

**What clause (a) said before.** Rule 30 landed 2026-09-05 (§12) to stop a touchpoint publishing as
a SECOND CARD for a configuration the keeper already publishes. It folded the run — hidden from the
run list, years offered in the keeper's selector — but it then MANDATED that the folded years render
"as columns of ONE combined **Validation Touchpoints** panel on the keeper's page beside the
in-sample column." The fold fixed the two-cards defect and introduced a smaller one of the same
kind: the keeper's own Report (`renderReport`) drew its year set from `runYears()` — the run's OWN
solve years — so a folded year was **absent from every report table and chart** and reachable only
through a separate panel, a `Held out (rule 22)` optgroup in the year dropdown, a ` — validation
holdout` tier suffix on each entry, and a "*<year>* is a held-out year" provenance banner. Four
designations for a year that is, by rule 30's own reasoning, the same recipe as the three beside it.

**What it says now.** The Report's year set is `selectableYears()` — own solve years UNION folded
held-out years, globally ascending — so a folded year is an ordinary year column everywhere the page
names a year. The panel, the optgroup split, the tier suffix and the banner are **DELETED, not
hidden** (rule 26 `[R-DELETE]`: a dead render path is a re-armable answer), together with the
`TIER_LABEL` map, `HOLDOUT_VERDICT`, `renderHoldoutPanel`, `renderHoldoutPanelCombined`,
`holdoutYearBanner` and `foldedHoldoutBlocks` — `docs/codebase-site/js/backcast-runs.js`
2,655 → 2,450 lines, +64/−270. Folded payloads are now loaded EAGERLY at run load rather than on
year selection, because a report that renders every year at once cannot wait for a lazy fetch.

**The one designation that survives, and why.** Rule 22 requires that a validation number never read
as a certified out-of-sample skill number. That reading is kept as a **single footnote** naming the
held-out years and restating rule 30(c) — not a panel, not a badge, not a per-year label. Dropping it
entirely would have put the amendment in conflict with rule 22 rather than with rule 30(a) alone.

**What is UNCHANGED, stated so it is not re-litigated.** The fold itself and the `holdout.keeper`
stamp; `scripts/stamp_touchpoint_holdout.py` (no output change — the block it writes is unchanged,
only its docstring); the deep-link redirect from a folded id to its keeper; clause (b)'s Calibration
Status **holdout ladder**, which is per-year by design, is a different surface, and stays; and clause
(c) entirely. **No determination moves**: no scorer path was touched (`git diff` names no `.py` file
on the verdict path), and all three affected keepers re-score `CALIBRATED` byte-identically —
`2026-08-17-neiso-99-joint-p1`, `2026-08-15-pjm-162-inputclock`,
`2026-09-05-ercot248-two-config-keeper`.

**Verified by rendering, not by reading the diff.** Headless Chromium over the six ISO keeper pages:
NEISO now reports 2020–2025, PJM 2021–2025, ERCOT 2022–2025 as ordinary year columns with a flat
ascending dropdown, zero optgroups, no panel and no banner; CAISO / MISO / NYISO (no folded
touchpoints) are unchanged at 2023–2025 and render no footnote. The three console errors on the
`file://` preview are blocked external CDN fetches (d3, Google Fonts) that a negative control
reproduces identically on unmodified `main`.

**Scope limit.** This is a PRESENTATION amendment to clause (a). It grants nothing about which years
may be solved, scored or registered: the rule-22 tier markers, the holdout freeze
(`scope.tiers = ['locked_test']`) and the registration marker gate (§4) are untouched.

Executed by session neiso-103, 2026-09-06.

## 15. Rule 30 `[R-TOUCHPOINT-FOLD]`(a) — the Run Explorer's Report is SCORES AND CHARTS ONLY (owner, 2026-09-06)

**Origin.** Hours after §14 landed, the owner opened the Run Explorer and rejected what was still
there, verbatim:

> *"Delete the stupid per year determination from the run explorer I do not need narrative from you
> in my results viewing ANYWHERE I just want the scores and charts and make it so every iso with
> holdout years run has them SHOW up in the report what the actual fuck"*

**What "the per year determination" actually was.** Not a leftover of the panel §14 deleted — that
was gone. It was the **Run Definition** panel, which renders the registry sidecar's `definition`
string verbatim, and for two ISOs that string had grown into a per-year determination essay. The
ERCOT keeper's read, in the results view, above the scores:

> *"2023 = the CARVE-OUT config … C3a -7.3% / C3b 0.102 / C3c 180 of 181, every criterion PASS,
> zero caveats. 2024/2025 = the FORWARD config … DETERMINATION CALIBRATED."*

A determination, per year, in a viewer whose job is to show numbers. §14 de-designated the held-out
*years* and left the *prose* untouched; this amendment finishes the job on the prose.

**What was deleted** (all four, render path and all — rule 26 `[R-DELETE]`, since a dead render
path is a re-armable answer):

| block | why it goes |
|---|---|
| **Run Definition** panel (`bc-narration`) | the per-year determination essay the instruction names |
| **rule 22 held-out-years footnote** | §14 kept it as "the one designation that survives"; it is narrative, and (b)'s surface already carries the reading |
| **Zero-forcing ablation twin** + market story | rule 20 `[R-DOF]` stopped requiring the twin 2026-07-14; no registered run carries one — the panel rendered "*not yet registered*" plus prose |
| **Diagnostics** auto-generated findings (`diagFindings`) | sentences about the numbers, beside the numbers |

Kept: **Year Scorecards**, **LMP Alignment**, **LMP Delta Heatmap** — and the Charts and Tables
views, untouched. The run's identity (id · date · keeper pill) moves from the deleted panel to the
page sub-header, where it now labels every view rather than only the Report. The two long
methodology captions on the surviving panels were cut to legends.

**Rule 22's substance is unchanged; only its surface moved.** A validation number must still never
read as a certified out-of-sample skill number. With the run explorer carrying no designation at
all, that reading rests entirely on clause (b)'s surface — the Calibration Status page's per-year
table, which carries a **Tier** column and the line *"Held-out years are reported, not gating — the
ISO determination is the 2023–2025 verdict (rule 22)."* The guard
(`tests/scoring/test_holdout_render_parity.py`) was re-pointed accordingly: its
`test_rule22_tier_caveat_survives_as_a_footnote` — which pinned the footnote to the run explorer —
is replaced by a pair, one asserting the run explorer renders no narrative prose and one asserting
the status page keeps the tier reading, each with its negative control.

**The instruction's second half was already true, with one hole.** All three ISOs that have ever
run a holdout year already rendered it as an ordinary year column at HEAD — verified by headless
render: ERCOT 2022, NEISO 2020/2021/2022, PJM 2021/2022. CAISO, MISO and NYISO show none because
**none exists**: no touchpoint run is registered for them, no out-of-training bundle sits in
`results/calibration/`, and CAISO's and NYISO's `complete` markers are withdrawn, so a spend is
governance-blocked, not hidden. The hole worth closing was in the fold's link resolution: a
companion whose `holdout.keeper` names a run that has since been **pruned** (rule 15's keeper-only
retention prunes a superseded keeper) was read as "linked to a *different* keeper" and skipped
entirely — its years vanished from the report AND it reappeared as its own run card, the exact
defect rule 30 names. A dangling stamp now reads as unstamped in both `holdoutCompanions` and
`foldTargetOf`, so a keeper promotion cannot silently drop an ISO's held-out years.

**Scope.** Presentation only. No scorer path was touched, the browser computes no verdict, grade,
caveat budget or determination, and every deleted block was display prose over data that still
lives in the committed sidecar (`definition`, `holdout`) or in `scripts/calibration_verdict.py`.
Clauses (b) and (c) are untouched, as are every marker, the holdout freeze, every keeper shard and
every determination. Verified by headless render of all six ISO keeper pages plus the Charts and
Tables views and a folded deep link.

## 16. Changes to this file

| date | change |
|---|---|
| 2026-09-06 | Added §15: rule 30 `[R-TOUCHPOINT-FOLD]`(a) amended AGAIN the same day by owner instruction (verbatim above) — the Run Explorer's Report is **scores and charts only**. The run-definition panel (the per-year determination essay the instruction names), the rule-22 footnote §14 had kept, the zero-forcing ablation twin + market story, and the auto-generated diagnostics are **deleted** (rule 26); run identity moves to the page sub-header. Rule 22's reading now rests entirely on clause (b)'s status-page year table (Tier column + "reported, not gating"), and the guard was re-pointed there with negative controls. Fold fix: a **dangling** `holdout.keeper` stamp (keeper pruned under rule 15) now reads as unstamped, so a promotion cannot drop an ISO's held-out years. Presentation only — no scorer path, marker, freeze, shard or determination touched; verified by headless render across all six ISOs. "Changes to this file" renumbered §15 → §16 (no external reference cited §15). |
| 2026-09-06 | Added §14: rule 30 `[R-TOUCHPOINT-FOLD]`(a) amended by owner instruction (verbatim above) — a folded held-out year renders as an ORDINARY YEAR COLUMN in the Run Explorer's Report, with the mandated *Validation Touchpoints* panel, year-selector optgroup split, tier suffix and held-out banner **deleted** (rule 26), and rule 22's tier caveat kept as a single footnote. Presentation only: no scorer path touched, all three affected keepers re-score identically, clause (b)'s status-page ladder and clause (c) untouched, no holdout marker or freeze moved. Verified by headless render across all six ISOs with a negative control on `main`. "Changes to this file" renumbered §14 → §15 (no external reference cited §14). Executed by session neiso-103. |
| 2026-09-06 | §4: recorded owner ruling **R-AZ** (audit-program director sitting, card "Marker gate", verbatim option *"Re-check at registration"*) — the rule-22 tier marker is now re-checked at REGISTRATION as well as at solve launch, closing the Z-6 window in which a multi-hour LP outlives the marker it launched under. New `holdout_policy.registration_refusals` + `dashboard_add_run.enforce_registration_marker_gate`; no bypass flag; launch gate, D-6, `audit_keepers`, markers, freeze, shards and every registered run untouched — all five holdout-year sidecars at HEAD replay clean. Executed by audit lane Y-16. |
| 2026-09-06 | Added §13: rule 21 `[R-DOF]` one-clause cross-reference to the rules 1/13 authorized price-tuning channel (owner ruling **R-AY**, audit-program director sitting 2026-09-06 ~00:15Z, card "DOF / C6", verbatim *"Count them in the DOF ledger, C6 passes under the declaration"*; executed by rule-amendment lane G-3). A price-tuned band multiplier is a ledgered free parameter identified by the ruling, reported at full magnitude, and not by itself an open root-cause issue; every other tuned value still is; no gate moves, no scoring logic changed. §11 gained a forward pointer. Records the live MISO keeper reading (declaration present, C6 PASS, no distinct ruling-identified ledger row — routed, not edited). Took §13 on merge behind main's same-day §12 (rule 30 `[R-TOUCHPOINT-FOLD]`); "Changes to this file" renumbered §13 → §14 (no external reference cited either number). |
| 2026-09-05 | Added §8.2: rule 29 `[R-SCREEN]` clause (c), **delete before merge** (owner ruling **R-AV**, verbatim *"Delete before merge"*, on the rule-29 / Class-E parity collision the v31 second coda `da99f34b` routed; executed by audit lane Y-13). A screen bundle, or a control bundle a screen earns under clause (b), is `git rm`-ed from `results/calibration/` before its PR merges; the PRECOMMIT/FINDING doc carries every number; `check_registry_payload_parity` is the enforcement and an unregistered bundle dir is a gate red, not an allowlist candidate. Records the first execution (two dirs pruned, numbers confirmed in committed records first). No keeper, marker, shard or determination touched. |
| 2026-09-05 | Added §11: the owner's authorized price-tuning carve-out amending rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]`, its five binding conditions, and the machine checks + fail-closed tests that enforce it. Landed alongside main's same-day §9 (rule 15 retention) and §10 (bench fingerprint); this section took §11 on merge and "Changes to this file" renumbered §11 → §12. The CLAUDE.md rule-1 genealogy pointer was repointed §9 → §11 in the same commit. |
| 2026-09-05 | Added §10: the bench builder fingerprint's hash narrowed from the RAW BYTES of `BUILDER_SOURCES` to `ast.dump(ast.parse(source))` (owner ruling **R-AS**, card M *"Adopt Proposal A"*, on the Y-10 finding; executed by audit lane Y-12). Records the mis-tuned trigger (53 % of the hashed surface is prose; three false alarms, zero true positives), the computed counterfactual over `dee6472c`/`677b605a`, the stated limit that docstring edits still fire, and the one-time re-stamp of all 20 bench parts `b2f21b9a00d3` → `4254168edcfe` with payload sha256 unchanged on every one. The nyiso-148 guarantee is unchanged; no keeper, marker, shard or determination touched. "Changes to this file" renumbered §10 → §11 (no external reference cited §10). |
| 2026-09-05 | Added §9: rule 15 `[R-DASHBOARD]` retention amended from the top-15-per-ISO age cap to **KEEPER-ONLY** (owner instruction of 2026-09-05, quoted verbatim; executed by session ercot-248 and the #4808/#4816 cleanup lane). Records what the cap was, what replaced it, that the registration duty for rejected probes is untouched, and the standing implementation lag (`dashboard_add_run.KEEP_PER_ISO` still sweeps by age — a calibration-desk item). "Changes to this file" renumbered §9 → §10 (no external reference cited §9). |
| 2026-08-30 | §3: indexed rubric **v3.1**'s C7 retirement (owner directive verbatim) and rubric **v3.5** (owner option-(B) decision of 2026-08-25 — diurnal price amplitude added REPORTED-ONLY and BAND-FREE; no CLAUDE.md rule text changed) alongside the rule-20 genealogy they extend. v3.5 re-verified determination-neutral over the 2026-08-30 six-keeper roster. Canonical narratives stay in the rubric §9; index entries only. |
| 2026-08-17 | §4: recorded rubric **v3.3** — the owner's amendment that a ledgered C3c caveat is REPORTED but no longer DOWNGRADES the determination, withdrawing the "never `CALIBRATED`" half of CLAUDE.md rule 22 guard (d). 6 registered runs re-score `CALIBRATED-WITH-CAVEATS → CALIBRATED`, 2 of them keepers (NYISO, NEISO); holdout tiers untouched. |
| 2026-08-17 | §4: recorded the first lane RESTED at `NOT-YET` (CAISO, session caiso-201, owner ruling Q1). No rule text changed — the entry exists so the precedent that an exhausted lane with a genuinely failing load-bearing criterion *rests* rather than ledgers or declares is citable. |
| 2026-08-23 | §7.1 MISO entry annotated with the owner's 2026-08-18 LANE-CLOSURE LIFT (session miso-178): the entry previously read as if the miso-163 closure stood. Lift scope recorded — the C3a-2025 lane re-opens, the `ordc_scarcity_overlay` cell stays `G`, the narrowed re-opening test is unchanged. Decision-record annotation only; no norm touched. |
| 2026-08-17 | Added §7.1: owner rulings adjudicated through the matrix, seeded with the 2026-08-17 MISO C3a-2025 model-class closure (session miso-163, mechanism `ordc_scarcity_overlay` cell `G`). Records the ruling, its two-half basis, the ERCOT (Q-B) precedent, and the narrowed re-opening test. No norm added, reworded or dropped — rule 28's text is unchanged and this is a decision record, not a rule. |
| 2026-07-27 | Added §7: rule 28 `[R-MECH-MATRIX]` (cross-ISO mechanism testing matrix) — origin and canonical file locations. "Changes to this file" renumbered §7 → §8 (no external references cited §7). |
| 2026-07-26 | Added §6: the 2026-07-22 history rewrite orphaning pre-rewrite bundle `git.sha` provenance (owner decision B close-out) — no SHA mapping saved, replay/goldens unaffected (`git_sha` in both ignore sets), the `--reuse-solved` unresolvable-SHA refusal intentional and load-bearing. "Changes to this file" renumbered §6 → §7 (no external references cited §6). |
| 2026-07-25 | §5: recorded the ≥300-line push deadlock (rule 27 + API-only leaving no compliant path) and the owner's per-commit `git push` waiver that landed wave 4C. Per-commit, not a standing exception. |
| 2026-07-25 | Created (refactor-consolidation Wave 5B, owner decision D-6). Takes the rule-27 incident writeup and the audit N↔N+1 mapping paragraph out of `CLAUDE.md`, and indexes the rule-20 / rule-22 amendment narratives at their canonical homes. No norm was moved, reworded, or dropped. |
