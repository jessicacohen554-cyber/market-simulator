"""The below-base ``carbon_price`` validation warning (capx-D34, owner ruling Q26).

Q26's ruling: ``ScenarioConfig.carbon_price`` KEEPS its documented replace
semantics — precedence (1) of ``policy.carbon.resolve_carbon_price`` — and
gains a loud validation warning when a forecast override sits BELOW the
resolved base carbon trajectory in any horizon year. That is the exact trap
the D21 ``carbon25`` arm fell into (D23: a "carbon price increase" that CUT
carbon in every year on an ISO whose base carries the projected RGGI
escalator). No semantics change, no field, no default move — so these tests
also pin the guard as a pure OBSERVER: the resolver's values must be
bit-identical with the guard silenced.

See ``docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md`` §2 and
``FINDING-capx-d34-carbonprice-guard-2026-09-01.md``.
"""

from __future__ import annotations

import warnings

import pytest

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy import carbon as carbon_policy
from market_sim.policy.carbon import (
    CARBON_PRICE_BELOW_BASE_REMEDY,
    carbon_price_below_base_warning,
    resolve_carbon_price,
    resolved_base_trajectory_price,
)

HORIZON = range(START_YEAR, END_YEAR + 1)


def _build(**kwargs) -> tuple[ScenarioConfig, list[warnings.WarningMessage]]:
    """Construct a config, capturing every warning ``__post_init__`` emits."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        config = ScenarioConfig(**kwargs)
    return config, list(caught)


def _below_base_warnings(
    caught: list[warnings.WarningMessage],
) -> list[warnings.WarningMessage]:
    return [w for w in caught if "base carbon trajectory" in str(w.message)]


# --- (i) fires on the exact D21/D23 configuration ---------------------------


class TestFiresOnTheD23Configuration:
    """NEISO + ``carbon_price=25`` against the projected RGGI base."""

    D23_KWARGS = dict(iso="NEISO", carbon_price=25.0, hours=24)

    def test_warning_is_emitted_at_scenario_validation(self):
        _, caught = _build(**self.D23_KWARGS)
        hits = _below_base_warnings(caught)
        assert len(hits) == 1, [str(w.message) for w in caught]
        assert issubclass(hits[0].category, RuntimeWarning)

    def test_message_names_iso_years_and_both_values_at_the_widest_gap(self):
        msg = carbon_price_below_base_warning(ScenarioConfig(**self.D23_KWARGS))
        assert msg is not None
        # The ISO.
        assert "NEISO" in msg
        # The years: every one of the 25 horizon years, rendered as a run.
        assert f"{len(HORIZON)} of {len(HORIZON)} horizon year(s)" in msg
        assert f"{START_YEAR}-{END_YEAR}" in msg
        # Both values at the widest gap. D23 §2: the base runs $26.05/t in
        # 2026 to $132.16/t in 2050, so the widest gap is 2050 at -$107.16.
        assert "Widest gap in 2050" in msg
        assert "$132.16/tCO2" in msg
        assert "$25.00/tCO2" in msg
        assert "$107.16/tCO2 CUT" in msg

    def test_message_carries_the_remedy_sentence_verbatim(self):
        msg = carbon_price_below_base_warning(ScenarioConfig(**self.D23_KWARGS))
        assert msg is not None
        assert (
            "a replace below the base trajectory REDUCES the carbon signal "
            "— for an increment use carbon_price_delta"
        ) in msg
        assert CARBON_PRICE_BELOW_BASE_REMEDY in msg

    def test_it_is_a_warning_not_an_error(self):
        """Q26 verbatim: guard, not semantics change — a deliberate
        below-base study stays legal, it just cannot be silent."""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            config = ScenarioConfig(**self.D23_KWARGS)
        assert config.carbon_price == 25.0

    def test_it_fires_on_a_partial_horizon_hit_and_names_only_those_years(self):
        """ "in ANY horizon year" — a crossing override still warns, and the
        year rendering collapses the contiguous run it actually hit."""
        config, caught = _build(iso="NEISO", carbon_price=50.0, hours=24)
        # $50/t is above the RGGI base through 2035 and below it from 2036 on.
        assert resolved_base_trajectory_price(config, 2035) < 50.0
        assert resolved_base_trajectory_price(config, 2036) > 50.0
        hits = _below_base_warnings(caught)
        assert len(hits) == 1
        msg = str(hits[0].message)
        assert "15 of 25 horizon year(s): 2036-2050" in msg
        assert CARBON_PRICE_BELOW_BASE_REMEDY in msg

    def test_the_remedy_actually_silences_it(self):
        """carbon_price_delta is an increment, so the guard never fires."""
        _, caught = _build(
            iso="NEISO", carbon_price=0.0, carbon_price_delta=25.0, hours=24
        )
        assert _below_base_warnings(caught) == []


# --- (ii)-(iv) the silent cases --------------------------------------------


class TestSilentCases:
    def test_silent_when_carbon_price_exceeds_the_base_everywhere(self):
        """$200/t clears NEISO's $132.16/t 2050 peak in every year."""
        config, caught = _build(iso="NEISO", carbon_price=200.0, hours=24)
        assert max(resolved_base_trajectory_price(config, y) for y in HORIZON) < 200.0
        assert _below_base_warnings(caught) == []
        assert carbon_price_below_base_warning(config) is None

    def test_silent_when_carbon_price_is_unset(self):
        """No override means no replacement, so there is nothing to warn about
        even though the RGGI base is armed and nonzero."""
        config, caught = _build(iso="NEISO", hours=24)
        assert config.carbon_price == 0.0
        assert resolved_base_trajectory_price(config, 2050) > 0.0
        assert _below_base_warnings(caught) == []
        assert carbon_price_below_base_warning(config) is None

    def test_silent_in_backcast_mode(self):
        """Backcast is untouched — even where the measured base genuinely
        exceeds the override, so ONLY the mode gate is suppressing it."""
        config, caught = _build(
            iso="NEISO",
            mode="backcast",
            weather_year=2024,
            hours=24,
            carbon_price=10.0,
        )
        assert config.mode == "backcast"
        # Premise: the measured RGGI auction average ($22.83/t in 2024) is
        # above the $10/t override, so a mode-blind guard WOULD fire here.
        assert resolved_base_trajectory_price(config, 2024) > 10.0
        assert _below_base_warnings(caught) == []
        assert carbon_price_below_base_warning(config) is None

    def test_silent_on_a_no_program_iso_at_the_zero_path(self):
        """ERCOT's base is 0.0/t, so no override can sit below it."""
        config, caught = _build(iso="ERCOT", carbon_price=25.0, hours=24)
        assert resolved_base_trajectory_price(config, 2050) == 0.0
        assert _below_base_warnings(caught) == []


# --- (v) the guard observes, never alters ----------------------------------


class TestResolverOutputIsByteUnchanged:
    """Every resolved value is bit-identical with the guard silenced.

    Silencing is done by monkeypatching the guard to a constant ``None`` —
    the exact pre-D34 behavior of ``__post_init__`` — and rebuilding each
    config from scratch, so the comparison covers both the construction path
    and the resolver's own extraction refactor
    (``_base_carbon_price`` -> ``resolved_base_trajectory_price``).
    """

    CASES = {
        "d23_below_base": dict(iso="NEISO", carbon_price=25.0, hours=24),
        "above_base": dict(iso="NEISO", carbon_price=200.0, hours=24),
        "unset": dict(iso="NEISO", hours=24),
        "backcast": dict(
            iso="NEISO",
            mode="backcast",
            weather_year=2024,
            hours=24,
            carbon_price=10.0,
        ),
    }

    @pytest.mark.parametrize("case", sorted(CASES))
    def test_resolved_prices_are_bit_identical(self, case, monkeypatch):
        kwargs = self.CASES[case]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            with_guard = ScenarioConfig(**kwargs)
            guarded = [resolve_carbon_price(with_guard, y) for y in HORIZON]

        monkeypatch.setattr(
            carbon_policy, "carbon_price_below_base_warning", lambda config: None
        )
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            without_guard = ScenarioConfig(**kwargs)
            unguarded = [resolve_carbon_price(without_guard, y) for y in HORIZON]

        assert _below_base_warnings(list(caught)) == []  # the silencing worked
        assert unguarded == guarded  # bit-equal, not approx


class TestYearRunRendering:
    """``_format_year_runs`` collapses contiguous runs, keeps the gaps."""

    @pytest.mark.parametrize(
        "years,expected",
        [
            ([], ""),
            ([2030], "2030"),
            (list(range(2026, 2051)), "2026-2050"),
            ([2026, 2027, 2028, 2040], "2026-2028, 2040"),
            ([2026, 2028, 2030], "2026, 2028, 2030"),
        ],
    )
    def test_rendering(self, years, expected):
        assert carbon_policy._format_year_runs(years) == expected
