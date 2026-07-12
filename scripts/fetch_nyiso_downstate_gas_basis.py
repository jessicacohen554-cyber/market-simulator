"""Fetch the NYISO downstate interruptible-gas (LDC city-gate) premium series.

Builds ``data/raw/gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv``: the
monthly premium a non-firm downstate (NYC / Long Island) gas peaker pays for
interruptible LDC city-gate gas OVER the Transco Zone 6 NY pipeline hub the
dispatch model prices its downstate gas at.

NYISO's downstate combustion-turbine peakers (NYC zone J + Long Island zone K —
the LM6000 fleet on the KeySpan / Con Edison / National Grid LDC systems) run
only a few hundred hours a year, so they hold no firm interstate pipeline
capacity: they take gas off the local LDC **city gate** on interruptible
service. Their delivered fuel index is therefore the city-gate price, not the
interstate pipeline hub. Non-firm downstate peakers are exactly the exception to
the "citygate overstates power-plant burn cost" caveat (constants.py MISO note):
that caveat is about firm-transport combined-cycle plants buying near the
*trading hub* — the interruptible peakers do face the LDC-delivered city-gate.

Two measured EIA Natural Gas monthly price series for New York State
(``https://api.eia.gov/v2/natural-gas/pri/sum``, $/Mcf):

  * ``N3050NY3`` — New York Natural Gas **Citygate** Price (the LDC city-gate
    delivered price; the downstate peaker's interruptible delivered index).
  * ``N3045NY3`` — New York Natural Gas Price **Sold to Electric Power
    Consumers** (informational: the volume-weighted delivered cost of the whole
    NY power fleet, dominated by firm-transport CCs).

The pipeline hub the model prices downstate gas at is Transco Zone 6 NY
(``data/raw/gas-prices/transco_z6_iroquois_monthly.csv`` — the same measured
NGI/EIA monthly series the NYISO hub-basis overlay uses). The downstate-peaker
premium is the city-gate delivered price over that hub, floored at zero:

    premium_m = max(0, citygate_m - transco_z6_ny_m)   [$/MMBtu]

It is positive year-round (the LDC city gate carries interstate-pipeline demand
charges + distribution + an interruptible premium over the pipeline hub in every
month), and widens in summer when NYC gas-for-power cooling demand makes
downstate interruptible gas scarce. It floors to zero only in months when the
pipeline hub *itself* spikes above the city gate (arctic cold events such as
Jan-2024), where the model's base gas is already at/above the delivered price so
no extra premium is due. Both the city-gate and the hub publish monthly and
project forward, so a forecast year regenerates the premium and it responds to
changed conditions (a tight winter/summer widens it) — CLAUDE.md rule #13
(delivered fuel prices are the canonical admissible measured input). Nothing is
fitted to a price/volume residual.

$/Mcf -> $/MMBtu via the EIA NY heat content (1.037 MMBtu/Mcf; same factor the
MISO citygate proxy uses, constants.py).

Usage:
    python scripts/fetch_nyiso_downstate_gas_basis.py [--api-key KEY]
    (DEMO_KEY works for these public series; pass a registered key to avoid the
    demo rate limit.)
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "data" / "raw" / "gas-prices" / "nyiso_downstate_ct_gas_basis_monthly.csv"
TRANSCO = REPO / "data" / "raw" / "gas-prices" / "transco_z6_iroquois_monthly.csv"

MCF_TO_MMBTU = 1.037  # EIA NY heat content (constants.py MISO citygate note)
CITYGATE = "N3050NY3"
DELIVERED_ELECTRIC = "N3045NY3"
START, END = "2023-01", "2025-12"


def _fetch(series: str, api_key: str, start: str, end: str) -> dict[str, float]:
    url = (
        "https://api.eia.gov/v2/natural-gas/pri/sum/data/"
        f"?frequency=monthly&data[0]=value&facets[series][]={series}"
        f"&start={start}&end={end}"
        "&sort[0][column]=period&sort[0][direction]=asc"
        f"&api_key={api_key}"
    )
    with urllib.request.urlopen(url, timeout=60) as resp:
        payload = json.loads(resp.read())
    return {r["period"]: float(r["value"]) for r in payload["response"]["data"]}


def _transco_monthly() -> dict[str, float]:
    frame = pd.read_csv(TRANSCO)
    return {str(r.date): float(r.transco_z6_ny_usd_mmbtu) for r in frame.itertuples()}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--api-key", default="DEMO_KEY")
    # Window + output overrides (defaults reproduce the committed 2023-2025
    # file exactly). Used by the rule-22 holdout intake to fetch an
    # out-of-training window into a scratch file that is then MERGED with the
    # committed rows (in-sample rows byte-frozen) — this script REPLACES its
    # output, so never point --out at the committed file for a partial window.
    ap.add_argument("--start", default=START, help="first month, YYYY-MM")
    ap.add_argument("--end", default=END, help="last month, YYYY-MM")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    citygate = _fetch(CITYGATE, args.api_key, args.start, args.end)
    delivered = _fetch(DELIVERED_ELECTRIC, args.api_key, args.start, args.end)
    transco = _transco_monthly()

    rows = []
    for period in sorted(set(citygate) & set(transco)):
        year, month = period.split("-")
        cg = citygate[period] / MCF_TO_MMBTU
        hub = transco[period]  # already $/MMBtu
        de = delivered.get(period)
        de = round(de / MCF_TO_MMBTU, 4) if de is not None else ""
        premium = max(0.0, cg - hub)
        rows.append(
            (int(year), int(month), round(cg, 4), round(hub, 4), de, round(premium, 4))
        )

    header = (
        "year,month,citygate_usd_mmbtu,transco_z6_ny_usd_mmbtu,"
        "delivered_electric_usd_mmbtu,premium_usd_mmbtu,source\n"
    )
    src = (
        f"EIA NG {CITYGATE} (NY citygate) minus Transco Z6 NY hub "
        "(transco_z6_iroquois_monthly.csv), $/Mcf/1.037, floored 0"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as fh:
        fh.write(header)
        for y, m, cg, hub, de, pr in rows:
            fh.write(f'{y},{m},{cg},{hub},{de},{pr},"{src}"\n')
    print(f"wrote {len(rows)} rows -> {args.out}")
    ann: dict[int, list[float]] = {}
    for y, m, cg, hub, de, pr in rows:
        ann.setdefault(y, []).append(pr)
    for y, prs in ann.items():
        print(
            f"  {y}: premium mean {sum(prs) / len(prs):.2f} $/MMBtu, "
            f"min {min(prs):.2f}, max {max(prs):.2f}"
        )


if __name__ == "__main__":
    main()
