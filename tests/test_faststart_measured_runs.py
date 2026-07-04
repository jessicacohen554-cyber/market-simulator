"""Tests for the fast-start amortization v3 (measured run-length basis),
the generator-level EIA-860 oil-primary screen, and the NYSDEC 227-3
peaker-rule availability overlay (2026-07-04 NYISO CT offer-grounding
session)."""

import textwrap
import unittest
from pathlib import Path

import numpy as np

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.outages import (
    OZONE_SEASON_HOURS,
    _nysdec_peaker_rows,
    nysdec_peaker_restrictions,
)
from market_sim.model.commitment import compute_monthly_markup


def _ct(unit_id: str, measured: float = 0.0, startup: float = 20.0) -> Generator:
    """Return one CAMPD-bin CT_PEAKER tranche carrying an fsp startup cost."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="z",
        fuel_type="gas_ct",
        pmax_mw=100.0,
        pmin_mw=0.0,
        heat_rate=10.0,
        eford=0.0,
        is_campd_bin=True,
        plant_group="CT_PEAKER",
        startup_cost_per_mw=startup,
        fast_start_run_hours=measured,
    )


class TestMeasuredRunMarkup(unittest.TestCase):
    """v3: the measured median caps the amortization horizon."""

    T = 24 * 31  # January only

    def _markup(self, gen: Generator, dispatch_row: np.ndarray) -> float:
        gens = [gen]
        fa = generators_to_fleet_arrays(gens, ["z"], hours=self.T)
        dispatch = dispatch_row[np.newaxis, :]
        markup = compute_monthly_markup(gens, fa, dispatch, self.T)
        return float(markup[0, 0])

    def test_long_p0_runs_capped_at_measured(self):
        # P0 runs the CT in one long 240 h block (the too-cheap-offer
        # signature). v2 would amortize 20/240 ~ 0.08 $/MWh; the 4 h measured
        # horizon caps it at 20/4 = 5 $/MWh.
        d = np.zeros(self.T)
        d[:240] = 100.0
        self.assertAlmostEqual(self._markup(_ct("v3", measured=4.0), d), 5.0)
        # v2 (no measured horizon) keeps the self-disabling long-run basis.
        self.assertAlmostEqual(self._markup(_ct("v2"), d), 20.0 / 240.0)

    def test_short_p0_runs_still_shorten_the_horizon(self):
        # P0 starts the unit for one 2 h run: min(P0, measured) = 2 h — the
        # endogenous run may only SHORTEN the horizon, never lengthen it.
        d = np.zeros(self.T)
        d[10:12] = 100.0
        self.assertAlmostEqual(self._markup(_ct("v3", measured=4.0), d), 10.0)

    def test_no_p0_runs_amortize_over_measured(self):
        # A month with no P0 runs uses the measured horizon outright (v2
        # bids startup/1 — effectively out of market).
        d = np.zeros(self.T)
        self.assertAlmostEqual(self._markup(_ct("v3", measured=4.0), d), 5.0)
        self.assertAlmostEqual(self._markup(_ct("v2"), d), 20.0)

    def test_zero_field_is_byte_identical_v2(self):
        d = np.zeros(self.T)
        d[:48] = 100.0
        self.assertAlmostEqual(
            self._markup(_ct("a", measured=0.0), d), self._markup(_ct("b"), d)
        )


class TestOilPrimaryGeneratorLevel(unittest.TestCase):
    """Generator-level EIA-860 oil-primary screen (per-plant ISOs)."""

    def test_nyiso_majority_screen_is_unit_grounded(self):
        from market_sim.data.fleet import oil_primary_ct_plants_from_eia860

        s = oil_primary_ct_plants_from_eia860("NYISO")
        # Pure-oil GT plants are majority-oil (Holtsville 8007, Glenwood 2514,
        # Shoreham 2518, Wading River 7146)...
        for code in (8007, 2514, 2518, 7146):
            self.assertIn(code, s)
        # ...while NG-primary CT plants (Bayonne 56964, Equus 56032,
        # Edgewood 55786, Gowanus 2494, Narrows 2499) and the minority-oil
        # Freeport-2 (2679: 18 MW KER vs 60 MW NG) never flip.
        for code in (56964, 56032, 55786, 2494, 2499, 2679):
            self.assertNotIn(code, s)

    def test_ercot_keeps_registry_screen(self):
        # ERCOT bins resolve from the curated master registry only — the
        # generator-level screen must not silently move ERCOT keeper sets.
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.data.fleet import bins_to_fleet  # noqa: F401
        from market_sim.data.fleet import oil_primary_bin_plants

        reg = oil_primary_bin_plants(ScenarioConfig().plant_registry_path)
        self.assertIn(3492, reg)  # Morgan Creek, the canonical registry case


class TestNysdecPeakerOverlay(unittest.TestCase):
    """NYSDEC 227-3 curated schedule → ozone-window availability events."""

    def test_windows_by_year(self):
        r23 = nysdec_peaker_restrictions(2023, 8760)
        r24 = nysdec_peaker_restrictions(2024, 8760)
        r25 = nysdec_peaker_restrictions(2025, 8760)
        codes = lambda rs: {r["plant_code"] for r in rs}  # noqa: E731
        # Phase-1 (2023-05-01) units restricted every year from 2023.
        for y in (r23, r24, r25):
            self.assertIn(2487, codes(y))  # Coxsackie GT (gas_ct)
            self.assertIn(2518, codes(y))  # Shoreham 1&2 (oil)
        # South Cairo retired 2024-03-31: restricted 2023, gone from the
        # 2024 window (retirement precedes May 1).
        self.assertIn(2482, codes(r23))
        self.assertNotIn(2482, codes(r24))
        # Phase-2 (2025-05-01) rows appear only in 2025.
        self.assertNotIn(2503, codes(r24))
        self.assertIn(2503, codes(r25))
        # STAR-designated barges are NEVER restricted.
        for y in (r23, r24, r25):
            self.assertNotIn(2494, codes(y))
            self.assertNotIn(2499, codes(y))
        # Window bounds are the ozone season.
        lo, hi = OZONE_SEASON_HOURS
        for r in r23 + r24 + r25:
            self.assertGreaterEqual(r["h_lo"], lo)
            self.assertLessEqual(r["h_hi"], hi)

    def test_availability_application(self):
        from market_sim.config.scenarios import ScenarioConfig

        lo, hi = OZONE_SEASON_HOURS
        gens = [
            _ct("2487_committed"),  # Coxsackie CT bin tranche
            Generator(
                unit_id="2518_GT1",
                name="Shoreham GT1",
                zone="z",
                fuel_type="oil",
                pmax_mw=52.9,
                pmin_mw=0.0,
                heat_rate=12.0,
                eford=0.0,
            ),
        ]
        gens[0].plant_code = 2487
        gens[1].plant_code = 2518
        config = ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            weather_year=2024,
            nysdec_peaker_rule_availability=True,
        )
        fa = generators_to_fleet_arrays(
            gens, ["z"], hours=8760, iso="NYISO", config=config, year=2024
        )
        # Both units are zeroed across the ozone window and untouched outside.
        for g in (0, 1):
            self.assertEqual(float(fa.availability[g, lo:hi].max()), 0.0)
            self.assertGreater(float(fa.availability[g, :lo].mean()), 0.0)

    def test_overlay_off_is_untouched(self):
        from market_sim.config.scenarios import ScenarioConfig

        lo, hi = OZONE_SEASON_HOURS
        g = _ct("2487_committed")
        g.plant_code = 2487
        config = ScenarioConfig(iso="NYISO", mode="backcast", weather_year=2024)
        fa = generators_to_fleet_arrays(
            [g], ["z"], hours=8760, iso="NYISO", config=config, year=2024
        )
        self.assertGreater(float(fa.availability[0, lo:hi].mean()), 0.0)

    def test_parser_handles_partial_windows(self, tmp_name="_dec_tmp.csv"):
        import tempfile

        csv = textwrap.dedent(
            """\
            plant_code,plant_name,unit_ids,ptid,zone,scope,restriction,effective_date,end_date,restricted_mw,source,note
            1,Mid,GT1,,J,gas_ct,ozone_season_oos,2024-07-01,,,src,starts mid-window
            2,End,GT1,,J,gas_ct,ozone_season_oos,2023-05-01,2024-08-15,,src,ends mid-window
            """
        )
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write(csv)
            path = Path(f.name)
        try:
            _nysdec_peaker_rows.cache_clear()
            rs = {
                r["plant_code"]: r
                for r in nysdec_peaker_restrictions(2024, 8760, csv_path=path)
            }
            lo, hi = OZONE_SEASON_HOURS
            # Jul 1 2024 = day 182 -> hour 4344.
            self.assertEqual(rs[1]["h_lo"], (182 - 1) * 24)
            self.assertEqual(rs[1]["h_hi"], hi)
            # Aug 15 = day 227 -> hour 5424.
            self.assertEqual(rs[2]["h_lo"], lo)
            self.assertEqual(rs[2]["h_hi"], (227 - 1) * 24)
        finally:
            path.unlink()
            _nysdec_peaker_rows.cache_clear()


if __name__ == "__main__":
    unittest.main()
