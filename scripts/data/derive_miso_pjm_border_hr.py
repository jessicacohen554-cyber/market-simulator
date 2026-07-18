"""Derive MISO's eastern PJM seam heat rate re-anchored to the WESTERN border.

The reference-price interface prices the MISO->PJM seam as
``(henry_hub + gas_basis) x marginal_heat_rate x load_shape``, with the per-year
``hr_by_year`` (``scripts/data/derive_neighbor_hr_by_year.py --iso MISO``) anchored to
PJM's SYSTEM-average realized RT LMP. But the MISO-Central seam physically clears
against PJM's WESTERN border zones (ComEd / AEP-Ohio / ATSI), which price below
PJM's eastern-load-weighted system average, so the system anchor over-prices the
import and MISO under-imports over its largest seam.

This re-anchors the seam to the equal-weight mean of the three MISO-facing PJM
generator hubs (CHICAGO GEN / AEP GEN / ATSI GEN — the model's declared
``border_zones``), measured from the PJM RT LMP extract, as a per-year ratio on
the existing system anchor::

    ratio[y]      = mean(border-hub RT LMP[y]) / mean(PJM system RT LMP[y])
    HR_border[y]  = HR_system[y] x ratio[y]

This is the import mirror of the pjm58 NYISO-WEST re-anchor. It is a measured
neighbor price-formation input (claude.md rule #12 — measured over estimate) and
is blind to MISO's own interchange (rule #11 — it reads only PJM zonal LMP, never
MISO flow). Forward-reproducible: each year's ratio regenerates from that year's
measured PJM zonal LMP and responds to changed border congestion.

Run::

    python scripts/data/derive_miso_pjm_border_hr.py

and paste the emitted ``MISO_PJM_BORDER_HR_BY_YEAR`` block into constants.py.
"""

from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS

# The three MISO-facing PJM generator hubs (ComEd / AEP-Ohio / ATSI), matching the
# PJM-side border zones the MISO-Central seam clears against.
_BORDER_HUBS: tuple[str, ...] = ("CHICAGO GEN HUB", "AEP GEN HUB", "ATSI GEN HUB")


def _system_mean_lmp(year: int) -> float | None:
    """PJM realized annual-mean system RT LMP ($/MWh) — the current anchor base."""
    path = paths.CALIBRATION_DIR / "actual_lmp_hourly_PJM.parquet"
    if not path.is_file():
        return None
    df = pd.read_parquet(path)
    rows = df[df["year"] == year]
    if rows.empty or "rt" not in rows.columns:
        return None
    return float(np.nanmean(rows["rt"].to_numpy(dtype=float)))


def _border_mean_lmp(year: int) -> float | None:
    """Equal-weight mean of the MISO-facing PJM border generator hubs' RT LMP."""
    path = paths.RAW_DIR / "lmp-data" / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not path.is_file():
        return None
    df = pd.read_csv(
        path, usecols=["datetime_beginning_ept", "pnode_name", "total_lmp_rt"]
    )
    ept = pd.to_datetime(df["datetime_beginning_ept"], errors="coerce")
    df = df[ept.dt.year == year]
    means = []
    for hub in _BORDER_HUBS:
        sub = df[df["pnode_name"] == hub]
        if sub.empty:
            return None
        means.append(np.nanmean(pd.to_numeric(sub["total_lmp_rt"], errors="coerce")))
    return float(np.mean(means))


def derive(years: list[int]) -> dict[int, float]:
    """Return ``{year: border-anchored HR}`` for the MISO PJM seam."""
    cur = {
        n.name: n.hr_by_year
        for n in INTERFACE_NEIGHBORS.get("MISO", [])
        if n.name == "PJM"
    }.get("PJM") or {}
    out: dict[int, float] = {}
    for year in years:
        sys_lmp = _system_mean_lmp(year)
        border_lmp = _border_mean_lmp(year)
        hr_sys = cur.get(year)
        if sys_lmp is None or border_lmp is None or hr_sys is None or sys_lmp <= 0:
            continue
        ratio = border_lmp / sys_lmp
        out[year] = round(hr_sys * ratio, 2)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()
    table = derive(args.years)
    cells = ", ".join(f"{y}: {hr}" for y, hr in sorted(table.items()))
    print("# Border-anchored MISO PJM-seam heat rates (paste into constants.py):")
    print(f"MISO_PJM_BORDER_HR_BY_YEAR: dict[int, float] = {{{cells}}}")


if __name__ == "__main__":
    main()
