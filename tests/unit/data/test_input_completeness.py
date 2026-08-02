"""The armed-mechanism / missing-CLEAN-partition guard (caiso-157).

Trivial case first: a config with everything at its default must never raise,
whatever is on disk. Then each armed flag against an EMPTY tmp CLEAN_DIR (the
degraded state caiso-157 found in the CAISO keeper lineage) and against a
partition that exists.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.data import capacity_deliverability as capdel
from market_sim.data.input_completeness import (
    DegradedInputError,
    check_clean_partitions,
)


class _Config:
    """Minimal stand-in for the two ScenarioConfig fields the guard reads."""

    def __init__(self, **flags):
        self.capacity_deliverability_limits = flags.get(
            "capacity_deliverability_limits", False
        )
        self.hydro_ror_split = flags.get("hydro_ror_split", False)


@pytest.fixture()
def empty_clean(tmp_path, monkeypatch):
    """Point ``paths.CLEAN_DIR`` at an empty tmp tree (a fresh container)."""
    from scripts.lib import clean_io

    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.setattr(clean_io.paths, "CLEAN_DIR", clean)
    return clean


def _write_capdel(clean, iso="CAISO"):
    """Write a one-row capacity-deliverability partition for ``iso``."""
    part = clean / "capacity-deliverability" / iso
    part.mkdir(parents=True)
    pd.DataFrame(
        [
            {
                "iso": iso,
                "area": "COTP",
                "area_type": "branch_group",
                "delivery_year": "2023",
                "season": "annual",
                "metric": "import_limit",
                "value_mw": 30.0,
                "value_pu": None,
                "source_doc": "test",
                "source_page": "1",
            }
        ]
    ).to_parquet(part / "capacity-deliverability.parquet")


def _write_hydro_modes(clean, iso="CAISO"):
    """Write a one-row hydro-plant-modes partition for ``iso``."""
    part = clean / "hydro-plant-modes" / iso
    part.mkdir(parents=True)
    pd.DataFrame([{"iso": iso, "plant_id": 1, "shapeable": True}]).to_parquet(
        part / "hydro-plant-modes.parquet"
    )


def test_all_defaults_never_raise(empty_clean):
    """Nothing armed -> the guard is a no-op even with an empty clean tree."""
    check_clean_partitions(_Config(), "CAISO")


def test_armed_deliverability_without_partition_raises(empty_clean):
    """The caiso-157 defect: armed Part A with no curated partition."""
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(capacity_deliverability_limits=True), "CAISO")
    message = str(excinfo.value)
    assert "capacity_deliverability_limits" in message
    assert "curate_capacity_deliverability.py" in message


def test_armed_ror_split_without_partition_raises(empty_clean):
    """The other half: armed RoR split with no classifier."""
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(hydro_ror_split=True), "CAISO")
    assert "curate_hydro_plant_modes.py" in str(excinfo.value)


def test_both_armed_reports_both(empty_clean):
    """One raise names every offender, so the fix is one round trip."""
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(
            _Config(capacity_deliverability_limits=True, hydro_ror_split=True),
            "CAISO",
        )
    message = str(excinfo.value)
    assert "capacity_deliverability_limits" in message
    assert "hydro_ror_split" in message


def test_present_partitions_pass(empty_clean):
    """With both partitions curated the guard passes silently."""
    _write_capdel(empty_clean)
    _write_hydro_modes(empty_clean)
    check_clean_partitions(
        _Config(capacity_deliverability_limits=True, hydro_ror_split=True), "CAISO"
    )


def test_energy_only_iso_is_not_degraded(empty_clean):
    """ERCOT publishes no locational RA construct — empty is the right answer.

    Arming the flag there is inert by design, not a missing-data condition, so
    the guard must not fire (it would break an unrelated ERCOT lane).
    """
    assert capdel.partition_expected("ERCOT") is False
    assert capdel.partition_available("ERCOT") is None
    check_clean_partitions(_Config(capacity_deliverability_limits=True), "ERCOT")


def test_neiso_alias_resolves_to_isone(empty_clean):
    """The model says NEISO, the clean tree says ISONE — the guard follows."""
    assert capdel.partition_expected("NEISO") is True
    with pytest.raises(DegradedInputError):
        check_clean_partitions(_Config(capacity_deliverability_limits=True), "NEISO")
    _write_capdel(empty_clean, iso="ISONE")
    check_clean_partitions(_Config(capacity_deliverability_limits=True), "NEISO")
