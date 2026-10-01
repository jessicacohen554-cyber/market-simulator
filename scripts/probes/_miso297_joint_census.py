#!/usr/bin/env python3
"""miso-297 (ZERO LP): identify the coal econ band multiplier from the IMM census.

Owner rulings 2026-10-01 (miso-296 decision cards): "PRECOMMIT the joint arm"
(gas at hub + variable transport PLUS a coal econ band multiplier through the
authorized channel, rule 1 (a)-(e)) and "IMM marginal-share census" as the
identification: the multiplier is the value at which the rebuilt stack's coal
price-setting share matches the IMM SOM Table 1 coal SMP share, pooled over the
six published years 2019-2024. A structural statistic, not a gate (rule 1 (c)).

What this does, per year 2019-2025, all at zero LP:

1. Rebuilds the keeper fleet (``fleet_only``) twice: the keeper recipe, and the
   keeper recipe with ``miso_gas_marginal_commodity_pricing`` +
   ``miso_gas_variable_transport`` armed (the owner-ruled gas form; the hub
   staircases and the per-plant variable wedge come from the production
   applier, nothing is re-implemented here).
2. Scales the fuel component of every coal ``econ`` tranche by ``m`` (the band
   multiplier scales the tranche heat rate, offer_curves.py / assembly.py, so
   ``offer(m) = offer - hr * fuel * (1 - m)`` exactly). ``committed`` and
   ``peak`` do not move (PRECOMMIT s2 says why).
3. Clears the P0 base stack and the P1 bid stack (base + the miso-287 startup
   markup, recomputed from each P0 clear) at the keeper's own P1 thermal
   quantity every hour, for every ``m`` on the grid, on two legs: coal-only
   (keeper gas) and joint (ruled gas). Gas-only is the joint leg at m = 1; the
   keeper is the coal-only leg at m = 1 (reproduces miso-296 block B).
4. Reports the marginal-row family census (coal / gas / seam / other), all hours
   and by load quintile, the coal econ dispatched share, the family dispatch,
   and the static price (q1-q2 medians, load-weighted mean) for every (leg, m).
5. Pools 2019-2024 (hours-weighted = the equal-year mean on the 8760 clock) and
   reads the declared ``m*`` where the joint leg's pooled bid-stack coal share
   crosses the pooled IMM share, descending from m = 1 (first crossing),
   linearly interpolated between grid points and rounded to 2 decimals.
6. Transport-table coverage of the gas fleet per year (own-plant rung vs the
   pooled rungs), since the table was derived on 2023-2025 receipts.

Output: ``results/phase0/miso/_miso297_joint_census.json``.

Usage (repo root)::

    uv run python scripts/probes/_miso297_joint_census.py [--years ...] [--grid ...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso287_p1_residual import run_ratio  # noqa: E402
from scripts.probes._miso296_lowload_stack import (  # noqa: E402
    COAL,
    GAS,
    IMM_SMP_SHARE,
    INTERNAL,
    KEEPER,
    NON_LP,
    T,
    YEARS,
    family,
    zone_actual,
)

OUT = REPO / "results/phase0/miso/_miso297_joint_census.json"
ARM_FLIPS = {
    "miso_gas_marginal_commodity_pricing": True,
    "miso_gas_variable_transport": True,
}
POOL_YEARS = (2019, 2020, 2021, 2022, 2023, 2024)
#: Pooling rule (fixed before any number): hours-weighted over the six
#: published years; every model year is 8760 hours, so this is the equal-year
#: mean of the IMM Table 1 coal SMP shares.
IMM_POOLED_COAL = float(np.mean([IMM_SMP_SHARE[y]["coal"] for y in POOL_YEARS]))
DEFAULT_GRID = [round(x, 2) for x in np.arange(1.00, 0.299, -0.05)]
CHUNK = 730  # hours per vectorized clear block (memory bound)


def _r(x, k=3):
    """Round for the JSON record."""
    return (
        None
        if x is None or (isinstance(x, float) and np.isnan(x))
        else round(float(x), k)
    )


def clear_vec(mc, mg, flex, q):
    """Vectorized merit clear at quantity ``q`` per hour.

    Same construction as ``_miso287_p1_residual.clear_all`` (stable argsort of
    the offer, min_gen as the price-taking base, the marginal row is the first
    row whose cumulative flexible capacity reaches ``q``); returns
    ``(price, marginal_row, dispatch)``.
    """
    n, TT = mc.shape
    price = np.empty(TT)
    marg = np.empty(TT, dtype=int)
    disp = np.empty((n, TT), dtype=np.float32)
    rows = np.arange(n)[:, None]
    for a in range(0, TT, CHUNK):
        b = min(TT, a + CHUNK)
        m = mc[:, a:b]
        o = np.argsort(m, axis=0, kind="stable")
        base = mg[:, a:b].sum(axis=0)
        cum = base[None, :] + np.cumsum(np.take_along_axis(flex[:, a:b], o, 0), 0)
        k = np.minimum((cum < q[None, a:b]).sum(axis=0), n - 1)
        cols = np.arange(b - a)
        mrow = o[k, cols]
        price[a:b] = m[mrow, cols]
        marg[a:b] = mrow
        rank = np.empty_like(o)
        np.put_along_axis(rank, o, np.broadcast_to(rows, o.shape), 0)
        d = mg[:, a:b] + flex[:, a:b] * (rank < k[None, :])
        prev = np.where(k > 0, cum[np.maximum(k - 1, 0), cols], base)
        d[mrow, cols] += np.maximum(0.0, q[a:b] - prev)
        disp[:, a:b] = d
    return price, marg, disp


def rebuild(y, hh, flips):
    """Fleet-only rebuild -> dict of arrays the census needs."""
    from scripts.run_calibration import run_year  # type: ignore

    st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, flips))
    cfg, fa = st["config"], st["fleet_arrays"]
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
    grp = np.asarray(fa.plant_group).astype(str)
    uid = np.asarray(list(fa.unit_ids)).astype(str)
    bandn = np.array([u.rsplit("_", 1)[-1] if "_" in u else "?" for u in uid])
    fam = np.where(np.char.startswith(bandn, "econ"), "econ", bandn)
    return {
        "st": st,
        "cfg": cfg,
        "fa": fa,
        "mc": mc,
        "fp": fp,
        "cap": cap,
        "mg": mg,
        "flex": cap - mg,
        "hr": np.asarray(fa.heat_rate, float),
        "vom": np.asarray(fa.vom, float),
        "grp": grp,
        "band": bandn,
        "fam": fam,
        "lab": np.char.add(np.char.add(grp, "|"), fam),
        "plant": np.asarray(fa.plant_code) if fa.plant_code is not None else None,
        "fuel_idx": np.asarray(fa.fuel_type_idx),
    }


def markup_for(b, d0):
    """The miso-287 P1 startup markup from a P0 dispatch."""
    from market_sim.model.commitment import compute_monthly_markup

    cfg, fa = b["cfg"], b["fa"]
    return compute_monthly_markup(
        b["st"]["fleet"],
        fa,
        d0.astype(float),
        T,
        gas_st_season_spread=cfg.gas_st_startup_spread,
        gas_st_startup_cost=getattr(cfg, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(cfg, "chp_startup_covered", False),
        coal_warm_committed=getattr(cfg, "coal_warm_committed", False),
        run_ratio_t=run_ratio(b["st"])
        if getattr(cfg, "tranche_startup_conditional_runs", False)
        else None,
    )


def transport_coverage(b):
    """Share of gas capacity priced by its own measured transport rung."""
    from market_sim.data.fuel.basis.miso import _load_miso_gas_variable_transport

    by_plant, _, _, _ = _load_miso_gas_variable_transport()
    gas = np.isin(b["grp"], GAS)
    if b["plant"] is None:
        return {"own_plant_cap_share": None}
    own = np.array([int(p) in by_plant for p in b["plant"]])
    capm = b["cap"].mean(axis=1)
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fuel.basis.miso import _miso_gas_variable_transport_vector

    zn = tuple(get_iso_config("MISO").zone_names)
    v = np.zeros(len(capm))
    gi = np.nonzero(gas)[0]
    v[gi] = _miso_gas_variable_transport_vector(b["fa"], gi, zn)
    out = {
        "gas_cap_gw": _r(capm[gas].sum() / 1e3, 2),
        "own_plant_cap_share": _r(capm[gas & own].sum() / capm[gas].sum()),
        "n_gas_plants": int(len(set(b["plant"][gas].tolist()))),
        "n_gas_plants_own": int(len(set(b["plant"][gas & own].tolist()))),
        "by_group": {},
    }
    for g in GAS:
        sel = b["grp"] == g
        if capm[sel].sum() <= 0:
            continue
        out["by_group"][g] = {
            "cap_gw": _r(capm[sel].sum() / 1e3, 2),
            "own_plant_cap_share": _r(capm[sel & own].sum() / capm[sel].sum()),
            "v_cap_wtd": _r((v[sel] * capm[sel]).sum() / capm[sel].sum()),
        }
    out["v_cap_wtd_all_gas"] = _r((v[gas] * capm[gas]).sum() / capm[gas].sum())
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--grid", type=float, nargs="+", default=DEFAULT_GRID)
    ap.add_argument("--no-pool", action="store_true", help="skip the pooled read")
    args = ap.parse_args()
    from scripts.data import derive_actual_lmp as dal  # noqa: E402
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    grid = [round(float(m), 2) for m in args.grid]
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    out["_rule"] = {
        "pooling": "hours-weighted over 2019-2024 = equal-year mean (8760 h each)",
        "imm_pooled_coal": _r(IMM_POOLED_COAL, 4),
        "identification": "joint leg, P1 bid stack, all hours; first crossing of "
        "the pooled IMM coal share descending from m = 1.00; linear interpolation "
        "between grid points; rounded to 2 decimals",
        "bands_scaled": "coal econ_low + econ_high (fuel component x m); "
        "committed and peak unchanged",
        "grid": grid,
    }
    famv = np.vectorize(family)
    for y in args.years:
        t0 = time.time()
        yo: dict = {}
        hh = _henry_hub_actual(_load_reference(), y)
        legs = {
            "coal_only": rebuild(y, hh, {}),
            "joint": rebuild(y, hh, ARM_FLIPS),
        }
        b0, b1 = legs["coal_only"], legs["joint"]
        # --- identity checks: only gas rows move between the legs
        gas = np.isin(b0["grp"], GAS)
        non_gas_same = bool(np.allclose(b0["mc"][~gas], b1["mc"][~gas]))
        cce = (b0["grp"] == "CC_REGULAR") & (b0["fam"] == "econ")
        dmc = (b1["mc"] - b0["mc"])[cce]
        dfc = (b0["hr"][:, None] * (b1["fp"] - b0["fp"]))[cce]
        yo["gas_leg_identity"] = {
            "non_gas_rows_identical": non_gas_same,
            "cc_regular_econ_mc_delta_equals_hr_x_fuel_delta_max_abs_err": _r(
                np.abs(dmc - dfc).max()
            ),
            "gas_fuel_cap_wtd_keeper": _r(
                (b0["fp"][gas] * b0["cap"][gas]).sum() / b0["cap"][gas].sum()
            ),
            "gas_fuel_cap_wtd_ruled": _r(
                (b1["fp"][gas] * b1["cap"][gas]).sum() / b1["cap"][gas].sum()
            ),
            "cc_regular_fuel_cap_wtd_keeper": _r(
                (
                    b0["fp"][b0["grp"] == "CC_REGULAR"]
                    * b0["cap"][b0["grp"] == "CC_REGULAR"]
                ).sum()
                / b0["cap"][b0["grp"] == "CC_REGULAR"].sum()
            ),
            "cc_regular_fuel_cap_wtd_ruled": _r(
                (
                    b1["fp"][b1["grp"] == "CC_REGULAR"]
                    * b1["cap"][b1["grp"] == "CC_REGULAR"]
                ).sum()
                / b1["cap"][b1["grp"] == "CC_REGULAR"].sum()
            ),
            "n_rows": int(b0["mc"].shape[0]),
        }
        yo["transport_coverage"] = transport_coverage(b1)
        # --- coal econ anatomy (keeper leg): resid must be ~0 for the scaling identity
        coal_econ = np.isin(b0["grp"], COAL) & (b0["fam"] == "econ")
        fc0 = b0["hr"][:, None] * b0["fp"]
        resid = (b0["mc"] - fc0 - b0["vom"][:, None])[coal_econ]
        capce = b0["cap"][coal_econ]
        yo["coal_econ_anatomy"] = {
            "n_rows": int(coal_econ.sum()),
            "bands": {
                k: int(v)
                for k, v in pd.Series(b0["band"][np.isin(b0["grp"], COAL)])
                .value_counts()
                .items()
            },
            "cap_gw_mean": _r(capce.mean(axis=1).sum() / 1e3, 2),
            "offer_cap_wtd": _r((b0["mc"][coal_econ] * capce).sum() / capce.sum()),
            "fuel_component_cap_wtd": _r((fc0[coal_econ] * capce).sum() / capce.sum()),
            "vom_cap_wtd": _r((b0["vom"][coal_econ, None] * capce).sum() / capce.sum()),
            "resid_cap_wtd": _r((resid * capce).sum() / capce.sum()),
            "resid_max_abs": _r(np.abs(resid).max()),
        }
        # --- quantity, demand weights, quintiles, actual
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        chl = ch[~ch.klass.astype(str).isin(NON_LP)]
        q = chl.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        w = dal._measured_zone_demand("MISO", y)
        assert w is not None and w.shape == (6, T), w.shape
        load = w.sum(axis=0)
        q5 = pd.qcut(load, 5, labels=False)
        pa = zone_actual(y)
        ok = ~np.isnan(pa).any(axis=0)
        lw_a = (pa * w).sum(0) / w.sum(0)
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        pz = s.pivot(index="hour", columns="zone", values="price").sort_index()
        pm = pz[INTERNAL].to_numpy().T
        lw_m = (pm * w).sum(0) / w.sum(0)
        wt = np.where(ok, load, 0.0)
        yo["reference"] = {
            "actual_lw_mean": _r((lw_a[ok] * wt[ok]).sum() / wt.sum()),
            "keeper_p1_lw_mean": _r((lw_m[ok] * wt[ok]).sum() / wt.sum()),
            "actual_q1_median": _r(np.median(lw_a[(q5 == 0) & ok])),
            "actual_q2_median": _r(np.median(lw_a[(q5 == 1) & ok])),
            "keeper_p1_q1_median": _r(np.median(lw_m[q5 == 0])),
            "keeper_p1_q2_median": _r(np.median(lw_m[q5 == 1])),
            "coverage_hours": int(ok.sum()),
            "imm_smp_share": IMM_SMP_SHARE.get(y),
        }
        fam_all = {leg: famv(b["lab"]) for leg, b in legs.items()}
        rows = {}
        for leg, b in legs.items():
            fc = b["hr"][:, None] * b["fp"]
            ce = np.isin(b["grp"], COAL) & (b["fam"] == "econ")
            fam_row = fam_all[leg]
            is_coal = fam_row == "coal"
            is_gas = fam_row == "gas"
            is_seam = fam_row == "seam"
            cc = b["grp"] == "CC_REGULAR"
            for m in grid:
                t_pt = time.time()
                mcm = b["mc"].copy()
                mcm[ce] -= fc[ce] * (1.0 - m)
                p0, m0, d0 = clear_vec(mcm, b["mg"], b["flex"], q)
                mk = markup_for(b, d0)
                p1, m1, d1 = clear_vec(mcm + mk, b["mg"], b["flex"], q)

                def census(marg, mask):
                    v = pd.Series(fam_row[marg[mask]]).value_counts(normalize=True)
                    return {k: _r(x) for k, x in v.items()}

                allm = np.ones(T, bool)
                lw_s = p1  # system-wide single stack price (no zones)
                rows[f"{leg}|{m:.2f}"] = {
                    "leg": leg,
                    "m": m,
                    "p0_all": census(m0, allm),
                    "bid_all": census(m1, allm),
                    "bid_q": {f"q{i + 1}": census(m1, q5 == i) for i in range(5)},
                    "bid_coal_band_all": {
                        k: _r(v)
                        for k, v in pd.Series(b["fam"][m1[is_coal[m1]]])
                        .value_counts(normalize=True)
                        .items()
                    },
                    "coal_econ_dispatched_share": _r(
                        d1[ce].sum() / max(b["cap"][ce].sum(), 1.0)
                    ),
                    "coal_econ_dispatched_share_q12": _r(
                        d1[ce][:, q5 <= 1].sum()
                        / max(b["cap"][ce][:, q5 <= 1].sum(), 1.0)
                    ),
                    "dispatch_gw_mean": {
                        "coal": _r(d1[is_coal].sum(0).mean() / 1e3),
                        "coal_econ": _r(d1[ce].sum(0).mean() / 1e3),
                        "gas": _r(d1[is_gas].sum(0).mean() / 1e3),
                        "cc_regular": _r(d1[cc].sum(0).mean() / 1e3),
                        "seam": _r(d1[is_seam].sum(0).mean() / 1e3),
                    },
                    "dispatch_gw_mean_q12": {
                        "coal": _r(d1[is_coal][:, q5 <= 1].sum(0).mean() / 1e3),
                        "coal_econ": _r(d1[ce][:, q5 <= 1].sum(0).mean() / 1e3),
                        "gas": _r(d1[is_gas][:, q5 <= 1].sum(0).mean() / 1e3),
                        "cc_regular": _r(d1[cc][:, q5 <= 1].sum(0).mean() / 1e3),
                        "seam": _r(d1[is_seam][:, q5 <= 1].sum(0).mean() / 1e3),
                    },
                    "price": {
                        "bid_q1_median": _r(np.median(lw_s[q5 == 0])),
                        "bid_q2_median": _r(np.median(lw_s[q5 == 1])),
                        "bid_q5_median": _r(np.median(lw_s[q5 == 4])),
                        "bid_lw_mean": _r((lw_s[ok] * wt[ok]).sum() / wt.sum()),
                        "bid_minus_actual_q12_median": _r(
                            np.median((lw_s - lw_a)[(q5 <= 1) & ok])
                        ),
                        "bid_minus_actual_lw_mean": _r(
                            ((lw_s - lw_a)[ok] * wt[ok]).sum() / wt.sum()
                        ),
                        "bid_minus_actual_lw_mean_q12": _r(
                            ((lw_s - lw_a)[(q5 <= 1) & ok] * wt[(q5 <= 1) & ok]).sum()
                            / wt[(q5 <= 1) & ok].sum()
                        ),
                        "markup_at_margin_q12_median": _r(
                            np.median(mk[m1, np.arange(T)][q5 <= 1])
                        ),
                    },
                }
                print(
                    y,
                    leg,
                    f"m={m:.2f}",
                    "bid coal",
                    rows[f"{leg}|{m:.2f}"]["bid_all"].get("coal"),
                    "gas",
                    rows[f"{leg}|{m:.2f}"]["bid_all"].get("gas"),
                    "seam",
                    rows[f"{leg}|{m:.2f}"]["bid_all"].get("seam"),
                    "ce_disp",
                    rows[f"{leg}|{m:.2f}"]["coal_econ_dispatched_share"],
                    "q1",
                    rows[f"{leg}|{m:.2f}"]["price"]["bid_q1_median"],
                    f"{time.time() - t_pt:.0f}s",
                    flush=True,
                )
        yo["scan"] = rows
        yo["elapsed_s"] = round(time.time() - t0, 1)
        out[str(y)] = yo
        OUT.write_text(json.dumps(out, indent=1))
    if not args.no_pool:
        pool_read(out, grid)
        OUT.write_text(json.dumps(out, indent=1))
    return 0


def pool_read(out: dict, grid: list[float]) -> None:
    """Pool 2019-2024 and read m* on the joint leg (and the coal-only leg, for the record)."""
    years = [y for y in POOL_YEARS if str(y) in out]
    pooled: dict = {"years": years, "imm_pooled_coal": _r(IMM_POOLED_COAL, 4)}
    for leg in ("coal_only", "joint"):
        curve = []
        for m in grid:
            vals = [
                out[str(y)]["scan"][f"{leg}|{m:.2f}"]["bid_all"].get("coal", 0.0)
                for y in years
            ]
            vals0 = [
                out[str(y)]["scan"][f"{leg}|{m:.2f}"]["p0_all"].get("coal", 0.0)
                for y in years
            ]
            curve.append(
                {
                    "m": m,
                    "bid_coal_pooled": _r(np.mean(vals), 4),
                    "p0_coal_pooled": _r(np.mean(vals0), 4),
                    "per_year": {str(y): v for y, v in zip(years, vals)},
                }
            )
        m_star = None
        for a, b in zip(curve, curve[1:]):
            sa, sb = a["bid_coal_pooled"], b["bid_coal_pooled"]
            if sa < IMM_POOLED_COAL <= sb:
                frac = (IMM_POOLED_COAL - sa) / (sb - sa) if sb != sa else 0.0
                m_star = round(a["m"] + frac * (b["m"] - a["m"]), 2)
                break
        if m_star is None and curve and curve[0]["bid_coal_pooled"] >= IMM_POOLED_COAL:
            m_star = 1.0
        pooled[leg] = {"curve": curve, "m_star": m_star}
    out["_pooled"] = pooled
    print(
        "POOLED",
        json.dumps(
            {k: v.get("m_star") for k, v in pooled.items() if isinstance(v, dict)}
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
