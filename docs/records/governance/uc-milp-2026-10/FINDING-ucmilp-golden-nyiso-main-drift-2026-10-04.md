# FINDING — the NYISO golden FAIL under uc-milp UC-1 is pre-existing main drift (commit 59490433), not the UC engine

Lane UC-1 (`session_01TaYG9p5stirhcFVYgK3r6j`, Fable), 2026-10-04. Ruled on by
UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`, message 2026-10-04 00:15 UTC):
G-OFF tests whether the UC engine with its gate off is byte-inert; a diff
counts against the engine only if the UC hunks cause it. This record is the
zero-LP discharge of that test for NYISO and the hand-off of the drift itself
to the owner (rule 29 — a CALIBRATED ISO's keeper no longer reproduces at HEAD).
Nothing on `main` is fixed by this lane; the fix is outside its region.

## 1. Facts

| Item | Value |
|---|---|
| Keeper | `2026-10-02-w0-nyiso`, bundle `results/calibration/w0_nyiso_span`, years 2021–2025, composed from five single-year legs |
| Keeper basis | `306f2c00b6268b791fb77c392c8d69a756959e76` (merge of #7037, 2026-10-02 08:21 UTC); legs solved 08:43–08:46 UTC, solve-surface fingerprint `cb770a26d18f570f` |
| Golden shard | `ucmilp-golden-nyiso`, `session_01Bhmmw7g6mNYUpKvmPuttTd` (Opus), off-gate replay at the engine SHA `ec758d64c03f6407fe382f6a52814f3028b71890`; report + unit list on `claude/ucmilp-golden-nyiso` @ `1d3f2799` |
| Recipe fidelity | `313 recorded flags replayed identically; scenario_config 947 matched, 0 drifted` — the recipe is the keeper's; the drift is code-side |
| Result | `golden-diff: FAIL — 30 hourly files (5 yrs × 6 families), 175 numeric columns; 12 failing columns, all 2021`; 2022–2025 bit-identical in every file and column |
| 2021 root symptom | exactly ONE unit's P1 offer `mc` moves: `CT_CHP_NYC_p2493_committed` (CT_CHP, gas_ct, NYC, 88.36 MW), −0.077 $/MWh on every hour of May–June 2021 (hours 2880–4343, 1,464 unit-hours, one contiguous run); `cap_mw` identical everywhere; row sets identical (8,707,440 joined rows) |
| Consequence columns | `system_2021.price` (max 2.72 $/MWh, 10,544 zone-hours), `class_*_2021.mw` (max 70 MW), `storage_2021.*`, `reserve_family_2021.held_mw`, `unit_marginal_2021.{mw,marginal}` — the merit-order consequence of the one offer shift |

## 2. Zero-LP reproduction (no shard, no LP)

Method: the keeper recipe of year 2021 is replayed through
`replay_keeper.build_kwargs` → `run_calibration_full.solve_and_persist`
exactly as `scripts/lib/uc_bench.capture_year(solve=False)` does, with
`run_calibration.run_energy_solve` replaced by a spy that records its inputs
(`fleet`, `mc_base`, every keyword, `dispatch_kwargs`) and aborts before any
LP. The same `data/clean` (regenerated once at the engine SHA, NYISO solve
profile) is read by every tree; only the code differs. Three trees:

| Tree | Checkout |
|---|---|
| **basis** | sparse `git worktree` at `306f2c00` |
| **main-without-UC** | sparse `git worktree` at `origin/main` `e8570532` (the branch's merge-base; carries none of the UC commits) |
| **branch** | `ec758d64` (main-without-UC + the UC-1 commits) |

Results, every comparison at atol = rtol = 0 (`np.array_equal`; sparse
operands by `(A != B).nnz`):

| Comparison | `mc_base` (994 × 8760) | `run_energy_solve` keywords | `dispatch_kwargs` (36 arrays, 50 keys) |
|---|---|---|---|
| main-without-UC vs branch | identical | identical (all `None`) | **identical** |
| basis vs branch | identical | identical | identical except **`solar_cf`**: 5 of 7 zones, all 5,088 daylight hours, max \|Δ\| 0.0017, 25,440 cells |

Bisection of the `solar_cf` carrier inside `306f2c00..origin/main` by file
overlay onto the basis tree:

| Overlay on the basis tree | `solar_cf` equals |
|---|---|
| none | basis |
| `renewables.py` + `zone_assignment.py` from **`59490433`** only | **branch / main** exactly (`wind_cf` unchanged) |
| `renewables.py` from `origin/main` alone | not runnable (signature of `vintage_coords_zone_lookup` changed in `zone_assignment.py` by the same commit) |

`e86fc2c5` ("Vectorize inert hot paths…", the desk's first suspect) was
examined first: its `eia923` / `plant_prices` / `emission_rates` /
`fuel/basis/nyiso` hunks are `iterrows → zip` rewrites with identical
semantics, and the three-way capture shows `mc_base` identical across all
three trees, so it moves nothing on this recipe.

**Pinned commit:** `59490433` — *Admit eGRID-absent wind/solar under
fleet_zone_vintage_coords* — 2026-10-02 08:45:22 UTC, **24 minutes after the
keeper's basis**. It is LIVE for this keeper because `w0_nyiso_span` arms
`fleet_zone_vintage_coords = True`: the renewable zone lookup gains the
coordinate-admitted plants (`renewables._renewable_zone_lookup`), which
changes the zone solar geometry / capacity weights and hence the zonal solar
CF shape.

Chain from `solar_cf` to the symptom (consistent, not byte-proven — proving it
needs the P0 LP, which this discharge excludes): Δ`solar_cf` → P0 dispatch →
the May and June P0 run lengths of `CT_CHP_NYC_p2493` → `model/commitment.
compute_monthly_markup` (startup cost / mean monthly run length, a
calendar-month constant) → −0.077 $/MWh on the committed tranche in exactly
those two months → the P1 deltas. The keeper's adder for that unit is
3.0909 $/MWh in May and 1.4181 in June (keeper `mc` minus the captured
`mc_base`); the golden's May adder is 3.0137 (its first-hour `mc` 33.934921),
and the shard's unit list reports the Δ as a constant −0.0772 over all 1,464
hours (median = max), i.e. the same shift in both months — a monthly-markup
signature, not a fuel or heat-rate change (those would move `mc_base`, which
is identical).

## 3. G-OFF NYISO verdict

**PASS (engine-inert).** Main-without-UC and the branch produce identical
inputs to `run_energy_solve`; the only code difference inside
`run_energy_solve` between them is the `if config.unit_commitment_milp:`
hunk, which does not execute on this recipe (G-DRIFT). The 2021 difference is
pre-existing main drift, pinned to `59490433`, reproduced zero-LP without the
UC hunks. Any off-gate replay of the NYISO keeper at any SHA ≥ `59490433`,
including `origin/main` without this PR, carries the same 2021 difference.

## 4. Scope — does `59490433` move any other keeper?

Zero-LP, from the nine committed `run_config.json`:

| Keeper | `fleet_zone_vintage_coords` | basis vs `59490433` (2026-10-02 08:45 UTC) | exposed |
|---|---|---|---|
| NYISO `w0_nyiso_span` | **True** | `306f2c00`, 08:21 UTC — **before** | **yes (this record)** |
| PJM `closeout_pjm_nuc_full_span` | True | `8c3ea461`, 2026-10-03 03:45 UTC — after | no (already carries it) |
| NEISO `w0_neiso_span` | False | `306f2c00`, before | no (flag off; golden exact) |
| CAISO, ERCOT, MISO, SOCO, SPP, NWPP | False | — | no |

The UC-1 goldens agree: NEISO (42 files / 154 columns), SPP (35 / 196),
SOCO (42 / 238) and ERCOT (forward span 2024–2025, 14 / 84) are exact at
`ec758d64`. The PJM golden, when it reports, replays a keeper that already
includes `59490433`.

## 5. Hand-off

* **Owner, via UC-DESK (rule 29):** the NYISO keeper `2026-10-02-w0-nyiso`
  does not reproduce at HEAD for 2021 (one plant-month offer, 2.72 $/MWh max
  price change over 10,544 zone-hours); whether to re-solve / re-register the
  2021 leg at a SHA ≥ `59490433`, and whether `59490433`'s effect on an armed
  keeper should have earned a control solve at landing, are the owner's
  calls. This lane changes nothing on `main`.
* **UC-1:** records this verdict in the PR's G-OFF table and proceeds once
  the remaining goldens report.

## 6. Artifacts

* Golden report + unit list: branch `claude/ucmilp-golden-nyiso` @ `1d3f2799`
  (`results/bench/uc/golden_nyiso/report.md`, `diff_2021_units.csv`); the
  shard is archived (rule 33); its golden bundle did not outlive the container.
* The three `.npz` / `.pkl` captures are session scratch (not committed). The
  capture spy is `scripts/lib/uc_bench.capture_year(solve=False)` re-stated as
  a standalone script so it runs on a tree that predates `uc_bench.py`
  (identical mechanism, `solve=False`); its text and the exact commands are in
  Appendix A so the reproduction can be re-run from this record alone.

## Appendix A — reproduction commands and the capture script

Prerequisites (one container, the engine SHA checked out at
`/home/user/market-simulator`): `uv sync`;
`python3 scripts/hydrate_data.py --profile nyiso`;
`uv run python scripts/regenerate_clean.py --solve-profile NYISO` (one
`data/clean`, shared by every tree below through a symlink).

```bash
# sparse worktrees (code only; data/ results/ .venv symlinked to the main checkout)
for pair in "ms-basis 306f2c00b6268b791fb77c392c8d69a756959e76" "ms-main e857053252d65b893bb171422002b5d75428cc36"; do
  set -- $pair; W=/home/user/$1
  git worktree add --no-checkout $W $2
  git -C $W sparse-checkout init --cone && git -C $W sparse-checkout set src scripts configs tests/helpers
  (cd $W && git checkout)
  ln -s /home/user/market-simulator/data $W/data; ln -s /home/user/market-simulator/results $W/results; ln -s /home/user/market-simulator/.venv $W/.venv
done
PY=/home/user/market-simulator/.venv/bin/python; B=/home/user/market-simulator/results/calibration/w0_nyiso_span
(cd /home/user/market-simulator && $PY capture_mc.py /home/user/market-simulator 2021 mc/head_2021.npz $B)
(cd /home/user/ms-main  && $PY capture_mc.py /home/user/ms-main  2021 mc/main_2021.npz  $B)
(cd /home/user/ms-basis && $PY capture_mc.py /home/user/ms-basis 2021 mc/basis_2021.npz $B)
# bisection: overlay ONLY 59490433's two files on the basis tree, recapture, restore
cd /home/user/ms-basis
git -C /home/user/market-simulator show 59490433:src/market_sim/data/renewables.py      > src/market_sim/data/renewables.py
git -C /home/user/market-simulator show 59490433:src/market_sim/data/zone_assignment.py > src/market_sim/data/zone_assignment.py
$PY capture_mc.py /home/user/ms-basis 2021 mc/basis_59490433_2021.npz $B
git checkout -- src/market_sim/data/renewables.py src/market_sim/data/zone_assignment.py
```

Comparison: `np.array_equal` on `mc` and on every array under `dk` /
`kw` of the `.kw.pkl` (sparse operands via `(A != B).nnz`), walking dicts,
lists and tuples; shapes and dtypes compared first.

`capture_mc.py` (the spy; nothing here is committed to `scripts/`):

```python
"""Zero-LP capture of NYISO <year> mc_base from the keeper recipe at the tree given as argv[1].

usage: python capture_mc.py <repo_root> <year> <out.npz> [bundle]
Mirrors scripts.lib.uc_bench.capture_year(solve=False) without depending on it.
"""
import json, sys, os
from pathlib import Path
import numpy as np

ROOT = Path(sys.argv[1]).resolve()
YEAR = int(sys.argv[2])
OUT = Path(sys.argv[3])
BUNDLE = Path(sys.argv[4]) if len(sys.argv) > 4 else ROOT / "results/calibration/w0_nyiso_span"
os.chdir(ROOT)
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "src"))
from scripts import replay_keeper as rk
from scripts import run_calibration as rc
from scripts import run_calibration_full as rcf

class CaptureAbort(Exception):
    pass

rk.pin_determinism_env()
meta = json.loads((BUNDLE / "meta.json").read_text())
kwargs = rk.build_kwargs(meta)
kwargs["years"] = [YEAR]; kwargs["iso"] = meta["iso"]; kwargs["hours"] = int(meta.get("hours", 8760))
kwargs["reference"] = rcf._load_reference()
kwargs["run_dir"] = OUT.parent / f"replay_{ROOT.name}"
if hasattr(rk, "enforce_single_recipe_partition"):
    rk.enforce_single_recipe_partition(meta, kwargs["years"], kwargs)
if hasattr(rk, "flipped_default_overlay"):
    rk.apply_config_overlay(kwargs, rk.flipped_default_overlay(BUNDLE, kwargs["years"], meta))
else:
    print("NOTE: no flipped_default_overlay at this tree")
rcf.enforce_legacy_p2_kwargs(kwargs, False)
kwargs.setdefault("note", "zero-LP mc capture (never registered)")
box = {}
real = rc.run_energy_solve
def spy(fleet, fleet_arrays, demand, mc_base, dispatch_kwargs, config, **kw):
    box.update(fleet=fleet, fa=fleet_arrays, mc=np.asarray(mc_base, dtype=float), config=config, dk=dispatch_kwargs, kw=kw)
    raise CaptureAbort()
rc.run_energy_solve = spy
try:
    try:
        rcf.solve_and_persist(**kwargs)
    except CaptureAbort:
        pass
finally:
    rc.run_energy_solve = real
fleet = box["fleet"]; mc = box["mc"]
uid = np.array([str(g.unit_id) for g in fleet]); pc = np.array([int(g.plant_code) for g in fleet])
grp = np.array([str(g.plant_group) for g in fleet]); fuel = np.array([str(g.fuel_type) for g in fleet]); zone = np.array([str(g.zone) for g in fleet])
sel = pc == 2493
dump = {}
for g in [g for g in fleet if int(g.plant_code) == 2493]:
    d = g.model_dump() if hasattr(g, "model_dump") else g.__dict__
    dump[str(g.unit_id)] = {k: (v.tolist() if hasattr(v, "tolist") else v) for k, v in d.items() if not isinstance(v, (list, dict)) or len(str(v)) < 2000}
np.savez_compressed(OUT, mc=mc, unit_id=uid, plant_code=pc, plant_group=grp, fuel=fuel, zone=zone)
(OUT.with_suffix(".plant2493.json")).write_text(json.dumps(dump, indent=1, default=str))
import pickle
def _plain(o, depth=0):
    if isinstance(o, np.ndarray): return o
    if isinstance(o, dict): return {k: _plain(v, depth+1) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return type(o)(_plain(v, depth+1) for v in o)
    if isinstance(o, (int, float, str, bool, type(None))): return o
    if callable(o): return f"<callable {getattr(o,'__name__',type(o).__name__)}>"
    try:
        pickle.dumps(o); return o
    except Exception:
        return f"<{type(o).__name__}>"
with open(OUT.with_suffix(".kw.pkl"), "wb") as fh:
    pickle.dump({"kw": _plain(box["kw"]), "dk": _plain(box["dk"])}, fh)
print("kw keys:", {k: (getattr(v, "shape", None) if v is not None else None) for k, v in box["kw"].items()})
cfg = box["config"]
print("captured", mc.shape, "gens of 2493:", uid[sel].tolist())
print("config id-ish:", getattr(cfg, "cache_key", lambda: "?")())
```
