"""Close-out CAISO w4, phase 0 (ZERO LP): where and why the 2020 CC_REGULAR over-run sits on the w3 leg.

Control: the w3 probe 2020 leg ``results/calibration/closeout_caiso_w3_a1_2020``
(keeper + R-63 arm + w3 L1/L2). Reads only that leg's committed P1 sidecars
(``unit_marginal``, ``network``, ``system``, ``class_hourly``), its floors
(``floors/2020_P1.npz``), the shared EIA-923 / CAMPD frames the span bundle pins,
and the EIA-930 corridor interchange (``corridor_net_import``).

Per month (and per hod band in the object months Jun-Sep + Dec):

* CC_REGULAR model - actual (EIA-923 levelled on CEMS), DSW / PNW net import
  model - EIA-930, other gas model - actual;
* in the CC over-run hours with a DSW shortfall (measured - model > 300 MW):
  what limits the DSW clean rung that is armed in that hour (corridor binding /
  rung at capability / rung priced above lambda / no rung armed) and the offer
  gap (rung mc - lambda_SP15);
* CC energy at binding floors (mw <= min_gen + 1 MW, min_gen > 0), by mechanism;
* the price operands: lambda_SP15, the clean-rung offer (= the formula hub),
  the marginal CC offer.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w4_2020_hours.py [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts", str(Path(__file__).resolve().parent)]

import _closeout_caiso_w4_cc_object as cco  # noqa: E402  (scripts/probes on path below)
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
YEAR = 2020
LEG = ROOT / f"results/calibration/closeout_caiso_w3_a1_{YEAR}"
T = 8760
MONTH = cco.MONTH
HOD = np.arange(T) % 24
OBJ_MONTHS = (6, 7, 8, 9, 12)
BANDS = {"00-05": (0, 5), "06-16": (6, 16), "17-21": (17, 21), "22-23": (22, 23)}
CLEAN = (
    "DSW_surplus_clean",
    "DSW_overnight_clean",
    "DSW_daytime_clean",
    "DSW_lateevening_clean",
)
SHORT_MW = 300.0
BIND_TOL = 1.0


def _link(net: pd.DataFrame, name: str) -> np.ndarray:
    s = net[(net["pass"] == "P1") & (net.name.astype(str) == name)]
    return s.set_index("hour").mw.reindex(range(T)).fillna(0.0).to_numpy(float)


def _actual_classes(e923, campd):
    """Hourly actual CC_REGULAR and other-gas (EIA-923 levelled on CEMS)."""
    ey = e923[e923.year == YEAR]
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    cy = campd[campd.year == YEAR]
    cmap = {int(p): cco._dense(g, "net_mw") for p, g in cy.groupby("plant_id")}
    out = {}
    for k in ("CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "CC_CHP"):
        e = ey[ey.klass == k].groupby("plant_id")[mcols].sum()
        a = np.zeros(T)
        for p, r in e.iterrows():
            a += cco._levelled(cmap.get(int(p), np.zeros(T)), r.to_numpy(float))
        out[k] = a
    return out


def main() -> None:
    """Write the 2020 object table."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(ROOT / "docs/records/caiso/closeout-caiso-w4/_2020_hours_w3.json"),
    )
    a = ap.parse_args()
    cco.BUNDLE = ROOT / "results/calibration/closeout_caiso_w3_a1_span"
    act = _actual_classes(cco._shared("eia923"), cco._shared("campd"))

    ch = pd.read_parquet(LEG / f"hourly/class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    mod = {str(k): cco._dense(g, "mw") for k, g in ch.groupby("klass", observed=True)}
    net = pd.read_parquet(LEG / f"hourly/network_{YEAR}.parquet")
    dsw_m = _link(net, "WECC_DSW>SP15_rest")
    pnw_m = _link(net, "WECC_PNW>NP15")
    dsw_bind = (
        np.abs(
            net[(net["pass"] == "P1") & (net.name.astype(str) == "WECC_DSW>SP15_rest")]
            .set_index("hour")
            .dual.reindex(range(T))
            .fillna(0)
            .to_numpy()
        )
        > BIND_TOL
    )
    meas = corridor_net_import(years=(YEAR,)).loc[YEAR]
    dsw_a = np.nan_to_num(meas["WECC_DSW"].to_numpy(float)[:T])
    pnw_a = np.nan_to_num(meas["WECC_PNW"].to_numpy(float)[:T])

    sysh = pd.read_parquet(LEG / f"hourly/system_{YEAR}.parquet")
    sysh = sysh[sysh["pass"] == "P1"]
    lam = (
        sysh[sysh.zone == "SP15_rest"]
        .set_index("hour")
        .price.reindex(range(T))
        .to_numpy()
    )

    um = pd.read_parquet(
        LEG / f"hourly/unit_marginal_{YEAR}.parquet",
        columns=[
            "unit_id",
            "zone",
            "plant_group",
            "hour",
            "mw",
            "cap_mw",
            "mc",
            "marginal",
        ],
    )
    um["unit_id"] = um.unit_id.astype(str)
    dsw = um[um.zone.astype(str) == "WECC_DSW"].copy()
    dsw["n"] = dsw.unit_id.str[len("WECC_DSW_") :]
    wide = {
        c: dsw[dsw.n.isin(CLEAN)]
        .pivot_table(index="hour", columns="n", values=c, aggfunc="mean")
        .reindex(range(T))
        for c in ("mw", "cap_mw", "mc")
    }
    # the armed rung per hour = the clean rung with capability > 1 MW (windows are disjoint)
    armed_name = np.full(T, "", dtype=object)
    r_mw = np.zeros(T)
    r_cap = np.zeros(T)
    r_mc = np.full(T, np.nan)
    for n in CLEAN:
        if n not in wide["cap_mw"].columns:
            continue
        cap = wide["cap_mw"][n].fillna(0).to_numpy()
        on = cap > 1.0
        armed_name[on] = n
        r_mw[on] = wide["mw"][n].fillna(0).to_numpy()[on]
        r_cap[on] = cap[on]
        r_mc[on] = wide["mc"][n].to_numpy()[on]

    cc = um[um.plant_group.astype(str) == "CC_REGULAR"]
    cc_marg = (
        cc[cc.marginal == 1].groupby("hour").mc.median().reindex(range(T)).to_numpy()
    )

    fl = np.load(LEG / f"floors/{YEAR}_P1.npz", allow_pickle=True)
    fl_ids = np.asarray(fl["unit_ids"]).astype(str)
    fl_grp = np.asarray(fl["plant_group"]).astype(str)
    mw_w = um.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
    cc_rows = np.where(fl_grp == "CC_REGULAR")[0]
    mg = fl["min_gen"][cc_rows]
    mech = fl["mechanism"][cc_rows]
    mw_cc = (
        mw_w.reindex([fl_ids[i] for i in cc_rows])
        .reindex(columns=range(T))
        .fillna(0)
        .to_numpy()
    )
    at_floor = (mg > 0) & (mw_cc <= mg + 1.0)
    floor_e = np.where(at_floor, mw_cc, 0.0)

    cc_d = mod.get("CC_REGULAR", np.zeros(T)) - act["CC_REGULAR"]
    og_d = sum(
        mod.get(k, np.zeros(T)) - act[k] for k in ("CT_CHP", "CT_PEAKER", "ST_GAS")
    )
    dsw_d = dsw_m - dsw_a
    pnw_d = pnw_m - pnw_a
    short = (dsw_a - dsw_m) > SHORT_MW

    def twh(x, k):
        return round(float(x[k].sum() / 1e6), 3)

    out = {"by_month": {}, "object_by_band": {}, "object_short_hours": {}}
    for m in range(1, 13):
        k = MONTH == m
        out["by_month"][m] = {
            "cc_d": twh(cc_d, k),
            "dsw_d": twh(dsw_d, k),
            "pnw_d": twh(pnw_d, k),
            "other_gas_d": twh(og_d, k),
            "cc_floor_twh": round(float(floor_e[:, k].sum() / 1e6), 3),
            "lambda_sp15": round(float(np.nanmean(lam[k])), 2),
            "rung_mc_mean": round(float(np.nanmean(r_mc[k])), 2)
            if np.isfinite(r_mc[k]).any()
            else None,
            "cc_marginal_mc_median": round(float(np.nanmedian(cc_marg[k])), 2)
            if np.isfinite(cc_marg[k]).any()
            else None,
        }
    obj = np.isin(MONTH, OBJ_MONTHS)
    for b, (h0, h1) in BANDS.items():
        k = obj & (HOD >= h0) & (HOD <= h1)
        out["object_by_band"][b] = {
            "cc_d": twh(cc_d, k),
            "dsw_d": twh(dsw_d, k),
            "pnw_d": twh(pnw_d, k),
            "other_gas_d": twh(og_d, k),
        }
    over = cc_d > 0
    for label, k0 in (("object_months", obj), ("all_year", np.ones(T, bool))):
        k = k0 & over & short
        sh = np.where(k, dsw_a - dsw_m, 0.0)
        bind = k & dsw_bind
        none = k & ~dsw_bind & (armed_name == "")
        atcap = k & ~dsw_bind & (armed_name != "") & (r_mw >= r_cap - 1.0)
        priced = k & ~dsw_bind & (armed_name != "") & (r_mw < r_cap - 1.0)
        gap = (r_mc - lam)[priced]
        out["object_short_hours"][label] = {
            "hours": int(k.sum()),
            "shortfall_twh": round(float(sh.sum() / 1e6), 3),
            "corridor_binding_twh": round(float(sh[bind].sum() / 1e6), 3),
            "no_rung_armed_twh": round(float(sh[none].sum() / 1e6), 3),
            "rung_at_cap_twh": round(float(sh[atcap].sum() / 1e6), 3),
            "rung_priced_twh": round(float(sh[priced].sum() / 1e6), 3),
            "priced_gap_p25_p50_p75": [
                round(float(np.nanpercentile(gap, q)), 2) for q in (25, 50, 75)
            ]
            if gap.size
            else None,
            "priced_by_rung_twh": {
                n: round(float(sh[priced & (armed_name == n)].sum() / 1e6), 3)
                for n in CLEAN
            },
            "cc_floor_twh_in_these_hours": round(float(floor_e[:, k].sum() / 1e6), 3),
        }
    mech_names = {}
    for code in np.unique(mech[at_floor]):
        mech_names[str(code)] = round(
            float(floor_e[at_floor & (mech == code)].sum() / 1e6), 3
        )
    out["cc_floor_by_mechanism_twh"] = mech_names
    Path(a.out).write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
