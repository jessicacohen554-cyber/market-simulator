"""The shared benchmark's BTM subtrahend may never follow the run's flag.

nyiso-149 root cause (FINDING-nyiso149-bench-root-cause-2026-08-22): the
per-(ISO, year) bench part's ``classFull`` subtracts the CHP behind-the-meter
hold-out from the EIA-923 class totals, and that subtrahend was taken from the
registering bundle's ``btm.parquet`` — which sizes from the run's
``nyiso_chp_btm_measured`` flag. A flag-off registration therefore committed a
sector-carve benchmark (35% merchant, residual-identified) and a flag-on one a
measured-share benchmark, flipping the shared part between registrations and
silently re-arming the ±3% EIA-930 family reconcile (×1.07–×1.19 on every
NYISO gas class).

The pin: ``_btm_frame`` now emits ``btm_bench_twh`` — the measured-basis class
totals, applied whenever the measured artifact exists, INDEPENDENT of the flag
— alongside the run-basis ``btm_twh`` (what this run's LP actually held out,
still flag-dependent: it is the model-side add-back). The render's bench-part
writers consume ``btm_bench_twh``. These tests pin both properties on
synthetic frames (hermetic: the share sources are monkeypatched) so they run
without the EIA-923 corpus.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

import run_calibration_full as rcf  # noqa: E402

import market_sim.data.chp as chp_mod  # noqa: E402
import market_sim.data.coal as coal_mod  # noqa: E402

SECTOR = 35.0  # stand-in sector share (%)
MEASURED = {100: 0.0}  # plant 100's measured host share (%): grid-only cogen
PLANT_NET = 3_000_000.0  # its EIA-923 CT_CHP net generation (MWh)


def _generation(year: int) -> pd.DataFrame:
    cols = rcf.monthly_netgen_columns()
    return pd.DataFrame(
        [
            {
                "year": year,
                "plant_id": 100,
                "fuel_type": "NG",
                "prime_mover": "GT",
                "chp": "Y",
                "netgen_annual_mwh": PLANT_NET,
                **{c: PLANT_NET / 12.0 for c in cols},
            }
        ]
    )


@pytest.fixture()
def hermetic_shares(monkeypatch):
    monkeypatch.setattr(chp_mod, "chp_btm_pct", lambda code, grp, iso="ERCOT": SECTOR)
    monkeypatch.setattr(chp_mod, "measured_chp_btm_pct_nyiso", lambda: dict(MEASURED))
    monkeypatch.setattr(coal_mod, "coal_chp_overrides", lambda iso, year: {})


def _frame(iso: str, flag: bool, year: int = 2024) -> pd.DataFrame:
    return rcf._btm_frame(
        year,
        "P1",
        _generation(year),
        iso=iso,
        group_by_code={100: "CT_CHP"},
        nyiso_chp_btm_measured=flag,
    )


def _cell(frame: pd.DataFrame, col: str) -> float:
    row = frame[frame["klass"] == "CT_CHP"]
    return float(row[col].iloc[0]) if len(row) else 0.0


def test_bench_basis_is_measured_for_nyiso_regardless_of_flag(hermetic_shares):
    """btm_bench_twh carries the measured share with the flag OFF and ON."""
    for flag in (False, True):
        f = _frame("NYISO", flag)
        assert _cell(f, "btm_bench_twh") == pytest.approx(
            PLANT_NET * (MEASURED[100] / 100.0) / 1e6
        ), f"flag={flag}"


def test_run_basis_still_follows_the_flag(hermetic_shares):
    """btm_twh is the run's own hold-out: sector when off, measured when on."""
    off, on = _frame("NYISO", False), _frame("NYISO", True)
    assert _cell(off, "btm_twh") == pytest.approx(PLANT_NET * SECTOR / 100.0 / 1e6)
    assert _cell(on, "btm_twh") == pytest.approx(
        PLANT_NET * (MEASURED[100] / 100.0) / 1e6
    )


def test_non_nyiso_iso_duplicates_the_run_basis(hermetic_shares):
    """No measured artifact -> the two columns are identical (byte-stable)."""
    for flag in (False, True):
        f = _frame("NEISO", flag)
        assert _cell(f, "btm_bench_twh") == _cell(f, "btm_twh")
        assert _cell(f, "btm_twh") == pytest.approx(PLANT_NET * SECTOR / 100.0 / 1e6)


def test_nyiso_without_artifact_falls_back_to_sector(monkeypatch):
    """An absent measured artifact leaves both columns on the sector share."""
    monkeypatch.setattr(chp_mod, "chp_btm_pct", lambda code, grp, iso="ERCOT": SECTOR)
    monkeypatch.setattr(chp_mod, "measured_chp_btm_pct_nyiso", lambda: {})
    monkeypatch.setattr(coal_mod, "coal_chp_overrides", lambda iso, year: {})
    f = _frame("NYISO", False)
    assert _cell(f, "btm_bench_twh") == _cell(f, "btm_twh")
    assert _cell(f, "btm_twh") == pytest.approx(PLANT_NET * SECTOR / 100.0 / 1e6)


def test_empty_frame_carries_both_columns(hermetic_shares):
    """The no-CHP empty frame declares btm_bench_twh so readers never KeyError."""
    year = 2024
    cols = rcf.monthly_netgen_columns()
    gen = pd.DataFrame(
        [
            {
                "year": year,
                "plant_id": 200,
                "fuel_type": "NG",
                "prime_mover": "CA",
                "chp": "N",
                "netgen_annual_mwh": 1_000_000.0,
                **{c: 1_000_000.0 / 12.0 for c in cols},
            }
        ]
    )
    f = rcf._btm_frame(year, "P1", gen, iso="NYISO", group_by_code={200: "CC_REGULAR"})
    assert "btm_bench_twh" in f.columns and "btm_twh" in f.columns
    assert f.empty
