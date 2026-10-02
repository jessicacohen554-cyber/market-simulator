"""Close-out CAISO wave 1, steps 0c and 0d (ZERO LP): zonal gas basis sizing and the C3c-2021 census.

``tail`` (0d): census of the model's C3c 2021 tail hours on the fold bundle
(``rcaiso20_A_tp_2019_2021``). The model count is the scorer's own
construction (``render_calibration_html._tail_hours``: max over every zone's
P1 dual > $200, all 8,760 hours); the actual is the RT hub series of
``actual_lmp_hourly_CAISO.parquet`` (NaN outside the OASIS retention window).
Reports the count by date, month, argmax zone, RT coverage, the SDGE-only
share, and the like-for-like count on RT-covered hours only.

``basis`` (0c): first-order C3a shift of ``caiso_zonal_gas_basis`` for one
year. Rebuilds the keeper's fleet twice with ``replay_keeper.run_year_kwargs``
+ ``run_year(fleet_only=True)`` (the sanctioned zero-LP rebuild), flag off and
on, and takes the per-unit P0 marginal-cost delta. Attribution: in each hour,
the P0 marginal set is every unit dispatched > 0.5 MW whose base-cost MC is
within $0.05 of its zone's P0 dual; a zone's Δλ is the mean delta over the
marginal units in its price island (zones whose P0 dual matches within
$0.01), counting non-gas marginal units as zero. First order: no re-dispatch,
P0 marginal set applied to the P1-scored level. A bundle with no P0 sidecars
(post-W0 keepers) uses the committed P1 ``unit_marginal_<year>`` flags instead, with
price islands from the P1 zonal duals.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_closeout_caiso_w1_basis_tail.py tail
    PYTHONPATH=.:src:scripts python3 scripts/probes/_closeout_caiso_w1_basis_tail.py basis \
        --year 2021 --bundle results/calibration/rcaiso20_A_tp_2019_2021 --months 5,6,7,9,10,11,12
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]

FOLD = Path("results/calibration/rcaiso20_A_tp_2019_2021")
ACTUAL = Path("data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet")
BENCH = Path("data/raw/_validation-source/actual_lmp.json")
THRESHOLD = 200.0  # rubric §5 CAISO C3c threshold (calibration_verdict.TAIL_THRESHOLD)
IN_CAISO = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")


def _wide(sy: pd.DataFrame, col: str) -> pd.DataFrame:
    """Return the (hour x zone) pivot of one ``system_<year>`` column."""
    return sy.pivot(index="hour", columns="zone", values=col)


def census_tail(year: int = 2021) -> dict:
    """Return the C3c census of the fold's ``year`` tail hours."""
    sy = pd.read_parquet(FOLD / f"hourly/system_{year}.parquet")
    price = _wide(sy, "price")
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == year].set_index("hour")["rt"].reindex(range(8760))
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(8760), "h")
    mx = price.max(axis=1)
    tail = mx > THRESHOLD
    cov = rt.notna().to_numpy()
    others = price[[z for z in IN_CAISO if z != "SDGE"]].max(axis=1)
    t = pd.DataFrame(
        {"ts": ts[tail.to_numpy()], "price": mx[tail].to_numpy()},
        index=mx.index[tail],
    )
    return {
        "model_tail_hours": int(tail.sum()),
        "actual_rt_tail_hours": int((rt > THRESHOLD).sum()),
        "rt_covered_hours": int(cov.sum()),
        "first_rt_hour": str(ts[cov].min()),
        "tail_hours_rt_covered": int((tail.to_numpy() & cov).sum()),
        "tail_by_date": {
            str(k): int(v) for k, v in t.groupby(t.ts.dt.date).size().items()
        },
        "tail_by_argmax_zone": {
            str(k): int(v) for k, v in price.idxmax(axis=1)[tail].value_counts().items()
        },
        "tail_in_caiso_zones": int(
            (price[list(IN_CAISO)].max(axis=1) > THRESHOLD).sum()
        ),
        "tail_sdge_only": int(
            ((price["SDGE"] > THRESHOLD) & (others <= THRESHOLD)).sum()
        ),
        "tail_with_slack": int((_wide(sy, "slack").sum(axis=1)[tail] > 0).sum()),
        "tail_price_min_max": [
            round(float(t.price.min()), 1),
            round(float(t.price.max()), 1),
        ],
        "actual_rt_tail_by_month": {
            int(k): int(v)
            for k, v in pd.Series(ts[(rt > THRESHOLD).to_numpy()].month)
            .value_counts()
            .sort_index()
            .items()
        },
    }


def _rebuild(bundle: Path, year: int, arm: bool) -> dict:
    """Fleet-only rebuild of ``bundle``'s recipe for ``year``; ``arm`` sets the basis flag."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"]["caiso_zonal_gas_basis"] = True
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def size_basis(bundle: Path, year: int, months: list[int]) -> dict:
    """Return the first-order load-weighted Δλ of ``caiso_zonal_gas_basis`` for ``year``."""
    off = _rebuild(bundle, year, arm=False)
    on = _rebuild(bundle, year, arm=True)
    zones = list(off["iso_config"].zone_names)
    fa = off["fleet_arrays"]
    zi = np.asarray(fa.zone_idx)
    ids = np.array([u.unit_id for u in off["fleet"]])
    dfuel = on["fuel_prices"] - off["fuel_prices"]
    dmc = on["mc_base"] - off["mc_base"]
    gas = np.abs(dfuel).max(axis=1) > 1e-6
    sy = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    dem = _wide(sy, "demand")[zones].to_numpy().T
    p0 = bundle / f"hourly/p0_dispatch_{year}.parquet"
    if p0.exists():
        # P0 marginal set: dispatched units whose base-cost MC equals their zone's P0 dual.
        disp = pd.read_parquet(p0)
        if len(ids) != len(disp) or not (ids == disp.unit_id.to_numpy()).all():
            raise SystemExit(
                f"{year}: HEAD fleet ({len(ids)} units) != keeper P0 fleet ({len(disp)}) — G-DRIFT, not sizeable"
            )
        mw = np.vstack([np.frombuffer(b, dtype=np.float64) for b in disp.mw])
        pp = (
            pd.read_parquet(bundle / f"hourly/p0_prices_{year}.parquet")
            .pivot(index="hour", columns="zone", values="price")[zones]
            .to_numpy()
            .T
        )
        match = (mw > 0.5) & (np.abs(off["mc_base"] - pp[zi]) < 0.05)
    else:
        # P1 marginal set from the committed slim layer (scripts/lib/unit_marginal.py):
        # the LP's own price-setting columns; islands from the P1 zonal duals.
        um = pd.read_parquet(
            bundle / f"hourly/unit_marginal_{year}.parquet",
            columns=["unit_id", "hour", "marginal"],
            filters=[("marginal", "==", 1)],
        )
        row = {u: i for i, u in enumerate(ids)}
        missing = set(um.unit_id.astype(str)) - set(row)
        if missing:
            raise SystemExit(
                f"{year}: {len(missing)} marginal keeper units absent from the HEAD fleet — G-DRIFT, not sizeable"
            )
        pp = _wide(sy, "price")[zones].to_numpy().T
        match = np.zeros((len(ids), pp.shape[1]), dtype=bool)
        match[um.unit_id.astype(str).map(row).to_numpy(), um.hour.to_numpy()] = True
    n_z, n_t = pp.shape
    dl = np.zeros((n_z, n_t))
    for t in range(n_t):
        g = np.nonzero(match[:, t])[0]
        if g.size == 0:
            continue
        for z in range(n_z):
            isl = g[np.abs(pp[zi[g], t] - pp[z, t]) < 0.01]
            if isl.size:
                gg = isl[gas[isl]]
                if gg.size:
                    dl[z, t] = dmc[gg, t].mean() * gg.size / isl.size
    inz = [i for i, n in enumerate(zones) if n in IN_CAISO]
    w = dem[inz]
    ws = w.sum(axis=0)
    lw = (dl[inz] * w).sum(axis=0) / ws
    mon = (
        pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(n_t), "h")
    ).month.to_numpy()
    gated = np.isin(mon, months)
    bench = json.loads(BENCH.read_text())["CAISO"][str(year)]["rt_lw"]
    d_gated = float((lw * ws)[gated].sum() / ws[gated].sum())
    return {
        "year": year,
        "fuel_spread_by_zone": {
            zones[z]: round(float(dfuel[(zi == z) & gas].mean()), 3)
            for z in range(n_z)
            if ((zi == z) & gas).any()
        },
        "dlambda_lw_gated": round(d_gated, 2),
        "bench_rt_lw": bench,
        "c3a_pp": round(100 * d_gated / bench, 2),
        "monthly": [
            {
                "month": m,
                "gated": m in months,
                "dlambda_lw": round(
                    float((lw * ws)[mon == m].sum() / ws[mon == m].sum()), 2
                ),
                **{
                    f"d_{zones[i]}": round(float(dl[i, mon == m].mean()), 2)
                    for i in inz
                },
            }
            for m in range(1, 13)
        ],
    }


def main() -> None:
    """Dispatch the ``tail`` / ``basis`` sub-commands and print JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tail")
    b = sub.add_parser("basis")
    b.add_argument("--year", type=int, required=True)
    b.add_argument("--bundle", type=Path, required=True)
    b.add_argument("--months", default=",".join(str(m) for m in range(1, 13)))
    args = ap.parse_args()
    if args.cmd == "tail":
        out = census_tail()
    else:
        out = size_basis(
            args.bundle, args.year, [int(m) for m in args.months.split(",")]
        )
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
