"""R-NWPP phase 0: the corrected-backcast-input census for NWPP 2019–2025. ZERO LP.

Rebuilds NWPP's LP-facing fleet with ``run_year(fleet_only=True)`` per year
under two recipes and reports what the audit
(``docs/handoffs/AUDIT-backcast-inputs-860-heatrate-outage-2026-09-24.md``
§5.3.5) asks phase 0 to show:

* ``pre``  — the incumbent keeper recipe (``nwpp49_ror_span``) in its
  pre-F1 posture: the six F1 backcast defaults pinned to their recorded
  values (vintage OFF, measured CT/ST/CC/CHP OFF, coal ON), no short/partial
  outage families. For 2023–2025 this is the keeper's own fleet.
* ``arm``  — the R-NWPP recipe: the same keeper recipe plus every F1 flag ON
  and the F2 outage families the PRECOMMIT arms (short-coal, unit-partial).

Per year: (a) the EIA-860 source the fleet resolved (``vintage_<Y>`` or the
canonical snapshot), (b) thermal MW whose loaded heat rate is still the
``HEAT_RATE_BINS`` class-table value, listed by plant, (c) the per-class MW,
available TWh and capacity-weighted heat rate, and (d) outage-family window
counts / MW-hours for the year from the armed extracts.

The recipe comes from ``scripts/replay_keeper.run_year_kwargs`` (the only
sanctioned fleet-only reconstruction, caiso-244). Years the keeper never
solved (2019–2022) have no ``class_hourly`` sidecar, so
``derived_run_year_inputs`` is taken from the keeper's 2023 sidecar and
reported as such.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_rnwpp_census.py \
        [--years 2019 ... 2025] [--out results/calibration/_rnwpp_census.json]
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

BUNDLE = Path("results/calibration/nwpp49_ror_span")

#: F1 backcast defaults, pinned explicitly in both recipes so neither reads an
#: ambient default: the keeper's recorded posture vs the R-NWPP arm.
F1_FLAGS_PRE = {
    "eia860_vintage_tracks_solve_year": False,
    "measured_ct_heat_rates": False,
    "measured_coal_heat_rates": True,
    "measured_st_heat_rates": False,
    "measured_cc_heat_rates": False,
    "measured_chp_heat_rates": False,
}
F1_FLAGS_ARM = {k: True for k in F1_FLAGS_PRE}
#: F2 outage families armed by the R-NWPP PRECOMMIT (short-gas deliberately
#: NOT armed — PRECOMMIT §3: the merit guard separates nothing on NWPP).
OUTAGE_ARM = {"unit_outage_short_windows": True, "unit_partial_outage_windows": True}

ARRAY_FIELDS = (
    "pmax", "pmin", "heat_rate", "vom", "emission_rate", "nox_rate", "zone_idx",
    "fuel_type_idx", "availability", "efficiency_bin", "plant_code", "min_gen",
)
THERMAL = ("coal", "gas_cc", "gas_ct", "gas_st", "oil")


def _class_table_values() -> set[float]:
    """Every ``HEAT_RATE_BINS`` value (MMBtu/MWh), rounded, for the audit heuristic."""
    from market_sim.config.constants import HEAT_RATE_BINS

    vals: set[float] = set()

    def walk(x):
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, (list, tuple)):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)):
            vals.add(round(float(x), 4))

    walk(HEAT_RATE_BINS)
    return vals


def _build(year: int, flags: dict) -> dict:
    """Fleet-only rebuild of the keeper recipe for one year under ``flags``."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    src_year = year if (BUNDLE / "hourly" / f"class_hourly_{year}.parquet").exists() else 2023
    kw.update(derived_run_year_inputs(BUNDLE, src_year))
    kw["prb_overrides"] = copy.deepcopy(kw.get("prb_overrides") or {})
    params = inspect.signature(run_year).parameters
    for k, v in flags.items():
        if k in params:
            kw[k] = v
        else:
            kw["prb_overrides"][k] = v
    gas = meta["gas_prices"].get(str(year))
    if gas is None:  # the solve's own rule (run_calibration_full._recorded_config)
        from market_sim.pipeline import reference as _ref

        gas = float(_ref.henry_hub_actual(_ref.load_reference(), int(year)))
    built = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
    built["_derived_from_year"] = src_year
    built["_gas"] = gas
    return built


def _frame(built: dict) -> pd.DataFrame:
    """One row per LP unit: id, plant, class, fuel, pmax, hr, available TWh."""
    fa, fleet = built["fleet_arrays"], built["fleet"]
    avail = np.asarray(fa.availability, float)
    pmax = np.asarray(fa.pmax, float)
    mwh = (avail * pmax[:, None]).sum(1) if avail.ndim == 2 else avail * pmax * 8760
    return pd.DataFrame({
        "unit_id": list(fa.unit_ids),
        "plant": np.asarray(fa.plant_code).astype(int),
        "name": [str(getattr(g, "name", "") or getattr(g, "plant_name", "")) for g in fleet],
        "klass": [str(getattr(g, "plant_group", None) or getattr(g, "fuel_type", "")) for g in fleet],
        "fuel": [str(getattr(g, "fuel_type", "")) for g in fleet],
        "pmax": pmax,
        "hr": np.asarray(fa.heat_rate, float),
        "avail_twh": mwh / 1e6,
    })


def _digest(built: dict) -> str:
    """sha256 over every LP-facing FleetArrays field plus mc_base."""
    fa = built["fleet_arrays"]
    h = hashlib.sha256()
    h.update("|".join(fa.unit_ids).encode())
    for f in ARRAY_FIELDS:
        v = getattr(fa, f, None)
        if v is not None:
            h.update(np.ascontiguousarray(np.asarray(v)).tobytes())
    h.update(np.ascontiguousarray(np.asarray(built["mc_base"], float)).tobytes())
    return h.hexdigest()


def _eia860_source(year: int, flags: dict) -> str:
    """The EIA-860 directory a backcast year resolves to under ``flags``."""
    from market_sim.config.paths import RAW_DATA_DIR

    vdir = RAW_DATA_DIR / "eia-860" / f"vintage_{year}"
    if flags.get("eia860_vintage_tracks_solve_year") and vdir.exists():
        return f"vintage_{year}"
    return "canonical (2025ER snapshot)"


def _outage_counts(year: int) -> dict:
    """Windows / MW-hours starting in ``year`` for each NWPP outage family file."""
    from market_sim.config.paths import RAW_DATA_DIR

    out = {}
    for fam, fn in (("std", "campd-unit-outages-NWPP.csv"),
                    ("short_coal", "campd-unit-outages-short-NWPP.csv"),
                    ("short_gas (NOT armed)", "campd-unit-outages-shortgas-NWPP.csv"),
                    ("partial", "campd-partial-outages-NWPP.csv")):
        p = RAW_DATA_DIR / fn
        if not p.exists():
            out[fam] = None
            continue
        d = pd.read_csv(p)
        d["y"] = pd.to_datetime(d["outage_start"]).dt.year
        d = d[d.y == year]
        mw = d["unit_capacity_mw"].astype(float)
        if "derate_factor" in d:
            mw = (1.0 - d["derate_factor"].astype(float)) * mw
        out[fam] = {"windows": int(len(d)),
                    "gwh": round(float((mw * d["duration_days"].astype(float) * 24).sum() / 1e3), 1),
                    "plants": int(d["facility_id"].nunique())}
    return out


def census(year: int, bins: set[float]) -> dict:
    """Pre vs arm fleet census for one year."""
    rec = {"year": year}
    frames = {}
    for tag, flags in (("pre", F1_FLAGS_PRE), ("arm", {**F1_FLAGS_ARM, **OUTAGE_ARM})):
        b = _build(year, flags)
        f = _frame(b)
        frames[tag] = f
        th = f[f.fuel.isin(THERMAL)]
        on_bin = th[th.hr.round(4).isin(bins)]
        rec[tag] = {
            "eia860_source": _eia860_source(year, flags),
            "derived_inputs_from_year": b["_derived_from_year"],
            "gas_price": b["_gas"],
            "n_units": int(len(f)),
            "digest": _digest(b),
            "thermal_mw": round(float(th.pmax.sum()), 1),
            "class_table_mw": round(float(on_bin.pmax.sum()), 1),
            "class_table_share_pct": round(100 * float(on_bin.pmax.sum()) / max(float(th.pmax.sum()), 1e-9), 2),
            "class_table_plants": on_bin.groupby(["plant", "name", "klass"]).pmax.sum().round(1)
            .reset_index().to_dict("records"),
            "by_class": f.groupby("klass").apply(
                lambda g: pd.Series({"mw": round(float(g.pmax.sum()), 1),
                                     "avail_twh": round(float(g.avail_twh.sum()), 3),
                                     "hr_cw": round(float((g.hr * g.pmax).sum() / max(g.pmax.sum(), 1e-9)), 4)}),
                include_groups=False).reset_index().to_dict("records"),
        }
    a, b = frames["pre"], frames["arm"]
    pa = a[a.fuel.isin(THERMAL)].groupby(["plant", "name"]).agg(mw=("pmax", "sum"), twh=("avail_twh", "sum"))
    pb = b[b.fuel.isin(THERMAL)].groupby(["plant", "name"]).agg(mw=("pmax", "sum"), twh=("avail_twh", "sum"))
    m = pa.join(pb, how="outer", lsuffix="_pre", rsuffix="_arm").fillna(0.0)
    m["d_mw"] = m.mw_arm - m.mw_pre
    m["d_twh"] = m.twh_arm - m.twh_pre
    rec["thermal_plant_moves"] = m[(m.d_mw.abs() > 1) | (m.d_twh.abs() > 0.01)].round(3) \
        .reset_index().sort_values("d_twh").to_dict("records")
    rec["outages"] = _outage_counts(year)
    return rec


def main() -> None:
    """Run the census for every year and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--out", type=Path, default=Path("results/calibration/_rnwpp_census.json"))
    args = ap.parse_args()
    bins = _class_table_values()
    out = []
    for y in args.years:
        r = census(y, bins)
        out.append(r)
        for tag in ("pre", "arm"):
            s = r[tag]
            print(f"{y} {tag:<3} {s['eia860_source']:<28} units {s['n_units']:4d}  thermal "
                  f"{s['thermal_mw']:9.1f} MW  class-table {s['class_table_mw']:7.1f} MW "
                  f"({s['class_table_share_pct']:.2f} %)")
        print(f"   outages {r['outages']}")
        args.out.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
