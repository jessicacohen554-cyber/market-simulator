"""NWPP-NEXT-15 phase 0: captive vs non-captive coal receipts census (zero LP).

Applies the identification rule fixed in
docs/records/nwpp/PHASE0-nwppnext15-captive-mine-2026-09-30.md §1 (commit f6e07ffe) to the
NWPP model coal fleet, 2019-2024, and writes a JSON census next to that doc.
"""

import json
import sys

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR as DATA_RAW

TRANCHES = DATA_RAW / "_processed-legacy" / "thermal_tranches-perunit-vintage-NWPP.csv"
RECEIPTS = DATA_RAW / "coal-receipts"
YEARS = range(2019, 2025)
MINE_MOUTH_MODES = {"TC", "TR"}  # EIA-923 codes: TC = tramway/conveyor/slurry, TR = truck (PHASE0 §1 erratum)


def classify(df: pd.DataFrame) -> pd.Series:
    """Return True where a receipt row is captive under PHASE0 §1."""
    mode = df["Primary Transportation Mode"].astype(str).str.strip().str.upper()
    same_state = df["Coalmine State"].astype(str).str.strip() == df["Plant State"].astype(str).str.strip()
    not_spot = df["Purchase Type"].astype(str).str.strip().str.upper() != "S"
    return mode.isin(MINE_MOUTH_MODES) & same_state & not_spot


def wavg(df: pd.DataFrame) -> float | None:
    """MMBtu-weighted FUEL_COST in $/MMBtu over rows with a reported cost."""
    d = df[df["cost"].notna() & (df["mmbtu"] > 0)]
    if d.empty:
        return None
    return round(float((d["cost"] * d["mmbtu"]).sum() / d["mmbtu"].sum()) / 100.0, 3)


def main() -> None:
    """Run the census and print a summary table."""
    tr = pd.read_csv(TRANCHES)
    coal = tr[tr["plant_group"].astype(str).str.startswith("COAL")]
    plants = dict(zip(coal["plant_code"].astype(int), coal["name"]))
    out = {"rule_commit": "f6e07ffe", "fleet_source": str(TRANCHES.relative_to(DATA_RAW.parent.parent)), "rows": []}
    for y in YEARS:
        r = pd.read_csv(RECEIPTS / f"coal_receipts_{y}.csv", low_memory=False)
        r = r[r["Plant Id"].astype(int).isin(plants)]
        r["mmbtu"] = pd.to_numeric(r["QUANTITY"], errors="coerce").fillna(0) * pd.to_numeric(
            r["Average Heat Content"], errors="coerce"
        ).fillna(0)
        r["cost"] = pd.to_numeric(r["FUEL_COST"], errors="coerce")
        r["captive"] = classify(r)
        for pid, g in r.groupby("Plant Id"):
            tot = g["mmbtu"].sum()
            if tot <= 0:
                continue
            cap = g.loc[g["captive"], "mmbtu"].sum()
            row = {
                "year": y,
                "plant": int(pid),
                "name": plants[int(pid)],
                "captive_share": round(float(cap / tot), 3),
                "p_captive": wavg(g[g["captive"]]),
                "p_noncaptive": wavg(g[~g["captive"]]),
                "p_blend": wavg(g),
                "captive_sources": sorted(g.loc[g["captive"], "Coalmine Name"].dropna().astype(str).unique().tolist()),
                "noncaptive_sources": sorted(
                    g.loc[~g["captive"], "Coalmine Name"].dropna().astype(str).unique().tolist()
                ),
            }
            row["mixed"] = 0 < row["captive_share"] < 1
            row["gap"] = (
                round(row["p_blend"] - row["p_noncaptive"], 3)
                if row["mixed"] and row["p_blend"] is not None and row["p_noncaptive"] is not None
                else None
            )
            out["rows"].append(row)
        missing = sorted(set(plants) - set(r["Plant Id"].astype(int)))
        out.setdefault("no_receipts", {})[y] = [f"{p} {plants[p]}" for p in missing]
    dest = sys.argv[1] if len(sys.argv) > 1 else "captive_census.json"
    with open(dest, "w") as f:
        json.dump(out, f, indent=1)
    df = pd.DataFrame(out["rows"])
    pd.set_option("display.width", 250)
    print(df[["year", "plant", "name", "captive_share", "p_captive", "p_noncaptive", "p_blend", "gap", "mixed"]]
          .to_string(index=False))
    print("no receipts:", json.dumps(out["no_receipts"]))


if __name__ == "__main__":
    main()
