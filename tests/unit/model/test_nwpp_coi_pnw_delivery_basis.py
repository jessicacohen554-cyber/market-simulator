"""NWPP-NEXT-23: COI's export leg on CAISO's registered PNW delivered-cost basis.

``ScenarioConfig.nwpp_coi_pnw_delivery_basis`` prices the CAISO_COI seam's NW->CA
export bands at ``(band - wheel) / (1 + loss)`` with CAISO's own
``CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]`` instead of ``band - hurdle``. Import
legs and the other seams keep the hurdle; the default is byte-identical.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest import mock

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.interchange import import_nodes
from market_sim.model.interchange.spec import (
    CAISO_IMPORT_DELIVERY_BASIS,
    INTERFACE_NEIGHBORS,
    NWPP_SEAM_EXPORT_DELIVERY_TRANCHE,
)

HOURS = 24


def _fleet():
    """One ordinary unit plus NWPP's reference-price seam bands."""
    gens = import_nodes.build_reference_price_node("NWPP")
    ids = ["ordinary_unit"] + [g.unit_id for g in gens]
    return SimpleNamespace(
        unit_ids=ids,
        pmax=np.array([100.0] + [g.pmax_mw for g in gens]),
        pmin=np.array([0.0] + [g.pmin_mw for g in gens]),
    ), len(ids)


def _fake_tranches(spec, year, hours, n_tranches=SEAM_FLOW_TRANCHES, **_):
    """Deterministic band prices: export 40 + k, import 50 + k, every hour."""
    k = np.arange(n_tranches, dtype=float)[:, None]
    flat = np.zeros((n_tranches, hours))
    return 40.0 + k + flat, 50.0 + k + flat, spec.ba_code


def _inject(basis):
    fa, n = _fleet()
    mc = np.full((n, HOURS), -1.0)
    agg = SimpleNamespace(aggregate=lambda: None)
    with (
        mock.patch(
            "market_sim.data.neighbor_price.seam_tranche_prices", _fake_tranches
        ),
        mock.patch(
            "market_sim.data.neighbor_price.interface_reference_prices",
            lambda *a, **k: agg,
        ),
    ):
        import_nodes.inject_reference_price_mc(
            fa, mc, "NWPP", 2024, export_delivery_basis=basis
        )
    return fa.unit_ids, mc


def _rows(ids, mark, seam):
    return [
        (i, int(u.rsplit("#", 1)[1]) - 1 if "#" in u else 0)
        for i, u in enumerate(ids)
        if mark in u and u.rsplit(mark, 1)[1].partition("#")[0] == seam
    ]


HURDLE = {n.name: n.hurdle for n in INTERFACE_NEIGHBORS["NWPP"]}
EXP, IMP = import_nodes._REF_EXPORT_MARK, import_nodes._REF_IMPORT_MARK


def test_registry_maps_coi_to_caiso_pnw_rung():
    """COI is the only mapped seam, and it reads CAISO's PNW_midC basis."""
    assert NWPP_SEAM_EXPORT_DELIVERY_TRANCHE == {"CAISO_COI": "PNW_midC"}
    assert CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"] == (0.05, 5.0)


def test_default_is_hurdle_pricing():
    """No basis: every export band is band - hurdle, every import band + hurdle."""
    ids, mc = _inject(None)
    for seam in HURDLE:
        for row, k in _rows(ids, EXP, seam):
            np.testing.assert_allclose(mc[row], 40.0 + k - HURDLE[seam])
        for row, k in _rows(ids, IMP, seam):
            np.testing.assert_allclose(mc[row], 50.0 + k + HURDLE[seam])


def test_basis_prices_only_coi_export_leg():
    """Armed: COI exports at (band - 5) / 1.05; COI imports and other seams untouched."""
    ids, armed = _inject({"CAISO_COI": (0.05, 5.0)})
    _, base = _inject(None)
    coi_exp = _rows(ids, EXP, "CAISO_COI")
    assert coi_exp, "NWPP must carry COI export bands"
    for row, k in coi_exp:
        np.testing.assert_allclose(armed[row], (40.0 + k - 5.0) / 1.05)
    changed = {row for row, _ in coi_exp}
    untouched = [r for r in range(len(ids)) if r not in changed]
    np.testing.assert_array_equal(armed[untouched], base[untouched])


def test_basis_is_stricter_than_hurdle_at_nw_prices():
    """At any positive band the delivered basis demands a wider spread than 3.0."""
    band = np.linspace(10.0, 200.0, 50)
    assert np.all((band - 5.0) / 1.05 < band - HURDLE["CAISO_COI"])


def test_armed_without_priced_seams_raises():
    """pjm-119: the key armed where no priced seam exists raises, never no-ops."""
    fa, n = _fleet()
    cfg = ScenarioConfig(nwpp_coi_pnw_delivery_basis=True)
    with pytest.raises(ValueError, match="reference_price_interface"):
        import_nodes.apply_reference_price_seam_injections(
            fa, np.zeros((n, HOURS)), cfg, "NWPP", 2024
        )


def test_armed_passes_caiso_basis_to_injector():
    """Armed with the priced interface: the injector receives CAISO's PNW basis."""
    fa, n = _fleet()
    cfg = ScenarioConfig(
        nwpp_coi_pnw_delivery_basis=True, reference_price_interface=True
    )
    seen = {}

    def _capture(*a, **k):
        seen.update(k)
        return False

    with (
        mock.patch.object(import_nodes, "inject_reference_price_mc", _capture),
        mock.patch.object(
            import_nodes, "inject_reference_price_firm_export", lambda *a: False
        ),
    ):
        import_nodes.apply_reference_price_seam_injections(
            fa, np.zeros((n, HOURS)), cfg, "NWPP", 2024
        )
    assert seen["export_delivery_basis"] == {"CAISO_COI": (0.05, 5.0)}


def test_other_iso_ignores_the_key():
    """The key is NWPP-scoped: another ISO's injector sees no basis."""
    fa, n = _fleet()
    cfg = ScenarioConfig(
        nwpp_coi_pnw_delivery_basis=True, reference_price_interface=True
    )
    seen = {}

    def _capture(*a, **k):
        seen.update(k)
        return False

    with (
        mock.patch.object(import_nodes, "inject_reference_price_mc", _capture),
        mock.patch.object(
            import_nodes, "inject_reference_price_firm_export", lambda *a: False
        ),
    ):
        import_nodes.apply_reference_price_seam_injections(
            fa, np.zeros((n, HOURS)), cfg, "MISO", 2024
        )
    assert seen["export_delivery_basis"] is None


def test_cache_key_default_stable_armed_distinct():
    """Default drops from the hash (byte-stable keys); arming changes it."""
    base = ScenarioConfig(iso="NWPP")
    off = ScenarioConfig(iso="NWPP", nwpp_coi_pnw_delivery_basis=False)
    armed = ScenarioConfig(iso="NWPP", nwpp_coi_pnw_delivery_basis=True)
    assert base.cache_key() == off.cache_key()
    assert base.cache_key() != armed.cache_key()
