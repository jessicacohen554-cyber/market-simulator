"""NYISO phase 0 (zero LP): the CT_PEAKER merit collapse, cut at the BAND grain.

The LP row id is ``<CLASS>_<ZONE>_p<plant>_<band>``, so the committed per-unit hourly sidecar
already carries the band layer the offer curve is written in — no solve and no offer-array
rebuild is needed to read where each band sits.

THE OBJECT (docs/FINDING-nyiso240-c1-margin-bench-attribution-2026-09-19.md §7): CT_PEAKER
falls 2.43 -> 0.25 / 0.30 / 0.77 TWh from 2023 against a flat ~2.1-2.8 TWh actual, with
capacity intact, so the cause is merit order.

THE DISCRIMINATING TEST, and why it needs no gas series. Every gas class sees the same fuel
price in a given zone-hour. If each class's offer were purely `heat_rate x band x gas`, the
RATIO between two classes' offers in the same zone-hour would be a constant, invariant to the
gas level, and no fall in gas could reorder them. So:

  * a ratio that is FLAT across years says the collapse is not the offer curve's doing;
  * a ratio that RISES as gas falls localises a component of the offer that does not scale
    with fuel, and names the band it sits in.

This is measured in-hour and in-zone, so no fuel series, no deflator and no assumption about
which hub a plant prices against enters it.

Reads only committed artifacts (the nyiso-240 MER legs, whose ``dispatch/<yr>_P1.parquet`` are
sha256-identical to the keeper's). No LP is solved; nothing is swept against any gate.

Usage:
    python3 scripts/probes/nyiso241_band_merit_phase0.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_band_merit_phase0.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

FOSSIL_CLASSES = ("CT_PEAKER", "ST_GAS", "CC_REGULAR", "CC_CHP")

# The CT_PEAKER band the recommended lever touches, and its two reference classes — the two
# C1 rows still inside half a band (2023 ST_GAS, 2024 CC_REGULAR).
CT_CLASS = "CT_PEAKER"
REFERENCE_CLASSES = ("ST_GAS", "CC_REGULAR")


def _is_plant_token(tok: str) -> bool:
    """True for the ``p<digits>`` plant segment of an LP row id.

    Tested on the digits rather than the leading ``p`` alone: the band name ``peak`` also
    starts with ``p``, and reading it as a plant token silently drops the entire peak band.
    """
    return len(tok) > 1 and tok[0] == "p" and tok[1:].isdigit()


def parse_band(unit_id: str) -> str:
    """Return the band segment of an LP row id, or '' when the id carries none."""
    tail = unit_id.rsplit("_", 1)[-1]
    return "" if _is_plant_token(tail) else tail


def load_rows(leg: Path, year: int) -> pd.DataFrame:
    """Load the leg's P1 per-row hourly offers with class, zone and band attached."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=[
            "pass",
            "unit_id",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    unit = unit[unit["pass"] == "P1"].copy()
    unit["band"] = unit["unit_id"].map(parse_band)
    return unit


def band_table(unit: pd.DataFrame) -> dict:
    """Capacity-weighted mean offer and dispatched energy, per class x band."""
    out: dict[str, dict] = {}
    for klass in FOSSIL_CLASSES:
        sub = unit[unit["plant_group"] == klass]
        if sub.empty:
            continue
        rows: dict[str, dict] = {}
        for band, grp in sub.groupby("band"):
            cap = grp.groupby("unit_id")["cap_mw"].max()
            weights = grp["cap_mw"].to_numpy()
            wsum = weights.sum()
            rows[band or "_none"] = {
                "rows": int(grp["unit_id"].nunique()),
                "cap_mw": float(cap.sum()),
                "offer_capwt": float((grp["mc"].to_numpy() * weights).sum() / wsum)
                if wsum
                else float("nan"),
                "offer_median": float(grp["mc"].median()),
                "twh": float(grp["mw"].sum() / 1e6),
            }
        out[klass] = rows
    return out


def cross_class_ratio(unit: pd.DataFrame) -> dict:
    """In-zone, in-hour ratio of the CT_PEAKER offer to each reference class's offer.

    Computed on the CHEAPEST row of each class in that zone-hour — the row that decides
    whether the class enters the merit order at all — so the ratio is not moved by how many
    tranches a class happens to be split into.
    """
    cheapest = (
        unit.groupby(["plant_group", "zone", "hour"], as_index=False)["mc"]
        .min()
        .pivot_table(index=["zone", "hour"], columns="plant_group", values="mc")
    )
    out: dict[str, dict] = {}
    for ref in REFERENCE_CLASSES:
        if CT_CLASS not in cheapest.columns or ref not in cheapest.columns:
            continue
        pair = cheapest[[CT_CLASS, ref]].dropna()
        ratio = pair[CT_CLASS] / pair[ref]
        spread = pair[CT_CLASS] - pair[ref]
        out[f"CT_over_{ref}"] = {
            "zone_hours": int(len(pair)),
            "ratio_p25": float(np.percentile(ratio, 25)),
            "ratio_median": float(np.median(ratio)),
            "ratio_p75": float(np.percentile(ratio, 75)),
            "spread_median_usd": float(np.median(spread)),
            "ct_cheapest_median": float(pair[CT_CLASS].median()),
            "ref_cheapest_median": float(pair[ref].median()),
        }
    return out


def ct_band_vs_price(unit: pd.DataFrame, system: pd.DataFrame) -> dict:
    """Zone-hours in which each CT_PEAKER band's offer is at or below its own zone's LMP."""
    price_col = "price" if "price" in system.columns else "lmp"
    prices = system[["zone", "hour", price_col]].rename(columns={price_col: "price"})
    sub = unit[unit["plant_group"] == CT_CLASS]
    out: dict[str, dict] = {}
    for band, grp in sub.groupby("band"):
        cheapest = grp.groupby(["zone", "hour"], as_index=False)["mc"].min()
        joined = cheapest.merge(prices, on=["zone", "hour"], how="inner")
        if joined.empty:
            continue
        out[band or "_none"] = {
            "zone_hours": int(len(joined)),
            "clears": int((joined["price"] >= joined["mc"]).sum()),
            "clear_share": float((joined["price"] >= joined["mc"]).mean()),
            "offer_median": float(joined["mc"].median()),
            "price_median": float(joined["price"].median()),
        }
    return out


def main() -> None:
    """Run the band-grain decomposition over each committed per-year leg."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report: dict[str, dict] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = int(leg.name.rsplit("_", 1)[-1])
        unit = load_rows(leg, year)
        system = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
        report[str(year)] = {
            "bands": band_table(unit),
            "cross_class_ratio": cross_class_ratio(unit),
            "ct_band_vs_price": ct_band_vs_price(unit, system),
        }

        print(f"=== {year} ===")
        for klass in FOSSIL_CLASSES:
            bands = report[str(year)]["bands"].get(klass, {})
            parts = " ".join(
                f"{b}:{d['offer_capwt']:.1f}/{d['twh']:.2f}TWh"
                for b, d in sorted(bands.items())
            )
            print(f"  {klass:<12} {parts}")
        for name, row in report[str(year)]["cross_class_ratio"].items():
            print(
                f"  {name:<20} cheapest-row ratio median {row['ratio_median']:.3f} "
                f"(spread {row['spread_median_usd']:+.2f} $/MWh; "
                f"{row['ct_cheapest_median']:.2f} vs {row['ref_cheapest_median']:.2f})"
            )
        for band, row in sorted(report[str(year)]["ct_band_vs_price"].items()):
            print(
                f"  CT band {band:<10} offer p50 {row['offer_median']:>7.2f} vs price p50 "
                f"{row['price_median']:>7.2f} -> clears {row['clear_share'] * 100:>5.1f} % of zone-hours"
            )

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
