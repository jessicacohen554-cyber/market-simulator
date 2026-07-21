"""Facade re-export + single-definition tests for the 3E layering fix.

Session 3E (refactor-consolidation plan §5 item 5, 2026-07-21) moved
``config/reserve_config.py`` → ``model/reserves/spec.py`` and
``config/interchange_config.py`` → ``model/interchange/spec.py``, leaving
``sys.modules``-alias facades at the historical ``config/`` paths, and added
the ``data/fleet_models.py`` types-only leaf so config/model-layer code can
name ``Generator`` / ``FleetArrays`` without importing the 10k-line
``data.fleet`` loader.

Pinned contracts:

* **Alias identity** — each facade and its spec module are ONE namespace
  object, so every historical import spelling and monkeypatch/attribute
  write keeps working (the ``model/capacity.py`` pattern).
* **Surface** — the frozen inventories below list every meaningful top-level
  name of the pre-move modules (public and private alike; stdlib/numpy
  namespace incidentals excluded). Extend these lists, never prune them —
  removing a name is a breaking change for src/script/test importers.
* **Single definition** (rule 25: deleted means deleted) — the interchange
  module's local duplicated constants are GONE:
  ``CARB_UNSPECIFIED_IMPORT_EF`` has exactly one assignment site in
  ``src/market_sim`` (config/fuel_trajectories.py, re-exported by
  config/constants.py) and every import path resolves the one object;
  ``_GAS_BASIS_NYISO`` no longer exists anywhere — the use site reads the
  canonical ``GAS_BASIS_DIFFERENTIAL["NYISO"]``.
* **Leaf identity** — ``data.fleet_models`` re-exports the very class
  objects defined in ``data.fleet`` (``__module__`` unchanged; the
  committed p2_state pickles depend on it — see
  ``tests/test_persisted_identity.py``).
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"

# Every meaningful top-level name of the pre-move config/reserve_config.py
# (2,932 ln, main @ 3cbf5b1).
_RESERVE_SURFACE = (
    "CAISO_AS_SUSTAIN_DURATION_H",
    "CAISO_CONTINGENCY_FRAC",
    "CAISO_ENERGY_BID_CAP_SOFT",
    "CAISO_HYDRO_RAMP10_FRAC",
    "CAISO_NONSPIN_DEMAND_CURVE",
    "CAISO_SPIN_DEMAND_CURVE",
    "CAISO_SPIN_FRACTION",
    "CALIBRATION_DIR",
    "ERCOT_AS_ECRS_BASE_MW",
    "ERCOT_AS_ECRS_MAX_MW",
    "ERCOT_AS_ECRS_MIN_MW",
    "ERCOT_AS_ECRS_RAMP_COEF",
    "ERCOT_AS_ECRS_SIGMA_COEF",
    "ERCOT_AS_FE_FRAC_LOAD",
    "ERCOT_AS_FE_FRAC_SOLAR",
    "ERCOT_AS_FE_FRAC_WIND",
    "ERCOT_AS_NSPIN_BASE_MW",
    "ERCOT_AS_NSPIN_LOAD_COEF",
    "ERCOT_AS_NSPIN_MAX_MW",
    "ERCOT_AS_NSPIN_MIN_MW",
    "ERCOT_AS_NSPIN_RAMP_COEF",
    "ERCOT_AS_PLAN_HOLD_EPS",
    "ERCOT_AS_PRODUCTS",
    "ERCOT_AS_PRODUCT_DURATION_H",
    "ERCOT_AS_RAMP_WINDOW_HOURS",
    "ERCOT_AS_REGUP_FLOOR_MW",
    "ERCOT_AS_REGUP_MAX_MW",
    "ERCOT_AS_REGUP_MIN_MW",
    "ERCOT_AS_REGUP_SIGMA_COEF",
    "ERCOT_AS_RRS_FLOOR_MW",
    "ERCOT_AS_RRS_INERTIA_COEF_MW",
    "ERCOT_AS_RRS_MAX_MW",
    "ERCOT_ECRS_RELEASE_REFORM_HOUR",
    "ERCOT_ECRS_RELEASE_REFORM_YEAR",
    "ERCOT_LR_RRS_ENROLL_BASE_MW",
    "ERCOT_LR_RRS_ENROLL_BASE_YEAR",
    "ERCOT_LR_RRS_ENROLL_CAP_MW",
    "ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR",
    "FUEL_TYPE_NAMES",
    "FleetArrays",
    "MISO_EMERGENCY_TIER1_OFFER_FLOOR",
    "MISO_EMERGENCY_TIER2_OFFER_FLOOR",
    "MISO_MIDWEST_ZONES",
    "MISO_REGULATING_RESERVE_MW",
    "MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW",
    "MISO_RESERVE_DEMAND_CURVE_MAX",
    "MISO_RPE_DEMAND_VALUE",
    "MISO_ZONAL_ORDC_STEPS",
    "MISO_ZONAL_RESERVE_DEFAULT_ZONES",
    "NEISO_RCPF_PRODUCTS",
    "NYISO_DOWNSTATE_SPIN_ZONES",
    "NYISO_RCPF_LOCATIONAL",
    "NYISO_RCPF_PRODUCTS",
    "NYISO_SPIN_FRACTION",
    "ORDC_FLOOR_START_HOUR_2023",
    "ORDC_FLOOR_STEPS",
    "PJM_MAD_ZONES",
    "PJM_ORDC_CURVE_PATH",
    "PJM_PERGEN_SIZE_SPLIT_MEAN_MULTIPLE",
    "PJM_PRIMARY_RESERVE_LSC_FACTOR",
    "POSTURE_FAST_START_MIN_DOWN_H",
    "POSTURE_FAST_START_STARTUP_PER_MW",
    "QUICK_START_FUEL_TYPES",
    "RESERVE_FUEL_TYPES",
    "ReserveDesign",
    "ReserveFamily",
    "build_reserve_dispatch_kwargs",
    "caiso_pergen_pool_ramp10",
    "caiso_pergen_structure",
    "ercot_commitment_headroom_overrides",
    "ercot_commitment_posture_spec",
    "get_reserve_design",
    "pjm_pergen_pool_ramp10",
    "pjm_pergen_structure",
    "_ERCOT_POSTURE_CHP_GROUPS",
    "_caiso_design",
    "_caiso_locational_as_families",
    "_caiso_reserve_eligible",
    "_ercot_design",
    "_ercot_multiproduct_design",
    "_miso_design",
    "_neiso_design",
    "_nyiso_design",
    "_pjm_design",
    "_posture_pool_params",
    "_quick_start_eligible",
    "_reserve_eligible",
)

# Every meaningful top-level name of the pre-move config/interchange_config.py
# (1,919 ln, main @ 3cbf5b1), minus the deleted duplicate ``_GAS_BASIS_NYISO``.
_INTERCHANGE_SURFACE = (
    "CAISO_CORRIDOR_ATC_SOLAR_K",
    "CAISO_CORRIDOR_DIBA",
    "CAISO_CORRIDOR_FLOW_PERCENTILE",
    "CAISO_DAYTIME_CLEAN_HOD_MAX",
    "CAISO_DAYTIME_CLEAN_HOD_MIN",
    "CAISO_DAYTIME_CLEAN_TRIM_HOD_MAX",
    "CAISO_DSW_DAYTIME_CLEAN_DEPTH_BY_YEAR",
    "CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC",
    "CAISO_DSW_DAYTIME_CLEAN_NAME",
    "CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_BY_YEAR",
    "CAISO_DSW_DAYTIME_CLEAN_TRIM_DEPTH_STATIC",
    "CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR",
    "CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC",
    "CAISO_DSW_OVERNIGHT_CLEAN_NAME",
    "CAISO_DSW_SURPLUS_CLEAN_DEPTH_BY_YEAR",
    "CAISO_DSW_SURPLUS_CLEAN_DEPTH_STATIC",
    "CAISO_DSW_SURPLUS_CLEAN_NAME",
    "CAISO_DSW_SURPLUS_REMOTE_VOM",
    "CAISO_FIRM_IMPORT_SHAPE_PERCENTILE",
    "CAISO_IMPORT_DELIVERY_BASIS",
    "CAISO_IMPORT_TRANCHE_HUB",
    "CAISO_OVERNIGHT_CLEAN_HOD_MAX",
    "CAISO_PER_HUB_IMPORT_ZONES",
    "CAISO_PER_HUB_NEIGHBORS",
    "CARB_UNSPECIFIED_IMPORT_EF",
    "CaisoHubNeighbor",
    "Corridor",
    "EXPORT_TRANCHES",
    "EXPORT_TRANCHES_BY_YEAR",
    "EXTERNAL_SIMULTANEOUS_LIMITS",
    "FirmImport",
    "Generator",
    "IMPORT_EFORD",
    "IMPORT_NODE_LINKS",
    "IMPORT_TRANCHES",
    "IMPORT_TRANCHES_BY_YEAR",
    "IMPORT_TRANCHE_EF",
    "IMPORT_ZONE",
    "INTERFACE_NEIGHBORS",
    "InterchangeSpec",
    "MISO_FIRM_IMPORT_DEFAULT_ISOS",
    "MISO_MANITOBA_FIRM_IMPORT_FLOOR_FRAC",
    "MISO_MANITOBA_FIRM_IMPORT_MW",
    "MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR",
    "MISO_MANITOBA_FIRM_IMPORT_NAME",
    "MISO_MANITOBA_FIRM_IMPORT_OFFER",
    "MISO_MANITOBA_FIRM_IMPORT_ZONE",
    "MISO_MANITOBA_SEAM_SPEC",
    "MISO_PJM_BORDER_HR_BY_YEAR",
    "MISO_SEAM_DIBA",
    "MISO_SEAM_LADDER_BY_YEAR",
    "NYISO_FIRM_IMPORT_FLOOR_FRAC",
    "NYISO_IMPORT_RECON_BAND_FRAC",
    "NeighborInterface",
    "PJM_SEAM_LADDER_BY_YEAR",
    "PJM_SEAM_TIE",
    "PRICED_INTERCHANGE_DEFAULT_ISOS",
    "REFERENCE_PRICE_DEFAULT_ISOS",
    "ReconciliationBand",
    "WECC_EXPORT_CAP_MW",
    "WECC_IMPORT_EFORD",
    "WECC_IMPORT_TRANCHES",
    "apply_interchange_topology",
    "build_interchange_fleet",
    "get_interchange_spec",
    "resolve_miso_firm_imports",
    "resolve_miso_manitoba_firm_import_mw",
    "resolve_priced_interchange",
    "_build_static_tranche_gens",
)


class TestFacadeAlias(unittest.TestCase):
    """Each facade and its spec module are one module object (one namespace)."""

    def test_reserve_facade_is_the_spec_module(self):
        import market_sim.config.reserve_config as facade
        import market_sim.model.reserves.spec as spec

        self.assertIs(facade, spec)

    def test_interchange_facade_is_the_spec_module(self):
        import market_sim.config.interchange_config as facade
        import market_sim.model.interchange.spec as spec

        self.assertIs(facade, spec)

    def test_from_import_resolves_to_the_spec_modules(self):
        import market_sim.model.interchange.spec as ic_spec
        import market_sim.model.reserves.spec as res_spec
        from market_sim.config import interchange_config, reserve_config

        self.assertIs(reserve_config, res_spec)
        self.assertIs(interchange_config, ic_spec)


class TestFacadeSurface(unittest.TestCase):
    """Every pre-move top-level name resolves via the facade AND the package."""

    def test_reserve_surface_resolves(self):
        import market_sim.config.reserve_config as facade
        import market_sim.model.reserves as pkg

        missing = [n for n in _RESERVE_SURFACE if not hasattr(facade, n)]
        self.assertEqual(missing, [], f"facade lost {len(missing)} name(s)")
        missing_pkg = [n for n in _RESERVE_SURFACE if not hasattr(pkg, n)]
        self.assertEqual(missing_pkg, [], f"package lost {len(missing_pkg)} name(s)")

    def test_interchange_surface_resolves(self):
        import market_sim.config.interchange_config as facade
        import market_sim.model.interchange as pkg

        missing = [n for n in _INTERCHANGE_SURFACE if not hasattr(facade, n)]
        self.assertEqual(missing, [], f"facade lost {len(missing)} name(s)")
        missing_pkg = [
            n
            for n in _INTERCHANGE_SURFACE
            if n != "_GAS_BASIS_NYISO" and not hasattr(pkg, n)
        ]
        self.assertEqual(missing_pkg, [], f"package lost {len(missing_pkg)} name(s)")

    def test_named_from_imports_resolve(self):
        # The import styles the src/script/test importers actually use.
        from market_sim.config.interchange_config import (  # noqa: F401
            INTERFACE_NEIGHBORS,
            IMPORT_TRANCHES,
            IMPORT_ZONE,
            InterchangeSpec,
            NeighborInterface,
            _build_static_tranche_gens,
            apply_interchange_topology,
            build_interchange_fleet,
            get_interchange_spec,
            resolve_priced_interchange,
        )
        from market_sim.config.reserve_config import (  # noqa: F401
            ERCOT_AS_PRODUCTS,
            RESERVE_FUEL_TYPES,
            ReserveDesign,
            ReserveFamily,
            _caiso_design,
            _miso_design,
            _nyiso_design,
            _posture_pool_params,
            build_reserve_dispatch_kwargs,
            ercot_commitment_posture_spec,
            get_reserve_design,
            pjm_pergen_structure,
        )

    def test_classes_are_one_object_via_both_paths(self):
        from market_sim.config.interchange_config import (
            InterchangeSpec as via_facade_ic,
        )
        from market_sim.config.reserve_config import ReserveDesign as via_facade_res
        from market_sim.model.interchange.spec import InterchangeSpec as via_spec_ic
        from market_sim.model.reserves.spec import ReserveDesign as via_spec_res

        self.assertIs(via_facade_res, via_spec_res)
        self.assertIs(via_facade_ic, via_spec_ic)


class TestPatchSemantics(unittest.TestCase):
    """Attribute writes through the historical path reach the spec namespace."""

    def test_probe_style_attribute_write_is_shared(self):
        import market_sim.config.interchange_config as facade
        import market_sim.model.interchange.spec as spec

        original = facade.IMPORT_TRANCHE_EF
        sentinel = object()
        try:
            facade.IMPORT_TRANCHE_EF = sentinel
            self.assertIs(spec.IMPORT_TRANCHE_EF, sentinel)
        finally:
            facade.IMPORT_TRANCHE_EF = original


class TestFleetModelsLeaf(unittest.TestCase):
    """``data.fleet_models`` re-exports the classes DEFINED in ``data.fleet``."""

    def test_leaf_classes_are_the_fleet_classes(self):
        from market_sim.data.fleet import FleetArrays as fleet_fa
        from market_sim.data.fleet import Generator as fleet_gen
        from market_sim.data.fleet_models import FleetArrays as leaf_fa
        from market_sim.data.fleet_models import Generator as leaf_gen

        self.assertIs(leaf_gen, fleet_gen)
        self.assertIs(leaf_fa, fleet_fa)

    def test_pickle_module_paths_unchanged(self):
        # Redundant with tests/test_persisted_identity.py by design: the leaf
        # must never become the DEFINING module before session 3H.
        from market_sim.data.fleet_models import FleetArrays, Generator

        self.assertEqual(Generator.__module__, "market_sim.data.fleet")
        self.assertEqual(FleetArrays.__module__, "market_sim.data.fleet")


def _assignment_sites(name: str) -> list[str]:
    """Module-relative paths in src/market_sim with a top-level assignment of ``name``."""
    sites = []
    for path in sorted((_SRC / "market_sim").rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in tree.body:
            targets = []
            if isinstance(node, ast.Assign):
                targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                targets = [node.target.id]
            if name in targets:
                sites.append(str(path.relative_to(_SRC)))
    return sites


class TestSingleDefinition(unittest.TestCase):
    """The deduped constants have exactly one definition site (rule 25)."""

    def test_carb_unspecified_import_ef_single_assignment(self):
        self.assertEqual(
            _assignment_sites("CARB_UNSPECIFIED_IMPORT_EF"),
            ["market_sim/config/fuel_trajectories.py"],
        )

    def test_gas_basis_differential_single_assignment(self):
        self.assertEqual(
            _assignment_sites("GAS_BASIS_DIFFERENTIAL"),
            ["market_sim/config/fuel_trajectories.py"],
        )

    def test_gas_basis_nyiso_deleted_not_zeroed(self):
        self.assertEqual(_assignment_sites("_GAS_BASIS_NYISO"), [])

    def test_every_import_path_resolves_the_one_object(self):
        import market_sim.config.constants as constants
        import market_sim.config.fuel_trajectories as fuel_trajectories
        import market_sim.config.interchange_config as facade
        import market_sim.model.interchange.spec as spec

        for mod in (constants, facade, spec):
            self.assertIs(
                mod.CARB_UNSPECIFIED_IMPORT_EF,
                fuel_trajectories.CARB_UNSPECIFIED_IMPORT_EF,
                mod.__name__,
            )
        self.assertIs(
            constants.GAS_BASIS_DIFFERENTIAL,
            fuel_trajectories.GAS_BASIS_DIFFERENTIAL,
        )
        self.assertIs(
            spec.GAS_BASIS_DIFFERENTIAL, fuel_trajectories.GAS_BASIS_DIFFERENTIAL
        )
        self.assertEqual(constants.CARB_UNSPECIFIED_IMPORT_EF, 0.428)
        self.assertEqual(constants.GAS_BASIS_DIFFERENTIAL["NYISO"], 0.55)

    def test_nyiso_neighbor_gas_basis_reads_the_canonical_value(self):
        # The one pre-move ``_GAS_BASIS_NYISO`` use site: the PJM→NYISO
        # reference-price neighbor. Byte-for-byte value transplant (rule 23).
        from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
        from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

        nyiso = [n for n in INTERFACE_NEIGHBORS["PJM"] if n.name == "NYISO"]
        self.assertEqual(len(nyiso), 1)
        self.assertEqual(nyiso[0].gas_basis, GAS_BASIS_DIFFERENTIAL["NYISO"])
        self.assertEqual(nyiso[0].gas_basis, 0.55)


if __name__ == "__main__":
    unittest.main()
