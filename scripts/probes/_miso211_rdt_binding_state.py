"""miso-211 — THE RDT SOUTH->NORTH BINDING STATE (phase 0, zero-solve).

Executes ``results/calibration/PREREG-miso211-rdt-binding-state-2026-09-04.md``
(pushed blind at ``5320e4dc``) on the miso-210 keeper's committed/local
sidecars and measured in-repo series. No LP is solved.

  R-1  the LP's corridor state (three priced S->N tiers, three N->S tiers,
       ``hourly/network_<year>.parquet`` flows + duals) in the hours MISO's own
       RT sub-regional PBC record shows the RDT binding S->N;
  R-2  WHY: (a) limit LEVEL discriminated through the LP's own flow, (b) the
       South boundary net (measured rf_al load - sr_gfm RT SE generation vs
       the model's into-South link flows) with a by-fuel decomposition,
       (c) the routing-around identity (topology verification);
  R-3  static reach on both populations: (a) the miso-208 strand lift
       re-measured, (b) the separation ceiling — measured INDIANA.HUB minus
       the four South hubs vs the model's Indiana-South zonal spread in the
       real binding hours;
  N-1  footing: populations and gaps reproduce miso-207/208; binding shares
       reproduce miso-208 within 2 pp.

Clocks (miso-183 convention, re-implemented verbatim here rather than imported
because that probe's module guard points at a since-pruned bundle): the model
index is CST hour-beginning; PBC 5-min rows are EST interval starts -> CST
hour H-1; rf_al / sr_gfm rows are Market Hour ENDING k EST -> CST hour k-2.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso211_rdt_binding_state.py

Record: ``results/calibration/_miso211_rdt_binding_state.json``.
"""

from __future__ import annotations

import dataclasses
import gzip
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso207_bound_the_shoulder as m207  # noqa: E402
import _miso208_find_the_supply as m208  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config, keeper_prices  # noqa: E402

# T-1: re-point EVERY module global to the miso-210 keeper BEFORE any helper runs.
KEEPER = REPO / "results/calibration/miso210_clock_B"
m207.KEEPER = KEEPER
_m134.BUNDLE = KEEPER
m208.KEEPER = KEEPER
assert m207.KEEPER == KEEPER and _m134.BUNDLE == KEEPER

OUT = REPO / "results/calibration/_miso211_rdt_binding_state.json"
PBC = REPO / "data/raw/transfer-constraint-binding/MISO"
REGBAL = REPO / "data/raw/miso-regional-balance"
ZONAL = m207.ZONAL
YEARS = (2023, 2024, 2025)
HOURS = 8760
HUB = m207.SCORING_HUB
SOUTH_HUBS = ("ARKANSAS.HUB", "LOUISIANA.HUB", "MS.HUB", "TEXAS.HUB")
S2N = "MISO-South>MISO-Plains"
N2S = "MISO-Plains>MISO-South"
EXT_S = "MISO_external_South>MISO-South"
FREE_S2N = 2300.0  # 0.92 x 2,500 (constants.MISO_RDT_*), the free tier
FREE_N2S = 2760.0
BIND_TOL = 1.0
LICENSE = 0.25
BINDING_MAJORITY = 6  # of 12 five-minute rows (miso-183)
GAS_CLASSES = m207.GAS_CLASSES
COAL_POOL = m207.COAL_POOL


# ----------------------------------------------------------------- clocks (miso-183)
def _nonleap_hour(y: int, m: int, d: int, hour_cst: int) -> int:
    if m == 2 and d == 29:
        return -1
    doy = (date(y, m, d) - date(y, 1, 1)).days + 1
    if date(y, 12, 31).timetuple().tm_yday == 366 and doy > 60:
        doy -= 1
    h = (doy - 1) * 24 + hour_cst
    return h if 0 <= h < HOURS else -1


def pbc_hourly(year: int, token: str) -> dict[str, np.ndarray]:
    """Per model hour: n 5-min rows, mean |shadow| over rows, for one RDT direction."""
    counts = np.zeros(HOURS, dtype=int)
    ssum = np.zeros(HOURS, dtype=float)
    with gzip.open(PBC / f"miso_pbc_rt_{year}.csv.gz", "rt") as fh:
        next(fh)
        for line in fh:
            parts = line.split(",", 3)
            if len(parts) < 3 or token not in parts[1]:
                continue
            ts = parts[0].strip()
            m, d, y = int(ts[0:2]), int(ts[3:5]), int(ts[6:10])
            if y != year:
                continue
            hh = int(ts[11:13]) - 1  # EST hour-beginning -> CST
            if hh < 0:
                prev = date(y, m, d) - pd.Timedelta(days=1)
                if prev.year != year:
                    continue
                h = _nonleap_hour(prev.year, prev.month, prev.day, 23)
            else:
                h = _nonleap_hour(y, m, d, hh)
            if h >= 0:
                counts[h] += 1
                try:
                    ssum[h] += abs(float(parts[2]))
                except ValueError:
                    pass
    with np.errstate(invalid="ignore", divide="ignore"):
        mean_shadow = np.where(counts > 0, ssum / np.maximum(counts, 1), 0.0)
    return {
        "any": counts >= 1,
        "majority": counts >= BINDING_MAJORITY,
        "n_rows": counts,
        "mean_abs_shadow": mean_shadow,
    }


def regional_series(
    year: int, kind: str, region: str, fuel: str | None = None
) -> np.ndarray:
    """rf_al actual load / sr_gfm RT SE generation (one fuel or Total) on the model clock."""
    out = np.full(HOURS, np.nan)
    if kind == "load":
        df = pd.read_csv(REGBAL / f"miso_regional_load_{year}.csv.gz")
        df = df[df["region"] == region]
        val = "actual_mw"
    else:
        df = pd.read_csv(REGBAL / f"miso_regional_genmix_{year}.csv.gz")
        df = df[(df["region"] == region) & (df["fuel"] == (fuel or "Total"))]
        val = "mw"
    for mdate, he, v in df[["market_date", "he_est", val]].itertuples(index=False):
        y, m, d = int(mdate[:4]), int(mdate[5:7]), int(mdate[8:10])
        h_cst = int(he) - 2
        if h_cst < 0:
            prev = date(y, m, d) - pd.Timedelta(days=1)
            if prev.year != year:
                continue
            h = _nonleap_hour(prev.year, prev.month, prev.day, h_cst + 24)
        else:
            h = _nonleap_hour(y, m, d, h_cst)
        if h >= 0:
            out[h] = v
    return out


FUEL_FAMILY = {
    "coal": "Coal",
    "gas": "Gas",
    "nuclear": "Nuclear",
    "hydro": "Hydro",
    "wind": "Wind",
    "solar": "Solar",
}


def _family(fuel: str) -> str:
    s = str(fuel).lower()
    for k, v in FUEL_FAMILY.items():
        if k in s:
            return v
    return "Other"


# ----------------------------------------------------------------- keeper readers
def corridor(year: int) -> dict[str, np.ndarray]:
    n = pd.read_parquet(KEEPER / f"hourly/network_{year}.parquet")
    n = n[(n["pass"] == "P1") & (n["kind"] == "link")]
    out: dict[str, np.ndarray] = {}
    for name, key in ((S2N, "s2n"), (N2S, "n2s")):
        sub = n[n["name"] == name]
        tot = sub.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0).to_numpy()
        free_lim = FREE_S2N if key == "s2n" else FREE_N2S
        free = sub[np.isclose(sub["limit_up"], free_lim)]
        out[f"{key}_flow"] = tot
        out[f"{key}_free_flow"] = (
            free.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0).to_numpy()
        )
        out[f"{key}_free_dual"] = (
            free.groupby("hour")["dual"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
        )
        out[f"{key}_max_dual"] = (
            sub.groupby("hour")["dual"].max().reindex(range(HOURS)).fillna(0).to_numpy()
        )
    ext = n[n["name"] == EXT_S]
    out["ext_south_flow"] = (
        ext.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0).to_numpy()
    )
    return out


def zone_prices(year: int) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    price = sysd.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(HOURS)
    )
    dem = sysd.pivot_table(index="hour", columns="zone", values="demand").reindex(
        range(HOURS)
    )
    slack = sysd.pivot_table(index="hour", columns="zone", values="slack").reindex(
        range(HOURS)
    )
    num = sysd.assign(pw=sysd["price"] * sysd["demand"]).groupby("hour")["pw"].sum()
    den = sysd.groupby("hour")["demand"].sum()
    lw = (num / den).reindex(range(HOURS)).to_numpy()
    return (
        price,
        lw,
        dem["MISO-South"].to_numpy(),
        slack["MISO-South"].fillna(0).to_numpy(),
    )


def south_generation(year: int) -> tuple[dict[str, np.ndarray], np.ndarray]:
    uh = pd.read_parquet(
        KEEPER / f"hourly/unit_hourly_{year}.parquet",
        columns=["pass", "fuel", "zone", "hour", "mw"],
    )
    uh = uh[(uh["pass"] == "P1") & (uh["zone"] == "MISO-South")]
    uh = uh.assign(fam=uh["fuel"].map(_family))
    by = (
        uh.groupby(["fam", "hour"])["mw"]
        .sum()
        .unstack("fam")
        .reindex(range(HOURS))
        .fillna(0.0)
    )
    fams = {c: by[c].to_numpy() for c in by.columns}
    return fams, by.sum(axis=1).to_numpy()


def south_storage_net(year: int) -> np.ndarray:
    st = pd.read_parquet(KEEPER / "storage.parquet")
    st = st[(st["year"] == year)]
    if "pass" in st.columns:
        st = st[st["pass"] == "P1"]
    if "zone" in st.columns:
        st = st[st["zone"] == "MISO-South"]
        g = st.groupby("hour")
        return (
            (g["discharge_mw"].sum() - g["charge_mw"].sum())
            .reindex(range(HOURS))
            .fillna(0)
            .to_numpy()
        )
    return np.zeros(HOURS)


def actual_hubs(year: int) -> tuple[np.ndarray, np.ndarray]:
    zon = pd.read_parquet(ZONAL)
    ind = m207.hub_series(zon, year, "rt")

    def _hub(h: str) -> np.ndarray:
        s = zon[(zon.year == year) & (zon.hub == h)].sort_values("hour")
        arr = np.full(HOURS, np.nan)
        idx = s["hour"].to_numpy(int)
        keep = idx < HOURS
        arr[idx[keep]] = s["rt"].to_numpy(float)[keep]
        return arr

    south = np.nanmean([_hub(h) for h in SOUTH_HUBS], axis=0)
    return ind, south


def _m(x: np.ndarray, idx: np.ndarray) -> float:
    v = np.asarray(x, float)[idx]
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


def _share(idx: np.ndarray, mask: np.ndarray) -> float:
    return float(mask[idx].mean()) if idx.size else float("nan")


# ----------------------------------------------------------------- main
def main() -> None:  # noqa: PLR0915
    m207rec = json.loads(m207.OUT.read_text())["years"]
    m208rec = json.loads(m208.OUT.read_text())["years"]
    cfg0 = keeper_config()
    mon = m207._hour_month()
    jj = np.where(np.isin(mon, (6, 7)))[0]
    hod = np.arange(HOURS) % 24
    rep: dict = {
        "charter": "miso-211 phase 0 — the RDT South->North binding state; zero-solve.",
        "prereg": "results/calibration/PREREG-miso211-rdt-binding-state-2026-09-04.md @ 5320e4dc",
        "keeper": "2026-09-04-miso-210-clock",
        "corridor_in_keeper": {
            "s2n_tiers_mw": [2300.0, 46.0, 154.0],
            "s2n_tier_costs": [0.0, 240.0, 700.0],
            "n2s_tiers_mw": [2760.0, 55.2, 184.8],
        },
        "years": {},
    }

    for year in YEARS:
        y: dict = {}
        price, lw, dem_s, slack_s = zone_prices(year)
        ind_act, south_act = actual_hubs(year)
        cor = corridor(year)
        pbc_s2n = pbc_hourly(year, "RDT_SO_MW")
        pbc_n2s = pbc_hourly(year, "RDT_MW_SO")

        # ---- populations (miso-207/208 verbatim)
        a = ind_act[jj]
        rank = (a.argsort().argsort() / len(a)) * 100.0
        thr99 = float(np.nanpercentile(a, 99.0))
        tail = jj[a >= thr99]
        shoulder = jj[(rank >= 75.0) & (a < thr99)]
        other = np.array(sorted(set(jj) - set(shoulder) - set(tail)))
        day_other = other[np.isin(hod[other], range(10, 21))]
        pops = {"SHOULDER": shoulder, "TAIL": tail, "OTHER_DAYTIME": day_other}
        gaps = {k: _m(lw, v) - _m(ind_act, v) for k, v in pops.items()}
        y["n1_footing"] = {
            "n_tail": int(tail.size),
            "n_shoulder": int(shoulder.size),
            "gap_lw_minus_rt": {k: round(v, 3) for k, v in gaps.items()},
            "m207_gap": {
                k: m207rec[str(year)]["gaps"][k]["gap_lw_minus_rt"]
                for k in ("SHOULDER", "TAIL")
            },
            "real_s2n_any_share": {
                k: round(_share(v, pbc_s2n["any"]), 4) for k, v in pops.items()
            },
            "m208_real_s2n_share": {
                k: (m208rec[str(year)].get("item3_deliverability") or {})
                .get(k if k != "OTHER_DAYTIME" else "OTHER_JJ_DAYTIME", {})
                .get("rdt_south_to_north_binding_share")
                for k in ("SHOULDER", "TAIL", "OTHER_DAYTIME")
            },
        }

        # ---- R-1: the LP corridor in the real S->N binding hours
        lp_s2n_bind = cor["s2n_free_flow"] >= FREE_S2N - BIND_TOL
        lp_n2s_bind = cor["n2s_free_flow"] >= FREE_N2S - BIND_TOL
        lp_n2s_any = cor["n2s_flow"] > BIND_TOL
        lp_s2n_any = cor["s2n_flow"] > BIND_TOL
        spread_ind_s = price["MISO-Indiana"].to_numpy() - price["MISO-South"].to_numpy()
        spread_pl_s = price["MISO-Plains"].to_numpy() - price["MISO-South"].to_numpy()
        r1 = {}
        for k, idx in pops.items():
            rb = idx[pbc_s2n["any"][idx]]
            rbm = idx[pbc_s2n["majority"][idx]]
            r1[k] = {
                "n_hours": int(idx.size),
                "real_s2n_any_hours": int(rb.size),
                "real_s2n_majority_hours": int(rbm.size),
                "real_n2s_any_hours": int(pbc_n2s["any"][idx].sum()),
                "real_s2n_mean_abs_shadow_in_binding_hours": round(
                    _m(pbc_s2n["mean_abs_shadow"], rb), 3
                ),
                "lp_in_real_s2n_hours": {
                    "s2n_flow_mean_mw": round(_m(cor["s2n_flow"], rb), 1),
                    "s2n_flow_p90_mw": round(
                        float(np.percentile(cor["s2n_flow"][rb], 90)), 1
                    )
                    if rb.size
                    else None,
                    "s2n_at_free_tier_share": round(_share(rb, lp_s2n_bind), 4),
                    "s2n_any_flow_share": round(_share(rb, lp_s2n_any), 4),
                    "n2s_any_flow_share": round(_share(rb, lp_n2s_any), 4),
                    "n2s_flow_mean_mw": round(_m(cor["n2s_flow"], rb), 1),
                    "n2s_at_free_tier_share": round(_share(rb, lp_n2s_bind), 4),
                    "s2n_free_dual_mean": round(_m(cor["s2n_free_dual"], rb), 3),
                    "spread_indiana_minus_south_mean": round(_m(spread_ind_s, rb), 3),
                    "spread_plains_minus_south_mean": round(_m(spread_pl_s, rb), 3),
                    "ext_south_flow_mean_mw": round(_m(cor["ext_south_flow"], rb), 1),
                },
                "lp_over_population": {
                    "s2n_at_free_tier_share": round(_share(idx, lp_s2n_bind), 4),
                    "n2s_at_free_tier_share": round(_share(idx, lp_n2s_bind), 4),
                    "n2s_any_flow_share": round(_share(idx, lp_n2s_any), 4),
                    "s2n_flow_mean_mw": round(_m(cor["s2n_flow"], idx), 1),
                    "spread_indiana_minus_south_mean": round(_m(spread_ind_s, idx), 3),
                },
            }
        # whole-year census of LP binding vs real binding
        r1["ANNUAL"] = {
            "real_s2n_any_hours": int(pbc_s2n["any"].sum()),
            "real_n2s_any_hours": int(pbc_n2s["any"].sum()),
            "lp_s2n_at_free_tier_hours": int(lp_s2n_bind.sum()),
            "lp_n2s_at_free_tier_hours": int(lp_n2s_bind.sum()),
            "lp_s2n_binding_AND_real_s2n": int((lp_s2n_bind & pbc_s2n["any"]).sum()),
            "lp_n2s_binding_AND_real_s2n": int((lp_n2s_bind & pbc_s2n["any"]).sum()),
            "lp_s2n_max_dual": round(float(cor["s2n_max_dual"].max()), 2),
        }
        y["r1_corridor"] = r1

        # ---- R-2b: South boundary net, measured vs model; by-fuel decomposition
        load_s = regional_series(year, "load", "South")
        gen_s = regional_series(year, "gen", "South")
        meas_ns = load_s - gen_s  # + = South imports (net intake); - = exports
        model_inflow = cor["n2s_flow"] - cor["s2n_flow"] + cor["ext_south_flow"]
        fams_model, gen_model_s = south_generation(year)
        stor_s = south_storage_net(year)
        # R-2c identity: demand - gen - storage_net - slack = inflow (into-South links)
        resid = dem_s - gen_model_s - stor_s - slack_s - model_inflow
        r2 = {}
        for k, idx in pops.items():
            rb = idx[pbc_s2n["any"][idx]]
            fam_meas = {
                f: regional_series(year, "gen", "South", fuel=f)
                for f in ("Coal", "Gas", "Nuclear", "Hydro", "Wind", "Solar", "Other")
            }
            r2[k] = {
                "hours_real_s2n": int(rb.size),
                "measured_south_net_intake_gw_mean": round(_m(meas_ns, rb) / 1e3, 3),
                "model_south_net_inflow_gw_mean": round(_m(model_inflow, rb) / 1e3, 3),
                "gap_model_minus_measured_gw": round(
                    (_m(model_inflow, rb) - _m(meas_ns, rb)) / 1e3, 3
                ),
                "south_load_gw": {
                    "measured": round(_m(load_s, rb) / 1e3, 3),
                    "model": round(_m(dem_s, rb) / 1e3, 3),
                },
                "south_gen_total_gw": {
                    "measured": round(_m(gen_s, rb) / 1e3, 3),
                    "model": round(_m(gen_model_s, rb) / 1e3, 3),
                },
                "south_gen_by_fuel_gw_model_minus_measured": {
                    f: round(
                        (
                            _m(fams_model.get(f, np.zeros(HOURS)), rb)
                            - _m(fam_meas[f], rb)
                        )
                        / 1e3,
                        3,
                    )
                    for f in fam_meas
                },
                "south_gen_by_fuel_gw_measured": {
                    f: round(_m(fam_meas[f], rb) / 1e3, 3) for f in fam_meas
                },
                "south_gen_by_fuel_gw_model": {
                    f: round(_m(fams_model.get(f, np.zeros(HOURS)), rb) / 1e3, 3)
                    for f in fam_meas
                },
                "whole_population_measured_intake_gw": round(_m(meas_ns, idx) / 1e3, 3),
                "whole_population_model_inflow_gw": round(
                    _m(model_inflow, idx) / 1e3, 3
                ),
            }
        y["r2b_south_boundary"] = r2
        y["r2c_identity"] = {
            "max_abs_residual_mw": round(float(np.nanmax(np.abs(resid))), 3),
            "mean_abs_residual_mw": round(float(np.nanmean(np.abs(resid))), 3),
            "into_south_links": [N2S, S2N, EXT_S],
            "holds_under_1mw": bool(np.nanmax(np.abs(resid)) < 1.0),
        }

        # ---- R-3b: separation ceiling on the scored comparator
        meas_sep = ind_act - south_act
        r3b = {}
        for k, idx in pops.items():
            rb_mask = pbc_s2n["any"][idx]
            lift = np.where(
                rb_mask, np.maximum(0.0, meas_sep[idx] - spread_ind_s[idx]), 0.0
            )
            lift = np.nan_to_num(lift)
            gap = gaps[k]
            r3b[k] = {
                "measured_sep_indiana_minus_south_hubs_mean_in_binding_hours": round(
                    _m(meas_sep, idx[rb_mask]), 3
                ),
                "measured_sep_mean_whole_population": round(_m(meas_sep, idx), 3),
                "model_spread_mean_in_binding_hours": round(
                    _m(spread_ind_s, idx[rb_mask]), 3
                ),
                "pbc_mean_abs_shadow_in_binding_hours": round(
                    _m(pbc_s2n["mean_abs_shadow"], idx[rb_mask]), 3
                ),
                "lift_usd_mean_over_population": round(float(lift.mean()), 3),
                "share_of_gap": round(float(lift.mean()) / abs(gap), 4)
                if gap
                else None,
                "reaches_25pct": bool(gap and float(lift.mean()) / abs(gap) >= LICENSE),
            }
        y["r3b_separation_ceiling"] = r3b

        # ---- R-3a: strand re-measured on the miso-210 keeper (miso-208 engine)
        cfg = dataclasses.replace(cfg0, weather_year=year, mode="backcast")
        _raw, fleet, arrays, _fp, mc, _zn = build_year(cfg, year)
        mc = np.asarray(mc, dtype=np.float64)
        labels = np.array([m207.class_label(g) for g in fleet], dtype=object)
        zones = np.array([str(g.zone) for g in fleet], dtype=object)
        avail = np.asarray(arrays.availability, dtype=np.float64)
        if avail.ndim == 1:
            avail = np.broadcast_to(avail[:, None], (len(fleet), HOURS))
        avail_mw = np.asarray(arrays.pmax, dtype=np.float64)[:, None] * avail
        price_df, _dem = keeper_prices(year)
        price_df = price_df.reindex(range(HOURS))
        r3a = {}
        for k, idx in pops.items():
            per_hour, by_class, by_zone = m208.idle_census(
                idx, mc, avail_mw, labels, zones, price_df
            )
            south_cushion = by_zone.get("MISO-South", np.zeros(idx.size))
            removal = np.where(pbc_s2n["any"][idx], south_cushion, 0.0)
            blk = m208.lift(idx, mc, avail_mw, zones, price_df, removal)
            blk = m208.with_share(blk, gaps[k])
            blk["south_cushion_gw_mean"] = round(float(south_cushion.mean()) / 1e3, 3)
            blk["cushion_total_gw_mean"] = round(float(per_hour.mean()) / 1e3, 3)
            r3a[k] = blk
        y["r3a_strand"] = r3a
        y["r3a_m208_reference"] = {"shoulder": 0.048, "tail": 0.007}

        rep["years"][year] = y
        print(year, "footing", y["n1_footing"], flush=True)
        print(
            year,
            "R-1 shoulder",
            json.dumps(r1["SHOULDER"], default=str)[:900],
            flush=True,
        )
        print(
            year,
            "R-2b shoulder",
            json.dumps(r2["SHOULDER"], default=str)[:900],
            flush=True,
        )
        print(year, "R-2c", y["r2c_identity"], flush=True)
        print(year, "R-3b", json.dumps(r3b, default=str)[:900], flush=True)
        print(
            year,
            "R-3a",
            json.dumps(
                {k: (v["share_of_gap"], v["lift_usd_mean"]) for k, v in r3a.items()}
            ),
            flush=True,
        )

    OUT.write_text(json.dumps(rep, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
