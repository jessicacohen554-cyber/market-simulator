"""pjm-132: the within-season tightness vintage of the PJM offer-surface family.

Owner-authorized 2026-07-27 with an amendment
(``docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`` decision banner;
charter ``docs/handoffs/pjm-132-midcurve-reconditioning-charter-2026-07.md``):
the within-YEAR surfaces stay live and keep their filenames, the within-season
vintage lives in separate artifacts, and one default-OFF ScenarioConfig gate
switches the JSON vintage and the solve-time binning **together**.

What is pinned here:

* **Default-off byte identity** — the gate is off by default and the binning
  helper reproduces the original ``np.quantile``/``searchsorted`` construction
  exactly, so every existing keeper and forecast run is unchanged.
* **The seasonal binning does what it claims** — under within-season ranking
  each season contributes ~the same share of the tight bin, which is the whole
  point (an annual top-percentile bin is structurally a summer-only sample in
  a summer-peaking ISO).
* **The vintage guard** — an armed gate against a within-year JSON, and an
  unarmed gate against a within-season JSON, both hard-fail rather than
  silently mismeasure.
* **Rule 25** — the season map is PJM's; no other ISO's binning changes.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.constants import PJM_SEASON_OF_MONTH
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet.offer_surfaces import (
    _assert_surface_vintage,
    _month_of_hour,
    _tightness_hour_bin,
)

EDGES = (0.80, 0.90, 0.97)


def _net_load(hours: int = 8760, seed: int = 0) -> np.ndarray:
    """Synthetic PJM-shaped net load: summer-peaking with a winter secondary."""
    rng = np.random.default_rng(seed)
    t = np.arange(hours)
    month = _month_of_hour(hours)
    seasonal = np.where(
        np.isin(month, (6, 7, 8, 9)),
        110_000.0,
        np.where(np.isin(month, (12, 1, 2, 3)), 95_000.0, 80_000.0),
    )
    diurnal = 8_000.0 * np.sin(2 * np.pi * (t % 24) / 24.0)
    return seasonal + diurnal + rng.normal(0.0, 3_000.0, hours)


def test_gate_is_default_off() -> None:
    """The within-year config stays the default (the owner's amendment)."""
    assert ScenarioConfig().pjm_offer_surface_within_season is False


def test_within_year_binning_is_byte_identical_to_the_original() -> None:
    """Gate off reproduces the pre-change construction exactly."""
    net_load = _net_load()
    expected = np.searchsorted(np.quantile(net_load, EDGES), net_load, side="right")
    got = _tightness_hour_bin(net_load, EDGES, within_season=False)
    assert np.array_equal(got, expected)


def test_empty_edges_yield_a_single_bin() -> None:
    """No edges → every hour in bin 0, matching the original guard."""
    net_load = _net_load(240)
    assert not _tightness_hour_bin(net_load, (), within_season=False).any()
    assert not _tightness_hour_bin(net_load, (), within_season=True).any()


def test_within_year_tight_bin_is_a_summer_only_sample() -> None:
    """The defect the re-conditioning exists to remove, pinned as a baseline."""
    net_load = _net_load()
    month = _month_of_hour(net_load.size)
    tight = _tightness_hour_bin(net_load, EDGES, within_season=False) == len(EDGES)
    seasons = np.array([PJM_SEASON_OF_MONTH[int(m)] for m in month])
    summer_share = float((seasons[tight] == "summer").mean())
    # A summer-peaking ISO's annual top-percentile bin is overwhelmingly summer.
    assert summer_share > 0.90


def test_within_season_balances_the_tight_bin_across_seasons() -> None:
    """Each season contributes ~its own top percentile — the intended semantics."""
    net_load = _net_load()
    month = _month_of_hour(net_load.size)
    seasons = np.array([PJM_SEASON_OF_MONTH[int(m)] for m in month])
    tight = _tightness_hour_bin(net_load, EDGES, within_season=True) == len(EDGES)
    for season in ("summer", "winter", "shoulder"):
        in_season = seasons == season
        # ~3% of every season's own hours (edges top out at 0.97).
        share = float(tight[in_season].mean())
        assert 0.02 < share < 0.05, (season, share)


def test_within_season_preserves_the_bin_count() -> None:
    """Same edges → same number of bins, both vintages (the shared contract)."""
    net_load = _net_load()
    for within_season in (False, True):
        bins = _tightness_hour_bin(net_load, EDGES, within_season=within_season)
        assert bins.min() >= 0
        assert bins.max() == len(EDGES)


def test_month_of_hour_handles_leap_years() -> None:
    """Month boundaries follow the array's leap-ness when no year is given."""
    assert _month_of_hour(8760)[-1] == 12
    assert _month_of_hour(8784)[-1] == 12
    # 2024-02-29 exists, so hour 1416 (Mar 1 in a non-leap year) is still Feb.
    assert _month_of_hour(8784, 2024)[1416] == 2
    assert _month_of_hour(8760, 2023)[1416] == 3


@pytest.mark.parametrize(
    ("tag", "within_season", "should_raise"),
    [
        (None, False, False),  # legacy JSON, gate off — the live default
        ("within-year", False, False),
        ("within-season", True, False),
        ("within-season", False, True),  # unarmed gate, seasonal JSON
        ("within-year", True, True),  # armed gate, year JSON
        (None, True, True),  # armed gate, legacy JSON
    ],
)
def test_vintage_guard_pairs_json_with_binning(
    tag: str | None, within_season: bool, should_raise: bool
) -> None:
    """A half-updated state hard-fails instead of silently mismeasuring."""
    prov: dict = {} if tag is None else {"conditioning": tag}
    surface = {"_provenance": prov}
    if should_raise:
        with pytest.raises(ValueError, match="surface vintage mismatch"):
            _assert_surface_vintage(surface, within_season, "pjm_test", "re-derive")
    else:
        _assert_surface_vintage(surface, within_season, "pjm_test", "re-derive")


def test_season_map_is_the_preregistered_definition() -> None:
    """Memo §3 / pjm-126 commit 9409f7f — symmetric 4/4/4, PJM's own convention."""
    assert PJM_SEASON_OF_MONTH == {
        1: "winter",
        2: "winter",
        3: "winter",
        4: "shoulder",
        5: "shoulder",
        6: "summer",
        7: "summer",
        8: "summer",
        9: "summer",
        10: "shoulder",
        11: "shoulder",
        12: "winter",
    }
    counts = {
        s: sum(1 for v in PJM_SEASON_OF_MONTH.values() if v == s)
        for s in set(PJM_SEASON_OF_MONTH.values())
    }
    assert counts == {"summer": 4, "winter": 4, "shoulder": 4}
