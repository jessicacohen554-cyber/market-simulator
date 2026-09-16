"""nyiso-236 PHASE 0 (ZERO-LP): the hydro SHAPE gap, and how price-responsive the LP makes hydro.

Record: ``docs/PRECOMMIT-nyiso236-hydro-budget-period-screen-2026-09-16.md`` §1.

Hydro is ~26 TWh/yr in NYISO -- more than wind and solar combined -- and it appears
in neither ``fuelRows`` nor ``nonfossil`` in the run payload, so **C1 never scores
it**. This probe measures what is actually wrong with it, from committed artifacts
only:

* **LEVEL is fine.** Annual model hydro against EIA-930 ``NG: WAT`` (the measured
  NYISO hydro meter), and monthly energy, which the armed ``hydro_dispatch_envelope``
  / ``hydro_min_flow_floor`` family already pins.
* **SHAPE is not.** Hourly correlation and the model/actual standard-deviation ratio.
* **WHY**, in the one statistic that names a mechanism: the correlation of hydro
  output with price, on each side against ITS OWN price. The LP dispatches hydro as
  a price-optimizing arbitrageur inside its monthly budget; the real fleet is
  roughly half as price-responsive, because 71.38 % of its MW sits on regulated
  Great-Lakes outflow (nyiso-219).

This reproduces, from the price side, the residual nyiso-218 §8 localized from the
load side ("within-month day-to-day r 0.207-0.392", "the keeper tracks load at
1.86-2.25x the actual"). It is a DIAGNOSTIC: it is the motive for testing a
mechanism, never the instrument that identifies one, and nothing here is a gate
(rule 1 ``[R-STRUCT]``).

Usage (from the repo root, ``--profile nyiso`` hydration)::

    python3 scripts/probes/nyiso236_hydro_shape_phase0.py
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

METER = Path("data/raw/eia-930-hourly/NYIS hourly.parquet")
ACTUAL_LMP = Path("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
HOURS = 8760


def payload_gm(path: Path) -> dict:
    """Return ``{year: {class: TWh}}`` from a committed dashboard run payload."""
    s = path.read_text()
    blob = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    d = json.loads(gzip.decompress(base64.b64decode(blob)))
    return {y: v["gmModel"] for y, v in d["years"].items()}


def model_price(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray]:
    """``(load-weighted zonal price $/MWh, total load MW)`` per hour, P1 pass."""
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    p = df.pivot(index="hour", columns="zone", values="price").sort_index().to_numpy(float)
    d = df.pivot(index="hour", columns="zone", values="demand").sort_index().to_numpy(float)
    return (p * d).sum(axis=1) / d.sum(axis=1), d.sum(axis=1)


def main() -> None:
    """Print the level table, the shape table and the price-response table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=Path("results/calibration/nyiso235_gasrepair_span"))
    ap.add_argument("--years", type=int, nargs="+", default=[2022, 2023, 2024, 2025])
    ap.add_argument("--tail-pct", type=float, default=1.0)
    args = ap.parse_args()

    meter = pd.read_parquet(METER)
    meter["ts"] = pd.to_datetime(meter["Local date"])
    meter["yr"] = meter["ts"].dt.year
    act_lmp = pd.read_parquet(ACTUAL_LMP)

    print(f"{'year':>6}{'meter TWh':>11}{'model TWh':>11}{'err %':>8}"
          f"{'hourly r':>10}{'sd ratio':>10}{'mo r':>8}"
          f"{'r(hyd,px) act':>15}{'r(hyd,px) mod':>15}{'ratio':>7}")
    for year in args.years:
        sub = meter[meter["yr"] == year]
        a = sub["NG: WAT"].to_numpy(float)[:HOURS]
        ap_ = act_lmp[act_lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)
        ch = pd.read_parquet(args.bundle / f"hourly/class_hourly_{year}.parquet")
        m = ch[(ch["pass"] == "P1") & (ch["klass"] == "hydro")].sort_values("hour")["mw"].to_numpy(float)
        mp, _ = model_price(args.bundle, year)

        ok = np.isfinite(a) & np.isfinite(m) & np.isfinite(ap_) & np.isfinite(mp)
        mo = sub["ts"].dt.month.to_numpy()[:HOURS]
        mm = np.array([m[(mo == k) & ok].sum() for k in range(1, 13)])
        aa = np.array([a[(mo == k) & ok].sum() for k in range(1, 13)])
        ra = float(np.corrcoef(a[ok], ap_[ok])[0, 1])
        rm = float(np.corrcoef(m[ok], mp[ok])[0, 1])
        print(
            f"{year:>6}{a[ok].sum()/1e6:11.3f}{m[ok].sum()/1e6:11.3f}"
            f"{100*(m[ok].sum()-a[ok].sum())/a[ok].sum():+8.1f}"
            f"{np.corrcoef(a[ok],m[ok])[0,1]:10.3f}{m[ok].std()/a[ok].std():10.3f}"
            f"{np.corrcoef(mm,aa)[0,1]:8.3f}{ra:+15.3f}{rm:+15.3f}{rm/ra:7.2f}"
        )
    print("\nDIAGNOSTIC ONLY (rule 1 [R-STRUCT]): motive for a test, never the instrument.")


if __name__ == "__main__":
    main()
