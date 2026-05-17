"""Derive ERCOT transmission-zone load shares from NP6-345-CD sample days.

Reads the ERCOT "Actual System Load by Weather Zone" (NP6-345-CD) daily CSV
archives under ``data/reference/`` and aggregates the 8 ERCOT weather zones
onto the model's 6 transmission zones. Prints the per-day weather-zone shares
(to expose seasonal variability) and the averaged transmission-zone shares
that feed ``load_share`` in ``iso_configs._ercot_config``.

Run from the repo root: ``python scripts/derive_load_shares.py``
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd

REF = Path("data/reference")
WZ = ["COAST", "EAST", "FAR_WEST", "NORTH", "NORTH_C", "SOUTHERN", "SOUTH_C", "WEST"]

# ERCOT weather zone -> model transmission zone. ERCOT has no Panhandle
# weather zone, so the Panhandle transmission zone receives no load here.
WZ_TO_ZONE = {
    "COAST": "Houston",
    "NORTH_C": "North",
    "EAST": "North",
    "NORTH": "North",
    "SOUTH_C": "South_Central",
    "SOUTHERN": "South",
    "FAR_WEST": "West",
    "WEST": "West",
}
ZONES = ["West", "Panhandle", "North", "Houston", "South_Central", "South"]


def _daily_totals() -> list[tuple[str, dict[str, float]]]:
    """Return ``(operday, {weather_zone: daily MWh})`` for each sample file."""
    out = []
    for zp in sorted(REF.glob("*ACTUALSYSLOADWZNP6345_csv.zip")):
        with zipfile.ZipFile(zp) as z:
            df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        out.append((df["OperDay"].iloc[0], {w: float(df[w].sum()) for w in WZ}))
    return out


def main() -> None:
    days = _daily_totals()
    if not days:
        raise SystemExit(f"no NP6-345-CD archives found under {REF}/")

    print(f"=== Weather-zone share of ERCOT load, {len(days)} sample days ===")
    print("day".ljust(12) + "".join(w[:7].rjust(9) for w in WZ))
    for day, daily in days:
        tot = sum(daily.values())
        print(day.ljust(12) + "".join(f"{daily[w] / tot:8.1%} " for w in WZ))

    # Average of per-day shares -> transmission-zone load_share values.
    zshare = {z: 0.0 for z in ZONES}
    for _, daily in days:
        tot = sum(daily.values())
        for w in WZ:
            zshare[WZ_TO_ZONE[w]] += daily[w] / tot / len(days)

    print("\n=== Transmission-zone load_share (averaged) ===")
    for z in ZONES:
        print(f"  {z:14s} {zshare[z]:.4f}")
    print(f"  {'sum':14s} {sum(zshare.values()):.4f}")

    print("\n=== Seasonal spread per transmission zone ===")
    for z in ZONES:
        vals = [
            sum(d[w] for w in WZ if WZ_TO_ZONE[w] == z) / sum(d.values())
            for _, d in days
        ]
        if max(vals) > 0:
            print(
                f"  {z:14s} min {min(vals):6.1%}  max {max(vals):6.1%}  "
                f"spread {max(vals) - min(vals):5.1%}"
            )


if __name__ == "__main__":
    main()
