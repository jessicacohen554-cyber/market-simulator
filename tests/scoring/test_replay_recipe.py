"""Tests for scripts/lib/replay_recipe.py: replay must reproduce each year's config."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib.replay_recipe import replay_config_diffs  # noqa: E402


def _bundle(tmp_path: Path, recorded: dict) -> Path:
    (tmp_path / "meta.json").write_text(json.dumps({"iso": "ERCOT", "years": [2025]}))
    (tmp_path / "run_config_2025.json").write_text(
        json.dumps({"scenario_config": recorded})
    )
    return tmp_path


def test_a_faithful_replay_has_no_diffs(tmp_path):
    bundle = _bundle(tmp_path, {"ercot_offer_swcap_clip": False, "voll": 5000.0})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"ercot_offer_swcap_clip": False, "voll": 5000.0},
    )
    assert diffs == {}


def test_a_replay_of_the_wrong_recipe_is_reported(tmp_path):
    bundle = _bundle(tmp_path, {"ercot_offer_swcap_clip": False, "voll": 5000.0})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"ercot_offer_swcap_clip": True, "voll": 9000.0},
    )
    assert diffs == {
        "ercot_offer_swcap_clip": (False, True),
        "voll": (5000.0, 9000.0),
    }


def test_bookkeeping_fields_are_not_recipe(tmp_path):
    bundle = _bundle(tmp_path, {"voll": 5000.0, "_explicitly_set_fields": ["a"]})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"voll": 5000.0, "_explicitly_set_fields": ["b"]},
    )
    assert diffs == {}


def test_a_year_without_a_recorded_config_is_not_checked(tmp_path):
    bundle = _bundle(tmp_path, {"voll": 5000.0})
    called = []
    diffs = replay_config_diffs(
        bundle, 2024, resolve=lambda b, y: called.append(y) or {}
    )
    assert diffs == {} and called == []


def test_value_comparison_is_by_content_not_identity(tmp_path):
    bundle = _bundle(tmp_path, {"offer_curve_by_group": {"CC": {"peak": 4.576}}})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"offer_curve_by_group": {"CC": {"peak": 4.576}}},
    )
    assert diffs == {}


def test_a_stale_inert_rule26_deleted_field_is_not_a_mismatch(tmp_path):
    """A field deleted under rule 26 after the solve, recorded at its inert value."""
    bundle = _bundle(
        tmp_path,
        {"unit_outage_dispatched_bin_live_denominator": False, "voll": 5000.0},
    )
    diffs = replay_config_diffs(bundle, 2025, resolve=lambda b, y: {"voll": 5000.0})
    assert diffs == {}


def test_the_deleted_polarity_in_its_owning_iso_is_still_reported(tmp_path):
    """NWPP recording the deleted (diluted-roster) polarity replays differently."""
    (tmp_path / "meta.json").write_text(json.dumps({"iso": "NWPP", "years": [2025]}))
    (tmp_path / "run_config_2025.json").write_text(
        json.dumps(
            {"scenario_config": {"unit_outage_dispatched_bin_live_denominator": False}}
        )
    )
    diffs = replay_config_diffs(tmp_path, 2025, resolve=lambda b, y: {})
    assert diffs == {"unit_outage_dispatched_bin_live_denominator": (False, None)}


def test_a_field_registered_after_the_solve_at_its_default_is_not_a_mismatch(tmp_path):
    """A field added to ScenarioConfig after the solve is absent from the recording."""
    bundle = _bundle(tmp_path, {"voll": 5000.0})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"voll": 5000.0, "spp_mmu_offer_repair": False},
    )
    assert diffs == {}


def test_a_field_absent_from_the_recording_but_replayed_armed_is_reported(tmp_path):
    """Only the registered default is excused; an armed replay of an absent field is not."""
    bundle = _bundle(tmp_path, {"voll": 5000.0})
    diffs = replay_config_diffs(
        bundle,
        2025,
        resolve=lambda b, y: {"voll": 5000.0, "spp_mmu_offer_repair": True},
    )
    assert diffs == {"spp_mmu_offer_repair": (None, True)}
