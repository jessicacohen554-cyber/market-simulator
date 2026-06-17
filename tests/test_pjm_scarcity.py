"""Tests for the PJM stepped-ORDC reserve-scarcity primitives.

Covers the published two-step demand curve (market_sim.results.scarcity:
pjm_reserve_demand_price), the nested product/locational cascade
(pjm_reserve_cascade_mcp), the cited curve loader (load_pjm_ordc_curve) and
the plant-level online-reserve primitive (pjm_online_reserve). The curve
parameters ($850 Step 1 at the requirement, $300 Step 2 at +190 MW) are PJM
Manual 11 sec 4.3.3 — see docs/multi-iso/pjm-reserve-curve-source.md. Nothing
here is fitted to a price residual.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from market_sim.results.scarcity import (
    PJM_RESERVE_CASCADE,
    load_pjm_ordc_curve,
    pjm_online_reserve,
    pjm_reserve_cascade_mcp,
    pjm_reserve_demand_price,
)

REPO = Path(__file__).resolve().parent.parent
CURVE_CSV = REPO / "data" / "raw" / "_validation-source" / "pjm_ordc_curve.csv"

# The published two-step curve (offset_mw from requirement, penalty $/MWh).
STEPS = [(0.0, 850.0), (190.0, 300.0)]


class TestDemandPrice:
    def test_three_regimes(self):
        """Below requirement -> $850; within +190 -> $300; beyond -> $0."""
        req = 1000.0
        r = np.array([900.0, 1000.0, 1100.0, 1189.0, 1190.0, 1500.0])
        price = pjm_reserve_demand_price(r, req, STEPS)
        # r<req: 850; req<=r<req+190: 300; r>=req+190: 0
        np.testing.assert_array_equal(
            price, [850.0, 300.0, 300.0, 300.0, 0.0, 0.0])

    def test_boundary_at_requirement_is_step2(self):
        """Exactly at the requirement is the Step 2 ($300) regime, not Step 1."""
        assert pjm_reserve_demand_price(1000.0, 1000.0, STEPS) == 300.0
        assert pjm_reserve_demand_price(999.99, 1000.0, STEPS) == 850.0

    def test_tightest_step_wins(self):
        """A deep shortage takes the top penalty, never a wider/cheaper step."""
        # Far below requirement: must be $850, not overwritten by the +190 step.
        assert pjm_reserve_demand_price(0.0, 1000.0, STEPS) == 850.0

    def test_hourly_arrays_broadcast(self):
        """Hourly reserves against an hourly requirement broadcast elementwise."""
        r = np.array([500.0, 1500.0, 2500.0])
        req = np.array([1000.0, 1000.0, 1000.0])
        np.testing.assert_array_equal(
            pjm_reserve_demand_price(r, req, STEPS), [850.0, 0.0, 0.0])

    def test_zero_adder_when_comfortable(self):
        """The vertical step is exactly $0 with ample reserves (honesty gate)."""
        r = np.full(8760, 16_000.0)  # ~model plant-online reserve
        req = np.full(8760, 3_000.0)
        assert pjm_reserve_demand_price(r, req, STEPS).max() == 0.0


class TestCascade:
    def _curve(self):
        return {p: STEPS for p in ("Synchronized", "Primary", "Secondary")}

    def test_all_short_gives_nested_sums(self):
        """All three nested requirements short -> SR=2550, PR=1700, 30=850.

        Matches the measured 2025 maxima (3x/2x/1x $850) — the cascade in
        Manual 11 sec 4.4.1.
        """
        short = {p: np.array([0.0]) for p in
                 ("Synchronized", "Primary", "Secondary")}
        req = {p: np.array([1000.0]) for p in
               ("Synchronized", "Primary", "Secondary")}
        mcp = pjm_reserve_cascade_mcp(short, req, self._curve())
        assert mcp["SR"][0] == pytest.approx(2550.0)   # 3 x 850
        assert mcp["PR"][0] == pytest.approx(1700.0)   # 2 x 850
        assert mcp["30MIN"][0] == pytest.approx(850.0)  # 1 x 850
        assert mcp["energy_adder"][0] == pytest.approx(2550.0)

    def test_only_synchronized_short(self):
        """Only the SR requirement short -> SR=850, PR=0, 30=0."""
        reserves = {"Synchronized": np.array([500.0]),
                    "Primary": np.array([5000.0]),
                    "Secondary": np.array([5000.0])}
        req = {p: np.array([1000.0]) for p in
               ("Synchronized", "Primary", "Secondary")}
        mcp = pjm_reserve_cascade_mcp(reserves, req, self._curve())
        assert mcp["SR"][0] == pytest.approx(850.0)
        assert mcp["PR"][0] == 0.0
        assert mcp["30MIN"][0] == 0.0

    def test_no_shortage_all_zero(self):
        """Comfortable reserves on every product clear at $0."""
        reserves = {p: np.array([9000.0]) for p in
                    ("Synchronized", "Primary", "Secondary")}
        req = {p: np.array([1000.0]) for p in
               ("Synchronized", "Primary", "Secondary")}
        mcp = pjm_reserve_cascade_mcp(reserves, req, self._curve())
        assert all(mcp[s][0] == 0.0 for s in ("SR", "PR", "30MIN"))

    def test_monotone_cascade_ordering(self):
        """SRMCP >= NSRMCP >= SecRMCP always (Manual 11 sec 4.4.5)."""
        rng = np.random.default_rng(0)
        reserves = {p: rng.uniform(0, 2000, 200) for p in
                    ("Synchronized", "Primary", "Secondary")}
        req = {p: np.full(200, 1000.0) for p in
               ("Synchronized", "Primary", "Secondary")}
        mcp = pjm_reserve_cascade_mcp(reserves, req, self._curve())
        assert np.all(mcp["SR"] >= mcp["PR"] - 1e-9)
        assert np.all(mcp["PR"] >= mcp["30MIN"] - 1e-9)


class TestCurveCsv:
    def test_loads_cited_curve(self):
        """The committed CSV loads to the published $850/$300 +190 MW steps."""
        curve = load_pjm_ordc_curve(CURVE_CSV)
        # RTO Synchronized must be the two published steps.
        steps = curve[("Synchronized", "RTO")]
        assert steps == [(0.0, 850.0), (190.0, 300.0)]

    def test_all_products_zones_present(self):
        """Every product x reserve-zone combination is defined."""
        curve = load_pjm_ordc_curve(CURVE_CSV)
        for svc in ("Synchronized", "Primary", "Secondary"):
            for loc in ("RTO", "MAD"):
                assert (svc, loc) in curve
                # Penalty factors are shared across products/zones (sec 4.3.3).
                assert curve[(svc, loc)] == [(0.0, 850.0), (190.0, 300.0)]

    def test_csv_reproduces_measured_step_regime(self):
        """Loaded curve reproduces the $850 / $300 measured shortage values."""
        steps = load_pjm_ordc_curve(CURVE_CSV)[("Synchronized", "RTO")]
        # total < requirement -> 850; requirement..+190 -> 300.
        assert pjm_reserve_demand_price(1754.6, 1947.0, steps) == 850.0
        assert pjm_reserve_demand_price(2050.0, 2000.0, steps) == 300.0


class TestOnlineReserve:
    def test_plant_level_aggregation(self):
        """A plant's tranches aggregate: online headroom is plant-wide, not 0.

        Two tranches of one plant (avail 100+50), one dispatching at its cap
        (100) and one idle (0). The plant is online (tranche 1 runs), so its
        reserve is the *other* tranche's full headroom (50), even though the
        running tranche itself has 0 headroom (bang-bang).
        """
        avail = np.array([[100.0], [50.0]])      # (2 tranches, 1 hour)
        disp = np.array([[100.0], [0.0]])        # tranche 1 maxed, tranche 2 off
        plant_id = np.array([7, 7])              # same plant
        thermal = np.array([True, True])
        r = pjm_online_reserve(avail, disp, plant_id, thermal)
        assert r[0] == pytest.approx(50.0)

    def test_offline_plant_contributes_nothing(self):
        """A fully idle plant is not synchronized -> contributes no reserve."""
        avail = np.array([[100.0], [80.0]])
        disp = np.array([[0.0], [0.0]])          # both tranches off
        plant_id = np.array([1, 2])              # two distinct idle plants
        thermal = np.array([True, True])
        r = pjm_online_reserve(avail, disp, plant_id, thermal)
        assert r[0] == 0.0

    def test_non_thermal_excluded(self):
        """Non-thermal units (wind/solar) never count toward reserve."""
        avail = np.array([[100.0], [100.0]])
        disp = np.array([[40.0], [40.0]])
        plant_id = np.array([1, 2])
        thermal = np.array([True, False])        # second unit is renewable
        r = pjm_online_reserve(avail, disp, plant_id, thermal)
        assert r[0] == pytest.approx(60.0)       # only the thermal plant

    def test_as_plan_netting(self):
        """The AS plan is subtracted from the online reserve."""
        avail = np.array([[1000.0]])
        disp = np.array([[400.0]])
        plant_id = np.array([1])
        thermal = np.array([True])
        r = pjm_online_reserve(avail, disp, plant_id, thermal, as_plan_mw=200.0)
        assert r[0] == pytest.approx(400.0)      # 600 headroom - 200 AS plan

    def test_cascade_keys_consistent(self):
        """The cascade table covers exactly the three published data services."""
        assert set(PJM_RESERVE_CASCADE) == {"SR", "PR", "30MIN"}
        assert PJM_RESERVE_CASCADE["SR"] == (
            "Synchronized", "Primary", "Secondary")
