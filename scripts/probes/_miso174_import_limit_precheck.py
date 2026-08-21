"""miso-174 — the PRE-REGISTERED inertness pre-check for `measured_interface_limits`.

READ-ONLY. **No LP is solved and nothing here re-enters a solve** (rule 13
``[R-MEASURED]``). Executes the kills fixed in
``results/calibration/PREREG-miso174-seam-import-limit-precheck-2026-08-21.md``
§3, whose thresholds were committed BEFORE these quantities were computed
(commit 6cd0335).

  K-PRE-1  capability exceedance — does the model move MORE than the seam has
           ever been observed to deliver in the same (month x hour-of-day)
           bucket?  KILL (a) if the PJM-seam exceedance share is < 20 % of
           scarce hours in >= 2 of 3 years.
  K-PRE-2  reach — hour-wise upper bound on ANY admissible import ceiling.
           KILL (a) if < 0.50 GW in >= 2 of 3 years.
  K-PRE-3  zonal-basis redundancy (rule 19) — reported evidence: the share of
           scarce hours in which the keeper's Midwest zonal prices separate.
  reported price reach — the over-import's value at the model's OWN local
           supply slope inside the scarce set. NOT a gate, NOT a C3a claim.
  reported envelope hour-key rotation — the production envelope buckets the
           measured series on its raw hour-ENDING local stamp and applies the
           bucket to the model's hour-BEGINNING clock; the resulting one-hour
           rotation of the diurnal cap profile is measured here and disclosed.

Run:  python3 scripts/probes/_miso174_import_limit_precheck.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.constants import MISO_SEAM_FLOW_PERCENTILE  # noqa: E402
from market_sim.config.interchange_config import MISO_SEAM_DIBA  # noqa: E402
from market_sim.data.eia930 import measured_seam_import_envelope  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso174_seam_overimport_decomposition import (  # noqa: E402
    HOURS,
    KEEPER,
    YEARS,
    build_frames,
    diba_wide,
    hour_sets,
    model_seam_flows,
)

CAL = ROOT / "results" / "calibration"
E930_DIBA = ROOT / "data" / "raw" / "eia-930-interchange" / "MISO interchange hourly.parquet"
OUT = CAL / "_miso174_import_limit_precheck.json"

ALIGN_SHIFT = -1        # solved in the decomposition (r = 1.0000 / 0.8286 / 1.0000)
K1_THRESHOLD = 0.20     # PREREG §3 K-PRE-1
K2_THRESHOLD_GW = 0.50  # PREREG §3 K-PRE-2
MIDWEST = ("MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East")


def bucket_stat(year: int, stat: str, shift_h: int) -> dict[str, np.ndarray]:
    """Per-seam (month x hour-of-day) statistic of measured net import, on the model clock.

    ``shift_h`` is applied to the file's ``local_time`` BEFORE bucketing, so
    ``shift_h = -1`` reproduces the alignment the decomposition solved and
    ``shift_h = 0`` reproduces the PRODUCTION envelope's own convention.
    ``stat`` is ``"max"`` (p100 — the observed capability) or a percentile.
    """
    diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}
    frame = pd.read_parquet(E930_DIBA)
    local = pd.DatetimeIndex(frame["local_time"]) + pd.Timedelta(hours=shift_h)
    keep = local.year == year
    frame, local = frame[keep], local[keep]
    seam = frame["diba"].astype(str).map(diba_to_seam)
    work = pd.DataFrame(
        {"seam": seam.to_numpy(), "month": local.month.to_numpy(),
         "hod": local.hour.to_numpy(), "ts": local.to_numpy(),
         "mw": pd.to_numeric(frame["mw"], errors="coerce").to_numpy()}
    ).dropna(subset=["seam", "mw"])
    per_ts = work.groupby(["seam", "ts", "month", "hod"], observed=True)["mw"].sum()
    per_ts = (-per_ts).reset_index(name="net_import")  # EIA sign: + = MISO exports

    from market_sim.data.fleet import _hour_to_month_index
    rm = _hour_to_month_index(HOURS) + 1
    rh = np.arange(HOURS) % 24
    out: dict[str, np.ndarray] = {}
    for name in MISO_SEAM_DIBA:
        sub = per_ts[per_ts["seam"] == name]
        if sub.empty:
            continue
        tab = np.full((12, 24), np.nan)
        for (m, h), g in sub.groupby(["month", "hod"], observed=True):
            v = g["net_import"].to_numpy()
            tab[m - 1, h] = v.max() if stat == "max" else np.percentile(v, float(stat))
        for m in range(12):
            row = tab[m]
            if not np.all(np.isnan(row)):
                tab[m] = np.where(np.isnan(row), np.nanmax(row), row)
        if np.any(np.isnan(tab)):
            tab = np.where(np.isnan(tab), np.nanmax(tab), tab)
        out[name] = tab[rm - 1, rh]
    return out


def main() -> None:
    frames = build_frames()
    rec: dict = {
        "session": "miso-174",
        "prereg": "PREREG-miso174-seam-import-limit-precheck-2026-08-21.md (commit 6cd0335)",
        "align_shift_h": ALIGN_SHIFT,
        "thresholds": {"K_PRE_1_exceedance_share": K1_THRESHOLD,
                       "K_PRE_2_reach_gw": K2_THRESHOLD_GW},
        "k_pre_1": {}, "k_pre_2": {}, "k_pre_3_evidence": {},
        "reported_price_reach": {}, "reported_envelope_rotation": {},
    }

    for y in YEARS:
        df = frames[y]
        sets = hour_sets(df)
        m = sets["summer_scarce_rt200"]
        net, by_side = model_seam_flows(y)
        meas_w = diba_wide(y, ALIGN_SHIFT)
        diba_to_seam = {d: s for s, dibas in MISO_SEAM_DIBA.items() for d in dibas}

        # ---------------- K-PRE-1 : capability exceedance ----------------
        k1: dict = {}
        for conv, shift in (("aligned", ALIGN_SHIFT), ("production", 0)):
            cap100 = bucket_stat(y, "max", shift)
            per_seam = {}
            for seam, cap in cap100.items():
                if (seam, "imp") not in by_side.columns:
                    continue
                gi = by_side[(seam, "imp")].to_numpy()
                exceed = gi[m] > cap[m]
                per_seam[seam] = {
                    "n": int(m.sum()),
                    "exceedance_share": float(np.mean(exceed)),
                    "exceedance_hours": int(exceed.sum()),
                    "mean_model_gross_import_gw": float(np.mean(gi[m])) / 1000,
                    "mean_observed_max_gw": float(np.mean(cap[m])) / 1000,
                    "mean_excess_when_exceeding_gw": (
                        float(np.mean((gi[m] - cap[m])[exceed])) / 1000 if exceed.any() else 0.0
                    ),
                }
            k1[conv] = per_seam
        rec["k_pre_1"][str(y)] = k1

        # ---------------- K-PRE-2 : reach ----------------
        total = np.zeros(HOURS)
        per_seam_reach = {}
        for seam in MISO_SEAM_DIBA:
            if (seam, "imp") not in by_side.columns:
                continue
            gi = by_side[(seam, "imp")].to_numpy()
            cols = [c for c in meas_w.columns if diba_to_seam.get(str(c)) == seam]
            meas = meas_w[cols].sum(axis=1, min_count=1).to_numpy() if cols else np.zeros(HOURS)
            excess = np.maximum(0.0, gi - np.nan_to_num(meas, nan=0.0))
            total += excess
            per_seam_reach[seam] = float(np.mean(excess[m])) / 1000
        rec["k_pre_2"][str(y)] = {
            "n": int(m.sum()),
            "reach_gw": float(np.mean(total[m])) / 1000,
            "per_seam_gw": per_seam_reach,
            "object_over_import_gw": float(
                np.mean((df["model_net"].to_numpy() + df["TI"].to_numpy())[m])
            ) / 1000,
        }

        # ------------- K-PRE-3 evidence : zonal price separation -------------
        sysd = pd.read_parquet(KEEPER / f"system_{y}.parquet")
        sysd = sysd[(sysd["pass"] == "P1") & (sysd["zone"].isin(MIDWEST))]
        pz = sysd.pivot_table(index="hour", columns="zone", values="price").reindex(range(HOURS))
        spread = (pz.max(axis=1) - pz.min(axis=1)).to_numpy()
        rec["k_pre_3_evidence"][str(y)] = {
            "midwest_zones": list(MIDWEST),
            "scarce_mean_spread": float(np.nanmean(spread[m])),
            "scarce_share_separated_gt_0p01": float(np.nanmean(spread[m] > 0.01)),
            "scarce_share_separated_gt_1": float(np.nanmean(spread[m] > 1.0)),
            "annual_share_separated_gt_0p01": float(np.nanmean(spread > 0.01)),
            "annual_mean_spread": float(np.nanmean(spread)),
        }

        # ------------- reported : price reach at the model's OWN slope -------------
        su = sets["summer"]
        d_gw = df["demand"].to_numpy() / 1000
        p = df["price"].to_numpy()
        hi = su & (d_gw >= np.nanpercentile(d_gw[su], 80))
        slope_hi = float(np.polyfit(d_gw[hi], p[hi], 1)[0])
        slope_all = float(np.polyfit(d_gw[su], p[su], 1)[0])
        reach = rec["k_pre_2"][str(y)]["reach_gw"]
        rec["reported_price_reach"][str(y)] = {
            "summer_slope_usd_per_gw": slope_all,
            "summer_top20pct_slope_usd_per_gw": slope_hi,
            "reach_gw": reach,
            "implied_price_lift_usd_at_top_slope": reach * slope_hi,
            "scarce_mean_model_price": float(np.nanmean(p[m])),
            "scarce_mean_actual_rt": float(np.nanmean(df["rt"].to_numpy()[m])),
        }

        # ------------- reported : envelope hour-key rotation -------------
        prod = measured_seam_import_envelope("MISO", y, HOURS, None, "import") or {}
        aligned = bucket_stat(y, str(MISO_SEAM_FLOW_PERCENTILE), ALIGN_SHIFT)
        rot = {}
        for seam, cap in prod.items():
            if seam not in aligned:
                continue
            a = np.maximum(aligned[seam], 0.0)  # production clips the cap at 0
            rot[seam] = {
                "mean_production_cap_gw": float(np.mean(cap)) / 1000,
                "mean_aligned_cap_gw": float(np.mean(a)) / 1000,
                "mean_abs_diff_mw": float(np.mean(np.abs(cap - a))),
                "max_abs_diff_mw": float(np.max(np.abs(cap - a))),
                "scarce_mean_diff_mw": float(np.mean((cap - a)[m])),
            }
        rec["reported_envelope_rotation"][str(y)] = rot

    # ---------------- verdicts ----------------
    pjm_shares = [rec["k_pre_1"][str(y)]["aligned"]["PJM"]["exceedance_share"] for y in YEARS]
    reaches = [rec["k_pre_2"][str(y)]["reach_gw"] for y in YEARS]
    rec["verdict"] = {
        "K_PRE_1_pjm_exceedance_shares": pjm_shares,
        "K_PRE_1_years_below_threshold": int(sum(s < K1_THRESHOLD for s in pjm_shares)),
        "K_PRE_1_FIRES": bool(sum(s < K1_THRESHOLD for s in pjm_shares) >= 2),
        "K_PRE_2_reaches_gw": reaches,
        "K_PRE_2_years_below_threshold": int(sum(r < K2_THRESHOLD_GW for r in reaches)),
        "K_PRE_2_FIRES": bool(sum(r < K2_THRESHOLD_GW for r in reaches) >= 2),
    }

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}\n")

    print("== K-PRE-1 capability exceedance (aligned key) ==")
    for y in YEARS:
        print(f"  {y}")
        for seam, v in rec["k_pre_1"][str(y)]["aligned"].items():
            print(f"    {seam:9s} model {v['mean_model_gross_import_gw']:.2f} GW vs observed-max "
                  f"{v['mean_observed_max_gw']:.2f} GW  exceed {v['exceedance_hours']:3d}/{v['n']} "
                  f"= {v['exceedance_share']*100:5.1f}%  excess-when {v['mean_excess_when_exceeding_gw']:+.2f} GW")
    print(f"\n  PJM shares {['%.3f' % s for s in pjm_shares]} "
          f"-> K-PRE-1 {'FIRES (KILL)' if rec['verdict']['K_PRE_1_FIRES'] else 'does not fire'}")

    print("\n== K-PRE-2 reach ==")
    for y in YEARS:
        v = rec["k_pre_2"][str(y)]
        print(f"  {y} reach {v['reach_gw']:.3f} GW vs object {v['object_over_import_gw']:.3f} GW   "
              + "  ".join(f"{k} {x:+.3f}" for k, x in v["per_seam_gw"].items()))
    print(f"  -> K-PRE-2 {'FIRES (KILL)' if rec['verdict']['K_PRE_2_FIRES'] else 'does not fire'}")

    print("\n== K-PRE-3 evidence: Midwest zonal price separation ==")
    for y in YEARS:
        v = rec["k_pre_3_evidence"][str(y)]
        print(f"  {y} scarce spread ${v['scarce_mean_spread']:.2f} "
              f"separated>{0.01}: {v['scarce_share_separated_gt_0p01']*100:.1f}% "
              f"(annual {v['annual_share_separated_gt_0p01']*100:.1f}%)")

    print("\n== reported: price reach at the model's own slope ==")
    for y in YEARS:
        v = rec["reported_price_reach"][str(y)]
        print(f"  {y} slope(top20%) {v['summer_top20pct_slope_usd_per_gw']:.2f} $/GW x reach "
              f"{v['reach_gw']:.2f} GW = {v['implied_price_lift_usd_at_top_slope']:+.2f} $/MWh "
              f"(model {v['scarce_mean_model_price']:.0f} vs actual {v['scarce_mean_actual_rt']:.0f})")

    print("\n== reported: production-envelope hour-key rotation ==")
    for y in YEARS:
        for seam, v in rec["reported_envelope_rotation"][str(y)].items():
            print(f"  {y} {seam:9s} prod {v['mean_production_cap_gw']:.3f} vs aligned "
                  f"{v['mean_aligned_cap_gw']:.3f} GW  mean|Δ| {v['mean_abs_diff_mw']:.1f} MW  "
                  f"max|Δ| {v['max_abs_diff_mw']:.0f} MW")


if __name__ == "__main__":
    main()
