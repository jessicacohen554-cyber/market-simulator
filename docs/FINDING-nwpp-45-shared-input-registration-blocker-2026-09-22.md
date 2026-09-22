# FINDING — a sharded bundle cannot be registered: the benchmark inputs are a gitignored sibling

**Lane:** NWPP-45 · **Date:** 2026-09-22 · Branch `claude/nwpp-45-registration-coal-lef7ra`
**Scope:** infrastructure, program-wide. **Zero LP spent.**

---

## 1. The defect

`dashboard_add_run.py` dies with

```
TypeError: Expected a path-like, list of path-likes or a list of Datasets
           instead of the given type: NoneType
```

inside `render_calibration_html.build_payload`. The source is three unguarded reads:

```python
e923_all  = pd.read_parquet(bundle_input_path(bdir, "eia923"))   # :1409
e930_all  = pd.read_parquet(bundle_input_path(bdir, "eia930"))   # :1410
campd_all = pd.read_parquet(bundle_input_path(bdir, "campd"))    # :1411
```

`bundle_input_path` is typed `-> Path | None` and returns `None` when the frame cannot be
resolved. Two more call sites had the same shape: `run_calibration_full.py:9406` (`eia923`,
the ERCOT report path) and `scripts/lib/session_score.py:40`.

**Why the frame is absent.** A bundle's benchmark/input parquets do not live in the bundle.
They live in the content-addressed shared store `results/calibration/_shared/<ISO>/`, which is
**gitignored** (`.gitignore:707-712` — *not* `:2284` as `RESULT-nwpp-44` §1c.3 cites; that line
is the SPP-only re-ignore inside the SPP-43 negation block) and is a **SIBLING of the bundle
dir, not a child**. Rule 34 `[R-SHARD-PROMOTABLE]` (a) has a shard commit its own out-dir:
`git add results/calibration/<out-dir>` cannot reach a sibling. So a shard can solve a perfect,
fully-verified bundle and the parent still receives something it **structurally cannot
register, report or score**.

## 2. Blast radius — this is not an NWPP problem

Measured at HEAD `b969ffaa`, over every registered run's `meta.json`:

| ISO | registered run | shared inputs resolvable? |
|---|---|---|
| ERCOT | `2026-09-19-ercot266-mer-five-year` | **0 of 5** |
| NEISO | `2026-09-19-neiso112-mer-year-isolated` | **0 of 8** |
| CAISO | `2026-09-20-caiso-290-leftedge` | **6 of 9** |
| MISO | `2026-09-20-miso-264-anchor-vintage` | **0 of 9** |
| NWPP | `2026-09-20-nwpp-44-measured-take` | **0 of 8** |
| NYISO | `2026-09-20-nyiso247-fuel-invariance-disarm` | **0 of 9** |
| PJM | `2026-09-20-pjm-h15-coalwindow-span` (+ touchpoint) | **0 of 8** each |
| SOCO | `2026-09-20-soco53g-prb-own-iso`, `…-soco57-measured-cc-heat` | **0 of 8** each |
| SPP | four runs | **all present** |

**10 of 14 registered runs — every ISO but SPP — cannot resolve their benchmark inputs in a
fresh checkout.** SPP is clean only because SPP-43 hand-negated its own ISO's store path in
`.gitignore:2283-2285`, and that negation is deliberately SPP-only (its own comment explains
why a blanket negation is unsafe: it would let any lane's `git add` sweep another ISO's inputs
onto `main`, rule 32(c)(6)).

So the state of the program is that **the current designated keeper of six of nine ISOs is not
re-registrable, re-reportable or re-scorable from a clean clone.**

## 3. Which fix, and why

**(i) Have the bundle carry its own copy.** Rejected. This reverts the content-addressed store,
whose entire purpose is that these frames are byte-identical across runs of an ISO — ~6 MB per
bundle, gigabytes across the archive, and the bulk of the working-tree checkout that fills the
disk on a fresh clone (`bundle_io` module docstring). Paying that back to fix an error-handling
gap is the wrong trade.

**(ii) Rebuild from the recorded content hash.** A hash cannot regenerate bytes, so as stated
this is not a route. But it contains the right idea with the roles reversed. The *recipe* is
recorded — `meta.json` carries `iso`, `years`, and the benchmark flags (`btm_backfill_year`,
`mustrun_chp_btm_holdout`, `benchmark_membership_vintage_union`) — and the frames are pure
functions of `(ISO, year, reference data)`, which is exactly what `rebuild_benchmark()` already
exploits to refresh a benchmark with no re-solve. So regeneration is possible at **zero LP**;
the recorded hash is not its input, it is its **proof**.

**(iii) — ADOPTED. Regenerate from the recorded recipe, then VERIFY against the recorded hash.**

Because the store is content-addressed (`<name>-<hash12>.parquet`), a regenerated frame lands at
the reference `meta.json` already records **if and only if** its bytes are what the solve read.
That makes the verification free and total:

* **hash matches** → the bundle is restored and *provably* reads the benchmark it was solved
  and scored against. `meta.json` is left byte-identical.
* **hash differs** → the benchmark builders have drifted since the solve, and adopting the new
  bytes would re-base a scored run's benchmark against a dispatch solved on the old one — a
  **bench/model basis split**. That is a hard error, never a silent swap.

That last branch is the substantive part, and it is a gap in the existing tooling rather than a
hypothetical. `rebuild_benchmark()` today regenerates and **unconditionally re-points
`meta.json`** at whatever it produced. It is *right* for it to do so — that is what "adopt a
benchmark-logic change" means — but it makes it the wrong instrument for recovery, because on a
drifted tree it silently changes what a registered run is scored against. The two intents are
now two entries, and the recovery one verifies.

## 4. What changed

| file | change |
|---|---|
| `scripts/lib/bundle_io.py` | `MissingBundleInput` (a `FileNotFoundError` naming bundle, input, recorded ref and the remedy), `require_bundle_input`, `shared_input_ref`, `missing_bundle_inputs` |
| `scripts/render_calibration_html.py` | the three registration-path reads → `require_bundle_input` |
| `scripts/run_calibration_full.py` | `build_benchmark_frames()` factored out of `rebuild_benchmark()` so there is **one** builder (rule 19 `[R-ONE-MECH]`) and every benchmark-flag recovery inside it — the btm-backfill year, the miso-253 must-run partition, the spp-49 membership union — is reproduced identically by both callers rather than drifting between two copies; new `restore_shared_inputs()`; new `--restore-shared-inputs`; the `eia923` read → `require_bundle_input` |
| `scripts/lib/session_score.py` | the `eia923` read → `require_bundle_input` |
| `tests/scoring/test_bundle_io.py` | 9 new tests over the strict resolver and the restore guard |

`--rebuild-benchmark`'s help now says what it does that the new entry does not (re-point), so
the choice between them is visible at the CLI.

**No `ScenarioConfig` field is added and nothing solve-affecting changes**, so no cache key
moves, no run re-keys, and every keeper is byte-identical. The new CLI flag is a
post-processing entry in the same class as `--rebuild-benchmark` / `--report`, which likewise
appear in no flag or cache-key registry.

## 5. Verified end to end on the live NWPP keeper

```
$ python3 scripts/run_calibration_full.py --restore-shared-inputs \
      results/calibration/nwpp44_takeorpay_reg
INFO:   campd    verified campd-a5fde7813755.parquet
INFO:   eia923   verified eia923-84bb6ac40d29.parquet
INFO:   eia930   verified eia930-e539ed483b64.parquet
INFO: results/calibration/nwpp44_takeorpay_reg: restored 3 shared input(s),
      all hash-verified against meta.json
```

All three regenerated to **the exact hashes the solve recorded**, `meta.json` is byte-identical
(`git diff` empty), and all three inputs now resolve (eia923 2,282 rows; eia930 271,560;
campd 1,725,720). This is also a substantive result about the keeper in its own right: the
NWPP-44 benchmark is **reproducible from committed data at HEAD**, 121+ commits after its legs
were solved.

## 6. What this does NOT fix, stated at the gate

* **`dispatch/<year>_P1.parquet` and `system.parquet` are also gitignored** and are also
  required by `build_payload`. They are genuine per-run solve outputs, so rule 34(a) has the
  shard push them **inside** its own out-dir and they arrive with the bundle. The shared store
  is the one input class that cannot arrive that way. A *committed keeper* in a fresh checkout
  therefore still lacks its dispatch parquets — that is rule 15's slim committed set working as
  designed, not this defect.
* **It does not make a drifted bundle registrable.** If the builders have moved, restore fails
  loudly and the operator chooses: adopt via `--rebuild-benchmark` and re-score, or re-solve.
  That is the intended outcome, not a shortfall.
* The per-ISO `.gitignore` negation route (SPP-43's) still works and is untouched. It is now
  unnecessary for recovery, but it remains the only way to make a store entry *committed*.

## 7. Recommendation for shard prompts

A shard prompt no longer needs a `_shared` negation. The parent's recipe after fetching a leg is
one zero-LP line before scoring or registering:

```
python3 scripts/run_calibration_full.py --restore-shared-inputs results/calibration/<bundle>
```
