"""ERCOT-75 leg-0/1 decisive measurement: what actually priced the offer-formed core?

Rule-16 diagnostic (no solve). Measures, from the 60-Day SCED disclosure
intake parquets, the ONLINE merchant-gas fleet's REMAINING-ROOM price ladder —
the MW-weighted price quantiles of the SCED1 curve segments between each
online resource's operating point (max(Base Point, Telemetered Net Output),
the ERCOT-74 IRR-safe convention) and its HASL (the AS-carved sustainable
limit) — at named hours and per (netload bin x loaded w-state) cell,
tail-days vs control-days.

WHY THIS MEASUREMENT CLOSED THE LANE (2026-07-16 session; full adjudication in
the ERCOT-75 calibration-log entry). At the six offer-formed 2024 core hours
(May-8 h15-17, Apr-28 h20, Aug-7 h18, Aug-19 h19):

* the online CC fleet's room is 0.04-0.26 GW priced $12-75 (CHEAP — its
  measured curve tops and room prices carry no event level; the CC phenomenon
  is room QUANTITY, i.e. availability, not price);
* the online CT fleet's room is 0.01-0.36 GW priced $881-5,000 — the measured
  carrier of the $965+ prints (system lambda formed on the CT marginal-room
  tail);
* in loaded (w <= 1/3) cells at large, CC room is ~0.5-1.2 GW at the SAME
  cheap prices on tail and control days alike — the core hours are the
  event-only extreme tail of the loaded state, and the control sample has
  ZERO CT-loaded support in bins 1-3 (the state that priced the events occurs
  only on event days);
* w_CT at May-8 h15-17 reads 1.00/0.85/0.78 — the CT headroom there was
  AS-held (HASL-carved), not energy room, so a (1-w_CT)-conditioned CT
  correction would not even engage at three of the six core hours.

Together with the gate probe's inertness measurement (the RT per-hour
curve-top quantile ladder sits BELOW the DAM mode-B ladder at every
sub-threshold rung), this closes the chartered price-side correction from
both sides: what passes the selection gate is inert, and what carries the
level is event-confounded (and quantity-, not price-, shaped — the
quantity-side projection, capping model availability at the measured online
envelope, is the rule-14 actuals-pin family).

Usage::

    python scripts/probes/_ercot75_room_ladder.py \
        [--hours 2024-05-08T15 2024-05-08T16 ...] [--cells] [--sced2]
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from build_ercot_hsl import _prevailing_to_standard  # noqa: E402
from derive_dam_offer_hrmults import HCAP_USD_MWH, NETLOAD_PCT_EDGES  # noqa: E402
from derive_ercot_dam_cleared_share import _netload_pct  # noqa: E402

from _ercot75_control_gate import (  # noqa: E402
    CLASS_OF_RESTYPE,
    DEFAULT_CONTROL,
    DEFAULT_TAIL,
    STATE_JSON,
    _hoy_nonleap,
)

# The ERCOT-74 offer-formed 2024 core (model-clock CST hours).
CORE_HOURS = (
    "2024-05-08T15",
    "2024-05-08T16",
    "2024-05-08T17",
    "2024-04-28T20",
    "2024-08-07T18",
    "2024-08-19T19",
)

ROOM_QS = (0.10, 0.30, 0.50, 0.70, 0.90)


def _load(parquets: list[Path], fam: str) -> pd.DataFrame:
    """Interval-grain online CC/CT rows with curves, telemetry and cell keys."""
    import json

    pr_cols = [f"{fam} Curve-Price{i}" for i in range(1, 36)]
    mw_cols = [f"{fam} Curve-MW{i}" for i in range(1, 36)]
    cols = (
        [
            "SCED Time Stamp",
            "Repeated Hour Flag",
            "Resource Name",
            "Resource Type",
            "Telemetered Resource Status",
            "HSL",
            "HASL",
            "Base Point",
            "Telemetered Net Output ",
        ]
        + pr_cols
        + mw_cols
    )
    frames = []
    for pq in parquets:
        df = pd.read_parquet(pq, columns=cols)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        online = df["Telemetered Resource Status"].astype(str).str.upper()
        df = df[online.str.startswith("ON")].copy()
        ts = pd.to_datetime(df["SCED Time Stamp"], format="%m/%d/%Y %H:%M:%S")
        ts_cst = _prevailing_to_standard(
            ts, df["Repeated Hour Flag"].fillna("N").astype(str).str.upper().eq("Y")
        )
        ok = ts_cst.notna().to_numpy()
        df, ts_cst = df[ok], ts_cst[ok]
        year, hoy, keep = _hoy_nonleap(ts_cst)
        df = df[keep].copy()
        df["ts"] = ts_cst[keep]
        df["year"], df["hoy"] = year[keep], hoy[keep]
        df["cls"] = df["Resource Type"].map(CLASS_OF_RESTYPE)
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)

    state = json.loads(STATE_JSON.read_text())
    edges = np.asarray(NETLOAD_PCT_EDGES, dtype=float)
    df["bin"] = -1
    df["w"] = np.nan
    for y in sorted(df["year"].unique()):
        pct = _netload_pct(int(y))
        my = (df["year"] == y).to_numpy()
        df.loc[my, "bin"] = np.searchsorted(
            edges, pct[df.loc[my, "hoy"].to_numpy(int)], side="right"
        )
        for cls in df["cls"].unique():
            tbl = state.get(cls, {}).get("years", {}).get(str(int(y)))
            if tbl is None:
                continue
            w = np.asarray(tbl, dtype=float)
            m = my & (df["cls"] == cls).to_numpy()
            df.loc[m, "w"] = np.clip(w[df.loc[m, "hoy"].to_numpy(int)], 0.0, 1.0)
    return df


def room_ladder(d: pd.DataFrame, fam: str) -> dict | None:
    """MW-weighted price quantiles of online remaining room (op -> HASL).

    Staircase segments of the (MW_i, Price_i) curve clipped to
    [max(prev, op), min(MW_i, HASL)]; per-hour room normalized by the hour's
    interval count so 15-min and 5-min (post-RTC) publication grains weigh
    equally.
    """
    pr_cols = [f"{fam} Curve-Price{i}" for i in range(1, 36)]
    mw_cols = [f"{fam} Curve-MW{i}" for i in range(1, 36)]
    mw = d[mw_cols].to_numpy(float)
    pr = d[pr_cols].to_numpy(float)
    op = np.maximum(
        d["Base Point"].to_numpy(float), d["Telemetered Net Output "].to_numpy(float)
    )
    hasl = d["HASL"].to_numpy(float)
    prev = np.zeros(len(d))
    Ws, Ps = [], []
    for i in range(35):
        m, p = mw[:, i], pr[:, i]
        ok = np.isfinite(m) & np.isfinite(p)
        lo = np.maximum(prev, op)
        hi = np.minimum(np.where(ok, m, prev), hasl)
        Ws.append(np.where(ok, np.clip(hi - lo, 0.0, None), 0.0))
        Ps.append(np.where(ok, p, np.nan))
        prev = np.where(ok, m, prev)
    W = np.concatenate(Ws)
    P = np.concatenate(Ps)
    m = np.isfinite(P) & (W > 0)
    if not m.any():
        return None
    W, P = W[m], np.clip(P[m], None, HCAP_USD_MWH)
    n_iv = d.groupby(["year", "hoy"])["ts"].nunique().sum()
    n_hours = d.groupby(["year", "hoy"]).ngroups
    order = np.argsort(P)
    P, W = P[order], W[order]
    cw = np.cumsum(W)
    tot = cw[-1]
    out = {
        "n_hours": n_hours,
        "room_gw_mean": tot / max(n_iv, 1) / 1e3,
        "sub200_mw_mean": float(W[P <= 200].sum()) / max(n_iv, 1),
    }
    for q in ROOM_QS:
        out[f"p{int(q * 100)}"] = float(np.interp(q * tot, cw, P))
    return out


def _print_ladder(label: str, r: dict | None) -> None:
    if r is None:
        print(f"  {label}: no room segments")
        return
    print(
        f"  {label}: {r['n_hours']:4d} hrs, mean room {r['room_gw_mean']:6.2f} GW/hr, "
        f"sub-$200 {r['sub200_mw_mean']:7.0f} MW/hr, p10/30/50/70/90 = "
        + "/".join(f"{r[f'p{int(q * 100)}']:.0f}" for q in ROOM_QS)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tail", type=Path, nargs="+", default=[DEFAULT_TAIL])
    ap.add_argument("--control", type=Path, nargs="+", default=DEFAULT_CONTROL)
    ap.add_argument("--hours", nargs="+", default=list(CORE_HOURS))
    ap.add_argument(
        "--cells",
        action="store_true",
        help="also print per-(cls, bin) LOADED-cell room ladders, tail vs control",
    )
    ap.add_argument("--sced2", action="store_true")
    args = ap.parse_args()
    fam = "SCED2" if args.sced2 else "SCED1"

    tail = _load(args.tail, fam)
    print(f"===== named hours ({fam}): online remaining-room ladder per class =====")
    for spec in args.hours:
        day, hh = spec.split("T")
        t0 = pd.Timestamp(f"{day} {int(hh):02d}:00")
        m = (tail["ts"] >= t0) & (tail["ts"] < t0 + pd.Timedelta(hours=1))
        for cls in ("CC", "CT"):
            d = tail[m & (tail["cls"] == cls)]
            if len(d):
                w_cls = float(d["w"].iloc[0])
                r = room_ladder(d, fam)
                _print_ladder(
                    f"{spec} {cls} (bin {int(d['bin'].iloc[0])}, w {w_cls:.2f})", r
                )
            else:
                print(f"  {spec} {cls}: not in the intake")

    if args.cells:
        ctrl = _load(args.control, fam)
        for name, df in (("TAIL", tail), ("CONTROL", ctrl)):
            print(f"\n===== {name}: LOADED (w<=1/3) cell room ladders =====")
            sub = df[df["w"] <= 1 / 3]
            for (cls, b), d in sub.groupby(["cls", "bin"]):
                _print_ladder(f"{cls} bin{int(b)}", room_ladder(d, fam))


if __name__ == "__main__":
    main()
