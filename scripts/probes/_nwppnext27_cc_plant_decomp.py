"""NWPP-NEXT-27 zero-LP phase 0: where the keeper's CC_REGULAR over-run sits, plant by plant and hour by hour.

Reads only committed artifacts — no LP, no fleet build:
  - keeper bundle results/calibration/nwppnext26_span/hourly/unit_marginal_<Y>.parquet (per-unit P1 mw / cap_mw / mc)
  - keeper bundle hourly/system_<Y>.parquet (zonal prices)
  - the NWPP bench frontend/data/backcast/bench/NWPP/<Y>.json.gz (CAMPD hourly CF per plant, EIA-923 annual)

For each CC_REGULAR plant it splits model-minus-CAMPD energy into three hour sets: CAMPD off / model on
("commitment"), both on ("loading"), model off / CAMPD on ("short"). Writes
results/phase0/nwpp/_nwppnext27_cc_plant_decomp.json. Record: docs/records/nwpp/FINDING-nwppnext27-*.md.
"""

from __future__ import annotations

import base64
import gzip
import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

BUNDLE = REPO_ROOT / "results/calibration/nwppnext26_span/hourly"
OFF_PCT = 5.0  # CAMPD hour counted "off" below 5 % of nameplate (CEMS idle/aux noise)


def decode(b64: str) -> np.ndarray:
    """Decode a bench CAMPD CF series (uint8 percent of nameplate)."""
    return np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)


def year_census(year: int) -> dict:
    """Per-plant CC_REGULAR decomposition for one year."""
    bench = json.load(gzip.open(REPO_ROOT / f"frontend/data/backcast/bench/NWPP/{year}.json.gz"))["bench"]["plants"]
    um = pd.read_parquet(BUNDLE / f"unit_marginal_{year}.parquet")
    um = um[um["plant_group"] == "CC_REGULAR"]
    out = {}
    for code, g in um.groupby("plant_code", observed=True):
        mw = g.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0).to_numpy(float)
        cap = g.groupby("hour")["cap_mw"].sum().reindex(range(8760), fill_value=0).to_numpy()
        mc = g.groupby("hour")["mc"].mean().reindex(range(8760)).to_numpy()
        b = bench.get(str(code)) or bench.get(f"{code}|CC_REGULAR")
        if b is None:
            out[int(code)] = {"model_twh": round(float(mw.sum()) / 1e6, 3), "bench": None}
            continue
        cf = decode(b["campd"])[:8760]
        act = cf / 100.0 * b["npl"]
        on_m, on_a = mw > 1.0, cf >= OFF_PCT
        out[int(code)] = {
            "name": b["name"], "zone": b["zone"], "npl": b["npl"],
            "model_twh": round(float(mw.sum()) / 1e6, 3), "campd_twh": round(act.sum() / 1e6, 3), "e923_twh": b["e_ann"],
            "commit_twh": round(float(mw[on_m & ~on_a].sum()) / 1e6, 3),
            "load_twh": round(float((mw - act)[on_m & on_a].sum()) / 1e6, 3),
            "short_twh": round(-act[~on_m & on_a].sum() / 1e6, 3),
            "hours_on_model": int(on_m.sum()), "hours_on_campd": int(on_a.sum()),
            "mean_cap_mw": round(float(cap.mean()), 1),
            "mean_load_on_model_mw": round(float(mw[on_m].mean()) if on_m.any() else 0.0, 1),
            "mean_load_on_campd_mw": round(float(act[on_a].mean()) if on_a.any() else 0.0, 1),
            "mean_mc": round(float(np.nanmean(mc)), 2),
        }
    return out


def main() -> None:
    """Run the census for the requested years and write the JSON record."""
    years = [int(y) for y in sys.argv[1:]] or [2019, 2023, 2024, 2025]
    res = {y: year_census(y) for y in years}
    dst = REPO_ROOT / "results/phase0/nwpp/_nwppnext27_cc_plant_decomp.json"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(res, indent=1))
    for y, r in res.items():
        rows = sorted((v for v in r.values() if v.get("bench")is not False and "campd_twh" in v),
                      key=lambda v: v["model_twh"] - v["e923_twh"], reverse=True)
        print(f"== {y}  model {sum(v['model_twh'] for v in r.values()):.2f}  e923 {sum(v.get('e923_twh',0) for v in r.values()):.2f}")
        print("name zone npl model campd e923 | commit load short | h_on m/a | cap  loadM loadA mc")
        for v in rows:
            print(f"{v['name'][:20]:20s} {v['zone'][5:]:6s} {v['npl']:5d} {v['model_twh']:6.2f} {v['campd_twh']:6.2f} {v['e923_twh']:6.2f} | "
                  f"{v['commit_twh']:6.2f} {v['load_twh']:6.2f} {v['short_twh']:6.2f} | {v['hours_on_model']:4d}/{v['hours_on_campd']:4d} | "
                  f"{v['mean_cap_mw']:6.0f} {v['mean_load_on_model_mw']:5.0f} {v['mean_load_on_campd_mw']:5.0f} {v['mean_mc']:5.1f}")


if __name__ == "__main__":
    main()
