"""Revenue-side audit for the joint FOM+scarcity protocol (plan §5 step 1).

Compares the Potomac Economics ERCOT State-of-the-Market published CT/CC net
revenues (the external identification source for the revenue side of the
retirement inequality — rule 13: compare, never pin) against a replica of the
SOM price-taker calculation computed from the repo's MEASURED hourly real-time
hub prices and daily Henry Hub gas, using the SOM's own stated assumptions
(2024 SOM footnote 48: CC heat rate 7.0 MMBtu/MWh, CT 10.5 MMBtu/MWh,
$4/MWh VOM, 10% total outage rate; price-taker — runs any hour it is
profitable).

Scope note (W2-P3 session constraint): the committed keeper bundles carry fit
summaries, not hourly price/dispatch arrays, and regenerating them would be a
multi-year calibration solve, which this session's mandate forbids. The
model-side screen revenue stack is therefore instrumented in the FORWARD 2x3
grid probes (scripts/run_fom_scarcity_grid.py) — the quantity the FOM bar is
actually compared against in a forecast — while this script establishes (a)
the published SOM benchmark table and (b) that the repo's measured price data
reproduces the SOM's price-taker arithmetic. In-sample years 2023-2025 only;
2022 and H1-2026 stay under full quarantine (rule 22).

Usage::

    python scripts/probes/fom_scarcity_revenue_audit.py \
        --out docs/handoffs/fom-scarcity-revenue-audit-2026-07-05.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

# Potomac Economics ERCOT SOM published CT/CC net revenues, $/kW-yr.
# 2023: 2023 SOM (Final 2024-06-06), Resource Adequacy §, p.75: CT $224-257,
#       CC $228-272 (ranges across locations; CONE ~$80-130).
# 2024: 2024 SOM (June 2025), §"Interpreting Single-Year Net Revenues": CT
#       net revenue averaged $68, CC $89, vs CONE $102-106 (CT) / $116-121
#       (CC). (The report text prints "per MWh"; the section's Figure 56 axis
#       and every neighbouring usage is $/kW-year — treated as a units typo.)
# 2025: 2025 SOM (June 2026), Figure 56 §2 "CONE vs Net Revenue", p.102: CT
#       $52.59, CC $82.96, vs PUCT planning CONE $140 (legacy $105).
SOM_NET_REVENUE = {
    2023: {"gas_ct": (224.0, 257.0), "gas_cc": (228.0, 272.0)},
    2024: {"gas_ct": (68.0, 68.0), "gas_cc": (89.0, 89.0)},
    2025: {"gas_ct": (52.59, 52.59), "gas_cc": (82.96, 82.96)},
}

# SOM price-taker assumptions (2024 SOM footnote 48).
SOM_ASSUMPTIONS = {
    "gas_ct": {"heat_rate": 10.5, "vom": 4.0},
    "gas_cc": {"heat_rate": 7.0, "vom": 4.0},
}
SOM_OUTAGE_RATE = 0.10

YEARS = (2023, 2024, 2025)  # in-sample only; 2022 / H1-2026 quarantined


def _daily_gas_by_hour(year: int, hh: pd.DataFrame) -> np.ndarray:
    """Return an (8760,) Henry Hub $/MMBtu series, daily prices ffilled."""
    days = pd.date_range(f"{year}-01-01", periods=366, freq="D")
    s = hh.set_index("date")["price_usd_mmbtu"].reindex(days).ffill().bfill()
    return s.to_numpy()[np.arange(8760) // 24]


def price_taker_net_revenue(
    rt: np.ndarray, gas: np.ndarray, heat_rate: float, vom: float
) -> float:
    """SOM-replica price-taker net revenue in $/kW-yr."""
    # One NaN hour per year (DST fall-back) in the measured series: a missing
    # price earns nothing.
    margin = np.nan_to_num(rt - (heat_rate * gas + vom), nan=0.0)
    return float(np.maximum(margin, 0.0).sum()) * (1.0 - SOM_OUTAGE_RATE) / 1000.0


def main(argv: list[str] | None = None) -> None:
    """Compute the audit table and write JSON + a printed markdown table."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=None, help="JSON output path.")
    args = p.parse_args(argv)

    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_daily.csv")
    hh["date"] = pd.to_datetime(hh["date"])

    rows = []
    for year in YEARS:
        rt = lmp.loc[lmp["year"] == year].sort_values("hour")["rt"].to_numpy()
        assert rt.size == 8760, f"{year}: {rt.size} hours"
        gas = _daily_gas_by_hour(year, hh)
        for fuel, a in SOM_ASSUMPTIONS.items():
            replica = price_taker_net_revenue(rt, gas, a["heat_rate"], a["vom"])
            lo, hi = SOM_NET_REVENUE[year][fuel]
            mid = 0.5 * (lo + hi)
            rows.append(
                {
                    "year": year,
                    "class": fuel,
                    "som_published_kw_yr": [lo, hi],
                    "replica_measured_prices_kw_yr": round(replica, 2),
                    "replica_over_som_mid": round(replica / mid, 3) if mid else None,
                }
            )

    print("| Year | Class | SOM published $/kW-yr | Replica (measured RT+HH) | ratio |")
    print("|---|---|---|---:|---:|")
    for r in rows:
        lo, hi = r["som_published_kw_yr"]
        som = f"{lo:g}" if lo == hi else f"{lo:g}-{hi:g}"
        print(
            f"| {r['year']} | {r['class']} | {som} | "
            f"{r['replica_measured_prices_kw_yr']} | {r['replica_over_som_mid']} |"
        )

    payload = {
        "som_net_revenue_kw_yr": {str(y): v for y, v in SOM_NET_REVENUE.items()},
        "som_assumptions": SOM_ASSUMPTIONS,
        "outage_rate": SOM_OUTAGE_RATE,
        "rows": rows,
        "notes": (
            "Replica uses ERCOT hub RT hourly prices "
            "(data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet) and "
            "daily Henry Hub ($/MMBtu, no basis adjustment); SOM uses "
            "generation-weighted settlement point prices and includes AS "
            "sales, so the replica is expected to sit modestly below SOM in "
            "AS-rich years."
        ),
    }
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=1))
        print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
