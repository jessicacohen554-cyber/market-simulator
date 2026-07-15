"""pjm-112 BUILD-TIME provenance check (gate #4, no-LP) — do the two derived PJM
unit-availability extracts demonstrably target the measured C3c summer phantom
BEFORE the LP ever runs?

Adapts the arithmetic of ``_pjm_c3c_summer_tail_decomp.py --section derivers``
to read the DERIVED CSVs (short full-stops + unit-grain partial plateaus)
instead of simulating the deriver rules. For each of the 22 actual 2025 summer
DA-tail hours (DA > $200 in Jun/Jul/Aug/Sep — the Jun 23-25 and Jul 28-29 heat
events) it sums the capacity each extract REMOVES from availability in that hour:

  * short  : ``unit_capacity_mw``                         (a full stop)
  * partial: ``(1 - derate_factor) x unit_capacity_mw``   (a plateau derate)

Gate (diagnosis §8 item 4): the COMBINED mean over the 22 hours must be
>= 800 MW — i.e. the mechanism recovers a material fraction of the measured
+3.0 GW coal phantom in the exact hours the tail lives. Reports both the raw
per-unit sum (the probe's "extract arithmetic") and the plant-clipped
aggregation the fleet overlay actually applies (unit-capacity share, concurrent
units summed, clipped at full plant derate). PASS/FAIL on the raw sum, the
figure the pre-committed gate was set against.

Usage: .venv/bin/python scripts/probes/_pjm112_provenance_check.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_PJM.parquet"
SHORT_CSV = REPO / "data/raw/campd-unit-outages-short-PJM.csv"
PARTIAL_CSV = REPO / "data/raw/campd-partial-outages-PJM.csv"

HOURS = 8760
YEAR = 2025
TAIL_THR = 200.0
GATE_MW = 800.0
_MDAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)  # non-leap (2025)
MONTH = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)


def _summer_tail_hours() -> np.ndarray:
    """The 22 actual 2025 summer DA-tail hour indices (DA > $200, Jun-Sep)."""
    a = pd.read_parquet(ACTUAL_LMP)
    a = a[a.year == YEAR].sort_values("hour")
    da = a["da"].to_numpy()[:HOURS]
    return np.where((da > TAIL_THR) & np.isin(MONTH, (6, 7, 8, 9)))[0]


def _window_hours(start: str, end: str) -> tuple[int, int]:
    """Day-granular [lo, hi) hour range on the 2025 clock for a date window."""
    base = pd.Timestamp(f"{YEAR}-01-01")
    lo = int((pd.Timestamp(start) - base).total_seconds() // 3600)
    hi = int((pd.Timestamp(end) + pd.Timedelta(days=1) - base).total_seconds() // 3600)
    return max(0, lo), min(HOURS, hi)


def _removed_series(csv: Path, partial: bool) -> tuple[np.ndarray, np.ndarray]:
    """Return (raw_sum, plant_clipped) per-hour removed-MW arrays for one extract.

    raw_sum      : Σ over rows of removed MW covering each hour (the probe basis).
    plant_clipped: the same but each (plant, group)'s summed removed MW is
                   clipped at the plant's own capacity before adding to the
                   total — the fleet overlay's actual effect (clip at full).
    """
    raw = np.zeros(HOURS)
    per_bin: dict[tuple[int, str], tuple[np.ndarray, float]] = {}
    if not csv.exists():
        return raw, raw
    df = pd.read_csv(csv)
    df = df[pd.to_datetime(df.outage_start).dt.year == YEAR]
    for r in df.itertuples(index=False):
        ucap = float(r.unit_capacity_mw)
        removed = ucap * (1.0 - float(r.derate_factor)) if partial else ucap
        if removed <= 0:
            continue
        lo, hi = _window_hours(r.outage_start, r.outage_end)
        if hi <= lo:
            continue
        raw[lo:hi] += removed
        key = (int(r.facility_id), str(r.plant_group))
        arr, pcap = per_bin.setdefault(
            key, (np.zeros(HOURS), float(r.plant_capacity_mw))
        )
        arr[lo:hi] += removed
    clipped = np.zeros(HOURS)
    for arr, pcap in per_bin.values():
        clipped += np.minimum(arr, pcap) if pcap > 0 else arr
    return raw, clipped


def main() -> int:
    tail = _summer_tail_hours()
    print(f"2025 summer DA-tail hours (DA > ${TAIL_THR:.0f}, Jun-Sep): {len(tail)}")
    if len(tail) == 0:
        print("FAIL: no summer tail hours found")
        return 1
    s_raw, s_clip = _removed_series(SHORT_CSV, partial=False)
    p_raw, p_clip = _removed_series(PARTIAL_CSV, partial=True)
    comb_raw = s_raw + p_raw
    comb_clip = s_clip + p_clip
    print("\nmean removed MW across the summer tail hours:")
    print(f"  short   (full stops)      raw {s_raw[tail].mean():7.0f}")
    print(f"  partial (plateaus)        raw {p_raw[tail].mean():7.0f}")
    print(
        f"  COMBINED                  raw {comb_raw[tail].mean():7.0f}"
        f"   plant-clipped {comb_clip[tail].mean():7.0f}"
    )
    gate_value = comb_raw[tail].mean()
    ok = gate_value >= GATE_MW
    print(
        f"\nGATE #4 (>= {GATE_MW:.0f} MW combined raw over 22 summer tail hours): "
        f"{'PASS' if ok else 'FAIL'} ({gate_value:.0f} MW)"
    )
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
