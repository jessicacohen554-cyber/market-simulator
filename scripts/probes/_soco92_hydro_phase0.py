"""soco-92 Track A phase 0 (zero LP): size the RECONCILED reservoir min-flow floor
and the pumped-storage cycling gap on the SOCO keeper, from measured data.

Owner ruling 2026-09-29 (soco-91 card, "Queue as next SOCO lane"): build
``hydro_min_flow_floor`` under ``hydro_ror_split`` (the rule-19 reconciled form
``data.hydro.build_hydro_fleet`` already implements) for STRUCTURE, plus PS
cycling depth only if a measured, year-regenerable driver exists. Rule 32
``[R-SHARD]`` (a): this never solves.

Per year:

1. ``fleet_only`` rebuild of the keeper recipe (``results/calibration/soco87_span``
   via ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs``) with the
   floor OFF (keeper) and ON (arm). Reports every unit whose ``min_gen``,
   ``pmax``, ``availability`` or ``mc_base`` moved, and the fleet floor by month
   split into the RoR flat base and the reconciled reservoir floor.
2. The measured EIA-930 Q05 level (``measured_hydro_min_flow_level``) that the
   reconciliation starts from.
3. Against the keeper's committed ``hourly/class_hourly_<y>`` hydro dispatch:
   the hours in which the reservoir class sits below the arm's reservoir floor
   (a LOWER bound on binding hours, since the floor is per plant) and the MWh it
   would have to lift.
4. Pumped storage: the keeper's annual PS charge / discharge (``hourly/storage``)
   against EIA-930 ``NG: PS`` where it exists (2024-07-15 onward).

Usage::

    uv run python scripts/probes/_soco92_hydro_phase0.py --out DIR [--years ...]
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
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

SPAN = ROOT / "results/calibration/soco87_span"
YEARS = tuple(range(2019, 2026))
T = 8760
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH = np.repeat(np.arange(12), np.array(_DAYS) * 24)


def rebuild(year: int, floor_on: bool) -> dict:
    """``fleet_only`` rebuild of the keeper recipe, floor off (keeper) or on (arm)."""
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    if floor_on:
        kw.setdefault("prb_overrides", {})
        kw["prb_overrides"] = dict(kw["prb_overrides"] or {})
        kw["prb_overrides"]["hydro_min_flow_floor"] = True
    clear_fleet_caches()
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    h.setLevel(logging.INFO)
    lg = logging.getLogger("market_sim.data.hydro")
    lg.addHandler(h)
    lg.setLevel(logging.INFO)
    try:
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
    finally:
        lg.removeHandler(h)
    fa = st["fleet_arrays"]

    def _2d(a):
        a = np.asarray(a, float)
        return a if a.ndim == 2 else np.repeat(a[:, None], T, 1)

    fleet = st["fleet"]
    return dict(
        ids=np.array([str(g.unit_id) for g in fleet]),
        fuel=np.array([str(g.fuel_type) for g in fleet]),
        ror=np.array(
            [getattr(g, "hydro_ror_flat_monthly_mw", None) is not None for g in fleet]
        ),
        pmax=np.asarray(fa.pmax, float),
        avail=_2d(fa.availability),
        floor=_2d(fa.min_gen),
        mc=_2d(st["mc_base"]),
        log=buf.getvalue(),
    )


def _monthly_mean(x: np.ndarray) -> list[float]:
    return [round(float(x[MONTH == m].mean()), 1) for m in range(12)]


def phase0(year: int) -> dict:
    """Size the reconciled floor and count keeper binding hours for one year."""
    from market_sim.data.eia930.envelopes import measured_hydro_min_flow_level

    k = rebuild(year, False)
    a = rebuild(year, True)
    assert (k["ids"] == a["ids"]).all(), "unit set moved"
    moved = {}
    for f in ("pmax", "avail", "floor", "mc"):
        d = np.abs(np.atleast_2d(a[f]) - np.atleast_2d(k[f]))
        rows = np.where(d.reshape(d.shape[0], -1).max(1) > 1e-9)[0]
        moved[f] = sorted(set(k["fuel"][rows].tolist()))
        moved[f + "_n"] = int(len(rows))
    hy = k["fuel"] == "hydro"
    ror = hy & k["ror"]
    res = hy & ~k["ror"]
    ror_base = k["floor"][ror].sum(0)  # RoR flat base (== its availability cap)
    res_floor_k = k["floor"][res].sum(0)
    res_floor_a = a["floor"][res].sum(0)
    q05 = measured_hydro_min_flow_level("SOCO", year)

    ch = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    hyd = (
        ch[(ch["pass"] == "P1") & (ch.klass == "hydro")]
        .set_index("hour")
        .mw.reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )
    res_disp = hyd - ror_base
    short = np.clip(res_floor_a - res_disp, 0.0, None)
    res_cap = (k["pmax"][res][:, None] * k["avail"][res]).sum(0)
    return dict(
        year=year,
        n_hydro=int(hy.sum()),
        n_ror=int(ror.sum()),
        moved=moved,
        q05_mw=[round(float(v), 1) for v in q05] if q05 is not None else None,
        ror_base_mw=_monthly_mean(ror_base),
        res_floor_keeper_mw=_monthly_mean(res_floor_k),
        res_floor_arm_mw=_monthly_mean(res_floor_a),
        res_floor_arm_avg=round(float(res_floor_a.mean()), 1),
        res_floor_arm_share_of_res_energy=round(
            float(res_floor_a.sum() / max(res_disp.clip(0).sum(), 1.0)), 3
        ),
        res_cap_avg=round(float(res_cap.mean()), 1),
        keeper_hydro_min=round(float(hyd.min()), 1),
        keeper_res_min=round(float(res_disp.min()), 1),
        bind_hours_lb=int((short > 1.0).sum()),
        lift_gwh=round(float(short.sum() / 1e3), 2),
        log=[ln for ln in a["log"].splitlines() if "min-flow" in ln or "RoR" in ln],
    )


def ps_gap(year: int) -> dict:
    """Keeper PS charge/discharge vs EIA-930 ``NG: PS`` on the split window."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    stg = pd.read_parquet(SPAN / f"hourly/storage_{year}.parquet")
    ps = stg[(stg["pass"] == "P1") & (stg.tech == "pumped_storage")].set_index("hour")
    dis = ps.discharge_mw.reindex(range(T), fill_value=0.0).to_numpy(float)
    chg = ps.charge_mw.reindex(range(T), fill_value=0.0).to_numpy(float)
    fr = _eia_hourly_frame_filled("SOCO", year).reset_index(drop=True)
    out = dict(
        year=year,
        model_dis_twh=round(float(dis.sum() / 1e6), 3),
        model_chg_twh=round(float(chg.sum() / 1e6), 3),
    )
    if "NG: PS" in fr.columns:
        m = fr["NG: PS"].to_numpy(float)
        ok = np.isfinite(m)
        out.update(
            split_hours=int(ok.sum()),
            model_dis_twh_split=round(float(dis[ok].sum() / 1e6), 3),
            model_chg_twh_split=round(float(chg[ok].sum() / 1e6), 3),
            meas_dis_twh_split=round(float(np.clip(m[ok], 0, None).sum() / 1e6), 3),
            meas_chg_twh_split=round(float(np.clip(-m[ok], 0, None).sum() / 1e6), 3),
            model_cycles_per_day=round(
                float(dis[ok].sum() / max(dis.max(), 1) / (ok.sum() / 24)), 3
            ),
            meas_cycles_per_day=round(
                float(
                    np.clip(m[ok], 0, None).sum() / max(dis.max(), 1) / (ok.sum() / 24)
                ),
                3,
            ),
        )
    return out


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    res = []
    for y in args.years:
        r = phase0(y)
        r["ps"] = ps_gap(y)
        res.append(r)
        print(json.dumps(r, default=str))
        (args.out / "soco92_hydro_phase0.json").write_text(
            json.dumps(res, indent=1, default=str)
        )


if __name__ == "__main__":
    main()
