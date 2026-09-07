"""F-A: the priced-interchange seam's MEASURED backcast gas level (pjm-172).

Card: ``docs/handoffs/PRECOMMIT-pjm172-seam-measured-gas-2026-09-07.md``.
Defect: ``docs/handoffs/../../results/calibration/ADDENDUM-pjm171-seam-fuel-basis-freeze-2026-09-07.md``.

``neighbor_gas_price``'s contract is that *"a neighbor and its bordering ISO see
the same Henry Hub level"*. Below the trajectory's FIRST knot that broke:
``low``/``mid``/``high`` begin at 2023, so ``_hold_flat_extrapolate`` handed
2021 and 2022 the 2023 knot ($2.54) while the ISO burned the measured year
price — -32 % in 2021, -61 % in 2022.

These are the PRECOMMIT's own gates, asserted rather than argued:

* **§3.4 inertness** — the branch cannot execute for 2023/2024/2025 or for any
  forecast year, on any scenario key (gate **S2**).
* **§2.1 look-ahead refusal** — the measured path is refused for every
  ``hindcast_asknown_*`` key (that lane must see only what was knowable then).
* **§4/§5 S3 magnitude** — the per-neighbour and mean seam baseload levels the
  card pre-registered, to |err| <= 1e-6.
"""

from __future__ import annotations

import pytest

from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.fuel.trajectories import _hold_flat_extrapolate
from market_sim.data.neighbor_price import (
    _HINDCAST_ASKNOWN_PREFIX,
    _measured_henry_hub_annual,
    neighbor_gas_price,
    neighbor_heat_rate,
)

# The measured EIA Henry Hub spot annual means, at full precision. PRECOMMIT §2
# declares them rounded (2019 2.565 / 2020 2.034 / 2021 3.910 / 2022 6.419);
# these are the values the resolver actually returns, and the rounded card
# values are asserted separately below.
_MEASURED_ANNUAL: dict[int, float] = {
    2019: 2.5650749999999998,
    2020: 2.033716666666667,
    2021: 3.9096833333333336,
    2022: 6.419058333333333,
}

#: The same four values as PRECOMMIT §2 prints them (3 dp).
_CARD_DECLARED_ANNUAL: dict[int, float] = {
    2019: 2.565,
    2020: 2.034,
    2021: 3.910,
    2022: 6.419,
}

_PRICE_KEYS: tuple[str, ...] = ("low", "mid", "high")
_PJM_NEIGHBOURS = INTERFACE_NEIGHBORS["PJM"]


class TestMeasuredAnnualSeries:
    """The measured resolver itself — the only new input this card reads."""

    @pytest.mark.parametrize("year,expected", sorted(_MEASURED_ANNUAL.items()))
    def test_annual_mean_is_exact(self, year, expected):
        assert _measured_henry_hub_annual(year) == expected

    @pytest.mark.parametrize("year,declared", sorted(_CARD_DECLARED_ANNUAL.items()))
    def test_annual_mean_matches_the_card_to_its_stated_precision(self, year, declared):
        assert _measured_henry_hub_annual(year) == pytest.approx(declared, abs=5e-4)

    def test_incomplete_year_is_refused(self):
        """A year the series does not carry 12 months of yields None.

        The extract's forward edge is partial (H1-2026 carries 6 months), and a
        half-year mean dressed as an annual one would be a silent defect. Such a
        year keeps the hold-flat rule.
        """
        assert _measured_henry_hub_annual(1800) is None

    def test_series_is_not_the_trajectory(self):
        """The card's premise: the measured level differs from the held knot."""
        first_knot = min(HENRY_HUB_TRAJECTORIES["mid"])
        held = HENRY_HUB_TRAJECTORIES["mid"][first_knot]
        assert _measured_henry_hub_annual(2021) != pytest.approx(held, abs=1e-3)
        assert _measured_henry_hub_annual(2022) != pytest.approx(held, abs=1e-3)


class TestPreFirstKnotRepair:
    """Below the first knot the seam now sees the measured level (§1, §2)."""

    @pytest.mark.parametrize("gas_scenario", _PRICE_KEYS)
    @pytest.mark.parametrize("year", (2021, 2022))
    def test_seam_gas_is_measured_plus_basis(self, gas_scenario, year):
        for neighbour in _PJM_NEIGHBOURS:
            got = neighbor_gas_price(neighbour, year, gas_scenario)
            assert got == pytest.approx(
                _MEASURED_ANNUAL[year] + neighbour.gas_basis, abs=1e-6
            )

    def test_the_defect_is_actually_repaired(self):
        """The -32 % / -61 % errors the predecessor measured are gone."""
        first_knot = min(HENRY_HUB_TRAJECTORIES["mid"])
        held = HENRY_HUB_TRAJECTORIES["mid"][first_knot]
        for year, measured in ((2021, 3.9097), (2022, 6.4191)):
            for neighbour in _PJM_NEIGHBOURS:
                got = neighbor_gas_price(neighbour, year, "mid")
                assert got != pytest.approx(held + neighbour.gas_basis, abs=1e-3)
                assert got == pytest.approx(measured + neighbour.gas_basis, abs=1e-4)

    def test_the_neighbours_basis_is_applied_unchanged(self):
        """Only the Henry Hub LEVEL moves; the basis structure is untouched."""
        for neighbour in _PJM_NEIGHBOURS:
            spread = neighbor_gas_price(neighbour, 2022, "mid") - neighbor_gas_price(
                neighbour, 2021, "mid"
            )
            assert spread == pytest.approx(
                _MEASURED_ANNUAL[2022] - _MEASURED_ANNUAL[2021], abs=1e-6
            )


class TestLookAheadRefusal:
    """§2.1 — the as-known-then hindcast lane never sees a realized price."""

    def test_asknown_keys_keep_hold_flat(self):
        asknown = [
            k for k in HENRY_HUB_TRAJECTORIES if k.startswith(_HINDCAST_ASKNOWN_PREFIX)
        ]
        assert asknown, "no hindcast_asknown_* path registered — guard is untested"
        for key in asknown:
            trajectory = HENRY_HUB_TRAJECTORIES[key]
            for year in (2019, 2020, 2021, 2022):
                if year >= min(trajectory):
                    continue  # a knot or beyond it: the branch is unreachable
                for neighbour in _PJM_NEIGHBOURS:
                    assert neighbor_gas_price(neighbour, year, key) == pytest.approx(
                        _hold_flat_extrapolate(trajectory, year) + neighbour.gas_basis,
                        abs=1e-12,
                    )

    def test_at_least_one_asknown_year_actually_exercises_the_guard(self):
        """The refusal must be reachable, or the test above is vacuous."""
        reachable = [
            (key, year)
            for key, trajectory in HENRY_HUB_TRAJECTORIES.items()
            if key.startswith(_HINDCAST_ASKNOWN_PREFIX)
            for year in (2019, 2020, 2021, 2022)
            if year < min(trajectory) and _measured_henry_hub_annual(year) is not None
        ]
        assert reachable, "the look-ahead guard is never exercised"

    def test_hindcast_realized_is_untouched_by_construction(self):
        """It carries its own 2021 knot, so the branch cannot fire for 2021."""
        trajectory = HENRY_HUB_TRAJECTORIES["hindcast_realized"]
        assert 2021 in trajectory
        for neighbour in _PJM_NEIGHBOURS:
            assert neighbor_gas_price(
                neighbour, 2021, "hindcast_realized"
            ) == pytest.approx(trajectory[2021] + neighbour.gas_basis, abs=1e-12)


class TestInertAboveTheFirstKnot:
    """§3.4 / gate S2 — bit-identity for every year >= 2023 and every forecast year."""

    @pytest.mark.parametrize("gas_scenario", _PRICE_KEYS)
    def test_every_year_at_or_above_the_first_knot_is_bit_identical(self, gas_scenario):
        trajectory = HENRY_HUB_TRAJECTORIES[gas_scenario]
        first_knot = min(trajectory)
        assert first_knot == 2023, "the card's premise moved; re-derive the gates"
        for iso_neighbours in INTERFACE_NEIGHBORS.values():
            for neighbour in iso_neighbours:
                for year in range(first_knot, 2051):
                    assert (
                        neighbor_gas_price(neighbour, year, gas_scenario)
                        == _hold_flat_extrapolate(trajectory, year)
                        + neighbour.gas_basis
                    )

    @pytest.mark.parametrize("gas_scenario", _PRICE_KEYS)
    @pytest.mark.parametrize("year", (2023, 2024, 2025))
    def test_training_years_are_bit_identical_for_every_registered_iso(
        self, gas_scenario, year
    ):
        """No ISO's keeper can move: the branch is unreachable in-window."""
        trajectory = HENRY_HUB_TRAJECTORIES[gas_scenario]
        for iso, iso_neighbours in INTERFACE_NEIGHBORS.items():
            for neighbour in iso_neighbours:
                assert neighbor_gas_price(neighbour, year, gas_scenario) == (
                    _hold_flat_extrapolate(trajectory, year) + neighbour.gas_basis
                ), f"{iso}/{neighbour.name} moved in a training year"


class TestSeamBaselineMagnitudes:
    """The MEASURED 2022/2021 seam baseload levels — and why gates S1/S3 failed.

    ``baseload = neighbor_gas_price x neighbor_heat_rate`` (before the load
    shape), the quantity PRECOMMIT §4 tabulates.

    **These constants are the MEASURED values, not the card's §4 predictions**,
    and the divergence is the session's result rather than a tolerance to be
    widened. §4 predicted the 2022 arm at a 74.156 $/MWh mean; the measured arm
    is **61.145**. The control column reproduces §4 EXACTLY on all five seams
    (32.766 / 32.136 / 28.424 x3, mean 30.035), so the apparatus agrees with the
    card wherever the card is self-consistent.

    The gap is entirely the three Southeast seams. Carolinas / TVA / LGEE carry
    ``hr_by_year = None`` in EVERY year — SERC publishes no nodal LMP to anchor
    a per-year heat rate to — so they always take
    :func:`neighbor_heat_rate`'s gas-elastic branch, ``hr = hr_phys +
    hr_adder / gas`` with ``_HR_GAS_ELASTIC = (5.6, 14.2)``. Their implied heat
    rate is therefore a FUNCTION of the very gas level this card moves, and it
    falls as gas rises — deliberately, so the coal/nuclear Southeast does not
    ride Henry Hub up in a dear-gas year. §4 held those heat rates fixed at
    their control-gas value (71.833 = 6.419058 x 11.1906, the $2.54 heat rate),
    which is the whole of the -21.686 $/MWh per-seam miss.

    Consequence for the gates, recorded here and graded in the FINDING:

    * **S1 FAILS** — it requires ``neighbor_heat_rate`` to be *unchanged*, which
      no gas-level repair can satisfy on this ISO.
    * **S3 FAILS** — 61.145 against a predicted 74.156, tolerance 1e-6.
    """

    # MEASURED (this HEAD), 2022 arm vs the true pre-repair control.
    _ARM_2022: dict[str, float] = {
        "MISO": 82.8059,
        "NYISO": 72.4782,
        "Carolinas": 50.1467,
        "TVA": 50.1467,
        "LGEE": 50.1467,
    }
    _CONTROL_2022: dict[str, float] = {
        "MISO": 32.7660,
        "NYISO": 32.1360,
        "Carolinas": 28.4240,
        "TVA": 28.4240,
        "LGEE": 28.4240,
    }
    _ARM_MEAN_2022: float = 61.1448
    _CONTROL_MEAN_2022: float = 30.0348
    _ARM_MEAN_2021: float = 41.0197

    #: What PRECOMMIT §4 predicted for the 2022 arm. Kept so the divergence is
    #: asserted rather than merely narrated.
    _CARD_PREDICTED_ARM_2022: dict[str, float] = {
        "MISO": 82.806,
        "NYISO": 72.478,
        "Carolinas": 71.833,
        "TVA": 71.833,
        "LGEE": 71.833,
    }
    _CARD_PREDICTED_ARM_MEAN_2022: float = 74.156
    _CARD_CONTROL_MEAN_2022: float = 30.035

    @staticmethod
    def _baseload(neighbour, year: int) -> float:
        return neighbor_gas_price(neighbour, year, "mid") * neighbor_heat_rate(
            neighbour, year
        )

    def test_measured_arm_per_neighbour(self):
        for neighbour in _PJM_NEIGHBOURS:
            assert self._baseload(neighbour, 2022) == pytest.approx(
                self._ARM_2022[neighbour.name], abs=1e-3
            ), neighbour.name

    def test_measured_arm_mean(self):
        arm = [self._baseload(n, 2022) for n in _PJM_NEIGHBOURS]
        assert sum(arm) / len(arm) == pytest.approx(self._ARM_MEAN_2022, abs=1e-3)

    def test_southeast_heat_rate_is_gas_elastic_in_every_year(self):
        """The structural fact that makes gate S1 unsatisfiable.

        These three seams have no ``hr_by_year`` at all, so the elastic branch
        is not a 2021/2022 gap that card F-B could close — it is their
        permanent price-formation anchor.
        """
        for name in ("Carolinas", "TVA", "LGEE"):
            neighbour = next(n for n in _PJM_NEIGHBOURS if n.name == name)
            assert neighbour.hr_by_year is None
            for year in (2021, 2022, 2023, 2024, 2025):
                gas = neighbor_gas_price(neighbour, year, "mid")
                assert neighbor_heat_rate(neighbour, year) == pytest.approx(
                    5.6 + 14.2 / gas, abs=1e-9
                )

    def test_the_two_anchored_seams_reproduce_the_card_exactly(self):
        """MISO and NYISO have flat heat rates in 2022, so §4 is right for them."""
        for name in ("MISO", "NYISO"):
            neighbour = next(n for n in _PJM_NEIGHBOURS if n.name == name)
            assert self._baseload(neighbour, 2022) == pytest.approx(
                self._CARD_PREDICTED_ARM_2022[name], abs=1e-3
            )

    def test_gate_s3_fails_against_the_precommit_prediction(self):
        """The kill, asserted: the measured arm is not §4's 74.156."""
        arm = [self._baseload(n, 2022) for n in _PJM_NEIGHBOURS]
        measured_mean = sum(arm) / len(arm)
        assert abs(measured_mean - self._CARD_PREDICTED_ARM_MEAN_2022) > 1e-6
        assert measured_mean - self._CARD_PREDICTED_ARM_MEAN_2022 == pytest.approx(
            -13.011, abs=2e-3
        )

    def test_the_control_column_reproduces_the_card_exactly(self):
        """The apparatus is sound: only the ARM prediction diverges.

        Reconstructed with each seam's control-gas heat rate — for the elastic
        three that is ``5.6 + 14.2 / 2.54``, which is precisely the value §4
        then (incorrectly) carried into the arm column.
        """
        held = _hold_flat_extrapolate(HENRY_HUB_TRAJECTORIES["mid"], 2022)
        control = []
        for neighbour in _PJM_NEIGHBOURS:
            gas = held + neighbour.gas_basis
            hr = (
                5.6 + 14.2 / gas
                if neighbour.hr_by_year is None
                else neighbour.marginal_heat_rate
            )
            value = gas * hr
            control.append(value)
            assert value == pytest.approx(
                self._CONTROL_2022[neighbour.name], abs=1e-3
            ), neighbour.name
        assert sum(control) / len(control) == pytest.approx(
            self._CARD_CONTROL_MEAN_2022, abs=1e-3
        )

    def test_the_screen_year_choice_survives_the_correction(self):
        """2022 is still the larger footprint, and still by ~2.83x.

        Recorded because it is the one §4 conclusion the correction leaves
        standing: the screen-year choice was not contaminated.
        """
        deltas = {}
        for year, arm_mean in (
            (2021, self._ARM_MEAN_2021),
            (2022, self._ARM_MEAN_2022),
        ):
            measured = [self._baseload(n, year) for n in _PJM_NEIGHBOURS]
            assert sum(measured) / len(measured) == pytest.approx(arm_mean, abs=1e-3)
            deltas[year] = arm_mean - self._CONTROL_MEAN_2022
        assert deltas[2022] > deltas[2021] > 0.0
        assert deltas[2022] / deltas[2021] == pytest.approx(2.83, abs=0.01)
