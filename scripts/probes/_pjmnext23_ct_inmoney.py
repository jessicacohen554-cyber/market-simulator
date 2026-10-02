"""PJM-NEXT-23 cards 1-2 (zero LP): do CT_PEAKER units run where their offer clears?

Per CT_PEAKER plant and year, against the plant's first econ tranche offer (``econc00`` P1
``mc``, hourly) from the keeper's ``unit_marginal_<y>``:

- ``h_pz_in``: hours the keeper's own zonal price >= the offer; ``h_rt_in`` / ``h_da_in``:
  hours PJM actual system RT / DA >= the offer;
- ``h_run_m`` / ``h_run_r``: model / real run-hours (output > 5 % of mean LP capacity; real =
  the C1 bench's CAMPD shape rescaled to EIA-923);
- ``twh_in_money``: real energy produced in hours where DA or RT >= the offer.

Capacity-weighted fleet aggregates by year plus the per-plant rows.
Writes ``results/phase0/pjm/_pjmnext23_ct_inmoney.json``.
Run: ``python3 scripts/probes/_pjmnext23_ct_inmoney.py``
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
OUT = REPO / "results/phase0/pjm/_pjmnext23_ct_inmoney.json"
YEARS = range(2019, 2026)
T = 8760
GROUP = "CT_PEAKER"
RUN_FRAC = 0.05


def bench_ct(y: int) -> dict[int, np.ndarray]:
    """C1 bench CT_PEAKER hourly real output (MW) per plant code."""
    bp = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    out: dict[int, np.ndarray] = {}
    for key, b in bp.items():
        if (
            b.get("group") != GROUP
            or b.get("nodata") in (True, "True")
            or not b.get("campd")
        ):
            continue
        raw = str(b.get("pcode") or key).split(":")[0]
        if raw.isdigit():
            out[int(raw)] = out.get(int(raw), 0) + _dec(
                b["campd"], b.get("e_ann") or b.get("c_ann")
            )
    return out


def plants_year(y: int, act: pd.DataFrame) -> list[dict]:
    """Per CT plant: in-money hours (model zonal / actual RT / actual DA) and run-hours."""
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
    u = u[(u.plant_group == GROUP) & (u.hour < T)]
    s = pd.read_parquet(HOURLY / f"system_{y}.parquet")
    pz_all = s.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(T)
    )
    a = act[act.year == y].sort_values("hour")
    rt, da = a.rt.to_numpy()[:T], a.da.to_numpy()[:T]
    bench = bench_ct(y)
    rows = []
    for code, g in u.groupby("plant_code", observed=True):
        zone = str(g.zone.iloc[0])
        e0 = g[g.unit_id.astype(str).str.endswith("_econc00")]
        if e0.empty or zone not in pz_all.columns:
            continue
        lo = e0.groupby("hour").mc.mean().reindex(range(T)).to_numpy()
        h = g.groupby("hour")[["mw", "cap_mw"]].sum().reindex(range(T)).fillna(0.0)
        mw, cap = h.mw.to_numpy(), h.cap_mw.to_numpy()
        thr = RUN_FRAC * cap.mean()
        pz = pz_all[zone].to_numpy()
        real = bench.get(int(code))
        inm = (rt >= lo) | (da >= lo)
        r = {
            "year": y,
            "plant_code": int(code),
            "zone": zone,
            "cap_mw": round(float(cap.mean()), 1),
            "offer_med": round(float(np.nanmedian(lo)), 2),
            "model_twh": round(mw.sum() / 1e6, 3),
            "h_pz_in": int((pz >= lo - 0.01).sum()),
            "h_rt_in": int((rt >= lo).sum()),
            "h_da_in": int((da >= lo).sum()),
            "h_run_m": int((mw > thr).sum()),
        }
        if real is not None:
            on = real > thr
            r.update(
                bench_twh=round(real.sum() / 1e6, 3),
                h_run_r=int(on.sum()),
                twh_in_money=round(real[inm].sum() / 1e6, 3),
                da_med_when_on=round(float(np.median(da[on])), 2) if on.any() else None,
            )
        rows.append(r)
    return rows


def main() -> None:
    """Fleet aggregates by year + per-plant rows."""
    act = pd.read_parquet(ACTUAL)
    df = pd.DataFrame([r for y in YEARS for r in plants_year(y, act)])
    d = df[df.bench_twh.notna() & (df.cap_mw > 20)]
    agg = {}
    for y, g in d.groupby("year"):
        w = g.cap_mw / g.cap_mw.sum()
        agg[int(y)] = {
            **{
                c: round(float((g[c] * w).sum()), 0)
                for c in (
                    "offer_med",
                    "h_pz_in",
                    "h_rt_in",
                    "h_da_in",
                    "h_run_m",
                    "h_run_r",
                )
            },
            "model_twh": round(float(g.model_twh.sum()), 2),
            "bench_twh": round(float(g.bench_twh.sum()), 2),
            "share_real_twh_in_money": round(
                float(g.twh_in_money.sum() / g.bench_twh.sum()), 3
            ),
        }
        print(y, agg[int(y)], flush=True)
    OUT.write_text(
        json.dumps(
            {"by_year": agg, "plants": df.replace({np.nan: None}).to_dict("records")},
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
