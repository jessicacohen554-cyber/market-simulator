"""SPP-61 G2 footprint set (rule 29 screen gate G2): which plants the vintage arm moves, and whether each is
explained by the year's own EIA-860 release differing from the canonical snapshot."""

from __future__ import annotations
import sys
import json
from collections import defaultdict
from pathlib import Path

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
import pandas as pd
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import set_eia860_vintage
from market_sim.data.fleet import load_fleet_from_csv

cfg = get_iso_config("SPP")
out = {}
for year in (2023, 2024):

    def snap(v):
        set_eia860_vintage(v)
        try:
            gens = load_fleet_from_csv("SPP", cfg, year=year)
        finally:
            set_eia860_vintage(None)
        by = defaultdict(float)
        for g in gens:
            by[(int(g.plant_code or 0), g.plant_group)] += float(g.pmax_mw)
        return by

    c, a = snap(None), snap(year)
    moved = sorted(
        {k[0] for k in set(c) | set(a) if abs(a.get(k, 0.0) - c.get(k, 0.0)) > 0.05}
    )
    # Does each moved plant's row set differ between the two EIA-860 releases?
    canon = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    vint = pd.read_parquet(
        REPO / f"data/raw/eia-860/vintage_{year}/eia860_generator_operable.parquet"
    )
    KEY = [
        "Plant Code",
        "Generator ID",
        "Energy Source 1",
        "Prime Mover",
        "Summer Capacity (MW)",
        "Status",
    ]

    def rows(df, pid):
        s = df[df["Plant Code"] == pid][[k for k in KEY if k in df.columns]]
        return sorted(tuple(str(x) for x in r) for r in s.itertuples(index=False))

    unexplained = [p for p in moved if rows(canon, p) == rows(vint, p)]
    out[year] = {
        "n_moved_plants": len(moved),
        "moved_plants": moved,
        "n_unexplained": len(unexplained),
        "unexplained_plants": unexplained,
    }
    print(
        f"{year}: {len(moved)} plants move; {len(unexplained)} NOT explained by a "
        f"canonical-vs-vintage_{year} row difference -> {unexplained}"
    )
(REPO / "results/calibration/_spp61_g2_footprint.json").write_text(
    json.dumps(out, indent=2)
)
print("wrote results/calibration/_spp61_g2_footprint.json")
