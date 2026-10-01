# FINDING — audit gate repairs: parity classifier, bench drift arithmetic, gate-(a) guard

**Session:** audit-gate-repairs (2026-09-01). **Lane:** CI infrastructure for the
model audit release program. **Board:**
`docs/handoffs/audit-program-director-board-2026-08.md` RESTART CHECKLIST items
10 and 12, plus finding F-5 (v17). All three owner-ruled 2026-09-01.

**Pin:** taken at `origin/main` `6f6e9d11f9ae88ea4005686efe75f3a39e84ea7b` (merge
of #4486), held stable across two polls. **REBASED mid-session to `e2fa8ab0`**
(merge of #4488) — see §3.4: the separate records lane's gate-(a) repair landed
while this lane was working, and the guard had to be validated against the
repaired file. Every before/after gate reading below was re-taken at `e2fa8ab0`
so both sides share a base.

**ZERO SOLVE.** No LP, no year solved, no run registered, no re-scoring, no
keeper / marker / freeze edit, no mechanism tested, no matrix shard touched. No
new GitHub Actions workflow: the one CI change is a step added to an existing
job.

**Headline.** All three instruments were green for the wrong reason, in three
different ways: the parity gate's green was a maintenance state (a 40-entry
hand-maintained allowlist, not the 26 the board last counted); the bench gate's
drift count was arithmetically wrong and **understated** — the true reading is
**20 of 20 parts with engine drift, not 19**; and the gate-(a) rows were
verifiable against committed artifacts by nothing at all. All three are now
structural. One gate reading changed: bench drift 19 → 20. Nothing else moved.

---

## 1. Job 1 — the parity gate's CLASSIFIER (checklist item 10)

`scripts/check_registry_payload_parity.py`.

### 1.1 What was actually there

The board reported `KEEP_REQUIRED_UNMAPPED_BUNDLES` at **26 named entries**.
Measured at the pin it stood at **40** — the count had grown by 14 since the
board's reading, which is the item-10 thesis (an allowlist growing one to three
entries per A/B session) demonstrating itself inside the board's own figure.

One of the 40, `nyiso147_control`, named a directory that **no longer exists on
the tree at all** (verified against `origin/main`: absent from
`git ls-tree results/calibration/`). That is exactly the "re-armable hole in the
gate" the allowlist's own comment warns about, sitting in the list unnoticed.

### 1.2 The class, derived from the 26/40 entries' own comments

The comments state, per entry, why each legitimately outlives its sidecar. Two
recurring structural reasons, not one:

* **Class R — replay-recipe dir.** *"These hold exactly ONE file, `meta.json`,
  and NO solve output of any kind … `run_replay_bundle` reads only `meta.json`,
  so a one-file dir is a COMPLETE and valid replay input by construction."*
  17 entries. This is the class
  `results/calibration/FINDING-ws6-parity-nyiso-recipe-dirs-2026-08-20.md` §5.1
  recommended (B-8) and which still did not exist.
* **Class P — pre-registered campaign point.** *"Each dir keeps exactly one
  committed file — `ercot235_point_score.json`, the record FINDING-ercot235
  quotes"*; *"Each dir keeps its committed `ercot236_point_score.json` +
  `official_2023.json`."* 14 entries. The heavy bundle contents are gitignored
  by each campaign's own scratch rule (`.gitignore` 586–595), so the marker plus
  its sibling record JSONs are the whole committed artifact.

The remaining 9 entries are FULL bundles carrying real solve output (hourly
parquet, `metrics.json`, diagnostics) — in-flight controls and bit-identical
replication arms. **Their comments justify them case by case, not by class**,
which is why B-8 ranked a structural fix for the recipes and only a *lane-side
duty* for the controls (§5.2), and why this repair does not invent a class for
them.

### 1.3 The classifier, and why it is not a looser rule

`classify_prereg_artifact()` admits a dir only when **both** conjuncts hold:

1. **No solve output.** None of `metrics.json`,
   `calibration_attestation.json`, `legitimacy_diagnostics.json`, and no
   `*.parquet` / `*.npz`, recursively. Point 4's stated target is *"dead solve
   output committed forever with nothing rendering or scoring it"* — a dir
   holding no solve output is not the thing the rule is about.
2. **A committed record names it.** Class R by dir name; class P by its
   point-score marker's **filename**, because a campaign's PRECOMMIT records the
   campaign and its record file, not each of ten grid points. Corpus:
   `results/calibration/*.md` + `docs/**/*.md` (both are needed — the ERCOT
   campaign records live under `docs/`, the NYISO lane's under
   `results/calibration/`). Measured cost 1,824 files / 34.9 MB / **0.14 s**,
   and it is read lazily — only an unmapped dir triggers it.

**Why each conjunct is load-bearing** (each has its own refusal test):

| drop this | what gets admitted | why that is the dead-bundle class |
|---|---|---|
| conjunct (1) | every abandoned control or A/B arm any doc mentions | a real abandoned bundle **always** carries solve output; the citation test alone cannot tell it from a live one |
| conjunct (2) | any stray `meta.json` or point-score file | an abandoned lane's litter would exempt itself — an allowlist with no keeper of the list |
| both, for a naming pattern (`*_recipe`, `*_control`, a campaign prefix) | anything named to look right | naming is not evidence; a batch-prune keyed to `_recipe` is what the 2026-08-20 finding was written to stop |

The citation test uses a delimiter guard (`(?<![\w-])…(?![\w-])`), without which
a pruned `ercot235_r1` would inherit `ercot235_r10`'s citation. Tested.

**NOT a pre-merge check**, deliberately (B-8 §5.3). Nothing is made stricter or
earlier. A pre-registered artifact is legitimately unmapped for hours or days
while its lane is mid-flight; an earlier gate would block correct
pre-registration commits and train lanes to skip pre-registration.

### 1.4 Before / after

| | before | after |
|---|--:|--:|
| `KEEP_REQUIRED_UNMAPPED_BUNDLES` entries | **40** | **8** |
| covered by the class (retired from the list) | — | **31** |
| stale entries removed (dir already gone) | — | **1** (`nyiso147_control`) |
| gate exit code | 0 | 0 |
| gate result | 58 runs / 93 bundle dirs / 0 tolerated | **identical** |

Verified per-entry: all 31 retired entries are admitted **by the class**, and
all 8 residue entries are **not** class-admissible (they are correctly still
kept by name). The residue: `caiso224_a0_control`, `caiso224_b1_fsno`,
`miso170_layup_A`, `miso170_layup_B`, `nyiso150_control`, `nyiso151_armHC`,
`nyiso151_control`, `nyiso152_control` — every one a full bundle with solve
output, i.e. excluded by conjunct (1) by design. Their original justifications
are preserved verbatim in the comments.

Two of the new tests are **live-tree invariants** rather than fixtures, and they
are what stops the list re-growing: `test_live_allowlist_holds_only_uncoverable_residue`
fails if a future entry is one the classifier could have recognised, and
`test_live_allowlist_has_no_entry_for_an_absent_dir` fails on the next
`nyiso147_control`.

---

## 2. Job 2 — the bench gate's drift arithmetic (checklist item 12)

`scripts/check_bench_freshness.py`, SOFT (warning-only) leg. **It stays
ungated** — this repair does not make it fail the build.

### 2.1 The defect, confirmed in source and reproduced

Two independent errors compounding, both on the same comparison:

* **Date KIND mismatch.** `_last_commit` read `--format=%h %ad` — the **author**
  date — and fed it to `git log --since=`, which git applies to the
  **COMMITTER** date. A rebased or cherry-picked engine commit carries an author
  date well before its committer date, which is how one commit tripped the
  signal 38 minutes after it was authored.
* **Day granularity in the runner's local timezone.** `--date=short` truncated
  to `YYYY-MM-DD`, and the caller hand-appended `" 23:59:59"`. The cutoff
  therefore landed at the end of the part's calendar **day in whatever timezone
  the container happened to be in**, not at the moment the part was written.

Reproduced at the pin on a UTC runner. `frontend/data/backcast/bench/NYISO/2025.json.gz`
was committed at `2026-08-30T14:53:31-07:00` = `21:53:31Z`; the old cutoff
resolved to `2026-08-30T23:59:59Z`, **2 h 06 m later than the part itself**, so
every engine commit in that window was silently discarded — 5 counted where 8
had landed.

That direction is not fixed: it is undercount here only because the runner is
east of the commits' offset. A container at UTC+13 resolves the same string to
`2026-08-30T10:59:59Z`, *before* the part, and **over**counts. That is the
mechanism behind the 6 → 0 → 20 swing on the record with the bench bytes never
touched.

### 2.2 The fix

Both sides now use the **committer** instant in offset-bearing ISO-8601
(`%cI`, e.g. `2026-08-30T14:53:31-07:00`), so the comparison is between two
absolute points in time and does not consult the runner's clock at all.
Report lines render the instant in UTC (`_as_utc`) so two parts written a
minute apart do not read hours apart.

Verified 2026-09-01 that `--since` is **inclusive** (a commit passed its own
`%cI` matches itself), so the pre-existing `exclude_sha` guard is load-bearing
rather than belt-and-braces — a bench commit that also touched an engine path
would otherwise count itself as its own drift. Documented and tested.

Also corrected in the same line: the warning rendered `ENGINE_PATHS` with
`'/'.join(...)`, printing `src/market_sim/data//src/market_sim/config/` — one
malformed path rather than two paths. Now `', '.join(...)`.

### 2.3 Was "19 of 20 with engine drift" real, inflated, or understated?

**UNDERSTATED**, on both axes, measured over all 20 parts at the same base:

| | before | after |
|---|--:|--:|
| parts reading engine drift | **19 / 20** | **20 / 20** |
| sum of per-part drift counts | **95** | **156** |
| per-part count (19 of the parts) | 5 | **8** |
| `MISO/2023` | **0** | **4** |

`MISO/2023` read zero drift for exactly the reason item 12 predicted — its bench
commit (`2026-08-31T00:33:15Z`) shared calendar day 2026-08-31 with the engine
commits, so `--since=2026-08-31 23:59:59` excluded all of them. It was the one
part propping up the "19 of 20" reading, and the true figure is 20 of 20.

The board's reading-discipline warning ("do not cite '0 engine drift' as
evidence a bench is fresh") was therefore correct and, if anything,
under-stated: **at this pin no bench part is free of engine drift.** The gate's
exit code is unaffected (0 STALE either way, and the leg never gated).

---

## 3. Job 3 — the gate-(a) staleness guard (board finding F-5)

New: `scripts/check_gate_a_provenance.py`. Wired into `.github/workflows/ci.yml`
in the **existing** `forecast-*` job beside `check_forecast_staleness`; no new
workflow file.

### 3.1 Why a separate script, not a leg of `check_forecast_staleness.py`

The gate-(a) block deliberately avoids the `forecast-provenance/v1` field names
— it says so itself, in `gate_a_provenance.note` — so that a keeper/marker
**DERIVATION** stamp can never be read by the staleness checker as evidence of a
forecast **RE-SCORE**. That is a correct design choice and this repair does not
weaken it.

The comparison needs the **backcast** side: `keepers/<ISO>.json` and
`calibration-complete.json`. Teaching `check_forecast_staleness.py` to open
those would put the backcast instruments inside the forecast-provenance reader
and re-create by the back door the conflation the field-name separation exists
to prevent. A separate script makes the split structural rather than
conventional: **staleness reads provenance stamps and nothing else; this reads
the gate-(a) row, the keeper shards and the marker file, and touches no
provenance stamp.** Neither imports the other.

### 3.2 What it checks — identity and marker state only

1. **Keeper identity** — the run id the row cites must be the ISO's current
   designated keeper. The citation is anchored on the **first** `keeper <run-id>`
   in the detail: every repaired row carries its predecessor's id later in the
   prose (`RE-KEYED here from <old-id>`), which is history, not the citation.
2. **Marker state** — the row's `marker complete=<bool> final=<bool>` claim must
   match membership in `calibration-complete.json`'s two blocks. (`final` holds
   only `_note`; `_`-prefixed keys are notes, not ISOs.)
3. **Status vs marker, one direction only** — a row reading `pass` for an ISO
   **absent** from `complete` asserts a marker the ISO does not hold, since
   charter §2.1b(2)(a) makes a `complete` entry a NECESSARY condition. The
   converse is deliberately **not** checked: `complete` is necessary but not
   sufficient (a full-span keeper is also required), so a `fail` on a `complete`
   ISO is the records lane's derivation, not this guard's.

**FAIL-CLOSED.** A row whose keeper citation or marker claim will not parse is
FAILED, not skipped — an unverifiable row is not a verified row, and silently
passing one is how F-5 stayed invisible. The expected phrasings are named in the
failure message so a records lane rewriting the prose knows the contract.

### 3.3 The boundary: it reads NO determination

Determinations come from `build_status.py`'s partition-aware rollup. A guard
that re-derived one would stand up a second, competing instrument for the
program's most contested reading, so this one never reads, re-derives or asserts
a determination. The rows themselves say why that is right: the determination is
*"concurring evidence, not the gate test."*

**ERCOT is the live case that makes the boundary concrete.** Its ISO-level
determination is the ercot-246 two-config partition rollup **CALIBRATED** while
its registered run-level determination is **NOT-YET**. Both are real; neither is
"the" determination. The guard is correct there **by construction rather than by
picking a side** — it reads neither value. Pinned by two tests: one feeds the
same row three different determination claims (including a self-contradictory
"CALIBRATED and NOT-YET") and asserts silence every time; the other is ERCOT's
two-value text specifically.

### 3.4 Coordination with the records lane — and the guard validated in BOTH directions

The separate records lane (`claude/audit-gate-a-repair-12ewmv`) was repairing
the four stale rows in the same window. It **landed as #4488** while this lane
was mid-flight, so this branch was rebased from `6f6e9d11` onto `e2fa8ab0` and
the guard re-run. That gives the strongest possible validation — the guard was
measured against the real defect and against the real repair:

**Against the pre-repair file (`6f6e9d11`) — exit 1, five problems, exactly F-5:**

```
CAISO: cites SUPERSEDED keeper '2026-08-17-caiso-200-h1-memberpanel'
       (current: '2026-08-26-caiso-220-c1-crosswalk')
ERCOT: cites SUPERSEDED keeper '2026-08-24-231-tie-zone-measured'
       (current: '2026-08-25-234-eastex-identity')
ERCOT: claims marker complete=False final=False, but
       calibration-complete.json has complete=True final=False   <- the verdict flip
MISO:  cites SUPERSEDED keeper '2026-08-22-miso-177-rho-measured'
       (current: '2026-08-30-miso-191-bexit')
NYISO: cites SUPERSEDED keeper '2026-08-30-nyiso-157-par-attribution'
       (current: '2026-08-30-nyiso-159-loss-surface')
```

Four stale identities and the one verdict-flipping marker claim — F-5's count
and F-5's ERCOT case, independently reproduced by an instrument that did not
exist when F-5 was written.

**Against the repaired file (`e2fa8ab0`) — exit 0**, all six rows clean; ERCOT
now reads `pass` on `2026-08-25-234-eastex-identity` with
`marker complete=True final=False`.

Nothing was tuned to make either reading come out. The guard is a hard gate
(unlike the WARN-level staleness step beside it) because a row citing a keeper
that is not the ISO's designated one is a false statement about committed
artifacts, not a freshness lag, and it is cheap and unambiguous to fix.

---

## 4. Verification — all gates, before and after, at the same base

Exit codes captured directly (unpiped), both sets at `e2fa8ab0`, the AFTER set
with this lane's changes applied:

| gate | before | after | changed? |
|---|---|---|---|
| `audit_keepers.py` | **0** — PASS 0 failures / 0 warnings | **0** — PASS 0 / 0 | no |
| `check_registry_payload_parity.py` | **0** — 58 runs / 93 dirs / 0 tolerated | **0** — 58 / 93 / 0 | no (allowlist 40 → 8) |
| `check_mechanism_matrix.py` | **0** — integrity OK, 6 ISO shards | **0** — identical | no |
| `check_forecast_staleness.py` | **0** — Δ unknown; 31 of 52 undated | **0** — identical | no |
| `check_bench_freshness.py` | **0** — 20 parts, 0 STALE, **19** with drift | **0** — 20 parts, 0 STALE, **20** with drift | **YES** |
| `check_gate_a_provenance.py` *(new)* | n/a | **0** — 6 rows checked | new |

**The one state change, explained:** bench engine drift 19 → 20 is the item-12
correction itself (§2.3). It is a WARN-level count on an ungated leg; the gate's
exit code and its STALE count are unchanged, and no bench part was regenerated,
no C1 verdict re-scored, no bench byte touched.

`check_bench_freshness.py` is **not wired into CI at all** (verified: no
reference in `.github/workflows/`). It is a session-run instrument. This repair
does not wire it in — that would add billed runner minutes for a warning-only
leg, against the repo's CI cost policy — but it is worth the board knowing that
its bench readings come only from whoever runs it by hand.

### Tests

Per `docs/testing.md`, hermetic, no network, no writes into the checkout:

* `tests/scoring/test_registry_payload_parity.py` — **+11** (21 total, all pass).
  Both classes admitted; both conjuncts refused independently; the delimiter
  guard; the empty-dir case; the `docs/` corpus root; and the two live-tree
  invariants that stop the allowlist re-growing.
* `tests/scoring/test_bench_freshness_drift.py` — **new, 8 tests.** Builds a
  throwaway git repo with author and committer dates explicitly separated.
  Pins committer-not-author, the same-day case (the exact `MISO/2023` failure),
  the not-yet-drifted case, the `exclude_sha` inclusivity guard, and
  timezone-independence across UTC / America/Los_Angeles / Pacific/Auckland.
* `tests/scoring/test_gate_a_provenance.py` — **new, 13 tests.** Both F-5 halves,
  both fail-closed paths, the `RE-KEYED from` anchoring, the necessary-condition
  direction and its converse, the no-determination boundary, ERCOT's two-value
  case, and a live-tree test that the committed board passes.

`ruff check` and `ruff format --check` clean on all six files.

### Two PRE-EXISTING test failures in `tests/scoring/`, not this lane's

The full `tests/scoring/` fast lane reads **1147 passed, 2 failed** with this
lane's changes applied. Both failures reproduce **on a clean tree at
`e2fa8ab0`** with every change of this lane stashed, so neither is caused here.
Reported rather than fixed: both are other lanes' state, and editing them would
collide with the records and capx lanes working the same window.

* `test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` —
  `AssertionError: NYISO / assert 'withdrawn' == 'complete'`. The test asserts
  every listed ISO reads `complete`; NYISO was **withdrawn** from the block. A
  stale test expectation, and the test's own comment says this exact class of
  drift has happened before. **Records lane's.**
* `test_forecast_parity.py::test_all_six_keepers_resolve` — ERCOT:
  `ercot_adaptive_event_release`, `ercot_storage_adaptive_expectation` armed in
  the keeper with no forecast-orchestrator consumer and no declaration in
  `scripts/lib/forecast_parity_registry.py` (FR-22). **A real parity gap in the
  ERCOT keeper's posture**, not a test bug — for the ERCOT/capx lane.

---

## 5. For the records lane

Two lines per job, for the board (this lane does **not** edit the board or the
plan):

* **Item 10 — parity classifier: DONE.** `KEEP_REQUIRED_UNMAPPED_BUNDLES` **40
  → 8** (the board's "26" was itself 14 stale); 31 entries retired to a
  two-conjunct structural class (no solve output **and** named by a committed
  record), 1 stale entry removed whose dir was already gone. Gate exit 0 with
  the identical substantive result (58 runs / 93 dirs); two live-tree tests now
  fail if the list starts re-growing. **The gate's green is a property now, not
  a maintenance state.**
* **Item 12 — bench drift arithmetic: DONE, and the board's reading was
  UNDERSTATED.** The author-date vs committer-date mismatch plus day granularity
  in the runner's timezone is fixed (offset-bearing committer instants on both
  sides). The true reading at this base is **20 of 20 parts with engine drift,
  not 19** — `MISO/2023` read 0 only because its bench commit shared a calendar
  day with the engine commits — and per-part counts were 5 where 8 had landed
  (sum 95 → 156). Leg stays ungated; exit code unchanged.
* **F-5 — gate-(a) guard: DONE and validated in both directions.** New hard gate
  `scripts/check_gate_a_provenance.py`, wired into the existing CI job (no new
  workflow). It **failed loudly on the pre-repair file with exactly F-5's five
  problems** (four stale identities + ERCOT's verdict-flipping
  `complete=False`), and **passes on your repair at `e2fa8ab0`**. It compares
  identity and marker state only and reads **no determination** — ERCOT's
  ISO-level CALIBRATED / run-level NOT-YET split is handled by reading neither.
  Note the parse contract: a row must carry `keeper <run-id>` as its first
  keeper reference and `marker complete=<bool> final=<bool>`, or it fails
  closed.

Two **pre-existing** `tests/scoring/` failures found in passing and reproduced
on a clean tree at `e2fa8ab0` (§4): a stale `complete`-marker expectation naming
NYISO (`'withdrawn' == 'complete'` — records lane), and an FR-22 forecast-parity
gap where `ercot_adaptive_event_release` / `ercot_storage_adaptive_expectation`
are armed in the ERCOT keeper with no forecast-orchestrator consumer and no
registry declaration (ERCOT/capx lane — a real gap, not a test bug). Neither is
this lane's and neither was touched.

**Finding path:** `docs/FINDING-audit-gate-repairs-2026-09.md`.
