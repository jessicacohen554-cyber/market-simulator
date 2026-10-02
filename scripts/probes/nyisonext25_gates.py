"""NYISO-NEXT-25 gates G-2 / G-3 / G-5 (zero LP), each arm vs its control's committed bundles.

Pre-registered in ``docs/records/nyiso/PRECOMMIT-nyiso-next25-print-level-2026-10-01.md`` sec. 4:

* G-2: 2025 NYC P1 mean price over the January days on which the NYC dual-fuel cap does not
  bind (the FINDING population, ``nyisonext25_offcap_winter_gap.cap_binding_days``) is HIGHER
  than the control's;
* G-3: per year/zone P1 demand within 0.1 GWh of the control's; load slack <= control + 1 GWh;
* G-5: no D-4 FAIL row keyed (year, check, floor, plant) absent from the control AND carrying
  >= 5 GWh; new FAIL rows under 5 GWh are listed, not blocking.

G-1 is ``nyisonext25_compose_span.py --check-only``; G-4 is the scorer's C6 / C8.
Arm A's control is the NEXT-21 keeper; arm B's is the NEXT-23 arm (PR #6984's branch).

Usage: python3 scripts/probes/nyisonext25_gates.py --arm A|B [--out <json>]
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
CAL = REPO / "results" / "calibration"
D4_MIN_GWH = 5.0  # PRECOMMIT sec. 4 G-5, fixed ex ante


def _names(prefix: str) -> dict[int, str]:
    return {2021: f"{prefix}_2021", **{y: f"{prefix}_span" for y in range(2022, 2026)}}


ARMS = {
    "A": (_names("nyisonext25"), _names("nyisonext21")),
    "B": (_names("nyisonext25f"), _names("nyisonext23")),
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


def main() -> None:
    """Print (and optionally write) the gate table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(ARMS), required=True)
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
        rec = {
            "G3_max_zone_demand_dgwh": round(float(dem), 4),
            "G3_slack_dgwh": round(float(sl), 4),
            "G3_pass": bool(dem <= 0.1 and sl <= 1.0),
            "G5_new_d4_fail_gwh": new,
            "G5_blocking": blocking,
            "G5_pass": not blocking,
        }
        if y == 2025:
            from scripts.probes.nyisonext25_offcap_winter_gap import cap_binding_days

            bind = cap_binding_days(2025)
            jan = [d for d in range(31) if d not in bind]
            hours = np.concatenate([np.arange(24 * d, 24 * d + 24) for d in jan])
            pa = s[s.zone == "NYC"].sort_values("hour").price.to_numpy()[hours].mean()
            pk = k[k.zone == "NYC"].sort_values("hour").price.to_numpy()[hours].mean()
            rec.update(
                {
                    "G2_jan_offcap_days": len(jan),
                    "G2_nyc_arm": round(float(pa), 2),
                    "G2_nyc_control": round(float(pk), 2),
                    "G2_pass": bool(pa > pk),
                }
            )
        out[y] = rec
    txt = json.dumps(out, indent=1)
    if a.out:
        Path(a.out).write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
