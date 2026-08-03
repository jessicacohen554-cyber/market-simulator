"""caiso-163 pre-solve wiring/no-op probe for ``caiso_asymmetric_path_ratings``.

No LP. Answers the two questions caiso-162 proved must be answered BEFORE a
solve is spent (``results/calibration/FINDING-caiso162-per-year-import-caps-
2026-08-03.md`` §1a/1b):

1. **Does a call site exist on the BACKCAST lane?** Replays the calibration
   lane's exact topology sequence (``pipeline.ttc.apply_iso_year_ttc`` →
   ``apply_caiso_local_import_limits`` →
   ``interchange.apply_interchange_topology``, as
   ``scripts/run_calibration.py::run_year`` runs it) for each solve year with the
   committed keeper's own ``ScenarioConfig``, and resolves the result through
   ``interchange.core.build_interface_groups`` — so "the LP sees it" is shown on
   the resolved flow-column groups, not inferred from a config field.
2. **Is the flag-off path a structural no-op?** This mechanism has no built-in
   zero-delta year (the published ratings are year-invariant), so the identity
   assertion below stands in for one: with the flag off,
   ``apply_caiso_asymmetric_path_limits`` must return the SAME OBJECT.

Usage:
    PYTHONPATH=.:src python scripts/probes/caiso163_wiring_probe.py
"""

from __future__ import annotations

import dataclasses
import json
import sys

sys.path.insert(0, ".")
sys.path.insert(0, "src")

from market_sim.config.interchange_config import get_interchange_spec  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.interchange import apply_interchange_topology  # noqa: E402
from market_sim.model.interchange.core import build_interface_groups  # noqa: E402
from market_sim.model.transmission import (  # noqa: E402
    apply_caiso_asymmetric_path_limits,
    apply_caiso_local_import_limits,
)
from market_sim.pipeline.ttc import apply_iso_year_ttc  # noqa: E402

# The incumbent keeper at the time of writing (2026-08-03-caiso162-per-year-import).
KEEPER = "results/calibration/caiso162_peryear_import_caps_v2/run_config.json"
_FIELDS = {f.name for f in dataclasses.fields(ScenarioConfig)}
_NS_ZONES = {"NP15", "ZP26", "SP15_rest"}


def main() -> None:
    """Run the probe and print its findings (no LP, no solve, no writes)."""
    with open(KEEPER) as fh:
        sc = json.load(fh)["scenario_config"]
    base = ScenarioConfig(**{k: v for k, v in sc.items() if k in _FIELDS})
    print(
        f"mode = {base.mode} | per_hub = {base.caiso_per_hub_intertie} "
        f"| endog_wecc = {base.caiso_endogenous_wecc_node} "
        f"| asym = {base.caiso_asymmetric_path_ratings}"
    )

    # (A) SAME-OBJECT no-op when off — the stand-in for a zero-delta year.
    cfg0 = get_iso_config("CAISO")
    same = apply_caiso_asymmetric_path_limits(cfg0, base) is cfg0
    print("A. flag-off returns SAME OBJECT:", same)

    on = base.with_overrides(caiso_asymmetric_path_ratings=True)
    out1 = apply_caiso_asymmetric_path_limits(cfg0, on)
    print("B. flag-on returns a NEW object:", out1 is not cfg0)
    for lim in out1.interface_limits:
        if lim.name.startswith("CAISO_path_directional_"):
            print(
                f"   + {lim.name}: cap={lim.cap_mw} "
                f"rev={lim.reverse_cap_mw} links={lim.links}"
            )

    # (C) The full backcast topology sequence, both arms, each solve year.
    for year in (2023, 2024, 2025):
        for label, cf in (("OFF", base), ("ON", on)):
            c = apply_iso_year_ttc(get_iso_config("CAISO"), "CAISO", year)
            if getattr(cf, "caiso_per_year_import_caps", False):
                c = apply_caiso_local_import_limits(c, "CAISO", year)
            spec = get_interchange_spec(cf, "CAISO", year=year)
            c = apply_interchange_topology(c, spec, cf, year=year, extend_node=True)
            dirs = [
                lim
                for lim in c.interface_limits
                if lim.name.startswith("CAISO_path_directional_")
            ]
            ns_links = [
                (ln.from_zone, ln.to_zone, ln.ttc_mw)
                for ln in c.links
                if ln.from_zone in _NS_ZONES and ln.to_zone in _NS_ZONES
            ]
            groups = build_interface_groups(c.links, c.interface_limits)
            live = sum(
                1
                for lim, g in zip(c.interface_limits, groups)
                if lim.name.startswith("CAISO_path_directional_") and len(g[0]) > 0
            )
            print(
                f"{year} {label}: internal N-S links={ns_links} "
                f"| directional limits={len(dirs)} | resolved-to-LP-groups={live}"
            )
            for lim in dirs:
                print(f"      {lim.name} cap={lim.cap_mw} rev={lim.reverse_cap_mw}")


if __name__ == "__main__":
    main()
