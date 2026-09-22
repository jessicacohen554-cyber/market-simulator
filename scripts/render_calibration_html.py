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
# Package imports, not ``spec_from_file_location`` file-loads (refactor plan
# §6-E). The old form executed each module a SECOND time under a synthetic name
# ("rcf" / "ordc_overlay"), so this file held private copies whose module-level
# state could drift from the canonical ``scripts.*`` entries any co-running
# importer sees. The canonical bootstrap above (REPO on sys.path) is what makes
# the PEP-420 ``scripts`` / ``scripts.data`` namespace packages resolvable —
# there is deliberately no ``__init__.py`` under ``scripts/``.
from scripts import run_calibration_full as rcf  # noqa: E402

# The ORDC scarcity overlay deriver supplies the reference monthly-MAE /
# actual-RT / demand-weight implementations; the dashboard's display-only
# overlay series reuses them verbatim so its numbers match the deriver's
# stdout report (docs/ordc-overlay.md, "Reliability-deployment overlay").
from scripts.data import derive_ordc_overlay as ordc  # noqa: E402

from scripts.lib import bench_multiclass as bm  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402
from scripts.lib.bundle_io import require_bundle_input  # noqa: E402
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

# --- Non-fossil + interchange hourly panels (Charts-tab heatmaps) -----------
# The Charts tab's hourly coverage is CAMPD-backed and therefore FOSSIL-ONLY:
# CEMS meters combustion units, so nuclear / hydro / the renewables / net
# interchange had no hourly actual anywhere in the payload (only the annual
# ``nonfossil`` scalars). ``build_nonfossil_hourly`` closes that blind spot from
# EIA-930, whose hourly per-fuel net-generation series ARE the measured record
# for those classes.
#
# The panel key is the EIA-930 FUEL BUCKET (``PlantClass.fuel930``), not a model
# class name: the model side sums every non-fossil class that rolls up to the
# bucket, so a bucket comparison is valid by construction and no split is ever
# fabricated. Two consequences worth stating, both deliberate:
#   * ``wind`` sums {wind, offshore_wind} against NG: WND — an ISO with both
#     compares the total, never one leg against the aggregate meter.
#   * ``other`` sums {biomass, geothermal, OTHER} against NG: OTH — EIA-930's
#     "Other Fuel Sources" cell is itself that aggregate, so the bucket is the
#     only honest unit of comparison for it (a per-class actual does not exist).
# Adding a class to plant_taxonomy.PLANT_CLASSES routes it into its bucket here
# automatically; there is no per-ISO branch anywhere in this path.
#
# Values are the ``name`` keys of eia_loader._EIA930_BENCHMARK_COLUMNS (the
# series names in the bundle's eia930 extract), NOT the raw "NG: XXX" columns.
# Citations are the EIA-930 net-generation-by-energy-source column each name
# reads (src/market_sim/data/eia930/actuals.py::_EIA930_BENCHMARK_COLUMNS).
NONFOSSIL_930_SERIES: dict[str, tuple[str, ...]] = {
    "nuclear": ("nuclear",),  # EIA-930 "NG: NUC" — nuclear net generation
    "hydro": ("hydro",),  # EIA-930 "NG: WAT" — conventional hydro
    "wind": ("wind",),  # EIA-930 "NG: WND" — wind (on + offshore)
    "solar": ("solar",),  # EIA-930 "NG: SUN" — utility-scale solar
    "oil": ("oil",),  # EIA-930 "NG: OIL" — petroleum-fired
    "other": ("other",),  # EIA-930 "NG: OTH" — geothermal + biomass + process
    # Storage is reported as two separate net series (positive = discharging);
    # the model's single ``storage`` class is their sum. Both are optional —
    # a BA that has not begun reporting the BAT/PS breakout supplies neither,
    # and the panel then shows the model with no hourly actual.
    "storage": ("battery", "pumped_storage"),  # EIA-930 "NG: BAT" / "NG: PS"
}

# Net interchange is not a fuel bucket — it is the priced import/export node, so
# it carries its own panel key and its own series. SIGN CONVENTION (assert-backed
# in tests/test_nonfossil_hourly.py): the model's ``import`` klass is positive
# INTO the ISO, while EIA-930 "Total interchange" is positive EXPORT (NYIS 2023
# reads -23.45 TWh for ~23.4 TWh of net imports). This panel publishes the
# IMPORT-POSITIVE convention — the natural reading of a panel labelled "Imports"
# — so the model side is used as-is and the 930 series is NEGATED. Get this
# backwards and the heatmap is exactly inverted, which is why the reconciliation
# against the ``interchange`` fuelRows row (which publishes the OPPOSITE,
# export-positive convention) is asserted at build time.
IMPORT_KLASS = "import"
IMPORT_PANEL = "import"
IMPORT_930_SERIES = "interchange"

# Affine uint8 codec resolution: hourly values are encoded as
# ``round(_B64_SCALE * (mw - lo) / (hi - lo))`` over a per-panel [lo, hi] MW
# window SHARED by the model and actual series, so the browser's subtraction is
# a true MW-space delta (see build_nonfossil_hourly). 250 matches the ceiling the
# sibling ``_b64`` CF codec clips to (so the two stay visually comparable) and
# gives 1/250 = 0.4% of the panel's MW span per byte — ~20 MW on a 5 GW nuclear
# fleet, far below any delta the heatmap's 98th-percentile cap resolves. int16
# (_b64_i16) would give exact 1-MW steps at 2x the payload; measured on the NYISO
# keeper that is +245 KB vs +127 KB gzipped for three years, and the extra
# resolution buys nothing a 365x24 canvas can display.
_B64_SCALE = 250.0
# Display labels for the panels (the model classes' own labels come from the
# taxonomy; a bucket that sums several classes needs its own name).
NONFOSSIL_PANEL_LABEL: dict[str, str] = {
    "nuclear": "Nuclear",
    "hydro": "Hydro",
    "wind": "Wind",
    "solar": "Solar",
    "oil": "Oil",
    "other": "Other (biomass/geo)",
    "storage": "Storage",
    IMPORT_PANEL: "Imports (net)",
}
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
_GAS_GROUPS = bs.GAS_GROUPS
_COAL_GROUPS = bs.COAL_GROUPS
# The third reconcile-family member (nyiso-239): EIA-923 books a dual-fuel
# plant's oil burn under `oil` while EIA-930 books the same generation under
# `NG: OIL`, so a gas-only comparison straddles a fuel boundary. Joined to the
# family ONLY when the bundle's extract carries the 930 `oil` series — see
# reconcile_vintage_classes.
_OIL_GROUPS = bs.OIL_GROUPS
# Grid-delivered benchmark reconciliation deadband (half-width ~3%). The COMBINED
# fossil (gas + coal) grid-delivered EIA-923 total is reconciled to the complete
# EIA-930 grid series — the authority the model's fossil volume is scored on — in
# BOTH directions: scaled UP when a preliminary monthly 923 vintage under-counts
# thermal generation the CAMPD backfill can't fully repair, and scaled DOWN when
# the 923 total over-states grid delivery (residual CHP behind-the-meter +
# 923<->930 assignment). Every fossil class scales by the SAME factor, so the
# CEMS-validated 923 gas/coal split is preserved — the reconcile corrects the
# fossil LEVEL, never the SPLIT (EIA-930's per-fuel coal/gas attribution mis-splits
# by 7-21 TWh/yr vs CAMPD; see reconcile_vintage_classes). A total already within
# +/-(1-frac) of the grid series is left byte-identical (well-measured vintages —
# e.g. ERCOT — unchanged; and offsetting per-family misses that net to an in-band
# total, e.g. PJM 2024, are now correctly left alone).
_VINTAGE_RECONCILE_FRAC = bs.VINTAGE_RECONCILE_FRAC
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
EIA930_GAS_FOLDS_GEO_BIOMASS: frozenset[str] = bs.EIA930_GAS_FOLDS_GEO_BIOMASS
# BAs whose EIA-930 "Natural Gas" cell is demonstrably CORRUPTED against two
# independent measured sources (CEMS hourly + EIA-923), so the combined
# vintage reconcile must be CAPPED at a CEMS-anchored fossil total instead of
# scaling classFull up to the 930 cell. CAISO: from ~2024-05 the CISO NG cell
# carries a growing noon-peaked, solar-shaped block no gas fleet produced
# (+4.2/+7.9 TWh unexplained in 2024/25 vs CEMS bench gas + the flat non-CEMS
# cogen block + the geo/biomass fold-in; the raw series RISES 8.1→13.2 GW into
# noon in Jun-Aug 2025 — the inverse of the measured duck curve). Scaling to
# it fabricated ×1.10/×1.21/×1.44 classFull inflation. Owner-signed rework
# 2026-07-12; see results/calibration/
# FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §3/§5. The anchor fields
# (``gas_cems_grid``/``gas_cogen_grid``/``fossil_cems_grid``) are written into
# the bench part's ``e930`` dict by the render (sole writer, same coverage
# basis as ``coal_cems``); other ISOs carry no anchor and are unchanged.
EIA930_NG_CELL_CORRUPT: frozenset[str] = bs.EIA930_NG_CELL_CORRUPT
# First VINTAGE year the corruption contaminates (CISO onset ~2024-05): the
# hourly gas actual (fuelRows / C4) switches to the CEMS+cogen basis from this
# vintage; earlier years keep 930 for continuity — the two agree pre-onset.
EIA930_NG_CORRUPT_ONSET: dict[str, int] = bs.EIA930_NG_CORRUPT_ONSET
_CUM = np.cumsum([0] + list(rcf._DAYS_IN_MONTH)) * 24  # month hour boundaries
_T = 8760


def reconcile_vintage_classes(
    classfull: dict[str, float], e930: dict[str, float], iso: str
) -> dict[str, float]:
    """Reconcile the COMBINED fossil (gas+coal) EIA-923 total to EIA-930, in place.

    Puts the actual fossil benchmark on the SAME grid-delivered basis as the
    model (and the C2 volume gate): the grid-delivered EIA-923 gas+coal total is
    scaled to the complete EIA-930 grid series the model is calibrated to, in
    BOTH directions —
      * UP when the current-year 923 release is a preliminary monthly survey that
        under-counts thermal generation the CAMPD backfill can't fully repair, and
      * DOWN when the 923 total over-states grid delivery (residual CHP
        behind-the-meter the ``btm.parquet`` hold-out under-removes, plus
        923<->930 plant-to-BA assignment) — so the actual "gen + net imports" row
        reconciles to load instead of reading as a phantom over-supply.

    Every fossil class scales by the SAME factor, so the reconcile corrects only
    the fossil LEVEL and NEVER the gas/coal SPLIT. This is deliberate: the earlier
    per-family reconcile scaled gas and coal each to their own EIA-930 cell, which
    forced the EIA-923 split onto EIA-930's fuel attribution — and that attribution
    is unreliable. Against CAMPD (every coal unit and every grid CC/CT/ST gas unit
    is CEMS-metered), EIA-930 mis-splits coal vs gas by 7-21 TWh/yr (PJM 930 coal
    runs +7..+11 ABOVE CEMS, under-attributing gas by ~the same; MISO is the mirror,
    -17..-21 BELOW), so the per-family reconcile manufactured per-class errors even
    when the total fossil was in tolerance — PJM 2024 gas +4.2% / coal -5.9% both
    fired, dumping ~85% of a spurious -15 TWh gas cut onto CC_REGULAR (which read
    +21 TWh over when the CEMS-basis miss is ~+3) and inflating the coal target so a
    real model coal over-run read as under. The row-level EIA-923 split is
    CAMPD-validated (923 coal tracks CEMS to within ~1 TWh); the combined reconcile
    keeps it. A total already within :data:`_VINTAGE_RECONCILE_FRAC` of the grid
    series is left byte-identical (well-measured vintages — e.g. ERCOT — and
    offsetting misses that net in-band, e.g. PJM 2024). ISO-agnostic: one rule for
    every BA, no per-ISO branch. LIMITATION: the uniform scale still distributes a
    preliminary-vintage (2025) level repair proportionally across coal and gas; a
    CAMPD-per-class target (complete in every vintage) is the follow-up refinement
    (docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md §6).

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
    # Reconcile the COMBINED fossil total (gas + coal) to the EIA-930 grid series
    # as ONE family, scaling every fossil class by the SAME factor so the
    # row-level EIA-923 gas/coal SPLIT is preserved. Scaling gas and coal
    # separately to EIA-930's per-fuel cells (the earlier behaviour) forced the
    # EIA-923 split onto EIA-930's fuel attribution — which is unreliable: every
    # coal unit and every grid CC/CT/ST gas unit is CEMS-metered, and against that
    # CAMPD ground truth EIA-930 MIS-SPLITS coal vs gas by 7–21 TWh/yr (PJM 930
    # coal runs +7..+11 ABOVE CEMS and under-attributes gas by ~the same; MISO is
    # the mirror, −17..−21 BELOW). The per-fuel reconcile therefore manufactured
    # per-class errors even when the TOTAL fossil was fine — e.g. PJM 2024 gas
    # +4.2% / coal −5.9% each breach the ±(1−frac) band and fire, dumping ~85% of
    # a spurious −15 TWh gas correction onto CC_REGULAR (read +21 TWh over when the
    # CEMS-basis miss is ~+3) and inflating the coal target so a real model coal
    # over-run read as under. Reconciling the combined total corrects only the
    # GENUINE level miss (CHP over-statement the btm.parquet hold-out under-removes;
    # preliminary-vintage under-count) and leaves the CAMPD-validated split intact.
    # PJM 2024's +4.2%/−5.9% OFFSET to a +1.6% total that is now correctly left
    # byte-identical. ISO-agnostic; the CAISO geo/biomass gas fold-in is still
    # deflated from the (now combined) target. NOTE: the uniform combined scale
    # still distributes a preliminary-vintage (2025) level repair proportionally
    # across coal and gas even when they under-report by different amounts — a
    # CAMPD-per-class target (complete in every vintage) is the follow-up refinement
    # (docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md §6).
    # FAMILY MEMBERSHIP. Gas + coal, plus OIL when — and only when — the bundle's
    # extract carries EIA-930's own `NG: OIL` cell (nyiso-239). EIA-923 books a
    # plant's MWh under the fuel it BURNED, so a dual-fuel unit's oil hours land
    # in the 923 `oil` class while its gas hours stay in the CC/CT/ST classes;
    # EIA-930 books the same generation under `NG: OIL`. Comparing the 923 gas
    # classes against the 930 `gas` cell alone therefore straddles that boundary
    # and reads an attribution difference as a LEVEL error — exactly the failure
    # this function already refuses to propagate one fuel over (the coal/gas
    # paragraph above). Measured on NYISO 2022: +5.13 % gas-only (fires, x0.951167
    # on every fossil class, 1.62 TWh of it on `CC_REGULAR`) against +0.08 % with
    # oil on both sides — the tightest agreement of any complete NYISO vintage,
    # corroborated by the ISO's OWN published fuel mix (which files oil-capable
    # units under `Dual Fuel` and publishes no oil category at all), by CEMS on a
    # fixed plant set, and on SHAPE, where model(gas+oil) vs 930(gas+oil) beats
    # model(gas) vs 930(gas) on r AND NRMSE in all four years.
    # A bundle whose extract predates the series has no "oil" key: the family
    # stays gas+coal and the bench part re-renders byte-identical — the same
    # fallback contract the "other" (NG: OTH) series already carries.
    _oil930 = e930.get("oil")
    _families = (
        (*_GAS_GROUPS, *_COAL_GROUPS)
        if _oil930 is None
        else (*_GAS_GROUPS, *_COAL_GROUPS, *_OIL_GROUPS)
    )
    _present = [g for g in _families if g in classfull]
    _cur = sum(classfull[g] for g in _present)
    _tgt = float(e930.get("gas", 0.0)) + float(e930.get("coal", 0.0))
    if _oil930 is not None:
        _tgt += float(_oil930)
    _tgt -= _gas_foldin_deflation(classfull, e930, iso)
    # CEMS-anchor cap (owner-signed 2026-07-12): for a BA whose 930 NG cell is
    # corrupted (EIA930_NG_CELL_CORRUPT), the reconcile target may never
    # exceed the measured fossil total — CEMS bench-gas net + the 923
    # non-CEMS cogen block + 923 coal, all grid-delivered
    # (``fossil_cems_grid``, written by this render). One-directional by
    # design: the cap protects against scaling UP to a fabricated cell; a 930
    # total below the anchor still governs.
    if iso in EIA930_NG_CELL_CORRUPT:
        _anchor = e930.get("fossil_cems_grid")
        if _anchor is not None and float(_anchor) > 0.0:
            # The anchor is built from the CEMS gas block + the 923 non-CEMS cogen
            # block + 923 coal, so it spans gas+coal ONLY. When oil joins the
            # family the cap must span the same boundary as `_cur`, or it would
            # bind a wider current against a narrower target (nyiso-239). CAISO is
            # the only capped ISO and its 930 oil cell is 0.45-0.61 % of gas, so
            # this is a measured near-no-op there — it exists to keep the two
            # sides on one boundary, not to move CAISO.
            _cap = float(_anchor)
            if _oil930 is not None:
                _cap += sum(classfull.get(g, 0.0) for g in _OIL_GROUPS)
            _tgt = min(_tgt, _cap)
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


# Genuinely-folded geothermal+biomass TWh in a BA's EIA-930 "Natural Gas" cell
# (single home: scripts.lib.benchmark_semantics). reconcile_vintage_classes calls
# it under this name.
_gas_foldin_deflation = bs.gas_foldin_deflation


def _eia923_gas_family_incomplete(iso: str, year: int) -> bool:
    """Whether the EIA-923 gas family is preliminary/incomplete for (iso, year).

    Reads the committed completeness part
    (``frontend/data/backcast/completeness/eia923_<year>.json``, written by
    ``scripts/audit_eia923_completeness.py``) — the same source of truth
    ``calibration_verdict.family_is_complete`` scores from. A year with no
    part is a complete vintage. Used by the CEMS-anchor writer to decide when
    the non-CEMS cogen block must be carried from the latest complete vintage
    (a preliminary 923 release under-counts the non-CEMS cogens the anchor
    needs at full coverage).
    """
    part = (
        REPO
        / "frontend"
        / "data"
        / "backcast"
        / "completeness"
        / (f"eia923_{int(year)}.json")
    )
    if not part.exists():
        return False
    fams = json.loads(part.read_text()).get("families", {})
    return not bool(fams.get(str(iso).upper(), {}).get("gas", True))


def _b64(cf: np.ndarray) -> str:
    """Encode a capacity-factor series (0-100) as base64 uint8 of length 8760."""
    a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)
    if a.shape[0] < _T:
        a = np.concatenate([a, np.zeros(_T - a.shape[0], np.uint8)])
    return base64.b64encode(a[:_T].tobytes()).decode()


def _b64_i16(x: np.ndarray) -> str:
    """Encode a SIGNED hourly series as base64 little-endian int16 of length 8760.

    Used for the Report-tab LMP delta heatmap (model $/MWh minus actual $/MWh):
    the value can be either sign and span the full scarcity range, so unlike
    :func:`_b64` (unsigned CF bytes) it keeps 1-$/MWh resolution over
    ``[-32767, 32767]`` and reserves ``-32768`` as the NOT-A-NUMBER sentinel for
    hours with no model dual or no actual price (rendered neutral, not colored).
    ``<i2`` forces little-endian so the browser's ``Int16Array`` decode is
    byte-order-independent of the machine that rendered the run.
    """
    v = np.asarray(x, dtype=float)
    out = np.full(v.shape, -32768, dtype="<i2")  # sentinel = NaN
    finite = np.isfinite(v)
    out[finite] = np.clip(np.round(v[finite]), -32767, 32767).astype("<i2")
    if out.shape[0] < _T:
        out = np.concatenate([out, np.full(_T - out.shape[0], -32768, dtype="<i2")])
    return base64.b64encode(out[:_T].astype("<i2").tobytes()).decode()


def _b64_affine(mw: np.ndarray, lo: float, hi: float) -> str:
    """Encode an hourly MW series as base64 uint8 over the window ``[lo, hi]``.

    ``byte = round(_B64_SCALE * (mw - lo) / (hi - lo))``, so the browser rebuilds
    MW as ``lo + byte / _B64_SCALE * (hi - lo)``. Signed series (net interchange,
    a net storage series, a hydro meter that dips negative) are handled by the
    offset — no separate signed codec is needed — and because the model and
    actual series of a panel share ONE ``[lo, hi]``, their decoded difference is
    a true MW-space delta.

    Same byte layout as the frozen :func:`_b64` (uint8, base64), so the browser's
    existing ``dec()`` reader decodes it unchanged — but LENGTH-EXACT rather than
    padded to 8760. ``_b64`` zero-pads a short series, and a zero byte here
    decodes to ``lo`` (not 0 MW), which for a signed panel like net interchange
    would silently append thousands of hours pinned at the series minimum. Every
    production panel is a full 8760, so this only matters for the ``hours``
    parameter's shorter cases (tests, a partial-year bundle) — but a codec that
    is wrong at one length is a codec waiting to be reused at that length.
    """
    v = np.nan_to_num(np.asarray(mw, dtype=float))
    span = float(hi) - float(lo)
    if not np.isfinite(span) or span <= 0.0:
        # Degenerate (flat) panel: every byte 0, decoding to exactly lo.
        return base64.b64encode(np.zeros(v.shape[0], np.uint8).tobytes()).decode()
    scaled = np.clip(np.round(_B64_SCALE * (v - float(lo)) / span), 0, _B64_SCALE)
    return base64.b64encode(scaled.astype(np.uint8).tobytes()).decode()


def _hourly_series(arr: np.ndarray | None, hours: int) -> np.ndarray | None:
    """Coerce a benchmark/model hourly array to exactly ``hours`` samples.

    Shorter series are zero-extended and longer ones truncated, so a BA-year a
    few hours short of 8760 still yields a full-length panel. ``None`` in,
    ``None`` out.
    """
    if arr is None:
        return None
    a = np.asarray(arr, dtype=float)
    if a.shape[0] >= hours:
        return a[:hours]
    return np.concatenate([a, np.zeros(hours - a.shape[0])])


def _actual_is_absent(arr: np.ndarray | None) -> bool:
    """Whether an EIA-930 series carries no usable observation for the year.

    A series that is missing, all-NaN, or identically zero is NOT an actual of
    zero — it is a fuel the BA does not report (NYISO files no utility-scale
    solar series, so its ``NG: SUN`` cell reads 0.0 TWh against ~2 TWh of
    modelled solar). Comparing a model series against it would manufacture a
    -100% class error and a fully-saturated delta map, so such a panel publishes
    the model side only, with a labelled reason and no delta (see the frontend's
    "no hourly actual" note).
    """
    if arr is None:
        return True
    a = np.asarray(arr, dtype=float)
    return bool(a.size == 0 or not np.isfinite(a).any() or not np.any(a != 0.0))


def build_nonfossil_hourly(
    model_hourly: dict[str, np.ndarray],
    actual_930: dict[str, np.ndarray],
    *,
    hours: int = _T,
) -> dict[str, dict]:
    """Build the ``nonfossilHr`` payload: hourly model vs EIA-930 by fuel bucket.

    Closes the Charts tab's fossil-only blind spot. ``model_hourly`` is
    ``{klass: (T,) MW}`` (``run_calibration_full._class_hourly``, or the
    equivalent read off a bundle's committed ``hourly/class_hourly_<year>``
    sidecar) and ``actual_930`` is ``{series: (T,) MW}`` (the bundle's eia930
    extract, or ``eia930.actuals.load_eia_hourly_benchmark``). Both are on the
    model's chronological fixed-standard-time 8760 clock, so hour ``k`` pairs
    hour ``k`` with no DST correction — verified by cross-correlating model
    against actual demand (lag 0 must dominate; see
    docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md and
    tests/test_nonfossil_hourly.py::test_clock_alignment_lag_zero_dominates).

    Returns ``{panel: {...}}`` over :data:`NONFOSSIL_930_SERIES` (the non-fossil
    EIA-930 fuel buckets) plus :data:`IMPORT_PANEL`, keeping only panels the run
    actually dispatches. Each entry carries:

      ``m``/``a``   base64 uint8 model / actual MW over the shared ``[lo, hi]``
                    window (:func:`_b64_affine`); ``a`` is ``None`` when the BA
                    reports no usable series for the bucket.
      ``lo``/``hi`` the shared MW decode window — the SAME for both series, so
                    the browser's ``m - a`` is a true MW delta, never a
                    CF%-minus-CF% difference between two different maxima.
      ``mTwh``/``aTwh``  annual totals (``aTwh`` ``None`` with no actual).
      ``r``/``nrmse``    hourly fit, computed HERE (Python) — the frontend never
                    recomputes class fit, matching the existing contract.
      ``src``       provenance label for the actual map ("EIA-930").
      ``note``      why the actual is absent, when it is.
      ``classes``   the model classes summed into this panel.
      ``label``     display label.

    Imports publish the IMPORT-POSITIVE convention (positive = into the ISO):
    the model's ``import`` klass is used as-is and EIA-930's export-positive
    "Total interchange" is negated. See :data:`IMPORT_930_SERIES`.
    """
    out: dict[str, dict] = {}
    # Panel -> the model classes that roll up to it. Non-fossil buckets take
    # every non-fossil class of the bucket (taxonomy-driven, no string matching);
    # imports are their own single-class panel.
    panels: list[tuple[str, tuple[str, ...], tuple[str, ...], bool]] = [
        (
            panel,
            tuple(c for c in classes_for_fuel930(panel) if c in _NONFOSSIL_KLASS),
            series,
            False,
        )
        for panel, series in NONFOSSIL_930_SERIES.items()
    ]
    panels.append((IMPORT_PANEL, (IMPORT_KLASS,), (IMPORT_930_SERIES,), True))

    for panel, classes, series_names, negate_actual in panels:
        present = [c for c in classes if c in model_hourly]
        if not present:
            continue  # the run does not dispatch this panel at all
        model = np.zeros(hours)
        for c in present:
            s = _hourly_series(model_hourly[c], hours)
            if s is not None:
                model = model + np.nan_to_num(s)
        # Actual: sum the bucket's series (storage has two); a bucket whose
        # series are all missing/blank yields None, never an implied zero.
        parts = [
            _hourly_series(actual_930.get(name), hours)
            for name in series_names
            if not _actual_is_absent(actual_930.get(name))
        ]
        actual = None
        if parts:
            actual = np.zeros(hours)
            for p in parts:
                actual = actual + np.nan_to_num(p)
            if negate_actual:
                # 930 interchange is export-positive; publish import-positive.
                actual = -actual
        note = None
        if actual is None:
            note = (
                f"EIA-930 reports no {panel} series for this BA-year — "
                "model shown without an hourly actual."
            )
        # ONE decode window shared by both series (the MW-space guarantee).
        stack = model if actual is None else np.concatenate([model, actual])
        lo = float(np.nanmin(stack))
        hi = float(np.nanmax(stack))
        if hi <= lo:
            hi = lo + 1.0
        entry: dict = {
            "m": _b64_affine(model, lo, hi),
            "a": None if actual is None else _b64_affine(actual, lo, hi),
            "lo": round(lo, 3),
            "hi": round(hi, 3),
            "mTwh": round(float(model.sum()) / 1e6, 4),
            "aTwh": None if actual is None else round(float(actual.sum()) / 1e6, 4),
            "r": None,
            "nrmse": None,
            "src": EIA930_SOURCE,
            "note": note,
            "classes": list(present),
            "label": NONFOSSIL_PANEL_LABEL.get(panel, class_label(panel)),
        }
        if actual is not None:
            if actual.std() > 0 and model.std() > 0:
                entry["r"] = round(_pearson(model, actual), 3)
            # _nrmse normalizes by the actual's MEAN, which is meaningless for a
            # signed series that straddles zero (net interchange): use the MW
            # SPAN there instead, and label it so the frontend can say which.
            if negate_actual or float(actual.mean()) <= 0.0:
                rng = float(actual.max() - actual.min())
                if rng > 0:
                    entry["nrmse"] = round(
                        float(np.sqrt(((model - actual) ** 2).mean()) / rng), 3
                    )
                    entry["nrmseBasis"] = "range"
            else:
                entry["nrmse"] = round(_nrmse(model, actual), 3)
                entry["nrmseBasis"] = "mean"
        out[panel] = entry
    return out


def _assert_nonfossil_hourly_reconciles(
    nfhr: dict[str, dict],
    model_hourly: dict[str, np.ndarray],
    fuel_rows: list[dict],
    *,
    iso: str,
    year: int,
    hours: int = _T,
    tol_twh: float = 0.01,
) -> None:
    """Cross-check the ``nonfossilHr`` panels against the payload's own tables.

    Two independent reconciliations, both cheap and both catching a real class of
    silent error before a single pixel is trusted:

    1. **Volume** — each panel's ``mTwh`` must equal the sum of its classes in
       ``model_hourly``. Catches a bucket that dropped or double-counted a class.
    2. **Imports sign** — the ``import`` panel is IMPORT-positive while the
       ``interchange`` row of ``fuelRows`` is EXPORT-positive, so the two must be
       exact negatives. This is the assertion that catches an inverted
       interchange map, which is otherwise invisible (the magnitudes are right
       and only the color is flipped).

    Raises:
        AssertionError: on a mismatch — a render-time stop, not a warning: a
            wrong-signed or mis-summed panel would be published as a diagnostic
            people then reason from.
    """
    for panel, entry in nfhr.items():
        # Summed over the SAME length-coerced series the panel encoded, so this
        # tests the bucket membership (did we sum the right classes?) and never
        # trips over the 8760 truncate/extend policy the panel already applied.
        want = (
            sum(
                float(np.nan_to_num(_hourly_series(model_hourly[c], hours)).sum())
                for c in entry["classes"]
            )
            / 1e6
        )
        got = float(entry["mTwh"])
        assert abs(got - want) <= tol_twh, (
            f"{iso} {year}: nonfossilHr[{panel!r}] model volume {got:.4f} TWh "
            f"does not reconcile to its classes {entry['classes']} "
            f"({want:.4f} TWh)"
        )
    imp = nfhr.get(IMPORT_PANEL)
    ix_row = next((r for r in fuel_rows if r.get("fuel") == "interchange"), None)
    if imp is not None and ix_row is not None and ix_row.get("m") is not None:
        # fuelRows publishes export-positive; this panel publishes
        # import-positive. Exact negatives (to the rows' 2-dp rounding).
        assert abs(float(imp["mTwh"]) + float(ix_row["m"])) <= 0.02, (
            f"{iso} {year}: import panel {imp['mTwh']:+.4f} TWh (import-positive) "
            f"is not the negative of the interchange fuelRow {ix_row['m']:+.2f} "
            "TWh (export-positive) — the interchange sign convention is wrong"
        )
        if imp.get("aTwh") is not None and ix_row.get("b") is not None:
            assert abs(float(imp["aTwh"]) + float(ix_row["b"])) <= 0.02, (
                f"{iso} {year}: import panel actual {imp['aTwh']:+.4f} TWh is not "
                f"the negative of the interchange fuelRow benchmark "
                f"{ix_row['b']:+.2f} TWh — EIA-930 interchange sign is wrong"
            )


def _monthly_gwh(mw: np.ndarray) -> list[float]:
    """Return 12 monthly GWh totals from an hourly MW series."""
    return [round(float(mw[_CUM[m] : _CUM[m + 1]].sum()) / 1e3, 2) for m in range(12)]


def _vol_err(model_twh: float, actual_twh: float) -> float | None:
    """Signed volume error, JSON-safe: ``None`` when it is not finite.

    ``signed_volume_error`` returns ``inf`` for a nonzero model against a
    zero actual; ``json.dumps`` would emit a bare ``Infinity`` token that the
    browser's ``JSON.parse`` rejects (and would take the whole run payload
    down with it), so a non-finite error is stored as ``null`` instead.
    """
    e = signed_volume_error(model_twh, actual_twh)
    return round(e, 4) if np.isfinite(e) else None


def _primary_pass(df: "pd.DataFrame") -> "pd.DataFrame":
    """Filter a per-pass frame to the bundle's PRIMARY dispatch pass.

    P1 — the no-commitment solve — is the model's MAIN run; every normal
    bundle is P1-only and scores byte-identically under this rule. A bundle
    carries a P2 frame only when the run explicitly opted into the commitment
    screen (``commitment_enabled`` / ``ercot_as_aware_commitment`` /
    ``caiso_ra_mustoffer``, all default off); for those opt-in bundles the
    solver labels P2 the primary result, so the dashboard scores P2 there —
    the mechanism the run actually proposes — rather than silently reporting
    the pre-commitment P1. This does NOT make P2 a default anywhere: it only
    reports what a bundle chose to run.
    """
    if "pass" not in df.columns:
        return df
    for label in ("P2", "P1"):
        sel = df["pass"] == label
        if sel.any():
            return df[sel]
    return df


def _model_storage_twh(storage_all: pd.DataFrame | None, year: int) -> float | None:
    """Return the model's annual storage discharge throughput (TWh) for a year.

    Sums ``discharge_mw`` over every storage unit (li-ion + pumped storage) and
    hour from the bundle's ``storage.parquet`` P1 frame — the same dispatch pass
    the price/mix metrics score. Returns ``None`` when the bundle has no storage
    frame (no storage fleet); callers coerce to ``0.0`` so the payload always
    carries the key.
    """
    if storage_all is None:
        return None
    sy = _primary_pass(storage_all[storage_all["year"] == year])
    if sy.empty:
        return None
    return round(float(sy["discharge_mw"].to_numpy(float).sum()) / 1e6, 4)


def _model_storage_monthly(
    storage_all: pd.DataFrame | None, year: int
) -> list[float] | None:
    """Return 12 monthly DISCHARGE GWh from the model's storage frame.

    Discharge basis to match ``_actual_storage_monthly`` (see its docstring):
    the EIA-930 actual is gross discharge for the BAs that report storage at
    all, so the run-page storage-shape diagnostic (ex-C5c — removed from the
    rubric, v2.7) compares whether the model DISCHARGES in the right months.
    The prior net basis (discharge − charge) is ≤ 0 over any month by
    round-trip losses and could never correlate with a discharge-only actual.
    """
    if storage_all is None:
        return None
    sy = _primary_pass(storage_all[storage_all["year"] == year])
    if sy.empty:
        return None
    net = np.zeros(_T, dtype=float)
    for _, row in sy.iterrows():
        h = int(row["hour"])
        if 0 <= h < _T:
            net[h] += float(row.get("discharge_mw", 0.0))
    return [round(float(net[_CUM[m] : _CUM[m + 1]].sum()) / 1e3, 2) for m in range(12)]


# EIA-930 net-generation-by-energy-source series that are storage discharge when
# positive (charging is the negative half). ``battery_discharge`` is the ERCOT
# loader's already-split positive series; ``battery`` / ``pumped_storage`` are the
# generic per-BA series, signed (positive = to grid). The model dispatches both
# li-ion and pumped storage as LP storage, so the actual must include both techs.
_STORAGE_E930_SERIES = ("battery", "pumped_storage", "battery_discharge")


def _actual_storage_twh(e930_year: pd.DataFrame) -> float | None:
    """Return observed storage discharge throughput (TWh) from EIA-930, or None.

    Sums the positive (discharge-to-grid) half of the EIA-930 battery and
    pumped-storage net-generation series for the year. Returns ``None`` when no
    storage series is present or the discharge total is ~0 (the BA had not begun
    reporting a storage breakout, e.g. NEISO 2023) — an absent/zeroed actual is
    not a real observation, so the criterion stays SKIPPED rather than being
    scored against a spurious zero (which ``_pct`` cannot divide by).
    """
    present = e930_year[e930_year["series"].isin(_STORAGE_E930_SERIES)]
    if present.empty:
        return None
    # NOTE (filed with rubric v2.6, deliberately unchanged; the throughput
    # number has been a run-page diagnostic only since v2.7 removed C5b): any
    # NaN hour in a storage series poisons this sum to NaN, so `disch > 1e-6`
    # is False and a partial-coverage year (pre-breakout NaNs — ERCO 2024)
    # returns None. That accidental behavior is the CORRECT outcome (a
    # partial-year actual cannot benchmark a full-year model throughput) but
    # it also nulls a complete year with a stray missing hour; an explicit
    # per-month coverage rule (like `_actual_storage_monthly`'s) would change
    # other ISOs' committed bench values, so it needs its own cross-ISO pass.
    disch = np.clip(present["mw"].to_numpy(float), 0.0, None).sum() / 1e6
    return round(float(disch), 4) if disch > 1e-6 else None


# A bench month is a real storage observation only when this fraction of its
# hours carries a non-NaN value in at least one EIA-930 storage series. Months
# below it (pre-breakout months are 0.0-covered by construction) are emitted as
# null — MISSING, never zero. Robustness constant, not a tuned quantity: it
# tolerates ordinary reporting gaps while refusing to book a month the BA had
# not begun reporting (rubric v2.6, owner amendment 2026-07-16 — the ERCO 2024
# C5c FAIL was a correlation against nine fabricated pre-breakout zeros).
_STORAGE_MONTH_COVERAGE_MIN = 0.9


def _actual_storage_monthly(e930_year: pd.DataFrame) -> list[float | None] | None:
    """Return 12 monthly DISCHARGE GWh from EIA-930 storage series, or None.

    Discharge basis (positive half only), matching the throughput
    diagnostic's basis — and the only basis the actual supports everywhere:
    several BAs report a discharge-only storage series (NEISO ``NG: PS`` —
    pumping shows up as load, never as a negative storage value; ERCOT's
    ``battery_discharge`` is pre-split positive). Summing those series signed
    silently yields gross discharge, while the model side used to report net
    (discharge − charge, ≤ 0 over a month by round-trip losses) — an
    apples-to-oranges comparison a perfectly-cycling model could never pass.
    Both sides are now discharge. (These monthly vectors have been run-page
    diagnostics only since rubric v2.7 removed the C5b/C5c criteria.)

    Months without a real observation are ``None``, never 0.0 (rubric v2.6):
    the ERCOT battery series carries NaN over hours the BA had not yet begun
    reporting a storage breakout (ERCO: mid-Oct-2024), and booking those
    months as zero discharge fabricates an actual — a partial-breakout year
    is visibly partial rather than dressed in invented zeros.
    """
    present = e930_year[e930_year["series"].isin(_STORAGE_E930_SERIES)]
    if present.empty:
        return None
    net = np.zeros(_T, dtype=float)
    covered = np.zeros(_T, dtype=bool)  # hour has >= 1 real (non-NaN) observation
    for _, row in present.iterrows():
        h = int(row["hour"])
        mw = float(row["mw"])
        if 0 <= h < _T and not np.isnan(mw):
            net[h] += max(mw, 0.0)
            covered[h] = True
    if not covered.any() or abs(float(net.sum())) < 1.0:
        return None
    out: list[float | None] = []
    for m in range(12):
        if float(covered[_CUM[m] : _CUM[m + 1]].mean()) < _STORAGE_MONTH_COVERAGE_MIN:
            out.append(None)  # unobserved (e.g. pre-breakout) month: missing, not 0
        else:
            out.append(round(float(net[_CUM[m] : _CUM[m + 1]].sum()) / 1e3, 2))
    return out


def _tail_hours(price_by_zone_hourly: dict[str, np.ndarray], threshold: float) -> int:
    """Count hours whose max zonal LMP across the ISO's zones exceeds ``threshold``.

    The C3c scarcity-tail proxy (rubric §5) is "hours with zonal LMP > threshold".
    We pin ONE definition and use it identically for model and actual: stack the
    per-zone hourly price arrays and count an hour once if the **max across zones**
    is in scarcity, so a localized congestion/scarcity spike in any zone registers
    the hour (a system-wide proxy would dilute it). NaNs (unpadded/missing hours)
    are mapped to -inf so they never count. The actual hub series enters as a
    single "zone", so the same max-across-zones rule reduces to the series itself.
    """
    if not price_by_zone_hourly:
        return 0
    stack = np.vstack(
        [np.asarray(v, dtype=float) for v in price_by_zone_hourly.values()]
    )
    # NaN = an unpadded/missing hour; map to -inf so an all-missing hour never
    # registers as scarcity (and ``max`` raises no all-NaN-slice warning).
    stack = np.nan_to_num(stack, nan=-np.inf)
    return int((stack.max(axis=0) > threshold).sum())


@lru_cache(maxsize=None)
def _actual_lmp_hourly(iso: str, year: int) -> np.ndarray | None:
    """Return the actual hourly LMP series ($/MWh) for an ISO-year, or ``None``.

    Loads ``data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet`` — a
    single hub series with columns ``year, hour, rt, da`` (not zonal). Returns
    the **real-time series alone** — the scarcity-relevant series the C3c tail
    scores — with NaN left in place for hours the RT column does not carry.
    Returns ``None`` when the file or the year is absent, so the tail criterion
    stays SKIPPED rather than scoring against a missing actual. The returned
    array is sorted by hour.

    **NO DA FALLBACK (repaired 2026-09-16, session caiso-284).** This function
    used to fill an RT-NaN hour with that hour's day-ahead price, on the stated
    rationale that it "mirrors the rt→da fallback in ``_actual_avg_lmp`` / C3a".
    That rationale was wrong in kind: C3a's ladder falls back to the DA series
    *as a whole* and then **labels the record ``vs DA``**, so the basis is always
    declared; this fill spliced DA hours into a series the payload goes on to
    call ``actual`` RT, with nothing anywhere recording that it had. Rubric v2.7
    gates every ISO's tail on RT, so a DA hour standing in for a missing RT hour
    is a benchmark of the wrong market carried under the right market's name.
    Measured blast radius over every committed ISO-year: the fill changed a
    tail count in **exactly one** — CAISO 2023, where 48 RT-NaN hours (two whole
    days, Jan 4 and Jan 11) were filled from DA at a mean of $187.22 and pushed
    the payload's ``ordc.hoursGt200.actual`` to **62 h against the gated 47 h**.
    No determination moved, because nothing reads that field and the C3c gate
    reads the pure-RT ``tail/actual_tail.json`` instead; the defect was that a
    DA-contaminated number sat in a keeper's committed payload labelled
    ``actual``. Rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`: an hour with no
    measured RT price has no measured RT price, and NaN says so.
    (`docs/RESULT-caiso284-rescore-on-rt-audit-2026-09-16.md` §2 rows 10–12.)
    """
    from market_sim.config.paths import CALIBRATION_DIR

    p = CALIBRATION_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df = df[df["year"] == int(year)]
    if df.empty:
        return None
    df = df.sort_values("hour")
    return df["rt"].to_numpy(float)


@lru_cache(maxsize=None)
def _actual_rt_padded(iso: str, year: int, hours: int) -> np.ndarray | None:
    """Return the actual hourly RT LMP as an ``(hours,)`` NaN-padded array, or ``None``.

    Same source as :func:`_actual_lmp_hourly` (``actual_lmp_hourly_<ISO>.parquet``
    under the canonical validation-source dir), but scattered by the ``hour``
    column into a fixed ``hours``-length array so it aligns positionally with the
    model's per-hour series for the C3c scarcity-tail count and the demand-weighted
    monthly-MAE. This is the ISO-agnostic replacement for ``derive_ordc_overlay``'s
    ERCOT-only ``_actual_rt`` — it lets the settlement-price overlay block (below)
    score every ISO from its own actuals, not just ERCOT. (That function's CAL_DIR
    was repaired to the post-W1 root long ago; the claim here that it "still points
    at the pre-W1 ``inputs/calibration`` tree" was stale and is dropped.)

    **RT ONLY — no DA fallback** (2026-09-16, caiso-284), for the reason spelled
    out in :func:`_actual_lmp_hourly`. An hour with no measured RT price stays
    NaN here, which is what makes the two consumers honest: ``hoursGt200.actual``
    counts only hours the real-time market actually cleared above the threshold,
    and ``lmpDeltaHr`` carries the int16 NaN sentinel there instead of a
    model−DA difference. The second one also repairs a calendar mismatch in the
    REPORTED-ONLY D-A diurnal measurement, whose
    ``calibration_verdict.score_diurnal_amplitude`` docstring asserts that the
    delta's missing-hour mask and the committed ``rt_hod`` part's mask
    "coincide" — with the fill in place they did not (CAISO 2023: a 363-day
    measured profile was added to a 365-day delta profile, D-A 72.9 % reported
    as 72.5 %, a 0.4 pp band-free error), and with it gone they do.
    """
    from market_sim.config.paths import CALIBRATION_DIR

    p = CALIBRATION_DIR / f"actual_lmp_hourly_{iso}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    df = df[df["year"] == int(year)]
    if df.empty:
        return None
    out = np.full(int(hours), np.nan)
    hr = df["hour"].to_numpy()
    rt = df["rt"].to_numpy(float)
    # Guard against a stray out-of-range hour index (leap-year / DST artifacts).
    valid = (hr >= 0) & (hr < int(hours))
    out[hr[valid]] = rt[valid]
    return out


def _gt_count(series: np.ndarray | None, cut: float) -> int | None:
    """Count finite entries of ``series`` strictly above ``cut`` (``None`` -> ``None``)."""
    if series is None:
        return None
    return int(np.nansum(np.asarray(series, dtype=float) > cut))


@lru_cache(maxsize=1)
def _actual_lmp_table() -> dict:
    """Load the derived actual-LMP reference (``scripts/data/derive_actual_lmp.py``).

    Returns an empty dict when the reference is absent, so the dashboard renders
    a model-only price card rather than failing.

    The reference resolves through ``paths.CALIBRATION_DIR``
    (``data/raw/_validation-source``) — the single post-W1 home. The former
    second candidate ``REPO / "inputs" / "calibration"`` was dropped: W1 was a
    pure ``git mv``, so no post-W1 checkout has an ``inputs/`` root at all and
    the branch was unreachable (every other ``actual_lmp.json`` reader already
    resolved to ``CALIBRATION_DIR`` alone). Rule 26 [R-DELETE].
    """
    from market_sim.config.paths import CALIBRATION_DIR

    p = CALIBRATION_DIR / "actual_lmp.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _actual_avg_lmp(iso: str, year: int) -> dict | None:
    """Return ``{da?, rt?}`` actual avg LMP ($/MWh) for an ISO-year, or None.

    The ``src`` provenance string in the reference is dropped here; only the
    numeric day-ahead / real-time means flow into the dashboard payload.
    """
    rec = _actual_lmp_table().get(str(iso), {}).get(str(int(year))) or {}
    # Key order is the bench-part serialization order — the v2.4 lw fields
    # append after the legacy equal-hour fields (matching the committed-part
    # retrofit in retrofit_lw_price_bench.py (retired script, deleted 2026-09-05), so re-renders are
    # byte-stable).
    out = {
        k: rec[k]
        for k in (
            "da",
            "rt",
            "da_mon",
            "rt_mon",
            "da_lw",
            "rt_lw",
            "da_lw_mon",
            "rt_lw_mon",
        )
        if k in rec
    }
    # NOT included: the `da_cov` / `rt_cov` staging-coverage vectors. They are
    # what puts C3a/C3b on a like-for-like calendar, but the bench part's
    # PAYLOAD FINGERPRINT covers this builder's output shape, so adding a key
    # here marks EVERY committed part of EVERY ISO stale at once (measured
    # 2026-09-10: 0 -> 31 of 31). The scorer therefore reads the vectors from
    # the same committed reference this function reads
    # (calibration_verdict._actual_lmp_coverage), which changes no part.
    return out or None


def _pearson(m: np.ndarray, o: np.ndarray) -> float:
    m = m - m.mean()
    o = o - o.mean()
    d = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / d) if d > 0 else 0.0


def _nrmse(m: np.ndarray, o: np.ndarray) -> float:
    den = float(o.mean())
    return float(np.sqrt(((m - o) ** 2).mean()) / den) if den > 0 else 9.9


def _fossil_co2(
    class_twh: dict[str, float], intensity: dict[str, float]
) -> tuple[float, dict[str, float]]:
    """Return ``(total Mt CO2, {class: Mt})`` for fossil classes.

    A class's generation (TWh) times its CO2 intensity (metric tonnes / MWh,
    from :func:`market_sim.data.egrid.class_co2_intensity`) is metric tonnes of
    CO2 expressed in Mt (1 TWh = 1e6 MWh, 1 Mt = 1e6 t, so TWh × t/MWh = Mt).
    Only classes with a positive intensity contribute, so non-fossil classes
    (no intensity) are dropped.
    """
    by = {
        k: round(class_twh[k] * intensity[k], 4)
        for k in class_twh
        if intensity.get(k, 0.0) > 0.0
    }
    return round(sum(by.values()), 3), by


def _capture(r: float, nrmse: float, dev: float) -> float:
    """Geometric-mean capture% from r, NRMSE and annual fractional deviation."""
    rs = max(0.0, r)
    ns = max(0.0, 1.0 - nrmse)
    ls = max(0.0, 1.0 - abs(dev))
    return round(100.0 * (rs * ns * ls) ** (1.0 / 3.0), 1)


# Net/gross parasitic-load factor for reconstructing CAMPD annual GROSS from the
# committed NET series (net = gross x factor). Absent-plant fallback is the
# measured PJM-CC pooled mean (~2.7% parasitic, flat year-round; diagnosis
# docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md §2).
_DEFAULT_PARASITIC = 0.973
# EIA-923-net / CAMPD-gross ratio above which a CEMS record is judged INCOMPLETE
# (physically gross >= net, so a ratio > 1 already signals missing MWh; 1.1 adds
# margin for survey noise). The CT-only 2x1 signature lands at ~1.45-1.59.
_CT_ONLY_RATIO = 1.1


@lru_cache(maxsize=1)
def _parasitic_factors() -> dict[int, float]:
    """Return ``{plant_id: net/gross}`` for reconstructing CAMPD gross.

    The same derived artifact the bundle's CAMPD-net series was built from
    (``run_calibration_full._parasitic_factor_map``); empty when the artifact
    is missing, so absent plants fall back to :data:`_DEFAULT_PARASITIC`.
    """
    return rcf._parasitic_factor_map()


def _flag_ct_only_reporters(bplants: dict[str, dict]) -> list[dict]:
    """Flag CT-only CEMS reporters in ``bplants``; return their provenance rows.

    A complete CEMS record's gross generation exceeds the plant's EIA-923 NET
    generation (gross >= net). A plant whose EIA-923 annual net exceeds
    :data:`_CT_ONLY_RATIO` x its CAMPD annual gross is therefore submitting an
    INCOMPLETE record — the 2x1 combined-cycle signature where only the
    combustion-turbine block reports to CEMS (steam-turbine MWh absent), so
    923-net / CAMPD-gross ~ 1.5. Their CAMPD series understates the plant,
    making any CAMPD-basis per-plant capture / Δ-vs-CEMS heatmap structurally
    unfair, so each is marked ``ct_only`` and scored on its EIA-923 monthly row
    instead (:func:`_capture_on_923`; diagnosis §3a). CAMPD gross is
    reconstructed from the committed net as ``c_ann / parasitic_factor``.
    Mutates ``bplants`` in place; returns one provenance row per flagged plant.
    """
    factors = _parasitic_factors()
    flagged: list[dict] = []
    for code_s, p in bplants.items():
        c_ann = float(p.get("c_ann", 0.0))
        e_ann = float(p.get("e_ann", 0.0))
        # nodata plants (no usable CAMPD) are already excluded from CAMPD-basis
        # scoring; ct_only targets plants WITH a CAMPD series that is too small.
        if c_ann <= 0.0 or e_ann <= 0.0:
            continue
        # Slice keys ("<code>:<KLASS>") carry the plant's parasitic factor;
        # the provenance row keeps the full key so the flag stays per-slice.
        factor = factors.get(bm.plant_code_of_key(code_s), _DEFAULT_PARASITIC)
        campd_gross = c_ann / factor if factor > 0.0 else c_ann
        if campd_gross > 0.0 and e_ann > _CT_ONLY_RATIO * campd_gross:
            ratio = round(e_ann / campd_gross, 3)
            p["ct_only"] = True
            p["ct_ratio"] = ratio
            flagged.append(
                {
                    "code": code_s if bm.KEY_SEP in code_s else int(code_s),
                    "name": p.get("name", str(code_s)),
                    "group": p.get("group", "?"),
                    "ratio": ratio,
                }
            )
    return sorted(flagged, key=lambda r: r["ratio"], reverse=True)


def _capture_on_923(
    mw: np.ndarray, e_mon: np.ndarray, m_ann: float, e_ann: float
) -> tuple[float | None, float | None, float | None]:
    """Per-plant capture on the EIA-923 MONTHLY basis: ``(r, NRMSE, capture%)``.

    The CT-only fallback for the default CAMPD-hourly capture: a plant whose
    CEMS record is incomplete is scored on its EIA-923 monthly row instead — a
    12-point model-vs-923 monthly correlation and NRMSE plus the annual 923
    deviation. Returns ``(None, None, None)`` when the 923 row is empty or the
    model series is flat.
    """
    m_mon = np.asarray(_monthly_gwh(mw), dtype=float)
    e_mon = np.asarray(e_mon, dtype=float)
    if e_mon.sum() <= 0.0 or m_mon.std() <= 0.0:
        return None, None, None
    r = round(_pearson(m_mon, e_mon), 3)
    nr = round(_nrmse(m_mon, e_mon), 3)
    dev = (m_ann - e_ann) / e_ann if e_ann > 0.0 else 0.0
    return r, nr, _capture(r, nr, dev)


def _btm_share(
    plant_id: int,
    group: str,
    iso: str = "ERCOT",
    measured: dict[int, float] | None = None,
) -> float:
    """Behind-the-meter host self-supply share of net gen for a CHP plant.

    Mirrors :func:`market_sim.data.fleet.chp_btm_pct` — the ISO's derived
    EIA-923 sector (thermal-tranches artifact) first, then the hardcoded
    ERCOT sector map — so the report's add-back uses the same share the LP
    pull-out used. ``measured`` (a 0-1 fraction map — the nyiso-147 measured
    per-plant shares, resolved by artifact PRESENCE since nyiso-149, never by
    the registering run's flag) supersedes the sector share for the plants it
    carries, so the shared bench part's grid-delivered actuals stay on the
    measured basis whatever the run's config.
    """
    if group not in ("CC_CHP", "CT_CHP", "ST_CHP"):
        return 0.0
    if measured is not None and int(plant_id) in measured:
        return float(measured[int(plant_id)])
    from market_sim.data.chp import chp_btm_pct

    return chp_btm_pct(int(plant_id), group, iso=iso) / 100.0


@lru_cache(maxsize=1)
def _eia860_plant_info() -> tuple[dict[int, float], dict[int, str]]:
    """Return ``({plant_id: nameplate MW}, {plant_id: name})`` from EIA-860.

    The national per-plant nameplate (summed over units) and plant name, so
    non-ERCOT bundles (PJM, etc.) — whose plants are absent from the ERCOT
    CAMPD bin sheet — still get a real capacity and label in the dashboard.

    **Unions the within-window retiree vintage** (pjm-159, the cross-ISO defect
    pjm-158 §1.1 found): the committed operable snapshot is a single recent
    vintage, so a plant that ran through part of the backcast window and retired
    before that vintage is absent from it — exactly the gap
    :func:`market_sim.data.fleet.load_retired_within_window` exists to close on
    the model side. Without the union those plants fell through the
    ``or 1.0`` guard at the payload sites and silently defaulted to ``npl = 1``,
    which destroys their per-plant hourly ``campd`` blob (stored as
    ``uint8 % of nameplate × npl``) while leaving ``c_ann`` and every annual gate
    correct — so it was invisible to the gates and wrong for any probe
    reconstructing hourly/monthly actuals from the blob. Measured at the fix:
    PJM 2022 stranded 4 plants / 9.87 TWh (W H Sammis 1,706.5 MW, Homer City
    2,012.0, AES Warrior Run 229.0, Joliet 29 1,320.0), and MISO / NEISO / CAISO
    were affected the same way.

    Operable wins on conflict — a plant present in both keeps its operable
    nameplate, so every already-correct entry is byte-identical and the union is
    purely additive. No parameter is introduced: both vintages are the same
    committed EIA-860 release.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME
    from market_sim.data.fleet.eia860 import EIA_860_RETIRED_WINDOW_PARQUET_NAME

    cols = ["plant_id", "plant_name", "nameplate_capacity_mw"]
    npl: dict[int, float] = {}
    nm: dict[int, str] = {}
    # Retiree vintage FIRST so the operable pass overwrites it on conflict.
    for name in (EIA_860_RETIRED_WINDOW_PARQUET_NAME, EIA_860_PARQUET_NAME):
        path = EIA_860_DIR / name
        if not path.exists():
            continue
        df = pd.read_parquet(path, columns=cols)
        df["plant_id"] = df["plant_id"].astype(int)
        npl.update(
            {
                int(k): float(v)
                for k, v in df.groupby("plant_id")["nameplate_capacity_mw"]
                .sum()
                .items()
            }
        )
        nm.update(
            {
                int(k): str(v)
                for k, v in df.groupby("plant_id")["plant_name"].first().items()
            }
        )
    return npl, nm


def _nameplates() -> dict[int, float]:
    """Plant nameplate MW: ERCOT bin sheet first, EIA-860 fleet for the rest."""
    bins = pd.read_csv(ScenarioConfig().campd_bins_path)
    out = dict(_eia860_plant_info()[0])
    out.update(zip(bins["Plant_Code"].astype(int), bins["Nameplate_MW"].astype(float)))
    return out


def _plant_names() -> dict[int, str]:
    """Plant names: ERCOT bin sheet first, EIA-860 fleet for the rest."""
    bins = pd.read_csv(ScenarioConfig().campd_bins_path)
    out = dict(_eia860_plant_info()[1])
    out.update(zip(bins["Plant_Code"].astype(int), bins["Plant_Name"].astype(str)))
    return out


def _coal_group(klass: str) -> str:
    return klass


_BINS_CACHE: dict[str, dict] = {}


def _tranche_bands_for_bundle(bdir: Path) -> dict[int, list]:
    """Return ``{plant_code: tranche bands}`` for a bundle's stored config.

    Reads the bundle's ``run_config.json`` (the serialized scenario config the
    run was generated with) and computes each plant's offer-curve tranche bands
    via :func:`market_sim.data.fleet.plant_tranche_bands`, so the dashboard's
    CF chart can mark where each band engages and the multiplier priced there.
    Returns ``{}`` for bundles without a stored config.
    """
    cfg_path = bdir / "run_config.json"
    if not cfg_path.exists():
        return {}
    try:
        sc = json.loads(cfg_path.read_text())["scenario_config"]
        # Tolerate configs serialized under an older/newer schema (fields added
        # or removed since the bundle was written — e.g. the rule-26 removal of
        # the never-wired coal_*_hr_mult / coal_peak_hr_penalty knobs): keep only
        # keys ScenarioConfig still defines so historical bundles keep rendering.
        import dataclasses as _dc

        _known = {f.name for f in _dc.fields(ScenarioConfig)}
        config = ScenarioConfig(**{k: v for k, v in sc.items() if k in _known})
    except Exception:
        return {}
    bins_path = config.campd_bins_path
    rows = _BINS_CACHE.get(bins_path)
    if rows is None:
        bins = load_campd_bins(bins_path)
        rows = {int(r["Plant_Code"]): r for _, r in bins.iterrows()}
        _BINS_CACHE[bins_path] = rows
    out: dict[int, list] = {}
    for code, row in rows.items():
        bands = plant_tranche_bands(row, config)
        if bands:
            out[code] = bands
    return out


def _load_scarcity_overlay(bdir: Path, year: int, hours: int) -> dict | None:
    """Load a bundle-year's post-solve scarcity overlay sidecar, or ``None``.

    ISO-agnostic (G-20a): the overlay is the ``lmp_scarcity = lmp +
    scarcity_adder`` series written next to the energy-only duals by whichever
    ``derive_*_overlay.py`` ran for this ISO — ERCOT ORDC, PJM two-step, NYISO/
    NEISO RCPF, or CAISO LOLP. They all write the same ``scarcity.parquet``
    schema (``year, hour, scarcity_adder, lmp, lmp_scarcity``). Prefers the
    ERCOT calibrated reliability-deployment series
    (``scarcity_reldeploy2500.parquet``) and falls back to the default
    ``scarcity.parquet``; returns ``None`` when neither exists (a run with no
    derived overlay), so the energy-only payload is left exactly as it was.

    Returns ``{adder, lmp, lmp_scarcity, series, reldeploy}`` with the three
    hourly arrays NaN-padded to ``hours`` (the system-wide adder is added
    uniformly to every zone, mirroring ERCOT's system-level reserve price
    adder), the source file name and the reliability-deployment MW parsed
    from it for the display label.
    """
    for name in ("scarcity_reldeploy2500.parquet", "scarcity.parquet"):
        p = bdir / name
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[df["year"] == year]
        if df.empty:
            continue
        hh = df["hour"].to_numpy()
        adder = np.full(hours, np.nan)
        lmp = np.full(hours, np.nan)
        lmp_scar = np.full(hours, np.nan)
        adder[hh] = df["scarcity_adder"].to_numpy(float)
        lmp[hh] = df["lmp"].to_numpy(float)
        lmp_scar[hh] = df["lmp_scarcity"].to_numpy(float)
        m = re.search(r"reldeploy(\d+)", name)
        return {
            "adder": adder,
            "lmp": lmp,
            "lmp_scarcity": lmp_scar,
            "series": name,
            "reldeploy": float(m.group(1)) if m else 0.0,
        }
    return None


def build_payload(runs: list[tuple[str, Path]], years: set[int] | None = None) -> dict:
    """Assemble the embedded data for every run, with a shared CAMPD benchmark.

    Returns a dict with: groups / labels / zones / years; ``bench`` (per year:
    per-plant CAMPD CF + annual + monthly, EIA-923 per-plant annual + monthly,
    EIA-930 per-fuel annual + hourly); and ``model`` (per run, per year:
    per-plant model CF + annual + monthly + per-plant r / NRMSE / capture%, the
    non-fossil model annual, the system fuel-vs-930 table rows, and
    ``volErr`` -- the signed volume error (model vs the authoritative actuals
    source per class) decomposed by zone and month for the heatmap).
    """
    npl = _nameplates()
    pnames = _plant_names()
    labels = [lab for lab, _ in runs]
    years_set: set[int] = set()
    zones_set: set[str] = set()
    groups_set: set[str] = set()

    bench: dict[int, dict] = {}  # year -> benchmark payload
    model_runs: list[dict] = []  # per run -> {year -> payload}

    for label, bdir in runs:
        meta = json.loads((bdir / "meta.json").read_text())
        tr_bands = _tranche_bands_for_bundle(bdir)
        # nyiso-147 introduced the measured CHP BTM shares; nyiso-149 PINS the
        # bench side to them. The shared bench part states the ACTUAL grid
        # delivery — a physical fact — so its per-plant ``btm`` fields and the
        # classFull subtrahend use the measured shares whenever the measured
        # artifact exists, INDEPENDENT of the registering run's
        # ``nyiso_chp_btm_measured`` flag. Gating this on the flag made the
        # committed NYISO parts flip between flag-off and flag-on
        # registrations (sector-carve subtrahend re-arming the ±3% family
        # reconcile: ×1.07–×1.19 on every gas class —
        # FINDING-nyiso149-bench-root-cause-2026-08-22 §3). The run's OWN
        # add-back (what its LP actually held out) still comes from the
        # bundle's ``btm_twh`` below. [R-ACCURATE]
        _btm_measured: dict[int, float] | None = None
        if meta.get("iso") == "NYISO":
            from market_sim.data.chp import measured_chp_btm_pct_nyiso

            _measured_map = measured_chp_btm_pct_nyiso()
            if _measured_map:
                _btm_measured = {c: p / 100.0 for c, p in _measured_map.items()}
        # The MODEL-side add-back must mirror what THIS run's LP held out
        # (fleet/assembly.py: the measured share under
        # ``nyiso_chp_btm_measured``, the sector default otherwise). nyiso-192
        # found the per-plant payload site adding the 35 % sector default on
        # top of an LP that held out the measured share (0 % at Sithe
        # Independence 54547): +2.1 TWh/yr of phantom flat energy on one plant,
        # +6.6 TWh/yr across the NYISO CHP classes, inflating the nyiso-190/191
        # plant-grain record 3x at its top row. [R-ACCURATE]
        _btm_run_measured: dict[int, float] | None = (
            _btm_measured if meta.get("nyiso_chp_btm_measured") else None
        )
        run_years: dict[int, dict] = {}
        # Non-CEMS gas-class cogen block per rendered year — (grid, full-plant)
        # TWh — for the CEMS-anchor writer (EIA930_NG_CELL_CORRUPT ISOs): a
        # preliminary-923 year carries the latest complete vintage's block
        # (rule 16 keeps all years in one bundle, so it is always available).
        gas_cogen_by_year: dict[int, tuple[float, float]] = {}
        # Strict: these three benchmark frames live in the GITIGNORED shared
        # store beside the bundle, so a bundle that arrived by fetch or fresh
        # checkout has the meta reference without the bytes. require_* names the
        # bundle, the input and the zero-LP remedy instead of letting a None path
        # reach pandas as a bare TypeError (CLAUDE.md rule 34 [R-SHARD-PROMOTABLE]).
        e923_all = pd.read_parquet(require_bundle_input(bdir, "eia923"))
        e930_all = pd.read_parquet(require_bundle_input(bdir, "eia930"))
        campd_all = pd.read_parquet(require_bundle_input(bdir, "campd"))
        sys_all = pd.read_parquet(bdir / "system.parquet")
        # Per-storage-unit hourly charge/discharge (run_calibration_full
        # _storage_frame), present only when the bundle has a storage fleet.
        # Feeds the run-page storage-throughput diagnostic (ex-C5b, removed
        # from the rubric v2.7); gitignored like dispatch/ + system.parquet,
        # so it is read at render time and its annual scalar baked into the
        # committed payload.
        storage_all = (
            pd.read_parquet(bdir / "storage.parquet")
            if (bdir / "storage.parquet").exists()
            else None
        )
        # Behind-the-meter must-run per (year, pass, class) — the same off-grid
        # CHP host self-supply the LP held out, as the calibration report uses
        # it (run_calibration_full). Drives the system-wide generation mix.
        btm_all = (
            pd.read_parquet(bdir / "btm.parquet")
            if (bdir / "btm.parquet").exists()
            else None
        )
        for year in meta["years"]:
            if years is not None and int(year) not in years:
                continue
            years_set.add(int(year))
            # Re-bucket genuinely-mixed gas-thermal plants into OTHER_FOSSIL on
            # both the model and the EIA-923 side, so a coin-flip plant scores in
            # the same bucket on both and stops distorting the clean classes
            # (a scoring transform — dispatch itself is unchanged).
            # Primary-pass dispatch: the commitment re-solve (P2) when the
            # bundle ran one, else P1 (see _primary_pass).
            _disp_path = bdir / "dispatch" / f"{year}_P2.parquet"
            if not _disp_path.exists():
                _disp_path = bdir / "dispatch" / f"{year}_P1.parquet"
            disp = apply_other_fossil_scoring(
                pd.read_parquet(_disp_path),
                year,
                plant_col="plant_code",
            )
            e923 = apply_other_fossil_scoring(
                e923_all[e923_all["year"] == year],
                year,
                plant_col="plant_id",
            )
            e930 = e930_all[e930_all["year"] == year]
            campd = campd_all[campd_all["year"] == year]

            # Model hourly MW per (fossil) plant AND class. Keyed by the
            # serialized (plant_code, klass) slice key — bare "<code>" for a
            # single-class plant (wire format unchanged), "<code>:<KLASS>" per
            # class slice of a multi-class plant. The old dicts keyed by
            # plant_code alone silently attributed a multi-class plant's whole
            # measured series to its alphabetically-last class and dropped the
            # other classes' model dispatch (nyiso-88 finding §5).
            dm = disp[(disp["plant_code"] > 0) & (disp["klass"].isin(FOSSIL_GROUPS))]
            mw_pc: dict[tuple[int, str], np.ndarray] = {}
            zone_p: dict[int, str] = {}
            for (code, klass), g in dm.groupby(["plant_code", "klass"], observed=True):
                arr = (
                    g.groupby("hour")["mw"]
                    .sum()
                    .reindex(range(_T), fill_value=0.0)
                    .to_numpy(float)
                )
                mw_pc[(int(code), str(klass))] = arr
                zone_p[int(code)] = str(g["zone"].iloc[0])
                zones_set.add(zone_p[int(code)])
                groups_set.add(str(klass))
            classes_p: dict[int, list[str]] = {}
            for _code, _klass in mw_pc:
                classes_p.setdefault(_code, []).append(_klass)
            classes_p = {c: sorted(ks) for c, ks in classes_p.items()}
            multi_p = {c: ks for c, ks in classes_p.items() if len(ks) > 1}
            mw_p: dict[str, np.ndarray] = {}
            grp_p: dict[str, str] = {}
            code_p: dict[str, int] = {}
            for (code, klass), arr in mw_pc.items():
                key = bm.slice_key(code, klass if code in multi_p else None)
                mw_p[key] = arr
                grp_p[key] = klass
                code_p[key] = code

            # CAMPD net hourly per plant (benchmark — built once on run 0).
            cn_p: dict[int, np.ndarray] = {}
            for code, g in campd.groupby("plant_id", observed=True):
                a = np.nan_to_num(g.sort_values("hour")["net_mw"].to_numpy(float))
                cn_p[int(code)] = np.concatenate(
                    [a, np.zeros(max(0, _T - a.shape[0]))]
                )[:_T]

            mcols = [f"m{i:02d}" for i in range(1, 13)]
            # EIA-923 per (plant, klass) — the slice actuals and the monthly
            # split-fallback basis, as a 13-vector [annual_mwh, m01..m12] so
            # the slice ``e_ann`` stays on the reported annual (NOT the
            # monthly sum, which can differ) exactly like the plant total did.
            # Rows map onto each plant's MODEL classes (exact name ->
            # technology family -> largest class) so a single-class plant
            # keeps its whole-plant e923 byte-identical and a multi-class
            # plant's e923 lands in the measured class.
            e923_pk: dict[int, dict[str, np.ndarray]] = {}
            for (pid, klass), g in e923.groupby(["plant_id", "klass"], observed=True):
                arr = np.concatenate(
                    [[float(g["annual_mwh"].sum())], g[mcols].sum().to_numpy(float)]
                )
                d = e923_pk.setdefault(int(pid), {})
                d[str(klass)] = d.get(str(klass), np.zeros(13)) + arr
            # Measured-series split for multi-class plants (the basis ladder:
            # CAMPD unit-level hourly shares, then EIA-923 monthly shares,
            # then EIA-860 nameplate proration — scripts/lib/bench_multiclass,
            # rules 13/14). ``cn_s``/``grp_b`` are the slice-keyed bench-side
            # dicts every consumer below joins on.
            _iso_bm = str(meta.get("iso", "ERCOT"))
            unit_hr, _bm_unres = (
                bm.unit_class_hourly(_iso_bm, int(year), multi_p)
                if multi_p
                else ({}, {})
            )
            npl_fam = bm.plant_class_nameplates(set(multi_p)) if multi_p else {}
            e923_slices: dict[int, dict[str, np.ndarray]] = {}
            for code, klasses in classes_p.items():
                if code in multi_p:
                    e923_slices[code] = bm.map_e923_to_model_classes(
                        e923_pk.get(code, {}),
                        klasses,
                        bm.class_nameplate_split(npl_fam.get(code, {}), klasses),
                        # Every consumer below reads these as the 13-vector
                        # [annual, m01..m12] that ``e923_pk`` is built as, and
                        # slices ``[1:]`` for twelve months. A multi-class plant
                        # with NO EIA-923 rows has no input array to take the
                        # length from, so the length must be stated here or the
                        # month loop runs off an 11-long array (MISO 2025).
                        empty_len=13,
                    )
                else:
                    whole = np.zeros(13)
                    for arr in e923_pk.get(code, {}).values():
                        whole = whole + arr
                    e923_slices[code] = {klasses[0]: whole}
            # Per-slice nameplate for EVERY dispatch plant (model payload CF
            # scale needs it whether or not the plant is CAMPD-benched).
            npl_s: dict[str, float] = {}
            # pjm-159: the `or 1.0` guard below is a last resort, and it used to
            # be SILENT — a plant missing from every EIA-860 vintage got npl = 1,
            # which destroys its hourly `campd` blob while leaving `c_ann` and
            # all annual gates correct. Collect and report instead, so the next
            # vintage gap is visible on the build rather than found by a probe
            # three sessions later.
            _npl_missing: list[int] = []
            for code, klasses in classes_p.items():
                cap_plant = float(npl.get(code, 0.0)) or 1.0
                if not float(npl.get(code, 0.0)):
                    _npl_missing.append(int(code))
                if code not in multi_p:
                    npl_s[str(code)] = cap_plant
                else:
                    _shares = bm.nameplate_shares(
                        bm.class_nameplate_split(npl_fam.get(code, {}), klasses),
                        klasses,
                        cap_plant,
                    )
                    for k in klasses:
                        npl_s[bm.slice_key(code, k)] = _shares[k]
            if _npl_missing:
                print(
                    f"  WARNING {meta.get('iso', '?')} {year}: "
                    f"{len(_npl_missing)} plant(s) have NO EIA-860 nameplate in "
                    "either the operable or the within-window retiree vintage and "
                    "fall back to npl = 1 MW — their per-plant hourly `campd` blob "
                    "is NOT usable (c_ann and annual gates are unaffected): "
                    + ", ".join(str(c) for c in sorted(_npl_missing)),
                    file=sys.stderr,
                )
            cn_s: dict[str, np.ndarray] = {}
            grp_b: dict[str, str] = {}
            split_notes: dict[str, str] = {}
            for code, cn in cn_p.items():
                code = int(code)
                klasses = classes_p.get(code)
                if klasses is None:
                    continue  # CAMPD plant absent from the dispatch (as before)
                if code not in multi_p:
                    key = str(code)
                    cn_s[key] = cn
                    grp_b[key] = klasses[0]
                    continue
                uh = unit_hr.get(code)
                covered = (
                    [k for k in klasses if uh.get(k) is not None and uh[k].sum() > 0]
                    if uh
                    else []
                )
                caps = bm.class_nameplate_split(npl_fam.get(code, {}), klasses)
                if covered:
                    # The facility CEMS series sums the REPORTING units only,
                    # so it splits across the CEMS-covered classes; an
                    # uncovered class's CEMS slice is genuinely zero (its
                    # actual lives in its EIA-923 slice — the ct_only shape).
                    series, basis = bm.split_measured_series(
                        cn,
                        covered,
                        {k: caps.get(k, 0.0) for k in covered},
                        {k: uh[k] for k in covered},
                        None,
                    )
                    for k in klasses:
                        if k not in series:
                            series[k] = np.zeros(_T)
                else:
                    series, basis = bm.split_measured_series(
                        cn,
                        klasses,
                        caps,
                        None,
                        e923_slices.get(code),
                    )
                for k in klasses:
                    key = bm.slice_key(code, k)
                    cn_s[key] = series[k]
                    grp_b[key] = k
                    split_notes[key] = basis

            # ---- benchmark payload (newest bundle wins) ----
            # Rebuilt for every run, so the LAST run in the id-sorted registry
            # (the newest bundle covering each year) supplies the shared
            # benchmark. Building it once from run 0 froze the benchmark to
            # the OLDEST bundle: its plant -> group classification and EIA-923
            # class totals could predate the current taxonomy (e.g. PJM coal
            # as one generic COAL, COAL_SUB before the SUB -> COAL_PRB
            # rename), making every newer run compare against incompatible
            # groups (-100% "Coal" rows, vanished class heatmaps).
            bplants: dict[str, dict] = {}
            for key, cn in cn_s.items():
                code = bm.plant_code_of_key(key)
                grp = grp_b[key]
                cap = float(npl_s.get(key, 0.0)) or 1.0
                # Slice e923: the (plant, klass) measured record mapped onto
                # the model classes; a single-class plant's slice is its whole
                # plant (byte-identical to the pre-split payload).
                _e13 = e923_slices.get(code, {}).get(grp, np.zeros(13))
                _e_mon = _e13[1:]
                e_ann = float(_e13[0]) / 1e6
                bplants[key] = {
                    "name": pnames.get(code, str(code)),
                    "zone": zone_p.get(code, "?"),
                    "group": grp,
                    "npl": round(cap),
                    # No usable CAMPD hourly series (plant absent from CEMS
                    # or all-NaN, e.g. some waste-coal units): flagged so the
                    # charts show the model without a misleading flat-zero
                    # 'actual' comparison.
                    "nodata": bool(cn.sum() <= 0.0),
                    "campd": _b64(100.0 * cn / cap),
                    "c_ann": round(float(cn.sum()) / 1e6, 4),
                    "c_mon": _monthly_gwh(cn),
                    "e_ann": round(e_ann, 4),
                    "btm": round(
                        e_ann
                        * _btm_share(
                            code,
                            grp,
                            meta.get("iso", "ERCOT"),
                            measured=_btm_measured,
                        ),
                        4,
                    ),
                    "e_mon": [round(x, 2) for x in (_e_mon / 1e3)],
                }
                if key in split_notes:
                    bplants[key]["split"] = split_notes[key]
            # CT-only CEMS reporters: EIA-923 net > 1.1x CAMPD gross is a
            # physically impossible complete record (the 2x1 CC block reports
            # only its combustion turbines). Flag them so the per-plant capture
            # scores on the EIA-923 monthly row (below), not the understated
            # CAMPD series, and carry the provenance into the bench payload.
            ct_only_rows = _flag_ct_only_reporters(bplants)
            if ct_only_rows:
                print(
                    f"  {meta.get('iso', '?')} {year}: CT-only CEMS bench flag "
                    f"(923 net > 1.1x CAMPD gross) — scored on EIA-923 monthly: "
                    + ", ".join(
                        f"{r['code']} {r['name']} ({r['ratio']:.2f}x)"
                        for r in ct_only_rows
                    )
                )
            e = {
                s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy(float)
                for s in e930["series"].unique()
            }
            # Full EIA-923 net generation per fossil class (TWh) — every
            # 923 plant of the class, NOT just the ones the model matches.
            # This is the true class total the generation-mix benchmark and
            # the zonal Δ-vs-923 are scaled to (matched plants understate
            # it, e.g. CC_REGULAR 145 TWh vs ~138 matched in 2024).
            e923_cls = e923.groupby("klass")["annual_mwh"].sum()
            # Grid-delivered benchmark (2026-06-14, user directive): subtract
            # each class's behind-the-meter CHP host supply (btm.parquet, the
            # authoritative BTM held out of the LP) from the full EIA-923 class
            # total, so the benchmark is what actually reached the grid — the
            # same basis the model (grid LP, no add-back) and the gate score on.
            # ISOs without a btm.parquet (no CHP split) keep full 923.
            btm_cls = {}
            btm_cls_bench = {}
            if btm_all is not None:
                _by = _primary_pass(btm_all[btm_all["year"] == year])
                btm_cls = dict(zip(_by["klass"], _by["btm_twh"]))
                # Benchmark-basis BTM (nyiso-149): the measured-share class
                # totals, flag-independent, so the shared bench part cannot
                # flip with the registering run's config. Bundles predating
                # the column fall back to the run basis (their btm_twh).
                _bcol = "btm_bench_twh" if "btm_bench_twh" in _by.columns else "btm_twh"
                btm_cls_bench = dict(zip(_by["klass"], _by[_bcol]))
            # Every actual class is kept (not just the hardcoded MIX_GROUPS)
            # so the model's real plant classification — e.g. EIA-923-derived
            # coal ranks COAL_BIT / COAL_PRB / COAL_WC — carries its actual
            # into the table for every ISO. groups_set picks them up below.
            groups_set.update(str(g) for g in e923_cls.index)
            _e930d = {
                f: round(float(e.get(f, np.zeros(1)).sum()) / 1e6, 3)
                for f in ("gas", "coal", "nuclear", "wind", "solar")
            }
            # Carry the EIA-930 "Other Fuel Sources" total when the bundle was
            # re-extracted with it (eia_loader._EIA930_BENCHMARK_COLUMNS adds the
            # NG: OTH series), so reconcile_vintage_classes can subtract only the
            # GENUINELY-folded geothermal+biomass. A bundle predating the series
            # has no "other" key, and reconcile falls back to the per-ISO
            # EIA930_GAS_FOLDS_GEO_BIOMASS allowlist — no silent regression.
            if "other" in e:
                _e930d["other"] = round(float(e["other"].sum()) / 1e6, 3)
            # Carry the EIA-930 "Petroleum" total (NG: OIL) on the same terms:
            # present when the bundle's extract carries the series, absent
            # otherwise, so reconcile_vintage_classes falls back to the gas-only
            # family and a bundle predating it re-renders byte-identical
            # (nyiso-239; the identical "carry it when present" contract the
            # "other" series above established).
            if "oil" in e:
                _e930d["oil"] = round(float(e["oil"].sum()) / 1e6, 3)
            # G-21b split anchor: CEMS-net coal-family total (every coal unit
            # ≥25 MW is metered), consumed by calibration_verdict's C2
            # preliminary-vintage fallback so an incomplete family gates the
            # measured split, not the BA-reported 930 per-fuel cell (whose
            # coal attribution runs −17..−21 TWh below CEMS in MISO and
            # +7..+11 above in PJM). Built from the same CAMPD frame as the
            # plant benchmark above — regenerating the bench part can never
            # silently drop the anchor. The render is the anchor's SOLE
            # writer (an earlier post-hoc splice script wrote an all-ISO-
            # plants basis and was deleted 2026-07-12: two writers with
            # different coverage bases would contaminate the k-ratio when a
            # bench year is regenerated by one and backfilled by the other;
            # non-MISO parts keep the splice-basis values consistently until
            # their next registration atomically re-renders all their years).
            # Coal-plant coverage = the model dispatch's class map (grp_p).
            # This under-counts the full ISO CAMPD coal total by a stable
            # ~8% in MISO (CAMPD coal plants with no dispatch rows), but the
            # verdict's anchor NEVER uses the level raw: it multiplies by the
            # in-run complete-vintage ratio k = Σ classFull-coal ÷ coal_cems,
            # which cancels any coverage basis so long as it is CONSISTENT
            # across the run's years — which a single class map guarantees.
            # (An e923-taxonomy union was tried and reverted: multi-class
            # plants' `.first()` klass is arbitrary, pulling whole-plant
            # CAMPD nets of mixed coal/gas plants into the sum, +9..+15
            # TWh/yr of cross-contamination.)
            # Slice-keyed since the multi-class split: a mixed coal/gas
            # plant contributes ONLY its coal slices here (the whole-plant
            # `.first()`-klass cross-contamination the note above describes
            # is exactly what the split removes), and the basis stays
            # consistent across a registration's years because all parts are
            # re-rendered atomically.
            _e930d["coal_cems"] = round(
                sum(
                    float(cn.sum())
                    for key, cn in cn_s.items()
                    if str(grp_b.get(key, "")).startswith("COAL")
                )
                / 1e6,
                3,
            )
            # CEMS-anchored fossil actual (EIA930_NG_CELL_CORRUPT ISOs only —
            # owner-signed rework 2026-07-12, FINDING-caiso-c2c4-bench-basis-
            # 930ng-2026-07-12.md §5). Three fields, same bplants coverage
            # basis as ``coal_cems`` (the render is the sole writer):
            #   gas_cems_grid  — CEMS bench-gas net (CAMPD hourly-integrated,
            #                    parasitic-scaled) minus the measured BTM CHP
            #                    host supply → grid-delivered CEMS gas block.
            #   gas_cogen_grid — the 923 non-CEMS gas-class block (plants with
            #                    no usable CAMPD series), grid-delivered; a
            #                    preliminary-923 vintage carries the latest
            #                    complete vintage's block (the prelim survey
            #                    under-counts exactly these cogens).
            #   fossil_cems_grid — gas anchor + the 923 coal grid block: the
            #                    combined-family reconcile cap.
            _iso_anchor = str(meta.get("iso", "ERCOT"))
            fossil_cems_full_anchor: float | None = None  # C5a full-plant cap
            if _iso_anchor in EIA930_NG_CELL_CORRUPT:
                _gas_grps = set(_GAS_GROUPS)
                # A dispatch plant with NO usable CAMPD series (nodata) is not
                # CEMS-covered: it contributes nothing to the CEMS block and
                # its EIA-923 mass falls to the cogen block below instead.
                _cems_ids = {
                    bm.plant_code_of_key(c)
                    for c, p in bplants.items()
                    if not p["nodata"]
                }
                _gas_cems_full = sum(
                    float(p["c_ann"])
                    for p in bplants.values()
                    if p["group"] in _gas_grps and not p["nodata"]
                )
                _gas_cems_grid = _gas_cems_full - sum(
                    float(p["btm"])
                    for p in bplants.values()
                    if p["group"] in _gas_grps and not p["nodata"]
                )
                _nc = e923[
                    e923["klass"].isin(_gas_grps)
                    & ~e923["plant_id"].astype(int).isin(_cems_ids)
                ]
                _cogen_full = float(_nc["annual_mwh"].sum()) / 1e6
                _cogen = sum(
                    float(r["annual_mwh"])
                    / 1e6
                    * (
                        1.0
                        - _btm_share(
                            int(r["plant_id"]),
                            str(r["klass"]),
                            _iso_anchor,
                            measured=_btm_measured,
                        )
                    )
                    for _, r in _nc.iterrows()
                )
                if _eia923_gas_family_incomplete(_iso_anchor, int(year)):
                    _complete = [y for y in sorted(gas_cogen_by_year) if y < int(year)]
                    if _complete:
                        _cogen, _cogen_full = gas_cogen_by_year[_complete[-1]]
                else:
                    gas_cogen_by_year[int(year)] = (_cogen, _cogen_full)
                _coal_grid = sum(
                    float(e923_cls.get(c, 0.0)) / 1e6 - float(btm_cls_bench.get(c, 0.0))
                    for c in _COAL_GROUPS
                    if c in e923_cls.index
                )
                _coal_full = sum(
                    float(e923_cls.get(c, 0.0)) / 1e6
                    for c in _COAL_GROUPS
                    if c in e923_cls.index
                )
                _e930d["gas_cems_grid"] = round(_gas_cems_grid, 3)
                _e930d["gas_cogen_grid"] = round(_cogen, 3)
                _e930d["fossil_cems_grid"] = round(
                    _gas_cems_grid + _cogen + _coal_grid, 3
                )
                fossil_cems_full_anchor = _gas_cems_full + _cogen_full + _coal_full
            bench[int(year)] = {
                "plants": bplants,
                "e930": _e930d,
                # Grid-delivered actual: the BTM subtrahend is the BENCH basis
                # (measured shares where the measured artifact exists,
                # flag-independent — nyiso-149), never the registering run's
                # own hold-out, so the shared part is stable across runs.
                "classFull": {
                    str(g): round(
                        float(v) / 1e6 - float(btm_cls_bench.get(str(g), 0.0)), 4
                    )
                    for g, v in e923_cls.items()
                },
            }
            # Bench provenance: the CT-only CEMS reporters scored on EIA-923
            # (kept out of the payload when none, so unaffected bundles diff
            # clean).
            if ct_only_rows:
                bench[int(year)]["ctOnly"] = ct_only_rows
            # Grid-delivered actual for the variable renewables (2026-06-25 user
            # directive). EIA-923 'classFull' counts every plant >= 1 MW including
            # the distribution-connected / net-metered behind-the-meter PV that
            # ISO-NE / CAISO / PJM / NYISO / MISO net into LOAD and that never
            # reaches the wholesale grid (e.g. NEISO solar 3.70 EIA-923 vs 0.89
            # EIA-930-grid; CAISO +4.7, PJM +5.3, MISO +2.8, NYISO +2.1 TWh of
            # BTM PV). The model dispatches only grid solar/wind, so for an
            # apples-to-apples per-class actual AND total the variable renewables
            # use the authoritative EIA-930 grid series instead of full EIA-923 --
            # the SAME source-authority `results.calibration.actuals_source`
            # already applies to the solar/wind fuel-mix gate. Nuclear is left on
            # EIA-923 (no BTM nuclear; EIA-930 under-reports it for some BAs, e.g.
            # NYIS), matching actuals_source (nuclear -> eia923). This is the single
            # BTM-removal point; downstream system totals then count each class
            # exactly once (no separate EIA-930 add-on -- see calibration_verdict
            # ._gen_totals and the run explorer's totalGen).
            #
            # ISO override (NYISO solar). NYISO grid solar is structurally 0 in
            # EIA-930 — NYISO solar is overwhelmingly behind-the-meter / net-metered
            # and invisible to the NYIS balancing-area telemetry — so the default
            # EIA-930 routing would score the model's ~2 TWh of dispatched grid
            # solar against a spurious zero. For NYISO, `actuals_source("solar",
            # iso)` returns EIA-923 (the ~2 TWh of utility-scale grid solar the
            # model actually dispatches), so classFull KEEPS its EIA-923 value and
            # that value is MIRRORED into the e930 slot, because the dashboard's
            # nonFosErr reads the variable-renewable actual from bench.e930 (the
            # bench part itself must carry the right number).
            _iso_key = str(meta.get("iso", "ERCOT"))
            _cf = bench[int(year)]["classFull"]
            for _vre in ("wind", "solar"):  # variable renewables
                if actuals_source(_vre, _iso_key) == EIA930_SOURCE:
                    if _vre in _cf and _vre in _e930d:
                        _cf[_vre] = round(float(_e930d[_vre]), 4)
                elif _vre in _cf:
                    # EIA-923 is authoritative here (NYISO solar): keep classFull on
                    # the utility-scale 923 total and mirror it into e930 so the
                    # dashboard scores the variable-renewable row against it, not 0.
                    _e930d[_vre] = round(float(_cf[_vre]), 4)
            # Repair a preliminary EIA-923 vintage: when a fossil fuel's class
            # total is materially below the complete EIA-930 grid series (the
            # same authority the model's gas/coal are calibrated to), scale that
            # fuel's classes up to the EIA-930 total so the fossil volume error
            # compares the model against a COMPLETE benchmark, not a partial
            # survey. Without this the 2025 NEISO benchmark under-counted CC by
            # ~4 TWh, inflating the system volume error to +7% though the model
            # matches EIA-930 within 1%. Complete vintages (>= frac) are
            # untouched; the inter-class split and monthly shape are preserved.
            # For fold-in BAs (CAISO) the gas target is deflated by the EIA-930
            # geothermal+biomass fold-in first, so gas doesn't scale to the
            # inflated NG cell (see reconcile_vintage_classes / [1] note).
            reconcile_vintage_classes(
                bench[int(year)]["classFull"],
                bench[int(year)]["e930"],
                str(meta.get("iso", "ERCOT")),
            )
            # Actual historical avg LMP ($/MWh), system hub-average, for the
            # summary page's model-vs-actual price comparison. Absent for an
            # ISO-year with no price file -> the card shows model only.
            actual_lmp = _actual_avg_lmp(meta.get("iso", "ERCOT"), year)
            if actual_lmp:
                bench[int(year)]["avgLMP"] = actual_lmp

            # Observed storage discharge throughput (TWh), the cycling-realism
            # diagnostic actual (ex-C5b — a run-page diagnostic since rubric
            # v2.7): the positive half of the EIA-930 battery + pumped-storage
            # net-gen series. None when the BA doesn't report a storage
            # breakout or coverage is below the threshold, so consumers can
            # distinguish "no EIA-930 data" from "data says zero".
            actual_storage = _actual_storage_twh(e930)
            actual_storage_monthly = _actual_storage_monthly(e930)
            bench[int(year)]["storage"] = {
                "throughput_twh": actual_storage,
                "monthly_net_gwh": actual_storage_monthly,
            }

            # Actual fossil CO2 (Mt), the calibration-page emissions metric.
            # Each fossil plant's CO2 rate (kg / net MWh) comes from eGRID — the
            # only source spanning the small non-CEMS units — overridden by the
            # CAMPD-measured intensity where it exists; the rates are net-gen-
            # weighted within each class to a tonnes/MWh intensity.
            # FULL-PLANT (CHP-inclusive) basis on both sides (rubric v2.3,
            # owner directive 2026-07-09): eGRID/CAMPD rates are defined over
            # each cogen's FULL net generation (host self-supply + grid), so
            # the intensity is applied to the full EIA-923 class totals — NOT
            # the BTM-stripped ``classFull`` the generation-mix gate uses —
            # and the model side adds the same measured BTM host supply back
            # (see the model payload below). Atmospheric CO2 doesn't stop at
            # the meter: the system-CO2 number policy consumes must count the
            # cogen fleet's whole burn, matching what eGRID reports.
            e_fossil = e923[e923["klass"].isin(FOSSIL_GROUPS)]
            co2_rate = egrid.fossil_co2_rate_map(int(year))
            co2_intensity = egrid.class_co2_intensity(
                e_fossil,
                co2_rate,
                plant_col="plant_id",
                klass_col="klass",
                gen_col="annual_mwh",
            )
            # Full EIA-923 class totals (TWh) BEFORE the BTM subtraction —
            # the CHP-inclusive basis the eGRID rates were measured on.
            class_full_923 = {
                str(g): round(float(v) / 1e6, 4) for g, v in e923_cls.items()
            }
            # CEMS-anchor complete-coverage repair (C5a): a preliminary-923
            # vintage under-counts fossil generation, so the CO2 actual built
            # from it is vintage-understated (the caiso-76 FINDING §4 defect —
            # 2025 CO2-implied CC 37.5 TWh vs a ~54 TWh family gate). For a
            # corrupted-NG-cell ISO the measured full-plant total exists (CEMS
            # bench gas + carried cogen block + coal); scale the fossil classes
            # to it — the same uniform level-repair the classFull reconcile
            # applies, on the full-plant basis — before the intensity multiply.
            # Complete vintages: anchor ≈ booked total → inside the same ±3%
            # deadband, untouched (owner-signed rework 2026-07-12).
            if fossil_cems_full_anchor is not None and _eia923_gas_family_incomplete(
                _iso_anchor, int(year)
            ):
                _fclasses = [
                    g for g in class_full_923 if g in (*_GAS_GROUPS, *_COAL_GROUPS)
                ]
                _cur_full = sum(class_full_923[g] for g in _fclasses)
                if _cur_full > 0.0 and not (
                    _VINTAGE_RECONCILE_FRAC * fossil_cems_full_anchor
                    <= _cur_full
                    <= fossil_cems_full_anchor / _VINTAGE_RECONCILE_FRAC
                ):
                    _sc = fossil_cems_full_anchor / _cur_full
                    for g in _fclasses:
                        class_full_923[g] = round(class_full_923[g] * _sc, 4)
            actual_co2_mt, actual_co2_by = _fossil_co2(class_full_923, co2_intensity)
            # Share of fossil-class EIA-923 generation carrying a plant rate —
            # the class intensity is extrapolated to the small remainder.
            _frate = e_fossil.assign(
                rate=e_fossil["plant_id"].astype(int).map(co2_rate)
            )
            _gcov = float(_frate.loc[_frate["rate"].notna(), "annual_mwh"].sum())
            _gall = float(_frate["annual_mwh"].sum())
            # Key the scalar actual "egrid" — the name calibration_verdict's
            # C5a gate (score_co2) reads — so committing this benchmark part
            # activates the CO2 verdict that has been SKIPPED for want of an
            # actual. ("eGRID" names the fleet-wide base; CAMPD overrides the
            # large plants.) byClass / intensity / covPct drive the panel.
            # ``btmClass`` records the per-class measured BTM CHP host supply
            # (TWh) added back on the model side, and ``basis`` marks the
            # payload as full-plant so the scorer/retrofit can tell a v2.3
            # part from a legacy grid-basis one.
            bench[int(year)]["co2"] = {
                "egrid": actual_co2_mt,
                "byClass": actual_co2_by,
                "intensity": {k: round(v, 5) for k, v in co2_intensity.items()},
                "covPct": round(100.0 * _gcov / _gall, 1) if _gall > 0 else 0.0,
                # Bench basis (nyiso-149): the shared part carries the
                # measured BTM, not the registering run's hold-out, so its
                # bytes cannot flip with the run's flag. (C5a is reported-only
                # since rubric v2.9.)
                "btmClass": {
                    str(k): round(float(v), 4)
                    for k, v in sorted(btm_cls_bench.items())
                    if float(v) > 0.0
                },
                "basis": "full-plant",
            }

            # ---- model payload (per run) ----
            # Slice-keyed like the bench: one entry per (plant, class), so a
            # multi-class plant's every class keeps its model dispatch (the
            # old plant-keyed dict silently dropped all but the last class)
            # and pairs with ITS OWN measured slice.
            mplants: dict[str, dict] = {}
            for key, mw in mw_p.items():
                code = code_p[key]
                cap = float(npl_s.get(key, npl.get(code, 0.0))) or 1.0
                grp = grp_p.get(key, "")
                _e13 = e923_slices.get(code, {}).get(grp, np.zeros(13))
                # CHP add-back (report only, NOT in the LP): the host
                # behind-the-meter self-supply was held out of the grid solve,
                # but CAMPD measures the full plant. Add it back flat so the
                # plant heatmap and the plant/class r / NRMSE / capture compare
                # the full plant to the full CAMPD plant. A flat add is
                # correlation-invariant (it corrects the level, not the shape).
                if grp in ("CC_CHP", "CT_CHP", "ST_CHP"):
                    btm_mwh = float(_e13[0]) * _btm_share(
                        code,
                        grp,
                        meta.get("iso", "ERCOT"),
                        measured=_btm_run_measured,
                    )
                    if btm_mwh > 0.0:
                        mw = mw + btm_mwh / float(_T)
                cn = cn_s.get(key)
                r = nr = None
                cap_pct = None
                _bp = bench[int(year)]["plants"].get(key)
                if _bp is not None and _bp.get("ct_only"):
                    # CT-only CEMS reporter: the CAMPD series is incomplete, so
                    # score this plant on its EIA-923 monthly row instead
                    # (diagnosis §3a). The per-plant Δ table is already 923-based.
                    r, nr, cap_pct = _capture_on_923(
                        mw,
                        _e13[1:] / 1e3,
                        float(mw.sum()) / 1e6,
                        float(_e13[0]) / 1e6,
                    )
                elif cn is not None and cn.sum() > 0 and mw.std() > 0:
                    r = round(_pearson(mw, cn), 3)
                    nr = round(_nrmse(mw, cn), 3)
                    dev = (mw.sum() - cn.sum()) / cn.sum()
                    cap_pct = _capture(r, nr, dev)
                mplants[key] = {
                    "m": _b64(100.0 * mw / cap),
                    "m_ann": round(float(mw.sum()) / 1e6, 4),
                    "m_mon": _monthly_gwh(mw),
                    "r": r,
                    "nrmse": nr,
                    "cap": cap_pct,
                }
                if _bp is not None and _bp.get("ct_only"):
                    mplants[key]["b923"] = True
                if code in tr_bands:
                    mplants[key]["tr"] = tr_bands[code]
            # Non-fossil model annual (nuclear / wind / solar) for fuel table.
            nf = {}
            for f in ("nuclear", "wind", "solar"):
                s = disp[disp["klass"] == f]
                nf[f] = round(float(s["mw"].sum()) / 1e6, 3)
            # System fuel-vs-EIA-930 table (all zones; 930 is not zonal).
            mh = rcf._class_hourly(disp)
            e = {
                s: e930[e930["series"] == s].sort_values("hour")["mw"].to_numpy(float)
                for s in e930["series"].unique()
            }
            fuel_rows = []
            # Each EIA-930 fuel row sums the model classes that roll up to it
            # (market_sim.config.plant_taxonomy) — so any class is counted once,
            # in the right bucket, with no hardcoded membership list.
            specs = [
                (fuel, classes_for_fuel930(fuel), e.get(fuel), fuel == "gas")
                for fuel in ("gas", "coal", "nuclear", "wind", "solar")
            ]
            cfull = bench[int(year)]["classFull"]
            for fuel, classes, ob, is_gas in specs:
                # Grid-delivered model vs the RAW EIA-930 grid series, for every
                # fuel (user directive 2026-07-02): the model sum includes EVERY
                # class of the fuel — the CHP classes' grid dispatch too, since
                # EIA-930 meters CHP grid exports while the behind-the-meter host
                # supply is held out of the LP on the model side and invisible to
                # the BA meter on the actual side. (The old gas row dropped the
                # CHP classes from the model and releveled the "930" benchmark to
                # the EIA-923 classFull basis — a 923 subtotal mislabeled 930 that
                # double-showed the CC_REGULAR/CC_CHP classification split already
                # scored per class by C1.)
                ms = sum((mh.get(c, np.zeros(_T)) for c in classes), np.zeros(_T))
                if (
                    is_gas
                    and _iso_anchor in EIA930_NG_CELL_CORRUPT
                    and int(year) >= EIA930_NG_CORRUPT_ONSET.get(_iso_anchor, 9999)
                    and "gas_cogen_grid" in _e930d
                ):
                    # Corrupted-NG-cell BA, on/after the corruption onset
                    # vintage: the gas hourly actual is the MEASURED series —
                    # CEMS bench-gas hourly (grid-delivered: flat BTM CHP host
                    # supply removed) plus the flat non-CEMS cogen block — not
                    # the 930 NG cell (FINDING-caiso-c2c4-bench-basis-930ng-
                    # 2026-07-12.md §5.2; flat adjustments preserve pearson r).
                    # Pre-onset years keep 930. The CAISO onset moved 2024 ->
                    # 2023 (owner ruling 2026-07-26, caiso-121) once the
                    # "pre-onset years agree" premise was tested and failed for
                    # 2023 — benchmark_semantics.EIA930_NG_CORRUPT_ONSET.
                    _btm_gas_flat = (
                        sum(
                            float(p["btm"])
                            for p in bplants.values()
                            if p["group"] in set(classes) and not p["nodata"]
                        )
                        * 1e6
                        / _T
                    )
                    ob = (
                        sum(
                            (
                                cn_s[c]
                                for c, p in bplants.items()
                                if p["group"] in set(classes)
                                and not p["nodata"]
                                and c in cn_s
                            ),
                            np.zeros(_T),
                        )
                        - _btm_gas_flat
                        + float(_e930d["gas_cogen_grid"]) * 1e6 / _T
                    )
                elif is_gas and ob is not None and "other" in e:
                    # Gas fold-in correction, identical to the C2 verdict
                    # (calibration_verdict.score_sysvol): some BAs (MISO) fold
                    # biomass/process gas into the EIA-930 NG series while the
                    # model books them in its own biomass/OTHER rows; subtract
                    # that excess as a flat baseload (biomass/process gas run
                    # ~flat, so pearson r is preserved).
                    fold = max(
                        0.0,
                        float(cfull.get("OTHER", 0.0))
                        + float(cfull.get("biomass", 0.0))
                        - float(e["other"].sum()) / 1e6,
                    )
                    ob = ob - fold * 1e6 / _T
                m_twh = float(ms.sum()) / 1e6
                b_twh = float(ob.sum()) / 1e6 if ob is not None else None
                r2 = (
                    round(_pearson(ms, ob), 3)
                    if ob is not None and ob.std() > 0
                    else None
                )
                n2 = round(_nrmse(ms, ob), 3) if ob is not None else None
                fuel_rows.append(
                    {
                        "fuel": fuel,
                        "m": round(m_twh, 2),
                        "b": round(b_twh, 2) if b_twh is not None else None,
                        "r": r2,
                        "nrmse": n2,
                    }
                )
            # Net interchange (net-export positive, the EIA-930 sign
            # convention): model = -(priced import/export node dispatch:
            # import tranches positive, export sinks negative), actual = the
            # EIA-930 region "interchange" series. Only present when the
            # bundle solved with --priced-interchange (klass "import" rows
            # exist); a measured-schedule bundle nets interchange into demand,
            # so a row would compare actual to itself. Informational — it
            # makes the import/export node's error visible instead of letting
            # fuels silently shift to cover it.
            imp = disp[disp["klass"] == "import"]
            ob_ix = e.get("interchange")
            if not imp.empty and ob_ix is not None:
                ms_ix = -(
                    imp.groupby("hour")["mw"]
                    .sum()
                    .reindex(range(_T), fill_value=0.0)
                    .to_numpy(float)
                )
                fuel_rows.append(
                    {
                        "fuel": "interchange",
                        "m": round(float(ms_ix.sum()) / 1e6, 2),
                        "b": round(float(ob_ix.sum()) / 1e6, 2),
                        "r": (
                            round(_pearson(ms_ix, ob_ix), 3)
                            if ob_ix.std() > 0
                            else None
                        ),
                        "nrmse": round(_nrmse(ms_ix, ob_ix), 3),
                    }
                )
            # Per-zone average LMP (load-weighted) from the system duals, for
            # the dashboard's average-LMP KPI. Primary pass (P2 when the bundle
            # ran commitment, else P1); the shell averages over
            # the selected zones, weighting by demand. ``pMon``/``dMon`` carry
            # the same load-weighted price + demand-weight per month (Jan-Dec)
            # so the summary page can build a model-vs-actual monthly LMP table;
            # the shell re-weights pMon across the selected zones by dMon.
            sy = _primary_pass(sys_all[sys_all["year"] == year])
            # Post-solve scarcity overlay (any ISO with a derived sidecar;
            # display + C3c settlement-price scoring): the SECOND LMP series
            # shown next to the energy-only duals. The energy-only ``lmp`` block
            # below stays byte-identical and is the series every VOLUME gate
            # uses; ``lmpScar`` is purely additive (the published system-wide
            # reserve/scarcity adder added uniformly to each zone — ERCOT ORDC,
            # PJM two-step, NYISO/NEISO RCPF, CAISO LOLP). G-20a (2026-07-07,
            # owner-approved) removed the old ``iso == "ERCOT"`` gate here so the
            # settlement tail scores for every ISO whose derive_*_overlay.py
            # wrote a scarcity.parquet into the bundle.
            hours = int(meta.get("hours", _T))
            scar = _load_scarcity_overlay(bdir, int(year), hours)
            lmp = {}
            lmp_scar: dict[str, dict] = {}
            # Per-zone hourly model price (hour-indexed, NaN-padded to ``hours``)
            # for the C3c scarcity-tail count. The model dual under-shoots
            # scarcity by construction (energy-only LP), so this tail can collapse
            # — that is the intended, truthful signal, not a thing to tune.
            model_price_by_zone: dict[str, np.ndarray] = {}
            # Per-zone hourly demand (0-padded), the load weights for the
            # ISO-wide hourly price the delta heatmap compares against actuals.
            model_demand_by_zone: dict[str, np.ndarray] = {}
            for zone, zg in sy.groupby("zone", observed=True):
                price = zg["price"].to_numpy(float)
                dem = zg["demand"].to_numpy(float)
                hr = zg["hour"].to_numpy()
                full = np.full(hours, np.nan)
                full[hr] = price
                model_price_by_zone[str(zone)] = full
                full_d = np.zeros(hours)
                full_d[hr] = dem
                model_demand_by_zone[str(zone)] = full_d
                d_tot = float(dem.sum())
                p = (
                    float((price * dem).sum()) / d_tot
                    if d_tot > 0
                    else float(price.mean())
                )
                # hour 0-8759 -> month 0-11 via the cumulative month-hour edges.
                midx = np.clip(np.searchsorted(_CUM, hr, side="right") - 1, 0, 11)
                p_mon: list = [None] * 12
                d_mon = [0.0] * 12
                # Overlaid price for this zone = energy-only price + the
                # system-wide adder (uniform across zones); demand-weighted per
                # month exactly like p_mon so the shell re-weights it across the
                # selected zones with the SAME dMon weights.
                op = price + scar["adder"][hr] if scar is not None else None
                p_mon_scar: list = [None] * 12
                for m in range(12):
                    sel = midx == m
                    if not sel.any():
                        continue
                    dd = float(dem[sel].sum())
                    p_mon[m] = (
                        round(float((price[sel] * dem[sel]).sum()) / dd, 2)
                        if dd > 0
                        else round(float(price[sel].mean()), 2)
                    )
                    d_mon[m] = round(dd / 1e6, 4)
                    if op is not None:
                        p_mon_scar[m] = (
                            round(float((op[sel] * dem[sel]).sum()) / dd, 2)
                            if dd > 0
                            else round(float(op[sel].mean()), 2)
                        )
                lmp[str(zone)] = {
                    "p": round(p, 2),
                    "d": round(d_tot / 1e6, 4),
                    "pMon": p_mon,
                    "dMon": d_mon,
                }
                if scar is not None:
                    lmp_scar[str(zone)] = {"pMonScar": p_mon_scar}
            # System-wide generation mix per fossil class (TWh), GRID-DELIVERED:
            # model = grid LP only (``_class_hourly`` sum, NO behind-the-meter
            # add-back), compared against ``bench.classFull`` which is now
            # EIA-923 minus the per-class BTM host supply — so the mix table and
            # the scorecard judge what the model dispatched to the grid against
            # what actually reached the grid (user directive 2026-06-14). The
            # per-plant heatmaps keep the whole-plant add-back (they compare to
            # CEMS, which is whole-plant); only these class/system totals are
            # grid-delivered.
            gm_model = {
                g: round(float(mh.get(g, np.zeros(_T)).sum()) / 1e6, 4)
                # sorted: set iteration order is hash-randomized per process,
                # and the payload must be byte-stable across re-renders (an
                # unchanged run must not show up as a git diff).
                for g in sorted(set(MIX_GROUPS) | set(mh))
            }
            # Model fossil CO2 (Mt): the model's class totals times the SAME
            # per-class CO2 intensity the benchmark used. FULL-PLANT basis
            # (rubric v2.3): the measured BTM CHP host supply (btm_cls — the
            # exact hold-out the LP never dispatched, a pure function of
            # committed inputs) is added back onto the grid totals first,
            # mirroring the benchmark side, because the eGRID/CAMPD rates are
            # measured over each cogen's full net generation. The comparison
            # is therefore the model's generation mix re-weighted by measured
            # carbon intensity — an independent check on the coal/gas split
            # that a pure MWh volume gate is blind to.
            gm_model_full = {
                g: round(float(gm_model.get(g, 0.0)) + float(btm_cls.get(g, 0.0)), 4)
                for g in sorted(set(gm_model) | {str(k) for k in btm_cls})
            }
            model_co2_mt, model_co2_by = _fossil_co2(
                gm_model_full, bench[int(year)]["co2"]["intensity"]
            )
            # ---- signed volume error per (class, zone, month) ----
            # Model monthly TWh vs the authoritative actuals source for each
            # class (EIA-923 for every class except solar -> EIA-930; the rule
            # lives in calibration.actuals_source, not here or in JS). Built
            # from the matched fossil plants so it decomposes by zone and month
            # -- the dashboard heatmap re-aggregates these to whatever axis it
            # shows. GRID-DELIVERED on BOTH sides (user directive), matching the
            # class/system mix scorecard (gm_model vs classFull): the model uses
            # the grid LP series (``mw_p``, NO behind-the-meter CHP add-back) and
            # the EIA-923 actual has each plant's behind-the-meter CHP host
            # self-supply removed (``_btm_share`` is 0 for non-CHP classes, so
            # only CHP plants change). This diverges deliberately from the
            # per-plant Δ-vs-923 table, which stays whole-plant to compare
            # against whole-plant CEMS. Solar carries only a system annual
            # because EIA-930 is neither zonal nor monthly here.
            _iso = meta.get("iso", "ERCOT")
            vol_err: dict[str, dict] = {}
            for key in mw_p:
                code = code_p[key]
                grp = grp_p.get(key)
                zone = zone_p.get(code)
                if grp is None or zone is None:
                    continue
                cell = vol_err.setdefault(
                    grp,
                    {"src": actuals_source(grp, meta.get("iso")), "zoneMon": {}},
                )
                zc = cell["zoneMon"].setdefault(
                    zone, {"m": [0.0] * 12, "a": [0.0] * 12}
                )
                # Grid-delivered: model from the grid LP (mw_p, no add-back),
                # actual from the plant's own-class EIA-923 slice minus its
                # BTM host supply (a single-class plant's slice is its whole
                # plant, unchanged; a multi-class plant's actual lands in the
                # measured class instead of the collapsed one).
                m_mon = _monthly_gwh(mw_p[key])  # grid-LP model GWh
                # Actual side: the MEASURED share whenever the artifact exists,
                # the bench-side convention (nyiso-149) — a physical fact,
                # independent of the registering run's flag.
                _grid_frac = 1.0 - _btm_share(code, grp, _iso, measured=_btm_measured)
                a_mon = (
                    e923_slices.get(code, {}).get(grp, np.zeros(13))[1:] / 1e3
                )  # EIA-923 GWh
                for mo in range(12):
                    zc["m"][mo] += float(m_mon[mo]) / 1e3  # GWh -> TWh
                    zc["a"][mo] += float(a_mon[mo]) * _grid_frac / 1e3
            for cell in vol_err.values():
                for zc in cell["zoneMon"].values():
                    zc["m"] = [round(x, 4) for x in zc["m"]]
                    zc["a"] = [round(x, 4) for x in zc["a"]]
                    zc["e"] = [_vol_err(m, a) for m, a in zip(zc["m"], zc["a"])]
            # Variable renewables: EIA-930 system annual baseline (no zone/month
            # breakdown — 930 is neither zonal nor split into model classes
            # here). Both solar and wind route to EIA-930 via actuals_source
            # (the BA-level 923 net-gen survey under-counts CISO wind and
            # collapses in the incomplete 2025 release for every ISO).
            for _vr in ("solar", "wind"):
                vr_m = float(nf.get(_vr, 0.0))
                vr_a = float(bench[int(year)]["e930"].get(_vr, 0.0))
                if vr_a > 0.0 or vr_m > 0.0:
                    vol_err[_vr] = {
                        "src": actuals_source(_vr, meta.get("iso")),
                        "sys": {
                            "m": round(vr_m, 4),
                            "a": round(vr_a, 4),
                            "e": _vol_err(vr_m, vr_a),
                        },
                    }
            run_years[int(year)] = {
                "plants": mplants,
                "nonfossil": nf,
                "fuelRows": fuel_rows,
                "gmModel": gm_model,
                "lmp": lmp,
                "volErr": vol_err,
                # Scalar keyed "model" for calibration_verdict's C5a gate;
                # "basis" marks the v2.3 full-plant (BTM-added-back) payload.
                "co2": {
                    "model": model_co2_mt,
                    "byClass": model_co2_by,
                    "basis": "full-plant",
                },
            }
            # ---- Non-fossil + interchange hourly panels (Charts-tab maps) ----
            # POPULATE-ON-NEXT-RENDER, exactly like ``lmpDeltaHr`` below: only
            # runs rendered after this field was added carry it, and the Charts
            # tab lists the non-fossil classes off the payload's own keys, so
            # every already-registered run stays valid and simply shows the
            # fossil panels. ``mh`` (model hourly by class) and ``e`` (the EIA-930
            # hourly series) are both already materialized above for the fuel
            # table — this keeps them instead of collapsing them to annual
            # scalars, which is why the field costs no new data read.
            nfhr = build_nonfossil_hourly(mh, e, hours=_T)
            if nfhr:
                run_years[int(year)]["nonfossilHr"] = nfhr
            _assert_nonfossil_hourly_reconciles(
                nfhr, mh, fuel_rows, iso=meta.get("iso", "?"), year=int(year)
            )
            # Model storage discharge throughput (TWh) for the run-page
            # storage diagnostic (ex-C5b, removed from the rubric v2.7) —
            # li-ion + pumped storage from this run's storage.parquet P1
            # frame. Always set: 0.0 when no storage fleet, so consumers can
            # distinguish "model has no storage" from "model has storage but
            # data is missing".
            model_storage = _model_storage_twh(storage_all, year)
            model_storage_monthly = _model_storage_monthly(storage_all, year)
            run_years[int(year)]["storage"] = {
                "throughput_twh": model_storage if model_storage is not None else 0.0,
                "monthly_net_gwh": model_storage_monthly,
            }
            # ---- ISO-wide hourly LMP delta (model - actual RT) ----
            # Feeds the Report-tab delta heatmap: where the model runs HOT
            # (model price > actual, orange) or COLD (model < actual, blue) for
            # each of the 8760 hours. Model system price = load-weighted mean of
            # the per-zone energy-only duals (the SAME series the avg-LMP KPI and
            # the settlement tail use); actual = _actual_rt_padded (RT only, no
            # DA fallback) — the ISO-wide real-time reference, since the model's
            # clearing price is a real-time marginal-energy analogue (no
            # day-ahead unit-commitment smoothing). Hours with no model dual or
            # no actual price stay NaN (neutral). Serialized as signed int16
            # (_b64_i16). POPULATE-ON-NEXT-RENDER: only runs rendered after this
            # field was added carry it; the dashboard omits the panel otherwise.
            _iso_dz = meta.get("iso", "ERCOT")
            if model_price_by_zone:
                zorder = list(model_price_by_zone)
                pz = np.vstack([model_price_by_zone[z] for z in zorder])
                dz = np.vstack([model_demand_by_zone[z] for z in zorder])
                wsum = np.nansum(dz, axis=0)
                with np.errstate(invalid="ignore", divide="ignore"):
                    mp_iso = (
                        np.nansum(np.where(np.isfinite(pz), pz * dz, 0.0), axis=0)
                        / wsum
                    )
                mp_iso[wsum <= 0] = np.nan
                rt_iso = _actual_rt_padded(_iso_dz, int(year), hours)
                if rt_iso is not None:
                    run_years[int(year)]["lmpDeltaHr"] = _b64_i16(mp_iso - rt_iso)
            # Year-level scarcity-overlay summary: demand-weighted monthly LMP
            # MAE vs actual RT for the energy-only and settlement (overlaid)
            # series, and tail-hour counts, for ANY ISO whose derive_*_overlay.py
            # wrote a scarcity.parquet into the bundle (ERCOT ORDC, PJM two-step,
            # NYISO/NEISO RCPF, CAISO LOLP). ``lam`` is the energy-only system
            # lambda and ``lam_s = lam + adder`` the settlement price; the
            # ``hoursGt200.overlay`` count is what C3c scores (G-20a) — the
            # ``.model`` count (energy-only) stays emitted for diagnostics. The
            # per-ISO threshold (rubric §5: $200, NYISO/NEISO $300) is applied to
            # the primary tail; the >$500 companion stays fixed. ``_actual_rt_padded``
            # is the ISO-agnostic RT reader (replaces the ERCOT-only ordc._actual_rt,
            # whose CAL_DIR points at the pre-W1 inputs/ tree); _demand_weights /
            # _monthly_mae are reused from the deriver unchanged (bundle-relative).
            iso = meta.get("iso")
            thr = TAIL_THRESHOLD.get(iso, 200.0)
            if scar is not None and lmp_scar:
                rt = _actual_rt_padded(iso, int(year), hours)
                w = ordc._demand_weights(bdir, int(year), hours)
                lam, lam_s = scar["lmp"], scar["lmp_scarcity"]
                run_years[int(year)]["lmpScar"] = lmp_scar
                run_years[int(year)]["ordc"] = {
                    "maeEnergyOnly": (
                        round(ordc._monthly_mae(lam, rt, w), 1)
                        if rt is not None
                        else None
                    ),
                    "maeOverlay": (
                        round(ordc._monthly_mae(lam_s, rt, w), 1)
                        if rt is not None
                        else None
                    ),
                    "hoursGt200": {
                        "actual": _gt_count(rt, thr),
                        "model": _gt_count(lam, thr),
                        "overlay": _gt_count(lam_s, thr),
                    },
                    "hoursGt500": {
                        "actual": _gt_count(rt, 500),
                        "model": _gt_count(lam, 500),
                        "overlay": _gt_count(lam_s, 500),
                    },
                    "series": scar["series"],
                    "reldeployMw": scar["reldeploy"],
                }
            # Scarcity tail (C3c) fallback — no overlay sidecar: count hours where
            # the max zonal LMP exceeds the ISO's threshold, for the model duals
            # and the actual hub series, stored under the legacy key "hoursGt200"
            # the scorer reads regardless of threshold. Emitted only when the
            # overlay block above did not fire (a bundle with no derived
            # scarcity.parquet — e.g. a co-opt run). No ``overlay`` key here, so
            # C3c scores the energy-only ``model`` for these runs. The energy-only
            # LP may under-shoot the actual scarcity tail — that is the truthful,
            # expected signal, not a thing to tune.
            if "ordc" not in run_years[int(year)]:
                thr = TAIL_THRESHOLD.get(iso, 200.0)
                actual_hourly = _actual_lmp_hourly(iso, int(year))
                if actual_hourly is not None and model_price_by_zone:
                    run_years[int(year)]["ordc"] = {
                        "hoursGt200": {
                            "model": _tail_hours(model_price_by_zone, thr),
                            "actual": _tail_hours({"hub": actual_hourly}, thr),
                        }
                    }
        model_runs.append({"label": label, "years": run_years})

    # Only the fossil classes actually present in this ISO's dispatch, in the
    # canonical order — so the class selector and its default land on a
    # populated class (PJM has no COAL_LIGNITE, so it must not default there and
    # render an empty view). ERCOT keeps all classes (all present).
    # Fossil classes actually present in this ISO's model or benchmark, in
    # canonical order first then any extra (auto-wired) classes sorted — so a
    # new classification like the EIA-923 coal ranks shows up for every ISO
    # without being hardcoded here. Non-fossil classes are excluded.
    fossil_present = {g for g in groups_set if g not in _NONFOSSIL_KLASS}
    groups = [g for g in FOSSIL_GROUPS if g in fossil_present] + sorted(
        fossil_present - set(FOSSIL_GROUPS)
    )
    groups = groups or FOSSIL_GROUPS
    return {
        "groups": groups,
        "groupLabel": {g: _group_label(g) for g in groups},
        "zones": sorted(zones_set),
        "years": sorted(years_set),
        "runLabels": labels,
        "bench": bench,
        "model": model_runs,
    }


def main() -> None:
    """Render the multi-run report from one or more bundles."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+", help="[LABEL=]BUNDLE_DIR for each run/config")
    ap.add_argument(
        "--out",
        default=str(REPO / "results" / "calibration" / "calibration-report.html"),
    )
    args = ap.parse_args()
    runs: list[tuple[str, Path]] = []
    for spec in args.bundles:
        if "=" in spec:
            lab, _, d = spec.partition("=")
        else:
            d = spec
            lab = Path(spec).name
        runs.append((lab, Path(d)))
    payload = build_payload(runs)
    # Gzip + base64 the payload (CF series compress ~5x); the browser inflates
    # it with DecompressionStream. Keeps the self-contained file small enough
    # for mobile and version control.
    import gzip

    gz = gzip.compress(json.dumps(payload).encode(), compresslevel=9)
    b64 = base64.b64encode(gz).decode()
    out = Path(args.out)
    out.write_text(
        TEMPLATE.replace("__B64__", b64).replace(
            "__GEN__", datetime.now().strftime("%Y-%m-%d %H:%M")
        )
    )
    n_series = sum(
        len(y["plants"]) for r in payload["model"] for y in r["years"].values()
    )
    print(
        f"wrote {out}  ({out.stat().st_size / 1e6:.1f} MB, "
        f"{len(runs)} runs, {n_series} model series)"
    )


TEMPLATE = r"""PLACEHOLDER_TEMPLATE_BODY"""


if __name__ == "__main__":
    main()
