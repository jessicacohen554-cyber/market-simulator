# FINDING — Y-13: CI plumbing repairs + rule 29 disposal duty (R-AU, R-AV)

**Lane:** Y-13, Model Audit & Release-Finalization Program. **Date:** 2026-09-05 (dispatched 23:05Z).
**Rulings executed:** R-AU (*"Charter Y-13, flip at next 6-of-6"*) and R-AV (*"Delete before merge"*),
audit-program director sitting 2026-09-05 ~23:00Z.
**Base pin:** `2886235c` (origin/main at lane start, 23:1xZ). The director's pin `5cc1e7ce` is its
ancestor, three merges back (#4852, #4853-era desk-log commits, #4854); every reading below
labelled "at 5cc1e7ce" was re-taken locally at `2886235c` and agreed with the director's.
**Branch / PR:** `claude/y13-ci-plumbing-repairs-c1pn1k`, PR #4864. *(Dispatch-vs-repo difference,
recorded per the standing test: the dispatch named `claude/y13-ci-plumbing-g2-k7m2qa`; the session's
harness assigned `…-repairs-c1pn1k` and forbids pushing elsewhere, so that is the branch.)*
**Model:** Fable (rule 27 `[R-PUSH]` scope: `.github/workflows/`, `CLAUDE.md`, a CI gate script).

## 0. Result in one paragraph

Three of the four reds on the R-AE flip set were plumbing and are repaired here; the fourth (Fast test
tier, the two Y-11 STOP tests) is Y-14's and is untouched. G-2 is written into rule 29 as clause (c)
and executed once: the two unregistered bundle dirs are deleted after confirming their numbers live
in committed records. At the PR head every one of the seven gate scripts, ruff, and the refactor
guards exit 0 locally; `test_golden_manifest_provenance.py` is red on exactly the two Y-14 tests.
**Expected flip set after this PR and Y-14 merge: 6 of 6; after this PR alone: 5 of 6.**

## 1. Gate readings, before → after (local, `uv run --frozen`, `$?` read directly)

| gate | at 5cc1e7ce / 2886235c (before) | at PR head (after) |
|---|---|---|
| `scripts/ci_refactor_guards.py` | **1** — `tests/scoring/test_bench_stamp_ast.py: references missing script 'scripts/fake_builder.py'` (11 known-dangling tolerated) | **0** — `script-refs: OK (12 known-dangling tolerated)` |
| `scripts/audit_keepers.py --check` | **1** — `[✗] status — S1: stale vs the current verdicts: frontend/data/backcast/status/NEISO.js`; 1 warning (repaired concurrently by #4865 on main, §4.1) | **0** — `PASS: 0 failure(s), 1 warning(s)` (the pre-existing NYISO E11 lineage warning: former keeper `2026-09-05-nyiso-189-steam-identity` has no resolvable bundle on disk — not this lane's) |
| `scripts/check_registry_payload_parity.py` | **1** — 2 problems: `miso220_nonsteamlift_screen2025`, `neiso_headctrl_k99` "bundle dir maps to no retained sidecar `bundle` field and is not keep-required" | **0** at `6edbb066` (pre-merge head) — `OK (8 runs checked, 41 bundle dirs swept)`; **1** at `e68af00e` (merged head) on `miso220_nonsteamlift_B` alone, a bundle `main` gained after the pin (§4.1) |
| `scripts/check_gate_a_provenance.py` | 0 (not re-read before; not touched) | **0** — 6 rows checked |
| `scripts/check_mechanism_matrix.py` | 0 (not touched) | **0** — integrity OK, 6 ISO shards |
| `scripts/check_forecast_staleness.py` | 0 (WARN-only) | **0** — solve-affecting Δ 6 commits (threshold 10) |
| `scripts/check_bench_freshness.py` | 0 (not touched) | **0** |
| `scripts/check_golden_manifest.py` | 0 (not touched) | **0** — `golden-manifest: OK` |
| `ruff check .` / `ruff format --check .` | 0 / 0 | **0 / 0** |
| `pytest tests/scoring/test_golden_manifest_provenance.py -q` | 2 failed / 43 passed (Y-11 STOPs) | **2 failed / 43 passed, 14 subtests passed** — `PartitionCaptureKeyTest::test_resolve_capture_targets_reaches_the_carveout_bundle` and `GoldenManifestSchemaTest::test_partition_entries_agree_with_the_keeper_shard[ERCOT__carveout-2023]`. **Exactly the two Y-11 STOP tests; Y-14's; expected.** Nothing else red. |
| `tests/regression/test_file_integrity_guard.py` | 7 passed | **7 passed** (the workflow step is extracted verbatim and replayed under `bash -e`) |

## 2. The three repairs

### 2.1 Structural refactor guards (task 1)

`scripts/fake_builder.py` is the synthetic builder-source path the Y-12 test writes into its
`tmp_path` fixture tree (`tests/scoring/test_bench_stamp_ast.py`, `rel = "scripts/fake_builder.py"`
at the `tree` fixture and again in the absent-file test; commit `3d0fd19d`). `BUILDER_SOURCES` is
monkeypatched to it, so it must look like a `scripts/` path and the `--script-refs` scan necessarily
sees it. One `KNOWN_DANGLING` entry with a reason string naming the test and the commit — the same
class as the six `tests/regression/test_file_integrity_guard.py` fixture paths already allowlisted.
The test is untouched. *(Dispatch-vs-repo: the dispatch listed `ci_refactor_guards.py` among the
≥300-line files; it is 250 → 260 lines. The blob was verified after the push regardless.)*

### 2.2 file-integrity-guard two-dot false positive (task 2)

**Defect, as the v31 coda `8e26a153` measured it:** `BASE_SHA` is `pull_request.base.sha` — the base
branch's TIP at job time — and the step ran a two-dot `git diff <base-tip> <head>`. When `main`
advanced past the fork point between the push and the job (there: `48051605 → 9e8de3dc`, #4842, in
~7 min), every file main gained read as **D**eleted by the PR: two-dot 3 phantom deletions (one of
them the 547-line `scripts/probes/nyiso195_screen_gates.py`, the one that fired), merge-base form 0.
The guard only examines paths ≥300 lines at base, so it false-positives most reliably on the files
it exists to protect.

**Repair:** after the existing availability fallback (kept: `HEAD^` when the base sha is unknown;
an explicit `git fetch --no-tags --filter=blob:none origin <sha>` is tried first when the sha is
absent — `fetch-depth: 0` already brings every `refs/heads/*` commit, so this is belt-and-braces),
compute `git merge-base "$BASE_SHA" "$HEAD_SHA"` once and reassign `BASE_SHA` to it. Both consumers
— the `--name-status -M` diff and the `blob_lines()` base read — take `BASE_SHA`, so they can never
disagree about what "base" means. A merge-base equal to the tip (fast-forward push, or a branch
rebased onto the current tip) leaves it unchanged. No merge-base → warning and the old behaviour.

**Validation (actionlint is NOT installed in this environment; stated per the dispatch):**
YAML parse via PyYAML + `bash -n` on the extracted `run:` body; the regression suite (7 passed, it
extracts the step from the workflow file and replays it under `bash -e`, the shell Actions uses); and
a live replay of the phantom case in this repo with `BASE_SHA=2886235c` (tip) and `HEAD_SHA=5cc1e7ce`
(an older commit, standing in for a PR head whose base moved): the OLD two-dot diff reports
`D docs/handoffs/wallclock-desk-log-2026-09.md` (a phantom), the repaired step prints
*"Base tip … is past the fork point; diffing from merge-base 5cc1e7ce… instead. Scanned 0/0 core
paths. file-integrity-guard passed."* This guard is not one of the six R-AE checks (Y-9 §3).

### 2.3 Rule-22 quarantine gates (task 3)

`audit_keepers --check` S1 read `status/NEISO.js` stale because PRs #4839 and #4852 (branch
`neiso-pjm-validation-touchpoints`) registered `2026-09-05-neiso-2022-touchpoint-k99` and
`2026-09-05-neiso-2020-2021-touchpoints` without a status rebuild; the later steps of the job
(legitimacy_diagnostics, parity, golden manifest) were skipped behind it. `build_status.py --iso
NEISO` rewrote exactly one line of `frontend/data/backcast/status/NEISO.js` (`shared.js` unchanged),
committed alone. No keeper shard, marker or determination touched.

## 3. G-2 — rule 29 `[R-SCREEN]` clause (c) (task 4), and the R-AV execution record (task 5)

**The collision** (board, v31 second coda `da99f34b`): rule 29 says a screen bundle is *"never
registered on the dashboard"*; Class-E retention point 4 (`check_registry_payload_parity.
check_bundle_retention`) says every `results/calibration/<bundle>` dir maps to a retained sidecar or
is keep-required. miso-220 committed its 2025 screen bundle (`7ccdc4fd`, 22:22Z) as rule 29 directed
and turned the always-on parity gate red for every PR — *by obeying it*. The gate's message offered
register / prune / allowlist; rule 29 forbade the first and nothing chose between the other two.

**The ruling and its text.** R-AV: *"Delete before merge."* Written as:
- `CLAUDE.md` rule 29 clause (c): a screen bundle, and any control bundle a screen earns under
  (b)'s LIVE-hunk case, is deleted from `results/calibration/` before its PR merges; the
  PRECOMMIT/FINDING doc carries every number the session will ever cite; the parity sweep is the
  enforcement and an unregistered bundle dir is a gate RED, not an allowlist candidate.
- `docs/governance/rule-history.md` §8.2 (ruling verbatim, the collision, first execution) + a §11
  changelog row.
- `frontend/data/backcast/keepers/README.md` Class-E rule: one cross-reference sentence.
- `scripts/check_registry_payload_parity.py`: the unmapped-bundle problem message names clause (c)
  as the one exit for a screen/control bundle. Message text only; the gate's behaviour is unchanged
  (no test asserts on the message text — checked).

**Execution — numbers confirmed in a committed record BEFORE each `git rm -r`:**

| dir | tracked files | where its numbers live (opened and confirmed) |
|---|---:|---|
| `results/calibration/miso220_nonsteamlift_screen2025` | 8 | G-1 `$39.869 → $42.276` (+6.039 %, band 3–12 %), G-2 `ST_GAS 16.0362 → 18.3038 TWh` (+2.2676), G-3 no flip, verdict "SCREEN CLEARS" — `results/calibration/_miso220_screen_gates.json` (committed, `7ccdc4fd`, whose commit body also carries the table); gate definitions and the screen-year argument in `PREREG-miso220-nonsteam-offer-lift-2026-09-05.md` Addendum A. *(Dispatch-vs-repo: the dispatch said "the miso-220 FINDING/PRECOMMIT docs from PRs #4838/#4840/#4841". There is no `FINDING-miso220` doc; the PRs are the miso-219 branch's and carry the PREREG + the `_`-prefixed gate JSON. The JSON is the committed gate table; that satisfied the stop condition.)* |
| `results/calibration/neiso_headctrl_k99` | 17 | worst-drift table (price −0.008 %, demand/slack/dump/reserve_price bit-identical, total generation ≤ 0.0008 %, worst per-class energy 0.17 %) — `results/calibration/ASSESSMENT-neiso-pjm-validation-touchpoints-2026-09-05.md` §4(i), PR #4852. Confirmed. *(That doc cites the drift audit as "rule-30 G-DRIFT"; CLAUDE.md numbers it rule 29(b). Not this lane's to fix; noted.)* |

Neither dir was allowlisted, registered or archived. Parity: 2 problems before, OK after. One
residual reference remains and is harmless: `scripts/probes/_miso220_screen_gates.py` still names
the deleted screen dir in its `SCREEN` path constant (a record-only scorer; `scripts/probes/` is
excluded from the refactor-guards scan by design).

## 4. Commits on the PR (small, logical, in dispatch order)

1. `70acec77` — guard allowlist entry (`scripts/ci_refactor_guards.py`).
2. `a49cf291` — file-integrity-guard merge-base repair (`.github/workflows/file-integrity-guard.yml`).
3. `0983cf26` — NEISO status rebuild (`frontend/data/backcast/status/NEISO.js`, 1 line).
4. `01565ca7` — G-2 text (CLAUDE.md, rule-history §8.2 + a changelog row, keepers README, parity message).
5. `6edbb066` — R-AV prune of the two dirs (25 tracked files).
6. `e68af00e` — merge of `origin/main` (`9b62c6de`, 27 commits past the pin) into the branch, see §4.1.
7. this finding.

### 4.1 Main moved under the PR — merge, two conflicts, one new red that is NOT this lane's

The PR read `mergeable_state: dirty` before any CI run was created (GitHub cannot build the merge ref
of a conflicted PR, so no `pull_request` run fired). `origin/main` had advanced 27 commits past the
pin. Two conflicts, both resolved by keeping main's work whole:

- `frontend/data/backcast/status/NEISO.js` — PR #4865 (`a5928410`, capx-director standing lane)
  regenerated the same file for the same S1 reason. Rebuilding on main's copy changes only the
  `generated` stamp (content identical with the stamp stripped, sha `45796c1eb90caa3e` both sides),
  so main's copy is kept and this branch's own rebuild (`0983cf26`) is superseded — the S1 repair
  landed twice, once from each lane, and once was enough.
- `docs/governance/rule-history.md` — PR #4855 (miso-220) added §11 (the rules 1/13 authorized
  price-tuning carve-out) and renumbered "Changes to this file" §11 → §12. Both new changelog rows
  kept; §8.2 is unaffected.

**The new red.** The same #4855 merge commit (`74403263`) committed
`results/calibration/miso220_nonsteamlift_B` — the miso-220 **full-span ARM** bundle (2023–2025,
19 files) — with no registry sidecar naming it, so `check_registry_payload_parity` exits 1 on `main`
from `80695cb2` on, and therefore on this PR's merged head too. This is **not** a rule-29 screen or
control bundle, so R-AV does not reach it: it is the arm whose scoring the miso-220 lane said was
still to come ("every prediction and kill is scored only there"), and rule 15 `[R-DASHBOARD]` says
a finished arm — keeper or rejected — REGISTERS. Its numbers exist in no committed doc yet, so under
this dispatch's own stop condition it is left untouched and reported. The exit is the miso-220
lane's registration (or, if the arm is abandoned, its own rule-15 prune with a FINDING carrying the
numbers) — either turns the gate green with no change here.

Rule 27: pushed over `git push`; every ≥300-line file (CLAUDE.md 695 lines, parity script 553,
rule-history 762) plus the four smaller touched files fetched back from `origin/<branch>` and compared
— line count and sha256 identical on all seven.

## 5. Per-job CI reading on the PR head

Head `e68af00e` (the merge commit; the five lane commits + the merge of `9b62c6de`), CI run **2522**
(`33998673249`, created 23:26:20Z) and file-integrity-guard run **3223** (`33998673257`), read job by job
at 23:27–23:3xZ. The reference column is the v32 records lane's run 2520 (`33998448389`, head
`89d2067c`, created 23:21:18Z — the newest run whose merge ref already carried `main` at #4855/#4865).

| job | R-AE? | run 2520 (reference) | **run 2522 (this PR)** | note |
|---|---|---|---|---|
| Ruff lint + format | yes | success | **success** | |
| Pinned default cache key | yes | success | **success** | |
| Cache-key registration guard | yes | success | **success** | |
| Structural refactor guards | yes | **failure** (`fake_builder.py`) | **success** — compileall, import-walk + script-reference lint, facade tests all green | §2.1 repaired it |
| Rule-22 quarantine gates | yes | **failure** | **failure** — `audit_keepers --check` **success** (S1 repaired), `legitimacy_diagnostics --keepers` **success**, `check_registry_payload_parity` **failure** on `results/calibration/miso220_nonsteamlift_B` alone (the message now carries the clause-(c) sentence), `check_golden_manifest` skipped behind it | §4.1 — the one remaining red is `main`'s, not this PR's |
| Fast test tier | yes | in progress at reading | **in progress** at the 23:33Z reading (pytest step started 23:28:08Z; ~6 min on the reference run) — final reading appended in §5.1 below | Y-14's two tests |
| Rule-28 mechanism-matrix guard | no | success | **success** | |
| FR-21 forecast-board staleness (WARN only) | no | success | **success** | |
| FR-22 backcast→forecast parity | no | **failure** | **failure** — `ercot_storage_as_soc_reserve` (ERCOT) and `nyiso_seam_deliverability_envelope` (NYISO) armed in the keeper with no forecast consumer / registry declaration | pre-existing on `main`, identical on the reference run; no file this PR touches is on its path |
| Forecast-invariant artifact audit | no | **failure** | **failure** — 17 forecast sidecars with undeclared invariant FAILs (I3/I7/I9/I12) | pre-existing on `main`, identical on the reference run; forecast namespace, untouched here |
| file-integrity-guard / shrink-guard | no (own workflow) | — | **success** — the repaired step ran on the runner: `BASE_SHA=9b62c6de`, *"Comparing merge-base 9b62c6de… -> e68af00e…"*, *"Scanned 4/4 core paths."* | §2.2; the merge-base equals the tip here because the branch had just merged it — the phantom path is exercised by the local replay in §2.2 |

### 5.1 Fast test tier — final reading

FAST_TIER_FINAL

## 6. Expected flip set after merge

R-AE's six required checks: Ruff lint + format · Pinned default cache key · Structural refactor
guards · Cache-key registration guard · Fast test tier · Rule-22 quarantine gates.

| check | at 5cc1e7ce (director, runs 2512/2513/2514) | expected after this PR |
|---|---|---|
| Ruff lint + format | green | green |
| Pinned default cache key | green | green |
| Cache-key registration guard | green | green |
| Structural refactor guards | **red** (fixture path) | **green** (§2.1) |
| Rule-22 quarantine gates | **red** (S1 stale status; parity would have been the next red) | S1 + the two R-AV dirs **green** (§2.3 + §3); **red on `miso220_nonsteamlift_B`** until miso-220 registers it (§4.1) |
| Fast test tier | **red** — 2 failed / 8098 passed, the Y-11 STOPs | **red until Y-14 merges** |

**Corrected for §4.1:** the Rule-22 quarantine gate stays RED on `main` (and on this PR's merged
head) until the miso-220 lane registers or prunes `miso220_nonsteamlift_B` — that red is
independent of this PR and would be red with or without it. So: **4 of 6 with this PR alone while
`_B` is unregistered; 5 of 6 once miso-220 registers; 6 of 6 at the first head after Y-14 also
lands — that head is R-AU's flip.** Every repair this lane was chartered for is green at the PR
head (§1); the `_B` red was added to `main` at 23:18Z, after the 23:05Z dispatch. Branch protection
is untouched here; the flip is the owner's click.

## 7. Not done, deliberately

Y-14's files (`test_golden_manifest_provenance.py`, `capture_keeper_goldens.py`,
`check_golden_manifest.py`, golden manifests); any keeper shard, marker, freeze file,
`program-status.json`, matrix shard or bench part; any solve/score/registration; any test
xfail/skip/delete; any new workflow; branch protection; the board and plan (the v32 records lane's).
