"""Tests for the NYISO condition-varying reserve-requirement channel (#1344).

Covers the measured-series loader (``data.nyiso_reserve_requirements``), the
``_nyiso_design`` hourly-requirement path behind
``ScenarioConfig.nyiso_dynamic_reserve_requirements`` (default-off
byte-identical, hard-error without the Ask-B intake), and the rule-19
mutual-exclusion guard between the in-LP co-opt families and the post-solve
RCPF overlay (``nyiso_rcpf_enabled``).
"""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from market_sim.config.reserve_config import _nyiso_design
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.nyiso_reserve_requirements import (
    FAMILY_BY_REGION_PRODUCT,
    load_nyiso_reserve_requirements,
)

T = 48
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]


def _fa():
    """One reserve-eligible gas unit per zone, flat availability."""
    n = len(ZONES)
    return FleetArrays(
        pmax=np.full(n, 1000.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.arange(n),
        fuel_type_idx=np.full(n, FUEL_TYPE_MAP["gas_ct"]),
        availability=np.ones((n, T)),
        unit_ids=[f"g{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.zeros(n, dtype=int),
    )


def _config(**overrides):
    base = dict(
        iso="NYISO",
        weather_year=2024,
        nyiso_rcpf_products=None,
        nyiso_rcpf_locational=None,
        nyiso_synchronised_reserve=False,
        nyiso_rcpf_enabled=False,
        nyiso_dynamic_reserve_requirements=False,
        commitment_enabled=False,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _write_series(path, hours, rows):
    """Write a synthetic requirement CSV: rows = [(region, product, base_mw)]."""
    ts = pd.date_range("2024-01-01", periods=hours, freq="h")
    frames = []
    for region, product, base in rows:
        frames.append(
            pd.DataFrame(
                {
                    "Time Stamp": ts,
                    "region": region,
                    "product": product,
                    "requirement_mw": base + np.arange(hours, dtype=float),
                }
            )
        )
    pd.concat(frames).to_csv(path, index=False)


class TestLoader:
    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="Ask-B"):
            load_nyiso_reserve_requirements(2024, T, path=tmp_path / "absent.csv")

    def test_loads_and_maps_families(self, tmp_path):
        p = tmp_path / "req.csv"
        _write_series(
            p, T, [("NYC", "10min_total", 500.0), ("SENY", "30min_total", 1100.0)]
        )
        out = load_nyiso_reserve_requirements(2024, T, path=p)
        assert set(out) == {"nyc_10min_total", "seny_30min_total"}
        np.testing.assert_allclose(
            out["nyc_10min_total"], 500.0 + np.arange(T, dtype=float)
        )

    def test_short_series_raises(self, tmp_path):
        p = tmp_path / "req.csv"
        _write_series(p, T - 1, [("NYC", "10min_total", 500.0)])
        with pytest.raises(ValueError, match="covers"):
            load_nyiso_reserve_requirements(2024, T, path=p)

    def test_unknown_region_product_raises(self, tmp_path):
        p = tmp_path / "req.csv"
        _write_series(p, T, [("NYC", "5min_total", 500.0)])
        with pytest.raises(ValueError, match="unknown"):
            load_nyiso_reserve_requirements(2024, T, path=p)

    def test_family_map_matches_design_names(self):
        cfg = _config()
        design = _nyiso_design(cfg, _fa(), T, ZONES)
        names = {f.name for f in design.families}
        assert set(FAMILY_BY_REGION_PRODUCT.values()) <= names


class TestDesignChannel:
    def test_default_off_static_requirements(self):
        design = _nyiso_design(_config(), _fa(), T, ZONES)
        for fam in design.families:
            assert fam.requirement.shape == (T,)
            assert np.all(fam.requirement == fam.requirement[0])

    def test_flag_without_data_raises(self):
        cfg = _config(nyiso_dynamic_reserve_requirements=True, weather_year=1999)
        with pytest.raises(FileNotFoundError, match="Ask-B"):
            _nyiso_design(cfg, _fa(), T, ZONES)

    def test_dynamic_series_replaces_family_requirement(self, monkeypatch):
        series = {"nyc_10min_total": 500.0 + np.arange(T, dtype=float)}
        monkeypatch.setattr(
            "market_sim.data.nyiso_reserve_requirements."
            "load_nyiso_reserve_requirements",
            lambda year, hours, path=None: series,
        )
        cfg = _config(nyiso_dynamic_reserve_requirements=True)
        design = _nyiso_design(cfg, _fa(), T, ZONES)
        by_name = {f.name: f for f in design.families}
        np.testing.assert_allclose(
            by_name["nyc_10min_total"].requirement, series["nyc_10min_total"]
        )
        # Families without a measured series keep the static published value.
        static = by_name["nyca_30min_total"].requirement
        assert np.all(static == static[0])
        # ORDC step shape stays anchored to the published static anchors.
        base = _nyiso_design(_config(), _fa(), T, ZONES)
        base_by_name = {f.name: f for f in base.families}
        np.testing.assert_allclose(
            by_name["nyc_10min_total"].ordc_penalties,
            base_by_name["nyc_10min_total"].ordc_penalties,
        )
        np.testing.assert_allclose(
            by_name["nyc_10min_total"].ordc_step_widths,
            base_by_name["nyc_10min_total"].ordc_step_widths,
        )


class TestMeasuredStepSpan:
    """``nyiso_ordc_measured_step_span`` — the ORDC width construction fix."""

    @staticmethod
    def _series():
        # SENY is the family whose measured requirement (1,800 MW) exceeds its
        # published base (1,300 MW); NYC's measured == published, so it is the
        # in-file no-op control.
        return {
            "seny_30min_total": np.full(T, 1800.0),
            "nyc_10min_total": np.full(T, 500.0),
        }

    def _designs(self, monkeypatch):
        monkeypatch.setattr(
            "market_sim.data.nyiso_reserve_requirements."
            "load_nyiso_reserve_requirements",
            lambda year, hours, path=None: self._series(),
        )
        off = _nyiso_design(
            _config(nyiso_dynamic_reserve_requirements=True), _fa(), T, ZONES
        )
        on = _nyiso_design(
            _config(
                nyiso_dynamic_reserve_requirements=True,
                nyiso_ordc_measured_step_span=True,
            ),
            _fa(),
            T,
            ZONES,
        )
        return {f.name: f for f in off.families}, {f.name: f for f in on.families}

    def test_default_off_is_byte_identical(self, monkeypatch):
        """Absent the flag the design is unchanged, widths still static 1-D."""
        off, _ = self._designs(monkeypatch)
        seny = off["seny_30min_total"]
        assert seny.ordc_step_widths.ndim == 1
        # The defect: RHS enforces 1,800 MW while the curve spans only 1,300.
        assert seny.requirement[0] == 1800.0
        assert seny.ordc_step_widths.sum() == pytest.approx(1300.0)

    def test_widths_span_the_measured_requirement(self, monkeypatch):
        off, on = self._designs(monkeypatch)
        seny_on = on["seny_30min_total"]
        # Hourly (n_steps, T), total width == the hour's measured requirement,
        # so the curve reaches its max penalty exactly at zero reserve.
        assert seny_on.ordc_step_widths.shape == (
            off["seny_30min_total"].ordc_step_widths.shape[0],
            T,
        )
        np.testing.assert_allclose(
            seny_on.ordc_step_widths.sum(axis=0), seny_on.requirement
        )

    def test_penalties_and_shape_are_untouched(self, monkeypatch):
        """Published RCPF penalties are requirement-independent — only widths move."""
        off, on = self._designs(monkeypatch)
        for name in ("seny_30min_total", "nyc_10min_total", "nyca_30min_total"):
            np.testing.assert_allclose(
                on[name].ordc_penalties, off[name].ordc_penalties
            )
            np.testing.assert_allclose(on[name].requirement, off[name].requirement)
        # Shape preserved: every width scales by the same requirement ratio.
        w_off = off["seny_30min_total"].ordc_step_widths
        w_on = on["seny_30min_total"].ordc_step_widths
        np.testing.assert_allclose(
            w_on, np.tile(w_off[:, None] * (1800.0 / 1300.0), (1, T))
        )

    def test_noop_where_measured_equals_static(self, monkeypatch):
        """NYC measured == published, so its curve must not move."""
        off, on = self._designs(monkeypatch)
        np.testing.assert_allclose(
            on["nyc_10min_total"].ordc_step_widths,
            off["nyc_10min_total"].ordc_step_widths[:, None] * np.ones(T),
        )

    def test_untouched_without_measured_series(self, monkeypatch):
        """A family with no measured series keeps its static 1-D widths."""
        _, on = self._designs(monkeypatch)
        assert on["nyca_30min_total"].ordc_step_widths.ndim == 1

    def test_inert_without_dynamic_requirements(self):
        """No measured series ⇒ nothing to translate to; design is unchanged."""
        base = _nyiso_design(_config(), _fa(), T, ZONES)
        armed = _nyiso_design(
            _config(nyiso_ordc_measured_step_span=True), _fa(), T, ZONES
        )
        for a, b in zip(armed.families, base.families):
            np.testing.assert_array_equal(a.ordc_step_widths, b.ordc_step_widths)

    def test_dispatch_kwargs_promote_to_hourly(self, monkeypatch):
        """Mixed static/hourly families stack into one (n_ordc_steps, T) bound."""
        from market_sim.model.reserves.spec import build_reserve_dispatch_kwargs

        monkeypatch.setattr(
            "market_sim.data.nyiso_reserve_requirements."
            "load_nyiso_reserve_requirements",
            lambda year, hours, path=None: self._series(),
        )
        design = _nyiso_design(
            _config(
                nyiso_dynamic_reserve_requirements=True,
                nyiso_ordc_measured_step_span=True,
            ),
            _fa(),
            T,
            ZONES,
        )
        kw = build_reserve_dispatch_kwargs(design)
        w = kw["ordc_step_widths"]
        assert w.shape == (kw["ordc_penalties"].shape[0], T)
        # A static family broadcasts its constant width across the horizon.
        n_dyn = sum(
            f.ordc_penalties.shape[0]
            for f in design.families
            if f.ordc_step_widths.ndim == 2
        )
        assert n_dyn > 0 and w.shape[0] > n_dyn
        assert np.all(w > 0)


class TestRule19Guard:
    def test_overlay_plus_coopt_raises(self):
        cfg = _config(nyiso_rcpf_enabled=True)
        with pytest.raises(ValueError, match="rule 19"):
            _nyiso_design(cfg, _fa(), T, ZONES)
