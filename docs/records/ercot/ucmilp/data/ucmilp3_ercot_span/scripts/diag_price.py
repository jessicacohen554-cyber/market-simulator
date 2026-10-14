"""UC-3-ERCOT price-move diagnosis (PRECOMMIT §2), zero LP, control bundle vs arm bundle, one year.

Usage: diag_price.py <control_bundle> <arm_bundle> <year> [--json out.json]

1. Δ demand-weighted system price by hour class (actual terciles, actual <= $15, top-100 actual,
   on-peak weekday HE07-22 vs off-peak) and each class's contribution to Δ annual mean.
2. Marginal unit-hour mix (unit_marginal marginal==1) by plant_group x tranche, per class.
3. Online MW of slow classes (plant-level output >= 1 % of plant cap, both bundles, same convention).
4. Mean reserve MCP per class.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "/home/user/market-simulator/scripts/probes")
sys.path.insert(0, "/home/user/market-simulator/src")
from _ucmilp_benefit_screen import actual_rt, model_reserve_mcp, system_price  # noqa: E402

T = 8760
SLOW = ["CC_REGULAR", "ST_GAS", "COAL_PRB", "COAL_LIGNITE"]


def tranche(uid: pd.Series) -> pd.Series:
    suf = uid.str.rsplit("_", n=1).str[-1]
    out = np.where(
        suf.str.startswith("peak"),
        "peak",
        np.where(
            suf.str.startswith("econ"),
            "econ",
            np.where(
                suf.str.startswith("mustrun"),
                "mustrun",
                np.where(suf.str.startswith("commit"), "committed", "other"),
            ),
        ),
    )
    return pd.Series(out, index=uid.index)


def classes(act: np.ndarray, y: int) -> dict[str, np.ndarray]:
    ok = ~np.isnan(act)
    q1, q2 = np.nanquantile(act, [1 / 3, 2 / 3])
    ts = pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), unit="h")
    he = ts.hour + 1
    onpk = (ts.dayofweek < 5) & (he >= 7) & (he <= 22)
    top = np.zeros(T, bool)
    top[np.argsort(np.where(ok, act, -np.inf))[-100:]] = True
    return {
        "all": ok,
        "T1_low": ok & (act <= q1),
        "T2_mid": ok & (act > q1) & (act <= q2),
        "T3_high": ok & (act > q2),
        "act<=15": ok & (act <= 15),
        "top100": top & ok,
        "onpeak": ok & np.asarray(onpk),
        "offpeak": ok & ~np.asarray(onpk),
    }


def marginal_mix(bundle: Path, y: int) -> pd.DataFrame:
    u = pd.read_parquet(
        bundle / f"hourly/unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_group", "hour", "marginal"],
    )
    u = u[u["marginal"] == 1].copy()
    u["unit_id"] = u["unit_id"].astype(str)
    u["grp"] = (
        u["plant_group"].astype(str).replace("", "other") + ":" + tranche(u["unit_id"])
    )
    return u[["hour", "grp"]]


def online_mw(bundle: Path, y: int) -> pd.DataFrame:
    u = pd.read_parquet(
        bundle / f"hourly/unit_marginal_{y}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
    )
    u["plant_group"] = u["plant_group"].astype(str)
    u = u[u["plant_group"].isin(SLOW)]
    g = u.groupby(["plant_group", "plant_code", "hour"], observed=True)[
        ["mw", "cap_mw"]
    ].sum()
    g["on"] = g["mw"] >= 0.01 * g["cap_mw"]
    g["on_cap"] = np.where(g["on"], g["cap_mw"], 0.0)
    return (
        g.groupby(["plant_group", "hour"], observed=True)["on_cap"]
        .sum()
        .unstack(0)
        .reindex(range(T))
        .fillna(0.0)
    )


def main() -> None:
    ctl, arm, y = Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3])
    act = actual_rt("ERCOT", y)
    _, pc, _ = system_price(ctl, y)
    _, pa, _ = system_price(arm, y)
    rc, ra = model_reserve_mcp(ctl, y), model_reserve_mcp(arm, y)
    cl = classes(act, y)
    mc, ma = marginal_mix(ctl, y), marginal_mix(arm, y)
    oc, oa = online_mw(ctl, y), online_mw(arm, y)
    n_all = cl["all"].sum()
    out = {"year": y, "classes": {}}
    for name, m in cl.items():
        hrs = np.flatnonzero(m)
        d = pa[m] - pc[m]
        row = {
            "hours": int(m.sum()),
            "actual_mean": float(np.nanmean(act[m])),
            "ctl_mean": float(np.nanmean(pc[m])),
            "arm_mean": float(np.nanmean(pa[m])),
            "delta_mean": float(np.nanmean(d)),
            "contrib_to_annual_delta": float(np.nansum(d) / n_all),
            "share_hours_arm_up": float(np.mean(d > 0.5)),
            "share_hours_arm_down": float(np.mean(d < -0.5)),
            "reserve_mcp_ctl": float(rc[m].mean()),
            "reserve_mcp_arm": float(ra[m].mean()),
            "online_gw_ctl": {
                k: float(oc[k].to_numpy()[m].mean() / 1e3) for k in oc.columns
            },
            "online_gw_arm": {
                k: float(oa[k].to_numpy()[m].mean() / 1e3) for k in oa.columns
            },
        }
        hs = set(hrs.tolist())
        for tag, mm in (("ctl", mc), ("arm", ma)):
            sub = mm[mm["hour"].isin(hs)]
            row[f"marginal_mix_{tag}"] = (
                sub["grp"].value_counts(normalize=True).head(8).round(3).to_dict()
            )
        out["classes"][name] = row
    js = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    if js:
        Path(js).write_text(json.dumps(out, indent=1))
    print(f"ERCOT {y}: Δ mean system price arm−ctl by actual-hour class")
    print(
        f"{'class':<9}{'hrs':>6}{'act':>8}{'ctl':>8}{'arm':>8}{'Δ':>8}{'→annual':>9}{'up%':>6}{'dn%':>6}{'resC':>7}{'resA':>7}  CC_on ctl→arm GW  ST_on"
    )
    for k, r in out["classes"].items():
        cc = (
            r["online_gw_ctl"].get("CC_REGULAR", 0),
            r["online_gw_arm"].get("CC_REGULAR", 0),
        )
        st = (r["online_gw_ctl"].get("ST_GAS", 0), r["online_gw_arm"].get("ST_GAS", 0))
        print(
            f"{k:<9}{r['hours']:>6}{r['actual_mean']:>8.1f}{r['ctl_mean']:>8.1f}{r['arm_mean']:>8.1f}{r['delta_mean']:>+8.1f}"
            f"{r['contrib_to_annual_delta']:>+9.2f}{r['share_hours_arm_up'] * 100:>6.0f}{r['share_hours_arm_down'] * 100:>6.0f}"
            f"{r['reserve_mcp_ctl']:>7.1f}{r['reserve_mcp_arm']:>7.1f}  {cc[0]:5.1f}→{cc[1]:5.1f}  {st[0]:4.1f}→{st[1]:4.1f}"
        )
    for k in ("T1_low", "T3_high", "top100"):
        r = out["classes"][k]
        print(
            f"  marginal mix {k}: ctl {r['marginal_mix_ctl']}\n  {'':>17}arm {r['marginal_mix_arm']}"
        )


if __name__ == "__main__":
    main()
