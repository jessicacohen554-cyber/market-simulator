"""Quick class-level comparison of calibration bundles for tuning iteration.

Prints, for each bundle and year, the thermal-by-class model total (grid LP +
data-driven BTM add-back) vs the EIA-923 benchmark — the [3b] table of the
full report — side by side across runs, plus the headline plant panel for the
plants under active tuning. Pure parquet reads; no LP solve.

Usage: python scripts/archive/compare_runs_classes.py Run-72 Run-73 [...]
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.bundle_io import bundle_input_path  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
CLASSES = [
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "COAL_LIGNITE",
    "COAL_PRB",
]
PLANTS = {
    55015: "Sweeny Cogen",
    10298: "Bayou Cogen",
    58378: "Petra Nova",
    55464: "Deer Park",
    55327: "Baytown",
    3470: "W A Parish 5-8",
}


def class_table(run: str) -> pd.DataFrame:
    """Return model-vs-923 diff%% per (year, class) for one bundle."""
    d = ROOT / run
    e923 = pd.read_parquet(bundle_input_path(d, "eia923"))
    btm = pd.read_parquet(d / "btm.parquet")
    rows = []
    for f in sorted((d / "dispatch").glob("*_P1.parquet")):
        disp = pd.read_parquet(f, columns=["year", "klass", "mw"])
        year = int(disp["year"].iloc[0])
        grid = disp.groupby("klass")["mw"].sum() / 1e6  # TWh
        b = btm[(btm["year"] == year) & (btm["pass"] == "P1")]
        bt = dict(zip(b["klass"], b["btm_twh"]))
        bench = e923[e923["year"] == year].groupby("klass")["annual_mwh"].sum() / 1e6
        for cls in CLASSES:
            m = grid.get(cls, 0.0) + bt.get(cls, 0.0)
            a = bench.get(cls, 0.0)
            rows.append(
                {
                    "year": year,
                    "class": cls,
                    f"{run} TWh": round(m, 2),
                    "EIA-923": round(a, 2),
                    f"{run} %": round((m - a) / a * 100, 1) if a else None,
                }
            )
    return pd.DataFrame(rows)


def plant_table(run: str) -> pd.DataFrame:
    """Return model-vs-CAMPD GWh for the tuning plant panel."""
    fit = pd.read_parquet(ROOT / run / "plant_hourly_fit.parquet")
    fit = fit[fit["plant_code"].isin(PLANTS)].copy()
    fit["plant"] = fit["plant_code"].map(PLANTS)
    fit[f"{run} GWh"] = fit["model_gwh"].round(0)
    return fit[["year", "plant", f"{run} GWh", "campd_gwh"]]


def main(runs: list[str]) -> None:
    pd.set_option("display.width", 250)
    base = class_table(runs[0])
    for r in runs[1:]:
        t = class_table(r)
        base = base.merge(
            t.drop(columns=["EIA-923"]), on=["year", "class"], how="outer"
        )
    cols = ["year", "class", "EIA-923"] + [
        c for r in runs for c in (f"{r} TWh", f"{r} %")
    ]
    print(base[cols].to_string(index=False))
    print()
    pbase = plant_table(runs[0])
    for r in runs[1:]:
        pbase = pbase.merge(
            plant_table(r).drop(columns=["campd_gwh"]),
            on=["year", "plant"],
            how="outer",
        )
    print(pbase.sort_values(["plant", "year"]).to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1:] or ["Run-72"])
