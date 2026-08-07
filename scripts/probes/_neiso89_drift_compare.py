"""neiso-89 bisect comparator — locate the HEAD drift in the NEISO keeper's 2025.

neiso-87 §4.0 found that replaying the committed keeper
``2026-08-05-neiso-83-ca1-reclass`` at HEAD reproduces 2023 and 2024 identically
and DIVERGES in 2025, confined entirely to January (731 of 744 hours), with
max |Δλ| $25.52 and mean Δλ −0.334 $/MWh over the year. Owner decision D-88.3
sent it to its own bisect session; this is that session's instrument.

It compares two solved 2025 sidecar sets and reports the drift signature at the
grain the finding is stated in — so a bisect step is a single number to read
(``differs`` / ``identical``) plus the January localisation that says whether a
candidate commit reproduces the SAME defect or a different one.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_neiso89_drift_compare.py \
        --a /home/user/bisect-out/KEEPERSHA_2025 \
        --b /home/user/bisect-out/HEAD_2025 \
        [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEAR = 2025
#: Hours in January of a non-leap 8760 year — the window neiso-87 localised to.
JAN_HOURS = 744
#: Sidecars every solve writes since 2026-08-03 (CLAUDE.md rule 15).
SIDECARS = ("class_hourly", "system", "storage", "reserve_family")


#: Hours per month in a non-leap 8760-hour year, Jan..Dec.
_MONTH_HOURS = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)


def _month_profile(delta: np.ndarray) -> dict:
    """Per-month ``{n_differing, max_abs, mean}`` for an 8760-hour delta."""
    out: dict[str, dict] = {}
    start = 0
    for i, n in enumerate(_MONTH_HOURS, start=1):
        seg = delta[start : start + n]
        nz = int(np.sum(np.abs(seg) > 1e-9))
        if nz:
            out[f"{i:02d}"] = {
                "n": nz,
                "max_abs": round(float(np.max(np.abs(seg))), 4),
                "mean": round(float(np.mean(seg)), 4),
            }
        start += n
    return out


def _read(bundle: Path, kind: str) -> pd.DataFrame | None:
    """Read one hourly sidecar from a bundle, or ``None`` when absent."""
    p = bundle / "hourly" / f"{kind}_{YEAR}.parquet"
    if not p.is_file():
        return None
    df = pd.read_parquet(p)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df.reset_index(drop=True)


def _price_series(bundle: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """Return ``(hourly_system_price, hour_index)`` for a bundle's P1 pass.

    The ``system`` sidecar is per (zone, hour), so the system price is the
    DEMAND-WEIGHTED zonal mean — the same construction the keeper's registered
    mean λ uses, so the numbers here are comparable to neiso-87 §2.2/§4.0
    ($70.049 for the committed keeper's 2025) rather than to a zone.
    """
    df = _read(bundle, "system")
    if df is None or "price" not in df.columns:
        return None
    df = df.copy()
    w = df["demand"].to_numpy(float)
    df["_num"] = df["price"].to_numpy(float) * w
    g = df.groupby("hour", sort=True).agg(num=("_num", "sum"), den=("demand", "sum"))
    return (g["num"] / g["den"]).to_numpy(float), g.index.to_numpy(int)


def compare(arm_a: Path, arm_b: Path) -> dict:
    """Compare two solved 2025 bundles; return the drift signature."""
    out: dict = {"arm_a": str(arm_a), "arm_b": str(arm_b), "sidecars": {}}
    for kind in SIDECARS:
        a, b = _read(arm_a, kind), _read(arm_b, kind)
        if a is None or b is None:
            out["sidecars"][kind] = "missing"
            continue
        out["sidecars"][kind] = (
            "identical" if a.equals(b) else f"differs ({len(a)} vs {len(b)} rows)"
        )

    ra, rb = _price_series(arm_a), _price_series(arm_b)
    if ra is None or rb is None or len(ra[0]) != len(rb[0]):
        out["price"] = "unavailable"
        return out
    pa, pb = ra[0], rb[0]

    d = pb - pa
    nz = np.flatnonzero(np.abs(d) > 1e-9)
    out["price"] = {
        "n_hours": int(len(d)),
        "n_hours_differing": int(nz.size),
        "max_abs_delta": round(float(np.max(np.abs(d))), 4),
        "mean_delta_year": round(float(np.mean(d)), 4),
        "mean_lambda_a": round(float(np.mean(pa)), 4),
        "mean_lambda_b": round(float(np.mean(pb)), 4),
        # The localisation leg: neiso-87 measured EVERY differing hour inside
        # January. A candidate that moves hours outside it is a DIFFERENT defect.
        "differing_in_january": int(np.sum(nz < JAN_HOURS)),
        "differing_outside_january": int(np.sum(nz >= JAN_HOURS)),
        "first_differing_hour": int(nz[0]) if nz.size else None,
        "last_differing_hour": int(nz[-1]) if nz.size else None,
        # Month profile: which months move, and by how much. A drift that is
        # ONE month is a different object from one smeared across the year.
        "by_month": _month_profile(d),
    }
    out["verdict"] = "IDENTICAL" if nz.size == 0 else "DIVERGES"
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--a", required=True, type=Path, help="baseline bundle dir")
    ap.add_argument("--b", required=True, type=Path, help="comparison bundle dir")
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    res = compare(args.a, args.b)
    print(json.dumps(res, indent=1))
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main()
