# capx director — prompt pack (revised at refresh #15, 2026-08-30; first issued 2026-08-25)

Canonical text of the session prompts live on the capacity-expansion (Forecast Finalization)
track. Ledger: `docs/handoffs/capx-director-ledger-2026-08.md`. Signatures:
`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5. Revisions at r#8: D7 LANDED
(`ca8b749`) and drops from the live set; D10 corrected for the nyiso-155 keeper state; D11
RE-SCOPED to D11-R (the D-1 volume rule — ledger §0e.3), never run in its original form.
Revision at r#9: every prompt's freeze guardrail updated to the TIER-SCOPED state (owner card 6,
executed 2026-08-30 — locked test frozen for every ISO; validation governed by the `complete`
marker + --holdout-authorized; nothing a capx lane touches either way).
Revision at r#11: **S-4V added** — S-4 landed its intake (PR #4312) but ended before its
verification pair ran; the owed §5 (pair + FC-1 re-score + registration + finding TBDs + cell
re-stamp + board refresh) is chartered as its own lane below.
Revision at r#12: **Q5-W added** (governance RECORDS lane, not a capx lane) — the owner's
r#12 decision-card ruling on Q5's recurrence: WITHDRAW the NYISO `complete` marker (CAISO
precedent, applied uniformly). **Once Q5-W lands, `complete` = {NEISO, PJM}** and every
guardrail line below reading "`complete` = {NEISO, NYISO, PJM}" is superseded accordingly
(in-flight lanes fetch fresh state and are unaffected — no capx lane touches either tier).

| lane | status | branch | model | profile | heavy slot? |
|---|---|---|---|---|---|
| **D10** NYISO T1-X crossover | reissued r#8 (corrected) — **still unstarted at r#11; highest-value light lane** | `claude/capx-d10-nyiso-t1x` | Fable | nyiso | no |
| **D11-R** D-1 entry volume rule | **RUNNING since r#10** (owner-dispatched 2026-08-30; nothing pushed at r#11) | `claude/capx-d11r-entry-volume-rule` | Fable | ercot | no (Phase 0 first; A/B is light) |
| **S-123** MISO adequacy package | issued r#5, not started — **check FAILED at r#9/r#10/r#11: miso-190 in flight; held on the start-time check** | `claude/capx-s123-miso-adequacy` | Fable | miso | only if it re-measures (MISO = no co-run) |
| **S-4** NEISO hydro accreditation | **LANDED r#10** (PR #4312; factor 0.7352) — historical prompt below; its owed verification is lane **S-4V** | `claude/capx-s4-neiso-hydro-syqu7m` | Fable | neiso | no |
| **S-4V** NEISO verification | **NEW at r#11** — completes S-4's §5: pair, re-score, registration, finding TBDs, cell re-stamp, board refresh | `claude/capx-s4v-neiso-verification` | Fable | neiso | no (9.2 min/leg) |
| **S-5** PJM requirement horizon-edge | issued r#5, not started — ready when a heavy slot frees | `claude/capx-s5-pjm-horizon-edge` | Fable | pjm | no (S-6 is the heavy one, strictly after) |
| **Q5-W** NYISO marker withdrawal | **NEW at r#12** — governance records lane executing the owner's Q5 ruling (WITHDRAW, CAISO precedent) | `claude/q5w-nyiso-marker-withdrawal` | Fable/Opus | code | no (records only) |

**Suggested order (r#11):** S-4V + D10 now (both light; S-4V unblocks S-4b and possibly a
second (a)+(b)-PASS ISO). S-5 as a heavy slot frees (its re-score self-gates; PJM quiet on the
backcast side). S-123 held on its start-time check (miso-190 in flight). D12 is chartered only
after D11-R reports (owner-ratified sequencing). Only S-123's optional re-measure and the later
S-6 contend for the ≤2 heavy-solve cap, which is SHARED with the owner's concurrent backcast
solves.

---

## D7-NYISO — gate re-score + leg-(c) harmonisation — **LANDED `ca8b749` (PR #4289); historical record, do not re-run**

```
You are the D7-NYISO GATE RE-SCORE session of the capacity-expansion (Forecast
Finalization) track, chartered by the capacity-expansion director
(ledger: docs/handoffs/capx-director-ledger-2026-08.md §0.2).

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (core-infrastructure territory — Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-d7-nyiso-gate — create FRESH off origin/main (git fetch origin main first)
and rebase before pushing; other sessions land to main in parallel.

TASK — RECORDS ONLY, NO SOLVE. Two jobs on frontend/data/forecast/program-status.json:

(1) THE BOARD IS STALE BY ONE LANDED RE-SCORE. It was last touched 2026-08-24 05:55 and still
carries NYISO as FC-1 FAIL / gate (b) fail. The D2-NYISO-INTAKE lane landed 2026-08-25 and the
bare `nyiso-t1f` key in frontend/data/forecast/ff-verdicts.json now carries a re-score:
14/14 invariants PASS, FC-1 PASS (was FAIL['I7']), FC-2 PASS (was CAVEAT), determination
HOLD -> PROMOTE-WITH-CAVEATS, FC-7 CAVEAT (the program-wide DOF-ledger gap) the only caveat left.
Evidence: docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md §0/§4/§7.
NOTE the vintage convention: the FFR-3A-2 measurement is preserved verbatim under
`nyiso-t1f-ffr3a2`, the FF-2D baseline under `nyiso-t1f-ff2d`, and the BARE key carries the live
re-score. Read the bare keys. Quoting a preserved baseline as current state is the exact defect
the capx-D1 refresh corrected board-wide — do not reintroduce it.

(2) APPLY THE OWNER'S SIGNED CARD-A DISPOSITION (A-A, signed 2026-08-25 —
docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md §5): gate leg (c) harmonises to the
NEISO reading for every ISO with no T1-X run. CAISO and NYISO move `na` -> `fail`, and "c" is
added to both ISOs' `closed_on` lists. NEISO's `fail` is unchanged. The basis, in the board's own
NEISO cell: §2.1b(c) requires BOTH FF-3E readiness AND the crossover input gap (FC-4) measured and
reported; an unrun leg is not a measured one. Cite the card in the edited cells.

SO NYISO'S GATE SHOULD READ, AFTER YOUR EDIT: (a) PASS · (b) PASS · (c) fail · (d) none, with
`open: false`. VERIFY that against the criteria rather than asserting it, and if any leg reads
otherwise, say so and STOP on that leg rather than forcing it. NO ISO'S GATE OPENS from this
session: leg (d) is owner authorization and is untouched.

(3) CARRY THIS PROGRAM-WIDE SCORING INSTRUCTION into the board's prose, from
docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md §7: NO BASE-YEAR I7 LEG IS A
CAPACITY-EVOLUTION DEFECT. `evolve_fleet` is skipped when `fleet is None`, so the base year runs
no evolution at all — no adequacy backstop, no retirement screen, no entry. MISO 2026 and CAISO
2026 are base-year legs and grade input data only; neither backstop tuning nor floor relaxation is
ever the answer to one. Also refresh the I7/I12 honest_unfit row: NYISO is no longer a member.

DO NOT re-score any run, do not write forecast-provenance/v1 stamp fields (the board's own
gate_a_provenance note explains why a records refresh must never read as a re-score), and do not
touch any other ISO's determination. If a correction WOULD move a gate outcome beyond the signed
card-A change, STOP and escalate it in the FINDING rather than editing it — the capx-D1 pattern.

MECHANISM MATRIX (rule 28): this session tests no mechanism and must mint NO cell verdict. Flag,
do not edit, any cell whose fc posture your reading contradicts.

GUARDRAILS: no LP, no solve, no registration. NO out-of-training backcast year solved, scored or
registered — the spend freeze is TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY, `complete` = {NEISO, NYISO, PJM}
(rule 22). No measured-outcome feedback (rule 13). Touch NO backcast keeper shard, status/*.js,
calibration-complete.json, offer curve or commitment bridge. No new GitHub Actions workflows, no
CI offloading (private repo, billed minutes). Push per CLAUDE.md Git & Pushing; on HTTP 408 set
`git config http.version HTTP/1.1` and retry before concluding anything about pack size;
mcp__github__push_files is a fine fallback for small text commits. Blob-verify any file >=300
lines after push (rule 27) — program-status.json qualifies.

EXIT: the corrected board + docs/handoffs/FINDING-capx-d7-nyiso-gate-<date>.md recording every
changed field with before/after and its citation, NYISO's four legs re-read against the criteria,
and an explicit statement of what now stands between NYISO and an open gate. Report to the owner.
```

---

## D10 — NYISO T1-X crossover (chartered by card A, A-A) — **LANDED PR #4354; historical record, do not re-run**

```
You are the D10 NYISO T1-X CROSSOVER session of the capacity-expansion (Forecast Finalization)
track, chartered by the owner's signature on card A (A-A, 2026-08-25 —
docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md §5) and recorded in the director's
ledger (docs/handoffs/capx-director-ledger-2026-08.md, lane D10).

DATA PROFILE: nyiso
MODEL ASSIGNMENT: Fable (Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-d10-nyiso-t1x — create FRESH off origin/main (git fetch origin main first)
and rebase before pushing.

WHY THIS EXISTS. NYISO cleared FC-1 on 2026-08-25 and is the first ISO in the program to pass
both §2.1b legs that depend on model quality: (a) PASS on the charter's literal test — the
`complete` marker plus the designated full-span keeper, which is now
`2026-08-25-nyiso-155-hydro-repair` (NOT-YET; the marker/keeper reconciliation is open owner
question Q5 in the director's ledger §3 — you take gate (a) as PASS and do NOT re-read it in
either direction) — and (b) PASS (FC-1 and FC-2 both PASS on the bare `nyiso-t1f` key;
determination PROMOTE-WITH-CAVEATS). D7 landed the signed leg-(c) harmonisation on 2026-08-26,
so leg (c) now reads a measured `fail` awaiting exactly this run, and the owner signed the
reading that an ISO with no T1-X run FAILS it. THIS SESSION CLOSES LEG (c) ON MEASUREMENT: run
NYISO's T1-X crossover so FC-4 is measured and reported rather than absent. NYISO has never had
one — no `nyiso-t1x` key exists in ff-verdicts.json and FC-4 reads n/a in every NYISO verdict.

TASK — build, solve, score and register a NYISO T1-X crossover leg.
- Read docs/handoffs/ffr-3a2-battery-close-2026-08-03.md and
  docs/handoffs/ffr-3a4-miso-t1x-instrument-debt-2026-08-04.md for the crossover harness, its
  invocation and its known instrument debts BEFORE building anything. The PJM and MISO crossover
  legs (`pjm-2023-2027-crossover-ffr3a3-t1x`, `miso-2023-2027-crossover-ffr3a4-t1x`) are the
  worked examples — 2023-2027 window, scored 2023-2025.
- POSTURE: follow the MISO FFR-3A-4 precedent — omit solve-affecting flags so each inherits its
  shipped default, and VERIFY THE POSTURE IN THE RESOLVED CONFIG, not in the request. NYISO's
  FF-2C flip posture is curve-OFF (capacity clearing off; the R5a Option B question is a separate
  standing owner item and this session does not touch it).
- Years sequential within the run. NYISO is not memory-bound (T1-F recorded 2.82 GB peak RSS,
  13.1 min), so it does not contend for a heavy slot — but the ≤2 concurrent heavy cap (rule 12)
  is SHARED with the owner's backcast solves, so check before launching anything large.

SCORING AND REGISTRATION (rule 15): register on the FORECAST namespace via
scripts/register_forecast_run.py with the appropriate `--kind` and a `verdict_key` of `nyiso-t1x`,
and COMMIT the bundle's run_config.json — a bundle without one scores FC-7 FAIL (commit c0562d9;
seven existing legs already carry that debt, lane D8). NEVER the backcast registry. Follow the
preserve-then-overwrite convention for ff-verdicts.json if you touch an existing key; you are
adding a new one, so nothing should be displaced.

REPORT FC-4 HONESTLY, WHATEVER IT SAYS. The crossover measures the backcast->forecast INPUT GAP;
it is diagnostic. For context, the other ISOs' measured CO2 gaps are ERCOT 43-50%, PJM 43-58%,
MISO 63-76%, all outside the 30% band — so a NYISO miss would be consistent with a program-wide
derivation question (lane D5), not a NYISO-specific defect. Do not tune anything to move FC-4, and
do not treat a miss as a reason to withhold registration.

STATE PLAINLY AT THE END whether NYISO's gate leg (c) can now close, and what remains between
NYISO and an open gate (expected: leg (d), owner authorization, which this session does NOT
request and cannot grant).

MECHANISM MATRIX (rule 28): read docs/mechanism-testing-matrix.md §5 NYISO lever queue and
docs/codebase-site/data/mechanism-matrix/NYISO.js. Running an existing instrument on a new ISO
tests no mechanism and should mint no cell verdict; if you arm anything, update ONLY the NYISO
shard, and any new ScenarioConfig field needs its matrix row plus a cell line in EVERY shard in
the same PR (CI enforces this) and must appear in run_config.json (rule 24).

GUARDRAILS: the crossover's 2023-2025 scored window is BACKCAST-tier on the scoring side — score
ONLY against already-committed benchmark artifacts and solve NO year outside the leg's own
2023-2027 definition. NO out-of-training backcast year solved, scored or registered;
the spend freeze is TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY (rule 22). No measured-outcome feedback (rule 13). NYISO's backcast
lane is LIVE and owner-managed (keeper NOT-YET; the nyiso-156 winter-intake legs may run
concurrently in the owner's own sessions) — touch NO backcast keeper shard, status/*.js,
calibration-complete.json, offer curve, commitment bridge, or anything the intake spec names;
your crossover runs at your own fetched HEAD and its FINDING records that HEAD. No new GitHub
Actions workflows, no CI offloading (private repo, billed minutes). Push per CLAUDE.md Git &
Pushing (run payloads over git push; on HTTP 408 set http.version HTTP/1.1 and retry);
blob-verify any >=300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d10-nyiso-t1x-<date>.md with the measured FC-4 at full magnitude,
the registered leg, and the leg-(c) verdict. Report to the owner.
```

---

## D11-R — the D-1 entry volume rule (re-scoped at r#8; supersedes D11) — **LANDED PR #4355; arming RULED Q8 HOLD-until-D12; historical record, do not re-run**

*(The original D11 pro-forma-signal prompt, issued 2026-08-25, was superseded BEFORE FIRST RUN by
the director's refresh-#8 re-scope — ledger §0e.3. The forward-expectation A/B measured trajectory
invariance across three signal constructions and its own adjudication recommended "(b) first —
rest the signal lane and charter D-1's volume rule." The B-C object charter is intact: margin
exhaustion is the allocator half of the developer pro-forma. The signal lane's successor rung —
the scarcity-consistent delta basis — is queued as D12, owner-gated at the finding's §7
escalation.)*

```
You are the D11-R ENTRY VOLUME RULE session of the capacity-expansion (Forecast Finalization)
track. Lane chartered by the owner's card-B signature (B-C, 2026-08-25 —
docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md §5), re-scoped by the director at
refresh #8 on the forward-expectation A/B's evidence (ledger:
docs/handoffs/capx-director-ledger-2026-08.md §0e.3, lane D11-R).

DATA PROFILE: ercot
MODEL ASSIGNMENT: Fable (edits src/market_sim/ — Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-d11r-entry-volume-rule — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

WHY THIS EXISTS — THE EVIDENCE THAT RE-POINTED THIS LANE. Three entry-signal constructions
spanning a ~$200/MWh swing in the entering-2024 mean produce ONE trajectory: terminal RM 25.19 %
(shipped zone-flat), 40.24 % (disarm, raw duals), 40.38 % (forward-expectation composition).
docs/FINDING-entry-signal-forward-expectation-2026-08-25.md §3: once the locational object lets
storage and wind clear at all, volumes are set by QUEUE_CAP_PER_TECH_GW /
STORAGE_ANNUAL_BUILD_CAP_MW and the top-2 share split — a technology clearing by $1 builds its
full cap (new_entry.py:1441, storage.py:1892-1901). "D-1 owns the trajectory; the signal lane
should not be re-chartered against it." Its §7 adjudication recommends exactly this lane.
DO NOT build any signal construction in this session — the shipped default HOLDS
(entry_lookahead_reprice=True, its cell and the entry_forward_expectation_signal cell both stay
as adjudicated), and the pro-forma/scarcity-basis question is a separate owner-gated rung (D12).

THE CONSTRUCTION IS ALREADY NAMED AND PRE-MEASURED — YOU PRODUCTIONIZE IT, YOU DO NOT INVENT IT.
docs/FINDING-entry-signal-l1-2026-08.md §2 (L-1b) measured the MARGIN-EXHAUSTION closure offline
(probe: scripts/probes/entry_signal_l1b_allocator_counterfactual.py): add capacity in tranches
until the screen's own REPRICED margin is exhausted, bounded by the SAME caps. It is the
precommit's named admissible closure, in its own words: "an equilibrium condition the model
already contains — build until the screen's own repriced margin is exhausted — never a tuned
elasticity or damping coefficient" (rule 21 [R-DOF]). Measured offline: terminal RM 18.7 % vs
shipped 25.2 %; ~6.5 pp of the recovery overshoot is bang-bang volume; amplitude lives at the
shoulders (2022: exhaustion supports 1.0 GW where bang-bang built 4.571; 2024: 3 GW vs 6); the
2023 peak is cap-bound under BOTH rules; and the B-2 cobweb SURVIVES (swings −10.5/+1.6/+8.6 pp)
— B-2 is real market dynamics and is NOT your target. If your implementation kills the
oscillation outright, that is a red flag against the implementation, not a success.

READ FIRST: FINDING-entry-signal-l1-2026-08.md (§2 especially), the L-1b probe source,
FINDING-entry-signal-forward-expectation-2026-08-25.md §3/§7, FINDING-entry-screen-t1h-2026-08.md
(the D-1 rows), new_entry.py's allocator and storage.py's winner-take-share split, and
model-methodology-spec.md §5.4/§5.5.

TASK:
1. PHASE 0 — RECONCILE THE PROBE TO THE LIVE ALLOCATOR. Establish exactly what the offline
   counterfactual did (tranche size, repricing step, cap interaction, both screens or thermal
   only) and what the live equivalent must do in new_entry.py AND storage.py (the storage
   allocator has the same defect via the top-2 absolute-margin split). Confirm zero-DOF: every
   quantity in the exhaustion condition must already exist in the screen; if you find yourself
   needing a tranche-size or step-count choice that moves the answer, that is a free parameter —
   STOP and report it (Phase-0 stop is an honourable exit; precedent FINDING-ercot201/208,
   caiso-218/219).
2. IMPLEMENT behind a NEW default-OFF ScenarioConfig field, applying to both the thermal and
   storage allocators (one mechanism, one field — rule 19; do not ship a thermal-only half unless
   Phase 0 shows the storage split is genuinely a different object, and say so if so).
3. A/B on an ERCOT T1-F leg: arm vs control, same HEAD, years sequential. Report at full
   magnitude: per-step build volumes by tech, terminal RM against the four known anchors (shipped
   25.19 / disarm 40.24 / fwd 40.38 / L-1b offline 18.7 %), whether B-2 survives, and the
   secondary L-1b observation (under repricing the second storage slot flips flow_battery ->
   compressed_air — report what your construction does to the storage mix, li-ion included).
   Register BOTH arms on the FORECAST namespace via scripts/register_forecast_run.py with
   run_config.json COMMITTED (FC-7); never the backcast registry (rule 15).

RULE 1 [R-STRUCT] CUTS BOTH WAYS: do not adopt because the RM band improved, do not reject
because one worsened. The question is whether exhaustion-bounded volume is the real allocator
object — a developer builds until the expected margin no longer clears cost, which is why this
re-scope stays inside the B-C charter. ARMING IS THE OWNER'S DECISION: recommend, never arm.

MECHANISM MATRIX (rule 28): read docs/mechanism-testing-matrix.md §5 ERCOT lever queue and
docs/codebase-site/data/mechanism-matrix/ERCOT.js. Your NEW ScenarioConfig field requires its row
in docs/codebase-site/data/mechanism-matrix.js plus a cell line in EVERY ISO shard in the same PR
(CI enforces this), must appear in run_config.json (rule 24), and its ERCOT cell gets your
verdict in THIS session whatever the outcome, rejections included. Do NOT touch the
entry_lookahead_reprice or entry_forward_expectation_signal cells. Rule 25: nothing you derive
crosses an ISO boundary.

GUARDRAILS: forecast-mode 2026+ runs are UNRESTRICTED. NO out-of-training backcast year solved,
scored or registered — the spend freeze is TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY (rule 22). No measured-outcome feedback
(rule 13). DECONFLICTION IS SHARP: ERCOT's backcast lane is ACTIVE this period (check
`git ls-remote --heads origin` at start for in-flight backcast branches) — touch NO backcast
keeper shard, status/*.js, calibration-complete.json, offer curve, commitment bridge,
ORDC/scarcity mechanism or ERCOT backcast matrix cell; if your root cause reaches backcast
territory, STOP at a FINDING and hand back. Check the ≤2-heavy concurrent cap (rule 12) BEFORE
launching solves — it is SHARED with the owner's backcast solves, which start and land without
notice. Years
sequential within a run. No new GitHub Actions workflows, no CI offloading (private repo, billed
minutes). Push per CLAUDE.md Git & Pushing (on HTTP 408 set http.version HTTP/1.1 and retry);
blob-verify any >=300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d11r-entry-volume-rule-<date>.md — the Phase-0 reconciliation
(zero-DOF confirmed or the named free parameter that stopped you), the implementation, the A/B
with the four-anchor terminal-RM comparison and B-2 survival, the matrix cell verdict, and an
explicit arming recommendation that the OWNER decides, not this session. Report to the owner.
```

---

## S-123 — MISO adequacy package (reissued)

```
You are the S-123 MISO ADEQUACY PACKAGE session of the capacity-expansion (Forecast Finalization)
track, chartered by the capacity-expansion director
(ledger: docs/handoffs/capx-director-ledger-2026-08.md, lane S-123).

DATA PROFILE: miso
MODEL ASSIGNMENT: Fable (edits src/market_sim/ — Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-s123-miso-adequacy — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing; MISO's backcast lane lands to main in parallel.

READ FIRST: docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md §2 and §8 (lanes S-1, S-2,
S-3) and §10 recommendation 1. That session reproduced MISO's 2026 I7 leg TO THE MW from the
committed FFR-1C ledger and named three independent, published-source terms. This session
executes all three as a package, because — in the finding's own words — "together they plausibly
account for the whole 6,037 MW base-year gap, and none may be sized against the residual."

THE BASELINE (live record, ff-verdicts.json bare `miso-t1f` key, FFR-3A-2 @ 8ba59281):
I7 2026: accredited firm 135,304 < requirement 141,341 MW (6,037 MW); 2027: 139,147 < 142,806
(3,659 MW). MISO 2026 is a BASE-YEAR leg — evolve_fleet is skipped when fleet is None, so no
capacity mechanism can move it; it grades input data only. Do not propose a backstop or
floor change for it.

S-1 — REQUIREMENT RE-VINTAGE. PLANNING_RESERVE_MARGIN_BY_ISO["MISO"] = 0.179 is cited to the
PY 2024-25 LOLE Study; PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["MISO"] = 1.079/1.157 is
cited to the PY 2025-26 LOLE Study Module E-1, whose own citation block
(capacity_market.py:2635-2637) records "Summer PRM stated both ways: ICAP 15.7%, UCAP 7.9%". The
shipped composite therefore multiplies one planning year's ICAP PRM by the next year's conversion
and equals NEITHER year's published requirement. Re-derive as the same-document PY 2025-26 pair.
Rule 23 [R-FROZEN-DERIVE] basis: THE SOURCE DATA UPDATED (PY 2025-26 publishes both halves) — the
commit must cite the data change, never a residual. EXPECTED EFFECT, STATED IN ADVANCE SO IT
CANNOT BE BACK-FITTED: -2,637.4 MW of requirement at the 2026 peak, 44% of the gap. THE TRAP THE
FINDING NAMES: ship it because the source updated, NOT because of what it closes — and do not
"finish off" the ~3,400 MW residual by tuning S-2 or S-3, which have their own published sources.
This is solve-affecting and shares machinery with the retirement reliability floor, so it needs a
verification re-measure (below) and cannot be a bookkeeping push.

S-2 — EXTERNAL-CAPACITY INTAKE. MISO credits ZERO external firm capacity
(ADEQUACY_EXTERNAL_TIE_FIRM_MW has no MISO entry) while the forecast path floors a 1,400 MW
Manitoba firm-hydro block at 100% in every hour, default-on (MISO_FIRM_IMPORT_DEFAULT_ISOS,
interchange/spec.py). MISO is the second NYISO. Intake MISO's PUBLISHED PRA external-resource /
ZRC accreditation onto the FF-2B construction, exactly as the NYISO lane did — the worked example
is docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md §1/§2 (published operand, converted
to the model's requirement basis with the SAME published factor the requirement side uses, one
basis, rule 19; citation block; tests pinning the rejected bases). NEVER the 1,400 MW dispatch
constant (an inherited ladder constant, not an accreditation) and NEVER an interface/CIL limit —
the CAISO entry explicitly rejects that error. Data intake is UNRESTRICTED (rule 22 channel 1, no
marker, no-LP). HONESTY TEST, DECLARED IN ADVANCE: MISO's published figure is O(10^3) MW against a
6 GW gap — it should close a large MINORITY. A value that happened to close the whole residual is
the SUSPICIOUS one (rule 21); treat that as a red flag on your basis and re-derive.

S-3 — LEDGER DIFFERENCING (solve-free). Difference the model's class ledger against MISO's own
PY 2025-26 PRA / LOLE resource table, the FFR-3P Table-1.1 method that found CAISO's dominant
fork-2 term. Include (a) the LMR/DR documented reconciliation — MISO is absent from
ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO yet counts LMRs as ZRC supply; follow the PJM/NEISO
documented-reconciliation pattern and claim NO number without a citation — and (b) the peak-basis
check (the model's simulated weather-year peak vs MISO's coincident 1-in-2 planning forecast; the
same class of question FFR-3P measured at +3,435 MW for CAISO).

RIDE WITH D9 (the director's sequencing note, finding §2.5): ba_code="SOCO" is superseded in the
keeper's backcast years but LIVE IN THE FORECAST FALLBACK, and SOCO is the counterparty MISO
essentially never exports to (0.1-0.3% of gross). Trace: model/interchange/miso.py:280 ->
import_nodes.py:598-628. It is a rule-14 [R-ACCURATE] item handed to this program by miso-183 and
it bears on the same import accounting; handle it in this session or state why not.

VERIFICATION: after the package lands, re-measure MISO's T1-F leg and re-score FC-1, reporting
each term's contribution separately so none is credited with another's effect. MISO is
MEMORY-BOUND (9.6 GB peak RSS recorded, "no co-run") — run it SOLO and only when a heavy slot is
free; the ≤2 concurrent heavy cap (rule 12) is SHARED with the owner's backcast solves. Years
sequential. Register on the FORECAST namespace via scripts/register_forecast_run.py with
run_config.json COMMITTED (FC-7); never the backcast registry (rule 15).

MECHANISM MATRIX (rule 28): read docs/mechanism-testing-matrix.md §5 MISO lever queue and
docs/codebase-site/data/mechanism-matrix/MISO.js. Registry constants with published citations are
inputs, not mechanisms, and mint no cell verdict; any new ScenarioConfig field needs its matrix
row plus a cell line in EVERY shard in the same PR (CI enforces this) and must appear in
run_config.json (rule 24). Update ONLY the MISO shard.

GUARDRAILS: forecast-mode 2026+ UNRESTRICTED; NO out-of-training backcast year solved, scored or
registered — the spend freeze is TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY, MISO holds NEITHER marker (rule 22). No
measured-outcome feedback (rule 13). DECONFLICTION: miso-190 CONCLUDED 2026-08-30 (arm rejected
on its own prereg kill; keeper miso-188-rvsscope unchanged) but a successor MISO backcast lane
may open at any time — check git ls-remote --heads origin at start, and either way
touch NO backcast keeper shard, status/*.js, calibration-complete.json, offer curve, commitment
bridge or MISO backcast matrix cell. S-1 changes the requirement that ALSO feeds the retirement
reliability floor: if your change reaches backcast-solve behaviour, STOP at a FINDING and hand
back rather than shipping it. No new GitHub Actions workflows, no CI offloading (private repo,
billed minutes). Push per CLAUDE.md Git & Pushing; blob-verify any >=300-line file after push
(rule 27).

EXIT: docs/handoffs/FINDING-capx-s123-miso-adequacy-<date>.md — the three terms with their
citations and per-term contributions, the D9 disposition, the re-scored I7 (or an explicit
statement of the residual at full magnitude), and any term that had to be routed rather than
shipped. Report to the owner.
```

---

## S-4 — NEISO hydro accreditation intake (reissued)

```
You are the S-4 NEISO HYDRO ACCREDITATION session of the capacity-expansion (Forecast
Finalization) track, chartered by the capacity-expansion director
(ledger: docs/handoffs/capx-director-ledger-2026-08.md, lane S-4).

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (edits src/market_sim/config — Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-s4-neiso-hydro — create FRESH off origin/main (git fetch origin main first)
and rebase before pushing.

WHY THIS EXISTS. docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md §4.3 measured that NEISO's
hydro credit is LOAD-BEARING AND DECIDES ITS VERDICT'S SIGN. HYDRO_ACCREDITATION_CREDIT_BY_ISO has
no NEISO entry — deliberately: FFR-1C located no ISO-published NEISO hydro class factor (ISO-NE
qualifies hydro per-resource at Seasonal Claimed Capability) and fell back to the generic
RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50 rather than borrow a foreign ISO's factor (rule 25).
That was correct then and FFR-1C filed it as an open item
(docs/handoffs/ffr-1c-hydro-accreditation-2026-07-31.md). What is new is the measurement: the
fallback contributes 949.75 MW (1,899.5 MW nameplate x 0.50) against a 218 MW gap — 4.4x. A class
factor of 0.39 would flip 2027 to FAIL; 0.62 would clear 2028 outright. NEISO'S 2028 I7 VERDICT IS
NOT DECIDABLE AT THE CURRENT INPUT FIDELITY, and until this lands it must be read as "within input
uncertainty", never as a capacity-evolution defect.

TASK — replace the generic fallback with a NEISO-specific class factor derived from ISO-NE's own
published per-resource qualified capacity.
- SOURCE: ISO-NE per-resource Seasonal Claimed Capability / qualified capacity for the hydro
  fleet, aggregated to a class factor against the same nameplate basis the model uses
  (1,899.5 MW; the FFR-1C doc's NEISO table). Check data/raw/ for what is already on disk and its
  README/SHA256SUMS provenance record before re-fetching; corpus payloads are gitignored and the
  README carries the verified re-fetch URL (CLAUDE.md, cloning & session data).
- BASIS DISCIPLINE: aggregate on the model's own nameplate denominator so the factor and the fleet
  it multiplies are the same population; ISO-NE's intermittent-hydro median-output construction is
  the documented complication — state how you handled it. One basis, cited, zero free parameters
  (rules 5, 13, 19). If ISO-NE's published construction genuinely cannot be mapped to a class
  factor, SHIP NOTHING and report that — the generic 0.50 with a measured load-bearing warning is
  more honest than a fabricated NEISO-specific number.
- DECLARE THE DIRECTION BEFORE YOU LOOK: state, before computing, that a factor below ~0.39 flips
  2027 to FAIL and above ~0.62 clears 2028, so that whatever you find cannot be read as chosen.
  You are fixing an input, not steering a verdict (rule 13, rule 21).
- Refresh the FCA vintage in the same session if ISO-NE has published a newer one (rule 23: on
  publication, not on a residual). §4.4 notes NEISO's requirement inputs are same-document FCA-17
  and that CCP 2026/27 values are currently held for 2028.

VERIFICATION: re-measure NEISO's T1-F leg and re-score FC-1, reporting the 2026/2027/2028 I7
position at full magnitude in whichever direction it moves. NEISO is cheap (T1-F recorded 9.2 min)
and not memory-bound, so it does not contend for a heavy slot. Years sequential. Register on the
FORECAST namespace via scripts/register_forecast_run.py with run_config.json COMMITTED (FC-7);
never the backcast registry (rule 15).

MECHANISM MATRIX (rule 28): read docs/mechanism-testing-matrix.md §5 NEISO lever queue and
docs/codebase-site/data/mechanism-matrix/NEISO.js. A registry constant with a published citation
is an input, not a mechanism, and mints no cell verdict; a new ScenarioConfig field would need its
matrix row plus a cell line in EVERY shard in the same PR (CI enforces) and must appear in
run_config.json (rule 24). Update ONLY the NEISO shard. Rule 25: derive NEISO's factor from
NEISO's own published record — never transfer another ISO's.

GUARDRAILS: forecast-mode 2026+ UNRESTRICTED; data intake unrestricted and no-LP. NO
out-of-training backcast year solved, scored or registered by this lane — the spend freeze is
TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022
governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches
neither), `final` EMPTY (rule 22). No measured-outcome feedback (rule 13). NEISO's backcast lane is CALIBRATED and holds a
`complete` marker — touch NO backcast keeper shard, status/*.js, calibration-complete.json, offer
curve or commitment bridge. No new GitHub Actions workflows, no CI offloading (private repo,
billed minutes). Push per CLAUDE.md Git & Pushing; blob-verify any >=300-line file after push
(rule 27).

EXIT: docs/handoffs/FINDING-capx-s4-neiso-hydro-<date>.md — the sourced class factor with its
primary citation (or the explicit could-not-source verdict), the pre-declared direction statement,
the re-scored I7 for 2026-2028, and a clear answer to whether NEISO's 2028 leg is now decidable.
Report to the owner.
```

---

## Q5-W — NYISO marker withdrawal (r#12; governance RECORDS lane) — **LANDED PR #4343; historical record, do not re-run**

```
You are the Q5-W NYISO MARKER WITHDRAWAL records session, executing an owner ruling delivered
2026-08-30 at the capacity-expansion director's refresh-#12 decision card (recorded:
docs/handoffs/capx-director-ledger-2026-08.md §0i and §3 Q5). RECORDS ONLY — no solve, no
re-score, no keeper change.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable or Opus (governance records — NEVER Sonnet, rule 27 posture).
BRANCH: claude/q5w-nyiso-marker-withdrawal — create FRESH off origin/main (git fetch origin
main first) and rebase before pushing. DECONFLICTION: the capx S-4V lane may land a
NEISO-block edit to frontend/data/forecast/program-status.json concurrently — edit ONLY your
own blocks and rebase before pushing.

THE RULING (the option selected on the director's card, verbatim label: "Withdraw the marker
(CAISO precedent)"): apply the 2026-08-06 CAISO precedent uniformly — a `complete` marker
cannot stand on a NOT-YET keeper. NYISO's marker withdraws; re-entry is a NEW explicit owner
declaration once NYISO's designated keeper again scores CALIBRATED (expected route: the
nyiso-156 winter intake Leg 2 + the C3c standing rule, per the marker's own successor note).
This resolves ledger Q5: the reconciliation is now WRITTEN AND UNIFORM — the
structural-integrity formula remains the standard for KEEPER promotions (nyiso-155 and
nyiso-157 stand untouched as keepers) but no longer sustains a `complete` marker on a NOT-YET
determination.

READ FIRST:
- frontend/data/backcast/calibration-complete.json — NYISO's entry as it stands (keeper
  2026-08-30-nyiso-157-par-attribution; determination NOT-YET on C3a/C3b/C3c, D-5(b)
  re-verified 2026-08-30; keeper_at_declaration preserved).
- The CAISO withdrawal precedent's recorded form (2026-08-06): docs/governance/rule-history.md
  §4 and whatever the marker file/docs retained of that withdrawal — MIRROR its form.
- docs/handoffs/capx-director-ledger-2026-08.md §3 (Q5's full genealogy, r#8 WAIT → r#12
  WITHDRAW).
- CLAUDE.md rule 22 (the `complete` block's role: validation-tier authorization).

TASK:
1. WITHDRAW NYISO from the `complete` block of
   frontend/data/backcast/calibration-complete.json, following the CAISO precedent's own
   recorded form. Absence must NOT be self-explaining: record — in the file's convention if
   it carries withdrawal notes, else in the FINDING and the governance docs the precedent
   used — WHY (the ruling + its verbatim basis), the date, the provenance (capx director
   r#12 decision card), the keeper + determination it stood on at withdrawal, what happens
   to the prior declaration record (preserve keeper_at_declaration history, never erase it),
   and the explicit re-entry condition (new owner declaration on a CALIBRATED keeper).
2. STATE THE VALIDATION-TIER CONSEQUENCE in the record: NYISO's 2020-2022 touchpoint
   authorization lapses with the marker (rule 22: `complete` marker + --holdout-authorized
   govern validation spends; the tier-scoped freeze itself is UNTOUCHED — do not edit
   holdout-freeze.json). Verify from the committed registry sidecars whether any NYISO
   out-of-training year was ever solved/registered (none is expected) and state what you
   find; report any surprise, do not adjudicate it.
3. FLIP THE FORECAST BOARD IN THE SAME SESSION (so the two surfaces cannot disagree): NYISO
   gate leg (a) in frontend/data/forecast/program-status.json moves PASS → fail on the
   marker, citing the ruling. Leg (b) is UNTOUCHED (it is the bare nyiso-t1f verdict,
   PROMOTE-WITH-CAVEATS — no marker moves a bare verdict); legs (c)/(d) untouched. Update
   any board prose that names NYISO's marker or its (a)+(b) lead position. This is a records
   flip with a citation, never a re-score — do not write forecast-provenance stamp fields
   (the D7 discipline).
4. CHECK WHAT RENDERS the marker (backcast dashboard/status surfaces that bake
   calibration-complete.json) and rebuild exactly what the CAISO withdrawal precedent
   rebuilt — nothing more.
5. RUN scripts/audit_keepers.py and report it clean (M1 has no NYISO `complete` entry to
   verify once absent; nothing else should move).
6. FINDING: docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md — the ruling verbatim
   with its card provenance, before/after of every changed field on both surfaces, the
   written reconciliation statement, the re-entry condition, the validation-tier
   consequence, and the audit result.

DO NOT TOUCH: frontend/data/backcast/keepers/<ISO>.json (nyiso-157 REMAINS the keeper — the
ruling moves the marker, not the keeper), any run registry/bundle, ff-verdicts.json, any
mechanism-matrix shard, holdout-freeze.json, any other ISO's marker entry ({NEISO, PJM}
stand), and no solve of any kind. If executing the withdrawal surfaces a question this
prompt does not answer (e.g. the file's schema forces a choice the CAISO precedent does not
cover), STOP and route it back to the director rather than improvising governance state.

GUARDRAILS: records only — no LP, no solve, no registration, no out-of-training year
touched in any way. No new GitHub Actions workflows, no CI offloading (private repo, billed
minutes). Push per CLAUDE.md Git & Pushing (on HTTP 408 set `git config http.version
HTTP/1.1` and retry before concluding anything about pack size); blob-verify any >=300-line
file after push (rule 27) — calibration-complete.json and program-status.json both qualify.

EXIT: the withdrawal landed on both surfaces + the FINDING + audit_keepers clean + a
one-line statement of what NYISO's gate now reads (expected: (a) fail on marker · (b) PASS ·
(c) fail · (d) none) and what re-entry requires. Report to the owner.
```

---

## S-4V — NEISO verification (r#11; completes S-4's owed §5) — **LANDED PRs #4337/#4353; historical record, do not re-run**

```
You are the S-4V NEISO VERIFICATION session of the capacity-expansion (Forecast Finalization)
track, chartered by the capacity-expansion director (ledger:
docs/handoffs/capx-director-ledger-2026-08.md, lane S-4V — the verification half S-4's charter
owed).

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-s4v-neiso-verification — create FRESH off origin/main (git fetch origin
main first) and rebase before pushing.

WHY THIS EXISTS. S-4 landed 2026-08-30 (PR #4312):
HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"] = 1_396.472 / 1_899.5 (= 0.7352) — ISO-NE's own
per-resource August 2026 summer SCC aggregate over the 244-asset active conventional-hydro
fleet, divided by the model's own accreditation basis; zero free parameters, direction
pre-declared before computation. But the session ended before its verification pair ran:
docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md §5 reads TBD, headline items 2/3 read
TBD, §8's chartered question ("is NEISO's 2028 I7 leg now decidable?") is unanswered, and the
forecast namespace is byte-unchanged since 2026-08-26 — the board still shows NEISO FC-1 FAIL
on the generic 0.50 the shipped factor replaced. You complete S-4's §5. Read the S-4 finding
in full first, plus the worked example for the whole flow:
docs/handoffs/FINDING-capx-d2-nyiso-extcap-2026-08-25.md §4 (re-score + honest decomposition)
and its registration mechanics.

PRE-DECLARED EXPECTATION — write it into the finding BEFORE running anything, then run (rules
13/21; S-4's own §2 is the model case). From D2-B's committed arithmetic
(FINDING-capx-d2b-i7-ledger-2026-08-25.md §4.3): the credited hydro term moves 949.75 →
1,396.5 MW (+446.7 MW) against a 218 MW 2028 gap, so I7-2028 is expected to clear by
≈ +229 MW ON THE D2-B LEDGER BASIS; 2026/2027 already passed and should stay passing. HEAD has
moved since the FFR-3A-2 epoch, so decompose the measured delta honestly against this
prediction — the NYISO extcap lane's demand-drift disclosure (−341.4 MW, its finding §4) is
the pattern. If the measurement CONTRADICTS the expectation (2028 does not clear, or the hydro
term's isolated delta is not ≈ +446.7 MW), that is the headline, reported at full magnitude —
and the factor is NOT touched: it is sourced (rule 14), so a surprise is a discovered
attribution question, never a reason to revert.

TASK:
1. CONTROL/TREATMENT PAIR at ONE HEAD, years sequential within each run:
   - TREATMENT: scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030,
     HEAD defaults (the shipped factor is in the default construction — no flag involved).
   - CONTROL: identical invocation with the one NEISO registry entry locally reverted (remove
     the "NEISO" key so resolve_hydro_capacity_credit falls back to the generic 0.50) — an
     UNCOMMITTED diagnostic arm for attribution only, never a shippable configuration; label
     it control everywhere and state in the finding exactly what the reversion was.
   NEISO is light (T1-F recorded 9.2 min, not memory-bound) — but check
   `git ls-remote --heads origin` for in-flight backcast branches and the ≤2-heavy concurrent
   cap (rule 12) before launching; the cap is SHARED with the owner's backcast solves, which
   start and land without notice.
2. RE-SCORE FC-1 from the pair: the 2026/2027/2028 I7 rows at full magnitude in BOTH arms,
   the hydro-term delta isolated (an evolution ledger's exits live in BOTH `retirements` and
   `confirmed_derates` — sum both), FC-2/I12 re-read, and the determination the re-score
   produces, whatever it is.
3. REGISTER on the FORECAST namespace via scripts/register_forecast_run.py (rule 15; NEVER
   the backcast registry), run_config.json COMMITTED for both bundles (FC-7):
   - the TREATMENT as the live leg, verdict_key `neiso-t1f`, following the
     preserve-then-overwrite convention exactly as the NYISO extcap lane did: first preserve
     the current bare content under the epoch-suffixed key its provenance names (the NYISO
     precedent used `-ffr3a2`), then write the re-score to the bare key. The `-ff2d` baseline
     is untouched.
   - the CONTROL as a labelled diagnostic leg under its own suffixed key (e.g.
     `neiso-t1f-s4control`), so the pair is on the record.
4. COMPLETE THE FINDING IN PLACE: fill §5, headline items 2/3, and §8 of
   FINDING-capx-s4-neiso-hydro-2026-08-30.md with the measured results, as a dated
   verification-session addendum naming this session — do not rewrite S-4's own record.
5. BOARD REFRESH (D7-class records discipline, delegated by the director): update the NEISO
   block of frontend/data/forecast/program-status.json to the measured post-verification
   state — fc rows, blocking_rows, t1f_determination — citing the finding and the bare-key
   verdict. Re-read NEISO's four §2.1b gate legs against the criteria rather than asserting
   them; if leg (b) flips on the measured determination, say so plainly (NEISO would be the
   program's second (a)+(b)-PASS ISO). Leg (d) is owner authorization — untouched. NO other
   ISO's block is edited; if anything beyond NEISO's own measured state seems to need
   editing, STOP and route it to the director instead.
6. MECHANISM MATRIX (rule 28): re-stamp the existing `hydro_accreditation` row's NEISO cell
   (O since FFR-1C) from this verification pair, per S-4's own §4 commitment — NEISO shard
   ONLY (docs/codebase-site/data/mechanism-matrix/NEISO.js), evidence citation to the
   finding. A registry constant is an input, not a mechanism — no new row, no other cell,
   no other shard.

OUT OF SCOPE: the ARA requirement re-vintage (≈ +380 MW, S-4 finding §6) is lane S-4b,
chartered separately AFTER you land — do not adopt it here, even partially, and do not "pair"
it with your re-score. The FCA-vintage NO-SWAP stands as S-4 closed it.

GUARDRAILS: forecast-mode 2026+ runs are UNRESTRICTED. NO out-of-training backcast year
solved, scored or registered — the spend freeze is TIER-SCOPED since 2026-08-26 (locked test
2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker +
--holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY (rule 22).
No measured-outcome feedback (rule 13): the pair attributes a shipped input's effect —
nothing is tuned to a residual, and no value is reverse-engineered to clear an invariant
(rule 21). NEISO's backcast lane is CALIBRATED and holds a `complete` marker — touch NO
backcast keeper shard, status/*.js, calibration-complete.json, offer curve or commitment
bridge. No new GitHub Actions workflows, no CI offloading (private repo, billed minutes).
Push per CLAUDE.md Git & Pushing (run payloads over git push; on HTTP 408 set
`git config http.version HTTP/1.1` and retry before concluding anything about pack size);
blob-verify any >=300-line file after push (rule 27) — program-status.json and the finding
both qualify.

EXIT: the completed finding (§5/§8 and headline TBDs filled), both legs registered with
run_config.json committed, the refreshed NEISO board block, the re-stamped NEISO matrix
cell, and a plain statement of (a) whether NEISO's 2028 I7 leg is now decidable and what it
reads, (b) what NEISO's §2.1b gate reads after this lands, and (c) that S-4b is now
charterable. Report to the owner.
```

---

## S-5 — PJM requirement horizon-edge (unblocked by card C, C-A) — **LANDED PR #4340; historical record, do not re-run**

```
You are the S-5 PJM REQUIREMENT HORIZON-EDGE session of the capacity-expansion (Forecast
Finalization) track, chartered by the owner's signature on card C (C-A, 2026-08-25 —
docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md §5) and recorded in the director's
ledger (docs/handoffs/capx-director-ledger-2026-08.md, lane S-5).

DATA PROFILE: pjm
MODEL ASSIGNMENT: Fable (edits src/market_sim/ and scoring machinery — Opus or Fable, NEVER
Sonnet, rule 27).
BRANCH: claude/capx-s5-pjm-horizon-edge — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

THE CONVENTION IS ALREADY DECIDED — THIS SESSION IMPLEMENTS IT, IT DOES NOT RE-LITIGATE IT. The
owner signed C-A: HOLD-LAST-FPR is the declared convention beyond the last published FPR table.
Evidence: docs/handoffs/FINDING-capx-d2b-i7-ledger-2026-08-25.md §5.2.
FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"] ends at delivery year 2028/29 and
resolve_forecast_pool_requirement returns None beyond it, so the model falls back to a composite
whose IRM half is two vintages stale. Crossing 2028->2029 the bar DROPS 3.18% of peak — 5,492 MW
at the 2030 peak — while PJM's own published series RISES (2027/28 IRM 20.0%; FPR 0.9170 ->
0.9260 -> 0.9401). Precedent for hold-last is already in the repo: forward_net_cone_anchor
establishes exactly this convention for the demand curve's forward values.

EXPECT THE RESULT TO BE WORSE, AND REPORT IT AT FULL MAGNITUDE. PJM's reported I7 miss should
restate from 366 MW to ~5.9 GW at 2030, and 2029 plausibly joins it as a failing year. That is the
point of the signature: the 366 MW was an artifact of grading the horizon edge against the weakest
available construction, and every correction available on either side runs against leniency (the
supply side too — the external tie 1,281.7 MW is 2026/27 BRA cleared UCAP held static against a
published 2027/28 figure of 1,005.9 MW). DO NOT soften, hedge, or offset this; a lane that
"improves" PJM's number has done the wrong thing.

TASK, IN THREE PARTS:
1. IMPLEMENT hold-last-FPR as a DECLARED, DOCUMENTED convention in
   resolve_forecast_pool_requirement (and anywhere else the beyond-table fallback is reached),
   with a citation comment naming the forward_net_cone_anchor precedent and the card C signature.
   It must be explicit and greppable — not an incidental change of a default (rule 5, rule 24).
   Check whether other ISOs reach the same beyond-table edge; the discontinuity is crossed by
   every T1-F leg that reaches 2029, so state the cross-ISO scope of your change even if you scope
   the change itself to PJM.
2. BUNDLE THE D-1 CHECKER REPAIR, routed to the director by both D2 findings: the invariant checker
   drops the `year` argument on PJM's published-FPR path, so for 2026-2028 the MODEL builds to the
   published FPR while the CHECKER grades against the lower fallback. It is INERT for the 2030 leg
   (no published FPR there, both sides use the fallback) but live for 2026-2028. Same machinery,
   same round.
3. RE-SCORE PJM's T1-F leg and report the restated I7/I12 position per year.

THIS IS A SCORER/GOVERNANCE ROUND: it changes an FC-1 verdict. Say so plainly in the FINDING, keep
the before/after verdicts side by side, and do not quietly absorb the change into a board refresh
— the board update is the director's D7-class work, and your FINDING is its input.

RULE 23 [R-FROZEN-DERIVE]: intake PJM's 2029/30 planning parameters ON PUBLICATION, never against
a residual. If PJM has posted them, take them and say so; if not, hold-last stands and say that
too.

SEQUENCING, BINDING: S-6 (the PJM T1-F ledger run that makes PJM's supply side observable — the
one leg no committed artifact can reproduce) runs STRICTLY AFTER this session, so it measures
against the corrected bar. PJM is memory-bound (8.8 GB peak RSS, "no co-run", 19.0 min cold /
3.8 min per solve-year). Do NOT launch S-6 here. If you re-score with a solve, run it SOLO and
only when a heavy slot is free — the ≤2 concurrent heavy cap (rule 12) is SHARED with the owner's
backcast solves. Years sequential. Register on the FORECAST namespace via
scripts/register_forecast_run.py with run_config.json COMMITTED (FC-7); never the backcast
registry (rule 15).

MECHANISM MATRIX (rule 28): read docs/mechanism-testing-matrix.md §5 PJM lever queue and
docs/codebase-site/data/mechanism-matrix/PJM.js. A declared requirement convention is scoring
machinery, not a market mechanism, and should mint no cell verdict; if you add a ScenarioConfig
field it needs its matrix row plus a cell line in EVERY shard in the same PR (CI enforces this)
and must appear in run_config.json (rule 24). Update ONLY the PJM shard.

GUARDRAILS: forecast-mode 2026+ UNRESTRICTED. NO out-of-training backcast year solved, scored or
registered — the spend freeze is TIER-SCOPED since 2026-08-26 (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 governed by the `complete` marker + --holdout-authorized alone — a lane of THIS track touches neither), `final` EMPTY (rule 22). No measured-outcome feedback (rule 13). PJM's
backcast lane is CALIBRATED and holds a `complete` marker — touch NO backcast keeper shard,
status/*.js, calibration-complete.json, offer curve or commitment bridge. Verify your change
cannot reach the backcast path (the calibration backcast solves every year as its own base year
and never runs evolve_fleet — the NYISO extcap finding §6 states the argument; reproduce it for
this change rather than assuming it). No new GitHub Actions workflows, no CI offloading (private
repo, billed minutes). Push per CLAUDE.md Git & Pushing; blob-verify any >=300-line file after
push (rule 27).

EXIT: docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-<date>.md — the implemented convention with
its citation, the D-1 repair, the restated per-year I7/I12 at full magnitude, the cross-ISO scope
statement, and explicit confirmation that S-6 is now unblocked. Report to the owner.
```

---

## D13 — board reconcile (r#13) — **LANDED PR #4372; historical record, do not re-run**

```
You are the D13 BOARD RECONCILE session of the capacity-expansion (Forecast Finalization) track,
chartered at director refresh #13 (docs/handoffs/capx-director-ledger-2026-08.md §0j, lane D13).
This is a RECORDS lane: zero solves, zero re-scores. You edit the forecast board and the
decision-card record so they describe the state that already exists in committed artifacts.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable or Opus (never Sonnet, rule 27).
BRANCH: claude/capx-d13-board-reconcile — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

READ FIRST: frontend/data/forecast/program-status.json (the board you are editing);
frontend/data/forecast/ff-verdicts.json (bare keys only — suffixed keys are preserved
baselines); docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md §0/§3;
docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md §3.3/§4/§5;
docs/handoffs/FINDING-capx-d10-nyiso-t1x-2026-08-30.md; the ledger §0j.3 (the Q7/Q8 rulings);
docs/forecast-development-plan-2026-07.md §2.1b(2)(c) (the leg-(c) charter text);
docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md §1.2/§5 (card A-A as signed).

FIVE EDITS, ALL RECORDS, NOTHING ELSE:
1. EXECUTE Q7 (owner ruling, r#13 sitting, 2026-08-30: "Measured closes the leg"). Gate leg (c)
   for ERCOT, PJM and MISO moves fail → pass: each has a measured, registered FC-4
   (ercot-t1x / pjm-2023-2027-crossover-ffr3a3-t1x / miso-2023-2027-crossover-ffr3a4-t1x) and a
   green readiness battery, which is the charter-literal §2.1b(c) test and the card A-A reading
   ("leg (c) closes on a measured FC-4 rather than on an unscored cell"). In each cell state the
   FC-4 FAIL magnitudes AT FULL MAGNITUDE and that the leg passes on measurement, not on the
   verdict; cite the Q7 ruling (ledger §0j.3/§3) + charter §2.1b(c) + card A-A. NEISO's leg (c)
   stays fail (genuinely unrun — no neiso-t1x key; lane D14 is chartered to close it). NYISO's
   PASS stands. Also CORRECT the NYISO leg-(c) cell's claim that the other measured ISOs
   "read pass" — false when written, true after your edit; annotate rather than silently rewrite.
2. APPLY the S-5 restatement to the PJM block (its finding is the director's D7-class input):
   leg (b) and blocking_rows currently say the 2030 I7 miss is 366 MW; restate to 5,858 MW
   (3.39% of peak) under the signed hold-last-FPR convention (card C-A), with 2029 plausibly
   joining (flagged as inference — S-6 measures it) and the 2026-2028 checker bars rising
   0.96/1.83/3.18 pp of peak. Cite FINDING-capx-s5 §3. The leg-(b) STATUS does not move (fail
   before, fail after).
3. STAMP D11-R currency on the ERCOT block: entry_margin_exhaustion measured (live arm terminal
   RM 22.02% vs shipped 25.19, B-2 survives, gas half inert on the live reserve leg), matrix
   cell O, and the Q8 ruling: arming HELD until D12 adjudicates the scarcity basis (finding §5
   recommendation, adopted by the owner 2026-08-30). Do NOT touch any FC verdict or flip_config.
4. REPAIR the stale top-level prose (headline + gate_reading), which currently contradicts the
   board's own per-ISO blocks: it still says no ISO holds (a)+(b) both (FALSE — NEISO does,
   since S-4V), that leg (b) passes only for NYISO (FALSE — bare neiso-t1f is
   PROMOTE-WITH-CAVEATS), and that leg (c) fails for all six (superseded by D10 + Q7). Rewrite
   those passages to the live state: NEISO (a) PASS · (b) PASS · (c) fail (unrun; D14 chartered)
   · (d) none — the program lead; NYISO (a) fail on the withdrawn marker · (b) PASS · (c) PASS ·
   (d) none; leg (c) after Q7 fails ONLY where no T1-X exists (NEISO, CAISO). Preserve the
   honest-accounting tone: no ISO clears the full gate; leg (d) is none everywhere; nothing in
   this session opens a gate.
5. APPEND the Q7/Q8/Q9 rulings to docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md
   as a dated §6 addendum (question, options presented, ruling verbatim from the ledger §0j.3,
   consequences, execution lane), so the signature record stays one document.

GUARDRAILS: you re-score NOTHING — every number you write must already exist in a committed
FINDING or verdict record; cite it in place. Only the three ruled leg-(c) cells change status;
no gate opens (verify and state this). Touch NO backcast surface (keepers, status/*.js,
calibration-complete.json), no ff-verdicts.json content (provenance prose in
program-status.json sources is fine), no src/, no ScenarioConfig. NO out-of-training backcast
year solved, scored or registered; freeze is TIER-SCOPED (locked test frozen for every ISO;
validation by `complete` marker + --holdout-authorized — you touch neither). No new GitHub
Actions workflows. Push per CLAUDE.md Git & Pushing; program-status.json is >300 lines-scale —
blob-verify after push (rule 27).

EXIT: docs/FINDING-capx-d13-board-reconcile-<date>.md with the per-cell before/after (the Q5-W
finding is the format model), the no-gate-opened verification, and the corrected D10-cell
annotation. Report to the owner.
```

---

## D14 — NEISO T1-X crossover (r#13) — **LANDED PR #4376; historical record, do not re-run**

```
You are the D14 NEISO T1-X CROSSOVER session of the capacity-expansion (Forecast Finalization)
track, chartered at director refresh #13 (docs/handoffs/capx-director-ledger-2026-08.md §0j,
lane D14) under the owner's Q7 ruling (leg (c) closes on a measured FC-4 — the card A-A reading
made uniform, 2026-08-30).

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (Opus or Fable, NEVER Sonnet, rule 27).
BRANCH: claude/capx-d14-neiso-t1x — create FRESH off origin/main (git fetch origin main first)
and rebase before pushing.

WHY THIS EXISTS. NEISO is the program's lead ISO since S-4V (2026-08-30): (a) PASS (`complete`
member; CALIBRATED full-span keeper 2026-08-17-neiso-99-joint-p1) · (b) PASS
(PROMOTE-WITH-CAVEATS on the bare `neiso-t1f` key, re-scored by the S-4V verification pair) ·
(c) fail — NEISO has NEVER had a T1-X: no `neiso-t1x` key exists and FC-4 reads n/a in every
NEISO verdict · (d) none. THIS SESSION CLOSES LEG (c) ON MEASUREMENT. If it lands, NEISO
becomes the FIRST ISO in program history with legs (a)+(b)+(c) all satisfied — leaving only
leg (d), the explicit owner authorization, which this session does NOT request and cannot grant.

TASK — build, solve, score and register a NEISO T1-X crossover leg.
- Read docs/handoffs/ffr-3a2-battery-close-2026-08-03.md and
  docs/handoffs/ffr-3a4-miso-t1x-instrument-debt-2026-08-04.md for the crossover harness and its
  known instrument debts BEFORE building anything;
  docs/handoffs/FINDING-capx-d10-nyiso-t1x-2026-08-30.md is the direct worked example (D10 built
  NYISO's from the same precedents: 2023-2027 window, scored 2023-2025, vintage 2023).
- POSTURE: follow the FFR-3A-4/D10 precedent — omit solve-affecting flags so each inherits its
  shipped default, and VERIFY THE POSTURE IN THE RESOLVED CONFIG, not in the request. NEISO's
  FF-2C flip posture is curve-ON (capacity clearing ON). The shipped HEAD carries S-4's sourced
  hydro accreditation factor (0.7352) — that is the default, not a flag; confirm it resolves.
- Years sequential within the run (rule 12). NEISO is light (4 zones + HQ import node; T1-F
  class runtimes) — it does not contend for a heavy slot, but the ≤2 concurrent heavy cap is
  SHARED with the owner's backcast solves (a MISO heavy solve is running as of charter), so
  check before launching anything large.
- COVERAGE HONESTY: benchmark coverage for 2025 fuel volumes may be partial (D10 hit the
  preliminary EIA-923 vintage; NEISO may differ) — report uncovered rows as uncovered, never
  proxy them in.

SCORING AND REGISTRATION (rule 15): register on the FORECAST namespace via
scripts/register_forecast_run.py with the appropriate --kind and verdict_key `neiso-t1x`, and
COMMIT the bundle's run_config.json — a bundle without one scores FC-7 FAIL. NEVER the backcast
registry. You are adding a NEW key — nothing is displaced; preserve-then-overwrite applies only
if you touch an existing key (you should not).

REPORT FC-4 HONESTLY, WHATEVER IT SAYS — the crossover measures the backcast→forecast INPUT
GAP; it is diagnostic, and the leg closes on MEASUREMENT (Q7), not on a pass. Context: measured
co2 gaps are ERCOT 43-50%, PJM 43-58%, MISO 63-76%, while NYISO measured ~10% and does NOT
reproduce the program-wide miss — wherever NEISO lands is evidence for lane D5, not a NEISO
verdict. Do not tune anything to move FC-4, and do not withhold registration on a miss.

BOARD + GATE STATEMENT: refresh the NEISO block of frontend/data/forecast/program-status.json
(leg (c) + t1x fields + blocking rows) with your measured record — fetch and rebase first; lane
D13 (board reconcile) may merge around you, and if it has, keep its Q7 harmonisation intact.
STATE PLAINLY at the end whether NEISO now holds (a)+(b)+(c), and that leg (d) remains.

MECHANISM MATRIX (rule 28): running an existing instrument on a new ISO tests no mechanism —
mint no cell verdict. If you arm anything, update ONLY the NEISO shard
(docs/codebase-site/data/mechanism-matrix/NEISO.js) in this session; a new ScenarioConfig field
needs its matrix row plus a cell line in EVERY shard in the same PR, and must appear in
run_config.json (rule 24).

GUARDRAILS: the crossover's 2023-2025 scored window is BACKCAST-tier on the scoring side —
score ONLY against already-committed benchmark artifacts and solve NO year outside the leg's
own 2023-2027 definition. NO out-of-training backcast year solved, scored or registered; the
freeze is TIER-SCOPED (locked test 2019/H1-2026 frozen for every ISO; validation 2020-2022 by
`complete` marker + --holdout-authorized — this lane touches neither). No measured-outcome
feedback (rule 13); nothing reverse-engineered to clear an invariant (rule 21). The ≥2026 half
of the window is forecast-mode by construction — verify the quarantine row (no H1-2026 actual
read) and report it. Touch NO backcast keeper shard, status/*.js, calibration-complete.json,
offer curve or commitment bridge. S-4b (the ARA requirement re-vintage) dispatches strictly
AFTER this lane merges — do not take its scope. No new GitHub Actions workflows, no CI
offloading. Push per CLAUDE.md Git & Pushing (run payloads over git push; on HTTP 408 set
http.version HTTP/1.1 and retry); blob-verify any ≥300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d14-neiso-t1x-<date>.md with the measured FC-4 at full
magnitude, the registered leg, the board refresh, and the (a)+(b)+(c) statement. Report to the
owner.
```

---

## D12 — scarcity-consistent delta basis (r#13) — **LANDED PR #4373; Q10 ruled confirm-pair-then-arm (see D12-C); historical record, do not re-run**

```
You are the D12 SCARCITY-CONSISTENT DELTA BASIS session of the capacity-expansion (Forecast
Finalization) track, chartered at director refresh #13 under the owner-ratified sequencing
(r#8 sitting: D12 strictly after D11-R reports — it has,
docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md) and named as the successor by
docs/FINDING-entry-signal-forward-expectation-2026-08-25.md §4. Your report is the INPUT to the
owner's held arming decision (Q8, r#13 sitting: entry_margin_exhaustion arming HELD until this
lane adjudicates the scarcity basis).

DATA PROFILE: ercot
MODEL ASSIGNMENT: Fable (rule 27).
BRANCH: claude/capx-d12-scarcity-basis — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

THE OBJECT. The ERCOT entry screen evaluates scarcity through TWO different objects in one
margin: (i) the SIGNAL side — the lookahead/forward-expectation composition with the model's
own expected-ORDC adder (runner._lookahead_reprice_signal); (ii) the RESERVE LEG — the prior
year's REALIZED post-solve ORDC adder r in Σ max(price − vc, r)
(screen_reserve_value_enabled). The two-scarcity-objects defect is MEASURED: the composed
entering-2024 signal mean is −$48.22/MWh with solar capture −$185/MWh (fwd-expectation §4 —
exact arithmetic, a delta crossing bases), and D11-R §4 measured the consequence from the live
side: the realized-r leg is an inexhaustible floor that keeps the GAS half of the
margin-exhaustion rule inert (gas builds to caps in both arms). D11-R's within-walk closure
(r_walk = max(0, r + Δadder)) is deliberately within-year-only and does NOT resolve the
cross-year basis question. That question — WHICH scarcity basis is the screen's margin — is
yours.

TASK — adjudicate, with exact arithmetic on existing committed objects; build at most a
default-OFF construction.
1. STATE THE CANDIDATE BASES precisely (at minimum: realized prior-year r as shipped; the
   signal's own expected-ORDC adder evaluated consistently; any composition the committed
   findings already name). For each: what a developer's pro-forma would actually use, and what
   it regenerates from in a forecast year (rule 13 admissibility — forward drivers only).
2. EXACT ARITHMETIC ON EXISTING OBJECTS FIRST (the charter's own words): recompute the
   committed entry-screen margins/anchors under each candidate basis from the committed dumps
   and probe artifacts (scripts/probes/entry_signal_l1b_allocator_counterfactual.py,
   entry_volume_rule_compare.py, results/calibration/entry_volume_rule_ab_ercot.json, the
   registered t1h-d11r pair). Deliverable: a per-year, per-candidate table of the screen margin
   and the implied terminal-RM anchor (open-loop reconstruction is sufficient; a live solve is
   NOT required for adjudication). Pre-declare, before computing, what each basis is expected
   to do to the gas-inertness result — the honesty test.
3. If, and only if, the adjudication needs a live A/B to be decisive: ONE arm-vs-control pair
   on the ERCOT T1-H leg at the registered posture, single run_config delta, registered on the
   FORECAST namespace with run_config.json (rule 15), years sequential (rule 12; ERCOT T1-H is
   not heavy, but the ≤2 heavy cap is shared — a MISO heavy solve is running at charter).
4. Any code you ship is a default-OFF ScenarioConfig field with its matrix row + a cell line in
   EVERY shard in the same PR (rule 28c) and byte-identical-off proof. You change NO default:
   the shipped screen behaviour is untouched. Arming ANYTHING is the owner's decision — your
   exit is a recommendation plus the decision-card material for the Q8 re-decision (options,
   what each re-opens, your recommendation and its evidence).

GUARDRAILS: no measured-outcome feedback (rule 13) — a basis is chosen for its market/physics
fidelity and forward reproducibility, never because it lands the RM anchor somewhere pleasing;
pre-declare directions before looking (S-4 is the model case). Nothing reverse-engineered to
clear an invariant (rule 21). One mechanism per phenomenon (rule 19): if the unified basis
supersedes the D11-R within-walk Δadder closure, say so explicitly — never stack. NO
out-of-training backcast year solved, scored or registered; freeze TIER-SCOPED (locked test
frozen for every ISO; validation by `complete` marker + --holdout-authorized — you touch
neither). Touch NO backcast keeper shard, status/*.js, calibration-complete.json, offer curve
or commitment bridge; the ERCOT backcast lane is active (ercot-239/241) — check
git ls-remote --heads origin at start and deconflict. Never re-test matrix cells adjudicated
R/I/G without new evidence; the ERCOT entry_margin_exhaustion cell is O (measured, escalated) —
your report may move it, but only the owner's ruling arms anything. No new GitHub Actions
workflows, no CI offloading. Push per CLAUDE.md Git & Pushing; blob-verify any ≥300-line file
after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d12-scarcity-basis-<date>.md with the candidate-basis table,
the exact arithmetic, the pre-declared expectations vs outcomes, the recommendation, and the
Q8 re-decision card material. Report to the owner; the director folds it into the next sitting.
```

---

## S-4b — NEISO ARA requirement re-vintage (r#13) — **LANDED PRs #4392/#4396; leg (b) strengthened, Q13 card presented at r#17; historical record, do not re-run**

```
You are the S-4b NEISO ARA REQUIREMENT RE-VINTAGE session of the capacity-expansion (Forecast
Finalization) track, chartered at director refresh #13 (ledger §0j; queued at r#10 by S-4's own
finding §0.4). DO NOT START if lane D14 (claude/capx-d14-neiso-t1x) has not merged — both edit
ff-verdicts.json and the NEISO board block; check git log origin/main for its merge first.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (rule 27).
BRANCH: claude/capx-s4b-neiso-ara — create FRESH off origin/main (git fetch origin main first)
and rebase before pushing.

WHY THIS EXISTS. S-4 (docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md §0.4/§6.3)
surfaced that ISO-NE's Nov 21 2025 ARA filing implies ≈ +380 MW of Installed Capacity
Requirement — LARGER than the 218 MW 2028 gap the hydro repair addressed — and rule 23
[R-FROZEN-DERIVE] requires requirement inputs to re-derive when their SOURCE publishes, never
because a residual moved. This is an intake on publication. It was blocked inside S-4 on the
missing ARA-cycle demand-resource companion value (finding §6.3): a requirement re-vintage
without its consistent DR companion mixes vintages.

TASK:
1. LOCATE THE COMPANION FIRST. Find the ARA-cycle-consistent DR/passive-demand-resource value
   that pairs with the Nov 21 2025 requirement filing (ISO-NE ARA filing docs / CELT / FCA
   result records). If no consistent companion is published, SHIPPING NOTHING IS THE HONEST
   OUTCOME — record precisely what is missing, where it will publish, and an intake pointer;
   do not mix vintages and do not estimate the companion (rule 14: a reconciled real value
   beats a guess, but a fabricated companion is neither).
2. If the pair is complete: intake it through the NEISO requirement registry the same way S-4's
   sourcing worked (per-source extract committed, provenance README, reproducible fetch,
   tests; data-intake conventions), citing the filing. Zero free parameters — the values are
   the filing's own.
3. PRE-DECLARED ARITHMETIC (recorded at charter, before you compute): on the D2-B basis the
   hydro repair cleared 2028 by ≈ +229 MW; a ≈ +380 MW requirement increase therefore plausibly
   RE-OPENS 2028 by ≈ −151 MW, and NEISO's leg (b) PROMOTE-WITH-CAVEATS may flip back. THAT IS
   THE HONEST OUTCOME IF IT HAPPENS — report it at full magnitude, never touch the sourced
   0.7352 hydro factor, never offset or re-tune anything to keep 2028 clear (rules 13/21). A
   result landing just clear of the gap is the SUSPICIOUS one.
4. RE-SCORE the NEISO T1-F leg at one HEAD (control = shipped requirement, treatment = re-vintaged
   pair; single run_config delta), register both on the FORECAST namespace with run_config.json
   (rule 15), preserve-then-overwrite on the bare `neiso-t1f` key (preserve the S-4V vintage
   under a suffix, exactly as S-4V preserved its predecessors). Refresh the NEISO board block —
   fetch/rebase around D13/D14's edits and keep their content intact.

GUARDRAILS: NO out-of-training backcast year solved, scored or registered; freeze TIER-SCOPED
(locked test frozen for every ISO; validation by `complete` marker + --holdout-authorized —
this lane touches neither). NEISO holds a `complete` marker on a CALIBRATED keeper — touch NO
backcast surface (keeper shard, status/*.js, calibration-complete.json). Years sequential
within a run; the ≤2 heavy cap is shared (a MISO heavy solve is running at charter; NEISO T1-F
is light). Mechanism matrix (rule 28): a requirement re-vintage is data intake, not a
mechanism — mint no cell verdict; if the requirement term's representation itself changes, that
IS a mechanism change and needs its row + cells + a director escalation before promotion. No
new GitHub Actions workflows, no CI offloading. Push per CLAUDE.md Git & Pushing; blob-verify
any ≥300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-s4b-neiso-ara-<date>.md with the sourced pair (or the honest
no-ship record), the pre-declared arithmetic vs the measured outcome at full magnitude, the
re-scored leg, and the board refresh. Report to the owner.
```

---

## D5 — three-ISO crossover CO2 derivation (r#14) — **LANDED PR #4374; Q12 ruled full-fix (see D5-R); historical record, do not re-run**

```
You are the D5 CROSSOVER CO2 DERIVATION session of the capacity-expansion (Forecast
Finalization) track, chartered at director refresh #14
(docs/handoffs/capx-director-ledger-2026-08.md §0k, lane D5). This is a ZERO-SOLVE attribution
lane: you decompose a measured miss on committed artifacts; you solve nothing, tune nothing,
re-score nothing, and edit no board surface.

DATA PROFILE: code (widen with `python3 scripts/hydrate_data.py --profile <iso>` ONLY if the
derivation chain forces a raw-source read; say so in the finding if you do).
MODEL ASSIGNMENT: Fable (rule 27).
BRANCH: claude/capx-d5-crossover-co2 — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

THE MEASURED OBJECT. The T1-X crossover scores forecast-mode (forward-derived) inputs against
the same actuals the calibrated backcast matches. Three ISOs miss CO2 far outside their bands
— ERCOT 49.2/42.7/50.6 %, PJM 45.1/40.4/54.2 %, MISO 63–76 % — while NYISO, measured by D10 on
the identical instrument, lands 10.1/10.3/3.9 %. Read every number from the LIVE verdict
records (bare/live keys in frontend/data/forecast/ff-verdicts.json: ercot-t1x /
pjm-2023-2027-crossover-ffr3a3-t1x / miso-2023-2027-crossover-ffr3a4-t1x / nyiso-t1x), never a
-ff2d baseline.

PRE-DECLARED HYPOTHESIS — TO TEST, NOT ASSUME (record your expected direction per ISO BEFORE
computing anything): the discriminant between the three and NYISO is a material coal fleet,
and the coal_twh crossover rows already FAIL in ERCOT (35.0/44.1 %) and PJM (23.9 % 2024). If
the CO2 miss is dominated by fuel-VOLUME error at roughly correct rates, the defect lives in
forecast-mode dispatch/fuel inputs (prices, must-run, retirement/vintage composition of the
crossover fleet); if volumes are roughly right and the RATE term dominates, it lives in the
forecast emission-rate derivation (multi-year CAMPD conditioned on model-simulated operation —
docs/handoffs/emissions-co2-rate-plan-2026-07.md) vs the backcast's same-year CEMS overlay. A
mixed answer is a real answer; report the split per ISO per year.

TASK:
1. EXACT DECOMPOSITION on the committed crossover bundles (each leg's registered artifacts
   carry per-class/per-fuel generation and emissions): split each ISO-year CO2 miss into a
   volume term (actual rates × modeled-vs-actual generation mix) and a rate term
   (modeled-vs-effective-actual rate at actual volumes), plus the interaction — an index
   decomposition with the arithmetic shown, reproducible from cited files. Run the SAME
   decomposition on NYISO as the control: whatever term the three share must be small or
   absent there, or the discriminant hypothesis is refuted — say so plainly.
2. TRACE the dominant term to its derivation chain (name the module/spec section and the
   input vintage actually consumed by the crossover runs — verify in each bundle's
   run_config.json, don't infer). Distinguish a DERIVATION defect (fixable: wrong vintage,
   wrong conditioning, boundary mismatch) from an honest INPUT GAP the crossover exists to
   measure (forward fuel prices vs delivered, weather-year, etc.) — the two have different
   successors and conflating them is the failure mode.
3. RECOMMEND the repair lane(s): what change, in which module, admissible under rule 13
   (forward-reproducible, responds to changed conditions), and what the crossover would be
   expected to do — pre-declared, so a future re-measure cannot be back-fitted. If the honest
   answer is "input gap, no repair," say that; FC-4's job is to measure it.

GUARDRAILS: zero solves; nothing registered; no ff-verdicts.json or program-status.json edits
(your FINDING is the director's input — board currency rides D13-class records work). No
measured-outcome feedback (rule 13): actual CO2/CEMS data is used here to ATTRIBUTE a measured
miss, never to adjust any input, rate, or curve in this lane. Nothing reverse-engineered
(rule 21). Mechanism matrix (rule 28): analysis tests no mechanism — mint no cell verdict; if
your recommendation names a new mechanism, it enters the matrix as a row only when its PR
exists (the successor lane's job). NO out-of-training backcast year solved, scored or
registered; freeze TIER-SCOPED (locked test frozen for every ISO; validation by `complete`
marker + --holdout-authorized — you touch neither). Touch NO backcast surface. In-flight
backcast branches at charter: caiso-224, ercot-241, miso-190 — you conflict with none, but
check git ls-remote --heads origin at start anyway. No new GitHub Actions workflows, no CI
offloading. Push per CLAUDE.md Git & Pushing; blob-verify any ≥300-line file after push
(rule 27).

EXIT: docs/handoffs/FINDING-capx-d5-crossover-co2-<date>.md with the pre-declared directions,
the per-ISO-per-year decomposition table (NYISO control included), the traced chain with file
citations, the derivation-defect vs input-gap adjudication, and the recommended successor
lane(s). Report to the owner; the director folds it into the queue.
```

---

## D12-C — arming confirmation pair (r#15) — **CONCLUDED PR #4406: CONTRADICTION (V-2), nothing armed; Q15 ruled ARM at r#18 (see D12-A); historical record, do not re-run**

```
You are the D12-C ARMING CONFIRMATION PAIR session of the capacity-expansion (Forecast
Finalization) track, executing the owner's Q10 ruling (r#15 sitting, 2026-08-30: "Confirm-pair,
then arm" — docs/handoffs/capx-director-ledger-2026-08.md §0l.2/§3). You run ONE closed-loop
A/B; ON A CONFIRMING RECORD YOU ARM BOTH FIELDS as ERCOT forecast defaults in the same session
— that arming is pre-authorized by the ruling and needs no further ask. A CONTRADICTING record
arms NOTHING and returns to the owner at full magnitude.

DATA PROFILE: ercot
MODEL ASSIGNMENT: Fable (edits defaults in config — rule 27).
BRANCH: claude/capx-d12c-confirm-pair — create FRESH off origin/main (git fetch origin main
first) and rebase before pushing.

READ FIRST: docs/handoffs/FINDING-capx-d12-scarcity-basis-2026-08-30.md (§0, §5, §7 —
the adjudication and its open-loop predictions) + PREDECL-capx-d12-scarcity-basis-2026-08-30.md;
docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md §3 (the A/B protocol you are
repeating and its committed control bracket).

THE PAIR. On the ERCOT `ercot-2021-2025-realized` T1-H leg at the registered posture, same
HEAD, both invocations solved by this session, years sequential within each (rule 12):
- CONTROL: bare invocation — must reproduce the committed registered bracket EXACTLY (the
  D11-R control did: cache key 28cef3500ec1fd9e, RM 19.00→8.54→14.65→25.19, additions
  verbatim). Any control drift is a stop-the-line finding, not a baseline.
- ARM: exactly TWO run_config fields differ, as the single logical delta:
  entry_margin_exhaustion=True + entry_forward_reserve_leg=True. Hard-fail the probe unless
  the delta condition holds (reuse/extend scripts/probes/entry_volume_rule_compare.py).

PRE-DECLARED EXPECTATIONS (write them in the finding BEFORE the arm solves; they are D12's
open-loop arithmetic, and the pair exists to test them closed-loop):
- The exhaustion walk on the consistent leg reproduces D12's reconstruction: expected terminal
  RM ≈ 18.71 % (2024-step ≈ 18.08 % variant per §5.1), no 6 GW phantom gas at the entering-2024
  and entering-2025 steps (those margins are negative on the forward leg).
- Scored gas addition bands improve (gas_cc toward 6 GW, gas_ct toward 4.571; CT |err| toward
  0.879) — attached evidence, never the verdict (rule 1).
- B-2 posture re-measured and reported (the cobweb under the armed pair — whatever it shows).
- State your numeric confirmation tolerance ex ante (from D12's own reproduction error, $0.05
  on margins; a sensible RM tolerance follows) — do not choose it after seeing the arm.

THEN, ON CONFIRMATION (all pre-declared checks inside tolerance): ARM — flip BOTH fields to
the ERCOT forecast defaults via the ISOConfig/default route (cite the Q10 ruling verbatim in
the citation block), update the ERCOT matrix shard cells in this session (rule 28b:
entry_margin_exhaustion O → K-forecast-armed with this pair as evidence; the
entry_forward_reserve_leg row's ERCOT cell likewise; sister-ISO cells enter/stay U — rule 26,
verdicts are ERCOT's), and record the armed posture honestly: the volume rule with its gas
half live on a one-object margin. ON CONTRADICTION: arm nothing, leave cells O, FINDING at
full magnitude with the divergence decomposed, report back — the owner re-decides.

REGISTRATION (rule 15): both arms on the FORECAST namespace with run_config.json committed
(`ercot-2021-2025-realized-t1h-d12c-{control,armed}`), never the backcast registry.

DECONFLICTION: the audit-track T1-H capacity-entry lane is live and has ceded defect D-1 to
this track (its precommit's dedup gate) — do not take its storage/wind scope; you both touch
the ERCOT matrix shard, so fetch/rebase carefully. The ercot-242 backcast lane is in flight
(different surfaces). Check git ls-remote --heads origin at start. ERCOT T1-H is not heavy,
but the ≤2 concurrent heavy cap is shared with the owner's backcast solves (caiso-224 may be
solving) — you fit, but launch nothing larger.

GUARDRAILS: NO out-of-training backcast year solved, scored or registered; freeze TIER-SCOPED
(locked test frozen for every ISO; validation by `complete` marker + --holdout-authorized —
you touch neither). No measured-outcome feedback (rule 13); nothing tuned to land the
confirmation (rule 21) — the tolerance is declared before the arm runs. Touch NO backcast
keeper shard, status/*.js, calibration-complete.json, offer curve or commitment bridge. No new
GitHub Actions workflows, no CI offloading. Push per CLAUDE.md Git & Pushing; blob-verify any
≥300-line file after push (rule 27) — the config file carrying the default flip qualifies.

EXIT: docs/handoffs/FINDING-capx-d12c-confirm-pair-<date>.md with the pre-declared
expectations vs measured, the confirm/contradict verdict, and — on confirm — the armed default
diff, matrix stamps, and the honest posture description. Report to the owner either way.
```

---

## D5-R — crossover-scorer coal-grain repair (r#15) — **LANDED PR #4388, controls verified at r#17; historical record, do not re-run**

```
You are the D5-R SCORER COAL-GRAIN REPAIR session of the capacity-expansion (Forecast
Finalization) track, executing the owner's Q12 ruling (r#15 sitting, 2026-08-30: full fix,
D5's preference (a) — docs/handoffs/capx-director-ledger-2026-08.md §0l.2/§3). This is a
scorer-side repair + ZERO-SOLVE re-score: no model input, rate, curve, or default changes; no
LP solves.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (edits scripts/score_*.py — rule 27).
BRANCH: claude/capx-d5r-scorer-coal-grain — create FRESH off origin/main (git fetch origin
main first) and rebase before pushing.

READ FIRST: docs/handoffs/FINDING-capx-d5-crossover-co2-2026-08-30.md — §0 (the mechanism),
§2 (the rate-exoneration measurement), §5.1 (the fix you are implementing), §5.2 (THE
PRE-DECLARED EXPECTATION TABLE — your honesty gate), §5.3 (what is explicitly not recommended).
Also docs/handoffs/FINDING-capx-d14-neiso-t1x-2026-08-30.md finding 1 (NEISO as second control).

THE FIX (D5 §5.1 preference (a), as ruled): in scripts/score_crossover.py, map each model coal
generator to its supply class at gmModel-build time via the repo's CANONICAL chain —
`coal_supply_class` on `plant_code`, falling back to generic `COAL` exactly as
`run_calibration_full.py::_coal_supply_class` does. One taxonomy chain, no second map
(rule 19 [R-ONE-MECH]); this puts the crossover on the keeper's own basis and repairs the C1
fuelmix coal rows (~60 TWh/ISO-yr phantom) in the same stroke. Tests: trivial-first (a
synthetic two-plant fixture through the mapping), plus a regression asserting the NYISO no-op.

THE RE-SCORE (zero-solve): re-score the committed crossover bundles via the rescore path
(scripts/rescore_forecast_verdicts.py / score_crossover.py --rescore) and re-emit the affected
verdicts — the live keys `ercot-t1x`, `pjm-2023-2027-crossover-ffr3a3-t1x`,
`miso-2023-2027-crossover-ffr3a4-t1x`, `nyiso-t1x`, `neiso-t1x` — PRESERVE-THEN-OVERWRITE:
keep each pre-repair record under a `-pre-d5r` suffix so the superseded baseline stays
committed, exactly the namespace's convention. Update the affected FC-4 cells/blocking rows on
the board (frontend/data/forecast/program-status.json) with the re-scored magnitudes and a
citation to this repair; leg (c) statuses DO NOT move (measured-closes, Q7 — a re-scored
measurement is still measured); state explicitly that no gate leg changes.

THE HONESTY GATE (D5 §5.2, pre-declared before this lane existed — measure against it and
report every deviation at full magnitude):
- NYISO must be an EXACT no-op; NEISO moves ≲0.4 %. Any control movement means the fix touched
  more than the unmapped-coal seam — STOP, do not commit the re-score, report.
- MISO's coal_twh and PJM's gas_twh family rows must be untouched (already grain-reconciled).
- Expected outcomes (existing bands, K unchanged): ERCOT co2 → −25.3/−23.2/+1.3 % (2023/24
  still FAIL — the honest volume gap; 2025 PASS); PJM → −7.6/−10.5/−1.3 % (co2 leaves PJM's
  FC-4 FAIL set); MISO → +1.2/−1.9/+13.4 % (co2 leaves MISO's FAIL set). Offsets up to the
  finding's stated ~2-3 pp are anticipated for the (a) fix; anything beyond is a deviation to
  report, never to absorb.
- Also record D5's corollary 2 where the board cites FC-4 co2: as constructed the metric scores
  volume/mix + mapping, not rate error (rate is measured separately, §2's own-rate comparison)
  — an instrument property to document, not to "fix" here.

RULE 28: this tests no mechanism and adds no ScenarioConfig field — no matrix row, no cell
verdict. t1x DETERMINATIONS may move on the re-score (e.g. a FAIL row leaving a set) — re-emit
them from the scorer honestly; you decide nothing, the scorer does.

GUARDRAILS: NO solves; NO out-of-training backcast year touched; freeze TIER-SCOPED (you touch
neither tier). No measured-outcome feedback (rule 13): bench data enters only through the
scorer's own intensity reconciliation, never a model input. Touch NO backcast surface except
score_crossover.py itself if shared (it is a forecast scorer; if any backcast scorer imports
the changed seam, measure and report the backcast-side effect — expected: none, the keepers
score through calibration_verdict.py whose PLANT_GROUP_MEMBERS patch already handled this
seam). The C1 fuelmix repair changes crossover-scored fuelmix rows — report those before/after
too. No new GitHub Actions workflows. Push per CLAUDE.md Git & Pushing; blob-verify
score_crossover.py and program-status.json after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d5r-scorer-coal-grain-<date>.md with the diff summary, the
§5.2 table measured-vs-predeclared (controls first), the re-emitted verdicts, the board
before/after, and the no-gate-moved statement. Report to the owner.
```

## CAISO-224-FIN — finish the caiso-224 FSNO arm round (r#17; OWNER-REQUESTED backcast-track completion — a director-boundary exception recorded in the ledger; gates S-6's release)

```
You are the CAISO-224 FINISHER session for the market-simulator repo — completing the
caiso-224 FSNO sub-zonal arm round whose session ran out of context after its solves
completed but BEFORE registration, adjudication and records landed. This is BACKCAST-track
completion work, drafted by the capacity-expansion director at the owner's explicit request
(capx r#17 sitting, Q14). ZERO SOLVES: every solve artifact is already committed.
DATA PROFILE: code (widen via `python3 scripts/hydrate_data.py --profile caiso` ONLY if a
scoring input is genuinely missing from the committed artifacts — a solve replay is NOT
licensed under any circumstance).
MODEL: Opus/Fable (rule 27). BRANCH: claude/caiso-224-fsno-finisher — fresh off origin/main
(git fetch origin main first). Check `git ls-remote --heads origin` at start for in-flight
branches; do not trust this prompt's snapshot.

STATE ON MAIN (verify, don't trust): the round's precommit is
results/calibration/PRECOMMIT-caiso224-fsno-arm-2026-08-30.md (§5 = pre-registered gates and
falsifiers, §6 = the records this round owes). Committed and complete:
- results/calibration/caiso224_a0_control/ (A0 control — reproduced the caiso-220 keeper
  G-CTRL BIT-ZERO) and results/calibration/caiso224_b1_fsno/ (the FSNO arm, 2023/24/25 —
  hourly sidecars, legitimacy_diagnostics.json, meta.json, run_config.json).
- results/calibration/_caiso224_ctrl_tolerance.json and _caiso224_split_witness.json (the §5
  primary witness + F1/F2 measurements, computed post-B1 over all three years).
- The mechanism row/cells for `caiso_fsno_subzonal_topology` were minted when the gated field
  landed; the CAISO cell VERDICT stamp is still owed.

WHAT REMAINS (precommit §6, executed faithfully — the precommit governs, not anyone's
recollection of intent):
1. ADJUDICATE per §5 from the committed artifacts. The committed witness record shows, and
   you must re-read rather than take from this prompt: F1 (over-trapping) FIRES all three
   years on NP15<->FSNO (binding_share 0.3054/0.3547/0.3380 vs the 0.27 DMM ceiling) and F2
   (static-vintage) FIRES (arm split vector [1556,1359,1186] strictly year-ordered vs
   reality's non-monotone [1310,1691,1347]). Per §5's own pre-registered rule, F1 firing ⇒
   the static DMM-cap arm is **R for keeper purposes** (the partition REPRESENTATION remains;
   W-2/W-3 are the named upgrade feeds; F2 additionally records the backcast-admissible
   transmission-outage derate channel as the WATCH, not armed). §5's verdict space is
   K/O/R and NEVER auto-promoted: if your full-guard evaluation somehow reads K, STOP and
   put a decision card to the owner — promotion is an owner act; do NOT touch the keeper.
2. GUARDS, from committed artifacts only (calibration_verdict.py --run-id pattern — never a
   solve): C1 rows re-scored (the zonal recut must not flip fuel-mix rows); the C3b tripwire
   (any year worsening >0.005 EMD named to a mechanism); C2/C4/C8 re-scored; C3a movement
   reported at FULL magnitude against the §5 pre-bound (direct pocket-floor channel ≈
   −$0.23/−$0.32/−$0.25 lw; full 2025 close NOT expected ex ante).
3. REGISTER BOTH BUNDLES on the BACKCAST dashboard (rule 15): calibration-report skill /
   scripts/dashboard_add_run.py + build_manifest.py, control and arm alike, rejected-probe
   labelling per the verdict; honour top-15 retention. The run payload
   (frontend/data/backcast/runs/<id>.js) goes over `git push` (push_files cannot carry it);
   if git push hits HTTP 408/500, set `git config http.version HTTP/1.1` and retry BEFORE
   concluding anything (CLAUDE.md Git & Pushing §2 — the 500s are transport, not pack size).
4. RECORDS: FINDING-caiso224-fsno-arm-2026-08-30.md (the adjudication, F1/F2 at full
   magnitude, guard scores, the honest witness result — the split RESTORATION is real
   (52/40/17 control → 1556/1359/1186 arm vs reality 1310/1691/1347) AND both falsifiers
   fire; both facts are the record); docs/calibration-log/caiso.md entry; the CAISO matrix
   shard cell verdict stamp (rule 28b — your OWN shard only, expected R with the citation).
5. UNTOUCHED, verbatim: the CAISO keeper (2026-08-26-caiso-220-c1-crosswalk), every keeper
   shard, calibration-complete.json, holdout-freeze.json, every other ISO's shard, all
   forecast-namespace surfaces.

GUARDRAILS: reads stay in 2023–2025 (rule 22 — no out-of-training year solved, scored or
registered); no measured-outcome feedback (rule 13); no src/market_sim edits; no new
workflows/CI offloading; push per CLAUDE.md Git & Pushing, blob-verify every ≥300-line file
after push on either transport (rule 27). THE OWNER MERGES.

EXIT: registration + finding + log + matrix stamp committed and pushed; report the verdict
and the C3a movement to the owner. [SUPERSEDED at r#19: S-6 no longer waits on this lane —
the owner voided the cross-session heavy-slot queue; sessions run in isolated containers.]
```

## T3-NEISO-GOLDEN — the FIRST §2.1b-authorized full-horizon campaign (r#17; owner ruling Q13)

> **r#20 RELAUNCH ANNOTATION RETRACTED at r#21 (2026-08-31, owner correction): the original golden session was NEVER LOST — it is STILL RUNNING its solve.** T3-GOLDEN-R was RECALLED UNRUN (never dispatched). Do NOT launch a second golden: the Q13 authorization covers ONE campaign, and the NEISO keys of ff-verdicts.json + program-status.json are the running session's to write. This section remains the original (r#17) lane's binding charter (ledger §0r.1).

```
You are the T3-NEISO-GOLDEN session of the capacity-expansion (Forecast Finalization
Program) track — executing the FIRST full-solve campaign ever authorized under the §2.1b
gate. AUTHORIZATION (leg (d), owner ruling Q13, capx r#17 sitting 2026-08-30, recorded in
docs/handoffs/capx-director-ledger-2026-08.md §3): ISO=NEISO, window=2026–2050 T3 BAU
golden, budget ~1.0 h wall / ~4.3 GB RSS (the FF-3E projected table), THIS CAMPAIGN ONLY —
no standing authorization, and any gate-condition regression re-closes the gate (charter
§2.1b(2)(d)). Cite this authorization verbatim in your finding and the board stamp.
DATA PROFILE: neiso
MODEL: Opus/Fable (rule 27). BRANCH: claude/capx-t3-neiso-golden — fresh off origin/main
(git fetch origin main first); check `git ls-remote --heads origin` for in-flight branches.

READ FIRST: docs/forecast-development-plan-2026-07.md §2.1b (the gate you are executing) +
§2.1a (posture); docs/handoffs/FINDING-capx-s4b-neiso-ara-2026-08-30.md (the CURRENT
requirement bar — ARA-3 factor 1.0286103, DR 0.08784, imports 409.31 — and §5.3's
floor-dependence honesty notes, which you carry verbatim); FINDING-capx-s4-neiso-hydro +
FINDING-capx-d14-neiso-t1x (the composition caveat); the NEISO block of
frontend/data/forecast/program-status.json.

THE RUN — zero config invention, HEAD defaults at golden posture (exactly the S-4b
treatment construction, extended to the authorized window):
  MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 \
    --golden-posture --full-solve-authorized --out-dir results/ff-t3-neiso-golden/bau
- --full-solve-authorized is the FF-3E schedulability guard for >5 solve-years; it is
  licensed by the Q13 authorization above and by nothing else. Years run SEQUENTIALLY
  within the invocation (rule 12) — never parallelize the year loop.
- PRE-DECLARE in the finding BEFORE launching: expected wall/RSS (~1.0 h / ~4.3 GB;
  report measured vs projected), and the caveats the campaign record carries WITHOUT
  re-tuning anything: (i) 2028/29 I7 margins are floor-dependent (+419.0/+333.6 MW riding
  on the 699.3 MW retention response, S-4b §5.3); (ii) D14's retirement-composition miss
  (exit recall 2/6 in the crossover window) — out-year fleet composition inherits this
  known defect and the record SAYS SO; (iii) FC-7 program-wide DOF-ledger gap. Out-year
  behavior (2031+) is REPORTED, never judged against actuals (none exist) and never
  back-tuned (rule 13).
- Commit per-year evolution artifacts as checkpoints as the horizon progresses (the T1-F
  evolution_<year>.json pattern), so a mid-horizon failure preserves the record. If the
  solve breaks mid-horizon, the failure record IS the deliverable — report at full
  magnitude; never register a partial run as complete.
- HEAVY-SLOT: ~4.3 GB is co-runnable, but NOT alongside a PJM (8.8 GB) or MISO (9.6 GB)
  no-co-run measure — check in-flight branches and recent solve checkpoints before
  launching; if the S-6 PJM ledger run is in flight, WAIT for it (it is short).

REGISTRATION (rule 15, FORECAST namespace ONLY — never the backcast registry):
scripts/register_forecast_run.py --summary, run id neiso-2026-2050-t3-golden-bau,
committing run_config.json (a bundle without one scores FC-7 FAIL), full_horizon_summary,
per-year evolution files, resolved config; heavy dispatch outputs stay gitignored.
Preserve-then-overwrite on any existing verdict key (no t3 key exists today — verify).

BOARD (program-status.json, NEISO block only): stamp leg d_owner_auth with the Q13
authorization (date, sitting, ISO/window/budget, scope: this campaign only), flip
gate.open accordingly with the scope stated, and add the T3 campaign row after
registration lands. Keep D14's leg-(c) and S-4b's leg-(b) content verbatim. Rebase care:
D12-C and S-123 are in flight and may touch adjacent board blocks.

GUARDRAILS: forecast-mode 2026+ is UNRESTRICTED (no out-of-training backcast year solved,
scored or registered; freeze TIER-SCOPED, you touch neither tier; measured overlays are
backcast-only by construction). No measured-outcome feedback (rule 13); no value
reverse-engineered to clear an invariant (rule 21). No new mechanism, no ScenarioConfig
field, no matrix duty (shipped defaults only — if you find yourself wanting a config
change, STOP: that is a different lane). Touch NO backcast surface. No new GitHub Actions
workflows. Push per CLAUDE.md Git & Pushing (HTTP/1.1 retry on 408/500 before any
conclusion about pack size); blob-verify every ≥300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-t3-neiso-golden-<date>.md — the pre-declaration, measured
wall/RSS vs projected, the horizon record (fleet evolution trajectory, entry/exit waves,
price/RM paths at reporting grain), the carried caveats verbatim, registration +
board-stamp confirmation. Report to the owner; the director stamps the ledger on its
refresh.
```

## D12-A — arming execution (r#18; executes the Q15 ruling on the D12-C contradiction record)

> **LANDED at r#21 (PR #4429); historical record, do not re-run.** > **RELAUNCHED at r#20 (2026-08-31) as D12-A-R, model Fable:** the dispatched session was lost with an ORPHAN branch (`claude/capx-d12a-arming-0ibtzh`, 2 unmerged commits arming the pair + stamping the matrix). NOT landed. This section stays the BINDING charter. The relaunch session treats that branch as EVIDENCE only — re-verify its diff against the Q15 ruling and this charter (cache-epoch verification included; rule 27 blob-verify every >=300-line file), then land it re-verified or redo clean. Never blind-merge (ledger §0q.2).

```
You are the D12-A ARMING EXECUTION session of the capacity-expansion (Forecast Finalization
Program) track. ZERO SOLVES. You execute owner ruling Q15 (r#18 sitting, 2026-08-30,
docs/handoffs/capx-director-ledger-2026-08.md §3): on the D12-C confirmation pair's measured
record — CONTRADICTING on the single V-2 window, every other criterion and every structural
claim confirmed — the owner judged the record CONFIRMING-IN-SUBSTANCE per the finding's own
§4.3 clause and DIRECTED the arming of BOTH fields as ERCOT forecast defaults.
DATA PROFILE: code
MODEL: Opus/Fable (rule 27 — this edits src/market_sim/config). BRANCH:
claude/capx-d12a-arming — fresh off origin/main (git fetch origin main first); check
`git ls-remote --heads origin` for in-flight branches (expect the T3 NEISO golden open —
no surface overlap; rebase care on the ERCOT matrix shard).

READ FIRST: docs/handoffs/FINDING-capx-d12c-confirm-pair-2026-08-30.md (§1.4 = the exact
execution list confirmation would have triggered — you execute it under Q15 instead; §4.2 =
the V-2 miss you must describe honestly); FINDING-capx-d12-scarcity-basis-2026-08-30.md §5
(the mechanism being armed); the ERCOT shard docs/codebase-site/data/mechanism-matrix/ERCOT.js.

THE EDIT (the §1.4 list, adapted to the Q15 route):
1. Flip `entry_margin_exhaustion` and `entry_forward_reserve_leg` to ERCOT forecast defaults
   via the ISOConfig `default_scenario_overrides` route (the FFR-9C stage-B pattern). In the
   citation block cite Q10 ("confirm-pair, then arm") AND Q15 verbatim (owner direction on a
   contradiction record judged confirming-in-substance), and describe the posture honestly:
   ERCOT forecast entry becomes exhaustion-bounded on the entering year's own expected-ORDC
   surface for every candidate class; the V-2 entering-2022 gas_cc window missed [750,1250]
   at 0 MW — a pre-declaration derivation error (offline walk's restricted candidate set),
   conservative direction, tolerance never widened (rule 21).
2. ERCOT matrix shard cells: `entry_margin_exhaustion` O → K-forecast-armed and
   `entry_forward_reserve_leg` likewise, evidence = the registered pair
   (`ercot-2021-2025-realized-t1h-d12c-{control,armed}`) + Q15. Sister-ISO cells stay U
   (rule 26). Rule 28b: your own shard, this session.
3. VERIFICATION, zero-solve: after the flip, the resolved ERCOT ScenarioConfig carries both
   fields True and `ScenarioConfig.cache_key()` for the bare ERCOT T1-H construction
   reproduces `f061b2646bfaac8b` — the D12-C armed bundle's key: the registered armed run IS
   the record of the new default posture (state this in the finding; no re-solve, no
   re-registration — both bundles are already registered). Run the repo's fast checks and
   update any default-assertion tests the flip breaks (assert the NEW default with the Q15
   citation, never weaken a test).
4. NO other surface: backcast untouched by construction (backcast runs no capacity
   evolution); no board edit (the director stamps the board on its refresh); no new
   ScenarioConfig field (both fields exist — no new matrix row).

CROSS-TRACK NOTE (carry into the finding): the arming moves ERCOT forecast defaults under
the audit track's T1-H capacity-entry lane. Their registered-posture control bundles are
unaffected (committed run_configs pin their values), but any FUTURE bare ERCOT T1-H/forecast
invocation lands on the armed defaults — flag it in the finding so their next session sees
it; do not touch their surfaces.

GUARDRAILS: zero solves; no out-of-training backcast year touched (freeze TIER-SCOPED, you
touch neither tier); no measured-outcome feedback (rule 13); no value invented (rule 21 —
you flip two booleans and cite two rulings). Push per CLAUDE.md Git & Pushing (HTTP/1.1
retry on 408/500; note: git push to a NOT-YET-EXISTING remote branch has failed repeatedly
through this proxy until the branch exists — if it 500s persistently, create the branch via
the API first, then push); blob-verify every ≥300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d12a-arming-2026-08-30.md — the edit, the cache-key
verification, the honest posture description with the V-2 miss, the cross-track flag, test
results. Report to the owner; the director stamps board + ledger on its refresh.
```

## S-6 — PJM T1-F ledger run (r#19; the first supply-side measure against the corrected hold-last bar)

> **LANDED at r#21 (PR #4436); historical record, do not re-run.** > **RELAUNCHED at r#20 (2026-08-31) as S-6-R, model Opus:** the dispatched session was lost AFTER landing the pre-declaration (PR #4418, `FINDING-capx-s6-pjm-ledger-2026-08-30.md` — post-solve sections empty) and BEFORE the solve. The committed pre-declaration + this section stay BINDING: owed are the solve, the FC re-score, registration `pjm-2026-2030-s6-ledger`, the preserve-then-overwrite verdict keys and the PJM board refresh. Branch fresh from main (`claude/capx-s6-pjm-ledger-r2`); the old branch carries 0 unique commits (ledger §0q.2).

```
You are the S-6 PJM T1-F LEDGER RUN session of the capacity-expansion (Forecast Finalization
Program) track. ONE five-year solve, PJM's own container. Charter: S-5 (LANDED PR #4340)
restated PJM's I7 2030 miss 366 MW → 5,858 MW scorer-side by adopting hold-last-FPR (owner
card C-A) and repairing the checker's year-threading — but it ran NO solve, so the SUPPLY
side has never been measured against the corrected bar. You run the minimum solve that makes
it observable: does 2029 actually join the fail set, and what is the true 2030 magnitude once
the fleet responds?
DATA PROFILE: pjm
MODEL: Opus/Fable (rule 27). BRANCH: claude/capx-s6-pjm-ledger — fresh off origin/main
(git fetch origin main first); check `git ls-remote --heads origin` for in-flight branches
(expect the T3 NEISO golden and possibly others — different ISOs, different surfaces; the
shared files you both touch are ff-verdicts.json and program-status.json on DISTINCT
keys/blocks: rebase before pushing, never resolve another lane's block).

READ FIRST: docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md (the corrected bar,
its restatement arithmetic, the 2029/30 intake pointer); FINDING-capx-s4b-neiso-ara §5.2-5.3
(the floor-retention response pattern you may see the PJM analogue of — pre-declare it);
the PJM block of program-status.json; docs/handoffs/FINDING-capx-d2b-i7-ledger (PJM leg).

PRE-DECLARE BEFORE THE SOLVE (commit §§1-N of your finding first — the S-4b discipline):
- The solve: MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
    python scripts/run_full_horizon.py --iso PJM --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ff-t1f-s6-pjm/ledger
  (5 solve-years — inside the §2.1b window cap, no authorization flag needed; years
  sequential within the run, rule 12.)
- ONE run, no control pair: nothing changed since S-5 landed at HEAD — this is the FIRST
  measure on the corrected bar, decomposed against the COMMITTED pjm-t1f ledger (requirement
  delta = S-5's scorer-side restatement, already quantified; what this run adds is the
  supply-side response). Any epoch drift vs the committed bundle is decomposed and named,
  the S-4V/NYISO-lane discipline.
- Pre-declare directions, not targets: S-5's arithmetic says 2030 I7 ≈ −5.9 GW on a static
  supply; the known endogenous response is reliability-floor exit retention (the S-4b
  mirror — declare its direction, let the run measure the net); 2029 "plausibly joins" is
  S-5's language — the run answers it. A result landing just clear of a gap is the
  suspicious one (rule 21); an honest FAIL is a finding, not a problem.
- I12 and the backstop row are re-read as consequences, never targets; a clearance bought
  by backstop builds is REPORTED AS SUCH.

REGISTRATION (rule 15, FORECAST namespace only): register_forecast_run.py --summary, run id
pjm-2026-2030-s6-ledger, committing run_config.json + summary + per-year evolution +
resolved config. Preserve-then-overwrite: the current bare pjm-t1f vintage is preserved
under a dated suffix key before the bare key moves. Refresh the PJM board block (T1-F rows,
fc map, gate leg (b) detail) with the S-5 restatement provenance kept verbatim; touch no
other ISO's block.

GUARDRAILS: forecast-mode 2026-2030 — no out-of-training backcast year solved, scored or
registered (freeze TIER-SCOPED; you touch neither tier); no measured-outcome feedback (rule
13); no config change, no new mechanism, no matrix duty (shipped defaults at golden
posture — a config urge is a different lane); no backcast surface. No new workflows. Push
per CLAUDE.md Git & Pushing (HTTP/1.1 retry on 408/500; if push to a new remote branch 500s
persistently, create the branch via the API first, then push); blob-verify ≥300-line files
(rule 27).

EXIT: docs/handoffs/FINDING-capx-s6-pjm-ledger-<date>.md — pre-declaration, the measured
per-year I7 ledger with the supply-side decomposition vs the committed bundle, whether 2029
joins, the true 2030 magnitude, FC re-score, registration + board confirmation. Report to
the owner; the director stamps the ledger on its refresh.
```

## S-123-V — the MISO verification re-measure (r#19; fills S-123's §6, the lane's owed half)

> **LANDED at r#21 (PR #4441); historical record, do not re-run.** > **RELAUNCHED at r#20 (2026-08-31) as S-123-V-R, model Opus:** the dispatched session was lost with NOTHING landed. This section stays the BINDING charter unchanged; the stop-at-start check on the original S-123 session now trivially passes (that session is confirmed dead, its A/B long since concluded). Branch fresh from main (`claude/capx-s123v-miso-verify-r2`) (ledger §0q.2).

```
You are the S-123-V session of the capacity-expansion (Forecast Finalization Program) track,
completing lane S-123's owed verification half. S-123 (LANDED PRs #4397/#4398/#4402) shipped
the three-term MISO adequacy package — S-1 PRM re-vintage 0.179→0.157, S-2 external-ZRC
+3,505.9 MW, S-3a DR fraction 0.0665940 — with pre-solve arithmetic moving the 2026 position
−6,037.0 → +9,343.2 MW, and committed its finding with §6 "RESULTS: TBD". You run the solo
MISO T1-F re-measure §6 pre-declares, fill it, and register. If the original S-123 session is
still alive and mid-run, STOP at start (ls-remote + a fresh commit check) and report instead
of duplicating.
DATA PROFILE: miso
MODEL: Opus/Fable (rule 27). BRANCH: claude/capx-s123v-miso-verify — fresh off origin/main;
check `git ls-remote --heads origin` (the T3 NEISO golden and S-6 PJM may be in flight —
different ISOs; shared-file rebase care on ff-verdicts.json / program-status.json, distinct
keys/blocks only).

READ FIRST: docs/handoffs/FINDING-capx-s123-miso-adequacy-2026-08-30.md — §6's pre-solve
predictions ARE your pre-registration (2026 requirement 141,341.4 → 129,467.1; accredited
135,304.4 → 138,810.3; position → +9,343.2; I7 2026 → PASS; I12 floor +0.71%, rm +7.98%
in-band; 2027 backstop fires less or not at all). Do not restate them — run against them.
Any HEAD demand-path drift is decomposed separately, the NYISO-lane discipline.

THE RUN: MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/run_full_horizon.py --iso MISO --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-s123/verify
(5 solve-years, years sequential, rule 12; the ff-t1f-s123 slim-vs-heavy gitignore block is
already committed.)

THEN: fill §6 RESULTS in the finding (run id, cache key, wall/RSS, per-year ledger with the
three-term intake decomposition, FC-1/FC-2 re-score); register on the FORECAST namespace
(register_forecast_run.py --summary, run id miso-2026-2030-s123-ara... use the §4-declared id
if the finding names one, else miso-2026-2030-s123-verify), committing run_config.json;
preserve-then-overwrite — the current bare miso-t1f vintage preserved under a dated suffix
key; refresh the MISO board block (FC-1 rows, I7/I12 detail, the S-123 provenance) and no
other ISO's. An I7 that does NOT close as the arithmetic predicts is the headline, reported
at full magnitude — never absorbed (the package is 2.5× over-determined; a miss means an
endogenous response or a defect, and you name which).

GUARDRAILS: forecast-mode 2026-2030 only; freeze TIER-SCOPED, touch neither tier; no
measured-outcome feedback (rule 13); no config change beyond what S-123 already shipped —
zero new values (rule 21); no backcast surface; no new workflows. Push per CLAUDE.md
(HTTP/1.1 retry; API-create a stubborn new branch); blob-verify ≥300-line files (rule 27).

EXIT: §6 filled + registration + board refresh committed and pushed; report the measured
position table vs the §6 predictions to the owner.
```

## NEISO-RC — retirement-composition Phase-0 diagnosis (r#19; the D14 successor object, zero-solve)

```
You are the NEISO-RC PHASE-0 session of the capacity-expansion (Forecast Finalization
Program) track. ZERO SOLVES. Object (D14, FINDING-capx-d14-neiso-t1x-2026-08-30.md): the
first crossover window to execute in-window economic exits produced a retirement
COMPOSITION miss — gas_cc over-retired 3.128 vs 1.884 GW actual, while biomass, coal,
gas_ct and oil exits were missed entirely (recall 2 of 6). Your job is ATTRIBUTION from the
committed artifacts, not repair: why does the economic screen concentrate exits in gas_cc
and never reach the other fuels?
DATA PROFILE: code (widen to neiso only if a required committed artifact is missing).
MODEL: Opus/Fable (rule 27). BRANCH: claude/capx-neiso-rc-phase0 — fresh off origin/main;
check `git ls-remote --heads origin` (the T3 NEISO golden may be in flight — it writes the
NEISO BOARD block and t3 verdict key; you write NEITHER: finding-only lane, no shared
surface).

READ FIRST: the D14 finding (the miss, per-fuel); the committed
neiso-2023-2027-crossover-capxd14 bundle — its evolution ledgers (exits live in TWO keys,
`retirements` AND `confirmed_derates` — the established fact, do not re-derive it), its
per-year screen diagnostics; model-methodology-spec.md §5.2 (the economic screen: attainable
pro-forma inframarginal margin vs FOM-only going-forward cost, per-fuel thresholds,
reliability floor); FINDING-capx-s4b §5.2 (the floor-retention mechanics on these exact
gas-CC tranches).

PRE-DECLARE (commit before measuring): the candidate drivers you will test, e.g. (a) the
screen prices only classes with meaningful energy margins — small biomass/oil/ct classes
may never clear the screen's materiality path; (b) per-fuel FOM/threshold inputs
(gas_ct=2yr, coal=3yr etc.) vs NEISO's actual exit economics; (c) actual exits driven by
non-economic instruments (age/permit/RMR) the forecast has no channel for — a
REPRESENTATION gap, not a tuning gap; (d) the gas_cc over-retirement as the mirror of
(a)-(c): the screen concentrating ALL exit pressure on the one fuel it prices richly.
State ex ante what evidence would distinguish them.

MEASURE from the committed artifacts: per-fuel, the screen's margin inputs, threshold
verdicts and floor interactions for every actual-exit unit the model kept and every modeled
exit the actuals kept; name each miss to a driver. The 2025 price sign-flip year (−21.8%)
overlaps — note any coupling, chase nothing.

DELIVERABLE: docs/handoffs/FINDING-capx-neiso-rc-phase0-<date>.md — the attribution table,
the distinguished driver(s), and ROUTED repair candidates (each named with its admissibility
under rules 13/21/23 — e.g. an announced-retirement instrument intake is rule-23
publication-driven; a tuned threshold is refused on its face). NO mechanism change, NO
ScenarioConfig field, NO matrix cell, NO board edit, NO verdict touch in this phase. Push
per CLAUDE.md; blob-verify ≥300-line files (rule 27). Report to the owner; repair chartering
is the director's next-batch decision on your finding.
```

## D16 — armed-interface mc=0 seam guard (r#19; the S-123-routed latent defect, fail-closed)

```
You are the D16 session of the capacity-expansion (Forecast Finalization Program) track.
Object (S-123 finding §5, routed to the director 2026-08-30): in an armed-interface
FORECAST solve year with no resolvable seam load shape (every year ≥ 2026 at HEAD),
`inject_reference_price_mc` prices nothing and returns False, and the seam band rows keep
the mc = 0 placeholder from `build_reference_price_node` with LIVE bounds — up to ~14.3 GW
of free import capacity (and free export sinks) in the LP. No default or keeper config
reaches this today; any future "arm the reference interface in forecast" experiment would
silently solve on free seams.
THE DIRECTOR'S MECHANISM DECISION, which you execute: FAIL CLOSED — a hard, loud refusal
when an armed reference interface resolves no seam shape for a solve year, in the
established fail-closed pattern (holdout_policy's precedent). The alternative (a flat
gas × HR fallback price) is deliberately NOT built: it would synthesize a price input
needing its own identification and matrix row (rules 5/21/28) — if a future lane wants it,
that is its own charter. A guard that refuses is not a mechanism: no ScenarioConfig field,
no matrix row.
DATA PROFILE: code
MODEL: Opus/Fable (rule 27 — src/market_sim edit). BRANCH: claude/capx-d16-seam-guard —
fresh off origin/main; check `git ls-remote --heads origin` (no in-flight lane touches the
seam path; the golden solves NEISO on its own checkout, unaffected).

THE EDIT: at the seam where `inject_reference_price_mc` returns False for an
armed-interface year (data/neighbor_price.py / import_nodes.py — read the actual seam
before deciding the exact raise site), raise a hard error naming the ISO, year, and the
unresolvable shape (and citing S-123 finding §5) INSTEAD of leaving mc=0 rows with live
bounds. Backcast-armed years covered by the measured seam ladder are UNTOUCHED (the ladder
displaces these rows — verify that path still passes). Regression tests: (a) trivial-case
first (rule: 1 zone/small system) — armed interface + no shape ⇒ the refusal fires; (b)
the ladder-covered backcast path still builds byte-identically; (c) default-OFF forecast
path untouched. Run the repo's fast checks + the touched module's test file.

GUARDRAILS: zero solves; no behavior change on ANY reachable default/keeper path (prove it
via (b)/(c) — byte-identity where feasible); no new tunable (rule 21); no backcast surface
beyond the untouched-path verification; docstrings per rule 11; cite [R-NO-MAGIC]/S-123 §5
at the raise site. Push per CLAUDE.md (HTTP/1.1 retry; API-create a stubborn new branch);
blob-verify ≥300-line files (rule 27).

EXIT: docs/handoffs/FINDING-capx-d16-seam-guard-<date>.md — the raise site, the
unreachability re-verification (the three S-123 lanes), tests. Report to the owner; the
director stamps the ledger.
```

## NEISO-RC-R — the retirement-composition REPAIR phase (r#21; executes the Phase-0 finding's routed repairs R1–R4)

**Model: Fable · DATA PROFILE: neiso · branch: `claude/capx-neiso-rc-repair`**

**Binding basis:** `docs/handoffs/FINDING-capx-neiso-rc-phase0-2026-08-30.md` §6 (routed
repairs, admissibility per item) + §9 (successor instructions). This charter funds the
load-bearing trio **R2 + R1 + R3, with R4 riding along**. R5 (biomass FOM) is DEFERRED —
26 MW in-window, not worth a `ScenarioConfig` field this phase. **R6 stands as the standing
refusal:** no per-fuel FOM constant, execution lag, threshold, or demand-curve parameter is
ever tuned against the retirement-composition residual (rules 21/24).

**Phase A — land the repairs (order matters):**
1. **R2 — FCA sloped-curve re-derivation.** Re-derive the capacity demand curve from ISO-NE's
   PUBLISHED MRI curve / auction parameters (FCA 15–18 clearing evidence, dynamic de-list
   threshold), rule 23 + rule 14; sha-pin every source. The current linear FCA-11 geometry
   pays $0 past 8.3 % surplus where real FCAs cleared $24–43/kW-yr — that $0 is the
   degenerate bar. REFUSED ON ITS FACE if any parameter is identified from the retirement
   residual. Applied to every year consistently (an input repair, the neiso-85/86 pattern —
   not a gated mechanism).
2. **R1 — confirmed-registry intake completion.** (i) Mystic 8/9 FERC cost-of-service/RMR
   end — pin the exact public instrument date against the FERC docket (hindcast information
   gate: applies only where instrument_date ≤ vintage cutoff, per the confirmed-exits
   rules); (ii) re-attempt the EIA-860 identity matches for the held-out de-list-bid rows;
   (iii) restate the instrument bar in terms of ISO-NE's one-year deactivation-notification
   process. NO tunables anywhere in R1.
3. **R3 — scorer trio (MUST land with R1, especially R3(iii)):** (i) the FFR-7C-style
   per-unit NEISO exit decode so D-24 operates on positive evidence; (ii) the
   vintage-consistent crossover retirement target — REPORT BOTH BASES SIDE BY SIDE (the
   signed D-9(ii) additions pattern), never silently replace the basis; any committed
   verdict/determination this flips requires a signed decision card AND the affected lane's
   own re-verification BEFORE the flip publishes (the 2026-08-30 cross-lane re-grade
   ruling); (iii) close the `confirmed_derates` blind spot — `model_retirements` reads only
   the `retirements` ledger key (`scripts/score_capacity_hindcast.py:167-187`) and will
   silently swallow exactly the exits R1 creates on binned NEISO plants.
4. **R4 — decided-in-window retirement reporting (report-only)** + the tracked-set change so
   crossover bundles commit their evolution ledgers (the S-4b bundles already do).

**Phase B — verification (PREREG-first, then at most ONE solve):** pre-declare the
expectation from the finding BEFORE any solve — R2 REDUCES exits by restoring capacity
revenue (reachable-basis level moves from +20 % toward 0) while DE-CONCENTRATING the
composition (the screen discriminates; the floor returns to backstop duty); Mystic becomes
instrument-driven under R1. Then ONE NEISO T1-X crossover treatment run at HEAD against the
committed capxd14 record as control (zero-solve on the control side), scored on the R3
dual-basis scorer, registered on the FORECAST namespace preserve-then-overwrite (the
capxd14-era key preserved under a suffixed name first). Grade the pre-declared expectation
honestly — a miss is recorded, never re-tuned in-lane (R6).

**Collision care:** the T3 golden LANDED mid-sitting (PRs #4447/#4452) — the standing form
remains: never write the t3 verdict key or the bare `neiso-t1f` key (not this lane's keys); `ff-verdicts.json` + `program-status.json` edits touch ONLY the
crossover/capxd14 keys and the NEISO retirement rows they own; rebase before every push and leave the golden's fresh writes intact. Rules 12 (years sequential),
22 (crossover window is diagnostic; no out-of-training backcast year), 27 (blob-verify every
≥300-line push), 28 duties as triggered (R2/R1 are input repairs, no new field; if any step
does add a `ScenarioConfig` field, its matrix row lands in the same PR).

**Exit:** repairs + finding §-updates + verification pair landed and pushed blob-verified;
report the measured composition/level deltas to the director at full magnitude.

## D3 — MISO retirement G3: the t1h `retire.total_gw` PASS→FAIL flip (r#21; cap-grain regression, attribution-first)

**Model: Fable · DATA PROFILE: miso · branch: `claude/capx-d3-miso-retire-g3`**

**Object:** MISO's T1-H `retire.total_gw` gate flipped PASS→FAIL with FFR-3A-3 and stands
untouched — a cap-grain regression on its own tier (board note, `program-status.json` MISO
block). **Charter discipline:** the I13 cobweb closure on the live MISO t1f record is a
SCORER-READ, not an attribution — no session claims to have fixed it and no control isolates
what closed it. Treat "why did I13 close" as an OPEN question inside this lane's evidence
sweep; never cite it as a settled repair. It is NOT the same finding as the G3 flip.

**Phase 0 (zero-solve, precommit-first):** push the precommit (candidate drivers,
distinguishing evidence, adjudication rule, kills) BEFORE measurement. Then attribute the
flip from committed artifacts only: the FFR-3A-3-era t1h record vs its predecessor, the
evolution ledgers where committed, the miso-190/191 unit-vs-bin truths (per-unit exits are
discarded at `fleet_to_bins` — a cap-grain scorer may be measuring a fleet the LP never
carried). Candidate classes to distinguish, stated ex ante: (a) scorer-grain artifact
(cap-grain target vs binned-fleet execution — the miso-191 keeper changed exit delivery); (b)
real retirement-volume regression introduced by FFR-3A-3; (c) basis/vintage misalignment (the
NEISO-RC §2.1 class). Disclosure duty: the live ffr3a3/-3a4 gate keys carry known mismeasured
co2 rows with bundles never committed (D5-R annotation) — work from what is committed and
name what is not, rather than regenerating history.

**No mechanism, no tuning, no solve in Phase 0.** If attribution requires an A/B, STOP at the
finding and route it — the solve is a separate director decision. Collision: `miso-193` (cc_duct_peaking, BACKCAST track) is mid-A/B at issuance — distinct
namespace from this lane's forecast-board object; proceed, but never touch miso-193's
surfaces (its PREREG, scorer, or backcast registrations); re-run the collision check at
start for anything newer. Rules 22/25/27/28 as always.

**Exit:** finding with the attributed driver class + routed repair (or a clean adjudicated
"scorer-grain, repair = R3-style dual-basis reporting"), board note refreshed on the MISO
G3 row only, pushed blob-verified.

## D4-I3 — ERCOT I3 scarcity-slack invariant, HALF SCOPE (r#21; the net-revenue half stays HELD under card Y-C)

**Model: Opus · DATA PROFILE: ercot · branch: `claude/capx-d4i3-ercot-slack`**

**Scope boundary first:** card Y is signed **Y-C** (hold open) — this lane owns ONLY the I3
scarcity-slack invariant half. The net-revenue half is HELD; do not touch, measure, or
re-open it.

**Prior (binding, from `docs/forecast-readiness-audit-2026-07.md` FR-6):** ERCOT I3 slack =
LP unserved energy at VOLL (`lp/bounds.py:193-194`, `lp/costs.py:127-134`); the adequacy
backstop is disabled for energy-only ERCOT BY DESIGN (`adequacy.py:258-266`), so a one-pass
under-build has no corrective and lands as slack (0.01–0.03 % of load, 2027–2030). The cause
"lives only in memos; no code comment marks it."

**Phase 0 (zero-solve, on committed artifacts only):**
1. Measure the I3 breach set at each committed ERCOT T1-H record (the D11-R and D12-C A/B
   bundles carry the arm/control pairs): slack MW/hours by year, attributed to under-build
   vs entry-timing vs curve shape, control vs arm deltas.
2. **Pre-declare (not measure) the post-arming expectation:** D12-A armed
   `entry_margin_exhaustion` + `entry_forward_reserve_leg` as ERCOT forecast defaults —
   state ex ante, from the committed A/B deltas, what the armed pair should do to I3.
   The post-arming MEASUREMENT belongs to the next chartered T1-H run (D6 or a director
   decision) — no solve in this lane.
3. **Give the cause a code home:** add the FR-6-cited design-intent comment at the
   `adequacy.py` energy-only seam (comment/docs only, zero behavior change) so the
   by-design disable stops living only in memos.
4. Route (never build) the repair options for the director — e.g. an energy-only-aware
   backstop variant, scarcity-revenue-consistent entry timing — each with its rules-13/21
   admissibility stated.

Collision: ERCOT surfaces free at issuance (D12-A-R landed, ercot-245 concluded); D6 is held
partly on contention with this lane — land promptly. Rules 22/25/27/28 as always; matrix
duty (a) only (no mechanism tested).

**Exit:** finding + breach-set tables + the pre-declared arming expectation + the code
comment, board I3 row refreshed (ERCOT block only), pushed blob-verified.

## D8-RE — the deferred verdict/board re-emission (r#21 mid-sitting release; records only)

**Model: Opus · DATA PROFILE: code · branch: `claude/capx-d8-re-emission`**

**Basis:** D8 landed its two halves (PR #4427, `FINDING-capx-d8-dof-ledger-2026-08-30.md`)
with ALL verdict/board re-emission EXPLICITLY DEFERRED because three in-flight lanes wrote
those files on other keys. All three writers have now LANDED (S-6 PR #4436 · S-123-V
PR #4441 · the T3 golden PRs #4447/#4452), so the deferral is discharged. Execute exactly
the re-emission the D8 finding names — no more: re-emit the FC-7/DOF-ledger-touched verdict
records and board fields from the COMMITTED instrument + artifacts (zero-solve,
`forecast_verdict.py` / board tooling on committed inputs only), preserving every
provenance note the finding requires. Take the file state at your HEAD as authoritative —
the S-6/S-123-V/golden writes are newer than D8's deferral and are NEVER overwritten or
"restored"; if a key the finding expects to re-emit was since rewritten by one of them,
re-emit ON TOP of the live value only where the finding's instrument output actually
changes it, and record any key you therefore skip. Any re-emission that would FLIP a
committed verdict/gate is a STOP — the cross-lane re-grade ruling (2026-08-30) requires the
affected lane's re-verification before such a flip publishes; report it to the director
instead of landing it. Rebase before pushing; rules 22/27 as always; no mechanism, no
matrix cell (rule 28 duty (a) only). **Exit:** re-emitted records + a short completion note
appended to the D8 finding, pushed blob-verified.

## D8 — forecast DOF-ledger instrument + provenance debt (r#19; FC-7's two halves; verdict re-emission DEFERRED)

```
You are the D8 session of the capacity-expansion (Forecast Finalization Program) track.
ZERO SOLVES. FC-7 has two halves, and you build both WITHOUT re-emitting any verdict:
(1) THE DOF-LEDGER INSTRUMENT — the program-wide gap every T1-F leg carries as its
CAVEAT (now NEISO's ONLY caveat, so this instrument is what stands between the program's
best ISO and a clean FC map). Build scripts/build_forecast_dof_ledger.py: for a registered
forecast bundle (its committed run_config.json + resolved config), enumerate every free
parameter that entered the solve with its identification source — the rule-21 keeper
discipline, forecast-side: registry citation (constants.py/ScenarioConfig cite comments),
derive-script provenance, or published-source intake finding. A parameter with NO
identifiable source is listed as UNIDENTIFIED — that is the instrument's point, never
paper over one. Emit a committed per-bundle ledger artifact (dof_ledger.json beside the
sidecar) + a human-readable table in the finding. Generate ledgers for the LIVE t1f
bundles (NEISO s4b-ara, NYISO, MISO, PJM — and the s6/s123v bundles if they have landed
by your start; skip in-flight ones).
(2) THE LEGACY PROVENANCE DEBT — the seven legacy legs tracking no run_config.json
(FC-7 FAIL shape). For each: reconstruct the run_config from committed evidence (sidecar
meta, resolved config, finding) where honestly recoverable — labelled RECONSTRUCTED with
its evidence chain, never presented as original — else document IRRECOVERABLE with what
is missing. Commit what is recoverable.
DEFERRED, EXPLICITLY: NO FC-7 re-score, NO ff-verdicts.json write, NO board edit — three
in-flight lanes (golden, S-6, S-123-V) are writing those files on other keys; the
re-emission is a small follow-up the director charters once they land. Your deliverable
is the instrument + artifacts + finding.
DATA PROFILE: code
MODEL: Opus/Fable (rule 27 — new scripts/ instrument). BRANCH: claude/capx-d8-dof-ledger —
fresh off origin/main; check `git ls-remote --heads origin`.

GUARDRAILS: zero solves; read-only against every model surface; no measured-outcome
feedback (rule 13); the ledger REPORTS identification, it never supplies one (rule 21); no
verdict/board/backcast surface; tests for the instrument (trivial fixture bundle first);
docstrings (rule 11). Push per CLAUDE.md (HTTP/1.1 retry; API-create a stubborn new
branch); blob-verify ≥300-line files (rule 27).

EXIT: docs/handoffs/FINDING-capx-d8-dof-ledger-<date>.md — the instrument's contract, the
per-bundle ledger tables (UNIDENTIFIED rows highlighted), the legacy-leg
recovered/irrecoverable table, and the deferred re-emission note. Report to the owner.
```
