#!/usr/bin/env python
"""Derive-and-adjudicate the CAISO local-commitment response curve (caiso-81).

The approved design (``docs/handoffs/caiso-local-commitment-driver-design-
2026-07.md``, owner-approved 2026-07-13) floors the named LCR-area CT_PEAKER
units in the HE15-23 window at a *measured response curve*
``share_committed(ramp decile, season)`` estimated from CAMPD 2023-2025
unit-hours conditioned on the pocket's evening net-load ramp. Its §4
pre-commitments make the curve NOT LOYO-exempt: it is fitted (pooled
2023-2025), so it must survive leave-one-year-out before any promotion.

This script builds the estimation panel from committed data only and scores
that LOYO gate AT THE ESTIMATION STAGE — before any LP solve — exactly the
short-circuit the NYISO ST_GAS net-load-drag rejection established
(``scripts/derive_nyiso_st_gas_netload_drag.py``; cited in the
``D4_WINDOWS`` (MECH_RELIABILITY_FLOOR, "ST_GAS") row): a floor whose own
measured level is not year-stable at equal driver fails rule 12/13 by
construction, whatever it would do to the residual, and no dispatch solve
can rescue it (the LP only dispatches *above* the floor; the floor itself is
what mispredicts the held-out year).

VERDICT (2026-07-13, data through the committed 2025 CAMPD vintage):
**REFUTED — every candidate driver fails estimation-stage LOYO on 2025.**
The filed driver (pocket evening net-load ramp x season) overpredicts
held-out 2025 pocket committed energy by +376 % to +3,600 % across the three
pockets, and the two storage-conditioned rescue variants (ramp minus / ramp
over the pocket zone's measured battery power) fail the same way. The
2024->2025 signature is a regime break, not a condition response: the driver
moves ~-10 % while measured commitment moves ~-80 % (steepest-ramp-decile
days committed: Greater Bay 81/68/27 %, LA Basin 97/92/59 %, SDGE
68/62/11 % across 2023/24/25) — coincident with the pocket battery build
(LA_BASIN 1.2->2.9 GW, SDGE 0.8->1.8 GW, system 9.6->17.5 GW) and CAISO's
2025 slice-of-day RA reform. See
``results/calibration/FINDING-caiso81-local-commitment-driver-refuted-
2026-07-13.md``.

Accordingly this script WRITES NO ARTIFACT and no ``ScenarioConfig`` field,
injector, or ``D4_WINDOWS`` row exists for the mechanism (CLAUDE.md rule 26:
a refuted curve must not persist as a re-armable answer key). Re-run it when
a new measured source lands that can carry the regime term — a per-year
local-commitment volume series (DMM annual-report exceptional-dispatch /
minimum-online-commitment MWh by local area) or an RA-framework regime field
— and the LOYO table below re-adjudicates from source.

Inputs (all committed):
- ``data/raw/reference/lcr_area_membership_CAISO.csv`` (pocket membership)
- ``data/raw/campd-unit-level/CA_<year>.parquet`` (CEMS unit-hours, routed to
  model classes via the canonical EIA-923 dominant-class map)
- ``data/raw/reference/caiso-supply-consistent-demand/`` (the caiso-80
  owner-signed honest demand basis — the same series the LP dispatches)
- model loaders for zonal VRE potential (``load_renewable_profiles``, the
  exact upper bound the keeper's LP sees: under
  ``caiso_solar_endogenous_spill`` the solar CF passes to the LP underated)
  and the measured battery fleet (``load_eia860_storage``).

Usage: python scripts/derive_caiso_local_commitment.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP  # noqa: E402
from market_sim.data.fleet import eia923_dominant_class_by_plant  # noqa: E402
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.storage import load_eia860_storage  # noqa: E402

HOURS = 8760

# The design doc's pockets (§3) and their model zones. Greater Bay sits
# INSIDE NP15 (plant-scoped floor, no zone split); LA Basin and San
# Diego/Imperial Valley ARE their model zones (SP15 local-area split,
# 2026-07-09), so "pocket load share x zone net load" reduces to the zone
# net load (and for GB the share is a constant that cannot change decile
# assignment, so it drops out of a decile-binned curve).
POCKET_ZONE: dict[str, str] = {
    "Greater Bay": "NP15",
    "LA Basin": "LA_BASIN",
    "San Diego/Imperial Valley": "SDGE",
}

# Design-doc windows, model local-standard hour-beginning convention:
# commitment window HE15-23 -> [14, 23); evening ramp HE18-21 -> [17, 21);
# midday trough HE10-16 -> [9, 16).
COMMIT_WINDOW: tuple[int, int] = (14, 23)
EVENING_WINDOW: tuple[int, int] = (17, 21)
TROUGH_WINDOW: tuple[int, int] = (9, 16)

N_BINS = 10  # driver deciles (design doc §2: "share_committed(ramp decile, season)")

_MEMBERSHIP = RAW_DIR / "reference" / "lcr_area_membership_CAISO.csv"
_HONEST_DEMAND_DIR = RAW_DIR / "reference" / "caiso-supply-consistent-demand"
_CAMPD_DIR = RAW_DIR / "campd-unit-level"

# Cumulative hours at the start of each month (non-leap), for the
# date+hour -> hour-of-year mapping (same as derive_caiso_ct_reliability_floor).
_MONTH_START_HOUR = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]
_SEASON_BY_MONTH = [
    "DJF",
    "DJF",
    "MAM",
    "MAM",
    "MAM",
    "JJA",
    "JJA",
    "JJA",
    "SON",
    "SON",
    "SON",
    "DJF",
]


def _hoy_from_date_hour(date: pd.Series, hour: pd.Series) -> np.ndarray:
    """(date, 0-based local hour) -> non-leap hour-of-year (Feb 29 -> -1)."""
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    idx = np.array(_MONTH_START_HOUR)[m - 1] + (d - 1) * 24 + h
    return np.where((m == 2) & (d == 29), -1, idx)


def pocket_ct_mw(year: int, plants: set[int]) -> np.ndarray:
    """Measured pocket CT_PEAKER MW per hour (8760) from CAMPD CEMS.

    Units are routed to model classes via the canonical EIA-923
    dominant-class map (after the unit->plant remap), and only CT_PEAKER
    units belonging to *plants* are summed — the same class assignment the
    dispatch fleet and the shape-probe gates use.
    """
    dom = eia923_dominant_class_by_plant(year)
    raw = pd.read_parquet(
        _CAMPD_DIR / f"CA_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad"],
    ).dropna(subset=["grossLoad"])
    raw["fac"] = pd.to_numeric(raw["facilityId"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["fac"])
    eff = np.array(
        [
            CAMPD_UNIT_PLANT_REMAP.get((int(f), str(u)), int(f))
            for f, u in zip(raw["fac"], raw["unitId"])
        ]
    )
    keep = np.array([dom.get(p) == "CT_PEAKER" and p in plants for p in eff])
    raw = raw[keep]
    hoy = _hoy_from_date_hour(pd.to_datetime(raw["date"]), raw["hour"].astype(int))
    ok = (hoy >= 0) & (hoy < HOURS)
    raw = raw[ok].copy()
    raw["hoy"] = hoy[ok]
    return (
        raw.groupby("hoy")["grossLoad"]
        .sum()
        .reindex(range(HOURS), fill_value=0.0)
        .to_numpy()
    )


def zone_net_load(year: int, zone: str) -> np.ndarray:
    """The pocket zone's hourly net load on the model's own input basis.

    ``load_share x honest system demand − zone wind potential − zone solar
    potential`` — the same zonal demand construction the LP dispatches
    (``caiso_supply_consistent_demand``, the owner-signed caiso-80 basis) and
    the same VRE upper bound it sees (under the keeper's
    ``caiso_solar_endogenous_spill`` the solar CF reaches the LP underated),
    so the estimation driver and any runtime driver would be the one series.
    """
    ic = get_iso_config("CAISO")
    cfg = ScenarioConfig(iso="CAISO", mode="backcast", weather_year=year)
    znames = [z.name for z in ic.zones]
    zi = znames.index(zone)
    share = ic.zones[zi].load_share
    dem = pd.read_csv(
        _HONEST_DEMAND_DIR / f"caiso_supply_consistent_demand_{year}.csv"
    )["demand_mw"].to_numpy()[:HOURS]
    w_cf, w_cap, s_cf, s_cap = load_renewable_profiles("CAISO", year, ic, cfg)
    return dem * share - w_cf[zi] * w_cap[zi] - s_cf[zi] * s_cap[zi]


def zone_battery_mw(year: int, zone: str) -> float:
    """Measured battery power capacity (MW) in the pocket's zone (EIA-860)."""
    cfg = ScenarioConfig(iso="CAISO", mode="backcast", weather_year=year)
    units = load_eia860_storage("CAISO", year, cfg)
    return float(sum(u.power_cap_mw for u in units if u.zone == zone))


def build_panel(years: tuple[int, ...]) -> pd.DataFrame:
    """One row per (pocket, day): season, driver candidates, committed MW."""
    mem = pd.read_csv(_MEMBERSHIP)
    hod = np.arange(HOURS) % 24
    w_commit = (hod >= COMMIT_WINDOW[0]) & (hod < COMMIT_WINDOW[1])
    w_eve = (hod >= EVENING_WINDOW[0]) & (hod < EVENING_WINDOW[1])
    w_trough = (hod >= TROUGH_WINDOW[0]) & (hod < TROUGH_WINDOW[1])
    month_of_day = np.searchsorted(
        np.array(_MONTH_START_HOUR + [HOURS]), np.arange(365) * 24, side="right"
    )

    rows = []
    for year in years:
        for area, zone in POCKET_ZONE.items():
            plants = set(mem[mem["lcr_area"] == area]["plant_id"].astype(int))
            nl = zone_net_load(year, zone)
            mw = pocket_ct_mw(year, plants)
            batt = zone_battery_mw(year, zone)
            for d in range(365):
                sl = slice(d * 24, (d + 1) * 24)
                ramp = float(nl[sl][w_eve[sl]].mean() - nl[sl][w_trough[sl]].min())
                rows.append(
                    (
                        year,
                        area,
                        d,
                        _SEASON_BY_MONTH[month_of_day[d] - 1],
                        ramp,
                        batt,
                        float(mw[sl][w_commit[sl]].mean()),
                    )
                )
    return pd.DataFrame(
        rows,
        columns=["year", "area", "day", "season", "ramp_mw", "batt_mw", "commit_mw"],
    )


def loyo_table(panel: pd.DataFrame, driver: str) -> list[tuple]:
    """LOYO: predict each held-out year from the other two years' curve.

    The curve is the design's estimator — mean committed MW per
    (season, pooled-driver-decile) cell, decile edges frozen on the training
    years (the fixed-MW-edge construction the artifact would have carried so
    a forecast year's steeper ramps map onto higher bins). Season cells
    missing in training fall back to the all-season decile mean.
    """
    out = []
    for area in POCKET_ZONE:
        a = panel[panel["area"] == area]
        for held in sorted(a["year"].unique()):
            tr = a[a["year"] != held]
            te = a[a["year"] == held]
            edges = np.quantile(tr[driver], np.linspace(0.0, 1.0, N_BINS + 1))

            def _bin(x: np.ndarray) -> np.ndarray:
                return np.clip(
                    np.searchsorted(edges, x, side="right") - 1, 0, N_BINS - 1
                )

            trb = tr.assign(bin=_bin(tr[driver].to_numpy()))
            curve = trb.groupby(["season", "bin"])["commit_mw"].mean()
            fallback = trb.groupby("bin")["commit_mw"].mean()
            teb = te.assign(bin=_bin(te[driver].to_numpy()))
            pred = np.array(
                [
                    curve.get((s, b), fallback.get(b, float(trb["commit_mw"].mean())))
                    for s, b in zip(teb["season"], teb["bin"])
                ]
            )
            span = COMMIT_WINDOW[1] - COMMIT_WINDOW[0]
            act_twh = te["commit_mw"].sum() * span / 1e6
            pred_twh = float(pred.sum()) * span / 1e6
            out.append((area, held, act_twh, pred_twh))
    return out


def main() -> None:
    """Build the panel, score every candidate driver LOYO, print the verdict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    panel = build_panel(years)
    # Candidate drivers: the filed one plus the two storage-conditioned
    # rescue variants (both measured + forward-native — the model tracks the
    # battery build by year — so they were admissible had they worked).
    panel["drv_filed"] = panel["ramp_mw"]
    panel["drv_ramp_minus_batt"] = panel["ramp_mw"] - panel["batt_mw"]
    panel["drv_ramp_over_batt"] = panel["ramp_mw"] / panel["batt_mw"].clip(lower=1.0)

    print("Pocket committed-window energy (TWh, HE15-23 mean MW x 9h x 365d):")
    for area in POCKET_ZONE:
        a = panel[panel["area"] == area]
        vals = {
            y: round(float(a[a["year"] == y]["commit_mw"].sum()) * 9 / 1e6, 3)
            for y in years
        }
        print(f"  {area:26s} {vals}")

    worst_abs_2025 = 0.0
    for driver in ("drv_filed", "drv_ramp_minus_batt", "drv_ramp_over_batt"):
        print(f"\nLOYO (curve trained on the other years) — driver: {driver}")
        for area, held, act, pred in loyo_table(panel, driver):
            err = (pred - act) / max(act, 1e-9) * 100.0
            flag = "  <-- FAIL" if abs(err) > 50.0 else ""
            print(
                f"  {area:26s} held-out {held}: actual {act:6.3f} TWh, "
                f"predicted {pred:6.3f} TWh ({err:+7.0f} %){flag}"
            )
            if held == max(years):
                worst_abs_2025 = max(worst_abs_2025, abs(err))

    print(
        "\nVERDICT: "
        + (
            "REFUTED — the response curve fails its own §4 LOYO gate at the "
            "estimation stage (held-out final year mispredicted by up to "
            f"{worst_abs_2025:+.0f} %); no artifact written, no mechanism "
            "implemented (see module docstring / the caiso-81 FINDING)."
            if worst_abs_2025 > 50.0
            else "curve passes estimation-stage LOYO — re-open the design "
            "doc's implementation path."
        )
    )


if __name__ == "__main__":
    main()
