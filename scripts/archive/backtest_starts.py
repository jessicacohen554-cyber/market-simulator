"""Backtest modeled unit starts against CAMPD historic actuals.

This is the start-count probe into "how much do startup costs really move the
model": it counts, per plant and per asset type / ISO / month, how many times a
unit physically started in the historic CAMPD (CEMS) record, converts that into
an annual startup-O&M dollar figure using the NREL startup-cost tables, and --
when pointed at a run bundle -- does the same for the model's dispatch and
reports the plant-by-plant delta and the annual O&M cost delta.

Two sides:

* Historic actuals (always available). A start is an off->on transition in the
  unit-level CAMPD record. The cleaner ``opTime`` signal (fraction of the hour
  the unit ran, unit-level only) is used when present, falling back to a
  ``grossLoad`` crossing -- the same off->on rule ``campd._startup_factors``
  uses at the plant grain. Capacity is the unit's max gross load.

* Modeled (requires a run bundle). Reads ``dispatch/<year>_<pass>.parquet`` from
  a calibration bundle (written by ``run_calibration_full.py``; gitignored, so
  regenerate the bundle first) and counts off->on transitions in each plant's
  hourly MW. The dispatch frame is keyed by ``plant_code`` (EIA ORISPL), which
  joins to the historic ``facilityId``.

Startup cost ($/MW per start) comes from the same NREL/SR-5500-55433 tables the
dispatch model amortizes into the P1 bid markup
(``config/constants.py``). Without a per-unit heat rate in the CAMPD extract we
key the rate off asset type using a representative tranche; ``--cc-rate`` /
``--ct-rate`` override it for a sensitivity sweep.

Usage:
    # Historic actuals only -- the size-of-the-prize number:
    python scripts/archive/backtest_starts.py --iso ERCOT --year 2024
    python scripts/archive/backtest_starts.py --states TX --year 2024 --by month

    # Modeled vs actual delta (after producing a bundle with a dispatch/ dir):
    python scripts/archive/backtest_starts.py --iso ERCOT --year 2024 \
        --bundle results/calibration/ercot_keeper --pass P1
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

import numpy as np
import pandas as pd

# ISO -> CAMPD state footprint, mirrored from market_sim.data.campd.ISO_STATES.
# States overlap across ISOs (e.g. IL in both PJM and MISO); without the
# EIA-860 balancing-authority fleet filter an ISO slice on an overlapping state
# is approximate. ERCOT (TX) and CAISO (CA) are clean single-state footprints.
ISO_STATES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("TX",),
    "CAISO": ("CA",),
    "NYISO": ("NY", "NJ"),
    "NEISO": ("ME", "NH", "MA", "CT", "RI", "VT"),
    "PJM": (
        "PA",
        "NJ",
        "MD",
        "DE",
        "IL",
        "OH",
        "IN",
        "KY",
        "WV",
        "VA",
        "NC",
        "TN",
        "MI",
        "DC",
    ),
    "MISO": (
        "AR",
        "IA",
        "IL",
        "IN",
        "KY",
        "LA",
        "MI",
        "MN",
        "MO",
        "MS",
        "ND",
        "SD",
        "TX",
        "WI",
    ),
}

# Representative startup cost ($/MW per start), NREL/SR-5500-55433 (Kumar 2012),
# matching CC_STARTUP_PARAMS / CT_STARTUP_PARAMS in config/constants.py. CAMPD
# carries no per-unit heat rate, so we use the f-class CC and older-CT tranches
# as the central estimate; override with --cc-rate / --ct-rate.
DEFAULT_CC_RATE = 48.6  # CC f-class (range 24.1-63.8)
DEFAULT_CT_RATE = 19.0  # CT older  (range 12.3-24.5)

# CAMPD ``unitType`` -> model klass. Combined cycle and combustion turbine are
# the commitment-screened cyclers; everything else is a steam boiler (coal/oil),
# which the model treats as must-run / output-cycling, not start/stop.
_ONLINE_MW = 1.0


def _klass(unit_type: str) -> str:
    ut = (unit_type or "").lower()
    if "combined cycle" in ut and "ended" not in ut:
        return "CC"
    if "combustion turbine" in ut and "ended" not in ut:
        return "CT"
    if "combined cycle" in ut:  # transitional "CT (started)/CC (ended)" rows
        return "CC"
    if "combustion turbine" in ut:
        return "CT"
    return "STEAM"


def _model_klass_bucket(klass: str) -> str:
    """Map a model dispatch class to the bare CC/CT cycler bucket.

    The dispatch frame carries the full model taxonomy (``CC_REGULAR``,
    ``CC_CHP``, ``CT_PEAKER``, ``CT_CHP``, ``ST_GAS``, ``COAL_*``, ``oil`` ...),
    while the historic side keys startup cost off the bare ``CC`` / ``CT``
    classes. Combined-cycle and combustion-turbine variants collapse to ``CC`` /
    ``CT``; every non-cycler (gas/coal steam, oil, nuclear, hydro, wind, solar)
    passes through unchanged and is dropped by the CC/CT filter downstream.
    """
    k = (klass or "").upper()
    if "CC" in k:
        return "CC"
    if "CT" in k:
        return "CT"
    return k


def _starts_from_online(online: np.ndarray) -> int:
    """Count off->on transitions in a boolean online series."""
    if online.sum() < 1:
        return 0
    prev = np.concatenate([[False], online[:-1]])
    return int((online & ~prev).sum())


def historic_starts(states: tuple[str, ...], year: int) -> pd.DataFrame:
    """Per-unit historic start counts and capacity from CAMPD unit-level data.

    Returns one row per (state, facilityId, unitId) with ``klass``, ``starts``,
    ``cap_mw``, ``online_hrs`` and per-month start counts ``m01``..``m12``.
    """
    rows: list[dict] = []
    for st in states:
        path = f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not os.path.exists(path):
            print(f"  (no CAMPD extract for {st} {year}, skipping)", file=sys.stderr)
            continue
        df = pd.read_parquet(
            path,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "unitType",
            ],
        )
        df = df.sort_values(["facilityId", "unitId", "date", "hour"])
        df["month"] = pd.to_datetime(df["date"]).dt.month
        for (fid, uid, ut), g in df.groupby(
            ["facilityId", "unitId", "unitType"], sort=False
        ):
            opt = g["opTime"].to_numpy()
            gross = g["grossLoad"].to_numpy()
            if np.isfinite(opt).any() and np.nanmax(opt) > 0:
                online = np.nan_to_num(opt, nan=0.0) > 0.0
            else:
                online = np.nan_to_num(gross, nan=0.0) > _ONLINE_MW
            cap = float(np.nanmax(gross)) if np.isfinite(gross).any() else 0.0
            month = g["month"].to_numpy()
            row = {
                "state": st,
                "facilityId": int(fid),
                "unitId": str(uid),
                "klass": _klass(ut),
                "unitType": ut,
                "starts": _starts_from_online(online),
                "cap_mw": cap,
                "online_hrs": int(online.sum()),
            }
            for m in range(1, 13):
                row[f"m{m:02d}"] = _starts_from_online(online & (month == m))
            rows.append(row)
    return pd.DataFrame(rows)


def historic_plant_starts(states: tuple[str, ...], year: int) -> pd.DataFrame:
    """Per-PLANT plant-aggregate historic CC/CT starts (like-for-like grain).

    ``historic_starts`` counts each *unit's* off->on and sums the counts to the
    plant; a four-CT plant whose units stagger so the plant never fully shuts
    racks up four units' worth of starts. The model, by contrast, dispatches
    each plant as a single aggregated offer curve (its ``unit_id`` tranches are
    points on that curve, not physical units), so it can only register a
    plant-aggregate cycle -- the whole plant's summed MW going off->on.

    To compare the two on the same footing this sums every CC/CT unit's gross
    load to the plant first, then counts plant-aggregate off->on with the same
    ``_ONLINE_MW`` threshold the modeled side uses on summed dispatched MW.
    Returns one row per ``facilityId`` with ``klass`` (majority CC/CT vote),
    ``starts`` and ``cap_mw`` (sum of per-unit max gross load).
    """
    rows: list[dict] = []
    for st in states:
        path = f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not os.path.exists(path):
            continue
        df = pd.read_parquet(
            path,
            columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType"],
        )
        df["klass"] = df["unitType"].map(_klass)
        df = df[df["klass"].isin(["CC", "CT"])].copy()
        if df.empty:
            continue
        df["ts"] = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"], unit="h")
        # Plant-aggregate online series: sum every CC/CT unit's gross load per
        # hour, online when the plant puts >_ONLINE_MW on the grid -- the same
        # rule the modeled side applies to summed dispatched MW.
        plant = df.groupby(["facilityId", "ts"], as_index=False)["grossLoad"].sum()
        klass_by_fac = df.groupby("facilityId")["klass"].agg(
            lambda s: s.value_counts().idxmax()
        )
        cap_by_fac = (
            df.groupby(["facilityId", "unitId"])["grossLoad"]
            .max()
            .groupby("facilityId")
            .sum()
        )
        for fid, g in plant.sort_values(["facilityId", "ts"]).groupby("facilityId"):
            online = g["grossLoad"].to_numpy() > _ONLINE_MW
            rows.append(
                {
                    "plant_code": int(fid),
                    "klass": str(klass_by_fac.get(fid, "")),
                    "starts": _starts_from_online(online),
                    "cap_mw": float(cap_by_fac.get(fid, 0.0)),
                }
            )
    return pd.DataFrame(rows)


def modeled_starts(bundle: str, year: int, pass_label: str) -> pd.DataFrame:
    """Per-plant modeled start counts from a run bundle's dispatch parquet.

    A start is an off->on transition in the plant's hourly summed MW. Returns
    one row per ``plant_code`` with ``klass``, ``starts`` and ``cap_mw``.
    """
    path = os.path.join(bundle, "dispatch", f"{year}_{pass_label}.parquet")
    if not os.path.exists(path):
        alt = sorted(glob.glob(os.path.join(bundle, "dispatch", f"{year}_*.parquet")))
        raise FileNotFoundError(
            f"{path} not found. The dispatch/ dir is gitignored -- regenerate "
            f"the bundle with run_calibration_full.py. Found: {alt or 'nothing'}"
        )
    d = pd.read_parquet(path)
    # _dispatch_frame columns: year, pass, unit_id, plant_code, klass, fuel,
    # supply, zone, hour, mw, lmp. The model taxonomy (CC_REGULAR, CT_PEAKER,
    # CC_CHP, ...) is collapsed to the bare CC/CT bucket the historic side and
    # the NREL startup tables key off.
    d = d.copy()
    d["bucket"] = d["klass"].map(_model_klass_bucket)
    plant = d.groupby(["plant_code", "hour"], as_index=False)["mw"].sum()
    rows: list[dict] = []
    # A plant's bucket is the cycler class most of its tranches carry (plants in
    # the ERCOT fleet are single-group, so this is just that group).
    bucket_by_plant = d.groupby("plant_code")["bucket"].agg(
        lambda s: s.value_counts().idxmax()
    )
    for pc, g in plant.sort_values(["plant_code", "hour"]).groupby("plant_code"):
        online = g["mw"].to_numpy() > _ONLINE_MW
        rows.append(
            {
                "plant_code": int(pc) if str(pc).isdigit() else pc,
                "klass": str(bucket_by_plant.get(pc, "")),
                "starts": _starts_from_online(online),
                "cap_mw": float(g["mw"].max()),
            }
        )
    return pd.DataFrame(rows)


def annual_om(df: pd.DataFrame, cc_rate: float, ct_rate: float) -> pd.Series:
    """Annual startup-O&M $ per row: starts * $/MW * cap_mw, CC/CT only."""
    rate = df["klass"].map({"CC": cc_rate, "CT": ct_rate}).fillna(0.0)
    return df["starts"] * rate * df["cap_mw"]


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--iso", choices=sorted(ISO_STATES))
    g.add_argument("--states", nargs="+")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument(
        "--by",
        choices=["type", "month", "iso"],
        default="type",
        help="historic aggregation grain (default: asset type)",
    )
    ap.add_argument("--bundle", help="run bundle dir for modeled vs actual delta")
    ap.add_argument("--pass", dest="pass_label", default="P1")
    ap.add_argument("--cc-rate", type=float, default=DEFAULT_CC_RATE)
    ap.add_argument("--ct-rate", type=float, default=DEFAULT_CT_RATE)
    args = ap.parse_args()

    states = ISO_STATES[args.iso] if args.iso else tuple(s.upper() for s in args.states)
    label = args.iso or "+".join(states)

    hist = historic_starts(states, args.year)
    if hist.empty:
        print("No historic CAMPD units found.")
        return
    hist["annual_om"] = annual_om(hist, args.cc_rate, args.ct_rate)
    cyc = hist[hist["klass"].isin(["CC", "CT"])]

    print(
        f"\n=== Historic CAMPD starts -- {label} {args.year} "
        f"({len(hist)} units, {len(cyc)} CC/CT cyclers) ==="
    )
    print(f"CC rate ${args.cc_rate}/MW/start, CT rate ${args.ct_rate}/MW/start\n")

    if args.by == "month":
        mcols = [f"m{m:02d}" for m in range(1, 13)]
        per_month = cyc.groupby("klass")[mcols].sum()
        per_month.columns = [f"{m}" for m in range(1, 13)]
        print("CC/CT starts by month:")
        print(per_month.to_string())
    elif args.by == "iso":
        print(
            cyc.groupby("klass")
            .agg(
                units=("starts", "size"),
                starts=("starts", "sum"),
                annual_om=("annual_om", "sum"),
            )
            .to_string()
        )
    else:
        agg = (
            hist.groupby("unitType")
            .agg(
                units=("starts", "size"),
                starts=("starts", "sum"),
                mean_starts=("starts", "mean"),
                median_starts=("starts", "median"),
                annual_om=("annual_om", "sum"),
            )
            .round(1)
        )
        print(agg.sort_values("starts", ascending=False).to_string())

    print(f"\nTotal CC/CT starts: {int(cyc['starts'].sum()):,}")
    print(f"Total annual startup O&M: ${cyc['annual_om'].sum():,.0f}")

    if not args.bundle:
        print("\n(no --bundle given; historic-actuals side only)")
        return

    mod = modeled_starts(args.bundle, args.year, args.pass_label)
    mod["annual_om"] = annual_om(mod, args.cc_rate, args.ct_rate)
    modc = mod[mod["klass"].isin(["CC", "CT"])]
    print(
        f"\n=== Modeled starts -- bundle {args.bundle} {args.year} "
        f"pass {args.pass_label} ({len(modc)} CC/CT plants) ==="
    )
    print(f"Total CC/CT starts: {int(modc['starts'].sum()):,}")
    print(f"Total annual startup O&M: ${modc['annual_om'].sum():,.0f}")

    # Like-for-like delta. The model dispatches each plant as a single
    # aggregated offer curve, so it can only register a plant-aggregate cycle
    # (whole-plant summed MW off->on). Comparing that to the unit-grain headline
    # above (which sums each unit's starts) is apples-to-oranges -- a multi-unit
    # plant whose units stagger never zeroes the plant sum, so unit-grain counts
    # several starts where the model (and the grid) sees one. The delta therefore
    # rebuilds the HISTORIC side on the same plant-aggregate grain.
    histp = historic_plant_starts(states, args.year)
    histp["annual_om"] = annual_om(histp, args.cc_rate, args.ct_rate)
    histpc = histp[histp["klass"].isin(["CC", "CT"])]
    print(
        f"\n=== Historic plant-aggregate (like-for-like grain) -- {label} "
        f"{args.year} ({len(histpc)} CC/CT plants) ==="
    )
    print(f"Total CC/CT starts: {int(histpc['starts'].sum()):,}")
    print(f"Total annual startup O&M: ${histpc['annual_om'].sum():,.0f}")

    hp = histpc.rename(columns={"starts": "hist_starts", "annual_om": "hist_om"})[
        ["plant_code", "hist_starts", "hist_om"]
    ]
    mp = modc.rename(columns={"starts": "mod_starts", "annual_om": "mod_om"})
    j = hp.merge(
        mp[["plant_code", "mod_starts", "mod_om"]], on="plant_code", how="outer"
    ).fillna(0)
    j["d_starts"] = j["mod_starts"] - j["hist_starts"]
    j["d_om"] = j["mod_om"] - j["hist_om"]
    print("\n=== Plant-by-plant delta (modeled - actual), top 15 by |O&M delta| ===")
    top = j.reindex(j["d_om"].abs().sort_values(ascending=False).index).head(15)
    print(
        top[
            [
                "plant_code",
                "hist_starts",
                "mod_starts",
                "d_starts",
                "hist_om",
                "mod_om",
                "d_om",
            ]
        ].to_string(
            index=False,
            formatters={
                "hist_om": "${:,.0f}".format,
                "mod_om": "${:,.0f}".format,
                "d_om": "${:,.0f}".format,
            },
        )
    )
    print(f"\nNet annual O&M delta (modeled - actual): ${j['d_om'].sum():,.0f}")
    print(f"Net start-count delta: {int(j['d_starts'].sum()):,}")


if __name__ == "__main__":
    main()
