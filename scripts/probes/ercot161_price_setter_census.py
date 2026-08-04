"""ERCOT-161 Phase 0 addendum 2 — WHICH resource type set lambda at the gap hours.

The dispatched-segment census (``ercot161_dispatched_segment_census.py``)
refuted the merchant-gas premise: at the top-100 gap hours the ON-status
merchant CC/CT SCED2 curves carried only ~0.12 GW priced >= $500 across
dispatched AND spare, while ERCOT's system lambda averaged $1,470. The
$500-3,000 price formation therefore lives in a resource population the RT
wall's scope (CCGT90/CCLE90/SCGT90/SCLE90) never samples. This census
attributes it: per gap-hour interval, across ALL resource types in the
delivery-2023 corpus, the ABOVE-LSL dispatched SCED2 segments whose price
falls in the lambda-neighbourhood band [0.7, 1.3] x lambda(hour) — the
price-setting band — summed by Resource Type, plus each type's dispatched and
offered (LSL -> HASL) MW at >= $500 / $1,000.

NO LP, no solve. Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot161_price_setter_census.py
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

DEFAULT_OUT = REPO / "results/calibration/_ercot161_price_setter.json"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
YEAR = 2023

#: Lambda-neighbourhood band (fractions of the hour's system lambda) treated
#: as "price-setting" for the attribution.
BAND = (0.7, 1.3)

#: Renewable/other types with no meaningful incremental offer curve — reported
#: but expected ~0 in the band.
ALL_TYPES_NOTE = "every Resource Type in the corpus is included; none excluded"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--min-lambda",
        type=float,
        default=300.0,
        help="restrict the attribution to gap hours with lambda >= this",
    )
    args = ap.parse_args()

    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR
    from derive_ercot_sced_offer_wall import (
        _NUMERIC_COLS,
        _READ_COLS,
        _delivery_year_rows,
        _sced_source_files,
    )

    read_cols = [c for c in _READ_COLS if c != "Resource Type"] + [
        "Resource Type",
        "LSL",
    ]

    phase0 = json.loads(PHASE0_JSON.read_text())
    top = sorted(int(h) for h in phase0["hour_set"]["hours"])
    lam = (
        pd.read_parquet(
            REPO / f"data/raw/ercot/ercot_{YEAR}_ordc_reserves_hourly.parquet"
        )
        .set_index("hour")["system_lambda"]
        .reindex(range(8760))
        .to_numpy(float)
    )
    hours = [h for h in top if np.isfinite(lam[h]) and lam[h] >= args.min_lambda]
    keep = set(hours)

    from derive_ercot_sced_offer_wall import _SCED2_MW, _SCED2_PR

    band_mw: dict[str, float] = {}
    ge500_disp: dict[str, float] = {}
    ge500_off: dict[str, float] = {}
    ge1000_disp: dict[str, float] = {}
    n_iv_seen: set = set()
    n_files = 0
    for path in _sced_source_files(YEAR):
        df = pd.read_parquet(path, columns=read_cols)
        df = _delivery_year_rows(df, YEAR)
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.str.startswith("ON")].copy()
        n_files += 1
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
        df = df[df["hoy"].isin(keep)]
        if df.empty:
            continue
        cols = [c for c in _NUMERIC_COLS if c in df.columns]
        df[cols] = df[cols].apply(pd.to_numeric, errors="coerce")

        MW = df[_SCED2_MW].to_numpy(float)
        PR = df[_SCED2_PR].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        bp = df["Base Point"].to_numpy(float)
        hasl = df["HASL"].to_numpy(float)
        hoy = df["hoy"].to_numpy(int)
        rtype = df["Resource Type"].astype(str).to_numpy()
        lam_h = lam[hoy]
        n_iv_seen.update(df["SCED Time Stamp"].tolist())

        prev = lsl.copy()
        for k in range(MW.shape[1]):
            q = MW[:, k]
            p = PR[:, k]
            valid = np.isfinite(q) & np.isfinite(p)
            lo = np.maximum(prev, lsl)
            d_mw = np.where(valid, np.maximum(np.minimum(q, bp) - lo, 0.0), 0.0)
            o_mw = np.where(valid, np.maximum(np.minimum(q, hasl) - lo, 0.0), 0.0)
            in_band = valid & (p >= BAND[0] * lam_h) & (p <= BAND[1] * lam_h)
            for t in np.unique(rtype[(d_mw > 0) | (o_mw > 0)]):
                sel = rtype == t
                band_mw[t] = band_mw.get(t, 0.0) + float(d_mw[sel & in_band].sum())
                ge500_disp[t] = ge500_disp.get(t, 0.0) + float(
                    d_mw[sel & valid & (p >= 500)].sum()
                )
                ge1000_disp[t] = ge1000_disp.get(t, 0.0) + float(
                    d_mw[sel & valid & (p >= 1000)].sum()
                )
                ge500_off[t] = ge500_off.get(t, 0.0) + float(
                    o_mw[sel & valid & (p >= 500)].sum()
                )
            prev = np.where(valid, np.maximum(prev, q), prev)

    n_iv = max(len(n_iv_seen), 1)

    def _gw(d: dict[str, float]) -> dict[str, float]:
        return {
            t: round(v / n_iv / 1e3, 3)
            for t, v in sorted(d.items(), key=lambda kv: -kv[1])
            if v / n_iv / 1e3 >= 0.0005
        }

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot161_price_setter_census.py",
            "session": "ercot-161 Phase 0 addendum 2 (no LP, no solve)",
            "population": ALL_TYPES_NOTE,
            "band": list(BAND),
            "min_lambda": args.min_lambda,
            "n_gap_hours_used": len(hours),
            "n_intervals": n_iv,
            "n_files_read": n_files,
        },
        "mean_gw_dispatched_in_lambda_band_by_type": _gw(band_mw),
        "mean_gw_dispatched_ge500_by_type": _gw(ge500_disp),
        "mean_gw_dispatched_ge1000_by_type": _gw(ge1000_disp),
        "mean_gw_offered_ge500_by_type": _gw(ge500_off),
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(f"gap hours with lambda >= {args.min_lambda}: {len(hours)}; intervals {n_iv}")
    print("dispatched MW in [0.7,1.3]xlambda band, mean GW by type:")
    print(" ", out["mean_gw_dispatched_in_lambda_band_by_type"])
    print("dispatched >= $500 by type:", out["mean_gw_dispatched_ge500_by_type"])
    print("dispatched >= $1000 by type:", out["mean_gw_dispatched_ge1000_by_type"])
    print("offered >= $500 by type:", out["mean_gw_offered_ge500_by_type"])
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
