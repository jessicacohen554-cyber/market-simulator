"""PJM-NEXT-23 cards 1-2 (zero LP): CT_PEAKER per plant and per year, keeper vs the C1 bench.

Keeper P1 per-unit layer (``unit_marginal_<y>``) vs the C1 bench (EIA-923 net, CAMPD-shaped) for
every CT_PEAKER plant, 2019-2025. Per plant-year:

- ``model`` / ``bench`` TWh, the over-run, mean LP capacity and capacity factors on it;
- output by tranche band (``committed`` / ``econ`` / ``peak``, from the unit id suffix);
- ``offer``: capacity-weighted P1 offer of the plant's econ tranches (the first econ step's offer
  is ``offer_lo``); ``rt``: PJM actual RT (system);
- run-hours: model hours with output > 5 % of the plant's LP capacity, real hours with CAMPD
  output > 5 % of the same capacity; hours where actual RT >= ``offer_lo`` (``rt_in``).

Aggregates by zone-year, and splits 2022 -> 2023 by continuing plants vs fleet change.

Writes ``results/phase0/pjm/_pjmnext23_ct_plants.json`` (+ a per plant-year parquet in the
scratch dir is NOT written; the JSON carries every plant-year row).
Run: ``python3 scripts/probes/_pjmnext23_ct_plants.py``
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
OUT = REPO / "results/phase0/pjm/_pjmnext23_ct_plants.json"
YEARS = range(2019, 2026)
T = 8760
GROUP = "CT_PEAKER"
RUN_FRAC = 0.05  # an hour "runs" when output exceeds this share of LP capacity


def band_of(unit_id: str) -> str:
    """Tranche band from the unit id suffix (``_committed`` / ``_econcNN`` / ``_peak``)."""
    tail = unit_id.rsplit("_", 1)[-1]
    if tail.startswith("econ"):
        return "econ"
    return tail if tail in ("committed", "peak") else "other"


def plants_year(y: int, rt: np.ndarray) -> pd.DataFrame:
    """Per CT_PEAKER plant: model/bench TWh, bands, offers, run-hours."""
    cols = [
        "unit_id",
        "plant_code",
        "plant_group",
        "zone",
        "hour",
        "mw",
        "cap_mw",
        "mc",
    ]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[(u.plant_group == GROUP) & (u.hour < T)].copy()
    u["band"] = u.unit_id.astype(str).map(band_of)
    u["capmc"] = u.cap_mw * u.mc
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    bench: dict[int, list[dict]] = {}
    for key, b in bp.items():
        if str(b.get("group", "")) != GROUP:
            continue
        raw = str(b.get("pcode") or key).split(":")[0]
        if raw.isdigit():
            bench.setdefault(int(raw), []).append(b)
    rows = []
    for code, g in u.groupby("plant_code", observed=True):
        h = g.groupby("hour")[["mw", "cap_mw"]].sum()
        mw = np.zeros(T)
        cap = np.zeros(T)
        mw[h.index.to_numpy()] = h.mw.to_numpy()
        cap[h.index.to_numpy()] = h.cap_mw.to_numpy()
        econ = g[g.band == "econ"]
        offer = (
            float(econ.capmc.sum() / econ.cap_mw.sum())
            if econ.cap_mw.sum() > 0
            else np.nan
        )
        lo_ids = sorted(econ.unit_id.astype(str).unique())
        lo = econ[econ.unit_id.astype(str) == lo_ids[0]] if lo_ids else econ
        lo_h = lo.groupby("hour").mc.mean().reindex(range(T)).to_numpy()
        real = np.zeros(T)
        benched = False
        for b in bench.get(int(code), []):
            if b.get("nodata") not in (True, "True") and b.get("campd"):
                real = real + _dec(b["campd"], b.get("e_ann") or b.get("c_ann"))
                benched = True
        cmean = cap.mean()
        thr = RUN_FRAC * cmean
        r = {
            "plant_code": int(code),
            "name": (bench.get(int(code)) or [{}])[0].get("name", ""),
            "zone": str(g.zone.iloc[0]),
            "benched": benched,
            "model_twh": mw.sum() / 1e6,
            "bench_twh": real.sum() / 1e6,
            "cap_mw": cmean,
            "offer": offer,
            "offer_lo": float(np.nanmean(lo_h)) if lo_ids else np.nan,
            "run_h_model": int((mw > thr).sum()),
            "run_h_real": int((real > thr).sum()) if benched else None,
            "rt_in_h": int((rt >= lo_h).sum()) if lo_ids else None,
        }
        for band in ("committed", "econ", "peak"):
            r[f"{band}_twh"] = g.loc[g.band == band, "mw"].sum() / 1e6
            r[f"{band}_cap"] = g.loc[g.band == band, "cap_mw"].sum() / T
        rows.append(r)
    df = pd.DataFrame(rows)
    df["over"] = df.model_twh - df.bench_twh
    df["year"] = y
    return df


def main() -> None:
    """Build the plant-year table, zone-year aggregates and the 2022 -> 2023 split."""
    act = pd.read_parquet(ACTUAL)
    frames = []
    for y in YEARS:
        rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
        frames.append(plants_year(y, rt))
        print(y, "done", flush=True)
    df = pd.concat(frames, ignore_index=True)
    agg = {
        "model_twh": "sum",
        "bench_twh": "sum",
        "over": "sum",
        "cap_mw": "sum",
        "committed_twh": "sum",
        "econ_twh": "sum",
        "peak_twh": "sum",
        "committed_cap": "sum",
        "plant_code": "count",
    }
    by_year = df.groupby("year").agg(agg).round(2)
    by_zone = df.groupby(["zone", "year"]).agg(agg).round(2)
    w = df.assign(ow=df.offer * df.cap_mw)
    offer_zone = (
        w.groupby(["zone", "year"]).ow.sum() / w.groupby(["zone", "year"]).cap_mw.sum()
    ).round(2)
    a, b = (
        df[df.year == 2022].set_index("plant_code"),
        df[df.year == 2023].set_index("plant_code"),
    )
    both = a.index.intersection(b.index)
    split = {
        "continuing_n": int(len(both)),
        "continuing_delta_model": round(
            b.loc[both].model_twh.sum() - a.loc[both].model_twh.sum(), 2
        ),
        "continuing_delta_bench": round(
            b.loc[both].bench_twh.sum() - a.loc[both].bench_twh.sum(), 2
        ),
        "exits_2022_model": round(a.drop(both).model_twh.sum(), 2),
        "exits_2022_bench": round(a.drop(both).bench_twh.sum(), 2),
        "entries_2023_model": round(b.drop(both).model_twh.sum(), 2),
        "entries_2023_bench": round(b.drop(both).bench_twh.sum(), 2),
        "entries_2023_cap": round(b.drop(both).cap_mw.sum(), 0),
        "exits_2022_cap": round(a.drop(both).cap_mw.sum(), 0),
    }
    out = {
        "by_year": by_year.reset_index().to_dict("records"),
        "by_zone": by_zone.reset_index().to_dict("records"),
        "offer_by_zone": offer_zone.rename("offer").reset_index().to_dict("records"),
        "split_2022_2023": split,
        "plants": df.round(3).replace({np.nan: None}).to_dict("records"),
    }
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(by_year.to_string())
    print(json.dumps(split, indent=1))


if __name__ == "__main__":
    main()
