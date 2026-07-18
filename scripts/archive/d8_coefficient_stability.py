"""D-8 frozen-coefficient stability (legitimacy audit §7 D-8, out-of-sample).

Refit the model's *fitted-to-the-scored-years* coefficient families on a
TRAINING subset of the calibration years, then measure how far the coefficients
move — and how well the training fit predicts the held-out year — relative to
the all-years fit the keepers actually ship. Nothing here solves the LP or
touches a holdout year (2022 / H1-2026); every input is the 2023-2025 CAMPD /
EIA-930 calibration data the coefficients were fitted on. It reuses each
mechanism's *own* frozen derive/probe fit code (imported, not reimplemented) so
the stability numbers are on the same estimand the keeper uses.

Three coefficient families (audit line 147 / §7 D-8 / S4 item 3):

  A. Net-load drag hinges (``ct_netload_drag``) — the template mechanism.
     Leave-2025-out: fit the evening-ramp CF-vs-net-load floor on 2023-24 only,
     predict the 2025 floor energy, compare to the all-years fit and to the
     measured 2025 CT energy. ERCOT / PJM / CAISO.

  B. Temperature-CF reliability-floor coefficients
     (``derive_reliability_coeffs``). Leave-2025-out: recompute per-(zone,class,
     limb) ``commit_frac`` / ``floor_pct`` on 2023-24 CAMPD only, compare to the
     all-years value and score the 2025-only value; report drift and any
     enable-gate flip.

  C. Coal passthrough sigmoid parameters (``COAL_SIGMOID_DEFAULTS``).
     Leave-2024-out identifiability: 2024 is the ONLY cheap-gas year, so the
     sigmoid's cheap-gas asymptote (``floor``) and midpoint (``gas_mid``) are
     sampled by one year. Report the per-year monthly delivered-gas coverage
     that identifies each parameter and what leave-2024-out removes.

Usage:
    python scripts/archive/d8_coefficient_stability.py [--iso ERCOT PJM CAISO]
Writes results/calibration/d8-coefficient-stability/{summary.json,report.md}.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

TRAIN = (2023, 2024)  # leave-2025-out training window for A + B
FULL = (2023, 2024, 2025)  # the all-years fit the keepers ship
HOURS = 8760
OUT_DIR = REPO / "results" / "calibration" / "d8-coefficient-stability"


def _load_probe(rel: str, name: str):
    """Import a scripts/probes module by file path (dir not a package)."""
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _binned_median(x, y, edges, min_n=30):
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (x >= lo) & (x < hi)
        if int(sel.sum()) >= min_n:
            rows.append((0.5 * (lo + hi), float(np.median(y[sel]))))
    return np.array(rows)


# --------------------------------------------------------------------------- #
# A. Net-load drag hinges — leave-2025-out                                    #
# --------------------------------------------------------------------------- #
def _fit_line(enl, ecf, edges):
    """ERCOT/CAISO recipe: LS line through 2-GW binned evening CF, 95pct cap."""
    binned = _binned_median(enl, ecf, edges)
    slope, intercept = np.polyfit(binned[:, 0], binned[:, 1], 1)
    cap = float(np.percentile(ecf, 95))
    return {"slope": float(slope), "intercept": float(intercept), "cap": cap}


def _fit_hinge(enl, ecf, edges):
    """PJM recipe: grid-search hinge knee, LS line on the active segment."""
    binned = _binned_median(enl, ecf, edges)
    cap = float(np.percentile(ecf, 95))
    best = None
    for knee_i in range(len(binned) - 3):
        seg = binned[knee_i:]
        s, b = np.polyfit(seg[:, 0], seg[:, 1], 1)
        if s <= 0.0:
            continue
        pred = np.clip(s * binned[:, 0] + b, 0.0, cap)
        sse = float(((pred - binned[:, 1]) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, float(s), float(b))
    return {"slope": best[1], "intercept": best[2], "cap": cap}


def _floor_twh(coef, nl_gw, nameplate, ramp_mask):
    base = np.clip(coef["slope"] * nl_gw + coef["intercept"], 0.0, coef["cap"])
    return float((np.where(ramp_mask, base, 0.0) * nameplate).sum() / 1e6)


def drag_ercot():
    m = _load_probe("probes/_ct_netload_drag_fit.py", "_ct_drag_ercot")
    plants = m._ct_peaker_plants()
    nameplate = sum(plants.values())
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    evening = (hod >= 17) & (hod < 23)  # fit window (probe main)
    ramp = (hod >= 15) & (hod < 22)  # applied window (ScenarioConfig)
    per = {}
    for y in FULL:
        nl = m._net_load_eia930(y) / 1000.0
        cf, fleet_mw, _ = m._ct_fleet_cf(y, plants)
        per[y] = (nl, cf, fleet_mw)
    edges = np.arange(10, 56, 2)
    return _assemble_drag("ERCOT", per, evening, ramp, nameplate, _fit_line, edges)


def drag_pjm():
    m = importlib.import_module("derive_pjm_ct_netload_drag")
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    start, end = m.CT_EVENING_HOURS
    win = (hod >= start) & (hod < end)  # fit == applied window
    per, nameplate = {}, None
    for y in FULL:
        plants, npl = m.model_ct_peaker_plants(y)
        nameplate = npl
        mw = m.measured_ct_mw(y, set(plants))
        nl = m.pjm_net_load_mw(y) / 1000.0
        per[y] = (nl, mw / npl, mw)
    edges = np.arange(40, 145, 2)
    return _assemble_drag("PJM", per, win, win, nameplate, _fit_hinge, edges)


def drag_caiso():
    m = importlib.import_module("derive_caiso_ct_reliability_floor")
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    start, end = m.CT_EVENING_HOURS
    win = (hod >= start) & (hod < end)
    # CAISO ships a clean derive_curve(years); use it verbatim for coefficients.
    ctrain = m.derive_curve(TRAIN)
    cfull = m.derive_curve(FULL)
    train = {
        "slope": ctrain["_slope"],
        "intercept": ctrain["_intercept"],
        "cap": ctrain["_cap"],
    }
    full = {
        "slope": cfull["_slope"],
        "intercept": cfull["_intercept"],
        "cap": cfull["_cap"],
    }
    nameplate = m.model_ct_peaker_nameplate(2025)
    nl25 = m.ciso_net_load_mw(2025) / 1000.0
    mw25 = m.routed_ct_peaker_mw(2025)
    return _drag_row("CAISO", train, full, nl25, mw25, nameplate, win)


def _assemble_drag(iso, per, fit_win, ramp, nameplate, fitter, edges):
    def pooled(years):
        enl = np.concatenate([per[y][0][fit_win] for y in years])
        ecf = np.concatenate([per[y][1][fit_win] for y in years])
        return fitter(enl, ecf, edges)

    train, full = pooled(TRAIN), pooled(FULL)
    nl25, _, mw25 = per[2025]
    return _drag_row(iso, train, full, nl25, mw25, nameplate, ramp)


def _drag_row(iso, train, full, nl25, mw25, nameplate, ramp):
    zc_t = -train["intercept"] / train["slope"] if train["slope"] else float("nan")
    zc_f = -full["intercept"] / full["slope"] if full["slope"] else float("nan")
    ft = _floor_twh(train, nl25, nameplate, ramp)
    ff = _floor_twh(full, nl25, nameplate, ramp)
    meas = float(mw25.sum() / 1e6)
    return {
        "iso": iso,
        "nameplate_gw": round(nameplate / 1000.0, 2),
        "train_slope": round(train["slope"], 5),
        "full_slope": round(full["slope"], 5),
        "slope_drift_pct": _pct(train["slope"], full["slope"]),
        "train_intercept": round(train["intercept"], 4),
        "full_intercept": round(full["intercept"], 4),
        "train_zero_gw": round(zc_t, 1),
        "full_zero_gw": round(zc_f, 1),
        "zero_drift_gw": round(zc_t - zc_f, 1),
        "train_cap": round(train["cap"], 3),
        "full_cap": round(full["cap"], 3),
        "pred2025_floor_twh_trainfit": round(ft, 2),
        "pred2025_floor_twh_fullfit": round(ff, 2),
        "measured2025_ct_twh": round(meas, 2),
        "floor_pred_drift_pct": _pct(ft, ff),
    }


def _pct(a, b):
    if b == 0:
        return float("nan")
    return round(100.0 * (a - b) / abs(b), 1)


# --------------------------------------------------------------------------- #
# B. Temperature-CF reliability floor — leave-2025-out                        #
# --------------------------------------------------------------------------- #
def temp_cf(iso):
    """Recompute per-(zone,class,limb) commit_frac/floor_pct on TRAIN vs FULL.

    Reuses derive_reliability_coeffs' frozen fit helpers (_plant_map, _fit_limb,
    _limb_threshold, _group_daily_cf, _min_stable_pct) with a year-subset CAMPD
    loader so the estimand is identical to the shipped coefficient.
    """
    rc = importlib.import_module("derive_reliability_coeffs")
    iso = iso.upper()
    temps = rc._zone_temps(iso)
    pmap = rc._plant_map(iso)
    if pmap.empty:
        return []
    pmap = pmap[pmap["plant_class"].isin(rc.FOSSIL_CLASSES)].copy()
    all_codes = set(pmap["plant_code"].astype(int))
    states = rc.ISO_CAMPD_STATES.get(iso, ())

    def load_campd(years):
        frames = []
        for st in states:
            for yr in years:
                p = rc.RAW_DIR / "campd-unit-level" / f"{st}_{yr}.parquet"
                if p.exists():
                    frames.append(
                        pd.read_parquet(p, columns=["facilityId", "date", "grossLoad"])
                    )
        c = pd.concat(frames, ignore_index=True)
        c["facilityId"] = c["facilityId"].astype(int)
        c = c[c["facilityId"].isin(all_codes)].copy()
        c["date"] = pd.to_datetime(c["date"])
        return c

    campd_train = load_campd(TRAIN)
    campd_hold = load_campd((2025,))
    rows = []
    for (zone, klass), grp in pmap.groupby(["zone", "plant_class"], sort=False):
        plant_npl = dict(
            zip(grp["plant_code"].astype(int), grp["nameplate_mw"].astype(float))
        )
        nameplate = float(grp["nameplate_mw"].sum())
        msp = rc._min_stable_pct(klass)
        if msp <= 0.0:
            continue
        zt = temps[temps["zone"] == zone].set_index("date")
        if zt.empty:
            continue
        # CAISO CT classes use a net-load limb (skip here; covered by Part A).
        if iso == "CAISO" and klass in rc._CT_CLASSES:
            continue
        cf_tr = rc._group_daily_cf(campd_train, plant_npl, nameplate)
        cf_ho = rc._group_daily_cf(campd_hold, plant_npl, nameplate)
        if cf_tr.empty or cf_ho.empty:
            continue
        for driver, cold in (("tmax", False), ("tmin", True)):
            thr, _ = rc._limb_threshold(iso, klass, driver, zt)
            ft = rc._fit_limb(cf_tr, zt[f"{driver}_c"], thr, cold)
            fh = rc._fit_limb(cf_ho, zt[f"{driver}_c"], thr, cold)
            if ft is None or fh is None:
                continue
            en_tr = bool(
                (not np.isnan(ft["rho"]))
                and ft["rho"] >= rc.RHO_MIN
                and ft["n"] >= rc.N_MIN
                and ft["commit_frac"] > ft["baseline_commit"]
            )
            en_ho = bool(
                (not np.isnan(fh["rho"]))
                and fh["rho"] >= rc.RHO_MIN
                and fh["n"] >= rc.N_MIN
                and fh["commit_frac"] > fh["baseline_commit"]
            )
            # only report limbs the shipped (full) fit would enable OR the train enables
            if not (en_tr or en_ho):
                continue
            rows.append(
                {
                    "iso": iso,
                    "zone": zone,
                    "class": klass,
                    "driver": driver,
                    "train_floor_pct": round(ft["commit_frac"] * msp, 4),
                    "hold2025_floor_pct": round(fh["commit_frac"] * msp, 4),
                    "floor_drift_pct": _pct(ft["commit_frac"], fh["commit_frac"]),
                    "train_rho": round(ft["rho"], 3)
                    if not np.isnan(ft["rho"])
                    else None,
                    "hold2025_rho": round(fh["rho"], 3)
                    if not np.isnan(fh["rho"])
                    else None,
                    "train_enabled": en_tr,
                    "hold2025_enabled": en_ho,
                    "enable_flip": en_tr != en_ho,
                    "train_n": ft["n"],
                    "hold2025_n": fh["n"],
                }
            )
    return rows


# --------------------------------------------------------------------------- #
# C. Coal sigmoid identifiability — leave-2024-out                            #
# --------------------------------------------------------------------------- #
def coal_sigmoid_identifiability(iso):
    """Per-year monthly delivered-gas coverage vs each ISO's sigmoid gas_mid.

    The sigmoid ``passthrough = floor + (ceil-floor)*logistic((gas-gas_mid)*
    gas_slope)`` is identified in gas where samples exist: the cheap-gas
    asymptote (floor) needs months well below gas_mid; the dear-gas asymptote
    (ceil) needs months well above. Report, per calendar year, the fraction of
    monthly gas below/near/above each ISO's gas_mid, so leave-2024-out's effect
    on floor/gas_mid identification is explicit (2024 = the only cheap-gas year).
    """
    from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig
    from market_sim.data import fuel

    iso = iso.upper()
    supplies = sorted({s for (i, s) in COAL_SIGMOID_DEFAULTS if i == iso})
    if not supplies:
        return None
    gas_mid = COAL_SIGMOID_DEFAULTS[(iso, supplies[0])]["gas_mid"]
    # Monthly delivered gas ($/MMBtu) the sigmoid keys on, per year.
    cfg = ScenarioConfig(iso=iso, mode="backcast")
    per_year = {}
    for y in FULL:
        try:
            g = np.asarray(fuel._gas_series(cfg, y, HOURS), dtype=float)
        except Exception as exc:  # noqa: BLE001
            per_year[y] = {"error": str(exc)[:120]}
            continue
        # collapse to the 12 monthly levels
        hpm = np.array([744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744])
        idx, monthly = 0, []
        for h in hpm:
            monthly.append(float(np.median(g[idx : idx + h])))
            idx += h
        monthly = np.array(monthly)
        per_year[y] = {
            "gas_min": round(float(monthly.min()), 2),
            "gas_max": round(float(monthly.max()), 2),
            "gas_mean": round(float(monthly.mean()), 2),
            "months_below_mid": int((monthly < gas_mid).sum()),
            "months_near_mid": int((np.abs(monthly - gas_mid) <= 0.35).sum()),
            "months_above_mid": int((monthly > gas_mid).sum()),
        }
    return {"iso": iso, "gas_mid": gas_mid, "supplies": supplies, "per_year": per_year}


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=["ERCOT", "PJM", "CAISO"])
    ap.add_argument("--temp-iso", nargs="*", default=["ERCOT", "PJM"])
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    out = {
        "train_years": TRAIN,
        "full_years": FULL,
        "drag": [],
        "temp_cf": [],
        "coal_sigmoid": [],
    }

    drag_fns = {"ERCOT": drag_ercot, "PJM": drag_pjm, "CAISO": drag_caiso}
    for iso in args.iso:
        if iso.upper() in drag_fns:
            print(f"[A] net-load drag: {iso} ...", flush=True)
            try:
                out["drag"].append(drag_fns[iso.upper()]())
            except Exception as exc:  # noqa: BLE001
                out["drag"].append({"iso": iso, "error": repr(exc)[:200]})
                print(f"    ERROR {iso}: {exc!r}", flush=True)

    for iso in args.temp_iso:
        print(f"[B] temp-CF floor: {iso} ...", flush=True)
        try:
            out["temp_cf"].extend(temp_cf(iso))
        except Exception as exc:  # noqa: BLE001
            out["temp_cf"].append({"iso": iso, "error": repr(exc)[:200]})
            print(f"    ERROR {iso}: {exc!r}", flush=True)

    for iso in args.iso:
        print(f"[C] coal sigmoid identifiability: {iso} ...", flush=True)
        try:
            r = coal_sigmoid_identifiability(iso)
            if r:
                out["coal_sigmoid"].append(r)
        except Exception as exc:  # noqa: BLE001
            out["coal_sigmoid"].append({"iso": iso, "error": repr(exc)[:200]})
            print(f"    ERROR {iso}: {exc!r}", flush=True)

    (OUT_DIR / "summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT_DIR / 'summary.json'}")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
