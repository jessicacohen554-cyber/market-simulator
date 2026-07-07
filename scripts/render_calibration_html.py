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


def _b64(cf: np.ndarray) -> str:
    """Encode a capacity-factor series (0-100) as base64 uint8 of length 8760."""
    a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)
    if a.shape[0] < _T:
        a = np.concatenate([a, np.zeros(_T - a.shape[0], np.uint8)])
    return base64.b64encode(a[:_T].tobytes()).decode()


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
    all, so C5c scores whether the model DISCHARGES in the right months. The
    prior net basis (discharge − charge) is ≤ 0 over any month by round-trip
    losses and could never correlate with a discharge-only actual.
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
    disch = np.clip(present["mw"].to_numpy(float), 0.0, None).sum() / 1e6
    return round(float(disch), 4) if disch > 1e-6 else None


def _actual_storage_monthly(e930_year: pd.DataFrame) -> list[float] | None:
    """Return 12 monthly DISCHARGE GWh from EIA-930 storage series, or None.

    Discharge basis (positive half only), matching C5b's throughput basis —
    and the only basis the actual supports everywhere: several BAs report a
    discharge-only storage series (NEISO ``NG: PS`` — pumping shows up as
    load, never as a negative storage value; ERCOT's ``battery_discharge`` is
    pre-split positive). Summing those series signed silently yields gross
    discharge, while the model side used to report net (discharge − charge,
    ≤ 0 over a month by round-trip losses) — an apples-to-oranges C5c that a
    perfectly-cycling model could never pass. Both sides are now discharge.
    """
    present = e930_year[e930_year["series"].isin(_STORAGE_E930_SERIES)]
    if present.empty:
        return None
    net = np.zeros(_T, dtype=float)
    for _, row in present.iterrows():
        h = int(row["hour"])
        mw = float(row["mw"])
        if 0 <= h < _T and not np.isnan(mw):
            net[h] += max(mw, 0.0)
    if abs(np.nansum(net)) < 1.0:
        return None
    return [
        round(float(np.nansum(net[_CUM[m] : _CUM[m + 1]])) / 1e3, 2) for m in range(12)
    ]


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
    single hub series with columns ``year, hour, rt, da`` (not zonal). Prefers
    real-time (``rt``) — the scarcity-relevant series the C3c tail scores — and
    falls back to day-ahead (``da``) for hours where ``rt`` is NaN (e.g. CAISO,
    whose ``rt`` column is partly unpopulated), mirroring the rt→da fallback in
    ``_actual_avg_lmp`` / C3a. Returns ``None`` when the file or the year is
    absent, so the tail criterion stays SKIPPED rather than scoring against a
    missing actual. The returned array is sorted by hour.
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
    rt = df["rt"].to_numpy(float)
    da = df["da"].to_numpy(float) if "da" in df.columns else np.full_like(rt, np.nan)
    return np.where(np.isnan(rt), da, rt)


@lru_cache(maxsize=None)
def _actual_rt_padded(iso: str, year: int, hours: int) -> np.ndarray | None:
    """Return the actual hourly RT LMP as an ``(hours,)`` NaN-padded array, or ``None``.

    Same source as :func:`_actual_lmp_hourly` (``actual_lmp_hourly_<ISO>.parquet``
    under the canonical validation-source dir), but scattered by the ``hour``
    column into a fixed ``hours``-length array so it aligns positionally with the
    model's per-hour series for the C3c scarcity-tail count and the demand-weighted
    monthly-MAE. This is the ISO-agnostic replacement for ``derive_ordc_overlay``'s
    ERCOT-only ``_actual_rt`` (whose CAL_DIR still points at the pre-W1
    ``inputs/calibration`` tree) — it lets the settlement-price overlay block
    (below) score every ISO from its own actuals, not just ERCOT.
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
    if "da" in df.columns:
        rt = np.where(np.isnan(rt), df["da"].to_numpy(float), rt)
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
    """Load the derived actual-LMP reference (``scripts/derive_actual_lmp.py``).

    Returns an empty dict when the reference is absent, so the dashboard renders
    a model-only price card rather than failing.

    The reference lives under the canonical validation-source dir
    (``data/raw/_validation-source``, ``paths.CALIBRATION_DIR``) since the W1
    data relocation; the pre-relocation ``inputs/calibration`` path is kept as a
    fallback so an older checkout still resolves.
    """
    from market_sim.config.paths import CALIBRATION_DIR

    for p in (
        CALIBRATION_DIR / "actual_lmp.json",
        REPO / "inputs" / "calibration" / "actual_lmp.json",
    ):
        if p.exists():
            return json.loads(p.read_text())
    return {}


def _actual_avg_lmp(iso: str, year: int) -> dict | None:
    """Return ``{da?, rt?}`` actual avg LMP ($/MWh) for an ISO-year, or None.

    The ``src`` provenance string in the reference is dropped here; only the
    numeric day-ahead / real-time means flow into the dashboard payload.
    """
    rec = _actual_lmp_table().get(str(iso), {}).get(str(int(year))) or {}
    out = {k: rec[k] for k in ("da", "rt", "da_mon", "rt_mon") if k in rec}
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


def _btm_share(plant_id: int, group: str, iso: str = "ERCOT") -> float:
    """Behind-the-meter host self-supply share of net gen for a CHP plant.

    Mirrors :func:`market_sim.data.fleet.chp_btm_pct` — the ISO's derived
    EIA-923 sector (thermal-tranches artifact) first, then the hardcoded
    ERCOT sector map — so the report's add-back uses the same share the LP
    pull-out used.
    """
    if group not in ("CC_CHP", "CT_CHP", "ST_CHP"):
        return 0.0
    from market_sim.data.chp import chp_btm_pct

    return chp_btm_pct(int(plant_id), group, iso=iso) / 100.0


@lru_cache(maxsize=1)
def _eia860_plant_info() -> tuple[dict[int, float], dict[int, str]]:
    """Return ``({plant_id: nameplate MW}, {plant_id: name})`` from EIA-860.

    The national per-plant nameplate (summed over units) and plant name, so
    non-ERCOT bundles (PJM, etc.) — whose plants are absent from the ERCOT
    CAMPD bin sheet — still get a real capacity and label in the dashboard.
    """
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.fleet import EIA_860_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_PARQUET_NAME
    if not path.exists():
        return {}, {}
    df = pd.read_parquet(
        path, columns=["plant_id", "plant_name", "nameplate_capacity_mw"]
    )
    df["plant_id"] = df["plant_id"].astype(int)
    npl = df.groupby("plant_id")["nameplate_capacity_mw"].sum().to_dict()
    nm = df.groupby("plant_id")["plant_name"].first().to_dict()
    return (
        {int(k): float(v) for k, v in npl.items()},
        {int(k): str(v) for k, v in nm.items()},
    )


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
        config = ScenarioConfig(**sc)
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
