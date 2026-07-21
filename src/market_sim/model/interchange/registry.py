"""ISO -> interchange-injection registry and the shared injection sequence.

``apply_interchange_injections`` is the single post-assembly injection
sequence BOTH orchestrators run (forecast ``runner.py`` and backcast
``scripts/run_calibration.py``). Session 3F re-seats its per-ISO steps as a
registry (:data:`INTERCHANGE_INJECTIONS`) mapping each ISO to the exact
ordered step functions the monolith ran for it — the repo's per-ISO-registry
convention instead of an ``iso == ...`` ladder. Each step is the verbatim
monolith block (every gate check preserved inside the step), so the injected
LP is byte-identical; there is NO generic fallback entry — an ISO absent
from the registry runs no pre-overlay injections (rule 25: per-ISO behaviour
never merges into a generic default).
"""

import logging

import numpy as np

from market_sim.model.interchange.caiso import (
    apply_caiso_seam_injections,
    inject_caiso_import_gas_coupling,
    inject_caiso_import_solar_shape,
)
from market_sim.model.interchange.import_nodes import (
    apply_reference_price_seam_injections,
)
from market_sim.model.interchange.miso import apply_miso_firm_import_injections
from market_sim.model.interchange.nyiso import apply_nyiso_firm_import_injections

_logger = logging.getLogger(__name__)

# ISO -> ordered pre-overlay injection steps: EXACTLY the sequence the
# pre-split monolith executed for that ISO (steps 1-3; every config gate and
# ISO check lives inside the step functions, so behaviour is byte-identical).
# The shared generic seam step self-gates on INTERFACE_NEIGHBORS membership
# (CAISO/MISO/PJM today), so entries for ISOs without a seam registry are
# no-ops by construction. NO generic fallback: an ISO absent here runs no
# pre-overlay injections at all (rule 25 — per-ISO steps never collapse into
# a tuned generic default; ERCOT's interchange rides in its demand series).
INTERCHANGE_INJECTIONS: dict[str, tuple] = {
    "CAISO": (apply_caiso_seam_injections,),
    "ERCOT": (apply_reference_price_seam_injections,),
    "MISO": (
        apply_reference_price_seam_injections,
        apply_miso_firm_import_injections,
    ),
    "NEISO": (apply_reference_price_seam_injections,),
    "NYISO": (
        apply_reference_price_seam_injections,
        apply_nyiso_firm_import_injections,
    ),
    "PJM": (apply_reference_price_seam_injections,),
}


def apply_interchange_injections(
    fleet_arrays,
    mc: np.ndarray,
    config,
    iso: str,
    year: int,
    *,
    carbon_price: float = 0.0,
    gas_scenario: str = "mid",
    net_load: np.ndarray | None = None,
    measured_overlay=None,
) -> None:
    """Apply the forward-native interchange price/limit injections.

    The single post-assembly injection sequence BOTH orchestrators run
    (forecast ``runner.py`` and backcast ``scripts/run_calibration.py``), so a
    forward-native seam mechanism is reachable from both paths by construction
    (orchestrator-unification plan §2.2/§3.2). Every injection is gated by its
    existing ``ScenarioConfig`` field — all default off — and each underlying
    injector self-no-ops when its rows/data are absent, so a run without the
    gate (or without a priced node) is byte-identical.

    Order (replicating the backcast orchestrator's long-standing sequence):

    1. Generic reference-price seam (non-CAISO): hourly gas × heat-rate ×
       load-shape seam prices (:func:`inject_reference_price_mc`, with the
       MISO ``miso_pjm_border_anchor`` re-anchor when set), the firm
       scheduled-export floor (:func:`inject_reference_price_firm_export`),
       and the ``miso_firm_import_floor`` mirror.
    2. CAISO dedicated seams (mutually exclusive, the spec ladder):
       ``caiso_reference_price_seam`` (both corridor legs priced forward, CARB
       border carbon on the import leg) or the per-hub FORWARD reference
       prices (``caiso_intertie_reference_price``). The per-hub/bidir
       *measured-hub* pricing is a backcast overlay and lives in
       ``measured_overlay``, never here.
    3. Firm import floors: Manitoba (``miso_firm_imports``) and NYISO
       HQ/Ontario (``nyiso_firm_imports``) must-flow baseloads.
    4. ``measured_overlay(fleet_arrays, mc)`` — the caller-supplied backcast
       measured-price block (measured hub LMP overwrites). The forecast
       runner passes ``None``. It sits exactly here because the measured hub
       overwrites must land on the forward base prices (the MISO PJM-LMP
       overwrite replaces seam rows step 1 priced) and before the offer
       couplings below (which shift/blend whatever base price is active).
    5. Offer couplings (CAISO, skipped under the bidir tie whose injector owns
       both legs): commodity-gas coupling of the desert-SW blocks
       (:func:`inject_caiso_import_gas_coupling`) and the net-load-keyed
       solar-shape collapse (:func:`inject_caiso_import_solar_shape`).

    Args:
        fleet_arrays: Vectorized fleet (modified in place — floors/bounds).
        mc: Base marginal-cost matrix (modified in place).
        config: Scenario config carrying the gates.
        iso: ISO identifier.
        year: Solve year.
        carbon_price: Resolved carbon price ($/t) for the CARB border adder.
        gas_scenario: Gas price path for the reference-price formula.
        net_load: Hourly LP-served net load (demand − must-run − VRE), only
            required when ``caiso_import_solar_shape`` is on.
        measured_overlay: Optional callable ``(fleet_arrays, mc) -> None``
            holding the backcast-only measured-price overlays.

    ``config.neighbor_hr_forward_skill`` (default ``None``) is read here and
    threaded into every :func:`inject_reference_price_mc` call as
    ``forward_skill`` — see that field's docstring.

    Raises:
        ValueError: ``caiso_import_solar_shape`` is on but ``net_load`` was
            not supplied.
    """
    for _step in INTERCHANGE_INJECTIONS.get(iso, ()):
        _step(
            fleet_arrays,
            mc,
            config,
            iso,
            year,
            carbon_price=carbon_price,
            gas_scenario=gas_scenario,
            forward_skill=getattr(config, "neighbor_hr_forward_skill", None),
        )

    # --- 4. Backcast measured-price overlays (caller-supplied; forecast
    #     passes None). Must land after the forward base prices and before
    #     the couplings below. ---
    if measured_overlay is not None:
        measured_overlay(fleet_arrays, mc)

    bidir_intertie = getattr(config, "caiso_bidir_intertie", False) and iso == "CAISO"
    # --- 5. CAISO offer couplings (skipped under the bidir tie, whose
    #     injector prices both legs itself). ---
    if not bidir_intertie and getattr(config, "caiso_import_gas_coupling", False):
        if inject_caiso_import_gas_coupling(fleet_arrays, mc, config, year):
            _logger.info(
                "%s %d: desert-SW gas import tranches (DSW_CCGT/DSW_CT) coupled "
                "to the measured commodity-gas delta (tracks --gas-hub-basis-overlay)",
                iso,
                year,
            )
    if not bidir_intertie and getattr(config, "caiso_import_solar_shape", False):
        if net_load is None:
            raise ValueError(
                "caiso_import_solar_shape is on but the orchestrator did not "
                "supply net_load to apply_interchange_injections"
            )
        if inject_caiso_import_solar_shape(fleet_arrays, mc, config, net_load):
            _logger.info(
                "%s %d: desert-SW solar import (DSW_solar_PV) offer collapsed "
                "toward the negative keep-running floor in the net-load belly "
                "(negative midday tail)",
                iso,
                year,
            )
