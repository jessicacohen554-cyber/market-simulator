"""capx D33 ``entry_vre_zone_selection``: WHERE a new VRE MW is built.

OFF (the shipped default) every economically-entered wind/solar MW is sited in
the single per-ISO ``renewables.RENEWABLE_ZONE_ALLOCATION`` bucket, whatever
that zone's prices, resource or REC eligibility. ON the screen values the
candidate in every zone that carries the resource and sites it where its own
margin is highest, over machinery the screen already had (per-zone CF profile,
per-zone LP price, the K-row zone-resolved REC credit, the zonal RA gate).

The object the gate repairs, measured in capx D33 §2: MISO's bucket is
MISO-South, the ONE model zone excluded from every state compliance region's
eligible-zone mask (``MISO_RPS_MIDWEST_FOOTPRINT_ZONES``), so a solar candidate
was screened at a $0 REC credit while the run's own zonal REC vector peaked at
the $30/MWh ACP.
"""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.renewables import RENEWABLE_ZONE_ALLOCATION
from market_sim.model.capacity import apply_economic_new_entry

ZONES = [z.name for z in get_iso_config("MISO").zones]
BUCKET_SOLAR = RENEWABLE_ZONE_ALLOCATION["MISO"]["solar"]


def _config(armed: bool) -> ScenarioConfig:
    """MISO entry config with emerging techs pushed past the horizon."""
    return ScenarioConfig(
        iso="MISO",
        entry_vre_zone_selection=armed,
        miso_rps_compliance_regions=True,
        h2_available_year=2099,
        ccs_available_year=2099,
        egs_available_year=2099,
        offshore_wind_available_year=2099,
    )


def _zonal(value: float, hours: int = 8760) -> np.ndarray:
    return np.full((len(ZONES), hours), value)


def _screen(armed: bool, rps_vector: np.ndarray, prices: np.ndarray | None = None):
    """Run the real screen and return ``{zone: {tech: mw}}``."""
    solar_cf = _zonal(0.25)
    wind_cf = _zonal(0.40)
    _, additions = apply_economic_new_entry(
        [],
        _zonal(70.0) if prices is None else prices,
        2030,
        _config(armed),
        "MISO",
        rps_shadow_price=rps_vector,
        zone_names=ZONES,
        wind_cf=wind_cf,
        solar_cf=solar_cf,
    )
    return additions


class TestBucketIsTheDefault(unittest.TestCase):
    """OFF: the single-bucket siting, unchanged."""

    def test_solar_lands_in_the_allocation_bucket(self):
        # A REC price that exists ONLY in MISO-East, i.e. exactly the MISO
        # signature: the bucket zone earns nothing while another zone pays.
        rps = np.zeros(len(ZONES))
        rps[ZONES.index("MISO-East")] = 30.0
        adds = _screen(False, rps)
        built = {z: t for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
        self.assertEqual(list(built), [BUCKET_SOLAR])
        self.assertEqual(BUCKET_SOLAR, "MISO-South")

    def test_off_path_ignores_the_zonal_rec_signal(self):
        """OFF is insensitive to WHERE the REC price is — the defect itself."""
        rps_east = np.zeros(len(ZONES))
        rps_east[ZONES.index("MISO-East")] = 30.0
        rps_ill = np.zeros(len(ZONES))
        rps_ill[ZONES.index("MISO-Illinois")] = 30.0
        self.assertEqual(_screen(False, rps_east), _screen(False, rps_ill))


class TestArmedFollowsTheValue(unittest.TestCase):
    """ON: the candidate is sited where its own margin is highest."""

    def test_solar_moves_to_the_rec_eligible_zone(self):
        rps = np.zeros(len(ZONES))
        rps[ZONES.index("MISO-East")] = 30.0
        adds = _screen(True, rps)
        built = {z for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
        self.assertEqual(built, {"MISO-East"})

    def test_the_chosen_zone_tracks_the_signal(self):
        for zone in ("MISO-East", "MISO-Illinois", "MISO-Plains"):
            with self.subTest(zone=zone):
                rps = np.zeros(len(ZONES))
                rps[ZONES.index(zone)] = 30.0
                adds = _screen(True, rps)
                built = {z for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
                self.assertEqual(built, {zone})

    def test_price_decides_when_no_attribute_price_exists(self):
        """With a flat zero REC vector the energy leg alone picks the zone."""
        prices = _zonal(70.0)
        prices[ZONES.index("MISO-Plains")] = 140.0
        adds = _screen(True, np.zeros(len(ZONES)), prices=prices)
        built = {z for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
        self.assertEqual(built, {"MISO-Plains"})

    def test_scalar_dual_leaves_siting_to_the_bucket(self):
        """A scalar (legacy single-row) dual is zone-blind: no relocation."""
        adds = _screen(True, 0.0, prices=_zonal(70.0))
        built = {z for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
        self.assertEqual(built, {BUCKET_SOLAR})


class TestNoZonalInputIsNeverARelocation(unittest.TestCase):
    """Missing zonal inputs fall back to the bucket, never to zone 0."""

    def test_absent_cf_profiles_keep_the_bucket(self):
        _, adds = apply_economic_new_entry(
            [],
            np.full(8760, 70.0),
            2030,
            _config(True),
            "MISO",
            rps_shadow_price=30.0,
            zone_names=ZONES,
        )
        built = {z for z, t in adds.items() if t.get("solar", 0.0) > 0.0}
        self.assertEqual(built, {BUCKET_SOLAR})


class TestMisoIsArmedAndOthersAreNot(unittest.TestCase):
    """Rule 25 [R-ISO-SCOPE]: the arming is MISO's alone."""

    def test_scenario_default_is_off(self):
        self.assertFalse(ScenarioConfig().entry_vre_zone_selection)

    def test_only_miso_overrides_it(self):
        armed = {
            iso
            for iso in (
                "ERCOT",
                "CAISO",
                "PJM",
                "MISO",
                "NYISO",
                "NEISO",
                "SPP",
                "NWPP",
                "SOCO",
            )
            if get_iso_config(iso).default_scenario_overrides.get(
                "entry_vre_zone_selection"
            )
        }
        self.assertEqual(armed, {"MISO"})

    def test_default_cache_key_is_byte_stable(self):
        # 2026-09-02: 603c2498bf71d21d -> cedadc285f8603b9, the owner-authorized
        # capx D41 key ADVANCE (`11af6f1c`; cause block and blast radius in
        # tests/regression/test_persisted_identity.py beside
        # PINNED_DEFAULT_CACHE_KEY). D41 swept every other pin and missed this
        # one; re-pinned to the same authorized value by the fast-tier repair
        # lane. Not a re-baseline to silence red: the two re-identified CCS
        # fixed-cost fields are hashed at every value, so registration is not
        # a remedy and re-pinning is the sanctioned route.
        # 2026-09-03: cedadc285f8603b9 -> 4c6b03ae098b6e3e, capx D44's declared
        # flip of fossil_announced_exits_enabled (owner ruling Q30). That field
        # IS registered, and the key moving is what capx D24-R (b'-1) exists to
        # make happen — the drop is at the FROZEN declaration, so the armed
        # default enters the hash instead of colliding with the pre-flip bundle.
        # ADVANCED 2026-09-06, e5ecd4105ada3e58 -> 547053bdfccd4264 — capx D65-B's
        # COUPLED ccs_retrofit_fixed_cost_co2_scaling (Act A, a declared (b'-1)
        # default flip) + ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$ (Act B, a
        # plain value field with no drop value, so it re-keys unconditionally).
        # Nothing about THIS file's mechanism moved — the pin advances because the
        # global default did. Rationale and provenance live on the pin in
        # tests/regression/test_persisted_identity.py; pre-declared BEFORE the solve
        # in docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3. Re-pinned here by
        # capx D65-B-R, completing the partial re-key fb93b76e left behind.
        self.assertEqual(ScenarioConfig().cache_key(), "547053bdfccd4264")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
