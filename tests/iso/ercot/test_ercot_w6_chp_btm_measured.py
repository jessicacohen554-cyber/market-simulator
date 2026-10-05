"""closeout-ERCOT-w6: the measured ERCOT CHP behind-the-meter share.

``ercot_chp_btm_measured`` replaces the sector-keyed CHP BTM default in the
capacity carve with the plant's own EIA-923 Schedules 6/7 on-site-use share
(the closeout-CAISO-w6 derive, ERCO-scoped). Because ERCOT's
``chp_export_floor_measured`` grid floor multiplies the same share, the floor
follows it (one share, rule 19). Off (the default), the carve never reads the
artifact; the flag is ERCOT-scoped (rule 25). The benchmark subtrahend reads
the artifact whenever it exists (nyiso-149).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))

import run_calibration_full as rcf  # noqa: E402

import market_sim.data.chp as chp_mod  # noqa: E402
import market_sim.data.coal as coal_mod  # noqa: E402
import market_sim.data.fleet as fleet_mod  # noqa: E402
from market_sim.config.paths import CAMPD_BINS_CSV, PROCESSED_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.chp import (  # noqa: E402
    chp_btm_measured_armed,
    measured_chp_btm_pct_ercot,
    measured_chp_btm_pct_for_iso,
)

ARTIFACT = Path(PROCESSED_DIR) / "chp_btm_share_measured_ERCOT.csv"
SECTOR = 35.0  # stand-in sector share (%)
CODE = 100  # synthetic plant
PLANT_NET = 3_000_000.0  # its EIA-923 CC_CHP net generation (MWh)


def _cfg(iso: str, **kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast", iso=iso, **kw)


def test_off_by_default():
    """The shipping default never arms the measured carve."""
    assert ScenarioConfig().ercot_chp_btm_measured is False
    assert chp_btm_measured_armed(_cfg("ERCOT")) is False


def test_flag_is_iso_scoped():
    """The ERCOT flag arms only ERCOT; the other ISOs' flags never arm ERCOT."""
    assert chp_btm_measured_armed(_cfg("ERCOT", ercot_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("CAISO", ercot_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("PJM", ercot_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("ERCOT", caiso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("ERCOT", nyiso_chp_btm_measured=True))


def test_for_iso_routes_ercot_to_its_own_artifact(monkeypatch):
    """measured_chp_btm_pct_for_iso('ERCOT') reads the ERCOT map only."""
    monkeypatch.setattr(chp_mod, "measured_chp_btm_pct_ercot", lambda: {CODE: 3.0})
    assert measured_chp_btm_pct_for_iso("ERCOT") == {CODE: 3.0}
    assert measured_chp_btm_pct_for_iso("ercot") == {CODE: 3.0}
    assert measured_chp_btm_pct_for_iso("PJM") == {}


# --- _btm_frame: bench basis pinned, run basis follows the flag (1 plant) ---


def _generation(year: int) -> pd.DataFrame:
    cols = rcf.monthly_netgen_columns()
    return pd.DataFrame(
        [
            {
                "year": year,
                "plant_id": CODE,
                "fuel_type": "NG",
                "prime_mover": "CT",
                "chp": "Y",
                "netgen_annual_mwh": PLANT_NET,
                **{c: PLANT_NET / 12.0 for c in cols},
            }
        ]
    )


@pytest.fixture()
def hermetic(monkeypatch):
    """One ERCOT CC_CHP plant, sector 35 %, measured 0 % (a grid-only cogen)."""
    bins = pd.DataFrame(
        {
            "Plant_Code": [CODE],
            "Plant_Group": ["CC_CHP"],
            "fuel": ["gas"],
            "pct_mr": [SECTOR],
            "capacity_mw": [500.0],
            "hr_weighted": [8.0],
        }
    )
    monkeypatch.setattr(fleet_mod, "load_campd_bins", lambda *a, **k: bins.copy())
    monkeypatch.setattr(chp_mod, "chp_btm_pct", lambda code, grp, iso="ERCOT": SECTOR)
    monkeypatch.setattr(chp_mod, "measured_chp_btm_pct_ercot", lambda: {CODE: 0.0})
    monkeypatch.setattr(coal_mod, "coal_chp_overrides", lambda iso, year: {})
    monkeypatch.setattr(rcf, "_classify_f923", lambda f, pm, chp, pid: "CC_CHP")


def _frame(flag: bool, year: int = 2024) -> pd.DataFrame:
    return rcf._btm_frame(
        year, "P1", _generation(year), iso="ERCOT", ercot_chp_btm_measured=flag
    )


def _cell(frame: pd.DataFrame, col: str) -> float:
    row = frame[frame["klass"] == "CC_CHP"]
    return float(row[col].iloc[0]) if len(row) else 0.0


def test_ercot_bench_basis_is_measured_regardless_of_flag(hermetic):
    """btm_bench_twh carries the measured share (0 %) with the flag off and on."""
    for flag in (False, True):
        assert _cell(_frame(flag), "btm_bench_twh") == pytest.approx(0.0)


def test_ercot_run_basis_follows_the_flag(hermetic):
    """btm_twh is the run's own hold-out: sector when off, measured when on."""
    assert _cell(_frame(False), "btm_twh") == pytest.approx(
        PLANT_NET * SECTOR / 100.0 / 1e6
    )
    assert _cell(_frame(True), "btm_twh") == pytest.approx(0.0)


# --- the carve and the export floor read the one share (real 1-plant bin) ---


@pytest.mark.skipif(not Path(CAMPD_BINS_CSV).exists(), reason="bins not hydrated")
def test_carve_and_export_floor_follow_the_measured_share(monkeypatch):
    """Armed, grid capacity and the chp_export_floor_measured floor both scale
    by (1 - measured) / (1 - default); off, neither reads the artifact."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.chp import chp_btm_pct, chp_class_netgen_mwh
    from market_sim.data.fleet import bins_to_fleet, load_campd_bins

    year = 2023
    netgen = chp_class_netgen_mwh(year)
    bins = load_campd_bins(str(CAMPD_BINS_CSV), year=year)
    cc_chp = bins[bins["Plant_Group"] == "CC_CHP"]
    code = next(
        int(c)
        for c in cc_chp["Plant_Code"]
        if netgen.get((int(c), "CC_CHP"), 0.0) > 0.0
    )
    row = cc_chp[cc_chp["Plant_Code"] == code]
    default = chp_btm_pct(code, "CC_CHP")
    zones = get_iso_config("ERCOT").zone_names

    def build(flag: bool) -> tuple[float, float]:
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            weather_year=year,
            chp_steam_following=True,
            chp_export_floor_measured=True,
            ercot_chp_btm_measured=flag,
        )
        fleet, _ = bins_to_fleet(row, zones, cfg)
        cap = sum(g.pmax_mw for g in fleet)
        floor = sum(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0 for g in fleet)
        return cap, floor

    calls: list[int] = []

    def measured() -> dict[int, float]:
        calls.append(1)
        return {code: 0.0}

    monkeypatch.setattr(chp_mod, "measured_chp_btm_pct_ercot", measured)
    cap_off, floor_off = build(False)
    assert calls == []  # off: the artifact is never read
    cap_on, floor_on = build(True)
    assert calls  # armed: read
    ratio = 1.0 / (1.0 - default / 100.0)
    assert cap_on == pytest.approx(cap_off * ratio, rel=1e-6)
    assert floor_on > floor_off
    nameplate = float(row["capacity_mw"].iloc[0])
    total_cf = min(1.0, netgen[(code, "CC_CHP")] / (nameplate * 8760.0))
    assert floor_on <= total_cf * nameplate + 1e-6  # measured 0 % -> all grid


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not hydrated")
def test_artifact_refutes_the_sector_default():
    """The committed artifact carries the measured shares the design cites."""
    m = measured_chp_btm_pct_ercot()
    assert m[55464] < 10.0  # Deer Park: sells ~all of its net
    assert m[55047] < 10.0  # Pasadena Cogen
    assert m[55015] > 70.0  # Sweeny: Phillips 66 refinery self-supply
    assert 0.0 <= min(m.values()) and max(m.values()) <= 100.0
