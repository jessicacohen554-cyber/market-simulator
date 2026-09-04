"""caiso-244 — the IMPORT_TRANCHES[CAISO] LEVEL object, Phase 0: row-level import dispatch from the keeper's own duals. ZERO LP.

Pre-registered in ``PRECOMMIT-caiso244-import-level-phase0-2026-09-04.md`` §2
(pushed before this file was written). NOTHING ARMED, NO SOLVE, NO FIELD.

The question: the keeper imports ~8 / 8.5 / 5 TWh more than the measured
CAISO corridor net interchange. WHICH import rows carry that excess, in WHICH
hours, and is it FORCED (the self-scheduled firm floor) or ECONOMIC (an offer
below the WECC zone's dual)? No committed artifact carries per-row import
dispatch (the ``class_hourly`` sidecar aggregates the ``import`` klass), and a
unit-level replay costs ~75 min of LP — so this probe reconstructs each row's
dispatch from LP complementarity instead:

* the keeper fleet is rebuilt ON-RECIPE (``replay_keeper.run_year_kwargs`` —
  the strict path this session promoted; the first CAISO probe to run on it by
  construction) so every import row's assembled offer ``c[r,t]`` (measured hub
  + wheel + CARB as injected), capability ``u[r,t] = pmax x availability`` and
  floor ``f[r,t] = min_gen`` are exactly what the LP saw;
* the keeper's committed P1 zonal duals ``lambda[z,t]`` (``hourly/system_*``)
  decide each row's state: ``c < lambda - tol`` -> at capability;
  ``c > lambda + tol`` -> at floor; within ``tol`` -> MARGINAL, taking the
  residual that closes the hour's committed ``import`` klass total;
* the export legs (``pmin < 0``) are the mirror: ``c > lambda + tol`` -> full
  export, ``c < lambda - tol`` -> 0.

THE EXPORT LEGS ARE CLOSED ON THE SCORED P1 PASS. The fleet-only state carries
the P0 bounds (export ``pmin`` = -corridor rating), but P1's RA-bridge floor
composition (``pipeline/commitment._bridge_floored_fleet``) lifts every
``pmin < 0`` absorption row's lower bound to >= 0 unless
``caiso_p1_export_sink_seam`` is armed — and that flag is OFF on the keeper
(matrix cell ``R``, caiso-142). This probe therefore (i) reports the
complementarity-implied export the legs WOULD carry at the P1 duals if they
were open (a diagnostic of the CAISO-vs-hub price relation, never a dispatch),
(ii) takes the P1 export as ZERO, and (iii) verifies that reading against the
committed ISO energy balance: sum(class_hourly) + discharge - charge + slack -
dump - demand, whose annual residual (losses + any export) bounds the export
from above (measured here: 0.58 / 2.21 / 2.31 TWh, never above 509 MW in an
hour — against a would-export of 58-72 TWh).

G-RECON (the instrument's own falsifier, PRECOMMIT §2.4): the reconstruction
must reproduce the committed ``import`` klass to <= 1 % annual energy and
< 100 MW hourly RMSE on ONE of two bases (klass nets the export legs / klass is
gross imports). FAIL -> no attribution is claimed.

The measured side is the committed producer
``derive_caiso_import_tranches.corridor_net_import`` (EIA-930 CISO <-> DIBA on
the model clock, ``CAISO_CORRIDOR_DIBA``).

Writes ``results/calibration/_caiso244_import_level_anatomy.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso244_import_level_anatomy.py
"""

from __future__ import annotations

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
sys.path.insert(0, str(REPO / "scripts" / "data"))

BUNDLE = REPO / "results/calibration/caiso243_b1_f923_fallback_guard"
OUT = REPO / "results/calibration/_caiso244_import_level_anatomy.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
#: Complementarity tolerance on the persisted duals ($/MWh). The injector's own
#: tie-break is CAISO_INTERTIE_TIEBREAK_EPS = 1e-3; 0.05 absorbs float noise in
#: the persisted prices. Reported, not tuned (PRECOMMIT §2.3).
TOL = 0.05
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m + 1) for m, d in enumerate(_DAYS)])[
    :HOURS
]
HOD = np.arange(HOURS) % 24
#: corridor zone -> the CAISO zone its link lands on (iso_configs CAISO links).
CORRIDOR_LANDING = {"WECC_PNW": "NP15", "WECC_DSW": "SP15_rest"}
FIRM_ROWS = ("PNW_hydro_base", "DSW_solar_PV")
SPOT_ROWS = ("PNW_midC", "DSW_CCGT", "DSW_CT", "WECC_scarcity")
CLEAN_ROWS = ("DSW_surplus_clean", "DSW_overnight_clean", "DSW_daytime_clean")


def rebuild(year: int) -> dict:
    """Rebuild the keeper fleet on-recipe (no LP) and pull the import rows."""
    from market_sim.config.iso_configs import get_iso_config
    from run_calibration import run_year
    from replay_keeper import run_year_kwargs
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    clear_fleet_caches()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year,
            meta["iso"],
            HOURS,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kwargs,
        )
    fa = st["fleet_arrays"]
    gens = st.get("fleet") or []
    # The LP's zone list under the keeper's per-hub split: WECC_import replaced
    # by the two corridor zones (the same construction run_year applies; the
    # committed system sidecar's zone set confirms the order).
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub

    zone_names = list(split_caiso_import_node_per_hub(get_iso_config("CAISO")).zone_names)
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    avail = np.asarray(fa.availability, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    pmin = np.asarray(fa.pmin, dtype=float)
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(pmin[:, None], (pmin.size, HOURS))
    mg = np.asarray(mg, dtype=float)
    uid = np.array([str(u) for u in fa.unit_ids], dtype=object)
    group = np.array([str(getattr(g, "plant_group", "")) for g in gens], dtype=object)
    zidx = np.asarray(fa.zone_idx, dtype=int)
    rows = []
    for r, u in enumerate(uid):
        z = zone_names[zidx[r]]
        if z not in CORRIDOR_LANDING:
            continue
        name = u[len(z) + 1 :]
        rows.append(
            {
                "r": r,
                "uid": u,
                "name": name,
                "zone": z,
                "is_export": bool(pmin[r] < 0.0),
            }
        )
    # cheapest AVAILABLE domestic gas offer per hour (ISO-wide and per landing zone)
    gas = np.isin(group, GAS_GROUPS)
    cheapest_gas = {}
    for label, zsel in (
        ("ISO", np.ones(uid.size, dtype=bool)),
        ("NP15", np.array([zone_names[i] == "NP15" for i in zidx])),
        ("SP15_rest", np.array([zone_names[i] == "SP15_rest" for i in zidx])),
    ):
        sel = gas & zsel
        m = np.where(avail[sel] > 0.01, mc[sel], np.inf)
        cheapest_gas[label] = m.min(axis=0)
    return {
        "rows": rows,
        "mc": mc,
        "avail": avail,
        "pmax": pmax,
        "pmin": pmin,
        "min_gen": mg,
        "cheapest_gas": cheapest_gas,
        "log": buf.getvalue(),
    }


def sidecars(year: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Committed P1 zonal duals (zone x hour) and the ``import`` klass series."""
    s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    price = s.pivot(index="zone", columns="hour", values="price").reindex(
        columns=range(HOURS)
    )
    c_all = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c_all = c_all[c_all["pass"] == "P1"]
    c = c_all[c_all["klass"] == "import"].sort_values("hour")
    imp = np.zeros(HOURS)
    imp[c["hour"].to_numpy(int)] = c["mw"].to_numpy(float)
    # ISO energy balance from the committed sidecars: the residual is link
    # losses (caiso_zonal_loss_surface) plus any P1 export — an upper bound on
    # what the export legs carried on the scored pass.
    gen = c_all.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    dem = s.groupby("hour")["demand"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    dump = s.groupby("hour")["dump"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    slack = s.groupby("hour")["slack"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    st = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    st = st[st["pass"] == "P1"]
    chg = st.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    dis = st.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    balance_residual = gen + dis - chg + slack - dump - dem
    return price, imp, balance_residual


def reconstruct(fl: dict, price: pd.DataFrame, klass_import: np.ndarray) -> dict:
    """Row-level dispatch from complementarity; both klass bases; G-RECON."""
    rows = fl["rows"]
    n = len(rows)
    x_lo = np.zeros((n, HOURS))
    x_hi = np.zeros((n, HOURS))
    state = np.zeros((n, HOURS), dtype=np.int8)  # -1 floor/zero, 0 marginal, +1 capability/full
    lam = np.zeros((n, HOURS))
    for i, row in enumerate(rows):
        r = row["r"]
        lam_z = price.loc[row["zone"]].to_numpy(float)
        lam[i] = lam_z
        c = fl["mc"][r]
        if row["is_export"]:
            lo = np.minimum(fl["min_gen"][r], 0.0)
            lo = np.where(np.isfinite(lo), lo, fl["pmin"][r])
            hi = np.zeros(HOURS)
            # export when the hub (offer) sits ABOVE the zone dual
            st = np.where(c > lam_z + TOL, 1, np.where(c < lam_z - TOL, -1, 0))
            x_lo[i], x_hi[i] = lo, hi
            # +1 = full export (lo), -1 = zero
            state[i] = st
        else:
            hi = fl["pmax"][r] * fl["avail"][r]
            lo = np.clip(fl["min_gen"][r], 0.0, None)
            lo = np.minimum(lo, hi)
            st = np.where(c < lam_z - TOL, 1, np.where(c > lam_z + TOL, -1, 0))
            x_lo[i], x_hi[i] = lo, hi
            state[i] = st
    is_exp = np.array([r["is_export"] for r in rows])
    # determined value per row/hour
    x = np.where(state == 1, np.where(is_exp[:, None], x_lo, x_hi), x_lo)
    x = np.where(state == -1, np.where(is_exp[:, None], x_hi, x_lo), x)
    marg = state == 0
    out = {}
    best = None
    for basis in ("net", "gross"):
        xb = x.copy()
        incl = np.ones(n, dtype=bool) if basis == "net" else ~is_exp
        fixed = (np.where(marg, 0.0, xb) * incl[:, None]).sum(axis=0)
        resid = klass_import - fixed
        # allocate residual to marginal rows (imports and, on the net basis, exports)
        span_lo = (np.where(marg & incl[:, None], np.where(is_exp[:, None], x_lo, x_lo), 0.0)).sum(axis=0)
        span_hi = (np.where(marg & incl[:, None], np.where(is_exp[:, None], x_hi, x_hi), 0.0)).sum(axis=0)
        target = np.clip(resid, span_lo, span_hi)
        width = span_hi - span_lo
        frac = np.where(width > 1e-9, (target - span_lo) / np.where(width > 1e-9, width, 1.0), 0.0)
        alloc = x_lo + (x_hi - x_lo) * frac[None, :]
        xb = np.where(marg & incl[:, None], alloc, xb)
        recon = (xb * incl[:, None]).sum(axis=0)
        err = recon - klass_import
        n_marg_rows = (marg & incl[:, None]).sum(axis=0)
        determined = n_marg_rows == 0
        res = {
            "annual_twh_klass": float(klass_import.sum() / 1e6),
            "annual_twh_recon": float(recon.sum() / 1e6),
            "annual_energy_err_pct": float(100.0 * (recon.sum() - klass_import.sum()) / max(klass_import.sum(), 1.0)),
            "hourly_rmse_mw": float(np.sqrt(np.mean(err**2))),
            "hourly_rmse_mw_determined_hours": float(np.sqrt(np.mean(err[determined] ** 2))) if determined.any() else None,
            "hours_determined": int(determined.sum()),
            "hours_with_marginal_import_row": int((n_marg_rows > 0).sum()),
            "hours_with_gt1_marginal_rows": int((n_marg_rows > 1).sum()),
            "hours_residual_clipped": int((np.abs(target - resid) > 1.0).sum()),
            "max_abs_err_mw": float(np.abs(err).max()),
        }
        res["G_RECON_pass"] = bool(abs(res["annual_energy_err_pct"]) <= 1.0 and res["hourly_rmse_mw"] < 100.0)
        out[basis] = res
        if best is None or res["hourly_rmse_mw"] < out[best]["hourly_rmse_mw"]:
            best = basis
            best_x = xb
    out["basis_selected"] = best
    out["G_RECON_pass"] = out[best]["G_RECON_pass"]
    return out, best_x, state, lam, x_lo, x_hi


def measured_corridors(years) -> pd.DataFrame:
    from derive_caiso_import_tranches import corridor_net_import

    return corridor_net_import(tuple(years))


def _hod_means(v: np.ndarray) -> list[float]:
    return [round(float(v[HOD == h].mean()), 1) for h in range(24)]


def _month_twh(v: np.ndarray) -> list[float]:
    return [round(float(v[MONTH_OF_HOUR == m].sum() / 1e6), 4) for m in range(1, 13)]


def analyse(year: int, fl: dict, price: pd.DataFrame, klass_import: np.ndarray, meas: pd.DataFrame, balance: np.ndarray) -> dict:
    recon, x, state, lam, x_lo, x_hi = reconstruct(fl, price, klass_import)
    rows = fl["rows"]
    is_exp = np.array([r["is_export"] for r in rows])
    # P0-bound complementarity export ("would export if the legs were open"),
    # kept as a diagnostic; the P1 export is ZERO (docstring) and every net
    # figure below uses x_p1.
    x_would_export = x.copy()
    x = np.where(is_exp[:, None], 0.0, x)
    out = {
        "recon": recon,
        "p1_export_closure": {
            "basis": "pipeline/commitment._bridge_floored_fleet lifts pmin<0 rows to >=0 in P1 unless caiso_p1_export_sink_seam (OFF on the keeper; cell R, caiso-142)",
            "energy_balance_residual_twh": round(float(balance.sum() / 1e6), 4),
            "energy_balance_residual_mw_mean": round(float(balance.mean()), 1),
            "energy_balance_residual_mw_max": round(float(balance.max()), 1),
            "energy_balance_residual_mw_min": round(float(balance.min()), 1),
            "would_export_if_open_twh": round(float((-x_would_export * is_exp[:, None]).sum() / 1e6), 4),
        },
        "rows": {},
        "corridor": {},
        "classes": {},
    }
    # --- per row -------------------------------------------------------------
    for i, row in enumerate(rows):
        xi = x[i]
        if row["is_export"]:
            xw = x_would_export[i]
            rec = {
                "zone": row["zone"],
                "export": True,
                "p1_energy_twh": 0.0,
                "would_export_if_open_twh": round(float(-xw.sum() / 1e6), 4),
                "hours_hub_above_zone_dual": int((state[i] == 1).sum()),
                "hours_would_export": int((xw < -1e-6).sum()),
                "hours_marginal": int((state[i] == 0).sum()),
                "offer_mean": round(float(fl["mc"][row["r"]].mean()), 2),
            }
        else:
            u, f = x_hi[i], x_lo[i]
            strictly_between = (xi > f + 1e-6) & (xi < u - 1e-6)
            cap_hours = u > 1e-6
            clip_active = f < u - 1e-6
            rec = {
                "zone": row["zone"],
                "export": False,
                "hours_floor_below_capability": int(clip_active.sum()),
                "hours_price_live_above_floor": int((clip_active & (xi > f + 1e-6)).sum()),
                "energy_price_live_above_floor_twh": round(float(((xi - f) * clip_active).sum() / 1e6), 4),
                "pmax_mw": round(float(fl["pmax"][row["r"]]), 1),
                "capability_mean_mw": round(float(u.mean()), 1),
                "floor_mean_mw": round(float(f.mean()), 1),
                "energy_twh": round(float(xi.sum() / 1e6), 4),
                "floor_energy_twh": round(float(f.sum() / 1e6), 4),
                "energy_above_floor_twh": round(float((xi - f).sum() / 1e6), 4),
                "hours_at_capability_in_merit": int((state[i] == 1).sum()),
                "hours_at_floor_out_of_merit": int((state[i] == -1).sum()),
                "hours_marginal": int((state[i] == 0).sum()),
                "hours_strictly_between_floor_and_capability": int(strictly_between.sum()),
                "share_hours_strictly_between": round(float(strictly_between.mean()), 4),
                "capability_hours_dispatched_share": round(float(((xi > 1e-6) & cap_hours).sum() / max(cap_hours.sum(), 1)), 4),
                "offer_mean": round(float(fl["mc"][row["r"]].mean()), 2),
                "offer_is_constant": bool(np.ptp(fl["mc"][row["r"]]) < 1e-9),
                "spread_lambda_minus_offer_mean_when_in_merit": (
                    round(float((lam[i] - fl["mc"][row["r"]])[state[i] == 1].mean()), 2)
                    if (state[i] == 1).any()
                    else None
                ),
                "month_twh": _month_twh(xi),
                "hod_mean_mw": _hod_means(xi),
            }
        out["rows"][row["name"]] = rec
    # --- per corridor ------------------------------------------------------------
    for z, land in CORRIDOR_LANDING.items():
        sel = np.array([r["zone"] == z for r in rows])
        imp = (x * (sel & ~is_exp)[:, None]).sum(axis=0)
        exp = (-x * (sel & is_exp)[:, None]).sum(axis=0)
        net = imp - exp
        m = meas.loc[year, z].to_numpy(float) if z in meas.columns else np.full(HOURS, np.nan)
        ok = np.isfinite(m)
        firm = (x_lo * (sel & ~is_exp & np.isin([r["name"] for r in rows], FIRM_ROWS))[:, None]).sum(axis=0)
        lam_w = price.loc[z].to_numpy(float)
        lam_l = price.loc[land].to_numpy(float)
        out["corridor"][z] = {
            "landing_zone": land,
            "model_gross_import_twh": round(float(imp.sum() / 1e6), 4),
            "model_export_twh_p1": round(float(exp.sum() / 1e6), 4),
            "model_net_import_twh": round(float(net.sum() / 1e6), 4),
            "measured_net_import_twh": round(float(np.nansum(m) / 1e6), 4),
            "measured_gross_import_twh_positive_hours": round(float(np.nansum(np.clip(m, 0.0, None)) / 1e6), 4),
            "measured_gross_export_twh_negative_hours": round(float(np.nansum(np.clip(-m, 0.0, None)) / 1e6), 4),
            "model_gross_minus_measured_gross_import_twh": round(float((imp[ok].sum() - np.clip(m[ok], 0.0, None).sum()) / 1e6), 4),
            "firm_floor_minus_measured_gross_import_twh": round(float((firm[ok].sum() - np.clip(m[ok], 0.0, None).sum()) / 1e6), 4),
            "measured_hours_covered": int(ok.sum()),
            "excess_model_minus_measured_twh": round(float((net[ok].sum() - m[ok].sum()) / 1e6), 4),
            "firm_floor_energy_twh": round(float(firm.sum() / 1e6), 4),
            "firm_floor_minus_measured_net_twh": round(float((firm[ok].sum() - m[ok].sum()) / 1e6), 4),
            "model_net_month_twh": _month_twh(net),
            "measured_net_month_twh": _month_twh(np.where(ok, m, 0.0)),
            "model_net_hod_mean_mw": _hod_means(net),
            "measured_net_hod_mean_mw": _hod_means(np.where(ok, m, np.nan)),
            "firm_floor_hod_mean_mw": _hod_means(firm),
            "hours_link_unbound_lambda_equal": int((np.abs(lam_w - lam_l) <= TOL).sum()),
            "lambda_wecc_mean": round(float(lam_w.mean()), 2),
            "lambda_landing_mean": round(float(lam_l.mean()), 2),
        }
    tot_model = sum(c["model_net_import_twh"] for c in out["corridor"].values())
    tot_meas = sum(c["measured_net_import_twh"] for c in out["corridor"].values())
    out["corridor_shares"] = {
        "model_pnw_share_of_net": round(out["corridor"]["WECC_PNW"]["model_net_import_twh"] / tot_model, 4) if tot_model else None,
        "measured_pnw_share_of_net": round(out["corridor"]["WECC_PNW"]["measured_net_import_twh"] / tot_meas, 4) if tot_meas else None,
        "total_model_net_twh": round(tot_model, 4),
        "total_measured_net_twh": round(tot_meas, 4),
        "total_excess_twh": round(tot_model - tot_meas, 4),
    }
    # --- classes of rows -------------------------------------------------------------
    names = np.array([r["name"] for r in rows])
    total_import = float((x * (~is_exp)[:, None]).sum() / 1e6)
    for label, members in (("firm", FIRM_ROWS), ("spot", SPOT_ROWS), ("clean", CLEAN_ROWS)):
        sel = np.isin(names, members) & ~is_exp
        e = float((x * sel[:, None]).sum() / 1e6)
        f = float((x_lo * sel[:, None]).sum() / 1e6)
        out["classes"][label] = {
            "energy_twh": round(e, 4),
            "share_of_model_import": round(e / max(total_import, 1e-9), 4),
            "floor_energy_twh": round(f, 4),
            "economic_energy_twh": round(e - f, 4),
            "month_twh": _month_twh((x * sel[:, None]).sum(axis=0)),
        }
    out["classes"]["exports_twh"] = round(float((-x * is_exp[:, None]).sum() / 1e6), 4)
    out["classes"]["total_model_import_twh"] = round(total_import, 4)
    # --- import-marginal hours (P-6) ------------------------------------------------
    marg_any = np.zeros(HOURS, dtype=bool)
    marg_unbound = np.zeros(HOURS, dtype=bool)
    for i, row in enumerate(rows):
        if row["is_export"]:
            continue
        mi = state[i] == 0
        lam_l = price.loc[CORRIDOR_LANDING[row["zone"]]].to_numpy(float)
        marg_any |= mi
        marg_unbound |= mi & (np.abs(lam[i] - lam_l) <= TOL)
    out["import_marginal"] = {
        "hours_any_import_row_marginal_at_wecc_zone": int(marg_any.sum()),
        "hours_marginal_and_link_unbound": int(marg_unbound.sum()),
        "share_marginal_and_link_unbound": round(float(marg_unbound.mean()), 4),
    }
    # --- economic slice spread anatomy ---------------------------------------------
    econ_spreads = {}
    for i, row in enumerate(rows):
        if row["is_export"]:
            continue
        inm = state[i] == 1
        if not inm.any():
            continue
        land = CORRIDOR_LANDING[row["zone"]]
        c = fl["mc"][row["r"]]
        lam_l = price.loc[land].to_numpy(float)
        cg_iso = fl["cheapest_gas"]["ISO"]
        cg_land = fl["cheapest_gas"][land]
        finite = np.isfinite(cg_iso)
        econ_spreads[row["name"]] = {
            "hours_in_merit": int(inm.sum()),
            "offer_mean_in_merit": round(float(c[inm].mean()), 2),
            "lambda_landing_mean_in_merit": round(float(lam_l[inm].mean()), 2),
            "cheapest_avail_gas_ISO_mean_in_merit": round(float(cg_iso[inm & finite].mean()), 2) if (inm & finite).any() else None,
            "share_in_merit_hours_offer_below_cheapest_gas_ISO": round(float((c[inm & finite] < cg_iso[inm & finite]).mean()), 4) if (inm & finite).any() else None,
            "share_in_merit_hours_offer_below_cheapest_gas_landing": round(float((c[inm] < cg_land[inm]).mean()), 4),
        }
    out["economic_spreads"] = econ_spreads
    # --- December (P-7) --------------------------------------------------------------
    dec = MONTH_OF_HOUR == 12
    firm_sel = np.isin(names, FIRM_ROWS) & ~is_exp
    econ_sel = (~firm_sel) & (~is_exp)
    out["december"] = {
        "forced_firm_floor_twh": round(float((x_lo * firm_sel[:, None])[:, dec].sum() / 1e6), 4),
        "firm_above_floor_twh": round(float(((x - x_lo) * firm_sel[:, None])[:, dec].sum() / 1e6), 4),
        "economic_spot_plus_clean_twh": round(float((x * econ_sel[:, None])[:, dec].sum() / 1e6), 4),
        "exports_twh": round(float((-x * is_exp[:, None])[:, dec].sum() / 1e6), 4),
        "model_net_import_mean_mw": round(float(((x * (~is_exp)[:, None]).sum(axis=0) - (-x * is_exp[:, None]).sum(axis=0))[dec].mean()), 1),
        "measured_net_import_mean_mw": round(float(np.nanmean(meas.loc[year].to_numpy(float).sum(axis=1)[dec])), 1) if len(meas.columns) else None,
    }
    return out


def main() -> None:
    meas = measured_corridors(YEARS)
    out: dict = {
        "_provenance": {
            "session": "caiso-244",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": "2026-09-04-caiso-243-b1-f923",
            "precommit": "PRECOMMIT-caiso244-import-level-phase0-2026-09-04.md §2",
            "recipe": "replay_keeper.run_year_kwargs (strict, on-recipe)",
            "tol_usd_mwh": TOL,
            "measured_source": "derive_caiso_import_tranches.corridor_net_import (EIA-930 CISO<->DIBA, model clock)",
            "note": "ZERO LP; nothing armed; row-level dispatch reconstructed from the keeper's committed P1 duals",
        },
        "years": {},
    }
    for y in YEARS:
        fl = rebuild(y)
        price, klass_import, balance = sidecars(y)
        res = analyse(y, fl, price, klass_import, meas, balance)
        res["log_lines"] = [ln for ln in fl["log"].splitlines() if "import" in ln.lower() and "INFO" in ln][:12]
        out["years"][y] = res
        r = res["recon"]
        print(f"--- {y} ---  G-RECON basis={r['basis_selected']} pass={r['G_RECON_pass']}")
        for b in ("net", "gross"):
            rb = r[b]
            print(f"   {b:5s}: klass {rb['annual_twh_klass']:.3f} TWh recon {rb['annual_twh_recon']:.3f} ({rb['annual_energy_err_pct']:+.3f} %), RMSE {rb['hourly_rmse_mw']:.1f} MW (determined-hours RMSE {rb['hourly_rmse_mw_determined_hours']}), marginal-import hours {rb['hours_with_marginal_import_row']}, >1 marginal {rb['hours_with_gt1_marginal_rows']}, clipped {rb['hours_residual_clipped']}")
        for z, c in res["corridor"].items():
            print(f"   {z}: model net {c['model_net_import_twh']:.3f} (P1 export {c['model_export_twh_p1']:.3f}) vs measured net {c['measured_net_import_twh']:.3f} (gross {c['measured_gross_import_twh_positive_hours']:.3f}, export {c['measured_gross_export_twh_negative_hours']:.3f}) -> excess {c['excess_model_minus_measured_twh']:+.3f} TWh; firm floor {c['firm_floor_energy_twh']:.3f} (floor - meas net {c['firm_floor_minus_measured_net_twh']:+.3f}; floor - meas gross {c['firm_floor_minus_measured_gross_import_twh']:+.3f})")
        print(f"   shares {res['corridor_shares']}; P1 export closure {res['p1_export_closure']}")
        for k, v in res["classes"].items():
            if isinstance(v, dict):
                print(f"   {k:6s}: {v['energy_twh']:.3f} TWh ({v['share_of_model_import']:.1%}), floor {v['floor_energy_twh']:.3f}, economic {v['economic_energy_twh']:.3f}")
        print(f"   P1 exports {res['classes']['exports_twh']:.3f} TWh; import-marginal & unbound {res['import_marginal']}")
        print(f"   December: {res['december']}")
        for name, rr in res["rows"].items():
            if not rr["export"]:
                print(f"     {name:20s} E {rr['energy_twh']:.3f} floor {rr['floor_energy_twh']:.3f} between {rr['share_hours_strictly_between']:.3f} inmerit_h {rr['hours_at_capability_in_merit']} marg_h {rr['hours_marginal']} disp_share {rr['capability_hours_dispatched_share']:.3f} offer {rr['offer_mean']} clip_h {rr['hours_floor_below_capability']} pricelive_h {rr['hours_price_live_above_floor']} pricelive_TWh {rr['energy_price_live_above_floor_twh']:.3f}")
            else:
                print(f"     {name:20s} P1 export 0; would-export-if-open {rr['would_export_if_open_twh']:.3f} TWh in {rr['hours_would_export']} h (hub above zone dual {rr['hours_hub_above_zone_dual']} h)")
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
