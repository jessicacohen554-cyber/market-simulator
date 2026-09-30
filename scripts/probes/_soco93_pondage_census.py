"""soco-93 zero-LP pondage census: does SOCO's keeper hydro dispatch fit each plant's forebay?

Owner ruling 2026-09-30 (soco-92 card "Next lane"): "Pondage bound phase 0". Rule 32
``[R-SHARD]`` (a): this never solves. Per year it

1. does one ``fleet_only`` rebuild of the keeper recipe
   (``results/calibration/soco93_span``; the FINDING ran on the then-keeper soco92_span) and captures, from ``build_dispatch_fleet``,
   the hydro generators, their EIA plant codes, the RoR-flat flags and the MEASURED
   ``(n_hydro, 12)`` monthly budget the LP carries;
2. selects the plants ``data.hydro.load_hydro_pondage`` would give a row, with its own
   rule (not RoR-flat, a storage row in ``data/raw/soco-hydro/soco_hydro_pondage.csv``,
   storage < the plant's largest monthly budget);
3. reads the keeper's per-unit hourly hydro dispatch ``P(t)`` (the soco-92 year-shard
   bundles' ``dispatch/<y>_P1.parquet``, passed as ``--dispatch-dir``) and tests it
   against the row ``P + Spill + V(t) - V(t-1) = I(t)``, ``0 <= V <= B``, cyclic, with
   ``I = budget / hours-in-month``. With free spill the storage a trajectory NEEDS is the
   running deficit ``D(t) = max(0, D(t-1) + P(t) - I(t))`` (two cyclic passes); an hour
   violates iff ``D(t) > B``;
4. builds the CLIP trajectory, the nearest feasible dispatch that keeps the keeper's
   timing: ``P'(t) = min(P(t), V(t-1) + I(t))`` and ``V(t) = min(B, V(t-1) + I(t) - P'(t))``.
   ``P - P'`` is the energy the bound forbids at those hours. The LP would re-place it
   inside the same feasible set, so the clip's peak reduction is an UPPER bound on what
   the pondage row can move off the top-20 % lambda hours.

Usage::

    uv run python scripts/probes/_soco93_pondage_census.py --out DIR --dispatch-dir DIR
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

SPAN = (
    ROOT / "results/calibration/soco93_span"
)  # repointed soco-93 (rule 35); FINDING ran on soco92_span
SPAN_HOURLY = SPAN  # --span overrides the hourly frames only (E1 on an arm)
ARTIFACT = ROOT / "data/raw/soco-hydro/soco_hydro_pondage.csv"
YEARS = tuple(range(2019, 2026))
T = 8760
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(12), _DAYS * 24)


def rebuild_hydro(year: int, cache: Path) -> dict:
    """``fleet_only`` rebuild; capture the hydro budget the LP carries (cached)."""
    f = cache / f"hydro93_{year}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        return {k: z[k] for k in z.files}
    import run_calibration as rc
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.lib.bundle_fleet import clear_fleet_caches

    cap: dict = {}
    orig = rc.build_dispatch_fleet

    def _spy(*a, **k):
        out = orig(*a, **k)
        cap["out"] = out
        return out

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    clear_fleet_caches()
    rc.build_dispatch_fleet = _spy
    try:
        with (
            contextlib.redirect_stderr(io.StringIO()),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            st = rc.run_year(
                year,
                meta["iso"],
                T,
                float(meta["gas_prices"][str(year)]),
                {},
                fleet_only=True,
                **kw,
            )
    finally:
        rc.build_dispatch_fleet = orig
    fleet, _ff, hidx, energy = cap["out"]
    hidx = np.asarray(hidx, int)
    r = dict(
        unit_id=np.array([str(fleet[i].unit_id) for i in hidx]),
        plant=np.array([int(getattr(fleet[i], "plant_code", 0)) for i in hidx]),
        flat=np.array(
            [
                getattr(fleet[i], "hydro_ror_flat_monthly_mw", None) is not None
                for i in hidx
            ]
        ),
        pmax=np.array([float(fleet[i].pmax_mw) for i in hidx]),
        energy=np.asarray(energy, float),
    )
    # The LP's hourly hydro floor (min-flow floor + RoR flat), by unit id.
    fa = st["fleet_arrays"]
    row = {str(g.unit_id): k for k, g in enumerate(st["fleet"])}
    mg = np.asarray(fa.min_gen, float)
    r["floor"] = np.vstack(
        [(mg[row[u]] if mg.ndim == 2 else np.full(T, mg[row[u]])) for u in r["unit_id"]]
    ).astype(np.float32)
    np.savez(f, **r)
    return r


def deficit(P: np.ndarray, inflow: np.ndarray) -> np.ndarray:
    """Storage a trajectory needs with free spill: cyclic running deficit, MWh."""
    d, out = 0.0, np.zeros_like(P)
    for _ in range(2):  # second pass settles the cyclic boundary
        for t in range(P.size):
            d = max(0.0, d + P[t] - inflow[t])
            out[t] = d
    return out


def clip(P: np.ndarray, inflow: np.ndarray, B: float) -> np.ndarray:
    """Nearest feasible dispatch keeping the keeper's timing (cyclic, 2 passes)."""
    v, out = B, np.zeros_like(P)
    for _ in range(2):
        for t in range(P.size):
            avail = v + inflow[t]
            p = min(P[t], avail)
            v = min(B, avail - p)
            out[t] = p
    return out


def census(year: int, cache: Path, ddir: Path) -> dict:
    """One year's census row plus per-plant records."""
    from _soco91_intraday_census import eia930, lambda_cst

    h = rebuild_hydro(year, cache)
    art = pd.read_csv(ARTIFACT)
    store = dict(zip(art.plant_id.astype(int), art.storage_mwh.astype(float)))
    d = pd.read_parquet(
        ddir / f"{year}_P1.parquet", columns=["unit_id", "klass", "hour", "mw"]
    )
    d = d[d.klass == "hydro"]
    Pu = {
        u: g.sort_values("hour").mw.to_numpy(float)
        for u, g in d.groupby("unit_id", observed=True)
    }
    hpm = (_DAYS * 24).astype(float)
    lam = lambda_cst(year)
    hi = lam > np.quantile(lam, 0.8)
    lo = lam <= np.quantile(lam, 0.4)

    dP = np.zeros(T)
    recs, n_pm, n_pm_viol = [], 0, 0
    counts = dict(flat=0, unlinked=0, redundant=0, bounded=0)
    for i, u in enumerate(h["unit_id"]):
        pid, E = int(h["plant"][i]), h["energy"][i]
        B = store.get(pid)
        if h["flat"][i]:
            counts["flat"] += 1
            continue
        if B is None or B <= 0:
            counts["unlinked"] += 1
            continue
        if B >= E.max():
            counts["redundant"] += 1
            continue
        counts["bounded"] += 1
        P = Pu.get(u, np.zeros(T))
        inflow = (E / hpm)[MONTH]
        D = deficit(P, inflow)
        viol = D > B + 1e-6
        mviol = np.bincount(MONTH[viol], minlength=12) > 0
        active = E > 0
        n_pm += int(active.sum())
        n_pm_viol += int((mviol & active).sum())
        Pc = clip(P, inflow, B)
        # Floor/row compatibility: the floor is a forced minimum draw, so the
        # forebay must cover its running deficit against inflow (else the
        # armed LP is infeasible for this unit).
        fneed = float(deficit(h["floor"][i].astype(float), inflow).max())
        dP += P - Pc
        recs.append(
            dict(
                year=year,
                unit_id=u,
                plant_id=pid,
                pmax_mw=round(float(h["pmax"][i]), 1),
                storage_mwh=round(B, 0),
                pondage_h=round(B / max(h["pmax"][i], 1e-9), 1),
                need_mwh=round(float(D.max()), 0),
                need_over_B=round(float(D.max() / B), 2),
                viol_h=int(viol.sum()),
                viol_months=int((mviol & active).sum()),
                clipped_gwh=round(float((P - Pc).sum() / 1e3), 2),
                floor_need_over_B=round(fneed / B, 3),
            )
        )
    # soco-92's shape instrument: model hydro+PS vs EIA-930 WAT(+PS) by lambda band
    ch = pd.read_parquet(SPAN_HOURLY / f"hourly/class_hourly_{year}.parquet")
    hyd = (
        ch[(ch["pass"] == "P1") & (ch.klass == "hydro")]
        .set_index("hour")
        .mw.reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )
    stg = pd.read_parquet(SPAN_HOURLY / f"hourly/storage_{year}.parquet")
    ps = stg[(stg["pass"] == "P1") & (stg.tech == "pumped_storage")].set_index("hour")
    H = hyd + ps.discharge_mw.reindex(range(T), fill_value=0.0).to_numpy(float)
    e = eia930(year)
    A = np.clip(
        e["NG: WAT"].to_numpy(float)
        + np.clip(np.nan_to_num(e["NG: PS"].to_numpy(float)), 0, None),
        0,
        None,
    )
    tot_mw = float(h["pmax"].sum())
    bnd_mw = sum(r["pmax_mw"] for r in recs)
    return dict(
        row=dict(
            year=year,
            hydro_units=len(h["unit_id"]),
            **counts,
            bounded_mw=round(bnd_mw, 0),
            hydro_mw=round(tot_mw, 0),
            plant_months=n_pm,
            plant_months_violated=n_pm_viol,
            units_violating=sum(r["viol_h"] > 0 for r in recs),
            floor_infeasible_units=sum(r["floor_need_over_B"] > 1.0 for r in recs),
            max_floor_need_over_B=max(
                (r["floor_need_over_B"] for r in recs), default=0.0
            ),
            clipped_gwh=round(float(dP.sum() / 1e3), 1),
            top20_model_mw=round(float(H[hi].mean()), 0),
            top20_eia_mw=round(float(A[hi].mean()), 0),
            top20_excess_mw=round(float(H[hi].mean() - A[hi].mean()), 0),
            top20_clip_cut_mw=round(float(dP[hi].mean()), 0),
            low40_model_mw=round(float(H[lo].mean()), 0),
            low40_eia_mw=round(float(A[lo].mean()), 0),
        ),
        plants=recs,
    )


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--dispatch-dir", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument(
        "--span",
        type=Path,
        default=None,
        help="bundle whose hourly frames are read (default: the keeper); the "
        "hydro budgets always come from the keeper recipe's rebuild",
    )
    a = ap.parse_args()
    if a.span is not None:
        global SPAN_HOURLY
        SPAN_HOURLY = a.span
    a.out.mkdir(parents=True, exist_ok=True)
    rows, plants = [], []
    for y in a.years:
        r = census(y, a.out, a.dispatch_dir)
        rows.append(r["row"])
        plants += r["plants"]
        print(json.dumps(r["row"]), flush=True)
    pd.DataFrame(rows).to_csv(a.out / "soco93_pondage_census.csv", index=False)
    pd.DataFrame(plants).to_csv(a.out / "soco93_pondage_plants.csv", index=False)


if __name__ == "__main__":
    main()
