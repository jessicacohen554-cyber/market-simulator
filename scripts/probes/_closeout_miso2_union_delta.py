"""closeout-miso-2 zero-LP probe: MISO bench EIA-923 class delta under the vintage union.

Diffs ``run_calibration_full._eia923_frame`` with
``benchmark_membership_vintage_union`` off vs on, per class and per added
plant, 2019-2025. Writes ``docs/records/miso/closeout-miso-2/union_delta*.csv``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

import run_calibration_full as rcf  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

OUT = REPO / "docs/records/miso/closeout-miso-2"


def main() -> None:
    gen = load_monthly_generation()
    cls_rows, plant_rows = [], []
    for y in range(2019, 2026):
        a = rcf._eia923_frame(y, gen, "MISO", benchmark_membership_vintage_union=False)
        b = rcf._eia923_frame(y, gen, "MISO", benchmark_membership_vintage_union=True)
        added = b[~b["plant_id"].isin(set(a["plant_id"]))]
        for k, v in added.groupby("klass")["annual_mwh"].sum().items():
            cls_rows.append({"year": y, "klass": k, "delta_twh": v / 1e6})
        for (pid, k), v in (
            added.groupby(["plant_id", "klass"])["annual_mwh"].sum().items()
        ):
            plant_rows.append({"year": y, "plant_id": pid, "klass": k, "twh": v / 1e6})
    c = pd.DataFrame(cls_rows)
    p = pd.DataFrame(plant_rows)
    c.to_csv(OUT / "union_delta_class.csv", index=False)
    p.to_csv(OUT / "union_delta_plant.csv", index=False)
    print(
        c.pivot_table(index="klass", columns="year", values="delta_twh", aggfunc="sum")
        .round(3)
        .fillna(0)
        .to_string()
    )
    print(
        p[p.twh.abs() > 0.2]
        .sort_values(["year", "twh"], ascending=[True, False])
        .round(3)
        .to_string()
    )


if __name__ == "__main__":
    main()
