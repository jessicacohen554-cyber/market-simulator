"""SPP-109 (zero LP): the sub-5-day gas outage gap SPP-105 left open.

Record: ``docs/records/spp/PRECOMMIT-spp-109-subfiveday-gas-outage-2026-10-03.md`` (readings R1-R6, bar
B1, kills Z1-Z3, all fixed before this probe ran) and its FINDING / RESULT.

Rebuilds the designated keeper ``results/calibration/w0_sppr_span`` ``fleet_only`` per year
(``scripts.lib.bundle_fleet.reconstruct_bundle_fleet``, no LP) under four instruments, never configs:

* ``K``  -- the keeper as recorded;
* ``G``  -- K + ``unit_outage_short_windows_gas`` (the measured sub-5-day gas family);
* ``Gp`` -- G + ``wefor_residual_groups`` = the four gas short-family groups at the keeper's 0.0 (the arm);
* ``K0`` -- K with ``wefor_residual`` unset (the ST_GAS statistical WEFOR R-29 removed, restored).

All four on SPP-105's outage-type basis: the flat GADS derate and the flat summer class derate are zeroed
(SPP's CROW report carries no ambient derate), identically in every instrument, so differences are exact.

R1 is read from the extracts at unit grain; R2-R4 from availability differences; R5 against SPP's published
hourly Natural Gas outage (``data/raw/spp-gen-outage/spp_capacity_gen_outage_hourly.csv``); R6 is the daily
correlation of the short family's MW with that series. Solves nothing. Usage:
``python scripts/probes/_spp109_subfiveday_gas_phase0.py --cache <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp84_published_outage_rebasis import (  # noqa: E402
    spp_outage_on_model_clock,
)
from scripts.probes._spp105_gas_outage_hourly_phase0 import (  # noqa: E402
    class_of,
    edge_mask,
    hour_meta,
)

BUNDLE = REPO_ROOT / "results/calibration/w0_sppr_span"
YEARS = tuple(range(2019, 2026))
GAS_FUELS = ("gas_cc", "gas_ct", "gas_st")
SHORT_GROUPS = ("CC_CHP", "CC_REGULAR", "ST_CHP", "ST_GAS")
ARMS: dict[str, dict] = {
    "K": {},
    "G": {"unit_outage_short_windows_gas": True},
    "Gp": {
        "unit_outage_short_windows_gas": True,
        "wefor_residual_groups": frozenset(SHORT_GROUPS),
    },
    "K0": {"wefor_residual": None, "wefor_residual_groups": None},
}
#: SPP-105 carrier A's removed gas unavailability, GW (DESIGN-spp-105 s4), and bar B1 = 0.5 x it.
SPP105_GAP_GW = {
    2019: 0.67,
    2020: 0.71,
    2021: 0.61,
    2022: 0.67,
    2023: 0.79,
    2024: 0.84,
    2025: 0.81,
}
TRAIN = (2023, 2024, 2025)
EXTRACTS = {
    "L": "campd-unit-outages-netloadmask-splitremap-SPP.csv",
    "S": "campd-unit-outages-shortgas-splitremap-SPP.csv",
    "S_lay": "campd-unit-outages-layup-shortgas-SPP.csv",
}


def rebuild(y: int, cache: Path, arm: str) -> dict:
    """``fleet_only`` rebuild of keeper year ``y`` under instrument ``arm`` (outage-type basis, cached)."""
    p = cache / f"spp109_{y}_{arm}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import arrays as _arr
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    orig_out, orig_sum = _arr._thermal_outage, dict(_arr._SUMMER_CLASS_DERATE)
    orig_post = ScenarioConfig.__post_init__

    def _patched(c, a):
        pof, wefor, _derate = orig_out(c, a)
        return pof, wefor, 0.0

    def _armed(self):
        for k, v in ARMS[arm].items():
            object.__setattr__(self, k, v)
        orig_post(self)

    _arr._thermal_outage = _patched
    _arr._SUMMER_CLASS_DERATE.clear()
    ScenarioConfig.__post_init__ = _armed
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        _arr._thermal_outage = orig_out
        _arr._SUMMER_CLASS_DERATE.clear()
        _arr._SUMMER_CLASS_DERATE.update(orig_sum)
        ScenarioConfig.__post_init__ = orig_post
    for k, v in ARMS[arm].items():
        assert getattr(st["config"], k) == v, (arm, k, getattr(st["config"], k))
    fa = st["fleet_arrays"]
    keys = ("unit_id", "fuel_type", "plant_group", "zone", "plant_code", "online_year")
    out = {
        "rows": [{k: getattr(g, k, None) for k in keys} for g in st["fleet"]],
        "pmax": np.asarray(fa.pmax, dtype=np.float32),
        "availability": np.asarray(fa.availability, dtype=np.float32),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def extract_grain(y: int) -> dict:
    """R1: unit-capacity x window-hours per class (GWh, and annual-mean GW) per extract."""
    out: dict = {}
    for tag, name in EXTRACTS.items():
        d = pd.read_csv(RAW_DATA_DIR / name)
        d = d[d.plant_group.isin(SHORT_GROUPS)]
        s = pd.to_datetime(d.outage_start)
        e = pd.to_datetime(d.outage_end) + pd.Timedelta(days=1)
        lo, hi = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")
        hrs = (e.clip(upper=hi) - s.clip(lower=lo)).dt.total_seconds().clip(
            lower=0
        ) / 3600
        gwh = d.unit_capacity_mw.fillna(0).to_numpy() * hrs.to_numpy() / 1e3
        by = pd.Series(gwh, index=d.plant_group.to_numpy()).groupby(level=0).sum()
        out[tag] = {
            c: {
                "gwh": round(float(by.get(c, 0.0)), 1),
                "gw": round(float(by.get(c, 0.0)) / 8760, 3),
            }
            for c in SHORT_GROUPS
        }
        out[tag]["n_windows"] = int(((s < hi) & (e > lo)).sum())
    out["share_S_over_S_plus_L"] = {
        c: (
            round(out["S"][c]["gwh"] / (out["S"][c]["gwh"] + out["L"][c]["gwh"]), 3)
            if out["S"][c]["gwh"] + out["L"][c]["gwh"] > 0
            else None
        )
        for c in SHORT_GROUPS
    }
    return out


def year_readings(y: int, cache: Path, spp: pd.DataFrame, lmp: pd.DataFrame) -> dict:
    """R1-R6 for one year."""
    fl = {a: rebuild(y, cache, a) for a in ARMS}
    rows = fl["K"]["rows"]
    for a in ARMS:
        assert len(fl[a]["rows"]) == len(rows), (y, a)
    cls = class_of(rows)
    ft = np.array([r["fuel_type"] for r in rows])
    pm = fl["K"]["pmax"].astype(float)
    av = {a: pm[:, None] * fl[a]["availability"].astype(float) for a in ARMS}
    live = ~np.array([edge_mask(x) for x in av["K"]])
    un = {a: np.where(live, pm[:, None] - av[a], 0.0) for a in ARMS}
    gas = np.isin(ft, GAS_FUELS)
    meta = hour_meta(y, lmp)
    upper = (meta.seg == "upper").to_numpy()
    sp = spp_outage_on_model_clock(spp, y)["Natural Gas MW"].to_numpy()
    ok = np.isfinite(sp)

    def gw(x: np.ndarray, m: np.ndarray | None = None) -> float:
        return round(float(x[m].mean() if m is not None else x.mean()) / 1e3, 3)

    per_class = {}
    for c in SHORT_GROUPS:
        sel = cls == c
        if not sel.any():
            per_class[c] = None
            continue
        s_g = (un["G"][sel] - un["K"][sel]).sum(0)
        w_cc = (un["G"][sel] - un["Gp"][sel]).sum(0)
        w_st = (un["K0"][sel] - un["K"][sel]).sum(0)
        n = (un["Gp"][sel] - un["K"][sel]).sum(0)
        per_class[c] = {
            "live_pmax_gw": gw(np.where(live[sel], pm[sel][:, None], 0.0).sum(0)),
            "R2_S_g_gw": gw(s_g),
            "R3_W_removed_by_arm_gw": gw(w_cc),
            "R3_W_removed_at_R29_gw": gw(w_st),
            "R4_net_gw": gw(n),
            "R4_net_upper_gw": gw(n, upper),
        }
    four = np.isin(cls, SHORT_GROUPS)
    s_tot = (un["G"][four] - un["K"][four]).sum(0)
    w_tot = (un["G"][four] - un["Gp"][four]).sum(0)
    n_tot = (un["Gp"][four] - un["K"][four]).sum(0)
    k_gas = un["K"][gas].sum(0)
    g_gas = un["Gp"][gas].sum(0)
    r5 = {}
    for tag, x in (("K", k_gas), ("Gp", g_gas)):
        r5[tag] = {
            "gas_gw_all": gw(x),
            "minus_spp_all_gw": round(float(np.mean(x[ok] - sp[ok])) / 1e3, 3),
            "mean_abs_gap_all_gw": round(
                float(np.mean(np.abs(x[ok] - sp[ok]))) / 1e3, 3
            ),
            "mean_abs_gap_upper_gw": round(
                float(np.mean(np.abs(x[ok & upper] - sp[ok & upper]))) / 1e3, 3
            ),
        }
    d = pd.DataFrame({"s": s_tot, "p": sp, "day": np.arange(8760) // 24}).dropna()
    dd = d.groupby("day").mean()
    return {
        "year": y,
        "R1_extract": extract_grain(y),
        "per_class": per_class,
        "four_class": {
            "R2_S_g_gw": gw(s_tot),
            "R2_S_g_upper_gw": gw(s_tot, upper),
            "R3_W_removed_by_arm_gw": gw(w_tot),
            "R4_net_gw": gw(n_tot),
            "R4_net_upper_gw": gw(n_tot, upper),
            "R4_net_peak_hour_gw": round(float(n_tot.max()) / 1e3, 3),
        },
        "R5_rule14": r5,
        "R6_daily_corr": round(float(dd.s.corr(dd.p)), 3),
        "_daily": dd.reset_index().to_dict(orient="list"),
        "spp105_gap_gw": SPP105_GAP_GW[y],
        "B1_threshold_gw": round(0.5 * SPP105_GAP_GW[y], 3),
    }


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    spp = pd.read_csv(
        RAW_DATA_DIR / "spp-gen-outage/spp_capacity_gen_outage_hourly.csv"
    )
    spp.columns = [c.strip() for c in spp.columns]
    spp["t"] = pd.to_datetime(
        spp["Market Hour"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    spp = spp.dropna(subset=["t"]).drop_duplicates("t", keep="last")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    res = {y: year_readings(y, args.cache, spp, lmp) for y in args.years}
    daily = {y: r.pop("_daily") for y, r in res.items()}
    pooled = pd.concat([pd.DataFrame(v) for v in daily.values()])
    summary = {
        "B1": {
            str(y): {
                "S_g_gw": res[y]["four_class"]["R2_S_g_gw"],
                "threshold_gw": res[y]["B1_threshold_gw"],
                "pass": res[y]["four_class"]["R2_S_g_gw"] >= res[y]["B1_threshold_gw"],
            }
            for y in TRAIN
            if y in res
        },
        "Z1_pooled_mean_abs_gap_gw": {
            a: round(
                float(
                    np.mean(
                        [res[y]["R5_rule14"][a]["mean_abs_gap_all_gw"] for y in res]
                    )
                ),
                3,
            )
            for a in ("K", "Gp")
        },
        "Z2_pooled_daily_corr": round(float(pooled.s.corr(pooled.p)), 3),
    }
    summary["B1_pass"] = all(v["pass"] for v in summary["B1"].values())
    summary["Z1_kill"] = (
        summary["Z1_pooled_mean_abs_gap_gw"]["Gp"]
        > summary["Z1_pooled_mean_abs_gap_gw"]["K"]
    )
    summary["Z2_kill"] = summary["Z2_pooled_daily_corr"] <= 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"summary": summary, "years": res}, indent=1, default=str)
    )
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
