"""nyiso-247 G-C — the CC_REGULAR class MW-weighted loading-share comparator.

The PRECOMMIT's G-C bar is stated RELATIVE to the keeper and is measured "by the
identical construction on both legs from each run's own committed per-plant
hourly loading series" — i.e. the registered payload's ``plants[*].m``, which
``render_calibration_html._b64(100 x mw / cap)`` writes as integer loading
percent. Reading BOTH legs out of that one encoder is what makes the comparison
apples-to-apples: the keeper bundle carries no ``dispatch/`` (it is committed
slim), so its per-plant loading exists nowhere else.

Bins are nyiso-195's ten 10-pp bins; the reported statistic is bin [80, 90).
Per-plant capacity is recovered from the pair the payload already carries,
``cap = m_ann x 1e6 / (sum(L) / 100)``, so no fleet capacity is assumed.

Usage:  nyiso247_loading_shape.py <run-id> [<run-id> ...]
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
RUNS = REPO / "frontend" / "data" / "backcast" / "runs"
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
KLASS = "CC_REGULAR"
CAMPD_REFERENCE_80_90 = 16.5  # nyiso-195, committed


def payload(run_id: str) -> dict:
    """Decode a registered run payload (gzip+base64 inside a JS assignment)."""
    src = (RUNS / f"{run_id}.js").read_text()
    blob = re.search(r'"(H4sI[^"]+)"', src).group(1)
    return json.loads(gzip.decompress(base64.b64decode(blob)))


def class_plant_codes(year: int) -> set[str]:
    """Plant codes the fleet assigns to KLASS — the payload carries no class."""
    z = np.load(CACHE / f"{year}.npz", allow_pickle=False)
    grp, code = z["gen_plant_group"], z["gen_plant_code"]
    return {str(c) for c, g in zip(code, grp) if str(g) == KLASS}


def shares(run_id: str, year: int) -> dict | None:
    """Class MW-weighted loading-bin shares (%) for one run-year."""
    yr = payload(run_id)["years"].get(str(year))
    if yr is None:
        return None
    plants, codes = yr["plants"], class_plant_codes(year)
    binned = np.zeros(10)
    total = 0.0
    n = 0
    for code in sorted(codes):
        rec = plants.get(f"{code}:{KLASS}") or plants.get(code)
        if rec is None:
            continue
        load = np.frombuffer(base64.b64decode(rec["m"]), dtype=np.uint8).astype(float)
        tot_l = load.sum()
        if tot_l <= 0:
            continue
        energy = float(rec["m_ann"]) * 1e6  # MWh
        mw = energy * load / tot_l  # cap cancels; MWh per hour
        idx = np.clip((load // 10).astype(int), 0, 9)
        binned += np.bincount(idx, weights=mw, minlength=10)
        total += mw.sum()
        n += 1
    if total <= 0:
        return None
    pct = 100.0 * binned / total
    return {
        "plants": n,
        "energy_twh": round(total / 1e6, 4),
        "bins_0_100_pct": [round(float(x), 1) for x in pct],
        "share_80_90_pct": round(float(pct[8]), 2),
        "share_90_100_pct": round(float(pct[9]), 2),
    }


def main() -> None:
    out: dict = {"class": KLASS, "campd_reference_80_90_pct": CAMPD_REFERENCE_80_90, "runs": {}}
    for run_id in sys.argv[1:]:
        out["runs"][run_id] = {
            str(y): shares(run_id, y) for y in (2022, 2023, 2024, 2025)
        }
    print(json.dumps(out, indent=1))
    dst = REPO / "results" / "calibration" / "_nyiso247_loading_shape.json"
    dst.write_text(json.dumps(out, indent=1) + "\n")
    print("wrote", dst, file=sys.stderr)


if __name__ == "__main__":
    main()
