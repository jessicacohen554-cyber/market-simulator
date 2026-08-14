# ERCOT-SCAR WORKSTREAM PACK — 2026-08

> Maintained by the ERCOT-SCAR workstream manager (persistent session; branch
> `claude/ercot-scar-workstream-mgr-14o689`, pack + addenda only, one commit per
> cycle). Precedent: the FFR-FH manager's pack/addenda pattern. The manager
> sequences, dispatches, verifies, and escalates — it edits no `src/`, solves no
> LP, builds no mechanism. §0 is the live board (rewritten each cycle); §1 the
> standing fences every dispatched prompt carries; §2 the dispatched prompt
> texts verbatim; §A the dated addenda (append-only — old addenda are never
> rewritten).

---

## §0 STATE BOARD — cycle 8, 2026-08-14

**Recorded HEAD (origin/main): `dbde0c2`.** The owner returned and
batch-merged PRs #3914–#3924, including ALL THREE of this workstream's
verified branches — hygiene fix `9e3a6c4` (#3917), ercot-196 card T
`3395389` (#3916), replay-diagnostics fix `8653317` (#3920) — plus this
pack's branch at its cycle-6 state (#3919). All merges were silent (no PR
comments): the LANDING CONVENTION is thereby ANSWERED BY EXAMPLE — workers
land push-and-stop on manager-verified branches, the OWNER opens and merges
the PRs. That is now the standing convention (§1 fence 6 unchanged; the
owner can override it any time). Card T was merged AS RECORD ONLY — no
RESOLUTIONS block exists on main, so it is NOT signed. Remaining owner
items: TWO (card T signature; L-SCAR V0-FAIL adjudication).

### Signed rulings in force (the governance this workstream enforces)

| ruling | content | citation |
|---|---|---|
| **Q-B (FINAL)** | NO ERCOT C3a-2023 backcast spend, of any kind, ever. Card Q signed (Q-C) 2026-08-12; the licence re-test FAILED at ercot-191 (L1 0.3857 vs 0.90), making (Q-B) automatic and final; item 11 CLOSED. | `docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md` + RESOLUTIONS |
| **R-A** | NOT-YET stands as ERCOT's public claim. No C3b-2023-targeted determination rounds (best non-Aug/Sep case ≈ 0.59 NRMSE vs 0.20 bar — C3a-2023/C3b-2023/C3c are one Q-B-closed physical object, 96.2 % Aug+Sep 2023). ERCOT bandwidth → protective/hygiene defects, the 2024/2025 shape queue, standing re-gates, forecast readiness. R-B reporting-text variant NOT signed. | `docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md` + RESOLUTIONS |
| **S1/S2/S3** | S1: the L-1 residual scarcity-rent term ADMISSIBLE AS CHARTERED (§2.6 distinction owner-signed — workers stay inside it or stop). S2: L-1 runs, SCREEN ONLY (capacity-evolution steps 3/5; §4 must-nots verbatim; L-2 named follow-on complement, unchartered). S3: A/B now, PROMOTION WAITS BEHIND OVERRIDE-FIX. | `docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md` + RESOLUTIONS |
| ercot-188 seven rulings | All executed; historical context only. | `docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` |

### Pending merges

- **ercot-194 signing commit — RESOLVED.** `3bfd33a` merged to main via PR
  #3904 (`c9aeeb6`); verified ancestor of origin/main. Flag cleared cycle 1.
- **PR #3912 (L-SCAR V0-stop deliverable) — RESOLVED: MERGED at `cfb8127`,
  2026-08-13T05:28:59Z.** The original worker landed it itself (rebase onto
  main + a provenance re-stamp confined to the FINDING, then merge) 34 s
  before the manager's FIX-IT-1 dispatch. Landed content verified on main:
  both `docs/calibration-log/ercot.md` entries (ercot-193, ercot-195) present
  in order; `docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`
  present; the re-stamp commit (`cfad808`) touched only the FINDING
  provenance block (+7/−1). FIX-IT-1 was moot at dispatch and did nothing
  (see A2).

### Workers

| worker | state | verification |
|---|---|---|
| **L-SCAR-SCREEN-2** (branch `claude/l-scar-screen-2-implement-lo897d`, PR #3912) | **STOPPED AT V0, per charter — V0 FAIL.** Intake succeeded (SOM anchors 3→7 vintages, 2019–2025, schema-validated, source_doc+source_page; 2018 SOM absent from Potomac library and outside working span). V0: best of eight candidate forms = 4/14 folds vs required 14/14; model-free identifiability bound proves NO function of any candidate tightness variable can pass (near-tied pairs carry $94–$330 irreducible error vs $15 tolerance); ex-Uri WORSE (2/14); monitor's own attribution: the 2019–2025 rent series is a REGIME series (Uri/$9k SWCAP; ORDC changes; ECRS = 50 % of 2023 net revenue), not a tightness series. Correctly built NOTHING: no ScenarioConfig field, no matrix row (28c not triggered — no field), no A/B, no registration, no promotion; screen-revenue movement $0.00/kW-yr, stated. | Duties verified cycle 1 against the branch: FINDING (`docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`) reports at full magnitude with Q-B/S1 citations; log entry present (+76 lines `docs/calibration-log/ercot.md`); rule 22 clean (data intake only, no year solved/scored — the stale quarantine notes in the som README/schema corrected to the 2026-08-06 clarification); deriver `scripts/data/derive_screen_scarcity_rent.py` committed as the standing re-derive test (rule 23 trigger = new SOM/telemetry vintage). LANDED on main at `cfb8127` (worker self-landed; content verified — A2). **Lane adjudication → OWNER (decision bullets, cycle-1 report).** |
| **SOC-REGATE-EXEC** (branch `claude/ercot-193-c3b-ceiling-2xu9lg`, PRs #3906 + #3911, MERGED) | **LANDED — RG-PASS on every gate; ercot-167 standing expectation DISCHARGED; lane CLOSED-CLEAN.** G1 663.7→516.1 MW vs measured 423 (61 % of gap, no overshoot); G2 0.72 (≥0.70); G3 2023 2→2, 2024 6→5, 2025 1→1; G4 C3a-2024 Δ0.989 pp on the unrounded scorer basis (knife-edge disclosed), C3a-2025 Δ0.607 pp; G5 shed identical; G-COAL148 ≈ 0.0 of 0.5 TWh bar; G-REPRO keeper reproduces BYTE-IDENTICALLY (12/12 hourly-sidecar sha256, zero scored-value drift). Keeper UNCHANGED at `2026-08-12-run192-arm-coal-peak` (direction-blind rule honoured). | Duties verified cycle 1: both runs registered (`2026-08-13-ercot193-ctl-nosoc` / `-arm-soc`, backcast registry sidecars + run payloads); retention evictions exactly as pre-registered (run168b-year-curves, run173a-reconc-control; neither the keeper); keeper shard untouched (empty diff on `frontend/data/backcast/keepers/`); matrix ERCOT shard cell + `mechanism-testing-matrix.md` item-10 block updated in the same PR; `scripts/check_mechanism_matrix.py` **exit 0** at 016b659 (236 warnings, all cosmetic line-number anchor drift; 0 errors); calibration-log entry present (+90 lines); precommit pushed pre-solve (`5ad4975`); C3b-2023 side-effect reported with the card-R ceiling stated up front; Q-B/R-A citations present. No keeper-shard edit → no keeper-auditor spawn needed. |
| **FIX-IT-1** (child session `session_01Ne18N4kQa3EPfZ7pCbN8FL`, dispatched cycle 1, 2026-08-13T05:29:33Z) | **MOOT AT DISPATCH; DID NOTHING; self-archived 05:31Z.** PR #3912 had merged at 05:28:59Z, 34 s before dispatch (manager read the PR state ~2 min stale). The session also could not clone the repo (child sessions do not inherit the repo attachment — pass `source_url` on `create_session`; A2). No push, no PR action, no artifact. Prompt kept verbatim at §2.1 for the record. | Manager unsubscribed from #3912 (merged). Two lessons appended as A2 duties. |
| **HYGIENE-1** (child session `session_013ADXP9Kq5nGEAqsrB6WoKh`, dispatched cycle 1 with `source_url`) | **PROVISIONING FAILED — never started; archived cycle 2.** Init died at 05:58Z with `clone_timeout`, unrecoverable: a `source_url` dispatch makes the platform attempt a FULL clone, which stalls on this repo (7.37 GiB live at tip — the exact docs/fast-clone.md failure). No work performed, no branch created. | Postmortem in A3; re-dispatched as HYGIENE-1b with the add_repo + blobless provisioning preamble. |
| **HYGIENE-1b** (child session `session_011sYFijAwLntGLjFM1do3vp`, dispatched cycle 2, NO source_url + §2.3 provisioning preamble) | **LANDED, REVIEW-READY — verified cycle 3.** The provisioning pattern WORKED (add_repo → blobless clone). One commit `9e3a6c4` on `claude/ercot-scar-hygiene-1-dashboard-sidecar` off `5b05f84`, push-and-stop honored (no PR opened). Root fix: `resolve_bundle()` anchors a relative `--bundle` at the repo root once at the top of `main()`, making the meta.json guard, rendering, and the metrics-sidecar write CWD-independent; also explains the "determination: unavailable" mis-report disclosed at ercot-193. | Verified via commit stats + patch: exactly 2 files — `scripts/dashboard_add_run.py` +21/−1 (minimal) and NEW `tests/scoring/test_dashboard_add_run_sidecar.py` (126 lines, drives `main()` from a non-repo tmp CWD with a decoy tree, verified failing pre-fix). Citations to the ercot-193 filing + FINDING §4 present. **AWAITING LANDING** per the owner's landing-convention answer (merge `9e3a6c4` or authorize worker PRs). |
| **SHAPE-CHARTER-1** (child session `session_018hZXhKv19qih79y62t1uPw`, dispatched cycle 3) | **LANDED, REVIEW-READY — verified cycle 4.** One commit `3395389` on `claude/ercot-scar-shape-charter-1` off `5b05f84`, push-and-stop honored (no PR). Deliverable: `docs/DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md` (324 lines, **card T**) + read-only probe `scripts/probes/ercot196_shape_decomposition.py` + its JSON + log entry. The object SIZED: 2024 NRMSE 0.1352 is pure shape (Nov+Apr+Aug+May = 78.1 % of squared residual; three-month ceiling 0.0824); 2025 0.0957 is LEVEL-dominated (uniform −2.76 $/MWh; May+Feb+Apr = 72.5 %; ceiling 0.0501). ATTRIBUTED measured: (a) sub-tail scarcity content the LP does not form (Nov/Aug-2024 tail wedges $5.12/$7.39; 2025's 217-vs-35 hours >$100) — the Q-B/R-A-closed model-class family at smaller amplitude; (b) Apr/May-2024 outage-season over-read remainder (every face governed: D2 freeze / ercot-174 R / ercot-185 K); (c) measured-HH monthly fuel-shape wedge (supports Jan/Apr-2024, Feb-2025; adverse H2-2025); (d) a scoring-basis wedge — the published-adder overlay is in bench `rt_lw_mon` but not scored `pMon` (+0.25/+0.42 $/MWh demand-weighted; Feb-2025 +1.50); (e) hydro/renewables/storage/2025-gas-level ruled OUT. **Board: T-0 do-nothing / T-1 `gas_hh_monthly_shape` input-correctness A/B (RECOMMENDED, ercot-145b posture: fit gain NOT predicted) + T-3b overlay-completeness audit companion / T-2 outage-remainder OWNER-GATED (D2) / T-3a C3b settlement-basis scoring = rubric change, owner-only / T-4 sub-tail formation REFUSED on Q-B/R-A.** | Verified cycle 4: 4 files, all new (no matrix edit, no field, no keeper/registry/bench touch); ceiling stated first with Q-B+R-A citations, 2023 only in the ceiling citation; probe validates against the C3c ledger counts (53/22, 31/1); §5 cites every matrix cell checked (G/K/R/U) with `diurnal_price_amplitude` untouched per PRECOMMIT §0(b); log entry +74 lines. **Card T → OWNER sitting.** |
| **HYGIENE-2** (child session `session_01TWoByqhaqZE6MVwHJeNg5D`, dispatched cycle 4) | **LANDED, REVIEW-READY — verified cycle 5.** One commit `8653317` on `claude/ercot-scar-hygiene-2-replay-diagnostics` off `5b05f84`, push-and-stop honored (no PR). The replay driver now invokes the SAME legitimacy-diagnostics post-step the normal calibration path uses (`legitimacy_diagnostics` main() with the `calibration_verdict._LEGIT_HOWTO` argv) on the output bundle after solve+date-restore — same suite, same CLI surface, no second implementation (the §2.5 seam-reuse requirement, met); a gate FAIL or suite crash is loud but never discards the completed solve. | Verified cycle 5: exactly 2 files — `scripts/replay_keeper.py` +58, new `tests/scoring/test_replay_keeper_diagnostics.py` (161 lines: argv contract in-place and --out-dir, artifact lands in the output bundle, error tolerance; solve stubbed, no LP). No src/market_sim edit, no matrix, no registry. Worker reports 92 tests pass, pushed blobs verified. **AWAITING LANDING** with the other two branches. |

### Dependencies tracked, not tasked (boundary: FFR-FH manager, addenda AP/AQ/AR)

- **OVERRIDE-FIX / FFR-9C stage-B — LANDED** (PR #3915,
  "OVERRIDE-FIX: make an ISO-armed flag turn-off-able at the config seam";
  FFR-FH pack addendum AS records both §0ar lanes landed and accepted). For
  THIS workstream it changes nothing actionable: the S3 promotion hold it
  once gated is MOOT (L-1 died at V0). The boundary stands — that lane was
  and is the FFR-FH manager's; this row is now historical tracking only.

### Next round (sequenced cycle 1; dispatch on later cycles as slots clear)

1. ~~FIX-IT-1 completes~~ — CLOSED IN-CYCLE: #3912 merged by its own worker;
   FIX-IT-1 moot (A2).
2. ~~HYGIENE-1b completes~~ — DONE cycle 3: verified, review-ready at
   `9e3a6c4`; **landing awaits the owner's convention answer.** Remaining
   hygiene backlog: (i) the replay path writes no
   `legitimacy_diagnostics.json` (ercot-193 disclosure — generated manually
   there); (ii) ERCOT-137 pooled-vs-anchored convention — OPEN in the DOF
   ledger, inside band, NOT quick-dispatch material.
3. ~~SHAPE-CHARTER-1 completes~~ — DONE cycle 4: verified, review-ready at
   `3395389`; **card T queued for the owner sitting** alongside the L-SCAR
   adjudication.
4. **L-SCAR lane** — BLOCKED ON OWNER (V0-FAIL adjudication; the manager
   dispatches nothing here on its own authority).
5. ~~HYGIENE-2 completes~~ — DONE cycle 5: verified, review-ready at
   `8653317`. **The owner-independent queue is now EMPTY**: T-1/T-3b
   execution needs card T signed; T-2 needs a D2 unfreeze; T-3a is rubric
   (owner-only); T-4 refused; L-SCAR routes all owner-gated. Cycles are
   verify-and-flag only until the owner acts; check-in interval lengthens
   after consecutive quiet cycles.

### Owner decisions pending — TWO remain as of cycle 8 (the merge items
and the landing convention were discharged by the #3914–#3924 batch; see the
§0 header). Historical text of the original five kept below unchanged:

- **L-SCAR V0-FAIL adjudication** — L-1's pre-registered identification gate
  failed with a model-free non-identifiability proof; S1's instruction ("stay
  inside that distinction or stop") was honoured. The charter's named routes,
  none dispatchable by the manager: (a) **L-0 fallback** — enter the second
  `readiness_limits` row (screen's measured ~50–70 $/kW-yr merchant-revenue
  understatement) and re-classify frontier rank 2 "open lane" → "accepted
  limit" (card §6 says this re-classification is owner-only); (b) **charter
  L-2** (E1 dispersion repair — structural complement; expected reach
  single-digit-to-~20 $/kW-yr of the gap, per the card's own bound); (c) a
  **new card for regime-conditioned identification** (condition on market
  DESIGN — ORDC vintage/ECRS/SWCAP/RTC+B — the variable the anchors actually
  exhibit; NOT authorized by S1/S2, and the forward regime has zero measured
  anchors until the 2026 SOM publishes ~mid-2027); (d) any combination,
  or park the lane.
- **Worker landing convention** — the manager's §1 fence 6 reads "no PRs
  unless the owner asked", yet every recent worker deliverable landed via a
  self-merged PR (#3906/#3911/#3912). HYGIENE-1 is parked at push-and-stop
  pending the owner's word: (a) authorize workers dispatched by this manager
  to open+merge PRs for verified in-scope landings (the observed repo
  convention), or (b) owner merges manager-verified branches, or (c) another
  route. Until answered, every manager dispatch lands push-and-stop.
- **Merge the two verified branches** (cycle 3–4): the hygiene fix
  `claude/ercot-scar-hygiene-1-dashboard-sidecar` @ `9e3a6c4` and the
  ercot-196 card `claude/ercot-scar-shape-charter-1` @ `3395389` — both
  manager-verified, both off current main, zero conflict risk between them
  (disjoint files). Acting on either also answers the convention question by
  example.
- **Card T signature** (`docs/DECISION-CARD-ercot196-shape-2024-2025-2026-08-13.md`
  §0/§4): recommendation **T-1** (`gas_hh_monthly_shape` input-correctness
  A/B, ercot-145b posture, guards on every PASSing gate) **+ T-3b** (adder
  overlay-completeness audit, read-only companion); T-0 meanwhile; T-2 stays
  behind the D2 freeze unless the owner unfreezes; T-3a named as a rubric
  question, not proposed; T-4 refused on Q-B/R-A. The manager executes
  nothing from this card without the signature.

---

## §1 STANDING FENCES — carried by every prompt this manager authors

1. **Rule 27 model assignment**: Opus/Fable for anything touching `src/`,
   `scripts/run_*` / `scripts/score_*`, `CLAUDE.md`, the spec, or workflows;
   push-integrity — blob-verify any pushed file ≥300 lines (both transports);
   never bulk-rewrite core files from regenerated content.
2. **Rule 12**: years sequential within a single invocation; separate
   invocations may run concurrently (cap ~2 for per-plant multi-zone LPs).
3. **Rule 22**: ERCOT holds NO `complete`/`final` marker — solve/score years
   {2023, 2024, 2025} ONLY, no exceptions; data intake unrestricted
   (2026-08-06 clarification: what is held out is the score, never the data).
4. **Rules 15/28**: every run registered in-session (backcast lanes → backcast
   registry; L-SCAR/forecast lanes → the FORECAST namespace via
   `scripts/register_forecast_run.py`, NEVER crossed); matrix cell/row updated
   in the same PR/session; `scripts/check_mechanism_matrix.py` exit 0.
5. **No GitHub-Actions offloading** (private repo, billed minutes); no new
   workflows; no cron without owner sign-off.
6. **No PRs unless the owner asked**; small-pack pushes (fresh fetch first;
   run payloads over `git push`, small multi-file commits over `push_files`).
7. **Standing rulings cited in every prompt**: card Q = (Q-B) FINAL — no
   C3a-2023 spend; card R = (R-A) — no C3b-2023-targeted determination rounds;
   L-SCAR §4 must-nots verbatim for anything in that lane. Residuals reported
   at full magnitude, never the basis of a direction-blind outcome.
8. **DO-NOT-REDO**: check `docs/mechanism-testing-matrix.md` §5.1 + the ERCOT
   shard before any lever prompt; never re-test an adjudicated `R`/`I`/`G`
   cell without new evidence.
9. **Boundary**: OVERRIDE-FIX / FFR-9C stage-B belongs to the FFR-FH manager.
   Track as dependency; never task it; conflicts escalate to the owner.
10. **Keeper-shard edits** → spawn `calibration-keeper-auditor` scoped
    `--iso ERCOT` in the same cycle.

---

## §2 DISPATCHED PROMPTS (verbatim)

### §2.1 FIX-IT-1 — land PR #3912 (cycle 1, 2026-08-13; child session `session_01Ne18N4kQa3EPfZ7pCbN8FL`)

```
ERCOT-SCAR FIX-IT-1 — dispatched by the ERCOT-SCAR workstream manager (cycle 1, 2026-08-13; pack docs/handoffs/ercot-scar-workstream-pack-2026-08.md §2.1 once it lands).

ONE MECHANICAL TASK: land PR #3912 — the ercot-195 / L-SCAR-SCREEN-2 V0-stop deliverable on branch claude/l-scar-screen-2-implement-lo897d — which is merge-conflicted against main (mergeable_state "dirty"; PR #3911 merged 10 s before it was opened and both append to docs/calibration-log/ercot.md). You do NOT re-open, re-fit, extend, or edit the deliverable itself in any way.

STANDING RULINGS you inherit and cite, never re-litigate:
- Card Q = (Q-B) FINAL (docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md; licence re-test FAILED at ercot-191, L1 0.3857 vs 0.90): NO ERCOT C3a-2023 spend of any kind, ever.
- Card R = (R-A) (docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md): NOT-YET stands as the public claim; no C3b-2023-targeted determination rounds.
- L-SCAR S1/S2/S3 signed (docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md): the lane ran to its pre-registered V0 identification gate and FAILED it (docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md, on the branch); per S1 ("stay inside that distinction or stop") the lane STOPPED, correctly. Your task is landing its report — the stop IS the deliverable. The follow-on routes (L-2, a regime-conditioning card, L-0 disclosure) are OWNER decisions; take none of them.

STEPS:
1. git fetch origin main claude/l-scar-screen-2-implement-lo897d; git checkout claude/l-scar-screen-2-implement-lo897d.
2. git merge origin/main. EXACTLY ONE conflict is expected: docs/calibration-log/ercot.md — main's ercot-193 SOC re-gate entry vs the branch's ercot-195 entry. Resolve by KEEPING BOTH entries whole, ordered per that log's existing convention (session order, ercot-193 before ercot-195), changing no other line of either entry. If ANY other file conflicts, STOP and report; resolve nothing else.
3. Verify locally BEFORE pushing: (a) python3 scripts/check_mechanism_matrix.py exits 0; (b) both log entries present and intact in docs/calibration-log/ercot.md; (c) the merge introduced no change to the four SOM PDFs under data/raw/ERCOT/ or to data/raw/som-competitive-conduct/.
4. Push the merge commit: git push -u origin claude/l-scar-screen-2-implement-lo897d (retry only on network failure, exponential backoff). Rule 27 blob-verify: docs/calibration-log/ercot.md is ≥300 lines — after pushing, fetch that blob back from the remote branch and compare line count + content hash to local before proceeding.
5. Update PR #3912 (mcp__github__update_pull_request): title "ercot-195: L-SCAR V0 FAIL — R_f non-identifiable from measured tightness; lane stops at V0 (SOM anchors 3→7 vintages)". Body: summarize the FINDING faithfully at full magnitude — V0 4/14 folds vs required 14/14 on the best of eight candidate forms; the model-free identifiability bound (near-tied tightness pairs carry $94–$330 irreducible error vs the $15 fold tolerance; 2019 vs 2020 sit within 1.7% on prc_mean yet paid 127 vs 39 $/kW-yr); ex-Uri sensitivity WORSE (2/14); the monitor's own attribution of the 2021/2022/2023 levels to regime/event (Uri under $9k SWCAP; "primarily due to the ORDC changes"; ECRS = 50% of 2023 net revenue), i.e. the rent series is a regime series, not a tightness series; intake deliverable 3→7 SOM vintages, schema-validated with source_doc+source_page; NOTHING built — no ScenarioConfig field, no matrix row (rule 28c not triggered: no field), no A/B, no registration, no promotion; screen-revenue movement produced: $0.00/kW-yr; frontier rank 2 stays OPEN; the three follow-on routes are owner decisions, none taken. Cite Q-B and R-A as standing rulings. End the body with the Claude Code attribution footer.
6. Confirm the PR reads mergeable (conflict cleared). If CI checks run on the PR, wait for them to complete (up to ~20 min); any failure → report it verbatim and STOP (do not merge, do not force, do not re-run more than once). Otherwise merge PR #3912 with a merge commit.
7. Report back: merged SHA, guard outputs, and confirmation that the only content you authored is the conflict resolution and the PR title/body.

FENCES (standing, non-negotiable): no src/ edits; no LP solve; no year solved or scored (rule 22 — ERCOT holds no complete/final marker; {2023,2024,2025} only, and nothing here solves anyway); no ScenarioConfig field; no matrix row/cell edit; no keeper/registry/bench file touched; no new .github/workflows (private repo, billed minutes); no other PRs; no push to any branch except claude/l-scar-screen-2-implement-lo897d; small-pack pushes only (fresh fetch first). If anything outside this scope looks necessary, STOP and report to the manager instead of doing it.
```

### §2.2 HYGIENE-1 — dashboard_add_run sidecar path bug (cycle 1, 2026-08-13; child session `session_013ADXP9Kq5nGEAqsrB6WoKh`, repo source attached)

```
ERCOT-SCAR HYGIENE-1 — dispatched by the ERCOT-SCAR workstream manager (cycle 1, 2026-08-13; pack docs/handoffs/ercot-scar-workstream-pack-2026-08.md §2.2).

ONE MECHANICAL TASK: fix the `dashboard_add_run` metrics-sidecar relative-path bug at root, with a regression test. This is card-R (R-A) re-pointed hygiene bandwidth (docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md, signed 2026-08-13: ERCOT bandwidth goes to protective/hygiene defects, the 2024/2025 shape queue, standing re-gates, forecast readiness — never the 2023 price criteria).

THE DEFECT (filed at ercot-193: docs/calibration-log/ercot.md "Disclosures" block of the ercot-193 entry, and results/calibration/FINDING-ercot193-soc-regate-2026-08-13.md §4): `scripts/dashboard_add_run.py`'s metrics-sidecar write has a relative-vs-absolute path bug; the ercot-193 session worked around it by calling `calibration_verdict.write_metrics_sidecar` directly on the resolved path. Diagnose the actual defect in the script (where the sidecar path is composed against the CWD instead of resolved against the bundle/out dir), fix it minimally at root, and add a pytest that fails on the old behavior (invoke the write from a non-repo CWD against a tmp bundle dir and assert the sidecar lands in the bundle dir, not the CWD). If the true defect turns out to live in `calibration_verdict.write_metrics_sidecar` or another shared seam instead of `dashboard_add_run.py`, STOP and report to the manager rather than widening scope.

STANDING RULINGS you inherit and cite, never re-litigate: card Q = (Q-B) FINAL (docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md; licence re-test FAILED at ercot-191) — NO ERCOT C3a-2023 spend of any kind; card R = (R-A) — NOT-YET stands, no C3b-2023-targeted determination rounds. This task touches neither: tooling only.

FENCES AND DUTIES:
- No LP solve, no run registered, no year solved/scored (rule 22: ERCOT holds no complete/final marker; {2023,2024,2025} only — and this task solves nothing). No ScenarioConfig field, no matrix row or cell (no mechanism — rule 28c not triggered). No keeper/registry/bench/dashboard-data edits — the fix is the SCRIPT plus its test, nothing else.
- Rule 27: edit locally with the Edit tool, never regenerate a file wholesale; after pushing, blob-verify any touched file ≥300 lines (fetch the pushed blob, compare line count + content hash to local). Rule 11: docstrings on any new/changed public function.
- Testing: tmp-dir test, no network, no real bundle; also run the existing tests covering dashboard_add_run / calibration_verdict (pytest -k, report the command and results verbatim).
- LANDING: create branch claude/ercot-scar-hygiene-1-dashboard-sidecar off latest origin/main, commit, push (small pack — fresh fetch first), and STOP THERE. Do NOT open a PR and do NOT merge — the manager carries the landing question to the owner. Report back: branch name, commit SHA, the diff summary, test output, and blob-verification result.
- No new .github/workflows (private repo, billed minutes). No pushes to any other branch. If anything outside this scope looks necessary, STOP and report to the manager instead of doing it.
```

### §2.3 HYGIENE-1b — re-dispatch with provisioning preamble (cycle 2, 2026-08-13; child session `session_011sYFijAwLntGLjFM1do3vp`)

Identical to §2.2 in task, rulings, fences and landing (push-and-stop on
`claude/ercot-scar-hygiene-1-dashboard-sidecar`), with this PROVISIONING
preamble prepended and NO `source_url` on the dispatch:

```
PROVISIONING — DO THIS FIRST, exactly as written. Your session starts with NO repository checked out:
1. Call the add_repo tool (from the claude-code-remote MCP server; load via ToolSearch "add_repo" if deferred) with owner="jessicacohen554-cyber", repo="market-simulator", access="push". Do NOT pre-check the repo with curl/ls-remote/gh — unauthenticated probes 404 on private repos; call add_repo directly. If it returns an authorization error, STOP and report the exact error text back to the manager; do not retry.
2. Clone BLOBLESS using the clone command/URL add_repo returns, adding --filter=blob:none (a full or shallow clone of this repo stalls — 7.37 GiB is live at tip; see docs/fast-clone.md after checkout). Then call register_repo_root with the clone path.
3. This task needs NO data/raw hydration (profile `code` semantics): do not run hydrate_data.py, and never resolve blobs under data/raw — run read-side git commands under GIT_NO_LAZY_FETCH=1.
```

### §2.4 SHAPE-CHARTER-1 — 2024/2025 monthly-shape decision card (cycle 3, 2026-08-13; child session `session_018hZXhKv19qih79y62t1uPw`)

```
ERCOT-SCAR SHAPE-CHARTER-1 — dispatched by the ERCOT-SCAR workstream manager (cycle 3, 2026-08-13; pack docs/handoffs/ercot-scar-workstream-pack-2026-08.md §2.4).

PROVISIONING — DO THIS FIRST, exactly as written. Your session starts with NO repository checked out:
1. Call the add_repo tool (from the claude-code-remote MCP server; load via ToolSearch "add_repo" if deferred) with owner="jessicacohen554-cyber", repo="market-simulator", access="push". Do NOT pre-check the repo with curl/ls-remote/gh — call add_repo directly. If it returns an authorization error, STOP and report the exact error text to the manager.
2. Clone BLOBLESS using the clone command add_repo returns, adding --filter=blob:none (a full or shallow clone stalls — 7.37 GiB live at tip; docs/fast-clone.md). Then call register_repo_root with the clone path.
3. No data/raw hydration (profile `code` semantics); never resolve blobs under data/raw; run read-side git under GIT_NO_LAZY_FETCH=1. You WILL need the keeper's committed hourly sidecars and bench under results/calibration/ and frontend/data/backcast/ — those are regular tree paths, fetch only what you read.

TASK — MEASURE-FIRST CHARTER ASSEMBLY, DOC-ONLY, NO SOLVE. Assemble the decision card for the 2024/2025 monthly-shape object that signed card R (R-A) re-pointed ERCOT bandwidth to, named by docs/PRECOMMIT-ercot193-soc-regate-2026-08-13.md §0(c) as "the outage-season/fuel-shape monthly object … 2024/2025 shape work for a later charter" (2024 shoulder-months negative / summer positive; 2025 worst April–May). Deliverable: a decision card at docs/DECISION-CARD-ercot<NNN>-shape-2024-2025-2026-08-13.md under the next free session shorthand (read the tail of docs/calibration-log/ercot.md for "Next shorthand" and claim it) + a calibration-log entry, landed PUSH-AND-STOP on branch claude/ercot-scar-shape-charter-1 off latest origin/main. NO PR, NO merge.

METHOD (the ercot-189/ercot-193 read-only card precedent):
1. DO-NOT-REDO FIRST: read docs/mechanism-testing-matrix.md §5.1 (the ERCOT queue) and the cell verdicts in docs/codebase-site/data/mechanism-matrix/ERCOT.js. Any lever the card proposes is checked against adjudicated R/I/G cells — never propose re-testing one without new evidence, and cite each cell checked. Also honor the PRECOMMIT §0(b) refusal: diurnal_price_amplitude is a cross-ISO audit row, stays U — do not re-adjudicate it.
2. SIZE THE OBJECT FROM COMMITTED ARTIFACTS ONLY: the keeper 2026-08-12-run192-arm-coal-peak's registered dashboard payload + hourly sidecars (results/calibration/ercot192_arm_B or its byte-identical ercot193_arm_soc replay) + committed bench actuals, using the rubric's own C3b arithmetic (pattern: scripts/probes/ercot193_c3b_decomposition.py). You MAY add a read-only probe script under scripts/probes/ writing to results/calibration/. Report the 2024 and 2025 per-month model/actual/residual tables at FULL magnitude; identify which months carry the squared residual; attribute candidate physical objects (maintenance/outage-season shape, fuel-shape/basis months, hydro/renewable months, …) from the committed diagnostics (legitimacy_diagnostics.json D-1/D-2 rows, reserve_family/system hourlies) — measured attribution, not narrative.
3. STATE THE CEILING UP FRONT (card R consequence, mandatory sentence): 2024 C3b = 0.135 and 2025 C3b = 0.096 both already PASS; this is SHAPE-QUALITY and forecast-readiness work, never determination work — ERCOT's determination stays NOT-YET regardless (rulings Q-B and R-A standing, cite both). The card must state concretely what the work buys (which reported numbers improve, which forecast-readiness properties strengthen).
4. THE OPTION BOARD, ercot-189-style: do-nothing as the honest baseline (with the bias it accepts, stated measurably), plus named structural candidates — each with (a) its external driver, (b) rule-13 admissibility argued per option, (c) expected reach bounded from the measured record, (d) its cost row. End at an owner-sitting board with a recommendation. NO option is executed in this session.

FENCES: rulings Q-B (NO C3a-2023 spend of any kind; docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md) and R-A (no C3b-2023-targeted rounds — 2023 appears ONLY in the ceiling citation; docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md); the L-SCAR lane is stopped at V0 and is NOT yours (docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md). No solve, no LP, no year solved; actuals enter counterfactual re-scoring of committed payloads only (rule 13 clean, the ercot-189 footing; rule 22: ERCOT holds no complete/final marker, artifacts referenced stay in {2023,2024,2025}). No ScenarioConfig field; no matrix cell or row edit (a card is a read, not a mechanism test — the ercot-182/189 precedent; record this in the card's governance section). No keeper/registry/bench edits. Rule 27: you are Opus/Fable; blob-verify any pushed file ≥300 lines (fetch the pushed blob, compare line count + hash to local). No new .github/workflows. Small-pack push (fresh fetch first). Report back: branch, commit SHA(s), the card's board table verbatim, and the log-entry text. If anything outside this scope looks necessary, STOP and report to the manager.
```

### §2.5 HYGIENE-2 — replay-path legitimacy_diagnostics gap (cycle 4, 2026-08-13; child session `session_01TWoByqhaqZE6MVwHJeNg5D`)

Provisioning preamble as §2.3. Task core (full prompt in the dispatch record):

```
ONE MECHANICAL TASK: close the ercot-193-disclosed replay-path tooling gap — "The replay path writes no legitimacy_diagnostics.json; generated for both bundles so C8 scores (PASS both)" (docs/calibration-log/ercot.md ercot-193 "Disclosures"; FINDING-ercot193-soc-regate-2026-08-13.md §4). Card-R (R-A) hygiene bandwidth.

DIAGNOSE FIRST: read scripts/replay_keeper.py and find how the normal solve path (scripts/run_calibration_full.py) produces a bundle's legitimacy_diagnostics.json (inline write vs a post-step calling scripts/legitimacy_diagnostics.py). Make the replay path produce it the SAME way — reuse the existing generation seam, add no second mechanism (rule-19 spirit). If generation needs solve-time state a replay does not have, do NOT approximate — STOP and report. If the right change lands anywhere other than scripts/replay_keeper.py (plus a small shared-helper extraction), STOP and report before widening scope.

Regression test: tmp-dir, exercises the diagnostics-write seam without an LP solve (fixture bundle; docs/testing.md patterns, trivial-first). Run existing replay_keeper / legitimacy_diagnostics tests (pytest -k, report verbatim).

Rulings cited: Q-B final (no C3a-2023 spend), R-A (no C3b-2023 determination rounds) — tooling only, touches neither. FENCES: no LP solve, no run registered, no year solved/scored (rule 22); no ScenarioConfig field, no matrix edit; no keeper/registry/bench/dashboard-data edits; no src/market_sim/ edits (STOP if needed); rule 27 edit-local + blob-verify ≥300-line pushed files; rule 11 docstrings. LANDING: branch claude/ercot-scar-hygiene-2-replay-diagnostics off latest origin/main, push, STOP — NO PR, NO merge. Report: branch, SHA, diff summary, test output, blob-verify.
```

---

## §A ADDENDA (append-only; dated; old addenda are never rewritten)

### A1 — 2026-08-13, cycle 1 seed

Board seeded at origin/main `016b659`. Facts established this cycle:

1. **ercot-194 pending-merge flag CLEARED**: `3bfd33a` (both cards'
   RESOLUTIONS) is an ancestor of main via PR #3904.
2. **SOC-REGATE-EXEC verified LANDED and duty-complete** (PR #3911; detail on
   the §0 board). RG-PASS, keeper unchanged/byte-identical, both runs
   registered, matrix guard exit 0. The ercot-167 standing expectation is
   DISCHARGED in matrix + log; lane CLOSED-CLEAN.
3. **L-SCAR-SCREEN-2 stopped at V0, per its charter** — a correct stop, not a
   failed worker: identification is structurally impossible on this data
   (model-free bound), and the worker refused to ship an unidentified knob
   (the §2.6 distinction working exactly as the owner signed it). The
   deliverable (intake 3→7 vintages + deriver-as-standing-test + FINDING) is
   conflicted in PR #3912; FIX-IT-1 dispatched to land it verbatim.
4. **The S3 promotion hold behind OVERRIDE-FIX is MOOT for L-1** (nothing to
   promote). The L-SCAR lane is BLOCKED ON OWNER adjudication of the V0 FAIL
   (§0 decision bullets). The manager dispatches nothing in that lane.
5. Environment note for successor cycles: this manager session runs on a
   data-profile fast clone (most of the tree staged-deleted on disk); read
   repo files via `git show origin/main:<path>`, materialize selectively with
   `git checkout origin/main -- <path>`, and commit the pack path-scoped
   (`git commit -- docs/handoffs/ercot-scar-workstream-pack-2026-08.md`) so
   the profile's staged deletions never enter a commit.

### A2 — 2026-08-13, cycle 1 close-out corrections (same cycle, second commit)

1. **PR #3912 was MERGED at 05:28:59Z — 34 s before FIX-IT-1 was dispatched
   (05:29:33Z).** The original L-SCAR worker landed its own deliverable:
   rebase onto main (the log conflict resolved in the rebase), a provenance
   re-stamp confined to the FINDING (`cfad808`, +7/−1), merge at `cfb8127`.
   Manager verified the landed content on main (both log entries in order,
   FINDING present, PR counters 873/21/11 consistent with the branch +
   re-stamp). FIX-IT-1 did nothing: it also failed to clone (see 2) and
   self-archived at 05:31Z. Board corrected; manager unsubscribed from #3912.
2. **Dispatch mechanics lessons (binding on future cycles):**
   (a) re-read the target PR/branch state IMMEDIATELY before dispatching a
   fix-it — the manager's `dirty` read was ~2 min stale and the window was
   live; (b) child sessions created via `create_session` do NOT inherit the
   repo attachment — pass `source_url` (+`source_revision`) or the child
   cannot clone (FIX-IT-1's failure mode). HYGIENE-1 was dispatched with the
   source attached and is the pattern to copy.
3. **HYGIENE-1 dispatched** (§2.2): the ercot-193-filed `dashboard_add_run`
   metrics-sidecar relative-path defect, root-fix + regression test,
   push-and-stop landing on `claude/ercot-scar-hygiene-1-dashboard-sidecar`
   (no PR, no merge) pending the owner's landing-convention answer (§0 owner
   decisions). Card-R hygiene bandwidth; no solve path touched.
4. **Transport note for this manager's own pack commits:** porcelain
   `git commit`/`git push` hang on this data-profile clone (index scan /
   partial-clone pack negotiation). Working recipe: plumbing commit
   (`hash-object` → temp-index `read-tree`+`update-index --cacheinfo` →
   `write-tree`/`commit-tree`/`update-ref`) — or, simpler and preferred for
   this small text file, `mcp__github__create_branch` once +
   `mcp__github__push_files` per cycle, then blob-verify (cycle 1 verified:
   local and remote blob both `b1c117b9`).

### A3 — 2026-08-13, cycle 2 (self check-in, 07:51Z trigger)

1. **PR #3913: the OWNER merged this pack's seed commit (`4035ac7`) to main**
   (`5b05f84`). Read as: the pack belongs on main; the owner is reading it.
   Main's copy lags the branch (it predates the A2 close-out corrections);
   the branch stays the live copy — the owner can merge again at will. NOT
   read as an answer to the landing-convention question (still flagged).
2. **HYGIENE-1 postmortem — both create_session provisioning modes measured:**
   (a) NO source_url → child has no repo and (FIX-IT-1's record) reports
   access denied if it doesn't call add_repo; (b) WITH source_url → the
   platform attempts a FULL clone and dies at `clone_timeout` on this repo
   (7.37 GiB live at tip; the docs/fast-clone.md failure verbatim,
   `recoverable: false`). HYGIENE-1 never started; archived.
3. **HYGIENE-1b dispatched (§2.3)**: no source_url + an explicit provisioning
   preamble — add_repo(access=push) → `--filter=blob:none` clone →
   register_repo_root; no data hydration; GIT_NO_LAZY_FETCH=1. This is the
   dispatch pattern under test. If 1b also fails at provisioning, worker
   provisioning escalates to the owner (the workstream cannot spawn workers
   any other way within its fences).
4. Owner decisions L-SCAR V0-FAIL adjudication + landing convention: still
   open, re-flagged in the cycle-2 report. No new ERCOT-lane branches or PRs
   this cycle; other lanes' branches (caiso-arm-k, miso-156, neiso-2021,
   iso-armed-flags-turnoff, model-audit) are out of scope and untouched.

### A4 — 2026-08-13, cycle 3 (self check-in, 09:56Z trigger)

1. **HYGIENE-1b LANDED and verified** — the §2.3 provisioning pattern
   (add_repo → `--filter=blob:none` clone → register_repo_root) WORKS and is
   the standing dispatch recipe. Commit `9e3a6c4` on
   `claude/ercot-scar-hygiene-1-dashboard-sidecar`, exactly 2 files
   (`scripts/dashboard_add_run.py` +21/−1; new 126-line regression test that
   was verified failing pre-fix), push-and-stop honored, no PR. Review-ready;
   landing awaits the owner's convention answer.
2. **Manager-session git credentials EXPIRED mid-day** (`could not read
   Username for 'https://github.com'` on fetch/ls-remote; no credential
   helper or askpass configured after idle). Cycle 3 ran entirely over the
   GitHub MCP tools (list_commits/get_commit for inventory and verification;
   push_files for this pack commit). Successor cycles: if local git auth is
   dead, this is the fallback path — and blob-verify via the MCP
   `get_file_contents` sha against local `git hash-object`.
3. **SHAPE-CHARTER-1 dispatched** (§2.4): the card-R-named 2024/2025
   monthly-shape charter assembly, doc-only, committed-artifacts-only,
   DO-NOT-REDO first, ceiling sentence mandatory, owner-sitting option board
   as the deliverable, push-and-stop on `claude/ercot-scar-shape-charter-1`.
4. Main unchanged at `5b05f84` all cycle; no ERCOT-lane branches/PRs beyond
   the two workstream branches; both owner decisions (L-SCAR V0-FAIL
   adjudication; landing convention) remain OPEN and re-flagged. A THIRD
   owner item added by cycle 3: `9e3a6c4` is ready to land — merging it is
   itself an instance of the landing-convention answer.

### A5 — 2026-08-13, cycle 4 (self check-in, 12:06Z trigger)

1. **Local git auth RECOVERED** (fetch works again). The local manager branch
   was reset onto the remote `dac1d8c` (the cycle-3 push_files commit); the
   offline mirror commit `53ba6a9` (content-identical blob `de3f78af`,
   built while auth was dead — see the cycle-3 stop-hook note) is discarded
   unpushed, exactly as its own commit message instructed. No content
   differed.
2. **SHAPE-CHARTER-1 landed and verified** — ercot-196 / card T, review-ready
   at `3395389` (board summary on §0; full verification in the worker table).
   The card surfaces one latent duty for the T-1 executing session: the
   existing default-off `gas_hh_monthly_shape` field carries NO matrix row
   (the rule-28c gap ercot-145 §6 surfaced) — the session that arms the A/B
   closes the row gap in the same PR.
3. **HYGIENE-2 dispatched** (§2.5): the replay-path legitimacy_diagnostics
   gap, diagnose-first, reuse-the-seam, push-and-stop on
   `claude/ercot-scar-hygiene-2-replay-diagnostics`. After it lands, the
   owner-independent queue is EMPTY — all remaining work is behind owner
   signatures (card T, L-SCAR adjudication, landing convention, D2, T-3a).
4. Owner state: absent since the 05:46Z #3913 merge; main unchanged at
   `5b05f84` all day; no open PRs; hygiene fix `9e3a6c4` and card T
   `3395389` both await merge. Owner items now FOUR (§0 list): two merges /
   convention / L-SCAR adjudication / card T signature — the two sittings
   (L-SCAR + card T) can be one sitting.

### A6 — 2026-08-13, cycle 5 (self check-in, 14:26Z trigger)

1. **HYGIENE-2 landed and verified** (detail in the worker table): the
   replay path now writes `legitimacy_diagnostics.json` through the exact
   post-step the calibration path uses — seam reuse as specified, 2 files,
   solve-stubbed regression test, no PR. Third branch on the review-ready
   pile: `8653317`.
2. **Quiet cycle otherwise**: main unchanged at `5b05f84` since 05:46Z; no
   open PRs; no owner action on any of the four §0 decision items. The
   owner-independent dispatch queue is EMPTY as forecast in A5.3 — this was
   a verify-and-flag cycle and the next ones will be too, so the check-in
   interval stretches (next at ~2h; if it is also fully quiet, subsequent
   check-ins move to ~4h to stop burning cycles against an absent owner —
   the pack and the three branches hold all state either way).
3. For the owner, the entire actionable state in one line each:
   **merge `9e3a6c4`** (dashboard sidecar fix), **merge `3395389` + sign
   card T** (T-1+T-3b recommended), **merge `8653317`** (replay
   diagnostics), **answer the landing convention**, **adjudicate L-SCAR
   V0-FAIL** (L-0 / L-2 / regime card / park).

### A7 — 2026-08-13, cycle 6 (16:40Z trigger) — NOOP

Fully quiet: main unchanged at `5b05f84`; `9e3a6c4`/`3395389`/`8653317` all
still unmerged; no open PRs; no owner action on any §0 item; no new lane
branches. Nothing dispatched (queue empty by design). Check-in interval
stretched to ~4 h per A6.2.

### A8 — 2026-08-14, cycle 8 (00:49Z trigger) — the owner's batch merge

1. **Quiet stretch A7→cycle 8 recorded**: cycle 7 (20:46Z) was fully quiet
   and deliberately committed nothing (local git auth was down; a noop
   commit would have required a full-file MCP resend to record nothing —
   the deviation was reported in-chat at the time).
2. **The owner batch-merged #3914–#3924** (main `5b05f84` → `dbde0c2`),
   including all three workstream branches (#3917 hygiene-1, #3916 the
   ercot-196 card, #3920 hygiene-2) and this pack at cycle-6 (#3919), all
   without comment. Convention read: MANAGER-VERIFIED PUSH-AND-STOP
   BRANCHES + OWNER-OPENED/MERGED PRs is the operating mode. Every future
   dispatch keeps the push-and-stop landing.
3. **Card T is merged but NOT signed** (no RESOLUTIONS on main) — T-1+T-3b
   execution stays blocked on the signature. **L-SCAR adjudication** also
   still open. These are the only two owner items.
4. **OVERRIDE-FIX landed** (#3915, FFR-FH lane) — dependency row updated to
   historical.
5. **Transport correction (supersedes the A2.4/A4.2 diagnosis in part)**:
   the FFR-FH lane reproduced the `git push` hang on a 32 KB five-object
   pack and identified it as HTTP/2 negotiation failure, fixed by
   `git config http.version HTTP/1.1` (now in CLAUDE.md Git & Pushing, via
   71ea677). This manager's cycle-1 hang was likely the same object, not
   pack size; the config is now set in this session's clone. Plumbing
   commits + `git push` remain the pack transport, with push_files only as
   the auth-outage fallback.
6. Cadence: owner active again → check-ins tighten back to ~2 h.
