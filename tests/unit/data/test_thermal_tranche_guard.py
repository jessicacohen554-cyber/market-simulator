"""Tests for the thermal-tranche arm-over-gap guard (xiso-6).

``campd_bins.assert_thermal_tranche_coverage`` fails loudly when a running
config ARMS a per-plant tranche mechanism over an artifact vintage gap — a
column absent from ``thermal_tranches_<ISO>.csv``, or blank ``status="ok"``
rows in the mechanism's target groups — instead of letting the loaders skip
the rows silently and the mechanism read as inert on the merits
(FINDING-xiso5-thermal-tranche-coverage-2026-08-04.md §4.3).

Trivial synthetic artifacts first (one plant, one group — the testing
pattern), then the committed five artifacts against each ISO's designated
keeper gates: the guard must be a measured no-op at every current keeper, and
must fire on exactly the latent arm-over-gap states the xiso-5 census
enumerated (CAISO ``cc_mustrun_per_plant``, PJM ``chp_steam_floor_p25``, …).
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

import market_sim.data.fleet.campd_bins as cb
from market_sim.data.fleet.campd_bins import assert_thermal_tranche_coverage
from tests.helpers import REPO_ROOT

KEEPER_DIR = REPO_ROOT / "frontend" / "data" / "backcast" / "keepers"
REGISTRY = REPO_ROOT / "frontend" / "data" / "backcast" / "registry"
TRANCHES = REPO_ROOT / "data" / "raw" / "_processed-legacy"

ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

# Every ScenarioConfig gate the guard covers (mirrors _TRANCHE_GATE_COLUMNS).
GATES = tuple(g for g, _, _ in cb._TRANCHE_GATE_COLUMNS)


class _Cfg:
    """Minimal config stub: attributes are gate flags, absent -> False."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _write_artifact(directory, iso: str, rows: list[dict]) -> None:
    """Write a synthetic thermal_tranches_<ISO>.csv from row dicts."""
    pd.DataFrame(rows).to_csv(directory / f"thermal_tranches_{iso}.csv", index=False)


def _row(code=1, group="ST_GAS", status="ok", **cols) -> dict:
    base = {"plant_code": code, "plant_group": group, "name": "P", "status": status}
    base.update(cols)
    return base


@pytest.fixture()
def tranche_dir(tmp_path, monkeypatch):
    """Redirect campd_bins.PROCESSED_DIR to an empty temp artifact store."""
    monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
    return tmp_path


class TestSyntheticTrivial:
    """One plant, one group — the guard's core decision table."""

    def test_unarmed_never_fires(self, tranche_dir):
        _write_artifact(tranche_dir, "MISO", [_row(online_frac=None)])
        assert_thermal_tranche_coverage("MISO", _Cfg())  # no raise

    def test_armed_over_blank_ok_row_fires(self, tranche_dir):
        _write_artifact(tranche_dir, "MISO", [_row(online_frac=None)])
        with pytest.raises(ValueError, match="ST_GAS.*1 of 1.*BLANK"):
            assert_thermal_tranche_coverage("MISO", _Cfg(st_gas_mustrun_per_plant=True))

    def test_armed_over_populated_row_passes(self, tranche_dir):
        _write_artifact(tranche_dir, "MISO", [_row(online_frac=0.98)])
        assert_thermal_tranche_coverage("MISO", _Cfg(st_gas_mustrun_per_plant=True))

    def test_armed_over_absent_column_fires(self, tranche_dir):
        _write_artifact(tranche_dir, "MISO", [_row(committed_pct=30.0)])
        with pytest.raises(ValueError, match="COLUMN ABSENT"):
            assert_thermal_tranche_coverage("MISO", _Cfg(st_gas_mustrun_per_plant=True))

    def test_missing_artifact_armed_fires(self, tranche_dir):
        with pytest.raises(ValueError, match="no per-plant tranche artifact"):
            assert_thermal_tranche_coverage("MISO", _Cfg(cc_mustrun_per_plant=True))

    def test_missing_artifact_unarmed_passes(self, tranche_dir):
        assert_thermal_tranche_coverage("MISO", _Cfg())

    def test_non_ok_rows_never_counted(self, tranche_dir):
        # A rarely_online / eia923_cf row with a blank cell is the deriver's
        # own skip, not a vintage gap.
        _write_artifact(
            tranche_dir,
            "MISO",
            [
                _row(status="rarely_online", online_frac=None),
                _row(code=2, status="eia923_cf", online_frac=None),
            ],
        )
        assert_thermal_tranche_coverage("MISO", _Cfg(st_gas_mustrun_per_plant=True))

    def test_absent_target_group_passes(self, tranche_dir):
        # No COAL rows at all: the class is absent from the ISO, so an armed
        # coal gate engages on nothing LEGITIMATELY (self-targeting design).
        _write_artifact(tranche_dir, "NYISO", [_row(group="CC_REGULAR")])
        assert_thermal_tranche_coverage("NYISO", _Cfg(coal_mustrun_online_pmin=True))

    def test_chp_blanks_by_design_never_fire(self, tranche_dir):
        # CHP groups blank in online_frac are BY DESIGN (their floor is the
        # steam host, rule 19) — unreachable by every online_frac gate.
        _write_artifact(
            tranche_dir,
            "CAISO",
            [
                _row(group="CT_CHP", online_frac=None, steam_level_cf=40.0),
                _row(code=2, group="CC_REGULAR", online_frac=0.5),
            ],
        )
        assert_thermal_tranche_coverage(
            "CAISO",
            _Cfg(cc_mustrun_per_plant=True, chp_steam_floor_p25=True),
        )

    def test_coal_sync_alone_is_inert_not_a_gap(self, tranche_dir):
        # The sync split engages only under coal_mustrun_online_pmin (the
        # assembly consumer's own conjunction) — armed alone, no fire.
        _write_artifact(tranche_dir, "PJM", [_row(group="COAL", online_frac=None)])
        assert_thermal_tranche_coverage("PJM", _Cfg(coal_sync_srmc_tranche=True))
        with pytest.raises(ValueError, match="coal_sync_srmc_tranche"):
            assert_thermal_tranche_coverage(
                "PJM",
                _Cfg(coal_sync_srmc_tranche=True, coal_mustrun_online_pmin=True),
            )

    def test_steam_level_falls_back_to_p25_allhr(self, tranche_dir):
        # Pre-WP-3 artifacts carry p25_allhr_cf; the loader reads it, so a
        # populated fallback column is NOT a gap.
        _write_artifact(tranche_dir, "CAISO", [_row(group="CT_CHP", p25_allhr_cf=12.0)])
        assert_thermal_tranche_coverage("CAISO", _Cfg(chp_steam_floor_p25=True))

    def test_empty_string_counts_as_blank(self, tranche_dir):
        # The deriver writes "" (not NaN) for suppressed cells in-memory;
        # read back it is NaN, but guard both representations.
        _write_artifact(tranche_dir, "MISO", [_row(online_frac="")])
        with pytest.raises(ValueError, match="BLANK"):
            assert_thermal_tranche_coverage("MISO", _Cfg(st_gas_mustrun_per_plant=True))


def _keeper_gate_stub(iso: str) -> _Cfg:
    """Build a config stub carrying the ISO's designated keeper's gate flags."""
    keeper = json.loads((KEEPER_DIR / f"{iso}.json").read_text())["keeper"]
    reg = json.loads((REGISTRY / f"{keeper}.json").read_text())
    cfg = json.loads((REPO_ROOT / reg["bundle"] / "run_config.json").read_text())
    merged = {**cfg.get("calibration_flags", {}), **cfg.get("scenario_config", {})}
    return _Cfg(**{g: bool(merged.get(g, False)) for g in GATES})


@pytest.mark.integration
@pytest.mark.fulldata
class TestCommittedArtifacts:
    """The guard against the five committed artifacts and the six keepers."""

    def test_no_op_at_every_current_keeper(self):
        # xiso-5 §4.3(i) measured zero silent no-ops at the keepers; the
        # guard must therefore pass every keeper's own armed-gate state.
        for iso in ISOS:
            assert_thermal_tranche_coverage(iso, _keeper_gate_stub(iso))

    def test_caiso_cc_mustrun_trap_fires(self):
        # The census's canonical latent trap: CAISO's committed artifact has
        # online_frac all-null (70 blank ok rows), so arming the CC floor
        # there must be a hard error, never a silent inert mechanism.
        with pytest.raises(ValueError, match="CC_REGULAR.*23.*BLANK"):
            assert_thermal_tranche_coverage("CAISO", _Cfg(cc_mustrun_per_plant=True))

    def test_pjm_st_gas_vintage_trap_fires(self):
        # PJM ST_GAS 0/10 (pre-2026-07-12 vintage, xiso-5 §3).
        with pytest.raises(ValueError, match="ST_GAS.*10.*BLANK"):
            assert_thermal_tranche_coverage("PJM", _Cfg(st_gas_mustrun_per_plant=True))

    def test_nyiso_neiso_column_absent_fires(self):
        for iso in ("NYISO", "NEISO"):
            with pytest.raises(ValueError, match="COLUMN ABSENT"):
                assert_thermal_tranche_coverage(iso, _Cfg(cc_mustrun_per_plant=True))

    def test_miso_control_arm_passes_all_gates(self):
        # MISO is the census's clean control: every emitting-group ok row
        # publishes a value, so even the full gate set passes.
        assert_thermal_tranche_coverage(
            "MISO",
            _Cfg(
                cc_mustrun_per_plant=True,
                st_gas_mustrun_per_plant=True,
                st_gas_mustrun_p25_level=True,
                coal_mustrun_online_pmin=True,
                coal_sync_srmc_tranche=True,
                cc_peaking_per_plant=True,
            ),
        )
