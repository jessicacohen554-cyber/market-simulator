"""MISO scarcity-tail bind gate — memory-light, no LP re-solve.

The design-first gate for the MISO >$200 scarcity-tail workstream
(docs/multi-iso/miso-zonal-refinement-scope.md gate 4, the miso-38
perfect-foresight-headroom diagnosis): would 10-minute-ramp deliverability
limits on reserve supply (``miso_reserve_pergen``, the class-level pooled
``R <= sum ramp10 x availability`` build) let the market-wide RBDC or the
MISO-South zonal family genuinely run SHORT — pricing the published curve
steps — or does the perfect-foresight LP hold deliverable headroom above the
requirement even in the hours actual MISO priced >$200?

Reads a solved bundle's per-unit dispatch and reconstructs the exact fleet
(pmax x availability incl. the CAMPD outage overlay) via
``run_year(fleet_only=True)``, then reports, per family:

* total eligible headroom (what the zone-aggregate co-opt draws on),
* AS-DISPATCHED deliverable reserve = sum_pools min(sum ramp10 x avail,
  pool headroom) — what the pergen build could clear without re-dispatch,
* RE-DISPATCH MAX deliverable reserve — the LP's best case: load the
  non-reserve (beyond-ramp) capacity first, so deliverable =
  min(sum min(ramp10, cap), total cap - thermal load). If even this crosses
  below the requirement, the pergen LP MUST price the curve in those hours.

Both are checked against the actual Indiana-hub RT/DA >$200 event hours so
the verdict is about the right hours, not just any hours.

Usage:
  PYTHONPATH=.:src python scripts/probes/_miso_scarcity_bindgate.py \
      results/calibration/MISO/_diag_miso38_base 2025
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.fleet import FUEL_TYPE_NAMES  # noqa: E402
from market_sim.config.reserve_config import (  # noqa: E402
    MISO_REGULATING_RESERVE_MW,
    RESERVE_FUEL_TYPES,
)


def _fleet_state(meta: dict, year: int) -> dict:
    """Reconstruct the bundle's fleet (same config, outage overlay, derates)."""
    from run_calibration import run_year  # heavy import

    return run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        meta["gas_prices"][str(year)],
        ttc_overrides={},
        commitment_enabled=False,
        commitment_screen_coal=meta.get("commitment_screen_coal", True),
        outage_source=meta.get("outage_source", "historic"),
        coal_prb_passthrough=meta.get("coal_prb_passthrough", 1.0),
        coal_prb_passthrough_sigmoid=meta.get("coal_prb_passthrough_sigmoid", False),
        coal_prb_passthrough_tiered=meta.get("coal_prb_passthrough_tiered", False),
        coal_bit_sigmoid=meta.get("coal_bit_passthrough_sigmoid", False),
        coal_mustrun_per_plant=meta.get("coal_mustrun_per_plant", False),
        coal_drop_pof=meta.get("coal_drop_pof", False),
        ct_intermediate_split=meta.get("ct_intermediate_split", False),
        cc_intermediate_split=meta.get("cc_intermediate_split", False),
        st_gas_intermediate=meta.get("st_gas_intermediate", False),
        miso_zonal_gas_basis=meta.get("miso_zonal_gas_basis", False),
        cc_nameplate_summer_derate=meta.get("cc_nameplate_summer_derate", False),
        priced_interchange=meta.get("priced_interchange", False),
        fleet_only=True,
    )


def _actual_event_hours(year: int, hours: int) -> tuple[np.ndarray, np.ndarray]:
    """(rt_mask, da_mask): Indiana-hub actual >$200 hours on the model clock."""
    path = RAW_DIR / "_validation-source" / "actual_lmp_hourly_zonal_MISO.parquet"
    df = pd.read_parquet(path)
    ind = df[(df.year == year) & (df.hub == "INDIANA.HUB")].set_index("hour")
    rt = np.zeros(hours, dtype=bool)
    da = np.zeros(hours, dtype=bool)
    rt[ind.index[ind.rt > 200.0]] = True
    da[ind.index[ind.da > 200.0]] = True
    return rt, da


def main(bundle: Path, year: int) -> None:
    meta = json.loads((bundle / "meta.json").read_text())
    hours = int(meta["hours"])
    state = _fleet_state(meta, year)
    fa = state["fleet_arrays"]

    fuel = np.array([FUEL_TYPE_NAMES[i] for i in fa.fuel_type_idx])
    elig = np.isin(fuel, sorted(RESERVE_FUEL_TYPES))
    ramp10 = np.asarray(fa.ramp10, dtype=float)
    member = elig & (ramp10 > 0.0)
    cap = fa.pmax[:, None] * fa.availability  # (n_unit, T)
    zone_idx = np.asarray(fa.zone_idx, dtype=int)
    uids = np.asarray(fa.unit_ids, dtype=object)

    disp = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    dmat = (
        disp.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(uids)
        .fillna(0.0)
        .to_numpy()
    )
    headroom = np.maximum(cap - dmat, 0.0)

    from market_sim.config.iso_configs import get_iso_config

    zone_names = list(get_iso_config(meta["iso"]).zone_names)
    south = zone_names.index("MISO-South") if "MISO-South" in zone_names else None

    # Requirements as the LP builds them (reserve_config._miso_design).
    from market_sim.results.scarcity import largest_single_contingency_mw

    mssc = largest_single_contingency_mw(
        fa.pmax,
        availability=fa.availability,
        reserve_mask=elig,
        plant_code=fa.plant_code,
    )
    req_mkt = float(mssc) + MISO_REGULATING_RESERVE_MW
    req_south = None
    if south is not None:
        req_south = float(
            largest_single_contingency_mw(
                fa.pmax,
                availability=fa.availability,
                reserve_mask=elig & (zone_idx == south),
                plant_code=fa.plant_code,
            )
        )

    rt_mask, da_mask = _actual_event_hours(year, hours)

    def family_report(name: str, mask: np.ndarray, req: float) -> None:
        """mask: (n_unit,) member-of-family units (reserve draws only on these)."""
        m = member & mask
        hr = headroom[m]  # (n_m, T)
        cap_m = cap[m]
        r10_t = ramp10[m][:, None] * fa.availability[m]  # avail-scaled ramp
        total_hr = headroom[elig & mask].sum(axis=0)  # aggregate-co-opt view
        # As-dispatched deliverable, pooled per (zone, fuel-class).
        keys = np.stack([zone_idx[m], np.asarray(fa.fuel_type_idx)[m]], axis=1)
        _, col = np.unique(keys, axis=0, return_inverse=True)
        n_r = int(col.max()) + 1 if col.size else 0
        pool_hr = np.zeros((n_r, hours))
        pool_r10 = np.zeros((n_r, hours))
        np.add.at(pool_hr, col, hr)
        np.add.at(pool_r10, col, r10_t)
        as_disp = np.minimum(pool_hr, pool_r10).sum(axis=0)
        # Re-dispatch max: thermal load on family units can be re-packed onto
        # beyond-ramp capacity first.
        load_m = dmat[m].sum(axis=0)
        sum_min = np.minimum(cap_m, r10_t).sum(axis=0)
        nonres = np.maximum(cap_m - r10_t, 0.0).sum(axis=0)
        redisp = np.minimum(
            sum_min - np.maximum(load_m - nonres, 0.0), cap_m.sum(axis=0) - load_m
        )

        print(f"\n--- family {name}: requirement {req:,.0f} MW ---")
        for label, series in (
            ("aggregate headroom", total_hr),
            ("as-dispatched deliverable (pooled ramp)", as_disp),
            ("re-dispatch MAX deliverable", redisp),
        ):
            below = series < req
            print(
                f"  {label:42s} min {series.min():8,.0f}  p1 "
                f"{np.percentile(series, 1):8,.0f}  p50 "
                f"{np.percentile(series, 50):8,.0f}  | h<req "
                f"{int(below.sum()):4d}  in actual RT-tail h "
                f"{int((below & rt_mask).sum()):3d}/{int(rt_mask.sum())}  "
                f"DA-tail h {int((below & da_mask).sum()):3d}/{int(da_mask.sum())}"
            )
        # Where do the actual event hours sit on the deliverable duration curve?
        if rt_mask.any():
            print(
                f"  re-dispatch-max deliverable in actual RT-tail hours: "
                f"min {redisp[rt_mask].min():,.0f}  median "
                f"{np.median(redisp[rt_mask]):,.0f}  (vs req {req:,.0f})"
            )

    print(f"\n=== MISO scarcity bind gate: {bundle.name} {year} ===")
    print(
        f"members {int(member.sum())} of {len(uids)} units; "
        f"actual IND RT>$200 h: {int(rt_mask.sum())}, DA>$200 h: {int(da_mask.sum())}"
    )
    family_report("miso_rbdc (market-wide)", np.ones(len(uids), bool), req_mkt)
    if south is not None and req_south:
        family_report("miso_zonal_or_miso_south", zone_idx == south, req_south)


if __name__ == "__main__":
    main(Path(sys.argv[1]), int(sys.argv[2]) if len(sys.argv) > 2 else 2025)
