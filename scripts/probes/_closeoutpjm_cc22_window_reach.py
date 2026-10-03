"""closeout-PJM-cc22 phase 0 (zero LP): static reach of ``mustrun_online_frac_per_year`` on the PJM CC floor.

The keeper arms ``cc_mustrun_per_plant``: each CC_REGULAR plant's committed tranche is held on in the
top ``online_frac`` share of the solve year's hours ranked by system load. ``online_frac`` is the
POOLED 2023–2025 CEMS synchronization share (``thermal_tranches_PJM.csv``, reproduced to 5e-4 by
summing the per-year artifact over 2023–25), so 2020–22 are committed on a later vintage's window.
The per-year artifact ``thermal_tranches_online_frac_by_year_PJM.csv`` (2020–2025, no 2019 rows)
already exists; the gate ``mustrun_online_frac_per_year`` swaps the window size to the solve year's.

Static estimate on the keeper's own P1 dispatch (``unit_marginal_<y>``, ``system_<y>``):
- removed hours (pooled window minus own-year window): energy the floor forces, i.e. the committed
  tranche's MW in hours its offer sits above the zone price (out of money), is released;
- added hours (own-year minus pooled): the floor would force (cap − mw) where the tranche is below
  cap and out of money.
``d_forced`` is the net change in floor-forced CC energy (TWh, an UPPER bound on the CC cut before
re-dispatch); the CC class change after re-clear is ``d_forced × (1 − s)`` for a replacement share
``s`` that CC itself takes (0.35–0.50, the keeper's measured displacement shares). Also the share
of released energy in hours the plant's own CEMS meter was dark (rule 17 conduct reading).
Writes ``results/phase0/pjm/_closeoutpjm_cc22_window_reach.json``.
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURLY = REPO / "results/calibration/closeout_pjm_nuc_full_span/hourly"
POOL = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"
BYYEAR = (
    REPO / "data/raw/_processed-legacy/thermal_tranches_online_frac_by_year_PJM.csv"
)
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_cc22_window_reach.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
T = 8760
TOL = 0.01  # $/MWh: an offer this far above price is out of money


def _campd_on(bench: dict, pc: int) -> np.ndarray | None:
    """The plant's CEMS hourly on-mask (bench CAMPD CF bytes > 0), or None."""
    p = bench["plants"].get(str(pc))
    if not p or not p.get("campd") or str(p.get("nodata")) == "True":
        return None
    raw = np.frombuffer(base64.b64decode(p["campd"]), dtype=np.uint8)
    return raw[:T] > 0 if raw.size >= T else None


def run_year(y: int, pool: pd.DataFrame, byy: pd.DataFrame) -> dict:
    """Static reach for one year."""
    sysd = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    sysd = sysd[(sysd["pass"] == "P1") & (sysd.zone != "PJM_external")]
    load = sysd.groupby("hour").demand.sum().reindex(range(T)).to_numpy()
    rank = np.argsort(-load, kind="stable")
    price = sysd.pivot(index="hour", columns="zone", values="price")
    u = pd.read_parquet(
        HOURLY / f"unit_marginal_{y}.parquet",
        columns=[
            "unit_id",
            "plant_code",
            "plant_group",
            "zone",
            "hour",
            "mw",
            "cap_mw",
            "mc",
        ],
    )
    u = u[
        (u.plant_group.astype(str) == "CC_REGULAR")
        & u.unit_id.astype(str).str.endswith("_committed")
    ]
    bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
    own = byy[byy.year == y].set_index("plant_code").online_frac
    rows = []
    for (uid, pc), d in u.groupby([u.unit_id.astype(str), "plant_code"], observed=True):
        if (
            pc not in pool.index
            or pd.isna(pool.at[pc, "online_frac"])
            or pc not in own.index
        ):
            continue
        fp, fy = float(pool.at[pc, "online_frac"]), float(own.at[pc])
        d = d.sort_values("hour")
        mw, cap, mc = d.mw.to_numpy(), d.cap_mw.to_numpy(), d.mc.to_numpy()
        pz = price[str(d.zone.iloc[0])].to_numpy()
        oom = mc > pz + TOL
        np_, ny = int(round(fp * T)), int(round(fy * T))
        inpool = np.zeros(T, bool)
        inpool[rank[:np_]] = True
        inown = np.zeros(T, bool)
        inown[rank[:ny]] = True
        rem = inpool & ~inown
        add = inown & ~inpool
        released = float(np.where(rem & oom, mw, 0.0).sum())
        forced = float(np.where(add & oom, np.clip(cap - mw, 0, None), 0.0).sum())
        on = _campd_on(bench, pc)
        dark_rel = (
            float(np.where(rem & oom & ~on, mw, 0.0).sum())
            if on is not None
            else np.nan
        )
        rows.append(
            {
                "pc": int(pc),
                "pool": fp,
                "own": fy,
                "released": released,
                "forced": forced,
                "released_dark": dark_rel,
            }
        )
    df = pd.DataFrame(rows)
    rel, frc = df.released.sum() / 1e6, df.forced.sum() / 1e6
    return {
        "n": int(len(df)),
        "released_twh": round(rel, 3),
        "forced_twh": round(frc, 3),
        "d_forced_twh": round(frc - rel, 3),
        "cc_d_s035": round((frc - rel) * 0.65, 3),
        "cc_d_s050": round((frc - rel) * 0.50, 3),
        "released_dark_share": round(
            float(df.released_dark.sum() / max(df.released.sum(), 1e-9)), 3
        ),
        "top_released": df.sort_values("released", ascending=False)
        .head(6)[["pc", "pool", "own", "released"]]
        .assign(released=lambda x: (x.released / 1e6).round(3))
        .values.tolist(),
    }


def main() -> None:
    """Every year; print and write."""
    pool = pd.read_csv(POOL)
    pool = pool[(pool.plant_group == "CC_REGULAR") & (pool.status == "ok")].set_index(
        "plant_code"
    )
    byy = pd.read_csv(BYYEAR)
    byy = byy[byy.plant_group == "CC_REGULAR"]
    res = {}
    for y in YEARS:
        res[y] = (
            run_year(y, pool, byy)
            if y in set(byy.year)
            else {"n": 0, "note": "no own-year rows: pooled kept"}
        )
        print(y, {k: v for k, v in res[y].items() if k != "top_released"}, flush=True)
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
