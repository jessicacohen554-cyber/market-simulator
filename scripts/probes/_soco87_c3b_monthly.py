"""soco-87 zero-LP C3b monthly diagnosis: does the measured Henry Hub MONTHLY gas shape
(``gas_hh_monthly_shape``) repair SOCO's flat monthly price profile?

Rule 32 ``[R-SHARD]`` (a): never solves. Per year, two ``fleet_only`` rebuilds of the
incumbent keeper's own recipe (``results/calibration/soco96_span`` through
``replay_keeper.run_year_kwargs``): the keeper as recorded (generic climatological
``GAS_MONTHLY_SEASONALITY``) and the keeper + ``gas_hh_monthly_shape=True`` (measured HH
monthly shape, same annual level). Counterfactual = SAME-MARGINAL-UNIT re-pricing of the
keeper's committed hourly zone prices: in each zone-hour the unit whose keeper ``mc_base``
sits within ``TOL`` $/MWh of the LP price is taken as price-setter and the price moves to
that unit's armed ``mc_base``; other hours are left unchanged. No merit-order reshuffle is
modelled (first-order). Monthly load-weighted prices are then scored with the scorer's own
``_nrmse`` against the bench's ``rt_lw_mon``.

REPOINTED after the soco-87 promotion (rule 35 pruned soco85_span): ``SPAN`` now reads
soco92_span, which already arms the flag, so a re-run measures ~zero delta. The FINDING-soco-87
numbers came from soco85_span at e44cf620 (git history is the record).

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_soco87_c3b_monthly.py [--years ...] [--json-out P]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import logging
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(_ROOT / "scripts"), str(_ROOT / "src"), str(_ROOT)]

SPAN = (
    _ROOT / "results/calibration/soco96_span"
)  # repointed soco-93 (rule 35 prune of soco92_span)
RUN_ID = "2026-09-28-soco85-gas-daily-shape"
T = 8760
TOL = (
    0.5  # $/MWh match window for the price-setting unit (diagnostic, not a model input)
)
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH = np.repeat(np.arange(12), np.array(_DAYS) * 24)


def rebuild(year: int, hh_monthly: bool) -> dict:
    """``fleet_only`` rebuild of the keeper recipe, optionally with the HH monthly shape."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    if hh_monthly:
        kw["gas_hh_monthly_shape"] = True
    clear_fleet_caches()
    log = io.StringIO()
    h = logging.StreamHandler(log)
    with contextlib.redirect_stderr(log), contextlib.redirect_stdout(io.StringIO()):
        logging.getLogger().addHandler(h)
        try:
            st = run_year(
                year,
                meta["iso"],
                T,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kw,
            )
        finally:
            logging.getLogger().removeHandler(h)
    fa = st["fleet_arrays"]
    mc = np.asarray(st["mc_base"], float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], T, 1)
    return dict(
        mc=mc,
        pmax=np.asarray(fa.pmax, float),
        ids=list(map(str, fa.unit_ids)),
        fuel=np.asarray(fa.fuel_type_idx),
        group=list(getattr(fa, "plant_group", [])),
    )


def monthly_lw(price: np.ndarray, demand: np.ndarray) -> list[float]:
    """(zones, T) prices/demand -> 12 load-weighted monthly means (all zones pooled)."""
    out = []
    for m in range(12):
        sl = MONTH == m
        out.append(float((price[:, sl] * demand[:, sl]).sum() / demand[:, sl].sum()))
    return out


def main() -> None:
    """Print per-year keeper vs HH-monthly counterfactual monthly prices and C3b NRMSE."""
    import pandas as pd
    import calibration_verdict as cv

    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--json-out")
    a = ap.parse_args()
    art = cv.load_artifacts(RUN_ID)
    res = {}
    for y in a.years:
        sysdf = pd.read_parquet(SPAN / f"hourly/system_{y}.parquet")
        zones = sorted(sysdf.zone.unique())
        P = np.vstack(
            [sysdf[sysdf.zone == z].sort_values("hour").price.to_numpy() for z in zones]
        )
        D = np.vstack(
            [
                sysdf[sysdf.zone == z].sort_values("hour").demand.to_numpy()
                for z in zones
            ]
        )
        k, h = rebuild(y, False), rebuild(y, True)
        assert k["ids"] == h["ids"]
        live = k["pmax"] > 0
        mk, mh = k["mc"][live], h["mc"][live]
        Pn = P.copy()
        matched = np.zeros_like(P, bool)
        for zi in range(P.shape[0]):
            diff = np.abs(mk - P[zi][None, :])
            i = diff.argmin(0)
            ok = diff[i, np.arange(T)] <= TOL
            Pn[zi, ok] = mh[i[ok], np.arange(T)[ok]]
            matched[zi] = ok
        act = art["bench"][y]["avgLMP"]["rt_lw_mon"]
        base, cf = monthly_lw(P, D), monthly_lw(Pn, D)
        res[y] = dict(
            actual=act,
            keeper=base,
            cf=cf,
            nrmse_keeper=cv._nrmse(base, act),
            nrmse_cf=cv._nrmse(cf, act),
            c3a_keeper=float(np.average(P, weights=D)),
            c3a_cf=float(np.average(Pn, weights=D)),
            matched_share=float(matched.mean()),
        )
        print(
            f"{y}: C3b keeper {res[y]['nrmse_keeper']:.3f} -> HH-monthly {res[y]['nrmse_cf']:.3f}; "
            f"LW mean {res[y]['c3a_keeper']:.2f} -> {res[y]['c3a_cf']:.2f}; matched {res[y]['matched_share']:.0%}"
        )
        print("   act " + " ".join(f"{v:6.1f}" for v in act))
        print("   kpr " + " ".join(f"{v:6.1f}" for v in base))
        print("   cf  " + " ".join(f"{v:6.1f}" for v in cf))
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, indent=1))


def census(years: list[int]) -> None:
    """PRECOMMIT §2 phase-0 census: only gas fuel moves, and each moved unit keeps its annual mean."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((SPAN / "meta.json").read_text())

    def build(y: int, arm: bool) -> dict:
        kw = run_year_kwargs(copy.deepcopy(meta))
        kw.update(derived_run_year_inputs(str(SPAN), y))
        if arm:
            kw["gas_hh_monthly_shape"] = True
        clear_fleet_caches()
        with (
            contextlib.redirect_stderr(io.StringIO()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            st = run_year(
                y,
                meta["iso"],
                T,
                float(meta["gas_prices"][str(y)]),
                {},
                fleet_only=True,
                **kw,
            )
        fa = st["fleet_arrays"]
        fuel = np.asarray(st["fuel_prices"], float)
        return dict(
            ids=[str(u) for u in fa.unit_ids],
            fuel=fuel if fuel.ndim == 2 else np.repeat(fuel[:, None], T, 1),
            ft=np.asarray(fa.fuel_type_idx),
            **{
                f: np.asarray(getattr(fa, f), float)
                for f in ("pmax", "availability", "heat_rate", "min_gen")
            },
        )

    for y in years:
        k, a = build(y, False), build(y, True)
        same = k["ids"] == a["ids"] and all(
            np.array_equal(k[f], a[f])
            for f in ("pmax", "availability", "heat_rate", "min_gen")
        )
        moved = ~np.all(np.isclose(k["fuel"], a["fuel"], rtol=0, atol=1e-12), axis=1)
        ft_moved = sorted(set(k["ft"][moved].tolist()))
        ann = (
            np.abs(a["fuel"][moved].mean(1) / k["fuel"][moved].mean(1) - 1).max()
            if moved.any()
            else 0.0
        )
        mon = np.array(
            [
                a["fuel"][moved][:, MONTH == m].mean()
                / k["fuel"][moved][:, MONTH == m].mean()
                for m in range(12)
            ]
        )
        print(
            f"{y}: arrays identical {same}; units moved {int(moved.sum())} of {len(k['ids'])}; "
            f"fuel_type_idx moved {ft_moved}; max |annual mean ratio-1| {ann:.2e}; "
            f"monthly fuel ratio {mon.min():.3f}-{mon.max():.3f}"
        )


if __name__ == "__main__":
    if "--census" in sys.argv:
        census(
            [int(v) for v in sys.argv[sys.argv.index("--census") + 1 :]]
            or list(range(2019, 2026))
        )
    else:
        main()
