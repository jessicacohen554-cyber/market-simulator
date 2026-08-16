"""caiso-197 (lane 2) — G-ONEMECH config diff + engagement summary on the A/B.

`GATESPEC-caiso193-wefor-residual-2026-08-11.md` §4 G-ONEMECH: the A/B
``scenario_config`` diff must be EXACTLY the three-field move —
``wefor_multiplier`` 0.7→1.0, ``wefor_residual`` None→0.0,
``wefor_residual_groups`` None→{CC_REGULAR} — verified over the FULL config
of the two bundles' committed ``run_config.json``. Also records the LP
engagement summary (zone-hours with changed prices; class-hour dispatch
deltas per year) from the two bundles' hourly sidecars — model artifacts
only, no actuals, no fit statistic (the direction-hazard regime stays
intact: nothing here compares to measured prices).

Usage::

    python scripts/probes/_caiso197_l2_gates.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
CONTROL = REPO / "results" / "calibration" / "caiso197_l2_control"
ARM = REPO / "results" / "calibration" / "caiso197_l2_wefor"
YEARS = [2023, 2024, 2025]
OUT = REPO / "results" / "calibration" / "_caiso197_l2_gates.json"

EXPECTED = {
    "wefor_multiplier": (0.7, 1.0),
    "wefor_residual": (None, 0.0),
    "wefor_residual_groups": (None, ["CC_REGULAR"]),
}


def _norm(v):
    """Normalize config values for comparison (frozenset/list/tuple → sorted list)."""
    if isinstance(v, (list, tuple, set, frozenset)):
        return sorted(str(x) for x in v)
    return v


def main() -> None:
    """Diff the two committed configs; summarize LP engagement per year."""
    c = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    a = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    keys = sorted(set(c) | set(a))
    diffs = {}
    for k in keys:
        cv, av = _norm(c.get(k)), _norm(a.get(k))
        if cv != av:
            diffs[k] = {"control": cv, "arm": av}
    expected_norm = {
        k: {"control": _norm(cv), "arm": _norm(av)}
        for k, (cv, av) in EXPECTED.items()
    }
    onemech_pass = diffs == expected_norm

    engagement = {}
    for year in YEARS:
        sys_c = pq.read_table(CONTROL / "hourly" / f"system_{year}.parquet")
        sys_a = pq.read_table(ARM / "hourly" / f"system_{year}.parquet")
        pc = sys_c.column("price").to_numpy(zero_copy_only=False).astype(float)
        pa = sys_a.column("price").to_numpy(zero_copy_only=False).astype(float)
        cls_c = pq.read_table(CONTROL / "hourly" / f"class_hourly_{year}.parquet")
        cls_a = pq.read_table(ARM / "hourly" / f"class_hourly_{year}.parquet")
        mc = cls_c.column("mw").to_numpy(zero_copy_only=False).astype(float)
        ma = cls_a.column("mw").to_numpy(zero_copy_only=False).astype(float)
        engagement[year] = {
            "zone_hours_price_changed": int((pc != pa).sum()),
            "zone_hours_total": int(len(pc)),
            "max_abs_price_delta": float(np.max(np.abs(pc - pa))),
            "class_hours_mw_changed": int((mc != ma).sum()),
            "max_abs_mw_delta": float(np.max(np.abs(mc - ma))),
        }
    inert = all(
        e["zone_hours_price_changed"] == 0 and e["class_hours_mw_changed"] == 0
        for e in engagement.values()
    )

    out = {
        "control": CONTROL.name,
        "arm": ARM.name,
        "gatespec": "GATESPEC-caiso193-wefor-residual-2026-08-11.md",
        "g_onemech": {
            "expected_diff": expected_norm,
            "measured_diff": diffs,
            "pass": onemech_pass,
        },
        "engagement": engagement,
        "arm_inert": inert,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    sys.exit(0 if onemech_pass else 2)


if __name__ == "__main__":
    main()
