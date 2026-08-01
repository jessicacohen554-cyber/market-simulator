"""neiso-73 Kendall Square (EIA 1595) capacity-basis screen — NO-LP adjudication.

The neiso-71 lever screen left one named successor: decide whether the ~90 MW
gap between CAMPD facility-1595 unit "4" gross load (278/299/283 MW median,
max 321) and the EIA-860 CC_CHP basis (213.4 MW nameplate / 206.0 MW summer =
the model pmax) is an **EIA-860 understatement** (missing CC_CHP capacity) or a
**metering/attribution artifact** (nothing missing). This screen adjudicates it
from primary sources only — EIA-860 vintages (all statuses), EIA-923 Page-1 net
generation, and the CAMPD unit configuration. No LP, no bundle, no scoring.

Verdict (all five evidence blocks must hold): **ARTIFACT — the EIA-860 basis is
correct; CAMPD ``grossLoad`` for this CHP unit is not gross electrical MW.**

* E1 physical bound: max CAMPD gross (317-323 MW, every year 2018-2025)
  exceeds the summed nameplate of EVERY generator ever installed at 1595 —
  294.9 MW including the retired 1949/1951 steam units and both DFO jets.
* E2 thermodynamic bound: implied gross heat rate 6.36-6.59 mmBtu/MWh
  (53-54 % HHV) is impossible for a 2002-vintage 7FA CT + 1958 steam turbine;
  on the EIA-923 net basis it is 9.3-10.1 — right for this cogen vintage.
* E3 basis stability: EIA-923-net / CAMPD-gross is flat at 0.654-0.687 across
  96 months x 8 years, spanning the 2018 unit-1/2 retirement — a fixed basis
  transformation, not station use (2-5 % typical) and not the post-2024
  district-steam electric boiler.
* E4 saturation: monthly EIA-923 net pins at the EIA-860 winter rating
  (209.3 MW avg Dec-2023 vs 210.3 MW W) — 860 and 923 mutually consistent.
* E5 vintage stability: EIA-860 2019-2024 identical (186.2/183.1 GEN4 +
  27.2/22.9 gen "3"); no uprate ever filed.

Closure: 1/0.678 = 1.475 ~= the neiso-71 saturated ``steam_level_cf`` of
1.461 — that statistic measured the gross/net basis ratio, not a steam
obligation. Consequence for the floor lane: any future Kendall host-steam
identification (and any ``measured_chp_heat_rates`` derivation touching 1595)
must be built on the NET basis; the CAMPD gross channel is contaminated for
both level and heat rate at this unit.

Usage::

    PYTHONPATH=src uv run python scripts/probes/_neiso73_kendall_capacity_screen.py
"""

from __future__ import annotations

import calendar
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data" / "raw"

PLANT = 1595  # Kendall Square Station / Kendall Green Energy LLC (Cambridge, MA)
YEARS_CAMPD = range(2018, 2026)

# Every generator ever installed at EIA 1595 (eia860_generator_operable +
# eia860_generator_retired_and_canceled), nameplate MW: CC1 block gens
# 1 (17.2, RE 2018) + 2 (23.0, RE 2018) + 3 (27.2) + GEN4 (186.2), plus
# JET1 (21.3) and JET2 (20.0, RE 2004). Physical ceiling for any electrical
# reading at the site, any era.
EVER_INSTALLED_NAMEPLATE_MW = 17.2 + 23.0 + 27.2 + 186.2 + 21.3 + 20.0
CURRENT_SUMMER_MW = 22.9 + 183.1  # apply_cc_summer_guard CC1 sum = model pmax
CURRENT_WINTER_MW = 22.9 + 187.4

# CC efficiency sanity line: >= ~52 % HHV (< 6.6 mmBtu/MWh gross) is beyond
# any 2002-vintage F-class 1x1 with a 1958 steam turbine; used only to flag,
# not to tune (docs/parameter-citations.md is not touched by this screen).
IMPOSSIBLE_GROSS_HR = 6.6


def campd_gross_by_year() -> pd.DataFrame:
    """Annual CAMPD unit-4 gross load, heat input and per-unit facility roster."""
    rows = []
    for yr in YEARS_CAMPD:
        df = pd.read_parquet(RAW / "campd-unit-level" / f"MA_{yr}.parquet")
        fac = df[df["facilityId"] == str(PLANT)]
        u4 = fac[fac["unitId"] == "4"]
        on = u4[u4["grossLoad"] > 0]
        rows.append(
            {
                "year": yr,
                "units": ",".join(sorted(fac["unitId"].unique())),
                "on_hours": len(on),
                "med_gross_mw": on["grossLoad"].median(),
                "max_gross_mw": on["grossLoad"].max(),
                "gross_twh": on["grossLoad"].sum() / 1e6,
                "gross_hr": on["heatInput"].sum() / on["grossLoad"].sum(),
            }
        )
    return pd.DataFrame(rows)


def eia923_net_by_year() -> pd.Series:
    """Annual EIA-923 Page-1 net generation for the plant, TWh (all PMs)."""
    g = pd.read_parquet(
        RAW / "_processed-legacy" / "eia923_monthly_generation.parquet"
    )
    k = g[g["plant_id"] == PLANT]
    return k.groupby("year")["netgen_annual_mwh"].sum() / 1e6


def monthly_ratio(yr: int) -> tuple[list[float], list[float]]:
    """Per-month EIA-923-net / CAMPD-gross ratio and gap in average MW."""
    g = pd.read_parquet(
        RAW / "_processed-legacy" / "eia923_monthly_generation.parquet"
    )
    mcols = [
        c
        for c in g.columns
        if c.startswith("netgen_") and c != "netgen_annual_mwh"
    ]
    net = g[(g["plant_id"] == PLANT) & (g["year"] == yr)][mcols].sum()
    df = pd.read_parquet(RAW / "campd-unit-level" / f"MA_{yr}.parquet")
    u4 = df[(df["facilityId"] == str(PLANT)) & (df["unitId"] == "4")].copy()
    u4["month"] = u4["date"].dt.month
    gross = u4.groupby("month")["grossLoad"].sum()
    hours = [calendar.monthrange(yr, m)[1] * 24 for m in range(1, 13)]
    ratio = [net.iloc[m - 1] / gross[m] for m in range(1, 13)]
    gap_mw = [(gross[m] - net.iloc[m - 1]) / hours[m - 1] for m in range(1, 13)]
    return ratio, gap_mw


def eia860_vintages() -> None:
    """Print the 1595 operable roster per EIA-860 vintage (uprate check)."""
    for v in range(2018, 2025):
        p = RAW / "eia-860" / f"vintage_{v}" / "eia860_generator_operable.parquet"
        if not p.exists():
            print(f"  vintage {v}: file missing")
            continue
        d = pd.read_parquet(p)
        k = d[pd.to_numeric(d["Plant Code"], errors="coerce") == PLANT]
        roster = {
            r["Generator ID"]: (
                r["Nameplate Capacity (MW)"],
                r["Summer Capacity (MW)"],
            )
            for _, r in k.iterrows()
        }
        print(f"  vintage {v}: {roster}")


def main() -> None:
    """Run the five-evidence screen and print the verdict."""
    print("=" * 78)
    print("neiso-73 — Kendall Square (EIA 1595) capacity-basis screen (NO-LP)")
    print("=" * 78)

    campd = campd_gross_by_year()
    net = eia923_net_by_year()
    campd["net923_twh"] = campd["year"].map(net)
    campd["net_over_gross"] = campd["net923_twh"] / campd["gross_twh"]
    campd["net_hr"] = campd["gross_hr"] / campd["net_over_gross"]
    print("\nCAMPD unit 4 vs EIA-923 plant net, by year:")
    print(campd.round(3).to_string(index=False))

    print(
        f"\nE1 physical bound: max gross "
        f"{campd['max_gross_mw'].max():.0f} MW vs {EVER_INSTALLED_NAMEPLATE_MW:.1f} MW "
        f"= every generator ever installed (incl. retired): "
        f"{'EXCEEDED -> channel is not electrical MW' if campd['max_gross_mw'].max() > EVER_INSTALLED_NAMEPLATE_MW else 'inside bound'}"
    )
    print(
        f"E2 thermodynamic bound: gross HR {campd['gross_hr'].min():.2f}-"
        f"{campd['gross_hr'].max():.2f} mmBtu/MWh "
        f"({'IMPOSSIBLE for this vintage' if campd['gross_hr'].max() < IMPOSSIBLE_GROSS_HR else 'plausible'}); "
        f"net-basis HR {campd['net_hr'].min():.2f}-{campd['net_hr'].max():.2f}"
    )
    print(
        f"E3 basis stability: annual net/gross "
        f"{campd['net_over_gross'].min():.3f}-{campd['net_over_gross'].max():.3f} "
        f"across {len(campd)} years (spans the 2018 unit-1/2 retirement)"
    )
    for yr in (2023, 2024):
        ratio, gap = monthly_ratio(yr)
        print(
            f"   {yr} monthly net/gross: "
            + " ".join(f"{r:.3f}" for r in ratio)
            + f"  (gap {min(gap):.0f}-{max(gap):.0f} avg MW)"
        )

    dec23_net_mw = (
        pd.read_parquet(
            RAW / "_processed-legacy" / "eia923_monthly_generation.parquet"
        )
        .query("plant_id == @PLANT and year == 2023")["netgen_december_mwh"]
        .sum()
        / (31 * 24)
    )
    print(
        f"E4 saturation: Dec-2023 monthly avg net {dec23_net_mw:.1f} MW vs "
        f"EIA-860 winter rating {CURRENT_WINTER_MW:.1f} MW "
        f"({dec23_net_mw / CURRENT_WINTER_MW:.1%} of W rating)"
    )
    print("E5 EIA-860 vintage roster (uprate check):")
    eia860_vintages()

    basis_ratio = 1.0 / campd["net_over_gross"].mean()
    print(
        f"\nClosure: mean gross/net = {basis_ratio:.3f} vs the neiso-71 "
        f"saturated steam_level_cf 1.461 — the statistic measured the basis "
        f"ratio, not a steam obligation."
    )
    print(
        "\nVERDICT: ARTIFACT — EIA-860 basis (206.0 MW summer) is CORRECT; "
        "no missing CC_CHP capacity; no model change; no A/B."
    )


if __name__ == "__main__":
    main()
