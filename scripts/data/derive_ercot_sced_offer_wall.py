"""Derive the ERCOT measured RT (SCED) spare-offer wall ladder.

The ERCOT-86 RT/SCED-basis correction of the cleared-share wall's price ladder
(``ScenarioConfig.ercot_offer_surface_cleared_share_rt``). ERCOT-84 Finding 1
measured that the DAM wall's data basis is structurally cheap: over the mid-band
windows the *entire* submitted DAM curve mass prices $13-44 effective, while the
real $150-800 moderate-tightness band cleared on the RT (SCED) offers of the
~3 GW online spare beyond the AS carve-out — a surface the 60-Day DAM
disclosure genuinely does not contain. This derive measures that surface from
the 60-Day **SCED** Gen Resource Data full-year corpus on disk (the
publication-month shards ``YYYY-MM.part*.parquet`` under ``data/raw/ercot/``
and/or ``data/raw/ercot/SCED/`` — see ``_CORPUS_DIRS``; the 2026-08-03
delivery-2023 re-upload lives in the subdirectory):

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
artifact gets NO RT wall (the DAM basis is retained byte-identical), and each
year's ladder is derived only from that year's own posted RT offers. Since the
full-year NP3-965 intake (2026-07-21) the training window 2023-2025 is all
present; the owner authorized extending the SCED basis to 2023, lifting the
earlier post-Uri regime bar. The publication shards carry ~60-day-lagged
delivery, so rows are filtered to the exact DELIVERY year (`_delivery_year_rows`)
— the validation-holdout 2022 and locked-test 2026 rows carried in adjacent
publication files never enter a training-year surface.

Coverage is DISCLOSED, never silently capped: the provenance block records the
per-year source-file inventory and the per-(class x bin) interval/day counts, so
an under-sampled bin (e.g. 2024-05, sparse in the corpus; 2025 Nov partial / Dec
absent, published after the corpus cutoff) is visible at the artifact level.

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
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from market_sim.config.paths import CALIBRATION_DIR, ERCOT_MIS_DIR  # noqa: E402

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

SCED_DIR = ERCOT_MIS_DIR
DEFAULT_OUT = CALIBRATION_DIR / "ercot_sced_offer_wall_condbinned.json"

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

# Numeric SCED columns stored as strings in the corpus — the full-year
# publication shards leave unused curve steps as EMPTY STRINGS ('') where the
# sample-day extracts left them null, so a bare ``.to_numpy(float)`` raises.
# Coerced once at load ('' -> NaN); the segment builder already treats NaN as
# an absent step (np.isfinite guard).
_NUMERIC_COLS = _SCED2_MW + _SCED2_PR + ["HASL", "HSL", "HDL", "LSL", "Base Point"]


def _coerce_sced_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """In-place-coerce the string-typed numeric SCED columns present to float."""
    cols = [c for c in _NUMERIC_COLS if c in df.columns]
    df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")
    return df


# Full-year publication-month shard name: ``YYYY-MM.partNNNN.parquet``. The
# ``YYYY-MM`` is the ERCOT MIS PUBLICATION month; NP3-965 posts ~60 days after
# delivery, so a publication file carries delivery dates ~2 months earlier. A
# file is therefore NEVER trusted to belong to its filename year — the shards
# are selected by a publication WINDOW and rows are filtered to the exact
# DELIVERY year (`_delivery_year_rows`). Without that filter the ~60-day bleed
# would fold the validation holdout (Nov/Dec 2022, carried in early-2023
# publication files) and the locked-test 2026 rows into adjacent training
# years — a rule-22 holdout leak.
_PUB_SHARD_RE = re.compile(r"(\d{4})-(\d{2})\.part\d+\.parquet$")

# Where the publication-month corpus may live: the top-level MIS directory
# (the original 2026-07-21 full-corpus upload, purged from the repo by the
# 2026-07-22 large-blob history rewrite) and the ``SCED/`` subdirectory (the
# 2026-08-03 owner re-upload of the delivery-2023 window, ERCOT-151 §4 ask 1).
# Both are scanned; a filename present in both resolves to the LAST directory
# listed (the re-upload wins over a stale top-level copy).
_CORPUS_DIRS: tuple[Path, ...] = (SCED_DIR, SCED_DIR / "SCED")

# A publication-month corpus supersedes the legacy sample-day extracts for a
# delivery year ONLY when it covers a majority of that year's 12 delivery
# months, judged from filenames alone by the exact 60-day lag (delivery month
# M's primary publication month is M+2). This guards the partial-window
# footgun the 2026-08-03 re-upload created: its edge months (2024-01..03)
# fall inside delivery-2024's publication window but carry only Jan-2024
# deliveries — 1 of 12 months must NOT silently replace 2024's sample-day
# basis. The July-2026 full corpus covered 12/12/10 delivery months for
# 2023/2024/2025, so every historical derive selects exactly as before.
_CORPUS_MIN_DELIVERY_MONTHS = 7


def _sced_source_files(year: int) -> list[Path]:
    """Parquet shards that may contain SCED delivery rows for ``year``.

    Unions the two on-disk naming families:

    * legacy delivery-labeled sample-day files
      (``60_DAY_SCED_DISCLOSURE_..._{year}_*.parquet``), and
    * full-year publication-month shards (``YYYY-MM.partNNNN.parquet``, in any
      of ``_CORPUS_DIRS``) whose publication month falls in
      ``[(year, Feb) .. (year+1, Mar)]`` — the window that brackets delivery
      year ``year`` (delivery month M publishes ~M+2; ±1 month margin for the
      60-day lag straddling month boundaries).

    Row-level delivery-year filtering (`_delivery_year_rows`) is still applied
    after read, so an over-wide window only costs a wasted read, never a leak.
    """
    lo = year * 12 + 1  # (year, Feb), 0-based month index
    hi = (year + 1) * 12 + 2  # (year+1, Mar)
    by_name: dict[str, Path] = {}
    for d in _CORPUS_DIRS:
        for p in d.glob("[0-9][0-9][0-9][0-9]-[0-1][0-9].part*.parquet"):
            m = _PUB_SHARD_RE.search(p.name)
            if m and lo <= int(m.group(1)) * 12 + (int(m.group(2)) - 1) <= hi:
                by_name[p.name] = p  # later _CORPUS_DIRS entries win
    pub = sorted(by_name.values(), key=lambda p: p.name)
    # The full-year publication-month corpus SUPERSEDES the legacy
    # delivery-labeled sample-day extracts: those specific days also appear in
    # the full-year shards (and the legacy extracts are hour-windowed subsets),
    # so unioning both would double-weight them. Supersede only on MAJORITY
    # delivery-month coverage (see _CORPUS_MIN_DELIVERY_MONTHS): a fragmentary
    # publication bleed from an adjacent year's window falls back to legacy.
    if pub:
        months = {
            (int(m.group(1)), int(m.group(2)))
            for p in pub
            if (m := _PUB_SHARD_RE.search(p.name))
        }
        covered = 0
        for dm in range(1, 13):  # delivery month -> primary publication month
            idx = year * 12 + (dm - 1) + 2
            if (idx // 12, idx % 12 + 1) in months:
                covered += 1
        if covered >= _CORPUS_MIN_DELIVERY_MONTHS:
            return pub
    legacy = SCED_DIR.glob(
        f"60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_{year}_*.parquet"
    )
    return sorted(legacy)


def _delivery_year_rows(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Keep only rows whose SCED delivery year == ``year``.

    The delivery year is the ``SCED Time Stamp`` (Central Prevailing Time)
    calendar year. The corpus stamps are ``MM/DD/YYYY HH:MM:SS`` (the NP3-965
    publication format); legacy sample-day files were ISO ``YYYY-MM-DD``. The
    year is the only 4-consecutive-digit run in either format (month/day are
    always 2 digits), so a first-``\\d{4}`` extract reads the year from both.
    This equals the CST year everywhere except the sub-hour Jan-1 boundary
    (negligible against the whole-month 60-day-lag bleed this removes).
    """
    yr = df["SCED Time Stamp"].astype(str).str.extract(r"(\d{4})", expand=False)
    return df[yr == str(year)]


def _load_year(year: int) -> tuple[pd.DataFrame, list[str]]:
    """ON-status merchant gas SCED rows for ``year`` + the source file names."""
    files = _sced_source_files(year)
    frames: list[pd.DataFrame] = []
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        frames.append(_coerce_sced_numeric(df[stat.str.startswith("ON")].copy()))
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


def _chunk_segments(
    df: pd.DataFrame, gas_day: pd.Series, hour_bin: np.ndarray
) -> pd.DataFrame:
    """One file's ON-gas rows -> priced/binned spare segments (memory-bounded).

    The per-file leg of the streaming derive: CPT->CST clock, hour-of-year,
    delivered-gas normalization and net-load binning, applied to a single
    shard's rows so the wide 70-column frame is never held for a whole year.
    Returns segments with ``cls, bin, mult, mw, ts, day`` (empty frame if the
    shard contributes nothing).
    """
    if df.empty:
        return pd.DataFrame(columns=["cls", "bin", "mult", "mw", "ts", "day"])
    # CPT -> fixed CST -> non-leap hour-of-year (Feb 29 dropped to match the
    # model's 8760 clock and _netload_pct).
    ts = pd.to_datetime(df["SCED Time Stamp"])
    cst = ts.dt.tz_localize(
        "America/Chicago", ambiguous=True, nonexistent="shift_forward"
    ).dt.tz_convert(_STD_TZ)
    mo = cst.dt.month.to_numpy()
    dy = cst.dt.day.to_numpy()
    hh = cst.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    if df.empty:
        return pd.DataFrame(columns=["cls", "bin", "mult", "mw", "ts", "day"])
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    df["_ts_key"] = df["SCED Time Stamp"].to_numpy()
    df["_date"] = cst.dt.normalize().dt.tz_localize(None)[np.asarray(ok)].to_numpy()
    df["gas_day"] = gas_day.reindex(pd.DatetimeIndex(df["_date"])).to_numpy(float)
    df = df[df["gas_day"] > 0]
    if df.empty:
        return pd.DataFrame(columns=["cls", "bin", "mult", "mw", "ts", "day"])

    seg = _spare_segments(df)
    if seg.empty:
        return pd.DataFrame(columns=["cls", "bin", "mult", "mw", "ts", "day"])
    # Effective-HR multiplier: price / delivered-gas day (the DAM wall's own
    # convention, so the apply-time target = mult x gas_day).
    date_by_ts = dict(zip(df["_ts_key"], df["gas_day"]))
    seg["mult"] = (seg["price"] / seg["ts"].map(date_by_ts).astype(float)).astype(
        "float32"
    )
    seg["mw"] = seg["mw"].astype("float32")
    seg["bin"] = hour_bin[np.minimum(seg["hoy"].to_numpy(int), HOURS - 1)]
    seg["day"] = seg["hoy"].to_numpy(int) // 24
    return seg[["cls", "bin", "mult", "mw", "ts", "day"]]


def derive_year(
    year: int,
    gas_day: pd.Series,
    edges_override: "tuple[float, ...] | None" = None,
    position_tail: bool = False,
) -> tuple[dict, dict, list[str]]:
    """Return ``({cls: {"ladder": [...]}}, coverage, source_files)`` for one year.

    Streams the year's source shards one at a time, accumulating only the
    compact ``(mult, mw)`` arrays and interval/day sets per ``(class, bin)`` —
    the full-year corpus's wide offer-curve frame never lands in memory at once
    (the non-streaming build OOM'd at ~12 GB on a full year).
    ``edges_override`` (ercot-180 ``--top-scoped``) refines the bin grid with
    the IDENTICAL statistic; default None keeps the frozen stepped geometry.
    ``position_tail`` (ercot-181 ``--position-tail``) additionally emits each
    (class, bin)'s measured tail step points above the p90 grid point
    (``lib.positiontail.tail_support`` — the same population, its own
    support); the ladders themselves are byte-unchanged.
    """
    files = _sced_source_files(year)
    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES if edges_override is None else edges_override)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1

    mult_acc: dict[tuple, list[np.ndarray]] = {}
    mw_acc: dict[tuple, list[np.ndarray]] = {}
    ts_seen: dict[tuple, set] = {}
    day_seen: dict[tuple, set] = {}
    saw_rows = False
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = _coerce_sced_numeric(df[stat.str.startswith("ON")].copy())
        seg = _chunk_segments(df, gas_day, hour_bin)
        del df
        if seg.empty:
            continue
        saw_rows = True
        for (cls, b), grp in seg.groupby(["cls", "bin"], sort=False):
            key = (cls, int(b))
            mult_acc.setdefault(key, []).append(grp["mult"].to_numpy())
            mw_acc.setdefault(key, []).append(grp["mw"].to_numpy())
            ts_seen.setdefault(key, set()).update(grp["ts"].tolist())
            day_seen.setdefault(key, set()).update(grp["day"].tolist())
        del seg
    if not saw_rows:
        return {}, {}, [p.name for p in files]

    out: dict[str, dict] = {}
    coverage: dict[str, list[dict]] = {}
    for cls in sorted({c for (c, _b) in mult_acc}):
        ladders: list[list[list[float]]] = []
        cov: list[dict] = []
        tails: list[list[list[float]]] = []
        for b in range(n_bins):
            key = (cls, b)
            if key in mult_acc:
                mult = np.concatenate(mult_acc[key])
                mw = np.concatenate(mw_acc[key])
                qs = _weighted_quantiles(
                    mult.astype(float), mw.astype(float), LADDER_QUANTILES
                )
                n_iv = len(ts_seen[key])
                n_days = len(day_seen[key])
                mw_sum = float(mw.sum())
                if position_tail:
                    from lib.positiontail import tail_support

                    tails.append(tail_support(mult, mw))
            else:
                qs = [float("nan")] * len(LADDER_QUANTILES)
                n_iv = n_days = 0
                mw_sum = 0.0
                if position_tail:
                    tails.append([])
            ladders.append(
                [[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)]
            )
            cov.append(
                {
                    "intervals": n_iv,
                    "days": n_days,
                    "mean_spare_gw": round(mw_sum / max(n_iv, 1) / 1e3, 3),
                }
            )
        out[cls] = {"ladder": ladders}
        if position_tail:
            out[cls]["tail"] = tails
        coverage[cls] = cov
    return out, coverage, [p.name for p in files]


def derive_year_continuous(
    year: int, gas_day: pd.Series
) -> tuple[dict, dict, list[str]]:
    """Per-hour-node RT spare-offer ladder for one year (ERCOT-178).

    The IDENTICAL statistic :func:`derive_year` computes per net-load bin —
    the MW-weighted :data:`LADDER_QUANTILES` of online-spare SCED2 segment
    multipliers — keyed per corpus hour node instead (PRECOMMIT-ercot178 §2):
    a node's x-coordinate is the hour's within-year net-load percentile rank
    (:func:`_netload_pct`, unchanged). Hours with exactly tied ranks pool
    their segments (forced by x-monotonicity). Streaming accumulation exactly
    as the stepped derive (per (class, hour) instead of per (class, bin)).
    Zero new parameters; year-scoped with no pooled fallback, as the stepped
    artifact.
    """
    files = _sced_source_files(year)
    pct = _netload_pct(year)
    # hour_bin is only consumed by _chunk_segments for the 'bin' column; feed
    # the hour-of-year index instead so the same streaming leg keys per hour.
    hour_key = np.arange(HOURS)

    mult_acc: dict[tuple, list[np.ndarray]] = {}
    mw_acc: dict[tuple, list[np.ndarray]] = {}
    ts_seen: dict[tuple, set] = {}
    saw_rows = False
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, year)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = _coerce_sced_numeric(df[stat.str.startswith("ON")].copy())
        seg = _chunk_segments(df, gas_day, hour_key)
        del df
        if seg.empty:
            continue
        saw_rows = True
        for (cls, h), grp in seg.groupby(["cls", "bin"], sort=False):
            key = (cls, int(h))
            mult_acc.setdefault(key, []).append(grp["mult"].to_numpy())
            mw_acc.setdefault(key, []).append(grp["mw"].to_numpy())
            ts_seen.setdefault(key, set()).update(grp["ts"].tolist())
        del seg
    if not saw_rows:
        return {}, {}, [p.name for p in files]

    out: dict[str, dict] = {}
    coverage: dict[str, dict] = {}
    for cls in sorted({c for (c, _h) in mult_acc}):
        by_x: dict[float, tuple[list[np.ndarray], list[np.ndarray]]] = {}
        n_iv = 0
        for (c, h), mults in mult_acc.items():
            if c != cls:
                continue
            x = float(pct[h])
            acc = by_x.setdefault(x, ([], []))
            acc[0].extend(mults)
            acc[1].extend(mw_acc[(c, h)])
            n_iv += len(ts_seen[(c, h)])
        pct_nodes: list[float] = []
        ladders: list[list[float]] = []
        for x in sorted(by_x):
            mult = np.concatenate(by_x[x][0])
            mw = np.concatenate(by_x[x][1])
            qs = _weighted_quantiles(
                mult.astype(float), mw.astype(float), LADDER_QUANTILES
            )
            if not all(np.isfinite(q) for q in qs):
                continue
            pct_nodes.append(round(x, 6))
            ladders.append([round(float(m), 3) for m in qs])
        out[cls] = {"pct": pct_nodes, "ladder": ladders, "n_nodes": len(pct_nodes)}
        coverage[cls] = {"nodes": len(pct_nodes), "intervals": n_iv}
    return out, coverage, [p.name for p in files]


def _main_position_tail(args) -> None:
    """ERCOT-181: write the position-tail vintage (PRECOMMIT-ercot181 §3).

    The frozen stepped artifact is loaded and COPIED VERBATIM (its ladder
    blocks are the sub-p90 truth the seam proof asserts byte-identity
    against); each requested year's (class, bin) tail is derived fresh from
    the corpus with the identical population construction, and the
    re-computed 5-rung ladder must REPRODUCE the frozen artifact's exactly —
    a corpus drifted since the frozen derive would make the appended tail
    inconsistent with its p90 anchor, so a mismatch is stop-the-line, never
    papered over.
    """
    from lib.positiontail import POSITIONTAIL_TAG

    frozen = json.loads(DEFAULT_OUT.read_text())
    gas_day = _gas_day_series()
    result = json.loads(json.dumps(frozen))  # deep copy via round-trip
    tail_cov: dict[str, dict] = {}
    for y in args.years:
        per_cls, cov, _files = derive_year(y, gas_day, position_tail=True)
        for cls, entry in per_cls.items():
            frozen_tbl = frozen.get(cls, {}).get("years", {}).get(str(y))
            if not frozen_tbl:
                raise SystemExit(
                    f"--position-tail: frozen artifact has no {cls} year "
                    f"{y} block to anchor a tail on"
                )
            if entry["ladder"] != frozen_tbl["ladder"]:
                raise SystemExit(
                    f"--position-tail: re-derived {cls} {y} ladder does not "
                    "reproduce the frozen artifact's — the corpus has "
                    "drifted since the frozen derive; STOP (rule 23: "
                    "re-derive only on a source-data update, and then the "
                    "frozen artifact first)"
                )
            result[cls]["years"][str(y)]["tail"] = entry["tail"]
            tail_cov.setdefault(str(y), {})[cls] = [len(t) for t in entry["tail"]]
            print(f"{y} {cls}: tail points by bin = {[len(t) for t in entry['tail']]}")
    prov = result.setdefault("_provenance", {})
    prov["conditioning"] = POSITIONTAIL_TAG
    prov["positiontail"] = {
        "precommit": "docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md",
        "statistic": (
            "per (class, year, bin): the MW-weighted empirical quantile "
            "function of the SAME spare-segment multiplier population the "
            "frozen ladder measured, at its own distinct step points above "
            "the p90 grid point (lib/positiontail.tail_support; multipliers "
            "HCAP-clipped by the parent segment construction, round(3); x = "
            "cumulative-MW fraction, round(6), strictly increasing). "
            "Sub-p90 ladders are the frozen artifact's blocks byte-verbatim; "
            "an empty tail keeps the frozen p90 end-clamp byte-identical "
            "(zero-support rule)"
        ),
        "tail_years": [int(y) for y in args.years],
        "tail_points_per_bin": tail_cov,
        "frozen_source": DEFAULT_OUT.name,
    }
    out = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_sced_offer_wall_positiontail.json"
    )
    out.write_text(json.dumps(result, indent=1))
    print(f"wrote {out} (frozen artifact untouched)")


def main() -> None:
    """Derive and write the RT (SCED) spare-offer wall ladder JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2024])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--continuous",
        action="store_true",
        help="ERCOT-178: write the continuous-node vintage "
        "(ercot_sced_offer_wall_contpct.json) instead of the stepped bins — "
        "the frozen stepped artifact is never touched by this mode",
    )
    ap.add_argument(
        "--top-scoped",
        action="store_true",
        help="ERCOT-180: write the top-scoped vintage "
        "(ercot_sced_offer_wall_topscoped.json) — frozen stepped values below "
        "p97, conduct-identified stepped sub-bins above, ULP-pair step-encoded "
        "(PRECOMMIT-ercot180 §3); neither frozen artifact is touched",
    )
    ap.add_argument(
        "--position-tail",
        action="store_true",
        help="ERCOT-181: write the position-tail vintage "
        "(ercot_sced_offer_wall_positiontail.json) — the frozen stepped "
        "ladders byte-verbatim plus each (class, year, bin)'s measured tail "
        "step points above p90 (PRECOMMIT-ercot181 §3); the frozen artifact "
        "is never touched",
    )
    args = ap.parse_args()
    if sum([args.continuous, args.top_scoped, args.position_tail]) > 1:
        raise SystemExit(
            "--continuous, --top-scoped and --position-tail are mutually exclusive"
        )
    if args.position_tail:
        _main_position_tail(args)
        return
    if args.top_scoped:
        _main_topscoped(args)
        return
    if args.continuous:
        _main_continuous(args)
        return

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
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965), "
                "full-year publication-month corpus (data/raw/ercot/"
                "YYYY-MM.part*.parquet), rows filtered to delivery years "
                + "-".join(str(y) for y in args.years)
                + "; publication files carry ~60-day-lagged delivery, so "
                "rows are delivery-year-filtered — 2022 (validation holdout) "
                "and 2026 (locked test) rows carried in adjacent publication "
                "files are excluded. Per-delivery-year coverage (may be "
                "partial at the corpus edges — 2024-05 sparse; 2025 Nov "
                "partial and Dec absent, published after the corpus cutoff) "
                "is disclosed per (class x bin) in coverage below"
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
                "Per-year ladders, NO pooled fallback (rule 13): a year "
                "absent from this artifact gets NO RT wall (the DAM basis is "
                "retained byte-identical). 2023 is now INCLUDED — the "
                "full-year NP3-965 corpus intake (2026-07-21) supplies "
                "complete 2023 delivery coverage, and the owner authorized "
                "extending the SCED basis to 2023, lifting the earlier "
                "post-Uri regime bar (charter §3.4/§5). Each year's ladder is "
                "still derived only from that year's own posted RT offers"
            ),
            "source_files": sources,
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


def _main_continuous(args) -> None:
    """Write the ERCOT-178 continuous-node vintage (``--continuous``).

    A NEW artifact (`ercot_sced_offer_wall_contpct.json` unless ``--out``
    overrides) for the pre-registered `ercot_offer_surface_continuous` gate —
    the frozen stepped artifact is never modified (PRECOMMIT-ercot178 §2).
    Year-scoped, no pooled fallback, exactly as the stepped vintage.
    """
    out_path = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_sced_offer_wall_contpct.json"
    )
    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        per_year[y], cov, files = derive_year_continuous(y, gas_day)
        coverage[str(y)] = cov
        sources[str(y)] = files
        for cls, entry in per_year[y].items():
            print(f"{y} {cls}: {entry['n_nodes']} ladder nodes")

    classes = sorted({c for d in per_year.values() for c in d})
    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day SCED Disclosure Gen Resource Data (NP3-965), "
                "full-year publication-month corpus, rows filtered to "
                "delivery years " + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "IDENTICAL statistic to the stepped vintage (MW-weighted "
                "quantile ladder of online-spare SCED2 segment multipliers), "
                "keyed per corpus HOUR NODE at the hour's within-year "
                "net-load percentile rank instead of per bin; rank-tied hours "
                "pool their segments (PRECOMMIT-ercot178 §2, zero new "
                "parameters)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - "
                "wind - solar), forward-native"
            ),
            "conditioning": "continuous-netload-pct",
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "classes": {
                "CC": ["CCGT90", "CCLE90"],
                "CT": ["SCGT90", "SCLE90"],
            },
            "year_scoped": (
                "Per-year node tables, NO pooled fallback (rule 13): a year "
                "absent from this artifact gets NO RT wall (the DAM basis is "
                "retained byte-identical), exactly as the stepped vintage"
            ),
            "source_files": sources,
            "coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update, never because a residual moved; the stepped artifact "
                "is untouched by this vintage"
            ),
        }
    }
    for cls in classes:
        result[cls] = {
            "years": {
                str(y): per_year[y][cls] for y in args.years if cls in per_year[y]
            }
        }

    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


def _main_topscoped(args) -> None:
    """Write the ercot-180 TOP-SCOPED vintage (``--top-scoped``).

    PRECOMMIT-ercot180 §1/§3: below p97 the FROZEN stepped artifact's own
    per-bin ladders are byte-copied; the former p97-p100 top bin is split at
    the conduct-identified edges (the committed edge-identification record),
    each sub-bin's ladder computed by the IDENTICAL stepped statistic on the
    sub-bin's own rows; a zero-support sub-bin inherits the frozen parent
    top-bin ladder. ULP-pair step-encoded for the merged interpolation
    machinery. Year-scoped, training years only, no pooled fallback; neither
    frozen artifact is touched.
    """
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from scripts.lib.topscoped_encode import (
        TOPSCOPED_TAG,
        encode_step_nodes,
        load_identified_edges,
        rows_from_pairs,
        split_top_bin,
    )

    out_path = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_sced_offer_wall_topscoped.json"
    )
    frozen = json.loads(DEFAULT_OUT.read_text())
    legacy_edges = [float(x) for x in frozen["_provenance"]["netload_pct_edges"]]
    new_edges = load_identified_edges()
    edges_ext = tuple(legacy_edges + new_edges)
    n_legacy = len(legacy_edges)
    n_sub = len(new_edges) + 1

    gas_day = _gas_day_series()
    result_cls: dict[str, dict] = {}
    coverage: dict[str, dict] = {}
    sources: dict[str, list[str]] = {}
    for y in args.years:
        ext, cov, files = derive_year(y, gas_day, edges_override=edges_ext)
        sources[str(y)] = files
        for cls in ("CC", "CT"):
            fro_tbl = frozen.get(cls, {}).get("years", {}).get(str(y))
            if not fro_tbl:
                continue  # year-scoped: absent years stay absent
            legacy_rows = rows_from_pairs(fro_tbl["ladder"])
            sub_rows: list = []
            sub_disc: list[dict] = []
            for k in range(n_sub):
                b = n_legacy + k  # extended top sub-bins: indices n_legacy .. end
                lad = (
                    rows_from_pairs([ext[cls]["ladder"][b]])[0]
                    if cls in ext and b < len(ext[cls]["ladder"])
                    else [float("nan")] * len(LADDER_QUANTILES)
                )
                ok = all(np.isfinite(v) for v in lad)
                sub_rows.append(lad if ok else None)
                cov_b = (
                    cov.get(cls, [{}] * (b + 1))[b]
                    if cls in cov and b < len(cov[cls])
                    else {}
                )
                sub_disc.append(
                    {
                        "computed": ok,
                        "inherited_parent": not ok,
                        **{k2: cov_b.get(k2) for k2 in ("intervals", "days")},
                    }
                )
            edges_all, rows_all = split_top_bin(
                legacy_edges, legacy_rows, new_edges, sub_rows
            )
            xs, ys = encode_step_nodes(edges_all, rows_all)
            result_cls.setdefault(cls, {"years": {}})["years"][str(y)] = {
                "pct": xs,
                "ladder": ys,
            }
            coverage.setdefault(cls, {})[str(y)] = sub_disc
            print(f"{y} {cls}: sub-bins {[d['computed'] for d in sub_disc]}")

    result: dict = {
        "_provenance": {
            "source": frozen["_provenance"].get("source"),
            "method": (
                "TOP-SCOPED (ercot-180, form b): frozen stepped per-bin "
                "ladders byte-copied below p97; the p97-p100 bin split at the "
                "conduct-identified edges with the IDENTICAL MW-weighted "
                "quantile statistic per sub-bin; zero-support sub-bins "
                "inherit the frozen parent ladder; ULP-pair step-encoded "
                "(PRECOMMIT-ercot180 §1/§3, zero fitted scalars)"
            ),
            "driver": frozen["_provenance"].get("driver"),
            "conditioning": TOPSCOPED_TAG,
            "netload_pct_edges": list(edges_ext),
            "new_edges": list(new_edges),
            "edge_identification": "results/calibration/"
            "ercot180_edge_identification.json",
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "classes": frozen["_provenance"].get("classes"),
            "year_scoped": (
                "Per-year node tables, NO pooled fallback (rule 13), exactly "
                "as the frozen stepped vintage; training years only"
            ),
            "source_files": sources,
            "topscoped_sub_bin_coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a SCED disclosure source-data "
                "update or a re-identified edge record, never because a "
                "residual moved; neither frozen artifact is touched"
            ),
        }
    }
    result.update(result_cls)
    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
