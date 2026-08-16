"""Derive the ERCOT measured DAM CLEARED-SHARE boundary + above-boundary offer wall.

The ERCOT-72 covered-CC / CT composition mechanism's frozen measured artifact
(``ScenarioConfig.ercot_offer_surface_cleared_share``). Two measured facts from
the 60-Day DAM disclosure Gen Resource Data, 2023-2025, per gas class per
net-load-percentile bin:

1. **The cleared-share boundary.** The share of the class's live capability
   (config-collapsed non-OUT HSL) that the DAM actually cleared for energy
   (``Awarded Quantity``, self-schedules included). ERCOT has no DAM must-offer:
   on moderate shoulder days ~34% of CC and ~53% of CT live capability is not
   in the day-ahead energy supply at ANY price (ERCOT-72 measurement, May-2024
   shoulder family: 8.6 GW of CC live HSL carried no offer curve at all while
   only 63 MW held spinning AS). The model's econ tranches span ~92% of each
   plant, so it serves shoulder demand with capacity reality's market did not
   have on offer — the ERCOT-70 "+675 MW covered-CC excess at $24-29" and the
   flat mid-stack in one number.

2. **The above-boundary wall.** The MW-weighted quantile ladder of the offer
   prices of the OFFERED-BUT-UNCLEARED curve segments (the real posted supply
   between the cleared level and the top of the posted curves), as effective
   heat-rate multipliers ``price / gas_day`` — the same normalization the
   mid-curve/conditional surfaces use (target = mult x gas_day at apply time).
   This is the measured price of the real marginal supply above the cleared
   position: on the May-2024 shoulders it spans ~$30-100+ where the model's
   econ_high band reads ~$25.

Provenance / admissibility (CLAUDE.md rules 13/14/26): both quantities are
ex-ante market-design measurements (posted offers and cleared positions, never
clearing-price outcomes fed back as inputs); the driver is the year's own
net-load percentile (forward-native — a forecast year's bins regenerate from
its own load/VRE and respond to changed conditions); zero fitted scalars. The
boundary is CONDITION-BINNED, not day-pinned: a given day gets its bin's pooled
share, never its own observed value.

FROZEN AGAINST RESIDUALS (rule 23): re-derive only when the disclosure source
files update; never because a residual moved. Re-derivation commits must cite
the data change.

Usage::

    python scripts/data/derive_ercot_dam_cleared_share.py \
        [--years 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_dam_cleared_share_condbinned.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

from market_sim.config.paths import (  # noqa: E402
    CALIBRATION_DIR,
    EIA_HOURLY_DIR,
    ERCOT_MIS_DIR,
)
import sys  # noqa: E402

sys.path.insert(0, str(REPO))  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO / "src"))

from scripts.data.build_ercot_as_withholding import prevailing_he_to_cst  # noqa: E402
from scripts.data.derive_ercot_thermal_dam_availability import _site  # noqa: E402

from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL  # noqa: E402
from market_sim.data.fuel import HENRY_HUB_DAILY_PATH  # noqa: E402

DAM_DIR = ERCOT_MIS_DIR
EIA930_HOURLY = EIA_HOURLY_DIR / "ERCO hourly.parquet"
DEFAULT_OUT = CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json"

HOURS = 8760
_STD_TZ = "Etc/GMT+6"  # ERCOT fixed standard-time clock (derive_actual_lmp)
_MONTH_START_HOUR = np.array(
    [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016]
)

# DAM Resource Type -> derived class key. Scope: the two disclosure-covered
# MERCHANT gas classes the composition thesis names (ERCOT-70/72). CHP/cogen
# behaviour differs (steam-host self-schedules) but the disclosure cannot
# separate them at class grain; the pooled CC share is therefore biased HIGH
# (cogens clear ~always), making the boundary CONSERVATIVE for the merchant
# CC_REGULAR fleet it is applied to.
CLASS_OF_RESTYPE: dict[str, str] = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
    # ERCOT-77 (drag-lane steam participation cliff, 2026-07-17 charter):
    # the legacy gas-STEAM class, added as a NEW derived class from the SAME
    # frozen disclosure source (rule 23 — an extension deriving a new class,
    # not a residual re-tune; the CC/CT tables above re-derive byte-identical).
    # ERCOT-73 leg c measured the steam version of the no-must-offer cliff on
    # the May-2024 shoulder family: live HSL 5.9 GW vs 1.2 GW DA-cleared
    # (share 0.20), ~half of live resource-hours declared OFF in the DAM.
    "GSREH": "ST",
    "GSNONR": "ST",
    "GSSUP": "ST",
}

# Net-load percentile bin edges. Finer than the peak surface's (0.80/0.90/0.97):
# the cleared-share boundary's phenomenon lives in the MODERATE bands (the
# May-shoulder family sits ~p30-p70), which the peak surface's single [0, 0.80)
# bottom bin cannot resolve. Even coverage below p80, then the peak surface's
# own tight-range edges — structural resolution, not a tuned quantity.
NETLOAD_PCT_EDGES: tuple[float, ...] = (0.25, 0.50, 0.70, 0.80, 0.90, 0.97)

# Ladder quantiles: the conditional-surface convention (5 rungs).
LADDER_QUANTILES: tuple[float, ...] = (0.1, 0.3, 0.5, 0.7, 0.9)

# Offer prices at/above the cap family are clipped to HCAP so a single $9,999
# test row cannot skew a rung; the builder additionally caps targets at
# 0.95 x VOLL (the shared ercot_offer_surface_price_cap_frac guard).
HCAP_USD_MWH = 5000.0

_MW_COLS = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
_PR_COLS = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
_READ_COLS = [
    "Delivery Date",
    "Hour Ending",
    "Resource Name",
    "Resource Type",
    "HSL",
    "Resource Status",
    "Awarded Quantity",
] + [c for pair in zip(_MW_COLS, _PR_COLS) for c in pair]


def _gas_day_series() -> pd.Series:
    """Delivered-gas daily price: HH daily + ERCOT basis, forward-filled."""
    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    return s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])


def _netload_pct(year: int) -> np.ndarray:
    """Measured net-load percentile rank (0-1) on the model's non-leap clock."""
    df = pd.read_parquet(EIA930_HOURLY)
    std = pd.DatetimeIndex(df["UTC time"]).tz_localize("UTC").tz_convert(_STD_TZ)
    ok = (std.year == year) & ~((std.month == 2) & (std.day == 29))
    idx = _MONTH_START_HOUR[std.month - 1] + (std.day - 1) * 24 + std.hour
    sub = df.loc[np.asarray(ok)].copy()
    sub["hoy"] = idx[np.asarray(ok)]
    sub = sub.groupby("hoy").first().reindex(range(HOURS))
    netload = (
        sub["Demand"].to_numpy(float)
        - sub["NG: WND"].to_numpy(float)
        - sub["NG: SUN"].to_numpy(float)
    )
    return pd.Series(netload).rank(pct=True).to_numpy()


def _load_year(year: int) -> pd.DataFrame:
    """Gen_Resource rows whose DELIVERY date falls in ``year`` (60-day lag
    spills a year's deliveries into the following year's publication files)."""
    frames: list[pd.DataFrame] = []
    for y in (year, year + 1):
        for path in sorted(DAM_DIR.glob(f"*60d_DAM_Gen_Resource_Data_{y}_*.parquet")):
            df = pd.read_parquet(path, columns=_READ_COLS)
            df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
            dd = pd.to_datetime(df["Delivery Date"], format="%m/%d/%Y")
            keep = dd.dt.year == year
            if keep.any():
                sub = df[keep].copy()
                sub["dd"] = dd[keep]
                frames.append(sub)
    if not frames:
        return pd.DataFrame(columns=_READ_COLS + ["dd"])
    return pd.concat(frames, ignore_index=True)


def _collapse_and_segment(
    df: pd.DataFrame, gas_day: pd.Series
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Config-collapse to site-hours and extract uncleared offered segments.

    Returns ``(site_hours, segments)``:

    * ``site_hours``: one row per (cls, site, hoy) with ``live`` (max non-OUT
      config HSL), ``cleared`` (summed award, clipped to live).
    * ``segments``: offered-but-uncleared curve segments of the representative
      config (the awarded config where one exists, else the max-live config)
      with ``mw`` and effective-HR ``mult`` (price / gas_day, price clipped to
      HCAP), tagged with the site-hour's ``hoy``.
    """
    ts = prevailing_he_to_cst(df["dd"], df["Hour Ending"].astype(int))
    mo = ts.dt.month.to_numpy()
    dy = ts.dt.day.to_numpy()
    hh = ts.dt.hour.to_numpy()
    ok = ~((mo == 2) & (dy == 29))
    df = df.loc[np.asarray(ok)].copy()
    df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
    df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    df["avail"] = np.where(df["Resource Status"].eq("OUT"), 0.0, df["HSL"])
    df["award"] = df["Awarded Quantity"].fillna(0.0).clip(lower=0.0)

    # Representative config per site-hour: the awarded config where one
    # exists (its curve is the one the market saw at the cleared position),
    # else the max-live config (the train's capability statement).
    df["_awarded"] = (df["award"] > 0).astype(int)
    df = df.sort_values(["cls", "site", "hoy", "_awarded", "avail"])
    rep = df.groupby(["cls", "site", "hoy"], sort=False).tail(1)

    grp = df.groupby(["cls", "site", "hoy"], sort=False)
    site_hours = grp.agg(live=("avail", "max"), cleared=("award", "sum"))
    site_hours["cleared"] = np.minimum(site_hours["cleared"], site_hours["live"])
    site_hours = site_hours.reset_index()

    # Uncleared offered segments from the representative config's curve:
    # MW in (award, min(live, qmax)] at each curve step's price.
    MW = rep[_MW_COLS].to_numpy(float)
    PR = rep[_PR_COLS].to_numpy(float)
    award = rep["award"].to_numpy(float)
    avail = rep["avail"].to_numpy(float)
    gas = gas_day.reindex(rep["dd"].dt.normalize()).to_numpy(float)
    hoy = rep["hoy"].to_numpy(int)

    cls_vals = rep["cls"].to_numpy()
    seg_mw: list[np.ndarray] = []
    seg_mult: list[np.ndarray] = []
    seg_hoy: list[np.ndarray] = []
    seg_cls: list[np.ndarray] = []
    prev = np.zeros(len(rep))
    for k in range(MW.shape[1]):
        q = MW[:, k]
        p = np.minimum(PR[:, k], HCAP_USD_MWH)
        valid = ~np.isnan(q) & ~np.isnan(p) & (gas > 0)
        lo = np.maximum(prev, award)
        hi = np.minimum(q, avail)
        mw = np.where(valid, np.maximum(hi - lo, 0.0), 0.0)
        take = mw > 0
        if take.any():
            seg_mw.append(mw[take])
            seg_mult.append(p[take] / gas[take])
            seg_hoy.append(hoy[take])
            seg_cls.append(cls_vals[take])
        prev = np.where(valid, np.maximum(prev, q), prev)
    segments = pd.DataFrame(
        {
            "hoy": np.concatenate(seg_hoy) if seg_hoy else np.array([], int),
            "mw": np.concatenate(seg_mw) if seg_mw else np.array([]),
            "mult": np.concatenate(seg_mult) if seg_mult else np.array([]),
            "cls": (np.concatenate(seg_cls) if seg_cls else np.array([], dtype=object)),
        }
    )
    return site_hours, segments


def _weighted_quantiles(
    values: np.ndarray, weights: np.ndarray, qs: tuple[float, ...]
) -> list[float]:
    """MW-weighted quantiles of ``values``."""
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cw = np.cumsum(w)
    if cw[-1] <= 0:
        return [float("nan")] * len(qs)
    cw = cw / cw[-1]
    return [float(np.interp(q, cw, v)) for q in qs]


def derive_year(
    year: int,
    gas_day: pd.Series,
    edges_override: "tuple[float, ...] | None" = None,
) -> dict:
    """Return ``{cls: {"cleared_share": [...], "ladder": [...]}}`` for one year.

    ``edges_override`` (ercot-180 ``--top-scoped``) refines the bin grid with
    the IDENTICAL statistics; default None keeps the frozen stepped geometry.
    """
    df = _load_year(year)
    if df.empty:
        return {}
    site_hours, segments = _collapse_and_segment(df, gas_day)
    pct = _netload_pct(year)
    edges = np.asarray(NETLOAD_PCT_EDGES if edges_override is None else edges_override)
    hour_bin = np.searchsorted(edges, pct, side="right")  # (HOURS,)
    n_bins = len(edges) + 1

    site_hours["bin"] = hour_bin[site_hours["hoy"].to_numpy(int)]
    segments["bin"] = hour_bin[segments["hoy"].to_numpy(int)]

    out: dict[str, dict] = {}
    for cls in sorted(site_hours["cls"].unique()):
        sh = site_hours[site_hours["cls"] == cls]
        seg = segments[segments["cls"] == cls]
        shares: list[float] = []
        ladders: list[list[list[float]]] = []
        for b in range(n_bins):
            sb = sh[sh["bin"] == b]
            live = float(sb["live"].sum())
            cleared = float(sb["cleared"].sum())
            shares.append(round(cleared / live, 4) if live > 0 else float("nan"))
            gb = seg[seg["bin"] == b]
            qs = _weighted_quantiles(
                gb["mult"].to_numpy(float), gb["mw"].to_numpy(float), LADDER_QUANTILES
            )
            ladders.append(
                [[float(q), round(m, 3)] for q, m in zip(LADDER_QUANTILES, qs)]
            )
        out[cls] = {"cleared_share": shares, "ladder": ladders}
    return out


def derive_year_continuous(year: int, gas_day: pd.Series) -> dict:
    """Per-hour-node cleared share + wall ladder for one year (ERCOT-178).

    The IDENTICAL statistics :func:`derive_year` computes per net-load bin,
    keyed per corpus hour node instead (PRECOMMIT-ercot178 §2): a node's
    x-coordinate is the hour's within-year net-load percentile rank
    (:func:`_netload_pct`, unchanged); its ``share`` is Σcleared/Σlive over
    that hour's site-rows; its ladder is the MW-weighted
    :data:`LADDER_QUANTILES` of that hour's offered-but-uncleared segment
    multipliers. Hours with exactly tied ranks pool their rows (the only
    cross-hour pooling; forced by x-monotonicity). Zero new parameters.
    """
    df = _load_year(year)
    if df.empty:
        return {}
    site_hours, segments = _collapse_and_segment(df, gas_day)
    pct = _netload_pct(year)
    site_hours = site_hours.copy()
    segments = segments.copy()
    site_hours["x"] = pct[site_hours["hoy"].to_numpy(int)]
    segments["x"] = pct[segments["hoy"].to_numpy(int)]

    out: dict[str, dict] = {}
    for cls in sorted(site_hours["cls"].unique()):
        sh = site_hours[site_hours["cls"] == cls]
        seg = segments[segments["cls"] == cls]
        g = sh.groupby("x").agg(live=("live", "sum"), cleared=("cleared", "sum"))
        g = g[g["live"] > 0].sort_index()
        share_pct = [round(float(x), 6) for x in g.index]
        share = [
            round(float(c) / float(lv), 4) for c, lv in zip(g["cleared"], g["live"])
        ]
        pct_nodes: list[float] = []
        ladders: list[list[float]] = []
        for x, gb in seg.groupby("x", sort=True):
            qs = _weighted_quantiles(
                gb["mult"].to_numpy(float), gb["mw"].to_numpy(float), LADDER_QUANTILES
            )
            if not all(np.isfinite(q) for q in qs):
                continue
            pct_nodes.append(round(float(x), 6))
            ladders.append([round(float(m), 3) for m in qs])
        out[cls] = {
            "share_pct": share_pct,
            "share": share,
            "pct": pct_nodes,
            "ladder": ladders,
            "n_share_nodes": len(share_pct),
            "n_ladder_nodes": len(pct_nodes),
        }
    return out


def main() -> None:
    """Derive and write the cleared-share boundary + wall JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--continuous",
        action="store_true",
        help="ERCOT-178: write the continuous-node vintage "
        "(ercot_dam_cleared_share_contpct.json) instead of the stepped bins — "
        "the frozen stepped artifact is never touched by this mode",
    )
    ap.add_argument(
        "--top-scoped",
        action="store_true",
        help="ERCOT-180: write the top-scoped vintage "
        "(ercot_dam_cleared_share_topscoped.json) — frozen stepped values "
        "below p97, conduct-identified stepped sub-bins above, ULP-pair "
        "step-encoded (PRECOMMIT-ercot180 §3); neither frozen artifact is "
        "touched",
    )
    args = ap.parse_args()
    if args.continuous and args.top_scoped:
        raise SystemExit("--continuous and --top-scoped are mutually exclusive")
    if args.top_scoped:
        _main_topscoped(args)
        return
    if args.continuous:
        _main_continuous(args)
        return

    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    for y in args.years:
        per_year[y] = derive_year(y, gas_day)
        for cls, entry in per_year[y].items():
            print(f"{y} {cls}: cleared_share by bin = {entry['cleared_share']}")
            print(
                f"          wall p50 mult by bin = "
                f"{[lad[2][1] for lad in entry['ladder']]}"
            )

    classes = sorted({c for d in per_year.values() for c in d})
    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day DAM Disclosure Gen Resource Data, delivery years "
                + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "config-collapsed site-hour live HSL vs summed energy awards "
                "(cleared share of live capability) + MW-weighted quantile "
                "ladder of offered-but-uncleared curve-segment prices as "
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
                "ST": ["GSREH", "GSNONR", "GSSUP"],
            },
            "frozen": (
                "rule 23 — re-derive only on a disclosure source-data update, "
                "never because a residual moved"
            ),
        }
    }
    for cls in classes:
        years_entry = {
            str(y): per_year[y][cls] for y in args.years if cls in per_year[y]
        }
        # Pooled fallback (forward/unmapped years): per-bin live-weighted pool
        # across years — recomputed from the per-year shares' simple mean and
        # the per-year ladders' rung-wise mean (each year contributes equally;
        # the shares are within +/-0.03 across 2023-2025 so the pooling choice
        # is immaterial).
        n_bins = len(NETLOAD_PCT_EDGES) + 1
        pooled_share = [
            float(np.nanmean([years_entry[y]["cleared_share"][b] for y in years_entry]))
            for b in range(n_bins)
        ]
        pooled_ladder = [
            [
                [
                    float(LADDER_QUANTILES[r]),
                    float(
                        np.nanmean(
                            [years_entry[y]["ladder"][b][r][1] for y in years_entry]
                        )
                    ),
                ]
                for r in range(len(LADDER_QUANTILES))
            ]
            for b in range(n_bins)
        ]
        result[cls] = {
            "years": years_entry,
            "pooled": {
                "cleared_share": [round(s, 4) for s in pooled_share],
                "ladder": [[[q, round(m, 3)] for q, m in lad] for lad in pooled_ladder],
            },
        }

    args.out.write_text(json.dumps(result, indent=1))
    print(f"wrote {args.out}")


def _main_continuous(args) -> None:
    """Write the ERCOT-178 continuous-node vintage (``--continuous``).

    A NEW artifact (`ercot_dam_cleared_share_contpct.json` unless ``--out``
    overrides) for the pre-registered `ercot_offer_surface_continuous` gate —
    the frozen stepped artifact is never modified (PRECOMMIT-ercot178 §2; the
    PJM within-season vintage precedent). Pooled fallback = the same node
    statistics over the union of the years' rows at each rank.
    """
    out_path = (
        args.out
        if args.out != DEFAULT_OUT
        else CALIBRATION_DIR / "ercot_dam_cleared_share_contpct.json"
    )
    gas_day = _gas_day_series()
    per_year: dict[int, dict] = {}
    pooled_frames: dict[str, dict[str, list]] = {}
    for y in args.years:
        per_year[y] = derive_year_continuous(y, gas_day)
        for cls, entry in per_year[y].items():
            print(
                f"{y} {cls}: {entry['n_share_nodes']} share nodes, "
                f"{entry['n_ladder_nodes']} ladder nodes"
            )

    # Pooled fallback: union of the years' node rows re-grouped by rank. Never
    # consulted for a year carried in `years` (the apply precedence), so it
    # only serves forward/unmapped years exactly as the stepped pooled table.
    classes = sorted({c for d in per_year.values() for c in d})
    for cls in classes:
        rows: list[tuple[float, list[float]]] = []
        srows: list[tuple[float, float]] = []
        for y in args.years:
            e = per_year.get(y, {}).get(cls)
            if not e:
                continue
            rows += list(zip(e["pct"], e["ladder"]))
            srows += list(zip(e["share_pct"], e["share"]))
        lad_by_x: dict[float, list[list[float]]] = {}
        for x, lad in rows:
            lad_by_x.setdefault(x, []).append(lad)
        sh_by_x: dict[float, list[float]] = {}
        for x, s in srows:
            sh_by_x.setdefault(x, []).append(s)
        xs = sorted(lad_by_x)
        sxs = sorted(sh_by_x)
        pooled_frames[cls] = {
            "share_pct": [round(x, 6) for x in sxs],
            "share": [round(float(np.mean(sh_by_x[x])), 4) for x in sxs],
            "pct": [round(x, 6) for x in xs],
            "ladder": [
                [
                    round(float(np.mean([lad[r] for lad in lad_by_x[x]])), 3)
                    for r in range(len(LADDER_QUANTILES))
                ]
                for x in xs
            ],
        }

    result: dict = {
        "_provenance": {
            "source": (
                "ERCOT 60-Day DAM Disclosure Gen Resource Data, delivery years "
                + "-".join(str(y) for y in args.years)
            ),
            "method": (
                "IDENTICAL statistics to the stepped vintage (config-collapsed "
                "site-hour cleared share of live capability + MW-weighted "
                "quantile ladder of offered-but-uncleared segment multipliers), "
                "keyed per corpus HOUR NODE at the hour's within-year net-load "
                "percentile rank instead of per bin; rank-tied hours pool "
                "their rows (PRECOMMIT-ercot178 §2, zero new parameters)"
            ),
            "driver": (
                "system net-load percentile within year (EIA-930 demand - wind "
                "- solar), forward-native (a forecast year ranks its own "
                "load+VRE)"
            ),
            "conditioning": "continuous-netload-pct",
            "ladder_quantiles": list(LADDER_QUANTILES),
            "hcap_usd_mwh": HCAP_USD_MWH,
            "iso": "ERCOT",
            "classes": {
                "CC": ["CCGT90", "CCLE90"],
                "CT": ["SCGT90", "SCLE90"],
                "ST": ["GSREH", "GSNONR", "GSSUP"],
            },
            "frozen": (
                "rule 23 — re-derive only on a disclosure source-data update, "
                "never because a residual moved; the stepped artifact is "
                "untouched by this vintage"
            ),
        }
    }
    for cls in classes:
        years_entry = {
            str(y): per_year[y][cls] for y in args.years if cls in per_year[y]
        }
        result[cls] = {"years": years_entry, "pooled": pooled_frames[cls]}

    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


def _main_topscoped(args) -> None:
    """Write the ercot-180 TOP-SCOPED vintage (``--top-scoped``).

    PRECOMMIT-ercot180 §1/§3: below p97 the FROZEN stepped artifact's own
    per-bin shares and ladders are byte-copied; the former p97-p100 top bin is
    split at the conduct-identified edges, each sub-bin's share/ladder
    computed by the IDENTICAL stepped statistics on the sub-bin's own rows; a
    zero-support sub-bin inherits the frozen parent top-bin value (share and
    ladder handled independently — their supports differ). The pooled
    fallback mirrors the frozen pooled construction: sub-bin values are the
    nanmean of the years' COMPUTED sub-bin values, all-NaN sub-bins
    inheriting the frozen pooled parent. ULP-pair step-encoded. Neither
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
        else CALIBRATION_DIR / "ercot_dam_cleared_share_topscoped.json"
    )
    frozen = json.loads(DEFAULT_OUT.read_text())
    legacy_edges = [float(x) for x in frozen["_provenance"]["netload_pct_edges"]]
    new_edges = load_identified_edges()
    edges_ext = tuple(legacy_edges + new_edges)
    n_legacy = len(legacy_edges)
    n_sub = len(new_edges) + 1

    def _tbl_from(
        fro_shares: list, fro_ladder: list, sub_sh: list, sub_ld: list
    ) -> dict:
        """One year/pooled table: separate share + ladder encodes."""
        e_sh, r_sh = split_top_bin(
            legacy_edges,
            [[float(s)] for s in fro_shares],
            new_edges,
            [None if s is None else [s] for s in sub_sh],
        )
        xs_s, ys_s = encode_step_nodes(e_sh, r_sh)
        e_ld, r_ld = split_top_bin(
            legacy_edges, rows_from_pairs(fro_ladder), new_edges, sub_ld
        )
        xs_l, ys_l = encode_step_nodes(e_ld, r_ld)
        return {
            "share_pct": xs_s,
            "share": [r[0] for r in ys_s],
            "pct": xs_l,
            "ladder": ys_l,
        }

    gas_day = _gas_day_series()
    ext_by_year = {
        y: derive_year(y, gas_day, edges_override=edges_ext) for y in args.years
    }

    classes = sorted(k for k in frozen if not k.startswith("_"))
    result_cls: dict[str, dict] = {}
    coverage: dict[str, dict] = {}
    for cls in classes:
        years_entry: dict[str, dict] = {}
        # raw computed sub values per year (NaN = no support), for pooling
        raw_sh: dict[int, list[float]] = {}
        raw_ld: dict[int, list[list[float]]] = {}
        for y in args.years:
            fro_tbl = frozen[cls].get("years", {}).get(str(y))
            ext_tbl = ext_by_year.get(y, {}).get(cls)
            if not fro_tbl or not ext_tbl:
                continue
            sub_sh: list = []
            sub_ld: list = []
            disc: list[dict] = []
            for k in range(n_sub):
                b = n_legacy + k
                s = float(ext_tbl["cleared_share"][b])
                lad = rows_from_pairs([ext_tbl["ladder"][b]])[0]
                raw_sh.setdefault(y, []).append(s)
                raw_ld.setdefault(y, []).append(lad)
                sub_sh.append(s if np.isfinite(s) else None)
                ok_l = all(np.isfinite(v) for v in lad)
                sub_ld.append(lad if ok_l else None)
                disc.append(
                    {"share_computed": bool(np.isfinite(s)), "ladder_computed": ok_l}
                )
            years_entry[str(y)] = _tbl_from(
                fro_tbl["cleared_share"], fro_tbl["ladder"], sub_sh, sub_ld
            )
            coverage.setdefault(cls, {})[str(y)] = disc
            print(f"{y} {cls}: sub-bins {[d['ladder_computed'] for d in disc]}")
        # pooled: frozen pooled below p97; nanmean of computed sub values above
        pooled = frozen[cls].get("pooled")
        if pooled and years_entry:
            sub_sh_p: list = []
            sub_ld_p: list = []
            for k in range(n_sub):
                ss = [raw_sh[y][k] for y in raw_sh]
                sv = (
                    float(np.nanmean(ss))
                    if any(np.isfinite(x) for x in ss)
                    else float("nan")
                )
                sub_sh_p.append(round(sv, 4) if np.isfinite(sv) else None)
                lads = np.array([raw_ld[y][k] for y in raw_ld], dtype=float)
                with np.errstate(all="ignore"):
                    lv = np.nanmean(lads, axis=0)
                sub_ld_p.append(
                    [round(float(v), 3) for v in lv] if np.isfinite(lv).all() else None
                )
            result_cls[cls] = {
                "years": years_entry,
                "pooled": _tbl_from(
                    pooled["cleared_share"], pooled["ladder"], sub_sh_p, sub_ld_p
                ),
            }
        else:
            result_cls[cls] = {"years": years_entry}

    result: dict = {
        "_provenance": {
            "source": frozen["_provenance"].get("source"),
            "method": (
                "TOP-SCOPED (ercot-180, form b): frozen stepped per-bin "
                "shares/ladders byte-copied below p97; the p97-p100 bin split "
                "at the conduct-identified edges with the IDENTICAL "
                "statistics per sub-bin; zero-support sub-bins inherit the "
                "frozen parent values; pooled fallback mirrors the frozen "
                "pooled construction over the computed sub values; ULP-pair "
                "step-encoded (PRECOMMIT-ercot180 §1/§3, zero fitted scalars)"
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
            "topscoped_sub_bin_coverage": coverage,
            "frozen": (
                "rule 23 — re-derive only on a disclosure source-data update "
                "or a re-identified edge record, never because a residual "
                "moved; neither frozen artifact is touched"
            ),
        }
    }
    result.update(result_cls)
    out_path.write_text(json.dumps(result, indent=1))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
