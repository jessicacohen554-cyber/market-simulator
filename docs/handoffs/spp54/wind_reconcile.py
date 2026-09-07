"""SPP-54 design (C) — the SPP-57b R-18 wind reconciliation (PRECOMMIT-spp-54 §4), zero LP.

Builds the LP's wind bound through the real path (renewables._eia860_monthly_capacity ->
_forecast_uncurtailed_cf -> _wind_zone_reanalysis_shapes -> _distribute_by_eia860) for the
THREE-zone map and the rebuilt shapes, and beside it the TWO-zone baseline (HEAD's committed
two-zone parquets, the South = South + SPS capacity), then grades:

  C-1  the redistribution identity  Sum_z cap_z cf_z(t) == M(t) == delivered_EIA930(t) / (1 - r_ref)
       (relative, every hour, all three years; STOP > 1e-9)
  C-2  every cf <= 1 and no water-filling overflow lost (STOP if any)
  C-3  the Dec-21-2025 window (h8496-h8520) per zone: wind potential two-zone vs three-zone
       (the regional feasibility arithmetic itself needs demand + thermal, which census.py
       prints for the same hours)
  C-4  attribution of the North's change, three-zone minus two-zone, annual and in the window,
       against a counterfactual in which the SPS zone keeps the OLD South shape

usage: uv run python docs/handoffs/spp54/wind_reconcile.py <two_zone_parquet_dir>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path("/home/user/market-simulator")
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import renewables as rn  # noqa: E402
from market_sim.data.eia930.actuals import load_eia_hourly_renewable_gen  # noqa: E402

two_zone_dir = Path(sys.argv[1])
ZONES3 = list(get_iso_config("SPP").zone_names)  # North, South, SPS
ZONES2 = ["SPP-North", "SPP-South"]
iN, iS, iP = (ZONES3.index(z) for z in ("SPP-North", "SPP-South", "SPP-SPS"))
cfg = ScenarioConfig(iso="SPP", mode="backcast")
WINDOW = range(
    8496, 8521
)  # 2025-12-21 00:00 -> 12-22 00:00 local (h8507 = 12-21 11:00)
rate, rate_year = rn._reference_curtailment_rate("SPP", "wind")
print(
    f"reference curtailment rate {rate:.6f} (gross-up {1 / (1 - rate):.6f}), source year {rate_year}"
)
rows = []
window_rows = []
verdict = True
for year in (2023, 2024, 2025):
    monthly3 = rn._eia860_monthly_capacity("SPP", "wind", ZONES3, year)
    cf_profile = rn._forecast_uncurtailed_cf("SPP", year, "wind", monthly3)
    installed = float(monthly3[:, -1].sum())
    shapes3 = rn._wind_zone_reanalysis_shapes("SPP", "wind", ZONES3, year, config=cfg)
    assert shapes3 is not None and shapes3.shape == (3, HOURS_PER_YEAR)
    cf3, cap3 = rn._distribute_by_eia860(cf_profile, installed, monthly3, True, shapes3)
    cf_flat, _ = rn._distribute_by_eia860(cf_profile, installed, monthly3, True, None)
    M = (cap3[:, None] * cf_flat).sum(axis=0)
    # the measured EIA-930 SWPP delivered wind, grossed up (the charter's reconciliation target)
    delivered = load_eia_hourly_renewable_gen("SPP", year)["wind"]
    M_meas = delivered / (1.0 - rate)
    # two-zone baseline: HEAD's committed parquets, South capacity = South + SPS
    monthly2 = np.vstack([monthly3[iN], monthly3[iS] + monthly3[iP]])
    shapes2 = rn._wind_zone_reanalysis_shapes(
        "SPP", "wind", ZONES2, year, data_dir=two_zone_dir, config=cfg
    )
    assert shapes2 is not None
    cf2, cap2 = rn._distribute_by_eia860(cf_profile, installed, monthly2, True, shapes2)
    # counterfactual: three zones, but the SPS zone keeps the OLD South shape (C-4 attribution)
    shapes3b = shapes3.copy()
    shapes3b[iP] = shapes2[1]
    cf3b, _ = rn._distribute_by_eia860(cf_profile, installed, monthly3, True, shapes3b)

    W3 = cap3[:, None] * cf3
    W2 = cap2[:, None] * cf2
    W3b = cap3[:, None] * cf3b
    tot3 = W3.sum(axis=0)
    tot2 = W2.sum(axis=0)
    rel3 = np.abs(tot3 - M) / np.maximum(M, 1.0)
    rel2 = np.abs(tot2 - M) / np.maximum(M, 1.0)
    relm = np.abs(tot3 - M_meas) / np.maximum(M_meas, 1.0)
    clip_hours = int((np.abs(M - M_meas) > 1e-6 * np.maximum(M_meas, 1.0)).sum())
    lost3 = int((tot3 < M - 1e-6).sum())
    c1 = bool(rel3.max() <= 1e-9)
    c2 = bool((cf3 <= 1.0 + 1e-12).all() and lost3 == 0)
    verdict &= c1 and c2
    hod = np.arange(HOURS_PER_YEAR) % 24
    night = shapes3[:, (hod >= 0) & (hod < 6)].mean(axis=1)
    aft = shapes3[:, (hod >= 12) & (hod < 18)].mean(axis=1)
    dN = W3[iN] - W2[0]
    dN_shape = W3[iN] - W3b[iN]
    print(f"\n===== {year} =====")
    print(
        f"cap3 {dict(zip(ZONES3, cap3.round(1)))}  cap2 {dict(zip(ZONES2, cap2.round(1)))}  installed {installed:.1f} MW"
    )
    print(
        f"C-1 identity: max rel |sum_z cap cf3 - M| {rel3.max():.3e} (two-zone {rel2.max():.3e}); "
        f"vs delivered/(1-r): max rel {relm.max():.3e}, hours where M != delivered/(1-r) beyond 1e-6 (the CF clip) {clip_hours}; "
        f"annual M {M.sum() / 1e6:.4f} TWh = delivered {delivered.sum() / 1e6:.4f} x {1 / (1 - rate):.6f} -> {'PASS' if c1 else 'STOP'}"
    )
    print(
        f"C-2 feasibility: max cf3 {cf3.max():.6f}; hours with lost overflow {lost3}; "
        f"per-zone max cf {dict(zip(ZONES3, cf3.max(axis=1).round(4)))} -> {'PASS' if c2 else 'STOP'}"
    )
    print(
        f"night/afternoon ratio {dict(zip(ZONES3, (night / aft).round(3)))}; "
        f"shape corr N-S {np.corrcoef(shapes3[iN], shapes3[iS])[0, 1]:.3f}, N-SPS {np.corrcoef(shapes3[iN], shapes3[iP])[0, 1]:.3f}, S-SPS {np.corrcoef(shapes3[iS], shapes3[iP])[0, 1]:.3f}"
    )
    print(
        f"annual potential TWh three-zone {dict(zip(ZONES3, (W3.sum(axis=1) / 1e6).round(3)))}; "
        f"two-zone {dict(zip(ZONES2, (W2.sum(axis=1) / 1e6).round(3)))}; "
        f"South+SPS three-zone {(W3[iS].sum() + W3[iP].sum()) / 1e6:.3f}"
    )
    print(
        f"C-4 North change (three-zone minus two-zone): annual {dN.sum() / 1e3:+.1f} GWh; mean |.| {np.abs(dN).mean():.1f} MW; "
        f"p1/p99 {np.percentile(dN, 1):+.0f}/{np.percentile(dN, 99):+.0f} MW; of which the SPS-shape replacement alone "
        f"{dN_shape.sum() / 1e3:+.1f} GWh (mean |.| {np.abs(dN_shape).mean():.1f} MW); residual (the South's own 6-site set changing) "
        f"{(dN - dN_shape).sum() / 1e3:+.1f} GWh"
    )
    rows.append(
        {
            "year": year,
            "rel_identity_max": float(rel3.max()),
            "rel_vs_delivered_max": float(relm.max()),
            "lost_overflow_hours": lost3,
            "max_cf": float(cf3.max()),
            "north_delta_gwh": float(dN.sum() / 1e3),
            "north_delta_shape_gwh": float(dN_shape.sum() / 1e3),
            "c1": c1,
            "c2": c2,
        }
    )
    if year == 2025:
        print(
            "\nC-3 Dec-21-2025 window, wind potential MW (two-zone South = South+SPS):"
        )
        print(
            "  h    M(t)   N_3z    S_3z   SPS_3z | N_2z    S_2z  | dN(3z-2z) | region S+SPS 3z vs 2z"
        )
        for h in WINDOW:
            print(
                f"  {h} {M[h]:7.0f} {W3[iN, h]:7.0f} {W3[iS, h]:7.0f} {W3[iP, h]:7.0f} | {W2[0, h]:7.0f} {W2[1, h]:7.0f} | "
                f"{dN[h]:+8.0f} | {W3[iS, h] + W3[iP, h]:7.0f} vs {W2[1, h]:7.0f} ({W3[iS, h] + W3[iP, h] - W2[1, h]:+.0f})"
            )
            window_rows.append(
                {
                    "hour": h,
                    "M_mw": float(M[h]),
                    "north_3z": float(W3[iN, h]),
                    "south_3z": float(W3[iS, h]),
                    "sps_3z": float(W3[iP, h]),
                    "north_2z": float(W2[0, h]),
                    "south_2z": float(W2[1, h]),
                }
            )
pd.DataFrame(rows).to_csv(REPO / "docs/handoffs/spp54/wind_reconcile.csv", index=False)
pd.DataFrame(window_rows).to_csv(
    REPO / "docs/handoffs/spp54/dec21_window_2025_wind.csv", index=False
)
print(f"\n===== C-1/C-2 over all years: {'PASS' if verdict else 'STOP'} =====")
