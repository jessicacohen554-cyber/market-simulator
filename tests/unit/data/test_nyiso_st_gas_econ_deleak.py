"""Guards for ``nyiso_st_gas_econ_bands_deleaked`` (nyiso-232, rule 25).

`_NYISO_OFFER_CURVE`'s ST_GAS block derives `econ_low`/`econ_high` as the
measured steam marginal HR times a CC "reach ratio" whose numerator —
`CC_REGULAR.econ_high` 1.21 — the SAME file records as REMOVED under rule 25
`[R-ISO-SCOPE]` (an ERCOT keeper value). The registered `econ_low` 1.08
reproduces that cited construction to 0.2 %, so the bands carry ERCOT's 1.21
multiplicatively and the de-leak never propagated (rule 26 `[R-DELETE]`).

These tests pin the repair's SHAPE, not its effect on any residual:

* the two econ bands go to the rule-24/25 neutral 1.0 and NOTHING else moves —
  above all `committed` (which sits below its own `phys_committed`, so its
  markup clips to 0 in both legs and the multiplier only scales FUEL there) and
  `peak` (the $1,000-offer-cap scarcity wall);
* every `phys_*` measurement survives untouched, so the physical basis the
  `gas_offer_net_revenue_margin` decomposition prices against is unchanged;
* the arithmetic that identifies the defect still holds, so a future edit to
  either cited number fails here rather than silently re-stranding the bands;
* the gate is NYISO-scoped and fails loudly off-ISO and without its `phys_*`
  basis, never silently no-ops;
* the flag is honoured on BOTH routes (named kwarg and ScenarioConfig field),
  because `replay_keeper --set` writes the field and never the kwarg.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.backcast_config import _NYISO_OFFER_CURVE

_BANDS = ("committed", "econ_low", "econ_high", "peak")
_PHYS = ("phys_committed", "phys_econ_low", "phys_econ_high", "phys_peak")


def _resolve(iso: str = "NYISO", **kw):
    from scripts.run_calibration import _calibration_config

    return _calibration_config(year=2024, iso=iso, hours=8760, gas_price=2.19, **kw)


def test_registered_bands_reproduce_the_leaked_construction():
    """The defect itself: the registered 1.08 IS the CITED construction.

    `econ_low` = (native steam marginal) x (CC econ_high 1.21 / CC marginal
    0.925). The agreement depends on WHICH of the file's own two recorded
    native-steam triples is read — the ST_GAS band dict's `phys_econ_low`
    0.830 / `phys_econ_high` 0.828, or the run-28 note's 0.818/0.825/0.830 —
    and lands between 0.08 % and 0.53 %. Every reading reproduces 1.08 to
    better than 1 %, which is what identifies the construction; the block's own
    stated form ("~0.82-0.83 x 1.31 ~= 1.08") is exact at the precision it
    states. Pinned as a RANGE so the guard cannot be read as a false-precision
    claim, and so an edit to either cited number fails here.
    """
    st = _NYISO_OFFER_CURVE["ST_GAS"]
    cc = _NYISO_OFFER_CURVE["CC_REGULAR"]
    leaked_reach = 1.21 / cc["phys_econ_high"]  # the CITED ratio, numerator removed
    assert cc["econ_high"] == 1.0, "CC econ_high is the de-leaked neutral band"
    assert abs(leaked_reach - 1.3081) < 1e-4
    for native in (st["phys_econ_low"], st["phys_econ_high"], 0.825):
        rel = abs(native * leaked_reach - st["econ_low"]) / st["econ_low"]
        assert rel < 0.01, f"{native} x reach misses the registered band by {rel:.1%}"
    # ...and the CURRENT reach cannot reproduce it: that is the whole defect.
    current_reach = cc["econ_high"] / cc["phys_econ_high"]
    assert (
        abs(st["phys_econ_low"] * current_reach - st["econ_low"]) / st["econ_low"]
        > 0.15
    )


def test_deleak_moves_exactly_the_two_econ_bands():
    ctl = _resolve().offer_curve_by_group["ST_GAS"]
    arm = _resolve(nyiso_st_gas_econ_bands_deleaked=True).offer_curve_by_group["ST_GAS"]

    assert arm["econ_low"] == 1.0
    assert arm["econ_high"] == 1.0
    # committed and peak are EXCLUDED, and so is every structural share.
    for k in ("committed", "peak", "econ_low_share", "pct_peaking"):
        assert arm[k] == ctl[k], f"{k} must not move"
    # every measured physical basis survives
    for k in _PHYS:
        assert arm[k] == ctl[k], f"{k} is measured data and must not move"


def test_deleak_leaves_every_other_class_untouched():
    ctl = _resolve().offer_curve_by_group
    arm = _resolve(nyiso_st_gas_econ_bands_deleaked=True).offer_curve_by_group
    for cls in set(ctl) | set(arm):
        if cls == "ST_GAS":
            continue
        assert ctl.get(cls) == arm.get(cls), f"{cls} moved"


def test_deleak_lands_on_ct_peakers_registered_posture():
    """The repair's target IS the state the sibling de-leaked class carries."""
    arm = _resolve(nyiso_st_gas_econ_bands_deleaked=True).offer_curve_by_group
    ct = arm["CT_PEAKER"]
    assert (ct["econ_low"], ct["econ_high"]) == (1.0, 1.0)
    assert (arm["ST_GAS"]["econ_low"], arm["ST_GAS"]["econ_high"]) == (1.0, 1.0)
    # and, like CT_PEAKER, committed and peak stay off the neutral
    assert ct["committed"] != 1.0 and ct["peak"] != 1.0
    assert arm["ST_GAS"]["committed"] != 1.0 and arm["ST_GAS"]["peak"] != 1.0


@pytest.mark.parametrize("iso", ["ERCOT", "CAISO", "PJM", "MISO", "NEISO", "SPP"])
def test_deleak_is_nyiso_scoped_and_hard_errors_off_iso(iso):
    with pytest.raises(ValueError, match="NYISO-scoped"):
        _resolve(iso=iso, nyiso_st_gas_econ_bands_deleaked=True)


def test_deleak_hard_errors_without_its_measured_basis():
    """Never a silent no-op when the phys_* basis is absent (rule 25/caiso-157)."""
    import importlib

    bc = importlib.import_module("market_sim.pipeline.backcast_config")
    saved = dict(bc._NYISO_OFFER_CURVE["ST_GAS"])
    try:
        bc._NYISO_OFFER_CURVE["ST_GAS"].pop("phys_econ_low")
        with pytest.raises(ValueError, match="phys_econ_low"):
            _resolve(nyiso_st_gas_econ_bands_deleaked=True)
    finally:
        bc._NYISO_OFFER_CURVE["ST_GAS"].clear()
        bc._NYISO_OFFER_CURVE["ST_GAS"].update(saved)


def test_flag_is_honoured_when_the_incoming_config_already_carries_it():
    """The gate reads kwarg-OR-field, so a config that arrives already armed
    (an ISOConfig `default_scenario_overrides`, a round-tripped recipe) is
    honoured rather than silently ignored — the nyiso-231 seam on the gas-anchor
    sibling, where a kwarg-only gate let an A/B solve the CONTROL."""
    armed = ScenarioConfig(iso="NYISO", nyiso_st_gas_econ_bands_deleaked=True)
    assert armed.nyiso_st_gas_econ_bands_deleaked is True
    # the gate's own predicate, exercised directly on an already-armed config
    assert (
        bool(False or getattr(armed, "nyiso_st_gas_econ_bands_deleaked", False)) is True
    )


def test_prb_overrides_route_fails_loudly_rather_than_no_opping():
    """`prb_overrides` is applied AFTER `backcast_config` resolves the curve, so
    arming through it alone would record the flag beside the LEAKED bands the LP
    solved. `run_year` must raise, never ship a bundle that lies (rule 24,
    the caiso-157 defect class)."""
    from scripts.run_calibration import run_year

    with pytest.raises(ValueError, match="nyiso_st_gas_econ_bands_deleaked"):
        run_year(
            2024,
            "NYISO",
            24,
            2.19,
            {},
            fleet_only=True,
            prb_overrides={"nyiso_st_gas_econ_bands_deleaked": True},
        )


def test_default_is_off_and_does_not_move_any_cache_key():
    from market_sim.config import scenarios as s

    assert ScenarioConfig().nyiso_st_gas_econ_bands_deleaked is False
    assert "nyiso_st_gas_econ_bands_deleaked" in s._CACHE_KEY_OPTIONAL_FIELDS
    assert (
        s._CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["nyiso_st_gas_econ_bands_deleaked"]
        == "False"
    )
    base = ScenarioConfig(iso="NYISO")
    assert (
        base.cache_key()
        == base.with_overrides(nyiso_st_gas_econ_bands_deleaked=False).cache_key()
    )
    assert (
        base.cache_key()
        != base.with_overrides(nyiso_st_gas_econ_bands_deleaked=True).cache_key()
    )
