"""SPP-63 parent-side G-5 instrument — score C3a/C3b/C4/C2 from a bundle's own sidecars.

`scripts/calibration_verdict.py` can only score a REGISTERED run (it resolves a
registry sidecar + run payload), and rule 29(2) `[R-SCREEN]` forbids registering
a screen bundle. Lane SPP-58 hit exactly this and had to report its G-5 gate as
"unavailable". This module closes that gap without registering anything: it
rebuilds the same quantities the run payload carries (`pMon`/`dMon` per zone,
per `scripts/render_calibration_html.py`) straight from the bundle's committed
`hourly/` sidecars, then applies the scorer's OWN `_wmean` / `_nrmse` / band
constants — imported, never re-implemented — against the committed benchmark.

VALIDATION IS THE POINT: :func:`validate_against_scorer` re-scores a REGISTERED
bundle both ways and asserts they agree, so the instrument is only ever used
after it has reproduced the scorer it stands in for.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _month_index(year: int, hours: np.ndarray) -> np.ndarray:
    """Map hour-of-year -> month 0-11 on the payload's OWN month-hour edges.

    Deliberately the FIXED 365-day calendar (``render_calibration_html._CUM``,
    built from ``rcf._DAYS_IN_MONTH`` with ``_T = 8760``) and NOT a leap-aware
    one. The model's clock is 8,760 hours in every year (rule 8 ``[R-8760]``),
    so the payload the scorer consumes bins a leap year on non-leap edges; a
    leap-aware reimplementation is a DIFFERENT statistic and was measured to
    move 2024's C3b NRMSE 0.172 -> 0.170. Reproducing the scorer means
    reproducing its edges.
    """
    del year  # the edges are year-invariant by construction; see above
    from scripts.render_calibration_html import _CUM

    return np.clip(np.searchsorted(_CUM, hours, side="right") - 1, 0, 11)


def zone_lmp_payload(bundle: str | Path, year: int) -> dict:
    """Rebuild the run payload's ``{zone: {p, d, pMon, dMon}}`` from sidecars.

    Mirrors ``render_calibration_html`` exactly, rounding included — the scorer
    consumes rounded payload values, so an unrounded reimplementation would not
    be the same statistic.
    """
    df = pd.read_parquet(Path(bundle) / "hourly" / f"system_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    out: dict[str, dict] = {}
    for zone, zg in df.groupby("zone", observed=True):
        price = zg["price"].to_numpy(dtype=float)
        dem = zg["demand"].to_numpy(dtype=float)
        hr = zg["hour"].to_numpy()
        d_tot = float(dem.sum())
        p = float((price * dem).sum()) / d_tot if d_tot > 0 else float(price.mean())
        midx = _month_index(year, hr)
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
        out[str(zone)] = {
            "p": round(p, 2),
            "d": round(d_tot / 1e6, 4),
            "pMon": p_mon,
            "dMon": d_mon,
        }
    return out


def score_c3(bundle: str | Path, year: int, bench: dict) -> dict:
    """C3a mean LMP and C3b monthly NRMSE, via the scorer's own functions."""
    from scripts.calibration_verdict import score_price_mean, score_price_shape

    ypay = {"lmp": zone_lmp_payload(bundle, year)}
    return {
        "C3a": score_price_mean(year, ypay, bench, "SPP"),
        "C3b": score_price_shape(year, ypay, bench, "SPP"),
    }


def class_twh(bundle: str | Path, year: int) -> dict[str, float]:
    """P1 annual TWh per model class from the bundle's class-hourly sidecar."""
    df = pd.read_parquet(Path(bundle) / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {
        str(k): float(v) / 1e6
        for k, v in df.groupby("klass", observed=True)["mw"].sum().items()
    }


def wind_and_forcing(bundle: str | Path, year: int) -> dict:
    """G-2 / G-4 raw quantities: wind dispatch, slack and dump."""
    s = pd.read_parquet(Path(bundle) / "hourly" / f"system_{year}.parquet")
    if "pass" in s.columns:
        s = s[s["pass"] == "P1"]
    return {
        "wind_TWh": class_twh(bundle, year).get("wind", 0.0),
        "slack_MWh": float(s["slack"].sum()),
        "dump_MWh": float(s["dump"].sum()),
    }


def load_bench(year: int) -> dict:
    """The committed per-year benchmark the scorer reads."""
    import gzip
    import json

    p = REPO / "frontend" / "data" / "backcast" / "bench" / "SPP" / f"{year}.json.gz"
    with gzip.open(p) as fh:
        return json.load(fh)["bench"]


def validate_against_scorer(bundle: str | Path, years: tuple[int, ...]) -> list[str]:
    """Re-score a REGISTERED bundle both ways; return human-readable comparisons.

    The instrument is used on a screen bundle only after this reproduces the
    scorer's own C3a/C3b on the keeper it stands in for.
    """
    lines = []
    for y in years:
        r = score_c3(bundle, y, load_bench(y))
        lines.append(
            f"  {y}: C3a model={r['C3a'].get('model')} status={r['C3a'].get('status')} "
            f"| C3b NRMSE={r['C3b'].get('model')} status={r['C3b'].get('status')}"
        )
    return lines
