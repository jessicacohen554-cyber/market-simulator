"""caiso-249 — resolve the STORAGE residual bucket: OWN-ZONE complementarity + the measured delivery-factor ratio. ZERO LP.

Pre-registered in
``PRECOMMIT-caiso249-ownzone-loss-adjusted-attribution-2026-09-05.md``
(pushed to ``origin`` before this file was written and before any cell of the
object was computed). **NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG.**

The object (PRECOMMIT §0): caiso-248's corrected decomposition leaves
``STORAGE`` — a RESIDUAL label, assigned when no unit price-matched and storage
happened to be cycling — carrying **43.2 % (2024) / 53.3 % (2025)** of the C3a
gap, the largest 2025 cell. No DOM_GAS number can be quoted until it resolves.

The diagnosed cause, from the code rather than the residual (PRECOMMIT §0.1):
the keeper runs ``caiso_zonal_loss_surface``, and
``model.interchange.caiso.build_caiso_link_loss`` states the resulting price
relation exactly — for an interior uncongested flow ``x -> y``,
``lambda_y = lambda_x * (1 + dev_y,m) / (1 + dev_x,m)``. CAISO's measured
deviations run about −3 to −4 %, so two zones' duals differ by 0.4–1.5 $/MWh
with nothing congested. caiso-247 matched every unit against EVERY zone's dual
inside a 0.05 window, so a unit in NP15 was compared to SDGE's dual and could
only miss; those zone-hours fell through to ``STORAGE``.

The replacement (PRECOMMIT §1.1), frozen before measurement:

1. **OWN-ZONE** — a domestic unit LOCATED in ``z``, available, with
   ``|mc - lambda_z| <= TOL``. Exact complementarity: same zone, same dual, no
   delivery factor between them. ``DOM_GAS`` / ``DOM_OTHER`` by family.
2. **DF-IMPORT** — no own-zone match, but some ``z'`` has one and
   ``|lambda_z - lambda_z' * (1+dev_z,m)/(1+dev_z',m)| <= TOL``: an interior
   uncongested path from ``z'`` to ``z``. Takes ``z'``'s family.
3. **HUB** — the caiso-247 definition unchanged (import-row complementarity at
   the WECC node with the corridor link unbound), its landing-zone reach test
   also delivery-factor corrected. Runs AFTER the domestic passes here, the
   reverse of caiso-247; the G-ORDER variant restores caiso-247's order so the
   HUB cell stays comparable to the published one.
4. Then ``STORAGE`` / ``SURPLUS`` / ``UNRESOLVED``.

Gap decomposition, weights and comparator are UNCHANGED from caiso-247/248 —
the caiso-131 §2 / caiso-140 §A common-weight convention over zone-hours, the
rubric's ``rt_lw`` weights on both sides. Only the LABELLING changes, which is
what G-CONSERVE checks.

Gates: G-FLEET (new — the gate caiso-248 §5.2 named as missing), G-CONSERVE,
G-BENCH, G-RECON, G-GAP, G-ORDER, G-DF (PRECOMMIT §1.2).

Writes ``results/calibration/_caiso249_ownzone_attribution.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso249_ownzone_attribution.py
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

_spec = importlib.util.spec_from_file_location(
    "_caiso247_residual_regime_anatomy",
    REPO / "scripts/probes/_caiso247_residual_regime_anatomy.py",
)
C247 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C247)
C244 = C247.C244

BUNDLE = C247.BUNDLE
KEEPER_RUN_ID = C247.KEEPER_RUN_ID
OUT = REPO / "results/calibration/_caiso249_ownzone_attribution.json"
YEARS = C247.YEARS
HOURS = C247.HOURS
MONTH = C247.MONTH
TOL = C247.TOL
TOL_SENS = C247.TOL_SENS
CA_ZONES = C247.CA_ZONES
GAS_GROUPS = C247.GAS_GROUPS
FITTED_ROWS = C247.FITTED_ROWS
REGIMES = C247.REGIMES

#: gap_hourly published by caiso-248 — G-CONSERVE pins the total (PRECOMMIT P-2)
CAISO248_GAP = {2023: 1.3071, 2024: 3.7812, 2025: 3.1507}


def delivery_ratio(year: int) -> dict[tuple[str, str], np.ndarray]:
    """``(z', z) -> (1+dev_z,m)/(1+dev_z',m)`` per hour, on the model's 8760 map.

    The ``build_caiso_link_loss`` relation. Expanded on the SAME non-leap month
    map the loss-link builder expands on, so the caiso-248 leap-calendar trap
    cannot recur here.
    """
    from market_sim.data.loss_surface import load_zone_month_deviation

    dev = load_zone_month_deviation("CAISO", year)
    out: dict[tuple[str, str], np.ndarray] = {}
    for zp in CA_ZONES:
        for z in CA_ZONES:
            a = np.asarray(dev[zp], dtype=float)[MONTH - 1]
            b = np.asarray(dev[z], dtype=float)[MONTH - 1]
            out[(zp, z)] = (1.0 + b) / (1.0 + a)
    return out


def own_zone_matches(
    fl: dict, price: pd.DataFrame, tol: float
) -> tuple[dict[str, dict[str, np.ndarray]], dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Per zone: which domestic families are marginal AT THAT ZONE'S OWN dual.

    Exact complementarity — ``mc = lambda`` is necessary for a unit strictly
    between its bounds, and unit and dual are in the SAME zone, so no delivery
    factor sits between them (PRECOMMIT §0.2). It can still OVER-identify (a
    unit at a bound whose offer coincides with the dual); disclosed, and the
    TOL_SENS variant bounds it.
    """
    zone_names = fl["zone_names"]
    zof = np.array([zone_names[i] for i in fl["zone_idx"]], dtype=object)
    avail = fl["avail"] > 0.01
    mc = fl["mc"]
    by_group: dict[str, dict[str, np.ndarray]] = {}
    gas: dict[str, np.ndarray] = {}
    other: dict[str, np.ndarray] = {}
    for z in CA_ZONES:
        lam = price.loc[z].to_numpy(float)
        in_z = zof == z
        g_any = np.zeros(HOURS, dtype=bool)
        o_any = np.zeros(HOURS, dtype=bool)
        groups: dict[str, np.ndarray] = {}
        for grp in sorted(set(fl["group"][in_z])):
            sel = in_z & (fl["group"] == grp)
            if not sel.any():
                continue
            hit = ((np.abs(mc[sel] - lam[None, :]) <= tol) & avail[sel]).any(axis=0)
            if not hit.any():
                continue
            groups[str(grp)] = hit
            if grp in GAS_GROUPS:
                g_any |= hit
            else:
                o_any |= hit
        by_group[z] = groups
        gas[z] = g_any
        other[z] = o_any
    return by_group, gas, other


def analyse(year: int, hub_first: bool = False, tol: float = TOL) -> dict:
    fl = C247.rebuild_full(year)
    price, klass_import, _bal = C244.sidecars(year)
    recon, x, state, lam, x_lo, x_hi = C244.reconstruct(fl, price, klass_import)

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
    chg = stg.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    dis = stg.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    storage_active = (chg > 1e-6) | (dis > 1e-6)

    a = C247.actual_rt(year)
    w = C247.rubric_weights(year)
    ok = np.isfinite(a) & (w > 0)
    denom = float(w[ok].sum())
    d_ca = demand.loc[list(CA_ZONES)].to_numpy(float)
    p_ca = price.loc[list(CA_ZONES)].to_numpy(float)
    share = d_ca / np.maximum(d_ca.sum(axis=0), 1e-9)
    lam_sys = (p_ca * share).sum(axis=0)
    gap_hourly = float((w[ok] * (lam_sys[ok] - a[ok])).sum() / denom)

    # ---- G-FLEET: the rebuilt fleet IS the solve's fleet ---------------------
    c_all = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c_all = c_all[c_all["pass"] == "P1"]
    sidecar_classes = {
        str(k)
        for k, g in c_all.groupby("klass", observed=True)
        if float(g["mw"].sum()) > 0
    }
    injected = set(fl["injected_mustrun_classes"])
    fleet_families = {str(g) for g in fl["group"]}
    #: sidecar klass -> the rebuild's family label for it
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
    #: klasses with no LP-fleet twin by construction (LP variables or injected)
    NON_FLEET = {"solar", "wind", "import", "OTHER"}
    missing = sorted(
        k
        for k in sidecar_classes - injected - NON_FLEET
        if KLASS_TO_FAMILY.get(k, k) not in fleet_families
    )
    phantom = sorted(
        f
        for f in fleet_families
        if f and f.startswith("fuel:") and f.split(":", 1)[1] in injected
    )
    g_fleet = {
        "sidecar_classes": sorted(sidecar_classes),
        "injected_mustrun_classes": sorted(injected),
        "fleet_families": sorted(f for f in fleet_families if f),
        "sidecar_classes_with_no_lp_units": missing,
        "phantom_families_of_injected_classes": phantom,
        "pass": bool(not missing and not phantom),
    }

    # ---- labelling ----------------------------------------------------------
    ratio = delivery_ratio(year)
    by_group, gas_own, other_own = own_zone_matches(fl, price, tol)
    hubs = C247.hub_masks(fl, price, state)
    lam_land = {
        land: price.loc[land].to_numpy(float) for land in C244.CORRIDOR_LANDING.values()
    }

    labels: dict[str, np.ndarray] = {}
    src_zone: dict[str, np.ndarray] = {}
    df_material = {"df_import_zonehours": 0, "raw_outside_tol": 0}
    for z in CA_ZONES:
        lam_z = price.loc[z].to_numpy(float)
        # --- pass 3 inputs: HUB, with the reach test delivery-factor corrected
        hub_f = np.zeros(HOURS, dtype=bool)
        hub_m = np.zeros(HOURS, dtype=bool)
        for land, hm in hubs.items():
            reach = np.abs(lam_z - lam_land[land] * ratio[(land, z)]) <= tol
            hub_f |= hm["fitted"] & reach
            hub_m |= hm["measured"] & reach
        hub_m &= ~hub_f
        # --- pass 1: own zone
        own_gas, own_other = gas_own[z], other_own[z]
        # --- pass 2: delivery-factor import from a zone that HAS a match
        df_gas = np.zeros(HOURS, dtype=bool)
        df_other = np.zeros(HOURS, dtype=bool)
        source = np.full(HOURS, "", dtype=object)
        pending = ~(own_gas | own_other)
        for zp in CA_ZONES:
            if zp == z:
                continue
            lam_p = price.loc[zp].to_numpy(float)
            implied = lam_p * ratio[(zp, z)]
            near = np.abs(lam_z - implied) <= tol
            raw_far = np.abs(lam_z - lam_p) > tol
            for src_mask, dst in ((gas_own[zp], "gas"), (other_own[zp], "other")):
                take = pending & near & src_mask & (source == "")
                if not take.any():
                    continue
                source[take] = zp
                if dst == "gas":
                    df_gas |= take
                else:
                    df_other |= take
                df_material["df_import_zonehours"] += int(take.sum())
                df_material["raw_outside_tol"] += int((take & raw_far).sum())
        df_other &= ~df_gas
        dump_pos = dump.loc[z].to_numpy(float) > 1e-6
        surplus = (lam_z <= 0.01) | dump_pos
        order = (
            [
                ("HUB_FITTED", hub_f),
                ("HUB_MEASURED", hub_m),
                ("DOM_GAS", own_gas | df_gas),
                ("DOM_OTHER", own_other | df_other),
            ]
            if hub_first
            else [
                ("DOM_GAS", own_gas | df_gas),
                ("DOM_OTHER", own_other | df_other),
                ("HUB_FITTED", hub_f),
                ("HUB_MEASURED", hub_m),
            ]
        )
        order += [("STORAGE", storage_active), ("SURPLUS", surplus)]
        lab = np.full(HOURS, "UNRESOLVED", dtype=object)
        assigned = np.zeros(HOURS, dtype=bool)
        for name, mask in order:
            take = mask & ~assigned
            lab[take] = name
            assigned |= take
        labels[z] = lab
        src_zone[z] = source

    # ---- decomposition (unchanged convention) -------------------------------
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
    by_regime = {}
    for r in REGIMES:
        gs = float(contrib[r].sum()) / denom
        ws = float(weight[r].sum()) / denom
        by_regime[r] = {
            "weight_share": round(ws, 4),
            "gap_contribution_usd_per_mwh": round(gs, 4),
            "gap_share": round(gs / tot, 4) if abs(tot) > 1e-9 else None,
            "CR": round((gs / tot) / ws, 3) if ws > 1e-9 and abs(tot) > 1e-9 else None,
            "mean_residual_usd_per_mwh": round(gs / ws, 3) if ws > 1e-9 else None,
        }
    by_regime["_total_gap_usd_per_mwh"] = round(tot, 4)

    # per-family characterisation inside DOM_GAS (own-zone matches only)
    fam: dict[str, dict] = {}
    for zi, z in enumerate(CA_ZONES):
        base = w * share[zi]
        inreg = np.isin(labels[z], ["DOM_GAS", "DOM_OTHER"]) & ok
        for g, m in by_group[z].items():
            sel = inreg & m
            if not sel.any():
                continue
            e = fam.setdefault(g, {"gap": 0.0, "weight": 0.0})
            e["gap"] += float((base * (p_ca[zi] - np.nan_to_num(a)))[sel].sum()) / denom
            e["weight"] += float(base[sel].sum()) / denom
    families = {
        g: {
            "gap_contribution_usd_per_mwh": round(v["gap"], 4),
            "weight_share": round(v["weight"], 4),
            "mean_residual_usd_per_mwh": (
                round(v["gap"] / v["weight"], 3) if v["weight"] > 1e-9 else None
            ),
        }
        for g, v in sorted(fam.items(), key=lambda kv: -abs(kv[1]["gap"]))
    }

    # --- POST-REGISTRATION CHARACTERISATION of the STORAGE cell -------------
    # Not a new labelling rule (the stop rule forbids reaching for one) and not
    # a scored prediction: a DESCRIPTION of a registered cell, in the caiso-247
    # group-characterisation convention. In the zone-hours that fell through to
    # STORAGE, how far is lambda_z from the nearest available domestic offer in
    # that zone, and on which side? A systematic POSITIVE wedge points at an
    # adder / floor / co-optimisation term above the offer stack; a symmetric
    # spread points at storage's own opportunity-cost dual.
    zone_names_l = fl["zone_names"]
    zof_l = np.array([zone_names_l[i] for i in fl["zone_idx"]], dtype=object)
    dom_l = ~np.isin(zof_l, list(C244.CORRIDOR_LANDING))
    wedge_vals: list[np.ndarray] = []
    wedge_wts: list[np.ndarray] = []
    for zi, z in enumerate(CA_ZONES):
        sel_h = (labels[z] == "STORAGE") & ok
        if not sel_h.any():
            continue
        in_z = dom_l & (zof_l == z)
        if not in_z.any():
            continue
        lam_z = price.loc[z].to_numpy(float)
        offers = np.where(fl["avail"][in_z] > 0.01, fl["mc"][in_z], np.nan)
        d = offers - lam_z[None, :]
        near = np.nanmin(np.abs(d), axis=0)
        idx = np.nanargmin(np.abs(d), axis=0)
        signed = d[idx, np.arange(HOURS)]
        wedge_vals.append(signed[sel_h])
        wedge_wts.append((w * share[zi])[sel_h])
    if wedge_vals:
        wv = np.concatenate(wedge_vals)
        ww = np.concatenate(wedge_wts)
        finite = np.isfinite(wv)
        wv, ww = wv[finite], ww[finite]
        order_i = np.argsort(wv)
        cw = np.cumsum(ww[order_i]) / max(ww.sum(), 1e-9)
        q = lambda f: float(wv[order_i][np.searchsorted(cw, f)])  # noqa: E731
        storage_wedge = {
            "definition": "nearest available OWN-ZONE domestic offer minus lambda_z, in STORAGE zone-hours, load-weighted",
            "p10": round(q(0.10), 3),
            "p25": round(q(0.25), 3),
            "median": round(q(0.50), 3),
            "p75": round(q(0.75), 3),
            "p90": round(q(0.90), 3),
            "share_offer_above_lambda": round(float(ww[wv > 0].sum() / ww.sum()), 4),
            "share_within_0_75": round(float(ww[np.abs(wv) <= 0.75].sum() / ww.sum()), 4),
        }
    else:
        storage_wedge = None

    month_regime = {}
    for m in range(1, 13):
        hm = MONTH == m
        month_regime[m] = {
            r: round(float(contrib[r][hm].sum()) / denom, 4) for r in REGIMES
        }
        month_regime[m]["_month_gap_usd_per_mwh"] = round(
            float(sum(contrib[r][hm].sum() for r in REGIMES)) / denom, 4
        )

    bench = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"))
    rt_lw = float((a[ok] * w[ok]).sum() / denom)
    return {
        "keeper_run_id": KEEPER_RUN_ID,
        "tol": tol,
        "hub_first": hub_first,
        "G_FLEET": g_fleet,
        "G_CONSERVE": {
            "gap_hourly": round(gap_hourly, 4),
            "cells_sum": round(tot, 4),
            "max_abs_deviation": round(abs(tot - gap_hourly), 12),
            "caiso248_published_gap": CAISO248_GAP[year],
            "pass": bool(
                abs(tot - gap_hourly) < 1e-9
                and abs(gap_hourly - CAISO248_GAP[year]) <= 5e-4
            ),
        },
        "G_BENCH": {
            "recomputed_rt_lw": round(rt_lw, 4),
            "committed_rt_lw": bench["bench"]["avgLMP"]["rt_lw"],
            "pass": bool(abs(rt_lw - float(bench["bench"]["avgLMP"]["rt_lw"])) <= 0.01),
        },
        "G_RECON": {"basis": recon["basis_selected"], "pass": recon["G_RECON_pass"]},
        "G_DF": {
            **df_material,
            "share_raw_outside_tol": (
                round(df_material["raw_outside_tol"] / df_material["df_import_zonehours"], 4)
                if df_material["df_import_zonehours"]
                else None
            ),
            "pass": bool(
                df_material["df_import_zonehours"] > 0
                and df_material["raw_outside_tol"] / df_material["df_import_zonehours"] >= 0.60
            ),
        },
        "by_regime": by_regime,
        "families_own_zone": families,
        "storage_cell_wedge_POST_REGISTRATION": storage_wedge,
        "month_regime": month_regime,
        "hub_total": {
            "weight_share": round(
                by_regime["HUB_FITTED"]["weight_share"]
                + by_regime["HUB_MEASURED"]["weight_share"],
                4,
            ),
            "gap_share": round(
                (by_regime["HUB_FITTED"]["gap_share"] or 0.0)
                + (by_regime["HUB_MEASURED"]["gap_share"] or 0.0),
                4,
            ),
        },
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-249 (own-zone + delivery-factor attribution, ZERO LP)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": KEEPER_RUN_ID,
            "precommit": "PRECOMMIT-caiso249-ownzone-loss-adjusted-attribution-2026-09-05.md",
            "instrument": (
                "own-zone complementarity (exact) + the build_caiso_link_loss "
                "delivery-factor ratio from the measured CAISO_loss_surface.csv; "
                "gap decomposition unchanged (caiso-131/140 common-weight convention)"
            ),
            "fleet": "replay_keeper.run_year_kwargs + derived_run_year_inputs (caiso-248 repair)",
            "tol_usd_mwh": TOL,
            "note": "NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG.",
        },
        "years": {},
    }
    for y in YEARS:
        primary = analyse(y)
        hubfirst = analyse(y, hub_first=True)
        sens = analyse(y, tol=TOL_SENS)
        primary["G_ORDER_hub_first"] = {
            "hub_gap_share": hubfirst["hub_total"]["gap_share"],
            "hub_weight_share": hubfirst["hub_total"]["weight_share"],
            "hub_CR": (
                round(
                    hubfirst["hub_total"]["gap_share"]
                    / max(hubfirst["hub_total"]["weight_share"], 1e-9),
                    3,
                )
            ),
            "by_regime": hubfirst["by_regime"],
        }
        primary["SENSITIVITY_tol075"] = sens["by_regime"]
        out["years"][y] = primary
        b = primary["by_regime"]
        print(f"\n===== {y} =====")
        print(
            f"  G-FLEET {primary['G_FLEET']['pass']} (missing {primary['G_FLEET']['sidecar_classes_with_no_lp_units']}, "
            f"phantom {primary['G_FLEET']['phantom_families_of_injected_classes']})"
        )
        print(
            f"  G-CONSERVE {primary['G_CONSERVE']['pass']} (cells {primary['G_CONSERVE']['cells_sum']} vs "
            f"gap {primary['G_CONSERVE']['gap_hourly']} vs caiso-248 {primary['G_CONSERVE']['caiso248_published_gap']})"
            f"; G-BENCH {primary['G_BENCH']['pass']}; G-RECON {primary['G_RECON']['pass']}"
        )
        print(f"  G-DF {primary['G_DF']['pass']} {primary['G_DF']}")
        print(f"  {'regime':14s} {'w':>7s} {'gap$':>8s} {'share':>7s} {'CR':>6s} {'resid':>8s}")
        for r in REGIMES:
            v = b[r]
            print(
                f"  {r:14s} {v['weight_share']:7.3f} {v['gap_contribution_usd_per_mwh']:8.3f} "
                f"{(v['gap_share'] if v['gap_share'] is not None else float('nan')):7.3f} "
                f"{(v['CR'] if v['CR'] is not None else float('nan')):6.2f} "
                f"{(v['mean_residual_usd_per_mwh'] if v['mean_residual_usd_per_mwh'] is not None else float('nan')):8.2f}"
            )
        print(f"  HUB {primary['hub_total']}; HUB-first {primary['G_ORDER_hub_first']['hub_gap_share']} "
              f"(CR {primary['G_ORDER_hub_first']['hub_CR']})")
        print("  STORAGE wedge (post-registration):", primary["storage_cell_wedge_POST_REGISTRATION"])
        print("  families (own-zone):", {k: v["mean_residual_usd_per_mwh"] for k, v in list(primary["families_own_zone"].items())[:7]})
        print("  tol=0.75 shares:", {r: sens["by_regime"][r]["gap_share"] for r in REGIMES})
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
