"""ERCOT-74 leg-1 measured adjudication: what priced the missed RT tail hours?

Reads the scoped 60-Day SCED disclosure intake
(``data/raw/ercot/60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_*.parquet``,
NP3-965-ER — the telemetered RT energy offer curves SCED actually ran on) and,
for each target hour, measures the ONLINE fleet's remaining sub-threshold
supply at the printing intervals:

* ``sub200_hasl`` — MW offered at <= threshold between each online resource's
  Base Point and HASL (its AS-carved sustainable limit), summed over the
  fleet: the headroom an HOURLY market model sees. ~Exhausted => the online
  offer stack itself priced the hour ("offer-formed") — an hourly
  offer-surface mechanism is the admissible build.
* ``sub200_hdl`` — the same capped at HDL (the 5-minute ramp-feasible
  dispatch limit): the headroom SCED could actually reach that interval.
  ``sub200_hdl ~ 0`` while ``sub200_hasl`` is large => the print was
  RAMP-formed (sub-hourly dispatch-limit scarcity an hourly LP cannot see) —
  ledger evidence, NOT a mechanism lane.

The classification thresholds and the decision rule were PRE-REGISTERED in
the session scratchpad before any curve was read (ERCOT-74 leg-1
pre-registration): offer-formed if median ``sub200_hasl`` < 500 MW;
ramp-formed if ``sub200_hasl`` >= 500 while median ``sub200_hdl`` < 500;
mixed otherwise. 500 MW is ~one peaker block — well inside the several-GW
granularity of the fleet stack; a diagnostic cutoff, not a solve tunable.

Timestamps: the parquet keeps the disclosure's raw CPT stamps; they are
converted CPT->CST here via ``build_ercot_hsl._prevailing_to_standard`` (the
NP6-905 convention) before hour matching, so target hours are model-clock CST.

Usage::

    python scripts/probes/_ercot74_sced_headroom.py \
        --parquet data/raw/ercot/60_DAY_SCED_DISCLOSURE_..._tail_days.parquet \
        --hours 2024-04-03T18 2024-05-08T15 ... [--threshold 200] [--sced2]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
# Statuses counting as synchronized/online supply in SCED (Gen + ESR).
# OFF/OFFNS/OUT/EMR etc. are excluded: their curves are not online supply.
_ONLINE_PREFIXES = ("ON",)

# Pre-registered classification cutoff (~one peaker block; see module docstring).
_EXHAUSTED_MW = 500.0


def _load(parquet: Path, sced2: bool) -> pd.DataFrame:
    fam = "SCED2" if sced2 else "SCED1"
    pair_cols = []
    for i in range(1, 36):
        pair_cols += [f"{fam} Curve-MW{i}", f"{fam} Curve-Price{i}"]
    cols = [
        "SCED Time Stamp",
        "Repeated Hour Flag",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "Base Point",
        "HASL",
        "HDL",
    ] + pair_cols
    df = pd.read_parquet(parquet, columns=cols)
    from build_ercot_hsl import _prevailing_to_standard

    ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    df["ts_cst"] = _prevailing_to_standard(
        ts, df["Repeated Hour Flag"].fillna("N").astype(str).str.upper().eq("Y")
    )
    return df


def _mw_at_or_below(df: pd.DataFrame, fam: str, threshold: float) -> np.ndarray:
    """Per row: the largest curve MW whose price is <= threshold (0 if none).

    Conservative staircase reading of the (MW_i, Price_i) points — no
    interpolation across the crossing segment; classification-insensitive at
    the fleet's multi-GW scale.
    """
    mw = df[[f"{fam} Curve-MW{i}" for i in range(1, 36)]].to_numpy(dtype=float)
    pr = df[[f"{fam} Curve-Price{i}" for i in range(1, 36)]].to_numpy(dtype=float)
    ok = np.isfinite(mw) & np.isfinite(pr) & (pr <= threshold)
    return np.where(ok, mw, 0.0).max(axis=1)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parquet", required=True)
    ap.add_argument(
        "--hours",
        nargs="+",
        required=True,
        help="target hours as YYYY-MM-DDTHH (CST, model clock)",
    )
    ap.add_argument("--threshold", type=float, default=200.0)
    ap.add_argument(
        "--sced2", action="store_true", help="use the SCED2 curve family instead"
    )
    args = ap.parse_args()

    fam = "SCED2" if args.sced2 else "SCED1"
    df = _load(Path(args.parquet), args.sced2)
    online = df["Telemetered Resource Status"].astype(str).str.upper()
    df = df[online.str.startswith(_ONLINE_PREFIXES)].copy()
    df["mw_at_thr"] = _mw_at_or_below(df, fam, args.threshold)
    bp = df["Base Point"].to_numpy(dtype=float)
    df["sub_hasl"] = np.clip(
        np.minimum(df["mw_at_thr"], df["HASL"].to_numpy(dtype=float)) - bp, 0.0, None
    )
    df["sub_hdl"] = np.clip(
        np.minimum(df["mw_at_thr"], df["HDL"].to_numpy(dtype=float)) - bp, 0.0, None
    )

    print(
        f"{'hour (CST)':>14} {'ivals':>5} {'onlineGW':>8} "
        f"{'sub{thr}_hdl MW (med/min)':>26} {'sub{thr}_hasl MW (med/min)':>27} "
        f"{'verdict':>12}".replace("{thr}", f"{args.threshold:.0f}")
    )
    for spec in args.hours:
        day, hh = spec.split("T")
        t0 = pd.Timestamp(f"{day} {int(hh):02d}:00")
        m = (df["ts_cst"] >= t0) & (df["ts_cst"] < t0 + pd.Timedelta(hours=1))
        sub = df[m]
        if not len(sub):
            print(f"{spec:>14}  -- no intervals in the intake (check hod window) --")
            continue
        g = sub.groupby("ts_cst").agg(
            online_mw=("HASL", "sum"),
            sub_hasl=("sub_hasl", "sum"),
            sub_hdl=("sub_hdl", "sum"),
        )
        med_hasl, min_hasl = g["sub_hasl"].median(), g["sub_hasl"].min()
        med_hdl, min_hdl = g["sub_hdl"].median(), g["sub_hdl"].min()
        if med_hasl < _EXHAUSTED_MW:
            verdict = "offer-formed"
        elif med_hdl < _EXHAUSTED_MW:
            verdict = "ramp-formed"
        else:
            verdict = "mixed"
        print(
            f"{spec:>14} {len(g):>5} {g['online_mw'].mean() / 1e3:>8.1f} "
            f"{med_hdl:>13,.0f}/{min_hdl:>9,.0f} "
            f"{med_hasl:>14,.0f}/{min_hasl:>9,.0f} {verdict:>12}"
        )


if __name__ == "__main__":
    main()
