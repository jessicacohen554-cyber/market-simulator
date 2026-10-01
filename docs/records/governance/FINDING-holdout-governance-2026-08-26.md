# FINDING — Holdout governance rulings, program-director sitting 2026-08-26

**Lane:** holdout-governance records lane, branch
`claude/holdout-governance-rulings-0826-iryy5i` (the harness-designated name for
the dispatch's `claude/holdout-governance-0826`; recorded here for
traceability). **Executed 2026-08-30** against a moving `origin/main` — the
dispatch named base `3f7388e`; the work was re-derived on `4ed7cd3` and rebased
forward as main advanced (`159aba5` → `f79f4aa` → `a53b7b3`), with the owner
merging rulings 1 and 2 mid-session (PRs #4306, #4307).

**NO LP, NO SOLVE, NO YEAR SPENT.** This lane changed what is *permitted*,
never exercised it: every verification below runs the gates' own
refusal/permission code paths (function-level invocations plus synthetic
registry sidecars), and nothing was scored or registered. No ISO keeper shard,
no mechanism-matrix shard, no backcast registry file, no bench part, and no
`.github/workflows/` file was touched.

Three signed owner rulings from the 2026-08-26 sitting, executed in order and
pushed ruling-by-ruling:

| ruling | card | commit (as pushed) | state |
|---|---|---|---|
| 1 — scoped freeze lift + charter closed with cause | 6 | `0589b6f` + `7a40c55` (merged to main, PR #4306) | EXECUTED |
| 2 — locked-test scheduling precondition | 7 | `3643318` (merged to main, PR #4307) | EXECUTED |
| 3 — decision-1 acknowledged CLOSED-OVERTAKEN | 10 | `583d3ad` | EXECUTED |

---

## 1. Ruling 1 (card 6) — the freeze lifted for the VALIDATION tier only; the layup charter closed WITH CAUSE

**The ruling, verbatim:** *"Close the layup charter with cause; lift the freeze
for the VALIDATION tier (2020-2022) for ISOs holding a `complete` marker.
`final` stays empty and the locked test stays frozen. Restores the diagnostic
touchpoint loop."* It takes option (A) of the decision card
`docs/audit/AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4 exactly as recommended.

### 1.1 The cause, stated plainly

"Closed with cause" states the cause; it does not imply resolution. **The CAMPD
economic-layup detector question REMAINS OPEN**: the post-guard `CC_REGULAR`
capacity-weighted outage share is **14.2–36.7 %** with **17 of 18 ISO-years
above the ~10–15 % EFOR+planned norm** (audit row O4 re-measurement,
2026-08-18), and charter §9 records the residual as a **definitional seam**
(published series measure *unavailability*; the CEMS detector measures
*non-operation*) that four independent investigation lanes measured as **not
closable by any admissible discriminator**. The lift is a decision to **proceed
with a known-open input question** — carried explicitly as a documented seam
that **every keeper's availability envelope inherits** — on the asymmetry the
owner relied on in both prior narrow lifts: validation years are iterable,
re-spendable, model-selection-only evidence; locked-test years are touch-once
and stay frozen. One clause of the charter's §7 close-with-cause leg is met
only in a weaker form and the closure says so: the extract is confirmed the
best **buildable** representation, not "fit for purpose" without remainder
(charter §10).

### 1.2 How the scoped lift is expressed — and why it needed one code change

The CLI year gate read the freeze as a **boolean** (`freeze.get("active")`), so
"validation lifted, locked test frozen" was not expressible in JSON alone, and
a blanket `active: false` was rejected because it would have removed the freeze
layer from the locked tier entirely (leaving its refusal resting *only* on the
empty `final` block, where the ruling says the locked test **stays frozen** —
the freeze must keep outranking even a future `final` marker until explicitly
lifted for that tier). The implementation:

- **`frontend/data/backcast/holdout-freeze.json`** keeps `active: true` and
  gains the scope as current state: `scope.tiers = ["locked_test"]`. The
  `history` array is **appended, never rewritten** (6 → 7 entries, prefix
  asserted byte-equal programmatically before write); `declared` (2026-07-25),
  the original `reason`, and the 2026-08-06 narrow-lift/re-arm record
  (`lifted_and_rearmed`, `lift_scope`, `by`) are preserved **verbatim**
  (asserted). The superseded `lifts_when` text is preserved verbatim inside the
  new history entry. The `note` rewrite also corrects the standing prose
  conflict (director-board item 9): intake needs **no** authorization per rule
  22 as amended 2026-08-06 — the old Option-2 wording is kept as a bracketed
  correction notice.
- **`scripts/lib/holdout_policy.frozen_tiers`** is the new **single, fail-closed
  scope reader**: an inactive freeze covers nothing; an active freeze whose
  `scope.tiers` is missing, empty, or unparseable covers **every** tier (the
  pre-ruling file shape and behaviour, pinned by the pre-existing
  `test_freeze_still_outranks_both_markers`, which passes unchanged); unknown
  tier names can only fail to narrow, never widen.
- **`run_calibration_full.enforce_holdout_year_gate`** now refuses on the
  **frozen subset** of the breach years *before* the flag and marker checks;
  non-frozen breach years fall through to the tier-marker check unchanged. This
  function is the choke point for every solve path (the CLI, `run_calibration.py`,
  the `replay_keeper` paths and `knob_jacobian` — the O5 closure's wiring).
- **`tests/scoring/test_holdout_year_gate.py`** gains a `TestTierScopedFreeze`
  class (8 tests): the end state, the marker gate not bypassed, the
  locked-refusal-over-`final`-marker case, mixed-tier refusal naming the frozen
  years, every degenerate-scope fail-closed shape, the inactive case, the
  reader's full behaviour table, and a pin that the **live committed file**
  reads as locked-test-only. 38/38 pass.
- **`calibration-complete.json`**: two surgical prose corrections only — the
  `note`'s freeze sentence brought current (old wording preserved in a
  bracketed notice) and NYISO's `freeze_interaction` annotated with the lift. A
  structural walk asserted the **only** changed leaves are `.note` and
  `.complete.NYISO.freeze_interaction`; **the `final` block is byte-untouched
  and still `_note`-only**, `complete` = {NEISO, NYISO, PJM} unchanged,
  `withdrawn` unchanged.

### 1.3 Behavioural verification — all three enforcement paths, by invocation

Run on the live post-edit repo state (`scratchpad/verify_gates.py`; function
-level invocations + synthetic registry sidecars; nothing solved, scored or
registered). **55/55 checks as required.** The full transcript is reproduced
here because it is the deliverable's core evidence.

**PATH 1 — `run_calibration_full.enforce_holdout_year_gate`** (the CLI `--year`
gate; also the choke point for `run_calibration.py`, `replay_keeper`,
`knob_jacobian`):

- **PERMITTED** — validation years {2020, 2021, 2022} × `complete` ISOs
  {NEISO, NYISO, PJM} with `--holdout-authorized`: all **9** invocations return
  cleanly (with the gate's own "ITERABLE validation-tier score" warning).
- **REFUSED (flag missing)** — 2022 × {NEISO, NYISO, PJM} *without*
  `--holdout-authorized`: all 3 exit `--holdout-authorized not passed`. The
  flag remains half the grant.
- **REFUSED (no marker)** — 2022 × {ERCOT, CAISO, MISO} *with* the flag: all 3
  exit `<ISO> is not in the 'complete' block`. Lifting the freeze does not
  bypass the marker gate.
- **REFUSED (freeze) — THE CHECK THAT MATTERS** — locked-test years
  {2019, 2026} × **all six ISOs** × {with, without `--holdout-authorized`}:
  all **24** invocations exit on the freeze branch (`ACTIVE HOLDOUT SPEND
  FREEZE … frozen tiers ['locked_test']`), including the three `complete`
  ISOs. 2018 (dropped year, fail-closed to locked tier) × all six ISOs with
  the flag: all **6** refuse on the same branch. A mixed
  `--year 2022 2019` request refuses naming `[2019]`.

**PATH 2 — `legitimacy_diagnostics.run_d6_quarantine`** (the `--keepers` CI
gate). D6 sweeps *registered* sidecars against the **tier markers**; it has
never read the freeze file, so its locked-test refusal rests on the empty
`final` block (fail-closed `holdout_policy`), unchanged by this ruling:

- Live registry: **PASS, 0 failures** — the only out-of-training rows are the
  two authorized 2022 touchpoints (`2026-08-05-pjm-2022-touchpoint`,
  `2026-08-06-neiso-2022-corrected-basis`), verdict `authorized one-shot`.
- Synthetic sidecars scored against the **live** marker doc: NEISO-2022 and
  NYISO-2020/2021 → `authorized one-shot`; ERCOT-2022 → **FAIL** (no marker);
  NEISO-2019, PJM-2026, NYISO-2018 → **FAIL** (`locked_test` tier, no `final`
  entry). Exactly the required split.

**PATH 3 — `scripts/audit_keepers.py::holdout_quarantine_failures`** (the H1
CI gate). Same posture as D6 (tier markers, no freeze read):

- Live registry: **0 failures**.
- The same six synthetic sidecars: **exactly**
  {ERCOT-2022, NEISO-2019, NYISO-2018, PJM-2026} fail; the marked validation
  spends pass. Agrees with paths 1–2.

The CI-tier composite gates were also run end-to-end on the final tree:
`scripts/audit_keepers.py --check` → **PASS 0/0**, and
`scripts/legitimacy_diagnostics.py --keepers --no-d2-recompute` → all gates
PASS including **D-6 holdout quarantine — PASS**.

### 1.4 Records closed by ruling 1

- `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` — **§10 CLOSED
  WITH CAUSE** (ruling verbatim, the honest §7-clause caveat, the open-seam
  cost, the execution list, and what the closure does NOT do); header status
  updated; §6's freeze statement annotated as superseded with the original
  retained verbatim.
- `docs/audit/third-party-audit-2026-08.md` row **O4 → RESOLVED 2026-08-26**
  (prior text preserved; resolution appended per the row convention).
- Director board item 2 (the O4/O5 card) → signed/executed; item 9 (the
  freeze-file prose conflict) → corrected as part of the same edit.

## 2. Ruling 2 (card 7) — locked-test scheduling gates on the validation ladder

**The ruling, verbatim:** *"Locked test is scheduled only after an ISO has run
its 2020-2022 touchpoints and the loop has stopped surfacing repairs. Spends
the one-shot against the most-prepared config, which is the whole design
intent."*

**A STANDING POLICY — not a schedule, not a grant.** As recorded: an ISO
becomes **eligible to be considered** for `final` only after (i) its 2020–2022
validation touchpoints have been run and (ii) the touchpoint loop has stopped
surfacing repairs. **Eligibility is not a grant** — `final` remains an explicit
owner act, per ISO, every time, and adding an ISO to `final` still spends the
single most irreversible resource in the policy.

**The two standing constraints, restated so this is never read as a green
light:**

1. **NEISO's 2019 basis is UNREPAIRABLE** — ISO-NE migrated its newswire
   mid-2018 and the Mar–Jun recaps were never carried over
   (`FINDING-neiso86-gas-basis-intake-2026-08-06.md` §5.1) — and NEISO's
   `final` readiness reads **NOT YET ON THE MERITS** (2019 unsolvable at HEAD;
   non-discriminating on C3c).
2. **NO ISO HAS EVER SPENT A LOCKED-TEST YEAR.** `final` carries only its
   `_note`. Verified structurally in this lane before every push: the `final`
   block of `calibration-complete.json` is byte-identical to its pre-session
   state, `_note`-only.

**Where it is recorded:** CLAUDE.md rule 22's locked-test bullet (surgical
edit, blob-verified; the same commit also brings rule 22's freeze sentence
current with the card-6 tier scoping); `docs/governance/rule-history.md` §4
(two dated 2026-08-26 entries — the scoped-freeze machinery change and this
precondition); audit row **O6** (standing policy recorded; the row correctly
remains about unspent one-shots — it is *advanced by a decision*, not resolved
by a spend); the freeze file's `lifts_when` (landed with ruling 1); and
director-board item 4. **No marker was touched: `final` stays exactly as
found.**

## 3. Ruling 3 (card 10) — decision-1 acknowledged CLOSED-OVERTAKEN

The owner acknowledged **decision-1** (the `forecast_xyear_warmstart` default
flip, `docs/handoffs/perf-a-warmstart-decision-memo-2026-08.md`) as
**CLOSED — OVERTAKEN BY EVENTS** and dropped it from the owner decision queue.
The substance was decided at K.3 (D-9 flipped the default ON; D-10 disarmed the
forecast lane through `shipped_forecast_xyear_warmstart()`; no flip ships) and
the G1 declaration (2026-08-16) had recorded exactly that with "owner ack
requested". **A records line only — no code, no config, no determination
changed.**

Queue removals, everywhere the queue is enumerated: plan §6 item 1 annotated
closed; plan §8 ledger entry appended (append-only, tail-appended); director
-board item 6 retired in place (retired-in-place rather than deleted, so item
numbering cited elsewhere survives); the memo's STATUS header updated with the
original preserved. **One count discrepancy recorded rather than smoothed
over:** the sitting's card says the item was carried **twenty-one** director
cycles; the board's v13 pin says **eighteen** (and the board has once before
corrected a ±2 numbering drift on this same counter). The owner's count is
recorded as ruling text; the divergence is noted here for the next director
cycle to reconcile.

## 4. `audit_keepers` before / after

- **BEFORE any edit** (branch base `4ed7cd3`): `scripts/audit_keepers.py
  --check` → **PASS: 0 failure(s), 0 warning(s)**. The dispatch expected a
  failing S1 (stale status parts + unlabelled bench fingerprints for
  PJM/CAISO/NEISO); **that failure is not present at this HEAD** — it was
  evidently repaired on main between the dispatch's pin (`3f7388e`) and this
  lane's base. What remains are `[!] STALE BENCHMARK` *warnings* for PJM/NEISO
  bench parts (fingerprint `dbea7bf45111`), printed but not failing, and not
  touched by this lane.
- **AFTER all three rulings**: **PASS: 0 failure(s), 0 warning(s)** — identical
  verdict; the same stale-benchmark warning lines; no new failure introduced.
  `tests/scoring/test_holdout_year_gate.py` 38/38;
  `legitimacy_diagnostics --keepers --no-d2-recompute` all-PASS.

## 5. Integrity notes

- Every push blob-verified (git blob sha, local vs remote, plus line counts)
  before the next ruling began; every touched file **grew** (CLAUDE.md
  605 → 618, plan 3,390 → 3,413, board 1,424 → 1,434, charter 498 → 577,
  rule-history 417 → 455, freeze file 65 → 74 lines) — nothing shrank, no
  list or count got shorter (the board queue items retired in place).
- The freeze `history` prefix and the marker `final`/`complete`/`withdrawn`
  blocks were asserted unchanged programmatically before writing, not by
  inspection.
- Concurrent lanes: the ERCOT governance-rulings lane (#4303) and two
  calibration lanes (#4304, #4308) merged to main during this session; none
  touched this lane's files (checked by name-diff before each rebase), so no
  race on `holdout-freeze.json` or `calibration-complete.json` occurred.
- Transport: `git push` on a freshly fetched base each time; no HTTP 408/500,
  no `push_files` fallback needed; no new workflow files; no CI runner minutes
  spent by this lane.
