"""Compare two bundles' committed ``hourly/`` sidecars for bit-identity.

The pjm-169 F2 ARM verification (rule 29 / the pjm-168 H6 re-check): a keeper
replay solved with ``pjm_interface_feed_admissibility_gate`` ARMED must be
bit-identical to the keeper's own committed sidecars for every in-sample year,
because the zero-LP admissibility test clears every consumed series in
2023-2025 and the gate therefore takes the identical branch.

pjm-168 proved this through the ``--set`` override channel. This session arms
the mechanism at a DIFFERENT site (``pipeline.backcast_config``), so the proof
is re-run through the site that actually ships.

Reports exact frame equality and max absolute numeric delta per sidecar. No LP
is constructed and nothing is written.

Usage:
    python scripts/probes/_pjm169_sidecar_identity.py REF_BUNDLE ARM_BUNDLE --year 2023
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

#: The sidecar families every solve since 2026-08-03 writes (CLAUDE.md rule 15).
FAMILIES = ("class_hourly", "system", "reserve_family", "storage")


def compare(ref: Path, arm: Path, year: int) -> tuple[list[dict], bool]:
    """Return per-sidecar comparison rows and whether every one is identical.

    Args:
        ref: reference bundle directory (the committed keeper).
        arm: bundle directory solved with the mechanism armed.
        year: solve year whose sidecars to compare.

    Returns:
        ``(rows, all_identical)``.
    """
    rows: list[dict] = []
    ok = True
    for fam in FAMILIES:
        rp = ref / "hourly" / f"{fam}_{year}.parquet"
        ap = arm / "hourly" / f"{fam}_{year}.parquet"
        if not rp.exists() or not ap.exists():
            rows.append({"sidecar": f"{fam}_{year}", "status": "MISSING",
                         "detail": f"ref={rp.exists()} arm={ap.exists()}"})
            ok = False
            continue
        a, b = pd.read_parquet(rp), pd.read_parquet(ap)
        if a.shape != b.shape or list(a.columns) != list(b.columns):
            rows.append({"sidecar": f"{fam}_{year}", "status": "SHAPE-DIFF",
                         "detail": f"{a.shape}{list(a.columns)} vs {b.shape}{list(b.columns)}"})
            ok = False
            continue
        equal = a.equals(b)
        num = a.select_dtypes(include=[np.number]).columns
        delta = (
            float(np.nanmax(np.abs(a[num].to_numpy() - b[num].to_numpy())))
            if len(num)
            else 0.0
        )
        rows.append({
            "sidecar": f"{fam}_{year}",
            "status": "IDENTICAL" if (equal and delta == 0.0) else "DIFFERS",
            "detail": f"{a.shape[0]:,} x {a.shape[1]}  exact_equal={equal}  max|delta|={delta:g}",
        })
        ok = ok and equal and delta == 0.0
    return rows, ok


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("ref")
    ap.add_argument("arm")
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()

    rows, ok = compare(Path(args.ref), Path(args.arm), args.year)
    width = max(len(r["sidecar"]) for r in rows)
    for r in rows:
        print(f"{r['sidecar']:<{width}}  {r['status']:<10}  {r['detail']}")
    print("\nVERDICT:", "BIT-IDENTICAL" if ok else "NOT IDENTICAL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
