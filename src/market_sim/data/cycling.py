"""Thermal cycling cost adders for the marginal-cost array.

Coal and gas units that ramp, start and stop incur real costs beyond their
fuel and VOM: thermal fatigue, startup fuel and auxiliary power, and the
opportunity cost of running at minimum load. :func:`apply_cycling_adders`
folds a per-bin ``$/MWh`` adder into the dispatch marginal-cost array so the
merit order reflects those cycling costs.

Source: NREL/SR-5500-55433 (Kumar et al. 2012) "Power Plant Cycling Costs".
Per-bin adders are derived in :mod:`market_sim.config.scenarios` from
startup cost, cycle length and minimum-run drag; plant profiles come from
EPA eGRID 2023.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator


def _match_bin(unit_id: str, bin_map: dict[str, float], default: float) -> float:
    """Return the cycling adder whose bin name appears in ``unit_id``.

    Aggregated representative units carry their efficiency bin in the
    ``unit_id`` (e.g. ``gas_cc_h_class_North``). Units without a standard
    bin name — pass-through units keyed ``plantid_generatorid`` — match no
    key and fall back to ``default``.
    """
    for key, value in bin_map.items():
        if key in unit_id:
            return value
    return default


def apply_cycling_adders(
    mc: np.ndarray,
    generators: list[Generator],
    fleet: FleetArrays,
    config: ScenarioConfig,
) -> np.ndarray:
    """Add bin-specific cycling cost adders to the marginal cost array.

    Matches each generator's fuel type and efficiency bin to the
    corresponding cycling adder from ``config`` and adds it to that
    generator's ``$/MWh`` marginal cost in every hour. Pass-through units
    (individual nuclear units, units carrying a ``retirement_year``) that do
    not carry a standard bin name in their ``unit_id`` get the ``older``
    adder for their fuel type. Renewables, nuclear, hydro and imports get no
    adder.

    Args:
        mc: The ``(n_gen, T)`` marginal-cost array from
            :func:`~market_sim.data.fleet.assemble_mc`.
        generators: The generator list aligned row-for-row with ``mc``.
        fleet: The vectorized fleet ``mc`` was assembled from.
        config: Scenario configuration supplying the nine cycling adders.

    Returns:
        A new ``(n_gen, T)`` marginal-cost array with the adders applied.

    Source: NREL/SR-5500-55433, EPA eGRID 2023 plant profiles.
    """
    mc = mc.copy()

    cc_map = {
        "h_class": config.cc_cycling_adder_h_class,
        "f_class": config.cc_cycling_adder_f_class,
    }
    coal_map = {
        "supercritical": config.coal_cycling_adder_supercritical,
        "subcritical": config.coal_cycling_adder_subcritical,
    }
    ct_map = {
        "aero": config.ct_cycling_adder_aero,
        "frame": config.ct_cycling_adder_frame,
    }

    for i, g in enumerate(generators):
        adder = 0.0
        if g.fuel_type == "gas_cc":
            adder = _match_bin(g.unit_id, cc_map, config.cc_cycling_adder_older)
        elif g.fuel_type == "coal":
            adder = _match_bin(
                g.unit_id, coal_map, config.coal_cycling_adder_older
            )
        elif g.fuel_type == "gas_ct":
            adder = _match_bin(g.unit_id, ct_map, config.ct_cycling_adder_older)
        if adder > 0.0:
            mc[i] += adder
    return mc
