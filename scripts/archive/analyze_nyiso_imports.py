"""Ad-hoc validation for the NYISO import-discipline work (Step 4).

For a backcast bundle, reports:
  - LMP level/MAE: model NYCA hub (demand-weighted across the 5 internal
    zones) monthly mean vs measured actual_lmp.json rt_mon.
  - Import tranche dispatch: per-tranche dispatched-hour share and the
    "marginal" share (0 < mw < pmax, i.e. the tranche sets price), with
    import_scarcity broken out.
  - Net interchange TWh (import positive) vs the priced node total.

Usage:
    uv run python scripts/archive/analyze_nyiso_imports.py <bundle_dir> [<bundle_dir> ...]
"""

import json
import sys
from pathlib import Path

import pandas as pd

from market_sim.config.interchange_config import (
    IMPORT_TRANCHES,
    IMPORT_TRANCHES_BY_YEAR,
)

ACTUAL = json.load(open("data/raw/_validation-source/actual_lmp.json"))["NYISO"]

INTERNAL_ZONES = [
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
]


def _last_pass_dispatch(bundle: Path, year: int) -> Path | None:
    cands = sorted(bundle.glob(f"dispatch/{year}_P*.parquet"))
    return cands[-1] if cands else None


def _tranche_caps(year: int) -> dict[str, float]:
    tr = IMPORT_TRANCHES_BY_YEAR.get("NYISO", {}).get(year)
    if tr is None:
        tr = IMPORT_TRANCHES.get("NYISO", [])
    return {name: cap for name, cap, _ in tr}


def analyze(bundle: Path) -> None:
    sysdf = pd.read_parquet(bundle / "system.parquet")
    years = sorted(sysdf["year"].unique())
    print(f"\n===== {bundle.name} =====")
    for year in years:
        sy = sysdf[sysdf["year"] == year]
        last_pass = sy["pass"].iloc[-1]
        sy = sy[sy["pass"] == last_pass]
        intern = sy[sy["zone"].isin(INTERNAL_ZONES)].copy()
        # demand-weighted hub price per hour, then monthly mean
        hub = (
            intern.groupby("hour").apply(
                lambda g: (g["price"] * g["demand"]).sum() / g["demand"].sum()
            )
        ).to_frame("price")
        hub["month"] = (hub.index.to_numpy() // 730).clip(max=11)
        model_mon = hub.groupby("month")["price"].mean().values
        actual = ACTUAL.get(str(year))
        if actual is None:
            continue
        act_mon = actual["rt_mon"]
        n = min(len(model_mon), len(act_mon))
        mae = sum(abs(model_mon[i] - act_mon[i]) for i in range(n)) / n
        model_mean = float(
            intern.groupby("hour")
            .apply(lambda g: (g["price"] * g["demand"]).sum() / g["demand"].sum())
            .mean()
        )
        print(f"\n  --- {year} (pass {last_pass}) ---")
        print(
            f"  LMP hub: model {model_mean:5.1f} / actual {actual['rt']:5.1f}"
            f"   monthly MAE {mae:5.2f}"
        )

        dpath = _last_pass_dispatch(bundle, year)
        if dpath is None:
            print("  (no dispatch parquet)")
            continue
        dd = pd.read_parquet(dpath)
        imp = dd[dd["fuel"] == "import"].copy()
        imp["name"] = imp["unit_id"].str.replace("NYISO_external_", "", regex=False)
        caps = _tranche_caps(year)
        n_hours = imp["hour"].nunique()
        print(f"  import tranches (n_hours={n_hours}):")
        for name in [
            "HQ_hydro",
            "IESO_Ontario",
            "PJM_west",
            "ISONE_tie",
            "import_scarcity",
        ]:
            g = imp[imp["name"] == name]
            if g.empty:
                continue
            cap = caps.get(name, float("nan"))
            disp = (g["mw"] > 1e-3).sum()
            marg = ((g["mw"] > 1e-3) & (g["mw"] < cap - 1e-3)).sum()
            twh = g["mw"].sum() / 1e6
            print(
                f"    {name:16s} cap {cap:6.0f}  disp {disp / n_hours * 100:5.1f}%"
                f"  marginal {marg / n_hours * 100:5.1f}%  {twh:5.2f} TWh"
            )
        # net import (all import minus export sinks)
        net_twh = imp[~imp["name"].str.startswith("export")]["mw"].sum() / 1e6
        exp_twh = imp[imp["name"].str.startswith("export")]["mw"].sum() / 1e6
        print(f"  net import {net_twh:.2f} TWh (export sinks {exp_twh:.2f} TWh)")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        analyze(Path(arg))
