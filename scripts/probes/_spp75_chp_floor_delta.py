"""SPP-75 part C: size the existing CHP steam-floor level swap (chp_steam_floor_p25), zero LP.

``data/fleet/assembly.py`` sets the grid floor to ``pmin_cf x (1 - btm) x nameplate`` and, when
``chp_steam_floor_p25`` is armed, swaps ``pmin_cf`` for the artifact's ``steam_level_cf``
wherever that is higher (a level-source swap on MECH_CHP_STEAM, rule 19). The fleet_only dump
(``_spp75_fleet_membership.py``) carries each CHP row's post-BTM ``pmax``, so the floor
before / after is ``pmax x chp_pmin_cf`` / ``pmax x max(chp_pmin_cf, steam_level_cf)`` — before
the availability clip. Checked against the rung's class_hourly CHP MW in RT<=0 hours.

Usage: ``uv run python scripts/probes/_spp75_chp_floor_delta.py --fleet-dir <dir> --out <json>``
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

CHP = ("CC_CHP", "CT_CHP", "ST_CHP")


def main() -> None:
    """Per-year CHP floor before / after the level swap, by class and plant."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--fleet-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    art = pd.read_csv(RAW_DATA_DIR / "_processed-legacy/thermal_tranches_SPP.csv")
    art = art[art["plant_group"].isin(CHP)].set_index(["plant_code", "plant_group"])
    out = {}
    for y in (2019, 2020, 2021, 2022):
        fl = pd.DataFrame(
            json.loads((Path(a.fleet_dir) / f"fleet_{y}.json").read_text())
        )
        fl = fl[fl["klass"].isin(CHP)]
        pm = fl.groupby(["plant", "klass"])["pmax"].sum()
        rows = []
        for (pc, k), p in pm.items():
            r = art.loc[(pc, k)] if (pc, k) in art.index else None
            lo = float(r["chp_pmin_cf"]) / 100 if r is not None else 0.0
            lvl = float(r["steam_level_cf"]) / 100 if r is not None else 0.0
            rows.append(
                {
                    "plant": int(pc),
                    "klass": k,
                    "pmax": float(p),
                    "name": str(r["name"]) if r is not None else "?",
                    "floor_ctl": p * lo,
                    "floor_arm": p * max(lo, lvl),
                }
            )
        df = pd.DataFrame(rows)
        out[y] = {
            "by_class": df.groupby("klass")[["pmax", "floor_ctl", "floor_arm"]]
            .sum()
            .round(1)
            .to_dict("index"),
            "total_ctl": float(df["floor_ctl"].sum()),
            "total_arm": float(df["floor_arm"].sum()),
            "plants": df.round(1).to_dict("records"),
        }
        print(y, {k: v for k, v in out[y].items() if k != "plants"})
    Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
