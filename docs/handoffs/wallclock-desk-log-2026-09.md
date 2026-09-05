# Wall-clock desk log — 2026-09

**Desk:** session `claude/wc-desk-coordination-pyy4eo` (this file lives on branch
`claude/wc-desk-log` and is the only thing the desk commits). Implements
`docs/handoffs/wallclock-opportunities-2026-09.md` §5 by issuing worker prompts, tracking
their PRs and phasing them so no two open branches edit the same file. The standing
constraints every prompt carries are `docs/handoffs/perfb-session2-markup-charter-2026-09.md`
§6 plus the desk charter's "Constraints" block. Main at desk open: `d01ab8b0`.

Gate state vocabulary: `issued` (prompt sent, no PR yet) · `pr-open` (PR up, gates being
read by the desk) · `gates-ok` (gate tables present, class stated, diff confined to the
collision-map files) · `needs-revert` (strayed into another item's file) · `measured-negative`
(worker's own gate FAILed; reverted) · `merged` · `closed`.

## 1. Item ledger

| item | lever | prompt issued | model | worker session | branch | PR | gate state | merged sha | measured s/yr |
|---|---|---|---|---|---|---|---|---|---|
| A-1 | vectorize `cod_ramp._load_cod_map` | 2026-09-05 22:32 UTC (wave 1a) | claude-opus-5 | `session_01XqXmNuy2TJAAigPy7bAYWq` | `claude/wc-a1-cod-map-vectorize` | — | issued | — | — |
| A-2 | eGRID parquet mirror (both call sites) | 2026-09-05 22:32 UTC (wave 1b) | claude-opus-5 | `session_01B1av3LGXp9gjSBoqg85iFg` | `claude/wc-a2-egrid-mirror` | — | issued | — | — |
| A-3 | band-sidecar vectorization + sidecars on the clock | 2026-09-05 22:45 UTC (wave 1c, handed to owner) | claude-fable-5-1 | owner-launched | `claude/wc-a3-band-sidecar-clock` | — | issued | — | — |
| A-6 | `malloc_trim` at the cold-P1 seam | 2026-09-05 22:45 UTC (wave 1d, handed to owner) | claude-opus-5 | owner-launched | `claude/wc-a6-malloc-trim-p1-seam` | — | issued | — | — |
| A-5 | held CAMPD normalization (PERF-B change f) | desk action 2026-09-05 (wave 1e) | — | — | `claude/perf-b-apply-nabnpi` | #4579 | **merged 2026-09-02** (see §2.1) | `60a6d539` | PJM/MISO `bench` −64–71 % per PR #4579 |
| B-0 | P1 basis-seed owner memo (+ the missing ERCOT bench) | 2026-09-05 22:45 UTC (wave 1f, handed to owner) | claude-fable-5-1 | owner-launched | `claude/wc-b0-p1-seed-memo` | — | issued | — | n/a (docs) |
| B | P1 basis seed on the cold-rebuild route | wave 2a — blocked on A-3 merged, A-6 merged, B-0 memo SIGNED | claude-fable-5-1 | — | `claude/wc-b-p1-basis-seed` | — | blocked | — | — |
| A-4 | on-disk memo for the remaining year-1 caches | wave 2b — blocked on A-1 merged, A-2 merged | claude-opus-5 | — | `claude/wc-a4-year1-memo` | — | blocked | — | — |
| 3a | re-baseline anchor table on main | wave 3 — after every wave-1/2 PR merged or closed | claude-opus-5 | — | `claude/wc-3a-rebaseline` | — | blocked | — | n/a (docs) |

## 2. Decisions and findings

### 2.1 A-5 (wave 1e) — no director decision needed: the held change is already on main

The assessment doc (§2 A-5, written at main `4d4dc6ce`) says the CAMPD normalization
"is not on main" and that `git branch -r --contains 27b3a92c` is empty. Checked at desk
open: PR #4579 (`claude/perf-b-apply-nabnpi`, head `60a6d539`) was **merged by the owner
on 2026-09-02 04:22 UTC**, and `src/market_sim/data/campd.py` on `origin/main` carries its
`_to_numeric_by_uniques` helper (lines 318/363/387). `27b3a92c` is simply a pre-rebase sha
of the same branch. So the "MERGE HELD on stale goldens" condition the assessment cites was
overtaken by the owner's merge; the MISO golden question is moot for this item. No MISO
golden capture is issued by this desk. Two consequences:

* the assessment doc's A-5 row and its §5 rank 5 are stale; the wave-3 re-baseline prompt
  will note the correction in the baseline doc rather than editing the assessment;
* wave-1 workers' merge-base controls already include change (f), so their `bench`
  sub-phase numbers are post-(f) — no worker should attribute a `bench` delta to itself.

### 2.2 B-0 (wave 1f) — the prompt was widened, because the bench it cites does not exist

`wallclock-opportunities-2026-09.md` §3's "Measurement" table is the unfilled placeholder
`<!-- ERCOT_BENCH_TABLE -->` and there is no §6.3 (only `<!-- ADDENDUM -->`); the commit
that added the doc (`2173d0dc`) is titled "ERCOT bench pending" and the assessment
session's branch is gone from origin. A flip memo without the number cannot be signed, and
wave 2a is gated on the signature, so the desk widened 1f: **DATA PROFILE ercot**, the
worker measures ERCOT__forward 2025 seed OFF vs ON through a scratch monkeypatch driver
(never committed, no repo code), reports the H2-shaped `diff_warmstart_bundles.py` table
plus P1 seconds / iterations, and fills both placeholders in the assessment doc in the same
docs-only PR. Model raised from "any" to Fable because the driver wraps solver internals.

### 2.3 Wave-2 note for the 2a prompt

`tests/test_xyear_warmstart_default.py`, which prompt 2a says to extend, does not exist at
HEAD (no `tests/*xyear*` or `tests/*warm*` file). The 2a prompt will say "create it" rather
than "extend it", covering the existing cross-year switch family as well as the new one.

### 2.4 Desk mechanics

* Worker sessions are separate cloud containers, so the charter's "if the workers share a
  host" stagger for the ERCOT carve-out does not apply; each worker still runs one ERCOT
  solve at a time inside its own session.
* Model assignment (owner ask 2026-09-05): A-1/A-2/A-6/A-4/3a on `claude-opus-5`;
  A-3 (13k-line `run_calibration_full.py` under rule 27 + the frozen phase-line wire
  contract), B-0 (solver-internals monkeypatch) and B (the plan's own "Fable") on
  `claude-fable-5-1`. Never Sonnet, per rule 27.
* **Owner instruction 2026-09-05 22:44 UTC: the desk does NOT launch sessions.** Prompts are
  handed to the owner as copy-paste blocks and the owner launches the workers; the desk
  monitors PRs and `origin/main`. The two sessions the desk launched before that instruction
  (A-1, A-2) are recorded above; the owner decides whether they run or are archived.
* The desk does not approve or merge; the owner merges. Wave-2 blockers are checked with
  `git log origin/main`, never PR state.

## 3. Timeline

| when (UTC) | event |
|---|---|
| 2026-09-05 22:28 | desk opened on main `d01ab8b0`; assessment + charter read |
| 2026-09-05 22:32 | 1a (A-1) and 1b (A-2) issued |
| 2026-09-05 22:35 | 1e resolved: PR #4579 already merged (§2.1) |
| 2026-09-05 22:40 | 1c / 1d / 1f launches held for approval |
| 2026-09-05 22:44 | owner: desk must not launch sessions — prompts handed over as code blocks instead; 1c/1d/1f issued that way; first PR check-in scheduled +60 min |
