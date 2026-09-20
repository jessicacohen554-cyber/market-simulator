#!/usr/bin/env python3
"""caiso-288 — the blackout census (G-CENSUS) and the fill-construction
selection (G-FILL), both at ZERO LP.

Run:  .venv/bin/python scripts/probes/caiso288_blackout_census.py

G-CENSUS prints the committed CA Composite daily citygate series' trade-gap
histogram, which is what identifies ``_GAS_BLACKOUT_MIN_GAP_DAYS``: gaps of 1-4
days are the market's own trading packages, gaps of >=8 days are weeks in which
EIA published no Natural Gas Weekly Update, and the histogram is EMPTY at 6 and
7 — so any threshold in that region selects the identical gap set and the value
is not selectable against any result (rules 1 [R-STRUCT], 5 [R-NO-MAGIC]).

G-FILL chooses between the three candidate fill constructions on RECONSTRUCTION
SKILL AGAINST WITHHELD MEASURED GAS DAYS, with no reference whatever to the
CAISO price residual. Every fully-measured window of 8 / 12 / 15 / 19 days in
the committed series is a synthetic holdout: the interior is withheld, each
construction reconstructs it from the two bracketing prints (plus, for the
HH-basis form, the measured Henry Hub daily series inside the gap), and the
error is scored against the withheld truth.
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
from market_sim.data.fuel.hubs import _caiso_citygate_daily_dated

ca = _caiso_citygate_daily_dated(None)
rows = [(pd.Timestamp(year=y, month=m, day=d), v)
        for y, mm in ca.items() for m, dd in mm.items() for d, v in dd.items()]
ca_s = pd.Series(dict(rows)).sort_index()

hh = pd.read_csv("data/raw/gas-prices/henry_hub_daily.csv", parse_dates=["date"])
hh_s = hh.set_index("date")["price_usd_mmbtu"].sort_index()

def daily_grid(a, b):
    return pd.date_range(a, b, freq="D")

def hh_stair(idx):
    """HH value on every calendar day: last measured HH print, forward-filled."""
    return hh_s.reindex(hh_s.index.union(idx)).sort_index().ffill().bfill().reindex(idx)

def recon(L_date, R_date, L, R, idx, how):
    n = len(idx)
    if how == "hold":                       # (a) current behaviour
        return pd.Series(L, index=idx)
    span = (R_date - L_date).days
    w = np.array([(d - L_date).days / span for d in idx])
    if how == "interp":                     # (b) linear in price
        return pd.Series(L + w * (R - L), index=idx)
    if how == "hh_basis":                   # (c) HH daily shape, basis interpolated
        h = hh_stair(idx).to_numpy()
        hL = float(hh_stair(pd.DatetimeIndex([L_date])).iloc[0])
        hR = float(hh_stair(pd.DatetimeIndex([R_date])).iloc[0])
        bL, bR = L - hL, R - hR
        return pd.Series(h + bL + w * (bR - bL), index=idx)
    raise ValueError(how)

# ---- build synthetic holdouts ---------------------------------------------
# Real blackouts are 8-19 calendar days. Use every measured print as a left
# anchor whose forward window of GAPLEN days is FULLY measured on its own
# trading calendar (>=5 interior measured days), so the truth is dense.
def trials(gaplen):
    out = []
    dates = ca_s.index
    for i, L_date in enumerate(dates):
        R_date = L_date + pd.Timedelta(days=gaplen)
        if R_date not in ca_s.index:
            continue
        interior = [d for d in dates if L_date < d < R_date]
        if len(interior) < 5:
            continue
        out.append((L_date, R_date, interior))
    return out

print(f"{'gap':>4} {'trials':>7} | " + " | ".join(f"{h:>22s}" for h in
      ("(a) hold last", "(b) linear interp", "(c) HH-basis interp")))
print(" " * 13 + "| " + " | ".join(f"{'MAE':>10}{'bias':>12}" for _ in range(3)))
agg = {h: [] for h in ("hold", "interp", "hh_basis")}
for gaplen in (8, 12, 15, 19):
    T = trials(gaplen)
    if not T:
        print(f"{gaplen:>4} {0:>7} | (no fully-measured window of this length)")
        continue
    res = {}
    for how in ("hold", "interp", "hh_basis"):
        err = []
        for L_date, R_date, interior in T:
            idx = pd.DatetimeIndex(interior)
            pred = recon(L_date, R_date, float(ca_s[L_date]), float(ca_s[R_date]), idx, how)
            err.extend((pred - ca_s[idx]).tolist())
        err = np.array(err, dtype=float)
        res[how] = (np.abs(err).mean(), err.mean())
        agg[how].extend(err.tolist())
    print(f"{gaplen:>4} {len(T):>7} | " + " | ".join(
        f"{res[h][0]:>10.3f}{res[h][1]:>+12.3f}" for h in ("hold", "interp", "hh_basis")))

print("\nPOOLED over all gap lengths:")
for h, lab in (("hold", "(a) hold last (CURRENT)"), ("interp", "(b) linear interp"),
               ("hh_basis", "(c) HH-basis interp")):
    e = np.array(agg[h])
    print(f"  {lab:26s} n={len(e):6d}  MAE {np.abs(e).mean():7.3f}  "
          f"bias {e.mean():+7.3f}  RMSE {np.sqrt((e**2).mean()):7.3f}  "
          f"p95|e| {np.percentile(np.abs(e),95):7.3f}")

# ---- the same test restricted to SPIKE left-anchors -----------------------
# The defect only bites when the last print before the blackout is elevated.
print("\nRestricted to left anchors in the TOP DECILE of the series (the spike case):")
thr = float(np.percentile(ca_s.to_numpy(), 90))
print(f"  top-decile threshold = ${thr:.2f}/MMBtu")
agg2 = {h: [] for h in agg}
for gaplen in (8, 12, 15, 19):
    for L_date, R_date, interior in trials(gaplen):
        if float(ca_s[L_date]) < thr:
            continue
        idx = pd.DatetimeIndex(interior)
        for how in agg2:
            pred = recon(L_date, R_date, float(ca_s[L_date]), float(ca_s[R_date]), idx, how)
            agg2[how].extend((pred - ca_s[idx]).tolist())
for h, lab in (("hold", "(a) hold last (CURRENT)"), ("interp", "(b) linear interp"),
               ("hh_basis", "(c) HH-basis interp")):
    e = np.array(agg2[h])
    if not len(e):
        print(f"  {lab:26s} no trials"); continue
    print(f"  {lab:26s} n={len(e):6d}  MAE {np.abs(e).mean():7.3f}  "
          f"bias {e.mean():+7.3f}  RMSE {np.sqrt((e**2).mean()):7.3f}")
