"""OBJECT A: what is the model DOING in NYISO's extreme-price hours? (nyiso-233, ZERO LP)

nyiso-232 established that NYISO's C3a residual is TWO objects
(``docs/FINDING-nyiso232-c3a-is-two-objects-2026-09-13.md``): remove each year's
top actual-price hours and the model is OVER-priced by +4.1 to +14.2 % in all
four years, so the headline C3a is a DIFFERENCE OF TWO LARGE ERRORS OF OPPOSITE
SIGN. Any mechanism that lifts ordinary-hour prices to close C3a makes the tail
object worse. A tail mechanism must raise the TAIL WITHOUT raising ordinary
hours — and this probe asks which KIND of mechanism could.

The question it answers, per tail hour, is a fork:

* **The model is NOT short** (thermal headroom available, reserves met, no
  slack): the real market was scarce for a reason the model does not see — its
  fleet is more available than reality's was (outage depth, fuel/gas
  deliverability, energy limits) — and the repair is an AVAILABILITY object.
  A steeper scarcity price curve would do nothing, because nothing is binding.
* **The model IS short** (headroom exhausted, reserve shortfall, or slack):
  the model reproduces the physical scarcity but prices it too cheaply, and the
  repair is a PRICE-FORMATION object (ORDC / reserve demand curve / VOLL shape).

That fork decides an entire mechanism family, so it is measured before any
mechanism is proposed (rule 1 ``[R-STRUCT]``).

Every input is committed: the keeper's ``hourly/`` sidecars and the validation
actuals at ``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``. The
tail is selected on the ACTUAL series only, so the model's own behaviour can
never choose which hours it is judged on.

Run: ``python3 scripts/probes/_nyiso233_tail_mechanism_census.py [top_pct]``
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BUN = Path("results/calibration/nyiso232_deleak_span/hourly")
ACT = Path("data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet")
YEARS = (2022, 2023, 2024, 2025)
TOP_PCT = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0


def _load(year: int) -> pd.DataFrame:
    """Load-weighted model price, demand, slack, dump per hour, beside actual RT."""
    s = pd.read_parquet(BUN / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    n = (
        s.assign(pw=s.price * s.demand)
        .groupby("hour")
        .agg(
            pw=("pw", "sum"),
            demand=("demand", "sum"),
            slack=("slack", "sum"),
            dump=("dump", "sum"),
            rsv=("reserve_price", "max"),
        )
    )
    g = pd.DataFrame(
        {
            "hour": n.index,
            "model": (n.pw / n.demand).to_numpy(),
            "demand": n.demand.to_numpy(),
            "slack": n.slack.to_numpy(),
            "dump": n.dump.to_numpy(),
            "rsv": n.rsv.to_numpy(),
        }
    )
    act = pd.read_parquet(ACT)
    a = act[act.year == year][["hour", "rt"]].rename(columns={"rt": "actual"})
    return g.merge(a, on="hour").dropna()


def _headroom(year: int, hours: np.ndarray) -> tuple[float, float, float]:
    """Thermal (MW dispatched, MW available, spare) averaged over ``hours``."""
    u = pd.read_parquet(
        BUN / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_group", "hour", "mw", "cap_mw"],
    )
    u = u[(u["pass"] == "P1") & u.hour.isin(hours) & (u.plant_group.astype(str) != "")]
    agg = u.groupby("hour")[["mw", "cap_mw"]].sum()
    return (
        float(agg.mw.mean()),
        float(agg.cap_mw.mean()),
        float((agg.cap_mw - agg.mw).mean()),
    )


def _reserve(year: int, hours: np.ndarray) -> tuple[float, int]:
    """Mean total reserve shortfall MW, and how many tail hours carry any."""
    p = BUN / f"reserve_family_{year}.parquet"
    if not p.exists():
        return float("nan"), -1
    r = pd.read_parquet(p)
    r = r[(r["pass"] == "P1") & r.hour.isin(hours)]
    if r.empty:
        return 0.0, 0
    per = r.groupby("hour").shortfall_mw.sum()
    return float(per.reindex(hours, fill_value=0.0).mean()), int((per > 1e-6).sum())


print(
    f"OBJECT A — NYISO extreme-price hours, top {TOP_PCT:g} % by ACTUAL RT price "
    f"(keeper 2026-09-13-nyiso-232-st-gas)\n"
)
hdr = (
    f"{'yr':>5} {'n':>4} {'actual':>9} {'model':>9} {'gap/h':>9} {'%of yr gap':>11} "
    f"{'rsv$':>7} {'short MW':>9} {'hrs sh':>7} {'spare MW':>9} {'spare %':>8} {'slack':>7}"
)
print(hdr)
print("-" * len(hdr))
rows = []
for y in YEARS:
    d = _load(y)
    k = max(1, int(round(len(d) * TOP_PCT / 100.0)))
    tail = d.nlargest(k, "actual")
    hrs = tail.hour.to_numpy()
    # Annual load-weighted gap, and how much of it the tail carries.
    ann_gap = float((d.actual * d.demand).sum() - (d.model * d.demand).sum())
    tail_gap = float(
        (tail.actual * tail.demand).sum() - (tail.model * tail.demand).sum()
    )
    disp, cap, spare = _headroom(y, hrs)
    short_mw, short_hrs = _reserve(y, hrs)
    rows.append((y, k, tail, spare, cap, short_mw, short_hrs, tail_gap, ann_gap))
    print(
        f"{y:>5} {k:>4} {tail.actual.mean():>9.2f} {tail.model.mean():>9.2f} "
        f"{tail.actual.mean() - tail.model.mean():>9.2f} "
        f"{100 * tail_gap / ann_gap if ann_gap else float('nan'):>10.1f}% "
        f"{tail.rsv.mean():>7.1f} {short_mw:>9.1f} {short_hrs:>7d} "
        f"{spare:>9.0f} {100 * spare / cap:>7.1f}% {tail.slack.mean():>7.2f}"
    )

print(
    "\nREAD: 'spare MW' is thermal cap_mw - mw summed over classified units, averaged over the\n"
    "tail hours. Large spare + zero reserve shortfall + zero slack = the model is NOT short in the\n"
    "hours the real market priced highest, so the object is AVAILABILITY, not price formation:\n"
    "a steeper scarcity curve prices nothing, because nothing binds."
)

print("\nWORST DAYS (by summed load-weighted gap), the events the tail is made of:")
for y in YEARS:
    d = _load(y)
    d = d.assign(day=(d.hour // 24), gap=(d.actual - d.model) * d.demand)
    top = d.groupby("day").gap.sum().nlargest(5)
    tot = d.gap.sum()
    days = ", ".join(
        f"{(pd.Timestamp(f'{y}-01-01') + pd.Timedelta(days=int(dd))).strftime('%b %d')}"
        f" ({100 * v / tot:.0f}%)"
        for dd, v in top.items()
    )
    print(f"  {y}: {days}   [worst 5 = {100 * top.sum() / tot:.1f}% of the annual gap]")
