"""soco-74 zero-LP probe: can SOCO's own EIA-923 Page-5 receipts identify a sunk (take-or-pay) coal share?

Reads the committed ``data/raw/coal-receipts`` (Page 5, Purchase Type) and ``data/raw/coal-stocks`` corpora for
the eight SOCO coal plants and prints, per plant-year: contract (C/NC/T) and spot (S) tons, contract share,
delivered $/MMBtu by purchase type, December stock, implied burn (receipts - delta stock), and the
contract-tons / burn ratio. Also prints the year-on-year delta test (delta contract tons vs delta burn).

Record: docs/handoffs/r-soco/FINDING-soco-74-2026-09-27.md. No LP, no ScenarioConfig field touched.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

PLANTS = {3: "Barry", 26: "Gaston", 641: "Crist", 703: "Bowen", 6002: "Miller",
          6052: "Wansley", 6073: "Daniel", 6257: "Scherer"}
CONTRACT = ("C", "NC", "T")  # scripts/data/derive_coal_takeorpay.py _CONTRACT_CODES


def contract_table() -> pd.DataFrame:
    """Return the per plant-year contract/spot/stock/burn table for SOCO's coal plants."""
    r = pd.concat(pd.read_csv(p, low_memory=False)
                  for p in sorted(glob.glob(str(RAW_DATA_DIR / "coal-receipts" / "coal_receipts_*.csv"))))
    r = r[r["Plant Id"].isin(PLANTS)].copy()
    r["mm"] = r.QUANTITY * r["Average Heat Content"]
    r["c"] = pd.to_numeric(r.FUEL_COST, errors="coerce") * r.mm / 100.0  # FUEL_COST is cents/MMBtu
    r["pt"] = r["Purchase Type"].astype(str).str.strip()
    s = pd.concat(pd.read_csv(p, low_memory=False)
                  for p in sorted(glob.glob(str(RAW_DATA_DIR / "coal-stocks" / "coal_stocks_*.csv"))))
    s = s[s["Plant Id"].isin(PLANTS)].copy()
    s["dec"] = pd.to_numeric(s["Quantity December"], errors="coerce")
    dec = s.groupby(["Plant Id", "YEAR"]).dec.sum(min_count=1)
    rows = []
    for (pid, y), g in r.groupby(["Plant Id", "YEAR"]):
        isc = g.pt.isin(CONTRACT)
        C, S = g.loc[isc, "QUANTITY"].sum(), g.loc[g.pt == "S", "QUANTITY"].sum()
        pc = g.loc[isc, "c"].sum() / g.loc[isc, "mm"].sum() if isc.any() else np.nan
        ps = g.loc[g.pt == "S", "c"].sum() / g.loc[g.pt == "S", "mm"].sum() if (g.pt == "S").any() else np.nan
        d1, d0 = dec.get((pid, y), np.nan), dec.get((pid, y - 1), np.nan)
        burn = C + S - (d1 - d0)
        rows.append(dict(plant=PLANTS[pid], year=y, contract_Mt=C / 1e6, spot_Mt=S / 1e6, share=C / (C + S),
                         contract_usd_mmbtu=pc, spot_usd_mmbtu=ps, stock_dec_Mt=d1 / 1e6, burn_Mt=burn / 1e6,
                         contract_over_burn=C / burn if burn > 0 else np.nan))
    return pd.DataFrame(rows).sort_values(["plant", "year"])


def main() -> None:
    """Print the table, the fleet totals and the delta test."""
    d = contract_table()
    pd.set_option("display.width", 250)
    print(d.round(2).to_string(index=False))
    print(d.groupby("year")[["contract_Mt", "spot_Mt", "burn_Mt"]].sum(min_count=1).round(2))
    d["dC"] = d.groupby("plant").contract_Mt.diff()
    d["dB"] = d.groupby("plant").burn_Mt.diff()
    x = d.dropna(subset=["dC", "dB"])
    x = x[~x.plant.isin(["Crist", "Wansley"])]  # gas conversion / no-contract years
    print(f"delta test: corr(dC, dB) = {np.corrcoef(x.dC, x.dB)[0, 1]:.3f}  n = {len(x)}")


if __name__ == "__main__":
    main()
