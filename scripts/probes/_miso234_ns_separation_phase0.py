"""miso-234 phase 0 part B (rule 29 clause 0) — is the South seam's wrong-signed
decile slope a SEAM defect, or an inherited symptom of the model's North-South
price separation? Zero LP.

Part A measured that the MEASURED South seam responds to the MISO-SOUTH LOCAL
price with the correct arbitrage sign (spearman -0.19 / -0.18 / -0.00 vs
south_da, decile slope +323 / +427 / -236 MW export-positive) and is FLAT on the
MISO Indiana hub basis the residual is scored on (-125 / -10 / -636). The model's
South seam, by contrast, carries a +913 / +1,096 / +819 MW export slope on that
same Indiana basis.

The candidate explanation is not the ladder and not the anchor: it is that the
MODEL's MISO-South price is a near-copy of its Midwest price, so anything the
South seam clears on inherits the Midwest price's decile structure. Part A's
corroboration: corr(model South bus, measured SOUTH DA) = corr(model South bus,
measured HUB DA) to within 0.06 in every year -- the model's South price carries
no independent South information at all.

This part measures the separation directly, model against measured, and then
asks the decisive counterfactual with no solve: how much of the model's South
export decile slope survives if the SAME ladder and the SAME envelope are
cleared against a South bus price carrying the MEASURED North-South separation?

Usage: python3 scripts/probes/_miso234_ns_separation_phase0.py
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

KEEPER = REPO / "results/calibration/miso233_sppseam_K"
OUT = REPO / "results/calibration/_miso234_ns_separation_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760


def decile_slope(x: np.ndarray, basis: np.ndarray) -> float:
    ok = np.isfinite(basis) & np.isfinite(x)
    order = np.argsort(basis[ok], kind="stable")
    parts = np.array_split(order, 10)
    xx = x[ok]
    return float(xx[parts[0]].mean() - xx[parts[-1]].mean())


def pearson(a, b):
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def main() -> int:
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import MISO_SEAM_LADDER_BY_YEAR

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    z = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet")
    meas_south = z[z["zone"] == "MISO-South"].groupby(["year", "hour"])["da"].mean()
    meas_ind = z[z["zone"] == "MISO-Indiana"].groupby(["year", "hour"])["da"].mean()

    report = {
        "probe": "miso-234 phase 0 part B — North-South separation, model vs measured",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "years": {},
    }
    years_out = {}

    for year in YEARS:
        gy = g_all.loc[year]
        exp_meas = -(gy["South"].reindex(range(HOURS)).interpolate(limit=3)
                     .ffill().bfill().to_numpy(float))
        m_s = meas_south.loc[year].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        m_i = meas_ind.loc[year].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        meas_sep = m_i - m_s

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        pz = {zn: sysf[sysf["zone"] == zn].sort_values("hour")["price"].to_numpy(float)
              for zn in sysf["zone"].unique()}
        mod_i, mod_s = pz["MISO-Indiana"], pz["MISO-South"]
        bus = pz["MISO_external_South"]
        mod_sep = mod_i - mod_s

        sep = {
            "measured_mean_sep": round(float(meas_sep.mean()), 2),
            "measured_mean_abs_sep": round(float(np.abs(meas_sep).mean()), 2),
            "measured_std_sep": round(float(meas_sep.std()), 2),
            "measured_p90_abs_sep": round(float(np.quantile(np.abs(meas_sep), 0.9)), 2),
            "measured_corr_indiana_south": round(pearson(m_i, m_s), 3),
            "model_mean_sep": round(float(mod_sep.mean()), 2),
            "model_mean_abs_sep": round(float(np.abs(mod_sep).mean()), 2),
            "model_std_sep": round(float(mod_sep.std()), 2),
            "model_p90_abs_sep": round(float(np.quantile(np.abs(mod_sep), 0.9)), 2),
            "model_corr_indiana_south": round(pearson(mod_i, mod_s), 3),
            "sep_compression_ratio_meanabs": round(
                float(np.abs(mod_sep).mean() / np.abs(meas_sep).mean()), 3
            ),
        }

        # --- the decisive zero-LP counterfactual --------------------------
        # Same ladder, same envelope, same band grid. ONLY the bus price the
        # export bands clear against is replaced by a South price carrying the
        # MEASURED separation: p_cf(t) = model Indiana price - measured (I - S).
        # This holds the model's own Midwest price level fixed (so it is not a
        # level shift of the whole system) and injects only the separation the
        # model is missing. It is a DIAGNOSTIC, never a mechanism.
        bus_cf = mod_i - meas_sep

        lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"]["export"], float)
        ladi = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"]["import"], float)
        width = 3000.0 / SEAM_FLOW_TRANCHES
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        env_e = np.asarray(measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True)["South"], float)
        env_i = np.asarray(measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True)["South"], float)
        band_e = np.clip(env_e[None, :] - ks * width, 0.0, width)
        band_i = np.clip(env_i[None, :] - ks * width, 0.0, width)

        def seam_net(p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
            exp = ((p[None, :] < lade[:, None]) * band_e).sum(0)
            imp = ((p[None, :] > ladi[:, None]) * band_i).sum(0)
            return exp, imp

        exp_base, imp_base = seam_net(bus)
        exp_cf, imp_cf = seam_net(bus_cf)

        cf = {
            "basis_for_deciles": "measured MISO Indiana-hub DA (the scored basis)",
            "model_bus_export_mean_mw": round(float(exp_base.mean()), 1),
            "model_bus_export_slope_mw": round(decile_slope(exp_base, m_i), 1),
            "cf_bus_export_mean_mw": round(float(exp_cf.mean()), 1),
            "cf_bus_export_slope_mw": round(decile_slope(exp_cf, m_i), 1),
            "measured_export_mean_mw": round(float(exp_meas.mean()), 1),
            "measured_export_slope_mw": round(decile_slope(exp_meas, m_i), 1),
            "model_bus_net_slope_mw": round(decile_slope(imp_base - exp_base, m_i), 1),
            "cf_bus_net_slope_mw": round(decile_slope(imp_cf - exp_cf, m_i), 1),
            "measured_net_slope_mw": round(decile_slope(-exp_meas, m_i), 1),
            "cf_bus_mean": round(float(bus_cf.mean()), 2),
            "cf_bus_std": round(float(bus_cf.std()), 2),
            "model_bus_mean": round(float(bus.mean()), 2),
            "model_bus_std": round(float(bus.std()), 2),
        }
        cf["slope_gap_closed_pct"] = round(
            100.0
            * (cf["model_bus_export_slope_mw"] - cf["cf_bus_export_slope_mw"])
            / (cf["model_bus_export_slope_mw"] - cf["measured_export_slope_mw"]),
            1,
        )
        years_out[str(year)] = {"separation": sep, "counterfactual": cf}

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        y = years_out[str(year)]
        s, c = y["separation"], y["counterfactual"]
        print(f"====================== {year} ======================")
        print("  North-South price separation (Indiana - South), $/MWh:")
        print(f"    MEASURED  mean {s['measured_mean_sep']:+7.2f}   mean|.| {s['measured_mean_abs_sep']:6.2f}"
              f"   std {s['measured_std_sep']:6.2f}   p90|.| {s['measured_p90_abs_sep']:6.2f}"
              f"   corr(I,S) {s['measured_corr_indiana_south']:+.3f}")
        print(f"    MODEL     mean {s['model_mean_sep']:+7.2f}   mean|.| {s['model_mean_abs_sep']:6.2f}"
              f"   std {s['model_std_sep']:6.2f}   p90|.| {s['model_p90_abs_sep']:6.2f}"
              f"   corr(I,S) {s['model_corr_indiana_south']:+.3f}")
        print(f"    compression (model mean|.| / measured mean|.|) = {s['sep_compression_ratio_meanabs']:.3f}")
        print("  Zero-LP counterfactual — same ladder, same envelope, South bus")
        print("  re-priced with the MEASURED separation (diagnostic, not a mechanism):")
        print(f"    export mean MW   model {c['model_bus_export_mean_mw']:8.1f} ->"
              f" cf {c['cf_bus_export_mean_mw']:8.1f}   (measured {c['measured_export_mean_mw']:8.1f})")
        print(f"    export slope MW  model {c['model_bus_export_slope_mw']:+8.1f} ->"
              f" cf {c['cf_bus_export_slope_mw']:+8.1f}   (measured {c['measured_export_slope_mw']:+8.1f})")
        print(f"    net slope MW     model {c['model_bus_net_slope_mw']:+8.1f} ->"
              f" cf {c['cf_bus_net_slope_mw']:+8.1f}   (measured {c['measured_net_slope_mw']:+8.1f})")
        print(f"    => {c['slope_gap_closed_pct']:.1f} % of the export-slope gap closed by separation alone")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
