# capx director — prompt pack (revised at refresh #9, 2026-08-30; first issued 2026-08-25)

Canonical text of the session prompts live on the capacity-expansion (Forecast Finalization)
track. Ledger: `docs/handoffs/capx-director-ledger-2026-08.md`. Signatures:
`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5. Revisions at r#8: D7 LANDED
(`ca8b749`) and drops from the live set; D10 corrected for the nyiso-155 keeper state; D11
RE-SCOPED to D11-R (the D-1 volume rule — ledger §0e.3), never run in its original form.
Revision at r#9: every prompt's freeze guardrail updated to the TIER-SCOPED state (owner card 6,
executed 2026-08-30 — locked test frozen for every ISO; validation governed by the `complete`
marker + --holdout-authorized; nothing a capx lane touches either way).

| lane | status | branch | model | profile | heavy slot? |
|---|---|---|---|---|---|
| **D10** NYISO T1-X crossover | reissued r#8 (corrected) — **still unstarted at r#10; highest-value light lane** | `claude/capx-d10-nyiso-t1x` | Fable | nyiso | no |
| **D11-R** D-1 entry volume rule | **RUNNING since r#10** (owner-dispatched 2026-08-30) | `claude/capx-d11r-entry-volume-rule` | Fable | ercot | no (Phase 0 first; A/B is light) |
| **S-123** MISO adequacy package | issued r#5, not started — **r#10 check FAILED again: miso-190 in flight; held on the start-time check** | `claude/capx-s123-miso-adequacy` | Fable | miso | only if it re-measures (MISO = no co-run) |
| **S-4** NEISO hydro accreditation | **LANDED r#10** (PR #4312; factor 0.7352) — **T1-F verification pair + FC-1 re-score + forecast registration still owed**; historical prompt below | `claude/capx-s4-neiso-hydro-syqu7m` | Fable | neiso | no |
| **S-5** PJM requirement horizon-edge | issued r#5, not started — ready when a heavy slot frees | `claude/capx-s5-pjm-horizon-edge` | Fable | pjm | no (S-6 is the heavy one, strictly after) |

**Suggested order (r#8, per the owner sitting 2026-08-30):** D10 + D11-R + S-4 now (all light —
CAISO and ERCOT backcast branches are in flight and may hold the heavy slots; D11-R re-scope
RATIFIED). S-5 next as a heavy slot frees. S-123 is HELD until r#9 by owner ruling. D12 is
chartered only after D11-R reports (owner-ratified sequencing). Only S-123's optional re-measure
and the later S-6 contend for the ≤2 heavy-solve cap, which is SHARED with the owner's
concurrent backcast solves.

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

## D10 — NYISO T1-X crossover (chartered by card A, A-A)

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

## D11-R — the D-1 entry volume rule (re-scoped at director refresh #8; supersedes D11, never run)

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
measured-outcome feedback (rule 13). DECONFLICTION: MISO's backcast lane is LIVE and active —
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

## S-5 — PJM requirement horizon-edge (unblocked by card C, C-A)

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
