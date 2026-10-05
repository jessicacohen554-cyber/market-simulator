"""closeout-MISO-w3e: the measured MISO CHP behind-the-meter share.

``miso_chp_btm_measured`` is the MISO leg of the caiso_chp_btm_measured family:
the capacity carve reads the plant's own EIA-923 Schedules 6/7 on-site-use
share, built by the SAME derive function as CAISO's. Off (the default), the
carve never reads the artifact; the flag is MISO-scoped (rule 25).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import scripts.data.derive_caiso_chp_btm_share as caiso_derive
import scripts.data.derive_miso_chp_btm_share as miso_derive
from market_sim.config.paths import PROCESSED_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.chp import (
    chp_btm_measured_armed,
    chp_btm_pct,
    measured_chp_btm_pct_for_iso,
    measured_chp_btm_pct_miso,
)

ARTIFACT = Path(PROCESSED_DIR) / "chp_btm_share_measured_MISO.csv"


def _cfg(iso: str, **kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast", iso=iso, **kw)


def test_off_by_default():
    """The shipping default never arms the measured carve."""
    assert ScenarioConfig().miso_chp_btm_measured is False
    assert chp_btm_measured_armed(_cfg("MISO")) is False


def test_flag_is_iso_scoped():
    """The MISO flag arms only MISO, and no other ISO's flag arms MISO."""
    assert chp_btm_measured_armed(_cfg("MISO", miso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("CAISO", miso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("PJM", miso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("MISO", caiso_chp_btm_measured=True))
    assert not chp_btm_measured_armed(_cfg("MISO", nyiso_chp_btm_measured=True))


def test_one_derive_function():
    """MISO reuses CAISO's derive (one definition); only the plant scope differs."""
    assert miso_derive.derive is caiso_derive.derive


def test_for_iso_routes_miso():
    """The per-ISO resolver returns the MISO map for MISO."""
    assert measured_chp_btm_pct_for_iso("MISO") == measured_chp_btm_pct_miso()


@pytest.mark.skipif(not ARTIFACT.exists(), reason="artifact not hydrated")
def test_artifact_refutes_the_sector_default():
    """The committed artifact carries the measured shares the design cites."""
    m = measured_chp_btm_pct_miso()
    assert m[10745] < 10.0  # Midland Cogen: sells ~all of its net for resale
    assert m[55088] < 10.0  # Dearborn: tolled, ~0 on-site
    assert chp_btm_pct(10745, "CC_CHP", iso="MISO") > 30.0  # the refuted default
    assert 0.0 <= min(m.values()) and max(m.values()) <= 100.0
