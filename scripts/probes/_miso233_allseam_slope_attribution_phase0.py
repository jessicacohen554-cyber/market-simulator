"""miso-233 phase 0, part B (rule 29 clause 0) — the seam decile slope,
attributed PER SEAM. Zero LP.

Part A (``_miso233_seam_slope_anatomy_phase0.py``) measured the PJM seam's own
decile slope under the miso-232 keeper's hourly ladder and found it ALREADY
STEEPER than the measured PJM seam in every year (+2,377 / +2,611 / +2,704 MW
reconstructed against a measured +1,319 / +1,052 / +815), with the cheapest
decile losing only 194-271 MW to the deliverability envelope. So the queue's
named hypothesis — that the DEEP PJM bands (k = 6-8) under-clear in MISO's cheap
hours and cost the slope its magnitude — is not what the keeper's own artifacts
say. Something else is cancelling a slope the PJM seam already has.

This part reconstructs EVERY priced seam on the same static instrument and adds
them up, so the published total slope (+139 / +111 / +681 MW) is decomposed into
per-seam contributions that sum to it.

    PJM       hourly neighbour ladder   pi_k(t) = border(t) + delta_k   [repaired]
    SPP       incumbent MISO-hub Q-Q ladder, FIXED annual prices        [not repaired]
    South     incumbent MISO-hub Q-Q ladder, FIXED annual prices        [not repaired]

A fixed ladder cleared against the model's own bus price imports MORE when MISO
is EXPENSIVE — the exact defect miso-226 named and the hourly form repaired on
PJM. If SPP and South still carry it, their contribution to the slope is
NEGATIVE and cancels PJM's repair. That is the hypothesis this part tests, and
it is testable with no solve at all.

Usage: python3 scripts/probes/_miso233_allseam_slope_attribution_phase0.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

KEEPER = REPO / "results/calibration/miso232_hourlyseam_K"
OUT = REPO / "results/calibration/_miso233_allseam_slope_attribution_phase0.json"
YEARS = (2023, 2024, 2025)
ZONE = "MISO-Indiana"
HOURS = 8760
# split_miso_south_external_node re-homes the South seam onto its own external
# bus (the keeper runs miso_south_seam_split=True); PJM and SPP stay on
# MISO_external.
BUS_OF_SEAM = {"PJM": "MISO_external", "SPP": "MISO_external", "South": "MISO_external_South"}


def decile_masks(price: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    d1 = np.zeros(price.size, bool)
    d10 = np.zeros(price.size, bool)
    d1[parts[0]] = True
    d10[parts[-1]] = True
    return d1, d10


def main() -> int:
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
    )
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}

    report: dict[str, object] = {
        "probe": "miso-233 phase 0 part B — decile slope attributed per seam",
        "keeper": "2026-09-06-miso-232-hourly-seam",
        "zero_lp": True,
        "years": {},
    }
    years_out: dict[str, object] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        border = (
            gy["pjm_border"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill()
            .to_numpy(float)
        )
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        committed = (
            cls.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0)
            .to_numpy(float)
        )

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )

        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        d1, d10 = decile_masks(act[ok])

        def dslope(x: np.ndarray) -> float:
            xx = x[ok]
            return float(xx[d1].mean() - xx[d10].mean())

        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        total = np.zeros(HOURS)
        seams_out = {}
        for seam, spec in specs.items():
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            p_bus = bus_price[BUS_OF_SEAM[seam]]
            # --- import direction -----------------------------------------
            if seam == "PJM":
                d_imp = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                in_merit = ((p_bus - border)[None, :] > d_imp[:, None])
                basis = "hourly neighbour ladder: border(t) + delta_k"
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = (p_bus[None, :] > lad[:, None])
                basis = "incumbent FIXED MISO-hub Q-Q ladder"
            cap_i = np.asarray(env_i[seam], float)
            band_i = np.clip(cap_i[None, :] - ks * width, 0.0, width)
            imp = (in_merit * band_i).sum(0)
            # --- export direction (negative output) -----------------------
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            out_merit = (p_bus[None, :] < lade[:, None])
            cap_e = np.asarray(env_e[seam], float)
            band_e = np.clip(cap_e[None, :] - ks * width, 0.0, width)
            exp = (out_merit * band_e).sum(0)
            net = imp - exp
            total += net
            seams_out[seam] = {
                "ladder_basis": basis,
                "interface_limit_mw": float(spec.interface_limit_mw),
                "band_width_mw": round(width, 1),
                "net_mean_mw": round(float(net.mean()), 1),
                "import_mean_mw": round(float(imp.mean()), 1),
                "export_mean_mw": round(float(exp.mean()), 1),
                "net_d1_mw": round(float(net[ok][d1].mean()), 1),
                "net_d10_mw": round(float(net[ok][d10].mean()), 1),
                "slope_net_mw": round(dslope(net), 1),
                "slope_import_mw": round(dslope(imp), 1),
                "slope_export_mw": round(dslope(exp), 1),
                "corr_net_vs_measured_price": round(
                    float(np.corrcoef(net[ok], act[ok])[0, 1]), 3
                ),
            }
            if seam in gy.columns:
                meas = (
                    gy[seam].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill()
                    .to_numpy(float)
                )
                seams_out[seam]["measured_mean_mw"] = round(float(meas.mean()), 1)
                seams_out[seam]["measured_slope_mw"] = round(dslope(meas), 1)
                seams_out[seam]["measured_corr_vs_price"] = round(
                    float(np.corrcoef(meas[ok], act[ok])[0, 1]), 3
                )

        # Manitoba is the firm block (miso_firm_imports), not a priced seam:
        # a constant-shape injection with no price response. Reported from the
        # measured record only.
        meas_mb = (
            gy["Manitoba"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill()
            .to_numpy(float)
        )
        years_out[str(year)] = {
            "seams": seams_out,
            "manitoba_measured_mean_mw": round(float(-meas_mb.mean()), 1),
            "manitoba_measured_slope_mw": round(dslope(-meas_mb), 1),
            "recon_total_mean_mw": round(float(total.mean()), 1),
            "committed_import_mean_mw": round(float(committed.mean()), 1),
            "harness_corr_recon_vs_committed": round(
                float(np.corrcoef(total, committed)[0, 1]), 3
            ),
            "slope_recon_total_mw": round(dslope(total), 1),
            "slope_committed_mw": round(dslope(committed), 1),
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        y = years_out[str(year)]
        print(f"============================== {year} ==============================")
        print(
            f"  harness: recon total {y['recon_total_mean_mw']:.0f} MW vs committed"
            f" {y['committed_import_mean_mw']:.0f} MW, corr"
            f" {y['harness_corr_recon_vs_committed']:+.3f}"
        )
        print(
            f"  SLOPE d1-d10:  recon total {y['slope_recon_total_mw']:+.0f} MW"
            f"   |  committed (published) {y['slope_committed_mw']:+.0f} MW"
        )
        print(
            f"    {'seam':<7} {'ladder':<40} {'net MW':>8} {'slope':>8}"
            f" {'meas MW':>9} {'meas slope':>11}"
        )
        for seam, s in y["seams"].items():
            print(
                f"    {seam:<7} {s['ladder_basis']:<40} {s['net_mean_mw']:>8.0f}"
                f" {s['slope_net_mw']:>+8.0f} {s.get('measured_mean_mw', float('nan')):>9.0f}"
                f" {s.get('measured_slope_mw', float('nan')):>+11.0f}"
            )
        print(
            f"    {'MHEB':<7} {'firm block (not a priced seam)':<40}"
            f" {'—':>8} {'—':>8} {y['manitoba_measured_mean_mw']:>9.0f}"
            f" {y['manitoba_measured_slope_mw']:>+11.0f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
