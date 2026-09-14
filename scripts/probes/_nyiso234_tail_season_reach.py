"""OBJECT A, SEASONAL REACH: can the `temp_dependent_derate` cell reach the tail? (nyiso-234, ZERO LP)

nyiso-233 measured WHAT KIND of object NYISO's price tail is
(``docs/FINDING-nyiso233-tail-is-an-availability-object-2026-09-13.md``): in the
top 1 % of hours by ACTUAL RT price the model carries 3.4-6.2 GW of idle thermal,
zero slack and near-zero reserve shortfall, so the object is AVAILABILITY, not
price formation. It then recorded — correctly, per rule 28(a) — that
``temp_dependent_derate`` sits at ``G`` (nyiso-111 ex-ante refusal) and that the
headroom measurement is new evidence the refusal should be re-read against.

This probe answers the question that re-reading actually turns on, and it is NOT
the identification question nyiso-111 decided. It is a REACH question:

    Of the tail gap the object is made of, how much lies in hours where the
    committed ``temp_dependent_derate`` curve is IDENTICALLY 1.0 — i.e. where the
    mechanism does nothing whatever its slope?

That matters because the curve as coded (``data/fleet/arrays.py``) has exactly two
forms and NEITHER derates a cold hour:

* hinge form (``temp_derate_mean_anchored`` False, the default):
  ``raw = 1 - slope * max(0, Tmax - temp_derate_ref_c)`` with
  ``temp_derate_ref_c = 15.0`` C, so ``Tmax <= 15 C`` gives EXACTLY 1.0;
* mean-anchored form: ``raw = 1 - slope * (Tmax - mean(Tmax))``, which for
  ``Tmax < mean`` exceeds 1.0 and is then clipped to 1.0 by ``np.clip``.

So the dead zone is a property of the COMMITTED CODE, not a fit judgement, and a
reach deficit measured here cannot be rescued by any slope — including one a
future capability instrument might identify. Selection is on the ACTUAL series
only (nyiso-233's exact construction), so no model outcome chooses its own test.

Every input is committed: the keeper's ``hourly/system_<year>.parquet``, the
validation actuals, and the curated NYISO weather the derate itself reads.

Run: ``python3 scripts/probes/_nyiso234_tail_season_reach.py [top_pct]``
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
REF_C = 15.0  # ScenarioConfig.temp_derate_ref_c — the hinge's dead-zone edge


def _load(year: int) -> pd.DataFrame:
    """Load-weighted model price beside the actual RT price, per hour."""
    s = pd.read_parquet(BUN / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    n = (
        s.assign(pw=s.price * s.demand)
        .groupby("hour")
        .agg(pw=("pw", "sum"), demand=("demand", "sum"))
    )
    g = pd.DataFrame(
        {
            "hour": n.index,
            "model": (n.pw / n.demand).to_numpy(),
            "demand": n.demand.to_numpy(),
        }
    )
    act = pd.read_parquet(ACT)
    a = act[act.year == year][["hour", "rt"]].rename(columns={"rt": "actual"})
    return g.merge(a, on="hour").dropna()


def _tmax(year: int, hours: np.ndarray) -> np.ndarray | None:
    """Warmest-zone daily Tmax (C) at ``hours``, exactly as the derate reads it.

    The curve is evaluated per zone (``_zone_tmax.get(gen.zone)``), so a tail
    hour escapes the dead zone if ANY zone is above the hinge. Taking the
    per-hour MAXIMUM over zones is therefore the most generous possible reading
    for the mechanism — the measured dead share is a LOWER bound on the share
    the curve cannot touch.
    """
    try:
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.data.eia930.weather import iso_zone_tmax
    except Exception as exc:  # pragma: no cover - diagnostic probe
        print(f"  (weather unavailable: {exc})")
        return None
    try:
        zones = [z.name for z in get_iso_config("NYISO").zones]
    except Exception:
        zones = [None]
    cols = []
    for z in zones:
        try:
            pair = iso_zone_tmax("NYISO", year, 8760, zone=z)
        except Exception:
            pair = None
        if pair is not None and pair[0] is not None:
            cols.append(np.asarray(pair[0], dtype=float))
    if not cols:
        print(f"  (weather unavailable for {year})")
        return None
    full = np.max(np.vstack(cols), axis=0)
    idx = np.clip(np.asarray(hours, dtype=int), 0, full.size - 1)
    return full[idx]


def main() -> None:
    print(f"NYISO tail SEASONAL REACH — top {TOP_PCT} % of hours by ACTUAL RT price")
    print(
        f"dead zone = the hinge's Tmax <= {REF_C} C, where the curve is identically 1.0\n"
    )

    rows = []
    for year in YEARS:
        df = _load(year)
        k = max(1, int(round(len(df) * TOP_PCT / 100.0)))
        tail = df.nlargest(k, "actual").copy()

        # hour -> calendar month, from the hour index of a calendar year
        ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(
            tail.hour.to_numpy(), unit="h"
        )
        tail["month"] = ts.month

        # the object itself: the under-pricing, load-weighted, in $ terms
        tail["gap"] = (tail.actual - tail.model) * tail.demand
        total = float(tail.gap.clip(lower=0).sum())

        winter = tail.month.isin([12, 1, 2])
        summer = tail.month.isin([6, 7, 8, 9])
        w = float(tail.gap.clip(lower=0)[winter].sum()) / total * 100.0
        s = float(tail.gap.clip(lower=0)[summer].sum()) / total * 100.0

        t = _tmax(year, tail.hour.to_numpy())
        if t is not None:
            dead = t <= REF_C
            d_share = float(tail.gap.clip(lower=0)[dead].sum()) / total * 100.0
            d_hrs = int(dead.sum())
        else:
            d_share, d_hrs = float("nan"), -1

        rows.append(
            (year, k, int(winter.sum()), w, int(summer.sum()), s, d_hrs, d_share)
        )

    print(
        f"{'year':>5} {'tail h':>7} {'DJF h':>6} {'DJF % gap':>10} "
        f"{'JJAS h':>7} {'JJAS % gap':>11} {'Tmax<=15 h':>11} {'DEAD % gap':>11}"
    )
    for year, k, wh, w, sh, s, dh, d in rows:
        dtxt = "n/a" if dh < 0 else f"{dh:>11d}"
        dsh = "n/a" if dh < 0 else f"{d:>10.1f} "
        print(f"{year:>5} {k:>7} {wh:>6} {w:>9.1f}  {sh:>7} {s:>10.1f}  {dtxt} {dsh}")

    print(
        "\nDEAD % gap is the share of the tail's positive under-pricing that falls in hours\n"
        "the committed curve cannot touch AT ANY SLOPE. It is a ceiling on the mechanism's\n"
        "reach, measured on the actual-selected tail — never a statement about fit."
    )


if __name__ == "__main__":
    main()
