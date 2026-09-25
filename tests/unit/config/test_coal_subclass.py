"""COAL-SUB invariants: the bare ``COAL`` class is gone; every coal unit carries its subclass.

Owner instruction 2026-09-25 (verbatim): "we need to completely eliminate the
class Coal From the model altogether all coal should be sorted into its
subclass". These tests pin the invariant at every seam that could re-introduce
it: the taxonomy, the resolver, the generator model, the config and override
channels, the per-unit parameter tables (carried byte-identically to every
subclass), the offer-curve registries, the curated ERCOT bin sheet, and the
legacy-recipe translation.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config import plant_taxonomy as pt
from market_sim.config.plant_taxonomy import (
    COAL_ARTIFACT_FAMILY,
    COAL_CLASSES,
    COAL_CODE_TO_SUPPLY,
    BareCoalClassError,
    artifact_class,
    artifact_class_array,
    classify_plant,
    fold_legacy_coal_key,
)

SUBCLASSES = ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC")


def test_coal_classes_are_exactly_the_four_subclasses():
    """The coal family is the four supply ranks, and no PlantClass is bare COAL."""
    assert set(COAL_CLASSES) == set(SUBCLASSES)
    keys = {c.key for c in pt.PLANT_CLASSES}
    assert "COAL" not in keys
    assert set(pt.classes_for_fuel930("coal")) == set(SUBCLASSES)


@pytest.mark.parametrize("code", sorted(COAL_CODE_TO_SUPPLY))
def test_classify_plant_never_returns_bare_coal(code):
    """Every EIA coal energy-source code classifies to a subclass (benchmark == fleet)."""
    cls = classify_plant(code, "ST", False, 0)
    assert cls in COAL_CLASSES


@pytest.mark.parametrize(
    "code,expected",
    [
        ("BIT", "COAL_BIT"),
        ("ANT", "COAL_BIT"),
        ("RC", "COAL_BIT"),
        ("SC", "COAL_BIT"),
        ("SUB", "COAL_PRB"),
        ("LIG", "COAL_LIGNITE"),
        ("WC", "COAL_WC"),
    ],
)
def test_energy_source_fallback_map(code, expected):
    """The final-fallback map the fleet uses is the benchmark's own fuel-code map."""
    assert pt.coal_code_to_class(code) == expected


def test_artifact_class_folds_only_coal():
    """artifact_class maps each subclass to the family token and nothing else moves."""
    for c in SUBCLASSES:
        assert artifact_class(c) == COAL_ARTIFACT_FAMILY
    for c in ("CC_REGULAR", "ST_GAS", "CT_PEAKER", "", "nuclear"):
        assert artifact_class(c) == c
    out = artifact_class_array(["COAL_PRB", "CC_REGULAR", "COAL_WC"])
    assert list(out) == [COAL_ARTIFACT_FAMILY, "CC_REGULAR", COAL_ARTIFACT_FAMILY]


def test_generator_refuses_bare_coal():
    """No generator can be built carrying the bare COAL class."""
    from pydantic import ValidationError

    from market_sim.data.fleet import Generator

    kw = dict(unit_id="u", name="u", zone="z", fuel_type="coal", pmax_mw=1.0)
    for c in SUBCLASSES:
        assert Generator(**kw, plant_group=c).plant_group == c
    with pytest.raises(ValidationError, match="bare 'COAL' class"):
        Generator(**kw, plant_group="COAL")


def test_coal_subclass_resolver_fallback_and_refusal(monkeypatch):
    """The resolver takes the unit's own energy source last, and never invents a class."""
    from market_sim.data import coal

    monkeypatch.setattr(coal, "_UNIT_ENERGY_SOURCE_COAL_SUPPLY", {})
    unknown = 999_999_001
    assert coal.coal_supply_class(unknown) == ""
    assert coal.coal_subclass(unknown, "SUB") == "COAL_PRB"
    # Plant-grained: a later unit of the same plant with another code keeps
    # the plant's registered subclass (one plant, one subclass).
    assert coal.coal_subclass(unknown, "BIT") == "COAL_PRB"
    with pytest.raises(ValueError, match="NO coal subclass"):
        coal.coal_subclass(999_999_002, "NG")
    # A curated plant is never overridden by the fallback.
    assert coal.coal_subclass(6180, "SUB") == "COAL_LIGNITE"  # Oak Grove: lignite


def test_fold_legacy_coal_key_semantics():
    """COAL reaches only subclasses nothing else covers, then the key is gone."""
    curve = {"COAL": {"peak": 9.0}, "COAL_BIT": {"peak": 1.0}}
    folded = fold_legacy_coal_key(curve)
    assert "COAL" not in folded
    assert folded["COAL_BIT"] == {"peak": 1.0}
    for c in ("COAL_PRB", "COAL_LIGNITE", "COAL_WC"):
        assert folded[c] == {"peak": 9.0}
    covered = fold_legacy_coal_key({"COAL": {"peak": 9.0}}, covered=COAL_CLASSES)
    assert covered == {}
    assert fold_legacy_coal_key({"CC_REGULAR": {}}) == {"CC_REGULAR": {}}


def test_scenario_config_bare_coal_channels():
    """Config refuses COAL, except a recorded curve that also names all four subclasses."""
    from market_sim.config.scenarios import ScenarioConfig

    full = {c: {"peak": float(i)} for i, c in enumerate(SUBCLASSES)}
    cfg = ScenarioConfig(offer_curve_by_group={**full, "COAL": {"peak": 99.0}})
    assert cfg.offer_curve_by_group == full
    with pytest.raises(BareCoalClassError):
        ScenarioConfig(offer_curve_by_group={"COAL": {"peak": 1.0}})
    with pytest.raises(BareCoalClassError):
        ScenarioConfig(wefor_residual_groups=frozenset({"COAL"}))
    with pytest.raises(BareCoalClassError):
        ScenarioConfig(temp_derate_classes=frozenset({"COAL", "ST_GAS"}))
    with pytest.raises(BareCoalClassError):
        ScenarioConfig(econ_split_by_group={"COAL": [0.5]})


def test_offer_curve_override_channels_refuse_bare_coal():
    """The --offer-curve-json / --offer-curve-delta-json merges refuse the key."""
    import importlib

    mod = importlib.import_module("market_sim.pipeline.backcast_config")
    with pytest.raises(BareCoalClassError):
        mod._deep_merge_offer_curve({}, {"COAL": {"peak": 1.0}})
    with pytest.raises(BareCoalClassError):
        mod._apply_offer_curve_deltas(
            {"COAL_BIT": {"peak": 1.0}}, {"COAL": {"peak": 0.1}}
        )


def test_base_offer_curves_carry_every_subclass_and_no_bare_coal():
    """Every registry curve carries no COAL; the generic base covers all four ranks."""
    import importlib

    from market_sim.pipeline.offer_curve_base.generic import GENERIC_BASE_OFFER_CURVE

    mod = importlib.import_module("market_sim.pipeline.backcast_config")
    assert "COAL" not in GENERIC_BASE_OFFER_CURVE
    assert set(SUBCLASSES) <= set(GENERIC_BASE_OFFER_CURVE)
    for name in dir(mod):
        obj = getattr(mod, name)
        if name.endswith("_OFFER_CURVE") and isinstance(obj, dict):
            assert "COAL" not in obj, name


def test_per_unit_tables_carry_identical_values_to_every_subclass():
    """Former COAL-keyed per-unit tables: no COAL key, one identical value per subclass."""
    from market_sim.config.constants import (
        CORRELATED_OUTAGE_CURVE,
        MIN_STABLE_PCT_PHYSICAL,
        THERMAL_AVAILABILITY,
    )
    from market_sim.config.fuel_trajectories import MAINTENANCE_MONTHLY_SHAPE
    from market_sim.data.fleet.campd_bins import (
        _BIN_GROUP_MEASURED_FAMILY,
        _DEFAULT_HR_MULT_BY_GROUP,
        _DEFAULT_TRANCHE_PCT_BY_GROUP,
        _RAMP_BUCKET_BY_GROUP,
    )
    from market_sim.data.fleet.eia860 import (
        BIN_GROUP_HR_DEFAULT,
        BIN_GROUP_TO_FUEL,
        BIN_STARTUP_COST_PER_MW,
    )
    from market_sim.data.fleet.offer_surfaces import _PJM_MIDCURVE_SEGMENT_OF
    from market_sim.data.fleet.withholding import RAMP10_FRAC_BY_GROUP

    tables = {
        "THERMAL_AVAILABILITY": THERMAL_AVAILABILITY,
        "MAINTENANCE_MONTHLY_SHAPE": MAINTENANCE_MONTHLY_SHAPE,
        "MIN_STABLE_PCT_PHYSICAL": MIN_STABLE_PCT_PHYSICAL,
        "CORRELATED_OUTAGE_CURVE[ERCOT][pre]": CORRELATED_OUTAGE_CURVE["ERCOT"]["pre"],
        "CORRELATED_OUTAGE_CURVE[ERCOT][post]": CORRELATED_OUTAGE_CURVE["ERCOT"][
            "post"
        ],
        "_BIN_GROUP_MEASURED_FAMILY": _BIN_GROUP_MEASURED_FAMILY,
        "_DEFAULT_HR_MULT_BY_GROUP": _DEFAULT_HR_MULT_BY_GROUP,
        "_DEFAULT_TRANCHE_PCT_BY_GROUP": _DEFAULT_TRANCHE_PCT_BY_GROUP,
        "_RAMP_BUCKET_BY_GROUP": _RAMP_BUCKET_BY_GROUP,
        "BIN_GROUP_HR_DEFAULT": BIN_GROUP_HR_DEFAULT,
        "BIN_GROUP_TO_FUEL": BIN_GROUP_TO_FUEL,
        "BIN_STARTUP_COST_PER_MW": BIN_STARTUP_COST_PER_MW,
        "_PJM_MIDCURVE_SEGMENT_OF": _PJM_MIDCURVE_SEGMENT_OF,
        "RAMP10_FRAC_BY_GROUP": RAMP10_FRAC_BY_GROUP,
    }
    for name, table in tables.items():
        assert "COAL" not in table, name
        vals = [table[c] for c in SUBCLASSES]
        assert all(v == vals[0] for v in vals), name


def test_ercot_curated_bin_sheet_has_no_bare_coal():
    """The curated ERCOT sheet carries each coal plant's curated subclass."""
    from market_sim.config.paths import CAMPD_BINS_CSV
    from market_sim.data.coal import COAL_PLANT_SUPPLY

    if not CAMPD_BINS_CSV.exists():
        pytest.skip("curated bin sheet not hydrated")
    df = pd.read_csv(CAMPD_BINS_CSV, usecols=["Plant_Group", "Plant_Code"])
    assert "COAL" not in set(df["Plant_Group"])
    coal = df[df["Plant_Group"].isin(SUBCLASSES)]
    assert len(coal) == 10
    for code, grp in zip(coal["Plant_Code"], coal["Plant_Group"]):
        assert grp == pt.COAL_SUPPLY_TO_CLASS[COAL_PLANT_SUPPLY[int(code)]]


def test_replay_keeper_translates_legacy_coal_keys():
    """A pre-COAL-SUB recipe's COAL keys are folded, never passed to a refusing channel."""
    from scripts.replay_keeper import translate_legacy_coal_keys

    full = {c: {"peak": 1.0} for c in SUBCLASSES}
    kwargs = {
        "offer_curve_overrides": {**full, "COAL": {"peak": 7.0}},
        "prb_overrides": {
            "offer_curve_by_group": {"COAL": {"peak": 5.0}, "COAL_BIT": {}}
        },
    }
    translate_legacy_coal_keys(kwargs)
    assert kwargs["offer_curve_overrides"] == full
    curve = kwargs["prb_overrides"]["offer_curve_by_group"]
    assert "COAL" not in curve and curve["COAL_BIT"] == {}
    assert curve["COAL_PRB"] == {"peak": 5.0}
