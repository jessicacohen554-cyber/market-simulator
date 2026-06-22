"""Cheap (no-solve) Track-1 check: dump the MEASURED ERCOT DAM offer stack for
CC vs ST_GAS vs CT_PEAKER and test whether the measured offers actually order
ST_GAS / CT_PEAKER *below* combined-cycle in the shoulder months.

This is the decisive first step for the within-gas merit-order miss (the model
over-runs CC_REGULAR and under-runs ST_GAS + CT_PEAKER, worst in Apr/May/Oct).
If the measured offers DO order ST_GAS/CT below CC in the shoulder, the keeper's
offer_curve_deltas have the merit stack wrong and a measured re-derivation is
warranted. If they DON'T (ST_GAS/CT genuinely offer above CC on energy), then
pushing them below CC is a markup — the residual is the energy-only-LP
local-reliability / AS-commitment limitation, and the honest move is to ledger
CT_PEAKER/ST_GAS as an accepted measured-input limitation.

It reports the offer in two grounded forms, no fit to any TWh / price target:
  * raw $/MWh offer (Min Gen Cost for the committed floor; energy-curve points
    bucketed econ_low / econ_high across the LSL->HSL range), per-resource median
    then distribution across resources; and
  * the implied heat-rate multiplier (offer = base_hr * mult * gas + vom), the
    space the model's bands live in, so the stack can be compared like-for-like
    against the keeper offer_curve_deltas.

Usage:
    python scripts/probes/_ercot_offer_stack_meritorder.py \
        data/raw/_processed-legacy/ercot_dam_offers_2024.parquet
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HENRY_HUB = REPO / "data" / "raw" / "gas-prices" / "henry_hub_daily.csv"
ERCOT_GAS_BASIS = -0.5  # $/MMBtu over Henry Hub (GAS_BASIS_DIFFERENTIAL['ERCOT'])

# Class reference heat rate (MMBtu/MWh) and VOM ($/MWh), matching
# analyze_dam_offer_multipliers.py / the lmp-decomposition overlay.
CLASS_PARAMS = {
    "CT_PEAKER": {"base_hr": 10.65, "vom": 3.5},
    "CC": {"base_hr": 7.16, "vom": 2.0},
    "ST_GAS": {"base_hr": 10.75, "vom": 4.0},
}
SHOULDER = {4, 5, 10}  # Apr / May / Oct
OFFER_CAP = 4900.0
PCTS = [0.10, 0.25, 0.50, 0.75, 0.90]


def _mult(price, cls, gas):
    p = CLASS_PARAMS[cls]
    return (price - p["vom"]) / (p["base_hr"] * gas)


def load(path: Path, committed_only: bool) -> pd.DataFrame:
    df = pd.read_parquet(
        path,
        columns=[
            "delivery_date",
            "model_class",
            "resource_name",
            "committed",
            "hsl",
            "lsl",
            "curve_mw",
            "curve_price",
            "min_gen_cost",
        ],
    )
    df = df[df["model_class"].isin(CLASS_PARAMS)].copy()
    if committed_only:
        df = df[df["committed"]].copy()
    hh = pd.read_csv(HENRY_HUB, parse_dates=["date"]).rename(
        columns={"price_usd_mmbtu": "hh"}
    )
    hh = hh.set_index("date")["hh"].sort_index()
    daily = hh.reindex(pd.date_range(hh.index.min(), hh.index.max())).ffill()
    df["gas"] = df["delivery_date"].map(daily) + ERCOT_GAS_BASIS
    df = df[df["gas"] > 0].copy()
    df["month"] = df["delivery_date"].dt.month
    return df


def econ_bands(df: pd.DataFrame) -> pd.DataFrame:
    d = df[(df["hsl"] > 0) & (df["curve_price"] < OFFER_CAP)].copy()
    d["load_frac"] = d["curve_mw"] / d["hsl"]
    d["lsl_frac"] = (d["lsl"] / d["hsl"]).clip(0, 0.99)
    above = (d["load_frac"] - d["lsl_frac"]).clip(lower=0)
    span = (1.0 - d["lsl_frac"]).clip(lower=0.05)
    rel = above / span
    d["band"] = pd.cut(
        rel, [-0.01, 0.33, 0.90, 1.01], labels=["econ_low", "econ_mid", "econ_high"]
    )
    d["mult"] = [
        _mult(p, c, g) for p, c, g in zip(d["curve_price"], d["model_class"], d["gas"])
    ]
    return d


def report(d_econ: pd.DataFrame, df: pd.DataFrame, label: str) -> None:
    print(f"\n{'=' * 78}\n{label}\n{'=' * 78}")
    # Committed floor: Min Gen Cost per resource (median), raw $/MWh + mult.
    comm = df[(df["min_gen_cost"].notna()) & (df["lsl"] > 0)]
    crows = []
    for cls, g in comm.groupby("model_class", observed=True):
        per = g.groupby("resource_name", observed=True).agg(
            mg=("min_gen_cost", "median"), gas=("gas", "median")
        )
        crows.append(
            {
                "class": cls,
                "n": len(per),
                "mingen_$/MWh_p50": round(per["mg"].median(), 1),
                "mingen_mult_p50": round(_mult(per["mg"], cls, per["gas"]).median(), 3),
            }
        )
    print("\n-- COMMITTED floor (Min Gen Cost) --")
    print(pd.DataFrame(crows).to_string(index=False))

    print(
        "\n-- ENERGY-CURVE bands ($/MWh raw, per-resource median across resources) --"
    )
    rows = []
    for (cls, band), g in d_econ.groupby(["model_class", "band"], observed=True):
        if band == "econ_mid":
            continue
        per = g.groupby("resource_name", observed=True).agg(
            price=("curve_price", "median"), mult=("mult", "median")
        )
        q = per["price"].quantile(PCTS)
        mq = per["mult"].quantile(PCTS)
        rows.append(
            {
                "class": cls,
                "band": str(band),
                "n_res": len(per),
                **{f"$p{int(p * 100)}": round(q[p], 1) for p in PCTS},
                "mult_p50": round(mq[0.50], 3),
            }
        )
    print(pd.DataFrame(rows).to_string(index=False))


def main(argv: list[str]) -> int:
    path = (
        Path(argv[0])
        if argv
        else (REPO / "data/raw/_processed-legacy/ercot_dam_offers_2024.parquet")
    )
    committed_only = "--committed-only" in argv
    df = load(path, committed_only)
    print(
        f"Loaded {len(df):,} offer point rows "
        f"({df['delivery_date'].min().date()} -> {df['delivery_date'].max().date()})"
        f"  gas median ${df['gas'].median():.2f}/MMBtu"
        f"{'  [committed only]' if committed_only else ''}"
    )
    d_econ = econ_bands(df)

    report(d_econ, df, "ALL MONTHS")
    sh = SHOULDER
    report(
        d_econ[d_econ["month"].isin(sh)],
        df[df["month"].isin(sh)],
        "SHOULDER (Apr / May / Oct)",
    )
    print(
        "\nMerit-order read: compare each class's econ_low / econ_high $/MWh. "
        "If CC sits BELOW ST_GAS & CT_PEAKER, the energy-only LP is RIGHT to run "
        "CC first -> the ST_GAS/CT under-run is the AS/local-reliability "
        "limitation (ledger), NOT an offer-curve miss."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
