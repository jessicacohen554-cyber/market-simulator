"""caiso-127 §TASK-1: how the model forms (and compresses) the evening premium.

Attribution-only instrument (NO solve, no mechanism, nothing armed). The
promoted keeper ``2026-07-27-caiso-126-ror-split`` carries a disclosed evening
hydro starvation whose root cause FINDING-caiso126 §3 attributes to the
compressed evening-overnight price premium (FINDING-caiso125 §4b). This probe
decomposes that premium's FORMATION on the keeper's own committed sidecars plus
a no-LP fleet reconstruction, and answers the three chartered questions:

  A. ladder + spread, re-based on the PROMOTED keeper (arm B) with its
     same-HEAD control (arm A) — the caiso-125 numbers were measured on the
     caiso-124 control; this section only re-anchors them, it does not
     re-derive the §4b attribution.
  B. the STORAGE ROUND-TRIP BREAKEVEN as a spread BOUND. If the fleet
     battery is strictly interior (neither at its discharge cap nor at its
     charge cap) in BOTH the overnight and the evening window of the same
     day, LP optimality equalizes the marginal value of stored energy across
     the two windows and the evening-overnight premium is PINNED at the
     round-trip wedge — no supply-side rung can widen it. The test is
     whether the model's spread can exceed that bound while the battery is
     interior in both windows.
  C. the MARGINAL RUNG, per evening hour, on the LP's OWN offer prices
     (``run_year(fleet_only=True)`` -> ``mc_base``, the assembled P0
     objective the LP solved on) x the exact availability caps: which class
     brackets lambda, what sits immediately above it, and how much capacity
     is stacked in the band the premium would have to climb.
  D. reality's implied stack in the same hours: the actual RT print against
     the model's own cheapest-available CT offer, and CEMS gas by class
     (model vs measured) — who reality calls in the evening that the model
     does not.
  E. the STEEPENING REQUIREMENT: the MW/hour that must be re-priced or
     displaced in the (lambda, lambda+delta] band for the premium to reach
     the implied-real level, per class — i.e. which rung must steepen.

Bounds caveat (stated, not worked around): the slim keeper bundle carries no
``floors/`` npz, so the lower bound used here is the fleet reconstruction's
own ``min_gen`` (the P0 floor). The P0->P1 seam bridge floors (CAISO RA
must-offer) are NOT in it, so "headroom above a floor" is an UPPER bound on
the truly free capacity and "interior" is an over-count. Every upper cap
(``pmax x availability``) is exact, and §C/§E rest on the caps and the offer
prices, not on the floor.

Usage:
    PYTHONPATH=.:src:scripts:scripts/probes .venv/bin/python \
        scripts/probes/_caiso127_evening_formation.py \
        --arm results/calibration/caiso126_rorsplit_B \
        --control results/calibration/caiso126_control_A
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from _caiso125_overnight_attribution import (  # noqa: E402
    GAS_CLASSES,
    WINDOWS,
    ca_lambda,
    class_pivot,
    storage_net,
    system_frame,
)

YEARS = (2023, 2024, 2025)
OVERNIGHT = list(WINDOWS["overnight"])  # hod 0-6
EVENING = list(WINDOWS["evening"])  # hod 17-21
LMP_PARQUET = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_CAISO.parquet"
)
CAMPD = REPO / "data" / "raw" / "campd-facility-level"
# LA-Basin facilityId -> ORISPL pins (the _caiso102_evening_merit crosswalk).
LA_BASIN = {"315": 62115, "335": 62116, "330": 57901}
CEMS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# A unit counts as price-setting when its offer sits within this band of lambda.
BRACKET_TOL = 0.50  # $/MWh
# Bound tolerance for "at its cap" (caiso-125 CEIL_BIND_FRAC convention).
BIND_FRAC = 0.995


def actual_rt(year: int) -> np.ndarray:
    """Return the committed actual CAISO RT hourly price on the model clock."""
    frame = pd.read_parquet(LMP_PARQUET)
    rows = frame[frame["year"] == year].sort_values("hour")
    out = np.full(8760, np.nan)
    hrs = rows["hour"].to_numpy(dtype=int)
    sel = hrs < 8760
    out[hrs[sel]] = rows["rt"].to_numpy(dtype=float)[sel]
    return out


def window_mask(hours: int, hods: list[int]) -> np.ndarray:
    """Return the boolean hour mask of an hour-of-day window."""
    return np.isin(np.arange(hours) % 24, hods)


def fleet_reconstruction(bundle: Path, year: int) -> dict:
    """Return the no-LP fleet state for ``year`` under the bundle's own flags."""
    from _caiso105_evening_q1_pin import fleet_state

    return fleet_state(bundle, year)


def unit_klasses(state: dict) -> np.ndarray:
    """Return the per-unit model class, exactly as the bundle writer assigns it.

    ``run_calibration_full._dispatch_frame``: non-ERCOT fleets class by the real
    plant group where present, else the fuel/efficiency-bin classifier.
    """
    from run_calibration_full import _model_class_for_unit

    fa = state["fleet_arrays"]
    ids = list(fa.unit_ids)
    groups = list(fa.plant_group)
    gens = list(state["fleet"])
    fuels = [g.fuel_type for g in gens]
    bins = [getattr(g, "efficiency_bin", "") for g in gens]
    out = []
    for i, uid in enumerate(ids):
        grp = groups[i] if i < len(groups) else ""
        out.append(grp if grp else _model_class_for_unit(uid, fuels[i], bins[i]))
    return np.asarray(out, dtype=object)


# --------------------------------------------------------------------------
# A. ladder + spread on the promoted keeper
# --------------------------------------------------------------------------
def section_a(arm: Path, control: Path) -> dict[int, dict]:
    """A. The lambda ladder and the evening-overnight spread, arm B vs arm A."""
    print("\n=== A. ladder + evening-overnight spread (arm B = promoted keeper) ===")
    print("  model = CA demand-weighted P1 lambda; actual = committed RT print")
    out: dict[int, dict] = {}
    for year in YEARS:
        lam_b = ca_lambda(system_frame(arm, year))
        lam_a = ca_lambda(system_frame(control, year))
        rt = actual_rt(year)[: len(lam_b)]
        ok = np.isfinite(rt)
        m_on = window_mask(len(lam_b), OVERNIGHT) & ok
        m_ev = window_mask(len(lam_b), EVENING) & ok

        rec = {
            "lam_on_b": float(lam_b[m_on].mean()),
            "lam_ev_b": float(lam_b[m_ev].mean()),
            "lam_on_a": float(lam_a[m_on].mean()),
            "lam_ev_a": float(lam_a[m_ev].mean()),
            "rt_on": float(rt[m_on].mean()),
            "rt_ev": float(rt[m_ev].mean()),
        }
        rec["spread_b"] = rec["lam_ev_b"] - rec["lam_on_b"]
        rec["spread_a"] = rec["lam_ev_a"] - rec["lam_on_a"]
        rec["spread_rt"] = rec["rt_ev"] - rec["rt_on"]
        rec["resid_on"] = rec["lam_on_b"] - rec["rt_on"]
        rec["resid_ev"] = rec["lam_ev_b"] - rec["rt_ev"]
        # The premium the evening must gain to reach the measured spread, if
        # the overnight level is held where the model has it.
        rec["delta"] = rec["spread_rt"] - rec["spread_b"]
        out[year] = rec

        print(
            f"  {year}: overnight model {rec['lam_on_b']:6.2f} (A {rec['lam_on_a']:6.2f}) "
            f"actual {rec['rt_on']:6.2f} resid {rec['resid_on']:+6.2f} | "
            f"evening model {rec['lam_ev_b']:6.2f} (A {rec['lam_ev_a']:6.2f}) "
            f"actual {rec['rt_ev']:6.2f} resid {rec['resid_ev']:+6.2f}"
        )
        print(
            f"        spread model {rec['spread_b']:+6.2f} (A {rec['spread_a']:+6.2f}) "
            f"vs actual {rec['spread_rt']:+6.2f}  ->  compression "
            f"{rec['delta']:+6.2f} $/MWh "
            f"({100 * rec['spread_b'] / rec['spread_rt']:.0f} % of measured)"
        )
    return out


# --------------------------------------------------------------------------
# B. the storage round-trip breakeven as a spread bound
# --------------------------------------------------------------------------
def storage_caps(state: dict, year: int, hours: int) -> dict[str, np.ndarray]:
    """Return fleet-aggregate battery/PS charge and discharge caps (MW, hourly).

    The keeper runs ``caiso_storage_shape_anchor``, so the battery rows carry
    the measured diurnal envelope (``model.storage.caiso_storage_shape_caps``);
    pumped storage passes its power cap through.
    """
    from market_sim.model.storage import _battery_mask, caiso_storage_shape_caps

    units = state["storage_units"]
    pcap = np.asarray(state["storage_power_cap"], dtype=float)
    if pcap.ndim == 1:
        pcap = np.repeat(pcap[:, None], hours, axis=1)
    pcap = pcap[:, :hours]
    chg, dis = caiso_storage_shape_caps(pcap, units, year, hours)
    batt = _battery_mask(units)
    return {
        "chg_total": chg.sum(axis=0),
        "dis_total": dis.sum(axis=0),
        "chg_batt": chg[batt].sum(axis=0),
        "dis_batt": dis[batt].sum(axis=0),
        "power_total": pcap.sum(axis=0),
    }


def measured_storage_net(year: int, hours: int) -> np.ndarray:
    """Return measured CISO battery net injection (EIA-930 ``NG: OTH``, MW).

    The CISO ``OTH`` cell is the battery fleet's net (+ discharge / - charge);
    it also carries the small non-battery "other" residual, so the LEVEL is a
    slight positive bias — the SHAPE (which window charges) is what §B reads.
    """
    from _caiso102_evening_merit import eia930_hourly

    return eia930_hourly(year)["battery"][:hours]


def states_for(year: int, states: dict[int, dict]) -> dict:
    """Return the reconstructed fleet state for ``year``."""
    return states[year]


def states_energy(state: dict) -> dict[str, np.ndarray]:
    """Return the storage energy cap / vom arrays from a fleet reconstruction."""
    arrays = state["storage"]
    return {
        "energy_cap": np.asarray(arrays.energy_cap, dtype=float),
        "vom": np.asarray(arrays.vom, dtype=float),
    }


def section_b(arm: Path, states: dict[int, dict], ladder: dict[int, dict]) -> None:
    """B. Is the evening-overnight spread bounded by the storage arbitrage?"""
    print("\n=== B. the storage round-trip breakeven as a SPREAD BOUND ===")
    print(
        "  LP storage: SOC[t]=SOC[t-1]+eta_c*Chg-Dis/eta_d, RTE 0.85 "
        "(ScenarioConfig.storage_rte_4hr), battery_dispatch_adder 0.0, "
        "epsilon 0.001 $/MWh (CLAUDE.md #9).\n"
        "  If the fleet is strictly INTERIOR in both windows of a day, the "
        "marginal value of stored energy equalizes and the premium is PINNED:\n"
        "    both windows DISCHARGING interior  -> lambda_ev - lambda_on ~ 0\n"
        "    overnight CHARGING, evening DISCHARGING interior "
        "-> lambda_ev = lambda_on / eta_rt (the round-trip wedge)."
    )
    rte = 0.85
    for year in YEARS:
        sysf = system_frame(arm, year)
        piv = class_pivot(arm, year)
        net = storage_net(sysf, piv)  # + = net injection (discharge)
        hours = len(net)
        caps = storage_caps(states[year], year, hours)
        lam = ca_lambda(sysf)

        m_on = window_mask(hours, OVERNIGHT)
        m_ev = window_mask(hours, EVENING)
        dis_cap, chg_cap = caps["dis_total"], caps["chg_total"]

        def _state(mask: np.ndarray) -> dict:
            n = net[mask]
            dcap, ccap = dis_cap[mask], chg_cap[mask]
            return {
                "mean": float(n.mean()),
                "dis_bound": float((n >= BIND_FRAC * dcap).mean()),
                "chg_bound": float((n <= -BIND_FRAC * ccap).mean()),
                "discharging": float((n > 1.0).mean()),
                "charging": float((n < -1.0).mean()),
                "cap": float(dcap.mean()),
                "util": float((n / np.maximum(dcap, 1.0)).mean()),
            }

        s_on, s_ev = _state(m_on), _state(m_ev)
        print(f"\n  {year}: fleet power {caps['power_total'].mean():.0f} MW")
        for lbl, s in (("overnight", s_on), ("evening", s_ev)):
            print(
                f"    {lbl:>9}: net {s['mean']:+7.0f} MW "
                f"(discharging {s['discharging']:.2f} of hours, charging "
                f"{s['charging']:.2f}); at discharge cap {s['dis_bound']:.3f}, "
                f"at charge cap {s['chg_bound']:.3f}; dis cap {s['cap']:.0f} MW, "
                f"utilisation {s['util']:+.2f}"
            )

        # --- the diurnal shape, model vs measured (EIA-930 CISO NG: OTH) -----
        prof_m = net[: (hours // 24) * 24].reshape(-1, 24).mean(axis=0)
        meas = measured_storage_net(year, hours)
        prof_a = np.nanmean(meas[: (hours // 24) * 24].reshape(-1, 24), axis=0)
        print("    hod net (+ = discharge, MW): model / measured 930 OTH")
        for lo in (0, 12):
            print("      " + " ".join(f"{h:>6d}" for h in range(lo, lo + 12)))
            print("      " + " ".join(f"{prof_m[h]:>6.0f}" for h in range(lo, lo + 12)))
            print("      " + " ".join(f"{prof_a[h]:>6.0f}" for h in range(lo, lo + 12)))

        for lbl, hods in (("overnight", OVERNIGHT), ("evening", EVENING)):
            mm = float(prof_m[hods].mean())
            ma = float(prof_a[hods].mean())
            print(
                f"      {lbl:>9} net: model {mm:+7.0f} vs measured {ma:+7.0f} MW "
                f"({mm - ma:+.0f})"
            )
        thr_m, thr_a = float(prof_m.clip(min=0).sum()), float(prof_a.clip(min=0).sum())
        print(
            f"      daily discharge from the mean profile: model {thr_m:.0f} vs "
            f"measured {thr_a:.0f} MWh ({thr_m / max(thr_a, 1.0):.2f}x)"
        )

        # --- energy-boundedness: is the fleet cycling out its SOC? ----------
        arrays = states_energy(states_for(year, states))
        e_cap = float(arrays["energy_cap"].sum())
        daily_dis = (
            np.maximum(net, 0.0)[: (hours // 24) * 24].reshape(-1, 24).sum(axis=1)
        )
        print(
            f"    fleet energy cap {e_cap:.0f} MWh; mean daily discharge "
            f"{daily_dis.mean():.0f} MWh = {daily_dis.mean() / e_cap:.2f} cycles/day "
            f"(p95 {np.percentile(daily_dis, 95) / e_cap:.2f})"
        )

        # --- Day-paired interiority ----------------------------------------
        days = hours // 24
        n_d = net[: days * 24].reshape(days, 24)
        dcap_d = dis_cap[: days * 24].reshape(days, 24)
        ccap_d = chg_cap[: days * 24].reshape(days, 24)
        lam_d = lam[: days * 24].reshape(days, 24)
        free = (n_d < BIND_FRAC * dcap_d) & (n_d > -BIND_FRAC * ccap_d)
        active = np.abs(n_d) > 1.0
        int_on = (free[:, OVERNIGHT] & active[:, OVERNIGHT]).all(axis=1)
        int_ev = (free[:, EVENING] & active[:, EVENING]).all(axis=1)
        both = int_on & int_ev
        spread_d = lam_d[:, EVENING].mean(axis=1) - lam_d[:, OVERNIGHT].mean(axis=1)
        # sign convention: overnight net < 0 => the fleet CHARGES overnight
        on_charging = n_d[:, OVERNIGHT].mean(axis=1) < 0.0
        ev_dis_bound = (n_d[:, EVENING] >= BIND_FRAC * dcap_d[:, EVENING]).any(axis=1)

        print(
            f"    day pairing ({days} days): interior+active overnight "
            f"{int_on.mean():.3f}, evening {int_ev.mean():.3f}, BOTH "
            f"{both.mean():.3f}; overnight is a CHARGING window on "
            f"{on_charging.mean():.3f} of days"
        )
        for lbl, sel in (
            ("BOTH interior-discharging", both & ~on_charging),
            ("evening at DISCHARGE cap", ev_dis_bound),
            ("evening interior", ~ev_dis_bound),
            ("all days", np.ones(days, dtype=bool)),
        ):
            if sel.any():
                print(
                    f"      {lbl:>26}: n={int(sel.sum()):4d}  mean day spread "
                    f"{float(spread_d[sel].mean()):+6.2f} $/MWh"
                )

        # --- the KKT pinning test -------------------------------------------
        # A battery strictly interior in DISCHARGE prices at lambda = vom + mu
        # (mu = the SOC shadow value). Within one SOC episode mu is constant, so
        # every interior-discharge hour of the episode carries the SAME lambda.
        # Measure the within-day lambda RANGE over interior-discharge hours: a
        # small range means storage is pinning the day's price surface.
        idis = free & active & (n_d > 1.0)
        rng, n_ok = [], 0
        for d in range(days):
            sel = idis[d]
            if sel.sum() >= 2:
                rng.append(float(lam_d[d][sel].max() - lam_d[d][sel].min()))
                n_ok += 1
        if rng:
            print(
                f"    KKT pinning: over {n_ok} days with >=2 interior-discharge "
                f"hours, within-day lambda RANGE across those hours: median "
                f"{np.median(rng):.2f}, p75 {np.percentile(rng, 75):.2f}, "
                f"p95 {np.percentile(rng, 95):.2f} $/MWh"
            )
        cross = idis[:, OVERNIGHT].any(axis=1) & idis[:, EVENING].any(axis=1)
        if cross.any():
            gap = [
                float(
                    lam_d[d][EVENING][idis[d][EVENING]].mean()
                    - lam_d[d][OVERNIGHT][idis[d][OVERNIGHT]].mean()
                )
                for d in np.flatnonzero(cross)
            ]
            print(
                f"      on the {int(cross.sum())} days with interior discharge in "
                f"BOTH windows the evening-overnight gap is mean "
                f"{np.mean(gap):+.2f} (median {np.median(gap):+.2f}) $/MWh — "
                f"the LP's own no-arbitrage prediction is 0.00"
            )
            # Is the pin the DEFECT, or only a correlate? Score the ladder
            # residual (model - actual RT) on the pinned days against the rest.
            rt = actual_rt(year)[: days * 24].reshape(days, 24)
            for lbl, sel in (("pinned", cross), ("not pinned", ~cross)):
                if not sel.any():
                    continue
                r_on = float(
                    np.nanmean(lam_d[sel][:, OVERNIGHT] - rt[sel][:, OVERNIGHT])
                )
                r_ev = float(np.nanmean(lam_d[sel][:, EVENING] - rt[sel][:, EVENING]))
                s_m = float(
                    np.nanmean(
                        lam_d[sel][:, EVENING].mean(axis=1)
                        - lam_d[sel][:, OVERNIGHT].mean(axis=1)
                    )
                )
                s_a = float(
                    np.nanmean(
                        rt[sel][:, EVENING].mean(axis=1)
                        - rt[sel][:, OVERNIGHT].mean(axis=1)
                    )
                )
                print(
                    f"        {lbl:>11} days (n={int(sel.sum()):3d}): resid overnight "
                    f"{r_on:+6.2f}, evening {r_ev:+6.2f}; spread model {s_m:+6.2f} "
                    f"vs actual {s_a:+6.2f}"
                )

        # The breakeven wedge the LP would have to respect if the overnight
        # were a charging window at the model's own overnight level.
        lam_on = ladder[year]["lam_on_b"]
        vom = float(np.max(arrays["vom"]))
        print(
            f"    charge->discharge breakeven at the model's own overnight "
            f"level: {lam_on:.2f}/{rte:.2f} + vom {vom:.0f} - {lam_on:.2f} = "
            f"{lam_on / rte + vom - lam_on:+.2f} $/MWh required premium "
            f"(model spread {ladder[year]['spread_b']:+.2f}, measured "
            f"{ladder[year]['spread_rt']:+.2f})"
        )


# --------------------------------------------------------------------------
# C / E. the marginal rung and the steepening requirement
# --------------------------------------------------------------------------
def section_ce(arm: Path, states: dict[int, dict], ladder: dict[int, dict]) -> None:
    """C+E. Which class brackets lambda, and what must steepen to double it."""
    print("\n=== C. marginal rung on the LP's own offer prices (mc_base x caps) ===")
    print("\n=== E. the steepening requirement (band capacity above lambda) ===")
    for year in YEARS:
        state = states[year]
        fa = state["fleet_arrays"]
        mc = np.asarray(state["mc_base"], dtype=float)
        cap = fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)
        mg = np.asarray(fa.min_gen, dtype=float)
        if mg.ndim == 1:
            mg = np.repeat(mg[:, None], cap.shape[1], axis=1)
        kl = unit_klasses(state)

        sysf = system_frame(arm, year)
        lam = ca_lambda(sysf)
        piv = class_pivot(arm, year)
        hours = min(len(lam), cap.shape[1])
        mc, cap, mg = mc[:, :hours], cap[:, :hours], mg[:, :hours]
        lam = lam[:hours]

        delta = ladder[year]["delta"]
        for wname, hods in (("evening", EVENING), ("overnight", OVERNIGHT)):
            mask = window_mask(hours, hods)
            idx = np.flatnonzero(mask)
            lm = lam[idx][None, :]
            capw, mcw, mgw = cap[:, idx], mc[:, idx], mg[:, idx]
            avail = capw > 0.0
            free = np.maximum(capw - mgw, 0.0) * avail

            bracket = avail & (np.abs(mcw - lm) <= BRACKET_TOL)
            above = avail & (mcw > lm + BRACKET_TOL)
            band = above & (mcw <= lm + max(delta, 0.0))

            print(
                f"\n  {year} {wname} (n={len(idx)} h, lambda mean {lam[idx].mean():.2f}):"
            )
            print(
                f"    hours with an offer bracketing lambda (+/-{BRACKET_TOL} $): "
                f"{float(bracket.any(axis=0).mean()):.3f}"
            )
            rows = []
            for k in sorted(set(kl)):
                sel = kl == k
                b_mw = (
                    float(free[sel][bracket[sel]].sum() / len(idx))
                    if bracket[sel].any()
                    else 0.0
                )
                a_mw = float(free[sel].sum() / len(idx))
                bd_mw = (
                    float(free[sel][band[sel]].sum() / len(idx))
                    if band[sel].any()
                    else 0.0
                )
                disp = (
                    float(piv[k].to_numpy()[idx].mean())
                    if k in piv.columns
                    else float("nan")
                )
                rows.append((k, disp, a_mw, b_mw, bd_mw))
            print(
                f"      {'class':>12} {'dispatch':>9} {'free MW':>9} "
                f"{'@lambda':>9} {'in band':>9}"
            )
            for k, disp, a_mw, b_mw, bd_mw in rows:
                if max(a_mw, abs(disp) if disp == disp else 0.0) < 1.0:
                    continue
                print(
                    f"      {k:>12} {disp:>9.0f} {a_mw:>9.0f} {b_mw:>9.0f} {bd_mw:>9.0f}"
                )
            if wname == "evening":
                tot_band = float(free[band].sum() / len(idx))
                nxt = np.where(above, mcw, np.inf)
                nxt_price = np.min(nxt, axis=0)
                fin = np.isfinite(nxt_price)
                print(
                    f"    E: to lift lambda by delta={delta:+.2f} $/MWh the "
                    f"(lambda, lambda+delta] band holds {tot_band:.0f} MW/h of "
                    f"free capacity that must be CALLED (or re-priced through)"
                )
                print(
                    f"       next rung above lambda: median +"
                    f"{float(np.median(nxt_price[fin] - lam[idx][fin])):.2f} $/MWh "
                    f"(p25 +{float(np.percentile(nxt_price[fin] - lam[idx][fin], 25)):.2f}, "
                    f"p75 +{float(np.percentile(nxt_price[fin] - lam[idx][fin], 75)):.2f})"
                )
                if "import" in piv.columns:
                    imp = float(piv["import"].to_numpy()[idx].mean())
                    print(
                        f"       model evening import {imp:.0f} MW/h — the band is "
                        f"{100 * tot_band / max(imp, 1.0):.0f} % of it"
                    )
        del mc, cap, mg


# --------------------------------------------------------------------------
# D. reality's implied stack
# --------------------------------------------------------------------------
def cems_by_klass(year: int, plant_klass: dict[int, str]) -> dict[str, np.ndarray]:
    """Return (8760,) measured CA gas MW by model class from CAMPD facility CEMS."""
    path = CAMPD / f"CA_{year}.parquet"
    if not path.exists():
        return {}
    d = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
    dt = pd.to_datetime(d["date"])
    keep = (dt.dt.month != 2) | (dt.dt.day != 29)
    d, dt = d[keep], dt[keep]
    doy = dt.dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where((dt.dt.month > 2).to_numpy(), doy - 1, doy)
    hidx = (doy - 1) * 24 + d["hour"].to_numpy(dtype=int)
    fid = d["facilityId"].astype(str)
    pc = pd.to_numeric(fid.map(LA_BASIN).fillna(pd.to_numeric(fid, errors="coerce")))
    klass = pc.map(plant_klass)
    out = {}
    for k in CEMS_KLASSES:
        sub = klass == k
        v = np.zeros(8760)
        np.add.at(
            v,
            hidx[sub.to_numpy()],
            d["grossLoad"].fillna(0.0).to_numpy(dtype=float)[sub.to_numpy()],
        )
        out[k] = v
    return out


def section_d(arm: Path, states: dict[int, dict]) -> None:
    """D. Reality's implied evening stack against the model's own offers."""
    print(
        "\n=== D. reality's implied evening stack (actual RT vs the model's rungs) ==="
    )
    for year in YEARS:
        state = states[year]
        fa = state["fleet_arrays"]
        mc = np.asarray(state["mc_base"], dtype=float)
        cap = fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)
        kl = unit_klasses(state)
        plant_klass = {int(p): k for p, k in zip(fa.plant_code, kl) if int(p) > 0}

        sysf = system_frame(arm, year)
        lam = ca_lambda(sysf)
        hours = min(len(lam), cap.shape[1])
        rt = actual_rt(year)[:hours]
        mask = window_mask(hours, EVENING) & np.isfinite(rt)
        idx = np.flatnonzero(mask)

        ct = np.flatnonzero(kl == "CT_PEAKER")
        ct_cap, ct_mc = cap[np.ix_(ct, idx)], mc[np.ix_(ct, idx)]
        cheapest_ct = np.min(np.where(ct_cap > 0.0, ct_mc, np.inf), axis=0)
        fin = np.isfinite(cheapest_ct)
        print(
            f"\n  {year} evening: cheapest AVAILABLE CT offer "
            f"{float(np.mean(cheapest_ct[fin])):.2f} $/MWh; "
            f"model lambda {float(lam[idx][fin].mean()):.2f} "
            f"({float(np.mean(lam[idx][fin] - cheapest_ct[fin])):+.2f} vs the rung); "
            f"actual RT {float(rt[idx][fin].mean()):.2f} "
            f"({float(np.mean(rt[idx][fin] - cheapest_ct[fin])):+.2f} vs the rung)"
        )
        print(
            f"    hours actual RT >= the CT rung: "
            f"{float((rt[idx][fin] >= cheapest_ct[fin]).mean()):.3f}; "
            f"model lambda >= the CT rung: "
            f"{float((lam[idx][fin] >= cheapest_ct[fin]).mean()):.3f}"
        )

        cems = cems_by_klass(year, plant_klass)
        piv = class_pivot(arm, year)
        if cems:
            print(f"    {'class':>12} {'model':>8} {'CEMS':>8} {'gap':>8}")
            for k in CEMS_KLASSES:
                if k not in piv.columns or k not in cems:
                    continue
                m = float(piv[k].to_numpy()[idx].mean())
                c = float(cems[k][:hours][idx].mean())
                print(f"    {k:>12} {m:>8.0f} {c:>8.0f} {m - c:>+8.0f}")
            m = float(
                piv[[c for c in GAS_CLASSES if c in piv.columns]]
                .sum(axis=1)
                .to_numpy()[idx]
                .mean()
            )
            c = float(sum(v[:hours][idx] for v in cems.values()).mean())
            print(f"    {'gas total':>12} {m:>8.0f} {c:>8.0f} {m - c:>+8.0f}")
        del mc, cap


def section_b2(bundle: Path, states: dict[int, dict]) -> None:
    """B2 (gate D0). Split §B's pin between battery and pumped storage.

    Consumes the per-tech ``hourly/storage_<year>.parquet`` sidecar (added
    caiso-127; produced by any solve from that point on). The KKT argument of
    §B is technology-blind, but which technology is interior decides which
    mechanism family is even admissible — the caiso-99 shape anchor binds
    batteries only, so pumped storage is the model's one unrestrained
    arbitrageur. Silently skips a bundle without the sidecar.
    """
    print("\n=== B2 (gate D0). the pin, split by storage technology ===")
    for year in YEARS:
        path = bundle / "hourly" / f"storage_{year}.parquet"
        if not path.exists():
            print(f"  {year}: no per-tech sidecar in {bundle} — skipped")
            continue
        frame = pd.read_parquet(path)
        frame = frame[frame["pass"] == "P1"]
        frame = frame.assign(net=frame["discharge_mw"] - frame["charge_mw"])
        piv = frame.pivot_table(
            index="hour", columns="tech", values="net", aggfunc="sum", observed=True
        ).sort_index()
        hours = len(piv)
        lam = ca_lambda(system_frame(bundle, year))[:hours]
        caps = storage_caps(states[year], year, hours)
        units = states[year]["storage_units"]
        from market_sim.model.storage import _battery_mask

        batt = _battery_mask(units)
        pcap = np.asarray(states[year]["storage_power_cap"], dtype=float)
        if pcap.ndim == 1:
            pcap = np.repeat(pcap[:, None], hours, axis=1)
        cap_by = {
            "li_ion": (caps["dis_batt"], caps["chg_batt"]),
            "pumped_storage": (
                pcap[~batt, :hours].sum(axis=0),
                pcap[~batt, :hours].sum(axis=0),
            ),
        }
        days = hours // 24
        print(f"\n  {year}:")
        for tech in piv.columns:
            net = piv[tech].to_numpy(dtype=float)
            dcap, ccap = cap_by.get(tech, (np.full(hours, np.inf),) * 2)
            for lbl, hods in (("overnight", OVERNIGHT), ("evening", EVENING)):
                m = window_mask(hours, hods)
                print(
                    f"    {tech:>14} {lbl:>9}: net {net[m].mean():+7.0f} MW "
                    f"(discharging {float((net[m] > 1.0).mean()):.2f} of hours, "
                    f"at cap {float((net[m] >= BIND_FRAC * dcap[m]).mean()):.3f})"
                )
            n_d = net[: days * 24].reshape(days, 24)
            d_d = dcap[: days * 24].reshape(days, 24)
            c_d = ccap[: days * 24].reshape(days, 24)
            lam_d = lam[: days * 24].reshape(days, 24)
            idis = (n_d > 1.0) & (n_d < BIND_FRAC * d_d) & (n_d > -BIND_FRAC * c_d)
            cross = idis[:, OVERNIGHT].any(axis=1) & idis[:, EVENING].any(axis=1)
            if cross.any():
                gap = [
                    float(
                        lam_d[d][EVENING][idis[d][EVENING]].mean()
                        - lam_d[d][OVERNIGHT][idis[d][OVERNIGHT]].mean()
                    )
                    for d in np.flatnonzero(cross)
                ]
                print(
                    f"    {tech:>14} pinned days {int(cross.sum()):3d}/{days} "
                    f"({cross.mean():.3f}); evening-overnight gap mean "
                    f"{np.mean(gap):+.2f} (median {np.median(gap):+.2f}) $/MWh"
                )
            else:
                print(f"    {tech:>14} pinned days 0/{days} — no pin from this tech")
            print(
                f"    {tech:>14} annual: charge "
                f"{float(frame[frame.tech == tech]['charge_mw'].sum()) / 1e6:.2f} TWh, "
                f"discharge "
                f"{float(frame[frame.tech == tech]['discharge_mw'].sum()) / 1e6:.2f} TWh"
            )


def main() -> None:
    """Run every section against the promoted keeper and its control."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", default="results/calibration/caiso126_rorsplit_B")
    ap.add_argument("--control", default="results/calibration/caiso126_control_A")
    ap.add_argument(
        "--pertech",
        default=None,
        help="bundle carrying hourly/storage_<year>.parquet for §B2 (gate D0)",
    )
    ap.add_argument("--sections", default="ABCDE")
    args = ap.parse_args()
    arm, control = Path(args.arm), Path(args.control)

    ladder = section_a(arm, control)
    want = set(args.sections.upper())
    if want & set("BCDE"):
        states = {y: fleet_reconstruction(arm, y) for y in YEARS}
        if "B" in want:
            section_b(arm, states, ladder)
            section_b2(Path(args.pertech) if args.pertech else arm, states)
        if want & {"C", "E"}:
            section_ce(arm, states, ladder)
        if "D" in want:
            section_d(arm, states)


if __name__ == "__main__":
    main()
