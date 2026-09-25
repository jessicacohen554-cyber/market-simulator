#!/usr/bin/env python3
"""miso-273 phase 0 (zero LP): the short-screened coal WEFOR relief on the MISO keeper recipe.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the designated keeper
(``results/calibration/miso272b_span``) via the miso-271 decomposition helpers:

* ``B``   — the keeper recipe;
* ``ARM`` — ``wefor_residual_short_screened_coal=True`` (the one field);
* ``noWc`` — statistical WEFOR relieved on ALL coal (the upper bound; W on coal);
* ``noSc`` — short-coal windows off (the short family's own removal).

Identification (the frozen caiso-187 formula, rule 23; miso-271 applied it to gas):
per year, over the SCREENED coal capacity only,

    W_s = sum_bins s_b x (avail_noWc_b - avail_B_b)     (the statistical term)
    X_s = sum over screened unit-years of the measured window MWh
          (>= 5-day unitroute + < 5-day short + maxgen), overlap-clipped to the year
    residual_s = max(0, W_s - X_s) / (screened MW x 8760)

``residual_s == 0`` in every year means the measured record already removes at
least what the statistical term claims on those units, so relief to the
keeper's ``wefor_residual = 0.0`` is identified, not tuned.

Usage::

    uv run python scripts/probes/_miso273_screened_phase0.py --out results/calibration/_miso273_screened_phase0.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(Path(__file__).resolve().parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

import pandas as pd  # noqa: E402

import _miso271_cc_decomp as dec  # noqa: E402

dec.KEEPER = REPO / "results/calibration/miso272b_span"
COAL = ["COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"]
VARIANTS = {
    "B": {},
    "ARM": {"wefor_residual_short_screened_coal": True},
    "noWc": {
        "wefor_residual": 0.0,
        "wefor_residual_groups": ["CC_REGULAR", "ST_CHP", "ST_GAS", *COAL],
    },
    "noSc": {"unit_outage_short_windows": False},
}
RAW = REPO / "data/raw"
SCREENED = RAW / "campd-unit-outages-short-screened-MISO.csv"
WINDOWS = {
    "ge5d": (RAW / "campd-unit-outages-unitroute-MISO.csv", "outage_start", "outage_end", "unit_capacity_mw", True),
    "short": (RAW / "campd-unit-outages-short-MISO.csv", "outage_start", "outage_end", "unit_capacity_mw", True),
    "maxgen": (RAW / "campd-unit-outages-maxgen-unitroute-MISO.csv", "window_start", "window_end", "derate_mw", False),
}


def _unit_window_mwh(year: int, keys: set) -> dict[str, float]:
    """Measured window MWh on the screened (facility, unit) set, clipped to ``year``."""
    y0, y1 = pd.Timestamp(f"{year}-01-01"), pd.Timestamp(f"{year + 1}-01-01")
    out = {}
    for name, (path, s, e, mw, incl) in WINDOWS.items():
        df = pd.read_csv(path)
        uid_col = "unit_id" if "unit_id" in df.columns else None
        if uid_col is None:
            out[name] = float("nan")
            continue
        m = [(int(f), str(u)) in keys for f, u in zip(df["facility_id"], df[uid_col])]
        df = df[m]
        st = pd.to_datetime(df[s])
        en = pd.to_datetime(df[e]) + (pd.Timedelta(days=1) if incl else pd.Timedelta(0))
        hrs = (en.clip(upper=y1) - st.clip(lower=y0)).dt.total_seconds().clip(lower=0) / 3600.0
        out[name] = float((hrs * df[mw]).sum())
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames-dir", default=None)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.outages import short_screened_coal_shares

    ref = _load_reference()
    scr = pd.read_csv(SCREENED)
    res: dict[str, dict] = {}
    for y in args.years:
        hh = _henry_hub_actual(ref, y)
        fr = {v: dec.unit_frame(y, hh, VARIANTS[v])[0] for v in VARIANTS}
        if args.frames_dir:
            Path(args.frames_dir).mkdir(parents=True, exist_ok=True)
            for v, df in fr.items():
                df.to_parquet(Path(args.frames_dir) / f"{y}_{v}.parquet", index=False)
        b = fr["B"]
        coal_b = b[b.group.isin(COAL)]
        roster = (
            coal_b.assign(k=coal_b.plant_code.astype(int))
            .groupby("k")["pmax"]
            .sum()
        )
        shares = short_screened_coal_shares(
            y, "MISO", tuple(sorted(((int(k), "COAL"), float(v)) for k, v in roster.items()))
        )

        def by_plant(df):
            d = df[df.group.isin(COAL)]
            return d.groupby(d.plant_code.astype(int))["avail_mwh"].sum()

        wb = by_plant(b)
        W_s = sum(s * (by_plant(fr["noWc"]).get(k[0], 0.0) - wb.get(k[0], 0.0)) for k, s in shares.items())
        scr_mw_lp = sum(s * roster.get(k[0], 0.0) for k, s in shares.items())
        keys = {(int(f), str(u)) for f, u, yy in zip(scr.facility_id, scr.unit_id, scr.year) if yy == y}
        X = _unit_window_mwh(y, keys)
        X_s = sum(v for v in X.values() if v == v)
        cap_h = scr_mw_lp * 8760.0
        per_class = {}
        for v in VARIANTS:
            d = fr[v]
            per_class[v] = {
                c: round(float(d.loc[d.group == c, "avail_mwh"].sum()) / 1e6, 4) for c in COAL
            }
        arm_minus_b = {c: round(per_class["ARM"][c] - per_class["B"][c], 4) for c in COAL}
        other = b[~b.group.isin(COAL)].set_index("unit_id")["avail_mwh"]
        other_arm = fr["ARM"][~fr["ARM"].group.isin(COAL)].set_index("unit_id")["avail_mwh"]
        res[str(y)] = {
            "screened_unit_years": int(len(keys)),
            "screened_extract_mw": round(float(scr.loc[scr.year == y, "unit_capacity_mw"].sum()), 1),
            "coal_bins_with_share": len(shares),
            "coal_lp_mw": round(float(roster.sum()), 1),
            "screened_lp_mw": round(scr_mw_lp, 1),
            "W_screened_twh": round(W_s / 1e6, 4),
            "X_screened_twh": {k: round(v / 1e6, 4) for k, v in X.items()},
            "residual_share": round(max(0.0, W_s - X_s) / cap_h, 5) if cap_h else None,
            "W_share": round(W_s / cap_h, 5) if cap_h else None,
            "X_share": round(X_s / cap_h, 5) if cap_h else None,
            "avail_twh_by_variant": per_class,
            "arm_minus_B_twh": arm_minus_b,
            "noWc_minus_B_twh": {c: round(per_class["noWc"][c] - per_class["B"][c], 4) for c in COAL},
            "non_coal_units_moved": int((other_arm.reindex(other.index) - other).abs().gt(1e-6).sum()),
            "pmax_identical": bool((fr["ARM"]["pmax"].values == b["pmax"].values).all()),
            "heat_rate_identical": bool((fr["ARM"]["heat_rate"].values == b["heat_rate"].values).all()),
        }
        print(json.dumps({y: res[str(y)]}), flush=True)
    Path(args.out).write_text(json.dumps(res, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
