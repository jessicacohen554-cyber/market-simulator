"""closeout-SOCO-w3p: carry the parasitic back-fill's effect onto the committed SOCO tranche artifact.

``thermal_tranches_SOCO.csv`` does not reproduce end to end at HEAD (pre-existing fleet / attribution drift since it
was cut; the control re-derive at HEAD differs from the committed bytes with the parasitic map untouched). Its
deriver reads the pooled parasitic map as a pure scale on each plant's CAMPD gross
(``campd.plant_group_hourly_net``: ``gross * factors.get(code, 1.0)``). So the back-fill's effect is isolated as
the ratio of two HEAD re-derives with the identical invocation (2024 base + soco-70 coal-unit coverage
2019-2025): ``arm`` (map with SOCO's measured_running rows) over ``control`` (map as committed). It is applied
to the committed rows: share / CF columns ``committed x arm / control`` (rounded to the artifact's one decimal),
``online_hours`` by the integer difference. Rows whose plant has no running factor are untouched.

Run (after both re-derives exist):
    uv run python scripts/probes/_closeout_socow3p_tranche_transplant.py --control DIR --arm DIR
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ART = REPO / "data/raw/_processed-legacy/thermal_tranches_SOCO.csv"
KEY = ["plant_code", "plant_group"]
RATIO_COLS = (
    "committed_pct",
    "mustrun_pct",
    "mustrun_online_pct",
    "p25_cf",
    "median_cf",
    "peaking_pct",
    "chp_pmin_cf",
    "steam_level_cf",
)


def main() -> None:
    """Apply the arm/control ratio to the committed artifact and refresh its sidecar hash."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    a = ap.parse_args()
    com = pd.read_csv(ART)
    c = pd.read_csv(a.control / ART.name).set_index(KEY)
    r = pd.read_csv(a.arm / ART.name).set_index(KEY)
    out = com.copy()
    moved = []
    for i, row in com.iterrows():
        k = (row.plant_code, row.plant_group)
        if k not in c.index or k not in r.index:
            continue
        for col in RATIO_COLS:
            cv, av = c.at[k, col], r.at[k, col]
            if pd.isna(cv) or pd.isna(av) or cv == 0 or cv == av or pd.isna(row[col]):
                continue
            out.at[i, col] = round(float(row[col]) * float(av) / float(cv), 1)
            moved.append((k, col, row[col], out.at[i, col]))
        dh = int(r.at[k, "online_hours"]) - int(c.at[k, "online_hours"])
        if dh:
            out.at[i, "online_hours"] = int(row.online_hours) + dh
            moved.append((k, "online_hours", row.online_hours, out.at[i, "online_hours"]))
    out.to_csv(ART, index=False)
    side = ART.with_suffix(".meta.json")
    meta = json.loads(side.read_text())
    meta["artifact_sha256"] = hashlib.sha256(ART.read_bytes()).hexdigest()
    meta["parasitic_running_transplant"] = (
        "closeout-SOCO-w3p: share/CF columns scaled by the arm/control ratio of two HEAD re-derives "
        "(SOCO measured_running parasitic rows added); see scripts/probes/_closeout_socow3p_tranche_transplant.py"
    )
    side.write_text(json.dumps(meta, indent=2) + "\n")
    for k, col, old, new in moved:
        print(f"{k[0]:>6} {k[1]:<11} {col:<20} {old} -> {new}")
    print(f"{len(moved)} cells moved; rows {len(com)}; {np.int64(len(set(m[0] for m in moved)))} plant rows")


if __name__ == "__main__":
    main()
