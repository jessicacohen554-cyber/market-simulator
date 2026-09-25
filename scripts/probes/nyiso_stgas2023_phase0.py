"""NYISO-STGAS-2023 phase 0 (zero LP): decompose the 2023 ST_GAS over-dispatch.

Reads ONLY committed artifacts: the keeper's run payload (per-plant hourly model CF),
the NYISO bench parts (per-plant CAMPD hourly + EIA-923), the keeper bundles'
``hourly/class_band_hourly_<y>.parquet`` and ``legitimacy_diagnostics.json`` (D-2/D-4).
Writes ``results/calibration/_nyiso_stgas2023_phase0.json``.

2021 inputs (``results/calibration/rnyiso_2021``, run payload ``2026-09-25-nyiso-r-inputs-2021``
and ``bench/NYISO/2021.json.gz``) come from R-NYISO-2021's branch head
``8671806374d1c08a945f497769b65783cc2fc70e`` (PR #6636, closed unmerged); check them out from
that SHA to re-run 2021. They are not on ``main``.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RUNS = {
    "2026-09-24-nyiso-r-inputs-860vintage": "results/calibration/rnyiso_span",
    "2026-09-25-nyiso-r-inputs-2021": "results/calibration/rnyiso_2021",
}
YEARS = [2021, 2022, 2023, 2024, 2025]
T = 8760


def _payload(rid: str) -> dict:
    """Decode a gzip+base64 run payload."""
    s = (ROOT / f"frontend/data/backcast/runs/{rid}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def _cf(b64: str) -> np.ndarray:
    """Decode a uint8 CF% series."""
    return np.frombuffer(base64.b64decode(b64), np.uint8).astype(float)[:T]


def main() -> None:
    """Build the phase-0 decomposition."""
    yrs, bundles = {}, {}
    for rid, bdir in RUNS.items():
        p = _payload(rid)
        for y, v in p["years"].items():
            yrs[int(y)] = v
            bundles[int(y)] = bdir
    out: dict = {"years": {}}
    for y in YEARS:
        bench = json.loads(
            gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{y}.json.gz").read()
        )["bench"]
        P = yrs[y]["plants"]
        hrs = pd.date_range(f"{y}-01-01", periods=T, freq="h")
        plants = {}
        for key, bp in bench["plants"].items():
            if bp["group"] != "ST_GAS":
                continue
            mp = P.get(key) or P.get(key.split(":")[0])
            if mp is None:
                continue
            cap = bp["npl"]
            m = _cf(mp["m"]) * cap / 100.0
            c = _cf(bp["campd"]) * cap / 100.0
            df = pd.DataFrame({"m": m, "c": c}, index=hrs)
            plants[key] = {
                "name": bp["name"],
                "zone": bp["zone"],
                "npl_mw": cap,
                "model_twh": mp["m_ann"],
                "e923_twh": bp["e_ann"],
                "cems_twh": bp.get("c_ann"),
                "delta_vs_923_twh": round(mp["m_ann"] - bp["e_ann"], 3),
                "model_mon_gwh": mp["m_mon"],
                "e923_mon_gwh": bp["e_mon"],
                "model_hod_mw": df["m"].groupby(df.index.hour).mean().round(1).tolist(),
                "cems_hod_mw": df["c"].groupby(df.index.hour).mean().round(1).tolist(),
                "model_hours_on": int((m > 1).sum()),
                "cems_hours_on": int((c > 1).sum()),
                "model_mean_mw_when_on": round(
                    float(m[m > 1].mean()) if (m > 1).any() else 0, 1
                ),
                "cems_mean_mw_when_on": round(
                    float(c[c > 1].mean()) if (c > 1).any() else 0, 1
                ),
            }
        # class band split (committed = floor tranche, econ*/peak = merit order)
        cb = pd.read_parquet(
            ROOT / bundles[y] / f"hourly/class_band_hourly_{y}.parquet"
        )
        cb = cb[cb.klass == "ST_GAS"]
        band = (cb.groupby("band", observed=True)["mw"].sum() / 1e6).round(3).to_dict()
        # D-2 forced share
        ld = json.loads((ROOT / bundles[y] / "legitimacy_diagnostics.json").read_text())
        d2 = [
            r
            for r in ld["diagnostics"]["D2"]["rows"]
            if r["class"] == "ST_GAS" and r["year"] == y
        ]
        d4 = [
            r
            for r in ld["diagnostics"]["D4"]["rows"]
            if r["year"] == y
            and "ST_GAS" in r["floor"]
            and r["check"] == "unit-conduct"
        ]
        forced = sum(r["forced_twh"] for r in d2)
        tot_model = sum(v["model_twh"] for v in plants.values())
        tot_923 = sum(v["e923_twh"] for v in plants.values())
        by_zone: dict = {}
        for v in plants.values():
            z = by_zone.setdefault(v["zone"], {"model": 0.0, "e923": 0.0})
            z["model"] += v["model_twh"]
            z["e923"] += v["e923_twh"]
        out["years"][y] = {
            "stgas_model_twh_923set": round(tot_model, 3),
            "stgas_e923_twh": round(tot_923, 3),
            "c1_delta_twh": round(tot_model - tot_923, 3),
            "by_zone": {
                z: {k: round(x, 3) for k, x in v.items()}
                | {"delta": round(v["model"] - v["e923"], 3)}
                for z, v in by_zone.items()
            },
            "class_band_twh": band,
            "d2_forced": d2,
            "d2_forced_twh_total": round(forced, 4),
            "d4_unit_rows": [
                {
                    k: r[k]
                    for k in (
                        "floor",
                        "plant",
                        "floored_twh",
                        "binding_hours",
                        "measured_zero_share",
                        "verdict",
                    )
                }
                for r in d4
            ],
            "plants": plants,
        }
    dst = ROOT / "results/calibration/_nyiso_stgas2023_phase0.json"
    dst.write_text(json.dumps(out, indent=1))
    for y, v in out["years"].items():
        print(
            y,
            "C1d",
            v["c1_delta_twh"],
            "forced",
            v["d2_forced_twh_total"],
            "bands",
            v["class_band_twh"],
        )
        print("   zones", v["by_zone"])
        for k in ("2500:ST_GAS", "8906:ST_GAS", "8906", "2490:ST_GAS", "2490", "2516"):
            if k in v["plants"]:
                q = v["plants"][k]
                print(
                    f"   {k:12s} m={q['model_twh']:.2f} 923={q['e923_twh']:.2f} on m/c={q['model_hours_on']}/{q['cems_hours_on']}"
                    f" mw_on m/c={q['model_mean_mw_when_on']}/{q['cems_mean_mw_when_on']}"
                )
                print("      mon m", [round(x) for x in q["model_mon_gwh"]])
                print("      mon a", [round(x) for x in q["e923_mon_gwh"]])


if __name__ == "__main__":
    main()
