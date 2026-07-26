"""ERCOT-111 — measured incremental-heat-rate floor on the COAL econ ramp.

Pins both sides of ``ScenarioConfig.coal_econ_marginal_hr_bound``:

* OFF (the default) — the resolved offer curve is untouched, so every existing
  keeper is byte-identical and the default ``cache_key`` is unmoved;
* ON — each coal class's ``econ_low`` / ``econ_high`` is clamped UP to the
  ISO's own measured CAMPD marginal heat rate for COAL, while markups above
  that basis, the ``committed`` / must-run take-or-pay bands and the ``peak``
  scarcity wall pass through unchanged (rule 19).

The floor is read from the already-committed measured artifact
``data/raw/reference/<iso>_campd_marginal_hr_summary.csv``
(``scripts/data/derive_campd_marginal_hr.py``) — this suite asserts the ERCOT
COAL row is present and that the loader reads its ``marg_econ_*_p50`` columns,
so a re-derive that dropped the class fails loudly rather than silently
disarming the mechanism.
"""

from __future__ import annotations

import dataclasses

import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.coal import (
    COAL_ECON_MARGINAL_HR_BANDS,
    apply_coal_econ_marginal_hr_floor,
    coal_marginal_hr_bounds,
)


@pytest.fixture
def curve() -> dict[str, dict]:
    """A resolved ERCOT-shaped offer curve: PRB below basis, lignite above."""
    return {
        # The ERCOT keeper's resolved bands (base 0.70 + the fitted -0.30 run
        # delta => econ_low 0.40, 2.2x below the measured 0.886).
        "COAL_PRB": {
            "committed": 0.91,
            "econ_low": 0.40,
            "econ_high": 1.38,
            "peak": 1.562,
            "econ_low_share": 0.556,
        },
        "COAL_LIGNITE": {
            "committed": 0.88,
            "econ_low": 1.216,
            "econ_high": 1.113,
            "peak": 1.55,
            "econ_low_share": 0.556,
        },
        # A non-coal class far below the coal basis: must never be touched.
        "CC_REGULAR": {"committed": 1.048, "econ_low": 0.10, "econ_high": 1.454},
    }


class TestMeasuredArtifact:
    def test_ercot_coal_row_present(self):
        bounds = coal_marginal_hr_bounds("ERCOT")
        assert set(bounds) == set(COAL_ECON_MARGINAL_HR_BANDS)
        # The committed derive_campd_marginal_hr artifact's ERCOT COAL row.
        assert bounds["econ_low"] == pytest.approx(0.886)
        assert bounds["econ_high"] == pytest.approx(0.898)

    def test_unknown_iso_is_empty(self):
        assert coal_marginal_hr_bounds("NOT_AN_ISO") == {}

    def test_iso_without_coal_row_is_empty(self):
        # CAISO's artifact carries no COAL row (no CEMS coal fleet).
        assert coal_marginal_hr_bounds("CAISO") == {}


class TestFloorApplication:
    def test_lifts_only_bands_below_basis(self, curve):
        out, lifted = apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        assert lifted == [("COAL_PRB", "econ_low", 0.40, 0.886)]
        assert out["COAL_PRB"]["econ_low"] == pytest.approx(0.886)

    def test_markups_above_basis_pass_through(self, curve):
        out, _ = apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        # PRB econ_high 1.38 > 0.898 and lignite's whole ramp is above basis.
        assert out["COAL_PRB"]["econ_high"] == pytest.approx(1.38)
        assert out["COAL_LIGNITE"]["econ_low"] == pytest.approx(1.216)
        assert out["COAL_LIGNITE"]["econ_high"] == pytest.approx(1.113)

    def test_committed_mustrun_and_peak_out_of_scope(self, curve):
        out, _ = apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        # committed 0.91 / 0.88 sit ABOVE 0.886 and 0.88 sits below it — neither
        # is floored, because the take-or-pay band is a contractual discount and
        # the peak band is a scarcity wall (rule 19).
        assert out["COAL_PRB"]["committed"] == pytest.approx(0.91)
        assert out["COAL_LIGNITE"]["committed"] == pytest.approx(0.88)
        assert out["COAL_PRB"]["peak"] == pytest.approx(1.562)

    def test_non_coal_classes_untouched(self, curve):
        out, _ = apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        assert out["CC_REGULAR"]["econ_low"] == pytest.approx(0.10)

    def test_input_not_mutated(self, curve):
        apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        assert curve["COAL_PRB"]["econ_low"] == pytest.approx(0.40)

    def test_no_artifact_is_a_no_op(self, curve):
        out, lifted = apply_coal_econ_marginal_hr_floor(curve, "NOT_AN_ISO")
        assert lifted == []
        assert out == curve

    def test_non_float_bands_skipped(self):
        # peak_ladder rungs are lists; econ_low_share is a share, not a band.
        curve = {"COAL_PRB": {"econ_low": [[0.2, 1.5]], "econ_high": None}}
        out, lifted = apply_coal_econ_marginal_hr_floor(curve, "ERCOT")
        assert lifted == []
        assert out["COAL_PRB"]["econ_low"] == [[0.2, 1.5]]


class TestGate:
    def test_default_is_off(self):
        assert ScenarioConfig().coal_econ_marginal_hr_bound is False

    def test_field_exists_on_config(self):
        names = {f.name for f in dataclasses.fields(ScenarioConfig)}
        assert "coal_econ_marginal_hr_bound" in names

    def test_registered_cache_key_optional(self):
        # Default-off must not move any historical cache key (keeper replay).
        assert "coal_econ_marginal_hr_bound" in _CACHE_KEY_OPTIONAL_FIELDS
        assert (
            ScenarioConfig().cache_key()
            == ScenarioConfig(coal_econ_marginal_hr_bound=False).cache_key()
        )

    def test_armed_run_gets_a_distinct_cache_key(self):
        assert (
            ScenarioConfig(coal_econ_marginal_hr_bound=True).cache_key()
            != ScenarioConfig().cache_key()
        )


class TestErcotPromotion:
    """ercot-115 promotion (owner sign-off 2026-07-26): ERCOT-scoped default-ON.

    The floor is enabled in the ERCOT branch of ``backcast_config`` rather than
    by flipping the global ``ScenarioConfig`` default, because the mechanism is
    ISO-generic and reads each ISO's own artifact — flipping the default would
    silently re-point the PJM / MISO / NEISO keepers, which have never tested it
    (rule 25). These tests pin that scoping and the tri-state seam the promotion
    depends on.
    """

    def test_ercot_backcast_default_is_on(self):
        from market_sim.pipeline.backcast_config import backcast_config

        cfg = backcast_config(2023, "ERCOT", 8760, 2.54)
        assert cfg.coal_econ_marginal_hr_bound is True

    @pytest.mark.parametrize("iso", ["PJM", "MISO", "NEISO", "CAISO", "NYISO"])
    def test_other_isos_stay_off(self, iso):
        # Each of these reads its OWN artifact, so arming them is a decision for
        # their own lane — never a side effect of ERCOT's promotion.
        from market_sim.pipeline.backcast_config import backcast_config

        cfg = backcast_config(2023, iso, 8760, 2.54)
        assert cfg.coal_econ_marginal_hr_bound is False

    def test_global_default_still_off(self):
        # The promotion must NOT have flipped the shared default — that is the
        # whole point of scoping it per-ISO.
        assert ScenarioConfig().coal_econ_marginal_hr_bound is False

    @pytest.mark.parametrize(
        ("kwarg", "config_value", "expected"),
        [
            (None, True, True),  # per-ISO default-ON, no CLI opinion -> ON
            (None, False, False),  # default-off ISO, no CLI opinion -> OFF
            (False, True, False),  # explicit scrub of a default-ON (ablation)
            (True, False, True),  # explicit arm on an ISO that defaults off
        ],
    )
    def test_tristate_resolution(self, kwarg, config_value, expected):
        # Mirrors the resolution in run_calibration.run_year and
        # run_calibration_full._recorded_config. A bare ``or`` would make the
        # explicit-False scrub case unreachable once a per-ISO default is on.
        resolved = bool(config_value) if kwarg is None else bool(kwarg)
        assert resolved is expected

    def test_cli_default_is_none_not_false(self):
        # A False CLI default would pass an explicit False on every run and
        # scrub any per-ISO default, so a promotion would never take effect on
        # the calibration path at all.
        from market_sim.pipeline.flags import iter_family

        spec = next(
            s for s in iter_family("coal") if s.dest == "coal_econ_marginal_hr_bound"
        )
        assert spec.default is None
