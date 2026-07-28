"""pjm-135 M2b (no LP): per-border star-link band utilisation, from arm A's flows.

The M1/M2 probe (:mod:`_pjm135_star_node_import`) could only compare the
measured tie-line series against the *band* the envelope hands the LP, because
no committed bundle carries flows (``results/calibration/*/*.parquet`` is
gitignored). This probe closes that gap using the arm-A bundle's own
``flows.parquet`` while it exists in the working tree, and answers the two
questions the band comparison could not:

* **Is the band a ceiling the LP clears below, or the schedule itself?**
  Measured: ``PJM_external -> PJM_Dominion`` sits AT its p95 import band in
  92.6 / 93.3 / 76.5 % of hours. It is pinned, not merely near.
* **Would a per-border correction be re-routed?** Measured: the simultaneous
  import headroom (Σ per-border band − Σ positive star flow) averages
  4,224 / 5,317 MW and is **never** zero in any hour of any year — ATSI alone
  runs 1.0-1.5 GW under its band. So yes: tightening one border leaves the LP
  strictly feasible headroom on another at the same dual, which is why pjm-135
  charters an AGGREGATE cut rather than a border re-attribution.

It also verifies the identity the net-position delta rests on: the summed star
flow equals the ``import`` class in the ``hourly/`` sidecar to the MWh, i.e.
``Σ_z Flow(PJM_external -> z)`` really is the LP's net interchange.

No LP is solved. ``flows.parquet`` is a gitignored bundle intermediate, so this
probe runs only in a session that still has the arm on disk; the numbers it
produces are recorded in ``FINDING-pjm135-star-node-import-2026-07-28.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import PJM_EXTERNAL_FLOW_PERCENTILE
from market_sim.config.interchange_config import IMPORT_NODE_LINKS, IMPORT_ZONE
from market_sim.data.eia_loader import (
    pjm_zonal_interchange,
    pjm_zonal_interchange_envelope,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760

ARM = Path("results/calibration/pjm135_control_A")

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

OUT_PATH = Path("results/probes/pjm135_star_flow_utilisation.json")


def _at_bound(flow: np.ndarray, bound: np.ndarray) -> float:
    """Return the share of hours (%) ``flow`` sits at ``bound``.

    Tolerance is 1 MW absolute / 1e-4 relative — tight enough that "at the
    band" means pinned, loose enough to survive simplex round-off.
    """
    return float(100.0 * np.isclose(flow, bound, rtol=1e-4, atol=1.0).mean())


def measure(year: int) -> dict:
    """Return per-border utilisation and simultaneous headroom for ``year``."""
    flows = pd.read_parquet(ARM / "flows.parquet")
    flows = flows[(flows["pass"] == "P1") & (flows["year"] == year)]
    star = flows[flows["from_zone"] == IMPORT_ZONE["PJM"]]

    import_cap, export_cap = pjm_zonal_interchange_envelope(
        year, PJM_ZONES, HOURS, PJM_EXTERNAL_FLOW_PERCENTILE
    )
    measured = np.clip(-pjm_zonal_interchange(year, PJM_ZONES), 0.0, None)
    row = {z: i for i, z in enumerate(PJM_ZONES)}

    borders: dict[str, dict] = {}
    positive_total = np.zeros(HOURS)
    band_total = np.zeros(HOURS)
    for zone, _ttc in IMPORT_NODE_LINKS["PJM"]:
        flow = star[star["to_zone"] == zone].sort_values("hour")["mw"].to_numpy()[:HOURS]
        imp_cap, exp_cap = import_cap[row[zone]], export_cap[row[zone]]
        meas = measured[row[zone]]
        positive_total += np.clip(flow, 0.0, None)
        band_total += imp_cap
        borders[zone] = {
            "mean_mw": float(flow.mean()),
            "twh": float(flow.sum()) / 1.0e6,
            "import_band_mean_mw": float(imp_cap.mean()),
            "export_band_mean_mw": float(exp_cap.mean()),
            "hours_at_import_band_pct": _at_bound(flow, imp_cap),
            "hours_at_export_band_pct": _at_bound(flow, -exp_cap),
            "measured_import_mean_mw": float(meas.mean()),
            "measured_import_twh": float(meas.sum()) / 1.0e6,
            "flow_over_measured": (
                float(flow.mean() / meas.mean()) if meas.mean() > 0 else None
            ),
            "flow_cv": (
                float(flow.std() / abs(flow.mean())) if flow.mean() != 0 else None
            ),
            "measured_cv": float(meas.std() / meas.mean()) if meas.mean() > 0 else None,
            "corr_with_measured_hourly": float(np.corrcoef(flow, meas)[0, 1]),
        }

    headroom = band_total - positive_total
    net = star.groupby("hour")["mw"].sum().sort_index().to_numpy()[:HOURS]

    # Identity check: the summed star flow IS the `import` class.
    klass = pd.read_parquet(ARM / "hourly" / f"class_hourly_{year}.parquet")
    klass = klass[(klass["pass"] == "P1") & (klass["klass"] == "import")]
    imports = klass.sort_values("hour")["mw"].to_numpy()[:HOURS]

    return {
        "borders": borders,
        "simultaneous_import_headroom_mw_mean": float(headroom.mean()),
        "simultaneous_import_headroom_mw_min": float(headroom.min()),
        "hours_zero_headroom_pct": float(100.0 * (headroom < 1.0).mean()),
        "star_net_twh": float(net.sum()) / 1.0e6,
        "import_class_twh": float(imports.sum()) / 1.0e6,
        "identity_max_abs_diff_mw": float(np.abs(net - imports).max()),
    }


def main() -> None:
    """Run M2b for every scored year and write the machine output."""
    if not (ARM / "flows.parquet").exists():
        raise SystemExit(
            f"{ARM}/flows.parquet absent — it is a gitignored bundle intermediate, "
            "so this probe only runs in the session that produced the arm."
        )
    out = {
        "probe": "pjm135_star_flow_utilisation",
        "no_lp": True,
        "arm": str(ARM),
        "years": {str(y): measure(y) for y in YEARS},
    }
    for year in YEARS:
        r = out["years"][str(year)]
        print(f"\n===== {year} =====")
        print(
            f"  {'border':14s} {'mean MW':>9s} {'TWh':>7s} {'imp band':>9s}"
            f" {'at imp':>7s} {'exp band':>9s} {'at exp':>7s}"
        )
        for zone, b in r["borders"].items():
            print(
                f"  {zone:14s} {b['mean_mw']:9.0f} {b['twh']:7.2f}"
                f" {b['import_band_mean_mw']:9.0f} {b['hours_at_import_band_pct']:6.1f}%"
                f" {b['export_band_mean_mw']:9.0f} {b['hours_at_export_band_pct']:6.1f}%"
            )
        print(
            f"  simultaneous import headroom: mean {r['simultaneous_import_headroom_mw_mean']:.0f} MW,"
            f" min {r['simultaneous_import_headroom_mw_min']:.0f} MW,"
            f" zero-headroom hours {r['hours_zero_headroom_pct']:.1f} %"
        )
        print(
            f"  identity  Σ star flow {r['star_net_twh']:+.2f} TWh"
            f" vs `import` class {r['import_class_twh']:+.2f} TWh"
            f"  (max |Δ| {r['identity_max_abs_diff_mw']:.6f} MW)"
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()
