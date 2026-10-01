"""NYISO-NEXT-28 phase 0 (zero LP): Ravenswood 2500 steam over-dispatch, 2023.

Reads the keeper's per-year leg bundles (``unit_hourly_<year>.parquet`` from the
``claude/nyisonext21-<year>`` leg branches, extracted under ``--legs``), CAMPD
unit-level hourly for facility 2500, the committed ``-perunitmerithour-``
outage / layup extract pair, NYISO DA zonal LBMP for 2023, and the merit-order
guard's own panel (``scripts/lib/outage_detect.build_merit_order_panel``).
Writes ``results/phase0/nyiso/_nyisonext28_ravenswood_phase0.json``.

Questions answered: by year, Ravenswood steam model vs CAMPD energy and model
availability; for 2023, the split by month, by LP state (reduced cost) and by
spread to Zone J; the guard's per-window out-of-merit share for unit 30 in
every year; and whether the units' measured conduct is price-responsive.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data import campd  # noqa: E402
from scripts.lib import outage_detect as od  # noqa: E402

PLANT = 2500
FAC = "2500"  # CAMPD facilityId is a STRING
ST_UNITS = ["10", "20", "30"]
YEARS = [2022, 2023, 2024, 2025]
OUTAGES = ROOT / "data/raw/campd-unit-outages-perunitmerithour-NYISO.csv"
LAYUPS = ROOT / "data/raw/campd-unit-outages-layup-perunitmerithour-NYISO.csv"
OUT = ROOT / "results/phase0/nyiso/_nyisonext28_ravenswood_phase0.json"


def load_unit_hourly(legs: Path, year: int) -> pd.DataFrame:
    """Return the keeper leg's P1 unit_hourly rows for Ravenswood steam."""
    path = legs / f"nyisonext21_{year}/hourly/unit_hourly_{year}.parquet"
    u = pd.read_parquet(path)
    return u[(u.plant_code == PLANT) & (u.plant_group == "ST_GAS")].copy()


def load_campd(year: int) -> pd.DataFrame:
    """Return CAMPD hourly rows for Ravenswood's three boilers, with a timestamp."""
    c = pd.read_parquet(ROOT / f"data/raw/campd-unit-level/NY_{year}.parquet")
    c = c[(c.facilityId == FAC) & c.unitId.isin(ST_UNITS)].copy()
    c["ts"] = c.date + pd.to_timedelta(c.hour, "h")
    return c


def load_da_zone_j(year: int) -> pd.Series:
    """Return hourly DA LBMP for N.Y.C. from the staged monthly archives."""
    frames = []
    for z in sorted(
        glob.glob(str(ROOT / f"data/raw/lmp-data/NYISO/{year}*damlbmp_zone_csv.zip"))
    ):
        with zipfile.ZipFile(z) as zf:
            frames += [pd.read_csv(zf.open(n)) for n in zf.namelist()]
    d = pd.concat(frames)
    d.columns = [c.strip() for c in d.columns]
    d["ts"] = pd.to_datetime(d["Time Stamp"])
    return d[d.Name == "N.Y.C."].groupby("ts")["LBMP ($/MWHr)"].mean()


def window_hours(row: pd.Series, t0: pd.Timestamp) -> tuple[int, int]:
    """Return the [start, stop) hour index of an extract window from Jan 1."""
    s = int((pd.Timestamp(row.outage_start) - t0) / pd.Timedelta("1h")) + int(
        row.outage_start_hour
    )
    e = (
        int((pd.Timestamp(row.outage_end) - t0) / pd.Timedelta("1h"))
        + int(row.outage_end_hour)
        + 1
    )
    return s, e


def main() -> None:
    """Compute the phase-0 measurements and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--legs",
        type=Path,
        required=True,
        help="dir holding nyisonext21_<year>/hourly/unit_hourly_<year>.parquet",
    )
    args = ap.parse_args()
    rec: dict = {"plant": PLANT, "keeper": "2026-10-01-nyisonext21-astoria-hr-span"}

    # 1. By year: energy and availability.
    by_year = {}
    for y in YEARS:
        r = load_unit_hourly(args.legs, y)
        h = r.groupby("hour").agg(mw=("mw", "sum"), cap=("cap_mw", "sum"))
        c = load_campd(y)
        by_year[y] = {
            "model_twh": round(float(h.mw.sum()) / 1e6, 3),
            "campd_gross_twh": round(c.grossLoad.sum() / 1e6, 3),
            "model_avail_mean_mw": round(float(h.cap.mean()), 0),
            "model_hours_avail_gt_500mw": int((h.cap > 500).sum()),
            "campd_unit30_on_hours": int((c[c.unitId == "30"].grossLoad > 1).sum()),
        }
    rec["by_year"] = by_year

    # 2. 2023: the split of the excess.
    y = 2023
    ts = pd.date_range(f"{y}-01-01", periods=8760, freq="h")
    r = load_unit_hourly(args.legs, y)
    r["lmp"] = r.mc - r.red_cost
    run = r[r.mw > 0.5]
    state = np.select(
        [run.red_cost > 0.01, run.red_cost < -0.01],
        ["floor", "inframarginal"],
        "marginal",
    )
    rec["2023_energy_by_lp_state_gwh"] = (
        (run.groupby(state).mw.sum() / 1e3).round(0).to_dict()
    )
    econ = r[r.unit_id.str.endswith("econlo")].set_index("hour").sort_index()
    model = r.groupby("hour").mw.sum().reindex(range(8760)).fillna(0).values
    c = load_campd(y)
    meas = c.groupby("ts").grossLoad.sum().reindex(ts).fillna(0).values
    df = pd.DataFrame(
        {
            "model": model,
            "campd": meas,
            "offer": econ.mc.values,
            "lmp_model": econ.lmp.values,
        },
        index=ts,
    )
    df["da_j"] = load_da_zone_j(y).reindex(ts).ffill().values
    m = df.groupby(df.index.month)
    rec["2023_by_month"] = (
        pd.DataFrame(
            {
                "model_gwh": m.model.sum() / 1e3,
                "campd_gwh": m.campd.sum() / 1e3,
                "offer_mean": m.offer.mean(),
                "j_model_mean": m.lmp_model.mean(),
                "j_da_mean": m.da_j.mean(),
            }
        )
        .round(1)
        .to_dict(orient="index")
    )
    on_m, on_c = df.model > 1, df.campd > 1
    rec["2023_mw_when_on_p50"] = {
        "model": round(float(df.model[on_m].median()), 0),
        "campd": round(float(df.campd[on_c].median()), 0),
    }
    rec["2023_hours_in_merit"] = {
        "model_j_vs_offer": int((df.lmp_model > df.offer + 0.01).sum()),
        "da_j_vs_offer": int((df.da_j > df.offer).sum()),
    }

    # 3. Is measured conduct price-responsive? (spread = DA J - model offer)
    spr = df.da_j - df.offer
    resp = {}
    for uid in ST_UNITS:
        on = c[c.unitId == uid].set_index("ts").grossLoad.reindex(ts).fillna(0) > 1
        resp[uid] = {
            "hours_on": int(on.sum()),
            "spread_mean_on": round(float(spr[on].mean()), 2),
            "spread_mean_off": round(float(spr[~on].mean()), 2),
            "p_on_spread_gt5": round(float(on[spr > 5].mean()), 3),
            "p_on_spread_lt0": round(float(on[spr < 0].mean()), 3),
        }
    rec["2023_conduct_vs_spread"] = resp

    # 4. The guard: per-window out-of-merit share for unit 30, every year.
    outs = pd.read_csv(OUTAGES, dtype={"facility_id": str, "unit_id": str})
    lays = pd.read_csv(LAYUPS, dtype={"facility_id": str, "unit_id": str})
    states = campd.merit_panel_states_for_iso("NYISO")
    guard = {
        "MERIT_OOM_FRAC": od.MERIT_OOM_FRAC,
        "MERIT_RCC_PCTL": od.MERIT_RCC_PCTL,
        "panel_states": list(states),
        "years": {},
    }
    for y in YEARS:
        n = len(pd.date_range(f"{y}-01-01", f"{y}-12-31 23:00", freq="h"))
        p = od.build_merit_order_panel("NYISO", y, n, states, od.MERIT_RCC_PCTL)
        t0 = pd.Timestamp(f"{y}-01-01")
        srmc = p.srmc.get((PLANT, "30"))
        rows = []
        for kind, src in (("outage", outs), ("layup", lays)):
            w = src[
                (src.facility_id == FAC)
                & (src.unit_id == "30")
                & (src.outage_start.str[:4] == str(y))
            ]
            for _, x in w.iterrows():
                s, e = window_hours(x, t0)
                sh = p.out_of_merit_share((PLANT, "30"), s, e)
                rows.append(
                    {
                        "kind": kind,
                        "start": x.outage_start,
                        "end": x.outage_end,
                        "oom_share": None if sh is None else round(sh, 3),
                    }
                )
        guard["years"][y] = {
            "unit30_srmc_p50": round(float(np.nanmedian(srmc)), 1),
            "rcc_p50": round(float(np.nanmedian(p.rcc)), 1),
            "windows": rows,
        }
    rec["guard_unit30"] = guard

    OUT.write_text(json.dumps(rec, indent=1, default=str) + "\n")
    print(
        json.dumps(
            {
                k: rec[k]
                for k in (
                    "by_year",
                    "2023_energy_by_lp_state_gwh",
                    "2023_mw_when_on_p50",
                    "2023_hours_in_merit",
                )
            },
            indent=1,
            default=str,
        )
    )


if __name__ == "__main__":
    main()
