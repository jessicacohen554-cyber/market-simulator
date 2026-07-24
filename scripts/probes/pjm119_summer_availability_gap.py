"""PJM C3a/C3c Lane 1 probe: size the missing summer thermal de-rate.

Captures the keeper's own hourly ``availability`` matrix (the array the LP's
generator upper bound is built from) without solving the LP, by wrapping
:func:`market_sim.data.fleet.generators_to_fleet_arrays` at the ``runner`` call
site and aborting the run immediately after the fleet-array build. Reports, per
month and for the summer-peak hours specifically, the cap-weighted mean
availability of the PJM fossil-thermal classes the measured PJM outage feed
covers, alongside the measured unplanned-outage MW from Data Miner 2
(``data.pjm_outages``) — i.e. the model's *modelled* de-rate vs the *measured*
one, in GW.

Diagnostic only (no dispatch, no scoring): it answers "how many GW of thermal
capacity does the model keep available at the June/July peaks that PJM reports
on forced/maintenance outage?", which is the Lane 1 gating question in the
PJM 2025 summer-scarcity handoff.

Usage:
    python scripts/probes/pjm119_summer_availability_gap.py \
        results/calibration/pjm_netrev_retune --year 2025 [--dam-overlay]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import replay_keeper as rk  # noqa: E402
import run_calibration as rc  # noqa: E402
import run_calibration_full as rcf  # noqa: E402
from market_sim.data.pjm_outages import (  # noqa: E402
    PJM_OUTAGE_COVERED_GROUPS,
    pjm_outage_mw_series,
)


class _Captured(Exception):
    """Sentinel raised to abort the run once the fleet arrays exist."""


def capture(bundle: Path, year: int, overrides: dict, out: Path) -> Path:
    """Solve nothing: build ``year``'s fleet arrays for ``bundle``'s config, dump them."""
    meta = json.loads((bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["years"] = [int(year)]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = out.parent / f"_capture_{year}"
    # The DA-virtual mechanism is availability-independent and hard-fails without
    # its (gitignored) raw feed — off for the capture, which never solves.
    kwargs.setdefault("prb_overrides", {})["pjm_da_virtual_bids"] = False
    if overrides:
        kwargs["prb_overrides"].update(overrides)

    real = rc.generators_to_fleet_arrays

    def _wrapped(generators, zone_names, **kw):
        fa = real(generators, zone_names, **kw)
        np.savez_compressed(
            out,
            availability=fa.availability.astype(np.float32),
            pmax=fa.pmax.astype(np.float64),
            min_gen=(
                fa.min_gen.astype(np.float32)
                if getattr(fa, "min_gen", None) is not None
                else np.zeros((0, 0), dtype=np.float32)
            ),
            groups=np.array([str(g.plant_group) for g in generators]),
        )
        raise _Captured

    rc.generators_to_fleet_arrays = _wrapped
    try:
        rcf.solve_and_persist(**kwargs)
    except _Captured:
        pass
    finally:
        rc.generators_to_fleet_arrays = real
    return out


def report(npz: Path, year: int, label: str) -> pd.DataFrame:
    """Print the modelled-vs-measured de-rate table for a captured fleet."""
    d = np.load(npz, allow_pickle=False)
    avail, pmax, groups = d["availability"], d["pmax"], d["groups"]
    covered = np.isin(groups, sorted(PJM_OUTAGE_COVERED_GROUPS))
    cap = pmax[covered]
    a = avail[covered].astype(np.float64)
    # Modelled available MW and the de-rate it implies against nameplate.
    avail_mw = (a * cap[:, None]).sum(axis=0)
    nameplate = float(cap.sum())
    model_derate = nameplate - avail_mw

    meas_mw = pjm_outage_mw_series(int(year), a.shape[1])
    idx = pd.date_range(f"{year}-01-01", periods=a.shape[1], freq="h")
    df = pd.DataFrame(
        {
            "model_derate_gw": model_derate / 1000.0,
            "measured_derate_gw": meas_mw / 1000.0,
        },
        index=idx,
    )
    df["gap_gw"] = df["measured_derate_gw"] - df["model_derate_gw"]

    print(
        f"\n=== {label} ({year}) — PJM fossil-thermal nameplate {nameplate / 1000:.1f} GW"
    )
    print("month  model_derate  measured  gap   (GW, monthly mean)")
    mo = df.groupby(df.index.month).mean()
    for m, row in mo.iterrows():
        print(
            f"  {m:>2}      {row.model_derate_gw:6.2f}      "
            f"{row.measured_derate_gw:6.2f}  {row.gap_gw:+6.2f}"
        )
    print(
        f"  ann     {df.model_derate_gw.mean():6.2f}      "
        f"{df.measured_derate_gw.mean():6.2f}  {df.gap_gw.mean():+6.2f}"
    )
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument(
        "--dam-overlay",
        action="store_true",
        help="capture with pjm_dam_availability=True (the aggregate overlay) "
        "instead of the keeper's CAMPD-only availability",
    )
    ap.add_argument("--out-dir", default=None)
    args = ap.parse_args()

    out_dir = Path(args.out_dir or (REPO / "results" / "probes" / "pjm119"))
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = "damoverlay" if args.dam_overlay else "keeper"
    npz = out_dir / f"avail_{tag}_{args.year}.npz"
    overrides = {"pjm_dam_availability": True} if args.dam_overlay else {}
    if not npz.exists():
        capture(Path(args.bundle), args.year, overrides, npz)
    df = report(npz, args.year, tag)
    df.to_parquet(out_dir / f"derate_{tag}_{args.year}.parquet")


if __name__ == "__main__":
    main()
