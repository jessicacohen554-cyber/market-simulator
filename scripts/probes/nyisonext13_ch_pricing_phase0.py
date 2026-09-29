"""NYISO-NEXT-13 phase 0 (ZERO LP): what drives the NE AC node to its posted export bound.

The NE AC node (``nyiso_ne_ac_node``) clears its Q-Q bands on the spread
``Capital_Hudson price - Roseton DA`` (``derive_nyiso_ne_ac_ladder``). The bands were
fitted on the MEASURED spread (CAPITL DA - Roseton DA), so the node exports too much in
exactly the hours the keeper's Capital_Hudson price sits below the measured CAPITL DA
price. This probe decomposes that gap on the keeper's committed hourlies:

* ``gap_ch``  = model Capital_Hudson - measured CAPITL DA (the node's operand error);
* ``gap_uw``  = model Upstate_West - measured upstate DA (load-weighted WEST..MHK VL
  is not published per model zone; the simple mean of WEST/GENESE/CENTRL/NORTH/MHK VL
  is used and named as such);
* ``ce_model`` = model CH - model UW (Central-East congestion the LP prices);
* ``ce_meas``  = measured CAPITL - upstate mean (Central-East congestion the market priced).

``gap_ch = gap_uw + (ce_model - ce_meas)`` exactly, so the node's operand error splits into
an upstate LEVEL error and a Central-East SPREAD error. Reported on all hours and on the
hours the node sits at its posted export bound (implied from the model price via the
node's own bands, the NEXT-11 construction). Record: ``results/calibration/_nyisonext13_phase0.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO / "src", REPO, REPO / "scripts" / "data", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

import derive_nyiso_ne_ac_ladder as dne  # noqa: E402
from nyisonext11_ne_ac_node_phase0 import implied_flow  # noqa: E402

from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES  # noqa: E402

CAL = REPO / "results" / "calibration"
SNP = REPO / "data" / "raw" / "seam-neighbour-price"
OUT = CAL / "_nyisonext13_phase0.json"
H = dne.H
BUNDLE = {
    2021: "nyisonext12_2021",
    **{y: "nyisonext12_span" for y in range(2022, 2026)},
}
UPSTATE = ("WEST", "GENESE", "CENTRL", "NORTH", "MHK VL")
MODEL_TO_MEAS = {
    "Upstate_West": UPSTATE,
    "Capital_Hudson": ("CAPITL",),
    "Lower_Hudson": ("HUD VL", "MILLWD", "DUNWOD"),
    "NYC": ("N.Y.C.",),
    "Long_Island": ("LONGIL",),
}


def meas_da(year: int) -> pd.DataFrame:
    """Measured NYISO DA zonal LBMP on the local hour-of-year clock (dne's convention)."""
    with gzip.open(SNP / "nyiso" / f"NYISO_dam_proxy_lbmp_{year}.csv.gz", "rt") as f:
        d = pd.read_csv(f)
    out = {}
    for name, g in d.groupby("name"):
        local = pd.to_datetime(g["time_stamp"], format="%m/%d/%Y %H:%M")
        out[name] = dne._on_clock(dne._hoy(local), g["lbmp"].to_numpy(dtype=float))
    return pd.DataFrame(out)


def model_prices(year: int) -> pd.DataFrame:
    """Keeper P1 zonal price, hour-indexed."""
    s = pd.read_parquet(CAL / BUNDLE[year] / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return s.pivot_table(index="hour", columns="zone", values="price").reindex(range(H))


def _stats(x: np.ndarray, m: np.ndarray) -> dict:
    v = x[m & np.isfinite(x)]
    if v.size == 0:
        return {"n": 0}
    return {
        "n": int(v.size),
        "mean": round(float(v.mean()), 2),
        "p10": round(float(np.percentile(v, 10)), 2),
        "p50": round(float(np.percentile(v, 50)), 2),
        "p90": round(float(np.percentile(v, 90)), 2),
    }


def year_block(year: int) -> dict:
    """Decomposition for one year."""
    d = dne.derive_year(year)
    ros = dne.load_roseton_da(year)
    meas, mod = meas_da(year), model_prices(year)
    up_meas = meas[list(UPSTATE)].mean(axis=1).to_numpy()
    ch_meas = meas["CAPITL"].to_numpy()
    ch, uw = mod["Capital_Hudson"].to_numpy(), mod["Upstate_West"].to_numpy()

    L_i, L_e = d["node"]["import_mw"], d["node"]["export_mw"]
    ci = np.nan_to_num(d["limit_import"], nan=L_i)
    ce = np.nan_to_num(d["limit_export"], nan=L_e)
    ros_f = np.nan_to_num(ros, nan=np.nanmean(ros))
    q_mod = implied_flow(
        ch - ros_f, d["node"]["import"], d["node"]["export"],
        L_i / SEAM_FLOW_TRANCHES, L_e / SEAM_FLOW_TRANCHES, ci, ce,
    )  # fmt: skip
    q_meas_sp = implied_flow(
        np.nan_to_num(ch_meas - ros_f), d["node"]["import"], d["node"]["export"],
        L_i / SEAM_FLOW_TRANCHES, L_e / SEAM_FLOW_TRANCHES, ci, ce,
    )  # fmt: skip
    at_exp = -q_mod >= ce - 1
    alln = np.ones(H, bool)

    gap_ch, gap_uw = ch - ch_meas, uw - up_meas
    ce_mod, ce_meas = ch - uw, ch_meas - up_meas
    ce_bind_mod = np.abs(ce_mod) > 0.5
    zone_gap = {
        z: {
            "all": _stats(
                mod[z].to_numpy() - meas[list(c)].mean(axis=1).to_numpy(), alln
            ),
            "at_export_bound": _stats(
                mod[z].to_numpy() - meas[list(c)].mean(axis=1).to_numpy(), at_exp
            ),
        }
        for z, c in MODEL_TO_MEAS.items()
    }
    month = (np.arange(H) // 24 * 24 // 730).clip(0, 11)  # approx month of hour
    hod = np.arange(H) % 24
    return {
        "node_twh_implied_model_price": round(float(q_mod.sum()) / 1e6, 3),
        "node_twh_implied_measured_price": round(float(q_meas_sp.sum()) / 1e6, 3),
        "node_twh_measured": round(float(np.nansum(d["flow"])) / 1e6, 3),
        "hours_at_export_bound_implied": int(at_exp.sum()),
        "hours_at_export_bound_measured_price": int((-q_meas_sp >= ce - 1).sum()),
        "gap_ch": {
            "all": _stats(gap_ch, alln),
            "at_export_bound": _stats(gap_ch, at_exp),
        },
        "gap_upstate_level": {
            "all": _stats(gap_uw, alln),
            "at_export_bound": _stats(gap_uw, at_exp),
        },
        "central_east_model": {
            "all": _stats(ce_mod, alln),
            "at_export_bound": _stats(ce_mod, at_exp),
            "hours_binding": int(ce_bind_mod.sum()),
        },
        "central_east_measured": {
            "all": _stats(ce_meas, alln),
            "at_export_bound": _stats(ce_meas, at_exp),
        },
        "model_ch_at_export_bound": _stats(ch, at_exp),
        "measured_capitl_at_export_bound": _stats(ch_meas, at_exp),
        "roseton_at_export_bound": _stats(ros, at_exp),
        "zone_gap_model_minus_measured_da": zone_gap,
        "export_bound_hours_by_month": np.bincount(
            month[at_exp], minlength=12
        ).tolist(),
        "export_bound_hours_by_hod": np.bincount(hod[at_exp], minlength=24).tolist(),
    }


def main() -> None:
    """Run every year, write the record, print a compact table."""
    res = {str(y): year_block(y) for y in range(2021, 2026)}
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    for y, b in res.items():
        print(
            y,
            "nodeTWh mod/measpx/meas",
            b["node_twh_implied_model_price"],
            b["node_twh_implied_measured_price"],
            b["node_twh_measured"],
            "| h@exp mod/measpx",
            b["hours_at_export_bound_implied"],
            b["hours_at_export_bound_measured_price"],
        )
        for k in (
            "gap_ch",
            "gap_upstate_level",
            "central_east_model",
            "central_east_measured",
        ):
            print(
                "   ",
                k,
                "all",
                b[k]["all"].get("mean"),
                "@exp",
                b[k]["at_export_bound"],
            )
        print("    CE binding h (model)", b["central_east_model"]["hours_binding"])
        print(
            "    zone gap mean all:",
            {
                z: v["all"].get("mean")
                for z, v in b["zone_gap_model_minus_measured_da"].items()
            },
        )
        print("    @exp by month", b["export_bound_hours_by_month"])


if __name__ == "__main__":
    main()
