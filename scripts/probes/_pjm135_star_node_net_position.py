"""pjm-135 M1b/M4 (no LP): the star node's NET position and the simultaneity gap.

Companion to :mod:`_pjm135_star_node_import`. M3 there measured the star node
price-tied to every PJM zone in **100.00 %** of hours, so any single link's flow
is a degenerate vertex choice, not a physical statement. This probe therefore
moves to the two quantities that are **not** degenerate:

* **M4 net position** -- the ``import`` class in the committed
  ``pjm134_control_A/hourly/class_hourly_<year>.parquet`` sidecar is the star
  node's hourly NET injection into PJM (negative = net export), i.e. the model's
  own net interchange. It is compared against PJM's measured net interchange
  (:func:`~market_sim.data.eia_loader.pjm_net_interchange`, the same tie-line
  file the envelope is built from), hour by hour.
* **M1b simultaneity** -- ``pjm_zonal_interchange_envelope`` takes the
  ``PJM_EXTERNAL_FLOW_PERCENTILE`` of each border's import side and of each
  border's export side **independently**. The sum of five marginal 95th
  percentiles is not the 95th percentile of the simultaneous sum, and neither
  the per-link groups (``build_pjm_external_flow_groups``) nor the per-neighbor
  bands (``inject_pjm_seam_flow_limit``) constrain the total. This measures the
  gap, and the double-counting the per-neighbor bands introduce by summing the
  same border rows across overlapping ``border_zones``.

No LP is solved and nothing is written outside ``results/probes/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.eia930.envelopes import (
    pjm_net_interchange,
    pjm_zonal_interchange,
    pjm_zonal_interchange_envelope,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760

ARM_A_DIR = Path("results/calibration/pjm134_control_A")

PJM_ZONES = [
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
]

OUT_PATH = Path("results/probes/pjm135_star_node_net_position.json")


def _bucket_percentile(series: np.ndarray, year: int, pct: float) -> np.ndarray:
    """Return the (month x hour-of-day) ``pct`` of ``series``, tiled over 8760 h.

    Byte-identical bucketing to :func:`pjm_zonal_interchange_envelope`, so the
    simultaneous-total envelope below is the same construction applied to the
    summed series rather than border by border.
    """
    clock = pd.date_range(f"{year}-01-01", periods=HOURS, freq="h")
    month, hod = clock.month.to_numpy(), clock.hour.to_numpy()
    table = np.zeros((12, 24))
    for m in range(1, 13):
        for h in range(24):
            sel = (month == m) & (hod == h)
            if sel.any():
                table[m - 1, h] = float(np.percentile(series[sel], pct))
    return table[month - 1, hod]


def _r2(actual: np.ndarray, predicted: np.ndarray) -> float:
    """Return the coefficient of determination of ``predicted`` against ``actual``."""
    ss_res = float(np.sum((actual - predicted) ** 2))
    ss_tot = float(np.sum((actual - np.mean(actual)) ** 2))
    return float("nan") if ss_tot <= 0 else 1.0 - ss_res / ss_tot


def model_net_injection(year: int) -> np.ndarray | None:
    """Return the model's hourly net star-node injection (MW, import-positive).

    Read from the ``import`` class of the arm-A ``class_hourly`` sidecar (P1,
    the scored pass). The class is the star node's pergen supply, so its signed
    MW is exactly the LP's net interchange: positive = PJM importing.
    """
    path = ARM_A_DIR / "hourly" / f"class_hourly_{year}.parquet"
    if not path.exists():
        return None
    frame = pd.read_parquet(path)
    frame = frame[(frame["pass"] == "P1") & (frame["klass"] == "import")]
    if frame.empty:
        return None
    return frame.sort_values("hour")["mw"].to_numpy(dtype=float)[:HOURS]


def measure(year: int) -> dict:
    """Return the M4 net-position and M1b simultaneity measurements for ``year``."""
    zonal = pjm_zonal_interchange(year, PJM_ZONES)  # export-positive
    env = pjm_zonal_interchange_envelope(
        year, PJM_ZONES, HOURS, PJM_EXTERNAL_FLOW_PERCENTILE
    )
    measured_export = pjm_net_interchange(year)  # export-positive, system total
    assert zonal is not None and env is not None and measured_export is not None
    import_cap, export_cap = env
    pct = PJM_EXTERNAL_FLOW_PERCENTILE

    measured_net_import = -measured_export  # import-positive
    model_net = model_net_injection(year)

    # --- M1b: simultaneity ------------------------------------------------
    # The measured simultaneous totals, hour by hour, across the five border
    # rows the star node actually links to.
    imp_side = np.clip(-zonal, 0.0, None)  # (n_zones, T) measured import side
    exp_side = np.clip(zonal, 0.0, None)
    sim_import = imp_side.sum(axis=0)  # simultaneous gross import
    sim_export = exp_side.sum(axis=0)

    sum_of_marginal_import = import_cap.sum(axis=0)  # the model's aggregate ceiling
    sum_of_marginal_export = export_cap.sum(axis=0)
    sim_import_env = _bucket_percentile(sim_import, year, pct)  # the joint p95
    sim_export_env = _bucket_percentile(sim_export, year, pct)
    net_import_env = _bucket_percentile(measured_net_import, year, pct)

    # Per-neighbor band double-counting: each neighbor's band sums the envelope
    # over its border_zones, and zones appear in more than one neighbor.
    zone_row = {z: i for i, z in enumerate(PJM_ZONES)}
    multiplicity: dict[str, int] = {z: 0 for z in PJM_ZONES}
    for neighbor in INTERFACE_NEIGHBORS.get("PJM", []):
        for zone in neighbor.border_zones:
            if zone in multiplicity:
                multiplicity[zone] += 1
    seam_import_ceiling = sum(
        multiplicity[z] * import_cap[zone_row[z]] for z in PJM_ZONES
    )

    out = {
        "percentile": pct,
        "m1b_simultaneity": {
            "measured_sim_import_mw_mean": float(sim_import.mean()),
            "measured_sim_import_mw_p95": float(np.percentile(sim_import, 95)),
            "measured_sim_export_mw_mean": float(sim_export.mean()),
            "model_sum_of_marginal_import_mw_mean": float(sum_of_marginal_import.mean()),
            "model_sum_of_marginal_export_mw_mean": float(sum_of_marginal_export.mean()),
            "joint_p95_sim_import_mw_mean": float(sim_import_env.mean()),
            "joint_p95_sim_export_mw_mean": float(sim_export_env.mean()),
            "simultaneity_gap_mw": float(
                sum_of_marginal_import.mean() - sim_import_env.mean()
            ),
            "simultaneity_gap_twh": float(
                (sum_of_marginal_import - sim_import_env).sum()
            )
            / 1.0e6,
            "sum_of_marginal_over_joint_p95": float(
                sum_of_marginal_import.mean() / sim_import_env.mean()
            ),
            "border_multiplicity": {
                z: multiplicity[z] for z in PJM_ZONES if multiplicity[z]
            },
            "seam_band_import_ceiling_mw_mean": float(seam_import_ceiling.mean()),
        },
        "m4_net_position": {
            "measured_net_import_mw_mean": float(measured_net_import.mean()),
            "measured_net_import_twh": float(measured_net_import.sum()) / 1.0e6,
            "measured_hours_net_importing_pct": float(
                100.0 * (measured_net_import > 0).mean()
            ),
            "measured_net_import_p95_envelope_mw_mean": float(net_import_env.mean()),
        },
    }

    if model_net is not None and model_net.size == HOURS:
        err = model_net - measured_net_import
        out["m4_net_position"].update(
            {
                "model_net_import_mw_mean": float(model_net.mean()),
                "model_net_import_twh": float(model_net.sum()) / 1.0e6,
                "model_hours_net_importing_pct": float(100.0 * (model_net > 0).mean()),
                "net_error_twh": float(err.sum()) / 1.0e6,
                "net_error_mw_mean": float(err.mean()),
                "net_error_mae_mw": float(np.abs(err).mean()),
                "model_vs_measured_r2": _r2(measured_net_import, model_net),
                "model_vs_measured_corr": float(
                    np.corrcoef(measured_net_import, model_net)[0, 1]
                ),
                "hours_model_above_measured_p95_envelope_pct": float(
                    100.0 * (model_net > net_import_env).mean()
                ),
                "hours_model_above_measured_net_pct": float(
                    100.0 * (model_net > measured_net_import).mean()
                ),
            }
        )
    else:
        out["m4_net_position"]["model_available"] = False
    return out


def main() -> None:
    """Run M1b/M4 for every scored year and write the machine output."""
    out = {
        "probe": "pjm135_star_node_net_position",
        "charter": "FINDING-pjm134-dominion-zonal-inversion-2026-07-27.md §7",
        "no_lp": True,
        "arm_a_dir": str(ARM_A_DIR),
        "years": {},
    }
    for year in YEARS:
        res = measure(year)
        out["years"][str(year)] = res
        s, n = res["m1b_simultaneity"], res["m4_net_position"]
        print(f"\n===== {year} =====")
        print(
            f"  M4 net position   model {n.get('model_net_import_twh', float('nan')):+7.2f} TWh"
            f"   measured {n['measured_net_import_twh']:+7.2f} TWh"
            f"   err {n.get('net_error_twh', float('nan')):+6.2f} TWh"
        )
        print(
            f"     hourly           R2 {n.get('model_vs_measured_r2', float('nan')):+6.3f}"
            f"   corr {n.get('model_vs_measured_corr', float('nan')):+6.3f}"
            f"   MAE {n.get('net_error_mae_mw', float('nan')):7.0f} MW"
            f"   model above measured in {n.get('hours_model_above_measured_net_pct', float('nan')):.1f} % of hours"
        )
        print(
            f"  M1b simultaneity  sum-of-marginal import band {s['model_sum_of_marginal_import_mw_mean']:7.0f} MW"
            f"   joint p{res['percentile']:.0f} of the simultaneous total {s['joint_p95_sim_import_mw_mean']:7.0f} MW"
        )
        print(
            f"                     gap {s['simultaneity_gap_mw']:7.0f} MW"
            f"  ({s['simultaneity_gap_twh']:+.2f} TWh/yr, {s['sum_of_marginal_over_joint_p95']:.2f} x)"
            f"   | measured simultaneous import mean {s['measured_sim_import_mw_mean']:.0f} MW"
        )
        print(
            f"                     per-neighbor seam ceiling {s['seam_band_import_ceiling_mw_mean']:7.0f} MW"
            f"   (border multiplicity {s['border_multiplicity']})"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
