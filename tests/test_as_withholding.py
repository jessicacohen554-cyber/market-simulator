"""Tests for the ERCOT ancillary-service reserve-withholding probe.

The feature removes the hourly cleared DAM up-AS MW (built by
``scripts/data/build_ercot_as_withholding.py``) from thermal headroom before the
energy supply curve clears, an ERCOT-only upper bound that books all AS to
thermal. See ``ScenarioConfig.as_reserve_withholding`` and
``fleet.generators_to_fleet_arrays``.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    caiso_operating_reserve_mw,
    generators_to_fleet_arrays,
    load_as_reserve_withholding_mw,
    load_as_thermal_withholding,
)
from market_sim.model.dispatch import solve_dispatch

HOURS = 8760


def _gen(uid: str, group: str, fuel: str, pmax: float, code: int) -> Generator:
    return Generator(
        unit_id=uid,
        name=uid,
        plant_group=group,
        fuel_type=fuel,
        pmax_mw=pmax,
        heat_rate=8.0,
        zone="Z0",
        eford=0.0,
        plant_code=code,
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
        on = self._fleet(
            ScenarioConfig(iso="ERCOT", weather_year=2024, as_reserve_withholding=True)
        )
        by_class = load_as_thermal_withholding(2024, HOURS)
        # Single-unit pool per class -> exact cut of class_mw / pmax.
        np.testing.assert_allclose(
            on.availability[0],
            off.availability[0] - by_class["gas_cc"] / 60_000.0,
            atol=1e-9,
        )
        np.testing.assert_allclose(
            on.availability[1],
            off.availability[1] - by_class["coal"] / 30_000.0,
            atol=1e-9,
        )
        np.testing.assert_allclose(on.availability[2], off.availability[2])

    def test_unconfigured_iso_unaffected(self):
        """The withholding is scoped to ISOs with an AS series; others no-op."""
        off = self._fleet(ScenarioConfig(iso="MISO", weather_year=2024), iso="MISO")
        on = self._fleet(
            ScenarioConfig(iso="MISO", weather_year=2024, as_reserve_withholding=True),
            iso="MISO",
        )
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


class TestPjmWithholding:
    """PJM: the RT Primary Reserve requirement on the gas + flexible-oil pool."""

    def test_loads_pjm_primary_requirement(self):
        """The PJM parquet loads as a positive ~3 GW series."""
        s = load_as_reserve_withholding_mw(2024, HOURS, iso="PJM")
        assert s is not None and s.shape == (HOURS,)
        assert 2_000.0 < s.mean() < 5_000.0
        assert s.min() > 0.0

    def test_withholds_gas_and_oil_not_coal(self):
        """Gas + oil headroom is cut top-of-merit; coal/wind untouched."""
        as_mw = load_as_reserve_withholding_mw(2024, HOURS, iso="PJM")
        # Oil has the higher heat rate, so the top-of-merit withdrawal empties
        # the oil headroom first, then spills the remainder into the gas unit.
        gens = [
            _gen("cc1", "CC_REGULAR", "gas_cc", 40_000.0, 1),
            _gen("oil1", "oil", "oil", 4_000.0, 2),
            _gen("co1", "COAL", "coal", 20_000.0, 3),
            _gen("wind1", "WIND", "wind", 5_000.0, 4),
        ]
        gens[1].heat_rate = 12.0  # oil dearer than gas (8.0) -> withdrawn first
        off = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="PJM",
            config=ScenarioConfig(iso="PJM", weather_year=2024),
        )
        on = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="PJM",
            config=ScenarioConfig(
                iso="PJM", weather_year=2024, as_reserve_withholding=True
            ),
        )
        # Coal and wind never lose headroom.
        np.testing.assert_allclose(on.availability[2], off.availability[2])
        np.testing.assert_allclose(on.availability[3], off.availability[3])
        # The 4 GW oil unit is fully withdrawn (3+ GW requirement > 4 GW only
        # in the peak, so oil is ~emptied) and the gas unit carries the rest;
        # total withdrawn equals the requirement (pool headroom >> requirement).
        oil_cut = (off.availability[1] - on.availability[1]) * 4_000.0
        gas_cut = (off.availability[0] - on.availability[0]) * 40_000.0
        np.testing.assert_allclose(oil_cut + gas_cut, as_mw, atol=1e-3)
        assert on.availability.min() >= 0.0


class TestCaisoReserveFormula:
    """CAISO formula-based operating-reserve requirement and withholding.

    R(t) = max(MSSC, 0.067*load) + 0.01*load (WECC MORC contingency + 1%
    regulation-up), withdrawn from gas top-of-merit headroom; CAISO-only,
    default off. See ``ScenarioConfig.as_reserve_formula``,
    ``fleet.caiso_operating_reserve_mw`` and ``generators_to_fleet_arrays``.
    """

    # --- formula correctness (pure function, no fitted constants) ---

    def test_mssc_binds_at_low_load(self):
        """At low load the most-severe single contingency floors contingency."""
        load = np.full(HOURS, 10_000.0)
        r = caiso_operating_reserve_mw(load, mssc_mw=1_150.0, hours=HOURS)
        # contingency = max(1150, 0.067*10000=670) = 1150; reg = 0.01*10000=100.
        np.testing.assert_allclose(r, 1_150.0 + 100.0)

    def test_load_fraction_binds_at_high_load(self):
        """At high load the 6.7% MORC term dominates the fixed MSSC."""
        load = np.full(HOURS, 40_000.0)
        r = caiso_operating_reserve_mw(load, mssc_mw=1_150.0, hours=HOURS)
        # contingency = max(1150, 0.067*40000=2680) = 2680; reg = 400.
        np.testing.assert_allclose(r, 2_680.0 + 400.0)

    def test_pad_and_truncate(self):
        """A short load series zero-pads; a long one truncates to ``hours``."""
        short = caiso_operating_reserve_mw(np.array([20_000.0]), 1_150.0, 3)
        assert short.shape == (3,)
        # hour 0 from load 20000; padded hours from load 0 -> just the MSSC.
        np.testing.assert_allclose(short[1:], 1_150.0)
        long = caiso_operating_reserve_mw(np.arange(5.0) + 1.0, 1.0, 2)
        assert long.shape == (2,)

    # --- structural withholding (availability cut by R on the gas pool) ---

    def _gen(self, uid, group, fuel, pmax, code, hr=8.0):
        return Generator(
            unit_id=uid,
            name=uid,
            plant_group=group,
            fuel_type=fuel,
            pmax_mw=pmax,
            heat_rate=hr,
            zone="Z0",
            eford=0.0,
            plant_code=code,
        )

    def test_withholds_gas_not_coal_nuclear_wind(self):
        """R(t) is cut from gas top-of-merit; coal/nuclear/wind untouched."""
        load = np.full(HOURS, 30_000.0)
        gens = [
            self._gen("cc1", "CC_REGULAR", "gas_cc", 20_000.0, 1, hr=7.0),
            self._gen("ct1", "CT_PEAKER", "gas_ct", 20_000.0, 2, hr=12.0),
            self._gen("co1", "COAL", "coal", 10_000.0, 3, hr=9.0),
            self._gen("nuc1", "", "nuclear", 1_122.0, 4, hr=10.0),
            self._gen("wind1", "WIND", "wind", 5_000.0, 5, hr=0.0),
        ]
        kw = dict(hours=HOURS, iso="CAISO", load_shape=load)
        off = generators_to_fleet_arrays(
            gens, ["Z0"], config=ScenarioConfig(iso="CAISO", weather_year=2024), **kw
        )
        on = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            config=ScenarioConfig(
                iso="CAISO", weather_year=2024, as_reserve_formula=True
            ),
            **kw,
        )
        # MSSC = largest non-(import/wind/solar) unit = 20 GW gas here (the test
        # fleet has no separate single-unit cap); R = max(20000, 0.067*30000) +
        # 0.01*30000 = 20000 + 300 = 20300 MW. Withdrawn from the dearer gas (ct
        # at hr 12 first, then cc).
        r = caiso_operating_reserve_mw(load, mssc_mw=20_000.0, hours=HOURS)
        np.testing.assert_allclose(r, 20_300.0)
        ct_cut = (off.availability[1] - on.availability[1]) * 20_000.0
        cc_cut = (off.availability[0] - on.availability[0]) * 20_000.0
        np.testing.assert_allclose(ct_cut + cc_cut, r, atol=1e-3)
        # The dearer CT (hr 12) is emptied before the cheaper CC (hr 7) is cut.
        np.testing.assert_allclose(on.availability[1], 0.0, atol=1e-9)
        # Coal, nuclear and wind keep their full headroom.
        np.testing.assert_allclose(on.availability[2], off.availability[2])
        np.testing.assert_allclose(on.availability[3], off.availability[3])
        np.testing.assert_allclose(on.availability[4], off.availability[4])

    def test_default_off_is_byte_identical(self):
        """Flag off -> availability is untouched (byte-identical baseline)."""
        load = np.full(HOURS, 30_000.0)
        gens = [self._gen("cc1", "CC_REGULAR", "gas_cc", 20_000.0, 1)]
        base = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="CAISO",
            load_shape=load,
            config=ScenarioConfig(iso="CAISO", weather_year=2024),
        )
        flagged_off = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="CAISO",
            load_shape=load,
            config=ScenarioConfig(
                iso="CAISO", weather_year=2024, as_reserve_formula=False
            ),
        )
        np.testing.assert_array_equal(base.availability, flagged_off.availability)

    def test_other_iso_unaffected(self):
        """The formula is CAISO-scoped; other ISOs no-op even with the flag."""
        load = np.full(HOURS, 30_000.0)
        gens = [self._gen("cc1", "CC_REGULAR", "gas_cc", 20_000.0, 1)]
        off = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="MISO",
            load_shape=load,
            config=ScenarioConfig(iso="MISO", weather_year=2024),
        )
        on = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="MISO",
            load_shape=load,
            config=ScenarioConfig(
                iso="MISO", weather_year=2024, as_reserve_formula=True
            ),
        )
        np.testing.assert_array_equal(on.availability, off.availability)

    def test_availability_stays_in_unit_interval(self):
        """R(t) larger than gas headroom still leaves availability in [0, 1]."""
        load = np.full(HOURS, 30_000.0)
        gens = [self._gen("cc1", "CC_REGULAR", "gas_cc", 500.0, 1)]
        fa = generators_to_fleet_arrays(
            gens,
            ["Z0"],
            hours=HOURS,
            iso="CAISO",
            load_shape=load,
            config=ScenarioConfig(
                iso="CAISO", weather_year=2024, as_reserve_formula=True
            ),
        )
        assert fa.availability.min() >= 0.0
        assert fa.availability.max() <= 1.0

    def test_formula_range_20_to_40_gw_load(self):
        """R ≈ 1.5–2.5 GW for 20–40 GW load (WECC BAL-002, CAISO Tariff §8.2.3)."""
        mssc = 1_150.0  # Diablo Canyon unit
        for load_mw, r_lo, r_hi in [
            (20_000.0, 1_300.0, 1_700.0),
            (30_000.0, 1_800.0, 2_500.0),
            (40_000.0, 2_500.0, 3_200.0),
        ]:
            r = caiso_operating_reserve_mw(np.full(HOURS, load_mw), mssc, HOURS)
            mean_r = float(r.mean())
            assert r_lo <= mean_r <= r_hi, (
                f"load={load_mw / 1e3:.0f} GW: R={mean_r:.0f} MW outside "
                f"[{r_lo:.0f}, {r_hi:.0f}]"
            )

    # --- price impact: lifts the tight hour, leaves the slack hour flat ---

    def test_lifts_tight_hour_price_only(self):
        """Withholding lifts the binding tight-hour price; off-peak unchanged."""
        T = 2
        # hour 0 tight (2500 MW), hour 1 slack (800 MW), one zone.
        demand = np.array([[2_500.0, 800.0]])
        load_shape = demand.sum(axis=0)
        # Gas pool ordered by heat rate (top-of-merit withdrawal order):
        # exp CT (hr 15) emptied first, then mid CT (hr 10), then cheap CC.
        gens = [
            self._gen("cc", "CC_REGULAR", "gas_cc", 1_000.0, 1, hr=7.0),
            self._gen("ct_mid", "CT_PEAKER", "gas_ct", 1_000.0, 2, hr=10.0),
            self._gen("ct_exp", "CT_PEAKER", "gas_ct", 1_000.0, 3, hr=15.0),
            # Coal is outside the gas pool: never withheld, stays as the dear
            # marginal unit the tight hour climbs to once gas headroom is gone.
            self._gen("co", "COAL", "coal", 1_000.0, 4, hr=9.0),
        ]
        # Marginal costs decoupled from heat rate so the clearing order is
        # explicit: cc 20 < ct_mid 50 < ct_exp 100 < coal 200.
        mc = np.array(
            [
                [20.0, 20.0],
                [50.0, 50.0],
                [100.0, 100.0],
                [200.0, 200.0],
            ]
        )
        renew = dict(
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
        )

        def _solve(formula: bool):
            fa = generators_to_fleet_arrays(
                gens,
                ["Z0"],
                hours=T,
                iso="CAISO",
                load_shape=load_shape,
                config=ScenarioConfig(
                    iso="CAISO", weather_year=2024, as_reserve_formula=formula
                ),
            )
            return solve_dispatch(fa, demand, mc=mc, T=T, **renew)

        off = _solve(False).prices[0]  # (T,) zone-0 prices
        on = _solve(True).prices[0]
        # Off: tight hour clears on ct_exp (100); slack hour on cheap CC (20).
        np.testing.assert_allclose(off[0], 100.0)
        np.testing.assert_allclose(off[1], 20.0)
        # On: R(2500) = max(1000, 167.5) + 25 = 1025 MW withdrawn from the gas
        # pool empties ct_exp and bites ct_mid, so the tight hour must climb to
        # the un-withheld coal unit (200) -> lift. The slack hour (800 < cheap
        # CC cap, and CC is the last gas cut) is unchanged.
        assert on[0] > off[0]
        np.testing.assert_allclose(on[0], 200.0)
        np.testing.assert_allclose(on[1], off[1])


class TestStorageAsCommitment:
    """Reserving measured storage up-AS MW from the battery power cap."""

    def test_reserves_as_pro_rata(self):
        from market_sim.model.storage import reserve_storage_as_power
        import pandas as pd

        asr = pd.read_parquet(
            RAW_DATA_DIR / "ercot-AS" / "ercot_2024_as_by_restype_hourly.parquet"
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
