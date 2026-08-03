"""The two write-only diagnostic sidecars: ``unit_hourly`` and ``network``.

Both are built from a solved :class:`DispatchResult` and written under a
bundle's ``hourly/`` directory, which escapes the slim-bundle gitignore so a
KEEPER bundle can carry them (CLAUDE.md rule 15). They exist because a slim
bundle otherwise exposes no per-unit series at all (blocking the plant-level
ONLINE reserve measure of the caiso-131 ask §4 D1) and no transmission duals
(so ``FINDING-caiso132`` §2 could not say WHICH import limit binds).

These tests pin the two properties that make them safe and useful: the frames
are a faithful, lossless view of the solved arrays, and building them cannot
touch the LP.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pandas as pd  # noqa: E402

from market_sim.config.iso_configs import TransferLink  # noqa: E402
from market_sim.model.dispatch import solve_dispatch  # noqa: E402
from market_sim.model.transmission import (  # noqa: E402
    build_incidence_matrix,
    get_ttc_array,
)
from run_calibration_full import (  # noqa: E402
    _network_frame,
    _reserve_family_frame,
    _unit_hourly_frame,
    _write_hourly_sidecar,
)

from tests.unit.model.test_dispatch import _make_fleet  # noqa: E402


class _Ctx:
    """The three ``context`` attributes the unit frame reads."""

    def __init__(self, unit_ids, fuel_types, zones):
        self.unit_ids = unit_ids
        self.fuel_types = fuel_types
        self.zones = zones


def _solved(T=6, link_ttc=6000.0, groups=None):
    """Trivial 2-zone, 1-link solve (CLAUDE.md: trivial case first)."""
    zone_names = ["Z0", "Z1"]
    fleet = _make_fleet(
        ["Z0", "Z1"], zone_names, hours=T, pmax=10000.0, pmin=0.0, eford=0.0
    )
    links = [TransferLink(from_zone="Z0", to_zone="Z1", ttc_mw=link_ttc)]
    res = solve_dispatch(
        fleet,
        np.array([np.zeros(T), np.full(T, 5000.0)]),
        mc=np.vstack([np.full(T, 10.0), np.full(T, 90.0)]),
        T=T,
        incidence=build_incidence_matrix(links, zone_names),
        ttc=get_ttc_array(links),
        wind_cf=np.zeros((2, T)),
        wind_cap=np.zeros(2),
        solar_cf=np.zeros((2, T)),
        solar_cap=np.zeros(2),
        interface_groups=groups,
    )
    ctx = _Ctx(list(fleet.unit_ids), ["gas"] * 2, ["Z0", "Z1"])
    return fleet, res, ctx, links, T


class TestUnitHourlySidecar(unittest.TestCase):
    def test_frame_reproduces_dispatch_and_availability_cap(self):
        fleet, res, ctx, _links, T = _solved()
        df = _unit_hourly_frame(2025, "P1", res, ctx, fleet, iso="CAISO")
        self.assertEqual(len(df), len(ctx.unit_ids) * T)
        piv = df.pivot_table(
            index="hour", columns="unit_id", values="mw", observed=True
        )
        for g, uid in enumerate(ctx.unit_ids):
            np.testing.assert_allclose(
                piv[uid].to_numpy(), res.dispatch[g], rtol=0, atol=1e-5
            )
        cap = df.pivot_table(
            index="hour", columns="unit_id", values="cap_mw", observed=True
        )
        expect = fleet.pmax[:, None] * fleet.availability
        for g, uid in enumerate(ctx.unit_ids):
            np.testing.assert_allclose(
                cap[uid].to_numpy(), expect[g], rtol=1e-6, atol=1e-4
            )

    def test_headroom_is_recoverable_and_never_negative(self):
        # The reason the sidecar exists: online headroom = cap - mw summed over
        # the units of a running plant (results.scarcity.reserve_headroom).
        fleet, res, ctx, _links, _T = _solved()
        df = _unit_hourly_frame(2025, "P1", res, ctx, fleet, iso="CAISO")
        self.assertTrue((df["cap_mw"] - df["mw"] >= -1e-4).all())

    def test_returns_none_on_fleet_dispatch_misalignment(self):
        # A misaligned bundle must degrade to "no sidecar", never to a wrong
        # one and never to a failed solve.
        fleet, res, ctx, _links, _T = _solved()
        res.dispatch = res.dispatch[:1]
        self.assertIsNone(_unit_hourly_frame(2025, "P1", res, ctx, fleet))


class TestNetworkSidecar(unittest.TestCase):
    def test_link_rows_carry_flow_dual_and_the_column_bounds(self):
        _fleet, res, _ctx, links, T = _solved(link_ttc=2000.0)
        df = _network_frame(2025, "P1", res, links)
        link = df[df["kind"] == "link"]
        self.assertEqual(len(link), T)
        self.assertEqual(link["name"].iloc[0], "Z0>Z1")
        np.testing.assert_allclose(link["mw"].to_numpy(), res.flows[0], atol=1e-4)
        np.testing.assert_allclose(link["limit_up"].to_numpy(), 2000.0, atol=1e-6)
        np.testing.assert_allclose(link["limit_dn"].to_numpy(), -2000.0, atol=1e-6)

    def test_group_rows_are_self_describing_and_close_the_identity(self):
        _fleet, res, _ctx, links, T = _solved(
            link_ttc=6000.0, groups=[(np.array([0]), 2000.0, False)]
        )
        df = _network_frame(2025, "P1", res, links)
        grp = df[df["kind"] == "group"]
        self.assertEqual(len(grp), T)
        # The label names its signed membership, so no group-name channel has
        # to be threaded through the solve path to identify it downstream.
        self.assertEqual(grp["name"].iloc[0], "grp:+Z0>Z1")
        np.testing.assert_allclose(grp["mw"].to_numpy(), res.flows[0], atol=1e-4)
        np.testing.assert_allclose(grp["limit_up"].to_numpy(), 2000.0, atol=1e-6)
        # spread == -(link reduced cost) - (group dual): the whole point.
        link = df[df["kind"] == "link"]
        spread = res.prices[1] - res.prices[0]
        np.testing.assert_allclose(
            spread,
            -link["dual"].to_numpy() - grp["dual"].to_numpy(),
            atol=1e-4,
        )

    def test_returns_none_without_links(self):
        _fleet, res, _ctx, _links, _T = _solved()
        self.assertIsNone(_network_frame(2025, "P1", res, []))


class TestSidecarWriter(unittest.TestCase):
    def test_writes_only_the_requested_year_and_round_trips(self):
        _fleet, res, _ctx, links, _T = _solved()
        a = _network_frame(2023, "P1", res, links)
        b = _network_frame(2024, "P1", res, links)
        with tempfile.TemporaryDirectory() as td:
            out = _write_hourly_sidecar(Path(td), 2024, "network", [a, b])
            self.assertEqual(out.name, "network_2024.parquet")
            back = pd.read_parquet(out)
            self.assertEqual(set(back["year"].unique()), {2024})
            pd.testing.assert_frame_equal(
                back.reset_index(drop=True), b.reset_index(drop=True), check_like=True
            )
            self.assertIsNone(_write_hourly_sidecar(Path(td), 2019, "network", [a, b]))


if __name__ == "__main__":
    unittest.main()


class TestDuplicateGroupLabels(unittest.TestCase):
    """Two groups over the same signed membership must stay separable.

    ``name`` is the sidecar's only group key, so a reader selecting by label
    would otherwise silently concatenate two groups' duals into one 2T-long
    series and get the arithmetic wrong without any error.
    """

    def test_repeat_membership_is_suffixed(self):
        _fleet, res, _ctx, links, T = _solved(
            link_ttc=6000.0,
            groups=[(np.array([0]), 2000.0, False), (np.array([0]), 2000.0, False)],
        )
        df = _network_frame(2025, "P1", res, links)
        names = sorted(df[df["kind"] == "group"]["name"].unique())
        self.assertEqual(names, ["grp:+Z0>Z1", "grp:+Z0>Z1#2"])
        for n in names:
            self.assertEqual(len(df[df["name"] == n]), T)


class TestSidecarEncoding(unittest.TestCase):
    """``hour`` must stay delta-packed — it is 88 % of the file otherwise.

    These frames are tall and narrow, so the tiled 0..8759 ramp falls back to
    PLAIN int32 and dominates: measured on the CAISO 2023 unit frame, 11.12 MB
    of a 12.60 MB file against 1.04 MB for the actual dispatch and capacity.
    Losing this encoding takes a 3-year keeper bundle from ~5 MB to ~38 MB and
    out of what rule 15 lets a keeper carry, with no test failing — hence this
    one.
    """

    def test_hour_column_is_delta_packed(self):
        import pyarrow.parquet as pq

        _fleet, res, ctx, _links, _T = _solved()
        frame = _unit_hourly_frame(2025, "P1", res, ctx, _fleet, iso="CAISO")
        with tempfile.TemporaryDirectory() as td:
            out = _write_hourly_sidecar(Path(td), 2025, "unit_hourly", [frame])
            md = pq.ParquetFile(out).metadata
            names = [md.schema.column(i).name for i in range(md.num_columns)]
            col = md.row_group(0).column(names.index("hour"))
            self.assertIn("DELTA_BINARY_PACKED", [str(e) for e in col.encodings])
            # And it still round-trips to the same values.
            back = pd.read_parquet(out)
            np.testing.assert_array_equal(
                back["hour"].to_numpy(), frame["hour"].to_numpy()
            )


class TestReserveFamilySidecar(unittest.TestCase):
    """``hourly/reserve_family_<year>.parquet`` — the per-family reserve dual.

    The third write-only sidecar, and the one that closes a standing all-ISO
    blind spot (nyiso-113 §8): ``DispatchResult.reserve_price_by_family`` is
    ``(T, n_fam)`` in memory but was discarded at persist time, while
    ``system``'s ``reserve_price`` is the cross-family SUM broadcast
    identically into every zone's rows. So NO committed bundle in ANY ISO
    could show whether a LOCATIONAL reserve family ever bound — and a gate
    written against the system column reads inert by construction.
    """

    @staticmethod
    def _fam(name, req, zone_mask, reserve_class=0):
        from market_sim.model.reserves.spec import ReserveFamily

        return ReserveFamily(
            name=name,
            requirement=np.asarray(req, dtype=float),
            zone_mask=np.asarray(zone_mask, dtype=bool),
            ordc_penalties=np.array([300.0, 850.0]),
            ordc_step_widths=np.array([190.0, 300.0]),
            reserve_class=reserve_class,
        )

    def _solved_two_family(self, T=6, sub_req=400.0):
        """2 zones, 2 nested families; ``sub_req`` sizes the zone-1-only one."""
        from types import SimpleNamespace

        zone_names = ["Z0", "Z1"]
        fleet = _make_fleet(
            ["Z0", "Z1"], zone_names, hours=T, pmax=10000.0, pmin=0.0, eford=0.0
        )
        # Zone 1's unit is small, so a large zone-1-only requirement must
        # shortfall while the system-wide family is met from zone 0.
        fleet.pmax = np.array([2000.0, 200.0])
        links = [TransferLink(from_zone="Z0", to_zone="Z1", ttc_mw=1000.0)]
        res = solve_dispatch(
            fleet,
            np.array([np.full(T, 800.0), np.full(T, 100.0)]),
            mc=np.vstack([np.full(T, 10.0), np.full(T, 30.0)]),
            T=T,
            incidence=build_incidence_matrix(links, zone_names),
            ttc=get_ttc_array(links),
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
            reserve_requirement=np.vstack([np.full(T, 300.0), np.full(T, sub_req)]),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([300.0, 850.0, 300.0, 850.0]),
            ordc_step_widths=np.array([190.0, 300.0, 190.0, 300.0]),
            reserve_balance_zone_mask=np.array([[True, True], [False, True]]),
            reserve_balance_ordc_counts=np.array([2, 2]),
            reserve_pergen_gen_idx=np.array([0, 1]),
            reserve_pergen_ramp10=np.array([500.0, 200.0]),
        )
        design = SimpleNamespace(
            families=[
                self._fam("system_10min", np.full(T, 300.0), [True, True]),
                self._fam("z1_10min", np.full(T, sub_req), [False, True]),
            ]
        )
        return res, design, T

    def test_zones_column_names_each_family_region(self):
        """``zones`` resolves the family's own mask — what makes it LOCATIONAL.

        Without it the frame cannot distinguish a zone-scoped requirement from
        a system-wide one: the two carry the same columns and the same row
        shape, and the family NAME is only a convention while the zone mask is
        the LP's actual scoping. A reader asking "did a LOCATIONAL family
        bind?" needs the region, not a naming habit.
        """
        res, design, T = self._solved_two_family()
        df = _reserve_family_frame(2025, "P1", res, design, ["Z0", "Z1"])
        got = dict(df.drop_duplicates(subset=["family"])[["family", "zones"]].values)
        self.assertEqual(got["system_10min"], "Z0|Z1")
        self.assertEqual(got["z1_10min"], "Z1")

    def test_zones_degrades_to_empty_rather_than_mislabelling(self):
        """A missing or mismatched zone list empties the column, never guesses.

        The mask is positional, so pairing it with the wrong-length zone list
        would silently attach one family's region to another. Degrading beats
        mislabelling: every other column stays usable.
        """
        res, design, T = self._solved_two_family()
        for zones in (None, [], ["Z0", "Z1", "Z2"]):
            df = _reserve_family_frame(2025, "P1", res, design, zones)
            self.assertEqual(set(df["zones"].unique()), {""}, f"zone list {zones!r}")

    def test_frame_names_each_family_and_closes_the_lp_identity(self):
        res, design, T = self._solved_two_family()
        df = _reserve_family_frame(2025, "P1", res, design)
        self.assertEqual(len(df), 2 * T)
        self.assertEqual(sorted(df["family"].unique()), ["system_10min", "z1_10min"])
        for f, fam in enumerate(design.families):
            rows = df[df["family"] == fam.name].sort_values("hour")
            np.testing.assert_allclose(
                rows["dual"].to_numpy(),
                res.reserve_price_by_family[:, f],
                rtol=0,
                atol=1e-3,
            )
            np.testing.assert_allclose(
                rows["requirement_mw"].to_numpy(), fam.requirement, atol=1e-6
            )
            # held + shortfall >= requirement — the LP row itself, now
            # checkable from the persisted frame alone (held_mw is the balance
            # row's own activity net of its ORDC steps, so no re-derivation of
            # the row's layout-dependent coefficients is needed).
            slack = (
                rows["held_mw"].to_numpy()
                + rows["shortfall_mw"].to_numpy()
                - fam.requirement
            )
            self.assertTrue((slack >= -1e-3).all())
            # And it is TIGHT exactly where the family prices.
            binds = rows["dual"].to_numpy() > 1e-9
            if binds.any():
                np.testing.assert_allclose(slack[binds], 0.0, atol=1e-3)
            # Cross-check held_mw against the zone-summed reserve dispatch on
            # this simple single-class layout, where the two must agree.
            zsum = res.reserve_dispatch[np.asarray(fam.zone_mask)].sum(axis=0)
            np.testing.assert_allclose(rows["held_mw"].to_numpy(), zsum, atol=1e-3)

    def test_locational_binding_is_visible_where_the_system_column_is_not(self):
        # The whole point. The zone-1-only family prices at its own $850 step
        # while the system-wide family is slack — a distinction the persisted
        # per-zone ``reserve_price`` (the family SUM, broadcast to every zone)
        # cannot express.
        res, design, _T = self._solved_two_family(sub_req=400.0)
        df = _reserve_family_frame(2025, "P1", res, design)
        sysrow = df[df["family"] == "system_10min"]
        subrow = df[df["family"] == "z1_10min"]
        self.assertTrue(np.allclose(sysrow["shortfall_mw"].to_numpy(), 0.0, atol=1e-6))
        self.assertTrue(np.all(subrow["shortfall_mw"].to_numpy() > 0.0))
        self.assertTrue(np.allclose(subrow["dual"].to_numpy(), 850.0, atol=1e-3))
        # And the system-level series every bundle already had is their sum,
        # so it cannot attribute the $850 to a zone.
        np.testing.assert_allclose(
            res.reserve_price,
            res.reserve_price_by_family.sum(axis=1),
            atol=1e-6,
        )

    def test_slack_family_is_recorded_too_not_just_binding_ones(self):
        # A family that never binds must still appear with dual 0 — "family X
        # never bound" is only a readable claim if non-binding rows exist.
        res, design, T = self._solved_two_family(sub_req=100.0)
        df = _reserve_family_frame(2025, "P1", res, design)
        self.assertEqual(len(df), 2 * T)
        self.assertTrue(np.allclose(df["shortfall_mw"].to_numpy(), 0.0, atol=1e-6))
        self.assertTrue(np.allclose(df["dual"].to_numpy(), 0.0, atol=1e-6))

    def test_returns_none_without_a_design_or_a_coopt(self):
        res, design, _T = self._solved_two_family()
        self.assertIsNone(_reserve_family_frame(2025, "P1", res, None))
        res.reserve_price_by_family = None
        self.assertIsNone(_reserve_family_frame(2025, "P1", res, design))

    def test_shape_mismatch_degrades_to_no_frame_never_a_mislabelled_one(self):
        # Family labels come from the design and duals from the LP positionally.
        # If they disagree the frame would attribute one family's dual to
        # another's name, which is worse than having no sidecar.
        res, design, _T = self._solved_two_family()
        design.families = design.families[:1]
        self.assertIsNone(_reserve_family_frame(2025, "P1", res, design))

    def test_round_trips_through_the_hourly_writer(self):
        res, design, _T = self._solved_two_family()
        a = _reserve_family_frame(2023, "P1", res, design)
        b = _reserve_family_frame(2024, "P1", res, design)
        with tempfile.TemporaryDirectory() as td:
            out = _write_hourly_sidecar(Path(td), 2024, "reserve_family", [a, b])
            self.assertEqual(out.name, "reserve_family_2024.parquet")
            back = pd.read_parquet(out)
            self.assertEqual(set(back["year"].unique()), {2024})
            pd.testing.assert_frame_equal(
                back.reset_index(drop=True), b.reset_index(drop=True), check_like=True
            )
