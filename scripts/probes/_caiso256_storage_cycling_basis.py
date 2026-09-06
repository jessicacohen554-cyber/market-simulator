"""caiso-256 (ZERO LP): does "the model OVER-CYCLES storage" survive its own basis?

Registered in
``results/calibration/PRECOMMIT-caiso256-storage-cycling-basis-2026-09-06.md``.
caiso-255b (queue item 2) read the keeper's ``hourly/storage_<year>.parquet``
summed over BOTH techs (``li_ion`` + ``pumped_storage``) against EIA-930 CISO
``NG: OTH``, which EXCLUDES pumped storage by construction (FINDING-caiso168
§3, DO-NOT-REDO #1 — the caiso-121 all-tech-vs-PS-excluding basis error).
This probe re-states the comparison battery-only and then separates a CONDUCT
shortfall from a CAPACITY one, using the fact that the armed
``caiso_storage_shape_anchor`` caps the battery fleet at a per-hod p95 of the
measured ratio (``model/storage.py::caiso_storage_shape_caps``).

Every actual comes from ``eia930.frames._eia_hourly_frame_filled`` — row k is
local hour k on the model's clock (caiso-255b §6 DO-NOT-REDO #1); the raw
parquet's hour-ending stamps are never read.

Gates (thresholds fixed in the PRECOMMIT before this file ran):

* G-BASIS       li_ion + pumped_storage reproduces caiso-255b's 35.4 / 42.1
                GWh/d (2025) to +/-0.1; battery-only model/actual discharge
                ratio in [0.90, 1.00] every year.
* G-INTENSITY   cycling intensity = daily discharge / p99 hourly net discharge,
                model vs actual within +/-5 % every year (P-1).
* G-FLEET-BATT  model p99 / actual p99 net discharge in [0.88, 0.98] (P-2).
* G-CAP         share of hod-19 hours with li_ion discharge within 1 % of its
                shape-anchor cap >= 50 % every year (P-3); needs a fleet_only
                rebuild on the keeper recipe (skipped under --no-rebuild).
* D-PROFILE     hod diff li_ion net minus NG:OTH; belly |diff| <= 400 MW and
                22-23 diff > 0 (P-4) — reported.
* D-SPREAD      realised arbitrage margin vs the LP's own hurdle (P-5) —
                reported.
* D-PS          pumped-storage model cycling, reported beside the caiso-141
                wall; no comparator is constructed (caiso-168 §8 #4).

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso256_storage_cycling_basis.py
    PYTHONPATH=.:src uv run python scripts/probes/_caiso256_storage_cycling_basis.py --no-rebuild
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.data.eia930.frames import _eia_hourly_frame_filled  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
OUT = REPO / "results/calibration/_caiso256_storage_cycling_basis.json"
YEARS = (2023, 2024, 2025)
T = 8760
BELLY = (10, 15)
PEAK_HOD = 19
#: caiso-255b's published all-tech pair for 2025 (FINDING §2), the G-BASIS
#: reproduction target.
PUB_2025 = {"dis": 35.4, "chg": 42.1}
#: Storage tiebreaker (CLAUDE.md rule 9 [R-EPSILON]).
EPS = 0.001
#: Keeper run_config: battery_dispatch_adder 5.0, storage_rte_4hr 0.85.
ADDER = 5.0
RTE = 0.85
#: Registered thresholds (PRECOMMIT §3).
G_BASIS_BAND = (0.90, 1.00)
G_INT_TOL = 0.05
G_FLEET_BAND = (0.88, 0.98)
G_CAP_MIN_SHARE = 0.50
G_CAP_TOL = 0.01
D_BELLY_MAX = 400.0


def actual(year: int) -> np.ndarray:
    """EIA-930 CISO ``NG: OTH`` on the MODEL's clock, 8760 rows. Never the raw stamps."""
    f = _eia_hourly_frame_filled("CISO", year)
    if f is None or len(f) != T:
        raise SystemExit(f"EIA-930 CISO {year}: expected an {T}-row clean frame")
    return pd.to_numeric(f["NG: OTH"], errors="coerce").to_numpy(dtype=float)


def model(year: int) -> dict[str, pd.DataFrame]:
    """Keeper P1 storage per tech, indexed 0..8759."""
    s = pd.read_parquet(BUNDLE / f"hourly/storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    out = {}
    for tech, g in s.groupby("tech"):
        g = g.set_index("hour").sort_index().reindex(range(T)).fillna(0.0)
        out[str(tech)] = g[["charge_mw", "discharge_mw"]]
    return out


def system_price(year: int) -> np.ndarray:
    """Load-weighted ISO-mean P1 price per hour (system sidecar carries zones)."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    s = s.assign(pd=s["price"] * s["demand"])
    g = s.groupby("hour")[["pd", "demand"]].sum()
    return (g["pd"] / g["demand"]).reindex(range(T)).to_numpy(dtype=float)


def _fleet_dis_cap(year: int) -> np.ndarray | None:
    """Fleet-wide li_ion discharge cap per hour from the shipped anchor builder.

    Two ``fleet_only`` rebuilds' worth of plumbing is not needed — one rebuild on
    the keeper's own recipe hands back ``storage_units`` and
    ``storage_power_cap``; the cap is ``caiso_storage_shape_caps`` on those.
    """
    from market_sim.model.storage import _battery_mask, caiso_storage_shape_caps
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(BUNDLE), year))
    clear_fleet_caches()
    with contextlib.redirect_stderr(io.StringIO()):
        st = run_year(
            year, meta["iso"], T, float(meta["gas_prices"][str(year)]), {},
            fleet_only=True, **kw,
        )
    units = st["storage_units"]
    _chg, dis = caiso_storage_shape_caps(st["storage_power_cap"], units, year, T)
    mask = _battery_mask(units)
    return dis[mask].sum(axis=0)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-rebuild", action="store_true", help="skip G-CAP (no fleet rebuild)")
    a = ap.parse_args()

    res: dict = {"session": "caiso-256", "basis": {}, "years": {}, "gates": {}}
    hod = np.arange(T) % 24
    idx = pd.date_range("2023-01-01", periods=T, freq="h")  # non-leap hod/month template
    eta_dis = RTE**0.5
    hurdle = ADDER + EPS * (1.0 + 1.0 / RTE)  # $/MWh on the efficiency-adjusted margin

    g_basis_ok = g_int_ok = g_fleet_ok = g_cap_ok = True
    p4_ok = p5_ok = True
    for y in YEARS:
        oth = actual(y)
        m = model(y)
        li = m["li_ion"]
        ps = m.get("pumped_storage")
        a_dis = np.nansum(np.clip(oth, 0, None)) / 1e3 / 365
        a_chg = -np.nansum(np.clip(oth, None, 0)) / 1e3 / 365
        li_net = (li["discharge_mw"] - li["charge_mw"]).to_numpy(dtype=float)
        m_dis = float(li["discharge_mw"].sum()) / 1e3 / 365
        m_chg = float(li["charge_mw"].sum()) / 1e3 / 365
        ps_dis = float(ps["discharge_mw"].sum()) / 1e3 / 365 if ps is not None else 0.0
        ps_chg = float(ps["charge_mw"].sum()) / 1e3 / 365 if ps is not None else 0.0
        both = (li["discharge_mw"] > 1.0) & (li["charge_mw"] > 1.0)

        # --- G-INTENSITY / G-FLEET-BATT ------------------------------------
        a_p99 = float(np.nanpercentile(np.clip(oth, 0, None), 99))
        m_p99 = float(np.percentile(np.clip(li_net, 0, None), 99))
        a_int = a_dis * 1e3 / a_p99  # h/day at the fleet's coincident rate
        m_int = m_dis * 1e3 / m_p99
        int_ratio = m_int / a_int
        fleet_ratio = m_p99 / a_p99

        # --- D-PROFILE -------------------------------------------------------
        ao = pd.Series(oth).groupby(hod).mean()
        mo = pd.Series(li_net).groupby(hod).mean()
        diff = (mo - ao).reindex(range(24))
        belly = diff.loc[BELLY[0] : BELLY[1]]
        p4 = bool(belly.abs().max() <= D_BELLY_MAX and diff.loc[22] > 0 and diff.loc[23] > 0)

        # --- D-SPREAD --------------------------------------------------------
        lam = system_price(y)
        wd = li["discharge_mw"].to_numpy(dtype=float)
        wc = li["charge_mw"].to_numpy(dtype=float)
        lam_d = float(np.average(lam, weights=wd)) if wd.sum() > 0 else float("nan")
        lam_c = float(np.average(lam, weights=wc)) if wc.sum() > 0 else float("nan")
        margin = lam_d - lam_c / RTE  # $/MWh discharged, after round-trip losses
        p5 = bool(margin >= hurdle)

        # --- G-CAP -----------------------------------------------------------
        cap_row: dict = {"skipped": True}
        if not a.no_rebuild:
            cap = _fleet_dis_cap(y)
            at_peak = hod == PEAK_HOD
            dis19 = li["discharge_mw"].to_numpy(dtype=float)[at_peak]
            cap19 = cap[at_peak]
            share = float(np.mean(dis19 >= (1.0 - G_CAP_TOL) * cap19))
            cap_row = {
                "skipped": False,
                "hod19_share_at_cap": round(share, 4),
                "hod19_mean_dis_mw": round(float(dis19.mean()), 1),
                "hod19_mean_cap_mw": round(float(cap19.mean()), 1),
                "annual_max_cap_mw": round(float(cap.max()), 1),
                "annual_max_dis_mw": round(float(li["discharge_mw"].max()), 1),
                "pass": bool(share >= G_CAP_MIN_SHARE),
            }
            g_cap_ok &= cap_row["pass"]

        ratio = m_dis / a_dis
        g_basis_ok &= G_BASIS_BAND[0] <= ratio <= G_BASIS_BAND[1]
        g_int_ok &= abs(int_ratio - 1.0) <= G_INT_TOL
        g_fleet_ok &= G_FLEET_BAND[0] <= fleet_ratio <= G_FLEET_BAND[1]
        p4_ok &= p4
        p5_ok &= p5

        res["years"][str(y)] = {
            "actual_ng_oth_gwh_per_day": {"discharge": round(a_dis, 2), "charge": round(a_chg, 2)},
            "model_li_ion_gwh_per_day": {"discharge": round(m_dis, 2), "charge": round(m_chg, 2)},
            "model_pumped_storage_gwh_per_day": {"discharge": round(ps_dis, 2), "charge": round(ps_chg, 2)},
            "model_all_tech_gwh_per_day": {"discharge": round(m_dis + ps_dis, 2), "charge": round(m_chg + ps_chg, 2)},
            "li_ion_hours_both_legs_gt_1mw": int(both.sum()),
            "battery_only_ratio_model_over_actual": {"discharge": round(ratio, 4), "charge": round(m_chg / a_chg, 4)},
            "implied_rte": {"actual": round(a_dis / a_chg, 4), "model": round(m_dis / m_chg, 4)},
            "p99_net_discharge_mw": {"actual": round(a_p99, 1), "model": round(m_p99, 1)},
            "max_net_discharge_mw": {"actual": round(float(np.nanmax(oth)), 1), "model": round(float(li_net.max()), 1)},
            "cycling_intensity_h_per_day": {"actual": round(a_int, 3), "model": round(m_int, 3), "ratio": round(int_ratio, 4)},
            "fleet_ratio_p99_model_over_actual": round(fleet_ratio, 4),
            "hod_diff_li_ion_net_minus_oth_mw": [round(float(v), 1) for v in diff.to_numpy()],
            "belly_max_abs_diff_mw": round(float(belly.abs().max()), 1),
            "hod22_23_diff_mw": [round(float(diff.loc[22]), 1), round(float(diff.loc[23]), 1)],
            "spread": {
                "lambda_discharge_weighted": round(lam_d, 2),
                "lambda_charge_weighted": round(lam_c, 2),
                "raw_spread": round(lam_d - lam_c, 2),
                "margin_after_rte": round(margin, 2),
                "hurdle_adder_plus_eps": round(hurdle, 3),
                "eta_dis": round(eta_dis, 4),
                "P5_pass": p5,
            },
            "G_CAP": cap_row,
            "P4_pass": p4,
        }

    y25 = res["years"]["2025"]["model_all_tech_gwh_per_day"]
    repro = abs(y25["discharge"] - PUB_2025["dis"]) <= 0.1 and abs(y25["charge"] - PUB_2025["chg"]) <= 0.1
    res["basis"] = {
        "caiso255b_published_2025_all_tech": PUB_2025,
        "reproduced_as_li_ion_plus_pumped_storage": bool(repro),
        "actual_series": "EIA-930 CISO NG: OTH via _eia_hourly_frame_filled; discharge = hour-separated positive part, charge = negative part",
        "note": "NG: OTH excludes pumped storage (FINDING-caiso168 §3); the all-tech sum is the caiso-121 basis error named in caiso-168 §8 #1",
    }
    res["gates"] = {
        "G_BASIS": {"reproduced": bool(repro), "ratio_in_band_all_years": bool(g_basis_ok), "band": G_BASIS_BAND, "pass": bool(repro and g_basis_ok)},
        "G_INTENSITY_P1": {"tol": G_INT_TOL, "pass": bool(g_int_ok)},
        "G_FLEET_BATT_P2": {"band": G_FLEET_BAND, "pass": bool(g_fleet_ok)},
        "G_CAP_P3": {"min_share": G_CAP_MIN_SHARE, "pass": (None if a.no_rebuild else bool(g_cap_ok))},
        "D_PROFILE_P4": {"belly_max_abs_mw": D_BELLY_MAX, "pass": bool(p4_ok)},
        "D_SPREAD_P5": {"pass": bool(p5_ok)},
    }
    OUT.write_text(json.dumps(res, indent=1))
    for y in YEARS:
        r = res["years"][str(y)]
        print(
            f"{y}: actual dis/chg {r['actual_ng_oth_gwh_per_day']['discharge']}/{r['actual_ng_oth_gwh_per_day']['charge']} | "
            f"li_ion {r['model_li_ion_gwh_per_day']['discharge']}/{r['model_li_ion_gwh_per_day']['charge']} | "
            f"PS {r['model_pumped_storage_gwh_per_day']['discharge']}/{r['model_pumped_storage_gwh_per_day']['charge']} | "
            f"ratio {r['battery_only_ratio_model_over_actual']['discharge']} | intensity ratio {r['cycling_intensity_h_per_day']['ratio']} "
            f"| fleet p99 ratio {r['fleet_ratio_p99_model_over_actual']} | belly max {r['belly_max_abs_diff_mw']} | 22/23 {r['hod22_23_diff_mw']} "
            f"| margin {r['spread']['margin_after_rte']} vs hurdle {r['spread']['hurdle_adder_plus_eps']} | G-CAP {r['G_CAP']}"
        )
    print("GATES:", json.dumps(res["gates"]))


if __name__ == "__main__":
    main()
