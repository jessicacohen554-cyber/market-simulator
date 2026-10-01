#!/usr/bin/env python3
"""G-DRIFT probe (capx D67): does the PJM T1-H SCREEN SEAM PEAK reproduce at HEAD?

Zero LP. Rebuilds the screen-seam peak the way ``runner.py`` does at the top of
its year loop (``_scale_demand`` over the once-loaded weather-year base, then
``add_load_layers``) and compares it to the committed D57 arm A ledger's
``screen_peak_demand_mw``. A 0.000 MW match proves the demand path -- and with
it every SCN load-table hunk in the drift window -- INERT for this recipe by
measurement rather than by argument (rule 29 [R-SCREEN] clause (b), G-DRIFT).

**capx D76 extension (2026-09-06).** The seam reproduction this probe performs
is the same object the D76 six-ISO peak census needs, so it is factored out
here into :func:`seam_context`, :func:`seam_peak_mw` and
:func:`measured_peak_mw` and IMPORTED by ``docs/handoffs/d76/peak_census.py``
rather than copied (D76 charter: "extend, do not fork"). ``main()`` is
unchanged in behaviour -- it now calls the helpers, and its committed
``gdrift_peak_probe.json`` re-derives byte-identically.
"""

import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.iso_configs import (
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.paths import set_eia860_vintage
from market_sim.data.datacenter import add_load_layers
from market_sim.data.eia_loader import load_demand
from market_sim.model.interchange.spec import (
    apply_interchange_topology,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.runner import _get_growth_rate, _scale_demand
from scripts.run_capacity_hindcast import build_config

ARM_A = Path("results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/PJM/f0e050e820c1159a")
ISO = "PJM"
YEARS = range(2021, 2026)


class SeamContext:
    """The runner-preamble state the capacity-screen seam peak is built from.

    Holds exactly what ``runner.run_scenario`` has resolved by the time it
    reaches the top of its year loop: the ISO-defaulted config, the topology-
    extended ``iso_config`` (hence ``zone_names``), whether the ISO carries an
    interchange import node, and the ONCE-loaded weather-year demand base.
    """

    def __init__(self, iso, config, iso_config, zone_names, base, import_generators):
        self.iso = iso
        self.config = config
        self.iso_config = iso_config
        self.zone_names = zone_names
        self.base = base
        self.import_generators = import_generators


def seam_context(iso: str, config, first_year: int) -> SeamContext:
    """Reproduce ``runner.run_scenario``'s preamble for ``iso`` exactly.

    Interchange topology first (it can extend the node set), then the EIA-860
    vintage pin, then the once-loaded weather-year base -- the same order and
    the same arguments the runner uses, so the base array this returns is the
    one ``_scale_demand`` is handed in production.

    Args:
        iso: ISO code, e.g. ``"PJM"``.
        config: The ISO-defaulted :class:`ScenarioConfig` for the recipe.
        first_year: The window's first year, passed to the topology helper
            exactly as the runner passes its start year.

    Returns:
        The populated :class:`SeamContext`.
    """
    iso_config = get_iso_config(iso)
    spec = get_interchange_spec(config, iso)
    import_generators = build_interchange_fleet(spec, 0.0)
    iso_config = apply_interchange_topology(
        iso_config, spec, config, year=first_year, extend_node=bool(import_generators)
    )
    set_eia860_vintage(
        config.eia860_vintage_year
        if (config.mode == "backcast" or config.hindcast)
        else None
    )
    base = load_demand(
        iso,
        config.weather_year,
        iso_config,
        td_loss_factor=config.td_loss_factor,
        include_interchange=not import_generators,
        strict_demand_profile=config.strict_demand_profile,
        ercot_tie_zonal_interchange=config.ercot_tie_zonal_interchange,
    )
    if config.hours < base.shape[1]:
        base = base[:, : config.hours]
    return SeamContext(
        iso, config, iso_config, iso_config.zone_names, base, import_generators
    )


def seam_peak_mw(ctx: SeamContext, year: int) -> float:
    """The capacity screens' seam peak for ``year``, as ``runner.py`` builds it.

    ``_scale_demand`` over the once-loaded weather-year base, then
    ``add_load_layers``, then the system-coincident max -- ``runner.py`` lines
    2029-2031, the GROWTH path the capacity screens consume regardless of
    hindcast mode.

    Args:
        ctx: The seam context from :func:`seam_context`.
        year: The target (entering) year.

    Returns:
        The seam peak in MW.
    """
    dem = _scale_demand(ctx.base, ctx.config, year)
    dem = add_load_layers(dem, ctx.config, ctx.iso, year, ctx.zone_names)
    return float(dem.sum(axis=0).max())


def measured_peak_mw(ctx: SeamContext, year: int) -> float:
    """The MEASURED peak of ``year``, as the hindcast LP's own load branch sees it.

    The same ``load_demand`` call ``runner.py`` makes for ``year_base_demand``
    on the hindcast branch (line 2472), so this is the load the LP actually
    dispatches in that year -- the quantity the seam peak above is supposed to
    be, and in every non-weather year is not.

    Args:
        ctx: The seam context from :func:`seam_context`.
        year: The target year.

    Returns:
        The measured system-coincident peak in MW.
    """
    dem = load_demand(
        ctx.iso,
        year,
        ctx.iso_config,
        td_loss_factor=ctx.config.td_loss_factor,
        include_interchange=not ctx.import_generators,
        strict_demand_profile=ctx.config.strict_demand_profile,
        ercot_tie_zonal_interchange=ctx.config.ercot_tie_zonal_interchange,
    )
    if ctx.config.hours < dem.shape[1]:
        dem = dem[:, : ctx.config.hours]
    return float(dem.sum(axis=0).max())


def main() -> int:
    cfg = apply_iso_scenario_defaults(
        build_config(ISO, 2021, 2025, "realized", vintage=2020,
                     entry_screen_diagnostics=True),
        ISO,
    )
    ctx = seam_context(ISO, cfg, 2021)

    print(f"weather_year={cfg.weather_year}  growth_vintage={cfg.demand_growth_vintage}")
    print("growth rates read: " +
          ", ".join(f"{y}:{_get_growth_rate(cfg, y):.6f}" for y in range(2021, 2026)))
    print()
    hdr = f"{'year':>6} {'screen peak @HEAD':>19} {'arm A committed':>17} {'delta MW':>12}"
    print(hdr); print("-" * len(hdr))
    out, worst = {}, 0.0
    for year in YEARS:
        peak = seam_peak_mw(ctx, year)
        committed = json.loads((ARM_A / f"evolution_{year}.json").read_text())
        ref = float(committed["screen_peak_demand_mw"])
        delta = peak - ref
        worst = max(worst, abs(delta))
        out[year] = {"head": peak, "arm_a": ref, "delta": delta}
        print(f"{year:>6} {peak:>19.3f} {ref:>17.3f} {delta:>12.3f}")
    print()
    verdict = "INERT (0.000 MW)" if worst < 5e-4 else f"LIVE (max |delta| {worst:.3f} MW)"
    print(f"VERDICT: demand path @HEAD vs D57 arm A -> {verdict}")
    Path("docs/handoffs/d67/gdrift_peak_probe.json").write_text(
        json.dumps({"iso": ISO, "years": out, "max_abs_delta_mw": worst,
                    "verdict": verdict}, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
