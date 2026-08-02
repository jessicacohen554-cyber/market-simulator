"""Zone-resolved anchor for ``gas_offer_net_revenue_margin`` (nyiso-109).

``apply_gas_offer_margin``'s identity is *at ``fuel == anchor`` the reformed
offer reduces EXACTLY to the registered band multiplier* — a statement about a
unit's OWN delivered fuel. The ISO anchor is derived from the ISO-level
``_gas_series``, which does not carry the per-zone basis the solve applies
afterwards, so on an ISO whose keeper arms a zonal basis (NYISO) every non-
reference zone's units price their markup at a fuel level they never pay. These
tests pin the gate's three contracts: byte-identical OFF, hard-fail on a
half-armed config, and per-zone resolution ON with band-scoped rebasis winning.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ZONE
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.offer_curves import apply_gas_offer_margin

ZONE_NAMES = get_iso_config("NYISO").zone_names
ISO_ANCHOR = 3.9046
CT_HR = 10.6

CT_BANDS = {
    "committed": 1.35,
    "econ_low": 1.0,
    "econ_high": 1.0,
    "peak": 4.0,
    "econ_low_share": 0.526,
    "pct_peaking": 7.0,
    "phys_committed": 0.843,
    "phys_econ_low": 0.661,
    "phys_econ_high": 0.658,
    "phys_peak": 1.0,
}


def _bin(zone: str, plant: int) -> dict:
    """One synthetic per-plant CT bin row homed in ``zone``."""
    return {
        "Plant_Group": "CT_PEAKER",
        "ERCOT_Zone": zone,  # the bin sheet's zone column, whatever the ISO
        "Bin_Number": 1,
        "Bin_Label": f"TEST{plant}",
        "Plant_Code": plant,
        "Plant_Name": f"Test Plant {plant}",
        "capacity_mw": 1000.0,
        "hr_weighted": CT_HR,
        "hr_mr": CT_HR,
        "hr_mc": CT_HR,
        "hr_econ": CT_HR,
        "hr_peak": CT_HR,
        "pct_mr": 0,
        "pct_mc": 30,
        "pct_econ": 55,
        "pct_peak": 15,
        "min_run": 0,
        "min_down": 0,
        "plant_count": 1,
        "plant_codes": [plant],
        "fuel": "gas_ct",
    }


def _bins() -> pd.DataFrame:
    """One plant in the reference zone and one in each shifted zone."""
    return pd.DataFrame(
        [
            _bin("Capital_Hudson", 1),
            _bin("NYC", 2),
            _bin("Upstate_West", 3),
        ]
    )


def _config(**overrides) -> ScenarioConfig:
    """NYISO config with the margin form armed at the ISO anchor."""
    base = dict(
        iso="NYISO",
        gas_offer_net_revenue_margin=True,
        gas_offer_margin_anchor=ISO_ANCHOR,
        offer_curve_by_group={"CT_PEAKER": dict(CT_BANDS)},
    )
    base.update(overrides)
    return ScenarioConfig(**base)


def _zonal_config(**overrides) -> ScenarioConfig:
    """The same config with the zone-resolved anchor armed."""
    base = dict(
        gas_offer_margin_zonal_anchor=True,
        gas_offer_margin_anchor_by_zone=dict(GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]),
    )
    base.update(overrides)
    return _config(**base)


def _anchors_by_zone(config) -> dict[str, set]:
    """``{zone: {resolved tranche anchors}}`` for the marked-up tranches."""
    fleet, _ = bins_to_fleet(_bins(), ZONE_NAMES, config)
    out: dict[str, set] = {}
    for g in fleet:
        if g.offer_markup_hr > 0.0:
            out.setdefault(g.zone, set()).add(g.offer_margin_anchor)
    return out


class TestZonalAnchorGate(unittest.TestCase):
    """The gate's arming contract."""

    def test_off_is_byte_identical(self):
        off = bins_to_fleet(_bins(), ZONE_NAMES, _config())[0]
        for g in off:
            self.assertIsNone(g.offer_margin_anchor)

    def test_armed_without_the_margin_form_raises(self):
        cfg = _config(
            gas_offer_net_revenue_margin=False,
            gas_offer_margin_anchor=None,
            gas_offer_margin_zonal_anchor=True,
            gas_offer_margin_anchor_by_zone={"NYC": 2.7612},
        )
        with self.assertRaises(ValueError):
            bins_to_fleet(_bins(), ZONE_NAMES, cfg)

    def test_armed_without_the_zone_map_raises(self):
        cfg = _config(gas_offer_margin_zonal_anchor=True)
        with self.assertRaises(ValueError):
            bins_to_fleet(_bins(), ZONE_NAMES, cfg)


class TestZonalAnchorResolution(unittest.TestCase):
    """Each marked-up tranche prices its markup at ITS zone's anchor."""

    def test_each_zone_resolves_its_own_anchor(self):
        got = _anchors_by_zone(_zonal_config())
        table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]
        for zone in ("Capital_Hudson", "NYC", "Upstate_West"):
            self.assertEqual(got[zone], {table[zone]}, zone)

    def test_reference_zone_keeps_the_iso_anchor(self):
        table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]
        self.assertAlmostEqual(table["Capital_Hudson"], ISO_ANCHOR, places=6)

    def test_zone_absent_from_the_map_keeps_the_window_anchor(self):
        cfg = _zonal_config(
            gas_offer_margin_anchor_by_zone={"NYC": 2.7612},
        )
        got = _anchors_by_zone(cfg)
        self.assertEqual(got["NYC"], {2.7612})
        self.assertEqual(got["Capital_Hudson"], {None})

    def test_band_scoped_rebasis_still_wins(self):
        # rule 19 [R-ONE-MECH]: the ERCOT-118/119 per-band identification
        # anchor and the zone anchor never stack — the band-scoped key wins.
        bands = dict(CT_BANDS)
        bands["margin_anchor"] = 9.99
        cfg = _zonal_config(offer_curve_by_group={"CT_PEAKER": bands})
        got = _anchors_by_zone(cfg)
        for zone in ("Capital_Hudson", "NYC", "Upstate_West"):
            self.assertEqual(got[zone], {9.99}, zone)


class TestZonalAnchorPricing(unittest.TestCase):
    """The resolved anchor is what ``apply_gas_offer_margin`` prices at."""

    def _mc(self, config, fuel_by_zone: dict[str, float]) -> dict[str, float]:
        """Marked-up ``econlo`` offer per zone at that zone's delivered fuel.

        Returns the FULL assembled offer (burn + VOM), which is what
        ``apply_gas_offer_margin`` mutates.
        """
        fleet, _ = bins_to_fleet(_bins(), ZONE_NAMES, config)
        hr = np.array([g.heat_rate for g in fleet], dtype=float)
        vom = np.array([g.vom for g in fleet], dtype=float)
        fuel = np.array([[fuel_by_zone[g.zone]] for g in fleet], dtype=float).repeat(
            2, axis=1
        )
        mc = hr[:, None] * fuel + vom[:, None]
        apply_gas_offer_margin(mc, fleet, fuel, config)
        return {
            g.zone: float(mc[i, 0])
            for i, g in enumerate(fleet)
            if g.unit_id.endswith("econlo")
        }

    def test_offer_reduces_to_the_multiplier_at_its_own_zone_anchor(self):
        # The mechanism's identity, now true in EVERY zone: priced at the
        # zone's own anchor the reformed offer is the registered multiplier.
        table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]
        cfg = _zonal_config()
        fleet, _ = bins_to_fleet(_bins(), ZONE_NAMES, cfg)
        vom = float(next(g.vom for g in fleet if g.unit_id.endswith("econlo")))
        got = self._mc(cfg, {z: table[z] for z in ZONE_NAMES if z in table})
        for zone, anchor in table.items():
            if zone not in got:
                continue
            expected = CT_BANDS["econ_low"] * CT_HR * anchor + vom
            self.assertAlmostEqual(got[zone], expected, places=6, msg=zone)

    def test_shifted_zones_offer_strictly_less_than_under_the_iso_anchor(self):
        # At the SAME (below-ISO-anchor) delivered fuel a shifted zone's unit
        # offers less once its markup is priced at its own anchor; the
        # reference zone is unchanged.
        fuel = {"Capital_Hudson": 3.3566, "NYC": 2.0166, "Upstate_West": 1.8966}
        iso = self._mc(_config(), fuel)
        zonal = self._mc(_zonal_config(), fuel)
        self.assertAlmostEqual(zonal["Capital_Hudson"], iso["Capital_Hudson"], places=9)
        self.assertLess(zonal["NYC"], iso["NYC"])
        self.assertLess(zonal["Upstate_West"], iso["Upstate_West"])


class TestZonalAnchorRegistry(unittest.TestCase):
    """Registry hygiene (rules 24 / 25)."""

    def test_only_zonal_basis_isos_carry_a_table(self):
        # NYISO (nyiso-109) + PJM (pjm-144): the two keepers that arm a
        # per-zone delivered-gas basis with a derived zone-anchor table.
        # ERCOT/MISO stay U in the matrix until their own lanes derive one.
        self.assertEqual(set(GAS_OFFER_MARGIN_ANCHOR_BY_ZONE), {"NYISO", "PJM"})

    def test_every_model_zone_is_covered(self):
        self.assertEqual(set(GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]), set(ZONE_NAMES))


class TestPjmZonalAnchorRegistry(unittest.TestCase):
    """PJM table hygiene (pjm-144): coverage + the mean-zero geometry.

    PJM's applier is the capacity-weighted MEAN-ZERO core
    (``data.fuel.basis.meanzero``), not NYISO's reference-zone convention, so
    its zone anchors must straddle the ISO anchor from BOTH sides (premium
    east, discount west) rather than sit uniformly at or below it.
    """

    def test_every_pjm_model_zone_is_covered(self):
        pjm_zones = get_iso_config("PJM").zone_names
        self.assertEqual(set(GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]), set(pjm_zones))

    def test_anchors_are_two_sided_around_the_iso_anchor(self):
        from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

        iso_anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"]
        table = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["PJM"]
        self.assertTrue(any(v > iso_anchor for v in table.values()))
        self.assertTrue(any(v < iso_anchor for v in table.values()))


if __name__ == "__main__":
    unittest.main()
