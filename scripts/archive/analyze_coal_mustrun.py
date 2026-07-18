"""Coal must-run floors and seasonal outage patterns from CAMPD CEMS.

For each coal plant — split into mine-mouth lignite and railed PRB by the
model's :data:`market_sim.data.fleet.COAL_PLANT_SUPPLY` mapping — this derives
two things the dispatch model needs to tune:

1. **Must-run floor.** The minimum capacity factor a plant holds while
   committed (i.e. excluding hours it is fully offline). Reported as robust
   percentiles (P5 / P10) of the committed-hour CF distribution rather than
   the absolute minimum, so single-hour ramp transients do not set the floor.
   The P10 of committed CF is the candidate "true must-run %". Min stable load
   is also given as a share of the plant's own demonstrated max output, which
   is robust to nameplate mismatch.

2. **Seasonal outage pattern.** Multi-day offline events, classified into the
   model's seasons (summer 6-9, shoulder 3-5/10-11, winter 12-2). Events that
   recur in the same season across every analyzed year are surfaced as
   universal-rule candidates — e.g. "Plant A is offline ~X days every shoulder
   season" — for the seasonal availability machinery.

CAMPD provides facility- (plant-) level hourly data, so this reports per plant;
multi-unit plants' partial (single-unit) outages cannot be isolated and will
lower the committed-CF floor — the outage table helps spot those plateaus.

Usage:
    python scripts/archive/analyze_coal_mustrun.py --iso ERCOT --years 2023 2024
    python scripts/archive/analyze_coal_mustrun.py --states TX --years 2023 --supply lignite
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.data import campd  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.coal import COAL_PLANT_SUPPLY  # noqa: E402

# EIA-923 fuel codes burned by coal-class units.
_COAL_FUELS: frozenset[str] = frozenset({"SUB", "BIT", "LIG", "ANT", "RC", "WC", "SC"})
# A plant below this coal share of net generation, or with a non-steam prime
# mover (a co-located gas turbine / CC), is "mixed": facility-level CEMS sums
# its non-coal units into the gross load, so its coal must-run floor cannot be
# isolated from this extract and is excluded from the headline stats.
_MIN_COAL_SHARE: float = 0.90

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("analyze_coal_mustrun")

PROCESSED_DIR = REPO / "inputs" / "processed"
REGISTRY_PATH = REPO / "inputs" / "master-plant-registry.csv"

# Model seasons (1-based months); mirrors fleet._SUMMER_MONTHS / _CC_SHOULDER.
_SEASON_OF_MONTH: dict[int, str] = {
    12: "winter",
    1: "winter",
    2: "winter",
    3: "shoulder",
    4: "shoulder",
    5: "shoulder",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "summer",
    10: "shoulder",
    11: "shoulder",
}
_SEASON_ORDER: tuple[str, ...] = ("winter", "shoulder", "summer")


def _season(month: int) -> str:
    return _SEASON_OF_MONTH[int(month)]


def _print_table(rows: list[tuple]) -> None:
    widths = [max(len(str(r[c])) for r in rows) for c in range(len(rows[0]))]
    for row in rows:
        print("    " + "  ".join(str(row[c]).ljust(widths[c]) for c in range(len(row))))


def _outage_events(
    grid: pd.DataFrame,
    online_mw: float,
    min_days: float,
) -> list[dict]:
    """Return multi-day offline events for one plant-year's hourly grid.

    An event is a contiguous run of hours with gross load at or below
    ``online_mw`` lasting at least ``min_days``. Each is dated by its first
    and last offline hour and seasoned by its midpoint.
    """
    gross = grid["gross_mw"].to_numpy()
    ts = grid.index
    offline = gross <= online_mw
    events: list[dict] = []
    i, n = 0, len(gross)
    min_hours = int(min_days * 24)
    while i < n:
        if not offline[i]:
            i += 1
            continue
        j = i
        while j < n and offline[j]:
            j += 1
        if (j - i) >= min_hours:
            mid = ts[i + (j - i) // 2]
            events.append(
                {
                    "start": ts[i].date().isoformat(),
                    "end": ts[j - 1].date().isoformat(),
                    "days": round((j - i) / 24.0, 1),
                    "season": _season(mid.month),
                }
            )
        i = j
    return events


def _must_run_stats(
    grid: pd.DataFrame,
    nameplate: float,
    online_mw: float,
) -> dict:
    """Return committed-hour CF percentiles and min-stable-load metrics."""
    gross = grid["gross_mw"].to_numpy()
    committed = gross[gross > online_mw]
    total_hours = len(gross)
    if committed.size < 10:
        return {"online_hours": int(committed.size), "online_share": 0.0}
    p95_out = float(np.percentile(committed, 95))
    cf = committed / nameplate if nameplate > 0 else committed / p95_out
    return {
        "online_hours": int(committed.size),
        "online_share": round(committed.size / total_hours, 3),
        "cf_p5": round(float(np.percentile(cf, 5)), 3),
        "cf_p10": round(float(np.percentile(cf, 10)), 3),
        "cf_p50": round(float(np.percentile(cf, 50)), 3),
        "cf_p95": round(float(np.percentile(cf, 95)), 3),
        "minload_pct_of_max": round(float(np.percentile(committed, 10)) / p95_out, 3)
        if p95_out > 0
        else 0.0,
    }


def _coal_mix(generation: pd.DataFrame, years: list[int]) -> dict[int, dict]:
    """Return ``{plant_id: {coal_share, prime_movers, mixed}}`` from EIA-923.

    Flags plants whose CAMPD facility gross blends non-coal units — a low coal
    share of net generation or a non-steam prime mover (co-located GT/CC) — so
    their facility-level must-run floor can be set aside.
    """
    sub = generation[generation["year"].isin(years)]
    out: dict[int, dict] = {}
    for code, grp in sub.groupby("plant_id"):
        total = float(grp["netgen_annual_mwh"].sum())
        if total <= 0:
            continue
        is_coal = grp["fuel_type"].astype(str).str.upper().isin(_COAL_FUELS)
        coal_gen = float(grp[is_coal]["netgen_annual_mwh"].sum())
        pms = sorted(
            grp.loc[grp["netgen_annual_mwh"] != 0, "prime_mover"]
            .astype(str)
            .str.upper()
            .unique()
        )
        share = coal_gen / total
        out[int(code)] = {
            "coal_share": round(share, 3),
            "prime_movers": "+".join(pms),
            "mixed": bool(share < _MIN_COAL_SHARE or pms != ["ST"]),
        }
    return out


def _analyze(
    df: pd.DataFrame,
    years: list[int],
    supply_types: list[str],
    online_frac: float,
    min_days: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return ``(floors, events)`` frames for the requested coal supply types."""
    reg = pd.read_csv(REGISTRY_PATH).set_index("plantid")
    mix = _coal_mix(load_monthly_generation(), years)
    floors_rows: list[dict] = []
    event_rows: list[dict] = []

    plants = [
        (code, sup) for code, sup in COAL_PLANT_SUPPLY.items() if sup in supply_types
    ]
    for code, supply in sorted(plants, key=lambda x: (x[1], x[0])):
        name = (
            str(reg.loc[code, "plant_name"]) if code in reg.index else f"plant {code}"
        )
        nameplate = (
            float(reg.loc[code, "nameplate_capacity_mw"])
            if code in reg.index and pd.notna(reg.loc[code, "nameplate_capacity_mw"])
            else 0.0
        )
        # Pool committed-hour gross across years for the must-run floor; collect
        # outage events per year for the seasonal-recurrence pass.
        pooled_grids = []
        for year in years:
            grid = campd.plant_hourly_grid(df, code, year)
            if grid.empty:
                continue
            np_used = (
                nameplate
                if nameplate > 0
                else float(np.percentile(grid["gross_mw"], 99))
            )
            online_mw = max(1.0, online_frac * np_used)
            for ev in _outage_events(grid, online_mw, min_days):
                event_rows.append(
                    {
                        "plant_code": code,
                        "name": name,
                        "supply": supply,
                        "year": year,
                        **ev,
                    }
                )
            pooled_grids.append((grid, np_used, online_mw))

        if not pooled_grids:
            continue
        combined = pd.concat([g for g, _, _ in pooled_grids])
        np_used = pooled_grids[0][1]
        online_mw = pooled_grids[0][2]
        stats = _must_run_stats(combined, np_used, online_mw)
        m = mix.get(
            code, {"coal_share": float("nan"), "prime_movers": "?", "mixed": False}
        )
        floors_rows.append(
            {
                "plant_code": code,
                "name": name,
                "supply": supply,
                "nameplate_mw": round(nameplate, 1),
                "cap_mw_used": round(np_used, 1),
                "nameplate_source": "registry" if nameplate > 0 else "p99_observed",
                "coal_share": m["coal_share"],
                "prime_movers": m["prime_movers"],
                "mixed": m["mixed"],
                **stats,
            }
        )

    return pd.DataFrame(floors_rows), pd.DataFrame(event_rows)


def _print_report(
    floors: pd.DataFrame,
    events: pd.DataFrame,
    years: list[int],
) -> None:
    """Print must-run floors, seasonal outage totals, and recurring rules."""
    for supply in ("lignite", "prb"):
        fl = floors[floors["supply"] == supply]
        if fl.empty:
            continue
        label = "MINE-MOUTH LIGNITE" if supply == "lignite" else "PRB (railed)"
        print(
            f"\n{'=' * 78}\n  {label} COAL — must-run floor "
            f"({', '.join(map(str, years))})\n{'=' * 78}"
        )
        rows = [
            (
                "plant",
                "code",
                "MW",
                "coal%",
                "pm",
                "online%",
                "CF P5",
                "CF P10",
                "CF P50",
                "minLoad%max",
            )
        ]
        for _, r in fl.sort_values(
            ["mixed", "cap_mw_used"], ascending=[True, False]
        ).iterrows():
            cap = (
                f"{r['nameplate_mw']:.0f}"
                if r["nameplate_source"] == "registry"
                else f"~{r['cap_mw_used']:.0f}"
            )
            name = r["name"][:24] + (" *" if r["mixed"] else "")
            rows.append(
                (
                    name,
                    str(r["plant_code"]),
                    cap,
                    f"{r['coal_share'] * 100:.0f}",
                    r["prime_movers"],
                    f"{r.get('online_share', 0) * 100:.0f}",
                    f"{r.get('cf_p5', float('nan')):.2f}",
                    f"{r.get('cf_p10', float('nan')):.2f}",
                    f"{r.get('cf_p50', float('nan')):.2f}",
                    f"{r.get('minload_pct_of_max', float('nan')):.2f}",
                )
            )
        _print_table(rows)
        reliable = fl[~fl["mixed"]]
        if len(reliable):
            print(
                f"    coal-only median: CF P10={reliable['cf_p10'].median():.2f}, "
                f"minLoad%max={reliable['minload_pct_of_max'].median():.2f}  "
                f"(CF P10 of committed hours = candidate true must-run %)"
            )
        if fl["mixed"].any():
            print(
                "    * mixed plant (co-located gas units in facility CEMS) — "
                "coal floor not isolable from this extract; excluded from median."
            )

    if events.empty:
        print("\n  No multi-day outage events detected.")
        return

    print(
        f"\n{'=' * 78}\n  SEASONAL OUTAGE PATTERN — multi-day offline events"
        f"\n{'=' * 78}"
    )
    rows = [("plant", "supply", "year", "season", "start", "end", "days")]
    for _, e in events.sort_values(["supply", "plant_code", "start"]).iterrows():
        rows.append(
            (
                e["name"][:24],
                e["supply"],
                str(e["year"]),
                e["season"],
                e["start"],
                e["end"],
                f"{e['days']:.0f}",
            )
        )
    _print_table(rows)

    # Universal-rule candidates: a plant with a multi-day outage in the same
    # season in every analyzed year.
    print(
        f"\n{'=' * 78}\n  RECURRING SEASONAL OUTAGES (universal-rule candidates)"
        f"\n{'=' * 78}"
    )
    n_years = len({e for e in years})
    found = False
    for (code, season), grp in events.groupby(["plant_code", "season"]):
        yrs = sorted(grp["year"].unique())
        if len(yrs) < n_years or n_years < 2:
            continue
        found = True
        name = grp["name"].iloc[0]
        avg_days = grp.groupby("year")["days"].sum().mean()

        def _per_year(y: int) -> str:
            gy = grp[grp.year == y]
            top = gy.loc[gy["days"].idxmax()]
            return (
                f"{y}: {gy['days'].sum():.0f}d total, "
                f"longest {top['start']}→{top['end']}"
            )

        spans = "; ".join(_per_year(y) for y in yrs)
        print(
            f"    • {name} ({code}, {grp['supply'].iloc[0]}): ~{avg_days:.0f} "
            f"days offline every {season} season  [{spans}]"
        )
    if not found:
        print("    (none recur in the same season across all analyzed years)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", default=None)
    parser.add_argument("--states", nargs="+", default=None)
    parser.add_argument("--years", nargs="+", type=int, required=True)
    parser.add_argument(
        "--supply",
        choices=["lignite", "prb", "all"],
        default="all",
        help="Coal supply type(s) to report (default all).",
    )
    parser.add_argument(
        "--online-frac",
        type=float,
        default=0.05,
        help="Gross load below this fraction of capacity counts as offline.",
    )
    parser.add_argument(
        "--min-outage-days",
        type=float,
        default=2.0,
        help="Minimum contiguous offline span (days) to log as an outage.",
    )
    parser.add_argument("--no-csv", action="store_true")
    args = parser.parse_args()

    states = args.states or list(campd.states_for_iso(args.iso or ""))
    if not states:
        parser.error("supply --states or an --iso with a known state mapping")
    supply_types = ["lignite", "prb"] if args.supply == "all" else [args.supply]

    df = campd.load_campd_hourly(states, args.years)
    if df.empty:
        logger.error("no CAMPD extracts found for the requested states/years")
        return

    floors, events = _analyze(
        df, args.years, supply_types, args.online_frac, args.min_outage_days
    )
    _print_report(floors, events, args.years)

    if not args.no_csv:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        floors.to_csv(PROCESSED_DIR / "coal_mustrun_floors.csv", index=False)
        events.to_csv(PROCESSED_DIR / "coal_outage_events.csv", index=False)
        logger.info(
            "wrote %s and %s",
            PROCESSED_DIR / "coal_mustrun_floors.csv",
            PROCESSED_DIR / "coal_outage_events.csv",
        )


if __name__ == "__main__":
    main()
