"""PJM-NEXT-18 card 2 (zero LP): which offer band carries the CC_REGULAR night over-load?

NEXT-16 card 1 located the CC_REGULAR year signal in LOADING at night (+4.3 TWh in 2023,
+0.1 in 2024). This probe splits the keeper's own CC_REGULAR energy by offer BAND
(``hourly/class_band_hourly_<y>.parquet``: mustrun / committed / sync / econ*) and by
night (HE 24-07) vs day, and sets it against the actual CC_REGULAR energy in the same
hours (``bench/PJM/<y>.json.gz`` CAMPD rescaled to EIA-923 net, the NEXT-15/16 basis) and
against the model vs actual price in those hours (load-weighted P1 vs RT hub).

If the night excess sits in the committed/mustrun floor, it is a commitment object
(``cc_mustrun_per_plant``, rule 17); if it sits in the econ bands, the night price is high
enough to clear CC econ, which is the card-1 price-floor object seen from the CC side.

Run: ``python3 scripts/probes/_pjmnext18_cc_night_band.py``
Writes ``results/phase0/pjm/_pjmnext18_cc_night_band.json``.
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
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext18_cc_night_band.json"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
KLASS = "CC_REGULAR"
T = 8760
#: Night = HE 24-07, i.e. model hour-of-day index 23 and 0-6 (hour 0 = HE 01).
NIGHT = np.isin(np.arange(T) % 24, [23, 0, 1, 2, 3, 4, 5, 6])


def _band_group(b: str) -> str:
    """Collapse the band label to floor / sync / econ."""
    if b in ("mustrun", "committed"):
        return "floor"
    if b == "sync":
        return "sync"
    if b.startswith("econ"):
        return "econ"
    return b or "unbanded"


def main() -> None:
    """Band x night/day census for every year; write the JSON artifact."""
    res: dict = {"what": "PJM-NEXT-18 card 2: CC_REGULAR night load by band. ZERO LP."}
    act_px = pd.read_parquet(ACTUAL)
    for y in YEARS:
        cb = pd.read_parquet(HOURLY / f"class_band_hourly_{y}.parquet")
        cb = cb[(cb["pass"].astype(str) == "P1") & (cb.klass.astype(str) == KLASS)]
        cb = cb.assign(g=cb.band.astype(str).map(_band_group))
        piv = (
            cb.pivot_table(index="hour", columns="g", values="mw", aggfunc="sum")
            .reindex(range(T))
            .fillna(0.0)
        )
        bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        act = np.zeros(T)
        for bp in bench["plants"].values():
            if bp.get("group") != KLASS or bp.get("nodata") or not bp.get("campd"):
                continue
            act += _dec(bp["campd"], bp.get("e_ann") or bp.get("c_ann"))
        s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
        s = s[(s["pass"].astype(str) == "P1") & (s.hour < T)]
        s = s[s.zone.astype(str) != "PJM_external"]
        lw = (s.price * s.demand).groupby(s.hour).sum() / s.demand.groupby(s.hour).sum()
        lw = lw.reindex(range(T)).to_numpy()
        rt = act_px[act_px.year == y].sort_values("hour").rt.to_numpy()[:T]
        row: dict = {}
        for name, mask in (("night", NIGHT), ("day", ~NIGHT)):
            bands = {
                k: round(float(piv[k].to_numpy()[mask].sum()) / 1e6, 2) for k in piv
            }
            model = float(piv.to_numpy()[mask].sum()) / 1e6
            actual = float(act[mask].sum()) / 1e6
            row[name] = {
                "model_twh": round(model, 2),
                "actual_twh": round(actual, 2),
                "gap_twh": round(model - actual, 2),
                "model_by_band_twh": bands,
                "median_price_model_lw": round(float(np.nanmedian(lw[mask])), 2),
                "median_price_actual_rt": round(float(np.nanmedian(rt[mask])), 2),
            }
        res[str(y)] = row
        n = row["night"]
        print(
            y,
            "night gap",
            n["gap_twh"],
            "bands",
            n["model_by_band_twh"],
            "px m/a",
            n["median_price_model_lw"],
            n["median_price_actual_rt"],
        )
    OUT.write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
