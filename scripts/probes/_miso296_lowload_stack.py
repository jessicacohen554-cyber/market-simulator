#!/usr/bin/env python3
"""miso-296 (ZERO LP): who sets MISO's low-load price in the model, and who in reality?

Owner ruling 2026-10-01 (miso-295 card: "C3a 2020 low-load stack (Recommended)").
C3a 2020 reads +11.6 % on the zone-resolved basis (miso-294), and in every year
the model prices $3-7 above actual in load quintiles 1-4. miso-295 settled that
this is not coal inventory. This probe asks the next question at zero LP: at low
load, which class is marginal in the model, which in reality (IMM SOM Table 1),
and what the marginal offer is made of.

Blocks (all measured; nothing here feeds a solve, rule 13):

A. Price gap by load quintile, hour block and actual-price band. Model = keeper P1
   zonal price; actual = zone-resolved hub series (the miso-294 scorer basis);
   both weighted by the measured zonal demand. Each band reports n, means and its
   contribution to the annual load-weighted error, so bands sum to the total.
B. Marginal class census. Fleet-only rebuild of the keeper recipe; the base-cost
   (P0) stack and the P1 bid stack (base + startup markup, the miso-287
   construction) cleared at the keeper's P1 thermal quantity every hour. Shares
   of the marginal row by class family, all hours and per quintile, beside the
   IMM's published SMP price-setting shares (SOM Table 1, 2019-2024).
C. Marginal offer anatomy in the low-load hours (quintiles 1-2): heat rate, fuel
   print, VOM, residual (sigmoid / adders), and the Chicago Citygate flow-day hub
   price the same day, so the fuel-convention wedge at the margin is a number.
   Coal position: the cheapest undispatched coal econ offer minus the clearing
   price, and the coal econ offer anatomy.
D. Quantities in the low-load hours: model vs EIA-930 by fuel and interchange,
   model vs CAMPD by keeper class, model dump/slack, wind vs its bound.
E. Coal band composition in the low-load hours (mustrun / committed / econ).

Output: ``results/phase0/miso/_miso296_lowload_stack.json``.

Usage (repo root, so ``scripts`` is importable and load_demand finds its data)::

    uv run python scripts/probes/_miso296_lowload_stack.py --bench-pkl <frames.pkl>
"""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso287_p1_residual import clear_all, run_ratio  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
ZONAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
OUT = REPO / "results/phase0/miso/_miso296_lowload_stack.json"
T = 8760
YEARS = tuple(range(2019, 2026))
NON_LP = ("wind", "solar", "biomass", "OTHER")
PLAINS_PROXY = ("MINN.HUB", "ILLINOIS.HUB")
INTERNAL = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]
COAL = ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB")
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
CAMPD_CLASSES = [
    "COAL_BIT",
    "COAL_LIGNITE",
    "COAL_PRB",
    "CC_REGULAR",
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "ST_GAS",
    "CT_PEAKER",
    "OTHER",
]
SERIES = {
    **{k: "coal" for k in COAL},
    **{k: "gas" for k in GAS},
    "nuclear": "nuclear",
    "wind": "wind",
    "solar": "solar",
    "hydro": "hydro",
    "oil": "other",
    "biomass": "other",
    "OTHER": "other",
    "import": "interchange",
}
#: Potomac Economics, MISO State of the Market Reports, Table 1 "Capacity, Energy
#: Output, and Price-Setting by Fuel Type", SMP column (share of real-time
#: intervals each fuel set the system marginal price). PDF page 6 of each report
#: body: 2020 SOM (2019/2020 columns), 2022 SOM (2021/2022), 2023 SOM (2022/2023),
#: 2024 SOM (2023/2024). Cited, not a model input (rule 13).
IMM_SMP_SHARE = {
    2019: {"coal": 0.47, "gas": 0.51, "wind": 0.01, "hydro": 0.01, "other": 0.00},
    2020: {"coal": 0.40, "gas": 0.57, "wind": 0.01, "hydro": 0.01, "other": 0.00},
    2021: {"coal": 0.35, "gas": 0.64, "wind": 0.00, "hydro": 0.01, "other": 0.00},
    2022: {"coal": 0.24, "gas": 0.75, "wind": 0.00, "hydro": 0.01, "other": 0.00},
    2023: {"coal": 0.36, "gas": 0.63, "wind": 0.00, "hydro": 0.01, "other": 0.00},
    2024: {"coal": 0.36, "gas": 0.63, "wind": 0.00, "hydro": 0.01, "other": 0.00},
}


def _r(x, k=2):
    """Round a float for the JSON record."""
    return (
        None
        if x is None or (isinstance(x, float) and np.isnan(x))
        else round(float(x), k)
    )


def zone_actual(year: int) -> np.ndarray:
    """Zone-resolved actual RT price ``(6, T)`` in INTERNAL order (miso-294 basis)."""
    z = pd.read_parquet(ZONAL)
    z = z[z["year"] == year]
    hubs: dict[str, np.ndarray] = {}
    zone_hubs: dict[str, set] = {}
    for (hub, zone), g in z.groupby(["hub", "zone"]):
        zone_hubs.setdefault(zone, set()).add(hub)
        dense = np.full(T, np.nan)
        hr = g["hour"].to_numpy(int)
        ok = hr < T
        dense[hr[ok]] = g["rt"].to_numpy(float)[ok]
        hubs[hub] = dense
    zone_hubs["MISO-Plains"] = set(PLAINS_PROXY)
    return np.vstack(
        [
            np.nanmean(np.vstack([hubs[h] for h in sorted(zone_hubs[zn])]), axis=0)
            for zn in INTERNAL
        ]
    )


def family(label: str) -> str:
    """Marginal-row label -> IMM fuel family."""
    grp = label.split("|")[0]
    if grp == "":
        return "seam"
    if grp.startswith("COAL"):
        return "coal"
    if grp in GAS:
        return "gas"
    return grp.lower()


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--bench-pkl", required=True, help="pickled build_benchmark_frames dict"
    )
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    args = ap.parse_args()
    from scripts.data import derive_actual_lmp as dal  # noqa: E402
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.fuel.hubs import (
        _flow_date_staircase,
        _miso_citygate_daily_dated,
    )
    from market_sim.model.commitment import compute_monthly_markup

    dec.KEEPER = KEEPER
    fr = pickle.load(open(args.bench_pkl, "rb"))
    e923, campd, e930 = fr["eia923"], fr["campd"], fr["eia930"]
    chi_all = _miso_citygate_daily_dated(None)
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    hod = np.arange(T) % 24
    night = hod < 6
    for y in args.years:
        yo: dict = {}
        # ---------------- A. price gap by band (zone-resolved, demand-weighted)
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        dump = s.pivot(index="hour", columns="zone", values="dump").sort_index()[
            INTERNAL
        ]
        slack = s.pivot(index="hour", columns="zone", values="slack").sort_index()[
            INTERNAL
        ]
        pm = pz[INTERNAL].to_numpy().T  # (6, T)
        pa = zone_actual(y)
        w = dal._measured_zone_demand("MISO", y)  # (6, T) measured zonal demand
        assert w is not None and w.shape == (6, T), w.shape
        ok = ~np.isnan(pa).any(axis=0)
        wt = np.where(ok, w.sum(axis=0), 0.0)
        lw_m = (pm * w).sum(0) / w.sum(0)  # hourly system load-weighted model price
        lw_a = (pa * w).sum(0) / w.sum(0)
        err = lw_m - lw_a
        tot_w = wt.sum()
        ann_m = float((lw_m[ok] * wt[ok]).sum() / tot_w)
        ann_a = float((lw_a[ok] * wt[ok]).sum() / tot_w)
        load = w.sum(axis=0)
        q5 = pd.qcut(load, 5, labels=False)

        def band(mask):
            mk = mask & ok
            ww = wt[mk]
            if ww.sum() <= 0:
                return {"n": int(mk.sum())}
            return {
                "n": int(mk.sum()),
                "actual_lw": _r((lw_a[mk] * ww).sum() / ww.sum()),
                "model_lw": _r((lw_m[mk] * ww).sum() / ww.sum()),
                "err_lw": _r((err[mk] * ww).sum() / ww.sum()),
                "contrib_to_annual_err": _r((err[mk] * ww).sum() / tot_w),
                "actual_p10": _r(np.percentile(lw_a[mk], 10)),
                "model_p10": _r(np.percentile(lw_m[mk], 10)),
                "actual_median": _r(np.median(lw_a[mk])),
                "model_median": _r(np.median(lw_m[mk])),
            }

        yo["price"] = {
            "coverage_hours": int(ok.sum()),
            "annual_lw": {
                "model": _r(ann_m),
                "actual": _r(ann_a),
                "err": _r(ann_m - ann_a),
                "pct": _r(100 * (ann_m - ann_a) / ann_a),
            },
            "by_load_quintile": {f"q{i + 1}": band(q5 == i) for i in range(5)},
            "night_h0_5": band(night),
            "day_h6_23": band(~night),
            "q12_night": band((q5 <= 1) & night),
            "q12_day": band((q5 <= 1) & ~night),
            "actual_band": {
                "lt_0": band(lw_a < 0),
                "lt_5": band(lw_a < 5),
                "lt_10": band(lw_a < 10),
                "lt_15": band(lw_a < 15),
                "lt_20": band(lw_a < 20),
                "ge_20": band(lw_a >= 20),
            },
            "share_hours_lt": {
                f"{k}": {
                    "actual": _r((lw_a[ok] < k).mean(), 4),
                    "model": _r((lw_m[ok] < k).mean(), 4),
                }
                for k in (0, 5, 10, 15, 20)
            },
            "zone_err_lw": {
                zn: _r(((pm[i] - pa[i])[ok] * w[i][ok]).sum() / w[i][ok].sum())
                for i, zn in enumerate(INTERNAL)
            },
            "quintile_load_edges_gw": [
                _r(np.percentile(load, p) / 1e3, 1) for p in (0, 20, 40, 60, 80, 100)
            ],
        }
        # ---------------- B. stack rebuild and marginal census
        hh = _henry_hub_actual(_load_reference(), y)
        st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, {}))
        cfg, fa, fleet = st["config"], st["fleet_arrays"], st["fleet"]
        n = len(fa.pmax)
        mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
        if mc.shape[1] == 1:
            mc = np.repeat(mc, T, axis=1)
        fp = np.asarray(st["fuel_prices"], dtype=float).reshape(n, -1)
        if fp.shape[1] == 1:
            fp = np.repeat(fp, T, axis=1)
        pmax = np.asarray(fa.pmax, float)
        cap = pmax[:, None] * np.asarray(fa.availability, float)
        mg = np.minimum(np.asarray(fa.min_gen, float), cap)
        flex = cap - mg
        hr = np.asarray(fa.heat_rate, float)
        vom = np.asarray(fa.vom, float)
        grp = np.asarray(fa.plant_group).astype(str)
        uid = np.asarray(list(fa.unit_ids)).astype(str)
        bandn = np.array([u.rsplit("_", 1)[-1] if "_" in u else "?" for u in uid])
        fam = np.where(np.char.startswith(bandn, "econ"), "econ", bandn)
        lab = np.char.add(np.char.add(grp, "|"), fam)
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        chl = ch[~ch.klass.astype(str).isin(NON_LP)]
        q = chl.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        p0, m0, d0 = clear_all(mc, mg, flex, q)
        mk = compute_monthly_markup(
            fleet,
            fa,
            d0,
            T,
            gas_st_season_spread=cfg.gas_st_startup_spread,
            gas_st_startup_cost=getattr(cfg, "gas_st_startup_cost", False),
            chp_startup_covered=getattr(cfg, "chp_startup_covered", False),
            coal_warm_committed=getattr(cfg, "coal_warm_committed", False),
            run_ratio_t=run_ratio(st)
            if getattr(cfg, "tranche_startup_conditional_runs", False)
            else None,
        )
        p1b, m1, d1 = clear_all(mc + mk, mg, flex, q)
        famv = np.vectorize(family)

        def census(marg, mask):
            v = pd.Series(famv(lab[marg[mask]])).value_counts(normalize=True)
            return {k: _r(x, 3) for k, x in v.items()}

        def census_lab(marg, mask, top=8):
            v = pd.Series(lab[marg[mask]]).value_counts(normalize=True)
            return {k: _r(x, 3) for k, x in v.head(top).items()}

        allm = np.ones(T, bool)
        yo["marginal"] = {
            "imm_smp_share": IMM_SMP_SHARE.get(y),
            "p0_stack_all_hours": census(m0, allm),
            "bid_stack_all_hours": census(m1, allm),
            "p0_stack_by_quintile": {
                f"q{i + 1}": census(m0, q5 == i) for i in range(5)
            },
            "bid_stack_by_quintile": {
                f"q{i + 1}": census(m1, q5 == i) for i in range(5)
            },
            "p0_stack_night": census(m0, night),
            "p0_stack_q12_labels": census_lab(m0, q5 <= 1),
            "bid_stack_q12_labels": census_lab(m1, q5 <= 1),
            "stack_vs_p1_median": {
                f"q{i + 1}": {
                    "p1": _r(np.median(lw_m[q5 == i])),
                    "p0_stack": _r(np.nanmedian(p0[q5 == i])),
                    "bid_stack": _r(np.nanmedian(p1b[q5 == i])),
                    "actual": _r(np.median(lw_a[(q5 == i) & ok])),
                }
                for i in range(5)
            },
        }
        # ---------------- C. marginal offer anatomy, low-load hours (q1-q2)
        chi = _flow_date_staircase(chi_all.get(y, {}), y)
        chi = np.asarray(chi, float) if chi is not None else np.full(365, np.nan)
        if chi.shape[0] <= 366:
            chi_h = np.repeat(chi, 24)[:T]
        else:
            chi_h = chi[:T]
        low = (q5 <= 1) & ok
        tt = np.arange(T)
        rows = pd.DataFrame(
            {
                "hour": tt,
                "lab": lab[m1],
                "fam": famv(lab[m1]),
                "grp": grp[m1],
                "band": fam[m1],
                "mc_bid": (mc + mk)[m1, tt],
                "mc_base": mc[m1, tt],
                "markup": mk[m1, tt],
                "hr": hr[m1],
                "fuel": fp[m1, tt],
                "vom": vom[m1],
                "chi": chi_h,
                "p1_lw": lw_m,
                "act_lw": lw_a,
            }
        )
        rows["resid"] = rows.mc_base - rows.hr * rows.fuel - rows.vom
        rows["wedge"] = rows.fuel - rows.chi
        rows["wedge_mwh"] = rows.wedge * rows.hr
        lowr = rows[low]

        def anat(df):
            if len(df) == 0:
                return {"n": 0}
            return {
                "n": int(len(df)),
                "mc_bid_med": _r(df.mc_bid.median()),
                "mc_base_med": _r(df.mc_base.median()),
                "markup_med": _r(df.markup.median()),
                "hr_med": _r(df.hr.median(), 3),
                "fuel_print_med": _r(df.fuel.median(), 3),
                "chicago_hub_med": _r(df.chi.median(), 3),
                "wedge_mmbtu_med": _r(df.wedge.median(), 3),
                "wedge_mwh_med": _r(df.wedge_mwh.median()),
                "wedge_mwh_mean": _r(df.wedge_mwh.mean()),
                "vom_med": _r(df.vom.median()),
                "resid_med": _r(df.resid.median()),
                "p1_minus_actual_mean": _r((df.p1_lw - df.act_lw).mean()),
                "p1_minus_actual_med": _r((df.p1_lw - df.act_lw).median()),
                "bid_minus_actual_med": _r((df.mc_bid - df.act_lw).median()),
            }

        yo["anatomy_q12"] = {
            "all_marginal": anat(lowr),
            "cc_regular_marginal": anat(lowr[lowr.grp == "CC_REGULAR"]),
            "cc_regular_econ_marginal": anat(
                lowr[(lowr.grp == "CC_REGULAR") & (lowr.band == "econ")]
            ),
            "coal_marginal": anat(lowr[lowr.fam == "coal"]),
            "seam_marginal": anat(lowr[lowr.fam == "seam"]),
            "gas_rows_q12_all": {
                "fuel_print_cap_wtd": _r(
                    float(
                        (
                            fp[np.isin(grp, GAS)][:, low]
                            * cap[np.isin(grp, GAS)][:, low]
                        ).sum()
                        / cap[np.isin(grp, GAS)][:, low].sum()
                    ),
                    3,
                ),
                "cc_regular_fuel_print_cap_wtd": _r(
                    float(
                        (
                            fp[grp == "CC_REGULAR"][:, low]
                            * cap[grp == "CC_REGULAR"][:, low]
                        ).sum()
                        / cap[grp == "CC_REGULAR"][:, low].sum()
                    ),
                    3,
                ),
                "chicago_hub_mean": _r(np.nanmean(chi_h[low]), 3),
                "henry_hub_annual": _r(hh, 3),
            },
        }
        # coal position in q1-q2: cheapest undispatched coal econ MW offer vs clearing price
        coal_econ = np.isin(grp, COAL) & (fam == "econ")
        head = []
        coal_anat = []
        for t in np.where(low)[0]:
            undis = coal_econ & (d1[:, t] < cap[:, t] - 1.0) & (cap[:, t] > 1.0)
            if undis.any():
                o = (mc + mk)[undis, t]
                head.append(float(o.min() - p1b[t]))
            i = np.where(coal_econ & (cap[:, t] > 1.0))[0]
            if len(i):
                ww = cap[i, t]
                coal_anat.append(
                    [
                        float((mc[i, t] * ww).sum() / ww.sum()),
                        float((hr[i] * ww).sum() / ww.sum()),
                        float((fp[i, t] * ww).sum() / ww.sum()),
                        float((vom[i] * ww).sum() / ww.sum()),
                    ]
                )
        ca = np.array(coal_anat)
        yo["coal_position_q12"] = {
            "cheapest_undispatched_coal_econ_minus_price_med": _r(np.median(head))
            if head
            else None,
            "cheapest_undispatched_coal_econ_minus_price_p25": _r(
                np.percentile(head, 25)
            )
            if head
            else None,
            "coal_econ_offer_cap_wtd": {
                "mc_base": _r(ca[:, 0].mean()),
                "hr": _r(ca[:, 1].mean(), 3),
                "fuel_print": _r(ca[:, 2].mean(), 3),
                "vom": _r(ca[:, 3].mean()),
                "resid": _r((ca[:, 0] - ca[:, 1] * ca[:, 2] - ca[:, 3]).mean()),
            },
            "coal_econ_dispatched_share_of_cap_q12": _r(
                float(d1[coal_econ][:, low].sum() / cap[coal_econ][:, low].sum()), 3
            ),
        }
        # ---------------- D. quantities, low-load hours
        ch2 = ch.copy()
        ch2["series"] = ch2.klass.astype(str).map(SERIES).fillna("other")
        m = ch2.pivot_table(index="hour", columns="series", values="mw", aggfunc="sum")
        m = m.reindex(range(T)).fillna(0.0)
        a = (
            e930[e930.year == y]
            .pivot(index="hour", columns="series", values="mw")
            .reindex(range(T))
        )
        rows_q: dict = {}
        for ser in [
            "coal",
            "gas",
            "nuclear",
            "wind",
            "solar",
            "hydro",
            "other",
            "interchange",
        ]:
            mv = m[ser].to_numpy() if ser in m else np.zeros(T)
            av = a[ser].to_numpy() if ser in a else np.full(T, np.nan)
            okk = low & ~np.isnan(av)
            rows_q[ser] = {
                "model": _r(mv[okk].mean(), 0),
                "e930": _r(av[okk].mean(), 0),
                "diff": _r((mv - av)[okk].mean(), 0),
            }
        if "demand" in a:
            av = a["demand"].to_numpy()
            okk = low & ~np.isnan(av)
            rows_q["demand"] = {
                "model": _r(load[okk].mean(), 0),
                "e930": _r(av[okk].mean(), 0),
            }
        wind_bound = (st["wind_cap"][:, None] * st["wind_cf"]).sum(axis=0)
        wind_model = m["wind"].to_numpy() if "wind" in m else np.zeros(T)
        cls = (
            e923[(e923.year == y) & e923.klass.isin(CAMPD_CLASSES)]
            .sort_values("annual_mwh", ascending=False)
            .drop_duplicates("plant_id")
            .set_index("plant_id")
            .klass
        )
        c = campd[campd.year == y]
        c = c[c.plant_id.isin(cls.index)]
        c = c.assign(klass=cls.reindex(c.plant_id.to_numpy()).to_numpy())
        c = c[c.hour.isin(np.where(low)[0])]
        act = c.groupby("klass").net_mw.sum() / low.sum()
        mod = (
            ch[ch.hour.isin(np.where(low)[0])].groupby("klass", observed=True).mw.sum()
            / low.sum()
        )
        yo["quantity_q12"] = {
            "n_hours": int(low.sum()),
            "e930": rows_q,
            "campd_by_class": {
                k: {
                    "model": _r(mod.get(k, 0), 0),
                    "campd": _r(act.get(k, 0), 0),
                    "diff": _r(mod.get(k, 0) - act.get(k, 0), 0),
                }
                for k in CAMPD_CLASSES
            },
            "model_dump_mw_mean": _r(dump.to_numpy().sum(1)[low].mean(), 1),
            "model_slack_mw_mean": _r(slack.to_numpy().sum(1)[low].mean(), 1),
            "hours_with_dump": int((dump.to_numpy().sum(1)[low] > 1).sum()),
            "wind_model_minus_bound_mw_mean": _r(
                (wind_model - wind_bound)[low].mean(), 0
            ),
            "wind_curtailed_hours": int(((wind_bound - wind_model)[low] > 1).sum()),
        }
        # ---------------- E. coal band composition, low-load hours
        cb = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & cb.hour.isin(np.where(low)[0])]
        cb = cb[cb.klass.astype(str).isin(COAL)]
        cb["bandf"] = cb.band.astype(str).str.replace(r"^econ.*$", "econ", regex=True)
        bb = cb.groupby("bandf").mw.sum() / low.sum()
        yo["coal_bands_q12_mw"] = {k: _r(v, 0) for k, v in bb.items()}
        yo["coal_bands_q12_mw"]["total"] = _r(bb.sum(), 0)
        # cross-check: night census for continuity with miso-285/287
        yo["night_p0_stack_median"] = _r(np.nanmedian(p0[night]))
        out[str(y)] = yo
        print(
            y,
            json.dumps(yo["price"]["annual_lw"]),
            json.dumps(yo["marginal"]["p0_stack_by_quintile"]["q1"]),
            flush=True,
        )
        OUT.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
