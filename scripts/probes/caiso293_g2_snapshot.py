"""G-2 half: snapshot the keeper's composed floor arrays for a bit-exact diff.

Run ONCE on the working tree with caiso-293's change present (gate OFF, its
default) and ONCE on the pre-change tree, then compare the two ``.npz`` files.
That is a true two-version comparison; the in-process "reference" the first
draft of ``caiso293_gates.py`` used was MIS-SPECIFIED — it compared the
POST-clip ``min_gen`` against the raw per-unit ``pmin_mw``, but
``fleet/arrays.py`` clips every floor to ``pmax x availability`` and four later
floor blocks legitimately overwrite the same cells, so it counted correct
behaviour as a diff.

Usage:
    PYTHONPATH=.:src python scripts/probes/caiso293_g2_snapshot.py <out.npz>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib.bundle_fleet import ensure_probe_path, reconstruct_bundle_fleet  # noqa: E402

ensure_probe_path()

BUNDLE = REPO / "results/calibration/xiso8_leftedge_span"
YEARS = (2022, 2023, 2024, 2025)


def main() -> None:
    out = Path(sys.argv[1])
    blobs: dict[str, np.ndarray] = {}
    for year in YEARS:
        state, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
        arrays = state["fleet_arrays"]
        gens = state["fleet"]
        gens = getattr(gens, "generators", gens)
        blobs[f"min_gen_{year}"] = np.asarray(arrays.min_gen, dtype=np.float64)
        blobs[f"mech_{year}"] = np.asarray(arrays.min_gen_mechanism)
        blobs[f"chp_floor_{year}"] = np.array(
            [float(getattr(g, "chp_grid_pmin_mw", 0.0) or 0.0) for g in gens],
            dtype=np.float64,
        )
        blobs[f"pmax_{year}"] = np.asarray(arrays.pmax, dtype=np.float64)
        print(
            f"{year}: {blobs[f'min_gen_{year}'].shape} rows, "
            f"chp-floored {int((blobs[f'chp_floor_{year}'] > 0).sum())}, "
            f"min_gen sum {blobs[f'min_gen_{year}'].sum():,.6f}"
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out, **blobs)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
