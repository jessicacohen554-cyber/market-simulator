"""miso-217 — `phys_*` coverage for the three duty-split intermediate cohorts.

``gas_offer_net_revenue_margin`` merges its ``phys_*`` keys onto exactly five gas
classes, so the ``*_INTERMEDIATE`` curves the duty splits route to carry none and
:func:`gas_offer_margin_markup_mult` returns its documented rule-24 neutral 0.0 —
the mechanism skips the cohort. ``miso_intermediate_gas_offer_margin`` closes that
gap by borrowing the PARENT class's already-frozen ``phys_econ_*``.

These pin the four properties the miso-217 PREREG froze before the solve:
flag-off byte identity, the ECON-ONLY band scope, the no-mutation copy contract,
and the rule-25 [R-ISO-SCOPE] MISO gate.
"""

from __future__ import annotations

import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.offer_curves import (
    _INTERMEDIATE_PHYS_KEYS,
    _INTERMEDIATE_PHYS_PARENT,
    _with_intermediate_phys,
    gas_offer_margin_markup_mult,
)

# The MISO keeper's own registered bands (miso213_layering_B run_config).
PARENTS = {
    "CT_PEAKER": {
        "committed": 1.025,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 4.0,
        "phys_committed": 1.025,
        "phys_econ_low": 0.687,
        "phys_econ_high": 0.691,
        "phys_peak": 1.0,
    },
    "CC_REGULAR": {
        "committed": 1.005,
        "econ_low": 0.95,
        "econ_high": 1.08,
        "peak": 2.25,
        "phys_committed": 1.005,
        "phys_econ_low": 0.887,
        "phys_econ_high": 1.008,
        "phys_peak": 2.25,
    },
    "ST_GAS": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.0,
        "peak": 1.0,
        "phys_committed": 1.079,
        "phys_econ_low": 0.812,
        "phys_econ_high": 0.849,
        "phys_peak": 1.0,
    },
}
INTERMEDIATES = {
    "CT_INTERMEDIATE": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.2,
        "peak": 3.0,
    },
    "CC_INTERMEDIATE": {
        "committed": 1.005,
        "econ_low": 0.95,
        "econ_high": 1.08,
        "peak": 2.25,
    },
    "ST_GAS_INTERMEDIATE": {
        "committed": 1.0,
        "econ_low": 1.0,
        "econ_high": 1.15,
        "peak": 2.2,
    },
}


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso=kw.pop("iso", "MISO"),
        mode="backcast",
        offer_curve_by_group={**PARENTS, **INTERMEDIATES},
        **kw,
    )


@pytest.mark.parametrize("key", sorted(INTERMEDIATES))
def test_flag_off_is_the_same_object(key: str) -> None:
    """Flag off => byte identity: the SAME dict comes back, unwrapped."""
    cfg = _cfg()
    assert cfg.miso_intermediate_gas_offer_margin is False  # default off
    inter = cfg.offer_curve_by_group[key]
    assert _with_intermediate_phys(inter, key, cfg) is inter


@pytest.mark.parametrize("key", sorted(INTERMEDIATES))
def test_flag_off_markup_is_neutral_zero(key: str) -> None:
    """Flag off => the documented rule-24 neutral fallback, every band."""
    cfg = _cfg()
    inter = _with_intermediate_phys(cfg.offer_curve_by_group[key], key, cfg)
    for suffix, mult in (
        ("committed", 1.0),
        ("econlo", 1.0),
        ("econhi", 1.2),
        ("peak", 3.0),
    ):
        assert gas_offer_margin_markup_mult(suffix, mult, inter) == 0.0


@pytest.mark.parametrize("key", sorted(INTERMEDIATES))
def test_flag_on_borrows_exactly_the_econ_keys(key: str) -> None:
    """ECON-ONLY: phys_econ_* borrowed, phys_committed / phys_peak never."""
    cfg = _cfg(miso_intermediate_gas_offer_margin=True)
    parent = PARENTS[_INTERMEDIATE_PHYS_PARENT[key]]
    out = _with_intermediate_phys(cfg.offer_curve_by_group[key], key, cfg)
    assert set(_INTERMEDIATE_PHYS_KEYS) == {"phys_econ_low", "phys_econ_high"}
    for k in _INTERMEDIATE_PHYS_KEYS:
        assert out[k] == parent[k]
    assert "phys_committed" not in out
    assert "phys_peak" not in out
    # the registered multipliers are untouched
    for band in ("committed", "econ_low", "econ_high", "peak"):
        assert out[band] == INTERMEDIATES[key][band]


@pytest.mark.parametrize("key", sorted(INTERMEDIATES))
def test_flag_on_returns_a_copy_and_never_mutates_the_config(key: str) -> None:
    """The recorded config must not acquire keys through this read path."""
    cfg = _cfg(miso_intermediate_gas_offer_margin=True)
    inter = cfg.offer_curve_by_group[key]
    before = dict(inter)
    out = _with_intermediate_phys(inter, key, cfg)
    assert out is not inter
    assert dict(cfg.offer_curve_by_group[key]) == before
    assert not any(k.startswith("phys_") for k in cfg.offer_curve_by_group[key])


@pytest.mark.parametrize("iso", ["ERCOT", "PJM", "CAISO", "NYISO", "NEISO"])
def test_rule_25_non_miso_is_untouched_even_with_the_flag_on(iso: str) -> None:
    """Rule 25 [R-ISO-SCOPE]: PJM/CAISO share the gap in kind — their lanes'."""
    cfg = _cfg(iso=iso, miso_intermediate_gas_offer_margin=True)
    for key in INTERMEDIATES:
        inter = cfg.offer_curve_by_group[key]
        assert _with_intermediate_phys(inter, key, cfg) is inter


def test_flag_on_markup_is_the_registered_minus_the_borrowed_physics() -> None:
    """The whole point: a live, positive markup on the econ bands only."""
    cfg = _cfg(miso_intermediate_gas_offer_margin=True)
    out = _with_intermediate_phys(
        cfg.offer_curve_by_group["CT_INTERMEDIATE"], "CT_INTERMEDIATE", cfg
    )
    # econ_low 1.00 - phys_econ_low 0.687; econ_high 1.20 - phys_econ_high 0.691
    assert gas_offer_margin_markup_mult("econlo", 1.0, out) == pytest.approx(0.313)
    assert gas_offer_margin_markup_mult("econhi", 1.2, out) == pytest.approx(0.509)
    # committed and peak stay neutral because their phys_* keys are absent
    assert gas_offer_margin_markup_mult("committed", 1.0, out) == 0.0
    assert gas_offer_margin_markup_mult("peak", 3.0, out) == 0.0


def test_a_parent_without_phys_keys_is_a_no_op() -> None:
    """Fail-safe: no parent phys => nothing merged, same object back."""
    cfg = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        miso_intermediate_gas_offer_margin=True,
        offer_curve_by_group={
            "CT_PEAKER": {
                "committed": 1.025,
                "econ_low": 1.0,
                "econ_high": 1.0,
                "peak": 4.0,
            },
            "CT_INTERMEDIATE": dict(INTERMEDIATES["CT_INTERMEDIATE"]),
        },
    )
    inter = cfg.offer_curve_by_group["CT_INTERMEDIATE"]
    assert _with_intermediate_phys(inter, "CT_INTERMEDIATE", cfg) is inter


def test_an_existing_key_is_never_overwritten() -> None:
    """A curve that already declares its own physics keeps it."""
    cfg = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        miso_intermediate_gas_offer_margin=True,
        offer_curve_by_group={
            "CT_PEAKER": dict(PARENTS["CT_PEAKER"]),
            "CT_INTERMEDIATE": {
                **INTERMEDIATES["CT_INTERMEDIATE"],
                "phys_econ_low": 0.5,
            },
        },
    )
    out = _with_intermediate_phys(
        cfg.offer_curve_by_group["CT_INTERMEDIATE"], "CT_INTERMEDIATE", cfg
    )
    assert out["phys_econ_low"] == 0.5  # its own, kept
    assert out["phys_econ_high"] == 0.691  # the parent's, borrowed


def test_cache_key_is_registered_dropped_at_default() -> None:
    """Rule 7 [R-PARQUET] caching: adding the field must not orphan every cache.

    The field is registered in ``_CACHE_KEY_OPTIONAL_FIELDS`` so its default is
    dropped from the hash — the repo-wide pinned default key is unmoved — while
    an armed run keys as a distinct scenario.
    """
    assert ScenarioConfig().cache_key() == "4c6b03ae098b6e3e"
    assert (
        ScenarioConfig(miso_intermediate_gas_offer_margin=True).cache_key()
        != ScenarioConfig().cache_key()
    )
