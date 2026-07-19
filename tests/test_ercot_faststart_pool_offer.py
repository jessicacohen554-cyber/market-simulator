"""Trivial-case tests for the ERCOT-88 offline fast-start pool offer.

Covers :func:`market_sim.data.fleet.build_ercot_faststart_pool_markup`
(``ScenarioConfig.ercot_faststart_pool_offer``): pool-without-wall hard error,
bin-geometry-mismatch hard error, the physics eligibility gate (min_down <=
FASTSTART_POOL_MIN_DOWN_HOURS — a slow row above the boundary is never
priced), boundary scoping (rows at/below the measured pool boundary are never
touched), row-family scoping (econ*/peak* only — committed/mustrun rows stay
with their floor structure), bin-window scoping via the returned own_mask,
year-scoping (a year absent from the artifact returns None — no pooled
fallback), and VOLL capping. Plus artifact-level checks on the committed
derive output: shared bin geometry with the wall artifacts, year-scoped (no
pooled key), pool_frac in (0, 1), and the above-LSL invariant (no negative
ladder rung — the below-LSL min-gen curve bottoms are excluded by
construction).
"""

import json
from pathlib import Path

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    build_ercot_faststart_pool_markup,
)

T = 48
REPO = Path(__file__).resolve().parents[1]


class _FA:
    """Minimal FleetArrays stand-in (the builder only reads ``pmax``)."""

    def __init__(self, pmax):
        self.pmax = np.asarray(pmax, dtype=float)


def _gen(
    unit_id: str,
    pmax: float,
    hr: float,
    group: str = "CT_PEAKER",
    min_down: int = 1,
):
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z",
        fuel_type="gas_ct",
        efficiency_bin=group,
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=hr,
        vom=2.0,
        emission_rate_co2=0.5,
        nox_rate=0.1,
        eford=0.05,
        online_year=2000,
        plant_group=group,
        plant_code=1,
        min_down_hours=min_down,
    )


def _fleet():
    """One CT plant: econhi 85 / peak 15 (mids 0.425 / 0.925)."""
    gens = [
        _gen("p1_econhi", 85.0, 11.0),
        _gen("p1_peak", 15.0, 12.0),
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
    net_load = np.linspace(0.0, 100.0, T)  # first half bin 0, second half bin 1
    return fa, gens, mc, net_load


def _wall_surface(tmp_path, edges=(0.5,)):
    """Minimal DAM cleared-share artifact (the geometry cross-check target)."""
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "ladder_quantiles": [0.1, 0.9],
        }
    }
    p = tmp_path / "surface_dam.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _pool_surface(
    tmp_path,
    pool_frac=(0.2, 0.2),
    mults=((300.0, 500.0), (300.0, 500.0)),
    year="2024",
    edges=(0.5,),
    quantiles=(0.1, 0.9),
):
    surf = {
        "_provenance": {
            "netload_pct_edges": list(edges),
            "ladder_quantiles": list(quantiles),
        },
        "CT": {
            "years": {
                year: {
                    "pool_frac": list(pool_frac),
                    "ladder": [
                        [[quantiles[0], m[0]], [quantiles[-1], m[1]]] for m in mults
                    ],
                }
            }
        },
    }
    p = tmp_path / "surface_pool.json"
    p.write_text(json.dumps(surf))
    return str(p)


def _cfg(tmp_path, pool_path, **overrides):
    kwargs = dict(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_offer_surface_cleared_share=True,
        ercot_offer_surface_cleared_share_path=_wall_surface(tmp_path),
        ercot_faststart_pool_offer=True,
        ercot_faststart_pool_offer_path=pool_path,
    )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def test_pool_without_wall_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = ScenarioConfig(
        iso="ERCOT",
        mode="backcast",
        weather_year=2024,
        ercot_faststart_pool_offer=True,
        ercot_faststart_pool_offer_path=_pool_surface(tmp_path),
    )
    with pytest.raises(ValueError, match="cleared-share"):
        build_ercot_faststart_pool_markup(fa, gens, mc, nl, cfg, 2024)


def test_geometry_mismatch_is_hard_error(tmp_path):
    fa, gens, mc, nl = _fleet()
    pool = _pool_surface(
        tmp_path, edges=(0.25, 0.5), pool_frac=(0.2,) * 3, mults=((1.0, 2.0),) * 3
    )
    cfg = _cfg(tmp_path, pool)  # wall artifact carries edges (0.5,)
    with pytest.raises(ValueError, match="edges"):
        build_ercot_faststart_pool_markup(fa, gens, mc, nl, cfg, 2024)


def test_prices_above_boundary_with_mask(tmp_path):
    """The peak row (mid 0.925 > boundary 0.8) is priced in measured bins."""
    fa, gens, mc, nl = _fleet()
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, _pool_surface(tmp_path)), 2024
    )
    assert out is not None
    markup, mask = out
    # econ row (mid 0.425 <= 0.8): never touched.
    assert markup[0].max() == 0.0 and not mask[0].any()
    # peak row: owned in every hour (both bins measured), positive markup
    # (target = mult x gas >> mc for mults 300-500).
    assert mask[1].all()
    assert (markup[1] > 0.0).all()


def test_bin_window_scoping(tmp_path):
    """A NaN bin is unmeasured: the mask (and markup) end at the bin edge."""
    fa, gens, mc, nl = _fleet()
    pool = _pool_surface(tmp_path, mults=((float("nan"), float("nan")), (300.0, 500.0)))
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, pool), 2024
    )
    assert out is not None
    markup, mask = out
    assert not mask[1][: T // 2].any() and markup[1][: T // 2].max() == 0.0
    assert mask[1][T // 2 :].all() and (markup[1][T // 2 :] > 0.0).all()


def test_physics_gate_excludes_slow_rows(tmp_path):
    """A min_down > 2h row above the boundary is never priced (rule 12)."""
    gens = [
        _gen("p1_econhi", 85.0, 11.0),
        _gen("p1_peak", 15.0, 12.0, min_down=4),  # slow: fails the gate
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 30.0), np.full(T, 80.0)])
    nl = np.linspace(0.0, 100.0, T)
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, _pool_surface(tmp_path)), 2024
    )
    assert out is None  # no eligible row above the boundary -> byte-identical


def test_row_family_scoping(tmp_path):
    """A committed row above the boundary stays with its floor structure."""
    gens = [
        _gen("p1_econ", 80.0, 9.0),  # mid 0.40
        _gen("p1_committed", 20.0, 13.0),  # mid 0.90 > boundary, wrong family
    ]
    fa = _FA([g.pmax_mw for g in gens])
    mc = np.vstack([np.full(T, 25.0), np.full(T, 60.0)])
    nl = np.linspace(0.0, 100.0, T)
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, _pool_surface(tmp_path)), 2024
    )
    assert out is None


def test_year_scoped_no_pooled_fallback(tmp_path):
    """A year absent from the artifact returns None (rule 13)."""
    fa, gens, mc, nl = _fleet()
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, _pool_surface(tmp_path, year="2025")), 2024
    )
    assert out is None


def test_gate_off_returns_none(tmp_path):
    fa, gens, mc, nl = _fleet()
    cfg = _cfg(tmp_path, _pool_surface(tmp_path), ercot_faststart_pool_offer=False)
    assert build_ercot_faststart_pool_markup(fa, gens, mc, nl, cfg, 2024) is None


def test_target_voll_capped(tmp_path):
    """An extreme pool ladder is capped at price_cap_frac x VOLL."""
    fa, gens, mc, nl = _fleet()
    pool = _pool_surface(tmp_path, mults=((1e6, 1e6),) * 2)
    out = build_ercot_faststart_pool_markup(
        fa, gens, mc, nl, _cfg(tmp_path, pool), 2024
    )
    assert out is not None
    markup, _ = out
    cap = 0.95 * 5000.0
    assert float((markup[1] + mc[1]).max()) <= cap + 1e-9


# ---------------------------------------------------------------------------
# Committed-artifact checks (the real derive output, when present)
# ---------------------------------------------------------------------------

_POOL_JSON = REPO / "data/raw/_validation-source/ercot_faststart_pool_condbinned.json"
_DAM_JSON = REPO / "data/raw/_validation-source/ercot_dam_cleared_share_condbinned.json"


@pytest.mark.skipif(not _POOL_JSON.exists(), reason="pool artifact not derived")
def test_artifact_shares_wall_bin_geometry():
    pool = json.loads(_POOL_JSON.read_text())
    dam = json.loads(_DAM_JSON.read_text())
    assert (
        pool["_provenance"]["netload_pct_edges"]
        == dam["_provenance"]["netload_pct_edges"]
    )
    assert (
        pool["_provenance"]["ladder_quantiles"]
        == dam["_provenance"]["ladder_quantiles"]
    )


@pytest.mark.skipif(not _POOL_JSON.exists(), reason="pool artifact not derived")
def test_artifact_is_year_scoped_above_lsl_and_sane():
    pool = json.loads(_POOL_JSON.read_text())
    assert "pooled" not in pool.get("CT", {}), (
        "pool artifact must not carry a pooled fallback"
    )
    for year, tbl in pool["CT"]["years"].items():
        for f in tbl["pool_frac"]:
            assert 0.0 < f < 1.0, f"{year}: pool_frac {f} out of (0,1)"
        for b, lad in enumerate(tbl["ladder"]):
            for _, m in lad:
                if m == m:  # finite
                    assert m >= 0.0, (
                        f"{year} bin {b}: negative rung {m} — the above-LSL "
                        "restriction must exclude the min-gen curve bottoms"
                    )
