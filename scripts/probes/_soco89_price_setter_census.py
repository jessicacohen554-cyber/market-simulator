"""soco-89 zero-LP price-setter census: which class sets SOCO's price, and where does the
C3a gap vs Southern's FERC-714 system lambda come from?

Rule 32 ``[R-SHARD]`` (a): never solves. Per year one ``fleet_only`` rebuild of the keeper
recipe (``results/calibration/soco92_span`` via ``replay_keeper.run_year_kwargs``, the same
construction as ``_soco87_c3b_monthly.py``) supplies each unit's ``mc_base[g, t]``. In each
zone-hour of the keeper's committed ``hourly/system_<y>.parquet`` the live unit IN THAT ZONE
(else any zone) whose ``mc_base`` sits within ``TOL`` of the LP price is taken as the
price-setter; hours with no match are labelled ``UNMATCHED`` (storage, startup markup,
congestion, slack). The load-weighted gap ``Σ D_zh (P_zh − λ_h) / Σ D_zh`` is then
decomposed by price-setting class, month and hour band, against the lambda on the same
dense CST 8760 calendar the bench builder uses (``derive_actual_lmp._soco``).

Usage::

    uv run python scripts/probes/_soco89_price_setter_census.py [--years ...] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "src"), str(_ROOT)]

from probes import _soco87_c3b_monthly as p87  # noqa: E402

T = p87.T
TOL = p87.TOL  # $/MWh match window (diagnostic only)
BANDS = {
    "night 0-5": range(0, 6),
    "morning 6-11": range(6, 12),
    "afternoon 12-17": range(12, 18),
    "evening 18-23": range(18, 24),
}


def rebuild(year: int) -> dict:
    """``fleet_only`` rebuild of the keeper recipe; returns per-unit arrays."""
    import contextlib
    import copy
    import io

    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((p87.SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(p87.SPAN), year))
    clear_fleet_caches()
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
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], T, 1)
    fuel = np.asarray(st["fuel_prices"], float)
    if fuel.ndim == 1:
        fuel = np.repeat(fuel[:, None], T, 1)
    zones = st.get("zones") or st.get("zone_names")
    return dict(
        mc=mc,
        fuel=fuel,
        hr=np.asarray(fa.heat_rate, float),
        vom=np.asarray(fa.vom, float),
        pmax=np.asarray(fa.pmax, float),
        zone_idx=np.asarray(fa.zone_idx),
        group=np.asarray(fa.plant_group).astype(str),
        zones=list(zones) if zones is not None else None,
    )


def lambda_cst(year: int) -> np.ndarray:
    """Southern's lambda on the bench builder's dense CST 8760 calendar."""
    from data.derive_actual_lmp import _soco

    _rec, hourly = _soco(year)
    return hourly["rt"].to_numpy(float)


def census(year: int, cache: Path) -> dict:
    """Price-setter attribution and C3a gap decomposition for one year."""
    import pandas as pd

    f = cache / f"fleet_{year}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        r = {k: z[k] for k in z.files}
        r["zones"] = list(r["zones"]) if r["zones"].ndim else None
    else:
        r = rebuild(year)
        np.savez(
            f,
            **{
                k: (np.array(v, dtype=object) if k == "zones" else v)
                for k, v in r.items()
            },
        )
    sysdf = pd.read_parquet(p87.SPAN / f"hourly/system_{year}.parquet")
    zn = sorted(sysdf.zone.unique())
    P = np.vstack(
        [sysdf[sysdf.zone == q].sort_values("hour").price.to_numpy() for q in zn]
    )
    D = np.vstack(
        [sysdf[sysdf.zone == q].sort_values("hour").demand.to_numpy() for q in zn]
    )
    lam = lambda_cst(year)
    live = r["pmax"] > 0
    idx = np.flatnonzero(live)
    mc = r["mc"][live]
    grp = r["group"][live]
    zmap = r["zones"] or zn
    uz = np.array([zmap[i] for i in r["zone_idx"][live]])
    setter = np.full(P.shape, "UNMATCHED", dtype=object)
    setter_mc = np.full(P.shape, np.nan)
    setter_fuel = np.full(P.shape, np.nan)
    ar = np.arange(T)
    for zi, q in enumerate(zn):
        diff = np.abs(mc - P[zi][None, :])
        diff_in = np.where((uz == q)[:, None], diff, np.inf)
        i_in, i_all = diff_in.argmin(0), diff.argmin(0)
        ok_in = diff_in[i_in, ar] <= TOL
        i = np.where(ok_in, i_in, i_all)
        ok = diff[i, ar] <= TOL
        setter[zi, ok] = grp[i[ok]]
        setter_mc[zi, ok] = mc[i[ok], ar[ok]]
        setter_fuel[zi, ok] = r["fuel"][idx[i[ok]], ar[ok]]
    W = D / D.sum()
    gap = P - lam[None, :]
    month = np.broadcast_to(p87.MONTH, P.shape)
    hod = np.broadcast_to(ar % 24, P.shape)
    out = dict(
        year=year,
        model_lw=float((W * P).sum()),
        lam_lw=float((W * lam[None]).sum()),
        lam_flat=float(lam.mean()),
        matched=float((setter != "UNMATCHED").mean()),
    )
    out["gap_pct"] = 100 * (out["model_lw"] / out["lam_lw"] - 1)
    # by class: share of load-weighted hours, mean P, mean lambda in those hours, gap contribution
    by = {}
    for c in sorted(set(setter.ravel())):
        m = setter == c
        w = W[m].sum()
        by[c] = dict(
            share=float(w),
            P=float((W * P)[m].sum() / w),
            lam=float((W * lam[None])[m].sum() / w),
            contrib=float((W * gap)[m].sum()),
            fuel=float(np.nanmean(setter_fuel[m]))
            if np.isfinite(setter_fuel[m]).any()
            else None,
        )
    out["by_class"] = by
    out["by_month"] = {
        int(k) + 1: dict(
            P=float((W * P)[month == k].sum() / W[month == k].sum()),
            lam=float((W * lam[None])[month == k].sum() / W[month == k].sum()),
            contrib=float((W * gap)[month == k].sum()),
        )
        for k in range(12)
    }
    out["by_band"] = {
        b: dict(
            P=float(
                (W * P)[np.isin(hod, list(h))].sum() / W[np.isin(hod, list(h))].sum()
            ),
            lam=float(
                (W * lam[None])[np.isin(hod, list(h))].sum()
                / W[np.isin(hod, list(h))].sum()
            ),
            contrib=float((W * gap)[np.isin(hod, list(h))].sum()),
        )
        for b, h in BANDS.items()
    }
    # capacity-weighted class offer (mc_base) and fuel price, annual mean
    cls = {}
    for c in sorted(set(grp)):
        m = grp == c
        wcap = r["pmax"][live][m]
        cls[c] = dict(
            mw=float(wcap.sum()),
            mc=float(np.average(mc[m].mean(1), weights=wcap)),
            fuel=float(np.average(r["fuel"][idx[m]].mean(1), weights=wcap)),
            hr=float(np.average(r["hr"][idx[m]], weights=wcap)),
        )
    out["class_offer"] = cls
    return out


def main() -> None:
    """Run the census for the requested years and write JSON."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for y in a.years:
        res = census(y, out)
        (out / f"census_{y}.json").write_text(json.dumps(res, indent=1))
        top = sorted(res["by_class"].items(), key=lambda kv: -kv[1]["share"])[:6]
        print(
            f"{y}: model {res['model_lw']:.2f} lam {res['lam_lw']:.2f} ({res['gap_pct']:+.1f}%) matched {res['matched']:.0%}"
        )
        for c, v in top:
            print(
                f"   {c:14s} share {v['share']:.2f} P {v['P']:.2f} lam {v['lam']:.2f} contrib {v['contrib']:+.2f}"
            )


if __name__ == "__main__":
    main()
