"""Derive per-plant CC_REGULAR conduct profiles (month x hour-of-day online counts) from CAMPD.

Feeds ``ScenarioConfig.cc_mustrun_conduct_window`` (PJM-NEXT-17): the ``cc_mustrun_per_plant``
floor keeps its SIZE (``online_frac`` x hours) but its hours are ranked by the plant's own
measured online probability in the hour's month x hour-of-day cell, pooled over every
artifact year EXCEPT the solved one (leave-one-year-out at runtime), ties broken by system
load.

Measurement, frozen to ``derive_thermal_tranches.py`` (rule 23 [R-FROZEN-DERIVE]):
- per-unit routing: ``_per_unit_group_resolver`` (the unit lands on the bin that contains it);
- net = CAMPD gross x the pooled parasitic factor (``plant_group_hourly_net``);
- an hour is ONLINE when net > ``_SYNC_MW_NAMEPLATE_FRAC`` (1 %) x the plant's CC_REGULAR
  nameplate -- the identical test that defines ``online_frac``.

The hour clock is CAMPD's local-standard hour of year (Feb 29 dropped), the clock the model
dispatches on. Cell = month(0..11) x hour-of-day(0..23); the grain was chosen ex ante by
held-out conduct log-loss in ``scripts/probes/_pjmnext17_cc_conduct_window.py`` (month x hour
beats month x day-type x hour in all seven PJM years) and never against a price or volume
residual.

Output: ``data/raw/_processed-legacy/cc_conduct_profile_<ISO>.csv`` with columns
``plant_code, year, month, hod, sync_hours, hours``.

Usage::

    python scripts/data/derive_cc_conduct_profile.py --iso PJM --years 2019 2020 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.data.derive_thermal_tranches import (  # noqa: E402
    _SYNC_MW_NAMEPLATE_FRAC,
    _fleet_nameplate_and_group,
    _parasitic_factor_map,
    _per_unit_group_resolver,
)

GROUP = "CC_REGULAR"
HOURS = 8760
# Month of each hour of a 365-day year (Feb 29 is dropped by the CAMPD loader).
_MONTH = np.repeat(
    np.arange(12), [744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]
)
_HOD = np.tile(np.arange(24), 365)


def output_path(iso: str) -> Path:
    """Committed artifact path for *iso*."""
    return PROCESSED_DIR / f"cc_conduct_profile_{iso}.csv"


def derive(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the per-(plant, year, month, hour-of-day) online counts for *iso*."""
    cap, primary = _fleet_nameplate_and_group(iso)
    cc = {code: mw for (code, g), mw in cap.items() if g == GROUP and mw > 0}
    group_of = _per_unit_group_resolver(cap, primary, iso)
    factors = _parasitic_factor_map()
    states = list(campd.states_for_iso(iso))
    cell = _MONTH * 24 + _HOD
    rows = []
    for year in years:
        df = campd.load_campd_hourly(states, [year], prefer_unit_level=True)
        if df.empty:
            continue
        net = campd.plant_group_hourly_net(df, factors, year, group_of)
        for code, nameplate in sorted(cc.items()):
            series = net.get((code, GROUP))
            if series is None or len(series) != HOURS:
                continue
            sync = (series > _SYNC_MW_NAMEPLATE_FRAC * nameplate).astype(float)
            on = np.bincount(cell, weights=sync, minlength=288)
            n = np.bincount(cell, minlength=288)
            for c in range(288):
                rows.append((code, year, c // 24, c % 24, int(on[c]), int(n[c])))
        print(
            f"{iso} {year}: {sum(1 for r in rows if r[1] == year) // 288} plants",
            flush=True,
        )
    return pd.DataFrame(
        rows, columns=["plant_code", "year", "month", "hod", "sync_hours", "hours"]
    )


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", type=int, nargs="+", required=True)
    a = ap.parse_args()
    out = derive(a.iso.upper(), a.years)
    path = output_path(a.iso.upper())
    out.to_csv(path, index=False)
    print(f"wrote {path} ({len(out)} rows)")


if __name__ == "__main__":
    main()
