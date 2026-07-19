"""Derive the ERCOT measured RT (SCED) spare-offer wall ladder.

The ERCOT-86 RT/SCED-basis correction of the cleared-share wall's price ladder
(``ScenarioConfig.ercot_offer_surface_cleared_share_rt``). ERCOT-84 Finding 1
measured that the DAM wall's data basis is structurally cheap: over the mid-band
windows the *entire* submitted DAM curve mass prices $13-44 effective, while the
real $150-800 moderate-tightness band cleared on the RT (SCED) offers of the
~3 GW online spare beyond the AS carve-out — a surface the 60-Day DAM
disclosure genuinely does not contain. This derive measures that surface from
the 60-Day **SCED** Gen Resource Data sample days on disk:

* Per SCED interval, per merchant gas class (CCGT90/CCLE90 -> CC,
  SCGT90/SCLE90 -> CT; ST_GAS deliberately EXCLUDED — rule 19, the steam class
  is owned by the drag/steam-cliff structure), segment the energy-dispatchable
  **online spare** offer curve between Base Point and HASL (net of AS
  responsibility) on the SCED2 (as-dispatched) curve — the exact construction
  of ``scripts/probes/_ercot84_sced_spare_offers.py``, promoted to derive.
* Bin each interval by its hour's **within-year net-load percentile** (EIA-930
  demand - wind - solar), on the SAME bin edges as the DAM cleared-share
  artifact (imported, so the RT wall shares the DAM wall's bin geometry by
  construction — the apply seam asserts agreement).
* Emit, per (class x net-load bin), **capacity-weighted quantiles** of the
  spare segments' price-as-effective-HR-multiplier (price / delivered-gas day,
  price clipped to HCAP) — the conditional-surface ladder convention.

Provenance / admissibility (CLAUDE.md rule 13): the SCED spare offer ladder is
an ex-ante market-design measurement (posted RT offers of online capability,
never clearing-price outcomes fed back as inputs); the driver is the year's own
net-load percentile (forward-native); zero fitted scalars. The artifact is
**YEAR-SCOPED**: no pooled fallback is emitted — a year absent from the
artifact gets NO RT wall (the DAM basis is retained byte-identical). This is
deliberate (charter §3.4/§5): the on-disk SCED corpus is scoped SAMPLE days,
and a 2024/2025-derived surface is barred from 2023's distinct post-Uri
conservative-operations regime.

Coverage is DISCLOSED, never silently capped: the provenance block records the
per-year sample-day inventory and the per-(class x bin) interval/day counts, so
an under-sampled bin (e.g. 2025's tail bins, control days only) is visible at
the artifact level.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the SCED disclosure
source files update; never because a residual moved. Re-derivation commits must
cite the data change.

Usage::

    python scripts/data/derive_ercot_sced_offer_wall.py \
        [--years 2024] \
        [--out data/raw/_validation-source/ercot_sced_offer_wall_condbinned.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_ercot_dam_cleared_share import (  # noqa: E402
    HCAP_USD_MWH,
    HOURS,
    LADDER_QUANTILES,
    NETLOAD_PCT_EDGES,
    _MONTH_START_HOUR,
    _gas_day_series,
    _netload_pct,
    _weighted_quantiles,
)

SCED_DIR = REPO / "data" / "raw" / "ercot"
DEFAULT_OUT = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "ercot_sced_offer_wall_condbinned.json"
)

_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)

# SCED Resource Type -> derived class key. Scope: the two disclosure-covered
# MERCHANT gas classes only (the DAM wall's own scope minus steam — rule 19:
# ST_GAS pricing above its DA position is the steam-cliff/drag structure's).
CLASS_OF_RESTYPE: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
}

_SCED2_MW = [f"SCED2 Curve-MW{i}" for i in range(1, 36)]
_SCED2_PR = [f"SCED2 Curve-Price{i}" for i in range(1, 36)]
_READ_COLS = [
    "SCED Time Stamp",
    "Resource Type",
    "Telemetered Resource Status",
    "HASL",
    "Base Point",
] + [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ON-status merchant gas SCED rows for ``year`` + the source file names."""
    files = sorted(
        SCED_DIR.glob(
            f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
        )
    )
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        frames.append(df[stat.str.startswith("ON")].copy())
    if not frames:
        return pd.DataFrame(columns=_READ_COLS), []
    return pd.concat(frames, ignore_index=True), [p.name for p in files]


def _spare_segments(df: pd.DataFrame) -> pd.DataFrame:
    """Base Point -> HASL segments of the SCED2 curve (the online spare).

    One row per (interval-resource, curve step) slice of energy-dispatchable
    spare: MW in ``(max(prev_step, Base Point), min(step_MW, HASL)]`` at the
    step's price (clipped to HCAP). The ercot84 probe construction, vectorized
    over curve steps.
    """
    MW = df[_SCED2_MW].to_numpy(float)
    PR = df[_SCED2_PR].to_numpy(float)
    bp = np.maximum(df["Base Point"].to_numpy(float), 0.0)
    hasl = df["HASL"].to_numpy(float)
    hoy = df["hoy"].to_numpy(int)
    ts = df["_ts_key"].to_numpy()
    cls_vals = df["cls"].to_numpy()

    seg_mw: list[np.ndarray] = []
    seg_pr: list[np.ndarray] = []
    seg_hoy: list[np.ndarray] = []
    seg_ts: list[np.ndarray] = []
    seg_cls: list[np.ndarray] = []
    prev = bp.copy()
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = PR[:, k]
        valid = np.isfinite(q) & np.isfinite(p)
        hi = np.minimum(q, hasl)
        mw = np.where(valid, np.maximum(hi - np.maximum(prev, bp), 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg_mw.append(mw[take])
            seg_pr.append(np.minimum(p[take], HCAP_USD_MWH))
            seg_hoy.append(hoy[take])
            seg_ts.append(ts[take])
            seg_cls.append(cls_vals[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    return pd.DataFrame(
        {
            "hoy": np.concatenate(seg_hoy) if seg_hoy else np.array([], int),
            "mw": np.concatenate(seg_mw) if seg_mw else np.array([]),
            "price": np.concatenate(seg_pr) if seg_pr else np.array([]),
            "ts": np.concatenate(seg_ts) if seg_ts else np.array([], dtype=object),
            "cls": (np.concatenate(seg_cls) if seg_cls else np.array([], dtype=object)),
        }
    )


def derive_year(year: int, gas_day: pd.Series) -> tuple[dict, dict, list[str]]:
    """Return ``({cls: {"ladder": [...]}}, coverage, source_files)`` for one year."""
    df, files = _load_year(year)
    if df.empty:
        return {}, {}, files

    # CPT -> fixed CST -> non-leap hour-of-year (the probe's clock handling;
    # Feb 29 dropped to match the model's 8760 clock and _netload_pct).
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    df["_ts_key"] = df["SCED Time Stamp"].to_numpy()
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()

    gas = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    df["gas_day"] = gas
    df = df[df["gas_day"] > 0].copy()

    segments = _spare_segments(df)
    # Effective-HR multiplier normalization: price / delivered-gas day (the
    # DAM wall's own convention, so the apply-time target = mult x gas_day).
    date_by_ts = dict(zip(df["_ts_key"], df["gas_day"]))
    segments["mult"] = segments["price"] / segments["ts"].map(date_by_ts).astype(float)

    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1
    segments["bin"] = hour_bin[np.minimum(segments["hoy"].to_numpy(int), HOURS - 1)]

    out: dict[str, dict] = {}
    coverage: dict[str, list[dict]] = {}
    for cls in sorted(segments["cls"].unique()):
        seg = segments[segments["cls"] == cls]
        ladders: list[list[list[float]]] = []
        cov: list[dict] = []
        for b in range(n_bins):
            gb = seg[seg["bin"] == b]
            n_iv = int(gb["ts"].nunique())
            n_days = int(pd.Series(gb["hoy"] // 24).nunique())
            qs = (
                _weighted_quantiles(
                    gb["mult"].to_numpy(float),
                    gb["mw"].to_numpy(float),
                    LADDER_QUANTILES,
                )
                if len(gb)
                else [float("nan")] * len(LADDER_QUANTILES)
            )
            ladders.append(
                [[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)]
            )
            cov.append(
                {
                    "intervals": n_iv,
                    "days": n_days,
                    "mean_spare_gw": round(
                        float(gb["mw"].sum()) / max(n_iv, 1) / 1e3, 3
                    ),
                }
            )
        out[cls] = {"ladder": ladders}
        coverage[cls] = cov
    return out, coverage, files


def main() -> None:
    """Derive and write the RT (SCED) spare-offer wall ladder JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], cov, files = derive_year(y, gas_day)
        coverage[str(y)] = cov
        sources[str(y)] = files
        for cls, entry in per_year[y].items():
            p50 = [lad[2][1] for lad in entry["ladder"]]
            ivs = [c["intervals"] for c in cov[cls]]
            print(f"{y} {cls}: wall p50 mult by bin = {p50}")
            print(f"          intervals by bin     = {ivs}")

    classes = sorted({c for d in per_year.values() for c in d})
    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data, scoped sample "
                "days, delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "per-interval Base Point -> HASL segments of the SCED2 "
                "(as-dispatched) offer curve of ON-status merchant gas (the "
                "energy-dispatchable online spare, net of AS responsibility), "
                "MW-weighted quantile ladder of segment prices as "
                "effective-HR multipliers (price / HH-daily+ERCOT-basis gas), "
                "derived within net-load-percentile bins"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - wind "
                "- solar), forward-native (a forecast year's bins regenerate "
                "from its own load+VRE)"
            ),
            "netload_pct_edges": list(NETLOAD_PCT_EDGES),
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "classes": {
                "CC": ["CCGT90", "CCLE90"],
                "CT": ["SCGT90", "SCLE90"],
            },
            "year_scoped": (
                "NO pooled fallback by design (rule 13): the SCED corpus is "
                "scoped sample days and the RT offer surface is regime-bound "
                "— a year absent from this artifact gets NO RT wall (the DAM "
                "basis is retained); a 2024/2025-derived ladder is barred "
                "from 2023's post-Uri conservative-operations regime"
            ),
            "sample_day_files": sources,
            "coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved"
            ),
        }
    }
    for cls in classes:
        result[cls] = {
            "years": {
                str(y): per_year[y][cls] for y in args.years if cls in per_year[y]
            }
        }

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
