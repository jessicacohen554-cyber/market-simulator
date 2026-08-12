"""miso-153 Phase 1 identification step — how wide is the model's CT_PEAKER
ACROSS-UNIT offer dispersion at the summer peak, and on which axis? NO LP.

Owner charter (2026-08-12): the miso-151 G-5 across-unit dispersion object,
scoped to CT_PEAKER at peak.

**The scoping blocker this probe exists to size.** MISO's masked
energy-offer corpus carries **no fuel or technology attribute**, and the
offer-side class bridge was **built and REFUTED at miso-138**
(``data/raw/miso-energy-offers/README.md``), so the measured across-unit
dispersion **cannot be scoped to CT_PEAKER from the corpus**. miso-151's G-5
quantiles (DA-2025-07, cap-weighted: p10 0.169 / p50 19.583 / p90 48.007 /
p95 91.445 / p99 298.026 $/MWh; p90-p10 = 47.837) are therefore **FLEET-WIDE**
and are quoted here only as the fleet-wide reference they are — never as a
CT_PEAKER target.

What this probe measures, model-side only, so the identification gap is sized
before any lever is proposed:

  X-1  ACROSS-PLANT dispersion of CT_PEAKER effective mc at the top-200
       model-demand hours: cap-weighted p10/p50/p90/p95/p99 and p90-p10, one
       observation per (plant, hour) at the plant's cheapest econ tranche.
  X-2  the same for every thermal class, so CT's spread is read against its
       own fleet rather than against a fleet-wide number from a different
       population.
  X-3  the DECOMPOSITION — how much of CT's across-plant mc spread is
       heat-rate dispersion (already measured and armed, `measured_ct_heat_rates`
       K at miso-117) versus everything else. Computed by holding the heat rate
       at its cap-weighted mean and re-pricing.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    PYTHONPATH=$PWD .venv/bin/python scripts/probes/_miso153_ct_dispersion.py
"""

from __future__ import annotations

import dataclasses
import json
import re
import sys
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
    keeper_prices,
)

OUT = REPO / "results/calibration/_miso153_ct_dispersion.json"
YEARS = (2023, 2024, 2025)
TOPN = 200
CARRY = ("MISO-East", "MISO-Illinois", "MISO-Indiana", "MISO-Plains",
         "MISO-South", "MISO-West")
THERMAL = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL", "CC_CHP", "CT_CHP",
           "ST_CHP")
QUANTS = (10, 50, 90, 95, 99)

# miso-151 G-5, DA-2025-07, cap-weighted, FLEET-WIDE (no class attribution is
# possible from the masked corpus — miso-138). Reference only.
G5_FLEETWIDE = {"p10": 0.169, "p50": 19.583, "p90": 48.007,
                "p95": 91.445, "p99": 298.026, "p90_minus_p10": 47.837}


def _plant_of(uid: str) -> int:
    m = re.search(r"_p(\d+)_", uid)
    return int(m.group(1)) if m else -1


def _band_of(uid: str) -> str:
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", uid)
    return m.group(2) if m else ""


def _wq(vals: np.ndarray, wts: np.ndarray, q: float) -> float:
    """Capacity-weighted quantile."""
    o = np.argsort(vals)
    v, w = vals[o], wts[o]
    c = np.cumsum(w)
    if c[-1] <= 0:
        return float("nan")
    return float(np.interp(q / 100.0 * c[-1], c, v))


def run_year(year: int) -> dict:
    cfg = dataclasses.replace(keeper_config(), weather_year=year)
    _price, demand = keeper_prices(year)
    _raw, fleet, arrays, fuel_prices, mc, _zn = build_year(cfg, year)

    top = np.sort(np.argsort(demand)[::-1][:TOPN])
    pmax = np.asarray(arrays.pmax, dtype=np.float64)
    avail = np.asarray(arrays.availability, dtype=np.float64)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], (len(fleet), 8760))

    klass = np.array([str(g.plant_group or "") for g in fleet], dtype=object)
    plant = np.array([_plant_of(str(g.unit_id)) for g in fleet])
    band = np.array([_band_of(str(g.unit_id)) for g in fleet], dtype=object)
    hr = np.asarray(arrays.heat_rate, dtype=np.float64)

    out = {"g5_fleetwide_reference": G5_FLEETWIDE, "classes": {}}
    for k in THERMAL:
        # one observation per (plant, hour): the plant's CHEAPEST econ tranche,
        # which is the across-unit position the merit order actually sees.
        sel = (klass == k) & np.char.startswith(band.astype(str), "econ")
        if not sel.any():
            continue
        mc_k = mc[sel][:, top]
        cap_k = (pmax[sel][:, None] * avail[sel][:, top])
        pl = plant[sel]
        vals, wts = [], []
        for p in np.unique(pl):
            m = pl == p
            j = np.argmin(mc_k[m], axis=0)          # cheapest econ per hour
            vals.append(mc_k[m][j, np.arange(len(top))])
            wts.append(cap_k[m].sum(axis=0))
        vals = np.concatenate(vals)
        wts = np.concatenate(wts)
        ok = np.isfinite(vals) & (wts > 0)
        vals, wts = vals[ok], wts[ok]
        q = {f"p{n}": _wq(vals, wts, n) for n in QUANTS}
        q["p90_minus_p10"] = q["p90"] - q["p10"]
        q["n_plants"] = int(len(np.unique(pl)))
        q["capwtd_mean"] = float(np.average(vals, weights=wts))
        out["classes"][k] = q

    # X-3: how much of CT's spread is heat-rate dispersion?
    sel = (klass == "CT_PEAKER") & np.char.startswith(band.astype(str), "econ")
    if sel.any():
        cap = (pmax[sel][:, None] * avail[sel][:, top])
        hr_k = hr[sel]
        hr_bar = float(np.average(hr_k, weights=pmax[sel]))
        # implied fuel $/MMBtu per row-hour from the assembled mc and heat rate
        # (mc = hr x fuel + adders); hold hr at hr_bar and keep the adder.
        mc_k = mc[sel][:, top]
        adder = mc_k - hr_k[:, None] * _fuel_of(fuel_prices, sel, top)
        mc_flat = hr_bar * _fuel_of(fuel_prices, sel, top) + adder
        pl = plant[sel]
        def _spread(mat):
            vals, wts = [], []
            for p in np.unique(pl):
                m = pl == p
                j = np.argmin(mat[m], axis=0)
                vals.append(mat[m][j, np.arange(len(top))])
                wts.append(cap[m].sum(axis=0))
            v = np.concatenate(vals); w = np.concatenate(wts)
            ok = np.isfinite(v) & (w > 0)
            return _wq(v[ok], w[ok], 90) - _wq(v[ok], w[ok], 10)
        out["X3_ct_heat_rate_decomposition"] = {
            "hr_capwtd_mean": hr_bar,
            "hr_p10": float(np.percentile(hr_k, 10)),
            "hr_p90": float(np.percentile(hr_k, 90)),
            "p90_minus_p10_actual": float(_spread(mc_k)),
            "p90_minus_p10_flat_heat_rate": float(_spread(mc_flat)),
        }
    return out


def _fuel_of(fuel_prices, sel, top) -> np.ndarray:
    """Return the (n_sel, len(top)) delivered fuel price used by assemble_mc."""
    fp = np.asarray(fuel_prices, dtype=np.float64)
    if fp.ndim == 1:
        fp = np.broadcast_to(fp[:, None], (fp.shape[0], 8760))
    return fp[sel][:, top]


def main() -> None:
    res = {"bundle": BUNDLE.name, "years": {}}
    for y in YEARS:
        print(f"\n===== {y} =====", flush=True)
        r = run_year(y)
        res["years"][str(y)] = r
        for k, q in r["classes"].items():
            print(f"  {k:<12} n={q['n_plants']:>3}  p10 {q['p10']:>7.2f}  "
                  f"p50 {q['p50']:>7.2f}  p90 {q['p90']:>7.2f}  "
                  f"p90-p10 {q['p90_minus_p10']:>7.2f}")
        d = r.get("X3_ct_heat_rate_decomposition")
        if d:
            print(f"  X-3 CT hr p10/mean/p90 = {d['hr_p10']:.2f}/"
                  f"{d['hr_capwtd_mean']:.2f}/{d['hr_p90']:.2f} | "
                  f"p90-p10 actual {d['p90_minus_p10_actual']:.2f} -> "
                  f"flat-hr {d['p90_minus_p10_flat_heat_rate']:.2f}")
    OUT.write_text(json.dumps(res, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
