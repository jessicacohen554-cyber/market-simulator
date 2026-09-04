#!/usr/bin/env python3
"""nyiso-187 — the CT / steam-vs-CC merit-position decomposition, NO LP.

PREREG-nyiso187-ct-steam-merit-position §3, every bar read verbatim, on the
keeper's own 2024 sidecars (``unit_hourly`` carries the LP's INSTALLED offer
``mc`` and the generation columns' reduced cost — the nyiso-181 instrument):

* **M1** per class × zone: measured hourly class MW (the bench's per-plant
  CAMPD series) vs model hourly class MW; deficit energy ``D``, the CC excess
  ``X`` on the same grid, and their hourly coincidence.
* **M2** each deficit MW filled from the cheapest un-run capacity of the class
  in the zone, bucketed A / B / C against the model zonal price and the actual
  RT price (ISO-level ``rt``; the NYC / Capital zonal premium from the sample
  months as a sensitivity).
* **M3** bucket C's reduced-cost charge ``red_cost − (mc − price_z)``.
* **M4** bucket B's offer decomposed into fuel × HR + VOM + carbon + markup on
  the reconstruction (S0: the reconstruction must reproduce the installed
  ``mc``), each term against its own source.
* **M5** the CC mirror: depth in the money and headroom in the deficit hours.

Rule 13: everything here diagnoses; nothing feeds the LP.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
for _p in (str(_REPO), str(_REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.data.fleet.legacy_bins import assemble_mc  # noqa: E402
from market_sim.data.fuel import resolve_fuel_prices  # noqa: E402
from market_sim.data.offer_curves import apply_gas_offer_margin  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from scripts.legitimacy_diagnostics import load_bench  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

KEEPER = _REPO / "results" / "calibration" / "nyiso186_astoria_identity"
LMP = _REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"
RTD_DIR = _REPO / "data" / "raw" / "lmp-data" / "NYISO"
ISO = "NYISO"
HOURS = 8760
DEFICIT_CLASSES = ("CT_PEAKER", "CT_CHP", "ST_GAS")
CC_CLASSES = ("CC_REGULAR", "CC_CHP")
ZONES = ("NYC", "Capital_Hudson", "Long_Island")
ZONE_TO_RTD = {"NYC": "N.Y.C.", "Capital_Hudson": "CAPITL", "Long_Island": "LONGIL"}
# PREREG §3 bars, verbatim.
OWNER_SHARE = 0.50
ONLINE_FRAC = 0.05


def _bench_class_zone(year: int) -> dict[tuple[str, str], np.ndarray]:
    out: dict[tuple[str, str], np.ndarray] = {}
    for _pid, rec in load_bench(_REPO, ISO, year).items():
        key = (str(rec["group"]), str(rec.get("zone") or ""))
        mw = np.asarray(rec["mw"], dtype=float)[:HOURS]
        if mw.size < HOURS:
            mw = np.pad(mw, (0, HOURS - mw.size))
        out[key] = out.get(key, np.zeros(HOURS)) + np.nan_to_num(mw)
    return out


def _zonal_premium(year: int) -> dict[str, tuple[float, int]]:
    """Mean (zonal RT − ISO-mean RT) over the archive's sample months, per zone."""
    prem: dict[str, list[float]] = {z: [] for z in ZONE_TO_RTD}
    n = 0
    for path in sorted(glob.glob(str(RTD_DIR / f"{year}*realtime_zone_csv.zip"))):
        zf = zipfile.ZipFile(path)
        df = pd.concat([pd.read_csv(io.BytesIO(zf.read(nm))) for nm in zf.namelist()])
        df.columns = [c.strip() for c in df.columns]
        pc = next(c for c in df.columns if "LBMP" in c.upper())
        nc = next(c for c in df.columns if "Name" in c)
        df["t"] = pd.to_datetime(df[df.columns[0]])
        wide = df.groupby(["t", nc])[pc].mean().unstack()
        m = wide.mean(axis=1)
        n += 1
        for z, rtd in ZONE_TO_RTD.items():
            if rtd in wide.columns:
                prem[z].append(float((wide[rtd] - m).mean()))
    return {z: (round(float(np.mean(v)), 2), n) for z, v in prem.items() if v}


def run(year: int, bundle: Path, bare_srmc: bool = False) -> dict:
    u = pd.read_parquet(bundle / "hourly" / f"unit_hourly_{year}.parquet")
    if "pass" in u.columns:
        u = u[u["pass"].astype(str) == "P1"]
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    if "pass" in s.columns:
        s = s[s["pass"].astype(str) == "P1"]
    price = {
        z: g.sort_values("hour")["price"].to_numpy(float)[:HOURS]
        for z, g in s.groupby("zone")
    }
    lmp = pd.read_parquet(LMP)
    rt = lmp[lmp["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:HOURS]
    prem = _zonal_premium(year)
    meas = _bench_class_zone(year)

    # --- S0 / M4 instrument: the reconstruction's offer vs the installed mc
    state, _ = reconstruct_bundle_fleet(bundle, year, verbose=False)
    fa, gens, cfg = state["fleet_arrays"], state["fleet"], state["config"]
    cfg_y = (
        cfg.with_overrides(weather_year=year) if hasattr(cfg, "with_overrides") else cfg
    )
    fuel = resolve_fuel_prices(cfg_y, fa, year)
    carbon = resolve_carbon_price(cfg_y, year)
    mc_phys = assemble_mc(fa, fuel, carbon, 0.0, so2=(fa.so2_rate, 0.0))
    mc_full = mc_phys.copy()
    apply_gas_offer_margin(mc_full, gens, fuel, cfg_y)
    uid = [str(x) for x in fa.unit_ids]
    uidx = {x: i for i, x in enumerate(uid)}
    piv_mc = u.pivot_table(
        index="unit_id", columns="hour", values="mc", aggfunc="first"
    )
    common = [x for x in uid if x in piv_mc.index]
    d = np.abs(
        np.vstack([mc_full[uidx[x]] for x in common])
        - piv_mc.loc[common].to_numpy()[:, :HOURS]
    )
    s0 = {
        "units": len(common),
        "max_abs_delta": float(d.max()),
        "EXACT": bool(d.max() <= 1e-4),
    }

    # unit static attributes
    attrs = u.groupby("unit_id").agg(
        plant=("plant_code", "first"),
        group=("plant_group", "first"),
        zone=("zone", "first"),
    )
    piv_mw = u.pivot_table(
        index="unit_id", columns="hour", values="mw", aggfunc="first"
    )
    piv_cap = u.pivot_table(
        index="unit_id", columns="hour", values="cap_mw", aggfunc="first"
    )
    piv_rc = u.pivot_table(
        index="unit_id", columns="hour", values="red_cost", aggfunc="first"
    )

    out: dict = {
        "year": year,
        "S0_offer_identity": s0,
        "zonal_premium_sample": prem,
        "class_zone": {},
    }
    for zone in ZONES:
        pz = price[zone]
        premium = prem.get(zone, (0.0, 0))[0]
        # CC excess on the same grid
        cc_model = np.zeros(HOURS)
        cc_meas = np.zeros(HOURS)
        cc_units = attrs[(attrs.zone == zone) & attrs.group.isin(CC_CLASSES)].index
        if len(cc_units):
            cc_model = np.nan_to_num(piv_mw.loc[cc_units].to_numpy()[:, :HOURS]).sum(
                axis=0
            )
        for k in CC_CLASSES:
            cc_meas += meas.get((k, zone), np.zeros(HOURS))
        x_t = np.clip(cc_model - cc_meas, 0, None)
        cc_mc = (
            np.nan_to_num(piv_mc.loc[cc_units].to_numpy()[:, :HOURS], nan=1e9)
            if len(cc_units)
            else None
        )
        cc_cap = (
            np.nan_to_num(piv_cap.loc[cc_units].to_numpy()[:, :HOURS])
            if len(cc_units)
            else None
        )
        cc_mw = (
            np.nan_to_num(piv_mw.loc[cc_units].to_numpy()[:, :HOURS])
            if len(cc_units)
            else None
        )
        for klass in DEFICIT_CLASSES:
            m = meas.get((klass, zone))
            units = attrs[(attrs.zone == zone) & (attrs.group == klass)].index
            if m is None or not len(units):
                continue
            mw = np.nan_to_num(piv_mw.loc[units].to_numpy()[:, :HOURS])
            cap = np.nan_to_num(piv_cap.loc[units].to_numpy()[:, :HOURS])
            mc = np.nan_to_num(piv_mc.loc[units].to_numpy()[:, :HOURS], nan=1e9)
            rc = np.nan_to_num(piv_rc.loc[units].to_numpy()[:, :HOURS])
            if bare_srmc:
                # POST-HOC sensitivity (PREREG §3 M4 rider): bucket against the
                # reconstructed PHYSICAL offer fuel x HR + VOM + carbon, i.e.
                # every markup term removed — a BOUND on what any offer-level
                # lever could reach, never a lever.
                _gi = np.array([uidx[x] for x in units])
                _fuel = fuel[_gi][:, :HOURS] if fuel.ndim == 2 else np.repeat(fuel[_gi][:, None], HOURS, axis=1)
                mc = fa.heat_rate[_gi][:, None] * _fuel + fa.vom[_gi][:, None] + (fa.emission_rate[_gi] * carbon)[:, None]
            model_t = mw.sum(axis=0)
            def_t = np.clip(m - model_t, 0, None)
            D = float(def_t.sum())
            if D <= 0:
                continue
            # M2: fill each hour's deficit from the cheapest un-run capacity
            headroom = np.clip(cap - mw, 0, None)
            order = np.argsort(mc, axis=0)
            A = B = C = 0.0
            A2 = B2 = 0.0  # with the zonal premium on the actual price
            unmet = 0.0
            charge: list[float] = []
            for t in np.nonzero(def_t > 0)[0]:
                need = def_t[t]
                for g in order[:, t]:
                    if need <= 0:
                        break
                    h = headroom[g, t]
                    if h <= 0:
                        continue
                    take = min(h, need)
                    need -= take
                    c_ = mc[g, t]
                    if c_ <= pz[t]:
                        C += take
                        charge.append(float(rc[g, t] - (c_ - pz[t])))
                    elif c_ <= rt[t]:
                        A += take
                    else:
                        B += take
                    if c_ <= pz[t]:
                        pass
                    elif c_ <= rt[t] + premium:
                        A2 += take
                    else:
                        B2 += take
                unmet += max(need, 0.0)
            filled = A + B + C
            rec = {
                "measured_twh": round(float(m.sum()) / 1e6, 3),
                "model_twh": round(float(model_t.sum()) / 1e6, 3),
                "D_twh": round(D / 1e6, 3),
                "deficit_hours": int((def_t > 0).sum()),
                "unmet_no_headroom_twh": round(unmet / 1e6, 3),
                "bucket_share_of_filled": {
                    "A": round(A / filled, 3),
                    "B": round(B / filled, 3),
                    "C": round(C / filled, 3),
                }
                if filled > 0
                else None,
                "bucket_share_with_zonal_premium": {
                    "A": round(A2 / filled, 3),
                    "B": round(B2 / filled, 3),
                    "C": round(C / filled, 3),
                }
                if filled > 0
                else None,
                "bucket_C_charge_usd_per_mwh": {
                    "median": round(float(np.median(charge)), 2),
                    "p90": round(float(np.percentile(charge, 90)), 2),
                }
                if charge
                else None,
                "hourly_r_deficit_vs_cc_excess": round(
                    float(np.corrcoef(def_t, x_t)[0, 1]), 3
                )
                if x_t.std() > 0
                else None,
                "share_of_cc_excess_in_deficit_hours": round(
                    float(x_t[def_t > 0].sum() / max(x_t.sum(), 1.0)), 3
                ),
                "model_on_share": round(
                    float((model_t >= ONLINE_FRAC * cap.sum(axis=0).max()).mean()), 3
                ),
                "meas_on_share": round(
                    float((m >= ONLINE_FRAC * np.percentile(m, 99.5)).mean()), 3
                ),
            }
            # M4: bucket-B offer terms at the class's cheapest un-run capacity in deficit hours
            gi = np.array([uidx[x] for x in units])
            hr_ = fa.heat_rate[gi]
            vom_ = fa.vom[gi]
            fuel_ = (
                fuel[gi][:, :HOURS]
                if fuel.ndim == 2
                else np.repeat(fuel[gi][:, None], HOURS, axis=1)
            )
            em_ = fa.emission_rate[gi] * carbon
            markup = mc[:, :HOURS] - (
                hr_[:, None] * fuel_ + vom_[:, None] + em_[:, None]
            )
            dh = def_t > 0
            cheapest = np.argmin(np.where(headroom > 0, mc, 1e9), axis=0)
            sel = cheapest[dh]
            rec["M4_cheapest_unrun_in_deficit_hours"] = {
                "mc_median": round(float(np.median(mc[sel, dh])), 2),
                "model_price_median": round(float(np.median(pz[dh])), 2),
                "actual_rt_median": round(float(np.median(rt[dh])), 2),
                "fuel_median_usd_mmbtu": round(float(np.median(fuel_[sel, dh])), 3),
                "heat_rate_median": round(float(np.median(hr_[sel])), 3),
                "vom_median": round(float(np.median(vom_[sel])), 2),
                "carbon_term_median": round(float(np.median(em_[sel])), 2),
                "markup_median": round(float(np.median(markup[sel, dh])), 2),
                "fuel_x_hr_median": round(
                    float(np.median(hr_[sel] * fuel_[sel, dh])), 2
                ),
            }
            # M5: the CC mirror in these hours
            if cc_mc is not None:
                depth = pz[None, :] - cc_mc
                run_ = cc_mw > 0
                rec["M5_cc_mirror"] = {
                    "cc_excess_in_deficit_hours_twh": round(
                        float(x_t[dh].sum()) / 1e6, 3
                    ),
                    "cc_depth_itm_median_usd_running": round(
                        float(np.median(depth[:, dh][run_[:, dh]])), 2
                    )
                    if run_[:, dh].any()
                    else None,
                    "cc_headroom_mean_mw_deficit_hours": round(
                        float(
                            np.clip(cc_cap - cc_mw, 0, None)[:, dh].sum(axis=0).mean()
                        ),
                        1,
                    ),
                }
            out["class_zone"][f"{klass}@{zone}"] = rec
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", default=str(KEEPER))
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--bare-srmc", action="store_true", help="post-hoc: bucket against the physical SRMC (no markups)")
    ap.add_argument(
        "--out",
        default=str(
            _REPO / "results" / "calibration" / "_nyiso187_merit_position.json"
        ),
    )
    a = ap.parse_args()
    rec = run(a.year, Path(a.bundle), bare_srmc=a.bare_srmc)
    rec["basis"] = "bare_srmc_no_markups" if a.bare_srmc else "installed_mc"
    rec["prereg"] = "results/calibration/PREREG-nyiso187-ct-steam-merit-position.md"
    Path(a.out).write_text(json.dumps(rec, indent=1) + "\n")
    print("S0", rec["S0_offer_identity"], "premium", rec["zonal_premium_sample"])
    for k, v in rec["class_zone"].items():
        print(
            k,
            {
                kk: v[kk]
                for kk in (
                    "measured_twh",
                    "model_twh",
                    "D_twh",
                    "bucket_share_of_filled",
                    "bucket_share_with_zonal_premium",
                    "hourly_r_deficit_vs_cc_excess",
                    "share_of_cc_excess_in_deficit_hours",
                )
            },
        )
        print("   M4", v.get("M4_cheapest_unrun_in_deficit_hours"))
        print(
            "   M3", v.get("bucket_C_charge_usd_per_mwh"), "M5", v.get("M5_cc_mirror")
        )
    print("wrote", a.out)


if __name__ == "__main__":
    main()
