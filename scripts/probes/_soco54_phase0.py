"""SOCO-54 phase 0 — zero-LP offer-stack census for SOCO's gas fleet.

Modes
-----
``stack``  -- per LP unit: heat rate, fuel price, VOM, resulting ``mc_base``,
              with EIA-860 owner/sector and the plant's own EIA-923 actual, so
              the MERIT ORDER the LP sees can be read against the merit order
              the real system ran.  Answers SOCO-54 phase-0 check #3.
``rule19`` -- the two-grain rule 19 ``[R-ONE-MECH]`` proof (``fuel_prices`` and
              ``mc_base``) for an arm expressed as ``--set field=value``.

Every mode is a ``run_year(..., fleet_only=True)`` rebuild off a committed
bundle's own ``meta.json`` — NO LP is solved (rule 32(a) ``[R-SHARD]``).
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _build(bundle: Path, year: int, overrides: dict | None = None):
    """``run_year(fleet_only=True)`` off a committed bundle's recipe."""
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


def _owner_table() -> pd.DataFrame:
    p = pd.read_parquet(_ROOT / "data/raw/eia-860/eia860_plant.parquet")
    return p.drop_duplicates("Plant Code").set_index("Plant Code")[
        ["Plant Name", "Utility Name", "Sector Name"]
    ]


def _actuals(year: int) -> pd.Series:
    import importlib.util

    from market_sim.data import eia923

    spec = importlib.util.spec_from_file_location(
        "rcf", str(_ROOT / "scripts/run_calibration_full.py")
    )
    rcf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rcf)
    fr = rcf._eia923_frame(year, eia923.load_monthly_generation(), "SOCO")
    return fr.set_index(["plant_id", "klass"])["annual_mwh"] / 1e6


def _stack(bundle: Path, years: list[int], classes: tuple[str, ...]) -> None:
    own = _owner_table()
    for year in years:
        built = _build(bundle, year)
        fa, fleet = built["fleet_arrays"], built["fleet"]
        act = _actuals(year)
        rows = []
        for i, g in enumerate(fleet):
            grp = str(getattr(g, "plant_group", "") or "")
            if classes and grp not in classes:
                continue
            code = getattr(g, "plant_code", None)
            hr = float(np.asarray(fa.heat_rate)[i])
            vom = float(np.asarray(fa.vom)[i])
            fp = np.asarray(built["fuel_prices"])[i]
            rows.append(
                {
                    "plant": code,
                    "klass": grp,
                    "unit": getattr(g, "name", "")[-30:],
                    "cap": float(np.asarray(fa.pmax)[i]),
                    "hr": hr,
                    "fuel": float(np.mean(fp)),
                    "vom": vom,
                    "mc": hr * float(np.mean(fp)) + vom,
                }
            )
        df = pd.DataFrame(rows)
        if df.empty:
            print(f"{year}: no units in {classes}")
            continue
        byp = df.groupby(["plant", "klass"], as_index=False).agg(
            cap=("cap", "sum"), hr=("hr", "median"), fuel=("fuel", "median"),
            vom=("vom", "median"), mc=("mc", "median"),
        )
        byp["actual"] = [
            float(act.get((int(p), k), np.nan)) for p, k in zip(byp["plant"], byp["klass"])
        ]
        byp = byp.sort_values("mc")
        print("=" * 122)
        print(f"YEAR {year}   OFFER STACK, ascending mc   (bundle {bundle.name})")
        print(
            f"  {'mc$':>7s} {'plant':>7s} {'klass':11s} {'name':25s} {'utility':28s} "
            f"{'cap':>7s} {'HR':>6s} {'$/MMBtu':>8s} {'vom':>5s} {'actTWh':>7s}"
        )
        for _, r in byp.iterrows():
            o = own.loc[int(r["plant"])] if int(r["plant"]) in own.index else None
            print(
                f"  {r['mc']:7.2f} {int(r['plant']):7d} {r['klass']:11s} "
                f"{(o['Plant Name'] if o is not None else '?')[:25]:25s} "
                f"{(o['Utility Name'] if o is not None else '?')[:28]:28s} "
                f"{r['cap']:7.1f} {r['hr']:6.3f} {r['fuel']:8.3f} {r['vom']:5.2f} "
                f"{r['actual']:7.3f}"
            )


def _rule19(bundle: Path, years: list[int], overrides: dict) -> None:
    for year in years:
        a = _build(bundle, year)
        b = _build(bundle, year, overrides)
        for key in ("fuel_prices", "mc_base"):
            x, y = np.asarray(a[key]), np.asarray(b[key])
            groups = [str(getattr(g, "plant_group", "")) for g in a["fleet"]]
            d = np.abs(x - y)
            per = {}
            for i, grp in enumerate(groups):
                per[grp] = max(per.get(grp, 0.0), float(d[i].max()))
            print(f"{year} {key}: global max|d| = {float(d.max()):.12f}")
            for grp in sorted(per):
                if per[grp] > 0:
                    print(f"    {grp:14s} max|d| {per[grp]:.12f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("stack", "rule19"))
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--classes", default="CT_PEAKER,ST_GAS,CC_REGULAR")
    ap.add_argument("--set", dest="sets", action="append", default=[])
    a = ap.parse_args()
    bundle = Path(a.bundle)
    if a.mode == "stack":
        _stack(bundle, a.years, tuple(x for x in a.classes.split(",") if x))
    else:
        ov = {}
        for s in a.sets:
            k, v = s.split("=", 1)
            ov[k] = json.loads(v)
        _rule19(bundle, a.years, ov)


if __name__ == "__main__":
    main()
