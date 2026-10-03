"""closeout-PJM-cc22 phase 0 (zero LP): the system energy ledger by year, model vs EIA-930 vs the C1 bench.

Keeper ``2026-10-03-closeout-pjm-nuc-keeper``. Per year: model generation by family (payload
``gmModel``), model demand (``hourly/system_<y>.parquet``), model net import (``class_hourly`` klass
``import``); the C1 bench ``classFull``; EIA-930 PJM BA demand / net generation by fuel / interchange
(Adjusted). Answers whether 2022's CC over-run sits in a system energy surplus, and whether the
2022 bench (EIA-923) under-reads gas against EIA-930. Writes
``results/phase0/pjm/_closeoutpjm_cc22_ledger.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RUN = REPO / "frontend/data/backcast/runs/2026-10-03-closeout-pjm-nuc-keeper.js"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
HOURLY = REPO / "results/calibration/closeout_pjm_nuc_full_span/hourly"
E930 = REPO / "data/raw/eia-930"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_cc22_ledger.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
COAL = ("COAL_BIT", "COAL_PRB", "COAL_WC", "COAL_LIGNITE")
A = " (MW) (Adjusted)"


def _payload() -> dict:
    """Decode the keeper's registered run payload."""
    m = re.search(r'runGz\["[^"]+"\]="([^"]+)"', RUN.read_text())
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def _e930(year: int) -> dict:
    """Annual PJM BA totals (TWh) from EIA-930 BALANCE, Adjusted columns."""
    d = pd.concat(
        pd.read_parquet(f)
        for f in sorted(E930.glob(f"EIA930_BALANCE_{year}_*.parquet"))
    )
    d = d[d["Balancing Authority"] == "PJM"]
    col = {
        "demand": "Demand" + A,
        "ng": "Net Generation" + A,
        "ti_export": "Total Interchange" + A,
        "gas": "Net Generation (MW) from Natural Gas (Adjusted)",
        "coal": "Net Generation (MW) from Coal (Adjusted)",
        "nuclear": "Net Generation (MW) from Nuclear (Adjusted)",
        "other": "Net Generation (MW) from Other Fuel Sources (Adjusted)",
        "unknown": "Net Generation (MW) from Unknown Fuel Sources (Adjusted)",
    }
    return {
        k: float(pd.to_numeric(d[c], errors="coerce").sum() / 1e6)
        for k, c in col.items()
    }


def main() -> None:
    """Build the ledger and print it."""
    pay = _payload()["years"]
    res = {}
    for y in YEARS:
        gm = pay[str(y)]["gmModel"]
        cf = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["classFull"]
        sysd = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        ch = pd.read_parquet(HOURLY / f"class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        imp = float(ch.loc[ch.klass == "import", "mw"].sum() / 1e6)
        e = _e930(y)
        r = {
            "model_demand": float(
                sysd.loc[~sysd.zone.str.contains("external"), "demand"].sum() / 1e6
            ),
            "model_net_import": imp,
            "model_gas": sum(gm.get(k, 0) for k in GAS),
            "model_coal": sum(gm.get(k, 0) for k in COAL),
            "bench_gas": sum(cf.get(k, 0) for k in GAS),
            "bench_coal": sum(cf.get(k, 0) for k in COAL),
            "model_gen": sum(v for k, v in gm.items() if k in cf),
            "bench_gen": sum(cf[k] for k in cf if k in gm),
            **{f"e930_{k}": v for k, v in e.items()},
        }
        r["d_gen"] = r["model_gen"] - r["bench_gen"]
        r["d_gas_model_bench"] = r["model_gas"] - r["bench_gas"]
        r["d_gas_930_bench"] = r["e930_gas"] - r["bench_gas"]
        r["d_coal_930_bench"] = r["e930_coal"] - r["bench_coal"]
        r["d_ng_930_bench"] = r["e930_ng"] - r["bench_gen"]
        r["d_demand_model_930"] = r["model_demand"] - r["e930_demand"]
        res[y] = {k: round(v, 2) for k, v in r.items()}
    OUT.write_text(json.dumps(res, indent=1))
    keys = list(res[2019])
    print("key".ljust(22) + "".join(f"{y:>9}" for y in YEARS))
    for k in keys:
        print(k.ljust(22) + "".join(f"{res[y][k]:9.2f}" for y in YEARS))


if __name__ == "__main__":
    main()
