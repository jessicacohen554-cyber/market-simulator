"""The armed-mechanism / missing-input guard (caiso-157, widened at caiso-190).

Trivial case first: a config with everything at its default must never raise,
whatever is on disk. Then each armed flag against an EMPTY tmp CLEAN_DIR (the
degraded state caiso-157 found in the CAISO keeper lineage) and against a
partition that exists.

caiso-190 adds the severity axis below the original cases: a mechanism with no
declared fallback is fatal on every lane, one with a declared fallback is fatal
only in **strict** mode (the calibration lane keepers are promoted from), and a
probe that RAISES is treated as degraded rather than healthy. The fixtures also
moved to ``write_clean`` — written as bare parquet they had no embedded
datatype metadata, so both probes raised ``SchemaError``, the guard swallowed
it, and ``test_present_partitions_pass`` passed without ever reading a
partition.
"""

from __future__ import annotations

import dataclasses
import logging

import pandas as pd
import pytest

from market_sim.data import capacity_deliverability as capdel
from market_sim.data.input_completeness import (
    DegradedInputError,
    check_clean_partitions,
)


class _Config:
    """Minimal stand-in for the ScenarioConfig fields the guard reads."""

    def __init__(self, **flags):
        self.capacity_deliverability_limits = flags.get(
            "capacity_deliverability_limits", False
        )
        self.hydro_ror_split = flags.get("hydro_ror_split", False)
        self.outage_source = flags.get("outage_source", "statistical")
        self.coal_fuel_inventory = flags.get("coal_fuel_inventory", False)


@pytest.fixture()
def empty_clean(tmp_path, monkeypatch):
    """Point ``paths.CLEAN_DIR`` at an empty tmp tree (a fresh container)."""
    from scripts.lib import clean_io

    clean = tmp_path / "clean"
    clean.mkdir()
    monkeypatch.setattr(clean_io.paths, "CLEAN_DIR", clean)
    return clean


def _write_capdel(clean, iso="CAISO"):
    """Write a one-row capacity-deliverability partition for ``iso``.

    Through ``write_clean`` (caiso-190). These fixtures previously wrote a
    bare ``to_parquet``, which the reader rejects for having no embedded
    ``market_sim.datatype`` metadata — so the probes raised ``SchemaError``,
    the guard swallowed it, and ``test_present_partitions_pass`` passed
    without ever reading a partition. The partition-present leg was therefore
    untested, and a malformed partition was silently tolerated on the solve
    path; both are fixed here.
    """
    from scripts.lib.clean_io import write_clean

    df = pd.DataFrame(
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
    )
    df["value_mw"] = df["value_mw"].astype("float64")
    df["value_pu"] = df["value_pu"].astype("float64")
    write_clean(df, "capacity-deliverability", iso=iso)


def _write_hydro_modes(clean, iso="CAISO"):
    """Write a one-row hydro-plant-modes partition for ``iso``."""
    from scripts.lib.clean_io import write_clean

    df = pd.DataFrame(
        [
            {
                "iso": iso,
                "plant_id": 1,
                "eha_ptid": "1",
                "plant_name": "fixture",
                "ch_mw": 10.0,
                "mode": "Peaking",
                "shapeable": True,
                "method": "eha_mode",
            }
        ]
    )
    df["plant_id"] = df["plant_id"].astype("int64")
    df["ch_mw"] = df["ch_mw"].astype("float64")
    df["shapeable"] = df["shapeable"].astype("bool")
    write_clean(df, "hydro-plant-modes", iso=iso)


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


# ---------------------------------------------------------------------------
# caiso-190: per-requirement severity, and the strict/non-strict lane split
# ---------------------------------------------------------------------------
# A mechanism with NO declared fallback is fatal everywhere; one WITH a
# declared fallback is fatal only on the lane keepers are promoted from. The
# asymmetry exists because a forecast run that degrades to a declared fallback
# is recoverable from run_config.json's resolved_inputs block, whereas a
# KEEPER that did so is the caiso-188 defect — it ships a bundle advertising a
# mechanism its LP never ran.


def test_strict_is_the_default(empty_clean):
    """Fail-closed: a caller must opt OUT of strictness deliberately."""
    with pytest.raises(DegradedInputError):
        check_clean_partitions(_Config(capacity_deliverability_limits=True), "CAISO")


def test_declared_fallback_warns_instead_of_raising_when_not_strict(
    empty_clean, caplog
):
    """capacity_deliverability_limits has a declared fallback -> WARN + record."""
    with caplog.at_level(logging.WARNING, logger="market_sim.data.input_completeness"):
        check_clean_partitions(
            _Config(capacity_deliverability_limits=True), "CAISO", strict=False
        )
    message = caplog.text
    assert "capacity_deliverability_limits" in message
    assert "ARMED" in message
    assert "curate_capacity_deliverability.py" in message
    # The warning must name what the LP will actually solve against.
    assert "fitted scalar" in message


def test_no_fallback_mechanism_raises_even_when_not_strict(empty_clean):
    """hydro_ror_split has NO fallback — the classifier IS the mechanism."""
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(hydro_ror_split=True), "CAISO", strict=False)
    assert "NO fallback" in str(excinfo.value)


def test_strict_names_the_lane_in_the_failure(empty_clean):
    """A strict-only failure explains why it is fatal here and not elsewhere."""
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(
            _Config(capacity_deliverability_limits=True), "CAISO", strict=True
        )
    assert "STRICT mode" in str(excinfo.value)


def test_campd_extract_is_registered(empty_clean, monkeypatch, tmp_path):
    """The third requirement: the measured CAMPD unit-outage overlay.

    ``outage_source`` is a STRING axis, so this entry exercises the registry's
    per-requirement ``armed`` callable rather than flag truthiness.
    """
    from market_sim.data import outages

    missing = tmp_path / "nonexistent-campd.csv"
    monkeypatch.setattr(outages, "unit_outage_csv_for_iso", lambda iso: missing)

    # Not armed (the default statistical source) -> never reached.
    check_clean_partitions(_Config(), "CAISO", strict=True)

    # Armed + absent -> fatal on the calibration lane...
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(outage_source="historic"), "CAISO", strict=True)
    assert "outage_source" in str(excinfo.value)
    assert "derive_campd_unit_outages.py" in str(excinfo.value)

    # ...and a loud warning on the forecast lane (declared fallback).
    check_clean_partitions(_Config(outage_source="historic"), "CAISO", strict=False)


def test_unreadable_partition_is_degraded_not_healthy(empty_clean, monkeypatch):
    """caiso-190: a probe that RAISES is not evidence of health.

    A partition that exists but cannot be parsed no-ops the mechanism exactly
    as an absent one does. Before this, the probe's exception was swallowed
    and the solve proceeded — the same silent-no-op class the guard exists to
    kill, and the reason this module's own partition-present test passed while
    both its fixtures raised SchemaError.
    """
    import market_sim.data.input_completeness as ic

    def _boom(iso):
        raise RuntimeError("truncated parquet")

    monkeypatch.setattr(ic, "_hydro_plant_modes_absent", _boom)
    monkeypatch.setattr(
        ic,
        "_PARTITION_REQUIREMENTS",
        tuple(
            (
                req
                if req.flag != "hydro_ror_split"
                else dataclasses.replace(req, absent=_boom)
            )
            for req in ic._PARTITION_REQUIREMENTS
        ),
    )

    # Strict (the calibration lane) fails closed on an unverifiable input.
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(hydro_ror_split=True), "CAISO", strict=True)
    assert "UNREADABLE" in str(excinfo.value)

    # Non-strict stays loud but survives.
    check_clean_partitions(_Config(hydro_ror_split=True), "CAISO", strict=False)


def test_coal_fuel_inventory_is_registered(empty_clean, monkeypatch):
    """The fourth requirement: MISO's coal fuel-inventory monthly budget.

    miso-263. ``build_coal_fuel_budget`` returns ``None`` when EITHER of its
    two clean partitions resolves empty, appending zero budget rows and
    leaving coal with floors and no ceiling — so the mechanism has NO
    fallback and is fatal in every mode, the ``hydro_ror_split`` severity
    class. The keeper ``2026-09-19-miso-262-cold-year`` was promoted out of
    exactly this state: six shard containers with a hydrated ``data/raw`` and
    no curated coal partitions, each recording ``coal_fuel_inventory: true``
    and solving without the row.
    """
    from market_sim.data import coal_receipts, coal_stocks

    # Not armed -> never reached, even on a fresh container's empty tree.
    check_clean_partitions(_Config(), "MISO", strict=True)

    # Armed + absent -> fatal, and the message hands back both curate commands.
    with pytest.raises(DegradedInputError) as excinfo:
        check_clean_partitions(_Config(coal_fuel_inventory=True), "MISO", strict=True)
    message = str(excinfo.value)
    assert "coal_fuel_inventory" in message
    assert "curate_coal_stocks.py" in message
    assert "curate_coal_receipts.py" in message

    # No declared fallback, so a non-strict lane is fatal too.
    with pytest.raises(DegradedInputError):
        check_clean_partitions(_Config(coal_fuel_inventory=True), "MISO", strict=False)

    # EITHER half missing is the degraded state, not both-and.
    monkeypatch.setattr(
        coal_stocks, "load_coal_stocks", lambda *a, **k: pd.DataFrame({"x": [1]})
    )
    with pytest.raises(DegradedInputError):
        check_clean_partitions(_Config(coal_fuel_inventory=True), "MISO", strict=True)

    # Both present -> the guard passes.
    monkeypatch.setattr(
        coal_receipts, "load_coal_receipts", lambda *a, **k: pd.DataFrame({"x": [1]})
    )
    check_clean_partitions(_Config(coal_fuel_inventory=True), "MISO", strict=True)
