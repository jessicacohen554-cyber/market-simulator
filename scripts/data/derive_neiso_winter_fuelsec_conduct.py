"""Derive the winter fuel-security floor's measured CONDUCT per plant-year (neiso-119).

The NEISO winter fuel-security must-run (Component B,
``winter_fuel_inventory.apply_winter_fuelsec_mustrun``) postures the fuel-secure
steam fleet — the coal family and ST_GAS — at minimum-stable over each zone's
winter cold-day window. neiso-119 phase 0 measured that most of that fleet is
metered OFFLINE across those very hours (2019: Middletown 562 online 2 %,
Newington 8002 1 %, West Springfield 1642 1 %, Merrimack 2364 45 %;
``docs/handoffs/neiso119/phase0_fuelsec_<Y>.json``). This derive writes the
measurement the ``neiso_winter_fuelsec_conduct_roster`` gate reads
(``winter_fuel_inventory.winter_fuelsec_conduct_roster``, leave-one-year-out).

For every backcast year and every plant carrying a fuel-secure class in that
year's backcast fleet (``scripts.lib.heat_rate_years.backcast_fleets`` — the
year-matched EIA-860 vintage plus the retiree channel), it records:

* ``window_hours`` — hours in the plant's ZONE cold-day window, computed by the
  floor's own definition (``winter_fuel_inventory.winter_fuelsec_cold_window``,
  default -7 C / 48 h bridging / Nov-Mar), so the roster tests exactly the hours
  the floor can bind;
* ``online_hours`` — of those, the hours in which the plant's CEMS BOILER units
  (``derive_campd_gas_st_heat_rates._is_boiler``: CTs and CC blocks excluded) sum
  to a positive gross load (EPA CAMPD unit-level hourly, ``data/raw/campd-unit-level``).

Frozen against residuals (rule 23 [R-FROZEN-DERIVE]): it re-derives only when
CAMPD, the fleet vintages or the pinned zone temperatures change.

Output: ``data/raw/_processed-legacy/winter_fuelsec_conduct_NEISO.csv``.

Usage::

    uv run python scripts/data/derive_neiso_winter_fuelsec_conduct.py [--out PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR, RAW_DATA_DIR  # noqa: E402
from market_sim.config.plant_taxonomy import artifact_class  # noqa: E402
from market_sim.data.winter_fuel_inventory import (  # noqa: E402
    _WINTER_FUELSEC_CLASSES,
    winter_fuelsec_cold_window,
)
from scripts.data.derive_campd_gas_st_heat_rates import _is_boiler  # noqa: E402
from scripts.lib.heat_rate_years import backcast_fleets  # noqa: E402

ISO = "NEISO"
YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
#: ISO-NE footprint states (the CAMPD extracts are per state).
STATES: tuple[str, ...] = ("CT", "MA", "ME", "NH", "RI", "VT")
HOURS = 8760


def fuelsec_plants(fleet: list) -> dict[int, str]:
    """Return ``{plant_code: zone}`` for plants carrying a fuel-secure class."""
    out: dict[int, str] = {}
    for g in fleet:
        if artifact_class(g.plant_group) in _WINTER_FUELSEC_CLASSES:
            try:
                out[int(g.plant_code)] = str(g.zone)
            except (TypeError, ValueError):
                continue
    return out


def boiler_online(year: int) -> pd.Series:
    """Return a ``(facilityId, hour) -> online`` boolean series for CEMS boilers."""
    frames = []
    for st in STATES:
        p = RAW_DATA_DIR / "campd-unit-level" / f"{st}_{year}.parquet"
        if p.exists():
            frames.append(
                pd.read_parquet(
                    p, columns=["facilityId", "date", "hour", "grossLoad", "unitType"]
                )
            )
    df = pd.concat(frames, ignore_index=True)
    df = df[_is_boiler(df["unitType"])]
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    t = (pd.to_datetime(df["date"]) - pd.Timestamp(f"{year}-01-01")).dt.days * 24 + df[
        "hour"
    ]
    df = df.assign(t=t.astype(int), facilityId=df["facilityId"].astype(int))
    df = df[(df["t"] >= 0) & (df["t"] < HOURS)]
    load = df.groupby(["facilityId", "t"])["grossLoad"].sum(min_count=1)
    return load.fillna(0.0) > 0.0


def derive() -> pd.DataFrame:
    """Build the per plant-year conduct table (see module docstring)."""
    fleets = backcast_fleets(ISO, YEARS)
    rows = []
    for y in YEARS:
        plants = fuelsec_plants(fleets[y])
        online = boiler_online(y)
        windows: dict[str, np.ndarray | None] = {}
        for code, zone in sorted(plants.items()):
            if zone not in windows:
                windows[zone] = winter_fuelsec_cold_window(ISO, y, zone, HOURS)
            w = windows[zone]
            n_win = int(w.sum()) if w is not None else 0
            on = np.zeros(HOURS, dtype=bool)
            if code in online.index.get_level_values(0):
                s = online.loc[code]
                on[s.index.to_numpy()] = s.to_numpy()
            n_on = int((on & w).sum()) if w is not None else 0
            rows.append(
                {
                    "plant_code": code,
                    "year": y,
                    "zone": zone,
                    "window_hours": n_win,
                    "online_hours": n_on,
                    "online_share": round(n_on / n_win, 4) if n_win else None,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None, help="Output CSV path override")
    args = ap.parse_args()
    out = (
        Path(args.out)
        if args.out
        else PROCESSED_DIR / f"winter_fuelsec_conduct_{ISO}.csv"
    )
    df = derive()
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} plant-year rows)")
    print(df[df["window_hours"] > 0].to_string(index=False))


if __name__ == "__main__":
    main()
