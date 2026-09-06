"""capx D74 — the NO-DEFAULT-CAP price-taker convention gate, pre-solve tests.

A screened thermal unit whose PUBLISHED resource class carries no default gross
Avoidable Cost Rate for the delivery year the screen prices (PJM Manual 18 Rev
62 §5.4.8.4(B): "Steam Oil & Gas" is "NA" through DY 2025/26) has no default
cap to elect, offers at $0 in the D57 stack and is exempt from the merchant
screen in that year. Charter: ``docs/handoffs/
PRECOMMIT-capx-d74-pjm-steam-oil-convention-2026-09-06.md`` §1; design:
``DESIGN-capx-d74-pjm-steam-oil-convention-2026-09-06.md`` §3.

Five properties, one test class each:

1. the OFF path is byte-identical and cache-neutral (absent / ``None`` /
   ``{"PJM": False}``), and no scalar companion field exists;
2. the resolver REQUIRES the D62 published-bar gate and reaches one ISO only;
3. the predicate is what ``pjm.csv`` says — True for ``gas_st`` / ``oil`` at
   DY 2022/23–2025/26, False from DY 2026/27, False for every class with a
   published value and for a fuel with no published class (rule 21: fixed by
   the data, never selectable by a result);
4. the toy-stack identity — an exempted unit is never in ``margins``, sits in
   the price-taking block on its accredited MW, and the D54 §3.5 identity holds
   (a price taker clears; nothing exempt can fail);
5. the ledger block is present exactly when the gate is armed.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config.capacity_market import (
    resolve_capacity_going_forward_bar_published,
    resolve_capacity_no_default_cap_convention,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.avoidable_cost_rate import (
    PUBLISHED_ACR_CLASS_BY_FUEL,
    no_default_cap_class,
    published_bar_per_kw_yr,
)
from market_sim.model.capacity_evolution.adequacy import clear_capacity_supply_stack
from market_sim.model.capacity_evolution.retirements import _THERMAL_FOM

FIELD = "capacity_no_default_cap_convention_by_iso"
BAR_FIELD = "capacity_going_forward_bar_published_by_iso"
SCREENED_FUELS = tuple(_THERMAL_FOM)


def _fc(**kw) -> ScenarioConfig:
    """A forecast-mode config (the only mode the screen runs in)."""
    return ScenarioConfig(iso=kw.pop("iso", "PJM"), mode="forecast", **kw)


class TestOffPathByteIdentityAndCacheNeutrality:
    def test_default_is_none_for_every_iso(self):
        for iso in ("PJM", "ERCOT", "CAISO", "MISO", "NYISO", "NEISO"):
            cfg = _fc(iso=iso)
            assert getattr(cfg, FIELD) is None
            assert resolve_capacity_no_default_cap_convention(cfg, iso) is False

    def test_field_is_registered_with_its_declared_default(self):
        assert FIELD in _CACHE_KEY_OPTIONAL_FIELDS
        assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[FIELD] == "None"

    def test_cache_key_unmoved_absent_explicit_none_and_explicit_false(self):
        base = _fc().cache_key()
        assert _fc(**{FIELD: None}).cache_key() == base
        # An explicit {"PJM": False} row is a NON-default value and keys
        # distinctly by design (the cache-key ledger's separability rule) —
        # what stays byte-identical is the resolved gate.
        assert (
            resolve_capacity_no_default_cap_convention(
                _fc(**{FIELD: {"PJM": False}, BAR_FIELD: {"PJM": True}}), "PJM"
            )
            is False
        )

    def test_armed_row_keys_distinctly(self):
        off = _fc(**{BAR_FIELD: {"PJM": True}})
        on = _fc(**{BAR_FIELD: {"PJM": True}, FIELD: {"PJM": True}})
        assert on.cache_key() != off.cache_key()

    def test_backcast_coerces_the_gate_off(self):
        cfg = ScenarioConfig(iso="PJM", mode="backcast", **{FIELD: {"PJM": True}})
        assert getattr(cfg, FIELD) is None

    def test_no_scalar_companion_field_exists(self):
        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        for bad in (
            "no_default_cap_offer_usd_per_mw_day",
            "steam_oil_offer_cap",
            "no_default_cap_share",
            "steam_price_taker_share",
        ):
            assert bad not in names


class TestResolutionScope:
    def test_requires_the_published_bar_gate(self):
        cfg = _fc(**{FIELD: {"PJM": True}})  # bar gate absent
        assert resolve_capacity_going_forward_bar_published(cfg, "PJM") is False
        assert resolve_capacity_no_default_cap_convention(cfg, "PJM") is False

    def test_armed_with_the_bar_gate_resolves_on(self):
        cfg = _fc(**{FIELD: {"PJM": True}, BAR_FIELD: {"PJM": True}})
        assert resolve_capacity_no_default_cap_convention(cfg, "PJM") is True

    def test_armed_row_for_one_iso_does_not_reach_another(self):
        cfg = _fc(
            iso="MISO",
            **{FIELD: {"PJM": True}, BAR_FIELD: {"PJM": True, "MISO": True}},
        )
        assert resolve_capacity_no_default_cap_convention(cfg, "MISO") is False
        assert resolve_capacity_no_default_cap_convention(cfg, "PJM") is True

    def test_iso_without_a_table_has_no_na_cell(self):
        for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
            for fuel in SCREENED_FUELS:
                for year in (2022, 2025, 2026):
                    assert no_default_cap_class(iso, fuel, year) is False


# DATA TIER, exactly like its D62 sibling. The three tests below are the only
# ones in this file that READ the published table, which lives in the DERIVED,
# gitignored clean tree (``data/clean/capacity-market-avoidable-cost-rate``) a
# ``code``-profile checkout does not build. They belong on the same marker
# ``test_d62_published_going_forward_bar.py`` already puts its own two
# table-reading classes on, and for the same reason.
#
# THIS REPLACES A MODULE-LEVEL ``pytestmark`` SKIPIF that read
# ``published_bar_per_kw_yr("PJM", "coal", 2022) is None``. That predicate can
# never be None on an unbuilt checkout: every value-returning entry point in
# the seam raises ``PublishedBarUnavailable`` instead — deliberately, so an
# armed gate can never degrade silently (``avoidable_cost_rate`` module
# docstring). So the guard raised the very error it meant to detect, at IMPORT
# time, erroring the whole file out of collection in the fast tier. Nothing is
# loosened: every assertion is unchanged, and the file's four data-free classes
# now actually run in the fast tier instead of being collected away with it.
# (``partition_available`` is the seam's non-raising predicate if a future lane
# wants a skip rather than a tier move.)
@pytest.mark.fulldata
class TestThePredicateIsTheData:
    @pytest.mark.parametrize("year", [2022, 2023, 2024, 2025])
    def test_steam_oil_and_gas_has_no_default_through_2025_26(self, year):
        for fuel in ("gas_st", "oil"):
            assert PUBLISHED_ACR_CLASS_BY_FUEL["PJM"][fuel] == "Steam Oil & Gas"
            assert no_default_cap_class("PJM", fuel, year) is True
            # The same limb D62's rule reports — one table, one rule.
            assert published_bar_per_kw_yr("PJM", fuel, year)[1] == "first_published"

    @pytest.mark.parametrize("year", [2026, 2027, 2030, 2040])
    def test_the_class_reenters_the_screen_when_the_table_publishes(self, year):
        for fuel in ("gas_st", "oil"):
            assert no_default_cap_class("PJM", fuel, year) is False
            value, basis = published_bar_per_kw_yr("PJM", fuel, year)
            assert basis == "vintage"
            assert value == pytest.approx(64.0 * 365.0 / 1000.0)

    @pytest.mark.parametrize("year", [2022, 2025, 2026, 2030])
    def test_every_class_with_a_published_value_is_screened(self, year):
        for fuel in ("coal", "gas_cc", "gas_ct", "nuclear"):
            assert no_default_cap_class("PJM", fuel, year) is False

    def test_a_fuel_with_no_published_class_is_never_exempt(self):
        assert "gas_cc_ccs" not in PUBLISHED_ACR_CLASS_BY_FUEL["PJM"]
        for year in (2022, 2026, 2030):
            assert no_default_cap_class("PJM", "gas_cc_ccs", year) is False


class TestToyStackIdentity:
    def test_exempt_unit_is_a_price_taker_that_clears(self):
        """DESIGN-capx-d54 §3.2 / §3.5 on a 1-curve, 3-offer toy stack.

        Under the convention the steam unit is not in the offer stack; its
        accredited MW is in ``Q_0``. Whatever the curve does, it is cleared —
        and the screen never sees it, so it cannot fail (the identity).
        """

        # A flat demand curve at $100/MW-day above position 0.9 falling to 0
        # at 1.1 — enough to put the crossing inside the CT plateau.
        def curve(position: float) -> float:  # $/firm-MW-yr
            if position <= 0.9:
                return 100.0 * 365.0
            if position >= 1.1:
                return 0.0
            return 100.0 * 365.0 * (1.1 - position) / 0.2

        requirement = 1000.0
        steam_a_mw = 150.0
        offers_screened = [
            ("coal_1", "coal", 10.0, 300.0, 330.0),
            ("ct_1", "gas_ct", 46.78, 400.0, 425.0),
            ("ct_2", "gas_ct", 46.78, 400.0, 425.0),
        ]
        # D62 posture: the steam unit offers its full bar (zero E&AS).
        with_steam = offers_screened + [("st_1", "gas_st", 103.1, steam_a_mw, 160.0)]
        q0 = 200.0
        d62 = clear_capacity_supply_stack(with_steam, q0, requirement, curve)
        assert "st_1" not in d62.cleared_unit_ids  # uncleared -> fails the screen
        # D74 posture: the steam unit is exempt and its A_g sits in Q_0.
        d74 = clear_capacity_supply_stack(
            offers_screened, q0 + steam_a_mw, requirement, curve
        )
        assert d74.price_takers_mw == pytest.approx(q0 + steam_a_mw)
        assert d74.census_mw == pytest.approx(
            d62.census_mw
        )  # I1: the census is unchanged
        # The price-taking block always clears; a unit outside ``margins`` has
        # nothing to fail. The CT plateau absorbs the moved MW.
        assert d74.price_usd_per_mw_day == pytest.approx(d62.price_usd_per_mw_day)


class TestLedgerBlockShape:
    def test_gate_off_writes_no_block(self):
        cfg = _fc(**{BAR_FIELD: {"PJM": True}})
        assert resolve_capacity_no_default_cap_convention(cfg, "PJM") is False
