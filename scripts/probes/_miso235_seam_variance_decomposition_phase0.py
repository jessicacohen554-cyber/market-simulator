"""miso-235 phase 0 — the fourth seam miso-234's instrument omitted, and the
variance identity that says whether MISO's interchange defect is an over-strong
price response or a missing non-price one. Zero LP.

Pre-registration:
``results/calibration/PREREG-miso235-manitoba-seam-and-the-sigma-question-2026-09-07.md``
(pushed before any adjudicating quantity). Every decision rule applied here is
fixed there; nothing below selects anything.

Three questions, in the PREREG's order:

* **Q1 (instrument).** ``_miso234_corr_overshoot_phase0.py`` reconstructed the
  keeper's seams by iterating ``INTERFACE_NEIGHBORS["MISO"]``, which carries only
  PJM/SPP/South. The keeper's ``run_config.json`` however sets
  ``miso_manitoba_seam=true``, under which ``get_interchange_spec`` drops the MHEB
  firm block and ``build_interchange_fleet`` appends ``MISO_MANITOBA_SEAM_SPEC``
  as a **fourth priced neighbour**. Both reconstructions are recomputed here on one
  code path; (I-1)+(I-2) decide whether the four-seam one supersedes.
* **Q2 (item 2's premise).** The handoff asserts the model's Manitoba contribution
  is zero "by construction". ``sigma(x_MB) > 100 MW`` in every year REFUTES it.
* **Q3 (the adjudicating question).** Per seam and year, OLS of the flow on the
  price signal that seam's bands actually clear against, on the measured record and
  again on the reconstructed model flow, with the exact identity
  ``Var(x) = beta^2 Var(z) + Var(r)``. Beta ratio >= 1.5 is a PRICE-RESPONSE
  OVERSHOOT; residual-sigma ratio <= 0.5 is MISSING NON-PRICE VARIATION.

Basis discipline (miso-234 §0a): the correlation price ``P`` is the Indiana-hub
**RT** series (the lane's scored basis); every regressor is the Indiana-hub **DA**
series (the basis the seam ladders were Q-Q derived against). They correlate only
+0.402/+0.424/+0.553 and are never interchanged.

Usage: python3 scripts/probes/_miso235_seam_variance_decomposition_phase0.py
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
OUT = REPO / "results/calibration/_miso235_seam_variance_decomposition_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
ZONE = "MISO-Indiana"

# The bus each seam's bands clear on in the keeper's topology: South rides the
# miso_south_seam_split external node, every other seam the shared MISO_external.
BUS_OF_SEAM = {
    "PJM": "MISO_external",
    "SPP": "MISO_external",
    "South": "MISO_external_South",
    "Manitoba": "MISO_external",
}
THREE_SEAM = ("PJM", "SPP", "South")  # miso-234's instrument
FOUR_SEAM = ("PJM", "SPP", "South", "Manitoba")  # the keeper's actual spec

# PREREG §3 classification bars, fixed ex ante.
BETA_RATIO_BAR = 1.5
RESID_RATIO_BAR = 0.5
# PREREG §2 inertness bar, fixed ex ante.
MANITOBA_SIGMA_BAR_MW = 100.0


def contrib(x: np.ndarray, p: np.ndarray, sigma_total: float) -> float:
    """Signed contribution of ``x`` to ``corr(total, p)``; contributions sum exactly."""
    return float(np.cov(x, p, bias=True)[0, 1] / (sigma_total * p.std()))


def ols(x: np.ndarray, z: np.ndarray) -> tuple[float, float, float, float]:
    """Return ``(beta, sigma_resid, r2, sigma_x)`` for ``x = a + beta*z + r``."""
    zc = z - z.mean()
    var_z = float((zc * zc).mean())
    beta = float(((x - x.mean()) * zc).mean() / var_z) if var_z > 0 else 0.0
    resid = x - (x.mean() + beta * zc)
    sx = float(x.std())
    return (
        beta,
        float(resid.std()),
        (1.0 - (resid.std() / sx) ** 2 if sx > 0 else 0.0),
        sx,
    )


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

    # The keeper's ACTUAL neighbour set: the static registry plus the Manitoba
    # seam get_interchange_spec appends under miso_manitoba_seam (run_config.json).
    specs = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}
    specs["Manitoba"] = MISO_MANITOBA_SEAM_SPEC

    keeper_cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    armed = {
        k: keeper_cfg.get(k)
        for k in (
            "miso_manitoba_seam",
            "miso_firm_imports",
            "reference_price_interface",
            "miso_seam_measured_ladder",
            "miso_seam_neighbour_hourly_ladder",
            "miso_seam_neighbour_hourly_spp",
            "miso_south_seam_split",
        )
    }

    report = {
        "probe": "miso-235 phase 0 — four-seam attribution repair + the price/non-price variance split",
        "prereg": "results/calibration/PREREG-miso235-manitoba-seam-and-the-sigma-question-2026-09-07.md",
        "keeper": "2026-09-07-miso-233-spp-hourly",
        "zero_lp": True,
        "keeper_armed_flags": armed,
        "static_registry_seams": [n.name for n in INTERFACE_NEIGHBORS["MISO"]],
        "keeper_resolved_seams": list(FOUR_SEAM),
        "price_basis": "P = Indiana hub RT (scored basis); every regressor = Indiana hub DA",
        "bars": {
            "beta_ratio_overshoot": BETA_RATIO_BAR,
            "resid_ratio_missing_nonprice": RESID_RATIO_BAR,
            "manitoba_inert_sigma_mw": MANITOBA_SIGMA_BAR_MW,
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
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        committed = (
            cls.groupby("hour")["mw"]
            .sum()
            .reindex(range(HOURS))
            .fillna(0.0)
            .to_numpy(float)
        )

        env_i = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        env_e = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="export", hour_ending_key=True
        )
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]

        # Regressor per seam, named by basis (PREREG §3 table).
        regressor = {
            "PJM": da - border,
            "SPP": da - spp_hub,
            "South": da,
            "Manitoba": da,
        }

        model_net: dict[str, np.ndarray] = {}
        meas_net: dict[str, np.ndarray] = {}
        for seam in FOUR_SEAM:
            spec = specs[seam]
            width = float(spec.interface_limit_mw) / SEAM_FLOW_TRANCHES
            pb = bus_price[BUS_OF_SEAM[seam]]
            if seam == "PJM":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"],
                    float,
                )
                in_merit = (pb - border)[None, :] > d[:, None]
            elif seam == "SPP":
                d = np.asarray(
                    MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]["SPP"][
                        "import"
                    ],
                    float,
                )
                in_merit = (pb - spp_hub)[None, :] > d[:, None]
            else:
                lad = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["import"], float)
                in_merit = pb[None, :] > lad[:, None]
            band_i = np.clip(
                np.asarray(env_i[seam], float)[None, :] - ks * width, 0.0, width
            )
            imp = (in_merit * band_i).sum(0)
            lade = np.asarray(MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"], float)
            band_e = np.clip(
                np.asarray(env_e[seam], float)[None, :] - ks * width, 0.0, width
            )
            exp = ((pb[None, :] < lade[:, None]) * band_e).sum(0)
            model_net[seam] = (imp - exp)[ok]
            meas_net[seam] = dense(seam)[ok]

        comm = committed[ok]
        recon3 = sum(model_net[s] for s in THREE_SEAM)
        recon4 = sum(model_net[s] for s in FOUR_SEAM)

        # --- Q1: instrument, (I-1) + (I-2) ---
        inst = {}
        for tag, rec in (("three_seam", recon3), ("four_seam", recon4)):
            inst[tag] = {
                "harness_corr_recon_vs_committed": round(
                    float(np.corrcoef(rec, comm)[0, 1]), 4
                ),
                "mean_abs_level_error_mw": round(
                    abs(float(rec.mean() - comm.mean())), 1
                ),
                "recon_mean_mw": round(float(rec.mean()), 1),
                "recon_sigma_mw": round(float(rec.std()), 1),
                "corr_recon_vs_measured_price": round(
                    float(np.corrcoef(rec, p)[0, 1]), 4
                ),
            }
        inst["I1_corr_rises"] = bool(
            inst["four_seam"]["harness_corr_recon_vs_committed"]
            > inst["three_seam"]["harness_corr_recon_vs_committed"]
        )
        inst["I2_level_error_not_worse"] = bool(
            inst["four_seam"]["mean_abs_level_error_mw"]
            <= inst["three_seam"]["mean_abs_level_error_mw"]
        )

        # --- attribution on both instruments ---
        meas_tot = sum(meas_net.values())
        attribution = {
            "three_seam_model": {
                s: round(contrib(model_net[s], p, recon3.std()), 4) for s in THREE_SEAM
            },
            "four_seam_model": {
                s: round(contrib(model_net[s], p, recon4.std()), 4) for s in FOUR_SEAM
            },
            "measured": {
                s: round(contrib(meas_net[s], p, meas_tot.std()), 4) for s in FOUR_SEAM
            },
            "corr_committed_vs_measured_price": round(
                float(np.corrcoef(comm, p)[0, 1]), 4
            ),
            "corr_measured_total_vs_measured_price": round(
                float(np.corrcoef(meas_tot, p)[0, 1]), 4
            ),
        }

        # --- Q3: the variance identity, per seam ---
        decomp = {}
        price_leg_sum = 0.0
        resid_leg_sum = 0.0
        for seam in FOUR_SEAM:
            z = regressor[seam][ok]
            bm, rm, r2m, sm = ols(model_net[seam], z)
            be, re_, r2e, se = ols(meas_net[seam], z)
            sigma_z = float(z.std())
            price_leg = abs(bm) * sigma_z - abs(be) * sigma_z
            resid_leg = rm - re_
            price_leg_sum += price_leg
            resid_leg_sum += resid_leg
            beta_ratio = (abs(bm) / abs(be)) if abs(be) > 1e-12 else float("inf")
            resid_ratio = (rm / re_) if re_ > 1e-12 else float("inf")
            flags = []
            if beta_ratio >= BETA_RATIO_BAR:
                flags.append("PRICE_RESPONSE_OVERSHOOT")
            if resid_ratio <= RESID_RATIO_BAR:
                flags.append("MISSING_NON_PRICE_VARIATION")
            headline = (
                "NEITHER"
                if not flags
                else (
                    flags[0]
                    if len(flags) == 1
                    else (
                        "PRICE_RESPONSE_OVERSHOOT"
                        if abs(price_leg) > abs(resid_leg)
                        else "MISSING_NON_PRICE_VARIATION"
                    )
                )
            )
            decomp[seam] = {
                "regressor": {
                    "PJM": "MISO Indiana hub DA - PJM border price",
                    "SPP": "MISO Indiana hub DA - SPP NORTH hub DA",
                    "South": "MISO Indiana hub DA (level)",
                    "Manitoba": "MISO Indiana hub DA (level)",
                }[seam],
                "sigma_z": round(sigma_z, 3),
                "beta_model_mw_per_usd": round(bm, 3),
                "beta_measured_mw_per_usd": round(be, 3),
                "beta_ratio": round(beta_ratio, 3),
                "sigma_model_mw": round(sm, 1),
                "sigma_measured_mw": round(se, 1),
                "sigma_price_explained_model_mw": round(abs(bm) * sigma_z, 1),
                "sigma_price_explained_measured_mw": round(abs(be) * sigma_z, 1),
                "sigma_resid_model_mw": round(rm, 1),
                "sigma_resid_measured_mw": round(re_, 1),
                "resid_ratio": round(resid_ratio, 3),
                "r2_model": round(r2m, 4),
                "r2_measured": round(r2e, 4),
                "price_leg_mw": round(price_leg, 1),
                "resid_leg_mw": round(resid_leg, 1),
                "flags": flags,
                "headline": headline,
            }

        total_leg = abs(price_leg_sum) + abs(resid_leg_sum)
        sigma_gap_total = float(recon4.std() - meas_tot.std())
        sum_of_seam_sigma_gap = sum(
            decomp[s]["sigma_model_mw"] - decomp[s]["sigma_measured_mw"]
            for s in FOUR_SEAM
        )

        years_out[str(year)] = {
            "instrument": inst,
            "attribution": attribution,
            "manitoba_sigma_model_mw": round(float(model_net["Manitoba"].std()), 1),
            "manitoba_mean_model_mw": round(float(model_net["Manitoba"].mean()), 1),
            "manitoba_sigma_measured_mw": round(float(meas_net["Manitoba"].std()), 1),
            "manitoba_mean_measured_mw": round(float(meas_net["Manitoba"].mean()), 1),
            "Q2_premise_refuted": bool(
                float(model_net["Manitoba"].std()) > MANITOBA_SIGMA_BAR_MW
            ),
            "decomposition": decomp,
            "sigma_split": {
                "price_leg_sum_mw": round(price_leg_sum, 1),
                "resid_leg_sum_mw": round(resid_leg_sum, 1),
                "price_share_pct": round(100.0 * abs(price_leg_sum) / total_leg, 1)
                if total_leg > 0
                else None,
                "resid_share_pct": round(100.0 * abs(resid_leg_sum) / total_leg, 1)
                if total_leg > 0
                else None,
                "sum_of_per_seam_sigma_gap_mw": round(sum_of_seam_sigma_gap, 1),
                "total_sigma_gap_mw": round(sigma_gap_total, 1),
                "reconciliation_note": (
                    "the per-seam legs sum over seams; the total sigma gap carries "
                    "cross-seam covariance too, so the two differ by construction and "
                    "both are reported"
                ),
            },
            "model_total_sigma_mw": round(float(recon4.std()), 1),
            "measured_total_sigma_mw": round(float(meas_tot.std()), 1),
            "committed_sigma_mw": round(float(comm.std()), 1),
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        y = years_out[str(year)]
        i3, i4 = y["instrument"]["three_seam"], y["instrument"]["four_seam"]
        print(f"===================== {year} =====================")
        print(
            f"  Q1 instrument   3-seam corr {i3['harness_corr_recon_vs_committed']:+.4f}"
            f" level-err {i3['mean_abs_level_error_mw']:>7.1f} MW"
            f"   ->  4-seam corr {i4['harness_corr_recon_vs_committed']:+.4f}"
            f" level-err {i4['mean_abs_level_error_mw']:>7.1f} MW"
            f"   I-1 {y['instrument']['I1_corr_rises']}"
            f"  I-2 {y['instrument']['I2_level_error_not_worse']}"
        )
        print(
            f"  Q2 Manitoba     model sigma {y['manitoba_sigma_model_mw']:>8.1f} MW"
            f"  mean {y['manitoba_mean_model_mw']:>8.1f} MW"
            f"   (measured sigma {y['manitoba_sigma_measured_mw']:.1f},"
            f" mean {y['manitoba_mean_measured_mw']:.1f})"
            f"   premise refuted: {y['Q2_premise_refuted']}"
        )
        a = y["attribution"]
        print(
            f"  attribution     committed corr {a['corr_committed_vs_measured_price']:+.4f}"
            f"   measured corr {a['corr_measured_total_vs_measured_price']:+.4f}"
        )
        print(
            f"  {'seam':<10} {'3-seam mdl':>11} {'4-seam mdl':>11} {'measured':>10}"
            f" {'beta mdl':>10} {'beta meas':>10} {'b-ratio':>8}"
            f" {'sd r mdl':>9} {'sd r meas':>10} {'r-ratio':>8}  headline"
        )
        for s in FOUR_SEAM:
            d = y["decomposition"][s]
            m3 = a["three_seam_model"].get(s)
            print(
                f"  {s:<10} {('n/a' if m3 is None else f'{m3:+.4f}'):>11}"
                f" {a['four_seam_model'][s]:>+11.4f} {a['measured'][s]:>+10.4f}"
                f" {d['beta_model_mw_per_usd']:>10.2f} {d['beta_measured_mw_per_usd']:>10.2f}"
                f" {d['beta_ratio']:>8.2f}"
                f" {d['sigma_resid_model_mw']:>9.1f} {d['sigma_resid_measured_mw']:>10.1f}"
                f" {d['resid_ratio']:>8.2f}  {d['headline']}"
            )
        sp = y["sigma_split"]
        print(
            f"  SIGMA SPLIT     price leg {sp['price_leg_sum_mw']:>+9.1f} MW"
            f" ({sp['price_share_pct']}%)   residual leg {sp['resid_leg_sum_mw']:>+9.1f} MW"
            f" ({sp['resid_share_pct']}%)"
        )
        print(
            f"                  sum-of-seam sigma gap {sp['sum_of_per_seam_sigma_gap_mw']:>+9.1f} MW"
            f"   total sigma gap {sp['total_sigma_gap_mw']:>+9.1f} MW"
            f"   (model {y['model_total_sigma_mw']:.0f} vs measured"
            f" {y['measured_total_sigma_mw']:.0f}, committed {y['committed_sigma_mw']:.0f})"
        )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
