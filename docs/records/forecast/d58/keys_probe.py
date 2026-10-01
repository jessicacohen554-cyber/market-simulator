"""capx D58 cache-key resolution at HEAD — zero LP.

Resolves the D58 arm and same-HEAD control recipe keys through the harness path
(``run_capacity_hindcast.build_config`` → ``apply_iso_scenario_defaults`` →
``cache_key()``), and re-resolves the two known-answer anchors so a moved key is
attributed rather than assumed. Writes ``keys_probe.json`` beside this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))

from run_capacity_hindcast import build_config  # noqa: E402

from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402

BASE = dict(
    iso="PJM",
    start_year=2021,
    end_year=2025,
    variant="realized",
    vintage=2020,
    entry_screen_diagnostics=True,
)


def key(**over) -> str:
    kw = dict(BASE)
    kw.update(over)
    cfg = build_config(**kw)
    cfg = apply_iso_scenario_defaults(cfg, kw["iso"])
    for field, value in (over.get("_post") or {}).items():
        setattr(cfg, field, value)
    return cfg.cache_key()


def main() -> None:
    out = {
        "control_bare_pjm_t1h_at_head": key(),
        "arm_sector_gate_at_head": key(retirement_sector_gate=True),
        "screen_span_control_2021_2023": key(end_year=2023),
        "screen_span_arm_2021_2023": key(end_year=2023, retirement_sector_gate=True),
        # Known-answer anchors: what the committed records were solved under.
        "anchor_d57_armA_committed": "f0e050e820c1159a",
        "anchor_d67_measured_alloff_control": "7297dcb3b92be3fb",
        "anchor_d45r_committed": "c6091bd5b62bbc3f",
    }
    out["arm_differs_from_control"] = (
        out["arm_sector_gate_at_head"] != out["control_bare_pjm_t1h_at_head"]
    )
    out["control_matches_d57_armA"] = (
        out["control_bare_pjm_t1h_at_head"] == out["anchor_d57_armA_committed"]
    )
    Path(__file__).with_name("keys_probe.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
