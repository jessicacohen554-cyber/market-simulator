"""Score C3b (monthly load-weighted price NRMSE) straight from a bundle.

**Why this exists.** ``scripts/calibration_verdict.py`` resolves REGISTERED
runs only — it reads the dashboard payload ``frontend/data/backcast/runs/<id>.js``,
which the *registration* path writes. Rule 32 ``[R-SHARD]`` (c)(6) forbids a
shard to register anything, so a shard that has just solved a bundle has no
route to a C3b number, and rule 29 ``[R-SCREEN]``/31 ``[R-RETAIN]`` may leave
that bundle on an ephemeral container that never reaches the parent. nyiso-226
hit exactly that wall: five independent retrieval routes were blocked and the
tightest-margin load-bearing criterion went unmeasured through a whole
three-year span (``docs/ADDENDUM-nyiso226-not-promoted-and-main-reverted-2026-09-10.md``
§3).

This module closes that gap **without weakening anything**: it does not
re-implement the criterion. It rebuilds the one payload block C3b reads —
``lmp[zone] = {"pMon": [...], "dMon": [...]}`` — from the bundle's committed
``hourly/system_<year>.parquet`` using
:mod:`scripts.render_calibration_html`'s own arithmetic, then calls
:func:`scripts.calibration_verdict.score_price_shape` itself. The band, the
load-weighted-actual ladder, the partial-month coverage mask and the NRMSE are
the scorer's, unmodified. Verified against the NYISO keeper
``2026-09-09-nyiso-221-fuelvintage-span``: 0.122 / 0.179 / 0.160 for
2023 / 2024 / 2025, identical to the registered verdict.

It reads the committed benchmark part ``frontend/data/backcast/bench/<ISO>/<year>.json.gz``,
so it measures the arm against exactly the benchmark the registered control was
measured against.

Usage:
    python scripts/score_bundle_price_shape.py results/calibration/<bundle> \
        --iso NYISO --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (_ROOT, _ROOT / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts import calibration_verdict as cv  # noqa: E402
from scripts import render_calibration_html as rch  # noqa: E402


def zone_lmp_block(bundle: Path, year: int) -> dict:
    """Rebuild the payload's ``lmp`` block for one year from the bundle.

    Mirrors ``render_calibration_html.py``'s per-zone construction exactly,
    including its rounding (price to 2 dp, monthly demand to 4 dp in TWh) —
    the rounding is part of the scored quantity, so it is reproduced rather
    than skipped.

    Args:
        bundle: The calibration bundle directory.
        year: Solve year.

    Returns:
        ``{zone: {"pMon": [12], "dMon": [12]}}``.
    """
    sys_all = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sy = rch._primary_pass(sys_all[sys_all["year"] == year])
    out: dict[str, dict] = {}
    for zone, zg in sy.groupby("zone", observed=True):
        price = zg["price"].to_numpy(float)
        dem = zg["demand"].to_numpy(float)
        hr = zg["hour"].to_numpy()
        # hour 0-8759 -> month 0-11 via the cumulative month-hour edges.
        midx = np.clip(np.searchsorted(rch._CUM, hr, side="right") - 1, 0, 11)
        p_mon: list = [None] * 12
        d_mon = [0.0] * 12
        for m in range(12):
            sel = midx == m
            if not sel.any():
                continue
            dd = float(dem[sel].sum())
            p_mon[m] = (
                round(float((price[sel] * dem[sel]).sum()) / dd, 2)
                if dd > 0
                else round(float(price[sel].mean()), 2)
            )
            d_mon[m] = round(dd / 1e6, 4)
        out[str(zone)] = {"pMon": p_mon, "dMon": d_mon}
    return out


def bench_year(iso: str, year: int) -> dict:
    """Load the committed benchmark part for ``(iso, year)``."""
    part = cv.BENCH_DIR / iso / f"{year}.json.gz"
    with gzip.open(part, "rt") as fh:
        return json.load(fh)["bench"]


def score_year(bundle: Path, iso: str, year: int) -> dict:
    """Return the scorer's own C3b record for one bundle-year."""
    ypay = {"lmp": zone_lmp_block(bundle, year)}
    return cv.score_price_shape(year, ypay, bench_year(iso, year), iso)


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: print one C3b line per requested year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--json", action="store_true", help="emit the raw records")
    args = ap.parse_args(argv)

    records = [score_year(args.bundle, args.iso, y) for y in args.years]
    if args.json:
        print(json.dumps(records, indent=1))
        return 0
    for rec in records:
        print(
            f"C3b {args.iso} {rec['year']}: NRMSE={rec.get('model')} "
            f"status={rec.get('status')} tol={rec.get('tol')} "
            f"metric={rec.get('metric')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
