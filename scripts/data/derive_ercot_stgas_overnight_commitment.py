#!/usr/bin/env python
"""Derive each ERCOT ST_GAS plant's measured OVERNIGHT energy per year (R-ERCOT-18).

The input to ``ScenarioConfig.netload_drag_prior_year_commitment_index``: the
per-plant allocation index of the ST_GAS net-load drag floor
(``fleet.floors.apply_gas_st_netload_drag_floor``).

Why it exists. The drag's driver is a FLEET quantity — the CAMPD overnight
(23–05h, low-price) capacity factor of the drag-covered ST_GAS fleet,
regressed on net-load (``docs/ercot-st-gas-netload-drag-2026-06.md``). The
pro-rata applier puts that one fraction on every covered plant, which asserts
that every plant carries the fleet's overnight commitment. The meter says a
two-shifting plant carries none of it: Lake Hubbard (3452) ran an overnight CF
of 0.000–0.012 in 2019–2022 (online by day, off every night), and it is the
plant the D-4 per-unit conduct rider convicts in 2019–2023
(``docs/records/ercot/r-ercot/PRECOMMIT-r-ercot-18-drag-overnight-index-2026-09-30.md``).
This artifact is the plant decomposition of the drag's OWN driver statistic,
from the SAME source, window and unit routing the curve's derive uses.

Construction — nothing here reads a model output, a price or a residual:

* Fleet and unit routing are imported from the curve's own measurement probe
  (``scripts.probes.ercot90_stgas_shoulder_measure``): the model's ST_GAS plant
  set from ``custom-bin-assignments.csv``, steam units only (CT/CC unit types
  dropped), the two split facilities (34702 Parish gas steamers, 49392 Barney
  Davis unit 1) unit-routed exactly as ``data.outages`` does, CAMPD gross netted
  by the class parasitic factor.
* Window: the drag's driver window, ``OVERNIGHT_START_H``–``OVERNIGHT_END_H``
  (23–05h local standard), on the model's fixed non-leap 8760 clock.
* Output: one row per (plant, year) — overnight net MWh and whether the plant
  had any CAMPD rows that year (``metered``). No capacity is stored: the
  consumer divides by the floor's own ``pmax`` basis at solve time, so the index
  lands in the exact coordinates the floor multiplies onto.

Frozen (rule 23 [R-FROZEN-DERIVE]): re-derive only when the CAMPD unit-level
source updates or a new year's vintage lands — never because a residual moved.

Usage::

    python scripts/data/derive_ercot_stgas_overnight_commitment.py \
        [--years 2019 2020 2021 2022 2023 2024 2025] \
        [--out data/raw/_validation-source/ercot_stgas_overnight_commitment.csv]
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))  # repo root: canonical scripts.* sibling imports
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402

from scripts.data.derive_ercot_dam_cleared_share import HOURS  # noqa: E402
from scripts.probes.ercot90_stgas_shoulder_measure import (  # noqa: E402
    CAMPD_UNIT_DIR,
    OVERNIGHT_END_H,
    OVERNIGHT_START_H,
    _campd_st_hourly,
    _st_gas_plants,
)

DEFAULT_OUT = CALIBRATION_DIR / "ercot_stgas_overnight_commitment.csv"
DEFAULT_YEARS = [2019, 2020, 2021, 2022, 2023, 2024, 2025]


def _sha256(path: Path) -> str:
    """Return the hex sha256 of ``path`` (source-identity record)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def derive(years: list[int]) -> pd.DataFrame:
    """Per-(plant, year) measured overnight net MWh for the drag-covered ST_GAS fleet.

    Args:
        years: Calendar years to derive; each needs ``TX_<year>.parquet``.

    Returns:
        DataFrame with columns ``iso, plant_code, year, overnight_net_mwh,
        overnight_hours, metered, source_sha256``.
    """
    plants = _st_gas_plants()
    covered = plants[plants["drag_covered"]]
    hod = np.arange(HOURS) % 24
    overnight = (hod >= OVERNIGHT_START_H) | (hod < OVERNIGHT_END_H)
    rows = []
    for year in years:
        src = CAMPD_UNIT_DIR / f"TX_{year}.parquet"
        if not src.exists():
            raise SystemExit(f"{src} not on disk — cannot derive {year}")
        sha = _sha256(src)
        _, per_plant, notes = _campd_st_hourly(year, covered)
        unmetered = {int(n.split()[1]) for n in notes if n.startswith("plant ")}
        for code, series in sorted(per_plant.items()):
            rows.append(
                {
                    "iso": "ERCOT",
                    "plant_code": int(code),
                    "year": int(year),
                    "overnight_net_mwh": round(float(series[overnight].sum()), 1),
                    "overnight_hours": int(overnight.sum()),
                    "metered": int(code) not in unmetered,
                    "source_sha256": sha,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Derive the per-plant overnight-energy table and write the frozen artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=DEFAULT_YEARS)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    df = derive(args.years)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    piv = df.pivot(index="plant_code", columns="year", values="overnight_net_mwh")
    print((piv / 1e3).round(1).to_string())
    print(f"wrote {len(df)} rows -> {args.out}")


if __name__ == "__main__":
    main()
