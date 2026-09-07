"""Tests for scripts/export_lce_lmp.py — the Scope 2 LCE Portfolio LMP export.

Data-free: exercises the zonal→ISO collapse math on synthetic arrays and the
CSV/sidecar shape on synthetic frames. No solver runs, no cached results, no
``lce_portfolio`` import (the consumer's validation is exercised separately;
the collapse semantics here mirror its ``collapse_zonal_lmp`` seam by
construction — load-weighted average, zero-load hour → simple mean).
"""

import importlib.util
import json

import numpy as np
import pandas as pd
import pytest
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "export_lce_lmp",
    REPO_ROOT / "scripts" / "export_lce_lmp.py",
)
xl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(xl)


class TestCollapseZonalPrices:
    def test_load_weighted_average(self):
        # 2 zones, 3 hours: hand-computed weighted means.
        prices = np.array([[10.0, 20.0, 30.0], [50.0, 40.0, 30.0]])
        loads = np.array([[1.0, 3.0, 2.0], [3.0, 1.0, 2.0]])
        out = xl.collapse_zonal_prices(prices, loads)
        expected = np.array(
            [
                (10 * 1 + 50 * 3) / 4,  # 40.0
                (20 * 3 + 40 * 1) / 4,  # 25.0
                (30 * 2 + 30 * 2) / 4,  # 30.0
            ]
        )
        np.testing.assert_allclose(out, expected)

    def test_zero_load_hour_falls_back_to_simple_mean(self):
        # Hour 1 has zero total load -> unweighted mean of zonal LMPs,
        # matching the consumer's collapse_zonal_lmp fallback.
        prices = np.array([[10.0, 100.0], [30.0, 200.0]])
        loads = np.array([[1.0, 0.0], [1.0, 0.0]])
        out = xl.collapse_zonal_prices(prices, loads)
        np.testing.assert_allclose(out, [20.0, 150.0])

    def test_zero_load_zone_gets_zero_weight(self):
        # An import/export pseudo-zone (load_share == 0) must never move
        # the ISO price while any real zone carries load.
        prices = np.array([[25.0], [999.0]])
        loads = np.array([[10.0], [0.0]])
        out = xl.collapse_zonal_prices(prices, loads)
        np.testing.assert_allclose(out, [25.0])

    def test_shape_mismatch_raises(self):
        with pytest.raises(ValueError, match="must align"):
            xl.collapse_zonal_prices(np.zeros((2, 4)), np.zeros((3, 4)))

    def test_weights_invariant_to_uniform_scaling(self):
        # Demand growth / T&D-loss gross-up are uniform multipliers, so the
        # collapsed price must not change when loads are rescaled.
        rng = np.random.default_rng(7)
        prices = rng.uniform(10, 90, size=(4, 24))
        loads = rng.uniform(0.5, 5.0, size=(4, 24))
        base = xl.collapse_zonal_prices(prices, loads)
        scaled = xl.collapse_zonal_prices(prices, loads * 1.37)
        np.testing.assert_allclose(base, scaled)


class TestWriteExport:
    def _frames(self):
        hours = np.arange(4)
        f1 = pd.DataFrame(
            {"hour": hours, "iso": "ERCOT", "lmp": [30.0, 31.5, 29.25, 28.0]}
        )
        f2 = pd.DataFrame(
            {"hour": hours, "iso": "CAISO", "lmp": [40.0, 41.0, 42.0, 43.0]}
        )
        prov = [
            {"iso": "ERCOT", "scenario_cache_key": "abc", "simulation_year": 2026},
            {"iso": "CAISO", "scenario_cache_key": "def", "simulation_year": 2026},
        ]
        return [f1, f2], prov

    def test_csv_shape_and_roundtrip(self, tmp_path):
        frames, prov = self._frames()
        out = xl.write_export(frames, prov, tmp_path / "bau_lmp_2026.csv")
        df = pd.read_csv(out)
        assert list(df.columns) == ["hour", "iso", "lmp"]
        assert len(df) == 8  # one block per ISO, 4 hours each
        ercot = df[df["iso"] == "ERCOT"].sort_values("hour")
        np.testing.assert_allclose(ercot["lmp"], [30.0, 31.5, 29.25, 28.0])
        assert list(ercot["hour"]) == [0, 1, 2, 3]

    def test_no_comment_header(self, tmp_path):
        # The consumer reads the CSV with a plain pd.read_csv: the first
        # line must be the header row, never a '#' provenance comment.
        frames, prov = self._frames()
        out = xl.write_export(frames, prov, tmp_path / "bau_lmp_2026.csv")
        assert out.read_text().splitlines()[0] == "hour,iso,lmp"

    def test_provenance_sidecar(self, tmp_path):
        frames, prov = self._frames()
        out = xl.write_export(frames, prov, tmp_path / "bau_lmp_2026.csv")
        sidecar = out.with_suffix(out.suffix + ".provenance.json")
        assert sidecar.exists()
        payload = json.loads(sidecar.read_text())
        assert [p["iso"] for p in payload["isos"]] == ["ERCOT", "CAISO"]
        assert payload["isos"][0]["scenario_cache_key"] == "abc"
        assert "ADR 0011" in payload["contract"]


class TestSyntheticStub:
    def test_deterministic_per_iso_year(self):
        a = xl.synthetic_lmp("ERCOT", 2026)
        b = xl.synthetic_lmp("ERCOT", 2026)
        np.testing.assert_array_equal(a, b)
        # Different ISO or year -> different series (independent seeds).
        assert not np.array_equal(a, xl.synthetic_lmp("CAISO", 2026))
        assert not np.array_equal(a, xl.synthetic_lmp("ERCOT", 2030))

    def test_full_calendar_and_sane_level(self):
        # The consumer requires hours 0..8759; means must sit in the
        # forecast-plausible $15-80/MWh class for every registered ISO.
        for iso in ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP"]:
            lmp = xl.synthetic_lmp(iso, 2026)
            assert lmp.shape == (8760,)
            assert 15.0 < lmp.mean() < 80.0, f"{iso} mean {lmp.mean():.2f}"
            assert lmp.min() > 0.0
            assert lmp.max() < 2000.0

    def test_every_registered_iso_has_a_dummy_base(self):
        """Every ISO in ``_ISO_BUILDERS`` needs its own placeholder level.

        Without this, a newly registered ISO silently falls through to
        ``_DUMMY_DEFAULT_BASE`` and its stub is indistinguishable from PJM's
        — which is exactly how SPP's row was missed at registration
        (FINDING-spp-20 §5 routed item R-8).
        """
        from market_sim.config.iso_configs import SUPPORTED_ISOS

        missing = [i for i in SUPPORTED_ISOS if i not in xl._DUMMY_BASE_LMP]
        assert not missing, f"no _DUMMY_BASE_LMP row for {missing}"

    def test_dummy_block_contract_and_provenance(self):
        frame, prov = xl.export_iso_dummy("ercot", 2026, T=48)
        assert list(frame.columns) == ["hour", "iso", "lmp"]
        assert list(frame["hour"]) == list(range(48))
        assert (frame["iso"] == "ERCOT").all()
        assert prov["source"] == "synthetic-dummy"
        assert "NOT market-sim output" in prov["warning"]

    def test_dummy_sidecar_marks_synthetic(self, tmp_path):
        frame, prov = xl.export_iso_dummy("ERCOT", 2026, T=24)
        out = xl.write_export([frame], [prov], tmp_path / "x.csv", dummy=True)
        payload = json.loads(
            out.with_suffix(out.suffix + ".provenance.json").read_text()
        )
        assert "SYNTHETIC DUMMY" in payload["contract"]


class TestResolveBauConfig:
    def test_iso_override_and_deterministic_key(self):
        base = xl.ScenarioConfig()
        cfg = xl.resolve_bau_config(base, "ercot")
        assert cfg.iso == "ERCOT"
        assert cfg.mode == "forecast"
        # Canonicalization is deterministic: same inputs, same cache key.
        assert cfg.cache_key() == xl.resolve_bau_config(base, "ERCOT").cache_key()
