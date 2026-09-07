"""SPP priced-seam registry (lane SPP-51, 2026-09-07).

Pins the three SPP-51 adjudications on ``INTERFACE_NEIGHBORS["SPP"]`` and the
per-ISO anchor map of ``scripts/data/derive_neighbor_hr_by_year.py``:

* the MISO seam is two blocks (``MISO_West`` / ``MISO_South``), one per
  bordering MISO zone, each with a measured per-year ``hr_by_year``;
* every SPP block's flat ``marginal_heat_rate`` is the ``HH + gas_basis``
  construction — the mean of its own ``hr_by_year`` cells (FINDING-spp-33 §4 R2);
* the ERCOT DC-tie limit is the measured 835 MW clip (rule 14);
* the producer's per-ISO anchor map reproduces the registry from the committed
  anchor files (integration, skipped without data) and FAILS LOUD where it used
  to ``continue`` silently (FINDING-spp-33 §2 R1);
* every block stays DEFAULT-OFF and topology-less: no ``IMPORT_ZONE`` entry, so
  the served keeper is a byte-identical no-op (PRECOMMIT-spp-51 §2).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from market_sim.config.interchange_config import (
    IMPORT_NODE_LINKS,
    IMPORT_ZONE,
    INTERFACE_NEIGHBORS,
    PRICED_INTERCHANGE_DEFAULT_ISOS,
    REFERENCE_PRICE_DEFAULT_ISOS,
)
from market_sim.config.paths import CALIBRATION_DIR
from market_sim.data.neighbor_price import _HR_GAS_ELASTIC, neighbor_heat_rate

_REPO = Path(__file__).resolve().parents[3]
_PRODUCER = _REPO / "scripts" / "data" / "derive_neighbor_hr_by_year.py"

# The SPP-51 table (PRECOMMIT-spp-51 §1(b)); SPP-33 §3's combined MISO row is
# the equal-weight mean of the two legs.
_HR_BY_YEAR = {
    "MISO_West": {2023: 10.12, 2024: 11.02, 2025: 10.52},
    "MISO_South": {2023: 9.52, 2024: 10.09, 2025: 9.28},
    "AECI": {2023: 10.30, 2024: 12.08, 2025: 8.32},
    "ERCOT": {2023: 23.70, 2024: 15.87, 2025: 10.76},
}
_SPP33_COMBINED_MISO = {2023: 9.82, 2024: 10.55, 2025: 9.90}


def _producer():
    spec = importlib.util.spec_from_file_location(
        "derive_neighbor_hr_by_year", _PRODUCER
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def spp_blocks() -> dict[str, object]:
    return {n.name: n for n in INTERFACE_NEIGHBORS["SPP"]}


def test_spp_registers_the_four_blocks(spp_blocks):
    assert set(spp_blocks) == {"MISO_West", "MISO_South", "AECI", "ERCOT"}


def test_hr_by_year_is_the_declared_measured_table(spp_blocks):
    for name, table in _HR_BY_YEAR.items():
        assert spp_blocks[name].hr_by_year == table, name


def test_miso_legs_reproduce_spp33_combined_table(spp_blocks):
    """Equal-weight mean of the two legs == SPP-33 §3's single-MISO row."""
    west, south = (
        spp_blocks["MISO_West"].hr_by_year,
        spp_blocks["MISO_South"].hr_by_year,
    )
    for year, combined in _SPP33_COMBINED_MISO.items():
        assert round((west[year] + south[year]) / 2, 2) == pytest.approx(
            combined, abs=0.011
        )


def test_flat_heat_rate_is_the_hh_plus_basis_construction(spp_blocks):
    """marginal_heat_rate == mean(hr_by_year) — never a bare-HH divisor (R2)."""
    for name, block in spp_blocks.items():
        mean_hr = sum(block.hr_by_year.values()) / len(block.hr_by_year)
        assert block.marginal_heat_rate == pytest.approx(mean_hr, abs=0.006), name


def test_backcast_years_resolve_measured_and_forward_falls_to_flat(spp_blocks):
    for name, block in spp_blocks.items():
        for year, hr in block.hr_by_year.items():
            assert neighbor_heat_rate(block, year) == hr, (name, year)
        # No _HR_GAS_ELASTIC key exists for any SPP seam (R3 reported, not
        # fixed), so a forecast year prices off the flat value.
        assert name not in _HR_GAS_ELASTIC
        assert neighbor_heat_rate(block, 2030) == block.marginal_heat_rate


def test_ercot_limit_is_the_measured_clip(spp_blocks):
    assert spp_blocks["ERCOT"].interface_limit_mw == 835.0
    assert spp_blocks["ERCOT"].border_zones == ("SPP-South",)


def test_miso_legs_land_on_different_sides_and_sum_to_the_mmu_total(spp_blocks):
    assert spp_blocks["MISO_West"].border_zones == ("SPP-North",)
    assert spp_blocks["MISO_South"].border_zones == ("SPP-South",)
    assert (
        spp_blocks["MISO_West"].interface_limit_mw
        + spp_blocks["MISO_South"].interface_limit_mw
    ) == 6000.0


def test_hurdle_and_shape_are_the_registered_neutral_values(spp_blocks):
    for block in spp_blocks.values():
        assert block.hurdle == 2.0
        assert block.load_shape_exponent == 1.0


def test_seam_names_are_unique_across_every_iso_registry():
    """G10: no SPP name collides with another ISO's neighbour (rule 25)."""
    owners: dict[str, set[str]] = {}
    for iso, neighbors in INTERFACE_NEIGHBORS.items():
        for n in neighbors:
            owners.setdefault(n.name, set()).add(iso)
    for n in INTERFACE_NEIGHBORS["SPP"]:
        assert owners[n.name] == {"SPP"}, n.name


def test_spp_blocks_are_default_off_and_topology_less():
    """The served keeper is a byte-identical no-op (PRECOMMIT-spp-51 §2)."""
    assert "SPP" not in REFERENCE_PRICE_DEFAULT_ISOS
    assert "SPP" not in PRICED_INTERCHANGE_DEFAULT_ISOS
    assert "SPP" not in IMPORT_ZONE
    assert "SPP" not in IMPORT_NODE_LINKS


# --- the producer's per-ISO anchor map (FINDING-spp-33 §2 R1) ----------------


def test_anchor_map_names_every_spp_block_and_keeps_other_isos_unchanged():
    mod = _producer()
    anchors = mod.NEIGHBOR_LMP_ANCHORS
    assert set(anchors["SPP"]) == set(_HR_BY_YEAR)
    assert anchors["SPP"]["MISO_West"] == mod.Anchor("zonal_MISO", ("MISO-West",))
    assert anchors["SPP"]["MISO_South"] == mod.Anchor("zonal_MISO", ("MISO-South",))
    assert anchors["SPP"]["AECI"].proxy is True
    assert anchors["SPP"]["AECI"].product == "SPP"
    assert anchors["SPP"]["ERCOT"] == mod.Anchor("ERCOT")
    # The pre-SPP-51 global map, carried per ISO unchanged.
    assert anchors["PJM"] == {"MISO": mod.Anchor("MISO"), "NYISO": mod.Anchor("NYISO")}
    assert anchors["MISO"] == {"PJM": mod.Anchor("PJM"), "SPP": mod.Anchor("SPP")}
    assert mod.unanchored("SPP") == []
    assert set(mod.unanchored("PJM")) == {"Carolinas", "TVA", "LGEE"}


def test_unregistered_iso_fails_loud():
    mod = _producer()
    with pytest.raises(KeyError):
        mod.derive("ERCOT", [2023])


def test_declared_anchor_with_missing_rows_fails_instead_of_continuing(monkeypatch):
    mod = _producer()
    monkeypatch.setattr(mod, "_measured_mean_lmp", lambda anchor, year, run="rt": None)
    with pytest.raises(FileNotFoundError):
        mod.derive("SPP", [2023])


_ANCHOR_FILES = (
    "actual_lmp_hourly_zonal_MISO.parquet",
    "actual_lmp_hourly_SPP.parquet",
    "actual_lmp_hourly_ERCOT.parquet",
)


@pytest.mark.skipif(
    not all((CALIBRATION_DIR / f).is_file() for f in _ANCHOR_FILES),
    reason="committed SPP seam anchor files not hydrated",
)
def test_producer_reproduces_the_registry_from_committed_anchors(spp_blocks):
    """The registry IS the producer's output (rule 23: re-derivable, not typed)."""
    mod = _producer()
    try:
        table = mod.derive("SPP", [2023, 2024, 2025])
    except FileNotFoundError as exc:  # EIA-930 shape extracts not hydrated
        pytest.skip(str(exc))
    assert table == _HR_BY_YEAR
