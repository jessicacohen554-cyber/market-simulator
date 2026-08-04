"""Tests for the NYISO external-seam deliverability envelope (nyiso-125).

Covers the three properties the mechanism's legitimacy rests on:

* it caps **only** the two links whose ties land unambiguously in one NYISO
  load zone, and leaves the two refused on identification untouched;
* the cap is **directional** and **hourly**, and never exceeds the incumbent
  rating (the monotonicity guard);
* it **never silently no-ops** — a missing clean partition raises rather than
  leaving the run claiming a measured input it never read (the pjm-119 lesson).

The hermetic tests build a synthetic posting; the ``fulldata`` test checks the
real committed partitions reproduce the pre-registered MW figures.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import NYISO_SEAM_FLOW_PERCENTILE
from market_sim.data.nyiso_seam_envelope import (
    NYISO_SEAM_ACCOUNTING_DUPLICATE,
    NYISO_SEAM_TIE_LANDING,
    nyiso_seam_ttc_hourly,
    seam_envelope_by_zone,
)

HOURS = 8760


def _synthetic_posting(level: dict[str, float]) -> pd.DataFrame:
    """Return a flat-flow posting frame carrying ``level`` MW on each tie."""
    stamps = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    rows = []
    for tie, mw in level.items():
        rows.append(
            pd.DataFrame(
                {
                    "interval_start_local": stamps,
                    "interface": tie,
                    "flow_mw": float(mw),
                }
            )
        )
    return pd.concat(rows, ignore_index=True)


ALL_TIES = {t for ties in NYISO_SEAM_TIE_LANDING.values() for t in ties}


class _Link:
    def __init__(self, from_zone: str, to_zone: str, ttc_mw: float) -> None:
        self.from_zone, self.to_zone, self.ttc_mw = from_zone, to_zone, ttc_mw


class _Config:
    """Minimal ISOConfig stand-in — the module only reads ``links``."""

    def __init__(self, links: list[_Link]) -> None:
        self.links = links


def _nyiso_links() -> list[_Link]:
    return [
        _Link("Upstate_West", "Capital_Hudson", 2850.0),
        _Link("NYISO_external", "Upstate_West", 3000.0),
        _Link("NYISO_external", "Capital_Hudson", 1600.0),
        _Link("NYISO_external", "NYC", 1000.0),
        _Link("NYISO_external", "Long_Island", 1200.0),
    ]


def test_flat_import_gives_that_import_and_zero_export():
    """A constant import schedule envelopes to itself, with no export leg."""
    frame = _synthetic_posting({t: 100.0 for t in ALL_TIES})
    env = seam_envelope_by_zone(frame, HOURS, NYISO_SEAM_FLOW_PERCENTILE)
    assert set(env) == set(NYISO_SEAM_TIE_LANDING)
    imp_nyc, exp_nyc = env["NYC"]
    # NYC hosts two ties at 100 MW each.
    assert np.allclose(imp_nyc, 200.0)
    assert np.allclose(exp_nyc, 0.0)
    # Long_Island hosts three.
    imp_li, exp_li = env["Long_Island"]
    assert np.allclose(imp_li, 300.0)
    assert np.allclose(exp_li, 0.0)


def test_export_schedule_populates_the_export_leg_only():
    """A constant EXPORT schedule envelopes onto the reverse direction."""
    frame = _synthetic_posting({t: -50.0 for t in ALL_TIES})
    env = seam_envelope_by_zone(frame, HOURS, NYISO_SEAM_FLOW_PERCENTILE)
    imp, exp = env["NYC"]
    assert np.allclose(imp, 0.0)
    assert np.allclose(exp, 100.0)


def test_only_the_identified_links_are_capped():
    """Upstate_West / Capital_Hudson keep their statics; internal links too."""
    frame = _synthetic_posting({t: 10.0 for t in ALL_TIES})
    cfg = _Config(_nyiso_links())
    static = np.array([ln.ttc_mw for ln in cfg.links], dtype=float)
    ttc, ttc_import = _run(frame, static, cfg)

    by_zone = {ln.to_zone: i for i, ln in enumerate(cfg.links)}
    # Refused on identification — byte-unchanged, both directions.
    for zone in ("Upstate_West", "Capital_Hudson"):
        i = by_zone[zone]
        assert np.allclose(ttc[:, i], static[i])
        assert np.allclose(ttc_import[:, i], static[i])
    # Internal link untouched.
    i = by_zone["Capital_Hudson"]
    assert np.allclose(ttc[:, i], static[i])
    # Identified — capped to the measured envelope, export closed.
    assert np.allclose(ttc[:, by_zone["NYC"]], 20.0)
    assert np.allclose(ttc_import[:, by_zone["NYC"]], 0.0)
    assert np.allclose(ttc[:, by_zone["Long_Island"]], 30.0)


def test_envelope_never_exceeds_the_incumbent_rating():
    """The monotonicity guard: a deliverability envelope cannot beat the rating."""
    # 5,000 MW per tie is far above either static rating.
    frame = _synthetic_posting({t: 5000.0 for t in ALL_TIES})
    cfg = _Config(_nyiso_links())
    static = np.array([ln.ttc_mw for ln in cfg.links], dtype=float)
    ttc, _ = _run(frame, static, cfg)
    by_zone = {ln.to_zone: i for i, ln in enumerate(cfg.links)}
    assert np.allclose(ttc[:, by_zone["NYC"]], 1000.0)
    assert np.allclose(ttc[:, by_zone["Long_Island"]], 1200.0)


def test_envelope_is_hourly_and_directional():
    """Different (month x hour-of-day) bins get different caps."""
    stamps = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    # 900 MW in hour 18, 100 MW otherwise — one tie, so NYC sees it directly.
    flow = np.where(stamps.hour == 18, 900.0, 100.0)
    frame = pd.concat(
        [
            pd.DataFrame(
                {
                    "interval_start_local": stamps,
                    "interface": tie,
                    "flow_mw": flow if tie == "SCH - PJM_HTP" else 0.0,
                }
            )
            for tie in ALL_TIES
        ],
        ignore_index=True,
    )
    env = seam_envelope_by_zone(frame, HOURS, NYISO_SEAM_FLOW_PERCENTILE)
    imp, _ = env["NYC"]
    cal = pd.date_range("2023-01-01", periods=HOURS, freq="h")
    assert np.allclose(imp[cal.hour == 18], 900.0)
    assert np.allclose(imp[cal.hour == 3], 100.0)


def test_accounting_duplicate_is_not_read():
    """SCH - HQ_IMPORT_EXPORT names no tie any landing zone reads."""
    assert NYISO_SEAM_ACCOUNTING_DUPLICATE not in ALL_TIES


def test_missing_partition_raises_rather_than_no_opping(monkeypatch):
    """The mechanism never silently keeps the static TTC (pjm-119 lesson)."""
    import scripts.lib.clean_io as clean_io

    monkeypatch.setattr(clean_io, "read_clean", lambda *a, **k: None)
    cfg = _Config(_nyiso_links())
    static = np.array([ln.ttc_mw for ln in cfg.links], dtype=float)
    with pytest.raises(FileNotFoundError, match="never silently no-ops"):
        nyiso_seam_ttc_hourly(static, cfg, 2023, HOURS)


def _run(frame, static, cfg):
    """Call the overlay with ``frame`` standing in for the clean partition."""
    import scripts.lib.clean_io as clean_io

    original = clean_io.read_clean
    clean_io.read_clean = lambda *a, **k: frame
    try:
        return nyiso_seam_ttc_hourly(static, cfg, 2023, HOURS)
    finally:
        clean_io.read_clean = original


@pytest.mark.fulldata
@pytest.mark.integration
@pytest.mark.parametrize(
    ("year", "nyc_cut", "li_cut"),
    [(2023, 94.6, 212.3), (2024, 177.9, 228.4), (2025, 97.0, 271.5)],
)
def test_committed_partitions_reproduce_the_prereg_figures(year, nyc_cut, li_cut):
    """The real postings give the MW removed pre-registered before the solve.

    PREREG-nyiso125-seam-envelope-2026-08-04.md §3. A drift here means the
    source data changed — which is the ONLY admissible reason for these
    numbers to move (rule 23 ``[R-FROZEN-DERIVE]``).
    """
    pytest.importorskip("pyarrow")
    cfg = _Config(_nyiso_links())
    static = np.array([ln.ttc_mw for ln in cfg.links], dtype=float)
    try:
        ttc, _ = nyiso_seam_ttc_hourly(static, cfg, year, HOURS)
    except FileNotFoundError as exc:
        pytest.skip(f"nyiso-interface-flows clean partition absent: {exc}")
    by_zone = {ln.to_zone: i for i, ln in enumerate(cfg.links)}
    got_nyc = float(np.clip(1000.0 - ttc[:, by_zone["NYC"]], 0.0, None).mean())
    got_li = float(np.clip(1200.0 - ttc[:, by_zone["Long_Island"]], 0.0, None).mean())
    assert got_nyc == pytest.approx(nyc_cut, abs=0.5)
    assert got_li == pytest.approx(li_cut, abs=0.5)
