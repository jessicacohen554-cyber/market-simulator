"""NYISO phase 0 (zero LP): split each fossil offer EXACTLY into energy-proportional and fixed.

The identification is arithmetic and needs no fuel series, no deflator and no assumption about
which hub a plant prices against. Within one plant and hour, two bands of the same class differ
ONLY by their registered band multiplier on the same base heat rate, while everything that is not
proportional to fuel burn — VOM, the P0->P1 amortized startup markup — is the same row-to-row:

    mc(b1) - mc(b2) = HR_base * (band(b1) - band(b2)) * F        (F = $/MMBtu incl. any carbon)
    =>  HR_base * F  =  (mc(b1) - mc(b2)) / (band(b1) - band(b2))
    =>  fixed(plant, hour)  =  mc(b2) - HR_base * F * band(b2)

The band multipliers are the REGISTERED values in
``pipeline/backcast_config._NYISO_OFFER_CURVE`` — quoted, never re-derived, and nothing here is
fitted or swept (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).

WHY IT MATTERS. A multiplicative band scales with fuel, so on its own it can never reorder the
merit stack as gas falls. A FIXED $/MWh component can, and does so hardest in the cheapest-gas
year — which is 2023, the year CT_PEAKER collapses from 2.43 to 0.25 TWh against a flat actual.
This probe measures how large that fixed component is in each class, so the successor lever is
aimed at the term that actually moves rather than at the band that happens to be nearest to hand.

Reads only committed artifacts (the nyiso-240 MER legs, whose ``dispatch/<yr>_P1.parquet`` are
sha256-identical to the keeper's). No LP is solved.

Usage:
    python3 scripts/probes/nyiso241_fixed_wedge.py \
        --legs results/calibration/nyiso_mer_2026-09-19_{2022,2023,2024,2025} \
        --out results/calibration/_nyiso241_fixed_wedge.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

# Registered band multipliers, quoted from `_NYISO_OFFER_CURVE`. For each class the pair used
# for the identification is the widest one whose two bands both resolve to real LP rows, so the
# divisor is as far from zero as the curve allows.
IDENT_PAIRS: dict[str, tuple[str, str, float, float]] = {
    # class:        (band_hi, band_lo, mult_hi, mult_lo)
    "CT_PEAKER": ("committed", "econlo", 1.35, 1.00),
    "ST_GAS": ("econhi", "committed", 1.13, 1.05),
    "CC_REGULAR": ("econc05", "committed", 1.00, 0.90),
    "CC_CHP": ("econc05", "committed", 1.24, 0.90),
}


def _is_plant_token(tok: str) -> bool:
    """True for the ``p<digits>`` plant segment of an LP row id.

    Tested on the digits rather than the leading ``p`` alone: the band name ``peak`` also
    starts with ``p``, and reading it as a plant token silently drops the entire peak band.
    """
    return len(tok) > 1 and tok[0] == "p" and tok[1:].isdigit()


def parse_parts(unit_id: str) -> tuple[str, str]:
    """Return (plant token, band) for an LP row id ``<CLASS>_<ZONE>_p<plant>_<band>``."""
    tail = unit_id.rsplit("_", 1)[-1]
    if _is_plant_token(tail):
        return tail, ""
    head = unit_id.rsplit("_", 2)
    return (head[-2] if len(head) >= 2 else ""), tail


def wedge_for_year(leg: Path, year: int) -> dict:
    """Decompose every plant-hour offer in each class into energy-proportional and fixed."""
    unit = pd.read_parquet(
        leg / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "unit_id", "plant_group", "zone", "hour", "mc", "cap_mw"],
    )
    unit = unit[unit["pass"] == "P1"].copy()
    parts = [parse_parts(uid) for uid in unit["unit_id"]]
    unit["plant"] = [p for p, _ in parts]
    unit["band"] = [b for _, b in parts]

    out: dict[str, dict] = {}
    for klass, (b_hi, b_lo, m_hi, m_lo) in IDENT_PAIRS.items():
        sub = unit[unit["plant_group"] == klass]
        if sub.empty:
            continue
        wide = sub.pivot_table(index=["plant", "hour"], columns="band", values="mc")
        if b_hi not in wide.columns or b_lo not in wide.columns:
            continue
        pair = wide[[b_hi, b_lo]].dropna()
        if pair.empty:
            continue
        # HR_base * F, the $/MWh the plant pays for fuel at a band multiplier of exactly 1.0.
        hr_f = (pair[b_hi] - pair[b_lo]) / (m_hi - m_lo)
        fixed = pair[b_lo] - hr_f * m_lo
        # Capacity weight: the plant's own cap in this class, broadcast over its hours.
        caps = sub.groupby("plant")["cap_mw"].max()
        w = caps.reindex(pair.index.get_level_values("plant")).to_numpy()
        w = np.where(np.isfinite(w), w, 0.0)
        wsum = w.sum()
        offer_lo = pair[b_lo].to_numpy()
        out[klass] = {
            "plant_hours": int(len(pair)),
            "ident_pair": f"{b_hi}({m_hi}) - {b_lo}({m_lo})",
            "energy_usd_per_mwh_at_band_1": float((hr_f.to_numpy() * w).sum() / wsum)
            if wsum
            else float("nan"),
            "fixed_usd_per_mwh": float((fixed.to_numpy() * w).sum() / wsum)
            if wsum
            else float("nan"),
            "offer_at_lo_band": float((offer_lo * w).sum() / wsum)
            if wsum
            else float("nan"),
            "fixed_share": float((fixed.to_numpy() * w).sum() / (offer_lo * w).sum())
            if wsum
            else float("nan"),
            "fixed_median": float(fixed.median()),
            "negative_fixed_share_of_rows": float((fixed < 0).mean()),
        }
    return out


def main() -> None:
    """Run the exact wedge decomposition over each committed per-year leg."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report: dict[str, dict] = {}
    for leg_str in args.legs:
        leg = Path(leg_str)
        year = int(leg.name.rsplit("_", 1)[-1])
        report[str(year)] = wedge_for_year(leg, year)
        print(f"=== {year} ===")
        for klass, row in report[str(year)].items():
            print(
                f"  {klass:<12} [{row['ident_pair']:<26}] energy@1.0 "
                f"{row['energy_usd_per_mwh_at_band_1']:>7.2f}  fixed {row['fixed_usd_per_mwh']:>7.2f} "
                f"$/MWh  = {row['fixed_share'] * 100:>5.1f} % of a {row['offer_at_lo_band']:>7.2f} offer"
            )

    Path(args.out).write_text(json.dumps(report, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
