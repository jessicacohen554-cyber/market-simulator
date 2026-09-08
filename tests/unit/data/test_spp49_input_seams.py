"""SPP-49 — the two measured-input seam repairs (owner ruling P19, repo-wide).

Seam 1: the EIA-923 own-month gas-price plausibility screen
(``plant_prices.screen_gas_plant_month_prices`` + its wiring in
``apply_plant_monthly_fuel_prices`` under ``ScenarioConfig.f923_gas_price_plausibility_screen``).
Seam 2: the simple-cycle heat-rate floor (``eia860._apply_simple_cycle_hr_floor``).

Every fixture is synthetic (a tmp reference CSV, an in-memory F923 frame, a
three-row fleet); nothing here reads the committed data except the
declared-default / coercion tests, which read ``ScenarioConfig`` alone.
PRECOMMIT: docs/handoffs/PRECOMMIT-spp-49-2026-09-08.md.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import (
    EGRID_CT_HR_PHYSICAL_FLOOR,
    F923_GAS_PRICE_PLAUSIBILITY_BAND,
    HEAT_RATE_BINS,
)
from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.fleet.eia860 import _apply_simple_cycle_hr_floor
from market_sim.data.fuel import plant_prices as pp

YEAR = 2024
HOURS = 8760
MONTH_HOURS = np.repeat(
    np.arange(12), [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]
)
MCF = pp._MCF_TO_MMBTU


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def reference_csv(tmp_path):
    """A state reference table: TX published every month at $2.072/Mcf (= $2.00/MMBtu),
    OK unpublished in 2024 (NA), NM negative in August, US at $3.108/Mcf (= $3.00)."""
    rows = []
    for m in range(1, 13):
        rows.append(("TX", "N3045TX3", YEAR, m, f"{2.0 * MCF:.3f}"))
        rows.append(("OK", "N3045OK3", YEAR, m, "NA"))
        rows.append(
            ("NM", "N3045NM3", YEAR, m, f"{(-0.16 if m == 8 else 1.0 * MCF):.3f}")
        )
        rows.append(("US", "N3045US3", YEAR, m, f"{3.0 * MCF:.3f}"))
    path = tmp_path / "ref.csv"
    pd.DataFrame(
        rows, columns=["state", "series", "year", "month", "price_usd_mcf"]
    ).to_csv(path, index=False)
    return path


def _costs(rows):
    return pd.DataFrame(
        [
            dict(
                year=YEAR,
                month=m,
                plant_id=pid,
                state=st,
                fuel_group=fg,
                price_per_mmbtu=p,
                quantity=q,
            )
            for (pid, st, fg, m, p, q) in rows
        ]
    )


@pytest.fixture
def costs_frame():
    """Own-reported months: plant 1 (TX) in band except Feb ($0.30, low), Mar
    (-$0.50, negative), Apr ($9.00, high); plant 2 (OK, unpublished state ->
    US $3.00) at $1.20 in Jan (low against US) and $3.10 in Feb (in band);
    plant 3 (NM) at $0.05 in Aug (reference -0.16 -> unscreened) and $0.10 in
    Sep (low against $1.00); a coal row at $50 (never screened)."""
    rows = []
    for m in range(1, 13):
        p = {2: 0.30, 3: -0.50, 4: 9.00}.get(m, 2.10)
        rows.append((1, "TX", "Natural Gas", m, p, 1000.0))
    rows += [
        (2, "OK", "Natural Gas", 1, 1.20, 500.0),
        (2, "OK", "Natural Gas", 2, 3.10, 500.0),
        (3, "NM", "Natural Gas", 8, 0.05, 100.0),
        (3, "NM", "Natural Gas", 9, 0.10, 100.0),
        (4, "TX", "Coal", 1, 50.0, 100.0),
    ]
    return _costs(rows)


def _fleet(plant_codes=(1, 2, 3)):
    n = len(plant_codes)
    return FleetArrays(
        pmax=np.full(n, 100.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 8.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.full(n, FUEL_TYPE_MAP["gas_ct"]),
        availability=np.ones((n, HOURS)),
        unit_ids=[f"U{p}" for p in plant_codes],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.array(plant_codes),
        state=np.array([""] * n, dtype=object),  # the fleet carries NO state (R-7)
        plant_group=np.array(["CT_PEAKER"] * n, dtype=object),
    )


# --------------------------------------------------------------------------- #
# seam 1 — the screen function
# --------------------------------------------------------------------------- #
class TestReferenceTable:
    def test_loads_and_converts_mcf_to_mmbtu(self, reference_csv):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        assert table[("TX", YEAR, 1)] == pytest.approx(2.0)
        assert ("OK", YEAR, 1) not in table  # NA is absent, not zero
        assert table[("NM", YEAR, 8)] == pytest.approx(-0.16 / MCF)

    def test_state_then_us_then_none(self, reference_csv):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        assert pp.state_reference_gas_price(table, "TX", YEAR, 1) == (
            pytest.approx(2.0),
            "state",
        )
        assert pp.state_reference_gas_price(table, "OK", YEAR, 1) == (
            pytest.approx(3.0),
            "us",
        )
        v, prov = pp.state_reference_gas_price(table, "TX", 1999, 1)
        assert prov == "none" and np.isnan(v)

    def test_absent_file_returns_none(self, tmp_path):
        assert pp.load_state_electric_power_gas_prices(tmp_path / "missing.csv") is None


class TestScreenFunction:
    def test_band_is_the_declared_constant(self):
        assert F923_GAS_PRICE_PLAUSIBILITY_BAND == (0.5, 2.0)

    def test_replaces_out_of_band_months_by_the_reference_and_keeps_the_rest(
        self, reference_csv, costs_frame
    ):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        out, report = pp.screen_gas_plant_month_prices(costs_frame, YEAR, table)
        p1 = out[(out.plant_id == 1)].set_index("month")["price_per_mmbtu"]
        assert p1[2] == pytest.approx(2.0)  # low -> TX reference
        assert p1[3] == pytest.approx(2.0)  # negative -> TX reference
        assert p1[4] == pytest.approx(2.0)  # high -> TX reference
        assert p1[1] == 2.10 and p1[12] == 2.10  # in band, byte-identical
        assert report["low"] == 3 and report["negative"] == 1 and report["high"] == 1
        assert report["in_band"] == 9 + 1  # plant 1's nine + plant 2's Feb

    def test_unpublished_state_falls_to_us_and_counts_it(
        self, reference_csv, costs_frame
    ):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        out, report = pp.screen_gas_plant_month_prices(costs_frame, YEAR, table)
        p2 = out[out.plant_id == 2].set_index("month")["price_per_mmbtu"]
        assert p2[1] == pytest.approx(3.0)  # $1.20 < 0.5 x US 3.00 -> US
        assert p2[2] == 3.10  # in band against US
        assert report["ref_us"] == 2

    def test_nonpositive_reference_leaves_the_month_unscreened(
        self, reference_csv, costs_frame
    ):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        out, report = pp.screen_gas_plant_month_prices(costs_frame, YEAR, table)
        p3 = out[out.plant_id == 3].set_index("month")["price_per_mmbtu"]
        assert p3[8] == 0.05  # NM Aug reference is negative: no band, kept
        assert p3[9] == pytest.approx(1.0 / 1.0)  # Sep: $0.10 < 0.5 x 1.00 -> reference
        assert report["unscreened_nonpos_ref"] == 1

    def test_coal_rows_and_other_years_are_never_touched(
        self, reference_csv, costs_frame
    ):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        extra = costs_frame.copy()
        extra.loc[len(extra)] = dict(
            year=YEAR - 1,
            month=2,
            plant_id=1,
            state="TX",
            fuel_group="Natural Gas",
            price_per_mmbtu=0.30,
            quantity=1.0,
        )
        out, _ = pp.screen_gas_plant_month_prices(extra, YEAR, table)
        assert out[out.fuel_group == "Coal"]["price_per_mmbtu"].item() == 50.0
        assert out[(out.year == YEAR - 1)]["price_per_mmbtu"].item() == 0.30

    def test_plant_ids_restriction_and_no_mutation(self, reference_csv, costs_frame):
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        before = costs_frame.copy()
        out, report = pp.screen_gas_plant_month_prices(
            costs_frame, YEAR, table, plant_ids={2}
        )
        pd.testing.assert_frame_equal(costs_frame, before)  # input never mutated
        assert report["plants_flagged"] == 1
        assert (
            out[(out.plant_id == 1) & (out.month == 2)]["price_per_mmbtu"].item()
            == 0.30
        )

    def test_state_read_from_the_frame_not_the_fleet(self, reference_csv, costs_frame):
        """The fleet rows carry no state (SPP-46 R-7); the frame's state keys the reference."""
        table = pp.load_state_electric_power_gas_prices(reference_csv)
        frame = costs_frame.copy()
        frame.loc[frame.plant_id == 1, "state"] = (
            "NM"  # same prints, NM reference ($1.00)
        )
        out, _ = pp.screen_gas_plant_month_prices(frame, YEAR, table)
        p1 = out[out.plant_id == 1].set_index("month")["price_per_mmbtu"]
        assert p1[4] == pytest.approx(1.0)  # $9.00 high against NM -> NM reference
        assert p1[1] == pytest.approx(1.0)  # $2.10 > 2 x 1.00: high against NM


# --------------------------------------------------------------------------- #
# seam 1 — the wiring under the registered gate
# --------------------------------------------------------------------------- #
def _apply(config, costs_frame, reference_csv, tmp_path):
    parquet = tmp_path / "costs.parquet"
    costs_frame.to_parquet(parquet)
    fleet = _fleet()
    fuel = np.full((fleet.n_gen, HOURS), 5.0)
    pp.apply_plant_monthly_fuel_prices(
        fuel,
        fleet,
        config,
        YEAR,
        monthly_costs_path=parquet,
        state_gas_reference_path=reference_csv,
    )
    return fuel


class TestWiring:
    def test_armed_backcast_screens_the_own_months(
        self, reference_csv, costs_frame, tmp_path
    ):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=HOURS,
            gas_plant_monthly_fuel_pricing=True,
        )
        assert cfg.f923_gas_price_plausibility_screen is True  # default ON, reachable
        fuel = _apply(cfg, costs_frame, reference_csv, tmp_path)
        assert fuel[0, MONTH_HOURS == 1].mean() == pytest.approx(2.0)  # Feb low -> ref
        assert fuel[0, MONTH_HOURS == 3].mean() == pytest.approx(2.0)  # Apr high -> ref
        assert fuel[0, MONTH_HOURS == 0].mean() == pytest.approx(2.10)  # Jan kept

    def test_explicit_off_consumes_the_raw_series(
        self, reference_csv, costs_frame, tmp_path
    ):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=HOURS,
            gas_plant_monthly_fuel_pricing=True,
            f923_gas_price_plausibility_screen=False,
        )
        fuel = _apply(cfg, costs_frame, reference_csv, tmp_path)
        assert fuel[0, MONTH_HOURS == 1].mean() == pytest.approx(0.30)
        assert fuel[0, MONTH_HOURS == 2].mean() == pytest.approx(-0.50)

    def test_nearby_pool_is_built_from_screened_months(
        self, reference_csv, costs_frame, tmp_path
    ):
        """A non-filing TX plant fills from the pool; plant 1's screened Feb ($2.00)
        seeds it, never the raw $0.30."""
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=HOURS,
            gas_plant_monthly_fuel_pricing=True,
            nearby_fuel_price_fallback=True,
            nearby_fuel_price_min_state_plants=99,
        )  # force the zone tier
        parquet = tmp_path / "costs.parquet"
        costs_frame.to_parquet(parquet)
        fleet = _fleet(plant_codes=(1, 999))  # 999 files nothing, same zone as plant 1
        fuel = np.full((fleet.n_gen, HOURS), 5.0)
        pp.apply_plant_monthly_fuel_prices(
            fuel,
            fleet,
            cfg,
            YEAR,
            monthly_costs_path=parquet,
            state_gas_reference_path=reference_csv,
        )
        assert fuel[1, MONTH_HOURS == 1].mean() == pytest.approx(2.0)

    def test_absent_reference_passes_through_unscreened_with_a_warning(
        self, costs_frame, tmp_path, caplog
    ):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=HOURS,
            gas_plant_monthly_fuel_pricing=True,
        )
        fuel = _apply(cfg, costs_frame, tmp_path / "nope.csv", tmp_path)
        assert fuel[0, MONTH_HOURS == 1].mean() == pytest.approx(0.30)
        assert any(
            "plausibility screen" in r.message and "SKIPPED" in r.message
            for r in caplog.records
        )


# --------------------------------------------------------------------------- #
# seam 1 — the (b'-1) declaration and the coercion
# --------------------------------------------------------------------------- #
class TestGateDeclaration:
    def test_default_on_frozen_false(self):
        from dataclasses import fields

        default = next(
            f.default
            for f in fields(ScenarioConfig)
            if f.name == "f923_gas_price_plausibility_screen"
        )
        assert default is True
        assert cache_key_drop_defaults()["f923_gas_price_plausibility_screen"] is False

    @pytest.mark.parametrize(
        "kwargs",
        [
            dict(mode="forecast"),
            dict(mode="forecast", gas_plant_monthly_fuel_pricing=True),
            dict(mode="backcast"),  # gas not priced from F923 -> unreachable
            dict(mode="forecast", f923_gas_price_plausibility_screen=True),
        ],
    )
    def test_coerced_to_the_frozen_declaration_where_unreachable(self, kwargs):
        assert (
            ScenarioConfig(iso="SPP", **kwargs).f923_gas_price_plausibility_screen
            is False
        )

    def test_reachable_configs_keep_true_and_rekey(self):
        armed = ScenarioConfig(
            iso="SPP", mode="backcast", gas_plant_monthly_fuel_pricing=True
        )
        assert armed.f923_gas_price_plausibility_screen is True
        off = ScenarioConfig(
            iso="SPP",
            mode="backcast",
            gas_plant_monthly_fuel_pricing=True,
            f923_gas_price_plausibility_screen=False,
        )
        assert armed.cache_key() != off.cache_key()
        # a hindcast (forecast-mode machinery over history) keeps the overlay
        hind = ScenarioConfig(
            iso="SPP",
            mode="forecast",
            hindcast=True,
            gas_plant_monthly_fuel_pricing=True,
        )
        assert hind.f923_gas_price_plausibility_screen is True

    def test_unreachable_config_key_is_unmoved_by_the_field(self):
        plain = ScenarioConfig(iso="SPP", mode="backcast")
        explicit = ScenarioConfig(
            iso="SPP", mode="backcast", f923_gas_price_plausibility_screen=False
        )
        assert plain.cache_key() == explicit.cache_key()


# --------------------------------------------------------------------------- #
# seam 2 — the simple-cycle floor
# --------------------------------------------------------------------------- #
class TestSimpleCycleFloor:
    def test_floor_is_the_aero_bin(self):
        assert EGRID_CT_HR_PHYSICAL_FLOOR == HEAT_RATE_BINS["gas_ct"]["aero"] == 9.0

    def test_clamps_a_gt_ic_only_plant_and_leaves_mixed_and_plausible_plants(self):
        df = pd.DataFrame(
            {
                "plant_id": [57881, 57881, 57881, 1, 1, 2, 3],
                "prime_mover": ["GT", "GT", "IC", "GT", "CA", "GT", "GT"],
                "heat_rate": [3.43, 3.43, 3.43, 5.0, 5.0, 9.5, 8.2],
            }
        )
        out = _apply_simple_cycle_hr_floor(df)
        assert out.loc[out.plant_id == 57881, "heat_rate"].tolist() == [9.0, 9.0, 9.0]
        assert out.loc[out.plant_id == 1, "heat_rate"].tolist() == [
            5.0,
            5.0,
        ]  # mixed: untouched
        assert out.loc[out.plant_id == 2, "heat_rate"].item() == 9.5  # above the floor
        assert (
            out.loc[out.plant_id == 3, "heat_rate"].item() == 9.0
        )  # near-floor: clamped, not binned
        assert df.loc[0, "heat_rate"] == 3.43  # input not mutated

    def test_chp_plants_are_left_to_the_steam_credit_chain(self):
        """A CHP plant's eGRID rate is steam-credited: a sub-floor value there is
        the published power-only convention, owned by _correct_chp_steam_credit_hr /
        measured_chp_heat_rates, never clamped here (rule 19)."""
        df = pd.DataFrame(
            {
                "plant_id": [10496, 10496, 57881],
                "prime_mover": ["GT", "GT", "GT"],
                "chp": ["Y", "Y", "N"],
                "heat_rate": [5.79, 5.79, 3.43],
            }
        )
        out = _apply_simple_cycle_hr_floor(df)
        assert out.loc[out.plant_id == 10496, "heat_rate"].tolist() == [5.79, 5.79]
        assert out.loc[out.plant_id == 57881, "heat_rate"].item() == 9.0
        # one CHP row anywhere at the plant is enough
        df2 = pd.DataFrame(
            {
                "plant_id": [1, 1],
                "prime_mover": ["GT", "IC"],
                "chp": ["N", "Y"],
                "heat_rate": [4.0, 4.0],
            }
        )
        assert _apply_simple_cycle_hr_floor(df2)["heat_rate"].tolist() == [4.0, 4.0]

    def test_missing_columns_or_nan_rates_are_left_alone(self):
        df = pd.DataFrame({"plant_id": [1], "heat_rate": [3.0]})
        assert _apply_simple_cycle_hr_floor(df) is df
        df2 = pd.DataFrame(
            {"plant_id": [1], "prime_mover": ["GT"], "heat_rate": [np.nan]}
        )
        assert _apply_simple_cycle_hr_floor(df2) is df2

    def test_lowercase_and_padded_prime_movers_count(self):
        df = pd.DataFrame(
            {"plant_id": [1, 1], "prime_mover": [" gt", "ic "], "heat_rate": [4.0, 4.0]}
        )
        assert _apply_simple_cycle_hr_floor(df)["heat_rate"].tolist() == [9.0, 9.0]
