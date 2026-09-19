"""ercot-267: WHICH ERCOT units did the SOCO-15 COD-ramp regrain move, and WHEN?

The bisect (``_ercot267_bisect_driver.py``) named the commit; this says whether
its effect has the SHAPE the repair claims. A COD regrain should move capacity
in the months around a unit's real commercial-operation date and nowhere else —
a concentrated, calendar-anchored change. A flat, all-year change of the same
size would instead be a derate wearing a COD costume, and would not be a repair.

So this rebuilds one year at two shas and reports, per LP unit whose
``availability`` row moved: its class, its pmax, the annual delta, and the
MONTHLY profile of the delta. Zero LP.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_ercot267_cod_unit_delta.py \\
        --pre 6d8dd509b2 --post a0bcb04f93 --year 2023 --meta <control meta>
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

CHILD = r"""
import contextlib, io, json, sys
import numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "scripts"); sys.path.insert(0, "src")
BUNDLE, YEAR, META_PATH = sys.argv[1], int(sys.argv[2]), sys.argv[3]
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
av = np.ascontiguousarray(np.asarray(fa.availability), dtype=float)
# 8760 hours -> 12 model months on the model's own equal-ish split: use the
# real calendar month boundaries of a 365-day clock so a "month" is readable.
DAYS = [31,28,31,30,31,30,31,31,30,31,30,31]
edges, acc = [0], 0
for d in DAYS:
    acc += d * 24
    edges.append(acc)
monthly = np.stack([av[:, edges[i]:edges[i+1]].sum(axis=1) for i in range(12)], axis=1)
groups = ["" ] * len(fa.unit_ids) if fa.plant_group is None else [str(g) for g in fa.plant_group]
print("@@JSON@@" + json.dumps({
    "unit_ids": [str(u) for u in fa.unit_ids],
    "group": groups,
    "pmax": [round(float(x), 4) for x in np.asarray(fa.pmax, dtype=float)],
    "monthly": [[round(float(x), 4) for x in row] for row in monthly],
}))
"""


def arm(sha_: str, year: int, meta_path: str) -> dict:
    """One fleet rebuild at ``sha_`` in a throw-away sparse worktree."""
    with tempfile.TemporaryDirectory(prefix="ercot267_unit_") as tmp:
        wt = Path(tmp) / "tree"
        subprocess.run(
            ["git", "worktree", "add", "--detach", "--no-checkout", str(wt), sha_],
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
            return json.loads(line[len("@@JSON@@") :])
    raise SystemExit(f"no payload at {sha_}\n{p.stdout[-2000:]}\n{p.stderr[-3000:]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pre", required=True)
    ap.add_argument("--post", required=True)
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()

    meta_path = str(Path(a.meta).resolve())
    pre, post = arm(a.pre, a.year, meta_path), arm(a.post, a.year, meta_path)
    assert pre["unit_ids"] == post["unit_ids"], "unit set moved — not a COD-only change"

    moved = []
    for i, uid in enumerate(pre["unit_ids"]):
        d = [round(post["monthly"][i][m] - pre["monthly"][i][m], 4) for m in range(12)]
        if any(abs(x) > 1e-6 for x in d):
            moved.append(
                {
                    "unit": uid,
                    "group": pre["group"][i],
                    "pmax": pre["pmax"][i],
                    "annual_delta": round(sum(d), 4),
                    "monthly_delta": d,
                }
            )
    moved.sort(key=lambda r: r["annual_delta"])

    month_tot = [round(sum(r["monthly_delta"][m] for r in moved), 2) for m in range(12)]
    print(f"{a.year}: {len(moved)} of {len(pre['unit_ids'])} LP units moved")
    print(
        "monthly total delta (MW-h): "
        + "  ".join(f"{m + 1:02d}:{month_tot[m]:,.0f}" for m in range(12))
    )
    print(
        f"\n{'unit':<14}{'class':<12}{'pmax':>10}{'annual Δ':>14}   first/last month with Δ"
    )
    for r in moved[:40]:
        nz = [m + 1 for m, x in enumerate(r["monthly_delta"]) if abs(x) > 1e-6]
        print(
            f"{r['unit']:<14}{r['group']:<12}{r['pmax']:>10,.1f}{r['annual_delta']:>14,.1f}"
            f"   {nz[0] if nz else '-'}..{nz[-1] if nz else '-'} ({len(nz)} mo)"
        )
    if len(moved) > 40:
        print(f"... and {len(moved) - 40} more")
    if a.out:
        a.out.write_text(
            json.dumps(
                {
                    "year": a.year,
                    "pre": a.pre,
                    "post": a.post,
                    "monthly_total_delta": month_tot,
                    "moved": moved,
                },
                indent=1,
            )
            + "\n"
        )
        print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
