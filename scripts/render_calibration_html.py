"""Render the multi-run interactive HTML calibration report from bundles.

Self-contained (no external JS/CSS). One HTML compares several calibration
runs (configs) with a top toggle between a cross-run **Summary** page and a
per-run **Detail** page, a **Zone** multi-select (all zones or any subset), and
a Year selector. Class aggregation, capture metrics and the comparison tables
all recompute client-side from embedded per-plant series so the zone filter is
live.

Two capture scores (each in [0,100]%, see :func:`_capture`):
  * **Class capture%** — geometric mean of the class-aggregate hourly r,
    (1-NRMSE) and (1-|annual deviation|) vs CAMPD: is the class total right in
    shape and level?
  * **Plant capture%** — capacity-weighted mean of each plant's own
    geometric-mean capture%: are the *right plants* running (merit order)?
    Stays low when the class total is right but generation is on the wrong
    plants, and rises only when a config fixes the per-plant allocation.

Summary page: capture gauges per run, a per-fuel delta-vs-EIA-930 table, a
fossil-class table (Δ / r / NRMSE vs CAMPD) and a plant Δ-vs-EIA-923 table
across runs (2025 excluded — EIA-923 incomplete), plus model-vs-CAMPD monthly
lines and an annual model/EIA/CAMPD bar by fuel class. Detail page keeps the
per-plant commitment heatmaps, dispatch profile, annual and monthly charts.

Per-plant hourly CF series are embedded base64 uint8 (0-100); the CAMPD
benchmark is embedded once and shared across runs. See
docs/calibration-report.md.

Usage:
    python scripts/render_calibration_html.py [LABEL=]BUNDLE ... [--out FILE]
    # each BUNDLE is one config (may hold several years); LABEL overrides the
    # run name shown in the toggle (default: the bundle directory name).
"""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import re
import sys
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rcf", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)
# The ORDC scarcity overlay deriver supplies the reference monthly-MAE /
# actual-RT / demand-weight implementations; the dashboard's display-only
# overlay series reuses them verbatim so its numbers match the deriver's
# stdout report (docs/ordc-overlay.md, "Reliability-deployment overlay").
_spec_ordc = importlib.util.spec_from_file_location(
    "ordc_overlay", str(REPO / "scripts" / "derive_ordc_overlay.py")
)
ordc = importlib.util.module_from_spec(_spec_ordc)
_spec_ordc.loader.exec_module(ordc)

from scripts.lib.bundle_io import bundle_input_path  # noqa: E402
from scripts.calibration_verdict import TAIL_THRESHOLD  # noqa: E402  # rubric §5 per-ISO tail $
from market_sim.config.plant_taxonomy import (  # noqa: E402
    LABELS,
    class_label,
    classes_for_fuel930,
    fossil_classes,
    nonfossil_classes,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import egrid  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    OTHER_FOSSIL_CLASS,
    apply_other_fossil_scoring,
    load_campd_bins,
)
from market_sim.data.offer_curves import plant_tranche_bands  # noqa: E402
from market_sim.results.calibration import (  # noqa: E402
    EIA930_SOURCE,
    actuals_source,
    signed_volume_error,
)

# All class groupings derive from the canonical taxonomy
# (market_sim.config.plant_taxonomy) — the single source of truth mapping model
# plant classes to EIA-930 fuel buckets and labels. Adding a class there flows
# through every table here automatically (no hardcoded class lists). The
# per-ISO filter (in build_payload) keeps only the classes an ISO dispatches.
_group_label = class_label  # known canonical name, else humanized
GROUP_LABEL = dict(LABELS)
_NONFOSSIL_KLASS = nonfossil_classes()
# OTHER_FOSSIL: the scoring bucket for genuinely-mixed gas-thermal plants
# (apply_other_fossil_scoring). Added to the fossil groups so the model side's
# `klass.isin(FOSSIL_GROUPS)` filter keeps it, matching the EIA-923 side.
FOSSIL_GROUPS = [*fossil_classes(), OTHER_FOSSIL_CLASS]
MIX_GROUPS = list(FOSSIL_GROUPS)
# OTHER_FOSSIL (the mixed gas-thermal reconciliation bucket) burns gas, so
# EIA-930 books it in the "gas" series — include it in the gas family that
# reconciles to the EIA-930 grid total, else its 923 generation double-counts
# against the grid total (the canonical gas classes would absorb its share AND
# it stays in the table). It is still excluded from the per-class merit GATE
# (calibration_verdict.FUELMIX_EXCLUDED) — that is a scoring choice, separate
# from the family grid-delivered reconciliation here.
_GAS_GROUPS = (*classes_for_fuel930("gas"), OTHER_FOSSIL_CLASS)
_COAL_GROUPS = classes_for_fuel930("coal")
# Grid-delivered benchmark reconciliation deadband (half-width ~3%). Each fossil
# family's grid-delivered EIA-923 total is reconciled to the complete EIA-930
# grid series — the same authority the model's gas/coal volume is scored on —
# in BOTH directions: scaled UP when a preliminary monthly 923 vintage
# under-counts thermal generation the CAMPD backfill can't fully repair, and
# scaled DOWN when the 923 plant total over-states grid delivery (residual CHP
# behind-the-meter + 923<->930 plant-to-BA assignment). A family already within
# +/-(1-frac) of the grid series is left byte-identical (well-measured vintages
# — e.g. ERCOT — unchanged). Keeps the actual gen+imports row reconciled to load
# and the per-class shares on the model's grid-delivered denominator.
_VINTAGE_RECONCILE_FRAC = 0.97
# LEGACY FALLBACK ONLY. Balancing authorities whose EIA-930 "Natural Gas"
# (NG: NG) aggregate silently folds in geothermal + biomass net generation, so
# the raw 930 gas cell over-states true natural-gas output. The general fix
# (_gas_foldin_deflation) now threads the EIA-930 "Other Fuel Sources" (NG: OTH)
# series through the bundle and subtracts only the GENUINELY-folded portion
# (max(0, model OTHER+biomass - 930 other)) for EVERY BA — self-zeroing for clean
# BAs, full for total-fold CAISO (930 other≈0), partial for MISO (~12.8 of 15.5,
# since MISO reports ~2.7 TWh in its own Other series). This allowlist is used
# ONLY when a bundle predates the NG: OTH series (not re-extracted), to keep
# already-committed bundles byte-identical. Re-extracting a bundle's eia930
# parquet retires its dependence on this set.
EIA930_GAS_FOLDS_GEO_BIOMASS: frozenset[str] = frozenset({"CAISO"})
_CUM = np.cumsum([0] + list(rcf._DAYS_IN_MONTH)) * 24  # month hour boundaries
_T = 8760


def reconcile_vintage_classes(
    classfull: dict[str, float], e930: dict[str, float], iso: str
) -> dict[str, float]:
    """Reconcile each fossil family's EIA-923 total to the EIA-930 grid series, in place.

    Puts the actual fossil benchmark on the SAME grid-delivered basis as the
    model (and the C2 volume gate): each fossil family's grid-delivered EIA-923
    class total is scaled to the complete EIA-930 grid series the model is
    calibrated to, in BOTH directions —
      * UP when the current-year 923 release is a preliminary monthly survey that
        under-counts thermal generation the CAMPD backfill can't fully repair, and
      * DOWN when the 923 plant total over-states grid delivery (residual CHP
        behind-the-meter the ``btm.parquet`` hold-out under-removes, plus
        923<->930 plant-to-BA assignment) — so the actual "gen + net imports" row
        reconciles to load instead of reading as a phantom over-supply, and the
        per-class shares share the model's grid-delivered denominator.
    The inter-class split and monthly shape are preserved; a family already
    within :data:`_VINTAGE_RECONCILE_FRAC` of the grid series (well-measured
    vintages — e.g. ERCOT) is left byte-identical. ISO-agnostic: one rule for
    every BA, no per-ISO branch.

    Some BAs silently fold geothermal + biomass into the EIA-930 "Natural Gas"
    cell, so the GAS target must be deflated by that fold-in before scaling — else
    the gas classes absorb non-gas energy the model already books as its own
    OTHER/biomass rows (run_calibration_full.py [1] note). The deflation is the
    GENUINELY-folded portion only (:func:`_gas_foldin_deflation`): when the bundle
    carries the EIA-930 "other" series it is ``max(0, model OTHER+biomass - 930
    other)``, which self-zeroes for clean BAs (930 reports geo/biomass in its own
    Other series), gives the full subtraction for a total-fold BA (CAISO, 930
    other≈0), and the right partial subtraction for a partial-fold BA (MISO ~12.8
    of 15.5). Bundles predating the "other" series fall back to the per-ISO
    :data:`EIA930_GAS_FOLDS_GEO_BIOMASS` allowlist. Coal never folds.

    Mutates and returns ``classfull``.
    """
    for _fuel, _klasses in (("gas", _GAS_GROUPS), ("coal", _COAL_GROUPS)):
        _present = [g for g in _klasses if g in classfull]
        _cur = sum(classfull[g] for g in _present)
        _tgt = float(e930.get(_fuel, 0.0))
        if _fuel == "gas":
            _tgt -= _gas_foldin_deflation(classfull, e930, iso)
        # Reconcile the family's grid-delivered EIA-923 total to the complete
        # EIA-930 grid series — the same authority the model's gas/coal volume is
        # scored on — in BOTH directions. Scale UP a preliminary/under-counting
        # vintage (the original repair), and scale DOWN a vintage whose EIA-923
        # plant total OVER-states grid delivery: residual CHP behind-the-meter
        # the btm.parquet hold-out under-removes, plus 923<->930 plant-to-BA
        # assignment. Either way the family lands on its grid-measured total, so
        # the actual "gen + net imports" reconciles to load and the per-class
        # shares use the SAME grid-delivered denominator the model does — without
        # this the EIA-923 fossil total runs tens of TWh above the grid for
        # CHP-heavy BAs (MISO 2023 +19 TWh) and the absolute supply row reads as
        # a phantom over-supply. The inter-class split + monthly shape are
        # preserved; a family already within +/-(1-frac) of the grid series is
        # left byte-identical (well-measured vintages — e.g. ERCOT — unchanged).
        # ISO-agnostic: one rule, no per-ISO branch.
        if (
            _tgt > 0.0
            and _cur > 0.0
            and not (
                _VINTAGE_RECONCILE_FRAC * _tgt <= _cur <= _tgt / _VINTAGE_RECONCILE_FRAC
            )
        ):
            _scale = _tgt / _cur
            for g in _present:
                classfull[g] = round(classfull[g] * _scale, 4)
    return classfull


def _gas_foldin_deflation(
    classfull: dict[str, float], e930: dict[str, float], iso: str
) -> float:
    """TWh of geothermal+biomass the BA folded into its EIA-930 "Natural Gas" cell.

    Subtract this from the EIA-930 gas reconcile target so the gas classes don't
    scale to gas+geo+biomass. Two regimes:

    * **Re-extracted bundle** (carries the EIA-930 ``other`` = "Other Fuel
      Sources" series): the folded amount is the model's clean OTHER (geothermal)
      + biomass actuals MINUS what the BA correctly reported in its own Other
      series — i.e. only the part that *leaked* into NG. ``max(0, …)`` self-zeroes
      a clean BA (930 other ≈ model other+biomass) and yields the full model
      other+biomass for a total-fold BA (930 other ≈ 0).
    * **Legacy bundle** (no ``other`` series): fall back to the per-ISO
      :data:`EIA930_GAS_FOLDS_GEO_BIOMASS` allowlist (full subtraction for the
      known total-fold BAs, none elsewhere) so committed bundles don't regress.
    """
    model_other_bio = float(classfull.get("OTHER", 0.0)) + float(
        classfull.get("biomass", 0.0)
    )
    if "other" in e930:
        return max(0.0, model_other_bio - float(e930.get("other", 0.0)))
    return model_other_bio if iso in EIA930_GAS_FOLDS_GEO_BIOMASS else 0.0
