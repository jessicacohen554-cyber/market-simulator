"""capx D78 cache-key resolution at HEAD — zero LP.

Resolves the D78 legs' recipe keys through the harness path
(``run_capacity_hindcast.build_config`` → ``apply_iso_scenario_defaults`` →
``cache_key()``) and ATTRIBUTES the move from D58's keys (solved at
``99c75b3d``) by reverting the two capx D65-B value changes on the same
recipe — so a moved key is explained, never assumed (rule 29(b): a matched
key is not a G-DRIFT verdict, and neither is a moved one). Writes
``keys_probe.json`` beside this file.

Because D78 adds NO field (design §3.4), the repaired arm resolves to the SAME
key as D58's arm at HEAD; the semantic change under that key is recorded in
``results/cache.py`` and has zero committed bundles in its blast radius.
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

# D58's keys, resolved at its HEAD 99c75b3d (PREDECL-capx-d58 §5 / FINDING §1).
D58 = {
    "control_full": "aef81c84c4609c76",
    "arm_full": "f546407cf3489761",
    "control_screen": "e47fee08f5f37d6f",
    "arm_screen": "0265ce2b262ad37f",
}


def key(post: dict | None = None, **over) -> str:
    kw = dict(BASE)
    kw.update(over)
    cfg = build_config(**kw)
    cfg = apply_iso_scenario_defaults(cfg, kw["iso"])
    for field, value in (post or {}).items():
        setattr(cfg, field, value)
    return cfg.cache_key()


# The two capx D65-B (fb93b76e) value changes, reverted to their pre-D65-B
# values on the same recipe. If the reverted keys equal D58's, the whole move
# is D65-B's — a CCS-retrofit re-key, inert below ccs_retrofit_available_year.
PRE_D65B = {"ccs_retrofit_vom_adder": 8.0, "ccs_retrofit_fixed_cost_co2_scaling": False}


def main() -> None:
    out = {
        "head_control_full_2021_2025": key(),
        "head_arm_full_2021_2025": key(retirement_sector_gate=True),
        "head_control_screen_2021_2023": key(end_year=2023),
        "head_arm_screen_2021_2023": key(end_year=2023, retirement_sector_gate=True),
        "d58_keys_at_99c75b3d": D58,
        "reverted_d65b_control_full": key(PRE_D65B),
        "reverted_d65b_arm_full": key(PRE_D65B, retirement_sector_gate=True),
        "reverted_d65b_control_screen": key(PRE_D65B, end_year=2023),
        "reverted_d65b_arm_screen": key(
            PRE_D65B, end_year=2023, retirement_sector_gate=True
        ),
    }
    out["move_attributed_to_d65b_entirely"] = (
        out["reverted_d65b_control_full"] == D58["control_full"]
        and out["reverted_d65b_arm_full"] == D58["arm_full"]
        and out["reverted_d65b_control_screen"] == D58["control_screen"]
        and out["reverted_d65b_arm_screen"] == D58["arm_screen"]
    )
    out["arm_differs_from_control"] = (
        out["head_arm_screen_2021_2023"] != out["head_control_screen_2021_2023"]
    )
    Path(__file__).with_name("keys_probe.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
