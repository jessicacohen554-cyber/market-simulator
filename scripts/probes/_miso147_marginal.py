"""miso-147 leg (ii) + Q4 — the merit-order marginal census (PREREG §4.4).

Reuses the miso-144 CORRECTED same-universe construction verbatim (fleet
THERMAL_FLEET rows vs sidecar THERMAL_COLS need minus the INJECTED must-run
classes; v2 adds the rbdc reserve held_mw): P-8 gates each stratum on the
miso-143 bars (median |p_hat - P1| <= $4.00, r >= 0.85, v2/lo). A stratum
failing P-8 gets NO marginal reading. Then, in each gated stratum: the
marginal-class census (lo/hi endpoints), the quantity-agree deficit split
(PREREG P-3), and the S0 clearing-offer-vs-actual reading (PREREG P-6a).

Writes ``results/calibration/_miso147_marginal.json``.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _miso147_strata import (  # noqa: E402
    FAMILY_TO_KLASSES,
    FLOOR_MW,
    FLOOR_FRAC,
    REPO,
    TAIL_USD,
    THERMAL_COLS,
    YEARS,
    bucket_series,
    campd_family_hourly,
    campd_units,
    c3a_weight,
    clear_many,
    fleet_pack,
    hygiene,
    model_price,
    parasitic_map,
    sidecar_pivot,
    strata,
    wmean,
)
from _miso144_attribution import INJECTED, THERMAL_FLEET, reserve_held  # noqa: E402
from _miso137_c3a_gap_decomposition import actual_hourly  # noqa: E402

OUT = REPO / "results" / "calibration" / "_miso147_marginal.json"
P8_MEDIAN_USD = 4.00  # miso-143 bars, carried by PREREG §5 P-8
P8_R = 0.85
P3_HI = 0.50  # deficit persistence in quantity-agree hours => offer object
P3_LO = 0.25  # below => composition-borne


def quantity_agree_mask(year: int) -> tuple[np.ndarray, dict]:
    """Hours where every Pair-B family |model - CAMPD_net| <= its per-hour floor."""
    piv = sidecar_pivot(year)
    units, _meta = campd_units(year)
    fam_net = campd_family_hourly(units, "net", parasitic_map())
    agree = np.ones(piv.shape[0], dtype=bool)
    per_fam = {}
    for fam, kl in FAMILY_TO_KLASSES.items():
        m = bucket_series(piv, kl)
        a = fam_net[fam]
        fl = np.maximum(FLOOR_MW, FLOOR_FRAC * a)
        ok = np.abs(m - a) <= fl
        per_fam[fam] = int(ok.sum())
        agree &= ok
    del units
    return agree, per_fam


def year_block(year: int) -> dict:
    s = strata(year)
    rt = s["rt"]
    w = c3a_weight(year)
    p1 = model_price(year)
    fp = fleet_pack(year)
    kl = fp["klass"]
    thermal_rows = np.isin(kl, THERMAL_FLEET)
    kl_t = kl[thermal_rows]
    cap = (fp["pmax"][:, None] * fp["availability"])[thermal_rows]
    mc0 = fp["mc_base"][thermal_rows].astype(float)
    off = {"lo": mc0, "hi": mc0 + fp["markup"][thermal_rows][:, None]}

    piv = sidecar_pivot(year)
    need_all = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
    inj = sum(piv[c].to_numpy(float) for c in INJECTED)
    need_fleet = need_all - inj
    held, _ = reserve_held(year)

    agree, agree_per_fam = quantity_agree_mask(year)

    out: dict = {"quantity_agree_hours_per_family": agree_per_fam}
    census_strata = [n for n in s["masks"] if n != "S3"]  # S3: composition only
    for sname in census_strata:
        mask = s["masks"][sname] & np.isfinite(p1) & np.isfinite(need_fleet) & (need_fleet > 0)
        hrs = np.nonzero(mask)[0]
        blk: dict = {"n_hours": int(hrs.size)}
        # P-8 instrument gate on the corrected construction, v2 (need + reserve), lo
        p_hat_v2, rows_v2 = clear_many(off["lo"], cap, need_fleet[hrs] + held[hrs], hrs)
        d = p1[hrs] - p_hat_v2
        med = float(np.median(np.abs(d)))
        r = float(np.corrcoef(p_hat_v2, p1[hrs])[0, 1]) if hrs.size > 2 else float("nan")
        gate = bool(med <= P8_MEDIAN_USD and r >= P8_R)
        blk["P8"] = {"median_abs_err": round(med, 3), "r": round(r, 4), "pass": gate,
                     "construction": "miso-144 corrected: THERMAL_FLEET rows vs "
                                     "THERMAL_COLS need - INJECTED + rbdc held (v2), lo"}
        if not gate:
            blk["marginal_reading"] = "WITHHELD (P-8 failed for this stratum)"
            out[sname] = blk
            continue
        # marginal-class census at both endpoints
        census: dict = {}
        for tag in ("lo", "hi"):
            p_hat, rows = clear_many(off[tag], cap, need_fleet[hrs] + held[hrs], hrs)
            marg = np.where(rows >= 0, kl_t[np.clip(rows, 0, None)], "UNREACHED")
            shares = {
                k: round(float(np.isin(marg, [k]).mean()), 4)
                for k in sorted(set(marg.tolist()))
            }
            census[tag] = {
                "marginal_class_share_of_hours": shares,
                "clear_minus_actual_rt_wmean": round(wmean(
                    np.where(np.isfinite(rt[hrs]), p_hat - rt[hrs], np.nan),
                    w[hrs], np.ones(hrs.size, bool)), 3),
                "clear_minus_p1_wmean": round(wmean(p_hat - p1[hrs], w[hrs],
                                                    np.ones(hrs.size, bool)), 3),
            }
        blk["census"] = census
        # P-3 split (S1 only is adjudicated; reported for all census strata)
        m_all = s["masks"][sname] & np.isfinite(rt) & np.isfinite(p1)
        m_agree = m_all & agree
        d_all = wmean(p1 - rt, w, m_all)
        d_agree = wmean(p1 - rt, w, m_agree)
        blk["deficit_split"] = {
            "deficit_all": round(d_all, 3),
            "deficit_quantity_agree": round(d_agree, 3) if m_agree.sum() else None,
            "n_agree": int(m_agree.sum()),
            "agree_share_of_hours": round(float(m_agree.sum() / max(1, m_all.sum())), 4),
            "persistence_ratio": (
                round(d_agree / d_all, 4) if m_agree.sum() and abs(d_all) > 1e-9 else None
            ),
        }
        # S0/P-6a: ordinary-hours clearing offer vs actual
        if sname in ("S0", "MAYCTRL"):
            mo = s["masks"][sname] & np.isfinite(rt) & (rt <= TAIL_USD) & np.isfinite(p1) & (need_fleet > 0)
            ho = np.nonzero(mo)[0]
            p_hat_o, _ = clear_many(off["lo"], cap, need_fleet[ho] + held[ho], ho)
            blk["P6a_ordinary"] = {
                "clear_lo_minus_actual_rt_wmean": round(wmean(
                    p_hat_o - rt[ho], w[ho], np.ones(ho.size, bool)), 3),
                "p1_minus_actual_rt_wmean": round(wmean(p1 - rt, w, mo), 3),
                "n_hours": int(ho.size),
            }
        out[sname] = blk
    return out


def run() -> dict:
    hygiene()
    res: dict = {"session": "miso-147", "years": {}}
    for year in YEARS:
        res["years"][str(year)] = year_block(year)
    s1 = res["years"]["2025"]["S1"]
    p3 = None
    if s1.get("deficit_split"):
        pr = s1["deficit_split"]["persistence_ratio"]
        if pr is not None:
            verdict = ("offer_object_persists" if pr >= P3_HI
                       else ("composition_borne" if pr <= P3_LO else "BOTH_reported"))
            p3 = {"persistence_ratio": pr, "verdict": verdict,
                  "bars": {"hi": P3_HI, "lo": P3_LO},
                  "note": "adjudicated on S1-2025 (PREREG §5 P-3)"}
    res["P3"] = p3 or {"verdict": "NOT_COMPUTABLE (P-8 failed or no agree hours)"}
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print("P-3:", json.dumps(r["P3"], indent=1))
    for y in ("2023", "2024", "2025"):
        for sname, blk in r["years"][y].items():
            if isinstance(blk, dict) and "P8" in blk:
                print(y, sname, "P-8", "PASS" if blk["P8"]["pass"] else "FAIL",
                      blk["P8"]["median_abs_err"], blk["P8"]["r"])
    print(f"-> {OUT}")
