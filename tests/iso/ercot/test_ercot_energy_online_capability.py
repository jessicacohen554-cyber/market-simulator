"""Tests for the ERCOT-159 energy-side online-capability cap provider.

`ercot_energy_online_capability_cap_mw` fills the EXISTING
``ReserveDesign.online_capacity_cap`` row block (whose LP mechanics —
condition-responsiveness, energy-dual pricing, structural no-op when None —
are already proven by ``test_ercot_online_capacity_envelope.py``; this
mechanism only supplies a different RHS). What is new and tested here:

* gating: flag off / forecast mode / uncovered weather year / missing
  artifact → ``None`` (LP byte-unchanged — the year-scoping and G4 seam);
* the fast-tier-only shape: row 0 carries the cell envelope, row 1 stays at
  the uncapped sentinel;
* cell assignment: (season × hour-block × within-run net-load percentile
  bin) lookup with unmeasured cells left at the sentinel;
* ``ScenarioConfig.__post_init__`` exclusivity (envelope family,
  ``ercot_ordc_only_scarcity``) and the co-opt requirement.
"""

import json
import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.results.scarcity import (
    _RESERVE_SUPPLY_CAP_UNCAPPED_MW,
    ercot_energy_online_capability_cap_mw,
)

#: A minimal artifact on the real grain: January hours are season 0 (DJF);
#: hour blocks per the derive's HOUR_BLOCKS; net-load bins on the 13 rank
#: edges (14 bins).
GRAIN = {
    "season_by_month": [0, 0, 1, 1, 1, 2, 2, 2, 2, 3, 3, 0],
    "season_names": ["DJF", "MAM", "JJAS", "ON"],
    "hour_blocks": [[0, 5], [6, 9], [10, 13], [14, 16], [17, 21], [22, 23]],
    "netload_rank_edges": [
        0.10,
        0.20,
        0.30,
        0.40,
        0.50,
        0.60,
        0.70,
        0.80,
        0.90,
        0.92,
        0.94,
        0.96,
        0.98,
    ],
}


def _artifact(tmpdir, cells: dict) -> str:
    path = tmpdir / "cap.json"
    path.write_text(
        json.dumps(
            {
                "_provenance": {"grain": GRAIN},
                "2023": {"cells": cells, "n_cells": len(cells)},
            }
        )
    )
    return str(path)


def _cfg(**kw) -> ScenarioConfig:
    base = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2023,
        hours=24,
        energy_reserve_coopt=True,
        ercot_multiproduct_as_coopt=True,
        ercot_energy_online_capability_cap=True,
    )
    base.update(kw)
    return ScenarioConfig(**base)


class TestProviderGating(unittest.TestCase):
    def test_flag_off_returns_none(self):
        cfg = _cfg(ercot_energy_online_capability_cap=False)
        self.assertIsNone(
            ercot_energy_online_capability_cap_mw(cfg, 24, net_load=np.arange(24.0))
        )

    def test_forecast_mode_returns_none(self):
        # The G4 seam: the forward branch is a later derivation — uncapped.
        cfg = _cfg(
            mode="forecast", weather_year=2030, ercot_as_forward_requirement=True
        )
        self.assertIsNone(
            ercot_energy_online_capability_cap_mw(cfg, 24, net_load=np.arange(24.0))
        )

    def test_missing_artifact_returns_none(self):
        cfg = _cfg(ercot_energy_online_capability_cap_path="/nonexistent/cap.json")
        self.assertIsNone(
            ercot_energy_online_capability_cap_mw(cfg, 24, net_load=np.arange(24.0))
        )

    def test_uncovered_year_returns_none(self):
        # 2024/2025 carry no artifact block (full-corpus year scoping) — the
        # mechanism must be byte-inert there.
        import pathlib
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            path = _artifact(pathlib.Path(d), {"s0_b0_n0": {"max_mw": 100.0, "n": 5}})
            cfg = _cfg(weather_year=2024, ercot_energy_online_capability_cap_path=path)
            self.assertIsNone(
                ercot_energy_online_capability_cap_mw(cfg, 24, net_load=np.arange(24.0))
            )


class TestProviderShape(unittest.TestCase):
    def test_fast_tier_only_and_cell_assignment(self):
        import pathlib
        import tempfile

        # 24 January hours; net_load monotone 0..23 -> rank (i+1)/24. Hour 0
        # (block 0) has rank 1/24 ≈ 0.042 -> bin 0; hour 18 (block 4) has rank
        # 19/24 ≈ 0.792 -> bin 7 (edges .70 < r <= .80... searchsorted right of
        # 0.70/0.80 boundary: 0.7917 -> past 0.70, not past 0.80 -> bin 7).
        with tempfile.TemporaryDirectory() as d:
            cells = {
                "s0_b0_n0": {"max_mw": 111.0, "n": 3},
                "s0_b4_n7": {"max_mw": 222.0, "n": 4},
            }
            path = _artifact(pathlib.Path(d), cells)
            cfg = _cfg(ercot_energy_online_capability_cap_path=path)
            out = ercot_energy_online_capability_cap_mw(
                cfg, 24, net_load=np.arange(24.0)
            )
        self.assertIsNotNone(out)
        self.assertEqual(out.shape, (2, 24))
        # Row 1 (all tier) is never capped by this mechanism.
        self.assertTrue((out[1] == _RESERVE_SUPPLY_CAP_UNCAPPED_MW).all())
        # Hour 0: (DJF, block 0, bin 0) -> 111. Hour 18: (DJF, block 4=17-21,
        # bin 7) -> 222. Hour 23 (block 5): no cell -> sentinel.
        self.assertEqual(out[0, 0], 111.0)
        self.assertEqual(out[0, 18], 222.0)
        self.assertEqual(out[0, 23], _RESERVE_SUPPLY_CAP_UNCAPPED_MW)


class TestConfigExclusivity(unittest.TestCase):
    def test_envelope_family_is_excluded(self):
        with self.assertRaises(ValueError):
            _cfg(ercot_online_capacity_envelope=True)

    def test_ordc_only_scarcity_is_excluded(self):
        with self.assertRaises(ValueError):
            _cfg(
                ercot_ordc_only_scarcity=True,
                ercot_online_capacity_envelope=False,
            )

    def test_requires_multiproduct_coopt(self):
        with self.assertRaises(ValueError):
            _cfg(ercot_multiproduct_as_coopt=False)


if __name__ == "__main__":
    unittest.main()
