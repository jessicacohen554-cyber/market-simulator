"""SPP-74 part B — marginal fuel (b) and the model's own monthly gas price (c).

Pre-registered in ``docs/handoffs/PRECOMMIT-spp-74-price-body-2026-09-23.md`` §3(b)/(c).
Reuses SPP-70's validated merit-order reconstruction (``_spp70_meritorder_counterfactual.clear``
over ``reconstruct_bundle_fleet``), re-pointed at the hydro-5 rung. ONE interpreter per year
(trap (b)): run once per ``--year``.

Per hour: the marginal thermal row's class / band / mc / heat rate / fuel price at the served
thermal ``Q_mod`` (committed class_hourly), and the mc on the SAME stack at the measured
EIA-930 thermal ``Q_meas`` (COL + NG, trap-(f) guarded). Per month: capacity-weighted delivered
gas and coal fuel price over the LP's own rows.

Usage: ``uv run python scripts/probes/_spp74_marginal_fuel.py --year 2020 --out <json>``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp70_meritorder_counterfactual import (  # noqa: E402
    THERMAL_PREFIXES,
    _bandkey,
)
from scripts.probes._spp72_demand_tightness import (  # noqa: E402
    CST_OFFSET_H,
    model_clock_index,
)
from scripts.probes._spp74_body_decomposition import (  # noqa: E402
    RUNG,
    fueltype,
    hour_types,
    model_price_demand,
)


def main() -> int:
    """One year of part B; writes one JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    y = args.year
    bundle = REPO / "results/calibration" / RUNG

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
    from scripts.run_calibration_full import _coal_supply_class, _tranche_band

    state, _ = reconstruct_bundle_fleet(bundle, y, verbose=False)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], float)
    T = mc.shape[1]
    fuel = np.asarray(state["fuel_prices"], float)
    if fuel.ndim == 1:
        fuel = fuel[:, None]
    fuel = np.broadcast_to(fuel, mc.shape) if fuel.shape[1] in (1, T) else fuel
    pmax = np.asarray(fa.pmax, float)
    hr = np.asarray(fa.heat_rate, float)
    avail = np.asarray(fa.availability, float)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], mc.shape)
    groups, codes = fa.plant_group, np.asarray(fa.plant_code)
    klass = np.array(
        [
            _coal_supply_class(int(codes[i]))
            if str(groups[i]) == "COAL"
            else str(groups[i])
            for i in range(len(fa.unit_ids))
        ],
        dtype=object,
    )
    band = np.array(
        [_bandkey(_tranche_band(str(u))) for u in fa.unit_ids], dtype=object
    )
    th = np.array([str(k).startswith(THERMAL_PREFIXES) for k in klass])
    mc, cap, fuelT, hrT = mc[th], (pmax[:, None] * avail)[th], fuel[th], hr[th]
    kl, bd = klass[th], band[th]
    is_gas = np.array(
        [str(k).startswith(("CC_", "CT_", "ST_GAS", "ST_CHP")) for k in kl]
    )
    is_coal = np.array([str(k).startswith("COAL") for k in kl])

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{y}.parquet")
    ch = ch[
        (ch["pass"] == "P1") & ch["klass"].astype(str).str.startswith(THERMAL_PREFIXES)
    ]
    served = ch.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy()
    ft = pd.read_parquet(RAW_DATA_DIR / "SWPP_fueltype.parquet")
    q_meas = fueltype(ft, "COL", y) + fueltype(ft, "NG", y)

    price, _ = model_price_demand(y)
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    a = lmp[lmp["year"] == y].sort_values("hour")["rt"].to_numpy(float)
    lab = hour_types(a)
    clock = model_clock_index(y).tz_convert(None) - pd.Timedelta(hours=CST_OFFSET_H)
    month = clock.month.to_numpy() - 1

    marg_i = np.empty(T, int)
    mc_mod = np.empty(T)
    mc_meas = np.empty(T)
    for t in range(T):
        o = np.argsort(mc[:, t], kind="stable")
        c = np.cumsum(cap[o, t])
        i = min(int(np.searchsorted(c, served[t])), len(o) - 1)
        j = min(int(np.searchsorted(c, q_meas[t])), len(o) - 1)
        marg_i[t], mc_mod[t], mc_meas[t] = o[i], mc[o[i], t], mc[o[j], t]

    ok = np.isfinite(price)
    val = {
        "r": float(np.corrcoef(price[ok], mc_mod[ok])[0, 1]),
        "mean_err": float(np.mean(mc_mod[ok] - price[ok])),
        "mae": float(np.mean(np.abs(mc_mod[ok] - price[ok]))),
    }
    mcls = np.array([str(kl[i]) for i in marg_i], dtype=object)
    mfam = np.where(
        np.char.startswith(mcls.astype(str), "COAL"),
        "coal",
        np.where(np.char.startswith(mcls.astype(str), "CT_"), "CT", "gas_other"),
    )
    capw = cap.mean(axis=1)
    months = []
    for m in range(12):
        mm = month == m
        mid = mm & np.isin(lab, ["MID1", "MID2"]) & np.isfinite(a)
        high = mm & (lab == "HIGH") & np.isfinite(a)
        low = mm & np.isin(lab, ["NEG", "LOW"]) & np.isfinite(a)
        fcols = np.flatnonzero(mm) if fuelT.shape[1] == T else [0]
        gas_px = float(
            np.average(fuelT[is_gas][:, fcols].mean(axis=1), weights=capw[is_gas])
        )
        coal_px = float(
            np.average(fuelT[is_coal][:, fcols].mean(axis=1), weights=capw[is_coal])
        )

        def fam_share(mask):
            n = max(int(mask.sum()), 1)
            return {
                f: float((mfam[mask] == f).sum() / n)
                for f in ("coal", "gas_other", "CT")
            }

        def hr_marg_gas(mask):
            sel = [marg_i[t] for t in np.flatnonzero(mask) if is_gas[marg_i[t]]]
            return float(np.mean(hrT[sel])) if sel else None

        months.append(
            {
                "month": m + 1,
                "gas_px_model": gas_px,
                "coal_px_model": coal_px,
                "served_gw": float(served[mm].mean() / 1e3),
                "q_meas_gw": float(q_meas[mm].mean() / 1e3),
                "mid": {
                    "n": int(mid.sum()),
                    "lp_price": float(price[mid].mean()),
                    "rt": float(a[mid].mean()),
                    "mc_Qmod": float(mc_mod[mid].mean()),
                    "mc_Qmeas": float(mc_meas[mid].mean()),
                    "quantity_term": float((mc_mod - mc_meas)[mid].mean()),
                    "level_term": float((mc_meas - a)[mid].mean()),
                    "marg_family": fam_share(mid),
                    "hr_marg_gas": hr_marg_gas(mid),
                },
                "high": {
                    "n": int(high.sum()),
                    "lp_price": float(price[high].mean()),
                    "rt": float(a[high].mean()),
                    "mc_Qmod": float(mc_mod[high].mean()),
                    "mc_Qmeas": float(mc_meas[high].mean()),
                    "marg_family": fam_share(high),
                    "hr_marg_gas": hr_marg_gas(high),
                },
                "low": {
                    "n": int(low.sum()),
                    "lp_price": float(price[low].mean()),
                    "rt": float(a[low].mean()),
                    "marg_family": fam_share(low),
                },
                "marg_family_all": fam_share(mm),
            }
        )
    # the marginal (class, band) census in ordinary hours, whole year
    mid_all = np.isin(lab, ["MID1", "MID2"]) & np.isfinite(a)
    cen = pd.Series([f"{kl[i]}/{bd[i]}" for i in marg_i[mid_all]]).value_counts(
        normalize=True
    )
    # capacity-weighted annual mc by class (the stack's level)
    cls_mc = {}
    for k in sorted(set(kl)):
        s = kl == k
        cls_mc[str(k)] = {
            "gw": float(capw[s].sum() / 1e3),
            "mc": float(np.average(mc[s].mean(axis=1), weights=capw[s])),
            "hr": float(np.average(hrT[s], weights=capw[s])),
            "fuel": float(np.average(fuelT[s].mean(axis=1), weights=capw[s])),
        }
    out = {
        "year": y,
        "validation": val,
        "months": months,
        "mid_census": cen.head(10).to_dict(),
        "class_mc": cls_mc,
        "fuel_cols": int(fuelT.shape[1]),
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(y, json.dumps(val))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
