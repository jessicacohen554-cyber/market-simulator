"""Tests for the MISO measured reserve-requirement intake and the v4
condition-keyed fast-start amortization horizon (Lane-2 miso-56).

Covers:
* ``data.miso_reserve_requirements.load_miso_reserve_requirements`` — clock
  mapping (incl. the leap-year Feb-29 drop), STR exclusion, gap tolerance,
  and the no-silent-fallback hard error.
* ``reserve_config._miso_design`` under
  ``miso_measured_reserve_requirements`` — the market-wide and South zonal
  families take the measured hourly series; shortfall steps stay
  published-shaped and span the requirement (feasibility guard).
* ``model.commitment.compute_monthly_markup`` with ``run_ratio_t`` — the v4
  hourly ceiling semantics and the v3 byte-identity when ``None``.
* ``data.fleet.campd_ct_run_band_ratios`` — the committed MISO artifact.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.data.miso_reserve_requirements import (
    OR_PRODUCTS,
    load_miso_reserve_requirements,
)


def _write_cleared_parquet(
    path: Path,
    year: int,
    *,
    reg: float = 400.0,
    spin: float = 900.0,
    supp: float = 1100.0,
    south_frac: float = 0.15,
    drop_hours: int = 0,
) -> None:
    """Write a synthetic full-year cleared-MW parquet in the source schema."""
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    rows = []
    per_product = {"reg": reg, "spin": spin, "supp": supp, "str": 350.0}
    for d in days:
        for he in range(1, 25):
            for product, total in per_product.items():
                rows.append(
                    (d.date().isoformat(), he, "South", product, total * south_frac)
                )
                rows.append(
                    (
                        d.date().isoformat(),
                        he,
                        "Central",
                        product,
                        total * (1 - south_frac),
                    )
                )
    df = pd.DataFrame(
        rows, columns=["date", "hour_end_est", "region", "product", "cleared_mw"]
    )
    if drop_hours:
        df = df.iloc[: -drop_hours * len(per_product) * 2]
    df.to_parquet(path)


class TestLoadMisoReserveRequirements(unittest.TestCase):
    def test_full_year_sums_or_products_and_excludes_str(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "asm.parquet"
            _write_cleared_parquet(p, 2023)
            out = load_miso_reserve_requirements(2023, 8760, path=p)
        # market = reg + spin + supp summed over regions; STR excluded.
        np.testing.assert_allclose(out["market"], 400.0 + 900.0 + 1100.0)
        np.testing.assert_allclose(out["MISO-South"], 2400.0 * 0.15)
        self.assertEqual(out["market"].shape, (8760,))

    def test_leap_year_feb29_dropped(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "asm.parquet"
            _write_cleared_parquet(p, 2024)  # 366 source days
            out = load_miso_reserve_requirements(2024, 8760, path=p)
        self.assertEqual(out["market"].shape, (8760,))
        self.assertTrue(np.all(np.isfinite(out["market"])))
        np.testing.assert_allclose(out["market"], 2400.0)

    def test_small_gaps_filled_large_gaps_error(self):
        with TemporaryDirectory() as td:
            p = Path(td) / "asm.parquet"
            _write_cleared_parquet(p, 2023, drop_hours=3)
            out = load_miso_reserve_requirements(2023, 8760, path=p)
            self.assertTrue(np.all(np.isfinite(out["market"])))

            p2 = Path(td) / "asm2.parquet"
            _write_cleared_parquet(p2, 2023, drop_hours=400)
            with self.assertRaises(ValueError):
                load_miso_reserve_requirements(2023, 8760, path=p2)

    def test_missing_file_hard_errors(self):
        with self.assertRaises(FileNotFoundError):
            load_miso_reserve_requirements(
                2023, 8760, path=Path("/nonexistent/asm.parquet")
            )

    def test_or_products_constant(self):
        self.assertEqual(set(OR_PRODUCTS), {"reg", "spin", "supp"})


class TestMisoDesignMeasuredRequirements(unittest.TestCase):
    """_miso_design consumes the measured series when the flag is on."""

    def _fleet(self, zones=1):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        nuc_idx = FUEL_TYPE_NAMES.index("nuclear")
        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        n, T = 3, 24
        return FleetArrays(
            pmax=np.array([1300.0, 800.0, 500.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([0.0, 7.0, 7.5]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, zones - 1]),
            fuel_type_idx=np.array([nuc_idx, cc_idx, cc_idx]),
            availability=np.ones((n, T)),
            unit_ids=["nuc", "cc", "cc2"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200, 300]),
        )

    def test_market_family_takes_measured_series(self):
        from market_sim.config.reserve_config import get_reserve_design

        T = 24
        measured = {
            "market": np.linspace(2300.0, 3000.0, T),
            "MISO-South": np.full(T, 420.0),
        }
        cfg = SimpleNamespace(
            iso="MISO", weather_year=2023, miso_measured_reserve_requirements=True
        )
        with mock.patch(
            "market_sim.data.miso_reserve_requirements.load_miso_reserve_requirements",
            return_value=measured,
        ):
            design = get_reserve_design(cfg, self._fleet(), T, ["z0"])
        fam = design.families[0]
        self.assertEqual(fam.name, "miso_rbdc")
        np.testing.assert_allclose(fam.requirement, measured["market"])
        # Feasibility: steps span the hourly requirement everywhere.
        self.assertGreaterEqual(
            float(fam.ordc_step_widths.sum()), float(fam.requirement.max()) - 1e-6
        )

    def test_south_zonal_family_takes_measured_series(self):
        from market_sim.config.reserve_config import (
            MISO_ZONAL_ORDC_STEPS,
            get_reserve_design,
        )

        T = 24
        south = np.full(T, 420.0)
        south[18] = 1200.0  # event-evening bump
        measured = {"market": np.full(T, 2500.0), "MISO-South": south}
        cfg = SimpleNamespace(
            iso="MISO",
            weather_year=2023,
            miso_measured_reserve_requirements=True,
            miso_zonal_reserves=True,
            miso_zonal_reserve_zones=("MISO-South",),
        )
        with mock.patch(
            "market_sim.data.miso_reserve_requirements.load_miso_reserve_requirements",
            return_value=measured,
        ):
            design = get_reserve_design(cfg, self._fleet(), T, ["MISO-South"])
        zonal = [f for f in design.families if f.name.startswith("miso_zonal_or")]
        self.assertEqual(len(zonal), 1)
        np.testing.assert_allclose(zonal[0].requirement, south)
        # Widths anchor to the measured MAX with the published fractions.
        np.testing.assert_allclose(
            zonal[0].ordc_step_widths,
            [frac * 1200.0 for frac, _ in MISO_ZONAL_ORDC_STEPS],
        )
        # Published penalties unchanged.
        np.testing.assert_allclose(
            zonal[0].ordc_penalties, [p for _, p in MISO_ZONAL_ORDC_STEPS]
        )

    def test_flag_off_is_static_basis(self):
        from market_sim.config.reserve_config import (
            MISO_REGULATING_RESERVE_MW,
            get_reserve_design,
        )

        cfg = SimpleNamespace(iso="MISO", weather_year=2023)
        design = get_reserve_design(cfg, self._fleet(), 24, ["z0"])
        np.testing.assert_allclose(
            design.families[0].requirement, 1300.0 + MISO_REGULATING_RESERVE_MW
        )


class TestConditionalRunMarkup(unittest.TestCase):
    """compute_monthly_markup with the v4 hourly run-ratio ceiling."""

    def _ct(self, hours):
        import sys

        sys.path.insert(0, str(Path(__file__).parent))
        from test_commitment import _single_ct

        return _single_ct(heat_rate=10.5, hours=hours)

    def test_ratio_scales_measured_ceiling_hourly(self):
        from market_sim.model.commitment import compute_monthly_markup

        hours = 744
        gens, arrays = self._ct(hours)
        gens[0].fast_start_run_hours = 10.0
        dispatch = np.zeros((1, hours))  # no P0 runs -> measured basis outright
        ratio = np.ones(hours)
        ratio[500:520] = 0.6  # tight-band hours: 10h ceiling -> 6h
        markup = compute_monthly_markup(
            gens, arrays, dispatch, hours, run_ratio_t=ratio
        )
        startup = float(markup[0, 0]) * 10.0  # back out the startup cost
        self.assertGreater(startup, 0.0)
        np.testing.assert_allclose(markup[0, 0], startup / 10.0)
        np.testing.assert_allclose(markup[0, 510], startup / 6.0)

    def test_none_ratio_is_v3_identical(self):
        from market_sim.model.commitment import compute_monthly_markup

        hours = 744
        gens, arrays = self._ct(hours)
        gens[0].fast_start_run_hours = 8.0
        dispatch = np.zeros((1, hours))
        dispatch[0, 100:104] = 200.0  # one 4h P0 run
        base = compute_monthly_markup(gens, arrays, dispatch, hours)
        ones = compute_monthly_markup(
            gens, arrays, dispatch, hours, run_ratio_t=np.ones(hours)
        )
        np.testing.assert_allclose(base, ones)

    def test_p0_run_still_shortens_hourly_ceiling(self):
        from market_sim.model.commitment import compute_monthly_markup

        hours = 744
        gens, arrays = self._ct(hours)
        gens[0].fast_start_run_hours = 10.0
        dispatch = np.zeros((1, hours))
        dispatch[0, 100:104] = 200.0  # P0 avg run 4h < any scaled ceiling
        ratio = np.full(hours, 2.0)  # would lengthen to 20h — must not
        markup = compute_monthly_markup(
            gens, arrays, dispatch, hours, run_ratio_t=ratio
        )
        base = compute_monthly_markup(gens, arrays, dispatch, hours)
        np.testing.assert_allclose(markup, base)


class TestCampdRunBandRatiosLoader(unittest.TestCase):
    def test_miso_artifact_loads(self):
        from market_sim.data.fleet import campd_ct_run_band_ratios

        bands = campd_ct_run_band_ratios("MISO")
        self.assertIsNotNone(bands)
        edges, ratios = bands
        self.assertEqual(len(edges), len(ratios) - 1)
        self.assertEqual(list(edges), [0.50, 0.75, 0.90, 0.975])
        # The measured monotone tightening at the top bands.
        self.assertLess(ratios[-1], ratios[0])
        self.assertLess(ratios[-1], 1.0)

    def test_absent_iso_returns_none(self):
        from market_sim.data.fleet import campd_ct_run_band_ratios

        self.assertIsNone(campd_ct_run_band_ratios("NOSUCHISO"))


if __name__ == "__main__":
    unittest.main()
