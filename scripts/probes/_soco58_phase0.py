"""SOCO-58 phase 0 — why is SOCO's coal under-dispatched, and what holds it down?

Zero-LP throughout (rule 32 ``[R-SHARD]`` (a)): every number here is read off the
designated keeper's own committed hourlies, its committed floor sidecars and a
``fleet_only`` rebuild off its own recipe. **No LP is solved.**

The object is the SOCO-57 named successor: 2024 ``COAL_PRB`` is −5.781 TWh short
of its actual and C4 2024 coal FAILS at NRMSE 0.309 / r 0.829, while 2023 and
2025 both pass.

Modes
-----
``markup``   -- THE FINDING. The realized P1 startup-amortization markup per
                tranche, reconstructed as ``mc(P1) − mc_base``, against the
                ``coal_warm_committed`` exemption predicate
                (``fuel_type == "coal" and must_run_pct > 0``). This is the
                rule 19 ``[R-ONE-MECH]`` scope proof at the grain the mechanism
                actually moves — the markup is applied at the P0→P1 seam, so it
                is invisible on the fleet grains ``_soco57_rule19.py`` reads.
``avail``    -- reading (1): coal availability and utilisation per plant-year,
                and THE CONTRADICTION TEST (hours in which the model's own
                availability ceiling sits BELOW the plant's measured CAMPD
                output in that very hour).
``reach``    -- check A: the distance, in $/MWh and TWh-in-reach. Per exempted
                tranche, how much headroom the de-marked-up offer puts in merit.
``restack``  -- the greedy zero-LP bound on what the exemption moves, per class
                and per plant, respecting min-gen floors. Keyed by ``unit_id``
                (tranche grain), not ``plant_code``: only the ``_committed``
                tranche is repriced.
``c4``       -- the 2024 coal hourly shape: where in the year the NRMSE sits,
                and whether the residual is level or shape.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: CAMPD states the SOCO footprint draws on (AL/GA/MS plus the FL panhandle).
STATES = ("AL", "GA", "MS", "FL")
#: The exemption's own predicate, transcribed from
#: ``model/commitment.py::compute_monthly_markup``.
EXEMPT = lambda g: (
    str(getattr(g, "fuel_type", "")) == "coal"
    and float(getattr(g, "must_run_pct", 0.0) or 0.0) > 0.0
)


def _build(bundle: Path, year: int, overrides: dict | None = None):
    """``run_year(fleet_only=True)`` off a committed bundle's own recipe."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if overrides:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"].update(overrides)
    return run_year(
        year, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw
    )


def _hourly_price(bundle: Path, year: int) -> pd.Series:
    """Load-weighted system price per hour, from the committed system sidecar."""
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    if "pass" in s.columns:
        s = s[s["pass"] == "P1"]
    return s.groupby("hour").apply(
        lambda d: float(np.average(d.price, weights=np.maximum(d.demand, 1e-9))),
        include_groups=False,
    )


def markup(bundle: Path, year: int) -> pd.DataFrame:
    """Realized P1 markup per tranche, and the exemption's exact scope.

    The startup amortization is added at the P0→P1 seam, so it is absent from
    ``mc_base``. Reconstructing it as ``mc(P1) − mc_base`` measures the markup
    the keeper's own scored solve actually carried.
    """
    built = _build(bundle, year)
    fleet, fa = built["fleet"], built["fleet_arrays"]
    mcb = np.asarray(built["mc_base"])
    rows = []
    for i, g in enumerate(fleet):
        uid = str(getattr(g, "unit_id", "") or getattr(g, "name", ""))
        base = mcb[i] if mcb.ndim == 1 else mcb[i, :]
        rows.append(
            {
                "unit_id": uid,
                "plant": int(getattr(g, "plant_code", 0) or 0),
                "plant_group": str(getattr(g, "plant_group", "") or ""),
                "fuel_type": str(getattr(g, "fuel_type", "") or ""),
                "pmax": float(np.asarray(fa.pmax)[i]),
                "startup_per_mw": float(getattr(g, "startup_cost_per_mw", 0.0) or 0.0),
                "must_run_pct": float(getattr(g, "must_run_pct", 0.0) or 0.0),
                "exempt_by_arm": bool(EXEMPT(g)),
                "mc_base_med": float(np.median(np.atleast_1d(base))),
            }
        )
    fl = pd.DataFrame(rows)

    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[uh["pass"] == "P1"]
    obs = uh.groupby("unit_id").agg(
        mc_p1_med=("mc", "median"),
        avail_TWh=("cap_mw", lambda s: s.sum() / 1e6),
        gen_TWh=("mw", lambda s: s.sum() / 1e6),
    )
    out = fl.merge(obs, on="unit_id", how="left")
    out["markup_med"] = (out.mc_p1_med - out.mc_base_med).round(3)
    return out


def contradiction(bundle: Path, year: int, group_prefix: str = "COAL") -> pd.DataFrame:
    """THE CONTRADICTION TEST: model availability ceiling vs measured CAMPD output.

    Hours in which the plant's own metered output exceeds the ceiling the model
    gives it — i.e. generation the model is physically forbidden from producing.
    """
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[(uh["pass"] == "P1") & uh.plant_group.astype(str).str.startswith(group_prefix)]
    cap = uh.groupby(["plant_code", "hour"]).cap_mw.sum().unstack(fill_value=0.0)

    frames = []
    for st in STATES:
        f = _ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "primaryFuelInfo"]
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d.facilityId.isin(cap.index)]
        if len(d):
            frames.append(d)
    if not frames:
        return pd.DataFrame()
    raw = pd.concat(frames, ignore_index=True)
    raw = raw[raw.primaryFuelInfo.astype(str).str.contains("Coal", case=False, na=False)]
    raw["ts"] = pd.to_datetime(raw.date) + pd.to_timedelta(raw.hour, unit="h")
    raw = raw.sort_values("ts")
    raw["h"] = raw.groupby("facilityId").ts.transform(
        lambda s: (s - s.min()).dt.total_seconds() // 3600
    ).astype(int)
    meas = raw.groupby(["facilityId", "h"]).grossLoad.sum().unstack(fill_value=0.0)

    rows = []
    for pl in cap.index:
        if pl not in meas.index:
            continue
        n = min(cap.shape[1], meas.shape[1])
        c, m = cap.loc[pl].to_numpy()[:n], meas.loc[pl].to_numpy()[:n]
        short = np.maximum(m - c, 0.0)
        rows.append(
            {
                "plant": int(pl),
                "hours_forbidden": int((short > 1.0).sum()),
                "TWh_forbidden": round(float(short.sum()) / 1e6, 4),
                "max_MW": round(float(short.max()), 1),
                "cap_p50": round(float(np.median(c)), 1),
                "meas_p50": round(float(np.median(m)), 1),
            }
        )
    return pd.DataFrame(rows).sort_values("TWh_forbidden", ascending=False)


def reach(bundle: Path, year: int) -> pd.DataFrame:
    """Check A: per exempted tranche, the markup removed and the TWh it reaches."""
    mk = markup(bundle, year)
    tgt = mk[mk.exempt_by_arm & (mk.startup_per_mw > 0)]
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[uh["pass"] == "P1"]
    px = _hourly_price(bundle, year)
    rows = []
    for _, r in tgt.iterrows():
        d = uh[uh.unit_id == r.unit_id].merge(
            px.rename("price"), left_on="hour", right_index=True
        )
        head = np.maximum(d.cap_mw - d.mw, 0.0)
        arm_mc = d.mc - float(r.markup_med)
        rows.append(
            {
                "unit_id": r.unit_id,
                "plant": int(r.plant),
                "mc_now": round(float(d.mc.median()), 2),
                "mc_arm": round(float(arm_mc.median()), 2),
                "markup": round(float(r.markup_med), 2),
                "avail_TWh": round(float(d.cap_mw.sum()) / 1e6, 3),
                "gen_TWh": round(float(d.mw.sum()) / 1e6, 3),
                "head_TWh": round(float(head.sum()) / 1e6, 3),
                "h_merit_now": int((d.mc <= d.price).sum()),
                "h_merit_arm": int((arm_mc <= d.price).sum()),
                "reach_TWh": round(float(head[arm_mc <= d.price].sum()) / 1e6, 3),
            }
        )
    return pd.DataFrame(rows)


def restack(bundle: Path, year: int, deltas: dict[str, float]) -> pd.DataFrame:
    """Greedy zero-LP bound, keyed by ``unit_id`` (tranche grain).

    Reprices ``deltas`` ($/MWh, signed, per unit_id) and lets those tranches
    fill headroom by displacing the dearest ABOVE-FLOOR producing MW in the same
    hour. An UPPER bound that ignores network, ramp and storage — and, as
    SOCO-57 §6 measured, a bound that systematically UNDERSTATES the movement
    because it cannot model the LP re-committing units.
    """
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[uh["pass"] == "P1"].copy()
    z = np.load(bundle / f"floors/{year}_P1.npz", allow_pickle=True)
    mg, flmap = z["min_gen"], {u: i for i, u in enumerate(z["unit_ids"])}
    uh["mc_new"] = uh.mc + uh.unit_id.map(deltas).fillna(0.0)

    MW = uh.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum").fillna(0.0)
    units = MW.index.to_numpy()
    CAP = (
        uh.pivot_table(index="unit_id", columns="hour", values="cap_mw", aggfunc="sum")
        .fillna(0.0)
        .reindex(units)
        .to_numpy()
    )
    MC = (
        uh.pivot_table(index="unit_id", columns="hour", values="mc_new", aggfunc="mean")
        .reindex(units)
        .to_numpy()
    )
    meta = uh.drop_duplicates("unit_id").set_index("unit_id").reindex(units)
    grp, pc = meta["plant_group"].to_numpy(), meta["plant_code"].to_numpy()
    MW = MW.to_numpy()
    FLOOR = np.zeros_like(MW)
    for i, u in enumerate(units):
        j = flmap.get(u)
        if j is not None:
            FLOOR[i] = mg[j][: MW.shape[1]]

    tgt = np.isin(units, list(deltas))
    moved = np.zeros(len(units))
    for t in range(MW.shape[1]):
        head = np.where(tgt, np.maximum(CAP[:, t] - MW[:, t], 0.0), 0.0)
        disp = np.where(~tgt, np.maximum(MW[:, t] - FLOOR[:, t], 0.0), 0.0)
        if head.sum() <= 0.01 or disp.sum() <= 0.01:
            continue
        oh = np.argsort(np.where(head > 0, MC[:, t], np.inf))
        od = np.argsort(np.where(disp > 0, -MC[:, t], np.inf))
        hi = di = 0
        while hi < len(oh) and di < len(od):
            a, b = oh[hi], od[di]
            if head[a] <= 1e-9:
                hi += 1
                continue
            if disp[b] <= 1e-9:
                di += 1
                continue
            if not (MC[a, t] < MC[b, t] - 1e-9):
                break
            q = min(head[a], disp[b])
            moved[a] += q
            moved[b] -= q
            head[a] -= q
            disp[b] -= q
    return pd.DataFrame({"unit": units, "grp": grp, "pc": pc, "dTWh": moved / 1e6})


def c4(bundle: Path, year: int) -> pd.DataFrame:
    """Where the 2024 coal C4 residual sits: monthly level vs shape."""
    import gzip

    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[(uh["pass"] == "P1") & uh.plant_group.astype(str).str.startswith("COAL")]
    model = uh.groupby("hour").mw.sum()

    bench = json.loads(
        gzip.open(_ROOT / f"frontend/data/backcast/bench/SOCO/{year}.json.gz").read()
    )["bench"]
    e930 = bench.get("e930", {})
    rows = [
        {
            "model_TWh": round(float(model.sum()) / 1e6, 3),
            "e930_coal_TWh": e930.get("coal"),
            "coal_cems_TWh": e930.get("coal_cems"),
            "model_p50_MW": round(float(model.median()), 1),
            "model_p95_MW": round(float(model.quantile(0.95)), 1),
            "model_min_MW": round(float(model.min()), 1),
        }
    ]
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("markup", "avail", "reach", "restack", "c4"))
    ap.add_argument("--bundle", required=True, type=Path)
    ap.add_argument("--year", required=True, type=int)
    args = ap.parse_args()
    pd.set_option("display.width", 200)

    if args.mode == "markup":
        mk = markup(args.bundle, args.year)
        paying = mk[mk.startup_per_mw > 0]
        print("=== tranches PAYING a startup markup today (startup_cost_per_mw > 0) ===")
        print(
            paying[
                [
                    "unit_id", "plant_group", "fuel_type", "pmax", "startup_per_mw",
                    "must_run_pct", "exempt_by_arm", "mc_base_med", "mc_p1_med",
                    "markup_med", "avail_TWh", "gen_TWh",
                ]
            ]
            .sort_values(["fuel_type", "markup_med"], ascending=[True, False])
            .to_string(index=False)
        )
        print()
        ex = mk[mk.exempt_by_arm]
        print(f"EXEMPT SET (arm): {len(ex)} tranches, {ex.pmax.sum():.1f} MW")
        print(f"  of which pay a markup today: {int((ex.startup_per_mw > 0).sum())}")
        print(
            f"  coal tranches paying a markup that the arm does NOT exempt: "
            f"{int(((mk.fuel_type == 'coal') & (mk.startup_per_mw > 0) & ~mk.exempt_by_arm).sum())}"
        )
        print(
            f"  NON-coal tranches touched by the arm: "
            f"{int(((mk.fuel_type != 'coal') & mk.exempt_by_arm).sum())}"
        )
    elif args.mode == "avail":
        uh = pd.read_parquet(args.bundle / f"hourly/unit_hourly_{args.year}.parquet")
        uh = uh[(uh["pass"] == "P1") & uh.plant_group.astype(str).str.startswith("COAL")]
        g = uh.groupby("plant_code").agg(
            avail_TWh=("cap_mw", lambda s: s.sum() / 1e6),
            gen_TWh=("mw", lambda s: s.sum() / 1e6),
        )
        g["util"] = (g.gen_TWh / g.avail_TWh).round(3)
        print("=== coal availability and utilisation ===")
        print(g.round(3).to_string())
        print()
        print("=== THE CONTRADICTION TEST (ceiling below own measured output) ===")
        print(contradiction(args.bundle, args.year).to_string(index=False))
    elif args.mode == "reach":
        r = reach(args.bundle, args.year)
        print(r.to_string(index=False))
        print(f"\nTOTAL reach: {r.reach_TWh.sum():.3f} TWh")
    elif args.mode == "restack":
        mk = markup(args.bundle, args.year)
        tgt = mk[mk.exempt_by_arm & (mk.startup_per_mw > 0)]
        deltas = {r.unit_id: -float(r.markup_med) for _, r in tgt.iterrows()}
        print(f"repricing {len(deltas)} tranches: "
              + ", ".join(f"{k} {v:+.2f}" for k, v in deltas.items()))
        d = restack(args.bundle, args.year, deltas)
        print()
        print(d.groupby("grp").dTWh.sum().round(4).sort_values().to_string())
        print()
        print(d[d.dTWh.abs() > 0.01].sort_values("dTWh").round(4).to_string(index=False))
    else:
        print(c4(args.bundle, args.year).to_string(index=False))


if __name__ == "__main__":
    main()
