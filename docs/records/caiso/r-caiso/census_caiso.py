"""R-CAISO phase-0 census (zero LP): fleet heat-rate sources + outage families, 2019-2025.

Two postures, each loaded exactly the way ``scripts/run_calibration.py`` builds the
CAISO backcast thermal fleet (``set_eia860_vintage`` → ``load_fleet_from_csv`` +
``load_retired_within_window``), without building or solving an LP:

* ``keeper`` — the incumbent caiso-290 recipe: canonical 2025ER snapshot + COD ramp
  + retiree parquet; measured CT + CHP, eGRID family ON; ST / CC OFF.
* ``treatment`` — the R-CAISO recipe: year-matched ``vintage_<Y>`` (canonical for
  2025), measured CT + CHP + ST + CC, eGRID family ON.

For every thermal unit online in the year it attributes the loaded heat rate to a
source: ``class_table`` (equals a ``HEAT_RATE_BINS`` value AND the plant has no eGRID
rate in the active table), else ``plant_specific``. Also reports the per-family CAMPD
outage windows / MW-h that fall in each year for CAISO's fleet.

Usage: python docs/handoffs/r-caiso/census_caiso.py --out docs/handoffs/r-caiso/census_caiso.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import HEAT_RATE_BINS  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    RAW_DATA_DIR,
    resolve_backcast_eia860_vintage,
    set_eia860_vintage,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.fleet.eia860 import ba_codes, load_retired_within_window  # noqa: E402

ISO = "CAISO"
YEARS = tuple(range(2019, 2026))
THERMAL = ("coal", "gas_cc", "gas_ct", "gas_st", "oil")
POSTURES = {
    "keeper": dict(track=False, ct=True, chp=True, st=False, cc=False),
    "treatment": dict(track=True, ct=True, chp=True, st=True, cc=True),
}
OUTAGE_FILES = {
    "std (armed)": "campd-unit-outages-CAISO.csv",
    "short-gas": "campd-unit-outages-shortgas-CAISO.csv",
    "partial": "campd-partial-outages-CAISO.csv",
    "short-coal": "campd-unit-outages-short-CAISO.csv",
}


def _is_bin(fuel: str, hr: float) -> bool:
    """True when ``hr`` equals a ``HEAT_RATE_BINS[fuel]`` value."""
    return any(abs(hr - v) < 1e-9 for v in HEAT_RATE_BINS.get(fuel, {}).values())


def _null_plants(table: Path) -> set[int]:
    """Plant codes whose EIA-860 source rows carry no joined eGRID heat rate."""
    if not table.is_file():
        return set()
    df = pd.read_parquet(table)
    codes = ba_codes(ISO)
    if codes and "balancing_authority_code" in df.columns:
        df = df[df["balancing_authority_code"].astype(str).str.strip().isin(codes)]
    if "heat_rate" not in df.columns:
        return set(pd.to_numeric(df["plant_id"], errors="coerce").dropna().astype(int))
    hr = pd.to_numeric(df["heat_rate"], errors="coerce")
    return set(
        pd.to_numeric(df.loc[hr.isna() | (hr <= 0), "plant_id"], errors="coerce")
        .dropna()
        .astype(int)
    )


def fleet_census(posture: str, year: int) -> dict:
    """Heat-rate source attribution for one posture-year."""
    p = POSTURES[posture]
    vintage = resolve_backcast_eia860_vintage(None, year, p["track"])
    data_dir = set_eia860_vintage(vintage)
    flags = dict(
        measured_ct_heat_rates=p["ct"],
        measured_chp_heat_rates=p["chp"],
        measured_st_heat_rates=p["st"],
        measured_cc_heat_rates=p["cc"],
        egrid_family_heat_rates=True,
    )
    try:
        op = load_fleet_from_csv(ISO, year=year, **flags)
        ret = load_retired_within_window(ISO, year=year, **{
            k: v for k, v in flags.items() if k.startswith("measured_")})
        null = _null_plants(Path(data_dir) / "eia860_generators.parquet") | _null_plants(
            EIA_860_DIR / "eia860_generator_retired_within_window.parquet")
    finally:
        set_eia860_vintage(None)
    tot = cls = 0.0
    by_fuel: dict[str, float] = {}
    resid: dict[int, dict] = {}
    hr_mw: dict[str, list] = {}
    for g in op + ret:
        if g.fuel_type not in THERMAL:
            continue
        if int(g.online_year or 0) > year:
            continue
        if g.retirement_year is not None and int(g.retirement_year) < year:
            continue
        mw = float(g.pmax_mw)
        tot += mw
        by_fuel[g.fuel_type] = by_fuel.get(g.fuel_type, 0.0) + mw
        hr_mw.setdefault(g.fuel_type, []).append((float(g.heat_rate), mw))
        code = int(g.plant_code or 0)
        if code in null and _is_bin(g.fuel_type, float(g.heat_rate)):
            cls += mw
            r = resid.setdefault(code, {"plant_code": code, "name": g.name,
                                        "fuel": g.fuel_type, "mw": 0.0})
            r["mw"] += mw
    wavg = {f: round(sum(h * m for h, m in v) / sum(m for _, m in v), 3)
            for f, v in hr_mw.items() if sum(m for _, m in v) > 0}
    return {
        "eia860_source": Path(data_dir).name if Path(data_dir) != EIA_860_DIR else "canonical",
        "thermal_mw": round(tot, 1),
        "mw_by_fuel": {k: round(v, 1) for k, v in sorted(by_fuel.items())},
        "mw_weighted_hr_by_fuel": wavg,
        "class_table_mw": round(cls, 1),
        "class_table_share": round(cls / tot, 4) if tot else None,
        "class_table_plants": sorted(
            ({**r, "mw": round(r["mw"], 1)} for r in resid.values()),
            key=lambda r: -r["mw"]),
    }


def outage_census() -> dict:
    """Windows starting per year and MW-h overlapping each year, per family file."""
    out: dict = {}
    for fam, fn in OUTAGE_FILES.items():
        path = RAW_DATA_DIR / fn
        if not path.is_file():
            out[fam] = None
            continue
        df = pd.read_csv(path)
        if df.empty:
            out[fam] = {str(y): {"windows": 0, "mwh": 0.0} for y in YEARS}
            continue
        s = pd.to_datetime(df["outage_start"])
        e = pd.to_datetime(df["outage_end"])
        mwcol = next((c for c in ("unit_capacity_mw", "capacity_mw", "pmax_mw") if c in df.columns), None)
        mw = pd.to_numeric(df[mwcol], errors="coerce").fillna(0.0) if mwcol else 0.0
        if "derate_factor" in df.columns:
            mw = mw * (1 - pd.to_numeric(df["derate_factor"], errors="coerce").fillna(0.0))
        rec = {}
        for y in YEARS:
            y0, y1 = pd.Timestamp(f"{y}-01-01"), pd.Timestamp(f"{y + 1}-01-01")
            ov = ((e.clip(upper=y1) - s.clip(lower=y0)).dt.total_seconds() / 3600).clip(lower=0)
            rec[str(y)] = {"windows": int((s.dt.year == y).sum()),
                           "mwh": round(float((ov * mw).sum()), 0)}
        out[fam] = rec
    return out


def main() -> int:
    """Run the census and write its JSON."""
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rec = {"iso": ISO, "fleet": {}, "outages": outage_census()}
    for posture in POSTURES:
        rec["fleet"][posture] = {}
        for y in YEARS:
            r = fleet_census(posture, y)
            rec["fleet"][posture][str(y)] = r
            print(f"{posture:9s} {y} src={r['eia860_source']:12s} thermal={r['thermal_mw']:9.1f} "
                  f"class={r['class_table_mw']:7.1f} ({r['class_table_share']}) hr={r['mw_weighted_hr_by_fuel']}",
                  flush=True)
    Path(a.out).write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    for fam, v in rec["outages"].items():
        print(fam, v and {y: (c["windows"], c["mwh"]) for y, c in v.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
