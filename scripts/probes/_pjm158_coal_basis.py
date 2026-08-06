"""pjm-158 Phase-0 question C — what basis does the bench's coal census sit on?

pjm-157 §5 left the 2022 C1/C2 coal rows unreadable: on an identical
42-plant / 38,003 MW census, EIA-930 ``COL`` minus the bench's CAMPD coal is
**+19.49 TWh (11.7 %)** in 2022 against +7.26 / +7.05 / +11.02 (5.8-7.6 %)
in-sample, so the two available bases disagree about the SIGN of the model's
2022 coal error.  This probe adjudicates between the three candidate causes the
handoff names:

* **(a) net/gross convention** — a parasitic-load or metering-basis difference;
* **(b) out-of-registry / non-CEMS PJM coal** — real coal inside the 930 BA
  footprint that the bench's plant census does not carry;
* **(c) a 2022 CAMPD extract defect** — missing units or months in the extract.

Everything is read from committed artifacts plus ``data/raw/`` sources that are
already on disk: the per-year bench parts (which carry THREE independent coal
measures — 930 ``COL``, the CAMPD ``coal_cems`` sum and the EIA-923 ``classFull``
grid total), the raw EIA-930 fuel-type frames, and EIA-860 operable/retired
capacity.  **No LP is solved and no year is scored**, so this is legal under the
active holdout freeze (CLAUDE.md rule 22); 2022 is READ, never solved.

Run:  .venv/bin/python scripts/probes/_pjm158_coal_basis.py
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

TWH = 1e6
YEARS = (2022, 2023, 2024, 2025)
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_WC")
BENCH = "frontend/data/backcast/bench/PJM/{year}.json.gz"


def load_bench(year: int) -> dict:
    """Return one year's committed PJM bench part."""
    return json.load(gzip.open(BENCH.format(year=year)))["bench"]


def coal_plants(bench: dict) -> dict[str, dict]:
    """Coal-group plant records of one bench part, keyed by plant id."""
    return {
        pid: rec
        for pid, rec in bench["plants"].items()
        if rec["group"] in COAL_CLASSES
    }


def plant_hourly(rec: dict) -> np.ndarray:
    """Decode a bench plant's CAMPD hourly MW (uint8 % of nameplate)."""
    cf = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
    return cf / 100.0 * float(rec["npl"])


def hour_months(year: int) -> np.ndarray:
    """Month index (1-12) for each of the year's 8760 model hours."""
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return idx.month.to_numpy()


def section_1_three_bases() -> pd.DataFrame:
    """The three independent coal measures the bench already carries."""
    rows = []
    for y in YEARS:
        b = load_bench(y)
        e, cf = b["e930"], b["classFull"]
        col = float(e["coal"])
        cems = float(e["coal_cems"])
        g923 = sum(float(cf.get(c, 0.0)) for c in COAL_CLASSES)
        pl = coal_plants(b)
        npl = sum(float(r["npl"]) for r in pl.values())
        rows.append(
            {
                "year": y,
                "930_COL": col,
                "cems": cems,
                "eia923": g923,
                "col_minus_cems": col - cems,
                "col_minus_cems_pct": 100 * (col - cems) / col,
                "eia923_minus_cems": g923 - cems,
                "col_minus_923": col - g923,
                "n_plants": len(pl),
                "npl_mw": npl,
                "cems_cf": cems * TWH / (npl * 8760),
            }
        )
    return pd.DataFrame(rows).set_index("year")


def section_2_census_identity() -> pd.DataFrame:
    """Is the coal census literally the same plant set in every bench year?"""
    sets = {y: set(coal_plants(load_bench(y))) for y in YEARS}
    base = sets[2023]
    rows = []
    for y in YEARS:
        rows.append(
            {
                "year": y,
                "n": len(sets[y]),
                "vs_2023_added": len(sets[y] - base),
                "vs_2023_dropped": len(base - sets[y]),
            }
        )
    return pd.DataFrame(rows).set_index("year")


def section_3_monthly_gap() -> pd.DataFrame:
    """Monthly 930 COL vs bench CAMPD coal — concentrated or proportional?

    A missing-months/units EXTRACT defect concentrates the gap; a CENSUS
    (coverage) gap tracks the fleet's own monthly output.
    """
    out = {}
    for y in YEARS:
        b = load_bench(y)
        mon = hour_months(y)
        tot = np.zeros(8760)
        for rec in coal_plants(b).values():
            if rec.get("nodata"):
                continue
            tot += plant_hourly(rec)
        cems_m = pd.Series(tot).groupby(mon).sum() / TWH

        f = Path(f"data/raw/eia-930/PJM_fueltype_{y}.parquet")
        if not f.exists():
            f = Path("data/raw/PJM_fueltype.parquet")
        ft = pd.read_parquet(f)
        ft = ft[ft["fueltype"] == "COL"].copy()
        # 930 timestamps are UTC; the model clock is PJM local (EPT = UTC-5).
        ts = pd.to_datetime(ft["period"], utc=True).dt.tz_convert("Etc/GMT+5")
        ft = ft[ts.dt.year == y]
        col_m = ft.groupby(ts[ts.dt.year == y].dt.month)["value_mwh"].sum() / TWH
        out[y] = pd.DataFrame(
            {"930_COL": col_m, "cems": cems_m, "gap": col_m - cems_m}
        ).assign(gap_pct=lambda d: 100 * d["gap"] / d["930_COL"])
    return out


#: EIA-860 ``Energy Source 1`` codes for the coal family.
COAL_ES = {"BIT", "SUB", "LIG", "RC", "WC", "ANT", "SGC"}
#: PJM-footprint states (the same list pjm-157 §3 used for delivered fuel).
PJM_STATES = {"OH", "PA", "NJ", "MD", "DE", "VA", "WV", "IL", "IN", "KY", "MI", "NC", "DC"}


def section_4_retired_capacity() -> pd.DataFrame:
    """EIA-860 PJM-footprint coal capacity retiring in each year.

    Hypothesis (b): coal that ran in 2022 and retired before 2023 sits inside
    930 ``COL`` and EIA-923 for 2022 but is absent from the CAMPD census in
    EVERY bench year (the census is a single 42-plant set for 2022 AND 2023),
    so its 2022 output lands entirely in the gap.
    """
    d = pd.read_parquet("data/raw/eia-860/eia860_generator_retired_and_canceled.parquet")
    d = d[
        d["Energy Source 1"].astype(str).str.upper().isin(COAL_ES)
        & d["State"].astype(str).str.upper().isin(PJM_STATES)
    ].copy()
    d["Retirement Year"] = pd.to_numeric(d["Retirement Year"], errors="coerce")
    d["Nameplate Capacity (MW)"] = pd.to_numeric(
        d["Nameplate Capacity (MW)"], errors="coerce"
    )
    g = (
        d[d["Retirement Year"].between(2019, 2025)]
        .groupby("Retirement Year")
        .agg(units=("Generator ID", "size"), mw=("Nameplate Capacity (MW)", "sum"))
    )
    return g


def section_5_model_vs_bases() -> pd.DataFrame:
    """The model's own coal against each of the three measured bases.

    Reads the COMMITTED P1 class hourlies only (no solve): 2023-2025 from the
    pjm-152 keeper bundle, 2022 from the registered touchpoint.
    """
    bundles = {
        2022: "results/calibration/pjm2022_touchpoint",
        2023: "results/calibration/pjm152_collapse_A",
        2024: "results/calibration/pjm152_collapse_A",
        2025: "results/calibration/pjm152_collapse_A",
    }
    rows = []
    for y, bundle in bundles.items():
        ch = pd.read_parquet(f"{bundle}/hourly/class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(COAL_CLASSES))]
        model = ch["mw"].sum() / TWH
        b = load_bench(y)
        e, cf = b["e930"], b["classFull"]
        col, cems = float(e["coal"]), float(e["coal_cems"])
        g923 = sum(float(cf.get(c, 0.0)) for c in COAL_CLASSES)
        rows.append(
            {
                "year": y,
                "model": model,
                "vs_930COL": model - col,
                "vs_eia923": model - g923,
                "vs_cems_census": model - cems,
            }
        )
    return pd.DataFrame(rows).set_index("year")


def main() -> None:
    pd.set_option("display.width", 170)
    print("=" * 78)
    print("pjm-158 Phase-0 question C — the bench coal-coverage basis")
    print("=" * 78)

    print("\n--- §1  three independent coal measures (TWh) ---")
    t1 = section_1_three_bases()
    print(t1.round(3).to_string())

    print("\n--- §2  is the coal census the same plant set every year? ---")
    print(section_2_census_identity().to_string())

    print("\n--- §3  monthly 930 COL vs bench CAMPD coal ---")
    for y, df in section_3_monthly_gap().items():
        print(f"\n  {y}:")
        print(df.round(3).to_string())
        print(
            f"   annual: 930={df['930_COL'].sum():.2f}  cems={df['cems'].sum():.2f}  "
            f"gap={df['gap'].sum():.2f} ({100*df['gap'].sum()/df['930_COL'].sum():.1f}%)"
            f"  gap/month sd={df['gap'].std():.3f}  gap_pct sd={df['gap_pct'].std():.2f}pp"
        )

    print("\n--- §4  EIA-860 PJM-footprint coal retirements by year (nameplate MW) ---")
    print(section_4_retired_capacity().to_string())

    print("\n--- §5  the model's own coal against each measured basis (TWh) ---")
    print(section_5_model_vs_bases().round(3).to_string())


if __name__ == "__main__":
    main()
