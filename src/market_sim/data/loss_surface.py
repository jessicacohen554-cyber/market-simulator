"""Loader for the MISO marginal delivery-factor (loss) surface.

Reads the committed derive artifact
``data/raw/iso-specific-transmission/MISO_loss_surface.csv`` (produced by
the frozen ``scripts/data/derive_miso_loss_surface.py`` — miso-76 charter
``docs/handoffs/miso-nc-price-separation-design-2026-07.md`` §4) and hands
the LP builder plain per-zone monthly deviation arrays (struct-of-arrays,
rule #6).

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

from market_sim.config.paths import ISO_TRANSMISSION_DIR

# The derive artifact (see module docstring).
SURFACE_PATH = ISO_TRANSMISSION_DIR / "MISO_loss_surface.csv"

# Pooled-surface sentinel year (matches derive_miso_loss_surface.POOLED_YEAR).
_POOLED_YEAR = 0

_N_MONTHS = 12


@lru_cache(maxsize=8)
def load_zone_month_deviation(iso: str, year: int) -> dict[str, tuple[float, ...]]:
    """Return each zone's monthly delivery-factor deviations for ``year``.

    Args:
        iso: ISO identifier; only ``"MISO"`` has a surface (rule 24 — the
            surface is derived from MISO's own published components and
            never crosses an ISO boundary).
        year: Simulation year. Resolved to the year's own rows when the
            surface carries them, else the pooled ``year = 0`` rows
            (module docstring).

    Returns:
        Mapping ``zone -> 12 monthly dimensionless deviations`` (Jan..Dec).

    Raises:
        FileNotFoundError: When the derive artifact is absent (regenerate
            with ``scripts/data/derive_miso_loss_surface.py``).
        ValueError: When neither the year's rows nor pooled rows exist, or
            a zone's month vector is incomplete (fail loud, never guess).
    """
    iso = iso.upper()
    if not SURFACE_PATH.is_file():
        raise FileNotFoundError(
            f"no loss surface at {SURFACE_PATH} — regenerate with "
            "scripts/data/derive_miso_loss_surface.py"
        )
    rows_by_year: dict[int, dict[str, dict[int, float]]] = {}
    with SURFACE_PATH.open(newline="") as fh:
        for row in csv.DictReader(fh):
            if row["iso"].upper() != iso:
                continue
            y = int(row["year"])
            rows_by_year.setdefault(y, {}).setdefault(row["zone"], {})[
                int(row["month"])
            ] = float(row["df_deviation"])
    if not rows_by_year:
        raise ValueError(f"loss surface {SURFACE_PATH} carries no {iso} rows")
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
