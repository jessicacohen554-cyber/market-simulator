"""PJM-NEXT-14 card 2 (zero LP): where each PJM CC buys its gas, and what the keeper charges it.

Plant-level gas SUPPLY POINT from EIA-860's own per-plant fields (Schedule 2 plant file,
``data/raw/eia-860/eia860_plant.parquet``: ``Natural Gas Pipeline Name 1-3``,
``Natural Gas LDC Name``, ``Pipeline Notes``) — a measured, public, per-plant source,
already in the repo, so no new intake. The pipeline is mapped to a PRICING AREA by the
IMM's own index definitions (2025 SOM §3, footnote to "Spot average fuel price
comparison"; recorded in ``data/raw/som-competitive-conduct/README.md``):

* ``imm_production`` — the three pricing points the IMM's *production gas* averages:
  Dominion South (Dominion/Eastern Gas Transmission receipts in PA/OH/WV), Tennessee
  Zone 4 (TGP in PA/OH/WV) and Transco Leidy Line receipts (Transco in the Leidy-line
  counties of north-central / north-east PA).
* ``appalachian_receipt`` — other Marcellus/Utica receipt-zone supply that the IMM's
  three-point average does not name but which trades against the same basin: TETCO M2
  (TETCO west of the M2/M3 boundary: western PA, OH, WV), Equitrans, REX and NEXUS in
  OH, intrastate gathering/midstream, and LDC-served plants inside a Marcellus/Utica
  producing county.
* ``market`` — everything else: east market area (Transco Z5/Z6, TETCO M3, NJ/MD/DE/VA
  LDCs, Cove Point, Eastern Gas deliveries into MD/VA) and the Chicago/Midwest city
  gates (ANR, NGPL, Alliance, Vector, GTN/TransCanada, Nicor, MidAmerican, Texas Gas).

The tier table is a PIPELINE x STATE (x COUNTY for TETCO/Transco in PA) lookup, fixed
before any comparison is read. Unclassifiable rows are reported as ``unknown``; nothing
is inferred from a price.

Then, per year, from the ``fleet_only`` dump of the keeper (``_pjmnext13_fleet_dump.py``):
the capacity-weighted keeper fuel price of CC_REGULAR plants by tier against the IMM's
Platts production / east / west annual spot. Writes
``results/calibration/_pjmnext14_supply_point.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/calibration/_pjmnext14_supply_point.json"
EIA860 = REPO / "data/raw/eia-860"
SOM = REPO / "data/raw/som-competitive-conduct/som_competitive_conduct.csv"
APPALACHIA = {"PA", "OH", "WV"}
#: Transco in these PA counties sits on the Leidy Line (IMM production point);
#: elsewhere in PA it is the Zone 6 mainline (market). Williams Leidy Line route.
TRANSCO_LEIDY_PA = {
    "Clinton",
    "Lycoming",
    "Union",
    "Northumberland",
    "Columbia",
    "Luzerne",
    "Carbon",
    "Monroe",
    "Wyoming",
    "Susquehanna",
    "Bradford",
    "Tioga",
    "Sullivan",
}
#: TETCO in these PA counties is M3 (east of the Perulack/Lebanon M2/M3 boundary).
TETCO_M3_PA = {
    "Adams",
    "York",
    "Lancaster",
    "Lebanon",
    "Berks",
    "Chester",
    "Delaware",
    "Montgomery",
    "Bucks",
    "Philadelphia",
    "Northampton",
    "Lehigh",
    "Dauphin",
    "Cumberland",
    "Franklin",
    "Perry",
    "Juniata",
}
#: Marcellus / Utica producing counties (EIA shale-play footprint) where an LDC or a
#: gathering system serves a plant from local production.
PRODUCING_COUNTIES = (
    {
        ("PA", c)
        for c in (
            "Lycoming",
            "Bradford",
            "Susquehanna",
            "Tioga",
            "Wyoming",
            "Sullivan",
            "Clinton",
            "Greene",
            "Washington",
            "Butler",
            "Westmoreland",
            "Fayette",
            "Beaver",
            "Allegheny",
        )
    }
    | {
        ("OH", c)
        for c in (
            "Guernsey",
            "Belmont",
            "Monroe",
            "Carroll",
            "Harrison",
            "Noble",
            "Columbiana",
            "Jefferson",
            "Trumbull",
            "Washington",
            "Muskingum",
        )
    }
    | {("WV", c) for c in ("Marshall", "Wetzel", "Doddridge", "Tyler", "Ohio")}
)


def _has(s: str, *keys: str) -> bool:
    return any(k in s for k in keys)


def classify(state: str, county: str, pipes: list[str], ldc: str, notes: str) -> str:
    """Pricing-area tier of one plant from its EIA-860 supply-point fields."""
    county = county.strip().title() if isinstance(county, str) else ""
    text = " | ".join(p.upper() for p in pipes if p) + " || " + (notes or "").upper()
    if state in APPALACHIA:
        if _has(text, "DOMINION TRANSMISSION", "EASTERN GAS TRANSMISSION"):
            return "imm_production"
        if _has(text, "TENNESSEE GAS"):
            return "imm_production"
        if _has(text, "TRANSCONTINENTAL", "WILLIAMS") and (
            state == "PA" and county in TRANSCO_LEIDY_PA
        ):
            return "imm_production"
        if _has(text, "TEXAS EASTERN"):
            if state != "PA" or county not in TETCO_M3_PA:
                return "appalachian_receipt"
        if _has(
            text,
            "EQUITRANS",
            "EUREKA",
            "NEXUS",
            "ROCKIES EXPRESS",
            "ROVER",
            "MIDSTREAM",
            "GATHERING",
            "INTRASTATE",
            "COLUMBIA GAS TRANS",
        ):
            return "appalachian_receipt"
        if (state, county) in PRODUCING_COUNTIES and (ldc or not any(pipes)):
            return "appalachian_receipt"
    if any(pipes) or ldc:
        return "market"
    return "unknown"


def plant_tiers() -> pd.DataFrame:
    """One row per EIA-860 plant with its supply-point tier."""
    p = pd.read_parquet(EIA860 / "eia860_plant.parquet")
    cols = [
        "Natural Gas Pipeline Name 1",
        "Natural Gas Pipeline Name 2",
        "Natural Gas Pipeline Name 3",
    ]
    rows = []
    for _, r in p.iterrows():
        pipes = [str(r[c]) for c in cols if isinstance(r[c], str)]
        pipes = [x for x in pipes if not x.upper().startswith("OTHER")]
        ldc = (
            r["Natural Gas LDC Name"]
            if isinstance(r["Natural Gas LDC Name"], str)
            else ""
        )
        ldc = "" if ldc.upper().startswith("OTHER") else ldc
        notes = r["Pipeline Notes"] if isinstance(r["Pipeline Notes"], str) else ""
        rows.append(
            {
                "plant_code": str(int(r["Plant Code"])),
                "state": r["State"],
                "county": r["County"],
                "pipeline": "; ".join(pipes),
                "ldc": ldc,
                "notes": notes,
                "tier": classify(r["State"], r["County"], pipes, ldc, notes),
            }
        )
    return pd.DataFrame(rows).set_index("plant_code")


def imm_annual(y: int) -> dict:
    """IMM Platts annual spot by region."""
    d = pd.read_csv(SOM)
    d = d[
        (d.iso == "PJM")
        & (d.year == y)
        & (d.period == "annual")
        & (d.metric == "spot_price_digitized_usd_per_mmbtu")
    ]
    return {
        r.fleet_segment: round(float(r.value), 3)
        for r in d.itertuples()
        if r.fleet_segment.endswith("_gas")
    }


def per_year(y: int, f: dict, tiers: pd.DataFrame) -> dict:
    """Cap-weighted keeper CC_REGULAR fuel price by supply tier."""
    grp = f["plant_group"].astype(str)
    pc = pd.Series(f["plant_code"].astype(str)).str.split(".").str[0].to_numpy()
    s = grp == "CC_REGULAR"
    fp = f["fuel_prices"][:, :8760].mean(axis=1)
    df = pd.DataFrame({"plant": pc[s], "mw": f["pmax"][s], "fuel": fp[s]})
    pl = df.groupby("plant").apply(
        lambda g: pd.Series(
            {
                "mw": g.mw.sum(),
                "fuel": float((g.fuel * g.mw).sum() / max(g.mw.sum(), 1e-9)),
            }
        )
    )
    pl = pl.join(tiers[["tier", "state", "county", "pipeline", "ldc"]], how="left")
    pl["tier"] = pl["tier"].fillna("not_in_860")
    out = {
        "imm": imm_annual(y),
        "total_cc_mw": round(float(pl.mw.sum()), 0),
        "tiers": {},
    }
    for t, g in pl.groupby("tier"):
        out["tiers"][t] = {
            "mw": round(float(g.mw.sum()), 0),
            "mw_share": round(float(g.mw.sum() / pl.mw.sum()), 3),
            "n_plants": int(len(g)),
            "keeper_fuel_capw": round(float((g.fuel * g.mw).sum() / g.mw.sum()), 3),
            "keeper_fuel_p10_p90": [
                round(float(np.percentile(g.fuel, q)), 3) for q in (10, 90)
            ],
        }
    prod = out["imm"].get("production_gas")
    for t in out["tiers"].values():
        if prod:
            t["minus_imm_production"] = round(t["keeper_fuel_capw"] - prod, 3)
    out["plants"] = {
        k: {
            "mw": round(float(r.mw), 0),
            "fuel": round(float(r.fuel), 3),
            "tier": r.tier,
            "st": r.state if isinstance(r.state, str) else None,
        }
        for k, r in pl.sort_values("mw", ascending=False).iterrows()
    }
    return out


def main() -> None:
    """Classify, then compare per dumped year."""
    d = Path(sys.argv[1])
    years = [int(a) for a in sys.argv[2:]]
    tiers = plant_tiers()
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in years:
        z = np.load(d / f"pjmnext13_fleet_{y}.npz", allow_pickle=True)
        rec = per_year(y, {k: z[k] for k in z.files}, tiers)
        out[str(y)] = rec
        print(
            y,
            json.dumps({k: v for k, v in rec.items() if k != "plants"}, indent=1),
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
