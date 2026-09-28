"""NYISO-NEXT-9 phase 0 (ZERO LP): the always-on 900 MW ``HQ_hydro`` firm-import floor.

Rule-17 ``[R-FLOOR-WINDOW]`` question routed by NYISO-NEXT-8 (PRECOMMIT sec. 3).
Reads only committed artifacts: the keeper's hourly sidecars
(``results/calibration/nyisonext8_{span,2021}/hourly``), the measured NYISO
interface flows and DA LMP through ``derive_nyiso_import_tranches`` (the same
loaders the ladder derivation uses, HQ duplicate removed), and the ladder in
``interchange/spec.py``.  Per year it reports:

1. the floor's binding footprint on the keeper (hours at exactly the floor,
   the upper bound on MWh it forces, and the model/actual price in those hours);
2. the measured total net import and the measured HQ seam in the same hours;
3. the measured hours below the floor (the driver-data test rule 17 asks).

Output: ``results/calibration/_nyisonext9_phase0.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

import derive_nyiso_import_tranches as dnit  # noqa: E402
from market_sim.model.interchange.spec import (  # noqa: E402
    IMPORT_TRANCHES_BY_YEAR,
    NYISO_FIRM_IMPORT_FLOOR_FRAC,
)

CAL = REPO / "results" / "calibration"
OUT = CAL / "_nyisonext9_phase0.json"
YEARS = (2021, 2022, 2023, 2024, 2025)
TOL_MW = 0.5  # numerical tolerance for "at the floor" (solver output is float32)


def _bundle(year: int) -> Path:
    """Return the keeper bundle holding ``year``."""
    return CAL / ("nyisonext8_2021" if year == 2021 else "nyisonext8_span")


def _model(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (hourly model import MW, hourly load-weighted model price)."""
    h = _bundle(year) / "hourly"
    c = pd.read_parquet(h / f"class_hourly_{year}.parquet")
    imp = c[c.klass == "import"].sort_values("hour").mw.to_numpy(dtype=float)
    s = pd.read_parquet(h / f"system_{year}.parquet")
    s["pd"] = s.price * s.demand
    g = s.groupby("hour")[["pd", "demand"]].sum().sort_index()
    return imp, (g.pd / g.demand).to_numpy(dtype=float)


def main() -> None:
    """Compute the per-year footprint and write the JSON record."""
    firm = next(c for n, c, _ in IMPORT_TRANCHES_BY_YEAR["NYISO"][YEARS[0]] if n == "HQ_hydro")
    floor_mw = NYISO_FIRM_IMPORT_FLOOR_FRAC["HQ_hydro"] * firm
    out: dict = {"floor_mw": floor_mw, "years": {}}
    for y in YEARS:
        imp, p_model = _model(y)
        net = dnit.load_net_import(y)
        da = dnit.load_da_lmp(y)
        hq_rung = next(p for n, _, p in IMPORT_TRANCHES_BY_YEAR["NYISO"][y] if n == "HQ_hydro")
        bind = imp <= floor_mw + TOL_MW
        below = net < floor_mw
        ok = np.isfinite(net) & np.isfinite(da)
        b = bind & ok
        rec = {
            "hq_rung_price": hq_rung,
            "keeper_hours_at_floor": int(bind.sum()),
            "forced_twh_upper_bound": round(float(floor_mw * bind.sum()) / 1e6, 4),
            "keeper_import_twh": round(float(imp.sum()) / 1e6, 3),
            "measured_net_import_twh": round(float(np.nansum(net)) / 1e6, 3),
            "measured_hours_below_floor": int(below.sum()),
            "measured_share_below_floor_pct": round(100 * below.mean(), 2),
            "measured_min_mw": round(float(np.nanmin(net)), 0),
        }
        if b.any():
            rec.update({
                "bind_measured_net_import_mean_mw": round(float(net[b].mean()), 0),
                "bind_measured_below_floor_hours": int((b & below).sum()),
                "bind_measured_shortfall_twh": round(float(np.clip(floor_mw - net[b], 0, None).sum()) / 1e6, 4),
                "bind_model_price_mean": round(float(p_model[b].mean()), 2),
                "bind_actual_da_mean": round(float(da[b].mean()), 2),
                "bind_hours_model_below_hq_rung": int((p_model[b] < hq_rung - 1e-6).sum()),
                "bind_hours_share_pct": round(100 * b.mean(), 2),
                "annual_mean_effect_if_bind_gap_closed": round(float((da[b] - p_model[b]).sum()) / 8760, 3),
            })
        # measured below-floor hours: what did the keeper do there
        mb = below & ok
        if mb.any():
            rec.update({
                "measured_below_keeper_import_mean_mw": round(float(imp[mb].mean()), 0),
                "measured_below_actual_da_mean": round(float(da[mb].mean()), 2),
                "measured_below_model_price_mean": round(float(p_model[mb].mean()), 2),
            })
        rec["model_price_mean"] = round(float(p_model.mean()), 2)
        rec["actual_da_mean"] = round(float(np.nanmean(da)), 2)
        out["years"][y] = rec
        print(y, json.dumps(rec))
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print("wrote", OUT.relative_to(REPO))


if __name__ == "__main__":
    main()
