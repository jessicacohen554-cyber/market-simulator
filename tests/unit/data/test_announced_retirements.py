"""Tests for the owner-filed FOSSIL announced-date loader (capx D42).

``data.announced_retirements`` reads a vintage EIA-860 snapshot's Schedule-3
planned retirement dates for an ISO's operable fossil units (the rule-13
vintage gate: a date is admissible only because it was on file at the
snapshot's cutoff), optionally VERIFIES them against later in-repo vintages
(a filed deferral / withdrawal is honored per unit; nothing is injected or
advanced), drops reversal-registry plants, and records every disposition.

Trivial synthetic vintages in a tmp root first (rule: 1 gen, 1 plant, then
scale), then the committed-data case (MISO vintage 2020 — the D32 §4.3
magnitudes).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from market_sim.data import announced_retirements as ar
from market_sim.data.fleet.models import BA_CODE_TO_ISO, EIA_860_PARQUET_NAME
from market_sim.model.capacity_evolution.retirements import _FOSSIL_FUELS

_MISO_BA = next(k for k, v in BA_CODE_TO_ISO.items() if v == "MISO")
_OTHER_BA = next(k for k, v in BA_CODE_TO_ISO.items() if v == "PJM")


def _row(
    plant,
    gid,
    *,
    ry=None,
    rm=None,
    status="OP",
    ba=_MISO_BA,
    tech="Conventional Steam Coal",
    src="BIT",
    mover="ST",
    mw=100.0,
    summer=95.0,
    sector=1,
    name="P",
):
    return {
        "plant_id": plant,
        "generator_id": gid,
        "plant_name": name,
        "state": "IN",
        "balancing_authority_code": ba,
        "technology": tech,
        "energy_source": src,
        "prime_mover": mover,
        "nameplate_capacity_mw": mw,
        "net_summer_capacity_mw": summer,
        "operating_year": 1975,
        "planned_retirement_year": ry,
        "status": status,
        "heat_rate": 10.0,
        "_rm": rm,
        "_sector": sector,
    }


def _write_vintage(root: Path, year: int, rows: list[dict]) -> Path:
    d = root / f"vintage_{year}"
    d.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    canon = df.drop(columns=["_rm", "_sector"])
    canon["planned_retirement_year"] = pd.to_numeric(canon["planned_retirement_year"])
    canon.to_parquet(d / EIA_860_PARQUET_NAME, index=False)
    sheet = pd.DataFrame(
        {
            "Plant Code": df["plant_id"],
            "Generator ID": df["generator_id"],
            "Planned Retirement Month": df["_rm"],
            "Sector": df["_sector"],
        }
    )
    sheet.to_parquet(d / ar._OPERABLE_SHEET_NAME, index=False)
    return d


class TestFuelSetPinned(unittest.TestCase):
    def test_fossil_fuels_match_the_announced_step_exemption(self):
        # The loader's fuel set IS the set the non-fossil announced step
        # exempts (duplicated to keep data free of a model import).
        self.assertEqual(ar.FOSSIL_FUELS, _FOSSIL_FUELS)


class TestVintageSet(unittest.TestCase):
    """Ex-ante posture: the vintage's own dated fossil OP units, nothing else."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.v2020 = _write_vintage(
            self.root,
            2020,
            [
                _row(1, "1", ry=2023, rm=6, name="Coal A"),  # dated coal
                _row(1, "2", ry=None, name="Coal A"),  # undated sibling
                _row(2, "1", ry=2022, rm=None, mw=0.0, summer=50.0),  # summer fallback
                _row(3, "1", ry=2024, status="SB"),  # not operable -> excluded
                _row(4, "1", ry=2024, ba=_OTHER_BA),  # other ISO -> excluded
                _row(5, "1", ry=2024, tech="Nuclear", src="NUC"),  # non-fossil
                _row(
                    6,
                    "GT1",
                    ry=2025,
                    rm=13,
                    tech="Natural Gas Fired Combustion Turbine",
                    src="NG",
                    mover="GT",
                ),  # bad month -> None
            ],
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_membership_and_provenance(self):
        rows = ar.load_announced_fossil_exits(
            "MISO", self.v2020, vintage_root=self.root
        )
        keyed = {(r.plant_id, r.generator_id): r for r in rows}
        self.assertEqual(set(keyed), {(1, "1"), (2, "1"), (6, "GT1")})
        a = keyed[(1, "1")]
        self.assertEqual((a.exit_year, a.exit_month, a.mw), (2023, 6, 100.0))
        self.assertEqual(a.fuel_type, "coal")
        self.assertEqual(a.filed_vintage, 2020)
        self.assertEqual(a.disposition, ar.DISPOSITION_VINTAGE)
        self.assertEqual(a.sector, 1)
        self.assertIsNone(a.verified_vintage)
        # Nameplate 0 -> summer fallback.
        self.assertEqual(keyed[(2, "1")].mw, 50.0)
        # Out-of-range month is dropped, not honored.
        self.assertIsNone(keyed[(6, "GT1")].exit_month)
        self.assertEqual(keyed[(6, "GT1")].fuel_type, "gas_ct")
        # Sorted by (exit_year, plant, gid).
        self.assertEqual([r.exit_year for r in rows], [2022, 2023, 2025])

    def test_reversed_plant_is_dropped_but_audited(self):
        live = ar.load_announced_fossil_exits(
            "MISO",
            self.v2020,
            reversed_plant_codes=frozenset({1}),
            vintage_root=self.root,
        )
        self.assertNotIn(1, {r.plant_id for r in live})
        table = ar.disposition_table(
            "MISO",
            self.v2020,
            reversed_plant_codes=frozenset({1}),
            vintage_root=self.root,
        )
        rev = [r for r in table if r.plant_id == 1]
        self.assertEqual([r.disposition for r in rev], [ar.DISPOSITION_REVERSED])

    def test_missing_snapshot_is_empty(self):
        self.assertEqual(
            ar.load_announced_fossil_exits("MISO", self.root / "nowhere"), []
        )

    def test_no_later_vintages_means_verify_is_identity(self):
        ex = ar.load_announced_fossil_exits("MISO", self.v2020, vintage_root=self.root)
        ver = ar.load_announced_fossil_exits(
            "MISO", self.v2020, verify=True, vintage_root=self.root
        )
        self.assertEqual(
            [(r.plant_id, r.generator_id, r.exit_year, r.exit_month) for r in ex],
            [(r.plant_id, r.generator_id, r.exit_year, r.exit_month) for r in ver],
        )
        self.assertTrue(all(r.disposition == ar.DISPOSITION_VINTAGE for r in ver))


class TestVerificationPosture(unittest.TestCase):
    """Later-vintage verification: defer / cancel / exited / kept / advanced."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.v2020 = _write_vintage(
            self.root,
            2020,
            [
                _row(10, "1", ry=2023, rm=6),  # deferred in 2021 to 2026
                _row(11, "1", ry=2022, rm=10),  # cancelled in 2022 (sold)
                _row(12, "1", ry=2021, rm=10),  # absent later: exited
                _row(13, "1", ry=2024, rm=12),  # kept as filed
                _row(14, "1", ry=2022, rm=12),  # re-filed EARLIER (2022/6)
                _row(15, "1", ry=2025, rm=None),  # deferred in 2022 only
                _row(16, "1", ry=None),  # never dated; later filed 2024 -> NOT injected
            ],
        )
        _write_vintage(
            self.root,
            2021,
            [
                _row(10, "1", ry=2026, rm=None),
                _row(11, "1", ry=2022, rm=10),
                _row(13, "1", ry=2024, rm=12),
                _row(14, "1", ry=2022, rm=6),
                _row(15, "1", ry=2025, rm=None),
                _row(16, "1", ry=None),
            ],
        )
        _write_vintage(
            self.root,
            2022,
            [
                _row(10, "1", ry=2026, rm=None),
                _row(11, "1", ry=None),
                _row(13, "1", ry=2024, rm=12),
                _row(15, "1", ry=2027, rm=3),
                _row(16, "1", ry=2024, rm=1),
            ],
        )

    def tearDown(self):
        self._tmp.cleanup()

    def test_later_vintage_dirs_are_strictly_later_and_sorted(self):
        got = ar.later_vintage_dirs(2020, self.root)
        self.assertEqual([y for y, _ in got], [2021, 2022])
        self.assertEqual([y for y, _ in ar.later_vintage_dirs(2022, self.root)], [])

    def test_dispositions(self):
        table = {
            r.plant_id: r
            for r in ar.disposition_table(
                "MISO", self.v2020, verify=True, vintage_root=self.root
            )
        }
        # Deferred: the later vintage's date is honored; first change 2021.
        d = table[10]
        self.assertEqual(d.disposition, ar.DISPOSITION_DEFERRED)
        self.assertEqual((d.exit_year, d.exit_month), (2026, None))
        self.assertEqual((d.vintage_exit_year, d.vintage_exit_month), (2023, 6))
        self.assertEqual((d.first_change_vintage, d.verified_vintage), (2021, 2022))
        # Cancelled: date dropped in vintage 2022 (2021 still carried it).
        c = table[11]
        self.assertEqual(c.disposition, ar.DISPOSITION_CANCELLED)
        self.assertEqual((c.first_change_vintage, c.verified_vintage), (2022, 2022))
        # Exited: absent from every later vintage -> vintage date stands.
        e = table[12]
        self.assertEqual(e.disposition, ar.DISPOSITION_EXITED)
        self.assertEqual((e.exit_year, e.exit_month), (2021, 10))
        self.assertIsNone(e.first_change_vintage)
        # Kept.
        k = table[13]
        self.assertEqual(k.disposition, ar.DISPOSITION_KEPT)
        self.assertEqual(k.verified_vintage, 2022)
        # Advanced: recorded, but the vintage date STANDS (never advance).
        a = table[14]
        self.assertEqual(a.disposition, ar.DISPOSITION_ADVANCED)
        self.assertEqual((a.exit_year, a.exit_month), (2022, 12))
        self.assertEqual(a.first_change_vintage, 2021)
        # Deferred only by the LATEST vintage: first change is 2022.
        f = table[15]
        self.assertEqual(f.disposition, ar.DISPOSITION_DEFERRED)
        self.assertEqual((f.exit_year, f.exit_month), (2027, 3))
        self.assertEqual(f.first_change_vintage, 2022)
        # Never injected: plant 16 was undated at the vintage.
        self.assertNotIn(16, table)

    def test_live_set_drops_cancelled_only(self):
        live = ar.load_announced_fossil_exits(
            "MISO", self.v2020, verify=True, vintage_root=self.root
        )
        self.assertEqual(sorted(r.plant_id for r in live), [10, 12, 13, 14, 15])

    def test_records_are_json_ready(self):
        recs = ar.rows_as_records(
            ar.disposition_table(
                "MISO", self.v2020, verify=True, vintage_root=self.root
            )
        )
        self.assertEqual(
            set(recs[0]),
            {
                "plant_id",
                "generator_id",
                "plant_name",
                "fuel",
                "mw",
                "sector",
                "filed_vintage",
                "vintage_exit_year",
                "vintage_exit_month",
                "exit_year",
                "exit_month",
                "disposition",
                "verified_vintage",
                "first_change_vintage",
            },
        )


_V2020 = Path("data/raw/eia-860/vintage_2020")


@unittest.skipUnless(
    (_V2020 / EIA_860_PARQUET_NAME).exists(), "MISO vintage data not hydrated"
)
class TestCommittedMisoVintage2020(unittest.TestCase):
    """The committed-data case behind D32 §4.3 / the D42 pre-declaration."""

    def test_ex_ante_and_verified_magnitudes(self):
        ex = ar.load_announced_fossil_exits("MISO", _V2020)
        ver = ar.load_announced_fossil_exits("MISO", _V2020, verify=True)

        def gw(rows, fuel=None):
            return (
                sum(
                    (r.mw or 0.0)
                    for r in rows
                    if r.exit_year <= 2025 and (fuel is None or r.fuel_type == fuel)
                )
                / 1000.0
            )

        # Every returned row is dated and fossil.
        self.assertTrue(all(r.fuel_type in ar.FOSSIL_FUELS for r in ex))
        # Ex-ante the 2020 vintage dates ~21-22 GW of MISO fossil capacity
        # through 2025, coal-dominated; verification against the later
        # vintages (the filed deferrals / sales) leaves ~12 GW.
        self.assertGreater(gw(ex), 20.0)
        self.assertLess(gw(ex), 23.0)
        self.assertGreater(gw(ex, "coal"), 17.0)
        self.assertGreater(gw(ver), 11.0)
        self.assertLess(gw(ver), 13.5)
        self.assertLess(gw(ver), gw(ex))
        # The deferral class is countered by a published re-filing, per unit:
        # Baldwin 1-2 (889) -> 2027, Coal Creek (6030) withdrawn, Merom
        # (6213) withdrawn, Columbia (8023) -> 2029, Schahfer 17/18 -> 2026,
        # Edgewater 5 (4050) withdrawn.
        by_plant = {}
        for r in ver:
            by_plant.setdefault(r.plant_id, []).append(r)
        self.assertTrue(all(r.exit_year >= 2027 for r in by_plant[889]))
        self.assertNotIn(6030, by_plant)
        self.assertNotIn(6213, by_plant)
        self.assertNotIn(4050, by_plant)
        self.assertTrue(all(r.exit_year >= 2029 for r in by_plant[8023]))
        self.assertTrue(
            all(
                r.exit_year >= 2026
                for r in by_plant[6085]
                if r.generator_id in ("17", "18")
            )
        )
        # Never advanced: no verified row exits earlier than its vintage date.
        for r in ver:
            self.assertGreaterEqual(
                (r.exit_year, r.exit_month or 12),
                (r.vintage_exit_year, r.vintage_exit_month or 12),
            )


if __name__ == "__main__":
    unittest.main()
