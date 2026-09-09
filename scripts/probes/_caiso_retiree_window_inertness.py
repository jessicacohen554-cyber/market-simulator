"""caiso-fuelvintage-1 charter task 3 (ZERO LP): does the widened retiree window move 2023-2025?

``7934e92c`` widened ``RETIREMENT_WINDOW_START`` 2023 -> 2019, adding 86 units /
1,700.6 MW summer to CAISO's fleet — **every one of them retired in 2019-2022**,
so in a 2023, 2024 or 2025 solve the COD ramp should mask all of them offline
for all 8,760 hours and the training window should not move at all.

"Should" is the charter's own worry, and it names the mechanism precisely: the
COD ramp deliberately does **not** touch ``pmax``, so an added unit still enters
``FleetArrays`` as a row, and anything that reads *capacity* rather than
*availability* can move even though the unit can never dispatch. A reserve
requirement, an accreditation census, a share denominator or a capacity-keyed
offer statistic would all do it silently.

The consuming code is unchanged by that commit — it changed one parquet artifact
(20,185 -> 35,250 bytes) and the builder that writes it — so the whole question
is an A/B on that single file, and it needs no LP: two ``fleet_only`` rebuilds
per year on the keeper's own recipe, one against the shipped (widened) artifact
and one against its pre-commit parent, differenced on every LP-visible array.
The LP is deterministic in these inputs, so bit-identical inputs are a *stronger*
statement than a bit-identical dispatch: they say the solve could not have
differed, rather than that this one did not.

Usage::

    PYTHONPATH=.:src:scripts uv run python \
        scripts/probes/_caiso_retiree_window_inertness.py
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
ARTIFACT = REPO / "data/raw/eia-860/eia860_generator_retired_within_window.parquet"
WIDEN_COMMIT = "7934e92c"
BUNDLE = REPO / "results/calibration/caiso260_demand_vintage"
T = 8760

#: Every LP-visible array. ``pmax`` and ``min_gen`` are the capacity-denominated
#: ones the charter's worry is actually about; ``availability`` is what the COD
#: ramp masks. Keep both, and keep this exhaustive.
ARRAYS = (
    "pmax",
    "pmin",
    "min_gen",
    "availability",
    "heat_rate",
    "emission_rate",
    "vom",
    "fuel_type_idx",
)


def _sha(a) -> str:
    x = np.asarray(a)
    if x.dtype.kind in "UO":
        return hashlib.sha256("\x1f".join(map(str, x.tolist())).encode()).hexdigest()[:24]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:24]


#: Each arm runs in its OWN process. ``cod_ramp._load_cod_map`` is an
#: ``lru_cache`` keyed on the eia860 DIRECTORY, not on the artifact's contents,
#: so swapping the parquet under a live interpreter leaves a stale COD map and
#: the control arm silently inherits the arm's retirement dates. That produced a
#: false "retired units are dispatchable" reading on the first pass; process
#: isolation is what makes the A/B mean what it says.
CHILD = r"""
import contextlib, hashlib, io, json, sys
import numpy as np
sys.path[:0] = [".", "src", "scripts"]
from replay_keeper import derived_run_year_inputs, run_year_kwargs
from run_calibration import run_year
from scripts.lib.bundle_fleet import clear_fleet_caches

BUNDLE, year = sys.argv[1], int(sys.argv[2])
ARRAYS = sys.argv[3].split(",")
T = 8760

def sha(a):
    x = np.asarray(a)
    if x.dtype.kind in "UO":
        return hashlib.sha256("\x1f".join(map(str, x.tolist())).encode()).hexdigest()[:24]
    return hashlib.sha256(np.ascontiguousarray(x, dtype=float).tobytes()).hexdigest()[:24]

meta = json.load(open(BUNDLE + "/meta.json"))
kw = run_year_kwargs(meta); kw.update(derived_run_year_inputs(BUNDLE, year))
clear_fleet_caches()
with contextlib.redirect_stderr(io.StringIO()):
    st = run_year(year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
                  fleet_only=True, **kw)
fa = st["fleet_arrays"]
pmax = np.asarray(fa.pmax, dtype=float)
avail = np.asarray(fa.availability, dtype=float)
if avail.ndim == 1:
    avail = avail[:, None] * np.ones(T)
ids = list(map(str, fa.unit_ids))
row = {
    "n_units": len(ids),
    "unit_ids": ids,
    "pmax_sum_mw": float(pmax.sum()),
    # The quantity that decides the LP: capacity the unit may actually deliver.
    "deliverable_MWh": float((pmax[:, None] * avail).sum()),
    "mc_base_sha": sha(st["mc_base"]),
    "fuel_prices_sha": sha(st["fuel_prices"]),
    "demand_sha": sha(st["demand"]),
    "unit_ids_sha": sha(fa.unit_ids),
}
for name in ARRAYS:
    row[name + "_sha"] = sha(getattr(fa, name))
print("@@JSON@@" + json.dumps(row))
"""


def _rebuild(year: int) -> dict:
    """Run one arm in a fresh interpreter against whatever artifact is in place."""
    p = subprocess.run(
        [sys.executable, "-c", CHILD, str(BUNDLE), str(year), ",".join(ARRAYS)],
        cwd=REPO, capture_output=True, text=True,
        env={**__import__("os").environ,
             "PYTHONPATH": f"{REPO}:{REPO / 'src'}:{REPO / 'scripts'}"},
    )
    for line in p.stdout.splitlines():
        if line.startswith("@@JSON@@"):
            return json.loads(line[len("@@JSON@@"):])
    raise SystemExit(f"child failed (rc={p.returncode})\n{p.stdout[-1500:]}\n{p.stderr[-2500:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", default="results/calibration/_caiso_retiree_window_inertness.json")
    args = ap.parse_args()

    scratch = Path(__file__).resolve().parent / "_caiso_retiree_ab_tmp"
    scratch.mkdir(exist_ok=True)
    shipped = scratch / "shipped.parquet"
    parent = scratch / "parent.parquet"
    shutil.copy2(ARTIFACT, shipped)
    parent.write_bytes(
        subprocess.run(
            ["git", "show", f"{WIDEN_COMMIT}^:data/raw/eia-860/eia860_generator_retired_within_window.parquet"],
            cwd=REPO, check=True, capture_output=True,
        ).stdout
    )
    print(f"shipped {shipped.stat().st_size} B   parent {parent.stat().st_size} B", flush=True)

    out: dict = {"widen_commit": WIDEN_COMMIT, "years": {}}
    try:
        for year in args.years:
            shutil.copy2(shipped, ARTIFACT)
            arm = _rebuild(year)          # widened window (HEAD, shipped)
            shutil.copy2(parent, ARTIFACT)
            ctl = _rebuild(year)          # narrow window (pre-7934e92c)

            mismatched = sorted(
                k for k in arm
                if k.endswith("_sha") and arm[k] != ctl[k]
            )
            extra = sorted(set(arm["unit_ids"]) - set(ctl["unit_ids"]))
            row = {
                "n_units_arm": arm["n_units"],
                "n_units_control": ctl["n_units"],
                "n_units_only_in_arm": len(extra),
                "pmax_sum_mw_arm": round(arm["pmax_sum_mw"], 6),
                "pmax_sum_mw_control": round(ctl["pmax_sum_mw"], 6),
                "pmax_sum_delta_mw": round(arm["pmax_sum_mw"] - ctl["pmax_sum_mw"], 9),
                # The load-bearing number: capacity the added rows may actually
                # deliver. A masked retiree adds pmax but zero deliverable MWh.
                "deliverable_MWh_arm": round(arm["deliverable_MWh"], 6),
                "deliverable_MWh_control": round(ctl["deliverable_MWh"], 6),
                "deliverable_MWh_delta": round(
                    arm["deliverable_MWh"] - ctl["deliverable_MWh"], 6
                ),
                "mismatched_arrays": mismatched,
                "mc_base_identical": arm["mc_base_sha"] == ctl["mc_base_sha"],
                "fuel_prices_identical": arm["fuel_prices_sha"] == ctl["fuel_prices_sha"],
                "demand_identical": arm["demand_sha"] == ctl["demand_sha"],
                "units_only_in_arm": extra[:60],
            }
            out["years"][str(year)] = row
            print(
                f"  {year}: units {ctl['n_units']} -> {arm['n_units']} (+{len(extra)})  "
                f"pmax delta {row['pmax_sum_delta_mw']:+.6f} MW  "
                f"DELIVERABLE delta {row['deliverable_MWh_delta']:+.6f} MWh",
                flush=True,
            )
            print(f"        mismatched arrays: {mismatched or 'none'}", flush=True)
    finally:
        shutil.copy2(shipped, ARTIFACT)   # ALWAYS restore the shipped artifact
        print("restored shipped artifact", flush=True)

    dest = REPO / args.out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1))
    print(f"wrote {dest.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
