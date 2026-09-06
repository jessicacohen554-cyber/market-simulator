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
| A-1 | vectorize `cod_ramp._load_cod_map` | 2026-09-05 22:32 UTC (wave 1a) | claude-opus-5 | `session_01XqXmNuy2TJAAigPy7bAYWq` | `claude/wc-a1-cod-map-vectorize` (deleted after merge) | #4875 (code) + #4926 (evidence, retro) | **merged, complete** — evidence landed 2026-09-06 01:0x UTC via #4926 (`9d113767`, commit `bc3373f4`): §WALLCLOCK A-1 in the baseline doc, CHANGELOG, `wc-a1-{before,after}` manifests; `vec == ref` True on all 8 EIA-860 vintage dirs; NEISO 3-yr byte gate check [1] PASS (9 files, 32 cols, atol=rtol=0), check [4] pre-existing by control; class BYTE-IDENTICAL | `fc05c5c3` (commit `be598ead`) | `_load_cod_map` 16.20 → 0.07 s canonical vintage (231×), 91.60 → 0.38 s across all eight; NEISO year-1 `data_prep` 72.9 → 35.9 s (−37 s, −51 %), warm years −1 s |
| A-2 | eGRID parquet mirror (both call sites) | 2026-09-05 22:32 UTC (wave 1b) | claude-opus-5 | `session_01B1av3LGXp9gjSBoqg85iFg` | `claude/wc-a2-egrid-mirror` | #4876 | **merged** 2026-09-06 00:08 UTC (CHANGELOG conflict resolved by merge); gates present (three `frame.equals` True on the real workbook, 8 fast-tier tests, NEISO byte gate check [1] PASS, check [4] pre-existing by control); class BYTE-IDENTICAL; diff confined to the collision map; baseline row + CHANGELOG on main | `eb8ae4db` (commit `ddc907e1`) | three `read_excel` calls 27.80 → 0.219 s; NEISO year-1 `data_prep` **36.7 → 10.8 s (−25.9 s, −71 %) at post-A-1 base** (re-measured 2026-09-06; at the pre-A-1 base it read 71.3 → 46.1 s — the two wins do not add, A-1+A-2 together take y1 `data_prep` 71.3 → 10.8 s); once per process |
| A-3 | band-sidecar vectorization + sidecars on the clock | 2026-09-05 22:45 UTC (wave 1c, handed to owner) | claude-fable-5-1 | owner-launched (`session_016yZoyAbBuop3K2kd8Bbfxo`) | `claude/wc-a3-band-sidecar-clock-hfflwe` | #4858 (code) + #4874 (evidence) | code **merged** via #4858; evidence PR #4874 **merged** 2026-09-06 00:14 UTC (`a85076d7`, CHANGELOG conflict resolved by merge); gates present (unit test 14/14, NEISO 3-yr byte gate check [1] PASS, 21 sidecars + dispatch frames sha-identical, check [4] pre-existing by control); class BYTE-IDENTICAL; `timing.py` untouched | `2b9e4219` (commit `4d5a59b2`) | band Categorical 15.63 → 0.16 s; writer 16.8 → 4.6 s on the NEISO 2023 frame; phase line now shows `sidecars` 8.0/5.9/7.2 s (2023/24/25) |
| A-6 | `malloc_trim` at the cold-P1 seam | 2026-09-05 22:45 UTC (wave 1d, handed to owner) | claude-opus-5 | owner-launched | `claude/wc-a6-malloc-trim-p1-seam` | #4893 | code **merged** 2026-09-06 00:03 UTC (`src/market_sim/pipeline/solve.py` +12, NEW `src/market_sim/utils/heap.py::malloc_trim`; PR title says "merge-base control golden manifest" — it carried the BEFORE arm's manifest with the code). **Evidence OUTSTANDING**: no AFTER arm, no VmHWM before/after, no byte-gate reading, no baseline row, no CHANGELOG entry on main; PR body empty. Worker presumably still running (§2.8) | `b2bd9fdb` (commit `c2cb9a78`) | not yet measured |
| A-5 | held CAMPD normalization (PERF-B change f) | desk action 2026-09-05 (wave 1e) | — | — | `claude/perf-b-apply-nabnpi` | #4579 | **merged 2026-09-02** (see §2.1) | `60a6d539` | PJM/MISO `bench` −64–71 % per PR #4579 |
| B-0 | P1 basis-seed owner memo (+ the missing ERCOT bench) | 2026-09-05 22:45 UTC (wave 1f, handed to owner) | claude-fable-5-1 | owner-launched | `claude/wc-b0-p1-seed-memo-9euk97` | #4862 (draft) + #4880 (bench) | **merged**, memo on main with the ERCOT forward-2025 OFF/ON bench and the §3/§6.3 placeholders filled; **UNSIGNED** — the Owner decision block (memo L366–377) has no box ticked and no signature (§2.6) | `8209201c` (commit `2d0900d0`) | bench: seed ON `solve_p1` 287.1 → 139.3 s, P1 iters 273,893 → 78,856, objective identical, total gen Δ 0 MWh, max Δ price 1.1e-12, 0 dual-degenerate hours, 16 unit-hours marginal-tie reshuffle; year total 717.4 → 581.5 s |
| B | P1 basis seed on the cold-rebuild route | wave 2a — A-3 merged ✓, A-6 merged ✓ (code), B-0 memo SIGNED ✗ | claude-fable-5-1 | — | `claude/wc-b-p1-basis-seed` | — | **blocked on the owner signature only**; prompt handed to owner 2026-09-06 00:20 UTC with a worker-side "stop if unsigned" check | — | — |
| A-4 | on-disk memo for the remaining year-1 caches | 2026-09-06 00:20 UTC (wave 2b, handed to owner; A-1 ✓ A-2 ✓) | claude-opus-5 | owner-launched | `claude/wc-a4-year1-memo` | — | issued | — | — |
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

### 2.3 Wave-2 note for the 2a prompt — CORRECTED

The desk first recorded here that `tests/test_xyear_warmstart_default.py` does not exist at
HEAD. That was a root-path lookup error: the file is
`tests/unit/pipeline/test_xyear_warmstart_default.py` (10 tests), as the B-0 memo's §8
checklist points out. Prompt 2a extends that file, as the charter says.

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

### 2.5 A-1 landed without its docs

PR #4875 merged with `cod_ramp.py` + `tests/unit/data/test_cod_ramp.py` only; the charter's
dated baseline-doc row and CHANGELOG entry are not on main and no `wc-a1` branch survives
on origin. The PR body is empty, so the NEISO phase line and the merge-base byte-gate
reading exist only in the worker's transcript. Owed: a docs-only follow-up PR carrying the
row (with the before/after `data_prep`), the CHANGELOG entry and the byte-gate reading.

### 2.6 Wave-1 collision found: CHANGELOG.md

Both evidence PRs (#4876 A-2, #4874 A-3) are `dirty` against main on `CHANGELOG.md` —
every wave-1 item appends to the same file, and main moved ~30 merges in the hour. The
collision map listed source files only; CHANGELOG was the one shared file. Fix per PR:
merge `origin/main` into the branch, keep BOTH entries, push. No rebase (charter: never
rewrite history on a pushed branch). Wave-2 prompts will say so up front.

### 2.7 B-0 memo is on main and neutral; the signature is the only open blocker for 2a

Measured on ERCOT forward config 2025 (the C-1a two-run year), determinism pin, OFF vs ON:
`solve_p0` 327.8 vs 335.4 s (same 273,083 iters, same objective); `solve_p1` **287.1 →
139.3 s**, iters **273,893 → 78,856**, P1 objective identical to 16 digits, total
generation Δ 0 MWh, served load / slack / dump / `reserve_price` bit-identical, max zonal
price Δ 1.1e-12 $/MWh, 0 dual-degenerate hours of 61,320, 16 unit-hours of marginal-tie
reshuffle across 11 of 2,335 units; basis export 16.9 s + apply 3.0 s; year `total`
717.4 → 581.5 s; maxrss 12.46 → 13.07 GB. That is the neutrality class
`docs/cross-year-warmstart.md` defines. The memo's §7 offers (A) FLIP / (B) DO NOT FLIP;
the owner ticks one and signs at memo L371–377. The desk issues 2a only after that AND
A-6 is on main.

### 2.8 A-6 merged ahead of its evidence

The owner merged #4893 at 00:03 UTC; it carried the `malloc_trim` call, the new
`utils/heap.py` helper and the merge-base control manifest (`results/regression-goldens/
wc-a6-before`), i.e. the BEFORE arm only. The item's result — VmHWM at the second model's
"after addRows" and the process peak, before vs after, and the byte gate on the AFTER arm —
is not on main. The change is byte-identical by construction (a trim of already-freed heap),
so the merge carries no correctness risk; the number is still owed. Expected as a docs +
manifest follow-up PR from the same worker; the desk records A-6 `measured s/yr` as pending
until then.

### 2.9 Y-14 (R-AW) retired the `ERCOT__carveout-2023` capture key — wave-2/3 gates re-targeted

Commit `18dadeb1` (merged 2026-09-05 23:2x UTC, `docs/FINDING-y14-ercot-golden-forward-2026-09-05.md`):
the ERCOT stage-0 golden now captures the FORWARD config on {2024, 2025}; `ERCOT__forward`
and bare `ERCOT` resolve identically, and `ERCOT__carveout-2023` is in
`check_golden_manifest.RETIRED_CAPTURE_KEYS` and refused. The charter's 1d/2a/2b prompts
named the carve-out key; from wave 2 on the ERCOT byte instrument is
`--iso ERCOT` (forward, 2024 + 2025, ~2 × 12.5 GB-peak years) or one of its years. The
2a and 2b prompts handed today say so.

### 2.10 Desk-log branch

The owner merged the desk log itself into main (#4886, `8ec83789`); the branch fast-forwards
onto `origin/main` at each sweep and keeps its name.

## 3. Timeline

| when (UTC) | event |
|---|---|
| 2026-09-05 22:28 | desk opened on main `d01ab8b0`; assessment + charter read |
| 2026-09-05 22:32 | 1a (A-1) and 1b (A-2) issued |
| 2026-09-05 22:35 | 1e resolved: PR #4579 already merged (§2.1) |
| 2026-09-05 22:40 | 1c / 1d / 1f launches held for approval |
| 2026-09-05 22:44 | owner: desk must not launch sessions — prompts handed over as code blocks instead; 1c/1d/1f issued that way; first PR check-in scheduled +60 min |
| 2026-09-06 00:05 | sweep #1: A-1 merged (#4875, docs owed); A-3 code merged (#4858), evidence #4874 conflicted; A-2 #4876 open + conflicted; B-0 merged (#4880) unsigned; A-6 not started. Follow-up prompts handed to owner |
| 2026-09-06 00:20 | sweep #2 (owner: "A-2 and A-3 landed"): A-2 #4876 merged, A-3 evidence #4874 merged, A-6 #4893 merged code-only (evidence owed), memo still unsigned. 2b (A-4) handed to owner; 2a (B) handed with a stop-if-unsigned guard |
| 2026-09-06 01:00 | sweep #3 (owner "refresh"): no change on the wallclock lane — no `wc-*` branch or PR opened since sweep #2; A-6 evidence still owed (worker running per owner); A-1 docs follow-up not yet launched; A-4 (2b) not yet launched; memo still unsigned. Main at `3dcf1b22` (~45 unrelated merges). Desk log was merged to main again at `144eabe3` (#4904) |
| 2026-09-06 01:10 | sweep #4 (owner: "A-1 landed"): A-1 evidence #4926 merged — A-1 is complete. Still owed: A-6 evidence (session running), A-4 launch, memo signature. Prompts re-sent to owner. Main `9d113767` |
| 2026-09-06 01:20 | sweep #5 (owner "refresh"): no change — no `wc-*` branch or PR; A-6 evidence still owed; A-4 (2b) and B (2a) not launched; memo unsigned. Main `4777935e`. Note for the B worker's merge-base control: capx D62 (`9028992c`) touched a solve-path file since A-6 — the merge-base capture absorbs it, no desk action |
| 2026-09-06 ~01:40 | sweep #6 (owner "refresh"): no change — zero open PRs, no `wc-*` branch; A-6 evidence still owed; A-4 (2b) and B (2a) not launched; memo unsigned. Main `ad45b0e4` |
