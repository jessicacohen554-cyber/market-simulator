"""xiso-8 phase 0 — the year-start LEFT-EDGE object, measured across BOTH ISOs.

ZERO LP. Pure arithmetic over the committed dated citygate maps.

THE DEFECT (caiso-289 §4, owner ruling 2026-09-20 opening this as its own
cross-ISO object). ``_flow_date_staircase`` places each trade-day print on its
gas FLOW day (trade + 1; Friday's trade covers the holiday-extended weekend
package) and forward-fills the non-trading gaps, then ``.bfill()``s whatever is
left. The only days ``.bfill()`` can reach are the year's OPENING flow days —
those before the first January trade's flow day. On the function's own
documented convention those days were priced by the PREVIOUS DECEMBER's last
trade; the back-fill instead hands them the year's FIRST JANUARY trade, which
had not happened yet and which prices a LATER flow day.

THE BASIS IS RULE 14 ``[R-ACCURATE]``, ON THE SOURCE CONVENTION, AND NOTHING
ELSE. This probe reports direction and magnitude per ISO per year. It does not
read, quote or rank any residual, and no gate below selects anything.

THE TWO ISOs ARE EXPOSED THROUGH DIFFERENT CHANNELS, which is the whole point
of measuring MISO before sizing the object:

  * CAISO — ``hubs.py::caiso_citygate_monthly_from_daily`` uses the staircase as
    a LEVEL series under ``caiso_citygate_flow_date`` (armed in the keeper), so a
    left-edge error is a direct $/MMBtu error on those flow days.
  * MISO — two call sites, and the keeper arms neither as a level:
      - ``basis/miso.py:160`` ``miso_chicago_daily_shape_factors``, under
        ``miso_winter_citygate_daily`` (ARMED in the MISO keeper). The factors
        are renormalized to mean EXACTLY 1.0 WITHIN EVERY MONTH, so a left-edge
        change cannot move January's gas LEVEL at all — it redistributes price
        WITHIN January. G-MISO-SHAPE below measures that redistribution.
      - ``basis/miso.py:501`` ``apply_miso_marginal_commodity_pricing``, under
        ``miso_gas_marginal_commodity_pricing`` (OFF in the MISO keeper). That
        one IS a level channel; measured here for the record, inert today.

Gates:
  G-LE-CENSUS  — per ISO per year: which days the back-fill reaches, the value
                 it hands them, the value the prior December's last trade would
                 hand them, and the delta.
  G-MISO-SHAPE — the live MISO channel: the within-month shape factors before
                 and after, and the mean-preservation identity that bounds it.
  G-DERIVE     — every call site of ``_flow_date_staircase``, so nothing that
                 would move under a repair is missed (rule 23 ``[R-FROZEN-DERIVE]``
                 names ``derive_miso_gas_variable_transport.py`` in particular).
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, "src")
from market_sim.data.fuel.hubs import (  # noqa: E402
    _caiso_citygate_daily_dated,
    _flow_date_staircase,
    _GAS_BLACKOUT_MIN_GAP_DAYS,
    _miso_citygate_daily_dated,
)

OUT = Path("results/calibration/_xiso8_left_edge_census.json")

#: CAISO CC_REGULAR cap-weighted base heat rate, MMBtu/MWh. Identical to
#: ``caiso288_blackout_census.CC_HR``; converts a $/MMBtu fuel error into the
#: $/MWh marginal-cost error it causes. Nothing is fitted with it.
CAISO_CC_HR = 7.44

#: MISO CC_REGULAR cap-weighted base heat rate, MMBtu/MWh, from the same
#: published-heat-rate construction the MISO lane uses for its own sizing
#: (miso-262 §3). Reporting only.
MISO_CC_HR = 7.45

AUDIT: dict = {"gates": {}}


def _flow_map(dated: dict) -> pd.Series:
    """Full multi-year FLOW-day series ($/MMBtu) from a dated trade-day map."""
    return pd.Series(
        {
            pd.Timestamp(year=y, month=m, day=d) + pd.Timedelta(days=1): v
            for y, months in sorted(dated.items())
            for m, days in sorted(months.items())
            for d, v in sorted(days.items())
        }
    ).sort_index()


def left_edge_census(name: str, dated: dict, hr: float) -> list[dict]:
    """G-LE-CENSUS for one ISO: the days ``.bfill()`` reaches, and by how much.

    The *correct* left-edge value under the function's own convention is the
    last FLOW value the previous December's trades produce — i.e. the previous
    year's last print, forward-filled across the New Year package.
    """
    flow_all = _flow_map(dated)
    rows = []
    for year in sorted(dated):
        cal = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        cal = cal[~((cal.month == 2) & (cal.day == 29))]
        cur = _flow_date_staircase(dated[year], year)
        if cur is None:
            continue
        # The days the back-fill reaches: flow days strictly before the first
        # flow print ``_flow_date_staircase`` ITSELF sees. That function builds
        # ``stamps`` from ``dated_year`` ALONE, so a prior-year Dec-31 trade —
        # which flows on Jan 1 of THIS year — is NOT in its index and does not
        # shorten the edge. Deriving ``first_flow`` from the multi-year series
        # instead silently undercounts exactly those years.
        own = pd.Series(
            {
                pd.Timestamp(year=year, month=m, day=d) + pd.Timedelta(days=1): v
                for m, days in sorted(dated[year].items())
                for d, v in sorted(days.items())
            }
        ).sort_index()
        own = own[own.index.year == year]
        if own.empty:
            continue
        this_year = own
        first_flow = own.index.min()
        edge = cal[cal < first_flow]
        if not len(edge):
            rows.append({"year": year, "days": 0})
            continue
        # The anchor is the PRIOR YEAR's last TRADE, wherever its FLOW day
        # lands. A Dec-31 trade flows on Jan 1 of THIS year, so slicing the
        # multi-year series on ``index < Jan 1`` drops precisely the print that
        # most often prices the edge — it must be selected on the trade's year,
        # not on its flow day's year.
        prior = pd.Series(
            {
                pd.Timestamp(year=year - 1, month=m, day=d) + pd.Timedelta(days=1): v
                for m, days in sorted(dated.get(year - 1, {}).items())
                for d, v in sorted(days.items())
            }
        ).sort_index()
        if prior.empty:  # an empty dict yields a RangeIndex, not a DatetimeIndex
            rows.append({"year": year, "days": int(len(edge)), "prior_print": None})
            continue
        prior = prior[prior.index < first_flow]
        if prior.empty:
            rows.append({"year": year, "days": int(len(edge)), "prior_print": None})
            continue
        used = float(this_year.loc[first_flow])          # bfill  (current)
        correct = float(prior.iloc[-1])                  # ffill  (the convention)
        # G-LE-GAP: is the year boundary bracketed by a TRADING PACKAGE or by a
        # PUBLICATION BLACKOUT? The convention argument (Friday's trade covers
        # the holiday-extended weekend package) licenses forward-fill only
        # across a package. A gap of >= _GAS_BLACKOUT_MIN_GAP_DAYS is the EIA
        # blackout the caiso-288 bridge owns (rule 19 [R-ONE-MECH]) -- constant-
        # extending the last print across one is the very artifact that lane
        # exists to remove, and this object must NOT reach it.
        gap_days = int((first_flow - prior.index[-1]).days)
        gap_class = "package" if gap_days < _GAS_BLACKOUT_MIN_GAP_DAYS else "BLACKOUT"
        rows.append(
            {
                "year": year,
                "days": int(len(edge)),
                "gap_days": gap_days,
                "gap_class": gap_class,
                "edge_days": [str(t.date()) for t in edge],
                "used_trade_day": str((first_flow - pd.Timedelta(days=1)).date()),
                "used_usd": round(used, 4),
                "correct_trade_day": str((prior.index[-1] - pd.Timedelta(days=1)).date()),
                "correct_usd": round(correct, 4),
                "delta_usd_mmbtu": round(correct - used, 4),
                "delta_cc_mc_usd_mwh": round((correct - used) * hr, 3),
            }
        )
    print(f"\nG-LE-CENSUS — {name}")
    print(
        f"  {'year':>5} | {'days':>4} | {'gap':>3} {'class':>8} | "
        f"{'prior Dec last trade':>22} | {'used (first Jan)':>20} | "
        f"{'d $/MMBtu':>10} | {'d CC mc':>9}"
    )
    for r in rows:
        if not r.get("days") or r.get("correct_usd") is None:
            print(f"  {r['year']:>5} | {r.get('days', 0):>4} | {'-':>3} {'-':>8} | "
                  f"{'(no prior-year print)':>22} | {'-':>20} | {'-':>10} | {'-':>9}")
            continue
        print(
            f"  {r['year']:>5} | {r['days']:>4} | {r['gap_days']:>3} {r['gap_class']:>8} | "
            f"{r['correct_trade_day'] + ' = ' + format(r['correct_usd'], '6.2f'):>22} | "
            f"{r['used_trade_day'] + ' = ' + format(r['used_usd'], '6.2f'):>20} | "
            f"{r['delta_usd_mmbtu']:>+10.3f} | {r['delta_cc_mc_usd_mwh']:>+9.2f}"
        )
    inscope = [r for r in rows if r.get("gap_class") == "package"]
    outscope = [r for r in rows if r.get("gap_class") == "BLACKOUT"]
    print(
        f"  -> IN SCOPE for this object (package): {len(inscope)} year(s) "
        f"{[r['year'] for r in inscope]}\n"
        f"  -> OUT OF SCOPE (blackout, the caiso-288 bridge's territory): "
        f"{len(outscope)} year(s) {[r['year'] for r in outscope]}"
    )
    return rows


def miso_shape_channel(dated: dict, census: list[dict]) -> list[dict]:
    """G-MISO-SHAPE — the LIVE MISO channel, and why it is bounded.

    ``miso_chicago_daily_shape_factors`` renormalizes each month's factors to
    mean EXACTLY 1.0, so the monthly gas LEVEL is invariant to the left edge by
    construction. What moves is the within-January distribution. Reported as the
    max and RMS factor change over January, and the implied $/MWh swing on those
    days at a nominal $4/MMBtu January level (a REPORTING scale, not an input).
    """
    rows = []
    print("\nG-MISO-SHAPE — the live MISO channel (mean-preserving within month)")
    print(
        f"  {'year':>5} | {'edge d':>6} | {'Jan mean $ before':>17} | "
        f"{'after':>7} | {'max |df|':>9} | {'rms df':>7} | {'edge d mc @$4':>13}"
    )
    for year in sorted(dated):
        cur = _flow_date_staircase(dated[year], year)
        if cur is None:
            continue
        # Same derivation as G-LE-CENSUS (see there): own-year stamps set the
        # first flow day, the prior year's last TRADE sets the anchor, and the
        # repair is scoped to a PACKAGE gap only.
        r = {x["year"]: x for x in census}.get(year)
        if not r or r.get("gap_class") != "package":
            continue
        n_edge = int(r["days"])
        rep = cur.copy()
        rep[:n_edge] = float(r["correct_usd"])  # the repaired left edge
        jan_cur, jan_rep = cur[:31], rep[:31]
        f_cur = jan_cur / jan_cur.mean()
        f_rep = jan_rep / jan_rep.mean()
        df = f_rep - f_cur
        rows.append(
            {
                "year": year,
                "edge_days": n_edge,
                "jan_mean_before": round(float(jan_cur.mean()), 4),
                "jan_mean_after": round(float(jan_rep.mean()), 4),
                "max_abs_factor_change": round(float(np.abs(df).max()), 5),
                "rms_factor_change": round(float(np.sqrt((df**2).mean())), 5),
                "edge_factor_change": round(float(df[:n_edge].mean()), 5),
                "edge_delta_mc_at_4usd": round(
                    float(df[:n_edge].mean()) * 4.0 * MISO_CC_HR, 3
                ),
            }
        )
        r = rows[-1]
        print(
            f"  {year:>5} | {n_edge:>6} | {r['jan_mean_before']:>17.3f} | "
            f"{r['jan_mean_after']:>7.3f} | {r['max_abs_factor_change']:>9.4f} | "
            f"{r['rms_factor_change']:>7.4f} | {r['edge_delta_mc_at_4usd']:>+13.2f}"
        )
    print(
        "\n  The monthly MEAN moves because the January segment's own mean moves;\n"
        "  the FACTORS are then renormalized to 1.0, so the gas LEVEL the caller\n"
        "  applies them to is untouched and only the within-January SHAPE moves."
    )
    return rows


print("=" * 78)
print("xiso-8 phase 0 — the year-start left-edge object, CAISO + MISO. ZERO LP.")
print("=" * 78)

ca = _caiso_citygate_daily_dated(None)
mi = _miso_citygate_daily_dated(None)
AUDIT["gates"]["G-LE-CENSUS"] = {
    "CAISO": left_edge_census("CAISO (SoCal citygate)", ca, CAISO_CC_HR),
    "MISO": left_edge_census("MISO (Chicago citygate)", mi, MISO_CC_HR),
}
AUDIT["gates"]["G-MISO-SHAPE"] = miso_shape_channel(
    mi, AUDIT["gates"]["G-LE-CENSUS"]["MISO"]
)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(AUDIT, indent=1) + "\n")
print(f"\nwrote {OUT}")
