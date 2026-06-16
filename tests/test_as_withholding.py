"""Tests for the ERCOT ancillary-service reserve-withholding probe.

The feature removes the hourly cleared DAM up-AS MW (built by
``scripts/build_ercot_as_withholding.py``) from thermal headroom before the
energy supply curve clears, an ERCOT-only upper bound that books all AS to
thermal. See ``ScenarioConfig.as_reserve_withholding`` and
``fleet.generators_to_fleet_arrays``.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    generators_to_fleet_arrays,
    load_as_reserve_withholding_mw,
)

HOURS = 8760


def _gen(uid: str, group: str, fuel: str, pmax: float, code: int) -> Generator:
    return Generator(
        unit_id=uid, name=uid, plant_group=group, fuel_type=fuel,
        pmax_mw=pmax, heat_rate=8.0, zone="Z0", eford=0.0, plant_code=code,
    )


class TestLoader:
    def test_loads_2024_series(self):
        """The built 2024 parquet loads as a positive (hours,) MW series."""
        s = load_as_reserve_withholding_mw(2024, HOURS)
        assert s is not None
        assert s.shape == (HOURS,)
        # ERCOT cleared up-AS sits in the multi-GW band every hour.
        assert s.min() > 1_000.0
        assert 4_000.0 < s.mean() < 12_000.0

    def test_missing_year_returns_none(self):
        """A year with no parquet no-ops (returns None), never raises."""
        assert load_as_reserve_withholding_mw(1999, HOURS) is None


class TestWithholding:
    def _fleet(self, config: ScenarioConfig, iso: str = "ERCOT"):
        # A large gas unit (so the multi-GW AS is a partial cut, not a full
        # zero-out), a coal unit that must stay untouched (gas-only pool), and
        # a wind unit that must stay untouched (non-thermal).
        gens = [
            _gen("cc1", "CC_REGULAR", "gas_cc", 60_000.0, 1),
            _gen("co1", "COAL", "coal", 5_000.0, 2),
            _gen("wind1", "WIND", "wind", 5_000.0, 3),
        ]
        return generators_to_fleet_arrays(
            gens, ["Z0"], hours=HOURS, iso=iso, config=config
        )

    def test_on_removes_as_from_gas_only(self):
        """Flag on cuts gas headroom by the AS series; coal and wind untouched.

        The cut composes with the existing seasonal WEFOR derate, so the test
        compares the flag-on fleet against the flag-off baseline rather than a
        bare 1.0. For a single gas unit the top-down withdrawal is exactly
        ``as_mw / pmax`` of nameplate each hour.
        """
        off = self._fleet(ScenarioConfig(iso="ERCOT", weather_year=2024))
        on = self._fleet(ScenarioConfig(
            iso="ERCOT", weather_year=2024, as_reserve_withholding=True))
        as_mw = load_as_reserve_withholding_mw(2024, HOURS)
        np.testing.assert_allclose(
            on.availability[0], off.availability[0] - as_mw / 60_000.0,
            atol=1e-9,
        )
        # Gas headroom genuinely fell; coal and wind are untouched.
        assert on.availability[0].max() < off.availability[0].max()
        np.testing.assert_allclose(on.availability[1], off.availability[1])
        np.testing.assert_allclose(on.availability[2], off.availability[2])

    def test_non_ercot_iso_unaffected(self):
        """The withholding is ERCOT-scoped; other ISOs see no effect."""
        off = self._fleet(
            ScenarioConfig(iso="PJM", weather_year=2024), iso="PJM")
        on = self._fleet(
            ScenarioConfig(iso="PJM", weather_year=2024,
                           as_reserve_withholding=True),
            iso="PJM")
        np.testing.assert_allclose(on.availability[0], off.availability[0])

    def test_never_below_zero(self):
        """When AS exceeds thermal headroom, availability floors at zero."""
        cfg = ScenarioConfig(
            iso="ERCOT", weather_year=2024, as_reserve_withholding=True
        )
        # Tiny thermal fleet (1 GW) vs multi-GW AS: fully withheld, not negative.
        gens = [_gen("cc1", "CC_REGULAR", "gas_cc", 1_000.0, 1)]
        fa = generators_to_fleet_arrays(
            gens, ["Z0"], hours=HOURS, iso="ERCOT", config=cfg
        )
        assert fa.availability.min() >= 0.0
        assert fa.availability[0].max() == pytest.approx(0.0)
