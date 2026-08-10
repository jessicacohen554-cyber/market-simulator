"""miso-149 G-1/G-2/G-4 — the overlay-vs-CEMS contradiction census. **NO LP.**

Adjudicates PREREG ``results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md``
(pushed at ``318c0542``, blob verified against the fetched remote ref, BEFORE this
script was written).

The one sign-definite question, at plant-hour grain, for the CURRENT keeper
``miso148_basis_B``::

    C_ph = model NET capability of plant p, hour h  = sum_g in (p,F) pmax_g * availability_g[h]
    A_ph = CAMPD observed NET output of plant p, h  = gross_ph * parasitic_p
    contradiction_ph = max(0, A_ph - C_ph)

i.e. capacity-hours in which the model asserts an incapability the plant's own
CEMS record refutes.  CEMS enters ONLY as a lower bound on an availability
INPUT ("a plant that generated X was capable of at least X") -- never as a
dispatch target, never as a pin (rule 13 ``[R-MEASURED]``).

G-2 attributes the census to the availability stack's own layers.  In a historic
backcast ``data.fleet.arrays`` builds

    availability = stat  x  ufac(>=5-day)  x  sfac(short, coal-only)  x  mgfac(maxgen events)

multiplicatively and in that order, so with the three overlay dicts read back
through the SHIPPED loaders (same arguments the fleet build passes) the
statistical layer is recoverable by division, and every counterfactual is an
exact product.  T-EXACT verifies the reconstruction against the fleet's own
availability array before any attribution is reported.

G-4 splits May-2025's CC availability deficit between the 2025 EIA-860 vintage
under-carry (the cross-ISO defect, reported not repaired at miso-148) and the
overlay.

Writes ``results/calibration/_miso149_overlay.json``.

Usage::

    python scripts/probes/_miso149_overlay.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for _i, _p in enumerate((REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes")):
    sys.path.insert(_i, str(_p))

# The miso-149 fleet pack must NOT collide with the miso-147 footing cache: that
# one is keyed by year alone and is built against the PREVIOUS keeper.
os.environ.setdefault("MISO149_CACHE", str(Path("/tmp") / "_miso149_cache"))

import _miso143_stack as stack  # noqa: E402
from _miso147_strata import (  # noqa: E402
    FAMILY_TO_KLASSES,
    HOURS,
    YEARS,
    campd_units,
    fam_of_klass,
    parasitic_map,
    strata,
)
from _miso143_stack import hygiene, klass_of, month_of_hour  # noqa: E402

#: PREREG §2 — the CURRENT keeper (miso-148), not the miso-147 footing target.
KEEPER149 = REPO / "results" / "calibration" / "miso148_basis_B"
OUT = REPO / "results" / "calibration" / "_miso149_overlay.json"

#: PREREG §3 G-1 — the materiality bar, fixed before any value existed.
KCC_BAR_MW = 500.0
NONSUMMER_MONTH_BAR_MW = 300.0
LAYER_OWN_SHARE = 0.60

#: PREREG §3 G-2 — the classes whose statistical POF is dropped in the historic
#: backcast and the only ones eligible for a WEFOR-residual relief.
POF_DROP_GROUPS = frozenset({"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"})

#: PREREG §3 G-4(a) — the 9 EIA-860 rows OP in vintage_2024 and dropped in 2025
#: (miso-148 §3.1 / ``_miso148_admission.json``).  Read, never re-derived.
OA_DROPPED_PLANTS = {941: 2.8, 7474: 2.0, 10234: 12.5, 55358: 576.2, 58330: 1.2}

SUMMER_MONTHS = (6, 7, 8, 9)


def _cache() -> Path:
    d = Path(os.environ["MISO149_CACHE"])
    d.mkdir(parents=True, exist_ok=True)
    return d


# --------------------------------------------------------------------------- #
# Model side — the keeper's own fleet, WITHOUT a solve
# --------------------------------------------------------------------------- #
def fleet149(year: int) -> dict:
    """Per-generator pack for the CURRENT keeper: plant, group, pmax, availability.

    ``stack.fleet_state`` reads its keeper from the module global, so the global
    is re-pointed for the call and restored afterwards -- the shared miso-143/147
    modules keep their own keeper, so the footing reproduction stays valid.
    """
    p = _cache() / f"fleet149_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in z.files}
    prev = stack.KEEPER
    stack.KEEPER = KEEPER149
    try:
        st = stack.fleet_state(year)
    finally:
        stack.KEEPER = prev
    gens, fa = st["fleet"], st["fleet_arrays"]
    pack = {
        "plant": np.array([int(g.plant_code) for g in gens], dtype=np.int64),
        "group": np.array([str(g.plant_group) for g in gens], dtype=object),
        "zone": np.array([str(g.zone) for g in gens], dtype=object),
        "klass": klass_of(gens).astype(str),
        "pmax": np.asarray(fa.pmax, dtype=np.float64),
        "availability": np.asarray(fa.availability, dtype=np.float32),
        # G-3 needs the offer side too; built here so both miso-149 probes share
        # ONE fleet build per year (rule 12 -- no duplicated multi-GB work).
        "mc_base": np.asarray(st["mc_base"], dtype=np.float32),
        "markup": np.asarray(
            stack.markup_ceiling(gens, fa, st["config"]), dtype=np.float64
        ),
    }
    np.savez_compressed(p, **pack)
    return pack


def overlay_layers(year: int) -> dict[str, dict[tuple[int, str], np.ndarray]]:
    """The three shipped overlay dicts, with the keeper's own arguments.

    Read through ``data.outages`` -- never re-implemented -- so what is measured
    is the overlay the LP actually applies.  ``unit_partial_outage_windows`` is
    OFF on this keeper and is therefore absent by construction.
    """
    from market_sim.config.paths import CAMPD_BINS_CSV
    from market_sim.data.outages import (
        unit_outage_derate_factors,
        unit_outage_maxgen_derate_factors,
        unit_outage_short_derate_factors,
    )

    meta = json.loads((KEEPER149 / "meta.json").read_text())
    ovr = meta.get("coal_prb_sigmoid_overrides", {}) or {}
    bins = meta.get("campd_bins_path", str(CAMPD_BINS_CSV))
    reclass = bool(meta.get("cc_steam_part_reclass", ovr.get("cc_steam_part_reclass", False)))
    npbasis = bool(meta.get("unit_outage_lp_capacity_basis") or False)
    out: dict[str, dict] = {
        "ufac": unit_outage_derate_factors(
            year, HOURS, bins, iso="MISO",
            cc_steam_part_reclass=reclass, cc_nameplate_basis=npbasis,
        )
    }
    out["sfac"] = (
        unit_outage_short_derate_factors(
            year, HOURS, bins, iso="MISO",
            cc_steam_part_reclass=reclass, cc_nameplate_basis=npbasis,
        )
        if ovr.get("unit_outage_short_windows") or meta.get("unit_outage_short_windows")
        else {}
    )
    out["mgfac"] = (
        unit_outage_maxgen_derate_factors(
            year, HOURS, iso="MISO",
            cc_steam_part_reclass=reclass, cc_nameplate_basis=npbasis,
        )
        if ovr.get("unit_outage_maxgen_events") or meta.get("unit_outage_maxgen_events")
        else {}
    )
    return out


def layer_matrix(pack: dict, layers: dict) -> dict[str, np.ndarray]:
    """Expand each overlay dict onto the (n_gen, HOURS) generator grid."""
    n = pack["plant"].size
    out = {}
    for name, d in layers.items():
        m = np.ones((n, HOURS), dtype=np.float32)
        if d:
            for g in range(n):
                f = d.get((int(pack["plant"][g]), str(pack["group"][g])))
                if f is not None:
                    m[g, :] = f
        out[name] = m
    return out


def decompose(pack: dict, lay: dict) -> tuple[np.ndarray, dict]:
    """Recover the statistical layer ``stat`` with ``availability = stat * u*s*m``.

    Exact by division wherever the overlay product is > 0.  Where the product is
    0 the availability array carries no information about ``stat``, so the cell
    takes that generator-month's own constant (the statistical layer is a
    seasonal/age function, constant within a month for every class this census
    reads).  T-EXACT reports both the within-(gen, month) constancy and the share
    of cells that needed the fallback, so the reconstruction is auditable rather
    than assumed.
    """
    avail = pack["availability"].astype(np.float64)
    prod = (lay["ufac"] * lay["sfac"] * lay["mgfac"]).astype(np.float64)
    pos = prod > 1e-12
    stat = np.zeros_like(avail)
    np.divide(avail, prod, out=stat, where=pos)

    mon = month_of_hour(np.arange(HOURS))
    n_fallback = 0
    cv_max = 0.0
    n_cells = 0
    for m in range(1, 13):
        hm = mon == m
        sub_pos = pos[:, hm]
        sub_stat = stat[:, hm]
        any_pos = sub_pos.any(axis=1)
        # within-(gen, month) constancy of the recovered statistical layer
        with np.errstate(invalid="ignore"):
            s = np.where(sub_pos, sub_stat, np.nan)
            mu = np.nanmean(s, axis=1)
            sd = np.nanstd(s, axis=1)
        ok = any_pos & (mu > 1e-9)
        if ok.any():
            cv_max = max(cv_max, float(np.nanmax(sd[ok] / mu[ok])))
            n_cells += int(ok.sum())
        fill = np.where(any_pos, np.nan_to_num(mu), np.nan)
        need = (~sub_pos) & np.isfinite(fill)[:, None]
        if need.any():
            n_fallback += int(need.sum())
            sub_stat = np.where(need, np.broadcast_to(fill[:, None], sub_stat.shape), sub_stat)
            stat[:, hm] = sub_stat
    # generators with no positive-product hour anywhere: annual median fallback
    dead = ~pos.any(axis=1)
    if dead.any():
        stat[dead, :] = 0.0
    recon = stat * prod
    t_exact = {
        "max_abs_recon_err": float(np.max(np.abs(recon - avail))),
        "max_within_gen_month_cv": cv_max,
        "n_gen_month_cells": n_cells,
        "n_fallback_cells": n_fallback,
        "frac_fallback_cells": float(n_fallback / max(1, avail.size)),
        "n_gen_zero_product_all_year": int(dead.sum()),
    }
    return stat, t_exact


# --------------------------------------------------------------------------- #
# CAMPD side
# --------------------------------------------------------------------------- #
def campd_plant_hour(year: int) -> tuple[dict[str, dict[int, np.ndarray]], dict]:
    """{family: {plant_id: (8760,) NET MW}} plus the universe metadata."""
    units, meta = campd_units(year)
    fac = parasitic_map()
    out: dict[str, dict[int, np.ndarray]] = {f: {} for f in FAMILY_TO_KLASSES}
    for (fam, pid), g in units.groupby(["family", "plant_id"], sort=False):
        arr = np.zeros(HOURS)
        np.add.at(arr, g["hoy"].to_numpy(int), g["gross"].to_numpy(float))
        out[str(fam)][int(pid)] = arr * float(fac.get(int(pid), 1.0))
    return out, meta


def model_plant_hour(pack: dict, cap: np.ndarray) -> dict[str, dict[int, np.ndarray]]:
    """{family: {plant_id: (8760,) NET capability MW}} for a capability array."""
    fmap = fam_of_klass()
    out: dict[str, dict[int, np.ndarray]] = {f: {} for f in FAMILY_TO_KLASSES}
    fam_of_gen = np.array([fmap.get(str(k), "") for k in pack["klass"]], dtype=object)
    for fam in FAMILY_TO_KLASSES:
        sel = np.flatnonzero(fam_of_gen == fam)
        if sel.size == 0:
            continue
        d: dict[int, np.ndarray] = {}
        for g in sel:
            pid = int(pack["plant"][g])
            v = d.get(pid)
            d[pid] = cap[g] if v is None else v + cap[g]
        out[fam] = d
    return out


# --------------------------------------------------------------------------- #
# The census
# --------------------------------------------------------------------------- #
def census(
    model: dict[str, dict[int, np.ndarray]],
    obs: dict[str, dict[int, np.ndarray]],
    fam: str,
    shift: int = 0,
) -> dict:
    """max(0, A - C) over the plants present on BOTH sides, in MW-hours."""
    mp, op = model.get(fam, {}), obs.get(fam, {})
    both = sorted(set(mp) & set(op))
    contrib = np.zeros(HOURS)
    per_plant: dict[int, float] = {}
    n_hours_hit = 0
    for pid in both:
        a = op[pid]
        if shift:
            a = np.roll(a, shift)
        c = mp[pid]
        d = np.maximum(0.0, a - c)
        contrib += d
        s = float(d.mean())
        if s > 0:
            per_plant[pid] = s
            n_hours_hit += int((d > 0).sum())
    return {
        "mean_mw": float(contrib.mean()),
        "series": contrib,
        "n_plants_both": len(both),
        "n_plants_contradicted": len(per_plant),
        "n_plant_hours": n_hours_hit,
        "model_only_plants": sorted(set(mp) - set(op)),
        "campd_only_plants": sorted(set(op) - set(mp)),
        "top_plants": sorted(per_plant.items(), key=lambda kv: -kv[1])[:12],
    }


def monthly(series: np.ndarray) -> list[float]:
    mon = month_of_hour(np.arange(HOURS))
    return [round(float(series[mon == m].mean()), 1) for m in range(1, 13)]


def run() -> dict:
    hygiene()
    # Every NEW miso-149 measurement reads the CURRENT keeper. The shared
    # miso-143 module's global is the single source of that path for
    # fleet_state / sidecar_price / sidecar_classes, so it is re-pointed once,
    # here, AFTER the miso-147 footing reproduction has already run against the
    # keeper those probes were written for (PREREG §2).
    stack.KEEPER = KEEPER149
    res: dict = {
        "session": "miso-149",
        "prereg": "results/calibration/PREREG-miso149-overlay-contradiction-2026-08-10.md",
        "prereg_commit": "318c0542",
        "keeper": "2026-08-09-miso-148-basis-aware",
        "keeper_bundle": str(KEEPER149.relative_to(REPO)),
        "years": {},
    }
    for year in YEARS:
        pack = fleet149(year)
        layers = overlay_layers(year)
        lay = layer_matrix(pack, layers)
        stat, t_exact = decompose(pack, lay)
        pmax = pack["pmax"][:, None]

        obs, campd_meta = campd_plant_hour(year)
        st = strata(year)

        # --- capability variants (PREREG G-2) --------------------------------
        # Built LAZILY, one at a time: each is (n_gen, 8760) float64 and holding
        # five at once needs several GB for no reason.
        variants = {
            "keeper": lambda: stat * lay["ufac"] * lay["sfac"] * lay["mgfac"],
            "no_ufac": lambda: stat * lay["sfac"] * lay["mgfac"],
            "no_sfac": lambda: stat * lay["ufac"] * lay["mgfac"],
            "no_mgfac": lambda: stat * lay["ufac"] * lay["sfac"],
            "stat_only": lambda: stat.copy(),
        }
        yr: dict = {
            "T_EXACT": t_exact,
            "campd_meta": campd_meta,
            "S1_threshold_usd": st["S1_thr_usd"],
            "overlay_rows": {k: len(v) for k, v in layers.items()},
            "families": {},
            "G2_layer_attribution": {},
        }
        base_model = None
        keeper_cap = None
        for name, make in variants.items():
            mult = make()
            if name == "keeper":
                keeper_cap = pmax * mult
                mdl = model_plant_hour(pack, keeper_cap)
            else:
                mdl = model_plant_hour(pack, pmax * mult)
            del mult
            if name == "keeper":
                base_model = mdl
            for fam in ("CC", "CT", "ST_GAS", "ST_COAL"):
                c = census(mdl, obs, fam)
                row = {
                    "mean_mw": round(c["mean_mw"], 1),
                    "monthly_mw": monthly(c["series"]),
                    "S1_mean_mw": round(float(c["series"][st["masks"]["S1"]].mean()), 1),
                    "n_plants_both": c["n_plants_both"],
                    "n_plants_contradicted": c["n_plants_contradicted"],
                    "n_plant_hours": c["n_plant_hours"],
                }
                if name == "keeper":
                    row["top_plants"] = [[int(p), round(v, 1)] for p, v in c["top_plants"]]
                    row["model_only_plants"] = c["model_only_plants"][:40]
                    row["campd_only_plants"] = c["campd_only_plants"][:40]
                    row["n_model_only"] = len(c["model_only_plants"])
                    row["n_campd_only"] = len(c["campd_only_plants"])
                    yr["families"][fam] = row
                else:
                    yr["G2_layer_attribution"].setdefault(fam, {})[name] = {
                        "mean_mw": row["mean_mw"],
                        "monthly_mw": row["monthly_mw"],
                    }
            del mdl

        # --- TRAP 1 (gross basis) and TRAP 4 (+-1 h alignment) ---------------
        units, _ = campd_units(year)
        gross: dict[str, dict[int, np.ndarray]] = {f: {} for f in FAMILY_TO_KLASSES}
        for (fam, pid), g in units.groupby(["family", "plant_id"], sort=False):
            arr = np.zeros(HOURS)
            np.add.at(arr, g["hoy"].to_numpy(int), g["gross"].to_numpy(float))
            gross[str(fam)][int(pid)] = arr
        yr["TRAP1_gross_basis_CC_mean_mw"] = round(census(base_model, gross, "CC")["mean_mw"], 1)
        yr["TRAP4_shift"] = {
            str(s): round(census(base_model, obs, "CC", shift=s)["mean_mw"], 1)
            for s in (-1, 0, 1)
        }
        # TRAP 3 — CC_REGULAR alone (the CHP boundary held out)
        reg_model: dict[str, dict[int, np.ndarray]] = {"CC": {}}
        keep = np.flatnonzero(np.array([str(k) == "CC_REGULAR" for k in pack["klass"]]))
        for g in keep:
            pid = int(pack["plant"][g])
            v = reg_model["CC"].get(pid)
            add = keeper_cap[g]
            reg_model["CC"][pid] = add if v is None else v + add
        yr["TRAP3_cc_regular_only_mean_mw"] = round(census(reg_model, obs, "CC")["mean_mw"], 1)

        # --- G-2 W_c vs X_c (the caiso-187 frozen formula, MISO's own fleet) --
        prod = (lay["ufac"] * lay["sfac"] * lay["mgfac"]).astype(np.float64)
        wx = {}
        for grp in sorted(POF_DROP_GROUPS | {"COAL"}):
            sel = np.flatnonzero(np.array([str(g) == grp for g in pack["group"]]))
            if sel.size == 0:
                continue
            w = pack["pmax"][sel]
            tot = float(w.sum())
            if tot <= 0:
                continue
            W_c = 1.0 - float((w * stat[sel].mean(axis=1)).sum() / tot)
            X_c = 1.0 - float((w * prod[sel].mean(axis=1)).sum() / tot)
            wx[grp] = {
                "fleet_mw": round(tot, 1),
                "W_c": round(W_c, 4),
                "X_c": round(X_c, 4),
                "residual_c": round(max(0.0, W_c - X_c), 4),
                "X_over_W": round(X_c / W_c, 2) if W_c > 1e-9 else None,
            }
        yr["G2_W_vs_X"] = wx

        # --- G-4 the May split ----------------------------------------------
        mon = month_of_hour(np.arange(HOURS))
        may = mon == 5
        oa_may = 0.0
        for pid in OA_DROPPED_PLANTS:
            for fam in obs:
                if pid in obs[fam]:
                    oa_may += float(obs[fam][pid][may].mean())
        yr["G4_may"] = {
            "oa_dropped_plants_may_cems_net_mw": round(oa_may, 1),
            "oa_dropped_plants_may_cems_by_plant": {
                str(pid): round(
                    sum(float(obs[f][pid][may].mean()) for f in obs if pid in obs[f]), 1
                )
                for pid in OA_DROPPED_PLANTS
            },
            "overlay_contradiction_may_cc_mw": yr["families"]["CC"]["monthly_mw"][4],
            "oa_rows_nameplate_mw": round(sum(OA_DROPPED_PLANTS.values()), 1),
        }
        res["years"][str(year)] = yr
        # release the (n_gen, 8760) arrays; rebound rather than `del`ed so the
        # closures above stay statically resolvable.
        pack = lay = stat = variants = obs = base_model = keeper_cap = None

    # --- verdicts ---------------------------------------------------------- #
    cc25 = res["years"]["2025"]["families"]["CC"]
    kcc = cc25["mean_mw"]
    nonsummer = [
        v for i, v in enumerate(cc25["monthly_mw"], start=1) if i not in SUMMER_MONTHS
    ]
    n_ns = sum(1 for v in nonsummer if v >= NONSUMMER_MONTH_BAR_MW)
    if kcc < KCC_BAR_MW:
        g1 = "B-2 immaterial"
    elif n_ns >= 4:
        g1 = "B-1 overlay_over_removal"
    else:
        g1 = "B-3 summer_only"
    res["G1_verdict"] = {
        "branch": g1,
        "Kcc_2025_mean_mw": kcc,
        "bar_mw": KCC_BAR_MW,
        "n_nonsummer_months_ge_300mw": n_ns,
        "monthly_mw_2025": cc25["monthly_mw"],
    }

    att = res["years"]["2025"]["G2_layer_attribution"].get("CC", {})
    owns = {k: round((kcc - v["mean_mw"]) / kcc, 3) if kcc > 0 else None
            for k, v in att.items() if k != "stat_only"}
    owns["stat_only"] = (
        round((kcc - att["stat_only"]["mean_mw"]) / kcc, 3)
        if kcc > 0 and "stat_only" in att else None
    )
    single = [k for k, v in owns.items()
              if k != "stat_only" and v is not None and v >= LAYER_OWN_SHARE]
    res["G2_verdict"] = {
        "share_of_Kcc_removed_by_dropping_layer": owns,
        "single_layer_owner": single[0] if len(single) == 1 else None,
        "bar": LAYER_OWN_SHARE,
    }

    g4 = res["years"]["2025"]["G4_may"]
    deficit = 1201.0  # miso-147 committed May-2025 AV_CC - A_CC, cited not re-derived
    a = g4["oa_dropped_plants_may_cems_net_mw"] / deficit
    b = g4["overlay_contradiction_may_cc_mw"] / deficit
    res["G4_verdict"] = {
        "may2025_AV_minus_A_cited_mw": deficit,
        "share_a_vintage_undercarry": round(a, 3),
        "share_b_overlay": round(b, 3),
        "branch": (
            "M-1 vintage_blocked" if a >= 0.40
            else "M-2 overlay_may" if b >= 0.40
            else "M-3 open"
        ),
    }
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    return res


if __name__ == "__main__":
    r = run()
    print("G-1", r["G1_verdict"]["branch"], "Kcc(2025) =", r["G1_verdict"]["Kcc_2025_mean_mw"], "MW")
    print("     monthly", r["G1_verdict"]["monthly_mw_2025"])
    print("G-2 owner:", r["G2_verdict"]["single_layer_owner"], r["G2_verdict"]["share_of_Kcc_removed_by_dropping_layer"])
    print("G-2 W vs X 2025:", json.dumps(r["years"]["2025"]["G2_W_vs_X"]))
    print("G-4", r["G4_verdict"]["branch"], r["G4_verdict"])
    for y in ("2023", "2024", "2025"):
        print(y, "T-EXACT", r["years"][y]["T_EXACT"])
    print("->", OUT)
