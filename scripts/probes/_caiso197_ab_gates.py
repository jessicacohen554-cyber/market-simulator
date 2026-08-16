"""caiso-197 — generic A/B gate probe: G-ONEMECH config diff + LP engagement.

Generalizes `_caiso197_l2_gates.py` for the campaign's remaining arms (lane 3,
lane 5, Wave-2 rungs): verifies the two bundles' committed ``run_config.json``
``scenario_config`` diff is EXACTLY the expected field moves — nothing else —
and summarizes LP engagement (zone-hours with changed prices, class-hour
dispatch deltas) from the hourly sidecars. Model artifacts only; no actuals,
no fit statistic (the campaign direction-hazard regime stays intact).

Usage::

    python scripts/probes/_caiso197_ab_gates.py <control-bundle> <arm-bundle> \
        <out-record.json> '<expected-diff-json>'

where ``<expected-diff-json>`` maps field -> [control_value, arm_value], e.g.
``'{"gas_st_wefor_base_override": [null, 0.1591]}'``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
YEARS = [2023, 2024, 2025]


def _norm(v):
    """Normalize config values (set-likes → sorted str lists) for comparison."""
    if isinstance(v, (list, tuple, set, frozenset)):
        return sorted(str(x) for x in v)
    return v


def main() -> None:
    """Diff the configs against the expected moves; summarize engagement."""
    control, arm, out_path, expected_raw = sys.argv[1:5]
    control, arm = Path(control), Path(arm)
    expected = {
        k: {"control": _norm(cv), "arm": _norm(av)}
        for k, (cv, av) in json.loads(expected_raw).items()
    }

    c = json.loads((control / "run_config.json").read_text())["scenario_config"]
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    diffs = {}
    for k in sorted(set(c) | set(a)):
        cv, av = _norm(c.get(k)), _norm(a.get(k))
        if cv != av:
            diffs[k] = {"control": cv, "arm": av}
    onemech_pass = diffs == expected

    engagement = {}
    for year in YEARS:
        pc = (
            pq.read_table(control / "hourly" / f"system_{year}.parquet")
            .column("price").to_numpy(zero_copy_only=False).astype(float)
        )
        pa = (
            pq.read_table(arm / "hourly" / f"system_{year}.parquet")
            .column("price").to_numpy(zero_copy_only=False).astype(float)
        )
        mc = (
            pq.read_table(control / "hourly" / f"class_hourly_{year}.parquet")
            .column("mw").to_numpy(zero_copy_only=False).astype(float)
        )
        ma = (
            pq.read_table(arm / "hourly" / f"class_hourly_{year}.parquet")
            .column("mw").to_numpy(zero_copy_only=False).astype(float)
        )
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
        "control": control.name,
        "arm": arm.name,
        "g_onemech": {
            "expected_diff": expected,
            "measured_diff": diffs,
            "pass": onemech_pass,
        },
        "engagement": engagement,
        "arm_inert": inert,
    }
    Path(out_path).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {out_path}")
    sys.exit(0 if onemech_pass else 2)


if __name__ == "__main__":
    main()
