"""closeout-miso-2 zero-LP probe: per plant-month model nuclear vs EIA-923, 2019-2022.

Reads the MISO keeper's committed ``unit_marginal_<Y>.parquet`` (P1) and the
EIA-923 monthly net generation (``market_sim.data.eia923``) for every nuclear
plant that either the model fleet carries or EIA-923 attributes to the MISO
nuclear set (incl. Duane Arnold 1060 and Palisades 1715). Writes
``docs/records/miso/closeout-miso-2/nuc_plant_month.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

BUNDLE = REPO / "results/calibration/w0_miso_span/hourly"
OUT = REPO / "docs/records/miso/closeout-miso-2"
EXTRA = {1060: "Duane Arnold", 1715: "Palisades"}
YEARS = range(2019, 2026)


def model_plant_month(year: int) -> pd.DataFrame:
    """Return P1 model nuclear MWh by (plant_code, month) for one year."""
    u = pd.read_parquet(
        BUNDLE / f"unit_marginal_{year}.parquet",
        columns=["pass", "plant_code", "fuel", "hour", "mw", "cap_mw"],
        filters=[("fuel", "==", "nuclear")],
    )
    u = u[u["pass"] == "P1"]
    ts = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(u["hour"], unit="h")
    u = u.assign(month=ts.dt.month)
    return (
        u.groupby(["plant_code", "month"])
        .agg(model_mwh=("mw", "sum"), cap_mwh=("cap_mw", "sum"))
        .reset_index()
    )


def main() -> None:
    gen = load_monthly_generation()
    mcols = [
        c for c in gen.columns if c.startswith("netgen_") and c != "netgen_annual_mwh"
    ]
    gen = gen[gen["fuel_type"].str.upper().isin(["NUC"])]
    rows = []
    for y in YEARS:
        m = model_plant_month(y)
        codes = sorted(set(m["plant_code"].astype(int)) | set(EXTRA))
        g = gen[(gen["year"] == y) & (gen["plant_id"].isin(codes))]
        g = g.groupby("plant_id")[mcols].sum()
        for pc in codes:
            for mo in range(1, 13):
                mm = m[(m.plant_code == pc) & (m.month == mo)]
                rows.append(
                    {
                        "year": y,
                        "plant_code": pc,
                        "month": mo,
                        "model_mwh": float(mm.model_mwh.sum()),
                        "cap_mwh": float(mm.cap_mwh.sum()),
                        "eia923_mwh": float(g.loc[pc, mcols[mo - 1]])
                        if pc in g.index
                        else 0.0,
                    }
                )
    df = pd.DataFrame(rows)
    df["gap_mwh"] = df.model_mwh - df.eia923_mwh
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "nuc_plant_month.csv", index=False)
    py = (
        df.groupby(["year", "plant_code"])[["model_mwh", "eia923_mwh", "gap_mwh"]].sum()
        / 1e6
    )
    print(py.round(3).to_string())
    print(
        (df.groupby("year")[["model_mwh", "eia923_mwh", "gap_mwh"]].sum() / 1e6).round(
            3
        )
    )


if __name__ == "__main__":
    main()
