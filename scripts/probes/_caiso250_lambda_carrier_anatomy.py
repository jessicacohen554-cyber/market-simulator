"""caiso-250 — WHAT SETS lambda when no thermal unit is marginal. ZERO LP.

Pre-registered in ``PRECOMMIT-caiso250-lambda-carrier-2026-09-05.md`` (pushed
to ``origin`` before this file was written and before any cell of the object
was computed). **NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG.**

The object (PRECOMMIT §0): caiso-249's ``STORAGE`` cell — a RESIDUAL label,
assigned when no own-zone or delivery-factor-reachable domestic unit
price-matched and storage happened to be cycling — carries **43.4 % (2024) /
55.0 % (2025)** of the C3a gap and is the largest 2025 cell. No DOM_GAS number
is quotable until it resolves.

The candidate carriers, read off the shipped LP builder and the keeper's own
``run_config.json`` BEFORE measurement (PRECOMMIT §0.1). A column strictly
between its bounds has zero reduced cost, so its stationarity is an EXACT
identity for ``lambda``:

* thermal own-zone ``lambda_z = mc_g`` — **already tested**, it is caiso-249's
  own-zone pass, so by construction it FAILED in every ``STORAGE`` zone-hour;
* storage charge ``lambda_z = -eps - eta_c*nu_s``; storage discharge
  ``lambda_z = eps + vom_s - nu_s/eta_d`` (``nu`` = the SOC-row dual);
* hydro ``lambda_z = mc_g + w_{g,m}`` — **invisible to every price-match
  instrument this lane has run**, because ``hydro_dispatch_envelope`` /
  ``hydro_budget_nameplate_aware`` / ``hydro_min_flow_floor`` are ARMED, so
  ``model.lp.rows._build_hydro_rows`` puts a monthly energy-budget row per
  (hydro unit, month) in the LP and its dual ``w`` is NOT in ``mc``;
* ramp rows and reserve co-opt rows **DO NOT EXIST on this keeper**
  (``ramp_limits = False``; ``caiso_reserve_coopt`` /
  ``energy_reserve_coopt = False``), so two of the handoff's four named
  constraint falsifiers are decided by the recipe, not by measurement;
* the post-solve ORDC scarcity adder is **cited, never re-measured** —
  caiso-229 bounded it at ``$0.017 / $0.006 / $0.003`` per MWh (2023/24/25) on
  CAISO's own constants against caiso-131 §4's committed minimum-headroom hour.

Stages (PRECOMMIT §1): 1 the interior-column census; 2 the dual signature
(G-FLAT — a budget/SOC dual is CONSTANT over the hours it governs, so
``lambda`` must take EXACTLY REPEATED values within a (zone, month)); 3 the
caiso-168 belly-surplus overlap (carried, never re-adjudicated); 4 the caiso-249
wedge re-read against LP optimality; 5 the hydro water-value band.

Gates: G-REPRO, **G-FLEET'** (the caiso-249 §6 item 3 repair, registered in
advance: the phantom test keys on the solver's authoritative
``_INJECTED_MUSTRUN_CLASSES`` tuple, not the caiso-248 shape heuristic),
G-CONSERVE, G-BENCH, G-CAP, G-HOLDOUT.

Writes ``results/calibration/_caiso250_lambda_carrier_anatomy.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso250_lambda_carrier_anatomy.py
"""

from __future__ import annotations

import gzip
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


C247 = _load("_caiso247_residual_regime_anatomy", "scripts/probes/_caiso247_residual_regime_anatomy.py")
C249 = _load("_caiso249_ownzone_attribution", "scripts/probes/_caiso249_ownzone_attribution.py")
C168 = _load("caiso168_storage_bid_phase0", "scripts/probes/caiso168_storage_bid_phase0.py")
C244 = C247.C244

BUNDLE = C247.BUNDLE
KEEPER_RUN_ID = C247.KEEPER_RUN_ID
OUT = REPO / "results/calibration/_caiso250_lambda_carrier_anatomy.json"
C249_JSON = REPO / "results/calibration/_caiso249_ownzone_attribution.json"
YEARS = C247.YEARS
HOURS = C247.HOURS
MONTH = C247.MONTH
TOL = C247.TOL
CA_ZONES = C247.CA_ZONES
GAS_GROUPS = C247.GAS_GROUPS
REGIMES = C247.REGIMES

#: rule 22 [R-HOLDOUT], fail-closed: this probe may read NOTHING else.
TRAINING_YEARS = frozenset({2023, 2024, 2025})

#: caiso-168's own belly-surplus cut, carried VERBATIM (never re-chosen here).
C168.BUNDLE = BUNDLE / "hourly"

#: G-FLAT recurrence thresholds, fixed a priori in PRECOMMIT §2 (P-6).
FLAT_MIN_REPEATS = (5, 10)
#: lambda rounding for the exact-repeat test, PRECOMMIT §1 stage 2.
FLAT_ROUND = 6


# ---------------------------------------------------------------------------
# fleet rebuild, WITH the storage block C247.rebuild_full drops
# ---------------------------------------------------------------------------
def rebuild_plus(year: int) -> dict:
    """``C247.rebuild_full``'s recipe path, keeping ``storage_units`` too.

    Same sanctioned path (``replay_keeper.run_year_kwargs`` +
    ``derived_run_year_inputs`` — never by parameter name, caiso-243 §10.4 /
    caiso-248 §8.1), one ``run_year(fleet_only=True)`` call, and the returned
    dict is a SUPERSET of ``C247.rebuild_full``'s so every downstream helper
    (``C249.own_zone_matches``, ``C244.reconstruct``) stays verbatim. The
    storage block is kept because the caiso-249 instrument never needed it and
    this session's whole object is which column carries ``rc = 0``.
    """
    import contextlib
    import io

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs.update(derived_run_year_inputs(BUNDLE, year))
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
    zone_names = list(
        split_caiso_import_node_per_hub(get_iso_config("CAISO")).zone_names
    )
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    pmax = np.asarray(fa.pmax, dtype=float)
    pmin = np.asarray(fa.pmin, dtype=float)
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(pmin[:, None], (pmin.size, HOURS))
    uid = np.array([str(u) for u in fa.unit_ids], dtype=object)
    group = np.array(
        [
            str(getattr(g, "plant_group", "") or "")
            or f"fuel:{getattr(g, 'fuel_type', 'unknown')}"
            for g in gens
        ],
        dtype=object,
    )
    zidx = np.asarray(fa.zone_idx, dtype=int)
    rows = []
    for r, u in enumerate(uid):
        z = zone_names[zidx[r]]
        if z not in C244.CORRIDOR_LANDING:
            continue
        rows.append(
            {
                "r": r,
                "uid": u,
                "name": u[len(z) + 1 :],
                "zone": z,
                "is_export": bool(pmin[r] < 0.0),
            }
        )
    return {
        "rows": rows,
        "mc": mc,
        "avail": np.asarray(fa.availability, dtype=float),
        "pmax": pmax,
        "pmin": pmin,
        "min_gen": np.asarray(mg, dtype=float),
        "zone_idx": zidx,
        "group": group,
        "zone_names": zone_names,
        "injected_mustrun_classes": sorted(C247.injected_mustrun_classes(year)),
        "storage_units": st.get("storage_units") or [],
        "storage_power_cap": st.get("storage_power_cap"),
        "log": buf.getvalue(),
    }


# ---------------------------------------------------------------------------
# the caiso-249 labelling, REPRODUCED (gated against the committed artifact)
# ---------------------------------------------------------------------------
def label_zone_hours(year: int, fl: dict, tol: float = TOL) -> dict:
    """Reproduce caiso-249's per-zone-hour regime labels and gap decomposition.

    Verbatim in construction with ``C249.analyse`` (own-zone complementarity,
    the delivery-factor import pass, the HUB reach test, then STORAGE /
    SURPLUS / UNRESOLVED), re-implemented here only because the committed probe
    returns aggregates and this session needs the per-zone-hour masks.
    **G-REPRO** checks the reproduction against the committed
    ``_caiso249_ownzone_attribution.json`` rather than trusting it.
    """
    price, klass_import, _bal = C244.sidecars(year)
    _recon, _x, state, _lam, _lo, _hi = C244.reconstruct(fl, price, klass_import)

    s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    demand = s.pivot(index="zone", columns="hour", values="demand").reindex(
        columns=range(HOURS)
    )
    dump = s.pivot(index="zone", columns="hour", values="dump").reindex(
        columns=range(HOURS)
    )
    stg = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    stg = stg[stg["pass"] == "P1"]
    chg_tot = stg.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0)
    dis_tot = stg.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0)
    storage_active = (chg_tot.to_numpy(float) > 1e-6) | (dis_tot.to_numpy(float) > 1e-6)

    a = C247.actual_rt(year)
    w = C247.rubric_weights(year)
    ok = np.isfinite(a) & (w > 0)
    denom = float(w[ok].sum())
    d_ca = demand.loc[list(CA_ZONES)].to_numpy(float)
    p_ca = price.loc[list(CA_ZONES)].to_numpy(float)
    share = d_ca / np.maximum(d_ca.sum(axis=0), 1e-9)
    lam_sys = (p_ca * share).sum(axis=0)
    gap_hourly = float((w[ok] * (lam_sys[ok] - a[ok])).sum() / denom)

    ratio = C249.delivery_ratio(year)
    by_group, gas_own, other_own = C249.own_zone_matches(fl, price, tol)
    hubs = C247.hub_masks(fl, price, state)
    lam_land = {
        land: price.loc[land].to_numpy(float) for land in C244.CORRIDOR_LANDING.values()
    }

    labels: dict[str, np.ndarray] = {}
    for z in CA_ZONES:
        lam_z = price.loc[z].to_numpy(float)
        hub_f = np.zeros(HOURS, dtype=bool)
        hub_m = np.zeros(HOURS, dtype=bool)
        for land, hm in hubs.items():
            reach = np.abs(lam_z - lam_land[land] * ratio[(land, z)]) <= tol
            hub_f |= hm["fitted"] & reach
            hub_m |= hm["measured"] & reach
        hub_m &= ~hub_f
        own_gas, own_other = gas_own[z], other_own[z]
        df_gas = np.zeros(HOURS, dtype=bool)
        df_other = np.zeros(HOURS, dtype=bool)
        source = np.full(HOURS, "", dtype=object)
        pending = ~(own_gas | own_other)
        for zp in CA_ZONES:
            if zp == z:
                continue
            implied = price.loc[zp].to_numpy(float) * ratio[(zp, z)]
            near = np.abs(lam_z - implied) <= tol
            for src_mask, dst in ((gas_own[zp], "gas"), (other_own[zp], "other")):
                take = pending & near & src_mask & (source == "")
                if not take.any():
                    continue
                source[take] = zp
                if dst == "gas":
                    df_gas |= take
                else:
                    df_other |= take
        df_other &= ~df_gas
        surplus = (lam_z <= 0.01) | (dump.loc[z].to_numpy(float) > 1e-6)
        order = [
            ("DOM_GAS", own_gas | df_gas),
            ("DOM_OTHER", own_other | df_other),
            ("HUB_FITTED", hub_f),
            ("HUB_MEASURED", hub_m),
            ("STORAGE", storage_active),
            ("SURPLUS", surplus),
        ]
        lab = np.full(HOURS, "UNRESOLVED", dtype=object)
        assigned = np.zeros(HOURS, dtype=bool)
        for name, mask in order:
            take = mask & ~assigned
            lab[take] = name
            assigned |= take
        labels[z] = lab

    contrib, weight = {}, {}
    for r in REGIMES:
        c = np.zeros(HOURS)
        wt = np.zeros(HOURS)
        for zi, z in enumerate(CA_ZONES):
            m = labels[z] == r
            c += np.where(m, w * share[zi] * (p_ca[zi] - np.nan_to_num(a)), 0.0)
            wt += np.where(m, w * share[zi], 0.0)
        contrib[r] = np.where(ok, c, 0.0)
        weight[r] = np.where(ok, wt, 0.0)
    tot = sum(float(v.sum()) for v in contrib.values()) / denom
    by_regime = {
        r: {
            "weight_share": round(float(weight[r].sum()) / denom, 4),
            "gap_share": (
                round((float(contrib[r].sum()) / denom) / tot, 4)
                if abs(tot) > 1e-9
                else None
            ),
        }
        for r in REGIMES
    }
    return {
        "labels": labels,
        "price": price,
        "p_ca": p_ca,
        "share": share,
        "w": w,
        "a": a,
        "ok": ok,
        "denom": denom,
        "contrib": contrib,
        "weight": weight,
        "gap_hourly": gap_hourly,
        "cells_sum": tot,
        "by_regime": by_regime,
        "storage_charge_total": chg_tot.to_numpy(float),
        "storage_discharge_total": dis_tot.to_numpy(float),
    }


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------
def g_fleet_prime(fl: dict, year: int) -> dict:
    """The caiso-249 §6 item 3 repair, REGISTERED IN ADVANCE (PRECOMMIT §1.1).

    caiso-249's G-FLEET keyed its phantom test on caiso-248's SHAPE heuristic,
    which flags CAISO 2023 ``oil`` (65 MWh, 2 levels) by coincidence and so
    failed the gate on a documented false positive. The authority is the
    solver's own ``_INJECTED_MUSTRUN_CLASSES`` tuple: a class is injected only
    if it is BOTH in that tuple and shape-detected in the bundle's sidecar.
    """
    import run_calibration_full as RCF

    authoritative = set(RCF._INJECTED_MUSTRUN_CLASSES)
    detected = set(fl["injected_mustrun_classes"])
    injected = detected & authoritative

    c_all = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c_all = c_all[c_all["pass"] == "P1"]
    sidecar_classes = {
        str(k) for k, g in c_all.groupby("klass", observed=True) if float(g["mw"].sum()) > 0
    }
    KLASS_TO_FAMILY = {
        "CC_REGULAR": "CC_REGULAR",
        "CC_CHP": "CC_CHP",
        "CT_PEAKER": "CT_PEAKER",
        "CT_CHP": "CT_CHP",
        "ST_GAS": "ST_GAS",
        "COAL": "COAL",
        "hydro": "hydro",
        "oil": "fuel:oil",
        "nuclear": "fuel:nuclear",
        "biomass": "fuel:biomass",
    }
    NON_FLEET = {"solar", "wind", "import", "OTHER"}
    families = {str(g) for g in fl["group"]}
    missing = sorted(
        k
        for k in sidecar_classes - injected - NON_FLEET
        if KLASS_TO_FAMILY.get(k, k) not in families
    )
    phantom = sorted(
        f for f in families if f.startswith("fuel:") and f.split(":", 1)[1] in injected
    )
    shape_only_phantom = sorted(
        f
        for f in families
        if f.startswith("fuel:") and f.split(":", 1)[1] in (detected - authoritative)
    )
    return {
        "authoritative_tuple": sorted(authoritative),
        "shape_detected": sorted(detected),
        "injected_effective": sorted(injected),
        "false_positives_dropped_by_the_repair": sorted(detected - authoritative),
        "sidecar_classes_with_no_lp_units": missing,
        "phantom_families_of_injected_classes": phantom,
        "families_the_caiso249_gate_would_have_flagged": shape_only_phantom,
        "pass": bool(not missing and not phantom),
    }


def g_repro(by_regime: dict, year: int) -> dict:
    """The reproduced labelling must match the COMMITTED caiso-249 artifact."""
    ref = json.loads(C249_JSON.read_text())["years"][str(year)]["by_regime"]
    diffs = {}
    worst = 0.0
    for r in REGIMES:
        for key in ("weight_share", "gap_share"):
            a = by_regime[r][key]
            b = ref[r][key]
            if a is None or b is None:
                continue
            d = abs(float(a) - float(b))
            diffs[f"{r}.{key}"] = round(d, 6)
            worst = max(worst, d)
    return {"max_abs_diff": round(worst, 6), "diffs": diffs, "pass": bool(worst <= 0.001)}


# ---------------------------------------------------------------------------
# stage 1 — the interior-column census
# ---------------------------------------------------------------------------
def storage_states(fl: dict, year: int, chg_tot: np.ndarray, dis_tot: np.ndarray) -> dict:
    """Per-tech charge/discharge bound state, on the keeper's OWN armed caps.

    Reconstructed by calling the shipped bound builders on the rebuilt fleet
    (``caiso_storage_shape_caps`` for the armed anchor, ``caiso_ps_charge_caps``
    for the per-plant pump ratings) rather than by inverting the dispatch
    (caiso-168's route) — the caps are then the LP's own, exactly.

    ISO-AGGREGATE by tech, because ``storage_<year>.parquet`` carries no zone
    (caiso-168 §7). A fleet strictly inside its aggregate bound is a NECESSARY
    condition for some unit of that tech to be interior, not a sufficient one.
    """
    from market_sim.model.storage import (
        _battery_mask,
        caiso_ps_charge_caps,
        caiso_storage_shape_caps,
    )

    units = fl["storage_units"]
    pc = np.asarray(fl["storage_power_cap"], dtype=float)
    pc2 = np.repeat(pc[:, None], HOURS, axis=1) if pc.ndim == 1 else pc
    chg_cap, dis_cap = caiso_storage_shape_caps(pc, units, year, HOURS)
    ps_chg = caiso_ps_charge_caps(pc, units, HOURS, chg_cap)
    if ps_chg is not None:
        chg_cap = ps_chg
    batt = _battery_mask(units)
    out: dict[str, dict] = {}
    for tech, mask in (("li_ion", batt), ("pumped_storage", ~batt)):
        out[tech] = {
            "n_units": int(mask.sum()),
            "chg_cap": chg_cap[mask].sum(axis=0),
            "dis_cap": dis_cap[mask].sum(axis=0),
            "power_cap": pc2[mask].sum(axis=0),
        }
    return out


def stage1_census(fl: dict, lab: dict, year: int) -> dict:
    """Which candidate family CAN carry ``rc = 0`` in the STORAGE zone-hours."""
    stg = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    stg = stg[stg["pass"] == "P1"]
    per_tech = {
        t: {
            "chg": g.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float),
            "dis": g.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float),
        }
        for t, g in stg.groupby("tech", observed=True)
    }
    caps = storage_states(fl, year, lab["storage_charge_total"], lab["storage_discharge_total"])

    EPS = 1e-6
    states: dict[str, np.ndarray] = {}
    gcap = {}
    for tech in ("li_ion", "pumped_storage"):
        d = per_tech.get(str(tech), {"chg": np.zeros(HOURS), "dis": np.zeros(HOURS)})
        c = caps[tech]
        states[f"{tech}_chg_interior"] = (d["chg"] > EPS) & (d["chg"] < c["chg_cap"] - EPS)
        states[f"{tech}_dis_interior"] = (d["dis"] > EPS) & (d["dis"] < c["dis_cap"] - EPS)
        gcap[tech] = {
            "fleet_power_cap_mw_dec": round(float(c["power_cap"][-1]), 1),
            "n_units": c["n_units"],
            "max_chg_over_cap_mw": round(float(np.max(d["chg"] - c["chg_cap"])), 4),
            "max_dis_over_cap_mw": round(float(np.max(d["dis"] - c["dis_cap"])), 4),
            "hours_chg_at_cap": int(((d["chg"] > EPS) & (d["chg"] >= c["chg_cap"] - EPS)).sum()),
            "hours_dis_at_cap": int(((d["dis"] > EPS) & (d["dis"] >= c["dis_cap"] - EPS)).sum()),
        }
    storage_interior = (
        states["li_ion_chg_interior"]
        | states["li_ion_dis_interior"]
        | states["pumped_storage_chg_interior"]
        | states["pumped_storage_dis_interior"]
    )

    # hydro: ISO-aggregate hourly envelope from the rebuilt fleet
    hyd = fl["group"] == "hydro"
    avail = fl["avail"][hyd]
    upper = (fl["pmax"][hyd][:, None] * avail).sum(axis=0)
    lower = np.minimum(fl["min_gen"][hyd], fl["pmax"][hyd][:, None] * avail).sum(axis=0)
    c_all = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c_all = c_all[(c_all["pass"] == "P1") & (c_all["klass"] == "hydro")]
    hyd_mw = (
        c_all.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )
    hydro_interior = (hyd_mw > lower + 1.0) & (hyd_mw < upper - 1.0)

    # census over the STORAGE cell, load-weighted on the caiso-131/140 convention
    w, share, ok = lab["w"], lab["share"], lab["ok"]
    p_ca, a, denom = lab["p_ca"], lab["a"], lab["denom"]
    cells = {
        "BOTH": hydro_interior & storage_interior,
        "HYDRO_ONLY": hydro_interior & ~storage_interior,
        "STORAGE_ONLY": ~hydro_interior & storage_interior,
        "NEITHER": ~hydro_interior & ~storage_interior,
    }
    out = {"gates_G_CAP": gcap, "hydro_envelope_mw": {
        "mean_lower": round(float(lower.mean()), 1),
        "mean_upper": round(float(upper.mean()), 1),
        "mean_dispatch": round(float(hyd_mw.mean()), 1),
        "hours_interior": int(hydro_interior.sum()),
    }}
    for regime in ("STORAGE", "DOM_GAS"):
        tot_w = 0.0
        tot_g = 0.0
        rows = {}
        for name, mask in cells.items():
            gw = 0.0
            gg = 0.0
            for zi, z in enumerate(CA_ZONES):
                sel = (lab["labels"][z] == regime) & ok & mask
                base = w * share[zi]
                gw += float(base[sel].sum())
                gg += float((base * (p_ca[zi] - np.nan_to_num(a)))[sel].sum())
            rows[name] = {"weight": gw / denom, "gap": gg / denom}
            tot_w += gw / denom
            tot_g += gg / denom
        out[regime] = {
            "cell_weight_share": round(tot_w, 4),
            "cell_gap_usd_per_mwh": round(tot_g, 4),
            "split": {
                k: {
                    "weight_share_of_cell": round(v["weight"] / tot_w, 4) if tot_w > 1e-12 else None,
                    "gap_share_of_cell": round(v["gap"] / tot_g, 4) if abs(tot_g) > 1e-12 else None,
                    "gap_usd_per_mwh": round(v["gap"], 4),
                }
                for k, v in rows.items()
            },
        }
    out["storage_column_states_hours"] = {
        k: int(v.sum()) for k, v in states.items()
    }
    return out


# ---------------------------------------------------------------------------
# stage 2 — the dual signature (G-FLAT)
# ---------------------------------------------------------------------------
def stage2_flat(lab: dict) -> dict:
    """Exact-repeat multiplicity of ``lambda`` within each (zone, month).

    A monthly hydro budget dual is CONSTANT over a month; a storage SOC dual is
    constant over an SOC-interior episode. Either way ``lambda_z`` must take
    EXACTLY REPEATED values wherever such a column is the setter. Multiplicity
    is counted over ALL hours of the (zone, month), not just the cell's.
    """
    w, share, ok = lab["w"], lab["share"], lab["ok"]
    denom = lab["denom"]
    out: dict[str, dict] = {}
    mult = {}
    for zi, z in enumerate(CA_ZONES):
        lam = np.round(lab["p_ca"][zi], FLAT_ROUND)
        m = np.zeros(HOURS, dtype=int)
        for mo in range(1, 13):
            sel = MONTH == mo
            vals, inv, cnt = np.unique(lam[sel], return_inverse=True, return_counts=True)
            m[sel] = cnt[inv]
        mult[z] = m
    for regime in ("STORAGE", "DOM_GAS", "ALL"):
        num = {k: 0.0 for k in FLAT_MIN_REPEATS}
        den = 0.0
        for zi, z in enumerate(CA_ZONES):
            sel = ok if regime == "ALL" else ((lab["labels"][z] == regime) & ok)
            base = (w * share[zi])[sel]
            den += float(base.sum())
            for k in FLAT_MIN_REPEATS:
                num[k] += float(base[mult[z][sel] >= k].sum())
        out[regime] = {
            "load_weight_share_of_year": round(den / denom, 4),
            **{
                f"share_on_lambda_repeating_ge_{k}": (
                    round(num[k] / den, 4) if den > 1e-12 else None
                )
                for k in FLAT_MIN_REPEATS
            },
        }
    return out


# ---------------------------------------------------------------------------
# stage 3 — the caiso-168 belly-surplus overlap (CARRIED, not re-adjudicated)
# ---------------------------------------------------------------------------
def stage3_overlap(lab: dict, year: int) -> dict:
    hub = C168._hub(year)
    hod = np.arange(HOURS) % 24
    belly = (hod >= C168.BELLY[0]) & (hod < C168.BELLY[1])
    mask = belly & np.isfinite(hub) & (hub <= C168.SURPLUS_MAX)
    w, share, ok, denom = lab["w"], lab["share"], lab["ok"], lab["denom"]
    p_ca, a = lab["p_ca"], lab["a"]
    res = {}
    for regime in ("STORAGE", "DOM_GAS"):
        gw = gg = tw = tg = 0.0
        for zi, z in enumerate(CA_ZONES):
            sel = (lab["labels"][z] == regime) & ok
            base = w * share[zi]
            gapv = base * (p_ca[zi] - np.nan_to_num(a))
            tw += float(base[sel].sum())
            tg += float(gapv[sel].sum())
            gw += float(base[sel & mask].sum())
            gg += float(gapv[sel & mask].sum())
        res[regime] = {
            "weight_share_inside_belly_surplus": round(gw / tw, 4) if tw > 1e-12 else None,
            "gap_share_inside_belly_surplus": round(gg / tg, 4) if abs(tg) > 1e-12 else None,
            "gap_inside_usd_per_mwh": round(gg / denom, 4),
        }
    res["_belly_surplus_hours"] = int(mask.sum())
    res["_cut"] = "caiso-168 VERBATIM: Pacific [09,16) and measured CA DA hub <= $20/MWh"
    return res


# ---------------------------------------------------------------------------
# stage 4 — the caiso-249 wedge, re-read against LP optimality
# ---------------------------------------------------------------------------
def stage4_wedge(fl: dict, lab: dict) -> dict:
    """Distance from lambda to the nearest available own-zone offer, BOTH sides.

    Every available unit at its LOWER bound satisfies ``mc >= lambda`` at any
    optimum, so a positive nearest-offer wedge is mechanical. If the distance
    to the nearest offer BELOW is of the same order, caiso-249's published
    "lambda sits JUST UNDER the thermal stack" is a statement about STACK
    DENSITY, not about a carrier.
    """
    zof = np.array([fl["zone_names"][i] for i in fl["zone_idx"]], dtype=object)
    dom = ~np.isin(zof, list(C244.CORRIDOR_LANDING))
    w, share, ok = lab["w"], lab["share"], lab["ok"]
    out: dict[str, dict] = {}
    for regime in ("STORAGE", "DOM_GAS"):
        above, below, wts = [], [], []
        for zi, z in enumerate(CA_ZONES):
            sel = (lab["labels"][z] == regime) & ok
            if not sel.any():
                continue
            in_z = dom & (zof == z)
            if not in_z.any():
                continue
            lam = lab["p_ca"][zi]
            offers = np.where(fl["avail"][in_z] > 0.01, fl["mc"][in_z], np.nan)
            d = offers - lam[None, :]
            up = np.where(d > 0, d, np.nan)
            dn = np.where(d < 0, -d, np.nan)
            with np.errstate(invalid="ignore"):
                nu = np.nanmin(np.where(np.isnan(up), np.inf, up), axis=0)
                nd = np.nanmin(np.where(np.isnan(dn), np.inf, dn), axis=0)
            above.append(nu[sel])
            below.append(nd[sel])
            wts.append((w * share[zi])[sel])
        if not wts:
            continue
        A = np.concatenate(above)
        B = np.concatenate(below)
        W = np.concatenate(wts)

        def q(v, f):
            fin = np.isfinite(v)
            vv, ww = v[fin], W[fin]
            if ww.sum() <= 0:
                return None
            o = np.argsort(vv)
            cw = np.cumsum(ww[o]) / ww.sum()
            return round(float(vv[o][np.searchsorted(cw, f)]), 3)

        out[regime] = {
            "median_to_nearest_offer_ABOVE": q(A, 0.5),
            "median_to_nearest_offer_BELOW": q(B, 0.5),
            "p25_ABOVE": q(A, 0.25),
            "p25_BELOW": q(B, 0.25),
            "ratio_below_over_above": (
                round(q(B, 0.5) / q(A, 0.5), 3)
                if q(A, 0.5) not in (None, 0.0) and q(B, 0.5) is not None
                else None
            ),
        }
    return out


# ---------------------------------------------------------------------------
# stage 5 — the hydro water-value band
# ---------------------------------------------------------------------------
def stage5_hydro(fl: dict, lab: dict, census_masks: dict) -> dict:
    hydro_interior = census_masks["hydro_interior"]
    w, share, ok = lab["w"], lab["share"], lab["ok"]
    hyd = fl["group"] == "hydro"
    iqrs, wts = [], []
    for zi, z in enumerate(CA_ZONES):
        sel0 = (lab["labels"][z] == "STORAGE") & ok & hydro_interior
        if not sel0.any():
            continue
        lam = lab["p_ca"][zi]
        for mo in range(1, 13):
            sel = sel0 & (MONTH == mo)
            if sel.sum() < 5:
                continue
            v = lam[sel]
            iqrs.append(float(np.percentile(v, 75) - np.percentile(v, 25)))
            wts.append(float((w * share[zi])[sel].sum()))
    if not iqrs:
        return {"n_zone_months": 0}
    iq = np.array(iqrs)
    ww = np.array(wts)
    o = np.argsort(iq)
    cw = np.cumsum(ww[o]) / ww.sum()
    mc_h = fl["mc"][hyd]
    return {
        "n_zone_months": len(iqrs),
        "weighted_median_within_zone_month_lambda_IQR": round(
            float(iq[o][np.searchsorted(cw, 0.5)]), 3
        ),
        "weighted_p75_IQR": round(float(iq[o][np.searchsorted(cw, 0.75)]), 3),
        "hydro_mc_median_usd_per_mwh": round(float(np.nanmedian(mc_h)), 3),
        "hydro_mc_p95_usd_per_mwh": round(float(np.nanpercentile(mc_h, 95)), 3),
    }



# ---------------------------------------------------------------------------
# stage 6 — POST-REGISTRATION CHARACTERISATION of the cell OUTSIDE the belly
# ---------------------------------------------------------------------------
def stage6_outside_belly(fl: dict, lab: dict, year: int) -> dict:
    """Describe the part of the STORAGE cell caiso-168 has NOT adjudicated.

    **Not a new labelling rule and not a scored prediction** (PRECOMMIT §3
    stop rule; the caiso-247/249 group-characterisation convention): a
    DESCRIPTION of a registered cell, reported because it makes the successor
    object concrete. It relabels nothing and changes no cell.
    """
    hub = C168._hub(year)
    hod = np.arange(HOURS) % 24
    belly = (hod >= C168.BELLY[0]) & (hod < C168.BELLY[1])
    inside = belly & np.isfinite(hub) & (hub <= C168.SURPLUS_MAX)
    outside = ~inside

    stg = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
    stg = stg[stg["pass"] == "P1"]
    per_tech = {
        str(t): {
            "chg": g.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float),
            "dis": g.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float),
        }
        for t, g in stg.groupby("tech", observed=True)
    }
    caps = storage_states(fl, year, lab["storage_charge_total"], lab["storage_discharge_total"])
    EPS = 1e-6
    st_state = {}
    for tech in ("li_ion", "pumped_storage"):
        d = per_tech.get(tech, {"chg": np.zeros(HOURS), "dis": np.zeros(HOURS)})
        c = caps[tech]
        st_state[f"{tech}_chg_interior"] = (d["chg"] > EPS) & (d["chg"] < c["chg_cap"] - EPS)
        st_state[f"{tech}_dis_interior"] = (d["dis"] > EPS) & (d["dis"] < c["dis_cap"] - EPS)

    w, share, ok, denom = lab["w"], lab["share"], lab["ok"], lab["denom"]
    p_ca, a = lab["p_ca"], lab["a"]

    def cell(mask: np.ndarray) -> tuple[float, float]:
        gw = gg = 0.0
        for zi, z in enumerate(CA_ZONES):
            sel = (lab["labels"][z] == "STORAGE") & ok & mask
            base = w * share[zi]
            gw += float(base[sel].sum())
            gg += float((base * (p_ca[zi] - np.nan_to_num(a)))[sel].sum())
        return gw / denom, gg / denom

    ow, og = cell(outside)
    hod_gap = {}
    for h in range(24):
        _, g = cell(outside & (hod == h))
        hod_gap[h] = round(g, 4)
    by_state = {}
    for name, m in st_state.items():
        _w, _g = cell(outside & m)
        by_state[name] = {"weight_share_of_year": round(_w, 4), "gap_usd_per_mwh": round(_g, 4)}
    _wn, _gn = cell(outside & ~(
        st_state["li_ion_chg_interior"]
        | st_state["li_ion_dis_interior"]
        | st_state["pumped_storage_chg_interior"]
        | st_state["pumped_storage_dis_interior"]
    ))
    by_state["no_storage_column_interior"] = {
        "weight_share_of_year": round(_wn, 4),
        "gap_usd_per_mwh": round(_gn, 4),
    }
    return {
        "_note": "POST-REGISTRATION CHARACTERISATION — not a labelling rule, not a scored prediction",
        "outside_belly_weight_share_of_year": round(ow, 4),
        "outside_belly_gap_usd_per_mwh": round(og, 4),
        "gap_by_hour_of_day": hod_gap,
        "gap_by_storage_column_state": by_state,
    }


# ---------------------------------------------------------------------------
def analyse(year: int) -> dict:
    if year not in TRAINING_YEARS:
        raise SystemExit(f"rule 22 [R-HOLDOUT]: {year} is outside 2023-2025")
    fl = rebuild_plus(year)
    lab = label_zone_hours(year, fl)

    bench = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"))
    rt_lw = float((lab["a"][lab["ok"]] * lab["w"][lab["ok"]]).sum() / lab["denom"])

    census = stage1_census(fl, lab, year)
    # recompute the hydro mask once more for stage 5 (same construction)
    hyd = fl["group"] == "hydro"
    avail = fl["avail"][hyd]
    upper = (fl["pmax"][hyd][:, None] * avail).sum(axis=0)
    lower = np.minimum(fl["min_gen"][hyd], fl["pmax"][hyd][:, None] * avail).sum(axis=0)
    c_all = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c_all = c_all[(c_all["pass"] == "P1") & (c_all["klass"] == "hydro")]
    hyd_mw = c_all.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    hydro_interior = (hyd_mw > lower + 1.0) & (hyd_mw < upper - 1.0)

    return {
        "keeper_run_id": KEEPER_RUN_ID,
        "tol": TOL,
        "G_REPRO": g_repro(lab["by_regime"], year),
        "G_FLEET_PRIME": g_fleet_prime(fl, year),
        "G_CONSERVE": {
            "gap_hourly": round(lab["gap_hourly"], 4),
            "cells_sum": round(lab["cells_sum"], 4),
            "caiso248_published_gap": C249.CAISO248_GAP[year],
            "pass": bool(
                abs(lab["cells_sum"] - lab["gap_hourly"]) < 1e-9
                and abs(lab["gap_hourly"] - C249.CAISO248_GAP[year]) <= 5e-4
            ),
        },
        "G_BENCH": {
            "recomputed_rt_lw": round(rt_lw, 4),
            "committed_rt_lw": bench["bench"]["avgLMP"]["rt_lw"],
            "pass": bool(abs(rt_lw - float(bench["bench"]["avgLMP"]["rt_lw"])) <= 0.01),
        },
        "G_HOLDOUT": {"year": year, "pass": year in TRAINING_YEARS},
        "stage1_census": census,
        "stage2_flatness": stage2_flat(lab),
        "stage3_caiso168_overlap": stage3_overlap(lab, year),
        "stage4_wedge_both_sides": stage4_wedge(fl, lab),
        "stage5_hydro_water_value": stage5_hydro(
            fl, lab, {"hydro_interior": hydro_interior}
        ),
        "stage5b_hydro_interiority_vacuity": {
            "hours_hydro_interior": int(hydro_interior.sum()),
            "share_of_all_hours": round(float(hydro_interior.mean()), 4),
        },
        "stage6_outside_belly_POST_REGISTRATION": stage6_outside_belly(fl, lab, year),
        "by_regime_reproduced": lab["by_regime"],
    }


def main() -> None:
    out = {
        "_provenance": {
            "session": "caiso-250 (what sets lambda when no thermal unit is marginal, ZERO LP)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": KEEPER_RUN_ID,
            "precommit": "PRECOMMIT-caiso250-lambda-carrier-2026-09-05.md",
            "instrument": (
                "LP reduced-cost complementarity on the NON-thermal columns "
                "(hydro monthly-budget dual, storage SOC dual) over caiso-249's "
                "own-zone labelling, reproduced and gated; plus the exact-repeat "
                "dual signature, the caiso-168 belly-surplus overlap (carried), "
                "and the caiso-249 wedge re-read against LP optimality"
            ),
            "fleet": "replay_keeper.run_year_kwargs + derived_run_year_inputs (caiso-248 repair)",
            "scarcity_overlay": (
                "NOT re-measured — caiso-229's arithmetic bound is cited: max "
                "$0.017/$0.006/$0.003 per MWh (2023/24/25)"
            ),
            "note": "NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG.",
        },
        "years": {},
    }
    for y in YEARS:
        r = analyse(y)
        out["years"][y] = r
        print(f"\n===== {y} =====")
        print(f"  G-REPRO {r['G_REPRO']['pass']} (max diff {r['G_REPRO']['max_abs_diff']})")
        print(
            f"  G-FLEET' {r['G_FLEET_PRIME']['pass']} "
            f"(injected {r['G_FLEET_PRIME']['injected_effective']}, "
            f"dropped-by-repair {r['G_FLEET_PRIME']['false_positives_dropped_by_the_repair']}, "
            f"caiso249-would-flag {r['G_FLEET_PRIME']['families_the_caiso249_gate_would_have_flagged']})"
        )
        print(
            f"  G-CONSERVE {r['G_CONSERVE']['pass']} {r['G_CONSERVE']['cells_sum']} vs "
            f"{r['G_CONSERVE']['gap_hourly']}; G-BENCH {r['G_BENCH']['pass']}"
        )
        print("  G-CAP:", r["stage1_census"]["gates_G_CAP"])
        print("  hydro envelope:", r["stage1_census"]["hydro_envelope_mw"])
        for reg in ("STORAGE", "DOM_GAS"):
            c = r["stage1_census"][reg]
            print(f"  [{reg}] weight {c['cell_weight_share']} gap {c['cell_gap_usd_per_mwh']}")
            for k, v in c["split"].items():
                print(f"     {k:14s} w {v['weight_share_of_cell']}  gap-share {v['gap_share_of_cell']}  gap$ {v['gap_usd_per_mwh']}")
        print("  flatness:", r["stage2_flatness"])
        print("  caiso-168 overlap:", r["stage3_caiso168_overlap"])
        print("  wedge:", r["stage4_wedge_both_sides"])
        print("  hydro water value:", r["stage5_hydro_water_value"])
        print("  hydro interiority vacuity:", r["stage5b_hydro_interiority_vacuity"])
        print("  OUTSIDE belly (post-reg):", {k: v for k, v in r["stage6_outside_belly_POST_REGISTRATION"].items() if k != "gap_by_hour_of_day"})
        print("  OUTSIDE belly hod gap:", r["stage6_outside_belly_POST_REGISTRATION"]["gap_by_hour_of_day"])
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
