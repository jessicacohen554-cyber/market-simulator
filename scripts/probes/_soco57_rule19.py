"""SOCO-57 rule 19 [R-ONE-MECH] proof at FOUR grains, zero LP.

``fuel_prices`` / ``mc_base`` / ``pmax`` / ``availability``, reported as
KEYS MOVED and not only max|delta| (the SOCO-56 lesson: a max|delta| of zero on
mc_base is compatible with an availability gate having fired, and only the key
census distinguishes "inert" from "fired somewhere else").
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.probes._soco57_phase0 import _build  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--set", dest="sets", action="append", default=[])
    args = ap.parse_args()

    ov: dict[str, object] = {}
    for kv in args.sets:
        k, _, v = kv.partition("=")
        ov[k] = {"true": True, "false": False}.get(v.strip().lower(), v)

    for year in args.years:
        bundle = Path(str(args.bundle).replace("YEAR", str(year)))
        a = _build(bundle, year)
        b = _build(bundle, year, ov)
        print(f"\n===== {year}   bundle {bundle.name}   arm {ov} =====")
        groups = [str(getattr(g, "plant_group", "")) for g in a["fleet"]]
        plants = [int(getattr(g, "plant_code", 0) or 0) for g in a["fleet"]]
        for key in ("fuel_prices", "mc_base"):
            x, y = np.asarray(a[key], dtype=float), np.asarray(b[key], dtype=float)
            d = np.abs(x - y)
            rows = d.reshape(len(groups), -1).max(axis=1) if d.ndim > 1 else d
            moved = int((rows > 0).sum())
            print(f"  {key:12s} global max|d| {float(d.max()):.12f}   rows moved {moved}/{len(groups)}")
            per: dict[str, float] = {}
            for i, g in enumerate(groups):
                per[g] = max(per.get(g, 0.0), float(rows[i]))
            for g in sorted(k for k, v in per.items() if v > 0):
                n = sum(1 for i, gg in enumerate(groups) if gg == g and rows[i] > 0)
                pl = sorted({plants[i] for i, gg in enumerate(groups) if gg == g and rows[i] > 0})
                print(f"      {g:12s} max|d| {per[g]:.10f}  rows {n}  plants {pl}")
        fa_a, fa_b = a["fleet_arrays"], b["fleet_arrays"]
        for key in ("pmax", "availability", "heat_rate"):
            if not hasattr(fa_a, key):
                continue
            x, y = np.asarray(getattr(fa_a, key), float), np.asarray(getattr(fa_b, key), float)
            d = np.abs(x - y)
            rows = d.reshape(d.shape[0], -1).max(axis=1) if d.ndim > 1 else d
            moved = int((rows > 0).sum())
            pl = sorted({plants[i] for i in range(len(rows)) if rows[i] > 0}) if moved else []
            print(f"  {key:12s} global max|d| {float(d.max()):.12f}   rows moved {moved}/{len(rows)}  plants {pl}")


if __name__ == "__main__":
    main()
