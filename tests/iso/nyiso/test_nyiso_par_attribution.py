"""Tests for the NYISO NY-NJ PAR seam attribution (nyiso-127).

Trivial cases first (a handful of hours, one PAR, one row), then the real
committed intake. The published objects under test are the PAR registry, the
posting's outage-reallocation rule, and the per-zone attribution of every posted
P-32 row — none of which may contain a chosen number.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data import nyiso_par_attribution as par


def _outages(rows: list[tuple[int, str, str]]) -> pd.DataFrame:
    """Build a minimal outage frame from ``(ptid, start, end)`` triples."""
    return pd.DataFrame(
        {
            "ptid": [r[0] for r in rows],
            "outage_start": pd.to_datetime([r[1] for r in rows]),
            "outage_end": pd.to_datetime([r[2] for r in rows]),
        }
    )


def test_published_shares_sum_to_one():
    """The eight percentages plus the western residual are exhaustive."""
    named = sum(share for *_, share in par.PAR_REGISTRY.values())
    assert named == pytest.approx(0.68)  # 2x16 + 3x5 + 3x7
    assert named + par.WEST_RESIDUAL_SHARE == pytest.approx(1.0)


def test_registry_is_eight_pars_across_three_interfaces():
    """Exactly the eight PARs the posting names, on its three interfaces."""
    assert len(par.PAR_REGISTRY) == 8
    by_iface: dict[str, float] = {}
    for _n, _e, iface, share in par.PAR_REGISTRY.values():
        by_iface[iface] = by_iface.get(iface, 0.0) + share
    assert by_iface == pytest.approx({"ramapo": 0.32, "jk": 0.15, "abc": 0.21})


def test_out_mask_is_the_union_of_nested_windows():
    """outSched rolls a long outage's Scheduled In forward; the union is the state."""
    idx = pd.date_range("2023-01-01", periods=10, freq="h")
    frame = _outages(
        [
            (25043, "2023-01-01 00:00", "2023-01-01 03:00"),
            (
                25043,
                "2023-01-01 00:00",
                "2023-01-01 06:00",
            ),  # the same outage, extended
        ]
    )
    mask = par.par_out_mask(frame, 25043, idx)
    assert mask[:6].all()
    assert not mask[6:].any()


def test_shares_sum_to_one_every_hour_and_reallocate_west():
    """An out-of-service PAR's share goes west, hour by hour, exactly."""
    # ABC-B and ABC-C out for the whole year; everything else in service.
    frame = _outages(
        [
            (25044, "2023-01-01", "2024-01-01"),
            (25043, "2023-01-01", "2024-01-01"),
        ]
    )
    shares = par.zone_shares(frame, 2023)
    total = sum(shares.values())
    assert np.allclose(total, 1.0)
    # Zone J keeps only ABC-A's 7 %; its other 14 points went west.
    assert shares["NYC"] == pytest.approx(0.07)
    assert shares["Capital_Hudson"] == pytest.approx(0.47)
    assert shares["Upstate_West"] == pytest.approx(0.46)


def test_no_outages_reproduces_the_nameplate_split():
    """With every PAR in service the split is the posting's face value."""
    shares = par.zone_shares(_outages([]), 2023)
    assert shares["Capital_Hudson"] == pytest.approx(0.47)
    assert shares["NYC"] == pytest.approx(0.21)
    assert shares["Upstate_West"] == pytest.approx(0.32)


def test_k9_unattributed_row_raises():
    """Kill gate K9: a posted seam row attributed to no zone is fatal."""
    frame = pd.DataFrame(
        {
            "interval_start_local": pd.date_range("2023-01-01", periods=3, freq="h"),
            "interface": ["SCH - MADE_UP"] * 3,
            "flow_mw": [1.0, 2.0, 3.0],
        }
    )
    with pytest.raises(ValueError, match="attributed to no zone"):
        par.attributed_zone_net(frame, 2023)


def test_missing_pjm_row_raises_rather_than_no_opping():
    """The mechanism never silently no-ops when its central row is absent."""
    frame = pd.DataFrame(
        {
            "interval_start_local": pd.date_range("2023-01-01", periods=3, freq="h"),
            "interface": ["SCH - OH - NY"] * 3,
            "flow_mw": [1.0, 2.0, 3.0],
        }
    )
    with pytest.raises(ValueError, match="absent from"):
        par.attributed_zone_net(frame, 2023)


def test_accounting_duplicate_is_never_attributed():
    """K8: the HQ accounting duplicate is excluded, so the HQ seam is not doubled."""
    assert par.ACCOUNTING_DUPLICATE not in par.SEAM_ROW_ZONE
    assert par.ACCOUNTING_DUPLICATE != par.PJM_AC_ROW


def test_every_mapped_row_lands_in_a_real_model_zone():
    """No attribution points at a zone the NYISO topology does not have."""
    zones = {"Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"}
    assert set(par.SEAM_ROW_ZONE.values()) <= zones
    assert set(par.INTERFACE_ZONE.values()) <= zones
    # Lower_Hudson has no external ties and must not acquire one here.
    assert "Lower_Hudson" not in set(par.SEAM_ROW_ZONE.values())


@pytest.mark.slow
def test_committed_intake_reproduces_the_measured_split():
    """The published intake gives G ~46 % / J ~7 % / A ~47 %, not 47/21/32."""
    outages = par.load_par_outages()
    for year, want_j in ((2023, 0.070), (2024, 0.068), (2025, 0.068)):
        shares = par.zone_shares(outages, year)
        assert np.allclose(sum(shares.values()), 1.0)
        assert shares["NYC"].mean() == pytest.approx(want_j, abs=0.002)
        # The nameplate 21 % is nowhere near the measured state.
        assert shares["NYC"].mean() < 0.10
