"""Derive measured zone load shares from per-zone ISO load archives.

Three modes, one per ISO with a per-zone load upload:

``ercot``
    Reads the ERCOT "Actual System Load by Weather Zone" (NP6-345-CD) daily
    CSV archives under ``data/raw/reference/`` and aggregates the 8 ERCOT
    weather zones onto the model's 7 transmission zones (EAST → Northeast,
    matching ``eia_loader._ERCOT_LOAD_ZONE_GROUPS``).

``caiso``
    Reads the CAISO TAC-area actual hourly load (upload U4: OASIS ``SLD_FCST``
    with ``market_run_id=ACTUAL``) under
    ``data/raw/zone-specific-demand/CAISO/`` and maps the TAC areas
    onto the model's five trading-hub zones (PGE-TAC split between NP15 and
    ZP26; SCE-TAC split between LA_BASIN and SP15_rest; SDGE-TAC to SDGE;
    VEA-TAC to SP15_rest) via the same ``eia_loader._CAISO_TAC_ZONE_WEIGHTS``
    mapping the hourly-shape loader uses.

``nyiso``
    Reads the NYISO OASIS "pal" actual-load CSVs (upload U3:
    ``NYISO_load_actuals_<year>.csv``) under
    ``data/raw/zone-specific-demand/NYISO/`` and aggregates the eleven
    NYISO settlement zones (A–K) onto the model's five transmission zones
    (A+B+C+D+E → Upstate_West; F+G → Capital_Hudson; H+I → Lower_Hudson;
    J → NYC; K → Long_Island) via the same
    ``eia_loader._NYISO_LOAD_ZONE_GROUPS`` mapping the hourly-shape loader
    uses.

``neiso``
    Reads the ISO-NE hourly load-zone net energy for load (upload U3: ISO-NE
    SMD hourly_load CSV with Date + Hour Ending + zone columns) under
    ``data/raw/zone-specific-demand/NEISO/`` and maps the eight ISO-NE
    load zones onto the model's four transmission zones:
    North (ME+NH+VT), Central (WCMASS+SEMASS+RI), Boston (NEMA), Connecticut (CT).

All modes print the per-day raw-zone shares (to expose seasonal variability)
and the averaged model-zone shares that feed ``load_share`` in ``iso_configs``.

Run from the repo root:
    ``python scripts/data/derive_load_shares.py [ercot|caiso|nyiso|neiso]``
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia_loader import (  # noqa: E402
    _CAISO_TAC_ZONE_WEIGHTS,
    _NYISO_LOAD_ZONE_GROUPS,
)

REF = REPO / "data" / "raw" / "reference"
CAISO_TAC_DIR = REPO / "data" / "raw" / "zone-specific-demand" / "CAISO"
NYISO_DIR = REPO / "data" / "raw" / "zone-specific-demand" / "NYISO"
NEISO_DIR = REPO / "data" / "raw" / "zone-specific-demand" / "NEISO"

WZ = ["COAST", "EAST", "FAR_WEST", "NORTH", "NORTH_C", "SOUTHERN", "SOUTH_C", "WEST"]

# ERCOT weather zone -> model transmission zone. Mirrors the live mapping in
# eia_loader._ERCOT_LOAD_ZONE_GROUPS (the NP6-345 archive column names differ
# from the eia_loader keys: FAR_WEST==FWEST, NORTH_C==NCENT, SOUTH_C==SCENT,
# SOUTHERN==SOUTH). The EAST weather zone is carved out as its own Northeast
# model zone (behind the NE_LOB export limit), not folded into North. ERCOT has
# no Panhandle weather zone, so the Panhandle transmission zone receives no load
# here (its share stays 0.0). FAR_WEST stays folded into West: the Far_West
# (Permian) split was investigated and rejected, so the committed topology keeps
# FAR_WEST in West (see docs/ercot-far-west-zone-split-2026-06.md).
WZ_TO_ZONE = {
    "COAST": "Houston",
    "NORTH_C": "North",
    "EAST": "Northeast",
    "NORTH": "North",
    "SOUTH_C": "South_Central",
    "SOUTHERN": "South",
    "FAR_WEST": "West",
    "WEST": "West",
}
ZONES = ["West", "Panhandle", "North", "Northeast", "Houston", "South_Central", "South"]

CAISO_ZONES = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"]

NYISO_ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]

# ISO-NE 8 load zones -> 4 model transmission zones (same mapping as
# eia_loader._NEISO_LOAD_ZONE_GROUPS).
NEISO_ZONE_MAP: dict[str, str] = {
    "ME": "North",
    "NH": "North",
    "VT": "North",
    "NEMA": "Boston",
    ".H.NEMA": "Boston",
    "SEMASS": "Central",
    ".H.SEMASS": "Central",
    "WCMASS": "Central",
    ".H.WCMASS": "Central",
    "RI": "Central",
    "CT": "Connecticut",
}
NEISO_MODEL_ZONES = ["North", "Central", "Boston", "Connecticut"]


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
    # (PGE-TAC split 0.86/0.14 between NP15/ZP26; SCE-TAC split 0.835/0.165
    # between LA_BASIN/SP15_rest; SDGE-TAC to SDGE; VEA-TAC to SP15_rest).
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


def derive_nyiso() -> None:
    """Derive NYISO model-zone load shares from OASIS "pal" actual-load CSVs.

    Reads all ``NYISO_load_actuals_<year>.csv`` files from
    ``data/raw/zone-specific-demand/NYISO/`` (upload U3). Each file
    must carry columns ``Time Stamp`` (Eastern local, hour-beginning),
    ``Name`` (NYISO zone name CAPITL/CENTRL/… or letter A–K), and
    ``Load`` (MW).

    Prints per-day zone shares (to expose seasonal variability), the annual-
    average model-zone shares to paste into ``iso_configs._nyiso_config()``,
    and the seasonal spread per model zone.
    """
    files = sorted(NYISO_DIR.glob("NYISO_load_actuals_*.csv"))
    if not files:
        raise SystemExit(
            f"no NYISO_load_actuals_<year>.csv found under {NYISO_DIR}/ "
            "(upload U3: NYISO OASIS 'pal' actual-load hourly CSVs)"
        )

    frames = []
    for f in files:
        df = pd.read_csv(f)
        # Flexible column detection to match NYISO OASIS CSV naming variants.
        ts_col = next(
            (
                c
                for c in df.columns
                if c.lower().replace(" ", "_")
                in ("time_stamp", "timestamp", "datetime", "date_time")
            ),
            None,
        )
        zone_col = next(
            (c for c in df.columns if c.lower() in ("name", "zone", "zone_name")),
            None,
        )
        load_col = next(
            (c for c in df.columns if c.lower() in ("load", "mw", "load_mw")),
            None,
        )
        if ts_col is None or zone_col is None or load_col is None:
            print(
                f"  WARNING: {f.name} missing expected columns "
                f"(need timestamp, zone-name, MW); skipping"
            )
            continue
        sub = pd.DataFrame(
            {
                "ts": pd.to_datetime(df[ts_col], errors="coerce"),
                "zone": df[zone_col].astype(str).str.strip(),
                "mw": pd.to_numeric(df[load_col], errors="coerce"),
            }
        ).dropna()
        if sub["ts"].dt.tz is not None:
            sub["ts"] = sub["ts"].dt.tz_localize(None)
        frames.append(sub)

    if not frames:
        raise SystemExit("No usable NYISO load files found.")

    df = pd.concat(frames, ignore_index=True)
    df["mzone"] = df["zone"].map(_NYISO_LOAD_ZONE_GROUPS)
    unmapped = df["mzone"].isna()
    if unmapped.any():
        print(
            f"  WARNING: zones not in mapping (skipped): "
            f"{sorted(df.loc[unmapped, 'zone'].unique())}"
        )
        df = df[~unmapped]

    # Keep only the eleven settlement zones (drop any system totals).
    known = set(_NYISO_LOAD_ZONE_GROUPS.keys())
    df = df[df["zone"].isin(known)]

    df["day"] = df["ts"].dt.strftime("%Y-%m-%d")
    pivot = df.pivot_table(index="day", columns="mzone", values="mw", aggfunc="sum")
    pivot = pivot.reindex(columns=NYISO_ZONES, fill_value=0.0)
    shares = pivot.div(pivot.sum(axis=1), axis=0)

    n_hours = df["ts"].nunique()
    print(
        f"=== Model-zone share of NYISO load, {len(pivot)} days "
        f"({n_hours} hours; full year = 8760) ==="
    )
    hdr = "day".ljust(12) + "".join(z[:9].rjust(12) for z in NYISO_ZONES)
    print(hdr)
    for day, row in shares.iterrows():
        print(day.ljust(12) + "".join(f"{row[z]:11.1%} " for z in NYISO_ZONES))

    avg = shares.mean()
    print("\n=== Model-zone load_share (averaged; paste into iso_configs) ===")
    for z in NYISO_ZONES:
        print(f"  {z:16s} {avg[z]:.4f}")
    print(f"  {'sum':16s} {avg.sum():.4f}")

    print("\n=== Seasonal spread per model zone ===")
    for z in NYISO_ZONES:
        vals = shares[z]
        print(
            f"  {z:16s} min {vals.min():6.1%}  max {vals.max():6.1%}  "
            f"spread {vals.max() - vals.min():5.1%}"
        )

    print(
        "\n=== Zone A–K → model-zone mapping ===\n"
        "  A B C D E → Upstate_West  (upstate generation belt)\n"
        "  F G       → Capital_Hudson (Capital District + Hudson Valley)\n"
        "  H I       → Lower_Hudson   (Millwood + Dunwoodie)\n"
        "  J         → NYC\n"
        "  K         → Long_Island\n"
    )


def derive_neiso() -> None:
    """Derive NEISO model-zone load shares from ISO-NE hourly load SMD CSVs."""
    files = sorted(NEISO_DIR.glob("NEISO_load_hourly_*.csv"))
    if not files:
        raise SystemExit(
            f"no NEISO_load_hourly_<year>.csv found under {NEISO_DIR}/ "
            "(upload U3: ISO-NE hourly_load SMD CSV with Date+Hour Ending+zone columns)"
        )

    frames = []
    for f in files:
        df = pd.read_csv(f)
        df.columns = [str(c).strip() for c in df.columns]
        date_col = next((c for c in df.columns if c.upper().startswith("DATE")), None)
        he_col = next(
            (c for c in df.columns if "HOUR" in c.upper() and "END" in c.upper()), None
        )
        if date_col is None or he_col is None:
            print(f"  WARNING: {f.name} missing Date / Hour Ending columns, skipped")
            continue
        df["_date"] = pd.to_datetime(df[date_col], format="mixed", errors="coerce")
        df["_he"] = pd.to_numeric(df[he_col], errors="coerce")
        df = df[(df["_he"] >= 1) & (df["_he"] <= 24)].copy()
        df["_day"] = df["_date"].dt.strftime("%Y-%m-%d")
        frames.append(df)

    if not frames:
        raise SystemExit("No usable NEISO load files found.")

    combined = pd.concat(frames, ignore_index=True)
    zone_cols = [c for c in NEISO_ZONE_MAP if c in combined.columns]
    if not zone_cols:
        raise SystemExit(
            f"No recognised zone columns found. Expected one of: "
            f"{sorted(NEISO_ZONE_MAP)}"
        )

    # Per-day totals per raw zone.
    daily = combined.pivot_table(
        index="_day", columns=None, values=zone_cols, aggfunc="sum"
    )
    daily_totals = daily.sum(axis=1)
    shares = daily.div(daily_totals, axis=0)

    n_hours = len(combined)
    print(
        f"=== ISO-NE zone share of NEISO load, {len(daily)} days "
        f"({n_hours} hours; full year = 8760) ==="
    )
    print("day".ljust(12) + "".join(c[:8].rjust(9) for c in zone_cols))
    for day, row in shares.iterrows():
        print(day.ljust(12) + "".join(f"{row[c]:8.1%} " for c in zone_cols))

    avg = shares.mean()
    print("\n=== ISO-NE zone shares (averaged over days) ===")
    for c in zone_cols:
        print(f"  {c:10s} {avg[c]:.4f}")

    # Map to model zones.
    mshare = {z: 0.0 for z in NEISO_MODEL_ZONES}
    for c in zone_cols:
        mshare[NEISO_ZONE_MAP[c]] += float(avg[c])

    print("\n=== Model-zone load_share (averaged; paste into iso_configs) ===")
    for z in NEISO_MODEL_ZONES:
        print(f"  {z:14s} {mshare[z]:.4f}")
    print(f"  {'sum':14s} {sum(mshare.values()):.4f}")

    print("\n=== Seasonal spread per model zone across sample days ===")
    for z in NEISO_MODEL_ZONES:
        zone_raw = [c for c in zone_cols if NEISO_ZONE_MAP[c] == z]
        vals = shares[zone_raw].sum(axis=1) if zone_raw else pd.Series([0.0])
        if vals.max() > 0:
            print(
                f"  {z:14s} min {vals.min():6.1%}  max {vals.max():6.1%}  "
                f"spread {vals.max() - vals.min():5.1%}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "iso",
        nargs="?",
        default="ercot",
        choices=("ercot", "caiso", "nyiso", "neiso"),
        help="which ISO's per-zone load archive to derive shares from",
    )
    args = parser.parse_args()
    if args.iso == "ercot":
        derive_ercot()
    elif args.iso == "caiso":
        derive_caiso()
    elif args.iso == "nyiso":
        derive_nyiso()
    else:
        derive_neiso()


if __name__ == "__main__":
    main()
