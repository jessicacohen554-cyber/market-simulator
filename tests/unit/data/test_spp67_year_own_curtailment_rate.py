"""SPP-67: the year-own curtailment rate (``vre_reference_rate_year_own``).

Guards the three properties the mechanism is promoted on:

1. **It re-keys nothing and changes nothing when off.** The reference rate is
   pinned to the exact value every registered keeper solved on, and the gated
   seam is proven identical to the ungated reader for every ISO-fuel-year.
2. **Rule 23 ``[R-FROZEN-DERIVE]``: nothing was re-derived.** The committed
   2023-2025 delivered rows and their rates are pinned to the values lane
   SPP-32 landed; the 2019-2022 rows added alongside them are a coverage
   extension and must not perturb the training-window mean.
3. **Rule 25 ``[R-ISO-SCOPE]``: the year-own registry is SPP wind alone**, so
   an armed run leaves every other ISO-fuel on the reference-rate path.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import renewables as R

# The value every SPP run registered before SPP-67 was solved on. Pinning it is
# what makes the coverage extension of the source table provably inert on the
# reference path (rule 23 [R-FROZEN-DERIVE]).
REFERENCE_RATE = 0.09650131886270663

# SPP-32's committed delivered rows, and the rates they form. Re-derived by
# SPP-67 from the same GenMix CSVs and reproduced exactly; pinned so a future
# re-derivation of the table cannot move them silently.
COMMITTED_RATES = {
    2023: 0.08493407350629845,
    2024: 0.10561173621991170,
    2025: 0.09895814686190971,
}

# The rows SPP-67 added, from SPP MMU ASOM curtailment MW already in the table
# paired with GenMix delivered wind on SPP-32's construction.
ADDED_RATES = {2019: 0.015908220021133547, 2022: 0.0935682937153296}

# SPP publishes no average hourly curtailment MW for these, so no rate forms
# and they must keep the reference-rate path even when the gate is armed.
UNPUBLISHED_YEARS = (2020, 2021)


def test_reference_rate_is_unchanged_by_the_coverage_extension() -> None:
    """The training-window mean must be byte-identical to what keepers solved on."""
    rate, latest = R._spp_wind_reference_curtailment_rate()
    assert rate == pytest.approx(REFERENCE_RATE, abs=1e-15)
    assert latest == 2025


def test_reference_window_still_excludes_the_added_years() -> None:
    """SPP-67 widens the READER, never the reference window itself."""
    assert R._SPP_REFERENCE_RATE_YEARS == frozenset({2023, 2024, 2025})


@pytest.mark.parametrize(("year", "expected"), sorted(COMMITTED_RATES.items()))
def test_committed_rows_reproduce(year: int, expected: float) -> None:
    assert R._spp_wind_annual_rates()[year] == pytest.approx(expected, abs=1e-12)


@pytest.mark.parametrize(("year", "expected"), sorted(ADDED_RATES.items()))
def test_added_rows_pair_into_a_year_own_rate(year: int, expected: float) -> None:
    own = R._spp_wind_year_own_curtailment_rate(year)
    assert own is not None
    assert own[0] == pytest.approx(expected, abs=1e-12)
    assert own[1] == year


@pytest.mark.parametrize("year", UNPUBLISHED_YEARS)
def test_unpublished_years_form_no_year_own_rate(year: int) -> None:
    assert R._spp_wind_year_own_curtailment_rate(year) is None


def test_2019_is_the_object_and_it_is_large() -> None:
    """The defect this mechanism repairs, stated as a guard rather than prose."""
    own = R._spp_wind_year_own_curtailment_rate(2019)
    assert own is not None
    reference, _ = R._spp_wind_reference_curtailment_rate()
    # SPP's own published 2019 rate is ~1.6 %; the training mean applies ~9.7 %.
    assert own[0] < 0.02 < reference
    assert reference / own[0] > 5.0


@pytest.mark.parametrize("year", range(2019, 2026))
@pytest.mark.parametrize(
    ("iso", "fuel"), [("SPP", "wind"), ("SPP", "solar"), ("MISO", "wind")]
)
def test_seam_is_identical_to_the_reference_reader_when_off(
    iso: str, fuel: str, year: int
) -> None:
    """Default-off, the gated seam IS ``_reference_curtailment_rate`` exactly."""
    assert R._curtailment_rate_for_year(iso, fuel, year, False) == (
        R._reference_curtailment_rate(iso, fuel)
    )


@pytest.mark.parametrize("year", range(2019, 2026))
@pytest.mark.parametrize(
    ("iso", "fuel"), [("SPP", "solar"), ("MISO", "wind"), ("CAISO", "wind")]
)
def test_armed_seam_leaves_every_other_iso_fuel_alone(
    iso: str, fuel: str, year: int
) -> None:
    """Rule 25 [R-ISO-SCOPE]: the registry carries SPP wind and nothing else."""
    assert R._curtailment_rate_for_year(iso, fuel, year, True) == (
        R._reference_curtailment_rate(iso, fuel)
    )


def test_year_own_registry_is_spp_wind_only() -> None:
    assert set(R._YEAR_OWN_RATE_PROVIDERS) == {("SPP", "wind")}


@pytest.mark.parametrize("year", UNPUBLISHED_YEARS)
def test_armed_spp_wind_falls_back_on_an_unpublished_year(year: int) -> None:
    assert R._curtailment_rate_for_year("SPP", "wind", year, True) == (
        R._reference_curtailment_rate("SPP", "wind")
    )


@pytest.mark.parametrize("year", sorted(COMMITTED_RATES | ADDED_RATES))
def test_armed_spp_wind_uses_the_years_own_rate(year: int) -> None:
    got = R._curtailment_rate_for_year("SPP", "wind", year, True)
    assert got == R._spp_wind_year_own_curtailment_rate(year)


def test_field_defaults_off_and_is_cache_key_registered() -> None:
    """Rules 24 / 28: a solve-affecting field is registered in the same commit."""
    assert ScenarioConfig(iso="SPP").vre_reference_rate_year_own is False
    assert "vre_reference_rate_year_own" in _CACHE_KEY_OPTIONAL_FIELDS
    assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["vre_reference_rate_year_own"] == "False"


def test_field_keys_when_armed_and_not_when_defaulted() -> None:
    base = ScenarioConfig(iso="SPP", mode="backcast")
    explicit_default = ScenarioConfig(
        iso="SPP", mode="backcast", vre_reference_rate_year_own=False
    )
    armed = ScenarioConfig(iso="SPP", mode="backcast", vre_reference_rate_year_own=True)
    assert base.cache_key() == explicit_default.cache_key()
    assert base.cache_key() != armed.cache_key()
