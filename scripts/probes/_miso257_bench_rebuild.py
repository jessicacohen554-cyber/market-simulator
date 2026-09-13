#!/usr/bin/env python3
"""Reconstruct the three gitignored solve artifacts a SLIM bundle is missing.

miso-257, following the recipe proved in
``docs/RESULT-pjm-h4-bench-move-landed-2026-09-13.md`` §2. A registered bundle
committed in the slim form carries only ``hourly/`` sidecars and its JSON;
``dispatch/<year>_P1.parquet``, ``system.parquet`` and ``btm.parquet`` are
gitignored and did not survive the solve container. ``build_payload`` reads all
three, so the bench part cannot be regenerated without them — and a re-solve to
reproduce a model side the bench change does not touch is ~35-70 min of LP.

Each artifact is reconstructed from a COMMITTED source:

* ``dispatch/<year>_P1.parquet`` — one row per ``(plant_code, klass, zone)``
  read off the committed bench part's own ``plants`` block. Only the class set
  and the zone label are consumed on the bench side (``classes_p`` / ``zone_p``
  in ``render_calibration_html.build_payload``); ``mw`` feeds the MODEL side,
  which this session does not regenerate.
* ``system.parquet`` — a concat of the committed ``hourly/system_<year>.parquet``
  sidecars (identical schema).
* ``btm.parquet`` — rebuilt through ``run_calibration_full._btm_frame``, which
  is a pure function of committed inputs by its own docstring and design. It is
  the BTM subtrahend of ``classFull``, so omitting it silently moves every CHP
  class (pjm-h4 §2 measured +3.3 / +2.4 / +0.9 TWh when it was left out).

The reconstruction is admissible ONLY under the gate in
``_miso257_bench_gate.py``: the rebuilt part's plant key set and every
dispatch-scoped field must come back byte-identical to the committed part.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from scripts.lib import backcast_artifacts as ba  # noqa: E402

BENCH = REPO / "frontend" / "data" / "backcast" / "bench"


def _dispatch_from_bench(iso: str, year: int) -> pd.DataFrame:
    """One ``(plant_code, klass, zone)`` row per committed bench plant key."""
    part = ba.load_bench_part(BENCH / iso / f"{year}.json.gz")
    rows = []
    for key, rec in part["bench"]["plants"].items():
        code_s, _, klass_s = str(key).partition(":")
        code = int(code_s)
        klass = klass_s or str(rec["group"])
        rows.append(
            {
                "year": year,
                "pass": "P1",
                "plant_code": code,
                "klass": klass,
                "zone": str(rec["zone"]),
                "hour": 0,
                "mw": 0.0,
            }
        )
    return pd.DataFrame(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    args = ap.parse_args()
    bundle = args.bundle if args.bundle.is_absolute() else REPO / args.bundle

    import scripts.run_calibration_full as rcf
    from market_sim.config.iso_configs import get_iso_config

    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    years = [int(y) for y in meta["years"]]
    hours = int(meta.get("hours", 8760))
    iso_config = get_iso_config(iso)
    generation = rcf.load_monthly_generation()
    parasitic = rcf._parasitic_factor_map()

    btm_backfill_year = meta.get("btm_backfill_year")
    btm_backfill_year = None if btm_backfill_year is None else int(btm_backfill_year)

    (bundle / "dispatch").mkdir(exist_ok=True)
    sys_frames, btm_frames = [], []
    for year in years:
        disp = _dispatch_from_bench(iso, year)
        disp.to_parquet(bundle / "dispatch" / f"{year}_P1.parquet", index=False)

        sidecar = bundle / "hourly" / f"system_{year}.parquet"
        sys_frames.append(pd.read_parquet(sidecar))

        campd_year = rcf._campd_hourly_frame(year, iso, parasitic, hours)
        campd_active = None
        if campd_year is not None:
            bp = campd_year.groupby("plant_id")["net_mw"].sum()
            campd_active = set(bp[bp > 0.0].index.astype(int))
        group_by_code = rcf._fleet_group_by_code(iso, iso_config, year)
        btm_frames.append(
            rcf._btm_frame(
                year,
                "P1",
                generation,
                btm_backfill_year=btm_backfill_year,
                campd_active=campd_active,
                iso=iso,
                group_by_code=group_by_code,
                nyiso_chp_btm_measured=bool(meta.get("nyiso_chp_btm_measured")),
            )
        )
        print(f"  {iso} {year}: dispatch {len(disp)} rows, btm {len(btm_frames[-1])} rows")

    pd.concat(sys_frames, ignore_index=True).to_parquet(
        bundle / "system.parquet", index=False
    )
    pd.concat(btm_frames, ignore_index=True).to_parquet(
        bundle / "btm.parquet", index=False
    )
    print(f"reconstructed dispatch/ + system.parquet + btm.parquet in {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
