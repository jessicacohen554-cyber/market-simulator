"""miso-175 — the PRE-SOLVE ENGINE-FROZEN instrument for the hour-key A/B.

READ-ONLY, NO LP. Freezes, BEFORE any solve, the exact per-seam hourly cap
arrays the control and arm will consume — built through the PRODUCTION loader
(``measured_seam_import_envelope``) at HEAD, never a re-derivation (the
miso-173 discipline: offline instruments are blind to composition, so what is
frozen is the engine's own input surface, and the A/B gates score the solve
against it).

Frozen per (year × direction × seam), for BOTH key conventions:
  * sha256 of the exact float64 cap array (M-1 scores digest equality of the
    regenerated arrays at scoring time — same loader, same committed parquet);
  * annual mean cap (GW), mean/max |Δ| between conventions, count of hours
    with Δ ≠ 0;
  * SIGNED window deltas mean(corrected − legacy) for the pre-registered
    windows (annual, Jun–Sep, Jun–Sep evening HE18–22, Jun–Sep morning
    HE07–12) — the engine-frozen DIRECTION predictions M-2(b) gates on.

Run:  python3 scripts/probes/_miso175_hour_key_instrument.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402

CAL = ROOT / "results" / "calibration"
OUT = CAL / "_miso175_hour_key_instrument.json"

YEARS = (2023, 2024, 2025)
HOURS = 8760
# Model fixed non-leap calendar month starts (hour-of-year).
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[8 + 1])  # Jun 1 .. Sep 30 inclusive


def _windows() -> dict[str, np.ndarray]:
    """The pre-registered scoring windows as boolean masks over the 8760 clock."""
    h = np.arange(HOURS)
    hod = h % 24
    summer = (h >= SUMMER[0]) & (h < SUMMER[1])
    return {
        "annual": np.ones(HOURS, dtype=bool),
        "summer": summer,
        # HE18-22 = hour-beginning 17:00-21:00 local standard.
        "summer_evening_he18_22": summer & (hod >= 17) & (hod <= 21),
        "summer_morning_he07_12": summer & (hod >= 6) & (hod <= 11),
    }


def main() -> None:
    """Freeze both conventions' cap arrays and the signed window deltas."""
    win = _windows()
    rec: dict = {
        "session": "miso-175",
        "frozen_before_solve": True,
        "loader": "market_sim.data.eia930.measured_seam_import_envelope (PRODUCTION)",
        "windows": {k: int(v.sum()) for k, v in win.items()},
        "arrays": {},
    }
    for y in YEARS:
        for direction in ("import", "export"):
            legacy = measured_seam_import_envelope("MISO", y, HOURS, None, direction) or {}
            fixed = (
                measured_seam_import_envelope(
                    "MISO", y, HOURS, None, direction, hour_ending_key=True
                )
                or {}
            )
            for seam in legacy:
                lo, hi = legacy[seam], fixed.get(seam)
                if hi is None:
                    continue
                d = hi - lo
                entry = {
                    "sha256_legacy": hashlib.sha256(
                        np.ascontiguousarray(lo, dtype=np.float64).tobytes()
                    ).hexdigest(),
                    "sha256_corrected": hashlib.sha256(
                        np.ascontiguousarray(hi, dtype=np.float64).tobytes()
                    ).hexdigest(),
                    "annual_mean_legacy_gw": float(np.mean(lo)) / 1000,
                    "annual_mean_corrected_gw": float(np.mean(hi)) / 1000,
                    "mean_abs_delta_mw": float(np.mean(np.abs(d))),
                    "max_abs_delta_mw": float(np.max(np.abs(d))),
                    "hours_delta_nonzero": int(np.sum(d != 0.0)),
                    "window_mean_delta_mw": {
                        k: float(np.mean(d[m])) for k, m in win.items()
                    },
                }
                rec["arrays"][f"{y}_{direction}_{seam}"] = entry

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}\n")
    print(f"{'array':26s} {'meanL':>7s} {'meanC':>7s} {'m|d|':>6s} "
          f"{'ann_d':>7s} {'sum_d':>7s} {'eve_d':>7s} {'mor_d':>7s}")
    for k, e in rec["arrays"].items():
        w = e["window_mean_delta_mw"]
        print(f"{k:26s} {e['annual_mean_legacy_gw']*1000:7.0f} "
              f"{e['annual_mean_corrected_gw']*1000:7.0f} {e['mean_abs_delta_mw']:6.1f} "
              f"{w['annual']:+7.1f} {w['summer']:+7.1f} "
              f"{w['summer_evening_he18_22']:+7.1f} {w['summer_morning_he07_12']:+7.1f}")


if __name__ == "__main__":
    main()
