"""NYISO-NEXT (ZERO LP): score the arm against the keeper's committed bundle, per year.

Reads only committed artifacts: ``scripts/calibration_verdict.py --json`` records for both
runs, the two run payloads (per-plant model TWh, ``lmpDeltaHr``), and the NYISO bench parts
(EIA-923 per plant). Reports per year: C1 (key classes), C3a, C3b, C3c, C4, C8; ST_GAS TWh vs
EIA-923 by zone and by plant; hourly price bias / MAE vs RT (ISO simple mean). Writes
``results/calibration/_nyisonext_compare.json``.

Usage::

    python3 scripts/probes/nyisonext_compare.py \\
        --pair 2026-09-25-nyiso-stgas-ldc-leg 2026-09-26-nyisonext-floor-layup-span
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CRIT = (
    "fuelmix",
    "price_mean",
    "price_shape",
    "price_tail",
    "dispatch_corr",
    "forced_share",
)
C1_KEYS = ("ST_GAS", "CC_REGULAR", "CC_CHP", "CT_PEAKER")


def _payload(rid: str) -> dict:
    """Decode a gzip+base64 run payload."""
    s = (REPO / f"frontend/data/backcast/runs/{rid}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))


def _verdict(rid: str) -> dict:
    """calibration_verdict.py --json for one run."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            rid,
            "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=REPO,
    ).stdout
    return json.loads(out)


def _records(v: dict) -> dict:
    """{(criterion, key, year): record}."""
    out = {}
    for c in CRIT:
        for r in (v["criteria"].get(c) or {}).get("records") or []:
            out[(c, str(r.get("key")), int(r["year"]))] = r
    return out


def _price(pay_year: dict) -> tuple[float, float] | None:
    """ISO simple-mean hourly price bias / MAE vs RT from ``lmpDeltaHr``.

    The payload carries the hourly (model - RT) ISO simple-mean delta as a base64
    little-endian int16 series in whole $/MWh.
    """
    d = pay_year.get("lmpDeltaHr")
    if not d:
        return None
    m = np.frombuffer(base64.b64decode(d), "<i2").astype(float)
    return round(float(m.mean()), 2), round(float(np.abs(m).mean()), 2)


def main() -> None:
    """Compare two registered runs year by year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=2, required=True, metavar=("KEEPER", "ARM"))
    ap.add_argument(
        "--out", default=str(REPO / "results/calibration/_nyisonext_compare.json")
    )
    a = ap.parse_args()
    runs = {}
    for rid in a.pair:
        v = _verdict(rid)
        runs[rid] = {
            "det": v["determination"],
            "rec": _records(v),
            "pay": _payload(rid),
        }
    k, x = a.pair
    years = sorted({int(y) for y in runs[x]["pay"]["years"]})
    res: dict = {"determination": {r: runs[r]["det"] for r in a.pair}, "years": {}}
    for y in years:
        bench = json.loads(
            gzip.open(REPO / f"frontend/data/backcast/bench/NYISO/{y}.json.gz").read()
        )["bench"]["plants"]
        row: dict = {"criteria": {}, "stgas_zone": {}, "stgas_plant": {}}
        for (c, key, yy), r in runs[x]["rec"].items():
            if yy != y or (c == "fuelmix" and key not in C1_KEYS):
                continue
            kr = runs[k]["rec"].get((c, key, yy), {})
            row["criteria"][f"{c}:{key}"] = {
                "keeper": [kr.get("magnitude") or kr.get("model"), kr.get("status")],
                "arm": [r.get("magnitude") or r.get("model"), r.get("status")],
            }
        zone = defaultdict(lambda: [0.0, 0.0, 0.0])
        for key, bp in bench.items():
            if bp.get("group") != "ST_GAS":
                continue
            mk = runs[k]["pay"]["years"].get(str(y), {}).get("plants", {}).get(key)
            mx = runs[x]["pay"]["years"][str(y)]["plants"].get(key)
            if mk is None or mx is None:
                continue
            z = zone[bp["zone"]]
            z[0] += mk["m_ann"]
            z[1] += mx["m_ann"]
            z[2] += bp["e_ann"]
            if max(mk["m_ann"], bp["e_ann"]) > 0.3:
                row["stgas_plant"][f"{key} {bp['name']}"] = [
                    round(mk["m_ann"], 2),
                    round(mx["m_ann"], 2),
                    round(bp["e_ann"], 2),
                ]
        row["stgas_zone"] = {z: [round(v, 2) for v in vals] for z, vals in zone.items()}
        row["price_bias_mae"] = {
            "keeper": _price(runs[k]["pay"]["years"].get(str(y), {})),
            "arm": _price(runs[x]["pay"]["years"][str(y)]),
        }
        res["years"][str(y)] = row
    Path(a.out).write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res["determination"]))
    for y, row in res["years"].items():
        print(f"== {y}")
        for c, v in sorted(row["criteria"].items()):
            print(f"  {c:28s} {v['keeper']} -> {v['arm']}")
        print("  ST_GAS zone [keeper, arm, 923]:", row["stgas_zone"])
        print("  ST_GAS plant:", row["stgas_plant"])
        print("  price bias/MAE:", row["price_bias_mae"])


if __name__ == "__main__":
    main()
