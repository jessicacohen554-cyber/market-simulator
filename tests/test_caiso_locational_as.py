"""Tests for the CAISO locational AS-requirement families (caiso-71).

Covers the measured OASIS AS_REQ regional-minimum loader
(``data.caiso_as_requirements``) and the zone-masked SP26/NP26 spin/non-spin
family builder (``reserve_config._caiso_locational_as_families``) behind
``ScenarioConfig.caiso_locational_as_families`` (default off).

The mechanism is EX-ANTE INERT on the current split topology (the SP26 minimum
is ~15x smaller than SoCal's own un-postured reserve supply — see
``results/calibration/FINDING-caiso71-locational-as-inert-2026-07-10.md``);
these tests assert it is wired correctly and default-off, not that it binds.
"""

import numpy as np
import pytest

from market_sim.config.reserve_config import _caiso_locational_as_families
from market_sim.data import caiso_as_requirements as asr
from market_sim.data.caiso_as_requirements import (
    REGION_ZONES,
    load_caiso_as_requirements,
)

CAISO_ZONES = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest", "WECC_import"]


# --- loader (real committed train-year data) -------------------------------


@pytest.mark.parametrize("year", [2023, 2024, 2025])
def test_loader_shape_and_keys(year):
    d = load_caiso_as_requirements(year, 8760, bound="min")
    assert set(d) == {"sp26_spin", "sp26_nonspin", "np26_spin", "np26_nonspin"}
    for k, v in d.items():
        assert v.shape == (8760,)
        assert np.all(np.isfinite(v)) and np.all(v >= 0), k


def test_loader_magnitudes_2024():
    d = load_caiso_as_requirements(2024, 8760, bound="min")
    # SP26 spin ~56 MW, non-spin ~225 MW (data/raw/CAISO-AS aggregation).
    assert 40 < d["sp26_spin"].mean() < 80
    assert 180 < d["sp26_nonspin"].mean() < 260
    # Non-spin floor materially exceeds the spin floor for the same region.
    assert d["sp26_nonspin"].mean() > d["sp26_spin"].mean()


def test_loader_max_is_zero_sentinel():
    # The regional MAX (anti-concentration cap) rows are a uniform 0 sentinel
    # for every SP26/NP26 spin/non-spin product — CAISO publishes no regional
    # cap on these, so only the MIN floor is a usable locational driver.
    hi = load_caiso_as_requirements(2024, 8760, bound="max")
    for k, v in hi.items():
        assert np.all(v == 0.0), k


def test_loader_missing_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_caiso_as_requirements(2024, 8760, raw_dir=tmp_path)


def test_loader_bad_bound():
    with pytest.raises(ValueError):
        load_caiso_as_requirements(2024, 8760, bound="mean")


# --- family builder (synthetic series, zone-mask semantics) ----------------


def _steps():
    pen = np.array([100.0, 500.0])
    wid = np.array([2000.0, 2000.0])
    return pen, wid


def test_families_zone_masks(monkeypatch):
    T = 24
    series = {
        "sp26_spin": np.full(T, 60.0),
        "sp26_nonspin": np.full(T, 220.0),
        "np26_spin": np.full(T, 55.0),
        "np26_nonspin": np.full(T, 210.0),
    }
    monkeypatch.setattr(asr, "load_caiso_as_requirements", lambda *a, **k: series)
    pen, wid = _steps()
    fams = _caiso_locational_as_families(
        CAISO_ZONES, len(CAISO_ZONES), T, 2024, pen, wid, pen, wid
    )
    by_name = {f.name: f for f in fams}
    assert set(by_name) == {
        "caiso_sp26_spin",
        "caiso_sp26_nonspin",
        "caiso_np26_spin",
        "caiso_np26_nonspin",
    }
    idx = {z: i for i, z in enumerate(CAISO_ZONES)}
    sp = by_name["caiso_sp26_spin"]
    assert sp.requirement.mean() == pytest.approx(60.0)
    sp_zones = {CAISO_ZONES[i] for i in np.flatnonzero(sp.zone_mask)}
    assert sp_zones == set(REGION_ZONES["AS_SP26"])
    # WECC_import must never be part of an in-region must-procure floor.
    assert not sp.zone_mask[idx["WECC_import"]]
    npf = by_name["caiso_np26_nonspin"]
    np_zones = {CAISO_ZONES[i] for i in np.flatnonzero(npf.zone_mask)}
    assert np_zones == set(REGION_ZONES["AS_NP26"])


def test_families_requires_sim_year():
    pen, wid = _steps()
    with pytest.raises(ValueError):
        _caiso_locational_as_families(
            CAISO_ZONES, len(CAISO_ZONES), 24, None, pen, wid, pen, wid
        )


def test_families_requires_zone_names():
    pen, wid = _steps()
    with pytest.raises(ValueError):
        _caiso_locational_as_families(None, 6, 24, 2024, pen, wid, pen, wid)
