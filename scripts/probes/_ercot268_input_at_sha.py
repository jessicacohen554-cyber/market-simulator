"""ercot-268: the ERCOT keeper's LP inputs at ONE sha — the bisect's measuring stick.

``_ercot268_drift_bisect.py`` differences two shas and found ``availability`` and
``min_gen`` moving in all five years while the plant->class map is bit-identical.
Bisecting *which commit* moved them needs the same measurement at an arbitrary
sha, cheaply and repeatably, so this is that measurement factored out: one
``run_year(fleet_only=True)`` rebuild of the keeper's own recipe in a sparse
worktree at ``--sha``, printing the hashes plus enough summary statistics to say
whether a difference is material or float noise.

Results are cached under ``--cache`` keyed by (sha, year), so re-probing a sha a
binary search already visited costs nothing.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_ercot268_input_at_sha.py \\
        --sha 760012f7a --year 2023 --meta /path/to/control_meta.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/ercot_mer20260919_five_year"
DEFAULT_CACHE = Path("/tmp/_ercot268_input_cache.json")

CHILD = r"""
import contextlib, hashlib, io, json, sys
import numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
BUNDLE, YEAR, META_PATH = sys.argv[1], int(sys.argv[2]), sys.argv[3]

def sha(a):
    if a is None:
        return "NONE"
    x = np.asarray(a)
    if x.dtype.kind in "UO":
        return hashlib.sha256("\x1f".join(map(str, x.ravel().tolist())).encode()).hexdigest()[:24]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:24]

def stats(a):
    if a is None:
        return None
    x = np.ascontiguousarray(np.asarray(a), dtype=float)
    return {"shape": list(x.shape), "sum": round(float(x.sum()), 6),
            "nonzero": int((x != 0).sum()), "min": round(float(x.min()), 8),
            "max": round(float(x.max()), 8)}

from replay_keeper import (run_year_kwargs, derived_run_year_inputs,
                           config_partition_overlay, apply_config_overlay)
from run_calibration import run_year
from scripts.lib.bundle_fleet import clear_fleet_caches
meta = json.loads(open(META_PATH).read())
kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, YEAR))
apply_config_overlay(kw, config_partition_overlay(meta, YEAR))
clear_fleet_caches()
with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
    st = run_year(YEAR, meta["iso"], 8760, float(meta["gas_prices"][str(YEAR)]), {},
                  fleet_only=True, **kw)
fa = st["fleet_arrays"]
out = {"n_units": len(fa.unit_ids)}
for name in ("availability", "min_gen", "pmax", "pmin", "mc_base", "unit_ids", "plant_group"):
    arr = st["mc_base"] if name == "mc_base" else getattr(fa, name, None)
    out[name] = sha(arr)
out["availability_stats"] = stats(fa.availability)
out["min_gen_stats"] = stats(fa.min_gen)
# Per-class availability mass, so a move can be attributed without a second run.
groups = ["" ] * len(fa.unit_ids) if fa.plant_group is None else [str(g) for g in fa.plant_group]
av = np.ascontiguousarray(np.asarray(fa.availability), dtype=float)
mg = (None if fa.min_gen is None
      else np.ascontiguousarray(np.asarray(fa.min_gen), dtype=float))
by = {}
for i, g in enumerate(groups):
    c = by.setdefault(g, {"avail_sum": 0.0, "min_gen_sum": 0.0, "n": 0})
    c["n"] += 1
    c["avail_sum"] += float(av[i].sum())
    if mg is not None:
        c["min_gen_sum"] += float(mg[i].sum())
out["by_class"] = {g: {k: (round(v, 4) if isinstance(v, float) else v)
                       for k, v in c.items()} for g, c in sorted(by.items())}
print("@@JSON@@" + json.dumps(out))
"""


def measure(sha_: str, year: int, meta_path: str, cache_path: Path) -> dict:
    """Return the LP-input fingerprint of ``year`` at ``sha_``, cached."""
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    full = subprocess.run(
        ["git", "rev-parse", sha_], cwd=REPO, capture_output=True, text=True
    ).stdout.strip()
    key = f"{full}:{year}"
    if key in cache:
        return cache[key]

    with tempfile.TemporaryDirectory(prefix="ercot268_sha_") as tmp:
        wt = Path(tmp) / "tree"
        subprocess.run(
            ["git", "worktree", "add", "--detach", "--no-checkout", str(wt), full],
            cwd=REPO,
            check=True,
            capture_output=True,
        )
        try:
            subprocess.run(
                ["git", "sparse-checkout", "set", "--no-cone", "src/", "scripts/"],
                cwd=wt,
                check=True,
                capture_output=True,
            )
            subprocess.run(["git", "checkout"], cwd=wt, check=True, capture_output=True)
            for shared in ("data", "results", "config", "configs", "pyproject.toml"):
                src = REPO / shared
                if src.exists() and not (wt / shared).exists():
                    (wt / shared).symlink_to(src)
            env = dict(os.environ)
            env["PYTHONPATH"] = f"{wt}:{wt / 'src'}:{wt / 'scripts'}"
            env["PYTHONHASHSEED"] = "0"
            env["MARKET_SIM_P1_BASIS_SEED"] = "0"
            p = subprocess.run(
                [sys.executable, "-c", CHILD, str(BUNDLE), str(year), meta_path],
                cwd=wt,
                env=env,
                capture_output=True,
                text=True,
            )
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(wt)],
                cwd=REPO,
                capture_output=True,
            )

    for line in p.stdout.splitlines():
        if line.startswith("@@JSON@@"):
            payload = json.loads(line[len("@@JSON@@") :])
            payload["sha"] = full
            payload["subject"] = subprocess.run(
                ["git", "log", "-1", "--format=%s", full],
                cwd=REPO,
                capture_output=True,
                text=True,
            ).stdout.strip()
            cache[key] = payload
            cache_path.write_text(json.dumps(cache, indent=1, sort_keys=True) + "\n")
            return payload
    raise SystemExit(
        f"no payload at {sha_} (rc={p.returncode})\n{p.stdout[-2000:]}\n{p.stderr[-3000:]}"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha", nargs="+", required=True)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    a = ap.parse_args()

    meta_path = str(Path(a.meta).resolve())
    rows = []
    for s in a.sha:
        r = measure(s, a.year, meta_path, a.cache)
        rows.append(r)
        print(
            f"{r['sha'][:10]}  avail={r['availability'][:16]}  "
            f"min_gen={r['min_gen'][:16]}  "
            f"avail_sum={r['availability_stats']['sum']}  "
            f"min_gen_sum={(r['min_gen_stats'] or {}).get('sum')}  "
            f"| {r['subject'][:70]}",
            flush=True,
        )
    if len(rows) > 1:
        print("\ndistinct availability hashes:", len({r["availability"] for r in rows}))
        print("distinct min_gen hashes:     ", len({r["min_gen"] for r in rows}))


if __name__ == "__main__":
    main()
