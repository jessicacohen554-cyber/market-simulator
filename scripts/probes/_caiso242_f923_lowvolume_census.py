"""caiso-242 — census of the EIA-923 LOW-VOLUME plant-month price pathology.

NO LP, NO SOLVE, NOTHING ARMED. Reads the committed
``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`` only.

**The defect, found while measuring the caiso-242 basis object.** CAISO's 2025
capacity-weighted delivered gas for ``CC_REGULAR`` reads **$20.78/MMBtu in
November** against ``CT_PEAKER``'s $6.08 and a CA-composite citygate of $3.20.
The cause is one EIA-923 row: plant 55077 (NV) reports **$96.161/MMBtu on a
quantity of 5,234** in 2025-11 and **$67.900 on 7,808** in 2025-12, against
115,774-674,308 in every other month of the same year. A reported cost divided
by a near-zero volume is a fixed/reservation charge, **not a marginal delivered
fuel price** -- but ``apply_plant_monthly_fuel_prices`` consumes it as one, and
the state/zone gap-fill then propagates it to plants that reported nothing.

This probe sizes the pathology, ISO-agnostically, on its own source:

  * per plant-year, the plant's own median monthly quantity;
  * plant-months whose quantity is a small fraction of that median AND whose
    price is a large multiple of the plant's own volume-weighted annual price;
  * the resulting price outliers, by year, by state, and against the
    contemporaneous hub level.

It proposes NO threshold as a repair -- the counts are reported across a SWEEP
of candidate cuts precisely so the repair's form stays an owner decision rather
than a number chosen here (rule 5 [R-NO-MAGIC], rule 21 [R-DOF]).

Writes ``results/calibration/_caiso242_f923_lowvolume_census.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso242_f923_lowvolume_census.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

OUT = REPO / "results/calibration/_caiso242_f923_lowvolume_census.json"
YEARS = (2023, 2024, 2025)
#: Candidate quantity cuts (plant-month quantity / the plant-year's own median)
#: and price multiples (plant-month price / the plant-year's own
#: volume-weighted mean). Swept, not selected.
QTY_CUTS = (0.02, 0.05, 0.10, 0.20)
PRICE_MULTS = (2.0, 3.0, 5.0)


def main() -> None:
    from market_sim.data.eia923 import (
        EIA923_MONTHLY_COSTS_PATH,
        load_monthly_fuel_costs,
    )

    d = load_monthly_fuel_costs()
    d = d[d["year"].isin(YEARS) & (d["fuel_group"] == "Natural Gas")].copy()
    d = d[(d["quantity"] > 0) & d["price_per_mmbtu"].notna()]

    # the plant-year's OWN normal volume and OWN volume-weighted price
    g = d.groupby(["plant_id", "year"])
    d["qty_median"] = g["quantity"].transform("median")
    vw = g.apply(
        lambda s: np.average(s["price_per_mmbtu"], weights=s["quantity"]),
        include_groups=False,
    ).rename("vw_price")
    d = d.merge(vw, on=["plant_id", "year"], how="left")
    d["qty_frac"] = d["quantity"] / d["qty_median"].replace(0, np.nan)
    d["price_mult"] = d["price_per_mmbtu"] / d["vw_price"].replace(0, np.nan)

    out: dict = {
        "_provenance": {
            "session": "caiso-242",
            "source": str(Path(EIA923_MONTHLY_COSTS_PATH).relative_to(REPO)),
            "scope": "fuel_group == 'Natural Gas', years 2023-2025",
            "note": (
                "no LP, nothing armed; thresholds are SWEPT, none selected "
                "(rule 5 [R-NO-MAGIC] -- the repair's form is an owner decision)"
            ),
        },
        "totals": {
            "plant_month_rows": int(len(d)),
            "plants": int(d["plant_id"].nunique()),
            "price_p50": round(float(d["price_per_mmbtu"].median()), 4),
            "price_p99": round(float(d["price_per_mmbtu"].quantile(0.99)), 4),
            "price_max": round(float(d["price_per_mmbtu"].max()), 4),
        },
        "sweep": {},
        "worst_rows": [],
        "by_year": {},
    }
    for q in QTY_CUTS:
        for p in PRICE_MULTS:
            m = (d["qty_frac"] <= q) & (d["price_mult"] >= p)
            out["sweep"][f"qty<={q}_x_price>={p}"] = {
                "rows": int(m.sum()),
                "plants": int(d.loc[m, "plant_id"].nunique()),
                "median_price": round(float(d.loc[m, "price_per_mmbtu"].median()), 3)
                if m.any()
                else None,
                "max_price": round(float(d.loc[m, "price_per_mmbtu"].max()), 3)
                if m.any()
                else None,
                "share_of_that_plant_years_volume_pct": round(
                    float(
                        100.0
                        * d.loc[m, "quantity"].sum()
                        / max(float(d["quantity"].sum()), 1.0)
                    ),
                    4,
                )
                if m.any()
                else None,
            }

    worst = d.nlargest(20, "price_per_mmbtu")
    for _, r in worst.iterrows():
        out["worst_rows"].append(
            {
                "plant_id": int(r["plant_id"]),
                "state": str(r["state"]),
                "year": int(r["year"]),
                "month": int(r["month"]),
                "price_per_mmbtu": round(float(r["price_per_mmbtu"]), 3),
                "quantity": int(r["quantity"]),
                "plant_year_qty_median": int(r["qty_median"]),
                "qty_frac": round(float(r["qty_frac"]), 5),
                "plant_year_vw_price": round(float(r["vw_price"]), 3),
                "price_mult": round(float(r["price_mult"]), 2),
            }
        )
    for y in YEARS:
        sub = d[d["year"] == y]
        hi = sub[sub["price_per_mmbtu"] > 20.0]
        out["by_year"][y] = {
            "rows": int(len(sub)),
            "rows_over_20_usd_mmbtu": int(len(hi)),
            "plants_over_20": sorted(int(x) for x in hi["plant_id"].unique()),
            "ca_nv_rows_over_20": int(len(hi[hi["state"].isin(["CA", "NV"])])),
        }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
