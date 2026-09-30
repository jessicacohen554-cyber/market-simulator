"""Per-landing-link monthly band (nyiso_import_landing_band, NYISO-NEXT-15).

Trivial cases first: the 2-zone import-node toy (one EXT -> Z link, two 24-h
"months"). The link-flow band forces the link's monthly energy onto its target
exactly as the node band does, the rows land one per (link, month), supplying
both bands is refused, and the builder places each attributed P-32 zone's
monthly energy on its own pooled border link. Byte-identity off is the
ScenarioConfig default plus the cache-key optional-field ledger.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import VariableLayout
from market_sim.model.lp.rows import _build_import_link_rows
from market_sim.pipeline.kwargs import build_base_dispatch_kwargs

from tests.unit.data.test_import_node_reconciliation import _solve


def test_link_band_forces_link_energy():
    """Gas cheaper than imports: the band still pulls the link to its target."""
    target = np.array([[24 * 200.0, 24 * 150.0]])  # (1 link, 2 months) MWh
    res = _solve(
        mc_gas=20.0,
        mc_import=30.0,
        demand_mw=300.0,
        import_link_band=(np.array([0]), target, target),
        import_node_month_index=np.repeat([0, 1], 24),
    )
    got = np.array([res.flows[0, :24].sum(), res.flows[0, 24:].sum()])
    assert np.allclose(got, target[0], atol=1e-3), got


def test_link_band_rows_one_per_link_month():
    """Row l*n_months+m carries +1 on link l's flow column in every hour of m."""
    layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=2, T=4)
    lo = np.array([[1.0, 2.0], [3.0, 4.0]])
    block, rlo, rhi = _build_import_link_rows(
        layout, np.array([1, 0]), np.array([0, 0, 1, 1]), lo, lo + 1
    )
    assert block.shape == (4, layout.total_columns)
    assert rlo.tolist() == [1.0, 2.0, 3.0, 4.0]
    dense = block.toarray()
    assert dense[0, layout.flow_col(1, 0)] == 1 and dense[0, layout.flow_col(1, 1)] == 1
    assert dense[3, layout.flow_col(0, 3)] == 1 and dense[3].sum() == 2


def test_both_bands_refused():
    """The link band replaces the node band (rule 19): both is an error."""

    class _Spec:
        def to_dispatch_kwargs(self):
            return {}

    with pytest.raises(ValueError):
        build_base_dispatch_kwargs(
            _Spec(),
            import_node_recon=(np.array([0]), np.zeros(1), np.zeros(1)),
            import_link_band=(np.array([0]), np.zeros((1, 1)), np.zeros((1, 1))),
        )


def test_flag_default_off_and_key_stable():
    """Default off; arming it moves the cache key, the default does not."""
    base = ScenarioConfig(iso="NYISO", mode="backcast")
    assert base.nyiso_import_landing_band is False
    armed = base.with_overrides(nyiso_import_landing_band=True)
    assert armed.cache_key() != base.cache_key()


def test_builder_on_measured_partition():
    """Each attributed zone's monthly energy lands on its own pooled link."""
    clean = pytest.importorskip("scripts.lib.clean_io")
    try:
        frame = clean.read_clean(
            "nyiso-interface-flows", iso="NYISO", year=2024, validate=False
        )
    except Exception:  # noqa: BLE001 — data-gated
        pytest.skip("nyiso-interface-flows 2024 partition not hydrated")
    from types import SimpleNamespace

    from market_sim.model.interchange.nyiso import build_nyiso_import_landing_band

    zones = ["Upstate_West", "Capital_Hudson", "NYC", "Long_Island"]
    cfg = SimpleNamespace(
        links=[SimpleNamespace(from_zone="Upstate_West", to_zone="Capital_Hudson")]
        + [SimpleNamespace(from_zone="NYISO_external", to_zone=z) for z in zones]
    )
    idx, lo, hi = build_nyiso_import_landing_band(
        cfg, 2024, 8760, exclude_rows=("SCH - NE - NY",), frame=frame
    )
    assert 0 not in idx.tolist()
    assert sorted(cfg.links[i].to_zone for i in idx) == [
        "Capital_Hudson",
        "Long_Island",
        "NYC",
        "Upstate_West",
    ]
    assert lo.shape == (4, 12) and np.all(hi >= lo)
    assert 20.0 < ((lo + hi) / 2).sum() / 1e6 < 35.0  # pooled TWh, P-32 basis
