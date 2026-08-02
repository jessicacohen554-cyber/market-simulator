"""Mode-hygiene guards on ScenarioConfig (FFR-1D; audit FR-10, FR-11, FR-15).

Three invariants, all pure config construction — no solve, no data root:

* **FR-10** ``correlated_forced_outage`` is coerced OFF in a backcast, so a
  backcast built outside ``pipeline/backcast_config.py`` (a YAML, a sweep
  member, a fixture) cannot get a spuriously distinct cache key for a solve
  that is byte-identical.
* **FR-11** the backcast-only MEASURED-overlay family hard-errors in forecast
  mode — rule 13's "never fires in forecast", enforced by the config rather
  than by operator discipline at the front end.
* **FR-15** ``_CACHE_KEY_OPTIONAL_FIELDS`` holds no duplicate literal.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config.scenarios import (
    _BACKCAST_ONLY_OUTAGE_SOURCE,
    _BACKCAST_ONLY_OVERLAY_FIELDS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)


# --------------------------------------------------------------------------- #
# FR-10 — correlated_forced_outage backcast coercion
# --------------------------------------------------------------------------- #
class TestCorrelatedForcedOutageCoercion:
    def test_backcast_coerces_the_derate_off(self):
        assert ScenarioConfig(mode="backcast").correlated_forced_outage is False

    def test_forecast_keeps_the_flipped_default_on(self):
        assert ScenarioConfig(mode="forecast").correlated_forced_outage is True

    def test_hindcast_harness_is_not_coerced(self):
        """The FF-1B probe legs arm it explicitly on the hindcast harness."""
        cfg = ScenarioConfig(mode="forecast", hindcast=True)
        assert cfg.correlated_forced_outage is True

    def test_a_backcast_built_two_ways_now_hashes_the_same(self):
        """The defect: identical backcast solves getting distinct cache keys.

        ``pipeline/backcast_config.py`` pins the field False; anything else
        inherited the FF-1F default-ON flip. Both must key identically, since
        the mechanism is a guaranteed no-op in a backcast either way.
        """
        via_builder = ScenarioConfig(mode="backcast", correlated_forced_outage=False)
        via_yaml = ScenarioConfig(mode="backcast")
        assert via_yaml.cache_key() == via_builder.cache_key()

    def test_forecast_default_cache_key_is_untouched(self):
        """The coercion must not move any forecast key — it is backcast-only."""
        armed = ScenarioConfig(mode="forecast")
        assert armed.cache_key() != ScenarioConfig(mode="backcast").cache_key()
        assert armed.correlated_forced_outage is True


# --------------------------------------------------------------------------- #
# FR-11 — the backcast-only measured-overlay family
# --------------------------------------------------------------------------- #
class TestBackcastOnlyOverlayGuard:
    def test_every_listed_field_exists_on_the_dataclass(self):
        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        unknown = sorted(set(_BACKCAST_ONLY_OVERLAY_FIELDS) - names)
        assert not unknown, f"registry names non-fields: {unknown}"

    def test_every_listed_field_carries_a_reason(self):
        blank = [k for k, v in _BACKCAST_ONLY_OVERLAY_FIELDS.items() if not v.strip()]
        assert not blank, f"no rule-13 reason recorded for: {blank}"

    def test_every_listed_field_is_inert_at_its_default(self):
        """A default-armed member would make every default forecast raise."""
        defaults = ScenarioConfig(mode="forecast")
        armed = [
            name
            for name in _BACKCAST_ONLY_OVERLAY_FIELDS
            if getattr(defaults, name) not in (None, False)
        ]
        assert not armed, f"listed overlays are ON by default: {armed}"

    @pytest.mark.parametrize("field", sorted(_BACKCAST_ONLY_OVERLAY_FIELDS))
    def test_forecast_refuses_each_overlay(self, field):
        with pytest.raises(ValueError, match="backcast-only measured overlays"):
            ScenarioConfig(mode="forecast", **{field: True})

    @pytest.mark.parametrize("field", sorted(_BACKCAST_ONLY_OVERLAY_FIELDS))
    def test_backcast_accepts_each_overlay(self, field):
        assert getattr(ScenarioConfig(mode="backcast", **{field: True}), field)

    def test_historic_outage_source_is_refused_in_forecast(self):
        with pytest.raises(ValueError, match="outage_source"):
            ScenarioConfig(mode="forecast", outage_source=_BACKCAST_ONLY_OUTAGE_SOURCE)

    def test_statistical_outage_source_is_the_forward_construction(self):
        """The default is the WEFOR/POF model — the forward-derivable half."""
        assert ScenarioConfig(mode="forecast").outage_source == "statistical"

    def test_the_hindcast_harness_is_guarded_too(self):
        """A capacity hindcast / crossover IS the forecast path being validated."""
        with pytest.raises(ValueError, match="backcast-only measured overlays"):
            ScenarioConfig(mode="forecast", hindcast=True, gas_monthly_actuals=True)

    def test_the_message_names_every_armed_overlay(self):
        with pytest.raises(ValueError) as exc:
            ScenarioConfig(
                mode="forecast", gas_daily_shape=True, coal_mustrun_per_plant=True
            )
        assert "gas_daily_shape" in str(exc.value)
        assert "coal_mustrun_per_plant" in str(exc.value)


# --------------------------------------------------------------------------- #
# FR-15 — the hand-maintained cache-key registry
# --------------------------------------------------------------------------- #
def test_cache_key_optional_fields_are_unique():
    """A duplicated literal makes a "did I register it?" grep answer yes twice."""
    seen: set[str] = set()
    dupes = sorted({n for n in _CACHE_KEY_OPTIONAL_FIELDS if n in seen or seen.add(n)})
    assert not dupes, f"_CACHE_KEY_OPTIONAL_FIELDS lists twice: {dupes}"


def test_cache_key_optional_fields_are_all_real_fields():
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    unknown = sorted(set(_CACHE_KEY_OPTIONAL_FIELDS) - names)
    assert not unknown, f"registered names that are not fields: {unknown}"
