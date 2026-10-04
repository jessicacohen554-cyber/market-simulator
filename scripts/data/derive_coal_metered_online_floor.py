"""Derive the DIAGNOSTIC metered coal online-state floor (never a keeper input).

Rule 13 ``[R-MEASURED]``: this artifact pins each coal plant's measured
commitment state (the hours its own CEMS meter shows it online), so it fails
the forward-reproducibility test and exists ONLY as the input of the
default-off, labelled diagnostic probe
``ScenarioConfig.diagnostic_coal_metered_online_floor`` (closeout-SOCO-w3,
desk direction 2026-10-04). Its question: when a coal plant is held at its own
metered minimum in every hour it was actually online, how much of the added
coal displaces CC? It must never back a keeper.

Per ``(plant_code, year)`` for every coal plant in the ISO fleet:

* the plant's coal-unit CAMPD net series (the frozen deriver's own coal-unit
  crosswalk ``_coal_unit_ids_by_plant`` and parasitic map, imported, not
  restated — rule 23 ``[R-FROZEN-DERIVE]``; gas-converted boilers sharing the
  facility id are excluded by that crosswalk);
* ``online`` = net above the frozen deriver's sync test
  (``_SYNC_MW_NAMEPLATE_FRAC`` x coal nameplate);
* ``floor_mw`` = the P5 of the plant's online net MW that year in every online
  hour, 0 elsewhere.

Output: ``data/raw/_processed-legacy/coal_metered_online_floor_<ISO>.parquet``
with columns ``plant_code, year, hour, floor_mw`` (online hours only).

Usage:
    python3 scripts/data/derive_coal_metered_online_floor.py --iso SOCO \
        --years 2019 2020 2021 2022 2023 2024 2025
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, set_eia860_vintage  # noqa: E402
from market_sim.config.plant_taxonomy import is_coal_class  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

_ONLINE_FLOOR_PCT: float = 5.0  # the census statistic: P5 of online net MW


def derive(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the long-format online-hour floor for ``iso`` over ``years``."""
    states = tuple(campd.states_for_iso(iso))
    if not states:
        raise SystemExit(f"no CAMPD states registered for ISO {iso!r}")
    factors = dtt._parasitic_factor_map()
    frames: list[pd.DataFrame] = []
    for year in years:
        set_eia860_vintage(year)
        cap: dict[int, float] = {}
        for gen in load_fleet_from_csv(iso, get_iso_config(iso), year=year):
            code = int(gen.plant_code)
            if code > 0 and is_coal_class(gen.plant_group):
                cap[code] = cap.get(code, 0.0) + float(gen.pmax_mw)
        if not cap:
            continue
        coal_units = dtt._coal_unit_ids_by_plant(states, year)
        df = campd.load_campd_hourly(states, [year], prefer_unit_level=True)
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue

        def group_of(plant_id: int, unit_id: str, unit_type: str) -> str | None:
            if plant_id in cap and unit_id in coal_units.get(plant_id, ()):
                return "COAL"
            return None

        net = campd.plant_group_hourly_net(df, factors, year, group_of)
        for code, nameplate in sorted(cap.items()):
            series = net.get((code, "COAL"))
            if series is None or nameplate <= 0.0:
                continue
            online = series > dtt._SYNC_MW_NAMEPLATE_FRAC * nameplate
            if not online.any():
                continue
            level = float(np.percentile(series[online], _ONLINE_FLOOR_PCT))
            hours = np.flatnonzero(online)
            frames.append(
                pd.DataFrame(
                    {
                        "plant_code": np.int32(code),
                        "year": np.int16(year),
                        "hour": hours.astype(np.int16),
                        "floor_mw": np.float32(level),
                    }
                )
            )
            print(
                f"  {iso} {year} plant {code}: online {online.mean():.3f}, "
                f"floor {level:.1f} MW, {level * online.sum() / 1e6:.2f} TWh"
            )
    if not frames:
        raise SystemExit(f"no coal online floor derived for {iso} {years}")
    return pd.concat(frames, ignore_index=True)


def main() -> None:
    """Derive and write the artifact."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    out = a.out or PROCESSED_DIR / f"coal_metered_online_floor_{a.iso}.parquet"
    d = derive(a.iso, a.years)
    d.to_parquet(out, index=False)
    print(f"Wrote {out} — {len(d)} online plant-hours")


if __name__ == "__main__":
    main()
