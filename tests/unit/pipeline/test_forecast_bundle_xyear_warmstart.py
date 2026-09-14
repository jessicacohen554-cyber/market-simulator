"""D-10 — cross-year LP warm start is OFF for every FORECAST BUNDLE.

Owner decision **D-10** (signed 2026-08-04, sitting
``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum K.3, on FFR-3M's
measured adjudication of FF-3E part c; implemented by FFR-3T,
``docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md``): a forecast bundle runs
``forecast_xyear_warmstart=False``, so a killed-and-resumed forecast solves its
first post-kill year exactly as its uninterrupted control does — cold — instead
of landing on a different vertex of a degenerate optimal face.

**What this file exists to prevent.** D-10 is carried by an EXPLICIT argument
from each shipped forecast runner, not by the ``ScenarioConfig`` default, which
stays ``True`` (see ``FORECAST_BUNDLE_XYEAR_WARMSTART``'s comment block for the
measurements: a default flip would leave every forecast cache key colliding with
its warm predecessor AND move all six backcast keeper keys). That split is the
correct design and also a fragile one to read: a future session that "tidies"
the explicit argument away, or flips the default and assumes the forecast
follows, silently reverts a signed decision and re-reds the drill. So the
forecast-path value is pinned here directly, at every shipped runner, and the
key separation that makes a cold bundle addressable apart from a warm one is
pinned with it.

The complementary pins live in ``test_forecast_xyear_warmstart_flag.py`` and
``test_xyear_warmstart_default.py`` (the DEFAULT stays ``True``, the field stays
cache-registered, an explicit bool overrides the env var). Between the three, a
default flip cannot silently revert D-10: it breaks those two, and if it were
made to pass by removing the explicit argument it breaks this one.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import (
    FORECAST_BUNDLE_XYEAR_WARMSTART,
    ScenarioConfig,
)
from scripts.lib.forecast_posture import shipped_forecast_xyear_warmstart

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")


class TestPosture:
    """The D-10 posture constant and its ONE reader."""

    def test_posture_is_off(self):
        """D-10: forecast bundles run cross-year warm start OFF."""
        assert FORECAST_BUNDLE_XYEAR_WARMSTART is False

    def test_reader_returns_the_posture(self):
        """The runners read the constant; they never mirror a literal (rule 24)."""
        assert shipped_forecast_xyear_warmstart() is FORECAST_BUNDLE_XYEAR_WARMSTART

    def test_scenarioconfig_default_is_unchanged(self):
        """The DEFAULT deliberately stays ``True`` — D-10 is carried explicitly.

        Flipping it would (a) drop the new value from the cache key, so a cold
        forecast run would silently re-use a warm bundle, and (b) move all six
        backcast keeper keys, which carry an explicit ``true``. Both measured in
        ``docs/handoffs/ffr-3t-warmstart-off-2026-08-04.md`` §3.
        """
        assert ScenarioConfig().forecast_xyear_warmstart is True


@pytest.mark.parametrize("iso", ISOS)
class TestShippedForecastRunners:
    """Every shipped forecast-bundle runner builds its config warm-start OFF."""

    def test_full_horizon_reference_config(self, iso):
        """T1-F (``scripts/run_full_horizon.py``)."""
        from scripts.run_full_horizon import reference_config

        cfg = reference_config(iso, 2026, 2050, cmc=False, golden_posture=True)
        assert cfg.forecast_xyear_warmstart is False

    def test_capacity_hindcast_build_config(self, iso):
        """T1-H (``scripts/run_capacity_hindcast.py``)."""
        from scripts.run_capacity_hindcast import build_config

        cfg = build_config(iso, 2021, 2025, variant="realized")
        assert cfg.forecast_xyear_warmstart is False

    def test_capacity_hindcast_crossover_config(self, iso):
        """T1-X crossover — the same builder, the forward-boundary posture."""
        from scripts.run_capacity_hindcast import build_config

        cfg = build_config(iso, 2021, 2030, variant="realized", crossover=True)
        assert cfg.forecast_xyear_warmstart is False

    def test_golden_posture_config(self, iso):
        """The §2.1a golden posture, which the kill-resume drill itself solves."""
        from scripts.ff_readiness_battery import golden_posture_config

        cfg = golden_posture_config(iso)
        assert cfg.forecast_xyear_warmstart is False


class TestCacheKeySeparation:
    """A cold forecast bundle is addressed apart from its warm predecessor.

    This is the property that makes D-10 safe to land without a purge: the
    explicit ``False`` is non-default and so enters the hash, which is exactly
    what a default flip would NOT have done.
    """

    def test_forecast_config_key_differs_from_the_warm_arm(self):
        from scripts.run_full_horizon import reference_config

        cold = reference_config("ERCOT", 2026, 2050, cmc=False, golden_posture=True)
        warm = cold.with_overrides(forecast_xyear_warmstart=True)
        assert cold.forecast_xyear_warmstart is False
        assert warm.cache_key() != cold.cache_key()

    def test_backcast_config_key_is_untouched(self):
        """A backcast config never carries the D-10 value, so its key is stable.

        The equality is with the config that inherits the default — i.e. D-10
        reaches the forecast lane and nothing else.
        """
        backcast = ScenarioConfig(iso="ERCOT", mode="backcast")
        assert backcast.forecast_xyear_warmstart is True
        assert (
            backcast.cache_key()
            == ScenarioConfig(
                iso="ERCOT", mode="backcast", forecast_xyear_warmstart=True
            ).cache_key()
        )
