"""Close-out CAISO w5, phase 0 (ZERO LP): per-unit model heat rate / VOM / offer vs CAMPD own-year operating heat rate.

Fleet-only rebuild of the w3 recipe (``replay_keeper.run_year_kwargs`` +
``derived_run_year_inputs`` + ``run_year(fleet_only=True)``, the sanctioned
zero-LP rebuild) for each requested year; per gas unit of CC_REGULAR /
CT_PEAKER / ST_GAS it records the LP heat rate, VOM, emission rate and the mean
P0 marginal cost, and per plant the CAMPD facility-level own-year operating
heat rate (sum heatInput / sum grossLoad over hours with grossLoad > 0, gross
basis) for comparison.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w5_fleet_hr.py --years 2020 2023 [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]

ROOT = Path(__file__).resolve().parents[2]
SPAN = ROOT / "results/calibration/closeout_caiso_w3_a1_span"
CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CT_CHP", "CC_CHP")


def campd_hr(year: int) -> pd.Series:
    """Plant own-year gross operating heat rate (MMBtu/MWh) from CAMPD facility-level hourly."""
    d = pd.read_parquet(
        ROOT / f"data/raw/campd-facility-level/CA_{year}.parquet",
        columns=["facilityId", "grossLoad", "heatInput"],
    )
    d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce")
    d = d[(d.grossLoad > 0) & (d.heatInput > 0)]
    g = d.groupby("facilityId")[["grossLoad", "heatInput"]].sum()
    return (g.heatInput / g.grossLoad).rename("campd_hr"), g.grossLoad.rename(
        "campd_gwh"
    ) / 1e3


def fleet(year: int) -> pd.DataFrame:
    """Per-unit LP heat rate, VOM, emission rate, mean P0 mc for the w3 recipe."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((SPAN / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(SPAN, year))
    r = run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )
    fa = r["fleet_arrays"]
    mc = np.asarray(r["mc_base"])
    mc_mean = mc.mean(axis=1) if mc.ndim == 2 else mc
    df = pd.DataFrame(
        {
            "unit_id": np.asarray(fa.unit_ids).astype(str),
            "plant_code": np.asarray(fa.plant_code),
            "plant_group": np.asarray(fa.plant_group).astype(str),
            "pmax": np.asarray(fa.pmax, float),
            "heat_rate": np.asarray(fa.heat_rate, float),
            "vom": np.asarray(fa.vom, float),
            "emission_rate": np.asarray(fa.emission_rate, float),
            "mc_mean": mc_mean.astype(float),
        }
    )
    return df[df.plant_group.isin(CLASSES)]


def main() -> None:
    """Write the per-class comparison."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument(
        "--out",
        default=str(ROOT / "docs/records/caiso/closeout-caiso-w5/_fleet_hr.json"),
    )
    a = ap.parse_args()
    out = {}
    for y in a.years:
        f = fleet(y)
        hr, gwh = campd_hr(y)
        f["campd_hr"] = f.plant_code.map(hr)
        f["campd_gwh"] = f.plant_code.map(gwh)
        res = {}
        for k, g in f.groupby("plant_group"):
            w = g.pmax
            both = g[g.campd_hr.notna()]
            res[k] = {
                "units": int(len(g)),
                "mw": round(float(w.sum()), 0),
                "lp_hr_mw_weighted": round(float((g.heat_rate * w).sum() / w.sum()), 3),
                "lp_vom_mw_weighted": round(float((g.vom * w).sum() / w.sum()), 2),
                "mc_mean_mw_weighted": round(float((g.mc_mean * w).sum() / w.sum()), 2),
                "units_with_campd": int(len(both)),
                "lp_hr_on_campd_units": round(
                    float((both.heat_rate * both.pmax).sum() / both.pmax.sum()), 3
                )
                if len(both)
                else None,
                "campd_gross_hr_gen_weighted": round(
                    float(
                        (
                            both.drop_duplicates("plant_code").campd_hr
                            * both.drop_duplicates("plant_code").campd_gwh
                        ).sum()
                        / both.drop_duplicates("plant_code").campd_gwh.sum()
                    ),
                    3,
                )
                if len(both)
                else None,
            }
        out[str(y)] = res
        f.to_parquet(Path(a.out).with_name(f"_fleet_hr_{y}.parquet"))
        print(y, json.dumps(res, indent=1), flush=True)
        Path(a.out).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
