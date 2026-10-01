"""NWPP-NEXT-14 phase 0 (ZERO LP): campd_per_unit_vintage_denominator on keeper #18.

Fleet-only rebuilds of keeper #18 (``results/calibration/nwppnext13pu_span``) on
its own recipe (``B``) and with ``campd_per_unit_vintage_denominator`` armed
(``PU``, kept as the variant key), which selects
``thermal_tranches-perunit-vintage-NWPP.csv``. Adapted verbatim from
``_nwppnext13_perunit_census.py`` (whose original docstring follows); only the
bundle and the flipped flag differ, plus a per-unit ``moved_units`` listing.

ORIGINAL: NWPP-NEXT-13 phase 0 (ZERO LP): campd_per_unit_attribution on keeper #17.

Fleet-only rebuilds of keeper #17 (``results/calibration/nwppnext12mr_span``) on
its own recipe (``B``) and with the ONE flag ``campd_per_unit_attribution``
armed (``PU``), which selects BOTH NWPP ``-perunit-`` companions (rule 19):

* ``data/raw/campd-unit-outages-perunit-NWPP.csv`` — the HEAD standard derive
  (== the keeper's ``-memberrepair-`` extract, Boardman rows included) re-routed
  per unit: Clark 2322's 24 GT peakers (2,951 windows) and Silverhawk 55841's
  2024 GTs A09/A10 (46) leave CC_REGULAR;
* ``data/raw/_processed-legacy/thermal_tranches-perunit-NWPP.csv``.

Reports, per year, per class: pmax, available TWh, and the per-(plant, class)
rows that move, beside each plant's EIA-923 net by prime mover. The test is
physics (available >= generated, rule 14), never a residual.

Usage::

    uv run python scripts/probes/_nwppnext13_perunit_census.py --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/nwppnext13pu_span"
GEN = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
VARIANTS = {"B": {}, "PU": {"campd_per_unit_vintage_denominator": True}}
# --flags overrides the armed set. (It also censused cc_subfloor_eia923_heat_rates,
# a field DELETED at the NWPP-NEXT-14 reconciliation in favour of the solved
# eia923_cc_family_heat_rates, rules 19 / 26; that --flags value no longer parses.)


def _frame(st: dict) -> pd.DataFrame:
    """One row per LP unit."""
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    mg = getattr(fa, "min_gen", None)
    return pd.DataFrame(
        {
            "unit_id": list(fa.unit_ids),
            "plant_code": np.asarray(fa.plant_code).astype(int),
            "group": list(fa.plant_group),
            "pmax": pmax,
            "avail_mwh": pmax * (av.sum(axis=1) if av.ndim == 2 else av * 8760),
            "heat_rate": np.asarray(fa.heat_rate, float),
            "min_gen_mwh": (
                np.asarray(mg, float).sum(axis=1)
                if mg is not None and np.ndim(mg) == 2
                else np.nan
            ),
        }
    )


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    ap.add_argument("--flags", nargs="+", default=None)
    args = ap.parse_args()
    if args.flags:
        VARIANTS["PU"] = {f: True for f in args.flags}

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.pipeline.reference import henry_hub_actual

    gen = pd.read_csv(GEN)
    pm_col = next(c for c in gen.columns if "prime" in c.lower())
    meta = json.loads((BUNDLE / "meta.json").read_text())
    res: dict[str, dict] = {}
    for y in args.years:
        gas = henry_hub_actual(rcf._load_reference(), y)
        fr = {}
        for v, flips in VARIANTS.items():
            kw = run_year_kwargs(meta)
            kw.update(derived_run_year_inputs(BUNDLE, y))
            kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **flips}
            if y <= 2022:
                kw["prb_overrides"]["hydro_backfill_year"] = None
            st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
            fr[v] = _frame(st)
            set_eia860_vintage(None)
        b, p = fr["B"], fr["PU"]
        d = b.merge(
            p, on=["unit_id", "plant_code", "group"], how="outer", suffixes=("", "_p")
        )
        added = sorted(set(p.unit_id) - set(b.unit_id))
        dropped = sorted(set(b.unit_id) - set(p.unit_id))
        for c in ("pmax", "avail_mwh", "heat_rate", "min_gen_mwh"):
            d[c] = d[c].fillna(0.0)
            d[c + "_p"] = d[c + "_p"].fillna(0.0)
        d = d.assign(
            d_avail=d.avail_mwh_p - d.avail_mwh,
            d_pmax=d.pmax_p - d.pmax,
            d_hr=d.heat_rate_p - d.heat_rate,
            d_ming=d.min_gen_mwh_p - d.min_gen_mwh,
        )
        cls = d.groupby("group")[["pmax", "avail_mwh", "d_avail", "d_pmax"]].sum()
        mv = d[
            (d.d_avail.abs() > 1)
            | (d.d_pmax.abs() > 1e-6)
            | (d.d_hr.abs() > 1e-9)
            | (d.d_ming.abs() > 1)
        ]
        by_pg = mv.groupby(["plant_code", "group"]).agg(
            pmax=("pmax", "sum"),
            avail_B=("avail_mwh", "sum"),
            d_avail=("d_avail", "sum"),
            d_pmax=("d_pmax", "sum"),
            n_hr=("d_hr", lambda s: int((s.abs() > 1e-9).sum())),
            d_ming=("d_ming", "sum"),
        )
        g = gen[(gen.year == y)]
        rows = []
        for (pc, grp), r in by_pg.iterrows():
            e = g[g.plant_id == pc].groupby(pm_col)["net_generation_mwh"].sum()
            rows.append(
                {
                    "plant": int(pc),
                    "group": grp,
                    "pmax": round(r.pmax, 1),
                    "avail_B_twh": round(r.avail_B / 1e6, 3),
                    "d_avail_twh": round(r.d_avail / 1e6, 3),
                    "d_pmax": round(r.d_pmax, 2),
                    "hr_units_moved": int(r.n_hr),
                    "d_min_gen_twh": round(r.d_ming / 1e6, 3)
                    if r.d_ming == r.d_ming
                    else None,
                    "eia923_twh_by_pm": {
                        str(k): round(v / 1e6, 3) for k, v in e.items()
                    },
                }
            )
        res[str(y)] = {
            "class_d_avail_twh": {
                k: round(v / 1e6, 3) for k, v in cls.d_avail.items() if abs(v) > 1
            },
            "class_d_pmax": {
                k: round(v, 2) for k, v in cls.d_pmax.items() if abs(v) > 1e-6
            },
            "moved": rows,
            "moved_units": [
                {
                    "unit_id": str(r.unit_id),
                    "pmax": round(float(r.pmax), 2),
                    "pmax_p": round(float(r.pmax_p), 2),
                    "d_min_gen_twh": round(float(r.d_ming) / 1e6, 4)
                    if r.d_ming == r.d_ming
                    else None,
                }
                for r in mv.itertuples()
            ],
            "units_added": added,
            "units_dropped": dropped,
        }
        print(json.dumps({y: res[str(y)]}), flush=True)
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
