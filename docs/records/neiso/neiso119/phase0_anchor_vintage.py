"""neiso-119 phase 0, zero LP: NEISO's solve-year gas-offer-margin anchors.

Evaluates the frozen derive's own formula (mean of ``_gas_series``) on each solve
year, from each year's RECORDED keeper config (post gas-posture resolution), exactly
as ``run_calibration_full.mirror_solve_year_gas_anchors`` does when
``gas_offer_margin_anchor_vintage`` is armed. Also reports the delivered-gas mean the
fleet actually pays (fleet_only not needed: the recorded anchor path is what arms).
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
B = REPO / "results/calibration/neiso118_span"


def main() -> None:
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.trajectories import _gas_series

    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    out = {}
    for y in range(2019, 2026):
        sc = json.loads((B / f"run_config_{y}.json").read_text())["scenario_config"]
        cfg = ScenarioConfig(**{k: v for k, v in sc.items() if k in names})
        a = float(np.asarray(_gas_series(cfg, y, 8760), float).mean())
        out[y] = {
            "frozen_anchor": cfg.gas_offer_margin_anchor,
            "vintage_anchor": round(a, 4),
            "delta": round(a - cfg.gas_offer_margin_anchor, 4),
        }
        print(y, out[y])
    Path(__file__).with_name("phase0_anchor_vintage.json").write_text(
        json.dumps(out, indent=1)
    )


if __name__ == "__main__":
    main()
