"""closeout-SOCO-2 cross-ISO nuclear-table coverage: which keeper years read the forecast fallback, and the nuclear TWh gap vs EIA-923."""

import base64
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
from market_sim.config.constants import NUCLEAR_MONTHLY_CF_BY_YEAR

# Rows this lane added (absent when every keeper below was solved).
ADDED_THIS_LANE = {("SOCO", y) for y in (2019, 2020, 2021, 2022)}
OUT = Path("docs/records/soco/r-soco/closeout-soco-2/nuc_coverage.csv")
rows = []
for iso in ["CAISO", "ERCOT", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SOCO", "SPP"]:
    keeper = json.load(open(f"frontend/data/backcast/keepers/{iso}.json"))["keeper"]
    js = Path(f"frontend/data/backcast/runs/{keeper}.js").read_text()
    pay = json.loads(
        gzip.decompress(
            base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', js).group(1))
        )
    )
    reg = json.load(open(f"frontend/data/backcast/registry/{keeper}.json"))
    rc_path = None
    for k in ("bundle", "bundle_dir", "results_dir", "out_dir"):
        if isinstance(reg.get(k), str):
            rc_path = Path(reg[k]) / "run_config.json"
    flags = {}
    if rc_path and rc_path.exists():
        rc = json.load(open(rc_path))
        sc = rc.get("scenario_config", {})
        flags = {
            f: sc.get(f)
            for f in ("nuclear_unit_availability", "ercot_nuclear_unit_availability")
        }
    for y, yp in sorted(pay["years"].items()):
        y = int(y)
        bench = Path(f"frontend/data/backcast/bench/{iso}/{y}.json.gz")
        if not bench.exists():
            continue
        b = json.load(gzip.open(bench))["bench"]["classFull"].get("nuclear")
        m = yp.get("gmModel", {}).get("nuclear")
        rows.append(
            dict(
                iso=iso,
                year=y,
                keeper=keeper,
                table_row_at_keeper=(y in NUCLEAR_MONTHLY_CF_BY_YEAR.get(iso, {}))
                and (iso, y) not in ADDED_THIS_LANE,
                nrc_overlay=flags.get("nuclear_unit_availability")
                or flags.get("ercot_nuclear_unit_availability"),
                model_twh=m,
                eia923_twh=b,
                gap_twh=(m - b) if (m is not None and b is not None) else None,
            )
        )
import pandas as pd

d = pd.DataFrame(rows)
d.to_csv(OUT, index=False)
print(d.round(2).to_string())
