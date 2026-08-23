"""Tests for the miso-180 anchored SPREAD-ONLY dispersion graft.

The PREREG-miso180 §5 unit-test set: raise-only, rank preservation, scope
exclusion, anchor-below untouched, artifact-hash consumption, zero-affected
hard-error, and the two inertness seams (gate off; armed on a non-MISO
config). Fixtures build the REAL :class:`market_sim.data.fleet.Generator`
and :class:`market_sim.data.fleet.FleetArrays` (the miso-151 lesson: a
stand-in namespace can encode the same wrong attribute assumption as the
code and never fail).

The expected graft values are recomputed IN-TEST from the committed artifact
and the measured G_ref CSVs with an independent reimplementation of the
frozen estimator, so the test adjudicates the formula, not the code against
itself.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import market_sim.data.offer_curves as oc
from market_sim.config.constants import (
    MISO_OFFER_SPREAD_ANCHOR_RANK,
    MISO_OFFER_SPREAD_ARTIFACT_SHA256,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays, Generator
from market_sim.data.offer_curves import apply_miso_offer_spread_anchored

REPO = Path(__file__).resolve().parents[3]
ARTIFACT = REPO / "data/raw/_validation-source/miso_offer_level_dispersion.json"

YEAR = 2025
T = 24  # January hours only — one month exercised, G_ref loads all twelve


def _gen(label: str, cap: float, plant: int = 1, group: str = "CT_PEAKER") -> Generator:
    """One CAMPD-style tranche row of a MISO plant."""
    return Generator(
        unit_id=f"p{plant}_{label}",
        name=label,
        zone="MISO-East",
        fuel_type="gas",
        pmax_mw=cap,
        heat_rate=9.0,
        plant_code=plant,
        plant_group=group,
        bin_label=f"X_{label}",
    )


def _arrays(gens: list[Generator]) -> FleetArrays:
    """A minimal REAL FleetArrays whose ``pmax`` mirrors the generators."""
    n = len(gens)
    return FleetArrays(
        pmax=np.array([g.pmax_mw for g in gens], dtype=float),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 9.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.zeros(n, dtype=int),
        availability=np.ones((n, T)),
        unit_ids=[g.unit_id for g in gens],
        efficiency_bin=np.array([g.plant_group for g in gens], dtype=object),
        plant_code=np.array([g.plant_code for g in gens], dtype=int),
    )


def _cfg(iso: str = "MISO", armed: bool = True) -> ScenarioConfig:
    return ScenarioConfig(iso=iso, mode="backcast").with_overrides(
        miso_offer_spread_anchored=armed
    )


@pytest.fixture(autouse=True)
def _clear_cache():
    """The artifact cache is module-global; isolate every test."""
    oc._MISO_SPREAD_CACHE.clear()
    yield
    oc._MISO_SPREAD_CACHE.clear()


def _expected_targets(mc_m: np.ndarray, pmax: np.ndarray) -> tuple[np.ndarray, float]:
    """Independent reimplementation of the frozen graft targets for month 1.

    Returns (per-tranche target where above-anchor else -inf, A_m).
    """
    art = json.loads(ARTIFACT.read_text())
    grid = np.asarray(art["quantile_grid"], float)
    vec = np.asarray(art["pooled"]["quantiles_mmbtu_per_mwh"], float)
    a = float(MISO_OFFER_SPREAD_ANCHOR_RANK)
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh = hh[hh["year"] == YEAR].set_index("month")["price_usd_mmbtu"]
    bs = pd.read_csv(REPO / "data/raw/gas_basis_by_iso_month.csv")
    bs = bs[(bs["iso"] == "MISO") & (bs["year"] == YEAR)].set_index("month")
    gref_jan = float(hh.loc[1]) + float(bs.loc[1, "basis_usd_mmbtu"])

    order = np.argsort(mc_m, kind="stable")
    w = pmax[order]
    cum = np.cumsum(w)
    mid = (cum - 0.5 * w) / cum[-1]
    r = np.empty_like(mid)
    r[order] = mid
    idx = int(np.clip(np.searchsorted(cum / cum[-1], a), 0, mc_m.size - 1))
    a_m = float(mc_m[order][idx])
    q_a = float(np.interp(a, grid, vec))
    tgt = np.full(mc_m.size, -np.inf)
    above = r > a
    tgt[above] = a_m + np.clip(
        (np.interp(r[above], grid, vec) - q_a) * gref_jan, 0.0, None
    )
    return tgt, a_m


def _toy_fleet(n_affected: int = 8):
    """n equal-cap econ tranches (rising mc) + one committed + one nuclear."""
    gens = [_gen(f"econ{i:02d}", 100.0, plant=i + 1) for i in range(n_affected)]
    gens.append(_gen("committed", 100.0, plant=90))
    gens.append(_gen("econ99", 100.0, plant=91, group="NUCLEAR"))
    mc = np.vstack(
        [np.full(T, 20.0 + 10.0 * i) for i in range(n_affected)]
        + [np.full(T, 15.0), np.full(T, 5.0)]
    )
    return gens, _arrays(gens), mc


def test_pinned_artifact_digest_matches_disk():
    """The committed artifact is byte-identical to the pinned identification."""
    assert (
        hashlib.sha256(ARTIFACT.read_bytes()).hexdigest()
        == MISO_OFFER_SPREAD_ARTIFACT_SHA256
    )


def test_off_is_byte_identical():
    gens, arrays, mc = _toy_fleet()
    before = mc.copy()
    apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(armed=False), YEAR)
    np.testing.assert_array_equal(mc, before)


def test_other_iso_untouched_when_armed():
    """Rule 25 seam: the graft is MISO's; an armed non-MISO config is inert."""
    gens, arrays, mc = _toy_fleet()
    before = mc.copy()
    apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(iso="ERCOT"), YEAR)
    np.testing.assert_array_equal(mc, before)


def test_graft_matches_frozen_formula_and_below_anchor_untouched():
    """Above-anchor rows = max(mc, A_m + rise); everything else untouched."""
    gens, arrays, mc = _toy_fleet()
    before = mc.copy()
    apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(), YEAR)

    n_aff = 8
    tgt, _a_m = _expected_targets(before[:n_aff, 0], arrays.pmax[:n_aff])
    # Equal 100-MW tranches -> midpoint ranks (i+0.5)/8; anchor 0.875 leaves
    # exactly the top tranche (rank 0.9375) above it.
    assert np.isfinite(tgt).sum() == 1
    for i in range(n_aff):
        if np.isfinite(tgt[i]):
            np.testing.assert_allclose(mc[i], np.maximum(before[i], tgt[i]))
            assert np.all(mc[i] >= before[i]), "the graft must be raise-only"
        else:
            np.testing.assert_array_equal(mc[i], before[i])
    # Scope exclusion: the committed band and the non-matching class are
    # untouched even though their ranks are irrelevant.
    np.testing.assert_array_equal(mc[n_aff], before[n_aff])
    np.testing.assert_array_equal(mc[n_aff + 1], before[n_aff + 1])


def test_rank_preservation_within_affected_stack():
    """Month-mean order of the affected stack survives the graft."""
    gens, arrays, mc = _toy_fleet()
    apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(), YEAR)
    month_mean = mc[:8].mean(axis=1)
    assert np.all(np.diff(month_mean) >= -1e-12)


def test_artifact_sha_mismatch_hard_errors(monkeypatch):
    gens, arrays, mc = _toy_fleet()
    monkeypatch.setattr(oc, "MISO_OFFER_SPREAD_ARTIFACT_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="sha256"):
        apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(), YEAR)


def test_zero_affected_tranches_hard_errors():
    gens = [_gen("committed", 100.0, plant=1)]
    arrays = _arrays(gens)
    mc = np.full((1, T), 15.0)
    with pytest.raises(ValueError, match="zero .*affected|affected .*tranches"):
        apply_miso_offer_spread_anchored(mc, gens, arrays, _cfg(), YEAR)
