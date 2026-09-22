"""miso-266 — DECOMPOSE the coal bins' summed removed share, at ZERO LP.

FINDING-miso265 locates the defect in :func:`market_sim.data.outages.
_unit_outage_factors_from_events`: concurrent unit shares SUM and clip at full
derate, so a plant is zeroed in hours it demonstrably ran. It names two live
repair directions and says the choice must be made on the extract's own
CONSTRUCTION, never on the residual (rule 1 ``[R-STRUCT]``).

This probe supplies the construction evidence. Under ``per_unit_clip`` (TRUE in
the MISO keeper) each unit's removed MW is already capped at its own capacity,
so at any hour ``v[t] = sum_{u flagged at t} ucap_u / denom`` EXACTLY -- i.e.
the per-unit union is already in place. Any residual ``v[t] > 1`` therefore has
exactly one arithmetic source:

    sum_{u flagged at t} unit_capacity_mw  >  cap[bin]

which is a NUMERATOR/DENOMINATOR BASIS question, not a concurrency question.
This probe measures that directly, per bin:

* ``n_units_extract`` / ``sum_ucap``  -- the extract's own roster and MW;
* ``cap_bin``                          -- the LP's own bin capacity (denominator);
* ``ratio``                            -- sum_ucap / cap_bin, the excess at FULL
  concurrency;
* ``max_v`` / ``h_over_1``             -- the realised peak share and the hours
  the pre-clip sum is above 1.0;
* ``h_all_out``                        -- hours in which EVERY unit the extract
  carries for the bin is flagged (a genuine full-plant outage, which SHOULD zero).

The discriminating question is then: of the hours a bin sits at availability 0,
how many are ``h_all_out`` (correct) and how many are basis excess (defect)?
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _generic_unit_outage_target,
    _iso_plant_capacity,
    _load_unit_outage_events,
    outage_hour_mask,
    unit_outage_csv_for_iso,
    unit_outage_event_window,
)
from scripts.probes._miso265_ceiling_vs_meter_hourly import decode_plant_mw  # noqa: E402
from scripts.probes._miso265_coal_availability_ceiling import (  # noqa: E402
    COAL_CLASSES,
    _assert_partition_leg,
    load_bench,
)

HOURS = {2020: 8784, 2024: 8784}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default="results/calibration/miso264_anchor_span")
    ap.add_argument("--year", type=int, default=2020)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--mixed-gas-routing", action="store_true", default=True)
    args = ap.parse_args()

    year = args.year
    hours = HOURS.get(year, 8760)
    bundle = REPO / args.bundle
    _assert_partition_leg(json.loads((bundle / "meta.json").read_text()), year)

    csv_path = unit_outage_csv_for_iso(args.iso, args.mixed_gas_routing, False, False, False)
    df = _load_unit_outage_events(csv_path, args.iso)
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    cap = _iso_plant_capacity(args.iso, False, False)

    # Per (bin, unit): the hour mask the unit is flagged, and its capacity.
    unit_mask: dict[tuple[tuple[int, str], str], np.ndarray] = {}
    unit_cap: dict[tuple[tuple[int, str], str], float] = {}
    for r in df.itertuples(index=False):
        tgt = _generic_unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap or tgt[1] != "COAL":
            continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        w0, w1 = unit_outage_event_window(r, False)
        mask = outage_hour_mask(w0, w1, year, hours)
        if not mask.any():
            continue
        k = (tgt, str(r.unit_id))
        m = unit_mask.get(k)
        unit_mask[k] = mask if m is None else (m | mask)
        unit_cap[k] = max(unit_cap.get(k, 0.0), float(ucap))

    bins: dict[tuple[int, str], list[str]] = defaultdict(list)
    for (tgt, uid) in unit_mask:
        bins[tgt].append(uid)

    bench = load_bench(args.iso, year)
    meters: dict[int, np.ndarray] = {}
    names: dict[int, str] = {}
    for key, rec in bench["plants"].items():
        if rec.get("group") not in COAL_CLASSES:
            continue
        base = int(key.split(":")[0])
        m = decode_plant_mw(rec, key)
        if m is not None:
            meters[base] = m if base not in meters else meters[base] + m
            names[base] = rec.get("name", "?")

    rows = []
    tot = dict(zero_h=0, allout_h=0, basis_h=0, contra_h=0, contra_allout=0, contra_basis=0)
    for tgt, uids in bins.items():
        denom = cap[tgt]
        sum_ucap = sum(unit_cap[(tgt, u)] for u in uids)
        v = np.zeros(hours)
        n_flag = np.zeros(hours, dtype=int)
        for u in uids:
            v[unit_mask[(tgt, u)]] += unit_cap[(tgt, u)] / denom
            n_flag[unit_mask[(tgt, u)]] += 1
        zero = v >= 1.0 - 1e-12
        all_out = n_flag >= len(uids)
        basis_only = zero & ~all_out
        meter = meters.get(tgt[0])
        contra = np.zeros(hours, dtype=bool)
        if meter is not None:
            n = min(hours, len(meter))
            contra[:n] = zero[:n] & (meter[:n] > 0.0)
        tot["zero_h"] += int(zero.sum())
        tot["allout_h"] += int((zero & all_out).sum())
        tot["basis_h"] += int(basis_only.sum())
        tot["contra_h"] += int(contra.sum())
        tot["contra_allout"] += int((contra & all_out).sum())
        tot["contra_basis"] += int((contra & ~all_out).sum())
        rows.append(
            dict(
                code=tgt[0],
                name=names.get(tgt[0], "?")[:26],
                n_u=len(uids),
                sum_ucap=sum_ucap,
                cap_bin=denom,
                ratio=sum_ucap / denom,
                max_v=float(v.max()),
                zero_h=int(zero.sum()),
                allout_h=int((zero & all_out).sum()),
                basis_h=int(basis_only.sum()),
                contra_h=int(contra.sum()),
                c_allout=int((contra & all_out).sum()),
                c_basis=int((contra & ~all_out).sum()),
            )
        )

    rows.sort(key=lambda r: -r["contra_h"])
    print(f"=== {args.iso} {year} — COAL bin removed-share decomposition (ZERO LP) ===")
    print(f"extract: {csv_path.name}   coal bins with >=1 window: {len(rows)}")
    print()
    hdr = (
        f"{'plant':>6} {'name':26} {'nU':>3} {'sumUcap':>8} {'capBin':>8} {'ratio':>6} "
        f"{'maxV':>6} {'zeroH':>6} {'allOut':>6} {'basis':>6} {'contra':>6} {'c_all':>6} {'c_bas':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows[:22]:
        print(
            f"{r['code']:6d} {r['name']:26} {r['n_u']:3d} {r['sum_ucap']:8.1f} {r['cap_bin']:8.1f} "
            f"{r['ratio']:6.3f} {r['max_v']:6.3f} {r['zero_h']:6d} {r['allout_h']:6d} "
            f"{r['basis_h']:6d} {r['contra_h']:6d} {r['c_allout']:6d} {r['c_basis']:6d}"
        )
    print()
    print("TOTALS over every coal bin:")
    print(f"  plant-hours at pre-clip share >= 1.0 (availability 0) : {tot['zero_h']:,d}")
    print(f"    of which EVERY extract unit is flagged (correct)    : {tot['allout_h']:,d}")
    print(f"    of which BASIS EXCESS only (defect)                 : {tot['basis_h']:,d}")
    print(f"  contradicted by the plant's own meter                 : {tot['contra_h']:,d}")
    print(f"    contradicted while EVERY unit is flagged            : {tot['contra_allout']:,d}")
    print(f"    contradicted by BASIS EXCESS only                   : {tot['contra_basis']:,d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
