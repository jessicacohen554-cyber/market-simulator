> Status: PROPOSED (2026-10-03) — the orchestrator-desk protocol for the MILP unit-commitment program. It follows the desks that ran before it (SPP/SOCO/NWPP addition desks, the backcast close-out desk) and the lane procedure in `docs/RUNBOOK.md`; where this document and `CLAUDE.md` differ, `CLAUDE.md` governs. The paste-whole prompts are in `HANDOFF-uc-milp-desk-2026-10-03.md`. Plan: `docs/uc-milp-program-plan-2026-10.md` (its §8, §11, §12 are the desk's ledger).

# CHARTER — the UC-MILP desk

## 0. Role, in one paragraph, and the never-list

The desk directs the program by chartering lanes and shards in the order that keeps them collision-free, grading their output by content, composing and scoring what shards return, serving the owner's decision cards, and keeping the plan's ledger current. It is a **zero-LP** session with `DATA PROFILE: code`. Model: Fable (adjudication); lanes Opus or Fable; Sonnet never (rule 27).

The desk **never**: runs an LP or MILP (rule 32); edits `src/`, `scripts/`, `tests/`, `configs/`, `frontend/`, `docs/codebase-site/`, the spec or `CLAUDE.md` (lanes own those; the amendment lands in its own PR on D-1); arms `unit_commitment_milp` in any keeper recipe; registers a run as a keeper without an owner ruling (rules 31, 35); deletes a result (rule 31); launches a shard on a branch name (SHA only); lets a shard outlive its verified fetch (rule 33); reads green CI as a discharged duty; merges an engine PR that flips a default; opens a cron or per-task workflow.

## 1. Session roles

| Role | Model | DATA PROFILE | Solves? | Owns (files, regions) | Deliverable |
|---|---|---|---|---|---|
| **Desk** | Fable | `code` | no | plan §8/§11/§12, this charter's errata, decision cards, PR merges in the desk slot | rulings recorded, lanes chartered, spans composed and scored |
| **Research lane UC-0** (benefit screen) | Fable | `code` + keeper bundles (`git` tree reads; hydrate only what the probe reads) | no | `scripts/probes/_ucmilp_benefit_screen.py`, `results/phase0/xiso/_ucmilp_*.json`, `docs/records/governance/uc-milp-2026-10/FINDING-uc-milp-benefit-screen-*.md` | the board (GATESPEC §1–2), cluster census, rule-19 floor census per ISO, DOF ledger draft |
| **Engine lane UC-1** | Opus or Fable | `code` (+ one ISO for the slow test) | no — its benches run in bench shards | `src/market_sim/model/uc/`, `src/market_sim/pipeline/uc.py`, the one `run_energy_solve` hunk, `data/floor_mechanisms.py` (id 28), `config/scenarios.py` (fields + validators), `solve_surface_declared.py` (generated), `scripts/data/derive_uc_cluster_params.py`, `scripts/lib/uc_bench.py`, `scripts/diagnostics/bench_uc_ladder.py`, `scripts/probes/_ucmilp_compose_span.py`, `tests/unit/model/uc/`, matrix row + every shard's cell line, `docs/codebase/` page | one PR, default-off, G-OFF…G-TESTS green (GATESPEC §4) |
| **Bench shard** | Opus | `<iso>` | yes — one rung | `results/bench/uc/<iso>_<y>_<rung>/` pushed on its own branch | the rung's report (GATESPEC §3) in its final message |
| **Golden shard** | Opus | `<iso>` | yes — one keeper replay at the engine SHA, gate off | its own out-dir | golden-diff PASS/FAIL with numbers |
| **A/B lane UC-2** (per ISO) | Fable | `code` | no — launches solve shards | its PRECOMMIT/RESULT, its ISO's matrix cell, its composed span under `results/calibration/ucmilp_<iso>_span` | RESULT with the gate table (GATESPEC §5–6) |
| **Solve shard** | Opus | `<iso>` | yes — one ISO-year | `results/calibration/ucmilp_<iso>_<y>/` on branch `claude/ucmilp-<iso>-<y>` | the standard shard report + the wall table row |
| **Forecast lane UC-3** | Fable | `code` + `neiso` | no — one forecast shard | its RESULT, the forecast dashboard registration | parity table |

## 2. The desk's first act, every sitting

1. Read freshly: `CLAUDE.md` in full; the plan (§8 rulings, §11 log, §12 lanes); `docs/RUNBOOK.md`; GATESPEC; the FINDINGs of lanes that landed since the last sitting; `frontend/data/backcast/keepers/<ISO>.json` for every ISO a lane will touch (keepers move daily — the control is whatever is designated at launch, named by bundle in the PRECOMMIT).
2. Pin main: `git fetch origin main && git rev-parse origin/main`; record the SHA in the §11 line. Recreate the desk branch fresh off `origin/main` (`claude/ucmilp-desk-r<NN>`); if the harness assigns a name, use it and record both.
3. Grade every chartered lane **by content**: `git log origin/main --grep=<lane-id>`, merged PRs, then open the cited FINDING/RESULT and check the artifact says what the dispatch says. Ask the lane before grading it LOST; never read green CI as a discharged duty (the matrix guard's validate mode checks nothing about registration).
4. Deconflict: the calibration lanes of the close-out program write keeper shards, matrix shards, `iso_configs.py` and `constants.py` daily. Before chartering a lane that touches a shared surface, read the close-out plan §6 desk log and name the disjoint region in the prompt, or hold the lane and record the hold in §12.
5. Serve due decision cards (§6) as clickable cards via `AskUserQuestion` (2–4 options, recommendation first and labelled). Record every ruling verbatim and numbered in plan §8.
6. Run the zero-LP gates and record exits: `audit_keepers --check`, `check_registry_payload_parity`, `check_mechanism_matrix`, `check_cache_key_registration`, `check_rubric_freeze`.
7. Sweep shards: every shard in §12 that has reported is fetched, verified and archived in this sitting (§4); every shard still PENDING after 45 minutes is archived and relaunched; name any left alive and why.

## 3. Issuing a lane

One fenced block per lane, self-contained, copied from the HANDOFF templates and edited only to pin SHAs, bundles, the selected ISO-years and the readings — never to widen a charter. Line 1: `You are lane UC-<id>. MODEL: <Opus|Fable> — <why>. DATA PROFILE: <profile>. Branch stem: claude/ucmilp-<id>-<slug>-<4 random chars>.` Then: PRECONDITIONS (verify with `git log`; STOP if unmet) · FILES YOU OWN (paths + regions) · FILES YOU MUST NOT TOUCH (with the owning lane) · the task · the rulings that scope it (D-*) · the PRECOMMIT requirement if anything solves · RULES THAT BITE by ID · EXIT / DELIVERABLES (FINDING/RESULT path with a `## Log entry` section; the lane's own matrix cell as the last commit after rebase) · the closing line (push by pack size; fetch-back verify every pushed file ≥ 300 lines; no CI workflows; no default moves; no solve outside the PRECOMMIT; route anything outside your regions to the desk in your FINDING).

Collision rules (inherited, enforced): a lane touches no shared record (plan, calibration log, CHANGELOG, keeper stamp) — the desk writes those from the lane's `## Log entry`; a lane edits only its own ISO's matrix cell (the engine lane's birth row is the exception, one `U` line per shard); rebase, never merge-in; one PR per lane, opened when the lane is DONE; disjoint regions — a second lane needing the same file is a desk sequencing error, so STOP and route. Record the issued stem **and** the realised branch in §12; they never match. Close every sitting that issues lanes with "dispatch is unconfirmed until a branch exists".

## 4. Shards: launch, verify, archive

```
engine PR merged ──► SHA=$(git rev-parse origin/main)  (40 chars; never a branch)
   bench rung:   create_session(source_url=repo, source_revision=SHA, prompt=<HANDOFF block D, rung filled in>)
   golden:       create_session(..., prompt=<block E>)            one per ISO, gate off
   A/B year:     python3 scripts/shard_prompt.py --iso <ISO> --all-years --sha $SHA --lane ucmilp-<iso> \
                   --bundle results/calibration/<keeper bundle> --set unit_commitment_milp=true [--set <rule-19 offs>] \
                   --budget <from the ladder: ceil(1.3 × L3 total minutes)> --note "ucmilp-<iso>: UC A/B"
                 commit the printed prompts to the lane branch; the shard `git show`s its prompt (NWPP-NEXT-25 gotcha)
shard reports ──► git fetch origin <shard branch> ; git ls-tree -r <sha> -- <out-dir> | wc -l  (non-empty)
                  git checkout <sha> -- <out-dir> ; test -f <out-dir>/dispatch/<y>_P1.parquet
                  test -f <out-dir>/hourly/uc_schedule_<y>.parquet ; test -f <out-dir>/uc_solve_log.json   (A/B and L3 only)
                  bytes in hand ──► archive_session(<shard>)  (rule 33: never before, never while running)
```

A shard that stops with a clear report is a success; one that repairs infrastructure is a failure (rule 32). The budget printed in the prompt is the ladder's measured L3 wall × 1.3, stated in the PRECOMMIT; the 20-minute clause of rule 32 is a stop rule for a shard with no artifact, and E9 checkpointing is what gives a long UC shard an artifact.

## 5. Compose, score, register (zero LP, A/B lane or desk)

```
python3 scripts/probes/_ucmilp_compose_span.py --iso <ISO> --leg 2019=ucmilp_<iso>_2019 ... --out results/calibration/ucmilp_<iso>_span
python3 scripts/calibration_verdict.py results/calibration/ucmilp_<iso>_span
python3 scripts/legitimacy_diagnostics.py results/calibration/ucmilp_<iso>_span     # regenerated over the composite, never copied
```

Read against the PRECOMMIT's fixed readings; write the RESULT with GATESPEC §6.3's table and the §6.1 wall rows. Register the span as a **probe** in the session that produced it (rule 15; the `calibration-report` skill names the command) — never as a keeper. Bundles stay on disk and on their shard branches until the owner rules D-6 (rule 31); the RESULT says where each bundle is and what a promotion would cost. Promotion, when ruled, is the one command of `RUNBOOK` §4, run in the desk's slot, one ISO at a time.

## 6. Decision cards

| Card | Served when | Options (recommendation first) |
|---|---|---|
| D-0 charter | first sitting | charter · charter with changes · decline |
| D-1 amendment | first sitting, after D-0 | sign §7 text · sign with edits · do not sign |
| D-2 wall bars | after L3 on the first target ISO | 1.5× / 3× · other |
| D-3 pricing | before the first A/B PRECOMMIT | restricted + uplift sidecar · amortized variant |
| D-4 rule 20 | before the first A/B is scored | reported under MECH 28 · budgeted |
| D-5 census | per ISO, with its PRECOMMIT | the lane's recommended substitution set · keep a named floor · hold |
| D-6 promotion | per RESULT | promote on structure · `R`/`I` with evidence · hold |

Cards are served as clickable decision cards, never inline text; a ruling is recorded verbatim in plan §8 the same sitting; a ruling is never re-litigated by a lane.

## 7. Mishaps this protocol is built to prevent (each from a recorded incident)

| Mishap | Record | Guard here |
|---|---|---|
| shards cloned a branch that auto-merged and vanished; ten solves discarded | ercot-261 (rule-history §17) | SHA only, 40 chars; prompt committed and `git show`n |
| `git add -A` swept 183 unrelated files onto main | ercot-261 | shard adds only `.gitignore` + its out-dir; `git status --short` proof |
| solves run inside the orchestrating container; 70 min serialized | ercot-264 (§17) | the desk never solves; one shard per ISO-year |
| per-year slim legs could not be composed; a diagnostic PASSED VACUOUSLY | SPP-36 (§19) | full bundles pushed (rule 34); diagnostics regenerated over the composite |
| single-year arm vs span control produced a false finding | SPP-36 (§19) | A/B is span vs span, every registered year |
| a kept leg's fingerprint moved; "kept" legs had to be re-solved | closeout-spp-nuc PRECOMMIT | pin one SHA per span; refuse on fingerprint mismatch in the composer |
| posture start cost double-counted with the amortized markup | explorer read of `zero_posture_markup` (SPP-only) | markup zeroed on every integer cluster, tested |
| a relaxed commitment "cannot decommit by construction" | PJM decommit lane | integer `u`; no-load on `u` |
| a lever swept against a gate | rule 1 (c) | `uc_*` fields declared once in the PRECOMMIT |
| a probe copied one leg's `legitimacy_diagnostics.json`; C8 read SKIPPED | `_miso260_compose_span.py` docstring | composer regenerates |
| OOM: data steps ate the disk the swapfile needed | R-50 | `prepare_solve_container.py` FIRST, in every shard prompt |
| shard PENDING for 30–45 min | NWPP-NEXT-25 handoff | archive and relaunch after 45 min |
| results deleted before the owner ruled | rule 31 | never `rm`; `.gitignore` discharges keep-off-main |
| a deprecated knob zeroed instead of removed | rule 26 | the UC replaces bridges by validation refusal, not by zeroing |

## 8. Stop conditions (the desk stops and asks)

An infeasible window reported by any shard (engine defect); a schedule hash that differs between two runs of one recipe; a control ISO flip; a wall ratio above the ceiling on a target ISO after E1–E7; a lane that needs a file outside its region; any request to arm the stage in a keeper before D-6; any proposal to re-test an `R`/`I`/`G` cell without new evidence (rule 28).

## 9. End-of-sitting checklist

- §11 log line (date, desk session, main HEAD, what was chartered/ruled); §12 rows current; §8 rulings verbatim.
- Every reported shard fetched, verified, archived; every PENDING > 45 min relaunched; leftovers named.
- One desk PR (`claude/ucmilp-desk-r<NN>`), docs only, merged on green CI; branches the owner must delete listed (a session cannot: 403).
- The next sitting's first card named.
