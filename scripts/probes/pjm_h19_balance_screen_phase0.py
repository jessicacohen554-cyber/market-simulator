"""pjm-h19 phase 0 (ZERO LP): census of every hour ``_screen_demand_balance`` flags.

Runs the screen on each ISO's ACTUAL loader output (after the existing
dropout and spike screens) for every year 2018-2025 on disk and records each
flagged hour with its neighbours and the balance-identity reading ``NG - TI``.
Output: ``results/calibration/_pjm_h19_balance_screen_phase0.json``.
Bar declared before measurement: docs/PRECOMMIT-pjm-h19-demand-balance-screen-2026-09-23.md §2.
"""

from __future__ import annotations

import json
import logging

import numpy as np

from market_sim.config.paths import REPO_ROOT
from market_sim.data.eia930 import demand as dm
from market_sim.data.eia930.frames import _eia_hourly_frame_filled, _ercot_hourly_frame

logging.disable(logging.WARNING)

LOADERS = {
    "ERCOT": lambda y: (dm._load_ercot_hourly(y) or (None,))[0],
    "CAISO": lambda y: dm._load_caiso_hourly_demand(y),
    "NYISO": dm._load_nyiso_hourly_demand,
    "NEISO": dm._load_neiso_hourly_demand,
    "MISO": dm._load_miso_hourly_demand,
    "PJM": dm._load_pjm_hourly_demand,
    "SPP": dm._load_spp_hourly_demand,
    "SOCO": dm._load_soco_hourly_demand,
    "NWPP": dm._load_nwpp_hourly_demand,
}


def main() -> None:
    """Write the census JSON and print a one-line summary per ISO-year."""
    out: dict = {"bar": "PRECOMMIT-pjm-h19 §2 (v2)", "iso_years": {}}
    for iso, load in LOADERS.items():
        for year in range(2018, 2026):
            try:
                raw = load(year)
            except Exception as exc:  # noqa: BLE001 - census records absence
                out["iso_years"][f"{iso}-{year}"] = {"status": f"error {type(exc).__name__}"}
                continue
            if raw is None:
                out["iso_years"][f"{iso}-{year}"] = {"status": "no frame"}
                continue
            fixed = dm._screen_demand_balance(raw, iso=iso, year=year)
            hours = np.flatnonzero(fixed != raw).tolist()
            rec: dict = {"status": "ok", "n_flagged": len(hours), "hours": []}
            ba = dm._BALANCE_SCREEN_BA.get(iso)
            if ba is not None:
                fr = _ercot_hourly_frame(year) if iso == "ERCOT" else _eia_hourly_frame_filled(ba, year)
                s = (fr["Net generation"] - fr["Total interchange"]).to_numpy(float)
                for t in hours:
                    rec["hours"].append(
                        {
                            "hour": t,
                            "demand_raw": float(raw[t]),
                            "prev": float(raw[t - 1]),
                            "next": float(raw[t + 1]),
                            "ng_minus_ti": float(s[t]),
                            "repaired": float(fixed[t]),
                            "utc": str(fr["UTC time"].iloc[t]) if "UTC time" in fr else None,
                        }
                    )
            else:
                rec["status"] = "inert by construction (no single-BA balance frame)"
            out["iso_years"][f"{iso}-{year}"] = rec
            print(iso, year, rec["status"], hours)
    path = REPO_ROOT / "results" / "calibration" / "_pjm_h19_balance_screen_phase0.json"
    path.write_text(json.dumps(out, indent=1))
    print("wrote", path)


if __name__ == "__main__":
    main()
