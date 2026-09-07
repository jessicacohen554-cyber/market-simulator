"""miso-234 phase 0 part A (rule 29 clause 0) — WHAT KIND OF OBJECT is MISO's
South seam? Zero LP.

The miso-233 lever queue's item 1 says the South seam is now the largest single
contributor to the residual price-decile slope (reconstructed -919 / -1,135 /
-827 MW against a measured +72 / +60 / +646) and asks, BEFORE any mechanism is
proposed: *is the MISO-South seam even a price-arbitrage seam?*

This probe answers that from the measured record alone, on every price basis the
repo actually holds, and it does so PER COUNTERPARTY (the seam is a pool of five
DIBAs and miso-182 measured that TVA carries 79-86 % of gross export while MISO
is a NET IMPORTER from SOCO).

Bases tested (all measured, all committed):
  * ``hub_da``    MISO Indiana-hub DA  — the basis MISO_SEAM_LADDER_BY_YEAR was
                  Q-Q derived against, and the price the model's decile slope is
                  scored on.
  * ``south_da``  MISO-South zonal DA (mean of ARKANSAS/LOUISIANA/MS/TEXAS hubs)
                  — the price at the bus the seam physically terminates on, and
                  the price the model's own ``MISO_external_South`` bus tracks
                  once ``miso_south_seam_split`` is armed (which the keeper has).
  * ``spread``    hub_da - south_da — the internal North-South separation the
                  RDT prices.
  * ``south_rt``  MISO-South zonal RT (miso-184 tested a DA/RT rebasis and
                  refused it; carried here only as a reported basis).

It also measures the MODEL side from the keeper's committed sidecars: the
``MISO_external_South`` P1 price distribution against the measured South zonal
DA, because a seam whose ladder is fine can still respond wrongly if the bus
price it clears against is distributed unlike the real one.

Usage: python3 scripts/probes/_miso234_south_seam_character_phase0.py
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
OUT = REPO / "results/calibration/_miso234_south_seam_character_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
_MONTH_START_HOUR = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def decile_slope(x: np.ndarray, basis: np.ndarray) -> float:
    """Mean of x in the CHEAPEST basis decile minus the mean in the dearest."""
    ok = np.isfinite(basis) & np.isfinite(x)
    order = np.argsort(basis[ok], kind="stable")
    parts = np.array_split(order, 10)
    xx = x[ok]
    return float(xx[parts[0]].mean() - xx[parts[-1]].mean())


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    ra = pd.Series(a[ok]).rank().to_numpy()
    rb = pd.Series(b[ok]).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1])


def per_diba_export() -> pd.DataFrame:
    """Hourly EXPORT-positive MW per South DIBA on the LP's (year, hour) clock."""
    from market_sim.config.interchange_config import MISO_SEAM_DIBA
    from market_sim.config.paths import RAW_DIR

    ix = pd.read_parquet(RAW_DIR / "eia-930-interchange" / "MISO interchange hourly.parquet")
    t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in t.dt.month])
    hr = base + (t.dt.day.to_numpy() - 1) * 24 + t.dt.hour.to_numpy()
    ix = ix.assign(year=t.dt.year.to_numpy(), hour=hr)
    ix.loc[(t.dt.month == 2) & (t.dt.day == 29), "hour"] = -1
    ix = ix[(ix["hour"] >= 0) & (ix["hour"] < HOURS)]
    ix = ix[ix["diba"].astype(str).isin(MISO_SEAM_DIBA["South"])]
    # EIA sign: + = MISO exports to the DIBA. Keep export-positive.
    return ix.pivot_table(
        index=["year", "hour"], columns="diba", values="mw", aggfunc="sum", observed=True
    )


def zonal_prices() -> pd.DataFrame:
    z = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet")
    z = z[z["zone"] == "MISO-South"]
    return z.groupby(["year", "hour"])[["da", "rt"]].mean()


def main() -> int:
    from market_sim.config.interchange_config import MISO_SEAM_DIBA

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()          # import-positive per seam + MISO hub da/rt
    dibas = per_diba_export()
    south_z = zonal_prices()

    report: dict[str, object] = {
        "probe": "miso-234 phase 0 part A — what kind of object is the South seam",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "sign_convention": "EXPORT-POSITIVE MW (MISO -> the southern DIBA pool)",
        "years": {},
    }
    years_out: dict[str, object] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        # Pooled seam, flipped to export-positive.
        exp_meas = -(
            gy["South"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        )
        hub_da = gy["da"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill().to_numpy(float)
        sz = south_z.loc[year].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill()
        south_da = sz["da"].to_numpy(float)
        south_rt = sz["rt"].to_numpy(float)
        spread = hub_da - south_da

        bases = {
            "hub_da": hub_da,
            "south_da": south_da,
            "south_rt": south_rt,
            "spread_hub_minus_south": spread,
        }

        # ---- 1. level and firmness of the pooled measured export ----------
        q = {f"p{int(p*100)}": round(float(np.quantile(exp_meas, p)), 1)
             for p in (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)}
        d_abs = np.abs(np.diff(exp_meas))
        firmness = {
            "mean_mw": round(float(exp_meas.mean()), 1),
            "std_mw": round(float(exp_meas.std()), 1),
            "cv": round(float(exp_meas.std() / abs(exp_meas.mean())), 3),
            "quantiles_mw": q,
            "pct_hours_exporting": round(float(100 * (exp_meas > 0).mean()), 1),
            "always_exported_base_p10_mw": q["p10"],
            "base_share_of_mean": round(float(q["p10"] / exp_meas.mean()), 3),
            "lag1_autocorr": round(float(pearson(exp_meas[:-1], exp_meas[1:])), 3),
            "lag24_autocorr": round(float(pearson(exp_meas[:-24], exp_meas[24:])), 3),
            "mean_abs_hourly_change_mw": round(float(d_abs.mean()), 1),
            "hourly_change_as_pct_of_mean": round(float(100 * d_abs.mean() / abs(exp_meas.mean())), 1),
        }
        # between-month vs within-month variance share (a contract steps monthly)
        month = np.repeat(np.arange(12), np.diff(np.append(_MONTH_START_HOUR, HOURS)) // 1)
        month = np.concatenate([np.full(int(n), i) for i, n in
                                enumerate(np.diff(np.append(_MONTH_START_HOUR, HOURS)))])
        mm = pd.Series(exp_meas).groupby(month).transform("mean").to_numpy()
        firmness["between_month_variance_share"] = round(
            float(np.var(mm) / np.var(exp_meas)), 3
        )

        # ---- 2. price responsiveness of the pooled measured export --------
        resp = {}
        for bname, b in bases.items():
            resp[bname] = {
                "pearson_r": round(pearson(exp_meas, b), 3),
                "spearman_rho": round(spearman(exp_meas, b), 3),
                "decile_slope_cheap_minus_dear_mw": round(decile_slope(exp_meas, b), 1),
                "basis_mean": round(float(np.nanmean(b)), 2),
                "basis_p10_p90": [round(float(np.nanquantile(b, 0.1)), 2),
                                  round(float(np.nanquantile(b, 0.9)), 2)],
            }

        # ---- 3. per-DIBA decomposition ------------------------------------
        per = {}
        dy = dibas.loc[year].reindex(range(HOURS))
        for d in MISO_SEAM_DIBA["South"]:
            if d not in dy.columns:
                per[d] = {"present": False}
                continue
            x = dy[d].interpolate(limit=3).ffill().bfill().to_numpy(float)
            gross_exp = float(np.clip(x, 0, None).sum())
            gross_imp = float(np.clip(-x, 0, None).sum())
            per[d] = {
                "present": True,
                "net_export_mean_mw": round(float(x.mean()), 1),
                "gross_export_TWh": round(gross_exp / 1e6, 3),
                "gross_import_TWh": round(gross_imp / 1e6, 3),
                "pct_hours_exporting": round(float(100 * (x > 0).mean()), 1),
                "cv_of_net": round(float(x.std() / abs(x.mean())) if x.mean() else float("nan"), 3),
                "p10_mw": round(float(np.quantile(x, 0.10)), 1),
                "spearman_vs_hub_da": round(spearman(x, hub_da), 3),
                "spearman_vs_south_da": round(spearman(x, south_da), 3),
                "spearman_vs_spread": round(spearman(x, spread), 3),
                "decile_slope_vs_hub_da_mw": round(decile_slope(x, hub_da), 1),
                "decile_slope_vs_south_da_mw": round(decile_slope(x, south_da), 1),
            }
        tot_gross_exp = sum(v["gross_export_TWh"] for v in per.values() if v.get("present"))
        for d, v in per.items():
            if v.get("present"):
                v["share_of_gross_export_pct"] = round(
                    100 * v["gross_export_TWh"] / tot_gross_exp, 1
                )

        # ---- 4. model side: the bus the South ladder clears against -------
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus = (sysf[sysf["zone"] == "MISO_external_South"].sort_values("hour")["price"]
               .to_numpy(float))
        zone_s = (sysf[sysf["zone"] == "MISO-South"].sort_values("hour")["price"]
                  .to_numpy(float))
        model_bus = {
            "external_south_bus_mean": round(float(bus.mean()), 2),
            "external_south_bus_p10_p90": [round(float(np.quantile(bus, 0.1)), 2),
                                           round(float(np.quantile(bus, 0.9)), 2)],
            "external_south_bus_std": round(float(bus.std()), 2),
            "miso_south_zone_mean": round(float(zone_s.mean()), 2),
            "miso_south_zone_std": round(float(zone_s.std()), 2),
            "measured_south_da_mean": round(float(south_da.mean()), 2),
            "measured_south_da_std": round(float(south_da.std()), 2),
            "corr_bus_vs_measured_south_da": round(pearson(bus, south_da), 3),
            "corr_bus_vs_measured_hub_da": round(pearson(bus, hub_da), 3),
        }
        # How many export bands are in-merit at the bus price, per decile of the
        # SCORED basis (measured Indiana hub DA)?  This is the model's own
        # mechanism, read off its own artifacts.
        from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
        from market_sim.model.interchange.spec import MISO_SEAM_LADDER_BY_YEAR

        lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year]["South"]["export"], float)
        nbands = (bus[None, :] < lade[:, None]).sum(0).astype(float)
        model_bus["export_bands_in_merit_mean"] = round(float(nbands.mean()), 2)
        model_bus["export_bands_in_merit_decile_slope"] = round(
            decile_slope(nbands, hub_da), 2
        )
        model_bus["export_ladder_top_band_price"] = float(lade[-1])
        model_bus["export_ladder_base_band_price"] = float(lade[0])
        model_bus["pct_hours_bus_below_top_band"] = round(
            float(100 * (bus < lade[-1]).mean()), 1
        )
        model_bus["pct_hours_bus_below_base_band"] = round(
            float(100 * (bus < lade[0]).mean()), 1
        )

        years_out[str(year)] = {
            "measured_pooled_export": firmness,
            "measured_price_response": resp,
            "measured_per_diba": per,
            "model_south_bus": model_bus,
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        y = years_out[str(year)]
        f = y["measured_pooled_export"]
        print(f"================== {year}  MEASURED South seam (export-positive) ==================")
        print(f"  mean {f['mean_mw']:.0f} MW   cv {f['cv']:.2f}   exporting {f['pct_hours_exporting']:.0f}% of hours"
              f"   p10 base {f['always_exported_base_p10_mw']:.0f} MW ({100*f['base_share_of_mean']:.0f}% of mean)")
        print(f"  quantiles {f['quantiles_mw']}")
        print(f"  lag1 acf {f['lag1_autocorr']:+.2f}  lag24 acf {f['lag24_autocorr']:+.2f}"
              f"  mean |Dh| {f['mean_abs_hourly_change_mw']:.0f} MW ({f['hourly_change_as_pct_of_mean']:.0f}% of mean)"
              f"  between-month var share {f['between_month_variance_share']:.2f}")
        print("  price response:")
        for b, r in y["measured_price_response"].items():
            print(f"    {b:<24} pearson {r['pearson_r']:+.3f}  spearman {r['spearman_rho']:+.3f}"
                  f"  decile slope {r['decile_slope_cheap_minus_dear_mw']:+8.1f} MW"
                  f"   (basis mean {r['basis_mean']:.1f})")
        print("  per DIBA:")
        print(f"    {'diba':<6} {'net MW':>8} {'grossE TWh':>11} {'grossI TWh':>11} {'%exp h':>7}"
              f" {'shareE%':>8} {'rho hub':>8} {'rho south':>10} {'slope hub':>10}")
        for d, v in y["measured_per_diba"].items():
            if not v.get("present"):
                print(f"    {d:<6} ABSENT")
                continue
            print(f"    {d:<6} {v['net_export_mean_mw']:>8.0f} {v['gross_export_TWh']:>11.3f}"
                  f" {v['gross_import_TWh']:>11.3f} {v['pct_hours_exporting']:>7.0f}"
                  f" {v['share_of_gross_export_pct']:>8.1f} {v['spearman_vs_hub_da']:>+8.3f}"
                  f" {v['spearman_vs_south_da']:>+10.3f} {v['decile_slope_vs_hub_da_mw']:>+10.1f}")
        m = y["model_south_bus"]
        print("  MODEL South bus (keeper committed sidecars):")
        print(f"    external_South bus  mean {m['external_south_bus_mean']:.2f}  std {m['external_south_bus_std']:.2f}"
              f"  p10/p90 {m['external_south_bus_p10_p90']}")
        print(f"    MISO-South zone     mean {m['miso_south_zone_mean']:.2f}  std {m['miso_south_zone_std']:.2f}")
        print(f"    measured South DA   mean {m['measured_south_da_mean']:.2f}  std {m['measured_south_da_std']:.2f}"
              f"   corr(bus, measured South DA) {m['corr_bus_vs_measured_south_da']:+.3f}")
        print(f"    export bands in merit: mean {m['export_bands_in_merit_mean']:.2f} of 8,"
              f" decile slope {m['export_bands_in_merit_decile_slope']:+.2f} bands")
        print(f"    ladder base ${m['export_ladder_base_band_price']:.2f} / top ${m['export_ladder_top_band_price']:.2f};"
              f" bus below base in {m['pct_hours_bus_below_base_band']:.0f}% of hours,"
              f" below top in {m['pct_hours_bus_below_top_band']:.0f}%")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
