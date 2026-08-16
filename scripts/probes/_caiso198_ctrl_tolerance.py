"""caiso-198 — control reproduction check against the committed caiso-197 keeper.

Integration-protocol §3 (ratified tolerance) on the caiso-197 base
(`PRECHECK-caiso198-desertstar-extract-2026-08-16.md` §4 G-CTRL): the control
`caiso198_f0_control` must reproduce the committed keeper `caiso197_w2_r5`
within per-year |ΔC3a| ≤ 0.1 pp and |ΔC3b| ≤ 0.005, with the control delta
quoted as the NOISE FLOOR at full precision BEFORE any treated delta is read.

Bit-zero is the observed CAISO norm (caiso-184/188/196/197 G-CTRL), so the
primary instrument is the same one those sessions used: max |Δ| over every
zone-hour of ``hourly/system_<year>.parquet`` (prices included) and every
class-hour of ``hourly/class_hourly_<year>.parquet``. When both are exactly
0.0 in a year, ΔC3a = ΔC3b = 0 for that year by construction and no scorer
is consulted. A nonzero delta is reported at full precision; the C3a/C3b
projection onto the tolerance is then owed by the session before any arm
result is read (a nonzero-but-in-tolerance delta is the noise floor; outside
tolerance is a stop-the-line finding about the head — no arm solves).

No price series is READ AS EVIDENCE here: the comparison is a reproduction
identity check between two model artifacts (the committed keeper's own
sidecars and their replay), not a fit measurement. Usage::

    python scripts/probes/_caiso198_ctrl_tolerance.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results" / "calibration" / "caiso197_w2_r5"
CONTROL = REPO / "results" / "calibration" / "caiso198_f0_control"
YEARS = [2023, 2024, 2025]
OUT = REPO / "results" / "calibration" / "_caiso198_ctrl_tolerance.json"


def _max_abs_delta(a_path: Path, b_path: Path) -> dict:
    """Max |Δ| per numeric column between two parquet sidecars (row-aligned)."""
    a = pq.read_table(a_path)
    b = pq.read_table(b_path)
    if a.num_rows != b.num_rows:
        return {"rows": f"MISMATCH {a.num_rows} vs {b.num_rows}"}
    out: dict[str, float] = {}
    for name in a.column_names:
        if name not in b.column_names:
            out[name] = float("nan")
            continue
        av = a.column(name).to_numpy(zero_copy_only=False)
        bv = b.column(name).to_numpy(zero_copy_only=False)
        if av.dtype.kind in "fiu" and bv.dtype.kind in "fiu":
            out[name] = float(
                np.max(np.abs(av.astype(float) - bv.astype(float)))
            )
    return out


def main() -> None:
    """Compare the control's hourly sidecars to the keeper's, per year."""
    result: dict = {
        "keeper": KEEPER.name,
        "control": CONTROL.name,
        "tolerance": {"dC3a_pp": 0.1, "dC3b": 0.005},
        "per_year": {},
    }
    bit_zero_all = True
    for year in YEARS:
        yr: dict = {}
        for kind in ("system", "class_hourly"):
            k = KEEPER / "hourly" / f"{kind}_{year}.parquet"
            c = CONTROL / "hourly" / f"{kind}_{year}.parquet"
            if not k.exists() or not c.exists():
                yr[kind] = {"missing": [str(p) for p in (k, c) if not p.exists()]}
                bit_zero_all = False
                continue
            deltas = _max_abs_delta(k, c)
            numeric = [v for v in deltas.values() if isinstance(v, float)]
            worst = max(numeric) if numeric else float("nan")
            yr[kind] = {
                "max_abs_delta_any_column": worst,
                "worst_columns": {
                    n: v
                    for n, v in sorted(
                        ((n, v) for n, v in deltas.items() if isinstance(v, float)),
                        key=lambda kv: -kv[1],
                    )[:4]
                },
            }
            if not (worst == 0.0):
                bit_zero_all = False
        result["per_year"][year] = yr
    result["bit_zero_all_years"] = bit_zero_all
    result["noise_floor_statement"] = (
        "BIT-ZERO: max |Δ| = 0.0 over every zone-hour (system, prices included) "
        "and every class-hour (class_hourly) of all three years — ΔC3a = 0.0 pp "
        "and ΔC3b = 0.000 identically; the ratified tolerance is met with a "
        "noise floor of exactly zero, quoted before any treated delta was read."
        if bit_zero_all
        else "NON-ZERO control delta — quote per-column maxima above at full "
        "precision and project onto |ΔC3a| ≤ 0.1 pp / |ΔC3b| ≤ 0.005 BEFORE "
        "reading any arm result; outside tolerance ⇒ stop-the-line, no arm."
    )
    OUT.write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    sys.exit(0 if bit_zero_all else 2)


if __name__ == "__main__":
    main()
