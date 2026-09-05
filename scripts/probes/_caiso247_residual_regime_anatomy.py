"""caiso-247 — PHASE-0 RESIDUAL ANATOMY: what price-formation regime carries the C3a gap? ZERO LP.

Pre-registered in ``PRECOMMIT-caiso247-residual-regime-anatomy-2026-09-05.md``
(pushed to ``origin`` before this file was written and before any cell of the
object was computed). **NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG.**

The question (PRECOMMIT §0.1): C3a is the CAISO lane's sole load-bearing
failure and its carrier has never been attributed by *price-formation regime*
over a whole year. Two readings compete — the **hub-basis** reading
(caiso-244 §3.6: an import row IS the NP15 / SP15_rest price in 18–23 % of
hours, so a residual there is a hub-basis residual) and the **domestic offer
surface** reading (caiso-242 §2.4 / caiso-243 P-5 / caiso-246 §3). This probe
measures the split; it does not adjudicate by arming anything.

Instrument (PRECOMMIT §1.1–§1.2), all from committed bytes:

* the **caiso-244 dual-merit reconstruction**, imported verbatim and
  re-pointed at the caiso-246 keeper bundle: the fleet is rebuilt on-recipe
  (``replay_keeper.run_year_kwargs``, ``fleet_only=True`` — no LP) and every
  import row's state comes from LP complementarity against the keeper's
  committed P1 zonal duals;
* the gap is decomposed over **zone-hours** on the caiso-131 §2 / caiso-140 §A
  common-weight convention — the rubric's own ``rt_lw`` weights (measured
  system load) applied to BOTH sides — so the cells sum exactly to
  ``gap_hourly``;
* the comparator is the committed hourly actual RT LMP
  (``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``), the same
  series ``avgLMP.rt_lw`` is built from. It is used to ATTRIBUTE a residual,
  never to close one (PRECOMMIT §0.3).

Regime taxonomy, frozen in PRECOMMIT §1.3 before any measurement, one label
per zone-hour in priority order: HUB_FITTED, HUB_MEASURED, DOM_GAS, DOM_OTHER,
STORAGE, SURPLUS, UNRESOLVED. The headline statistic is the scale-free
**concentration ratio** CR(R) = (share of gap) / (share of weight): CR = 1
means the regime is not a carrier, only where the hours are.

Gates: G-RECON, G-GAP, G-CLASS, G-ORDER, G-BENCH (PRECOMMIT §1.4).

Writes ``results/calibration/_caiso247_residual_regime_anatomy.json``.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso247_residual_regime_anatomy.py
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
    "_caiso244_import_level_anatomy",
    REPO / "scripts/probes/_caiso244_import_level_anatomy.py",
)
C244 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(C244)

#: THE NEW KEEPER (caiso-246). The caiso-244 module points at its own keeper;
#: re-pointing the module-level constant is what makes the imported
#: ``rebuild`` / ``sidecars`` read this bundle (PRECOMMIT §1.1).
BUNDLE = REPO / "results/calibration/caiso246_b1_spot_coverage"
C244.BUNDLE = BUNDLE
KEEPER_RUN_ID = "2026-09-05-caiso-246-b1-spot"

OUT = REPO / "results/calibration/_caiso247_residual_regime_anatomy.json"
BENCH = REPO / "frontend/data/backcast/bench/CAISO"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
YEARS = (2023, 2024, 2025)
HOURS = C244.HOURS
MONTH = C244.MONTH_OF_HOUR
TOL = C244.TOL  # 0.05 $/MWh, the caiso-244 value — reported, not tuned
#: Declared robustness variant only (never re-frozen): caiso-202 §C's own
#: nearest-rung tolerance, wide enough to absorb the zonal loss surface.
TOL_SENS = 0.75
#: The five CAISO load zones (the WECC corridor nodes carry no load).
CA_ZONES = ("NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest")
#: The two FITTED firm import rows (caiso-83/86 Q-Q derivation; $28 / $48).
FITTED_ROWS = ("PNW_hydro_base", "DSW_solar_PV")
GAS_GROUPS = C244.GAS_GROUPS
REGIMES = (
    "HUB_FITTED",
    "HUB_MEASURED",
    "DOM_GAS",
    "DOM_OTHER",
    "STORAGE",
    "SURPLUS",
    "UNRESOLVED",
)


def injected_mustrun_classes(year: int) -> set[str]:
    """Classes the SOLVE injected as a must-run profile, read off the sidecar.

    THE caiso-248 DEFECT REPAIR. ``run_calibration_full`` nets the residual
    must-run classes (``_INJECTED_MUSTRUN_CLASSES = ("biomass", "OTHER")``) out
    of demand, re-adds them as pseudo-units, and — for biomass alone — passes
    ``inject_biomass_mustrun`` into ``run_year``, which DROPS the raw biomass LP
    units so they are not served twice. That flag is derived from
    ``solve_and_persist``'s own locals, so it is **not recorded in meta.json**
    and ``replay_keeper.run_year_kwargs`` cannot carry it: a fleet-only rebuild
    silently keeps 184 CAISO biomass units the scored solve does not have.
    caiso-247 measured its DOM_OTHER cell on exactly those phantom units.

    An injected class is EXACTLY flat within every calendar month (the profile
    is annual EIA-923 energy shaped by a monthly vector, flat inside a month),
    which is the signature this reads — the same evidence caiso-202's probe
    cites for the same conclusion. Detection from committed bytes, no meta key.
    """
    c = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    out: set[str] = set()
    for klass, grp in c.groupby("klass", observed=True):
        mw = np.zeros(HOURS)
        hr = grp["hour"].to_numpy(int)
        ok = hr < HOURS
        mw[hr[ok]] = grp["mw"].to_numpy(float)[ok]
        if mw.sum() <= 0:
            continue
        # CALENDAR-AGNOSTIC on purpose: ``run_calibration_full._hour_months``
        # builds its month map from the REAL calendar, so in a leap year the
        # injected steps sit on 8784-clock boundaries (2024 biomass steps at
        # hour 1440 = 31 d + 29 d) while every array here is on the non-leap
        # 8760 clock. Testing "flat within MY months" therefore MISSES 2024.
        # A monthly step profile is instead identified by its shape: at most
        # 12 distinct levels joined by at most 11 change points.
        vals = np.round(mw, 6)
        if len(np.unique(vals)) <= 12 and int((np.diff(vals) != 0).sum()) <= 11:
            out.add(str(klass))
    return out


def rebuild_full(year: int) -> dict:
    """The caiso-244 on-recipe fleet rebuild, plus the DOMESTIC arrays it drops.

    ``_caiso244_import_level_anatomy.rebuild`` keeps only the import rows'
    arrays; this probe also needs every unit's zone index and plant group to
    price-match the DOMESTIC side. Rather than edit a committed evidence
    probe, this reproduces its rebuild through the same sanctioned recipe path
    (``replay_keeper.run_year_kwargs`` — never by parameter name, caiso-243
    §10.4 / caiso-244 §7.7) and returns a SUPERSET of the dict
    ``C244.reconstruct`` consumes, so the reconstruction itself stays verbatim.
    NO LP: ``fleet_only=True``.
    """
    import contextlib
    import io

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub
    from run_calibration import run_year
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    # The one recipe input meta.json does not record (see
    # :func:`injected_mustrun_classes`). Recovered from the committed sidecar
    # so the rebuilt fleet is the fleet the scored solve actually dispatched.
    injected = injected_mustrun_classes(year)
    # The shared helper is the authority (caiso-248 added it to replay_keeper so
    # every ISO's fleet-only probes stop rebuilding phantom biomass units); the
    # local detector above is kept only to report WHICH classes were injected.
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
    avail = np.asarray(fa.availability, dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    pmin = np.asarray(fa.pmin, dtype=float)
    mg = fa.min_gen
    if mg is None:
        mg = np.broadcast_to(pmin[:, None], (pmin.size, HOURS))
    mg = np.asarray(mg, dtype=float)
    uid = np.array([str(u) for u in fa.unit_ids], dtype=object)
    # 213 CAISO units carry no ``plant_group`` (biomass / oil / nuclear); keying
    # them by ``fuel_type`` is what makes the DOM_OTHER regime nameable.
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
        "avail": avail,
        "pmax": pmax,
        "pmin": pmin,
        "min_gen": mg,
        "zone_idx": zidx,
        "group": group,
        "zone_names": zone_names,
        "injected_mustrun_classes": sorted(injected),
        "log": buf.getvalue(),
    }


def actual_rt(year: int) -> np.ndarray:
    """Committed hourly actual RT LMP on the 8760 model clock (NaN where absent)."""
    h = pd.read_parquet(ACTUAL)
    h = h[h["year"] == int(year)]
    dense = np.full(HOURS, np.nan)
    hr = h["hour"].to_numpy(int)
    ok = hr < HOURS
    dense[hr[ok]] = h["rt"].to_numpy(float)[ok]
    return dense


def rubric_weights(year: int) -> np.ndarray:
    """The rubric's ``rt_lw`` weights: measured system load (eia_loader).

    Reused verbatim from ``_caiso186os_ps_intake_bound.rubric_weights`` so the
    decomposition composes with caiso-140 §A / caiso-186os L4 (rule 28).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia_loader import load_demand

    return np.asarray(load_demand("CAISO", year, get_iso_config("CAISO"))).sum(axis=0)[
        :HOURS
    ]


def hub_masks(fl: dict, price: pd.DataFrame, state: np.ndarray) -> dict:
    """Per landing zone: hours an import row is marginal with the link unbound.

    Returns ``{landing_zone: {"fitted": mask, "measured": mask, "row": names}}``
    — the caiso-244 §3.6 / caiso-245 §3 definition, split by whether the
    marginal row carries a FITTED firm price or a MEASURED hub series.
    """
    rows = fl["rows"]
    out = {
        land: {
            "fitted": np.zeros(HOURS, dtype=bool),
            "measured": np.zeros(HOURS, dtype=bool),
            "row": np.full(HOURS, "", dtype=object),
            "offer": np.full(HOURS, np.nan),
        }
        for land in C244.CORRIDOR_LANDING.values()
    }
    for i, row in enumerate(rows):
        if row["is_export"]:
            continue
        land = C244.CORRIDOR_LANDING[row["zone"]]
        lam_w = price.loc[row["zone"]].to_numpy(float)
        lam_l = price.loc[land].to_numpy(float)
        mi = (state[i] == 0) & (np.abs(lam_w - lam_l) <= TOL)
        key = "fitted" if row["name"] in FITTED_ROWS else "measured"
        newly = mi & ~(out[land]["fitted"] | out[land]["measured"])
        out[land][key] |= mi
        out[land]["row"][newly] = row["name"]
        out[land]["offer"][newly] = fl["mc"][row["r"]][newly]
    return out


def domestic_matches(
    fl: dict, zone_names: list[str], lam_z: np.ndarray, tol: float = TOL
) -> dict:
    """Price-match masks for one zone's dual: which domestic families sit at λ.

    Complementary slackness makes ``mc = λ`` a NECESSARY condition for a unit
    to be marginal; without a unit-level replay it is the only available test,
    so it can OVER-identify (a unit at a bound whose offer happens to equal λ).

    It can also UNDER-identify, and the reason is measured, not hypothetical:
    the keeper runs ``caiso_zonal_loss_surface`` (caiso-164), which splits the
    internal CAISO links into one-way loss pairs, so a marginal unit in zone A
    prices zone B at ``λ_A / (1 − loss)`` — 0.4–1.2 $/MWh away from its own
    offer at CAISO price levels, far outside the frozen 0.05 window. That is
    why this probe reports the whole decomposition a SECOND time at
    ``TOL_SENS`` = 0.75 $/MWh — caiso-202 §C's own rung tolerance — as a
    declared robustness variant. The PRIMARY numbers are the frozen 0.05 ones
    (PRECOMMIT §1.3); the variant is reported, never re-frozen.
    """
    mc = fl["mc"]
    avail = fl["avail"] > 0.01
    zidx = fl["zone_idx"]
    is_corridor = np.array(
        [zone_names[z] in C244.CORRIDOR_LANDING for z in zidx], dtype=bool
    )
    dom = ~is_corridor
    hit_by_group: dict[str, np.ndarray] = {}
    gas_any = np.zeros(HOURS, dtype=bool)
    other_any = np.zeros(HOURS, dtype=bool)
    for grp in sorted(set(fl["group"][dom])):
        sel = dom & (fl["group"] == grp)
        if not sel.any():
            continue
        hit = ((np.abs(mc[sel] - lam_z[None, :]) <= tol) & avail[sel]).any(axis=0)
        hit_by_group[str(grp)] = hit
        if grp in GAS_GROUPS:
            gas_any |= hit
        else:
            other_any |= hit
    return {"gas": gas_any, "other": other_any, "by_group": hit_by_group}


def classify(
    lam_z: np.ndarray,
    hub_f: np.ndarray,
    hub_m: np.ndarray,
    dom: dict,
    storage_active: np.ndarray,
    dump_pos: np.ndarray,
    gas_first: bool = False,
) -> np.ndarray:
    """One frozen label per zone-hour (PRECOMMIT §1.3 priority order).

    ``gas_first`` runs the G-ORDER falsifier variant (DOM_GAS ahead of HUB).
    """
    lab = np.full(HOURS, "UNRESOLVED", dtype=object)
    surplus = (lam_z <= 0.01) | dump_pos
    order = (
        [
            ("DOM_GAS", dom["gas"]),
            ("HUB_FITTED", hub_f),
            ("HUB_MEASURED", hub_m),
            ("DOM_OTHER", dom["other"]),
        ]
        if gas_first
        else [
            ("HUB_FITTED", hub_f),
            ("HUB_MEASURED", hub_m),
            ("DOM_GAS", dom["gas"]),
            ("DOM_OTHER", dom["other"]),
        ]
    )
    order += [("STORAGE", storage_active), ("SURPLUS", surplus)]
    assigned = np.zeros(HOURS, dtype=bool)
    for name, mask in order:
        take = mask & ~assigned
        lab[take] = name
        assigned |= take
    return lab


def analyse(year: int) -> dict:
    fl = rebuild_full(year)
    zone_names = fl["zone_names"]
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
    chg = (
        stg.groupby("hour")["charge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )
    dis = (
        stg.groupby("hour")["discharge_mw"].sum().reindex(range(HOURS)).fillna(0.0).to_numpy(float)
    )
    storage_active = (chg > 1e-6) | (dis > 1e-6)

    a = actual_rt(year)
    w = rubric_weights(year)
    ok = np.isfinite(a) & (w > 0)
    denom = float(w[ok].sum())

    # --- G-BENCH: the comparator reproduces the rubric's committed rt_lw -----
    bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["avgLMP"]
    rt_lw_recomputed = float((a[ok] * w[ok]).sum() / denom)
    g_bench = {
        "recomputed_rt_lw": round(rt_lw_recomputed, 4),
        "committed_rt_lw": bench["rt_lw"],
        "abs_diff": round(abs(rt_lw_recomputed - float(bench["rt_lw"])), 4),
        "hours_actual_missing": int((~np.isfinite(a)).sum()),
    }
    g_bench["pass"] = bool(g_bench["abs_diff"] <= 0.01)

    # --- the model side, on the SAME weights ---------------------------------
    d_ca = demand.loc[list(CA_ZONES)].to_numpy(float)
    p_ca = price.loc[list(CA_ZONES)].to_numpy(float)
    share = d_ca / np.maximum(d_ca.sum(axis=0), 1e-9)  # s[z,t]
    lam_sys = (p_ca * share).sum(axis=0)
    gap_hourly = float((w[ok] * (lam_sys[ok] - a[ok])).sum() / denom)

    # printed C3a (the rubric's own basis) from the committed verdict
    verdict = json.loads((BUNDLE / "_verdict.json").read_text())
    printed = None
    for c in ((verdict.get("criteria") or {}).get("price_mean") or {}).get("records") or []:
        # the GATED record is the RT one (the DA diagnostic is SKIPPED)
        if int(c.get("year", -1)) == year and c.get("status") in ("PASS", "FAIL"):
            printed = c
    g_gap = {
        "gap_hourly": round(gap_hourly, 4),
        "printed_model": printed and printed.get("model"),
        "printed_actual": printed and printed.get("actual"),
        "printed_gap": (
            round(float(printed["model"]) - float(printed["actual"]), 4)
            if printed
            else None
        ),
    }
    g_gap["abs_diff"] = (
        round(abs(gap_hourly - g_gap["printed_gap"]), 4) if printed else None
    )
    g_gap["pass"] = bool(printed is not None and g_gap["abs_diff"] <= 1.00)
    # WHERE the G-GAP difference comes from, measured rather than asserted.
    # The rubric's model side is Σ_z p_z·D_z / Σ_z D_z with p_z the zone's OWN
    # demand-weighted mean (render_calibration_html.py L2175), which reduces
    # to the MODEL-demand-weighted hourly mean; its actual side (rt_lw) is the
    # MEASURED-load-weighted hourly mean. This probe weights BOTH sides by the
    # measured load (the caiso-131/140 convention), so the whole difference
    # sits on the model side and is a WEIGHT-BASIS term, not a price error.
    model_rubric_all = float((p_ca * d_ca).sum() / max(d_ca.sum(), 1e-9))
    model_rubric_ok = float(
        (p_ca[:, ok] * d_ca[:, ok]).sum() / max(d_ca[:, ok].sum(), 1e-9)
    )
    g_gap["basis_decomposition"] = {
        "model_rubric_basis_all_hours": round(model_rubric_all, 4),
        "model_rubric_basis_ok_hours": round(model_rubric_ok, 4),
        "model_measured_load_weighted_ok_hours": round(
            float((w[ok] * lam_sys[ok]).sum() / denom), 4
        ),
        "weight_basis_term_usd_per_mwh": round(
            model_rubric_all - float((w[ok] * lam_sys[ok]).sum() / denom), 4
        ),
        "share_of_printed_gap": (
            round(
                (model_rubric_all - float((w[ok] * lam_sys[ok]).sum() / denom))
                / g_gap["printed_gap"],
                4,
            )
            if printed and abs(g_gap["printed_gap"]) > 1e-9
            else None
        ),
        "model_demand_twh": round(float(d_ca.sum() / 1e6), 4),
        "measured_load_twh": round(float(w.sum() / 1e6), 4),
        "note": (
            "rubric model side = MODEL-demand-weighted; rubric actual side = "
            "MEASURED-load-weighted. Reported as a like-for-like observation, "
            "NOT as a reduction of C3a: the rubric's basis is the rubric's."
        ),
    }

    # --- per-zone classification ---------------------------------------------
    hubs = hub_masks(fl, price, state)
    lam_land = {
        land: price.loc[land].to_numpy(float) for land in C244.CORRIDOR_LANDING.values()
    }

    def label_all(tol: float, gas_first: bool) -> tuple[dict, dict, dict, dict]:
        """Classify every zone-hour at one tolerance / priority order.

        ``tol`` widens ONLY the two tests the zonal loss surface distorts —
        the hub's reach into a zone and the domestic price match. The import
        rows' own marginality at their WECC node stays at the verbatim
        caiso-244 0.05 (no internal loss factor sits between an import offer
        and its own node's dual).
        """
        lab: dict[str, np.ndarray] = {}
        rows_at: dict[str, np.ndarray] = {}
        ovl = {"hub_and_gas_zonehours": 0, "hub_zonehours": 0, "gas_zonehours": 0}
        groups: dict[str, dict] = {}
        for z in CA_ZONES:
            lam_z = price.loc[z].to_numpy(float)
            hub_f = np.zeros(HOURS, dtype=bool)
            hub_m = np.zeros(HOURS, dtype=bool)
            rowname = np.full(HOURS, "", dtype=object)
            for land, hm in hubs.items():
                reach = np.abs(lam_z - lam_land[land]) <= tol
                newf, newm = hm["fitted"] & reach, hm["measured"] & reach
                take = (newf | newm) & (rowname == "")
                rowname[take] = hm["row"][take]
                hub_f |= newf
                hub_m |= newm
            hub_m &= ~hub_f
            dom = domestic_matches(fl, zone_names, lam_z, tol=tol)
            dump_pos = dump.loc[z].to_numpy(float) > 1e-6
            lab[z] = classify(
                lam_z, hub_f, hub_m, dom, storage_active, dump_pos, gas_first=gas_first
            )
            rows_at[z] = rowname
            ovl["hub_and_gas_zonehours"] += int(((hub_f | hub_m) & dom["gas"]).sum())
            ovl["hub_zonehours"] += int((hub_f | hub_m).sum())
            ovl["gas_zonehours"] += int(dom["gas"].sum())
            groups[z] = dom["by_group"]
        return lab, rows_at, ovl, groups

    labels, hub_row_at, overlap, per_zone_groups = label_all(TOL, gas_first=False)
    labels_gasfirst, _, _, _ = label_all(TOL, gas_first=True)
    labels_sens, _, overlap_sens, _ = label_all(TOL_SENS, gas_first=False)

    # --- the decomposition ----------------------------------------------------
    def decompose(lab: dict[str, np.ndarray]) -> dict:
        contrib = {}  # regime -> per-hour contribution summed over zones
        weight = {}
        for r in REGIMES:
            c = np.zeros(HOURS)
            wt = np.zeros(HOURS)
            for zi, z in enumerate(CA_ZONES):
                m = lab[z] == r
                c += np.where(m, w * share[zi] * (p_ca[zi] - np.nan_to_num(a)), 0.0)
                wt += np.where(m, w * share[zi], 0.0)
            contrib[r] = np.where(ok, c, 0.0)
            weight[r] = np.where(ok, wt, 0.0)
        return contrib, weight

    contrib, weight = decompose(labels)
    contrib_gf, weight_gf = decompose(labels_gasfirst)
    contrib_sn, weight_sn = decompose(labels_sens)

    def summarise(contrib, weight) -> dict:
        rec = {}
        tot_gap = sum(float(v.sum()) for v in contrib.values()) / denom
        for r in REGIMES:
            gshare = float(contrib[r].sum()) / denom
            wshare = float(weight[r].sum()) / denom
            rec[r] = {
                "weight_share": round(wshare, 4),
                "gap_contribution_usd_per_mwh": round(gshare, 4),
                "gap_share": round(gshare / tot_gap, 4) if abs(tot_gap) > 1e-9 else None,
                "CR": (
                    round((gshare / tot_gap) / wshare, 3)
                    if wshare > 1e-9 and abs(tot_gap) > 1e-9
                    else None
                ),
                "mean_residual_usd_per_mwh": (
                    round(gshare / wshare, 3) if wshare > 1e-9 else None
                ),
            }
        rec["_total_gap_usd_per_mwh"] = round(tot_gap, 4)
        # caiso-202 §C measured its rung attribution on the POSITIVE part of
        # the gap only; this is the like-for-like view of the same statistic.
        pos_tot = sum(float(np.clip(v, 0.0, None).sum()) for v in contrib.values())
        for r in REGIMES:
            rec[r]["positive_gap_share"] = (
                round(float(np.clip(contrib[r], 0.0, None).sum()) / pos_tot, 4)
                if pos_tot > 1e-9
                else None
            )
        rec["_positive_gap_usd_per_mwh"] = round(pos_tot / denom, 4)
        return rec

    by_regime = summarise(contrib, weight)
    by_regime_gasfirst = summarise(contrib_gf, weight_gf)
    by_regime_sens = summarise(contrib_sn, weight_sn)

    # month x regime
    month_regime = {}
    for m in range(1, 13):
        hm = MONTH == m
        cell = {}
        for r in REGIMES:
            cell[r] = {
                "gap_contribution_usd_per_mwh": round(
                    float(contrib[r][hm].sum()) / denom, 4
                ),
                "weight_share": round(float(weight[r][hm].sum()) / denom, 4),
            }
        cell["_month_gap_usd_per_mwh"] = round(
            float(sum(contrib[r][hm].sum() for r in REGIMES)) / denom, 4
        )
        month_regime[m] = cell

    # --- WHICH domestic family carries DOM_GAS / DOM_OTHER --------------------
    # Post-registration CHARACTERISATION of two registered cells, not a new
    # prediction: for each domestic plant group, the gap contribution and
    # weight of the zone-hours it price-matches, inside its own regime. A
    # zone-hour can match more than one group, so these sum to MORE than the
    # regime total; the regime total is the authority and both are printed.
    group_char: dict[str, dict] = {}
    for regime in ("DOM_GAS", "DOM_OTHER"):
        acc: dict[str, dict] = {}
        for zi, z in enumerate(CA_ZONES):
            inreg = (labels[z] == regime) & ok
            base = w * share[zi]
            for g, m in per_zone_groups[z].items():
                sel = inreg & m
                if not sel.any():
                    continue
                a_g = acc.setdefault(g, {"gap": 0.0, "weight": 0.0, "zonehours": 0})
                a_g["gap"] += float(
                    (base * (p_ca[zi] - np.nan_to_num(a)))[sel].sum()
                ) / denom
                a_g["weight"] += float(base[sel].sum()) / denom
                a_g["zonehours"] += int(sel.sum())
        group_char[regime] = {
            g: {
                "gap_contribution_usd_per_mwh": round(v["gap"], 4),
                "weight_share": round(v["weight"], 4),
                "mean_residual_usd_per_mwh": (
                    round(v["gap"] / v["weight"], 3) if v["weight"] > 1e-9 else None
                ),
                "zonehours": v["zonehours"],
            }
            for g, v in sorted(acc.items(), key=lambda kv: -abs(kv[1]["gap"]))
        }

    # which import row is marginal in HUB zone-hours (weighted by contribution)
    hub_rows: dict[str, float] = {}
    for zi, z in enumerate(CA_ZONES):
        m = np.isin(labels[z], ["HUB_FITTED", "HUB_MEASURED"]) & ok
        c = np.where(m, w * share[zi] * (p_ca[zi] - np.nan_to_num(a)), 0.0)
        for name in set(hub_row_at[z][m]):
            if not name:
                continue
            sel = m & (hub_row_at[z] == name)
            hub_rows[name] = hub_rows.get(name, 0.0) + float(c[sel].sum()) / denom
    hub_rows = {k: round(v, 4) for k, v in sorted(hub_rows.items(), key=lambda kv: -abs(kv[1]))}

    hubw = by_regime["HUB_FITTED"]["weight_share"] + by_regime["HUB_MEASURED"]["weight_share"]
    hubg = (
        by_regime["HUB_FITTED"]["gap_share"] + by_regime["HUB_MEASURED"]["gap_share"]
        if by_regime["HUB_FITTED"]["gap_share"] is not None
        else None
    )
    return {
        "keeper_run_id": KEEPER_RUN_ID,
        "injected_mustrun_classes": fl["injected_mustrun_classes"],
        "biomass_lp_units_dropped": bool("biomass" in fl["injected_mustrun_classes"]),
        "G_BENCH": g_bench,
        "G_GAP": g_gap,
        "G_RECON": {
            "basis_selected": recon["basis_selected"],
            "pass": recon["G_RECON_pass"],
            "gross": recon["gross"],
            "net": recon["net"],
        },
        "G_CLASS": {
            "unresolved_weight_share": by_regime["UNRESOLVED"]["weight_share"],
            "pass": bool(by_regime["UNRESOLVED"]["weight_share"] <= 0.12),
        },
        "by_regime": by_regime,
        "by_regime_gasfirst_G_ORDER": by_regime_gasfirst,
        "by_regime_tol075_SENSITIVITY": by_regime_sens,
        "taxonomy_overlap_tol075": overlap_sens,
        "hub_total": {
            "weight_share": round(hubw, 4),
            "gap_share": round(hubg, 4) if hubg is not None else None,
            "CR": round(hubg / hubw, 3) if hubg is not None and hubw > 1e-9 else None,
            "CR_tol075": (
                round(
                    (
                        by_regime_sens["HUB_FITTED"]["gap_share"]
                        + by_regime_sens["HUB_MEASURED"]["gap_share"]
                    )
                    / max(
                        by_regime_sens["HUB_FITTED"]["weight_share"]
                        + by_regime_sens["HUB_MEASURED"]["weight_share"],
                        1e-9,
                    ),
                    3,
                )
                if by_regime_sens["HUB_FITTED"]["gap_share"] is not None
                else None
            ),
            "weight_share_tol075": round(
                by_regime_sens["HUB_FITTED"]["weight_share"]
                + by_regime_sens["HUB_MEASURED"]["weight_share"],
                4,
            ),
            "CR_gasfirst": (
                round(
                    (
                        by_regime_gasfirst["HUB_FITTED"]["gap_share"]
                        + by_regime_gasfirst["HUB_MEASURED"]["gap_share"]
                    )
                    / max(
                        by_regime_gasfirst["HUB_FITTED"]["weight_share"]
                        + by_regime_gasfirst["HUB_MEASURED"]["weight_share"],
                        1e-9,
                    ),
                    3,
                )
                if by_regime_gasfirst["HUB_FITTED"]["gap_share"] is not None
                else None
            ),
        },
        "hub_marginal_row_gap_usd_per_mwh": hub_rows,
        "taxonomy_overlap": overlap,
        "domestic_group_characterisation": group_char,
        "month_regime": month_regime,
        "model_lw_hourly": round(float((w[ok] * lam_sys[ok]).sum() / denom), 3),
        "actual_lw_hourly": round(rt_lw_recomputed, 3),
    }


def main() -> None:
    out: dict = {
        "_provenance": {
            "session": "caiso-247 (queue item A, PHASE-0 residual anatomy, ZERO LP)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper_run_id": KEEPER_RUN_ID,
            "precommit": "PRECOMMIT-caiso247-residual-regime-anatomy-2026-09-05.md",
            "instrument": "_caiso244_import_level_anatomy reconstruct() on the committed P1 duals; caiso-131/140 common-weight gap decomposition over ZONE-HOURS",
            "comparator": "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet (rt) — the series avgLMP.rt_lw is built from",
            "weights": "rubric rt_lw weights (eia_loader measured system load), applied to BOTH sides",
            "tol_usd_mwh": TOL,
            "note": "NOTHING ARMED, NO SOLVE, NO FIELD, NO FLAG. Taxonomy frozen in PRECOMMIT §1.3 before any measurement.",
        },
        "years": {},
    }
    # Disclosure (caiso-244 §7.7 / replay_keeper): what a fleet-only rebuild
    # cannot carry from the recorded recipe. None of these touches the fleet,
    # the offers or the fuel prices, and the MODEL price/demand used here come
    # from the committed sidecars, not from the rebuild — reported anyway.
    from replay_keeper import run_year_unreachable

    out["_provenance"]["injected_mustrun_note"] = (
        "inject_biomass_mustrun is NOT in meta.json (derived from "
        "solve_and_persist locals) and run_year_kwargs cannot carry it; it is "
        "recovered here from the committed class_hourly sidecar's month-flat "
        "signature. caiso-247's first run omitted it and rebuilt 184 phantom "
        "biomass LP units — the caiso-248 defect repair."
    )
    out["_provenance"]["run_year_unreachable"] = {
        k: (str(v) if not isinstance(v, (int, float, bool, type(None), str)) else v)
        for k, v in run_year_unreachable(
            json.loads((BUNDLE / "meta.json").read_text())
        ).items()
    }
    for y in YEARS:
        rec = analyse(y)
        out["years"][y] = rec
        print(f"\n===== {y} =====")
        print(
            f"  injected must-run {rec['injected_mustrun_classes']}; biomass LP units dropped "
            f"{rec['biomass_lp_units_dropped']}\n"
            f"  G-BENCH {rec['G_BENCH']['pass']} (recomputed {rec['G_BENCH']['recomputed_rt_lw']} vs committed {rec['G_BENCH']['committed_rt_lw']}, {rec['G_BENCH']['hours_actual_missing']} h missing)"
        )
        print(
            f"  G-RECON {rec['G_RECON']['pass']} basis={rec['G_RECON']['basis_selected']}; "
            f"G-GAP {rec['G_GAP']['pass']} (hourly {rec['G_GAP']['gap_hourly']} vs printed {rec['G_GAP']['printed_gap']}, diff {rec['G_GAP']['abs_diff']}); "
            f"G-CLASS {rec['G_CLASS']['pass']} (unresolved {rec['G_CLASS']['unresolved_weight_share']:.1%})"
        )
        print(f"  {'regime':14s} {'w share':>8s} {'gap $':>8s} {'gap sh':>8s} {'CR':>6s} {'mean resid':>11s}")
        for r in REGIMES:
            v = rec["by_regime"][r]
            print(
                f"  {r:14s} {v['weight_share']:8.3f} {v['gap_contribution_usd_per_mwh']:8.3f} "
                f"{(v['gap_share'] if v['gap_share'] is not None else float('nan')):8.3f} "
                f"{(v['CR'] if v['CR'] is not None else float('nan')):6.2f} "
                f"{(v['mean_residual_usd_per_mwh'] if v['mean_residual_usd_per_mwh'] is not None else float('nan')):11.3f}"
            )
        print(f"  TOTAL gap {rec['by_regime']['_total_gap_usd_per_mwh']} $/MWh")
        print(f"  basis: {rec['G_GAP']['basis_decomposition']['weight_basis_term_usd_per_mwh']} $/MWh = "
              f"{rec['G_GAP']['basis_decomposition']['share_of_printed_gap']} of the printed gap "
              f"(model demand {rec['G_GAP']['basis_decomposition']['model_demand_twh']} TWh vs measured load "
              f"{rec['G_GAP']['basis_decomposition']['measured_load_twh']} TWh)")
        print(f"  HUB total {rec['hub_total']}")
        print(f"  hub marginal row gap $: {rec['hub_marginal_row_gap_usd_per_mwh']}")
        print(f"  overlap {rec['taxonomy_overlap']}")
        for regime, gc in rec["domestic_group_characterisation"].items():
            print(f"  {regime} by plant group (overlapping; regime total is the authority):")
            for g, v in list(gc.items())[:8]:
                print(
                    f"    {g:16s} gap$ {v['gap_contribution_usd_per_mwh']:7.3f} "
                    f"w {v['weight_share']:6.3f} mean resid {v['mean_residual_usd_per_mwh']}"
                )
        print("  SENSITIVITY tol=0.75 (reported, not frozen):")
        for r in REGIMES:
            v = rec["by_regime_tol075_SENSITIVITY"][r]
            print(
                f"    {r:14s} w {v['weight_share']:6.3f} gap$ {v['gap_contribution_usd_per_mwh']:7.3f} "
                f"CR {(v['CR'] if v['CR'] is not None else float('nan')):6.2f}"
            )
        print("  month gap $/MWh:", [rec["month_regime"][m]["_month_gap_usd_per_mwh"] for m in range(1, 13)])
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
