"""miso-153 — does the 2025 EIA-923 PRELIMINARY VINTAGE collapse the model's
across-plant delivered-fuel dispersion, and with it the CT offer spread that
sets MISO's summer peak price? NO LP.

The chain under test, each link already measured elsewhere in this session:

  1. D-3 — `CT_PEAKER` sets the summer peak price in 40.0/42.6/66.0 % of
     top-200-demand zone-hours.
  2. §12 X-1 — CT's across-plant offer spread NARROWS 40.09 -> 38.68 -> 26.45
     $/MWh as C3a worsens -1.98 -> -8.03 -> -15.58 %, and narrows AGAINST the
     fuel move that should widen it.
  3. The keeper arms `gas_plant_monthly_fuel_pricing = True` and
     `coal_plant_monthly_pricing = True`, so per-plant EIA-923 monthly
     delivered costs REPLACE the shared ISO trajectory where reported --
     "months with no reported cost keep the trajectory"
     (`data/fuel/resolve.py:56-120`).
  4. The C1 scorer reports the 2025 EIA-923 vintage as PRELIMINARY with
     incomplete plant data -- `CT_PEAKER` 71/96 prior plants missing,
     **26 % reporting**.

If (3)+(4) hold then in 2025 most CT plants fall back to ONE shared
trajectory price, which collapses across-plant fuel dispersion and therefore
the offer spread at exactly the margin that sets the peak price.

Statistics:

  F-1  across-plant dispersion of the annual-mean resolved delivered fuel
       price, per class, per year (p10/p50/p90, p90-p10, capacity-weighted).
  F-2  the FALLBACK SHARE: the fraction of a class's plants whose resolved
       price series is (numerically) the class's modal series -- i.e. plants
       carrying no plant-specific overlay.
  F-3  the count of DISTINCT resolved price series per class per year. A
       collapse shows up here as a fall in distinct series.

**This measures the INPUT, not a mechanism.** No lever is proposed here and no
`ScenarioConfig` field is added.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    PYTHONPATH=$PWD .venv/bin/python scripts/probes/_miso153_fuel_dispersion.py
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE

from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
)

OUT = REPO / "results/calibration/_miso153_fuel_dispersion.json"
YEARS = (2023, 2024, 2025)
CLASSES = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL", "CC_CHP", "CT_CHP")


def _plant_of(uid: str) -> int:
    m = re.search(r"_p(\d+)_", uid)
    return int(m.group(1)) if m else -1


def _wq(vals: np.ndarray, wts: np.ndarray, q: float) -> float:
    o = np.argsort(vals)
    v, w = vals[o], wts[o]
    c = np.cumsum(w)
    if c[-1] <= 0:
        return float("nan")
    return float(np.interp(q / 100.0 * c[-1], c, v))


def run_year(year: int) -> dict:
    cfg = dataclasses.replace(keeper_config(), weather_year=year)
    _raw, fleet, arrays, fuel_prices, _mc, _zn = build_year(cfg, year)

    fp = np.asarray(fuel_prices, dtype=np.float64)
    if fp.ndim == 1:
        fp = np.broadcast_to(fp[:, None], (fp.shape[0], 8760))
    pmax = np.asarray(arrays.pmax, dtype=np.float64)
    klass = np.array([str(g.plant_group or "") for g in fleet], dtype=object)
    plant = np.array([_plant_of(str(g.unit_id)) for g in fleet])

    out = {}
    for k in CLASSES:
        sel = klass == k
        if not sel.any():
            continue
        pl = plant[sel]
        fpk = fp[sel]
        capk = pmax[sel]
        # one observation per PLANT: annual-mean delivered price, cap-weighted
        vals, wts, sigs = [], [], []
        for p in np.unique(pl):
            m = pl == p
            series = fpk[m][0]                       # same fuel for the plant
            vals.append(float(series.mean()))
            wts.append(float(capk[m].sum()))
            # F-2/F-3 signature: round to 6 dp so float noise is not a series
            sigs.append(np.round(series, 6).tobytes())
        vals = np.asarray(vals)
        wts = np.asarray(wts)
        cnt = Counter(sigs)
        modal_n = cnt.most_common(1)[0][1] if cnt else 0
        out[k] = {
            "n_plants": int(len(vals)),
            "p10": _wq(vals, wts, 10), "p50": _wq(vals, wts, 50),
            "p90": _wq(vals, wts, 90),
            "p90_minus_p10": _wq(vals, wts, 90) - _wq(vals, wts, 10),
            "capwtd_mean": float(np.average(vals, weights=wts)),
            "n_distinct_series": int(len(cnt)),
            "modal_series_plants": int(modal_n),
            "fallback_share": float(modal_n / len(vals)) if len(vals) else None,
        }
    return out


def main() -> None:
    res = {"bundle": BUNDLE.name, "years": {}}
    for y in YEARS:
        print(f"\n===== {y} =====", flush=True)
        r = run_year(y)
        res["years"][str(y)] = r
        print(f"  {'class':<12}{'n':>4}{'p10':>8}{'p50':>8}{'p90':>8}"
              f"{'p90-p10':>9}{'distinct':>10}{'fallback':>10}")
        for k, v in r.items():
            print(f"  {k:<12}{v['n_plants']:>4}{v['p10']:>8.3f}{v['p50']:>8.3f}"
                  f"{v['p90']:>8.3f}{v['p90_minus_p10']:>9.3f}"
                  f"{v['n_distinct_series']:>10}"
                  f"{v['fallback_share']*100:>9.1f}%")
    OUT.write_text(json.dumps(res, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
