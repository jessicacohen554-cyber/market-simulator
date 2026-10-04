"""Synthetic Figure-30 CSV for the PJM Elliott overlay tests (no data/raw dependency)."""

from __future__ import annotations

from pathlib import Path

from scripts.data.digitise_pjm_elliott_forced_outages import BAR_TIMES

FUELS = ("gas", "coal", "oil", "nuclear", "hydro", "other")


def write_fixture_csv(path: Path) -> Path:
    """Write the real bar clock with hand-checkable MW (gas rising 1 GW per bar) and return it."""
    rows = ["hour_beginning_ept,fuel,forced_outage_mw,bar_total_mw"]
    for i, t in enumerate(BAR_TIMES):
        mw = {"gas": 3000.0 + 1000.0 * i, "coal": 8000.0 + 100.0 * i}
        total = sum(mw.get(f, 100.0) for f in FUELS)
        rows += [f"{t},{f},{mw.get(f, 100.0)},{total}" for f in FUELS]
    path.write_text("\n".join(rows) + "\n")
    return path
