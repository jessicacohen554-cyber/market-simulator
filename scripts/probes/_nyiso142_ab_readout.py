"""nyiso-142 — score the pre-registered Astoria stack-duplication A/B.

Reads the two committed bundles and reports, per pre-registered prediction
(``PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md`` §3) and per kill
gate (§4), what actually moved. Constructs no LP and solves nothing.

Usage:
    PYTHONPATH=$PWD python scripts/probes/_nyiso142_ab_readout.py \\
        --control results/calibration/nyiso142_control \\
        --arm     results/calibration/nyiso142_stackdup
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)


def _class_energy(bundle: Path, year: int) -> pd.Series:
    d = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.groupby("klass")["mw"].sum() / 1.0e6


def _system(bundle: Path, year: int) -> pd.DataFrame:
    d = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return d[d["pass"] == "P1"] if "pass" in d.columns else d


def class_table(control: Path, arm: Path) -> pd.DataFrame:
    rows = []
    for year in YEARS:
        c, a = _class_energy(control, year), _class_energy(arm, year)
        for klass in sorted(set(c.index) | set(a.index)):
            cv, av = float(c.get(klass, 0.0)), float(a.get(klass, 0.0))
            rows.append(
                {
                    "year": year,
                    "klass": klass,
                    "control_twh": cv,
                    "arm_twh": av,
                    "delta_twh": av - cv,
                }
            )
    return pd.DataFrame(rows)


def price_table(control: Path, arm: Path) -> pd.DataFrame:
    """P6 (mean LMP) and the K2 feasibility gate, per year and arm."""
    rows = []
    for year in YEARS:
        for name, bundle in (("control", control), ("arm", arm)):
            s = _system(bundle, year)
            rows.append(
                {
                    "year": year,
                    "run": name,
                    "mean_lmp": float(s["price"].mean()),
                    "slack_mwh": float(s["slack"].sum()),
                    "dump_mwh": float(s["dump"].sum()),
                }
            )
    df = pd.DataFrame(rows).pivot(index="year", columns="run")
    df[("mean_lmp", "delta")] = df[("mean_lmp", "arm")] - df[("mean_lmp", "control")]
    return df


def astoria_dispatch(control: Path, arm: Path) -> pd.DataFrame:
    """P3 at its source — what Astoria (8906) itself does across the arms."""
    rows = []
    for year in YEARS:
        for name, bundle in (("control", control), ("arm", arm)):
            path = bundle / "hourly" / f"unit_hourly_{year}.parquet"
            if not path.exists():
                continue
            d = pd.read_parquet(
                path, columns=["pass", "plant_code", "plant_group", "mw"]
            )
            d = d[d["pass"] == "P1"]
            hit = d[pd.to_numeric(d["plant_code"], errors="coerce") == 8906]
            rows.append(
                {
                    "year": year,
                    "run": name,
                    "astoria_twh": float(hit["mw"].sum()) / 1.0e6,
                    "groups": ",".join(sorted(set(hit["plant_group"].astype(str)))),
                }
            )
    return pd.DataFrame(rows)


def bench_stgas(iso: str = "NYISO") -> pd.DataFrame:
    """P1/P2 — the ST_GAS class benchmark the runs are scored against."""
    import gzip

    rows = []
    for year in YEARS:
        path = REPO / "frontend/data/backcast/bench" / iso / f"{year}.json.gz"
        if not path.exists():
            continue
        with gzip.open(path) as fh:
            bench = json.load(fh)["bench"]
        full = bench.get("classFull") or {}
        entry = full.get("ST_GAS")
        astoria = (bench.get("plants") or {}).get("8906") or {}
        rows.append(
            {
                "year": year,
                "classFull_ST_GAS": entry if not isinstance(entry, dict) else entry.get("actual"),
                "astoria_e_ann": astoria.get("e_ann"),
                "astoria_c_ann": astoria.get("c_ann"),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    args = ap.parse_args()

    print("nyiso-142 A/B readout — pre-registered predictions P1-P7, gates K1'-K6'")
    print("=" * 92)

    print("\n### Class energy, control vs arm (TWh) — P3")
    tbl = class_table(args.control, args.arm)
    moved = tbl[tbl["delta_twh"].abs() > 0.0005]
    print(
        moved.round(4).to_string(index=False)
        if len(moved)
        else "  no class moved by more than 0.5 GWh in any year"
    )
    print("\n  ST_GAS and CC_REGULAR in full:")
    print(
        tbl[tbl.klass.isin(["ST_GAS", "CC_REGULAR", "CC_CHP"])]
        .round(4)
        .to_string(index=False)
    )

    print("\n### System price + feasibility — P6, K2")
    print(price_table(args.control, args.arm).round(4).to_string())

    print("\n### Astoria's own dispatch — P3 at source")
    ast = astoria_dispatch(args.control, args.arm)
    print(ast.round(4).to_string(index=False) if len(ast) else "  no unit_hourly sidecar")

    print("\n### ST_GAS benchmark as committed — P1, P2")
    print(bench_stgas().to_string(index=False))


if __name__ == "__main__":
    main()
