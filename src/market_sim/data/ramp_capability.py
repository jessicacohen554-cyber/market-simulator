"""Read the curated ``ramp-capability`` clean datatype and reconcile it to a
per-plant 10-minute ramp fraction.

The model's *consumption seam* for the measured ramp/fast-start capability
intake (``scripts/lib/ramp_capability`` → ``data/clean/ramp-capability``),
consumed by :func:`market_sim.data.fleet._ramp10_capability` when
``ScenarioConfig.measured_ramp_capability`` is on (GATED, default off).

Two measured public quantities per plant, and one documented reconciliation:

* ``fast_start_mw`` — EIA-860 Schedule 3.1 ``Time from Cold Shutdown to Full
  Load`` = ``"10M"`` thermal nameplate: capacity the respondent reports as
  reaching full load within 10 minutes, i.e. deliverable inside a 10-minute
  reserve window from any state (PJM Manual 11 non-synchronized primary
  reserve; MISO BPM-002 §2.2 offline Supplemental).
* ``ramp_up_1h_mw`` — CAMPD CEMS maximum observed 1-hour increase in plant
  gross load (pooled 2023-2025). CEMS is hourly, so this is **not** a
  10-minute quantity; it is the measured *ceiling* on any sustained hourly
  move the plant has ever made.

Reconciliation (:func:`measured_ramp10_frac`), per CLAUDE.md rule 14 —
measured data preferred, misalignment reconciled explicitly rather than used
literally:

    ramp10_frac = clip( max( fast_start_mw / basis,
                             min( class_frac, ramp_up_1h_mw / basis ) ),
                        0, 1 )
    basis       = max( thermal_nameplate_mw, observed_pmax_mw )

* the NREL/EIA class 10-minute rate (``fleet.RAMP10_FRAC_BY_GROUP``, the
  prior estimate) supplies the sub-hourly rate *shape* CEMS cannot resolve;
* the measured hourly envelope CAPS it — a 10-minute sustained move cannot
  exceed the largest hourly move the plant has demonstrated (reserve
  products require sustained delivery: PJM primary reserve ~30 min, MISO
  contingency reserve 30-90 min, so the hourly envelope is the right
  ceiling, never a credit);
* the measured EIA-860 fast-start capacity FLOORS it — capacity reported as
  full-load-in-10-minutes is deliverable regardless of the class rate.

The envelope is trusted only with ≥ :data:`MIN_OBSERVED_HOURS` plant-hours of
CEMS coverage (the class-fallback threshold convention of
``docs/ramp-locational-design-2026-07.md`` §1.3); below it, only the
fast-start floor applies. Plants absent from the clean partition fall back to
the class fraction unchanged. Everything regenerates for a forecast year
(EIA-860 categories and CEMS envelopes are physical constants of the machine;
new entrants take the class fraction) and nothing reads a price or volume
residual — rule 13 admissible, rule 24 frozen against residuals.

Only the reader lives here. The clean tree is derived/gitignored, so a
missing partition yields an empty dict with a warning rather than an error —
the caller degrades to the class-fraction estimate.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

DATATYPE = "ramp-capability"

# Minimum pooled CEMS plant-hours before the hourly envelope is trusted as a
# ceiling; below it the plant keeps the class rate (the ~4,000-hour
# class-fallback threshold of docs/ramp-locational-design-2026-07.md §1.3).
MIN_OBSERVED_HOURS: int = 4000


@dataclass(frozen=True)
class PlantRampCapability:
    """Measured ramp-capability quantities for one plant (schema row)."""

    fast_start_mw: float  # EIA-860 "10M" thermal nameplate (NaN = no EIA rows)
    thermal_nameplate_mw: float  # EIA-860 thermal nameplate (NaN = no EIA rows)
    ramp_up_1h_mw: float  # CEMS max 1-h up-ramp (NaN = no CEMS coverage)
    observed_pmax_mw: float  # CEMS max plant gross load (NaN = no CEMS coverage)
    hours_observed: int  # pooled CEMS plant-hours (0 = no CEMS coverage)


def load_measured_ramp_capability(iso: str) -> dict[int, PlantRampCapability]:
    """Load the ISO's measured ramp-capability rows keyed by plant code.

    Returns an empty dict (with a warning) when the clean partition is
    absent — callers gate on ``ScenarioConfig.measured_ramp_capability`` and
    degrade to the class-fraction estimate.
    """
    try:
        from scripts.lib.clean_io import read_clean

        df = read_clean(DATATYPE, iso=str(iso).upper())
    except FileNotFoundError:
        logger.warning(
            "measured_ramp_capability: no clean ramp-capability partition for "
            "%s (run scripts/regenerate_clean.py ramp-capability); falling "
            "back to class ramp fractions",
            iso,
        )
        return {}
    out: dict[int, PlantRampCapability] = {}
    for row in df.itertuples(index=False):
        out[int(row.plant_code)] = PlantRampCapability(
            fast_start_mw=float(row.fast_start_mw)
            if row.fast_start_mw == row.fast_start_mw
            else float("nan"),
            thermal_nameplate_mw=float(row.thermal_nameplate_mw)
            if row.thermal_nameplate_mw == row.thermal_nameplate_mw
            else float("nan"),
            ramp_up_1h_mw=float(row.ramp_up_1h_mw)
            if row.ramp_up_1h_mw == row.ramp_up_1h_mw
            else float("nan"),
            observed_pmax_mw=float(row.observed_pmax_mw)
            if row.observed_pmax_mw == row.observed_pmax_mw
            else float("nan"),
            hours_observed=int(row.hours_observed),
        )
    return out


def measured_ramp10_frac(class_frac: float, cap: PlantRampCapability) -> float:
    """Reconcile one plant's measured quantities to a 10-minute ramp fraction.

    See the module docstring for the formula and its rationale. ``class_frac``
    is the plant's class 10-minute fraction (``fleet.RAMP10_FRAC_BY_GROUP`` /
    ``_BY_FUEL``), the estimate the measurement refines. The returned fraction
    multiplies unit pmax (the same convention as the class maps), so a
    plant-level measurement distributes pro-rata across the plant's LP
    tranches — exactly how the class fractions already apply, and exact under
    the per-plant/pooled reserve-column aggregation (members are summed).
    """
    # Measured capacity basis (guards stale nameplate vs derate/uprate).
    candidates = [
        v
        for v in (cap.thermal_nameplate_mw, cap.observed_pmax_mw)
        if np.isfinite(v) and v > 0.0
    ]
    if not candidates:
        return float(class_frac)
    basis = max(candidates)
    slow_frac = float(class_frac)
    if cap.hours_observed >= MIN_OBSERVED_HOURS and np.isfinite(cap.ramp_up_1h_mw):
        slow_frac = min(slow_frac, float(cap.ramp_up_1h_mw) / float(basis))
    fast_frac = 0.0
    if np.isfinite(cap.fast_start_mw):
        fast_frac = float(cap.fast_start_mw) / float(basis)
    return float(np.clip(max(fast_frac, slow_frac), 0.0, 1.0))
