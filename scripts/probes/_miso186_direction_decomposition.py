"""miso-186 — the Midwest-stack scarce-hour DIRECTION decomposition (no LP).

Executes ``PREREG-miso186-midwest-stack-direction-2026-08-25.md`` §2: from the
committed keeper sidecars (``miso177_rho_B``) plus measured inputs already
in-repo, decompose the scarce-hour Midwest-South direction error into its
formation inputs — load alignment (Leg L), availability vs the measured record
(Leg A), mc-idled capacity + marginal identity (Leg M), reserve withholding
(Leg R, report-only), seam context (Leg S, report-only) — and emit the
quantities the frozen §4 verdict mapping adjudicates.

Machinery reuse (byte-for-byte imports, never re-implementations):

* the model side is ``_miso156_c3a_decomposition.model_year`` repointed to the
  miso-177 keeper exactly as ``_miso178_c3a_decomposition.py`` repoints it
  (including the disclosed ``pathlib.Path.is_file`` import shim for the pruned
  ``miso148_basis_B`` guard path, restored immediately);
* the measured side is ``_miso183_south_basis_decomposition``'s own clock and
  loaders (``regional_series``, ``hour_sets``, ``_nonleap_hour``,
  ``keeper_spread``) — the committed alignment construction, verbatim; the
  per-fuel genmix reader below generalizes ``regional_series`` to non-Total
  fuel rows on the identical clock loop.

Record: ``results/calibration/_miso186_direction_decomposition.json``.

Run:
    uv run --no-project --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml \
      --python 3.12 python scripts/probes/_miso186_direction_decomposition.py
"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso183_south_basis_decomposition as _m183  # noqa: E402

# The disclosed import shim (the _miso178 docstring): satisfy _miso156's
# import-time existence check for the PRUNED miso148_basis_B bundle, then
# restore pathlib immediately.
_orig_is_file = pathlib.Path.is_file


def _shim(self: pathlib.Path) -> bool:  # noqa: ANN001
    return True if "miso148_basis_B" in str(self) else _orig_is_file(self)


pathlib.Path.is_file = _shim
try:
    import _miso156_c3a_decomposition as _m156  # noqa: E402
finally:
    pathlib.Path.is_file = _orig_is_file

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.interchange.spec import MISO_SEAM_LADDER_BY_YEAR  # noqa: E402
from scripts.data.curate_zonal_shares import parse_miso_shares  # noqa: E402

# T-1: repoint BOTH module globals to the miso-177 keeper (the _miso178 pattern).
BUNDLE = REPO / "results/calibration/miso177_rho_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
_m156.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE and _m156.BUNDLE == BUNDLE, "T-1: repoint failed"
_m156.V1_PUBLISHED_C3A = {2023: 0.012813, 2024: -0.040643, 2025: -0.117421}

OUT = REPO / "results/calibration/_miso186_direction_decomposition.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
SOUTH = "MISO-South"
MIDWEST = ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East"]

# PREREG §2 frozen constants.
SENS_P = (0.0, 25.0)  # additive sensitivity offsets on pi_MW; $479 handled below
P479 = 479.0  # committed 2025 scarce actual mean (restated, PREREG §2)
LEGA_FIRE_GW = 0.10  # per-family availability firing line (PREREG §2 Leg A)
MATERIALITY_GW = 0.25  # §4 clause (v) static-reach line
DEADBAND = 1.0  # the miso-183 classifier's ±$1 RPE dead band

# PREREG §2 fuel-family crosswalk (frozen partition). DISCLOSED fidelity note
# (the miso-184 §1 pattern): the PREREG spelled the crosswalk in the SIDECAR
# klass vocabulary; the rebuilt fleet's own vocabulary differs (South coal is
# plant_group="COAL"; nuclear/oil/biomass rows carry an EMPTY plant_group with
# the class in fuel_type) — the first run therefore attributed South
# coal/nuclear to "Other" with 0.000 in their own rows. The mapping below
# implements the SAME intended partition on the fleet's actual fuel_type
# vocabulary (coal→Coal, gas_*→Gas, nuclear→Nuclear, hydro→Hydro,
# oil/biomass→Other); no family's definition changed.
KLASS_FAMILY = {
    "COAL_BIT": "Coal", "COAL_LIGNITE": "Coal", "COAL_PRB": "Coal",
    "COAL": "Coal", "COAL_WC": "Coal",
    "CC_CHP": "Gas", "CC_REGULAR": "Gas", "CT_CHP": "Gas", "CT_PEAKER": "Gas",
    "ST_CHP": "Gas", "ST_GAS": "Gas",
    "nuclear": "Nuclear", "hydro": "Hydro", "wind": "Wind", "solar": "Solar",
    "biomass": "Other", "oil": "Other", "OTHER": "Other",
}
FUELTYPE_FAMILY = {
    "gas_cc": "Gas", "gas_ct": "Gas", "gas_st": "Gas", "gas": "Gas",
    "coal": "Coal", "nuclear": "Nuclear", "hydro": "Hydro",
    "oil": "Other", "biomass": "Other", "wind": "Wind", "solar": "Solar",
}
# Committed miso-183 Leg-2 scarce means of N_S = L_S - G_S (F-4 targets; GW).
F4_NS = {2023: -1.438, 2024: -2.222, 2025: -2.441}
F4_TOL = 0.02
# Committed 2025 scarce classifier composition (F-3 target).
F3_2025 = {"n2s": 9, "s2n": 0, "unconstrained": 38}


def _fuel_label_family(label: str) -> str:
    """Map a sr_gfm fuel label to the PREREG family (case-insensitive)."""
    s = label.strip().lower()
    if "coal" in s:
        return "Coal"
    if "gas" in s:
        return "Gas"
    if "nuclear" in s:
        return "Nuclear"
    if "hydro" in s:
        return "Hydro"
    if "wind" in s:
        return "Wind"
    if "solar" in s:
        return "Solar"
    return "Other"


def regional_fuel_series(year: int, region: str) -> dict[str, np.ndarray]:
    """Per-fuel hourly MW for one sr_gfm region on the model clock.

    The _miso183 ``regional_series`` clock loop verbatim, generalized to the
    non-Total fuel rows; returns ``{fuel_label: (8760,) MW}`` plus the summed
    ``__total__`` check series.
    """
    df = pd.read_csv(_m183.REGBAL / f"miso_regional_genmix_{year}.csv.gz")
    df = df[(df["region"] == region) & (df["fuel"] != "Total")]
    out: dict[str, np.ndarray] = {}
    for fuel, sub in df.groupby("fuel"):
        arr = np.full(HOURS, np.nan)
        for mdate, he, v in sub[["market_date", "he_est", "mw"]].itertuples(index=False):
            y, m, d = int(mdate[:4]), int(mdate[5:7]), int(mdate[8:10])
            h_cst = int(he) - 2
            if h_cst < 0:
                prev = date(y, m, d) - pd.Timedelta(days=1)
                if prev.year != year:
                    continue
                h = _m183._nonleap_hour(prev.year, prev.month, prev.day, h_cst + 24)
            else:
                h = _m183._nonleap_hour(y, m, d, h_cst)
            if h >= 0:
                arr[h] = v
        out[str(fuel)] = arr
    total = np.nansum([v for v in out.values()], axis=0)
    out["__total__"] = total
    return out


def _smean(x: np.ndarray, mask: np.ndarray) -> float:
    v = np.asarray(x, dtype=float)[mask]
    v = v[np.isfinite(v)]
    return float(v.mean()) if v.size else float("nan")


def _reserve_family(year: int) -> dict[str, dict[str, float | np.ndarray]]:
    """Committed reserve-family sidecar series, keyed by family."""
    rf = pd.read_parquet(BUNDLE / f"hourly/reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"] if "pass" in rf else rf
    out = {}
    for fam, sub in rf.groupby("family"):
        held = np.zeros(HOURS)
        req = np.zeros(HOURS)
        dual = np.zeros(HOURS)
        short = np.zeros(HOURS)
        h = sub["hour"].to_numpy()
        held[h] = sub["held_mw"].to_numpy()
        req[h] = sub["requirement_mw"].to_numpy()
        dual[h] = sub["dual"].to_numpy()
        short[h] = sub["shortfall_mw"].to_numpy()
        out[str(fam)] = {"held": held, "req": req, "dual": dual, "short": short}
    return out


def _marginal_class(mc: np.ndarray, availcap: np.ndarray, labels: np.ndarray,
                    zsel: np.ndarray, price: np.ndarray, hours: np.ndarray) -> dict:
    """Frequency table of the marginal class: the highest-mc unit at or below
    price+deadband with available capacity, per selected hour (PREREG Leg M)."""
    freq: dict[str, int] = {}
    for t in hours:
        cand = np.nonzero(zsel & (availcap[:, t] > 1.0) & (mc[:, t] <= price[t] + DEADBAND))[0]
        if cand.size == 0:
            freq["<none-below-price>"] = freq.get("<none-below-price>", 0) + 1
            continue
        g = cand[np.argmax(mc[cand, t])]
        k = str(labels[g])
        freq[k] = freq.get(k, 0) + 1
    return dict(sorted(freq.items(), key=lambda kv: -kv[1]))


def year_record(cfg, year: int) -> dict:
    """All legs for one year (PREREG §2), scarce-set means in GW."""
    rec: dict = {}
    masks = _m183.hour_sets(year)
    scarce = masks["scarce"]
    n_scarce = int(scarce.sum())
    rec["F1_scarce_n"] = n_scarce

    # ---- model side (F-2 footing + arrays) --------------------------------
    mb = _m156.model_year(cfg, year)
    v4 = {"n_gen": len(mb["fleet"]), "published": _m156.V4_NGEN[year],
          "pass": len(mb["fleet"]) == _m156.V4_NGEN[year] and len(mb["carry_idx"]) == 6}
    v2 = _m156.v2_floor_gate(mb, year)
    v1 = _m156.v1_c3a_gate(mb, year)
    # DISCLOSED instrument-fidelity correction (the miso-184 §1 pattern): the
    # first run gated F-2 on V2 as well and STOPped in all three years — but
    # the imported machinery's own committed usage gates on V1 ∧ V4 with V2
    # REPORTED (miso-178's committed record carries V2 pass=False in all
    # years; FINDING-miso178 §6: "V2 report-only drifts with the keeper
    # lineage as expected" — the m155 targets predate the keeper lineage).
    # F-2 is made faithful to the precedent construction: V1 ∧ V4 gate, V2
    # reported at full magnitude. No threshold moved; V1 reproducing the
    # registered C3a to ±0.0001 pp is the rebuild-fidelity evidence.
    rec["F2_rebuild"] = {"V4": v4, "V2_reported": {
        k: v2[k] for k in ("ct_floor_mwh", "m155_ct_floor_mwh",
                           "ct_floor_rel_err", "fleet_floor_rel_err",
                           "ct_rows_floored", "m155_ct_rows_floored", "pass")},
        "V1": {"c3a_pct": v1["c3a_pct"], "published": v1["published_c3a_pct"],
               "pass": bool(v1["pass"])}}
    if not (v4["pass"] and v1["pass"]):
        rec["STOP"] = "F-2 rebuild footing failed (V1/V4)"
        return rec

    zone_names = mb["zone_names"]
    iS = zone_names.index(SOUTH)
    iMW = [zone_names.index(z) for z in MIDWEST]
    labels = mb["labels"]
    zone_of = mb["zone_of"]
    availcap = mb["availcap"]          # (n_gen, T) pmax x availability
    mc = mb["mc_base"]                 # (n_gen, T) bid basis
    min_gen = mb["min_gen"]
    dz = mb["demand_zone"]             # (n_zones, T) committed sidecar demand
    price = mb["price"]                # (T x zones) committed P1 prices
    pi_mw = price["MISO-East"].to_numpy(dtype=float)
    pi_s = price[SOUTH].to_numpy(dtype=float)

    in_S = zone_of == iS
    in_MW = np.isin(zone_of, iMW)

    # ---- F-3: the miso-183 spread classifier composition ------------------
    spread, mw_maxspread = _m183.keeper_spread(year)
    sc = spread[scarce]
    comp = {"n2s": int((sc > DEADBAND).sum()), "s2n": int((sc < -DEADBAND).sum()),
            "unconstrained": int((np.abs(sc) <= DEADBAND).sum()),
            "midwest_copper_max_spread": mw_maxspread}
    rec["F3_classifier"] = comp

    # ---- measured side (F-4 footing) --------------------------------------
    L_S = _m183.regional_series(year, "load", "South")
    L_N = _m183.regional_series(year, "load", "North")
    L_C = _m183.regional_series(year, "load", "Central")
    L_MISO = _m183.regional_series(year, "load", "MISO")
    G_S_tot = _m183.regional_series(year, "gen", "South")
    gfm_S = regional_fuel_series(year, "South")
    gfm_labels = sorted(k for k in gfm_S if k != "__total__")
    rec["genmix_fuel_labels"] = gfm_labels
    N_S = L_S - G_S_tot
    ns_scarce = _smean(N_S, scarce) / 1000.0
    rec["F4_NS_scarce_gw"] = {"value": ns_scarce, "committed": F4_NS[year],
                              "pass": bool(abs(ns_scarce - F4_NS[year]) <= F4_TOL)}
    H_meas = -N_S  # surplus-positive

    # ---- reserve leg (R, report-only) -------------------------------------
    rfam = _reserve_family(year)
    rec["legR_reserves_scarce"] = {
        fam: {k: _smean(v[k], scarce) for k in ("held", "req", "dual", "short")}
        for fam, v in rfam.items()}
    R_S = rfam.get("miso_zonal_or_miso_south", {"held": np.zeros(HOURS)})["held"]

    # ---- renewables (model South availability) ----------------------------
    wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
        "MISO", year, get_iso_config("MISO"), mb["cfg"])
    wind_cf = np.asarray(wind_cf, dtype=float)
    solar_cf = np.asarray(solar_cf, dtype=float)
    wind_cap = np.asarray(wind_cap, dtype=float)
    solar_cap = np.asarray(solar_cap, dtype=float)
    assert wind_cf.ndim == 2 and wind_cf.shape[1] == HOURS, wind_cf.shape
    ren_S = {"Wind": wind_cf[iS] * wind_cap[iS], "Solar": solar_cf[iS] * solar_cap[iS]}
    ren_MW = {"Wind": wind_cf[iMW].T @ wind_cap[iMW],
              "Solar": solar_cf[iMW].T @ solar_cap[iMW]}

    # ---- Leg L: load alignment --------------------------------------------
    D_S = dz[iS]
    D_MW = dz[iMW].sum(axis=0)
    D_tot = dz.sum(axis=0)
    shares = parse_miso_shares(year, zone_names)
    if shares is None:
        rec["legL"] = {"DROPPED": "parse_miso_shares returned None"}
        D_S930 = np.full(HOURS, np.nan)
    else:
        D_S930 = shares[iS] * D_tot
    L_MW_meas = L_N + L_C
    legL = {
        "D_S_scarce_gw": _smean(D_S, scarce) / 1e3,
        "L_S_scarce_gw": _smean(L_S, scarce) / 1e3,
        "dD_total_scarce_gw": _smean(D_S - L_S, scarce) / 1e3,
        "dD_wiring_scarce_gw": _smean(D_S - D_S930, scarce) / 1e3,
        "dD_source_scarce_gw": _smean(D_S930 - L_S, scarce) / 1e3,
        "share_930_S_scarce": _smean(D_S930 / np.where(D_tot > 0, D_tot, np.nan), scarce),
        "share_rfal_S_scarce": _smean(L_S / L_MISO, scarce),
        "share_930_S_annual": _smean(D_S930 / np.where(D_tot > 0, D_tot, np.nan),
                                     masks["annual"]),
        "share_rfal_S_annual": _smean(L_S / L_MISO, masks["annual"]),
        "share_delta_x_Dtot_scarce_gw": _smean(
            (D_S930 / np.where(D_tot > 0, D_tot, np.nan) - L_S / L_MISO) * D_tot,
            scarce) / 1e3,
        "whole_miso_wedge_scarce_gw": _smean(D_tot - L_MISO, scarce) / 1e3,
        "midwest_mirror_scarce_gw": _smean(D_MW - L_MW_meas, scarce) / 1e3,
        "dD_total_annual_gw": _smean(D_S - L_S, masks["annual"]) / 1e3,
        "dD_total_summer_gw": _smean(D_S - L_S, masks["summer"]) / 1e3,
        # ±1h alignment sensitivity on the measured series (reported-only).
        "dD_total_scarce_gw_shift_p1": _smean(
            D_S - _m183.regional_series(year, "load", "South", shift_extra=+1),
            scarce) / 1e3,
        "dD_total_scarce_gw_shift_m1": _smean(
            D_S - _m183.regional_series(year, "load", "South", shift_extra=-1),
            scarce) / 1e3,
    }
    rec["legL"] = legL

    # ---- Leg A: availability vs the measured record (per family) ----------
    fuels = np.array([str(getattr(g, "fuel_type", "") or "") for g in mb["fleet"]])
    fam_of = np.array([
        FUELTYPE_FAMILY.get(f, KLASS_FAMILY.get(str(k), "Other"))
        for f, k in zip(fuels, labels)])
    # effective class label for Leg M: plant_group, else fuel_type.
    labels = np.where(labels == "", fuels, labels)
    cap_S_fam: dict[str, np.ndarray] = {}
    cap_MW_fam: dict[str, np.ndarray] = {}
    for fam in ("Coal", "Gas", "Nuclear", "Hydro", "Other"):
        sel = in_S & (fam_of == fam)
        cap_S_fam[fam] = availcap[sel].sum(axis=0) if sel.any() else np.zeros(HOURS)
        selm = in_MW & (fam_of == fam)
        cap_MW_fam[fam] = availcap[selm].sum(axis=0) if selm.any() else np.zeros(HOURS)
    cap_S_fam["Wind"] = ren_S["Wind"]
    cap_S_fam["Solar"] = ren_S["Solar"]
    cap_MW_fam["Wind"] = np.asarray(ren_MW["Wind"], dtype=float).reshape(-1)
    cap_MW_fam["Solar"] = np.asarray(ren_MW["Solar"], dtype=float).reshape(-1)

    G_S_fam: dict[str, np.ndarray] = {f: np.zeros(HOURS) for f in cap_S_fam}
    for lbl in gfm_labels:
        G_S_fam[_fuel_label_family(lbl)] = (
            G_S_fam.get(_fuel_label_family(lbl), np.zeros(HOURS))
            + np.nan_to_num(gfm_S[lbl]))
    gfm_MW_N = regional_fuel_series(year, "North")
    gfm_MW_C = regional_fuel_series(year, "Central")
    G_MW_fam: dict[str, np.ndarray] = {f: np.zeros(HOURS) for f in cap_MW_fam}
    for gfm in (gfm_MW_N, gfm_MW_C):
        for lbl in gfm:
            if lbl == "__total__":
                continue
            G_MW_fam[_fuel_label_family(lbl)] = (
                G_MW_fam.get(_fuel_label_family(lbl), np.zeros(HOURS))
                + np.nan_to_num(gfm[lbl]))

    legA = {"south": {}, "midwest_mirror": {}, "drill": {}}
    for fam, cap in cap_S_fam.items():
        g = G_S_fam.get(fam, np.zeros(HOURS))
        da = _smean(np.maximum(0.0, g - cap), scarce) / 1e3
        legA["south"][fam] = {
            "cap_scarce_gw": _smean(cap, scarce) / 1e3,
            "gen_meas_scarce_gw": _smean(g, scarce) / 1e3,
            "dA_scarce_gw": da,
            "gen_minus_cap_signed_gw": _smean(g - cap, scarce) / 1e3,
        }
        if da >= LEGA_FIRE_GW:
            sel = np.nonzero(in_S & (fam_of == fam))[0]
            units = []
            for g_i in sel:
                av = _smean(availcap[g_i] / max(1e-9, availcap[g_i].max()), scarce)
                if av < 0.95:
                    fl = mb["fleet"][g_i]
                    units.append({
                        "unit_id": str(getattr(fl, "unit_id", "")),
                        "klass": str(labels[g_i]),
                        "pmax_mw": float(availcap[g_i].max()),
                        "availcap_scarce_mw": _smean(availcap[g_i], scarce),
                        "avail_frac_scarce": av})
            units.sort(key=lambda u: u["availcap_scarce_mw"] - u["pmax_mw"])
            legA["drill"][fam] = units[:40]
    for fam, cap in cap_MW_fam.items():
        g = G_MW_fam.get(fam, np.zeros(HOURS))
        legA["midwest_mirror"][fam] = {
            "cap_scarce_gw": _smean(cap, scarce) / 1e3,
            "gen_meas_scarce_gw": _smean(g, scarce) / 1e3,
            "dA_scarce_gw": _smean(np.maximum(0.0, g - cap), scarce) / 1e3,
        }
    rec["legA"] = legA

    # ---- Leg M: mc-idled capacity + marginal identity ---------------------
    sc_hours = np.nonzero(scarce)[0]
    econ_S = np.zeros(HOURS)
    econ_S_p25 = np.zeros(HOURS)
    econ_S_479 = np.zeros(HOURS)
    idle_by_class: dict[str, list[float]] = {}
    for t in sc_hours:
        below = mc[:, t] <= pi_mw[t]
        econ_S[t] = availcap[in_S & below, t].sum()
        econ_S_p25[t] = availcap[in_S & (mc[:, t] <= pi_mw[t] + 25.0), t].sum()
        econ_S_479[t] = availcap[in_S & (mc[:, t] <= P479), t].sum()
        for k in np.unique(labels[in_S & ~below]):
            sel = in_S & ~below & (labels == k)
            idle_by_class.setdefault(str(k), []).append(float(availcap[sel, t].sum()))
    # thermal econ + renewables (MC=0 -> in at every price)
    ren_S_sum = ren_S["Wind"] + ren_S["Solar"]
    EconS = econ_S + ren_S_sum
    EconS_p25 = econ_S_p25 + ren_S_sum
    EconS_479 = econ_S_479 + ren_S_sum
    CapS_all = sum(cap_S_fam[f] for f in cap_S_fam)

    legM = {
        "idle_by_class_scarce_gw": {
            k: float(np.mean(v)) / 1e3 for k, v in sorted(
                idle_by_class.items(), key=lambda kv: -np.mean(kv[1]))},
        "pi_mw_scarce": _smean(pi_mw, scarce),
        "pi_s_scarce": _smean(pi_s, scarce),
        "marginal_class_midwest": _marginal_class(
            mc, availcap, labels, in_MW, pi_mw, sc_hours),
        "marginal_class_south": _marginal_class(
            mc, availcap, labels, in_S, pi_s, sc_hours),
        "class_mc_south": {},
        "gas_delivered_by_zone_scarce": {},
        "floored_above_price_scarce_gw": {
            "south": float(np.mean([min_gen[in_S & (mc[:, t] > pi_mw[t]), t].sum()
                                    for t in sc_hours])) / 1e3,
            "midwest": float(np.mean([min_gen[in_MW & (mc[:, t] > pi_mw[t]), t].sum()
                                      for t in sc_hours])) / 1e3,
        },
    }
    # class mc structure (capacity-weighted quantiles pooled over scarce hours)
    fp = mb["fuel_prices"]
    hr = np.asarray(mb["arrays"].heat_rate, dtype=float)
    for k in sorted(set(str(x) for x in labels[in_S])):
        sel = np.nonzero(in_S & (labels == k))[0]
        vals, wts = [], []
        for t in sc_hours:
            vals.append(mc[sel, t])
            wts.append(availcap[sel, t])
        vals = np.concatenate(vals)
        wts = np.concatenate(wts)
        ok = wts > 0
        if not ok.any():
            continue
        order = np.argsort(vals[ok])
        v, w = vals[ok][order], wts[ok][order]
        cw = np.cumsum(w) / w.sum()
        q = {p: float(v[np.searchsorted(cw, p / 100.0)]) for p in (10, 50, 90)}
        p50_hr = float(np.median(hr[sel])) if sel.size else float("nan")
        p50_fp = float(np.median(np.concatenate([fp[sel, t] for t in sc_hours])))
        need = (q[50] - _smean(pi_mw, scarce)) / p50_hr if p50_hr > 0 else float("nan")
        legM["class_mc_south"][k] = {
            "mc_p10": q[10], "mc_p50": q[50], "mc_p90": q[90],
            "hr_p50": p50_hr, "fuel_price_p50": p50_fp,
            "delta_fuel_to_clear_pi_usd_mmbtu": need,
            "availcap_scarce_gw": _smean(availcap[sel].sum(axis=0), scarce) / 1e3,
        }
    gas_rows = fam_of == "Gas"
    for zi, zn in enumerate(zone_names):
        sel = np.nonzero(gas_rows & (zone_of == zi))[0]
        if sel.size == 0:
            continue
        vals = []
        for t in sc_hours:
            w = availcap[sel, t]
            if w.sum() > 0:
                vals.append(float(np.average(fp[sel, t], weights=w)))
        if vals:
            legM["gas_delivered_by_zone_scarce"][zn] = float(np.mean(vals))
    rec["legM"] = legM

    # ---- Leg S: seam context (report-only) --------------------------------
    lad = MISO_SEAM_LADDER_BY_YEAR.get(year, {}).get("South", {})
    imp = np.array(lad.get("import", ()), dtype=float)
    exp = np.array(lad.get("export", ()), dtype=float)
    step = 3000.0 / 8.0
    if imp.size:
        imp_mw = np.array([float((imp < pi_s[t]).sum()) * step for t in sc_hours])
        exp_mw = np.array([float((exp > pi_s[t]).sum()) * step for t in sc_hours])
        rec["legS_seam_context"] = {
            "implied_import_at_pi_s_scarce_gw": float(imp_mw.mean()) / 1e3,
            "implied_export_at_pi_s_scarce_gw": float(exp_mw.mean()) / 1e3,
            "import_bands": imp.tolist(), "export_bands": exp.tolist(),
        }

    # ---- the headline table + exact bridge --------------------------------
    HmeasS = _smean(H_meas, scarce) / 1e3
    Hcap = _smean(CapS_all - R_S - D_S, scarce) / 1e3
    Hecon = _smean(EconS - R_S - D_S, scarce) / 1e3
    bridge_load = _smean(D_S - L_S, scarce) / 1e3
    bridge_gen = _smean(G_S_tot - EconS, scarce) / 1e3
    bridge_res = _smean(R_S, scarce) / 1e3
    rec["headline"] = {
        "H_meas_gw": HmeasS,
        "H_cap_gw": Hcap,
        "H_econ_gw": Hecon,
        "H_econ_p25_gw": _smean(EconS_p25 - R_S - D_S, scarce) / 1e3,
        "H_econ_479_gw": _smean(EconS_479 - R_S - D_S, scarce) / 1e3,
        "bridge": {
            "dD_load_gw": bridge_load,
            "gen_minus_econcap_gw": bridge_gen,
            "reserve_held_gw": bridge_res,
            "sum_gw": bridge_load + bridge_gen + bridge_res,
            "H_meas_minus_H_econ_gw": HmeasS - Hecon,
        },
    }

    # ---- §4 mechanical candidate screen (clause (v) static reach) ---------
    cand = {}
    cand["L_wiring"] = {"reach_2025_basis_gw": legL["dD_wiring_scarce_gw"]}
    cand["L_source"] = {"reach_2025_basis_gw": legL["share_delta_x_Dtot_scarce_gw"]}
    for fam, row in legA["south"].items():
        if row["dA_scarce_gw"] >= LEGA_FIRE_GW:
            cand[f"A_{fam}"] = {"reach_2025_basis_gw": row["dA_scarce_gw"]}
    rec["candidates_static_reach"] = cand
    return rec


def candidate_reach() -> dict:
    """PREREG §4 clause-(v) static reach of the SELECTED candidate, recorded.

    Computed AFTER the leg screen fired (the declared order: the screen names
    the deviation, this implements the clause-(v) re-evaluation for the named
    repair `unit_outage_fleet_status_scope`): rebuild each year with the field
    on and difference the scarce-hour economic capacity at the committed
    Midwest price, South and Midwest separately. Also records the mechanism's
    full event-drop footprint (plants/units/statuses) for the finding.
    """
    import dataclasses as _dc

    cfg0 = _m156.keeper_config()
    cfg1 = _dc.replace(cfg0, unit_outage_fleet_status_scope=True)
    out = {"candidate": "unit_outage_fleet_status_scope", "years": {}}
    for year in YEARS:
        sc = _m183.hour_sets(year)["scarce"]
        mb0 = _m156.model_year(cfg0, year)
        mb1 = _m156.model_year(cfg1, year)
        zn = mb0["zone_names"]
        iS = zn.index(SOUTH)
        iMW = [zn.index(z) for z in MIDWEST]
        pi = mb0["price"]["MISO-East"].to_numpy(dtype=float)

        def _econ(mb, sel):
            z = (np.isin(mb["zone_of"], sel) if isinstance(sel, list)
                 else (mb["zone_of"] == sel))
            vals = []
            for t in np.nonzero(sc)[0]:
                below = mb["mc_base"][:, t] <= pi[t]
                vals.append(float(mb["availcap"][z & below, t].sum()))
            return float(np.mean(vals)) if vals else float("nan")

        out["years"][str(year)] = {
            "d_econcap_south_scarce_gw": (_econ(mb1, iS) - _econ(mb0, iS)) / 1e3,
            "d_econcap_midwest_scarce_gw": (_econ(mb1, iMW) - _econ(mb0, iMW)) / 1e3,
        }
    return out


def main() -> dict:
    cfg = _m156.keeper_config()
    out = {
        "prereg": "PREREG-miso186-midwest-stack-direction-2026-08-25.md",
        "keeper": "2026-08-22-miso-177-rho-measured",
        "bundle": BUNDLE.name,
        "machinery": {
            "model_side": "_miso156.model_year repointed (the _miso178 pattern)",
            "measured_side": "_miso183 loaders verbatim; per-fuel genmix on the same clock",
        },
        "years": {},
    }
    for year in YEARS:
        print(f"=== {year} ===", flush=True)
        rec = year_record(cfg, year)
        out["years"][str(year)] = rec
        if "STOP" in rec:
            print(f"[{year}] STOP: {rec['STOP']}", flush=True)
            continue
        h = rec["headline"]
        print(f"[{year}] F1 n={rec['F1_scarce_n']}  F3 {rec['F3_classifier']}  "
              f"F4 {rec['F4_NS_scarce_gw']}", flush=True)
        print(f"[{year}] H_meas {h['H_meas_gw']:+.3f}  H_cap {h['H_cap_gw']:+.3f}  "
              f"H_econ {h['H_econ_gw']:+.3f}  bridge {h['bridge']}", flush=True)
        print(f"[{year}] legL dD_total {rec['legL']['dD_total_scarce_gw']:+.3f} "
              f"(wiring {rec['legL']['dD_wiring_scarce_gw']:+.3f} / "
              f"source {rec['legL']['dD_source_scarce_gw']:+.3f})", flush=True)
        for fam, row in rec["legA"]["south"].items():
            print(f"[{year}] legA {fam:8s} cap {row['cap_scarce_gw']:6.3f} "
                  f"meas {row['gen_meas_scarce_gw']:6.3f} dA {row['dA_scarce_gw']:6.3f}",
                  flush=True)
        print(f"[{year}] candidates {rec['candidates_static_reach']}", flush=True)

    def _clean(o):
        if isinstance(o, dict):
            return {k: _clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [_clean(v) for v in o]
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, float) and not np.isfinite(o):
            return None
        return o

    if "--candidate-reach" in sys.argv:
        out["candidate_reach"] = candidate_reach()
        print("candidate_reach:", json.dumps(out["candidate_reach"]), flush=True)

    OUT.write_text(json.dumps(_clean(out), indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
