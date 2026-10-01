"""PJM-NEXT-19 card 1b (zero LP): in the keeper's coal-set hours, what did real PJM run instead?

A "coal-set hour" is a keeper P1 hour whose marginal weight is >= 0.5 on COAL_* (NEXT-18,
``unit_marginal_<y>.parquet``). Over those hours, and over all other hours, compares the
keeper's class MW (``class_hourly``) with the C1 bench's per-plant CAMPD hourly profile
rescaled to each plant's EIA-923 annual (the NEXT-15/16/18 ``_dec`` basis), by bench group.
Classes the bench carries no hourly profile for (nuclear, VRE, hydro, imports) are
reported model-side only.

The question: when the model's coal is marginal and over-runs (2019-2021), is real PJM
running more CC (merit-order displacement) or is the excess system-wide (the NEXT-16
``U_a`` / export object)?

Writes ``results/phase0/pjm/_pjmnext19_coalset_balance.json``.
Run: ``python3 scripts/probes/_pjmnext19_coalset_balance.py``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext16_cc_loading import _dec  # noqa: E402

HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
BENCH = REPO / "frontend/data/backcast/bench/PJM"
OUT = REPO / "results/phase0/pjm/_pjmnext19_coalset_balance.json"
YEARS = range(2019, 2026)
T = 8760
COAL_SET_WEIGHT = 0.5
GROUPS = ("COAL", "CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "CT_CHP")


def _grp(k: str) -> str:
    """Collapse COAL_* subclasses."""
    return "COAL" if k.startswith("COAL") else k


def _coal_set_mask(y: int) -> np.ndarray:
    """Boolean 8760 mask of the keeper's coal-set hours."""
    cols = ["plant_group", "hour", "marginal"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    m = u[(u.marginal == 1) & (u.hour < T)].copy()
    m["coal"] = m.plant_group.astype(str).str.startswith("COAL")
    m["w"] = 1.0 / m.groupby("hour").hour.transform("size")
    cw = m[m.coal].groupby("hour").w.sum()
    mask = np.zeros(T, bool)
    mask[cw[cw >= COAL_SET_WEIGHT].index.to_numpy()] = True
    return mask


def main() -> None:
    """Class balance in coal-set vs other hours, every year."""
    res: dict = {"what": "PJM-NEXT-19 card 1b: coal-set-hour class balance. ZERO LP."}
    for y in YEARS:
        mask = _coal_set_mask(y)
        c = pd.read_parquet(HOURLY / f"class_hourly_{y}.parquet")
        c = c[(c["pass"].astype(str) == "P1") & (c.hour < T)]
        c = c.assign(g=c.klass.astype(str).map(_grp))
        piv = c.pivot_table(index="hour", columns="g", values="mw", aggfunc="sum")
        piv = piv.reindex(range(T)).fillna(0.0)
        act = {g: np.zeros(T) for g in GROUPS}
        for bp in json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"][
            "plants"
        ].values():
            g = _grp(str(bp.get("group")))
            if g not in act or bp.get("nodata") == "True" or not bp.get("campd"):
                continue
            act[g] += _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
        row: dict = {"coal_set_hours": int(mask.sum())}
        for name, mk in (("coal_set", mask), ("other", ~mask)):
            d = {}
            for g in GROUPS:
                mm = float(piv[g].to_numpy()[mk].sum()) / 1e6 if g in piv else 0.0
                aa = float(act[g][mk].sum()) / 1e6
                d[g] = {
                    "model": round(mm, 2),
                    "actual": round(aa, 2),
                    "gap": round(mm - aa, 2),
                }
            for g in (
                "nuclear",
                "wind",
                "solar",
                "hydro",
                "import",
                "OTHER",
                "biomass",
            ):
                if g in piv:
                    d[g] = {"model": round(float(piv[g].to_numpy()[mk].sum()) / 1e6, 2)}
            d["fossil_gap"] = round(sum(d[g]["gap"] for g in GROUPS), 2)
            row[name] = d
        res[str(y)] = row
        cs = row["coal_set"]
        print(
            y,
            row["coal_set_hours"],
            {g: cs[g]["gap"] for g in GROUPS},
            "fossil",
            cs["fossil_gap"],
            "| other fossil",
            row["other"]["fossil_gap"],
        )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
