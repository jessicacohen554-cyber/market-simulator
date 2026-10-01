"""NYISO-NEXT-26 gates G-2 / G-3 / G-5 / G-6 (zero LP), each arm vs its control's committed bundles.

Pre-registered in ``docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md`` sec. 3:

* G-2 live: ``NYC>Long_Island`` limit_up == 940 every hour, flow <= 940 + 1e-3, and the
  control's hours above 940 are >= 900 (read from the full legs' ``hourly/network``);
* G-3: per year/zone P1 demand within 0.1 GWh of the control's; load slack <= control + 1 GWh;
* G-5: no D-4 FAIL row keyed (year, check, floor, plant) absent from the control AND carrying
  >= 5 GWh; new FAIL rows under 5 GWh are listed, not blocking;
* G-6: |LI fossil - CAMPD gross| shrinks vs the control, and the LI net AC import moves toward
  the measured implied import (``nyisonext26_li_gap.measured_balance``).

G-1 is ``nyisonext26_compose_span.py --check-only``; G-4 is the scorer's C6 / C8.
Arm A's control is the NEXT-21 keeper; arm B's is NEXT-25 arm A (PR #6987's branch).

Usage: python3 scripts/probes/nyisonext26_gates.py --arm A|B --arm-legs <dir> --control-legs <dir> [--out <json>]
(each legs dir holds ``<year>/unit_hourly_<year>.parquet`` and ``<year>/network_<year>.parquet``)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))
from nyisonext26_li_gap import measured_balance, model_balance  # noqa: E402

CAL = REPO / "results" / "calibration"
D4_MIN_GWH = 5.0  # PRECOMMIT sec. 3 G-5, fixed ex ante
TSL = 940.0


def _names(prefix: str) -> dict[int, str]:
    return {2021: f"{prefix}_2021", **{y: f"{prefix}_span" for y in range(2022, 2026)}}


ARMS = {
    "A": (_names("nyisonext26"), _names("nyisonext21")),
    "B": (_names("nyisonext26p"), _names("nyisonext25")),
}


def _sys(b: str, y: int) -> pd.DataFrame:
    """P1 system frame (committed hourly sidecar)."""
    s = pd.read_parquet(CAL / b / "hourly" / f"system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _d4_fail(b: str, y: int) -> dict:
    """D-4 FAIL rows for ``y`` keyed (year, check, floor, plant) -> GWh floored."""
    ld = json.loads((CAL / b / "legitimacy_diagnostics.json").read_text())
    out = {}
    for r in ld["diagnostics"].get("D4", {}).get("rows", []):
        if r.get("year") == y and str(r.get("verdict", "")).upper() == "FAIL":
            key = (r.get("year"), r.get("check"), r.get("floor"), str(r.get("plant")))
            t = r.get("floored_twh")
            out[key] = round(1e3 * float(t), 3) if t not in ("", None) else None
    return out


def _link(leg: Path, y: int) -> pd.DataFrame:
    n = pd.read_parquet(leg / f"network_{y}.parquet")
    return n[n.name == "NYC>Long_Island"].sort_values("hour")


def main() -> None:
    """Print (and optionally write) the gate table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
    ap.add_argument("--arm-legs", type=Path, required=True)
    ap.add_argument("--control-legs", type=Path, required=True)
    ap.add_argument("--out")
    a = ap.parse_args()
    arm, ctl = ARMS[a.arm]
    out: dict = {"arm": a.arm, "control": ctl}
    for y in range(2021, 2026):
        s, k = _sys(arm[y], y), _sys(ctl[y], y)
        dem = (s.groupby("zone").demand.sum() - k.groupby("zone").demand.sum()).abs().max() / 1e3  # fmt: skip
        sl = (s.slack.sum() - k.slack.sum()) / 1e3
        fa, fk = _d4_fail(arm[y], y), _d4_fail(ctl[y], y)
        new = {str(key): g for key, g in fa.items() if key not in fk}
        blocking = {key: g for key, g in new.items() if g is None or g >= D4_MIN_GWH}
        la, lk = _link(a.arm_legs / str(y), y), _link(a.control_legs / str(y), y)
        g2 = {
            "limit_up_min": round(float(la.limit_up.min()), 3),
            "limit_up_max": round(float(la.limit_up.max()), 3),
            "flow_max": round(float(la.mw.max()), 3),
            "control_hours_gt_940": int((lk.mw.to_numpy() > TSL + 1e-3).sum()),
        }
        g2["pass"] = bool(
            abs(g2["limit_up_min"] - TSL) < 1e-6
            and abs(g2["limit_up_max"] - TSL) < 1e-6
            and g2["flow_max"] <= TSL + 1e-3
            and g2["control_hours_gt_940"] >= 900
        )
        ma, mk = (
            model_balance(y, a.arm_legs / str(y)),
            model_balance(y, a.control_legs / str(y)),
        )
        x = measured_balance(y, sorted(set(ma["plants"]) | set(mk["plants"])))
        meas_ac = float(np.mean(x["load"] - x["campd_gross"] - x["seams"]))
        campd = float(np.mean(x["campd_gross"]))
        g6 = {
            "li_fossil_mw_arm": round(float(ma["fossil_gen"].mean()), 1),
            "li_fossil_mw_control": round(float(mk["fossil_gen"].mean()), 1),
            "li_fossil_mw_campd_gross": round(campd, 1),
            "ac_import_mw_arm": round(float(ma["ac_import"].mean()), 1),
            "ac_import_mw_control": round(float(mk["ac_import"].mean()), 1),
            "ac_import_mw_measured_implied": round(meas_ac, 1),
        }
        g6["pass"] = bool(
            abs(g6["li_fossil_mw_arm"] - campd)
            < abs(g6["li_fossil_mw_control"] - campd)
            and abs(g6["ac_import_mw_arm"] - meas_ac)
            < abs(g6["ac_import_mw_control"] - meas_ac)
        )
        out[y] = {
            "G2": g2,
            "G3_max_zone_demand_dgwh": round(float(dem), 4),
            "G3_slack_dgwh": round(float(sl), 4),
            "G3_pass": bool(dem <= 0.1 and sl <= 1.0),
            "G5_new_d4_fail_gwh": new,
            "G5_blocking": {str(k_): v for k_, v in blocking.items()},
            "G5_pass": not blocking,
            "G6": g6,
        }
    txt = json.dumps(out, indent=1)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
