"""Rubric v3.9 — C8 scores each coal SUBCLASS as its own class (C8-SUBCLASS).

Owner ruling 2026-09-25 ("Yes" to docs/handoffs/RESULT-coal-sub-2026-09-25.md
§6): the D-2 forced-energy share, its class denominator, the rule-20 2 %
materiality line, the 30 % merchant cap and the grounded-above-budget
escalation apply to COAL_BIT / COAL_PRB / COAL_LIGNITE / COAL_WC separately,
never to one coal family.

Trivial cases first per the repo testing pattern: two one-unit coal plants,
one zone, 24 hours — one subclass over its cap, one under, on a family whose
POOLED share would pass.
"""

from __future__ import annotations

import numpy as np
import pytest

import scripts.calibration_verdict as cv
import scripts.legitimacy_diagnostics as ld
from market_sim.data.floor_mechanisms import MECH_RELIABILITY_FLOOR

HOURS = 24


def _two_subclass_fixture():
    """COAL_BIT: 50 % of its energy at a binding floor. COAL_PRB: ~8.3 %.

    BIT runs 10 MW flat (240 MWh) and is floored at 10 MW in hours 0-11
    (120 MWh forced). PRB runs 100 MW flat (2400 MWh) and is floored at
    100 MW in hours 0-1 (200 MWh forced). Pooled as one family that is
    320 / 2640 = 12.1 % — under the 30 % cap — which is exactly the
    over-cap subclass the family fold used to hide.
    """
    disp = np.array([[10.0] * HOURS, [100.0] * HOURS])
    floors = np.zeros_like(disp)
    floors[0, :12] = 10.0
    floors[1, :2] = 100.0
    mech = np.where(floors > 0, MECH_RELIABILITY_FLOOR, 0).astype(np.int8)
    klass = np.array(["COAL_BIT", "COAL_PRB"])
    return disp, floors, mech, klass


class TestD2PerSubclass:
    def test_class_vote_keeps_the_subclass(self):
        """aggregate_floors_by_plant no longer folds coal onto the family."""
        disp, floors, mech, _ = _two_subclass_fixture()
        arrays = {
            "min_gen": floors,
            "mechanism": mech,
            "unit_ids": np.array(["COAL_Z_p1_committed", "COAL_Z_p2_committed"]),
            "plant_code": np.array([1, 2]),
            "plant_group": np.array(["COAL_BIT", "COAL_PRB"]),
            "pmax": np.array([10.0, 100.0]),
        }
        _, _, _, groups, fk = ld.aggregate_floors_by_plant(arrays)
        assert groups.tolist() == ["COAL_BIT", "COAL_PRB"]
        assert "COAL" not in fk.names

    def test_one_subclass_over_cap_one_under(self):
        disp, floors, mech, klass = _two_subclass_fixture()
        res = ld.run_d2(disp, floors, mech, klass, year=2024, total_load_mwh=5280.0)
        by = {r["class"]: r for r in res.summary}
        assert set(by) == {"COAL_BIT", "COAL_PRB"}
        assert by["COAL_BIT"]["forced_share"] == pytest.approx(0.5)
        assert by["COAL_BIT"]["verdict"] == "FAIL"
        assert by["COAL_PRB"]["forced_share"] == pytest.approx(200 / 2400, abs=1e-4)
        assert by["COAL_PRB"]["verdict"] == "pass"
        # Each subclass carries its OWN denominator and materiality line.
        assert by["COAL_BIT"]["class_total_twh"] == pytest.approx(240 / 1e6, abs=1e-4)
        assert not by["COAL_BIT"]["immaterial"]
        assert [f.split(":")[0] for f in res.failures] == ["2024 COAL_BIT"]

    def test_materiality_is_per_subclass(self):
        """BIT at 1.2 % of load is immaterial even though coal as a family is not."""
        disp, floors, mech, klass = _two_subclass_fixture()
        res = ld.run_d2(disp, floors, mech, klass, year=2024, total_load_mwh=20000.0)
        by = {r["class"]: r for r in res.summary}
        assert by["COAL_BIT"]["immaterial"] and by["COAL_BIT"]["verdict"] == "pass"
        assert not by["COAL_PRB"]["immaterial"]
        assert (240 + 2400) / 20000.0 > cv.PROTECTIVE_MIN_LOAD_FRAC


def _legit(summary, rows=()):
    return {
        "gates": {"d1_min_profile_r": 0.8, "d1_min_cv_ratio": 0.5},
        "diagnostics": {
            "D1": {"rows": []},
            "D2": {"summary": list(summary), "rows": list(rows)},
            "D4": {"rows": []},
        },
    }


def _row(klass, share, total):
    return {
        "year": 2024,
        "class": klass,
        "forced_twh": round(share * total, 4),
        "class_total_twh": total,
        "forced_share": share,
        "lower_bound": False,
    }


class TestScorerPerSubclass:
    def test_over_cap_subclass_fails_while_the_other_passes(self):
        legit = _legit(
            [_row("COAL_BIT", 0.5, 10.0), _row("COAL_PRB", 0.083, 100.0)],
            rows=[
                {
                    "year": 2024,
                    "class": "COAL_BIT",
                    "mechanism": "reliability_floor",
                    "forced_twh": 5.0,
                    "class_total_twh": 10.0,
                    "share_of_class": 0.5,
                }
            ],
        )
        ypay = {"gmModel": {"COAL_BIT": 10.0, "COAL_PRB": 100.0, "CC_REGULAR": 110.0}}
        ybench = {
            "classFull": {"COAL_BIT": 10.0, "COAL_PRB": 100.0, "CC_REGULAR": 110.0}
        }
        recs = {r["key"]: r for r in cv.score_forced_share(2024, legit, ypay, ybench)}
        assert recs["COAL_PRB"]["status"] == cv.PASS
        # Above cap, no declared D-4 window for its mechanism and no D-1 row:
        # the escalation cannot ground it.
        assert recs["COAL_BIT"]["status"] == cv.FAIL
        assert "NOT grounded" in recs["COAL_BIT"]["magnitude"]

    def test_immaterial_subclass_skips_on_its_own_energy(self):
        legit = _legit([_row("COAL_WC", 0.9, 1.0), _row("COAL_PRB", 0.01, 100.0)])
        ypay = {"gmModel": {"COAL_WC": 1.0, "COAL_PRB": 100.0, "CC_REGULAR": 99.0}}
        ybench = {"classFull": {"COAL_WC": 1.0, "COAL_PRB": 100.0, "CC_REGULAR": 99.0}}
        recs = {r["key"]: r for r in cv.score_forced_share(2024, legit, ypay, ybench)}
        assert recs["COAL_WC"]["status"] == cv.SKIPPED
        assert "immaterial" in recs["COAL_WC"]["magnitude"]
        assert recs["COAL_PRB"]["status"] == cv.PASS

    def test_rubric_version(self):
        assert cv.RUBRIC_VERSION == 3.9


def _committed():
    """A pre-v3.9 artifact: one coal-family row per year beside a gas row."""
    gas = {
        "year": 2024,
        "class": "CC_REGULAR",
        "forced_twh": 1.0,
        "class_total_twh": 100.0,
        "forced_share": 0.01,
        "verdict": "pass",
    }
    return {
        "schema": "legitimacy-diagnostics/v1",
        "diagnostics": {
            "D1": {"rows": [{"year": 2024, "class": "COAL_BIT"}]},
            "D2": {
                "name": "D-2 forced-energy attribution",
                "passed": True,
                "rows": [
                    {
                        "year": 2023,
                        "class": "COAL",
                        "mechanism": "reliability_floor",
                        "forced_twh": 7.0,
                    },
                    {
                        "year": 2024,
                        "class": "COAL",
                        "mechanism": "reliability_floor",
                        "forced_twh": 3.2,
                    },
                    {
                        "year": 2024,
                        "class": "CC_REGULAR",
                        "mechanism": "x",
                        "forced_twh": 1.0,
                    },
                ],
                "summary": [
                    {
                        "year": 2023,
                        "class": "COAL",
                        "forced_twh": 7.0,
                        "class_total_twh": 70.0,
                    },
                    {
                        "year": 2024,
                        "class": "CC_REGULAR",
                        "forced_twh": 1.0,
                        "class_total_twh": 100.0,
                    },
                    {
                        "year": 2024,
                        "class": "COAL",
                        "forced_twh": 3.2,
                        "class_total_twh": 26.4,
                    },
                    gas | {"year": 2023},
                ],
                "failures": [],
                "notes": [],
            },
        },
    }


class TestResplitSplice:
    def test_splices_only_coal_rows_of_the_recomputed_years(self):
        recomputed = ld.GateResult("D-2 forced-energy attribution")
        recomputed.summary = [
            {
                "year": 2024,
                "class": "CC_REGULAR",
                "forced_twh": 9.9,
                "class_total_twh": 99.0,
            },
            {
                "year": 2024,
                "class": "COAL_BIT",
                "forced_twh": 1.2,
                "class_total_twh": 2.4,
                "verdict": "FAIL",
            },
            {
                "year": 2024,
                "class": "COAL_PRB",
                "forced_twh": 2.0,
                "class_total_twh": 24.0,
                "verdict": "pass",
            },
        ]
        recomputed.rows = [
            {
                "year": 2024,
                "class": "COAL_BIT",
                "mechanism": "reliability_floor",
                "forced_twh": 1.2,
            },
            {
                "year": 2024,
                "class": "COAL_PRB",
                "mechanism": "reliability_floor",
                "forced_twh": 2.0,
            },
        ]
        recomputed.failures = [
            "2024 COAL_BIT: forced share 50.0% > 30% (...)",
            "2024 CC_REGULAR: not coal, must not be spliced",
        ]
        before = _committed()
        out = ld.resplit_coal_d2(before, recomputed, {"basis": "test"}, [2024])
        d2 = out["diagnostics"]["D2"]
        classes = [(r["year"], r["class"]) for r in d2["summary"]]
        # 2023 is outside the recompute's scope: its family row is untouched.
        assert (2023, "COAL") in classes
        assert (2024, "COAL") not in classes
        assert (2024, "COAL_BIT") in classes and (2024, "COAL_PRB") in classes
        # Non-coal rows are the ORIGINAL ones, never the recomputed ones.
        cc = next(
            r for r in d2["summary"] if r["class"] == "CC_REGULAR" and r["year"] == 2024
        )
        assert cc["forced_twh"] == 1.0
        assert d2["failures"] == ["2024 COAL_BIT: forced share 50.0% > 30% (...)"]
        assert d2["passed"] is False
        assert classes == sorted(classes, key=lambda k: (k[0], k[1]))
        xc = out["coal_subclass_resplit"]["family_crosscheck"]["2024"]
        assert xc["committed_family_forced_twh"] == 3.2
        assert xc["resplit_subclass_forced_twh"] == 3.2
        assert xc["resplit_subclass_total_twh"] == 26.4
        # D-1 and the input artifact are untouched.
        assert out["diagnostics"]["D1"] == before["diagnostics"]["D1"]
        assert before["diagnostics"]["D2"]["summary"][2]["class"] == "COAL"


class TestLegacyFloorsResplit:
    def test_legacy_coal_rows_relabelled_by_unit_id(self, monkeypatch, tmp_path):
        """A pre-COAL-SUB npz's COAL rows take the rebuilt fleet's subclass,
        joined by unit_id (the rebuilt fleet is deliberately out of order)."""
        rebuilt = type("FA", (), {})()
        rebuilt.unit_ids = ["u_gas", "u_prb", "u_bit"]
        rebuilt.plant_group = np.array(
            ["CC_REGULAR", "COAL_PRB", "COAL_BIT"], dtype=object
        )
        monkeypatch.setattr(ld, "_rebuild_fleet_arrays", lambda *a: rebuilt)
        arrays = {
            "unit_ids": np.array(["u_bit", "u_prb", "u_gas", "u_gone"]),
            "plant_group": np.array(["COAL", "COAL", "CC_REGULAR", "COAL"]),
        }
        out = ld._resplit_legacy_coal(arrays, tmp_path, "PJM", 2020)
        # The unit the rebuild does not carry keeps the family label: nothing
        # is invented.
        assert out["plant_group"].tolist() == [
            "COAL_BIT",
            "COAL_PRB",
            "CC_REGULAR",
            "COAL",
        ]


class TestResplitBlindYears:
    """A year the recompute cannot see is relabelled exactly or kept, never emptied."""

    def _recomputed_without_coal(self):
        res = ld.GateResult("D-2 forced-energy attribution")
        res.summary = [
            {
                "year": 2024,
                "class": "CC_REGULAR",
                "forced_twh": 9.9,
                "class_total_twh": 99.0,
            }
        ]
        return res

    def test_single_subclass_fleet_relabels_the_committed_row(self):
        out = ld.resplit_coal_d2(
            _committed(),
            self._recomputed_without_coal(),
            {},
            [2024],
            single_subclass={2024: "COAL_BIT"},
        )
        rows = [r for r in out["diagnostics"]["D2"]["summary"] if r["year"] == 2024]
        coal = [r for r in rows if r["class"].startswith("COAL")]
        assert coal == [
            {
                "year": 2024,
                "class": "COAL_BIT",
                "forced_twh": 3.2,
                "class_total_twh": 26.4,
            }
        ]
        meta = out["coal_subclass_resplit"]
        assert meta["relabelled_years"] == {"2024": "COAL_BIT"}
        assert meta["family_crosscheck"]["2024"]["resplit_subclass_total_twh"] == 26.4

    def test_multi_subclass_fleet_keeps_the_family_row(self):
        out = ld.resplit_coal_d2(
            _committed(), self._recomputed_without_coal(), {}, [2024]
        )
        coal = [
            r
            for r in out["diagnostics"]["D2"]["summary"]
            if r["year"] == 2024 and r["class"].startswith("COAL")
        ]
        assert [r["class"] for r in coal] == ["COAL"]
        assert out["coal_subclass_resplit"]["unresolved_years"] == ["2024"]


def test_legacy_family_row_counts_generic_bucket_and_members():
    """A legacy COAL row whose payload also carries a generic-bucket COAL value
    is material through its members (the v2.8 bridge used to stay shut)."""
    legit = _legit([_row("COAL", 0.0, 89.6)])
    ypay = {
        "gmModel": {
            "COAL": 0.0389,
            "COAL_PRB": 77.9,
            "COAL_LIGNITE": 11.0,
            "CC_REGULAR": 160.0,
        }
    }
    ybench = {
        "classFull": {"COAL_PRB": 78.0, "COAL_LIGNITE": 11.0, "CC_REGULAR": 160.0}
    }
    (rec,) = cv.score_forced_share(2024, legit, ypay, ybench)
    assert rec["status"] == cv.PASS
