"""NYISO-NEXT-23 gates G-2 / G-3 / G-5 (zero LP), arm vs the NEXT-21 keeper's committed bundles.

Pre-registered in ``docs/records/nyiso/PRECOMMIT-nyiso-next23-z6-flow-date-2026-10-01.md`` sec. 4:
G-2 NYC P1 mean price on 2025-01-17 LOWER than the keeper's; G-3 per year/zone P1 demand
within 0.1 GWh and load slack <= keeper + 1 GWh; G-5 no D-4 FAIL row keyed (year, mechanism,
plant) absent from the keeper's. G-1 is ``nyisonext23_compose_span.py --check-only``; G-4 is
the scorer's C6 / C8. Also reports per-day NYC price deltas for the winter diagnosis.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CAL = Path(__file__).resolve().parents[2] / "results" / "calibration"
ARM = {2021: "nyisonext23_2021", **{y: "nyisonext23_span" for y in range(2022, 2026)}}
KEEP = {2021: "nyisonext21_2021", **{y: "nyisonext21_span" for y in range(2022, 2026)}}


def _sys(b: str, y: int) -> pd.DataFrame:
    """Keeper-comparable P1 system frame (committed hourly sidecar)."""
    s = pd.read_parquet(CAL / b / "hourly" / f"system_{y}.parquet")
    return s[s["pass"] == "P1"]


def _d4_fail(b: str, y: int) -> set:
    """D-4 FAIL rows for year ``y`` keyed (year, mechanism, plant)."""
    ld = json.loads((CAL / b / "legitimacy_diagnostics.json").read_text())
    rows = ld["diagnostics"].get("D4", {}).get("rows", [])
    return {
        (r.get("year"), r.get("mechanism"), r.get("plant") or r.get("plant_code"))
        for r in rows
        if r.get("year") == y
        and str(r.get("status", r.get("verdict", ""))).upper() == "FAIL"
    }


def main() -> None:
    """Print the gate table as JSON."""
    out: dict = {}
    for y in range(2021, 2026):
        a, k = _sys(ARM[y], y), _sys(KEEP[y], y)
        dem = (
            a.groupby("zone").demand.sum() - k.groupby("zone").demand.sum()
        ).abs().max() / 1e3
        sl = (a.slack.sum() - k.slack.sum()) / 1e3
        new_d4 = sorted(map(str, _d4_fail(ARM[y], y) - _d4_fail(KEEP[y], y)))
        rec = {
            "G3_max_zone_demand_dgwh": round(float(dem), 4),
            "G3_slack_dgwh": round(float(sl), 4),
            "G3_pass": bool(dem <= 0.1 and sl <= 1.0),
            "G5_new_d4_fail": new_d4,
            "G5_pass": not new_d4,
        }
        if y == 2025:
            h = slice(16 * 24, 17 * 24)
            pa = a[a.zone == "NYC"].sort_values("hour").price.to_numpy()[h].mean()
            pk = k[k.zone == "NYC"].sort_values("hour").price.to_numpy()[h].mean()
            rec.update(
                {
                    "G2_nyc_20250117_arm": round(float(pa), 2),
                    "G2_nyc_20250117_keeper": round(float(pk), 2),
                    "G2_pass": bool(pa < pk),
                }
            )
        out[y] = rec
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
