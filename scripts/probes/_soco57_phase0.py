"""SOCO-57 phase 0 — is SOCO's CC_REGULAR fleet priced off a defective heat rate?

Zero-LP throughout (rule 32 ``[R-SHARD]`` (a)): every number here is read off the
designated keeper's own committed hourlies, the committed EIA-860 / eGRID
artifacts and the raw CAMPD unit-level files. No LP is solved.

Modes
-----
``hr``       -- the per-plant table: the model's CC heat rate against the
                CAMPD-metered steady-state rate, with the BOUNDARY GUARD that
                decides which plants the meter can speak for at all.
``boundary`` -- the guard on its own: CAMPD CC gross / EIA-923 CC net per plant
                per year. A plant whose steam turbine is not metered reads
                ~0.68, and its ``heatInput/grossLoad`` is then the
                COMBUSTION-TURBINE rate, not the combined-cycle rate.
``restack``  -- the greedy zero-LP bound on what repricing the flagged plants
                moves, per class and per plant, respecting min-gen floors.
``marginal`` -- what is marginal, and what is DISPLACEABLE, in the hours the
                under-priced plants carry headroom.
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
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: CAMPD states the SOCO footprint draws on (AL/GA/MS plus the FL panhandle).
STATES = ("AL", "GA", "MS", "FL")
#: Steady-operating-hour screen, the COAL deriver's window -- a combined cycle
#: is committed and cycles across its range like a steam unit, so a near-HSL
#: window would price it at its best point (see the derive's module docstring).
MIN_OPTIME = 0.99
#: Physical gross-basis band for a combined cycle, fixed on physics ex ante.
HR_MIN_GROSS, HR_MAX_GROSS = 5.0, 20.0
MIN_STEADY_HOURS = 200
#: CC class default parasitic fraction -> net/gross factor.
PF_DEFAULT = 0.975


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


def model_cc(bundle: Path, year: int) -> pd.DataFrame:
    """Per-plant model CC_REGULAR heat rate, capacity, fuel price and VOM."""
    built = _build(bundle, year)
    fa, fleet = built["fleet_arrays"], built["fleet"]
    rows = []
    for i, g in enumerate(fleet):
        if str(getattr(g, "plant_group", "") or "") != "CC_REGULAR":
            continue
        rows.append(
            {
                "plant": int(getattr(g, "plant_code", 0) or 0),
                "cap": float(np.asarray(fa.pmax)[i]),
                "hr_model": float(np.asarray(fa.heat_rate)[i]),
                "fuel": float(np.mean(np.asarray(built["fuel_prices"])[i])),
            }
        )
    df = pd.DataFrame(rows)
    return df.groupby("plant", as_index=False).agg(
        cap=("cap", "sum"), hr_model=("hr_model", "median"), fuel=("fuel", "median")
    )


def _campd_cc(years, codes) -> pd.DataFrame:
    frames = []
    for st in STATES:
        for y in years:
            f = _ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet"
            if not f.exists():
                continue
            d = pd.read_parquet(
                f,
                columns=[
                    "facilityId", "unitId", "opTime", "grossLoad",
                    "heatInput", "unitType",
                ],
            )
            d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
            d = d[d.facilityId.isin(codes)]
            if len(d):
                d["year"] = y
                frames.append(d)
    raw = pd.concat(frames, ignore_index=True)
    return raw[
        raw.unitType.astype(str).str.strip().str.casefold().str.startswith("combined cycle")
    ].copy()


def measured_cc(years, codes) -> pd.DataFrame:
    """CAMPD-metered steady-state CC heat rate, per plant, pooled over years."""
    cc = _campd_cc(years, codes)
    st = cc[(cc.opTime >= MIN_OPTIME) & (cc.grossLoad > 0) & (cc.heatInput > 0)].copy()
    st["hr"] = st.heatInput / st.grossLoad
    st = st[(st.hr >= HR_MIN_GROSS) & (st.hr <= HR_MAX_GROSS)]
    per_unit = st.groupby(["facilityId", "unitId"]).agg(
        hi=("heatInput", "sum"), gl=("grossLoad", "sum"), h=("hr", "size")
    ).reset_index()
    per_unit = per_unit[per_unit.h >= MIN_STEADY_HOURS]
    p = per_unit.groupby("facilityId").apply(
        lambda d: pd.Series(
            {
                "n_units": len(d),
                "steady_h": int(d.h.sum()),
                "gross_gwh": d.gl.sum() / 1e3,
                "hr_gross": d.hi.sum() / d.gl.sum(),
            }
        ),
        include_groups=False,
    ).reset_index()
    p["hr_meas"] = p.hr_gross / PF_DEFAULT
    return p


def boundary(years, codes) -> pd.DataFrame:
    """CAMPD CC gross / EIA-923 CC net, per plant per year. THE GUARD."""
    from market_sim.data import eia923

    spec = importlib.util.spec_from_file_location(
        "rcf", str(_ROOT / "scripts/run_calibration_full.py")
    )
    rcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcf)
    mon = eia923.load_monthly_generation()
    cc = _campd_cc(years, codes)
    out = []
    for y in years:
        fr = rcf._eia923_frame(y, mon, "SOCO")
        act = fr[fr.klass == "CC_REGULAR"].set_index("plant_id")["annual_mwh"]
        g = cc[cc.year == y].groupby("facilityId").grossLoad.sum().reset_index()
        g["eia_net"] = [float(act.get(int(p), np.nan)) for p in g.facilityId]
        g["ratio"] = g.grossLoad / g.eia_net
        g["year"] = y
        out.append(g[["facilityId", "year", "ratio"]])
    piv = pd.concat(out).pivot_table(index="facilityId", columns="year", values="ratio")
    piv["mean"] = piv.mean(axis=1)
    return piv



def restack(bundle: Path, year: int, deltas: dict[int, float]) -> pd.DataFrame:
    """Greedy zero-LP bound: reprice ``deltas`` ($/MWh, signed) and let those
    plants fill headroom by displacing the dearest ABOVE-FLOOR producing MW in
    the same hour. An UPPER bound -- it ignores network, ramp and storage."""
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    z = np.load(bundle / f"floors/{year}_P1.npz", allow_pickle=True)
    mg, flmap = z["min_gen"], {u: i for i, u in enumerate(z["unit_ids"])}
    uh = uh.copy()
    uh["mc_new"] = uh.mc + uh.plant_code.map(deltas).fillna(0.0)
    MW = uh.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum").fillna(0.0)
    units = MW.index.to_numpy()
    CAP = uh.pivot_table(index="unit_id", columns="hour", values="cap_mw", aggfunc="sum").fillna(0.0).reindex(units).to_numpy()
    MC = uh.pivot_table(index="unit_id", columns="hour", values="mc_new", aggfunc="mean").reindex(units).to_numpy()
    meta = uh.drop_duplicates("unit_id").set_index("unit_id").reindex(units)
    grp, pc = meta["plant_group"].to_numpy(), meta["plant_code"].to_numpy()
    MW = MW.to_numpy()
    FLOOR = np.zeros_like(MW)
    for i, u in enumerate(units):
        j = flmap.get(u)
        if j is not None:
            FLOOR[i] = mg[j][: MW.shape[1]]
    tgt = np.isin(pc, list(deltas))
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
                hi += 1; continue
            if disp[b] <= 1e-9:
                di += 1; continue
            if not (MC[a, t] < MC[b, t] - 1e-9):
                break
            q = min(head[a], disp[b])
            moved[a] += q; moved[b] -= q
            head[a] -= q; disp[b] -= q
    return pd.DataFrame({"unit": units, "grp": grp, "pc": pc, "dTWh": moved / 1e6})


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("hr", "boundary", "restack", "marginal"))
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--ref-year", type=int, default=2024)
    ap.add_argument("--min-dmc", type=float, default=1.0)
    args = ap.parse_args()
    bundle = Path(args.bundle)
    m = model_cc(bundle, args.ref_year)
    codes = set(m.plant.astype(int))
    if args.mode == "boundary":
        print(boundary(args.years, codes).round(4).to_string())
        return
    meas = measured_cc(args.years, codes)
    bnd = boundary(args.years, codes)["mean"]
    t = m.merge(meas, left_on="plant", right_on="facilityId", how="left")
    t["bound"] = [float(bnd.get(int(p), np.nan)) for p in t.plant]
    t["VALID"] = np.where((t.bound >= 0.90) & (t.bound <= 1.25), "ok", "REFUSE-boundary")
    t["d_hr"] = t.hr_model - t.hr_meas
    t["d_mc"] = t.d_hr * t.fuel
    if args.mode == "hr":
        print(t.sort_values("d_hr").to_string(index=False, float_format=lambda x: f"{x:9.4f}"))
        return
    flagged = t[(t.VALID == "ok") & (t.d_mc.abs() >= args.min_dmc)]
    print(f"FLAGGED (valid, |d_mc| >= {args.min_dmc}): {sorted(flagged.plant.astype(int))}")
    for y in args.years:
        my = model_cc(bundle.parent / f"{bundle.name[:-4]}{y}" if bundle.name[-4:].isdigit() else bundle, y)
        fuel_y = float(my.fuel.median())
        dl = {int(r.plant): float(-(r.d_hr) * fuel_y) for r in flagged.itertuples()}
        bdir = Path(str(bundle).replace(str(args.ref_year), str(y)))
        res = restack(bdir, y, dl)
        byc = res.groupby("grp").dTWh.sum().sort_values()
        print(f"\n=== {y}  gas ${fuel_y:.3f}/MMBtu   deltas " +
              ", ".join(f"{k}:{v:+.2f}" for k, v in sorted(dl.items())))
        print(byc.round(4).to_string())
        cc = res[res.grp == "CC_REGULAR"].groupby("pc").dTWh.sum().sort_values()
        print("  CC per-plant:", ", ".join(f"{int(k)}:{v:+.3f}" for k, v in cc.items() if abs(v) > 0.001))


if __name__ == "__main__":
    main()
