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
    load_as_thermal_withholding,
)

HOURS = 8760


def _gen(uid: str, group: str, fuel: str, pmax: float, code: int) -> Generator:
    return Generator(
        unit_id=uid, name=uid, plant_group=group, fuel_type=fuel,
        pmax_mw=pmax, heat_rate=8.0, zone="Z0", eford=0.0, plant_code=code,
    )


class TestLoader:
    def test_loads_2024_system_total(self):
        """The NP3-911 system-total parquet loads as a positive series."""
        s = load_as_reserve_withholding_mw(2024, HOURS)
        assert s is not None and s.shape == (HOURS,)
        assert s.min() > 1_000.0
        assert 4_000.0 < s.mean() < 12_000.0

    def test_loads_2024_per_type(self):
        """The per-resource-type parquet loads the thermal columns only."""
        d = load_as_thermal_withholding(2024, HOURS)
        assert d is not None
        assert set(d) == {"gas_cc", "gas_ct", "gas_st", "coal"}
        assert all(v.shape == (HOURS,) for v in d.values())
        # Measured thermal AS is a few hundred MW per class — far below the
        # ~7 GW system total, since storage/load carry the bulk.
        assert 100.0 < sum(v.mean() for v in d.values()) < 2_000.0

    def test_missing_year_returns_none(self):
        """A year with no parquet no-ops (returns None), never raises."""
        assert load_as_reserve_withholding_mw(1999, HOURS) is None
        assert load_as_thermal_withholding(1999, HOURS) is None


class TestWithholding:
    def _fleet(self, config: ScenarioConfig, iso: str = "ERCOT"):
        # A large gas unit and a coal unit (both carry a measured AS share so
        # both should be cut) plus a wind unit that must stay untouched.
        gens = [
            _gen("cc1", "CC_REGULAR", "gas_cc", 60_000.0, 1),
            _gen("co1", "COAL", "coal", 30_000.0, 2),
            _gen("wind1", "WIND", "wind", 5_000.0, 3),
        ]
        return generators_to_fleet_arrays(
            gens, ["Z0"], hours=HOURS, iso=iso, config=config
        )

    def test_on_withholds_measured_per_class(self):
        """Each thermal class is cut by its own measured AS; wind untouched."""
        off = self._fleet(ScenarioConfig(iso="ERCOT", weather_year=2024))
        on = self._fleet(ScenarioConfig(
            iso="ERCOT", weather_year=2024, as_reserve_withholding=True))
        by_class = load_as_thermal_withholding(2024, HOURS)
        # Single-unit pool per class -> exact cut of class_mw / pmax.
        np.testing.assert_allclose(
            on.availability[0], off.availability[0] - by_class["gas_cc"] / 60_000.0,
            atol=1e-9,
        )
        np.testing.assert_allclose(
            on.availability[1], off.availability[1] - by_class["coal"] / 30_000.0,
            atol=1e-9,
        )
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
        """Availability stays in [0, 1] even when AS exceeds class headroom."""
        cfg = ScenarioConfig(
            iso="ERCOT", weather_year=2024, as_reserve_withholding=True
        )
        # Tiny gas fleet vs its (sub-GW but non-trivial) measured AS.
        gens = [_gen("cc1", "CC_REGULAR", "gas_cc", 200.0, 1)]
        fa = generators_to_fleet_arrays(
            gens, ["Z0"], hours=HOURS, iso="ERCOT", config=cfg
        )
        assert fa.availability.min() >= 0.0
        assert fa.availability.max() <= 1.0



class TestStorageAsCommitment:
    """Reserving measured storage up-AS MW from the battery power cap."""

    def test_reserves_as_pro_rata(self):
        from market_sim.model.storage import reserve_storage_as_power
        import pandas as pd
        asr = pd.read_parquet(
            "inputs/raw-data/ercot-AS/ercot_2024_as_by_restype_hourly.parquet"
        )["storage"].to_numpy(dtype=float)
        pc = np.array([4000.0, 2500.0])  # 6.5 GW across two units
        out = reserve_storage_as_power(pc, 2024, HOURS)
        assert out.shape == (2, HOURS)
        # Fleet power after = 6500 - storage_AS (floored at 0).
        np.testing.assert_allclose(
            out.sum(axis=0), np.clip(6500.0 - asr, 0.0, None), atol=1e-6
        )
        # Allocation stays pro-rata by unit power.
        np.testing.assert_allclose(
            out[0], (4000.0 / 6500.0) * out.sum(axis=0), atol=1e-6
        )
        assert out.min() >= 0.0

    def test_missing_year_passthrough(self):
        from market_sim.model.storage import reserve_storage_as_power
        pc = np.array([4000.0, 2500.0])
        out = reserve_storage_as_power(pc, 1999, HOURS)
        np.testing.assert_array_equal(out, pc)
