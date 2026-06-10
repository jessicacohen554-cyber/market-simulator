"""Derive each thermal plant's committed and must-run tranche % from CAMPD.

Generalizes :mod:`scripts.derive_cc_committed_pct` (CC-only, ERCOT-only) to
**every thermal group and every ISO**, so a plant's minimum-stable-load
(committed) and baseload-floor (must-run) tranche sizes are grounded in its own
observed EPA CAMPD/CEMS hourly output rather than coarse assumed CSV buckets.
This is the per-ISO analogue of the hardcoded ERCOT maps
``fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT`` / ``fleet.COAL_MUSTRUN_BY_PLANT``:
the output CSV is loaded at runtime and applied per plant, so adding a new ISO
is just running this script against that ISO's CAMPD extracts.

Method, per ``(plant, group)`` in the ISO's fleet (groups: CC_REGULAR, CC_CHP,
CT_PEAKER, CT_CHP, ST_GAS, COAL):

  1. CAMPD gross load is summed across the plant's units per hour and scaled to
     **net** by the plant's parasitic factor (same grid-MW basis the dispatch
     produces), via :func:`market_sim.data.campd.plant_hourly_net`.
  2. Available capacity per hour = nameplate x the unit-outage availability
     multiplier (:func:`market_sim.data.outages.unit_outage_derate_factors`),
     i.e. nameplate net of the plant's units the unit-outage extract reports in
     maintenance — so a plant running its remaining units while one is out is
     not mistaken for running below its true minimum.
  3. **Committed %** = the P5 of the available-capacity factor over the plant's
     *online* hours (net > ``_ONLINE_FRAC`` of available capacity): the minimum
     stable load the plant holds at when backed down, excluding ramp transients.
  4. **Must-run %** = the P5 of the available-CF over *all* hours the plant has
     any available capacity. For a baseload unit that almost never shuts off
     (coal) this is the sunk floor it holds even when prices are low; for a
     load-following unit that cycles off (CC/CT/ST gas) it is ~0, exactly the
     physical must-run of an economically-dispatched plant. The dispatch uses
     this floor only where it is structurally meaningful (coal), so gas values
     are recorded for transparency but generally land near zero.

Per ISO it writes ``inputs/processed/thermal_tranches_{ISO}.csv`` with one row
per ``(plant_code, plant_group)``. Plants with too little run-time to set a
reliable floor are written with ``status != ok`` and keep the model's CSV/class
default.

Usage:
    python scripts/derive_thermal_tranches.py --iso PJM --years 2024
    python scripts/derive_thermal_tranches.py --iso ERCOT --years 2023 2024
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
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins, load_fleet_from_csv  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

# Thermal groups that carry an offer-curve committed/must-run tranche.
_THERMAL_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP", "COAL"}
)

# CHP cogen groups: these additionally get a steam-following floor
# (``chp_pmin_cf``) and an EIA-923 sector class (``chp_sector``), the
# ISO-generic analogue of the hardcoded ERCOT maps
# ``fleet.CHP_PMIN_CF_BY_PLANT`` / ``fleet.CHP_SECTOR_CLASS_BY_PLANT``.
_CHP_GROUPS: frozenset[str] = frozenset({"CC_CHP", "CT_CHP", "ST_CHP"})

# Percentile of the all-hours available-CF distribution taken as a CHP cogen's
# total must-run floor — the steady host-steam output it holds essentially
# always. P2 matches how ERCOT's CHP_PMIN_CF_BY_PLANT values were derived
# (p2 CAMPD gross CF, non-outage hours).
_CHP_PMIN_PCTILE: int = 2

# EIA-923 Page 1 "EIA Sector Number" -> the BTM sector class the model's
# chp_btm_pct uses. Cogen sectors map directly (3 = NAICS-22 / merchant cogen,
# 5 = commercial cogen, 7 = industrial cogen); non-cogen sectors land on the
# nearest class so a plant whose 923 rows are mixed still classifies.
_EIA_SECTOR_CLASS: dict[int, str] = {
    1: "merchant", 2: "merchant", 3: "merchant",
    4: "commercial", 5: "commercial",
    6: "industrial", 7: "industrial",
}


def _chp_sector_map(years: list[int]) -> dict[int, str]:
    """Return ``{plant_id: sector_class}`` from the EIA-923 Page 1 workbooks.

    Reads "EIA Sector Number" for every plant from the raw
    ``inputs/raw-data/f923_{year} (1).zip`` archives (the same source the
    monthly-generation artifact is built from) and maps it through
    :data:`_EIA_SECTOR_CLASS`. When a plant's sector differs across rows or
    years (rare), the most frequent class wins.
    """
    import zipfile
    from collections import Counter

    votes: dict[int, Counter] = {}
    for year in years:
        zpath = REPO / "inputs" / "raw-data" / f"f923_{year} (1).zip"
        if not zpath.exists():
            print(f"  (no EIA-923 archive for {year}: {zpath.name})")
            continue
        z = zipfile.ZipFile(zpath)
        sheet_file = next(
            (n for n in z.namelist() if "Schedules_2_3_4_5" in n), None
        )
        if sheet_file is None:
            continue
        with z.open(sheet_file) as f:
            df = pd.read_excel(
                f, sheet_name="Page 1 Generation and Fuel Data", skiprows=5,
                usecols=["Plant Id", "EIA Sector Number"],
            )
        df = df.dropna()
        for pid, sector in df.itertuples(index=False):
            klass = _EIA_SECTOR_CLASS.get(int(sector))
            if klass is not None:
                votes.setdefault(int(pid), Counter())[klass] += 1
    return {pid: c.most_common(1)[0][0] for pid, c in votes.items()}


# EIA-923-CF fallback floor for CHP plants without CAMPD coverage (small
# cogens below the CEMS reporting threshold — e.g. every PJM ST_CHP). The
# plant's pooled EIA-923 class net generation over nameplate approximates its
# steady steam-following output; the mean-to-floor haircut converts that
# average CF into a holdable floor (a steady cogen's P2 hourly CF runs a bit
# under its mean), and the cap keeps a CEMS-invisible plant from being forced
# on harder than any CAMPD-observed peer.
_CHP_F923_FLOOR_FACTOR: float = 0.85
_CHP_F923_FLOOR_CAP: float = 75.0


def _chp_f923_floor_cf(
    years: list[int], cap: dict[tuple[int, str], float],
) -> dict[tuple[int, str], float]:
    """Return ``{(code, group): pmin_cf %}`` from EIA-923 class net generation.

    For each CHP ``(plant, group)`` in the fleet, the pooled EIA-923 net
    generation of that class (canonical :func:`classify_plant` bucketing)
    divided by ``nameplate x hours`` gives the average CF; scaled by
    :data:`_CHP_F923_FLOOR_FACTOR` and capped it becomes the total must-run
    floor for plants the CAMPD extracts cannot see.
    """
    from market_sim.config.plant_taxonomy import classify_plant
    from market_sim.data.eia923 import load_monthly_generation

    gen = load_monthly_generation()
    gen = gen[gen["year"].isin(years)].copy()
    gen["klass"] = [
        classify_plant(f, pm, str(c).upper().startswith("Y"), int(pid))
        for f, pm, c, pid in zip(
            gen["fuel_type"], gen["prime_mover"], gen["chp"], gen["plant_id"]
        )
    ]
    by_key = gen.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum()
    out: dict[tuple[int, str], float] = {}
    for (code, group), nameplate in cap.items():
        if group not in _CHP_GROUPS or nameplate <= 0:
            continue
        mwh = float(by_key.get((code, group), 0.0))
        if mwh <= 0.0:
            continue
        avg_cf = mwh / (nameplate * 8760.0 * len(years))
        out[(code, group)] = min(
            100.0 * avg_cf * _CHP_F923_FLOOR_FACTOR, _CHP_F923_FLOOR_CAP
        )
    return out

# An hour counts as "online / committed" when net output clears this fraction
# of the hour's available capacity — low enough to admit one unit of a
# multi-unit plant idling at part load, high enough to reject CEMS sensor noise
# and the single-hour ramp through zero on start/stop.
_ONLINE_FRAC: float = 0.05

# Percentile of the CF distribution taken as the floor. P5 (not the absolute
# minimum) discards isolated ramp-transient hours while still capturing the
# minimum stable / baseload load.
_FLOOR_PCTILE: int = 5

# A plant needs at least this many online hours over the window to set a floor.
_MIN_ONLINE_HOURS: int = 24

# Physical ceilings on the derived tranche shares (a unit's CEMS gross can
# exceed its EIA nameplate, which would otherwise push the floor above 100%).
_COMMITTED_CAP: float = 0.70
_MUSTRUN_CAP: float = 0.60


def _parasitic_factor_map() -> dict[int, float]:
    """Return ``{plant_id: net/gross factor}`` from the derived artifact."""
    path = REPO / "inputs" / "processed" / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def _fleet_nameplate_and_group(
    iso: str,
) -> tuple[dict[tuple[int, str], float], dict[int, str]]:
    """Return ``({(code, group): nameplate}, {code: primary_group})`` for an ISO.

    ERCOT reads the CAMPD bin sheet (one bin per plant); other ISOs read the
    per-plant EIA-860 fleet. The primary group is the group holding the most
    nameplate at each plant, used to attribute the facility-summed CAMPD net.
    """
    cap: dict[tuple[int, str], float] = {}
    if iso == "ERCOT":
        bins = load_campd_bins("inputs/custom-bin-assignments.csv")
        for c, g, m in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
        ):
            if m and float(m) > 0:
                cap[(int(c), str(g))] = cap.get((int(c), str(g)), 0.0) + float(m)
    else:
        for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
            code = int(gen.plant_code)
            if code <= 0 or not gen.plant_group:
                continue
            key = (code, gen.plant_group)
            cap[key] = cap.get(key, 0.0) + float(gen.pmax_mw)
    primary: dict[int, str] = {}
    best: dict[int, float] = {}
    for (code, group), mw in cap.items():
        if mw > best.get(code, -1.0):
            best[code], primary[code] = mw, group
    return cap, primary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument("--years", nargs="+", type=int, default=[2024])
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    iso = args.iso.upper()
    out_path = Path(args.out) if args.out else (
        REPO / "inputs" / "processed" / f"thermal_tranches_{iso}.csv"
    )

    states = campd.states_for_iso(iso)
    if not states:
        ap.error(f"no CAMPD state mapping for ISO {iso}")

    cap, primary = _fleet_nameplate_and_group(iso)
    factors = _parasitic_factor_map()
    chp_sectors = _chp_sector_map(args.years)

    # Pool the available-CF samples across the requested years, per (code, group).
    online_cf: dict[tuple[int, str], list[np.ndarray]] = {}
    allhr_cf: dict[tuple[int, str], list[np.ndarray]] = {}
    for year in args.years:
        df = campd.load_campd_hourly(states, [year])
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue
        net = campd.plant_hourly_net(df, factors, year)  # {code: (8760,) net MW}
        derate = unit_outage_derate_factors(year, iso=iso)
        for (code, group), nameplate in cap.items():
            if group not in _THERMAL_GROUPS or nameplate <= 0:
                continue
            # Attribute the facility-summed CAMPD net to the plant's primary
            # group only; secondary-group rows at a multi-group plant are left
            # to the CSV default (their net cannot be separated from CEMS).
            if primary.get(code) != group:
                continue
            series = net.get(code)
            if series is None:
                continue
            avail_mult = derate.get((code, group), np.ones(len(series)))
            avail_cap = nameplate * avail_mult
            with np.errstate(divide="ignore", invalid="ignore"):
                acf = np.where(avail_cap > 0.0, series / avail_cap, 0.0)
            acf = np.clip(acf, 0.0, 1.5)  # guard multi-unit CEMS noise
            # Exclude hours with no usable net (NaN from a missing parasitic
            # factor or a CEMS reporting gap) from both samples.
            finite = np.isfinite(acf) & (avail_cap > 0.0)
            online = finite & (series > _ONLINE_FRAC * avail_cap)
            allhr_cf.setdefault((code, group), []).append(acf[finite])
            if online.any():
                online_cf.setdefault((code, group), []).append(acf[online])

    names = {}
    if iso != "ERCOT":
        for gen in load_fleet_from_csv(iso, get_iso_config(iso)):
            names[int(gen.plant_code)] = gen.name

    rows: list[dict] = []
    for (code, group), nameplate in sorted(cap.items()):
        if group not in _THERMAL_GROUPS or primary.get(code) != group:
            continue
        on = online_cf.get((code, group))
        allh = allhr_cf.get((code, group))
        n_online = int(sum(len(a) for a in on)) if on else 0
        if not on or n_online < _MIN_ONLINE_HOURS:
            rows.append({
                "plant_code": code, "plant_group": group,
                "name": names.get(code, ""), "status": "rarely_online",
                "online_hours": n_online,
            })
            continue
        on_cat = np.concatenate(on)
        all_cat = np.concatenate(allh) if allh else on_cat
        # Committed = min stable load when online; cap at a physical ceiling
        # (a plant whose CEMS gross runs above its EIA nameplate, e.g. Doswell,
        # would otherwise report a committed floor > 100%).
        committed = min(float(np.percentile(on_cat, _FLOOR_PCTILE)), _COMMITTED_CAP)
        # Must-run = the always-on baseload floor. Physically meaningful only
        # for COAL (take-or-pay baseload) — the dispatch applies a must-run
        # floor to coal only; fast gas (CC / CT / ST) is load-following and is
        # never forced on, so its must-run is recorded as zero even when its
        # high capacity factor would make the all-hours floor look high.
        if group == "COAL":
            mustrun = min(float(np.percentile(all_cat, _FLOOR_PCTILE)),
                          _MUSTRUN_CAP)
        else:
            mustrun = 0.0
        row = {
            "plant_code": code, "plant_group": group,
            "name": names.get(code, ""), "status": "ok",
            "nameplate_mw": round(nameplate, 1),
            "online_hours": n_online,
            "committed_pct": round(100.0 * committed, 1),
            "mustrun_pct": round(100.0 * mustrun, 1),
            "p25_cf": round(100.0 * float(np.percentile(on_cat, 25)), 1),
            "median_cf": round(100.0 * float(np.percentile(on_cat, 50)), 1),
        }
        # CHP cogens additionally carry their steam-following total must-run
        # floor (P2 of the all-hours available-CF, the ERCOT
        # CHP_PMIN_CF_BY_PLANT convention) and the EIA-923 sector class that
        # sizes the behind-the-meter host self-supply share.
        if group in _CHP_GROUPS:
            row["chp_pmin_cf"] = round(
                100.0 * float(np.percentile(all_cat, _CHP_PMIN_PCTILE)), 1
            )
            row["chp_sector"] = chp_sectors.get(code, "")
        rows.append(row)

    # CHP plants the CAMPD extracts cannot see (no facility series, or too few
    # online hours) get an EIA-923-derived steam-following floor instead, so
    # the sub-CEMS cogen fleet (e.g. every PJM ST_CHP plant) still carries its
    # measured host-steam obligation. status="eia923_cf" marks the source; the
    # committed/must-run tranche columns stay blank (class defaults apply).
    have_floor = {
        (r["plant_code"], r["plant_group"]) for r in rows
        if r["status"] == "ok" and r["plant_group"] in _CHP_GROUPS
    }
    f923_floors = _chp_f923_floor_cf(args.years, cap)
    for (code, group), pmin in sorted(f923_floors.items()):
        if (code, group) in have_floor or primary.get(code) != group:
            continue
        rows.append({
            "plant_code": code, "plant_group": group,
            "name": names.get(code, ""), "status": "eia923_cf",
            "nameplate_mw": round(cap[(code, group)], 1),
            "online_hours": 0,
            "chp_pmin_cf": round(pmin, 1),
            "chp_sector": chp_sectors.get(code, ""),
        })

    out = pd.DataFrame(rows)
    ok = out[out["status"].isin(["ok", "eia923_cf"])].sort_values(
        ["plant_group", "plant_code"]
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ok.to_csv(out_path, index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_rows", 400)
    print(f"\n{iso} thermal committed / must-run %  —  CAMPD years "
          f"{args.years} (net vs available capacity)\n")
    cols = ["plant_code", "plant_group", "name", "nameplate_mw",
            "online_hours", "committed_pct", "mustrun_pct", "median_cf"]
    campd_ok = ok[ok["status"] == "ok"]
    print(campd_ok[cols].to_string(index=False))
    chp_rows = ok[ok["plant_group"].isin(_CHP_GROUPS)]
    if not chp_rows.empty:
        print("\nCHP steam-following floors (chp_pmin_cf % of nameplate; "
              "source: CAMPD p2 where status=ok, EIA-923 CF otherwise):")
        print(chp_rows[["plant_code", "plant_group", "name", "nameplate_mw",
                        "status", "chp_pmin_cf", "chp_sector"]]
              .to_string(index=False))
    print("\nby group (capacity-weighted committed%):")
    for g, sub in campd_ok.groupby("plant_group"):
        w = sub["nameplate_mw"]
        cw = float((sub["committed_pct"] * w).sum() / w.sum()) if w.sum() else 0.0
        mw = float((sub["mustrun_pct"] * w).sum() / w.sum()) if w.sum() else 0.0
        print(f"  {g:<12} n={len(sub):>3}  committed~{cw:5.1f}%  mustrun~{mw:5.1f}%")
    skipped = out[out["status"] != "ok"]
    print(f"\nwrote {len(ok)} plant-groups to {out_path} "
          f"({len(skipped)} skipped: too little run-time)")


if __name__ == "__main__":
    main()
