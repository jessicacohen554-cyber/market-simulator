"""R-CAISO-24 phase 0 (zero LP): what could a disaggregated battery fleet buy at the RT h18 peak?

Part A: the keeper's SP15_rest RT h18 residual split into the measured top-5 % (C3c tail) hours and
the body, beside model ``li_ion`` vs measured Outlook battery discharge at h16-21.

Part B (``--stack``): rebuild the keeper's offer surface with no LP and read the in-state gas
stack's price lift if the model's h18 battery discharge were moved to the measured level, body
hours only. Only gas responds in this bound (imports/hydro held), so it over-states the lift.

Run from the repo root:
    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso24_h18_bound.py [--stack]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import _rcaiso21_evening_phase0 as r21  # noqa: E402
import _rcaiso22_tail_phase0 as r22  # noqa: E402

BUNDLE = Path("results/calibration/rcaiso20_A_span/hourly")
ACT = Path("data/raw/storage-dispatch-actuals/CAISO_storage_hourly.parquet")
OUT = Path("results/calibration/_rcaiso24")
YEARS = (2022, 2023, 2024, 2025)
HOD = r21.HOD
TAIL_Q = 0.95  # R-CAISO-21 §2 split: each year's measured p95, same construction


def inputs(y: int) -> dict:
    """Model price/battery and measured RT price/battery on the fixed-PST 8760 clock."""
    s = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
    s = s[(s["pass"] == "P1") & (s.zone == "SP15_rest")].sort_values("hour")
    st = pd.read_parquet(BUNDLE / f"storage_{y}.parquet")
    st = st[(st["pass"] == "P1") & (st.tech == "li_ion")].sort_values("hour")
    a = pd.read_parquet(ACT)
    a = a[a.year == y].set_index("hour").reindex(range(r21.T))
    return {
        "p": s.price.to_numpy()[: r21.T],
        "m": r21.measured(y, "rtm")["SP15_rest"],
        "dis": st.discharge_mw.to_numpy()[: r21.T] - st.charge_mw.to_numpy()[: r21.T],
        "mdis": (a.discharge_mw - a.charge_mw).to_numpy(),
        "ecap": float(st.energy_cap_mwh.max()),
    }


def part_a() -> dict:
    """h18 residual decomposition and battery placement at h16-21."""
    res = {}
    for y in YEARS:
        d = inputs(y)
        k18 = (HOD == 18) & ~np.isnan(d["m"])
        thr = np.nanquantile(d["m"][k18], TAIL_Q)
        r = d["p"] - d["m"]
        tail = k18 & (d["m"] >= thr)
        body = k18 & ~tail
        n = k18.sum()
        res[y] = {
            "h18_resid": round(float(r[k18].mean()), 2),
            "from_tail": round(float(r[tail].sum() / n), 2),
            "from_body": round(float(r[body].sum() / n), 2),
            "body_median": round(float(np.median(r[body])), 2),
            "tail_thr": round(float(thr), 1),
            "li_ion_energy_mwh": round(d["ecap"]),
            "net_dis_by_hod": {
                h: {
                    "model": round(float(np.nanmean(d["dis"][HOD == h]))),
                    "meas": round(float(np.nanmean(d["mdis"][HOD == h]))),
                }
                for h in range(16, 22)
            },
        }
    return res


def part_b() -> dict:
    """Gas-stack price lift at h18 body hours if model battery net discharge matched measured."""
    repo = Path(__file__).resolve().parents[2]
    for q in (repo, repo / "src"):
        if str(q) not in sys.path:
            sys.path.insert(0, str(q))
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    out = {}
    for y in YEARS:
        d = inputs(y)
        state, _ = reconstruct_bundle_fleet(
            BUNDLE.parent, y, required_flags=(), required_sequences=()
        )
        fa, fleet = state["fleet_arrays"], state["fleet"]
        mc = np.asarray(state["mc_base"], float)
        cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
        klass = np.array(
            [
                str(getattr(g, "plant_group", "") or getattr(g, "fuel_type", ""))
                for g in fleet
            ]
        )
        zone = np.array([str(getattr(g, "zone", "")) for g in fleet])
        gmask = np.isin(klass, r22.GAS_CLASSES + ["oil"]) & ~np.char.startswith(
            zone.astype(str), "WECC"
        )
        cb = pd.read_parquet(BUNDLE / f"class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & cb.klass.isin(r22.GAS_CLASSES)]
        gas = (
            cb.groupby("hour").mw.sum().reindex(range(r21.T), fill_value=0.0).to_numpy()
        )
        k18 = (HOD == 18) & ~np.isnan(d["m"]) & ~np.isnan(d["mdis"])
        thr = np.nanquantile(d["m"][(HOD == 18) & ~np.isnan(d["m"])], TAIL_Q)
        body = np.flatnonzero(k18 & (d["m"] < thr))
        lifts, excess = [], []
        for h in body:
            x = float(d["dis"][h] - d["mdis"][h])  # model over-discharge, MW
            o = np.argsort(mc[gmask, h])
            cm, ms = np.cumsum(cap[gmask, h][o]), mc[gmask, h][o]

            def at(q: float) -> float:
                return float(ms[min(np.searchsorted(cm, max(q, 0.0)), len(ms) - 1)])

            lifts.append(at(gas[h] + x) - at(gas[h]))
            excess.append(x)
        lifts, excess = np.array(lifts), np.array(excess)
        k = len(np.flatnonzero(k18))
        out[y] = {
            "body_hours": int(len(body)),
            "excess_mw_mean": round(float(excess.mean())),
            "excess_mw_p50": round(float(np.median(excess))),
            "lift_mean": round(float(lifts.mean()), 2),
            "lift_as_h18_contrib": round(float(lifts.sum() / k), 2),
            "lift_p90": round(float(np.quantile(lifts, 0.9)), 2),
        }
        print(y, out[y], flush=True)
    return out


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if "--stack" in sys.argv:
        b = part_b()
        (OUT / "partB_stack.json").write_text(json.dumps(b, indent=1))
    else:
        a = part_a()
        (OUT / "partA_h18.json").write_text(json.dumps(a, indent=1))
        print(json.dumps(a, indent=1))
