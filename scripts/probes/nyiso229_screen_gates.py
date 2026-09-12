#!/usr/bin/env python3
"""Score the nyiso-229 2022 screen gates from two bundles' committed hourlies.

Pre-registration: ``results/calibration/PRECOMMIT-nyiso229-outage-window-hour-grain.md``
§4, plus ``docs/ADDENDUM-nyiso229-gdrift-and-the-control-is-solved-in-shard-2026-09-12.md``
(G-CTRL moved to a control solved in the same shard).

The gates are STRUCTURAL and STOP-ONLY (rule 29 ``[R-SCREEN]``): they ask whether the
mechanism does what its own arithmetic says. None reads the target residual — C3a, C3b's
value and C3c are reported, never gated, in either direction.

Usage::

    python3 scripts/probes/nyiso229_screen_gates.py \\
        --control results/calibration/nyiso229_ctrl_y2022 \\
        --arm     results/calibration/nyiso229_arm_y2022
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

YEAR = 2022
#: The two hours the control sheds firm load at VOLL (2022-05-31 16:00 / 17:00),
#: measured in nyiso-229 phase 0 from the recovered nyiso-228 arm-C control.
VOLL_HOURS = (3616, 3617)
#: Restored-capacity reference, from the phase-0 derive (zero LP): the hour-grain
#: extract frees 3,657 MW at both VOLL hours against 124.9 / 235.6 MW shed.
RESTORED_AT_VOLL_MW = 3657.0


def _p1(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def restored_hour_mask(hour_grain_csv: Path, day_grain_csv: Path) -> np.ndarray:
    """Hours of ``YEAR`` in which the two extracts disagree about availability.

    G-CONF-2's reference set: the mechanism claims to change availability only
    where the day-grain window asserted unavailability the detector never
    detected, so a dispatch move outside this set is outside the mechanism's own
    footprint.
    """
    idx = pd.date_range(f"{YEAR}-01-01", f"{YEAR}-12-31 23:00", freq="h")
    mask = np.zeros(len(idx), dtype=bool)
    h = pd.read_csv(hour_grain_csv, parse_dates=["outage_start", "outage_end"])
    h = h[h.outage_start.dt.year == YEAR]
    for r in h.itertuples():
        day0 = pd.Timestamp(r.outage_start)
        day1 = pd.Timestamp(r.outage_end) + pd.Timedelta(days=1)
        hr0 = day0 + pd.Timedelta(hours=int(r.outage_start_hour))
        hr1 = pd.Timestamp(r.outage_end) + pd.Timedelta(hours=int(r.outage_end_hour) + 1)
        # the released edges: [day0, hr0) and [hr1, day1)
        for a, b in ((day0, hr0), (hr1, day1)):
            if b > a:
                mask[idx.searchsorted(a) : idx.searchsorted(b)] = True
    return mask


def score(control: Path, arm: Path, restored: np.ndarray | None) -> dict:
    out: dict = {"gates": {}, "reported": {}}
    cs, as_ = (_p1(p / "hourly" / f"system_{YEAR}.parquet") for p in (control, arm))

    def agg(s: pd.DataFrame) -> dict:
        by_h = s.groupby("hour").agg(
            slack=("slack", "sum"), dump=("dump", "sum"), dem=("demand", "sum")
        )
        lw = s.groupby("hour").apply(
            lambda d: float(np.average(d.price, weights=d.demand.clip(lower=1e-9))),
            include_groups=False,
        )
        return {
            "slack_mwh": float(by_h.slack.sum()),
            "slack_h": int((by_h.slack > 1e-6).sum()),
            "slack_at_voll": {h: float(by_h.slack.get(h, 0.0)) for h in VOLL_HOURS},
            "dump_mwh": float(by_h.dump.sum()),
            "served_twh": float(by_h.dem.sum() / 1e6),
            "lw_mean": float(np.average(lw, weights=by_h.dem)),
            "lw_max": float(lw.max()),
            "h_gt": {t: int((lw > t).sum()) for t in (150, 200, 300)},
            "_lw": lw,
        }

    c, a = agg(cs), agg(as_)

    # --- G-DIR: 2022 firm-load slack must FALL -------------------------------
    out["gates"]["G-DIR"] = {
        "test": "2022 firm-load slack must FALL",
        "control_mwh": c["slack_mwh"],
        "arm_mwh": a["slack_mwh"],
        "verdict": "PASS" if a["slack_mwh"] < c["slack_mwh"] - 1e-9 else "STOP",
    }
    # --- G-MAG: slack must reach 0.0 and both VOLL hours must clear -----------
    cleared = all(a["slack_at_voll"][h] <= 1e-6 for h in VOLL_HOURS)
    out["gates"]["G-MAG"] = {
        "test": "slack -> 0.0 MWh and hours 3616/3617 clear "
        f"({RESTORED_AT_VOLL_MW:.0f} MW restored vs "
        f"{sum(c['slack_at_voll'].values()):.1f} MW shed)",
        "arm_slack_mwh": a["slack_mwh"],
        "arm_slack_at_voll": a["slack_at_voll"],
        "control_slack_at_voll": c["slack_at_voll"],
        "verdict": "PASS" if (a["slack_mwh"] <= 1e-6 and cleared) else "STOP",
    }
    # --- G-DEMAND: SERVED DEMAND identical (never generation) -----------------
    out["gates"]["G-DEMAND"] = {
        "test": "served demand identical to 4 dp; dump 0 both legs",
        "control_twh": round(c["served_twh"], 4),
        "arm_twh": round(a["served_twh"], 4),
        "control_dump": c["dump_mwh"],
        "arm_dump": a["dump_mwh"],
        "verdict": "PASS"
        if (
            round(c["served_twh"], 4) == round(a["served_twh"], 4)
            and c["dump_mwh"] <= 1e-6
            and a["dump_mwh"] <= 1e-6
        )
        else "STOP",
    }
    # --- G-CONF-2: the response is confined to the changed hours -------------
    if restored is not None:
        cc = _p1(control / "hourly" / f"class_hourly_{YEAR}.parquet")
        ac = _p1(arm / "hourly" / f"class_hourly_{YEAR}.parquet")
        m = cc.merge(ac, on=["klass", "hour"], suffixes=("_c", "_a"))
        m["d"] = (m.mw_a - m.mw_c).abs()
        outside = m[(~restored[m.hour.to_numpy()]) & (m.d > 1.0)]
        out["gates"]["G-CONF-2"] = {
            "test": "no class-hour outside the restored set moves > 1.0 MW",
            "restored_hours": int(restored.sum()),
            "violating_class_hours": int(len(outside)),
            "worst_outside_mw": float(outside.d.max()) if len(outside) else 0.0,
            "verdict": "PASS" if len(outside) == 0 else "STOP",
        }
    # --- reserve families (reported + context for G-DIR) ---------------------
    rf = {}
    for tag, p in (("control", control), ("arm", arm)):
        r = _p1(p / "hourly" / f"reserve_family_{YEAR}.parquet")
        s = r[r.shortfall_mw > 1e-6]
        rf[tag] = {
            "total_mwh": float(s.shortfall_mw.sum()),
            "hours": int(s.hour.nunique()),
            "by_family": {
                k: {"h": int(v.hour.nunique()), "mwh": round(float(v.shortfall_mw.sum()), 1)}
                for k, v in s.groupby("family")
            },
        }
    out["reported"]["reserve_shortfall"] = rf

    # --- REPORTED ONLY, never gated (rule 29 / rule 1) ----------------------
    out["reported"]["price"] = {
        "control": {k: c[k] for k in ("lw_mean", "lw_max", "h_gt")},
        "arm": {k: a[k] for k in ("lw_mean", "lw_max", "h_gt")},
        "note": "C3a/C3b/C3c are REPORTED, never gated, in either direction "
        "(rule 29 [R-SCREEN]; the price direction was declared ex ante in the "
        "phase-0 finding §6 and is DOWN).",
    }
    out["reported"]["class_twh"] = {}
    for tag, p in (("control", control), ("arm", arm)):
        cl = _p1(p / "hourly" / f"class_hourly_{YEAR}.parquet")
        out["reported"]["class_twh"][tag] = {
            k: round(float(v.mw.sum() / 1e6), 4) for k, v in cl.groupby("klass")
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument(
        "--hour-grain-csv",
        type=Path,
        default=Path("data/raw/campd-unit-outages-perunitmerithour-NYISO.csv"),
    )
    ap.add_argument(
        "--day-grain-csv",
        type=Path,
        default=Path("data/raw/campd-unit-outages-perunitmerit-NYISO.csv"),
    )
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    restored = None
    if args.hour_grain_csv.exists():
        restored = restored_hour_mask(args.hour_grain_csv, args.day_grain_csv)

    res = score(args.control, args.arm, restored)
    print(json.dumps(res, indent=2, default=str))
    stops = [k for k, v in res["gates"].items() if v["verdict"] != "PASS"]
    print(
        f"\nSCREEN VERDICT: {'STOP -> ' + ', '.join(stops) if stops else 'CLEARS every gate'}"
        f"  ({len(res['gates'])} gates scored)"
    )
    print(
        "A screen may KILL an arm; it may never PROMOTE one (rule 29 [R-SCREEN])."
    )
    if args.out:
        args.out.write_text(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
