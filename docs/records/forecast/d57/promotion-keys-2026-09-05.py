"""capx D57 promotion instrument: the cache keys every posture resolves to AFTER the PJM override.

Owner ruling 2026-09-05 (in-session, on the D57 A/B) armed the joint PJM configuration —
``pjm_accreditation_design_vintage`` + ``pjm_demand_response_supply`` +
``capacity_market_supply_clearing_by_iso[PJM]`` — through ``ISOConfig.default_scenario_overrides``
(``config/iso_configs.py::_pjm_config``), NOT by flipping the shared ScenarioConfig defaults. This
instrument prints, zero solves, what that does to the keys: the bare PJM T1-H recipe key must equal
arm A's ``f0e050e820c1159a`` (the same payload arm A hashed explicitly), the explicit all-off
control must still resolve D45-R's ``c6091bd5b62bbc3f``, every other ISO's bare key must be
unmoved, and a PJM plain-backcast config must resolve with all three fields coerced (key unmoved).

Run from the repo root: ``uv run python docs/handoffs/d57/promotion-keys-2026-09-05.py``
"""

import json
import sys

sys.path.insert(0, "src")
sys.path.insert(0, ".")
from scripts.run_capacity_hindcast import build_config  # noqa: E402
from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402

EXPECTED = {
    "pjm-t1h bare (post-override)": "f0e050e820c1159a",  # = arm A
    "pjm-t1h explicit control (all three off)": "c6091bd5b62bbc3f",  # = D45-R's bare key
    "pjm-t1h D48 fields off, clearing inherited": "ccee17a4c1563727",  # = arm B
}

out = {}
for iso in ("PJM", "MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
    cfg = build_config(iso, 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True)
    out[f"{iso.lower()}-t1h bare (post-override)"] = apply_iso_scenario_defaults(cfg, iso).cache_key()
cfg = build_config(
    "PJM",
    2021,
    2025,
    "realized",
    vintage=2020,
    entry_screen_diagnostics=True,
    pjm_accreditation_design_vintage=False,
    pjm_demand_response_supply=False,
    capacity_market_supply_clearing=False,
)
out["pjm-t1h explicit control (all three off)"] = apply_iso_scenario_defaults(cfg, "PJM").cache_key()
cfg = build_config(
    "PJM",
    2021,
    2025,
    "realized",
    vintage=2020,
    entry_screen_diagnostics=True,
    pjm_accreditation_design_vintage=False,
    pjm_demand_response_supply=False,
)
out["pjm-t1h D48 fields off, clearing inherited"] = apply_iso_scenario_defaults(cfg, "PJM").cache_key()
# A PJM plain backcast: the override is applied and then coerced by __post_init__ (replace()
# re-runs it), so the resolved config carries the three fields at their off values and the key
# is the un-resolved one.
back = ScenarioConfig(iso="PJM", mode="backcast")
res = apply_iso_scenario_defaults(back, "PJM")
out["pjm backcast: resolved fields"] = [
    res.mode,
    res.pjm_accreditation_design_vintage,
    res.pjm_demand_response_supply,
    res.capacity_market_supply_clearing_by_iso,
]
out["pjm backcast: key unmoved by the override"] = res.cache_key() == back.cache_key()
print(json.dumps(out, indent=1))
bad = {k: (v, EXPECTED[k]) for k, v in out.items() if k in EXPECTED and v != EXPECTED[k]}
print("EXPECTED keys:", "ALL MATCH" if not bad else f"MISMATCH {bad}")
