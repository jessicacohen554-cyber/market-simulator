"""Guards on the SOCO gas-steam CAMPAIGN commitment artifact and its seam.

The mechanism (``ScenarioConfig.soco_gas_st_campaign_commitment``, lane
SOCO-53d) reads per-plant MEASURED level/horizon/membership from
``data/raw/_processed-legacy/campd_gas_st_campaign_params_<ISO>.csv``. Three
properties have to hold or the mechanism is not what its declaration says:

1. the loader applies ONLY ``flag == "ok"`` rows, so the derive's ex-ante
   campaign-duty gate cannot be bypassed on the consumer side (rule 23
   ``[R-FROZEN-DERIVE]``);
2. the committed SOCO artifact reproduces the numbers the PRECOMMIT declared
   before the solve, so a silent re-derive cannot move the arm; and
3. the P1 prep hook is ISO-exclusive and default-off, so every other ISO and
   every control run is byte-identical (rule 25 ``[R-ISO-SCOPE]``).
"""

from __future__ import annotations

import csv

import pytest

from market_sim.config.paths import PROCESSED_DIR
from market_sim.data.gas_st_campaign import load_gas_st_campaign_params
from market_sim.pipeline.commitment import build_soco_gas_st_campaign_p1_prep

ARTIFACT = PROCESSED_DIR / "campd_gas_st_campaign_params_SOCO.csv"

#: The values PRECOMMIT-soco-53d-2026-09-19 §3 declared BEFORE the solve:
#: ``plant_code -> (min_load_frac, min_run_hours)``.
DECLARED: dict[int, tuple[float, int]] = {
    26: (0.0657, 64),
    2049: (0.1000, 76),
    728: (0.0829, 192),
    10: (0.1365, 132),
}

#: Barry (3) is measured synchronized 6.3 % of the year — standby iron, not
#: campaign iron — and is the one plant the derive's membership gate refuses.
EXCLUDED_PLANT: int = 3


def _rows() -> list[dict]:
    with ARTIFACT.open(newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.mark.skipif(not ARTIFACT.exists(), reason="SOCO artifact not hydrated")
def test_committed_artifact_reproduces_the_declared_parameters() -> None:
    """The arm's level and horizon are the ones declared before the solve."""
    loaded = load_gas_st_campaign_params("SOCO")
    assert set(loaded) == set(DECLARED)
    for code, (frac, hours) in DECLARED.items():
        assert loaded[code].min_load_frac == pytest.approx(frac, abs=1e-4)
        assert loaded[code].min_run_hours == hours


@pytest.mark.skipif(not ARTIFACT.exists(), reason="SOCO artifact not hydrated")
def test_membership_gate_is_applied_by_the_loader_not_the_consumer() -> None:
    """A ``not_campaign_duty`` row is present in the artifact and never loaded."""
    flags = {int(r["plant_code"]): r["flag"] for r in _rows()}
    assert flags[EXCLUDED_PLANT] == "not_campaign_duty"
    assert EXCLUDED_PLANT not in load_gas_st_campaign_params("SOCO")


@pytest.mark.skipif(not ARTIFACT.exists(), reason="SOCO artifact not hydrated")
def test_every_applied_plant_is_synchronized_more_than_half_the_year() -> None:
    """Rule 17 ``[R-FLOOR-WINDOW]``: the population is campaign-duty by measurement.

    The gate separates SOCO's plants by an order of magnitude (0.063 against
    0.639-0.920), so it selects nothing — it names a gap the data already has.
    """
    by_code = {int(r["plant_code"]): r for r in _rows()}
    applied = [float(by_code[c]["sync_share"]) for c in DECLARED]
    refused = float(by_code[EXCLUDED_PLANT]["sync_share"])
    assert min(applied) >= 0.50
    assert refused < 0.10
    # Any gate value strictly between the two populations gives the same
    # partition — the property that makes the 0.50 declaration un-tunable.
    assert refused < 0.07 < 0.63 < min(applied)


def test_loader_is_empty_for_an_iso_with_no_artifact() -> None:
    """A missing artifact is a normal state, not a failure."""
    assert load_gas_st_campaign_params("ERCOT") == {}


class _Cfg:
    def __init__(self, on: bool) -> None:
        self.soco_gas_st_campaign_commitment = on


def test_prep_hook_is_iso_exclusive_and_default_off() -> None:
    """Off, or any non-SOCO ISO, returns ``None`` — byte-identical everywhere."""
    assert build_soco_gas_st_campaign_p1_prep(_Cfg(False), "SOCO", [], None) is None
    assert build_soco_gas_st_campaign_p1_prep(_Cfg(True), "SPP", [], None) is None
    assert build_soco_gas_st_campaign_p1_prep(_Cfg(True), "ERCOT", [], None) is None
    assert build_soco_gas_st_campaign_p1_prep(_Cfg(True), "SOCO", [], None) is not None


def test_field_ships_off() -> None:
    """The gate's shipping default is off (rule 24 ``[R-REGISTRY]``)."""
    from market_sim.config.scenarios import ScenarioConfig

    assert ScenarioConfig().soco_gas_st_campaign_commitment is False
