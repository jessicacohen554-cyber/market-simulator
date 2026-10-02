"""PJM-NEXT-24 card 2 (zero LP): what real CTs are doing below their offer - run-block anatomy.

Card 1 (``_pjmnext24_loading_margin.py``) puts the CT_PEAKER gap at a persistent real
under-run at actual-price margins <= -$10 (-3 to -8 TWh every year). This splits real CT
energy (C1 bench: EIA-923 net, CAMPD hourly shape) into run blocks - maximal runs of
consecutive hours with output > 5 % of the plant's mean LP capacity - and classifies each
block by its best hour against the plant's keeper offer (capacity-weighted P1 ``mc``):

- ``in_money``: an hour of the block clears (actual DA or RT >= offer); its energy in
  out-of-money hours is the run-block tail around a cleared hour;
- ``near``: never clears, best margin within $10 of the offer;
- ``deep``: never clears, best margin below -$10 (whole block well below the offer).

Per year: energy and block counts by class, block-length quartiles by class, and the
deep-block energy by zone and by hour-of-day / month (when the deep blocks happen). The
same split is reported for the keeper's own CT output, on the keeper's zonal price.

Writes ``results/phase0/pjm/_pjmnext24_ct_runblocks.json``.
Run: ``python3 scripts/probes/_pjmnext24_ct_runblocks.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
from _pjmnext24_loading_margin import ACTUAL, T, YEARS, plant_hours  # noqa: E402

OUT = REPO / "results/phase0/pjm/_pjmnext24_ct_runblocks.json"
RUN_FRAC = 0.05
NEAR = -10.0


def blocks(on: np.ndarray) -> list[tuple[int, int]]:
    """Maximal [start, end) runs of True."""
    d = np.diff(np.r_[0, on.astype(int), 0])
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)))


def classify(g: pd.DataFrame, out_col: str, best_cols: tuple[str, ...]) -> pd.DataFrame:
    """One plant's run blocks for output column ``out_col``, classified by best margin."""
    g = g.sort_values("hour")
    x = np.zeros(T)
    x[g.hour.to_numpy()] = g[out_col].to_numpy()
    cap = np.zeros(T)
    cap[g.hour.to_numpy()] = g.cap.to_numpy()
    m = np.full(T, -1e9)
    for c in best_cols:
        mc = np.full(T, -1e9)
        mc[g.hour.to_numpy()] = g[c].fillna(-1e9).to_numpy()
        m = np.maximum(m, mc)
    rows = []
    for s, e in blocks(x > RUN_FRAC * cap.mean()):
        best = m[s:e].max()
        cls = "in_money" if best >= 0 else ("near" if best >= NEAR else "deep")
        rows.append(
            {
                "start": int(s),
                "len": int(e - s),
                "mwh": float(x[s:e].sum()),
                "mwh_oom": float(x[s:e][m[s:e] < 0].sum()),
                "best": float(best),
                "cls": cls,
            }
        )
    return pd.DataFrame(rows)


def year(y: int, act: pd.DataFrame) -> dict:
    """One year: real and keeper CT run blocks."""
    p = plant_hours(y, act)
    p = p[p.k == "CT"]
    res: dict = {}
    for who, col, axes in (
        ("real", "real", ("m_rt", "m_da")),
        ("model", "mw", ("m_pz",)),
    ):
        frames = []
        for code, g in p.groupby("plant_code"):
            b = classify(g, col, axes)
            if len(b):
                b["plant_code"] = int(code)
                b["zone"] = g.zone.iloc[0]
                frames.append(b)
        b = pd.concat(frames, ignore_index=True)
        tot = b.mwh.sum()
        r = {"twh": round(tot / 1e6, 2), "blocks": len(b)}
        for cls, g in b.groupby("cls"):
            r[cls] = {
                "twh": round(g.mwh.sum() / 1e6, 2),
                "share": round(float(g.mwh.sum() / tot), 3),
                "twh_in_oom_hours": round(g.mwh_oom.sum() / 1e6, 2),
                "blocks": len(g),
                "len_q": [float(v) for v in g.len.quantile([0.25, 0.5, 0.75])],
            }
        d = b[b.cls == "deep"]
        if who == "real" and len(d):
            r["deep_by_zone_twh"] = {
                z: round(v / 1e6, 2)
                for z, v in d.groupby("zone")
                .mwh.sum()
                .sort_values(ascending=False)
                .items()
            }
            hod = (d.start % 24).to_numpy()
            mon = np.minimum(d.start // 730, 11).to_numpy()
            r["deep_start_hod_share"] = np.round(
                np.bincount(hod, weights=d.mwh, minlength=24) / d.mwh.sum(), 3
            ).tolist()
            r["deep_month_share"] = np.round(
                np.bincount(mon, weights=d.mwh, minlength=12) / d.mwh.sum(), 3
            ).tolist()
            r["deep_best_margin_q"] = [
                round(float(v), 1) for v in d.best.quantile([0.25, 0.5, 0.75])
            ]
            top = (
                d.groupby("plant_code").mwh.sum().sort_values(ascending=False).head(12)
            )
            r["deep_top_plants_twh"] = {
                int(k): round(v / 1e6, 3) for k, v in top.items()
            }
        res[who] = r
    return res


def main() -> None:
    """Every year."""
    act = pd.read_parquet(ACTUAL)
    out: dict = {"what": "PJM-NEXT-24 card 2: real CT run-block anatomy. ZERO LP."}
    for y in YEARS:
        out[str(y)] = year(y, act)
        r = out[str(y)]["real"]
        print(
            y,
            r["twh"],
            {
                c: (r[c]["twh"], r[c]["len_q"][1])
                for c in ("in_money", "near", "deep")
                if c in r
            },
            "| model",
            {
                c: out[str(y)]["model"][c]["twh"]
                for c in ("in_money", "near", "deep")
                if c in out[str(y)]["model"]
            },
            flush=True,
        )
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
