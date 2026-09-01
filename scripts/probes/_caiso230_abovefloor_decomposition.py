"""caiso-230 Phase 0 — the caiso-229 §A ABOVE-FLOOR term decomposed into limbs.

NO LP, NO SOLVE. Every input is committed: the caiso-220 keeper's ``hourly/``
sidecars, the committed actual-LMP reference, the committed raw CAISO hub LMP
CSVs, and the caiso-105/121/131 ``run_year(fleet_only=True)`` offer
reconstruction (assembles the fleet + availability + P0 objective, builds no
matrix, calls no solver). The import-leg price reconstruction is imported
UNCHANGED from ``_caiso202_marginal_rung.py`` and the measured-hub loader
follows ``_caiso215_c3a_zonal_decomp.py`` (the caiso-227/229 reuse pattern;
only bundle + cache are re-pointed).

WHAT caiso-229 LEFT UNATTRIBUTED. Its §A identity, load-weighted,

    lambda - DA  ==  (lambda - cc_min)  +  (cc_min - DA)
                     \_ above-floor _/    \_ floor-level _/

split the C3a residual into two seasons with OPPOSITE signs on the above-floor
term (Sep-Dec +5.33 in 2024 / +7.30 in 2025; spring -11.30 / -5.96) and then
took the FLOOR-level term to a kill on both of its doors (§3-§6). The
above-floor term was MEASURED and NOT ATTRIBUTED. This probe attributes it.

TWO DECOMPOSITIONS, AND ONLY ONE OF THEM IS ACTIONABLE.

**§B, the zonal split**, is the charter's limb (e). Per hour, with ``p_min``
the cheapest CA zonal price and ``cc_min`` the model's cheapest AVAILABLE
gas-CC offer (the caiso-229 §G object, reproduced by the same code path),

    lambda - cc_min  ==  (lambda - p_min)  +  (p_min - cc_min)
                         \___ limb Z ___/    \___ limb S ___/

limb Z is the load-weighted ZONAL DISPERSION and is >= 0 by construction. It is
reported WITH ITS OWN DISQUALIFICATION: a mean-preserving zonal redistribution
moves limb Z without moving ``lambda`` at all, so limb Z is not a C3a lever by
construction — the measured corroboration is caiso-215's ISO-wide bridge terms
of +/-$0.15. §B therefore also measures the LIKE-FOR-LIKE dispersion (model vs
CAISO's own published trading hubs, same weights both sides) to say which way
the model errs, which is a statement about C3b/D-A and NOT about C3a.

**§C, the zone-hour rung attribution**, is the actionable one. The C3a metric
is the zone-hour load-weighted mean, so

    lambda - cc_min  ==  SUM_{z,h} omega_{z,h} * (p_{z,h} - cc_min_h)

and every zone-hour is attributed to the supply rung whose reconstructed offer
sits nearest ``p_{z,h}``: the in-state fleet rungs (gas-CC BY TRANCHE BAND,
CT_PEAKER, ST_GAS, hydro, oil, nuclear, coal), the per-hub priced import legs,
the static firm blocks, the corridor export legs, and a zero rung for renewable
spill. A rung's number is the exact amount the ISO's load-weighted price would
fall if those zone-hours cleared at the CC floor instead — i.e. an UPPER BOUND
on the reach of any mechanism that owns that rung. Zone-hours matching no rung
within tolerance are ``unmatched`` (the caiso-227 §B storage/hydro
inter-temporal-dual limb plus the transmission duals), interrogated in §D.

EVERYTHING IS ANNUALISED ON THE SCORER'S OWN BASIS — the zone-hour mean over
all 8,760 hours weighted by the model's own zonal demand, which reproduces
``calibration_verdict.score_price_mean``'s model number exactly (56.31 / 38.96
/ 39.76). So every limb reads directly against the required per-year C3a moves,
which §E re-derives on that same basis rather than quoting them.

Sections
  §A  identity replay — the caiso-229 §A table, re-measured (validity check)
  §B  limb Z (zonal dispersion) vs limb S, plus the like-for-like hub test
  §C  the zone-hour rung attribution, annualised on the scorer basis
  §D  the unmatched limb interrogated: storage / hydro / transmission duals
  §E  the scorer-basis envelope and each limb's reach against it
  §F  hour-of-day localisation vs the keeper's D-A 2025 phase-OFF flag

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso230_abovefloor_decomposition.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso220_c1_crosswalk"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
LMP_DIR = REPO / "data/raw/lmp-data/CAISO"
OUT = REPO / "results/calibration/_caiso230_abovefloor_decomposition.json"
CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "ae2aa6cf-7aea-535b-ba9b-27859fdf31cf/scratchpad/caiso230"
)

_spec = importlib.util.spec_from_file_location(
    "_caiso202_marginal_rung", REPO / "scripts/probes/_caiso202_marginal_rung.py"
)
M202 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M202)
M202.BUNDLE = BUNDLE
M202.CACHE = CACHE

SEPDEC = (9, 10, 11, 12)
SPRING = (3, 4, 5)
BELLY = (10, 11, 12, 13, 14, 15)
SCOPES = {"annual": None, "sepdec": SEPDEC, "spring": SPRING}

# Model zone -> CAISO trading hub, the caiso-215 mapping (config/iso_configs.py
# _caiso_config: the three SP15-split zones are the caiso-172/LCT partition of
# the old SP15). Used ONLY for the §B like-for-like dispersion test.
ZONE_HUB = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "LA_BASIN": "TH_SP15_GEN-APND",
    "SDGE": "TH_SP15_GEN-APND",
    "SP15_rest": "TH_SP15_GEN-APND",
}

# Nearest-offer tolerance, the caiso-202 estimator's own $0.75/MWh. A price
# further than this from EVERY reconstructed rung is `unmatched` — by
# construction the dual limb (storage SOC, hydro budget and transmission duals
# are the only prices in this LP with no offer-side counterpart).
TOL = 0.75

RESULT: dict = {}
FRAMES: dict = {}
HIT: dict = {}


def month_of_hour(year: int) -> np.ndarray:
    """Return the calendar month of each of the year's 8760 model hours."""
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS + 24), "h")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def local_hour_index(year: int) -> pd.DatetimeIndex:
    """The committed 8760 hour clock: local-standard PST, local Feb 29 dropped.

    Mirrors ``derive_actual_lmp.py`` and ``_caiso215_c3a_zonal_decomp.py``.
    """
    stamps = pd.date_range(
        f"{year}-01-01", periods=HOURS + 24, freq="h", tz="Etc/GMT+8"
    )
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps


def hub_prices(market: str, year: int) -> pd.DataFrame:
    """Return the measured CAISO trading-hub LMPs on the committed hour clock."""
    df = pd.read_csv(LMP_DIR / f"CAISO_{market}_hourly_{year}.csv")
    df = df[df["node"].isin(set(ZONE_HUB.values()))].copy()
    ts = pd.to_datetime(df["interval_start_gmt"], utc=True).dt.tz_convert("Etc/GMT+8")
    pos = pd.Series(np.arange(HOURS), index=local_hour_index(year))
    df["hour"] = pos.reindex(ts).to_numpy()
    df = df.dropna(subset=["hour"])
    df["hour"] = df["hour"].astype(int)
    return df.pivot_table(index="hour", columns="node", values="LMP").reindex(
        range(HOURS)
    )


def actuals(year: int) -> pd.DataFrame:
    """Return the committed DA/RT actual-LMP reference for the year."""
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour").reindex(range(HOURS))


def fleet_recon(year: int) -> dict:
    """Rebuild the keeper's offer surface with unit identity, and cache it.

    Identical to ``_caiso202_marginal_rung.fleet_recon`` (same ``run_year``
    call, same kwargs filter, same meta) except that it ALSO carries the unit
    ids, zone names and plant groups the tranche-band attribution needs.
    """
    p = CACHE / f"caiso230_recon_{year}.npz"
    if p.exists():
        z = np.load(p, allow_pickle=True)
        return {k: z[k] for k in ("cap", "mc", "fuel", "uid", "zone", "group")}
    import inspect

    from run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {k: v for k, v in meta.items() if k in params and k not in skip}
    gp = meta["gas_prices"]
    gas = float(gp.get(str(year), gp.get(year, 0.0)))
    state = run_year(year, meta["iso"], HOURS, gas, {}, fleet_only=True, **kwargs)

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    fa = state["fleet_arrays"]
    cap = (fa.pmax[:, None] * np.asarray(fa.availability, dtype=float)).astype(
        np.float32
    )
    mc = np.asarray(state["mc_base"], dtype=np.float32)
    fuel = np.array([inv.get(int(i), str(i)) for i in np.asarray(fa.fuel_type_idx)])
    uid = np.array([str(u) for u in fa.unit_ids])
    zn = [z.name for z in get_iso_config(ISO).zones]
    zone = np.array([zn[int(i)] if int(i) < len(zn) else "?" for i in fa.zone_idx])
    grp = fa.plant_group
    group = (
        np.array([str(g) for g in np.asarray(grp)])
        if grp is not None
        else np.array(["" for _ in uid])
    )
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, cap=cap, mc=mc, fuel=fuel, uid=uid, zone=zone, group=group)
    return {
        "cap": cap,
        "mc": mc,
        "fuel": fuel,
        "uid": uid,
        "zone": zone,
        "group": group,
    }


def rung_label(fuel: str, uid: str, group: str) -> str:
    """Return the attribution label for one LP unit.

    Gas-CC rungs keep their TRANCHE BAND (the last ``_``-segment of the unit
    id: ``committed`` / ``econ*`` / ``peak``), because the charter's limb (a)
    is the climb WITHIN the CC stack. Every other thermal class collapses to
    its plant group plus band; non-thermal classes to their fuel.
    """
    tag = uid.split("_")[-1]
    band = (
        "committed"
        if tag.startswith("committed")
        else "peak"
        if tag.startswith("peak")
        else "econ"
        if tag.startswith("econ")
        else tag
    )
    if fuel == "gas_cc":
        g = group if group in ("CC_REGULAR", "CC_CHP") else "CC"
        return f"fleet:{g}:{band}"
    if fuel in ("gas_ct", "gas_st", "coal"):
        return f"fleet:{group or fuel.upper()}:{band}"
    return f"fleet:{fuel}"


def frame(year: int) -> dict:
    """Assemble the per-hour / per-zone-hour common frame for one year."""
    from market_sim.config.fuel_trajectories import STATE_CARBON_PRICE_BY_ISO

    sc = M202.sidecars(year)
    a = actuals(year)
    rec = fleet_recon(year)
    mc, cap, fuel = rec["mc"], rec["cap"], rec["fuel"]
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    # The full runner injects biomass as an EIA-923 monthly must-run profile
    # and DROPS the raw biomass LP units (run_calibration_full
    # `_must_run_profiles` -> inject_biomass_mustrun); the keeper's sidecar
    # biomass is month-flat, confirming it. Exclude them from the candidate
    # rungs — they never clear the merit order in the scored solve. (Same
    # exclusion, same reason, as _caiso202_marginal_rung.)
    keep = fuel != "biomass"
    mc, cap = mc[keep], cap[keep]
    fuel, uid = fuel[keep], rec["uid"][keep]
    group, uzone = rec["group"][keep], rec["zone"][keep]

    cc = fuel == "gas_cc"
    sel = cc[:, None] & (cap > 1.0)
    assert sel.any(axis=0).all(), "an hour with no available CC offer"
    ccm = np.min(np.where(sel, mc, np.inf), axis=0)

    ca_zones = [z for z in sc["price"].columns if not str(z).startswith("WECC")]
    pz = sc["price"][ca_zones]
    dz = sc["demand"][ca_zones]
    return {
        "zones": ca_zones,
        "pz": pz.to_numpy(),  # (T, nz)
        "dz": dz.to_numpy(),  # (T, nz)
        "lam": M202.ca_lambda(sc),
        "p_min": pz.min(axis=1).to_numpy(),
        "w": dz.sum(axis=1).to_numpy(),  # the SCORER's hourly weight
        "da": a["da"].to_numpy(),
        "rt": a["rt"].to_numpy(),
        "cc_min": ccm,
        "mo": month_of_hour(year),
        "hod": np.arange(HOURS) % 24,
        "mc": mc,
        "cap": cap,
        "uzone": uzone,
        "ugroup": group,
        "uuid": uid,
        "labels": np.array([rung_label(f, u, g) for f, u, g in zip(fuel, uid, group)]),
        "legs": M202.import_leg_prices(year, STATE_CARBON_PRICE_BY_ISO[ISO][year]),
        # the caiso-229 basis, kept ONLY for the §A validity replay
        "w229": M202.rubric_weights(year),
    }


def _months(f: dict, months) -> np.ndarray:
    """Return the hour mask for a month scope (None = the whole year)."""
    return np.ones(HOURS, dtype=bool) if months is None else np.isin(f["mo"], months)


def section_a() -> dict:
    """Replay the caiso-229 §A identity as this probe's validity check."""
    print("=" * 78)
    print("§A — caiso-229 §A identity REPLAYED (validity check, not a new result)")
    print("=" * 78)
    print("    lambda - DA  ==  (lambda - cc_min)  +  (cc_min - DA)")
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        rows = {}
        print(f"\n[{year}]  {'scope':<8}{'lam-DA':>9}{'lam-ccmin':>11}{'ccmin-DA':>10}")
        for name, months in SCOPES.items():
            m = _months(f, months) & ~np.isnan(f["da"])
            w = f["w229"][m]
            gap = float(np.average(f["lam"][m] - f["da"][m], weights=w))
            above = float(np.average(f["lam"][m] - f["cc_min"][m], weights=w))
            floor = float(np.average(f["cc_min"][m] - f["da"][m], weights=w))
            print(f"        {name:<8}{gap:>+9.2f}{above:>+11.2f}{floor:>+10.2f}")
            rows[name] = {
                "gap_lam_minus_da": round(gap, 3),
                "above_floor_lam_minus_ccmin": round(above, 3),
                "floor_level_ccmin_minus_da": round(floor, 3),
            }
        out[year] = rows
    return out


def section_b() -> dict:
    """Limb Z vs limb S, and the like-for-like model-vs-hub dispersion test."""
    print("\n" + "=" * 78)
    print("§B — limb Z (zonal dispersion) vs limb S, and the like-for-like test")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        wann = f["w"].sum()
        rows = {}
        print(
            f"\n[{year}]  {'scope':<8}{'above-floor':>12}{'limb Z':>9}{'limb S':>9}"
            f"{'| annualised Z':>16}{'S':>8}{'total':>8}"
        )
        for name, months in SCOPES.items():
            m = _months(f, months)
            w = f["w"][m]
            above = f["lam"][m] - f["cc_min"][m]
            z = f["lam"][m] - f["p_min"][m]
            s = f["p_min"][m] - f["cc_min"][m]
            ann_z, ann_s = float((w * z).sum() / wann), float((w * s).sum() / wann)
            print(
                f"        {name:<8}{np.average(above, weights=w):>+12.2f}"
                f"{np.average(z, weights=w):>+9.2f}{np.average(s, weights=w):>+9.2f}"
                f"{ann_z:>+16.2f}{ann_s:>+8.2f}{ann_z + ann_s:>+8.2f}"
            )
            rows[name] = {
                "above_floor_scope_mean": round(float(np.average(above, weights=w)), 3),
                "limbZ_zonal_scope_mean": round(float(np.average(z, weights=w)), 3),
                "limbS_system_scope_mean": round(float(np.average(s, weights=w)), 3),
                "limbZ_annualised": round(ann_z, 3),
                "limbS_annualised": round(ann_s, 3),
                "above_floor_annualised": round(ann_z + ann_s, 3),
            }
        # LIKE-FOR-LIKE: collapse the model's 5 CA zones onto CAISO's own 3
        # trading hubs with the model's own demand weights, then compute the
        # SAME dispersion statistic on the model and on the measured hubs.
        # Same weights, same zone set, same estimator on both sides.
        hubs = sorted(set(ZONE_HUB.values()))
        hidx = [[i for i, z in enumerate(f["zones"]) if ZONE_HUB[z] == h] for h in hubs]
        hd = np.stack([f["dz"][:, ix].sum(axis=1) for ix in hidx], axis=1)
        hp_mod = np.stack(
            [
                (f["pz"][:, ix] * f["dz"][:, ix]).sum(axis=1)
                / np.maximum(f["dz"][:, ix].sum(axis=1), 1e-9)
                for ix in hidx
            ],
            axis=1,
        )
        rows["like_for_like"] = {}
        for mkt in ("dam", "rtm"):
            hp_act = hub_prices(mkt, year)[hubs].to_numpy()
            ok = np.isfinite(hp_act).all(axis=1)
            for name, months in (("annual", None), ("sepdec", SEPDEC)):
                m = _months(f, months) & ok
                w = f["w"][m]
                hw = hd[m] / np.maximum(hd[m].sum(axis=1, keepdims=True), 1e-9)
                d_mod = (hp_mod[m] * hw).sum(axis=1) - hp_mod[m].min(axis=1)
                d_act = (hp_act[m] * hw).sum(axis=1) - hp_act[m].min(axis=1)
                rows["like_for_like"][f"{mkt}_{name}"] = {
                    "n_hours": int(m.sum()),
                    "dispersion_model": round(float(np.average(d_mod, weights=w)), 3),
                    "dispersion_actual": round(float(np.average(d_act, weights=w)), 3),
                    "model_minus_actual": round(
                        float(np.average(d_mod - d_act, weights=w)), 3
                    ),
                }
                r = rows["like_for_like"][f"{mkt}_{name}"]
                print(
                    f"        hub dispersion [{mkt}/{name:<6}] model "
                    f"{r['dispersion_model']:>6.2f} vs actual "
                    f"{r['dispersion_actual']:>6.2f}  -> "
                    f"{r['model_minus_actual']:+.2f} ({r['n_hours']} h)"
                )
        out[year] = rows
    return out


def _attribute(f: dict, hours: np.ndarray) -> dict:
    """Nearest-offer rung match of every CA zonal price in the given hours.

    Returns ``{(hour, zone_index): (label, local_flag, fleet_index)}``, the
    fleet index being -1 when the match is a seam leg / zero rung / unmatched.
    The candidate set is
    the caiso-202 estimator's — the in-state fleet offers, the per-hub priced
    import legs, the static firm blocks, the corridor export legs — extended
    with a zero rung for renewable spill (wind/solar are LP variables at MC=0,
    not fleet rows, so a curtailment-set dual has no fleet counterpart and
    would otherwise read `unmatched`).
    """
    mc, cap, labels, legs, uzone = (
        f["mc"],
        f["cap"],
        f["labels"],
        f["legs"],
        f["uzone"],
    )
    leg_names = list(legs)
    leg_arr = np.stack([np.asarray(legs[n], dtype=float) for n in leg_names])
    hit: dict = {}
    nz = f["pz"].shape[1]
    for h in hours:
        avail = np.flatnonzero(cap[:, h] > 1.0)
        pr = mc[avail, h]
        lg = leg_arr[:, h]
        for zi in range(nz):
            p = f["pz"][h, zi]
            j = int(np.argmin(np.abs(lg - p)))
            best, bd, loc, gi = leg_names[j], abs(float(lg[j]) - p), False, -1
            if not best.startswith(("imp:", "exp:")):
                best = "imp:" + best
            if avail.size:
                k = int(np.argmin(np.abs(pr - p)))
                if abs(float(pr[k]) - p) < bd:
                    g = int(avail[k])
                    best, bd, gi = labels[g], abs(float(pr[k]) - p), g
                    loc = bool(uzone[g] == f["zones"][zi])
            if abs(p) < bd:
                best, bd, loc, gi = "renewable_zero", abs(p), False, -1
            if bd > TOL:
                best, loc, gi = "unmatched", False, -1
            hit[(int(h), zi)] = (best, loc, gi)
    return hit


def section_c() -> dict:
    """Attribute the zone-hour above-floor term by rung, on the scorer basis."""
    print("\n" + "=" * 78)
    print("§C — zone-hour above-floor term attributed by rung, ANNUALISED $/MWh")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        wann = f["w"].sum()
        rows = {}
        for scope, months in (("sepdec", SEPDEC), ("annual", None)):
            hs = np.flatnonzero(_months(f, months))
            hit = _attribute(f, hs)
            HIT[(year, scope)] = hit
            cat: dict[str, dict] = {}
            for (h, zi), (lab, loc, _gi) in hit.items():
                c = cat.setdefault(
                    lab,
                    {
                        "n_zone_hours": 0,
                        "n_local": 0,
                        "contrib": 0.0,
                        "p": [],
                        "hh": [],
                    },
                )
                c["n_zone_hours"] += 1
                c["n_local"] += int(loc)
                c["contrib"] += float(
                    f["dz"][h, zi] * (f["pz"][h, zi] - f["cc_min"][h]) / wann
                )
                c["p"].append(float(f["pz"][h, zi]))
                c["hh"].append(h % 24)
            tot = sum(c["contrib"] for c in cat.values())
            print(
                f"\n[{year}/{scope}] above-floor annualised {tot:+.2f} $/MWh over "
                f"{len(hs)} h x {f['pz'].shape[1]} zones"
            )
            print(
                f"    {'rung':<30}{'zone-h':>8}{'ann $/MWh':>11}{'share':>8}"
                f"{'local%':>8}{'p_z p50':>9}{'hod p50':>9}"
            )
            clean = {}
            for name, c in sorted(cat.items(), key=lambda kv: -kv[1]["contrib"]):
                clean[name] = {
                    "n_zone_hours": c["n_zone_hours"],
                    "local_pct": round(c["n_local"] / c["n_zone_hours"] * 100, 1),
                    "annualised_usd_mwh": round(c["contrib"], 3),
                    "share_pct": round(c["contrib"] / tot * 100, 1) if tot else None,
                    "p_zone_p50": round(float(np.percentile(c["p"], 50)), 2),
                    "hod_p50": int(np.percentile(c["hh"], 50)),
                }
                r = clean[name]
                print(
                    f"    {name:<30}{r['n_zone_hours']:>8}"
                    f"{r['annualised_usd_mwh']:>+11.3f}{r['share_pct']:>7.1f}%"
                    f"{r['local_pct']:>7.1f}%{r['p_zone_p50']:>9.2f}"
                    f"{r['hod_p50']:>9d}"
                )
            rows[scope] = {
                "above_floor_annualised_total": round(tot, 3),
                "rungs": clean,
            }
        out[year] = rows
    return out


def section_d() -> dict:
    """Interrogate the unmatched limb: storage / hydro / transmission duals."""
    print("\n" + "=" * 78)
    print("§D — the UNMATCHED limb: storage / hydro / transmission duals?")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        st = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
        st = st[st["pass"] == "P1"]
        dis = (
            st.pivot_table(index="hour", columns="tech", values="discharge_mw")
            .reindex(range(HOURS))
            .fillna(0.0)
            .sum(axis=1)
            .to_numpy()
        )
        chg = (
            st.pivot_table(index="hour", columns="tech", values="charge_mw")
            .reindex(range(HOURS))
            .fillna(0.0)
            .sum(axis=1)
            .to_numpy()
        )
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        hyd = (
            ch[ch["klass"] == "hydro"]
            .set_index("hour")["mw"]
            .reindex(range(HOURS))
            .fillna(0.0)
            .to_numpy()
        )
        rows = {}
        for scope in ("sepdec", "annual"):
            hit = HIT[(year, scope)]
            un = [k for k, v in hit.items() if v[0] == "unmatched"]
            if not un:
                rows[scope] = {"n_zone_hours": 0}
                continue
            uh = np.array([h for h, _ in un])
            uz = np.array([z for _, z in un])
            allh = np.array([h for h, _ in hit])
            # is the zone's price SEPARATED from the ISO's cheapest zone?
            sep = np.abs(f["pz"][uh, uz] - f["p_min"][uh]) > TOL
            act = (dis[uh] > 1.0) | (chg[uh] > 1.0)
            wann = f["w"].sum()
            contrib = float(
                (f["dz"][uh, uz] * (f["pz"][uh, uz] - f["cc_min"][uh])).sum() / wann
            )
            rows[scope] = {
                "n_zone_hours": len(un),
                "share_of_scope_zone_hours_pct": round(len(un) / len(hit) * 100, 2),
                "annualised_usd_mwh": round(contrib, 3),
                "zone_separated_pct": round(float(sep.mean() * 100), 1),
                "storage_active_pct": round(float(act.mean() * 100), 1),
                "hydro_active_pct": round(float((hyd[uh] > 1.0).mean() * 100), 1),
                "storage_active_pct_all_zone_hours": round(
                    float(((dis[allh] > 1.0) | (chg[allh] > 1.0)).mean() * 100), 1
                ),
                "p_zone_p50": round(float(np.percentile(f["pz"][uh, uz], 50)), 2),
            }
            r = rows[scope]
            print(
                f"  [{year}/{scope}] unmatched {r['n_zone_hours']} zone-h "
                f"({r['share_of_scope_zone_hours_pct']}%), "
                f"annualised {r['annualised_usd_mwh']:+.2f}: "
                f"zone-separated {r['zone_separated_pct']}%, storage active "
                f"{r['storage_active_pct']}% (baseline "
                f"{r['storage_active_pct_all_zone_hours']}%), hydro active "
                f"{r['hydro_active_pct']}%"
            )
        out[year] = rows
    return out


def section_e() -> dict:
    """The scorer-basis envelope: required C3a move, re-derived, per year."""
    print("\n" + "=" * 78)
    print("§E — the SCORER-basis C3a envelope (re-derived, not quoted)")
    print("=" * 78)
    # The committed actual the scorer gates on (rt_lw), read from the run's
    # own committed benchmark parts rather than recomputed.
    import gzip

    bench = {
        y: json.loads(
            gzip.open(REPO / f"frontend/data/backcast/bench/CAISO/{y}.json.gz").read()
        )["bench"]["avgLMP"]
        for y in YEARS
    }
    out = {}
    print(f"\n  {'year':<6}{'model lw':>10}{'RT lw':>9}{'C3a %':>8}{'req move':>10}")
    for year in YEARS:
        f = FRAMES[year]
        mod = float((f["w"] * f["lam"]).sum() / f["w"].sum())
        act = float(bench[year]["rt_lw"])
        pct = (mod - act) / act * 100.0
        req = min(0.0, act * 1.10 - mod)
        print(f"  {year:<6}{mod:>10.2f}{act:>9.2f}{pct:>+7.1f}%{req:>10.2f}")
        out[year] = {
            "model_lw": round(mod, 2),
            "rt_lw": round(act, 2),
            "c3a_pct": round(pct, 2),
            "required_move_usd_mwh": round(req, 3),
            "cc_min_lw": round(float((f["w"] * f["cc_min"]).sum() / f["w"].sum()), 2),
        }
    return out


def section_f() -> dict:
    """Localise the Sep-Dec above-floor term by hour of day (D-A phase flag)."""
    print("\n" + "=" * 78)
    print("§F — hour-of-day localisation of the Sep-Dec above-floor term")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        wann = f["w"].sum()
        m = _months(f, SEPDEC)
        rows = {}
        print(
            f"\n[{year}]  {'hod band':<14}{'ann Z':>9}{'ann S':>9}{'ann total':>11}"
            f"{'lam lw':>9}"
        )
        for name, hh in (
            ("night 0-6", range(0, 7)),
            ("morning 7-9", range(7, 10)),
            ("belly 10-15", BELLY),
            ("ramp 16-18", range(16, 19)),
            ("evening 19-23", range(19, 24)),
        ):
            b = m & np.isin(f["hod"], list(hh))
            w = f["w"][b]
            z = float((w * (f["lam"][b] - f["p_min"][b])).sum() / wann)
            s = float((w * (f["p_min"][b] - f["cc_min"][b])).sum() / wann)
            lam = float(np.average(f["lam"][b], weights=w))
            print(f"        {name:<14}{z:>+9.2f}{s:>+9.2f}{z + s:>+11.2f}{lam:>9.2f}")
            rows[name] = {
                "limbZ_annualised": round(z, 3),
                "limbS_annualised": round(s, 3),
                "total_annualised": round(z + s, 3),
                "lambda_lw": round(lam, 2),
                "n_hours": int(b.sum()),
            }
        out[year] = rows
    return out


# Rung FAMILIES for the §G cross-tab. `cc_body` is the CC stack's committed +
# econ bands (the caiso-229 offer-level door's own object); `peaking` is every
# rung whose commitment is an evening/peak act — the CT classes at any band, the
# CC/ST peak bands and ST_GAS; `import_export` the priced seam legs; `cheap` the
# rungs that sit BELOW the CC floor and therefore pull the mean down.
FAMILY = {
    "cc_body": lambda r: (
        r.startswith("fleet:CC_") and r.rsplit(":", 1)[1] in ("committed", "econ")
    ),
    "peaking": lambda r: (
        r.startswith("fleet:CT_")
        or r.startswith("fleet:ST_GAS")
        or (r.startswith("fleet:CC_") and r.endswith(":peak"))
    ),
    "import_export": lambda r: r.startswith(("imp:", "exp:", "fleet:import")),
    "coal_hydro_nuclear_renew": lambda r: r.startswith(
        ("fleet:COAL", "fleet:hydro", "fleet:nuclear", "fleet:oil", "renewable")
    ),
    "unmatched": lambda r: r == "unmatched",
}

HOD_BANDS = (
    ("night 0-6", tuple(range(0, 7))),
    ("morning 7-9", (7, 8, 9)),
    ("belly 10-15", BELLY),
    ("ramp 16-18", (16, 17, 18)),
    ("evening 19-23", tuple(range(19, 24))),
)


def _family(rung: str) -> str:
    """Return the §G family a rung label belongs to."""
    for name, test in FAMILY.items():
        if test(rung):
            return name
    return "other"


def section_g() -> dict:
    """Cross-tab the above-floor term by rung family x hour-of-day band.

    This is what localises the limb against the keeper's D-A phase flag: the
    §F split says WHEN the term sits, §C says WHICH rung carries it, and only
    the cross-tab says which rung carries it WHEN.
    """
    print("\n" + "=" * 78)
    print("§G — above-floor term by rung FAMILY x hour-of-day band, ANNUALISED")
    print("=" * 78)
    out = {}
    fams = list(FAMILY) + ["other"]
    for year in YEARS:
        f = FRAMES[year]
        wann = f["w"].sum()
        rows = {}
        for scope in ("annual", "sepdec"):
            hit = HIT[(year, scope)]
            grid = {b: dict.fromkeys(fams, 0.0) for b, _ in HOD_BANDS}
            band_of = {}
            for b, hh in HOD_BANDS:
                for h in hh:
                    band_of[h] = b
            for (h, zi), (lab, _loc, _gi) in hit.items():
                c = float(f["dz"][h, zi] * (f["pz"][h, zi] - f["cc_min"][h]) / wann)
                grid[band_of[h % 24]][_family(lab)] += c
            print(f"\n[{year}/{scope}]  annualised $/MWh")
            print(
                f"    {'hod band':<14}"
                + "".join(f"{x[:11]:>13}" for x in fams)
                + f"{'TOTAL':>10}"
            )
            for b, _ in HOD_BANDS:
                r = grid[b]
                tot = sum(r.values())
                print(
                    f"    {b:<14}"
                    + "".join(f"{r[x]:>+13.3f}" for x in fams)
                    + f"{tot:>+10.3f}"
                )
                rows.setdefault(scope, {})[b] = {
                    k: round(v, 3) for k, v in r.items()
                } | {"TOTAL": round(tot, 3)}
            col = {x: sum(grid[b][x] for b, _ in HOD_BANDS) for x in fams}
            print(
                f"    {'TOTAL':<14}"
                + "".join(f"{col[x]:>+13.3f}" for x in fams)
                + f"{sum(col.values()):>+10.3f}"
            )
            rows.setdefault(scope, {})["TOTAL"] = {
                k: round(v, 3) for k, v in col.items()
            } | {"TOTAL": round(sum(col.values()), 3)}
        out[year] = rows
    return out


# ---------------------------------------------------------------------------
# §H — the measured-band SIGN/SIZE test on CAISO's THREE UN-GROUNDED gas classes
# ---------------------------------------------------------------------------
#
# `_CAISO_OFFER_CURVE` (backcast_config.py) states in its own comment that
# CC_CHP / CT_CHP / ST_GAS "are PINNED to the values CAISO previously inherited
# from the generic ERCOT-lineage `else` branch. They are NOT CAISO-grounded —
# they are preserved verbatim ONLY so the neutral generic fallback (rule #24)
# does not silently change the caiso-51 keeper", and flags CT_CHP's inherited
# 1.20 econ against a measured 0.594 marginal as "the largest such margin —
# surfaced for A/B, not asserted good". Two more fitted bands sit alongside
# them: CC_REGULAR `committed` (the fitted Lever-A 1.00) and CT_PEAKER
# `committed` (a NYISO-grounded 1.35). Under rule 25 [R-ISO-SCOPE] every one of
# these is an out-of-ISO multiplier on CAISO's binding path.
#
# CAISO's OWN measured counterpart EXISTS for all five, and the derive script
# says so explicitly: the masked OASIS public bids cannot be plant-mapped, so
# `derive_caiso_offer_surface.py` discloses that "the three OTC/RMR steamers
# (ST_GAS ...) and priced CT_CHP curves land in the CT bucket ... CC_CHP
# (HR 6.90) lands in the CC bucket". The measured CC bucket is therefore the
# pooled CC_REGULAR+CC_CHP conduct and the CT bucket the pooled
# CT_PEAKER+CT_CHP+ST_GAS conduct — so re-grounding each un-grounded class on
# its OWN bucket is a measured-input substitution with ZERO free parameters,
# not a new fitted lever.
#
# This section applies the caiso-229 §3/§4 discipline to those five bands:
# FIRST the sign of the measured-faithful move, THEN its arithmetic size.
MEASURED_BUCKET = {  # model class -> the measured bucket it lands in
    "CC_REGULAR": "CC_REGULAR",
    "CC_CHP": "CC_REGULAR",
    "CT_PEAKER": "CT_PEAKER",
    "CT_CHP": "CT_PEAKER",
    "ST_GAS": "CT_PEAKER",
}

# Tranche-tag -> band. The continuous econ ramp econc00..econc05 interpolates
# econ_low -> econ_high (offer_curves.py `_econ_continuous_steps`), so its lower
# half is read against econ_low and its upper half against econ_high; `econlo`/
# `econhi` are the two-tranche CT_CHP form and `econ` the single-tranche one.
TAG_BAND = {
    "committed": "committed",
    "econlo": "econ_low",
    "econhi": "econ_high",
    "econ": "econ_mid",
    "econc00": "econ_low",
    "econc01": "econ_low",
    "econc02": "econ_low",
    "econc03": "econ_high",
    "econc04": "econ_high",
    "econc05": "econ_high",
    "peak": "peak",
}

# The conditional-ladder rungs. `caiso_offer_surface_conditional` reprices 380
# gas peak-rung rows across 4 net-load bins (P1-only), so peak2..peak5 carry the
# CONDITIONAL markup rather than the registered `peak` band multiplier and
# cannot be read against it. They are counted and reported separately so their
# size is on the record rather than silently dropped.
LADDER_TAGS = ("peak2", "peak3", "peak4", "peak5")


def _armed_measured() -> dict:
    """Return ``{class: {band: (armed_mult, measured_mult)}}`` for the five."""
    from market_sim.pipeline.backcast_config import _CAISO_OFFER_CURVE

    meas = json.loads(
        (
            REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
        ).read_text()
    )
    out: dict[str, dict[str, tuple[float, float]]] = {}
    for cls, bucket in MEASURED_BUCKET.items():
        armed = dict(_CAISO_OFFER_CURVE[cls])
        # the keeper arms caiso_offer_surface_measured, which deep-merges the
        # measured `bands` over the fitted curve for the two NAMED classes only
        if cls in meas:
            armed.update(meas[cls]["bands"])
        m = dict(meas[bucket]["bands"]) | dict(meas[bucket].get("unarmed", {}))
        row = {}
        for band in ("committed", "econ_low", "econ_high", "peak"):
            if band in armed and band in m:
                row[band] = (float(armed[band]), float(m[band]))
        row["econ_mid"] = (
            (row["econ_low"][0] + row["econ_high"][0]) / 2.0,
            (row["econ_low"][1] + row["econ_high"][1]) / 2.0,
        )
        out[cls] = row
    return out


def section_h() -> dict:
    """Sign and size of a measured-faithful re-grounding of the fitted bands.

    Sign is EXACT (both multipliers are committed constants). Size is a strict
    UPPER BOUND: the band multiplier scales only the FUEL component of the
    offer, so ``|dlambda| <= sum omega * p_z * |dmult / mult|`` over the
    zone-hours where that class-band is the marginal rung — the caiso-229 §4
    bounding form, applied to the above-floor term instead of the floor.
    """
    print("\n" + "=" * 78)
    print("§H — measured-faithful band re-grounding: SIGN first, then SIZE")
    print("=" * 78)
    am = _armed_measured()
    print(f"\n  {'class':<12}{'band':<11}{'armed':>8}{'measured':>10}{'move':>9}")
    for cls, row in am.items():
        for band, (a, m) in row.items():
            if band == "econ_mid":
                continue
            print(
                f"  {cls:<12}{band:<11}{a:>8.3f}{m:>10.3f}{(m - a) / a * 100:>+8.1f}%"
            )
    out = {
        "bands": {
            c: {
                b: {"armed": a, "measured": m, "move_pct": round((m - a) / a * 100, 2)}
                for b, (a, m) in r.items()
            }
            for c, r in am.items()
        },
        "years": {},
    }
    for year in YEARS:
        f = FRAMES[year]
        wann = f["w"].sum()
        hit = HIT[(year, "annual")]
        cells: dict[str, dict] = {}
        for (h, zi), (_lab, _loc, gi) in hit.items():
            if gi < 0:
                continue
            cls = str(f["ugroup"][gi])
            if cls not in am:
                continue
            tag = str(f["uuid"][gi]).split("_")[-1]
            w0 = float(f["dz"][h, zi] / wann)
            if tag in LADDER_TAGS:
                c = cells.setdefault(
                    f"{cls}:conditional_ladder",
                    {"n": 0, "bound": 0.0, "above": 0.0, "move_pct": float("nan")},
                )
                c["n"] += 1
                c["above"] += w0 * float(f["pz"][h, zi] - f["cc_min"][h])
                continue
            band = TAG_BAND.get(tag)
            if band is None or band not in am[cls]:
                continue
            a, m = am[cls][band]
            r = (m - a) / a
            w = w0
            c = cells.setdefault(
                f"{cls}:{band}",
                {"n": 0, "bound": 0.0, "above": 0.0, "move_pct": r * 100},
            )
            c["n"] += 1
            c["bound"] += w * float(f["pz"][h, zi]) * r
            c["above"] += w * float(f["pz"][h, zi] - f["cc_min"][h])
        tot = sum(c["bound"] for c in cells.values())
        print(
            f"\n[{year}] first-order bound on a full measured re-grounding: "
            f"{tot:+.3f} $/MWh (annual load-weighted)"
        )
        print(
            f"    {'class:band':<24}{'zone-h':>8}{'move':>8}{'|bound| $/MWh':>15}"
            f"{'above-floor $':>15}"
        )
        for k, c in sorted(cells.items(), key=lambda kv: -abs(kv[1]["bound"])):
            print(
                f"    {k:<24}{c['n']:>8}{c['move_pct']:>+7.1f}%"
                f"{c['bound']:>+15.3f}{c['above']:>+15.3f}"
            )
        out["years"][year] = {
            "total_first_order_bound_usd_mwh": round(tot, 3),
            "cells": {
                k: {
                    "n_zone_hours": c["n"],
                    "move_pct": (
                        None if np.isnan(c["move_pct"]) else round(c["move_pct"], 2)
                    ),
                    "first_order_bound_usd_mwh": round(c["bound"], 4),
                    "above_floor_usd_mwh": round(c["above"], 4),
                }
                for k, c in cells.items()
            },
        }
    return out


def main() -> None:
    """Run every section and write the committed JSON record."""
    for year in YEARS:
        FRAMES[year] = frame(year)
    RESULT["A_identity_replay"] = section_a()
    RESULT["B_zonal_split"] = section_b()
    RESULT["C_rung_attribution"] = section_c()
    RESULT["D_unmatched_limb"] = section_d()
    RESULT["E_envelope"] = section_e()
    RESULT["F_hod"] = section_f()
    RESULT["G_family_hod"] = section_g()
    RESULT["H_measured_regrounding"] = section_h()
    OUT.write_text(json.dumps(RESULT, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
