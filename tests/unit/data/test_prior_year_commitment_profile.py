"""Tests for the R-ERCOT-19 prior-year commitment-profile sub-gates.

``cc_committed_prior_year_commitment_eligibility`` (the ERCOT-139 CC committed
block weighted by the plant's prior-year online share) and
``netload_drag_prior_year_hour_profile`` (the ST_GAS drag floor reshaped by the
same measured profile), plus the shared loader's fail-closed gates.
"""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.commitment_profile import (
    _read_artifact,
    load_prior_year_commitment_profile,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.fleet.floors import (
    _prior_hour_shape,
    apply_gas_st_netload_drag_floor,
)
from market_sim.data.fleet.models import Generator
from market_sim.data.offer_curves import apply_cc_committed_offer_margin

T = 8760


def _write_profile(d: Path) -> None:
    """Two metered plants in vintage 2021 (one CC, one ST) + one unmetered CC."""
    lines = ["iso,plant_code,klass,year,month,hour,on_frac,metered,source_sha256"]
    for m in range(1, 13):
        for h in range(24):
            lines.append(
                f"ERCOT,900,CC_REGULAR,2021,{m},{h},{1.0 if h >= 12 else 0.0},True,x"
            )
            lines.append(f"ERCOT,901,CC_REGULAR,2021,{m},{h},,False,x")
            lines.append(
                f"ERCOT,800,ST_GAS,2021,{m},{h},{0.5 if h >= 12 else 0.0},True,x"
            )
    (d / "ercot_prior_year_commitment_profile.csv").write_text("\n".join(lines) + "\n")


class _ProfileDir:
    """Context manager: a temp CALIBRATION_DIR holding the synthetic artifact."""

    def __enter__(self):
        self._td = tempfile.TemporaryDirectory()
        d = Path(self._td.name)
        _write_profile(d)
        _read_artifact.cache_clear()
        self._patch = unittest.mock.patch("market_sim.config.paths.CALIBRATION_DIR", d)
        self._patch.start()
        return d

    def __exit__(self, *exc):
        self._patch.stop()
        _read_artifact.cache_clear()
        self._td.cleanup()


def _cfg(**kw):
    base = dict(
        mode="backcast",
        weather_year=2022,
        cc_committed_offer_margin=True,
        cc_committed_offer_level=10.354,
        gas_offer_margin_anchor=2.2494,
    )
    base.update(kw)
    return ScenarioConfig(**base)


def _cc_gens():
    """A metered CC (900), an unmetered CC (901): committed + econ rows."""
    out = []
    for code in (900, 901):
        shared = dict(
            name=f"C{code}",
            zone="South",
            fuel_type="gas_cc",
            online_year=2000,
            plant_group="CC_REGULAR",
            plant_code=code,
            is_campd_bin=True,
            vom=2.0,
        )
        out += [
            Generator(
                unit_id=f"CC_REGULAR_South_p{code}_committed",
                pmax_mw=100.0,
                heat_rate=10.0,
                **shared,
            ),
            Generator(
                unit_id=f"CC_REGULAR_South_p{code}_econc00",
                pmax_mw=50.0,
                heat_rate=11.0,
                **shared,
            ),
        ]
    return out


def _cc_mc(cfg, year):
    gens = _cc_gens()
    fa = generators_to_fleet_arrays(gens, ["South"], hours=T)
    mc = (fa.heat_rate[:, None] * 3.0 + fa.vom[:, None]) * np.ones((1, T))
    apply_cc_committed_offer_margin(mc, gens, fa, cfg, year)
    return gens, fa, mc


class TestLoader(unittest.TestCase):
    """The shared loader's gates: flag, backcast, vintage Y-1, class, metered."""

    def test_off_returns_none(self):
        with _ProfileDir():
            self.assertIsNone(
                load_prior_year_commitment_profile(
                    _cfg(),
                    "ERCOT",
                    2022,
                    "CC_REGULAR",
                    "cc_committed_prior_year_commitment_eligibility",
                    T,
                )
            )

    def test_forecast_refuses_both_flags(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(cc_committed_prior_year_commitment_eligibility=True)
        with self.assertRaises(ValueError):
            ScenarioConfig(netload_drag_prior_year_hour_profile=True)

    def test_reads_prior_vintage_metered_class_only(self):
        cfg = _cfg(cc_committed_prior_year_commitment_eligibility=True)
        with _ProfileDir():
            got = load_prior_year_commitment_profile(
                cfg,
                "ERCOT",
                2022,
                "CC_REGULAR",
                "cc_committed_prior_year_commitment_eligibility",
                T,
            )
        self.assertEqual(set(got), {900})
        q = got[900]
        self.assertEqual(q.shape, (T,))
        self.assertEqual(q[0], 0.0)  # Jan 1, hour 0
        self.assertEqual(q[13], 1.0)  # Jan 1, hour 13

    def test_missing_vintage_fails_closed(self):
        cfg = _cfg(
            weather_year=2019, cc_committed_prior_year_commitment_eligibility=True
        )
        with _ProfileDir():
            self.assertIsNone(
                load_prior_year_commitment_profile(
                    cfg,
                    "ERCOT",
                    2019,
                    "CC_REGULAR",
                    "cc_committed_prior_year_commitment_eligibility",
                    T,
                )
            )


class TestCCEligibility(unittest.TestCase):
    """The committed-block shift is weighted by q; q=1 hours equal the keeper."""

    def test_off_is_byte_identical(self):
        with _ProfileDir():
            _, _, keeper = _cc_mc(_cfg(), 2022)
            _, _, no_year = _cc_mc(
                _cfg(cc_committed_prior_year_commitment_eligibility=True), None
            )
        np.testing.assert_array_equal(keeper, no_year)

    def test_weights_only_the_metered_committed_row(self):
        with _ProfileDir():
            gens, _, keeper = _cc_mc(_cfg(), 2022)
            _, _, arm = _cc_mc(
                _cfg(cc_committed_prior_year_commitment_eligibility=True), 2022
            )
        ids = [g.unit_id for g in gens]
        c900 = ids.index("CC_REGULAR_South_p900_committed")
        hod = np.arange(T) % 24
        # q = 1 hours: exactly the keeper's measured-level bid.
        np.testing.assert_array_equal(arm[c900, hod >= 12], keeper[c900, hod >= 12])
        # q = 0 hours: the band's registered multiplier form (untouched mc).
        np.testing.assert_allclose(arm[c900, hod < 12], 10.0 * 3.0 + 2.0)
        # Unmetered plant and every econ row: identical to the keeper.
        for uid in (
            "CC_REGULAR_South_p901_committed",
            "CC_REGULAR_South_p900_econc00",
            "CC_REGULAR_South_p901_econc00",
        ):
            i = ids.index(uid)
            np.testing.assert_array_equal(arm[i], keeper[i])


def _st_gens():
    out = []
    for code in (800, 802):
        shared = dict(
            name=f"S{code}",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=code,
        )
        out += [
            Generator(
                unit_id=f"p{code}_committed", pmax_mw=100.0, heat_rate=10.0, **shared
            ),
            Generator(
                unit_id=f"p{code}_econc00", pmax_mw=100.0, heat_rate=11.0, **shared
            ),
        ]
    return out


def _drag(profile):
    gens = _st_gens()
    fa = generators_to_fleet_arrays(gens, ["North"], hours=T)
    cfg = ScenarioConfig(
        gas_st_netload_drag=True,
        gas_st_drag_slope_per_gw=0.00906,
        gas_st_drag_intercept=-0.1376,
        gas_st_drag_cap=0.34,
    )
    apply_gas_st_netload_drag_floor(
        fa, gens, np.full(T, 30_000.0), cfg, hour_profile=profile
    )
    return gens, fa


class TestDragHourProfile(unittest.TestCase):
    """Hour-eligibility only: same annual nominal floor, moved to committed hours."""

    def test_none_is_byte_identical(self):
        _, a = _drag(None)
        _, b = _drag({})
        np.testing.assert_array_equal(a.min_gen, b.min_gen)

    def test_delivered_is_preserved_when_the_clip_binds(self):
        """A lay-up-like hole in the basis: pro-rata loses it, the shape must not gain it."""
        q = np.where(np.arange(T) % 24 >= 12, 0.5, 0.0)
        gens, keeper = _drag(None)
        _, arm = _drag({800: q, 802: np.full(T, 0.3)})
        for code in (800, 802):
            rows = [i for i, g in enumerate(gens) if g.plant_code == code]
            self.assertAlmostEqual(
                float(arm.min_gen[rows].sum()),
                float(keeper.min_gen[rows].sum()),
                places=3,
            )

    def test_shape_is_mean_one_and_skips_dark_plants(self):
        q = np.where(np.arange(T) % 24 >= 12, 0.5, 0.0)
        s = _prior_hour_shape({800: q, 802: np.zeros(T)}, T)
        self.assertEqual(set(s), {800})
        self.assertAlmostEqual(float(s[800].mean()), 1.0, places=12)

    def test_floor_moves_off_dark_hours_and_keeps_its_annual_nominal(self):
        q = np.where(np.arange(T) % 24 >= 12, 0.5, 0.0)
        gens, keeper = _drag(None)
        _, arm = _drag({800: q})
        hod = np.arange(T) % 24
        for i, g in enumerate(gens):
            if g.plant_code == 800:
                self.assertEqual(float(arm.min_gen[i, hod < 12].sum()), 0.0)
                # Delivered energy is preserved per plant (aggregate-neutral).
                self.assertAlmostEqual(
                    float(arm.min_gen[i].sum()),
                    float(keeper.min_gen[i].sum()),
                    places=4,
                )
            else:
                np.testing.assert_array_equal(arm.min_gen[i], keeper.min_gen[i])


if __name__ == "__main__":
    unittest.main()
