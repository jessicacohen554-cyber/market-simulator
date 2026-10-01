"""PJM-NEXT-20 card 1c (zero LP): real coal's unit-grain state in in-merit hours.

Card 1 (``_pjmnext20_coal_price_response.py``) puts the 2019-2021/2025 coal over-run in
plant-hours where actual RT is above the keeper's own coal offer and the real plant is on.
This splits that real shortfall at CAMPD unit grain (``data/raw/campd-unit-level``, gross
load) for the keeper's COAL_* plants:

- ``units_on``: capacity share of the plant's units with gross load > 0 (unit capacity =
  the unit's own-year p99 gross load);
- ``on_loading``: gross load of on units / their capacity.

Each by year and by margin bin (actual RT minus the plant's MW-weighted model offer), with the
keeper's plant loading (model MW / available cap) beside it. If real on-unit loading is flat
in margin while the model's rises to full, the gap is partial-load conduct, not commitment.

Writes ``results/phase0/pjm/_pjmnext20_coal_unit_loading.json``.
Run: ``python3 scripts/probes/_pjmnext20_coal_unit_loading.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
CAMPD = REPO / "data/raw/campd-unit-level"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
OUT = REPO / "results/phase0/pjm/_pjmnext20_coal_unit_loading.json"
YEARS = range(2019, 2026)
T = 8760
STATES = (
    "PA",
    "OH",
    "WV",
    "VA",
    "MD",
    "IL",
    "IN",
    "KY",
    "NJ",
    "DE",
    "MI",
    "NC",
    "DC",
    "TN",
)
BINS = ((-1e9, 0), (0, 5), (5, 15), (15, 1e9))


def _model(y: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Keeper coal plant-hours: model MW, available cap, MW-weighted offer; and actual RT."""
    cols = ["plant_code", "plant_group", "hour", "mw", "cap_mw", "mc"]
    u = pd.read_parquet(HOURLY / f"unit_marginal_{y}.parquet", columns=cols)
    u = u[u.plant_group.astype(str).str.startswith("COAL") & (u.hour < T)]
    u["mwmc"] = u.mw * u.mc
    u["capmc"] = u.cap_mw * u.mc
    p = u.groupby(["plant_code", "hour"], observed=True)[
        ["mw", "cap_mw", "mwmc", "capmc"]
    ].sum()
    p = p.reset_index()
    p["offer"] = np.where(
        p.mw > 0, p.mwmc / p.mw.where(p.mw > 0, 1), p.capmc / p.cap_mw
    )
    act = pd.read_parquet(ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
    p = p.astype({"plant_code": "int32", "hour": "int32"})
    return p[["plant_code", "hour", "mw", "cap_mw", "offer"]], rt


def _campd(y: int, codes: set[int]) -> pd.DataFrame:
    """CAMPD unit hourly gross load for the keeper's coal plants -> plant-hour on-share, loading."""
    frames = []
    for st in STATES:
        f = CAMPD / f"{st}_{y}.parquet"
        if not f.exists():
            continue
        d = pd.read_parquet(
            f, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
        )
        d["facilityId"] = pd.to_numeric(d.facilityId, errors="coerce")
        frames.append(d[d.facilityId.isin(codes)])
    d = pd.concat(frames, ignore_index=True)
    t0 = pd.Timestamp(f"{y}-01-01")
    d["h"] = ((pd.to_datetime(d.date) - t0).dt.days * 24 + d.hour).astype(int)
    d = d[(d.h >= 0) & (d.h < T)]
    d["gl"] = d.grossLoad.fillna(0.0)
    cap = d.groupby(["facilityId", "unitId"]).gl.quantile(0.99).rename("ucap")
    d = d.join(cap, on=["facilityId", "unitId"])
    d = d[d.ucap > 0]
    d["on"] = d.gl > 0
    d["cap_on"] = d.ucap * d.on
    g = d.groupby(["facilityId", "h"])[["gl", "ucap", "cap_on"]].sum().reset_index()
    g = g.rename(columns={"facilityId": "plant_code", "h": "hour"})
    return g.astype({"plant_code": "int32", "hour": "int32"})


def year(y: int) -> dict:
    """One year."""
    p, rt = _model(y)
    c = _campd(y, set(int(x) for x in p.plant_code.unique()))
    j = p.merge(c, on=["plant_code", "hour"], how="inner")
    j["margin"] = rt[j.hour.to_numpy()] - j.offer
    res: dict = {"plants_joined": int(j.plant_code.nunique())}
    for lo, hi in BINS:
        k = j[(j.margin >= lo) & (j.margin < hi) & (j.cap_on > 0) & (j.cap_mw > 0)]
        tag = f"{lo if lo > -1e9 else '-inf'}..{hi if hi < 1e9 else 'inf'}"
        res[tag] = {
            "plant_hours": len(k),
            "real_units_on_share": round(float(k.cap_on.sum() / k.ucap.sum()), 3),
            "real_on_unit_loading": round(float(k.gl.sum() / k.cap_on.sum()), 3),
            "real_plant_loading": round(float(k.gl.sum() / k.ucap.sum()), 3),
            "model_plant_loading": round(float(k.mw.sum() / k.cap_mw.sum()), 3),
            "real_gross_over_model_avail": round(float(k.gl.sum() / k.cap_mw.sum()), 3),
            "model_twh": round(float(k.mw.sum()) / 1e6, 1),
            "real_gross_twh": round(float(k.gl.sum()) / 1e6, 1),
        }
    return res


def main() -> None:
    """Every year."""
    out: dict = {
        "what": "PJM-NEXT-20 card 1c: real coal unit state by margin. ZERO LP."
    }
    for y in YEARS:
        r = year(y)
        out[str(y)] = r
        print(y, r["plants_joined"])
        for k, v in r.items():
            if isinstance(v, dict):
                print("   ", k, v)
    OUT.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
