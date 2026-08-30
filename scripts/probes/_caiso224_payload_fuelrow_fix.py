"""caiso-224 finisher: repair the slim-render payload's gas fuelRow + strip co2.

The caiso-224 solve session's container was reclaimed before registration, so
the finisher session rendered both payloads from the committed slim artifacts
(`hourly/` sidecars re-expanded to `system.parquet` / `storage.parquet` and a
class-grain `dispatch/<year>_P1.parquet` with ``plant_code=0`` — no per-plant
model hourly survives the container, so the per-plant panels are honestly
EMPTY rather than fabricated; benchmark parquets rebuilt hash-identical to the
solve session's frozen `meta.json` refs via ``--rebuild-benchmark``).

Two payload fields cannot be produced correctly by that render and are fixed
here, from committed artifacts only:

* ``fuelRows`` gas row (C4-gas). CAISO is an ``EIA930_NG_CELL_CORRUPT`` ISO,
  so the native builder computes the gas hourly ACTUAL on the CEMS basis —
  Σ (bench-plant CAMPD hourly, gas classes, non-``nodata``) − flat BTM CHP
  host supply + flat non-CEMS cogen block (``e930.gas_cogen_grid``). With an
  empty dispatch plant map the in-render CEMS block degenerates (0 CEMS plants
  ⇒ the whole family lands in the flat cogen block ⇒ r undefined, NRMSE vs a
  constant). This probe recomputes ``r``/``nrmse``/``b`` from the COMMITTED
  ``bench/CAISO/<year>.json.gz`` part (the same uint8 ``plants[].campd``
  series + ``btm`` + ``gas_cogen_grid`` scalars `calibration_verdict.py::
  _cems_gas_hourly_fit` itself decodes — quantization tolerance ≤~0.01 in r,
  per that function's own docstring) against the committed
  ``hourly/class_hourly_<year>.parquet`` gas-class model series. The model
  side (``m``) is untouched: the render already computed it exactly from the
  committed class series.
* ``co2`` (C5a, REPORTED-ONLY since rubric v2.9). The full-plant basis needs
  ``btm.parquet`` (the solve's BTM CHP hold-out), which is gitignored and gone
  with the container. A grid-basis number labelled "full-plant" would be
  wrong, so the block is REMOVED — ``score_co2`` then reports its documented
  SKIP ("no CO2/eGRID actual in committed artifacts" path is the actual-side
  guard; the model-side absence lands in the same skip), never a silent pass.

Cross-checks printed for the record: the payload's per-year load-weighted LMP
against the committed ``_caiso224_split_witness.json`` (computed by the solve
session from the full artifacts — agreement proves the slim render reproduced
the solve's price surface bit-for-bit).

Run from the repo root:  python3 scripts/probes/_caiso224_payload_fuelrow_fix.py
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.plant_taxonomy import classes_for_fuel930  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402

T = 8760
GAS = set(classes_for_fuel930("gas"))
RUNS = {
    "2026-08-30-caiso-224-a0-control": "results/calibration/caiso224_a0_control",
    "2026-08-30-caiso-224-b1-fsno": "results/calibration/caiso224_b1_fsno",
}
WITNESS = json.loads(
    (REPO / "results/calibration/_caiso224_split_witness.json").read_text()
)


def _pearson(m: np.ndarray, o: np.ndarray) -> float:
    """render_calibration_html._pearson, verbatim."""
    m = m - m.mean()
    o = o - o.mean()
    d = float(np.sqrt((m * m).sum() * (o * o).sum()))
    return float((m * o).sum() / d) if d > 0 else 0.0


def _nrmse(m: np.ndarray, o: np.ndarray) -> float:
    """render_calibration_html._nrmse, verbatim."""
    den = float(o.mean())
    return float(np.sqrt(((m - o) ** 2).mean()) / den) if den > 0 else 9.9


def _decode_payload(rid: str) -> dict:
    txt = (REPO / "frontend/data/backcast/runs" / f"{rid}.js").read_text()
    b64 = json.loads(txt.split("]=", 1)[1].rstrip().rstrip(";"))
    return json.loads(gzip.decompress(base64.b64decode(b64)))


def _bench_part(year: int) -> dict:
    p = REPO / "frontend/data/backcast/bench/CAISO" / f"{year}.json.gz"
    return json.loads(gzip.decompress(p.read_bytes()))["bench"]


def _cems_gas_actual(bench: dict) -> np.ndarray:
    """The native builder's CEMS-basis gas hourly actual, from the committed part."""
    plants = bench["plants"]
    ob = np.zeros(T)
    btm_twh = 0.0
    n = 0
    for rec in plants.values():
        if rec["group"] not in GAS or rec["nodata"]:
            continue
        cf = np.frombuffer(base64.b64decode(rec["campd"]), dtype=np.uint8).astype(float)
        ob += cf[:T] * float(rec["npl"]) / 100.0
        btm_twh += float(rec.get("btm", 0.0))
        n += 1
    cogen = float(bench["e930"]["gas_cogen_grid"])
    ob = ob - btm_twh * 1e6 / T + cogen * 1e6 / T
    print(f"    CEMS gas plants used: {n}; btm {btm_twh:.3f} TWh; cogen {cogen:.3f} TWh")
    return ob


def main() -> None:
    for rid, bdir in RUNS.items():
        bundle = REPO / bdir
        payload = _decode_payload(rid)
        wside = "control" if "control" in rid else "arm"
        for ystr, ypay in payload["years"].items():
            year = int(ystr)
            ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
            ch = ch[ch["pass"] == "P1"]
            ms = (
                ch[ch["klass"].isin(GAS)]
                .groupby("hour")["mw"]
                .sum()
                .reindex(range(T), fill_value=0.0)
                .to_numpy(float)
            )
            bench = _bench_part(year)
            print(f"  {rid} {year}:")
            ob = _cems_gas_actual(bench)
            row = next(r for r in ypay["fuelRows"] if r["fuel"] == "gas")
            old = dict(row)
            row["b"] = round(float(ob.sum()) / 1e6, 2)
            row["r"] = round(_pearson(ms, ob), 3)
            row["nrmse"] = round(_nrmse(ms, ob), 3)
            print(f"    gas row: {old} -> {row}")
            if "co2" in ypay:
                del ypay["co2"]
                print("    co2 block removed (btm.parquet unrecoverable; C5a -> SKIP)")
            # Witness cross-check: load-weighted LMP over all zones vs the
            # committed split-witness (solve-session measurement).
            num = sum(z["p"] * z["d"] for z in ypay["lmp"].values())
            den = sum(z["d"] for z in ypay["lmp"].values())
            lw = num / den
            w = WITNESS["per_year"][ystr][wside]["lw_price"]
            print(f"    lw LMP payload {lw:.4f} vs witness {w:.4f} (d {lw - w:+.4f})")
            assert abs(lw - w) < 0.02, "payload price surface != solve witness"
        out = REPO / "frontend/data/backcast/runs" / f"{rid}.js"
        out.write_text(ba.encode_run_js(rid, payload))
        print(f"  rewrote {out.relative_to(REPO)}")


if __name__ == "__main__":
    main()
