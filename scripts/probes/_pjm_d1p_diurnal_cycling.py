"""D-1p — per-plant diurnal cycling metric (PJM), on verified clocks.

The class-level D-1 nets out per-plant shape errors (fleet profile_r
0.95-0.98 passes while individual cyclers are flat overnight where reality
two-shifts). D-1p makes the residual visible per plant, from committed
artifacts only (payload `m` hourly CF + bench `campd` hourly CF — CEMS is
stamped local STANDARD time, the model calendar, so no LMP-clock dependency).

Per CC_REGULAR plant (nameplate >= min_mw, complete CEMS, not CT-only):

  night_cf_m / night_cf_c   mean CF over h0-6, model vs CAMPD
  turndown_m / turndown_c   overnight turndown depth = 1 - (mean CF h0-6 /
                            mean CF h17-22); ~0 = flat through the night,
                            ~1 = full two-shift shutdown
  night_share               share of total |model-CAMPD| MWh accruing in h0-6
  phase                     diff-series best lag (hours; + = model early)

Clock caveats (2026-07 PJM phase audit): the model's 2023 demand input is 1 h
late and its 2024 wind/solar input is 1 h early (EIA-930 vintage defects), so
the *phase* column is only clean for 2025; the CF/turndown columns are
phase-robust in all years.

Usage: .venv/bin/python scripts/probes/_pjm_d1p_diurnal_cycling.py [run_id]
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

from _pjm2025_payload_lag import HOURS, best_lag, load_payload  # noqa: E402

BENCH_DIR = REPO / "frontend/data/backcast/bench/PJM"
HOD = np.arange(HOURS) % 24
NIGHT = HOD <= 6
EVE = (HOD >= 17) & (HOD <= 22)
MIN_MW = 500.0


def _dec(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8).astype(float) / 100.0


def d1p_rows(run_id: str, year: int) -> list[dict]:
    payload = load_payload(run_id)
    bench = json.loads(gzip.decompress((BENCH_DIR / f"{year}.json.gz").read_bytes()))
    bp = bench["bench"]["plants"]
    mp = payload["years"][str(year)]["plants"]
    rows = []
    for k, mv in mp.items():
        b = bp.get(k)
        if (
            not b
            or b.get("group") != "CC_REGULAR"
            or b.get("npl", 0) < MIN_MW
            or "campd" not in b
            or b.get("ct_only")
        ):
            continue
        m = _dec(mv["m"])[:HOURS]
        c = _dec(b["campd"])[:HOURS]
        if c.sum() == 0:
            continue
        ncf_m, ncf_c = m[NIGHT].mean(), c[NIGHT].mean()
        ecf_m, ecf_c = m[EVE].mean(), c[EVE].mean()
        td_m = 1 - ncf_m / ecf_m if ecf_m > 0.05 else np.nan
        td_c = 1 - ncf_c / ecf_c if ecf_c > 0.05 else np.nan
        adiff = np.abs(m - c)
        nshare = adiff[NIGHT].sum() / adiff.sum() if adiff.sum() > 0 else np.nan
        dm = np.append(np.diff(m), np.nan)
        dc = np.append(np.diff(c), np.nan)
        r = best_lag(dm, dc, np.ones(HOURS, dtype=bool))
        rows.append(
            {
                "plant": b["name"][:24],
                "zone": b["zone"].replace("PJM_", ""),
                "npl": b["npl"],
                "night_cf_m": ncf_m,
                "night_cf_c": ncf_c,
                "turndown_m": td_m,
                "turndown_c": td_c,
                "night_share": nshare,
                "phase": r["best"],
            }
        )
    rows.sort(key=lambda r: r["night_cf_m"] - r["night_cf_c"], reverse=True)
    return rows


def main() -> None:
    run_id = sys.argv[1] if len(sys.argv) > 1 else "2026-07-14-pjm-110-bench-hygiene"
    for year in (2023, 2024, 2025):
        rows = d1p_rows(run_id, year)
        flat = [
            r
            for r in rows
            if np.isfinite(r["turndown_m"])
            and np.isfinite(r["turndown_c"])
            and r["turndown_c"] - r["turndown_m"] > 0.15
        ]
        print(
            f"===== {year}: {len(rows)} CC plants >= {MIN_MW:.0f} MW;"
            f" {len(flat)} flat-overnight offenders"
            f" (model turndown 15+ pts shallower than CEMS)"
        )
        print(
            f"{'plant':24s} {'zone':11s} {'nCF m/c':>12s} {'turndn m/c':>12s}"
            f" {'nightshr':>8s} {'phase':>5s}"
        )
        for r in rows[:10]:
            print(
                f"{r['plant']:24s} {r['zone']:11s}"
                f" {r['night_cf_m']:.2f}/{r['night_cf_c']:.2f} "
                f" {r['turndown_m']:6.2f}/{r['turndown_c']:.2f}"
                f" {r['night_share']:8.2f} {r['phase']:+5d}"
            )


if __name__ == "__main__":
    main()
