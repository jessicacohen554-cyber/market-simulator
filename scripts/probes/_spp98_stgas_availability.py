"""SPP-98 phase 0 (zero LP): does the keeper's ST_GAS availability block hours SPP actually ran?

Rebuilds the keeper fleet per year with run_year(fleet_only=True) (no LP), sums ST_GAS pmax x
availability per plant-hour, and compares with the SPP bench's CAMPD hourly CF per plant. Reports
CAMPD ST_GAS energy in hours where the model's available MW is below CAMPD's actual MW
(availability-BLOCKED energy), and the share blocked with model availability == 0.

Usage: uv run python scripts/probes/_spp98_stgas_availability.py <year> [<year> ...]
Writes docs/records/spp/spp98/stgas_avail_<year>.json
"""

import base64
import gzip
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO), str(REPO / "src")]
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

B = REPO / "results/calibration/spp94_arm_span"
CLS = "ST_GAS"


def main():
    """Measure availability-blocked CAMPD ST_GAS energy for each requested year."""
    meta = json.loads((B / "meta.json").read_text())
    out_dir = REPO / "docs/records/spp/spp98"
    out_dir.mkdir(parents=True, exist_ok=True)
    for y in map(int, sys.argv[1:]):
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(B, y))
        fa = run_year(
            y, "SPP", 8760, float(meta["gas_prices"][str(y)]), {}, fleet_only=True, **kw
        )["fleet_arrays"]
        grp = np.asarray(fa.plant_group)
        pc = np.asarray(fa.plant_code)
        sel = grp == CLS
        avail_mw = (
            pd.DataFrame((fa.pmax[:, None] * fa.availability)[sel])
            .groupby(pc[sel])
            .sum()
        )
        bench = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz")
        )["bench"]["plants"]
        rows = []
        for k, v in bench.items():
            if v["group"] != CLS or v.get("nodata") or not v.get("campd"):
                continue
            code = int(k.split(":")[0])
            if code not in avail_mw.index:
                continue
            c_mw = (
                np.frombuffer(base64.b64decode(v["campd"]), dtype=np.uint8).astype(
                    float
                )
                / 100
                * v["npl"]
            )
            a = avail_mw.loc[code].values[: len(c_mw)]
            blocked = np.clip(c_mw - a, 0, None)
            rows.append(
                {
                    "plant": code,
                    "name": v["name"],
                    "npl": v["npl"],
                    "campd_twh": c_mw.sum() / 1e6,
                    "blocked_twh": blocked.sum() / 1e6,
                    "blocked_at_zero_twh": c_mw[a <= 0.5].sum() / 1e6,
                    "avail_mean": float(a.mean() / v["npl"]),
                    "campd_online_h": int((c_mw > 0).sum()),
                    "online_but_zero_avail_h": int(((c_mw > 0) & (a <= 0.5)).sum()),
                }
            )
        df = pd.DataFrame(rows).sort_values("blocked_twh", ascending=False)
        tot = {
            k: round(float(df[k].sum()), 3)
            for k in ("campd_twh", "blocked_twh", "blocked_at_zero_twh")
        }
        tot["plants"] = len(df)
        print(y, tot)
        print(df.head(8).round(3).to_string())
        (out_dir / f"stgas_avail_{y}.json").write_text(
            json.dumps(
                {"totals": tot, "plants": df.round(4).to_dict("records")}, indent=1
            )
        )


if __name__ == "__main__":
    main()
