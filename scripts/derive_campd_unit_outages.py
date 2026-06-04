"""Derive *unit-level* outage windows from EPA CAMPD hourly gross generation.

The facility-level detector (``scripts/derive_campd_outages.py``) sums every
unit at a plant into one CEMS series, so a single-unit outage at a multi-unit
plant — and, critically, a *coal*-unit outage at a mixed coal/gas facility
(W A Parish, Barney M Davis) — is masked by the units that keep running and is
never detected. This script reads the per-unit CAMPD extracts in
``inputs/raw-data/campd-unit-level/{STATE}_{YEAR}.parquet`` (one row per
``unit``-hour, carrying ``unitId``) and detects an outage for each *unit*
independently, on the unit's own gross output.

For every sustained unit outage (>= ``--min-outage-days``) it writes one row to
``inputs/raw-data/campd-unit-outages.csv`` in the schema the unit-level derate
overlay (:func:`market_sim.data.outages.unit_outage_derate_factors`) consumes:
each row removes the unit's capacity share of its model bin from availability
over the outage window. The unit's capacity is the EIA-860 generator nameplate
(matched on plant code + normalised unit id), falling back to the unit's
observed CAMPD peak gross when no EIA-860 generator matches.

The detector is chosen by the *unit's own fuel*, because what a per-unit output
gap means depends on how the unit is run:

* **Coal** units are baseload — they run continuously when available, so a
  sustained CF below :data:`~scripts.derive_campd_outages.REAL_RUN_CF` genuinely
  marks an outage. They use the averaged real-run rule (same as the facility
  detector for coal). This is the layer's core job: catch coal-unit outages the
  facility detector hides behind a mixed facility's running gas units (W A
  Parish 5-8) or behind other coal units at a multi-unit plant.
* **Everything else** (combined cycle, gas-steam) is load-following: an idle
  hour is usually economics, not a forced outage, so the averaged rule would
  badly over-flag a merchant CC turbine that simply isn't dispatched. These use
  the **event-based** rule — a window is broken by *any* single hour above
  :data:`~scripts.derive_campd_outages.ST_GAS_CF_PEAK` — so a unit is flagged
  only when it produced essentially nothing for the whole span (a genuine dead
  period), while an economically-idle-but-occasionally-firing unit is left to
  the economic dispatch and the facility-level overlay.

Detection is per calendar year, matching the facility detector; a window
straddling Dec 31 is clipped at the year boundary and each side must
independently clear the duration floor.

Combustion-turbine peakers carry no outage overlay (they dispatch
economically), so plants whose model bin is ``CT_PEAKER`` — and the
``ST_GAS`` peaker plants in
:data:`market_sim.data.outages.ST_GAS_PEAKER_PLANTS` — are skipped, matching the
overlay's convention.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
)
from scripts.derive_campd_outages import (  # noqa: E402
    ST_GAS_CF_PEAK,
    detect_outages,
    detect_outages_eventbased,
)

# CAMPD unit-level extracts live in their own subdirectory; the flat raw-data
# files are facility-summed and carry no unitId.
UNIT_LEVEL_DIR: Path = REPO / "inputs" / "raw-data" / "campd-unit-level"


def _norm_unit_id(uid: object) -> str:
    """Return an upper-cased alphanumeric-only unit id (drop spaces/dashes)."""
    return re.sub(r"[^0-9A-Za-z]", "", str(uid)).upper()


def build_capacity_index(
    eia860_path: Path,
) -> tuple[dict[tuple[int, str], float], dict[tuple[int, str], list[float]]]:
    """Return ``(exact, by_digits)`` EIA-860 nameplate lookups.

    CAMPD unit ids and EIA-860 generator ids label the same units differently
    (CAMPD ``WAP5`` vs EIA ``5``; CAMPD ``1`` vs EIA ``OG1``), so two lookups
    are built keyed by EIA plant code:

    * ``exact``: ``(plant, NORMALISED_ID) -> nameplate_mw`` — a direct hit when
      the ids already agree once punctuation/case are normalised.
    * ``by_digits``: ``(plant, DIGITS) -> [nameplate_mw, ...]`` — matched only
      when a single generator at the plant carries those trailing digits, so
      ``WAP5``/``5`` and ``1``/``OG1`` join without colliding.
    """
    gens = pd.read_parquet(
        eia860_path, columns=["plant_id", "generator_id", "nameplate_capacity_mw"]
    ).dropna(subset=["generator_id"])
    exact: dict[tuple[int, str], float] = {}
    by_digits: dict[tuple[int, str], list[float]] = {}
    for plant_id, gen_id, cap in gens.itertuples(index=False):
        if pd.isna(cap) or float(cap) <= 0.0:
            continue
        pid = int(plant_id)
        full = _norm_unit_id(gen_id)
        exact[(pid, full)] = float(cap)
        digits = re.sub(r"\D", "", full)
        if digits:
            by_digits.setdefault((pid, digits), []).append(float(cap))
    return exact, by_digits


def unit_capacity_mw(
    plant_id: int,
    unit_id: object,
    exact: dict[tuple[int, str], float],
    by_digits: dict[tuple[int, str], list[float]],
    observed_peak: float,
) -> tuple[float, str]:
    """Return ``(capacity_mw, source)`` for a CAMPD unit.

    Prefers the EIA-860 nameplate (exact id match, then a unique trailing-digit
    match) so the derate denominator is on the same nameplate basis as the
    model bin; falls back to the unit's observed CAMPD peak gross when no
    generator matches.
    """
    full = _norm_unit_id(unit_id)
    if (plant_id, full) in exact:
        return exact[(plant_id, full)], "eia_exact"
    digits = re.sub(r"\D", "", full)
    if digits:
        hits = by_digits.get((plant_id, digits))
        if hits and len(hits) == 1:
            return hits[0], "eia_digits"
    return observed_peak, "observed_peak"


def _unit_year_grid(sub: pd.DataFrame, year: int) -> np.ndarray:
    """Return one unit-year's hourly gross on the full calendar-year clock.

    CAMPD omits non-operating hours, so the unit's reported hours are placed on
    a gap-free hourly index spanning the whole year and missing hours are
    zero-filled (missing = no activity = offline), matching the facility
    detector. Returns the gross-MW array (length = hours in the year).
    """
    ts = sub["date"] + pd.to_timedelta(sub["hour"], unit="h")
    series = pd.Series(sub["grossLoad"].to_numpy(dtype=float), index=ts)
    series = series.groupby(level=0).sum().sort_index()
    full = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    return series.reindex(full).fillna(0.0).to_numpy(dtype=float)


def _load_unit_year(state: str, year: int) -> pd.DataFrame:
    """Load one unit-level state-year extract, or empty when absent."""
    path = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
    if not path.exists():
        print(f"  (no unit-level extract for {state} {year}: {path.name})")
        return pd.DataFrame()
    df = pd.read_parquet(
        path,
        columns=["facilityId", "facilityName", "unitId", "date", "hour",
                 "grossLoad", "primaryFuelInfo"],
    )
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df["facilityId"] = df["facilityId"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce")
    return df.dropna(subset=["hour"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024])
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--min-outage-days", type=float, default=5.0)
    ap.add_argument(
        "--bins", default=str(REPO / "inputs" / "custom-bin-assignments.csv"),
        help="Per-plant bin CSV; supplies each facility's model plant group.",
    )
    ap.add_argument(
        "--eia860",
        default=str(REPO / "inputs" / "raw-data" / "eia-860" / "eia860_generators.parquet"),
        help="EIA-860 generator parquet, for per-unit nameplate capacity.",
    )
    ap.add_argument(
        "--out", default=None,
        help="Output CSV; defaults to inputs/raw-data/campd-unit-outages.csv "
             "(ERCOT) or campd-unit-outages-{ISO}.csv.",
    )
    args = ap.parse_args()
    min_outage_hours = int(round(args.min_outage_days * 24))
    iso = args.iso.upper()
    if args.out is None:
        fname = (
            "campd-unit-outages.csv" if iso == "ERCOT"
            else f"campd-unit-outages-{iso}.csv"
        )
        args.out = str(REPO / "inputs" / "raw-data" / fname)

    # Each facility's model plant group (the LP bin the derate routes into).
    # Split facilities (W A Parish 3470, Barney M Davis 4939) carry their
    # primary group here; the overlay's _unit_outage_target re-routes their
    # gas-steam units to the split code by unit id, so the group passed for
    # them is immaterial.
    bins = pd.read_csv(args.bins)
    group_by_code = {
        int(c): str(g)
        for c, g in zip(bins["Plant_Code"], bins["Plant_Group"])
    }

    exact, by_digits = build_capacity_index(Path(args.eia860))

    states = campd.states_for_iso(iso)
    rows: list[dict] = []
    summary: list[tuple] = []
    for state in states:
        for year in args.years:
            df = _load_unit_year(state, year)
            if df.empty:
                continue
            for fac_id, fac in df.groupby("facilityId", observed=True):
                group = group_by_code.get(int(fac_id))
                # Only the coal/CC/gas-steam fleet carries an outage overlay;
                # peakers (CT and the listed ST_GAS peakers) dispatch
                # economically and are skipped, matching the overlay.
                if group not in QUALIFYING_PLANT_GROUPS:
                    continue
                if int(fac_id) in ST_GAS_PEAKER_PLANTS:
                    continue
                fac_name = str(fac["facilityName"].iloc[0])
                units = {
                    uid: _unit_year_grid(u, year)
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # A unit is coal (baseload) when its primary fuel is solid;
                # CAMPD labels every solid fuel — including ERCOT's lignite —
                # as "Coal".
                unit_is_coal = {
                    uid: str(u["primaryFuelInfo"].iloc[0]).strip().lower() == "coal"
                    for uid, u in fac.groupby("unitId", observed=True)
                }
                # Per-unit nameplate (EIA-860, peak fallback) and the facility
                # nameplate total for the informational pct column.
                peaks = {uid: float(g.max()) for uid, g in units.items()}
                caps: dict[object, tuple[float, str]] = {
                    uid: unit_capacity_mw(
                        int(fac_id), uid, exact, by_digits, peaks[uid]
                    )
                    for uid in units
                }
                fac_cap = sum(c for c, _ in caps.values()) or 0.0
                ran = {uid for uid, pk in peaks.items() if pk > 0.0}
                for uid, gross in units.items():
                    cap, cap_src = caps[uid]
                    # A unit that never reported gross output this year is
                    # left to the statistical/facility layers — we cannot
                    # distinguish a real full-year outage from a unit monitored
                    # under another id, and have no capacity basis for it.
                    if peaks[uid] <= 0.0 or cap <= 0.0:
                        continue
                    # Coal (baseload): a sustained low-output gap is an outage.
                    # Everything else (load-following CC / gas-steam): only a
                    # genuine dead span — no output at all — counts, via the
                    # event-based rule, so economic idleness is not over-flagged.
                    if unit_is_coal[uid]:
                        windows = detect_outages(gross, cap, min_outage_hours)
                    else:
                        windows = detect_outages_eventbased(
                            gross, cap, min_outage_hours, ST_GAS_CF_PEAK
                        )
                    if not windows:
                        continue
                    clock = pd.date_range(
                        f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h"
                    )
                    out_days = 0.0
                    for s, e in windows:
                        start = clock[s]
                        last = clock[e - 1]
                        duration_days = round((e - s) / 24.0, 1)
                        out_days += duration_days
                        peers = sum(
                            1 for o in ran if o != uid
                        )
                        rows.append({
                            "facility_name": fac_name,
                            "facility_id": int(fac_id),
                            "unit_id": uid,
                            "unit_capacity_mw": round(cap, 1),
                            "plant_capacity_mw": round(fac_cap, 1),
                            "unit_pct_of_plant": (
                                round(100.0 * cap / fac_cap, 1) if fac_cap else None
                            ),
                            "plant_group": group,
                            "capacity_source": cap_src,
                            "outage_start": start.strftime("%Y-%m-%d"),
                            "outage_end": last.strftime("%Y-%m-%d"),
                            "duration_days": duration_days,
                            "peer_units_online": peers,
                            "total_units_at_plant": len(units),
                        })
                    if out_days > 0:
                        summary.append(
                            (int(fac_id), fac_name, uid, group, year,
                             len(windows), out_days)
                        )

    cols = [
        "facility_name", "facility_id", "unit_id", "unit_capacity_mw",
        "plant_capacity_mw", "unit_pct_of_plant", "plant_group",
        "capacity_source", "outage_start", "outage_end", "duration_days",
        "peer_units_online", "total_units_at_plant",
    ]
    out = pd.DataFrame(rows, columns=cols).sort_values(
        ["facility_id", "unit_id", "outage_start"]
    )
    out.to_csv(args.out, index=False)

    print(f"\nwrote {len(out)} unit-outage windows to {args.out}\n")
    print(f"{'code':>6} {'plant':<24}{'unit':<8}{'group':<11}{'yr':>5}"
          f"{'#win':>5}{'out d':>8}")
    for code, nm, uid, g, yr, n, td in sorted(
        summary, key=lambda r: (r[0], str(r[2]), r[4])
    ):
        print(f"{code:>6} {nm[:23]:<24}{str(uid):<8}{g:<11}{yr:>5}{n:>5}{td:>8.0f}")


if __name__ == "__main__":
    main()
