"""Facade re-export tests for the 3F ``transmission`` → ``model/interchange`` split.

Session 3F (refactor-consolidation plan §5 item 6, 2026-07-21) split
``model/transmission.py`` (5,436 ln) into the ``model/interchange/`` package
(core / import_nodes / caiso / miso / pjm / nyiso / neiso / registry, joining
the session-3E spec module), leaving a ``sys.modules``-alias facade at the
historical path (the ``model/capacity.py`` pattern).

Pinned contracts:

* **Alias identity** — ``market_sim.model.transmission`` and the
  ``market_sim.model.interchange`` package are ONE namespace object, so every
  historical import spelling and monkeypatch / attribute write keeps working.
* **Historical surface** — the frozen inventory below lists every name any
  src/scripts/tests importer has ever pulled from
  ``market_sim.model.transmission`` (census 2026-07-21: 5 src + 12 script +
  43 test importer files, 77 names). Extend, never prune.
* **Home identity** — each moved name resolves via the facade to the very
  object defined in its new home submodule.
* **Patch transparency** — ``mock.patch("market_sim.model.transmission.X")``
  intercepts a call-time ``from market_sim.model.transmission import X``
  (the ``data/fleet.py`` / ``winter_fuel_inventory.py`` pattern).
* **Registry integrity** — :data:`INTERCHANGE_INJECTIONS` maps each ISO to
  the exact per-ISO step functions (rule 25: no generic fallback entry).
"""

from __future__ import annotations

import importlib
from unittest import mock

# The union of every name historically imported from
# market_sim.model.transmission by src/, scripts/, and tests/ (re-measured
# census, session 3F). This is the facade's minimum contractual surface.
HISTORICAL_SURFACE = (
    "CAISO_FIRM_IMPORT_TRANCHES",
    "CAISO_GAS_FLOOR_HOURS",
    "MISO_LOSS_LINK_TIEBREAK_EPS",
    "NYISO_IMPORT_HUB_HURDLE",
    "NYISO_SELFSUPPLY_FLOOR_HOURS",
    "PJM_EAST_CUT_LINKS",
    "_CAISO_IMPORT_COUPLE_HR",
    "_CAISO_SOLAR_SHAPE_EXPORT_TRANCHES",
    "_CAISO_SOLAR_SHAPE_TRANCHES",
    "_REF_EXPORT_MARK",
    "_REF_IMPORT_MARK",
    "_bridge_flagged_runs",
    "_distribute_group_floor",
    "_miso_firm_import_uid",
    "apply_caiso_asymmetric_path_limits",
    "apply_caiso_local_import_limits",
    "apply_deliverability_seam_limit",
    "apply_interchange_injections",
    "apply_miso_rdt_tcdc",
    "apply_miso_zonal_loss_links",
    "apply_nyiso_li_tsl_import_cap",
    "apply_nyiso_nyc_tsl_import_cap",
    "build_caiso_corridor_flow_groups",
    "build_caiso_per_hub_intertie",
    "build_export_sinks",
    "build_import_generators",
    "build_import_node_reconciliation",
    "build_incidence_matrix",
    "build_interface_groups",
    "build_miso_deliverability_groups",
    "build_miso_firm_imports",
    "build_miso_link_loss",
    "build_pjm_east_interface_cut_groups",
    "build_pjm_external_flow_groups",
    "build_reference_price_node",
    "build_wecc_export_sink",
    "build_wecc_import_generators",
    "caiso_solar_deliverability_derate",
    "extend_with_import_node",
    "forward_corridor_atc_envelope",
    "forward_corridor_interface_groups",
    "get_link_bidirectional_array",
    "get_link_flow_cost_array",
    "get_ttc_array",
    "inject_caiso_dsw_daytime_clean",
    "inject_caiso_dsw_overnight_clean",
    "inject_caiso_dsw_surplus_clean",
    "inject_caiso_export_hub_prices",
    "inject_caiso_firm_import_selfschedule",
    "inject_caiso_firm_import_shape",
    "inject_caiso_gas_commitment_floor",
    "inject_caiso_import_gas_coupling",
    "inject_caiso_import_hub_prices",
    "inject_caiso_import_solar_shape",
    "inject_caiso_per_hub_intertie_prices",
    "inject_caiso_per_hub_reference_prices",
    "inject_interchange_shape",
    "inject_miso_firm_imports",
    "inject_miso_pjm_lmp_import_prices",
    "inject_miso_seam_flow_limit",
    "inject_miso_seam_ladder_prices",
    "inject_neiso_gas_coldsnap_derate",
    "inject_nyiso_firm_imports",
    "inject_nyiso_import_hub_prices",
    "inject_nyiso_local_selfsupply",
    "inject_pjm_seam_flow_limit",
    "inject_pjm_seam_ladder_prices",
    "inject_reference_price_firm_export",
    "inject_reference_price_mc",
    "inject_reliability_floor",
    "split_caiso_import_node_per_hub",
    "split_miso_south_external_node",
    "wecc_border_carbon_adder",
)

# Every top-level name each new submodule defines (module loggers excluded);
# the facade must resolve each to the submodule's own object.
MOVED_SURFACE: dict[str, tuple[str, ...]] = {
    "market_sim.model.interchange.core": (
        "_bridge_flagged_runs",
        "_distribute_group_floor",
        "build_incidence_matrix",
        "build_interface_groups",
        "get_link_bidirectional_array",
        "get_link_flow_cost_array",
        "get_ttc_array",
        "inject_reliability_floor",
    ),
    "market_sim.model.interchange.import_nodes": (
        "_REF_EXPORT_MARK",
        "_REF_IMPORT_MARK",
        "_inject_seam_ladder",
        "apply_deliverability_seam_limit",
        "apply_reference_price_seam_injections",
        "build_export_sinks",
        "build_import_generators",
        "build_reference_price_node",
        "extend_with_import_node",
        "inject_interchange_shape",
        "inject_reference_price_firm_export",
        "inject_reference_price_firm_import",
        "inject_reference_price_mc",
        "wecc_border_carbon_adder",
    ),
    "market_sim.model.interchange.caiso": (
        "CAISO_FIRM_IMPORT_TRANCHES",
        "CAISO_GAS_FLOOR_HOURS",
        "CAISO_INTERTIE_TIEBREAK_EPS",
        "CAISO_PATH_DIRECTIONAL_RATINGS",
        "_CAISO_CORRIDOR_LINK_TO",
        "_CAISO_HUB_EXPORT_TRANCHES",
        "_CAISO_IMPORT_COUPLE_HR",
        "_CAISO_LOCAL_IMPORT_LINKS",
        "_CAISO_PER_HUB_EXPORT_PREFIX",
        "_CAISO_SOLAR_SHAPE_EXPORT_TRANCHES",
        "_CAISO_SOLAR_SHAPE_TRANCHES",
        "_caiso_corridor_export_cap_mw",
        "_caiso_corridor_import_ttc_mw",
        "_caiso_import_tranche_of",
        "apply_caiso_asymmetric_path_limits",
        "apply_caiso_local_import_limits",
        "apply_caiso_seam_injections",
        "build_caiso_corridor_flow_groups",
        "build_caiso_per_hub_intertie",
        "build_wecc_export_sink",
        "build_wecc_import_generators",
        "caiso_solar_deliverability_derate",
        "forward_corridor_atc_envelope",
        "forward_corridor_interface_groups",
        "inject_caiso_dsw_daytime_clean",
        "inject_caiso_dsw_overnight_clean",
        "inject_caiso_dsw_surplus_clean",
        "inject_caiso_export_hub_prices",
        "inject_caiso_firm_import_selfschedule",
        "inject_caiso_firm_import_shape",
        "inject_caiso_gas_commitment_floor",
        "inject_caiso_import_gas_coupling",
        "inject_caiso_import_hub_prices",
        "inject_caiso_import_solar_shape",
        "inject_caiso_per_hub_intertie_prices",
        "inject_caiso_per_hub_reference_prices",
        "split_caiso_import_node_per_hub",
    ),
    "market_sim.model.interchange.miso": (
        "MISO_LOSS_LINK_TIEBREAK_EPS",
        "_MISO_MONTH_TO_SEASON",
        "_MONTH_HOURS",
        "_miso_firm_import_uid",
        "_miso_midwest_internal",
        "apply_miso_firm_import_injections",
        "apply_miso_rdt_tcdc",
        "apply_miso_zonal_loss_links",
        "build_miso_deliverability_groups",
        "build_miso_firm_imports",
        "build_miso_link_loss",
        "inject_miso_firm_imports",
        "inject_miso_pjm_lmp_import_prices",
        "inject_miso_seam_flow_limit",
        "inject_miso_seam_ladder_prices",
        "split_miso_south_external_node",
    ),
    "market_sim.model.interchange.pjm": (
        "PJM_EAST_CUT_LINKS",
        "build_pjm_east_interface_cut_groups",
        "build_pjm_external_flow_groups",
        "inject_pjm_seam_flow_limit",
        "inject_pjm_seam_ladder_prices",
    ),
    "market_sim.model.interchange.nyiso": (
        "NYISO_IMPORT_HUB_HURDLE",
        "NYISO_SELFSUPPLY_FLOOR_HOURS",
        "_NYISO_HUB_EXPORT_TRANCHE",
        "_NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR",
        "_NYISO_HUB_SCARCITY_TRANCHE",
        "_dispatchable_thermal_codes",
        "apply_nyiso_firm_import_injections",
        "apply_nyiso_li_tsl_import_cap",
        "apply_nyiso_nyc_tsl_import_cap",
        "build_import_node_reconciliation",
        "inject_nyiso_firm_imports",
        "inject_nyiso_import_hub_prices",
        "inject_nyiso_local_selfsupply",
    ),
    "market_sim.model.interchange.neiso": (
        "NEISO_COLDSNAP_FLOOR_HOURS",
        "NEISO_GAS_DERATE_GROUPS",
        "inject_neiso_gas_coldsnap_derate",
    ),
    "market_sim.model.interchange.registry": (
        "INTERCHANGE_INJECTIONS",
        "apply_interchange_injections",
    ),
}

# Names transmission.py historically re-exported from its own module-level
# imports (facade passthroughs) → their canonical defining homes.
PASSTHROUGHS: dict[str, tuple[str, ...]] = {
    "market_sim.config.constants": (
        "CARB_UNSPECIFIED_IMPORT_EF",
        "MISO_RDT_CONTRACT_N_TO_S_MW",
        "MISO_RDT_CONTRACT_S_TO_N_MW",
        "MISO_RDT_DEFAULT_DERATE_FRAC",
        "MISO_RDT_TCDC_STEP1_PRICE",
        "MISO_RDT_TCDC_STEP2_PRICE",
        "MISO_RDT_TCDC_STEP2_START_FRAC",
        "MISO_RPE_DEMAND_VALUE",
        "MISO_SOUTH_EXTERNAL_ZONE",
        "NYISO_LOCAL_SELFSUPPLY_FRAC",
    ),
    "market_sim.config.iso_configs": (
        "InterfaceLimit",
        "ISOConfig",
        "TransferLink",
        "Zone",
    ),
    "market_sim.data.floor_mechanisms": (
        "MECH_CAISO_GAS_COMMITMENT_FLOOR",
        "MECH_FIRM_IMPORT",
        "MECH_NYISO_SELFSUPPLY",
        "MECH_RELIABILITY_FLOOR",
        "ensure_mechanism",
    ),
}


def _facade():
    return importlib.import_module("market_sim.model.transmission")


def _package():
    return importlib.import_module("market_sim.model.interchange")


class TestAliasIdentity:
    def test_facade_is_the_interchange_package(self):
        assert _facade() is _package(), (
            "market_sim.model.transmission must alias the model/interchange "
            "package (sys.modules self-replacement), not re-export a copy"
        )

    def test_historical_surface_resolves(self):
        facade = _facade()
        missing = [n for n in HISTORICAL_SURFACE if not hasattr(facade, n)]
        assert not missing, (
            "facade lost historically-imported names (breaking src/scripts/"
            f"tests importers): {missing}"
        )


class TestMovedSurface:
    def test_every_moved_name_is_the_home_object(self):
        facade = _facade()
        bad = []
        for home_path, names in MOVED_SURFACE.items():
            home = importlib.import_module(home_path)
            for n in names:
                if not hasattr(facade, n):
                    bad.append(f"{n} missing from facade")
                elif getattr(facade, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)

    def test_passthroughs_are_the_canonical_objects(self):
        facade = _facade()
        bad = []
        for home_path, names in PASSTHROUGHS.items():
            home = importlib.import_module(home_path)
            for n in names:
                if not hasattr(facade, n):
                    bad.append(f"{n} missing from facade")
                elif getattr(facade, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)


class TestPatchTransparency:
    def test_string_patch_intercepts_call_time_import(self):
        """The tests/regression/test_fleet_unification.py contract: a mock.patch through
        the historical dotted path must intercept production code that
        resolves the name at call time via the same path (data/fleet.py's
        function-local ``from market_sim.model.transmission import ...``)."""
        with mock.patch(
            "market_sim.model.transmission.inject_neiso_gas_coldsnap_derate"
        ) as spy:
            from market_sim.model.transmission import (
                inject_neiso_gas_coldsnap_derate,
            )

            assert inject_neiso_gas_coldsnap_derate is spy
        # ... and the patch unwinds: the real function is restored.
        from market_sim.model.interchange import neiso

        assert (
            _facade().inject_neiso_gas_coldsnap_derate
            is neiso.inject_neiso_gas_coldsnap_derate
        )


class TestInjectionRegistry:
    def test_per_iso_steps_are_exact(self):
        from market_sim.model.interchange import (
            caiso,
            import_nodes,
            miso,
            nyiso,
            registry,
        )

        expected = {
            "CAISO": (caiso.apply_caiso_seam_injections,),
            "ERCOT": (import_nodes.apply_reference_price_seam_injections,),
            "MISO": (
                import_nodes.apply_reference_price_seam_injections,
                miso.apply_miso_firm_import_injections,
            ),
            "NEISO": (import_nodes.apply_reference_price_seam_injections,),
            "NYISO": (
                import_nodes.apply_reference_price_seam_injections,
                nyiso.apply_nyiso_firm_import_injections,
            ),
            "PJM": (import_nodes.apply_reference_price_seam_injections,),
            # SPP (registered 2026-09-06, lane SPP-20): the self-gating generic
            # seam step alone — default-off for SPP, so a byte-identical no-op.
            "SPP": (import_nodes.apply_reference_price_seam_injections,),
            # NWPP (registered 2026-09-14, lane NWPP-20): the same self-gating
            # step alone — default-off, no IMPORT_ZONE, byte-identical no-op.
            "NWPP": (import_nodes.apply_reference_price_seam_injections,),
        }
        assert registry.INTERCHANGE_INJECTIONS == expected

    def test_no_generic_fallback_entry(self):
        """Rule 25: per-ISO steps never collapse into a generic default —
        the registry has only real ISO keys, and an unknown ISO gets no
        pre-overlay injections at all."""
        from market_sim.model.interchange.registry import INTERCHANGE_INJECTIONS

        assert set(INTERCHANGE_INJECTIONS) == {
            "CAISO",
            "ERCOT",
            "MISO",
            "NEISO",
            "NYISO",
            "PJM",
            "SPP",
            "NWPP",
        }
        assert INTERCHANGE_INJECTIONS.get("DEFAULT") is None
