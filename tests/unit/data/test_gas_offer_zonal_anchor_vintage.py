"""``gas_offer_margin_zonal_anchor_vintage`` — the (zone, year) identification point.

nyiso-230. The gate resolves ``gas_offer_margin_anchor_by_zone`` on the SOLVE
YEAR instead of on the frozen 2023-2025 training window. These tests pin the
three things that make it a rule-21 ``[R-DOF]`` zero-parameter construction
rather than a new number:

* **the identity** — averaging the runtime resolution over the training window
  reproduces the registered ``GAS_OFFER_MARGIN_ANCHOR_BY_ZONE`` table, so the
  runtime and the frozen derive cannot drift apart silently;
* **the defect is real** — the per-year anchors differ materially from the
  frozen means, which is the whole reason the gate exists;
* **the off path is byte-inert** and the cache key is stable at the declared
  default, so no pinned key of any ISO moves.

Plus the PLUMBING test: the kwarg must reach BOTH runners. A field threaded
into ``run_calibration_full`` but not into ``scripts/run_calibration.run_year``
is the nyiso-229 failure mode — two shard containers died on that exact
``TypeError``, and the precedent field's own comment says why it matters
("an override missing here would solve the control twice").
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "data"))

from market_sim.config.constants import (  # noqa: E402
    GAS_OFFER_MARGIN_ANCHOR_BY_ZONE,
    HOURS_PER_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fuel.zonal_anchor import (  # noqa: E402
    CAPACITY_WEIGHTED_ZONAL_ISOS,
    zonal_gas_anchors_for_year,
)

#: The registered table is stored to 4 dp, so the identity can only be checked
#: to half of that. Nothing here is tuned to the tolerance — it IS the
#: constants' own precision.
REGISTERED_DP_TOL = 5e-5


def _derive_base(iso: str):
    """The frozen derive's own base config, so both sides share a series."""
    from derive_gas_offer_margin_anchor import GAS_SERIES_FLAGS

    return ScenarioConfig(
        iso=iso, mode="backcast", hours=HOURS_PER_YEAR, **GAS_SERIES_FLAGS[iso]
    )


def _per_year_anchors(iso: str) -> dict[int, dict[str, float]]:
    from derive_gas_offer_margin_anchor import TRAIN_WINDOW_HH

    base = _derive_base(iso)
    return {
        yr: zonal_gas_anchors_for_year(
            base.with_overrides(gas_price_override=hh), yr, HOURS_PER_YEAR
        )
        for yr, hh in sorted(TRAIN_WINDOW_HH.items())
    }


# --------------------------------------------------------------------------
# 1. THE IDENTITY — the runtime resolution and the frozen derive agree
# --------------------------------------------------------------------------


def test_training_window_mean_reproduces_the_registered_zone_table():
    """mean over 2023-2025 of the per-year anchors == the registered table."""
    per = _per_year_anchors("NYISO")
    registered = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]
    assert set(per[2024]) >= set(registered), "a registered zone went missing"
    for zone, reg in registered.items():
        mean = float(np.mean([per[y][zone] for y in sorted(per)]))
        assert mean == pytest.approx(reg, abs=REGISTERED_DP_TOL), (
            f"{zone}: runtime window mean {mean:.6f} != registered {reg} — the "
            "runtime resolution has drifted from the frozen derive"
        )


def test_reference_zone_window_mean_is_the_iso_anchor():
    """NYISO's applier leaves the reference zone unshifted, so it IS the ISO anchor."""
    from market_sim.config.constants import GAS_OFFER_MARGIN_ANCHOR_BY_ISO

    per = _per_year_anchors("NYISO")
    ref_mean = float(np.mean([per[y]["Capital_Hudson"] for y in sorted(per)]))
    assert ref_mean == pytest.approx(
        GAS_OFFER_MARGIN_ANCHOR_BY_ISO["NYISO"], abs=REGISTERED_DP_TOL
    )


# --------------------------------------------------------------------------
# 2. THE DEFECT IS REAL — per-year anchors are not the window mean
# --------------------------------------------------------------------------


def test_per_year_anchors_depart_materially_from_the_frozen_window_mean():
    """If the years agreed with the window mean the gate would be pointless."""
    per = _per_year_anchors("NYISO")
    registered = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]
    worst = max(abs(per[y][z] - registered[z]) for y in per for z in registered)
    # NYISO's 2025 delivered gas sits ~1.66 $/MMBtu above the window mean; the
    # bar is deliberately far below that so the test states "materially
    # non-zero", not a fitted threshold.
    assert worst > 0.5, (
        f"largest per-year departure from the frozen anchor is only {worst:.4f} "
        "$/MMBtu — the gate would be inert and this test is the wrong guard"
    )


def test_the_departure_is_two_sided_across_the_window():
    """Some years sit above the frozen anchor and some below, by construction."""
    per = _per_year_anchors("NYISO")
    ref = [per[y]["Capital_Hudson"] for y in sorted(per)]
    anchor = GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]["Capital_Hudson"]
    assert min(ref) < anchor < max(ref)


# --------------------------------------------------------------------------
# 3. THE RESOLVER'S OWN GUARDS
# --------------------------------------------------------------------------


def test_one_entry_per_zone_in_iso_zone_order():
    from market_sim.config.iso_configs import get_iso_config

    got = zonal_gas_anchors_for_year(_derive_base("NYISO"), 2024, HOURS_PER_YEAR)
    assert list(got) == list(get_iso_config("NYISO").zone_names)
    assert all(np.isfinite(v) and v > 0 for v in got.values())


@pytest.mark.parametrize("iso", sorted(CAPACITY_WEIGHTED_ZONAL_ISOS))
def test_capacity_weighted_isos_are_refused_not_mis_measured(iso):
    """A synthetic one-row-per-zone probe cannot measure a cap-weighted applier."""
    cfg = ScenarioConfig(iso=iso, mode="backcast", hours=HOURS_PER_YEAR)
    with pytest.raises(ValueError, match="(?i)capacity"):
        zonal_gas_anchors_for_year(cfg, 2024, HOURS_PER_YEAR)


def test_iso_without_a_zonal_applier_is_refused():
    cfg = ScenarioConfig(iso="NEISO", mode="backcast", hours=HOURS_PER_YEAR)
    with pytest.raises(ValueError, match="no per-zone delivered-gas basis"):
        zonal_gas_anchors_for_year(cfg, 2024, HOURS_PER_YEAR)


# --------------------------------------------------------------------------
# 4. REGISTRATION: default off, byte-inert off, keys distinctly on
# --------------------------------------------------------------------------


def test_field_defaults_off():
    assert ScenarioConfig(iso="NYISO").gas_offer_margin_zonal_anchor_vintage is False


def test_cache_key_is_dropped_at_the_declared_default_and_moves_when_armed():
    from market_sim.config.scenarios import (
        _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
        _CACHE_KEY_OPTIONAL_FIELDS,
    )

    name = "gas_offer_margin_zonal_anchor_vintage"
    assert name in _CACHE_KEY_OPTIONAL_FIELDS
    assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[name] == "False"
    base = ScenarioConfig(iso="NYISO", mode="backcast", hours=HOURS_PER_YEAR)
    explicit_off = base.with_overrides(gas_offer_margin_zonal_anchor_vintage=False)
    armed = base.with_overrides(gas_offer_margin_zonal_anchor_vintage=True)
    assert explicit_off.cache_key() == base.cache_key()
    assert armed.cache_key() != base.cache_key()


# --------------------------------------------------------------------------
# 5. PLUMBING — the nyiso-229 TypeError, guarded
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "module_path,func_name",
    [
        ("scripts/run_calibration.py", "run_year"),
        ("scripts/run_calibration_full.py", "solve_and_persist"),
    ],
)
def test_the_kwarg_reaches_both_runners(module_path, func_name):
    """A field in one runner but not the other is the nyiso-229 shard killer."""
    import importlib.util

    name = module_path.replace("/", ".").removesuffix(".py")
    spec = importlib.util.spec_from_file_location(name, ROOT / module_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    params = inspect.signature(getattr(mod, func_name)).parameters
    assert "gas_offer_margin_zonal_anchor_vintage" in params, (
        f"{module_path}::{func_name} does not accept the kwarg — an armed run "
        "would raise TypeError, or worse, silently solve the control twice"
    )
    assert params["gas_offer_margin_zonal_anchor_vintage"].default is False


@pytest.mark.parametrize(
    "module_path,marker",
    [
        ("scripts/run_calibration.py", "config"),
        # nyiso-231: the recorded half moved out of an inline `recorded_cfg`
        # block and into the shared `mirror_solve_year_gas_anchors` helper,
        # fused to `_recorded_config`'s return, because the inline block
        # resolved BEFORE `gas_hub_basis_overlay` was on the config and so
        # recorded an anchor the LP never priced. The field-route duty this
        # test pins is unchanged; only the parameter it reads is now `cfg`.
        # Ordering itself is pinned by
        # tests/unit/data/test_recorded_config_gas_anchor_mirror.py.
        ("scripts/run_calibration_full.py", "cfg"),
    ],
)
def test_the_config_field_route_is_honoured_not_only_the_kwarg(module_path, marker):
    """``replay_keeper.py --set`` writes the CONFIG field, never the solve kwarg.

    Gating the resolution on the kwarg alone would let an A/B probe launched
    through ``--set`` silently solve the CONTROL while recording an armed
    config — the nyiso-229 failure mode one layer over, and undetectable from
    the bundle. The field is also in ``_CACHE_KEY_OPTIONAL_FIELDS``, so a config
    carrying it True MUST resolve or the cache key claims a resolution the solve
    never performed (rule 24 ``[R-REGISTRY]``).
    """
    src = (ROOT / module_path).read_text()
    needle = (
        "if gas_offer_margin_zonal_anchor_vintage or getattr(\n"
        f'        {marker}, "gas_offer_margin_zonal_anchor_vintage", False\n'
    )
    assert needle.strip() in " ".join(src.split()).replace("  ", " ") or (
        f'getattr(\n        {marker}, "gas_offer_margin_zonal_anchor_vintage"' in src
        or f'{marker}, "gas_offer_margin_zonal_anchor_vintage", False' in src
    ), (
        f"{module_path} gates the vintage resolution on the kwarg alone — a "
        "--set probe would solve the control and record an armed config"
    )
