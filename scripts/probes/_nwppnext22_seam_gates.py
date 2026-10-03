"""NWPP-NEXT-22 result gates (a), (d), (e): seam signs and hourly r, the BC<->CA wheel, seam volume.

Reads each leg's committed ``flows.parquet`` (P1) and the measured EIA-930 seam legs through the
solve's own reader (``_nwppnext20_seam_phase0._measured``). Net flow is export-positive
(NWPP zone -> external zone). Optional second root: NEXT-21's legs, for the volume comparison.

Usage: PYTHONPATH=. python scripts/probes/_nwppnext22_seam_gates.py ROOT_PATTERN [NEXT21_PATTERN]
(e.g. ``results/calibration/nwppnext22_{y}``; ``{y}`` is the year)
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
sys.path.insert(0, "scripts/probes")

from _nwppnext20_seam_phase0 import _measured  # noqa: E402

YEARS = tuple(range(2019, 2026))
ZONES = {
    "CAISO_COI": "NWPP_ext_COI",
    "CAISO_NEVP": "NWPP_ext_NEVP",
    "WECC_CAN": "NWPP_ext_BC",
}


def seam_net(flows: Path) -> dict[str, np.ndarray]:
    """Export-positive hourly net flow per seam from a leg's P1 flows."""
    f = pd.read_parquet(flows)
    f = f[f["pass"] == "P1"]
    out = {}
    for seam, z in ZONES.items():
        into = (
            f[f["to_zone"] == z]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(8760))
            .fillna(0.0)
        )
        outof = (
            f[f["from_zone"] == z]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(8760))
            .fillna(0.0)
        )
        out[seam] = (into - outof).to_numpy()
    return out


def main() -> None:
    """Print the per-(seam, year) table and the wheel."""
    pat = sys.argv[1]
    pat21 = sys.argv[2] if len(sys.argv) > 2 else None
    rows = []
    for y in YEARS:
        flows = Path(pat.format(y=y)) / "flows.parquet"
        if not flows.exists():
            continue
        net = seam_net(flows)
        net21 = seam_net(Path(pat21.format(y=y)) / "flows.parquet") if pat21 else None
        meas = _measured(y)
        priced = ("CAISO_COI", "CAISO_NEVP") + (("WECC_CAN",) if y >= 2023 else ())
        for seam in priced:
            m = meas[seam]
            rows.append(
                dict(
                    year=y,
                    seam=seam,
                    model_TWh=round(net[seam].sum() / 1e6, 2),
                    next21_TWh=round(net21[seam].sum() / 1e6, 2) if net21 else None,
                    measured_TWh=round(float(np.nansum(m)) / 1e6, 2),
                    sign_ok=bool(np.sign(net[seam].sum()) == np.sign(np.nansum(m))),
                    r=round(float(pd.Series(net[seam]).corr(pd.Series(m))), 3),
                )
            )
        if y >= 2023:
            w = (net["CAISO_COI"] < 0) & (net["WECC_CAN"] > 0)
            mwh = np.minimum(-net["CAISO_COI"][w], net["WECC_CAN"][w]).sum()
            print(
                f"{y} wheel (COI import & BC export): {int(w.sum())} h, {mwh / 1e6:.2f} TWh"
            )
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))
    cols = (
        ["model_TWh", "next21_TWh", "measured_TWh"]
        if pat21
        else ["model_TWh", "measured_TWh"]
    )
    print(
        "\nsum of priced seams (TWh):\n"
        + df.groupby("year")[cols].sum().round(1).to_string()
    )


if __name__ == "__main__":
    main()
