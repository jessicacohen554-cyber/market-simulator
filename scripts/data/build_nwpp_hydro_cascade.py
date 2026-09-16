#!/usr/bin/env python3
"""Derive the Columbia / lower Snake cascade-coupling parameters (NWPP-36, owner ruling N3).

Everything the LP row family ``model/lp/hydro_cascade.py`` needs is MEASURED
here from three committed sources and nothing is assumed (rule 13
``[R-MEASURED]``; PRECOMMIT ``docs/handoffs/PRECOMMIT-nwpp-36-2026-09-16.md`` §4,
whose acceptance rules are applied verbatim and whose STOP outcomes are written
into the artifact as ``coupled = False`` with the reason — never substituted):

* **τ per link** (§4.1) — cross-correlation of the two projects' hourly outflow
  HIGH-FREQUENCY ANOMALIES (value minus its centred 25-h moving mean) over
  2023–2024, ``τ = argmax_{L∈0..72} r(anom_u(t−L), anom_d(t))``; McNary's two
  upstreams are searched jointly on a 2-D grid. Acceptance: r(τ) ≥ 0.30 with a
  unique peak, 2023-only and 2024-only τ within ±1 h, implied celerity in
  1–30 mph for τ ≥ 1 h, cumulative τ monotone in distance down the mainstem.
* **The pondage band per coupled plant** (§4.2) — NID ``Surface Area (Acres)``
  × the MEASURED operated forebay range (p99.5 − p0.5 of the hourly forebay,
  2023 and 2024 separately, the smaller year used), in kcfs·h. A federal
  run-of-river plant outside 0.5–15 ft is a STOP on that plant.
* **η per plant-month** (§4.3) — EIA-923 net generation (NWPP-32's budget
  artifact) over the month's measured turbine flow, MWh per kcfs·h; a
  plant-month with no EIA-923 series takes the same month's η from the nearest
  year that has one and the substitution is listed.
* **Side inflow and head spill / outflow per plant-month** (§4.4) — measured
  monthly means, negatives floored at 0 with the magnitude listed; a floor
  above 2 % of the month's arriving water is a STOP on that link.

Sources (all committed): ``data/raw/nwpp-hydro/crohms/nwpp_crohms_hourly.parquet``
(+ ``nwpp_crohms_catalog.json`` for station coordinates) from
``scripts/data/fetch_nwpp_crohms_hourly.py``; ``data/raw/nwpp-hydro/
nwpp_hydro_budget.parquet`` (NWPP-32); ``data/raw/nwpp-hydro/nwpp_hydro_cascade_nid.csv``
(the verbatim NID rows, regenerated from the national CSV with ``--nid-national``).

Outputs (``data/raw/nwpp-hydro/``): ``nwpp_hydro_cascade_links.csv``,
``nwpp_hydro_cascade_monthly.csv``, ``nwpp_hydro_cascade_nid.csv``.

Rule 23 ``[R-FROZEN-DERIVE]``: re-run only when CROHMS, NID or EIA-923 update —
never against a residual.

Usage:
    python scripts/data/build_nwpp_hydro_cascade.py
    python scripts/data/build_nwpp_hydro_cascade.py --nid-national /path/nid_nation.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

HYDRO_DIR = RAW_DATA_DIR / "nwpp-hydro"
CROHMS_DIR = HYDRO_DIR / "crohms"
HOURLY_PATH = CROHMS_DIR / "nwpp_crohms_hourly.parquet"
CATALOG_PATH = CROHMS_DIR / "nwpp_crohms_catalog.json"
BUDGET_PATH = HYDRO_DIR / "nwpp_hydro_budget.parquet"
OUT_LINKS = HYDRO_DIR / "nwpp_hydro_cascade_links.csv"
OUT_MONTHLY = HYDRO_DIR / "nwpp_hydro_cascade_monthly.csv"
OUT_NID = HYDRO_DIR / "nwpp_hydro_cascade_nid.csv"

logger = logging.getLogger("build_nwpp_hydro_cascade")

# CROHMS station -> (EIA plant id, NID id, role, federal run-of-river?). The
# chain and its order are NWPP-32's published inventory (FINDING-nwpp-32
# §5(a); PRECOMMIT-nwpp-36 §2) — not chosen here. NID ids are the national
# CSV's own for the named dams (see nwpp_hydro_cascade_nid.csv).
STATIONS: dict[str, dict] = {
    "GCL": dict(plant_id=6163, nid="WA00262", role="head", federal_ror=False),
    "CHJ": dict(plant_id=3921, nid="WA00299", role="coupled", federal_ror=True),
    "WEL": dict(plant_id=3886, nid="WA00098", role="coupled", federal_ror=False),
    "RRH": dict(plant_id=3883, nid="WA00086", role="coupled", federal_ror=False),
    "RIS": dict(plant_id=6200, nid="WA00084", role="coupled", federal_ror=False),
    "WAN": dict(plant_id=3888, nid="WA00085", role="coupled", federal_ror=False),
    "PRD": dict(plant_id=3887, nid="WA00088", role="coupled", federal_ror=False),
    "MCN": dict(plant_id=3084, nid="OR00616", role="coupled", federal_ror=True),
    "JDA": dict(plant_id=3082, nid="OR00011", role="coupled", federal_ror=True),
    "TDA": dict(plant_id=3895, nid="OR00002", role="coupled", federal_ror=True),
    "BON": dict(plant_id=3075, nid="OR00001", role="coupled", federal_ror=True),
    "DWR": dict(plant_id=840, nid="ID00287", role="head", federal_ror=False),
    "LWG": dict(plant_id=6175, nid="WA00349", role="coupled", federal_ror=True),
    "LGS": dict(plant_id=3926, nid="WA00331", role="coupled", federal_ror=True),
    "LMN": dict(plant_id=3927, nid="WA00270", role="coupled", federal_ror=True),
    "IHR": dict(plant_id=3925, nid="WA00347", role="coupled", federal_ror=True),
}
# (link, upstream, downstream) in the PRECOMMIT §2 order.
LINKS: list[tuple[int, str, str]] = [
    (1, "GCL", "CHJ"),
    (2, "CHJ", "WEL"),
    (3, "WEL", "RRH"),
    (4, "RRH", "RIS"),
    (5, "RIS", "WAN"),
    (6, "WAN", "PRD"),
    (7, "PRD", "MCN"),
    (8, "IHR", "MCN"),
    (9, "MCN", "JDA"),
    (10, "JDA", "TDA"),
    (11, "TDA", "BON"),
    (12, "DWR", "LWG"),
    (13, "LWG", "LGS"),
    (14, "LGS", "LMN"),
    (15, "LMN", "IHR"),
]
MAINSTEM_ORDER = [
    "GCL",
    "CHJ",
    "WEL",
    "RRH",
    "RIS",
    "WAN",
    "PRD",
    "MCN",
    "JDA",
    "TDA",
    "BON",
]
# Published average discharge (BPA Inside Story pp. 14-15, via NWPP-32's chain
# csv) for the band-in-hours statistic; None where BPA publishes none.
PUBLISHED_AVG_DISCHARGE_KCFS: dict[str, float | None] = {
    "GCL": 107.7,
    "CHJ": 108.0,
    "WEL": None,
    "RRH": None,
    "RIS": None,
    "WAN": None,
    "PRD": None,
    "MCN": 169.8,
    "JDA": 172.4,
    "TDA": 177.9,
    "BON": 183.3,
    "DWR": 5.82,
    "LWG": 49.68,
    "LGS": 47.23,
    "LMN": 47.67,
    "IHR": 47.68,
}

S_OUT = "Flow-Out.Ave.1Hour.1Hour.CBT-REV"
S_SPILL = "Flow-Spill.Ave.1Hour.1Hour.CBT-REV"
S_GEN = "Flow-Gen.Ave.1Hour.1Hour.CBT-REV"
S_FB = "Elev-Forebay.Inst.1Hour.0.CBT-REV"
S_PWR = "Power.Total.1Hour.1Hour.CBT-RAW"

ACRE_FT_PER_KCFS_H = 82.6446  # 1 kcfs·h = 3.6e6 ft³ = 82.6446 acre-ft
MAX_LAG_H = 72
TRAIN_YEARS = (2023, 2024)
CHECK_YEAR = 2025
R_MIN = 0.30
CELERITY_MPH = (1.0, 30.0)
FED_ROR_BAND_FT = (0.5, 15.0)
SIDE_INFLOW_FLOOR_MAX_FRAC = 0.02
# Sentinel / invalid-value screens, applied before any statistic (reported in
# the monthly artifact as ``hours_invalid``): CROHMS carries -99999 in two
# Power series and isolated 0.0 forebay readings hundreds of feet below pool.
SENTINEL_MIN = -9000.0


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_hourly() -> dict[str, pd.DataFrame]:
    """Return ``{station: wide frame indexed by hourly ts with one column per series}``."""
    raw = pd.read_parquet(HOURLY_PATH)
    raw = raw[raw["quality"] == 0]
    full = pd.date_range("2023-01-01", "2026-01-01", freq="h")
    out: dict[str, pd.DataFrame] = {}
    for st, grp in raw.groupby("station"):
        wide = grp.pivot(index="ts", columns="series", values="value").reindex(full)
        wide.columns.name = None
        # Sentinels -> NaN; forebay readings far below pool (0.0 spikes) -> NaN.
        wide = wide.mask(wide <= SENTINEL_MIN)
        if S_FB in wide:
            med = wide[S_FB].median()
            wide[S_FB] = wide[S_FB].mask(wide[S_FB] < 0.5 * med)
        for s in (S_OUT, S_SPILL, S_GEN):
            if s in wide:
                wide[s] = wide[s].mask(wide[s] < 0.0)
        out[st] = wide
    return out


def load_catalog_coords() -> dict[str, tuple[float, float]]:
    cat = json.loads(CATALOG_PATH.read_text())
    return {
        st: (float(v["coordinates"]["latitude"]), float(v["coordinates"]["longitude"]))
        for st, v in cat.items()
        if st in STATIONS
    }


def load_nid(nid_national: Path | None) -> pd.DataFrame:
    """Return the NID rows for the chain dams (verbatim columns), regenerating from the national CSV when given."""
    if nid_national is None:
        return pd.read_csv(OUT_NID, dtype=str)
    want = {v["nid"] for v in STATIONS.values()}
    csv.field_size_limit(10**9)
    rows: list[dict] = []
    with open(nid_national, newline="", encoding="utf-8", errors="replace") as f:
        header_note = next(f).strip()
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("NID ID") in want and "Levee" not in (row.get("Dam Name") or ""):
                rows.append(row)
    df = pd.DataFrame(rows)
    keep = [
        "Dam Name",
        "NID ID",
        "State",
        "River or Stream Name",
        "Owner Names",
        "Primary Purpose",
        "Purposes",
        "Year Completed",
        "NID Height (Ft)",
        "Hydraulic Height (Ft)",
        "Max Storage (Acre-Ft)",
        "Normal Storage (Acre-Ft)",
        "Surface Area (Acres)",
        "Drainage Area (Sq Miles)",
        "Latitude",
        "Longitude",
    ]
    df = df[keep].copy()
    df.insert(
        0, "station", df["NID ID"].map({v["nid"]: k for k, v in STATIONS.items()})
    )
    df["nid_source_note"] = header_note
    df = df.sort_values("station").reset_index(drop=True)
    df.to_csv(OUT_NID, index=False)
    logger.info("wrote %s (%d rows; %s)", OUT_NID, len(df), header_note)
    return df.astype(str)


def load_budget_923() -> dict[tuple[int, int], np.ndarray | None]:
    """``{(plant_id, year): (12,) EIA-923 monthly MWh or None when NO_923_SERIES}``."""
    b = pd.read_parquet(BUDGET_PATH)
    out: dict[tuple[int, int], np.ndarray | None] = {}
    mcols = [f"m{m:02d}" for m in range(1, 13)]
    for _, r in b.iterrows():
        key = (int(r["plant_id"]), int(r["year"]))
        if str(r["status"]) == "NO_923_SERIES" or not bool(r["loader_kept"]):
            out[key] = None
        else:
            out[key] = np.asarray([float(r[c]) for c in mcols])
    return out


# --------------------------------------------------------------------------- #
# §4.1 τ by anomaly cross-correlation
# --------------------------------------------------------------------------- #
def _anomaly(x: pd.Series) -> pd.Series:
    return x - x.rolling(25, center=True, min_periods=13).mean()


def _corr_at_lag(a_u: np.ndarray, a_d: np.ndarray, lag: int) -> float:
    """Pearson r of ``a_u(t−lag)`` against ``a_d(t)`` over jointly finite hours."""
    if lag > 0:
        u = a_u[:-lag]
        d = a_d[lag:]
    else:
        u, d = a_u, a_d
    ok = np.isfinite(u) & np.isfinite(d)
    if ok.sum() < 1000:
        return float("nan")
    u = u[ok]
    d = d[ok]
    return float(np.corrcoef(u, d)[0, 1])


def _lag_curve(a_u: np.ndarray, a_d: np.ndarray) -> np.ndarray:
    return np.asarray([_corr_at_lag(a_u, a_d, L) for L in range(MAX_LAG_H + 1)])


def _joint_lag_grid(a_u1: np.ndarray, a_u2: np.ndarray, a_d: np.ndarray) -> np.ndarray:
    """(73, 73) r of ``a_u1(t−L1) + a_u2(t−L2)`` against ``a_d(t)`` (McNary's two inflows)."""
    n = a_d.size
    grid = np.full((MAX_LAG_H + 1, MAX_LAG_H + 1), np.nan)
    for L1 in range(MAX_LAG_H + 1):
        s1 = np.full(n, np.nan)
        s1[L1:] = a_u1[: n - L1]
        for L2 in range(MAX_LAG_H + 1):
            s2 = np.full(n, np.nan)
            s2[L2:] = a_u2[: n - L2]
            u = s1 + s2
            ok = np.isfinite(u) & np.isfinite(a_d)
            if ok.sum() < 1000:
                continue
            grid[L1, L2] = np.corrcoef(u[ok], a_d[ok])[0, 1]
    return grid


def _peak(curve: np.ndarray) -> tuple[int, float, bool]:
    """``(τ, r(τ), unique)``; plateaus break toward the SHORTER lag (argmax picks the first)."""
    if not np.isfinite(curve).any():
        return -1, float("nan"), False
    tau = int(np.nanargmax(curve))
    r = float(curve[tau])
    neigh = [curve[i] for i in (tau - 1, tau + 1) if 0 <= i <= MAX_LAG_H]
    unique = all(np.isfinite(v) and r - v > 0 for v in neigh)
    return tau, r, unique


def _great_circle_mi(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 3958.7613 * 2 * math.asin(math.sqrt(h))


def measure_tau(
    hourly: dict[str, pd.DataFrame], coords: dict[str, tuple[float, float]]
) -> pd.DataFrame:
    """Per link: τ, the r-table, per-year τ, distance and celerity, and the §4.1 verdict."""
    anom = {st: _anomaly(df[S_OUT]) for st, df in hourly.items()}
    years = {y: (anom["GCL"].index.year == y) for y in TRAIN_YEARS + (CHECK_YEAR,)}
    train = years[2023] | years[2024]
    rows: list[dict] = []
    # McNary's two inflows are searched jointly; everything else pairwise.
    mcn_grid = _joint_lag_grid(
        anom["PRD"].values[train], anom["IHR"].values[train], anom["MCN"].values[train]
    )
    mcn_tau = np.unravel_index(int(np.nanargmax(mcn_grid)), mcn_grid.shape)
    for link, u, d in LINKS:
        rec: dict = dict(
            link=link,
            u_station=u,
            d_station=d,
            u_plant_id=STATIONS[u]["plant_id"],
            d_plant_id=STATIONS[d]["plant_id"],
        )
        if d == "MCN":
            L1, L2 = int(mcn_tau[0]), int(mcn_tau[1])
            tau = L1 if u == "PRD" else L2
            r_tau = float(mcn_grid[L1, L2])
            # 1-D slices through the joint optimum for the r(τ±1) / r(0) columns.
            sl = mcn_grid[:, L2] if u == "PRD" else mcn_grid[L1, :]
            unique = all(
                np.isfinite(sl[i]) and r_tau - sl[i] > 0
                for i in (tau - 1, tau + 1)
                if 0 <= i <= MAX_LAG_H
            )
            r_m1 = float(sl[tau - 1]) if tau >= 1 else float("nan")
            r_p1 = float(sl[tau + 1]) if tau + 1 <= MAX_LAG_H else float("nan")
            r_0 = float(sl[0])
            per_year: dict[int, tuple[int, float]] = {}
            for y in TRAIN_YEARS + (CHECK_YEAR,):
                g = _joint_lag_grid(
                    anom["PRD"].values[years[y]],
                    anom["IHR"].values[years[y]],
                    anom["MCN"].values[years[y]],
                )
                ij = np.unravel_index(int(np.nanargmax(g)), g.shape)
                per_year[y] = (int(ij[0] if u == "PRD" else ij[1]), float(g[ij]))
            rec["search"] = "joint-2D (PRD,IHR)->MCN"
        else:
            curve = _lag_curve(anom[u].values[train], anom[d].values[train])
            tau, r_tau, unique = _peak(curve)
            r_m1 = float(curve[tau - 1]) if tau >= 1 else float("nan")
            r_p1 = float(curve[tau + 1]) if tau + 1 <= MAX_LAG_H else float("nan")
            r_0 = float(curve[0])
            per_year = {}
            for y in TRAIN_YEARS + (CHECK_YEAR,):
                c_y = _lag_curve(anom[u].values[years[y]], anom[d].values[years[y]])
                t_y, r_y, _ = _peak(c_y)
                per_year[y] = (t_y, r_y)
            rec["search"] = "pairwise 1-D"
        dist = _great_circle_mi(coords[u], coords[d])
        celerity = dist / tau if tau >= 1 else float("nan")
        rec.update(
            tau_h=tau,
            r_tau=round(r_tau, 4),
            r_tau_minus1=round(r_m1, 4) if np.isfinite(r_m1) else np.nan,
            r_tau_plus1=round(r_p1, 4) if np.isfinite(r_p1) else np.nan,
            r_lag0=round(r_0, 4),
            peak_unique=bool(unique),
            tau_2023=per_year[2023][0],
            r_2023=round(per_year[2023][1], 4),
            tau_2024=per_year[2024][0],
            r_2024=round(per_year[2024][1], 4),
            tau_2025=per_year[CHECK_YEAR][0],
            r_2025=round(per_year[CHECK_YEAR][1], 4),
            distance_mi=round(dist, 2),
            celerity_mph=round(celerity, 2) if np.isfinite(celerity) else np.nan,
        )
        fails: list[str] = []
        if not (r_tau >= R_MIN):
            fails.append(f"r({tau})={r_tau:.3f}<{R_MIN}")
        if not unique:
            fails.append("peak not unique (plateau, broken toward shorter lag)")
        if abs(per_year[2023][0] - per_year[2024][0]) > 1:
            fails.append(
                f"2023 tau {per_year[2023][0]} vs 2024 tau {per_year[2024][0]} differ >1h"
            )
        stop = False
        if tau >= 1 and not (CELERITY_MPH[0] <= celerity <= CELERITY_MPH[1]):
            fails.append(f"celerity {celerity:.1f} mph outside {CELERITY_MPH}")
            stop = True
        rec["tau_accepted"] = not fails
        rec["tau_stop"] = stop
        rec["tau_reason"] = "; ".join(fails) if fails else "accepted"
        rows.append(rec)
    df = pd.DataFrame(rows)
    # (iii) cumulative τ monotone in cumulative distance down the mainstem.
    cum = df[
        df["d_station"].isin(MAINSTEM_ORDER) & df["u_station"].isin(MAINSTEM_ORDER)
    ].sort_values("link")
    cum_tau = cum["tau_h"].cumsum().values
    cum_dist = cum["distance_mi"].cumsum().values
    monotone = bool(np.all(np.diff(cum_tau) >= 0) and np.all(np.diff(cum_dist) > 0))
    df["mainstem_cum_tau_monotone"] = monotone
    if not monotone:
        logger.warning(
            "cumulative mainstem tau is NOT monotone in distance: %s",
            list(zip(cum_dist, cum_tau)),
        )
    return df


# --------------------------------------------------------------------------- #
# §4.2 pondage band
# --------------------------------------------------------------------------- #
def measure_band(hourly: dict[str, pd.DataFrame], nid: pd.DataFrame) -> pd.DataFrame:
    nid_by_st = nid.set_index("station")
    rows: list[dict] = []
    for st, meta in STATIONS.items():
        fb = hourly[st][S_FB]
        area = float(nid_by_st.loc[st, "Surface Area (Acres)"])
        max_st = pd.to_numeric(
            nid_by_st.loc[st, "Max Storage (Acre-Ft)"], errors="coerce"
        )
        norm_st = pd.to_numeric(
            nid_by_st.loc[st, "Normal Storage (Acre-Ft)"], errors="coerce"
        )
        nid_band_ft = (
            (max_st - norm_st) / area
            if np.isfinite(max_st) and np.isfinite(norm_st) and area > 0
            else np.nan
        )
        bands: dict[int, float] = {}
        for y in TRAIN_YEARS:
            s = fb[fb.index.year == y].dropna()
            bands[y] = (
                float(s.quantile(0.995) - s.quantile(0.005))
                if len(s) > 1000
                else float("nan")
            )
        used_year = min(
            TRAIN_YEARS, key=lambda y: bands[y] if np.isfinite(bands[y]) else np.inf
        )
        band_ft = bands[used_year]
        daily_range = (
            fb[fb.index.year.isin(TRAIN_YEARS)]
            .groupby(pd.Grouper(freq="D"))
            .agg(lambda s: s.max() - s.min())
        )
        p99_daily = (
            float(daily_range.dropna().quantile(0.99))
            if daily_range.notna().any()
            else float("nan")
        )
        pond_kcfsh = band_ft * area / ACRE_FT_PER_KCFS_H
        q_pub = PUBLISHED_AVG_DISCHARGE_KCFS[st]
        q_meas = float(hourly[st][S_OUT].mean())
        stop = False
        reason = "measured"
        if not np.isfinite(band_ft):
            stop, reason = True, "no usable forebay series"
        elif meta["federal_ror"] and not (
            FED_ROR_BAND_FT[0] <= band_ft <= FED_ROR_BAND_FT[1]
        ):
            stop, reason = (
                True,
                f"federal run-of-river band {band_ft:.2f} ft outside {FED_ROR_BAND_FT}",
            )
        rows.append(
            dict(
                station=st,
                plant_id=meta["plant_id"],
                role=meta["role"],
                federal_ror=meta["federal_ror"],
                nid_id=meta["nid"],
                area_acres=area,
                nid_max_minus_normal_ft=round(nid_band_ft, 2)
                if np.isfinite(nid_band_ft)
                else np.nan,
                band_ft_2023=round(bands[2023], 3),
                band_ft_2024=round(bands[2024], 3),
                band_year_used=used_year,
                band_ft=round(band_ft, 3) if np.isfinite(band_ft) else np.nan,
                within_day_range_p99_ft=round(p99_daily, 3)
                if np.isfinite(p99_daily)
                else np.nan,
                pond_kcfsh=round(pond_kcfsh, 2) if np.isfinite(pond_kcfsh) else np.nan,
                pond_hours_of_published_avg_discharge=(
                    round(pond_kcfsh / q_pub, 2)
                    if (q_pub and np.isfinite(pond_kcfsh))
                    else np.nan
                ),
                pond_hours_of_measured_avg_outflow=round(pond_kcfsh / q_meas, 2)
                if np.isfinite(pond_kcfsh)
                else np.nan,
                measured_avg_outflow_kcfs=round(q_meas, 2),
                band_stop=stop,
                band_reason=reason,
            )
        )
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# §4.3 η and §4.4 side inflow / head flows, per plant-month
# --------------------------------------------------------------------------- #
def measure_monthly(
    hourly: dict[str, pd.DataFrame],
    budget: dict[tuple[int, int], np.ndarray | None],
    links: pd.DataFrame,
    band: pd.DataFrame,
) -> pd.DataFrame:
    area = band.set_index("station")["area_acres"].to_dict()
    tau_by_link = {int(r.link): int(r.tau_h) for r in links.itertuples()}
    up_of: dict[str, list[tuple[str, int]]] = {}
    for r in links.itertuples():
        up_of.setdefault(r.d_station, []).append(
            (r.u_station, tau_by_link[int(r.link)])
        )

    rows: list[dict] = []
    for st, meta in STATIONS.items():
        df = hourly[st]
        pid = meta["plant_id"]
        # Pond change from the forebay series (kcfs·h per hour), for the side
        # inflow balance: a month that drew its pond down is not booked as inflow.
        dV = df[S_FB].diff() * area[st] / ACRE_FT_PER_KCFS_H
        # Lagged upstream outflow sum (kcfs) at this plant.
        arriving = None
        if st in up_of:
            arriving = sum(hourly[u][S_OUT].shift(tau) for u, tau in up_of[st])
        for y in (2023, 2024, 2025):
            e923 = budget.get((pid, y))
            e_src_year = y
            if e923 is None:
                # Nearest year with a series, same month (PRECOMMIT §4.3).
                for alt in sorted((2023, 2024, 2025), key=lambda a: abs(a - y)):
                    if budget.get((pid, alt)) is not None:
                        e923, e_src_year = budget[(pid, alt)], alt
                        break
            for m in range(1, 13):
                sel = (df.index.year == y) & (df.index.month == m)
                sub = df[sel]
                hours = int(sel.sum())
                gen_ok = sub[S_GEN].notna()
                gen_sum = float(sub[S_GEN].sum())
                # Scale the turbine-flow sum to the full month when hours are
                # missing (stated, not hidden): η is a ratio of two monthly
                # totals and the missing hours are ≤ 140 in three years.
                scale = hours / max(int(gen_ok.sum()), 1)
                gen_sum_full = gen_sum * scale
                e_m = float(e923[m - 1]) if e923 is not None else float("nan")
                eta = (
                    e_m / gen_sum_full
                    if gen_sum_full > 0 and np.isfinite(e_m) and e_m > 0
                    else float("nan")
                )
                pwr = sub[S_PWR]
                both = pwr.notna() & gen_ok & (sub[S_GEN] > 0)
                eta_gross = (
                    float(pwr[both].sum() / sub[S_GEN][both].sum())
                    if both.any()
                    else float("nan")
                )
                out_mean = float(sub[S_OUT].mean())
                spill_mean = float(sub[S_SPILL].mean())
                rec = dict(
                    station=st,
                    plant_id=pid,
                    year=y,
                    month=m,
                    hours_in_month=hours,
                    hours_missing_gen=int(hours - gen_ok.sum()),
                    e923_mwh=round(e_m, 1) if np.isfinite(e_m) else np.nan,
                    eta_source_year=e_src_year,
                    gen_flow_kcfsh=round(gen_sum_full, 1),
                    eta_mwh_per_kcfsh=round(eta, 4) if np.isfinite(eta) else np.nan,
                    eta_gross_crohms=round(eta_gross, 4)
                    if np.isfinite(eta_gross)
                    else np.nan,
                    eta_net_over_gross=round(eta / eta_gross, 4)
                    if np.isfinite(eta) and np.isfinite(eta_gross) and eta_gross > 0
                    else np.nan,
                    outflow_mean_kcfs=round(out_mean, 3),
                    spill_mean_kcfs=round(spill_mean, 3),
                )
                if arriving is not None:
                    arr = arriving[sel]
                    bal = sub[S_OUT] + dV[sel] - arr
                    ok = bal.notna()
                    i_raw = float(bal[ok].mean()) if ok.any() else float("nan")
                    arr_mean = float(arr[ok].mean()) if ok.any() else float("nan")
                    floor = max(0.0, -i_raw) if np.isfinite(i_raw) else float("nan")
                    stop = bool(
                        np.isfinite(floor)
                        and arr_mean > 0
                        and floor > SIDE_INFLOW_FLOOR_MAX_FRAC * arr_mean
                    )
                    rec.update(
                        arriving_mean_kcfs=round(arr_mean, 3),
                        side_inflow_raw_kcfs=round(i_raw, 3),
                        side_inflow_kcfs=round(max(i_raw, 0.0), 3)
                        if np.isfinite(i_raw)
                        else np.nan,
                        side_inflow_floor_kcfs=round(floor, 3),
                        side_inflow_stop=stop,
                        hours_balance=int(ok.sum()),
                    )
                else:
                    rec.update(
                        arriving_mean_kcfs=np.nan,
                        side_inflow_raw_kcfs=np.nan,
                        side_inflow_kcfs=np.nan,
                        side_inflow_floor_kcfs=np.nan,
                        side_inflow_stop=False,
                        hours_balance=0,
                    )
                rows.append(rec)
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument(
        "--nid-national",
        default=None,
        help="NID national CSV to regenerate the committed NID rows from",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    hourly = load_hourly()
    coords = load_catalog_coords()
    nid = load_nid(Path(args.nid_national) if args.nid_national else None)
    budget = load_budget_923()

    links = measure_tau(hourly, coords)
    band = measure_band(hourly, nid)
    monthly = measure_monthly(hourly, budget, links, band)

    # Coupling verdict per link: τ accepted AND the downstream band measurable AND
    # no side-inflow STOP on any of its plant-months. Hells Canyon is absent by
    # construction (daily-only on CROHMS; PRECOMMIT §2) and never appears here.
    band_by_st = band.set_index("station")
    stop_months = (
        monthly[monthly["side_inflow_stop"]].groupby("station").size().to_dict()
    )
    coupled: list[bool] = []
    reasons: list[str] = []
    for r in links.itertuples():
        why: list[str] = []
        if not r.tau_accepted:
            why.append(f"tau: {r.tau_reason}")
        if bool(band_by_st.loc[r.d_station, "band_stop"]):
            why.append(f"band: {band_by_st.loc[r.d_station, 'band_reason']}")
        if r.d_station in stop_months:
            why.append(
                f"side inflow floor >{SIDE_INFLOW_FLOOR_MAX_FRAC:.0%} of arriving water in {stop_months[r.d_station]} plant-months"
            )
        coupled.append(not why)
        reasons.append("; ".join(why) if why else "coupled")
    links["coupled"] = coupled
    links["reason"] = reasons
    links = links.merge(
        band[
            [
                "station",
                "federal_ror",
                "nid_id",
                "area_acres",
                "nid_max_minus_normal_ft",
                "band_ft_2023",
                "band_ft_2024",
                "band_year_used",
                "band_ft",
                "within_day_range_p99_ft",
                "pond_kcfsh",
                "pond_hours_of_published_avg_discharge",
                "pond_hours_of_measured_avg_outflow",
                "measured_avg_outflow_kcfs",
                "band_stop",
                "band_reason",
            ]
        ].rename(columns={"station": "d_station"}),
        on="d_station",
        how="left",
    )
    links.to_csv(OUT_LINKS, index=False)
    monthly.to_csv(OUT_MONTHLY, index=False)
    logger.info(
        "wrote %s (%d links, %d coupled) and %s (%d plant-months)",
        OUT_LINKS,
        len(links),
        int(links["coupled"].sum()),
        OUT_MONTHLY,
        len(monthly),
    )
    pd.set_option("display.width", 250)
    print(
        links[
            [
                "link",
                "u_station",
                "d_station",
                "tau_h",
                "r_tau",
                "r_lag0",
                "tau_2023",
                "tau_2024",
                "tau_2025",
                "distance_mi",
                "celerity_mph",
                "band_ft",
                "pond_kcfsh",
                "pond_hours_of_measured_avg_outflow",
                "coupled",
                "reason",
            ]
        ].to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
