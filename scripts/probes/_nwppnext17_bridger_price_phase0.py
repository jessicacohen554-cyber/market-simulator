"""NWPP-NEXT-17 phase 0 (zero LP): why keeper #20 idles Jim Bridger 8066 in Jun-Oct 2023.

Reads one solved leg (default: keeper #20's 2023 shard leg, extracted from commit
a54c7b97 with ``git archive a54c7b97 results/calibration/nwppnext16c_2023``) plus
committed raw data (EIA-923 Page 5 coal receipts, WEIM hourly ELAP prices,
NID pondage). Prints the tables of
``docs/records/nwpp/FINDING-nwppnext17-bridger-price-formation-phase0-2026-10-01.md``.

Usage: python scripts/probes/_nwppnext17_bridger_price_phase0.py [LEG_DIR]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

BRIDGER = 8066
YEAR = 2023
# CEMS gross-to-net monthly GWh, 2023 (FINDING-nwppnext14 §1 table).
CEMS_GWH = pd.Series(
    [906, 416, 294, 164, 345, 662, 1155, 1171, 892, 1267, 879, 960], index=range(1, 13)
)
FIXED_TRANCHES = ("mustrun", "committed")


def _month(hour: pd.Series) -> pd.Series:
    """Map an hour-of-year index to its calendar month (non-leap fixed clock)."""
    return (pd.Timestamp(f"{YEAR}-01-01") + pd.to_timedelta(hour, "h")).dt.month


def bridger_receipts(raw: Path) -> pd.DataFrame:
    """Return Bridger's monthly delivered coal price by mine from EIA-923 Page 5."""
    r = pd.read_csv(raw / f"coal-receipts/coal_receipts_{YEAR}.csv", low_memory=False)
    b = r[r["Plant Id"] == BRIDGER].copy()
    b["mmbtu"] = b.QUANTITY * b["Average Heat Content"]
    b["usd"] = b.mmbtu * pd.to_numeric(b.FUEL_COST, errors="coerce") / 100
    g = b.groupby(["MONTH", "Coalmine Name"])[["mmbtu", "usd"]].sum()
    return (g.usd / g.mmbtu).unstack().round(2)


def bridger_offer_vs_price(leg: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return Bridger's monthly offer/dual/LMP table and the NWPP-EAST unit frame."""
    u = pd.read_parquet(leg / f"hourly/unit_hourly_{YEAR}.parquet")
    b = u[u.plant_code == BRIDGER].copy()
    b["m"] = _month(b.hour)
    sysd = pd.read_parquet(leg / "system.parquet")
    east = sysd[sysd.zone == "NWPP-EAST"][["hour", "price"]]
    b = b.merge(east, on="hour")
    b["dual"] = b.red_cost - (b.mc - b.price)
    econ = b[~b.unit_id.str.endswith(FIXED_TRANCHES)]
    fixed = b[b.unit_id.str.endswith(FIXED_TRANCHES)]
    h = econ.drop_duplicates("hour")
    tab = pd.DataFrame(
        {
            "model_gwh": b.groupby("m").mw.sum() / 1e3,
            "cems_gwh": CEMS_GWH,
            "fixed_gwh": fixed.groupby("m").mw.sum() / 1e3,
            "econ_offer": h.groupby("m").mc.mean(),
            "pile_dual": h.groupby("m").dual.median(),
            "east_lmp_mean": h.groupby("m").price.mean(),
            "east_lmp_p10": h.groupby("m").price.quantile(0.1),
            "east_lmp_p90": h.groupby("m").price.quantile(0.9),
        }
    )
    return tab.round(2), b


def price_setters(leg: Path, raw: Path) -> pd.DataFrame:
    """Count NWPP-EAST hours by the largest-pondage class among marginal hydro units."""
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{YEAR}.parquet",
        columns=["plant_code", "fuel", "zone", "hour", "mw", "cap_mw", "red_cost"],
    )
    u = u[(u.zone == "NWPP-EAST") & (u.fuel == "hydro")].copy()
    u["m"] = _month(u.hour)
    pond = pd.read_csv(raw / "nwpp-hydro/nwpp_hydro_pondage.csv")[
        ["plant_id", "pondage_hours"]
    ]
    u = u.merge(pond, left_on="plant_code", right_on="plant_id", how="left")
    marg = u[
        (u.mw > 0.05) & (u.mw < u.cap_mw - 0.05) & (u.red_cost.abs() < 0.05)
    ].copy()
    bins = [-np.inf, 24, 168, 720, np.inf]
    labels = ["<24h", "<168h", "<720h", ">=720h"]
    marg["cls"] = pd.cut(marg.pondage_hours, bins=bins, labels=labels).cat.codes
    best = marg.groupby(["m", "hour"]).cls.max()
    out = best.groupby(level=0).value_counts().unstack(fill_value=0)
    out.columns = [labels[c] if c >= 0 else "no NID row" for c in out.columns]
    print(
        f"NWPP-EAST hydro: {u.plant_code.nunique()} plants, {u.groupby('plant_code').cap_mw.max().sum():.0f} MW"
    )
    return out


def price_variance(leg: Path, raw: Path) -> pd.DataFrame:
    """Split measured WEIM and model zonal prices into mean, within-day and between-day SD."""
    w = pd.read_parquet(raw / "nwpp-weim/weim_hourly_by_ba.parquet")
    w = w[w.year == YEAR]
    sysd = pd.read_parquet(leg / "system.parquet")

    def _dec(df: pd.DataFrame, col: str) -> pd.DataFrame:
        df = df.copy()
        df["m"] = _month(df.hour)
        df["d"] = df.hour // 24
        df["dm"] = df.groupby("d")[col].transform("mean")
        df["mm"] = df.groupby("m")[col].transform("mean")
        return pd.DataFrame(
            {
                "mean": df.groupby("m")[col].mean(),
                "within_day_sd": (df[col] - df.dm).groupby(df.m).std(),
                "between_day_sd": (df.dm - df.mm).groupby(df.m).std(),
            }
        )

    parts = {
        ba: _dec(w[w.baa == ba][["hour", "lmp"]].dropna(), "lmp")
        for ba in ("PACE", "IPCO", "BPAT")
    }
    for z in ("NWPP-EAST", "NWPP-NW"):
        parts[f"model {z}"] = _dec(sysd[sysd.zone == z][["hour", "price"]], "price")
    return pd.concat(parts, axis=1).loc[6:12].round(1)


def measured_price_taker(b: pd.DataFrame, raw: Path) -> pd.DataFrame:
    """Bridger TWh if its keeper offer faced the measured WEIM hourly price (no pile dual)."""
    w = pd.read_parquet(raw / "nwpp-weim/weim_hourly_by_ba.parquet")
    w = w[w.year == YEAR]
    econ = b[~b.unit_id.str.endswith(FIXED_TRANCHES)]
    fixed = b[b.unit_id.str.endswith(FIXED_TRANCHES)].groupby("m").mw.sum() / 1e3
    out = pd.DataFrame({"model": b.groupby("m").mw.sum() / 1e6, "cems": CEMS_GWH / 1e3})
    for ba in ("PACE", "IPCO"):
        x = econ.drop(columns="price").merge(w[w.baa == ba][["hour", "lmp"]], on="hour")
        on = x.lmp > x.mc
        out[f"at {ba} price"] = ((x.cap_mw * on).groupby(x.m).sum() / 1e3 + fixed) / 1e3
    return out.loc[6:12].round(2)


def main() -> None:
    """Print every phase-0 table for the leg directory given on the command line."""
    leg = Path(
        sys.argv[1] if len(sys.argv) > 1 else "results/calibration/nwppnext16c_2023"
    )
    raw = Path("data/raw")
    pd.set_option("display.width", 250)
    print(
        "1. Bridger delivered price by mine ($/MMBtu)\n",
        bridger_receipts(raw).to_string(),
    )
    tab, b = bridger_offer_vs_price(leg)
    print("\n2. Bridger offer, pile dual, NWPP-EAST price\n", tab.T.to_string())
    print(
        "\n3. NWPP-EAST price-setting hydro (hours)\n",
        price_setters(leg, raw).to_string(),
    )
    print(
        "\n4. Price mean / within-day SD / between-day SD\n",
        price_variance(leg, raw).T.to_string(),
    )
    print(
        "\n5. Bridger at measured WEIM prices (TWh)\n",
        measured_price_taker(b, raw).T.to_string(),
    )


if __name__ == "__main__":
    main()
