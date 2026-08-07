"""caiso-181 ROUTE 1 — same-hour CEMS confrontation of the CAISO outage envelope.

Pre-registered in ``results/calibration/PRECHECK-caiso181-envelope-depth-2026-08-07.md``
(pushed and blob-verified, sha256 ``1c8e91f8...``, BEFORE any metric here was read).

**The question.** caiso-180 kept the regenerated outage envelope under rule 14
``[R-ACCURATE]`` and filed its +1.1 / +1.6 pp C3a cost as an OPEN ROOT-CAUSE issue.
This probe asks whether that envelope's *depth* (36.68 / 42.88 / 55.43 M outage MW-h)
is **CORRECT**, or whether the model asserts unavailability the units' **own CEMS
record contradicts**.

**Why the test is decisive.** It is a pure INTERNAL-CONSISTENCY test of the detector
against its OWN source — the same ``data/raw/campd-unit-level/CA_*.parquet`` the
windows were derived from. It is therefore immune to the NEISO definitional seam
(charter §9: published = *unavailability*, the CEMS detector = *non-operation*): a hit
here is a **construction error**, not a definitional difference. No LP, no new intake,
no DOF.

**The contract being audited.** 100 % of CAISO's committed envelope is produced by
:func:`scripts.lib.outage_detect.detect_outages_eventbased` (the deriver branches on the
unit's own fuel and CAMPD's CAISO population carries zero coal). That detector's
contract is exact: *"a maximal run of consecutive hours whose CF stays strictly below
``cf_peak`` for every hour"*, ``cf_peak = ST_GAS_CF_PEAK = 0.02``. **Zero in-window
hours at CF >= 0.02 are admissible by construction.**

Two measurements, per PRECHECK §3:

* **L1 (gating)** — unit-grain: per committed window, the share of in-window hours the
  unit's own CEMS shows generating, and the MW-hours the envelope zeroes that CEMS says
  ran. Split ``edge`` (first/last calendar day of the window — the H-EDGE day-granular
  seam) vs ``interior``, and by window-duration quartile.
* **L2 (magnitude)** — envelope-grain "impossible MW", the direct port of ercot-172's
  ``f_ceiling`` vs ``f_CEMS``: hours where the shipped loader's availability multiplier
  sits BELOW the fraction of the bin's capacity CEMS shows it produced.

Instruments are **REUSED, never re-implemented**: the deriver's own
``build_capacity_index`` / ``unit_capacity_mw`` (the detector's CF basis),
``campd.CAMPD_UNIT_PLANT_REMAP``, and for L2 the shipped
``outages.unit_outage_derate_factors`` and ``outages._generic_unit_outage_target`` /
``outages._iso_plant_capacity``.

Usage::

    uv run python scripts/probes/_caiso181_cems_confrontation.py

Writes ``results/calibration/_caiso181_cems_confrontation.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import EIA_860_DIR, RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    HOURS_PER_YEAR,
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _hour_of_year,
    _iso_plant_capacity,
    unit_outage_csv_for_iso,
    unit_outage_derate_factors,
)
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    build_capacity_index,
    unit_capacity_mw,
)
from scripts.lib.outage_detect import REAL_RUN_CF, ST_GAS_CF_PEAK  # noqa: E402

ISO = "CAISO"
STATE = "CA"
YEARS = (2023, 2024, 2025)
UNIT_DIR = RAW_DATA_DIR / "campd-unit-level"
OUT = REPO / "results" / "calibration" / "_caiso181_cems_confrontation.json"

# Committed envelope depth per year, measured at caiso-180 from the same blob
# (results/calibration/_caiso180_outage_reaudit.json). The B-2 denominator.
CAISO180_DEPTH_MWH: dict[int, float] = {
    2023: 36.68e6,
    2024: 42.88e6,
    2025: 55.43e6,
}

# PRECHECK §4 bars, fixed before measurement.
B1_INTERIOR_SHARE_BAR = 0.005  # 0.5 % of interior in-window hours at CF >= 0.02
B2_DEPTH_SHARE_BAR = 0.05  # impossible MW-h >= 5 % of committed depth
B3_EDGE_DOMINANCE_BAR = 0.70  # >= 70 % of contradicted MW-h on first/last day


def _year_grids(year: int) -> tuple[dict[tuple[int, str], np.ndarray], pd.DatetimeIndex]:
    """Return ``{(facility_id, unit_id): hourly gross}`` on the CAMPD year clock.

    NaN is PRESERVED (distinct from 0): CAMPD omits non-operating hours and the
    detector zero-fills them, but for the confrontation a missing/NaN hour is NOT a
    contradiction — only a *reported positive gross* counts. That convention can only
    under-count contradictions, never manufacture one (PRECHECK §3a).

    ``facility_id`` carries :data:`campd.CAMPD_UNIT_PLANT_REMAP` applied exactly as the
    deriver applies it, so the join to the committed CSV is on the same key.
    """
    df = pd.read_parquet(
        UNIT_DIR / f"{STATE}_{year}.parquet",
        columns=["facilityId", "unitId", "date", "hour", "grossLoad"],
    )
    df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
    df = df.dropna(subset=["facilityId"])
    df["facilityId"] = df["facilityId"].astype(int)
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = pd.to_numeric(df["hour"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["hour"])
    df["grossLoad"] = pd.to_numeric(df["grossLoad"], errors="coerce")
    # Same CEMS->EIA split-plant remap the deriver applies before grouping.
    df["facilityId"] = [
        campd.CAMPD_UNIT_PLANT_REMAP.get((f, u), f)
        for f, u in zip(df["facilityId"].astype(int), df["unitId"].astype(str))
    ]
    clock = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    grids: dict[tuple[int, str], np.ndarray] = {}
    ts = df["date"] + pd.to_timedelta(df["hour"].astype(int), unit="h")
    df = df.assign(_ts=ts)
    for (fac, uid), sub in df.groupby(["facilityId", "unitId"], observed=True):
        s = sub.set_index("_ts")["grossLoad"]
        # min_count=1 keeps an all-NaN hour NaN instead of collapsing it to 0.0.
        s = s.groupby(level=0).sum(min_count=1).sort_index()
        grids[(int(fac), str(uid))] = s.reindex(clock).to_numpy(dtype=float)
    return grids, clock


def _pctl(a: list[float] | np.ndarray, q: float) -> float:
    arr = np.asarray(a, dtype=float)
    return float(np.percentile(arr, q)) if arr.size else 0.0


def run_l1(year: int, windows: pd.DataFrame, grids, caps) -> dict:
    """L1 — per-window unit-grain confrontation against the unit's own CEMS."""
    clock_len = len(
        pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    )
    base = pd.Timestamp(f"{year}-01-01")
    per_window: list[dict] = []
    unmatched: list[dict] = []
    for r in windows.itertuples(index=False):
        key = (int(r.facility_id), str(r.unit_id))
        gross = grids.get(key)
        if gross is None:
            unmatched.append(
                {
                    "facility_id": int(r.facility_id),
                    "unit_id": str(r.unit_id),
                    "facility_name": str(r.facility_name),
                    "capacity_source": str(r.capacity_source),
                    "duration_days": float(r.duration_days),
                }
            )
            continue
        # The LOADER's own reconstruction: outage_start 00:00 -> outage_end 23:00
        # inclusive (outages.py _unit_outage_factors_from_events passes
        # outage_end + 1 day as the half-open stop), clipped to the year.
        lo = max(0, int((r.outage_start - base).total_seconds() // 3600))
        hi = min(
            clock_len,
            int(
                (r.outage_end + pd.Timedelta(days=1) - base).total_seconds() // 3600
            ),
        )
        if hi <= lo:
            continue
        span = gross[lo:hi]
        n = hi - lo
        detect_mw = caps.get(key, (0.0, 0.0, "none"))[0]
        cf = span / detect_mw if detect_mw > 0 else np.zeros_like(span)
        reported = ~np.isnan(span)
        running = reported & (np.nan_to_num(span) > 0.0)
        above_contract = reported & (np.nan_to_num(cf) >= ST_GAS_CF_PEAK)
        above_realrun = reported & (np.nan_to_num(cf) >= REAL_RUN_CF)
        mwh = float(np.nansum(np.where(running, span, 0.0)))
        # EDGE = the window's first or last CALENDAR day (the H-EDGE day-granular
        # seam, PRECHECK §2c(2)); INTERIOR = strictly inside.
        edge = np.zeros(n, dtype=bool)
        edge[: min(24, n)] = True
        edge[max(0, n - 24) :] = True
        interior = ~edge
        # Distance of each contradicted hour from the NEAREST window boundary —
        # the sharp H-EDGE signature (PRECHECK §4c).
        idx = np.arange(n)
        dist = np.minimum(idx, n - 1 - idx)
        per_window.append(
            {
                "facility_id": int(r.facility_id),
                "unit_id": str(r.unit_id),
                "facility_name": str(r.facility_name),
                "plant_group": str(r.plant_group),
                "capacity_source": str(r.capacity_source),
                "duration_days": float(r.duration_days),
                "detect_mw": float(detect_mw),
                "n_hours": int(n),
                "n_edge": int(edge.sum()),
                "n_interior": int(interior.sum()),
                "n_reported": int(reported.sum()),
                "n_running": int(running.sum()),
                "n_above_contract": int(above_contract.sum()),
                "n_above_realrun": int(above_realrun.sum()),
                "n_above_contract_edge": int((above_contract & edge).sum()),
                "n_above_contract_interior": int((above_contract & interior).sum()),
                "cems_mwh": mwh,
                "cems_mwh_edge": float(np.nansum(np.where(running & edge, span, 0.0))),
                "cems_mwh_interior": float(
                    np.nansum(np.where(running & interior, span, 0.0))
                ),
                "contradiction_dists": [
                    int(d) for d in dist[above_contract]
                ],
            }
        )

    df = pd.DataFrame(per_window)
    if df.empty:
        return {"n_windows": 0, "unmatched": unmatched}

    tot_h = int(df["n_hours"].sum())
    tot_int = int(df["n_interior"].sum())
    tot_edge = int(df["n_edge"].sum())
    int_above = int(df["n_above_contract_interior"].sum())
    edge_above = int(df["n_above_contract_edge"].sum())
    mwh_edge = float(df["cems_mwh_edge"].sum())
    mwh_int = float(df["cems_mwh_interior"].sum())
    mwh_tot = mwh_edge + mwh_int

    # Per-window share distribution (the charter's "distribution, not just a mean").
    shares = (df["n_above_contract"] / df["n_hours"]).to_numpy(dtype=float)
    # Duration quartiles (caiso-180's shape prediction: any residual concentrates
    # in the LONGEST windows).
    q = df["duration_days"].quantile([0.25, 0.5, 0.75]).to_list()
    bins = [-np.inf] + q + [np.inf]
    df["_dq"] = pd.cut(df["duration_days"], bins=bins, labels=["Q1", "Q2", "Q3", "Q4"])
    by_q = {}
    for label, sub in df.groupby("_dq", observed=True):
        by_q[str(label)] = {
            "n_windows": int(len(sub)),
            "duration_days_range": [
                float(sub["duration_days"].min()),
                float(sub["duration_days"].max()),
            ],
            "n_hours": int(sub["n_hours"].sum()),
            "n_above_contract": int(sub["n_above_contract"].sum()),
            "share_above_contract": (
                float(sub["n_above_contract"].sum() / sub["n_hours"].sum())
                if sub["n_hours"].sum()
                else 0.0
            ),
            "cems_mwh": float(sub["cems_mwh"].sum()),
        }

    by_src = {}
    for label, sub in df.groupby("capacity_source", observed=True):
        by_src[str(label)] = {
            "n_windows": int(len(sub)),
            "n_hours": int(sub["n_hours"].sum()),
            "n_above_contract": int(sub["n_above_contract"].sum()),
            "cems_mwh": float(sub["cems_mwh"].sum()),
        }

    dists = [d for w in per_window for d in w["contradiction_dists"]]
    worst = df.nlargest(10, "cems_mwh")[
        [
            "facility_id",
            "facility_name",
            "unit_id",
            "plant_group",
            "duration_days",
            "detect_mw",
            "n_hours",
            "n_above_contract",
            "cems_mwh",
            "cems_mwh_edge",
        ]
    ].to_dict("records")

    return {
        "n_windows": int(len(df)),
        "n_unmatched": len(unmatched),
        "unmatched": unmatched[:20],
        "total_in_window_hours": tot_h,
        "total_interior_hours": tot_int,
        "total_edge_hours": tot_edge,
        "n_reported": int(df["n_reported"].sum()),
        "n_running": int(df["n_running"].sum()),
        "n_above_contract": int(df["n_above_contract"].sum()),
        "n_above_realrun": int(df["n_above_realrun"].sum()),
        "share_reported_running": float(df["n_running"].sum() / tot_h) if tot_h else 0.0,
        "share_above_contract": (
            float(df["n_above_contract"].sum() / tot_h) if tot_h else 0.0
        ),
        "share_above_realrun": (
            float(df["n_above_realrun"].sum() / tot_h) if tot_h else 0.0
        ),
        # B-1: the GATING quantity.
        "interior_share_above_contract": (
            float(int_above / tot_int) if tot_int else 0.0
        ),
        "edge_share_above_contract": float(edge_above / tot_edge) if tot_edge else 0.0,
        "n_above_contract_interior": int_above,
        "n_above_contract_edge": edge_above,
        "cems_mwh_total": mwh_tot,
        "cems_mwh_edge": mwh_edge,
        "cems_mwh_interior": mwh_int,
        "edge_share_of_contradicted_mwh": (
            float(mwh_edge / mwh_tot) if mwh_tot else 0.0
        ),
        "per_window_share_distribution": {
            "p50": _pctl(shares, 50),
            "p90": _pctl(shares, 90),
            "p99": _pctl(shares, 99),
            "max": float(shares.max()) if shares.size else 0.0,
            "n_windows_share_gt_0": int((shares > 0).sum()),
            "n_windows_share_gt_0p05": int((shares > 0.05).sum()),
        },
        "contradiction_distance_from_boundary": {
            "n": len(dists),
            "p50": _pctl(dists, 50),
            "p90": _pctl(dists, 90),
            "max": float(max(dists)) if dists else 0.0,
            "share_within_24h": (
                float(sum(1 for d in dists if d < 24) / len(dists)) if dists else 0.0
            ),
        },
        "by_duration_quartile": by_q,
        "by_capacity_source": by_src,
        "worst_10_windows_by_cems_mwh": worst,
    }


def run_l2(year: int, grids) -> dict:
    """L2 — envelope-grain "impossible MW" (the ercot-172 f_ceiling vs f_CEMS port).

    ``f_model`` comes from the SHIPPED loader. CEMS is placed on the model's fixed
    8760-hour clock with :func:`outages._hour_of_year` — the identical non-leap mapping
    the loader uses for the window dates — so both sides sit on one clock and any
    local-standard-time offset affects them identically and cancels.
    """
    factors = unit_outage_derate_factors(year, hours=HOURS_PER_YEAR, iso=ISO)
    cap = _iso_plant_capacity(ISO)
    if not factors:
        return {"n_bins": 0}

    clock = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00:00", freq="h")
    hoy = np.array(
        [_hour_of_year(t.month, t.day, t.hour) for t in clock], dtype=int
    )
    # Feb 29 has no counterpart on the model's 8760 clock (the loader drops it);
    # excluded from BOTH sides and reported so the omission is visible.
    is_feb29 = np.array([(t.month == 2 and t.day == 29) for t in clock])

    # Aggregate each bin's CEMS gross onto the model clock.
    bin_cems: dict[tuple[int, str], np.ndarray] = {}
    feb29_mwh = 0.0
    csv = pd.read_csv(unit_outage_csv_for_iso(ISO))
    group_by_unit = {
        (int(r.facility_id), str(r.unit_id)): str(r.plant_group)
        for r in csv.itertuples(index=False)
    }
    for (fac, uid), gross in grids.items():
        group = group_by_unit.get((fac, uid))
        if group is None:
            continue
        tgt = _generic_unit_outage_target(fac, uid, group)
        if tgt is None or tgt not in cap or tgt not in factors:
            continue
        g = np.nan_to_num(gross)
        feb29_mwh += float(g[is_feb29].sum())
        arr = bin_cems.setdefault(tgt, np.zeros(HOURS_PER_YEAR))
        keep = ~is_feb29
        np.add.at(arr, hoy[keep], g[keep])

    # Per-bin EDGE-DAY mask on the model clock: the first / last calendar day of
    # every window routed to that bin (the H-EDGE day-granular seam), so L2's
    # excess can be attributed to the same seam L1 measures at unit grain.
    edge_mask: dict[tuple[int, str], np.ndarray] = {}
    wdf = pd.read_csv(
        unit_outage_csv_for_iso(ISO), parse_dates=["outage_start", "outage_end"]
    )
    wdf = wdf[
        (wdf["duration_days"] >= UNIT_OUTAGE_MIN_DAYS)
        & (wdf["outage_start"].dt.year == year)
    ]
    for r in wdf.itertuples(index=False):
        tgt = _generic_unit_outage_target(
            int(r.facility_id), r.unit_id, r.plant_group
        )
        if tgt is None or tgt not in cap:
            continue
        lo = _hour_of_year(r.outage_start.month, r.outage_start.day, 0)
        stop = r.outage_end + pd.Timedelta(days=1)
        hi = (
            HOURS_PER_YEAR
            if stop.year > year
            else _hour_of_year(stop.month, stop.day, stop.hour)
        )
        lo, hi = max(0, min(lo, HOURS_PER_YEAR)), max(0, min(hi, HOURS_PER_YEAR))
        if hi <= lo:
            continue
        m = edge_mask.setdefault(tgt, np.zeros(HOURS_PER_YEAR, dtype=bool))
        m[lo : min(lo + 24, hi)] = True
        m[max(lo, hi - 24) : hi] = True

    rows = []
    tot_imp_mwh = 0.0
    tot_imp_hours = 0
    # Exact decomposition of the excess (f_cems - f_model)+ into two disjoint
    # parts (identity: (f_cems - f_model)+ == (f_cems - 1)+ + (min(f_cems,1) - f_model)+
    # whenever f_model <= 1):
    #   BASIS  = the part of CEMS gross above the bin's ENTIRE EIA-860 nameplate.
    #            No availability envelope can represent it — a gross-vs-nameplate
    #            capacity-basis mismatch, NOT an outage-envelope defect.
    #   ENVELOPE = the part inside [0, 1] where the envelope derates below
    #            demonstrated output. This is the envelope-attributable excess,
    #            further split edge-day vs interior-day.
    basis_mwh = 0.0
    env_mwh = 0.0
    env_edge_mwh = 0.0
    env_int_mwh = 0.0
    for tgt, cems in bin_cems.items():
        pcap = cap[tgt]
        f_model = factors[tgt]
        f_cems = cems / pcap if pcap > 0 else np.zeros_like(cems)
        impossible = f_cems > f_model
        imp_mw = np.where(impossible, (f_cems - f_model) * pcap, 0.0)
        imp_mwh = float(imp_mw.sum())
        tot_imp_mwh += imp_mwh
        tot_imp_hours += int(impossible.sum())
        b_mw = np.clip(f_cems - 1.0, 0.0, None) * pcap
        e_mw = np.clip(np.minimum(f_cems, 1.0) - f_model, 0.0, None) * pcap
        em = edge_mask.get(tgt, np.zeros(HOURS_PER_YEAR, dtype=bool))
        basis_mwh += float(b_mw.sum())
        env_mwh += float(e_mw.sum())
        env_edge_mwh += float(e_mw[em].sum())
        env_int_mwh += float(e_mw[~em].sum())
        if imp_mwh > 0:
            rows.append(
                {
                    "plant_code": tgt[0],
                    "plant_group": tgt[1],
                    "plant_cap_mw": float(pcap),
                    "impossible_hours": int(impossible.sum()),
                    "impossible_mwh": imp_mwh,
                    "basis_excess_mwh": float(b_mw.sum()),
                    "envelope_excess_mwh": float(e_mw.sum()),
                    "envelope_excess_edge_mwh": float(e_mw[em].sum()),
                    "max_impossible_mw": float(imp_mw.max()),
                    "min_f_model_when_impossible": (
                        float(f_model[impossible].min()) if impossible.any() else 1.0
                    ),
                    "max_f_cems_when_impossible": (
                        float(f_cems[impossible].max()) if impossible.any() else 0.0
                    ),
                }
            )
    rows.sort(key=lambda d: -d["impossible_mwh"])
    depth = CAISO180_DEPTH_MWH[year]
    return {
        "n_bins_with_factors": len(factors),
        "n_bins_confronted": len(bin_cems),
        "impossible_bin_hours": tot_imp_hours,
        "impossible_mwh": tot_imp_mwh,
        "committed_depth_mwh": depth,
        # B-2 as pre-registered: the RAW impossible share (conservative — it
        # includes the basis-mismatch component that no envelope could fix).
        "impossible_share_of_depth": tot_imp_mwh / depth if depth else 0.0,
        # The honest decomposition (reported alongside, never instead).
        "basis_excess_mwh": basis_mwh,
        "envelope_excess_mwh": env_mwh,
        "envelope_excess_edge_mwh": env_edge_mwh,
        "envelope_excess_interior_mwh": env_int_mwh,
        "envelope_excess_share_of_depth": env_mwh / depth if depth else 0.0,
        "envelope_excess_edge_share": (
            env_edge_mwh / env_mwh if env_mwh else 0.0
        ),
        "feb29_cems_mwh_excluded": feb29_mwh,
        "worst_10_bins": rows[:10],
    }


def main() -> None:
    eia860 = EIA_860_DIR / "eia860_generators.parquet"
    exact, by_digits = build_capacity_index(eia860)
    csv_path = unit_outage_csv_for_iso(ISO)
    allw = pd.read_csv(csv_path, parse_dates=["outage_start", "outage_end"])
    # The loader's own filter: only >= UNIT_OUTAGE_MIN_DAYS windows reach the LP.
    allw = allw[allw["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]

    out: dict = {
        "session": "caiso-181",
        "precheck": "results/calibration/PRECHECK-caiso181-envelope-depth-2026-08-07.md",
        "envelope_csv": str(csv_path.relative_to(REPO)),
        "detector_contract": {
            "rule": "detect_outages_eventbased",
            "cf_peak": ST_GAS_CF_PEAK,
            "real_run_cf": REAL_RUN_CF,
            "admissible_in_window_hours_above_cf_peak": 0,
        },
        "bars": {
            "B1_interior_share_above_contract": B1_INTERIOR_SHARE_BAR,
            "B2_impossible_share_of_depth": B2_DEPTH_SHARE_BAR,
            "B3_edge_dominance": B3_EDGE_DOMINANCE_BAR,
        },
        "years": {},
    }

    for year in YEARS:
        grids, _ = _year_grids(year)
        # Per-unit detect_mw on the detector's OWN basis (the deriver's function,
        # observed-peak fallback taken from the same zero-filled grid it uses).
        caps = {
            key: unit_capacity_mw(
                key[0], key[1], exact, by_digits, float(np.nan_to_num(g).max())
            )
            for key, g in grids.items()
        }
        w = allw[allw["outage_start"].dt.year == year]
        l1 = run_l1(year, w, grids, caps)
        l2 = run_l2(year, grids)
        b1 = l1.get("interior_share_above_contract", 0.0) > B1_INTERIOR_SHARE_BAR
        b2 = l2.get("impossible_share_of_depth", 0.0) >= B2_DEPTH_SHARE_BAR
        out["years"][str(year)] = {
            "L1": l1,
            "L2": l2,
            "B1_fires": bool(b1),
            "B2_fires": bool(b2),
            "B3_edge_dominated": bool(
                l1.get("edge_share_of_contradicted_mwh", 0.0)
                >= B3_EDGE_DOMINANCE_BAR
            ),
        }
        print(
            f"{year}: windows={l1.get('n_windows')} "
            f"share_above_contract={l1.get('share_above_contract'):.6f} "
            f"INTERIOR={l1.get('interior_share_above_contract'):.6f} "
            f"(B1 {'FIRES' if b1 else 'clear'}) | "
            f"cems_mwh={l1.get('cems_mwh_total'):,.0f} "
            f"edge_share={l1.get('edge_share_of_contradicted_mwh'):.3f} | "
            f"L2 impossible={l2.get('impossible_mwh', 0):,.0f} MWh = "
            f"{l2.get('impossible_share_of_depth', 0):.4%} of depth "
            f"(B2 {'FIRES' if b2 else 'clear'})"
        )

    out["verdict"] = {
        "B1_any_year": any(v["B1_fires"] for v in out["years"].values()),
        "B2_any_year": any(v["B2_fires"] for v in out["years"].values()),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
