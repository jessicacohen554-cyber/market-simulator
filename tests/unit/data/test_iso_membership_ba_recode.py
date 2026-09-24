"""ISO plant membership drops plants the current EIA-860 recodes to another BA (SOCO-60).

``constants.ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE`` gates, per ISO, a subtraction
at the single ``run_calibration_full._iso_plant_ids`` seam that the EIA-923
benchmark frame, its class shares and the must-run injection all read. For SOCO
it removes the former Gulf Power plants that EIA-860 recodes to FPL from vintage
2024 and that EIA-930's SOCO series excludes in every year 2019-2024.

Pinned here: the registry is SOCO-only; only an explicit recode removes a plant
(a plant absent from the current file stays); and the named Gulf plants leave
SOCO's membership while every non-listed ISO's membership is untouched.
"""

import importlib.util

import pytest

from market_sim.config.constants import ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "rcf_ba_recode", str(REPO_ROOT / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_EIA860 = REPO_ROOT / "data" / "raw" / "eia-860" / "eia860_plant.parquet"
#: Lansing Smith, Gulf Clean Energy Center, Pea Ridge, Perdido.
_GULF = {643, 641, 7715, 57502}


def test_registry_is_soco_only():
    assert ISO_MEMBERSHIP_DROPS_CURRENT_BA_RECODE == {"SOCO": True}


@pytest.mark.skipif(not _EIA860.exists(), reason="EIA-860 plant file not hydrated")
def test_soco_membership_drops_gulf_plants_only_on_explicit_recode():
    from market_sim.data.zone_assignment import build_zone_lookup

    base = set(build_zone_lookup("SOCO"))
    members = rcf._iso_plant_ids("SOCO")
    assert _GULF <= base
    assert not (_GULF & members)
    dropped = base - members
    # Every dropped plant is an explicit recode, never an absence.
    assert dropped <= rcf._eia860_current_ba_recoded("SOCO")
    assert len(dropped) == 7


@pytest.mark.skipif(not _EIA860.exists(), reason="EIA-860 plant file not hydrated")
def test_unlisted_iso_membership_is_the_base():
    from market_sim.data.zone_assignment import build_zone_lookup

    assert rcf._iso_plant_ids("MISO") == frozenset(build_zone_lookup("MISO"))
