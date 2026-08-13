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

## §0 STATE BOARD — cycle 1, 2026-08-13

**Recorded HEAD (origin/main): `016b659`** (merge of PR #3911).

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
- **PR #3912 (L-SCAR V0-stop deliverable) — CONFLICTED, FIX-IT-1 in flight**
  (see worker table). Single conflict: `docs/calibration-log/ercot.md`
  (both #3911 and #3912 append entries; #3911 merged 10 s earlier).

### Workers

| worker | state | verification |
|---|---|---|
| **L-SCAR-SCREEN-2** (branch `claude/l-scar-screen-2-implement-lo897d`, PR #3912) | **STOPPED AT V0, per charter — V0 FAIL.** Intake succeeded (SOM anchors 3→7 vintages, 2019–2025, schema-validated, source_doc+source_page; 2018 SOM absent from Potomac library and outside working span). V0: best of eight candidate forms = 4/14 folds vs required 14/14; model-free identifiability bound proves NO function of any candidate tightness variable can pass (near-tied pairs carry $94–$330 irreducible error vs $15 tolerance); ex-Uri WORSE (2/14); monitor's own attribution: the 2019–2025 rent series is a REGIME series (Uri/$9k SWCAP; ORDC changes; ECRS = 50 % of 2023 net revenue), not a tightness series. Correctly built NOTHING: no ScenarioConfig field, no matrix row (28c not triggered — no field), no A/B, no registration, no promotion; screen-revenue movement $0.00/kW-yr, stated. | Duties verified cycle 1 against the branch: FINDING (`docs/FINDING-ercot195-lscar-v0-nonidentifiable-2026-08-13.md`) reports at full magnitude with Q-B/S1 citations; log entry present (+76 lines `docs/calibration-log/ercot.md`); rule 22 clean (data intake only, no year solved/scored — the stale quarantine notes in the som README/schema corrected to the 2026-08-06 clarification); deriver `scripts/data/derive_screen_scarcity_rent.py` committed as the standing re-derive test (rule 23 trigger = new SOM/telemetry vintage). DEFECT: PR conflicted → FIX-IT-1 dispatched (§2.1). **Lane adjudication → OWNER (decision bullets, cycle-1 report).** |
| **SOC-REGATE-EXEC** (branch `claude/ercot-193-c3b-ceiling-2xu9lg`, PRs #3906 + #3911, MERGED) | **LANDED — RG-PASS on every gate; ercot-167 standing expectation DISCHARGED; lane CLOSED-CLEAN.** G1 663.7→516.1 MW vs measured 423 (61 % of gap, no overshoot); G2 0.72 (≥0.70); G3 2023 2→2, 2024 6→5, 2025 1→1; G4 C3a-2024 Δ0.989 pp on the unrounded scorer basis (knife-edge disclosed), C3a-2025 Δ0.607 pp; G5 shed identical; G-COAL148 ≈ 0.0 of 0.5 TWh bar; G-REPRO keeper reproduces BYTE-IDENTICALLY (12/12 hourly-sidecar sha256, zero scored-value drift). Keeper UNCHANGED at `2026-08-12-run192-arm-coal-peak` (direction-blind rule honoured). | Duties verified cycle 1: both runs registered (`2026-08-13-ercot193-ctl-nosoc` / `-arm-soc`, backcast registry sidecars + run payloads); retention evictions exactly as pre-registered (run168b-year-curves, run173a-reconc-control; neither the keeper); keeper shard untouched (empty diff on `frontend/data/backcast/keepers/`); matrix ERCOT shard cell + `mechanism-testing-matrix.md` item-10 block updated in the same PR; `scripts/check_mechanism_matrix.py` **exit 0** at 016b659 (236 warnings, all cosmetic line-number anchor drift; 0 errors); calibration-log entry present (+90 lines); precommit pushed pre-solve (`5ad4975`); C3b-2023 side-effect reported with the card-R ceiling stated up front; Q-B/R-A citations present. No keeper-shard edit → no keeper-auditor spawn needed. |
| **FIX-IT-1** (child session `session_01Ne18N4kQa3EPfZ7pCbN8FL`, dispatched cycle 1, 2026-08-13T05:29Z) | IN FLIGHT. Scope: merge main into the L-SCAR branch, resolve the single `docs/calibration-log/ercot.md` conflict both-keep, verify guards, push (rule-27 blob-verify), fix PR #3912 title/body to reflect the actual deliverable, merge on green. Prompt verbatim: §2.1. | Manager subscribed to PR #3912 activity. |

### Dependencies tracked, not tasked (boundary: FFR-FH manager, addenda AP/AQ/AR)

- **OVERRIDE-FIX / FFR-9C stage-B**: the stage-B epoch declaration landed
  (PR #3903); addendum AR adjudicated FFR-9C completion + do-not-push ruling.
  The AP.2 override-precedence defect remains on the FFR-FH board. The S3
  promotion hold behind OVERRIDE-FIX is **MOOT for L-1** (V0 FAIL — nothing to
  promote), but the boundary stands: this workstream never tasks that lane.

### Next round (sequenced cycle 1; dispatch on later cycles as slots clear)

1. **FIX-IT-1 completes** → verify merge, close the #3912 board item.
2. **Hygiene candidate (dispatchable without owner, card R bandwidth):** the
   `dashboard_add_run` metrics-sidecar relative-vs-absolute path bug —
   worked around at ercot-193 (sidecar written directly via
   `calibration_verdict.write_metrics_sidecar`); fix at root. Small,
   Opus/Fable, no solve.
3. **2024/2025 shape-queue charter candidate (dispatchable without owner):**
   the outage-season/fuel-shape monthly object (2024 shoulder −/summer +;
   2025 worst Apr–May) — named by PRECOMMIT-ercot193 §0(c) as "2024/2025 shape
   work for a later charter"; both years' C3b PASS (0.135/0.096), so this is
   shape work, never determination work; any prompt states the card-R ceiling
   up front and checks matrix §5.1 + ERCOT shard first (DO-NOT-REDO).
4. **L-SCAR lane** — BLOCKED ON OWNER (V0-FAIL adjudication; see decision
   bullets in the cycle-1 report; the manager dispatches nothing here on its
   own authority).

### Owner decisions pending (also in the cycle-1 report)

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
