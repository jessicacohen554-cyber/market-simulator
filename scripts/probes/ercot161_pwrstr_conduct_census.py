"""ERCOT-161 Phase 0 addendum 3 — the PWRSTR (storage) offer-conduct census, 2023.

The price-setter census attributed the top-100 gap hours' $500-3,000 price
formation to PWRSTR — the resource type BOTH offer walls exclude by scope and
whose 2023 conduct no prior session has measured (ERCOT-154's identification
ran on the 2024/2025 sample-day extracts; the full delivery-2023 corpus landed
at ERCOT-157, after its probes ran). This census measures the 2023 storage
conduct with ERCOT-154's own population discipline:

* ONTEST split reported explicitly (ERCOT-154 excluded it; the addendum-2
  headline used a bare ``ON*`` filter — this census quantifies the difference);
* above-LSL discharge segments capped at HASL (the energy headroom the
  telemetered AS stack leaves to energy — ERCOT-154's rule-19 boundary);
* segment prices in ABSOLUTE $/MWh (ERCOT-154 refuted the gas-multiple basis
  for storage: a battery has no heat rate);
* conditioned on three hour sets: the top-100 gap hours, the remaining bin-6
  hours (the discrimination contrast — reality cleared $76 p50 there), and the
  whole year (per net-load bin, the wall geometry's own edges).

NO LP, no solve. Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot161_pwrstr_conduct_census.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DEFAULT_OUT = REPO / "results/calibration/_ercot161_pwrstr_conduct.json"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
YEAR = 2023

#: Absolute-$ quantiles of the discharge-offer ladder (MW-weighted).
QUANTS = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99)

#: $/MWh rungs for the offered-MW census.
USD_RUNGS = (100.0, 300.0, 500.0, 1000.0, 2000.0, 4000.0)


def _ladder(sub: pd.DataFrame) -> dict:
    """MW-weighted absolute-$ quantiles + rung census for one hour set."""
    from derive_ercot_sced_offer_wall import _weighted_quantiles

    if sub.empty:
        return {}
    price = sub["price"].to_numpy(float)
    mw = sub["mw"].to_numpy(float)
    qs = _weighted_quantiles(price, mw, QUANTS)
    per_iv = sub.groupby("ts")["mw"].sum()
    rungs = {
        f"gw_ge_{int(r)}": round(
            float(
                sub[sub["price"] >= r]
                .groupby("ts")["mw"]
                .sum()
                .reindex(per_iv.index)
                .fillna(0.0)
                .mean()
                / 1e3
            ),
            3,
        )
        for r in USD_RUNGS
    }
    return {
        "usd_quantiles": {
            f"p{int(q * 100)}": round(float(v), 1) for q, v in zip(QUANTS, qs)
        },
        "n_intervals": int(sub["ts"].nunique()),
        "n_hours": int(sub["hoy"].nunique()),
        "mean_offered_gw": round(float(per_iv.mean() / 1e3), 3),
        "mean_gw_at_usd_rungs": rungs,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR, _netload_pct
    from derive_ercot_sced_offer_wall import (
        _NUMERIC_COLS,
        _SCED2_MW,
        _SCED2_PR,
        NETLOAD_PCT_EDGES,
        _delivery_year_rows,
        _sced_source_files,
    )

    read_cols = [
        "SCED Time Stamp",
        "Resource Type",
        "Telemetered Resource Status",
        "HASL",
        "Base Point",
        "LSL",
    ] + [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]

    phase0 = json.loads(PHASE0_JSON.read_text())
    top = set(int(h) for h in phase0["hour_set"]["hours"])
    pct = _netload_pct(YEAR)
    eb = np.searchsorted(np.asarray(NETLOAD_PCT_EDGES), pct, side="right")
    bin6_rest = set(int(h) for h in np.where(eb == 6)[0]) - top

    seg_acc: list[pd.DataFrame] = []
    status_mw: dict[str, float] = {}
    n_files = 0
    for path in _sced_source_files(YEAR):
        df = pd.read_parquet(path, columns=read_cols)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"] == "PWRSTR"]
        n_files += 1
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON")].copy()
        df["status"] = stat[stat.str.startswith("ON")]
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert("Etc/GMT+6")
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        df = df.loc[np.asarray(ok)].copy()
        if df.empty:
            continue
        df["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        cols = [c for c in _NUMERIC_COLS if c in df.columns]
        df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

        MW = df[_SCED2_MW].to_numpy(float)
        PR = df[_SCED2_PR].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        hasl = df["HASL"].to_numpy(float)
        hoy = df["hoy"].to_numpy(int)
        tskey = df["SCED Time Stamp"].to_numpy()
        status = df["status"].to_numpy()

        seg = {k: [] for k in ("hoy", "mw", "price", "ts", "status")}
        prev = lsl.copy()
        for k in range(MW.shape[1]):
            q = MW[:, k]
            p = PR[:, k]
            valid = np.isfinite(q) & np.isfinite(p)
            cap = np.minimum(q, hasl)
            mw = np.where(valid, np.maximum(cap - np.maximum(prev, lsl), 0.0), 0.0)
            take = mw > 0
            if take.any():
                seg["hoy"].append(hoy[take])
                seg["mw"].append(mw[take])
                seg["price"].append(p[take])
                seg["ts"].append(tskey[take])
                seg["status"].append(status[take])
            prev = np.where(valid, np.maximum(prev, q), prev)
        if seg["mw"]:
            sdf = pd.DataFrame({k: np.concatenate(v) for k, v in seg.items()})
            for st_name, grp in sdf.groupby("status"):
                status_mw[st_name] = status_mw.get(st_name, 0.0) + float(
                    grp["mw"].sum()
                )
            seg_acc.append(sdf)

    seg = pd.concat(seg_acc, ignore_index=True)
    seg_clean = seg[seg["status"] != "ONTEST"]

    hour_bin = eb  # derive-geometry bins on the shared edges
    year_by_bin = {}
    for b in range(7):
        hrs = set(int(h) for h in np.where(hour_bin == b)[0])
        year_by_bin[f"bin{b}"] = _ladder(seg_clean[seg_clean["hoy"].isin(hrs)])

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot161_pwrstr_conduct_census.py",
            "session": "ercot-161 Phase 0 addendum 3 (no LP, no solve)",
            "population": (
                "PWRSTR above-LSL discharge segments capped at HASL, ONTEST "
                "excluded (the ERCOT-154 population discipline), absolute "
                "$/MWh (the gas-multiple basis is refuted for storage)"
            ),
            "n_files_read": n_files,
        },
        "status_mw_share": {
            k: round(v / sum(status_mw.values()), 4)
            for k, v in sorted(status_mw.items(), key=lambda kv: -kv[1])
        },
        "gap_hours": _ladder(seg_clean[seg_clean["hoy"].isin(top)]),
        "gap_hours_incl_ontest": _ladder(seg[seg["hoy"].isin(top)]),
        "bin6_rest": _ladder(seg_clean[seg_clean["hoy"].isin(bin6_rest)]),
        "year_by_netload_bin": year_by_bin,
    }
    args.out.write_text(json.dumps(out, indent=1))
    print("status MW share:", out["status_mw_share"])
    print("gap hours (ONTEST excluded):", json.dumps(out["gap_hours"], indent=1))
    print("bin6 rest:", json.dumps(out["bin6_rest"], indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
