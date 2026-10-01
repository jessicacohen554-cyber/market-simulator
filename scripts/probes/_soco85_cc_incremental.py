"""soco-85 zero-LP census: SOCO combined-cycle INCREMENTAL vs AVERAGE heat rate.

Owner ruling 2026-09-28 (soco-84 card): "Zero-LP census first". The numbers in
FINDING-soco-85 were measured on the soco83 legs (keeper at the time); after the
soco-85 promotion this probe reads soco85_span, whose recipe already carries
``gas_daily_shape``, so ``--arm gasdaily`` is then a no-op re-shape. Rule 32
``[R-SHARD]`` (a): never solves. Writes only to ``--out`` (a scratch path);
commits no artifact.

``derive``    — per SOCO CC unit, the FROZEN ``derive_campd_marginal_hr``
               construction (``load_campd`` steady-state filter,
               ``derive_unit_bands``: LSL/HSL = p3/p97, normalized-quadratic I/O
               fit, econ_low x=0.5 / econ_high x=0.9), normalized to the unit's
               OWN measured average HR (``hr_gross`` in the committed
               ``campd_cc_heat_rates_SOCO_units.csv``, the base the model's
               measured CC rates carry). Pooled 2019-2025 and per unit-year.
               Only plants the CC derive flags ``ok`` (steam turbine in the
               meter; boundary guard) are used. Also reported, as checks: a
               linear OLS slope over the econ range x in [0.2, 1.0]
               (soco-75's robustness check), and the no-load heat input (the
               same fitted curve at P = 0, SOCO-64 §(a)) as a share of
               full-load heat input.

``coherence`` — SOCO-63/64 question for CC: with econ tranches at incremental,
               does the fleet still pay the unit's measured full-load fuel?
               ``closure`` = (tranche MW x offered HR summed) / (HSL x measured
               average HR at HSL), on the model's own CC tranche split
               (fleet_only rebuild on the soco83 recipe).

``greedy``    — merit-order re-stack (SOCO-63 §4 instrument) of the restack
               set on the soco83 legs: dispatchable thermal bands from the
               committed ``class_band_hourly`` (``mustrun`` held), tranches
               from a fleet_only rebuild, keeper offers vs arm offers,
               baseline-differenced. Class deltas re-scored through
               ``calibration_verdict.score_fuelmix``; the hourly marginal-offer
               delta is added to each zone's committed price and re-scored
               through ``score_price_mean`` / ``score_price_shape``.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco85_cc_incremental.py derive --out S
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco85_cc_incremental.py coherence --out S
    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_soco85_cc_incremental.py greedy --out S
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

LEGACY = ROOT / "data/raw/_processed-legacy"
# Repointed soco-85 (2026-09-28): soco83_span was pruned at the soco-85 promotion (rule 35);
# the incumbent keeper is soco85_span (the soco-83 recipe + gas_daily_shape).
# Repointed soco-87 (2026-09-29): soco85_span was pruned at the soco-87 promotion (rule 35);
# the incumbent keeper is soco96_span (soco-96: the soco-93 recipe + dual_fuel_measured_oil_burn).
KEEPER = "2026-09-28-soco85-gas-daily-shape"
SPAN = (
    ROOT / "results/calibration/soco96_span"
)  # repointed soco-93 (rule 35 prune of soco92_span)
YEARS = tuple(range(2019, 2026))
T = 8760
RECIPE_SETS = (  # PRECOMMIT-soco-83 §5 --set flags (same list as _soco84_price_gap)
    "eia860_vintage_tracks_solve_year",
    "measured_chp_heat_rates",
    "unit_outage_short_windows",
    "unit_outage_short_windows_gas",
    "unit_partial_outage_windows",
    "unit_outage_precod_clip",
    "summer_derate_basis_aware",
    "coal_mustrun_requires_measured_row",
    "egrid_identity_heat_rates",
    "coal_econ_marginal_hr_two_sided",
    "st_gas_mustrun_per_plant",
    "st_gas_mustrun_p25_level",
    "st_gas_mustrun_oom_level",
    "gas_daily_shape",
)
RESTACK = (
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_WC",
    "oil",
)


def _dm():
    spec = importlib.util.spec_from_file_location(
        "dmhr", str(ROOT / "scripts/data/derive_campd_marginal_hr.py")
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# derive
# ---------------------------------------------------------------------------
def _unit_row(dm, g: pd.DataFrame, base: float) -> dict | None:
    r = dm.derive_unit_bands(g, base)
    if r is None:
        return None
    gl = g["grossLoad"].to_numpy(float)
    hi = g["heatInput"].to_numpy(float)
    lsl, hsl = np.percentile(gl, dm.LSL_PCT), np.percentile(gl, dm.HSL_PCT)
    rng = hsl - lsl
    x = (gl - lsl) / rng
    c2, c1, c0 = np.polyfit(x, hi, 2)
    x0 = -lsl / rng
    nl = c2 * x0 * x0 + c1 * x0 + c0  # heat input at P = 0 (SOCO-64 §(a))
    full = c2 + c1 + c0  # heat input at HSL (x = 1)
    m = (x >= 0.2) & (x <= 1.0)
    lin = float(np.polyfit(gl[m], hi[m], 1)[0]) / base if m.sum() >= 100 else np.nan
    near = gl >= np.percentile(gl, 90)
    r.update(
        lin=lin,
        nl_share=float(nl / full) if full > 0 else np.nan,
        lsl_over_hsl=float(lsl / hsl),
        avg_hsl=float(hi[near].sum() / gl[near].sum()) / base,
        hours=int(len(g)),
        gross_twh=float(gl.sum() / 1e6),
    )
    return r


def derive(out: Path) -> pd.DataFrame:
    """Unit-grain CC bands (own-average basis), pooled and per year."""
    dm = _dm()
    units = pd.read_csv(
        LEGACY / "campd_cc_heat_rates_SOCO_units.csv", dtype={"unit_id": str}
    )
    plant = pd.read_csv(LEGACY / "campd_cc_heat_rates_SOCO.csv")
    ok = set(plant[(plant.year == 0) & (plant.flag == "ok")].plant_code)
    units = units[units.plant_code.isin(ok)]
    camp = dm.load_campd("SOCO", YEARS)
    camp["unitId"] = camp["unitId"].astype(str)
    camp = camp.merge(
        units[["plant_code", "unit_id", "hr_gross", "cap_mw"]],
        left_on=["facilityId", "unitId"],
        right_on=["plant_code", "unit_id"],
    )
    rows = []
    for (pc, uid), g in camp.groupby(["plant_code", "unit_id"]):
        base = float(g.hr_gross.iloc[0])
        r = _unit_row(dm, g, base)
        if r is not None:
            rows.append(dict(plant=pc, unit=uid, year=0, **r))
        for y, gy in g.groupby("year"):
            ry = _unit_row(dm, gy, base)
            if ry is not None:
                rows.append(dict(plant=pc, unit=uid, year=int(y), **ry))
    d = pd.DataFrame(rows)
    d.to_csv(out / "soco85_cc_units.csv", index=False)
    cols = (
        "avg_committed",
        "marg_committed",
        "marg_econ_low",
        "marg_econ_high",
        "lin",
        "nl_share",
        "lsl_over_hsl",
        "avg_hsl",
    )
    summ = []
    for y, dy in d.groupby("year"):
        row = {
            "year": y or "pooled",
            "units": len(dy),
            "gross_twh": round(dy.gross_twh.sum(), 1),
        }
        for c in cols:
            q = dm._capwt(dy.rename(columns={}), c)
            row[c] = f"{q['p50']} [{q['p25']},{q['p75']}]"
        summ.append(row)
    s = pd.DataFrame(summ)
    pd.set_option("display.width", 250)
    print(f"ok plants {len(ok)}, units fitted (pooled) {int((d.year == 0).sum())}")
    print(s.to_string(index=False))
    s.to_csv(out / "soco85_cc_summary.csv", index=False)
    return d


# ---------------------------------------------------------------------------
# fleet / coherence / greedy
# ---------------------------------------------------------------------------
def fleet(year: int) -> dict:
    """fleet_only rebuild on the soco83 keeper recipe (PRECOMMIT-soco-83 §5)."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year

    meta = json.loads((SPAN / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    kw.setdefault("prb_overrides", {}).update({k: True for k in RECIPE_SETS})
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    fuel = np.asarray(st["fuel_prices"], float)
    return dict(
        ids=np.array([str(g.unit_id) for g in st["fleet"]]),
        klass=np.asarray(fa.plant_group).astype(str),
        plant=np.array([int(getattr(g, "plant_code", -1) or -1) for g in st["fleet"]]),
        zone=np.asarray(fa.zone_idx),
        hr=np.asarray(fa.heat_rate, float),
        fuel=fuel if fuel.ndim == 2 else np.repeat(fuel[:, None], T, axis=1),
        mc=mc if mc.ndim == 2 else np.repeat(mc[:, None], T, axis=1),
        pmax=np.asarray(fa.pmax, float),
        avail=np.asarray(fa.availability, float),
    )


def _band(uid: str) -> str:
    s = uid.rsplit("_", 1)[-1]
    for b in ("committed", "econlo", "econhi", "peak", "mustrun", "econ"):
        if s.startswith(b):
            return b
    return s


def ratios(out: Path, basis: str) -> dict[int, dict[str, float]]:
    """{plant: {band: ratio}} cap-weighted over the plant's units (pooled rows)."""
    d = pd.read_csv(out / "soco85_cc_units.csv")
    d = d[d.year == 0]
    res = {}
    for pc, g in d.groupby("plant"):
        w = g["cap"].to_numpy(float)

        def wm(c):
            m = np.isfinite(g[c].to_numpy(float))
            return (
                float(np.average(g[c].to_numpy(float)[m], weights=w[m]))
                if m.any()
                else 1.0
            )

        if basis == "integ":
            # SENSITIVITY, NOT the frozen construction: the linear marginal
            # m(x) (derive_unit_bands' own quadratic) AVERAGED over each
            # tranche's span (econlo x in [0, 0.5], econhi x in [0.5, 1]) instead
            # of evaluated at x = 0.5 / 0.9. An evaluation-point change.
            m0, m5, m9 = wm("marg_committed"), wm("marg_econ_low"), wm("marg_econ_high")
            m1 = m5 + (m9 - m5) * 1.25
            res[int(pc)] = {"econlo": (m0 + m5) / 2, "econhi": (m5 + m1) / 2}
        elif basis == "quad":
            res[int(pc)] = {
                "econlo": wm("marg_econ_low"),
                "econhi": wm("marg_econ_high"),
            }
        else:  # linear econ-range slope for both econ bands
            res[int(pc)] = {"econlo": wm("lin"), "econhi": wm("lin")}
        res[int(pc)]["committed"] = wm("marg_committed")  # ramp bottom (x = 0)
        res[int(pc)]["avg_committed"] = wm("avg_committed")
        res[int(pc)]["avg_hsl"] = wm("avg_hsl")
    return res


def coherence(out: Path, year: int = 2023) -> None:
    """Fuel closure of the arm offers on the model's own CC tranche split."""
    f = fleet(year)
    for basis in ("quad", "lin"):
        rt = ratios(out, basis)
        rows = []
        for pc, r in rt.items():
            m = (f["plant"] == pc) & (f["klass"] == "CC_REGULAR")
            if not m.any():
                continue
            mw = {
                b: f["pmax"][m & np.array([_band(u) == b for u in f["ids"]])].sum()
                for b in ("committed", "econlo", "econhi", "peak")
            }
            tot = sum(mw.values())
            if tot <= 0:
                continue
            offered = (
                mw["committed"]
                + mw["peak"]
                + mw["econlo"] * r["econlo"]
                + mw["econhi"] * r["econhi"]
            )
            rows.append(
                dict(
                    plant=pc,
                    mw=round(tot),
                    comm_share=round(mw["committed"] / tot, 3),
                    r_lo=round(r["econlo"], 3),
                    r_hi=round(r["econhi"], 3),
                    closure_vs_avg=round(offered / tot, 3),
                    closure_vs_avg_hsl=round(offered / tot / r["avg_hsl"], 3),
                )
            )
        df = pd.DataFrame(rows)
        w = df.mw
        print(
            f"\n[{basis}] {year} CC_REGULAR, closure = offered fuel at HSL / measured "
            f"(1.0 = the fleet pays its full-load fuel)"
        )
        print(df.to_string(index=False))
        print(
            f"  MW-weighted closure vs own average {np.average(df.closure_vs_avg, weights=w):.3f}; "
            f"vs measured average at HSL {np.average(df.closure_vs_avg_hsl, weights=w):.3f}"
        )


def _greedy(
    demand: np.ndarray, cap: np.ndarray, mc: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Merit-order fill (vectorized over t); returns dispatch and the marginal offer."""
    order = np.argsort(mc, axis=0, kind="stable")
    cs = np.take_along_axis(cap, order, axis=0)
    ms = np.take_along_axis(mc, order, axis=0)
    cum = np.cumsum(cs, axis=0)
    fill = np.clip(demand[None, :] - (cum - cs), 0.0, cs)
    out = np.zeros_like(cap)
    np.put_along_axis(out, order, fill, axis=0)
    k = np.clip((cum < demand[None, :] - 1e-6).sum(axis=0), 0, cap.shape[0] - 1)
    return out, ms[k, np.arange(cap.shape[1])]


def hub_monthly(gas_csv: Path, year: int) -> np.ndarray:
    """Hourly array of the Henry Hub calendar-day monthly mean (staircase over non-trading days)."""
    d = pd.read_csv(gas_csv, parse_dates=["date"]).set_index("date").iloc[:, 0]
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[~((days.month == 2) & (days.day == 29))]
    v = d.reindex(d.index.union(days)).sort_index().ffill().reindex(days)
    m = v.groupby(v.index.month).transform("mean")
    return np.repeat(m.to_numpy(float), 24)[:T]


def daily_factor(gas_csv: Path, year: int) -> np.ndarray:
    """Hourly within-month daily/monthly gas factor (mean-preserving per month).

    Daily prints forward-filled over non-trading days; each day's factor is its
    price over the calendar-day mean of its month, so a month's mean factor is
    exactly 1 and only the WITHIN-month shape is added to the model's monthly gas.
    """
    d = pd.read_csv(gas_csv, parse_dates=["date"]).set_index("date").iloc[:, 0]
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    days = days[~((days.month == 2) & (days.day == 29))]
    v = d.reindex(d.index.union(days)).sort_index().ffill().reindex(days)
    f = v / v.groupby(v.index.month).transform("mean")
    return np.repeat(f.to_numpy(float), 24)[:T]


def greedy(
    out: Path, basis: str, years=YEARS, arm: str = "econ", gas_csv: Path | None = None
) -> None:
    """Arm minus control, re-scored.

    ``arm="econ"``: the frozen construction — CC ``_econlo`` / ``_econhi`` at the
    measured incremental ratio, ``_committed`` / ``_peak`` unchanged (the
    committed block keeps carrying the no-load heat). ``arm="full"``: ALSO the
    ``_committed`` block at the ramp-bottom incremental (x = 0) — the SOCO-63/64
    incoherent form that drops no-load; reported as a bound only.
    """
    import calibration_verdict as cv

    art = cv.load_artifacts(KEEPER)
    rt = ratios(out, basis)
    res = []
    for y in years:
        f = fleet(y)
        band = np.array([_band(u) for u in f["ids"]])
        sel = np.isin(f["klass"], RESTACK) & (band != "mustrun")
        cap = (f["pmax"][:, None] * f["avail"])[sel]
        mc0 = f["mc"][sel]
        mc1 = mc0.copy()
        k, b, p = f["klass"][sel], band[sel], f["plant"][sel]
        fuelc = (f["hr"][:, None] * f["fuel"])[sel]
        if arm == "hub":
            # UPPER BOUND, not a mechanism: every gas unit re-priced from its
            # EIA-923 delivered monthly level to the Henry Hub monthly mean
            # (the replacement-commodity reading of Southern's lambda formula).
            hh = hub_monthly(gas_csv, y)
            gas = np.isin(
                k, ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
            )
            fp = f["fuel"][sel][gas]
            mon = np.searchsorted(
                np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[:-1] * 24,
                np.arange(T),
                side="right",
            )
            fm = np.stack([fp[:, mon == m].mean(axis=1) for m in range(12)], axis=1)[
                :, mon
            ]
            scale = np.where(fm > 0, hh[None, :] / fm, 1.0)
            mc1[gas] = mc0[gas] + (scale - 1.0) * fuelc[gas]
        if arm == "gasdaily":
            fac = daily_factor(gas_csv, y)
            gas = np.isin(
                k, ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
            )
            mc1[gas] = mc0[gas] + (fac[None, :] - 1.0) * fuelc[gas]
        moved = ("econlo", "econhi") + (("committed",) if arm == "full" else ())
        for i in np.where((k == "CC_REGULAR") & np.isin(b, moved))[0]:
            if arm in ("gasdaily", "hub"):
                break
            r = rt.get(int(p[i]), {}).get(b[i])
            if r is not None:
                mc1[i] = mc0[i] + (r - 1.0) * fuelc[i]
        cb = pd.read_parquet(SPAN / f"hourly/class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"] == "P1") & cb.klass.isin(RESTACK) & (cb.band != "mustrun")]
        dem = cb.groupby("hour").mw.sum().reindex(range(T), fill_value=0.0).to_numpy()
        g0, p0 = _greedy(dem, cap, mc0)
        g1, p1 = _greedy(dem, cap, mc1)
        dcls = {
            c: float((g1[k == c] - g0[k == c]).sum() / 1e6)
            for c in RESTACK
            if (k == c).any()
        }
        dp = p1 - p0
        # rescore
        ypay = copy.deepcopy(art["payload"]["years"][str(y)])
        yb = art["bench"].get(y, {})
        base = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a0 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b0 = cv.score_price_shape(y, ypay, yb, "SOCO")
        for c, dv in dcls.items():
            if c in ypay["gmModel"]:
                ypay["gmModel"][c] = float(ypay["gmModel"][c]) + dv
        s = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
        mon = np.searchsorted(
            np.cumsum([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])[:-1] * 24,
            np.arange(T),
            side="right",
        )
        for z, sz in s.groupby("zone"):
            if z not in ypay["lmp"]:
                continue
            d = sz.demand.to_numpy()
            zz = ypay["lmp"][z]
            shift_p = float((dp * d).sum() / d.sum())
            zz["p"] = float(zz["p"]) + shift_p
            zz["pMon"] = [
                float(pm)
                + float((dp[mon == i] * d[mon == i]).sum() / d[mon == i].sum())
                if pm is not None
                else None
                for i, pm in enumerate(zz["pMon"])
            ]
        armr = {
            r["key"]: r
            for r in cv.score_fuelmix(y, ypay, yb, "SOCO")
            if r["status"] != "SKIPPED"
        }
        c3a1 = cv.score_price_mean(y, ypay, yb, "SOCO")
        c3b1 = cv.score_price_shape(y, ypay, yb, "SOCO")
        row = dict(
            year=y,
            c3a=f"{c3a0['magnitude']} -> {c3a1['magnitude']}",
            c3b=f"{c3b0.get('model')} -> {c3b1.get('model')}",
            dp_lw=round(float((dp * dem).sum() / dem.sum()), 2),
            **{f"d_{c}": round(v, 3) for c, v in dcls.items() if abs(v) > 0.005},
        )
        c1 = []
        for key in ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB"):
            if key in base:
                a0, a1 = base[key], armr[key]
                c1.append(f"{key} {a0['magnitude']}->{a1['magnitude']} {a1['status']}")
        row["c1"] = " | ".join(c1)
        res.append(row)
        print(row, flush=True)
    pd.DataFrame(res).to_csv(out / f"soco85_greedy_{basis}_{arm}.csv", index=False)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("cmd", choices=("derive", "coherence", "greedy"))
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--basis", choices=("quad", "lin", "integ"), default="quad")
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument(
        "--arm", choices=("econ", "full", "gasdaily", "hub"), default="econ"
    )
    ap.add_argument(
        "--gas-csv", type=Path, default=ROOT / "data/raw/gas-prices/henry_hub_daily.csv"
    )
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.cmd == "derive":
        derive(a.out)
    elif a.cmd == "coherence":
        coherence(a.out)
    else:
        greedy(a.out, a.basis, tuple(a.years), a.arm, a.gas_csv)


if __name__ == "__main__":
    main()
