"""Shared helpers for the NYISO / NEISO zonal-sufficiency tests.

Both ISOs gate a multi-zone topology on the actual day-ahead LMP spreads — the
same empirical test as ``scripts/caiso_zonal_sufficiency.py``: if the zones
rarely diverge a single copper-plate price suffices; if they part by tens of
$/MWh for a meaningful share of hours the topology carries real information a
single zone cannot reproduce. This module holds the per-spread duration-curve
statistics, the seasonal / hour-of-day concentration of the wide hours, and
the table renderer; each per-ISO script supplies the model-zone hourly frames
(from ``scripts/data/derive_actual_lmp.py``) and the zone pairs to report.

Usage (per-ISO scripts):
    python scripts/nyiso_zonal_sufficiency.py [--years ...] [--kind da|rt] [--md]
    python scripts/neiso_zonal_sufficiency.py [--years ...] [--kind da|rt] [--md]
"""

from __future__ import annotations

import pandas as pd

# Calendar season of each month, for "where does the separation concentrate".
_SEASONS = {
    12: "Winter",
    1: "Winter",
    2: "Winter",
    3: "Spring",
    4: "Spring",
    5: "Spring",
    6: "Summer",
    7: "Summer",
    8: "Summer",
    9: "Fall",
    10: "Fall",
    11: "Fall",
}
_SEASON_ORDER = ("Winter", "Spring", "Summer", "Fall")

# $/MWh threshold defining a "separated" hour for the concentration analysis
# (the same > $20 cut reported in the duration-curve table).
WIDE = 20.0


def spread_stats(spread: pd.Series) -> dict:
    """Signed mean + |spread| duration-curve percentiles + threshold shares.

    ``spread`` is ``zone_a − zone_b`` per hour; NaN hours (the spring-forward
    gap) are ignored. The signed mean keeps the sign (which zone is dear); the
    percentiles and the > $5 / > $20 shares are on the absolute spread.
    """
    a = spread.abs().dropna()
    return {
        "hours": int(len(a)),
        "signed_mean": round(float(spread.mean()), 2),
        "p50": round(float(a.quantile(0.50)), 2),
        "p90": round(float(a.quantile(0.90)), 2),
        "p99": round(float(a.quantile(0.99)), 2),
        "pct_gt_5": round(100.0 * float((a > 5).mean()), 1),
        "pct_gt_20": round(100.0 * float((a > 20).mean()), 1),
    }


def concentration(spread: pd.Series) -> dict:
    """Where the |spread| > $20 hours fall: season shares, sign, top hours.

    ``spread`` is indexed by the local timestamp. Returns the count of wide
    hours, their share (%) in each season, the share that are positive (the
    first zone dear), and the three busiest hours-of-day (0-23, hour-beginning).
    """
    wide = spread[spread.abs() > WIDE].dropna()
    n = int(len(wide))
    if not n:
        return {"n": 0}
    months = pd.DatetimeIndex(wide.index).month
    seasons = pd.Series(months).map(_SEASONS)
    season_share = {
        s: round(100.0 * float((seasons == s).mean()), 1) for s in _SEASON_ORDER
    }
    hod = pd.Series(pd.DatetimeIndex(wide.index).hour).value_counts()
    return {
        "n": n,
        "seasons": season_share,
        "top_hod": [int(h) for h in hod.head(3).index],
        "pos_share": round(100.0 * float((wide > 0).mean()), 1),
    }


def analyze(frame_for, years: list[int], pairs, kind: str) -> tuple[dict, dict]:
    """Run the spread test for ``years``.

    Args:
        frame_for: ``year, kind -> DataFrame`` of model-zone (+ ``hub``) hourly
            LMP, or ``None`` if the year's source is absent.
        years: trade years to test.
        pairs: ``(zone_a, zone_b, label)`` triples to report.
        kind: ``"da"`` or ``"rt"``.

    Returns:
        ``(stats, conc)`` — ``{year: {label: spread_stats}}`` and
        ``{year: {label: concentration}}`` for the years with data.
    """
    stats: dict[int, dict[str, dict]] = {}
    conc: dict[int, dict[str, dict]] = {}
    for year in years:
        fr = frame_for(year, kind)
        if fr is None:
            print(f"  {year}: no {kind.upper()} source — skipped")
            continue
        stats[year] = {}
        conc[year] = {}
        for a, b, label in pairs:
            if a not in fr.columns or b not in fr.columns:
                continue
            spread = fr[a] - fr[b]
            stats[year][label] = spread_stats(spread)
            conc[year][label] = concentration(spread)
    return stats, conc


def render_table(stats: dict, markdown: bool) -> str:
    """Plain or markdown table of the spread duration curves."""
    bar = "| " if markdown else ""
    sep = " | " if markdown else "  "
    end = " |" if markdown else ""
    head = [
        "year",
        "spread",
        "signed mean",
        "|s| p50",
        "|s| p90",
        "|s| p99",
        "% |s|>$5",
        "% |s|>$20",
    ]
    lines = [bar + sep.join(head) + end]
    if markdown:
        lines.append("|" + "|".join("---" for _ in head) + "|")
    for year, pairs in stats.items():
        for label, s in pairs.items():
            row = [
                str(year),
                label,
                f"{s['signed_mean']:+.2f}",
                f"{s['p50']:.2f}",
                f"{s['p90']:.2f}",
                f"{s['p99']:.2f}",
                f"{s['pct_gt_5']:.1f}%",
                f"{s['pct_gt_20']:.1f}%",
            ]
            lines.append(bar + sep.join(row) + end)
    return "\n".join(lines)


def render_concentration(conc: dict) -> str:
    """Human-readable summary of where each spread's wide hours concentrate."""
    lines = []
    for year, pairs in conc.items():
        for label, c in pairs.items():
            if not c.get("n"):
                lines.append(f"{year} {label}: no |spread|>$20 hours")
                continue
            seasons = ", ".join(f"{s} {v:.0f}%" for s, v in c["seasons"].items())
            hod = ", ".join(f"{h:02d}:00" for h in c["top_hod"])
            lines.append(
                f"{year} {label}: {c['n']} wide hours, {c['pos_share']:.0f}% "
                f"first-zone-dear; by season [{seasons}]; top HB hours [{hod}]"
            )
    return "\n".join(lines)
