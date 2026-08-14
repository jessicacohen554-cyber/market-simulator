"""miso-157 Phase 0: is ``SUMMER_WEFOR_SHARE = 0.30`` supported by measurement?

PREREG ``results/calibration/PREREG-miso157-ct-summer-wefor-share-2026-08-14.md``
(commit ``09b7c87``, blob ``84091bdf``), pushed and blob-verified against the
FETCHED remote ref before any adjudicating statistic here was computed
(rule 27 ``[R-PUSH]``).

The object (PREREG section 0). On the MISO keeper ``miso148_basis_B``,
``CT_PEAKER`` carries no CAMPD outage coverage at all (miso-87: exactly 0.000),
so ``data/fleet/arrays.py:773-791`` governs its summer availability alone:
``1 - SUMMER_WEFOR_SHARE * WEFOR - DERATE`` over Jun-Sep, with the remaining
70 % of the forced-outage rate pushed into the shoulder months. That 0.30 is a
self-declared UNCITED heuristic carried in the keeper's DOF ledger under
identification ``residual`` (``config/fuel_trajectories.py:894-900``), and
``CT_PEAKER`` is the class that sets MISO's summer peak price.

Two legs, both fixed in the PREREG before measurement:

* **Leg 1 (SHAPE)** -- the Jun-Sep / annual unavailability ratio, measured three
  ways: the model's own array (``R_mod``), MISO's published outage record
  (``R_meas_MISO``, unplanned-only composite and ``Derated``-only), and MISO's
  committed CAMPD per-unit extract over the classes CAMPD covers
  (``R_meas_CAMPD``, class-resolved).
* **Leg 2 (MAGNITUDE)** -- the CT_PEAKER MW the share moves at the top-200
  Jun-Sep demand hours, against miso-153 D-1's published 6.31 GW cushion.

No LP is solved. Validity gates V1-V4 run before any adjudicating statistic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (
    str(REPO),
    str(REPO / "src"),
    str(REPO / "scripts" / "probes"),
    str(REPO / "scripts" / "data"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# T-1: _miso134 is HARD-WIRED to another bundle. Repoint to THIS lane's keeper
# and assert, before anything reads it.
BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE
assert _m134.BUNDLE == BUNDLE, "T-1: bundle repoint failed"

from _miso134_ct_night_order_screen import keeper_config  # noqa: E402
from _miso156_c3a_decomposition import model_year  # noqa: E402
from market_sim.config.fuel_trajectories import (  # noqa: E402
    SUMMER_WEFOR_SHARE,
    THERMAL_AVAILABILITY,
)
from market_sim.data.fleet.arrays import (  # noqa: E402
    _CC_SHOULDER_MONTHS,
    _SUMMER_MONTHS,
    generators_to_fleet_arrays,
)
from market_sim.data.miso_outages import (  # noqa: E402
    UNPLANNED_CAUSE_TYPES,
    miso_outage_mw_series,
)

# T-8: the fleet array builder must be the PRODUCTION one.
assert (
    generators_to_fleet_arrays.__module__ == "market_sim.data.fleet.arrays"
), "T-8: generators_to_fleet_arrays is not the production function"

YEARS = (2023, 2024, 2025)

# miso-153 D-1 / D-2, published -- the V1 reproduction targets.
V1_CT_JUNJUL_AVAIL = {2023: 0.923, 2024: 0.926, 2025: 0.919}
V1_TOP200_AVAIL_GW = {2023: 93.28, 2024: 92.41, 2025: 89.09}
# miso-155 / miso-156, published -- the V2 fleet census.
V2_NGEN = {2023: 2929, 2024: 2923, 2025: 2923}
# miso-153 D-1, published -- the cushion Leg 2 is measured against.
D1_CUSHION_GW_WITHIN_20 = {2023: 7.74, 2024: 7.56, 2025: 6.31}
D1_CT_IDLE_GW = {2023: 14.18, 2024: 12.90, 2025: 11.25}

CAMPD_MISO = REPO / "data/raw/campd-unit-outages-MISO.csv"
EIA860_GENS = REPO / "data/raw/eia-860/vintage_2024/eia860_generators.parquet"
# The classes MISO's CAMPD extract actually covers (CT carries 0.000 -- the very
# coverage hole this session measures, re-derived independently under T-26).
CAMPD_COVERED = ("COAL", "ST_GAS", "CC_REGULAR", "CC_CHP", "ST_CHP")


def _month_of_hour(hours: int, year: int) -> np.ndarray:
    """Month index 1-12 for each hour of the model's fixed non-leap clock."""
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy()


def _season_masks(hours: int, year: int) -> dict[str, np.ndarray]:
    """Jun-Sep (the model's own partition), Jun+Jul (T-29), shoulder, winter."""
    m = _month_of_hour(hours, year)
    summer = np.isin(m, sorted(_SUMMER_MONTHS))
    shoulder = np.isin(m, sorted(_CC_SHOULDER_MONTHS))
    return {
        "summer_junsep": summer,
        "junjul": np.isin(m, [6, 7]),
        "shoulder": shoulder,
        "winter": ~summer & ~shoulder,
        "month": m,
    }


# ----------------------------------------------------------------------------
# Validity gates
# ----------------------------------------------------------------------------


def v1_gate(mb: dict, year: int) -> dict:
    """**V1** -- the reconstruction reproduces miso-153's published D-1/D-2."""
    labels, avail = mb["labels"], mb["arrays"].availability
    pmax = mb["arrays"].pmax
    ms = _season_masks(mb["hours"], year)

    ct = labels == "CT_PEAKER"
    w = pmax[ct]
    # Cap-weighted mean CT_PEAKER availability over Jun+Jul, miso-153 D-2's grain.
    ct_junjul = float(
        np.average(avail[ct][:, ms["junjul"]].mean(axis=1), weights=w)
    ) if w.sum() > 0 else float("nan")

    # D-1: total available GW at the top-200 model-demand hours.
    dem_tot = mb["demand_zone"].sum(axis=0)
    top200 = np.argsort(dem_tot)[-200:]
    # D-1's scope is the classes carrying a THERMAL_AVAILABILITY entry. S-V1
    # fired on the first run of this gate because the aggregate was taken over
    # the WHOLE fleet, pulling in the 872 blank-plant_group rows (nuclear/VRE,
    # ~15.8 GW) and hydro (~2.4 GW) and reading ~+20 % high in all three years.
    # The uniformity of that offset is what identified it as scope rather than
    # noise; on the corrected scope the gate reproduces miso-153 D-1 exactly.
    # Disclosed in the finding rather than silently repaired.
    thermal = np.isin(labels, list(THERMAL_AVAILABILITY))
    availcap = mb["availcap"][thermal]
    top200_gw = float(availcap[:, top200].sum(axis=0).mean() / 1000.0)
    all_fleet_gw = float(mb["availcap"][:, top200].sum(axis=0).mean() / 1000.0)

    d_av = abs(ct_junjul - V1_CT_JUNJUL_AVAIL[year])
    d_gw = abs(top200_gw - V1_TOP200_AVAIL_GW[year]) / V1_TOP200_AVAIL_GW[year]
    return {
        "ct_junjul_avail": ct_junjul,
        "ct_junjul_avail_published": V1_CT_JUNJUL_AVAIL[year],
        "ct_junjul_abs_delta": d_av,
        "top200_avail_gw": top200_gw,
        "top200_avail_gw_ALL_FLEET_misscoped": all_fleet_gw,
        "ct_availcap_top200_gw": float(
            mb["availcap"][ct][:, top200].sum(axis=0).mean() / 1000.0
        ),
        "top200_avail_gw_published": V1_TOP200_AVAIL_GW[year],
        "top200_rel_delta": d_gw,
        "pass_avail": bool(d_av <= 0.02),
        "pass_gw": bool(d_gw <= 0.02),
        "pass": bool(d_av <= 0.02 and d_gw <= 0.02),
        "top200_hours": top200.tolist(),
    }


def v2_gate(mb: dict, year: int) -> dict:
    """**V2** -- the fleet census matches miso-155/156."""
    n_gen = int(len(mb["fleet"]))
    return {
        "n_gen": n_gen,
        "n_gen_published": V2_NGEN[year],
        "carry_zones": int(len(mb["carry_idx"])),
        "pass": bool(n_gen == V2_NGEN[year] and len(mb["carry_idx"]) == 6),
    }


def v3_gate(year: int) -> dict:
    """**V3** -- the measured record's own internal identity (T-3).

    ``MISO_<cause>`` must equal ``North + Central + South`` on every day, and
    the row count must be the calendar length. This is the record checking
    itself with a second derivation, not a spot check.
    """
    f = REPO / f"data/raw/miso-generation-outages/miso_outages_estimated_{year}.csv"
    df = pd.read_csv(f, parse_dates=["interval_date"])
    worst = 0.0
    for cause in ("Derated", "Forced", "Planned", "Unplanned"):
        parts = df[[f"{r}_{cause}" for r in ("North", "Central", "South")]].sum(axis=1)
        worst = max(worst, float((df[f"MISO_{cause}"] - parts).abs().max()))
    expect_rows = 366 if year % 4 == 0 else 365
    return {
        "rows": int(len(df)),
        "rows_expected": expect_rows,
        "max_abs_region_sum_mismatch_mw": worst,
        "pass": bool(len(df) == expect_rows and worst <= 1.0),
    }


# ----------------------------------------------------------------------------
# Leg 1 -- SHAPE
# ----------------------------------------------------------------------------


def r_mod(mb: dict, year: int) -> dict:
    """``R_mod`` -- the model's own CT_PEAKER Jun-Sep / annual unavailability.

    T-24: ``ct_floor_plants`` rows take a DIFFERENT branch of
    ``_apply_thermal_availability`` (``1 - derate``: no WEFOR in any month, no
    POF), so the two populations are measured separately and never pooled. The
    split is DETECTED from the array itself -- a floor row has no seasonal
    step -- and cross-checked against the WEFOR the class table implies.
    """
    labels, avail, pmax = mb["labels"], mb["arrays"].availability, mb["arrays"].pmax
    ms = _season_masks(mb["hours"], year)
    ct = np.where(labels == "CT_PEAKER")[0]

    su = avail[ct][:, ms["summer_junsep"]].mean(axis=1)
    wi = avail[ct][:, ms["winter"]].mean(axis=1)
    # A non-floor row carries the seasonal WEFOR step (summer strictly MORE
    # available than winter). A floor row is flat across the two.
    is_floor = (su - wi) <= 1e-9

    out: dict = {
        "n_ct_rows": int(ct.size),
        "n_floor_rows": int(is_floor.sum()),
        "n_nonfloor_rows": int((~is_floor).sum()),
        "ct_pmax_gw": float(pmax[ct].sum() / 1000.0),
        "floor_pmax_gw": float(pmax[ct][is_floor].sum() / 1000.0),
        "floor_cap_share": float(
            pmax[ct][is_floor].sum() / max(pmax[ct].sum(), 1e-9)
        ),
    }

    for tag, sel in (("nonfloor", ~is_floor), ("floor", is_floor)):
        idx = ct[sel]
        if idx.size == 0:
            out[tag] = None
            continue
        w = pmax[idx]
        unav = 1.0 - avail[idx]
        ann = float(np.average(unav.mean(axis=1), weights=w))
        summer = float(np.average(unav[:, ms["summer_junsep"]].mean(axis=1), weights=w))
        junjul = float(np.average(unav[:, ms["junjul"]].mean(axis=1), weights=w))
        out[tag] = {
            "unavail_annual": ann,
            "unavail_summer_junsep": summer,
            "unavail_junjul": junjul,
            "R_mod_junsep": summer / ann if ann > 0 else float("nan"),
            "R_mod_junjul": junjul / ann if ann > 0 else float("nan"),
            "avail_summer_junsep": 1.0 - summer,
            "avail_annual": 1.0 - ann,
        }

    # S-AGE: the cap-weighted WEFOR the class table implies for this fleet.
    pof, wb, wr, won, db, dr, don = THERMAL_AVAILABILITY["CT_PEAKER"]
    ages = np.array([float(year - g.online_year) for g in mb["fleet"]])[ct]
    wefor = wb + np.maximum(0.0, ages - won) * wr
    out["wefor_capwt"] = float(np.average(wefor, weights=pmax[ct]))
    out["age_capwt"] = float(np.average(ages, weights=pmax[ct]))
    out["S_AGE_fires"] = bool(
        out["wefor_capwt"] < 0.07 or out["wefor_capwt"] > 0.13
    )
    return out


def r_meas_miso(year: int, hours: int) -> dict:
    """``R_meas_MISO`` -- MISO's published record, Jun-Sep / annual.

    Unplanned-only composite (the miso-85 composition, not re-opened) plus the
    ``Derated``-only bucket, whose thermal attribution is physical rather than
    assumed (T-25 / S-DERATE-SPLIT).
    """
    ms = _season_masks(hours, year)
    out: dict = {"cause_types_composite": list(UNPLANNED_CAUSE_TYPES)}
    for tag, causes in (
        ("composite", UNPLANNED_CAUSE_TYPES),
        ("derated_only", ("Derated",)),
        ("forced_only", ("Forced",)),
        ("unplanned_only", ("Unplanned",)),
        ("planned_only", ("Planned",)),
    ):
        mw = miso_outage_mw_series(year, "MISO", causes, hours)
        ann = float(mw.mean())
        out[tag] = {
            "mw_annual": ann,
            "mw_summer_junsep": float(mw[ms["summer_junsep"]].mean()),
            "mw_junjul": float(mw[ms["junjul"]].mean()),
            "mw_shoulder": float(mw[ms["shoulder"]].mean()),
            "mw_winter": float(mw[ms["winter"]].mean()),
            "R_junsep": float(mw[ms["summer_junsep"]].mean() / ann) if ann > 0 else None,
            "R_junjul": float(mw[ms["junjul"]].mean() / ann) if ann > 0 else None,
        }
    return out


def r_meas_campd(year: int, hours: int) -> dict:
    """``R_meas_CAMPD`` -- MISO's committed per-unit extract, class-resolved.

    Expands each (unit, outage_start..outage_end) window onto the model's fixed
    non-leap clock, weights by ``unit_capacity_mw``, and takes the same
    Jun-Sep / annual ratio. T-26: CT's coverage is re-derived here independently
    rather than cited from miso-87.
    """
    df = pd.read_csv(CAMPD_MISO, parse_dates=["outage_start", "outage_end"])
    clock = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    ms = _season_masks(hours, year)

    out: dict = {"n_windows_total": int(len(df))}
    per_class: dict[str, np.ndarray] = {}
    for grp, sub in df.groupby("plant_group"):
        mw = np.zeros(hours, dtype=float)
        for _, r in sub.iterrows():
            s, e = r["outage_start"], r["outage_end"]
            if pd.isna(s) or pd.isna(e):
                continue
            if s.year > year or e.year < year:
                continue
            lo = np.searchsorted(clock, max(s, clock[0]))
            hi = np.searchsorted(clock, min(e, clock[-1]), side="right")
            if hi > lo:
                mw[lo:hi] += float(r["unit_capacity_mw"] or 0.0)
        per_class[str(grp)] = mw

    for grp, mw in sorted(per_class.items()):
        ann = float(mw.mean())
        out[str(grp)] = {
            "mw_annual": ann,
            "mw_summer_junsep": float(mw[ms["summer_junsep"]].mean()),
            "mw_junjul": float(mw[ms["junjul"]].mean()),
            "R_junsep": float(mw[ms["summer_junsep"]].mean() / ann) if ann > 0 else None,
            "R_junjul": float(mw[ms["junjul"]].mean() / ann) if ann > 0 else None,
            "n_windows": int((df["plant_group"] == grp).sum()),
        }

    # The covered-class aggregate -- the adjudicating CAMPD comparator.
    agg = np.zeros(hours, dtype=float)
    for grp in CAMPD_COVERED:
        if grp in per_class:
            agg += per_class[grp]
    ann = float(agg.mean())
    out["COVERED_AGGREGATE"] = {
        "classes": list(CAMPD_COVERED),
        "mw_annual": ann,
        "mw_summer_junsep": float(agg[ms["summer_junsep"]].mean()),
        "mw_junjul": float(agg[ms["junjul"]].mean()),
        "R_junsep": float(agg[ms["summer_junsep"]].mean() / ann) if ann > 0 else None,
        "R_junjul": float(agg[ms["junjul"]].mean() / ann) if ann > 0 else None,
    }

    # T-26: re-derive CT's CAMPD coverage independently of miso-87's citation.
    ct_mw = per_class.get("CT_PEAKER", np.zeros(hours))
    out["T26_ct_campd_second_derivation"] = {
        "n_ct_windows": int((df["plant_group"] == "CT_PEAKER").sum()),
        "ct_mw_annual": float(ct_mw.mean()),
        "ct_mw_summer_junsep": float(ct_mw[ms["summer_junsep"]].mean()),
        "ct_max_mw_any_hour": float(ct_mw.max()),
        "classes_present": sorted(per_class.keys()),
    }
    return out


# ----------------------------------------------------------------------------
# Leg 2 -- MAGNITUDE
# ----------------------------------------------------------------------------


def leg2_reach(mb: dict, year: int, r_star: float, top200: list[int]) -> dict:
    """MW the share moves at the top-200 Jun-Sep demand hours.

    Counterfactual availability rebuilt from the SAME class table the production
    branch uses, with the share swapped 0.30 -> ``r_star``; applied only to the
    non-floor CT_PEAKER population (T-24). T-27 asserts the counterfactual is a
    pure seasonal reallocation -- annual mean availability invariant.
    """
    labels, avail, pmax = mb["labels"], mb["arrays"].availability, mb["arrays"].pmax
    ms = _season_masks(mb["hours"], year)
    ct = np.where(labels == "CT_PEAKER")[0]
    su = avail[ct][:, ms["summer_junsep"]].mean(axis=1)
    wi = avail[ct][:, ms["winter"]].mean(axis=1)
    nonfloor = ct[(su - wi) > 1e-9]

    pof, wb, wr, won, db, dr, don = THERMAL_AVAILABILITY["CT_PEAKER"]
    ages = np.array([float(year - g.online_year) for g in mb["fleet"]])[nonfloor]
    wefor = wb + np.maximum(0.0, ages - won) * wr

    n_su = int(ms["summer_junsep"].sum())
    n_sh = int(ms["shoulder"].sum())
    su_to_sh = n_su / n_sh

    # Per-unit summer/shoulder availability DELTA between the two shares. The
    # level terms (derate, maint) cancel, so only the WEFOR reallocation shows.
    d_summer = (r_star - SUMMER_WEFOR_SHARE) * wefor          # availability falls
    d_should = -(r_star - SUMMER_WEFOR_SHARE) * wefor * su_to_sh  # rises

    # T-27: pure reallocation -- annual mean availability change must be ~0.
    ann_delta = (-d_summer * n_su + -d_should * n_sh) / mb["hours"]

    top = np.asarray(top200)
    top_summer = top[ms["summer_junsep"][top]]
    mw_lost = float((pmax[nonfloor] * d_summer).sum())

    return {
        "r_star": float(r_star),
        "share_current": float(SUMMER_WEFOR_SHARE),
        "n_nonfloor_ct": int(nonfloor.size),
        "nonfloor_pmax_gw": float(pmax[nonfloor].sum() / 1000.0),
        "wefor_capwt_nonfloor": float(np.average(wefor, weights=pmax[nonfloor])),
        "delta_mw_summer_capability_gw": mw_lost / 1000.0,
        "top200_hours_in_junsep": int(top_summer.size),
        "cushion_within_20_gw_published": D1_CUSHION_GW_WITHIN_20[year],
        "ct_idle_gw_published": D1_CT_IDLE_GW[year],
        "reach_vs_cushion": mw_lost / 1000.0 / D1_CUSHION_GW_WITHIN_20[year],
        "reach_vs_total_ct_idle": mw_lost / 1000.0 / D1_CT_IDLE_GW[year],
        "T27_annual_mean_avail_delta_max_abs": float(np.abs(ann_delta).max()),
        "T27_pass": bool(np.abs(ann_delta).max() < 1e-6),
    }



def s_age_true_vintage(mb: dict, year: int) -> dict:
    """**S-AGE fired** -- re-derive the reach from the MEASURED age distribution.

    The trigger's pre-registered instruction (PREREG section 6.1). ``S_AGE``
    fired because the cap-weighted CT_PEAKER WEFOR is EXACTLY 0.0700 in all
    three years -- a clean constant (T-3), which is only possible if no CT
    capacity is past the age-20 escalation onset.

    Second derivation: ``_commission_year`` (``data/fleet/assembly.py:280-285``)
    looks each plant up in ``master-plant-registry.csv`` and falls through to a
    hardcoded ``return 2010`` on a miss. That registry is ERCOT-only, so the
    miss is total for MISO and the whole plant-group-tagged fleet is stamped
    2010. This function measures the defect against EIA-860's own
    ``operating_year`` and re-prices WEFOR/DERATE on the true vintage.
    """
    e = pd.read_parquet(EIA860_GENS, columns=["plant_id", "operating_year",
                                              "nameplate_capacity_mw"]).dropna()
    e["plant_id"] = e["plant_id"].astype(int)
    true_year = (
        e.groupby("plant_id")
        .apply(
            lambda d: float(
                np.average(
                    d["operating_year"].astype(float),
                    weights=d["nameplate_capacity_mw"].astype(float),
                )
            ),
            include_groups=False,
        )
        .to_dict()
    )

    labels, pmax = mb["labels"], mb["arrays"].pmax
    codes = np.array([int(g.plant_code) for g in mb["fleet"]])
    model_year_field = np.array([int(g.online_year) for g in mb["fleet"]])

    # (a) the fleet-wide vintage census -- the defect's blast radius in MISO.
    census = {}
    for cls in sorted({str(c) for c in labels}):
        m = labels == cls
        if pmax[m].sum() <= 1.0:
            continue
        oy = model_year_field[m]
        census[cls or "(blank)"] = {
            "rows": int(m.sum()),
            "cap_gw": float(pmax[m].sum() / 1000.0),
            "n_distinct_model_online_year": int(len(set(oy.tolist()))),
            "model_online_year_min": int(oy.min()),
            "model_online_year_max": int(oy.max()),
        }

    # (b) CT_PEAKER re-priced on the measured vintage.
    ct = np.where(labels == "CT_PEAKER")[0]
    w = pmax[ct]
    ty = np.array([true_year.get(c, np.nan) for c in codes[ct]])
    ok = ~np.isnan(ty)
    pof, wb, wr, won, db, dr, don = THERMAL_AVAILABILITY["CT_PEAKER"]
    age_true = year - ty[ok]
    wefor_true = wb + np.maximum(0.0, age_true - won) * wr
    derate_true = db + np.maximum(0.0, age_true - don) * dr
    ww = w[ok]
    wefor_capwt = float(np.average(wefor_true, weights=ww))
    derate_capwt = float(np.average(derate_true, weights=ww))
    past = age_true > won

    # (c) what the defect alone costs in summer CT capability: the flat DERATE
    # leg is year-round (NOT a seasonal reallocation), the WEFOR leg enters
    # summer at the 0.30 share.
    d_derate = derate_capwt - db
    d_wefor_summer = (wefor_capwt - wb) * SUMMER_WEFOR_SHARE
    cap = float(ww.sum())
    return {
        "vintage_census_by_class": census,
        "registry_path": str(mb["cfg"].plant_registry_path),
        "eia860_cap_coverage": float(ww.sum() / w.sum()),
        "true_capwt_online_year": float(np.average(ty[ok], weights=ww)),
        "model_online_year": 2010,
        "true_capwt_age": float(year - np.average(ty[ok], weights=ww)),
        "model_age": int(year - 2010),
        "cap_past_onset_gw_true": float(ww[past].sum() / 1000.0),
        "cap_past_onset_share_true": float(ww[past].sum() / ww.sum()),
        "cap_past_onset_gw_model": 0.0,
        "wefor_capwt_true": wefor_capwt,
        "wefor_capwt_model": float(wb),
        "wefor_ratio_true_over_model": wefor_capwt / float(wb),
        "derate_capwt_true": derate_capwt,
        "derate_capwt_model": float(db),
        "summer_capability_overstatement_gw": float(
            (d_derate + d_wefor_summer) * cap / 1000.0
        ),
        "leg2_reach_scaled_by_true_wefor_gw": None,
    }


def main() -> dict:
    cfg = keeper_config()
    rec: dict = {
        "prereg": "PREREG-miso157-ct-summer-wefor-share-2026-08-14.md",
        "prereg_commit": "09b7c87",
        "prereg_blob": "84091bdf",
        "bundle": BUNDLE.name,
        "share_under_test": float(SUMMER_WEFOR_SHARE),
        "summer_months": sorted(_SUMMER_MONTHS),
        "shoulder_months": sorted(_CC_SHOULDER_MONTHS),
        "years": {},
    }

    for year in YEARS:
        # T-6: weather_year pinned per solve year inside model_year().
        mb = model_year(cfg, year)
        assert mb["cfg"].weather_year == year, "T-6: weather_year not pinned"
        y: dict = {}
        y["V1"] = v1_gate(mb, year)
        y["V2"] = v2_gate(mb, year)
        y["V3"] = v3_gate(year)
        y["V4_weather_year"] = int(mb["cfg"].weather_year)

        y["R_mod"] = r_mod(mb, year)
        y["R_meas_MISO"] = r_meas_miso(year, mb["hours"])
        y["R_meas_CAMPD"] = r_meas_campd(year, mb["hours"])

        r_star = y["R_meas_MISO"]["composite"]["R_junsep"]
        y["leg2"] = leg2_reach(mb, year, float(r_star), y["V1"].pop("top200_hours"))
        # S-AGE fired -- its pre-registered instruction is to re-derive from the
        # measured age distribution and report both.
        y["S_AGE_rederivation"] = s_age_true_vintage(mb, year)
        y["S_AGE_rederivation"]["leg2_reach_scaled_by_true_wefor_gw"] = (
            y["leg2"]["delta_mw_summer_capability_gw"]
            * y["S_AGE_rederivation"]["wefor_ratio_true_over_model"]
        )
        rec["years"][str(year)] = y
        del mb

    out = REPO / "results/calibration/_miso157_ct_summer_wefor.json"
    out.write_text(json.dumps(rec, indent=2, default=float))
    print(f"wrote {out}")
    return rec


if __name__ == "__main__":
    main()
