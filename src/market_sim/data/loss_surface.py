"""Loader for the per-ISO marginal delivery-factor (loss) surfaces.

Reads the committed derive artifact for the requested ISO and hands the LP
builder plain per-zone monthly deviation arrays (struct-of-arrays, rule #6):

* ``data/raw/iso-specific-transmission/MISO_loss_surface.csv`` — the frozen
  ``scripts/data/derive_miso_loss_surface.py`` (miso-76 charter
  ``docs/handoffs/miso-nc-price-separation-design-2026-07.md`` §4);
* ``data/raw/iso-specific-transmission/PJM_loss_surface.csv`` — the frozen
  ``scripts/data/derive_pjm_loss_surface.py`` (pjm-136 charter
  ``results/calibration/FINDING-pjm136-zonal-dual-structure-2026-07-28.md``).

**One file per ISO, never one shared file** (rule 25 ``[R-ISO-SCOPE]``): each
surface is derived from that ISO's own published LMP component record and its
values may never cross a market boundary. The loader resolves the path from the
``iso`` argument, so an ISO with no derive artifact fails loud rather than
silently reading another market's numbers.

Year resolution: a year with its own rows (a train-window backcast year)
uses them — the same-year measured physical network property, the CEMS-rate
admissibility class; any other year (every forecast year) falls back to the
pooled ``year = 0`` rows — the stable multi-year surface that regenerates
from rolling history (the forward analogue). Deterministic and
mode-independent.
"""

from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path

from market_sim.config.paths import ISO_TRANSMISSION_DIR

# The per-ISO derive artifacts, one module constant each so a test can patch a
# single market's surface without touching another's (the miso-76 tests do
# exactly this). :func:`surface_path` resolves the constant for an ISO.
SURFACE_PATH = ISO_TRANSMISSION_DIR / "MISO_loss_surface.csv"
PJM_SURFACE_PATH = ISO_TRANSMISSION_DIR / "PJM_loss_surface.csv"

# ISO -> the derive script that regenerates its surface (used in error text).
_DERIVE_SCRIPT = {
    "MISO": "scripts/data/derive_miso_loss_surface.py",
    "PJM": "scripts/data/derive_pjm_loss_surface.py",
    "CAISO": "scripts/data/derive_caiso_loss_surface.py",
}

# Pooled-surface sentinel year (matches the derives' POOLED_YEAR).
_POOLED_YEAR = 0

_N_MONTHS = 12


def surface_path(iso: str) -> Path:
    """Return the derive-artifact path for ``iso`` (one file per market)."""
    iso = iso.upper()
    if iso == "MISO":
        return SURFACE_PATH
    if iso == "PJM":
        return PJM_SURFACE_PATH
    return ISO_TRANSMISSION_DIR / f"{iso}_loss_surface.csv"


@lru_cache(maxsize=8)
def load_zone_month_deviation(iso: str, year: int) -> dict[str, tuple[float, ...]]:
    """Return each zone's monthly delivery-factor deviations for ``year``.

    Args:
        iso: ISO identifier. Each ISO reads its OWN ``<ISO>_loss_surface.csv``
            (rule 25 ``[R-ISO-SCOPE]`` — a surface is derived from that
            market's published components and never crosses a boundary);
            ``MISO``, ``PJM`` and ``CAISO`` have one.
        year: Simulation year. Resolved to the year's own rows when the
            surface carries them, else the pooled ``year = 0`` rows
            (module docstring).

    Returns:
        Mapping ``zone -> 12 monthly dimensionless deviations`` (Jan..Dec).

    Raises:
        FileNotFoundError: When the ISO's derive artifact is absent
            (regenerate with that ISO's derive script).
        ValueError: When neither the year's rows nor pooled rows exist, or
            a zone's month vector is incomplete (fail loud, never guess).
    """
    iso = iso.upper()
    path = surface_path(iso)
    if not path.is_file():
        script = _DERIVE_SCRIPT.get(iso, f"the {iso} loss-surface derive")
        raise FileNotFoundError(f"no loss surface at {path} — regenerate with {script}")
    rows_by_year: dict[int, dict[str, dict[int, float]]] = {}
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["iso"].upper() != iso:
                continue
            y = int(row["year"])
            rows_by_year.setdefault(y, {}).setdefault(row["zone"], {})[
                int(row["month"])
            ] = float(row["df_deviation"])
    if not rows_by_year:
        raise ValueError(f"loss surface {path} carries no {iso} rows")
    zones = rows_by_year.get(year) or rows_by_year.get(_POOLED_YEAR)
    if zones is None:
        raise ValueError(
            f"loss surface has neither year-{year} nor pooled rows for {iso}"
        )
    out: dict[str, tuple[float, ...]] = {}
    for zone, months in zones.items():
        if sorted(months) != list(range(1, _N_MONTHS + 1)):
            raise ValueError(
                f"loss surface {zone} ({iso}, year {year}) is missing months: "
                f"have {sorted(months)}"
            )
        out[zone] = tuple(months[m] for m in range(1, _N_MONTHS + 1))
    return out
