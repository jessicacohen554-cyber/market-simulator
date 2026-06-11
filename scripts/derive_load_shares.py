"""Derive measured zone load shares from per-zone ISO load archives.

Two modes, one per ISO with a per-zone load upload:

``ercot``
    Reads the ERCOT "Actual System Load by Weather Zone" (NP6-345-CD) daily
    CSV archives under ``data/reference/`` and aggregates the 8 ERCOT weather
    zones onto the model's 6 transmission zones.

``caiso``
    Reads the CAISO TAC-area actual hourly load (upload U4: OASIS ``SLD_FCST``
    with ``market_run_id=ACTUAL``) under
    ``inputs/raw-data/zone-specific-demand/CAISO/`` and maps the TAC areas
    onto the model's three trading-hub zones (PGE-TAC split between NP15 and
    ZP26, SCE + SDG&E + VEA to SP15) via the same
    ``eia_loader._CAISO_TAC_ZONE_WEIGHTS`` mapping the hourly-shape loader
    uses.

Both print the per-day raw-zone shares (to expose seasonal variability) and
the averaged model-zone shares that feed ``load_share`` in
``iso_configs``.

Run from the repo root: ``python scripts/derive_load_shares.py [ercot|caiso]``
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import _CAISO_TAC_ZONE_WEIGHTS  # noqa: E402

REF = REPO / "data" / "reference"
CAISO_TAC_DIR = REPO / "inputs" / "raw-data" / "zone-specific-demand" / "CAISO"

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

CAISO_ZONES = ["NP15", "ZP26", "SP15"]


def _daily_totals() -> list[tuple[str, dict[str, float]]]:
    """Return ``(operday, {weather_zone: daily MWh})`` for each sample file."""
    out = []
    for zp in sorted(REF.glob("*ACTUALSYSLOADWZNP6345_csv.zip")):
        with zipfile.ZipFile(zp) as z:
            df = pd.read_csv(io.BytesIO(z.read(z.namelist()[0])))
        out.append((df["OperDay"].iloc[0], {w: float(df[w].sum()) for w in WZ}))
    return out


def derive_ercot() -> None:
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


def derive_caiso() -> None:
    files = sorted(CAISO_TAC_DIR.glob("CAISO_tac_load_hourly_*.csv"))
    if not files:
        raise SystemExit(
            f"no CAISO_tac_load_hourly_<year>.csv found under {CAISO_TAC_DIR}/ "
            "(upload U4: OASIS SLD_FCST ACTUAL TAC-area load)"
        )
    df = pd.concat(
        [pd.read_csv(f, parse_dates=["interval_start_gmt"]) for f in files],
        ignore_index=True,
    )
    # Keep only the component TACs (drop the "CA ISO-TAC" system total) and
    # the verbatim duplicates that overlapping OASIS pulls produce.
    df = df[df["tac_area"].isin(_CAISO_TAC_ZONE_WEIGHTS)]
    df = df.drop_duplicates(subset=["tac_area", "interval_start_gmt"])
    local = df["interval_start_gmt"].dt.tz_convert("America/Los_Angeles")
    df = df.assign(day=local.dt.strftime("%Y-%m-%d"))

    tacs = sorted(df["tac_area"].unique())
    daily = df.pivot_table(index="day", columns="tac_area", values="mw", aggfunc="sum")
    shares = daily.div(daily.sum(axis=1), axis=0)

    n_hours = df["interval_start_gmt"].nunique()
    print(
        f"=== TAC-area share of CAISO load, {len(daily)} days "
        f"({n_hours} hours; full U4 = 8760/yr) ==="
    )
    print("day".ljust(12) + "".join(t.replace("-TAC", "")[:8].rjust(9) for t in tacs))
    for day, row in shares.iterrows():
        print(day.ljust(12) + "".join(f"{row[t]:8.1%} " for t in tacs))

    avg = shares.mean()
    print("\n=== TAC-area shares (averaged over days) ===")
    for t in tacs:
        print(f"  {t:10s} {avg[t]:.4f}")

    # TAC -> model zone via the same weights the hourly-shape loader uses
    # (PGE-TAC split 0.86/0.14 between NP15/ZP26, rest to SP15).
    zshare = {z: 0.0 for z in CAISO_ZONES}
    for t in tacs:
        for zone, weight in _CAISO_TAC_ZONE_WEIGHTS[t].items():
            zshare[zone] += weight * float(avg[t])

    print("\n=== Trading-hub load_share (averaged; paste into iso_configs) ===")
    for z in CAISO_ZONES:
        print(f"  {z:14s} {zshare[z]:.4f}")
    print(f"  {'sum':14s} {sum(zshare.values()):.4f}")

    print("\n=== Spread per model zone across sample days ===")
    for z in CAISO_ZONES:
        vals = shares.mul(
            [_CAISO_TAC_ZONE_WEIGHTS[t].get(z, 0.0) for t in tacs], axis=1
        ).sum(axis=1)
        print(
            f"  {z:14s} min {vals.min():6.1%}  max {vals.max():6.1%}  "
            f"spread {vals.max() - vals.min():5.1%}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "iso", nargs="?", default="ercot", choices=("ercot", "caiso"),
        help="which ISO's per-zone load archive to derive shares from",
    )
    args = parser.parse_args()
    if args.iso == "ercot":
        derive_ercot()
    else:
        derive_caiso()


if __name__ == "__main__":
    main()
