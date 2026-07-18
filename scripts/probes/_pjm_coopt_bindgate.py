"""PJM co-optimization PROBE #2 (the bind gate), memory-light / no LP re-solve.

The zone-aggregate ``dispatch._build_reserve_rows`` headroom row is
``sum_{elig g in zone z} P[g,t] + R_z[z,t] <= sum_{elig g in z} cap[g,t]`` — it
caps a zone's reserve at the zone's TOTAL eligible thermal headroom (idle units
included). The reserve balance ``sum_z R_z + shortfall >= REQ(t)+190`` is
system-wide, so reserve is fungible across zones. The reserve clearing price
(balance-row dual) is therefore $0 whenever the system can place the ~3.6 GW
requirement inside that free headroom — i.e. whenever total eligible thermal
headroom >> the requirement (finding #2). This probe measures that headroom from
the already-solved energy-only bundle, so no co-opt LP solve (which OOMs the box)
is needed to answer the gate.

Usage: python scripts/probes/_pjm_coopt_bindgate.py <energy_bundle> [year]
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from derive_pjm_ordc_overlay import _run_year_kwargs  # noqa: E402

from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    RESERVE_FUEL_TYPES,
    load_pjm_measured_reserve_requirement,
)


def main(bundle: Path, year: int) -> None:
    from run_calibration import run_year  # heavy import

    meta = json.loads((bundle / "meta.json").read_text())
    hours = int(meta["hours"])
    state = run_year(
        year,
        meta["iso"],
        hours,
        meta["gas_prices"][str(year)],
        **_run_year_kwargs(meta),
    )
    fa = state["fleet_arrays"]
    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    elig = np.isin(fuel, sorted(RESERVE_FUEL_TYPES))
    cap = fa.pmax[:, None] * fa.availability  # (n_unit, T)
    uids = np.asarray(fa.unit_ids, dtype=object)
    zone_idx = np.asarray(fa.zone_idx, dtype=int)

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    dmat = (
        disp.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )

    headroom = np.maximum(cap - dmat, 0.0)  # (n_unit, T), unused capacity
    # System-wide eligible thermal headroom (what the fungible balance row sees).
    sys_hr = headroom[elig].sum(axis=0)  # (T,)
    # Per-zone eligible thermal headroom (what each headroom row caps R_z at).
    n_zones = zone_idx.max() + 1
    zone_hr = np.zeros((n_zones, hours))
    for z in range(n_zones):
        m = elig & (zone_idx == z)
        if m.any():
            zone_hr[z] = headroom[m].sum(axis=0)

    req = load_pjm_measured_reserve_requirement(year, hours)
    rhs = req + 190.0  # the co-opt balance RHS (REQ + ORDC shoulder)

    # --- Finding #3 candidates: the deliverable-headroom caps that COULD make
    # the requirement bind. (a) plant-level ONLINE reserve (the honesty-gate
    # measure: only synchronized plants' headroom is real reserve); (b) that,
    # further capped at each unit's 10-minute ramp capability (illustrative
    # per-fuel engineering ramp fractions, NOT fitted — PJM CT peakers ramp
    # fast, coal/nuclear slow). If even these stay >> the ~3.6 GW requirement,
    # the ramp cap cannot make the step fire either -> STOP AND REPORT.
    plant_code = (
        disp.drop_duplicates("unit_id")
        .set_index("unit_id")
        .reindex(uids)["plant_code"]
        .fillna(-1)
        .to_numpy()
    )
    # plant online when any of its tranches dispatch (>0.5 MW this hour).
    codes, inv = np.unique(plant_code, return_inverse=True)
    plant_disp = np.zeros((len(codes), hours))
    np.add.at(plant_disp, inv, dmat)
    online_unit = (plant_disp > 0.5)[inv]  # (n_unit, T): unit's plant synchronized
    online_hr = np.where(elig[:, None] & online_unit, headroom, 0.0)
    sys_online = online_hr.sum(axis=0)

    # 10-minute ramp fraction of pmax per reserve fuel (engineering typicals).
    RAMP10 = {
        "gas_ct": 1.00,  # peakers/CTs reach full output well within 10 min
        "oil": 1.00,  # oil CTs fast; oil steamers rare in PJM reserve pool
        "gas_cc": 0.60,  # ~6%/min
        "gas_st": 0.30,  # ~3%/min
        "coal": 0.15,  # ~1.5%/min
        "nuclear": 0.00,  # baseload, not maneuverable
    }
    ramp10_mw = np.array([RAMP10.get(f, 0.0) for f in fuel])[:, None] * fa.pmax[:, None]
    deliverable = np.minimum(online_hr, ramp10_mw)  # online AND ramp-reachable
    sys_deliv = deliverable.sum(axis=0)

    print(f"\n=== PROBE #2 bind gate: {bundle.name} {year} ===")
    print(
        f"co-opt balance requirement (REQ+190): mean {rhs.mean() / 1000:.2f} GW, "
        f"max {rhs.max() / 1000:.2f} GW"
    )
    print(f"eligible reserve units: {int(elig.sum())} of {len(uids)}")
    print("\nSYSTEM-WIDE eligible thermal headroom (GW):")
    print(
        f"  min {sys_hr.min() / 1000:6.2f}   p1 {np.percentile(sys_hr, 1) / 1000:6.2f}   "
        f"p50 {np.percentile(sys_hr, 50) / 1000:6.2f}   max {sys_hr.max() / 1000:6.2f}"
    )
    # Does the requirement ever exceed the free system headroom?
    bind_hours = int((sys_hr < rhs).sum())
    slack_ratio = sys_hr / rhs
    print(f"  hours system headroom < requirement: {bind_hours}/{hours}")
    print(
        f"  headroom/requirement ratio: min {slack_ratio.min():.1f}x   "
        f"p50 {np.median(slack_ratio):.1f}x"
    )
    verdict = (
        "BINDS AT $0 (headroom slack — finding #2 confirmed)"
        if bind_hours == 0
        else f"may price in {bind_hours} h (headroom < req)"
    )
    print(f"\nVERDICT (as-built zone-aggregate): reserve {verdict}")

    # --- Finding #3: would a deliverable / ramp cap make it bind? ---
    def report(label, series):
        b = int((series < rhs).sum())
        r = series / rhs
        print(
            f"\n{label} (GW): min {series.min() / 1000:5.2f}  "
            f"p1 {np.percentile(series, 1) / 1000:5.2f}  "
            f"p50 {np.percentile(series, 50) / 1000:5.2f}"
        )
        print(
            f"  hours < requirement: {b}/{hours}   "
            f"ratio min {r.min():.1f}x p50 {np.median(r):.1f}x"
        )
        return b

    print("\n--- Finding #3 (deliverable-headroom caps that COULD make it bind) ---")
    report("PLANT-LEVEL ONLINE eligible headroom", sys_online)
    b_dl = report("ONLINE + 10-min RAMP-capped deliverable reserve", sys_deliv)
    if b_dl == 0:
        print(
            "\nFINDING #3 VERDICT: even online + 10-min-ramp-deliverable reserve "
            f"stays above the {rhs.mean() / 1000:.1f} GW requirement in ALL {hours} h"
            " -> the published vertical step STILL cannot fire. The lever is the "
            "model's commitment posture (too much fast headroom synchronized & "
            "idle), NOT the reserve curve. STOP AND REPORT (claude.md #11): do not "
            "lower the breakpoint or inflate the penalty."
        )
    else:
        print(
            f"\nFINDING #3 VERDICT: the ramp cap makes the requirement bind in "
            f"{b_dl} h -> build the per-gen R<=ramp10 co-opt and re-solve."
        )


if __name__ == "__main__":
    bundle = Path(sys.argv[1])
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2024
    main(bundle, year)
