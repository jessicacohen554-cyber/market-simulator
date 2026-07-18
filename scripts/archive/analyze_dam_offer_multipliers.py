"""Ground the model's thermal offer-curve bands in the measured ERCOT DAM offers.

Reads the tidy offer table produced by ``scripts/data/parse_ercot_dam_offers.py`` and
normalizes every QSE-submitted offer into the model's **heat-rate-multiplier**
space, so the *measured* offer distribution can be overlaid directly on the
model's ``offer_curve_by_group`` band multipliers (the open Task-2 gap from
``docs/lmp-decomposition-2026-06.md``: the CT/CC/ST band *shape* is defensible
but the *heights* were fitted, not validated against the real offer distribution).

The model prices each band as ``offer = base_hr * mult * gas + vom``, so the
inverse for a measured offer price is::

    mult = (offer_price - vom) / (base_hr * gas_delivered)

with:
  * ``base_hr`` = the class reference heat rate (cap-weighted, matching the
    ``docs/lmp-decomposition-2026-06.md`` overlay: CT 10.65, CC 7.16 MMBtu/MWh;
    ST 10.75 from the ERCOT registry). A per-plant base_hr would sharpen this but
    needs the resource->EIA-plant crosswalk (the flagged long pole; the
    resource->settlement-point half is emitted by the parser).
  * ``gas_delivered`` = the delivery-date Henry Hub daily price + the ERCOT basis
    (``GAS_BASIS_DIFFERENTIAL['ERCOT']`` = -0.5 $/MMBtu).
  * ``vom`` = the class VOM (gas_ct 3.5, gas_cc 2.0, gas_st 4.0).

The three-part ERCOT offer maps onto the model tranches as:

  * **committed**  <- Min Gen Cost + amortized Startup (per-start / typical
    run-MWh). This is the real measured grounding for the committed hurdle the
    model proxies; reported with the startup adder OFF and at two run-length
    assumptions so the band is bracketed, not point-fit.
  * **econ_low -> econ_high**  <- the energy offer-curve points across the
    LSL->HSL range, bucketed by load fraction (curve_mw / HSL).
  * **peak**  <- the top of the curve / the offer-cap price wall (often $5,000 in
    scarcity-capable hours; the normal-hours deep top is masked by ERCOT).

Outputs a per-class x band multiplier-distribution CSV
(``data/raw/_processed-legacy/ercot_offer_multiplier_summary.csv``) and prints the overlay
tables used in the writeup.

Usage::

    python scripts/archive/analyze_dam_offer_multipliers.py
    python scripts/archive/analyze_dam_offer_multipliers.py --committed-only
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFERS = REPO_ROOT / "inputs" / "processed" / "ercot_dam_offers.parquet"
HENRY_HUB = REPO_ROOT / "inputs" / "raw-data" / "gas-prices" / "henry_hub_daily.csv"
OUT_SUMMARY = REPO_ROOT / "inputs" / "processed" / "ercot_offer_multiplier_summary.csv"

ERCOT_GAS_BASIS = -0.5  # GAS_BASIS_DIFFERENTIAL['ERCOT'], $/MMBtu over Henry Hub

# Class reference heat rate (MMBtu/MWh) and VOM ($/MWh). CT/CC match the
# docs/lmp-decomposition-2026-06.md cap-weighted overlay; ST from the ERCOT
# master-plant-registry cap-weighted annual_heat_rate.
CLASS_PARAMS = {
    "CT_PEAKER": {"base_hr": 10.65, "vom": 3.5},
    "CC": {"base_hr": 7.16, "vom": 2.0},
    "ST_GAS": {"base_hr": 10.75, "vom": 4.0},
}

# run124 effective offer-curve band multipliers (the keeper under test).
MODEL_BANDS = {
    "CT_PEAKER": {
        "committed": 1.14,
        "econ_low": 1.27,
        "econ_high": 2.18,
        "peak": 13.15,
    },
    "CC": {"committed": 0.92, "econ_low": 1.16, "econ_high": 1.41, "peak": 2.25},
    "ST_GAS": {"committed": 0.91, "econ_low": 1.15, "econ_high": 1.55, "peak": 4.20},
}

# Typical online run length per start (hours) for amortizing the startup cost
# into the committed-band $/MWh. Bracketed, not point-fit.
RUN_HOURS = {"CT_PEAKER": (4, 8), "CC": (12, 24), "ST_GAS": (8, 16)}

PCTS = [0.10, 0.25, 0.50, 0.75, 0.90]
OFFER_CAP = 4900.0  # treat curve points at/above this as the offer-cap price wall


def load_offers(committed_only: bool) -> pd.DataFrame:
    cols = [
        "delivery_date",
        "model_class",
        "resource_name",
        "committed",
        "hsl",
        "lsl",
        "curve_mw",
        "curve_price",
        "min_gen_cost",
        "startup_cold",
        "startup_hot",
    ]
    df = pd.read_parquet(OFFERS, columns=cols)
    df = df[df["model_class"].isin(CLASS_PARAMS)].copy()
    if committed_only:
        df = df[df["committed"]].copy()
    # Delivery-date Henry Hub + ERCOT basis -> delivered gas $/MMBtu.
    hh = pd.read_csv(HENRY_HUB, parse_dates=["date"]).rename(
        columns={"price_usd_mmbtu": "hh"}
    )
    hh = hh.set_index("date")["hh"].sort_index()
    # Forward-fill weekends/holidays to a daily series, then map by date.
    daily = hh.reindex(pd.date_range(hh.index.min(), hh.index.max())).ffill()
    df["gas"] = df["delivery_date"].map(daily) + ERCOT_GAS_BASIS
    df = df[df["gas"] > 0].copy()
    return df


def _mult(price, cls, gas):
    p = CLASS_PARAMS[cls]
    return (price - p["vom"]) / (p["base_hr"] * gas)


def econ_band_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Per-class econ-band multiplier distribution from the energy curve points."""
    d = df[(df["hsl"] > 0) & (df["curve_price"] < OFFER_CAP)].copy()
    d["load_frac"] = d["curve_mw"] / d["hsl"]
    d["lsl_frac"] = (d["lsl"] / d["hsl"]).clip(0, 0.99)
    d["mult"] = [
        _mult(p, c, g) for p, c, g in zip(d["curve_price"], d["model_class"], d["gas"])
    ]

    # Band by position in the LSL->HSL operating range.
    #   econ_low  : the bottom third above LSL
    #   econ_mid  : the middle
    #   econ_high : the top decile of load (approaching HSL)
    above = (d["load_frac"] - d["lsl_frac"]).clip(lower=0)
    span = (1.0 - d["lsl_frac"]).clip(lower=0.05)
    rel = above / span  # 0 at LSL, 1 at HSL
    d["band"] = pd.cut(
        rel, [-0.01, 0.33, 0.90, 1.01], labels=["econ_low", "econ_mid", "econ_high"]
    )

    # Each resource contributes its median multiplier per band (so a few
    # high-frequency QSEs don't dominate), then describe across resources.
    permed = (
        d.groupby(["model_class", "band", "resource_name"], observed=True)["mult"]
        .median()
        .reset_index()
    )
    rows = []
    for (cls, band), g in permed.groupby(["model_class", "band"], observed=True):
        q = g["mult"].quantile(PCTS)
        rows.append(
            {
                "model_class": cls,
                "band": str(band),
                "n_resources": g["resource_name"].nunique(),
                **{f"p{int(p * 100)}": round(q[p], 3) for p in PCTS},
            }
        )
    return pd.DataFrame(rows)


def peak_band_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Top-of-curve (non-cap) multiplier and offer-cap incidence per class."""
    d = df[df["hsl"] > 0].copy()
    # Top economic curve point per (resource, date, hour-ish) below the cap.
    sub = d[d["curve_price"] < OFFER_CAP]
    top = (
        sub.groupby(["model_class", "resource_name"], observed=True)
        .agg(top_price=("curve_price", "max"), gas=("gas", "median"))
        .reset_index()
    )
    top["mult"] = [
        _mult(p, c, g)
        for p, c, g in zip(top["top_price"], top["model_class"], top["gas"])
    ]
    # Share of a class's offer rows that sit at the offer-cap price wall.
    capshare = (
        d.assign(at_cap=d["curve_price"] >= OFFER_CAP)
        .groupby("model_class", observed=True)["at_cap"]
        .mean()
    )
    rows = []
    for cls, g in top.groupby("model_class", observed=True):
        q = g["mult"].quantile(PCTS)
        rows.append(
            {
                "model_class": cls,
                "band": "peak_econ_top",
                "n_resources": g["resource_name"].nunique(),
                "offer_cap_share": round(float(capshare.get(cls, 0)), 3),
                **{f"p{int(p * 100)}": round(q[p], 3) for p in PCTS},
            }
        )
    return pd.DataFrame(rows)


def committed_band_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Committed-band multiplier from Min Gen Cost +/- amortized startup."""
    # One row per resource: median Min Gen Cost, LSL, startup, gas.
    d = df[(df["min_gen_cost"].notna()) & (df["lsl"] > 0)].copy()
    res = (
        d.groupby(["model_class", "resource_name"], observed=True)
        .agg(
            min_gen=("min_gen_cost", "median"),
            lsl=("lsl", "median"),
            startup_cold=("startup_cold", "median"),
            startup_hot=("startup_hot", "median"),
            gas=("gas", "median"),
        )
        .reset_index()
    )
    rows = []
    for cls, g in res.groupby("model_class", observed=True):
        out = {"model_class": cls, "n_resources": len(g)}
        # min-gen only (no startup)
        m0 = _mult(g["min_gen"], cls, g["gas"])
        out["mingen_only_p50"] = round(m0.median(), 3)
        # + amortized startup at the two run-length brackets (use hot start,
        # the typical recurring state for a cycling fleet).
        for label, hrs in zip(("short", "long"), RUN_HOURS[cls]):
            adder = g["startup_hot"].fillna(g["startup_cold"]) / (hrs * g["lsl"])
            m = _mult(g["min_gen"] + adder, cls, g["gas"])
            out[f"committed_{label}run_p50"] = round(m.median(), 3)
        rows.append(out)
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--committed-only",
        action="store_true",
        help="restrict to online/committed status rows",
    )
    args = ap.parse_args()

    df = load_offers(args.committed_only)
    print(
        f"Loaded {len(df):,} offer point rows "
        f"({df['delivery_date'].min().date()} -> {df['delivery_date'].max().date()})"
        f"{'  [committed only]' if args.committed_only else ''}\n"
    )

    econ = econ_band_distribution(df)
    peak = peak_band_distribution(df)
    comm = committed_band_distribution(df)

    pd.set_option("display.width", 200)
    print(
        "=== ENERGY-CURVE econ-band multiplier distribution (per-resource median) ==="
    )
    print(econ.to_string(index=False))
    print("\n=== PEAK band: top economic curve point + offer-cap incidence ===")
    print(peak.to_string(index=False))
    print("\n=== COMMITTED band: Min Gen Cost +/- amortized startup ===")
    print(comm.to_string(index=False))

    print("\n=== MODEL run124 bands vs MEASURED (median) overlay ===")
    overlay_rows = []
    for cls in CLASS_PARAMS:
        mb = MODEL_BANDS[cls]
        el = econ[(econ.model_class == cls) & (econ.band == "econ_low")]
        eh = econ[(econ.model_class == cls) & (econ.band == "econ_high")]
        pk = peak[peak.model_class == cls]
        cm = comm[comm.model_class == cls]
        overlay_rows.append(
            {
                "class": cls,
                "committed_model": mb["committed"],
                "committed_meas_mingen": float(cm["mingen_only_p50"].iloc[0]),
                "committed_meas_+startup": float(cm["committed_longrun_p50"].iloc[0]),
                "econ_low_model": mb["econ_low"],
                "econ_low_meas_p50": float(el["p50"].iloc[0]) if len(el) else np.nan,
                "econ_high_model": mb["econ_high"],
                "econ_high_meas_p50": float(eh["p50"].iloc[0]) if len(eh) else np.nan,
                "peak_model": mb["peak"],
                "peak_meas_econtop_p50": float(pk["p50"].iloc[0])
                if len(pk)
                else np.nan,
                "peak_meas_capshare": float(pk["offer_cap_share"].iloc[0])
                if len(pk)
                else np.nan,
            }
        )
    overlay = pd.DataFrame(overlay_rows)
    print(overlay.to_string(index=False))

    # Persist the tidy summary (econ + peak + committed long-form).
    econ_l = econ.assign(kind="econ")
    peak_l = peak.assign(kind="peak")
    comm_l = comm.melt(
        id_vars=["model_class", "n_resources"],
        var_name="metric",
        value_name="multiplier",
    ).assign(kind="committed", band="committed")
    summary = pd.concat([econ_l, peak_l, comm_l], ignore_index=True)
    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"\nWrote {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
