"""Derive each CC_REGULAR plant's committed-tranche % from observed data.

The committed tranche is a combined cycle's minimum stable load once started —
the most-efficient base slice that bids at the plant's full heat rate, below the
economic (part-load) and peaking (duct-fire) tranches. Its size (``pct_mc`` /
the CSV ``Pct_Committed``) is currently a coarse assumed value (clustered at
20/25/45/55). This script grounds it per plant by measuring each combined
cycle's minimum stable output directly from EPA CAMPD/CEMS hourly gross output
for Jan-July 2023, the window the unit-level outage extract
(``data/raw/reference/tx-jan-aug23-unit-outages.csv``) covers, so the *available* capacity
at each hour is known (nameplate minus the units the extract reports out for
maintenance). Without that correction a plant running its remaining units while
one is in outage would look like it is running below its true minimum.

Method, per CC_REGULAR plant:

  1. CAMPD gross load is summed across the plant's units per hour and scaled to
     **net** by the plant's parasitic factor (so the committed % is in the same
     grid-MW basis the dispatch model produces).
  2. Available capacity per hour = nameplate x the unit-outage availability
     multiplier (:func:`market_sim.data.outages.unit_outage_derate_factors`),
     i.e. nameplate net of the units the extract reports in maintenance.
  3. "Online / committed" hours are those where net output exceeds
     :data:`_ONLINE_FRAC` of available capacity (a low bar that admits a single
     unit at part load while rejecting sensor noise and ramp-through-zero).
  4. The available capacity factor over committed hours is summarized by
     percentiles. The committed-tranche % is the **P5** of that distribution:
     the minimum stable load the plant holds at when backed down, excluding
     brief ramp transients (the absolute minimum / P0).

The committed % is expressed as a percent of nameplate (available-capacity
basis). The script prints the full percentile distribution and the committed
(online) fraction so the choice of P5 is transparent. It writes the per-plant
table to ``data/raw/_processed-legacy/cc_committed_pct.csv``; the model constant
``fleet.CC_REGULAR_COMMITTED_PCT_BY_PLANT`` is populated from it and overrides
the CSV ``Pct_Committed`` when ``config.cc_committed_per_plant`` is set (the
economic tranche absorbs the difference so the tranche split still sums to 100%).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_campd_bins  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

# Jan-July 2023 on the model's non-leap 8760 clock: the window the unit-level
# outage extract covers (Jan-Aug), trimmed to whole months ending July 31.
_DAYS_THROUGH_JULY: int = 31 + 28 + 31 + 30 + 31 + 30 + 31  # 212
_WINDOW_END_HOUR: int = _DAYS_THROUGH_JULY * 24  # 5088
_YEAR: int = 2023

# An hour counts as "online / committed" when net output clears this fraction
# of the hour's available capacity. Low enough to admit one unit of a
# multi-unit plant idling at part load, high enough to reject CEMS sensor
# noise and the single-hour ramp through zero on start/stop.
_ONLINE_FRAC: float = 0.05

# Percentile of the committed-hour available-CF distribution taken as the
# committed-tranche %. P5 (not the absolute minimum) discards isolated
# ramp-transient hours while still capturing the minimum stable load.
_FLOOR_PCTILE: int = 5

_OUT_CSV: Path = PROCESSED_DIR / "cc_committed_pct.csv"


def _parasitic_factor_map() -> dict[int, float]:
    """Return ``{plant_id: net/gross factor}`` from the derived artifact."""
    path = PROCESSED_DIR / "parasitic_load_factors.parquet"
    if not path.exists():
        return {}
    return campd.pooled_factor_map(pd.read_parquet(path))


def main() -> None:
    """Derive and print the per-plant CC_REGULAR committed floor."""
    bins = load_campd_bins(ScenarioConfig().campd_bins_path)
    cc = bins[bins["Plant_Group"] == "CC_REGULAR"]
    nameplate = {
        int(c): float(m)
        for c, m in zip(cc["Plant_Code"], cc["capacity_mw"])
        if m and m > 0
    }
    names = {int(c): str(n) for c, n in zip(cc["Plant_Code"], cc["Plant_Name"])}

    factors = _parasitic_factor_map()
    derate = unit_outage_derate_factors(_YEAR)  # {(code, group): (8760,) avail}

    df = campd.load_campd_hourly(["TX"], [_YEAR])
    net = campd.plant_hourly_net(df, factors, _YEAR)  # {code: (8760,) net MW}

    rows: list[dict] = []
    for code, cap in sorted(nameplate.items()):
        series = net.get(code)
        if series is None:
            rows.append(
                {"plant_code": code, "name": names.get(code, ""), "status": "no_campd"}
            )
            continue
        net_win = series[:_WINDOW_END_HOUR]
        avail_mult = derate.get((code, "CC_REGULAR"), np.ones(len(series)))
        avail_cap = cap * avail_mult[:_WINDOW_END_HOUR]
        # Available capacity factor; guard the few hours a plant is fully
        # outaged (avail_cap == 0) — those are offline by construction.
        with np.errstate(divide="ignore", invalid="ignore"):
            acf = np.where(avail_cap > 0.0, net_win / avail_cap, 0.0)
        online = (avail_cap > 0.0) & (net_win > _ONLINE_FRAC * avail_cap)
        n_online = int(online.sum())
        if n_online < 24:  # under a day of run time — no reliable floor
            rows.append(
                {
                    "plant_code": code,
                    "name": names.get(code, ""),
                    "status": "rarely_online",
                    "online_hours": n_online,
                    "window_hours": _WINDOW_END_HOUR,
                }
            )
            continue
        acf_on = acf[online]
        pctiles = {p: float(np.percentile(acf_on, p)) for p in (0, 1, 5, 10, 25, 50)}
        rows.append(
            {
                "plant_code": code,
                "name": names.get(code, ""),
                "status": "ok",
                "nameplate_mw": round(cap, 1),
                "online_hours": n_online,
                "window_hours": _WINDOW_END_HOUR,
                "online_frac": round(n_online / _WINDOW_END_HOUR, 3),
                "p0": round(100 * pctiles[0], 1),
                "p1": round(100 * pctiles[1], 1),
                "p5": round(100 * pctiles[5], 1),
                "p10": round(100 * pctiles[10], 1),
                "p25": round(100 * pctiles[25], 1),
                "median": round(100 * pctiles[50], 1),
                "committed_pct": round(100 * pctiles[_FLOOR_PCTILE], 1),
            }
        )

    out = pd.DataFrame(rows)
    ok = out[out["status"] == "ok"].sort_values("plant_code")
    _OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    ok.to_csv(_OUT_CSV, index=False)

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    pd.set_option("display.max_rows", 100)
    print(
        f"\nCC_REGULAR committed-tranche % derivation — Jan-July {_YEAR} "
        f"(CAMPD net vs available capacity)\n"
    )
    cols = [
        "plant_code",
        "name",
        "nameplate_mw",
        "online_frac",
        "p0",
        "p1",
        "p5",
        "p10",
        "p25",
        "median",
        "committed_pct",
    ]
    print(ok[cols].to_string(index=False))
    skipped = out[out["status"] != "ok"]
    if len(skipped):
        print("\nskipped plants (keep CSV Pct_Committed):")
        print(skipped[["plant_code", "name", "status"]].to_string(index=False))
    print(
        f"\ncommitted % = P{_FLOOR_PCTILE} of available-CF over committed "
        f"hours (committed = net > {_ONLINE_FRAC:.0%} of available capacity)"
    )
    print(f"wrote {_OUT_CSV}")


if __name__ == "__main__":
    main()
