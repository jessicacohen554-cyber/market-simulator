"""Tests for the SRMC-priced coal synchronization tranche (rebuild step 3a).

``ScenarioConfig.coal_sync_srmc_tranche`` splits the coal min-load band (sized
to the measured online Pmin by ``coal_mustrun_online_pmin``) by the measured
EIA-923 Sch-5 contract share into a fuel-free ``_mustrun`` floor and a
full-SRMC ``_sync`` band, BOTH forced on (synchronized) via ``min_gen``. See
docs/multi-iso/pjm-coal-operations-firstprinciples-2026-06.md (Thread D).
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    RAMP10_FRAC_BY_GROUP,
    _ramp10_capability,
    bins_to_fleet,
    campd_tranche_fuel_frac,
)

ZONES = ["AEP"]


def _coal_row(code: int, name: str) -> dict:
    """One synthetic coal (COAL_PRB) bin row (one plant) at a 27% online-Pmin floor."""
    return {
        "Plant_Group": "COAL_PRB",
        "ERCOT_Zone": "AEP",
        "Bin_Number": 1,
        "Bin_Label": name,
        "Plant_Code": code,
        "Plant_Name": name,
        "Turbine_Class": "",
        "capacity_mw": 1000.0,
        "hr_weighted": 10.0,
        "pct_mr": 27.0,
        "pct_mc": 5.0,
        "pct_econ": 66.0,
        "pct_peak": 2.0,
        "min_run": 0,
        "min_down": 0,
        "hr_mr": 10.5,
        "hr_mc": 10.2,
        "hr_econ": 10.0,
        "hr_peak": 12.0,
        "plant_count": 1,
        "plant_codes": [code],
        "fuel": "coal",
    }


# Gavin 8102 is 100% contracted (take-or-pay), Miami Fort 2832 is 0% (all spot)
# in the PJM artifact — the two extremes of the split.
_GAVIN, _MIAMI = 8102, 2832


def _build(sync_on: bool) -> tuple[list[Generator], object]:
    bins = pd.DataFrame([_coal_row(_GAVIN, "Gavin"), _coal_row(_MIAMI, "Miami Fort")])
    cfg = ScenarioConfig(
        iso="PJM",
        weather_year=2024,
        mode="backcast",
        hours=8760,
        coal_takeorpay_from_data=True,
        coal_mustrun_online_pmin=True,
        coal_sync_srmc_tranche=sync_on,
    )
    return bins_to_fleet(bins, ZONES, cfg)


def _suffix(gen: Generator) -> str:
    return gen.unit_id.rsplit("_", 1)[1]


class TestFuelFrac(unittest.TestCase):
    """campd_tranche_fuel_frac pricing of the new _sync band."""

    def test_sync_bids_full_srmc(self):
        g = Generator(
            unit_id="COAL_X_p2832_sync",
            name="s",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
        )
        self.assertEqual(
            campd_tranche_fuel_frac(g, {"bituminous": 0.9}, {2832: 0.0}), 1.0
        )

    def test_mustrun_stays_fuel_free(self):
        g = Generator(
            unit_id="COAL_X_p2832_mustrun",
            name="m",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
        )
        self.assertEqual(campd_tranche_fuel_frac(g, {"bituminous": 0.9}, None), 0.0)


class TestCommittedTakeorpayBit(unittest.TestCase):
    """coal_bit_committed_takeorpay: contract-share discount on committed BIT."""

    def _committed(self, pc=2832, supply="bituminous"):
        return Generator(
            unit_id=f"COAL_X_p{pc}_committed",
            name="c",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
            plant_code=pc,
            coal_supply=supply,
        )

    def test_off_keeps_full_cost(self):
        # Flag off -> committed BIT bids the supply passthrough (1.0 here).
        g = self._committed()
        self.assertEqual(
            campd_tranche_fuel_frac(g, {"bituminous": 1.0}, {2832: 1.0}), 1.0
        )

    def test_fully_contracted_bids_fuel_free(self):
        g = self._committed()
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"bituminous": 1.0}, {2832: 1.0}, committed_takeorpay_bit=True
            ),
            0.0,
        )

    def test_partial_contract_passes_spot_share(self):
        g = self._committed()
        self.assertAlmostEqual(
            campd_tranche_fuel_frac(
                g, {"bituminous": 1.0}, {2832: 0.85}, committed_takeorpay_bit=True
            ),
            0.15,
        )

    def test_non_bituminous_unaffected(self):
        g = self._committed(supply="prb")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"prb": 1.0}, {2832: 1.0}, committed_takeorpay_bit=True
            ),
            1.0,
        )

    def test_plant_absent_from_map_unaffected(self):
        g = self._committed(pc=99999)
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"bituminous": 1.0}, {2832: 1.0}, committed_takeorpay_bit=True
            ),
            1.0,
        )

    def test_all_scope_discounts_prb(self):
        # committed_takeorpay_all extends the discount to every contracted coal
        # supply (PRB here); bit-only leaves PRB at full cost.
        g = self._committed(supply="prb")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"prb": 1.0}, {2832: 1.0}, committed_takeorpay_bit=True
            ),
            1.0,
        )
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"prb": 1.0}, {2832: 1.0}, committed_takeorpay_all=True
            ),
            0.0,
        )

    def test_all_scope_still_spares_econ(self):
        g = self._committed(supply="prb")
        g.unit_id = "COAL_X_p2832_econ1"
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"prb": 1.0}, {2832: 1.0}, committed_takeorpay_all=True
            ),
            1.0,
        )


class TestCommittedTakeorpayRegulated(unittest.TestCase):
    """coal_committed_takeorpay_regulated: the committed-band sunk-contract
    discount scoped by EIA-860 Regulatory Status (RE set) instead of coal
    rank — SOM Table 7's regulated/merchant conduct split
    (docs/handoffs/miso-coal-conduct-design-2026-07.md)."""

    def _committed(self, pc=2832, supply="prb"):
        return Generator(
            unit_id=f"COAL_X_p{pc}_committed",
            name="c",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
            plant_code=pc,
            coal_supply=supply,
        )

    def test_regulated_plant_discounts_any_supply(self):
        g = self._committed(supply="prb")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 1.0},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
            ),
            0.0,
        )

    def test_merchant_plant_keeps_full_cost(self):
        # An NR plant (absent from the RE set) bids the full supply
        # passthrough even when fully contracted — merchants offer
        # economically (SOM Table 7: 74-93% of merchant starts).
        g = self._committed(supply="bituminous")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"bituminous": 1.0},
                {2832: 1.0},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({999}),
            ),
            1.0,
        )

    def test_partial_contract_passes_spot_share(self):
        g = self._committed()
        self.assertAlmostEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 0.85},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
            ),
            0.15,
        )

    def test_no_set_means_no_discount(self):
        # Gate on but no RE set threaded (regulated_plants=None) -> inert.
        g = self._committed()
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 1.0},
                committed_takeorpay_regulated=True,
                regulated_plants=None,
            ),
            1.0,
        )

    def test_union_with_bit_flag(self):
        # Stacked flags act as a union: an NR bituminous plant still gets
        # the BIT-scope discount when that flag is also armed (backward
        # replay of miso-62/63/64/65 bundles).
        g = self._committed(supply="bituminous")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"bituminous": 1.0},
                {2832: 1.0},
                committed_takeorpay_bit=True,
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({999}),
            ),
            0.0,
        )

    def test_scope_set_membership_freeze(self):
        # Freeze the measured scope resolution on the design doc's decision
        # plants (rule 23: re-derives only on a new EIA-860 vintage).
        from market_sim.data.fleet import eia860_selfcommit_scope_plants

        scope = eia860_selfcommit_scope_plants()
        if not scope:
            self.skipTest("no EIA-860 plant parquet on disk")
        for pc in (55856, 6705, 1733, 2103):  # Prairie State, Warrick, Monroe, Labadie
            self.assertIn(pc, scope)
        for pc in (889, 6017, 56456, 6055, 10865, 50835):
            # Baldwin, Newton, Plum Point, Big Cajun 2, ADM Decatur, Filer City
            self.assertNotIn(pc, scope)

    def test_spares_econ_and_mustrun_semantics(self):
        # econ tranches keep full cost; _mustrun keeps its own (pre-existing)
        # contract-share rule independent of the regulated gate.
        g = self._committed()
        g.unit_id = "COAL_X_p2832_econ1"
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 1.0},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
            ),
            1.0,
        )


class TestSyncSplit(unittest.TestCase):
    """The min-load band split + forcing under coal_sync_srmc_tranche."""

    def test_off_keeps_step2_behaviour(self):
        fleet, fa = _build(sync_on=False)
        self.assertNotIn("sync", {_suffix(g) for g in fleet})
        self.assertIsNone(fa.min_gen)  # no forcing
        for g in fleet:
            self.assertEqual(g.coal_sync_pmin_mw, 0.0)

    def test_fully_contracted_plant_keeps_fuelfree_floor(self):
        """Gavin (100% contract): whole online-Pmin band stays _mustrun."""
        fleet, _ = _build(sync_on=True)
        gavin = [g for g in fleet if g.plant_code == _GAVIN]
        suff = {_suffix(g) for g in gavin}
        self.assertIn("mustrun", suff)
        self.assertNotIn("sync", suff)  # spot share is 0

    def test_all_spot_plant_gets_srmc_sync_band(self):
        """Miami Fort (0% contract): whole online-Pmin band becomes _sync."""
        fleet, _ = _build(sync_on=True)
        miami = [g for g in fleet if g.plant_code == _MIAMI]
        suff = {_suffix(g) for g in miami}
        self.assertIn("sync", suff)
        self.assertNotIn("mustrun", suff)  # contracted share is 0

    def test_split_preserves_total_minload(self):
        """mr + sync capacity == the original online-Pmin band (27% of 1000)."""
        fleet, _ = _build(sync_on=True)
        for code in (_GAVIN, _MIAMI):
            band = sum(
                g.pmax_mw
                for g in fleet
                if g.plant_code == code and _suffix(g) in ("mustrun", "sync")
            )
            self.assertAlmostEqual(band, 270.0, places=1)

    def test_minload_forced_on(self):
        """The _mustrun/_sync bands are forced on via min_gen (synchronized)."""
        fleet, fa = _build(sync_on=True)
        self.assertIsNotNone(fa.min_gen)
        for g in fleet:
            if _suffix(g) in ("mustrun", "sync"):
                self.assertGreater(g.coal_sync_pmin_mw, 0.0)
                self.assertAlmostEqual(g.coal_sync_pmin_mw, g.pmax_mw, places=1)
            else:
                self.assertEqual(g.coal_sync_pmin_mw, 0.0)
        # min_gen is forced positive for the sync tranches (clipped to
        # availability, so below nameplate but well above zero).
        sync_idx = [
            i
            for i, u in enumerate(fa.unit_ids)
            if u.endswith("_sync") or u.endswith("_mustrun")
        ]
        self.assertTrue((fa.min_gen[sync_idx, 0] > 0.0).all())


class TestRamp10(unittest.TestCase):
    """The forward-reproducible 10-minute ramp capability (step 3b unblock)."""

    def test_ramp10_by_class(self):
        gens = [
            Generator(
                unit_id="COAL_a",
                name="a",
                zone="X",
                fuel_type="coal",
                pmax_mw=1000,
                plant_group="COAL_PRB",
            ),
            Generator(
                unit_id="CT_b",
                name="b",
                zone="X",
                fuel_type="gas_ct",
                pmax_mw=200,
                plant_group="CT_PEAKER",
            ),
            Generator(
                unit_id="NUC_c",
                name="c",
                zone="X",
                fuel_type="nuclear",
                pmax_mw=1300,
                plant_group="",
            ),
        ]
        r = _ramp10_capability(gens, np.array([1000.0, 200.0, 1300.0]))
        self.assertAlmostEqual(r[0], RAMP10_FRAC_BY_GROUP["COAL_PRB"] * 1000.0)
        self.assertAlmostEqual(r[1], RAMP10_FRAC_BY_GROUP["CT_PEAKER"] * 200.0)
        self.assertEqual(r[2], 0.0)  # nuclear carries no upward reserve

    def test_fleet_arrays_carry_ramp10(self):
        _, fa = _build(sync_on=True)
        self.assertIsNotNone(fa.ramp10)
        self.assertEqual(len(fa.ramp10), fa.n_gen)
        self.assertTrue((fa.ramp10 >= 0.0).all())


class TestCommittedTakeorpaySunkFixed(unittest.TestCase):
    """coal_committed_takeorpay_sunk_fixed: the contract is an accounting-period
    tonnage obligation, so it is a sunk FIXED cost and must not discount the
    marginal MWh. Suppresses the committed-band discount of all three scopes
    while leaving `_mustrun` — the band that is on regardless of price, and the
    one place the contract is legitimately carried — untouched (miso-96,
    rules 17 [R-FLOOR-WINDOW] / 19 [R-ONE-MECH])."""

    def _gen(self, suffix, pc=2832, supply="prb"):
        return Generator(
            unit_id=f"COAL_X_p{pc}_{suffix}",
            name="c",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
            plant_code=pc,
            coal_supply=supply,
        )

    def test_suppresses_regulated_committed_discount(self):
        g = self._gen("committed")
        kw = dict(
            committed_takeorpay_regulated=True,
            regulated_plants=frozenset({2832}),
        )
        # control: the discount is live and drives the band to fully-sunk fuel
        self.assertEqual(
            campd_tranche_fuel_frac(g, {"prb": 1.0}, {2832: 1.0}, **kw), 0.0
        )
        # armed: the committed band reverts to its full supply passthrough
        self.assertEqual(
            campd_tranche_fuel_frac(
                g, {"prb": 1.0}, {2832: 1.0}, committed_takeorpay_sunk_fixed=True, **kw
            ),
            1.0,
        )

    def test_suppresses_bit_and_all_scopes_too(self):
        g = self._gen("committed", supply="bituminous")
        for scope in ("committed_takeorpay_bit", "committed_takeorpay_all"):
            with self.subTest(scope=scope):
                kw = {scope: True}
                self.assertEqual(
                    campd_tranche_fuel_frac(g, {"bituminous": 1.0}, {2832: 1.0}, **kw),
                    0.0,
                )
                self.assertEqual(
                    campd_tranche_fuel_frac(
                        g,
                        {"bituminous": 1.0},
                        {2832: 1.0},
                        committed_takeorpay_sunk_fixed=True,
                        **kw,
                    ),
                    1.0,
                )

    def test_mustrun_band_keeps_its_contract_discount(self):
        # The contract stays carried ONCE, on the band that runs regardless of
        # price — suppressing the committed discount must not touch `_mustrun`.
        g = self._gen("mustrun")
        self.assertAlmostEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 0.85},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
                committed_takeorpay_sunk_fixed=True,
            ),
            0.15,
        )

    def test_default_off_is_byte_identical(self):
        # Every existing keeper must be unmoved: the default must reproduce the
        # armed-discount value exactly.
        g = self._gen("committed")
        kw = dict(
            committed_takeorpay_regulated=True,
            regulated_plants=frozenset({2832}),
        )
        self.assertEqual(
            campd_tranche_fuel_frac(g, {"prb": 1.0}, {2832: 0.85}, **kw),
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 0.85},
                committed_takeorpay_sunk_fixed=False,
                **kw,
            ),
        )


class TestPrbCommittedDispatchable(unittest.TestCase):
    """coal_prb_committed_dispatchable: PRB/subbituminous plants are excluded
    from the committed-band take-or-pay discount — their committed band bids
    full delivered cost like a merchant's, while BIT/lignite keep the
    discount and `_mustrun` is untouched (miso-111,
    PREREG-miso111-prb-committed-flex-2026-07-31.md §8)."""

    _PRB_DISPATCH = frozenset({"prb", "subbituminous"})

    def _gen(self, suffix, pc=2832, supply="prb"):
        return Generator(
            unit_id=f"COAL_X_p{pc}_{suffix}",
            name="c",
            zone="X",
            fuel_type="coal",
            pmax_mw=100,
            plant_group="COAL_PRB",
            plant_code=pc,
            coal_supply=supply,
        )

    def test_regulated_prb_committed_bids_full_cost(self):
        g = self._gen("committed", supply="prb")
        self.assertEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 1.0},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
                committed_dispatchable_supplies=self._PRB_DISPATCH,
            ),
            1.0,
        )

    def test_regulated_bit_keeps_discount(self):
        # The exclusion is supply-scoped: a regulated bituminous plant's
        # committed band keeps its sunk-contract discount (the miso-102
        # COAL_BIT overshoot protection is by construction).
        g = self._gen("committed", supply="bituminous")
        self.assertAlmostEqual(
            campd_tranche_fuel_frac(
                g,
                {"bituminous": 1.0},
                {2832: 0.85},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
                committed_dispatchable_supplies=self._PRB_DISPATCH,
            ),
            0.15,
        )

    def test_mustrun_band_untouched(self):
        # The self-commitment stays carried once, on `_mustrun` (rule 19).
        g = self._gen("mustrun", supply="prb")
        self.assertAlmostEqual(
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 0.85},
                committed_takeorpay_regulated=True,
                regulated_plants=frozenset({2832}),
                committed_dispatchable_supplies=self._PRB_DISPATCH,
            ),
            0.15,
        )

    def test_default_none_is_byte_identical(self):
        # Default off: every existing keeper unmoved.
        g = self._gen("committed", supply="prb")
        kw = dict(
            committed_takeorpay_regulated=True,
            regulated_plants=frozenset({2832}),
        )
        self.assertEqual(
            campd_tranche_fuel_frac(g, {"prb": 1.0}, {2832: 1.0}, **kw),
            campd_tranche_fuel_frac(
                g,
                {"prb": 1.0},
                {2832: 1.0},
                committed_dispatchable_supplies=None,
                **kw,
            ),
        )


if __name__ == "__main__":
    unittest.main()
