"""DIAGNOSTIC PROBE (no LP solve): PJM summer available-capacity vs load.

Quantifies the owner's hypothesis that the pjm-90 keeper overstates summer-peak
AVAILABLE capacity, so the LP never climbs the supply curve into scarcity. For
each summer month (Jun-Sep) 2023-2025 it builds the pjm-90 fleet via
``run_year(..., fleet_only=True)`` (the exact keeper config, no solve) and
reports, over the top net-load hours:

  (a) model available MW  = sum_g pmax[g] x availability[g,t]  (dispatchable),
      + renewable potential (cf x cap) + storage power cap
  (b) load (the LP RHS, net of injected must-run), and the implied surplus /
      reserve margin
  (c) how many top-load hours the model has a COMFORTABLE surplus
  (d) the marginal-class stack at the peak hour (what the LP would climb into).

Throwaway diagnostic — never registered (rule 16). Run:
  MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=2 python scripts/probes/_pjm_summer_capacity_diag.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration import run_year  # noqa: E402
from scripts.run_calibration_full import (  # noqa: E402
    _henry_hub_actual,
    _load_reference,
)
from scripts.run_pjm74_cc_ct_rebalance import BIT_OVERRIDES  # noqa: E402
from scripts.run_pjm75_ct_drag_cc_cap import (  # noqa: E402
    CONFIG_OVERRIDES,
    CT_DRAG_OVERRIDES,
)
from scripts.run_pjm90_cchp_srmc import _OFFER_OVERRIDES  # noqa: E402


_SUMMER = (6, 7, 8, 9)
_HOURS = 8760


def _month_of_hour(hours: int, year: int) -> np.ndarray:
    """Return the 1-based calendar month for each hour of ``year``."""
    import pandas as pd

    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy()


def _fleet(year: int):
    """Build the pjm-90 fleet for ``year`` (no LP) and return the arrays dict."""
    reference = _load_reference()
    gas_price = _henry_hub_actual(reference, year)
    # NB: must_run (biomass/other-gas) netting is skipped here — it is ~1-2 GW
    # and nets from BOTH demand and (injected) supply, so it roughly cancels in
    # the surplus comparison. Skipping it also dodges the priced-interchange
    # zone-count mismatch. Demand here is therefore un-netted (slightly higher),
    # which is the conservative direction for a "phantom surplus" check.
    res = run_year(
        year,
        "PJM",
        _HOURS,
        gas_price,
        ttc_overrides={},
        commitment_enabled=False,
        commitment_screen_coal=True,
        outage_source="historic",
        coal_prb_passthrough=1.0,
        coal_prb_passthrough_sigmoid=True,
        coal_mustrun_per_plant=True,
        retiree_cems_cap=True,
        coal_drop_pof=True,
        coal_prb_passthrough_tiered=True,
        prb_overrides=CONFIG_OVERRIDES,
        coal_bit_sigmoid=True,
        bit_overrides=BIT_OVERRIDES,
        coal_mustrun_online_pmin=True,
        coal_sync_srmc_tranche=True,
        gas_monthly_actuals=True,
        pjm_zonal_gas_basis=True,
        pjm_congestion=True,
        reference_price_interface=True,
        priced_interchange=True,
        cc_derate_from_top=True,
        hydro_eia930_monthly=True,
        hydro_backfill_year=2024,
        reliability_floor=True,
        ct_intermediate_split=True,
        ct_intermediate_cf_threshold=30.0,
        pjm_seam_flow_limit=True,
        pjm_seam_export_limit=True,
        offer_curve_overrides=_OFFER_OVERRIDES,
        curve_smoothing={
            "cc_duct_peaking_cap_pct": 18.0,
            "offer_curve_smoothing_mid": 0.35,
        },
        energy_reserve_coopt=True,
        pjm_reserve_supply_cap=True,
        ct_netload_drag=True,
        ct_drag_overrides=CT_DRAG_OVERRIDES,
        fleet_only=True,
    )
    return res


def _renewable_potential(res) -> np.ndarray:
    """Total renewable (wind+solar) potential MW per hour (cf x cap)."""
    out = np.zeros(_HOURS)
    for cf_key, cap_key in (("wind_cf", "wind_cap"), ("solar_cf", "solar_cap")):
        cf = res.get(cf_key)
        cap = res.get(cap_key)
        if cf is None or cap is None:
            continue
        cf = np.asarray(cf, dtype=float)
        cap = np.asarray(cap, dtype=float)
        if cf.ndim == 2:  # (n_zones, hours)
            pot = (cf * cap[:, None]).sum(axis=0) if cap.ndim == 1 else cf.sum(axis=0)
        else:  # (hours,)
            pot = cf * float(cap.sum()) if cap.ndim >= 1 else cf * float(cap)
        out += pot[:_HOURS]
    return out


def _run(year: int) -> None:
    """Print the summer available-capacity diagnostic for ``year``."""
    res = _fleet(year)
    fa = res["fleet_arrays"]
    demand = np.asarray(res["demand"], dtype=float)  # (n_zones, hours)
    load = demand.sum(axis=0)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)  # (n_gen, hours)
    thermal_avail = (pmax[:, None] * avail).sum(axis=0)
    renew = _renewable_potential(res)
    stor = float(np.asarray(res.get("storage_power_cap", 0.0)).sum())
    total_avail = thermal_avail + renew + stor
    net_load = load - renew  # what the dispatchable stack must climb

    month = _month_of_hour(_HOURS, year)
    groups = np.asarray(fa.plant_group, dtype=object)

    print(f"\n========== PJM {year} ==========")
    print(
        f"  fleet: {len(pmax)} units, nameplate-ish sum pmax={pmax.sum() / 1e3:,.1f} GW; "
        f"storage cap={stor / 1e3:.1f} GW"
    )
    print(f"  annual peak load (LP RHS)={load.max() / 1e3:,.1f} GW")
    for m in _SUMMER:
        sel = month == m
        if not sel.any():
            continue
        nl = net_load[sel]
        ta = total_avail[sel]
        th = thermal_avail[sel]
        ld = load[sel]
        # top ~100 net-load hours of the month
        k = min(100, sel.sum())
        top = np.argsort(nl)[-k:]
        surplus = ta[top] - ld[top]  # total resource minus load
        thermal_headroom = th[top] - nl[top]  # dispatchable headroom over netload
        rm = surplus / ld[top]  # reserve margin
        # "comfortable": >8% reserve margin (PJM operates ~ IRM 15% but tight
        # real-time reserve is <~5%); count hours the model is NOT tight.
        comfy = int((rm > 0.08).sum())
        print(
            f"  {year}-{m:02d} top{k} netload hrs: "
            f"load={ld[top].mean() / 1e3:5.1f}GW avail={ta[top].mean() / 1e3:5.1f}GW "
            f"surplus={surplus.mean() / 1e3:4.1f}GW RM={rm.mean() * 100:4.1f}% "
            f"thermal_headroom_over_netload={thermal_headroom.mean() / 1e3:4.1f}GW "
            f"comfy(>8%RM)={comfy}/{k} minRM={rm.min() * 100:4.1f}%"
        )
    # Peak-hour marginal stack: at the single highest net-load hour, show the
    # class composition of the top slice of the merit order (by pmax*avail).
    peak_h = int(np.argmax(net_load))
    unit_avail_mw = pmax * avail[:, peak_h]
    print(
        f"  peak net-load hour = h{peak_h} (month {month[peak_h]}), "
        f"netload={net_load[peak_h] / 1e3:.1f}GW thermal_avail={thermal_avail[peak_h] / 1e3:.1f}GW"
    )
    for grp in sorted(set(groups.tolist())):
        gmw = unit_avail_mw[groups == grp].sum()
        if gmw > 1.0:
            print(f"      {grp:16s} available {gmw / 1e3:6.2f} GW")


def main() -> int:
    """Run the diagnostic for 2023-2025."""
    for year in (2023, 2024, 2025):
        try:
            _run(year)
        except Exception as exc:  # pragma: no cover - diagnostic
            import traceback

            print(f"\nPJM {year} FAILED: {exc}")
            traceback.print_exc()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
