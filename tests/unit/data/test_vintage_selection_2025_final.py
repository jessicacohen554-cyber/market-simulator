"""W0 E.8 / E.2: the solved year reads its own Final vintage; forecasts never do."""

from __future__ import annotations

from pathlib import Path

from market_sim.config import paths
from market_sim.config.scenarios import ScenarioConfig

REPO = Path(__file__).resolve().parents[3]


def test_2025_backcast_resolves_vintage_2025_when_present():
    cfg = ScenarioConfig(mode="backcast")
    year = paths.resolve_backcast_eia860_vintage(
        cfg.eia860_vintage_year, 2025, cfg.eia860_vintage_tracks_solve_year
    )
    assert year == 2025
    prior = paths.active_eia860_dir()
    try:
        resolved = paths.set_eia860_vintage(year)
        expected = paths.EIA_860_DIR / "vintage_2025"
        assert resolved == (expected if expected.is_dir() else paths.EIA_860_DIR)
    finally:
        paths.restore_eia860_dir(prior)


def test_year_without_a_vintage_falls_to_the_canonical_snapshot():
    prior = paths.active_eia860_dir()
    try:
        assert paths.set_eia860_vintage(2099) == paths.EIA_860_DIR
    finally:
        paths.restore_eia860_dir(prior)


def test_forecast_never_reads_a_vintage():
    for kwargs in ({"mode": "forecast"}, {"mode": "forecast", "hindcast": True}):
        cfg = ScenarioConfig(**kwargs, eia860_vintage_tracks_solve_year=True)
        assert cfg.eia860_vintage_tracks_solve_year is False
        assert (
            paths.resolve_backcast_eia860_vintage(
                cfg.eia860_vintage_year, 2025, cfg.eia860_vintage_tracks_solve_year
            )
            is None
        )


def test_eia860m_has_no_backcast_consumer():
    """860M is a forecast-only layer (audit §E.2): nothing on the model path reads it."""
    hits = [
        p.relative_to(REPO)
        for p in (REPO / "src").rglob("*.py")
        if "eia-860m" in p.read_text() or "eia860m" in p.read_text()
    ]
    assert all("forecast" in str(h) for h in hits), hits
