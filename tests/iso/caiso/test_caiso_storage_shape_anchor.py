"""Tests for the caiso-99 measured battery dispatch-shape envelope.

Covers the three seams of ``caiso_storage_shape_anchor`` (Mechanism B,
FINDING-caiso98 §7B): the cap builder
(:func:`market_sim.model.storage.caiso_storage_shape_caps`), the LP bound
application (``dispatch.build_variable_bounds`` charge/discharge caps), and
the config rule-19 exclusivity validator. Trivial cases first (1 unit, 24 h)
per the repo testing pattern.
"""

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.storage import StorageUnit, caiso_storage_shape_caps


def _unit(tech: str = "li_ion", power: float = 1000.0) -> StorageUnit:
    return StorageUnit(
        unit_id=f"test_{tech}",
        zone="NP15",
        tech_name=tech,
        power_cap_mw=power,
        energy_cap_mwh=power * 4.0,
        eta_charge=0.92,
        eta_discharge=0.92,
        zone_idx=0,
    )


class TestCaisoStorageShapeCaps:
    def test_battery_capped_below_power_cap_in_belly(self):
        """A battery's belly charge cap is the envelope fraction of its cap."""
        units = [_unit()]
        power_cap = np.array([1000.0])
        chg, dis = caiso_storage_shape_caps(power_cap, units, 2025, 8760)
        assert chg.shape == (1, 8760)
        hod = np.arange(8760) % 24
        belly = np.isin(hod, range(10, 15))
        # Measured 2025 belly charge p95 ~0.47-0.53 of fleet MW — far below
        # nameplate; the envelope must bind well under the power cap.
        assert chg[0, belly].max() < 700.0
        assert chg[0, belly].min() > 300.0
        # Evening discharge p95 ~0.5-0.65 — bounded but nonzero.
        evening = np.isin(hod, range(17, 22))
        assert 300.0 < dis[0, evening].max() < 800.0

    def test_pumped_storage_passes_through(self):
        """PS rows keep the full power cap (not an LESR, absent from OTH)."""
        units = [_unit("pumped_storage")]
        power_cap = np.array([500.0])
        chg, dis = caiso_storage_shape_caps(power_cap, units, 2024, 48)
        assert np.allclose(chg, 500.0)
        assert np.allclose(dis, 500.0)

    def test_composes_with_hour_varying_power_cap(self):
        """A 2-D (vintage-ramped) power cap scales per hour."""
        units = [_unit()]
        power_cap = np.full((1, 48), 1000.0)
        power_cap[0, 24:] = 2000.0  # capacity steps up at hour 24
        chg, _dis = caiso_storage_shape_caps(power_cap, units, 2024, 48)
        # Same hod ⇒ the cap doubles with the fleet step.
        assert chg[0, 36] == pytest.approx(2.0 * chg[0, 12])

    def test_forward_year_reuses_latest_envelope(self):
        """A year beyond the derived span falls back to the latest shape."""
        units = [_unit()]
        power_cap = np.array([1000.0])
        chg_fwd, _ = caiso_storage_shape_caps(power_cap, units, 2030, 24)
        chg_2025, _ = caiso_storage_shape_caps(power_cap, units, 2025, 24)
        assert np.allclose(chg_fwd, chg_2025)

    def test_missing_envelope_raises(self, monkeypatch, tmp_path):
        """A gated mechanism must never silently no-op (caiso-98 lesson)."""
        from market_sim.config import paths

        monkeypatch.setattr(paths, "RAW_DIR", tmp_path)
        with pytest.raises(FileNotFoundError, match="derive_caiso_storage_shape"):
            caiso_storage_shape_caps(np.array([100.0]), [_unit()], 2024, 24)


class TestDispatchChargeCapBounds:
    def _bounds(self, **kw):
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays
        from market_sim.model.dispatch import VariableLayout, build_variable_bounds

        T = 24
        fleet = generators_to_fleet_arrays(
            [
                Generator(
                    unit_id="G0",
                    name="G0",
                    zone="Z0",
                    fuel_type="gas_cc",
                    pmax_mw=100.0,
                    pmin_mw=0.0,
                    eford=0.0,
                )
            ],
            ["Z0"],
            hours=T,
        )
        layout = VariableLayout(T=T, n_gen=1, n_zones=1, n_storage=1, n_links=0)
        lower, upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            **kw,
        )
        return layout, lower, upper

    def test_charge_cap_tightens_chg_only(self):
        layout, _lower, upper = self._bounds(
            storage_charge_cap=np.full((1, 24), 30.0),
        )
        chg_cols = upper[layout._chg_off :: layout.vars_per_hour]
        dis_cols = upper[layout._dis_off :: layout.vars_per_hour]
        assert np.allclose(chg_cols, 30.0)
        assert np.allclose(dis_cols, 50.0)  # discharge untouched

    def test_discharge_cap_tightens_dis_only(self):
        layout, _lower, upper = self._bounds(
            storage_discharge_cap=np.full((1, 24), 20.0),
        )
        chg_cols = upper[layout._chg_off :: layout.vars_per_hour]
        dis_cols = upper[layout._dis_off :: layout.vars_per_hour]
        assert np.allclose(chg_cols, 50.0)
        assert np.allclose(dis_cols, 20.0)

    def test_caps_clip_at_power_cap(self):
        """An envelope above the power cap can only pass the cap through."""
        layout, _lower, upper = self._bounds(
            storage_charge_cap=np.full((1, 24), 500.0),
        )
        chg_cols = upper[layout._chg_off :: layout.vars_per_hour]
        assert np.allclose(chg_cols, 50.0)

    def test_none_is_byte_identical(self):
        _, l0, u0 = self._bounds()
        _, l1, u1 = self._bounds(storage_charge_cap=None, storage_discharge_cap=None)
        assert np.array_equal(u0, u1) and np.array_equal(l0, l1)


class TestConfigValidator:
    def test_shape_anchor_excludes_as_reservation(self):
        with pytest.raises(ValueError, match="rule 19"):
            ScenarioConfig(
                caiso_storage_shape_anchor=True,
                caiso_storage_as_reservation=True,
            )

    def test_shape_anchor_alone_is_valid(self):
        cfg = ScenarioConfig(caiso_storage_shape_anchor=True)
        assert cfg.caiso_storage_shape_anchor
