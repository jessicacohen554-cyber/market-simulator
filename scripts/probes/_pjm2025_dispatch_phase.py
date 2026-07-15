"""Lead-0 probe (part 7) — is the model's DISPATCH clock early too?

Per-plant hourly model dispatch (pjm-110 payload, uint8 CF%) vs CAMPD hourly
gross (bench file, same encoding; CEMS stamps local STANDARD time = the model
calendar). For the largest gas CC plants (complete CEMS reporters), compute
the differenced-series best lag and pooled daily on/off-edge offsets per year.

Reading: dispatch best-lag +1 in 2024/2025 but ~0 in 2023 => the LP consumed
a phase-shifted RHS (whole model early — same carrier as the price). Dispatch
aligned everywhere => the price layer alone is shifted (payload/dual
extraction). Dispatch FOLLOWS the input's own per-year phase (late 2023) =>
the LP is faithful to its input and the price lead is mechanism-level.
"""

from __future__ import annotations

import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _pjm2025_payload_lag import (  # noqa: E402
    HOURS,
    best_lag,
    load_payload,
)

BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"

# Large CC plants with complete CEMS (July diagnosis §0 table; CT-only
# reporters 55337/55976/55710 excluded).
PLANTS = {
    62949: "Guernsey",
    59913: "Greensville",
    55524: "York Energy",
    55736: "Hanging Rock",
    60356: "South Field",
    58260: "Brunswick Co",
    55939: "Warren Co",
    55502: "Lawrenceburg",
    55297: "New Covert",
    62926: "Jackson Gen",
    63931: "CPV Three Rivers",
    60368: "Hummel",
}


def _dec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float)


def main() -> None:
    payload = load_payload("2026-07-14-pjm-110-bench-hygiene")
    for year in (2023, 2024, 2025):
        bench = json.loads(
            gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes())
        )
        bp = bench["bench"]["plants"]
        mp = payload["years"][str(year)]["plants"]
        lags_by_plant = {}
        for pid, name in PLANTS.items():
            k = str(pid)
            if k not in mp or k not in bp or "campd" not in bp[k]:
                continue
            m = _dec(mp[k]["m"])[:HOURS]
            c = _dec(bp[k]["campd"])[:HOURS]
            if c.sum() == 0 or m.std() == 0:
                continue
            dm = np.append(np.diff(m), np.nan)
            dc = np.append(np.diff(c), np.nan)
            r = best_lag(dm, dc, np.ones(HOURS, dtype=bool))
            lags_by_plant[name] = (
                r["best"],
                r.get(-1, np.nan),
                r.get(0, np.nan),
                r.get(1, np.nan),
            )
        print(f"===== {year} (diff-series best lag, model vs CAMPD)")
        for name, (b, rm1, r0, rp1) in lags_by_plant.items():
            print(f"  {name:16s} best={b:+d}  -1:{rm1:.3f} 0:{r0:.3f} +1:{rp1:.3f}")
        votes = [v[0] for v in lags_by_plant.values()]
        print(
            "  vote: "
            + " ".join(f"{lag:+d}:{votes.count(lag)}" for lag in sorted(set(votes)))
        )


if __name__ == "__main__":
    main()
