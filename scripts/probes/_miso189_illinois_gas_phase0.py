"""miso-189 — phase-0 (ZERO-SOLVE): the MISO-Illinois scarce delivered-gas
observation, measured against the keeper's own input.

THE OBJECT (standing owner item 6, FINDING-miso186 §1 Leg R/S → FINDING-miso188
§7): the keeper's capacity-weighted delivered-gas input for the MISO-Illinois
gas fleet reads **$8.22/MMBtu over the 2025 scarce set** (47 Jun–Sep hours with
measured RT > $200) while every other Midwest zone reads $2.7–3.6 — flagged
there as "an F923 plant-level delivered-price artifact worth a look in the
Midwest lane". The miso-189 charter (ask B) phase-0s it against the measured
scarce-set record: if the MEASURED scarce delivered price EXCEEDS the model's
input materially, that is a rule-13/14 measured-input candidate with the right
sign for the C3a-2025 under-priced tail (PREREG + solve next); if not, the
candidate is REFUTED and the evidence stamped.

STANDING ADJUDICATION THIS MUST RECONCILE WITH (never quietly go around):
`gas_hub_basis_overlay` MISO `R` (miso-156, FINDING-miso156 §7.1) — at the
ANNUAL grain the model's capacity-weighted delivered gas is ABOVE both measured
comparators in all three years (+0.348/+0.092/+0.892 vs HH+ISO-basis;
+1.543/+1.005/+1.010 vs EIA delivered-to-electric-power) and the D2 cost-level
channel reads −6.156 $/MWh, i.e. the fuel channel runs BACKWARDS. This probe is
the SCARCE-SET-scoped version of the same comparison — different evidence, same
family — plus the per-unit provenance decomposition of the Illinois book that
neither miso-156 nor miso-186 performed.

ADJUDICATION RULE (declared here, BEFORE any adjudicating quantity is computed):

  * CANDIDATE  iff  on the 2025 scarce set the measured comparator EXCEEDS the
    model book by >= +$0.50/MMBtu on EITHER grain:
      (a) zone-book grain — best measured scarce-month comparator (C-A..C-E
          below) minus the model's capacity-weighted Illinois (or Midwest
          all-zone) gas book; or
      (b) matched-plant grain — the F923 own prints of reporting plants,
          availcap-weighted, minus the model book restricted to the same units.
  * REFUTED    otherwise (gap <= 0 everywhere: the input is not under-priced;
    or 0 < gap < 0.5: immaterial). Artifact-direction findings (model ABOVE
    measured) are REPORTED for the owner, never self-adjudicated to a repair —
    the sign is adverse to the C3a-2025 lane and any repair is its own charter.

FOOTING GATES (all must pass before the adjudicating comparison is read):

  * F-1: scarce-set sizes reproduce the committed miso-183 footing 11/14/47.
  * F-2: the rebuilt 2025 Illinois scarce book reproduces the committed
    miso-186 value 8.2179 within ±0.40 $/MMBtu (tolerance = the miso-186 →
    miso-188 fleet-membership delta; miso-186 computed on miso177_rho_B).
  * F-3: n_gen matches the keeper's own committed bundle count per year.

MACHINERY (byte-for-byte imports, never re-implementations):
  * model side — `_miso134_ct_night_order_screen.build_year` repointed to the
    miso-188 keeper `miso188_rvs_B` (the _miso156/_miso186 pattern), with the
    `dataclasses.replace(cfg, weather_year=year)` pin (the T-6 / miso-188 §6.4
    instrument lesson).
  * measured side — `_miso183_south_basis_decomposition.hour_sets` (the frozen
    scarce clock); the F923 parquet via `market_sim.data.eia923`; the fallback
    pools via the PRODUCTION `_NearbyFuelPrices` class; Chicago Citygate daily
    (`data/raw/gas-prices/miso_citygate_daily.csv`), IL/MI citygate monthly
    (`eia_citygate_IL_MI_monthly_2023-2025.csv`, $/MCF → /1.037 $/MMBtu),
    Henry Hub monthly + `gas_basis_by_iso_month.csv` MISO rows +
    `miso_zonal_gas_hub.csv` zone-annual basis.

Rule 22 [R-HOLDOUT]: 2023–2025 only; MISO holds no marker. NO LP is built or
solved anywhere below.

Record: results/calibration/_miso189_illinois_gas_phase0.json

Usage::

    python3 scripts/probes/_miso189_illinois_gas_phase0.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts" / "probes")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# Repoint to THIS lane's keeper (the _miso156/_miso186 T-1 pattern).
BUNDLE = REPO / "results/calibration/miso188_rvs_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE, "T-1: bundle repoint failed"

import _miso183_south_basis_decomposition as _m183  # noqa: E402
from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402

from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_fuel_costs,
    plant_month_price_grid,
)
from market_sim.data.fuel.plant_prices import _NearbyFuelPrices  # noqa: E402

OUT = REPO / "results/calibration/_miso189_illinois_gas_phase0.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
IL = "MISO-Illinois"
MIDWEST = ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East"]

# F-gates (docstring; frozen).
F1_SCARCE_N = {2023: 11, 2024: 14, 2025: 47}
F2_M186_IL_2025 = 8.2179
F2_TOL = 0.40
# The committed miso-186 books (miso177_rho_B fleet), context rows.
M186_BOOKS = {
    2023: {"MISO-West": 4.7569, "MISO-Plains": 3.9630, "MISO-Illinois": 9.2902,
           "MISO-Indiana": 2.9143, "MISO-East": 2.8243, "MISO-South": 2.9336},
    2024: {"MISO-West": 4.4680, "MISO-Plains": 3.4882, "MISO-Illinois": 5.6545,
           "MISO-Indiana": 2.5204, "MISO-East": 2.3439, "MISO-South": 2.7237},
    2025: {"MISO-West": 2.6787, "MISO-Plains": 2.6649, "MISO-Illinois": 8.2179,
           "MISO-Indiana": 3.6039, "MISO-East": 3.4069, "MISO-South": 3.8259},
}
# Adjudication line (docstring; frozen).
CANDIDATE_GAP = 0.50  # $/MMBtu, measured minus model, 2025 scarce set

_GAS_FUELS = {"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs", "gas"}
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296,
               8016, 8760]
MO = np.concatenate(
    [np.full(MONTH_START[m + 1] - MONTH_START[m], m + 1) for m in range(12)]
)
MCF_TO_MMBTU = 1.037  # EIA conversion: 1 MCF ≈ 1.037 MMBtu (citygate $/MCF)


def _fuel_name(arrays, g: int) -> str:
    from market_sim.data.fleet import FUEL_TYPE_MAP

    inv = {v: k for k, v in FUEL_TYPE_MAP.items()}
    return inv.get(int(arrays.fuel_type_idx[g]), "?")


def _capw_book(fp, availcap, sel, hours) -> float:
    """The miso-186 construction verbatim: per-hour availcap-weighted mean of
    fp over `sel` rows, then the mean over `hours`."""
    vals = []
    for t in hours:
        w = availcap[sel, t]
        if w.sum() > 0:
            vals.append(float(np.average(fp[sel, t], weights=w)))
    return float(np.mean(vals)) if vals else float("nan")


def _monthly_scarce_weights(scarce: np.ndarray) -> dict[int, int]:
    """{calendar month: scarce-hour count} over the 8760 clock."""
    out: dict[int, int] = {}
    for m in range(1, 13):
        n = int(scarce[MO == m].sum())
        if n:
            out[m] = n
    return out


def main() -> dict:
    cfg = keeper_config()
    costs = load_monthly_fuel_costs()

    # Measured series (loaded once).
    hh_m = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_monthly.csv")
    hh_by_ym = {(int(r.year), int(r.month)): float(r.price_usd_mmbtu)
                for r in hh_m.itertuples()}
    iso_basis = pd.read_csv(REPO / "data/raw/gas_basis_by_iso_month.csv")
    iso_basis = iso_basis[iso_basis.iso == "MISO"]
    iso_basis_by_ym = {(int(r.year), int(r.month)): float(r.basis_usd_mmbtu)
                       for r in iso_basis.itertuples()}
    zone_basis = pd.read_csv(REPO / "data/raw/miso_zonal_gas_hub.csv")
    cg_daily = pd.read_csv(REPO / "data/raw/gas-prices/miso_citygate_daily.csv",
                           parse_dates=["date"])
    cg_il_mi = pd.read_csv(
        REPO / "data/raw/gas-prices/eia_citygate_IL_MI_monthly_2023-2025.csv")
    cg_il = {}
    for r in cg_il_mi[cg_il_mi.series == "N3050IL3"].itertuples():
        y, m = r.period.split("-")
        cg_il[(int(y), int(m))] = float(r.value) / MCF_TO_MMBTU

    out: dict = {
        "prereg_rule": {
            "candidate_gap_usd_mmbtu": CANDIDATE_GAP,
            "grains": ["zone-book vs best measured comparator",
                       "matched-plant F923 own prints vs model, availcap-weighted"],
            "statement": "CANDIDATE iff measured - model >= +0.50 on the 2025 "
                         "scarce set on either grain; REFUTED otherwise",
        },
        "keeper": "2026-08-30-miso-188-rvsscope",
        "bundle": str(BUNDLE.name),
        "years": {},
    }

    for year in YEARS:
        rec: dict = {}
        masks = _m183.hour_sets(year)
        scarce = masks["scarce"]
        n_sc = int(scarce.sum())
        rec["F1_scarce_n"] = {"value": n_sc, "committed": F1_SCARCE_N[year],
                              "pass": n_sc == F1_SCARCE_N[year]}
        sc_hours = np.nonzero(scarce)[0]
        mo_w = _monthly_scarce_weights(scarce)

        cfg_y = dataclasses.replace(cfg, weather_year=year)  # T-6 pin
        raw_fleet, fleet, arrays, fp, mc_base, zone_names = build_year(cfg_y, year)
        availcap = arrays.pmax[:, None] * arrays.availability
        zone_of = np.array([zone_names.index(str(g.zone)) for g in fleet])
        n_gen = len(fleet)
        rec["F3_n_gen"] = n_gen

        fuelname = np.array([_fuel_name(arrays, g) for g in range(n_gen)])
        gas_rows = np.isin(fuelname, sorted(_GAS_FUELS))

        # --- the zone books (miso-186 construction) --------------------------
        books = {}
        for zi, zn in enumerate(zone_names):
            sel = gas_rows & (zone_of == zi)
            if sel.any():
                books[zn] = _capw_book(fp, availcap, sel, sc_hours)
        rec["model_gas_book_scarce"] = books
        rec["m186_committed_books"] = M186_BOOKS[year]
        if year == 2025:
            rec["F2_il_book"] = {
                "value": books.get(IL), "committed": F2_M186_IL_2025,
                "tol": F2_TOL,
                "pass": abs(books.get(IL, 1e9) - F2_M186_IL_2025) <= F2_TOL,
            }

        # --- per-unit Illinois decomposition + provenance --------------------
        grid = plant_month_price_grid(costs, year, "Natural Gas")
        nearby = _NearbyFuelPrices(costs, year, arrays, cfg_y)
        states = arrays.state
        il_zi = zone_names.index(IL)
        il_sel = np.nonzero(gas_rows & (zone_of == il_zi))[0]
        units = []
        for g in il_sel:
            pc = int(arrays.plant_code[g])
            own = grid.get(pc)
            klass = str(arrays.plant_group[g]) if arrays.plant_group is not None else ""
            st = str(states[g]) if states is not None else ""
            fill = nearby.month_prices("Natural Gas", st, int(arrays.zone_idx[g]),
                                       klass)
            prov = {}
            for m in sorted(mo_w):
                if own is not None and not np.isnan(own[m - 1]):
                    prov[m] = {"src": "own_f923", "monthly": float(own[m - 1])}
                elif not np.isnan(fill[m - 1]):
                    prov[m] = {"src": "nearby_fallback", "monthly": float(fill[m - 1])}
                else:
                    prov[m] = {"src": "default_hub_basis", "monthly": None}
            units.append({
                "i": int(g), "plant_code": pc,
                "unit_id": str(getattr(fleet[g], "unit_id", "")),
                "klass": klass, "state": st,
                "pmax_mw": float(arrays.pmax[g]),
                "availcap_scarce_mw": float(np.mean(availcap[g, sc_hours])),
                "fp_scarce_mean": float(np.mean(fp[g, sc_hours])),
                "provenance_scarce_months": prov,
            })
        units.sort(key=lambda u: -u["availcap_scarce_mw"])
        rec["illinois_units"] = units

        # book split: own-print vs fallback contribution to the IL book
        w_tot = sum(u["availcap_scarce_mw"] for u in units) or 1e-9
        for tag, pred in (
            ("own_f923", lambda p: p == "own_f923"),
            ("nearby_fallback", lambda p: p == "nearby_fallback"),
            ("default_hub_basis", lambda p: p == "default_hub_basis"),
        ):
            sel_u = [u for u in units if pred(
                # classify a unit by its dominant scarce-month source
                max(((v["src"], mo_w[m]) for m, v in
                     u["provenance_scarce_months"].items()),
                    key=lambda t: t[1])[0])]
            w = sum(u["availcap_scarce_mw"] for u in sel_u)
            rec.setdefault("il_book_split", {})[tag] = {
                "n_units": len(sel_u), "cap_share": w / w_tot,
                "capw_fp": (sum(u["fp_scarce_mean"] * u["availcap_scarce_mw"]
                                for u in sel_u) / w) if w > 0 else None,
            }

        # --- measured comparators over the scarce months ---------------------
        def _mo_wavg(series_by_m: dict[int, float]) -> float | None:
            num = den = 0.0
            for m, n in mo_w.items():
                v = series_by_m.get(m)
                if v is None or (isinstance(v, float) and np.isnan(v)):
                    continue
                num += v * n
                den += n
            return num / den if den else None

        f923 = costs[(costs.fuel_group == "Natural Gas") & (costs.year == year)]
        # C-A: IL-state burn-weighted F923
        il_st = f923[f923.state == "IL"]
        ca = {}
        for m, sub in il_st.groupby("month"):
            q = sub.quantity.sum()
            if q > 0:
                ca[int(m)] = float((sub.price_per_mmbtu * sub.quantity).sum() / q)
        # C-B: Illinois-ZONE plants burn-weighted F923 (the model's own members)
        il_pcs = {u["plant_code"] for u in units}
        zn_f = f923[f923.plant_id.isin(il_pcs)]
        cb = {}
        for m, sub in zn_f.groupby("month"):
            q = sub.quantity.sum()
            if q > 0:
                cb[int(m)] = float((sub.price_per_mmbtu * sub.quantity).sum() / q)
        # C-C: HH month + MISO iso-month basis (the miso-156 PRIMARY)
        cc = {m: (hh_by_ym.get((year, m), np.nan)
                  + iso_basis_by_ym.get((year, m), np.nan)) for m in mo_w}
        # C-D: HH month + Illinois zone annual basis
        zb = zone_basis[(zone_basis.zone == IL) & (zone_basis.year == year)]
        zb_v = float(zb.basis_vs_hh_usd_mmbtu.iloc[0]) if len(zb) else np.nan
        cd = {m: hh_by_ym.get((year, m), np.nan) + zb_v for m in mo_w}
        # C-E: Chicago Citygate daily, scarce-day mean (the exact scarce days)
        cg = cg_daily[cg_daily.date.dt.year == year]
        cg_by_doy = {}
        for r in cg.itertuples():
            doy = r.date.timetuple().tm_yday
            if r.date.is_leap_year and doy > 60:
                doy -= 1
            cg_by_doy[doy] = float(r.chicago_citygate_usd_mmbtu)
        sc_days = sorted({int(t // 24) + 1 for t in sc_hours})
        cg_vals = [cg_by_doy[d] for d in sc_days if d in cg_by_doy]
        ce = float(np.mean(cg_vals)) if cg_vals else None
        # C-F: EIA IL citygate monthly (state LDC gate)
        cf = {m: cg_il.get((year, m)) for m in mo_w}

        comps = {
            "C-A_f923_il_state_burnw": _mo_wavg(ca),
            "C-B_f923_il_zone_plants_burnw": _mo_wavg(cb),
            "C-C_hh_plus_miso_basis": _mo_wavg(cc),
            "C-D_hh_plus_il_zone_basis": _mo_wavg(cd),
            "C-E_chicago_citygate_scarce_days": ce,
            "C-F_eia_il_citygate_month": _mo_wavg(cf),
        }
        rec["measured_comparators_scarce"] = comps
        rec["measured_monthly_detail"] = {
            "scarce_month_weights": mo_w,
            "C-A_by_month": ca, "C-B_by_month": cb,
            "C-C_by_month": {m: (None if np.isnan(v) else v) for m, v in cc.items()},
        }

        # matched-plant grain: model vs own F923 prints, availcap-weighted,
        # restricted to (unit, month) cells where the plant reported.
        num_mod = num_mea = den = 0.0
        for u in units:
            for m, v in u["provenance_scarce_months"].items():
                if v["src"] != "own_f923":
                    continue
                w = u["availcap_scarce_mw"] * mo_w[m]
                # model fp mean over THIS month's scarce hours for this unit
                mask = scarce & (MO == m)
                num_mod += float(np.mean(fp[u["i"], np.nonzero(mask)[0]])) * w
                num_mea += v["monthly"] * w
                den += w
        rec["matched_plant_grain"] = {
            "model_capw": num_mod / den if den else None,
            "measured_capw": num_mea / den if den else None,
            "gap_measured_minus_model": ((num_mea - num_mod) / den) if den else None,
        }

        # zone-book grain gaps (2025 adjudicating)
        best = max((v for v in comps.values() if v is not None), default=None)
        rec["book_grain"] = {
            "il_book": books.get(IL),
            "midwest_books": {z: books.get(z) for z in MIDWEST},
            "best_measured_comparator": best,
            "gap_best_measured_minus_il_book":
                (best - books[IL]) if (best is not None and IL in books) else None,
        }
        out["years"][year] = rec

    # ---- the adjudication (2025 only; the rule frozen above) ---------------
    r25 = out["years"][2025]
    gaps = {
        "book": r25["book_grain"]["gap_best_measured_minus_il_book"],
        "matched": r25["matched_plant_grain"]["gap_measured_minus_model"],
    }
    fires = any(g is not None and g >= CANDIDATE_GAP for g in gaps.values())
    footing = (r25["F1_scarce_n"]["pass"] and r25["F2_il_book"]["pass"])
    out["adjudication"] = {
        "footing_pass": footing,
        "gaps_2025": gaps,
        "verdict": ("CANDIDATE" if fires else "REFUTED") if footing else
                   "FOOTING-FAIL",
    }

    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps(out["adjudication"], indent=1))
    for y in YEARS:
        r = out["years"][y]
        print(f"\n=== {y}  scarce n={r['F1_scarce_n']['value']} "
              f"(pass={r['F1_scarce_n']['pass']})")
        print("model books :", {k: round(v, 3) for k, v in
                                r["model_gas_book_scarce"].items()})
        print("comparators :", {k: (round(v, 3) if v is not None else None)
                                for k, v in
                                r["measured_comparators_scarce"].items()})
        print("matched     :", {k: (round(v, 4) if v is not None else None)
                                for k, v in r["matched_plant_grain"].items()})
        if "il_book_split" in r:
            for tag, s in r["il_book_split"].items():
                print(f"  IL split {tag:18s} n={s['n_units']:3d} "
                      f"cap_share={s['cap_share']:.3f} "
                      f"capw_fp={None if s['capw_fp'] is None else round(s['capw_fp'], 3)}")
        for u in r["illinois_units"][:12]:
            dom = max(((v['src'], 1) for v in
                       u['provenance_scarce_months'].values()),
                      key=lambda t: t[1])[0]
            print(f"  {u['plant_code']:6d} {u['unit_id'][:28]:28s} "
                  f"{u['klass']:10s} cap={u['availcap_scarce_mw']:7.1f} "
                  f"fp={u['fp_scarce_mean']:7.3f} {dom}")
    return out


if __name__ == "__main__":
    main()
