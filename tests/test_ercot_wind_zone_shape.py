"""Pin both sides of ``ScenarioConfig.ercot_wind_zone_shape`` (ERCOT-113).

The gate gives each ERCOT zone its own MERRA-2 reanalysis wind SHAPE instead of
one ISO-wide hourly profile. It is keeper-affecting, so the invariants that
matter are:

* it is **default-off** and an unarmed config is byte-identical to its pre-gate
  self (no cache-key move, no shape returned);
* MISO stays **unconditional** — its shape does not depend on the new gate, and
  it resolves to the same directory through the path registry as it did from
  the old hardcoded default;
* an ISO with no registered wind-shape directory no-ops rather than raising.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.paths import MISO_WIND_SHAPE_DIR, wind_shape_dir
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.renewables import (
    _WIND_ZONE_SHAPE_GATES,
    _WIND_ZONE_SHAPE_ISOS,
    _wind_zone_reanalysis_shapes,
    _wind_zone_shape_enabled,
)

_ERCOT_SHAPE = wind_shape_dir("ERCOT")
_YEAR = 2024


def _zone_names(iso: str) -> list[str] | None:
    """Zone columns of an ISO's committed wind-shape parquet, or ``None``."""
    d = wind_shape_dir(iso)
    if d is None:
        return None
    path = d / f"{iso.lower()}_{_YEAR}_wind_zone_shape.parquet"
    if not path.exists():
        return None
    return [c for c in pd.read_parquet(path).columns if c != "hour"]


class TestGateDefault:
    """The gate is off by default and inert at its default."""

    def test_default_is_off(self) -> None:
        assert ScenarioConfig().ercot_wind_zone_shape is False

    def test_registered_as_cache_key_optional(self) -> None:
        assert "ercot_wind_zone_shape" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_cache_key_unchanged_at_default(self) -> None:
        assert (
            ScenarioConfig().cache_key()
            == ScenarioConfig(ercot_wind_zone_shape=False).cache_key()
        )

    def test_cache_key_moves_when_armed(self) -> None:
        assert (
            ScenarioConfig().cache_key()
            != ScenarioConfig(ercot_wind_zone_shape=True).cache_key()
        )


class TestEnablement:
    """``_wind_zone_shape_enabled`` gates ERCOT but never MISO."""

    def test_miso_unconditional(self) -> None:
        assert "MISO" in _WIND_ZONE_SHAPE_ISOS
        assert _wind_zone_shape_enabled("MISO", ScenarioConfig()) is True
        assert _wind_zone_shape_enabled("MISO", None) is True

    def test_ercot_is_gated(self) -> None:
        assert _WIND_ZONE_SHAPE_GATES["ERCOT"] == "ercot_wind_zone_shape"
        assert _wind_zone_shape_enabled("ERCOT", ScenarioConfig()) is False
        assert (
            _wind_zone_shape_enabled(
                "ERCOT", ScenarioConfig(ercot_wind_zone_shape=True)
            )
            is True
        )

    def test_unregistered_iso_never_enabled(self) -> None:
        assert _wind_zone_shape_enabled("PJM", ScenarioConfig()) is False


class TestShapeLoader:
    """The loader no-ops when unarmed and returns a per-zone matrix when armed."""

    @pytest.mark.skipif(
        _zone_names("ERCOT") is None, reason="ERCOT wind-shape artifact absent"
    )
    def test_ercot_noop_when_gate_off(self) -> None:
        zn = _zone_names("ERCOT")
        assert (
            _wind_zone_reanalysis_shapes(
                "ERCOT", "wind", zn, _YEAR, config=ScenarioConfig()
            )
            is None
        )

    @pytest.mark.skipif(
        _zone_names("ERCOT") is None, reason="ERCOT wind-shape artifact absent"
    )
    def test_ercot_shape_when_armed(self) -> None:
        zn = _zone_names("ERCOT")
        shapes = _wind_zone_reanalysis_shapes(
            "ERCOT",
            "wind",
            zn,
            _YEAR,
            config=ScenarioConfig(ercot_wind_zone_shape=True),
        )
        assert shapes is not None
        assert shapes.shape == (len(zn), 8760)
        assert np.isfinite(shapes).all()
        assert (shapes >= 0.0).all()
        # The zones must not be one averaged profile — that is the whole point.
        assert not np.allclose(shapes[0], shapes[-1])

    @pytest.mark.skipif(
        _zone_names("MISO") is None, reason="MISO wind-shape artifact absent"
    )
    def test_miso_unchanged_by_the_new_gate(self) -> None:
        """MISO resolves through the registry to its old hardcoded directory."""
        zn = _zone_names("MISO")
        assert wind_shape_dir("MISO") == MISO_WIND_SHAPE_DIR
        off = _wind_zone_reanalysis_shapes(
            "MISO", "wind", zn, _YEAR, config=ScenarioConfig()
        )
        on = _wind_zone_reanalysis_shapes(
            "MISO", "wind", zn, _YEAR, config=ScenarioConfig(ercot_wind_zone_shape=True)
        )
        assert off is not None
        np.testing.assert_array_equal(off, on)

    def test_non_wind_fuel_noops(self) -> None:
        assert (
            _wind_zone_reanalysis_shapes(
                "ERCOT",
                "solar",
                ["West"],
                _YEAR,
                config=ScenarioConfig(ercot_wind_zone_shape=True),
            )
            is None
        )

    def test_unregistered_iso_noops_without_raising(self) -> None:
        assert wind_shape_dir("NYISO") is None
        assert (
            _wind_zone_reanalysis_shapes(
                "NYISO", "wind", ["A"], _YEAR, config=ScenarioConfig()
            )
            is None
        )
