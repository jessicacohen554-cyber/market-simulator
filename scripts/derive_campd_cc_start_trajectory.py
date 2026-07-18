"""Derive measured CC start-to-load durations from CAMPD gross load (caiso-96 WP-1).

Source basis for the RA must-offer bridge's STARTUP-TRAJECTORY extension
(``ScenarioConfig.caiso_ra_startup_trajectory`` →
``model.commitment.caiso_ra_mustoffer_min_gen(startup_lead_hours=…)``): the
measured hours a combined-cycle plant takes from first synchronization to full
load. The caiso-95 who-serves-the-day decomposition
(results/calibration/FINDING-caiso95-who-serves-the-day-2026-07-18.md §3) found
the model's evening CCs start ~3 h after the metered fleet: a real CC started
for the evening peak fires hours early (start-to-load trajectory + DAM
operating-day positioning), while the continuous-variable LP pays no startup
and materializes capacity exactly at the ramp hour. The bridge extension floors
the L pre-start hours of each detected run-start at the ramp-in trajectory;
this script derives L.

Per start EVENT (facility-level summed CC gross load, an off→on transition
after ≥ ``OFF_HOURS_MIN`` offline hours, reporting-gap-adjacent events
excluded): the 0-based hour index within the run at which gross load first
reaches ``FULL_LOAD_FRAC`` × the run's peak (peak taken within the first
``RUN_WINDOW_HOURS`` on-hours so late duct-firing/second-train staging cannot
inflate the ramp). Run-relative peak, not nameplate: a single-train evening
start of a two-train plant is a complete start event at its own committed
level.

Estimation gates — FROZEN before any solve (charter order, caiso-96 WP-1; the
values below were fixed from data volume/stability only, never a model
residual, and re-derive only when the CAMPD source updates — CLAUDE.md rule 23):

- A PLANT row (``basis == "plant"``) is accepted iff pooled events ≥
  ``MIN_EVENTS_PLANT``, robust dispersion IQR ≤ ``IQR_MAX_HOURS``, and
  leave-one-year-out stability holds: recomputing the p50 with each vintage
  (with ≥ ``MIN_EVENTS_LOYO_YEAR`` events) left out moves it by at most
  ``LOYO_MAX_DEV_HOURS``. Failing plants are written as ``basis == "sparse"``
  (informational; the loader ignores them → class fallback).
- The CLASS row (``plant_code == 0``, ``basis == "class"``) pools every event
  and requires ≥ ``MIN_EVENTS_CLASS`` events and the same LOYO gate; if it
  fails, no class row is written and the loader falls back to
  ``constants.CC_START_TO_LOAD_HOURS_DEFAULT`` (NREL/SR-5500-55433 hot/warm
  CC start-to-full-load).
- ``lead_hours`` = round(p50) clipped to [``LEAD_MIN_HOURS``,
  ``LEAD_MAX_HOURS``]: a lead below 1 h is sub-resolution, and a lead beyond
  6 h exceeds any credible same-operating-day DAM positioning window.

Governance (CLAUDE.md rules #13/#23): a measured physical-capability parameter
in the same admissibility class as the CAMPD ramp envelopes and min-stable
loads — it regenerates from the CAMPD pipeline for any vintage, responds to
fleet change (a repowered plant re-measures), and never reads a price or
volume residual. CT/steam classes are deliberately not derived: a fast-start
CT reaches load sub-hourly (CT_COMMITMENT_PARAMS min-run/min-down 1 h), so at
hourly LP resolution its lead is 0 by physics, and gas steamers are owned by
their own drag/startup mechanisms (one mechanism per phenomenon, rule 19).

Output: ``data/raw/_processed-legacy/campd_cc_start_trajectory_{ISO}.csv``,
consumed by :func:`market_sim.data.fleet.load_cc_start_trajectory`.

Usage::

    python scripts/derive_campd_cc_start_trajectory.py --iso CAISO
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data.campd import (  # noqa: E402
    CAMPD_UNIT_PLANT_REMAP,
    states_for_iso,
)
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

UNIT_LEVEL_DIR = RAW_DIR / "campd-unit-level"

# ---- FROZEN estimation gates (fixed before any solve; see module docstring) --
YEARS_DEFAULT = (2023, 2024, 2025)  # the training vintages (rule 22)
OFF_HOURS_MIN = 2  # h offline required before an on-transition counts as a start
RUN_WINDOW_HOURS = 12  # ramp measured within the run's first N on-hours
FULL_LOAD_FRAC = 0.90  # "at load" = ≥ this fraction of the run-window peak
MIN_EVENTS_PLANT = 100  # pooled starts required for a per-plant row
MIN_EVENTS_LOYO_YEAR = 20  # a vintage participates in LOYO only above this
LOYO_MAX_DEV_HOURS = 1.0  # max |p50_loyo − p50_pooled| tolerated
IQR_MAX_HOURS = 4.0  # robust dispersion gate on per-plant events
MIN_EVENTS_CLASS = 1000  # pooled starts required for the class row
LEAD_MIN_HOURS = 1  # sub-hourly leads are below LP resolution
LEAD_MAX_HOURS = 6  # bound: one same-day DAM positioning window


def _facility_hourly(iso: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Return facility-hour summed CC gross load for the ISO's CAMPD states.

    NaN gross load rows are offline hours (summed as 0 with presence kept);
    facility-hours with NO row at all are reporting gaps and stay absent, so
    the event scan can exclude gap-adjacent transitions.
    """
    fleet = load_fleet_from_csv(iso, get_iso_config(iso))
    fleet_plants = {int(g.plant_code) for g in fleet if g.plant_code}
    frames = []
    for state in states_for_iso(iso):
        for year in years:
            path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=[
                    "facilityId",
                    "unitId",
                    "date",
                    "hour",
                    "grossLoad",
                    "unitType",
                ],
            )
            df = df[df.unitType == "Combined cycle"]
            df["facilityId"] = pd.to_numeric(df.facilityId, errors="coerce")
            # CEMS-to-EIA split-plant remap (campd.CAMPD_UNIT_PLANT_REMAP):
            # repowered CCGTs filing under a legacy boiler ORIS move to the
            # EIA plant the model fleet knows them by (315/CT* -> 62115, ...).
            for (fac, unit), eia_plant in CAMPD_UNIT_PLANT_REMAP.items():
                mask = (df.facilityId == fac) & (df.unitId == unit)
                if mask.any():
                    df.loc[mask, "facilityId"] = eia_plant
            df = df[df.facilityId.isin(fleet_plants)]
            if not len(df):
                continue
            df["gl"] = df.grossLoad.fillna(0.0)
            fac = df.groupby(["facilityId", "date", "hour"], as_index=False).agg(
                gl=("gl", "sum")
            )
            fac["ts"] = fac.date + pd.to_timedelta(fac.hour, unit="h")
            fac["year"] = year
            frames.append(fac[["facilityId", "ts", "year", "gl"]])
    if not frames:
        raise SystemExit(f"no CAMPD unit-level CC data found for {iso} {years}")
    return pd.concat(frames, ignore_index=True)


def _scan_events(fac: pd.DataFrame) -> pd.DataFrame:
    """Return one row per start event: (plant_code, year, L) with L the 0-based
    hour-into-run at which gross load reaches FULL_LOAD_FRAC × run-window peak.

    Events whose pre-window or ramp window touches a reporting gap (a missing
    facility-hour) are dropped — a gap edge is not a start.
    """
    events: list[tuple[int, int, int]] = []
    for fid, g in fac.groupby("facilityId"):
        g = g.sort_values("ts")
        # Reindex to the facility's continuous hourly span; introduced NaNs
        # are true reporting gaps (offline hours arrived as gl == 0 above).
        full = pd.date_range(g.ts.iloc[0], g.ts.iloc[-1], freq="h")
        s = g.set_index("ts").reindex(full)
        gl = s.gl.to_numpy()
        yr = s.year.to_numpy()
        gap = np.isnan(gl)
        on = np.nan_to_num(gl, nan=0.0) > 0.0
        starts = np.flatnonzero(on[1:] & ~on[:-1]) + 1
        for st in starts:
            if st < OFF_HOURS_MIN or on[st - OFF_HOURS_MIN : st].any():
                continue
            # run window: first RUN_WINDOW_HOURS on-hours (or until off)
            e = st
            while e < len(gl) and on[e] and e - st < RUN_WINDOW_HOURS:
                e += 1
            if gap[max(0, st - OFF_HOURS_MIN) : e].any():
                continue  # gap-adjacent: not a trustworthy event
            run = gl[st:e]
            if len(run) < 2:
                continue
            peak = float(np.max(run))
            if peak <= 0.0:
                continue
            L = int(np.argmax(run >= FULL_LOAD_FRAC * peak))
            events.append((int(fid), int(yr[st]), L))
    return pd.DataFrame(events, columns=["plant_code", "year", "L"])


def _loyo_max_dev(ev: pd.DataFrame, pooled_p50: float) -> float:
    """Max deviation of the p50 when leaving out each qualifying vintage."""
    devs = [0.0]
    for year in sorted(ev.year.unique()):
        if int((ev.year == year).sum()) < MIN_EVENTS_LOYO_YEAR:
            continue
        rest = ev.loc[ev.year != year, "L"]
        if not len(rest):
            continue
        devs.append(abs(float(rest.median()) - pooled_p50))
    return max(devs)


def derive(iso: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Return the start-trajectory table (plant rows + class row)."""
    ev = _scan_events(_facility_hourly(iso, years))
    rows = []
    for pc, g in ev.groupby("plant_code"):
        p50 = float(g.L.median())
        iqr = float(g.L.quantile(0.75) - g.L.quantile(0.25))
        loyo = _loyo_max_dev(g, p50)
        ok = (
            len(g) >= MIN_EVENTS_PLANT
            and iqr <= IQR_MAX_HOURS
            and loyo <= LOYO_MAX_DEV_HOURS
        )
        rows.append(
            {
                "plant_code": int(pc),
                "basis": "plant" if ok else "sparse",
                "events": int(len(g)),
                "p50_hours": p50,
                "iqr_hours": iqr,
                "loyo_max_dev_hours": loyo,
                "lead_hours": int(np.clip(round(p50), LEAD_MIN_HOURS, LEAD_MAX_HOURS)),
            }
        )
    class_p50 = float(ev.L.median())
    class_loyo = _loyo_max_dev(ev, class_p50)
    if len(ev) >= MIN_EVENTS_CLASS and class_loyo <= LOYO_MAX_DEV_HOURS:
        rows.append(
            {
                "plant_code": 0,
                "basis": "class",
                "events": int(len(ev)),
                "p50_hours": class_p50,
                "iqr_hours": float(ev.L.quantile(0.75) - ev.L.quantile(0.25)),
                "loyo_max_dev_hours": class_loyo,
                "lead_hours": int(
                    np.clip(round(class_p50), LEAD_MIN_HOURS, LEAD_MAX_HOURS)
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(["basis", "events"], ascending=[True, False])


def main() -> None:
    """CLI entry point: derive and write the per-ISO artifact."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--iso", default="CAISO")
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS_DEFAULT))
    args = ap.parse_args()
    table = derive(args.iso, tuple(args.years))
    out = PROCESSED_DIR / f"campd_cc_start_trajectory_{args.iso.upper()}.csv"
    table.to_csv(out, index=False)
    n_plant = int((table.basis == "plant").sum())
    n_sparse = int((table.basis == "sparse").sum())
    cls = table[table.basis == "class"]
    print(f"wrote {out} — {n_plant} plant rows, {n_sparse} sparse (class-fallback)")
    if len(cls):
        print(
            f"class row: {int(cls.events.iloc[0])} events, "
            f"p50 {cls.p50_hours.iloc[0]:.1f} h, lead {int(cls.lead_hours.iloc[0])} h"
        )
    else:
        print("class row FAILED gates -> loader falls back to constants default")


if __name__ == "__main__":
    main()
