"""Derive the year-grounded NYISO import ladder from measured neighbor hubs.

Step 4 ("import discipline"): the NYISO import tranches proxy gas-priced
neighbor hubs, so the price ladder must track the neighbor's marginal cost
year over year instead of sitting at a static (or ratio-scaled) level. This
script derives ``IMPORT_TRANCHES_BY_YEAR["NYISO"]`` from the *measured*
neighbor-hub real-time LMP in ``actual_lmp.json`` so the values are sourced,
not fit to the NYISO LMP residual.

Rule (one set of year-invariant constants, applied to every backcast year),
anchored on each tie's role in the merit order:

  marginal gas ties  price[year] = hub_p75[year] + WHEEL
      The PJM and ISO-NE ties clear only in NYISO's upper-price hours
      (PJM_west ~50% of hours, ISONE_tie ~20%), so the neighbor price *given
      NYISO is importing through that seam* is the neighbor's upper quartile,
      not its annual mean. Anchoring on the measured hub p75 (actual_lmp
      rt_pct) captures that import-hour conditional price and auto-scales it
      with the neighbor's gas:
        PJM Western Hub p75  -> PJM_west   (32.7 / 33.9 / 47.9)
        ISO-NE Mass Hub p75  -> ISONE_tie  (38.4 / 43.4 / 81.1)

  baseload ties  price[year] = home_base + WHEEL + linkage * d(PJM mean)
      HQ and Ontario are gas-insensitive always-on baseload (HQ ~zero-SRMC
      hydro 100% of hours; Ontario surplus nuclear/hydro ~70-97%), so they
      anchor on their own home price (HQ economy energy ~$11.5; Ontario HOEP
      2023 ~US$21) and rise only with their export opportunity cost — HQ at
      half the PJM annual-mean increment, Ontario at the full increment.

  WHEEL ($1.5/MWh) — NYISO import marginal losses + the seam transaction
      margin a neighbor needs over its hub to schedule into NY.

  import_scarcity[year] = mean(PJM p95, Mass Hub p95)[year] — the neighbors'
      peak economy energy in NYISO's tightest hours, falling in the low-gas
      year instead of sitting stale-expensive at a hand-set $75.

  import_scarcity[year] = mean(PJM p95, Mass Hub p95)[year]
      The scarcity tie is the neighbors' peak economy energy in NYISO's
      tightest hours; anchoring it directly to the measured neighbor price
      tail (the average of the two gas hubs' 95th percentile) replaces the
      hand-set $75/$82/$138 ladder and lets it fall in the low-gas year
      instead of sitting stale-expensive.

Tranche *capacities* are unchanged (the duration-curve fit in
derive_import_tranches.py is capacity-keyed); only the price ladder moves.

Usage:
    uv run python scripts/data/derive_nyiso_import_ladder.py
"""

import json

ACTUAL = json.load(open("data/raw/_validation-source/actual_lmp.json"))

YEARS = [2023, 2024, 2025]

# capacities (MW) and 2023 base price proxies, from IMPORT_TRANCHES["NYISO"].
CAP = {
    "HQ_hydro": 900.0,
    "IESO_Ontario": 1200.0,
    "PJM_west": 1100.0,
    "ISONE_tie": 800.0,
    "import_scarcity": 1900.0,
}
# NYISO import marginal-loss + seam transaction adder over the neighbor's
# home hub price ($/MWh). NYISO RT marginal-loss component runs ~2-4% of the
# energy price (~$1 on a $30 hub) and inter-area economy transactions clear a
# small spread; $1.5 on top of the p75 import-hour conditional price.
WHEEL = 1.5
# Marginal gas ties anchor on the measured neighbor hub p75 + WHEEL (the
# import-hour conditional neighbor price; these ties clear only in NYISO's
# upper-price hours).
GAS_TIE = {"PJM_west": "PJM", "ISONE_tie": "NEISO"}
# Gas-insensitive baseload ties: 2023 home-price base + WHEEL, then rise with
# a fraction of the PJM annual-mean increment (export opportunity cost).
#   HQ economy energy ~$11.5 (HQ hydro, ~zero SRMC); Ontario HOEP 2023
#   ~US$21 (IESO HOEP, surplus nuclear/hydro baseload).
BASELOAD_TIE = {
    "HQ_hydro": (11.5, 0.5),
    "IESO_Ontario": (21.0, 1.0),
}


def hub_mean(hub: str, year: int) -> float:
    return ACTUAL[hub][str(year)]["rt"]


def hub_p95(hub: str, year: int) -> float:
    return ACTUAL[hub][str(year)]["rt_pct"]["p95"]


def hub_pct(hub: str, year: int, pct: str) -> float:
    return ACTUAL[hub][str(year)]["rt_pct"][pct]


def main() -> None:
    print("Measured neighbor-hub anchors (actual_lmp rt / rt_pct p95):")
    for hub in ("PJM", "NEISO"):
        means = [hub_mean(hub, y) for y in YEARS]
        p95s = [hub_p95(hub, y) for y in YEARS]
        print(f"  {hub:6s} mean {means}  p95 {p95s}")
    print()

    out: dict[int, list[tuple[str, float, float]]] = {}
    for year in YEARS:
        rows = []
        for tie in ["HQ_hydro", "IESO_Ontario"]:
            base, link = BASELOAD_TIE[tie]
            price = (
                base + WHEEL + link * (hub_mean("PJM", year) - hub_mean("PJM", 2023))
            )
            rows.append((tie, CAP[tie], round(price, 1)))
        for tie in ["PJM_west", "ISONE_tie"]:
            price = hub_pct(GAS_TIE[tie], year, "p75") + WHEEL
            rows.append((tie, CAP[tie], round(price, 1)))
        scar = 0.5 * (hub_p95("PJM", year) + hub_p95("NEISO", year))
        rows.append(("import_scarcity", CAP["import_scarcity"], round(scar, 1)))
        # keep cheapest-first merit order
        rows.sort(key=lambda r: r[2])
        out[year] = rows

    print("IMPORT_TRANCHES_BY_YEAR['NYISO'] = {")
    for year in YEARS:
        print(f"    {year}: [")
        for name, cap, price in out[year]:
            print(f'        ("{name}", {cap}, {price}),')
        print("    ],")
    print("}")


if __name__ == "__main__":
    main()
