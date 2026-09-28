"""``campd_split_remap_companions`` on a PLAIN-family ISO (SPP-99).

miso-280's split-remap companions were derived on MISO's fuel-split tranche family.
SPP's keeper reads the plain tranche artifact and the net-load-masked std extract,
so SPP-99 widened the selector to the plain family and committed SPP's four
``-splitremap-`` companions: the std (base and net-load-masked) outage extracts,
the measured CC heat rates and the plain tranches. Each is its incumbent with only
the remap plants' lines replaced (``scripts/data/build_campd_split_remap_companions.py``).
"""

from pathlib import Path

import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import campd
from market_sim.data.fleet import campd_bins as cb

_ROOT = Path(__file__).resolve().parents[3]
_RAW = _ROOT / "data" / "raw"
_PROC = _RAW / "_processed-legacy"
_SPP_PLANTS = {1416, 56565, 3006, 55655, 762, 7546, 63628, 2953}

_PAIRS = (
    (_RAW / "campd-unit-outages-SPP.csv", "facility_id"),
    (_RAW / "campd-unit-outages-netloadmask-SPP.csv", "facility_id"),
    (_PROC / "campd_cc_heat_rates_SPP.csv", "plant_code"),
    (_PROC / "thermal_tranches_SPP.csv", "plant_code"),
)


def test_plain_tag_selects_the_plain_companion(tmp_path):
    """The plain tag resolves the plain artifact's own companion, raising when absent."""
    base = tmp_path / "thermal_tranches_SPP.csv"
    base.write_text("x\n")
    with pytest.raises(FileNotFoundError):
        cb._fuel_split_companion(base, cb.PLAIN_SPLIT_REMAP_TAG)
    comp = tmp_path / "thermal_tranches-splitremap-SPP.csv"
    comp.write_text("x\n")
    assert cb._fuel_split_companion(base, cb.PLAIN_SPLIT_REMAP_TAG) == comp


def test_fuel_split_family_is_unchanged():
    """MISO's fuel-split selection is untouched by the plain widening."""
    armed = ScenarioConfig(
        campd_unit_fuel_split=True, campd_split_remap_companions=True
    )
    assert cb.campd_fuel_split_selector(armed) == campd.SPLIT_REMAP_TAG
    assert cb.campd_fuel_split_selector(ScenarioConfig()) is False


@pytest.mark.parametrize("incumbent,key", _PAIRS, ids=lambda x: getattr(x, "name", x))
def test_committed_spp_companion_moves_only_remap_plants(incumbent, key):
    """Every line outside the remap plants is byte-identical to the incumbent's."""
    stem = incumbent.stem
    cut = max(stem.rfind("-"), stem.rfind("_"))
    companion = incumbent.with_name(
        f"{stem[:cut]}-{campd.SPLIT_REMAP_TAG}-{stem[cut + 1 :]}{incumbent.suffix}"
    )
    if not (incumbent.is_file() and companion.is_file()):
        pytest.skip("SPP data profile not hydrated")
    inc, comp = pd.read_csv(incumbent), pd.read_csv(companion)
    assert list(inc.columns) == list(comp.columns)
    a = inc[~inc[key].isin(_SPP_PLANTS)].reset_index(drop=True)
    b = comp[~comp[key].isin(_SPP_PLANTS)].reset_index(drop=True)
    pd.testing.assert_frame_equal(a, b)


def test_stall_windows_move_off_arsenal_hill():
    """The masked std companion books Stall's CTs to 56565, leaving 1416 with unit 5A only."""
    path = _RAW / "campd-unit-outages-netloadmask-splitremap-SPP.csv"
    if not path.is_file():
        pytest.skip("SPP data profile not hydrated")
    df = pd.read_csv(path)
    assert set(df.loc[df.facility_id == 56565, "unit_id"]) == {"CTG-6A", "CTG-6B"}
    assert set(df.loc[df.facility_id == 1416, "unit_id"]) == {"5A"}
