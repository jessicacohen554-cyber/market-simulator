#!/usr/bin/env python3
"""caiso-288/289 — the blackout census (G-CENSUS), the fill-construction
selection (G-FILL) and the post-repair footprint audit (G-FOOT289), all ZERO LP.

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

caiso-289 — WHY THIS HARNESS HAD TO BE RE-RUN. Both gates above were originally
measured on the UNREPAIRED series. caiso-288 then recovered **85 published
prints** that ``fetch_caiso_citygate_daily.parse_spot_table`` had been throwing
away (1,806 -> 1,891 rows;
``docs/RESULT-caiso288-the-prints-were-published-2026-09-20.md``), which changes
the very histogram G-CENSUS identifies the threshold on and adds 3,382 days to
G-FILL's holdout. Re-running them is a rule 23 [R-FROZEN-DERIVE] re-derivation
cited to a SOURCE-DATA change, never to a residual. Both verdicts survive; the
numbers do not, and the ones in ``hubs.py`` / ``scenarios.py`` are restated from
this probe's output.

G-FOOT289 is the new gate, and it is the decision-relevant one: it measures what
``caiso_citygate_blackout_bridge`` would actually MOVE if it were armed over the
REPAIRED series, per year, and decomposes that into the two separate channels
the single flag carries — the blackout interiors (the mechanism) and the
year-start left edge (an undeclared convention change that is not the
mechanism). See ``docs/FINDING-caiso289-the-bridge-flag-carries-two-mechanisms-2026-09-20.md``.
"""
import json
import sys, collections, numpy as np, pandas as pd
from pathlib import Path

sys.path.insert(0, "src")
from market_sim.data.fuel.hubs import (
    _caiso_citygate_daily_dated,
    _flow_date_staircase,
    _GAS_BLACKOUT_MIN_GAP_DAYS,
)

OUT = Path("results/calibration/_caiso289_postrepair_audit.json")

#: CAISO CC_REGULAR cap-weighted base heat rate, MMBtu/MWh — converts a
#: $/MMBtu fuel error into the $/MWh marginal-cost error it causes. Identical to
#: ``caiso288_blackout_estimator_scoreboard.CC_HR``; nothing is fitted with it.
CC_HR = 7.44

#: The scored backcast years of the CAISO keeper, for reporting only.
SCORED_YEARS = (2022, 2023, 2024, 2025)

ca = _caiso_citygate_daily_dated(None)
rows = [(pd.Timestamp(year=y, month=m, day=d), v)
        for y, mm in ca.items() for m, dd in mm.items() for d, v in dd.items()]
ca_s = pd.Series(dict(rows)).sort_index()

hh = pd.read_csv("data/raw/gas-prices/henry_hub_daily.csv", parse_dates=["date"])
hh_s = hh.set_index("date")["price_usd_mmbtu"].sort_index()

AUDIT: dict = {
    "run": "caiso-289 post-repair blackout audit (G-CENSUS / G-FILL / G-FOOT289)",
    "series_rows": int(len(ca_s)),
    "series_span": [str(ca_s.index.min().date()), str(ca_s.index.max().date())],
    "min_gap_days": int(_GAS_BLACKOUT_MIN_GAP_DAYS),
    "cc_heat_rate_mmbtu_per_mwh": CC_HR,
}

# ---- G-CENSUS: the trade-gap histogram the threshold is identified on -------
# The docstring has always promised this table; until caiso-289 the code never
# actually printed it, so the numbers quoted in hubs.py could not be checked
# against a run. It prints now.
gaps = [(b - a).days for a, b in zip(ca_s.index, ca_s.index[1:])]
hist = collections.Counter(gaps)
print(f"G-CENSUS — committed CA-composite series: {len(ca_s)} prints, "
      f"{ca_s.index.min().date()} -> {ca_s.index.max().date()}, {len(gaps)} gaps")
print("  " + "   ".join(f"gap {g:>2} d: {hist[g]:>4}" for g in sorted(hist)))
empty = [g for g in range(1, max(hist) + 1) if g not in hist]
in_empty = _GAS_BLACKOUT_MIN_GAP_DAYS in empty
# Every threshold that selects the SAME gap set as the configured one.
sel_at = {t: sum(1 for g in gaps if g >= t) for t in range(1, max(hist) + 2)}
same = sorted(t for t, n in sel_at.items() if n == sel_at[_GAS_BLACKOUT_MIN_GAP_DAYS])
print(f"  histogram empty at: {empty}")
print(f"  _GAS_BLACKOUT_MIN_GAP_DAYS = {_GAS_BLACKOUT_MIN_GAP_DAYS} "
      f"{'sits in that empty region' if in_empty else 'DOES NOT sit in an empty region'}; "
      f"thresholds {same} all select the identical "
      f"{sel_at[_GAS_BLACKOUT_MIN_GAP_DAYS]} gaps")
AUDIT["census"] = {
    "histogram": {str(g): int(hist[g]) for g in sorted(hist)},
    "n_gaps": len(gaps),
    "empty_bins": empty,
    "threshold_in_empty_region": bool(in_empty),
    "thresholds_selecting_same_set": same,
    "n_blackouts_selected": int(sel_at[_GAS_BLACKOUT_MIN_GAP_DAYS]),
}
print()


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
AUDIT["g_fill_pooled"] = {}
for h, lab in (("hold", "(a) hold last (CURRENT)"), ("interp", "(b) linear interp"),
               ("hh_basis", "(c) HH-basis interp")):
    e = np.array(agg[h])
    print(f"  {lab:26s} n={len(e):6d}  MAE {np.abs(e).mean():7.3f}  "
          f"bias {e.mean():+7.3f}  RMSE {np.sqrt((e**2).mean()):7.3f}  "
          f"p95|e| {np.percentile(np.abs(e),95):7.3f}")
    AUDIT["g_fill_pooled"][h] = {
        "n": int(len(e)),
        "mae": round(float(np.abs(e).mean()), 4),
        "bias": round(float(e.mean()), 4),
        "rmse": round(float(np.sqrt((e ** 2).mean())), 4),
        "p95_abs": round(float(np.percentile(np.abs(e), 95)), 4),
    }

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
AUDIT["g_fill_spike"] = {"top_decile_threshold": round(thr, 4)}
for h, lab in (("hold", "(a) hold last (CURRENT)"), ("interp", "(b) linear interp"),
               ("hh_basis", "(c) HH-basis interp")):
    e = np.array(agg2[h])
    if not len(e):
        print(f"  {lab:26s} no trials"); continue
    print(f"  {lab:26s} n={len(e):6d}  MAE {np.abs(e).mean():7.3f}  "
          f"bias {e.mean():+7.3f}  RMSE {np.sqrt((e**2).mean()):7.3f}")
    AUDIT["g_fill_spike"][h] = {
        "n": int(len(e)),
        "mae": round(float(np.abs(e).mean()), 4),
        "bias": round(float(e.mean()), 4),
        "rmse": round(float(np.sqrt((e ** 2).mean())), 4),
    }


# ---- G-FOOT289: what arming the flag would MOVE, over the REPAIRED series ---
# The scoreboard (caiso288_blackout_estimator_scoreboard.py) adjudicated the
# bridge against the 14 blackouts whose prints caiso-288 RECOVERED. Those gaps
# no longer exist, so the bridge no longer touches them: that adjudication
# describes a footprint the armed flag would never have. This gate measures the
# footprint it WOULD have, and splits it in two, because the one flag moves two
# independent things:
#
#   (A) BLACKOUT INTERIORS — the mechanism. Days strictly inside a gap of
#       >= _GAS_BLACKOUT_MIN_GAP_DAYS between consecutive measured prints.
#   (B) THE YEAR-START LEFT EDGE — NOT the mechanism, and declared nowhere.
#       _flow_date_staircase's unbridged branch reindexes on ONE year's stamps
#       and .bfill()s, so flow days before the year's first print take the
#       year's FIRST JANUARY TRADE. Its bridged branch reindexes on the FULL
#       multi-year series (it has to, to bracket a December blackout against the
#       next January), so the same days .ffill() from the PREVIOUS DECEMBER's
#       last trade instead. That switch rides along with the flag in every year,
#       whether or not any blackout is near.
print("\n\nG-FOOT289 — what arming caiso_citygate_blackout_bridge moves, "
      "per year, over the REPAIRED series")
flow_all = pd.Series({
    pd.Timestamp(year=y, month=m, day=d) + pd.Timedelta(days=1): v
    for y, mm in sorted(ca.items())
    for m, dd in sorted(mm.items())
    for d, v in sorted(dd.items())
}).sort_index()
known = flow_all.dropna().index

blackouts, interior_days = [], set()
for a, b in zip(known, known[1:]):
    span = (b - a).days
    if span < _GAS_BLACKOUT_MIN_GAP_DAYS:
        continue
    inner = pd.date_range(a + pd.Timedelta(days=1), b - pd.Timedelta(days=1), freq="D")
    interior_days.update(inner)
    blackouts.append({
        "left_flow_day": str(a.date()), "right_flow_day": str(b.date()),
        "gap_days": int(span), "left_usd": round(float(flow_all[a]), 4),
        "right_usd": round(float(flow_all[b]), 4), "interior_days": int(len(inner)),
    })
print(f"  {len(blackouts)} blackouts remain, {len(interior_days)} interior calendar days; "
      f"{sum(1 for x in blackouts if int(x['left_flow_day'][:4]) >= 2021)} of them 2021+")
AUDIT["remaining_blackouts"] = blackouts

print(f"\n  {'year':>5} | {'(A) bridge d':>12} {'mean $':>8} {'d mc':>8} | "
      f"{'(B) left-edge d':>15} {'mean $':>8} {'d mc':>8}")
AUDIT["footprint_by_year"] = {}
for y in sorted(ca):
    base = _flow_date_staircase(ca[y], y)
    brid = _flow_date_staircase(ca[y], y, bridge_all_years=ca, bridge_hh=hh_s)
    if base is None or brid is None:
        continue
    cal = pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D")
    cal = cal[~((cal.month == 2) & (cal.day == 29))]
    d = brid - base
    moved = ~np.isclose(d, 0.0, atol=1e-12)
    is_int = np.array([t in interior_days for t in cal])
    A, B = moved & is_int, moved & ~is_int

    def leg(mask, width):
        if not mask.sum():
            return f"{0:>{width}} {'-':>8} {'-':>8}", None
        mean = float(d[mask].mean())
        return (f"{int(mask.sum()):>{width}} {mean:>+8.3f} {mean * CC_HR:>+8.2f}",
                {"days": int(mask.sum()), "mean_usd_mmbtu": round(mean, 4),
                 "mean_mc_usd_mwh": round(mean * CC_HR, 3),
                 "days_list": [str(t.date()) for t in cal[mask]]})

    ta, ra = leg(A, 12)
    tb, rb = leg(B, 15)
    print(f"  {y:>5} | {ta} | {tb}")
    AUDIT["footprint_by_year"][str(y)] = {"bridge_interiors": ra, "left_edge": rb}

print("\n  (A) is the mechanism. (B) is a convention change the flag carries "
      "silently.\n  In 2022 and 2023 the flag's ENTIRE effect is (B) — (A) is zero days.")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(AUDIT, indent=1) + "\n")
print(f"\nwrote {OUT}")
