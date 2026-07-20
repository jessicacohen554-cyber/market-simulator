"""Tests for FF-G3 forward net-CONE evolution (constants.forward_net_cone_anchor).

Trivial-first (CLAUDE.md testing pattern): the escalation arithmetic is
exercised on hand-computed values before any ISO vintage is touched, then the
byte-identity guarantee (``hold_last`` reproduces the pricing seam's current
hold-last anchor exactly) and the ``ScenarioConfig`` cache-key / backcast-
coercion invariants are asserted.

Scope guard (FF-G3): the escalation is designed and tested here but NOT wired
into ``MarketDesign.capacity_price_per_firm_mw_yr`` (FF-2C owns the seam +
flips); these tests exercise the helper and the config field only.
"""

import unittest

from market_sim.config.constants import (
    MARKET_DESIGN,
    MARKET_DESIGN_VINTAGES,
    NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO,
    forward_net_cone_anchor,
    resolve_demand_curve_vintage,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)

_CAPACITY_ISOS = ("PJM", "NYISO", "NEISO", "MISO")


class TestForwardNetConeAnchor(unittest.TestCase):
    """The pure escalation resolver."""

    def test_hold_last_is_byte_identical_to_vintage_anchor(self):
        # The shipped default reproduces the anchor the pricing seam reads today
        # (resolve_demand_curve_vintage), for in-span AND held-last years — the
        # byte-identity guarantee that lets FF-G3 ship without moving any price.
        for iso in _CAPACITY_ISOS:
            for year in (2019, 2024, 2026, 2028, 2035, 2050):
                v = resolve_demand_curve_vintage(iso, year)
                self.assertEqual(
                    forward_net_cone_anchor(iso, year, "hold_last"),
                    v.net_cone_curve_per_kw_yr,
                    msg=f"{iso} {year}",
                )

    def test_hold_last_is_the_default_escalation(self):
        for iso in _CAPACITY_ISOS:
            self.assertEqual(
                forward_net_cone_anchor(iso, 2040),
                forward_net_cone_anchor(iso, 2040, "hold_last"),
            )

    def test_none_when_no_vintage_table(self):
        # CAISO (fixed CPM-soft-cap proxy) and ERCOT (energy-only) have no
        # vintage table — None, so the caller keeps its fixed proxy, exactly as
        # resolve_demand_curve_vintage does.
        self.assertIsNone(forward_net_cone_anchor("CAISO", 2030))
        self.assertIsNone(forward_net_cone_anchor("CAISO", 2030, "reindex_net"))
        self.assertIsNone(forward_net_cone_anchor("ERCOT", 2030))
        self.assertIsNone(forward_net_cone_anchor(None, 2030))
        self.assertIsNone(forward_net_cone_anchor("PJM", None))

    def test_central_rate_collapses_every_mode_to_hold_last(self):
        # NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO is 0.0 for every ISO (the cited
        # inflation-only / field central finding), so with no explicit rate every
        # reindex mode equals hold_last — the honest central result and a second
        # byte-identity guarantee.
        for iso in _CAPACITY_ISOS:
            hl = forward_net_cone_anchor(iso, 2045, "hold_last")
            self.assertAlmostEqual(
                forward_net_cone_anchor(iso, 2045, "reindex_net"), hl, places=12
            )
            self.assertAlmostEqual(
                forward_net_cone_anchor(
                    iso, 2045, "reindex_gross", eas_offset_per_kw_yr=50.0
                ),
                hl,
                places=12,
            )

    def test_reindex_net_arithmetic_identity(self):
        # A hand rate escalates ONLY the years past the last published vintage,
        # compounding from the last delivery-period start year.
        for iso in _CAPACITY_ISOS:
            v = resolve_demand_curve_vintage(iso, 2050)  # the held-last vintage
            last_start = int(v.delivery_year[:4])
            base = v.net_cone_curve_per_kw_yr
            for year in (last_start + 1, last_start + 5, 2050):
                n = year - last_start
                self.assertAlmostEqual(
                    forward_net_cone_anchor(iso, year, "reindex_net", rate=0.02),
                    base * (1.02**n),
                    places=9,
                    msg=f"{iso} {year}",
                )

    def test_no_escalation_at_or_before_last_vintage(self):
        # Even with a large rate, a year at/before the resolved (published)
        # vintage returns the published anchor unescalated (rule 13).
        v = resolve_demand_curve_vintage("PJM", 2027)
        self.assertEqual(v.delivery_year, "2027/2028")
        self.assertAlmostEqual(
            forward_net_cone_anchor("PJM", 2027, "reindex_net", rate=0.5),
            v.net_cone_curve_per_kw_yr,
            places=12,
        )
        # A pre-span year holds-first and likewise never escalates downward.
        self.assertAlmostEqual(
            forward_net_cone_anchor("PJM", 2010, "reindex_net", rate=0.5),
            resolve_demand_curve_vintage("PJM", 2010).net_cone_curve_per_kw_yr,
            places=12,
        )

    def test_reindex_gross_re_nets_the_offset(self):
        # gross = net + offset; escalate gross; re-subtract offset.
        v = resolve_demand_curve_vintage("PJM", 2050)
        last_start = int(v.delivery_year[:4])
        base = v.net_cone_curve_per_kw_yr
        offset, rate, year = 60.0, 0.03, last_start + 4
        got = forward_net_cone_anchor(
            "PJM", year, "reindex_gross", rate=rate, eas_offset_per_kw_yr=offset
        )
        expect = (base + offset) * (1.0 + rate) ** (year - last_start) - offset
        self.assertAlmostEqual(got, expect, places=9)
        # A rising gross with a flat offset moves net-CONE MORE than reindex_net
        # (the offset is a smaller base), which is why the field re-nets rather
        # than indexing net directly — asserted directionally here.
        self.assertGreater(
            got, forward_net_cone_anchor("PJM", year, "reindex_net", rate=rate)
        )

    def test_reindex_gross_requires_offset(self):
        with self.assertRaises(ValueError):
            forward_net_cone_anchor("PJM", 2050, "reindex_gross", rate=0.02)

    def test_unknown_escalation_raises(self):
        with self.assertRaises(ValueError):
            forward_net_cone_anchor("PJM", 2050, "bogus")


class TestEscalationRegistryHygiene(unittest.TestCase):
    """The cited escalation-rate registry vs the capacity-market design."""

    def test_every_capacity_market_iso_has_a_rate(self):
        # Exactly the capacity-market ISOs (those with a MarketDesign
        # capacity_market=True) carry a rate; ERCOT (energy-only) is absent.
        cap_isos = {iso for iso, d in MARKET_DESIGN.items() if d.capacity_market}
        self.assertEqual(set(NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO), cap_isos)
        self.assertNotIn("ERCOT", NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO)

    def test_central_rates_are_inflation_only_zero_real(self):
        # The cited central finding (field escalates gross + re-nets; Brattle
        # out-year guidance is inflation-only — ~0.0 real). A non-zero central
        # rate would be a forecast-of-real-net-CONE-growth, which the field does
        # not do — a positive rate is a SCENARIO input, never the default.
        for iso, rate in NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO.items():
            self.assertEqual(rate, 0.0, msg=iso)

    def test_vintage_isos_all_have_a_rate(self):
        # Every ISO with a vintage table (the reindex modes act on it) has a rate.
        for iso in MARKET_DESIGN_VINTAGES:
            self.assertIn(iso, NET_CONE_FORWARD_ESCALATION_REAL_BY_ISO)


class TestScenarioConfigField(unittest.TestCase):
    """The default-OFF ScenarioConfig switch + cache/backcast invariants."""

    def test_default_is_hold_last(self):
        self.assertEqual(ScenarioConfig().net_cone_forward_escalation, "hold_last")

    def test_field_is_cache_optional(self):
        self.assertIn("net_cone_forward_escalation", _CACHE_KEY_OPTIONAL_FIELDS)

    def test_default_cache_key_is_neutral(self):
        # Setting the field to its default must NOT change the cache key vs a
        # bare default config (the field is dropped from the hash at default).
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(net_cone_forward_escalation="hold_last").cache_key(),
        )

    def test_reindex_mode_changes_cache_key(self):
        # A reindex run IS a distinct forward-capacity-price scenario — distinct
        # key (so it never collides with a cached hold_last run).
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(net_cone_forward_escalation="reindex_net").cache_key(),
        )
        self.assertNotEqual(
            ScenarioConfig(net_cone_forward_escalation="reindex_net").cache_key(),
            ScenarioConfig(net_cone_forward_escalation="reindex_gross").cache_key(),
        )

    def test_backcast_coerces_to_hold_last(self):
        # A backcast has no capacity evolution — the axis is inert; coerce to
        # hold_last so a backcast that sets it non-default stays byte-identical.
        bc = ScenarioConfig(mode="backcast", net_cone_forward_escalation="reindex_net")
        self.assertEqual(bc.net_cone_forward_escalation, "hold_last")
        self.assertEqual(bc.cache_key(), ScenarioConfig(mode="backcast").cache_key())

    def test_hindcast_forecast_path_not_coerced(self):
        # A capacity-hindcast (mode="forecast", hindcast=True) IS the forecast
        # path and arms forecast screens explicitly — it is NOT coerced.
        hc = ScenarioConfig(
            mode="forecast", hindcast=True, net_cone_forward_escalation="reindex_net"
        )
        self.assertEqual(hc.net_cone_forward_escalation, "reindex_net")

    def test_invalid_label_raises(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(net_cone_forward_escalation="bogus")


if __name__ == "__main__":
    unittest.main()
