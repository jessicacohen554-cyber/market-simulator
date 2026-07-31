"""ERCOT-148 Phase 0 (no LP): coal outage-window reconciliation, 10 plants x 2023-2025.

Owner directive 2026-07-31: the keeper (2026-07-31-ercot145-gas-daily-shape)
runs coal plants through months-long CAMPD zero-op windows (Coleto Creek
+31.4%/2023, +32.4%/2024; Limestone +40.3%/2024; Sandy Creek is the captured
control). This probe reconciles, for ALL 10 model coal plants and every unit,
the three measured layers that decide the keeper's coal availability:

  1. CAMPD unit-grain zero-op spells (gross == 0, zero-filled hourly grid, the
     derive script's own clock convention) of >= UNIT_OUTAGE_MIN_DAYS days —
     the physical record of the committed intake
     (``data/raw/campd-unit-level/TX_{year}.parquet``).
  2. The >= 5-day windows in ``data/raw/campd-unit-outages.csv`` exactly as the
     keeper's loader consumes them (``outages.unit_outage_derate_factors``:
     ``duration_days >= 5``, day-granular ``[start, end+1d)`` masks on the
     model clock).
  3. The 60-Day DAM COP disclosure site-hour live/rating fraction
     (``ercot-thermal-dam-availability-site-hourly.parquet`` through the
     accepted ``ercot-dam-plant-crosswalk.csv`` rows) — the layer the keeper's
     ``ercot_thermal_dam_availability_plant`` pin applies ON TOP of layer 2
     (bidirectional water-fill: where the site series is finite it OVERRIDES
     the window; where NaN the window stands).

For every zero-op spell it reports: window coverage (share of spell hours
inside a layer-2 mask), DAM row coverage and the cap-weighted mean DAM
fraction over the spell (layer 3), and the TWh at stake (unit MW x spell
hours). The Sandy-Creek-vs-Coleto/Limestone difference is adjudicated from
the same table. Pure data reconciliation: no LP, no dispatch, no scoring.

Usage:
    python scripts/probes/ercot148_coal_outage_phase0.py \
        [--years 2023 2024 2025] [--json-out results/calibration/...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import RAW_DATA_DIR, REFERENCE_DIR  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
)

# The 10 ERCOT model coal plants (custom-bin-assignments.csv Plant_Group=COAL).
COAL_PLANTS: dict[int, str] = {
    3470: "W A Parish [COAL]",
    6180: "Oak Grove (TX)",
    7030: "Major Oak Power",
    298: "Limestone",
    6146: "Martin Lake",
    6178: "Coleto Creek",
    6183: "San Miguel",
    6179: "Fayette Power Project",
    7097: "J K Spruce",
    56611: "Sandy Creek Energy Station",
}
# W A Parish coal units (the rest are gas steam, split code 34702 — not coal).
WAP_COAL_UNITS = {"WAP5", "WAP6", "WAP7", "WAP8"}

# CAMPD unit id -> DAM COP site(s), from the accepted crosswalk rows (jointly
# owned plants split one physical unit across J0x share sites — sum them).
UNIT_TO_SITES: dict[tuple[int, str], list[str]] = {
    (298, "LIM1"): ["LEG_LEG_G1"],
    (298, "LIM2"): ["LEG_LEG_G2"],
    (6146, "1"): ["MLSES_UNIT1"],
    (6146, "2"): ["MLSES_UNIT2"],
    (6146, "3"): ["MLSES_UNIT3"],
    (3470, "WAP5"): ["WAP_WAP_G5"],
    (3470, "WAP6"): ["WAP_WAP_G6"],
    (3470, "WAP7"): ["WAP_WAP_G7"],
    (3470, "WAP8"): ["WAP_WAP_G8"],
    (6180, "1"): ["OGSES_UNIT1A"],
    (6180, "2"): ["OGSES_UNIT2"],
    (7097, "**1"): ["CALAVERS_JKS1"],
    (7097, "**2"): ["CALAVERS_JKS2"],
    (6178, "1"): ["COLETO_COLETOG1"],
    (56611, "S01"): [
        "SCES_UNIT1_J01",
        "SCES_UNIT1_J02",
        "SCES_UNIT1_J03",
        "SCES_UNIT1_J04",
    ],
    (6183, "SM-1"): ["SANMIGL_G1"],
    (7030, "U1"): ["TNP_ONE_TNP_O_1"],
    (7030, "U2"): ["TNP_ONE_TNP_O_2"],
    (6179, "1"): ["FPPYD1_FPP_G1_J01", "FPPYD1_FPP_G1_J02"],
    (6179, "2"): ["FPPYD1_FPP_G2_J01", "FPPYD1_FPP_G2_J02"],
    (6179, "3"): ["FPPYD2_FPP_G3"],
}


def _unit_year_grid(sub: pd.DataFrame, year: int) -> np.ndarray:
    """One unit-year's hourly gross on the calendar-year clock (zero-filled).

    Mirrors ``derive_campd_unit_outages._unit_year_grid``: CAMPD omits
    non-operating hours, so missing hours are zero-filled (offline). The years
    audited here (2023-2025) are fully published, so no horizon clip.
    """
    ts = sub["date"] + pd.to_timedelta(sub["hour"], unit="h")
    series = pd.Series(sub["grossLoad"].to_numpy(dtype=float), index=ts)
    series = series.groupby(level=0).sum().sort_index()
    full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    return series.reindex(full).fillna(0.0).to_numpy(dtype=float)


def _zero_spells(gross: np.ndarray, min_hours: int) -> list[tuple[int, int]]:
    """Maximal runs of gross == 0 lasting >= min_hours, as [(s, e_excl), ...]."""
    down = ~(np.nan_to_num(gross) > 0.0)
    if not down.any():
        return []
    d = np.diff(down.astype(np.int8), prepend=0, append=0)
    starts = np.flatnonzero(d == 1)
    ends = np.flatnonzero(d == -1)
    return [(int(s), int(e)) for s, e in zip(starts, ends) if e - s >= min_hours]


def _window_mask(rows: pd.DataFrame, year: int, n: int) -> np.ndarray:
    """Layer-2 mask: the loader's day-granular [start, end+1d) windows, >= 5d."""
    mask = np.zeros(n, dtype=bool)
    base = pd.Timestamp(f"{year}-01-01")
    for r in rows.itertuples(index=False):
        start = pd.Timestamp(r.outage_start)
        stop = pd.Timestamp(r.outage_end) + pd.Timedelta(days=1)
        lo = max(0, int((start - base).total_seconds() // 3600))
        hi = min(n, int((stop - base).total_seconds() // 3600))
        if hi > lo:
            mask[lo:hi] = True
    return mask


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    win = pd.read_csv(
        RAW_DATA_DIR / "campd-unit-outages.csv",
        parse_dates=["outage_start", "outage_end"],
    )
    win = win[win["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]

    sh = pd.read_parquet(RAW_DATA_DIR / "ercot-thermal-dam-availability-site-hourly.parquet")
    sh["date"] = pd.to_datetime(sh["date"])
    xw = pd.read_csv(REFERENCE_DIR / "ercot-dam-plant-crosswalk.csv")
    xw = xw[xw["accepted"] == 1]

    spells_out: list[dict] = []
    plant_year: list[dict] = []

    for year in args.years:
        tx = pd.read_parquet(
            RAW_DATA_DIR / "campd-unit-level" / f"TX_{year}.parquet",
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "grossLoad",
                "primaryFuelInfo",
            ],
        )
        tx["facilityId"] = pd.to_numeric(tx["facilityId"], errors="coerce")
        tx = tx.dropna(subset=["facilityId"])
        tx["facilityId"] = tx["facilityId"].astype(int)
        tx = tx[tx["facilityId"].isin(COAL_PLANTS)]
        tx["date"] = pd.to_datetime(tx["date"])
        tx["hour"] = pd.to_numeric(tx["hour"], errors="coerce")
        tx = tx.dropna(subset=["hour"])
        tx["grossLoad"] = pd.to_numeric(tx["grossLoad"], errors="coerce")

        n = len(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))
        clock = pd.date_range(f"{year}-01-01", periods=n, freq="h")
        shy = sh[sh["date"].dt.year == year]

        for fac_id, fac in tx.groupby("facilityId"):
            for uid, u in fac.groupby("unitId"):
                fuel = str(u["primaryFuelInfo"].iloc[0]).strip().lower()
                is_coal = fuel in ("coal", "coal refuse")
                if int(fac_id) == 3470 and str(uid) not in WAP_COAL_UNITS:
                    continue  # gas-steam split units — not the coal bin
                if not is_coal:
                    continue
                gross = _unit_year_grid(u, year)
                peak = float(gross.max())
                if peak <= 0.0:
                    # whole-year silent unit: report as one full-year spell
                    spells = [(0, n)]
                else:
                    spells = _zero_spells(gross, UNIT_OUTAGE_MIN_DAYS * 24)
                wrows = win[
                    (win["facility_id"] == int(fac_id))
                    & (win["unit_id"].astype(str) == str(uid))
                    & (win["outage_end"] >= f"{year}-01-01")
                    & (win["outage_start"] <= f"{year}-12-31")
                ]
                wmask = _window_mask(wrows, year, n)
                ucap = float(
                    wrows["unit_capacity_mw"].iloc[0]
                    if len(wrows)
                    else win[
                        (win["facility_id"] == int(fac_id))
                        & (win["unit_id"].astype(str) == str(uid))
                    ]["unit_capacity_mw"].max()
                )
                if not np.isfinite(ucap):
                    ucap = peak

                # DAM site-hour fraction for this unit's mapped sites.
                sites = UNIT_TO_SITES.get((int(fac_id), str(uid)), [])
                frac = np.full(n, np.nan)
                if sites:
                    ss = shy[shy["site"].isin(sites)]
                    if len(ss):
                        agg = ss.groupby(["date", "he"], as_index=False)[
                            ["live_mw", "rating_mw"]
                        ].sum()
                        ts = agg["date"] + pd.to_timedelta(
                            agg["he"].astype(int) - 1, unit="h"
                        )
                        f = np.where(
                            agg["rating_mw"] > 0,
                            np.clip(agg["live_mw"] / agg["rating_mw"], 0, 1),
                            np.nan,
                        )
                        fs = pd.Series(f, index=ts).groupby(level=0).mean()
                        frac = fs.reindex(clock).to_numpy(dtype=float)

                zero_hours_total = int(sum(e - s for s, e in spells))
                for s, e in spells:
                    cov = float(wmask[s:e].mean()) if e > s else 0.0
                    fspan = frac[s:e]
                    fin = np.isfinite(fspan)
                    dam_cov = float(fin.mean())
                    dam_mean = float(np.nanmean(fspan)) if fin.any() else float("nan")
                    uncovered_h = int((~wmask[s:e]).sum())
                    spells_out.append(
                        {
                            "year": year,
                            "plant": COAL_PLANTS[int(fac_id)],
                            "facility_id": int(fac_id),
                            "unit_id": str(uid),
                            "unit_mw": round(ucap, 1),
                            "start": str(clock[s].date()),
                            "end": str(clock[e - 1].date()),
                            "days": round((e - s) / 24.0, 1),
                            "window_cov": round(cov, 3),
                            "uncovered_days": round(uncovered_h / 24.0, 1),
                            "twh_uncovered": round(uncovered_h * ucap / 1e6, 3),
                            "dam_row_cov": round(dam_cov, 3),
                            "dam_mean_frac": (
                                round(dam_mean, 3) if np.isfinite(dam_mean) else None
                            ),
                            "twh_spell": round((e - s) * ucap / 1e6, 3),
                        }
                    )
                plant_year.append(
                    {
                        "year": year,
                        "plant": COAL_PLANTS[int(fac_id)],
                        "facility_id": int(fac_id),
                        "unit_id": str(uid),
                        "unit_mw": round(ucap, 1),
                        "campd_twh": round(float(gross.sum()) / 1e6, 3),
                        "zero_days_ge5": round(zero_hours_total / 24.0, 1),
                        "windowed_days": round(float(wmask.sum()) / 24.0, 1),
                        "dam_mean_frac_year": (
                            round(float(np.nanmean(frac)), 3)
                            if np.isfinite(frac).any()
                            else None
                        ),
                    }
                )

    sp = pd.DataFrame(spells_out).sort_values(["facility_id", "unit_id", "year", "start"])
    py = pd.DataFrame(plant_year).sort_values(["facility_id", "unit_id", "year"])

    pd.set_option("display.width", 200)
    print("\n=== ERCOT-148 Phase 0: unit zero-op spells (gross==0, >= 5d) vs "
          "windows CSV vs DAM COP pin ===\n")
    print(sp.to_string(index=False))
    print("\n=== per unit-year summary ===\n")
    print(py.to_string(index=False))

    # Headline: spells materially uncovered by the windows CSV, and spells
    # covered by windows but ERASED by a finite high DAM fraction (the pin).
    sp_missing = sp[(sp["window_cov"] < 0.95) & (sp["days"] >= 5)]
    print("\n=== spells NOT fully covered by the >= 5-day windows CSV ===\n")
    print(
        sp_missing.to_string(index=False)
        if len(sp_missing)
        else "(none — every >= 5-day zero-op spell is windowed)"
    )
    sp_erased = sp[
        (sp["window_cov"] >= 0.5)
        & (sp["dam_row_cov"] > 0.5)
        & (sp["dam_mean_frac"].fillna(0) > 0.5)
    ]
    print(
        "\n=== spells windowed in the CSV but with a FINITE HIGH DAM fraction "
        "(pin would restore availability over the window) ===\n"
    )
    print(
        sp_erased.to_string(index=False)
        if len(sp_erased)
        else "(none)"
    )

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "spells": sp.to_dict(orient="records"),
                    "unit_years": py.to_dict(orient="records"),
                },
                indent=1,
            )
        )
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
