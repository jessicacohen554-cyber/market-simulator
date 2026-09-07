"""miso-233 phase 0 (rule 29 clause 0) — WHERE the seam's decile-slope magnitude
is lost: band k, hour-of-day, and — the question the queue did not name — whether
the loss is a MERIT loss (the band is out of the money) or an ENVELOPE loss (the
band is in the money and the measured deliverability cap has already taken its
width away).

**Zero LP.** Everything below is computed from the keeper's committed hourly
sidecars and committed measured series. Nothing is solved, nothing is tuned, and
the frozen ``delta_k`` ladder is read, never re-derived (rule 23).

THE OPEN ITEM (MISO lever queue item 1, miso-232 non-claim 1)
------------------------------------------------------------
The miso-232 keeper repaired the seam's measured-price decile slope in SIGN in
all three years but reaches only

    +139 / +111 / +681 MW   against measured  +1,303 / +1,384 / +948 MW

i.e. 11 / 8 / 72 % of the measured magnitude. The queue asks: decompose the
residual slope by band ``k`` and by hour-of-day, and determine whether the deep
bands (k = 6-8, ``delta_k`` +6 to +30) are the ones under-clearing in MISO's
cheap hours.

THE RECONSTRUCTION (the miso-231 readout-B instrument, extended)
----------------------------------------------------------------
The keeper's own arming is reproduced exactly:

    in_merit[k,t] = (p_bus(t) - border(t)) > delta_k          (hourly ladder)
    band_mw[k,t]  = clip(cap(t) - k*width, 0, width)          (merit_cap=True)
    cleared[k,t]  = in_merit * band_mw

``p_bus`` is the keeper's committed ``MISO_external`` P1 price, ``border`` the
measured PJM western-border DA the solve itself reads, ``cap`` the measured
(month x hour-of-day) p90 net-import deliverability envelope on the keeper's own
``hour_ending_key=True`` convention, and ``width = interface_limit / 8``. The
harness check is ``corr(sum_k cleared, keeper committed imports)``: the
reconstruction has to track the solve before its decomposition means anything.

THE ATTRIBUTION IDENTITY (exact, per band-hour)
----------------------------------------------
    width = cleared + lost_to_envelope + lost_to_merit + lost_to_both
      cleared          = in_merit  *  band_mw
      lost_to_envelope = in_merit  * (width - band_mw)   in the money, capped
      lost_to_merit    = ~in_merit *  band_mw            deliverable, out of money
      lost_to_both     = ~in_merit * (width - band_mw)

Decile-differencing each term on the MEASURED Indiana hub RT price (the frozen
miso-225/226 comparator basis every seam number on record uses) splits the
slope MISO does not have into the part a price mechanism could still reach and
the part a price mechanism structurally cannot.

Usage: python3 scripts/probes/_miso233_seam_slope_anatomy_phase0.py
"""

from __future__ import annotations

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
OUT = REPO / "results/calibration/_miso233_seam_slope_anatomy_phase0.json"
YEARS = (2023, 2024, 2025)
ZONE = "MISO-Indiana"      # the C1/G-2 reference hub, measured comparator basis
BUS = "MISO_external"      # the bus the reference-price seam bands clear against
HOURS = 8760

# miso-232's published comparators, quoted so every delta below is anchored to a
# committed number rather than recomputed here.
MISO232 = {
    "slope_model_mw": {"2023": 139.0, "2024": 111.0, "2025": 681.0},
    "slope_measured_mw": {"2023": 1303.0, "2024": 1384.0, "2025": 948.0},
}


def decile_slope(price: np.ndarray, series: np.ndarray) -> tuple[float, list[float]]:
    """(d1 - d10) and the ten decile means, binned on ``price`` (ascending)."""
    order = np.argsort(price, kind="stable")
    parts = np.array_split(order, 10)
    means = [float(series[p].mean()) for p in parts]
    return means[0] - means[-1], means


def decile_masks(price: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Boolean masks for the cheapest and dearest deciles of ``price``."""
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
        MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
    )

    import importlib.util

    spec_ld = importlib.util.spec_from_file_location(
        "derive_miso_seam_ladders", REPO / "scripts/data/derive_miso_seam_ladders.py"
    )
    dm = importlib.util.module_from_spec(spec_ld)
    spec_ld.loader.exec_module(dm)
    g_all = dm.load_joined()

    from _miso224_floor_anatomy_phase0 import actual_zone_price

    pjm = {n.name: n for n in INTERFACE_NEIGHBORS["MISO"]}["PJM"]
    limit = float(pjm.interface_limit_mw)
    width = limit / SEAM_FLOW_TRANCHES

    report: dict[str, object] = {
        "probe": "miso-233 phase 0 — seam decile-slope anatomy by band k, "
        "hour-of-day, and merit-vs-envelope attribution",
        "keeper": "2026-09-06-miso-232-hourly-seam",
        "zero_lp": True,
        "interface_limit_mw": limit,
        "band_width_mw": round(width, 1),
        "miso232_published": MISO232,
        "years": {},
    }
    years_out: dict[str, object] = {}

    for year in YEARS:
        gy = g_all.loc[year]
        border = (
            gy["pjm_border"]
            .reindex(range(HOURS))
            .interpolate(limit=3)
            .ffill()
            .bfill()
            .to_numpy(float)
        )
        meas_pjm_flow = (
            gy["PJM"].reindex(range(HOURS)).interpolate(limit=3).ffill().bfill()
            .to_numpy(float)
        )
        d_imp = np.asarray(
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]["PJM"]["import"], float
        )

        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        p_bus = sysf[sysf["zone"] == BUS].sort_values("hour")["price"].to_numpy(float)
        cls = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
        cls = cls[(cls["pass"] == "P1") & (cls["klass"] == "import")]
        model_imp = (
            cls.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0)
            .to_numpy(float)
        )

        env = measured_seam_import_envelope(
            "MISO", year, HOURS, None, direction="import", hour_ending_key=True
        )
        cap = np.asarray(env["PJM"], float)
        ks = np.arange(SEAM_FLOW_TRANCHES)[:, None]
        band_mw = np.clip(cap[None, :] - ks * width, 0.0, width)     # (8, 8760)
        in_merit = ((p_bus - border)[None, :] > d_imp[:, None])       # (8, 8760)

        cleared = in_merit * band_mw
        lost_env = in_merit * (width - band_mw)
        lost_mer = (~in_merit) * band_mw
        lost_both = (~in_merit) * (width - band_mw)

        act = actual_zone_price(year)[ZONE].to_numpy(float)
        ok = np.isfinite(act)
        # Bin on the measured hub price over the hours it exists (the published
        # comparator basis); everything is scored on the same hour set.
        price = act[ok]
        d1, d10 = decile_masks(price)

        def dslope(x: np.ndarray) -> float:
            xx = x[ok]
            return float(xx[d1].mean() - xx[d10].mean())

        # --- reproduction of the published comparators ---------------------
        slope_model = dslope(model_imp)
        slope_meas = dslope(meas_pjm_flow)
        recon_total = cleared.sum(0)
        harness = float(np.corrcoef(recon_total, model_imp)[0, 1])

        # --- per-band decomposition ---------------------------------------
        bands = []
        for k in range(SEAM_FLOW_TRANCHES):
            bands.append(
                {
                    "k": k + 1,
                    "delta_k": round(float(d_imp[k]), 2),
                    "mean_cleared_mw": round(float(cleared[k].mean()), 1),
                    "merit_frac_all": round(float(in_merit[k].mean()), 4),
                    "merit_frac_d1": round(float(in_merit[k][ok][d1].mean()), 4),
                    "merit_frac_d10": round(float(in_merit[k][ok][d10].mean()), 4),
                    "cap_frac_d1": round(float(band_mw[k][ok][d1].mean() / width), 4),
                    "cap_frac_d10": round(float(band_mw[k][ok][d10].mean() / width), 4),
                    "slope_cleared_mw": round(dslope(cleared[k]), 1),
                    "slope_if_uncapped_mw": round(dslope(in_merit[k] * width), 1),
                    "slope_lost_to_envelope_mw": round(dslope(lost_env[k]), 1),
                    "slope_lost_to_merit_mw": round(dslope(lost_mer[k]), 1),
                    "d1_cleared_mw": round(float(cleared[k][ok][d1].mean()), 1),
                    "d10_cleared_mw": round(float(cleared[k][ok][d10].mean()), 1),
                    "d1_envelope_loss_mw": round(float(lost_env[k][ok][d1].mean()), 1),
                    "d1_merit_loss_mw": round(float(lost_mer[k][ok][d1].mean()), 1),
                }
            )

        # --- the headroom question, stated at the seam level ---------------
        deep = slice(5, 8)  # k = 6, 7, 8
        anatomy = {
            "harness_corr_recon_vs_committed_imports": round(harness, 3),
            "recon_mean_mw": round(float(recon_total.mean()), 1),
            "committed_import_mean_mw": round(float(model_imp.mean()), 1),
            "measured_pjm_seam_mean_mw": round(float(meas_pjm_flow.mean()), 1),
            "envelope_cap_mean_mw": round(float(cap.mean()), 1),
            "envelope_cap_d1_mw": round(float(cap[ok][d1].mean()), 1),
            "envelope_cap_d10_mw": round(float(cap[ok][d10].mean()), 1),
            "measured_flow_d1_mw": round(float(meas_pjm_flow[ok][d1].mean()), 1),
            "measured_flow_d10_mw": round(float(meas_pjm_flow[ok][d10].mean()), 1),
            "recon_d1_mw": round(float(recon_total[ok][d1].mean()), 1),
            "recon_d10_mw": round(float(recon_total[ok][d10].mean()), 1),
            "slope_committed_model_imports_mw": round(slope_model, 1),
            "slope_measured_pjm_seam_mw": round(slope_meas, 1),
            "slope_recon_pjm_mw": round(dslope(recon_total), 1),
            "slope_recon_if_uncapped_mw": round(dslope((in_merit * width).sum(0)), 1),
            "slope_cap_profile_mw": round(dslope(cap), 1),
            "slope_deep_bands_k6_8_mw": round(
                float(sum(b["slope_cleared_mw"] for b in bands[deep])), 1
            ),
            "slope_shallow_bands_k1_5_mw": round(
                float(sum(b["slope_cleared_mw"] for b in bands[:5])), 1
            ),
            "d1_envelope_loss_total_mw": round(float(lost_env[:, ok][:, d1].sum(0).mean()), 1),
            "d1_merit_loss_total_mw": round(float(lost_mer[:, ok][:, d1].sum(0).mean()), 1),
            "d1_both_loss_total_mw": round(float(lost_both[:, ok][:, d1].sum(0).mean()), 1),
            "d1_cleared_total_mw": round(float(cleared[:, ok][:, d1].sum(0).mean()), 1),
            "measured_minus_cap_d1_mw": round(
                float(meas_pjm_flow[ok][d1].mean() - cap[ok][d1].mean()), 1
            ),
            "hours_measured_flow_above_cap_pct": round(
                100.0 * float((meas_pjm_flow > cap).mean()), 2
            ),
            "hours_measured_flow_above_cap_d1_pct": round(
                100.0 * float((meas_pjm_flow > cap)[ok][d1].mean()), 2
            ),
        }

        # --- hour-of-day decomposition -------------------------------------
        hod = np.arange(HOURS) % 24
        hod_rows = []
        for h in range(24):
            m = hod == h
            hod_rows.append(
                {
                    "hod": h,
                    "recon_mw": round(float(recon_total[m].mean()), 1),
                    "measured_mw": round(float(meas_pjm_flow[m].mean()), 1),
                    "cap_mw": round(float(cap[m].mean()), 1),
                    "gap_measured_minus_recon_mw": round(
                        float((meas_pjm_flow - recon_total)[m].mean()), 1
                    ),
                    "envelope_loss_mw": round(float(lost_env[:, m].sum(0).mean()), 1),
                    "merit_loss_mw": round(float(lost_mer[:, m].sum(0).mean()), 1),
                }
            )

        years_out[str(year)] = {
            "anatomy": anatomy,
            "bands": bands,
            "hour_of_day": hod_rows,
        }

    report["years"] = years_out
    OUT.write_text(json.dumps(report, indent=1) + "\n")
    print(f"wrote {OUT}\n")

    for year in YEARS:
        a = years_out[str(year)]["anatomy"]
        print(f"================================ {year} ================================")
        print(
            f"  harness corr(recon, committed imports) = {a['harness_corr_recon_vs_committed_imports']:+.3f}"
            f"   recon {a['recon_mean_mw']:.0f} MW vs committed {a['committed_import_mean_mw']:.0f} MW"
            f"   (committed = ALL seams; recon = PJM only)"
        )
        print(
            f"  SLOPE d1-d10 on measured hub price:"
            f"  committed model {a['slope_committed_model_imports_mw']:+.0f}"
            f" | measured PJM seam {a['slope_measured_pjm_seam_mw']:+.0f}"
            f" | recon PJM {a['slope_recon_pjm_mw']:+.0f}"
            f" | recon IF UNCAPPED {a['slope_recon_if_uncapped_mw']:+.0f}"
            f" | envelope cap profile itself {a['slope_cap_profile_mw']:+.0f}"
        )
        print(
            f"  d1 (cheapest decile): measured {a['measured_flow_d1_mw']:.0f} MW"
            f" | cap {a['envelope_cap_d1_mw']:.0f} MW"
            f" | recon cleared {a['d1_cleared_total_mw']:.0f} MW"
            f" | lost to ENVELOPE {a['d1_envelope_loss_total_mw']:.0f}"
            f" | lost to MERIT {a['d1_merit_loss_total_mw']:.0f}"
            f" | lost to BOTH {a['d1_both_loss_total_mw']:.0f}"
        )
        print(
            f"  measured flow EXCEEDS the p90 cap in {a['hours_measured_flow_above_cap_pct']:.1f} % of all hours"
            f" and {a['hours_measured_flow_above_cap_d1_pct']:.1f} % of d1 hours;"
            f" measured d1 - cap d1 = {a['measured_minus_cap_d1_mw']:+.0f} MW"
        )
        print(
            f"  slope by depth: shallow k1-5 {a['slope_shallow_bands_k1_5_mw']:+.0f} MW"
            f" | deep k6-8 {a['slope_deep_bands_k6_8_mw']:+.0f} MW"
        )
        print(
            f"    {'k':>2} {'delta_k':>8} {'merit d1':>9} {'merit d10':>10}"
            f" {'cap frac d1':>12} {'cleared d1':>11} {'slope':>8}"
            f" {'if uncapped':>12} {'env loss d1':>12} {'merit loss d1':>14}"
        )
        for b in years_out[str(year)]["bands"]:
            print(
                f"    {b['k']:>2} {b['delta_k']:>8.2f} {b['merit_frac_d1']:>9.3f}"
                f" {b['merit_frac_d10']:>10.3f} {b['cap_frac_d1']:>12.3f}"
                f" {b['d1_cleared_mw']:>11.0f} {b['slope_cleared_mw']:>+8.0f}"
                f" {b['slope_if_uncapped_mw']:>+12.0f} {b['d1_envelope_loss_mw']:>12.0f}"
                f" {b['d1_merit_loss_mw']:>14.0f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
