#!/usr/bin/env python3
"""closeout-MISO-w3e (ZERO LP): the MISO CHP / EIA-930 bench reconciliation.

Three measured tables behind FINDING-closeout-miso-w3e-bench-reconciliation:

1. PLANT: the five largest measured-vs-default CHP movers (Midland 10745, Taft
   55089, Sabine River 10789, Dearborn 55088, Carville 55404) -- EIA-860 BA and
   interconnecting TO, EIA-923 page-1 net, Schedules 6/7 net and grid
   (resale + tolling + outgoing), CAMPD CEMS net, and the grid energy the
   sector-default chp_btm_pct allows.
2. SOCO-60 FOLD TEST (benchmark_semantics.EIA930_GAS_FOLD_REFUTED): MISO EIA-930
   gas minus the EIA-923 gas generation of MISO-BA plants FULL (CHP host incl.),
   against the fold F = OTHER + biomass - 930 Other the deflation subtracts.
3. SYSTEM (optional, needs locally re-rendered bench parts): the fossil
   (gas+coal family) classFull per year on the default-share basis (committed
   parts), the measured-share basis and the reconciled basis (measured shares,
   MISO fold refuted), against raw EIA-930 gas+coal. Pass the two scratch
   bench-part directories as --measured-dir / --reconciled-dir; the parts are
   produced by registering a span bundle at the lane head (measured) and with
   EIA930_GAS_FOLD_REFUTED including MISO (reconciled).

Output: results/phase0/miso/_closeout_miso_w3e_bench_reconciliation.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO), str(REPO / "scripts")]

from market_sim.data.chp import chp_btm_pct  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402

OUT = REPO / "results/phase0/miso/_closeout_miso_w3e_bench_reconciliation.json"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
PLANTS = {
    10745: "Midland Cogen",
    55089: "Taft",
    10789: "Sabine River Works",
    55088: "Dearborn Industrial",
    55404: "Carville",
}
GROUP = {
    10745: "CC_CHP",
    55089: "CC_CHP",
    10789: "CC_CHP",
    55088: "CT_CHP",
    55404: "CC_CHP",
}
GAS_FUELS = {"NG", "OG", "BFG", "PG", "SGC"}
YEARS = range(2019, 2026)


def _bench(d: Path, y: int) -> dict:
    return json.load(gzip.open(d / f"{y}.json.gz"))["bench"]


def plant_table() -> list[dict]:
    """Per-plant meters for the five movers, 2019 / 2021 / 2023."""
    import scripts.run_calibration_full as rcf

    p860 = pd.read_parquet(REPO / "data/raw/eia-860/eia860_plant.parquet").set_index(
        "Plant Code"
    )
    disp = pd.read_csv(
        REPO / "data/raw/eia-923-disposition/eia923_disposition_2019_2025.csv"
    )
    g923 = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    )
    pf = rcf._parasitic_factor_map()
    rows = []
    for y in (2019, 2021, 2023):
        campd = (
            rcf._campd_hourly_frame(y, "MISO", pf, 8760)
            .groupby("plant_id")["net_mw"]
            .sum()
        )
        for pid, name in PLANTS.items():
            r = disp[(disp.plant_id == pid) & (disp.year == y)].iloc[0]
            net923 = float(
                g923[(g923.plant_id == pid) & (g923.year == y)].netgen_annual_mwh.sum()
            )
            dflt = chp_btm_pct(pid, GROUP[pid], iso="MISO") / 100.0
            rows.append(
                {
                    "year": y,
                    "plant": pid,
                    "name": name,
                    "ba": str(p860.loc[pid, "Balancing Authority Code"]),
                    "to": str(
                        p860.loc[pid, "Transmission or Distribution System Owner"]
                    ),
                    "eia923_net_gwh": round(net923 / 1e3, 1),
                    "sched67_net_gwh": round(
                        (r.gross_mwh - r.station_use_mwh) / 1e3, 1
                    ),
                    "sched67_grid_gwh": round(
                        (r.sales_for_resale_mwh + r.tolling_mwh + r.outgoing_mwh) / 1e3,
                        1,
                    ),
                    "campd_net_gwh": round(
                        float(campd.get(pid, float("nan"))) / 1e3, 1
                    ),
                    "default_grid_gwh": round(net923 * (1.0 - dflt) / 1e3, 1),
                    "default_share": dflt,
                }
            )
    return rows


def fold_test() -> list[dict]:
    """SOCO-60's test: 930 gas vs 923 gas FULL of MISO-BA plants, against F."""
    g923 = pd.read_parquet(
        REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
    )
    m = g923[(g923.ba_code == "MISO") & g923.fuel_type.isin(GAS_FUELS)]
    out = []
    for y in YEARS:
        b = _bench(BENCH, y)
        e, cf = b["e930"], b["classFull"]
        full = float(m[m.year == y].netgen_annual_mwh.sum()) / 1e6
        fold = bs.geo_biomass_outside_930_other(cf, e)
        out.append(
            {
                "year": y,
                "e930_gas": e["gas"],
                "eia923_gas_full": round(full, 2),
                "gap_930_minus_923": round(e["gas"] - full, 2),
                "fold_F": round(fold, 2),
            }
        )
    return out


def system_table(measured: Path | None, reconciled: Path | None) -> list[dict]:
    """Fossil family classFull per basis vs raw EIA-930 gas+coal."""
    fam = [*bs.GAS_GROUPS, *bs.COAL_GROUPS]
    out = []
    for y in YEARS:
        a = _bench(BENCH, y)
        row = {
            "year": y,
            "e930_gas_coal": round(a["e930"]["gas"] + a["e930"]["coal"], 1),
            "default": round(sum(a["classFull"].get(k, 0.0) for k in fam), 1),
        }
        for key, d in (("measured", measured), ("reconciled", reconciled)):
            if d is not None and (d / f"{y}.json.gz").exists():
                row[key] = round(
                    sum(_bench(d, y)["classFull"].get(k, 0.0) for k in fam), 1
                )
        out.append(row)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--measured-dir", type=Path)
    ap.add_argument("--reconciled-dir", type=Path)
    a = ap.parse_args()
    res = {
        "plant": plant_table(),
        "fold_test": fold_test(),
        "system": system_table(a.measured_dir, a.reconciled_dir),
    }
    OUT.write_text(json.dumps(res, indent=1, default=float))
    for k in ("fold_test", "system"):
        for r in res[k]:
            print(k, r)


if __name__ == "__main__":
    main()
