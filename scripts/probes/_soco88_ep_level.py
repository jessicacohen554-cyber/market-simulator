"""soco-88 zero-LP greedy: does the measured N3045 delivered-gas LEVEL
(``gas_electric_power_monthly_level``) move SOCO's failing C3a years?

Rule 32 ``[R-SHARD]`` (a): never solves. Same construction as
``_soco87_c3b_monthly.py``: per year, two ``fleet_only`` rebuilds of the incumbent
keeper's recipe (``results/calibration/soco87_span``) — as recorded, and with
``gas_electric_power_monthly_level=True`` — then SAME-MARGINAL-UNIT re-pricing of the
keeper's committed ``hourly/system_<y>.parquet`` (the unit whose keeper ``mc_base`` sits
within ``TOL`` of the LP price moves to its armed ``mc_base``; no merit-order reshuffle).
Scored with ``calibration_verdict._nrmse`` (C3b) and the load-weighted mean vs the bench
(C3a). Requires the SOCO rows in ``iso-gas-capacity-state-weights.csv``
(``scripts/data/derive_iso_gas_state_weights.py``); a year the basket cannot admit
returns identical arrays and reads as inert.

Usage::

    uv run python scripts/probes/_soco88_ep_level.py [--years ...] [--json-out P]
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

KEEPER_ID = "2026-09-29-soco87-gas-hh-monthly"
T = p87.T
TOL = p87.TOL


def rebuild(year: int, arm: bool) -> dict:
    """``fleet_only`` rebuild of the keeper recipe, optionally with the EP level armed."""
    import copy

    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches
    import contextlib
    import io

    meta = copy.deepcopy(json.loads((p87.SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(p87.SPAN), year))
    if arm:
        # Not a run_year kwarg: routed through the generic ScenarioConfig channel
        # replay_keeper --set uses (prb_overrides).
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["gas_electric_power_monthly_level"] = True
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
    return dict(
        mc=mc,
        fuel=fuel if fuel.ndim == 2 else np.repeat(fuel[:, None], T, 1),
        ft=np.asarray(fa.fuel_type_idx),
        pmax=np.asarray(fa.pmax, float),
        ids=list(map(str, fa.unit_ids)),
    )


def main() -> None:
    """Print per-year keeper vs EP-level counterfactual C3a / C3b."""
    import pandas as pd

    import calibration_verdict as cv

    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--json-out")
    a = ap.parse_args()
    art = cv.load_artifacts(KEEPER_ID)
    res = {}
    for y in a.years:
        sysdf = pd.read_parquet(p87.SPAN / f"hourly/system_{y}.parquet")
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
        moved = ~np.all(np.isclose(k["fuel"], h["fuel"], rtol=0, atol=1e-12), axis=1)
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
        bench = art["bench"][y]["avgLMP"]
        act_mon = bench["rt_lw_mon"]
        act_lw = float(
            np.average(act_mon, weights=[D[:, p87.MONTH == m].sum() for m in range(12)])
        )
        base, cf = p87.monthly_lw(P, D), p87.monthly_lw(Pn, D)
        lw_k, lw_c = float(np.average(P, weights=D)), float(np.average(Pn, weights=D))
        res[y] = dict(
            units_moved=int(moved.sum()),
            fuel_types_moved=sorted(set(k["ft"][moved].tolist())),
            gas_annual_keeper=float(k["fuel"][moved].mean()) if moved.any() else None,
            gas_annual_arm=float(h["fuel"][moved].mean()) if moved.any() else None,
            nrmse_keeper=cv._nrmse(base, act_mon),
            nrmse_cf=cv._nrmse(cf, act_mon),
            lw_keeper=lw_k,
            lw_cf=lw_c,
            lw_actual_proxy=act_lw,
            matched_share=float(matched.mean()),
            keeper_mon=base,
            cf_mon=cf,
            act_mon=act_mon,
        )
        r = res[y]
        print(
            f"{y}: moved {r['units_moved']} units ft{r['fuel_types_moved']}; "
            f"gas {r['gas_annual_keeper'] or 0:.3f}->{r['gas_annual_arm'] or 0:.3f}; "
            f"LW {lw_k:.2f}->{lw_c:.2f} ({100 * (lw_c / lw_k - 1):+.1f}%); "
            f"C3b {r['nrmse_keeper']:.3f}->{r['nrmse_cf']:.3f}; matched {r['matched_share']:.0%}"
        )
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
