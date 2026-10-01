# FINDING — the bench builder fingerprint is too coarse an instrument

**Session:** Y-10 (audit-program director dispatch, 2026-09-05). **Status: PROPOSAL ONLY.**
Nothing in `scripts/lib/bench_stamp.py` is changed by this session. Narrowing what the
fingerprint covers changes what the word "stale" *means* on a gate that guards C1
reproducibility for all six ISOs, and that is an owner ruling.

**Scope note.** This finding argues about the *instrument*. It does not argue that the
nyiso-148 defect the stamp closes is unreal — it is real, it cost a keeper-wide verdict flip,
and nothing here proposes weakening the guarantee. The claim is narrower: the stamp currently
fires on a strictly larger set of edits than the guarantee needs, and the excess is now
measurably expensive.

---

## 1. The observation: three fingerprint moves in one day, zero payload changes

`scripts/lib/bench_stamp.BUILDER_SOURCES` hashes the **raw bytes** of four whole files.
Any edit to any byte of any of them moves the fingerprint, which marks **all 20** committed
parts under `frontend/data/backcast/bench/` STALE and exits `check_bench_freshness.py` 1.

On 2026-09-05 that happened three times:

| commit | time | what it was | did any hunk reach a bench payload? |
|---|---|---|---|
| `ce2353bb` | — | merge #4714 (nyiso-188) | no — parts re-rendered through a genuine solve-backed build |
| `dee6472c` | 18:49Z | nyiso-192 pre-registration + CHP add-back repair | **no** — adjudicated by Y-8 at `a725bfc3`: both hunks land after `bench[int(year)]` is finalised, and the new operands are `None` for every non-NYISO ISO |
| `677b605a` | 20:52Z | the delete-not-archive cleanup | **no** — the single hunk is *inside a `#` comment* |

Each move cost a dedicated lane to adjudicate and re-stamp: Y-8 for `dee6472c` (14 parts),
Y-10 — this session — for `677b605a` (20 parts). **Neither found a moved payload. Every
re-stamp to date has been a relabelling.**

`677b605a` is the sharpest case. Its whole delta to the hashed surface is one comment line
rewording a reference to a script the cleanup deleted:

```
-    # retrofit in scripts/archive/retrofit_lw_price_bench.py, so re-renders are
+    # retrofit in retrofit_lw_price_bench.py (retired script, deleted 2026-09-05), so re-renders are
```

Measured this session: `ast.parse(...)` dumps of `render_calibration_html.py` at `677b605a^`
and at `677b605a` are **identical** (`sha256 090489d15135bfe3` both sides), as is the
`tokenize` stream excluding `COMMENT`/`NL`. No executable line in the file changed. A full
lane was spent to re-label 20 artifacts because a comment was reworded.

---

## 2. Why the byte-hash over-fires: 53 % of the hashed surface is prose

Measured at `49647dd6`, over the four `BUILDER_SOURCES`:

| source | bytes | comment + docstring bytes | prose share |
|---|---:|---:|---:|
| `scripts/render_calibration_html.py` | 132,700 | 69,490 | 52.4 % |
| `scripts/render_backcast.py` | 9,534 | 4,642 | 48.7 % |
| `scripts/lib/backcast_artifacts.py` | 12,461 | 6,979 | 56.0 % |
| `scripts/lib/bench_stamp.py` | 4,019 | 3,052 | 75.9 % |
| **TOTAL** | **158,714** | **84,163** | **53.0 %** |

**More than half the hashed surface cannot change a bench payload under any circumstances.**
This repo's house style is heavily documented — every rule cited in a comment, every parameter
carrying its provenance — so prose edits to these files are *routine*, not exceptional. The
instrument is at its most sensitive exactly where the codebase is most active.

A second, independent over-fire: `backcast_artifacts.py` is hashed whole, but only
`write_bench_part` and `load_bench_part` — **33 of its 299 lines (11 %)** — touch a bench
part at all. The other 89 % is `manifest.js` / registry-sidecar I/O whose output the deploy
rebuilds from `part["bench"]` and which provably cannot move a part.

---

## 3. Two proposals, and an honest measurement of what each buys

### Proposal A (recommended): hash the SEMANTICS, not the bytes

Replace `h.update(data)` with `h.update(ast.dump(ast.parse(data)).encode())`, falling back to
raw bytes on `SyntaxError`. Everything else — the path/length prefixes, the 12-char digest,
the content-derived determinism that keeps parts conflict-free — is untouched.

**Counterfactual over today's three moves, computed rather than argued:**

| commit | byte-hash (today) | AST-hash (proposed) | outcome under A |
|---|---|---|---|
| `ce2353bb` | `dbea7bf45111` | `3fabde12b672` | MOVED — correctly, semantic change |
| `dee6472c` | `4e78c85427bb` | `96e5860ce4ec` | MOVED — correctly, semantic change |
| `677b605a` | `b2f21b9a00d3` | `96e5860ce4ec` | **UNCHANGED — no re-stamp, no lane** |

Proposal A would have made today's third move a no-op and saved this session entirely, while
leaving both genuinely semantic moves firing. It costs one function body, needs no refactor,
and **cannot weaken the guarantee**: two files with identical ASTs compile to identical
behaviour, so a part written under either is byte-identical by construction.

Its honest limit: it does not help with `dee6472c`, which was a real code change that
nonetheless could not reach a payload. That case needs Proposal B — or nothing, since a
semantic change to the builder is precisely what the stamp is *for*.

### Proposal B: narrow `BUILDER_SOURCES` to the bench-feeding paths

The director's dispatch proposed naming the bench-feeding functions. Measured, this is
**worth doing for two of the four sources and not currently possible for the third**:

- `scripts/lib/backcast_artifacts.py` → hash `write_bench_part` + `load_bench_part` only.
  Drops 89 % of that file's surface. Clean, immediate.
- `scripts/lib/bench_stamp.py` → **arguably should not be hashed at all.** It contains no
  payload logic; it computes the hash. It is 76 % prose, and editing this very finding's
  companion docstring would mark 20 parts stale. Self-inclusion buys tamper-evidence, which
  the git history already provides.
- `scripts/render_calibration_html.py` → **narrowing buys little as the code stands.** The
  bench assembly lives inside `build_payload()`, a single **1,216-line** function
  (`:1272-2487`) that builds the bench payload *and* the run's model payload in one scope.
  Its transitive local-call closure is **36 of the file's 38 top-level functions and 2,132 of
  2,534 lines** — only `_coal_group` and `main` fall outside. Function-level granularity
  therefore excludes ~16 % of the file, not the ~50 % one might hope for.
  **Getting real narrowing here requires first splitting the bench assembly out of
  `build_payload` into its own function or module** — a genuine refactor of the most
  determination-critical renderer in the repo, and not something to do in passing.
- `scripts/render_backcast.py` → its `_write_bench_part` is a thin wrapper; same shape as
  `backcast_artifacts`, narrowable.

**Recommended sequencing.** Proposal A alone, first: it is a few lines, it is provably
guarantee-preserving, and it removes the single largest source of false staleness (53 % of
the surface). Proposal B's cheap legs (`backcast_artifacts`, `bench_stamp` self-inclusion)
can follow. The `render_calibration_html` refactor should be judged on its own merits as a
readability change — a 1,216-line function that mixes two payloads is worth splitting
regardless of the fingerprint — with the stamp narrowing as a side benefit.

---

## 4. What this does NOT propose

- **Not** weakening `check_bench_freshness.py`'s HARD tier, or making a mismatched
  fingerprint anything other than a gate failure.
- **Not** touching the SOFT engine-drift tier.
- **Not** the distinct "absent vs mismatched" split the 2026-08-30 adjudication offered as
  its cheaper alternative (`docs/FINDING-bench-fingerprint-adjudication-2026-08.md` §4). That
  addressed *unlabelled* parts; every part now carries a stamp, so that branch is spent.
- **Not** any change to a keeper, marker, shard, registry sidecar or bench payload.

## 5. The cost being carried, stated plainly

Since the stamp was introduced, **every** fingerprint move has been adjudicated as
payload-inert, and each cost a session. The gate has so far produced zero true positives and
three false alarms — which is not an argument that its guarantee is worthless (the nyiso-148
defect it closes was real and expensive), but *is* an argument that its trigger is
mis-tuned. A gate that reliably fires on comment edits is on the path to being routinely
re-stamped without adjudication, which is exactly the failure mode
`check_bench_freshness.py`'s own module docstring warns about for the SOFT tier: *"gating on
them would mark every part stale within a week and train everyone to ignore the signal."*
That warning now applies to the HARD tier too.

---

**Evidence** — every number above is reproducible from committed artifacts at `49647dd6`,
with no solve:
`git show 677b605a -- scripts/render_calibration_html.py` (the one comment hunk);
`ast.parse` comparison across `677b605a^`..`677b605a`;
`scripts/lib/bench_stamp.builder_fingerprint()` evaluated at each revision;
`tokenize` + `ast.get_docstring` prose accounting over `BUILDER_SOURCES`;
the `build_payload` call-closure walk over the file's own AST.
