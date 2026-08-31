# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization Program) track.
Maintained by the director session on branch `claude/capx-director-ledger`; one refresh = one
commit when anything changes. The director charters sessions and tracks state — it never runs
solves, never edits `src/market_sim/`, and never charters backcast-calibration work (that track
is the owner's own CAISO/ERCOT/MISO sessions, watched here for deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-08-31 (refresh #21) ·
**HEAD at refresh:** `50fd46c1` · **Owner cards A/B/C SIGNED 2026-08-25; Q5/Q6/signal/S-123 RULED at the r#8 sitting; Q5 RE-RULED at r#12 — WITHDRAW; Q7/Q8/Q9 RULED at the r#13 sitting (leg-(c) measured-closes · D11-R arming HOLD-until-D12 · miso-190 still running)** (§3)
**Handoff prompt for a successor director session:** `docs/handoffs/capx-director-handoff-2026-08-30.md` (REWRITTEN at r#16 — the four-lane wave in flight, the Q10 auto-arm authorization, and the standing leg-(d) re-present duty; r#17 amends its in-flight list: D5-R LANDED-VERIFIED)

---

## 0r. Refresh #21 (2026-08-31, HEAD `50fd46c1`) — the relaunch wave LANDS 3/3 (D12-A-R · S-123-V-R · S-6-R); OWNER CORRECTION: the NEISO golden was NEVER LOST (still running) — T3-GOLDEN-R RECALLED unrun; MISO promotes miso-191; ercot-245 KILLED on its own census

**1. OWNER CORRECTION (this sitting): the T3 NEISO golden is STILL RUNNING.** r#20's grading
of T3 as "session lost mid-solve" was WRONG — recorded against interest (the branch census
read 0 unique commits and no registration, which is exactly what a long solve mid-flight
looks like; absence of landing is not evidence of loss). **T3-GOLDEN-R is RECALLED UNRUN**
(never dispatched — no branch, no commits; the pack §T3 relaunch annotation is amended to a
recall notice). NOBODY launches a second golden: the NEISO keys of `ff-verdicts.json` +
`program-status.json` remain the running session's to write, and the Q13 authorization
covers ONE campaign. Standing lesson for future relaunch sittings: before grading a
solve-carrying lane LOST, ask the owner whether its session is still running — a ~1 h+
solve lands nothing observable until it finishes.

**2. RELAUNCH-WAVE LANDINGS — 3 of the 3 dispatched capx relaunches landed:**
- **D12-A-R LANDED** (PR #4429): the orphan branch's work re-verified per the r#20 protocol
  and landed — `entry_margin_exhaustion` + `entry_forward_reserve_leg` armed as ERCOT
  forecast defaults per Q15, matrix stamped (cells → K-forecast-armed), the re-verification
  recorded in the finding (`3415f456`).
- **S-123-V-R LANDED** (PR #4441 + `99ffb2ce`): the verification re-measure run and
  registered, S-123 finding §6 FILLED with measured results, MISO board refreshed. The
  S-123 package is now COMPLETE (scoreboard row LANDED-PARTIAL → LANDED).
- **S-6-R LANDED** (PR #4436): `pjm-2026-2030-s6-ledger` registered, bare `pjm-t1f`
  re-scored preserve-then-overwrite, PJM board block refreshed. **Headline: PJM's FC-1 FAIL
  set is {I7, I12}, not I7 alone** — the measured three-year I7 fail set restated onto the
  board; the finding corrects the prior "I7 is the only FC-1 failure left" reading. (Stray
  duplicate branch `claude/capx-s6-pjm-ledger-relaunch-p5kb8w` points at already-merged
  commits, 0 unique — safe to delete.)
- Model-economy readback (r#20 item 4): S-6-R and S-123-V-R ran their pre-declared charters
  on **Opus** and landed clean — the doctrine's first confirming instances.

**3. QUEUE RELEASED BY THESE LANDINGS:** **D4-I3 dispatchable** (D12-A-R landed and
ercot-245 concluded — ERCOT surfaces free) · **D3 dispatchable** (S-123-V-R landed,
miso-191/192 concluded — MISO surfaces free; start-time collision check vs any new MISO
branch stays in its prompt) · **D6** next batch as before · **D8's verdict/board
re-emission stays DEFERRED behind the golden** (the last of the three namespace writers
still in flight) · **NEISO-RC repair phase** remains a next-batch decision on its landed
Phase-0 finding.

**4. BACKCAST/AUDIT MOVEMENT (watch only):**
- **ercot-245 CONCLUDED — KILLED on its own census** (PR #4443): K-A (ST mass), K-C (both
  years, all legs) and K-T (T-1 CC/ST, T-2 p95) all fire; **Phase-1 NOT licensed, the A/B
  license never spent** — the precommit's stop rule executed exactly. Per its §8, the
  2024/2025 all-resource SCED conduct-corpus intake is the named unblock — an owner call.
- **MISO KEEPER → `2026-08-30-miso-191-bexit`** (PR #4433): the miso-190-named successor
  executed (binning-aware exit-cohort delivery), A/B registered control + arm, matrix cell
  `partial_plant_exit_carry` R → K; determination **NOT-YET on {C3a-2025} ALONE**, C6
  attested. **miso-192 landed** (PRs #4437/#4440): D-4 posture sitting — `chp_btm_measured`
  REFUTED zero-solve (U → R); the D-4 posture question returns to the owner better-posed
  (three options, `FINDING-miso192-chp-btm-phase0-2026-08-31.md`).
- **NYISO:** nyiso-162 re-verified the parked Leg-2 object against the live keeper (R-C;
  PR #4431); **nyiso-163** (PR #4438) built + pre-validated the on-receipt AORR
  identifiability gate and verified the Leg-2 access route — winter face stays
  identification-blocked, determination NOT-YET on {C3a-2025, C3c}; **the owner's action is
  one request** (the Applications-layer AORR record). Next shorthand: nyiso-164.
- **CAISO:** **caiso-226 LANDED** (PR #4435) — the A3 OFO intake funded and executed through
  the full data contract (gas-ofo-events schema + immutable SoCalGas snapshots + rule-13
  adjudication); **the caiso-227 arm is PRE-REGISTERED and UNFUNDED — an owner call** (filed
  item 11). Terminal rest otherwise unchanged; next number caiso-227.
- **T1-H storage-entry Leg A ARMED** (PR #4442, owner ruling R-A). **C-1 joint wind A/B
  landed** (PRs #4430/#4432/#4439): both kill-gates PASS, joint posture NON-COMPLEMENTARY on
  wind. Audit records v16 refreshed (PR #4434).

**6. DISPATCH RECORD (post-r#21 sitting, owner: "issue prompts"):** THREE lanes issued,
collision-mapped — **NEISO-RC-R** (the repair phase: R2 curve re-derivation + R1 registry
intake + R3 scorer trio + R4, per the Phase-0 finding §6/§9; Fable, neiso; golden care lines
— never the t3 or bare neiso-t1f keys) · **D3** (the MISO t1h `retire.total_gw` PASS→FAIL
flip, attribution-first, zero-solve Phase 0, precommit-first; the I13 cobweb closure is
treated as OPEN, not a settled repair; Fable, miso) · **D4-I3** (ERCOT I3 scarcity-slack
half ONLY, card Y-C boundary respected; zero-solve breach-set measurement + pre-declared
post-arming expectation + the FR-6 code-comment home; **Opus** under the r#20
model-economy doctrine — the cause is already characterized, the lane measures and routes).
**D6 stays HELD one more batch** (its four T1-H curve legs are the natural post-arming
measurement vehicle and contend with D4-I3's expectation half — sequence D6 after D4-I3
lands). Charters: the three new pack sections.

**MID-SITTING AMENDMENT (same sitting, before this dispatch pushed):** the **T3 GOLDEN
LANDED** — the ORIGINAL running session finished its solve and registered the first §2.1b
full-horizon campaign (PRs #4447/#4452, branch `capx-t3-neiso-golden-r2-74wk0h`; the r#21
recall stands CORRECT — this is the original campaign completing, not a second launch; the
R-A posture-epoch caveat is recorded on its own record). Consequences executed here:
(a) **D8-RE is RELEASED and ISSUED** (fourth prompt this sitting, **Opus**) — all three
namespace writers (S-6, S-123-V, golden) have landed, so the deferred verdict/board
re-emission can run; (b) the NEISO-RC-R golden care line relaxes to the standing form
(never write the t3 or bare `neiso-t1f` keys — they are simply not its keys); (c) **D3's
start-time collision check has a live object**: `miso-193` (cc_duct_peaking, backcast) is
mid-A/B with sections pending — distinct namespace (backcast vs D3's forecast board), so
D3 proceeds but must not touch miso-193's surfaces. Also landed mid-sitting, watch only:
**ercot-246** (ISO-level determination of a partitioned keeper = worst config over
designated spans — ERCOT reads CALIBRATED), ercot-245's FINDING/log/matrix records
(PRs #4448/#4451), **caiso-227** (C3a-2025 root cause measured, honest null; Helms
ps-water-state intake landed, PR #4450), and **nyiso-163b** (owner ruling: the AORR access
route is CLOSED permanently and a C3c scarcity program OPENS — the NYISO route question has
moved; next NYISO lane is that program's, chartered on its own record).

**7. OWNER-TIER ITEMS OPEN AFTER THIS REFRESH:** (a) the nyiso-161 winter-face-waiver card +
the one-request AORR Applications-layer ask (nyiso-163); (b) miso-192's D-4 posture options
(i)/(ii)/(iii); (c) caiso-227 arm funding; (d) the ERCOT 2024/2025 SCED conduct-corpus
intake (ercot-245's named unblock); (e) the NEISO-RC repair-phase decision; (f) D8
re-emission timing once the golden lands.

## 0q. Refresh #20 (2026-08-31, HEAD `ee75a0b`) — THE RELAUNCH SITTING: the r#19 wave graded (four lanes LANDED, four sessions LOST); everything unlanded restarts FRESH; model-economy doctrine (Opus for pre-declared execution, Fable for adjudication)

**1. OWNER INSTRUCTION (this sitting):** relaunch the calibration workstream; anything that was
in flight and has not LANDED restarts fresh; assign Opus wherever the lane allows it, to
preserve Fable capacity. Sitting held in session branch
`claude/calibration-workstream-relaunch-bml7zm` (one sitting, one refresh, ledger edited from
there).

**2. LANDING VERIFICATION of the r#19 eight-lane wave** (measured against `origin/main` @
`ee75a0b` plus a pruned remote-branch census — every claim below is from commits/PRs, not
recollection):

- **LANDED (4):** **CAISO-224-FIN** (PR #4415, verified at §0p.6 — Q14 arc closed) ·
  **NEISO-RC Phase-0** (PR #4422 — finding-only as chartered; repair phase = next-batch
  decision) · **D16 seam guard** (PR #4423 — fail-closed refusal shipped) · **D8** (PR #4427 +
  `49400c5`/`298b8e8`/`e6b57c0` — the FC-7 instrument + the seven-leg run_config provenance
  record; **verdict/board re-emission still DEFERRED as chartered**, see item 5).
- **LOST (4) — session containers reclaimed before landing; per the owner instruction each
  restarts FRESH:**
  - **S-6**: the pre-declaration LANDED (PR #4418,
    `docs/handoffs/FINDING-capx-s6-pjm-ledger-2026-08-30.md`, which ends at the
    "*(Sections below were written AFTER the solve.)*" sentinel with nothing after it). The
    solve, the FC re-score, the `pjm-2026-2030-s6-ledger` registration, the
    preserve-then-overwrite verdict keys and the PJM board refresh are ALL owed. Branch
    `claude/capx-s6-pjm-ledger-uihbbp` open at 0 unique commits.
  - **S-123-V**: nothing landed — no branch, no commits; the S-123 §6 verification TBD is
    still open and the MISO 2.5× overshoot verdict still rests on unverified terms.
  - **T3 golden**: mid-solve loss. The enabling `register_forecast_run.py` fix LANDED
    (PR #4408); branch `claude/capx-t3-neiso-golden-74sq45` open at 0 unique commits; no
    registration, no verdict key, no board write ever happened.
  - **D12-A**: **ORPHAN BRANCH** `claude/capx-d12a-arming-0ibtzh` at 2 unmerged commits
    (`7585ed0` arms `entry_margin_exhaustion` + `entry_forward_reserve_leg` as ERCOT forecast
    defaults per Q15; `d851cb3` stamps the matrix; 801 insertions incl. `scenarios.py` /
    `iso_configs.py`) — pushed, never PR'd, never verified, NOT landed. The relaunch session
    treats that branch as EVIDENCE, never blind-merges it: re-verify the diff against the Q15
    ruling and the pack §D12-A charter (cache-epoch verification included, rule 27
    blob-verification on every ≥300-line file), then land it re-verified or redo it clean.

**3. RELAUNCH WAVE — four capx prompts re-issued.** Charters are UNCHANGED: the committed pack
sections (`capx-director-prompt-pack-2026-08.md` §§T3-NEISO-GOLDEN / D12-A / S-6 / S-123-V)
remain binding; each relaunch prompt carries only the deltas in item 2. Collision map
unchanged from r#19 (golden / S-6 / S-123-V write DISTINCT ISO keys of `ff-verdicts.json` +
`program-status.json`, rebase-care; D12-A writes ERCOT config/matrix only and touches neither).

**4. MODEL-ECONOMY DOCTRINE (owner instruction, standing):** a lane whose discretion was
already spent in a committed binding pre-declaration/precommit (constructions, kills and
decision rules frozen ex ante) is EXECUTION and runs on **Opus**; a lane that ADJUDICATES
(arming decisions, kill-grading on a novel object, mechanism design, determination/marker
consequences) stays **Fable**. Rule 27's floor is unchanged: Sonnet never touches
infrastructure; purely additive data-intake/docs lanes stay Sonnet-eligible. Applied:
**S-6-R / S-123-V-R / T3-GOLDEN-R → Opus** (fully pre-declared execution);
**D12-A-R → Fable** (forecast-default arming + orphan-branch adjudication). Director and
owner-sitting sessions stay Fable.

**5. QUEUE AFTER THIS BATCH:** D3 dispatches after S-123-V-R lands (same MISO board/verdict
surfaces) · D4-I3 after D12-A-R (ERCOT surface contention) · D6 next batch (likely
zero-solve-diagnosis scope) · **D8's deferred verdict/board re-emission stays deferred until
golden / S-6-R / S-123-V-R land** (they write sibling keys of the same files) · NEISO-RC
repair phase is a next-batch decision on its landed Phase-0 finding.

**6. BACKCAST-TRACK WATCH (deconfliction only — backcast prompts are handed to the owner, not
issued by this ledger):** **ercot-245 died mid-lane** — the precommit + Amendment 1 + the
680-line census probe LANDED (PRs #4417/#4421,
`docs/PRECOMMIT-ercot245-commitment-state-phase0-2026-08-30.md`), but the census run, kill
grading, FINDING, log entry and matrix evidence are owed; relaunch prompt handed to the owner
(**Fable**; dispatch strictly AFTER D12-A-R lands — shared ERCOT matrix shard). **nyiso-161**
delivered `DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` (PR #4420) — an OWNER
card, pending ruling; no NYISO lane until ruled. **caiso-225** watch sweep landed (PR #4425):
all armed watches NULL, terminal rest re-affirmed, next sweep DATED (≤ 2026-12-01) — no CAISO
relaunch. **miso-190 concluded REJECTED on its own PREREG** (kill 2; cell U→R, keeper
unchanged); its named successor (binning-aware unit-grain exit timing) is unchartered — a
miso-191 charter prompt is offered to the owner (**Fable**). **T1-H storage-entry Leg A
landed** (PRs #4419/#4426; both kill-gates passed, ERCOT cells U→O) — the successor is the
audit track's, not this wave's. Keepers, markers and the freeze verified unchanged this
sitting: `complete` = {NEISO, PJM}, `final` EMPTY, freeze tier-scoped to the locked test.

## 0p. Refresh #19 (2026-08-30, HEAD `c0a35ce`) — OWNER VOIDS THE CROSS-SESSION HEAVY-SLOT QUEUE; five lanes issued at once (S-6 · S-123-V · NEISO-RC · D16 · D8); max safe parallelism is the new doctrine

**1. STANDING DOCTRINE CORRECTION (owner instruction, r#19): THERE IS NO CROSS-SESSION HEAVY
SLOT.** The director had been serializing "heavy" solves (PJM 8.8 / MISO 9.6 GB "no-co-run")
across SESSIONS — an over-generalization of rule 12, whose memory cap governs concurrent
invocations on ONE box. Lanes run in isolated per-session containers with their own RAM;
the ONLY dispatch constraint is SESSION COLLISION — two lanes writing the same surfaces
(a shared JSON, a shard, a branch) or duplicating the same work. Recorded against interest:
S-6 was held four refreshes on this misreading; Q14's "S-6 after the finisher" sequencing is
VOIDED with its premise (the CAISO-224-FIN prompt's exit line annotated). Rule 12 continues
to bind INSIDE a session (years sequential; ~2 concurrent invocations per box).

**2. FIVE LANES ISSUED THIS SITTING (everything runnable, per the owner's ask), collision-
mapped:** **S-6** (PJM T1-F ledger run — first pack prompt written; one run, no control pair,
decomposed vs the committed pjm-t1f ledger; S-4b floor-retention analogue pre-declared as a
direction) · **S-123-V** (the MISO §6 verification re-measure — fills the TBD, registers,
refreshes the MISO block; stops-at-start if the original session is still mid-run) ·
**NEISO-RC** (the D14 retirement-composition Phase-0 — zero-solve attribution, finding-only,
candidate drivers pre-declared, repairs routed not built) · **D16** (the S-123-routed
armed-interface mc=0 seam defect — DIRECTOR MECHANISM DECISION: FAIL CLOSED, a hard refusal
in the holdout_policy pattern; the gas×HR fallback-price alternative deliberately NOT built
without its own charter — a guard is not a mechanism, no field, no matrix row) · **D8**
(FC-7's two halves: the DOF-ledger instrument + the seven-leg run_config provenance debt;
ALL verdict/board re-emission EXPLICITLY DEFERRED — three in-flight lanes write those files
on other keys). Shared-file collision handling: golden/S-6/S-123-V each write DISTINCT
keys/blocks of ff-verdicts.json + program-status.json with rebase-care lines; NEISO-RC/D16/
D8 write neither. Still runnable from prior sittings: **D12-A** (Q15 execution) and
**CAISO-224-FIN** (Q14 — no longer gates anything).

**3. QUEUE STATE AFTER THIS BATCH:** D3 (MISO retirement G3) held ONE refresh — same MISO
board/verdict surfaces as S-123-V (real collision, not slot doctrine); D4-I3 (ERCOT I3
half) held ONE refresh — ERCOT surface contention with D12-A; D6 (FC-3 curve-ON over-fire)
next batch, likely zero-solve-diagnosis scope. NEISO-RC's repair phase and D8's re-emission
follow-up are next-batch decisions on their findings.

**4. BACKCAST/AUDIT MOVEMENT (watch only):** ercot-244 arc CLOSED (records + matrix-card
adjudication block, PRs #4411/#4412). miso-m2m-flowgates raw mirrors tracked (PR #4409,
data intake). **nyiso-161 backcast lane OPEN** (`claude/nyiso-161-backcast-calibration-9734io`)
— deconfliction noted in the new prompts. The T3 golden branch open, still mid-solve, no
new commits. Keepers/markers/freeze unchanged (spot-verified r#18, no marker-file commits
since).

**5. DISPATCH CONFIRMED (owner, post-r#19): S-123-V, NEISO-RC, D16 and D8 ARE IN FLIGHT**,
joining CAISO-224-FIN (dispatched earlier under Q14), D12-A and the T3 golden — seven
concurrent capx lanes, the largest set to date. S-6 was briefly OWNER-HELD post-release,
then **LAUNCHED by the owner the same sitting** — EIGHT concurrent capx lanes. Next
refresh: verify landings across all eight, in whatever order they arrive.

**6. CAISO-224-FIN LANDED AND VERIFIED (PR #4415, same sitting):** the finisher executed the
precommit's §5 adjudication exactly — **R for keeper purposes (F1 fires ×3 + F2 fires)**,
both bundles registered on the backcast dashboard from the committed slim artifacts
(`2026-08-30-caiso-224-{a0-control,b1-fsno}`), the CAISO matrix cell stamped R with the
falsification citation, and the keeper VERIFIED UNTOUCHED (caiso-220-c1-crosswalk). The
owner's "mid keeper promotion" recollection resolved exactly as the precommit bound it: no
promotion, honest R, partition representation retained with W-2/W-3 as the upgrade feeds.
Q14's arc is fully closed.

## 0o. Refresh #18 (2026-08-30, HEAD `d2cd019`) — D12-C CONCLUDED: CONTRADICTION, nothing armed, Q15 card presented; D5-R completion CORRECTS the director's r#17 fifth-bundle call; S-123 lands 3 terms (verification pending the slot); the golden is mid-solve

**1. D12-C CONCLUDED — the CONTRADICTION branch executed, mechanically and honorably (PR
#4406; `FINDING-capx-d12c-confirm-pair-2026-08-30.md`).** G-1/G-2 EXACT (control reproduces
the committed bracket to the cent — the whole margin machinery byte-stable; armed cache key
bit-equal to the ex-ante prediction `f061b2646bfaac8b`). V-1/V-3/V-4/V-5 PASS: no phantom
(2025 builds nothing on −$34.5k/−$20.9k, D12's reason exactly), terminal RM 15.84 inside the
ex-ante [15.0, 21.0] (walk bracket carried down by exactly the pre-named live-VRE feedback),
2023/24 cc as declared, gas bands improve (cc lands EXACTLY on the 6.000 GW charter anchor,
err 8.756 → 5.756; ct err 3.879 → 1.621), B-2 survives (−12.95/+0.74/+9.05), and the gas half
of the exhaustion rule is LIVE for the first time (2024 ct exhausts at 500 MW sub-cap).
**The single miss — V-2: entering-2022 gas_cc 0 vs the declared [750, 1,250]** — is
decomposed at full magnitude: NOT a construction defect (start margin bit-identical
+$45,930.9), NOT a phantom; the offline walk that produced the window fielded ONLY
gas+storage, while the live walk fields every candidate class, so solar wins the early
tranches and exhausts cc's margin first — **MORE exhaustion by the same mechanism on the same
one-object margin**. A pre-declaration derivation error (§1 named the artifact for V-4's band
and failed to carry it into V-2), discovered after the arm ran, so it stands: tolerance NOT
widened post hoc (rule 21), nothing armed, cells stay `O`, both bundles registered
(`…-t1h-d12c-{control,armed}`). **The owner re-decides — Q15 card presented this sitting.**

**2. D5-R COMPLETION PASS (PR #4403, the original issued branch) — and it CORRECTS THE
DIRECTOR'S r#17 CALL, recorded here against interest:** the fifth bundle
(`neiso-2023-2027-crossover-capxd14`) was rescored after all via `--rescore-co2-grain`:
co2 +12.8/+10.6/−2.3 → **+12.8/+11.1/−1.8 %** — my r#17 "~0.004 % bound, no follow-up owed"
adjudication had read the 2023 family row alone (0.001 TWh); 2024/25 carry 0.085/0.082 TWh
of unsplit COAL → **+0.49 pp each**, seam-only, banded statuses unchanged. Pre-repair
baseline preserved as `neiso-t1x-pre-d5r` (the handoff's predicted suffix). The lane ALSO
executed the §0n.3 deferred records item itself: **[D5-R 2026-08-30] annotations now stand
on all three board co2 cells AND `gate_reading`** — that records item is CLOSED. Exit record
`FINDING-capx-d5r-scorer-coal-grain-2026-08-30.md`. Lesson stamped: a bound asserted from
one year's row of a three-year artifact is not a bound.

**3. S-123 LANDED-PARTIAL (PRs #4397/#4398/#4402; `FINDING-capx-s123-miso-adequacy-2026-08-30.md`):
all three terms SHIPPED from single published operands** — S-1 PRM re-vintage 0.179→0.157
(PY 2025-26 LOLE Module E-1 pair, −2,637.4 MW exactly the charter's number), S-2 external-ZRC
+3,505.9 MW (PRA posting p.22), S-3a LMR/DR fraction 0.0665940 (−9,236.8 MW) — 2026 position
−6,037.0 → +9,343.2 MW pre-solve, a 2.5× overshoot (the NYISO-intake honesty signature, not a
tuned closure). **§6 verification (the solo MISO 9.6 GB T1-F re-measure + FC-1 re-score) is
TBD — holding for the heavy slot.** D9 adjudicated UNREACHABLE at HEAD and routed (TVA
re-point + data prerequisite). **NEW DEFECT ROUTED TO THE DIRECTOR** (finding §5/§7 item 5):
armed-interface forecast years leave seam rows at their **mc=0 build placeholder** — queued
as a mechanism-decision candidate (D16) below.

**4. T3-NEISO-GOLDEN MID-SOLVE:** PREDECL §§1–4 merged (PR #4405 — Q13 cited verbatim, gate
legs re-verified live, budget declared) + registration-prep (PR #4408: t3-golden
classification + campaign gitignore block, S-4b slim-vs-heavy pattern). Branch open with no
further commits — the 25-year solve is running. Stamp on landing.

**5. CAISO-224-FIN NOT LANDED** (zero caiso-224 registrations; PR #4401 patched the
registry/payload parity CI gate to tolerate the two interim unregistered bundles — an
interim-state accommodation, not the finisher). **S-6 stays RELEASED-CONDITIONAL.**
**HEAVY-SLOT QUEUE (explicit, for dispatch):** golden (running, ~4.3 GB) → S-123's §6
verification (9.6 GB no-co-run) → S-6 (8.8 GB no-co-run; ALSO gated on CAISO-224-FIN
landing). The two no-co-run measures must not overlap each other either.

**6. BACKCAST/AUDIT (watch only):** ercot-244 opened AND **KILLED AT CENSUS** in one arc
(PRs #4404/#4407 — rtolhsl online-capability ceiling; precommit-first discipline again;
branch deleted). Keepers ×6, `complete`={NEISO, PJM}, `final` EMPTY, freeze tier-scoped:
ALL verified unchanged at `d2cd019`.

**7. THE r#18 SITTING — Q15 RULED: ARM BOTH FIELDS (§3).** The owner judged the D12-C record
confirming-in-substance under the finding's own §4.3 clause and directed the arming. Lane
**D12-A** issued (pack-canonical): zero-solve execution of exactly the §1.4 confirmation list
— ISOConfig `default_scenario_overrides` route (FFR-9C stage-B pattern), Q10+Q15 cited
verbatim with the V-2 miss described honestly, ERCOT matrix cells O → K-forecast-armed on
the registered pair, sister cells U, no re-registration (both bundles already registered).
Cross-track note carried into the prompt: the arming moves ERCOT forecast defaults under the
audit track's T1-H capacity-entry lane — their registered-posture controls are unaffected,
but any FUTURE bare invocation lands on the armed defaults; ERCOT matrix-shard rebase care.

## 0n. Refresh #17 (2026-08-30, HEAD `83c1c5a` → `a305f46` mid-refresh) — D5-R and S-4b BOTH LANDED-VERIFIED; NEISO leg (b) STRENGTHENS on the ARA-3 bar; leg-(d) card DUE THIS SITTING; D12-C mid-execution (PREDECL in)

**1. D5-R LANDED AND VERIFIED (PR #4388, branch `claude/crossover-co2-grain-repair-oycsy6`
— the lane picked its own branch name; same charter). Controls checked BEFORE the headline,
per the standing duty — ALL PASS:** NYISO co2 byte-identical ×3 (structural no-op); the
grain-reconciled `family_volume` gas_twh/coal_twh rows and flat rubric rows deep-equal every
ISO-year; C1 records, price_mean, price_shape, retirements, additions, capacity-track co2 all
deep-equal. Every re-scored cell landed within ±0.2 pp of D5 §5.2's pre-declared table
(tolerance was ±0.5). **Verdict outcomes exactly as pre-declared:** PJM co2 LEAVES the FC-4
FAIL set (2023/25 clear, 2024 CAVEAT 10.3 %); MISO co2 LEAVES it (2023/24 clear, 2025 CAVEAT
13.4 %); ERCOT 2023/24 STAY FAIL on the honest volume gap (−25.2/−23.2 %), 2025 PASS (+1.3 %);
NYISO untouched. No FC-4 category status flips (surviving price/volume rows still gate); no
§2.1b leg moves (leg (c) is measurement-keyed per Q7). Ancillary honesty fix shipped: the
`register_hindcast --preserve-invariants` fall-through that fabricated 13 vacuous PASS
invariant rows over an absent cache now reuses-or-omits, never recomputes.
`docs/handoffs/RESULT-crossover-co2-grain-repair-2026-08-30.md`.

**2. THE FIFTH BUNDLE, ADJUDICATED (the r#16 handoff's open question — the prompt named five
keys, the lane rescored four).** The committed NEISO bundle
(`neiso-2023-2027-crossover-capxd14`) was NOT put through `--rescore-co2-grain`; its verdict
re-emitted provenance-stamps-only via the standard 9-verdict path. Director verified the bound
directly from the committed score artifact: NEISO's model carries **0.001 TWh** of generic
`COAL` (`family_volume.coal_twh.model_twh`, `model_only_classes=["COAL"]`) → the grain drop
bounds at ~0.001 Mt on 25.4 Mt ≈ **0.004 % of co2 — below representable precision and far
inside the pre-declared ≲0.4 % ceiling**. The skip is materially sound; D14's measured
+12.8/+10.6/−2.3 % stand as the honest values. No follow-up owed.

**3. NEW NAMED RECORDS ITEM — board co2 annotation (deferred, deliberately).** The board's
ERCOT/PJM/MISO leg-(c)/T1-X cells and `gate_reading` quote co2 magnitudes (49.2/42.7/50.6 ·
45.1/40.4/54.2 · 63.3/58.9/75.5 %) from the LIVE gate keys — faithfully: those FFR-3A-3/-3A-4
bundles were never committed, so no zero-solve re-measure exists for them (RESULT §4) and the
rows stay as scored. But D5 established those magnitudes are **46–117 % scoring-instrument
error**, and the board says so nowhere — the program's classic stale-quote defect waiting to
happen. The fix is a [D5-R 2026-08-30]-style annotation on three cells + `gate_reading`
(pattern: the existing [CORRECTED 2026-08-24] notes), cross-referencing the repaired committed
ffr2a/capxd10 rows. **DEFERRED to the next records act** rather than chartered now: D12-C,
S-4b and S-123 are all in flight and may edit adjacent board blocks — a records lane touching
`program-status.json` mid-wave invites the same merge contention D13 was sequenced to avoid.
Leg-(c) statuses are unaffected either way (Q7: measured closes the leg, whatever it says).

**4. D12-C CONTROL REPRODUCIBILITY RE-VERIFIED AT THE NEW HEAD (cross-track threat checked in
code, not assumed).** The audit track's T1-H Phase-1 Leg A landed since D12-C's bracket was
committed (PRs #4386/#4389: `storage_entry_availability_gate` + `storage_entry_cost_normalized_rank`,
gated default-off, matrix rows registered; A/B driver probe). Both new fields ride
`run_capacity_hindcast.py`'s None-drop dict — "OMIT inherits the shipped defaults so the
control arm's cache key is untouched" — so D12-C's bare control still reproduces the committed
`28cef3500ec1fd9e` bracket. No prompt amendment needed. **Dedup boundary VERIFIED CLEAN:**
their commits touch `model/storage.py`, config, harness wiring and their own probe — no
entry-allocator surface, no `entry_margin_exhaustion`/`entry_forward_reserve_leg`. The ERCOT
matrix-shard rebase-care watch item stands.

**5. S-4b LANDED MID-REFRESH (PRs #4392/#4396, `claude/capx-s4b-neiso-ara-3jhedd`) — VERIFIED,
AND THE PRE-DECLARED FLIP-BACK DID NOT MATERIALIZE.** `FINDING-capx-s4b-neiso-ara-2026-08-30.md`:
- **The companion was LOCATED** (2026 CELT 4.1 CSO summary, column labelled "Includes ARA 3
  Results") — the "ship nothing" clause did not fire. Intake = FOUR values, zero free
  parameters, sha256-pinned sources: requirement factor 1.0024544 → **1.0286103**, DR fraction
  0.09701 → 0.08784, firm-import credit 567.0 → **409.31 MW** (same-cycle pairing rule; ARA-2
  2027/28 values on the record, not adopted).
- **The move is LARGER than charter-declared** (+651…686 MW/yr of requirement + −157.7 MW of
  import credit, vs the ≈+380 MW estimate), in the honest direction. The §4 arithmetic
  re-opened 2028 (−280.4) AND 2029 (−365.7) — yet **measured I7 holds PASS ×5**
  (+3,374.8/+810.2/+419.0/+333.6/+1,197.5 MW): the reliability floor (same requirement, second
  verb) answers the higher requirement by RETAINING **699.3 MW of 2027 gas-CC exits** (8
  tranches named; the exact mirror of S-4V's 324.9 MW loosening). Decomposition closes ≤0.1 MW
  every year; the control reproduces the S-4V ledger BIT-FOR-BIT (zero epoch drift — first
  NEISO lane with no drift disclosure needed); 2026 base-year isolation EXACT (−808.6 = −651.0
  − 157.7, endogenous response 0.0). Backstop did NOT fire (0 MW, builds identical both arms).
- **Bare `neiso-t1f` → PROMOTE-WITH-CAVEATS with STRICTLY FEWER caveats: FC-1 PASS (14/14 —
  the lone I12-2026 WARN cleared mechanically on the re-derived band), FC-2 PASS, FC-7 CAVEAT
  (program-wide DOF ledger), FC-8 PASS. Leg (b) does NOT flip back — it STRENGTHENS.**
  Preserve-then-overwrite honored: S-4V vintage kept at `neiso-t1f-s4hydro`, control at
  `neiso-t1f-s4bcontrol`; board NEISO block refreshed with D14's leg-(c) content verbatim.
- **Honesty notes carried at full magnitude (quote them with the clearances):** the 2028/2029
  I7 margins are FLOOR-DEPENDENT (+419.0/+333.6 riding on the 699.3 MW retention; without it,
  −280/−366), and each successive measurement has moved them DOWN (+545→+419, +469→+334). The
  floor is a standing structural mechanism (spec §5.2) measured against a zero-drift control —
  not a tuned input; nothing was re-tuned, the 0.7352 hydro factor untouched.
- **CONSEQUENCE: the Q11 hold is RESOLVED — the leg-(d) decision card is DUE and PRESENTED at
  THIS sitting** (§3 Q13). NEISO's legs: (a) pass · (b) pass, strengthened · (c) pass ·
  (d) none. Campaign cost (FF-3E): ~1.0 h full-horizon, ~4.3 GB — the cheapest in the program.

**6. D12-C IS MID-EXECUTION (not concluded):** its PREDECL commit landed (PR #4394,
`bf5e08f`) — verdict criteria V-1…V-5 with ex-ante tolerances ($0.05/MW-yr margin
reproduction; every tested margin ≥$5.7k from zero) committed BEFORE either invocation
launched, and the A/B probe extended with `--expect-delta` hard-gating the two-field arm as
the single logical delta. The confirm-vs-contradict record is still to come — the Q10
auto-arm-on-confirmation stands. **S-123: no branch, no landing.** The one deconfliction
delta for in-flight prompts: audit-track branch `claude/ercot-243-release-exit-r7owkv` open
(0 unique commits), covered by start-time `ls-remote` checks.

**7. S-6 / HEAVY SLOT:** caiso-224's **B1-arm solves are COMPLETE and committed** (PR #4395:
full `caiso224_b1_fsno` bundle slim files — 2023/24/25 system parquets, legitimacy
diagnostics, meta, run_config — plus the split-witness/F1-F2 artifact), but the lane is
UNCONCLUDED (no registration, no finding; further arms possible). No heavy solve is
*verifiably* in flight → S-6's release put to the owner at this sitting (they know whether
the caiso-224 session is still running) rather than guessed. Held pending that answer.

**8. BACKCAST/AUDIT MOVEMENT (watch only):** PJM stage-0 golden captured (`29a9cba`,
audit-track owner card 1 — pjm-162-inputclock 2023–2025, 256 flags/713 config keys, 0
drifted). **nyiso-160 CONCLUDED its records** (PR #4393): Leg-2 stop annotations finalized,
touchpoint-prep audit replay registered (keeper bit-identical at HEAD) — NYISO marker
re-entry remains an open backcast-track question. Keepers, markers (`complete`={NEISO, PJM}),
`final` EMPTY, tier-scoped freeze: all verified UNCHANGED at `a305f46`.

**9. THE r#17 SITTING — TWO RULINGS (§3 Q13/Q14):**
- **Q13 — NEISO leg (d) AUTHORIZED: the T3 BAU golden, 2026–2050, ~1.0 h / ~4.3 GB, this
  campaign only.** The FIRST §2.1b gate opening in program history, granted on S-4b's measured
  result exactly as Q11 sequenced it. Lane **T3-NEISO-GOLDEN** issued (pack-canonical):
  zero config invention (HEAD defaults + `--golden-posture --full-solve-authorized`), forecast
  namespace registration (`neiso-2026-2050-t3-golden-bau`), board leg-(d)/gate stamp citing
  the ruling, caveats carried verbatim, failure-record-is-the-deliverable clause.
- **Q14 — caiso-224 ran out mid-completion; the owner directed the director to draft the
  finisher (RECORDED BOUNDARY EXCEPTION: backcast-track completion work, chartered on
  explicit owner request — not a standing widening of the director's charter).** Lane
  **CAISO-224-FIN** issued (pack-canonical): ZERO-SOLVE — all solve artifacts committed;
  executes `PRECOMMIT-caiso224-fsno-arm-2026-08-30.md` §5/§6 faithfully. Director verified
  the committed record before drafting: **F1 fires all three years** (NP15↔FSNO binding
  0.3054/0.3547/0.3380 vs the 0.27 DMM ceiling) **and F2 fires** (arm split vector
  [1556,1359,1186] strictly year-ordered vs reality's non-monotone [1310,1691,1347]) ⇒ per
  the precommit's own rule the static DMM-cap arm reads **R for keeper purposes** — the
  owner's "mid keeper promotion" recollection does not match the pre-registered record, and
  the prompt binds the finisher to the precommit, never the recollection (a K reading stops
  for an owner card; the keeper is untouched either way). The honest headline both ways: the
  split RESTORATION is real (52/40/17 → 1556/1359/1186 vs reality 1310/1691/1347) AND both
  falsifiers fire. **S-6 → RELEASED-CONDITIONAL on CAISO-224-FIN landing** (its own prompt
  stays pack-canonical, unchanged).

## 0m. Refresh #16 (2026-08-30, HEAD `b5050e9`) — pre-launch check: the r#15 wave (D12-C · D5-R · S-4b · S-123) is CURRENT VERBATIM; backcast-only movement

**1. WAVE VERIFIED CURRENT.** No capx branch exists at `b5050e9`; the forecast surfaces
(`program-status.json`, `ff-verdicts.json`) are untouched since D14's board edit (`a65d4e5`).
All four prompts launch as written. Minor staleness, harmless by construction (each prompt
checks `git ls-remote` at start): D12-C's deconfliction line lists ercot-242 as in flight — it
has since CONCLUDED. S-6 STAYS HELD: caiso-224 is still actively solving (B1-arm 2023 sidecar
checkpoint landed this window).

**2. BACKCAST MOVEMENT (watch only, nothing touches this track's gates):**
- **NYISO keeper PROMOTED → `2026-08-30-nyiso-159-loss-surface`** (owner ruling; the measured
  zonal loss-surface A/B registered `nyiso-159-loss-{control,surface}`; fail set NARROWS;
  status part rebuilt after the frontier-withdrawal merge). Marker stays withdrawn — re-entry
  still requires a CALIBRATED keeper (Q5-W).
- **nyiso-160: winter-intake Leg 2 STOPPED WITH CAUSE — the AORR files are unproducible**;
  touchpoint-prep audit method recorded. WATCH: Leg 2 was the designated route back to
  CALIBRATED and marker re-entry for NYISO; with it stopped, the re-entry route is open
  question territory for the BACKCAST track (not this track's to charter), and the NEISO-led
  gate board is unaffected.
- **ercot-242 CONCLUDED** (room-axis Phase-1 armed probe REJECTED-AS-ARMED on its own gates,
  registered + escalated, matrix cell R; branch deleted). **ercot-243 opened and STOPPED at
  Phase-0 census** (population = h3068-2024 alone; K-1/K-3 kills fire — precommit discipline
  again). **o7 CLOSED** (HP-1 holds; the pricing channel ≈ zero; audit row closed).
  **miso-191** (miso-190's binning-aware successor) landed its PREREG + delivery commits and
  its branch is deleted — no MISO backcast branch in flight, S-123's check still passes.
- In flight at `b5050e9`: `caiso-backcast-next-run` (caiso-224) ONLY.

## 0l. Refresh #15 (2026-08-30, HEAD `a6e68e2`) — the ENTIRE four-lane wave LANDED (D13 · D14 · D12 · D5); NEISO is the first (a)+(b)+(c) ISO; three rulings (Q10/Q11/Q12); D12-C + D5-R chartered; S-4b + S-123 RELEASED

**1. WAVE OUTCOME — four dispatched, four landed, second consecutive 100 % cycle:**
- **D13 LANDED** (PR #4372): Q7 executed (ERCOT/PJM/MISO leg (c) fail → pass-on-measurement),
  S-5's PJM restatement applied (366 MW → 5,858 MW), D11-R/Q8 stamped, stale headline/gate_reading
  repaired, rule-27 blob verification recorded in the finding.
- **D14 LANDED** (PR #4376; `FINDING-capx-d14-neiso-t1x-2026-08-30.md`): NEISO's first-ever
  T1-X registered (`neiso-t1x`, FC-4 FAIL measured at full magnitude, quarantine PASS) —
  **NEISO IS THE FIRST ISO IN PROGRAM HISTORY WITH (a)+(b)+(c) ALL SATISFIED; only leg (d)
  remains.** Substantive findings: (i) NEISO is the SECOND no/low-coal counter-example
  (co2 +12.8/+10.6/−2.3 %), confirming D5's mechanism; (ii) **first crossover leg whose window
  executes economic exits** — and it shows a retirement COMPOSITION miss (gas_cc over-retired
  3.128 vs 1.884 GW actual; biomass/coal/gas_ct/oil exits missed entirely, recall 2/6);
  (iii) price miss concentrated in 2025 (−21.8 %), the same sign-flip year as NYISO.
- **D12 LANDED** (PR #4373; `FINDING-capx-d12-scarcity-basis-2026-08-30.md` + PREDECL): the
  adjudication is DECISIVE with zero solves — the shipped realized-prior-year reserve leg is a
  **cross-year phantom** (entering-2024: both gas margins NEGATIVE under the entering year's own
  expectation — gas_cc −$10.7k, gas_ct −$42.7k/MW-yr — yet 6 GW built on the phantom;
  entering-2025 repeats it at −$118.6k/−$111.4k with the realized annuity ≥ 4× the forward
  leg's maximum). Everywhere else the consistent basis changes NOTHING that was right
  (bang-bang ledger RM path unchanged; scored gas bands improve, CT |err| 3.879 → 0.879); under
  it the exhaustion rule's gas half goes live via the exact identity `r_walk = adder_current`.
  Shipped `entry_forward_reserve_leg` default-OFF, byte-identical off. Recommended arming BOTH
  fields together (§7 card).
- **D5 LANDED** (PR #4374; `FINDING-capx-d5-crossover-co2-2026-08-30.md`): the three-ISO
  crossover CO2 miss is a **SCORING-TAXONOMY DROP, not a model defect** —
  `score_crossover.py::model_co2_mt_fullplant` iterates bench intensity keys (coal-rank grain)
  so the model's generic-`COAL` generation contributes ZERO to scored CO2. Explains MISO
  97–117 % of the miss, PJM 75–98 %, ERCOT 46–103 %; NYISO control exactly zero; NEISO (D14)
  the confirming second control. **The forecast emission-rate derivation is EXONERATED**
  (own-rates within ±5 % of same-year bench intensities, every ISO-year). Third instance of the
  known class-grain seam (the other two already patched). Repair + pre-declared re-score table
  in §5.
- **miso-190 CONCLUDED** (PR #4370): the partial-plant exit-carry arm was **REJECTED on its own
  pre-filed S-1 kill**, both A/B legs registered, matrix cell U → R, keeper unchanged
  (miso-188-rvsscope), branch deleted. The PREREG discipline holding again.

**2. THREE OWNER RULINGS AT THE r#15 SITTING (decision cards — §3 Q10/Q11/Q12):**
- **Q10 (the Q8 re-decision) — CONFIRM-PAIR, THEN ARM.** Lane **D12-C** chartered: ONE
  arm-vs-control A/B on the ERCOT T1-H leg at the registered posture with the TWO fields
  (`entry_margin_exhaustion` + `entry_forward_reserve_leg`) as the single logical delta,
  measuring the closed loop D12 open-loop-predicted. **Arming auto-executes on a confirming
  record** (both flip to ERCOT forecast defaults, honestly described); a contradiction does NOT
  arm and comes back to the owner at full magnitude.
- **Q11 (NEISO leg (d)) — HOLD FOR S-4b FIRST.** S-4b dispatches now; the leg-(d)
  authorization card is RE-PRESENTED on its measured result. Rationale adopted: authorizing a
  campaign against a requirement bar a published filing already supersedes spends the compute
  on a known-stale bar; D14's retirement-composition finding is additional context.
- **Q12 — D5-R CHARTERED, FULL FIX** (D5's preference (a)): map coal to its supply class at
  gmModel-build time via the canonical taxonomy chain (one chain, rule 19), repairing the C1
  fuelmix coal rows (~60 TWh/ISO-yr phantom) in the same stroke; zero-solve re-score of the
  committed crossover bundles with D5 §5.2's pre-declared table as the honesty gate (NYISO
  exact no-op, NEISO ≲0.4 %, MISO coal_twh / PJM gas_twh rows untouched — any control movement
  stops the lane).

**3. RELEASES: S-4b RELEASED** (D14 merged — its gate) and **S-123 RELEASED** (the start-time
check PASSES at last: miso-190 concluded and its branch is deleted — after six consecutive
fails; D9 rides with it). **S-6 STAYS HELD**: caiso-224 is actively solving (hourly sidecar
checkpoints on its open branch) and ercot-242 is in flight — the PJM 8.8 GB no-co-run slot is
not free. Re-check next refresh.

**4. CROSS-TRACK: the audit-program director chartered the T1-H CAPACITY-ENTRY repair lane
(owner card 2 of its own sitting), and the deconfliction is CLEAN BY CONSTRUCTION** — its
precommit's step-0 DEDUP GATE cedes defect D-1 (the bang-bang allocator) to this track's
D11-R/D12 lanes explicitly, scoping itself to the storage leg (D-2+D-3) and wind leg (D-8/B-3).
Watch item: D12-C's arming (if confirmed) moves ERCOT forecast defaults under that lane —
its Phase-1 runs at its own registered-posture controls, so no collision, but both lanes touch
the ERCOT matrix shard (rebase care). Also executed at that sitting: **NYISO's frontier
declaration REVERTED (frontier = {PJM, NEISO})** with a machine-readable
`frontier.withdrawn` mirror in the keeper shard (keeper-auditor pass), and a cross-lane
re-grade rule. Backcast: ercot-242 opened (SCED room-axis extension of the armed RT wall,
`rt_room_path` gated field, precommit-first; branch in flight); caiso-224 A0 control complete
(G-CTRL bit-zero vs the caiso-220 keeper sidecars) with the FSNO variant seam landing; o7
delta-equality control scoped. — r#13 batch verified CURRENT (none dispatched yet); D5 issued as the wave's addition; backcast-only movement

**0. DISPATCH CONFIRMED (owner, 2026-08-30, post-r#14): D13, D14, D12 AND D5 ARE ALL IN
FLIGHT** — the full four-lane wave launched at once (largest concurrent capx set to date; all
light/zero-solve, no shared heavy slot; the one surface overlap, D13/D14 on the NEISO board
block, is handled by D14's rebase instruction). S-4b remains staged strictly behind D14's
merge; S-123 and S-6 stay held on Q9 (miso-190). Next refresh: check all four for landings,
merge-behind gaps, and cross-lane merge conflicts on program-status.json / ff-verdicts.json.

**1. THE r#13 BATCH IS CURRENT VERBATIM.** No capx branch exists at `1421c4a` (D13/D14/D12
undispatched; S-4b staged behind D14) and the surfaces they edit are untouched since r#13:
`program-status.json` and `ff-verdicts.json` last moved at D10's merge (`158a688`), so D13's
edit list is exact, D14 displaces nothing, and D12's evidence set is unchanged. The director
r#13 commit merged cleanly (PR #4362, no merge-behind gap).

**2. D5 ISSUED — the three-ISO crossover CO2 derivation question, now fully evidenced.**
D10's NYISO measurement (co2 10.1/10.3/3.9 %) completed the scope D2-B's re-scope predicted:
the 43–76 % miss is ERCOT/PJM/MISO's, and the discriminant hypothesis (what the three share
and NYISO lacks — a material coal fleet; the coal_twh crossover rows FAIL in ERCOT and PJM) is
PRE-DECLARED in the charter as a hypothesis to test, not assume. Zero-solve attribution lane
on the committed crossover bundles; no board edit (D13's or a later refresh's job); no tuning.

**3. BACKCAST MOVEMENT (all of it — no forecast-surface touches):** ercot-239 r2/r3: the
graded-ladder arm was A/B-REJECTED on its own kills (officials collapse to pre-k33; spur
74→11), escalated, and the owner sitting adjudicated promotion NOT RECOMMENDED — keeper
unchanged; h3068-2024 attributed (event-exit lag). ercot-241 phase-0 measured the off-core
conduct screen — kills clear, Phase-1 gate OPEN. caiso-224 minted `caiso_fsno_subzonal_topology`
(gated default-off, matrix row by its own lane) + G-CTRL comparator probe; branch in flight.
nyiso-159 landed `nyiso_zonal_loss_surface` (measured delivery-factor surface, PREREG-first).
Audit-records v15 cycle executed (four rulings, zero promotions).

**4. Q9 CHECK RE-RUN: miso-190 head unchanged (`9cd6dc6`), A/B still unregistered — STILL
RUNNING. S-123 fails a SIXTH consecutive check; S-6 stays held.** Housekeeping: the
`capx-s4-neiso-hydro-syqu7m` branch is a fully-merged stale leftover — safe for the owner to
delete. In-flight backcast branches: caiso-224, ercot-241, miso-190 (D12's start-time
deconfliction covers the ERCOT one).

## 0j. Refresh #13 (2026-08-30, HEAD `f9eb73c`) — ALL FIVE in-flight lanes LANDED (D10 · S-4V · S-5 · Q5-W · D11-R); NEISO takes the program lead with (a)+(b) both PASS; three owner rulings; D12/D13/D14 issued

**1. THE ENTIRE IN-FLIGHT SET CLEARED IN ONE MERGE WINDOW — five lanes, zero refusals, every
deliverable where its charter said it would be.**

- **Q5-W LANDED** (PR #4343, `ecc2d60`; `docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md`):
  NYISO's `complete` marker WITHDRAWN on the r#12 ruling, both surfaces in one session —
  `complete` = **{NEISO, PJM}**, board NYISO gate (a) PASS → fail. Keeper nyiso-157 untouched;
  validation-tier authorization lapsed with the marker; re-entry = new owner declaration on a
  CALIBRATED keeper (winter-intake route).
- **S-4V LANDED** (PRs #4337/#4353): the verification pair ran at one HEAD and **the bare
  `neiso-t1f` key flips HOLD → PROMOTE-WITH-CAVEATS** (treatment: I7 PASS all five years, sole
  WARN the pre-declared I12-2026 17.1 % vs 15.2 % cap; FC-1/FC-2/FC-7 all CAVEAT-not-FAIL).
  **Honest attribution recorded on the record: the CONTROL arm ALSO clears 2028 — epoch drift
  alone flips the year — so the flip is NOT solely S-4's factor; the factor's isolated effect is
  exact** (control preserved as `neiso-t1f-s4control`). Board NEISO block refreshed and the
  `hydro_accreditation` matrix cell re-stamped O → K by the lane itself. S-4's finding §5/§8
  TBDs filled. **S-4b UNBLOCKS.**
- **S-5 LANDED** (PR #4340; `docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md`):
  hold-last-FPR implemented as the declared convention in `resolve_forecast_pool_requirement`
  (card C-A cited in code; zero DOF — the held value is the table's own last published entry),
  D-1 checker year-threading repaired (I7/I12 now grade the same bar the model builds to), and
  **PJM's 2030 I7 miss restates 366 MW → 5,858 MW (3.39 % of peak), 2029 plausibly joining**
  (flagged inference; S-6 measures it). No solve, no registration — the FINDING is the
  director's D7-class input, so **the board's PJM block restatement is OWED → carried by D13**.
  Rule-23 check done on publication terms: 2029/30 BRA is Dec 2026; intake pointer at the table
  edge. **S-6 UNBLOCKS** (held on the heavy slot, §0j.3).
- **D10 LANDED** (PR #4354; `docs/handoffs/FINDING-capx-d10-nyiso-t1x-2026-08-30.md`): NYISO's
  FIRST-EVER T1-X (`nyiso-2023-2027-crossover-capxd10`, ~10 min, <3 GB, shipped posture verified
  in the resolved config), **FC-4 measured and reported at FULL MAGNITUDE: FAIL** — price 2023
  +29.9 % / 2024 +2.5 % / 2025 −24.0 %; **co2 10.1 / 10.3 / 3.9 % — NYISO does NOT reproduce
  the program-wide 43–76 % crossover co2 miss** (D5 evidence: the derivation question is
  ERCOT/PJM/MISO's, not universal). Quarantine PASS (no H1-2026 read). Registered `nyiso-t1x`
  with run_config.json (no D8 debt). **Leg (c) closes on measurement: NYISO gate now
  (a) fail · (b) PASS · (c) PASS · (d) none.**
- **D11-R LANDED** (PR #4355; `docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md`):
  `entry_margin_exhaustion` shipped default-OFF (one field, both allocators, rule 19; matrix row
  + all-shard cells), zero-DOF confirmed (the walk re-invokes `runner._lookahead_reprice_signal`
  itself, delta-anchored; byte-identical off). A/B on ERCOT T1-H at the registered posture,
  control reproduces the committed bracket EXACTLY (RM 19.00→8.54→14.65→25.19, additions
  verbatim). **Four-anchor terminal RM: shipped 25.19 / disarm 40.24 / fwd-exp 40.38 / offline
  18.7 / LIVE ARM 22.02 % (−3.17 pp). B-2 cobweb SURVIVES** (−12.65/+5.20/+10.47 vs
  −10.46/+6.11/+10.54) — the implementation-sanity test passed. Named degradation vs offline:
  **the live reserve leg keeps the GAS half inert** (gas builds to caps in both arms; the
  prior-year realized ORDC leg carries the margin past exhaustion), so arming now = honest
  split "margin-exhaustion for VRE/storage, bang-bang for gas". Both arms registered
  `ercot-2021-2025-realized-t1h-d11r-{control,exhaustion}` with run_config.json; ERCOT matrix
  cell **O** (measured, owner escalation). Finding §5 recommends HOLD arming until D12. **D12
  RELEASES** (the r#8 ratified sequencing is satisfied — D11-R has reported).

**2. THE PROGRAM LEAD PASSES TO NEISO — the second ISO ever to hold (a)+(b), and the first to
hold them simultaneously with a live marker.** NEISO: (a) PASS (`complete` member, CALIBRATED
full-span keeper neiso-99-joint-p1) · (b) PASS (PROMOTE-WITH-CAVEATS on bare `neiso-t1f`) ·
(c) fail — the ONLY genuinely-unrun T1-X among the measured reading's fail set · (d) none.
**A NEISO T1-X (D14, issued this refresh) would make NEISO the first ISO in program history
with (a)+(b)+(c) all satisfied, leaving only leg (d) — the explicit owner authorization.**
NYISO holds (b)+(c) but fails (a) on the withdrawn marker.

**3. THREE OWNER RULINGS AT THE r#13 SITTING (decision cards, this session — §3 Q7/Q8/Q9):**
- **Q7 — leg-(c) semantics: MEASURED CLOSES THE LEG** (charter-literal §2.1b(c) + card A-A as
  signed). ERCOT/PJM/MISO leg (c) flips fail → pass-on-measurement (their FC-4 FAILs stay
  reported at full magnitude); NYISO's D10 PASS stands. The D7-era in-band reading is
  superseded; D10's cell claim about the other ISOs becomes true once D13 executes. Discovered
  and escalated this refresh: the board carried BOTH readings simultaneously (D7 wrote the
  measured ISOs fail-on-band; D10 wrote NYISO pass-on-measurement citing the others as pass —
  false at the time of writing).
- **Q8 — D11-R arming: HOLD until D12 adjudicates the scarcity basis** (the finding's own §5
  recommendation). Matrix cell stays O; the A/B is the standing measured record; re-decide on
  D12's report.
- **Q9 — miso-190: STILL RUNNING** (branch fully merged at `9cd6dc6` but the A/B solve is not
  yet registered — scorer committed before it runs). **S-123 start-time check FAILS a FIFTH
  time; S-6 held on the same heavy slot** (PJM 8.8 GB / MISO 9.6 GB are no-co-run). Both re-run
  next refresh.
- Also verified this sitting: the top-level board prose (headline/gate_reading) is STALE against
  its own NEISO/NYISO blocks — still says "no ISO holds (a) and (b) both" and "leg (c) fails
  for all six". D13 carries the reconcile.

**4. BATCH ISSUED (r#13): D13 BOARD RECONCILE (records; executes Q7 + the S-5 PJM restatement
+ D11-R/S-4V/D10 currency + the stale-prose repair), D14 NEISO T1-X CROSSOVER (the D10 analog;
the program's highest-value light lane), D12 SCARCITY-CONSISTENT DELTA BASIS (released by
D11-R's report; its result is the arming re-decision's input).** S-4b's prompt is written and
in the pack, **dispatch strictly after D14 merges** (both edit ff-verdicts.json + the NEISO
board block; S-4b's pre-declared arithmetic: +380 MW requirement vs the +229 MW post-hydro
clearance ⇒ 2028 plausibly RE-OPENS ≈ −151 MW and leg (b) may flip back — reported at full
magnitude if so, factor and requirement both sourced, nothing reverse-engineered). S-6 and
S-123 held on Q9. D5 stays queued, now carrying D10's evidence (NYISO co2 ~10 % ⇒ three-ISO
derivation question confirmed as the right scope).

## 0i. Refresh #12 (2026-08-30, HEAD `65a39e3`) — NYISO keeper → nyiso-157 (NOT-YET, fail set WIDENED); Q5's recurrence clause FIRED and the owner ruled WITHDRAW; FF-2D re-score benign

**1. NYISO'S KEEPER MOVED UNDER THE MARKER AGAIN — the Q5 fact pattern RECURRED.** nyiso-157
PROMOTED the eastern-seam PAR attribution to keeper (`2dc64b5`, PR #4323; keeper-auditor pass
PR #4326): keeper → **`2026-08-30-nyiso-157-par-attribution`**, promotion basis rules 14+1
(all four border-link caps now follow NYISO's measured P-32 schedules under the published PAR
attribution, zero free parameters; first real zonal price separation — CE utilisation
0.381 → 0.784 in 2025, Jan+Feb-2025 cutset binding 34 → 435 h), EXPLICITLY over TWO gate
regressions reported at full magnitude: C3a-2025 −10.8 → −12.0 % and C3b-2025 joining at a
knife-edge 0.203 vs the 0.20 bar (zero-delta control 0.197). Determination **NOT-YET on
{C3a, C3b, C3c}** — the fail set WIDENED — re-verified per D-5(b) without a solve, the stop
resolved by the owner's in-session standing formula (third application: nyiso-120/155/157).
The marker's own record names the deepened 2025 miss "the winter face of the nyiso-156
two-face object measured on an honest seam"; successor = intake Leg 2.

**2. THE OWNER RULED THE RECURRENCE AT THIS REFRESH'S DECISION CARD: WITHDRAW THE MARKER
(CAISO precedent), against the director's recommendation to adopt the standing formula —
recorded plainly.** The written reconciliation is now UNIFORM: **a `complete` marker cannot
stand on a NOT-YET keeper** (the 2026-08-06 CAISO precedent governs); the
structural-integrity formula remains the standard for KEEPER promotions (nyiso-155/157 stand
untouched as keepers) but no longer sustains a marker. Consequences: `complete` → {NEISO,
PJM} once executed; NYISO gate (a) flips to fail on the marker (leg (b) PROMOTE-WITH-CAVEATS
is untouched — no marker moves a bare verdict); NYISO's validation-tier (2020–2022)
touchpoint authorization lapses with the marker; re-entry is a NEW explicit owner
declaration, expected on the winter-intake route once the keeper again scores CALIBRATED.
**Execution chartered as Q5-W** (governance records lane, NOT a capx lane — it edits
calibration-complete.json + the board's NYISO gate (a), both surfaces in one session so they
cannot disagree; prompt canonical in the pack). Q5 CLOSES on this ruling — the recurrence
clause is discharged by uniformity, not by waiting. **The program's gate-board lead may pass
to NEISO on S-4V's measurement** (NEISO would be the only ISO with (a)+(b) both in reach).

**3. FF-2D RE-SCORE — MY NAMESPACE WAS TOUCHED BY AN OWNER LANE, AND IT WAS BENIGN
(verified, not assumed).** PR #4325 re-scored the 7 re-scorable FF-2D verdicts at HEAD
(`docs/FINDING-ff2d-verdict-rescore-2026-08-30.md`): **every one reproduces
byte-identically**; the diff is provenance-only (`scored_at_sha/date`); the FR-21 staleness
gate resets to Δ=0; the kill-rule did not fire. Bare keys unchanged (nyiso-t1f
PROMOTE-WITH-CAVEATS, all others HOLD). The board's verdicts are now *known* to describe
HEAD — strictly good for this track.

**4. OTHER BACKCAST MOVEMENT:** ercot-239 completed Phase-0 (PR #4331,
`FINDING-ercot239-missedevents-phase0-2026-08-30.md`): the 14-hour missed-event family is
**measured energy-lambda scarcity in tight-room hours no reserve adder carried** — model
ranks 12/14 inside its own bottom-5 % reserve room but prices it $0.00–$25.68; the
precommit's availability/outage/net-load-ramp priors are largely REFUTED (honest
prior-refutation); the object lands on the ercot-217 adjudicated conduct/model-class episode.
A successor **o7 attribution-harness precommit** landed ex ante (PR #4332: fleet-diff
de-laddering, swcap/markup/two-pass composition, HP-1..HP-3). caiso-221's records ARE on
main (verified `599f59b` reachable — the branch deletion lost nothing). Bench hygiene: 8
pre-stamp NEISO/PJM bench parts re-stamped (PR #4321/#4324). The backcast governance
director appended its 2026-08-30 sitting-execution entry (PR #4330).

**5. CAPX LANES: four in flight, nothing pushed yet** (S-4V, D10, S-5 dispatched this cycle;
D11-R since r#10; no capx branch at `65a39e3`). D10's WHY is now doubly stale (cites
nyiso-155 and gate (a) PASS) — the lane fetches fresh state and its charter (card A: close
leg (c) on measurement) is UNAFFECTED by the marker ruling, so it runs to completion; its
closing gate statement will read the live board. **S-123 START-TIME CHECK: FAILS a fourth
time** (miso-190 still the only branch in flight). Queue unchanged otherwise: D12 behind
D11-R's report, S-4b behind S-4V, S-6 behind S-5.

## 0h. Refresh #11 (2026-08-30, HEAD `9405aad`) — S-4's verification pair still owed → S-4V chartered; nyiso-157's Iroquois companion honestly REJECTED; ercot-239 opens

**1. THE FORECAST NAMESPACE IS BYTE-UNCHANGED since D7 (`ca8b749`, 2026-08-26)** — S-4's T1-F
verification pair, FC-1 re-score, leg registration and board refresh did NOT land in the merge
window; the board still shows NEISO FC-1 FAIL on the generic 0.50 the shipped 0.7352 replaced.
**S-4V is chartered this refresh** (the batch's one new lane): control/treatment pair at one
HEAD, FC-1 re-score, forecast-namespace registration (preserve-then-overwrite on the bare
`neiso-t1f` key), completion of the S-4 finding's §5/§8 TBDs in place, the NEISO
`hydro_accreditation` matrix-cell re-stamp S-4's §4 committed to, and the NEISO board block
refresh under D7-class records discipline (delegated to the lane). Expected effect,
pre-declared in the prompt from D2-B's committed arithmetic: hydro term 949.75 → 1,396.5 MW
(+446.7) against the 218 MW 2028 gap ⇒ 2028 clears by ≈ +229 MW on the D2-B basis; a
contradiction reports at full magnitude and never touches the sourced factor (rule 14).
If leg (b) flips on the measured determination, NEISO becomes the SECOND ISO with (a)+(b)
both PASS — its leg (c) then awaits a NEISO T1-X (a future D10 analog). S-4b stays queued
until S-4V lands.

**2. D11-R: still running, still nothing pushed** (no `capx-d11r` branch at `9405aad`;
owner-dispatched at r#10). D12 stays queued behind its report per the ratified sequencing.
D10 and S-5 remain unstarted — re-presented this refresh (D10 is still the highest-value
light lane).

**3. BACKCAST MOVEMENT (three commits since r#10):** nyiso-157 attested C6 on both Leg-1 A/B
bundles (`4d356f8`) and then solved the Iroquois companion arm — **REJECTED on its own
pre-filed W-gates** and registered anyway (`2026-08-30-nyiso-157-iroquois-companion`,
PR #4318; `2026-08-20-nyiso-147a-chp-btm` pruned for top-15 retention). The
prereg-before-solve discipline working exactly as designed: the companion was refuted by
gates frozen before the solve, and the Leg-1 PAR-attribution arm stands on its own A/B
(promotion decision still the backcast track's; branch open). **ercot-239 opened** (PR
#4320): PRECOMMIT-only Phase-0 driver characterization of the 14-hour missed-event family
(2023 carve-out lane object — model < $200 while actual ≥ $500; stated prior:
availability/outage/net-load-ramp representation, not offer curve; zero-solve, precommit
pushed before measurement). caiso-221's records commit sits on its branch unmerged;
miso-190's branch is open.

**4. S-123 START-TIME CHECK: FAILS a third time** (miso-190 in flight at `9405aad`). Held on
the check, re-run next refresh — no owner action needed.

**5. STATE VERIFIED UNCHANGED:** all six keepers as the r#10 watch table (ERCOT two-config
234+236, MISO miso-188-rvsscope, CAISO caiso-220, NEISO neiso-99, NYISO nyiso-155,
PJM pjm-162); `complete` = {NEISO, NYISO, PJM}, `final` EMPTY; freeze tier-scoped to locked
test. Bare verdicts: nyiso-t1f PROMOTE-WITH-CAVEATS, all others HOLD.

## 0g. Refresh #10 (2026-08-30, HEAD `9f73357`) — S-4 LANDED (factor 0.7352, verification pair pending); D11-R RUNNING; ERCOT becomes a two-config keeper

**1. S-4 LANDED — the second capx lane to complete, and it worked exactly as chartered** (PR
#4312, `docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md`). The NEISO hydro class factor
is SOURCED: **0.7352** = ISO-NE's own per-resource summer Seasonal Claimed Capability aggregated
over the active conventional-hydro fleet (August 2026 SCC Monthly Report, 244 assets,
1,396.472 MW) ÷ the model's own 1,899.5 MW accreditation basis — zero free parameters, shipped
as an explicit expression with the committed per-asset extract, provenance README, reproducible
fetch script and tests. The pre-declared direction (recorded before computation: <~0.39 flips
2027 FAIL, >~0.62 clears 2028) puts 0.7352 ABOVE the clearing threshold. **OUTSTANDING: the
T1-F verification pair had not completed at the finding draft** — headline items 2/3 read TBD,
and the forecast namespace is untouched, so FC-1's re-score, the leg registration and the board
refresh are still owed. The finding also surfaced successor work: ISO-NE's Nov 21 2025 ARA
filing implies **≈ +380 MW of requirement** (bigger than the old 218 MW gap) — queued here as
**S-4b** (NEISO requirement re-vintage on publication, rule 23), to be chartered once the
verification pair lands. The FCA-vintage half of S-4's own charter closed honestly as NO-SWAP
(CCP 2028/29 not yet published).

**2. D11-R IS RUNNING** (owner-dispatched this cycle; no branch pushed at fetch time). Its
prompt was merged one amend behind the final pack text — the D11-R deconfliction paragraph in
main still carries the stale "LIVE RIGHT NOW / three backcast sessions" snapshot (cosmetic; the
lane fetches fresh state regardless). Re-applied to the pack this refresh for the record.

**3. ERCOT IS NOW A TWO-CONFIG KEEPER** (owner ruling 3 of the 2026-08-26 sitting, executed
`db8836a5`): **forward keeper `2026-08-25-234-eastex-identity`** — "the configuration the MODEL
USES GOING FORWARD, forecast lane included"; CALIBRATED on its designated 2024–2025 span with
C3c the lone ledgered caveat ×2; its registered 3-year determination (NOT-YET on C3a/C3b-2023,
both 2023-only) stands untouched — plus the **2023 carve-out `236-swcap-clip-k33`**. Capx
consequences: (a) ERCOT's forecast-lane config of record is now eastex-identity — D11-R is
unaffected (it A/Bs both arms at its own fetched HEAD, which carries the eastex repair);
(b) the Q6 terrain moved by owner act, and Q6 stays RULED-HOLD — whether the two-config
structure satisfies §2.1b(2)(a)'s full-span requirement ripens only if a `complete` declaration
is ever considered, and is noted here rather than re-opened; gate (a) still fails on the absent
marker regardless.

**4. BACKCAST MOVEMENT:** **nyiso-157 registered the Leg-1 A/B** (control
`2026-08-30-nyiso-157-par-control` + arm `-par-attribution`, 2023–2025): the PAR attribution
restores a real downstate gradient — NYC−UW annual mean $0.59 → $10.00 in 2023 (measured
gradient ≈ $14.8), C3a-2023 +6.8 % → +1.0 % — and the Iroquois companion prereg is filed BEFORE
its solve; the lane continues (branch open, promotion decision the backcast track's). miso-190's
mechanism landed (`partial_plant_exit_carry`, gated default-off, unit-grain mid-window exits;
A/B scorer committed before it runs; branch open). caiso-221 killed the south-belly
surplus-pricing design object with measurement (branch open). Card 10: decision-1 (warm-start
flip) closed as CLOSED-OVERTAKEN.

**5. QUEUE STATE:** D10 remains the highest-value unstarted light lane (closes NYISO leg (c) on
measurement). **S-123's start-time check FAILS again** (miso-190 branch open) — held on the
check. S-5 ready (heavy re-score self-gates). S-4b queued pending S-4's verification pair. D12
queued behind D11-R per the ratified sequencing.

## 0f. Refresh #9 (2026-08-30, HEAD `a53b7b3`) — freeze goes TIER-SCOPED (card 6 executed); rubric v3.5 determination-neutral; still no capx lane started

**1. THE HOLDOUT SPEND FREEZE IS NOW TIER-SCOPED** (owner ruling 2026-08-26 card 6, executed
2026-08-30, `0589b6f`; record `docs/FINDING-holdout-governance-2026-08-26.md`): `active: true`
with `scope.tiers = ["locked_test"]` — the VALIDATION tier (2020–2022) is lifted from the freeze
and governed by the `complete` marker + `--holdout-authorized` alone, so the diagnostic
touchpoint loop is actually runnable for {NEISO, NYISO, PJM}; the locked test (2019/H1-2026)
stays frozen for every ISO and `final` stays EMPTY. Card 7 (`3643318`) added the standing
scheduling precondition to rule 22: an ISO is *eligible to be considered* for `final` only after
its 2020–2022 touchpoints have run and the loop has stopped surfacing repairs — eligibility is
never a grant. The CAMPD economic-layup charter is CLOSED WITH CAUSE in the same ruling (the
detector question stays open as a documented seam every keeper's availability envelope inherits).
**Director consequence: every pack prompt's freeze guardrail is updated to the tier-scoped
phrasing this refresh** — a capx lane touches neither tier, but this track does not quote stale
governance state. **Nothing else changes for capx lanes**: forecast-mode 2026+ stays
unrestricted, and no capx lane ever solves an out-of-training backcast year.

**2. RUBRIC v3.5 RESOLVED THE STANDING WATCH ITEM HARMLESSLY.** The xiso-6 diurnal
price-amplitude decision card (watched since r#6 as "could touch six determinations") was ruled
option (B): amplitude added REPORTED-ONLY and BAND-FREE — measured, published, no status, no
budget — and **re-verified determination-neutral over the 2026-08-30 six-keeper roster**
(`rule-history.md` changes table, 2026-08-30). Watch item CLOSED.

**3. BACKCAST MOVEMENT:** CAISO keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (the caiso-200
recipe replayed on the now-ACTIVE measured membership crosswalk — caiso-200 no longer reproduces
at HEAD; promoted by owner act on the pre-registered rule; CAISO holds no marker, no re-key due).
**miso-190 is in flight** (branch open: the partial-plant mid-window exit carry, miso-188's
named-not-built successor; PREREG frozen before the mechanism exists — the lane keeps validating
the S-123 hold). NYISO Leg-1 (eastern-seam PAR attribution) branch still open, nyiso-157 A/B
gate scorer filed before its solves. ERCOT: the O7 P0-seam Phase-0 landed ("restoration
escalates, exposure is inherent") plus two governance rulings (G-SPUR lidless count; the ≥$1,000
band-count 59 → 61 correction) — no ERCOT branch currently open. Forecast namespace:
**byte-unchanged**; board still NYISO (a) PASS · (b) PASS · (c) fail · (d) none, all others HOLD.

**4. CAPX LANES: none started** (no `capx-*` branch at `a53b7b3`). The r#8 batch stands: D10 +
D11-R + S-4 to dispatch (all light). S-5 ready — its heavy re-score self-gates on a free slot,
so it is safe to start as a fourth session any time. **S-123: the owner's hold-until-r#9 expired
and the r#9 start-time check FAILS** (miso-190 in flight) — it stays held on the check itself,
re-run every refresh; no new owner decision needed.

## 0e. Refresh #8 (2026-08-30) — no capx lane started; NYISO winter intake AUTHORIZED (backcast track); D11 RE-SCOPED to the D-1 volume rule

**1. NONE OF THE FIVE STANDING PROMPTS HAS BEEN STARTED.** `git ls-remote` at `d8d08ac`: no
`capx-*` branch exists. D10, D11, S-123, S-4 and S-5 all stand written in the pack. The board,
verdicts, markers and freeze are unchanged from refresh #7: NYISO (a) PASS · (b) PASS ·
(c) fail · (d) none, everyone else HOLD on FC-1; `complete` = {NEISO, NYISO, PJM}; `final` EMPTY;
holdout spend freeze ACTIVE. (Keepers: MISO moved mid-refresh — item 4.)

**2. BACKCAST MOVEMENT — nyiso-156b: the owner RULED the nyiso-156 card's Q1 as OPTION A, the
winter locational identification intake is AUTHORIZED** (PR #4295, `ab0513e`; spec
`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`). Two legs: **Leg 1** — the
eastern-seam PAR attribution from NYISO's own published NY-NJ PAR interchange percentages
(**session-executable, the owner gate on PREREG-nyiso126 is LIFTED**; adds an ABC→NYC AC border
path the model does not carry); **Leg 2** — MyNYISO as-enforced AORR access (owner-executable,
fail-closed). The ruling also corrected the stale "seam unidentifiable" record: nyiso-125's
refusal was discharged on identification by nyiso-126 the same day; the leg was
authorization-blocked, not identification-blocked. **Why this track cares — it bears directly on
Q5**: the card's §4 measures that closing the winter face alone (−$3.92/MWh of the annual lw mean)
returns C3a-2025 to ≈ −5.3 % (in band), whereupon C3c reverts to the lone failure, the standing
rule reclassifies it, and the determination returns **CALIBRATED**. Q5's tension (a `complete`
marker on a NOT-YET keeper) now has a live structural resolution path through the owner's own
backcast lane; the precedent-reconciliation question stays worth writing regardless (§3).
Also landed: the bench-fingerprint adjudication (PR #4293 — 11 "stale" bench parts adjudicated
UNLABELLED-not-wrong, measured over the complete builder-drift commit set; backcast dashboard
hygiene, no gate contact).

**3. D11 IS RE-SCOPED TO D11-R — THE D-1 BANG-BANG VOLUME RULE — and the pro-forma signal build
is HELD IN ABEYANCE.** Recorded under the remit refresh #7 claimed (the B-C signature chartered
the OBJECT — what the entry screen is meant to represent — not a particular lane). The evidence
that forces it: `FINDING-entry-signal-forward-expectation-2026-08-25.md` §3 — three signal
constructions spanning a ~$200/MWh swing in the entering-2024 mean produce one trajectory
(terminal RM 25.19 / 40.24 / 40.38 %), *"D-1 owns the trajectory; the signal lane should not be
re-chartered against it"* — and its §7 adjudication recommends exactly this: **"(b) first — rest
the signal lane and charter D-1's volume rule."** The construction is already named and
pre-measured: L-1b's **margin-exhaustion closure** (`FINDING-entry-signal-l1-2026-08.md` §2,
probe `scripts/probes/entry_signal_l1b_allocator_counterfactual.py`) — *build until the screen's
own repriced margin is exhausted, bounded by the same caps* — is the zero-DOF candidate, measured
offline at terminal RM 18.7 % vs the shipped 25.2 % with the B-2 cobweb surviving (real market
dynamics, NOT the target). D11-R productionizes it behind a NEW default-OFF ScenarioConfig field
and A/Bs it on an ERCOT T1-F leg. Margin exhaustion **is** the allocator half of the developer
pro-forma, so this stays inside the B-C charter. The signal-lane successor rung — the
scarcity-consistent delta basis, §4's named successor for the two-scarcity-objects defect — is
**queued as D12**, to run only if the owner continues the signal lane; the owner can override
either disposition at the finding's §7 escalation, which remains open.

**4. DECONFLICTION — THREE BACKCAST BRANCHES WERE IN FLIGHT** at `d8d08ac`
(`claude/caiso-c3a-overrun-closure-5n84mn`, `claude/ercot-backcast-calibration-9wkxrg`,
`claude/miso-188-rubric-failure-tuning-m1ph17`) — **and the MISO one MERGED MID-REFRESH**
(`212308b`, PR #4296): **miso-188 promoted a new MISO keeper, `2026-08-30-miso-188-rvsscope`**
(full-span, single delta `retiree_vintage_status_scope=true` — a NEW gated default-off field with
its rule-28c matrix row + cells minted; drops 28 dark retiree-channel units / 1,434 MW after the
phase-0 audit caught Grand Tower dispatching 4.8 TWh while CAMPD-dark for three years;
**C1 CC_REGULAR-2024 +8.037 → +6.820 PASS; determination narrows to NOT-YET on {C3a-2025}
ALONE**, promoted on the PREREG's own rule). Consequences: CAISO and ERCOT branches remain in
flight, so the ≤2-heavy cap must still be checked before any capx solve launches and D11-R's
deconfliction note stays sharp (ERCOT backcast live). **S-123's hold is DOWNGRADED to a
start-time check**: the MISO backcast lane is momentarily between sessions, so S-123 may start
whenever no new MISO backcast branch is in flight, its optional re-measure still gated on a free
heavy slot (MISO = 9.6 GB no-co-run). The batch issued this refresh stays deliberately all-light:
**D10** (NYISO T1-X, 2.82 GB), **D11-R** (Phase-0 zero-solve first), **S-4** (NEISO, 9.2 min).
S-5 stands ready (PJM quiet on the backcast side) for the next free heavy slot; S-6 strictly
after it.

**5. OWNER SITTING AT REFRESH #8 (2026-08-30, in-session decision cards) — FOUR RULINGS:**
- **Q5 → WAIT FOR WINTER INTAKE.** The precedent conflict (CAISO withdrawal vs nyiso-155
  structural-integrity promotion) is left standing unreconciled; the nyiso-156 winter-intake path
  is the designated resolution route (measured: winter-face closure alone returns the keeper to
  CALIBRATED). No marker moves; gate (a) stays PASS on the literal test. If the fact pattern
  recurs before the intake resolves it, the reconciliation question returns to the owner.
- **Q6 → HOLD, NO ACTION.** No direction is issued to the ERCOT backcast lane; revisit when it
  goes quiet. Gate (a) keeps failing on both counts meanwhile — recorded, not escalated further.
- **SIGNAL LANE → D11-R RATIFIED, D12 QUEUED.** The refresh-#8 re-scope is ratified at the
  finding's §7 escalation: volume rule first; D12 (scarcity-consistent delta basis) is chartered
  only after D11-R reports. The §7 escalation is now RESOLVED — (b) first, (a) queued behind it.
- **S-123 → HOLD UNTIL NEXT REFRESH.** This SUPERSEDES item 4's mid-refresh downgrade to a
  start-time check: the owner holds S-123 one more cycle to see whether a new MISO backcast
  session starts. Re-present at r#9.

**5b. POST-SITTING BURST (same day, `212308b` → `5ce92f4`) — two rulings validated within the
hour:** PR #4298 merged this ledger's refresh-#8 commit; PR #4297 merged the CAISO backcast
branch (caiso-220 records — CAISO no longer in flight); **PR #4299 merged miso-189** (phase-0
zero-solve refuting the Illinois scarce delivered-gas candidate) — a NEW MISO backcast session
did start immediately, exactly what the S-123 hold-until-r#9 ruling anticipated; PR #4301 landed
an ERCOT governance correction (≥$1,000 band count 59 → 61, owner ruling 2026-08-26); and
**PR #4300 shows nyiso-156 LEG 1 (the eastern-seam PAR attribution) ALREADY EXECUTING** —
nyiso-157 filed its A/B gate scorer (K1–K9) before the solves — so the Q5 wait-for-winter-intake
path is in motion, not hypothetical. ERCOT's backcast branch remains the one still in flight
alongside the NYISO Leg-1 branch.

**6. PACK CORRECTIONS with the reissue:** D10's WHY cited keeper
`2026-08-22-nyiso-152-duty-complete, CALIBRATED` — stale since the nyiso-155 promotion; now cites
the NOT-YET keeper with the Q5 posture stated (gate (a) taken as PASS on the literal test, not
re-read downward). Its guardrail "CALIBRATED with an owner-ratified frontier" likewise corrected
(frontier returned to the owner at the promotion). D7's row moves to LANDED (`ca8b749`, PR #4289
— was recorded in §0d but the scoreboard row still read ISSUED).

## 0d. Refresh #7 (2026-08-26) — D7 LANDED; ERCOT is CALIBRATED but 2023-ONLY; D11's premise is undercut

**1. D7 LANDED** (PR #4289, `ca8b749`) — the first dispatched capx lane to complete. Records-only,
two files, no solve. It carried the NYISO re-score onto the board **with the source finding's own
honesty note attached** (the 2026 leg was also flipped by −341.4 MW of epoch demand drift and would
have passed by a thin +332.9 MW without the intake, so the 2,749.9 MW credit buys structural margin,
not the sign), applied the signed card-A leg-(c) harmonisation, and carried the base-year I7
scoring instruction into the board's prose. **It re-read NYISO's four legs against the criteria
rather than asserting them** — including verifying full-span at the keeper's registry years — and
**recorded the Q5 tension while leaving the verdict unmoved**, exactly as chartered.
**NYISO's board gate now reads (a) PASS · (b) PASS · (c) fail · (d) none, `open: false`. No gate
opened; leg (d) is byte-unchanged for all six ISOs.**

**2. ERCOT IS NOW `CALIBRATED` — AND ITS KEEPER IS 2023-ONLY.** Keeper
`2026-08-25-236-swcap-clip-k33` (−7.3 % / 0.102 / 180) scores **CALIBRATED with an EMPTY failing
set** — the 2023 price object that card Y held open on 2026-08-24 has closed. But
`registry/2026-08-25-236-swcap-clip-k33.json` declares **`years: [2023]`**.
→ **Gate (a) now fails for ERCOT on TWO independent counts**: it is absent from `complete`, *and*
§2.1b(2)(a) requires a **FULL-SPAN** keeper (rule 16), which a 2023-only run is not. **This is the
note from refresh #6 becoming load-bearing.** A CALIBRATED determination is necessary but not
sufficient: **declaring ERCOT `complete` would NOT open its gate (a) while the designated keeper
covers one year.** ERCOT would need a full-span (2023–2025) keeper carrying the swcap-clip recipe
first. That is an owner-tier sequencing point, not a director action — **Q6**.

**3. D11's PREMISE IS SUBSTANTIALLY UNDERCUT by a lane I did not charter.** The ERCOT
`entry_forward_expectation_signal` A/B (`94463db`) built and measured a **THIRD** entry-signal
construction. Its result: P1 CONFIRMED (iron_air 3,000 MW enters all four steps), P2 CONFIRMED
(wind 1,092.2 MW enters), but **P3 OVERSHOOT SURVIVES — terminal RM 40.38 % vs disarm 40.24 % vs
control 25.19 %** — and its adjudication is the finding that matters:
**"the trajectory is invariant across all three measured signal constructions and D-1's bang-bang
volume rule owns it."** It also surfaced an unpredicted measured defect: *S_current's pro-forma tail
and the duals' realized overlay are two different scarcity objects*, making the entering-2024
composed level unphysical (mean −$48.22/MWh; solar capture −$185/MWh). Cell stays `O`;
owner decides the next rung.
→ **D11 as chartered would build a FOURTH signal construction against evidence that the signal is
not what owns the outcome.** Its Phase 0 must now absorb this: either re-point at **D-1's bang-bang
volume rule** (the thing measured to own the trajectory) or justify in writing why a pro-forma
construction still earns a session. The B-C signature chartered *the object*, not a particular
lane; re-scoping it on new measured evidence is within the director's remit and is recorded here.
**The "two scarcity objects" defect is itself a strong candidate lane** — it is a physical-coherence
problem in the entry screen's own inputs, not a signal-shape question.

**4. Also landed:** `audit_keepers` gained **check E11 — keeper-lineage recipe fidelity over the
full `solve_and_persist` kwarg surface**, which closes the "silently lost from the keeper lineage"
class that the nyiso-155 hydro repair was a victim of. MISO keeper re-keyed to
`2026-08-26-miso-187-nucavail` (NOT-YET, fuelmix + price_mean; `nuclear_unit_availability` U→K).
CAISO's caiso-220 replay is mid-solve (checkpoints only). ercot-237 Phase-0 band-swap
characterization is zero-solve.

---

## 0c. Refresh #6 — no lane started; three keeper promotions, and NYISO's gate-(a) BASIS moved under us

**1. NONE OF THE SIX PROMPTS HAS BEEN STARTED.** `git ls-remote` at `6af12ee`: no `capx-*` branch
exists except this ledger. D7, D10, D11, S-123, S-4 and S-5 all stand as written
(`docs/handoffs/capx-director-prompt-pack-2026-08.md`); the only thing that moved under them is
`main` (`99c8cf5` → `6af12ee`), which every prompt already handles by fetching fresh.

**2. NYISO'S KEEPER IS NOW NOT-YET, AND IT STILL HOLDS `complete`.** Promoted 2026-08-25:
**`2026-08-25-nyiso-155-hydro-repair`** (the hydro truncated-vintage repair pair
`hydro_backfill_year=2024` + `hydro_eia930_monthly=true`, zero fitted scalars), **NOT-YET on
price_mean + price_tail**. Promoted BY OWNER RULING on structural integrity over gate regression,
with **the D-5(b) worse-determination stop FIRED, ESCALATED, and resolved by that ruling**; the
determination is written explicitly into the marker (nyiso-120 precedent). C3a-2025 −8.1 → −10.8 %
because the truncation had been **masking ~2.7 pp of the real 2025 offer-level object**. **Frontier
status returned to the owner** — the 2026-08-23 ratification's CALIBRATED premise no longer holds.

→ **This moves the BASIS under my refresh-#5 headline, and I state it plainly rather than let it
stand.** Gate (a)'s literal test (charter §2.1b(2)(a)) is *a designated full-span keeper AND an
entry in the `complete` block*, and NYISO still satisfies both, so **gate (a) reads pass on the
test as written**. But the marker now rests on a NOT-YET keeper — **precisely the fact pattern that
withdrew CAISO's marker on 2026-08-06** ("a `complete` marker cannot stand on a NOT-YET keeper").
The two are reconciled only by the owner's explicit ruling. **That is an owner-tier question, not
mine: it is Q5.** Leg (b) is untouched — it is the forecast `nyiso-t1f` verdict
(PROMOTE-WITH-CAVEATS), which no backcast promotion can move.

**3. THE HYDRO TRUNCATION DOES NOT REACH OUR I7 PASS — verified, not assumed.** The backcast repair
fixes a 2025 hydro census truncated to **3 plants of ~147**. The forecast accreditation was already
immune by construction: `modelled_hydro_nameplate_mw` clamps the census to
`EIA923_LATEST_FINAL_VINTAGE`, and its docstring names this exact hazard — *"vintages after it are
monthly early releases carrying only the large reporters … so an unclamped year would accredit a
partial fleet."* So NYISO's forecast hydro credit (1,763.3 MW) was never computed on the 3-plant
vintage, and the extcap I7 PASS stands. **Also verified: the NYISO extcap registry entry survives
intact** at `capacity_market.py:2574` (`3_168.5 * (1.0 - 0.1321)`); the only change to that file
this cycle was CAISO's AS-revenue row.
**A consistency item for D7/D10, flagged not resolved:** the backcast now consumes the *repaired*
hydro input (147 plants, EIA-930 monthly pin) while the forecast consumes the *clamped complete
census*. Two constructions of one physical quantity. Not a defect I have established — a question
worth one paragraph in the next NYISO lane.

**4. ERCOT's keeper is now 2023-ONLY** — `2026-08-25-235-2023-discrete-k24`, NOT-YET on price_mean
(C3a-2023) alone, and **the first ERCOT run with C3b-2023 AND C3c-2023 both PASS**. It is registered
under the **rule-16 waiver the owner granted 2026-08-23, now SPENT**. No gate reading changes
(ERCOT fails gate (a) on the marker regardless) — but note for any future ERCOT declaration that
gate (a) also requires a **full-span** keeper, which a 2023-only keeper is not.

---

## 0. Refresh #5 — NYISO CLEARS FC-1. The program has its first ISO with legs (a) and (b) both passing.

**1. D2-NYISO-INTAKE LANDED and it worked** (PR #4259). NYISO added to
`ADEQUACY_EXTERNAL_TIE_FIRM_MW` on its **own published** external capacity — 2026 Gold Book
Table V-1, Summer-2026 net capacity purchases from external control areas, **3,168.5 MW ICAP,
sha-verified source** — converted to the model's UCAP requirement basis with the **same published
NYCA ICAP→UCAP factor the requirement side applies** (rule 19, one basis): 3,168.5 × (1 − 0.1321)
= **2,749.9 MW**. Corroborated against NYISO 2025 SOM Fig. A-97. Deliberately NOT the 900 MW HQ
dispatch floor, NOT the 4,350 MW Simultaneous Import Limit.
**The pre-declared honesty test passed: the value overshoots the 35.7 MW residual ~77×** — a real
accreditation, not a number tuned to the invariant.
**Re-scored leg `nyiso-2026-2030-extcap-capxd2`: 5/5 years, 14/14 invariants PASS.
FC-1 FAIL['I7'] → PASS. FC-2 CAVEAT → PASS. Determination HOLD → PROMOTE-WITH-CAVEATS.**
The 2026 accredited firm reproduced the pre-solve prediction to the digit (32,085.5 + 2,749.9 =
34,835.4 MW). Honest decomposition disclosed in the finding: HEAD demand drift since the FFR-3A-2
epoch (−341.4 MW peak) alone would have passed 2026 by a thin +333 MW; **the intake moves every
year to a structural +2.9–4.2 GW surplus.** Only remaining caveat is FC-7 — the program-wide
missing DOF-ledger instrument (lane D8).

**2. NYISO's §2.1b gate now reads (a) PASS · (b) PASS · (c) `fail` · (d) none.** *(Leg (c) was
`na` at refresh time; the owner's card-A signature harmonised it to `fail` — §3.)*
`frontend/data/forecast/program-status.json` was last touched 2026-08-24 05:55 and still carries
NYISO as FC-1 FAIL / gate (b) fail. **This is the D7 trigger, and it is immediate.** NYISO is the
first ISO in the program to clear both legs that depend on model quality; what remains is leg (c),
now chartered as a run (**D10**), and leg (d), owner authorization.

**3. D2-B LANDED** (PR #4258) and is the most substantial diagnosis this track has produced.
Three of four legs reproduced from committed artifacts with no solve — MISO 2026 and CAISO
2026–2030 **to the MW**, NEISO to the verdict's own rounding. Headlines:

- **MISO IS THE SECOND NYISO.** It credits **zero** external firm capacity while the forecast path
  floors a **1,400 MW Manitoba firm-hydro block at 100 % in every hour, default-on**. The registry
  now omits **exactly the two ISOs** that fail I7 with a default-on firm-import floor behind the
  miss. The registry's failure mode is **coverage, not basis** — every populated entry is
  accreditation-based and consistent with dispatch.
- **A second MISO defect, provable from the repo's own citation blocks:** the fallback requirement
  multiplies the **PY 2024-25** ICAP PRM (0.179) by the **PY 2025-26** ICAP→UCAP ratio, and that
  ratio's own cited source publishes ICAP 15.7 % / UCAP 7.9 % — contradicting the PRM it is
  multiplied with. Same-document PY 2025-26 pairing puts the requirement **2,637.4 MW lower = 44 %
  of MISO's 6,037 MW gap.** Correctly NOT shipped (solve-affecting, shares machinery with the
  backcast-reachable retirement floor), and routed with its expected effect stated in advance so it
  cannot be back-fitted.
- **NEISO's hydro fallback is load-bearing and decides the verdict's sign.** The generic
  `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50` (no ISO-published NEISO factor exists — an FFR-1C
  open item) contributes **949.75 MW against a 218 MW gap — 4.4×**. A class factor of 0.39 flips
  2027 to FAIL; 0.62 clears 2028 outright. **NEISO 2028 is not decidable at current input
  fidelity** and must be read as "within input uncertainty", not as a capacity-evolution defect.
- **PJM's 366 MW is an UNDERSTATEMENT, and my "PJM is the shortest path to T2" thesis is REFUTED.**
  The requirement factor falls **discontinuously at the published-FPR table edge** (2028→2029):
  beyond delivery year 2028/29 the model falls back to a composite whose IRM half is two vintages
  stale, dropping the bar **3.18 % of peak = 5,492 MW** at the 2030 peak. Against a hold-last-FPR
  requirement — the convention `forward_net_cone_anchor` already establishes elsewhere — 2030's miss
  is **~5.9 GW, not 366 MW, and 2029 plausibly fails too.** Every correction on both sides runs
  against leniency. PJM's supply side is **the one leg no committed artifact can reproduce.**
  *(Owner signed C-A 2026-08-25: hold-last-FPR is now the declared convention — §3.)*
- **CAISO's forks were already adjudicated by FFR-3P** and stand: fork 2 (fleet-snapshot vintage)
  dominates — base-year battery fleet 8,000 MW against a published **14,131 MW NDC**, ≥5,933 MW =
  **90 % of the base-year deficit**. D2-B adds the horizon evidence: the **14,043.6 MW
  administrative-CT backstop ladder and the 65.5 % backstop share are DOWNSTREAM artifacts of the
  input-vintage deficit, not independent defects.** Fix B-1 and most of the ladder never fires.
- **Program-wide:** no base-year I7 leg is a capacity-evolution defect, and neither backstop tuning
  nor floor relaxation is ever the answer to one. Carried into D7 as a scoring instruction.

**4. Method note worth carrying:** an evolution ledger's exits live in **two keys** —
`retirements` *plus* `confirmed_derates`. CAISO 2027 reads 1,491.0 MW in the first and 1,333.0 MW
in the second; summing only `retirements` under-counts the exit wave by 47 %. That is the repaired
I4/A1 leak working as designed — but any decomposition that forgets the second key mis-attributes
the gap.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **D1 BOARD-REFRESH** | Board vs live verdict records; A1/I4 cross-ISO | **LANDED** `c02f766` | `capx-d1-board-refresh-nfb31y` | Opus | 36 fields, 0 gates moved. |
| **D2-NYISO** | Root-cause NYISO I7 | **LANDED** `0a2238c` | `capx-d2-adequacy-nyiso-yxv6v0` | Opus | Adjudicated; shipped no fix, deliberately. |
| **D2-NYISO-INTAKE** | Gold Book external capacity | **LANDED — I7 CLEARED** `3786191` | `capx-d2-nyiso-extcap-sewmyx` | Fable | §0.1. First FC-1 PASS in the program. |
| **D2-B I7 LEDGER DECOMPOSITION** | Reproduce/decompose MISO, CAISO, NEISO, PJM | **LANDED** `5dda152` | `capx-d2b-i7-ledger-xaakeu` | Fable | §0.3. Six successor lanes named (S-1..S-6). |
| **D7-NYISO GATE RE-SCORE** | Refresh the board to the extcap re-score; re-read NYISO's four legs; **apply the card-A leg-(c) harmonisation** (CAISO + NYISO `na`→`fail`, `"c"` into both `closed_on`) | **LANDED** `ca8b749` (PR #4289) | `claude/capx-d7-nyiso-gate` | Opus | §0d.1. Board re-scored, no gate moved, Q5 tension recorded verbatim. |
| **D10 NYISO T1-X CROSSOVER** | Run NYISO's T1-X so gate leg (c) closes on a measured FC-4 | **LANDED** PR #4354 — FC-4 measured FAIL at full magnitude (price +29.9/+2.5/−24.0 %; co2 ~10 %, NOT the program-wide miss), quarantine PASS, registered `nyiso-t1x` with run_config.json; **NYISO leg (c) → PASS on measurement** | `claude/capx-d10-nyiso-t1x` | Fable | Card A's own consequence, executed. D5 evidence: the co2 derivation question is three-ISO, not universal. |
| **Q5-W NYISO MARKER WITHDRAWAL** | Execute the r#12 Q5 ruling: withdraw NYISO from `complete` (CAISO precedent, uniform), flip board gate (a), FINDING + audit | **LANDED** PR #4343 (`ecc2d60`) — both surfaces one session; `complete` = {NEISO, PJM}; NYISO gate (a) → fail | `claude/q5w-nyiso-marker-withdrawal` | Fable/Opus | Keeper untouched (nyiso-157 stands). Re-entry = new owner declaration on a CALIBRATED keeper. Validation-tier authorization lapsed. |
| **D11-R ENTRY VOLUME RULE (D-1)** | Productionize the L-1b margin-exhaustion closure — the measured zero-DOF volume rule — behind a default-OFF field; A/B on ERCOT T1-H | **LANDED** PR #4355 — `entry_margin_exhaustion` shipped default-OFF, zero-DOF confirmed; live arm 22.02 % vs shipped 25.19 (−3.17 pp), B-2 survives; gas half inert on the live reserve leg; matrix cell **O**; **arming RULED Q8: HOLD until D12** | `claude/capx-d11r-entry-volume-rule` | Fable | §0j.1. Both A/B arms registered on the forecast namespace with run_config.json. |
| **D12 SCARCITY-CONSISTENT DELTA BASIS** | Both `S` evaluations on one scarcity basis | **LANDED** PR #4373 — decisive, zero-solve: realized-r leg adjudicated a cross-year PHANTOM; `entry_forward_reserve_leg` shipped default-OFF; exhaustion's gas half goes live via exact identity; recommended arm-both (§7) → **Q10 ruled: confirm-pair then arm (lane D12-C)** | `claude/capx-d12-scarcity-basis` | Fable | Bang-bang RM path unchanged under the consistent basis; CT band \|err\| 3.879→0.879. |
| **D12-C ARMING CONFIRMATION PAIR** | ONE arm-vs-control A/B on ERCOT T1-H, the TWO fields as a single logical delta; **arming auto-executes on a confirming record** (Q10); a contradiction returns to the owner unarmed | **CONCLUDED — CONTRADICTION** PR #4406: V-2 cc window missed (0 vs [750, 1,250]); V-1/V-3/V-4/V-5 + G-1/G-2 all pass; divergence = pre-declaration derivation error (offline walk's restricted candidate set; live solar competition ⇒ MORE exhaustion, same mechanism); nothing armed, cells `O`, both bundles registered; tolerance NOT widened (rule 21) | `claude/capx-d12c-confirm-pair-oji8wv` | Fable | §0o.1. **Q15 re-decision card presented at r#18** — the protocol's own "owner may judge confirming-in-substance" clause. |
| **D13 BOARD RECONCILE** | Q7 execution + S-5 PJM restatement + landed-lane currency + stale-prose repair | **LANDED** PR #4372 — all five edits in; no gate opened; blob verification recorded | `claude/capx-d13-board-reconcile` | Fable/Opus | Board internally consistent again. |
| **D14 NEISO T1-X CROSSOVER** | NEISO's first-ever T1-X | **LANDED** PR #4376 — FC-4 measured FAIL (price +13.3/+7.9/−21.8 %; co2 +12.8/+10.6/−2.3 % — second no-coal control for D5), quarantine PASS, `neiso-t1x` registered; **NEISO = FIRST (a)+(b)+(c) ISO; leg (d) held for S-4b (Q11)** | `claude/capx-d14-neiso-t1x` | Fable | First T1-X with in-window economic exits: retirement COMPOSITION miss surfaced (recall 2/6) — a real successor object. |
| **S-123 MISO ADEQUACY PACKAGE** | S-1 requirement re-vintage + S-2 external-capacity intake + S-3 ledger differencing | **LANDED (complete)** PRs #4397/#4398/#4402 + **#4441 (S-123-V-R, Opus)** — three terms shipped (S-1 −2,637.4; S-2 +3,505.9; S-3a −9,236.8; 2026 position −6,037 → +9,343 MW, 2.5× overshoot, honest); **§6 verification re-measure LANDED at r#21** (registered, board refreshed, finding §6 filled); D9 adjudicated UNREACHABLE + routed | `claude/capx-s123-miso-adequacy-ukgiow` | Fable | §0o.3. Routed to director: the armed-interface **mc=0 seam placeholder** defect (→ D16 queued). Verify §6 fills on its next landing. |
| **S-4 NEISO HYDRO ACCREDITATION** | Per-resource ISO-NE SCC → class factor, replacing the generic 0.50 | **LANDED** PR #4312 — verification half chartered as **S-4V** (r#11) | `claude/capx-s4-neiso-hydro-syqu7m` | Fable | Factor 0.7352 sourced, above the pre-declared 0.62 clearing threshold. Finding §5/§8 TBDs are S-4V's to fill. |
| **S-4V NEISO VERIFICATION** | Complete S-4's owed §5: control/treatment T1-F pair at one HEAD, FC-1 re-score, forecast registration (preserve-then-overwrite on bare `neiso-t1f`), finding TBDs, NEISO `hydro_accreditation` cell re-stamp, NEISO board block refresh | **LANDED** PRs #4337/#4353 — bare `neiso-t1f` HOLD → **PROMOTE-WITH-CAVEATS** (I7 PASS ×5, sole WARN the pre-declared I12-2026); control preserved as `neiso-t1f-s4control`; matrix cell O → K; board block refreshed | `claude/capx-s4v-neiso-verification` | Fable | **Honest attribution: the control ALSO clears 2028 — epoch drift alone flips the year; the factor's isolated effect is exact.** NEISO takes the (a)+(b) lead. |
| **S-4b NEISO REQUIREMENT RE-VINTAGE** | Adopt the published Nov 21 2025 ARA filing pair | **LANDED** PRs #4392/#4396 — companion LOCATED (2026 CELT 4.1 "Incl. ARA 3"); 4-value zero-DOF intake (factor 1.02861, DR 0.08784, imports 409.31); move +651…686 MW/yr, LARGER than declared; **I7 holds PASS ×5** (floor retains 699.3 MW of gas-CC exits — decomposition ≤0.1 MW, zero-drift control, exact 2026 isolation); **leg (b) STRENGTHENS** (FC-1/FC-2 CAVEAT→PASS); 2028/29 margins floor-dependent, noted at full magnitude | `claude/capx-s4b-neiso-ara-3jhedd` | Fable | §0n.5. Q11's hold RESOLVED ⇒ leg-(d) card presented at r#17 (§3 Q13). |
| **S-5 PJM REQUIREMENT HORIZON-EDGE** | Implement hold-last-FPR + the D-1 checker repair; re-score PJM's T1-F leg | **LANDED** PR #4340 — hold-last-FPR in `resolve_forecast_pool_requirement` (zero DOF), checker year-threading repaired, **I7 2030 restates 366 MW → 5,858 MW, 2029 plausibly joins**; no solve, no registration; board restatement carried by D13 | `claude/capx-s5-pjm-horizon-edge` | Fable | The worse reported result, produced on purpose (the card's own arithmetic). 2029/30 intake pointer at the table edge (BRA Dec 2026). **S-6 unblocked.** |
| **S-6 PJM T1-F LEDGER RUN** | The minimum run that makes PJM's supply side observable, against the corrected (hold-last) bar | **LANDED PR #4436 (S-6-R, Opus)** — `pjm-2026-2030-s6-ledger` registered, `pjm-t1f` re-scored, board refreshed; **FC-1 FAIL = {I7, I12}**, three-year I7 fail set measured | `claude/capx-s6-pjm-ledger-r2` | Fable→Opus | §0q.2 + §0r.2. The corrected supply-side bar is now measured, not extrapolated. |
| **D5 FC-4 CO2 CROSSOVER** | Attribute the three-ISO crossover CO2 miss | **LANDED** PR #4374 — miss is a SCORING-TAXONOMY DROP (unmapped model-`COAL` → zero scored CO2): MISO 97–117 %, PJM 75–98 %, ERCOT 46–103 % of the miss; rate derivation EXONERATED (±5 %); controls clean → **Q12 ruled: D5-R full fix chartered** | `claude/capx-d5-crossover-co2` | Fable | Third instance of the known class-grain seam. |
| **D5-R SCORER COAL-GRAIN REPAIR** | Fix the seam at gmModel build (canonical taxonomy chain, rule 19 — also repairs the C1 fuelmix coal-row phantom), zero-solve re-score the committed crossover bundles | **LANDED** PR #4388 — every cell within ±0.2 pp of the §5.2 table; ALL hard controls pass (NYISO byte-identical, family rows deep-equal); PJM+MISO co2 leave the FC-4 FAIL sets, ERCOT 2023/24 stay FAIL honest; fifth bundle (neiso-capxd14) skip adjudicated sound at r#17 (generic-COAL 0.001 TWh ⇒ ~0.004 % bound) | `claude/crossover-co2-grain-repair-oycsy6` + completion `…-t6hoe2` | Fable | §0n.1–2 + §0o.2. **COMPLETION PASS PR #4403**: fifth bundle rescored (+0.49 pp 2024/25 — corrects the director's r#17 one-year-row bound), `neiso-t1x-pre-d5r` preserved, board co2 annotations EXECUTED (§0n.3 records item CLOSED). Live gate keys (ffr3a3/-3a4) still carry the mismeasured rows — bundles never committed, annotated in place. |
| **D3 MISO RETIREMENT / G3** | G3 cap-grain `retire.total_gw` t1h regression — attribution-first, zero-solve Phase 0 | **ISSUED r#21** | `claude/capx-d3-miso-retire-g3` | Fable | I13 cobweb closure = unattributed SCORER-READ, held open inside the lane; precommit-first. |
| **D4-I3 ERCOT** | I3 scarcity-slack invariant (net-revenue half HELD under card Y-C) — zero-solve breach-set + pre-declared post-arming expectation + FR-6 code-comment home | **ISSUED r#21** | `claude/capx-d4i3-ercot-slack` | Fable→**Opus** | Post-arming MEASUREMENT deferred to the next T1-H run (D6). |
| **D6 FC-3 CURVE-ON OVER-FIRE** | Four T1-H curve legs | QUEUED | — | Fable | — |
| **D8 FORECAST PROVENANCE DEBT + DOF LEDGER** | FC-7's two halves: the DOF-ledger instrument (every T1-F leg's caveat — NEISO's ONLY one) + the seven legacy legs' missing `run_config.json` | **LANDED r#21** (PR #4427; instrument + artifacts) — **re-emission half ISSUED r#21 mid-sitting as D8-RE (Opus)**, unblocked by the golden/S-6/S-123-V landings | `claude/capx-d8-dof-ledger` → `claude/capx-d8-re-emission` | Fable→Opus | §0p.2 + §0r.6. The instrument is what stands between the program's best ISO and a clean FC map. |
| **D9 MISO SOCO FORECAST FALLBACK** | `ba_code="SOCO"` live only in the forecast path | **ADJUDICATED UNREACHABLE at HEAD, ROUTED** (S-123 finding §5 — TVA re-point + data prerequisite named) | — | Fable | Handed in by miso-183; closed as a lane, lives on as a routed intake item. |
| **D16 ARMED-INTERFACE mc=0 SEAM** | Armed-interface forecast years leave seam rows at their mc=0 build placeholder (S-123 finding §5/§7-5) | **ISSUED r#19** — director mechanism decision: FAIL CLOSED (hard refusal, holdout_policy pattern); fallback-price alternative deliberately not built without its own charter | `claude/capx-d16-seam-guard` | Fable | §0p.2. New defect found on the D9 trace, routed to this track 2026-08-30. |
| **NEISO-RC-R REPAIR PHASE** | Execute the Phase-0 finding's routed repairs: R2 FCA-curve re-derivation + R1 registry intake + R3 scorer trio + R4 reporting; R5 deferred, R6 standing refusal; PREREG-first verification pair (one T1-X treatment vs the committed capxd14 control) | **ISSUED r#21** | `claude/capx-neiso-rc-repair` | Fable | Golden care lines (t3 / bare neiso-t1f keys untouchable); R1 and R3(iii) land together; cross-lane re-grade ruling applies to any verdict flip. |
| **D2-REMEASURE** | — | **RETIRED unrun** | — | — | Premise refuted at refresh #4. |

## 2. Backcast-track watch (last seen 2026-08-30 @ `83c1c5a`, refresh #17)

| item | state |
|---|---|
| CAISO (r#17) | **caiso-224 mid-lane**: A0 control G-CTRL bit-zero vs caiso-220 sidecars; FSNO variant seam set at the orchestrator; B1 arm 2023+2024 hourly-sidecar checkpoints landed; split-witness + F1/F2 falsifier probe PRE-REGISTERED (`scripts/probes/_caiso224_split_witness.py`, 21:58Z). Branch merged+deleted mid-cycle; unregistered ⇒ heavy slot NOT verifiably free (S-6 held). |
| Audit track (r#17) | **T1-H Phase-1 Leg A landed** (PRs #4386/#4389): gated default-off `storage_entry_availability_gate` (D-2) + `storage_entry_cost_normalized_rank` (D-3), matrix rows registered, A/B driver probe in. **Dedup boundary verified clean in code** — `model/storage.py` + config + harness only; None-drop passthrough keeps unarmed cache keys untouched (D12-C control safe). **PJM stage-0 golden captured** (`29a9cba`, audit card 1: pjm-162-inputclock 2023–2025, 0 drifted keys). `claude/ercot-243-release-exit-r7owkv` open, 0 unique commits. |
| NYISO (r#16) | **Keeper → `2026-08-30-nyiso-159-loss-surface`** (fail set narrows, still NOT-YET; marker stays withdrawn per Q5-W). **nyiso-160 winter-intake Leg 2 STOPPED WITH CAUSE** (AORR files unproducible) — NYISO's marker re-entry route is an open BACKCAST-track question. |
| NYISO (r#13) | **nyiso-158 phase-0 winter-face diagnosis landed** (PR #4339): the binding-depth differential is the measured Transco TTC step; no measured driver reaches the sharpened Iroquois re-open bar (first leg closed, Leg-2-only); C3b-2025 is WHOLLY the two faces (98.4 % of sq error — either face alone restores the band); CE-util overshoot adjudicated not-an-envelope-defect. **nyiso-159 opened** (PR #4352): phase-0 loss-component measurement on the 36-month record + PREREG of the zonal loss surface. Both merged; no NYISO branch in flight. |
| ERCOT (r#13) | **ercot-240 CLOSED in one arc** (PRs #4341/#4344/#4345/#4348): the event-hour demand gap is adjudicated the DC-tie import identity. **ercot-241 opened + merged** (PR #4349): Phase-0 precommit for the off-core conduct-parameterization screen. ercot-239 Stage-A census + Stage-B A/B driver landed (PRs #4351 etc.); the o7 attribution harness landed (PR #4334). |
| CAISO (r#13) | caiso-222 owner-sitting rulings recorded (R-1 keeper-currency annotation, Q1 terminal rest, Q2 routes armed/declined; PRs #4333/#4342/#4346). **caiso-223 sub-zonal scope round landed** (PRs #4347/#4350): partition adjudicated, membership derived, 3-way LDF split measured (gates 13/13 PASS), sufficiency gap list filed. |
| Governance (r#13) | The 2026-08-30 PM sitting executed four rulings (v14 ordering deviation recorded, gates re-measured green); director-records v14 board refreshed at re-derived pin. |
| Branches in flight (r#13) | `miso-190-backcast-calibration-okt1cn` ONLY — fully merged at `9cd6dc6` but **A/B solve NOT yet registered (scorer committed before it runs); owner confirms STILL RUNNING (Q9). S-123 check FAILS fifth consecutive; S-6 held on the same heavy slot.** |
| NYISO (r#12) | **Keeper → `2026-08-30-nyiso-157-par-attribution`** (owner ruling, structural-integrity formula, third application; D-5(b) stop fired and resolved by the ruling; keeper-auditor PASS). Determination **NOT-YET on {C3a-2025 −12.0 %, C3b-2025 0.203 knife-edge, C3c silenced-lone}** — fail set WIDENED vs nyiso-155. 2023 +1.0 % / 2024 −2.0 % PASS; first real zonal separation (CE util 0.381→0.784). Marker re-keyed at promotion, then **WITHDRAWN by the r#12 Q5 ruling (execution: lane Q5-W)**. Successor: intake Leg 2 (winter face). |
| ERCOT (r#12) | ercot-239 Phase-0 COMPLETE: missed-event family = measured energy-lambda scarcity in tight-room hours no reserve adder carried; precommit's availability/outage/ramp priors REFUTED; object = offer-surface conduct off the August core (ercot-217 episode). Successor o7 attribution-harness precommit landed ex ante (PR #4332). Both branches merged & deleted. |
| Forecast namespace (r#12) | FF-2D re-score (PR #4325): all 7 re-scorable verdicts byte-identical at HEAD, provenance-only diff, FR-21 gate reset. Bare keys unchanged. Benign — verified, not assumed. |
| Branches in flight (r#12) | `miso-190-backcast-calibration-okt1cn` ONLY. **S-123 check FAILS on it — fourth consecutive refresh.** caiso-221 records verified on main (`599f59b`); branch deletion lost nothing. |
| NYISO (r#11) | nyiso-157: C6 attested on both Leg-1 A/B bundles (`4d356f8`); **Iroquois companion arm REJECTED on its own pre-filed W-gates**, registered `2026-08-30-nyiso-157-iroquois-companion` (PR #4318; nyiso-147a-chp-btm pruned, top-15). Leg-1 PAR-attribution arm stands; promotion decision the backcast track's; branch open. |
| ERCOT (r#11) | **ercot-239 opened** (PR #4320): PRECOMMIT-only Phase-0 driver characterization of the 14-hour missed-event family (2023 carve-out lane; model < $200 while actual ≥ $500; stated prior: availability/outage/net-load-ramp representation object). Zero-solve; precommit pushed before measurement. Branch open. |
| Branches in flight (r#11) | `caiso-south-belly-pricing-24uv07` (records commit unmerged) · `ercot-239-residual-queue-lbkvbf` · `miso-190-backcast-calibration-okt1cn` · `nyiso-eastern-seam-par-leg1-w7s8mm`. **S-123 check FAILS on the MISO one — third consecutive refresh.** |
| ERCOT (r#10) | **TWO-CONFIG KEEPER** (owner ruling 3, 2026-08-26, executed `db8836a5`): forward keeper **`2026-08-25-234-eastex-identity`** (2024–2025 designated span, CALIBRATED, C3c ledgered ×2 — "the configuration the MODEL USES GOING FORWARD, forecast lane included") + 2023 carve-out `236-swcap-clip-k33`. Registered 3-year NOT-YET (C3a/C3b-2023) stands published. Q6 terrain moved by owner act; Q6 stays RULED-HOLD (§0g.3). |
| NYISO (r#10) | **nyiso-157 Leg-1 A/B registered** (control + arm, 2023–2025): PAR attribution restores the downstate gradient (NYC−UW 2023 annual mean $0.59 → $10.00, measured ≈ $14.8; C3a-2023 +6.8 → +1.0 %); Iroquois companion prereg filed BEFORE its solve; lane continues, branch open. |
| MISO / CAISO (r#10) | miso-190 mechanism landed (`partial_plant_exit_carry`, gated default-off; A/B scorer committed before running; branch open). caiso-221 killed the south-belly surplus-pricing design object with measurement (branch open). Card 10: decision-1 warm-start flip CLOSED-OVERTAKEN. |
| Branches in flight (r#10) | `caiso-south-belly-pricing-24uv07` · `miso-190-backcast-calibration-okt1cn` · `nyiso-eastern-seam-par-leg1-w7s8mm`. **S-123 check FAILS on the MISO one.** |
| Governance (r#9) | **Freeze TIER-SCOPED** (card 6 executed `0589b6f`): validation 2020–2022 lifted for `complete` ISOs, locked test frozen for all, `final` EMPTY. Card 7 standing precondition on any `final` grant (touchpoints run + loop quiescent). CAMPD layup charter closed with cause. Rubric **v3.5** (diurnal amplitude REPORTED-ONLY) verified determination-neutral over all six keepers — the xiso-6 watch item CLOSES. |
| CAISO (r#9) | Keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (caiso-200 recipe replayed on the active measured membership crosswalk; owner-act promotion on the pre-registered rule; no marker, no re-key due). |
| Branches in flight (r#9) | `miso-190-backcast-calibration-okt1cn` (partial-plant mid-window exit carry — miso-188's named successor; PREREG-first) · `nyiso-eastern-seam-par-leg1-w7s8mm` (Leg 1 executing; nyiso-157 gate scorer filed) · `holdout-governance-rulings-0826` (records lane). No ERCOT branch open; ERCOT landed O7 P0-seam Phase-0 + two governance rulings (G-SPUR lidless count, band count 59→61). |
| Branches in flight (r#8) | `caiso-c3a-overrun-closure-5n84mn` · `ercot-backcast-calibration-9wkxrg` still open; `miso-188-rubric-failure-tuning-m1ph17` MERGED mid-refresh (PR #4296). Heavy-slot deconfliction live for ERCOT/CAISO capx work; S-123 releasable on a start-time check (no new MISO branch in flight). |
| MISO (r#8, mid-refresh) | **Keeper → `2026-08-30-miso-188-rvsscope`** (full-span; NOT-YET narrowed to **{C3a-2025} alone**; single delta `retiree_vintage_status_scope=true`, new gated default-off field, matrix row + cells minted per rule 28c; 28 dark retiree-channel units / 1,434 MW dropped on the EIA-860 vintage-status oracle; promoted on the PREREG's own rule, keeper-auditor PASS). Named-not-built successor: the partial-plant mid-window exit gap (5.93 TWh 2023). |
| NYISO (r#8) | **nyiso-156b: Q1 ruled OPTION A — winter locational identification intake AUTHORIZED** (`ab0513e`, spec `INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`; Leg 1 session-executable, Leg 2 owner-executable fail-closed). Measured expectation: winter-face closure alone returns the keeper to CALIBRATED via the C3c standing rule — the live path through Q5 (§0e.2). Seam "unidentifiable" record corrected (authorization-blocked, not identification-blocked). |
| Dashboard hygiene (r#8) | Bench-fingerprint adjudication landed (PR #4293): 11 "stale" bench parts = UNLABELLED, not wrong; measured over the full builder-drift commit set. |
| Keepers (refresh #7 — MISO since superseded by the r#8 row above) | **ERCOT `2026-08-25-236-swcap-clip-k33` — CALIBRATED, empty fail set, but `years: [2023]` (2023-ONLY; see §0d.2 / Q6)** · CAISO `2026-08-17-caiso-200-h1-memberpanel` (caiso-220 replay mid-solve) · **MISO `2026-08-26-miso-187-nucavail`** (NOT-YET) · NEISO `2026-08-17-neiso-99-joint-p1` · NYISO `2026-08-25-nyiso-155-hydro-repair` (NOT-YET) · PJM `2026-08-15-pjm-162-inputclock` |
| Keepers (refresh #6 — superseded) | **ERCOT `2026-08-25-235-2023-discrete-k24`** (NOT-YET, price_mean; **2023-ONLY**, rule-16 waiver SPENT) · CAISO `2026-08-17-caiso-200-h1-memberpanel` (unchanged) · **MISO `2026-08-25-miso-186-statusscope`** (NOT-YET, **fuelmix + price_mean** — two criteria, was C3a-2025 alone) · NEISO `2026-08-17-neiso-99-joint-p1` (unchanged) · **NYISO `2026-08-25-nyiso-155-hydro-repair`** (NOT-YET, price_mean + price_tail) · PJM `2026-08-15-pjm-162-inputclock` (unchanged) |
| Markers / freeze | `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; freeze **TIER-SCOPED since r#9** (locked test frozen for all; validation by marker + `--holdout-authorized`) — was blanket-ACTIVE through r#8 |
| Gate (a) | pass on the literal test: PJM, NYISO, NEISO. fail on marker: ERCOT, CAISO, MISO. **NYISO's BASIS CHANGED** — its marker now rests on a NOT-YET keeper (§0c.2, Q5). |
| Other refresh-#6 movement | xiso-6 opened a **DECISION CARD on the diurnal price-amplitude rubric** (a cross-ISO rubric question — watch it, it could touch six determinations). CAISO AS-revenue registry row populated (storage 14.82 $/kW-yr @ ref 5.517 GW). xiso-5/6 landed a thermal-tranche vintage sidecar + an arm-over-gap guard at the `bins_to_fleet` seam. |
| ERCOT | Card Y signed **Y-C** (hold open). Card Z signed **Z-A**: crosswalk repair — **EASTEX (East Texas GTC) replaces the mis-attributed NE_LOB** on Northeast→North, static 1300 → 2300. ercot-234 also re-pointed the official scorer's validation gate at the ercot-231 keeper (stale since promotion). |
| MISO | miso-184 **V-DEFECT-COUPLING** (matrix cell R). miso-185 **V-NEG-ABSENT** — the §6b firm-export re-open data does not exist (698 EQR seller-quarter reports, no qualifying firm-export obligation); re-open narrowed to contract-grain. **~1.3 GW scarce-export model-class concession** is the honest residual; a D-4 posture question goes to the owner. |
| CAISO | Quiet this cycle. |

**Deconfliction: clean.** D2-B explicitly stopped at a FINDING on the one MISO root cause that
reaches shared solve machinery (S-1), per its charter.

## 3. Owner-tier questions — FIFTEEN ANSWERED (Q5/Q6 r#8; Q5 re-ruled r#12; Q7/Q8/Q9 r#13; Q10/Q11/Q12 r#15; Q13/Q14 r#17; Q15 r#18 — all 2026-08-30)

Full signature record and the consequences adopted:
**`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5** (cards A/B/C/Y);
Q7–Q9 were ruled via in-session decision cards at r#13 and are recorded here + in §0j.3
(execution of Q7 = lane D13).

| # | question | resolution |
|---|---|---|
| ~~Q7~~ | Leg-(c) semantics: the board carried BOTH readings (D7 wrote ERCOT/PJM/MISO fail-on-band; D10 wrote NYISO pass-on-measurement) | **RULED 2026-08-30 (r#13 sitting) — MEASURED CLOSES THE LEG**, per the charter-literal §2.1b(c) test ("measured and reported" + readiness green) and card A-A as signed ("closes on a measured FC-4"). ERCOT/PJM/MISO leg (c) → pass-on-measurement, FC-4 FAIL magnitudes stay at full magnitude; NYISO's PASS stands; the in-band reading is superseded. Execution = lane D13. No §2.1b gate opens (all three fail other legs). |
| ~~Q8~~ | Arm `entry_margin_exhaustion` as the ERCOT forecast default? (D11-R's escalation) | **RULED 2026-08-30 (r#13 sitting) — HOLD UNTIL D12**, at the finding's §5 recommendation. The gas half is inert on the live reserve leg, so arming now would bake in the VRE/storage-only split; D12 adjudicates the scarcity basis first and its report re-opens the decision. Matrix cell stays **O**. |
| ~~Q15~~ | The D12-C re-decision (Q10's contradiction branch): one V-2 window missed on a pre-declaration derivation error, every structural claim confirmed, conservative direction — arm? | **RULED 2026-08-30 (r#18 sitting) — ARM BOTH FIELDS** (`entry_margin_exhaustion` + `entry_forward_reserve_leg` → ERCOT forecast defaults), the owner judging the record confirming-in-substance per the finding's own §4.3 clause. The V-2 miss is described honestly in the arming citation; matrix cells O → K-forecast-armed on the registered pair's evidence; sister-ISO cells stay U (rule 26). Execution = lane **D12-A** (zero-solve; prompt in the pack). |
| ~~Q13~~ | NEISO §2.1b leg (d): first-ever full-solve authorization, presented on S-4b's measured result per Q11 | **RULED 2026-08-30 (r#17 sitting) — AUTHORIZED: the T3 BAU GOLDEN, NEISO, 2026–2050, budget ~1.0 h / ~4.3 GB (FF-3E), THIS CAMPAIGN ONLY.** The first §2.1b gate opening in program history. Caveats carried verbatim into the campaign record (floor-dependent 2028/29 I7; D14 exit-composition recall 2/6; FC-7 DOF gap); a gate-condition regression re-closes. Execution = lane T3-NEISO-GOLDEN (prompt in the pack). |
| ~~Q14~~ | caiso-224 / the S-6 heavy slot: is the CAISO session still solving? | **ANSWERED 2026-08-30 (r#17 sitting) — the caiso-224 session RAN OUT mid-completion** ("mid keeper promotion I think"); the owner directs the DIRECTOR to draft a finisher prompt (a recorded backcast-track boundary exception, owner-requested), then S-6 unblocks. Lane CAISO-224-FIN issued — zero-solve; it executes the PRECOMMIT's own §5 adjudication (measured record: F1 fires ×3 + F2 fires ⇒ R for keeper purposes, never auto-promoted), registers both bundles, stamps the matrix. **S-6 = RELEASED-CONDITIONAL on CAISO-224-FIN landing.** |
| ~~Q10~~ | The Q8 re-decision: D12 reported (phantom leg adjudicated; recommended arm-both) — arm? | **RULED 2026-08-30 (r#15 sitting) — CONFIRM-PAIR, THEN ARM.** Lane D12-C runs ONE arm-vs-control A/B (two fields, single logical delta) measuring the closed loop; **arming auto-executes on a confirming record**; a contradiction returns unarmed at full magnitude. |
| ~~Q11~~ | NEISO leg (d): first-ever full-solve authorization now live — sign? | **RULED 2026-08-30 (r#15 sitting) — HOLD FOR S-4b FIRST.** S-4b dispatches now; the leg-(d) card is re-presented on its measured result (a published filing supersedes the current requirement bar; D14's retirement-composition finding noted as context). |
| ~~Q12~~ | Charter the D5-R crossover-scorer repair (verdict-moving re-score)? | **RULED 2026-08-30 (r#15 sitting) — CHARTERED, FULL FIX** (D5 preference (a): canonical taxonomy-chain coal split at gmModel build; C1 coal rows repaired in the same stroke; §5.2 pre-declared table is the honesty gate). |
| ~~Q9~~ | Is the miso-190 backcast session still running? (governs the S-123 start-time check + S-6's heavy slot) | **ANSWERED 2026-08-30 (r#13 sitting) — STILL RUNNING.** S-123 held (fifth consecutive check fail); S-6 held on the heavy slot. Both re-checked every refresh. |
| ~~Q1~~ | ERCOT 2023 arc settled? | **ANSWERED** — card Y signed **Y-C**, hold open ⇒ D4 = I3-invariant half only. |
| ~~Q2~~ | Leg-(c) consistency (card A) | **SIGNED 2026-08-25 — (A-A), at the recommendation.** CAISO + NYISO move `na`→`fail`, `"c"` into both `closed_on`; NEISO unchanged. **NYISO T1-X chartered (D10)** so leg (c) closes on a measured FC-4. No gate opened; leg (d) untouched. |
| ~~Q3~~ | `entry_lookahead_reprice` disarm default (card B) | **SIGNED 2026-08-25 — (B-C), at the recommendation.** Shipped default HOLDS, cell stays `O`, no verdict minted. **Developer-pro-forma construction chartered (D11).** Neither known-wrong object is ratified. |
| ~~Q4~~ | PJM beyond-last-FPR convention (card C) | **SIGNED 2026-08-25 — (C-A), at the recommendation.** **Hold-last-FPR adopted**, bundled with the D-1 checker repair. PJM's I7 miss restates **366 MW → ~5.9 GW**, 2029 plausibly joining — a worse reported result, taken as the more honest bar. S-5 unblocked; S-6 strictly after. 2029/30 parameters intaken on publication (rule 23). |
| ~~Q5~~ | NYISO marker on NOT-YET keeper | **RE-RULED 2026-08-30 (r#12 decision card) — WITHDRAW THE MARKER (CAISO precedent), superseding the r#8 WAIT.** The recurrence clause fired (nyiso-157 promotion re-keyed the marker onto a second consecutive NOT-YET keeper, fail set widened). Written reconciliation, now uniform: a `complete` marker cannot stand on a NOT-YET keeper; the structural-integrity formula governs KEEPER promotions only. Execution = lane Q5-W. Re-entry is a new owner declaration once the keeper again scores CALIBRATED (winter-intake route). |
| ~~Q6~~ | ERCOT CALIBRATED but 2023-only | **RULED 2026-08-30 (r#8 sitting) — HOLD, NO ACTION.** No direction to the ERCOT backcast lane; revisit when it goes quiet. Gate (a) keeps failing on both counts meanwhile. |

**None of the four signatures** touched a backcast keeper, marker or matrix cell, lifted the
holdout freeze, authorized a §2.1b full-solve, or opened any ISO's gate.

### Q6 (refresh #7) — ERCOT is CALIBRATED but its keeper is 2023-only

**RULED 2026-08-30 (r#8 sitting): HOLD, NO ACTION** — no direction to the ERCOT backcast lane;
revisit when it goes quiet. The analysis below is preserved as the record the ruling was made on. `2026-08-25-236-swcap-clip-k33` scores **CALIBRATED with an empty failing
set**, closing the 2023 price object card Y held open two days earlier. But its registry declares
`years: [2023]`, so gate (a) fails on **two** counts: ERCOT is absent from `complete`, and
§2.1b(2)(a) requires a **full-span** keeper (rule 16), which this is not. **Declaring ERCOT
`complete` would therefore NOT open its gate (a).** To convert the CALIBRATED result into forecast
progress ERCOT needs a **full-span 2023–2025 keeper carrying the swcap-clip recipe**. Director
recommendation: **before spending any `complete` declaration, have the ERCOT lane re-solve the
swcap-clip recipe full-span** — the rule-16 waiver that licensed the 2023-only form was for the
backcast lane's regime argument and was never a forecast-gate instrument. Sequencing only; no
determination is questioned here.

### Q5 (refresh #6) — NYISO's `complete` marker now rests on a NOT-YET keeper

**RULED 2026-08-30 (r#8 sitting): WAIT FOR WINTER INTAKE** — the precedents are left standing
unreconciled and the nyiso-156 intake is the designated resolution route; no marker moves and
gate (a) stays PASS on the literal test. The analysis below is preserved as the record the
ruling was made on. NYISO's keeper moved to `2026-08-25-nyiso-155-hydro-repair` (NOT-YET on
price_mean + price_tail) and the marker was re-keyed to it, with the D-5(b) worse-determination
stop fired, escalated and resolved by an explicit owner ruling on structural integrity over gate
regression. **On 2026-08-06 the identical fact pattern — a `complete` marker whose keeper scored
NOT-YET — withdrew CAISO's marker outright**, on the reading that "a `complete` marker cannot stand
on a NOT-YET keeper". Both are now on the record and they point opposite ways.

**Why this track cares:** gate (a) is the only §2.1b leg that reads off the backcast marker, and
NYISO is the program's lead ISO — the one ISO whose legs (a) and (b) both pass. On the charter's
literal test (*designated full-span keeper AND an entry in `complete`*) gate (a) still passes, and
this director is NOT re-reading it downward on its own initiative. But the question of whether the
marker is sound is the owner's, and its answer decides whether NYISO's lead position is real.
**Director recommendation: state the reconciliation explicitly** — either (i) affirm that the
owner's structural-integrity standard permits a `complete` marker on a NOT-YET keeper, which
distinguishes the CAISO withdrawal on its own facts (CAISO's was a rubric re-score with no
compensating structural gain), or (ii) apply the CAISO precedent uniformly and withdraw. Option (i)
is the more defensible on this record, but either way the reconciliation should be **written**,
because the two precedents currently contradict each other and gate (a) hangs on which governs.
NYISO's **frontier** status has already returned to the owner on the same promotion.

*Refresh-#8 addendum:* the nyiso-156b ruling (winter intake AUTHORIZED, §0e.2) gives Q5 a live
structural resolution path — the card's §4 measures that winter-face closure alone returns the
keeper to CALIBRATED, which would re-key the marker onto a CALIBRATED keeper and dissolve the
tension prospectively. The written reconciliation of the two precedents remains worth having (it
governs the next time this fact pattern appears), but Q5 no longer blocks anything this track is
doing: gate (a) is taken as PASS on the literal test throughout.

## 4. Prompt issuance record

| date | lane | branch | model | profile | outcome |
|---|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `capx-d1-board-refresh` | Opus | code | **LANDED** |
| 2026-08-23 | D2 ADEQUACY — NYISO | `capx-d2-adequacy-nyiso` | Fable→Opus | nyiso | **LANDED** |
| 2026-08-24 | D2-REMEASURE | `capx-d2-remeasure-t1f` | Fable | all | **RETIRED unrun** |
| 2026-08-24 | D2-B I7 LEDGER | `capx-d2b-i7-ledger` | Fable | code | **LANDED** |
| 2026-08-24 | D2-NYISO-INTAKE | `capx-d2-nyiso-extcap-intake` | Fable | nyiso | **LANDED — I7 CLEARED** |
| 2026-08-24 | D5 CROSSOVER CO2 | `capx-d5-crossover-co2` | Fable | pjm | not started; **re-scoped r#5** |
| 2026-08-25 | **D7-NYISO GATE RE-SCORE** | `capx-d7-nyiso-gate` | Opus | code | issued (now also carries A-A) |
| 2026-08-25 | **S-123 MISO ADEQUACY PACKAGE** | `capx-s123-miso-adequacy` | Fable | miso | issued |
| 2026-08-25 | **S-4 NEISO HYDRO ACCREDITATION** | `capx-s4-neiso-hydro` | Fable | neiso | issued |
| 2026-08-25 | **D10 NYISO T1-X** | — | Fable | nyiso | chartered by card A; prompt written 2026-08-25 |
| 2026-08-25 | **D11 ENTRY-SIGNAL PRO-FORMA** | — | Fable | ercot | chartered by card B; prompt written 2026-08-25; **superseded by D11-R at r#8, never run** |
| 2026-08-25 | **S-5 PJM HORIZON-EDGE** | — | Fable | pjm | unblocked by card C; prompt written 2026-08-25; stands ready (heavy, solo slot) |
| 2026-08-30 | **D10 NYISO T1-X (reissued)** | `claude/capx-d10-nyiso-t1x` | Fable | nyiso | r#8 batch — pack corrected for nyiso-155 keeper state; **still unstarted at r#10** |
| 2026-08-30 | **D11-R ENTRY VOLUME RULE** | `claude/capx-d11r-entry-volume-rule` | Fable | ercot | r#8 batch — re-scoped per §0e.3; **RUNNING since r#10** |
| 2026-08-30 | **S-4 NEISO HYDRO (reissued)** | `claude/capx-s4-neiso-hydro` | Fable | neiso | r#8 batch — **LANDED at r#10** (PR #4312, verification pair pending) |
| 2026-08-30 | **S-4V NEISO VERIFICATION** | `claude/capx-s4v-neiso-verification` | Fable | neiso | r#11 batch — new charter (S-4's owed verification half); D10 + S-5 re-presented unchanged alongside it. **All three dispatched by the owner (in flight at r#12)** |
| 2026-08-30 | **Q5-W NYISO MARKER WITHDRAWAL** | `claude/q5w-nyiso-marker-withdrawal` | Fable/Opus | code | r#12 — governance records lane executing the owner's r#12 Q5 ruling (WITHDRAW, CAISO precedent). **LANDED at r#13** (PR #4343) — as did D10 (PR #4354), S-4V (PRs #4337/#4353), S-5 (PR #4340) and D11-R (PR #4355): the whole in-flight set |
| 2026-08-30 | **D13 BOARD RECONCILE** | `claude/capx-d13-board-reconcile` | Fable/Opus | code | r#13 batch — records lane: Q7 execution + S-5 PJM restatement + landed-lane board currency + stale-prose repair |
| 2026-08-30 | **D14 NEISO T1-X CROSSOVER** | `claude/capx-d14-neiso-t1x` | Fable | neiso | r#13 batch — the D10 analog on the new lead ISO; success ⇒ first (a)+(b)+(c) ISO |
| 2026-08-30 | **D12 SCARCITY-CONSISTENT DELTA BASIS** | `claude/capx-d12-scarcity-basis` | Fable | ercot | r#13 batch — released by D11-R's report; feeds the Q8 arming re-decision |
| 2026-08-30 | **S-4b NEISO ARA RE-VINTAGE** | `claude/capx-s4b-neiso-ara` | Fable | neiso | r#13 — prompt written; **dispatch strictly after D14 merges** (shared NEISO surfaces) |
| 2026-08-30 | **D5 CROSSOVER CO2 DERIVATION** | `claude/capx-d5-crossover-co2` | Fable | code (widen as needed) | r#14 — zero-solve three-ISO attribution. **LANDED at r#15** (PR #4374) — as did D13 (PR #4372), D14 (PR #4376) and D12 (PR #4373): the whole wave, second consecutive 100 % cycle |
| 2026-08-30 | **D12-C ARMING CONFIRMATION PAIR** | `claude/capx-d12c-confirm-pair` | Fable | ercot | r#15 batch — Q10 execution: confirm-then-arm, auto-arm on a confirming record |
| 2026-08-30 | **D5-R SCORER COAL-GRAIN REPAIR** | `claude/capx-d5r-scorer-coal-grain` → ran as `claude/crossover-co2-grain-repair-oycsy6` | Fable | code | r#15 batch — Q12 execution: full fix + zero-solve re-score under the pre-declared honesty gate. **LANDED at r#17** (PR #4388, controls verified) |
| 2026-08-30 | **S-4b (released)** + **S-123 (released)** | pack prompts | Fable | neiso / miso | r#15 — S-4b's D14 gate cleared; S-123's start-time check finally passes (miso-190 concluded). **S-4b LANDED at r#17** (PRs #4392/#4396) |
| 2026-08-30 | **CAISO-224-FIN** | `claude/caiso-224-fsno-finisher` | Fable | code | r#17 — owner-requested (Q14) backcast-track completion, boundary exception recorded; zero-solve. **LANDED PR #4415 (r#19 sitting): R per precommit §5, pair registered, matrix stamped, keeper untouched** |
| 2026-08-30 | **T3-NEISO-GOLDEN** | `claude/capx-t3-neiso-golden` | Fable | neiso | r#17 — executes the Q13 authorization: the program's FIRST §2.1b full-horizon campaign (NEISO 2026–2050 BAU golden, ~1.0 h / ~4.3 GB, this campaign only) |
| 2026-08-30 | **S-6 (released, conditional)** | pack prompt | Fable | pjm | r#17 — RELEASED-CONDITIONAL: dispatch strictly AFTER CAISO-224-FIN lands (Q14); no-co-run discipline vs the golden stated in both prompts |
| 2026-08-30 | **D12-A ARMING EXECUTION** | `claude/capx-d12a-arming` | Fable | code | r#18 — executes Q15 (ARM BOTH on the D12-C record judged confirming-in-substance); zero-solve; cache-key verification f061b2646bfaac8b; V-2 miss described honestly; ERCOT cells O → K-forecast-armed |
| 2026-08-30 | **S-6 PJM LEDGER RUN** | `claude/capx-s6-pjm-ledger` | Fable | pjm | r#19 — first pack prompt; released unconditionally (slot doctrine voided); briefly owner-held, then **DISPATCHED** |
| 2026-08-30 | **S-123-V MISO VERIFICATION** | `claude/capx-s123v-miso-verify` | Fable | miso | r#19 — fills S-123 §6; stops-at-start if the original session still runs. **DISPATCHED** |
| 2026-08-30 | **NEISO-RC PHASE-0** | `claude/capx-neiso-rc-phase0` | Fable | code | r#19 — D14 retirement-composition attribution, zero-solve, finding-only. **DISPATCHED** |
| 2026-08-30 | **D16 SEAM GUARD** | `claude/capx-d16-seam-guard` | Fable | code | r#19 — fail-closed refusal on the mc=0 armed-interface seam (director mechanism decision; fallback price deliberately not built). **DISPATCHED** |
| 2026-08-30 | **D8 DOF-LEDGER + PROVENANCE** | `claude/capx-d8-dof-ledger` | Fable | code | r#19 — FC-7 both halves; verdict/board re-emission explicitly deferred. **DISPATCHED — LANDED at r#20 (PR #4427; re-emission still deferred)** |
| 2026-08-31 | **S-6-R (relaunch)** | `claude/capx-s6-pjm-ledger-r2` | **Opus** | pjm | r#20 — pre-declared execution. **LANDED at r#21 (PR #4436): FC-1 FAIL = {I7, I12}** |
| 2026-08-31 | **S-123-V-R (relaunch)** | `claude/capx-s123v-miso-verify-r2` | **Opus** | miso | r#20 — pre-declared execution. **LANDED at r#21 (PR #4441): §6 filled, S-123 complete** |
| 2026-08-31 | **T3-GOLDEN-R (relaunch)** | — | **Opus** | neiso | r#20 — **RECALLED UNRUN at r#21 (owner correction: the original golden session is STILL RUNNING; r#20's LOST grading was wrong)**. Never dispatched; the original T3 issuance (r#17) stays the live lane |
| 2026-08-31 | **D12-A-R (relaunch)** | `claude/capx-d12a-arming-r2` | **Fable** | code | r#20 — orphan-branch adjudication. **LANDED at r#21 (PR #4429): re-verified and armed per Q15, matrix stamped** |
| 2026-08-31 | **NEISO-RC-R REPAIR PHASE** | `claude/capx-neiso-rc-repair` | **Fable** | neiso | r#21 batch — R2+R1+R3(+R4) per the Phase-0 finding; PREREG-first verification pair; golden care lines |
| 2026-08-31 | **D3 MISO RETIREMENT G3** | `claude/capx-d3-miso-retire-g3` | **Fable** | miso | r#21 batch — attribution-first zero-solve Phase 0 on the t1h `retire.total_gw` flip; precommit-first |
| 2026-08-31 | **D4-I3 ERCOT SLACK HALF** | `claude/capx-d4i3-ercot-slack` | **Opus** | ercot | r#21 batch — zero-solve breach-set + pre-declared post-arming expectation; net-revenue half stays HELD (card Y-C); D6 sequenced after it |
| 2026-08-31 | **D8-RE VERDICT/BOARD RE-EMISSION** | `claude/capx-d8-re-emission` | **Opus** | code | r#21 batch (mid-sitting release) — the D8-deferred re-emission, unblocked by the golden/S-6/S-123-V landings; records only, zero-solve |

## 5. History (compacted)

- **Refresh #1 (08-23):** charter; first state read; D1 + D2-NYISO issued.
- **Refresh #2 (08-24):** D1 landed. Director hypothesised the I7 verdicts sat on a pre-FFR-1C
  HEAD; chartered D2-REMEASURE on it. **Later refuted — see #4.**
- **Refresh #3 (08-24):** no lane started; ercot-233 opened card Y; D9 handed in by miso-183.
- **Refresh #4 (08-24):** Q1 answered (Y-C). D2-NYISO landed and **refuted the pre-fix-HEAD
  hypothesis** — FFR-1C hydro was already inside the FFR-3A-2 verdicts (1,763.3 MW; pre-hydro
  ledger 30,322.2 MW = the board's stale "30.3 GW"). D2-REMEASURE retired unrun; D2-B and
  D2-NYISO-INTAKE issued in its place. Recorded against interest.
- **Refresh #5 (08-25):** D2-NYISO-INTAKE and D2-B landed; **NYISO cleared FC-1**. Cards A/B/C put
  to the owner and **all three signed at the recommendation** the same day (§3).
