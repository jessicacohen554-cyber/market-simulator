"""miso-235 addendum — is a seam's OLS residual NON-PRICE variation, or variation
on a price the regressor cannot see? Zero LP.

Declared before it was computed in
``results/calibration/ADDENDUM-miso235-residual-character-2026-09-07.md``; the
interpretation rule applied here is fixed there. **No pre-registered verdict from
``_miso235_seam_variance_decomposition_phase0.py`` can move** — those values are
already committed and are only restated.

The blind spot this measures: the PREREG's OLS regresses BOTH sides on the
MEASURED price signal, but the model's bands clear on the model's OWN solved bus
price. Variation the model inherits from the gap between those two prices lands in
the OLS residual and is counted as "non-price variation" when it is not.

S-1 ``corr(residual, P)`` (P = Indiana hub RT, the scored basis), model vs measured.
S-2 ``R^2`` of each side's flow on its OWN native driver.
S-3 share of the model seam sigma explained by the model's own clearing spread.

Usage: python3 scripts/probes/_miso235_residual_character_addendum.py
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
PHASE0 = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
OUT = REPO / "results/calibration/_miso235_residual_character_addendum.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"

BUS_OF_SEAM = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}
SEAMS = ("PJM", "SPP", "South", "Manitoba")

# ADDENDUM interpretation bars, fixed ex ante.
CORR_RATIO_BAR = 2.0
R2_MODEL_OWN_BAR = 0.90
R2_MEASURED_BAR = 0.60


def ols_resid(x: np.ndarray, z: np.ndarray) -> tuple[np.ndarray, float]:
    """Return ``(residual, r2)`` for ``x = a + beta*z + r``."""
    zc = z - z.mean()
    var_z = float((zc * zc).mean())
    beta = float(((x - x.mean()) * zc).mean() / var_z) if var_z > 0 else 0.0
    resid = x - (x.mean() + beta * zc)
    sx = float(x.std())
    return resid, (1.0 - (resid.std() / sx) ** 2 if sx > 0 else 0.0)


def main() -> int:
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.eia_loader import (
        measured_miso_spp_hub_prices,
        measured_seam_import_envelope,
    )
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
    from market_sim.model.interchange.spec import (
        MISO_MANITOBA_SEAM_SPEC,
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
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC
    phase0 = json.loads(PHASE0.read_text())

    report = {
        "probe": "miso-235 addendum — residual character (price-coherent vs non-price)",
        "addendum": "results/calibration/ADDENDUM-miso235-residual-character-2026-09-07.md",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "bars": {
            "corr_ratio": CORR_RATIO_BAR,
            "r2_model_own_driver": R2_MODEL_OWN_BAR,
            "r2_measured": R2_MEASURED_BAR,
        },
        "years": {},
    }
    years_out: dict[str, dict] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        p = act[ok]

        def dense(col: str) -> np.ndarray:
            return (
                gy[col]
                .reindex(range(HOURS))
                .interpolate(limit=3)
                .ffill()
                .bfill()
                .to_numpy(float)
            )

        border = dense("pjm_border")
        da = dense("da")
        spp_hub = np.asarray(measured_miso_spp_hub_prices("MISO", year, HOURS), float)

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        bus_price = {
            b: sysf[sysf["zone"] == b].sort_values("hour")["price"].to_numpy(float)
            for b in set(BUS_OF_SEAM.values())
        }

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]

        measured_regressor = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }

        out_year: dict[str, dict] = {}
        for seam in SEAMS:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                in_merit = (pb - border)[None, :] > d[:, None]
                own_driver = pb - border
            elif seam == "SPP":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ],
                    float,
                )
                in_merit = (pb - spp_hub)[None, :] > d[:, None]
                own_driver = pb - spp_hub
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = pb[None, :] > lad[:, None]
                own_driver = pb
            band_i = np.clip(
                np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width
            )
            imp = (in_merit * band_i).sum(0)
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            band_e = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )
            exp = ((pb[None, :] < lade[:, None]) * band_e).sum(0)
            x_model = (imp - exp)[ok]
            x_meas = dense(seam)[ok]
            z_meas = measured_regressor[seam][ok]
            z_own = own_driver[ok]

            r_model, _ = ols_resid(x_model, z_meas)
            r_meas, r2_meas_on_meas = ols_resid(x_meas, z_meas)
            _, r2_model_on_own = ols_resid(x_model, z_own)

            c_rm = float(np.corrcoef(r_model, p)[0, 1])
            c_re = float(np.corrcoef(r_meas, p)[0, 1])
            ratio = abs(c_rm) / abs(c_re) if abs(c_re) > 1e-12 else float("inf")
            pre = phase0["years"][str(year)]["decomposition"][seam]
            qualifies = bool(
                ratio >= CORR_RATIO_BAR
                and r2_model_on_own >= R2_MODEL_OWN_BAR
                and r2_meas_on_meas <= R2_MEASURED_BAR
            )
            out_year[seam] = {
                "prereg_headline_restated": pre["headline"],
                "s1_corr_resid_model_vs_P": round(c_rm, 4),
                "s1_corr_resid_measured_vs_P": round(c_re, 4),
                "s1_ratio": round(ratio, 3),
                "s2_r2_model_on_own_clearing_spread": round(r2_model_on_own, 4),
                "s2_r2_measured_on_measured_spread": round(r2_meas_on_meas, 4),
                "s3_model_sigma_mw": round(float(x_model.std()), 1),
                "s3_model_sigma_explained_by_own_driver_mw": round(
                    float(x_model.std()) * float(np.sqrt(max(r2_model_on_own, 0.0))), 1
                ),
                "s3_model_sigma_explained_pct": round(
                    100.0 * float(np.sqrt(max(r2_model_on_own, 0.0))), 1
                ),
                "qualifies_price_coherent_residual": qualifies,
            }
        years_out[str(year)] = out_year

    report["years"] = years_out
    # Every-year qualification, per the ADDENDUM's rule.
    report["qualified_seams_all_years"] = sorted(
        s
        for s in SEAMS
        if all(years_out[str(y)][s]["qualifies_price_coherent_residual"] for y in YEARS)
    )
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")
    for year in YEARS:
        print(f"===================== {year} =====================")
        print(
            f"  {'seam':<10} {'prereg':>28} {'corr(r_mdl,P)':>14} {'corr(r_meas,P)':>15}"
            f" {'ratio':>7} {'R2 mdl own':>11} {'R2 meas':>9} {'sigma expl %':>13}  qualifies"
        )
        for s in SEAMS:
            d = years_out[str(year)][s]
            print(
                f"  {s:<10} {d['prereg_headline_restated']:>28}"
                f" {d['s1_corr_resid_model_vs_P']:>+14.4f}"
                f" {d['s1_corr_resid_measured_vs_P']:>+15.4f}"
                f" {d['s1_ratio']:>7.2f} {d['s2_r2_model_on_own_clearing_spread']:>11.4f}"
                f" {d['s2_r2_measured_on_measured_spread']:>9.4f}"
                f" {d['s3_model_sigma_explained_pct']:>12.1f}%"
                f"  {d['qualifies_price_coherent_residual']}"
            )
        print()
    print(f"QUALIFIED IN EVERY YEAR: {report['qualified_seams_all_years'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
