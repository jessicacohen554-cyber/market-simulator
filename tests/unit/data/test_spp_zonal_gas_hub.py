"""SPP zonal gas-hub table wiring (lane SPP-32).

The table is a **registered measured input, not an armed mechanism**: this
lane adds no ``ScenarioConfig`` field (plan §7 gate G8), so nothing in a solve
reads it yet. What these tests pin is that it will be read *correctly* when
SPP-40 / SPP-52 arms an applier, and — the load-bearing part — that the
publication gap in its source cannot turn into a fabricated cross-zonal
spread.

The schema tests run against synthetic tables in a tempdir (gate G17); the two
tests that inspect the committed table are marked ``fulldata`` and skip when it
is not hydrated.
"""

from __future__ import annotations

import pandas as pd
import pytest

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fuel import SPP_ZONAL_GAS_HUB_PATH
from market_sim.data.fuel.basis import meanzero

_COLUMNS = ["zone", "year", "basis_vs_hh_usd_mmbtu", "hub", "source"]


def _write_hub_table(path, rows):
    """Write a hub table in the shared MISO/PJM/CAISO schema."""
    pd.DataFrame(
        [
            {
                "zone": zone, "year": year, "basis_vs_hh_usd_mmbtu": basis,
                "hub": "test hub", "source": "synthetic fixture",
            }
            for zone, year, basis in rows
        ],
        columns=_COLUMNS,
    ).to_csv(path, index=False)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------


def test_path_is_registered_and_named_like_its_siblings():
    """SPP's table sits beside the other ISOs' in the same registry module."""
    assert SPP_ZONAL_GAS_HUB_PATH is meanzero.SPP_ZONAL_GAS_HUB_PATH
    assert SPP_ZONAL_GAS_HUB_PATH.name == "spp_zonal_gas_hub.csv"


def test_the_shared_loader_reads_the_shared_schema(tmp_path):
    """No new parsing code: the sibling loader reads SPP's table as-is."""
    path = tmp_path / "spp_zonal_gas_hub.csv"
    _write_hub_table(path, [("SPP-North", 2023, 0.784), ("SPP-South", 2023, 0.418)])
    assert meanzero._zonal_gas_basis_by_zone(path, 2023) == {
        "SPP-North": 0.784,
        "SPP-South": 0.418,
    }


def test_a_year_absent_from_the_table_reads_as_none(tmp_path):
    """An unpublished year must return ``None`` so an applier no-ops.

    This is the whole reason the committed table stops at the intersection of
    the two zones' published years: ``None`` makes the mean-zero applier return
    early, which is a visible absence.
    """
    path = tmp_path / "spp_zonal_gas_hub.csv"
    _write_hub_table(path, [("SPP-North", 2023, 0.784), ("SPP-South", 2023, 0.418)])
    assert meanzero._zonal_gas_basis_by_zone(path, 2025) is None


def test_a_half_populated_year_is_the_hazard_this_table_avoids(tmp_path):
    """Demonstrates WHY a North-only year is never committed.

    With only one zone present the lookup succeeds and returns a one-key dict;
    a consumer reading each zone with ``.get(name, 0.0)`` would then hand
    SPP-South a 0.0 basis and manufacture a ~$0.78/MMBtu spread out of a
    publication gap. Pinned as a live demonstration rather than a comment, so
    that anyone tempted to add the 2025 North row sees the consequence.
    """
    path = tmp_path / "spp_zonal_gas_hub.csv"
    _write_hub_table(path, [("SPP-North", 2025, 1.129)])
    basis = meanzero._zonal_gas_basis_by_zone(path, 2025)
    assert basis == {"SPP-North": 1.129}
    assert basis.get("SPP-South", 0.0) == 0.0  # the fabricated spread


# ---------------------------------------------------------------------------
# The committed table
# ---------------------------------------------------------------------------


_committed = pytest.mark.skipif(
    not SPP_ZONAL_GAS_HUB_PATH.exists(),
    reason="spp_zonal_gas_hub.csv not hydrated (needs the shared data profile)",
)


@_committed
def test_committed_table_covers_both_zones_in_every_year():
    """THE GATE: no year is half-populated, in either direction."""
    frame = pd.read_csv(SPP_ZONAL_GAS_HUB_PATH)
    assert list(frame.columns) == _COLUMNS
    zones = set(get_iso_config("SPP").zone_names)
    assert set(frame["zone"]) == zones
    for year, group in frame.groupby("year"):
        assert set(group["zone"]) == zones, f"{year} is half-populated"


@_committed
def test_committed_table_rests_on_thirty_six_monthly_observations_per_zone():
    """Each zone's committed span is 3 years x 12 monthly EIA prints.

    The annual basis is a mean of 12 monthly observations, so the committed
    span of 3 years is exactly 36 source observations per zone. A year added
    without its full 12 months would break this.
    """
    frame = pd.read_csv(SPP_ZONAL_GAS_HUB_PATH)
    for zone, group in frame.groupby("zone"):
        assert len(group) * 12 == 36, f"{zone} does not rest on 36 monthly prints"
        assert group["source"].str.contains("12 monthly observations").all()
