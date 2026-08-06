"""FFR-7B Arm 1 paired-control comparator (Addendum D).

Compares a control bundle (keeper recipe at branch base) against the arm
bundle (same recipe at the Arm-1 commits) file-by-file: sha256 over every
parquet payload, plus numeric max-abs-delta on system hourly prices and
class dispatch when hashes differ. Zero expected delta: the corrected
constants are unreachable in a backcast (rps_enabled=False).

Usage: python ffr7b_compare.py <ctrl_bundle> <arm_bundle> <out_json>
"""

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd


def file_hashes(bundle: Path) -> dict:
    out = {}
    for p in sorted(bundle.rglob("*.parquet")):
        out[str(p.relative_to(bundle))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def numeric_delta(a: Path, b: Path) -> float:
    da, db = pd.read_parquet(a), pd.read_parquet(b)
    if da.shape != db.shape:
        return float("inf")
    na = da.select_dtypes("number").to_numpy(dtype=float)
    nb = db.select_dtypes("number").to_numpy(dtype=float)
    if na.shape != nb.shape:
        return float("inf")
    import numpy as np

    return float(np.nanmax(np.abs(na - nb))) if na.size else 0.0


def main() -> None:
    ctrl, arm, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    hc, ha = file_hashes(ctrl), file_hashes(arm)
    keys = sorted(set(hc) | set(ha))
    rows, n_identical = [], 0
    for k in keys:
        if k not in hc or k not in ha:
            rows.append({"file": k, "status": "missing", "max_abs_delta": None})
            continue
        if hc[k] == ha[k]:
            n_identical += 1
            continue
        rows.append(
            {
                "file": k,
                "status": "differs",
                "max_abs_delta": numeric_delta(ctrl / k, arm / k),
            }
        )
    result = {
        "control": str(ctrl),
        "arm": str(arm),
        "n_parquet_compared": len(keys),
        "n_byte_identical": n_identical,
        "n_differing_or_missing": len(rows),
        "differing": rows,
        "verdict": "BYTE-IDENTICAL" if not rows else "DIFFERS",
    }
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("n_parquet_compared", "n_byte_identical", "verdict")}))
    if rows:
        for r in rows[:10]:
            print(r)


if __name__ == "__main__":
    main()
