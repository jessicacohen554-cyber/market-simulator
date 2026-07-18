"""DIAGNOSTIC (no LP): verify the GT ambient derate removes hot-hour capacity.

Builds the pjm-90 fleet WITHOUT and WITH ``gt_ambient_derate`` and reports the
CC_REGULAR / CT_PEAKER summer-peak available-MW delta at the hottest hours, to
confirm the mechanism bites where scarcity should occur (and by how much).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

from scripts.run_calibration import run_year  # noqa: E402
from scripts.run_calibration_full import _henry_hub_actual, _load_reference  # noqa: E402
from scripts.archive.run_pjm74_cc_ct_rebalance import BIT_OVERRIDES  # noqa: E402
from scripts.archive.run_pjm75_ct_drag_cc_cap import CONFIG_OVERRIDES, CT_DRAG_OVERRIDES  # noqa: E402
from scripts.archive.run_pjm90_cchp_srmc import _OFFER_OVERRIDES  # noqa: E402

_HOURS = 8760
_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP")


def _fleet(year: int, ambient: bool):
    reference = _load_reference()
    gas_price = _henry_hub_actual(reference, year)
    return run_year(
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
        gt_ambient_derate=ambient,
        fleet_only=True,
    )


def _run(year: int) -> None:
    base = _fleet(year, False)
    amb = _fleet(year, True)
    fb, fa = base["fleet_arrays"], amb["fleet_arrays"]
    demand = np.asarray(base["demand"], float).sum(axis=0)
    groups = np.asarray(fb.plant_group, dtype=object)
    pmax = np.asarray(fb.pmax, float)
    av_b = pmax[:, None] * np.asarray(fb.availability, float)
    av_a = pmax[:, None] * np.asarray(fa.availability, float)
    tot_b = av_b.sum(0)
    tot_a = av_a.sum(0)
    # top-50 load hours of summer (Jun-Sep)
    import pandas as pd

    month = pd.date_range(f"{year}-01-01", periods=_HOURS, freq="h").month.to_numpy()
    summer = np.isin(month, (6, 7, 8, 9))
    top = np.argsort(np.where(summer, demand, -1))[-50:]
    print(f"\n==== PJM {year} — top-50 summer load hours ====")
    print(
        f"  total available: base {tot_b[top].mean() / 1e3:6.2f} GW  "
        f"ambient {tot_a[top].mean() / 1e3:6.2f} GW  "
        f"delta {(tot_a[top] - tot_b[top]).mean() / 1e3:+.2f} GW"
    )
    for grp in _GROUPS:
        m = groups == grp
        if not m.any():
            continue
        gb = av_b[m][:, top].sum(0)
        ga = av_a[m][:, top].sum(0)
        print(
            f"    {grp:12s} base {gb.mean() / 1e3:6.2f} GW  ambient {ga.mean() / 1e3:6.2f} GW  "
            f"delta {(ga - gb).mean() / 1e3:+.3f} GW  (max-hr {(ga - gb).min() / 1e3:+.3f})"
        )
    # single hottest-load hour
    h = int(top[-1])
    print(
        f"  peak hour h{h}: total avail base {tot_b[h] / 1e3:.2f} -> ambient {tot_a[h] / 1e3:.2f} GW "
        f"({(tot_a[h] - tot_b[h]) / 1e3:+.2f} GW), load {demand[h] / 1e3:.2f} GW"
    )


def main() -> int:
    for year in (2024, 2025):
        _run(year)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
