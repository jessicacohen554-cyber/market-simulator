"""caiso-245 — queue item B: what carries the December price slab? ZERO LP.

caiso-232 found Dec-2025 over-priced in every hour (+7.4…+13.5 $/MWh) and
attributed it to the IMPORT_TRANCHES residual; caiso-244 §3.7 showed December
import VOLUME matches the measured record within ±420 MW, so volume is not
the carrier. This probe splits every December hour of 2023–2025 by WHAT SETS
the model's landing-zone price, using the caiso-244 dual-merit
reconstruction (imported from ``_caiso244_import_level_anatomy``):

  * IMPORT-MARGINAL: an import row is marginal at its WECC node AND the
    corridor link is unbound, so the landing zone's price IS that import
    offer (raw Palo Verde hub for the clean-depth rows, Malin + wheel + carbon
    for PNW_midC, hub + wheel + CARB for the DSW spot rows);
  * DOMESTIC-MARGINAL: otherwise.

For each bucket: hours, model load-weighted price, and — where the marginal
import offer is a measured hub price — the offer's decomposition (hub vs
adders). Against it, the measured CAISO RT monthly load-weighted price from
the committed bench (``frontend/data/backcast/bench/CAISO/<year>.json.gz``,
``avgLMP.rt_lw_mon``) — a MONTHLY actual, so the bucket comparison is a
decomposition of the model's December mean, not an hourly residual (hourly
actuals are not in the committed sidecars).

Writes ``results/calibration/_caiso245_december_carrier.json``. Nothing armed.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso245_december_carrier.py
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "_caiso244_import_level_anatomy",
    REPO / "scripts/probes/_caiso244_import_level_anatomy.py",
)
C244 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C244)

OUT = REPO / "results/calibration/_caiso245_december_carrier.json"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
MONTH = C244.MONTH_OF_HOUR
CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")


def system_lw_price(price: pd.DataFrame, demand: pd.DataFrame) -> np.ndarray:
    """ISO load-weighted hourly price over the CAISO load zones."""
    p = price.loc[list(CA_ZONES)].to_numpy(float)
    d = demand.loc[list(CA_ZONES)].to_numpy(float)
    return (p * d).sum(axis=0) / np.maximum(d.sum(axis=0), 1e-9)


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-245 (queue item B, zero LP)",
            "bundle": "results/calibration/caiso243_b1_f923_fallback_guard",
            "instrument": "_caiso244_import_level_anatomy reconstruct() on the committed P1 duals",
            "actual_source": "bench avgLMP.rt_lw_mon (monthly RT load-weighted actual)",
        },
        "years": {},
    }
    for y in YEARS:
        fl = C244.rebuild(y)
        price, klass_import, _bal = C244.sidecars(y)
        s = pd.read_parquet(C244.BUNDLE / "hourly" / f"system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        demand = s.pivot(index="zone", columns="hour", values="demand").reindex(columns=range(HOURS))
        recon, x, state, lam, x_lo, x_hi = C244.reconstruct(fl, price, klass_import)
        rows = fl["rows"]
        # per hour: is any import row marginal with its link unbound? which row?
        marg_unbound = np.zeros(HOURS, dtype=bool)
        marg_row = np.full(HOURS, "", dtype=object)
        offer_at_marg = np.full(HOURS, np.nan)
        for i, row in enumerate(rows):
            if row["is_export"]:
                continue
            land = C244.CORRIDOR_LANDING[row["zone"]]
            lam_l = price.loc[land].to_numpy(float)
            mi = (state[i] == 0) & (np.abs(lam[i] - lam_l) <= C244.TOL)
            newly = mi & ~marg_unbound
            marg_unbound |= mi
            marg_row[newly] = row["name"]
            offer_at_marg[newly] = fl["mc"][row["r"]][newly]
        lw = system_lw_price(price, demand)
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["avgLMP"]
        rec: dict = {"months": {}}
        for m in range(1, 13):
            hm = MONTH == m
            imp = hm & marg_unbound
            dom = hm & ~marg_unbound
            month_rec = {
                "model_lw_mean": round(float(lw[hm].mean()), 2),
                "actual_rt_lw_mean": bench["rt_lw_mon"][m - 1],
                "actual_da_lw_mean": bench["da_lw_mon"][m - 1],
                "hours_import_marginal_unbound": int(imp.sum()),
                "share_import_marginal": round(float(imp.mean() / max(hm.mean(), 1e-9)), 3),
                "model_lw_mean_import_marginal_hours": round(float(lw[imp].mean()), 2) if imp.any() else None,
                "model_lw_mean_domestic_marginal_hours": round(float(lw[dom].mean()), 2) if dom.any() else None,
                "marginal_import_rows": pd.Series(marg_row[imp]).value_counts().to_dict() if imp.any() else {},
                "marginal_import_offer_mean": round(float(np.nanmean(offer_at_marg[imp])), 2) if imp.any() else None,
            }
            rec["months"][m] = month_rec
        dec = rec["months"][12]
        rec["december"] = {
            **dec,
            "model_minus_actual_rt": round(dec["model_lw_mean"] - dec["actual_rt_lw_mean"], 2),
            "hod_import_marginal_share": [
                round(float((marg_unbound & (MONTH == 12) & (C244.HOD == h)).sum() / 31.0), 3) for h in range(24)
            ],
            "hod_model_lw_mean": [round(float(lw[(MONTH == 12) & (C244.HOD == h)].mean()), 2) for h in range(24)],
        }
        out["years"][y] = rec
        print(
            f"{y} Dec: model lw {dec['model_lw_mean']} vs actual RT {dec['actual_rt_lw_mean']} (DA {dec['actual_da_lw_mean']}); "
            f"import-marginal share {dec['share_import_marginal']:.1%} ({dec['hours_import_marginal_unbound']} h), "
            f"model lw in import-marginal hours {dec['model_lw_mean_import_marginal_hours']} vs domestic hours {dec['model_lw_mean_domestic_marginal_hours']}; "
            f"rows {dec['marginal_import_rows']}; marginal import offer mean {dec['marginal_import_offer_mean']}"
        )
        print("   annual import-marginal share by month:", [rec["months"][m]["share_import_marginal"] for m in range(1, 13)])
        print("   model-actual RT by month:", [round(rec["months"][m]["model_lw_mean"] - rec["months"][m]["actual_rt_lw_mean"], 1) for m in range(1, 13)])
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
