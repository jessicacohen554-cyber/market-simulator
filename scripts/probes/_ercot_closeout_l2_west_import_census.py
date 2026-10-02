"""Zero-LP L2 census: does a measured West-import bind carry the West LZ premium?

Close-out wave 1, step 2 (``docs/backcast-closeout-plan-2026-10.md`` §3.5).
Pre-fixed reading (charter, set before this script ran): if >= 70 % of the
hours whose actual LZ_WEST - HB_HUBAVG real-time premium exceeds $5/MWh
coincide with a measured West-import bind, build the asymmetric West import
rating (step 3); else record and close.

Definitions, fixed before the first read:

* Premium hour: ``rt(LZ_WEST) - rt(HB_HUBAVG) > 5`` in the validation-source
  zonal series (``data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet``).
* Binding: an NP6-86 SCED row with ``ShadowPrice > 0`` in any interval of the
  clock hour (``SCEDTimeStamp`` floored to the hour, CPT).
* Station zone: ``SUBSTATION -> SETTLEMENT_LOAD_ZONE`` from the ERCOT network
  model settlement-point list (``data/raw/ercot-network-model``).
* WEST-IMPORT bind (the decision class): a binding element with exactly one
  terminal in LZ_WEST and the other in a known non-West load zone (a seam
  element of the existing zonal link), or a West-boundary generic transmission
  constraint other than WESTEX (WESTEX limits West EXPORT and depresses the
  West price, so it is the wrong direction by construction).
* INTRA-WEST bind: both terminals in LZ_WEST — a sub-zonal pocket the zonal
  grain cannot represent (ERCOT-117, G); reported, never counted.
* WEST-UNKNOWN: one terminal West, the other absent from the station map;
  reported as a sensitivity, never counted.

Also reported: the base rate of each class in non-premium hours (lift), the
HB_WEST premium beside the LZ_WEST premium in premium hours (a West-WIDE
separation shows up at the 345 kV hub; a pocket shows up only at the load
zone), and limit-at-bind of the top seam elements.

Usage::

    uv run python scripts/probes/_ercot_closeout_l2_west_import_census.py --out <dir>
"""

from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
TX = RAW / "iso-specific-transmission"
COLS = [
    "SCEDTimeStamp",
    "ConstraintName",
    "ContingencyName",
    "ShadowPrice",
    "Limit",
    "Value",
    "FromStation",
    "ToStation",
]
#: West-boundary GTCs (FromStation empty) other than WESTEX. Names from the
#: NP6-86 GTC set; WESTEX is the export interface and is excluded by design.
WEST_IMPORT_GTCS: tuple[str, ...] = ()
WEST_INTERNAL_GTCS = ("MCCAMY", "CULBSN", "TRDWEL")
YEARS = tuple(range(2019, 2026))


def load_np686(year: int) -> pd.DataFrame:
    """Return the year's NP6-86 binding rows (ShadowPrice > 0)."""
    parts = []
    for f in sorted(TX.glob(f"SCEDBTCNP686_SCEDBTCNP686*_{year}.parquet")):
        parts.append(pd.read_parquet(f, columns=COLS))
    for f in sorted((RAW / "ercot").glob(f"*SCEDBTCNP686_{year}-*.zip")):
        with zipfile.ZipFile(f) as outer:
            for n in outer.namelist():
                with zipfile.ZipFile(io.BytesIO(outer.read(n))) as inner:
                    for m in inner.namelist():
                        parts.append(pd.read_csv(inner.open(m), usecols=COLS))
    d = pd.concat(parts, ignore_index=True)
    d = d[d["ShadowPrice"] > 0].drop_duplicates()
    ts = pd.to_datetime(d["SCEDTimeStamp"], format="%m/%d/%Y %H:%M:%S")
    d["hour"] = (
        (ts.dt.floor("h") - pd.Timestamp(f"{year}-01-01")) / pd.Timedelta("1h")
    ).astype(int)
    return d


def station_zone() -> dict[str, str]:
    """Return ``{substation: settlement load zone}``."""
    p = next((RAW / "ercot-network-model").glob("Settlement_Points_*.csv"))
    s = pd.read_csv(p, dtype=str).dropna(subset=["SUBSTATION", "SETTLEMENT_LOAD_ZONE"])
    return s.groupby("SUBSTATION")["SETTLEMENT_LOAD_ZONE"].first().to_dict()


def classify(d: pd.DataFrame, zmap: dict[str, str]) -> pd.Series:
    """Label each binding row seam / intra_west / west_unknown / gtc_* / other."""
    fz = d["FromStation"].map(zmap)
    tz = d["ToStation"].map(zmap)
    fw, tw = fz.eq("LZ_WEST"), tz.eq("LZ_WEST")
    gtc = d["FromStation"].isna() | d["FromStation"].eq("")
    lab = pd.Series("other", index=d.index)
    lab[(fw & tz.notna() & ~tw) | (tw & fz.notna() & ~fw)] = "seam"
    lab[fw & tw] = "intra_west"
    lab[(fw & tz.isna()) | (tw & fz.isna())] = "west_unknown"
    lab[gtc & d["ConstraintName"].isin(WEST_IMPORT_GTCS)] = "seam"
    lab[gtc & d["ConstraintName"].eq("WESTEX")] = "gtc_westex"
    lab[gtc & d["ConstraintName"].isin(WEST_INTERNAL_GTCS)] = "intra_west"
    return lab


def census_year(
    year: int, zmap: dict[str, str], lmp: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """Return the year's summary dict and its premium-hour seam-element table."""
    p = lmp[lmp["year"] == year].pivot_table(
        index="hour", columns="settlement_point", values="rt"
    )
    prem = p["LZ_WEST"] - p["HB_HUBAVG"]
    hub_w = p["HB_WEST"] - p["HB_HUBAVG"]
    hot = prem[prem > 5].index
    cold = prem[prem <= 5].index
    d = load_np686(year)
    d["cls"] = classify(d, zmap)
    by = {c: set(g["hour"]) for c, g in d.groupby("cls")}
    out = {
        "year": year,
        "premium_hours": int(len(hot)),
        "premium_mean": round(float(prem[hot].mean()), 2),
        "hb_west_premium_mean_in_premium_hours": round(float(hub_w[hot].mean()), 2),
        "share_of_lz_premium_at_hb_west": round(
            float(hub_w[hot].sum() / prem[hot].sum()), 3
        ),
    }
    for c in ("seam", "intra_west", "west_unknown", "gtc_westex"):
        h = by.get(c, set())
        out[f"{c}_cover"] = round(len(set(hot) & h) / max(len(hot), 1), 3)
        out[f"{c}_base"] = round(len(set(cold) & h) / max(len(cold), 1), 3)
    any_w = (
        by.get("intra_west", set())
        | by.get("seam", set())
        | by.get("west_unknown", set())
    )
    out["any_west_cover"] = round(len(set(hot) & any_w) / max(len(hot), 1), 3)
    seam_only = set(hot) & by.get("seam", set())
    intra_only = set(hot) & (by.get("intra_west", set()) - by.get("seam", set()))
    out["premium_mass_in_seam_hours"] = (
        round(float(prem[list(seam_only)].sum() / prem[hot].sum()), 3)
        if len(hot)
        else None
    )
    out["premium_mass_in_intra_only_hours"] = (
        round(float(prem[list(intra_only)].sum() / prem[hot].sum()), 3)
        if len(hot)
        else None
    )
    s = d[(d["cls"] == "seam") & d["hour"].isin(hot)]
    top = (
        s.groupby(["ConstraintName", "FromStation", "ToStation"])
        .agg(
            hours=("hour", "nunique"),
            limit_at_bind=("Limit", "mean"),
            shadow_mean=("ShadowPrice", "mean"),
        )
        .sort_values("hours", ascending=False)
        .head(12)
        .reset_index()
    )
    top.insert(0, "year", year)
    i = d[(d["cls"] == "intra_west") & d["hour"].isin(hot)]
    topi = (
        i.groupby(["ConstraintName"])
        .agg(hours=("hour", "nunique"), limit_at_bind=("Limit", "mean"))
        .sort_values("hours", ascending=False)
        .head(8)
        .reset_index()
    )
    out["top_intra_west"] = topi.round(1).values.tolist()
    return out, top


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    zmap = station_zone()
    lmp = pd.read_parquet(RAW / "_validation-source/actual_lmp_zonal_ERCOT.parquet")
    rows, tops = [], []
    for y in YEARS:
        r, t = census_year(y, zmap, lmp)
        rows.append(r)
        tops.append(t)
        print(json.dumps(r))
    (a.out / "l2_summary.json").write_text(json.dumps(rows, indent=1))
    pd.concat(tops).to_csv(a.out / "l2_top_seam_elements.csv", index=False)
    print(pd.concat(tops).round(1).to_string())


if __name__ == "__main__":
    main()
