"""closeout-MISO-w3g phase 0 (ZERO LP): can MISO arm the CHP host-level swap?

The desk's "host online leg inside chp_steam_following" is the registered
MECH_CHP_STEAM level swap ``chp_steam_floor_p25`` scoped by
``chp_steam_floor_conduct_scope`` (SPP-100, SPP cell K). It reads
``steam_level_cf`` from the ISO's tranche artifact, which MISO's does not carry.
This probe records the three facts the lane's FINDING rests on:

1. **Reproduction census.** A HEAD derive of the MISO base artifact
   (``derive_thermal_tranches.py --iso MISO --years 2019..2025``, written to a
   scratch path given on the command line) against the committed CHP rows:
   which committed columns reproduce. The keeper reads the
   ``-fuelsplit-stcov-splitremap-`` companion, whose CHP rows are copied
   verbatim from that base (``write_unit_fuel_split_companions`` protects
   ``_CHP_GROUPS``), so the base is the CHP vintage.
2. **Static added forced energy** on the arm-B legs if the swap were armed with
   the HEAD level (scope applied: metered rows need pooled on-frequency
   ``steam_level_cf / median_cf`` > ``CHP_STEAM_ALLHOURS_MIN_ON_FRAC``), by
   class-year and by lens (``ok`` = CAMPD-metered, ``eia923_cf`` = CEMS-
   invisible). Floor MW = level x the plant-class's grid capacity in the leg's
   ``unit_marginal`` sidecar (clipped hourly to ``cap_mw``); added energy =
   sum over hours of max(0, floor - arm-B dispatch). An upper bound on what
   the floor adds before LP re-dispatch.
3. **Basis check** per metered plant: the floored energy against the plant's
   own whole-year CAMPD net (2023).

Output: ``results/phase0/miso/_closeout_miso_w3g_chp_host_level_phase0.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO / "src"), str(REPO), str(REPO / "scripts")]

ARTIFACT = REPO / "data/raw/_processed-legacy/thermal_tranches_MISO.csv"
OUT = REPO / "results/phase0/miso/_closeout_miso_w3g_chp_host_level_phase0.json"
LEG = str(
    REPO
    / "results/calibration/closeout_miso_w3f_b_{y}/hourly/unit_marginal_{y}.parquet"
)
KEY = ["plant_code", "plant_group"]
COLS = [
    "status",
    "nameplate_mw",
    "chp_pmin_cf",
    "chp_sector",
    "median_cf",
    "committed_pct",
]


def census(com: pd.DataFrame, head: pd.DataFrame) -> dict:
    """Which committed CHP columns a HEAD derive reproduces."""
    c = com[com.plant_group.str.contains("CHP")]
    h = head[head.plant_group.str.contains("CHP")]
    m = c.merge(h, on=KEY, how="outer", suffixes=("_c", "_h"), indicator=True)
    out = {"rows": m._merge.value_counts().to_dict()}
    for col in COLS:
        a, b = m[f"{col}_c"], m[f"{col}_h"]
        out[col] = f"{int(((a == b) | (a.isna() & b.isna())).sum())}/{len(m)}"
    return out


def levels(com: pd.DataFrame, head: pd.DataFrame) -> dict:
    """``{(code, group): (status, swapped level %)}`` with the conduct scope."""
    from market_sim.config.constants import CHP_STEAM_ALLHOURS_MIN_ON_FRAC

    c = com[com.plant_group.str.contains("CHP")][KEY + ["status", "chp_pmin_cf"]]
    c = c.merge(head[KEY + ["steam_level_cf", "median_cf"]], on=KEY, how="left")
    on = c.steam_level_cf / c.median_cf
    keep = np.where(c.status == "ok", on > CHP_STEAM_ALLHOURS_MIN_ON_FRAC, True)
    lvl = np.where(
        keep, np.maximum(c.chp_pmin_cf, c.steam_level_cf.fillna(0)), c.chp_pmin_cf
    )
    return {
        (int(r.plant_code), r.plant_group): (
            r.status,
            float(v),
            float(o) if o == o else None,
        )
        for r, v, o in zip(c.itertuples(), lvl, on)
    }


def main() -> int:
    """Run the three measurements and write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--head-derive", required=True, type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    a = ap.parse_args()
    com, head = pd.read_csv(ARTIFACT), pd.read_csv(a.head_derive)
    lv = levels(com, head)
    res: dict = {
        "census": census(com, head),
        "metered_on_frac": {
            f"{k[0]}:{k[1]}": v[2] for k, v in lv.items() if v[0] == "ok"
        },
        "added_vs_B_twh": {},
        "basis_2023": {},
    }
    for y in a.years:
        u = pd.read_parquet(
            LEG.format(y=y),
            columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
        )
        u = u[u.plant_group.astype(str).str.contains("CHP")]
        g = (
            u.groupby(KEY + ["hour"], observed=True)[["mw", "cap_mw"]]
            .sum()
            .reset_index()
        )
        add: dict[str, float] = {}
        for (pc, pg), d in g.groupby(KEY, observed=True):
            k = (int(pc), str(pg))
            if k not in lv or d.cap_mw.max() <= 0:
                continue
            st, lvl, _ = lv[k]
            f = np.minimum(lvl / 100 * d.cap_mw.max(), d.cap_mw.values)
            key = f"{pg}|{st}"
            add[key] = add.get(key, 0.0) + float(
                np.maximum(0, f - d.mw.values).sum() / 1e6
            )
            if y == 2023 and st == "ok":
                res["basis_2023"][f"{pc}:{pg}"] = {
                    "level": round(lvl, 1),
                    "grid_cap_mw": round(float(d.cap_mw.max())),
                    "B_twh": round(float(d.mw.sum() / 1e6), 2),
                    "floored_twh": round(
                        float(np.maximum(f, d.mw.values).sum() / 1e6), 2
                    ),
                }
        res["added_vs_B_twh"][y] = {k: round(v, 2) for k, v in sorted(add.items())}
        print(y, res["added_vs_B_twh"][y], flush=True)
    import scripts.run_calibration_full as rcf

    camp = rcf._campd_hourly_frame(2023, "MISO", rcf._parasitic_factor_map(), 8760)
    net = camp.groupby("plant_id").net_mw.sum() / 1e6
    for k, v in res["basis_2023"].items():
        v["campd_net_twh"] = round(float(net.get(int(k.split(":")[0]), np.nan)), 2)
    OUT.write_text(json.dumps(res, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
