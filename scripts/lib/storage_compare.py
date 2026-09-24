"""Model-vs-actual storage dispatch + SOC comparison for the Run Explorer.

REPORT-ONLY. Builds the ``storageCmp`` block of a backcast run payload
(``runs/<id>.js``, one per year) from two committed inputs and nothing else:

* the bundle's ``hourly/storage_<year>.parquet`` sidecar — the model's P1
  charge / discharge / SOC per (tech, hour), written by every solve since
  2026-09-16 (``run_calibration_full._write_storage_hourly_sidecar``);
* ``data/raw/storage-dispatch-actuals/<ISO>_storage_hourly.parquet`` — the
  measured fleet series on the same fixed-standard-time 8760 clock
  (``scripts/data/build_storage_dispatch_actuals.py``).

No LP, no scorer, no gate: storage-dispatch accuracy left the rubric at v2.7
and nothing here re-arms it. The block is display data plus a few fit
statistics computed HERE (the frontend never recomputes fit).

Tech scope is per ISO (:data:`ACTUAL_TECHS`): the CAISO actual is batteries
only (CAISO folds pumped storage into Large Hydro), so the model side is its
``li_ion`` tech; ERCOT has no pumped storage.

Wire layout (per year)::

    {"src", "techs", "note", "obsHours",
     "net": {"m": i16b64, "a": i16b64|None},            # MW, NaN = -32768
     "soc": {"m": i16b64, "a": i16b64|None},            # % of own annual max x10
     "diur": {"m": [288], "a": [288]|None},             # month x hour mean net MW
     "socDiur": {"m": [288], "a": [288]|None},          # month x hour mean SOC %
     "stats": {...}}

SOC is compared as SHAPE (percent of each series' own annual max), never as
level: the CAISO SOC actual covers stand-alone batteries only, and the ERCOT
model's energy cap is hour-varying (the measured-capability overlay), so no
single MWh denominator is shared by both sides.
"""

from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUALS_DIR = REPO / "data" / "raw" / "storage-dispatch-actuals"

HOURS = 8760
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_OF_HOUR = np.repeat(np.arange(12), np.asarray(_DAYS_IN_MONTH) * 24)
_HOD = np.tile(np.arange(24), 365)

# Model storage techs that the ISO's actual series measures (see module doc).
ACTUAL_TECHS: dict[str, tuple[str, ...]] = {
    "CAISO": ("li_ion",),
    "ERCOT": ("li_ion", "pumped_storage"),
}
SOURCE_LABEL: dict[str, str] = {
    "CAISO": "CAISO Today's Outlook (batteries) · SOC: CAISO Daily Energy Storage Report (stand-alone, RTD)",
    "ERCOT": "EIA-930 ERCO (BAT + UES)",
}
# Minimum observed actual hours for a year to publish a comparison.
MIN_OBS_HOURS = 24 * 28
# Clock check: lags (h) scanned for the max-correlation lag. Reported only.
LAG_SCAN = range(-3, 4)
# A year whose actual discharge exceeds charge by more than this is flagged:
# physically a fleet cannot discharge more than it charged (RTE < 1), so the
# source is under-reporting charging (e.g. CAISO 2022 co-located charging).
CHARGE_UNDERREPORT_RATIO = 1.02


def _i16(a: np.ndarray, scale: float = 1.0) -> str:
    """Encode a (8760,) float series as base64 little-endian int16 (NaN = -32768)."""
    v = np.asarray(a, dtype=float) * scale
    out = np.full(v.shape, -32768, dtype="<i2")
    ok = np.isfinite(v)
    out[ok] = np.clip(np.round(v[ok]), -32767, 32767).astype("<i2")
    return base64.b64encode(out.tobytes()).decode()


def _diurnal(a: np.ndarray, mask: np.ndarray) -> list[float | None]:
    """Month x hour-of-day mean of ``a`` over ``mask`` hours, flattened m*24+h."""
    out: list[float | None] = []
    for m in range(12):
        for h in range(24):
            sel = mask & (_MONTH_OF_HOUR == m) & (_HOD == h)
            out.append(round(float(a[sel].mean()), 1) if sel.any() else None)
    return out


def _r(x: np.ndarray, y: np.ndarray) -> float | None:
    """Pearson r over jointly-finite entries, or None when undefined."""
    ok = np.isfinite(x) & np.isfinite(y)
    if ok.sum() < 3 or x[ok].std() == 0 or y[ok].std() == 0:
        return None
    return round(float(np.corrcoef(x[ok], y[ok])[0, 1]), 3)


def _best_lag(m: np.ndarray, a: np.ndarray) -> int | None:
    """Lag (h) maximizing corr(model[t], actual[t+lag]) — a clock sanity check."""
    best, best_r = None, -2.0
    for lag in LAG_SCAN:
        if lag >= 0:
            r = _r(m[: HOURS - lag], a[lag:])
        else:
            r = _r(m[-lag:], a[: HOURS + lag])
        if r is not None and r > best_r:
            best, best_r = lag, r
    return best


def _pct_of_max(a: np.ndarray) -> np.ndarray:
    """Series as percent of its own finite annual max (NaN-preserving)."""
    mx = np.nanmax(a) if np.isfinite(a).any() else np.nan
    if not np.isfinite(mx) or mx <= 0:
        return np.full(a.shape, np.nan)
    return 100.0 * a / mx


def load_actual(iso: str, year: int) -> pd.DataFrame | None:
    """Return the ISO-year actual frame (8760 rows, sorted by hour) or None."""
    path = ACTUALS_DIR / f"{iso}_storage_hourly.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    df = df[df["year"] == year].sort_values("hour")
    return df if len(df) == HOURS else None


def load_model(bundle_dir: Path, iso: str, year: int) -> dict[str, np.ndarray] | None:
    """Return the model's hourly charge/discharge/SOC summed over the ISO's techs."""
    path = Path(bundle_dir) / "hourly" / f"storage_{year}.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    if "pass" in df.columns:
        passes = set(df["pass"].astype(str))
        df = df[
            df["pass"].astype(str) == ("P1" if "P1" in passes else sorted(passes)[-1])
        ]
    techs = ACTUAL_TECHS.get(iso, tuple(df["tech"].astype(str).unique()))
    df = df[df["tech"].astype(str).isin(techs)]
    if df.empty:
        return None
    g = df.groupby("hour", sort=True)
    idx = np.arange(HOURS)

    def col(c: str, min_count: int = 0) -> np.ndarray:
        if c not in df.columns:
            return np.full(HOURS, np.nan)
        s = g[c].sum(min_count=min_count).reindex(idx)
        return s.to_numpy(dtype=float)

    return {
        "charge": np.nan_to_num(col("charge_mw")),
        "discharge": np.nan_to_num(col("discharge_mw")),
        "soc": col("soc_mwh", min_count=1),
        "techs": sorted(df["tech"].astype(str).unique()),
    }


def build_storage_compare(bundle_dir: Path, iso: str, year: int) -> dict | None:
    """Build one year's ``storageCmp`` payload block, or None when not comparable.

    None when the bundle has no storage sidecar, the ISO has no actuals file,
    or the actual observes fewer than :data:`MIN_OBS_HOURS` hours that year.
    """
    model = load_model(bundle_dir, iso, year)
    actual = load_actual(iso, year)
    if model is None or actual is None:
        return None
    a_net = actual["net_mw"].to_numpy(dtype=float)
    obs = np.isfinite(a_net)
    if obs.sum() < MIN_OBS_HOURS:
        return None
    m_net = model["discharge"] - model["charge"]
    a_dis = actual["discharge_mw"].to_numpy(dtype=float)
    a_chg = actual["charge_mw"].to_numpy(dtype=float)
    a_soc = actual["soc_mwh"].to_numpy(dtype=float)
    has_asoc = bool(np.isfinite(a_soc).sum() >= MIN_OBS_HOURS)
    m_soc_pct = _pct_of_max(model["soc"])
    a_soc_pct = _pct_of_max(a_soc) if has_asoc else None
    all_hours = np.ones(HOURS, dtype=bool)

    notes = []
    if obs.sum() < HOURS - 24:
        notes.append(
            f"Actual observed for {int(obs.sum())} of {HOURS} hours; fit statistics, "
            "throughput and the month x hour maps use those hours only."
        )
    a_dis_twh = float(np.nansum(a_dis)) / 1e6
    a_chg_twh = float(np.nansum(a_chg)) / 1e6
    if a_chg_twh > 0 and a_dis_twh > CHARGE_UNDERREPORT_RATIO * a_chg_twh:
        notes.append(
            f"Source reports more discharge ({a_dis_twh:.2f} TWh) than charging "
            f"({a_chg_twh:.2f} TWh) — physically impossible for a fleet, so the source "
            "under-reports charging (co-located charging not metered as battery). "
            "Read shape, not net level, for this year."
        )
    if iso == "CAISO":
        notes.append(
            "Batteries only (CAISO folds pumped storage into Large Hydro); model side = li_ion."
        )
        if has_asoc:
            notes.append(
                "SOC actual = stand-alone batteries only (hybrids publish no SOC) — "
                "compared as % of each series' own annual max."
            )
    elif iso == "ERCOT":
        notes.append(
            "No public historical fleet SOC for ERCOT — model SOC shown alone."
        )

    return {
        "src": SOURCE_LABEL.get(iso, iso),
        "techs": model["techs"],
        "note": " ".join(notes) or None,
        "obsHours": int(obs.sum()),
        "net": {"m": _i16(m_net), "a": _i16(a_net)},
        "soc": {
            "m": _i16(m_soc_pct, 10.0),
            "a": _i16(a_soc_pct, 10.0) if a_soc_pct is not None else None,
        },
        "diur": {"m": _diurnal(m_net, obs), "a": _diurnal(a_net, obs)},
        "socDiur": {
            "m": _diurnal(m_soc_pct, all_hours & np.isfinite(m_soc_pct)),
            "a": _diurnal(a_soc_pct, np.isfinite(a_soc_pct))
            if a_soc_pct is not None
            else None,
        },
        "stats": {
            "rNet": _r(np.where(obs, m_net, np.nan), a_net),
            "rDiur": _r(
                np.asarray(_diurnal(m_net, obs), dtype=float),
                np.asarray(_diurnal(a_net, obs), dtype=float),
            ),
            "rSoc": _r(m_soc_pct, a_soc_pct) if a_soc_pct is not None else None,
            "bestLag": _best_lag(np.where(obs, m_net, np.nan), a_net),
            "mDisTwh": round(float(model["discharge"][obs].sum()) / 1e6, 3),
            "aDisTwh": round(a_dis_twh, 3),
            "mChgTwh": round(float(model["charge"][obs].sum()) / 1e6, 3),
            "aChgTwh": round(a_chg_twh, 3),
            "mPeakDis": round(float(model["discharge"].max()), 0),
            "aPeakDis": round(float(np.nanmax(a_dis)), 0),
            "mPeakChg": round(float(model["charge"].max()), 0),
            "aPeakChg": round(float(np.nanmax(a_chg)), 0),
        },
    }


def summary_row(block: dict) -> dict:
    """The scalar part of a block (stats + provenance) for a JSON record."""
    return {
        "src": block["src"],
        "techs": block["techs"],
        "obsHours": block["obsHours"],
        "note": block["note"],
        **block["stats"],
    }
