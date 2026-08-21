"""miso-174 — corroborating evidence: WHY the model over-imports in scarce hours.

READ-ONLY, **NOT a gate**. The pre-registered kills live in
``_miso174_import_limit_precheck.py`` and are untouched by this file; this is
the supporting measurement the adjudication cites for the POSITIVE half of its
claim — having established (K-PRE-1) that the model never exceeds the seam's
observed transfer capability, it shows what DOES set the scarce-hour import.

Measures, in MISO's own scarce hours (summer, MISO RT > $200/MWh), the
NEIGHBOURS' measured prices against MISO's, and the model's own price in the
same hours. Nothing here re-enters a solve (rule 13 ``[R-MEASURED]``); the
neighbour price series are read only to characterise the residual.

Run:  python3 scripts/probes/_miso174_seam_price_evidence.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _miso174_seam_overimport_decomposition import (  # noqa: E402
    HOURS, YEARS, build_frames, hour_sets, model_seam_flows,
)

VS = ROOT / "data" / "raw" / "_validation-source"
OUT = ROOT / "results" / "calibration" / "_miso174_seam_price_evidence.json"


def series(path: Path, year: int, col: str) -> np.ndarray:
    """Return one column of a validation-source LMP parquet on the model hour key."""
    d = pd.read_parquet(path)
    d = d[d["year"] == year]
    return d.set_index("hour")[col].reindex(range(HOURS)).to_numpy(dtype=float)


def main() -> None:
    """Measure the neighbour prices and the seams' scarcity response; write the record."""
    frames = build_frames()
    rec: dict = {"session": "miso-174", "note": "evidence only — not a pre-registered gate"}
    for y in YEARS:
        df = frames[y]
        m = hour_sets(df)["summer_scarce_rt200"]
        net, by_side = model_seam_flows(y)

        miso_rt = df["rt"].to_numpy()
        miso_model = df["price"].to_numpy()
        pjm_border = series(VS / "pjm_border_lmp_hourly_MISO.parquet", y, "price")
        pjm_rt = series(VS / "actual_lmp_hourly_PJM.parquet", y, "rt")
        spp_rt = series(VS / "actual_lmp_hourly_SPP.parquet", y, "rt")

        def blk(a: np.ndarray) -> float:
            return float(np.nanmean(a[m]))

        pjm_imp = by_side[("PJM", "imp")].to_numpy() if ("PJM", "imp") in by_side.columns else np.zeros(HOURS)
        spread_measured = miso_rt - pjm_border
        rec[str(y)] = {
            "n": int(m.sum()),
            "miso_actual_rt": blk(miso_rt),
            "miso_model_price": blk(miso_model),
            "pjm_border_hub_lmp": blk(pjm_border),
            "pjm_system_rt": blk(pjm_rt),
            "spp_rt": blk(spp_rt),
            # the measured import incentive: MISO RT minus the MISO-facing PJM border hub
            "measured_miso_minus_pjm_border": blk(spread_measured),
            # the MODEL's incentive in the same hours: its own price vs the same border hub
            "model_miso_minus_pjm_border": blk(miso_model - pjm_border),
            "hours_pjm_border_above_miso_model": int(np.nansum(pjm_border[m] > miso_model[m])),
            "hours_pjm_border_above_miso_actual": int(np.nansum(pjm_border[m] > miso_rt[m])),
            "hours_pjm_border_gt_200": int(np.nansum(pjm_border[m] > 200.0)),
            "hours_spp_rt_gt_200": int(np.nansum(spp_rt[m] > 200.0)),
            "model_pjm_gross_import_gw": float(np.mean(pjm_imp[m])) / 1000,
            # correlation of the measured PJM-seam import with the measured spread,
            # over the whole summer — does the real seam respond to the spread?
            "summer_corr_measured_spread_vs_measured_seam_flow": None,
        }

        su = hour_sets(df)["summer"]
        from _miso174_seam_overimport_decomposition import diba_wide
        w = diba_wide(y, -1)
        meas_pjm = w[[c for c in w.columns if str(c) in ("PJM", "IESO")]].sum(axis=1, min_count=1).to_numpy()
        ok = su & np.isfinite(meas_pjm) & np.isfinite(spread_measured)
        rec[str(y)]["summer_corr_measured_spread_vs_measured_seam_flow"] = float(
            np.corrcoef(spread_measured[ok], meas_pjm[ok])[0, 1]
        )
        ok2 = su & np.isfinite(meas_pjm)
        rec[str(y)]["summer_corr_measured_spread_vs_model_seam_flow"] = float(
            np.corrcoef(spread_measured[ok2], pjm_imp[ok2])[0, 1]
        )

    # ---- the scarcity RESPONSE: how each seam moves when MISO goes tight ----
    from _miso174_seam_overimport_decomposition import diba_wide as _dw
    rec["scarcity_response"] = {}
    for y in YEARS:
        df = frames[y]
        s = hour_sets(df)
        su, m = s["summer"], s["summer_scarce_rt200"]
        net, _ = model_seam_flows(y)
        w = _dw(y, -1)
        seams = {"PJM": ("PJM", "IESO"), "SPP": ("SWPP", "SPA"),
                 "South": ("SOCO", "TVA", "AECI", "LGEE", "SIKE"), "Manitoba": ("MHEB",)}
        row = {}
        for seam, dl in seams.items():
            cols = [c for c in w.columns if str(c) in dl]
            meas = w[cols].sum(axis=1, min_count=1).to_numpy()
            mod = net[seam].to_numpy() if seam in net.columns else np.zeros(HOURS)
            row[seam] = {
                "measured_summer_gw": float(np.nanmean(meas[su])) / 1000,
                "measured_scarce_gw": float(np.nanmean(meas[m])) / 1000,
                "measured_response_gw": float(np.nanmean(meas[m]) - np.nanmean(meas[su])) / 1000,
                "model_summer_gw": float(np.mean(mod[su])) / 1000,
                "model_scarce_gw": float(np.mean(mod[m])) / 1000,
                "model_response_gw": float(np.mean(mod[m]) - np.mean(mod[su])) / 1000,
                "measured_mean_abs_hourly_change_mw": float(np.nanmean(np.abs(np.diff(meas[su])))),
                "model_mean_abs_hourly_change_mw": float(np.nanmean(np.abs(np.diff(mod[su])))),
            }
        rec["scarcity_response"][str(y)] = row

    OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT}\n")
    print("== scarcity response: seam flow in MISO's scarce hours vs its own summer mean ==")
    for y in YEARS:
        print(f"  {y}")
        for seam, v in rec["scarcity_response"][str(y)].items():
            print(f"    {seam:9s} measured {v['measured_summer_gw']:+.2f} -> {v['measured_scarce_gw']:+.2f} "
                  f"({v['measured_response_gw']:+.2f})   model {v['model_summer_gw']:+.2f} -> "
                  f"{v['model_scarce_gw']:+.2f} ({v['model_response_gw']:+.2f})   "
                  f"|Δ/h| meas {v['measured_mean_abs_hourly_change_mw']:.0f} / model "
                  f"{v['model_mean_abs_hourly_change_mw']:.0f} MW")
    print()
    for y in YEARS:
        v = rec[str(y)]
        print(f"{y} (n={v['n']} scarce hours)")
        print(f"   MISO actual RT ${v['miso_actual_rt']:7.2f}   model ${v['miso_model_price']:7.2f}")
        print(f"   PJM MISO-facing border hub ${v['pjm_border_hub_lmp']:7.2f}   PJM system RT "
              f"${v['pjm_system_rt']:7.2f}   SPP RT ${v['spp_rt']:7.2f}")
        print(f"   measured MISO-minus-border ${v['measured_miso_minus_pjm_border']:+8.2f}   "
              f"MODEL-minus-border ${v['model_miso_minus_pjm_border']:+8.2f}")
        print(f"   border above MODEL price in {v['hours_pjm_border_above_miso_model']}/{v['n']} h; "
              f"above ACTUAL in {v['hours_pjm_border_above_miso_actual']}/{v['n']} h; "
              f"border >$200 in {v['hours_pjm_border_gt_200']} h; SPP >$200 in {v['hours_spp_rt_gt_200']} h")
        print(f"   summer corr(spread, seam flow): measured "
              f"{v['summer_corr_measured_spread_vs_measured_seam_flow']:+.3f}  model "
              f"{v['summer_corr_measured_spread_vs_model_seam_flow']:+.3f}\n")


if __name__ == "__main__":
    main()
