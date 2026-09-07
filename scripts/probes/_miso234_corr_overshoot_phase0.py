"""miso-234 phase 0 part D — WHICH SEAM drives the 2024/2025 correlation
overshoot? Zero LP.

The miso-233 keeper's ``corr(imports, measured price)`` is -0.1095 / -0.1145 /
-0.1128 against a measured -0.136 / -0.039 / -0.059: 2023 improved and is still
short of the measured magnitude, but 2024 and 2025 have gone PAST it. The lever
queue's item 2 asks for that to be attributed before anything is proposed.

Correlation is exactly additive in the numerator, so the attribution is an
identity, not an approximation:

    corr(sum_s x_s, P) = sum_s  cov(x_s, P) / (sigma_total * sigma_P)

Every seam therefore carries a signed CONTRIBUTION to the published correlation
and the contributions sum to it exactly. The same decomposition is run on the
MEASURED seam flows, so the answer is "which seam's response does the model
overshoot", not merely "which seam is most negative".

Both sides use the same reconstruction instrument as
``_miso233_allseam_slope_attribution_phase0.py`` (harness corr vs the committed
import series is reported per year).

Usage: python3 scripts/probes/_miso234_corr_overshoot_phase0.py
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
OUT = REPO / "results/calibration/_miso234_corr_overshoot_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"
BUS_OF_SEAM = {"PJM": "MISO_external", "SPP": "MISO_external", "South": "MISO_external_South"}


def contrib(x: np.ndarray, p: np.ndarray, sigma_total: float) -> float:
    """Signed contribution of x to corr(total, p); contributions sum exactly."""
    return float(np.cov(x, p, bias=True)[0, 1] / (sigma_total * p.std()))


def main() -> int:
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import measured_seam_import_envelope
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_SEAM_LADDER_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
    )
    from _miso224_floor_anatomy_phase0 import actual_zone_price

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()
    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}

    # The SPP seam is on the hourly neighbour anchor in the miso-233 keeper.
    from market_sim.data.eia_loader import measured_miso_spp_hub_prices

    report = {
        "probe": "miso-234 phase 0 part D — corr(imports, measured price) attributed per seam",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "identity": "corr(sum_s x_s, P) = sum_s cov(x_s,P)/(sigma_total*sigma_P)",
        "years": {},
    }
    years_out = {}

    for year in YEARS:
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        p = act[ok]

        border = (gy["pjm_border"].reindex(range(HOURS)).interpolate(limit=3)
                  .ffill().bfill().to_numpy(float))
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
                     for b in set(BUS_OF_SEAM.values())}
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        committed = (cls.groupby("hour")["mw"].sum().reindex(range(HOURS))
                     .fillna(0.0).to_numpy(float))

        env_i = measured_seam_import_envelope("MISO", year, HOURS, None,
                                              direction="import", hour_ending_key=True)
        env_e = measured_seam_import_envelope("MISO", year, HOURS, None,
                                              direction="export", hour_ending_key=True)
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]

        model_net, meas_net = {}, {}
        for seam, spec in specs.items():
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                d = np.asarray(MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"], float)
                in_merit = ((pb - border)[None, :] > d[:, None])
            elif seam == "SPP":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"]["import"],
                    float)
                in_merit = ((pb - spp_hub)[None, :] > d[:, None])
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = (pb[None, :] > lad[:, None])
            band_i = np.clip(np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width)
            imp = (in_merit * band_i).sum(0)
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            band_e = np.clip(np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width)
            exp = ((pb[None, :] < lade[:, None]) * band_e).sum(0)
            model_net[seam] = (imp - exp)[ok]
            meas_net[seam] = (gy[seam].reindex(range(HOURS)).interpolate(limit=3)
                              .ffill().bfill().to_numpy(float))[ok]

        mb = -(gy["Manitoba"].reindex(range(HOURS)).interpolate(limit=3)
               .ffill().bfill().to_numpy(float))[ok]
        meas_net["Manitoba"] = -mb  # import-positive

        recon = sum(model_net.values())
        meas_tot = sum(meas_net.values())
        comm = committed[ok]

        mdl = {s: round(contrib(x, p, recon.std()), 4) for s, x in model_net.items()}
        mea = {s: round(contrib(x, p, meas_tot.std()), 4) for s, x in meas_net.items()}

        years_out[str(year)] = {
            "harness_corr_recon_vs_committed": round(float(np.corrcoef(recon, comm)[0, 1]), 3),
            "corr_committed_vs_measured_price": round(float(np.corrcoef(comm, p)[0, 1]), 4),
            "corr_recon_vs_measured_price": round(float(np.corrcoef(recon, p)[0, 1]), 4),
            "corr_measured_total_vs_measured_price": round(
                float(np.corrcoef(meas_tot, p)[0, 1]), 4),
            "model_contributions": mdl,
            "model_contribution_sum": round(sum(mdl.values()), 4),
            "measured_contributions": mea,
            "measured_contribution_sum": round(sum(mea.values()), 4),
            "model_seam_sigma_mw": {s: round(float(x.std()), 1) for s, x in model_net.items()},
            "measured_seam_sigma_mw": {s: round(float(x.std()), 1) for s, x in meas_net.items()},
            "model_total_sigma_mw": round(float(recon.std()), 1),
            "measured_total_sigma_mw": round(float(meas_tot.std()), 1),
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")
    for year in YEARS:
        y = years_out[str(year)]
        print(f"===================== {year} =====================")
        print(f"  harness corr(recon, committed) {y['harness_corr_recon_vs_committed']:+.3f}")
        print(f"  corr(imports, measured price):  committed {y['corr_committed_vs_measured_price']:+.4f}"
              f"   recon {y['corr_recon_vs_measured_price']:+.4f}"
              f"   MEASURED {y['corr_measured_total_vs_measured_price']:+.4f}")
        print(f"  {'seam':<10} {'MODEL contrib':>14} {'MEASURED contrib':>18}"
              f" {'model sigma':>12} {'meas sigma':>11}")
        for s in ("PJM", "SPP", "South", "Manitoba"):
            m = y["model_contributions"].get(s)
            e = y["measured_contributions"].get(s)
            ms = y["model_seam_sigma_mw"].get(s)
            es = y["measured_seam_sigma_mw"].get(s)
            print(f"  {s:<10} {('  n/a' if m is None else f'{m:+.4f}'):>14}"
                  f" {('  n/a' if e is None else f'{e:+.4f}'):>18}"
                  f" {('n/a' if ms is None else f'{ms:.0f}'):>12}"
                  f" {('n/a' if es is None else f'{es:.0f}'):>11}")
        print(f"  {'SUM':<10} {y['model_contribution_sum']:>+14.4f}"
              f" {y['measured_contribution_sum']:>+18.4f}"
              f" {y['model_total_sigma_mw']:>12.0f} {y['measured_total_sigma_mw']:>11.0f}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
