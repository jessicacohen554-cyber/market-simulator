#!/usr/bin/env python3
"""miso-297: write the declared arm ``offer_curve_by_group`` table from the keeper's.

The owner-authorized channel (CLAUDE.md rule 1 (a)-(e)): ONE multiplier ``m``,
identified ex ante by the IMM marginal-share census
(``_miso297_joint_census.py`` -> ``results/phase0/miso/_miso297_joint_census.json``
``_pooled.joint.m_star``), applied to the four coal subclasses' ``econ_low`` and
``econ_high`` band multipliers. ``committed`` and ``peak`` (and every non-coal
class, ``phys_*``, ``econ_low_share``) are byte-identical to the keeper's table.

Usage::

    uv run python scripts/probes/_miso297_arm_table.py --m 0.NN \\
        [--out docs/records/miso/miso297-arm-offer-curve-by-group.json]

Prints the eight moved cells and the sorted-JSON sha256 of both tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/miso280_span"
OUT = REPO / "docs/records/miso/miso297-arm-offer-curve-by-group.json"
COAL = ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB", "COAL_WC")
BANDS = ("econ_low", "econ_high")


def _sha(table: dict) -> str:
    return hashlib.sha256(
        json.dumps(table, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:16]


def build(m: float) -> tuple[dict, dict]:
    """Return ``(keeper_table, arm_table)``."""
    rc = json.loads((KEEPER / "run_config_2020.json").read_text())
    keeper = rc["scenario_config"]["offer_curve_by_group"]
    arm = json.loads(json.dumps(keeper))
    for g in COAL:
        for b in BANDS:
            arm[g][b] = round(float(keeper[g][b]) * m, 4)
    moved = [
        (g, b, keeper[g][b], arm[g][b])
        for g in keeper
        for b in keeper[g]
        if keeper[g][b] != arm[g][b]
    ]
    assert len(moved) == len(COAL) * len(BANDS), moved
    assert all(g in COAL and b in BANDS for g, b, _, _ in moved), moved
    for g, b, kv, av in moved:
        assert abs(av - kv * m) < 5e-5, (g, b, kv, av, m)
    return keeper, arm


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--m", type=float, required=True)
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    keeper, arm = build(args.m)
    Path(args.out).write_text(json.dumps(arm, indent=1, sort_keys=True) + "\n")
    print(f"m = {args.m}")
    for g in COAL:
        print(
            f"  {g:13s} committed {keeper[g]['committed']} (held) | "
            f"econ_low {keeper[g]['econ_low']} -> {arm[g]['econ_low']} | "
            f"econ_high {keeper[g]['econ_high']} -> {arm[g]['econ_high']} | "
            f"peak {keeper[g]['peak']} (held)"
        )
    print(f"keeper table sha256 {_sha(keeper)}  arm table sha256 {_sha(arm)}")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
