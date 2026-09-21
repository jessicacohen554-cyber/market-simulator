"""SPP-69 phase 0 (ZERO LP): the COST half of the Schedule-5 coal intake, and 2020.

`RESULT-spp-44-coal-deliverability-2026-09-16.md` killed the **tonnage** route from the
EIA-923 Schedule-5 intake to SPP's published MMU coal offer markup — receipts/burn
coverage, stockpile days, rail share, per-plant concentration and sub-annual timing, six
legs, none of which puts 2022 outside the other years' range. It did **not** touch the
delivered-**cost** side of the same intake (`FUEL_COST`, `Purchase Type`), which is a
distinct hypothesis: a generator offers at the cost of REPLACING the ton it burns, not at
its average contract cost, so a spot/contract divergence would raise coal offers through
ordinary opportunity-cost economics rather than through deliverability.

This probe closes that half, and re-derives the tonnage half independently on a DIFFERENT
statistic (days-of-burn rather than SPP-44's coverage ratio) as a cross-check.

Legs, all from committed artifacts, no LP:
  A  admissible coal ENERGY BUDGET vs model coal burn -- does it ever bind?
  B  spot-minus-contract delivered cost, $/MMBtu and $/MWh, vs the MMU markup
  C  FUEL_COST coverage and REG/UNREG split -- is leg B an artifact of suppression?
  D  per-plant days-of-burn distribution -- does it separate 2021 from 2022?
  E  the 2020 model price distribution -- the prompt's SECOND, SEPARATE object

Run:  uv run python scripts/probes/_spp69_coal_cost_channel_phase0.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNG = ROOT / "results/calibration/spp67_yearown_rung"
SPAN = ROOT / "results/calibration/spp67_yearown_span"

MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

# SPP MMU published annual coal offer markup, cleared-MW weighted, $/MWh (ASOM 2024
# fn. 135 / ASOM 2023 fn. 194), carried forward by RESULT-spp-41 §2.5.
# VALIDATION TARGET ONLY -- rule 1 [R-STRUCT] forbids fitting a mechanism to it.
MMU_MARKUP = {2021: 6.02, 2022: 21.12, 2023: 6.88, 2024: 4.29, 2025: 5.81}

# Model / actual coal TWh, grid-delivered basis, read off the two committed verdicts
# (scripts/calibration_verdict.py --json, criterion `fuelmix`). COAL_PRB + COAL_LIGNITE.
MODEL_COAL = {
    2019: 86.453,
    2020: 67.397,
    2021: 96.800,
    2022: 101.051,
    2023: 73.532,
    2024: 66.702,
    2025: 86.872,
}
ACTUAL_COAL = {
    2019: 89.687,
    2020: 76.958,
    2021: 90.830,
    2022: 90.755,
    2023: 74.778,
    2024: 68.696,
    2025: 83.490,
}

HEAT_RATE_MMBTU_PER_MWH = 10.5  # nominal subcritical PRB unit; leg B is reported in
# $/MMBtu too, so the conclusion does not rest on this constant.


def spp_coal_plants() -> set[int]:
    """SPP-footprint coal plant ids, attributed via the EIA-860 plant BA code."""
    plant = pd.read_parquet(ROOT / "data/raw/eia-860/eia860_plant.parquet")
    swpp = plant[
        plant["Balancing Authority Code"].astype(str).str.strip().str.upper() == "SWPP"
    ]
    swpp_ids = {
        int(x)
        for x in pd.to_numeric(swpp["Plant Code"], errors="coerce").dropna().unique()
    }
    gen = pd.read_parquet(ROOT / "data/raw/eia-860/eia860_generator_operable.parquet")
    coal = gen[
        gen["Energy Source 1"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin({"BIT", "SUB", "LIG", "WC", "RC", "SGC"})
    ]
    coal_ids = {
        int(x)
        for x in pd.to_numeric(coal["Plant Code"], errors="coerce").dropna().unique()
    }
    return swpp_ids & coal_ids


def load_stocks(spp: set[int]) -> pd.DataFrame:
    """Plant x month ending coal stock, short tons, SPP footprint."""
    frames = []
    for y in range(2018, 2025):
        df = pd.read_csv(
            ROOT / f"data/raw/coal-stocks/coal_stocks_{y}.csv", low_memory=False
        )
        df.columns = [str(c).strip() for c in df.columns]
        df = df[
            (df["Plant Id"] != 999999) & (df["Plant Id"].isin(spp))
        ]  # 999999 = EIA residual
        for mi, m in enumerate(MONTHS):
            q = pd.to_numeric(df[f"Quantity {m}"], errors="coerce").fillna(0)
            g = pd.DataFrame({"plant": df["Plant Id"].values, "tons": q.values})
            g = g.groupby("plant", as_index=False)["tons"].sum()
            g["year"], g["month"] = y, mi + 1
            frames.append(g)
    return pd.concat(frames, ignore_index=True)


def load_receipts(spp: set[int]) -> pd.DataFrame:
    """Delivery-level coal receipts, SPP footprint, with cost and purchase type."""
    frames = []
    for y in range(2018, 2025):
        d = pd.read_csv(
            ROOT / f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False
        )
        d.columns = [str(c).strip() for c in d.columns]
        d = d[d["Plant Id"].isin(spp)].copy()
        for c in ("QUANTITY", "Average Heat Content", "FUEL_COST"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d["QUANTITY"] = d["QUANTITY"].fillna(0)
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def leg_a(stock: pd.DataFrame, rec_mt: dict[int, float]) -> pd.DataFrame:
    """Does an admissible coal energy budget ever bind on SPP's model coal burn?"""
    dec = stock[stock["month"] == 12].groupby("year")["tons"].sum() / 1e6
    rows = []
    for y in range(2019, 2025):
        opening = float(dec[y - 1])
        prior = [rec_mt[p] for p in (y - 3, y - 2, y - 1) if p in rec_mt]
        rate = sum(prior) / len(prior)
        budget = opening + rate
        burn = opening + rec_mt[y] - float(dec[y])
        mwh_per_ton = ACTUAL_COAL[y] / burn
        model_mt = MODEL_COAL[y] / mwh_per_ton
        rows.append(
            {
                "year": y,
                "opening": round(opening, 3),
                "rate": round(rate, 3),
                "budget": round(budget, 3),
                "measured_burn": round(burn, 3),
                "MWh/ton": round(mwh_per_ton, 4),
                "model_burn": round(model_mt, 3),
                "headroom": round(budget - model_mt, 3),
                "binds": "YES" if model_mt > budget else "no",
            }
        )
    return pd.DataFrame(rows)


def leg_b_c(rc: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Spot-minus-contract delivered cost, and the suppression check behind it."""
    rc = rc.copy()
    rc["pt"] = rc["Purchase Type"].astype(str).str.strip().str.upper()
    rc["cost_mmbtu"] = rc["FUEL_COST"] / 100.0  # EIA files this in cents/MMBtu
    rc["mmbtu"] = rc["QUANTITY"] * rc["Average Heat Content"]

    cov = []
    for y in sorted(rc["YEAR"].unique()):
        s = rc[rc["YEAR"] == y]
        tot = float(s["mmbtu"].sum())
        reg = s.groupby(s["Regulated"].astype(str).str.strip().str.upper())[
            "mmbtu"
        ].sum()
        cov.append(
            {
                "year": int(y),
                "cost_coverage": round(
                    float(s[s["FUEL_COST"].notna()]["mmbtu"].sum() / tot), 4
                ),
                "REG_share": round(float(reg.get("REG", 0) / tot), 4),
                "UNREG_share": round(float(reg.get("UNREG", 0) / tot), 4),
            }
        )

    priced = rc[rc["cost_mmbtu"].notna() & (rc["mmbtu"] > 0)]
    out = []
    for y in sorted(priced["YEAR"].unique()):
        s = priced[priced["YEAR"] == y]

        def wavg(sub: pd.DataFrame) -> float:
            m = float(sub["mmbtu"].sum())
            return (
                float((sub["cost_mmbtu"] * sub["mmbtu"]).sum() / m)
                if m > 0
                else float("nan")
            )

        sp = wavg(s[s["pt"] == "S"])
        ct = wavg(s[s["pt"].isin(["C", "NC"])])
        allin = wavg(s)
        out.append(
            {
                "year": int(y),
                "contract_$/MMBtu": round(ct, 3),
                "spot_$/MMBtu": round(sp, 3),
                "spread_$/MMBtu": round(sp - ct, 3),
                "spot_vol_share": round(
                    float(s[s["pt"] == "S"]["mmbtu"].sum() / s["mmbtu"].sum()), 4
                ),
                "spread_$/MWh": round((sp - ct) * HEAT_RATE_MMBTU_PER_MWH, 2),
                "allin_$/MMBtu": round(allin, 3),
                "MMU_markup_$/MWh": MMU_MARKUP.get(int(y)),
            }
        )
    b = pd.DataFrame(out)
    b["allin_yoy_$/MWh"] = (b["allin_$/MMBtu"].diff() * HEAT_RATE_MMBTU_PER_MWH).round(
        2
    )
    return b, pd.DataFrame(cov)


def leg_d(stock: pd.DataFrame, rc: pd.DataFrame) -> pd.DataFrame:
    """Per-plant days-of-burn: does the stockpile separate 2021 from 2022?"""
    recp = (
        rc.groupby(["Plant Id", "YEAR"], as_index=False)["QUANTITY"]
        .sum()
        .rename(columns={"Plant Id": "plant", "YEAR": "year", "QUANTITY": "recv"})
    )
    dec = stock[stock["month"] == 12][["plant", "year", "tons"]].rename(
        columns={"tons": "dec"}
    )
    ann = recp.merge(dec, on=["plant", "year"], how="left").sort_values(
        ["plant", "year"]
    )
    ann["prev_dec"] = ann.groupby("plant")["dec"].shift(1)
    ann["daily"] = (ann["prev_dec"] + ann["recv"] - ann["dec"]) / 365.0

    mm = stock.merge(ann[["plant", "year", "daily"]], on=["plant", "year"], how="left")
    mm = mm[mm["daily"] > 0].copy()
    mm["days"] = mm["tons"] / mm["daily"]

    rows = []
    for y in range(2019, 2025):
        mins = mm[mm["year"] == y].groupby("plant")["days"].min()
        rows.append(
            {
                "year": y,
                "plants": int(mins.size),
                "p25": round(float(mins.quantile(0.25)), 1),
                "median": round(float(mins.median()), 1),
                "n<30": int((mins < 30).sum()),
                "n<45": int((mins < 45).sum()),
                "n<60": int((mins < 60).sum()),
                "MMU_markup": MMU_MARKUP.get(y),
            }
        )
    return pd.DataFrame(rows)


def leg_e() -> pd.DataFrame:
    """The model's own price distribution, 2019-2022, load-weighted across zones."""
    rows = []
    for y in (2019, 2020, 2021, 2022):
        p = RUNG / "hourly" / f"system_{y}.parquet"
        if not p.exists():
            continue
        s = pd.read_parquet(p)
        s = s[s["pass"] == "P1"]
        g = s.groupby("hour").apply(
            lambda d: np.average(d["price"], weights=d["demand"]), include_groups=False
        )
        c = pd.read_parquet(RUNG / "hourly" / f"class_hourly_{y}.parquet")
        c = c[(c["pass"] == "P1") & (c["klass"] == "CT_PEAKER")]
        ct = c.groupby("hour")["mw"].sum()
        rows.append(
            {
                "year": y,
                "mean": round(float(g.mean()), 2),
                "p05": round(float(g.quantile(0.05)), 2),
                "median": round(float(g.median()), 2),
                "p95": round(float(g.quantile(0.95)), 2),
                "max": round(float(g.max()), 2),
                "p05_p95_width": round(float(g.quantile(0.95) - g.quantile(0.05)), 2),
                "h>$100": int((g > 100).sum()),
                "CT_PEAKER_hours_on": int((ct > 1.0).sum()),
                "CT_PEAKER_TWh": round(float(ct.sum() / 1e6), 2),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    spp = spp_coal_plants()
    stock = load_stocks(spp)
    rc = load_receipts(spp)
    rec_mt = {int(y): float(g["QUANTITY"].sum()) / 1e6 for y, g in rc.groupby("YEAR")}

    print(
        f"SPP coal plants (EIA-860 BA=SWPP & coal energy source): {len(spp)}; "
        f"matched in coal-stocks: {stock['plant'].nunique()}; "
        f"in coal-receipts: {rc['Plant Id'].nunique()}"
    )

    print("\n" + "=" * 90)
    print("LEG A -- would an ADMISSIBLE coal energy budget ever bind?  [Mt]")
    print(
        "  budget(Y) = Dec(Y-1) ending stock + mean receipts over the <=3 years <= Y-1"
    )
    a = leg_a(stock, rec_mt)
    print(a.to_string(index=False))
    print(
        f"  -> binds in {int((a['binds'] == 'YES').sum())} of {len(a)} years; "
        f"min headroom {a['headroom'].min():.3f} Mt"
    )

    b, cov = leg_b_c(rc)
    print("\n" + "=" * 90)
    print("LEG B -- SPOT minus CONTRACT delivered coal cost vs the MMU markup")
    print(b.to_string(index=False))
    print("\nLEG C -- is leg B an artifact of FUEL_COST suppression?")
    print(cov.to_string(index=False))

    print("\n" + "=" * 90)
    print(
        "LEG D -- per-plant days-of-burn minima (independent of SPP-44's coverage ratio)"
    )
    print(leg_d(stock, rc).to_string(index=False))

    print("\n" + "=" * 90)
    print("LEG E -- the model's own price distribution, and CT_PEAKER duty")
    print(leg_e().to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
