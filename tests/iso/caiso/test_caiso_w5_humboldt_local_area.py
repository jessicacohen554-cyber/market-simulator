"""closeout-CAISO-w5 D3: the CAISO Humboldt local-area zone (topology variant).

``caiso_humboldt_local_area`` carves the CAISO LCT Humboldt area out of NP15:
measured load weight, Humboldt-county fleet carve, one-way NP15 -> HUMBOLDT
import link at the published LCT capability per study year. Off, the base
topology is byte-identical.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.constants import (
    CAISO_HUMBOLDT_IMPORT_CAP_MW_BY_YEAR,
    CAISO_HUMBOLDT_PGE_TAC_WEIGHT,
    CAISO_TAC_ZONE_WEIGHTS,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.topology_variant import (
    set_caiso_fsno_partition,
    set_caiso_humboldt_area,
)
from market_sim.model.interchange.caiso import apply_caiso_humboldt_import_limit


@pytest.fixture
def humboldt():
    """Arm the variant for one test and always disarm it afterwards."""
    set_caiso_humboldt_area(True)
    try:
        yield
    finally:
        set_caiso_humboldt_area(False)
        set_caiso_fsno_partition(False)


def _link(cfg, a, b):
    return next(link for link in cfg.links if (link.from_zone, link.to_zone) == (a, b))


def test_off_is_base_topology():
    """Disarmed: no HUMBOLDT zone, no extra link, NP15 at its base share."""
    cfg = get_iso_config("CAISO")
    assert "HUMBOLDT" not in cfg.zone_names
    assert all(link.to_zone != "HUMBOLDT" for link in cfg.links)
    assert next(z for z in cfg.zones if z.name == "NP15").load_share == 0.4079


def test_on_zone_and_load_shares(humboldt):
    """Armed: HUMBOLDT carries the measured weight of PG&E, NP15 the residual."""
    cfg = get_iso_config("CAISO")
    shares = {z.name: z.load_share for z in cfg.zones}
    assert abs(sum(shares.values()) - 1.0) < 1e-9
    assert shares["HUMBOLDT"] == pytest.approx(
        0.4615 * CAISO_HUMBOLDT_PGE_TAC_WEIGHT, abs=1e-6
    )
    assert shares["NP15"] + shares["HUMBOLDT"] == pytest.approx(0.4079, abs=1e-6)
    assert shares["ZP26"] == 0.0536


def test_on_link_is_one_way_tightest_year(humboldt):
    """The import link is one-way at the tightest published capability."""
    link = _link(get_iso_config("CAISO"), "NP15", "HUMBOLDT")
    assert link.is_bidirectional is False
    assert link.ttc_mw == min(CAISO_HUMBOLDT_IMPORT_CAP_MW_BY_YEAR.values())


@pytest.mark.parametrize("year", [2019, 2023, 2025, 2030, 2015])
def test_per_year_cap(humboldt, year):
    """Per study year: the table value; past it the latest, before it the earliest."""
    cfg = apply_caiso_humboldt_import_limit(get_iso_config("CAISO"), "CAISO", year)
    table = CAISO_HUMBOLDT_IMPORT_CAP_MW_BY_YEAR
    key = year if year in table else (max(table) if year > max(table) else min(table))
    assert _link(cfg, "NP15", "HUMBOLDT").ttc_mw == table[key]


def test_per_year_cap_noop_off_variant():
    """Variant off: the applier returns the same object (byte-identical)."""
    cfg = get_iso_config("CAISO")
    assert apply_caiso_humboldt_import_limit(cfg, "CAISO", 2023) is cfg
    assert apply_caiso_humboldt_import_limit(cfg, "ERCOT", 2023) is cfg


def test_does_not_compose_with_fsno(humboldt):
    """Both variants re-split the PG&E zone, so arming both raises."""
    set_caiso_fsno_partition(True)
    with pytest.raises(ValueError):
        get_iso_config("CAISO")


def test_hourly_rescale_preserves_columns_and_zp26(humboldt):
    """The hourly re-split keeps every column total and leaves ZP26 untouched."""
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zones = get_iso_config("CAISO").zone_names
    shares = load_zonal_shares("CAISO", 2023, zones)
    if shares is None:
        pytest.skip("CAISO 2023 TAC shares not hydrated")
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)
    h, n = zones.index("HUMBOLDT"), zones.index("NP15")
    w_np15 = CAISO_TAC_ZONE_WEIGHTS["PGE-TAC"]["NP15"]
    ratio = shares[h] / (shares[h] + shares[n])
    np.testing.assert_allclose(ratio, CAISO_HUMBOLDT_PGE_TAC_WEIGHT / w_np15, rtol=1e-9)


def test_fleet_carve_moves_humboldt_bay(humboldt):
    """Humboldt Bay (EIA 246, Humboldt County) is zoned HUMBOLDT; off it is NP15."""
    from market_sim.data.zone_assignment import build_zone_lookup

    on = build_zone_lookup("CAISO")
    if 246 not in on:
        pytest.skip("eGRID plant table not hydrated")
    assert on[246] == "HUMBOLDT"
    set_caiso_humboldt_area(False)
    assert build_zone_lookup("CAISO")[246] == "NP15"
