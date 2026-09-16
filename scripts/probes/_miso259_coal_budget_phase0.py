#!/usr/bin/env python3
"""Phase-0 reproduction: the MISO coal-inventory energy budget, six years, zero LP.

Rebuilds the ``FINDING-miso258-coal-stock-falsification-2026-09-14.md`` budget
table from committed bytes only, so the successor session can confirm the
G-FOOTPRINT premise before spending an LP (rule 29 ``[R-SCREEN]`` clause 0).

Every quantity that sizes year *Y*'s budget PREDATES year *Y* (rule 13
``[R-MEASURED]``, and the G-PIN stop gate):

* opening stock  = the footprint's December ending stock of *Y-1*
  (``coal-stocks``, :func:`market_sim.data.coal_stocks.opening_stock_tons`)
* delivery rate  = mean annual receipts over *Y-2* and *Y-1*
  (``coal-receipts``, :func:`market_sim.data.coal_receipts.prior_years_delivery_rate`)
* heat content   = quantity-weighted MMBtu/ton over those same prior years
* fleet heat rate = the measured CAMPD marginal-heat-rate summary's ``base_hr``

The MODEL side is read off the keeper's own committed ``hourly/`` class
sidecars, not re-solved.

Usage:
    python scripts/probes/_miso259_coal_budget_phase0.py
    python scripts/probes/_miso259_coal_budget_phase0.py --plant-set union
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.coal_receipts import (  # noqa: E402
    CONTRACT_PURCHASE_TYPES,
    prior_years_delivery_rate,
)
from market_sim.data.coal_stocks import opening_stock_tons  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "MISO"
KEEPER = REPO / "results" / "calibration" / "miso255_sil_keeper"
HR_SUMMARY = REPO / "data" / "raw" / "reference" / "miso_campd_marginal_hr_summary.csv"
YEARS = (2020, 2021, 2022, 2023, 2024, 2025)


def coal_plant_ids(year: int) -> set[int]:
    """Coal plant ids in the keeper's own committed bench part for ``year``."""
    part = ba.load_bench_part(BENCH / f"{year}.json.gz")
    return {
        int(str(k).split(":")[0])
        for k, v in part["bench"]["plants"].items()
        if "COAL" in str(v.get("group", "")).upper()
    }


def union_coal_plant_ids() -> set[int]:
    """Coal plant ids appearing in any scored year (the 67-plant model fleet)."""
    out: set[int] = set()
    for y in YEARS:
        out |= coal_plant_ids(y)
    return out


def model_coal_twh(year: int) -> float:
    """Keeper P1 coal energy for ``year``, from the committed class sidecar."""
    df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    sel = df[(df["pass"] == "P1") & df["klass"].str.upper().str.contains("COAL")]
    return float(sel["mw"].sum()) / 1e6


def fleet_heat_rate() -> tuple[float, int]:
    """Measured coal-fleet ``base_hr`` (MMBtu/MWh) and the unit count behind it."""
    rows = list(csv.DictReader(HR_SUMMARY.open()))
    coal = [r for r in rows if "COAL" in str(r.get("klass", r.get("class", ""))).upper()]
    if not coal:
        raise SystemExit(f"no coal rows in {HR_SUMMARY}")
    num = 0.0
    den = 0
    for r in coal:
        n = int(float(r.get("n_units", r.get("n", 1)) or 1))
        num += float(r["base_hr"]) * n
        den += n
    return num / den, den


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--plant-set",
        choices=("per-year", "union"),
        default="per-year",
        help="footprint definition: the year's own coal fleet, or the six-year union",
    )
    ap.add_argument(
        "--purchase-types",
        choices=("all", "contract"),
        default="all",
        help="delivery-rate construction: every receipt, or contracted tonnage only",
    )
    ap.add_argument("--json-out", type=Path, default=None)
    args = ap.parse_args()

    hr, n_units = fleet_heat_rate()
    ptypes = CONTRACT_PURCHASE_TYPES if args.purchase_types == "contract" else None
    union = union_coal_plant_ids()
    print(
        f"coal fleet heat rate {hr:.3f} MMBtu/MWh over {n_units} CAMPD units; "
        f"footprint = {args.plant_set} ({len(union)} plants in the six-year union); "
        f"delivery rate = {args.purchase_types}"
    )
    print(
        f"{'yr':>5} {'open Mt':>9} {'rate Mt':>9} {'HHV':>7} "
        f"{'avail TWh':>10} {'MODEL':>8} {'slack':>8}  verdict"
    )
    records = []
    for year in YEARS:
        ids = union if args.plant_set == "union" else coal_plant_ids(year)
        open_tons = opening_stock_tons(ids, year)
        rate = prior_years_delivery_rate(ids, year, purchase_types=ptypes)
        model = model_coal_twh(year)
        if open_tons is None or rate is None:
            print(f"{year:>5}  UNAVAILABLE (stock={open_tons}, rate={rate})")
            continue
        avail_mmbtu = (open_tons + rate.tons_per_year) * rate.mmbtu_per_ton
        avail_twh = avail_mmbtu / hr / 1e6
        slack = avail_twh - model
        verdict = "BINDS" if slack < 0 else "inert"
        print(
            f"{year:>5} {open_tons / 1e6:>9.2f} {rate.tons_per_year / 1e6:>9.2f} "
            f"{rate.mmbtu_per_ton:>7.3f} {avail_twh:>10.1f} {model:>8.1f} "
            f"{slack:>+8.1f}  {verdict}"
        )
        records.append(
            {
                "year": year,
                "n_plants": len(ids),
                "opening_stock_mt": open_tons / 1e6,
                "delivery_rate_mt": rate.tons_per_year / 1e6,
                "rate_source_years": list(rate.source_years),
                "mmbtu_per_ton": rate.mmbtu_per_ton,
                "heat_rate_mmbtu_per_mwh": hr,
                "available_twh": avail_twh,
                "model_twh": model,
                "slack_twh": slack,
                "verdict": verdict,
            }
        )
    if args.json_out:
        args.json_out.write_text(json.dumps(records, indent=2), encoding="utf-8")
        print(f"wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
