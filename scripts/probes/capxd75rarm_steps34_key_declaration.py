#!/usr/bin/env python3
"""capx D75-R-ARM steps 3-4 — THE KEY DECLARATION probe.

The charter's r#54 amendment makes one question load-bearing before any LP is
spent: **which cache key does the bare ``pjm-t1h`` recipe carry at THIS head?**
Three vintages were in play when the charter was re-emitted --
``a9c66d8ea25acb9d`` (the D67-ARM / Q52 posture, which is what the committed
``pjm-t1h`` row still is), ``b518f5fe7d02f961`` (D75-R-ARM / Q55, this lane's
own arm) and ``fb16fda2ddb0a94a`` (D78-ARM / Q56) -- and the charter forbids
assuming which one applies.

This probe answers it by MEASUREMENT, through the shipped harness path the
``TestQ52ArmingKeys`` override pin uses and nothing else::

    build_config(iso, 2021, 2025, "realized", vintage=2020,
                 entry_screen_diagnostics=True, **explicit_flags)
      -> apply_iso_scenario_defaults(cfg, iso)
        -> cfg.cache_key()

Overrides are passed **through ``build_config``**, i.e. as explicit CLI-caller
arguments, because that is the only path ``apply_iso_scenario_defaults`` honours
(the OVERRIDE-FIX explicit-caller rule): setting the attribute on an already
built config and applying the ISO defaults afterwards silently re-arms it, and
every control leg then collapses onto the bare key. That failure mode was hit
and corrected while writing this probe; the shape here is the correct one.

It reports, at zero LP cost:

* the bare row's key -- **the answer**;
* every (b'-1) inverse leg, so each pre-arm posture is shown still reachable
  and still identified;
* the four D57/D67 control legs, whose movement is pre-declared rather than
  discovered (``PRECOMMIT-capx-d75r-arm-2026-09-06.md`` §2.1, itself written
  against the miss ``FINDING-capx-d67arm-2026-09-06.md`` §2.1 recorded);
* the five non-PJM bare keys, which must be byte-identical to the PRECOMMIT's
  pre-arm literals (rule 25 ``[R-ISO-SCOPE]``);
* the resolved PJM forecast posture, field by field.

Usage::

    uv run python scripts/probes/capxd75rarm_steps34_key_declaration.py \
        --out docs/handoffs/d75rarm/steps34-keys.json
"""

import json
import subprocess
import sys
from pathlib import Path

_REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "src"))

from scripts.run_capacity_hindcast import build_config  # noqa: E402
from market_sim.config.iso_configs import apply_iso_scenario_defaults  # noqa: E402

HEAD = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=_REPO).decode().strip()


def key(iso, **over):
    cfg = build_config(
        iso, 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True, **over
    )
    return apply_iso_scenario_defaults(cfg, iso).cache_key()


novre = dict(pjm_vre_accreditation_vintage=False)
nogate = dict(retirement_sector_gate=False)
off3 = dict(
    pjm_accreditation_design_vintage=False,
    pjm_demand_response_supply=False,
    capacity_market_supply_clearing=False,
)
off2 = dict(pjm_accreditation_design_vintage=False, pjm_demand_response_supply=False)

rows = {
    "bare pjm-t1h (THE ROW)": key("PJM"),
    "bare + --no-retirement-sector-gate": key("PJM", **nogate),
    "bare + --no-pjm-vre-accreditation-vintage": key("PJM", **novre),
    "bare + both --no-": key("PJM", **novre, **nogate),
    "D57 off3 (D67+Q55+Q56 on)": key("PJM", **off3),
    "D57 off3 + nogate": key("PJM", **off3, **nogate),
    "D57 off3 + novre + nogate": key("PJM", **off3, **novre, **nogate),
    "D57 off3 + nogate + no-req-pub": key(
        "PJM", **off3, **nogate, capacity_adequacy_requirement_published=False
    ),
    "D57 off2 (arm B)": key("PJM", **off2),
    "D57 off2 + nogate": key("PJM", **off2, **nogate),
    "D57 off2 + novre + nogate": key("PJM", **off2, **novre, **nogate),
    "D57 off2 + nogate + no-req-pub": key(
        "PJM", **off2, **nogate, capacity_adequacy_requirement_published=False
    ),
}
for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
    rows[f"{iso} bare"] = key(iso)

cfg = apply_iso_scenario_defaults(
    build_config(
        "PJM", 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True
    ),
    "PJM",
)
posture = {
    f: getattr(cfg, f, "<absent>")
    for f in (
        "pjm_accreditation_design_vintage",
        "pjm_demand_response_supply",
        "capacity_market_supply_clearing_by_iso",
        "capacity_adequacy_requirement_published_by_iso",
        "pjm_vre_accreditation_vintage",
        "retirement_sector_gate",
        "fossil_announced_exits_enabled",
        "ccs_retrofit_capex_co2_scaling",
        "eia860_vintage_tracks_solve_year",
        "pjm_interface_feed_admissibility_gate",
    )
}
out = {"head": HEAD, "keys": rows, "resolved_pjm_posture": posture}
text = json.dumps(out, indent=2, default=str)
print(text)
if len(sys.argv) > 2 and sys.argv[1] == "--out":
    Path(sys.argv[2]).write_text(text + "\n")
