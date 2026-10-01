# FINDING — PERF-C shard S3: does HiGHS presolve help at ERCOT's current LP size? (2026-09-20)

**STATUS: FINDING — measurement only, no code changed.** Shard `claude/perfc-s3-presolve`,
pinned `source_revision` = `2a87343f8d7302ce84e66f45430a8d3b9e807d80` (`git rev-parse HEAD`
confirmed at start; unchanged throughout — no rebase, no pull). Parent: PERF-C orchestration,
`docs/handoffs/PRECOMMIT-perfc-orchestration-2026-09-20.md` §1 lever L3. This shard edits no
file under `src/` or `scripts/` (rule 27 `[R-PUSH]`); the only committed file is this doc.

**Question.** `src/market_sim/model/lp/model.py:648` sets `h.setOptionValue("presolve", "off")`
on a rationale written when the LP was ~1.8 M columns ("costs ~17s of pure overhead" on a full
8760-hour model). ERCOT 2025 is now 326,680 rows × 21,786,120 columns — presolve has never been
benched at this size. Does turning it ON change the optimum or the prices, and what does it do
to the solve?

**No control solve was run** — per rule 29(b), the keeper's own committed 2025 bundle
(`results/calibration/ercot_mer20260919_five_year/`) is the control, and per
`wallclock-baseline-2026-07.md` §WALLCLOCK 3a the OFF-arm P0/P1 seconds for this exact config are
already on record and are cited, not re-measured.

## 1. Driver (scratch, never committed — pasted verbatim; ran outside `src/`/`scripts/`)

Ran with `.venv/bin/python` (HiGHS 1.14.0, installed via `uv sync` this session — matches the
pinned version). `python3 scripts/hydrate_data.py --profile ercot` confirmed a no-op (full clone,
data already present).

```python
"""PERF-C shard S3 scratch driver — HiGHS presolve ON vs OFF (scratch, never committed).

Not a repo file: lives outside src/ and scripts/ per rule 27 (Sonnet may not edit
infrastructure). Run from the repo root with the `.venv` interpreter. Pasted
verbatim into docs/handoffs/FINDING-perfc-s3-presolve-2026-09-20.md as the record
of exactly what ran.

Monkeypatches highspy.Highs.setOptionValue so a call that sets "presolve" to
"off" (model.py ~line 648) instead sets "on", and forces output_flag True on
that same Highs instance right after so HiGHS's own presolve/postsolve log
lines land in stdout. Mirrors scripts/capture_keeper_goldens.py's
resolve_capture_targets -> build_solve_kwargs -> solve_and_persist pattern for
faithful keeper-recipe reconstruction.
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Running as `python /path/outside/repo/driver.py` puts the driver's own
# directory on sys.path[0], not the repo root cwd, so the `scripts` /
# `market_sim` namespace packages are not importable without this. Pin cwd
# (repo root) onto sys.path explicitly.
sys.path.insert(0, os.getcwd())

# Determinism pin, set BEFORE any market_sim/highspy import so nothing caches
# an unset env var at import time.
os.environ["MARKET_SIM_HIGHS_THREADS"] = "1"
os.environ["MARKET_SIM_WARMSTART"] = "1"
os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"
os.environ["MARKET_SIM_P1_BASIS_SEED"] = "0"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)

import highspy  # noqa: E402

_orig_setOptionValue = highspy.Highs.setOptionValue
SETOPT_LOG: list[tuple[int, str, object]] = []


def _patched_setOptionValue(self, option, value):
    if option == "presolve" and value == "off":
        print(
            f"[MONKEYPATCH] Highs id={id(self)}: intercepted setOptionValue("
            f"'presolve', 'off') -> forcing 'on'",
            flush=True,
        )
        value = "on"
        result = _orig_setOptionValue(self, option, value)
        SETOPT_LOG.append((id(self), "presolve", "on (forced, was off)"))
        _orig_setOptionValue(self, "output_flag", True)
        print(
            f"[MONKEYPATCH] Highs id={id(self)}: output_flag forced True "
            f"(so HiGHS log lines print)",
            flush=True,
        )
        SETOPT_LOG.append((id(self), "output_flag", "True (forced)"))
        return result
    result = _orig_setOptionValue(self, option, value)
    SETOPT_LOG.append((id(self), option, value))
    return result


highspy.Highs.setOptionValue = _patched_setOptionValue

REPO = Path(__file__).resolve()
# Not used for path resolution (driver runs with cwd = repo root); kept for
# the record of where this file physically lived (outside the tree).

from scripts.capture_keeper_goldens import (  # noqa: E402
    build_solve_kwargs,
    drop_dead_config_keys,
    resolve_capture_targets,
)
from scripts.run_calibration import _load_reference  # noqa: E402
from scripts.run_calibration_full import solve_and_persist  # noqa: E402

CAPTURE_KEY = "ERCOT__forward"
SOLVE_YEARS = [2025]
OUT_DIR = Path("results/calibration/perfc_s3_presolve_scratch")

print("=== PERF-C S3 presolve-ON driver ===", flush=True)
print(f"highspy version: {highspy.Highs().version()}", flush=True)

targets = resolve_capture_targets([CAPTURE_KEY])
info = targets[CAPTURE_KEY]
print(
    f"RESOLVED {CAPTURE_KEY} -> keeper={info['keeper_id']} bundle={info['bundle']} "
    f"designated_years={info['years']} role={info['role']}",
    flush=True,
)

meta = json.loads((info["bundle"] / "meta.json").read_text())
registered_years = sorted(int(y) for y in meta["years"])
assert set(SOLVE_YEARS) <= set(registered_years), (
    f"{SOLVE_YEARS} not a subset of bundle's recorded span {registered_years}"
)
hours = int(meta["hours"])

kwargs, defaulted = build_solve_kwargs(meta, solve_and_persist)
dropped_dead = drop_dead_config_keys(kwargs)
print(
    f"build_solve_kwargs: {len(kwargs)} recorded flags, {len(defaulted)} "
    f"defaulted-unrecorded, dropped_dead={dropped_dead}",
    flush=True,
)

OUT_DIR.mkdir(parents=True, exist_ok=True)

reference = _load_reference()

t0 = time.time()
solve_and_persist(
    SOLVE_YEARS,
    "ERCOT",
    hours,
    reference,
    commitment=bool(meta["commitment"]),
    screen_coal=bool(meta["commitment_screen_coal"]),
    run_dir=OUT_DIR,
    note="PERF-C S3 scratch bench — presolve ON monkeypatch, never registered",
    **kwargs,
)
t1 = time.time()

print(f"=== DRIVER DONE: wall {t1 - t0:.1f}s ===", flush=True)
print(f"Total setOptionValue calls logged: {len(SETOPT_LOG)}", flush=True)
presolve_related = [
    (hid, opt, val)
    for (hid, opt, val) in SETOPT_LOG
    if opt in ("presolve", "output_flag")
]
distinct_models = sorted({hid for (hid, _, _) in presolve_related})
print(
    f"Distinct Highs model ids touched by presolve/output_flag calls: {len(distinct_models)}",
    flush=True,
)
for hid, opt, val in presolve_related:
    print(f"  model={hid} setOptionValue({opt!r}, {val!r})", flush=True)
```

Resolved: `ERCOT__forward -> keeper=2026-09-19-ercot266-mer-five-year bundle=results/calibration/
ercot_mer20260919_five_year designated_years=[2024, 2025] role=forward`. `build_solve_kwargs`:
297 recorded flags, 16 defaulted-unrecorded, `dropped_dead={}`. Solved year 2025 only, into a
gitignored scratch dir (`results/calibration/perfc_s3_presolve_scratch/`, never registered, never
pushed, deleted from the working tree is not required by rule 31 since nothing here is a
promotable result — it is a presolve-diagnostic bench, explicitly out of scope for promotion).

**Two attempts were run**, both from the pinned SHA, never concurrently (rule 32):

- **Attempt 1** used an outer `timeout 1800` (the literal 30-minute figure from the task) wrapping
  the *whole process* (data_prep + P0 + P1). P0 alone consumed ~1479s of that budget and finished
  **Optimal** (objective `2.9385449721e+09`, 280,573 iterations) — so the literal hard-stop
  condition ("the first `h.run()` has not finished after 30 minutes") was never triggered. But the
  shared clock left P1 only ~3 minutes, and P1's `h.run()` was killed mid-presolve (before its
  first presolve-reduction print) at `EXIT_CODE=124`. This is an artifact of wrapping the whole
  process in one clock, not evidence that presolve is unworkable on P1.
- **Attempt 2** reran the same driver from a clean scratch dir with a 4200s (70-minute) outer
  timeout, so P1's `h.run()` would get its own real ~30-minute-plus window after P0 completed.
  Both `h.run()` calls finished **Optimal** well inside 30 minutes each. Attempt 2's P0 objective
  (`2.9385449721e+09`, 280,573 iterations) is **bit-identical to the last digit** to attempt 1's
  P0 — the monkeypatched presolve-ON path is deterministic across repeated runs at
  `MARKET_SIM_HIGHS_THREADS=1`. Attempt 2 is the complete record used below.

## 2. Confirmation: the patch reached BOTH the P0 and P1 model

```
[MONKEYPATCH] Highs id=140388434654800: intercepted setOptionValue('presolve', 'off') -> forcing 'on'
[MONKEYPATCH] Highs id=140388434654800: output_flag forced True (so HiGHS log lines print)
   ... (P0 solve — this id) ...
[MONKEYPATCH] Highs id=140388432288592: intercepted setOptionValue('presolve', 'off') -> forcing 'on'
[MONKEYPATCH] Highs id=140388432288592: output_flag forced True (so HiGHS log lines print)
   ... (P1 solve — this id, a distinct Highs() instance — "P1 route: COLD REBUILD") ...
```

Two distinct Highs model ids intercepted, one per pass, confirming presolve was forced ON for
both P0 and P1 (`model.py`'s `presolve off` line runs once per `DispatchModel` build, and P1 here
takes the COLD REBUILD route — `MARKET_SIM_P1_FLOOR_INPLACE` off by default — so it is a fresh
`Highs()` instance, not a reuse of P0's).

## 3. HiGHS presolve reduction lines (verbatim, both passes)

**P0:**
```
LP has 326680 rows; 21786120 cols; 53712656 nonzeros
Presolving model
302982 rows, 19497490 cols, 47811148 nonzeros 496s
302982 rows, 12941759 cols, 32602543 nonzeros 971s
Dependent equations search running on 122640 equations with time limit of 1000.00s
Dependent equations search removed 0 rows and 0 nonzeros in 1.78s (limit = 1000.00s)
302982 rows, 12941759 cols, 32602543 nonzeros 1059s
Presolve reductions: rows 302982(-23698); columns 12941759(-8844361); nonzeros 32602543(-21110113)
```

**P1:**
```
LP has 326680 rows; 21786120 cols; 53712656 nonzeros
Presolving model
302982 rows, 19482132 cols, 47765010 nonzeros 475s
302982 rows, 13284524 cols, 34101949 nonzeros 950s
Dependent equations search running on 122640 equations with time limit of 1000.00s
Dependent equations search removed 0 rows and 0 nonzeros in 1.72s (limit = 1000.00s)
302982 rows, 13284524 cols, 34101949 nonzeros 1041s
Presolve reductions: rows 302982(-23698); columns 13284524(-8501596); nonzeros 34101949(-19610707)
```

Presolve removes ~7.2% of rows and ~39–41% of columns/nonzeros — a real, substantial reduction —
but the reduction pass itself costs **1014–1059 seconds of wall time before simplex on the reduced
problem even starts** (the "Dependent equations search" step alone runs its full 1000s time-limit
budget on both passes and removes 0 rows / 0 nonzeros — pure sunk cost). "Solving LP with useful
basis so presolve not used" also appears on both passes' small follow-on iteration-limited re-run
(the `_marginal_emission_rate` re-pricing pass PERF-C lever L2 already flags as read-nowhere for
P0/read-once for P1) — that reuse is HiGHS's own basis-reuse behavior, unaffected by this patch.

## 4. Per-run table

| pass | Highs id | model status | simplex iterations | objective (full precision) | HiGHS `run time` s | market_sim `solve_p{0,1}` phase s |
|---|---|---|---:|---:|---:|---:|
| P0 | 140388434654800 | Optimal | 280,573 | 2,938,544,972.0814 | 1455.21 | 1455.4 |
| P1 | 140388432288592 | Optimal | 278,252 | 3,144,082,841.0655 | 1432.66 | 1432.8 |

(`P-D objective error` 2.69e-13 / 3.80e-13 on the two runs — both comfortably at LP optimality
tolerance.) Full phase line: `data_prep=55.9s solve_p0=1455.4s markup=77.6s solve_p1=1432.8s
results_write=33.4s total=3055.0s`. Memory: `container preflight: memory ceiling 13.36 GiB …
provisioned 6 GiB swap`; `memory peak: cgroup_peak_rss_gib=13.36, cgroup_peak_rss_plus_swap_gib=
15.82, process_vmhwm_gib=13.32`.

**No keeper-recorded objective exists to diff against** — `meta.json` /`metrics.json` for the
committed bundle carry no `objective` field (checked; absent). `wallclock-baseline-2026-07.md`
§WALLCLOCK 3a records iteration counts and seconds for this exact config's OFF arm, not
objectives, so the optimum-stability question below is answered from dispatch/price diffs, not
objective equality — exactly the method the task specified.

## 5. Diff vs. the keeper's committed 2025 outputs

Against `results/calibration/ercot_mer20260919_five_year/hourly/{system_2025,class_hourly_2025}
.parquet` (both P1-only, matching this run's scored pass):

| metric | value |
|---|---|
| Δ total generation (MWh) | **−90.54** of 488,442,880 MWh total (relative 1.85e-7) |
| max \|Δ zonal price\| ($/MWh) | **1.4900** |
| zone-hours with \|Δ price\| > 1e-6 | **3,488 of 61,320** (5.7%) |
| zone-hours with \|Δ price\| > 1e-3 | 3,456 |
| zone-hours with \|Δ price\| > $1 | 28 |
| max \|Δ slack\|, \|Δ dump\|, \|Δ demand\| | 0.0 (exact) |
| max \|Δ reserve_price\| | 2.84e-14 (float noise) |
| max \|Δ marginal_emission_rate\| | 0.874 |
| max \|Δ class-hour dispatch\| (MW) | **2,500.40** (single hour, `solar`) |
| class-hours with \|Δ dispatch\| > 1e-6 | 3,753 of 131,400 (2.9%) |
| per-class Σ Δ (MWh), largest movers | COAL_PRB +5,224; CC_REGULAR −5,091; solar +433; ST_GAS −734; CT_PEAKER −523; COAL_LIGNITE +623 |

Total generation and slack/dump/demand are unchanged to noise level, and the reserve price
(a separate dual family) is bit-identical. But the zonal energy price and per-class dispatch are
**not** dual-degenerate-only noise in the clean sense the codebase's other warm-start neutrality
claims use (e.g. the L1/H2 precedent: "0/61,320 dual-degenerate hours", "16 unit-hours of
offsetting marginal-tie swaps"). Here 5.7% of zone-hours move on price and 2.9% of class-hours
move on dispatch, with single-hour swings up to 2,500 MW (`solar`) and $1.49/MWh — an order of
magnitude larger footprint than the previously-documented benign warm-start ties, even though the
*aggregate* totals hold.

**Caveat (as instructed):** the keeper bundle was solved 2026-09-19 — the same day rule 36
`[R-YEAR-ISOLATION]` (miso-262) flipped `MARKET_SIM_WARMSTART_XYEAR` and `MARKET_SIM_P1_BASIS_SEED`
to default OFF. Neither env knob is recorded in `meta.json` or `run_config_forward_2024_2025.json`
(they are off-registry CLI performance knobs per rule 36(e), not `ScenarioConfig` fields), so
**it cannot be determined from the committed bundle which side of that flip the keeper's own 2025
solve landed on.** If the keeper was solved with a warm-start knob this bench's determinism pin
disables (or vice versa), some or all of the above price/dispatch movement is attributable to that
knob mismatch rather than to presolve — the two are confounded here and cannot be separated
without a same-knob OFF control, which rule 29(b) forbids this shard from running. This bench
answers "does presolve reach a different vertex than the currently-committed bundle", not
cleanly "does presolve alone perturb the vertex versus an otherwise-identical OFF run" — that
second, cleaner question needs a same-session OFF replay, which is exactly the control this shard
was told not to spend.

## 6. Reading

**Did the optimum move?** Total system generation is unchanged to 7 significant figures (Δ = −90.5
MWh of 488.4 million, i.e. noise), and slack/dump/demand are exact — so presolve ON reaches the
*same optimal value* in the aggregate sense the model is scored on. But the *vertex* differs
measurably: prices move on 5.7% of zone-hours (up to $1.49/MWh) and dispatch reallocates up to
2,500 MW between classes in a single hour, which is a real degenerate-vertex effect, not float
noise — consistent with the docstring's own warning ("the vertex reached can differ under
degeneracy") and larger than any other warm-start-class change this repo has measured and
accepted. Whether presolve itself is the cause, or the confound with the keeper's unknown
2026-09-19 warm-start knobs (§5 caveat), is not resolved by this bench alone.

**Was presolve cheaper or dearer?** Unambiguously **dearer**, and by a wide margin, at this LP
size. Against the OFF-arm numbers already on record for this identical config
(`wallclock-baseline-2026-07.md` §WALLCLOCK 3a, pinned-anchor arm, ERCOT 2025 row — cited, not
re-run: `solve_p0=334.7s` (273,522 iters), `solve_p1=363.7s` (273,933 iters), `total=785.9s`):

| phase | OFF (on record) | ON (this bench) | ratio | Δ |
|---|---:|---:|---:|---:|
| `solve_p0` | 334.7 s (273,522 iters) | 1455.4 s (280,573 iters) | 4.35× | +1120.7 s |
| `solve_p1` | 363.7 s (273,933 iters) | 1432.8 s (278,252 iters) | 3.94× | +1069.1 s |
| `total` | 785.9 s | 3055.0 s | 3.89× | **+2269.1 s (+37.8 min)** |

The presolve reduction itself (§3) removes ~39–41% of columns/nonzeros — a genuine, non-trivial
reduction — but costs **1014–1059 s of wall time per pass** to compute (the "Dependent equations
search" alone burns its full 1000 s budget for zero rows/nonzeros removed, on both passes), and
the resulting reduced-problem simplex solve needs essentially the **same number of iterations**
as the OFF arm needed on the *full, unreduced* problem (280,573 vs 273,522 for P0; 278,252 vs
273,933 for P1 — presolve iterations are actually slightly *higher*). So presolve buys no
iteration-count benefit here at all, while adding roughly 1000 s/pass of pure presolve/postsolve
overhead — the exact failure mode the 2018-era rationale in `model.py:648` predicted at 1.8 M
columns ("scales with the column count while removing almost nothing"), just twelve hundred
seconds worse at 21.8 M columns instead of seventeen. **Conclusion: do not adopt presolve at this
LP size.** The `model.py:648` `presolve off` setting and its comment remain correct in direction;
only the cited column count and specific seconds figure are now stale (this bench is the
up-to-date number, should the comment ever be refreshed).

## 7. Retrievability (rule 31/34 note)

This bench produced no promotable artifact — it is a rejected-on-cost diagnostic, not a keeper
candidate, and its scratch bundle (`results/calibration/perfc_s3_presolve_scratch/`) was never
intended for `main` (rule 29(c)/31 do not apply to a non-promotable bench). Every number this
shard will ever cite is in this doc. The scratch bundle sits on this container's local disk only
and will not survive session end; reproducing it costs one ~51-minute ERCOT 2025 solve (data_prep
+ P0 + P1, per §4) using the driver in §1 unchanged.
