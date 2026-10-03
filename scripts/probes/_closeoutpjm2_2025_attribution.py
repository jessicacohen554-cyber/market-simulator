"""closeout-PJM-2 (ZERO LP): attribute the PJM 2025 C3a/C3b PASS->FAIL move.

Incumbent ``pjmnext16_A_span`` (keeper 2026-09-30-pjm-next16-ovec, C3a -9.6 %, C3b 0.182)
against the W0 keeper ``w0_pjm_span`` (2026-10-02-w0-pjm-fix2, C3a -11.6 %, C3b 0.222).
Record: ``docs/records/pjm/FINDING-closeout-pjm-2-2025-regression-attribution-2026-10-03.md``.

Buckets: (i) the 2025 EIA-923 must-run drift (biomass + OTHER, injected by
``run_calibration_full._must_run_profiles`` as a demand-share split, flat within a month);
(ii) the ten W0 EIA-860 fleet fields (``rebuild_fleet`` fleet_only toggles on the incumbent's
2025 recipe: recorded, w0, alone-f, leave-one-out-f); (iii) the renewables fix #7040 (w0 with
``renewables._renewable_zone_lookup`` patched back to the pre-fix eGRID-only lookup);
(iv) the solver stack (incumbent highspy 1.15.1 vs locked 1.14.0) is documented only.

Steps:
1. Locate the hours where either bundle carries energy-balance slack (VOLL).
2. Per slack hour, the in-zone supply change by bucket and a Shapley split of the hours'
   load-weighted price move; a slack hour clears at the W0 price when its counterfactual
   shortfall is gone, else keeps the incumbent price.
3. Outside those hours, a greedy same-setter system re-clear on the committed
   ``unit_marginal_2025`` stacks: the must-run drift (both directions, bracket) and the W0
   in-merit capacity change (cap_mw by unit, units with mc <= the hour's setter).
4. Re-score C3a/C3b (``calibration_verdict`` helpers, committed bench part) on
   counterfactual price series that swap only the slack hours.

The incumbent bundle was pruned at promotion; its sidecars are read from git
(``d215d7a1^``, the commit before the W0 promotion). Writes
``results/phase0/pjm/_closeoutpjm2_2025_attribution.json``.
Run: ``.venv/bin/python scripts/probes/_closeoutpjm2_2025_attribution.py`` (~10 min, 24 rebuilds).
"""

from __future__ import annotations

import itertools
import json
import logging
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

YEAR = 2025
INC_REF = "d215d7a1^"
INC_DIR = "results/calibration/pjmnext16_A_span"
W0_DIR = REPO / "results/calibration/w0_pjm_span"
ZONE = "PJM_EMAAC"
INJECTED = ("biomass", "OTHER")
INC_FILES = (
    "meta.json",
    "metrics.json",
    "run_config.json",
    f"run_config_{YEAR}.json",
    f"hourly/class_hourly_{YEAR}.parquet",
    f"hourly/system_{YEAR}.parquet",
    f"hourly/unit_marginal_{YEAR}.parquet",
)
OUT = REPO / "results/phase0/pjm/_closeoutpjm2_2025_attribution.json"
UM_COLS = ["hour", "unit_id", "fuel", "zone", "mw", "cap_mw", "mc", "marginal"]


def extract_incumbent(dest: Path) -> Path:
    """Write the pruned incumbent's 2025 sidecars from git into ``dest``."""
    for f in INC_FILES:
        p = dest / f
        p.parent.mkdir(parents=True, exist_ok=True)
        blob = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{INC_REF}:{INC_DIR}/{f}"],
            check=True,
            capture_output=True,
        ).stdout
        p.write_bytes(blob)
    return dest


def system(bundle: Path) -> pd.DataFrame:
    """Zone-hour price/demand/slack for the year, external node dropped."""
    s = pd.read_parquet(bundle / f"hourly/system_{YEAR}.parquet")
    s = s[s.zone.astype(str) != "PJM_external"].copy()
    s["zone"] = s.zone.astype(str)
    return s


def sys_price(s: pd.DataFrame) -> np.ndarray:
    """Load-weighted system price per hour (8760)."""
    g = s.assign(x=s.price * s.demand).groupby("hour")
    return (g.x.sum() / g.demand.sum()).reindex(range(8760)).values


def mustrun(bundle: Path) -> np.ndarray:
    """System injected must-run MW per hour (biomass + OTHER pseudo-units)."""
    c = pd.read_parquet(bundle / f"hourly/class_hourly_{YEAR}.parquet")
    c = c[c.klass.astype(str).isin(INJECTED)]
    return c.groupby("hour").mw.sum().reindex(range(8760)).fillna(0.0).values


def unit_marginal(bundle: Path) -> pd.DataFrame:
    """The committed per-unit P1 layer, interchange pseudo-units dropped."""
    u = pd.read_parquet(bundle / f"hourly/unit_marginal_{YEAR}.parquet", columns=UM_COLS)
    for c in ("unit_id", "fuel", "zone"):
        u[c] = u[c].astype(str)
    return u[u.fuel != "import"]


def fleet_toggles(inc: Path, hours: list[int]) -> dict:
    """fleet_only rebuilds: zone in-zone availability and zone solar in ``hours``."""
    logging.disable(logging.WARNING)
    import market_sim.data.renewables as ren
    from scripts.build_fleet_census import _w0_fields, rebuild_fleet

    orig = ren._renewable_zone_lookup

    def prefix_lookup(iso, data_dir):  # the pre-#7040 membership: eGRID lookup only
        from market_sim.data.zone_assignment import build_zone_lookup

        try:
            return build_zone_lookup(iso)
        except Exception:
            return {}

    def one(posture: str, over: dict, prefix: bool = False) -> dict:
        ren._renewable_zone_lookup = prefix_lookup if prefix else orig
        o = {"pjm_da_virtual_bids": False}  # the census convention (input not in checkout)
        o.update(over)
        r = rebuild_fleet(inc, YEAR, posture, o)
        fa = r["fleet_arrays"]
        zn = list(r["iso_config"].zone_names)
        z = zn.index(ZONE)
        av = np.asarray(fa.pmax)[:, None] * np.asarray(fa.availability)
        av = np.broadcast_to(av, (len(fa.pmax), 8760))
        pg = np.asarray(fa.plant_group).astype(str)
        return {
            "zone_avail": av[np.asarray(fa.zone_idx) == z][:, hours].sum(0).tolist(),
            "zone_solar": (r["solar_cf"][z, hours] * r["solar_cap"][z]).tolist(),
            "solar_cap_by_zone": dict(zip(zn, np.round(np.asarray(r["solar_cap"]), 1).tolist())),
            "avail_twh_by_group": {g: float(av[pg == g].sum() / 1e6) for g in sorted(set(pg))},
        }

    fields = list(_w0_fields())
    out = {"recorded": one("recorded", {}), "w0": one("w0", {})}
    out["w0_prefix_renewables"] = one("w0", {}, prefix=True)
    for f in fields:
        out[f"alone:{f}"] = one("recorded", {f: True})
        out[f"loo:{f}"] = one("w0", {f: False})
    ren._renewable_zone_lookup = orig
    return out


def walk(u: pd.DataFrame, p: np.ndarray, delta: np.ndarray, up: bool) -> np.ndarray:
    """Greedy system re-clear: setter mc change after moving ``|delta|`` MW along the stack."""
    out = np.zeros(8760)
    for h, g in u.groupby("hour", sort=True):
        x = abs(delta[h])
        if x < 1:
            continue
        mc, mw, cap = g.mc.values, g.mw.values, g.cap_mw.values
        mk = g.marginal.values.astype(bool)
        ref = mc[mk][np.argmin(np.abs(mc[mk] - p[h]))] if mk.any() else p[h]
        if up:
            sel = (cap - mw > 0.5) & (mc >= ref - 1e-6)
            o = np.argsort(mc[sel])
            c = np.cumsum((cap - mw)[sel][o])
        else:
            sel = (mw > 0.5) & (mc <= ref + 1e-6)
            o = np.argsort(-mc[sel])
            c = np.cumsum(mw[sel][o])
        new = mc[sel][o][min(np.searchsorted(c, x), len(o) - 1)] if len(o) else ref
        out[h] = new - ref
    return out


def fleet_inmerit(uw: pd.DataFrame, ui: pd.DataFrame, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Per hour: W0-minus-incumbent cap_mw on units at/below the setter, and its price effect."""
    m = uw.merge(ui[["hour", "unit_id", "cap_mw", "mc"]], on=["hour", "unit_id"], how="outer", suffixes=("", "_i"))
    m[["cap_mw", "cap_mw_i", "mw"]] = m[["cap_mw", "cap_mw_i", "mw"]].fillna(0.0)
    m["mc"] = m.mc.fillna(m.mc_i)
    m["marginal"] = m.marginal.fillna(0)
    ds, eff = np.zeros(8760), np.zeros(8760)
    for h, g in m.groupby("hour", sort=True):
        mc, mw, cap, capi = g.mc.values, g.mw.values, g.cap_mw.values, g.cap_mw_i.values
        mk = g.marginal.values.astype(bool)
        ref = mc[mk][np.argmin(np.abs(mc[mk] - p[h]))] if mk.any() else p[h]
        x = ((cap - capi) * (mc <= ref + 1e-6)).sum()
        ds[h] = x
        if abs(x) < 1:
            continue
        if x > 0:
            sel = (cap - mw > 0.5) & (mc >= ref - 1e-6)
            o = np.argsort(mc[sel])
            c = np.cumsum((cap - mw)[sel][o])
        else:
            sel = (mw > 0.5) & (mc <= ref + 1e-6)
            o = np.argsort(-mc[sel])
            c = np.cumsum(mw[sel][o])
        new = mc[sel][o][min(np.searchsorted(c, abs(x)), len(o) - 1)] if len(o) else ref
        eff[h] = -(new - ref)
    return ds, eff


def rescore(s: pd.DataFrame, act_mon: list, act: float) -> dict:
    """C3a (load-weighted mean vs RT lw) and C3b (monthly lw NRMSE) on a zone-hour frame."""
    import scripts.calibration_verdict as cv

    mon = (pd.Timestamp(f"{YEAR}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month.values
    s = s.assign(m=mon[s.hour.values], x=s.price * s.demand)
    mean = s.x.sum() / s.demand.sum()
    mm = s.groupby("m").x.sum() / s.groupby("m").demand.sum()
    return {"mean": round(float(mean), 2), "c3a_pct": round(100 * (mean / act - 1), 2),
            "c3b": round(float(cv._nrmse(list(mm.values), act_mon)), 3)}


def main() -> int:
    """Run the attribution and write the JSON record."""
    from scripts.lib import backcast_artifacts as ba

    tmp = Path(tempfile.mkdtemp(prefix="closeoutpjm2_"))
    inc = extract_incumbent(tmp / "inc")
    si, sw = system(inc), system(W0_DIR)
    pi, pw = sys_price(si), sys_price(sw)
    dem = si.groupby("hour").demand.sum().reindex(range(8760)).values
    dt = dem.sum()
    zshare = float(si[si.zone == ZONE].demand.sum() / si.demand.sum())
    slack_hours = sorted(set(si[si.slack > 0].hour) | set(sw[sw.slack > 0].hour))
    scar = np.zeros(8760, bool)
    scar[slack_hours] = True
    dmr = mustrun(W0_DIR) - mustrun(inc)

    # Step 2: per slack hour, in-zone supply by bucket.
    ui, uw = unit_marginal(inc), unit_marginal(W0_DIR)
    zi = ui[(ui.zone == ZONE) & ui.hour.isin(slack_hours)].groupby("hour")
    zw = uw[(uw.zone == ZONE) & uw.hour.isin(slack_hours)].groupby("hour")
    zsys = lambda s, col: s[s.zone == ZONE].set_index("hour")[col].reindex(slack_hours).values  # noqa: E731
    tog = fleet_toggles(inc, slack_hours)
    F = np.array(tog["w0"]["zone_avail"]) - np.array(tog["recorded"]["zone_avail"])
    R = np.array(tog["w0"]["zone_solar"]) - np.array(tog["w0_prefix_renewables"]["zone_solar"])
    M = dmr[slack_hours] * zshare
    resid = lambda s, z, mr: zsys(s, "demand") - z.mw.sum().reindex(slack_hours).values - mr - zsys(s, "slack")  # noqa: E731
    N = (resid(sw, zw, mustrun(W0_DIR)[slack_hours] * zshare) - resid(si, zi, mustrun(inc)[slack_hours] * zshare)) - R
    buckets = {"W0_fleet": F, "mustrun_drift": M, "renewables_fix": R, "net_import_residual": N}
    sa = zsys(si, "slack")
    ph_i, ph_w, dh = pi[slack_hours], pw[slack_hours], dem[slack_hours]

    def value(keys) -> float:
        sup = sum((buckets[k] for k in keys), np.zeros(len(slack_hours)))
        p = np.where(np.maximum(0.0, sa - sup) > 0.5, ph_i, ph_w)
        return float(((p - ph_i) * dh).sum() / dt)

    keys = list(buckets)
    shapley = {}
    for k in keys:
        rest = [x for x in keys if x != k]
        shapley[k] = sum(
            math.factorial(len(c)) * math.factorial(len(keys) - len(c) - 1) / math.factorial(len(keys))
            * (value(set(c) | {k}) - value(set(c)))
            for n in range(len(rest) + 1) for c in itertools.combinations(rest, n)
        )
    field_zone_mw = {
        f.split(":", 1)[1]: {
            "alone": round(float(np.mean(np.array(tog[f]["zone_avail"]) - np.array(tog["recorded"]["zone_avail"]))), 1),
            "loo": round(float(np.mean(np.array(tog["w0"]["zone_avail"]) - np.array(tog["loo:" + f.split(":", 1)[1]]["zone_avail"]))), 1),
        }
        for f in tog if f.startswith("alone:")
    }
    field_avail_twh = {
        f.split(":", 1)[1]: {
            g: round(v - tog["recorded"]["avail_twh_by_group"].get(g, 0.0), 2)
            for g, v in tog[f]["avail_twh_by_group"].items()
            if abs(v - tog["recorded"]["avail_twh_by_group"].get(g, 0.0)) > 0.05
        }
        for f in tog if f.startswith("alone:")
    }

    # Step 3: off-slack-hour greedy re-clears.
    d_up = walk(uw, pw, dmr, up=True)  # remove the drift from W0
    d_dn = walk(ui, pi, dmr, up=False)  # add the drift to the incumbent
    ds, feff = fleet_inmerit(uw, ui, pw)
    w = lambda x: float((x * dem)[~scar].sum() / dt)  # noqa: E731

    # Step 4: re-score counterfactual price series.
    bench = ba.load_bench_part(REPO / f"frontend/data/backcast/bench/PJM/{YEAR}.json.gz")["bench"]["avgLMP"]
    act, act_mon = bench["rt_lw"], bench["rt_lw_mon"]
    x = si.merge(sw[["zone", "hour", "price"]], on=["zone", "hour"], suffixes=("", "_w"))
    hs = set(slack_hours)
    swap = x.assign(price=np.where(x.hour.isin(hs), x.price_w, x.price))
    keep = x.assign(price=np.where(x.hour.isin(hs), x.price, x.price_w))

    real = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_zonal_PJM.parquet")
    real = real[real.year == YEAR].merge(si[["zone", "hour", "demand"]], on=["zone", "hour"])
    real_sys = (real.assign(x=real.rt * real.demand).groupby("hour").x.sum() / real.groupby("hour").demand.sum())

    rec = {
        "year": YEAR,
        "incumbent": f"{INC_REF}:{INC_DIR}",
        "w0": str(W0_DIR.relative_to(REPO)),
        "zone": ZONE,
        "zone_demand_share": round(zshare, 4),
        "score": {
            "incumbent": rescore(si, act_mon, act),
            "w0": rescore(sw, act_mon, act),
            "incumbent_slack_hours_swapped_to_w0": rescore(swap, act_mon, act),
            "w0_slack_hours_restored_to_incumbent": rescore(keep, act_mon, act),
            "actual_rt_lw": act,
        },
        "move_total_lw": float(((pw - pi) * dem).sum() / dt),
        "move_slack_hours_lw": float(((pw - pi) * dem)[scar].sum() / dt),
        "move_other_hours_lw": float(((pw - pi) * dem)[~scar].sum() / dt),
        "mustrun_drift_twh": float(dmr.sum() / 1e6),
        "slack_hours": [
            {
                "hour": int(h),
                "ts": str(pd.Timestamp(f"{YEAR}-01-01") + pd.Timedelta(hours=int(h))),
                "slack_inc_mw": round(float(sa[i]), 1),
                "slack_w0_mw": round(float(zsys(sw, "slack")[i]), 1),
                "W0_fleet_mw": round(float(F[i]), 1),
                "mustrun_drift_mw": round(float(M[i]), 1),
                "renewables_fix_mw": round(float(R[i]), 1),
                "net_import_residual_mw": round(float(N[i]), 1),
                "sys_price_inc": round(float(pi[h]), 1),
                "sys_price_w0": round(float(pw[h]), 1),
                "sys_price_real_rt": round(float(real_sys.get(h, np.nan)), 1),
            }
            for i, h in enumerate(slack_hours)
        ],
        "slack_hours_bucket_mean_mw": {k: round(float(v.mean()), 1) for k, v in buckets.items()},
        "slack_hours_price_shapley_lw": {k: round(v, 4) for k, v in shapley.items()},
        "slack_hours_all_buckets_lw": round(value(set(keys)), 4),
        "slack_hours_real_vs_model_lw": {
            "real": float((real_sys.reindex(slack_hours).values * dh).sum() / dt),
            "incumbent": float((ph_i * dh).sum() / dt),
            "w0": float((ph_w * dh).sum() / dt),
        },
        "reserve_price_positive_hours": {
            "incumbent": int((si.groupby("hour").reserve_price.max() > 0).sum()),
            "w0": int((sw.groupby("hour").reserve_price.max() > 0).sum()),
        },
        "w0_field_zone_avail_mw_slack_hours": field_zone_mw,
        "w0_field_avail_twh_alone": field_avail_twh,
        "solar_cap_by_zone": {"w0": tog["w0"]["solar_cap_by_zone"], "prefix": tog["w0_prefix_renewables"]["solar_cap_by_zone"]},
        "other_hours": {
            "mustrun_drift_effect_lw_bracket": [w(-d_up), w(d_dn)],
            "w0_fleet_inmerit_mean_mw": float(ds[~scar].mean()),
            "w0_fleet_inmerit_effect_lw": w(feff),
        },
        "solver_stack": {"incumbent_highspy": "1.15.1", "w0_highspy": "1.14.0", "separated": False},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(json.dumps({k: rec[k] for k in ("score", "move_total_lw", "move_slack_hours_lw", "move_other_hours_lw",
                                          "slack_hours_price_shapley_lw", "other_hours")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
