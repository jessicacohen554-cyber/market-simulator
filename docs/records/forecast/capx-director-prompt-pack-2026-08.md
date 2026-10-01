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

> **r#22 status note (director, 2026-08-31):** nothing from this lane has landed and no
> branch `claude/capx-neiso-rc-repair` exists on the remote. Under the r#20/r#21 relaunch
> protocol this is NOT graded lost — a solve-carrying lane lands nothing observable until it
> finishes, and the T3 golden was wrongly graded on exactly this evidence. The owner has been
> asked whether the session is still running (ledger §0s.6). This charter stays BINDING and
> UNCHANGED either way: if the session is gone it relaunches FRESH from this text; if it is
> running, nobody launches a second one.

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

---

## D8-V — FC-7 ledger completion: publish the two stopped flips, close PJM + MISO (r#22; executes D8-RE's routed set)

```
You are the D8-V FC-7 LEDGER COMPLETION session of the capacity-expansion (Forecast
Finalization) track. Lane D8 built the DOF-ledger instrument; lane D8-RE re-emitted one key
and STOPPED two committed-verdict flips under the 2026-08-30 cross-lane re-grade rule, routing
them to the director. You execute the routed set: re-verify and publish those two flips, and
close the PJM and MISO ledgers D8-RE measured read-only. ZERO SOLVES — every number is
forecast_verdict.py's own output on committed artifacts.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (two ISO determinations move — adjudication, rule 27 / model economy).
BRANCH: claude/capx-d8v-fc7-ledger — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d8-dof-ledger-2026-08-30.md §6 (the pre-registration)
and §8 (D8-RE's completion note: §8.1's byte-for-byte control, the two stops, the measured
PJM/MISO ledger contents); frontend/data/forecast/program-status.json block `d8_re_emission`
(`stopped_not_landed` + `routed_to_director`); docs/handoffs/capx-director-ledger-2026-08.md
§0s.

THE CONTROL COMES FIRST, ON EVERY KEY YOU TOUCH (D8-RE's own protocol, repeated — do not
skip it because D8-RE already ran it): re-score the key on its committed artifacts WITHOUT
--dof-ledger and confirm it reproduces the committed record byte-for-byte apart from the
provenance stamp. If any key fails to reproduce, that is a stop-the-line finding — report it
and touch nothing.

TASK 1 — NEISO (`neiso-t1f`, affected lane capx-S4b-neiso-ara). Re-derive FC-7 from
results/ff-t1f-s4b-ara/neiso/ with the documented command
(`python scripts/forecast_verdict.py --tier t1f --summary <bundle>/full_horizon_summary.json
--run-config <bundle>/run_config.json --dof-ledger <bundle>/dof_ledger.json`). The
pre-registered movement is FC-7 'dof ledger' CAVEAT -> PASS and DETERMINATION
PROMOTE-WITH-CAVEATS -> PROMOTE with caveats []. PUBLISH ONLY IF the re-verification
reproduces exactly that and NOTHING ELSE MOVES — assert row-by-row that every other FC
category, row status and detail is byte-identical before writing. Record the re-verification
in the S-4b lane's own finding (docs/handoffs/FINDING-capx-s4b-neiso-ara-2026-08-30.md, an
appended addendum) — the cross-lane rule requires the AFFECTED lane's record, not just yours.
If anything else moves: STOP, publish nothing, report at full magnitude.

TASK 2 — NYISO (`nyiso-t1f`, affected lane capx-D2-extcap-intake). Identical shape on
results/ff-t1f-extcap/nyiso/. Same publish condition, same stop condition; the addendum goes
in that lane's finding.

TASK 3 — PJM (`pjm-t1f`). Build the ledger from results/ff-t1f-s6-pjm/ledger/ with
scripts/build_forecast_dof_ledger.py, COMMIT it into the bundle, and re-score. D8-RE measured
1 entry / 0 UNIDENTIFIED => FC-7 CAVEAT -> PASS with DETERMINATION UNCHANGED (HOLD, held by
the FC-1/FC-2 FAILs). That is NOT a stop. If the determination moves anyway, it becomes one:
stop and report.

TASK 4 — MISO (`miso-t1f`). Same build on results/ff-t1f-s123/verify/, commit the ledger, and
re-score. D8-RE measured 4 entries with 3 UNIDENTIFIED (entry_vre_capacity_revenue,
miso_clean_tier_rows, miso_rps_compliance_regions) => FC-7 STAYS CAVEAT, no verdict movement.
Commit it regardless: the value is the named attestation debt, which is the instrument working
as designed. Name those three as routed debt in your finding — do NOT attest them, and do NOT
invent an identification source to clear them (rule 21 [R-DOF]: a residual that can only be
closed by a tuned value is an open issue, not a parameter).

BOARD. Refresh only the NEISO / NYISO / PJM / MISO FC-7 blocking rows you actually moved, plus
one `d8_v_ledger_completion` lane block. Assert PROGRAMMATICALLY before commit, exactly as
D8-RE did: every ISO determination you did not move, every fc map, every keeper/marker/golden
field, every §2.1b gate cell (status AND detail) and every prior lane block byte-identical.

NOT YOURS — HARD BOUNDARIES. The seven legacy legs' reconstructed run_configs
(results/run-config-debt/) are a SEPARATE director decision, now ruled (ledger §0s.5): DO NOT
adopt them and do not touch their FC-7 rows. Do not create a ledger where none exists
(ercot-t1f, caiso-t1f, neiso-t1f-s4hydro, neiso-t1f-s4control, any -ff2d / -ffr3a2 vintage) —
D8-RE recorded those as correctly skipped. Never write `neiso-t3`, any crossover/t1x key, or
the ERCOT block: the NEISO crossover keys belong to NEISO-RC-R if it is in flight, and the
ERCOT block belongs to lane D4-M, which is dispatched in the same batch. Fetch and rebase
before every push and leave sibling writes intact.

GUARDRAILS: zero solves. Backcast namespace untouched — no keeper shard, no status/*.js, no
calibration-complete.json, no registry/runs sidecar. No holdout year of any tier is solved,
scored or registered. No mechanism, no ScenarioConfig field, no matrix cell (rule 28 not
triggered — nothing is tested). No new GitHub Actions workflow. Push per CLAUDE.md Git &
Pushing; blob-verify every ≥300-line file after push (rule 27) — ff-verdicts.json and
program-status.json both qualify.

EXIT: docs/handoffs/FINDING-capx-d8v-fc7-ledger-<date>.md carrying the four controls, the two
re-verifications with their published/stopped verdicts, the PJM/MISO ledger contents and the
MISO attestation debt; the two affected lanes' finding addenda; the board block. Report to the
director: which determinations moved, and the MISO debt list.
```

---

## D4-M — ERCOT post-arming T1-H measurement + the I3 instrument grain (r#22; the measurement half D4-I3 pre-declared)

```
You are the D4-M session of the capacity-expansion (Forecast Finalization) track. Lane D4-I3
measured the ERCOT I3 breach set zero-solve and FROZE an eight-point pre-declaration for the
first T1-H run at the newly-armed D12-A posture. You run that measurement and grade the
pre-declaration. It also lands the cheap instrument repair D4-I3 recommends doing FIRST.

DATA PROFILE: ercot
MODEL ASSIGNMENT: Opus (the discretion was spent ex ante in D4-I3 §4 — this is EXECUTION under
the r#20 model-economy doctrine; rule 27's Sonnet floor still bars Sonnet from scripts/).
BRANCH: claude/capx-d4m-ercot-t1h — create FRESH off origin/main (git fetch origin main first)
and rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md — §2 (the
volume↔slack monotonicity, the load-bearing claim), §4 (P-1..P-8 and F-1..F-4 — FROZEN; you
grade them, you never restate, widen or reinterpret them), §5.1 (the vintage caveat: an ERCOT
I3 magnitude is comparable only WITHIN a solve vintage — do not difference your result against
the 2026-08-22 `refresh` record), §5.2 + §6 R-4 (the instrument gap), §6 R-2 (why the
entry-volume question comes AFTER this run, never fitted to I3).

STAGE 1 — R-4, the instrument grain (do this first, land it before the run is scored).
Extend `check_i3_unserved_dump` in scripts/check_forecast_invariants.py so its detail carries
BREACH HOURS, SLACK GWh and PEAK SLACK MW alongside the existing `% of load`. DO NOT TOUCH the
1e-4 gate — the threshold is not yours and moving it would be a gate change dressed as a
reporting change. Existing committed sidecars keep their coarse strings; only newly written
ones gain the grain. Trivial fixture test first (CLAUDE.md Testing Pattern), then the suite.

STAGE 2 — the run. ONE ERCOT T1-H `ercot-2021-2025-realized` leg at the REGISTERED posture at
HEAD, years sequential within the invocation (rule 12). The D12-A pair is now the ERCOT
forecast DEFAULT, so a bare invocation IS the armed posture — assert it from the run's own
run_config.json (`entry_margin_exhaustion` and `entry_forward_reserve_leg` both True) BEFORE
grading anything; that assertion is F-1's first clause. The control side is the COMMITTED
`ercot-2021-2025-realized-t1h-d12c-control` record — zero-solve, no new control run. If your
solve reproduces `d12c-armed` exactly, SAY SO PLAINLY: that is the confirmation arriving for
free, not a failure to measure something new, and the new instrument grain is then the run's
actual novel content.

STAGE 3 — grade P-1..P-8 honestly, one row each, measured vs pre-declared, at full magnitude.
Report any of F-1..F-4 that fires as a contradiction of the pre-declaration, in its own
section, and do not repair it in-lane. P-8 is flagged in its own charter as UNBRACKETED — if
you cannot reach the T1-F horizon zero-solve, record it unmeasured rather than estimating it.

HOW TO READ A WORSE I3 — this is the part that matters, and D4-I3 §4 states it as binding:
a worse I3 under the armed pair is NOT a regression and MUST NOT be repaired by re-disarming,
by a volume knob, or by any parameter moved to close the breach. Rules 1 [R-STRUCT] and 14
[R-ACCURATE]: both levers are structurally-motivated corrections, and I3 rising is a
pre-existing under-build becoming visible. Your lane's job ends at measuring it.

REGISTRATION (rule 15, forecast namespace): register the run with run_config.json committed,
and — in the SAME commit as the registration — declare its invariant FAILs in
frontend/data/hindcast/invariant-failures.json, per that file's own `how_to_update`, naming
this finding. THAT LINE IS YOURS AND ONLY YOURS: lane D18 is dispatched in the same batch and
owns exactly the 13 PRE-EXISTING undeclared rows enumerated in its charter. Do not touch a row
you did not create; rebase and leave D18's sweep intact.

NOT YOURS: the net-revenue half of the I3 object stays HELD under card Y-C (signed) — do not
touch, measure or re-open it. The R-2 entry-screen volume calibration is a LATER lane and is
explicitly forbidden here; any volume parameter fitted to close I3 or I12 is inadmissible
(rule 13 [R-MEASURED]). Do not adjudicate the non-ERCOT I3 rows (MISO, NEISO) — rule 25
[R-ISO-SCOPE], they belong to their own ISO lanes. Board: the ERCOT block only; lane D8-V is
writing NEISO/NYISO/PJM/MISO FC-7 rows of the same two files in this batch — distinct
blocks/keys, rebase-care, leave its writes intact.

GUARDRAILS: no out-of-training backcast year solved, scored or registered (the T1-H hindcast
window is the forecast namespace, not a backcast holdout — keep it that way). No measured
outcome fed back (rule 13). Touch no backcast keeper shard, status/*.js,
calibration-complete.json, offer curve or commitment bridge. No new GitHub Actions workflow,
no CI offloading — the solve runs in your session. Push per CLAUDE.md Git & Pushing;
blob-verify every ≥300-line file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d4m-ercot-t1h-<date>.md with the R-4 diff, the posture
assertion, the P-1..P-8 grade table, any fired falsifier, the registration + declaration, and
the ERCOT board refresh. Report to the director whether the pre-declaration held.
```

---

## D17 — MISO's missing non-coal economic exit channel (r#22; D3's routed PRIMARY, Phase 0, zero-solve)

```
You are the D17 session of the capacity-expansion (Forecast Finalization) track, executing the
PRIMARY repair D3 routed. PHASE 0 ONLY: attribution from committed artifacts, ZERO SOLVES,
precommit-first. You build nothing and arm nothing.

DATA PROFILE: miso
MODEL ASSIGNMENT: Fable (novel-object adjudication and mechanism candidacy — rule 27 / model
economy).
BRANCH: claude/capx-d17-miso-exit-channel — create FRESH off origin/main (git fetch origin
main first) and rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d3-miso-retire-g3-2026-08-31.md — §5 (the per-fuel
table that IS the object) and §6.1 (the four candidate threads, none presumed);
docs/handoffs/PRECOMMIT-capx-d3-miso-retire-g3-2026-08-31.md (the precommit discipline you
repeat); docs/handoffs/FINDING-capx-s123-miso-adequacy-2026-08-30.md (the S-1/S-2/S-3
requirement terms thread (iii) depends on).

THE OBJECT, stated exactly as D3 measured it: over the MISO T1-H window the economic screen
executes ZERO gas_ct, gas_cc and oil exits — model 0.0 GW against actual 2.435 / 0.521 / 0.502
GW, i.e. 3.458 GW of real non-coal exits the screen never produces — while it OVER-retires
coal (+9.1 % after the G3 fix, +18.4 % before). The −16.5 % `retire.total_gw` FAIL is that
missing channel becoming visible once the G3 cap-grain fix removed the compensating coal
excess. THE FIX STAYS (rules 1 [R-STRUCT] / 14 [R-ACCURATE]): restoring the decision-year cap
grain, or reporting a dual basis to recover the old PASS, is REFUSED ON ITS FACE. The pre-fix
PASS is not a target.

PRECOMMIT FIRST — push it before you measure anything. It names, frozen: the candidate classes
you will test, the committed evidence for each, the adjudication rule, and the kill that
retires each candidate. D3 §6.1 offers four threads and presumes none — (i) the attainable
pro-forma inframarginal margin for MISO gas/oil (whether modelled energy/AS margins
over-reward these classes against FOM); (ii) per-fuel threshold / execution-lag
identification for gas_ct/gas_cc/oil against the EIA-860 record; (iii) the admission cap's
REQUIREMENT side in the hindcast window — S-123 established the t1f requirement basis was
overstated (PRM 0.179→0.157, external ZRC, DR netting) and the hindcast-window analogue has
never been measured; (iv) FFR-3F §1.4's recorded open item, that the cap's fleet side stays at
decision year with no entry crediting, biasing toward retention. Add or drop candidates on
your own reading of the artifacts — but freeze the set before you look at the answer.

EVIDENCE IS COMMITTED-ARTIFACT ONLY: the evolution ledgers, floor_retention_log attributions,
score.json / scorecards, the FFR-2B pipeline bundle, the battery-close docs, EIA-860. If a
question needs a solve, say so and route it — do not run one.

WHAT THIS MUST NEVER BECOME (state it in the precommit and hold to it): no per-fuel FOM
constant, retirement threshold, execution lag or margin adder identified from the retirement
residual — rule 21 [R-DOF] and rule 24 [R-REGISTRY]; that is the standing refusal NEISO-RC
carries as R6 and it binds here identically. A residual that can only be closed by a tuned
value is an open root-cause issue, not a parameter.

GUARDRAILS: zero solves. No mechanism, no ScenarioConfig field, no matrix cell — nothing is
tested, so rule 28 duty (b) is not triggered; check the MISO shard and lever queue before you
propose anything (duty (a)) and never re-test a cell adjudicated R/I/G. No board write, no
verdict/gate flip, no keeper/shard/marker touch — D3's own §6.3 established the FC-3 verdict
is correct as it stands. Backcast namespace untouched. No holdout year. No new GitHub Actions
workflow. Push per CLAUDE.md Git & Pushing; blob-verify every ≥300-line file (rule 27).

COLLISION: the backcast MISO track is the owner's; check `git ls-remote --heads origin` at
start and stay off any live MISO backcast branch's surfaces. Lane D8-V writes `miso-t1f`'s
FC-7 row in this same batch — you write no verdict file at all, so there is no contention.

EXIT: docs/handoffs/PRECOMMIT-capx-d17-miso-exit-channel-<date>.md (pushed first) and
docs/handoffs/FINDING-capx-d17-miso-exit-channel-<date>.md with the attribution, each
candidate's verdict against its own frozen kill, and the repairs ROUTED — priced, admissibility
stated per rule 13 / rule 21, and NOT built. Report to the director.
```

---

## D18 — the invariant declaration ledger sweep (r#22; D4-I3's routed R-6, records only)

```
You are the D18 session of the capacity-expansion (Forecast Finalization) track. This is a
RECORDS lane: it makes a standing-red CI job green by declaring what is already committed, and
it corrects one misattributing line. It adjudicates nothing and fixes no defect.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (enumerated records sweep, no adjudication; rule 27 keeps Sonnet off
scripts/ and CI-adjacent artifacts).
BRANCH: claude/capx-d18-invariant-ledger — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md §5.3 (the routed R-6 and
its boundary); frontend/data/hindcast/invariant-failures.json — its own `purpose`,
`how_to_update`, `capentry_note` and `c1joint_note`.

THE OBJECT. `scripts/check_forecast_invariants.py --sidecar-dir frontend/data/hindcast` (CI job
`forecast-invariant-artifacts`, FR-24) fails when a committed sidecar carries an invariant FAIL
absent from `declared_failures`. THIRTEEN rows are currently undeclared. The census was
measured by D4-I3 and INDEPENDENTLY RE-DERIVED by the director from the committed sidecars —
both agree on exactly these:

  caiso-2021-2025-realized                      I7, I9
  ercot-2021-2025-realized-t1h-d11r-control     I3
  ercot-2021-2025-realized-t1h-d11r-exhaustion  I3
  ercot-2021-2025-realized-t1h-d12c-armed       I3
  ercot-2021-2025-realized-t1h-d12c-control     I3
  ercot-2021-2025-realized-t1h-refresh          I3
  miso-2026-2030-s123-verify                    I3
  neiso-2021-2025-realized-k99                  I6
  neiso-2021-2025-realized-mystic-rescore       I6
  neiso-2026-2050-t3-golden-bau                 I3
  pjm-2021-2025-realized-exante-control         I7
  pjm-2021-2025-realized-verified-exits         I7
  pjm-2026-2030-s6-ledger                       I7, I12

VERIFY IT YOURSELF FIRST by running the checker (this director container lacks numpy; yours
should not) and reconcile any difference before writing — if your census differs from the list
above, report the difference rather than silently adopting either.

TASK 1 — declare each row, naming the finding or lane it belongs to, per `how_to_update`. A
declaration is NOT absolution: the file's own purpose says an invariant FAIL is a root-cause
finding, so each line must point at a real record. WHERE NO FINDING EXISTS, SAY SO EXPLICITLY
in the note rather than inventing an attribution — an honest "registered by lane X, cause
untracked" is correct and useful; a fabricated citation is not. Do not delete a row's sidecar
and do not touch `cleared`.

TASK 2 — correct `dominant_open_causes.I3`. It currently reads "FR-6 ERCOT energy-only
scarcity slack, structural and unowned in code", i.e. it treats I3 as ERCOT-only. Two committed
NON-ERCOT runs now carry an I3 FAIL — `miso-2026-2030-s123-verify` and
`neiso-2026-2050-t3-golden-bau` — and FR-6's cause CANNOT explain either, because MISO and
NEISO are capacity-market ISOs where `resolve_reserve_margin_build_enabled` returns True and
the adequacy backstop is armed. Rewrite the line so it no longer misattributes those rows.
DO NOT ADJUDICATE THEIR ACTUAL CAUSE: that is each ISO's own lane's work under rule 25
[R-ISO-SCOPE]. Name the open question; do not answer it.

TASK 3 — run the checker again and report it GREEN, with the command and its output in your
finding. If it cannot go green without a change outside this charter, stop and report that
instead of widening scope.

BOUNDARIES. Lane D4-M is dispatched in the same batch and will register a NEW ERCOT T1-H run,
declaring its own row in this same file in the same commit as its registration. You own ONLY
the 13 pre-existing rows listed above. If D4-M lands first, rebase and leave its row untouched;
never re-declare or re-word another lane's line. Touch no verdict file, no board block, no
keeper/shard/marker, nothing in the backcast namespace, and no invariant THRESHOLD anywhere —
this lane changes no gate and no scorer behaviour.

GUARDRAILS: zero solves. No mechanism, no ScenarioConfig field, no matrix cell (rule 28 not
triggered). No holdout year. No new GitHub Actions workflow — you make the existing job pass,
you do not add one. Push per CLAUDE.md Git & Pushing; blob-verify every ≥300-line file after
push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d18-invariant-ledger-<date>.md with the verified census, the
13 declarations and what each cites, the corrected `dominant_open_causes` line, and the green
checker output. Report to the director: how many declarations point at a real finding and how
many are honestly untracked.
```

---

## D21 — FC-6 driver battery: the t3 ceiling, half 1 (r#22; executes owner rulings Q16/Q19)

```
You are the D21 session of the capacity-expansion (Forecast Finalization) track. You build half
of the reason no golden run can currently be graded. FC-5 and FC-6 are REQUIRED at tier t3 and
neither instrument exists for ANY ISO, so `neiso-t3` scores HOLD regardless of model quality —
the owner ruled (Q16, 2026-08-31) that the ceiling is fixed BEFORE any second golden campaign,
FC-6 first because its tooling already exists and the gate is merely UN-RUN.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (the vacuous-pass and ladder-gating calls are judgment on a novel
object).
BRANCH: claude/capx-d21-fc6-battery — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: docs/forecast-determination-rubric.md §FC-6 (the four row types and their
thresholds — that section IS your spec, and you add nothing numeric of your own to it);
docs/handoffs/driver-battery-2026-07-12.md (the pre-registered ladder expectations and the
T1.6a/T1.7a vacuous-pass findings); docs/handoffs/FINDING-capx-t3-neiso-golden-2026-08-30.md
(the campaign whose FC-6 row you are filling) + the `t3_golden_campaign` block of
frontend/data/forecast/program-status.json.

STAGE 1 — PRICE THE LADDER BEFORE YOU RUN IT. `scripts/run_driver_battery.py` solves a rung
per ladder step; the full Tier-1 battery at a 2026–2050 config vintage could be far larger than
one session. Measure the cost first (rungs × horizon × per-solve time from the golden's own
29.2 min record), write it down, and IF THE FULL BATTERY DOES NOT FIT, STOP AND REPORT with the
priced options rather than running a truncated ladder and calling it the battery. A partial
battery is a CAVEAT at best and must never be presented as the gate being met.

STAGE 2 — run what you priced: the Tier-1 monotonicity ladders at the golden bundle's config
vintage, plus the paired invariants P1–P3 (`check_forecast_invariants.py --paired`). Commit the
machine output into the golden bundle so FC-6 reads a committed artifact, never a session
transcript.

STAGE 3 — re-score `neiso-t3` and let the rubric's own rows decide. Binding, from §FC-6:
a `gate`-marked ladder expectation that FAILs ⇒ FC-6 FAIL; **a gate row that passed on an
empty or all-constant series is a CAVEAT, NEVER a PASS** (check `n_rungs_solved` and the
constant-series flag; trust an explicit `vacuous` marker otherwise) — the 2026-07-12 report's
own instruction is that a vacuous pass must not be cited as confirmation; P1 or P2 FAIL ⇒ FAIL;
P3 WARN ⇒ CAVEAT. Report the outcome at full magnitude. **A FAIL here is a good outcome for the
program** — it is the instrument working — and must not be softened, re-run for a better draw,
or tuned toward. Nothing in the model moves in this lane.

WHAT THIS LANE DOES NOT DO: it does not re-solve the golden (Q16 HOLDS that — the campaign
stands as registered with its posture-epoch caveat visible, and nothing quotes it as a post-R-A
result), it does not touch FC-5 (lane D22), and it does not change a threshold, band or
expectation anywhere. If the battery's own pre-registered expectations look wrong to you,
report that as a finding — do not edit them.

COLLISION: you write `neiso-t3`'s FC-6 row and the golden bundle. Lane D8-V is explicitly
barred from `neiso-t3`; lane D4-M is ERCOT-only; NEISO-RC-R has LANDED (PR #4467) so its
`neiso-t1x` preserve-then-overwrite is settled history — rebase onto it, never re-write it.
Touch no other ISO's block.

GUARDRAILS: no out-of-training backcast year solved, scored or registered. No measured outcome
fed back (rule 13). Touch no backcast keeper shard, status/*.js, calibration-complete.json,
offer curve or commitment bridge. No mechanism, no ScenarioConfig field, no matrix cell (rule
28 not triggered — nothing is tested; check the NEISO shard under duty (a) if you propose
anything). Rule 12: years sequential within the invocation. No new GitHub Actions workflow —
the battery runs in your session. Push per CLAUDE.md Git & Pushing; blob-verify every ≥300-line
file after push (rule 27).

EXIT: docs/handoffs/FINDING-capx-d21-fc6-battery-<date>.md with the ladder pricing, what was
run, the committed artifact path, the row-by-row FC-6 verdict (vacuous passes named as such),
and the re-scored `neiso-t3`. Report to the director whether FC-6 can now grade a golden, and
what it says about this one.
```

---

## D22 — FC-5 benchmark corridor: the t3 ceiling, half 2 (r#22; executes owner rulings Q16/Q19)

```
You are the D22 session of the capacity-expansion (Forecast Finalization) track, building the
other half of the t3 ceiling. FC-5 scores SKIPPED for every ISO because the benchmark tables it
reads DO NOT EXIST on disk — the corridor memo was built from web fetches, which is not
reproducible scoring input. You make them exist.

DATA PROFILE: code (widen if an intake needs it)
MODEL ASSIGNMENT: Opus (a new curated datatype + fetch/curate scripts is infrastructure; rule
27 keeps Sonnet off everything but purely additive data-intake).
BRANCH: claude/capx-d22-fc5-corridor — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: docs/forecast-determination-rubric.md §FC-5 (the metric, the 15 %/opposite-sign
divergence trigger, the IN CORRIDOR / EXPLAINED DIVERGENCE / UNEXPLAINED row verdicts) and
**§6, the benchmark inventory — that section is your work order**, listing what is already on
disk, the eight intake gaps, and the schema in item 9;
docs/handoffs/cross-model-corridor-2026-07-13.md (the divergence-explanation discipline being
imported whole). Then the `data-intake` skill, whose contract this lane follows exactly.

SCOPE — DATA CONTRACT AND INTAKE ONLY. Build:
1. The curated `benchmark-corridor` datatype: `data/dictionary/schema/benchmark-corridor.schema.yaml`
   with columns {iso, source, vintage, target_year, quantity, tech?, value, unit, note}, the
   data-dictionary entry, and the curate script through the write_clean/read_clean seam with
   tmp-CLEAN_DIR tests (per the skill; no `if iso ==` ladders — per-ISO registry modules).
2. As many of rubric §6's eight sources as land cleanly, STARTING WITH (1) EIA AEO2025 regional
   electricity projections, which already has an API route — extend
   `scripts/data/fetch_eia_aeo.py`; the existing `eia-aeo-fuel-prices` datatype is the pattern.
   Raw downloads are immutable under `data/raw/` and never modified in place.
3. An honest coverage record: which of the eight are in, which are not, and WHY. Where a source
   is retrievable only at a coarser grain than the model's ISO regions (§6 flags this risk for
   NREL Standard Scenarios), **record the limitation in the table rather than downscaling it** —
   an invented regional split would be a fabricated benchmark.

DO NOT EDIT THE SCORER. `scripts/forecast_verdict.py`'s FC-5 read path is explicitly OUT of
scope and belongs to a later lane. Two reasons, both binding: lane D8-V is running live
re-scores through that file in this same batch and its controls are byte-for-byte, so a
behaviour change under it would confound a determination; and FC-5's current SKIPPED-with-
missing-source-list behaviour is CORRECT until the tables exist. Land the data; the wiring is
its own charter.

THE RULE THAT GOVERNS THIS WHOLE LANE: **benchmarks are context, never fit targets** (rule 13
`[R-MEASURED]`, plan §7.6, rubric §FC-5 rationale). Nothing you intake may become a target any
model quantity is moved toward, and the rubric deliberately makes conformance non-numeric for
exactly this reason — what gates is the EXPLANATION discipline, not closeness. Do not add a
numeric conformance band; do not rank ISOs by corridor distance; do not tune anything, ever, to
a benchmark row. Also explicitly REJECTED by the rubric's own methodology section and not to be
imported: ReEDS' practice of adjusting cost coefficients until generation matches history.

GUARDRAILS: zero solves. No mechanism, no ScenarioConfig field, no matrix cell (rule 28 not
triggered). No verdict file, no board block, no keeper/shard/marker, nothing in the backcast
namespace. No holdout year. Every intaken value is sha-pinned to its published source with a
citation (rule 23 / docs/parameter-citations.md discipline) — a benchmark whose provenance you
cannot state does not go in. No new GitHub Actions workflow; fetches run in your session. Push
per CLAUDE.md Git & Pushing; blob-verify every ≥300-line file after push (rule 27), and mind
the pack-size guidance if a raw download is large — a corpus payload may need the gitignored-
with-README treatment (CLAUDE.md "Cloning & session data").

EXIT: docs/handoffs/FINDING-capx-d22-fc5-corridor-<date>.md with the schema, the per-source
coverage record (in / out / why), the committed table, and a statement of what FC-5 will be
able to score once its read path is wired. Report to the director which of the eight sources
remain, and whether any of them is unreachable rather than merely un-fetched.
```

---

## D19 — board reconcile 2 (r#23; released once D8-V and D4-M landed)

```
You are the D19 BOARD RECONCILE session of the capacity-expansion (Forecast Finalization)
track. This is a RECORDS lane, the D13 successor. It makes the board tell the truth about a
program that has moved under it. It adjudicates nothing, re-scores nothing and solves nothing.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (deciding what a stale cross-ISO sentence should now say is judgment,
and several touch determinations).
BRANCH: claude/capx-d19-board-reconcile-2 — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: `docs/handoffs/capx-director-ledger-2026-08.md` §0t (the wave you are reconciling
to) and §0s · `frontend/data/forecast/program-status.json` blocks `t3_golden_campaign`
(`flagged_not_edited`), `d8_v_ledger_completion`, `d21_fc6_battery`, `d4i3_ercot_slack` ·
`docs/handoffs/capx-director-prompt-pack-2026-08.md` §D13 (the precedent: what a reconcile lane
may and may not touch).

THE SIX STALE FACTS, each with its source. Fix what is stale; verify the rest rather than
assuming it:
1. `tier_ladder`'s T3-golden row still reads "deferred (§2.1b, Wave 4 withdrawn)" — NEISO has a
   registered, now FC-6-scored T3 campaign. (Routed by the golden's own `flagged_not_edited`.)
2. The `readiness` prose still calls a ten-hour golden a projection. The campaign MEASURED
   29.2 min. It is no longer a projection and must not read as one.
3. `gate_reading` / `headline` were written for a board on which NO ISO held §2.1b leg (d).
   NEISO now holds it and has SPENT it.
4. **ERCOT's gate (a) now passes on the literal test** — ercot-247 declared ERCOT `complete` +
   frontier on 2026-08-31, so `complete` = {ERCOT, NEISO, PJM}. No lane has written this to the
   board. Verify it against `frontend/data/backcast/calibration-complete.json` yourself before
   writing it.
5. **The gate cells D8-V deliberately left alone and flagged to you by name.** Read its lane
   block's own note, and fix exactly what it flagged — no more.
6. **The two new PROMOTEs.** `neiso-t1f` and `nyiso-t1f` are now PROMOTE with empty caveat
   lists — the program's first clean FC maps. Any board prose that describes the dominant
   blocker set, or that says NEISO/NYISO carry FC-7 caveats, is now wrong.

THE ONE THING THIS LANE MUST NOT DO: it must not move a VERDICT. Every number, status and
determination it writes is COPIED from a committed verdict record or a committed marker file,
never recomputed and never re-scored. If reconciling a sentence would require deciding what a
verdict should be, that sentence is not yours — flag it and leave it, exactly as D8-V flagged
its gate cells to you and as the golden flagged its cross-ISO prose. A reconcile lane that
starts adjudicating is how a board acquires a fact nobody measured.

ASSERT BEFORE YOU COMMIT, programmatically, in the D8-RE/D8-V pattern: every ISO determination,
every fc map, every keeper/marker/golden field, every §2.1b gate cell you did not deliberately
edit, and every prior lane block — byte-identical. List what you changed and what you asserted
unchanged, in the finding.

GUARDRAILS: zero solves, zero re-scores. No keeper/shard/marker edit, nothing in the backcast
namespace, no ScenarioConfig field, no mechanism, no matrix cell (rule 28 not triggered). No
holdout year. No new GitHub Actions workflow. Push per CLAUDE.md Git & Pushing; blob-verify
every ≥300-line file after push (rule 27) — `program-status.json` qualifies.

COLLISION: lane D25 (FC-5 dispositions) is dispatched in the same batch and writes the FC-5
rows of the same file. You write cross-ISO prose, the tier ladder, the gate cells and the ISO
blocks' stale sentences; it writes FC-5. Distinct blocks — rebase before every push and leave
its writes intact.

EXIT: docs/handoffs/FINDING-capx-d19-board-reconcile-2-<date>.md with a before/after line per
edit, the byte-identity assertions, and anything you flagged rather than fixed. Report to the
director: what the board now says that it did not, and what remains flagged.
```

---

## D23 — the P1 carbon-CO2 sign failure (r#23; D21's routed object, Phase 0)

```
You are the D23 session of the capacity-expansion (Forecast Finalization) track. Lane D21 made
the FC-6 paired invariants scoreable for forecast bundles for the first time, and the first
thing they said is that THE MODEL'S RESPONSE TO A CARBON PRICE HAS THE WRONG SIGN. You attribute
it. PHASE 0: zero solves beyond what the committed arms already contain, precommit-first, build
nothing, tune nothing, arm nothing.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (a novel object reaching a shipped mechanism; adjudication).
BRANCH: claude/capx-d23-p1-carbon-sign — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: `docs/handoffs/FINDING-capx-d21-fc6-battery-*.md` (the P1 row and its decomposition)
and the committed paired-arm summaries under the golden bundle (base / carbon25, both 25/25
years at the `9e56f0f` vintage) · `docs/forecast-determination-rubric.md` §FC-6 row 3 · CLAUDE.md
"Capacity Evolution" step 2 (the CCS retrofit screen: `ccs_retrofit_available_year`,
`eac_price_gas_cc_ccs`, `ira_ccus_45q_last_year`, `ira_45q_credit_window_years`, valued as the
**incremental uplift over the best unabated state**, screened jointly with retirement) and
`model-methodology-spec.md` §5.6.

THE OBJECT: cumulative 2026–2050 CO2 **RISES** 210.52 → 320.84 Mt (**+52.4 %**) under
`carbon_price=25`. P1 is, in the rubric's own words, the model's economic core, so this is a
claim about the model's fitness for the policy-scenario purpose the whole forecast program
exists to serve. Two legs are already visible in the committed summaries and they are NOT the
same question — keep them apart:

* **CAPACITY-SIDE leg.** The CCS retrofit screen retrofits ~3 GW LESS under the carbon price:
  2040 base = 13,049 MW gas_cc_ccs / 0 MW unabated CC; carbon arm = 9,993.5 / 4,000 MW.
  **This leg may not be a bug.** A plausible real mechanism exists: the retrofit is valued as
  the incremental uplift over the best unabated state, and an unabated CC that runs less under a
  carbon price offers a smaller uplift, so fewer retrofits clear. Your job is to establish
  whether that is what is happening — a correct economics result with a surprising sign — or
  whether the uplift arithmetic mishandles the carbon price (e.g. counts it on one side only,
  or against the wrong counterfactual). **Do not assume either.**
* **DISPATCH-SIDE leg.** 2026, the SAME fleet, CO2 +0.21 Mt. **This one is much harder to
  explain benignly**: with the fleet fixed, a carbon price enters marginal cost as
  `emission_rate × carbon_price` and merit-order switching should move emissions DOWN, not up.
  Candidates to test, none presumed: an emission rate that is zero/absent for a class that then
  looks artificially cheap; the carbon term missing from one branch of the offer path; a
  storage/renewable interaction; a sign or unit error. Start here — it is the smaller, cleaner
  object and it constrains the capacity-side story.

PRECOMMIT FIRST — push it before you measure. Freeze: the candidate causes per leg, the
committed evidence for each, the adjudication rule, and the kill that retires each candidate.
State explicitly which leg you expect to be a real result and which a defect, BEFORE looking.

EVIDENCE IS THE COMMITTED ARMS plus code reading. The base and carbon25 arms are committed with
their summaries, run_configs and evolution ledgers. If a question genuinely needs a new solve,
NAME IT AND ROUTE IT — do not run it in this lane; a third arm is a director decision because
it changes what this lane costs.

WHAT THIS MUST NEVER BECOME: no parameter moved to make P1 pass. Not the carbon price, not an
emission rate, not a retrofit cost, not the 45Q window. Rule 13 `[R-MEASURED]` and rule 21
`[R-DOF]`; and rule 1 `[R-STRUCT]` in its exact sense — if the capacity-side leg turns out to be
a real mechanism with a surprising sign, THE RESULT STAYS and P1's expectation is what gets
re-examined, on its own evidence and by its owner, not by you. Report either finding at full
magnitude.

GUARDRAILS: no new solve (see above). No mechanism, no ScenarioConfig field, no matrix cell
(rule 28 not triggered — check the NEISO shard under duty (a) before proposing anything). No
board write, no verdict flip, no keeper/shard/marker touch — D21's FC-6 FAIL and the golden's
HOLD stand as scored. Backcast namespace untouched. No holdout year. No new GitHub Actions
workflow. Push per CLAUDE.md Git & Pushing; blob-verify every ≥300-line file (rule 27).

EXIT: docs/handoffs/PRECOMMIT-capx-d23-p1-carbon-sign-<date>.md (pushed FIRST) and
docs/handoffs/FINDING-capx-d23-p1-carbon-sign-<date>.md with each leg attributed against its own
frozen kill, the repairs ROUTED (priced, admissibility stated per rules 13/21) and NOT built,
and an explicit statement of which leg is a defect and which — if either — is the model being
right in a way we did not expect. Report to the director.
```

---

## D24 — the cache-key optional-fields defect (r#23; D4-M's R-5 upgrade; characterize, do not fix)

```
You are the D24 session of the capacity-expansion (Forecast Finalization) track. Lane D4-M
upgraded R-5 from a hypothesis to a DEMONSTRATED MECHANISM: the results cache can give ONE key
to TWO different dispatches, by construction. You characterize the blast radius and PROPOSE a
repair. **YOU DO NOT FIX IT** — see the scope boundary, which is the whole point of this lane.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (a well-characterized mechanical defect; the discretion is spent in the
boundary below).
BRANCH: claude/capx-d24-cache-key-defect — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: `docs/handoffs/FINDING-capx-d4m-ercot-t1h-*.md` (the R-5 upgrade and its exact
demonstration) · `docs/handoffs/FINDING-capx-d4i3-ercot-slack-2026-08-31.md` §5.1 (the original
observation, which honestly declined to assert a cause) · `src/market_sim/results/cache.py`
(`cache_key`, `_CACHE_KEY_OPTIONAL_FIELDS`, and the cache-epoch entries).

THE MECHANISM, as demonstrated: `cache_key()` DROPS `_CACHE_KEY_OPTIONAL_FIELDS` members at
whichever value is the LIVE DEFAULT. So when a default flips — as owner ruling R-A flipped
`storage_entry_availability_gate` and `storage_entry_cost_normalized_rank` on 2026-08-31 — a run
solved BEFORE the flip and a run solved AFTER it collide on the same key while their configs
differ. D4-M's key `f061b264…` is byte-identical to `d12c-armed`'s with both storage fields
different. This is exactly what D4-I3 §5.1 saw when five committed records shared one key and
three scored quantities disagreed.

THE MEASUREMENT — that is what this lane delivers:
1. **Enumerate the exposure.** Which fields are in `_CACHE_KEY_OPTIONAL_FIELDS`, and for each,
   when did its default last change (git history of the config/ISO-config default)? A field whose
   default never moved has no exposure; a field whose default moved has exposure for every run
   solved across that date.
2. **Enumerate the affected committed runs.** For each registered forecast/hindcast bundle,
   compare its `run_config.json` values for those fields against the default in force when it
   was solved. Produce a table: run, key, fields dropped, whether another committed run shares
   that key at a different posture. **The D4-M / d12c-armed pair is the known-true positive —
   your method must find it, or your method is wrong.**
3. **State the consequence honestly per affected pair.** A shared key does not by itself prove a
   wrong result was served — it proves it COULD be. Distinguish "collides and was re-solved
   anyway" from "collides and a cached result may have been served".
4. **Propose repairs with costs.** At minimum: (a) include optional fields unconditionally;
   (b) fold a defaults-snapshot hash into the key; (c) keep the drop but refuse a cache hit whose
   stored config differs. For each: correctness, and **how many committed cache entries it
   invalidates**.

SCOPE BOUNDARY — DO NOT LAND A FIX. Any repair changes cache keys, which invalidates cached
results across the program and forces re-solves that cost real compute. **That is an owner cost
decision, not a lane's**, and shipping it inside a characterization lane would spend the owner's
money on your judgment. Propose, price, stop. Equally: **do not purge or re-solve any existing
bundle** to "clean up" a collision — a committed record stands until someone decides otherwise.

GUARDRAILS: zero solves. No mechanism, no ScenarioConfig field, no matrix cell (rule 28 not
triggered). No verdict, board, keeper, shard or marker edit — if you find that a committed
verdict rests on a possibly-collided cache entry, **report it, do not act on it**; that is a
cross-lane re-grade question and it belongs to the affected lane. Backcast namespace untouched.
No holdout year. No new GitHub Actions workflow. Push per CLAUDE.md Git & Pushing; blob-verify
every ≥300-line file (rule 27).

EXIT: docs/handoffs/FINDING-capx-d24-cache-key-defect-<date>.md with the exposure enumeration,
the affected-run table (including the known-true positive as a method check), the honest
per-pair consequence, and the priced repair options. Report to the director: how many committed
runs are exposed, and whether any committed verdict is among them.
```

---

## D25 — the FC-5 disposition table: the t3 ceiling's last step (r#23)

```
You are the D25 session of the capacity-expansion (Forecast Finalization) track. Lane D22 landed
the benchmark tables FC-5 needs, and FC-5 STILL scores SKIPPED — by design, because the rubric
requires a per-row DISPOSITION table that a scoring session must AUTHOR. You author it. This is
judgment work, not intake, and it is the last step before the t3 ceiling owner ruling Q16 named
is actually lifted.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (every row is a judgment about whether a divergence is explained).
BRANCH: claude/capx-d25-fc5-dispositions — create FRESH off origin/main (git fetch origin main
first) and rebase before every push.

READ FIRST: `docs/forecast-determination-rubric.md` §FC-5 IN FULL (the metric, the per-row
verdicts, the threshold rule) and its §6 status note as D22 updated it ·
`docs/handoffs/cross-model-corridor-2026-07-13.md` (the divergence-explanation discipline,
imported whole — read §1 before you write a single disposition) ·
`docs/handoffs/FINDING-capx-d22-fc5-corridor-*.md` (what landed, what did not, and why).

THE RULE YOU ARE APPLYING, stated so you cannot drift from it: divergence **> 15 % or opposite
sign/direction** requires a WRITTEN ours-vs-theirs explanation NAMING THE MECHANISM. Each row is
`IN CORRIDOR` / `EXPLAINED DIVERGENCE` / `UNEXPLAINED`. Any `UNEXPLAINED` row ⇒ FC-5 **FAIL**
(and routes to root cause — the D5 precedent). All in-corridor ⇒ PASS. Explained divergences
only ⇒ CAVEAT, each listed with its blocker/mechanism reference.

**"Divergence is not failure; UNEXPLAINED divergence is."** That sentence is the whole design,
and it cuts against the temptation this lane will actually face — which is not to fudge a number
but to write a vague explanation that sounds like one. A disposition that says "our higher gas
build reflects different demand assumptions" NAMES NOTHING. A disposition that says "our 2035
gas_cc is 31 % above AEO2025 because our entry screen prices the ORDC reserve leg AEO's capacity
expansion has no analogue for (D12 finding §4)" names a mechanism and can be checked. **If you
cannot name the mechanism, the row is UNEXPLAINED — write that, and let FC-5 FAIL.** A FAIL that
routes to a root cause is the instrument working; a corridor full of hand-waving is the
instrument defeated, and it would be defeated permanently, because nobody re-audits a PASS.

SCOPE: author dispositions for the ISOs whose anchors D22 landed (AEO2025 across the board, plus
ERCOT CDR and PJM Load Forecast rows), score FC-5 on them, and register the result. Where an ISO
has too few anchors to score meaningfully, say so and leave it SKIPPED with the reason — do not
manufacture coverage. Report which of the 5 still-missing sources would most change the picture.

WHAT THIS MUST NEVER BECOME (rule 13 `[R-MEASURED]`, plan §7.6, and the rubric's own rationale):
benchmarks are CONTEXT, NEVER FIT TARGETS. Nothing in the model moves toward a benchmark row.
Do not add a numeric conformance band (the rubric deliberately has none, precisely so AEO cannot
become a target). Do not rank ISOs by corridor distance. Do not adjust a model quantity, an
input, or a threshold because a row is out of corridor — the row's disposition is the deliverable,
not its closeness.

GUARDRAILS: zero solves. No mechanism, no ScenarioConfig field, no matrix cell (rule 28 not
triggered). No keeper/shard/marker, nothing in the backcast namespace. No holdout year. If
scoring FC-5 moves a committed determination, STOP and report — that is the 2026-08-30 cross-lane
re-grade rule, and the affected lane re-verifies first. No new GitHub Actions workflow. Push per
CLAUDE.md Git & Pushing; blob-verify every ≥300-line file (rule 27).

COLLISION: lane D19 is dispatched in the same batch and writes cross-ISO board prose, the tier
ladder and the gate cells of `program-status.json`; you write the FC-5 rows. Distinct blocks —
rebase before every push and leave its writes intact.

EXIT: the committed disposition table, and
docs/handoffs/FINDING-capx-d25-fc5-dispositions-<date>.md with the per-row verdicts, every
explanation's named mechanism, the FC-5 score per ISO, and the honest count of UNEXPLAINED rows.
Report to the director whether the t3 ceiling is now lifted — i.e. whether a golden campaign can
finally be graded on all required categories.
```

## D26 — FC-6 P1 arm construction repair (issued r#24 chat-only; RECONSTRUCTION committed r#25)

**Provenance note:** r#24 issued this lane as a self-contained chat prompt with no committed
charter (the transport-era habit, repeated without the transport excuse). A running D26 session's
own prompt governs its run; THIS section is the charter of record for any relaunch, reconstructed
at r#25 from ledger §0u.1/§0u.3(b) and the D23 finding. If the lane was never dispatched, this
section is the issuable prompt.

```
You are the D26 session of the capacity-expansion (Forecast Finalization) track. Lane D23
attributed the FC-6 paired-P1 "carbon price raises CO2 +52.4%" FAIL to the ARM CONSTRUCTION,
not the model: a nonzero ScenarioConfig.carbon_price REPLACES the resolved carbon signal
(policy/carbon.py::resolve_carbon_price precedence (i), documented single-consumer semantics),
and the NEISO base already carries the projected RGGI trajectory ($26.05/t in 2026 escalating
at the published 7%/yr CCR rate to $132.16/t by 2050 — the EM-6 seam fix). So carbon25 CUT the
carbon price in every horizon year (−$1.05 in 2026 widening to −$107.16 in 2050), and P1
measured the premise of its own pair. You repair the INSTRUMENT so P1 measures the model, then
re-score neiso-t3's FC-6 under the cross-lane re-grade rule.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (instrument semantics are being adjudicated, and a committed verdict
may flip).
BRANCH: claude/capx-d26-p1-arm-construction — create FRESH off origin/main (git fetch origin
main first) and rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md IN FULL (the
attribution this lane executes — especially its routed instrument repairs and what it
deliberately left standing) · docs/handoffs/FINDING-capx-d21-fc6-battery-2026-08-31.md (how
FC-6 and the paired P1–P3 are constructed and scored; the golden's vintage discipline — D21
self-caught a data-vintage leak and re-ran from the golden's own raw bytes; you inherit that
bar) · policy/carbon.py::resolve_carbon_price (the precedence semantics you must NOT silently
change for model consumers) · scripts/run_driver_battery.py (the instrument you are repairing).

THE REPAIR: the P1 arm must construct a genuine carbon-price INCREASE over the resolved base
trajectory in EVERY horizon year — a strictly positive delta, stated in the run record
year-by-year. Design the construction yourself (that is why this lane is Fable); the
constraint set is: (1) the base leg and the arm leg differ ONLY in the carbon signal; (2)
resolve_carbon_price's documented precedence semantics stay intact for every non-instrument
consumer — if the honest fix is a new ScenarioConfig field (e.g. an additive carbon delta),
that is a solve-affecting mechanism: rule 28 duties fire (matrix row in
docs/codebase-site/data/mechanism-matrix.js + a cell line in EVERY ISO shard, same PR), it
ships default-off/neutral, and its existence is justified in the finding; (3) no model
parameter, threshold, retirement/retrofit economics or expectation moves — D23's line "repairs
are entirely instrument-side" is your scope fence.

THE RE-SCORE: re-run the paired P1 at the golden's vintage with the repaired arm (forecast-mode
2026+ solves — permitted under rule 22, no measured actuals), re-score FC-6, and publish under
the CROSS-LANE RE-GRADE RULE: reproduce the committed FC-6 record byte-for-byte FIRST
(control-first, the D8-V/D25 pattern), then apply the repaired instrument; if anything beyond
neiso-t3's FC-6 rows would flip, STOP and report to the director. D21's FC-6 FAIL was
deliberately left standing by D23 — whether it survives is exactly what your re-score decides,
and EITHER outcome is a valid result. Do not touch the vacuous-ladder CAVEAT
(renewable_buildout_pace) — that is a separate, still-true finding.

GUARDRAILS: rules 22 (no holdout year; forecast-mode 2026+ only), 27 (run_driver_battery.py
and any src/ file you touch are core; edit locally, push exact bytes, blob-verify ≥300-line
files), 28 (as above — triggered ONLY if a ScenarioConfig field is added). Solves are
budgeted: price the paired run before launching it (the golden was ~1.0h/~4.3GB; a pair is
two). No keeper/shard/marker; nothing in the backcast namespace. No new GitHub Actions
workflow.

COLLISION: D27 writes the MISO t1h key + MISO board block; D29 edits
scripts/run_full_horizon.py; D24-R edits runner.py/scenarios.py cache plumbing. You share NO
files with D27/D29; if D24-R's scenarios.py edit lands mid-lane, rebase — your ScenarioConfig
edit (if any) is additive and distinct. You write neiso-t3's FC-6 rows and the FC-6
instrument; nothing else on the board.

EXIT: the repaired instrument + the re-scored neiso-t3 FC-6 (published or STOPPED-and-routed,
per the re-grade rule) + docs/handoffs/FINDING-capx-d26-p1-arm-construction-<date>.md with the
year-by-year delta table of the repaired arm, the control reproduction, both scores, and the
verdict consequence honestly stated. Report to the director: the golden re-solve card (ledger
§0v.6(a)) is decided AFTER you land — say explicitly whether your result changes its terms.
```

## D27 — MISO T1-H HEAD re-measure (issued r#24 chat-only; RECONSTRUCTION committed r#25)

**Provenance note:** as §D26's. Reconstructed at r#25 from ledger §0u.1 (D17-R grade) and the
D17 finding. A running D27 session's own prompt governs; this is the relaunch charter of record.

```
You are the D27 session of the capacity-expansion track — the EXECUTION of D17-R's routed
PRIMARY. D17-R attributed MISO's missing non-coal exit channel to requirement rationing at the
admission cap: gas/oil units fail the screen bar en masse and are then blocked at the cap
(entry_capped 93.0 GW in 2023, 105.5 GW in 2024), whose requirement basis was the pre-S-123
composite. The S-123 repair is ALREADY SHIPPED AT HEAD (all three operands are registry
constants read through resolve_adequacy_requirement_mw / accredited_firm_capacity_mw), so the
committed MISO T1-H numbers simply predate their own fix. You re-solve the MISO T1-H leg at
HEAD and grade the result against D17's quantified expectation: the corrected basis is worth
≈14.7 GW of admission headroom at the 2024 screen (≈11.2 GW requirement overstatement + 3.5 GW
missing external accredited firm) — 3.7–4.3× the entire missing non-coal exit target
(3.458 GW actual).

DATA PROFILE: miso
MODEL ASSIGNMENT: Opus (the discretion is spent in D17's finding; this is a pre-quantified
re-measure).
BRANCH: claude/capx-d27-miso-t1h-remeasure — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d17-miso-exit-channel-2026-09-01.md IN FULL (the
attribution, the ≈14.7 GW arithmetic, and the standing refusal: no FOM/threshold/lag was
identified from the retirement residual — that refusal BINDS you too) ·
docs/handoffs/PRECOMMIT-capx-d17-miso-exit-channel-2026-09-01.md (the frozen threads) · the
committed miso-t1h verdict record + its run_config.json (the baseline you re-measure against).

THE RUN: the MISO T1-H hindcast leg at HEAD, unchanged recipe — you are re-measuring a shipped
repair, not testing a mechanism. Years sequential in-session (rule 12). BEFORE the solve,
write the expectation down as a short pre-declaration in the branch (the D4-M discipline):
expected direction and rough magnitude on (i) entry_capped 2023/2024, (ii) executed non-coal
exits vs the 3.458 GW actual, (iii) retire.total_gw and the G3 row, plus the honest note that
D17's headroom figure is a screen-side arithmetic, not a dispatch guarantee. Grade every
prediction at full magnitude afterward — misses included.

REGISTRATION: preserve-then-overwrite (the NEISO-RC-R pattern): preserve the current miso-t1h
record under a dated suffixed key (a PRESERVED BASELINE, never quoted as current), then
register the HEAD re-measure to the BARE miso-t1h key via scripts/register_forecast_run.py,
refresh the MISO board block, and leave every other ISO's rows untouched. If the re-measure
flips any committed verdict beyond miso-t1h's own rows, STOP and route (cross-lane re-grade).

GUARDRAILS: rule 22 (forecast/hindcast lanes touch no backcast holdout year; nothing scored
against measured H1-2026), rule 27 (no core-file rewrite; blob-verify ≥300-line pushes), rule
28 NOT triggered (no mechanism, no ScenarioConfig field — if you find yourself wanting one,
that is D17's standing refusal talking: STOP). No FOM, threshold, lag, or screen parameter
moves. No keeper/shard/marker. Solve budget: one T1-H leg, priced before launch.

COLLISION: D26 writes neiso-t3 FC-6 rows + the FC-6 instrument; D29 edits
scripts/run_full_horizon.py (if its grain lands before your solve starts, your bundle carries
the new fields — fine either way; do not wait); D24-R edits cache plumbing (your run uses its
own --out-dir per convention — unaffected). You write the miso-t1h key + MISO board block ONLY.

EXIT: the registered re-measure + graded pre-declaration +
docs/handoffs/FINDING-capx-d27-miso-t1h-remeasure-<date>.md stating what the corrected basis
actually bought (entry_capped movement, executed exits vs actual, G3), where D17's ≈14.7 GW
expectation held or missed, and what remains of the missing-exit object — including whether
the D28 contributing cause (the bar under-rewarding ~118.5 of 142.6 GW) is now the binding
residual.
```

## D28 — capacity revenue at long positions, cross-ISO Phase-0 (issued r#24 chat-only; RECONSTRUCTION committed r#25)

**Provenance note:** as §D26's. Reconstructed at r#25 from ledger §0u.2. A running D28
session's own prompt governs; this is the relaunch charter of record.

```
You are the D28 session of the capacity-expansion track — Phase-0 characterization of a
cross-ISO object two lanes surfaced independently and nobody owns: A MODELLED CAPACITY-DEMAND
CURVE THAT PAYS NOTHING EXACTLY WHERE THE MODEL SITS. D17-R measured MISO's screen bar
under-rewarding ~118.5 of 142.6 GW of screened thermal in 2024, chiefly because the modelled
capacity-revenue leg pays $0 at every long reserve position (RBDC zero-cross at 1.05; $0 on
every committed capped row) while MISO's real PRAs cleared small positive prices. NEISO-RC-R's
R2 leg measured the SAME pathology from the other end: the re-derived FCA demand curve pays $0
past 8.3% surplus ("near-inert at the model's long positions") where real FCAs cleared
$24–43/kW-yr. Two ISOs, two independently-derived curves, one shape of error.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (novel cross-ISO object; the deliverable is an adjudication-grade
characterization).
BRANCH: claude/capx-d28-longposition-capacity-revenue — FRESH off origin/main, rebase before
every push.

READ FIRST: docs/handoffs/FINDING-capx-d17-miso-exit-channel-2026-09-01.md (the MISO half —
the RBDC zero-cross evidence and the 2024 census) · the NEISO-RC-R record (ledger §1 row +
PR #4467's finding; the R2 curve re-derivation and its measured miss) · the per-ISO curve
implementations and their parameter citations (docs/parameter-citations.md) · the published
auction-clearing record each ISO's curve should be judged against (PRA clearing prices;
FCA results — use what is already in-repo; this lane FUNDS NO INTAKE).

PHASE-0 SCOPE — CHARACTERIZE, DO NOT REPAIR: (1) reconstruct, for MISO and NEISO, where the
model's long-run reserve position actually sits year-by-year vs where each modelled curve's
zero-cross sits — the "pays $0 exactly where the model sits" claim, made exact; (2) compare
each curve's shape against its ISO's PUBLISHED curve and published clearing outcomes at
comparable surplus — is the defect the curve's SHAPE, its zero-cross placement, the surplus
MEASUREMENT feeding it, or real (auctions clearing above a curve that says $0 — sloped-demand
mechanics, out-of-market effects)?; (3) name, per ISO, what a repair would be identified FROM
(a published curve parameter, a filing, a clearing record — never the residual); (4) check the
other two capacity-market ISOs (PJM, NYISO) for the same signature, evidence-level only.

SIGN DISCIPLINE, stated because it is the trap: the fix direction is MORE capacity revenue at
long positions, which makes retirements HARDER — i.e. it moves D17's headline residual the
WRONG way. Rule 14 [R-ACCURATE]: never resolve by whichever direction helps a residual; if the
accurate curve worsens a fit, that is a discovered bug elsewhere, not a reason to keep the
inaccurate curve. Write this into the finding explicitly wherever it bites.

GUARDRAILS: zero solves. Docs only — no mechanism, no ScenarioConfig field, no matrix cell
(rule 28 not triggered at Phase-0; the REPAIR lane, if chartered, carries those duties). No
keeper/board/verdict/marker edit. Rule 25: parameters and verdicts stay per-ISO — one shape of
error does NOT mean one shared fix. Rule 27 on any ≥300-line push.

COLLISION: none — you write docs only. D27 may re-measure MISO T1-H mid-lane; its result
changes your D17-residual CONTEXT but not your curve measurements; cite whichever record is
current when you finish.

EXIT: docs/handoffs/FINDING-capx-d28-longposition-capacity-revenue-<date>.md — the per-ISO
characterization, the four-ISO signature census, the identification source for each candidate
repair, and a routed recommendation (repair lane(s), per-ISO, with collision notes) for the
director. NO repair lands in this lane.
```

## D24-R — cache-key repair, Q20 execution (r#25)

```
You are the D24-R session of the capacity-expansion track — the EXECUTION of owner ruling Q20
(r#25) on lane D24's priced repair options for the cache-key optional-fields defect. The
ruling: land (c′) + (b′-1), the zero-cost pair, exactly as D24 §7 specifies them. Nothing else
is licensed — no (a), no (b), no (b′-2), no retroactive re-key of anything.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the discretion was spent in D24's finding §7; this is execution).
BRANCH: claude/capx-d24r-cachekey-repair — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d24-cache-key-defect-2026-09-01.md §1 (the mechanism),
§4 (the two demonstrated collision forms your change must catch — 4.1 differing-common-field,
4.2 absent-vs-armed-default — and §4.5's twelve designed-case groups your change must NOT
refuse), §7 (the option definitions — (c′) and (b′-1) verbatim), §8 (what D24 deliberately did
not touch: that is your work order). Also scripts/check_cache_key_registration.py (the guard
that must stay green) and the ledger comment above _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS in
scenarios.py — (b′-1) is the "deeper fix" it already names
(docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md §4).

THE TWO CHANGES, and nothing else:
1. (b′-1): cache_key()'s drop comparison reads the DECLARED default from
   _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS instead of the live field default, and that ledger
   becomes APPEND-ONLY — a future default flip ADDS a dated declaration, never overwrites the
   old. Re-baseline at today's declared values: measured a no-op on every current key
   (0 forecast, 0 backcast). VERIFY the no-op yourself before pushing — recompute the key for
   every committed run_config.json in both namespaces and assert zero moves; commit the
   assertion as a test/probe record. THAT ASSERTION IS YOUR MERGE GATE: any key that moves
   means you have implemented (b′-2), which is not licensed.
2. (c′): the is_cached seam (runner.py; D24 names the exact call) refuses a hit whose stored
   config.yaml differs from the requesting config on any COMMON field, OR where the requesting
   config carries a field ABSENT from the stored config whose value is not that field's
   registration-time default. Refusal = a logged cache miss naming the differing fields (then
   re-solve) — never an exception that kills the run. Follow the
   assert_cache_key_uncontaminated precedent (owner decision D-11) for placement and tone.

TESTS: (i) the §4.1 form refuses; (ii) the §4.2 form refuses; (iii) the twelve designed-case
groups still HIT — schema growth without a flip must not refuse (this is what distinguishes
(c′) from strict (c), which refused 14/14 with only 2 true positives); (iv) the append-only
ledger is enforced (an overwrite attempt fails loudly); (v) check_cache_key_registration.py
stays green.

GUARDRAILS: cache plumbing is not a mechanism — rule 28 NOT triggered, no matrix row, no
ScenarioConfig field, no new CLI flag. Zero solves. No committed bundle, sidecar, board,
keeper, shard or marker is touched; the two historical collision pairs stay unseparated
(provenance annotation only — D24 §6's NEISO verdict linkage is the affected lane's, not
yours). runner.py and scenarios.py are ≥300-line core files: edit locally, push exact on-disk
bytes, blob-verify after push (rule 27). No new GitHub Actions workflow.

COLLISION: D26 may add a ScenarioConfig field on the same file (scenarios.py) — additive and
distinct regions; rebase-care, never conflict-resolve away its edit. D27/D29 share no files
with you.

EXIT: both changes + tests + the zero-key-move assertion record +
docs/handoffs/FINDING-capx-d24r-cachekey-repair-<date>.md stating what landed, the no-op
verification result, and what deliberately remains open (the historical pairs; the
provenance-side cache_epoch question D24 §5 reported).
```

## D29 — trajectory reporting grain (r#25; D25 §6.1 routed)

```
You are the D29 session of the capacity-expansion track — the reporting-grain fix lane D25
routed (finding §6.1). run_full_horizon.extract_trajectory carries no generation-by-fuel, and
its capacity block's storage_mw reads cap.get("storage") over GENERATOR fuels — 0.0 by
construction even for a 17 GW ERCOT battery fleet. That blocks 252 corridor anchors (the
energy-mix family) from ever being dispositioned and leaves a standing basis caveat on FC-5.
You extend the summary schema; you re-run NOTHING.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the change is specified by D25 §6.1; execution).
BRANCH: claude/capx-d29-trajectory-grain — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d25-fc5-dispositions-2026-09-01.md §6.1 (the routed
spec) and §2 (what the corridor needs the summary to carry) · scripts/run_full_horizon.py
(extract_trajectory at ~line 412 and the writer that serializes it) · the committed
full_horizon_summary.json files of the bundles that have one (the schema you are extending).

THE CHANGE — ADDITIVE ONLY: extract_trajectory (and the summary it writes) gains
(1) generation-by-fuel per horizon year, read from the same per-year result object the
capacity block already reads, and (2) a REAL storage column — storage power capacity from the
storage fleet state, not cap.get("storage") over generator fuels. Every existing key keeps its
name, type and meaning, so committed summaries remain readable by every current consumer. For
the defective storage_mw key: enumerate its consumers call-site by call-site; if NOTHING
committed reads it, repair it in place and say so in the finding — otherwise keep it
bug-compatible, add the new column beside it, and document the defect at the definition
(cite this charter).

GUARDRAILS: zero solves — committed summaries are NOT regenerated (they lack the new fields
until their bundle next re-solves; making the energy-mix rows dispositionable for FUTURE runs
IS the deliverable). No mechanism, no ScenarioConfig field (rule 28 not triggered). No
board/verdict/keeper edit; do not touch FC-5 scores or dispositions.
scripts/run_full_horizon.py is a ≥300-line core run script (rule 27): edit locally, push exact
on-disk bytes, blob-verify; Opus is licensed for it, Sonnet is not. Tests: a unit test on
extract_trajectory over a synthetic run object asserting the new fields and a nonzero storage
value against a fleet with storage (the golden-system helpers in docs/testing.md are the
pattern). No new GitHub Actions workflow.

COLLISION: D27 (MISO T1-H re-measure, in flight) will write a new summary — if your change
lands before its solve starts, its bundle carries the new grain (good); if not, also fine. Do
not coordinate, do not wait, do not touch MISO board surfaces. D26/D24-R share no files with
you.

EXIT: the extended extractor + tests +
docs/handoffs/FINDING-capx-d29-trajectory-grain-<date>.md recording the schema addition, the
storage_mw consumer enumeration and what was done about it, and which committed bundles remain
on the old grain.
```

## D30 — the 45Q conversion pace (r#25 amendment 2; D25 §6.4 routed)

```
You are the D30 session of the capacity-expansion track — Phase-0 characterization of the D25
§6.4 routed question. The CCS retrofit screen (capacity-evolution step 2, spec §5.6) converts
existing gas-CC at its 3 GW/yr/ISO cap even where the resolved carbon signal is ZERO (PJM and
MISO — 45Q alone), reaching ~9 GW per ISO by 2030 and fleet fractions AEO2025 reaches nowhere.
Lane D23 cleared the model's carbon-response SIGN; the open question is the PACE: is
cap-saturated conversion on 45Q economics alone the INTENDED reading of spec §5.6, or a defect
in how the retrofit uplift is valued? You characterize; you do not repair, and you do not
decide arming.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (mechanism adjudication on a novel object — "intended reading vs
defect-candidate" is a judgment call with routing consequences).
BRANCH: claude/capx-d30-45q-pace — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d25-fc5-dispositions-2026-09-01.md §6.4 (the routed
question) + §4.3 mechanism 5 (the named revenue legs, per ISO) ·
model-methodology-spec.md §5.6 (the screen: ≥15 yr remaining life, 3 GW/yr/ISO cap, valued as
the INCREMENTAL uplift over the best unabated state, screened jointly with retirement) ·
CLAUDE.md capacity-evolution step 2 (ccs_retrofit_available_year, eac_price_gas_cc_ccs,
ira_ccus_45q_last_year, ira_45q_credit_window_years) · docs/parameter-citations.md for every
45Q/capture-cost/EAC number the screen consumes · the committed full-horizon/t1f bundles'
evolution ledgers (the conversion paths you are decomposing).

PHASE-0 SCOPE — CHARACTERIZE, DO NOT REPAIR:
(1) Decompose the screen's uplift arithmetic for the zero-carbon-signal case (PJM PRIMARY —
    see the seam below): which revenue legs make a retrofit clear the bar with carbon at zero
    — the 45Q credit value, the EAC price, avoided variable cost, anything else — with the
    year-by-year margin per leg for a representative cleared unit.
(2) Establish whether the cap BINDS in every conversion year in every ISO — if yes, the
    modelled pace IS the cap, and the economics question becomes "how far above the bar is
    the marginal retrofit", which you should quantify (headroom, not just pass/fail).
(3) Audit the leg values against their citations: is 45Q valued at statute, over the correct
    window (ira_45q_credit_window_years against ira_ccus_45q_last_year), against a cited
    capture cost and capture rate? Name any value whose citation does not support the use the
    screen puts it to.
(4) Adjudicate: INTENDED READING (the spec's economics, correctly implemented, genuinely
    imply cap-saturated conversion — then say so and close the object with the spec cite) or
    DEFECT-CANDIDATE (name the defective leg and what a repair would be identified FROM — a
    published capture cost, a credit-monetization haircut, retrofit capex — always a primary
    source, never the corridor).

TWO SEAMS, both hard:
- MISO's T1-H baseline is being re-measured by lane D27 IN FLIGHT. Characterize on PJM as the
  primary case (its 45Q-only economics are the clean instance); treat any MISO rows as
  provisional, label them so, and do not block on D27.
- If the pace turns out to be driven by the CAPACITY-REVENUE leg, STOP at that seam and route
  to lane D28, which owns the capacity-demand-curve object — do not re-derive curves or
  duplicate its census.

DISCIPLINE (rule 13 [R-MEASURED] and D25's own line): the AEO divergence MOTIVATES this
question; it must never CALIBRATE the answer. No parameter, threshold, cap or credit value
moves in this lane, and no proposed repair may be identified from the corridor distance.
GUARDRAILS: zero solves; docs only; no mechanism, no ScenarioConfig field, no matrix cell
(rule 28 fires in the repair lane, if one is chartered). No keeper/board/verdict/marker edit.
Rule 27 on any ≥300-line push. No new GitHub Actions workflow.

COLLISION: none on files — you write docs only. D27 (MISO t1h) and D28 (curve object) are the
two in-flight lanes your SEAMS reference; cite whichever records are current when you finish.

EXIT: docs/handoffs/FINDING-capx-d30-45q-pace-<date>.md — the per-leg decomposition, the
cap-binding census, the citation audit, the adjudication with its routing (closure-with-cite,
a repair-lane charter recommendation, or the D28 handoff), and the honest statement of what
the PJM-primary scope could not see.
```

## D26-S — the FC-6 arm solves + re-score (r#26) — **RETIRED UNRUN: D26's own session completed the runbook (PR #4522, P1 FAIL→PASS, FC-6 FAIL→CAVEAT) before this was dispatched; historical record, do not run**

```
You are the D26-S session of the capacity-expansion track — the SOLVE HALF of lane D26, whose
checkpoint landed at PR #4520: the carbon_price_delta instrument repair is in, the base-arm
control reproduced the golden EXACTLY at vintage+repair, and the finding is committed with a
literal TBD-HEADLINE plus the full runbook for what you now run. Your discretion is spent —
the runbook is literal commands.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Opus (execution; every design decision is in the D26 finding).
BRANCH: claude/capx-d26s-arm-solves — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d26-p1-arm-construction-2026-09-01.md IN FULL — it is
your charter, your runbook (tail section: the vintage checkout, env, the two
run_driver_battery.py invocations, the check_forecast_invariants --paired call, the
forecast_verdict call), and the document you finish. Also
docs/handoffs/FINDING-capx-d21-fc6-battery-2026-08-31.md (the scoring semantics you inherit)
and docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md (what the repaired pair now
actually measures).

THE WORK: (1) run the two paired arms EXACTLY as the runbook states — base, then
carbon_plus25, SEQUENTIAL (rule 12; budget ~1.0 h / ~4.3 GB each, price and state it before
launching); (2) score the pair with the committed instruments; (3) re-score neiso-t3's FC-6
and publish under the CROSS-LANE RE-GRADE RULE — the base-arm control is already reproduced,
so your remaining stop is: if anything beyond neiso-t3's FC-6 rows would flip, STOP and
report to the director; (4) fill the finding's TBD sections — headline, measured deltas, the
FC-6 verdict consequence — and grade D23's expectation of the repaired pair at full
magnitude, misses included. EITHER FC-6 outcome is a valid result: a surviving FAIL now
measures the MODEL, which is the whole point of the repair; do not lean either way.

GUARDRAILS: forecast-mode 2026+ solves only (rule 22 — no measured actuals, no holdout year).
The solves run in the PINNED VINTAGE checkout exactly as the runbook constructs it — do not
"upgrade" the vintage, and restore any vintage-pinned data checkouts exactly as the runbook's
git checkout lines do. No model parameter, threshold or expectation moves; carbon_price_delta
stays default-0 everywhere except the arm leg's config. No keeper/shard/marker; nothing in
the backcast namespace. Rule 27 on any ≥300-line push; rule 28 already discharged at D26 —
you add no field. No new GitHub Actions workflow.

COLLISION: D33 (NEISO position lane) writes docs + a NEISO position finding and is barred
from the golden's pinned inputs — you own those for the duration; if its landing touches
anything you read, rebase and say so. D31 is MISO-side; no shared files.

EXIT: the completed D26 finding (TBD sections filled, headline written), the committed arm
records + paired-invariants output, the re-scored (or STOPPED-and-routed) neiso-t3 FC-6, and
an explicit line for the director: the golden re-solve card (§0w.5) is decided on your
result — state whether the repaired P1 changes its terms, and whether D23's R4 design
question (replace/floor/stack semantics for carbon_price) is now ripe.
```

## D31 — the MISO capacity-revenue repair (r#26; D27-R2 + D28-R1, the primary lever; Q24-funded)

```
You are the D31 session of the capacity-expansion track — the REPAIR lane for the object two
findings converged on and D27 promoted to PRIMARY lever on the MISO exit residual. D28
measured: MISO's RBDC is (one exception) published-faithful, but in the $0 screen years the
model's accredited position sits ~+11 reserve-ratio points LONGER than the real market's
cleared position, and the curve is evaluated at a census quantity where the real PRA clears
supply against the curve. D27 measured at HEAD: the requirement repair released the
admission cap and the exit object did not move (non-coal exits 0.000 GW), because
composition is set elsewhere — capacity revenue at the model's positions stays $0 while real
PRAs cleared small positive prices. You repair the POSITION and the CURVE SHAPE from
published data, and measure the consequence.

DATA PROFILE: miso
MODEL ASSIGNMENT: Fable (mechanism repair with arming consequences on the program's
worst-understood screen).
BRANCH: claude/capx-d31-miso-caprev-repair — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d28-longposition-capacity-revenue-2026-09-01.md §6.1
(the position audit's identification — PRA Results Posting p.22 offered-and-cleared category
rows + Initial PRMR p.18, the S-123 operand source), §6.2 (the RBDC shape sources:
ER23-2977 / 187 FERC ¶ 61,202 / RAN BPM-011 / the PRA chart), §6.3 (the vertical-era floor —
an ADJUDICATION item, not a commitment), the one-position limit, and §7's census row for
MISO · docs/handoffs/FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md (the fresh baseline
you measure against, the floor-retention mechanism you must NOT conflate with this repair,
and R5 — which is D32's, not yours) · the S-123 registry seams
(resolve_adequacy_requirement_mw / accredited_firm_capacity_mw) your audit rows share.

OWNER RULING Q24 (r#26): the intake is FUNDED. The owner fetches the PRA Results Postings
(PY2023-24 / 2024-25 / 2025-26) and the RBDC shape source out-of-session (misoenergy.org is
403-blocked in-session) and hands you the files. Intake them through the full data contract
(data-intake skill: schema, immutable raw snapshot, curation, per-ISO registry — rule 13
admissibility stated in the schema notes). If a handed file is missing, run the in-repo
partial honestly and name the bound — do not fetch, and do not widen the ask.

THE REPAIR, two legs, both identified ONLY from the published record:
1. POSITION AUDIT: reconcile the model's accredited position (the screen's entering
   ratio) against the PRA's offered-and-cleared accounting, category by category
   (Generation / External / BTMG / DR / EE) — find which categories the model counts that
   the real auction did not clear (or vice versa), per planning year. The repair is whatever
   the reconciliation IDENTIFIES (a category exclusion, an accreditation basis, a
   requirement-side term), entered formulaically so it regenerates in a forecast year
   (rule 13 test).
2. RBDC SHAPE: replace the first-order construction with the published curve (shape +
   zero-cross + seasonal grain as the source defines them), citing the filing. The
   vertical-era floor question is adjudicated in the finding, not silently decided.

RULE-14 SIGN DISCIPLINE, verbatim from D28 and binding: every faithful repair here moves
capacity revenue UP at the screens' positions, which makes retirements HARDER and moves
D17's exit headline the WRONG way. That is not a reason to withhold or shade anything.
Nothing may be sized, tuned, or sequenced by what it does to the exit residual; if the
accurate inputs worsen it, the remaining error is elsewhere (thread (i-a) energy margins,
D32's retention key) and stays open on its own evidence.

MEASURE: re-run the MISO T1-H leg with the repair (sequential years, rule 12), register
preserve-then-overwrite against D27's baseline (`miso-t1h` bare key; preserve the D27 record
under a dated suffix), refresh the MISO board block, grade a written pre-declaration
(direction and rough magnitude on the position, screen revenue, exits by fuel, G3) at full
magnitude. If any committed verdict beyond miso-t1h's rows would flip, STOP (cross-lane
re-grade).

GUARDRAILS: rules 22 (no holdout year), 27 (blob-verify ≥300-line pushes; screen code is
core), 28 (a new ScenarioConfig field or armed default = matrix row + every shard cell in
the same PR; ship default-off unless the identification is complete and say which in the
finding). D32's floor-retention question is OUT OF SCOPE — do not touch
_floor_retention_merit. No FOM/threshold/lag tuning (D17's standing refusal binds).

COLLISION: miso-197 (owner's backcast lane) writes the MISO BACKCAST namespace — you write
forecast surfaces + screen code + the funded intake; no shared files, but rebase-care on
docs/. D26-S/D33 are NEISO-side. D30, if dispatched, is docs-only and stops at your seam.

EXIT: the intaken sources + the two-leg repair + the measured T1-H consequence +
docs/handoffs/FINDING-capx-d31-miso-caprev-repair-<date>.md with the reconciliation table,
the graded pre-declaration, the honest exit-residual direction, and what remains routed
(D32's retention key; anything the partial record could not identify).
```

## D33 — the NEISO position lane (r#26; D28-R2, RC-R §10.4(2) executed)

```
You are the D33 session of the capacity-expansion track — the NEISO half of D28's position
defect. D28 measured: NEISO's re-derived FCA curve is published-faithful, and in its three
$0 crossover years the model's position sits +21 / +6 / +7 reserve-ratio points past the
zero-cross (−3 / +1 in the dip/rebound years) — the curve pays $0 because the MODEL'S
POSITION is long, not because the curve is wrong. NEISO-RC-R's routed §10.4(2) named the
question this lane now executes: the ACCREDITATION BASIS (what the model counts as
accredited capacity entering the screen) and CLEARED-VS-QUALIFIED (the model's census
position vs what the real FCA actually cleared).

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (the accreditation basis is an adjudication, and its consequence
reaches the golden re-solve card).
BRANCH: claude/capx-d33-neiso-position — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d28-longposition-capacity-revenue-2026-09-01.md (the
NEISO census rows, the position-defect decomposition, and §6's identification sources for
NEISO) · the NEISO-RC-R record (PR #4467's finding §10.4(2) — the routed question in its own
words, and the R2 curve re-derivation this lane must NOT redo) · the in-repo FCA results and
capacity-market data under data/raw (the published cleared/qualified record) · the NEISO
screen's accreditation seams (accredited_firm_capacity_mw and what feeds it).

SCOPE — in-repo record ONLY (no intake is funded for NEISO; if a tightly-scoped ask emerges,
FILE it with the D28 §6 sourcing and stop — do not fetch):
1. Reconstruct, per FCA year in the screen window, the model's entering position vs the real
   auction's cleared and qualified totals — the +21/+6/+7 decomposed into its accounting
   causes (what the model counts that the FCA did not clear; retirements/de-list bids;
   imports; accreditation haircuts the model lacks).
2. Adjudicate the accreditation basis: is the model's accredited-capacity construction the
   published one (seasonal claimed capability / FCA qualified) or an artifact of the fleet
   build? Name the repair each divergence identifies, formulaically (rule 13), from the
   published record only.
3. State the consequence for the FCA-curve revenue leg at the repaired position — direction
   and rough magnitude, no tuning.

RULE-14 SIGN DISCIPLINE: shortening the model's position moves capacity revenue UP and
makes NEISO retirements HARDER. Nothing is sized by any residual.

GUARDRAILS: zero solves unless a repair is fully identified AND cheap to measure — and even
then, the golden's pinned inputs are UNTOUCHABLE while D26-S runs (its vintage checkout
reads the NEISO capacity-market demand-curve raw files; your work is additive-only, never an
edit of an existing raw file — data/raw is immutable regardless, rule: never modified in
place). Prefer landing the characterization + filed repair and routing the measurement.
Rules 22 / 27 / 28 as usual (a ScenarioConfig field = matrix duties, default-off).

COLLISION: D26-S owns the golden vintage and writes neiso-t3 FC-6 rows — you write a
position finding (+ any additive intake files and filed repair), never the FC-6 instrument
or neiso-t3 rows. D31 is MISO-side. Rebase-care on docs/.

EXIT: docs/handoffs/FINDING-capx-d33-neiso-position-<date>.md — the per-year
cleared-vs-qualified reconciliation, the accreditation adjudication, each identified repair
with its published source, the filed intake ask if one is needed, and the explicit line the
golden re-solve card is waiting for: does the position repair change what a second campaign
would measure?
```

## T3-NEISO-GOLDEN-2 — the SECOND §2.1b campaign (r#26 amendment; owner ruling Q25)

```
You are the T3-NEISO-GOLDEN-2 session — the second §2.1b full-horizon campaign in program
history, authorized by owner ruling Q25 (capx ledger §3, 2026-09-01). The standing golden
records the PRE-R-A unarmed storage-entry posture and its headline is ZERO storage entry in
25 years; ruling R-A armed exactly the storage-entry mechanisms, and D25 measured
zero-storage-entry as the corridor's largest cross-ISO divergence family (−56..−96 %, four
ISOs). You re-solve the NEISO BAU golden at HEAD with the armed posture and score it on the
full rubric — the ceiling that made Q16 hold this is gone (FC-5 scores via D25's
dispositions; FC-6 scores via D26's repaired P1 arm).

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (the program's only golden is re-registered wholesale; determination
consequences are live and the storage outcome is open — adjudication, not pre-declared
execution).
BRANCH: claude/capx-t3-golden-2 — FRESH off origin/main, rebase before every push.

READ FIRST: the pack §T3-NEISO-GOLDEN (the first campaign's charter — your recipe baseline
and registration pattern) · docs/handoffs/FINDING-capx-t3-neiso-golden-2026-08-30.md (what
the first campaign recorded, its posture-epoch caveat, and the gate-condition caveats
carried verbatim) · docs/handoffs/FINDING-capx-d26-p1-arm-construction-2026-09-01.md (the
repaired FC-6 arm construction you now use natively: carbon_price_delta, never a
carbon_price replace) · docs/handoffs/FINDING-capx-d21-fc6-battery-2026-08-31.md (battery
mechanics + the data-vintage discipline: score arms from THIS campaign's own bytes) ·
docs/handoffs/FINDING-capx-d25-fc5-dispositions-2026-09-01.md §4.1 (the t3-required FC-5
table you re-disposition against the NEW trajectory — authored judgment, benchmarks context
never targets).

THE CAMPAIGN:
1. BAU 2026–2050 at HEAD, the current NEISO recipe with the R-A-armed storage-entry posture
   (the live defaults — do NOT hand-set fields; the posture IS HEAD's defaults) and
   carbon_price_delta at its 0 default. Budget ~1.0 h / ~4.3 GB (FF-3E) — price and state
   before launch. D29's trajectory grain is at HEAD, so your summary carries
   generation-by-fuel + the real storage column — the corridor's energy-mix family becomes
   scoreable on a golden for the first time.
2. The FC-6 battery AT THIS CAMPAIGN'S OWN VINTAGE: the Tier-1 ladder + paired P1–P3, P1 via
   carbon_price_delta (the D26 construction). Price the battery before running it; solves
   sequential (rule 12). A vacuous rung is a CAVEAT, never a PASS (D21's line).
3. Score the FULL rubric (FC-1..FC-8, the FC-5 corridor with fresh dispositions for rows the
   new trajectory moves, FC-6 from step 2) and register PRESERVE-THEN-OVERWRITE: the
   standing golden's record and bundle stay preserved (dated suffix, posture-epoch caveat
   intact — it remains the pre-R-A record of note); the bare neiso-t3 key takes this
   campaign. Control-first: reproduce the committed neiso-t3 record byte-for-byte BEFORE
   overwriting anything.

WHAT THIS CAMPAIGN IS FOR, stated so the lane cannot drift: the question is whether the
ARMED storage-entry economics produce entry (and what the full-horizon system then looks
like) — NOT whether storage entry makes any verdict better. Rule 13/D25 discipline: no
input, parameter or threshold moves toward any corridor row; the corridor is re-dispositioned
against the new trajectory, not the other way around. EITHER storage outcome is a valid
result — zero entry under armed economics would itself be a major finding (route it, don't
"fix" it in-lane).

GUARDRAILS: rule 22 (forecast-mode 2026+; no measured actuals; no holdout year) · rule 12
(all solves sequential in-session) · rule 27 (blob-verify ≥300-line pushes) · rule 28 (you
add NO field and arm NOTHING new — the posture is HEAD's defaults; if you find yourself
wanting a field, STOP and route) · no keeper/shard/marker · no new workflow. Q13's
"this campaign only" scope note: Q25 authorizes THIS campaign only, same as before — say so
in the finding.

COLLISION: D33 (NEISO position lane) writes a position finding — docs only, no shared
surfaces; its result INFORMS interpretation of your capacity trajectory, cite it if landed.
D31 is MISO-side. D20 may edit the forecast scorer for the seven LEGACY legs — your keys are
not in its scope; rebase-care on ff-verdicts.json. D34 edits the carbon_price validation
guard — no overlap with carbon_price_delta usage.

EXIT: the registered campaign (bare neiso-t3, prior golden preserved), the battery records,
the re-scored verdict, and docs/handoffs/FINDING-capx-t3-golden2-<date>.md: the storage-entry
answer (GW by year, which mechanism admitted it), the full gate map vs the first campaign
side-by-side, what the armed posture changed and what it did not, and the honest list of
caveats carried forward. Flag to the director anything that moves a surface outside neiso-t3.
```

## D34 — the carbon_price below-base guard (r#26 amendment; owner ruling Q26)

```
You are the D34 session of the capacity-expansion track — the EXECUTION of owner ruling Q26:
ScenarioConfig.carbon_price KEEPS its documented replace semantics, and gains a LOUD
VALIDATION WARNING when a forecast scenario's carbon_price sits below the resolved base
carbon trajectory in any horizon year — the exact trap the carbon25 arm fell into (D23: a
"carbon price increase" that CUT carbon in every year on an ISO whose base carries the RGGI
trajectory). The warning points authors at carbon_price_delta for increments. No semantics
change, no field, no default move.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the ruling spent the discretion; this is a guard + tests).
BRANCH: claude/capx-d34-carbonprice-guard — FRESH off origin/main, rebase before every push.

READ FIRST: policy/carbon.py::resolve_carbon_price (precedence (i) and its documentation —
which you do not change) · docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md §2
(the trap, in the words you should echo in the warning text) ·
docs/handoffs/FINDING-capx-d26-p1-arm-construction-2026-09-01.md §1–2 (carbon_price_delta —
what the warning points to, and the rule-13 forecast-only guard pattern to mirror) · how
ScenarioConfig runs its other validations (__post_init__ patterns) so the guard sits where
every scenario passes through.

THE GUARD: at scenario validation (or first resolve — pick the seam that fires ONCE per run,
not per hour), when mode == "forecast" and carbon_price is set nonzero and the resolved BASE
trajectory (what would resolve with carbon_price unset) exceeds it in ANY year of the span:
emit one loud, specific warning naming the ISO, the years, both values at the widest gap, and
the sentence "a replace below the base trajectory REDUCES the carbon signal — for an
increment use carbon_price_delta". A WARNING, not an error (Q26 verbatim: guard, not
semantics change) — a deliberate below-base study remains legal and now cannot be silent.
Backcast mode: untouched. Tests: (i) fires on the exact D21/D23 configuration (NEISO,
carbon_price=25, RGGI base); (ii) silent when carbon_price exceeds the base everywhere;
(iii) silent when carbon_price is unset; (iv) silent in backcast mode; (v) the resolver's
output values are BYTE-UNCHANGED in all four (the guard observes, never alters).

GUARDRAILS: no ScenarioConfig field, no default move, no resolver behavior change ⇒ rule 28
NOT triggered — but scenarios.py/carbon.py are core ≥300-line files: edit locally, push exact
bytes, blob-verify (rule 27). Zero solves. No board/verdict/keeper surface. No new workflow.

COLLISION: T3-GOLDEN-2 solves NEISO at HEAD and D31 edits MISO screen code — neither touches
the validation seam; if scenarios.py moves under you, rebase. Nothing else shares your files.

EXIT: the guard + five tests + a short
docs/handoffs/FINDING-capx-d34-carbonprice-guard-<date>.md quoting the warning text verbatim
and citing Q26; note explicitly that R4's semantics question is now CLOSED (replace + guard)
so no successor re-opens it without a new owner act.
```

## D20 — the reconstruction-provenance scorer route (r#26 amendment; director decision §0s.5 executed, hold dissolved)

```
You are the D20 session of the capacity-expansion track — the EXECUTION of the director
decision taken at r#22 (§0s.5) on the seven legacy forecast legs whose run_config.json is a
RECONSTRUCTION: adoption-as-original is REFUSED (it would assert provenance the artifacts
lack); the admissible route is a scorer that recognizes `provenance: "reconstruction"` and
scores it **CAVEAT, never PASS** on the provenance criterion. The hold on this lane was the
scorer being a shared surface under active re-scoring lanes — D26 and D27 have both landed,
so the window is open.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the decision is taken; execution under control-first + STOP rules).
BRANCH: claude/capx-d20-reconstruction-provenance — FRESH off origin/main, rebase before
every push.

READ FIRST: the capx ledger §0s.5 (the decision, verbatim — your charter boundary) · the D8
DOF-ledger finding + D8-V's finding (which legs are the seven, why D8-V was barred from
them, and the FC-7 semantics you extend) · the current FC-7 scoring path in the forecast
verdict instrument (where provenance enters) · the seven legs' committed records in
frontend/data/forecast/ff-verdicts.json (your control set).

THE WORK: (1) the label — the seven legacy legs' run_config artifacts (or their registry
sidecars, whichever the scorer reads) carry an explicit `provenance: "reconstruction"`
marker; nothing else about them is edited, and no reconstruction is upgraded or re-derived;
(2) the scorer — FC-7 recognizes the label and scores the leg's provenance criterion CAVEAT
with a named reason ("run_config is a post-hoc reconstruction"), NEVER PASS, whatever else
the ledger shows; (3) the re-score — control-first: reproduce ALL SEVEN committed records
byte-for-byte with the unmodified scorer BEFORE applying the change, then re-emit exactly
those seven keys. STOP AND ROUTE if: any key outside the seven moves, any criterion other
than FC-7 moves on the seven, or any determination changes in a direction other than the
label route's own (a FAIL-for-missing-provenance becoming CAVEAT-for-reconstruction is the
designed effect; anything else is not). Preserved-baseline (suffixed) keys are NOT re-scored.

GUARDRAILS: the scorer edit is cross-lane infrastructure — the cross-lane re-grade rule is
your operating mode, not a footnote. Rule 27 (scorer files are core; blob-verify). Rule 28
not triggered (no mechanism, no ScenarioConfig field). No keeper/shard/marker; no backcast
surface; no solve. No new workflow.

COLLISION: T3-GOLDEN-2 re-registers the bare neiso-t3 key and runs the scorer at its own
checkout — neiso-t3 is NOT in your seven; rebase-care on ff-verdicts.json and
program-status.json (distinct keys/blocks). D31 will re-register miso-t1h — the bare key now
carries D27's REAL run_config and is NOT in your seven either; only dead legacy legs are.

EXIT: the label + scorer + seven re-emitted keys + a short
docs/handoffs/FINDING-capx-d20-reconstruction-provenance-<date>.md with the control
reproduction, the per-leg before/after FC-7 rows, any determination movement (expected
direction only), and the standing rule restated: a reconstruction can reach CAVEAT, never
PASS — so the only route to a clean FC-7 on those legs is a genuine re-run, which is a
charter decision, not this lane's.
```

## D36 — the storage value-stack timing decomposition (r#27; GOLDEN-2 routed item 1, the D25 §6.3 route)

```
You are the D36 session of the capacity-expansion track. GOLDEN-2 answered the armed-posture
question: the R-A-armed storage-entry economics produce 720 MW of 100-h iron-air in 2050 and
NOTHING in 2026–2049, so the corridor's largest cross-ISO divergence family (zero storage at
the 2030/35/40 anchors, −56.2 % at NEISO; −56..−96 % across four ISOs) SURVIVES the arming —
entry is late, single-tech, cap-bound (0.6 × 1,200 MW), and vanishes under gas ×1.5. Your
question, the D25 §6.3 route now backed by an armed measurement: WHY does the value stack
clear nothing for 24 years — which term is short, by how much, in which years?

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (mechanism decomposition on the entry screen; routing consequences).
BRANCH: claude/capx-d36-storage-valuestack — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-t3-golden2-2026-09-01.md §§5–8 (the measured record —
the 2050 iron-air event, the gas×1.5 sensitivity, the routed question as the lane that
measured it posed it) · spec §5.5 + CLAUDE.md "Storage entry" (the value stack: arbitrage
net of cycling degradation PLUS RA capacity value where MARKET_DESIGN pays;
STORAGE_TECH_BUILD_SHARE_CAP; the cost-decline inputs) · the storage-entry code the golden
exercised (model/capacity evolution, the entry screen's storage branch) ·
docs/handoffs/FINDING-capx-d28-longposition-capacity-revenue-2026-09-01.md (NEISO's RA/FCA
revenue at long positions pays ~$0 — if the RA leg of the storage stack is priced off the
same curve at the same positions, SAY SO: that would make D36 and the D33/D28 position
object one mechanism, not two).

PHASE-0 SCOPE — DECOMPOSE, DO NOT REPAIR: from the registered golden-2 bundle (zero new
solves), reconstruct the entry screen's storage arithmetic year-by-year 2026–2050: (1) the
arbitrage leg (what spread the dispatch actually offered each year, net of degradation);
(2) the RA capacity-value leg (what the NEISO curve paid at the model's position each year —
tie to D28's measured $0-at-long-positions if that is what it is); (3) the cost side (the
per-tech decline curves, which tech becomes cheapest when, why iron-air and why 2050);
(4) the caps and gates (which of STORAGE_TECH_BUILD_SHARE_CAP / availability gates /
normalized-rank actually bound). Name the SHORT term per year and its magnitude. Then state
what a repair would be identified FROM (a published RA accreditation rule, an FCA clearing
record, a cost-curve source — never the corridor row), per rule 13's forward test.

DISCIPLINE: AEO's 1.76 GW by 2030 is CONTEXT, NEVER A TARGET (rule 13; D25's line). If the
decomposition says the model's stack is faithful and the market's early build is driven by
something the model deliberately excludes (state policy procurement, out-of-market
contracts), then the honest answer is a DISPOSITION, not a repair — write it that way and
route the disposition to the corridor table instead.

GUARDRAILS: zero solves; docs only; no mechanism, no ScenarioConfig field, no matrix cell
(rule 28 fires only in a repair lane). No keeper/board/verdict/marker edit; do NOT touch
neiso-t3 or any FC row — the golden session may still be open. Rule 27 on any ≥300-line
push. No new workflow.

COLLISION: the GOLDEN-2 session may still be open — you READ its registered bundle and write
docs only; if the bundle moves under you, cite the version you read by commit. D33 (NEISO
position) is in flight and adjacent on the RA leg — cite, don't duplicate: your job is the
STACK decomposition, its job is the POSITION accounting.

EXIT: docs/handoffs/FINDING-capx-d36-storage-valuestack-<date>.md — the year-by-year
short-term table, the binding-gate census, the one-mechanism-or-two answer on the D28/D33
RA-leg question, and either the identified repair route (with its published source) or the
disposition recommendation. NO repair lands in this lane.
```

## T16-A — the T1.6 re-point execution (r#27; owner ruling Q27; **HELD-DISPATCH: paste only after the GOLDEN-2 session closes**)

```
You are the T16-A session of the capacity-expansion track — the EXECUTION of owner ruling
Q27 (capx ledger §3, 2026-09-01): T1.6 re-points to `entry_rate_limits`. The T16 lane
deleted `renewable_buildout_pace` under rule 26 (consumed by no model code), marked T1.6 out
of service, and pre-registered everything you need; your discretion is spent.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Opus (execution of a ruled re-point under a pre-registered honesty clause).
BRANCH: claude/capx-t16a-ladder-repoint — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-t16-driver-2026-09-01.md IN FULL (the adjudication,
the recommended lever's cited basis, the two rejected alternatives, the ~12-min pricing, and
THE PRE-REGISTERED CLAUSE) · the FC-6 ladder machinery (scripts/run_driver_battery.py, the
Tier-1 rung construction) · plan §2's Tier-1 table (T1.6's cell names an ECONOMIC CONDITION,
not a config field — your first deliverable is to verify and STATE whether pointing the
rungs at `entry_rate_limits` is a re-point WITHIN the existing pre-registration or an
AMENDMENT to it; if amendment, say so in the finding and record it as one — never silently).

THE WORK: (1) wire T1.6's two rungs to `entry_rate_limits` (True = short, False = long) at
the golden-2 vintage; (2) run the 2 rungs (~12 min priced — state actuals); (3) artifact-only
FC-6 re-score of neiso-t3 (control-first: reproduce the committed FC-6 record byte-for-byte
before re-scoring; the battery leg moves SKIP/out-of-service → scored). NO golden re-solve.
STOP if anything beyond neiso-t3's FC-6 rows would move.

THE HONESTY CLAUSE, verbatim from T16 and binding: the REC dual sits pinned at the $50 ACP
ceiling in every year of both D21 rungs with 33.0 GW of VRE built — a correctly-wired lever
may still not move it. **If it does not move, that is a REAL RPS/ACP finding — the dual
escaping to its cap — reported as the outcome. NEVER a third lever tried until one moves.**
Either rung outcome is a valid result.

GUARDRAILS: rule 28 — `entry_rate_limits` already exists and no default moves; you add no
field; the T1.6 matrix/ladder records are updated to the re-pointed lever with the Q27
citation. Rules 22/27 as usual. No keeper/shard/marker; nothing in the backcast namespace.

COLLISION: this prompt is HELD until the GOLDEN-2 session closes because you write
neiso-t3's FC-6 rows — if you are reading this as a running session, the director has
confirmed it closed; still rebase before every push. D36 reads the golden bundle and writes
docs only — no shared writes. D35 (P2 scope) is QUEUED and not running — if you find it
running, STOP and report.

EXIT: the re-pointed rungs + their results + the re-scored FC-6 +
docs/handoffs/FINDING-capx-t16a-ladder-repoint-<date>.md stating: re-point-vs-amendment (the
plan §2 verification), both rung outcomes at full magnitude, whether the REC dual moved (and
the RPS/ACP finding if not), and the FC-6 battery-leg status after (scored, or CAVEAT with
the named reason).
```

## D35 — the FC-6 P2 instrument-scope repair (r#28; GOLDEN-2 routed item 2, released on golden-close)

```
You are the D35 session of the capacity-expansion track. GOLDEN-2's FC-6 battery surfaced a
NEW, root-caused instrument-scope object and left it standing as scored: **P2 FAILs
("year 2050: wrong: gas_cc↓") while the all-gas sign is correct.** The leg tests
unabated-gas_cc generation FALLING under gas ×1.5 at the last common year — but the BASE
world holds ZERO unabated CC at 2050 (the fleet is 100 % CCS-converted by 2040), while the
gas ×1.5 world retrofits LESS (the retrofit's fuel-cost penalty scales with gas price:
CCS 9,846.8 vs 13,135.4 MW) and builds MORE late unabated CC. On 25-year evolution pairs
the leg crosses the CCS class migration — the same family as D23's P1 attribution: the
instrument measuring its own construction, not the model. You adjudicate the correct scope,
repair the checker, and re-score.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (instrument semantics on a novel object; a committed FC-6 row moves).
BRANCH: claude/capx-d35-p2-scope — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-t3-golden2-2026-09-01.md §7.1 (the P2 evidence, the
root cause as the lane measured it) · docs/handoffs/FINDING-capx-d23-p1-carbon-sign-*.md +
FINDING-capx-d26-p1-arm-construction-*.md (the family precedent: what "the instrument
measured its own premise" looked like, and what a repair that measures the MODEL looks
like) · scripts/check_forecast_invariants.py --paired (the P2 leg's implementation) · the
committed golden-2 fc6/ bundles (base `706e7ba8`, carbon_plus25, gasup150, gaspm5 — your
artifact set; NO new solves needed).

THE ADJUDICATION, yours to make and defend: what SHOULD the gas-up driver leg measure on a
25-year evolution pair where the CC class migrates to CCS? Candidates the finding implies
(adjudicate, don't assume): the whole gas_cc family including CCS-converted units; total
gas-fired generation; the last year BOTH worlds hold unabated CC; a
capacity-migration-aware construction. The repaired leg must (a) measure a real
model-response claim with a defensible sign expectation, (b) stay meaningful on ISOs whose
fleets do NOT migrate, (c) not be constructed so the golden passes — state the expected
verdict BEFORE running the repaired checker, then report what happened at full magnitude.

THE RE-SCORE: artifact-only, control-first — reproduce the committed FC-6 record
byte-for-byte with the unmodified checker, then apply the repair and re-score neiso-t3's
FC-6. PRESERVE T16-A's battery-row state (CAVEAT-measured, series [1.0, 1.0]) — you touch
the P2 row and nothing else. STOP AND ROUTE if anything beyond neiso-t3's FC-6 P2 row (and
the FC-6 rollup it feeds) would move. EITHER outcome of the repaired leg is valid — a
surviving FAIL now measures the model, which is the point.

GUARDRAILS: rule 27 (checker is core; blob-verify); rule 28 NOT triggered unless you add a
ScenarioConfig field (you should not need one — this is checker scope, not model config);
no keeper/shard/marker; no backcast surface; zero solves. Cross-lane re-grade is your
operating mode. No new workflow.

COLLISION: D38 edits the FC-5 disposition rows + the golden-2 finding text — no shared
files with your FC-6 work; rebase-care on ff-verdicts.json (distinct rows). D31/D33/D30 are
MISO/NEISO-position/45Q docs lanes — no overlap.

EXIT: the adjudication + repaired checker + tests + the re-scored P2 row +
docs/handoffs/FINDING-capx-d35-p2-scope-<date>.md with the scope decision defended, the
pre-stated expectation graded, the control reproduction, and the FC-6 state after — plus an
explicit line on whether the repaired leg changes anything for the OTHER five ISOs' future
FC-6 runs (the leg is cross-ISO instrument code; rule 25 governs verdicts, not the checker).
```

## D38 — the D36-routed records pair (r#28; corridor rows + the golden-2 wording correction)

```
You are the D38 session of the capacity-expansion track — a records-only lane executing D36's
routed items 1 and 3. Zero solves, zero scorer edits, no verdict moves.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the content is specified in D36 §7/§8; execution).
BRANCH: claude/capx-d38-d36-records — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d36-storage-valuestack-2026-09-02.md §7 (the
disposition text you are transcribing — the procurement-channel explanation and the R-1
residual, in the lane's own words) and §8 items 1 + 3 ·
results/ff-corridor/dispositions/neiso-t3.json (the three `capacity:storage` rows you
re-author) · docs/handoffs/FINDING-capx-t3-golden2-2026-09-01.md §6.1 (the sentence being
corrected).

THE WORK:
1. Re-author the three `capacity:storage` rows in the neiso-t3 disposition file with the
   D36 §7 explanation (procurement-channel driver + the R-1 residual named), citing D36.
   CONTROL-FIRST: byte-check the file's current state against the committed version before
   editing; the rows are already EXPLAINED DIVERGENCE and MUST remain so — if your edit
   would change any row's category or any verdict anywhere, STOP: that is not this charter.
2. The golden-2 §6.1 correction as a DATED ANNOTATION (never a rewrite): the 2050 storage
   clearing is a data-channel result (the RC-R demand-curve intake re-times exits, tightening
   the 2049 stack), not a D-3-rank result — the rank is sign-preserving. One paragraph,
   marked "Correction 2026-09-02 (D38, routed by D36 §8.3)", appended at the section.

GUARDRAILS: records only — no scorer, no FC row, no board, no keeper/shard/marker, no
ScenarioConfig. Rule 27 on any ≥300-line file (the golden-2 finding qualifies: edit locally,
push exact bytes, blob-verify). If the disposition file's schema resists a clean re-author,
report rather than force. No new workflow.

COLLISION: D35 edits FC-6 checker + ff-verdicts P2 row — no shared files. The FC-5
disposition file is yours alone this window.

EXIT: the re-authored rows + the annotation + a SHORT
docs/handoffs/FINDING-capx-d38-d36-records-<date>.md (a page: what changed, the control
check, confirmation that no category or verdict moved).
```

## D32 — the floor-retention composition monopoly (r#29; D27's R5, unlocked by D31)

```
You are the D32 session of the capacity-expansion track — the owner of MISO's non-coal exit
channel, the residual every repair has now sharpened. The chain: D17 attributed the missing
3.93 GW of non-coal exits to cap rationing; D27 released the cap and coal ate all of it
(selection, not depth); D31 landed the faithful capacity-revenue repair and the residual
swung to −74.3 % UNDER, localized to the margin/selection side. D27's R5 named your object:
`_apply_reliability_floor` selects retention in ascending going-forward-cost-per-firm-MW
(`_floor_retention_merit`), so WHENEVER THE FLOOR BINDS, exit composition is a pure function
of per-fuel FOM ranking. The real 2021–2025 MISO cohort — 3 large gas steamers plus a
158-unit small tail — is emphatically NOT FOM-rank-ordered. The question is structural, with
an external observable.

DATA PROFILE: miso
MODEL ASSIGNMENT: Fable (a selection-mechanism adjudication with an external observable and
rule-21 exposure).
BRANCH: claude/capx-d32-floor-retention — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md (R5 as posed;
the enriched pipeline_events evidence class) ·
docs/handoffs/FINDING-capx-d31-miso-caprev-repair-2026-09-02.md §5 (whether and where the
floor still binds AFTER the repair — your starting census) and §7 (the −74.3 % localization)
· `_apply_reliability_floor` / `_floor_retention_merit` and the floor_retention_log
attribution · the real cohort record (the confirmed/announced retirement data already
in-repo).

PHASE-0 SCOPE — CHARACTERIZE THE SELECTION RULE, DO NOT TUNE IT:
(1) With D31's repair at HEAD, census where the floor binds 2021–2025 and what
    _floor_retention_merit retained vs released, unit by unit, vs the real cohort.
(2) Adjudicate the RULE, not the ranking: cheapest-firm-adequacy is defensible as
    PROCUREMENT — is retention-by-FOM-rank a defensible model of which units actually EXIT
    when a floor binds? Name what a real ISO's process holds back (RMR designations,
    must-run agreements, location/deliverability, suspension-vs-retire) and which of those
    have PUBLISHED, per-unit, forward-regenerable identification (rule 13's test).
(3) For each candidate re-specification of the retention key: its external driver, its
    identification source, and its expected composition consequence — stated BEFORE any
    implementation, which this lane does NOT do.
RULE 21 [R-DOF], the charter's hard wall: a tuned retention weight is forbidden — the
−74.3 % residual is CONTEXT for where the error lives, never the identifier of any
parameter. If no published per-unit driver exists, say so and route the honest dead end.

GUARDRAILS: zero solves (D31's bundle + the enriched events are your data). Docs only; no
mechanism lands, no ScenarioConfig field, no matrix cell (the repair lane, if chartered,
takes rule 28). No keeper/board/verdict/marker. Rule 27 on any ≥300-line push.

COLLISION: D40/D41/D39 are NEISO/CCS/cross-ISO-docs — no shared files. miso-200 (owner's
backcast lane) writes the MISO backcast namespace — distinct. Rebase-care on docs/.

EXIT: docs/handoffs/FINDING-capx-d32-floor-retention-<date>.md — the post-repair binding
census, the unit-level retained-vs-released vs real-cohort table, the adjudication of the
selection rule with each candidate's published identification (or the honest absence), and
a routed recommendation. NO repair lands in this lane.
```

## D40 — the NEISO requirement devintage (r#29; D33's R-A/R-B executed)

```
You are the D40 session of the capacity-expansion track — the repair lane D33 routed. D33
measured: NEISO's position error (+21/+6/+7 reserve-ratio points past the FCA zero-cross in
the $0 years) is DOMINATED by a requirement-denominator artifact — a single-vintage
composite ratio held flat across delivery years — while the published per-CCP Net ICR
series is ALREADY COMMITTED IN-REPO, and the model's census supply is actually SHORT of
what the real FCAs cleared. You implement R-A (and R-B as D33 specifies it): resolve the
NEISO adequacy requirement from the published Net ICR series, the exact pattern
`resolve_adequacy_requirement_mw` already uses to prefer PJM's published FPR over the
composite (`retirements.py:1086-1096`), with the card C-A hold-last convention beyond the
last published year.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Fable (a load-bearing requirement resolution changes the screens; arming
posture and LOYO scoring are adjudications).
BRANCH: claude/capx-d40-neiso-devintage — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d33-neiso-position-2026-09-02.md IN FULL (R-A/R-B as
routed — their exact specification is your charter boundary; the census-supply-SHORT finding
that bounds what this repair can and cannot explain) · `retirements.py:1086-1096` (the
PJM-FPR precedent you mirror) · the committed Net ICR series (D33 names where) · the S-123
precedent (the MISO requirement repair — the registry-constant pattern, and its lesson: a
requirement repair RELEASES budget, it does not choose composition).

THE WORK: (1) the resolver prefers the published per-CCP Net ICR series for NEISO, per-year,
hold-last beyond the last published CCP (C-A convention), composite as the documented
fallback; (2) rule-28 duties in the same PR — the resolution lever's matrix row + per-ISO
shard cells, **DEFAULT-OFF**; (3) rule-22 discipline as D33 pre-stated it: the arming
verdict is scored **LEAVE-ONE-YEAR-OUT within 2023–2025 BEFORE any keeper or default
moves** — in-sample gain with held-out degradation is overfitting, not skill; (4) measure
the consequence at the screen grain (positions per year, floor binding, capacity-revenue at
the corrected positions) on committed artifacts — a NEISO T1-H re-run is D37's, not yours:
your exit hands D37 its armed-or-not input.

RULE-14 SIGN DISCIPLINE: the corrected (lower, per-year) requirement SHORTENS the model's
position → capacity revenue moves UP → NEISO retirements get HARDER. Nothing is sized by any
residual; the Net ICR series is the identification, full stop.

GUARDRAILS: rules 22/27/28 as above; no keeper/shard/marker; the backcast namespace
untouched (the requirement resolution is used by forecast screens — if you find a backcast
consumer, STOP and report the blast radius before landing anything). No new workflow.

COLLISION: D39 reads entry screens docs-only; D41 owns the CCS retrofit constants; D32 is
MISO-side. Nobody else touches the NEISO requirement seam or registry this window.

EXIT: the resolver + registry data path + matrix row/cells (default-off) + the LOYO score +
the screen-grain consequence + docs/handoffs/FINDING-capx-d40-neiso-devintage-<date>.md with
the per-CCP table, the LOYO result at full magnitude, the arming recommendation (the owner
arms; you recommend), and the explicit handoff line to D37.
```

## D41 — the CCS fixed-cost re-identification (r#29; D30's two defective legs)

```
You are the D41 session of the capacity-expansion track — the repair lane for D30's
adjudication: the 45Q mechanism is the intended reading, but TWO fixed-cost legs wrongly
clear the retrofit bar. (i) `fixed_om_gas_cc_ccs` = 25 sits BELOW `fixed_om_gas_cc` = 30
because the G-32 ATB flip raised the host CC's FOM 12 → 30 and left the "host + capture
island" value behind — so every retrofit is PAID $5,000/MW-yr in fixed-cost savings instead
of being CHARGED the capture island's O&M. (ii) `ccs_retrofit_capex_kw` = 900 carries an
unstated dollar-year and a `needs-citation` flag, and is 59 % of the capture-island
increment the model's own new-build CCS carries on the ATB-2024 2026$ basis. You re-identify
both from the ATB basis, with citations, and measure the screen-grain consequence.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (the identification source and direction are fully specified by D30;
this is execution under rule 23).
BRANCH: claude/capx-d41-ccs-fixedcost — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d30-45q-pace-2026-09-02.md IN FULL (the two legs, the
G-32 history, the ATB-2024 arithmetic it already did — your numbers likely already exist
there and need only be landed with citations) · docs/parameter-citations.md (where both
values' citations live and the citation format) · the G-32 record (the ATB flip that created
the inconsistency) · spec §5.6 + the retrofit screen implementation (the consumer).

THE WORK: (1) `fixed_om_gas_cc_ccs` re-identified on the same ATB-2024 basis as the host's
30 — host FOM PLUS the capture-island O&M increment, cited (rule 23: the re-derivation
commit cites the DATA change — the G-32 flip — never a residual); (2) `ccs_retrofit_capex_kw`
re-cited on the ATB-2024 2026$ capture-island increment with the dollar-year STATED and the
`needs-citation` flag cleared; (3) constants/citations updated together, tests pinning both
values to their cited sources; (4) MEASURE at screen grain only: re-run D30's own
decomposition arithmetic at the corrected values — which units still clear the bar, does the
cap still bind, the per-leg margin table before/after. **NO golden re-solve is licensed**
(Q13/Q25 this-campaign-only stand); do not re-run any full-horizon campaign or T1-H leg —
route the follow-on measurement needs in the finding.

RULE-14 LINE, stated because the corridor moves: the corrected legs make retrofits LESS
attractive → less CCS → the FC-5 CCS rows move TOWARD AEO. That is a consequence, never a
target — nothing is sized by the corridor distance, and the FC-5 dispositions are
re-authored only by a records lane after the next registered run, not by you.

GUARDRAILS: rule 23 (citations to primary sources in the same commit); rule 27 (constants
live in ≥300-line core files — edit locally, push exact bytes, blob-verify); rule 28 NOT
triggered (values move, no field is added and no default posture flips — but SAY SO in the
finding, and if you find either value is actually a registered cache-key field whose change
re-keys configs, STOP and report the blast radius first). No keeper/board/verdict/marker.
No new workflow.

COLLISION: D40 owns the NEISO requirement seam; D32/D39 are docs lanes. The retrofit screen
constants are yours alone this window.

EXIT: the two re-identified values + citations + tests + the screen-grain before/after +
docs/handoffs/FINDING-capx-d41-ccs-fixedcost-<date>.md with the cited derivations, the
cap-binding answer at corrected values, and the routed follow-on (which registered runs are
now stale on this axis, for the director to sequence — never re-run here).
```

## D39 — the entry-stack under-build, cross-ISO Phase-0 (r#29; T16-A outcome B + D36 converge)

```
You are the D39 session of the capacity-expansion track — Phase-0 of the object two
instruments measured independently in one week: T16-A found NEISO's REC dual pinned at the
$50 ACP ceiling in all 50 arm-years (the RPS target unreachable at every VRE volume the
entry stack builds, 4.1 → 37.1 GW), and D36 found the storage arbitrage leg short by
$50–150/kW-yr in every year. One shape: THE ENTRY STACK UNDER-BUILDS relative to both the
RPS constraint and every external view (the corridor's renewables rows). The chartered
route D36 named: the `entry_forward_expectation_signal` family — the entry screen's forward
price expectation — cross-ISO, every screen, NOT a storage lane and NOT an RPS lane.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (a cross-ISO mechanism question on the program's entry economics).
BRANCH: claude/capx-d39-entry-underbuild — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-t16a-ladder-repoint-*.md (the RPS/ACP finding at
full magnitude) · docs/handoffs/FINDING-capx-d36-storage-valuestack-2026-09-02.md §§2–6 +
§8.2 (the arbitrage-short table and the routed signal question) · the entry screen's price
expectation construction (what forward prices the economic-entry screen actually uses:
prior_results duals? a flat extrapolation? per-ISO?) · the matrix rows for the
entry-signal family (`entry_forward_expectation_signal`, `entry_margin_exhaustion`,
`entry_forward_reserve_leg` — the ERCOT pair is K-forecast-armed via Q15; NEISO's cell is
`U`; rule 25: nothing transfers, but the ERCOT identification PATTERN is citable) ·
docs/handoffs/FINDING-capx-d33-neiso-position-2026-09-02.md + D31's finding (the corrected
position/requirement context you now have — cite, don't re-derive).

PHASE-0 SCOPE — ONE QUESTION, CHARACTERIZED CROSS-ISO: does the entry screen's forward
expectation systematically UNDERSTATE the revenue a marginal entrant would actually earn —
and if so, through which term (energy price expectation, reserve leg, REC/EAC leg, capacity
leg), per ISO? For each ISO: reconstruct what the screen expected vs what the model's own
NEXT-YEAR solve actually paid at the margin (the model's own realized prices are the
in-model observable — no external target). The NEISO golden-2 horizon + T16-A arms are the
richest committed evidence; use ERCOT's armed pair as the worked example of what a
identified repair looked like there. Name, per ISO, what a repair would be identified FROM.
DISCIPLINE: the corridor's renewables rows and AEO are CONTEXT, never targets (rule 13);
rule 25 — per-ISO parameters and verdicts, always.

GUARDRAILS: zero solves; docs only; no mechanism, no field, no matrix cell edits beyond
evidence citations IF a lane convention requires none at Phase-0 (it does not — leave cells
alone). No keeper/board/verdict/marker. Rule 27 on any ≥300-line push. No new workflow.

COLLISION: D40 (NEISO requirement seam), D41 (CCS constants), D32 (MISO floor docs) — no
shared files; cite whichever of their findings are current when you finish.

EXIT: docs/handoffs/FINDING-capx-d39-entry-underbuild-<date>.md — the per-ISO
expected-vs-realized margin table, the term attribution, the per-ISO identification
sources, and a routed recommendation (which ISOs get repair lanes, in what order, and
whether the NEISO `U` cell should open first given D40's corrected requirement). NO repair
lands in this lane.
```

## D37 — the NEISO T1-H at the armed posture (r#30; GOLDEN-2 item 4 + D40's handoff; Q28 posture)

```
You are the D37 session of the capacity-expansion track — the NEISO capacity hindcast
(T1-H) re-run that three chains have been waiting for: GOLDEN-2 routed it (FC-3's evidence
carries the pre-arming leg), D40 built its requirement lever and declared the post-wave
years UNSCOREABLE until this run, and owner ruling Q28 armed that lever FOR THIS
MEASUREMENT ONLY.

DATA PROFILE: neiso
MODEL ASSIGNMENT: Opus (the posture is ruled, the expectations are D40's numbers; this is a
pre-declared re-measure — the D27/D4-M pattern).
BRANCH: claude/capx-d37-neiso-t1h-armed — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d40-neiso-devintage-2026-09-02.md IN FULL (the
lever, the screen-grain consequences at the clean entry — +21.4 → −2.1 pts — the LOYO
result, and the explicit D37 handoff line) ·
docs/handoffs/FINDING-capx-d33-neiso-position-2026-09-02.md (the census-supply-SHORT bound)
· the committed neiso-t1h record + run_config (your baseline) · the D27 finding (the
preserve-then-overwrite + pre-declaration pattern you copy).

THE POSTURE, exactly (Q28): HEAD recipe + the D40 Net ICR requirement lever ON in this
run's config (the run_config records it; the SHIPPED DEFAULT STAYS OFF — you flip nothing)
+ `entry_screen_diagnostics=True` (the D36/D39 zero-cost precondition — output-only, no
cache-key term; VERIFY that claim against the cache-key registry before the solve and say
so).

THE RUN: pre-declaration FIRST, pushed before the solve (direction + rough magnitude on:
per-year positions vs D40's screen-grain table; floor binding; capacity revenue at the
corrected positions; FC-3's retire/build legs; the honest note that D40's clean-entry
figure does not guarantee the post-wave years). Then the NEISO T1-H leg, years sequential
(rule 12). Then grade every prediction at full magnitude, misses included.

REGISTRATION: preserve-then-overwrite — the current neiso-t1h record to a dated suffix,
the re-measure to the bare key; refresh the NEISO board block; STOP if anything beyond
neiso-t1h's rows would flip (cross-lane re-grade). Note for your finding: with D41's
corrected CCS constants at HEAD, your bundle is the FIRST NEISO capacity run on the
repaired retrofit economics — state what the screen did on that axis even though it is not
your object.

GUARDRAILS: rules 22 (hindcast years only, no holdout), 27 (blob-verify), 28 NOT triggered
(no field added; the lever exists — you arm it per Q28 in-config only). No keeper/shard/
marker; the backcast namespace untouched. Solve priced before launch. No new workflow.

COLLISION: D42 (MISO) and D43 (CAISO) share no files; nobody else touches neiso-t1h or the
NEISO board this window. Rebase-care on docs/ and ff-verdicts.json.

EXIT: the registered re-measure + graded pre-declaration +
docs/handoffs/FINDING-capx-d37-neiso-t1h-armed-<date>.md: the per-year position table vs
D40's, FC-3's state after, the CCS-axis note, whether the post-wave years now score, and
the explicit line the arming decision needs — does the measured result support flipping the
Net ICR default (the owner decides; you recommend on the evidence).
```

## D42 — the fossil announced-date A/B (r#30; D32 R1 + owner ruling Q29)

```
You are the D42 session of the capacity-expansion track — the A/B owner ruling Q29
chartered on D32's R1. The finding behind it: post-repair, MISO's reliability floor decides
100 % of exit composition, its selection is measured indistinguishable from random against
the real 2021–2025 cohort, and the ONE published per-unit driver that discriminates is the
owner's filed retirement date — which `forecast_fossil_retirement_economic=True`
deliberately no-ops for fossil. This lane MEASURES the alternative posture. Nothing arms:
both legs register SUFFIXED, the bare key is untouched, and the posture decision returns to
the owner with the evidence.

DATA PROFILE: miso
MODEL ASSIGNMENT: Fable (a spec-§5.1-adjacent posture measurement with a rule-19
reconciliation to design).
BRANCH: claude/capx-d42-fossil-dates-ab — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d32-floor-retention-2026-09-02.md IN FULL — its §7
R1 is your charter body: the pre-declared numbers (coal +9.7 GW, gas_st +1.1, oil +0.3,
gas_ct +0.2 carried by the channel; recall 5/19 → ≥13/19; the six deferred/sold coal plants
≈6.5 GW of false positives), the vintage gate (2020), the reversal-registry arming, and the
economic-screen-as-residual construction · CLAUDE.md capacity-evolution step 1 +
`apply_announced_retirements` / `load_announced_reversal_plants` (the machinery that
already exists for non-fossil — you are extending a path, not inventing one) · the
EIA-860 announced-retirement data in-repo (the identification; vintage-gated per the
hindcast information rule, same as step 0's instrument_date gate).

THE A/B: control = the shipped posture at HEAD, replayed. Arm = fossil EIA-860 planned
dates honored as an exogenous step-1 input, vintage-gated at 2020 (a date is admissible in
year Y only if filed before Y's cutoff — the rule-13 forward test: the same construction
regenerates for a forecast year from the then-current 860), the reversal registry armed,
and the economic screen running on the RESIDUAL fleet. THE RULE-19 RECONCILIATION IS
IN-CHARTER, not an afterthought: when a date fires for a unit, the economic screen must not
double-count that unit's exit, and the floor's retention pool must see the dated units as
exogenous — design it, document it, test it. THE DEFERRAL CLASS: the six deferred/sold
plants are countered ONLY by a published per-unit instrument (a filed deferral, an RMR, a
sale record with continued operation) — NEVER a fitted filter; if no instrument exists,
take the false positives at full magnitude and report them.

SCORING: MISO T1-H 2021–2025 both legs, LOYO within 2023–2025 per rule 22, the D32
pre-declared table graded at full magnitude (recall, composition by fuel, false positives,
G3, false_retire). Registration: BOTH legs SUFFIXED (e.g. miso-t1h-d42-control /
-d42-dates); the bare miso-t1h key is NOT taken; the MISO matrix shard gets the posture
lever's row/cell (rule 28 — the new gate field ships DEFAULT-OFF in the same PR).

GUARDRAILS: rules 12 (years sequential per leg), 13 (the vintage gate is the admissibility
test — state it in the schema/notes), 22, 27, 28 as above. No keeper/shard/marker beyond
the matrix duty; the backcast namespace untouched. Nothing arms — the finding ends with
the evidence and a recommendation, and the decision line reads: THE OWNER ARMS OR
DECLINES; this lane did neither.

COLLISION: D37 (NEISO) and D43 (CAISO) share no files. The step-1 fossil path is yours
alone this window; D33-M's additions machinery is adjacent but landed — rebase, don't
re-derive. Rebase-care on docs/ and the MISO shard.

EXIT: both suffixed registrations + the reconciliation design + the graded pre-declaration
+ docs/handoffs/FINDING-capx-d42-fossil-dates-ab-<date>.md with the LOYO table, the
composition before/after by fuel, the deferral-class handling at full honesty, and the
posture recommendation for the owner.
```

## D43 — the CAISO dispersion A/B (r#30; D39 §7's CAISO-first single-term isolation)

```
You are the D43 session of the capacity-expansion track — the first repair measurement on
D39's object: the entry stack under-builds through ONE term, the energy leg's DISPERSION,
which the zone-flat tail-free stack re-price shared by five ISOs discards. D39 ranked
CAISO FIRST: the largest committed expected-vs-realized gap (peaker 0.00–0.07,
CC 0.07–0.92, storage 8–12×, sign flips in both the thermal and VRE screens at
entering-2024), the replay already in place, and a capacity leg whose correction is
measured INERT (0.0 MW) — the cleanest single-term isolation in the program.

DATA PROFILE: caiso
MODEL ASSIGNMENT: Fable (a novel mechanism construction on the entry screen; arming
consequences are cross-ISO in code even though verdicts are per-ISO).
BRANCH: claude/capx-d43-caiso-dispersion — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md IN FULL — §7.2's
CAISO construction and pre-declaration basis are your charter body; §3's
expected-vs-realized method is your instrument · the entry screen's stack re-price
implementation (the zone-flat tail-free construction D39 names) · the CAISO replay/probe
records D39 cites · the matrix entry-signal family rows (ERCOT's armed pair is the worked
PATTERN; rule 25 — CAISO's parameters come from CAISO's own record, nothing transfers).

THE MECHANISM, identified from the model's own record (rule 13): a dispersion-carrying
expectation — the screen re-prices the entrant against the realized price DISTRIBUTION
(the prior solve's own hourly duals: duration/deciles at the entrant's zone), not the flat
mean. Design the exact construction yourself (that is the Fable half): it must (a) use
only in-model prior-solve quantities that regenerate every forecast year, (b) carry no
fitted parameter — the distribution IS the identification, (c) ship as a gated
ScenarioConfig mechanism, DEFAULT-OFF, with rule-28 duties (matrix row + a cell line in
every ISO shard, CAISO's cell carrying this A/B's verdict) in the same PR.

THE A/B: control = shipped screen replayed on the D39 basis; arm = the dispersion
construction ON, CAISO only. Pre-declare from D39 §7.2's numbers BEFORE the arm runs
(which screens flip sign, which classes' expected-vs-realized ratios close, the entry
composition consequence). Score at the screen grain first; run the smallest solve that
makes the A/B observable (D39 names what the replay covers — if screen-grain replay
suffices, run NO new LP and say so; if a T1-H leg is needed, price it, run years
sequential, register both legs SUFFIXED — the bare caiso keys are untouched).

DISCIPLINE: the corridor's renewables rows and AEO are context, never targets (rule 13);
nothing is sized by any residual — the distribution is the whole identification. Rule 25:
the construction is shared code but the VERDICT is CAISO's; other ISOs' cells stay U until
their own lanes run it.

GUARDRAILS: rules 12/22/27/28 as above; no keeper/shard/marker beyond the matrix duty;
backcast namespace untouched. Nothing arms as default — the finding recommends, the owner
decides.

COLLISION: D37 (NEISO) and D42 (MISO) share no files; the entry-screen re-price code is
yours alone this window — if D37's solve is running when your shared-code change lands,
its container is isolated (no interference), but note the vintage in both findings.

EXIT: the gated mechanism + the A/B (screen-grain, plus the smallest observable solve if
needed) + graded pre-declaration +
docs/handoffs/FINDING-capx-d43-caiso-dispersion-<date>.md with the expected-vs-realized
closure table, the entry-composition consequence, the cross-ISO code note (what other
lanes would run), and the arming recommendation for the owner.
```

## D44 — arm the fossil announced-date default (r#31; owner ruling Q30) — **LANDED** PR #4639 (`57088c33`, 2026-09-03; graded at r#32 amendment 1 — the r#32 pin briefly read it unlaunched)

```
You are the D44 session of the capacity-expansion track — the EXECUTION of owner ruling Q30
on D42's decisive A/B (recall 5/19 → 16/19, zero screen displacement, per-unit published
deferral counters): the fossil announced-date channel ARMS AS THE DEFAULT POSTURE.

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (ruled and mechanical — but the files are core, so rule 27 is this
charter's spine).
BRANCH: claude/capx-d44-fossil-dates-arm — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md IN FULL (the
channel as built: the gated field, the vintage gate, the reversal registry, the rule-19
reconciliation, the deferral counters — you flip and document, you do not redesign) · the
capx ledger §3 Q30 (the ruling's exact scope) · CLAUDE.md capacity-evolution step 1 (the
text you amend) · model-methodology-spec.md §5.1 (same) ·
scenarios.py's _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS ledger (the b′-1 append-only declared
defaults — the flip ADDS a dated declaration line; D24-R's discipline).

THE WORK:
1. Flip the D42 gate field's default ON in ScenarioConfig, with the Q30 citation at the
   definition. Append the dated declaration to _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS (never
   overwrite — b′-1 is append-only; this is exactly the flip class it exists for).
2. Amend CLAUDE.md's step-1 bullet ("for fossil this step is a default no-op") and spec
   §5.1 to the new posture: fossil owner-filed EIA-860 dates honored as an exogenous step-1
   input, vintage-gated, reversal registry armed, economic screen on the residual fleet,
   with the D42/Q30 citation. Precise, minimal edits — CLAUDE.md and the spec are ≥300-line
   core files: edit locally, push exact bytes, blob-verify after push (rule 27), and NEVER
   regenerate either file wholesale.
3. Re-stamp the channel's matrix row/cells to the armed-default posture (Q30 citation);
   MISO's cell carries the D42 A/B verdict; other ISOs' cells note default-on with their
   own verdicts pending their own measurements (rule 25).
4. CHANGELOG + a short docs/handoffs/FINDING-capx-d44-fossil-dates-arm-<date>.md: what
   flipped, the declared-defaults line, the doc amendments quoted, and the consequence
   line: every future forecast/hindcast solve carries the channel; existing bundles join
   the batched re-measure decision (the director's queue — do NOT re-run anything here).

GUARDRAILS: no new field, no parameter values, no solve. Rule 22 untouched. The one
default flip is the entire licensed change; if anything else asks to move, STOP and route.

COLLISION: D45 runs PJM/NYISO solves — if its containers launched before your flip lands,
their bundles record the OLD posture; that is a vintage fact for their findings, not a
conflict. Nobody else touches scenarios.py/CLAUDE.md/spec this window.

EXIT: the flip + amendments + matrix + CHANGELOG + the finding, all blob-verified.
```

## D45 — PJM + NYISO capacity curves: the once-only D6+R3 joint charter (r#31) — **CHECKPOINT at r#32; RULED DEAD at r#33 (Q33) — superseded by §D45-R below; never re-paste this charter** (PRs #4643/#4647/#4649: PJM L1 registered + stages 2/3 written; **OWED: NYISO L2/L3, PJM L4, finding §4–§9 and the §9 close-out** — graded a checkpoint, not lost; a session resuming this charter starts from the committed finding's placeholders)

*r#32 amendment (recorded OUTSIDE the charter text, which does not move): the NYISO keeper is now `2026-09-02-nyiso-177-vintage-matched` (promoted 2026-09-02 by owner ruling; NOT-YET on {C1-2023 ST_GAS, C3a-2025, C3c}); PJM's is unchanged (`2026-08-15-pjm-162-inputclock`). The charter names no keeper id, so nothing in it changes — but the per-leg vintage line it already requires must name the keeper id per ISO alongside the fossil-dates posture. Also note: the forecast board's gate-(a) stamps for NYISO/MISO/CAISO were stale at r#32 (ledger §0ac.2) — read the keeper from `keepers/<ISO>.json`, never from `program-status.json`.*

```
You are the D45 session of the capacity-expansion track — the ONCE-ONLY cross-ISO
clearing-half + curve-ON charter (queued since r#26 as "D6+R3"), finally written against
what remains after the repair wave. The other four ISOs are done or owned: MISO has the
supply_accounting_ratio + published RBDC (D31), NEISO the Net ICR devintage measured to
±3.3 pts (D40/D37), ERCOT is curve-OFF energy-only, CAISO has no capacity market in the
program's design. PJM and NYISO are the two capacity-market ISOs NO repair lane has
touched: no diagnostics-on solve exists for either, and D28's NYISO row is the program's
loudest latent finding — the curve is NEVER CONSULTED at default (a flat $110/kW-yr
over-pays 2–6×), and a curve-ON probe would arm at +123 % retirements.

DATA PROFILE: pjm  (widen to nyiso when the NYISO half runs — hydration is incremental)
MODEL ASSIGNMENT: Fable (the once-only mechanism-class adjudication; arming consequences
on two ISOs).
BRANCH: claude/capx-d45-pjm-nyiso-curves — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d28-longposition-capacity-revenue-2026-09-01.md
(the four-ISO census; the PJM and NYISO rows — PJM's position +9..+14 pts hindcast-
confirmed, NYISO's LATENT flip-gate evidence; §6.5's clearing-half statement: the curve is
evaluated at a census quantity where every real market clears supply against the curve) ·
the D31 finding (the MISO worked example: supply-accounting reconciliation + published
curve shape) · the D40/D37 findings (the NEISO worked example: requirement devintage,
paired control, P9-style pre-stated flip conditions) · the PJM/NYISO curve implementations
+ docs/parameter-citations.md (what is published-faithful already, what is flat-default) ·
docs/handoffs/FINDING-capx-d43-caiso-dispersion-2026-09-02.md §routing (the PJM/NYISO
diagnostics precondition this charter absorbs).

THE CHARTER, three stages per ISO, PJM first then NYISO, sequential:
1. FIRST DIAGNOSTICS-ON T1-H SOLVE at the live stack posture (`entry_screen_diagnostics`
   on; pre-declaration first, the D37 pattern; preserve-then-overwrite on the bare t1h key;
   this also commits the expected-side dumps the dispersion family lacked — a free
   by-product, not an object).
2. THE POSITION + EVALUATION-QUANTITY RECONCILIATION, per ISO, from published data ONLY
   (rule 25 — own parameters; the MISO/NEISO patterns are worked examples, never
   transfers): PJM — the model's entering position vs the published BRA/RPM cleared and
   requirement record (CETO/CETL where the crosswalk carries it); NYISO — vs the published
   ICAP/IRM/LCR record. Name each divergence's identified repair with its published source.
3. THE CURVE-ON ADJUDICATION (D6's object, now per-ISO): NYISO — adjudicate whether the
   published demand curve should be CONSULTED at default (the +123 % latent probe says what
   would happen; the adjudication decides whether that is faithful or a position artifact —
   after stage 2's reconciliation, not before); PJM — whether the curve-ON leg's over-fire
   (the original D6 signal) survives the corrected position. NOTHING ARMS in this lane:
   pre-stated conditions, suffixed registrations for any probe legs, and every arming
   recommendation returns to the owner.

RULE-14 SIGN DISCIPLINE, inherited from every predecessor: faithful positions/curves move
capacity revenue UP and retirements HARDER; nothing is sized by any residual, and a
worse-looking G3/FC-3 after accurate inputs is the expected signature, not a failure.

GUARDRAILS: rules 12 (years sequential per solve), 13, 22, 25, 27, 28 (any new
field/lever: matrix row + all shards, default-off, in the same PR). Solves priced before
launch, one ISO at a time. No keeper/shard/marker; backcast namespace untouched. STOP if
anything beyond the two ISOs' t1h keys + board blocks would move.

COLLISION: D44 flips the fossil-dates default — your solves record whichever posture is at
HEAD when each launches; state the vintage per leg in the finding (a fact, not a
conflict). Nobody else touches PJM/NYISO forecast surfaces this window.

EXIT: two registered diagnostics-on baselines + the two reconciliations + the two curve-ON
adjudications + docs/handoffs/FINDING-capx-d45-pjm-nyiso-curves-<date>.md with the per-ISO
position tables, each identified repair and its source, the arming recommendations, and
the explicit close-out line: this was the once-only clearing-half charter — successor work
is per-ISO repair lanes, and the mechanism-class question does not reopen without new
evidence.
```

## D46 — the post-repair-wave RE-MEASURE, staged (r#32; owner ruling Q32 on card C-3) — **STAGE 1 LANDED IN FULL at r#33** (PRs #4661/#4668; finding `FINDING-capx-d46-remeasure-2026-09-03.md`); **Stage 2 PENDING on D45's §9 close-out — re-released via D45-R (r#33), never by re-pasting this charter** (the re-dispatch of 2026-09-04 correctly refused to re-execute: re-running would overwrite the `-pre-d46` baselines); Stage 3 re-priced at r#33 (card C-6)

```
You are the D46 session of the capacity-expansion track — the BATCHED RE-MEASURE the director
queued at r#30/r#31 and the owner scoped at r#32 (ruling Q32: STAGED — the cheap set now, the
t1f tail later). It is a BASELINE REFRESH, not an A/B: every registered forecast bundle is stale
on up to three independent axes that were each measured on their own lanes already —
(i) Q30/D44: `fossil_announced_exits_enabled` flipped default-ON at `57088c33` (every ISO);
(ii) D41: the CCS fixed-cost constants re-identified (PJM/MISO CCS waves; GOLDEN-2's CCS leg);
(iii) keeper vintage: CAISO (231→239→240), MISO (198→200→201→202), NYISO (159→177).
You re-solve at HEAD, register preserve-then-overwrite, refresh the board, and REPORT every
gate-leg flip at full magnitude. You attribute nothing to an axis (no per-ISO controls — the
axes were measured on D42/D41/the backcast lanes) and you arm nothing.

DATA PROFILE: ercot, caiso, miso, neiso — hydrate incrementally, one ISO as its leg starts
(`python3 scripts/hydrate_data.py --profile <iso>`); widen to pjm/nyiso only in Stage 2.
MODEL ASSIGNMENT: Opus (ruled, pre-declared, mechanical execution; no adjudication).
BRANCH: claude/capx-d46-remeasure-batch — FRESH off origin/main, rebase before every push.

READ FIRST: capx ledger §0ac.7 (the priced inventory) + §0ac amendment 2 (the Q32 ruling) ·
docs/handoffs/FINDING-capx-d44-fossil-dates-arm-2026-09-03.md (what the flip changed, the
cache-key advance, the harness pin it repaired) · FINDING-capx-d41-* (the CCS constants) ·
FINDING-capx-d37-neiso-t1h-armed-2026-09-02.md and FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md
(the diagnostics-on live-posture hindcast pattern: pre-declared cache keys, run_config vintage
lines, preserve-then-overwrite) · FINDING-capx-t3-golden2-2026-09-01.md (the golden recipe:
`run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 --golden-posture
--full-solve-authorized`) · FINDING-capx-s6-pjm-ledger-2026-08-30.md (the t1f recipe:
`run_full_horizon.py --golden-posture`, then `forecast_verdict.py --tier t1f`, then
`register_forecast_run.py --summary … --kind t1f --label d46-remeasure`) ·
scripts/register_forecast_run.py::VERDICT_MAP (the run-id → bare-key map; you ADD rows, never
edit existing ones) · frontend/data/forecast/ff-verdicts.json (the committed verdict snapshot;
suffixed keys are PRESERVED BASELINES).

POSTURE RULE: each leg is the ISO's LIVE default posture at HEAD — read the last committed
bare-key bundle's run_config.json for the flag set (diagnostics on, `entry_screen_diagnostics`,
as D37/D45 did) and change NOTHING except what HEAD's defaults changed. Pre-declare each leg's
expected cache key and record the realized one; record `fossil_announced_exits_enabled=True`
and the keeper id per leg in the finding's vintage table. Rule 12: years sequential inside
every solve; at most two solves concurrent, never MISO/PJM alongside another heavy one.

STAGE 1 — EXECUTE NOW (≈8 h wall; this dispatch):
  a. T1-H hindcasts 2021–2025 (`run_capacity_hindcast.py --iso <ISO> --start-year 2021
     --end-year 2025 --out-dir results/hindcast/<iso>-2021-2025-realized-t1h-d46`), in this
     order: NEISO (~6 min) · CAISO (~20 min) · ERCOT (~15 min) · MISO (~25 min).
     Registration: MISO and NEISO OVERWRITE their bare keys (`miso-t1h`, `neiso-t1h`) with the
     prior bare record preserved VERBATIM at `miso-t1h-pre-d46` / `neiso-t1h-pre-d46` (the
     `-pre-d45` mechanism). ERCOT and CAISO have NO bare t1h key today (their hindcasts are
     registered under long ids only) — MINT `ercot-t1h` and `caiso-t1h` as new bare keys via
     VERDICT_MAP rows, pre-declared in the finding, and leave every existing long-id record
     untouched (the D43 pair stays the dispersion baseline; the ERCOT c1joint/d12c legs stay).
  b. GOLDEN-2 re-solve: NEISO 2026–2050 at HEAD, golden posture, full rubric scoring (FC-1..7,
     the FC-6 battery at its own vintage as GOLDEN-2 did), registered on `neiso-t3` with the
     prior record preserved at `neiso-t3-pre-d46` (~35 min, ~3.5 GB).
  c. T1-F full-horizon 2026–2050 for the three PAIRABLE non-D45 ISOs — NEISO (~1.0 h), ERCOT
     (~2.0 h), CAISO (~2.8 h) — `--golden-posture`, scored `forecast_verdict.py --tier t1f`,
     registered `--summary --kind t1f --label d46-remeasure` on `neiso-t1f` / `ercot-t1f` /
     `caiso-t1f`, priors preserved at `<key>-pre-d46`. Pair NEISO with ERCOT, then CAISO alone.
  d. Board refresh: re-derive the FC legs and gate (b)/(c) rows of the four ISOs from the new
     records ONLY where a record moved; assert byte-identity for every untouched row; never
     move gate (a). Run `scripts/check_gate_a_provenance.py` and
     `scripts/check_forecast_staleness.py` before the records commit.
  e. Matrix (rule 28): NO mechanism is tested here, so NO cell verdict moves — with ONE
     bounded exception: where an ISO's `-pre-d46` baseline differs from its new leg on the
     fossil-dates axis ALONE (same keeper, no CCS decision in either leg — verify from the
     evolution ledgers, never assume), you MAY stamp that ISO's `fossil_announced_exits_enabled`
     cell with its own measured verdict + citation (rule 25: own data). Otherwise the cell stays
     as D44 left it, with the evidence citation appended.

STAGE 2 — GATED, do NOT start until D45's §9 close-out line is on origin/main (its finding's
§4–§9 are placeholders at issuance; PJM/NYISO forecast surfaces are D45's until then):
  PJM t1h + NYISO t1h (bare keys, priors at `-pre-d46`; D45's own L1 becomes `pjm-t1h-pre-d46`)
  + NYISO t1f (~1.1 h). Same rules as Stage 1. If D45 has not closed when Stage 1 lands, STOP
  after Stage 1, commit the finding with Stage 2 marked PENDING, and end the session — the
  director re-releases Stage 2.

STAGE 3 — NOT THIS DISPATCH: PJM t1f (~7.3 h, solo ~10 GB) and MISO t1f (~10.1 h, solo) are
owner-scheduled separately (MISO's is the one D41 touches most). Do not start them.

PRE-DECLARATION (commit `docs/handoffs/PREDECL-capx-d46-remeasure-<date>.md` BEFORE the first
solve): per leg — the expected cache key, the keeper id, the posture line, and the DIRECTION
you expect each FC-3 retirement row to move under the dates flip (rule-14 sign discipline:
faithful inputs move exits toward recall and G3 may read WORSE — that is the expected
signature, not a regression; you never re-tune anything to a band). Grade it at full magnitude
in the finding, misses included.

GUARDRAILS: rules 12, 13, 22 (nothing outside 2021–2025 hindcast / 2026+ forecast; no backcast
namespace touch), 25, 27 (blob-verify every push touching a ≥300-line file; VERDICT_MAP lives
in a ≥300-line script — edit locally, push exact bytes), 28. No new ScenarioConfig field, no
parameter value, no keeper/shard/marker. If any solve fails or a key collides with an existing
suffixed record, STOP and route — never overwrite a preserved baseline.

COLLISION: D45 owns PJM/NYISO forecast surfaces (Stage 2 gate). The audit programme's stage-0
re-captures (X-2) touch results/regression-goldens/ — disjoint. The owner's backcast lanes
(caiso-24x, miso-20x, nyiso-18x) own the keeper shards — you read them, never write them.
Nobody else touches ERCOT/CAISO/MISO/NEISO forecast surfaces this window.

EXIT: Stage-1 keys re-registered with priors preserved, the board refreshed, the pre-declaration
graded, and docs/handoffs/FINDING-capx-d46-remeasure-<date>.md with: a per-key table (old key
→ preserved key, new record, cache key, keeper, posture), EVERY FC/gate-leg flip listed with
before/after values, the stale-set inventory of ledger §0ac.7 marked closed for Stage-1 keys
and PENDING for Stages 2/3, and one line per ISO on what the dates flip did to its exit rows.
```

## D47 — GOLDEN-3 attestation + the D46 records items (r#33; records-only) — **LANDED at r#34** (PRs #4691/#4699 + D47b; FC-7 restored; routed items → D51 rider / card C-8)

```
You are the D47 session of the capacity-expansion track — a RECORDS lane, zero solves, that
closes three items D46 routed to the director (FINDING-capx-d46-remeasure-2026-09-03.md §4.6,
§9 items 4, 6 and 7).

DATA PROFILE: code
MODEL ASSIGNMENT: Opus (mechanical, pre-declared; no adjudication).
BRANCH: claude/capx-d47-golden3-attestation — FRESH off origin/main, rebase before every push.

READ FIRST: the D46 finding §4.6 (why GOLDEN-3's FC-7 reads FAIL on the attestation row alone,
and why the lane deliberately did not author one post-hoc) · FINDING-capx-t3-golden2-2026-09-01.md
§3 (GOLDEN-2's own pre-declaration and its attestation — the template) · the committed GOLDEN-3
bundle results/ff-t3-neiso-golden/ (the golden3 campaign dir, its DOF ledger, FC-6 battery and
T1.6 ladder) · scripts/forecast_verdict.py (the FC-7 rows and what an attestation must carry) ·
frontend/data/forecast/ff-verdicts.json `neiso-t3` + `neiso-t3-pre-d46`.

THE WORK, in this order and no other:
1. PRE-DECLARE FIRST. Commit docs/handoffs/PREDECL-capx-d47-golden3-attestation-<date>.md
   stating, before writing the attestation: which FC-7 row moves (the attestation row only),
   which rows must stay byte-identical (every other FC-7 row and every FC-1..FC-6 category),
   that the determination stays HOLD, and that the attestation's content is READ from the
   committed bundle (run_config.json, DOF ledger, cache key, keeper id, posture) — nothing is
   authored that the bundle does not already carry. Push it before step 2.
2. Author forecast_attestation.json for the GOLDEN-3 bundle from those committed inputs.
   Re-score `neiso-t3` artifact-only (no solve); register preserve-then-overwrite with the
   pre-attestation record kept at `neiso-t3-pre-d47`. Assert byte-identity of every category
   except FC-7's attestation row, and state the HOLD unchanged.
3. THE `-pre-d46` LIKE-FOR-LIKE TABLE (D46 §9 item 7): a short table in the finding — for each
   `-pre-d46` key, its vintage (cache epoch / HEAD), which of the three axes its delta spans,
   and whether a delta against it is attributable (NEISO t1h: one axis; GOLDEN-3: exactly the
   three axes; ERCOT/CAISO t1f: FFR-3A-2 vintage plus a month of HEAD — NOT attributable).
   Records only; it becomes the citation any later reading of a `-pre-d46` delta must carry.
4. THE `neiso-t1h` POSTURE DISCLOSURE (D46 §9 item 4): the bare `neiso-t1h` carries D37's
   Q28-armed Net ICR posture while the shipped default is OFF (the P9 flip failed). Director
   ruling r#33: a bare key carries the SHIPPED posture. You do NOT re-solve here — the
   default-posture NEISO leg rides the D45-R batch. You add a dated note to the board's NEISO
   FC-3 row and the finding stating the discrepancy, its origin (D37 registered the armed leg
   bare with the control suffixed), and that D45-R replaces it.
5. THE BOARD'S t1f COST FIELDS (r#33 amendment 3): D46 §2 measured the t1f legs at 8–23 min
   against `c_cost` fields of 1.0–2.8 h. Correct `isos.<ISO>.gate.c_cost.detail` for ERCOT,
   NEISO and CAISO to the MEASURED values (with the D46 citation and the container's ~55 min
   data/clean regeneration named separately); mark PJM/MISO/NYISO's fields "unmeasured at the
   t1f grain — D46 factor 7–10× suggests ~45–90 min" rather than rewriting them to a guess.
   Records only; no verdict, no gate status, no stamp moves.

GUARDRAILS: zero solves; no ScenarioConfig field, parameter, keeper, shard, marker or matrix
verdict; gate (a) never moved; rule 27 on every ≥300-line file (VERDICT_MAP's script,
program-status.json); rule 22 untouched. If the re-score moves ANY row other than the
attestation row, STOP — do not register — and route to the director.

COLLISION: D45-R owns PJM/NYISO forecast surfaces and the NEISO default-posture leg; the
audit programme's stage-0 re-captures own results/regression-goldens/. You touch only the
GOLDEN-3 bundle's attestation, `neiso-t3`'s registration, and the two records items.

EXIT: PREDECL + attestation + re-scored `neiso-t3` (prior at `-pre-d47`) + a short
docs/handoffs/FINDING-capx-d47-golden3-attestation-<date>.md carrying the byte-identity
assertion, the like-for-like table and the posture disclosure.
```

## D45-R — the D45 close-out + D46 Stages 2 and 3 (r#33; owner rulings Q33 + Q35) — **LANDED COMPLETE at r#34** (PRs #4690/#4697/#4708; the once-only question RETIRED; **leg 7 pre-declared but NOT RUN — card C-7**; leg 8 STOP-routed, CAISO keys unchanged)

*Keeper vintage at issuance (read the shards, never this note): NYISO `2026-09-04-nyiso-185-family-hr` (promoted after §0ad was written — ledger §0ad amendment 2), PJM `2026-08-15-pjm-162-inputclock`, MISO `2026-09-03-miso-202-unitclip`, NEISO `2026-08-17-neiso-99-joint-p1`. Name the keeper id per leg in the finding's vintage table.*

```
You are the D45-R session of the capacity-expansion track. D45 (the once-only PJM + NYISO
clearing-half + curve-ON charter) landed its PJM half and died before its NYISO half: on
origin/main, docs/handoffs/FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §4, §5, §6, §7,
§8 and §9 are literal `[filled …]` placeholders, and no NYISO L2/L3 or PJM L4 bundle exists.
The owner ruled it dead (Q33) and folded D46's Stages 2 and 3 into this lane (Q35). You
finish D45 AT HEAD — the post-D44 posture supersedes D45's pre-D44 L1 anyway — and you close
the program's forecast stale set in the same dispatch.

DATA PROFILE: pjm, nyiso, miso, neiso — hydrate incrementally as each leg starts
(`python3 scripts/hydrate_data.py --profile <iso>`).
MODEL ASSIGNMENT: Fable (the once-only mechanism-class adjudication; arming recommendations).
BRANCH: claude/capx-d45r-pjm-nyiso-close — FRESH off origin/main, rebase before every push.

READ FIRST: pack §D45 (the original charter — its READ FIRST list, stages, rule-14 sign
discipline and guardrails ALL still bind; this section only says what is different) · the D45
finding as it stands (§0–§3 are DONE and stand; you fill §4–§9 IN PLACE, never rewrite §0–§3;
where a HEAD result changes a §0–§3 reading you append a dated correction, you do not edit
history) · docs/handoffs/PREDECL-capx-d45-pjm-nyiso-curves-2026-09-03.md (its cache keys are
pre-D44 and WILL NOT match at HEAD — your own PREDECL re-declares every key) ·
FINDING-capx-d46-remeasure-2026-09-03.md §1 (t1f is a 2026–2030 five-year tier, NOT 2026–2050;
the run-id/label mechanics; the VERDICT_MAP re-pointing precedent; the -pre-<lane> preservation
pattern) and §2 (measured wall times: t1f legs ran 8–23 min, the board's estimates were
7–10× high) · FINDING-capx-d44-fossil-dates-arm-2026-09-03.md (the posture every leg now
carries) · scripts/register_forecast_run.py::VERDICT_MAP.

PRE-DECLARATION FIRST (docs/handoffs/PREDECL-capx-d45r-<date>.md, pushed before the first
solve): every leg's expected cache key, keeper id, posture line
(`fossil_announced_exits_enabled=True`), and — for the D45 legs — the SAME pre-stated flip
conditions D45's PREDECL carried for L3/L4, re-affirmed or explicitly amended with reason.

THE LEGS, in this order (rule 12: years sequential; at most two concurrent; PJM and MISO solo):
  1. PJM L1 REPLAY at HEAD (live posture, diagnostics-on) → registered as the bare `pjm-t1h`;
     D45's pre-D44 L1 preserved at `pjm-t1h-pre-d45r`. ~16 min.
  2. NYISO L2 — live, curve-OFF (flat $110), diagnostics-on → the bare `nyiso-t1h`; prior
     preserved at `nyiso-t1h-pre-d45r`. This is D46 Stage 2's NYISO leg, satisfied here.
  3. NYISO L3 — L2 + `--capacity-market-clearing` (the D28 latent curve-ON probe) → suffixed
     `nyiso-t1h-d45r-curveon`. NEVER the bare key.
  4. PJM L4 — L1 + `--fixed-net-cone` (the FFR-2E comparison arm) → suffixed
     `pjm-t1h-d45r-fixed`.
  5. NEISO default-posture T1-H (the Net ICR lever OFF, as shipped) → the bare `neiso-t1h`;
     D46's armed-posture record preserved at `neiso-t1h-pre-d45r` (director ruling r#33: a bare
     key carries the SHIPPED posture; D37's armed leg keeps its own suffixed key). ~7 min.
  6. T1-F 2026–2030, `--golden-posture`, `forecast_verdict.py --tier t1f`, registered
     `--summary --kind t1f --label d45r-remeasure`: NYISO (paired with leg 5), then PJM solo,
     then MISO solo — the bare `nyiso-t1f` / `pjm-t1f` / `miso-t1f`, priors at `-pre-d45r`.
     STOP RULE: if PJM's or MISO's t1f exceeds 2 h wall, kill it, record the measured time, and
     leave that key stale with a dated note — the owner priced them at ~45–90 min on D46's
     measured factor and a 2 h overrun is a finding, not a licence.
  7. NEISO DATES-OFF PAIRED CONTROL (r#33 amendment 3): leg 5's recipe with
     `fossil_announced_exits_enabled=False` set EXPLICITLY (cache-neutral by b′-1, D44 §1) →
     suffixed `neiso-t1h-d45r-datesoff`, NEVER the bare key. ~7 min. Pre-declare the expected
     direction: if the flip alone carries NEISO's recall 4/6 → 3/6 and false_retire 0.263 →
     0.315, say so at full magnitude — that is a rule-25 counter-example to Q30's default and
     it returns to the owner as a finding, not a recommendation. Nothing arms or disarms here.
  8. CONDITIONAL CAISO LEGS: read frontend/data/backcast/keepers/CAISO.json at launch. If the
     keeper is no longer `2026-09-03-caiso-241-b1-ctpeaker` (caiso-243 was mid-solve at
     issuance), include `caiso-t1h` (~10 min) and `caiso-t1f` (~23 min) on the same rules,
     priors at `-pre-d45r`. If it is unchanged, skip both and say so.
  VERDICT_MAP: add rows for every new run id; the three D45 rows that point at bundles that
  never existed (`nyiso-2021-2025-realized-t1h-d45`, `…-d45-curveon`,
  `pjm-2021-2025-realized-t1h-d45-fixed`) are RE-POINTED to this lane's run ids (the D46
  precedent), disclosed in the finding. Zero duplicate keys, verified by AST.

THEN THE D45 CHARTER'S STAGES 2 AND 3 FOR NYISO, exactly as pack §D45 wrote them: the position
+ evaluation-quantity reconciliation against the published ICAP/IRM/LCR record (rule 25, own
parameters, published sources cited), and the curve-ON adjudication — after the reconciliation,
never before. Fill §4 (L4), §5 (L2/L3 + the NYISO stages), §6 (the two arming recommendations
on their pre-stated conditions — NOTHING ARMS; every recommendation returns to the owner),
§7 (both pre-declarations graded at full magnitude, D45's original and yours), §8 (sources,
sha256, governance attestation) and §9 — THE CLOSE-OUT LINE: this was the once-only
clearing-half charter; successor work is per-ISO repair lanes, and the mechanism-class question
does not reopen without new evidence. The director re-releases nothing behind §9.

BOARD + MATRIX: refresh the FC legs and gate (b)/(c) rows of PJM/NYISO/MISO/NEISO only where a
record moved; assert byte-identity elsewhere; never move gate (a) (run
scripts/check_gate_a_provenance.py before the records commit — if it fails, STOP and route,
the director holds the standing re-key duty). Rule 28: no mechanism is armed, so no verdict
letter moves; PJM and NYISO may receive their own measured `fossil_announced_exits_enabled`
evidence exactly as D46 §6 stamped the other four.

GUARDRAILS: rules 12, 13, 14 (sign discipline: faithful positions/curves move capacity revenue
UP and retirements HARDER; nothing sized by a residual), 22, 25, 27 (blob-verify every push
touching a ≥300-line file), 28. No new ScenarioConfig field, no parameter value, no
keeper/shard/marker; backcast namespace untouched. Never overwrite a preserved baseline; on any
key collision STOP and route.

COLLISION: D47 (records-only) touches the GOLDEN-3 attestation and `neiso-t3` — disjoint from
every key here. The owner's backcast lanes own the keeper shards (CAISO is promoting again;
`caiso-t1h/t1f` are deliberately NOT in this lane). The audit programme's stage-0 re-captures
own results/regression-goldens/. Nobody else touches PJM/NYISO/MISO/NEISO forecast surfaces
this window.

EXIT: six bare keys current at HEAD (`pjm-t1h`, `nyiso-t1h`, `neiso-t1h`, `nyiso-t1f`,
`pjm-t1f`, `miso-t1f`) with priors preserved (plus CAISO's two if leg 8 fired), three
suffixed probe/control legs registered (L3, L4, the NEISO dates-OFF control), the D45
finding complete through §9 with its close-out line, both pre-declarations graded, the board
refreshed, and the ledger §0ac.7 stale set marked CLOSED for every key except CAISO's.
```

## D48 — the PJM accreditation-design devintage (r#33 amendment 3; D45 §2.3 items 1–2) — **PHASE 0 LANDED (PR #4707); PHASE 1 LANDED (PRs #4716/#4718, graded r#36 — one sitting late)**: accounting to the MW, FC-3 +1.4 GW via the admission cap, **DO NOT ARM alone — arm WITH the clearing half (§D57)**; its PREDECL corrects this charter's '2–4 points' premise to 7–11 on a consistent basis

```
You are the D48 session of the capacity-expansion track — the PJM per-ISO repair lane D45's
PJM half identified WITH PUBLISHED SOURCES and ZERO FREE PARAMETERS, and which its §9
close-out (being written by D45-R) names as successor work. D45 §2.2 established that PJM's
"$0 capacity revenue where the model sits" is a BASIS artifact: HEAD accredits PJM's
2021–2024 fleet on the 2025/26 ELCC-class design against a mixed-vintage composite
requirement, where the auctions those years actually cleared on the pre-CIFP UCAP design
against a published UCAP requirement. Restated on the auction's own basis the same fleet
sits 2–4 points past the zero-cross, not 10.

DATA PROFILE: pjm
MODEL ASSIGNMENT: Fable (a mechanism with arming consequences; rule-14 sign adjudication).
BRANCH: claude/capx-d48-pjm-accreditation-devintage — FRESH off origin/main, rebase before
every push.

READ FIRST: docs/handoffs/FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §2.1–§2.3 IN FULL
(the reconciliation, the two repairs, their sources: PJM Manual 18, the per-DY Planning Period
Parameters workbooks committed in-repo, the 2025/26 CIFP ELCC filing ER24-99, BRA Tables 3A/6)
· docs/handoffs/d45/published-positions-2026-09-03.{py,json} and
positions-from-ledgers-2026-09-03.{py,json} (the instruments — reuse, do not rebuild) ·
`THERMAL_ACCREDITATION_BASIS_BY_ISO` and `resolve_forecast_pool_requirement` in
src/market_sim (the two seams named) · the D40 finding (the NEISO requirement-devintage
precedent: default-off field, LOYO, P9-style pre-stated flip condition) · the D42/D44
findings (the vintage-gate construction — a published value is admissible in year Y only
because it was on file at the run's information cutoff) · docs/parameter-citations.md ·
docs/mechanism-testing-matrix.md §5 PJM lever queue + the PJM shard.

THE WORK, two phases, the second GATED:
PHASE 0 — BUILD + PRE-DECLARE (now):
  a. ONE gated field, default OFF, name it for the family (`pjm_accreditation_design_vintage`
     or the repo's convention), that (i) accredits thermal at UCAP = 1 − EFORd for delivery
     years ≤ 2024/25 and at the ELCC-class ratings from 2025/26, and (ii) resolves the pool
     requirement from the PUBLISHED FPR per DY (1.0898 / 1.0868 / 1.0901 / 1.0894 pre-CIFP;
     post-CIFP from 2025/26) — exactly as the published design switched, vintage-gated. Every
     value cited at the definition (rule 5), zero free parameters (rule 21), registered in
     ScenarioConfig + run_config (rule 24), matrix base row + a cell in EVERY shard in the
     same PR (rule 28c), byte-inert while off (prove it: a HEAD replay of `pjm-t1h`'s recipe
     with the field explicitly False must key identically).
  b. DR AS COUNTED SUPPLY (§2.3 item 2): the published BRA offered/cleared DR UCAP per DY as
     supply rather than a peak netting — the ONE repair that moves the position AWAY from the
     curve (+~3 points). Build it as a second gated field or a documented limb of the first;
     either way it is formulaic and published, never sized by a residual.
  c. PRE-DECLARE docs/handoffs/PREDECL-capx-d48-<date>.md BEFORE any solve: the expected
     entering positions per screen year on the corrected basis (D45 §2.2's restated numbers
     are the prediction — 1.077 / 1.077 / 1.095, 2–4 points past the zero-cross), the expected
     capacity-revenue direction (UP), the expected exit direction (HARDER; G3 may read WORSE —
     rule 14's signature, not a failure), the FC-3 rows you expect to move and which way, a
     P9-style flip condition for any arming recommendation, and the cache key of the A/B arm.
     Push it. Then STOP if D45-R's PJM legs (`pjm-t1h` at HEAD, `pjm-t1h-d45r-fixed`) are not
     yet on origin/main — the A/B's control IS D45-R's bare `pjm-t1h`, and solving before it
     lands would collide on the key and double-solve the control.
PHASE 1 — THE A/B (gated on D45-R's PJM legs landing; verify on origin/main, never assume):
  d. ONE arm: D45-R's `pjm-t1h` recipe + the field(s) ON, diagnostics-on → suffixed
     `pjm-t1h-d48-devintage`. NEVER the bare key. Score like-for-like against `pjm-t1h`; LOYO
     within 2021–2025 per rule 22. Grade the pre-declaration at full magnitude.
  e. Write docs/handoffs/FINDING-capx-d48-<date>.md: the position table on both bases, the
     capacity-revenue and exit deltas, every FC row that moved, the D45 §2.3 item 3 (the
     clearing half — clear the VRR curve against the net-ACR offer stack) explicitly NOT
     built here and routed, and the arming recommendation on its pre-stated condition.
     NOTHING ARMS — the recommendation returns to the owner.

GUARDRAILS: rules 5, 12 (PJM solves solo, ~8 GB), 13 (a published auction parameter is a
market-design input; an auction OUTCOME — cleared MW, price — is a validation observable,
never a target), 14, 21, 22, 24, 25 (PJM's own values from PJM's own publications; nothing
transfers from NEISO/MISO beyond the construction pattern), 27, 28. No keeper/shard/marker;
backcast namespace untouched.

COLLISION: D45-R owns `pjm-t1h` and the PJM forecast surface until its PJM legs land — that is
the Phase-1 gate. D49 reads PJM/MISO/ERCOT ledgers only (zero-solve). Nobody else touches PJM
forecast surfaces this window.

EXIT: Phase 0 landed (field(s) default-off, matrix row + cells, PREDECL pushed, byte-inertness
proven) and, once gated, the A/B arm registered suffixed, the finding with the arming
recommendation, and the lever's cell stamped in the PJM shard.
```

## D49 — two zero-solve Phase-0s on the D46 ledgers: ERCOT's CCS at carbon = 0, and the MISO exit-side margin (r#33 amendment 3; D46 routed items 2 and 3) — **LANDED at r#34** (PRs #4700/#4706; both halves are construction defects with named repairs → §D50, §D51)

```
You are the D49 session of the capacity-expansion track — a zero-solve diagnostic lane over
artifacts D46 committed. Two objects, two halves, one finding. You solve nothing, arm
nothing, and touch no ScenarioConfig field; every number is read from committed ledgers
and dumps with a probe script you commit.

DATA PROFILE: code (widen to ercot / miso only if a probe needs a clean-data input; say so)
MODEL ASSIGNMENT: Fable (the second half is a mechanism-class adjudication).
BRANCH: claude/capx-d49-d46-phase0s — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d46-remeasure-2026-09-03.md §4.5 (the ERCOT CCS rows),
§4.2 and §9 items 1–3 · FINDING-capx-d41-* (the corrected constants 900 → 1521.4 $/kW capex,
25 → 65 $/kW-yr FOM, and D41 §4.3's PJM/MISO zero-clearing construction — REUSE its arithmetic)
· FINDING-capx-d43-caiso-dispersion-2026-09-02.md (the dispersion-expectation construction at
the screen grain — the SAME construction is what half 2 mirrors onto exits) · D31/D32/D42
findings (the MISO exit residual's history: −74 % under on faithful inputs, floor-retention
random selection, the dates channel covering 16/19) · model-methodology-spec.md §5.2 (the
retirement screen: attainable margin Σ max(0, price − variable cost, reserve price) × pmax ×
availability vs FOM-only going-forward cost, the per-fuel lags, the floor) and §5.6 (the CCS
retrofit screen: incremental uplift over the best unabated state, 45Q window) · the committed
bundles: results/hindcast/miso-2021-2025-realized-t1h-d46/MISO/<key>/ (evolution_<yr>.json +
screen_signal_diag_<yr>_for_<yr+1>.npz) and the ERCOT t1f bundle registered as
`ercot-2026-2030-d46-remeasure` (its evolution ledgers with `ccs_retrofits`).

PRE-REGISTER FIRST (docs/handoffs/PREDECL-capx-d49-<date>.md, pushed before either probe
runs): for half 1, the candidate explanations ranked with a decision rule each (e.g. (a) ERCOT
host CCs carry higher energy margins so the 45Q-window uplift clears the corrected bar on
economics; (b) an ERCOT-specific screen path — a carbon or EAC term that is non-zero at ERCOT
though carbon is 0, or a cap/eligibility difference; (c) a construction defect — the uplift
compared against the wrong unabated state); for half 2, the two hypotheses with a numeric
discriminator fixed in advance (H-WALL: the undated cohort's screen margins cluster within a
band of the bar narrower than the dispersion D43 measured, so priced dispersion would push a
tail below it; H-BAR: the cohort sits far above the bar and the miss is the bar or the
capacity-revenue term).

HALF 1 — ERCOT CCS AT CARBON = 0. From the committed ERCOT t1f ledgers, reconstruct per
converting unit the screen's own uplift arithmetic on the corrected constants and identify
which term clears the bar. Run the identical reconstruction on PJM's and MISO's committed
ledgers (D41 §4.3's own cases) so the three ISOs are compared like-for-like. State whether
the ERCOT result is (a) economics, (b) an ERCOT-specific path, or (c) a defect; if (c), name
the seam and STOP — a defect is routed to the director as a candidate repair lane, never
fixed here. Physical-plausibility line, stated either way: no merchant gas-CC CCS retrofit has
cleared on 45Q alone in any US market to date; a model that clears 2.7 GW of them by 2029
without a carbon price owes an explanation, not a band.

HALF 2 — THE MISO EXIT-SIDE MARGIN. From evolution_<yr>.json + the screen_signal_diag dumps,
for every UNDATED fossil unit the screen evaluated in each window year: its attainable margin,
its bar (FOM going-forward cost with the per-fuel lag), the gap, its capacity-revenue term at
the repaired RBDC position, and whether it exited. Then apply the D43 construction: with the
LP's own realized price dispersion discarded, what fraction of the cohort sits within the
dispersion band of its bar (H-WALL) versus well above it (H-BAR)? Report the decomposition at
full magnitude against the actual exits (the published retirement record D42 used) — how much
of the −43.6 % `retire.total_gw` miss each hypothesis can account for. Rule-14 sign line: a
faithful margin moves exits HARDER; nothing here is sized by the residual.

EXIT: docs/handoffs/FINDING-capx-d49-<date>.md with both pre-registrations graded at full
magnitude, the per-unit tables, the two verdicts, and the routing — for half 1 a named seam or
a closed question; for half 2 either "the exit under-build is the D43 wall mirrored" (routed to
the wall's record, no lane) or a named margin-side object with its identified repair and
source. Matrix (rule 28): no mechanism tested, no verdict letter moves; append evidence
citations to the ERCOT `ccs` cells and the MISO retirement cells only. GUARDRAILS: zero solves;
rules 13, 14, 21, 22, 25, 27. COLLISION: none — read-only over committed artifacts; D45-R /
D48 own the live forecast surfaces.
```

## D50 — CCS capex scaled to captured CO2: the D49 half-1 seam repair (r#34) — **CHECKPOINT at r#36** (PR #4728: field built default-off, ERCOT arm 0 conversions vs 2,741.8 MW, NEISO cap still binds; **OWED: the PJM arm, the blast radius, the recommendation and the finding the shards cite** → §D50-R; never re-paste this charter)

```
You are the D50 session of the capacity-expansion track. D49 half 1 (FINDING-capx-d49-2026-09-04.md
§1) established, zero-solve and like-for-like across ERCOT / PJM / MISO, that the CCS retrofit
screen clears merchant gas-CC retrofits at carbon = 0 because of a CONSTRUCTION SEAM, not
economics: the §45Q credit scales with the host's measured CO2 flow per MWh while
`ccs_retrofit_capex_kw` is the ATB capture-island increment for an H-class reference host
charged FLAT per kW — so a host emitting 40–90 % more CO2 per kW is credited for all of it and
charged to capture none of the excess. D41 §4.3's zero-clearing result never held at unit grain.
You repair the seam, measure its blast radius, and return the arming question to the owner.

DATA PROFILE: ercot, neiso, pjm (incremental).
MODEL ASSIGNMENT: Fable (mechanism design with a default-flip consequence).
BRANCH: claude/capx-d50-ccs-capex-scaling — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d49-2026-09-04.md §1 IN FULL (§1.2 the 14 reconstructed rows, §1.3 the
PJM/MISO like-for-like, §1.4 what the term is, §1.5 the three seams — you build THOSE, not a
redesign) · FINDING-capx-d41-* (the ATB basis, dollar-year, the D41 §6.2 blast-radius precedent:
a CCS constant change re-keys every forecast config) · FINDING-capx-d44-* §1 (the b′-1
declared-default-flip mechanics) · model-methodology-spec.md §5.6 · src/market_sim/.../ccs.py
::apply_ccs_retrofit · NEW_ENTRY_COSTS["gas_cc"] (the ATB reference host heat rate) ·
docs/parameter-citations.md · the matrix CCS rows and every ISO shard's `ccs` cells.

THE WORK:
1. PRE-REGISTER (docs/handoffs/PREDECL-capx-d50-<date>.md, pushed before any code): per ISO
   (ERCOT, NEISO, PJM), the expected conversion count and MW under the repair versus the
   committed t1f/golden ledgers, derived from D49 §1.2/§1.3's own reconstruction with the
   capex scaled — no new arithmetic; the expected cache keys; the expected direction of every
   FC-1/FC-2 row the CCS wave touches; a STOP if the repaired screen clears MORE MW anywhere.
   D49 §5 item 2 is an input: at unit grain 5.0–5.7 GW of PJM/MISO gas_cc clears at the ceiling
   in 2028 cap-bound; state what the repair does to that.
2. BUILD, default-off, zero DOF: (a) `retrofit_capex_per_mw = capex_kw × 1000 ×
   (captured_t_per_mwh / captured_ref)` with `captured_ref` = 0.9 × the ATB gas_cc reference
   host's rate (NEW_ENTRY_COSTS heat rate × 0.057) — the basis D41's increment already
   carries, cited at the definition; (b) CHP hosts (`CC_CHP`) EXCLUDED from the retrofit
   candidate set, or rated on electric-only fuel — pick ONE on the published basis and cite
   it; (c) the p55470 row (hr 34.75) flagged in the ERCOT curated sheet's README as a
   data-quality item, not silently filtered. One gated field (or the repo's convention for a
   construction repair), registered in ScenarioConfig + run_config (rule 24), matrix base row +
   a cell in EVERY shard (rule 28c), byte-inert while off (prove it on `ercot-t1f`'s recipe).
3. A/B, t1f 2026–2030, `--golden-posture`: ERCOT (~12 min) and NEISO (~8 min) paired, then
   PJM solo (~28 min measured by D45-R). Each arm suffixed `<iso>-t1f-d50-ccscapex`; NEVER the
   bare keys. Score `forecast_verdict.py --tier t1f`; grade the pre-registration at full
   magnitude. MISO t1f (~65 min) only if PJM's result contradicts the pre-registration.
4. BLAST RADIUS, measured: list every committed forecast/hindcast key whose cache key the
   default flip would advance (the D41 §6.2 / D44 pattern) and the solve-minutes to
   re-measure them at the D45-R measured rates — that number goes on the owner's card.
5. FINDING docs/handoffs/FINDING-capx-d50-<date>.md: the per-ISO conversion tables before /
   after, the FC rows moved, the blast radius, and the ARMING RECOMMENDATION on the
   pre-stated condition. NOTHING ARMS in this lane — the default flip is an owner ruling.

GUARDRAILS: rules 5, 12, 13, 14 (a faithful capex makes retrofits HARDER — fewer conversions is
the expected signature), 21, 22, 24, 25, 27, 28. No keeper/shard/marker; backcast untouched.

COLLISION: D48 (PJM hindcast surfaces, `pjm-t1h`) — you touch only suffixed t1f keys; D51
(MISO) and D52 (NYISO) are disjoint. Nobody else touches the CCS screen or the ERCOT/NEISO/PJM
t1f surfaces this window.

EXIT: the repair default-off with matrix duties, three suffixed A/B legs registered, the
pre-registration graded, the blast radius priced, the finding with the arming recommendation.
```

## D51 — the MISO adequacy-accounting ratio re-identified on the dates-ON fleet (r#34; D49 half 2) — **LANDED at r#36** (PR #4729: 0.8546 → 0.8934, the 2024 double-netting closed to 1.5 pts; limb (c) fails by the letter → card C-11; NEISO leg 7: Q30 has no NEISO-side counter-example)

*r#34 amendment 1 (owner rulings Q36/Q37, same sitting): rider (d) is UNCONDITIONAL — leg 7 runs; rider (e) added — the rubric §5 amendment. The charter text below carries both.*

```
You are the D51 session of the capacity-expansion track. D49 half 2 (FINDING-capx-d49-2026-09-04.md
§2, esp. §2.6) established that MISO's exit under-build is NOT the D43 dispersion wall: the
undated cohort is floor-capped in 2022–23 and capacity-cliff-cleared in 2024–25, and the
margin-side object is the reserve POSITION the screens consume, which is netted TWICE — D31's
`ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"] = 0.8546` was identified as PRA offered
÷ the model's census internal supply on a fleet that still carried the 2021–2023 real exits, and
since Q30/D44 the fossil-dates channel removes those same plants explicitly while the ratio
still applies. The consumed position falls 5.8 / 6.9 pts SHORT of the market's own, and the
vertical 2024 vintage pays a $123/kW-yr cliff to 98 GW. You re-identify the ratio on the
fleet in the SAME posture the run applies, A/B it, and report.

DATA PROFILE: miso (+ neiso only if the C-7 rider below is live).
MODEL ASSIGNMENT: Opus (a rule-23 re-derivation with a pre-declared A/B; no design).
BRANCH: claude/capx-d51-miso-accounting-ratio — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d49-2026-09-04.md §2 IN FULL · FINDING-capx-d31-* §2 (the ratio's
identification arithmetic — you move ONE term, nothing else) and §4 (the vertical-era floor
adjudication) · FINDING-capx-d42/d44 (which plants the dates channel removes, by vintage) ·
data/raw/miso-pra/ (the PRA offered record, the two overlap years) · the committed
`miso-2021-2025-realized-t1h-d45r`… no: the bare `miso-t1h` at HEAD is D46's
`miso-2021-2025-realized-t1h-d46` — read scripts/register_forecast_run.py::VERDICT_MAP for the
live mapping and use THAT bundle's evolution ledgers as the control · FINDING-capx-d32-* (the
floor-retention objects the repair hands the cohort back to).

THE WORK:
1. PRE-REGISTER (docs/handoffs/PREDECL-capx-d51-<date>.md, pushed before the re-derivation):
   the re-identified ratio's expected range (D49's back-of-envelope ~0.88 / 0.91 — state it as
   the prior, never as the target), the expected 2023 / 2024 / 2025 positions (near 1.03 in
   2024), the expected capacity term per year (2024 → $0; 2025 ≈ $91–110/kW-yr against the
   market's $79), the FC-3 rows expected to move and their DIRECTION (exits HARDER in 2025;
   the cohort back to the floor-capped regime in 2024 — `retire.total_gw` may read WORSE, the
   rule-14 signature), the A/B cache key, and a STOP if the ratio leaves [0.80, 0.95].
2. RE-DERIVE (rule 23, citing the data/posture change: D44 flipped the fleet the ratio was
   identified on): PRA offered ÷ model accredited internal supply NET of the dated exits, on
   the same two overlap years, from the same PRA record, with the derive script's commit
   citing this finding and D49 §2.6. Zero free parameters: the ratio is an accounting identity,
   never sized by the exit residual. Ship it as a new registry value behind the SAME gated
   field pattern D31 used (default-off until the owner rules), matrix cell updated.
3. A/B: the bare `miso-t1h` recipe + the re-identified ratio ON, diagnostics-on → suffixed
   `miso-t1h-d51-ratio` (~25 min, solo). Score like-for-like; LOYO within 2021–2025; grade
   the pre-registration at full magnitude.
4. RECORDS RIDER (zero solves): (a) mark `ercot-t1f-pre-d46` and `caiso-t1f-pre-d46` as
   provenance-only stubs no delta may be read against (D47 §6 item 2), in ff-verdicts'
   notes and the board; (b) repoint the board's NEISO `golden` field to GOLDEN-3 (D47 §6
   item 4), preserving the GOLDEN-2 text beneath; (c) record D49 §5 item 5 — oil is not
   screened after 2022 (3.5 GW stays in `fleet_by_fuel_before`) — in the MISO matrix shard's
   retirement cell evidence so no successor reads "oil passes" as a margin fact.
   (d) RUN D45-R's leg 7 EXACTLY as its PREDECL §4.2 declared (owner ruling Q36) —
   `neiso-2021-2025-realized-t1h-d45r-datesoff` (L5's recipe + `--no-fossil-announced-exits`,
   pre-declared key `5925e67c572a910f`), registered suffixed `neiso-t1h-d45r-datesoff`, graded
   against P16/P17 at full magnitude in your finding. ~7 min; hydrate `neiso` for it. If the
   realized key differs from the pre-declared one, register it anyway, state the drift, and
   grade against P16/P17 as written. This decides whether Q30's default has a NEISO-side
   counter-example: report the answer as a finding to the owner, never as a recommendation.
   (e) RUBRIC §5 AMENDMENT (owner ruling Q37): add to the forecast rubric's attestation clause
   the second limb — "a follow-up lane may author a forecast attestation iff it is PRE-DECLARED
   before authoring, moves only the attestation row, and re-scores artifact-only" — citing
   FINDING-capx-d47-golden3-attestation-2026-09-04.md §1 as the model case and capx ledger §3
   Q37 as the signature; bump the rubric version per its own convention and note it in the
   CHANGELOG. Text only; no verdict, no re-score.
5. FINDING docs/handoffs/FINDING-capx-d51-<date>.md: the ratio's derivation table, the
   position/capacity-term/exit deltas, every FC row moved, the rider items, and the arming
   recommendation on the pre-stated condition. NOTHING ARMS — the default is the owner's.

GUARDRAILS: rules 12 (MISO solo, ~10 GB), 13, 14, 21, 22, 23, 24, 25, 27, 28. No keeper/shard/
marker; backcast untouched. Never overwrite a preserved baseline.

COLLISION: D50 (ERCOT/NEISO/PJM t1f suffixed keys) and D52 (NYISO) are disjoint; D48 owns PJM.
The owner's MISO backcast lanes (miso-210) own the keeper shard — read only.

EXIT: the re-identified ratio shipped default-off with citation, the A/B registered suffixed,
the pre-registration graded, the records rider done, the finding with the recommendation.
```

## D52 — the NYISO adequacy devintage: requirement on the published forecast peak + per-year adopted IRM (r#34; D45 §5.2.4 items 1–2) — **LANDED at r#36** (PR #4730: positions +9.4/+5.2/+7.3 → −2.6/−1.8/−0.6 pts, LOYO 3/3, FC-3 byte-identical at the default; curve-ON probe P9 1-of-3 → curve stays OFF; recommends ARM BOTH gates → card C-12; the locality half → §D59)

```
You are the D52 session of the capacity-expansion track — NYISO's per-ISO repair lane, the
successor D45's §9 close-out names. D45 §5.2 (filled by D45-R) established on published data
that the model's NYCA SUPPLY is the market's within 0.6 GW in every scored year, but its
REQUIREMENT is 1.9–2.2 GW low in 2021–2024 because the hindcast sets it on the model's
realized weather-year peak where NYSRC sets it on the ICAP-market FORECAST peak, plus a single
2025-26 vintage IRM/derate factor where the adopted values were 20.0 / 22.0 / 24.4 %. That
position error is why the latent curve-ON probe fired at +189 % (§5.3) and why the pre-stated
arming conditions read 0 of 3. You build the two zero-DOF repairs, A/B them, and re-run the
curve-ON probe ONLY if the position lands inside the ±3-point condition §6 fixed.

DATA PROFILE: nyiso
MODEL ASSIGNMENT: Fable (a mechanism whose result re-opens or keeps closed an arming question).
BRANCH: claude/capx-d52-nyiso-adequacy-devintage — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §5 IN FULL (§5.2.1–§5.2.4 the
reconciliation and the four identified repairs with sources; §5.3 the probe; §6 the
recommendation and the re-open condition) · docs/handoffs/d45/nyiso-reconciliation-2026-09-04.{py,json}
and published-positions-2026-09-03.{py,json} (the instruments — reuse) · the NYSRC IRM Study
Appendices Table D.2 (sha256 in D45 §8; the committed rows) · data/raw/capacity-market/
demand-curve/nyiso/nyiso.csv (the per-year IRMs and translation factors already committed) ·
`PLANNING_RESERVE_MARGIN_BY_ISO`, `…ICAP_TO_UCAP_RATIO_BY_ISO`, `adequacy_requirement_mw` and
its peak source in src/market_sim · the D40 finding (the NEISO requirement-devintage pattern:
default-off, LOYO, P9-style flip condition) and the D48 PREDECL (the consistent-basis lesson:
pair net supply with a net requirement or raw with raw, never mixed).

THE WORK:
1. PRE-REGISTER (docs/handoffs/PREDECL-capx-d52-<date>.md, before any code): the expected
   requirement per capability year on the published forecast peak (Table D.2 column 1 ×
   the adopted IRM × (1 − derate)), the expected entering positions (D45 §5.2.2's "model firm
   on the PUBLISHED requirement" column — 1.046 / 1.040 / 1.052 — is the prediction), the
   expected capacity term per year, the FC-3 rows expected to move and their direction
   (requirement UP 1.5–2.7 GW ⇒ positions DOWN 5–8 pts ⇒ capacity revenue UP ⇒ exits HARDER
   under any curve; 2025 the other way by 0.4 GW), the A/B cache keys, and the §6 re-open
   condition verbatim: the curve-ON probe re-runs ONLY if the repaired L2 positions sit
   within ±3 points of the published NYCA positions in every scored year.
2. BUILD, default-off, zero DOF: (a) the NYCA requirement set on the NYSRC ICAP-market
   forecast peak for the capability year — a published market-design input that regenerates
   forward from the Gold Book forecast (rule 13), vintage-gated like D42/D44 (a value is
   admissible in year Y only if published by the run's information cutoff); (b) the
   per-capability-year adopted IRM + derate factor in place of the single 2025-26 vintage —
   the D40 axis, on the committed csv rows. ONE gated field or two, the repo's convention;
   ScenarioConfig + run_config (rule 24); matrix base row + a cell in EVERY shard (rule 28c);
   byte-inert while off, proven on the bare `nyiso-t1h` recipe.
3. A/B: the bare `nyiso-t1h` recipe (D45-R's L2 at HEAD) + the field(s) ON, diagnostics-on →
   suffixed `nyiso-t1h-d52-devintage` (~12 min). LOYO within 2021–2025. Grade at full magnitude.
4. THE CONDITIONAL PROBE: if and only if step 3's positions meet the ±3-point condition in
   every scored year, re-run L3 on the repaired posture (`--capacity-market-clearing`) →
   suffixed `nyiso-t1h-d52-curveon`, and grade it against D45's P9 (a)/(b)/(c) verbatim. If
   the condition is not met, do NOT run it — say which year fails and by how much, and route
   to §5.2.4 item 3 (the locality half), which this lane does NOT build.
5. FINDING docs/handoffs/FINDING-capx-d52-<date>.md: the requirement/position tables on the
   published basis before / after, the FC rows moved, the conditional probe's fate, and the
   arming recommendations (the devintage default; the curve-ON flip) on their pre-stated
   conditions. NOTHING ARMS — both return to the owner.

GUARDRAILS: rules 5, 12, 13 (a published requirement parameter is a design input; the SOM
margins and cleared quantities are validation observables, never targets), 14, 21, 22, 24, 25
(NYISO's own values from NYISO/NYSRC publications only), 27, 28. No keeper/shard/marker;
backcast untouched; the D45 §9 close-out line binds — no re-litigation of the mechanism class.

COLLISION: D48 (PJM), D50 (ERCOT/NEISO/PJM t1f), D51 (MISO) are disjoint. The owner's NYISO
backcast lane owns the keeper shard (nyiso-187 at issuance; read the shard, never this line).
Nobody else touches NYISO forecast surfaces this window.

EXIT: the repair default-off with matrix duties, the A/B registered suffixed, the conditional
probe run or refused on the stated condition, the pre-registration graded, the finding with
both recommendations.
```

## D53 — the sector gate: who faces the merchant retirement screen (r#35; D32 C5 / R3) — **LANDED at r#37 (PR #4766 + `107f8c79`) AND ARMED FOR MISO ONLY by in-lane owner instruction (Q43): `_miso_config` override, bare `miso-t1h` → the solved leg, D46 preserved at `miso-t1h-pre-d53`, cell K; PJM untouched** — never re-paste; the PJM leg is §D58

```
You are the D53 session of the capacity-expansion track. D32 (FINDING-capx-d32-floor-retention-
2026-09-02.md §4.3–§4.4, §5 row C5, §7 R3) measured on MISO's 2021–2025 record that 88–92 % of
the coal / gas_st / oil MW that actually exited belonged to REGULATED UTILITIES — IRP decisions,
filed as EIA-860 planned dates — while the model applies a merchant net-revenue screen to the
WHOLE fleet, so the screen fails 77–92 % of a fleet 97 % of which stayed and the reliability
floor masks 96 % of it. Q30/D44 armed the companion channel (C3, the filed dates). D49 half 2
then measured the post-dates undated cohort STILL failing 73–77 GW at $0 capacity, every MW
`entry_capped`. The structural remainder is C5: which owners face the screen at all. You design
it, build it default-off, and A/B it. Rule 1 [R-STRUCT]: right market structure first.

DATA PROFILE: miso (widen to pjm ONLY after D48 lands; see COLLISION).
MODEL ASSIGNMENT: Fable (a structural mechanism with arming consequences).
BRANCH: claude/capx-d53-sector-gate — FRESH off origin/main, rebase before every push.

READ FIRST: D32 §4.3 (the sector row of the discriminator table: 0.88 / 0.09 / 0.46 / 0.90 /
0.92 / 0.02 of exited MW by fuel), §4.4 (why the retention key is the WRONG place for this
information), §5 C5 (driver, identification, rule-13/21 status), §7 R3 (the interactions the
design must state: confirmed exits, RPS-credited clean units, CHP sectors, and the additions
screen's mirror — utility builds are IRP-driven too) · FINDING-capx-d49-2026-09-04.md §2.3–§2.5
(the post-dates cohort census you pre-declare against) · FINDING-capx-d42-* / d44 (the dates
channel and reversal registry the gate partners with; rule 19: one exit decision per unit) ·
model-methodology-spec.md §5.1–§5.2 · src/market_sim/model/capacity_evolution/retirements.py
(the screen and floor; D51 is editing a registry constant and D55 `_floor_retention_merit` in
the same file this window — touch neither) · the EIA-860 generator/plant `Sector` and
`Regulatory Status` fields as they reach the fleet (data/raw/eia-860, the fleet assembly) ·
the matrix `economic_retirement_screen` rows and every shard's cell.

THE WORK, design before code:
1. DESIGN DOC FIRST (docs/handoffs/DESIGN-capx-d53-sector-gate-<date>.md, pushed before any
   code): the partition (EIA-860 Sector 1 = electric utility → exits ONLY through step 0
   instruments and the step-1 filed-date channel; IPP / commercial / industrial sectors → the
   economic screen as today), with every interaction D32 R3 names decided and cited: confirmed
   exits (step 0, unchanged), RPS-credited clean units, CHP sectors (steam-host ownership),
   utility-owned merchant affiliates (plant `Regulatory Status` = NR: state the rule), and the
   additions-screen mirror (NOT built here — named). Rule 13 test: a published attribute that
   regenerates forward. Rule 21: a partition, no weight — say so. State the EXPECTED
   consequence from D49's census with zero solves: how many of the 73–77 GW failing MW are
   Sector 1 and leave the screen; what that does to the admission floor's binding and the
   `entry_capped` pool; whether the reachable 2.785 GW of undated real exits are IPP (the
   screen's) or utility (the channel's, i.e. unreachable without a date). Then the
   PRE-DECLARATION: FC-3 rows and direction (rule-14 sign: a gate that removes utility units
   from the screen can only REDUCE economic exits — if total exits fall and G3 reads worse,
   that is the expected signature of a screen that had been retiring units for the wrong
   reason; composition and `false_retire` are where the gate should improve), the A/B cache
   key, a P9-style flip condition.
2. BUILD default-off, zero DOF: one gated field (repo convention, e.g. `retirement_sector_gate`),
   registered in ScenarioConfig + run_config (rule 24), matrix base row + a cell in EVERY shard
   (rule 28c), byte-inert while off (prove on the bare `miso-t1h` recipe). The per-unit sector
   enters through the existing fleet assembly (rule 6 struct-of-arrays), never a hardcoded dict.
3. A/B on MISO: the bare `miso-t1h` recipe + the gate ON, diagnostics-on → suffixed
   `miso-t1h-d53-sectorgate` (~25 min, solo). LOYO within 2021–2025. Grade at full magnitude.
4. FINDING docs/handoffs/FINDING-capx-d53-<date>.md: the partition census, the FC rows moved,
   the floor's binding before / after, the composition against the real cohort, and the arming
   recommendation on the pre-stated condition. NOTHING ARMS — the default is the owner's. Name
   the PJM leg as the successor once D48 lands (D45 L1 showed PJM's 2022 screen failing 111.7 GW
   of fossil candidates — the same shape).

GUARDRAILS: rules 1, 5, 6, 12 (MISO solo), 13, 14, 19 (one exit decision per unit — the gate
and the dates channel must be reconciled explicitly, never stacked), 21, 22, 24, 25, 27, 28.
No keeper/shard/marker; backcast untouched.

COLLISION: D51 edits a MISO registry constant + `miso-t1h-d51-ratio`; D55 edits
`_floor_retention_merit`; you edit the screen's candidate set only — three lanes in
retirements.py this window, so rebase before every push and keep the diff local to your seam.
D48 owns PJM forecast surfaces — no PJM solve here. D50/D52 disjoint.

EXIT: the design doc, the gated field with matrix duties, the suffixed A/B, the finding with
the recommendation, the PJM successor named.
```

## D54 — the PJM clearing half: design and pre-declaration only (r#35; D45 §2.3 item 3) — **LANDED at r#36** (PR #4746: `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` + PREDECL; the zero-solve instrument lands the cleared position within 0.7/1.0/2.6 pts of published and the price 1.7–5.5× because the CT/ST/oil E&AS operand is zero; the build is §D57)

```
You are the D54 session of the capacity-expansion track — a DESIGN lane, no code, no solve. D45
(FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md §2.2–§2.3, §3, §4, §6, §9) closed the once-only
clearing-half question with this residue: the model evaluates the published VRR curve at its
CENSUS position, where PJM's market clears a SUPPLY CURVE of sell offers (each capped at the
unit's avoidable cost net of E&AS — Manual 18 §6, the MSOC) against the VRR curve, so the price
forms at the CLEARED quantity, 2–4 points short of the census on the auction's own basis. The
model already carries every ingredient (per-unit going-forward cost and E&AS margin are the
retirement screen's own operands). D48 is putting the position on the auctions' own
accreditation basis right now; its PREDECL §3 says the clearing-half lane "inherits a position
it can clear against". You write the design and the pre-declaration that D48's landing unlocks.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (mechanism design; the arming consequence is the largest in the chain).
BRANCH: claude/capx-d54-pjm-clearing-design — FRESH off origin/main, rebase before every push.

READ FIRST: D45 §2.1–§2.3, §3(a) (the zero-solve re-screen at the published cleared price —
13.0 of 18.1 GW of 2022 coal decisions pass at $20.86/kW-yr), §4.1 (the L1/L4 bracket), §6
(PJM: "clearing half + basis devintage, not a curve shape") · docs/handoffs/PREDECL-capx-d48-
2026-09-04.md §0–§3 (the consistent basis and the seam `accredited_firm_capacity_mw`) ·
FINDING-capx-d28-* §6.5 (the clearing-half statement, cross-ISO) · FINDING-capx-d31-* (MISO's
worked example: PRA offered vs census) · docs/handoffs/d45/published-positions-2026-09-03.json
(BRA offered / cleared / requirement per DY — VALIDATION OBSERVABLES, never targets) · PJM
Manual 18 §6 and the MSOC rules (fetch, sha256, cite) · the retirement screen's net-revenue
operands in retirements.py and the capacity-market clearing code behind
`capacity_market_clearing` (FF-2C) · spec §5.2 / §5.8.

THE DELIVERABLE (docs/handoffs/DESIGN-capx-d54-pjm-clearing-half-<date>.md + a PREDECL):
1. THE MECHANISM, stated so a successor can build it without design choices: per-unit sell
   offer = max(0, going-forward cost − E&AS net revenue), capped at the published MSOC form
   (avoidable cost rate net of E&AS); the offer stack (accredited MW on D48's basis, DR as
   supply per D48) cleared against the VRR curve at the requirement; price at the intersection;
   cleared units receive the price, uncleared units $0 — and it is the UNCLEARED set, not a
   census-evaluated curve, that feeds the retirement screen's capacity leg. Zero DOF: every
   number is a published cap or the screen's own operand. Rule 13: cleared MW and price are
   observables the design is validated against, never inputs.
2. INTERACTIONS decided and cited: the exit-rate cap (D45 §2.3 item 4, the D32/D42 object — how
   the uncleared set relates to the admission floor); the dates channel (rule 19: a dated unit
   does not offer); the reliability floor (a cleared market makes the floor's role explicit —
   state what the floor still does); the entry side (does new entry offer into the same
   stack?); the 2028/29+ price floor (D28 §4).
3. PRE-DECLARATION, against the published BRA record, zero-solve: from D48's expected positions
   and the committed net-revenue operands, the clearing price and cleared quantity the design
   would produce per DY 2021/22–2025/26, beside the published $/MW-day and cleared UCAP — with
   a stated tolerance and a stated rule-14 sign (a faithful clearing pays MORE than $0 where the
   model sat and retires HARDER in the years it over-retired). Name the falsifier: a design that
   reproduces the published price only by tuning is refused.
4. THE SEAM LIST for the build lane: files, functions, the D48 field it depends on, the cache-key
   consequence, the matrix row, the A/B plan (`pjm-t1h` control at HEAD post-D48 vs the arm,
   suffixed), and the STOP conditions.

GUARDRAILS: NO code, NO solve, NO ScenarioConfig field (rule 28 not triggered here); rules 13,
14, 21, 25 (PJM's own rules and caps; NYISO's clearing half is a separate lane after D52).
COLLISION: none — docs only. D48 owns PJM surfaces; you read its PREDECL, never its branch.

EXIT: the design doc + PREDECL pushed; the build is a SEPARATE charter the director issues once
D48 lands, unless D48's result changes the design — in which case say what changes.
```

## D55 — the retention-key float-noise fix + the release-precision diagnostic (r#35; D32 R2 + R4) — **LANDED at r#36** (PR #4747: repair exact, scorer row shipped, `miso-t1h-d55-keyfix` byte-identical to D46 — the exhausted floor makes the order unobservable; stale-golden list EMPTY, correcting this charter's premise)

```
You are the D55 session of the capacity-expansion track — a small correctness lane. D32
(FINDING-capx-d32-floor-retention-2026-09-02.md §3.2, §7 R2/R4) found that
`_floor_retention_merit` key 1 is computed per unit as (FOM × pmax × 1000) / (pmax × (1 − EFORd))
rather than as the class constant FOM × 1000 / (1 − EFORd), so IEEE-754 rounding puts same-fuel
units on different floats at 1e-11 and the CO2 / heat-rate tie-breaks fire only inside rounding
buckets — Marion (1.533 t/MWh, the dirtiest coal in MISO) was retained ahead of cleaner units.
The guarding test uses two units of equal pmax and cannot see it. At `a35c9f9b` the defect is
still in src/market_sim/model/capacity_evolution/retirements.py (the quotient form). R4: the
scorer reports `plant_recall_frac` but not plant-grain RELEASE PRECISION (released MW at
real-exit plants ÷ released MW; 13.5 % on D31).

DATA PROFILE: miso
MODEL ASSIGNMENT: Opus (correctness + a reported-only diagnostic; nothing to adjudicate).
BRANCH: claude/capx-d55-retention-key-fix — FRESH off origin/main, rebase before every push.

READ FIRST: D32 §3.1–§3.3 and §7 R2/R4 · `_floor_retention_merit` and `_apply_reliability_floor`
in retirements.py · the guarding test D32 names (`test_retention_merit_cost_then_co2`) · the
matrix `economic_retirement_screen` MISO cell (the defect citation belongs there when the repair
lands, rule 28 note) · scripts/score_capacity_hindcast.py (the reported block around
`plant_recall_frac`) · docs/FINDING-stage0-* and results/regression-goldens/ (which goldens
exercise the floor — the fix changes within-fuel retention order wherever the floor binds, so
those goldens go stale; that is the audit programme's R-AF re-capture, not yours to run).

THE WORK:
1. PRE-DECLARE (docs/handoffs/PREDECL-capx-d55-<date>.md, before the code): (a) the fix
   changes NOTHING at the cross-fuel level — the A/B's per-fuel exit totals and every FC-3 band
   verdict identical to the control; (b) within coal the 2022 MISO release becomes the
   highest-CO2 tranches (D32 §3.2 names 976, 1073, 1012, 6098, 4271, 963, …) — list the expected
   released set; (c) which committed stage-0 goldens will go stale (those whose floor binds);
   (d) the A/B cache key (a code fix does not move the config key — say so, and say the golden
   manifest is the instrument that catches it).
2. FIX key 1 to the class constant (FOM × multiplier × 1000 / (1 − EFORd) per fuel, with the
   ISO's accreditation-basis convention from `_thermal_firm_mw` preserved) or round it to a
   documented precision — choose the form that keeps the existing three-key semantics and cite
   D32 §3.2 at the definition. Add the heterogeneous-pmax tie-break test D32 §3.2 says would
   fail today; keep the existing test. No parameter, no field (rule 28: no row; add the defect
   citation to the MISO `economic_retirement_screen` cell note).
3. R4: add `plant_release_precision` (released MW at real-exit plants ÷ released MW, per year
   and window) to the scorer's REPORTED block beside `plant_recall_frac` — reported-only, no
   band, no verdict, documented in the scorer's docstring and the rubric's reported-metrics
   list. Re-score the committed `miso-t1h` bundle to show the new row (13.5 % on D31's basis
   is the sanity anchor).
4. A/B: the bare `miso-t1h` recipe at the fixed code, diagnostics-on → suffixed
   `miso-t1h-d55-keyfix` (~25 min, solo). Show (a) and (b) from the pre-declaration at full
   magnitude; a cross-fuel move is a STOP (a second mechanism is reading the key — route it).
5. FINDING docs/handoffs/FINDING-capx-d55-<date>.md: the before/after retention order, the
   cross-fuel byte-identity assertion, the stale-golden list handed to the audit programme,
   the new scorer row. Nothing to arm.

GUARDRAILS: rules 12 (MISO solo), 21 (no DOF), 22, 27 (retirements.py and the scorer are
≥300-line files: edit locally, push exact bytes, blob-verify), 28. No keeper/shard/marker.

COLLISION: D51 (registry constant) and D53 (screen candidate set) edit retirements.py this
window — keep your diff to `_floor_retention_merit` + its test; rebase before every push.
D50/D52/D48 disjoint. The audit programme owns the goldens — you list, never re-capture.

EXIT: the fix + test + scorer row landed, the suffixed A/B registered, the pre-declaration
graded, the stale-golden list routed.
```

## D56 — the NYISO `complete` re-declaration on nyiso-188 (r#35 amendment 1; owner ruling Q38) — **NEVER LAUNCHED (r#36) and its keeper MOVED to nyiso-189 — SUPERSEDED by §D56-R below; never re-paste this charter**

```
You are the D56 session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero
solves, executing owner ruling Q38 (capx ledger §0af amendment 1, 2026-09-04): NYISO's
`complete` marker, WITHDRAWN 2026-08-30 by owner ruling Q5 (lane Q5-W), is RE-DECLARED on the
designated keeper `2026-09-04-nyiso-188-combined`, the first NYISO keeper to score CALIBRATED
(grade 7 of 8, fails 0, C3c the lone ledgered caveat under the rubric v3.3 standing rule). The
withdrawn block's own `reentry` clause is the licence: "a NEW explicit owner declaration …
on a designated keeper that scores CALIBRATED". You write the declaration exactly as the
file's own conventions record one; you decide nothing.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (a marker consequence — the one records act that changes what the
program may spend).
BRANCH: claude/capx-d56-nyiso-redeclaration — FRESH off origin/main, rebase before every push.

READ FIRST: docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md IN FULL (§3.1/§3.2 are the
field-by-field record of the withdrawal you are reversing; §7 the re-entry condition; §4 the
validation-tier consequence) · frontend/data/backcast/calibration-complete.json (the `withdrawn.
NYISO` block — every field — and the PJM/NEISO/ERCOT `complete` entries as the schema: declared,
keeper, by, determination, tier_authorized, locked_test, frontier_basis, freeze_interaction,
keeper_at_declaration, keeper_rekey_policy) · CLAUDE.md rule 22 (the re-key-on-promotion
clause, D-5(b), M1) · scripts/audit_keepers.py (M1a/M1b) · frontend/data/backcast/keepers/
NYISO.json + status/NYISO.js (the live keeper and its determination_note) ·
docs/FINDING-nyiso188-* (the keeper's own record; it requested no marker) ·
frontend/data/forecast/program-status.json `isos.NYISO` (gate.a_keeper_marker, closed_on,
note, marker_complete, keeper) + `headline` + `gate_reading` + the `q5w_marker_withdrawal`
block (whose `what_changed` list is the inverse of your edit) · scripts/check_gate_a_provenance.py
· frontend/data/backcast/holdout-freeze.json (tier-scoped: the validation tier is governed by
the marker + --holdout-authorized; the locked tier stays frozen).

THE WORK, in this order:
1. RE-VERIFY FIRST, artifact-only: `scripts/calibration_verdict.py --run-id
   2026-09-04-nyiso-188-combined` — record the determination string, grade, fail set and the
   C3c caveat magnitude verbatim. If it does not read CALIBRATED, STOP and route (the ruling
   was made on a CALIBRATED reading; a moved keeper voids it).
2. THE MARKER (`calibration-complete.json`): add `complete.NYISO` with `declared` =
   2026-09-04, `keeper` = `keeper_at_declaration` = `2026-09-04-nyiso-188-combined`, `by` =
   the Q38 ruling verbatim with its ledger citation (capx ledger §0af amendment 1 / §3 Q38 —
   the card's option label: "Re-declare now via a records lane"), `determination` = step 1's
   text prefixed "CALIBRATED on … RE-VERIFIED <date> without a solve (scripts/
   calibration_verdict.py --run-id, committed artifacts only)", `tier_authorized` =
   validation ONLY (2020–2022 ladder; 2023–2025 remains the only tuned window),
   `locked_test` = NOT AUTHORIZED (absent from `final`; never scored 2019 / H1-2026),
   `freeze_interaction` = the tier-scoped freeze covers the locked test only; the validation
   tier is spendable under this marker + --holdout-authorized, and NOTHING is spent by this
   declaration, `keeper_rekey_policy` = D-5(b) re-key on every promotion with determination
   re-verification, `redeclaration` = this is the THIRD grant (2026-07-13 withdrawn 07-19;
   2026-07-31 withdrawn 08-30; today) and names both, `frontier_basis` = NONE CLAIMED (the
   frontier claim was cleared 2026-08-06 and is not re-asserted here). Move the current
   `withdrawn.NYISO` block WHOLE into the new entry (e.g. `prior_withdrawal_2026_08_30`),
   exactly as the 2026-07-31 re-declaration nested the 2026-07-19 one — never delete a byte
   of it. Leave `withdrawn.CAISO`, `final`, `intake_log` byte-identical (assert it).
   Append a dated sentence to the top-level `note`.
3. `scripts/audit_keepers.py --iso NYISO` must read PASS with M1a (marker keeper == shard) and
   M1b (determination token == live verdict) both holding; run `build_status.py --iso NYISO`
   only if the auditor asks for it.
4. THE FORECAST BOARD (`program-status.json`): re-derive `isos.NYISO.gate.a_keeper_marker`
   — status FAIL → PASS on the literal §2.1b(2)(a) test (designated full-span keeper AND a
   `complete` entry), detail rewritten to the pass form the ERCOT/PJM/NEISO rows use, with
   the Q38 citation and this lane's derivation stamp (`read_live_at`, `corrected_by`; NEVER
   forecast-provenance field names); `closed_on` drops "a"; `marker_complete` true; the
   NYISO `note`, the board `headline` and `gate_reading` rewritten to the new state (NYISO
   holds (a) + (b) — `nyiso-t1f` PROMOTE — as at r#5; state plainly that this re-opens
   NYISO's §2.1b candidacy and that a campaign is a SEPARATE owner grant the director serves
   after D52 lands); append a `d56_nyiso_redeclaration` records block in the
   `q5w_marker_withdrawal` convention (what_changed / what_did_NOT_change /
   flagged_not_edited). Assert byte-identity of every other ISO's block and of legs
   (b)/(c)/(d). `check_gate_a_provenance.py` must read OK 6/6 after. Note: this file is no
   longer round-trippable through `json.dumps(indent=1)` — edit the leaves, preserve the
   rest of the bytes, and say which serializer you used.
5. RECORDS: docs/FINDING-capx-d56-nyiso-redeclaration-<date>.md with the before/after table of
   every changed field on both surfaces (the Q5-W §3 format, inverted), the auditor and guard
   outputs, the validation-tier consequence stated (re-authorized, nothing spent, the
   touchpoint loop's rules per CLAUDE.md rule 22), and the explicit line that this lane spent
   NOTHING and solved NOTHING. Calibration log `docs/calibration-log/nyiso.md` gets a dated
   entry; the NYISO matrix shard's keeper/gates stamp gets the marker state (rule 28d — no
   verdict letter moves).

GUARDRAILS: zero solves; no year outside 2023–2025 is solved, scored or registered (the
authorization RETURNS, it is not USED here); no keeper shard edit beyond the stamp the auditor
requires; `final` untouched; the freeze file untouched; rule 27 on every ≥300-line file
(calibration-complete.json and program-status.json are both — edit locally, push exact
bytes, blob-verify). If the keeper moves while you work (NYISO promoted four times this
week), STOP: re-run step 1 on the new keeper; if it reads CALIBRATED, re-key per D-5(b) and
proceed with the new id and a dated note; if not, STOP and route — never declare on a
NOT-YET keeper (the Q5 uniform rule).

COLLISION: D52 owns NYISO FORECAST solves (`nyiso-t1h` suffixed arms) — you touch the board's
NYISO gate-(a)/headline rows only, never its FC or t1h/t1f rows; the owner's NYISO backcast
lane owns the keeper shard (read it, stamp only what the auditor requires). The audit
programme's flip set (R-AE) reads `check_gate_a_provenance` — your edit must leave it OK.

EXIT: the marker entry, auditor PASS, guard OK, the board re-derived, the finding + log +
shard stamp, all blob-verified; NYISO reads (a) PASS · (b) PASS on the board.
```

## D56-R — the NYISO `complete` re-declaration, relaunched on nyiso-189 (r#36; owner ruling Q38 + card C-10) — **LANDED at r#37** (PR #4763: `complete.NYISO` on nyiso-189, M1 PASS, validation tier returns, gate (a) PASS; frontier NOT re-asserted → Q39 → §D56-R2)

```
You are the D56-R session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero
solves, executing owner ruling Q38 (capx ledger §0af amendment 1, 2026-09-04) on the keeper
that NOW holds NYISO: `2026-09-05-nyiso-189-steam-identity`. D56 (pack §D56) was issued on
nyiso-188 and never launched; nyiso-189 superseded 188 on 2026-09-05 (PR #4743, the owner's
Bethlehem form B2), CALIBRATED → CALIBRATED. This desk re-verified it at `e75250c7`:
`scripts/calibration_verdict.py --run-id 2026-09-05-nyiso-189-steam-identity` → CALIBRATED,
C1 14/14 free 10/10, C3a PASS, C3c the lone ledgered caveat (>$300 RT hours 2023 model 3 vs
actual 10; 2024 0 vs 13; 2025 4 vs 42). The withdrawn block's own `reentry` clause is the
licence. You write the declaration exactly as the file's conventions record one; you decide
nothing.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (a marker consequence — the one records act that changes what the
program may spend).
BRANCH: claude/capx-d56r-nyiso-redeclaration — FRESH off origin/main, rebase before every push.

READ FIRST: pack §D56 IN FULL — every READ FIRST item, every step, every guardrail of that
charter binds here verbatim with `2026-09-04-nyiso-188-combined` replaced by
`2026-09-05-nyiso-189-steam-identity` and `declared` = the date you land. Then:
docs/handoffs/FINDING-nyiso189-* and results/calibration/FINDING-nyiso189-steam-collapse-
identity-2026-09-05.md (the keeper's own record; it requested no marker) · the audit board
docs/handoffs/audit-program-director-board-2026-08.md v27 entry, sections "Z-4" and
"FOUR-INSTRUMENT ALIGNMENT" (the R-AG ruling and the frontier question) · capx ledger §0ag.5
(card C-10) and §3 (the R-AG cross-desk record) · frontend/data/backcast/keepers/NYISO.json
`frontier` history (declared 2026-08-23, withdrawn 2026-08-30 with the marker).

THE WORK: §D56 steps 1–5 unchanged on nyiso-189, PLUS:
A. THE FRONTIER LIMB — CONDITIONAL ON CARD C-10 (ledger §0ag.5; the ruling, if given, is Q39
   in ledger §3). Read §3 before you start:
   - If Q39 rules "both" (option A): re-declare `frontier` on nyiso-189 in keepers/NYISO.json
     in the exact shape ERCOT/PJM/NEISO carry (the 2026-08-30 withdrawal's inverse — read
     docs/FINDING-q5w-* for the fields it removed), `frontier_basis` in the marker entry names
     it, and the four instruments (frontier · complete · gate-(a) · determination) read
     {ERCOT, NEISO, PJM, NYISO} together; say so in the finding's alignment table.
   - If Q39 rules `complete` only (option B), or if NO ruling is recorded in §3 when you
     start: `frontier_basis` = NONE CLAIMED exactly as §D56 wrote it, the keeper shard's
     `frontier` untouched, and the finding's alignment table states that the frontier leg
     stays split BY THE OWNER'S CHOICE (or pending it), never silently.
   - If Q39 declines the re-declaration entirely (option C): STOP before step 2, record the
     ruling in the finding, land nothing else.
B. THE R-AG / Q38 RECORD: the finding's §1 states, verbatim from audit board v27, that owner
   ruling R-AG (2026-09-04 22:20Z) routed this question to the calibration director for a
   recommendation with no audit-lane marker edit, that Q38 (23:18Z) ruled the execution
   without sight of it, and that C-10 is the recommendation R-AG asked for — both rulings are
   the owner's and this lane executes Q38 (+ Q39 if ruled). No re-litigation.
C. THE STOP CLAUSE, SHARPENED: NYISO promoted five times in two days. Before EVERY push
   re-read keepers/NYISO.json; if the keeper moved again, re-run step 1 on the new id; if it
   reads CALIBRATED, re-key per D-5(b) with a dated note and proceed; if NOT-YET, STOP and
   route — never declare on a NOT-YET keeper (the Q5 uniform rule).
D. Process seam (desk doctrine from r#36, the audit board's X-6b): no scoring here, but the
   same rule for provenance stamps — every `derived_at` / `read_live_at` leaf you write names
   the origin/main sha you actually read at, re-read after your final rebase.

GUARDRAILS, COLLISION, EXIT: as §D56, on nyiso-189. D59 (NYISO forecast t1h suffixed arms)
and the owner's NYISO backcast lane are the other NYISO writers this window — you touch the
marker, the board's NYISO gate-(a)/headline rows, the finding, the log, and the shard stamp
the auditor requires (plus `frontier` only under option A); nothing else.
```

## D57 — the PJM clearing half: BUILD + A/B (r#36; D54 §7 executed; the D48 §8 configuration) — **LANDED + PROMOTED IN-SESSION (Q44) at r#38** (PRs #4761/#4775/#4786: cleared position within −0.5/−1.0/−2.8 pts of published, identity 8/8, price 1.5–5.7× because the CT/ST/oil E&AS operand is ZERO; joint PJM posture armed via `_pjm_config`; arm A = bare `pjm-t1h`; successor → §D61; `pjm-t1f` re-measure → §D60 Am.1)

```
You are the D57 session of the capacity-expansion track — the BUILD lane for the PJM clearing
half. The design is written and landed: docs/handoffs/DESIGN-capx-d54-pjm-clearing-half-
2026-09-05.md (§3 the mechanism stated so you build it without design choices; §4 every
interaction decided; §7 the seam list, the A/B plan and seven STOP conditions) with its
pre-declaration docs/handoffs/PREDECL-capx-d54-pjm-clearing-half-2026-09-05.md (§2 the
zero-solve instrument's per-DY cleared position and price on the committed ledgers; §3 the
per-leg expectations; §4 the falsifier). D48 Phase 1 (FINDING-capx-d48-2026-09-04.md §8)
landed with the recommendation that its two fields be armed WITH this mechanism, not alone —
the admission cap prices a consistent budget at an inconsistent $0 until the market clears.
The design's own instrument already says what you will measure: the cleared position lands
within 0.7 / 1.0 / 2.6 pts of the published cleared position, and the clearing price lands
1.7× / 2.4× / 5.5× the published price BECAUSE the gas-CT / gas-ST / oil fleets carry exactly
zero E&AS margin in the hindcast prices (D45 §1(i)). You build the mechanism, prove the
Phase-0 reproduction, solve the two arms, and report the E&AS operand as the object. A build
that lands on the published price without an operand change is REFUSED (PREDECL §4) — you
do not touch the operand.

DATA PROFILE: pjm
MODEL ASSIGNMENT: Fable (the largest arming consequence in the chain; the settlement identity
§3.5 is a mechanism, and every seam decision in §4 must be honoured, not re-decided).
BRANCH: claude/capx-d57-pjm-clearing-build — FRESH off origin/main, rebase before every push.

READ FIRST: the DESIGN §0–§9 IN FULL and the PREDECL IN FULL · FINDING-capx-d48-2026-09-04.md
§3.3 (the admission cap as the second mechanism), §5 item 1, §8 · FINDING-capx-d45-pjm-nyiso-
curves-2026-09-03.md §2.1–§2.3, §3(a), §6, §9 · docs/handoffs/d45/published-positions-
2026-09-03.json (VALIDATION OBSERVABLES, never targets) · src/market_sim/config/
capacity_market.py (`resolve_capacity_market_clearing`, the sibling predicate you add) ·
src/market_sim/model/capacity_evolution/retirements.py (the screen's capacity leg; D53's
`retirement_sector_gate` may or may not have merged — read origin/main at your start and
state which: design §4.7 says the gate needs no design change, gated units enter the stack as
$0 price-takers) · `_CACHE_KEY_OPTIONAL_FIELDS` / `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in
scenarios.py (D24-R's (b′-1) ledger) · scripts/check_cache_key_registration.py ·
scripts/run_capacity_hindcast.py (the harness flag convention; D48's flags as the template) ·
the matrix `capacity_market_clearing` rows and the PJM shard's cells · the D53 branch's
`tests/unit/model/test_capacity.py` if D53 is unmerged (you both add tests to that file —
put yours beside `TestPjmAccreditationDesignVintage` as §3.6 says, and rebase before every
push).

THE WORK, in this order:
1. PHASE 0 — REPRODUCE THE INSTRUMENT IN CODE, zero solves: implement the clearing function
   per design §3.2–§3.4 and run it on the committed ledgers (`pjm-t1h` D45-R and
   `pjm-t1h-d48-devintage`) — it must reproduce PREDECL §2's per-DY clearing price to within
   $1/MW-day and the cleared position to within 0.1 pt (STOP 1 otherwise). Commit the
   reproduction table BEFORE any solve.
2. BUILD, default-off, zero DOF: `capacity_market_supply_clearing_by_iso: dict[str, bool] |
   None = None` exactly as §7.1 (requires the curve gate; `None` ⇒ byte-identical; coerced
   to `None` in a plain backcast as the curve gate is); registered in the optional-field
   ledger at `"None"` (rule 24; `check_cache_key_registration.py --base origin/main` green);
   harness flag; `validate_parameters.py` entry; the invariants §3.6 as tests (I1 census
   recovered when every offer is $0 or the market is short; I2 cleared ⇔ passing beyond the
   marginal unit; I3–I5 as written); matrix base row + a cell in EVERY shard (rule 28c), PJM
   the only one that will carry a measured verdict (rule 25). Prove byte-inert on the bare
   `pjm-t1h` recipe (the key `c6091bd5b62bbc3f` must not move — STOP 2 if any bare key moves).
3. PRE-DECLARATION ADDENDUM (docs/handoffs/PREDECL-capx-d57-<date>.md, pushed before any
   solve): PREDECL-d54 §3 re-stated on the posture you actually found at HEAD (D53 merged or
   not; D48 fields' HEAD state), the two arm keys resolved through the harness path, the
   expected FC-3 sign (a faithful clearing pays MORE than $0 where the model sat and RETAINS
   the +1.4 GW of cap-admitted coal D48 released; 2025 moves only through the entering-fleet
   consequence), the expected price ratios per DY (1.7× / 2.4× / 5.5× — the E&AS operand's
   signature), and the STOP-4 falsifier restated: an arm's price within ±20 % of published in
   a long year means an operand moved — stop and find it.
4. THE A/B (design §7.6), PJM solo (rule 12; 9.6–9.9 GB measured), years sequential:
   control = the bare `pjm-t1h` at HEAD (re-solve it FIRST if its key moved since D45-R —
   D45-R's rule); **arm A** = D48 both fields ON + supply clearing ON → `pjm-t1h-d57-clearing`
   (the D48 §8 configuration, primary); **arm B** = D48 fields OFF + clearing ON →
   `pjm-t1h-d57-clearing-headbasis` (the isolating control; with `pjm-t1h-d48-devintage` the
   2×2 factorial is complete). `--entry-screen-diagnostics` on; suffixed keys ONLY, never the
   bare key; score `forecast_verdict.py --tier t1h`; register with `register_forecast_run.py
   --bundle`. Score and register AFTER your final rebase (desk doctrine: an orphaned
   `scored_at_sha` names a commit that no longer exists — if you must rebase after scoring,
   re-score artifact-only before merge so the stamp resolves).
5. FINDING docs/handoffs/FINDING-capx-d57-<date>.md: the Phase-0 reproduction; per DY the
   design's cleared position / price beside the published pair (both arms); the uncleared set
   vs the screen's failing set (the §3.5 identity asserted from the ledgers); FC-3 row by row
   for both arms against the control AND against `pjm-t1h-d48-devintage`; what the admission
   cap does now that the budget is priced; **the E&AS operand measured** — how many GW of
   offers sit above the published price by fuel, and what E&AS margin per unit would put the
   cleared position AND the price on the published pair (a statement about the operand, NOT
   a fitted value — you change nothing); the pre-declaration graded at full magnitude;
   the ARMING RECOMMENDATION on the pre-stated condition for the JOINT flip (D48's two fields
   + this gate for PJM) — NOTHING ARMS in this lane; the owner decides on the card.

GUARDRAILS: rules 1, 5, 6, 12 (PJM solo), 13 (cleared MW and price are observables you
validate against, never inputs), 14, 19 (one capacity-revenue mechanism per unit — the
census evaluation is REPLACED for PJM when the gate is on, never stacked), 21 (NO free
parameter; the E&AS operand is measured and reported, never tuned — PREDECL §4's refusal
binds), 22 (2021–2025 solve years, 2022 bridged and never scored, nothing outside), 24, 25
(PJM's own registry; the gate is generic in form and PJM-scoped by data), 27 (retirements.py,
scenarios.py, capacity_market.py and the test file are ≥300-line files: edit locally, push
exact bytes, blob-verify), 28 (row + six cells in the build commit). No keeper / shard /
marker; backcast byte-identical (assert the plain-backcast coercion with a keeper replay of
the run_config, no LP).

STOP conditions: design §7.7 items 1–7 verbatim, plus: D53 merges mid-lane and moves the
bare `pjm-t1h` key → re-resolve, re-declare the arm keys, say so.

COLLISION: D53 (`retirements.py` candidate set + `test_capacity.py`; in flight) — keep your
diff to the clearing function, the predicate, the screen's capacity-leg call site and your
own test class; rebase before every push. D58 (the PJM sector-gate leg) is HELD until you
land — you are the only PJM forecast writer. D50-R writes suffixed PJM t1f keys and the PJM
shard's CCS cell only; disjoint from your row. The owner's backcast lanes never touch PJM
forecast surfaces.

EXIT: the gated mechanism with matrix duties and tests; the Phase-0 reproduction table; both
suffixed arms registered; the pre-declaration graded; the E&AS operand measured and stated;
the joint arming recommendation on the pre-stated condition. Nothing armed.
```

## D58 — the PJM sector-gate leg (r#36; D53 routed item 1) — **RELEASED at r#38 (D53 merged ✓, D57 landed ✓) — dispatch AFTER D60's finding lands (D60 writes the PJM board t1f row); the control is the NEW bare `pjm-t1h` (the Q44 joint posture, `f0e050e820c1159a`); Opus per audit ruling R-AK** — **RELEASED r#46 am.1 (D60-R3 merged #5038). TWO CORRECTIONS TO THIS SECTION'S TEXT: `f0e050e820c1159a` is a CACHE KEY, not a git sha (the committed D57 arm A's git anchor is `5bb70047`); and that committed control is PRE-hunk on SCN-LOAD `d14a7ed0` (`DEMAND_GROWTH_RATES["PJM"].mid.near` 0.036 → 0.064645 moves the T1-H screen peak −10,819 / −7,574 / −3,977 / 0 / +4,386 MW, measured by the D67 lane) — form 4 is VOID, so solve a SAME-HEAD control for the screen span (rule 29(b)), delete it before merge (29(c)), and classify #5033 (P1 basis seed) in the drift audit. The D67 lane (`claude/capx-d67-pjm-requirement-operand-18wzjf`), D74 and D75 share PJM hindcast surfaces on different seams: merge-order care, not a dependency.**

```
You are the D58 session of the capacity-expansion track — the PJM leg of the sector gate D53
built and measured on MISO. D53 (FINDING-capx-d53-2026-09-05.md; design DESIGN-capx-d53-
sector-gate-2026-09-05.md) partitioned the retirement screen's candidate set on the published
EIA-860 `Sector` attribute (sector 1 = electric utility exits only through the step-0
instrument and step-1 filed-date channels; every other sector faces the merchant screen);
on MISO the screen's failing pool fell 76.75 → 17.46 GW with zero sector-1 rows and every
exit byte-identical. D53 §7 item 1 names PJM as the DISCRIMINATING test: D45 L1 showed
PJM's 2022 screen failing 111.7 GW of fossil candidates on a merchant-heavy sector mix, so
the failing pool should shrink by a MINORITY where MISO's shrank by 77 %. You run that leg,
pre-declared, against your own census.

DATA PROFILE: pjm
MODEL ASSIGNMENT: Opus (pre-declared execution of a landed mechanism on a second ISO; the
verdict letter is PJM's own — rule 25).
BRANCH: claude/capx-d58-pjm-sectorgate — FRESH off origin/main, rebase before every push.

PRECONDITIONS (check at start; STOP and say so if either fails): `retirement_sector_gate` is
in ScenarioConfig on origin/main (D53 merged); `capacity_market_supply_clearing_by_iso` is on
origin/main (D57 landed) — you run on the posture D57 leaves, and you state it.

READ FIRST: D53's design §0.2–§0.4 (the MISO census method you reproduce for PJM: fleet by
sector, the bare recipe's failing set by sector, the real cohort by sector), §1.2–§1.8
(the partition and every interaction), §2.1 (why the gate cannot move an exit on a
zero-headroom floor — check whether PJM's floor HAS headroom: D48 §3.3 says the PJM
admission cap admitted +1.4 GW, so PJM may be the first ISO where the gate's composition
effect is observable on the PRIMARY leg) · FINDING-capx-d53 §2–§4, §6 · FINDING-capx-d45 §2
(L1: the 111.7 GW pool) · FINDING-capx-d48 §3 · FINDING-capx-d57 (the posture at HEAD; which
of D48's fields and the clearing gate are ON in the bare `pjm-t1h` — if the owner armed the
joint flip, the bare key has moved and your control is the new bare) · the PJM matrix shard
`economic_retirement_screen` + `retirement_sector_gate` cells · data/raw/eia-860 (the PJM
plant table at the 2020 vintage, the sector reader D53 added).

THE WORK:
1. PRE-DECLARE (docs/handoffs/PREDECL-capx-d58-<date>.md, zero solves, before any LP): the
   PJM fleet by sector at the 2020 vintage; the bare `pjm-t1h` screen's 2022/2023 failing
   set by sector from the committed ledgers; the real PJM exit cohort 2021–2025 by sector;
   the expected gated-failing MW and the fraction of the failing pool that leaves (the
   "minority" claim, in numbers); whether PJM's floor has headroom at the 2022/2023 screens
   (if yes, pre-declare the composition of the release: merchant plants, plant-grain
   precision vs the control); the arm's cache key resolved through the harness path; the
   rule-14 sign (a gate can only REDUCE economic exits — if total exits fall and G3 reads
   worse that is the expected signature); a P9-style flip condition for PJM.
2. THE ARM: the bare `pjm-t1h` recipe at HEAD + `--retirement-sector-gate` (D53's harness
   flag) → suffixed `pjm-t1h-d58-sectorgate`, PJM solo (rule 12), sequential, ~15–25 min.
   Control = the bare `pjm-t1h` at HEAD (re-solve first if its key moved). Score and
   register AFTER the final rebase (desk doctrine: no orphaned `scored_at_sha`).
3. FINDING docs/handoffs/FINDING-capx-d58-<date>.md: the census before/after by sector, the
   FC-3 rows moved (expected: none on a zero-headroom floor; the composition of any release
   if PJM's floor has headroom), the pre-declaration graded at full magnitude, the PJM
   shard's `retirement_sector_gate` cell stamped with PJM's OWN letter (U → the measured
   verdict; rule 25 — MISO's K/O never fills it), and the arming recommendation for PJM on
   the pre-stated condition. NOTHING ARMS.

GUARDRAILS: rules 1, 12, 13, 14, 19, 21, 22, 24, 25, 27 (any ≥300-line file), 28d. No
keeper / shard / marker; no mechanism code (D53 built it; if PJM needs a seam D53 did not
build, STOP and route — do not extend the gate in this lane).

COLLISION: you are dispatched only when no other PJM forecast writer is open (D57 landed,
D50-R's PJM t1f leg disjoint by tier). Rebase before every push regardless.

EXIT: the pre-declaration, the suffixed arm registered, the finding with the PJM cell letter
and the recommendation.
```

## D59 — the NYISO locality half: the short-locality demand curve (r#36; D45 §5.2.4 item 3, D52 §8 route) — **LANDED at r#37** (PRs #4760/#4764: `locality_capacity_curves` built; A/B byte-identical — NYC census +0.7–0.8 GW above the Gold Book; P9 one-of-three; DO NOT ARM either; cell I)

```
You are the D59 session of the capacity-expansion track. D52 (FINDING-capx-d52-2026-09-04.md)
closed NYISO's POSITION artifact — with the two requirement gates on, the NYCA position sits
within ±3 pts of the market in every scored year — and re-ran the curve-ON probe: the 2023
wave D45 L3 fired at $0 is gone, and what fires instead is 1,801 MW of DOWNSTATE gas_st at
the 2025/26 NYCA curve's $28.65/kW-yr, where the market paid $51.36 NYCA-wide and Zone J
(NYC) cleared at $141. D52 §8(2) routes, in order: (1) the LOCALITY half — NYC / LI / G-J as
the NYISO instance of the locational capacity machinery; (2) the 2025/26 curve-vintage /
2025 SOM transcription check; (3) THEN the same P9 (a)/(b)/(c) probe re-run. Read the seam
before you design: the shipped Part-B gate (`capacity_deliverability_limits`,
docs/capacity-deliverability-wiring.md) COLLAPSES the marginal capacity payment in a LONG
zone (RA saturated). NYISO's object is the opposite sign — a SHORT locality paid ITS OWN
published demand curve, which is literally how the NYISO spot market administers price
(price = curve(supplied UCAP), per locality; D28 §4, D54 §4.9). So the instance is not a
re-use of the long-zone collapse; it is the per-locality curve evaluated at the per-locality
position, with a unit in NYC / LI / G-J paid the max over the localities it sits in and the
NYCA price. Rule 25: NYISO's own mechanism with NYISO's own published rows; rule 1: the
right market structure first.

DATA PROFILE: nyiso
MODEL ASSIGNMENT: Fable (mechanism design with an arming consequence; a design decision at
the seam).
BRANCH: claude/capx-d59-nyiso-locality — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d52 §0, §3–§5, §8 IN FULL · FINDING-capx-d45-pjm-nyiso-curves-
2026-09-03.md §5.2.4 items 3–4, §5.3 (L3), §6, §9 · FINDING-capx-d28-* §4 and §6.5 (NYISO:
"the one ISO whose real mechanism IS evaluate the curve at a census quantity") ·
docs/capacity-deliverability-wiring.md (Part B; the NYISO crosswalk: NYC(J)/LI(K) 1:1, G-J
aggregate excluded — decide whether G-J is representable on the 5-zone model and say so) ·
data/raw/capacity-deliverability/nyiso/nyiso.csv + README (the committed LCR / import-limit
rows: which capability years, which localities) · data/raw/demand-curve/nyiso/ (does it
carry the NYC / LI / G-J ICAP demand-curve parameters — reference point, zero-crossing,
net-CONE — per capability year, or NYCA only? If locality curves are NOT committed, the
intake is your Phase 0: NYISO ICAP Demand Curve filings / the annual reset, fetched,
sha256'd, curated through the data contract — a data-intake step, not a solve) · the D52
fields `nyiso_requirement_forecast_peak` / `nyiso_requirement_vintage_factors` and the four
seam ledger fields D52 added (`screen_*`) · src/market_sim/model/capacity.py
(`deliverability_headroom_by_zone`, `_zone_is_long`) and the screen's capacity-leg call
site in retirements.py · the NYISO matrix shard (`capacity_deliverability_limits`,
`capacity_market_clearing` cells) · the NYISO 2025 SOM capacity section (the $51.36 / $141
spot figures D52 quotes — the transcription check).

THE WORK, design before code:
1. DESIGN DOC FIRST (docs/handoffs/DESIGN-capx-d59-nyiso-locality-<date>.md, pushed before
   any code): (a) the locality set representable on the model's zones (J, K certainly; G-J
   only if the zone partition supports it — state the rule); (b) per locality: requirement
   = LCR × the locality's forecast peak (published), supply = in-locality accredited UCAP +
   the crosswalked import limit, position, the locality's own demand curve at that position;
   (c) settlement: a unit's capacity revenue = max(NYCA price, the price of every locality it
   sits in) × accredited MW — cite the ICAP Manual's locality-stacking rule; (d) zero DOF: every
   number a published curve parameter or requirement; (e) interactions decided: the D52
   requirement gates (the NYCA half; this design sits on top, never re-derives it), the
   shipped long-zone collapse (state whether it can co-exist for NYISO or must be superseded
   per rule 19 — one locational mechanism per ISO), the dates channel, the reliability floor,
   the entry side (does new downstate entry see the locality price? it must, or the design
   pulls exits without pulling entry); (f) the 2025/26 vintage / 2025 SOM transcription check
   (D52 §8 item 2), zero-solve, done here and its result stated; (g) THE PRE-DECLARATION: on
   D52's committed `nyiso-t1h-d52-curveon` ledger, zero-solve, the locality positions and
   prices per year beside the published locality clearing prices (validation observables,
   never targets); the expected FC-3 sign (downstate steam retires HARDER — the 1,801 MW
   gas_st wave at $28.65 should shrink or vanish under a $141 Zone J price; rule 14); the
   arm keys; a P9-style flip condition; the falsifier (a design that reproduces the published
   locality price only by tuning is refused).
2. BUILD default-off, zero DOF: one gated field (repo convention; per-ISO in form, NYISO in
   data — rule 25), registered in ScenarioConfig + run_config (rule 24), the optional-field
   ledger, harness flag, matrix base row + a cell in EVERY shard (rule 28c), byte-inert while
   off (prove on the bare `nyiso-t1h` recipe, key `91686abe7a744a88` or its HEAD successor).
   The locality rows enter through the existing curated readers (rule 6), never a dict.
3. THE A/B on NYISO (rule 12: NYISO solo, ~12 min per leg, sequential): the D52 posture
   (both requirement gates ON, curve ON — i.e. the `nyiso-t1h-d52-curveon` recipe) + the
   locality gate → suffixed `nyiso-t1h-d59-locality`; comparator `nyiso-t1h-d52-curveon`
   (`589f031432b6dc7d`). Then the SAME P9 (a)/(b)/(c) test D45/D52 pre-stated, re-read on
   this record — the curve question re-opens on it, not before (D52 §8). If the owner has
   armed D52's gates (card C-12) the bare `nyiso-t1h` key has moved — re-resolve and say so.
   Score and register AFTER the final rebase (desk doctrine: no orphaned `scored_at_sha`).
4. FINDING docs/handoffs/FINDING-capx-d59-<date>.md: the locality positions / prices per
   year vs published; FC-3 row by row vs the comparator; the P9 reading; the pre-declaration
   graded at full magnitude; the NYISO shard cells stamped; the arming recommendation on the
   pre-stated condition (the locality gate; and, separately, whether P9 now says the NYCA
   curve may be consulted — two recommendations, two conditions). NOTHING ARMS.

GUARDRAILS: rules 1, 5, 6, 12, 13 (published curves and requirements only; cleared prices are
observables), 14, 19, 21, 22 (2021–2025; nothing outside), 24, 25, 27, 28. No keeper / shard
/ marker; backcast byte-identical (the field coerces off in a plain backcast as the curve gate
does — assert it).

COLLISION: D56-R writes the marker + the board's NYISO gate-(a)/headline rows — you touch
NYISO FORECAST surfaces (suffixed t1h keys, FC rows) and the NYISO shard's cells only. The
owner's NYISO backcast lane owns the keeper shard. No other NYISO forecast writer this window.

EXIT: the design + pre-declaration pushed first; the gated field with matrix duties; the
suffixed A/B registered; the P9 re-read; the finding with both recommendations; the
transcription check answered.
```

## D50-R — the D50 completion: the PJM arm, the blast radius, the finding (r#36; D50 checkpoint) — **LANDED at r#37** (PR #4768: PJM 3,584.7 → 909.8 MW, MISO 4,631 → 0, blast radius 1.1 h residual, ARM recommended → Q42 ARM → §D60)

```
You are the D50-R session of the capacity-expansion track — a COMPLETION lane. D50 (pack §D50)
landed as a checkpoint in PR #4728: `ccs_retrofit_capex_co2_scaling` built default-off with
seam 2 (CHP hosts excluded) and the p55470 flag; the ERCOT t1f arm `ercot-t1f-d50-ccscapex`
(0 conversions vs the control's 2,741.8 MW; HOLD → HOLD) and the NEISO arm
`neiso-t1f-d50-ccscapex` (the 3 GW/yr cap still binds under RGGI; who converts changes;
PROMOTE → PROMOTE) registered and stamped into the ERCOT and NEISO matrix cells. OWED, and
you deliver: the PJM t1f arm, the §6 blast radius, the §8 arming recommendation, and
`docs/handoffs/FINDING-capx-d50-2026-09-04.md` ITSELF — which all three ISO shards' cells
already cite by name and which does not exist on main (write it under that exact filename so
the citations resolve; date the body honestly as written 2026-09-05+).

DATA PROFILE: pjm (ercot/neiso ledgers are committed; read them, do not re-solve)
MODEL ASSIGNMENT: Opus (execution of a committed pre-declaration; no new mechanism; the
arming decision is the owner's, on the card the finding prices).
BRANCH: claude/capx-d50r-completion — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/PREDECL-capx-d50-2026-09-04.md IN FULL (§2.2 the PJM expectation —
0 conversions vs the control's 16 rows / 2,832.6 MW 2028 + 3 / 752.1 2029 = 3,584.7 MW, seam 2
load-bearing for 722 MW of CHP rows; Addendum A.3 the PJM 2029–2030 residual channel; §3 the
STOPs; §4 the keys; §5 the FC rows; §6 the blast-radius expectation) · the ERCOT and NEISO
matrix cell texts for `ccs_retrofit_capex_co2_scaling` (the measured results you carry into
the finding verbatim) · results/ff-t1f-*/ for the two registered arms' `full_horizon_summary`
and evolution ledgers · FINDING-capx-d49-2026-09-04.md §1 · FINDING-capx-d41-* §6.2 (the
blast-radius precedent) · FINDING-capx-d44-* §1 (the b′-1 declared-default-flip mechanics) ·
frontend/data/forecast/ff-verdicts.json + registry (every committed forecast/hindcast key —
the blast radius is enumerated from them) · the D45-R measured t1f rates (PJM 28 min / MISO
65 min / ERCOT 11.8 / NEISO 6.7 / NYISO ~12) and D46/D47b's `c_cost` corrections.

THE WORK:
1. THE PJM ARM: the bare `pjm-t1f` recipe (`pjm-2026-2030-d45r-remeasure`, key
   `321f04e9060787f0` — re-resolve at HEAD; if it moved, say so and use the HEAD bare) +
   `--golden-posture` + the D50 field ON → suffixed `pjm-t1f-d50-ccscapex`, PJM solo (rule
   12), ~28 min. Score `forecast_verdict.py --tier t1f`; register `--bundle`. Score and
   register AFTER your final rebase (desk doctrine: no orphaned `scored_at_sha`). Grade
   PREDECL §2.2 at full magnitude; STOP per §3 if the repaired screen clears MORE MW.
   MISO t1f (~65 min) ONLY if PJM contradicts §2.2 (PREDECL §2.4's own rule).
2. THE BLAST RADIUS, measured (charter step 4): every committed forecast/hindcast key whose
   cache key the default flip would advance (the b′-1 pattern: the field enters the declared-
   defaults ledger; list keys by ISO and tier, bare and suffixed, goldens included — GOLDEN-2 /
   GOLDEN-3 carry the CCS screen from 2028), and the solve-minutes to re-measure the BARE keys
   at the measured rates. That number goes on the owner's card verbatim.
3. THE FINDING `docs/handoffs/FINDING-capx-d50-2026-09-04.md`: §1 the whole-fleet census
   (PREDECL §2.5 / A.1); §2 ERCOT (from the cell text + ledgers), §3 NEISO, §4 PJM (yours);
   §5 the FC rows moved per ISO; §6 the blast radius; §7 the pre-declaration graded (all of
   P1–P8 and Addendum A); §8 the ARMING RECOMMENDATION on D50's pre-stated condition (state it
   verbatim from the PREDECL, then grade it) — NOTHING ARMS; §9 governance attestation
   (rule 27 blob checks; rule 22; the pre-declared-follow-up attestation limb Q37 adopted,
   since you author for a lane that has closed). Stamp the PJM shard's cell with the measured
   result in the ERCOT/NEISO cells' exact style; leave the ERCOT/NEISO cell texts byte-identical
   except to replace "stamped with its measured verdict in FINDING…" wording only if it is
   false at your landing.
4. Records: the D46/D47 `t1f_provenance` conventions (D51 rider) apply to the new key;
   CHANGELOG line; nothing on the backcast side.

GUARDRAILS: rules 12, 13, 14 (fewer conversions is the expected signature), 21, 22, 24, 25,
27, 28. No keeper / shard / marker; no default flip; no ERCOT/NEISO re-solve.

COLLISION: D57 owns PJM t1h surfaces and the PJM shard's clearing cells — you write the PJM
t1f suffixed key and the PJM shard's CCS cell only; rebase before every push. D58 is held.

EXIT: `pjm-t1f-d50-ccscapex` registered; the blast radius priced; the finding at the cited
filename with §8's recommendation; the PJM cell stamped. Nothing armed.
```

## D56-R2 — the NYISO `frontier` re-declaration on nyiso-189 (r#37; owner ruling Q39 on card C-10) — **LANDED at r#38** (PR #4780; all four instruments read {ERCOT, NEISO, NYISO, PJM})

```
You are the D56-R2 session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero
solves, executing owner ruling Q39 (capx ledger §0ah.3 / §3, 2026-09-05): NYISO's `frontier`
declaration, WITHDRAWN 2026-08-30 together with the `complete` marker (lane Q5-W), is
RE-DECLARED on `2026-09-05-nyiso-189-steam-identity` — the keeper D56-R (PR #4763) already
restored `complete` on. The owner's ruling reads: both instruments, as the withdrawal removed
both; the four-instrument test (frontier · complete · gate-(a) · determination) reads
{ERCOT, NEISO, PJM, NYISO} together. You write the declaration in the file's own shape; you
decide nothing.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (a marker consequence).
BRANCH: claude/capx-d56r2-nyiso-frontier — FRESH off origin/main, rebase before every push.

READ FIRST: docs/handoffs/FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md IN FULL (the
`complete` half you complete; its alignment table names the frontier leg as split "by the
owner's pending choice") · docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md §3 (the
field-by-field record of what the withdrawal removed from keepers/NYISO.json `frontier` and
from the marker — your edit is its exact inverse on the new keeper) · frontend/data/backcast/
keepers/ERCOT.json, PJM.json, NEISO.json `frontier` blocks (the schema you mirror: declared
date, keeper, basis, the owner citation) · frontend/data/backcast/keepers/NYISO.json (the
withdrawn `frontier` history: declared 2026-08-23, withdrawn 2026-08-30) ·
frontend/data/backcast/calibration-complete.json `complete.NYISO.frontier_basis` (currently
"NONE CLAIMED …") · docs/handoffs/audit-program-director-board-2026-08.md v27 "FOUR-INSTRUMENT
ALIGNMENT" (the test your finding re-reads) · scripts/audit_keepers.py.

THE WORK:
1. RE-VERIFY FIRST, artifact-only: keepers/NYISO.json `keeper` is still
   `2026-09-05-nyiso-189-steam-identity` and `scripts/calibration_verdict.py --run-id` reads
   CALIBRATED. If the keeper moved: if the new one reads CALIBRATED, declare on it with a
   dated note (D-5(b)); if NOT-YET, STOP and route (never a frontier on a NOT-YET keeper).
2. keepers/NYISO.json: add the `frontier` block in the ERCOT/PJM/NEISO shape — declared
   2026-09-05, keeper nyiso-189, `by` = the Q39 ruling verbatim with its ledger citation
   (capx ledger §0ah.3 / §3 Q39; card C-10's option label "Re-declare frontier on nyiso-189"),
   the withdrawn 2026-08-30 block PRESERVED beneath it (never delete a byte). Run
   `build_status.py --iso NYISO` only if the auditor asks.
3. calibration-complete.json: rewrite `complete.NYISO.frontier_basis` from NONE CLAIMED to
   the declaration (keeper id + date + Q39 citation), preserving the prior text as a dated
   "was:" clause. Every other field of the entry, every other ISO, `withdrawn`, `final`,
   `intake_log` byte-identical (assert it).
4. `scripts/audit_keepers.py --iso NYISO` PASS; `check_gate_a_provenance.py` OK 6/6 (no
   gate-(a) leaf moves — frontier is not a gate-(a) input; say so); `check_mechanism_matrix.py`
   OK (re-stamp the NYISO shard's keeper/gates header ONLY if the checker asks).
5. RECORDS: docs/handoffs/FINDING-capx-d56r2-nyiso-frontier-<date>.md with the before/after
   table on both surfaces, the four-instrument alignment table re-read at your pin (all four
   now {ERCOT, NEISO, PJM, NYISO}), the auditor/guard outputs, and the explicit line that this
   lane spent NOTHING and solved NOTHING; a dated line in docs/calibration-log/nyiso.md; the
   audit board is NOT yours to edit — the alignment result is stated in your finding for the
   audit desk to read.

GUARDRAILS: zero solves; no year outside 2023–2025 touched; `final` untouched; the freeze
untouched; rule 27 on calibration-complete.json / keepers/NYISO.json / program-status.json
(edit locally, push exact bytes, blob-verify; program-status.json should not need touching —
if it does, targeted leaf edits only). Provenance stamps name the origin/main sha you actually
read at, re-read after your final rebase (desk doctrine X-6b).

COLLISION: D60 (the arming batch) writes NYISO FORECAST surfaces + scenarios.py/iso_configs.py
— disjoint from your two files. The owner's NYISO backcast lane owns the keeper shard's
promotion fields — you add the `frontier` block only.

EXIT: the frontier block, the marker's `frontier_basis`, auditor PASS, guards OK, the finding
with the alignment table, the log line; all blob-verified.
```

## D60 — the arming batch: Q40 (MISO ratio) + Q41 (NYISO requirement gates) + Q42 (CCS capex default), flip-first (r#37) — **RUNNING at r#39: flip + four renames + legs 1–2 (`miso-t1f`, `nyiso-t1f` — P10 STOP fired on FC-7) landed; pending `caiso-t1f`, `pjm-t1f`, GOLDEN-3, finding §5; Amendments 1 and 2 below**

```
You are the D60 session of the capacity-expansion track — an ARMING EXECUTION lane. Three
owner rulings, all given 2026-09-05 on measured records (capx ledger §0ah.3 / §3):
  Q40 — ARM `adequacy_accounting_ratio_dated_net` for MISO (D51; FINDING-capx-d51-2026-09-04.md
        §7: 0.8546 → 0.8934, zero DOF; form: `_miso_config` `default_scenario_overrides`, rule 25).
  Q41 — ARM BOTH `nyiso_requirement_forecast_peak` and `nyiso_requirement_vintage_factors` as
        NYISO's forecast default (D52; FINDING-capx-d52-2026-09-04.md §8(1); form: `_nyiso_config`
        `default_scenario_overrides`, rule 25). The NYCA curve stays OFF (P9 failed, D52 + D59).
  Q42 — ARM `ccs_retrofit_capex_co2_scaling` as THE DEFAULT for all six ISOs (D50/D50-R;
        FINDING-capx-d50-2026-09-04.md §8; a posture, no ISO's fitted number; form: the
        dataclass default flips True with a dated (b′-1) line in
        `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, the frozen drop value untouched — exactly
        the D44 pattern) AND schedule its residual re-measure (D50 §6.3: CAISO t1f, NYISO
        t1f, GOLDEN-3 ≈ 1.1 h).
You execute all three FLIP-FIRST so every re-solve lands on the final posture once, you
pre-declare every key, you preserve every prior, and you arm nothing else.

DATA PROFILE: miso, nyiso, caiso, neiso (incremental — widen as each leg starts; the PJM /
ERCOT t1f post-flip bare keys are the D50 arms, no solve).
MODEL ASSIGNMENT: Opus (execution of rulings on pre-declared records; nothing to adjudicate —
a surprise is a STOP, not a decision).
BRANCH: claude/capx-d60-arming-batch — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d44-* §1–§2 (the b′-1 declared-default-flip mechanics: post-flip bare
key == the explicit-True arm key; explicit False keeps its key) · FINDING-capx-d50-2026-09-04.md
§6 IN FULL (the blast-radius census: 153 configs, 7 bare keys, which are already measured,
the 1.1 h residual, the two qualifications) · FINDING-capx-d53-2026-09-05.md §6.1 (the
in-lane arming precedent you copy exactly: override form, the two-key VERDICT_MAP rename, the
`-pre-d53` preservation, the board `t1h_provenance` re-key with prior stamps beneath, the
"every other ISO's key unmoved" test) · FINDING-capx-d51 §7 (the arm form and what the ratio
does to `miso-t1f`'s I7 rows) · FINDING-capx-d52 §8(1) · src/market_sim/config/iso_configs.py
(`_miso_config` already carries `retirement_sector_gate: True` — you ADD the ratio beside it)
· src/market_sim/config/scenarios.py (`_CACHE_KEY_OPTIONAL_FIELDS`, `_DEFAULT_FLIPS`, the three
fields' defaults) · scripts/register_forecast_run.py `VERDICT_MAP` · scripts/run_full_horizon.py
(`reference_config(..., golden_posture=True)`, GOLDEN-3's recipe: results/ff-golden-3 or the
`neiso-t3` registry sidecar's run_config.json) · frontend/data/forecast/ff-verdicts.json +
program-status.json (every bare key's current provenance) · the matrix rows for the three
fields and every shard's cells · CLAUDE.md step-2/§ Capacity Evolution text on
`ccs_retrofit_capex_co2_scaling` ("GATED default off … arming is an owner ruling on the D50
A/B") and model-methodology-spec.md §5.6 — both need the dated amendment (rule 27 spine).

THE WORK, in this order:
0. HYGIENE COMMIT FIRST (routed by the director, §0ah.4): `ruff format` on exactly
   `src/market_sim/model/capacity_evolution/new_entry.py`,
   `scripts/gen_nyiso191_attestation.py`, `tests/curation/test_derive_cc_capacity_reconcile_
   scope.py` — format only, no other change, one commit, blob-verified. Do NOT format
   `capacity_market.py` / `retirements.py` / `runner.py` — D57 owns those this window.
1. PRE-DECLARE (docs/handoffs/PREDECL-capx-d60-<date>.md, pushed before any code): (a) the
   three edits and their form; (b) EVERY bare forecast key before and after, all six ISOs,
   t1h / t1x / t1f / t3, resolved through the harness path at HEAD — the post-flip values
   must equal D50 §6.1's right-hand column for the t1f keys, `c306ddc6…`-successor for
   `miso-t1h` (gate + ratio + CCS-flag: compare with the D53 rider `6ea92547eaa62559`, which
   carries gate + ratio but NOT the flipped CCS default — state the exact relation), and the
   D52 arm key `911371a8cf23d5c3` similarly for `nyiso-t1h`; (c) for each bare key: RENAME
   (byte-identical by construction — the t1h/t1x keys, whose horizons end ≤ 2027 and never
   reach the 2028-gated CCS screen; for `miso-t1h` and `nyiso-t1h` this holds ONLY if the
   committed suffixed leg already carries the ratio / the two gates — say which committed
   bundle each bare key renames from) or RE-SOLVE (`miso-t1f`, `nyiso-t1f`, `caiso-t1f`,
   `neiso-t3` GOLDEN-3; and `ercot/neiso/pjm-t1f` = the D50 arms, rename); (d) the expected
   FC rows per re-solve, from the committed arms' evidence (MISO t1f: the ratio's I7 sign
   from D51 §7 + the D50 MISO leg's null; NYISO t1f: D52's +0.24 % requirement; CAISO t1f:
   D50 P-rows for CAISO, untested — pre-declare from the §1 census; GOLDEN-3: D50's NEISO
   leg says the cap still binds, composition-only — the FC map should not move); (e) STOPs:
   any key ≠ its pre-declared value; any t1h rename whose committed leg is not byte-identical
   on every scored row to what the bare recipe would produce (if in doubt, RE-SOLVE it and say
   so — 12–25 min beats a wrong rename); any FC-3 / FC-1 row moving in a direction the
   committed arm did not show; any keeper / backcast key moving (the plain-backcast coercion
   assertion, ScenarioConfig() and the bare backcast key unmoved, as D53's test asserts).
2. THE FLIP COMMIT: the three edits + the b′-1 line + `validate_parameters.py` + tests
   (D53's override test as the template: every OTHER ISO's forecast key unmoved; ERCOT /
   PJM / CAISO / NEISO carry neither the ratio nor the NYISO gates); CLAUDE.md + spec §5.6 /
   §5.x dated amendments; CHANGELOG; matrix: the three rows' cells re-stamped (MISO ratio K
   on the D51 record; NYISO gates K on the D52 record; CCS capex: ERCOT/NEISO/PJM/MISO
   measured K, CAISO/NYISO K-by-posture with their own t1f evidence appended when the
   re-solve lands — rule 25: no ISO's letter is transferred, the POSTURE is global as Q30's
   was). `check_cache_key_registration.py --base origin/main` green; `check_mechanism_matrix`
   green.
3. RENAMES (zero solve): for each bare key that renames, the D53 §6.1 procedure — VERDICT_MAP
   two-key rename, the prior record preserved at `<key>-pre-d60` (never overwrite a
   preserved baseline that already exists: `-pre-d53`, `-pre-d51`, `-pre-d46` … stay), the
   board's provenance stamps re-keyed with the prior stamps beneath, `check_forecast_
   staleness.py` read before and after.
4. RE-SOLVES, sequential (rule 12; one solve at a time inside this session; `data/clean`
   regenerated once before the first): (i) `miso-t1f` 2026–2030 (~65 min) → the new bare
   `miso-t1f`, prior at `miso-t1f-pre-d60`; (ii) `nyiso-t1f` (~12 min); (iii) `caiso-t1f`
   (~22.6 min); (iv) `neiso-t3` GOLDEN-3 (25 yr, ~33 min, the golden posture per its own
   sidecar; prior at `neiso-t3-pre-d60`; its FC-5/FC-6 dispositions carry per D47's
   attestation rules — a pre-declared follow-up attestation under the Q37 limb). Each:
   `score` → `forecast_verdict --tier` → `register_forecast_run --bundle`, AFTER your final
   rebase of that leg (desk doctrine X-6b: no orphaned `scored_at_sha`; if you rebase after
   scoring, re-score artifact-only before merge). Push each leg as its own commit.
5. FINDING docs/handoffs/FINDING-capx-d60-<date>.md: the pre-declaration graded at full
   magnitude (every key, every rename's byte-identity evidence, every re-solve's FC rows vs
   its committed arm); the board's per-ISO gate rows before/after (state plainly which
   determinations moved, if any — expected: none; the MISO t1f I7 rows are the one place a
   row may move, and D51 §7 said which way); the blast-radius reconciliation against D50 §6.2
   (which of the 25 keys now carry a live re-measure, which stay preserved-only, which are
   unregistered); the governance attestation (rule 27 blob checks on scenarios.py,
   iso_configs.py, CLAUDE.md, the spec, program-status.json, ff-verdicts.json — all ≥300
   lines).

GUARDRAILS: rules 1, 5, 12, 13, 14, 19, 21 (no value changes — the ratio IS D51's 0.8934,
`captured_ref` IS D50's constant), 22 (t1h 2021–2025 / t1f 2026–2030 / t3 2026–2050; nothing
against measured H1-2026), 24, 25, 27, 28 (no new field; cells re-stamped). No keeper / shard
promotion field / `complete` / `final` / freeze touched (D56-R2 owns NYISO's frontier this
window). Nothing beyond the three rulings arms: `locality_capacity_curves` stays OFF (D59),
the NYCA curve stays OFF, PJM's D48 fields and D57's gate stay OFF (D57 is measuring them).

COLLISION: D57 (PJM: `scenarios.py` optional-field ledger APPEND, `capacity_market.py`,
`retirements.py`, `runner.py`, PJM t1h surfaces) — you append to a DIFFERENT dict in
`scenarios.py` (`_DEFAULT_FLIPS`) and to `iso_configs.py`; rebase before every push and keep
D57's lines verbatim. D56-R2 (NYISO keeper shard `frontier` + marker) — disjoint. D58 is held.
You are the only writer on MISO / NYISO / CAISO / NEISO forecast surfaces this window.

EXIT: the hygiene commit; the pre-declaration; the flip commit with docs/matrix/tests; every
bare key renamed or re-solved as pre-declared with priors preserved; the four re-solves
registered; the finding; all blob-verified. Then the director serves the NYISO t3 card.
```

### D60 — Amendment 1 (r#38; the owner's relaunch-protocol answer: the session is STILL RUNNING — this is appended to the live charter, nothing is re-issued)

```
D60 AMENDMENT 1 (director r#38, 2026-09-05; read before your next re-solve):

1. THE FIFTH RE-SOLVE — `pjm-t1f`. Your STOP 1 on the pjm-t1f rename was correct and is now
   resolved: D57 has LANDED (PR #4786) and its in-session owner ruling (Q44) armed the joint PJM
   posture via `_pjm_config` overrides, so PJM forecast surfaces are FREE this window and the
   bare `pjm-t1f` recipe resolves to `09996eca71ee80fd` — re-verify that key through the harness
   path at your HEAD first (D57's overrides + your Q42 flip; if it differs, the difference is
   the whole finding row — state it and use the resolved key). Re-solve `pjm-2026-2030` on the
   bare recipe (~28 min, PJM solo, `--golden-posture` as the D50/D45-R legs), preserve the
   D45-R record at `pjm-t1f-pre-d60`, register as the bare `pjm-t1f`. Pre-declare its FC rows
   from the two committed records it supersedes: the D50 PJM arm (CCS window 3,584.7 → 909.8 MW
   at the OLD posture) and D57's arm A (the clearing price $28.7/kW-yr replacing $0 at the entry
   screen; the gas-steam exits) — the t1f leg is the FIRST solve in which both act together on
   2026–2030, so its FC-1 I7/I12 rows may move; say which way before you run it.
2. ORDER: your remaining legs are miso-t1f (~65), nyiso-t1f (~12), caiso-t1f (~23), pjm-t1f
   (~28), neiso-t3 GOLDEN-3 (~33) — sequential (rule 12). If wall-clock is short, GOLDEN-3 last
   and, if it cannot complete, say so in the finding and the director charters it separately;
   never leave a half-registered golden.
3. THE FINDING gains a §"D57 interaction": the MISO t1f leg carries THREE mechanisms (your
   Addendum A.5) and the PJM t1f leg carries THREE too (Q42 + D48 ×2 + clearing) — each row that
   moves is attributed to one, from the committed single-mechanism records, never by inference.
4. HYGIENE: the ruff reds you were routed (§0ah.4) were formatted by the audit desk's Y-7 lane
   (#4771) — skip step 0; do NOT touch miso-217's two new reds (`offer_curves.py`,
   `test_miso_intermediate_gas_offer_margin.py`) — the owner's MISO track owns them.
5. Everything else in §D60 binds unchanged: STOPs, priors, the X-6b re-stamp, rule 27 blob
   checks, the arming scope (nothing beyond Q40/Q41/Q42 — and Q44 is D57's, already landed).
```

### D60 — Amendment 2 (r#39; the routed P10 STOP resolved under owner ruling Q37 — appended to the live charter, nothing re-issued)

```
D60 AMENDMENT 2 (director r#39, 2026-09-05; read before your next commit):

Your leg-2 STOP was correct and its routing was correct. The decision: the FC-7 CAVEAT on
`nyiso-t1f` is an INSTRUMENT gap, not a model gap, and owner ruling Q37 (r#34; rubric §5 second
limb) exists for exactly this case — "a follow-up lane may author an attestation iff
pre-declared before authoring, attestation row only, artifact-only re-score." The
identification of every field the batch armed is COMMITTED: `nyiso_requirement_forecast_peak`
(NYSRC IRM Study Appendices Table D.2 forecast peak, vintage-gated — D52 §8(1) / DESIGN §1),
`nyiso_requirement_vintage_factors` (adopted IRM × (1 − derate) per capability year, Table D.2
— D52 §8(1)), `adequacy_accounting_ratio_dated_net` (the D31 construction net of the dated
channel, 0.893436 — D51 §1.3, zero DOF), `ccs_retrofit_capex_co2_scaling` (captured_ref =
0.90 × 6.3 × 0.057 = 0.32319 t/MWh, composed of cited constants — D50 §1.2, zero DOF), and
D57's three PJM gates (design §3.7 DOF ledger: zero — every operand the screen's own). So:

1. ADDENDUM D FIRST (docs/handoffs/PREDECL-capx-d60-2026-09-05.md, appended BEFORE any row is
   written): for each of the seven fields, the curated design-decision row you will write —
   field, identification source, rule-13 forward-regeneration statement, rule-21 DOF status
   (zero), citation — and the list of bare keys whose FC-7 the rows will change, with the
   expected before/after (nyiso-t1f CAVEAT → PASS, PROMOTE-WITH-CAVEATS → PROMOTE; miso-t1f:
   state what its FC-7 reads now and after; pjm-t1f / GOLDEN-3: pre-state for when their legs
   land). State plainly that FC-7 is the ONLY row that may move and that any other movement is
   a STOP.
2. WRITE THE ROWS — the curated design-decision registry the FC-7 ledger reads (the same place
   D50's and D52's rows live; the D8/D8-V instrument). Attestation rows only; no run_config, no
   solve, no verdict edit by hand.
3. RE-SCORE ARTIFACT-ONLY: `forecast_verdict.py --tier t1f` on the committed `nyiso-t1f` and
   `miso-t1f` bundles (and `pjm-t1f` / `--tier t3` GOLDEN-3 after their legs land) → register
   in place (same key; the `-pre-d60` priors are NOT touched — they carry their own posture and
   their own ledger). Provenance re-stamped at the sha you re-score at (X-6b).
4. FINDING §5 / a §8 "instrument repair": the before/after per key, the Q37 citation, and the
   statement that the model rows are unmoved. If any non-FC-7 row moves, STOP: that is a model
   effect the rows cannot own — report it, route it, do not register.

Everything else in §D60 and Amendment 1 binds unchanged. The order of your remaining legs
(caiso-t1f, pjm-t1f, GOLDEN-3) is yours; Addendum D may land before or between them, but every
re-score happens AFTER its leg's final rebase.
```

## D60-R — the D60 relaunch: the three remaining re-solves, the Q37 attestation rows, the finding (r#39 amendment 1; relaunch protocol — the D60 session is dead, owner-confirmed) — **NEVER LAUNCHED (no branch, no commit at `c3addecc`); RE-ISSUED as D60-R2 below with a fresh stem — paste D60-R2, not this**

```
You are the D60-R session of the capacity-expansion track — the RELAUNCH of D60 (pack §D60 +
Amendments 1 and 2), whose session died after landing its flip commit, four renames and two of
five re-solves. You start FRESH from the committed record and finish the owed half. Nothing
D60 landed is re-done: the flip (Q40/Q41/Q42) is on main, the four renames are on main with
their `-pre-d60` priors, `miso-t1f` (key `b1a73a087064ffd8`, HOLD) and `nyiso-t1f` (key
`19a9690bb12c8459`, PROMOTE-WITH-CAVEATS on FC-7 alone — the P10 STOP) are registered, and the
D60 finding's §§0–4, 6–7 are written. You OWE: (1) the three remaining re-solves — `caiso-t1f`,
`pjm-t1f`, `neiso-t3` GOLDEN-3; (2) Amendment 2 — the Q37 pre-declared attestation rows and the
artifact-only re-scores that repair FC-7; (3) the finding's §5 and an §8 "instrument repair",
and its close.

DATA PROFILE: caiso, pjm, neiso (incremental — hydrate each before its leg; `data/clean`
regenerated once before the first solve, the D60 discipline).
MODEL ASSIGNMENT: Opus (execution of pre-declared legs; the one adjudication — the STOP — was
made by the director in Amendment 2; a NEW surprise is a STOP, not a decision).
BRANCH: claude/capx-d60r-completion — FRESH off origin/main, rebase before every push.

READ FIRST, IN THIS ORDER: pack §D60 (the charter), §D60 Amendment 1 (the `pjm-t1f` leg) and
Amendment 2 (the Q37 rows) · docs/handoffs/PREDECL-capx-d60-2026-09-05.md IN FULL — §5 (the
class-C re-solve list), §6.3 (`caiso-t1f` expectations, pre-declared from the census), §6.4
(GOLDEN-3: the FC map should not move), Addendum A (§A.1 the corrected `miso-t1f` key; §A.2
the authoritative key table — your three keys are THERE: caiso-t1f `29f8eb372810195f`,
pjm-t1f `09996eca71ee80fd` (Addendum C), neiso-t3 = the GOLDEN-3 recipe's post-flip key —
re-verify every one through the harness path at your HEAD before its leg and STOP on any
difference), Addendum B (the GOLDEN-3 attestation's six assertions, fixed in advance), Addendum
C (the pjm-t1f leg, P21–P25) · docs/handoffs/FINDING-capx-d60-2026-09-05.md (§§0–4, 6–7 as
landed; §5 is your section) · the two landed leg commits (`e7412237` miso-t1f, `091023a3`
nyiso-t1f — the attribution and STOP-reporting style you match) · FINDING-capx-d47-golden3-
attestation-2026-09-04.md (the GOLDEN-3 conventions: preserve-then-overwrite, the FC-5/FC-6
carry-over, the T3 attestation) · FINDING-capx-d57 §8.1 (the PJM posture the pjm-t1f leg now
resolves under) · the D8 / D8-V instrument (where curated design-decision rows live for the
FC-7 ledger; D50's and D52's rows as the template).

THE WORK, in this order:
1. STATE AT START (first commit, zero solve): re-resolve every bare forecast key through the
   harness path at your HEAD and diff against Addendum A §A.2 + Addendum C. Any drift since
   D60's pins is reported before anything runs (D57's posture is already IN those keys; a
   further owner-track merge — e.g. the pending nyiso-192 promotion — touches only backcast
   surfaces and must leave every forecast key unmoved: assert it).
2. ADDENDUM D (Amendment 2 step 1) — pushed BEFORE any row is written and before the first
   solve: the seven curated rows, the keys whose FC-7 they change, expected before/after,
   "FC-7 is the only row that may move" stated.
3. THE THREE RE-SOLVES, sequential (rule 12; one at a time): (i) `caiso-t1f` 2026–2030 on the
   bare recipe (`--golden-posture`, ~23 min; prior at `caiso-t1f-pre-d60`; PREDECL §6.3 graded
   at full magnitude — CAISO carries no committed D50 arm, so its CCS rows are the first
   measurement and the census is your only pre-declaration); (ii) `pjm-t1f` (~28 min; Amendment
   1 / Addendum C: prior at `pjm-t1f-pre-d60`, P21–P25 graded, three mechanisms attributed from
   the D45-R control and the D50 PJM arm — never by inference); (iii) `neiso-t3` GOLDEN-3
   (25 yr, ~33 min / ~3.7 GB; prior at `neiso-t3-pre-d60`; Addendum B's six assertions as the
   attestation; FC-5 dispositions and FC-6 battery carried per D47 — if the FC map moves where
   §6.4 said it would not, that is a STOP: report, do not register as bare). Each leg: `score`
   → `forecast_verdict --tier` → `register_forecast_run --bundle`, AFTER that leg's final rebase
   (X-6b: no orphaned `scored_at_sha`). One commit per leg, blob-verified (ff-verdicts.json and
   program-status.json are ≥300 lines).
4. THE Q37 ROWS + RE-SCORES (Amendment 2 steps 2–4): write the seven rows; re-score
   artifact-only `nyiso-t1f`, `miso-t1f`, and each of your three legs; register in place (same
   keys; `-pre-d60` priors untouched); FC-7 the only row that moves — any other movement is a
   STOP and is routed, not registered.
5. THE FINDING: fill §5 (five legs, each: key pre-declared/realized, wall/RAM, the FC rows
   moved with their mechanism attribution, the pre-declaration graded, HOLD/PROMOTE before and
   after); add §8 "instrument repair" (the Q37 citation, before/after per key, the statement
   that model rows are unmoved); the §"D57 interaction" Amendment 1 asked for; the board's
   per-ISO rows before/after; the blast-radius reconciliation against D50 §6.2; the governance
   attestation with rule-27 blob checks. Close the finding: D60 is COMPLETE when every bare key
   named in Addendum A §A.2 carries a post-D60 `scored_at_sha` and every `-pre-d60` prior exists.

GUARDRAILS: everything in §D60 — rules 1, 5, 12, 13, 14, 19, 21 (no value changes), 22 (t1f
2026–2030, t3 2026–2050; nothing against measured H1-2026), 24, 25, 27, 28. No keeper / shard
promotion field / marker / freeze; no default beyond Q40/Q41/Q42 moves (Q44's PJM posture is
D57's and already landed — you solve under it, you do not touch it); `locality_capacity_curves`
and the NYCA curve stay OFF. STOPs: PREDECL §7 verbatim + Amendment 2's "any non-FC-7 row
moves".

COLLISION: D58 (PJM t1h) and T3-NYISO-GOLDEN are HELD until you land — you are the only writer
on CAISO / PJM / NEISO forecast surfaces and on `ff-verdicts.json` / `program-status.json`
this window. D61 is docs-only. The owner's backcast lanes never touch forecast surfaces; the
pending nyiso-192 promotion (if it merges) moves NYISO's marker and gate-(a) row — rebase
before every push and keep its edits verbatim.

EXIT: three legs registered on their pre-declared keys with priors preserved; Addendum D and
the seven rows; every affected bare key re-scored artifact-only; the finding complete and
closed; all blob-verified. Then the director releases D58 and (marker permitting) the NYISO
golden.
```

## D60-R2 — the D60 relaunch, re-issued (r#39 amendment 2; D60-R never launched — audit ruling R-AK's launch-failure class, re-issued on failure) — **LAUNCHED at r#40 (PR #4824: state-at-start + Addendum D), then SILENT; OWNER RULED DEAD at r#42 am.2 → §D60-R3 below; never paste this one**

```
You are the D60-R2 session of the capacity-expansion track — the RELAUNCH of D60 (pack §D60 +
Amendments 1 and 2). D60's session died after landing its flip commit, four renames and two of
five re-solves; the first relaunch (D60-R) never launched. You start FRESH from the committed
record and finish the owed half. FIRST, before anything else: `git fetch origin --prune` and
check for any `claude/capx-d60r*` branch or any commit mentioning "D60-R" on origin/main
newer than `c3addecc`; if one exists, STOP and report it — a twin may be mid-flight and two
writers on `ff-verdicts.json` is the one collision this program cannot absorb.

Nothing D60 landed is re-done: the flip (Q40/Q41/Q42) is on main, the four renames are on
main with their `-pre-d60` priors, `miso-t1f` (key `b1a73a087064ffd8`, HOLD) and `nyiso-t1f`
(key `19a9690bb12c8459`, PROMOTE-WITH-CAVEATS on FC-7 alone — the P10 STOP) are registered,
and the D60 finding's §§0–4, 6–7 are written. You OWE: (1) the three remaining re-solves —
`caiso-t1f`, `pjm-t1f`, `neiso-t3` GOLDEN-3; (2) Amendment 2 — the Q37 pre-declared
attestation rows and the artifact-only re-scores that repair FC-7; (3) the finding's §5 and
an §8 "instrument repair", and its close.

DATA PROFILE: caiso, pjm, neiso (incremental — hydrate each before its leg; `data/clean`
regenerated once before the first solve, the D60 discipline).
MODEL ASSIGNMENT: Opus (execution of pre-declared legs; the one adjudication — the STOP — was
made by the director in Amendment 2; a NEW surprise is a STOP, not a decision).
BRANCH: claude/capx-d60r2-completion — FRESH off origin/main, rebase before every push.

READ FIRST, IN THIS ORDER: pack §D60 (the charter), §D60 Amendment 1 (the `pjm-t1f` leg) and
Amendment 2 (the Q37 rows) · docs/handoffs/PREDECL-capx-d60-2026-09-05.md IN FULL — §5 (the
class-C re-solve list), §6.3 (`caiso-t1f` expectations, pre-declared from the census), §6.4
(GOLDEN-3: the FC map should not move), Addendum A (§A.1 the corrected `miso-t1f` key; §A.2
the authoritative key table — your three keys are THERE: caiso-t1f `29f8eb372810195f`,
pjm-t1f `09996eca71ee80fd` (Addendum C), neiso-t3 = the GOLDEN-3 recipe's post-flip key —
re-verify every one through the harness path at your HEAD before its leg and STOP on any
difference), Addendum B (the GOLDEN-3 attestation's six assertions, fixed in advance), Addendum
C (the pjm-t1f leg, P21–P25) · docs/handoffs/FINDING-capx-d60-2026-09-05.md (§§0–4, 6–7 as
landed; §5 is your section) · the two landed leg commits (`e7412237` miso-t1f, `091023a3`
nyiso-t1f — the attribution and STOP-reporting style you match) · FINDING-capx-d47-golden3-
attestation-2026-09-04.md (the GOLDEN-3 conventions: preserve-then-overwrite, the FC-5/FC-6
carry-over, the T3 attestation) · FINDING-capx-d57 §8.1 (the PJM posture the pjm-t1f leg now
resolves under) · the D8 / D8-V instrument (where curated design-decision rows live for the
FC-7 ledger; D50's and D52's rows as the template).

THE WORK, in this order:
1. STATE AT START (first commit, zero solve): re-resolve every bare forecast key through the
   harness path at your HEAD and diff against Addendum A §A.2 + Addendum C. Any drift since
   D60's pins is reported before anything runs (D57's posture is already IN those keys; a
   further owner-track merge — e.g. the pending nyiso-192 promotion — touches only backcast
   surfaces and must leave every forecast key unmoved: assert it).
2. ADDENDUM D (Amendment 2 step 1) — pushed BEFORE any row is written and before the first
   solve: the seven curated rows, the keys whose FC-7 they change, expected before/after,
   "FC-7 is the only row that may move" stated.
3. THE THREE RE-SOLVES, sequential (rule 12; one at a time): (i) `caiso-t1f` 2026–2030 on the
   bare recipe (`--golden-posture`, ~23 min; prior at `caiso-t1f-pre-d60`; PREDECL §6.3 graded
   at full magnitude — CAISO carries no committed D50 arm, so its CCS rows are the first
   measurement and the census is your only pre-declaration); (ii) `pjm-t1f` (~28 min; Amendment
   1 / Addendum C: prior at `pjm-t1f-pre-d60`, P21–P25 graded, three mechanisms attributed from
   the D45-R control and the D50 PJM arm — never by inference); (iii) `neiso-t3` GOLDEN-3
   (25 yr, ~33 min / ~3.7 GB; prior at `neiso-t3-pre-d60`; Addendum B's six assertions as the
   attestation; FC-5 dispositions and FC-6 battery carried per D47 — if the FC map moves where
   §6.4 said it would not, that is a STOP: report, do not register as bare). Each leg: `score`
   → `forecast_verdict --tier` → `register_forecast_run --bundle`, AFTER that leg's final rebase
   (X-6b: no orphaned `scored_at_sha`). One commit per leg, blob-verified (ff-verdicts.json and
   program-status.json are ≥300 lines). PUSH EACH LEG AS IT LANDS — a session that dies after
   an unpushed solve loses the solve; a pushed leg is a checkpoint the next relaunch keeps.
4. THE Q37 ROWS + RE-SCORES (Amendment 2 steps 2–4): write the seven rows; re-score
   artifact-only `nyiso-t1f`, `miso-t1f`, and each of your three legs; register in place (same
   keys; `-pre-d60` priors untouched); FC-7 the only row that moves — any other movement is a
   STOP and is routed, not registered.
5. THE FINDING: fill §5 (five legs, each: key pre-declared/realized, wall/RAM, the FC rows
   moved with their mechanism attribution, the pre-declaration graded, HOLD/PROMOTE before and
   after); add §8 "instrument repair" (the Q37 citation, before/after per key, the statement
   that model rows are unmoved); the §"D57 interaction" Amendment 1 asked for; the board's
   per-ISO rows before/after; the blast-radius reconciliation against D50 §6.2; the governance
   attestation with rule-27 blob checks. Close the finding: D60 is COMPLETE when every bare key
   named in Addendum A §A.2 carries a post-D60 `scored_at_sha` and every `-pre-d60` prior exists.

GUARDRAILS: everything in §D60 — rules 1, 5, 12, 13, 14, 19, 21 (no value changes), 22 (t1f
2026–2030, t3 2026–2050; nothing against measured H1-2026), 24, 25, 27, 28. No keeper / shard
promotion field / marker / freeze; no default beyond Q40/Q41/Q42 moves (Q44's PJM posture is
D57's and already landed — you solve under it, you do not touch it); `locality_capacity_curves`
and the NYCA curve stay OFF. STOPs: PREDECL §7 verbatim + Amendment 2's "any non-FC-7 row
moves".

COLLISION: D58 (PJM t1h) and T3-NYISO-GOLDEN are HELD until you land — you are the only writer
on CAISO / PJM / NEISO forecast surfaces and on `ff-verdicts.json` / `program-status.json`
this window. D61 is docs-only. The owner's backcast lanes never touch forecast surfaces; the
pending nyiso-192 promotion (if it merges) moves NYISO's marker and gate-(a) row — rebase
before every push and keep its edits verbatim.

EXIT: three legs registered on their pre-declared keys with priors preserved; Addendum D and
the seven rows; every affected bare key re-scored artifact-only; the finding complete and
closed; all blob-verified. Then the director releases D58 and (marker permitting) the NYISO
golden.
```

## T3-NYISO-GOLDEN — the THIRD §2.1b full-horizon campaign: NYISO BAU 2026–2050 (r#38; owner ruling Q45 on card C-14) — **HELD at r#40: Q46 (#4817) WITHDREW `complete.NYISO`; Amendment 1's precondition fails and Q45's premise has lapsed — do NOT paste until a CALIBRATED NYISO keeper re-enters the marker and the director re-serves the card**

```
You are the T3-NYISO-GOLDEN session of the capacity-expansion track — the program's THIRD
§2.1b full-horizon campaign and NYISO's first, authorized by owner ruling Q45 (capx ledger
§0ai.3 / §3, 2026-09-05, card C-14: "Authorize — dispatch after D60's re-solves land"). NYISO
holds gate legs (a) PASS (`complete` re-declared 2026-09-05 by D56-R, frontier by D56-R2, on
keeper `2026-09-05-nyiso-189-steam-identity`, CALIBRATED), (b) PASS (`nyiso-t1f` PROMOTE),
(c) PASS (`nyiso-t1x` measured); its requirement gates are ARMED (Q41: NYSRC Table D.2 forecast
peak + per-capability-year IRM/derate), the CCS capex posture is armed program-wide (Q42), the
NYCA curve and `locality_capacity_curves` stay OFF (D52/D59 P9). You cut the 25-year golden on
that HEAD, score it on the full rubric, and register it as the bare `nyiso-t3`. You arm nothing.

DATA PROFILE: nyiso
MODEL ASSIGNMENT: Opus (a pre-declared campaign on a settled recipe — audit ruling R-AK; every
discretionary question below returns to the director, never decided here).
BRANCH: claude/capx-t3-nyiso-golden — FRESH off origin/main, rebase before every push.

PRECONDITION (check first; STOP and say so if it fails): `docs/handoffs/FINDING-capx-d60-*.md`
exists on origin/main and the bare `nyiso-t1f` verdict carries a post-D60 `scored_at_sha`. If
D60 has not landed, stop — the director released you on its landing.

READ FIRST: pack §T3-NEISO-GOLDEN and §T3-NEISO-GOLDEN-2 (the recipe you mirror; Q13 / Q25),
FINDING-capx-golden2-* and FINDING-capx-d47-golden3-attestation-2026-09-04.md (the campaign
shape: preserve-then-overwrite, the FC-5 disposition table, the FC-6 battery at the golden's
own vintage, the DOF ledger / FC-7 attestation, `-pre-*` conventions) · docs/forecast-
development-plan-2026-07.md §2.1b (the gate, the rubric FC-1…FC-7) · FINDING-capx-d52 §8(1)
and FINDING-capx-d60 (the NYISO posture you run: which fields the bare `nyiso-t1f` resolves ON)
· FINDING-capx-d59 §0/§8 (the NYC census object: the model's NYC ICAP census sits +0.7–0.8 GW
above the Gold Book — a KNOWN long position your golden will carry; state it in the finding,
never repair it here) · FINDING-capx-d25 (FC-5 dispositions: divergence is not failure,
UNEXPLAINED divergence is) · D21/D26/D35 (the FC-6 battery + P1–P3 pairs; `carbon_price_delta`)
· scripts/run_full_horizon.py (`reference_config(..., golden_posture=True)`), scripts/
register_forecast_run.py, scripts/forecast_verdict.py · frontend/data/forecast/ff-verdicts.json
(no `nyiso-t3` exists — this is a first registration, no prior to preserve) · the NYISO matrix
shard.

THE WORK:
1. PRE-DECLARE (docs/handoffs/PREDECL-capx-t3-nyiso-<date>.md, before any solve): the recipe
   (NYISO BAU 2026–2050, the bare posture at HEAD resolved through the harness path — list every
   armed field and the cache key), expected wall/RAM from the NYISO t1f rate (~12 min / 5 yr →
   ~1 h / 25 yr; the NEISO goldens ran 33–35 min / 3.5–3.7 GB), the FC-5 corridor rows NYISO can
   score (which benchmark sources exist for NYISO in the corridor datatype — say which are
   missing), the FC-6 battery plan (the Tier-1 ladder rungs live at NYISO + paired P1–P3 at this
   golden's vintage; price the battery before running it), and the expected FC map from
   `nyiso-t1f`'s record (PROMOTE, caveats [] — a 25-year run may open rows t1f cannot see:
   storage entry timing (D36), CCS from 2028 (D50), the RPS/ACP ceiling (T16-A)); the STOPs:
   wall > 2× estimate or RSS > 12 GB; any keeper / backcast key moving; any field resolving
   differently from the pre-declared posture.
2. THE GOLDEN: one 25-year solve, NYISO solo (rule 12), `--golden-posture`, diagnostics on;
   `score` → the FC-5 disposition table authored (every corridor row IN CORRIDOR / EXPLAINED /
   UNEXPLAINED with its reason — 0 UNEXPLAINED is a claim you audit adversarially, as D25 did) →
   the FC-6 battery + pairs solved and scored → `forecast_verdict --tier t3` → register as the
   bare `nyiso-t3` (first registration). Score and register AFTER your final rebase (desk
   doctrine X-6b: no orphaned `scored_at_sha`).
3. FC-7: the DOF ledger built from the run's own `run_config.json` (0 UNIDENTIFIED is the
   target; every armed field has a curated design-decision row — D50/D52's rows exist; verify
   D53/D51/D57 rows are NOT in NYISO's ledger since they are not armed for NYISO).
4. FINDING docs/handoffs/FINDING-capx-t3-nyiso-<date>.md: the determination and full FC map at
   full magnitude, the trajectory (fuel mix, retirements, entry, storage, CO2, REC dual, capacity
   price per year — the D29 grain), the position path (NYCA and, reported-only, the NYC/LI
   positions the D59 ledger block emits), the pre-declaration graded, the routed objects (the NYC
   census; anything the golden opens), the matrix stamp (NYISO shard keeper/gates header; no
   verdict letter moves — nothing is tested here), governance attestation (rule 22: 2026–2050,
   no measured 2026 actual touched; rule 27 blob checks).

GUARDRAILS: rules 5, 7, 8, 12, 13, 21 (no parameter), 22, 24, 27, 28d. Arm nothing; touch no
keeper / shard promotion field / marker / freeze; no backcast file. NEISO's goldens and every
other ISO's forecast key untouched.

COLLISION: D58 (PJM) and D61 (docs) are disjoint; D60 has landed by your precondition. The
owner's NYISO backcast lane (nyiso-19x) owns the keeper shard; you stamp the matrix header only.

EXIT: `nyiso-t3` registered with its FC-5 table, FC-6 battery and FC-7 ledger; the finding; the
board's NYISO t3 row; all blob-verified. The director serves any arming or repair question.
```

### T3-NYISO-GOLDEN — Amendment 1 (r#39; the marker is a START precondition of Q45)

```
T3-NYISO-GOLDEN AMENDMENT 1 (director r#39, 2026-09-05; binds with the charter above):

Q45 authorized this campaign on the premise that NYISO holds gate leg (a) — a designated
full-span keeper AND an entry in `calibration-complete.json`'s `complete` block. At r#39 an
UNMERGED branch (`claude/nyiso-192-frontier-adjudication-mo2nrq`) carries an in-lane owner
ruling that promotes a NOT-YET keeper (`2026-09-05-nyiso-192-astoria-panel`) and, under the Q5
uniform rule, WITHDRAWS `complete.NYISO` and the Q39 frontier. If that has merged when you
start, Q45's premise no longer holds.

PRECONDITION 2 (checked at start, after precondition 1): `frontend/data/backcast/
calibration-complete.json` `complete.NYISO` EXISTS and names the live keeper in
`keepers/NYISO.json`; `program-status.json` `isos.NYISO.gate.a_keeper_marker.status` reads
`pass`. If either fails: STOP, write nothing but a three-line note in your session output
(the marker state, the keeper id, the sha you read at), and route to the director. A §2.1b
campaign on an ISO without the marker is not something Q45 authorized, and re-authorization is
a NEW owner card the director serves — never an assumption this lane makes.

If both preconditions hold, the charter runs unchanged. Note for the finding either way: the
NYISO keeper this golden is cut against, by id, and the posture (armed fields) resolved at HEAD.
```

## D64 — the D50 FOURTH SEAM: the CCS retrofit fixed-cost legs per captured tonne (r#40; zero-solve Phase 0; D50 §8 Disclosure 1) — **LANDED at r#41 (PR #4847 `1adb0d3c`): both legs TPC-fractions → scale with `k`; PJM 2029 residual closes at zero solves; `ccs_retrofit_vom_adder` 8.0 UNCITED (ATB 2.95) → BUILD: §D65 (Act A) + card C-15/Q47 (Act B)**

```
You are the D64 session of the capacity-expansion track — a Phase-0 lane, zero solves, docs
only. D49 named three construction seams in the CCS retrofit screen and D50 built them (capex
∝ captured CO2 against the ATB reference host; CHP hosts excluded; the p55470 flag), and the
owner armed the repaired posture as the default (Q42, executed by D60). D50-R's finding §8
Disclosure 1 states the seam it did NOT close, at the gate: the retrofit's ΔFOM
(`fixed_om_gas_cc_ccs` − the host's FOM, $35,000/MW-yr on the D41 basis) and the capture VOM
adder stay REFERENCE-HOST-SIZED per MW, so they dilute per captured tonne as the host's
emission rate rises — the clearing threshold moves (`er ≥ ~0.46` → `~0.58–0.63` at carbon 0)
rather than vanishing, and D50's PJM 2029 residual (909.8 MW, two tranches at 1.02–1.03× the
scaled bar) sits on exactly that dilution. You adjudicate the fourth seam the way D49 §1
adjudicated the first three: what the ATB / NETL basis says these two legs scale with, what a
faithful construction is, zero DOF, and what it would do to the committed D50 / D60 ledgers —
without a solve, without a coefficient.

DATA PROFILE: code
MODEL ASSIGNMENT: Fable (a construction adjudication; the arming consequence is a re-key of
every forecast bare key under the (b′-1) pattern if it is ever armed).
BRANCH: claude/capx-d64-ccs-fixedcost-seam — FRESH off origin/main, rebase before every push.

READ FIRST: FINDING-capx-d50-2026-09-04.md §1 (the census), §4 (PJM: the 2029 converters at
1.023 / 1.030 of the bar), §8 Disclosure 1 IN FULL · FINDING-capx-d49-2026-09-04.md §1.4–§1.5
(the three seams and how each was sized to the reference host) · FINDING-capx-d41-* (the ATB
basis, dollar-year, the two fixed-cost legs' re-identification — the D30 defect and its repair)
· FINDING-capx-d30-* (the original 45Q-pace question) · src/market_sim/model/capacity_evolution/
ccs.py::apply_ccs_retrofit (where ΔFOM and the VOM adder enter the margin; how `captured_ref`
scales capex and does NOT scale these two) · the constants that carry `fixed_om_gas_cc_ccs`,
the capture VOM adder and `NEW_ENTRY_COSTS["gas_cc"]` (docs/parameter-citations.md rows) · the
ATB 2024 gas-CC-CCS entries and NETL's capture-plant cost basis (fetch, sha256, cite — the
question is whether FOM and VOM of a capture island are published per kW or per tonne, and
what the reference host's captured tonnage was when the per-kW number was formed) · the D60
`miso-t1f` / `nyiso-t1f` ledgers and (when landed) D60-R2's `pjm-t1f` / `caiso-t1f` / GOLDEN-3
ledgers (the post-flip CCS rows you re-screen under the fourth-seam construction, zero-solve,
exactly as D49 §1.2 reconstructed 14 rows and D50 §1 ran the census).

THE WORK (docs/handoffs/FINDING-capx-d64-<date>.md, one document, zero solves):
1. THE BASIS: for each of the two legs, what the source publishes it as (per kW-yr of host? per
   tonne captured? per MWh of host output?), at what reference host (heat rate, emission rate,
   capture rate), and therefore what it SCALES WITH under rule 5 / rule 13 when the host
   differs from the reference. State the construction that follows — the same shape D50 used
   for capex (`× captured_t_per_mwh / captured_ref`), or a different one if the source says so
   — with zero free parameters (every factor a cited constant).
2. THE ZERO-SOLVE RE-SCREEN: on the committed post-Q42 ledgers (every ISO whose CCS rows exist:
   NEISO under RGGI — the cap-bound case; PJM 2029's two converters; ERCOT/MISO's zero), the
   retrofit margin per candidate row under the fourth-seam construction beside the shipped
   one — how many rows change sign, in which direction (rule 14: a faithful per-tonne sizing
   makes retrofits HARDER on high-`er` hosts and EASIER on low-`er` hosts — state the expected
   asymmetry before computing it), and whether the PJM 2029 residual closes. The NEISO cap
   question (does a per-tonne ΔFOM unbind the 3 GW/yr cap under RGGI, or is the avoided-carbon
   leg still per-tonne-dominant?) answered from the arithmetic.
3. THE BLAST RADIUS, stated not measured: which forecast bare keys a default flip would re-key
   ((b′-1): every key, as D50 §6.1 showed) and which ledgers' behaviour can move (only horizons
   reaching 2028 with CCS rows — reuse D50 §6.2's census structure, updated for the D60 keys).
4. THE BUILD CHARTER (for the director to issue as D65 if warranted): the field (repo
   convention; default-off; one row + six cells), the seam in `ccs.py`, the tests, the A/B plan
   (a t1f arm on the ISO where the re-screen moves the most rows, ~12–28 min; GOLDEN-3 only if
   NEISO's cap answer says it can move), the STOPs (any row moving in the rule-14-wrong
   direction; any capex-seam row moving — the fourth seam must leave D50's three untouched).
   If the basis says the legs are ALREADY per-tonne-correct at the reference host and the
   dilution is a second-order effect below the cap-packing unit, say so — a "no build" is a
   valid Phase-0 result and closes the disclosure.

GUARDRAILS: zero solves; no ScenarioConfig field; no constant changed; rules 5, 13, 14, 21, 25
(a posture, no ISO's fitted number); rule 27 does not bind (docs only). COLLISION: none — docs
only; you read D60-R2's ledgers as they land (rebase before every push) and never write a
forecast surface.

EXIT: the finding with the basis, the construction, the zero-solve re-screen, the blast radius,
and the D65 build charter draft (or the "no build" closure); pushed.
```

## D61 — the PJM CT / ST / oil E&AS operand: Phase 0, zero-solve (r#38; D57 §4's named successor) — **LANDED at r#41 (PR #4848 `27a2996e`): the operand is NOT the object — the going-forward BAR (published gross ACR) + the 2024/25 census are → §D62 issued; D66/D67 named; card C-16/Q48 (co-opt arming)**

```
You are the D61 session of the capacity-expansion track — a Phase-0 ADJUDICATION lane, zero
solves. D57 (FINDING-capx-d57-2026-09-05.md §3–§4, §8) built the PJM clearing half and, armed
by owner ruling Q44, it now prices PJM's capacity market at the auction's own cleared quantity
(within 0.5–2.8 pts of the published BRA) — but at 1.5–5.7× the published price, because the
sell offers of the gas-CT (404 units / 24.2 GW firm), gas-ST (115 / 8.8 GW) and oil (421 /
3.7 GW) fleets carry EXACTLY ZERO E&AS margin in the hindcast prices and so offer at their full
avoidable-cost bars — a 37 GW plateau at $61–103/MW-day where the published price is $29–50. D57
measured that an E&AS margin of ≥ 3.8 / 18.0 / 8.6 $/kW-yr per CT / ST / oil unit (2022/23)
would put those offers AT the published price, and named the operand as the successor. You
adjudicate the operand: what the real market pays those fleets that the model's hindcast price
does not, where in the model that revenue belongs, and how a faithful representation would be
built with zero free parameters. You do not build, you do not tune, and a coefficient that
lands the price is REFUSED (rule 21; D57 §4's own line).

DATA PROFILE: pjm (start `code`; widen to pjm only if a ledger read needs the raw corpora)
MODEL ASSIGNMENT: Fable (a mechanism adjudication with the largest downstream consequence in
the PJM chain).
BRANCH: claude/capx-d61-pjm-eas-operand — FRESH off origin/main, rebase before every push.

READ FIRST: D57 §3.3–§3.5 and §4 IN FULL (the operand measurement and the "≥ X $/kW-yr" table;
the arm ledgers' `capacity_clearing` block carries the whole sell-offer stack — your census
reads off it) · DESIGN-capx-d54 §3.1 (the operands), §4.8 (the one-year vs three-year E&AS
offset — the one admissible alternative operand, named) · FINDING-capx-d12-* and the pjm-164
finding (the C3c program's Q1: PJM's reserve-dual channel is REAL — binds on opportunity cost,
$187.90 max dual, zero shortfall hours) · FINDING-capx-d4i3-* / d4m (the ERCOT scarcity-slack /
net-revenue half, the D12 scarcity-consistent basis) · model-methodology-spec.md §5.2 (the
screen's attainable inframarginal margin: `Σ_t max(0, price − full variable cost, reserve price)
× pmax × availability`) and the `screen_reserve_value_enabled` clause · retirements.py (where
the E&AS margin the screen and the clearing consume is computed; which price series — energy
λ, reserve duals, ORDC adder — it sees for PJM) · the PJM State of the Market reports (Monitoring
Analytics) — the Net Revenue tables for a new CT / CC and, where published, the historical
net-revenue analysis by unit type; the Ancillary Services and Uplift chapters (fetch, sha256,
cite: VALIDATION OBSERVABLES, never inputs) · the PJM hindcast price ledgers (`pjm-t1h` arms:
zonal λ, reserve prices if any) · the matrix `capacity_market_clearing`, `screen_reserve_value`,
`ercot_thermal_as_endogenous` rows and the PJM cells.

THE WORK (docs/handoffs/FINDING-capx-d61-<date>.md, one document, zero solves):
1. THE CENSUS OF DENIED REVENUE: from the committed D57 arm ledgers, per fuel class (CT / ST /
   oil) and per DY, the offer stack's E&AS margin distribution (how many units at exactly zero;
   the bar each offers at) beside the published SOM net-revenue evidence for the same classes
   and years (energy, reserves — synchronized / non-synchronized / secondary — regulation,
   black start, reactive, uplift; $/MW-yr). State which streams the hindcast price CAN carry
   (energy λ is there; are PJM reserve duals? — pjm-164 says the channel is real in the model —
   is it wired into the screen's `reserve price` term for PJM, and does `screen_reserve_value_
   enabled` reach the clearing's offer?) and which it structurally cannot (regulation, black
   start, reactive, uplift — out-of-market or non-LP settlements).
2. THE HOME OF THE OPERAND, adjudicated (rule 19 — one mechanism per phenomenon): (a) the
   reserve co-opt channel (D12's scarcity-consistent basis; the ERCOT `ercot_thermal_as_
   endogenous` form; PJM's own reserve market design — SR/NSR/30-min, the ORDC after 2022) —
   does a faithful PJM reserve co-opt produce the missing margin for CTs at the published
   scale? size it from the ledgers and the SOM without a solve where possible; (b) the
   non-market streams (regulation, black start, reactive, uplift) — a published per-unit or
   per-class revenue that regenerates forward (rule 13 test: could it be produced for 2035 from
   forward drivers? a tariff-based reactive payment yes; a historical uplift average no — say
   which passes); (c) the three-year E&AS offset (design §4.8) — what it changes and why it is
   not the operand; (d) what the operand would do INSIDE the D57 clearing: the price ratio it
   moves toward 1× WITHOUT a coefficient, and the composition (gas-steam exits 9.5 → ? GW;
   coal retained) — derived from the offer stack arithmetic, not solved.
3. RULE 13 / 14 / 21 DISCIPLINE, stated: every candidate stream is a published market-design
   or tariff quantity or a co-optimized LP dual; none is identified from the price residual;
   the falsifier for the eventual build (a mechanism that lands the published price only via a
   fitted scalar is refused; a faithful operand that OVER-shoots — price ratio < 1 — is a
   finding, not a failure).
4. THE BUILD CHARTER (for the director to issue as D62): the mechanism, the field(s), the seam
   (where the operand enters the screen AND the clearing offer — one object, design §4.8's
   identity), the data intake if any (SOM tables → the data contract), the A/B plan on
   `pjm-t1h` (the Q44 posture is the control now), the expected sign per DY, the STOPs. If
   Phase 0 finds the operand's home is the existing reserve co-opt already armed for ERCOT,
   say so and the build charter is a PJM arming of an existing mechanism (rule 25: PJM's own
   parameters from PJM's own reserve market data).

GUARDRAILS: zero solves; no ScenarioConfig field; no parameter value proposed as a number to
fit; rules 13, 14, 19, 21, 25; the SOM figures are observables. Rule 27 does not bind (docs
only). COLLISION: none — docs only; D58 / D60 / T3-NYISO are solve lanes on other surfaces.

EXIT: the finding with the census, the adjudicated home, the arithmetic of what the operand
would do to D57's price ratio and composition, and the D62 build charter draft; pushed.
```

## D62 — the PJM going-forward BAR: published default gross ACR + the reactive leg, BUILD + A/B (r#41; D61 §4 executed) — **ISSUED r#41; NOT LAUNCHED at r#42; RE-EMITTED AND DISPATCHED at r#43** with FOUR marked `[r#43]` changes and nothing else (D60-R2 → D60-R3 in both hold clauses; D65 recorded LANDED with D65-B named as the future writer of the same regions; the two director-verified G-DRIFT facts marked re-verify-don't-assume; **the D65 hunk-level lesson made binding on `retirements.py`**, D62's own seam-1 file) plus rule 29(c) stated explicitly. **This section IS the issued text.** — **DISPATCHED AND LIVE at r#44 (PRs #4949/#4958/#4962):** PRECOMMIT before the first line of build; mechanism built to charter (one `{iso: bool}` gate, default-off, no scalar); **Phase 0 PASS to 0.0000 $/MW-day and 0.0000 pt on all four DYs; SCREEN GATE PASS on all five legs on the pre-named DY 2022/23 — ratio 1.522 → 0.936×, position −0.477 → +0.267 pt, both inside the declared bands, landing on its own pre-solve arithmetic TO THE CENT; the footprint IS the arithmetic class by class (nuclear moves zero both sides); reactive enters once at 3.6e-16**; two disclosures against interest. OWED: §§5–9, the full T1-H window; registration correctly withheld behind D60-R3. — **LANDED IN FULL at r#45 and it REFUSES ITS OWN ARM: §8 DO-NOT-ARM on its own fired STOP 5, FC-3 worse (`retire.total_gw` 18.702 → 20.144 vs 15.062 actual; recall 0.60 → 0.55) and 4.137 GW of oil over-exit at 6.7× actual — while ESTABLISHING the published ACR as the right operand (price within 6.4 % of market, position inside a quarter-point, ZERO free parameters, FC-2 `gas_cc` FAIL → PASS). The STOP is SELF-EXECUTING: no card served. Its narrower partition alternative (arm only the classes PJM publishes a class default for) is real but sequenced BEHIND D66 and the requirement-operand lane, per D62 §9. Never re-paste**

```
You are capx lane D62 for the market-simulator repo — the BUILD + A/B of the object D61 relocated
the PJM clearing-price ratio to. Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md
§D62 and docs/handoffs/FINDING-capx-d61-2026-09-05.md §4 (the construction, the vintage rule, the
pre-declared signs and STOPs — read it whole first, then §2d for the arithmetic you must reproduce).
Director ledger: docs/handoffs/capx-director-ledger-2026-08.md §0al and §0an (r#43, this dispatch).
This charter was issued at r#41 and never launched; it is re-issued UNCHANGED except for the four
lines marked [r#43] below. You start FRESH from the committed charter (relaunch protocol).
DATA PROFILE: pjm
MODEL: Opus (pre-declared execution; rule 27 core scope is permitted for Opus)
BRANCH (suggested; the director grades by content): claude/capx-d62-pjm-acr-bar
Start: git fetch origin main && git checkout -b <branch> origin/main; hydrate: python3 scripts/hydrate_data.py --profile pjm

WHAT D61 FOUND (do not re-adjudicate): the CT/ST/oil E&AS operand is NOT the object — the SOM
medians are $2–18/kW-yr, mostly uplift/reactive, and adding them at the model's bars moves the D57
price ratio the WRONG way (1.52× → 1.86×). What moves the ratio toward 1× with ZERO coefficients is
the going-forward BAR: PJM's own published default gross ACR (Manual 18 §5.4.8.4(B), already intaken
at data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv, two vintage columns) in place of the
ATB-FOM proxy — 1.52 → 1.06×, 2.43 → 1.56× alone. In 2024/25–2025/26 every offer already clears; the
residual there is the supply CENSUS (D66, not yours).

MECHANISM (one object, two seams — rule 19 [R-ONE-MECH]):
 1. Field: ONE per-ISO gate in the {iso: bool} form the clearing half uses (D57 pattern), e.g.
    `capacity_going_forward_bar_published_by_iso: dict[str, bool] | None = None`, default None.
    NO scalar field — the published values are DATA (pjm.csv). Register it in the cache-key
    optional-fields table with its default so the off path is key-neutral; CLI on run_full_horizon.py
    (+ the --no- form); recorded in run_config.json. NOT armed in this lane — no _pjm_config
    override; arming is a later owner card.
 2. Seam 1 — THE BAR (retirements.py::apply_economic_retirements, the going_forward_cost line):
    a `resolve_going_forward_bar(iso, fuel_class, delivery_year)` that returns the published class
    value on nameplate ($/MW-day × 365 → $/kW-yr) when the gate is on for that ISO, else the ATB path
    UNCHANGED. Because the clearing's offer_g = max(0, GFC_g − EAS_g)/(A_g × 365) reads the SAME
    going_forward_cost, offer and exit stay ONE object (design §3.5 identity). Under the published bar
    `retirement_fom_multiplier_coal` does NOT apply (the published number is already the avoidable
    cost "assuming the unit would otherwise retire", §5.4.4) — stated in a comment, not tuned.
 3. Seam 2 — REACTIVE: the tariff's reactive component ($2,199/MW-yr, PJM's E&AS-offset input) enters
    net_revenue BEFORE the capacity leg, once, as pmax × reactive_per_mw_yr for every thermal unit —
    so the offer inherits it exactly as the screen does. The SOLE out-of-market credit: no uplift, no
    AS annual rate (rule 19).
 4. VINTAGE RULE, fixed here before any solve: DY ≤ 2025/26 reads the "through 2025/26" column
    (2022/23 $, nameplate); DY ≥ 2026/27 the second column; classes "n/a" in the first column (steam
    oil & gas) read the first published value, with that fact written into the DOF-ledger row. YOU
    MAY NOT pick between columns by result (rule 21 — the failure mode D61 §3 names).
 5. Data intake: pjm.csv is in place; add the reactive-component row(s) with source doc + page via
    the data-intake skill; extend the capacity_market/avoidable-cost-rate schema if
    cost_component=reactive_offset is new; tmp-CLEAN_DIR test.
 6. Tests (pre-solve): off path byte-identical + cache-neutral (bare keys unmoved with the field
    absent and explicitly None/False); resolver returns the ATB path for every non-armed ISO; the
    vintage rule asserted from pjm.csv; offer == screen bar identity on a toy stack; reactive enters
    once (no double count with the design's EAS_g).
 7. Matrix (rule 28c): one base row in docs/codebase-site/data/mechanism-matrix.js + a cell line in
    all six shards (U/U for the five others; PJM cell stamped from your result), LAST commit, one
    appended line per shard; check_mechanism_matrix.py green.

PHASE 0 (zero LP, a STOP gate): reproduce S0 (committed clearing) and S6 (published bar) of
docs/handoffs/d61/reclear-2026-09-05.py THROUGH THE CODE PATH — the new resolver feeding
clear_capacity_supply_stack — to 0.000 $/MW-day and 0.000 pt on the committed D57 arm-A ledgers
(results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/). Mismatch = STOP.

RULE 29 [R-SCREEN] — NO CONTROL SOLVE (clause b): the control is the committed bare `pjm-t1h`
(`f0e050e820c1159a`, D57 arm A). FIRST run G-DRIFT: `git diff <its git_sha> HEAD -- src/market_sim
scripts/run_full_horizon.py scripts/lib` and classify EVERY solve-path hunk INERT-with-reason or
LIVE in the PRECOMMIT before the arm is solved — the only thing that earns a control solve.
[r#43] Two facts the director verified at pin `04e6906d`, to be re-verified by you, not assumed:
D58's PJM sector-gate arming has NOT landed (bare `pjm-t1h` is unchanged), and `src/market_sim/` has
ZERO commits since `d66d5e6b`. D65 Act A HAS landed (`ccs.py` + a default-off scenarios.py field) —
classify its hunks explicitly. And note D65's own G-DRIFT was WRONG because it classified
`retirements.py` at FILE level: an ungated change to an EXISTING helper (D55's `_floor_retention_merit`)
was missed and the arm caught it hours later. `retirements.py` is YOUR seam-1 file. Classify it HUNK
BY HUNK or your control is not valid.
SCREEN YEAR = DY 2022/23 (the year the bar's footprint is largest: every CT/ST/oil offer
on the bar plateau, coal's 2.0× gap widest — named here, not chosen by residual); structural STOP
gate only (direction and order of magnitude per §2d, footprint confined to the bar rows, offer==exit
identity holds, no non-target load-bearing criterion flips). Then the full T1-H window
(2021–2025 realized, the D57 recipe) as ONE bundle; register the arm under a suffixed key with its
`-pre-d62` prior preserved.

PRE-DECLARED SIGNS (write them in the PRECOMMIT verbatim, grade them at full magnitude): 2022/23 ratio
1.52 → ≈1.06 (0.87–1.06), position −0.48 → +0.1 to +0.3 pt, coal uncleared 5.4 → ≤ 0.2 GW, steam 8.8 GW
UNCHANGED, oil 3.7 GW uncleared unless reactive+energy clears it; 2023/24 2.43 → ≈1.56 (1.28–1.56),
position −0.98 → −0.3 to 0; 2024/25 5.73 → 5.04 then FROZEN (all offers clear); 2025/26 unchanged.
FC-3: economic coal exits UP from 0.44 GW, gas-steam 9.5 GW unchanged, gas-CC 2023 entry below +4 GW,
retire.total_gw toward 15.06 actual; determination expected to STAY HOLD.

STOPs (kill the arm, never promote it): Phase 0 mismatch · bare `pjm-t1h` key moved by THIS lane ·
any other ISO's key moved · a residual-selected column or convention (rule 21) · the 2024/25 price
moving · the price landed through any scalar not in pjm.csv · wall/RSS beyond D57's 14 min / 9.3 GB.

COLLISION CARE: retirements.py beside D57's settlement hunk and D53's sector-gate hunk — rebase
before every push. [r#43] D65 has LANDED (ccs.py + the D50 neighbourhood of scenarios.py); D65-B will
re-write those same two regions AFTER D60-R3 — put your field OUTSIDE the D50 block, outside
SCN-WS1a's D34-guard region and outside SCN-WS2a/2b's federal_ces_* block (scenario-desk-ledger-
2026-09.md collision register). [r#43] NOBODY but D60-R3 — dispatched CONCURRENTLY with you — writes
frontend/data/forecast/program-status.json or ff-verdicts.json this window: build, test, Phase 0,
screen and full-window solves are yours now; REGISTRATION + the artifact-only re-score wait until
D60-R3's finding has merged (`git log origin/main --grep=D60-R3`) — if it has not by the time your
solves are done, push everything else as a CHECKPOINT and say exactly what is owed. Score and
register AFTER the final rebase; a rebase after scoring re-stamps scored_at_sha by an artifact-only
re-score before merge. Rule 22: no out-of-training solve (2021–2025 realized hindcast only; forecast
mode). Rule 27: edit locally, push exact bytes, blob-verify every ≥300-line file after push. Rule 28:
row + six cells in this PR. Rule 25: PJM's data and PJM's cell only. Rule 29(c): any screen or control
bundle is DELETED from results/calibration before your PR merges — the finding carries every number.

EXIT: FINDING-capx-d62-<date>.md (Phase 0 reproduction, G-DRIFT table, screen gate table, the
full-window A/B at full magnitude vs the pre-declared signs, FC-3/FC-2 rows, a §8 recommendation
ARM / DO-NOT-ARM with the owner card's text drafted, and what the census D66 and the steam
convention D67 still own); tests green; matrix green; pushed. Nothing arms in this lane.
```

## D65 — the CCS fourth seam, ACT A: the fixed-cost shape field, BUILD + A/B (r#41; D64 §4 Act A executed; Act B awaits card C-15 / Q47) — **ISSUED r#41** — **LANDED IN FULL at r#42 am.1 (PRs #4890/#4891/#4895/#4898): the lane's G-DRIFT was wrong and the arm caught a material HEAD drift (→ D71); A1 vs a same-HEAD control: the seam RE-ORDERS, not re-selects (34 rows either way); STOPs 5/5 not fired; §8 ARM ONLY COUPLED WITH ACT B → card C-15/Q47 amended to decide both. OWED: registration + re-score after D60-R2/-R3. Never re-paste**

```
You are capx lane D65 for the market-simulator repo — the BUILD + A/B of D64's Act A: the gated
field that makes the CCS retrofit's ΔFOM and capture-VOM legs scale with the capture island (k =
captured / captured_ref) exactly as D50 already scales its capex. Binding charter: docs/handoffs/
capx-director-prompt-pack-2026-08.md §D65 (this section) and docs/handoffs/FINDING-capx-d64-
2026-09-05.md §4 (field, seam, tests, A/B, STOPs — read it whole first; §1.2 for the basis, §2.3
for the committed converters you will re-rank). Director ledger: capx-director-ledger-2026-08.md §0al.
DATA PROFILE: neiso
MODEL: Opus (pre-declared execution; rule 27 core scope permitted for Opus)
BRANCH (suggested; graded by content): claude/capx-d65-ccs-fourth-seam
Start: git fetch origin main && git checkout -b <branch> origin/main; hydrate --profile neiso

SCOPE — ACT A ONLY. Act B (re-identifying `ccs_retrofit_vom_adder` 8.0 → 2.95 $/MWh 2026$) is a
VALUE change that re-keys every bare key unconditionally and is owner card C-15 / Q47 — DO NOT change
the constant, do not widen the ATB extract for it, do not solve an A2 arm. If §3 of the ledger shows
Q47 RULED (A) when you start, STOP and tell the director: the charter is re-cut, not improvised.

THE FIELD AND THE SEAM (D64 §4.2, zero DOF):
 1. `ccs_retrofit_fixed_cost_co2_scaling: bool = False` in scenarios.py BESIDE the D50 field
    `ccs_retrofit_capex_co2_scaling`; validator: True REQUIRES the D50 field (no k without seam 1).
    Registered in _CACHE_KEY_OPTIONAL_FIELDS + _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["…"] = "False";
    CLI --ccs-retrofit-fixed-cost-co2-scaling / --no- on run_full_horizon.py; in run_config.json.
 2. ccs.py::apply_ccs_retrofit: delta_fom_per_mw_yr becomes the REFERENCE value computed once;
    inside the loop delta_fom = delta_fom_ref × (capex_scale if scale_fixed else 1.0); mc_post uses
    vom_adder × (capex_scale if scale_fixed else 1.0); the conversion applies the SAME scaled adder to
    gen.vom (the dispatch VOM of the converted unit must be the VOM the screen priced); the log gains
    fixed_cost_scale and vom_adder_per_mwh (delta_fom_per_mw_yr now per host). Off path never enters
    the branch — byte-identical by construction.
 3. The converted unit's LATER retirement FOM: director ruling r#41 = D64 option (i) DISCLOSE AND
    DEFER (one seam per lane); write the disclosure into the finding and the ccs.py comment; option
    (ii) (Generator.fom_adder_per_kw_yr) is a routed successor, not yours.
 4. Matrix (rule 28c): base row `ccs_retrofit_fixed_cost_co2_scaling` in mechanism-matrix.js + a cell
    in all six shards (U/U; NEISO stamped from your A1), LAST commit, one appended line per shard;
    check_mechanism_matrix.py green. Act B's note in the existing ccs_retrofit_screen row is C-15's.

TESTS (all pre-solve; tests/unit/model/test_ccs_retrofit.py conventions): off path byte-identical +
cache-neutral (bare keys unmoved with the field absent AND explicitly False — the D50
test_off_is_byte_identical_and_cache_neutral shape); REFERENCE-HOST INVARIANCE (a k = 1 host: er =
6.3 × 0.057, capture 0.9 → identical uplift_window, payback_years, log rows on and off); PER-TONNE
INVARIANCE at carbon 0 (two hosts, equal hr, er ratio 2:1 → uplift_window / retrofit_capex_per_mw
differs only by the HR-penalty term, asserted analytically); converted vom carries vom_adder × k;
validator rejects the field without seam 1.

ZERO-LP PHASE 0 (rule 29 step 0): re-run the D64 census instrument's arithmetic through the CODE
path on the committed post-Q42 converters (results/calibration/capxd64_fourth_seam_census.json is
the reference): the seam-4 column must reproduce to the MW — PJM 2029 1.68 GW → 0, MISO 0.53 → 0,
NEISO/NYISO/CAISO eligible MW unchanged (12.39 / 6.80 / 13.68 GW). Mismatch = STOP.

RULE 29 [R-SCREEN] — NO CONTROL SOLVE (clause b): the control is the committed bare `neiso-t1f`
(`18515067bf4d2fbe`, the D50 arm = the post-Q42 bare key). FIRST run G-DRIFT from its git_sha to
HEAD over src/market_sim + scripts/run_full_horizon.py + scripts/lib and classify every hunk INERT-
with-reason or LIVE in the PRECOMMIT before the arm is solved; a LIVE hunk is the only thing that
earns a control re-solve. ARM A1 = NEISO t1f, seam 4 alone (~8 min; the ISO where the re-screen
re-ranks the most rows — 39 committed converters — and the cap-binding question is live). The
forecast hindcast leg is its own screen. NYISO (12 min) is the second RGGI witness ONLY if A1 moves
the cap; GOLDEN-3 ONLY if A1 shows the cap unbinding or the composition moving by more than the
cap-packing unit in any year. PJM is NOT an arm (its bare leg is D60-R2's to land; read the seam's
PJM effect from that re-solve when it exists). Register A1 under a suffixed key with the `-pre-d65`
prior preserved.

PRE-REGISTERED EXPECTATIONS (falsifiable, not gates; D64 §4.4 table): NEISO conversions cap-bound
(2,940–3,000 MW) every year; the MW-weighted er of the 2028 set falls below D50's 0.550 and every
year's set ranks by hr within the in-merit hosts; ERCOT/MISO (if solved) 0 rows, byte-identical.

STOPs (D64 §4.5 — kill the arm, never promote it): (1) a k = 1 row moving in any ledger or log field;
(2) seam 4 alone making any carbon-0 row clear that the committed keeper did not, or a k > 1 host
converting under A1 that did not convert in the control in a non-cap-bound year (rule-14-wrong
direction); (3) any NEISO/NYISO year converting more than the cap, or ERCOT/MISO gaining a row;
(4) key drift (a realized key ≠ its pre-declared value, or a collision with a committed key);
(5) byte-inertness failing on the committed neiso-t1f recipe with the field absent / False.

COLLISION CARE: scenarios.py — your field sits in the D50 block; SCN-WS1a owns the D34-guard region
of __post_init__ and SCN-WS2a the federal_ces_* block (scenario-desk-ledger-2026-09.md register) —
touch neither; D62 (issued alongside) adds its own field elsewhere. ccs.py is yours alone this
window. Six shards: one appended line each, last commit. NOBODY but D60-R2 writes program-status.json
/ ff-verdicts.json this window: build, tests, Phase 0 and the A1 solve are yours now; REGISTRATION +
the artifact-only re-score wait until D60-R2's finding has merged (git log origin/main --grep=
D60-R2); if it has not when A1 is done, push everything else as a CHECKPOINT and state what is owed.
Score and register AFTER the final rebase; a rebase after scoring re-stamps scored_at_sha by an
artifact-only re-score before merge. Rule 22: forecast mode only, no holdout year. Rule 27: edit
locally, exact bytes, blob-verify every ≥300-line file after push (scenarios.py, ccs.py, the shards).
Rule 25: NEISO's cell from NEISO's arm; five U cells. Rule 28: row + six cells in this PR.

EXIT: FINDING-capx-d65-<date>.md (Phase 0 reproduction, G-DRIFT table, A1 at full magnitude vs the
expectations, every STOP's reading, the k = 1 invariance evidence, the deferred-FOM disclosure, a §8
ARM / DO-NOT-ARM recommendation with the owner card drafted, and the exact re-cut D65-B would need if
Q47 rules A); tests green; matrix green; pushed. Nothing arms in this lane.
```

## D68 — the MISO `complete` DECLARATION on miso-220 (r#42; CONDITIONAL on owner card C-17 / Q49) — **CHARTERED r#42, DISPATCH ONLY IF Q49 RULES "DECLARE"** — **Q49 RULED DECLINE (r#42 am.2): CLOSED UNDISPATCHED; never paste**

```
You are the D68 session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero solves,
executing owner ruling Q49 (capx ledger §3; card C-17, §0am.3) IF AND ONLY IF §3 records Q49 as
RULED "declare". If §3 shows Q49 unruled or ruled "hold"/"decline": STOP before any edit and say so.
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md §D68 (this section), which
binds pack §D56 and §D56-R verbatim (every READ FIRST item, step and guardrail) with NYISO → MISO,
`2026-09-05-nyiso-189-steam-identity` → `2026-09-05-miso-220-nonsteam-lift`, and `declared` = the
date you land. MISO has NEVER held a `complete` entry — this is a FIRST declaration, not a
re-entry, so there is no `withdrawn.MISO` block and no re-entry clause to cite; the licence is Q49.
DATA PROFILE: code
MODEL: Fable (a marker consequence — the one records act that changes what the program may spend).
BRANCH (suggested; graded by content): claude/capx-d68-miso-complete — FRESH off origin/main,
rebase before every push.

READ FIRST (beyond §D56/§D56-R): results/calibration/FINDING-miso220-nonsteam-offer-lift-2026-09-05.md
(the keeper's own record; it requested no marker; §against-interest: CT_PEAKER-2023 −7.985 against
a ±8.00 kill — 0.015 TWh of headroom) · docs/calibration-log/miso.md §miso-220 · CLAUDE.md rules 1
[R-STRUCT] / 13 [R-MEASURED] AS AMENDED by PR #4855 (the band-multiplier carve-out, conditions
(a)–(e)) and the keeper's `governance.authorized_price_tuning` block in
results/calibration/miso220_nonsteamlift_B/calibration_attestation.json — C6 reads PASS ONLY through
that declaration ("without the amendment C6 fails and this reads NOT-YET"); the marker entry's
`determination_at_declaration` MUST say so in those words · frontend/data/backcast/calibration-
complete.json (the ERCOT entry of 2026-08-31 is the closest template: a first declaration on a
CALIBRATED keeper with a lone ledgered C3c) · the audit board's newest entry (any MISO-adjacent
ruling; never re-litigate one).

THE WORK: §D56 steps 1–5 on miso-220 —
 1. Re-verify artifact-only: `python3 scripts/calibration_verdict.py --run-id
    2026-09-05-miso-220-nonsteam-lift` → must read CALIBRATED (grade 7/8, fails 0, lone ledgered
    C3c; C3a +7.1 / +3.4 / −7.0 %; 2025 C1/C2 SKIPPED on the preliminary EIA-923 vintage — state
    that limitation in the entry). Anything else: STOP and route (Q5 uniform rule).
 2. Write `complete.MISO` in the file's own conventions (declared / keeper / keeper_at_declaration
    / determination_at_declaration criterion-by-criterion / frontier_basis = NONE CLAIMED unless §3
    also records a frontier ruling / one_shot_status: validation tier 2020–2022 AUTHORIZED and
    UNSPENT; locked_test NEVER AUTHORIZED, stays under the freeze / by: Q49 verbatim / the
    authorized_price_tuning disclosure).
 3. Forecast board: re-key MISO gate (a) FAIL → PASS by TARGETED STRING EDIT of the row's leaves
    + the gate_a_provenance block (the file is not json.dumps-round-trippable); `read_live_at` =
    the sha you read at, re-read after the final rebase. Gate (a) PASSERS become {ERCOT, MISO,
    NEISO, PJM}. Nothing else on the board moves; no ff-verdicts byte.
 4. `python3 scripts/audit_keepers.py --check` (M1 must PASS) · `check_gate_a_provenance.py` 0 ·
    the keeper shard stamp the auditor requires · the calibration-keeper-auditor agent scoped
    --iso MISO.
 5. FINDING-capx-d68-<date>.md + calibration-log/governance.md entry + a one-line CHANGELOG row;
    the finding's alignment table states the four instruments (frontier · complete · gate-(a) ·
    determination) and where MISO's frontier leg stands (not claimed here).
STOP CLAUSE: before EVERY push re-read keepers/MISO.json; if the keeper moved, re-run step 1 on the
new id — CALIBRATED ⇒ re-key per D-5(b) with a dated note; NOT-YET ⇒ STOP and route. Never declare
on a NOT-YET keeper.
COLLISION: the owner's MISO backcast lane (miso-221+) is the other MISO writer — you touch the
marker, the board's MISO gate-(a) row + provenance block, the finding, the log, the shard stamp;
nothing else. D60-R2 (if alive) writes ff-verdicts.json — you never do. Rule 27: exact bytes,
blob-verify calibration-complete.json and program-status.json after push. EXIT: the declaration
landed, both gates green, finding pushed.
```

## D69 — the CAISO `complete` RE-DECLARATION on caiso-252 (r#42; CONDITIONAL on owner card C-18 / Q50) — **CHARTERED r#42, DISPATCH ONLY IF Q50 RULES "RE-DECLARE"** — **RE-SERVED at r#43 with its condition MET (caiso-253 landed, arm refused, keeper unchanged) and RULED HOLD AGAIN at r#43 ("hold until caiso-253b resolves"). **RE-SERVED A THIRD TIME at r#44 with that condition MET (caiso-253b resolved, #4964; keeper unmoved) and HELD AGAIN: "hold until caiso-254 resolves"** — served with the unbounded-wait problem named (CAISO's lane has run continuously 252 → 253 → 253b → 254, so each hold buys a new successor) and a terminating option offered and declined. **PARKED AT OWNER DIRECTION (r#45).** The condition was met again (caiso-253b resolved) while caiso-254 opened; this desk put the structural problem — a condition written against a LANE LABEL cannot terminate on a continuously-renaming lane — and offered a keeper-state condition instead. **Owner ruled "Keep label conditions; I'll say when."** So this card is NOT re-served on any desk's own reading; the owner brings it back. Do not paste until then**

```
You are the D69 session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero solves,
executing owner ruling Q50 (capx ledger §3; card C-18, §0am.3) IF AND ONLY IF §3 records Q50 as
RULED "re-declare". Otherwise STOP before any edit and say so. Binding charter: pack §D69 (this
section), which binds pack §D56 and §D56-R verbatim with NYISO → CAISO,
`2026-09-05-nyiso-189-steam-identity` → `2026-09-05-caiso-252-b1-notrim`, `declared` = the date you
land. CAISO's `complete` was WITHDRAWN 2026-08-06 (owner directive: CALIBRATED-WITH-CAVEATS on a C3a
LMP caveat beyond ±10 %; "3c3 is only acceptable ledgered caveat") — the withdrawn block's own
re-entry clause is the licence, and the condition it named is now MET on the record: C3a PASSES all
three years (+4.65 / +9.04 / +8.86 %) and the single ledgered caveat is C3c (2024 only).
DATA PROFILE: code
MODEL: Fable (marker consequence).
BRANCH (suggested): claude/capx-d69-caiso-redeclaration — FRESH off origin/main.

READ FIRST (beyond §D56/§D56-R): results/calibration/PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-
2026-09-05.md (Part II — the arm, the promotion, predictions scored: P-A2 and P-A6 FALSIFIED,
reported) · the caiso-252 calibration-log entry · calibration-complete.json `withdrawn.CAISO`
WHOLE (reason, frontier_withdrawn, frontier_basis_at_withdrawal, one_shot_status, locked_test) —
the re-declaration NESTS the withdrawn entry as `prior_withdrawal_2026_08_06` exactly as the NYISO
D56-R re-entry did, deletes nothing · the board's CAISO row (already re-keyed to caiso-252 by the
promoting lane; gate (a) FAIL on the marker alone) · the audit board's newest entry.

THE WORK: §D56 steps 1–5 on caiso-252 —
 1. Re-verify artifact-only: `calibration_verdict.py --run-id 2026-09-05-caiso-252-b1-notrim` →
    CALIBRATED (8 scored, grade 7, fails 0, ledgered 1 = C3c 2024; C4 gas 0.285 / 0.261 / 0.297;
    2025 C1 7 SKIPPED + C2 gas SKIPPED on the preliminary vintage — state it). Else STOP.
 2. Write `complete.CAISO` (declared / keeper / keeper_at_declaration / determination_at_
    declaration criterion-by-criterion / `frontier_basis` = NONE CLAIMED unless §3 records a
    frontier ruling — the 2026-08-06 withdrawal removed both instruments, so frontier is a SEPARATE
    owner act, exactly the D56-R → Q39 sequence / one_shot_status: validation tier AUTHORIZED,
    UNSPENT — note the caiso-252 finding's own C3a weight-basis and DMM RA-import asks as carried,
    not as conditions / locked_test NEVER AUTHORIZED, under the freeze / by: Q50 verbatim), nesting
    the withdrawn block whole.
 3. Board: CAISO gate (a) FAIL → PASS by targeted string edit + the provenance block; `read_live_at`
    re-read after the final rebase. PASSERS become {CAISO, ERCOT, NEISO, PJM} (+ MISO if D68 landed
    first — read the file, never assume).
 4. audit_keepers M1 PASS · check_gate_a_provenance 0 · shard stamp · keeper-auditor --iso CAISO.
 5. FINDING-capx-d69-<date>.md + governance log + CHANGELOG row; four-instrument alignment table.
STOP CLAUSE as §D56-R C: re-read keepers/CAISO.json before every push (caiso-253 is OPEN on its
branch — a promotion may land under you; CALIBRATED ⇒ re-key per D-5(b) with a dated note; NOT-YET
⇒ STOP and route). COLLISION: caiso-253 (owner's lane) and D68 (the same two files — if both are
dispatched, D68 lands first and D69 rebases onto it; both edit disjoint ISO blocks). Rule 27 exact
bytes + blob-verify both JSON files. EXIT: declaration landed, gates green, finding pushed.
```

## D70 — the NYISO `complete` RE-DECLARATION on nyiso-196, the FOURTH (r#42 amendment 1; CONDITIONAL on owner card C-19 / Q51) — **CHARTERED r#42 am.1, DISPATCH ONLY IF Q51 RULES "RE-DECLARE"** — **RE-SERVED at r#43 with its condition MET (the keeper survived a full refresh byte-unmoved) and RULED HOLD AGAIN: "hold, nyiso-197 is live" (#4919's open CHP add-back basis question could move the keeper a fifth time). Re-serve condition: nyiso-197 lands AND the keeper reads CALIBRATED. **PARKED AT OWNER DIRECTION (r#45).** Its condition can NEVER be met as written: nyiso-197 never landed as such — the lane rolled straight to nyiso-198. **Owner ruled "Keep label conditions; I'll say when."** So this card is NOT re-served on any desk's own reading; the owner brings it back. Do not paste until then**

```
You are the D70 session of the capacity-expansion track — a GOVERNANCE RECORDS lane, zero solves,
executing owner ruling Q51 (capx ledger §3; card C-19, §0am amendment 1) IF AND ONLY IF §3 records
Q51 as RULED "re-declare". Otherwise STOP before any edit and say so. Binding charter: pack §D70
(this section), which binds pack §D56 and §D56-R verbatim with `2026-09-05-nyiso-189-steam-identity`
→ `2026-09-06-nyiso-196-extract-basis` and `declared` = the date you land. This is NYISO's FOURTH
declaration: the 2026-09-05 withdrawn block (Q46) states its own re-entry condition — "a NEW explicit
owner declaration on a keeper scoring CALIBRATED" — and that condition is met on the record. The
re-declaration NESTS the withdrawn entry whole as `prior_withdrawal_2026_09_05` (which itself nests
08-30 and 07-19); nothing is deleted.
DATA PROFILE: code
MODEL: Fable (marker consequence).
BRANCH (suggested; graded by content): claude/capx-d70-nyiso-redeclaration — FRESH off origin/main.

READ FIRST (beyond §D56/§D56-R): docs/FINDING-nyiso196-cc-outage-share-basis-2026-09-05.md and the
nyiso-196 entry in docs/calibration-log/nyiso.md (the keeper's own record — it wrote "`complete` NOT
re-declared — owner court"; its regressions at full magnitude: Linden CC_CHP 6.2 → 5.2 vs 7.3 meter,
Cricket Valley 0.53 TWh UNDER in 2024, C3a-2024 +1.5 pt — these go into the entry) ·
calibration-complete.json `withdrawn.NYISO` WHOLE · the board's NYISO row (already re-keyed to
nyiso-196 by the capx desk at r#42 am.1; gate (a) FAIL on the marker alone) · the audit board's newest
entry (Z-6, the register-time marker re-check, is live there — cite it, do not re-litigate it).

THE WORK: §D56 steps 1–5 on nyiso-196 —
 1. Re-verify artifact-only: `python3 scripts/calibration_verdict.py --run-id
    2026-09-06-nyiso-196-extract-basis` → CALIBRATED (grade 7/8, fails 0, lone ledgered C3c; C1 14/14
    free 10/10; C3a +4.6 / +4.7 / −6.9 %). Anything else: STOP and route (Q5 uniform rule).
 2. Write `complete.NYISO` in the file's conventions (declared / keeper / keeper_at_declaration /
    determination_at_declaration criterion-by-criterion incl. the regressions / `frontier_basis` =
    NONE CLAIMED unless §3 records a separate frontier ruling / one_shot_status: validation tier
    2020–2022 AUTHORIZED and UNSPENT — the 2022 touchpoint solved on 2026-09-05 was UN-REGISTERED and
    is diagnostic only (holdout-2022-completeness doc §1a) / locked_test NEVER AUTHORIZED, under the
    freeze / by: Q51 verbatim), nesting the withdrawn block whole.
 3. Board: NYISO gate (a) FAIL → PASS by TARGETED STRING EDIT of the row's leaves + the
    gate_a_provenance block; `read_live_at` re-read after the final rebase. If D68 / D69 have landed,
    read the file for the current passer set — never assume. No ff-verdicts byte.
 4. audit_keepers M1 PASS · check_gate_a_provenance 0 · shard stamp · keeper-auditor --iso NYISO.
 5. FINDING-capx-d70-<date>.md + governance log + CHANGELOG row; the four-instrument alignment table;
    ONE sentence stating that T3-NYISO-GOLDEN's start precondition (pack §T3-NYISO-GOLDEN Am.1) is
    now met and that Q45 stands as ruled — dispatch of the campaign is the DIRECTOR's act after
    D60-R2/-R3's finding merges, not yours.
STOP CLAUSE (§D56-R C, sharpened again — NYISO promoted six times in a week): before EVERY push
re-read keepers/NYISO.json; keeper moved and CALIBRATED ⇒ re-key per D-5(b) with a dated note;
NOT-YET ⇒ STOP and route. Never declare on a NOT-YET keeper.
COLLISION: the owner's NYISO backcast lane (nyiso-197+) is the other NYISO writer; D68 / D69 edit the
same two files in other ISO blocks — land AFTER them if all run, rebase before every push. Rule 27:
exact bytes; blob-verify calibration-complete.json + program-status.json after push. EXIT: the
declaration landed, both gates green, finding pushed.
```

## D72 — the S2 carbon-floor blast radius on the forecast board, and the D23 re-examination it forces (r#44 amendment 1; zero-LP phase 0) — **LANDED at r#45. THE PREMISE WAS FALSE and the null is CLEAN: the pre-repair predicate exempted `"zero"` BY LITERAL ENUMERATION (`not in ("zero", None)`), so every bundle listed in this charter is OUT and the blast radius is EMPTY. D23 UPHELD (verdict a), amended by dated cross-reference only.** Its §6.1 hands the desk the fact that narrows D73: the live golden is ALREADY re-armed off the mis-constructed pair, so the FC-6 P1 failure now fires only on the ARCHIVED `carbon25` arm. **Director error recorded (ledger §0ap.5): the premise was mine and a five-line code read would have killed it before the session was spent — a blast-radius charter now states the predicate read as a PRECONDITION OF ISSUING, not as the lane's first step.** Never re-paste**

```
You are the D72 session of the capacity-expansion track. Binding charter: pack §D72 (this section).
Zero LP in phase 0. Your object is a CODE REPAIR ANOTHER DESK LANDED and what it does to bundles and
verdicts THIS program already committed.
DATA PROFILE: code (widen to neiso only if phase 2 earns a solve).
MODEL: Fable (this can re-open a landed finding's attribution and move a golden's verdict BASIS —
determination consequences, not execution).
BRANCH (suggested; graded by content): claude/capx-d72-carbon-floor-blast-radius — FRESH off origin/main.

THE TRIGGER, stated as fact and to be VERIFIED BY YOU, never assumed. SCN-WS1c commit `b1996141`
("federal carbon price is a FLOOR under the state program", owner ruling S2) repaired a defect its own
message names G-C1: `resolve_carbon_program`'s FORECAST branch "nulled the program adder whenever a
non-default `carbon_price_path` was set, so a named federal RFF path SUPPRESSED the state
cap-and-trade program." Its measured consequence on ITS campaign: `policy_bundle="tight"` was a carbon
price CUT of $16–$102/tCO2 on CAISO, NYISO and NEISO in every one of 25 horizon years. The new
semantic is `effective = max(RFF path(year), program trajectory(year))` on a program ISO; the scalar
`carbon_price` keeps its Q26 replace semantics and `carbon_price_delta` its additive stage.

WHY THIS DESK OWNS A CONSEQUENCE OF ANOTHER DESK'S REPAIR. A director census of the committed
forecast bundles finds `carbon_price_path='zero'` together with `state_carbon_pricing=True` on
program ISOs across `results/ff-t1f-d46/{caiso,neiso}`, `ff-t1f-d50/neiso`, `ff-t1f-d65-{a1,ctl}/neiso`,
`ff-t1f-s4hydro/neiso*`, `hindcast/caiso-2021-2025-realized-t1h-d46`, and EVERY arm of
`ff-t3-neiso-golden/**` including the FC-6 arms `base`, `carbon25`, `carbon_plus25`, `gaspm5`,
`gasup150`. IF `'zero'` counts as "a non-default path" at those bundles' vintages, RGGI was nulled in
runs this program scored — and GOLDEN-3 is the golden. **Do not assume it does.** `'zero'` may resolve
as default-equivalent, or the defect may post-date those solves. THE FIRST QUESTION IS WHETHER THE
PREMISE IS TRUE AT ALL, and a clean null is a complete and welcome result.

PHASE 0 — ZERO LP, and it is the whole lane until it says otherwise:
 1. Read `b1996141` whole (diff + message) and state, from the CODE, the exact predicate the old
    branch used to null the adder and whether `carbon_price_path='zero'` satisfies it. Quote the
    lines. If it does not, STOP HERE, write the finding saying so, and close — that is the result.
 2. If it does: date the defect. `git log -L` the nulling predicate to find the commit that
    introduced it and the commit (`b1996141`) that removed it. Every bundle solved between those two
    shas with a program ISO + non-default path is IN the radius; everything else is out.
 3. CENSUS, in a table, every committed forecast bundle by `run_config.json` `git.sha` and its
    resolved carbon inputs: IN-RADIUS / OUT / INDETERMINATE, with the reason. This is exactly the
    method D60-R3 used for the retirements hunk (`FINDING-capx-d60-2026-09-05.md` §8-blast-radius,
    28 of 33 PRE-hunk) — reuse its shape so the two tables read as one instrument.
 4. PRICE IT WITHOUT SOLVING: for one in-radius NEISO year, compute `resolve_carbon_program` both
    ways from the bundle's own committed config and report the $/tCO2 gap per horizon year. A gap of
    zero means the radius is nominal; SCN measured $16–$102 on their arms, so state yours at full
    magnitude either way.

THE D23 RE-EXAMINATION (this is why the lane is Fable). `FINDING-capx-d23-p1-carbon-sign-2026-09-01.md`
adjudicated GOLDEN-2's FC-6 P1 "carbon-sign defect" as **the instrument's premise being inverted, not a
model defect**, on the reading that "rung 0 IS the RGGI world for a program ISO, sitting ABOVE rung 25
in every NEISO year". **That conclusion presupposes the base arm actually carried the RGGI adder.** If
phase 0 puts those arms in the radius, the adder may have been nulled and D23's attribution rests on a
behaviour now identified as a defect. State plainly which of three the evidence supports: (a) D23
stands unchanged (the arms are out of radius, or in it but the adder resolved anyway); (b) D23's
CONCLUSION stands but its stated MECHANISM needs amending; (c) D23's attribution is unsafe and the P1
verdict basis must be re-opened. **Amend D23's file only with a dated cross-reference — never rewrite
another lane's finding** (rule 27 discipline and the D23 §8 R3 precedent, which explicitly did not
edit D21's file).

WHAT YOU DO NOT DO. No re-solve, no re-score, no registration, no board byte — `ff-verdicts.json` and
`program-status.json` belong to D60-R3 this window and you must not touch them even if you conclude a
verdict is wrong; you REPORT that and the director serves the card. No keeper, marker, shard or freeze.
No `ScenarioConfig` field, no default flip, no semantic change — S2 is ruled and executed, and rules
19/24 require ONE documented semantic, so proposing a second is out of scope. Do not build D23's R1
guard: it is the routed successor (D73) and it is held on your answer, because whether the guard should
reclassify P1 as MIS-CONSTRUCTED depends on what you find.

EXIT: FINDING-capx-d72-<date>.md with the predicate quoted, the defect dated between two shas, the
full IN/OUT/INDETERMINATE census table, the unsolved $/tCO2 pricing, the (a)/(b)/(c) verdict on D23
with a dated cross-reference added to D23's file, and a §8 that states — as a recommendation to the
director, never an act — whether any committed verdict must be re-scored or re-run, at what LP cost,
and in what order relative to D60-R3's legs. Rules 13, 19, 21, 22 (no out-of-training anything), 24,
25, 27 (blob-verify any ≥300-line file), 28 (you test no mechanism; no cell moves). Push each stage as
it lands; rebase BETWEEN stages, never during one (r#44 doctrine, D60-R3 §5.0e).
```

## D66 — the PJM 2024/25 + 2025/26 supply census: the residual D61 named and D57 could not reach (r#44 amendment 1; zero-LP) — **LANDED at r#45, and it REFUTES the framing this desk was carrying.** The residual is NOT one-sided missing supply: on one recovered position definition it splits additively — **2024/25 +2.19 pt = 78 % requirement / 22 % supply; 2025/26 +4.38 pt = 67 % / 33 %** — and the requirement leg is entirely the peak, reproducing `R_model − R_published` to the MW with zero residual. Against PJM's **OFFERED** supply the model census is **9,332 / 3,147 MW short** (the cleared comparison flattered it: PJM left 8,530 MW uncleared, the model 406). **Largest clean closable item, sign PRE-DECLARED: the model applies 2026/27-vintage VRE ELCC to every DY (wind 0.41 vs published 0.16; solar 0.1064 vs 0.36/0.54) — correcting it moves the census DOWN 0.6–1.4 GW and WIDENS the residual, and rule 14 says do it anyway → queued as D75.** Never re-paste**

```
You are the D66 session of the capacity-expansion track. Binding charter: pack §D66 (this section) +
`FINDING-capx-d61-2026-09-05.md` (which named this residual) + `DESIGN-capx-d54-pjm-clearing-half-
2026-09-05.md` and `FINDING-capx-d57-2026-09-05.md` (the clearing half you are auditing the INPUTS of).
ZERO LP. No solve is authorized in this lane at all.
DATA PROFILE: pjm
MODEL: Opus (a measurement lane with a pre-declared method; no arming, no determination consequence).
BRANCH (suggested; graded by content): claude/capx-d66-pjm-supply-census — FRESH off origin/main.

THE OBJECT, and why it is NOT D62's. D57 landed PJM's cleared position within −0.5 / −1.0 / −2.8 pts
of the published BRA and the §3.5 identity 8/8. D61 then established that in **DY 2024/25 and 2025/26
every offer already clears**, so in those two years the price is set by where the demand curve meets a
stack whose composition is a CENSUS question — how much and what kind of capacity the model brings to
the auction — and NOT by the going-forward bar. D62 is repairing the BAR; it explicitly routes the
census here and cannot answer it, because in those two years the bar changes nothing (D62's own
pre-declared sign: "2024/25 5.73 → 5.04 then FROZEN — all offers clear"). **You are therefore not
blocked on D62 and must not wait for it.**

THE WORK — a reconciliation, not a model change:
 1. Reconstruct the model's offered supply for DY 2024/25 and 2025/26 from the COMMITTED D57 arm-A
    ledgers (`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a/`):
    accredited MW by fuel class, the price-taker block, `requirement_mw`, and the census position.
    D62's screen recorded the 2022/23 row as requirement 155,048 · price takers 30,578 · census
    position 1.17019 — reproduce that row first as your instrument check, then extend to the two
    target years. A mismatch on 2022/23 is a STOP: your reconstruction is wrong, not the model.
 2. Against it, place PJM's OWN published BRA supply for the same delivery years — cleared UCAP by
    resource type, total offered, the reliability requirement and the clearing price — from the
    published Base Residual Auction reports already under `data/raw/capacity-market/`. If a needed
    report is absent, say so and STOP on that year rather than substituting a proxy (rule 14).
 3. DECOMPOSE the gap into named, additive buckets, each traced to a source: DR and EE (PJM clears
    large volumes the model may not represent), energy-efficiency, imports/external units, storage
    and hybrid accreditation, nuclear/uprates, and the accreditation basis itself (EFORd-derated
    nameplate vs PJM's accredited UCAP under the D48 vintage). The deliverable is a table whose rows
    SUM to the measured gap — an unexplained residual is reported as its own row, at full magnitude,
    never distributed across the others.
 4. For each bucket, state whether it is (i) a representation gap this model could close and how, at
    what cost, (ii) a deliberate scope exclusion, or (iii) already handled and mis-attributed by you.
    Name which bucket, if any, is large enough to explain D57's remaining position error.

DISCIPLINE. This lane changes NOTHING: no `ScenarioConfig` field, no default, no arming, no matrix
cell (you test no mechanism — if you conclude one is needed, that is a routed successor and a director
card, per rule 28), no board byte, no keeper. Do not re-solve to "check" a number: the committed
ledgers and the published reports are the two sides, and where they cannot answer a question you write
that down. Rules 14 (prefer the accurate published number and never bury a discrepancy in an estimate),
21, 22, 24, 25 (PJM's data only), 27. Any new raw file goes in through the data-intake skill with its
source doc and page.

COLLISION: D62 owns `retirements.py`, `capacity_market.py`, `avoidable_cost_rate.py` and a
`scenarios.py` field this window — you write NO source file at all, so you are disjoint by
construction. Read the same committed ledgers freely; they are immutable. D60-R3 owns the forecast
board; you write no board byte.

EXIT: FINDING-capx-d66-<date>.md — the 2022/23 instrument check, the two-year model-vs-published
table, the additive decomposition with its residual row, the per-bucket disposition, and a §8 naming
what (if anything) should become a chartered repair and what it would cost. Push it; nothing arms.
```

## D60-R3 — the D60 relaunch, THIRD issue (r#42 amendment 2; owner ruling: D60-R2 is DEAD — "issue D60-R3"), with D65's HEAD-drift instrument folded in as the blast-radius section — **ISSUED r#42 am.2; NEVER DISPATCHED; RE-EMITTED AND DISPATCHED at r#43** with a new STATE AT START block (what main took since the charter was written) and an extended collision note. **This section IS the issued text.** — **DISPATCHED AND LIVE at r#44 (PRs #4946/#4955/#4959/#4963):** state at start 17/17 keys unmoved with all three charter assertions MEASURED; two environment defects (off-pin highspy/pandas/pydantic, a shallow clone) repaired before the first solve; control-first on all three legs, 0 non-provenance diffs, the rubric 1.0→1.1 advance INERT; the GOLDEN-3 FC-4 input pinned not guessed; NO second drift hunk; §8-blast-radius landed, 28 of 33 bundles PRE-hunk; **§5.0e — the lane rebased under its own running solve, killed the leg, and made the failure mode mechanical (`exit 90`); 'rebase BETWEEN legs, never DURING one' is now doctrine**. OWED: the three legs, the Q37 rows, §5 and the close. — **LIVE at r#45, leg 4 of 5.** Legs 3 (`caiso-t1f`) and 4 (`pjm-t1f`) registered; determination HOLD → HOLD. **Leg 4 FIRED Addendum C.4's I12 STOP on every comparable year (control −11.2/−13.5/−13.1/−13.0 vs arm −11.6/−15.6/−15.8/−16.5): supply lengthened +9.1–18.0 GW but the requirement rose MORE, +16.2–33.5 GW; the requirement is byte-identical to the committed D50 arm so Q42 owns none of it — the rise is D48 + D57's, and D48's accounting is NOT position-neutral forward. ROUTED to the director and HELD until this finding closes.** OWED: leg 5 (`neiso-t3` GOLDEN-3), the Q37 rows, §5 and the close. Never re-paste while live**

```
You are the D60-R3 session of the capacity-expansion track — the THIRD launch of D60's owed half (pack
§D60 + Amendments 1 and 2; §D60-R2 is the charter you inherit verbatim except where this section says
otherwise). D60 died after its flip, four renames and two of five re-solves; D60-R never launched;
D60-R2 (PR #4824) landed ONLY its state-at-start commit and Addendum D, then went silent and the owner
ruled it DEAD at r#42. You start FRESH from the committed record.
FIRST, before anything else: `git fetch origin --prune`; check for any `claude/capx-d60r*` branch and
any commit mentioning "D60-R2" or "D60-R3" on origin/main newer than `342c7593` (D60-R2's last
commit). If one exists, STOP and report it — two writers on ff-verdicts.json is the one collision
this program cannot absorb. (The director verified NONE exists at pin `04e6906d`, r#43.)
DATA PROFILE: caiso, pjm, neiso (incremental — hydrate each before its leg; `data/clean` regenerated
once before the first solve).
MODEL: Opus (execution of pre-declared legs; every adjudication is already made — Amendment 2's STOP
resolution, Addendum D's two pre-declared negatives, the owner's Q47/Q48/Q49/Q50/Q51 rulings of r#42
am.2; a NEW surprise is a STOP, not a decision).
BRANCH (suggested; the director grades by content): claude/capx-d60r3-completion — FRESH off
origin/main, rebase before every push, PUSH EACH LEG AS IT LANDS.

WHAT IS ALREADY ON MAIN (never re-done): the flip (Q40/Q41/Q42); four renames with `-pre-d60` priors;
`miso-t1f` (`b1a73a087064ffd8`, HOLD) and `nyiso-t1f` (`19a9690bb12c8459`, PROMOTE-WITH-CAVEATS on
FC-7 alone) registered; the D60 finding §§0–4, 6–7; **Addendum D** (docs/handoffs/PREDECL-capx-d60-
2026-09-05.md — the mechanism, the six NEW (ISO, field) rows with `requires="iso-registry"`, the
dormant seventh, and the TWO PRE-DECLARED NEGATIVES: miso-t1f's FC-7 will NOT clear (five pre-batch
MISO overrides without curated rows → D63, not yours), CAISO keeps its `negative_renewable_offers`
caveat). Read §D60-R2 "READ FIRST" in full — it binds.

WHAT YOU OWE (the §D60-R2 list, unchanged): (1) the three re-solves — `caiso-t1f` (key `29f8eb372810195f`,
~23 min, prior `caiso-t1f-pre-d60`), `pjm-t1f` (`09996eca71ee80fd`, ~28 min, prior `pjm-t1f-pre-d60`;
Addendum C P21–P25), `neiso-t3` GOLDEN-3 (~33 min / 3.7 GB, prior `neiso-t3-pre-d60`; Addendum B's six
assertions; an FC-map move where §6.4 said none is a STOP); each leg: score → `forecast_verdict --tier`
→ `register_forecast_run --bundle` AFTER that leg's final rebase (X-6b), one blob-verified commit per
leg, pushed at once; (2) the Q37 rows from Addendum D and the artifact-only re-scores of `nyiso-t1f`,
`miso-t1f` and your three legs — FC-7 the ONLY row that may move, anything else a STOP; (3) finding §5
and §8 and the close. STATE AT START first, zero solve: every bare key re-resolved through the harness
at your HEAD vs Addendum A §A.2 + Addendum C; ANY bare-key drift is reported before anything runs.

STATE AT START — WHAT MAIN HAS TAKEN SINCE D60-R2's PINS (director-verified at `04e6906d`):
 · D65 Act A — a default-off field registered in the cache-key optional-fields table. MUST be
   key-neutral: assert it explicitly in your state-at-start table.
 · THREE keeper promotions (MISO 220, CAISO 252, NYISO 196) and FOUR gate-(a) re-keys on
   program-status.json — BACKCAST only; no forecast verdict moved.
 · r#43 delta (`d66d5e6b..04e6906d`), all NEW since the charter was written:
   — rule 30 `[R-TOUCHPOINT-FOLD]` in CLAUDE.md (backcast dashboard; not your surface);
   — the R-AZ registration-time tier-marker re-check in `scripts/dashboard_add_run.py` +
     `scripts/lib/holdout_policy.py` — a BACKCAST registration gate. Your registrations go through
     `register_forecast_run.py`. State in one line whether that path is touched; if it IS, STOP.
   — three SCN hindcast sidecars under `frontend/data/hindcast/` — NOT the board.
   — **ZERO commits under `src/market_sim/`**, so any bare-key drift you find is not from this delta.

NEW IN R3 — THE BLAST-RADIUS SECTION (D65 §3b/§3c, capx D71 folded in; zero DOF, code only):
 (a) D65 found that the committed `neiso-t1f` (`18515067bf4d2fbe`, git_sha `9e48ff6`) is NO LONGER
     what HEAD produces from its own recipe: NEISO 2027 economic retirements 33 rows / 2,369.81 MW
     (committed = `git archive 9e48ff6` solved fresh, 0 differing ledger keys) vs 40 rows / 2,244.89 MW
     at HEAD — deterministic, not solver noise, not environment, no clock reads. Its named candidate is
     capx D55's `_floor_retention_merit` in retirements.py (an ungated ordering change; `floor_retained`
     is `[]` on both sides, so a candidate, not a cause).
 (b) BISECT it, before your three re-solves so the finding can say which side of the hunk each leg
     sits on: `git bisect` over `9e48ff6..HEAD` restricted to `src/ scripts/ configs/`, each probe =
     `git archive <sha> src scripts configs` run against the same `data/` via MARKET_SIM_DATA_ROOT on
     NEISO 2026–2027 with the committed `neiso-t1f` recipe (D65 §3c's exact instrument; ~2 solve-years
     ≈ 5 min per probe; ≤ 8 probes). The bisect is over LEDGER KEYS of `evolution_2027.json`
     (`retirements` rows/MW, `reserve_margin`, `fleet_by_fuel_after.gas_cc`) — a probe matches the
     committed side or the HEAD side; anything else is a second hunk and a STOP-and-report.
 (c) Report the hunk (commit, file, function, the lines) and WHAT IT DOES in words — never "fix" it:
     if it is an intentional repair (D55's is), the committed bundles are stale and the re-solves you
     run ARE the remedy; if it is an unintended behaviour change, that is a STOP routed to the director
     with the hunk named. Then classify EVERY committed forecast bundle (`results/ff-*/**/run_config.json`
     `git.sha`) as pre-hunk (stale vs HEAD) or post-hunk, in a table in the finding's §8-blast-radius.
     Your three legs are post-hunk by construction; say which bare keys remain pre-hunk after you land
     (those are D60-R3's routed residue, not its scope).
 (d) D65's A1 arm (`results/ff-t1f-d65-a1/neiso`, key `8ebed20ae90ec0e7`) and its same-HEAD control
     (`results/ff-t1f-d65-ctl/neiso`) are committed as SLIM files only. If `register_forecast_run.py
     --bundle` can register A1 from what is there, register it under its suffixed key with the incumbent
     preserved at `neiso-t1f-pre-d65` and re-score artifact-only; if it cannot, write ONE line in §8
     saying so and leave it to D65-B (released on your landing). Do NOT arm anything: bare `neiso-t1f`
     stays the designated leg.

GUARDRAILS: §D60's — rules 1, 5, 12 (sequential legs), 13, 14, 19, 21 (no value changes — Q47's Act B is
D65-B's, AFTER you land, never yours), 22 (t1f 2026–2030, t3 2026–2050; nothing against measured
H1-2026), 24, 25, 27 (exact bytes; blob-verify ff-verdicts.json + program-status.json + the finding
after every push), 28 (no cell moves — you test no mechanism; the bisect names a hunk, it does not
adjudicate one). No keeper, shard, marker, freeze or default moves (Q49 DECLINED; Q50/Q51 were RE-SERVED
at r#43 with their conditions met and HELD AGAIN — gate (a) reads FAIL for CAISO/MISO/NYISO by the owner's
choice, and no marker will land under you this window; you re-key nothing there). STOPs: PREDECL §7
verbatim; Amendment 2's "any non-FC-7 row moves"; a second drift hunk; a bare key moved by D65's field.

COLLISION: you are the ONLY writer on `ff-verdicts.json` / `program-status.json` and on CAISO / PJM /
NEISO forecast surfaces this window. D65-B, D62's registration, D58 and D63 are HELD until you land.
D62 is dispatched CONCURRENTLY with you — it builds, tests and solves PJM but registers nothing until
your finding merges; if you see a board edit that is not yours, STOP and report. SCN-WS1b / WS-2b /
WS-4b register into `frontend/data/hindcast/` under their own campaign keys and never touch the board.
D69 / D70 (records lanes) are HELD at r#43 and will not land marker edits under you; the owner's backcast
lanes (nyiso-197, caiso-253b, miso-221) move keepers and shards — rebase before every push and keep
their edits verbatim.

EXIT: three legs registered on their pre-declared keys with priors preserved; the seven rows; every
affected bare key re-scored artifact-only; the drift hunk named with its table; the finding complete
and closed; all blob-verified. Then the director releases D65-B, D62's registration, D58 and D63.
```

## D65-B — Act A ARMING + Act B RE-IDENTIFICATION, coupled (r#42 amendment 2; owner ruling Q47 = "Arm coupled, after D60-R3") — **CHARTERED r#42 am.2, RELEASED-CONDITIONAL: dispatch AFTER D60-R3's finding merges** — **RELEASED r#46 am.1 (D60-R3 merged #5038) FOR ITEMS 1–5; ITEM 6 (the every-bare-key batch) IS HELD UNTIL D77's FIX MERGES** (pack §D77: the CCS emission-rate seam is solve-affecting from 2028 and Q47's "one re-key event" cannot survive a second solve-affecting fix a day later). Before the batch, classify HUNK BY HUNK: SCN-LOAD `d14a7ed0` (`DEMAND_GROWTH_RATES` all six ISOs — LIVE on every T1-F key except CAISO, measured inert there), the wallclock P1 basis seed #5033 (`pipeline/solve.py` / `lp/model.py` — VERIFY forecast-path byte-identity from the code), and D77's repair. The batch lands the whole T1-F board in ONE demand vintage — that is now one of its purposes. A matched cache key is NOT a G-DRIFT verdict: `constants.py` is outside it. Board files: D60-R4 then D63 are the sole writers until they merge; rebase between legs, re-audit the delta, never rebase during a solve.

```
You are the D65-B session of the capacity-expansion track — executing owner ruling Q47 (capx ledger §3,
r#42 amendment 2, verbatim option "Arm coupled, after D60-R3"): flip `ccs_retrofit_fixed_cost_co2_scaling`
default ON (Act A) AND re-identify `ccs_retrofit_vom_adder` 8.0 → 2.95 $/MWh (2026$) (Act B) in ONE PR
and ONE re-key event. Binding charter: pack §D65-B (this section) + docs/handoffs/FINDING-capx-d65-
2026-09-05.md §8.1 (why never Act A alone) and §9 (the six items, verbatim your spec) + FINDING-capx-
d64-2026-09-05.md §2.4 (the level) and §4.5 closing clause. PRECONDITION: `git log origin/main
--grep=D60-R3` shows its finding MERGED; otherwise STOP — two re-key events a day apart is the thing Q47
was worded to prevent.
DATA PROFILE: all (the re-key batch touches every ISO's bare key).
MODEL: Opus (pre-declared execution; rule 27 core scope permitted).
BRANCH (suggested): claude/capx-d65b-coupled-arming — FRESH off origin/main.

THE WORK, in D65 §9's order:
 1. THE WIDENED EXTRACT FIRST (STOP 6 of D64): `fetch_nrel_atb.py`'s filter carries `Variable O&M` and
    `Heat Rate` for `NaturalGas_FE` from the SAME source bytes (OEDI ATBe.csv v4.0.0, sha256 567dde9d…);
    the pinned `data/raw/nrel-atb/atb_2024v4_electricity_filtered.*` regenerated; a test in the shape of
    `tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py` asserts
    `ccs_retrofit_vom_adder == (ATB gas_cc_ccs VOM − ATB gas_cc VOM) × inflation_factor()` (2.7 $/MWh
    2022$ × 1.0909 = 2.95 2026$). No derivation asserted ⇒ no value change (rule 23).
 2. ACT B: `ccs_retrofit_vom_adder` 8.0 → 2.95 in scenarios.py with the dollar-year stated;
    `docs/parameter-citations.md` `needs-citation` cleared, NETL Rev 4a 2.23 recorded as the cross-check,
    ATB the basis (host and island on one basis — D41 §2.3). Direction stated BEFORE any solve:
    re-identification makes retrofits EASIER; rule 14 keeps the accurate value whichever way it moves.
 3. ACT A: the (b′-1) declared default flip — dataclass default `True`, the frozen cache-key drop value
    stays `"False"` so an explicit `False` keeps its pre-flip key (the D50/Q42 pattern); the validator's
    seam-1 requirement is satisfied because Q42 armed seam 1.
 4. THE RE-KEY, DECLARED BEFORE THE SOLVE: every bare forecast key re-resolved and pre-declared in a
    PRECOMMIT; priors preserved at `-pre-d65b`; the cache-epoch ledger in `src/market_sim/results/
    cache.py` given its entry; the pinned-key cause blocks in `tests/regression/test_persisted_identity.py`
    updated; `test_off_is_byte_identical_and_cache_neutral`-shape test for the explicit-False path.
 5. RULE 29 SCREEN (one leg): the informative arm is a CARBON-0 ISO — RGGI ISOs are cap-bound on both
    constructions and cannot discriminate (D65 §8.1). Screen = ERCOT t1f (~12 min; D64 §2.4: 10.2 GW at
    the ceiling under Act B on the shipped shape, 5.7 GW under Act A + B, every row within 0.1–4 % of
    the bar). Structural STOP gate ONLY: rows that clear must be `er/phys` ≥ 1.27 hosts (D49 §1.3), the
    identity uplift/capex ∝ 1/k must hold, k = 1 rows byte-identical, no non-target FC row flips. A
    carbon-0 ISO GAINING rows is NOT a STOP — it is the accurate level's pre-registered signature.
 6. THE BATCH (screen cleared): re-solve every bare key sequentially (rule 12) — ercot-t1f, neiso-t1f
    (~8), nyiso-t1f (~12), caiso-t1f (~23), pjm-t1f (~28), miso-t1f (~65), neiso-t3 GOLDEN-3 (~33 min);
    score → verdict → register in place with `-pre-d65b` priors; FC-map moves reported at full
    magnitude against D64 §2.4's census and D65 §4's NEISO reading; the D50 §6.2 blast-radius
    reconciled; matrix: the `ccs_retrofit_screen` row's def/note carries Act B (no cell verdict moves),
    the `ccs_retrofit_fixed_cost_co2_scaling` row's cells re-stamped `fc: K` where the arm is now the
    bare leg; six shards, one appended line each, last commit.
 7. FINDING-capx-d65b-<date>.md: PRECOMMIT keys vs realized, the screen gate table, per-ISO before/after,
    the composition the coupled construction produces (the "no merchant NGCC ever clears at carbon 0"
    claim retired or confirmed on the record), the board rows, governance attestation with rule-27 blob
    checks; the D8 curated DOF-ledger rows for the flipped default (Q37's limb — a value identified to a
    published source is NOT unattested).
STOPs: extract/test absent (STOP 6); a realized key ≠ its pre-declared value; any k = 1 row moving; a
screen row clearing on any `er/phys` < 1.27 host; the explicit-False path moving a key; wall/RSS beyond
each leg's D60 envelope. COLLISION: you are the only writer on ff-verdicts.json / program-status.json
this window (D62's registration and D58 follow you); SCN lanes write the hindcast namespace only;
scenarios.py — your two lines sit in the D50 block; SCN-WS2a/2b's `federal_ces_*` block and WS-1a's
D34-guard region are not yours. Rules 22 (forecast mode only), 25 (a posture, no ISO's number), 27
(exact bytes, blob-verify every ≥300-line file), 28. Score and register AFTER the final rebase.
EXIT: both acts landed in one PR, every bare key re-solved and registered with its prior, the finding
closed and pushed. Nothing else arms.
```

## D60-R3 — AMENDMENT 1 (r#46): legs 4 and 5 were solved ACROSS the SCN-LOAD growth hunk `d14a7ed0`; date it, re-attribute from the committed ledgers, correct the two provenance strings, solve the ONE earned control, and close — **DISPATCHABLE NOW, to the live D60-R3 session if it is alive, else fresh as D60-R4 from this text (branch `claude/capx-d60r3-completion` at `cdb83016` is the checkpoint either way)**

```
You are the D60-R3 session (or its fresh successor D60-R4) of the capacity-expansion track. Binding
charter: pack §D60-R3 + this Amendment 1 (pack §D60-R3 AM.1). Everything the charter owed is landed on
`claude/capx-d60r3-completion` at `cdb83016` EXCEPT the finding's §5 leg-5 text, §8 and the close — and
this amendment ADDS one re-attribution and one control solve before that close. Nothing here re-opens
a registered key, a determination, a marker or a shard.
DATA PROFILE: pjm (widen to neiso ONLY if you elect the optional NEISO control in step 4b).
MODEL: Opus (the decomposition is pre-declared below to the MW; the control's reading is measured).
BRANCH: `claude/capx-d60r3-completion` — continue it; a fresh session checks it out, does NOT start
from main. Rebase onto origin/main BEFORE step 1 and NOT AGAIN until step 4's solve has exited; the
`exit 90` HEAD guard below is mandatory around the solve.

THE FACT (director r#46 §0aq.1 — verify from the trees, never trust): SCN-LOAD `d14a7ed0` (merged as
#4970 = `ad45b0e4`, 02:19 UTC 2026-09-06) re-derived `DEMAND_GROWTH_RATES` for all six ISOs (PJM
mid.near 0.036 → 0.064645; NEISO 0.031 → 0.054816 and long 0.020 → 0.014850; CAISO 0.028 → 0.032425),
`DATACENTER_ADDITIONS_MW` and `ELECTRIFICATION_LAYERS`. Your §5.0d second-hunk probe (`19473c82`,
01:55 UTC) pre-dates that merge; your final rebase (X-6b, `05968ab9`) admitted it. Leg 4's arm was
solved on `14f860fb` (contains the hunk: `git merge-base --is-ancestor d14a7ed0 14f860fb`); its
control `pjm-t1f-pre-d60` and the D50 arm are both PRE-hunk. Leg 5's `bau-d60` likewise; `bau-d46`
is PRE-hunk. Leg 3 is INERT by measurement (CAISO 2030 peak 54,820.591 MW on both sides). The
pre-declared keys matched because `constants.py` is OUTSIDE the cache key — a matched key is a config
audit, not a G-DRIFT verdict.

STEP 1 — DATE IT IN §5 (zero LP). Add §5.0f "The hunk the rebase admitted": the commit, the merge, the
UTC times of the probe vs the merge, and `git merge-base --is-ancestor` for each of the three legs'
`run_config.json` git.sha. State plainly that §5.0d's "no second hunk" was true at 01:55 and false
after X-6b, and that form-4 differencing against `-pre-d60` is VOID for legs 4 and 5 (rule 29(b)).

STEP 2 — RE-ATTRIBUTE LEG 4 FROM THE COMMITTED LEDGERS (zero LP). From `results/ff-t1f-d45r/pjm`
(control) and `results/ff-t1f-d60/pjm` (arm) `evolution_<year>.json`, read `peak_demand_mw` (P) and
`screen_adequacy_requirement_mw` (R) for 2027–2030; r = R/P. Decompose ΔR = (P_arm − P_ctl)·r_ctl +
P_arm·(r_arm − r_ctl). THE DIRECTOR'S PRE-DECLARED TABLE, which your numbers must reproduce to the MW
or the discrepancy is reported: peak leg +9,806 / +14,789 / +20,121 / +25,990; ratio leg +6,414 /
+6,818 / +7,151 / +7,515 (2027–2030); peak share 60 / 68 / 74 / 78 %. The ratio leg is the ONLY part
the Q44 gates own. Write this into §5's leg-4 text and REPLACE the sentence "the entire rise belongs
to the D48 + D57 gates" with the decomposition. Do not soften the STOP: it fired as written; what
changes is its attribution.

STEP 3 — RE-ATTRIBUTE LEG 5 (zero LP). Same read on `results/ff-t3-neiso-golden/bau-d46` vs
`bau-d60` for 2027/2030/2035/2040/2050: peaks 25,213 / 26,209 / 27,848 / 29,559 / 33,304 vs 24,801 /
25,359 / 26,934 / 28,774 / 32,839 MW. Amend the leg-5 text: "one substantive mechanism" is false as a
description of the difference; the >5 % co2 / gas-generation movements carry the sign of a LOWER
demand world, not of fewer retrofits. P16 stands as a STATUS reading. Keep P14/P15 as written and add
that the retrofit window now carries a demand co-movement.

STEP 3b — CORRECT THE TWO PROVENANCE STRINGS on the board (`program-status.json` `t1f_provenance` for
PJM, and the NEISO golden entry on your branch; `ff-verdicts.json` narrative fields likewise): add
one sentence each — "solved POST-`d14a7ed0` (PJM mid.near 0.064645 / NEISO 0.054816); the `-pre-d60`
prior is PRE-hunk; form-4 differencing is VOID for this row until D65-B re-solves every bare key at
one HEAD". You remain the SOLE writer of both files this window. Bytes only; no determination moves.

STEP 4 — THE ONE EARNED CONTROL (rule 29(b): a LIVE hunk earns a control solve for the years the
screen needs). Solve `pjm-t1f` at HEAD, 2026–2030, with the Q44 gates OFF (`--no-pjm-demand-response-
supply --no-pjm-accreditation-design-vintage`, and the D57 clearing gate off) and `ccs_retrofit_capex_
co2_scaling` at its default — i.e. the D45-R recipe on today's demand table. Pre-declare its cache key
in an Addendum E BEFORE the solve, the way Addendum A did. ~36 min, ~8.8 GB. PRE-DECLARED READING
(director): the arm's I12 reads LESS negative than this control's in every year 2027–2030 (supply rise
+9,092 / +10,276 / +14,303 / +18,000 exceeds the ratio leg in every year). FALSIFIER: any year in which
the same-HEAD control's I12 is LESS negative than the arm's — then and only then does "D48 is not
position-neutral forward" stand, and the director serves the owner card on those rows. Report at full
magnitude either way. This control is a THROWAWAY DIAGNOSTIC under rule 29: registered NOWHERE, and
its bundle DELETED before the PR merges (rule 29(c)); the Addendum E table carries every number.
  HEAD GUARD — wrap the solve:  H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ]
  || { echo "HEAD moved under the solve"; exit 90; }
STEP 4b (OPTIONAL, your call on cost, director recommends SKIP unless D65-B asks): a `bau` golden
control at HEAD (25 yr, ~33 min) for leg 5. Not required: the FC map did not move on status.

STEP 5 — RE-AUDIT AFTER EVERY REBASE (new doctrine, r#46 §0aq.5): before step 4's solve, and again
before the close, `git diff <pre-rebase> <post-rebase> -- src/market_sim scripts/run_*.py` and
classify EVERY hunk INERT/LIVE with reason, `constants.py` first; push the classification before the
solve. The wallclock branch `claude/p1-basis-seed-impl-oby2ka` edits `pipeline/solve.py` and
`lp/model.py` — if it has merged, it is a hunk you classify (backcast callers only, forecast path
byte-identical per its own docstring — VERIFY, do not copy).

STEP 6 — CLOSE: finding §5 (legs 3–5 + §5.0f), §8, the close; open the PR; blob-verify every ≥300-line
file (`FINDING-capx-d60`, both board JSONs, the new `build_forecast_dof_ledger.py`). Rules 13, 19, 21,
22 (no out-of-training year), 24, 25, 27, 28 (no cell moves — you armed nothing new), 29(b)/(c).
EXIT: PR open with §5.0f, the two re-attributions, the corrected provenance strings, Addendum E's
control reading, the control bundle deleted, ruff clean. Its merge releases D65-B, D62's
registration, D58 and D63.
```

## D67 — NOT THIS DESK'S CHARTER: label-collision record (r#45/r#46). `claude/capx-d67-pjm-requirement-operand-18wzjf` / #5012 #5019 #5022 is the PJM published-Reliability-Requirement operand lane (D66 §8 card A), dispatched by another desk. Cite it by branch + PR. Its state at r#46: build + phase 0 complete, matrix discharged, G-DRIFT LIVE, control at HEAD earned, screen (2024–2025, screen year 2025) NOT yet solved. The object this pack had queued under "D67" since r#41 — the steam/oil below-cap offer convention — is **D74** below. Never paste this section.

## D73 — D23's R1 instrument guard + the FC-6 P1 verdict-basis call, narrowed by D72 §6.1 to the ARCHIVED `carbon25` arm (r#46; D23 §8 R1, D72 §5/§6.1) — **ISSUED r#46, zero LP**

```
You are the D73 session of the capacity-expansion track. Binding charter: pack §D73 (this section) +
`FINDING-capx-d23-p1-carbon-sign-2026-09-01.md` §8 R1 (the repair you build) + `FINDING-capx-d72-2026-09-06.md`
§5–§6.1 (the fact that narrows the call). ZERO LP. No solve, no re-solve, no registration.
DATA PROFILE: code
MODEL: Fable (this moves a golden's VERDICT BASIS — a determination consequence, not execution).
BRANCH (suggested; graded by content): claude/capx-d73-fc6-p1-guard — FRESH off origin/main.

THE OBJECT. D23 adjudicated GOLDEN-2's FC-6 P1 "carbon-sign defect" as the INSTRUMENT'S premise being
inverted (rung 0 is the RGGI world for a program ISO and sits ABOVE rung 25) and routed R1: a premise
assertion in the paired checker and the battery scorer — compute `resolve_carbon_price(cfg, y)` for
every solve year from each arm's COMMITTED config, and unless the "high" arm's effective signal ≥
base's in every year, emit a MIS-CONSTRUCTED / vacuous row instead of a scored PASS/FAIL (the FC-6.2
vacuous-evidence lane). ~40–80 lines + tests in `scripts/check_forecast_invariants.py` (the string
"MIS-CONSTRUCTED: high-arm effective carbon ≤ base" already exists at ~L872 — READ what it guards
today before adding a second guard; rule 19 forbids two mechanisms for one phenomenon) and the
battery scorer (`scripts/ff_readiness_battery.py` / `scripts/forecast_verdict.py` — find the one
consumer that writes the P1 row). Strictly evidence-tightening; rules 13/21 admissible (no measured
data, no tunable). D72 §6.1 established that the LIVE golden families are already re-armed off the
mis-constructed pair and ONLY the archived snapshot family `bau-prera-2026-08-31` still carries
`carbon25`. So the call is NARROW, and it is the director's to make on your evidence:

  Q: should the guard RETROACTIVELY reclassify the archived `carbon25`-based P1 FAIL to
     MIS-CONSTRUCTED, given the live golden no longer rests on that pair?

PHASE 0 — READ FIRST, AND STOP IF ANY OF THESE FALSIFIES THE PREMISE: (a) quote the current L872 guard
and state exactly which arms/rows it fires on today (it may ALREADY be R1 in substance — if so, this
lane's build is a test + a cross-reference, and you say so); (b) enumerate every committed FC-6 row on
the board (`ff-verdicts.json`, bare keys only — suffixed keys are preserved baselines, never quote one
as current) and which arm pair each was scored on; (c) for each pair, compute the effective carbon
signal per year from the committed `run_config.json`s (D23's method) and tabulate MONOTONE /
INVERTED. A table with zero INVERTED live rows means the guard's live effect is nil and the whole
question is the archived row — say so.

PHASE 1 — BUILD R1 (if phase 0 leaves a gap): the assertion, the vacuous-row emission, tests for
both branches (monotone pair scores; inverted pair emits MIS-CONSTRUCTED and never PASS/FAIL), a
`--dry-run` that prints the table from phase 0. NO `ScenarioConfig` field, no default, no matrix
cell (rule 28: you test no mechanism). Do NOT touch `ff-verdicts.json` or `program-status.json` —
D60-R3 is their sole writer this window; you REPORT what the guard WOULD write and the director
serves it.

PHASE 2 — THE RECOMMENDATION, three-way and argued, to the director not the board: (i) reclassify
the archived P1 row (a verdict-basis change on a snapshot — state who reads that snapshot and what
changes for them); (ii) leave it, add a dated cross-reference to D23 and D72 (the D23 §8-R3 / D72
precedent: never rewrite another lane's finding); (iii) reclassify only on the next re-score event
that touches the family. Price each in LP (should be zero for all three) and in records touched.
Amend D23's file ONLY by dated cross-reference.

EXIT: FINDING-capx-d73-<date>.md with the phase-0 table, the guard's diff (or the finding that L872
already is R1), tests green, ruff clean, the three-way recommendation, and a §8 stating that nothing
on the board moved. Rules 13, 19, 21, 22, 24, 25, 27 (blob-verify any ≥300-line file you touch —
`check_forecast_invariants.py` is one), 28. Push each phase as it lands.
```

## D74 — the PJM regulated / self-supplied STEAM + OIL below-cap offer convention: the object D61 §4 card (c) named and D62 §9 item 2 widened to oil — the NEW label for what this pack mis-queued as "D67" (r#46) — **CHARTERED r#46, design-first, DISPATCHABLE**

```
You are the D74 session of the capacity-expansion track. Binding charter: pack §D74 (this section) +
`FINDING-capx-d61-2026-09-05.md` §4 card (c) + `FINDING-capx-d62-2026-09-06.md` §5.3 and §9 item 2 +
`DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §3.5 (the offer identity you must not break).
DATA PROFILE: pjm
MODEL: Fable (phase 0 is a DESIGN choice of a market object; the build follows the committed design).
BRANCH (suggested; graded by content): claude/capx-d74-pjm-steam-oil-convention — FRESH off origin/main.
DO NOT cite this as D67: `claude/capx-d67-pjm-requirement-operand-18wzjf` is a different object.

THE OBJECT, as measured. In BOTH D62 arms, to the MW, gas-steam is 8,801.9 MW UNCLEARED and 9.464 GW
economically EXITED — so no offer-side operand of any size (D62 moved the bar for every other class)
touches it. D62 §5.3: PJM's single published "Steam Oil & Gas" class is the one whose bar-to-clearing-
price relationship the published ACR table does not repair; D62 adds OIL to the scope on that ground.
D61 §4 card (c) named the convention itself: regulated / self-supplied steam units in PJM offer BELOW
their going-forward cost (self-supply, FRR, bilateral, must-run designations) — a real market
behaviour under rule 1, not a level. FC-3 grades composition, and D62's own §8 lists 4.137 GW of oil
over-exit at 6.7× actual as a reason it refused its own arm.

PHASE 0 — DESIGN, ZERO LP, committed BEFORE any code: (1) from PJM's own published record already in
`data/raw/capacity-market/` (BRA reports by resource type, FRR/self-supply tables, Manual 18) state
what fraction of the steam and oil UCAP is self-supplied / FRR / must-offer-at-zero in DY 2022/23–
2025/26, by source doc + page; if the published record cannot separate it, STOP and say so (rule 14 —
no proxy). (2) Design ONE mechanism (rule 19) that represents it: the candidates are (a) a sector /
supply-type partition (the D53 sector gate's Sector 1 + self-supply flag, per unit, from EIA-860 +
the FRR list — a published per-unit partition, NO weight) under which such units are price-takers
at $0 and EXEMPT from the merchant exit screen; or (b) D62's own narrower partition alternative —
arm the published bar ONLY for the classes PJM publishes a technology-class default for, holding
steam/oil on their own convention. State which is the market's mechanism and which is a level, and
choose on structure (rule 1), never on FC-3. (3) Pre-declare the sign on FC-3 `retire.total_gw`
(D62 arm 20.144 vs actual 15.062; control 18.702), on unit recall, and on the 2024/25 census
(D62's G6 invariant: the 2024/25 price must not move on the census — carried).
PHASE 1 — BUILD, default-off, one `{iso: bool}` gate in the D57 family, ZERO scalar fields, cache key
registered in the same commit, matrix row + a cell in every ISO shard (rule 28c). PHASE 2 — SCREEN
(rule 29): ONE year, named in the PRECOMMIT as the year the steam/oil UNCLEARED MW is largest in the
D62 arm ledgers (measured, not the biggest residual); minimum span 2024–2025 because year 1 has no
`prior_results`; control = the committed `pjm-2021-2025-realized-t1h-d57-clearing` arm A ONLY after a
hunk-by-hunk G-DRIFT from `5bb70047` (its git anchor — `f0e050e820c1159a` is a CACHE KEY) — and NOTE:
the D67 lane already found that window LIVE (`DEMAND_GROWTH_RATES["PJM"]` moved) so expect to solve a
same-HEAD control for the screen span; classify the wallclock `pipeline/solve.py` seed if merged.
Structural STOP gates only. PHASE 3 — the full 2021–2025 window only if the screen clears.
HEAD GUARD around every solve: H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ]
|| exit 90. Rebase BETWEEN legs, never during; RE-AUDIT the rebase delta before the next leg (r#46
doctrine); a matched cache key is not a G-DRIFT verdict (`constants.py` is outside it).
COLLISIONS: the D67 lane's build is on main (`8bc0feb5`) — `retirements.py`'s requirement seam is
settled; you touch the BAR / offer seam (`resolve_going_forward_bar`, the D57 offer stack), not the
requirement. D75 (VRE ELCC vintage) may run concurrently on `capacity_market.py`'s ELCC registry —
different region; rebase carefully, never resolve a conflict by dropping the other lane's hunk.
Registration / re-score after D60-R3 merges (sole board writer). Nothing arms without a ruling.
EXIT: DESIGN memo, PRECOMMIT (before the first solve), FINDING with phase-0 table, screen gate,
full-window A/B, FC-3 at full magnitude, §8 recommendation. Screen/control bundles DELETED before
merge (rule 29(c)). Rules 1, 13, 14, 19, 21, 22, 24, 25, 27, 28, 29.
```

## D75 — the PJM VRE ELCC delivery-year VINTAGE: D66 §8 card B, the VRE half of the vintage D48 gave the thermal classes (r#46) — **CHARTERED r#46, sign PRE-DECLARED to WIDEN the residual, DISPATCHABLE**

```
You are the D75 session of the capacity-expansion track. Binding charter: pack §D75 (this section) +
`FINDING-capx-d66-2026-09-06.md` §8 card B (+ its §1.2 position definition, matched to four decimals).
DATA PROFILE: pjm
MODEL: Opus (values on disk, zero free parameters, the sign pre-declared; arming returns to the director).
BRANCH (suggested; graded by content): claude/capx-d75-pjm-vre-elcc-vintage — FRESH off origin/main.

THE OBJECT. The model applies PJM's 2026/27-vintage marginal VRE ELCC ratings to EVERY delivery year
(`RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]`, `capacity_market.py` ~L2541–2560: wind 0.41, solar 0.1064),
while PJM's published 2024/25 class-average ratings were wind 0.16 and solar 0.36 fixed / 0.54
tracking. Give the PJM VRE curves the delivery-year vintage axis D48 gave the thermal classes
(`THERMAL_ELCC_CLASS_RATING_BY_ISO`, the `pjm_accreditation_design_vintage` gate — READ how D48 keys
its vintage and use the SAME seam, rule 19), so DY 2024/25 reads the Dec-2021 class-average ratings
and DY ≥ 2025/26 reads the marginal-ELCC ratings already wired. Values from `elcc/pjm/pjm.csv`
(reconcile by test, byte-for-byte, the way D67 reconciled its requirement rows). THE ONE NEW OPERAND
— the fixed/tracking MW split for the pre-reform blend — comes from PJM's own Table 5 mix, source doc
+ page, NEVER chosen; if the table is not in-repo, intake it additively (data-intake skill) and STOP
rather than estimate (rule 14). SCOPE LIMIT, stated not papered over: PJM's ELCC regime BEGAN with the
2024/25 BRA; 2022/23 and 2023/24 sit in a pre-ELCC regime this repo has not intaken — this card covers
2024/25 and later, and the earlier two years are reported as OUT OF SCOPE with the published break
quoted (wind offered 2,595 → 1,608 → 1,396 UCAP on a growing fleet).

PRE-DECLARED SIGN (D66, and this desk): the 2024/25 census moves DOWN 0.6–1.4 GW and the position
residual WIDENS. Under rule 14 that is the point — the accurate input is kept and the wider residual
is the discovered root cause, not a reason to revert. A lane that finds the census moving UP has a
bug, not a result.

PHASE 0 (zero LP): a `fleet_only` rebuild on the D57 arm-A recipe emitting accredited VRE MW by class
for DY 2024/25 and 2025/26 under both vintages — the delta must land inside the pre-declared band
before any solve. PHASE 1: build default-off (gate in the D48 family, zero scalar fields, key
registered, matrix row + six cells). PHASE 2 — SCREEN (rule 29): screen year = the DY where the
VRE accredited delta is largest in phase 0 (expected 2024/25 → solve span 2023–2024, year 1 has no
`prior_results`); control at HEAD (the D67 lane found the arm-A window LIVE on `DEMAND_GROWTH_RATES`
— form 4 is void, do not re-litigate it); structural gates: identity (accredited VRE MW = phase-0
arithmetic to the MW), confinement (thermal / storage / requirement byte-identical), no non-target
load-bearing flip. PHASE 3: full 2021–2025 window if the screen clears. HEAD GUARD around every
solve (H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90). Rebase
BETWEEN legs, never during; RE-AUDIT the rebase delta before the next leg; a matched cache key is not
a G-DRIFT verdict. COLLISIONS: the D67 lane (requirement seam) and D74 (bar/offer seam) may be live on
PJM — different regions of `capacity_market.py` / `retirements.py`; never drop another lane's hunk.
Registration after D60-R3 merges. Nothing arms without a ruling.
EXIT: PRECOMMIT before the first solve; FINDING with phase-0 table, screen gate, full-window A/B, the
position at full magnitude (both the like-for-like whole-RTO frame and the RPM comparator, per D66
§1.2), §8 recommendation. Screen/control bundles deleted before merge. Rules 1, 13, 14, 19, 21, 22,
24, 25, 27, 28, 29.
```

## D76 — the T1-H capacity-screen PEAK is de-grown from the growth path instead of read from the measured hindcast load — program-wide, all six ISOs (r#46; D67 FINDING §2.2 + §8(a)) — **CHARTERED r#46; PHASE 0 (zero LP, six-ISO census) DISPATCHABLE NOW; build + A/B only after phase 0 lands**

```
You are the D76 session of the capacity-expansion track. Binding charter: pack §D76 (this section) +
`FINDING-capx-d67-2026-09-06.md` §2.2 (the mechanism, quoted from `runner.py`) and §8(a) (the route).
PHASE 0 IS ZERO LP AND IS THE WHOLE LANE UNTIL THE DIRECTOR RELEASES PHASE 1.
DATA PROFILE: code for phase 0 (the census reads committed bundles + code); the ISO phase 1 names.
MODEL: Opus (the predicate is already read and quoted; phase 0 is a census; arming is the director's).
BRANCH (suggested; graded by content): claude/capx-d76-t1h-screen-peak — FRESH off origin/main.

THE PREDICATE, READ BY THE D67 LANE (r#45 doctrine: stated as a precondition of issuing, not as your
first step — you VERIFY it, you do not discover it): `runner.py` builds the capacity screen's seam
peak at the top of the year loop as `_scale_demand(base_demand, wx_config, year)` + `add_load_layers`
— the GROWTH path — and only the LP's own `year_demand`, further down, takes the measured hindcast
branch. With `weather_year=2024`, `crossover_solve_year_weather=False`, `demand_growth_vintage=None`,
`_scale_demand` compounds and DE-GROWS 2024's measured load across 2024↔Y. Measured by D67 on PJM at
zero LP: screen peak −10,819 / −7,574 / −3,977 / 0 / +4,386 MW vs the committed arm A across 2021–
2025 at HEAD's 6.46 % rate — i.e. the 2021–2023 screen peaks sit 10.8 / 7.6 / 4.0 GW BELOW the load
PJM actually served, while the LP dispatches the measured load in the same year. The director's own
census (r#46): ALL 24 committed hindcast bundles, all six ISOs, run `weather_year=2024`, solve years
2021–2025, `demand_growth_vintage=None` — so the defect reaches every T1-H recipe in the repo. Under
rule 14 the measured load is the accurate input; a synthesized historical peak is an estimate that
was silently compensating for nothing and mis-stating everything downstream of the seam (the
reliability floor, the reserve-margin build backstop, the CR-1 position, FC-1 I7/I12, FC-3).

PHASE 0 — THE CENSUS (zero LP), one table: for each of the six bare T1-H recipes (and the crossover
recipes, `weather_year=2025`), per solve year: the screen peak the seam produces at HEAD (reuse
`docs/handoffs/d67/gdrift_peak_probe.py` generalized to six ISOs — it reproduces the runner's preamble
and seam exactly; extend, do not fork), the MEASURED hindcast peak from the same bundle's demand
input, the delta in MW and %, and — from the committed evolution ledgers — the screen requirement
that peak fed. Then, per ISO, the year of LARGEST footprint (that is the screen year for phase 1,
fixed here before any solve) and whether the sign of the position error the delta implies matches
the FC-1 I7/I12 residual on the board (a HIT/MISS per ISO, reported either way — this is NOT a gate,
it is the reading that tells the director whether the defect explains a board row). State which
ISOs D67 (if armed) makes in-table-moot for the REQUIREMENT (PJM only, in-table DYs) and note the
floor/backstop still read the peak everywhere.

WHAT PHASE 1 WILL BE (do NOT build it in phase 0): one gate, default-off, `capacity_screen_peak_
measured_hindcast: bool` (or the name the code's own idiom prefers), under which — in hindcast mode
ONLY (forecast years have no measured load; the growth path stays THE forecast methodology, rule 13's
forward test) — the seam peak is the measured year's peak. Rule 19: it replaces the de-grown peak, it
does not stack on it; enumerate every consumer of the seam peak first. Zero scalar fields, key
registered, matrix row + six cells. Screen (rule 29) on the ISO + year phase 0 names, control at HEAD
(every committed T1-H control is PRE-hunk on `DEMAND_GROWTH_RATES`; form 4 is void everywhere), STOP
gates structural: the arm's screen peak = the measured peak to the MW; every non-peak operand
byte-identical; no non-target load-bearing flip. Registration after D60-R3 merges. Arming is an owner
card — this changes every hindcast bundle's screen operand and therefore every FC-1/FC-3 T1-H row.

COLLISIONS: read-only in phase 0 (nothing to collide with). Phase 1 touches `runner.py`'s preamble —
the wallclock branch `claude/p1-basis-seed-impl-oby2ka` is on `pipeline/solve.py` / `lp/model.py`,
not the preamble, but classify it if merged. The D67 lane owns the requirement resolver; you own the
peak — do not edit `gross_adequacy_requirement_mw`.
EXIT (phase 0): FINDING-capx-d76-<date>.md §§1–3 with the six-ISO census table, the per-ISO screen
year fixed, the HIT/MISS reading, and a §4 that names the phase-1 seam and every consumer of it. Push
it; the director releases phase 1 or serves the card. Rules 13, 14, 19, 21, 22 (2021–2025 hindcast
only; no out-of-training scoring), 24, 25, 27, 28, 29.
```

## D60-R4 — the D60-R3 AMENDMENT 1, re-issued FRESH because D60-R3 merged with its finding CLOSED and the growth hunk unrecorded (r#46 am.1) — **ISSUED r#46 am.1, DISPATCHABLE NOW**

```
You are the D60-R4 session of the capacity-expansion track. Binding charter: pack §D60-R3 AM.1 (the
amendment text, VERBATIM — every step, the pre-declared decomposition table, the HEAD guard, the
control's pre-declared reading and falsifier) with these changes and no others:
 (1) START FRESH off origin/main on branch claude/capx-d60r4-growth-hunk-attribution. D60-R3 is
     MERGED (#5038) and its finding `FINDING-capx-d60-2026-09-05.md` is CLOSED at `15631b8c`. You are
     the same lane's successor, so you MAY amend §5.4 and §5.5 — by DATED CORRECTION BLOCKS appended
     in place under each ("**Correction, D60-R4 <date>:** …"), NEVER by rewriting the original
     sentences; the record must show what was believed and when. §5.0f is new text.
 (2) The two provenance strings (STEP 3b) are on main now, in `program-status.json` (PJM
     `t1f_provenance`; the NEISO golden entry) and `ff-verdicts.json` narratives. You are the SOLE
     writer of both files for this window (D60-R3's lock passes to you); D63 and D65-B are told so.
 (3) Before the control solve (STEP 4), classify the FULL rebase-free drift window `15631b8c..HEAD`
     hunk by hunk — it includes #5033 (`pipeline/solve.py` / `lp/model.py`, the P1 basis seed:
     VERIFY its forecast-path byte-identity from the code, do not copy its docstring) — and push the
     classification before the solve. A matched cache key is NOT a G-DRIFT verdict.
 (4) EXIT: one PR — §5.0f, the two dated corrections, the provenance strings, Addendum E with the
     control's I12 rows at full magnitude, the control bundle DELETED (rule 29(c)), ruff clean, every
     ≥300-line file blob-verified. If the falsifier fires (the same-HEAD control's I12 LESS negative
     than the arm's in any year), say so in the PR title: the director serves the D48 card on it.
DATA PROFILE: pjm. MODEL: Opus. Rules 13, 19, 21, 22, 24, 25, 27, 28 (no cell moves), 29(b)/(c).
```

## D63 — the MISO + CAISO curated DOF-identification rows under Q37's limb, plus D62's suffixed registration (r#46 am.1; queued-named since r#40; released by D60-R3's merge) — **CHARTERED r#46 am.1, DISPATCHABLE, records-only**

```
You are the D63 session of the capacity-expansion track. Binding charter: pack §D63 (this section) +
owner ruling Q37 (capx ledger §3, r#34: a follow-up lane may author an attestation iff PRE-DECLARED
before authoring, attestation row only, artifact-only re-score) + `FINDING-capx-d60-2026-09-05.md`
§8 (the six rows D60-R3 wrote and the two negatives it routed here) + `PREDECL-capx-d60-2026-09-05.md`
Addendum D (the shape of a pre-declaration for this work). ZERO LP. No solve, no re-solve.
DATA PROFILE: code
MODEL: Opus (pre-declared, artifact-only; FC-7 is the only row that may move).
BRANCH (suggested; graded by content): claude/capx-d63-miso-caiso-dof-rows — FRESH off origin/main.
COLLISION: D60-R4 (if live) is the sole writer of `ff-verdicts.json` / `program-status.json` until
its PR merges — check `git log origin/main --grep=D60-R4` and open branches; if it is live, do steps
1–2 now and hold step 3's board write until it merges, rebasing between (never during) steps.

STEP 1 — PRE-DECLARE (an Addendum in a new PREDECL-capx-d63-<date>.md, pushed BEFORE any row is
written): for each of the SEVEN fields — MISO `entry_vre_capacity_revenue`, `entry_vre_zone_selection`,
`miso_rps_compliance_regions`, `miso_clean_tier_rows`, `retirement_sector_gate`; CAISO
`negative_renewable_offers`; and any other `unattested` entry the committed `miso-t1f` / `caiso-t1f`
`dof_ledger.json` carries — name the COMMITTED identification source (the FINDING / design doc that
landed the field and its value or its posture; the D53 finding for `retirement_sector_gate`, the
CAISO backcast keeper record for `negative_renewable_offers`, and so on), the expected FC-7 reading
after the row exists, and the expected determination (which must NOT move except through FC-7).
A field whose identification you cannot cite from a committed document gets NO row — it stays
UNIDENTIFIED and you say why (rule 21: the ledger REPORTS identification, it never supplies it).
STEP 2 — WRITE THE ROWS in `scripts/build_forecast_dof_ledger.py::CURATED_IDENTIFICATIONS`, keyed
(ISO, field), `requires: "iso-registry"`, source quoted per row, in the shape of D60-R3's six.
Test: the existing test module for that file, extended. ruff clean.
STEP 3 — ARTIFACT-ONLY RE-SCORE of the bare `miso-t1f` and `caiso-t1f` (same bundle, same bytes, same
key; only ledger labels change) → register in place; FC-7 must be the ONLY row that moves, and any
other movement is a STOP-and-report. THEN, in the same PR and window, register D62's arm on the board
SUFFIXED (`pjm-t1h-d62-pubbar`, DO-NOT-ARM per D62 §8; the bare `pjm-t1h` is untouched) — the
registration D62 withheld behind D60-R3, with D62's own verdict text as the provenance string.
EXIT: PREDECL pushed first; FINDING-capx-d63-<date>.md with the per-field source table, the two
re-scores' before/after, D62's registration line; ruff clean; blob-verify `ff-verdicts.json`,
`program-status.json`, `build_forecast_dof_ledger.py`. Rules 21, 22, 24, 25 (rows keyed (ISO, field),
never ("*", field)), 27, 28 (no cell moves — you test no mechanism).
```

## D77 — the CCS retrofit EMISSION-RATE SEAM: `ccs.py:572`'s capture write does not reach the dispatch fleet (r#46 am.1; SCN-WS2b §5.3 / §8 item 1, routed as a priority signal by SCN-DESK r#9 — Stage A-POLICY holds on it) — **CHARTERED r#46 am.1, DISPATCHABLE NOW; a DEPENDENCY of D65-B's batch**

```
You are the D77 session of the capacity-expansion track. Binding charter: pack §D77 (this section) +
`FINDING-scn-ws2b-2026-09-06.md` §5.3 (the measurement) and §8 item 1 (the route) + `FINDING-capx-d50-
2026-09-04.md` / `FINDING-capx-d65-2026-09-05.md` (the retrofit ledgers whose CO2 this mis-states).
DATA PROFILE: neiso (the reproduction and the screen are NEISO; the fix is ISO-agnostic code).
MODEL: Opus (the defect is measured and the fix is a construction repair with zero DOF; the
re-scores and every determination consequence route back to the director).
BRANCH (suggested; graded by content): claude/capx-d77-ccs-emission-rate-seam — FRESH off origin/main.

THE DEFECT, MEASURED BY SCN-WS2b (verify, never assume): `model/capacity_evolution/ccs.py` ~L565–575
executes three in-place writes on a retrofitted generator — `heat_rate × (1 + hr_penalty)`, `vom +=
adder`, `emission_rate_co2 × (1 − ccs_retrofit_capture_rate)`, `fuel_type = "gas_cc_ccs"`. Tracked
through the cached `FleetContext` for one NEISO unit across its own 2028 retrofit (BAU, key
`5e2c52ea81694c10`): heat rate 7.5101 → 8.4113 ✓, fuel `gas_cc_ccs` ✓, emission rate 0.3745 → 0.3745 ✗;
all six units of the 2028 cohort; NEISO 2030 `gas_cc_ccs` fleet-wide 0.4149 t/MWh vs unabated gas_cc
0.4663 on a 47-unit / 9.0 GW class. Leading candidate: a plant-keyed restoration of the measured CEMS
rate DOWNSTREAM of evolution (`plant_emission_rates_v2` or its successor) that overwrites the converted
unit's rate — which also explains why the rate did not follow the 12 % heat-rate rise. It is a DISPATCH
defect (carbon adder = `emission_rate × carbon_price`) and an accounting one, and it inverts NEISO's
headline CO2 under CES.

PHASE 0 — ZERO LP, and STOP if the premise fails: (1) reproduce the WS2b table from the committed
NEISO BAU bundle's cached fleet (no solve); (2) trace, in code, EVERY assignment to `emission_rate_co2`
downstream of `apply_ccs_retrofit` (grep `emission_rate_co2` across `src/market_sim/`; read the
CAMPD-history rate derivation the CLAUDE.md "Forecast vs backcast" paragraph describes) and name the
one that overwrites the converted unit — quote the lines; (3) state the semantics the repair must
preserve under rule 13: the forward-year rate for an EXISTING unit is the multi-year CAMPD-derived
measured rate (admissible), and a RETROFITTED unit's rate is THAT rate × (1 − capture) — the measured
input still enters, the capture applies on top; a converted unit is never silently returned to its
uncaptured rate. If the overwrite is instead in the FleetContext cache (a stale rate carried across
years), say so — the fix is then a cache-invalidation seam, not a rate seam.
PHASE 1 — THE FIX, one mechanism (rule 19): apply the capture at the point the measured rate is
restored (or exempt converted units from restoration and apply it once) — enumerate both, choose on
structure, write it, and add the test WS2b's table implies (a unit's rate across its retrofit year:
captured, and following the heat-rate rise if the derivation is heat-rate-linked). This is a BUG FIX
with zero DOF and no new `ScenarioConfig` field: no gate, no default, no matrix row — but it is
SOLVE-AFFECTING for every forecast year ≥ `ccs_retrofit_available_year` (2028), so the cache epoch
ledger in `src/market_sim/results/cache.py` gets its entry and every affected bare key's re-resolution
is pre-declared in a PRECOMMIT BEFORE any solve. Every backcast, hindcast and crossover horizon is
byte-identical by construction (nothing retrofits before 2028) — assert it with the persisted-identity
tests, not by argument.
PHASE 2 — THE SCREEN (rule 29): ONE leg, `neiso-t1f` 2026–2030 (~8 min; the largest measured
footprint — 8.8 GW retrofits by 2030), control = the committed bare `neiso-t1f` ONLY after a hunk-by-
hunk G-DRIFT of its window (it is PRE-hunk on D55, on `d14a7ed0` and on #5033 — expect form 4 VOID and
a same-HEAD control, which is the honest comparison anyway). Structural STOP gates only: converted
units' `emission_rate_co2` = uncaptured × (1 − capture) to the digit; heat rate, VOM, fuel_type
byte-identical to the control; NO unit outside the retrofit cohort moves its rate; total retrofit MW
within the D50/D65 band (the fix moves dispatch and CO2, not the screen's capex arithmetic — if the
retrofit SET moves, say by how much and why: the carbon adder now differs for converted units, which
CAN re-order the merit order, and that is a real effect, not a STOP). Report the NEISO 2030 CO2 and
`gas_cc_ccs` generation deltas at full magnitude. HEAD GUARD around the solve: H0=$(git rev-parse
HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. Rebase BETWEEN legs, never during;
re-audit the rebase delta before the next leg.
WHAT YOU DO NOT DO: no re-solve of any other bare key (D65-B's batch does that, at one HEAD, carrying
your fix — that is WHY you land first), no board byte (`ff-verdicts.json` / `program-status.json`
belong to D60-R4 / D63 this window; you REPORT what the re-scores would move), no GOLDEN-3 re-solve
(D65-B's batch), no keeper, marker, shard or freeze. The screen bundle and any control are DELETED
before merge (rule 29(c)); the FINDING carries every number.
EXIT: FINDING-capx-d77-<date>.md with the phase-0 reproduction and the quoted overwrite, the fix's
diff and tests, the cache-epoch entry, the PRECOMMIT'd key list, the screen table, and a §8 BLAST
RADIUS: every committed forecast bundle with a non-empty retrofit ledger (from D50 §6.2 / D60 §8-blast-
radius's census), its retrofit MW, and therefore which FC-4 / FC-5 co2 rows and which FC-6 battery
arms are mis-stated — as a table for D65-B's batch and the director's re-score card, never as an act.
Rules 13, 14, 19, 21, 22, 24, 25, 27 (blob-verify `ccs.py` and any ≥300-line file), 28, 29.
```

## D72 — LABEL SPENT TWICE (record). §D72 above is the carbon-floor blast radius (LANDED r#45). `claude/capx-d72-prehunk-resolves-e8naqn` (#5067/#5113) is ANOTHER DESK'S lane on D60-R3 §9's seven residue keys — cite by branch. Its result: four keys PROVED INERT against D55 at zero LP (permanent); leg 1 `neiso-t1f` fired STOP 3, bisected to SCN-LOAD `DEMAND_GROWTH_RATES["NEISO"]["low"]["near"]` 0.007 → 0.004009; every forecast row on the board is stale against HEAD on the demand axis; three keys (`neiso-t1f`, `miso-t1h`, `neiso-t1h`) need a re-based charter — QUEUED here behind D65-B's batch (t1f) and D76 phase 0 (t1h). Never paste.

## D80 — declare the 8 capx run ids' KNOWN invariant FAILs in `frontend/data/hindcast/invariant-failures.json` (r#47; the Y-24 ratchet is RED on `main`; SCN-FIX1 covers the SCN ids and leaves these to this desk) — **ISSUED r#47, records-only, DISPATCH FIRST**

```
You are the D80 session of the capacity-expansion track. Binding charter: pack §D80 (this section) +
audit lane Y-24's ratchet (`scripts/check_forecast_invariants.py --sidecar-dir`, wired into
`.github/workflows/ci.yml` — read the ratchet's own docstring and the `--failure-ledger` contract
before writing a row) + the SCN-FIX1 charter (scenario-desk ledger §5, r#10) which writes the SAME
file for the 17 SCN ids and names "the 8 capx ids" as this desk's. ZERO LP, records only.
DATA PROFILE: code
MODEL: Opus (a declaration is a records act with a citation per row; nothing is re-scored).
BRANCH (suggested; graded by content): claude/capx-d80-invariant-declarations — FRESH off origin/main.

WHY: `check_forecast_invariants.py --sidecar-dir` reads EXIT 1 on `main` (measured r#47 on a container
with the stack installed — `pip3 install --ignore-installed PyYAML -r requirements.txt` if `import
numpy` fails). A registered run that FAILs an invariant must declare it in
`frontend/data/hindcast/invariant-failures.json` (id → idents → the finding it belongs to) so a NEW
failure cannot land silently. These capx ids are undeclared and EVERY one is a KNOWN, DOCUMENTED
reading — the declaration is the missing row, not a new finding:
  neiso-2026-2050-t3-golden3-d60                 I3        (D60-R3 §5.5: FC-1 FAIL (I3), P16 HIT — the golden's standing I3)
  pjm-2026-2030-d60-arm                          I12, I7   (D60 §5.4 + Addendum E.4: the STOP that fired and was re-attributed)
  pjm-2021-2025-realized-t1h-d45                 I7        (D45 finding — the L1 pool)
  pjm-2021-2025-realized-t1h-d45r                I7        (D45-R re-measure)
  pjm-2021-2025-realized-t1h-d57-clearing        I7        (D57 §3 / the arm A ledger D66 reproduces)
  pjm-2021-2025-realized-t1h-d62-pubbar          I7        (D62 §8 DO-NOT-ARM; registered suffixed by D63)
  nyiso-2021-2025-realized-t1h-d45r-curveon      I7        (D45-R NYISO curve-on leg)
  pjm-2026-2026-scn-ws4-probe-t0-load-hi         I7        (a SCN campaign id — SCN-FIX1's, NOT yours, unless SCN-FIX1 has
                                                            landed without it; then declare it with its SCN finding cited and say so)
STEP 1 — RUN THE RATCHET at HEAD, paste its list into the PRECOMMIT/FINDING, and reconcile it against
the eight above: an id on the list not named here, or named here and not on the list, is reported,
never silently added or dropped. STEP 2 — for each id, open the cited finding and QUOTE the sentence
that states the invariant reading (id → idents → finding path + section). A FAIL you cannot cite from
a committed finding gets NO row and a report line instead (a declaration is not a place to invent a
reason). STEP 3 — write the rows in the file's existing shape (read the SCN rows if SCN-FIX1 has
landed; match their schema exactly; if it has not landed, write yours and expect to rebase onto
theirs — NEVER resolve a conflict by dropping their rows). STEP 4 — re-run the ratchet: the capx ids
must be gone from its list; whatever remains is SCN-FIX1's and is reported by id. ruff clean.
WHAT YOU DO NOT DO: no re-score, no registration, no sidecar edit, no board byte
(`ff-verdicts.json` / `program-status.json` are D65-B's this window), no verdict text anywhere.
EXIT: FINDING-capx-d80-<date>.md (one page: the ratchet before/after, the row table with quotes), the
JSON rows, PR opened. Rules 22 (nothing scored), 24, 27 (blob-verify the JSON if ≥300 lines), 28 (no
mechanism, no cell).
```

## D75-R — the PJM VRE ELCC delivery-year vintage, RE-CHARTERED on D75's own §8: four-vintage intake FIRST, the split RULED (option 1), THREE delivery years, per-year SIGN gates (r#47) — **CHARTERED r#47, DISPATCHABLE**

```
You are the D75-R session of the capacity-expansion track. Binding charter: pack §D75-R (this section)
+ `FINDING-capx-d75-2026-09-06.md` (§1 the superseded ratings; §2 the missing operand; §3 the per-year
table and bracket; §5 the 2025/26 gap; §6 the routes; §8 the recommendation — YOUR spec) + its
PRECOMMIT §6 (the pre-declared per-DY signs, recorded before any lane measures against them) + D66 §8
card B (the origin). DATA PROFILE: pjm. MODEL: Opus. BRANCH (suggested): claude/capx-d75r-pjm-vre-
elcc-vintage — FRESH off origin/main.

DIRECTOR RULINGS THAT BIND THIS LANE (r#47 §0ar.1): (R1) the fixed/tracking split = D75 §8 option (1):
carry PJM's OWN published Table-5 mix (12.01 % fixed) as a documented cross-vintage reconciliation
under rule 14's misalignment exception — a published PJM number on the wrong vintage, stated as such
in the code comment and the finding — with D75 §3's bracket recorded as its sensitivity; option (2)
(EIA-860 `Fixed Tilt?` / `Single-Axis Tracking?` derivation) is a SEPARATE data-intake card, not this
lane's; NEVER any split sized to the position residual or backed out of PJM's cleared solar UCAP
(rule 13). (R2) scope = THREE delivery years, 2023/24 · 2024/25 · 2025/26; 2022/23 and earlier out of
scope, stated. (R3) the phase-0 gate is PER YEAR and on the SIGN (DOWN in every in-scope year), never
on a magnitude band — D75 §3's table replaces the superseded band.

STEP 1 — THE INTAKE FIRST (D75 §6 item 1; `data-intake` skill; additive; no code, no gate): relabel
the Dec-2021 tranche of `data/raw/capacity-market/elcc/pjm/pjm.csv` PRELIMINARY / SUPERSEDED; add the
Dec-2023 FINAL 2024/25 set (wind 0.21, solar 0.33 fixed / 0.50 tracking), the 2023/24 set (posted
2021-12-16), and the 2025/26 3IA set (38 / 10 / 14), source doc + page per row; reconcile by test,
byte-for-byte, the way D67 reconciled its requirement rows. STOP if any set cannot be cited to a
primary PJM document. STEP 2 — THE BUILD: the delivery-year vintage axis on
`RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]` through D48's OWN vintage seam (read how
`pjm_accreditation_design_vintage` keys the thermal vintage and reuse it — rule 19; if a second key
is unavoidable, say why), default-off gate in the D48 family, zero scalars beyond the ruled published
mix, key registered, matrix row + six cells. STEP 3 — PHASE 0 (zero LP): `fleet_only` on the D57
arm-A recipe emitting accredited VRE MW by class per DY under both vintages; the SIGN gate per year
(D75 §3: 2023/24 ≈ −755, 2024/25 ≈ −333, 2025/26 ≈ −148 MW at PJM's mix — report the magnitudes,
gate on the signs). STEP 4 — SCREEN (rule 29): screen year = the DY with the largest phase-0
footprint (expected 2023/24 → span 2022–2023; year 1 has no `prior_results`); control at HEAD (form 4
is void on PJM — D67 measured it; the D60-R4 / D74 / D67 solves have all run same-HEAD controls, do
the same); structural gates: identity (accredited VRE = phase-0 arithmetic to the MW), confinement
(thermal / storage / requirement byte-identical), no non-target load-bearing flip. STEP 5 — the full
2021–2025 window if the screen clears; the position at full magnitude on BOTH frames (D66 §1.2).
Also route, do not fix: D75 §6 item 3 (`evolution_2022.json` lacks the adequacy block that 2021 and
2023–2025 carry).
HEAD GUARD around every solve: H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ]
|| exit 90. Rebase BETWEEN legs, never during; re-audit the rebase delta hunk by hunk before the next
leg; a matched cache key is NOT a G-DRIFT verdict. COLLISIONS: D74 (bar seam, `retirements.py`) and,
if Q52 arms it, the D67 arming leg (`iso_configs._pjm_config`) — different regions; D65-B is the sole
board writer until its batch lands, so registration/re-score waits on it. Nothing arms without a
ruling. Screen/control bundles DELETED before merge (rule 29(c)).
EXIT: PRECOMMIT before the first solve (carrying the per-year signs verbatim from D75's PRECOMMIT
§6), the intake PR (may merge first), FINDING with phase-0 table, screen gate, full-window A/B,
§8 recommendation. Rules 1, 13, 14, 19, 21, 22, 24, 25, 27, 28, 29.
```

## D78 — the sector-gate / capacity-clearing seam: a sector-1 unit must still OFFER (D58 §6 reading 1), so the offer stack is decoupled from the screen candidate set (r#47; CONDITIONAL on owner card C-21 / Q53 = READING 1) — **CHARTERED r#47, DISPATCH ONLY IF Q53 RULES READING 1** — **Q53 RULED READING 1 (2026-09-06, r#47 am.1): CONDITION MET, RELEASED — dispatch AFTER D74's screen lands (adjacent `retirements.py` region); the PRECONDITION line inside the prompt is satisfied.**

```
You are the D78 session of the capacity-expansion track. Binding charter: pack §D78 (this section) +
`FINDING-capx-d58-2026-09-06.md` §3 (the seam at the line: `retirements.py:2856` builds the sell-offer
stack from the screen's `margins`, `:3199` empties it through `exempt_unit_ids`, `:2872` computes
`price_takers_mw` as the residual) and §6 (the two readings) + `DESIGN-capx-d53-sector-gate-2026-09-05.md`
§1.8 (the interaction claim D58 refutes) + `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §3.5 (the
offer identity). PRECONDITION: owner ruling Q53 = READING 1 recorded in the capx ledger §3; otherwise
STOP and say so. DATA PROFILE: pjm. MODEL: Fable (a market-rule design choice with a clearing-price
consequence). BRANCH (suggested): claude/capx-d78-sector-gate-offer-seam — FRESH off origin/main.

THE OBJECT. Under D58's arm 34,172.4 MW of sector-1 capacity stopped submitting a net-ACR sell offer
and became $0 price-taker supply, `n_offers` 1,370 → 1,000, and PJM's 2022 clearing price fell 67.76 →
61.21 $/MW-day (−9.67 %), pushing 41 merchant rows (2,910.2 MW) under the bar. PJM's RPM must-offer
requirement says a rate-based existing unit IS in the stack, at its cost-based (net-ACR) price. One
filter (`exempt_unit_ids`) is doing two jobs — exit candidacy AND capacity offering — a rule-19
violation D58 discovered and did not patch.
PHASE 0 — DESIGN, zero LP, committed BEFORE code: (1) state the market rule with the Manual 18 /
tariff citation (must-offer; who may be excused; what a cost-based offer is); (2) design ONE change:
the clearing path builds its stack from the FULL accredited fleet's margins, and the sector gate
removes units from the EXIT decision only — enumerate every consumer of `exempt_unit_ids` and of
`margins` so the decoupling touches one seam; (3) pre-declare: with the gate armed AND the seam fixed,
`n_offers` returns to the control's 1,370, `price_takers_mw` to the control's, the 2022 clearing
price to within the D57 settlement tolerance of the control's 67.76, and the failing pool shrinks by
EXACTLY the 3,476.5 MW of sector-1 rows (D58's measured partition) — no merchant row changes state.
(4) State whether the seam is reachable by ANY other exemption channel (step-0 confirmed exits,
step-1 filed dates, retrofit exemption — does an exogenously-exiting unit still offer in its exit
year? cite the rule). PHASE 1 — build behind D58's existing gate (no new field if the decoupling is
the gate's correct semantics — say so; if a second gate is needed, rule 24/28 apply: key registered,
matrix row + six cells). PHASE 2 — SCREEN (rule 29) on D58's own screen span (2021–2023, the 2022
screen), three legs at HEAD: control-P (gate off), D58's arm (gate on, seam as built — reproduces
D58's 566.3 MW to the MW or STOP), the repaired arm; structural STOP gates = the phase-0 identities.
PHASE 3 — the full 2021–2025 window if the screen clears; PJM's `retirement_sector_gate` cell moves
from `O` to the measured letter; the arming recommendation pre-stated as D58 §5's flip condition.
HEAD GUARD around every solve; rebase BETWEEN legs, re-audit the delta; a matched key is not a
G-DRIFT verdict. COLLISIONS: `retirements.py`'s clearing path is ADJACENT to D74's bar seam — do not
dispatch until D74's screen has landed (r#47 §0ar.4), rebase onto it, never drop its hunk; D65-B is
the sole board writer until its batch lands. Bundles deleted before merge. Nothing arms without a
ruling. Rules 1, 13, 14, 19, 21, 22, 24, 25, 27, 28, 29.
EXIT: DESIGN memo, PRECOMMIT, FINDING with the three-leg table, the D53 §1.8 claim corrected by dated
cross-reference (never rewritten), §8 recommendation.
```

## D79 — the cache key is not a staleness detector (twice demonstrated: D55's ordering hunk, SCN-LOAD's constants): a SOLVE-SURFACE FINGERPRINT in the key — design phase 0 (r#47; D72-prehunk §6.4, D77's epoch entry "NO KEY MOVES, AND THAT IS THE HAZARD") — **CHARTERED r#47, PHASE 0 (zero LP, design only) DISPATCHABLE**

```
You are the D79 session of the capacity-expansion track. Binding charter: pack §D79 (this section) +
`FINDING-capx-d72-prehunk-2026-09-06.md` §6 items 1 and 4 + `src/market_sim/results/cache.py`'s epoch
ledger (read every entry, especially 2026-08-31 and 2026-09-06b, and the "why a denylist and not an
epoch bump" note) + capx D24 / D24-R (the last cache-key repair; the (c′) `is_cached` config-equality
refusal) + `FINDING-capx-d60-2026-09-05.md` §8-blast-radius. PHASE 0 IS A DESIGN MEMO, ZERO LP, NO
CODE. DATA PROFILE: code. MODEL: Fable (what belongs in the key is an adjudication with program-wide
consequences). BRANCH (suggested): claude/capx-d79-solve-surface-fingerprint — FRESH off origin/main.

THE DEFECT, measured twice. `cache_key()` hashes the resolved `ScenarioConfig` — not `constants.py`,
not the solve-path source. capx D55's `_floor_retention_merit` reordering moved every forecast
bundle's exit set at an unchanged key (found by D65 §3c); SCN-LOAD `d14a7ed0` re-derived
`DEMAND_GROWTH_RATES` / `DATACENTER_ADDITIONS_MW` / `ELECTRIFICATION_LAYERS` and moved every T1-F peak
at an unchanged key (found by D67, D60-R4 and the D72-prehunk lane, each by accident of re-solving);
D77's `Generator` attribute repair moved CO2 −48 % at an unchanged key. Consequence: a stale bundle at
a valid key is served as current (rule 26 in its cache form — a re-armable wrong answer), and the
board's 33 forecast rows are all stale against HEAD with nothing on the key saying so.

PHASE 0 — THE DESIGN MEMO, four questions answered with evidence, no code: (1) INVENTORY — every
`constants.py` table and every `*_BY_ISO` registry the FORECAST solve path reads (demand shape,
growth, DC/electrification layers, ELCC curves, capacity-market tables, retirement thresholds, CCS
constants, …) — by grep of the import graph, not from memory; classify each as solve-affecting or
reporting-only. (2) THE MECHANISM — compare: (a) a `constants_fingerprint` = hash of the canonical
JSON of the solve-affecting tables, appended to the key (moves the key exactly when a table moves;
keeps the key stable across pure-code refactors); (b) a solve-path source-tree hash (moves on EVERY
code change — every refactor invalidates every bundle; measure how often that would have fired over
the last 30 days from `git log`); (c) the existing human-read epoch ledger + denylist, made
mechanical (an epoch id in the key bumped by policy); (d) a hybrid — (a) automatically plus (c) for
code hunks. For each: what it would have caught among the three incidents, what it invalidates
spuriously, and the cost to every committed bundle and every pinned key in
`tests/regression/test_persisted_identity.py`. (3) THE BLAST RADIUS of adopting each — which
committed keys move, what the `-pre-*` prior convention becomes, and whether the D65-B batch (which
re-solves every bare key at one HEAD) is the natural moment to land it (one re-key event, Q47's
logic). (4) RECOMMEND ONE, with the phase-1 build spec and its tests, as a director card if it moves
keys program-wide (it will). Rules 24 (no off-registry knob — the fingerprint is derived, never
set), 26, 27 (`cache.py` and `scenarios.py` are ≥300 lines — nothing is rewritten in phase 0), 28
(no mechanism). EXIT: DESIGN-capx-d79-<date>.md; nothing else touched.
```

## D76 — RE-EMITTED r#47 UNCHANGED (never dispatched at r#46: zero commits, no branch). Paste §D76 above verbatim. Its phase 0 is the precondition for the D72-prehunk residue t1h keys and for D67's FALL-year root cause; dispatch it.

## D67 — ARMING LEG (r#47; owner card C-20 / Q52 RULED **ARM for PJM** 2026-09-06) — **SUPERSEDED by §D67-ARM below (the issued charter).** Original reservation: Scope if ARM: `iso_configs._pjm_config` `default_scenario_overrides` gains `capacity_adequacy_requirement_published_by_iso: {"PJM": True}` (the D57/Q44 pattern), the bare `pjm-t1h` re-keys with its prior preserved at `-pre-d67`, one re-solve (~13 min, same-HEAD; the arm's numbers are in D67 §7.1), board row re-scored after D65-B's batch, PJM shard cell `K`, matrix stamped; every other ISO and every backcast byte-identical, asserted by the persisted-identity tests. Opus.

## D67-ARM — arm the published PJM RTO Reliability Requirement as the adequacy operand (r#47 amendment 1; owner ruling Q52 = ARM for PJM) — **ISSUED r#47 am.1, DISPATCHABLE**

```
You are the D67-ARM session of the capacity-expansion track — executing owner ruling Q52 (capx ledger
§3, r#47 amendment 1: "ARM for PJM"). Binding charter: pack §D67-ARM (this section) +
`FINDING-capx-d67-2026-09-06.md` (§3 the build; §3.1/§3.2 the vintage + hold-last rules; §7.1 the full-
span arm you are re-solving as the bare posture; §8.1 what the owner was asked) + the D57/Q44 arming
precedent (`FINDING-capx-d57-2026-09-05.md` §8.1; `iso_configs.py::_pjm_config` `default_scenario_
overrides`). DATA PROFILE: pjm. MODEL: Opus (pre-declared execution of a ruled arming; the arm's
numbers already exist). BRANCH (suggested; graded by content): claude/capx-d67-arm-pjm-requirement —
FRESH off origin/main. NOT the D67 lane's branch (`claude/capx-d67-pjm-requirement-operand-18wzjf` is
another desk's, closed).

THE ACT, pre-declared before any solve in a PRECOMMIT-capx-d67arm-<date>.md:
 1. `iso_configs.py::_pjm_config` `default_scenario_overrides` gains
    `capacity_adequacy_requirement_published_by_iso: {"PJM": True}` — the D57/Q44 pattern. The shared
    dataclass default stays `None`; every other ISO's bare key and EVERY backcast key are byte-
    identical (assert with `tests/regression/test_persisted_identity.py`; `check_cache_key_
    registration.py --base origin/main` green). The explicit `--no-capacity-adequacy-requirement-
    published` CLI path reaches the pre-arm posture and keeps its key (the (b′-1) inverse test, in the
    shape `test_d60_arming_batch.py` uses).
 2. THE RE-KEY, declared before the solve: the bare `pjm-t1h` moves from `aef81c84c4609c76` to the
    D67 arm's key `3f4070767f29472a` (verify by resolving through the harness path at HEAD — if HEAD
    has moved it, say so and pre-declare the realized value); the prior is preserved at
    `pjm-t1h-pre-d67`; the cache-epoch ledger in `src/market_sim/results/cache.py` gets its entry.
 3. G-DRIFT hunk by hunk from D67's full-span commit (`b1155995`) to HEAD, `constants.py` first;
    classify D77 (`campd_bins.py` composition — inert below 2028, so inert on a 2021–2025 hindcast:
    ASSERT, don't assume), #5033 (P1 basis seed, backcast callers only), D65-B (Act A/B — forecast-
    only CCS seams, inert below 2028), D74's default-off gate. A matched cache key is NOT a G-DRIFT
    verdict. If every hunk is INERT, the D67 §7.1 arm bundle's numbers ARE the bare posture's and the
    re-solve is a reproduction (pre-declare byte-identity of the four DYs' requirement rows and the
    census/position table); if any is LIVE, say which and pre-declare the direction.
 4. ONE re-solve: the bare `pjm-t1h` recipe at HEAD (2021–2025, ~13 min, PJM solo, sequential), scored
    and registered in place with its prior; FC rows at full magnitude against `pjm-t1h-pre-d67` and
    against D67 §7.1. HEAD GUARD: H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ]
    || exit 90. Rebase BETWEEN legs, never during; re-audit the rebase delta before registering.
 5. Matrix: PJM's `capacity_adequacy_requirement_published_by_iso` cell → `K` with this finding cited,
    keeper/gates stamp refreshed, PJM shard ONLY (rule 28d). CLAUDE.md's Capacity Evolution bullet
    list gains one line under "PJM capacity-market clearing" naming the armed operand and Q52 (the
    D57 bullet is the template; `/sync-docs` discipline, docs follow code).
 6. FINDING-capx-d67arm-<date>.md: the PRECOMMIT graded, the re-key table, the board row, the
    governance attestation with rule-27 blob checks (`iso_configs.py`, `cache.py`, the shard).
COLLISIONS: D65-B is the SOLE writer of `ff-verdicts.json` / `program-status.json` until its batch
lands — do steps 1–5 now, hold the board registration (step 4's last act) until D65-B merges, and
rebase between (never during). D74 (bar seam) and D75-R (ELCC registry) share PJM surfaces on
different regions; `_pjm_config` is yours this window — say so in the PRECOMMIT. Rules 13, 19, 21
(zero free parameters — the ruling is the identification), 22 (2021–2025 hindcast, forecast mode,
nothing out-of-training), 24, 25 (a PJM posture; no other ISO's cell), 27, 28, 29(b).
EXIT: PRECOMMIT first; the override + tests + epoch entry + shard in one PR; the re-solve registered
after D65-B; the finding closed. Nothing else arms.
```

## D65-B-R — the coupled-arming BATCH, re-issued under corrected per-ISO structural gates (r#48; the r#46 charter's G1 was PJM/MISO's `er/phys` band transcribed onto an ERCOT screen and its G3 an Act-A-only invariant applied to a coupled arm — both charter defects, adjudicated §0as.3) — **ISSUED r#48, DISPATCHABLE; sole board writer until its batch registers**

```
You are the D65-B-R session of the capacity-expansion track — completing D65-B (owner ruling Q47,
"Arm coupled, after D60-R3"), whose Acts A + B are ON MAIN (#5112/#5131/#5135) and whose ERCOT screen
RAN and fired two gates the director has since adjudicated as CHARTER DEFECTS (capx ledger §0as.3).
Binding charter: pack §D65-B-R (this section) + `FINDING-capx-d65b-2026-09-06.md` (§3 the re-key table;
§4 the unconstructible-control repair; §5 the G-DRIFT; §6 the screen as measured — its numbers STAND
and are NOT re-run; §7 what the batch needs, all durable) + `PRECOMMIT-capx-d65b-2026-09-06.md` and
its Addenda A/B + `FINDING-capx-d64-2026-09-05.md` §2.4 (THE PER-ISO CENSUS TABLE every gate below
is read from). DATA PROFILE: all. MODEL: Opus. BRANCH (suggested): claude/capx-d65br-batch — FRESH
off origin/main.

THE ADJUDICATION YOU EXECUTE (not re-litigate): G1's 1.27 floor is D64 §2.4's PJM/MISO host band;
the same table's ERCOT row is 0.95–1.05, and the ERCOT screen measured 0.9458 / 1.0000 — inside that
row at the table's two-decimal precision, reported at full magnitude as sitting at the floor. G3's
k = 1 invariance is an Act-A property; a coupled arm moves k = 1 rows by Act B's design; the
invariance is discharged by the existing unit test `test_ccs_retrofit.py::test_reference_host_is_
invariant_on_and_off` at zero LP. The ERCOT screen therefore READS AS CLEARED under the corrected
gates and is not re-solved (rule 29: a screen bundle is spent once). The guard against gaming is that
every corrected number pre-dates the solve in a committed document.

STEP 0 — MAKE G2 EVALUABLE (zero LP, small code): persist the `retrofit_log` scaling fields
(`capex_scale`, `fixed_cost_scale`, the uplift and `vom_adder_per_mwh`) alongside `ccs_retrofits` in
the evolution ledger (`results/evolution` writer), with a test; the same defect class as D65 §3d's
`floor_retained`. No cache key moves (a ledger field, not a config field — assert it).
STEP 1 — RE-PIN: re-run D65-B's bare-key declaration at HEAD (PRECOMMIT §3 + Addendum B.1); every
key must resolve unmoved or the moved ones are re-declared with the moving hunk named. Hunk-by-hunk
G-DRIFT from D65-B's close (`002cfa8d`) to HEAD, `constants.py` first — D78's `exit_exempt_unit_ids`
(sector gate default-off everywhere but MISO; MISO's clearing is off → INERT, assert), D74's default-
off gate, the miso-225 fields, anything else. A matched cache key is NOT a G-DRIFT verdict.
STEP 2 — THE PER-ISO GATES, written in a PRECOMMIT Addendum C BEFORE any leg solves, read from D64
§2.4's own rows: for each of ercot-t1f, neiso-t1f, nyiso-t1f, caiso-t1f, pjm-t1f, miso-t1f and the
neiso-t3 GOLDEN-3 — (G1') the rows that clear are inside THAT ISO's `er/phys` band in D64 §2.4 (PJM
and MISO 1.27–1.49; ERCOT 0.95–1.05; the others as the table reads — quote each row); (G2') the
identity `uplift/capex ∝ 1/k` on the persisted fields; (G3') Act-A-only k = 1 invariance = the unit
test, cited, not re-solved; (G4') no non-target load-bearing FC row flips PASS → FAIL; (G5') the
window total inside D64 §2.4's per-ISO predicted band and the 3 GW/yr cap binding where the table
predicts; (G6') wall/RSS inside the D60 envelope per leg. A carbon-0 ISO GAINING rows is the
pre-registered signature, not a STOP. STOP-only, per leg.
STEP 3 — THE BATCH, sequential (rule 12): ercot-t1f, neiso-t1f (~8), nyiso-t1f (~12), caiso-t1f (~23),
pjm-t1f (~36), miso-t1f (~65), neiso-t3 GOLDEN-3 (~33 min); each leg scored → verdict → registered in
place with its `-pre-d65b` prior; FC-map moves at full magnitude against D64 §2.4 and D65 §4; D77's §8
blast radius reconciled (every retrofit row now carries the captured rate); the D50 §6.2 radius
reconciled; the D72-prehunk residue key `neiso-t1f` discharged by this re-solve (say so). HEAD GUARD
around every leg: H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90.
Rebase BETWEEN legs only; re-audit each rebase delta hunk by hunk before the next leg.
STEP 4 — matrix: the `ccs_retrofit_screen` row's def/note carries Act B; the `ccs_retrofit_fixed_
cost_co2_scaling` row's cells `fc: K` where the arm is now the bare leg; six shards, one line each,
last commit. FINDING-capx-d65br-<date>.md: Addendum C graded per ISO, the before/after board table,
the board now in ONE demand vintage (post-`d14a7ed0`) — say so, the D8 curated DOF rows for the
flipped default, governance with rule-27 blob checks.
COLLISIONS: you are the SOLE writer of `ff-verdicts.json` / `program-status.json` until the last leg
registers; D67-ARM, D78-R and D81 register after you. Rules 12, 22 (forecast mode only), 24, 25, 27,
28, 29. EXIT: every bare key re-solved and registered with its prior, the finding closed. Nothing
else arms.
```

## D78-R — the sector-gate seam repair on the FULL 2021–2025 window, with the sign line on the DECIDED COHORT (r#48; D78 §8 item 2) — **CHARTERED r#48, DISPATCHABLE (registers after D65-B-R)**

```
You are the D78-R session of the capacity-expansion track. Binding charter: pack §D78-R (this section)
+ `FINDING-capx-d78-2026-09-06.md` (§0–§4 the exact screen; §5 the pre-declaration graded; §8 item 2 —
YOUR spec) + `PRECOMMIT-capx-d78-…` §6 (the full-window leg runner is already committed) + D58 §5 /
D78 PRECOMMIT §7 (the flip condition (a) purity, (b) fidelity, (c) composition, (d) LOYO). The seam
repair is ON MAIN (#5144); `retirement_sector_gate` stays default-off. DATA PROFILE: pjm. MODEL: Opus
(the design and the identities are landed; this is two solves and a grading). BRANCH (suggested):
claude/capx-d78r-full-window — FRESH off origin/main.
WHAT WAS WRONG WITH G6: it asked that executed economic exits not rise in either screen year, and the
admission cap re-filled the budget the 226 sector-1 rows freed (a timing shift inside the window, the
PRECOMMIT's own §5 item 3 prediction). The sign line a candidate-set gate CAN obey is on the DECIDED
COHORT and the WINDOW TOTAL (D78 G3 is already that identity); per-year executions are REPORTED, not
gated. Write that pre-declaration in a PRECOMMIT before any solve, with the window-total band computed
on D78's same-HEAD control leg (D74 §9 item 3's procedure: brackets on the screen's own control, never
on the pre-hunk committed stack).
TWO LEGS at HEAD (~35 min total, PJM solo, sequential): control-P (gate off) and the repaired arm
(`--retirement-sector-gate`), 2021–2025; then grade (a) purity — every non-sector-1 row byte-identical
in every year; (b) fidelity — the failing pool = control minus exactly the sector-1 rows each year;
(c) composition on the full-window `score.json` — FC-3 `retire.total_gw`, recall, precision at full
magnitude, against the pre-declared cohort identity; (d) LOYO within the window. G-DRIFT hunk by hunk
from D78's close (`f3fb0988`) to HEAD first. HEAD GUARD around each leg; rebase between, never during.
EXIT: PRECOMMIT, FINDING with the four-condition grade and the arming recommendation for PJM
(pre-stated: ARM iff (a)–(d) all MET; HOLD-and-route otherwise), the arm registered SUFFIXED after
D65-B-R (`pjm-t1h-d78r-sectorgate`), PJM cell letter, both bundles' slim sets only. Rules 1, 12, 13,
14, 19, 21, 22, 24, 25, 27, 28, 29.
```

## D81 — the must-offer rule on the OTHER exemption channels: PENDING dated plants and the this-year retrofit (D78 §8 item 3 / design §4; Q53's ruled principle extended by the director, §0as.3(c)) — **CHARTERED r#48, DISPATCHABLE (registers after D65-B-R)**

```
You are the D81 session of the capacity-expansion track. Binding charter: pack §D81 (this section) +
`DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md` §4 (the channel table: which exemption channels
reach the residual price-taker construction and what PJM's rule says for each) and §4.1 + `FINDING-
capx-d78-2026-09-06.md` §5.1 and §8 item 3 + `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` §4.2
(the design reading being replaced: "does not submit a price-forming offer", with its stated bias —
price DOWN, cleared UP). Owner ruling Q53 (2026-09-06) ruled the must-offer reading for the sector
gate; the director extends the SAME rule to the channels below because D54 §4.2 was a design choice,
not a ruling — recorded in ledger §0as.3(c). DATA PROFILE: pjm. MODEL: Opus (one seam, the rule already
ruled, the fix already named as one line). BRANCH (suggested): claude/capx-d81-dated-must-offer —
FRESH off origin/main.
THE RULE (design §4): a resource whose Capacity Resource status removal is EFFECTIVE for the delivery
year is no longer eligible to offer (step 0/1 exits executed this year: correctly absent); a PENDING
dated plant — filed date later than the delivery year — MUST OFFER for every DY before the removal is
effective (§1.2), and today it lands in `Q_0` at $0 through the residual construction; a this-year
CCS retrofit is an existing resource and must offer (inert below 2028 by construction).
PHASE 0 (zero LP): size the pending dated block in the 2022–2025 fleets from the same-HEAD control's
census and the exit registry (count, nameplate, accredited MW) — D78 §5.1 could not separate it from
the committed ledgers, so build the read from the fleet + registry, not the ledgers; pre-declare the
sign: offers rise by the block's net-ACR-capped MW, price-takers fall by the same MW, clearing price
UP (D54 §4.2's stated bias reversed), position DOWN, second-order in the window — with magnitudes per
DY. PHASE 1: the one-line fix at the `_dated_exempt` site (→ `exit_exempt_unit_ids`, the D78 seam)
and the retrofit-year channel the same way; tests: a pending dated unit offers at its cap and does
not face the exit screen; an executed exit is absent from both; below-2028 hindcasts byte-identical
on the retrofit channel. No new field if the fix is the seam's correct semantics (say so); rule 24/28
otherwise. PHASE 2 — SCREEN (rule 29): ONE screen year = the DY where phase 0's pending block is
largest (named in the PRECOMMIT), two legs at HEAD, STOP gates = the phase-0 identities (offers +
price-takers conserved to the MW; every non-dated row byte-identical; no non-target load-bearing
flip). PHASE 3: the full window if the screen clears. HEAD GUARD; rebase between legs; a matched key
is not a G-DRIFT verdict. COLLISIONS: `retirements.py`'s clearing path — D78-R touches no code, so
compose; rebase onto its PRECOMMIT if both are live; D65-B-R is the sole board writer until its batch
registers. Bundles deleted before merge. Rules 1, 13, 14, 19, 21, 22, 24, 25, 27, 28, 29.
EXIT: PRECOMMIT, FINDING with the phase-0 block table, the screen, the window, §8 recommendation
(this is a rule already ruled: the recommendation is MERGE AS CODE unless a STOP fires).
```

## D82 — RESERVED (r#48): the PJM CT plateau — 24.2 GW of CT offering exactly the published bar on zero E&AS, the admission cap's re-fill pool once steam/oil leave the candidate set (D74 §8 item 2 / §9 item 1; D54 §6 item 1; D61 §1.5). A price-formation / E&AS-operand object, not a cap lane's. Needs a design read (the thin hindcast price tail vs a pro-forma that captures the whole price-duration integral; C3c's model-class limitation) before any charter. Do not spend this label on anything else.

## D80 — ID LIST CORRECTED r#48 (the r#47 text otherwise stands): the ratchet at `2617a5d3` names EIGHT capx ids — `caiso-2026-2030-d60-arm` (I12, I7 — D60 §5.3 / the leg-3 record), `neiso-2026-2050-t3-golden3-d60` (I3), `nyiso-2021-2025-realized-t1h-d45r-curveon` (I7), `pjm-2021-2025-realized-t1h-d45` (I7), `-d45r` (I7), `-d57-clearing` (I7), `-d62-pubbar` (I7), `pjm-2026-2030-d60-arm` (I12, I7). The SCN id is gone (SCN-FIX1 landed) and D74 declared its own arm. Reconcile against the live list at HEAD exactly as §D80 says.


## r#49 NOTE (2026-09-06): D80 LANDED (#5151); D65-B-R / D78-R / D81 are RUNNING checkpoints; D78-R exists on TWO stems (`-s35hos` merged and running; `-csniwn` = PR #5160, a duplicate to close). D67-ARM, D76, D75-R and D79 have never been dispatched — paste each ONCE; one session per prompt.

## D78-R2 — the sector-gate seam on the full window, RE-SOLVED at a HEAD carrying D81 + D67-ARM, with W5 restated as a tested E&AS-propagation identity and W4's lower edge corrected — plus the `exempt_unit_ids` deletion (D81 rec 2, director decision (a)) (r#50; D78-R §6 items 1–3) — **CHARTERED r#50, DISPATCHABLE (registers after D65-B-R)**

```
You are the D78-R2 session of the capacity-expansion track. Binding charter: pack §D78-R2 (this
section) + `FINDING-capx-d78r-2026-09-06.md` (§3 the identities; §3.4 the E&AS propagation; §4 the W4
construction error and the corrected edge; §6 the flip condition and its three successor items) +
`FINDING-capx-d81-2026-09-06.md` §8 item 2 (`exempt_unit_ids` has no producer) + D78 PRECOMMIT §7 / D58
§5 (the flip condition (a)–(d)). The seam repair (D78) and the dated/retrofit routing (D81) and the PJM
published requirement (D67-ARM) are ALL ON MAIN; `retirement_sector_gate` stays default-off. DATA
PROFILE: pjm. MODEL: Opus. BRANCH (suggested): claude/capx-d78r2-full-window — FRESH off origin/main.

STEP 0 — THE DELETION (rule 26's spirit, director decision (a)): `exempt_unit_ids` has no producer
since D81 routed every channel to `exit_exempt_unit_ids`. Delete the parameter; rewrite D78's T3 as a
NEGATIVE test on the residual construction (a unit absent from `margins` and absent from
`exit_exempt_unit_ids` is `Q_0` at $0 — the only remaining path); assert the bare `pjm-t1h` key and
every backcast key unmoved (a structural API parameter, not a config field).
STEP 1 — PRE-DECLARE, in a PRECOMMIT before any solve: (W4′) window decided total ∈ [Σdecided_ctl −
Σ(sector-1 decided_ctl), Σdecided_ctl + Σg_y], both edges computed on the SAME-HEAD control leg after
it solves and before the arm (D74 §9 item 3's procedure); the point value Σdecided_ctl − Σ(sector-1
decided_ctl) is the exact-partition prediction. (W5′) shared-stack `A_g`, fuel and cleared-flag
identical in every year; offers identical in the first divergent year; thereafter offers differ ONLY
through the prior year's price vector — TESTED, not assumed: the offer delta is zero for every unit
whose E&AS operand is zero (CT / ST / oil in the hindcast prices), and non-zero only where the prior
year's zonal price differs. W1/W2/W3 as D78-R. G-DRIFT hunk by hunk from D78-R's close (`f9b377a8`) to
HEAD, `constants.py` first. DIFF THE WHOLE LEDGER (D81 rec 4): the comparator differences EVERY
committed block of the two legs and explains each difference — an assertion list is the floor, not
the ceiling.
STEP 2 — TWO LEGS at HEAD (~35 min, PJM solo, sequential): control-P and the arm, 2021–2025; HEAD
GUARD around each; rebase BETWEEN legs, never during; if main moves under the lane, re-audit and
re-attribute (W0′) before grading. Grade (a)–(d); pre-stated: ARM iff all four MET; HOLD-and-route
otherwise. Arm registered SUFFIXED (`pjm-t1h-d78r2-sectorgate`) AFTER D65-B-R's batch registers;
PJM cell letter; bundles' slim sets only. Rules 1, 12, 13, 14, 19, 21, 22, 24, 25, 26, 27, 28, 29.
EXIT: PRECOMMIT, FINDING with the whole-ledger diff, the four-condition grade, the arming
recommendation; the deletion in the same PR.
```

## D76 — PHASE 2 (r#50): the measured-hindcast screen peak on the PJM FULL SPAN, then the 2021–2023 window on CAISO / ERCOT / MISO; NEISO and NYISO deferred — **CHARTERED r#50, DISPATCHABLE (registers after D65-B-R); ARMING = owner card on the phase-2 numbers**

```
You are the D76 phase-2 session of the capacity-expansion track. Binding charter: pack §D76 + this
phase-2 section + `FINDING-capx-d76-2026-09-06.md` (§2 the six-ISO census; §3 the screen years and
the 2021–2023 window offer; §4 the seam and every consumer; §6–§7 the PJM screen PASS and what the
mechanism did; §8 routes). The gate `capacity_screen_peak_measured_hindcast` is BUILT, default-OFF,
on main. DATA PROFILE: pjm first, then caiso / ercot / miso. MODEL: Opus. BRANCH (suggested):
claude/capx-d76-p2-full-span — FRESH off origin/main.
PRECONDITION (a STOP, not a suggestion): this section IS the director's release of phase 2; nothing
past phase 2 — no arming, no override, no default flip — without a further release.
DIRECTOR'S CALLS (§0au.3): window = 2021–2023 for CAISO, ERCOT and MISO (the bridge year exercises
2022's large delta at half the LP; §3.1 items 1–2); PJM = the FULL 2021–2025 span (its screen
passed); NEISO (smallest footprint) and NYISO (requirement-moot at HEAD through the D52 gates)
DEFERRED — say so, do not solve them.
LEG 1 — PJM full span, two legs at HEAD (control at HEAD: every committed T1-H control is PRE-hunk on
`DEMAND_GROWTH_RATES`; D67-ARM is on main so PJM's requirement is peak-independent in-table — the
remaining effect runs through accreditation, the floor/backstop and the CR-1 position; pre-declare
that). FC-3 at full magnitude: the `gas_st` survival phase 1 measured (+7,333.7 / +9,464.5 MW) against
2.702 GW of actual steam exits — this is D74's object seen from the demand side; report, never gate.
LEGS 2–4 — CAISO, ERCOT, MISO on 2021–2023, sequential (rule 12; per-plant multi-zone LPs, ~7 GB a
year): the structural STOP gate on the 2022 bridge ledger AND the 2023 solved ledger — the arm's
screen peak = the measured peak to the MW; every non-peak operand byte-identical; no non-target
load-bearing flip; DIFF THE WHOLE LEDGER and explain every difference (D81 rec 4). Pre-declare each
ISO's requirement move from phase 0's census before its leg.
Every leg: PRECOMMIT before the first solve; HEAD GUARD; rebase BETWEEN legs, never during; re-audit
each rebase delta hunk by hunk; a matched cache key is NOT a G-DRIFT verdict; bundles DELETED before
merge (rule 29(c)) — every number in the FINDING. Registration of any arm row AFTER D65-B-R's batch.
EXIT: FINDING-capx-d76-p2-<date>.md — the four ISOs' tables, PJM's FC rows at full magnitude, the
arming card drafted for the director (never served by the lane), matrix cells per ISO (rule 25:
each ISO's own letter). Rules 1, 12, 13, 14, 19, 21, 22, 24, 25, 27, 28, 29.
```

## D79 — PHASE 1 (superseded r#50 am.1 — Q54 RULED ADOPT, frozen-hash; the issued charter is §D79 phase 1 below). Original reservation: If ADOPT: Opus or Fable (rule 27 core scope — `cache.py` + `scenarios.py`), the §6 build spec verbatim, frozen-hash landing (zero key moves), backcast keys included, scoped-epoch list empty, attestation guard WARN; the persisted-identity pins re-asserted unmoved; no bundle, no board byte.

## D82 — RESERVED (updated r#50): now also carries D81 rec 3 — 2,306.4 MW of DY2022 pending dated capacity is UNCOMPETITIVE at its net-ACR cap under the ATB FOM proxy (a different number under the D62 bar); whether real PJM dated units clear is checkable against the BRA record as a validation observable. Still needs a design read before a charter.

## D79 — PHASE 1: the solve-surface fingerprint in the cache key, FROZEN-HASH landing (r#50 amendment 1; owner ruling Q54 = "ADOPT, frozen-hash now") — **ISSUED r#50 am.1, DISPATCHABLE**

```
You are the D79 phase-1 session of the capacity-expansion track — executing owner ruling Q54 (capx
ledger §3, r#50 amendment 1: "ADOPT, frozen-hash now"). Binding charter: pack §D79 phase 1 (this
section) + `DESIGN-capx-d79-2026-09-06.md` §6 (THE BUILD SPEC — §6.1 files and functions, §6.2 what a
bundle records, §6.3 the tests, §6.4 what is deliberately NOT built) and §7 (the ruled card: rows 1–5
as recommended, row 6 to a later card) + capx D24 / D24-R (the cache-key repair precedent whose
append-only guards, no-op probe and dated cause-block discipline you mirror). DATA PROFILE: code.
MODEL: Opus or Fable (rule 27 core scope: `scenarios.py` and `cache.py` are ≥300-line core files —
Edit tool, exact bytes, blob-verify every push). BRANCH (suggested; graded by content):
claude/capx-d79-p1-solve-surface — FRESH off origin/main.

THE RULING, as executed here: (1) the hybrid (d) — a per-name, per-ISO-PROJECTED value fingerprint
of the seven `SURFACE_MODULES`, each name dropped at its FROZEN registration-time hash, plus the
epoch ledger made mechanical as SCOPED `SolveEpoch` ids; (2) FROZEN-HASH landing: **ZERO keys move**
at landing — every name is declared at its live hash, `moved_rows(iso) == {}` for all six ISOs, and
the D24-R-style no-op probe over ALL committed run configs reads 0 moved (committed as
`capxd79-solve-surface-no-op-record.json`) — this is the MERGE GATE; (3) backcast keys carry the
fingerprint (§4.5); (4) `SOLVE_EPOCHS` starts EMPTY — D77's 2026-09-06b entry stays prose, the
D65-B-R batch is the re-solve; (5) the §6.4 attestation guard is NOT built in phase 1 (WARN-level
process check, priced by the owner later); (6) `reserves/spec.py` / `interchange/spec.py` and the
floor CSVs are OUT of scope (a later card).

BUILD, exactly §6.1: NEW `config/solve_surface.py` (< 300 lines: `SURFACE_MODULES`, `canonical`,
`surface_rows(iso)` ISO-projected + `lru_cache`, `moved_rows(iso)`, `SolveEpoch` + `SOLVE_EPOCHS`
append-only and empty, `applicable_epochs(config)`, `surface_stamp(iso, config)`); NEW
`config/solve_surface_declared.py` (`DECLARED`, one line per name, generated by the register script,
never hand-edited, append-only); `scenarios.py::cache_key` gains ~10 lines after the retired-field
re-insertion and before path folding (`__solve_surface__` = moved rows if any; `__solve_epochs__` =
applicable ids if any — dunder keys, invisible to `config_disagreements`, untouched by
`_normalize_cache_key_paths`); `cache.py::save_result` writes `solve_surface.json` beside
`config.yaml` and the module docstring gains the paragraph that says the key now sees the surface;
every site that writes `"cache_key"` (`pipeline/persist.py`, `run_full_horizon.py`,
`run_capacity_hindcast.py`, `results/export.py`) also writes `"solve_surface": surface_stamp(...)`;
`scripts/lib/forecast_provenance.py` `PROVENANCE_FIELDS += ("solve_surface",)`, read from the
artifact never recomputed; `check_cache_key_registration.py` checks 5 (every UPPERCASE name in
`SURFACE_MODULES` has a `DECLARED` entry — FAILS the PR), 6 (`DECLARED` and `SOLVE_EPOCHS` append-only;
a retired name keeps its last hash exactly as `_CACHE_KEY_RETIRED_FIELDS` — FAILS), 7 (a new
`**Epoch <date>` ledger heading with no matching `SolveEpoch` and no "KEY ADVANCE" marker — WARN);
NEW `scripts/solve_surface_register.py` (`--declare NAME…` at the live hash; `--diff <sha> [<sha>]`
printing per-ISO changed rows — the mechanised "constants.py FIRST" G-DRIFT step);
`tests/regression/test_persisted_identity.py`: the two config pins under a fixture pinning
`moved_rows` to `{}`, a new `PINNED_SURFACE_ROWS_BY_ISO` block with the dated cause-block discipline,
the path-invariance test extended to the surface.

TESTS, exactly §6.3: `tests/unit/config/test_solve_surface.py` (canonicalisation order-independent
and type-faithful; ISO projection rule; a docstring edit moves nothing; a value edit to `X["MISO"]`
moves MISO alone; a new name with a declaration moves nothing and without one fails check 5; a
revert restores the declared hash and the pre-change key; `SolveEpoch` scope predicates incl. the
backcast-inert case; the append-only guard's four cases), `tests/unit/results/test_cache_solve_
surface.py` (the sidecar; config/sidecar agreement; S1-solved bundle not addressed by S2 and
addressed again after revert), the persisted-identity extensions, the no-op probe record. CI:
checks 5–7 through the existing `check_cache_key_registration --base` step; NO new workflow.

DISCIPLINE: no `ScenarioConfig` field, no matrix row (not a mechanism — the D24-R precedent); rule
24 (derived, never settable: no env var, no CLI flag); rule 26 (append-only ledgers; a retired name
keeps its last hash); rule 27 (Edit tool on `scenarios.py` / `cache.py` / `test_persisted_identity.py`
/ `check_cache_key_registration.py`; fetch back and hash-compare every ≥300-line file after every
push); rule 22 (nothing solved). MERGE GATE = the no-op record reads 0 moved AND `tests/regression/
test_persisted_identity.py` 14/14 + the six surface pins PASS AND `check_cache_key_registration
--base origin/main` green. COLLISIONS: D65-B-R's batch is registering — its keys are config-only and
unmoved by a frozen-hash landing (assert by resolving its seven declared keys at HEAD before and
after: identical); D78-R2 / D76-P2 / D75-R touch no cache plumbing; `cache.py` is yours this window
— say so in the PRECOMMIT. EXIT: PRECOMMIT (the declared no-op prediction, key by key), one PR,
FINDING-capx-d79p1-<date>.md with the no-op record, the pin table, blob checks; CLAUDE.md's
"Cloning & session data" or Git section gains ONE sentence naming the fingerprint and Q54 (docs
follow code). Nothing else arms.
```

## r#51 NOTE (2026-09-06): D79 phase 1 / D78-R2 / D76 phase 2 / D75-R ALL LANDED; D65-B-R at 5/7 legs with G5′ adjudicated (§0av.3(b)); Q55 RULED ARM; five charters below — two DISPATCHABLE NOW (D78-R3, D75-R FACADE FIX), one NOTE for the running batch, two SEQUENCED/HELD (D75-R-ARM after D65-B-R's board write; D76 PHASE 3 after D75-R-ARM)

## D78-R3 — the per-delivery-year zero-E&AS set, pre-registered and derived STRUCTURALLY, then W5′ re-graded (r#51)

```
You are the capx D78-R3 lane for jessicacohen554-cyber/market-simulator. MODEL: Opus.
DATA PROFILE: pjm (hydrate with `python3 scripts/hydrate_data.py --profile pjm`; the
committed D78-R2 instruments and the arm's slim registered files need only `code`, so start
there and widen ONLY if step 3 earns the control re-solve).
Branch: claude/capx-d78r3-perdy-set, fresh off origin/main. Rebase before every push;
blob-verify every push touching a >=300-line file (rule 27).

WHAT YOU ARE. D78-R2 (FINDING-capx-d78r2-2026-09-06.md, merged #5227) proved the sector-gate
seam an EXACT candidate-set partition over 2021-2025 (W1/W2/W3 PASS, W4' HIT at 9,394.156 MW,
whole-ledger diff zero unclassified rows) and HELD on ONE limb: W5' fired because the lane
declared {gas_ct, gas_st, oil} a YEAR-INVARIANT zero-E&AS set on D57's headline, while
FINDING-capx-d57-2026-09-05.md section 4's table is PER DELIVERY YEAR and puts only `oil` at the
full bar in 2024/25 ("the CT fleet's 2024 margin is small but non-zero"). Measured exactly so:
all 404 shared gas_ct rows moved in 2024-25 and the 8 oil rows moved by exactly zero. Your job
is D78-R2 section 9, items 1-3, as a rule-29 SUCCESSOR pre-registration: declare the set per DY,
derive it structurally, re-grade W5', and recommend. You do NOT arm anything. You do NOT touch
retirement_sector_gate's default, _pjm_config, or any ScenarioConfig field.

READ FIRST: CLAUDE.md rules 1, 13, 14, 19, 21, 24-29; FINDING-capx-d78r2 (all of it, sections
5, 8, 9, 10 twice); its ADDENDUM 1 (docs/handoffs/d78r2/ADDENDUM-1-w4prime-band.md — the
derive-on-the-control-before-the-arm pattern you are copying); FINDING-capx-d57 section 4 (the
per-DY table) and section 8.1; FINDING-capx-d78r-2026-09-06.md section 4; the capx ledger
docs/handoffs/capx-director-ledger-2026-08.md section 0av.3(d) and 0av.5(ii) (why the control
may be gone); docs/handoffs/d78r2/{control_band,window_compare2}.json and .py.

STEP 0 (zero LP) - PRECOMMIT-capx-d78r3-<date>.md, pushed BEFORE reading any per-class number.
 (a) THE DECLARED SET, per delivery year, quoted from D57 section 4's rows, not its headline:
     DY2022/23 {gas_ct, gas_st, oil}; DY2023/24 {gas_ct, gas_st}; DY2024/25 {oil}. Cite the row.
     If D57 section 4 carries a DY2025/26 row, quote it too; if not, say the window's last DY has
     no published set and W5' is NOT evaluable there (report, do not gate).
 (b) THE STRUCTURAL DERIVATION RULE, stated before any count is read: "a class sits at its full
     bar in DY iff every one of its offers in the control's DY stack is the same value" (D78-R2
     section 9 item 2: oil 1 distinct value, nuclear 1, gas_st 3 while barred, gas_ct 12 while
     barred and 72 once live). State the exact tolerance (byte-equal, or <= 1e-6 $/MW-day) NOW.
     THE SUBSET GUARD: the derived set for a DY must be a subset of (a)'s declared set for that
     DY; a class the record does not put at its bar may NOT be admitted by arithmetic alone.
     If derived and declared differ, the DECLARED set governs W5' and the difference is REPORTED.
 (c) W5'' restated on the per-DY set: for each DY, every shared row of a class in the DY's set
     has a zero offer delta between control and arm; every class outside the set is REPORTED
     (moved / unmoved, count and MW), never gated. Pass/fail is per DY and the window verdict is
     the conjunction over the DYs where the set is non-empty and evaluable.
 (d) THE GRADE RULE, pre-stated: W5'' PASS on every evaluable DY => limbs (a)-(d) of D78-R2
     section 8 are ALL MET => you RECOMMEND ARM (owner card, served by the director as Q56); any
     DY FAIL => HOLD, and name the class and count. No other outcome exists; write both sentences
     now.
 (e) WHERE THE STRUCTURE LIVES. Enumerate, before reading, which committed artifact carries a
     per-DY per-class OFFER STACK: the arm's slim registered files under results/hindcast/
     pjm-2021-2025-realized-t1h-d78r2-sectorgate (list the files), the D78-R registered arm
     (FINDING-capx-d78r2 CORRECTION 1 says it carries its ledgers), docs/handoffs/d78r2/*.json.
     control_band.json and window_compare2.json carry SECTOR aggregates only (director r#51
     section 0av.5(ii)) - say so. If NO committed artifact carries the control's per-DY stack,
     say in the PRECOMMIT that the control-P re-solve (bare pjm-t1h, ~21 min, key
     a9c66d8ea25acb9d, HEAD guard on) is EARNED as the derivation base under rule 29(b)'s
     LIVE-hunk analogue (a deleted derivation base), and that it will be DELETED BEFORE MERGE
     again under 29(c). Deriving on the ARM's stack instead is FORBIDDEN (it is the object being
     graded).

STEP 1 (zero LP where (e) allows) - the derivation. Run the rule from (b) on the control's stack
per DY. Emit docs/handoffs/d78r3/zero_eas_set.json: per DY the distinct-offer count per class,
the derived set, the declared set, the subset check, and which artifact it was read from. If the
control stack had to be re-solved, record key/HEAD/wall exactly as D78-R2 section 1 does.

STEP 2 (zero LP) - re-grade W5'' on the committed arm and control ledgers/stacks. The arm is
pjm-t1h-d78r2-sectorgate (registered, suffixed). Emit docs/handoffs/d78r3/w5_regrade.json with
the per-DY per-class row counts, moved counts, max |delta|, and the verdict. Do NOT re-solve the
arm. If the arm's committed files cannot support the re-grade, STOP and route - do not re-solve
the arm to make a grade possible.

STEP 3 - FINDING-capx-d78r3-<date>.md: the per-DY table (declared vs derived vs measured), the
W5'' verdict per DY, the D78-R2 section 8 limb table re-stated with (a) updated, the
recommendation from (d) verbatim, everything at full magnitude. PJM's matrix shard: update the
retirement_sector_gate cell's evidence citation (rule 28(b); PJM shard only). If a control
re-solve was spent: delete the bundle before merge and cite every number in the FINDING.

GATES THAT STOP YOU: any per-class number read before the PRECOMMIT is pushed; the derived set
exceeding the declared set (report, do not admit); any arm re-solve; any change to a default,
an override, or retirements.py's decision logic. A stack-export helper (read-only, for the
derivation) is allowed if the committed files lack the structure - declare it in the PRECOMMIT
and keep it under scripts/probes/.
EXIT: PRECOMMIT, the two JSON instruments, FINDING with the recommendation sentence, PJM shard
cell, one PR (or two: PRECOMMIT first). Nothing arms.
```

## D75-R FACADE FIX — the red `test_moved_surface_is_complete` on main (r#51)

```
You are the capx D75-R FACADE FIX lane for jessicacohen554-cyber/market-simulator. MODEL: Opus
(rule 27 core scope: constants.py is a >=300-line file). DATA PROFILE: code.
Branch: claude/capx-d75r-facade-fix, fresh off origin/main.

THE DEFECT. tests/regression/test_constants_facade.py::test_moved_surface_is_complete is RED on
main at 00cee150: D75-R (merged #5206/#5229) added PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE and
RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO to src/market_sim/config/capacity_market.py without the
constants.py facade re-export (FINDING-capx-d79p1 section 6 reported it; the director measured
it red this sitting: `assert not {'PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE',
'RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO'}`).

DO. (1) Read how the facade re-exports the other capacity_market names (grep constants.py for
RENEWABLE_ELCC or CAPACITY_MARKET) and add the two names the SAME way, in the same block, with
the same one-line citation comment pointing at FINDING-capx-d75r-2026-09-06.md section 1.
(2) Edit with the Edit tool - never regenerate the file. (3) Run the test, then the whole
tests/regression/test_constants_facade.py, then `python3 scripts/check_cache_key_registration.py
--base origin/main` and `python3 scripts/solve_surface_register.py --diff origin/main HEAD` (or
its equivalent) and PASTE both outputs in the PR body: the fingerprint already sees both names
through the registry module, so the expected result is ZERO moved names and ZERO key moves -
if either moves, STOP and route, do not push. (4) ruff check + format. (5) Push; blob-verify
constants.py (line count + sha256 local vs origin) before anything else; put the verification
in the PR body.
DO NOT: touch capacity_market.py's values, any ScenarioConfig field, any test other than
observing it go green, or any other file. One commit, one PR, title "constants facade: re-export
the two D75-R capacity_market names". No FINDING needed; the PR body is the record.
```

## D65-B-R ADJUDICATION NOTE — paste into the RUNNING batch session (r#51 §0av.3(b))

```
DIRECTOR ADJUDICATION for capx D65-B-R (capx-director-ledger-2026-08.md section 0av.3(b),
2026-09-06). You routed G5' on neiso-t1f (fired: 2030 at 59.5 % of cap) and nyiso-t1f (fired
twice: 2029 75.7 %, 2030 33.3 %) because the gate contradicts its own source. RULING:

1. G5' AS TRANSCRIBED FOR THE CAP-BOUND LEGS (neiso-t1f, nyiso-t1f, caiso-t1f: "STOP if the cap
   does NOT bind in a year") IS VOID AS A STOP and is RECLASSIFIED to REPORTED. Ground: D64
   section 2.3, verbatim - "a year converting materially below the cap would be the informative
   surprise, not a STOP" - pre-registered this exact outcome as not a STOP, and Addendum C
   promoted section 2.4's hour-ceiling census cell (computed on the SHIPPED shape) into a floor
   on a solved quantity, the "a band is a window, never a floor" error Addendum C itself names
   for G1'. Same defect class as r#48 section 3(a); the ruling is made on the documents and
   would be identical had the below-cap years read against the seam.
2. The ceiling form of G5' on ercot / pjm / miso ("any year above its ceiling") is UNTOUCHED - a
   published ceiling is a legitimate upper bound.
3. neiso-t1f and nyiso-t1f are NOT STOPPED. They REGISTER on the board exactly as the three
   cleared legs do (you are the sole board writer), with the unbinding reported at full
   magnitude and the MW-weighted k column beside it (0.9952 -> 1.3032; 1.0544 -> 1.2235), and
   the CAISO control case (k 1.03-1.08, stays bound) cited as the mechanism reading. Fill
   FINDING sections 0 and 6 accordingly; state in section 6 that G5' fired, was routed, and was
   voided by this ruling - do not rewrite Addendum C.
4. LEG 7 (neiso-t3 GOLDEN-3) IS NOW POSITIVELY INDICATED by D64 section 2.3's own conditional
   ("only re-solved if the NEISO t1f arm shows the cap unbinding"). Run leg 6 (miso-t1f) then
   leg 7 as chartered; leg 7's Addendum C gate ("the converted set moves IN KIND - a class the
   RGGI ladder does not price") stands as written.
5. Recreate the branch claude/capx-d65br-batch-nmrwww off origin/main (it was merged and
   deleted at #5230); re-audit the delta since 81c8aa6c before the next LP (REBASE-THEN-RE-AUDIT,
   constants.py first); note that main now carries D79's fingerprint (zero key moves, verified
   0/148) and D75-R (a default-OFF field, absent from your recipes) - classify both.
6. The two test_capacity.py pins are GREEN at 00cee150 - record that section 3.2's debt is
   discharged. Then the board write, the FINDING close, and the PR.
```

## D75-R-ARM — arm `pjm_vre_accreditation_vintage` for PJM under owner ruling Q55 (r#51; SEQUENCED)

```
You are the capx D75-R-ARM lane for jessicacohen554-cyber/market-simulator. MODEL: Opus.
DATA PROFILE: pjm. Branch: claude/capx-d75r-arm-pjm, fresh off origin/main.
DISPATCH PRECONDITION (STOP): do NOT start until D65-B-R's board-write PR (the one that
registers pjm-t1f / neiso-t1f / nyiso-t1f / miso-t1f / neiso-t3 on
frontend/data/forecast/program-status.json) has MERGED to main. You move every bare PJM key;
the batch is the sole board writer and was re-declared once already for D67-ARM. Check with
`git log origin/main --grep="D65-B-R"` and the board's pjm-t1f row before your first commit;
if it has not merged, stop and say so.

AUTHORITY. Owner ruling Q55 (capx ledger section 3, r#51): ARM for PJM. Evidence:
FINDING-capx-d75r-2026-09-06.md (sections 0, 1, 5, 6, 8). Posture: the D57 / D67-ARM
precedent - FINDING-capx-d67arm-2026-09-06.md is your template, follow its structure.

DO, in this order.
 (0) PRECOMMIT-capx-d75r-arm-<date>.md pushed before any solve: the bare pjm-t1h key at HEAD
     (control) and the declared post-arm key; the no-op probe expectation (every non-PJM run
     config and every backcast config: ZERO key moves - run
     scripts/probes/capxd79_solve_surface_no_op_check.py or the D67-ARM probe and paste the
     count); G-DRIFT from D75-R's FINDING sha to HEAD, constants.py first; the invariants you
     expect to hold (D67-ARM had all 14 PASS on the bare row - state that as the bar); FC-3 rows
     reported at full magnitude, never gated.
 (1) The arm: in src/market_sim/config/iso_configs.py::_pjm_config default_scenario_overrides,
     add pjm_vre_accreditation_vintage=True beside the D48 / D57 / D67 entries, with a citation
     comment (Q55, FINDING-capx-d75r section 8). Shared ScenarioConfig default stays OFF. Confirm
     --no-pjm-vre-accreditation-vintage reaches the control (existing harness flag) and that an
     explicit False keeps the pre-arm key. Update the D67-ARM-style test that asserts the PJM
     override set (tests/unit/model/test_capacity.py::test_pjm_iso_override_arms_forecast_only)
     to include the new field - the intent is unchanged: forecast-only, PJM-only.
 (2) Byte-identity: run the no-op probe; every non-PJM config and every backcast config must
     show zero key moves; every PJM forecast config moves (report the list). Any other pattern:
     STOP.
 (3) Re-solve the BARE pjm-t1h (2021-2025, HEAD guard on, years sequential) and score it; run
     check_forecast_invariants on the sidecar; register the row (you are now the board writer
     for pjm-t1h). Report all 14 invariants and every FC-3 metric vs the committed row at full
     magnitude. Do not re-solve pjm-t1f (D65-B-R's row records its own sha; a later batch
     refresh owns it).
 (4) FINDING-capx-d75r-arm-<date>.md: keys before/after, the no-op table, the invariants table,
     FC-3 at full magnitude, and one paragraph stating what the arm does NOT close (over-
     retirement, unit recall, the 2024/25-2025/26 census direction). CLAUDE.md's Capacity
     Evolution list gains ONE bullet or one sentence under the D48 family naming the arm and
     Q55 (docs follow code). PJM's matrix shard cell: K-armed with the citation. Update
     docs/handoffs/d75r/full-gates.json only if it carries an "armed" field.
GATES THAT STOP YOU: any non-PJM or backcast key move; any change to the registry values, the
R1 reconciliation, or any ScenarioConfig default; the precondition above.
EXIT: PRECOMMIT, iso_configs.py + test edit, the pjm-t1h sidecar + board row, FINDING, CLAUDE.md
sentence, shard cell. Two PRs (PRECOMMIT + code; then the row + FINDING) or one - your call, but
the PRECOMMIT is pushed before the solve starts.
```

## D76 — PHASE 3 (HELD): NEISO + NYISO on the 2021–2023 window and a PJM re-A/B at a HEAD carrying D75-R-ARM (r#51)

```
You are the capx D76 phase 3 lane for jessicacohen554-cyber/market-simulator. MODEL: Opus.
DATA PROFILE: neiso, nyiso, pjm (hydrate one at a time, in that order).
Branch: claude/capx-d76-p3-neiso-nyiso-pjm, fresh off origin/main.
DISPATCH STOP: do NOT start until D75-R-ARM has MERGED to main (`git log origin/main
--grep="D75-R-ARM"` shows the FINDING commit and iso_configs.py::_pjm_config carries
pjm_vre_accreditation_vintage=True). Phase 1 ran without a release at r#50; this phase does
not. If the precondition is not met, stop and say so.

WHY. FINDING-capx-d76-p2-2026-09-06.md (merged #5228) measured the screen peak's ONE live
consumer (the adequacy requirement) across PJM / CAISO / ERCOT / MISO and found PJM INERT
end-to-end under D67-ARM - but section 4.1 states that PJM's accreditation inertness rests on
an ELCC curve that CLAMPS, "which is itself the defect capx D75-R is chartered to repair. If
pjm_vre_accreditation_vintage arms, PJM's census may become peak-sensitive again." Q55 armed it.
NEISO and NYISO were deferred at the director's call. The arming card (section 9) is served
by the director on THIS phase's table, never by you.

DO. Exactly the phase 2 protocol (PRECOMMIT-capx-d76-p2-2026-09-06.md + Addendum 1,
docs/handoffs/d76/p2_predeclare.py, p2_gate.py, p2_consumer_probe.py,
p2_accreditation_probe.py - reuse them, extend rather than fork):
 (0) PRECOMMIT-capx-d76-p3-<date>.md pushed BEFORE the first LP: the pre-declared measured peak
     per ISO-year (p2_predeclare), the control and arm keys for all six legs, G-DRIFT from
     e6a0402f (phase 2's base) to HEAD with every hunk classified (D75-R-ARM and D79 are LIVE
     for PJM keys by construction - say so and pre-declare the new PJM control key), the
     partition of expected-moved ledger fields per ISO, the six STOPs verbatim from phase 2,
     and the consumer table's expected verdicts per ISO (NYISO requirement-moot via D52 => the
     expectation is INERT like PJM-at-phase-2; write it down before solving).
 (1) Legs, sequential, one LP at a time, NO commits during a solve (D75-R and D76-P2 both
     tripped their own HEAD guards by committing mid-solve): NEISO 2021-2023 control + arm;
     NYISO 2021-2023 control + arm; PJM 2021-2025 control + arm at the post-D75-R-ARM HEAD.
 (2) Grade each ISO with p2_gate.py (STOP 1-6), the whole-ledger diff, the consumer probe and
     the accreditation probe at both peaks. For PJM the question is ONE thing: is the
     accreditation census still peak-inert now that the ELCC vintage is armed? Report the
     credits at both peaks per DY.
 (3) FINDING-capx-d76-p3-<date>.md: the six-ISO consumer table completed (phase 2's four rows
     carried verbatim, two new rows, PJM row re-measured and marked "re-measured post-Q55");
     every STOP; FC-3 at full magnitude never gated; and section 9 of phase 2 REDRAFTED with
     all six ISOs measured - drafted for the director, NOT served. Each ISO's matrix shard cell
     updated (rule 28(b), own-ISO shards only). Every control/arm bundle deleted before merge
     (rule 29(c)); every number lives in the FINDING and docs/handoffs/d76/p3_gate_<iso>.json.
GATES THAT STOP YOU: the dispatch STOP above; any commit during an LP; a realized key not
equal to its pre-declared value (re-declare in an addendum BEFORE the leg, never after); any
STOP firing (report it fired, do not reinterpret); arming anything.
EXIT: PRECOMMIT, three gate JSONs, FINDING with the redrafted card, three shard cells, bundles
deleted, one PR.
```

## D82 / D83 / D84 — RESERVED (r#51)

D82 unchanged in scope; D78-R2 §5 sharpens its object: the zero-E&AS operand is
per-delivery-year (D57 §4) and the CT plateau is LIVE by 2024/25 — a design read before any
charter, and D78-R3's per-DY set is an input to it. **D83 RESERVED** — `evolution_2022.json`
carries no adequacy block while 2021 / 2023–2025 do (D75-R §6 item 1, reproduced on a fresh
solve at HEAD; forced pool reconstruction in D75 and D75-R); a ledger-owning lane's defect,
charter after a zero-LP read of `capacity_evolution`'s 2022-bridge path. **D84 RESERVED** —
PJM's 2025/26 3IA THERMAL class ratings differ from the wired 2026/27 set (gas CC 78 vs 74,
CT 63 vs 60, steam 74 vs 73, diesel 92 vs 91; D75-R §6 item 4): D48's own half, the
"other half" of D66 card B; a follow-on card after D75-R-ARM lands, never a blocker on it.

## r#52 NOTE (2026-09-06): D65-B-R reached 6/7 (leg 6 merged #5250) and its branch was merged and DELETED again — the COMPLETION charter below is the sitting's only issuance and the program's critical path (D75-R-ARM and D76 phase 3 both wait on its board write). D78-R3 is RUNNING (`claude/capx-d78r3-perdy-set`, PRECOMMIT `e79a4ddd`) — do NOT re-dispatch it. D75-R FACADE FIX is EXECUTED and open as PR #5257 — merge it, do not re-issue. D75-R-ARM and D76 PHASE 3 keep their dispatch STOPs unmet and are NOT re-emitted here.

## D65-B-R COMPLETION — leg 7, the board write, and the finding's §0/§6 (r#52; the batch's last third, re-dispatched after its branch merged and was deleted)

```
You are the D65-B-R COMPLETION session of the capacity-expansion track. The D65-B-R batch (owner
ruling Q47, "Arm coupled, after D60-R3") is 6 of 7 legs done and ON MAIN; its branch merged and was
deleted, so you start fresh. You are FINISHING it, not re-opening it. MODEL: Opus. DATA PROFILE: all.
BRANCH: claude/capx-d65br-completion — FRESH off origin/main. Base: origin/main at your first fetch.

BINDING CHARTER: pack §D65-B-R (the original, whose STEP 3 and STEP 4 you are completing) + this
section + `docs/handoffs/FINDING-capx-d65br-2026-09-06.md` (§1–§5.6, all six landed legs — their
numbers STAND and are NOT re-solved) + `PRECOMMIT-capx-d65b-2026-09-06.md` Addendum C (the pre-declared
per-ISO gates) + `FINDING-capx-d64-2026-09-05.md` §2.3 and §2.4 (the per-ISO census table every gate is
read from). Capx ledger §0aw is this charter's grading record.

WHAT IS ALREADY DONE — DO NOT REDO ANY OF IT. Legs 1-6 (`ercot-t1f`, `neiso-t1f`, `nyiso-t1f`,
`caiso-t1f`, `pjm-t1f`, `miso-t1f`) are solved and their artifacts are committed under
`results/ff-t1f-d65br/{ercot,neiso,nyiso,caiso,pjm,miso}/`. Step 0 (the persisted `retrofit_log`
scaling fields) and Steps 1-2 (the re-pin, the all-INERT G-DRIFT, Addendum C) are on main. The ERCOT
screen is NOT re-run (rule 29: a screen bundle is spent once).

STEP A — LEG 7, the only solve you spend: `neiso-t3` GOLDEN-3 (~33 min), sequential, scored, verdict,
registered in place with its `-pre-d65b` prior, graded against Addendum C's G0'-G6' exactly as legs 1-6
were. D64 §2.3 POSITIVELY INDICATES this leg — that is an expectation to test, never a target to hit;
report the measurement whichever way it falls. HEAD GUARD, mandatory: H0=$(git rev-parse HEAD);
<solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. Rebase BETWEEN legs only, never during one;
re-audit any rebase delta hunk by hunk before proceeding (REBASE-THEN-RE-AUDIT), with `constants.py`
read first — a matched cache key is not a G-DRIFT verdict, and since D79 the solve-surface fingerprint
is in the key but the audit still reads `constants.py` first.

STEP B — THE BOARD WRITE, for ALL SEVEN legs at once. This is the deliverable the rest of the program
is waiting on. Measured at r#52: `frontend/data/forecast/ff-verdicts.json` was last touched by D63
(#5108) — this batch has written NO board byte at all, so all seven rows are yours, not just leg 7's.
Register through the SINGLE `scripts/register_forecast_run.py` path over the `frontend/data/forecast/`
namespace (rule 15: NEVER the backcast registry; the backcast CI gates stay blind to this namespace).
The generated `registry/<id>.json` / `runs/<id>.js` / `manifest.js` / `program-status.js` are gitignored
and rebuilt by the Pages deploy; the COMMITTED inputs are the hindcast sidecars + `ff-verdicts.json` +
the `program-status.json` board seed. State in the finding that the board is now in ONE demand vintage
(post-`d14a7ed0`) and say which rows moved because of that rather than because of the acts.

STEP C — FINDING §0 AND §6, plus one ordering repair. Fill §0 "The verdicts" (currently the placeholder
"*(filled at the close of the batch)*") with the per-ISO Addendum C grade and the batch verdict. Fill
§6 Governance, and MOVE it: §6 currently sits at line ~142 BETWEEN §5.1 and §5.2, so §5.2-§5.6 read as
if they were inside governance. Put §6 after §5.7. Governance carries the rule-27 blob checks, the D8
curated DOF rows for the flipped default, the D77 §8 blast-radius reconciliation (every retrofit row now
carries the captured rate), the D50 §6.2 radius, and an explicit statement that the D72-prehunk
`neiso-t1f` residue key is DISCHARGED by this batch's re-solve.

STEP C-2 — THE BASIS DISCLOSURE, and it is the director's defect, not yours. Your leg 6 established the
general form: "All three fired gates share one root: Addendum C compares a HEAD solve against a prior
that predates HEAD, and two of the three are measuring that gap, not the arm." That is true, it is a
defect in the charter I wrote, and §0 must say so in those terms. Concretely: G5' fired on `neiso-t1f`
and `nyiso-t1f` (VOIDED as a STOP by director adjudication r#51 §0av.3(b) on the narrower ground that
the gate contradicted D64 §2.3's own sentence — those legs REGISTER), and G4' fired on `miso-t1f` and is
provably not the acts' (I3 fails from 2026; `apply_ccs_retrofit` returns at year <
`ccs_retrofit_available_year` before reading either field; G0' measured 0 rows in 2026 and 2027). Record
all three as ONE root with its arithmetic. This is a BASIS DISCLOSURE, not a re-grade: no leg's numbers
change, no gate is retro-declared passed, no prior is re-solved, and each fired gate stays reported at
full magnitude. If leg 7 fires a gate whose root is the same vintage gap, grade it the same way — fired,
disclosed, with the arithmetic that shows what it measured.

STEP D — MATRIX (rule 28): the `ccs_retrofit_screen` row's def/note carries Act B; the
`ccs_retrofit_fixed_cost_co2_scaling` row's cells read `fc: K` where the arm is now the bare leg. Six
shards, ONE line each, in the last commit — a lane edits only the cells its own evidence covers.

STOP GATES. (1) Leg 7 exceeding the D60 wall/RSS envelope (G6') — stop and report, do not retry blind.
(2) The HEAD guard tripping (exit 90) — rebase, re-audit, re-solve that leg. (3) Any board row you
cannot reconcile to a committed leg artifact — stop; do not hand-author a row. (4) A gate you cannot
grade from a committed document — stop and route to the director rather than inventing a band.

DO NOT: re-solve legs 1-6 or the ERCOT screen; arm anything (this batch arms nothing beyond Q47's
already-landed Acts A+B); touch the backcast registry, another desk's ledger, or any ISO shard your
evidence does not cover; widen scope to D82/D83/D84.

COLLISIONS: you are the SOLE writer of `ff-verdicts.json` and `program-status.json` until your board
write lands — D67-ARM, D78-R and D81's queued rows all sit behind you, which is why this is the critical
path. D78-R3 is RUNNING on `claude/capx-d78r3-perdy-set` and writes docs + JSON only; you will not
collide, but rebase between legs and re-audit if it merges under you. Rules 12, 15, 22 (forecast mode
only), 24, 25, 27, 28, 29.

EXIT: leg 7 solved, scored and registered with its prior; all seven board rows written and committed;
FINDING §0 and §6 filled with §6 correctly ordered and the basis disclosure in §0; six matrix shards
stamped; rule-27 blob verification recorded for any file >=300 lines you push. Nothing else arms. Report
the batch verdict and the seven-row before/after board table in your close.
```

## r#53 NOTE (2026-09-06): the whole r#52 queue landed. FOUR charters below, ALL DISPATCHABLE NOW — and note the STOP form has changed: a STOP now names an ACT, never a session (§0ax.2(b)), so D78-ARM and D76-P3B start immediately and hold only their solve/register step. ORDERING CONSTRAINT: D75-R-ARM steps 3–4 must register the bare `pjm-t1h` before D78-ARM moves that key again, or the two PJM arms become inseparable on the board.

## D65-B-R COMPLETION-2 — leg 7 and the finding's §0/§6 (r#53; the board write landed #5283, this is the last third)

```
You are the D65-B-R COMPLETION-2 session of the capacity-expansion track. The batch (owner ruling
Q47) has SIX legs registered on main and its board write merged as #5283. You are finishing it.
MODEL: Opus. DATA PROFILE: all. BRANCH: claude/capx-d65br-completion2 — FRESH off origin/main.

BINDING: pack §D65-B-R (the original) + this section + docs/handoffs/FINDING-capx-d65br-2026-09-06.md
+ PRECOMMIT-capx-d65b-2026-09-06.md Addendum C (the pre-declared per-ISO gates) and Addendum G (the
fourth rebase re-audit) + FINDING-capx-d64-2026-09-05.md §2.3/§2.4. Capx ledger §0ax is the grading
record.

ALREADY DONE — DO NOT REDO, RE-GRADE, RE-SOLVE OR RE-REGISTER ANY OF IT. Legs 1-6 are solved,
graded and REGISTERED: ercot 9b9e5a48e3ca5c8e, neiso c3519b861f920bbe, nyiso f62431376dd9df03,
caiso 17770cdad3230938, pjm 542eeedadab83ee1, miso 74359fedbf2eadd6 — every key equal to the
Addendum C pre-declaration to the digit (PJM on Addendum E's re-declaration). Their sidecars are on
main under frontend/data/hindcast/. Step 0 and steps 1-2 are on main. The ERCOT screen is NOT re-run.

STEP A — LEG 7, your only solve: neiso-t3 GOLDEN-3 (~33 min), sequential, scored, verdict, registered
in place with its -pre-d65b prior through the SINGLE scripts/register_forecast_run.py path, graded
against Addendum C's G0'-G6' exactly as legs 1-6 were. D64 §2.3 POSITIVELY INDICATES this leg — an
expectation to test, never a target to hit; report the measurement whichever way it falls. HEAD GUARD:
H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. Rebase BETWEEN legs
only, never during one; re-audit any rebase delta hunk by hunk with constants.py read first.

STEP B — ANSWER A QUESTION THE DIRECTOR GOT WRONG, and treat it as open. At r#52 I asserted the batch
had "written no board byte" and proved it by citing frontend/data/forecast/ff-verdicts.json. That was
the WRONG INSTRUMENT: the registration artifact is the per-run hindcast sidecar under
frontend/data/hindcast/ (7 files in c36a3fe7, zero under frontend/data/forecast/), while
ff-verdicts.json is the FF-2D VERDICT SNAPSHOT, a different object that moves only when a verdict
moves. So the genuinely open question, which I am NOT asserting either way: DO any of the seven legs
require an ff-verdicts.json update? Determine it from the code path (register_forecast_run.py, what
writes ff-verdicts.json, and what --reindex consumes) and from rule 15's list of committed inputs.
Report the answer with its evidence. If yes, make the update and say which verdicts moved and why. If
no, say so and say what WOULD have moved it. Either answer is a good outcome; an unexamined one is not.

STEP C — FINDING §0 AND §6, plus the ordering repair. Fill §0 "The verdicts" (still the placeholder
"*(filled at the close of the batch)*") with the per-ISO Addendum C grade and the batch verdict. Fill
§6 Governance and MOVE it: §6 currently sits at line ~142 BETWEEN §5.1 and §5.2, so §5.2-§5.6 read as
if they were inside governance. Put §6 after your new §5.7. Governance carries the rule-27 blob
checks, the D8 curated DOF rows for the flipped default, the D77 §8 blast-radius reconciliation, the
D50 §6.2 radius, and an explicit statement that the D72-prehunk neiso-t1f residue key is DISCHARGED.

STEP C-2 — THE BASIS DISCLOSURE, and it is the director's defect, not yours. Your leg 6 established
the general form: "All three fired gates share one root: Addendum C compares a HEAD solve against a
prior that predates HEAD, and two of the three are measuring that gap, not the arm." That is true and
§0 must say so in those terms. Concretely: G5' fired on neiso-t1f and nyiso-t1f (VOIDED as a STOP by
director adjudication r#51 §0av.3(b) and reclassified to REPORTED — those legs registered), and G4'
fired on miso-t1f and is provably not the acts' (I3 fails from 2026; apply_ccs_retrofit returns at
year < ccs_retrofit_available_year before reading either field; G0' measured 0 rows in 2026 and 2027).
Record all three as ONE root with its arithmetic. BASIS DISCLOSURE, not a re-grade: no leg's numbers
change, no gate is retro-declared passed, no prior is re-solved, every fired gate stays reported at
full magnitude. Grade leg 7's gates the same way if one fires on the same vintage gap.

STEP D — MATRIX (rule 28): the ccs_retrofit_screen row's def/note carries Act B; the
ccs_retrofit_fixed_cost_co2_scaling row's cells read fc: K where the arm is now the bare leg. Six
shards, ONE line each, last commit. Edit only cells your own evidence covers.

STOP GATES. (1) Leg 7 exceeding the D60 wall/RSS envelope (G6') — stop and report, do not retry blind.
(2) HEAD guard trip (exit 90) — rebase, re-audit, re-solve. (3) A board row you cannot reconcile to a
committed leg artifact — stop, do not hand-author it. (4) A gate you cannot grade from a committed
document — stop and route to the director rather than inventing a band.

DO NOT: re-solve legs 1-6 or the ERCOT screen; arm anything; touch the backcast registry, another
desk's ledger, or any ISO shard your evidence does not cover; widen to D82/D83/D84.

COLLISIONS: you are NEISO and you collide with nobody this window. Three PJM lanes are live
(D75-R-ARM steps 3-4, D78-ARM, D76-P3B); stay out of PJM's shard and PJM's sidecars. Rules 12, 15,
22 (forecast mode only), 24, 25, 27, 28, 29.

EXIT: leg 7 solved, scored, registered with its prior; the ff-verdicts question answered with
evidence; FINDING §0 and §6 filled with §6 correctly ordered and the basis disclosure in §0; six
matrix shards stamped; rule-27 blob verification for any file >=300 lines pushed. Nothing else arms.
Report the batch verdict and the seven-row board table.
```

## D75-R-ARM STEPS 3–4 — the held re-solve and board registration, STOP now MET (r#53)

```
You are the D75-R-ARM STEPS 3-4 session of the capacity-expansion track. Steps 1-2 LANDED
(#5267/#5272, 6164231e): pjm_vre_accreditation_vintage is ARMED for PJM under owner ruling Q55. You
held steps 3-4 behind D65-B-R's board write. THAT BOARD WRITE MERGED (#5283, c36a3fe7). THE STOP IS
MET. MODEL: Opus. DATA PROFILE: pjm. BRANCH: claude/capx-d75r-arm-steps34 — FRESH off origin/main.

BINDING: PRECOMMIT-capx-d75r-arm-2026-09-06.md + FINDING-capx-d75r-2026-09-06.md + the D67-ARM
precedent (FINDING-capx-d67arm-2026-09-06.md, whose §2.1 recorded the moving-control-legs miss
against itself). Capx ledger §0ax.1 is the grading record for steps 1-2.

WHAT IS ALREADY TRUE, MEASURED, DO NOT RE-ARGUE IT. The arm is an ISO override in
_pjm_config.default_scenario_overrides, not a shared default flip. Of 153 committed run configs the
21 PJM FORECAST configs move and all 132 others are byte-identical. Bare pjm-t1h goes
a9c66d8ea25acb9d -> b518f5fe7d02f961, which IS D75-R's own measured full-window arm key;
--no-pjm-vre-accreditation-vintage reaches the pre-arm control and keeps a9c66d8ea25acb9d.

STEP 3 — RE-SOLVE the bare pjm-t1h at the armed key b518f5fe7d02f961, preserving its prior as
-pre-d75rarm. DECLARE the realized key against b518f5fe7d02f961 BEFORE the solve, in a short addendum
pushed first, and report realized-vs-declared. HEAD GUARD mandatory: H0=$(git rev-parse HEAD);
<solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. If the realized key is not
b518f5fe7d02f961, STOP and report — that would mean the arm does not reproduce D75-R's measured
recipe and the whole Q55 basis needs re-reading.

STEP 4 — REGISTER through the SINGLE scripts/register_forecast_run.py path over the
frontend/data/forecast namespace (rule 15; the committed artifacts are the per-run hindcast sidecar
under frontend/data/hindcast/ plus ff-verdicts.json and program-status.json — see the note below).
Score the row, report every invariant at full magnitude, and DECLARE any FAIL against the leg's own
committed prior in the same commit (the Y-24 ratchet). A declaration is not a fix: nothing is
relaxed, re-scored or exempted.

NOTE ON THE COMMITTED ARTIFACT SET, because the director got this wrong at r#52 and corrected it at
r#53: register_forecast_run.py writes the per-run hindcast sidecar; ff-verdicts.json is the FF-2D
verdict snapshot and moves only when a verdict moves. Determine from the code path which of the two
your registration must touch, and say which and why in your close.

THE FOUR D57/D67 CONTROL LEGS MOVE, and that was PRE-DECLARED in PRECOMMIT §2.1 rather than
discovered afterwards — the exact miss FINDING-capx-d67arm §2.1 recorded against itself. Handle them
as that precedent did: name each, say why it moved, and do not treat the movement as a defect.

DO NOT: arm anything further; touch retirement_sector_gate (D78-ARM owns it and must register AFTER
you); re-open D75-R's A/B; touch another ISO's shard (rule 25 — PJM only, locked by test across the
other five).

COLLISIONS AND WHY YOU GO FIRST. You must register the bare pjm-t1h BEFORE D78-ARM moves that key
again, or the VRE-devintage arm and the sector-gate arm become inseparable on the board. D78-ARM and
D76-P3B both carry an explicit STOP naming your board row as what they wait on, and both are doing
zero-LP work until it lands. Push promptly and say in your close that the row is on main. Rules 12,
15, 24, 25, 27, 28, 29.

EXIT: bare pjm-t1h re-solved at the declared key with the HEAD guard held; registered with its prior
preserved; every invariant reported and every FAIL declared against its own prior; the PJM matrix
shard stamped; the ff-verdicts question answered for your own registration; rule-27 blob verification
for any file >=300 lines. Report the key realized-vs-declared and the before/after row.
```

## D78-ARM — arm `retirement_sector_gate` for PJM under owner ruling Q56, WITH REGISTRATION REQUIRED (r#53)

```
You are the D78-ARM session of the capacity-expansion track, executing OWNER RULING Q56 (capx ledger
§0ax.3(a), r#53): "ARM, registration required." MODEL: Opus. DATA PROFILE: pjm. BRANCH:
claude/capx-d78-arm-sector-gate — FRESH off origin/main.

BINDING: FINDING-capx-d78r3-2026-09-06.md (§0 the verdict, §5 the flip condition, §5.2 the six things
the card had to state) + FINDING-capx-d78r2 + FINDING-capx-d78r + FINDING-capx-d57 §4 (the per-DY
rows the whole recommendation rests on) + owner ruling Q53 (must-offer reading 1: a sector-1 unit
still offers). Capx ledger §0ax.1/§0ax.3(a).

THE RULING, IN FULL. Arm retirement_sector_gate for PJM through iso_configs.py::_pjm_config
default_scenario_overrides — the D57/Q44 -> D67-ARM -> Q55 way. NEVER a shared ScenarioConfig default
flip: no _CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS entry, every other ISO and every backcast keeper
byte-identical, and an explicit --no-retirement-sector-gate must reach the pre-arm posture and keep
the pre-arm key. Assert all of that by test and by a --simulate-arm no-op probe run BEFORE
iso_configs.py is touched and again after with the flag omitted, exactly as D75-R-ARM did.

THE REGISTRATION CONDITION IS PART OF THE RULING, NOT A NOTE ON IT. D78-R3 §5.2 item 1: the evidence
for limbs (b), (c) and (d) rests on an arm bundle committed NOWHERE, because the D78-R2 arm was never
registered (merge 80c88b76 landed docs and JSON only). Arming means solving AND REGISTERING PJM T1-H
on the new default, which closes that gap by construction. The owner ruled that this is REQUIRED, not
waivable. A run that arms without registering does not discharge Q56.

*** STOP — AN ACT, NOT A DISPATCH. *** Begin immediately: the config act, the G-DRIFT audit, the key
declaration, the no-op probe and the PRECOMMIT are all zero-LP and are yours to do now. But DO NOT
SOLVE AND DO NOT REGISTER the armed PJM T1-H until D75-R-ARM's board row for the bare pjm-t1h is on
main. Reason, stated so you can verify it rather than trust it: D75-R-ARM moved that key
a9c66d8ea25acb9d -> b518f5fe7d02f961 and its row is not yet registered; if you move the key again
first, the VRE-devintage arm and the sector-gate arm become inseparable on the board. Check with:
git log origin/main --oneline --grep="D75-R-ARM" and confirm a registered bare pjm-t1h row exists.
If it has not landed when your zero-LP work is done, say so and hold.

PRE-REGISTER, BEFORE ANY VALUE IS OPENED: the declared key for the armed leg; the expected direction
of every metric you will report; and the six items D78-R3 §5.2 requires the record to carry, which you
must report at full magnitude whichever way they fall —
 1. limbs (b)/(c)/(d) were CARRIED from D78-R2, not re-measured, and their control bundle is not
    committed; your registration is what fixes that going forward.
 2. retire.total_gw moved FAIL -> PASS (18.058 -> 15.937 vs 15.062 actual). It is EXPLICITLY NOT a
    criterion in either direction (rule 14) and is NOT an argument for arming; a worse number would
    not have been an argument against. Do not cite it as support.
 3. unit_recall_gt300 FALLS 0.650 (13/20) -> 0.550 (11/20). A partition that removes matched sector-1
    exits must lose recall. Report it; it is not a criterion.
 4. the 2025 clearing price moves 358.267 -> 236.945 $/MW-day, because the control's cleared position
    (0.998023) sits short of the requirement on the steep VRR limb and the arm's extra 1,671.625 MW
    carries it to 1.009595. Report it; it is not a criterion.
 5. limb (d) CANNOT discriminate on recall in either leg (the control holds no recall-PASS fold); do
    not read it as positive evidence.
 6. W5''s PASS came from a corrected DECLARATION, not a new measurement, and the structural derivation
    is one-sided and SILENT on gas_ct and gas_st — the two classes that decide 2022/23 and 2023/24 —
    and has a proven false-positive class (nuclear derives at bar in all four DYs and belongs at none;
    the subset guard caught it). The derivation CORROBORATES the declaration; it does not replace it.
    Say this in the finding's head, not a footnote.

ZERO DOF. No new ScenarioConfig field, no parameter value, no retirements.py decision logic, no
keeper, no marker. The act is one override entry plus the solve and the registration.

MATRIX (rule 28): PJM's shard only — retirement_sector_gate's PJM cell to K with the Q56 citation.
Rule 25: the verdict is PJM's and transfers to no other ISO.

STOP GATES. (1) The armed key not equal to your pre-declaration — stop and report. (2) HEAD guard
trip (exit 90) — rebase, re-audit, re-solve. (3) Any non-target load-bearing invariant flipping
PASS -> FAIL — report it, declare it against the leg's own prior (Y-24), and do not relax or exempt
it. (4) --no-retirement-sector-gate failing to reproduce the pre-arm key — stop; the override is not
clean.

EXIT: retirement_sector_gate armed for PJM via _pjm_config; the no-op probe recorded both sides; PJM
T1-H solved AND REGISTERED on the new default with its prior preserved; all six §5.2 items reported at
full magnitude in the finding's head; PJM matrix shard stamped; rule-27 blob verification for any file
>=300 lines. Report the key realized-vs-declared, the before/after row, and Q56 discharged.
```

## D76 PHASE 3B — the PJM leg phase 3 could not ask, now that the vintage is armed (r#53)

```
You are the D76 PHASE 3B session of the capacity-expansion track. Phase 3 LANDED (#5268/#5315,
be871bec) and measured NEISO and NYISO with every STOP clean. It could NOT answer the charter's PJM
question, and its FINDING says so in those words: D75-R-ARM had not merged at that HEAD, so PJM's row
is phase 2's, carried verbatim and stamped NOT re-measured. It is now armed. You ask the question.
MODEL: Opus. DATA PROFILE: pjm. BRANCH: claude/capx-d76-p3b-pjm — FRESH off origin/main.

BINDING: FINDING-capx-d76 phases 2 and 3 + PRECOMMIT-capx-d76-p3 (whose no-commit-between-A/B-legs
rule you INHERIT — phase 2 took a literal STOP-3 FAIL from exactly that, and phase 3's fix worked) +
FINDING-capx-d67 / D67-ARM (PJM's requirement gate) + FINDING-capx-d75r + the D75-R-ARM record. Capx
ledger §0ax.1.

THE QUESTION, precisely: is PJM's accreditation census still PEAK-INERT now that
pjm_vre_accreditation_vintage is armed? Phase 2 measured PJM INERT under D67-ARM. Phase 3 established
the mechanism twice over — PJM's inertness comes from D67, NYISO's from D52, and mooting the
requirement moots the mechanism. Phase 3B tests whether arming the VRE devintage changes that, on PJM
alone.

*** STOP — AN ACT, NOT A DISPATCH. *** Begin immediately: phase 0, the zero-LP declaration, the
p3b_predeclare.json key emission and the PRECOMMIT are yours to do now. But DO NOT SOLVE the PJM A/B
until D75-R-ARM's board row for the bare pjm-t1h is on main. Reason you can verify: your control must
be unambiguous, and until that row registers the PJM board carries a key (b518f5fe7d02f961) that no
registered row corresponds to. Check with git log origin/main --oneline --grep="D75-R-ARM".

CARRY PHASE 3's DISCIPLINE, all of it: every realized cache key must EQUAL the value machine-emitted
into p3b_predeclare.json before the first LP; NO COMMIT BETWEEN THE LEGS OF THE A/B; one solve-code
state for both legs, named; STOPs 1-6 in the phase-3 form, pre-registered; the whole-ledger diff with
EVERY moved field classified and ZERO UNCLASSIFIED (D81 rec 4). HEAD GUARD around each leg:
H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90.

REPAIR PHASE 3's TWO DISCLOSED WEAKNESSES rather than inheriting them: (i) phase 3's control seam peak
reproduced its zero-LP declaration only to 0.005-0.065 MW, an order of magnitude looser than phase 2,
with a system-load fallback offered as hypothesis not finding — tighten the declaration or say
explicitly why it cannot be tightened; (ii) run_capacity_hindcast.py --help crashes on an unescaped %
in a help string, reported by phase 3 and not repaired. Repair it if it is a one-line fix in your path
(rule 27: targeted edit, push on-disk bytes, blob-verify if the file is >=300 lines); otherwise route
it with the line number.

THE CARD. D76's arming card is a FIVE-OF-SIX card today and phase 3 labelled it one and recommended
NOTHING, because a rule-29 screen may kill an arm and may never promote one. That is correct and you
inherit it: YOU DO NOT RECOMMEND ARMING. Your output is PJM's measured row, which completes the card
so the DIRECTOR can serve it. If PJM measures live where phase 2 measured it inert, that is the
finding — report it and stop; do not propose the arm.

DELETE BEFORE MERGE (rule 29(c)): every bundle you solve is deleted before your PR merges, and the
PRECOMMIT/FINDING carries every number you will ever cite from it — including, named before deletion,
which committed instrument carries every structure a successor could need. Phase 3 deleted all four
of its bundles; D78-R3 paid for an earlier lane that deleted a control without naming its derivation
base. Do not repeat that.

MATRIX (rule 28): PJM's shard only, and only the cells your own evidence covers (rule 25 — phase 3
correctly left four shards untouched because it did not test them).

DO NOT: arm anything; register anything; touch retirement_sector_gate (D78-ARM owns it); touch
NEISO/NYISO's rows (phase 3 owns them); widen beyond PJM.

EXIT: PJM's peak-inertness question ANSWERED with a measured A/B, every key equal to its
pre-declaration, every STOP graded, the whole-ledger diff at zero unclassified, the two phase-3
weaknesses repaired or explicitly routed, bundles deleted before merge, PJM matrix shard stamped.
Report the six-ISO synthesis row for PJM and state plainly whether the D76 card is now six-of-six.
```

## r#54 NOTE (2026-09-07): FIVE charters, all DISPATCHABLE NOW. D76 phase 3B closed its card six-of-six and Q57 RULED ARM via the D50 (b′-1) route. D78-ARM is ARMED on a live branch and was interrupted by owner reassignment — it is re-dispatched to COMPLETE, never to re-derive. D65-B-R COMPLETION-2 and D75-R-ARM STEPS 3–4 were never dispatched at r#53 and are re-emitted WHOLE. THE BARE `pjm-t1h` KEY NOW HAS THREE VINTAGES IN PLAY (`a9c66d8ea25acb9d` pre-Q55 · `b518f5fe7d02f961` post-Q55 · `fb16fda2ddb0a94a` post-Q56, on D78-ARM's unmerged branch) — whichever PJM lane registers first MUST NAME its key in the row, and the second rebases and re-declares rather than assuming.

## MISO gate-(a) RE-KEY — the Q34 standing duty, fifteenth firing (r#54)

```
You are a one-act MISO gate-(a) re-key session for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. BRANCH: claude/miso-gate-a-rekey-q34 — FRESH off origin/main.

THE DEFECT. scripts/check_gate_a_provenance.py is RED on main:
  MISO: gate.a_keeper_marker cites SUPERSEDED keeper '2026-09-06-miso-230-ctdrag-seam';
  the ISO's current designated keeper is '2026-09-06-miso-232-hourly-seam'.
The owner's MISO lane promoted miso-232 without re-keying the gate-(a) board row in
frontend/data/forecast/program-status.json. FIFTEENTH firing of the Q34 duty, THIRTEENTH promoter
miss since R-T. Record it in those terms. (NEISO's same-window promotion to neiso-106 did NOT miss —
its row was re-keyed at source, which is the pattern that makes this duty stop firing.)

YOUR ONLY JOB is that one row. Do not touch any other ISO's row, any other gate leg, any keeper
shard, calibration-complete.json, or the backcast namespace. Nothing is solved, scored or registered.

METHOD — BINDING. Edit frontend/data/forecast/program-status.json by TARGETED STRING EDIT scoped by
string position (Edit tool or an assert-guarded str.replace). NEVER a json.dumps round-trip: this
file's formatting is load-bearing and a re-serialize would rewrite the whole document — the rule 27
[R-PUSH] hazard, and file-integrity-guard would NOT catch it because a reformat is not a >30 %
shrink. Assert each old string occurs exactly once BEFORE replacing, and assert json.load() parses
AFTER. Watch for a LEADING SPACE where the prior text continues, so a prepended clause does not leave
a double space. Push the exact on-disk bytes and blob-verify after the push (fetch the file back,
compare line count + hash to local) — program-status.json is well over 300 lines.

THE THREE LEAVES, all inside the MISO block:
 1. gate.a_keeper_marker.detail — replace the head naming '2026-09-06-miso-230-ctdrag-seam' with the
    live keeper id and live determination, and prepend a RE-KEYED clause AHEAD OF THE PRESERVED PRIOR
    TEXT (preserve it verbatim; do not delete it).
 2. gate.a_keeper_marker.read_live_at — the sha you actually read at; move the existing corrected_by
    text under a "PRIOR:" label rather than deleting it.
 3. the top-level gate_a_provenance block — derived_at_sha, derived_at_date, and derived_by with the
    supersession chain prepended ahead of the preserved prior derived_by text.

READ EVERY FACT LIVE at your own HEAD before writing — keeper id and registry years from
frontend/data/backcast/keepers/MISO.json and the registry sidecar; determination, grade summary,
fails, ledgered caveats and C1 counts from frontend/data/backcast/status/MISO.js; the rubric version
from RUBRIC_VERSION in scripts/calibration_verdict.py; marker state from
frontend/data/backcast/calibration-complete.json. Do NOT copy figures from any prior row.

STATE THE VERDICT EFFECT PRECISELY. MISO is NOT in the `complete` block (the owner declined it at
Q49), so gate (a) reads FAIL before and FAIL after — the marker did not move and this re-key changes
IDENTITY AND DETERMINATION TEXT ONLY. Say exactly that in the row; do not imply the promotion changed
the gate.

EXIT: check_gate_a_provenance.py exits 0; json.load parses; `git diff` touches exactly the three
leaves in one file and nothing else; the prior text is preserved in all three; commit, push,
blob-verify. Report the diff and the gate exit code. Do not open a PR unless asked.
```

## D78-ARM COMPLETION — finish the interrupted lane: items (1)–(6), Q56's registration condition (r#54)

```
You are the D78-ARM COMPLETION session. The D78-ARM lane executed owner ruling Q56, ARMED
retirement_sector_gate for PJM, pushed and blob-verified it — and was then INTERRUPTED BY OWNER
REASSIGNMENT to SPP-14. You finish it. MODEL: Opus. DATA PROFILE: pjm.
BRANCH: continue on claude/pjm-retirement-sector-gate-at0cao (rebase onto origin/main first). If you
must branch fresh, branch FROM that branch, never from main — the arm lives only there.

YOU COMPLETE; YOU DO NOT RE-DERIVE. The arm (a154222c) is complete and blob-verified, and every
PRECOMMIT expectation reproduced exactly (docs/handoffs/d78arm/*measured.json). You may NOT re-argue
the arm, re-run the probes, or re-open Q56. If a probe now disagrees with the PRECOMMIT, STOP and
report — that is also not re-deriving.

WHAT IS ALREADY TRUE, MEASURED: _pjm_config default_scenario_overrides gains
retirement_sector_gate=True; the shared ScenarioConfig default stays False, so every other ISO and
every backcast key is byte-identical. Bare pjm-t1h b518f5fe7d02f961 -> fb16fda2ddb0a94a. Cache-epoch
2026-09-06h. PJM matrix cell O -> K. VERDICT_MAP re-keyed (d67arm -> pjm-t1h-pre-d78arm; the armed
re-solve takes pjm-t1h). The override pin re-keyed with every inverse beside it.

THE SIX ITEMS THE LANE ITSELF LEFT OWED, verbatim from its WIP commit 3b369f26:
 (1) tests/unit/config/test_d67arm_pjm_requirement.py TestQ52ArmingKeys — BARE_PJM_ARMED must move
     a9c66d8ea25acb9d -> fb16fda2ddb0a94a, and the explicit-off leg needs
     pjm_vre_accreditation_vintage=False + retirement_sector_gate=False beside
     capacity_adequacy_requirement_published=False to reach 15a723ba3b6dc856. Measured at the lane's
     HEAD: bare fb16fda2ddb0a94a, no-req 250882fbbbf64377, no-req+no-vre+no-gate 15a723ba3b6dc856.
     NOTE: this test was ALREADY RED on main since 6164231e (Q55 moved the bare key without
     re-pinning the file) and a separate commit d41ac928 has since landed on main claiming to repair
     the stale PJM cache-key pins. RE-READ THAT FILE AT YOUR HEAD FIRST and reconcile: state whether
     d41ac928 already did item (1), partly did it, or did something else, before you edit anything.
 (2) a data/clean rebuild (regenerate_clean.py) — the lane was killed at 6/56 datatypes.
 (3) the solve: bash docs/handoffs/d78arm/run_arm.sh (expected key fb16fda2ddb0a94a). HEAD GUARD:
     H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. If the
     realized key is not fb16fda2ddb0a94a, STOP and report.
 (4) score_capacity_hindcast.py --bundle ... and --flip-gate-extras.
 (5) register_forecast_run.py --bundle ... (VERDICT_MAP already re-keyed). THIS IS Q56's REGISTRATION
     CONDITION and it is part of the ruling, not a note on it: arming without registering does not
     discharge Q56.
 (6) the slim record + sidecar commit, FINDING-capx-d78arm-2026-09-06.md, the PR.

NAME YOUR KEY IN THE ROW. The bare pjm-t1h key has THREE vintages in play: a9c66d8ea25acb9d (pre-Q55),
b518f5fe7d02f961 (post-Q55, which the D75-R-ARM STEPS 3-4 lane was chartered to register), and
fb16fda2ddb0a94a (yours, post-Q56). Whichever of the two PJM registration lanes lands first must state
in its row which key it carries; if D75-R-ARM steps 3-4 has landed before you, rebase and re-declare
rather than assume. Check with: git log origin/main --oneline --grep="D75-R-ARM".

REPORT AT FULL MAGNITUDE, from FINDING-capx-d78r3 §5.2, whichever way they fall: retire.total_gw's
FAIL -> PASS is EXPLICITLY NOT an argument for arming (rule 14) and must not be cited as support;
unit_recall_gt300 falls 0.650 -> 0.550; the 2025 clearing price moves 358.267 -> 236.945 $/MW-day;
limb (d) cannot discriminate on recall; limbs (b)/(c)/(d) were carried, not re-measured, and YOUR
registration is what closes that gap; and W5''s PASS came from a corrected DECLARATION, not a new
measurement, with the derivation one-sided and silent on gas_ct/gas_st.

THE BOARD SNAPSHOT STAYS HELD (the D65-B-R lock), exactly as the WIP commit says.

MATRIX (rule 28): PJM's shard only; the cell is already O -> K — verify, do not duplicate.

EXIT: items (1)-(6) done; d41ac928 reconciled and stated; the armed leg solved at fb16fda2ddb0a94a
with the HEAD guard held, scored, and REGISTERED with its prior preserved; the §5.2 disclosures in the
FINDING's head; rule-27 blob verification for any file >=300 lines. Report the key realized-vs-declared,
the before/after row, and Q56 discharged.
```

## D76-ARM — arm `capacity_screen_peak_measured_hindcast` under owner ruling Q57, via the D50 (b′-1) route (r#54)

```
You are the D76-ARM session, executing OWNER RULING Q57 (capx ledger §0ay.3(a), r#54): "ARM via the
D50 (b′-1) route." MODEL: Opus. DATA PROFILE: code, widening to all if a verification solve is needed.
BRANCH: claude/capx-d76-arm-measured-peak — FRESH off origin/main.

BINDING: FINDING-capx-d76-2026-09-06.md + -p2- + -p3- (whose §7 is the card the owner ruled on) +
PRECOMMIT-capx-d76-measured-screen-peak-2026-09-06.md + the D50/Q42 landing as the ROUTE precedent
(CLAUDE.md, Capacity Evolution, step 2: "landed as a (b′-1) declared default flip with the frozen
cache-key drop value left at False, so an explicit False still selects the pre-flip construction and
keeps its key"). Capx ledger §0ay.3(a) and register Q57.

THE RULING. Arm capacity_screen_peak_measured_hindcast so the capacity screens test the solve year's
OWN MEASURED LOAD — the identical array the LP dispatches — instead of the weather year's load
de-grown across the span. Land it as a DECLARED DEFAULT FLIP with the frozen cache-key drop value
left at the OLD default, so existing bundles keep their keys and the correct operand applies going
forward, with frontier bundles re-solved on their natural cadence rather than a repository-wide sweep.

*** THE ROUTE IS PART OF THE RULING. *** The owner ruled the D50 (b′-1) route specifically, not
"arm somehow". So:
 - VERIFY ZERO KEY MOVES BEFORE YOU COMMIT THE FLIP. Measure it, do not assert it: enumerate every
   committed run config, compute the key under the pre-flip and post-flip constructions, and show the
   count that moves. Use scripts/check_cache_key_registration.py and
   scripts/solve_surface_register.py --diff origin/main HEAD as D75-R-ARM and the facade fix did.
 - IF IT DOES NOT LAND AT ZERO KEY MOVES, STOP AND RETURN TO THE OWNER. Do not work around it, do not
   widen to a full re-solve on your own authority, do not arm without the flip. A route that does not
   hold voids the authority rather than being reinterpreted. Report exactly which configs move and why.

WHAT THE MECHANISM IS, so you can check you have the right seam: ONE gate, ONE seam, ZERO scalar
fields, ZERO free parameters (rules 21/24). The seam and its full consumer enumeration are
FINDING-capx-d76 §4.1 and §4.2 (the rule-19 enumeration). It is INERT BY CONSTRUCTION in every
forecast year, every crossover forward year and every backcast — a forecast year has no measured load,
so the growth path remains THE forecast methodology and rule 13's forward test is met by construction.
ASSERT that inertness by test, do not just state it.

PRE-REGISTER, BEFORE ANY VALUE IS OPENED: the flip's expected key-move count (zero), the expected
inert set (all forecast/crossover-forward/backcast rows), and the two ISOs where decisions are
expected to move — CAISO (−2,532.391 MW of backstop gas CT it does not need) and MISO (343.312 MW of
coal saved from a 2024 exit, outside the scored window). Four ISOs are expected to show NO decision
change: PJM (D67 makes the requirement peak-independent), NYISO (D52 likewise), ERCOT (energy-only,
nothing reads the position), NEISO (fleet long by 5.0–7.6 GW).

DO NOT ARM ONLY WHERE IT BITES. The owner was offered "arm only in CAISO and MISO" and it was marked
NOT RECOMMENDED: arming a mechanism only where it changes the answer is the fitted-mechanism selection
rule 1 [R-STRUCT] exists to forbid. The gate arms everywhere or not at all.

DO NOT ARGUE THE ARM FROM THE RESIDUAL. The basis is rule 14 [R-ACCURATE]: the de-grown estimate is
wrong by −23.3 % to +15.4 % against the identical array the LP dispatches, and rule 14's only
exception (data misaligned to our representation) does not apply because it is the SAME array. The
fact that decisions move in only 2 of 6 ISOs is not a point for or against and must not be written as
one — the four inert ISOs are evidence the gate is well-behaved.

MATRIX (rule 28): the mechanism's row plus a cell line in EVERY ISO shard (duty c — the one
deliberately non-parallel edit), since this changes a solve-affecting default for all six.

STOP GATES. (1) Non-zero key moves — STOP, return to the owner (above). (2) Any forecast, crossover
forward or backcast row proving NOT inert — STOP; the construction is wrong. (3) Any determination
flipping anywhere — STOP and report; the card's basis was "no determination flips anywhere". (4) A
consumer of the seam that FINDING-capx-d76 §4.2 does not enumerate — STOP and route; rule 19 requires
the enumeration to be complete before the seam moves.

EXIT: the gate armed as a (b′-1) declared default flip with the frozen drop value at the old default;
zero key moves MEASURED and shown; inertness asserted by test for forecast/crossover-forward/backcast;
the matrix row + six shard cells; CLAUDE.md's Capacity Evolution section given its bullet in the same
PR; rule-27 blob verification for any file >=300 lines. Report the key-move count, the inert set, and
which ISOs' frontier bundles now owe a re-solve on their natural cadence.
```

## D65-B-R COMPLETION-2 — leg 7 and the finding's §0/§6 (r#54; RE-EMITTED WHOLE, never dispatched at r#53)

```
You are the D65-B-R COMPLETION-2 session of the capacity-expansion track. The batch (owner ruling
Q47) has SIX legs registered on main and its board write merged as #5283. You are finishing it.
MODEL: Opus. DATA PROFILE: all. BRANCH: claude/capx-d65br-completion2 — FRESH off origin/main.

BINDING: pack §D65-B-R (the original) + this section + docs/handoffs/FINDING-capx-d65br-2026-09-06.md
+ PRECOMMIT-capx-d65b-2026-09-06.md Addendum C (the pre-declared per-ISO gates) and Addendum G (the
fourth rebase re-audit) + FINDING-capx-d64-2026-09-05.md §2.3/§2.4. Capx ledger §0ax and §0ay.

ALREADY DONE — DO NOT REDO, RE-GRADE, RE-SOLVE OR RE-REGISTER ANY OF IT. Legs 1-6 are solved,
graded and REGISTERED: ercot 9b9e5a48e3ca5c8e, neiso c3519b861f920bbe, nyiso f62431376dd9df03,
caiso 17770cdad3230938, pjm 542eeedadab83ee1, miso 74359fedbf2eadd6 — every key equal to the
Addendum C pre-declaration to the digit (PJM on Addendum E's re-declaration). Their sidecars are on
main under frontend/data/hindcast/. Step 0 and steps 1-2 are on main. The ERCOT screen is NOT re-run.

STEP A — LEG 7, your only solve: neiso-t3 GOLDEN-3 (~33 min), sequential, scored, verdict, registered
in place with its -pre-d65b prior through the SINGLE scripts/register_forecast_run.py path, graded
against Addendum C's G0'-G6' exactly as legs 1-6 were. D64 §2.3 POSITIVELY INDICATES this leg — an
expectation to test, never a target to hit; report the measurement whichever way it falls. HEAD GUARD:
H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90. Rebase BETWEEN legs
only, never during one; re-audit any rebase delta hunk by hunk with constants.py read first.

STEP B — ANSWER A QUESTION THE DIRECTOR GOT WRONG, and treat it as open. At r#52 I asserted the batch
had "written no board byte" and proved it by citing frontend/data/forecast/ff-verdicts.json. That was
the WRONG INSTRUMENT: the registration artifact is the per-run hindcast sidecar under
frontend/data/hindcast/ (7 files in c36a3fe7, zero under frontend/data/forecast/), while
ff-verdicts.json is the FF-2D VERDICT SNAPSHOT, a different object that moves only when a verdict
moves. So the genuinely open question, which I am NOT asserting either way: DO any of the seven legs
require an ff-verdicts.json update? Determine it from the code path (register_forecast_run.py, what
writes ff-verdicts.json, and what --reindex consumes) and from rule 15's list of committed inputs.
Report the answer with its evidence. If yes, make the update and say which verdicts moved and why. If
no, say so and say what WOULD have moved it. Either answer is a good outcome; an unexamined one is not.

STEP C — FINDING §0 AND §6, plus the ordering repair. Fill §0 "The verdicts" (still the placeholder
"*(filled at the close of the batch)*") with the per-ISO Addendum C grade and the batch verdict. Fill
§6 Governance and MOVE it: §6 currently sits at line ~142 BETWEEN §5.1 and §5.2, so §5.2-§5.6 read as
if they were inside governance. Put §6 after your new §5.7. Governance carries the rule-27 blob
checks, the D8 curated DOF rows for the flipped default, the D77 §8 blast-radius reconciliation, the
D50 §6.2 radius, and an explicit statement that the D72-prehunk neiso-t1f residue key is DISCHARGED.

STEP C-2 — THE BASIS DISCLOSURE, and it is the director's defect, not yours. Your leg 6 established
the general form: "All three fired gates share one root: Addendum C compares a HEAD solve against a
prior that predates HEAD, and two of the three are measuring that gap, not the arm." That is true and
§0 must say so in those terms. Concretely: G5' fired on neiso-t1f and nyiso-t1f (VOIDED as a STOP by
director adjudication r#51 §0av.3(b) and reclassified to REPORTED — those legs registered), and G4'
fired on miso-t1f and is provably not the acts' (I3 fails from 2026; apply_ccs_retrofit returns at
year < ccs_retrofit_available_year before reading either field; G0' measured 0 rows in 2026 and 2027).
Record all three as ONE root with its arithmetic. BASIS DISCLOSURE, not a re-grade: no leg's numbers
change, no gate is retro-declared passed, no prior is re-solved, every fired gate stays reported at
full magnitude. Grade leg 7's gates the same way if one fires on the same vintage gap.

STEP D — MATRIX (rule 28): the ccs_retrofit_screen row's def/note carries Act B; the
ccs_retrofit_fixed_cost_co2_scaling row's cells read fc: K where the arm is now the bare leg. Six
shards, ONE line each, last commit. Edit only cells your own evidence covers.

STOP GATES. (1) Leg 7 exceeding the D60 wall/RSS envelope (G6') — stop and report, do not retry blind.
(2) HEAD guard trip (exit 90) — rebase, re-audit, re-solve. (3) A board row you cannot reconcile to a
committed leg artifact — stop, do not hand-author it. (4) A gate you cannot grade from a committed
document — stop and route to the director rather than inventing a band.

DO NOT: re-solve legs 1-6 or the ERCOT screen; arm anything; touch the backcast registry, another
desk's ledger, or any ISO shard your evidence does not cover; widen to D82/D83/D84.

COLLISIONS: you are NEISO and you collide with nobody. Three PJM lanes are or may be live (D78-ARM
COMPLETION, D75-R-ARM steps 3-4, D76-ARM); stay out of PJM's shard and PJM's sidecars. Rules 12, 15,
22 (forecast mode only), 24, 25, 27, 28, 29.

EXIT: leg 7 solved, scored, registered with its prior; the ff-verdicts question answered with
evidence; FINDING §0 and §6 filled with §6 correctly ordered and the basis disclosure in §0; six
matrix shards stamped; rule-27 blob verification for any file >=300 lines pushed. Nothing else arms.
Report the batch verdict and the seven-row board table.
```

## D75-R-ARM STEPS 3–4 — the held re-solve and board registration (r#54; RE-EMITTED WHOLE, never dispatched at r#53, with the key question now live)

```
You are the D75-R-ARM STEPS 3-4 session of the capacity-expansion track. Steps 1-2 LANDED
(#5267/#5272, 6164231e): pjm_vre_accreditation_vintage is ARMED for PJM under owner ruling Q55. Steps
3-4 were held behind D65-B-R's board write; THAT MERGED (#5283, c36a3fe7) and the STOP IS MET. This
charter was issued at r#53 and never dispatched; it is re-emitted whole with ONE change, marked below.
MODEL: Opus. DATA PROFILE: pjm. BRANCH: claude/capx-d75r-arm-steps34 — FRESH off origin/main.

BINDING: PRECOMMIT-capx-d75r-arm-2026-09-06.md + FINDING-capx-d75r-2026-09-06.md + the D67-ARM
precedent (FINDING-capx-d67arm-2026-09-06.md, whose §2.1 recorded the moving-control-legs miss
against itself). Capx ledger §0ax.1 and §0ay.

WHAT IS ALREADY TRUE, MEASURED, DO NOT RE-ARGUE IT. The arm is an ISO override in
_pjm_config.default_scenario_overrides, not a shared default flip. Of 153 committed run configs the
21 PJM FORECAST configs move and all 132 others are byte-identical. Bare pjm-t1h goes
a9c66d8ea25acb9d -> b518f5fe7d02f961; --no-pjm-vre-accreditation-vintage reaches the pre-arm control
and keeps a9c66d8ea25acb9d.

*** [r#54 CHANGE] THE KEY QUESTION IS NOW LIVE AND YOU MUST ANSWER IT FIRST. *** Since this charter
was written, D78-ARM armed retirement_sector_gate for PJM on branch
claude/pjm-retirement-sector-gate-at0cao (UNMERGED at r#54) and moved the bare pjm-t1h key AGAIN:
b518f5fe7d02f961 -> fb16fda2ddb0a94a. There are now THREE vintages of that key in play. Before you
solve anything: read origin/main AND that branch, determine which key the bare recipe carries at YOUR
head, and DECLARE it in an addendum pushed before the solve. If D78-ARM has merged before you start,
your row carries fb16fda2ddb0a94a and this lane's job is to register the VRE-devintage row against the
correct prior — say so explicitly rather than silently registering a different key than the charter
names. If it has not merged, you carry b518f5fe7d02f961 as originally chartered. Either way: NAME THE
KEY IN THE ROW. Do not assume.

STEP 3 — RE-SOLVE the bare pjm-t1h at the key you declared, preserving its prior as -pre-d75rarm.
DECLARE the expected key BEFORE the solve, in the addendum above, and report realized-vs-declared.
HEAD GUARD mandatory: H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit
90. If the realized key is not the declared one, STOP and report — a mismatch means the arm does not
reproduce the recipe the A/B was measured on, and the Q55 basis needs re-reading.

STEP 4 — REGISTER through the SINGLE scripts/register_forecast_run.py path (rule 15). Score the row,
report every invariant at full magnitude, and DECLARE any FAIL against the leg's own committed prior
in the same commit (the Y-24 ratchet). A declaration is not a fix: nothing is relaxed, re-scored or
exempted.

NOTE ON THE COMMITTED ARTIFACT SET, because the director got this wrong at r#52 and corrected it at
r#53: register_forecast_run.py writes the per-run hindcast sidecar; ff-verdicts.json is the FF-2D
verdict snapshot and moves only when a verdict moves. Determine from the code path which of the two
your registration must touch, and say which and why in your close.

NOTE ON D76-P3B: it solved the bare pjm-t1h at b518f5fe7d02f961 as its own control and then DELETED
that bundle before merge under rule 29(c). That solve does NOT discharge your registration; do not
cite it as though the row already exists.

THE FOUR D57/D67 CONTROL LEGS MOVE, and that was PRE-DECLARED in PRECOMMIT §2.1 rather than
discovered afterwards — the exact miss FINDING-capx-d67arm §2.1 recorded against itself. Handle them
as that precedent did: name each, say why it moved, and do not treat the movement as a defect.

DO NOT: arm anything further; touch retirement_sector_gate (D78-ARM COMPLETION owns it); re-open
D75-R's A/B; touch another ISO's shard (rule 25 — PJM only, locked by test across the other five).

COLLISIONS: D78-ARM COMPLETION is the other PJM registration lane and carries the same
name-your-key duty. Whichever of you lands first states its key; the second rebases and re-declares
rather than assuming. Rules 12, 15, 24, 25, 27, 28, 29.

EXIT: the key question answered and declared before the solve; bare pjm-t1h re-solved at the declared
key with the HEAD guard held; registered with its prior preserved; every invariant reported and every
FAIL declared against its own prior; the PJM matrix shard stamped; rule-27 blob verification for any
file >=300 lines. Report the key realized-vs-declared and the before/after row.
```

## r#55 NOTE (2026-09-07): ALL FIVE r#54 charters landed. TWO charters below, both DISPATCHABLE NOW. Also owed and not a charter: **MERGE `cf6ddf51`** on `claude/pjm-retirement-sector-gate-at0cao-lsffr8` — D78-ARM solved, scored and REGISTERED the armed `pjm-t1h` at `fb16fda2ddb0a94a`, discharging Q56's registration condition; it is one commit sitting on a branch.

## STATUS REBUILD — the `audit_keepers` S1 red on ERCOT and MISO (r#55)

```
You are a one-act status-rebuild session for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. BRANCH: claude/status-rebuild-ercot-miso — FRESH off origin/main.

THE DEFECT. scripts/audit_keepers.py --check is RED on main:
  ✗ S1: stale vs the current verdicts: frontend/data/backcast/status/ERCOT.js,
        frontend/data/backcast/status/MISO.js — re-run: python scripts/build_status.py
Both ISOs' keepers moved recently (MISO -> 2026-09-07-miso-233-spp-hourly; ERCOT's verdicts
re-scored) and the generated status parts were not rebuilt.

YOUR ONLY JOB is to regenerate those two status parts and commit them. Do not edit any keeper shard,
any registry sidecar, calibration-complete.json, program-status.json, or any scorer. Nothing is
solved, scored or registered. You are running a generator, not authoring a verdict.

METHOD.
 1. Reproduce the red first and paste the exact failure text.
 2. Run the per-ISO rebuild, one ISO at a time, as the keepers README requires (a lane edits only the
    ISO it is rebuilding): python3 scripts/build_status.py --iso ERCOT ; then --iso MISO.
 3. Re-run python3 scripts/audit_keepers.py --check and confirm it exits 0.
 4. `git diff --stat` must touch ONLY frontend/data/backcast/status/ERCOT.js and .../MISO.js. If it
    touches anything else, STOP and report what and why — a status rebuild that moves a third file is
    not a status rebuild.

READ THE DIFF BEFORE YOU COMMIT, and say in your close what actually changed in each file — which
keeper id, which determination, which per-year rows. If a determination TEXT changes for either ISO,
say so explicitly and quote both sides: a generated file is still a published artifact, and a silent
determination change is exactly what the S1 check exists to surface. If either ISO's rebuilt
determination is WORSE than what the file previously carried, STOP and report rather than committing —
that is a rule-22 D-5(b) escalation, not a housekeeping commit.

EXIT: audit_keepers --check exits 0; the diff touches exactly two files; the per-ISO changes are
described in the close; commit and push. Do not open a PR unless asked.
```

## D76-ARM-B — arm `capacity_screen_peak_measured_hindcast`, variant B, under owner ruling Q58 (r#55)

```
You are the D76-ARM-B session, executing OWNER RULING Q58 (capx ledger §0az.3(a), r#55).
MODEL: Opus. DATA PROFILE: code, widening to all only if a verification solve is needed.
BRANCH: claude/capx-d76-arm-variant-b — FRESH off origin/main.

WHY THIS CHARTER EXISTS. Q57 authorized this arm "via the D50 (b′-1) route" under a STOP requiring
ZERO KEY MOVES. The D76-ARM lane verified that route and it FAILS STRUCTURALLY: since Q20/(b′-1),
cache_key() drops a registered field IFF it equals its FROZEN declaration, so a config resolving the
new default necessarily enters the hash — which is the mechanism that stops a post-flip armed run
being served the pre-flip bundle. "Arm the gate" and "move no key" are the same sentence with opposite
signs. The lane measured both variants, took neither, and returned the card. READ
docs/handoffs/FINDING-capx-d76-arm-2026-09-07.md IN FULL before you touch anything — it is your
pre-registration and its numbers are the ones you must reproduce.

THE DESK'S ERROR, so you do not inherit it. My Q57 card demanded a criterion NO arm in this family has
ever met. D75-R-ARM reported "21 of 153 configs move, ALL PJM FORECAST, 132 byte-identical"; D78-ARM
reported "zero non-PJM moves, zero backcast moves … PJM forecast moves and is listed, because a moved
key is the intended effect and must be inspectable." THE HOUSE STANDARD IS ZERO OFF-TARGET MOVES WITH
IN-SCOPE MOVES LISTED. Report yourself in exactly that form.

THE RULING. Arm capacity_screen_peak_measured_hindcast as VARIANT B: the declared default flip PLUS
the non-hindcast coercion the five sibling gates already ship. THE __post_init__ COERCION IS EXPLICITLY
AUTHORIZED BY THIS RULING — it is the one thing D76-ARM correctly refused to land on its own, because a
construction change is not something a lane may add under a ruling whose route it must not reinterpret.
You have that authority now; you do not have authority to invent a third variant.

PRE-DECLARE, BEFORE YOU COMPUTE A SINGLE KEY, and reproduce D76-ARM's census to the config:
  * expected: 34 moved, 0 OFF TARGET — PJM 10, MISO 9, NEISO 6, NYISO 5, ERCOT 3, CAISO 1
  * expected: 0 backcast moves, 0 non-hindcast forecast moves
  * the moved set is exactly the hindcast configs the gate governs, enumerated by id
If your census does not reproduce those counts, STOP AND REPORT before editing src/market_sim/ — a
divergence means main moved under the measurement and the card's basis needs re-reading, not a patch.

ASSERT THE INERT SET BY TEST, do not state it: the gate is inert by construction in every forecast
year, every crossover forward year and every backcast, because a forecast year has no measured load
and the growth path remains THE forecast methodology (rule 13's forward test, met by construction).
D76-ARM re-verified this at its HEAD; re-verify at yours and ship the test.

DO NOT ARGUE THE ARM FROM THE RESIDUAL. The basis is rule 14 [R-ACCURATE]: the de-grown estimate is
wrong by −23.3 % to +15.4 % against the IDENTICAL array the LP dispatches, and rule 14's only
exception (data misaligned to our representation) does not apply because it is the same array. That
decisions move in only 2 of 6 ISOs (CAISO −2,532.391 MW of backstop gas CT; MISO 343.312 MW of coal
saved from a 2024 exit, outside the scored window) is NOT a point for or against and must not be
written as one — the four inert ISOs are evidence the gate is well-behaved. Do not arm only where it
bites; that was offered to the owner and refused as fitted-mechanism selection (rule 1 [R-STRUCT]).

MATRIX (rule 28): the mechanism's row plus a cell line in EVERY ISO shard (duty c — the one
deliberately non-parallel edit), since this changes a solve-affecting default for all six. CLAUDE.md's
Capacity Evolution section gets its bullet in the same PR.

STOP GATES. (1) A census that does not reproduce 34/0 — STOP and report. (2) Any off-target move at
all, backcast or non-hindcast forecast — STOP; variant B is defined by having none. (3) Any forecast,
crossover-forward or backcast row proving NOT inert — STOP; the construction is wrong. (4) Any
determination flipping anywhere — STOP and report; the card's basis was "no determination flips
anywhere". (5) A consumer of the seam that FINDING-capx-d76 §4.2 does not enumerate — STOP and route;
rule 19 requires the enumeration complete before the seam moves.

ROUTED, NOT YOURS: 15 committed run configs carry a cache_key the current rules cannot reproduce
(registration lag; 6 explained by caiso_offer_surface_measured_ungrounded registered after those
bundles solved). D76-ARM established this does NOT touch the census — a row's move verdict is
hash-independent — so it is not a dependency. It is RESERVED as D85. Do not audit it here; if your
census trips over one of the 15, name it and move on.

EXIT: the gate armed as variant B with the coercion; the census reported as "N moved, 0 off target,
in-scope listed" with the per-ISO breakdown; inertness asserted by test; the matrix row + six shard
cells; the CLAUDE.md bullet; rule-27 blob verification for any file ≥300 lines. Report which ISOs'
frontier bundles now owe a re-solve on their natural cadence, and state plainly that Q58 is discharged.
```

## r#56 NOTE (2026-09-07): both r#55 charters were never dispatched and are RE-EMITTED WHOLE below. The STATUS REBUILD charter is CHANGED in one way — it no longer names ISOs, because the S1 gate's target migrates between sittings (ERCOT+MISO at r#55, ERCOT+PJM now). D76-ARM-B is unchanged except for one added check: SPP now holds a keeper (`2026-09-07-spp-1-baseline`), so the mechanism matrix may carry a seventh column.

## STATUS REBUILD — the `audit_keepers` S1 red, whatever it names at YOUR head (r#56, re-emitted)

```
You are a one-act status-rebuild session for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. BRANCH: claude/status-rebuild-s1 — FRESH off origin/main.

THE DEFECT. scripts/audit_keepers.py --check is RED on main with an S1 failure: one or more
frontend/data/backcast/status/<ISO>.js parts are stale vs the current verdicts.

*** DO NOT TRUST ANY ISO LIST, INCLUDING ONE IN THIS CHARTER. *** S1 re-computes against whatever the
current verdicts are, so the ISOs it names MIGRATE between sittings as owner lanes promote and fold —
it read ERCOT + MISO on 2026-09-07 morning and ERCOT + PJM the same afternoon. Your first act is to
RUN THE GATE AND READ WHICH ISOs IT NAMES AT YOUR HEAD, and those are the ISOs you rebuild. If it
exits 0, say so and stop — a stale charter is not a reason to rebuild anything.

YOUR ONLY JOB is to regenerate the status parts S1 names and commit them. Do not edit any keeper
shard, any registry sidecar, calibration-complete.json, program-status.json, or any scorer. Nothing is
solved, scored or registered. You are running a generator, not authoring a verdict.

METHOD.
 1. Run python3 scripts/audit_keepers.py --check, paste the exact failure text, and list the ISOs.
 2. Rebuild ONE ISO AT A TIME, as the keepers README requires:
    python3 scripts/build_status.py --iso <ISO>   for each ISO the gate named, in turn.
 3. Re-run audit_keepers.py --check and confirm exit 0.
 4. `git diff --stat` must touch ONLY the frontend/data/backcast/status/<ISO>.js files for the ISOs
    the gate named. If it touches anything else — a third ISO, a sidecar, a keeper shard — STOP and
    report what and why. A status rebuild that moves a file the gate did not name is not a status
    rebuild.

READ THE DIFF BEFORE YOU COMMIT and say in your close, per ISO, what actually changed: which keeper
id, which determination, which per-year rows. If a determination TEXT changes for any ISO, quote both
sides — a generated file is still a published artifact, and a silent determination change is exactly
what S1 exists to surface. IF ANY ISO'S REBUILT DETERMINATION IS WORSE than what the file previously
carried, STOP AND REPORT rather than committing: that is a rule-22 D-5(b) escalation to the owner, not
a housekeeping commit.

NOTE FOR CONTEXT, not a target: ERCOT has been stale across two consecutive director sittings while
MISO cleared itself and PJM newly went stale. If ERCOT is still named at your head, look at WHY its
part keeps going stale and say what you find — a part that never clears is a different defect from a
part that goes stale after a promotion, and nobody has looked.

EXIT: audit_keepers --check exits 0; the diff touches only the named ISOs' status parts; the per-ISO
changes described in the close; commit and push. Do not open a PR unless asked.
```

## D76-ARM-B — arm `capacity_screen_peak_measured_hindcast`, variant B, under owner ruling Q58 (r#56, re-emitted)

```
You are the D76-ARM-B session, executing OWNER RULING Q58 (capx ledger §0az.3(a), r#55).
MODEL: Opus. DATA PROFILE: code, widening to all only if a verification solve is needed.
BRANCH: claude/capx-d76-arm-variant-b — FRESH off origin/main.

WHY THIS CHARTER EXISTS. Q57 authorized this arm "via the D50 (b′-1) route" under a STOP requiring
ZERO KEY MOVES. The D76-ARM lane verified that route and it FAILS STRUCTURALLY: since Q20/(b′-1),
cache_key() drops a registered field IFF it equals its FROZEN declaration, so a config resolving the
new default necessarily enters the hash — which is the mechanism that stops a post-flip armed run
being served the pre-flip bundle. "Arm the gate" and "move no key" are the same sentence with opposite
signs. The lane measured both variants, took neither, and returned the card. READ
docs/handoffs/FINDING-capx-d76-arm-2026-09-07.md IN FULL before you touch anything — it is your
pre-registration and its numbers are the ones you must reproduce.

THE DESK'S ERROR, so you do not inherit it. My Q57 card demanded a criterion NO arm in this family has
ever met. D75-R-ARM reported "21 of 153 configs move, ALL PJM FORECAST, 132 byte-identical"; D78-ARM
reported "zero non-PJM moves, zero backcast moves … PJM forecast moves and is listed, because a moved
key is the intended effect and must be inspectable." THE HOUSE STANDARD IS ZERO OFF-TARGET MOVES WITH
IN-SCOPE MOVES LISTED. Report yourself in exactly that form.

THE RULING. Arm capacity_screen_peak_measured_hindcast as VARIANT B: the declared default flip PLUS
the non-hindcast coercion the five sibling gates already ship. THE __post_init__ COERCION IS EXPLICITLY
AUTHORIZED BY THIS RULING — it is the one thing D76-ARM correctly refused to land on its own, because a
construction change is not something a lane may add under a ruling whose route it must not reinterpret.
You have that authority now; you do not have authority to invent a third variant.

PRE-DECLARE, BEFORE YOU COMPUTE A SINGLE KEY, and reproduce D76-ARM's census to the config:
  * expected: 34 moved, 0 OFF TARGET — PJM 10, MISO 9, NEISO 6, NYISO 5, ERCOT 3, CAISO 1
  * expected: 0 backcast moves, 0 non-hindcast forecast moves
  * the moved set is exactly the hindcast configs the gate governs, enumerated by id
D76-ARM measured over 173 committed run_config.json. THE CORPUS HAS GROWN SINCE (SPP landed its first
keeper, and other lanes have registered), so your denominator will differ and MAY your counts. If the
per-ISO breakdown or the off-target count differs from the above, do NOT patch toward it: report the
divergence, say which configs are new since 2026-09-07, and confirm the OFF-TARGET count is still
ZERO. Zero off-target is the ruling's criterion; 34 is a measurement, not the gate.

ASSERT THE INERT SET BY TEST, do not state it: the gate is inert by construction in every forecast
year, every crossover forward year and every backcast, because a forecast year has no measured load
and the growth path remains THE forecast methodology (rule 13's forward test, met by construction).
D76-ARM re-verified this at its HEAD; re-verify at yours and ship the test.

DO NOT ARGUE THE ARM FROM THE RESIDUAL. The basis is rule 14 [R-ACCURATE]: the de-grown estimate is
wrong by −23.3 % to +15.4 % against the IDENTICAL array the LP dispatches, and rule 14's only
exception (data misaligned to our representation) does not apply because it is the same array. That
decisions move in only 2 of 6 ISOs (CAISO −2,532.391 MW of backstop gas CT; MISO 343.312 MW of coal
saved from a 2024 exit, outside the scored window) is NOT a point for or against and must not be
written as one — the four inert ISOs are evidence the gate is well-behaved. Do not arm only where it
bites; that was offered to the owner and refused as fitted-mechanism selection (rule 1 [R-STRUCT]).

MATRIX (rule 28): the mechanism's row plus a cell line in EVERY ISO shard (duty c — the one
deliberately non-parallel edit), since this changes a solve-affecting default. *** SPP NOW HOLDS A
KEEPER (2026-09-07-spp-1-baseline), so the matrix may carry a SEVENTH column. Check
docs/codebase-site/data/mechanism-matrix/ for an SPP.js shard before you write duty (c)'s cells, and
if it exists give SPP a cell too — as U (untested), never a transferred verdict (rule 25
[R-ISO-SCOPE]). *** CLAUDE.md's Capacity Evolution section gets its bullet in the same PR.

STOP GATES. (1) Any OFF-TARGET move at all, backcast or non-hindcast forecast — STOP; variant B is
defined by having none. (2) Any forecast, crossover-forward or backcast row proving NOT inert — STOP;
the construction is wrong. (3) Any determination flipping anywhere — STOP and report; the card's basis
was "no determination flips anywhere". (4) A consumer of the seam that FINDING-capx-d76 §4.2 does not
enumerate — STOP and route; rule 19 requires the enumeration complete before the seam moves.

ROUTED, NOT YOURS: 15 committed run configs carry a cache_key the current rules cannot reproduce
(registration lag; 6 explained by caiso_offer_surface_measured_ungrounded registered after those
bundles solved). D76-ARM established this does NOT touch the census — a row's move verdict is
hash-independent — so it is not a dependency. It is RESERVED as D85. Do not audit it here; if your
census trips over one of the 15, name it and move on.

EXIT: the gate armed as variant B with the coercion; the census reported as "N moved, 0 off target,
in-scope listed" with the per-ISO breakdown and your denominator stated; inertness asserted by test;
the matrix row + one cell per shard that exists; the CLAUDE.md bullet; rule-27 blob verification for
any file ≥300 lines. Report which ISOs' frontier bundles now owe a re-solve on their natural cadence,
and state plainly that Q58 is discharged.
```

## r#57 NOTE (2026-09-07): both r#56 charters landed and **Q58 is DISCHARGED** — the measured hindcast screen peak is armed for every ISO at 34 in-scope key moves and zero off-target. The chartered queue was EMPTY for the first time; **owner ruling Q59 sets three lanes, all DISPATCHABLE NOW and all on disjoint surfaces**. D82 is a DESIGN READ and may not recommend an arm. SPP onboarding is the BOARD half only — the T1-H recipe is the SPP desk's.

## D82 DESIGN READ — the PJM CT plateau and the per-delivery-year zero-E&AS operand (r#57, owner ruling Q59)

```
You are the D82 DESIGN READ session of the capacity-expansion track, executing OWNER RULING Q59
(capx ledger §0bb.3(a), r#57). MODEL: Fable. DATA PROFILE: pjm. BRANCH: claude/capx-d82-ct-plateau-design
— FRESH off origin/main.

*** THIS IS A READ. YOU DO NOT RECOMMEND AN ARM, AND YOU DO NOT SOLVE. *** Your deliverable is a
design document. A design read that arrives carrying a recommendation has skipped the screen rule 29
[R-SCREEN] requires, and the desk will void it exactly as it voided Q57's route. If the read makes an
arm look obvious, say what the SCREEN would have to measure to establish it — that is the useful
output, not the conclusion.

THE OBJECT, and why it is now readable. D74 measured a 24.2 GW PJM CT plateau offering at the
published bar on ZERO E&AS margin. D57 §4 named the CT / ST / oil E&AS operand as the reason the
model's clearing price runs 1.5-5.7x the published, and D57's own record says that operand is zero in
the hindcast prices and was NEVER haircut. D78's finding states, at its gate, that `false_retire`
stays FAIL and that this operand is THE NAMED SUCCESSOR for the retirement bands. D78-R3 then
established the per-delivery-year zero-E&AS set from D57 §4's own published rows -- {gas_ct, gas_st,
oil} for DY2022/23, {gas_ct, gas_st} for 2023/24, {oil} for 2024/25, DY2025/26 NOT EVALUABLE. That set
is the input D82 was reserved waiting for and it now exists.

READ THESE FIRST, and cite them by section: FINDING-capx-d74 (the plateau measurement and its
admission-cap re-fill), FINDING-capx-d57 §3.1 / §4 (the offer construction and the per-DY at-bar
rows), FINDING-capx-d78r3 §3 (the derived set, its ONE-SIDEDNESS, and its proven false-positive class
-- nuclear derives at bar in all four DYs and belongs at none, being a $0 price taker), and
FINDING-capx-d78 / -d78arm (what the sector gate did and did not close).

THE QUESTIONS THE READ MUST ANSWER, each with evidence from committed artifacts:
 1. WHAT IS THE PLATEAU, mechanically? Is a CT at the published bar there because its E&AS margin is
    genuinely zero in these years, because the hindcast price series cannot express its scarcity
    revenue, or because the offer construction floors it? Distinguish these -- they have different
    repairs and only one of them is a model defect.
 2. IS THE ZERO E&AS OPERAND A DATA GAP OR A CONSTRUCTION GAP? D57 says it is zero in the hindcast
    prices. Establish WHY from the code path and the committed price series, not by inference.
 3. WHAT WOULD A NON-ZERO OPERAND BE DERIVED FROM, and would it be admissible under rule 13
    [R-MEASURED]'s forward test -- could the same quantity be produced for a forward year from
    forward drivers, and would it respond to changed conditions? If the honest answer is that the
    only available construction is a backcast-only overlay, SAY SO; that is a finding, and it closes
    the object rather than opening a lane.
 4. WHAT IS THE BLAST RADIUS? Which consumers read the E&AS margin (rule 19 [R-ONE-MECH] enumeration,
    complete before anything moves), and what else would move if it stopped being zero -- the clearing
    price, the failing set, `false_retire`, the retirement bands, the entry screen.
 5. IS THERE A ZERO-LP PHASE 0? Rule 29(0) says an arm with a computable pre-solve gate does not
    reach a solve until that gate passes. Name the phase-0 instrument a successor lane would build,
    or say that none exists and why.

STATE WHAT YOU CANNOT ANSWER. A design read whose §6 is empty is either a perfect object or an
incurious read, and the second is far more likely. D78-R3's own derivation is one-sided and carries a
proven false-positive class; assume yours has one too and go looking for it.

DO NOT: solve anything; arm anything; edit src/market_sim/; propose a ScenarioConfig field; write a
matrix cell (nothing is tested here); recommend. DO: write
docs/handoffs/DESIGN-capx-d82-ct-plateau-<date>.md, cite every claim to a committed artifact, and
close with the SCREEN SPECIFICATION a successor lane would pre-register -- the phase-0 gate, the
screen year chosen on FOOTPRINT (never residual), and the STOP conditions.

EXIT: the design doc committed and pushed; every one of questions 1-5 answered or explicitly declared
unanswerable with its reason; a §6 of open questions that is not empty; no recommendation, no arm, no
solve. Report the answer to question 3 first in your close -- it is the one that decides whether D82
is a lane at all.
```

## SPP FORECAST BOARD ROW — put the seventh ISO on the §2.1b board (r#57, owner ruling Q59)

```
You are the SPP FORECAST BOARD ROW session of the capacity-expansion track, executing OWNER RULING
Q59 (capx ledger §0bb.3(a), r#57). MODEL: Opus. DATA PROFILE: spp.
BRANCH: claude/capx-spp-board-row — FRESH off origin/main.

THE GAP, measured at r#57. SPP is a registered ISO in config/iso_configs.py (2 zones), holds TWO
backcast keepers (2026-09-07-spp-1-baseline, then 2026-09-07-spp-2-crosswalk-hydro), and has a
mechanism-matrix shard that capx D76-ARM-B correctly filled. It has NO forecast presence whatever:
no hindcast sidecar under frontend/data/hindcast/, and NO row in
frontend/data/forecast/program-status.json, whose gate board carries exactly six ISOs. SPP is the only
ISO that is calibrated and forecast-invisible.

*** SCOPE SPLIT, and it is the ruling's own term. *** You own THE BOARD ROW. You do NOT own the T1-H
recipe, the SPP forecast data intake, or any solve to populate it — those are the SPP desk's and are
routed there. If you find the board row cannot be written without the recipe, STOP AND SAY SO rather
than building the recipe: that finding is the deliverable and it re-routes the whole item.

STEP 1 — ESTABLISH WHAT A BOARD ROW ACTUALLY REQUIRES, from the code, before writing anything. Read
scripts/register_forecast_run.py, whatever consumes program-status.json, and rule 15 [R-DASHBOARD]'s
list of COMMITTED inputs for the forecast namespace (the hindcast sidecars + ff-verdicts.json +
program-status.json; registry/ runs/ manifest.js program-status.js are GENERATED and gitignored).
Determine: can a §2.1b row exist for an ISO with no hindcast sidecar, in a state that honestly reads
"no forecast run yet"? Or does the board's schema require a verdict, making the row impossible until
the SPP desk lands a T1-H? ANSWER THIS FROM THE SCHEMA, not from what would be convenient.

STEP 2 — IF THE ROW CAN EXIST HONESTLY, write it: an SPP entry whose gate legs read their true state,
with (a) keyed to SPP's live keeper (2026-09-07-spp-2-crosswalk-hydro at r#57 — RE-READ IT LIVE, it
has moved twice in two days) and marker state (SPP is NOT in `complete`; check, do not assume), and
(b)/(c)/(d) reading whatever "no forecast run" is in that schema. Add the gate_a_provenance stamp the
same way every other ISO's row carries it. The row must never imply a forecast result SPP does not
have.

STEP 3 — IF THE ROW CANNOT EXIST until a T1-H lands, do not force one. Write the finding, name
exactly which schema field blocks it, and state what the SPP desk must land first. That is a complete
and successful session.

A SCOPE-LABEL NOTE YOU MUST CARRY, from director ruling §0bb.3(b): every "all six ISOs" claim on the
capx record — D76's "peak-inert in ALL SIX", D78's per-ISO census, every prior six-ISO count — is now
a claim about SIX OF SEVEN. Those findings are NOT wrong and are NOT retro-edited: they measured the
six ISOs that had forecast rows, and rewriting a scope label after the fact destroys the record. The
repair is FORWARD ONLY. If your row lands, say plainly in your close that findings from this point
count seven, and do not touch a single prior finding's text.

DO NOT: solve anything; touch another ISO's row, shard or sidecar; edit the backcast namespace;
build the SPP T1-H recipe; retro-edit any six-ISO claim. Rules 15, 25 (SPP's cells stay U — no verdict
transfers in), 27 (program-status.json is well over 300 lines: TARGETED STRING EDIT, never a
json.dumps round-trip, blob-verify after push), 28.

EXIT: either the SPP board row committed with every leg reading its true state and gate (a) still
exiting 0, or a finding naming exactly what blocks it. Either way: check_gate_a_provenance.py exits 0,
the diff touches only SPP's row and its provenance stamp, and your close states whether the capx
record now counts six or seven going forward.
```

## D85 — the fifteen committed configs whose cache_key the current rules cannot reproduce (r#57, owner ruling Q59)

```
You are the D85 KEY-PROVENANCE AUDIT session of the capacity-expansion track, executing OWNER RULING
Q59 (capx ledger §0bb.3(a), r#57). MODEL: Fable. DATA PROFILE: code.
BRANCH: claude/capx-d85-key-provenance — FRESH off origin/main.

THE OBJECT. FINDING-capx-d76-arm-2026-09-07.md §6 routed, and did not repair: 15 committed run
configs carry a `cache_key` that the CURRENT rules cannot reproduce — registration lag, of which 6 are
explained by `caiso_offer_surface_measured_ungrounded` being registered AFTER those bundles solved.
The lane established that this does NOT touch any census, because a row's move verdict is
hash-independent, so nothing is blocked on it. It is nonetheless a real defect in committed artifacts:
a key that cannot be recomputed is a provenance hole.

*** THIS IS AN AUDIT. YOU DIAGNOSE AND CLASSIFY; YOU DO NOT REWRITE COMMITTED KEYS. *** A committed
`cache_key` is what that bundle actually solved under. Rewriting one to match today's rules would
make the artifact lie about its own provenance, which is worse than the hole. If the right repair
turns out to be a key rewrite, that is an owner card, not your act.

STEP 1 — REPRODUCE THE 15. Re-run D76-ARM's census instrument (docs/handoffs/d76arm/, and its
key-census scripts) at YOUR head and confirm the count. The corpus has been growing ~10-20 configs a
day, so the number may differ; report what you measure and note that D76-ARM measured over 173
configs, D76-ARM-B over 190. If your count differs, say which configs are new.

STEP 2 — CLASSIFY EVERY ONE, with a named cause. Expected classes, but find your own:
  (a) REGISTRATION LAG — a field registered in _CACHE_KEY_OPTIONAL_FIELDS after the bundle solved, so
      today's cache_key() reads a field the solving code did not. The 6
      caiso_offer_surface_measured_ungrounded cases are stated to be this.
  (b) DECLARED-DEFAULT FLIP — the bundle solved before a flip that has since been declared, so its
      frozen-declaration comparison differs. Four flips now exist; D76-ARM-B added the fourth.
  (c) SOLVE-SURFACE FINGERPRINT — since D79/Q54 the key carries a per-name, per-ISO value hash; a
      bundle predating a registry re-derivation may not reproduce.
  (d) SOMETHING ELSE — and if you find one, it is the most valuable output of this session.
Every one of the 15 gets a class and a citation. An unclassified row is the finding, not a footnote.

STEP 3 — SAY WHAT, IF ANYTHING, IS AT RISK. For each class: can a stale-keyed bundle be served to a
run that should have re-solved? That is the failure mode Q20/(b'-1) exists to prevent, and it is the
only question that decides whether this is housekeeping or a defect. Answer it from the code path
(results/cache.py's is_cached config-equality refusal, which D24-R landed for exactly this), not by
assertion. If the answer is "no, the equality refusal catches it", say so plainly — that is a good
outcome and it downgrades the whole item.

STEP 4 — PROPOSE, DO NOT EXECUTE. Price the candidate repairs (leave as provenance-only; add a
recorded exception list; re-register the lagging fields; something you find) with what each costs and
what it invalidates. Recommend one. The owner decides.

DO NOT: rewrite any committed cache_key; delete or re-register any bundle; edit
_CACHE_KEY_OPTIONAL_FIELDS or the FLIPS list; solve anything; widen to D82/D83/D84.

EXIT: docs/handoffs/FINDING-capx-d85-key-provenance-<date>.md with the reproduced count, all rows
classified with zero unclassified, step 3's risk answer derived from the code path, and a priced
recommendation. Report the step-3 answer FIRST in your close — it decides whether this item is a
defect or bookkeeping.
```

## r#58 NOTE (2026-09-07): all three Q59 lanes landed. **D82 is CLOSED — the label is spent** (every operand of the measured size is a backcast-only overlay; `false_retire` stays FAIL with NO named successor in the E&AS direction). Two charters below, both zero-LP and disjoint. The SPP re-key is the SIXTEENTH Q34 firing and the FIRST on a row this desk itself chartered — SPP promoted a third time within hours of the row landing, after the lane followed the read-live instruction exactly.

## SPP gate-(a) RE-KEY — the Q34 standing duty on this desk's own row (r#58)

```
You are a one-act SPP gate-(a) re-key session for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. BRANCH: claude/spp-gate-a-rekey — FRESH off origin/main.

THE DEFECT. scripts/check_gate_a_provenance.py is RED on main:
  SPP: gate.a_keeper_marker cites SUPERSEDED keeper '2026-09-07-spp-2-crosswalk-hydro';
  the ISO's current designated keeper is '2026-09-07-spp-3-screened-input'.

*** DO NOT TRUST THAT KEEPER ID EITHER. *** SPP has promoted THREE times in about a day
(spp-1-baseline -> spp-2-crosswalk-hydro -> spp-3-screened-input). The row that is now stale was
written yesterday by a lane that was explicitly told to read the keeper live, and it did — SPP simply
moved again within hours. Your FIRST act is to run the gate and read BOTH ids it names at YOUR head,
and re-key to whatever `frontend/data/backcast/keepers/SPP.json` says at the moment you write. If the
gate exits 0, say so and stop.

CONTEXT YOU SHOULD CARRY, from director ruling §0bc.3(b): this is the SIXTEENTH firing of the Q34
duty and the FIRST that is not a promoter's miss. The obvious "fix" — making the row derive its
keeper id instead of hard-coding it — WOULD DEFEAT THE CHECK: gate (a) compares identity precisely so
a promotion cannot silently drift past the board, and a derived id would always agree with itself and
assert nothing. DO NOT propose or implement that. The re-key treadmill is the cost of the guarantee.

YOUR ONLY JOB is SPP's row. Do not touch any other ISO's row, any other gate leg, any keeper shard,
calibration-complete.json, or the backcast namespace. Nothing is solved, scored or registered.

METHOD — BINDING. Edit frontend/data/forecast/program-status.json by TARGETED STRING EDIT scoped by
string position. NEVER a json.dumps round-trip: the file's formatting is load-bearing and a
re-serialize rewrites the whole document — the rule 27 [R-PUSH] hazard, and file-integrity-guard
would NOT catch it because a reformat is not a >30 % shrink. Assert each old string occurs exactly
once BEFORE replacing and json.load() parses AFTER. Watch for a leading space where prior text
continues. Push the exact on-disk bytes and blob-verify after the push.

THE THREE LEAVES, all inside the SPP block: (1) gate.a_keeper_marker.detail — the live keeper id and
live determination, with a RE-KEYED clause prepended AHEAD OF THE PRESERVED PRIOR TEXT; (2)
gate.a_keeper_marker.read_live_at — the sha you actually read at, with the existing corrected_by text
moved under a "PRIOR:" label; (3) the top-level gate_a_provenance block — derived_at_sha,
derived_at_date, derived_by with the supersession chain prepended ahead of the preserved prior text.

READ EVERY FACT LIVE: keeper id and registry years from keepers/SPP.json and the registry sidecar;
determination, grade summary, fails, caveats from frontend/data/backcast/status/SPP.js; rubric version
from RUBRIC_VERSION in scripts/calibration_verdict.py; marker state from calibration-complete.json.

STATE THE VERDICT EFFECT PRECISELY. SPP is NOT in the `complete` block, so gate (a) reads FAIL before
and FAIL after — the marker did not move, and this re-key changes IDENTITY AND DETERMINATION TEXT
ONLY. The row's `fail` status is what makes it schema-legal (a `pass` row must hold `complete`), so do
not "improve" it to pass.

EXIT: check_gate_a_provenance.py exits 0; json.load parses; `git diff` touches exactly the three
leaves in one file and nothing else; prior text preserved in all three; commit, push, blob-verify.
Report the diff, the gate exit code, and the keeper id you actually found. Do not open a PR unless asked.
```

## D85-R — execute D85's own four record repairs, including the 46-key census blind spot (r#58)

```
You are the D85-R session of the capacity-expansion track, executing the recommendations of
docs/handoffs/FINDING-capx-d85-key-provenance-2026-09-07.md (owner ruling Q59's follow-on; capx ledger
§0bc.3(c)). MODEL: Opus. DATA PROFILE: code. BRANCH: claude/capx-d85r-record-repairs — FRESH off
origin/main.

WHAT D85 ESTABLISHED, and you do not re-litigate it. Census at HEAD: 214 committed run configs, 169
reproduce, 30 keyless, 15 mismatch. All 15 derived to their recorded literal under a named recipe with
ZERO UNCLASSIFIED: 6 registration lag (caiso_offer_surface_measured_ungrounded, registered 2026-09-02
after those bundles solved), 3 pre-ledger flip (the R-A storage-entry pair, PR #4442), 5 pre-ledger
flip + split-root fold (the fc6 arms solved with MARKET_SIM_DATA_ROOT relocated, D21 finding 6), and 1
request-not-resolution (the ERCOT golden fixture serialized the UNRESOLVED config). Step 3, from the
code path: a stale key is UNREACHABLE BY CONSTRUCTION for every class except the D24 §4.2 collision
form of the R-A pair, which cache_config_disagreements refuses on the serving seam. VERDICT:
BOOKKEEPING, NOT A DEFECT.

*** THE REFUSALS ARE PART OF THE FINDING AND THEY BIND YOU. *** D85 refused to re-register the lagging
field and refused to rewrite any committed cache_key, and it was right: a committed key is what that
bundle actually solved under, and rewriting it makes the artifact lie about its own provenance. You
inherit both refusals. If you conclude a key rewrite is the right repair, that is an OWNER CARD, not
your act — stop and report.

THE FOUR REPAIRS, all forward-looking, none touching a committed key:
 1. A CHECKED EXCEPTION RECORD for the 15 — a committed list, machine-checked, so the census reports
    "15 known, 0 unknown" instead of "15 mismatch". The check must FAIL if a SIXTEENTH appears, and
    must fail if a listed one starts reproducing (a stale exception is its own defect). Each entry
    carries its class and its citation.
 2. FOLD ROOTS IN THE RUN RECORD — the 5 split-root cases are unreproducible only because the run
    record does not say which data root the solve folded. Record it going forward.
 3. RESOLVED CONFIG IN THE GOLDEN WRITER — the 1 request-not-resolution case is the ERCOT golden
    fixture serializing the config as REQUESTED rather than as RESOLVED. Fix the writer so future
    fixtures serialize the resolved config.
 4. BOTH KEYS IN THE CENSUS — D85 surfaced, unasked, that since 2026-09-07 the ERCOT and CAISO solve
    surfaces are OFF their declarations, so 46 FURTHER keys reproduce only with the surface AT
    DECLARATION. That is the D79/Q54 mechanism behaving exactly as designed (a re-derived registry
    re-keys the ISOs whose rows moved) — it is NOT a defect and you must not "fix" the re-key. What
    was wrong is that the census reported one key and was blind to the other. Report BOTH: the
    at-HEAD-surface key and the at-declaration-surface key, so a reader can tell a designed re-key
    from a genuine mismatch at a glance.

PRE-REGISTER, before you edit: the exception list's expected membership (the 15, by config id and
class) and the expected census output after each repair. If your reproduced count differs from 214 /
169 / 30 / 15 — and it will, the corpus grows ~10-20 configs a day — report the drift and say which
configs are new. The COUNTS are measurements; ZERO UNKNOWN is the gate.

STOP GATES. (1) A sixteenth unclassified mismatch — STOP and report; that is a new finding, not a
list entry. (2) Any repair that would change a committed key, bundle, registration, flip entry or
surface declaration — STOP; that is outside the refusals. (3) The exception check passing when a
listed config starts reproducing — the check is wrong, fix the check. (4) Any determination or gate
moving anywhere — STOP; this is record hygiene and must move nothing scored.

DO NOT: rewrite a committed cache_key; re-register caiso_offer_surface_measured_ungrounded or any
lagging field; edit _CACHE_KEY_OPTIONAL_FIELDS, the FLIPS list or solve_surface_declared.py; solve
anything; touch D83/D84.

EXIT: the four repairs landed; the census reads "N known, ZERO unknown" and reports both keys; the
exception check fails correctly on both a new mismatch and a stale entry (demonstrate both with a
test); a FINDING recording what the repairs changed and what they deliberately did not. Report the
zero-unknown census line first in your close.
```

---

## r#59 NOTE

Two charters, both issued 2026-09-07 at main `60f244e3`, both against ledger §0bd.

* **D84** discharges **owner ruling Q60** ("D84 first, D83 after") — the last unclosed half of the
  D48 devintage, reserved since r#51 and unblocked since D75-R-ARM landed at r#55.
* **D86** is **director-tier** and needs no card: it repairs the guards on this desk's own D79 /
  Q54 mechanism, which are red and — worse — one of them green and vacuous. No arm, no default, no
  determination, no LP.

They are **disjoint by file and by act** and may run concurrently. D86 owns
`tests/unit/results/test_cache_solve_surface.py` and touches nothing else; D84 must not touch that
file. **NEXT FREE LABEL after these: D87** (check for collisions before spending it).

---

## D86 — the D79 solve-surface guard repair (Fable, code, zero LP)

```
You are the D86 lane for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. Branch: claude/capx-d86-d79-guard-repair, fresh off origin/main.
ZERO LP. No solve, no registration, no keeper, no marker, no arm, no default flip, no matrix stamp.

WHY YOU EXIST. capx D79 (owner ruling Q54) put a solve-surface fingerprint in ScenarioConfig.cache_key():
a registry table the solve reads but the config cannot express enters the key once its live hash moves
off its FROZEN declaration in config/solve_surface_declared.py. The MECHANISM IS SOUND. Its GUARDS are
not, and one of them is passing for the wrong reason. The capx director measured this at main 60f244e3:

  (i) OUTSIDE pytest, at HEAD: mutate constants.DEMAND_GROWTH_RATES["MISO"], call
      solve_surface.reset_caches(), re-hash ScenarioConfig(iso="MISO").cache_key() ->
      bcaf6043b8bfea74 becomes 13afdf6f728e5336, and moved_rows("MISO") reads
      {'DEMAND_GROWTH_RATES': '6744aaed2256cf46'}. The mechanism works.

  (ii) INSIDE pytest, the same mutation moves nothing, because tests/conftest.py:138
      _solve_surface_neutralized is AUTOUSE and monkeypatches scenarios.moved_rows -> lambda iso: {}
      and scenarios.applicable_epochs -> lambda config: [] for every test that does not carry
      @pytest.mark.solve_surface_live. tests/unit/config/test_solve_surface.py:49 carries the opt-out
      as a module-level `pytestmark`. tests/unit/results/test_cache_solve_surface.py -- whose module
      docstring IS "the addressing half: a bundle solved on surface S1 is NOT handed to a config
      running on S2" -- never got it.

THE THREE DEFECTS, graded per test in that one file:
  A. test_a_bundle_solved_on_S1_is_not_addressed_on_S2 -- RED. D79's addressing half has no passing
     guard at HEAD.
  B. test_another_isos_key_is_untouched_by_a_MISO_row -- GREEN AND VACUOUS. With moved_rows stubbed
     to {}, the ERCOT key cannot move for ANY mutation, so the rule 25 [R-ISO-SCOPE] per-ISO
     isolation assertion is trivially satisfied. This is the worse of the two: nobody looks at a
     green test.
  C. test_sidecar_is_written_beside_the_config -- RED for a DIFFERENT reason, and the reason is
     correctness. The sidecar writer calls solve_surface.surface_stamp directly, which the fixture
     does NOT stub, so it truthfully reports
     moved = {'NUCLEAR_MONTHLY_CF_BY_YEAR': '00a8e8726fd0edd6'}. The assertEqual(stamp["moved"], {})
     expectation was true when D79 landed at zero moves and false since ercot-253 (2026-09-06) added
     the 2021 row. A STALE SCOPE LABEL IS NOT A WRONG MEASUREMENT -- REPAIR IT FORWARD, NEVER
     BACKWARD.

STEP 0 -- REPRODUCE (ii) YOURSELF, BEFORE EDITING ANYTHING, and write it into your PRECOMMIT.
Run the (i) repro outside pytest at your own HEAD and record both keys.
  ** STOP GATE. If the key does NOT move outside pytest at your HEAD, STOP AND REPORT. **
  That would mean the mechanism itself is broken, not its guards; the object of repair is then
  src/market_sim/config/solve_surface.py, which is a DIFFERENT and owner-tier card, and this
  charter does not authorize it. Do not proceed on your own reading.

STEP 1 -- ARM THE FILE. Add the module-level opt-out to
tests/unit/results/test_cache_solve_surface.py in the SAME form the precedent file uses
(tests/unit/config/test_solve_surface.py:47-49: a two-line comment saying the file is ABOUT the
surface entering the key, then `pytestmark = pytest.mark.solve_surface_live`). The marker is already
registered in pyproject.toml:44 -- do not re-register it.

STEP 2 -- REPAIR DEFECT C FORWARD. This is the construction detail the charter is explicit about,
because the obvious reading is wrong: do NOT replace {} with the ERCOT dict literal, which goes
stale at the next ledgered move exactly as {} did. Assert the stamp against the LIVE surface and the
LIVE ledger:
  - stamp["moved"] == solve_surface.moved_rows("ERCOT")           (the stamp is truthful)
  - every name in stamp["moved"] is a key of
    tests.regression.test_persisted_identity.LEDGERED_SURFACE_MOVES_BY_ISO["ERCOT"]
    (an UNLEDGERED move still fails here, so this is not a weakening)
  - stamp["epochs"] == solve_surface.applicable_epochs(config)
  - stamp["rows"] == len(solve_surface.surface_rows("ERCOT"))
If importing the ledger from tests/regression is awkward, move nothing -- read the constant, do not
copy its contents into this file, and say in a comment which module owns it.

STEP 3 -- DEMONSTRATE NON-VACUITY, one test at a time. This is the deliverable, not step 1.
For EACH of the five tests in the file, break the thing it claims to measure and confirm that test
goes RED, then restore. Record the five results in a table in your FINDING: test name, what you
broke, red/not-red. A test that stays green when you break its subject is a SECOND finding -- report
it, do not paper over it.

STEP 4 -- MAKE THE MARKER'S REMOVAL LOUD. Add one test to the file that fails if the opt-out is ever
silently dropped again -- assert that the name the config module actually calls is the real function,
e.g. `assert scenarios.moved_rows is solve_surface.moved_rows`. A marker that can vanish without a
red is this defect recurring, and step 1 alone does not prevent it.

NEVER, under any reading:
  - edit src/market_sim/config/solve_surface_declared.py. It is APPEND-ONLY (rule 26 [R-DELETE]), and
    re-declaring a moved row RESTORES THE PRE-CHANGE KEY and re-serves the pre-change bundle. The two
    live moves are ledgered and correct: ERCOT NUCLEAR_MONTHLY_CF_BY_YEAR (ercot-253, the 2021 row
    ADDED for the rule-22 ladder) and CAISO STATE_CARBON_PRICE_BY_ISO + NUCLEAR_MONTHLY_CF_BY_YEAR
    (caiso-262, the 2022 rows ADDED for the validation touchpoint).
  - edit anything under src/market_sim/. This is a test-file repair.
  - weaken, scope down, or delete tests/conftest.py's _solve_surface_neutralized fixture. It is
    correct and it exists for a good reason (ercot-253's real move failed 12 field-arming pins across
    nine unrelated lanes' files). The repair is the OPT-OUT, not the fixture.
  - touch any other lane's red. FOUR other fast-tier tests are red on main at 60f244e3 and NONE is
    yours: tests/scoring/test_forecast_parity.py (2, MISO's miso-233 arms three miso_seam_neighbour_*
    fields with no forecast_parity_registry declaration), tests/unit/data/test_caiso_st_gas_peak_measured.py
    (CAISO, registry 1.166 vs artifact 1.154), tests/unit/model/test_capacity.py::TestGetRPSTarget::
    test_unregistered_iso_is_none (SPP now has an RPS floor, so get_rps_target("SPP",2030) is 0.0 not
    None). Name them in your FINDING as still-red-and-not-mine; fix none.

EXIT: the five tests in tests/unit/results/test_cache_solve_surface.py green AND each demonstrated
non-vacuous by the step-3 table; the step-4 marker guard added; scripts/check_key_provenance.py,
scripts/audit_keepers.py --check and tests/regression/test_persisted_identity.py all still green and
UNCHANGED; ruff check + ruff format clean; a short FINDING
(docs/handoffs/FINDING-capx-d86-2026-09-07.md) whose first line is the step-3 table. Lead your close
with that table, not with a list of edits. Rule 27 [R-PUSH]: the file is under 300 lines, but push
the exact on-disk bytes regardless and verify the pushed blob.
```

---

## D84 — PJM's 2025/26 3IA THERMAL accreditation vintage (Opus, pjm)

```
You are the D84 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: pjm. Branch: claude/capx-d84-pjm-thermal-3ia-vintage, fresh off origin/main.
Authority: OWNER RULING Q60 (2026-09-07, capx ledger §0bd.3(c)) -- "D84 first, D83 after".
This charter authorizes phase 0 and, if its gate passes, ONE screen solve. IT DOES NOT AUTHORIZE AN
ARM: arming is an owner card you SERVE, never an act you take.

THE OBJECT, exactly. constants.THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"] (defined at
src/market_sim/config/capacity_market.py:3134) is a SINGLE-VINTAGE table -- its own comment says so:
"the 2026/2027 BRA official/final class-average rating". But
THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"] == "2025/2026", so delivery year 2025/26 is
the FIRST year accredited on the ELCC-class design -- and 2025/26 has its OWN published 3IA class
ratings, which DIFFER: gas CC 78 vs 74, gas CT 63 vs 60, steam 74 vs 73, diesel 92 vs 91 (nuclear and
coal equal). One post-reform rating table is therefore being applied to a delivery year that cleared
under a different published construct.

THIS IS THE THERMAL TRANSPOSE OF A LANE THAT ALREADY WORKED. D75-R (owner ruling Q55, ARMED at r#55)
fixed exactly this defect on the VRE side: RENEWABLE_ELCC_CURVES_BY_ISO["PJM"] is digitized from the
2026/27+ MARGINAL ELCC ratings and CLAMPS on every PJM pool in the window, so D75-R introduced
RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO plus the gate pjm_vre_accreditation_vintage as a SUB-GATE of
pjm_accreditation_design_vintage (the two halves are never devintaged apart -- rule 19 [R-ONE-MECH]).
It measured accredited VRE down 754.6 / 332.9 / 148.3 MW in DY 2023/24-2025/26, reproducing its
zero-LP prediction to ~0.001 MW, with ALL 26 SCORED BANDS BYTE-IDENTICAL. Read
docs/handoffs/FINDING-capx-d75r-2026-09-06.md (esp. §6 item 4, which ROUTED this card to you) and
PRECOMMIT-capx-d75r-arm-2026-09-06.md before you design anything. Follow that shape unless you can
say why it does not fit -- and if it does not, say so and stop rather than inventing a third form.

THE BASIS IS RULE 14 [R-ACCURATE], NEVER THE RESIDUAL. You are preferring the delivery year's own
published rating over a rating published for a different year. If the repair makes a scored band
worse, that is rule 14's "treat the worse fit as a discovered bug" case and you report it at full
magnitude -- you do NOT revert to the 2026/27 table because it fits better, and you do not select
between vintages by which one moves a criterion (rule 1 [R-STRUCT]: that is the fitted-mechanism
selection the rule exists to forbid).

PHASE 0 -- ZERO LP, AND IT MAY KILL THE LANE (rule 29 [R-SCREEN] step 0).
 (a) THE INTAKE IS ALREADY THERE. D75-R §6 item 4 states "The intake now carries them" -- the 2025/26
     3IA rows are in the committed data/raw/capacity-market/elcc/pjm/pjm.csv. CONFIRM THAT YOURSELF
     and quote the rows. If they are absent, STOP and report: an intake card is a different lane.
     ZERO SCALAR FIELDS is the standard D67 and D75-R both met -- the MW/ratings are digitized from
     committed rows and reconciled against them BY TEST, never typed (rules 21 [R-DOF] / 24
     [R-REGISTRY]).
 (b) DECIDE AND WRITE DOWN THE VINTAGE RULE AND THE FALL-THROUGH RULE **BEFORE ANY SOLVE**, exactly as
     D67 did. Which published table governs which delivery year; what a pre-reform year does (it is
     UCAP 1-EFORd under pjm_accreditation_design_vintage, so state that the two must compose and not
     stack); what a year past the forward edge does. NOTE THE KNOWN TRAP, from D75-R §6 item 3: the
     2025/26 BRA cleared on the ratings current in July 2024, and THAT report's tables are IMAGES
     THAT DO NOT EXTRACT -- so a BRA-vintage rule you cannot source is not available to you. Say which
     vintage you use and why, and neither rule may be selectable by a result.
 (c) COMPUTE THE PREDICTION, per fuel class per delivery year, in accredited MW: what the census
     moves by, with sign, before any LP. D75-R's prediction reproduced to ~0.001 MW; hold yourself to
     that. Name which delivery years in the window are in-table and which fall through.
 (d) ENUMERATE THE CONSUMERS of the accreditation census the way D76 §4.2 did -- the D57 clearing
     half's sell-offer stack, the reliability floor, the reserve-margin backstop, the D67 published
     adequacy requirement, the CR-1 position -- and say which this moves and which it cannot.
 (e) G-DRIFT (rule 29(b)): audit `git diff <PJM keeper 2026-08-15-pjm-162-inputclock git_sha> HEAD`
     over the backcast solve path and classify every hunk INERT-with-reason or LIVE. NO CONTROL
     SOLVE: the committed keeper is the control (form 4). A matched cache key is not a G-DRIFT
     verdict -- read constants.py first.

     ** PHASE 0 STOP GATE. If the predicted per-class accredited-MW move is ZERO in every delivery
     year in the window, the lane is INERT and it ENDS HERE with that measurement as its result. Do
     not spend an LP to confirm a zero you already computed. **

SCREEN (only if phase 0's gate passes) -- ONE YEAR, named in your PRECOMMIT BEFORE it runs, and named
on the MECHANISM'S OWN LARGEST MEASURED FOOTPRINT from (c), NEVER on the biggest residual. The gate is
STRUCTURAL and STOP-ONLY (rule 29): does the dispatch/decision response have the direction and order
of magnitude the pre-solve delta implies; is the footprint confined to the rows the mechanism claims;
does the identity hold; does any non-target load-bearing criterion flip PASS -> FAIL. It may kill the
arm; it may NEVER promote one, and it is NEVER read against the target residual.

RULE 31 [R-RETAIN] BINDS YOU ABSOLUTELY. Gitignore the screen bundle family the moment it is written
(that alone discharges rule 29(c) -- the duty is about what reaches `main`, not what sits on disk).
DO NOT rm ANY solved bundle. The ercot-255 incident cost ~50 min of re-solves because a lane deleted
results it had judged not-promotable and the owner then ruled promote. Your final report must ASK THE
PROMOTION QUESTION EXPLICITLY and state that the bundles are on local disk and will not survive the
session.

DELIVERABLES: a PRECOMMIT pushed BEFORE any solve carrying (a)-(e), the vintage + fall-through rules,
the per-class per-DY prediction and the named screen year; then
docs/handoffs/FINDING-capx-d84-2026-09-07.md with the measurement against the prediction at full
magnitude, every consumer's move, what it does NOT close stated at the gate, and an OWNER CARD
recommending arm or not-arm with both sides at equal strength. If you recommend arming, the card must
say it would be the (b'-1) declared-default route or an iso_configs default_scenario_overrides arm
(D57/D67/Q55/Q56 all used the latter for PJM), what re-keys, and that every other ISO and every
backcast keeper stays byte-identical. Rule 28 [R-MECH-MATRIX] duty (c): a NEW ScenarioConfig field
needs its base row in docs/codebase-site/data/mechanism-matrix.js plus a cell line in ALL SEVEN
shards (SPP included) in the same PR -- CI enforces this half. Rule 27 [R-PUSH]: capacity_market.py
and scenarios.py are far over 300 lines -- edit locally, push on-disk bytes, blob-verify after every
push.

DO NOT TOUCH tests/unit/results/test_cache_solve_surface.py -- the concurrent D86 lane owns it.
```

---

## r#60 NOTE

Four charters, all issued 2026-09-08 at main `a667073f`, all against ledger §0be. **Three are
zero-LP; none authorizes an arm.**

* **GATE-(a) RE-KEY** — the Q34 standing duty, seventeenth firing and the **first double**.
* **D83** — **owner ruling Q60**'s "D83 after", now due: D84 landed and armed.
* **D89** — **owner ruling Q61**: this desk's own 27 reds, and none of the other 28.
* **D87/D88 READ** — the two SCN ruling-S19 seams, dispositioned by a READ rather than a repair.

**Collision map.** GATE-(a) touches `program-status.json` alone. **D83 and D89 both sit near
capacity evolution, so the boundary is named in BOTH prompts**: D83 owns the evolution-ledger writer
and must not touch D62/D74 code or tests; D89 owns `test_d62_*` / `test_d74_*` and must not touch the
evolution-ledger writer. D87/D88 READ writes one design doc and edits no `src/`. **NEXT FREE LABEL:
D90.**

**A CHARTER-WIDE CORRECTION carried into every prompt below (§0be.2(b)).** My D84 charter told the
lane to run `git diff <keeper git_sha> HEAD` for G-DRIFT. **That command cannot run**: the PJM
keeper records `git_sha = 457ae04`, dead since the 2026-08-16 history rewrite, and so does every
keeper older than it. **G-DRIFT's durable basis is the keeper bundle's recorded CACHE KEY**; the sha
is an optimisation available only for keepers newer than the rewrite.

---

## GATE-(a) RE-KEY — two rows, ERCOT and MISO (Fable, code, zero LP)

```
You are the capx gate-(a) re-key lane for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. Branch: claude/capx-gate-a-rekey-r60, fresh off origin/main.
ONE ACT, ZERO LP. No solve, no scoring, no registration, no keeper edit, no marker edit, no
determination re-computation, no other ISO's row, no other desk's file.

WHY. scripts/check_gate_a_provenance.py is EXIT 1 at main a667073f on TWO ISOs at once -- the
seventeenth firing of this standing duty and the first double. Both are promoter misses: a lane
promoted a keeper and did not re-key the ISO's §2.1b gate-(a) row in
frontend/data/forecast/program-status.json.

  ERCOT: row cites '2026-09-05-ercot248-two-config-keeper'; live keeper is
         '2026-09-08-ercot256-drag-layup-mask' (the netload_drag_layup_window_mask promotion).
  MISO:  row cites '2026-09-07-miso-233-spp-hourly'; live keeper is
         '2026-09-07-miso-243-spp-pairing'.

** DO NOT TRUST EITHER KEEPER ID ABOVE. ** They are this desk's reading at a667073f and keepers in
this repo have gone stale within hours -- SPP promoted three times in one day, and an r#58 row went
stale before the session that wrote it had finished. Read EVERY fact LIVE at your own HEAD, from the
backcast store, and re-key against what you find there, not against what this prompt says. If your
HEAD disagrees with the ids above, YOUR HEAD IS RIGHT: re-key to it and say so in your record.

METHOD -- and the method is the deliverable, because a bad edit here is worse than the stale row.
 1. Read the live facts for EACH ISO, and cite where each came from:
      - the designated keeper id: frontend/data/backcast/keepers/<ISO>.json
      - the marker state: BOTH blocks of frontend/data/backcast/calibration-complete.json
        (complete / final) -- report each as True/False, and note that `final` is EMPTY for every
        ISO in this repo, so no locked-test claim may appear in any row
      - the determination and per-year verdicts: the ISO's committed status sidecar
        (frontend/data/backcast/status/<ISO>.js), NOT a re-score -- this lane computes no verdict
      - the promotion instrument: the FINDING/PR/commit that promoted the keeper, named as a
        DOCUMENT, not just a PR number. (§0bc's SPP-45 lane had to add this afterwards because the
        prior re-key cited a PR and a sha but named no document. Do not repeat that.)
 2. Edit by TARGETED STRING EDIT of each row's three leaves only -- the `detail` head, `read_live_at`,
    and the `gate_a_provenance` block -- scoped by string position.
    ** NEVER a json.dumps round-trip. ** program-status.json is a hand-maintained COMMITTED seed that
    build_program_status wraps VERBATIM; a reserialization silently reformats every other desk's row
    and makes the diff unreviewable.
 3. PRESERVE THE PRIOR TEXT. Everything in the row that is not one of those three leaves stays
    byte-identical. Where the existing detail carries a RE-KEYED provenance sentence, add yours
    beside it rather than replacing it -- the row is a chain, not a snapshot.
 4. Touch ONLY the ERCOT and MISO rows. Do not fix another ISO's row even if you think it is stale;
    report it instead.

STOP GATES:
  - If check_gate_a_provenance.py is ALREADY EXIT 0 at your HEAD for an ISO, that ISO's re-key has
    landed while you were chartered. DO NOT re-key it -- asserting a supersession that did not happen
    is a false record. Say so and move to the other one. (This exact case happened at §0bc.)
  - If an ISO's live keeper id disagrees with BOTH the row and this prompt, re-key to the LIVE id and
    record all three states.
  - If re-keying would require changing a determination, a marker, a leg status or a grade: STOP.
    This guard compares IDENTITY ONLY and asserts nothing about either keeper's determination. A
    determination change is a different lane and an owner-tier question.

EXIT: check_gate_a_provenance.py EXIT 0 on all seven rows; scripts/audit_keepers.py --check still
PASS; the diff touches exactly the two rows of one file; a short record (append to the ERCOT and MISO
calibration logs, or a FINDING if you prefer one document) carrying the before/after `detail` head
for each ISO VERBATIM and the promotion instrument for each. Lead your close with the gate's exit
code, then the two id transitions. Rule 27 [R-PUSH]: push the exact on-disk bytes and verify the
pushed blob.
```

---

## D83 — the missing 2022 adequacy block in the evolution ledger (Opus, pjm)

```
You are the D83 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: pjm. Branch: claude/capx-d83-evolution-2022-adequacy, fresh off origin/main.
Authority: OWNER RULING Q60 (2026-09-07, capx ledger §0bd.3(c)) -- "D84 first, D83 after". D84 has
landed AND been armed by the owner, so this lane is now due.
This charter authorizes a DIAGNOSIS and, if the cause is a writer defect, its REPAIR. It does not
authorize a mechanism, an arm, a default change, or a re-registration.

THE OBJECT. evolution_2022.json carries NO adequacy block -- wind_cap_mw / solar_cap_mw /
renewable_credit_applied / storage_firm_mw are absent -- while evolution_2021.json and
evolution_2023..2025.json all carry it. Raised as D75 §6 item 3, re-raised as
FINDING-capx-d75r-2026-09-06.md §6 item 1, and REPRODUCED ON A FRESH SOLVE at HEAD, so it is not a
stale-bundle artifact. It has forced MANUAL POOL RECONSTRUCTION in two separate lanes -- D75-R's
phase 0 and its full-window analyzer both had to rebuild what the ledger should have recorded. It is
unexplained. Read both citations before touching anything.

WHY IT MATTERS MORE THAN IT LOOKS. The adequacy block is how a later reader learns what the capacity
screen actually tested in that year. A year missing it is a year whose screen is not reproducible
from its own record -- the same class of defect capx D85/D85-R spent two lanes closing on the cache
key, and D85-R's repair 2 (recording cache_key_path_roots + market_sim_data_root because "nothing in
the record said so") is the precedent for how to think about it. A missing record is not cosmetic; it
is a hole in provenance.

PHASE 0 -- ZERO LP, AND IT MAY ANSWER THE WHOLE CARD.
 (a) REPRODUCE IT AT YOUR OWN HEAD and say exactly how -- which invocation, which bundle, which file.
     Confirm the 2021 and 2023-2025 blocks ARE present in the same run, so the comparison is within
     one artifact family and not across vintages.
 (b) FIND THE WRITER and read it. Where is the adequacy block emitted, under what condition, and what
     is different about 2022? Candidates worth ruling in or out by reading, not by guessing: a
     year-scoped branch; an early return; a delivery-year vs calendar-year mapping that has no 2022
     entry; a data input absent for 2022 only; an exception swallowed. NAME the line.
 (c) DECIDE WHICH OF TWO THINGS THIS IS, and say which before you repair anything:
       (i)  a RECORDING defect -- the screen ran correctly and the writer failed to record it. Repair
            is to the writer; NO decision changes, NO key moves, and you must demonstrate that.
       (ii) a SUBSTANTIVE defect -- the screen genuinely had no adequacy operand in 2022, so the
            year's capacity decisions were taken on a different basis than its neighbours. That is
            NOT a record repair. STOP, write it up, and serve it as an owner card: it would mean
            every committed run's 2022 evolution year is on a different footing, which reaches
            D67/D57/D76 and is far beyond this charter.
     ** THIS IS THE STOP GATE, and getting it wrong in the (i) direction is the expensive error: **
     repairing a writer that was faithfully recording a real absence would paper over the substantive
     defect. Prove (i) affirmatively -- show the operand existed at screen time -- do not infer it
     from the repair looking small.

IF IT IS (i): repair the writer, and prove the repair is inert where it must be.
  - ZERO key moves. Run the committed-config key census before and after (the D84-ARM /
    D76-ARM-B probes under scripts/probes/ are the pattern) and report the count both ways.
  - No committed bundle is rewritten. Only runs solved after this lands carry the new block -- that
    is D85-R repair 2's rule and it binds here identically.
  - A test that fails if a year ever loses the block again. This defect survived two lanes noticing
    it; the repair is not done until it cannot recur silently.

G-DRIFT, WITH MY OWN CORRECTION: do NOT use `git diff <keeper git_sha> HEAD`. That command is dead --
the PJM keeper records git_sha = 457ae04, which the 2026-08-16 history rewrite removed, and so does
every keeper older than the rewrite. Anchor on the keeper bundle's RECORDED CACHE KEY instead, and
audit the solve-path diff from a commit you can actually resolve. If you cannot establish drift at
all, say so rather than asserting either way.

RULE 31 [R-RETAIN]: if you solve anything, gitignore the bundle family the moment it is written and
DO NOT rm it. Ask the promotion question explicitly in your close and state that any bundle is on
local disk and will not survive the session.

DO NOT TOUCH tests/unit/model/test_d62_published_going_forward_bar.py or
test_d74_no_default_cap_convention.py, or the D62/D74 mechanism code -- the concurrent D89 lane owns
those. If your diagnosis reaches them, STOP and report the overlap rather than editing across the
boundary.

EXIT: docs/handoffs/FINDING-capx-d83-2026-09-07.md leading with (c)'s verdict -- (i) or (ii) -- and
the named line from (b); the repair with its zero-key-move census if (i); the owner card if (ii); the
recurrence test either way. Rule 27 [R-PUSH]: edit locally, push on-disk bytes, blob-verify any file
over 300 lines.
```

---

## D89 — the 27 reds in this desk's own D62 / D74 test files (Opus, code)

```
You are the D89 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d89-d62-d74-reds, fresh off origin/main.
Authority: OWNER RULING Q61 (2026-09-08, capx ledger §0be.3(b)) -- "Charter D89 for capx's own 27;
fix none of the other 28."
ZERO LP EXPECTED. If you conclude a solve is required, STOP and say why before spending one.

WHY YOU EXIST. capx D86, chartered to repair two guards, returned an inventory nobody asked for:
running `tests/unit tests/scoring tests/regression`, 55 tests are RED on main (57 before its repair,
55 after, 0 newly broken). TWENTY-SEVEN of them are in files named for THIS DESK'S OWN LANES:

  tests/unit/model/test_d62_published_going_forward_bar.py   15
  tests/unit/model/test_d74_no_default_cap_convention.py     12

D62 (PJM's published gross ACR as the retirement screen's going-forward bar AND the sell-offer cap)
and D74 (the Manual 18 "NA" no-default-cap price-taker convention) both LANDED at capx r#48, both
built DEFAULT-OFF, and neither has been touched since. D74 additionally carries a SELF-EXECUTING
DO-NOT-ARM -- and the evidence for that refusal is precisely these tests.

THE QUESTION, AND IT IS THE WHOLE LANE. Diagnose BEFORE you repair, and say which of these it is:

  (A) FIXTURE ROT. A later change (D67, D75-R, D76, D78, D84, the D79 solve surface, a registry
      re-derivation, the conftest autouse fixture family) moved something these tests hard-code, and
      the mechanisms themselves are fine. Repair is to the tests, FORWARD -- assert against the live
      source of truth, never re-freeze today's literal, which is exactly the stale-label mistake D86
      repaired in test_cache_solve_surface (see FINDING-capx-d86-2026-09-07.md §2 step 2 for the
      form: assert against the live registry/ledger, and import rather than copy it).

  (B) A REAL BEHAVIOUR CHANGE. D62's or D74's mechanism no longer does what it did at r#48. This is
      the serious answer: D74's DO-NOT-ARM rests on measurements those tests encode, so if the
      behaviour moved, the refusal may rest on a state that no longer exists. STOP at that point,
      write it up, and serve it as an owner card -- do NOT silently update a test to match changed
      behaviour, which would erase the evidence for a standing refusal.

  (C) A MIX. Classify EVERY ONE of the 27 individually. "Mostly A" is not an answer; the ledger's
      standard is ZERO UNCLASSIFIED (capx D85's census is the precedent -- 15 mismatches, all 15
      derived to their recorded literal, zero unknown).

METHOD:
 1. Reproduce the count at your own HEAD first and state the exact command. Numbers drift; D86's 55
    was measured at ad78cc3e. If your count differs, YOUR count is the one you work from, and say so.
    (§0be doctrine: A RED INVENTORY IS ONLY AS WIDE AS THE COMMAND THAT PRODUCED IT -- state yours.)
 2. Classify all 27 into A / B / C-per-test with the failing assertion and its cause named per row.
    A table is the deliverable, one row per test.
 3. Repair only the A rows, forward. For each, say what live source the assertion now reads.
 4. For any B row: STOP the repair for that row, and write the owner card. Report it at full
    magnitude -- what changed, when (bisect to a merge if you can do it cheaply), and what it does to
    D74's DO-NOT-ARM and D62's landed state.
 5. When you are done, re-run the SAME wide command and report the new total. "Fixed N, newly broken
    0" is the form D86 used and it is the form expected here.

BOUNDARIES, all binding:
  - FIX NONE OF THE OTHER 28. They belong to other desks: golden-manifest provenance 7, test_soundness
    end-to-end 6, results/export 4, FF readiness battery 4, forecast parity 2 (MISO's miso-233 arms
    three miso_seam_neighbour_* fields with no forecast_parity_registry declaration), caiso_st_gas_peak
    1 (registry 1.166 vs artifact 1.154), capacity TestGetRPSTarget 1 (SPP now has an RPS floor),
    registration-marker gate 1, gate-(a) 1, backcast artifacts 1. INVENTORY them in your FINDING with
    the owning desk named -- reporting is this lane's job, editing is not. An all-55 sweep was offered
    to the owner and marked NOT RECOMMENDED for exactly this reason (rule 25 [R-ISO-SCOPE], and the
    §0bd cross-desk collision).
  - DO NOT ARM D62 OR D74, or move any default. D74's DO-NOT-ARM stands until an owner says otherwise.
  - DO NOT TOUCH the evolution-ledger writer -- the concurrent D83 lane owns it. If your diagnosis
    reaches it, STOP and report the overlap.
  - DO NOT weaken, skip, xfail or delete a test to make it green. That is forbidden outright
    (CLAUDE.md's PR rules: never skip, disable or quarantine a test to get green). A test you cannot
    repair is a finding, not a deletion.
  - Rule 28 [R-MECH-MATRIX]: if any repair changes what a mechanism DOES rather than what a test
    reads, that is a cell update in all seven shards and probably answer (B) -- see step 4.

EXIT: docs/handoffs/FINDING-capx-d89-2026-09-08.md whose FIRST content is the 27-row classification
table (test · failing assertion · A/B · cause · action), then the before/after wide-command counts,
then the 28-row other-desk inventory with owners named. Lead your close with the table and the
"fixed N, newly broken 0" line. ruff check + ruff format clean. Rule 27 [R-PUSH]: both test files are
well over 300 lines -- edit locally, push exact on-disk bytes, blob-verify after every push.
```

---

## D87 / D88 READ — disposition the two SCN ruling-S19 seams (Fable, code, zero LP)

```
You are the D87/D88 READ lane for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. Branch: claude/capx-d87-d88-s19-read, fresh off origin/main.
THIS IS A READ, NOT A REPAIR. ZERO LP. You edit NOTHING under src/market_sim/, no test, no config,
no matrix shard, no registration. You write ONE design document. That is the entire deliverable.

WHY A READ AND NOT A CHARTER. SCN ruling S19 (2026-09-07, scenario-desk-ledger-2026-09.md §3) routed
two seams to the capx director on the D-9 -> S7 -> capx D77 precedent; the SCN desk charters neither
("SCN lanes report and stop") and its §4 records that the CCS pricing path and the fleet SoA builder
"are the capx director's objects". The capx desk ACCEPTED both at §0bd am.1 and reserved the labels
WITHOUT reading their substance, on its own standing doctrine: READ BEFORE CHARTERING, AND EXPECT THE
READ TO CLOSE THINGS. The precedent that earned that doctrine is capx D82 -- recommended as the
highest-value lane available, and one zero-LP read CLOSED it, replacing a solve program. THIS READ IS
LICENSED TO DO THE SAME. Closing one or both is a fully acceptable outcome and is not a failure.

THE TWO OBJECTS.

  D87 = SCN card D-15, raised by SCN-WS5A-POLICY-NYISO §9 item 1. "The CES target row cannot reach
  the CCS retrofit screen and the premium can -- a footprint-wide attribute-coverage seam."
  Anchor: ccs.py around lines 475-476, where the retrofit uplift is priced. This is capacity-evolution
  STEP 2 (the CCS retrofit screen), which is this desk's own step, and it sits next to capx D77's
  already-repaired CCS emission-rate seam -- read D77's finding first, because a second seam in the
  same file may be the same defect or its neighbour.

  D88 = SCN card D-14, raised at SCN r#19 by SCN-RESOLVE-G1-RECHECK. "unit_id is not a key in an
  evolved fleet." aggregate_fleet re-mints ids of the form {fuel_type}_{...}, so the question SCN
  poses is: should the fleet builder emit unique ids, or must every consumer qualify by fuel_type?
  The ask is a uniqueness GUARD plus a NARROW re-mint.

WHAT THE READ MUST ANSWER, per object:
 1. IS IT REAL AT HEAD? Reproduce the claim by reading the code, and quote the lines. A seam that has
    been repaired since SCN raised it is CLOSED -- say so and stop on that object. (D-14 was raised at
    SCN r#19, which is several days and many merges ago.)
 2. WHAT IS ITS BLAST RADIUS? Which committed artifacts, which ISOs, which modes. Specifically for
    D87: does it reach a BACKCAST at all, or only forecast-mode capacity evolution? (Step 2 is
    forecast-only, so state whether any keeper can be affected -- if none can, that changes the
    priority entirely.) For D88: enumerate the consumers that index by unit_id and say which of them
    can actually collide.
 3. IS IT A DEFECT OR A CONVENTION? A re-minted id is not automatically wrong; a consumer that
    qualifies by fuel_type is a legitimate design. Say which reading the code actually supports.
 4. WOULD A REPAIR HAVE ZERO FREE PARAMETERS? (rules 21 [R-DOF] / 24 [R-REGISTRY]). If a repair would
    need a tuned value, that is an owner card, not a lane.
 5. WOULD IT MOVE ANY KEY? Answer from the code path -- does the object sit inside a config the
    cache key sees, or inside a registry the D79 solve surface sees, or neither?
 6. YOUR RECOMMENDATION: CHARTER (with a one-paragraph scope and a model), MERGE THE TWO INTO ONE
    LANE, or CLOSE, with the reason. Recommend closing if that is what the read supports -- and if
    the two seams turn out to be one object, say so; merging them is a better outcome than two
    charters.

STOP GATES:
  - Do not repair anything, even a one-line fix that looks obvious. A repair inside a read is a
    change nobody pre-registered.
  - Do not spend an LP. If you believe a measurement is needed to answer a question above, name the
    measurement and leave it to the successor charter -- that is a legitimate finding.
  - If either object turns out to belong to another desk after all (SCN's, the SPP desk's, the audit
    board's), say so and route it back rather than absorbing it.

EXIT: docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md, one section per object, each answering
1-6 with code citations, and closing with a single RECOMMENDATION line per object. If you recommend
chartering, include the scope paragraph the director would paste. Lead your close with the two
recommendation lines and nothing else first. No src/ edit, no matrix touch, no registration.
```

---

## r#61 NOTE

Four charters, issued 2026-09-08 at main `7486cb9b`, against ledger §0bf. **D88 IS THE ONE TO RUN
FIRST** — it discharges owner ruling **Q62** and carries a flag on a live registered verdict.

* **D88** (Q62) — the fleet-id uniqueness guard, the vintage-stamped re-mint, and the `neiso-t3`
  provenance flag. Opus, `neiso` + `code`.
* **D87** — the CCS clean-tier seam. Opus, `nyiso` + `code`. **Phase 0 NOW; edit and screen AFTER
  D88 merges** — the STOP names an act, not a session.
* **D83** — **RE-EMITTED WHOLE**, never dispatched at r#60. Owner ruling Q60. Opus, `pjm`.
* **D89** — **RE-EMITTED WHOLE**, never dispatched at r#60. Owner ruling Q61. Opus, `code`.

**Collision map — `ccs.py` and `evolve.py` are touched by three of the four, so each prompt states
its own hunks.** D88 owns `ccs.py`'s conversion block (`:590-591`), `arrays.py:3651`, and
`evolve.py`'s `_retrofitted_ids` / exempt-set lines. D87 owns `ccs.py:475-476` and the
`evolve.py:664` threading. D83 owns the evolution-**ledger writer** (the adequacy block) and neither
lane's hunks. D89 is disjoint from all three. **NEXT FREE LABEL: D90.**

**Carried into every prompt (§0be.2(b)):** G-DRIFT's durable basis is the keeper bundle's recorded
**cache key**, never `git diff <keeper git_sha> HEAD` — that sha is dead for every keeper predating
the 2026-08-16 history rewrite.

---

## D88 — fleet ids are keys: a uniqueness guard, a vintage-stamped re-mint, and the `neiso-t3` flag (Opus, neiso + code) — RUN THIS FIRST

```
You are the D88 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso (for the screen) + code. Branch: claude/capx-d88-fleet-id-uniqueness,
fresh off origin/main.
Authority: OWNER RULING Q62 (2026-09-08, capx ledger §0bf.3(a)) -- "Fix first, flag the verdict now."
Source of the scope: docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md §2, whose §2.6 scope
paragraph this charter adopts. READ THAT DOCUMENT FIRST -- it did the census and it is the reason
this lane exists.

WHY THIS IS URGENT AND NOT BOOKKEEPING. A legacy representative (e.g. gas_cc_h_class_Central) is
retrofitted to CCS but KEEPS its unit_id, and the fleet builder then RE-MINTS that same id for the
next economic gas-CC build in the same zone. A census over 496 committed evolution_<year>.json
ledgers found this firing in ALL NINE NEISO T3 golden variants, colliding 2032->2050 (bau-d65br from
2037), and in ERCOT ff-t1f-d65br in 2030 (terminal year only, no screen reads it). The record shows
it happening: in bau-prera-2026-08-31 the SAME id is logged as retrofitted in 2031, 2040, 2042 and
2044 -- impossible for one unit, since a retrofit is irreversible (ccs.py:400) -- so by 2045 that
fleet carries FOUR generators named gas_cc_h_class_Central.

On a duplicate: retirements.py:3423's idx_of is LAST-WRITE-WINS, so a converted unit's pro-forma
margin reads its unabated twin's dispatch inside the step-3 exit screen; one twin's exemption exempts
both; RETIRING ONE TWIN DROPS BOTH from the fleet (a capacity leak); the loss_years exit clock is
shared; the D57 sell-offer stack double-offers under one id. Backcast: NEVER (a backcast rebuilds its
base fleet yearly and never enters evolve_fleet). Hindcast/crossover: cannot fire (the retrofit sits
below the 2028 gate).

WHAT IS NOT KNOWN, AND YOU MUST NOT PRETEND OTHERWISE: the SIZE AND DIRECTION of the decision delta
are UNMEASURED. Only your screen can measure them. Do not assert a direction before you have it.

TWO PARTS, ONE LANE, GUARD FIRST.

(a) THE GUARD. In generators_to_fleet_arrays (src/market_sim/data/fleet/arrays.py:3651), raise
    ValueError NAMING the duplicated ids when len(set(unit_ids)) != len(unit_ids). It changes no
    decision and costs one set build per year.
    ** PHASE 0, ZERO LP, BEFORE ANYTHING ELSE LANDS: ** prove the guard is SILENT on every ISO's
    on-recipe `fleet_only` rebuild -- every backcast keeper and every T1-F / T1-H recipe (~90 s
    each). If it fires anywhere you did not predict, STOP and report: that is a second population
    the census did not reach (the read's §4 item 2 names this as an open question), and it changes
    the lane.

(b) THE RE-MINT. In apply_ccs_retrofit's conversion block (ccs.py:590-591), for a NON-CAMPD legacy
    representative whose id equals f"gas_cc_{efficiency_bin}_{zone}" exactly, re-mint it as
    f"gas_cc_ccs_{efficiency_bin}_{zone}_r{year}" and write the new id to the ledger row as an
    ADDITIVE `to_unit_id` beside the existing `unit_id`. _retrofitted_ids / exit_exempt_unit_ids
    (evolve.py:685, :757) carry the NEW id.
    ** THE VINTAGE STAMP IS LOAD-BEARING AND THE OBVIOUS FORM IS WRONG. ** `gas_cc_ccs_{bin}_{zone}`
    alone is INSUFFICIENT: the T3 record shows the same zone converting a second (2040), third and
    fourth representative, and gas_cc_ccs is not aggregatable, so two converted representatives would
    collide WITH EACH OTHER. The `_r{year}` suffix mirrors new_entry.py:648's {tech}_new_{year}_{seq}
    -- deterministic, order-independent, and unique by construction once the guard holds (one id
    converts at most once per year). CAMPD per-plant ids are UNTOUCHED (is_campd_bin passthrough).
    ZERO config fields, ZERO constants (rules 21 [R-DOF] / 24 [R-REGISTRY]).

NOT IN SCOPE, and the read gives the reason for each: adding gas_cc_ccs to _AGGREGATABLE_FUELS (it
changes the LP column set by merging units with different online_year and ccs_capture_fraction
provenance -- a behaviour change and a second mechanism in one lane); any consumer refactor; the I5
forecast invariant's own keying (route it to the forecast desk, with your guard named as the fix).

KEYS: no key moves -- ids are not hashed (scenarios.py:18691-18717) and SURFACE_MODULES excludes
data/fleet. But BEHAVIOUR moves at UNCHANGED keys on the nine NEISO T3 variants from 2032 and on
ERCOT d65br's 2030 FleetContext: that is the same-key invalidation class, so this lane OWES a
cache-epoch entry naming them. Prove byte-identity on one non-colliding bundle at zero LP by
replaying its ledger (NYISO d65br is the read's suggestion).

SCREEN (rule 29 [R-SCREEN]) -- and ONE YEAR IS THE WRONG INSTRUMENT HERE, deliberately: the object
only exists ACROSS years, so the screen is the CHEAPEST COLLIDING HORIZON. NEISO T3 bau-d65br recipe,
2026-2040. CONTROL = the committed bundle under a G-DRIFT audit (rule 29(b) form 4) -- NO CONTROL
SOLVE. G-DRIFT's basis is the bundle's RECORDED CACHE KEY, not `git diff <git_sha> HEAD`, which is
dead for anything predating the 2026-08-16 history rewrite.
STOP GATES, STRUCTURAL ONLY, pre-registered before the screen runs:
  - the guard is SILENT in every year of the screen;
  - 2026-2031 ledgers BYTE-IDENTICAL to the control;
  - from the first colliding year the fleet carries NO duplicate id and the ccs_retrofits rows carry
    distinct to_unit_ids;
  - no NON-GAS ledger row moves in any year.
The gate is STOP-ONLY: it may kill the arm, it may never promote it, and it is never read against a
residual.

(c) THE FLAG -- Q62's second half, IN THIS SAME SESSION. Add a ONE-LINE ADDITIVE provenance field to
the neiso-t3 verdict record in frontend/data/forecast/ff-verdicts.json (the record at :4835-4843,
keyed to neiso-2026-2050-t3-golden3-d60, cache key f04fd06348e1623d) saying the run carries known
in-horizon unit_id collisions from 2032 and a re-score is pending, citing the design read.
  ** ADDITIVE ONLY. NEVER a verdict letter, NEVER a score, NEVER a leg status, NEVER a removal. **
  ff-verdicts.json is the COMMITTED FF-2D snapshot and `register_forecast_run.py --reindex` bakes it
  into the generated namespace -- CONFIRM your added field survives a --reindex and does not change
  any generated verdict; if it does not survive, STOP, do not force it, and report where the flag
  belongs instead. THE RE-SCORE IS NOT YOURS: route it to the D63/D65-B batch on repaired code and
  say so in the FINDING.

RULE 31 [R-RETAIN]: gitignore the screen bundle family the moment it is written; DO NOT rm any solved
bundle. Ask the promotion question explicitly in your close and state that the bundles are on local
disk and will not survive the session.

BOUNDARIES: you own ccs.py's CONVERSION block (:590-591), arrays.py:3651, and evolve.py's
_retrofitted_ids / exempt-set lines. You do NOT touch ccs.py:475-476 or evolve.py:664 -- the
concurrent D87 lane owns those. You do NOT touch the evolution-ledger adequacy-block writer -- the
concurrent D83 lane owns that. If your work reaches either, STOP and report the overlap.

EXIT: the guard + rename; a seam test (a legacy representative retrofitted then re-minted by later
entry yields two DISTINCT ids and no raise; a CAMPD tranche keeps its id; a fleet with a forced
duplicate raises); the cache-epoch entry naming the nine NEISO T3 variants and ERCOT d65br; the NEISO
matrix shard's ccs_retrofit_screen cell (rule 28 [R-MECH-MATRIX] duty b); the ff-verdicts flag; and
docs/handoffs/FINDING-capx-d88-2026-09-08.md leading with the phase-0 guard-silence result and then
the screen's STOP table. Rule 27 [R-PUSH]: every file here is well over 300 lines -- edit locally,
push exact on-disk bytes, blob-verify after every push.
```

---

## D87 — the retrofit screen consumes the clean-tier seam (Opus, nyiso + code)

```
You are the D87 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: nyiso (for the screen) + code. Branch: claude/capx-d87-ccs-clean-tier-seam,
fresh off origin/main.
Source of the scope: docs/handoffs/DESIGN-capx-d87-d88-s19-read-2026-09-08.md §1, whose §1.6 scope
paragraph this charter adopts. READ IT FIRST. Origin: SCN ruling S19 routed this seam to the capx
desk; capx §0bd am.1 accepted it and §0bf chartered it.

** THE STOP NAMES AN ACT, NOT A SESSION -- READ THIS BEFORE ANYTHING ELSE. **
Your PHASE 0 IS ZERO-LP AND STARTS NOW. Only your EDIT to ccs.py / evolve.py and your SCREEN wait
for the concurrent D88 lane to MERGE. Do not idle waiting for it; do the whole zero-LP half, push
your PRECOMMIT, and then take the edit when D88 is on main. If D88 has already merged when you open,
proceed straight through. The reason for the order is not politeness: D88 installs a duplicate-id
GUARD, and your screen should run with it armed so that if folding the dual grows the NYISO retrofit
set into a later re-mint, the SCREEN says so instead of a downstream scorer.

THE OBJECT. The CCS retrofit screen prices each continuation's certificate through ONE resolver:

    # ccs.py:472-476
    attr_unabated = effective_eac_price_for_unit(config, "gas_cc",     old_er, year)
    attr_post     = effective_eac_price_for_unit(config, "gas_cc_ccs", new_er, year)

and that resolver folds TWO legs only -- the legacy per-fuel scalar and the exogenous premium
(federal_ces.py:586-590, 627-629). The CES TARGET ROW's dual lives somewhere else entirely:
clean_attribute_price_by_fuel, threaded from the prior year's clean_region_duals
(runner.py:2331, :2351, :4724-4738) into evolve_fleet (evolve.py:118) -- and evolve_fleet NEVER hands
it to the retrofit screen (evolve.py:664-674). So the premium reaches the screen and the target row
cannot. Real at HEAD and unrepaired since SCN raised it: the only commit touching those files since
is the PJM sector-gate merge, which does not touch the pricing lines.

THE REPAIR, and it is one seam: thread clean_attribute_price_by_fuel from evolve_fleet
(evolve.py:664) into apply_ccs_retrofit as a None-DEFAULT keyword, and fold
clean_credit_for_zone(by_fuel, fuel, zone_idx) into BOTH attr_unabated and attr_post at
ccs.py:475-476 THROUGH THE EXISTING max() -- the same composition retirements.py:3634 and
new_entry.py:1202 already use. NO new field, NO new constant, NO RPS leg (rules 21/24). The
None-default is what makes every family without a clean dual byte-identical: no row => by_fuel has no
federal entry => max(x, 0) == x.

PHASE 0 -- ZERO LP, STARTS IMMEDIATELY, AND IT MAY CHANGE THE LANE:
 (i) Reconstruct the pre-solve delta for the NYISO CES-T80 2028-2030 cohort from its COMMITTED
     duals.json -- dual x 0.95 per MWh into the uplift_window -- and state, per year, what the
     retrofit set should move by and in which direction, before any solve.
 (ii) Measure whether the MI clean row's dual is NON-ZERO in 2027-2029 in ANY committed MISO T1-F
     bundle. The read could not answer this from the artifacts (its §4 item 1). If it IS non-zero,
     the MISO T1-F family is in the blast radius and your cache-epoch entry must name it.
 ** PHASE 0 STOP GATE: if the reconstructed delta is ZERO in every year of the target cohort, the
 seam is INERT on the committed record and the lane ENDS THERE with that measurement as its result.
 Do not spend an LP to confirm a zero you already computed. **

SCREEN (rule 29): ONE year, NYISO 2030 -- the only ISO with retrofit headroom (campaign §6) and the
ISO the seam was measured on. Name it in the PRECOMMIT before it runs. CONTROL = the committed
scn-campaign-policy-2026-09-06/NYISO/CES-T80 bundle under a G-DRIFT audit -- NEVER a control solve.
G-DRIFT's basis is the bundle's RECORDED CACHE KEY, not `git diff <git_sha> HEAD`, which is dead for
anything predating the 2026-08-16 history rewrite.
STOP GATES, STRUCTURAL ONLY:
  - every CES-P* leg's retrofit ledger BYTE-IDENTICAL (no row => no federal entry => max(x,0) == x);
  - the target leg's retrofit set moves in the DIRECTION and ORDER the phase-0 delta implies, and
    stays within the 3 GW/yr/ISO cap;
  - no non-CCS ledger row moves in 2026-2027;
  - every backcast keeper and every ff-t1h hindcast byte-identical, BY CONSTRUCTION and BY TEST.
STOP-ONLY: it may kill the arm, never promote it, and it is never read against a residual.

RULE 31 [R-RETAIN]: gitignore the screen bundle family when written; DO NOT rm any solved bundle; ask
the promotion question explicitly in your close and say the bundles will not survive the session.

BOUNDARIES: you own ccs.py:475-476 and the evolve.py:664 threading. You do NOT touch ccs.py's
conversion block (:590-591), arrays.py:3651, or evolve.py's _retrofitted_ids / exempt-set lines --
D88 owns those. You do NOT touch the evolution-ledger adequacy-block writer -- D83 owns that. Not in
scope: D77's routed parasitic-uplift item; the level of ccs_retrofit_vom_adder; anything under
_AGGREGATABLE_FUELS (that is D88's, and it declined it).

EXIT: the fix; a seam test in tests/unit/model/test_ccs_retrofit.py (a target-row config buys
retrofit where a zero-premium config does not; a None family is byte-identical); the cache-epoch
entry; the NYISO matrix shard's ccs_retrofit_screen and federal_ces cells (rule 28 duty b); and
docs/handoffs/FINDING-capx-d87-2026-09-08.md that RE-BASES the campaign's target-row rows and ROUTES
the six ISO policy FINDINGs' CES-T80 numbers to the SCN desk for re-statement -- route, do not
re-state them yourself. Lead your close with the phase-0 delta table and the screen verdict. Rule 27
[R-PUSH]: edit locally, push exact on-disk bytes, blob-verify after every push.
```

---

## D83 — the missing 2022 adequacy block (Opus, pjm) — RE-EMITTED WHOLE

```
You are the D83 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: pjm. Branch: claude/capx-d83-evolution-2022-adequacy, fresh off origin/main.
Authority: OWNER RULING Q60 (2026-09-07, capx ledger §0bd.3(c)) -- "D84 first, D83 after". D84 has
landed AND been armed by the owner, so this lane is due.
THIS CHARTER WAS ISSUED AT r#60 AND NEVER DISPATCHED (no branch, no commit, no document, confirmed on
a second fetch). It is RE-EMITTED WHOLE and nothing about it is re-derived -- start from the top.
This charter authorizes a DIAGNOSIS and, if the cause is a writer defect, its REPAIR. It does not
authorize a mechanism, an arm, a default change, or a re-registration.

THE OBJECT. evolution_2022.json carries NO adequacy block -- wind_cap_mw / solar_cap_mw /
renewable_credit_applied / storage_firm_mw are absent -- while evolution_2021.json and
evolution_2023..2025.json all carry it. Raised as D75 §6 item 3, re-raised as
FINDING-capx-d75r-2026-09-06.md §6 item 1, and REPRODUCED ON A FRESH SOLVE at HEAD, so it is not a
stale-bundle artifact. It has forced MANUAL POOL RECONSTRUCTION in two separate lanes -- D75-R's
phase 0 and its full-window analyzer both had to rebuild what the ledger should have recorded. It is
unexplained. Read both citations before touching anything.

WHY IT MATTERS MORE THAN IT LOOKS. The adequacy block is how a later reader learns what the capacity
screen actually tested in that year. A year missing it is a year whose screen is not reproducible
from its own record -- the same class of defect capx D85/D85-R spent two lanes closing on the cache
key, and D85-R's repair 2 (recording cache_key_path_roots + market_sim_data_root because "nothing in
the record said so") is the precedent for how to think about it. A missing record is not cosmetic; it
is a hole in provenance.

PHASE 0 -- ZERO LP, AND IT MAY ANSWER THE WHOLE CARD.
 (a) REPRODUCE IT AT YOUR OWN HEAD and say exactly how -- which invocation, which bundle, which file.
     Confirm the 2021 and 2023-2025 blocks ARE present in the same run, so the comparison is within
     one artifact family and not across vintages.
 (b) FIND THE WRITER and read it. Where is the adequacy block emitted, under what condition, and what
     is different about 2022? Candidates worth ruling in or out by reading, not by guessing: a
     year-scoped branch; an early return; a delivery-year vs calendar-year mapping that has no 2022
     entry; a data input absent for 2022 only; an exception swallowed. NAME the line.
 (c) DECIDE WHICH OF TWO THINGS THIS IS, and say which before you repair anything:
       (i)  a RECORDING defect -- the screen ran correctly and the writer failed to record it. Repair
            is to the writer; NO decision changes, NO key moves, and you must demonstrate that.
       (ii) a SUBSTANTIVE defect -- the screen genuinely had no adequacy operand in 2022, so the
            year's capacity decisions were taken on a different basis than its neighbours. That is
            NOT a record repair. STOP, write it up, and serve it as an owner card: it would mean
            every committed run's 2022 evolution year is on a different footing, which reaches
            D67/D57/D76 and is far beyond this charter.
     ** THIS IS THE STOP GATE, and getting it wrong in the (i) direction is the expensive error: **
     repairing a writer that was faithfully recording a real absence would paper over the substantive
     defect. Prove (i) affirmatively -- show the operand existed at screen time -- do not infer it
     from the repair looking small.

IF IT IS (i): repair the writer, and prove the repair is inert where it must be.
  - ZERO key moves. Run the committed-config key census before and after (the D84-ARM /
    D76-ARM-B probes under scripts/probes/ are the pattern) and report the count both ways.
  - No committed bundle is rewritten. Only runs solved after this lands carry the new block -- that
    is D85-R repair 2's rule and it binds here identically.
  - A test that fails if a year ever loses the block again. This defect survived two lanes noticing
    it; the repair is not done until it cannot recur silently.

G-DRIFT: do NOT use `git diff <keeper git_sha> HEAD`. That command is dead -- the PJM keeper records
git_sha = 457ae04, which the 2026-08-16 history rewrite removed, and so does every keeper older than
the rewrite. Anchor on the keeper bundle's RECORDED CACHE KEY instead, and audit the solve-path diff
from a commit you can actually resolve. If you cannot establish drift at all, say so rather than
asserting either way.

RULE 31 [R-RETAIN]: if you solve anything, gitignore the bundle family the moment it is written and
DO NOT rm it. Ask the promotion question explicitly in your close and state that any bundle is on
local disk and will not survive the session.

BOUNDARIES (three capx lanes are live and all three sit near capacity evolution): you own the
evolution-LEDGER WRITER -- the adequacy block. You do NOT touch ccs.py's conversion block (:590-591),
arrays.py:3651 or evolve.py's _retrofitted_ids / exempt-set lines (D88's), and you do NOT touch
ccs.py:475-476 or evolve.py:664 (D87's). You do NOT touch
tests/unit/model/test_d62_published_going_forward_bar.py or test_d74_no_default_cap_convention.py or
the D62/D74 mechanism code (D89's). If your diagnosis reaches any of them, STOP and report the
overlap rather than editing across the boundary.

EXIT: docs/handoffs/FINDING-capx-d83-2026-09-08.md leading with (c)'s verdict -- (i) or (ii) -- and
the named line from (b); the repair with its zero-key-move census if (i); the owner card if (ii); the
recurrence test either way. Rule 27 [R-PUSH]: edit locally, push on-disk bytes, blob-verify any file
over 300 lines.
```

---

## D89 — the 27 reds in this desk's own D62 / D74 test files (Opus, code) — RE-EMITTED WHOLE

```
You are the D89 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d89-d62-d74-reds, fresh off origin/main.
Authority: OWNER RULING Q61 (2026-09-08, capx ledger §0be.3(b)) -- "Charter D89 for capx's own 27;
fix none of the other 28."
THIS CHARTER WAS ISSUED AT r#60 AND NEVER DISPATCHED (no branch, no commit, no document, confirmed on
a second fetch). It is RE-EMITTED WHOLE -- start from the top.
ZERO LP EXPECTED. If you conclude a solve is required, STOP and say why before spending one.

WHY YOU EXIST. capx D86, chartered to repair two guards, returned an inventory nobody asked for:
running `tests/unit tests/scoring tests/regression`, 55 tests are RED on main (57 before its repair,
55 after, 0 newly broken). TWENTY-SEVEN of them are in files named for THIS DESK'S OWN LANES:

  tests/unit/model/test_d62_published_going_forward_bar.py   15
  tests/unit/model/test_d74_no_default_cap_convention.py     12

D62 (PJM's published gross ACR as the retirement screen's going-forward bar AND the sell-offer cap)
and D74 (the Manual 18 "NA" no-default-cap price-taker convention) both LANDED at capx r#48, both
built DEFAULT-OFF, and neither has been touched since. D74 additionally carries a SELF-EXECUTING
DO-NOT-ARM -- and the evidence for that refusal is precisely these tests.

THE QUESTION, AND IT IS THE WHOLE LANE. Diagnose BEFORE you repair, and say which of these it is:

  (A) FIXTURE ROT. A later change (D67, D75-R, D76, D78, D84, the D79 solve surface, a registry
      re-derivation, the conftest autouse fixture family) moved something these tests hard-code, and
      the mechanisms themselves are fine. Repair is to the tests, FORWARD -- assert against the live
      source of truth, never re-freeze today's literal, which is exactly the stale-label mistake D86
      repaired in test_cache_solve_surface (see FINDING-capx-d86-2026-09-07.md §2 step 2 for the
      form: assert against the live registry/ledger, and import rather than copy it).

  (B) A REAL BEHAVIOUR CHANGE. D62's or D74's mechanism no longer does what it did at r#48. This is
      the serious answer: D74's DO-NOT-ARM rests on measurements those tests encode, so if the
      behaviour moved, the refusal may rest on a state that no longer exists. STOP at that point,
      write it up, and serve it as an owner card -- do NOT silently update a test to match changed
      behaviour, which would erase the evidence for a standing refusal.

  (C) A MIX. Classify EVERY ONE of the 27 individually. "Mostly A" is not an answer; the ledger's
      standard is ZERO UNCLASSIFIED (capx D85's census is the precedent -- 15 mismatches, all 15
      derived to their recorded literal, zero unknown).

METHOD:
 1. Reproduce the count at your own HEAD first and state the exact command. Numbers drift; D86's 55
    was measured at ad78cc3e. If your count differs, YOUR count is the one you work from, and say so.
    (§0be doctrine: A RED INVENTORY IS ONLY AS WIDE AS THE COMMAND THAT PRODUCED IT -- state yours.)
 2. Classify all 27 into A / B / C-per-test with the failing assertion and its cause named per row.
    A table is the deliverable, one row per test.
 3. Repair only the A rows, forward. For each, say what live source the assertion now reads.
 4. For any B row: STOP the repair for that row, and write the owner card. Report it at full
    magnitude -- what changed, when (bisect to a merge if you can do it cheaply), and what it does to
    D74's DO-NOT-ARM and D62's landed state.
 5. When you are done, re-run the SAME wide command and report the new total. "Fixed N, newly broken
    0" is the form D86 used and it is the form expected here.

BOUNDARIES, all binding:
  - FIX NONE OF THE OTHER 28. They belong to other desks: golden-manifest provenance 7, test_soundness
    end-to-end 6, results/export 4, FF readiness battery 4, forecast parity 2 (MISO's miso-233 arms
    three miso_seam_neighbour_* fields with no forecast_parity_registry declaration), caiso_st_gas_peak
    1 (registry 1.166 vs artifact 1.154), capacity TestGetRPSTarget 1 (SPP now has an RPS floor),
    registration-marker gate 1, gate-(a) 1, backcast artifacts 1. INVENTORY them in your FINDING with
    the owning desk named -- reporting is this lane's job, editing is not. An all-55 sweep was offered
    to the owner and marked NOT RECOMMENDED for exactly this reason (rule 25 [R-ISO-SCOPE], and the
    §0bd cross-desk collision). NOTE: the gate-(a) red has since been repaired by another lane, so
    your count may legitimately be lower -- report what you measure.
  - DO NOT ARM D62 OR D74, or move any default. D74's DO-NOT-ARM stands until an owner says otherwise.
  - THREE OTHER CAPX LANES ARE LIVE AND ALL SIT NEAR CAPACITY EVOLUTION. Do not touch ccs.py,
    evolve.py, data/fleet/arrays.py or the evolution-ledger writer -- D88, D87 and D83 own those
    hunks respectively. If your diagnosis reaches any of them, STOP and report the overlap.
  - DO NOT weaken, skip, xfail or delete a test to make it green. That is forbidden outright
    (CLAUDE.md's PR rules: never skip, disable or quarantine a test to get green). A test you cannot
    repair is a finding, not a deletion.
  - Rule 28 [R-MECH-MATRIX]: if any repair changes what a mechanism DOES rather than what a test
    reads, that is a cell update in all seven shards and probably answer (B) -- see step 4.

EXIT: docs/handoffs/FINDING-capx-d89-2026-09-08.md whose FIRST content is the 27-row classification
table (test · failing assertion · A/B · cause · action), then the before/after wide-command counts,
then the other-desk inventory with owners named. Lead your close with the table and the
"fixed N, newly broken 0" line. ruff check + ruff format clean. Rule 27 [R-PUSH]: both test files are
well over 300 lines -- edit locally, push exact on-disk bytes, blob-verify after every push.
```

---

## r#62 NOTE

Two charters, issued 2026-09-08 at main `1393fdd2`, against ledger §0bg. **D90-RESCORE IS THE ONE TO
RUN FIRST** — it discharges owner ruling **Q63** and replaces a provenance flag on a live registered
verdict with a real number.

* **D90-RESCORE** (Q63) — re-solve NEISO T3 golden 2026–2050 on repaired code and re-score
  `neiso-t3`. Opus, `neiso`. **Phase 0 and G-DRIFT NOW; the solve waits for D88 to merge** — an
  act-STOP, not a session-STOP.
* **D91** — the sixteen cache-key pin tests red on `main`, surfaced by D88 and not repaired there.
  Opus, `code`.

**Collision map.** D90-RESCORE solves and scores; it edits **no** `src/`. D91 edits test pins only.
D88 is in flight on PR #5661 and owns `ccs.py`'s conversion block, `arrays.py:3651` and `evolve.py`'s
exempt-set lines — neither charter touches them. **NEXT FREE LABEL: D92.**

**TWO CORRECTIONS CARRIED INTO BOTH PROMPTS, both from §0bg:**

1. **G-DRIFT form 4 audits CODE drift and CANNOT see DERIVED-INPUT drift** (§3(c)). `data/clean` is
   gitignored and rebuilt per container, so a committed bundle is a valid **byte-level** control only
   if the session's own derived tree reproduces it — a fresh container's does not, by construction. A
   delta in a year the code says is inert is a derived-input signal; a short **same-container**
   control solve settles it, and rule 29(b) earns it.
2. **A gate is written in the units the mechanism's own report uses** (§2(b)). My D88 G6 said "no
   non-gas ledger row moves" when it meant "no non-gas **decision** moves", and failed on a
   re-pricing it was designed to permit.

---

## D90-RESCORE — re-solve and re-score `neiso-t3` on repaired code (Opus, neiso) — RUN THIS FIRST

```
You are the D90-RESCORE lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso. Branch: claude/capx-d90-neiso-t3-rescore, fresh off origin/main.
Authority: OWNER RULING Q63 (2026-09-08, capx ledger §0bg.3(a)) — "Charter the re-score as its own
lane now."

** THE STOP NAMES AN ACT, NOT A SESSION. ** Your PHASE 0 and your G-DRIFT audit START NOW. Only the
SOLVE waits for capx D88 (PR #5661) to merge, because the whole point is to re-solve on repaired
code. If D88 has already merged when you open, proceed straight through. Do not idle: do the entire
zero-LP half, push your PRECOMMIT, then take the solve.

WHY YOU EXIST. capx D88 repaired a fleet-identity defect: a legacy representative retrofitted to CCS
kept its unit_id, and the fleet builder re-minted that id for the next economic gas-CC build in the
zone. The registered `neiso-t3` verdict is scored on a run that carries the defect. Q62 flagged the
verdict and routed the re-score to "the D63/D65-B batch"; that batch CLOSED at capx r#55, so until
now the re-score had no owner. Q63 gave it one: you.

WHAT D88 MEASURED, so you know what you are re-scoring against (its FINDING is
docs/handoffs/FINDING-capx-d88-2026-09-08.md — READ IT FIRST):
  - The collision is a TIMING defect, not a level defect. On NEISO T3 `bau-d65br` 2026-2040 the
    pre-D88 control retires four `gas_cc_ccs` units totalling 955.076 MW in 2040; the repaired arm
    retires the IDENTICAL four at the IDENTICAL MW in 2038 — two years earlier — then a further
    1,115.861 MW in 2040. Cumulative through 2040: 962.7 -> 2,078.6 MW, 2.16x.
  - Mechanism: `retirements.py`'s `idx_of` is last-write-wins and `loss_years` is one shared counter,
    so while the duplicate existed the converted representative and its unabated twin were addressed
    as one unit and the exit clock ran on the wrong dispatch.
  - D88 is STOP-only and DECLINES to claim the repaired path is more accurate. **That claim is what
    your re-score decides, and you must be equally willing to report that it got worse.**

THE ONE THING THAT WOULD MAKE THIS LANE WORTHLESS: scoring a run and reporting only whether the
number improved. Rule 1 [R-STRUCT] governs here exactly as it governs an arm — the repair is in
because duplicate-free identity is structurally correct, and it stays in whatever the re-score says.
Your job is to produce the honest number and to say what moved, not to vindicate D88.

PHASE 0 — ZERO LP, STARTS IMMEDIATELY:
 (a) IDENTIFY THE RUN PRECISELY. `ff-verdicts.json` keys `neiso-t3` to `neiso-2026-2050-t3-golden3-d60`,
     cache key `f04fd06348e1623d` = the `ff-t3-neiso-golden/bau-d60` bundle, colliding from 2032.
     CONFIRM that at your own HEAD and quote what you find; do not carry these ids from this charter.
     Note that D88's flag reached FOUR generated sidecars, all on that cache_epoch, and that
     `neiso-2026-2050-t3-golden3-d65br` is in the colliding set but carries an UNSCORED stamp
     (`run_id: None`) — so it has no verdict to replace. Say which runs you are and are not re-scoring.
 (b) RECONSTRUCT THE RECIPE from the committed bundle's own `run_config.json` and state the key you
     expect the re-solve to realize, BEFORE solving. D88 established ids are not hashed and
     SURFACE_MODULES excludes `data/fleet` and `model/capacity_evolution`, so the key should NOT move:
     this is a SAME-KEY invalidation, which is why D88 wrote a cache-epoch entry rather than a re-key.
     If your predicted key differs from the committed one, STOP and report — that would mean something
     other than D88 moved, and re-scoring under it would confound two changes.
 (c) G-DRIFT, and read this carefully because it is the correction D88 earned. The basis is the
     bundle's RECORDED CACHE KEY, never `git diff <keeper git_sha> HEAD` (dead after the 2026-08-16
     history rewrite). **AND G-DRIFT FORM 4 AUDITS CODE DRIFT ONLY — IT CANNOT SEE DERIVED-INPUT
     DRIFT.** `data/clean` is gitignored and rebuilt per container, so the committed bundle is a valid
     BYTE-LEVEL control only if YOUR container's derived tree reproduces it. D88 found a 2027 delta
     against the committed bundle in a year its own change is provably inert, and attributed it 100 %
     to the container's `data/clean` rebuild. **So: before you attribute anything to D88, establish
     whether your container reproduces the committed bundle at all.** If it does not, a short
     same-container PRE-D88 control solve is what rule 29(b) earns, and it is the control you grade
     against — exactly as D88 did.
 (d) PRE-DECLARE WHAT YOU EXPECT THE RE-SCORE TO DO, per FF-2D leg, with reasons, before solving.
     D88's measurement says retirements roughly double through 2040; say what that should do to each
     scored leg and to the FC-5 corridor years 2035 and 2040 that D77 §8.2 names as the ones actually
     scored. A prediction you get wrong is worth more than no prediction — D87's missed bracket is
     this desk's current best example.

THE SOLVE (after D88 merges): NEISO T3 golden, FULL HORIZON 2026-2050, the committed recipe unchanged
but for D88's repair being present in the code. ONE INDIVISIBLE INVOCATION — the evolution chain
links the years and rule 12 [R-PARALLEL] makes them sequential within a run, so the horizon CANNOT be
sharded by year. Expect the multi-hour class. Do not shorten the horizon to save time: a T3 golden
scored on a truncated span is not the same instrument.

THE RE-SCORE: through the FF-2D rubric, the same scorer the standing verdict used. Report EVERY leg
at full magnitude, both directions, and state plainly whether the corrected trajectory scores better
or worse. Then REPLACE the Q62 provenance flag: `provenance.known_defect` on the `neiso-t3` record
was D88's placeholder for exactly this moment. Remove it and register the new verdict, OR — if for
any reason the re-score cannot complete — leave the flag EXACTLY as it is and say why. Never leave the
board asserting a defect is pending resolution when it has been resolved, and never remove the flag
without a verdict to put in its place.

RULE 31 [R-RETAIN] BINDS ABSOLUTELY, AND THIS LANE IS THE CASE IT WAS WRITTEN FOR. Gitignore the
bundle family the moment it is written; **DO NOT rm ANY solved bundle**, whatever the re-score says.
The ercot-255 incident cost ~50 minutes of re-solves because a lane deleted results it judged
not-promotable and the owner then ruled promote — and a 25-year NEISO T3 is far more expensive than
that was. Your final report MUST ask the promotion question explicitly and state that the bundles are
on local disk and will not survive the session.

BOUNDARIES: you edit NO file under `src/market_sim/`. This is a solve-and-score lane. D88 owns
`ccs.py`'s conversion block, `arrays.py:3651` and `evolve.py`'s exempt-set lines; the concurrent D91
lane owns the cache-key pin tests. If your work reaches any of them, STOP and report the overlap.
Note that 16 cache-key pin tests are RED on `main` (D88 §7) and are D91's, not yours — if they are
still red when you run, say so and move on; do not repair them.

EXIT: docs/handoffs/FINDING-capx-d90-rescore-2026-09-08.md leading with (1) the graded prediction from
phase 0(d), then (2) the per-leg re-score at full magnitude with better/worse stated plainly, then
(3) what happened to the flag. Lead your close with the verdict transition — old verdict, new verdict,
and the single sentence that says whether the repair helped, hurt, or neither. Rule 27 [R-PUSH]:
blob-verify anything over 300 lines.
```

---

## D91 — the sixteen cache-key pin tests red on `main` (Opus, code)

```
You are the D91 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d91-cache-key-pins, fresh off origin/main.
Authority: capx ledger §0bg.4. ZERO LP EXPECTED — if you conclude a solve is required, STOP and say
why before spending one.

WHY YOU EXIST. capx D88, working on something else entirely, measured `main` both ways after rebasing
onto `origin/main` 5e3b6c6a: clean `main` is 18 failed / 3,381 passed; its own branch is 18 failed /
3,389 passed — identical failing set, the +8 being exactly D88's new tests. **SIXTEEN of the eighteen
are CACHE-KEY PIN tests** — `test_default_cache_key_is_unmoved`, `…_is_byte_stable`,
`…_unmoved_and_armed_distinct` and kin — across fourteen files: test_capacity.py, test_scarcity.py,
test_storage_entry_gates.py, test_smr_available_year.py, test_entry_vre_zone_selection.py,
test_vre_procurement_ffr5e.py, test_capacity_screen_scarcity_restoration.py,
test_storage_whole_class_accreditation.py, test_ercot219_option_b.py, test_caiso_nqc_class_factors.py,
test_cc_committed_offer_margin.py, test_miso_intermediate_gas_offer_margin.py,
test_ramp_envelope_basis.py, and TWO inside test_ccs_retrofit.py itself. D88 verified those last two
failing on clean `main` with its own edits checked out, i.e. they are not D88's. Its conclusion, which
it surfaced rather than repaired: **"Something landed on main that moved the default cache key without
re-pinning it."**

This is THIS DESK'S OWN discipline. The cache key is the address a bundle has; capx D24 (Q20, the
(b′-1) drop-at-frozen-declaration construction), D79/Q54 (the solve-surface fingerprint) and D85/D85-R
(the key-provenance census and its standing gate) all exist to make key movement legible. Sixteen
silent pins is that discipline failing quietly.

THE QUESTION, AND IT IS THE WHOLE LANE. Diagnose BEFORE you repair, and say which of these it is:

  (A) A LEGITIMATE RE-KEY WHOSE PINS WERE NOT ADVANCED. Some lane armed a field, moved a default, or
      re-derived a registry table the D79 surface sees, the key moved BY DESIGN, and the pins simply
      were not updated in the same PR. Repair is to advance the pins, with the CAUSE named per pin —
      never a blanket re-pin. A re-pin with no named cause is an answer key.

  (B) AN ACCIDENTAL KEY MOVE. Something changed the default `ScenarioConfig` key that was not supposed
      to. **This is the expensive direction**: every committed bundle solved before it is addressed at
      a key nothing now computes, which is the D24 §4.2 collision class D85 spent two lanes proving
      unreachable. STOP at that point, write it up, and serve it as an OWNER CARD — do not "fix" it by
      re-pinning, which would bless the accident and erase the evidence.

  (C) A MIX. Classify EVERY ONE of the sixteen individually. "Mostly A" is not an answer; this
      ledger's standard is ZERO UNCLASSIFIED (capx D85's census — 15 mismatches, all 15 derived to
      their recorded literal, zero unknown — is the precedent).

METHOD:
 1. Reproduce the count at your own HEAD and STATE THE EXACT COMMAND. D88 measured 18/16 at
    origin/main 5e3b6c6a; numbers drift and your count is the one you work from. (§0be doctrine: A RED
    INVENTORY IS ONLY AS WIDE AS THE COMMAND THAT PRODUCED IT — state yours.)
 2. FIND WHAT MOVED THE KEY. Bisect over the merges between the last commit where the pins passed and
    your HEAD if that is cheap; otherwise reason from the payload. The instruments already exist and
    you should use them rather than building new ones: `scripts/check_key_provenance.py` and
    `scripts/lib/key_provenance.py` (D85-R's standing tooling), the `_CACHE_KEY_OPTIONAL_FIELDS` /
    `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` / `_CACHE_KEY_RETIRED_FIELDS` declarations in
    scenarios.py, and `config/solve_surface_declared.py` with `tests/regression/test_persisted_identity.py`'s
    LEDGERED_SURFACE_MOVES_BY_ISO. **NAME THE COMMIT AND THE FIELD.** A diagnosis that says "some
    default moved" is not a diagnosis.
 3. Classify all sixteen into A / B per pin, with the failing assertion, the old and new key, and the
    named cause per row. A table is the deliverable, one row per pin.
 4. Repair only the (A) rows, each with its cause named IN the pin's own comment so the next reader
    knows why the literal changed. For any (B) row: STOP that row and write the owner card, reporting
    at full magnitude what moved, when, and which committed bundles are addressed at the old key.
 5. Re-run the same wide command and report the new total in the form "fixed N, newly broken 0".
 6. ANSWER THE GATE QUESTION: `scripts/check_key_provenance.py` is EXIT 0 at HEAD (I ran it this
    sitting). Say why it is green while sixteen pins are red — the two instruments answer different
    questions and the difference is worth stating precisely, because if the standing gate CAN be green
    through a real key defect, that is a finding about the gate and belongs in your FINDING.

BOUNDARIES:
  - DO NOT arm, disarm, or move any default, and do not touch `config/solve_surface_declared.py`
    (APPEND-ONLY, rule 26 [R-DELETE]; re-declaring a moved row restores the pre-change key and
    re-serves the pre-change bundle).
  - DO NOT rewrite any committed `cache_key`. If a key rewrite is ever the right repair, that is an
    owner card, not a lane's act — D85 and D85-R both refused it and they were right.
  - DO NOT weaken, skip, xfail or delete a pin to make it green (CLAUDE.md's PR rules forbid it
    outright). A pin you cannot repair is a finding.
  - TWO OTHER CAPX LANES ARE LIVE: D88 (PR #5661) owns `ccs.py`'s conversion block, `arrays.py:3651`
    and `evolve.py`'s exempt-set lines; D90-RESCORE is solving NEISO T3 and edits no `src/`. Note that
    two of your sixteen pins sit inside `test_ccs_retrofit.py`, which D88 also touches — coordinate by
    rebasing onto D88 once it merges, and if your repair would conflict with its edits, STOP and
    report rather than resolving across the boundary.
  - The other TWO of D88's eighteen failures are not cache-key pins. Inventory them with their likely
    owner named; do not repair them.

EXIT: docs/handoffs/FINDING-capx-d91-2026-09-08.md whose FIRST content is the sixteen-row
classification table (pin · file · old key · new key · A/B · named cause · action), then the
before/after wide-command counts, then §6's answer about the standing gate. Lead your close with the
table and the named commit-and-field that moved the key. ruff check + ruff format clean. Rule 27
[R-PUSH]: blob-verify anything over 300 lines.
```

---

## r#63 NOTE

Two charters, issued 2026-09-09 at main `ad197380`, against ledger §0bh. **D91 IS THE ONE TO RUN
FIRST** — it discharges owner ruling **Q64** and its object is the program's whole cache addressing.

* **D91** (Q64) — the unregistered field, the other 95 payloads, and why this desk's own standing
  gate is green through all of it. **RE-EMITTED WHOLE** (never dispatched at r#62) and sharpened with
  D90's attribution. Opus, `code`.
* **D90-R** — complete the `neiso-t3` re-score from D90's own pushed pre-registration. **COMPLETE,
  never REDO.** Opus, `neiso`.

**Collision map: NONE, and that is a ruling, not an oversight** (§0bh.3(b)). D91 owns the
`_CACHE_KEY_OPTIONAL_FIELDS` declarations and the pin tests; D90-R solves and scores and edits **no**
`src/`. They may run concurrently in either order. If D91 lands first, D90-R's arm realizes
`f04fd06348e1623d` instead of `ae317e63263c8eef` — **a better address, not a different score**,
because the field is PJM-scoped, holds `False` and is behaviourally inert for a NEISO forecast solve.
**NEXT FREE LABEL: D92.**

---

## D91 — the unregistered field, the other 95, and the gate that did not fire (Opus, code) — RUN THIS FIRST

```
You are the D91 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d91-cache-key-pins, fresh off origin/main.
Authority: OWNER RULING Q64 (2026-09-09, capx ledger §0bh.3(a)) — "Re-emit D91 to diagnose fully,
then repair."
THIS CHARTER WAS ISSUED AT r#62 AND NEVER DISPATCHED. It is RE-EMITTED WHOLE — start from the top —
and it is SHARPER than the original, because another lane has since handed you the attribution.
ZERO LP. If you conclude a solve is required, STOP and say why before spending one.

WHAT IS ALREADY KNOWN, AND IT IS YOUR STARTING POINT, NOT YOUR CONCLUSION.
capx D90, auditing its own inputs before spending an LP, measured at HEAD:

  ScenarioConfig().cache_key()          72341e34fd261997
  _PINNED_DEFAULT_KEY (tests/unit/model) 547053bdfccd4264
  committed run payloads reproducing their own recorded key:  0 of 173

and attributed it BY EXPERIMENT — registering `pjm_seam_neighbour_hourly_ladder` in
`_CACHE_KEY_OPTIONAL_FIELDS` at a frozen "False", IN MEMORY ONLY with no file edited:

  committed payloads reproducing:        0/173  ->  78/173
  bau-d60  (D90's target)   ae317e63263c8eef  ->  f04fd06348e1623d
  bau-d65br (D88's control) 4a5f9695eeae815a  ->  0fc42cb56c24d544   <- D88's OWN reported key

The field was added by `f2a834de` (PJM hourly neighbour-anchored seam ladder) with NO registration
entry, so it always enters the hash and moves every key in the program. D90's write-up is
`docs/handoffs/PRECOMMIT-capx-d90-rescore-2026-09-09.md` §3.1 — READ IT FIRST, and re-derive rather
than inherit: if your HEAD disagrees with any number above, YOUR HEAD IS RIGHT and you say so.

THREE QUESTIONS, AND THE LANE IS NOT DONE UNTIL ALL THREE ARE ANSWERED.

 (1) THE OTHER 95. Registering that one field restores 78 of 173. **What accounts for the remaining
     95?** This is the half nobody has looked at and it is where a second key move would come from if
     the repair were taken on the partial answer — which is exactly why Q64 refused the hotfix-first
     option. Classify EVERY non-reproducing payload with its cause named. "Mostly the one field" is
     not an answer; this ledger's standard is ZERO UNCLASSIFIED (capx D85's census — 15 mismatches,
     all 15 derived to their recorded literal, zero unknown — is the precedent, and D85-R's
     `scripts/lib/key_provenance.py` is the instrument, already standing tooling).

 (2) WHY IS THE GATE GREEN? `scripts/check_key_provenance.py` is **EXIT 0** at this HEAD, reporting
     *"ok: every mismatch is a known, cited, recipe-verified exception"*, while 173 of 173 payloads do
     not reproduce. That gate is THIS DESK'S OWN — D85-R's deliverable — and its stated first duty is
     **G1_UNKNOWN: a committed record does not reproduce and is not listed**. It did not fire.
     Candidates worth ruling in or out BY READING, not guessing: the census reads
     `key_at_declaration` as well as `key_live_surface` and a row reproduces if EITHER matches
     (D85-R repair 4) — does the at-declaration construction insulate it? Does the census enumerate a
     different population than D90's 173? Is the exception list absorbing them? **NAME THE REASON.**
     Then say whether the gate needs repair, and if so what would have made it red — but do NOT
     weaken it, and do NOT add these to the exception record: an exception record is for records
     whose non-reproduction is UNDERSTOOD AND CITED, never a place to park a live defect (D85-R's own
     `what_this_is_not` block says so in the artifact).

 (3) THE REPAIR, and only after (1) and (2). The presumptive route is the (b′-1) construction — owner
     ruling Q20, capx D24 — registering the field in `_CACHE_KEY_OPTIONAL_FIELDS` at a frozen "False"
     so a default-off field stops entering the hash. It is PRESUMPTIVE, NOT PRE-COMMITTED: if (1)
     shows the other 95 need something else, say so.
     ** BEFORE YOU REGISTER ANYTHING, COUNT THE ORPHANS. ** Registering RESTORES pre-field keys rather
     than moving them somewhere new — but any bundle solved SINCE `f2a834de` at the default currently
     sits at the field-present key, and registration makes those interim bundles unaddressable.
     NOBODY HAS COUNTED THEM. Enumerate them, name them, and state the cost in your PRECOMMIT before
     the edit. If the count is large enough to change the recommendation, STOP and serve it as an
     owner card rather than deciding it yourself.

METHOD:
 1. Reproduce D90's numbers at your own HEAD and STATE THE EXACT COMMAND (§0be doctrine: A RED
    INVENTORY IS ONLY AS WIDE AS THE COMMAND THAT PRODUCED IT). Also re-measure the pin tests — D88
    counted 16 red at origin/main 5e3b6c6a across fourteen files; report what YOU see.
 2. Answer (1), (2), (3) in that order, in a PRECOMMIT pushed BEFORE any edit.
 3. Repair, then re-run both instruments and report "fixed N, newly broken 0" in D86's form.

BOUNDARIES:
  - DO NOT touch `config/solve_surface_declared.py` — APPEND-ONLY (rule 26 [R-DELETE]); re-declaring a
    moved row restores the pre-change key and re-serves the pre-change bundle.
  - DO NOT rewrite any committed `cache_key`. If a key rewrite is ever the right repair that is an
    owner card, not a lane's act — D85 and D85-R both refused it and were right.
  - DO NOT arm, disarm or move any default. `pjm_seam_neighbour_hourly_ladder` stays `False`; you are
    registering it, not changing it.
  - DO NOT weaken, skip, xfail or delete a pin to make it green (CLAUDE.md's PR rules forbid it
    outright). A pin you cannot repair is a finding. Each pin you DO advance carries its cause named
    in its own comment — a re-pin with no named cause is an answer key.
  - `check_mechanism_matrix.py` is EXIT 1 on `main` — the shared field
    `vre_curtailment_oversupply_allocation` is in neither the matrix nor the `absent_shared` ratchet.
    That is another desk's rule-28(c) miss (the SPP curtailment-allocation lane) and is NOT yours:
    name it in your FINDING and route it, do not repair it.
  - The concurrent D90-R lane solves and scores and edits no `src/`. Your repair would give its arm a
    better address, not a different score — no coordination is needed, and none is owed.

EXIT: docs/handoffs/FINDING-capx-d91-2026-09-09.md whose FIRST content is the classification table for
all 173 (payload · recorded key · recomputed key · cause · action), then the gate answer to (2), then
the orphan count from (3), then before/after counts. Lead your close with the named field and commit,
the 173-row disposition, and one sentence on why the gate was green. ruff check + ruff format clean.
Rule 27 [R-PUSH]: `scenarios.py` is far over 300 lines — edit locally, push exact on-disk bytes,
blob-verify after every push.
```

---

## D90-R — complete the `neiso-t3` re-score (Opus, neiso)

```
You are the D90-R lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso. Branch: claude/capx-d90r-neiso-t3-rescore, fresh off origin/main.
Authority: OWNER RULING Q63 (2026-09-08, capx ledger §0bg.3(a)). Predecessor: capx D90, which pushed
its full pre-registration and then stopped without solving.

** YOU COMPLETE D90. YOU DO NOT REDO IT. ** Everything below already exists on `main` and is YOURS to
inherit, not to re-derive:

  docs/handoffs/PRECOMMIT-capx-d90-rescore-2026-09-09.md   (+ ADDENDUM A and ADDENDUM B)

READ IT END TO END BEFORE ANYTHING ELSE. It spent ZERO LP and lost almost nothing, because it pushed
everything it established. What you inherit, and must NOT re-litigate:

  - §1  the run identified: ff-verdicts key `neiso-t3` -> run_id `neiso-2026-2050-t3-golden3-d60`,
        cache_epoch `f04fd06348e1623d`, determination HOLD, `provenance.known_defect` PRESENT.
        EXACTLY ONE committed record carries that flag (D88's "four sidecars" is about the GENERATED,
        gitignored registry namespace — a different surface).
  - §4/A.1  the pre-solve STOP PASSES: the pinned CLI recipe vs the committed config.yaml is ZERO
        field diffs, and the pinned+resolved key equals the committed recipe key f04fd06348e1623d.
        **The arm IS the scored recipe.**
  - A.2  THE SCORER IS VALIDATED. `forecast_verdict.py --tier t3` over the committed artifacts
        reproduces the committed forecast_verdict.json EXACTLY — every category, row, status and
        detail string, only `provenance` differing. Your re-score is therefore a CONTROLLED SWAP:
        the arm's summary and run_config replace d60's, every carried input held byte-identical, so
        any verdict movement is attributable to the solve alone.
  - A.2  FC-6 IS CARRIED FROM d46 AND WAS NEVER MEASURED ON d60's OWN SOLVE. Carry it identically, as
        D90 declared, so it cannot move spuriously — and repeat D90's disclosure in your FINDING:
        **no FC-6 reading here is evidence about D88.** Re-measuring it is another lane's work.
  - A.3  P6's bracket was mis-anchored to bau-d46's pair; bau-d60's own co2@2040 is 8.559 Mt. Grade
        P6 against the CORRECTED anchor, and say that the correction was pre-solve.
  - B    the FC-7 four-clause handling rule. FOLLOW IT LITERALLY. Clause 1 is the headline; clause 2's
        secondary reading is admissible ONLY for the two named restoration pins; clause 3 says any
        OTHER FC-7 movement is REAL and reported as a real FAIL; clause 4 forbids editing the
        DOF-ledger instrument to make it go away. And P9 is PRE-GRADED a likely MISS — grade it that
        way if the as-generated ledger carries an UNIDENTIFIED entry, do not rescue it.

WHAT IS YOURS: the solve, the re-score, the graded predictions, and the flag.

THE KEY SITUATION — RE-READ IT AT YOUR OWN HEAD, DO NOT INHERIT §3.1. D90 recorded that at its HEAD
`pjm_seam_neighbour_hourly_ladder` was unregistered, so 0 of 173 payloads reproduced their key and the
arm would land in a directory other than the scored one. The concurrent D91 lane is chartered to
repair exactly that. Re-measure at YOUR head and record what you find:
  - if the field is still unregistered, proceed exactly as D90 planned — the arm writes to its own
    `--out-dir` so it can neither cache-hit nor clobber the stale bundle, and the field is PJM-scoped,
    holds False and is BEHAVIOURALLY INERT for a NEISO forecast solve (D90 §3.1, verified);
  - if D91 has landed, your arm will realize `f04fd06348e1623d` — the scored key — which is a BETTER
    ADDRESS, not a different score. Say so and carry on.
**Either way the score is unaffected**, which is why the capx director ruled these two lanes
INDEPENDENT (§0bh.3(b)) and why you must not wait on D91.

THE SOLVE: NEISO T3 golden, FULL HORIZON 2026-2050, the committed recipe unchanged but for D88's
repair being present in the code (verified in-tree at ccs.py:702 and arrays.py:3314). ONE INDIVISIBLE
INVOCATION — the evolution chain links the years and rule 12 [R-PARALLEL] makes them sequential within
a run, so the horizon CANNOT be sharded by year. Expect the multi-hour class. Do not shorten it: a T3
golden scored on a truncated span is not the same instrument.

THE RE-SCORE: through the FF-2D rubric, the same scorer A.2 validated. Report EVERY leg at full
magnitude, both directions, and state plainly whether the corrected trajectory scores better or worse.
Rule 1 [R-STRUCT] governs exactly as it governs an arm: **the D88 repair is in because duplicate-free
fleet identity is structurally correct, and it stays in whatever this re-score says.** You produce the
honest number; you do not vindicate D88. Grade every one of D90's §5 predictions, hits and misses
alike — D87's missed bracket is this desk's current best example of a miss being the result.

THE FLAG: `provenance.known_defect` on the `neiso-t3` record was D88's placeholder for exactly this
moment. Remove it and register the new verdict — OR, if the re-score cannot complete, leave it EXACTLY
as it is and say why. Never leave the board asserting a defect is pending when it is resolved, and
never remove the flag without a verdict to put in its place.

RULE 31 [R-RETAIN] BINDS ABSOLUTELY AND THIS LANE IS THE CASE IT WAS WRITTEN FOR. Gitignore the bundle
family the moment it is written; **DO NOT rm ANY solved bundle**, whatever the re-score says. A 25-year
NEISO T3 is far more expensive than the ercot-255 incident that produced the rule. Your final report
MUST ask the promotion question explicitly and state that the bundles are on local disk and will not
survive the session. **And push your own addenda as you go, the way D90 did — that discipline is why
you inherited a validated scorer instead of a blank page.**

BOUNDARIES: you edit NO file under `src/market_sim/`. D91 owns the `_CACHE_KEY_OPTIONAL_FIELDS`
declarations and the pin tests. `check_mechanism_matrix.py` is EXIT 1 on `main` over another desk's
`vre_curtailment_oversupply_allocation` — not yours; note it and move on.

EXIT: docs/handoffs/FINDING-capx-d90r-2026-09-09.md leading with (1) every D90 prediction graded, hits
and misses named, then (2) the per-leg re-score at full magnitude with better/worse stated plainly,
then (3) what happened to the flag. Lead your close with the verdict transition — old verdict, new
verdict, and the single sentence that says whether the repair helped, hurt, or neither. Rule 27
[R-PUSH]: blob-verify anything over 300 lines.
```

---

## r#64 NOTE

Two charters, issued 2026-09-10 at main `5fa3a07f`, against ledger §0bi. **D92 IS THE ONE TO RUN
FIRST** — it discharges owner ruling **Q65** and repairs a number the board is publishing that a
landed repair has already halved.

* **D92** (Q65) — capx D77's named CO2 residue, plus this desk's own G1_UNKNOWN. Opus, `neiso`.
* **GATE-(a) RE-KEY** (Q34) — **four ISOs at once**, the eighteenth firing and the first quadruple.
  Fable, `code`.

**Collision map.** D92 solves, scores and registers under `frontend/data/forecast/`; the re-key
touches `frontend/data/forecast/program-status.json` alone. Disjoint. **NEXT FREE LABEL: D93.**

**CARRIED INTO BOTH PROMPTS, from §0bi:**
1. **A lane that DEFERS work names a LIVE owner or states that none exists.** Three capx documents —
   D77, D88, and my own r#61 charter — deferred to "the D65-B batch", which closed at r#55. That is
   why D92 exists at all.
2. **G-DRIFT form 4 on a recorded-key basis audits CONFIG drift ONLY.** It sees neither
   derived-input drift (D88's lesson) nor non-config code drift (D90-R's). Against an old bundle the
   control solve is not the fallback — it is the only instrument that isolates anything, and its cost
   should be assumed.

---

## D92 — capx D77's named CO2 residue, and capx's own G1_UNKNOWN (Opus, neiso) — RUN THIS FIRST

```
You are the D92 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso. Branch: claude/capx-d92-d77-co2-residue, fresh off origin/main.
Authority: OWNER RULING Q65 (2026-09-10, capx ledger §0bi.3(a)) — "Charter D77's named residue only."

WHY YOU EXIST. capx D90-R re-scored `neiso-t3` on D88-repaired code and found the flagged defect was
SCORING-INERT (HOLD -> HOLD, D88 moves zero of 19 scored rows) — but that a DIFFERENT repair, capx
D77, moves the same run far more, with an attribution exact to four decimals against D77's own
published A/B:

    year   D77 published A/B          D90-R's d60 -> pre-D88 control
    2028   15.8562 -> 12.9276 (-18.5%)  15.856 -> 12.928
    2029   14.0210 ->  6.7954 (-51.5%)  14.021 ->  6.795
    2030   13.3680 ->  6.9545 (-48.0%)  13.368 ->  6.955

D77 repaired the CCS emission-rate seam (`campd_bins.apply_plant_emission_rates_v2` re-booked a
converted unit's UNCAPTURED host rate over its captured one in every forecast year). Its own record
named the consequence precisely — "the three NEISO T3 verdicts' co2@2030/2035/2040 FC-5 rows and
their FC-6 paired-P1 cumulative-CO2 row are the only SCORED cells mis-stated" — and DEFERRED the
re-solve to "the D65-B batch". **That batch closed at capx r#55.** D90-R closed the measurement half
on `neiso-t3` and re-registered it. **The rest of D77's named residue is still stale and still has no
owner. You are the owner.**

READ FIRST, in this order: docs/handoffs/FINDING-capx-d90-rescore-2026-09-09.md (esp. §5.1, the
attribution) · docs/handoffs/FINDING-capx-d90r-2026-09-09.md · D77's own finding · and
PRECOMMIT-capx-d90-rescore-2026-09-09.md with its Addenda A/B, which carry a VALIDATED SCORER and a
pre-registered FC-7 handling rule you should reuse rather than reinvent.

PART 1 — SCOPE IT BEFORE YOU SOLVE, AND THE SCOPE IS D77's LIST, NOT YOUR JUDGEMENT.
 (a) Enumerate, from the committed record at YOUR head, exactly which verdicts carry D77's named
     mis-stated cells and which of them D90-R already closed. D77 said "the three NEISO T3 verdicts";
     `neiso-t3` is done. NAME the remainder — run ids, cache epochs, bundles — and say for each
     whether its bundle predates D77's merge. Quote what you find; do not carry ids from this prompt.
 (b) ** STOP GATE. If a verdict's bundle POSTDATES D77, it is not stale for this reason and it is NOT
     in scope. ** Say so and drop it. Scope creep here is how a bounded lane becomes a board sweep,
     which the owner explicitly declined this window.
 (c) Pre-declare, per verdict, what you expect the re-solve to do to the named cells — direction and
     rough magnitude — BEFORE solving. D90-R graded 5 hits / 3 misses / 3 partial and declined one of
     its own hits as "a hit on a technicality"; that is the standard. A prediction you can only grade
     charitably is not a prediction.

PART 2 — THE G1_UNKNOWN, AND IT IS THIS DESK'S OWN. `scripts/check_key_provenance.py` is EXIT 1 at
HEAD with:

    [G1_UNKNOWN] results/ff-t3-neiso-golden/d90-rescore/run_config.json
        a committed record does not reproduce and is not in key-provenance-exceptions.json.
        This is a SIXTEENTH: stop and report it as a new finding, do not append it here.

That bundle is D90-R's own registration — capx's residue, not another desk's. Diagnose it BEFORE you
solve anything, because it may tell you something about how your own arm will register. Two
directions, and say which: (i) the record genuinely does not reproduce and the cause is nameable — in
which case repair the CAUSE, and note that D91 has just registered `pjm_seam_neighbour_hourly_ladder`,
so a bundle solved either side of that lands differently; or (ii) it is a listing gap on a record
whose non-reproduction IS understood. **Do NOT append it to key-provenance-exceptions.json to make
the gate green** — that record's own `what_this_is_not` block forbids parking a live defect there,
and the gate message says so explicitly. If you cannot resolve it, leave it red and report it.

PART 3 — THE SOLVE. Each leg is NEISO T3 golden, FULL HORIZON 2026-2050, one INDIVISIBLE invocation
(the evolution chain links the years; rule 12 [R-PARALLEL] makes them sequential within a run, so the
horizon CANNOT be sharded). D90-R measured **31.1 minutes** of wall clock for one leg, so this is
cheap by this program's standards — but rule 12 also says separate invocations run CONCURRENTLY, so
if you have more than one leg, launch them in parallel with separate `--out-dir`s.

G-DRIFT — and read this, because it is the third correction in the series and it is why your control
matters. Form 4 on a recorded-key basis audits **CONFIG drift ONLY**. It sees neither DERIVED-INPUT
drift (D88's §3: `data/clean` is gitignored and rebuilt per container, so a committed bundle is a
valid byte-level control only if YOUR container reproduces it) nor **NON-CONFIG CODE drift** (D90-R's
§5.1: D77 is exactly that, and form 4 was blind to it). Against a bundle weeks old **the control
solve is not the fallback, it is the only instrument that isolates anything — assume its cost.**
D90-R's practice is the template: a same-container pre-repair control, and every gate graded against
THAT, not against the committed bundle.

PART 4 — THE RE-SCORE AND THE BOARD. Score through the FF-2D rubric. Reuse D90-R's Addendum A.2
validation practice: re-run the scorer over the COMMITTED artifacts first and confirm it reproduces
the standing verdict exactly, so your re-score is a CONTROLLED SWAP and any movement is attributable
to the solve alone. Follow Addendum B's FC-7 four-clause handling rule literally if FC-7 moves.
Report every leg at full magnitude, both directions, and state plainly whether each verdict's scores
move — remembering D90-R's own lesson: **the scores can be sound while the numbers are stale**, and
your object here is the NUMBERS.

RULE 31 [R-RETAIN]: gitignore each bundle family the moment it is written; **DO NOT rm ANY solved
bundle**, whatever you conclude. Ask the promotion question explicitly in your close and state that
the bundles are on local disk and will not survive the session. **Push your PRECOMMIT and any addenda
as you go** — D90 stopped mid-lane and lost almost nothing because it had pushed everything; that is
the discipline, not an accident.

** AND THE RULE THIS LANE EXISTS TO ENFORCE: IF YOU DEFER ANYTHING, NAME A LIVE OWNER OR SAY THERE IS
NONE. ** Three capx documents — D77, D88 and a director charter — deferred work to "the D65-B batch"
after it had closed, and this lane is the cost of that. "Routed to a later batch" is not a
disposition. Name a lane, a desk, or nobody.

BOUNDARIES: you edit NO `src/market_sim/` file — this is a solve, score and register lane. The
concurrent gate-(a) re-key touches `program-status.json` alone. Other reds on `main` are NOT yours
and must be named-and-left in your FINDING: four dead ERCOT bundle dirs failing the parity gate
(`ercot262_arm_2024/2025`, `ercot264_repro_2023/2025`, the ERCOT lane's, rule 29(c)); the SPP matrix
shard missing two cells; `status/SPP.js` stale; the CAISO marker asserting CALIBRATED on a NOT-YET
keeper; and `caiso_dsw_lateevening_clean` unregistered (D91's new G6 gate caught it — the CAISO
lane's).

EXIT: docs/handoffs/FINDING-capx-d92-2026-09-10.md leading with (1) the scope table from Part 1(a)
with in/out and why, (2) the G1_UNKNOWN disposition, (3) every pre-declared prediction graded, hits
and misses named, then (4) the per-verdict re-score at full magnitude. Lead your close with the
verdict transitions and one sentence per verdict on whether its NUMBERS moved and whether its SCORES
did. Rule 27 [R-PUSH]: blob-verify anything over 300 lines.
```

---

## GATE-(a) RE-KEY — four ISOs at once (Fable, code, zero LP)

```
You are the capx gate-(a) re-key lane for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. Branch: claude/capx-gate-a-rekey-r64, fresh off origin/main.
ONE ACT, ZERO LP. No solve, no scoring, no registration, no keeper edit, no marker edit, no
determination re-computation, no other desk's file.

WHY. `scripts/check_gate_a_provenance.py` is EXIT 1 at main 5fa3a07f on FOUR ISOs at once — the
eighteenth firing of this standing duty and the FIRST QUADRUPLE. The window that produced it was 573
commits and **every one of the seven ISOs promoted a keeper**. As read at 5fa3a07f:

  CAISO: row cites 2026-09-06-caiso-260-b1-demand   -> live 2026-09-10-caiso-269-lateevening-clean
  ERCOT: row cites 2026-09-08-ercot256-drag-layup-mask -> live 2026-09-09-ercot265-receipts-fallback
  MISO:  row cites 2026-09-09-miso-248-spp-ladder   -> live 2026-09-09-miso-250-ep-gas
  SPP:   row cites 2026-09-09-spp-52a-fossil-offer  -> live 2026-09-10-spp-61-vintage

** DO NOT TRUST ANY OF THOSE IDS. ** They are this desk's reading at one instant, and in this repo a
row has gone stale inside the session that wrote it. Read EVERY fact LIVE at your own HEAD from the
backcast store. If your HEAD disagrees, YOUR HEAD IS RIGHT: re-key to it and say so. Note that MISO's
row is already stale against a keeper that ITSELF superseded another within this window — state the
full chain of promotions each row was stale across, not a single arrow. (My r#60 charter described
ERCOT's case as one transition when it was two; the lane caught it. Do not let me do that to you.)

METHOD — the method is the deliverable, because a bad edit here is worse than a stale row.
 1. Read the live facts for EACH of the four ISOs, and cite where each came from:
      - designated keeper id: frontend/data/backcast/keepers/<ISO>.json
      - marker state: BOTH blocks of frontend/data/backcast/calibration-complete.json (complete /
        final), reported True/False. `final` is EMPTY for every ISO, so no locked-test claim may
        appear in any row.
      - determination and per-year verdicts: the committed status sidecar
        frontend/data/backcast/status/<ISO>.js — NOT a re-score. This lane computes no verdict.
        NOTE: `audit_keepers` reports status/SPP.js is STALE. If SPP's sidecar disagrees with the
        current verdicts, do NOT rebuild it (that is the SPP desk's) and do NOT copy a number you
        believe is stale — record what the sidecar says, mark it as reported-stale, and say so.
      - the promotion instrument, named as a DOCUMENT and not merely a PR number.
 2. TARGETED STRING EDIT of each row's three leaves only — the `detail` head, `read_live_at`, and the
    `gate_a_provenance` block — scoped by string position.
    ** NEVER a json.dumps round-trip. ** program-status.json is a hand-maintained COMMITTED seed that
    build_program_status wraps VERBATIM; reserialization silently reformats every other desk's row.
 3. PRESERVE THE PRIOR TEXT. Anything not one of those three leaves stays byte-identical; where a row
    already carries a RE-KEYED provenance sentence, add yours beside it — the row is a chain.
 4. Touch ONLY those four rows. Do not fix another ISO's row even if you think it is stale; report it.

** CAISO CARRIES TWO SEPARATE DEFECTS. REPORT BOTH; REPAIR NEITHER. ** `audit_keepers --check` is
EXIT 1 and two of its three failures are CAISO's:
  - M1b: calibration-complete.json `complete.CAISO.determination` asserts **CALIBRATED** while the
    live verdict of the keeper it names is **NOT-YET**. Rule 22's owner decision D-5(b) says a
    re-verified determination that is WORSE stops the promotion and escalates to the owner and is
    never silently written. It was written.
  - E1: that keeper's bundle dir `results/calibration/caiso269_lateevening_span` is MISSING.
Gate (a) compares IDENTITY ONLY and asserts nothing about determinations, so re-keying CAISO's row to
the live keeper id is correct AND ORTHOGONAL to both defects — do it. But the row also states marker
state, so: state the marker EXACTLY as `calibration-complete.json` currently holds it, add one clause
recording that the marker's asserted determination is under query with the audit board, and DO NOT
alter the marker, the determination, or anything under `results/calibration/`. Those belong to the
CAISO lane and the audit board. Say all of this plainly in your record.

STOP GATES:
  - If the gate is ALREADY EXIT 0 for an ISO at your HEAD, its re-key landed while you were
    chartered. DO NOT re-key it — asserting a supersession that did not happen is a false record.
  - If re-keying would require changing a determination, a marker, a leg status or a grade: STOP.
    That is a different lane and an owner-tier question.

EXIT: check_gate_a_provenance.py EXIT 0 on all seven rows; audit_keepers --check no WORSE than you
found it (it will still be EXIT 1 on the CAISO and SPP items, which are not yours — say so); the diff
touches exactly four rows of one file; and a short record carrying, per ISO, the before/after `detail`
head VERBATIM, the full promotion chain the row was stale across, and the promotion instrument as a
document. Lead your close with the gate's exit code and the four id transitions. Rule 27 [R-PUSH]:
push exact on-disk bytes and verify the pushed blob.
```

---

## r#65 NOTE

Three charters, issued 2026-09-24 at main `40f4ed7a` against ledger §0bj. The desk launched all three
itself (owner's standing preference). Each prompt below was sent verbatim, and each session is
pinned to the director commit that carries this pack.

* **GATE-(a) RE-KEY r#65** (Q34): six ISOs, plus SPP's marker claim. Fable, `code`.
* **D93** (Q66): the key-provenance lag class rule, plus the G6 registration of
  `coal_mustrun_requires_measured_row`. Opus, `code`.
* **D94** (Q67): `neiso-t3`'s FC-6 driver battery re-measured on the post-D77 basis. Opus, `neiso`.

**Collision map.** The three touch disjoint files: `program-status.json` / `check_key_provenance.py` +
`scenarios.py` + tests / `results/ff-t3-neiso-golden/d94/` + `ff-verdicts.json`.
D94's payloads interact with D93's registration, and its charter handles that. **NEXT FREE LABEL: D95.**

**Rules that changed since the r#64 charters and bind all three:** rule 29 `[R-SCREEN]`'s screen
regime is REMOVED (clauses (b)/(c) survive); rules 32–35 (`[R-SHARD]`, `[R-SHARD-ARCHIVE]` incl.
(f) "a shard branch is transport, not storage", `[R-SHARD-PROMOTABLE]`, `[R-PROMOTE]`); rule 36
`[R-YEAR-ISOLATION]` binds BACKCASTS only and leaves a forecast horizon one indivisible invocation.

---

## GATE-(a) RE-KEY r#65 — six ISOs and SPP's marker (Fable, code, zero LP)

```
You are the capx gate-(a) re-key lane (r#65) for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code. Branch: claude/capx-gate-a-rekey-r65, fresh off origin/main.
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "GATE-(a) RE-KEY r#65"; ledger §0bj.
ONE ACT, ZERO LP. No solve, no scoring, no registration, no keeper edit, no marker edit, no other
desk's file. You edit frontend/data/forecast/program-status.json and nothing else, plus your record.

WHY. scripts/check_gate_a_provenance.py is EXIT 1 at main 40f4ed7a on SIX ISOs, the nineteenth
firing of the standing Q34 duty. The desk read at that pin:
  CAISO row 2026-09-12-caiso-275-gascoupling        -> live 2026-09-20-caiso-290-leftedge
  ERCOT row 2026-09-09-ercot265-receipts-fallback   -> live 2026-09-19-ercot266-mer-five-year
  NEISO row 2026-09-09-neiso-108-fuelvintage        -> live 2026-09-22-hydro-5-neiso-ror
  NYISO row 2026-09-09-nyiso-221-fuelvintage-span   -> live 2026-09-22-nyiso-hydro3-ror-split
  PJM   row 2026-09-11-pjm-d4-4-gasoutage           -> live 2026-09-23-pjm-h19-dbs-span
  SPP   row 2026-09-12-spp-36-shortwindow-span      -> live 2026-09-22-hydro-5-spp-floor
  SPP   ALSO: row claims marker complete=False; calibration-complete.json holds complete=True
        (declared 2026-09-13, owner ruling in session spp-40, "Complete then run").
** DO NOT TRUST THOSE IDS. ** Read every fact LIVE at your HEAD. If your HEAD disagrees, YOUR HEAD IS
RIGHT: re-key to it and say so. For each row, state the FULL chain of promotions it was stale across
(read the keeper shard's own history fields and the calibration logs), not a single arrow.
MISO is green (miso-267 re-keyed it 2026-09-23, commit 1b175ce9). Its act is your worked example:
read `git show 1b175ce9`.

METHOD.
 1. Per ISO, read live and cite: keeper id (frontend/data/backcast/keepers/<ISO>.json); BOTH blocks
    of frontend/data/backcast/calibration-complete.json; determination from the committed status
    sidecar frontend/data/backcast/status/<ISO>.js (NOT a re-score; you compute no verdict); the
    promotion instrument AS A DOCUMENT.
 2. TARGETED STRING EDIT of each row's `detail`, `read_live_at` and `corrected_by` leaves, plus the
    row's top-level `keeper` / `marker_complete` fields. ** NEVER a json.dumps round-trip. ** The file
    is a hand-maintained seed wrapped verbatim; reserializing reformats every other desk's row.
 3. Preserve prior text. Each `corrected_by` is a chain, so prepend your sentence with "Supersedes:".
 4. Touch ONLY the rows that fail at your HEAD.

SPP IS THE ONE ROW WHERE A STATUS MOVES, AND IT MOVES BECAUSE THE MARKER DID, NOT BECAUSE YOU DID.
The guard calls a gate "closed on a marker the ISO holds" the verdict-flipping half of F-5. Re-derive
SPP's leg (a) on the LITERAL §2.1b(2)(a) test: the keeper is CALIBRATED per its committed status
sidecar, AND the ISO holds `complete`. The precedent for a (a) flip done as a records act is D56-R
(docs/handoffs/FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md). Follow it. Cite the owner
instrument verbatim from calibration-complete.json. STOP GATE: if SPP's committed status sidecar does
NOT read CALIBRATED for the live keeper, do NOT flip. Re-key identity and marker text only, leave
status fail, and report the contradiction between marker and keeper. That is the owner's to rule.
For every other ISO, if re-keying would move a leg status, a determination or a grade: STOP, report.

STOP GATES (as r#64): an ISO already green at your HEAD is not re-keyed, because asserting a
supersession that did not happen is a false record. If CAISO's marker entry names a keeper other than
its live one (at 40f4ed7a it named caiso-288 while the shard names caiso-290), REPORT it and do not
repair it. It belongs to the CAISO lane and the audit board.
Notes (not reds): NWPP and SOCO have keeper shards and no board row. Owner ruling Q68 (2026-09-24)
adds their rows only AFTER each declares backcast `complete`. Do NOT add them.

Score-after-rebase: this lane scores nothing, but rebase onto origin/main immediately before push and
re-run the gate AFTER the rebase. A promotion can land mid-lane.
EXIT: check_gate_a_provenance.py EXIT 0 on all seven rows at your final HEAD; the diff touches only
the failing rows of one file (plus your record, docs/handoffs/FINDING-capx-gate-a-rekey-r65-2026-09-24.md,
carrying per ISO the before/after `detail` head verbatim, the chain, and the instrument). Open a PR to
main. Lead your close with the gate's exit code, the six id transitions and SPP's (a) status before and
after. Rule 27 [R-PUSH]: push exact on-disk bytes; verify the pushed blob (program-status.json is
large). If you defer anything, name a LIVE owner or state that none exists.
```

---

## D93 — the key-provenance lag CLASS RULE, and the G6 registration (Opus, code)

```
You are the D93 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d93-key-lag-class, fresh off origin/main.
Authority: OWNER RULING Q66 (2026-09-24, capx ledger §0bj / §3): "Class rule."
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D93". ZERO LP.
Rule 27 [R-PUSH]: this lane edits src/market_sim/ (core scope). Edit locally, push exact bytes, and
blob-verify every file of 300+ lines after the push.

READ FIRST: docs/handoffs/FINDING-capx-d92-2026-09-10.md §2 (the seven-record diagnosis and the
recipe) · docs/handoffs/FINDING-capx-d91-2026-09-09.md (R1 registration, G6, the payload-driven vs
dataclass-driven census) · docs/handoffs/FINDING-capx-d85-key-provenance-2026-09-07.md ·
scripts/check_key_provenance.py and its exceptions / unregistered-baseline records (read their
`what_this_is_not` blocks).

STATE AT 40f4ed7a (verify, don't trust): check_key_provenance EXIT 1, 11 failures —
  10 x G1_UNKNOWN: docs/handoffs/scn-ws5b-neiso/{ALL-CLEAN,CAP-STATE-TIGHT,CARB-HI,CES-P60,CES-T80}
     results/ff-t3-neiso-golden/d90-rescore, results/ff-t3-neiso-golden/d92/{base,carbon_plus25,gaspm5,gasup150}
  1 x G6: coal_mustrun_requires_measured_row (added by PJM lane pjm-h14, docs/RESULT-pjm-h14-2026-09-20.md),
     absent from 235 committed payloads, NOT in scenarios.py::_CACHE_KEY_OPTIONAL_FIELDS.

PART 1 — DIAGNOSE BEFORE YOU ENCODE ANYTHING. The ten are NOT one population:
 (a) The six pre-D91 records (scn-ws5b-neiso/* minus REF, and d90-rescore). D92 showed that each one
     reproduces its recorded literal under {"undrop": ["pjm_seam_neighbour_hourly_ladder"]}.
     Re-verify that at your HEAD.
 (b) D92's four d92/* legs. D92 measured them REPRODUCING on 2026-09-10, and they CONTAIN
     pjm_seam_neighbour_hourly_ladder. So they are not lag records of that class. Something since
     2026-09-10 moved their keys. Name it by experiment, as D91 did, with a single-field drop search
     over the fields absent from their payload. Expect coal_mustrun_requires_measured_row (the G6
     field) and test it rather than assume it. If it IS that field, then its registration (Part 3)
     should return all four to green on its own, and that is your proof. If it is NOT, STOP and
     report. Do not widen the class rule to absorb an unexplained record.

PART 2 — THE CLASS RULE (Q66). In check_key_provenance.py, a record is classified `lag` (not
UNKNOWN, not a failure) iff ALL of: its payload lacks the named registered field; the field's
registration commit is not an ancestor of the record's recorded solve sha (or, where the record
carries no sha, a DECLARED fallback you state in the PRECOMMIT); and the recorded key reproduces
EXACTLY under the undrop of that field. Encode it as DATA: a small committed table of
{field, registration_sha} pairs seeded with pjm_seam_neighbour_hourly_ladder / ee2275d2 (VERIFY that
sha in history; the clone is shallow, so `git fetch --unshallow` or `--deepen` as needed). Every
future registration then adds one row, not N records. A `lag` classification must print as a
REPORTED line, never silently. A record that satisfies the payload/sha legs but does NOT reproduce
under the undrop stays a FAILURE: that is a real defect wearing the lag signature.
TESTS, BOTH DIRECTIONS (D91's doctrine, "a gate seen only green is indistinguishable from one that
cannot fail"): a synthetic lag record classifies lag; the same record with a perturbed literal fails;
a record carrying the field fails normally; a post-registration sha fails normally.
Do NOT append to key-provenance-exceptions.json or to the unregistered baseline. Both records forbid
it.

PART 3 — THE G6 REGISTRATION. Register coal_mustrun_requires_measured_row in
_CACHE_KEY_OPTIONAL_FIELDS and _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS at its FROZEN default "False", as
D91's R1 did for pjm_seam_neighbour_hourly_ladder. This is a REGISTRATION, not a default flip. The
dataclass default stays False and an armed run keys distinctly. Before editing, COUNT the orphans:
committed configs solved after the field landed and before your registration. List them. After your
edit they either reproduce, or fall under Part 2's class with a new table row ({field, your
registration sha}). The latter can only be known after merge, so write the row as the lane's last act
and say so. Run the cache-key pin tests (tests/**/test_persisted_identity.py and the pins D91 names)
and report red before → red after.
Rule 28 [R-MECH-MATRIX] does not fire: no new mechanism, and the row already exists. Rule 24
[R-REGISTRY] is the reason this lane exists.

PRE-DECLARE in docs/handoffs/PRECOMMIT-capx-d93-2026-09-24.md BEFORE editing code: the expected
failure count after each part, and the Part 1(b) attribution you expect. Push it first.
Collision: any concurrent lane adding a ScenarioConfig field edits the same _CACHE_KEY blocks, so
rebase immediately before push. Concurrent capx lanes: the gate-(a) re-key (program-status.json only)
and D94 (a neiso solve lane; it will record which side of your registration its pin sits).
EXIT: check_key_provenance EXIT 0 at your final HEAD, or EXIT 1 with every residual named with an
owner. docs/handoffs/FINDING-capx-d93-2026-09-24.md leading with the before/after failure table, the
Part 1(b) attribution, and the both-direction test proof. Open a PR to main. If you defer anything,
name a LIVE owner or state that none exists.
```

---

## D94 — `neiso-t3`'s FC-6 driver battery on the post-D77 basis (Opus, neiso)

```
You are the D94 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso (python3 scripts/hydrate_data.py --profile neiso).
Branch: claude/capx-d94-fc6-driver-battery, fresh off origin/main.
Authority: OWNER RULING Q67 (2026-09-24, capx ledger §0bj / §3): "Charter D94 now."
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D94".

WHY. capx D92 (docs/handoffs/FINDING-capx-d92-2026-09-10.md §4) found that the pre-D77 CCS
emission-rate seam SUPPRESSED the model's carbon response. The FC-6 paired-P1 margin went from 10.50 to
50.92 Mt when re-based on post-D77 arms. D92 re-based the PAIRED half of FC-6 on `neiso-t3` and
explicitly carried the DRIVER-BATTERY input byte-identical (its PRECOMMIT §1.5):
  results/ff-t3-neiso-golden/bau-d46/fc6/driver-battery-neiso-2026-09-03.json
That is the T1.6 ladder (RPS/ACP vs VRE supply, rungs vre_short / vre_long, 2026-2050), solved
2026-09-03 on the pre-D77 basis. Both rungs read rps_dual_over_acp = 1.0, and FC-6 reports T1.6a/b as
VACUOUS CAVEAT. D92 §9.8: "HAS NO LIVE OWNER." You are the owner. The director checked the scope:
`neiso-t3` is the ONLY bare T3 verdict, so this is one battery on one verdict, not a board sweep.

READ FIRST: FINDING-capx-d92 (§1.5, §4, §5, §6, §11) and PRECOMMIT-capx-d92-2026-09-10.md + Addenda
A/B. Pay particular attention to §3 of the PRECOMMIT: `run_driver_battery.py --paired-arm` builds
from reference_config UNPINNED and would solve a THIRD recipe. `neiso-t3`'s recipe carries two pins,
ccs_retrofit_vom_adder 8.0 and ccs_retrofit_fixed_cost_co2_scaling False (the two UNIDENTIFIED DOF
entries). Every rung you solve MUST carry both pins so the FC-6 block describes the same model the
verdict describes. State in the PRECOMMIT exactly how you pass them.
Also read scripts/run_driver_battery.py and scripts/forecast_verdict.py (--driver-battery).

PART 1 — PRE-DECLARE, AND PUSH BEFORE ANY LP: docs/handoffs/PRECOMMIT-capx-d94-2026-09-24.md with the
pinned recipe, the G-DRIFT plan (below), and graded-in-advance predictions per rung: co2_mt_total,
retired_thermal_gw, reserve_margin_final, rps_dual_over_acp, and whether T1.6a/T1.6b stay vacuous.
State direction AND rough magnitude. D92's standard: a prediction that can only be graded charitably
is not a prediction, and a declared near-certainty is worth nothing and must be labelled as one.

PART 2 — G-DRIFT. Form 4 on a recorded-key basis audits CONFIG drift only (D88, D90-R). D92's
same-container control at a post-D77 HEAD returned exactly zero drift against d90-rescore. Your
control is the committed `neiso-t3` primary (d92/base, key dd8203a8bf1546b9). If your rung
configs differ from it by anything other than the rung override (entry_rate_limits) and fields that
land at their frozen default, list every difference before solving. KEY INTERACTION: capx D93 is
concurrently registering coal_mustrun_requires_measured_row in the cache key. Record whether your
pinned SHA contains D93's registration. Either side is acceptable. Recording it is not optional.

PART 3 — SOLVE, IN SHARDS (rule 32 [R-SHARD]: this session NEVER runs an LP). Two rungs, and each is
ONE indivisible 2026-2050 invocation (a forecast horizon is an evolution chain: rule 12, and rule 36
[R-YEAR-ISOLATION] (c) leaves it unsharded by year). Launch the two rungs as two concurrent shards
via mcp__Claude_Code_Remote__create_session, following rule 32(c) to the letter: source_revision =
your pushed PRECOMMIT's FULL 40-char SHA, and the first hard stop is `git rev-parse HEAD` == that
sha. No rebase, pull or sync. Each shard gets its own --out-dir
results/ff-t3-neiso-golden/d94/<rung>/ and its own branch, and pushes its FULL bundle under rule 34
(the .gitignore negation plus a plain `git add`, never `-f`, never `git add -A`). It edits nothing
under src/ or scripts/ and never touches frontend/data/**. "A shard that stops with a clear report is
a SUCCESS; a shard that repairs infrastructure is a FAILURE." Each leg is measured at ~30-47 min, so
state that budget in the shard prompt (rule 32(b): longer single shard, never a fan-out). Tell each
shard to report container preflight / memory peak lines, wall time and its key. The parent fetches,
verifies (config signature + both pins), then archives each shard (rule 33). The parent lands what
must survive on main before its PR merges (rule 33(f)).

PART 4 — RE-SCORE. First re-run forecast_verdict.py over the COMMITTED inputs and confirm it
reproduces the standing `neiso-t3` exactly (D90-R Addendum A.2's controlled-swap practice). Then swap
ONLY --driver-battery for your new battery JSON and re-score. Preserve the prior at
`neiso-t3-pre-d94` byte-equal (the suffixed-key convention; bare key = current). Follow D90-R
Addendum B's FC-7 four-clause rule literally if FC-7 moves. Score and register AFTER your final
rebase. A rebase after scoring re-stamps `scored_at_sha` via an artifact-only re-score before merge.
You are the SOLE writer of frontend/data/forecast/ff-verdicts.json this window.

REPORT at full magnitude, both directions: per rung, the pre-D77 (2026-09-03) → post-D77 value of
every battery metric; whether T1.6a/b stay vacuous (and, if the ACP still caps the dual at 1.0 in
both rungs, say that the ladder CANNOT discriminate on this basis, and name what would); and the
verdict transition. RULE 31 [R-RETAIN]: never rm a solved bundle; ask the promotion question in your
close. Rule 27: blob-verify every file of 300+ lines. If you defer anything, name a LIVE owner or state
that none exists.
EXIT: docs/handoffs/FINDING-capx-d94-2026-09-24.md leading with the verdict transition, the
predictions graded, and the per-rung table. Open a PR to main.
```

---

## r#66 NOTE

Four charters, issued 2026-09-25 at main `a1b8ebd9` against ledger §0bk, all dispatched by the desk. They write disjoint files. **NEXT FREE LABEL: D98.**

---

## GATE-(a) RE-KEY r#66 — five ISOs (Opus, code, zero LP)

```
You are the capx gate-(a) re-key lane (r#66) for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-gate-a-rekey-r66, fresh off origin/main.
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "GATE-(a) RE-KEY r#66"; ledger §0bk.
ONE ACT, ZERO LP. You edit frontend/data/forecast/program-status.json and nothing else, plus your record.

WHY. scripts/check_gate_a_provenance.py is EXIT 1 at main a1b8ebd9 on FIVE ISOs. This is the twentieth
firing of the standing Q34 duty. Every row went stale because an R-* input-vintage promotion did not
re-key it. The desk read:
  CAISO row 2026-09-20-caiso-290-leftedge     -> live 2026-09-24-caiso-r-inputs-vintage
  ERCOT row 2026-09-19-ercot266-mer-five-year -> live 2026-09-24-r-inputs-2019-2025
  MISO  row 2026-09-24-miso-268-coal-yard     -> live 2026-09-24-rmiso-arm-b-mid
  NEISO row 2026-09-22-hydro-5-neiso-ror      -> live 2026-09-24-r-neiso-inputs-2019
  PJM   row 2026-09-24-pjm-h22-rggi-span      -> live 2026-09-25-pjm-r-pjm-2
** DO NOT TRUST THOSE IDS. ** Read every fact LIVE at your HEAD, and if your HEAD disagrees, re-key to
your HEAD and say so. The backcast track is promoting several times a day. So re-run the gate AFTER your
final rebase, and re-key any row that went stale while you worked. Name the full promotion chain for each
row.

WORKED EXAMPLES: `git show 1b175ce9` (miso-267) and the r#65 re-key (PR #6582,
docs/handoffs/FINDING-capx-gate-a-rekey-r65-2026-09-24.md). Follow that method exactly:
 1. Per ISO, read live and cite: the keeper (keepers/<ISO>.json), BOTH blocks of
    calibration-complete.json, the determination from the committed status/<ISO>.js (NOT a re-score),
    and the promotion instrument as a DOCUMENT.
 2. TARGETED STRING EDIT of the row's `detail`, `read_live_at` and `corrected_by` leaves, plus its
    top-level `keeper` / `marker_complete` fields. NEVER a json.dumps round-trip.
 3. Preserve the prior text. Each `corrected_by` is a chain, so prepend with "Supersedes:".
 4. Touch ONLY the rows that fail at your HEAD. NWPP/SOCO notes are not reds: owner ruling Q68 adds their
    rows only after each declares `complete`.
STOP GATES: an ISO already green at your HEAD is not re-keyed. If re-keying would move a leg status (the
marker or the determination changed, e.g. an ISO entering or leaving `complete`), re-derive leg (a) on the
literal §2.1b(2)(a) test ONLY where the owner's marker instrument is cited verbatim (the D56-R / r#65
SPP precedent). Otherwise STOP and report that row. Report and do not repair any marker entry that names
a keeper other than the live one.
EXIT: check_gate_a_provenance.py EXIT 0 at your final HEAD, and a record at
docs/handoffs/FINDING-capx-gate-a-rekey-r66-2026-09-25.md. Open a PR to main. Lead your close with the exit
code and the id transitions. Rule 27: push exact bytes and verify the pushed blob. If you defer anything,
name a LIVE owner or state that none exists.
```

---

## D95 — D94's two key-provenance UNKNOWNs (Opus, code, zero LP)

```
You are the D95 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. Branch: claude/capx-d95-d94-key-unknowns, fresh off origin/main. ZERO LP.
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D95"; ledger §0bk.

WHY. scripts/check_key_provenance.py is EXIT 1 at main a1b8ebd9: "2 mismatch(es) reproduce under NO recipe".
Both are capx's own records:
  results/ff-t3-neiso-golden/d94/vre_short/run_config.json  recorded 1be407901f4f8000
  results/ff-t3-neiso-golden/d94/vre_long/run_config.json   recorded df7b178ae9ccbe41
Both were solved at pin 924017c856780bd4b7e989624d621e621c215f75, and D94 (FINDING-capx-d94-2026-09-24.md
§3/§5) measured both REPRODUCING their own keys at its merge. So something that landed on main after
924017c8 has moved them.

READ FIRST: FINDING-capx-d93-2026-09-24.md (the Q66 class rule, encoded as one table row per registration),
FINDING-capx-d91-2026-09-09.md (single-field drop search), and the check_key_provenance.py ladder.

PART 1: ATTRIBUTE BY EXPERIMENT. Diff scenarios.py _CACHE_KEY_OPTIONAL_FIELDS* and config/solve_surface*
between 924017c8 and HEAD (deepen the shallow clone as needed). Run the D91 single-field drop search over
every ScenarioConfig field absent from those two payloads. Test the surface fingerprint (D79) separately:
a solve-surface registry row that re-derived after 924017c8 is a DIFFERENT class from an unregistered-field
lag. Name the cause with the reproducing literal.
PART 2: DISPOSE.
 (a) If it is an unregistered-field lag of the Q66 class, add ONE table row {field, registration_sha} and
     prove it both directions with tests, D93's pattern.
 (b) If it is a field that is STILL unregistered (a live G6-class defect that the census is blind to,
     because the payload predates the field), register it at its frozen default as D91 R1 did, then (a).
 (c) If it is a surface re-key, say which registry row moved, which ISOs it re-keys, and whether an
     existing exception class covers it. Do NOT invent a class. Report it for an owner card.
 (d) If no single cause reproduces: STOP and report. Never append to key-provenance-exceptions.json.
Pre-declare the expected attribution in docs/handoffs/PRECOMMIT-capx-d95-2026-09-25.md and push it
before editing code. Rule 27: blob-verify every file of 300+ lines. Concurrent capx lane D96 will solve
NEW neiso-t3 legs at a later pin. Its records must reproduce under your final rules, so check them if they
land before you merge.
EXIT: check_key_provenance EXIT 0, or every residual named with a LIVE owner.
docs/handoffs/FINDING-capx-d95-2026-09-25.md leads with the attribution and the before/after census line.
Open a PR to main.
```

---

## D96 — neiso-t3 onto post-F1, Q69 (Opus, neiso)

```
You are the D96 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso (python3 scripts/hydrate_data.py --profile neiso).
Branch: claude/capx-d96-neiso-t3-postf1, fresh off origin/main.
Authority: OWNER RULING Q69 (2026-09-25, capx ledger §0bk / §3): "Re-solve now."
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D96".

WHY. capx D94 (docs/handoffs/FINDING-capx-d94-2026-09-24.md §3, §6.2, §7(a)) found `neiso-t3` on TWO
data vintages. Its FC-6 driver battery (d94/) is post-F1: F1 is the eGRID-2024 heat-rate update, merged
2026-09-24, whose own note says it invalidates every forecast at the same key. Its primary bundle, its
paired arms and its FC-5 table (d92/{base,carbon_plus25,gaspm5,gasup150}) are pre-F1. D94's same-HEAD
control measured the drift: 293 trajectory cells, cumulative CO2 154.4195 -> 151.2747 Mt (-2.04 %),
2030 CCS 6,648.3 -> 6,979.7 MW. You put the whole verdict back on one vintage.

READ FIRST: FINDING-capx-d94 (whole), FINDING-capx-d92 + PRECOMMIT-capx-d92 with Addenda A/B (the four-leg
recipe, the two neiso-t3 pins ccs_retrofit_vom_adder 8.0 and ccs_retrofit_fixed_cost_co2_scaling False,
the controlled-swap scorer practice, and the FC-7 four-clause rule), and F1's own merge note/record.

PART 1: PRECOMMIT, PUSHED BEFORE ANY LP (docs/handoffs/PRECOMMIT-capx-d96-2026-09-25.md). The four legs
are identical to D92's recipe, both pins included, with only the HEAD changed. Include a G-DRIFT hunk
audit of 924017c8..your pin (D94's pin; its vre_short is your natural same-vintage control for `base`).
Pre-declare per leg: cumulative CO2, 2030 CCS MW, RM2050 and the FC-6 paired-P1 margin, each with
direction AND magnitude. Also predict whether ANY FC status moves, and label near-certainties as such.
EXPECTATION TO BEAT: `base` should land near D94's vre_short (151.27 Mt), since both run one recipe on one
vintage. Say in advance how close, and what a miss would mean.
PART 2: SOLVE, IN SHARDS (rule 32; this session never runs an LP). Four legs, each ONE indivisible
2026-2050 invocation (rule 36(c): a forecast horizon is never sharded by year). Launch four concurrent
shards per rule 32(c): source_revision = your pushed PRECOMMIT's full 40-char SHA, with the first hard stop
`git rev-parse HEAD` == that SHA and no rebase/pull/sync. Give each its own --out-dir
results/ff-t3-neiso-golden/d96/<leg>/ and its own branch, and have it push its FULL bundle (rule 34: a
.gitignore negation plus plain `git add`, never -f and never -A). No edits under src/ or scripts/, never
touch frontend/data/**, no PR. "A shard that stops with a clear report is a SUCCESS; a shard that repairs
infrastructure is a FAILURE." Budget ~30-47 min per leg, and state it. Each shard REPORTS its key, wall
time and the preflight/memory-peak lines. The parent fetches, verifies the config signature + both pins,
lands what must survive on main (rule 33(f)), and only then archives each shard.
PART 3: RE-SCORE. Re-run forecast_verdict.py over the COMMITTED inputs first and confirm it reproduces the
standing neiso-t3 exactly. Then swap the primary bundle, the paired arms and the FC-5 table onto d96, and
keep the d94 driver battery. Re-author FC-5 exactly as D92 §6 did. Preserve the prior at
`neiso-t3-pre-d96` byte-equal. Follow the FC-7 four-clause rule literally if FC-7 moves. Score and register
AFTER your final rebase; a rebase after scoring re-stamps scored_at_sha artifact-only. You are the SOLE
writer of ff-verdicts.json this window.
KEY PROVENANCE: concurrent lane D95 is attributing the two d94 UNKNOWNs. Your four new run_configs must
reproduce their own keys at your merge. Report the census line before and after.
REPORT every leg at full magnitude, both directions, plus the verdict transition. Rule 31: never rm a solved
bundle, and ask the promotion question. Rule 27: blob-verify every file of 300+ lines. If you defer
anything, name a LIVE owner or state that none exists.
EXIT: docs/handoffs/FINDING-capx-d96-2026-09-25.md leads with the verdict transition, the predictions
graded, and the per-leg table. Open a PR to main.
```

---

## D97 — T1.6 re-point DESIGN, Q70 (Fable, code, zero LP)

```
You are the D97 lane for jessicacohen554-cyber/market-simulator.
MODEL: Fable. DATA PROFILE: code (widen to neiso only if you need to READ inputs). ZERO LP. Branch:
claude/capx-d97-t16-design, fresh off origin/main.
Authority: OWNER RULING Q70 (2026-09-25, capx ledger §0bk / §3): "Design lane first."
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D97".

WHY. The FC-6 driver-battery ladder T1.6 ("RPS/ACP vs VRE supply, short -> long") cannot discriminate in
NEISO. capx D94 (FINDING-capx-d94-2026-09-24.md §1.1) measured this on the neiso-t3 golden recipe. Its lever,
entry_rate_limits True -> False, leaves NEISO wind+solar at 33.0 GW in BOTH rungs, and the REC dual sits at
the $50 ACP in every year of both. So T1.6a/T1.6b read VACUOUS CAVEAT. Q27 (capx ledger §3) is the
precedent ruling class for re-pointing a ladder. Read it, and read D35 (the P2 re-scope) as the worked
example of re-pointing an FC-6 element.

THE DESIGN QUESTION: which REAL driver moves NEISO's VRE supply, so that the pre-registered expectations
"REC dual <= ACP" and "REC dual falls as VRE builds toward the target" become TESTABLE? Candidates to
evaluate, not to assume: the RPS target level itself, VRE capex / ATB cost vintage, the offshore-wind
pipeline (known additions), interconnection / entry caps specific to NEISO, the ACP level. For each
candidate, work out by CODE READING and zero-LP arithmetic (committed d94/d92 trajectories, entry-screen
margins):
  (1) does it reach NEISO VRE entry at all (trace the seam in capacity evolution);
  (2) the expected direction and rough size of the VRE response;
  (3) whether the REC dual can leave the ACP ceiling in the rung;
  (4) whether it is a real forward driver (rule 1 / rule 13), never a knob chosen to make T1.6 pass.
      Selecting a lever BECAUSE it makes the gate pass is the fitted-mechanism selection rule 1 forbids,
      so say why each candidate is a legitimate driver independent of the outcome.
Then PRE-DECLARE the recommended ladder: its rungs, overrides and expectations, the cost (legs x ~35 min),
and what a vacuous result would mean.
BOUNDARIES: no solve, no edit under src/ or scripts/, no scorer change, no ff-verdicts edit. D96 is
concurrently re-solving neiso-t3 and is the sole ff-verdicts writer.
EXIT: docs/handoffs/DESIGN-capx-d97-t16-repoint-2026-09-25.md, ending in ONE owner card: the recommended
re-point, the alternatives, and "retire T1.6 for NEISO" as the named fallback. Open a PR to main. If you
defer anything, name a LIVE owner or state that none exists.
```

---

## r#67 NOTE

Two charters, issued 2026-09-26 at main `cf0950dc` against ledger §0bl, dispatched by the desk. They write disjoint files. **NEXT FREE LABEL: D100.**

---

## D98 — the solve_surface construction, Q71 (Opus, code, zero LP)

```
You are the D98 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: code. ZERO LP. Branch: claude/capx-d98-surface-construction, fresh off origin/main.
Authority: OWNER RULING Q71 (2026-09-26, capx ledger §0bl / §3): "Add the construction."
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D98".

WHY. check_key_provenance.py is EXIT 1 on two records, results/ff-t3-neiso-golden/d94/{vre_short,vre_long}/run_config.json.
capx D95 (docs/handoffs/FINDING-capx-d95-2026-09-25.md) attributed them to a SOLVE-SURFACE re-key (capx D79),
not to a field. After their pin, R-PJM-2's a669e4a4 and COAL-SUB's 5f8d153c moved NEISO's surface rows. Hashing
each record with the `moved` block from ITS OWN committed <ISO>/<key>/solve_surface.json reproduces its recorded
literal. D95's zero-code probe reproduced 9 of 10 committed solve_surface.json bundles that way; the 10th,
d90-rescore, is already a Q66 LAG.

THE ACT. Add that third construction to the census ladder, beside "declaration" and "live":
 - It applies ONLY when the record's own committed solve_surface.json exists and carries a `moved` block. The block
   is read from the record's bundle and never synthesized, so a record without one cannot reach it.
 - A record reproducing under it is classified by a new REPORTED class (name it, e.g. `surface-recorded`), printed
   as a line like the LAG rows. It is never silent and never a pass-through for a record that fails to reproduce.
 - Pre-declare in docs/handoffs/PRECOMMIT-capx-d98-2026-09-26.md, pushed before code: the expected census before
   and after, and which of the 10 bundles move class.
TESTS, BOTH DIRECTIONS (D91 doctrine): a synthetic record with a moved block that reproduces classifies; the same
record with a perturbed literal fails; a record with NO solve_surface.json cannot use it; and a tampered moved block
fails. Do not append to key-provenance-exceptions.json. Rule 27: blob-verify files of 300+ lines.
EXIT: check_key_provenance EXIT 0 at your final HEAD, or every residual named with a LIVE owner.
docs/handoffs/FINDING-capx-d98-2026-09-26.md leads with the census line before and after. Open a PR to main and merge
it once CI is green. Concurrent capx lane D99 will add new run_configs; re-run the census after your final rebase.
```

---

## D99 — T1.6 re-point execution, Q72 (Opus, neiso)

```
You are the D99 lane for jessicacohen554-cyber/market-simulator.
MODEL: Opus. DATA PROFILE: neiso (python3 scripts/hydrate_data.py --profile neiso).
Branch: claude/capx-d99-t16-repoint, fresh off origin/main.
Authority: OWNER RULING Q72 (2026-09-26, capx ledger §0bl / §3): "Re-point, 2041–2050 mean" = DESIGN-capx-d97 §6
option (a) with sub-choice (a-2).
Binding charter: docs/handoffs/capx-director-prompt-pack-2026-08.md "D99". The DESIGN is
docs/handoffs/DESIGN-capx-d97-t16-repoint-2026-09-25.md. Read it WHOLE. Its §3 outcome map (A–E), its honesty
clause and "no third lever" all BIND you.

THE ACT.
 1. Re-point the T1.6 ladder to `entry_pipeline_aware_signal`: vre_short = False (the golden's own posture),
    vre_long = True. This is a ladder-definition change, done the way D35 and T16-A did theirs; cite both.
 2. Implement (a-2): T1.6b's metric becomes the 2041–2050 horizon mean of rps_dual_over_acp. Make the plan-§2 edit
    and the one metric construction, and update the T16-A pin test. Do NOT change T1.6a or any other FC element.
    This is a scorer change, so run the whole scorer test lane and re-score every OTHER registered verdict
    artifact-only to prove none of them moves (cross-lane re-grade doctrine). Report that table.
 3. PRECOMMIT, pushed before any LP (docs/handoffs/PRECOMMIT-capx-d99-2026-09-26.md). Include the two rung recipes
    (the neiso-t3 golden recipe at D96's vintage, both pins ccs_retrofit_vom_adder 8.0 and
    ccs_retrofit_fixed_cost_co2_scaling False, plus the rung override), a G-DRIFT hunk audit against D96's pin, and
    predictions for each outcome A–E. vre_short IS D96's `base` recipe, so if G-DRIFT is all-INERT, reuse D96/base as
    the vre_short rung and solve ONE rung only. State this in the PRECOMMIT.
 4. SOLVE IN SHARDS (rule 32; you never run an LP): one 2026-2050 invocation per rung (rule 36(c)), pinned to the
    PRECOMMIT's full 40-char SHA. The first hard stop is `git rev-parse HEAD` == that SHA, with no rebase or pull.
    Give each its own --out-dir results/ff-t3-neiso-golden/d99/<rung>/ and its own branch. Push the full bundle
    (rule 34: a .gitignore negation plus plain `git add`, never -f or -A). No src/ or scripts/ edits in the shard,
    no frontend/data/**, no PR from the shard. "A shard that stops with a clear report is a SUCCESS; a shard that
    repairs infrastructure is a FAILURE." Budget ~35-45 min. Land the slim bundle on YOUR branch and verify it,
    then archive the shard. Do NOT merge shard cache-parquet PRs; D94/D96 precedent is that they stay off main.
 5. RE-SCORE: controlled swap as in D90-R A.2 (reproduce the standing neiso-t3 first), then swap in the new battery.
    Preserve the prior at neiso-t3-pre-d99 byte-equal. You are the SOLE writer of ff-verdicts.json. Score after your
    final rebase.
REPORT per rung at full magnitude, the outcome letter A–E realized, and the verdict transition. Rule 31: never rm a
solved bundle. Rule 27: blob-verify files of 300+ lines. If you defer anything, name a LIVE owner or state that none
exists.
EXIT: docs/handoffs/FINDING-capx-d99-2026-09-26.md leads with the verdict transition and the outcome letter. Open a
PR to main and merge it once CI is green.
```
