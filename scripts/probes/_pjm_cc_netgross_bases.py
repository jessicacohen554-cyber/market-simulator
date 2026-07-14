"""PJM CC parasitic-load seasonality + actuals-basis reconciliation.

Owner questions #2/#3 of the 2026-07-14 July-gas diagnosis
(``docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md``): does the gross->net
parasitic-load haircut between plant-monthly EIA-923 net and plant-monthly
CAMPD gross vary over the year (aux cooling rising with temperature), and what
does the model-vs-actual CC comparison look like on a NET basis?

Four measured blocks — no LP, no solve:

1. **Seasonality panel** — per plant-month ``EIA-923 net / CAMPD gross`` over
   the model's own 65 PJM CC_REGULAR plants (>= 90 % group purity), 2023-2025,
   capacity-weighted by month. Result: flat 0.969-0.975 in every calendar
   month (Jan-Jul delta -0.05 pp) — NO seasonality; the static
   ``parasitic_load_pct`` treatment is correct.
2. **CT-only CEMS detection** — plants whose EIA-923 annual net EXCEEDS their
   CAMPD annual gross (physically impossible for a complete CEMS record) are
   reporting only the combustion-turbine share of the block. PJM instances:
   Ironwood 55337, Hunterstown 55976, Allegheny 3-4-5 55710 (net/gross
   1.45-1.59, the 2x1 signature). Their CAMPD-basis "over-run" is a benchmark
   artifact.
3. **EIA-860 summer-capacity consistency audit** — CC plants whose
   generator-level summer-capacity rows sum ABOVE their nameplate sum
   (component/total double-filing). PJM instances: New Covert 55297
   (1,586 vs 1,176 MW), Keys 60302 (1,237 vs 830.6), Camden 10751 (222.7 vs
   172.9) — +867 MW phantom CC on the raw (flag-off) fleet basis. Keeper-inert
   under ``cc_nameplate_summer_derate=True`` (capacity clamps to nameplate).
4. **July basis reconciliation** — model July gas (pjm-107 payload, all gas
   classes) vs EIA-923 (matched-grid volErr and all-PJM-BA plants) vs EIA-930
   NG. The "+3 TWh July gas over-run" headline is the model measured against
   EIA-930; on the EIA-923 plant-survey basis the July gas error is
   +0.16..+0.76 TWh.

Diagnostic only. Usage:
    python scripts/probes/_pjm_cc_netgross_bases.py [YEAR ...]
"""

import base64
import gzip
import json
import logging
import re
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
logging.disable(logging.WARNING)

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

CAMPD_DIR = REPO / "data" / "raw" / "campd-unit-level"
E923_PARQUET = (
    REPO / "data" / "raw" / "_processed-legacy" / "eia923_monthly_generation.parquet"
)
E860_PARQUET = REPO / "data" / "raw" / "eia-860" / "eia860_generator_operable.parquet"
RUN_JS = (
    REPO / "frontend" / "data" / "backcast" / "runs" / "2026-07-14-pjm-107-gas-daily.js"
)
E930_PARQUET = REPO / "data" / "raw" / "PJM_fueltype.parquet"

PJM_STATES = (
    "PA",
    "NJ",
    "MD",
    "DE",
    "DC",
    "VA",
    "WV",
    "OH",
    "KY",
    "IL",
    "IN",
    "MI",
    "NC",
    "TN",
)
MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP")
GROUP_PURITY = 0.90


def _cc_fleet() -> pd.DataFrame:
    """Model CC_REGULAR plants (>= GROUP_PURITY of plant thermal MW).

    One row per plant with the FLEET-LOADED pmax sum — the capacity the raw
    (flag-off) build actually carries, i.e. after any NaN-fill of missing
    EIA-860 summer-capacity component rows. This is the basis the block-3
    consistency audit must use: plant-total-on-one-row corruption (Keys,
    Camden) hides behind NaN components and only shows up here, not in the
    raw EIA-860 summer sum.
    """
    gens = load_fleet_from_csv("PJM", get_iso_config("PJM"), year=2025)
    rows = [
        {
            "pid": int(str(g.unit_id).split("_")[0]),
            "group": g.plant_group,
            "mw": float(g.pmax_mw),
        }
        for g in gens
        if str(g.unit_id).split("_")[0].isdigit()
    ]
    fr = pd.DataFrame(rows)
    cap = fr.groupby(["pid", "group"], as_index=False)["mw"].sum()
    tot = cap.groupby("pid")["mw"].transform("sum")
    keep = cap[(cap["group"] == "CC_REGULAR") & (cap["mw"] / tot >= GROUP_PURITY)]
    return keep.rename(columns={"mw": "fleet_pmax"})[["pid", "fleet_pmax"]]


def _campd_monthly(years: list[int], plants: list[int]) -> pd.DataFrame:
    """CAMPD monthly gross MWh per facility over the PJM state files."""
    frames = []
    for year in years:
        for st in PJM_STATES:
            path = CAMPD_DIR / f"{st}_{year}.parquet"
            if not path.exists():
                continue
            d = pd.read_parquet(path, columns=["facilityId", "date", "grossLoad"])
            d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
            d = d[d["facilityId"].isin(plants)]
            if not len(d):
                continue
            d["month"] = pd.to_datetime(d["date"]).dt.month
            g = d.groupby(["facilityId", "month"], as_index=False)["grossLoad"].sum()
            g["year"] = year
            frames.append(g)
    return (
        pd.concat(frames)
        .groupby(["facilityId", "year", "month"], as_index=False)["grossLoad"]
        .sum()
    )


def _e923_monthly(years: list[int], plants: list[int]) -> pd.DataFrame:
    """EIA-923 monthly net MWh per plant (all fuel rows, whole plant)."""
    e = pd.read_parquet(E923_PARQUET)
    e = e[e["year"].isin(years) & e["plant_id"].isin(plants)]
    long = [
        (r["plant_id"], r["year"], mi, r[f"netgen_{mn}_mwh"])
        for _, r in e.iterrows()
        for mi, mn in enumerate(MONTHS, start=1)
    ]
    net = pd.DataFrame(long, columns=["facilityId", "year", "month", "net"])
    return net.groupby(["facilityId", "year", "month"], as_index=False)["net"].sum()


def main(years: list[int]) -> None:
    """Run the four measured blocks and print their headlines."""
    fleet = _cc_fleet()
    plants = sorted(fleet["pid"].unique())
    print(f"PJM CC_REGULAR panel: {len(plants)} plants")
    gross = _campd_monthly(years, plants)
    net = _e923_monthly(years, plants)
    m = gross.merge(net, on=["facilityId", "year", "month"], how="inner")

    # ---- block 2: CT-only CEMS detection (annual net > 1.1x annual gross)
    ann = m.groupby(["facilityId", "year"], as_index=False)[["grossLoad", "net"]].sum()
    ann["r"] = ann["net"] / ann["grossLoad"]
    ct_only = sorted(ann.loc[ann["r"] > 1.1, "facilityId"].unique().astype(int))
    print(f"\nCT-only CEMS reporters (923 net > 1.1x CAMPD gross): {ct_only}")
    print(ann[ann["facilityId"].isin(ct_only)].round(3).to_string(index=False))

    # ---- block 1: seasonality panel (complete reporters only)
    p = m[(m["grossLoad"] > 10_000) & (m["net"] > 0)].copy()
    p["ratio"] = p["net"] / p["grossLoad"]
    p = p[(p["ratio"] > 0.7) & (p["ratio"] < 1.1)]
    g860 = pd.read_parquet(E860_PARQUET)
    g860["pc"] = pd.to_numeric(g860["Plant Code"], errors="coerce")
    g860["ns"] = pd.to_numeric(g860["Summer Capacity (MW)"], errors="coerce")
    ns = g860.groupby("pc")["ns"].sum()
    p["w"] = p["facilityId"].map(ns).fillna(0.0)
    monthly = p.groupby("month").apply(
        lambda g: pd.Series(
            {
                "ratio_cw": (g["ratio"] * g["w"]).sum() / g["w"].sum(),
                "n": len(g),
            }
        ),
        include_groups=False,
    )
    print("\nNet/gross ratio by month (capacity-weighted, pooled years):")
    print(monthly.round(4).to_string())
    print(
        f"Jan {monthly.loc[1, 'ratio_cw']:.4f} vs Jul {monthly.loc[7, 'ratio_cw']:.4f} "
        f"-> summer extra haircut "
        f"{100 * (monthly.loc[1, 'ratio_cw'] - monthly.loc[7, 'ratio_cw']):+.2f} pp"
    )

    # ---- block 3: fleet pmax vs EIA-860 nameplate consistency audit.
    # Fleet basis, not raw 860 sums: plant-total-on-one-row corruption (Keys,
    # Camden) hides behind NaN component rows that the loader nameplate-fills,
    # so only fleet_pmax > nameplate_sum exposes every instance.
    g860["np_"] = pd.to_numeric(g860["Nameplate Capacity (MW)"], errors="coerce")
    cc = g860[g860["Technology"] == "Natural Gas Fired Combined Cycle"]
    sums = cc.groupby("pc")[["np_", "ns"]].sum()
    audit = fleet.merge(sums, left_on="pid", right_index=True, how="inner")
    bad = audit[audit["fleet_pmax"] > audit["np_"] * 1.001]
    print(
        "\nCC plants whose fleet-loaded pmax exceeds EIA-860 nameplate "
        "(corrupt summer-capacity rows):"
    )
    print(bad.round(1).to_string(index=False))
    print(
        "   phantom MW on the raw (flag-off) basis: "
        f"{(bad['fleet_pmax'] - bad['np_']).sum():.0f}"
    )

    # ---- block 4: July basis reconciliation
    run = json.loads(
        gzip.decompress(
            base64.b64decode(re.search(r'="([^"]+)"', RUN_JS.read_text()).group(1))
        )
    )
    e930 = pd.read_parquet(E930_PARQUET)
    e930["period"] = pd.to_datetime(e930["period"])
    ng = e930[e930["fueltype"] == "NG"]
    print("\nJuly gas basis reconciliation (TWh):")
    for year in years:
        ve = run["years"][str(year)]["volErr"]
        m923 = sum(
            z["m"][6] for c in GAS_CLASSES if c in ve for z in ve[c]["zoneMon"].values()
        )
        a923 = sum(
            z["a"][6] for c in GAS_CLASSES if c in ve for z in ve[c]["zoneMon"].values()
        )
        j930 = (
            ng[(ng["period"].dt.year == year) & (ng["period"].dt.month == 7)][
                "value_mwh"
            ].sum()
            / 1e6
        )
        print(
            f"   {year}: model(matched) {m923:6.2f} | 923 matched-grid {a923:6.2f} "
            f"| 930 NG {j930:6.2f} | model-923 {m923 - a923:+.2f} | "
            f"model-930 {m923 - j930:+.2f}"
        )


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [2023, 2024, 2025])
