"""miso-215 — THE ``phys_*`` COVERAGE GAP ON THE INTERMEDIATE-DUTY COHORTS (phase 0, zero-solve).

Executes ``results/calibration/PREREG-miso215-intermediate-phys-2026-09-05.md``
(pushed BLIND at ``cae766ec``) on the miso-213 keeper's committed sidecars and
the HEAD fleet chain. **No LP is solved.**

  M-1   SCOPE. Membership, capacity, econ tranche count, cap-weighted offer /
        physical-leg / markup heat rates, cap-weighted resolved delivered fuel
        and CAMPD energy for ``CT_INTERMEDIATE``, ``CC_INTERMEDIATE`` and
        ``ST_GAS_INTERMEDIATE`` and for their three parent cohorts.
  M-2   BAND SCOPE. The price-taking static reach of repricing each cohort into
        the ``gas_offer_net_revenue_margin`` form at the parent class's frozen
        p50s, measured ECON-ONLY and ECON+PEAK, with the peak leg's own offer
        shift and C3c tail exposure.
  M-3   ANCHOR GRAIN. ``GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"] = 3.0492`` is
        derived from ``data.fuel.trajectories._gas_series`` (ISO-level Henry
        Hub x seasonality x daily shape) while the fleet is priced by the
        per-plant EIA-923 PRINT path. Measured against each cohort-year's own
        cap-weighted resolved delivered fuel and against measured annual Henry
        Hub. This is the BASIS grain — a DIFFERENT question from the ZONAL
        grain already adjudicated ``I`` on MISO (miso-119/120), which is NOT
        re-tested here.
  M-3b  BORROWING VALIDITY. Each cohort's OWN measured marginal-HR multiplier
        (per-unit steady-state input-output slope over the class base HR,
        cap-weighted) against the pooled parent p50 an arm would borrow. The
        frozen rule-23 artifact carries MODEL-PLANT-GROUP rows only, so no
        ``*_INTERMEDIATE`` p50 exists; this is a DIAGNOSTIC of the borrowing,
        never a re-derivation, and nothing is written back.
  M-3c  ANCHOR-ARTEFACT DECOMPOSITION. The same static reach with the anchor
        replaced, per cohort-year, by that cohort-year's own cap-weighted
        resolved delivered fuel — a counterfactual diagnostic, never an arm.
        The share of the |screen delta| that vanishes is the share of the reach
        that is the anchor's position in the fuel distribution rather than the
        offer FORM.
  M-4   RULE-19 CENSUS. What already prices these cohorts' econ tranches: the
        P1 startup amortization and its cap-weighted $/MWh, the committed band,
        the armed reliability-floor limbs, and the keeper's own D-2 / D-4 rows
        and C8 forced shares.

INSTRUMENT LIMITS, DISCLOSED (PREREG §2): the keeper ships no ``unit_hourly/``
or ``dispatch/``, so plant-grain model merit is a PRICE-TAKING STATIC SCREEN on
``mc_base`` (no P1 startup adder) against the keeper's own committed P1 zone
prices — a BOUND, not the LP (miso-214 §1 measured it at 1.41-1.43x the LP's own
CT class energy). A price-taking screen holds the price FIXED, so cross-class
backfill (CT displaced -> CC picks it up) is INVISIBLE to it; the K-1 exposure
is therefore reported as an un-instrumented risk, not as a measurement. CAMPD is
read from ``data/raw/campd-unit-level/`` directly on the model's fixed non-leap
8760 clock with no timezone shift (the established MISO-probe convention),
CAMPD GROSS against the model's NET tranches unadjusted. The EIA-923 print is a
MONTHLY ALL-IN delivered cost applied to an HOURLY decision — the
average-vs-marginal convention (miso-212 §8) is OWNER-COURT and untouched.

Usage::

    PYTHONPATH=src python3 scripts/probes/_miso215_intermediate_phys_phase0.py

Record: ``results/calibration/_miso215_intermediate_phys.json``.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402
import _miso207_bound_the_shoulder as m207  # noqa: E402
import _miso208_find_the_supply as m208  # noqa: E402
import _miso211_rdt_binding_state as _m211  # noqa: E402  (re-points to miso-210 at import)

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso214_ct_peaker_conduct_phase0 import (  # noqa: E402
    HUB_TO_ZONES,
    _band,
    _r,
    _wshare,
    io_fit,
    keeper_price,
)
from market_sim.config.constants import (  # noqa: E402
    GAS_OFFER_MARGIN_ANCHOR_BY_ISO,
    HOURS_PER_YEAR,
)
from market_sim.config.iso_configs import RELIABILITY_FLOOR_REGISTRY  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    cc_intermediate_plants,
    ct_intermediate_plants,
    st_gas_intermediate_plants,
)
from market_sim.data.fuel.trajectories import _gas_series  # noqa: E402
from market_sim.data.outages import ST_GAS_PEAKER_PLANTS  # noqa: E402
from market_sim.model.commitment import _startup_cost  # noqa: E402

# T-1: re-point EVERY module global to the miso-213 keeper, AFTER the last
# import, because `_miso211` (pulled in transitively by `_miso212`, which
# `_miso214` imports) re-points `_m134.BUNDLE` to ITS OWN keeper,
# `miso210_clock_B`, at module scope. miso-214 §9 disclosed running its first
# three-year launch on the CONTROL config for exactly this reason; the assert
# below is what makes the repeat impossible.
KEEPER = REPO / "results/calibration/miso213_layering_B"
_m134.BUNDLE = KEEPER
m207.KEEPER = KEEPER
m208.KEEPER = KEEPER
_m211.KEEPER = KEEPER
assert _m134.BUNDLE == KEEPER and m207.KEEPER == KEEPER and m208.KEEPER == KEEPER
assert _m134.keeper_config().miso_zonal_gas_basis_skip_923_priced, (
    "T-1 re-point failed: the probe would run on the control config"
)

OUT = REPO / "results/calibration/_miso215_intermediate_phys.json"
# rule 22 [R-HOLDOUT]: MISO holds no marker, so 2023-2025 are the ONLY years
# this probe may touch. The env override exists for a single-year smoke test
# and is hard-gated to the training window.
YEARS = tuple(
    int(v) for v in os.environ.get("MISO215_YEARS", "2023,2024,2025").split(",")
)
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
EPS = 1e-9

#: Measured EIA annual Henry Hub spot averages for the training window — the
#: same literals ``scripts/data/derive_gas_offer_margin_anchor.py`` carries as
#: ``TRAIN_WINDOW_HH`` (EIA Natural Gas Spot Price, Henry Hub, annual average).
#: Read here as the M-3 reference point; nothing is re-derived (rule 23).
TRAIN_WINDOW_HH: dict[int, float] = {2023: 2.54, 2024: 2.19, 2025: 3.52}
#: The MISO recipe the anchor derive uses for ``_gas_series`` (its
#: ``GAS_SERIES_FLAGS["MISO"]``), restated so M-3 can reproduce the published
#: annual means rather than assume them.
ANCHOR_SERIES_FLAGS = {
    "gas_seasonality": True,
    "gas_daily_shape": True,
    "miso_zonal_gas_basis": True,
}

#: The three duty-split cohorts, each as
#: (parent model class, intermediate curve key, cohort resolver, split flag,
#:  cf-threshold field). The resolver signature mirrors
#: ``offer_curves._offer_curve_for_group`` exactly.
COHORTS = (
    ("CT_PEAKER", "CT_INTERMEDIATE", ct_intermediate_plants,
     "ct_intermediate_split", "ct_intermediate_cf_threshold"),
    ("CC_REGULAR", "CC_INTERMEDIATE", cc_intermediate_plants,
     "cc_intermediate_split", "cc_intermediate_cf_threshold"),
    ("ST_GAS", "ST_GAS_INTERMEDIATE", st_gas_intermediate_plants,
     "st_gas_intermediate_split", "st_gas_intermediate_cf_threshold"),
)

#: CAMPD ``unitType`` -> model class family, the same three-way map the frozen
#: derive ``scripts/data/derive_campd_marginal_hr.py::_unit_family`` uses.
#: Re-stated locally (six lines) rather than imported, so this probe never
#: couples to a rule-23 derive script's module scope.
def _unit_family(unit_type: str) -> str | None:
    t = str(unit_type).lower()
    if "combined cycle" in t:
        return "CC"
    if "combustion turbine" in t:
        return "CT"
    if "boiler" in t or "fired" in t:
        return "ST"
    return None


FAMILY_OF_CLASS = {"CT_PEAKER": "CT", "CC_REGULAR": "CC", "ST_GAS": "ST"}

IO_MIN_HOURS = 50
IO_MIN_OPTIME = 0.98

# Pre-registered bars (PREREG §5). Restated as data so the record carries them.
K_B_BAR = 0.06      # |cohort own marginal mult - borrowed parent p50|
K_C_FUEL_BAR = 0.30  # $/MMBtu the anchor sits below the cohort's delivered fuel
K_C_VANISH_BAR = 0.70  # share of |screen delta| that vanishes at the own anchor
K_E_BAR = 0.05      # uncovered cohorts' share of assembled MISO gas capacity
# Pre-registered protective faces (PREREG §5 K-d).
C1_CC_2024 = 7.419      # % vs the +/-8.00 band
C8_CT_2023 = 0.2044     # forced share vs the 15 % peaker budget


def campd_units(year: int, plant_ids: set[int], family: str) -> pd.DataFrame:
    """CAMPD **unit-level** hours for ``plant_ids``, restricted to ``family``.

    The miso-214 ``campd_ct`` reader generalized from simple-cycle CTs to the
    three model class families via :func:`_unit_family`, so a multi-class plant
    contributes only the units whose CAMPD ``unitType`` matches the cohort's
    own family (a CC plant that also hosts a peaking CT is not credited with
    the CT's energy). Read straight from ``data/raw/campd-unit-level`` — not
    through ``campd.load_campd_hourly``, which drops ``opTime`` that the M-3b
    input-output fit selects on. Clock: CAMPD local standard time onto the
    model's fixed non-leap 8760 clock with NO shift (the established MISO-probe
    convention, disclosed rather than corrected).
    """
    cols = ["facilityId", "unitId", "stateCode", "date", "hour", "opTime",
            "grossLoad", "heatInput", "unitType"]
    frames = []
    for st in campd.states_for_iso("MISO"):
        f = REPO / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if not f.exists():
            continue
        df = pd.read_parquet(f, columns=cols)
        df = df[df["facilityId"].astype("int64").isin(plant_ids)]
        if df.empty:
            continue
        fam = df["unitType"].map(_unit_family)
        df = df[fam == family]
        if df.empty:
            continue
        d = pd.to_datetime(df["date"])
        hoy = campd._hour_index_8760(d.dt.month, d.dt.day, df["hour"].astype(int))
        df = df.assign(hour_of_year=hoy)
        df = df[df["hour_of_year"] >= 0]
        frames.append(
            pd.DataFrame({
                "plant_id": df["facilityId"].astype("int64").to_numpy(),
                "unit_id": df["unitId"].astype(str).to_numpy(),
                "hour_of_year": df["hour_of_year"].astype("int32").to_numpy(),
                "gross_mw": pd.to_numeric(df["grossLoad"], errors="coerce")
                .fillna(0.0).to_numpy(),
                "heat_mmbtu": pd.to_numeric(df["heatInput"], errors="coerce")
                .fillna(0.0).to_numpy(),
                "op_time": pd.to_numeric(df["opTime"], errors="coerce")
                .fillna(0.0).to_numpy(),
            })
        )
    if not frames:
        return pd.DataFrame(
            columns=["plant_id", "unit_id", "hour_of_year", "gross_mw",
                     "heat_mmbtu", "op_time"]
        )
    out = pd.concat(frames, ignore_index=True)
    return out.groupby(
        ["plant_id", "unit_id", "hour_of_year"], observed=True, as_index=False
    ).agg({"gross_mw": "sum", "heat_mmbtu": "sum", "op_time": "max"})


def cohort_marginal_mult(
    cm: pd.DataFrame, plants: set[int], cap_by_plant: dict[int, float],
    base_hr: float,
) -> tuple[float, int, float]:
    """M-3b: a cohort's OWN measured marginal-HR multiplier, cap-weighted.

    Per CAMPD unit, the steady-state input-output slope ``b`` of
    ``heat = a + b x MW`` (:func:`_miso214...io_fit`: ``opTime >= 0.98``,
    inside the unit's own p3-p97 load envelope) — the same physical quantity
    the frozen ``derive_campd_marginal_hr.py`` reports per class as ``marg_*``
    — expressed as a MULTIPLE of the class cap-weighted ``base_hr`` the model's
    band multipliers scale, then capacity-weighted across the cohort's plants.
    Returns ``(multiplier, n_units_fit, covered_capacity_mw)``. Diagnostic only:
    nothing is written back to the frozen artifact (rule 23).
    """
    if cm.empty:
        return float("nan"), 0, 0.0
    per_plant: dict[int, list[float]] = {}
    n_fit = 0
    for (pid, _uid), sub in cm.groupby(["plant_id", "unit_id"], observed=True):
        if int(pid) not in plants:
            continue
        mw = np.zeros(HOURS)
        heat = np.zeros(HOURS)
        opt = np.zeros(HOURS)
        idx = sub["hour_of_year"].to_numpy(int)
        mw[idx] = sub["gross_mw"].to_numpy(float)
        heat[idx] = sub["heat_mmbtu"].to_numpy(float)
        opt[idx] = sub["op_time"].to_numpy(float)
        _a, b, n = io_fit(mw, heat, opt)
        if not np.isfinite(b):
            continue
        per_plant.setdefault(int(pid), []).append(float(b))
        n_fit += 1
    # Weight PER PLANT by the plant's model capacity, after averaging its own
    # CEMS units' slopes: CAMPD carries no per-unit model MW, so a plant's
    # units share its capacity rather than each claiming all of it (the
    # smoke-test defect: covered_mw ran 3x the cohort's own capacity).
    num = den = 0.0
    for pid, slopes in per_plant.items():
        w = cap_by_plant.get(int(pid), 0.0)
        if w <= 0:
            continue
        num += float(np.mean(slopes)) * w
        den += w
    if den <= 0:
        return float("nan"), n_fit, 0.0
    return float(num / den / max(base_hr, EPS)), n_fit, float(den)


def markup_mult_for(suffix: str, tranche_mult: float, offer: dict,
                    phys: dict) -> float:
    """``offer_curves.gas_offer_margin_markup_mult`` with a BORROWED phys dict.

    Byte-for-byte the production band resolution (committed -> ``phys_committed``;
    ``econlo`` / ``econhi`` / ``econcNN`` -> the registered ``econ_low ->
    econ_high`` ramp position interpolated onto ``phys_econ_low ->
    phys_econ_high``; ``peak*`` -> ``phys_peak``; ``mustrun`` / ``sync`` never
    marked up), except that ``phys`` is supplied separately — because the
    uncovered cohort HAS no ``phys_*`` keys and the candidate would borrow its
    PARENT class's already-registered ones. ``offer`` still supplies the
    cohort's OWN registered ``econ_low`` / ``econ_high``, exactly as production
    would once the keys were merged onto it.
    """
    if suffix.startswith("committed"):
        p = phys.get("phys_committed")
        return max(0.0, tranche_mult - float(p)) if p is not None else 0.0
    if suffix.startswith("econ"):
        p_lo, p_hi = phys.get("phys_econ_low"), phys.get("phys_econ_high")
        if p_lo is None or p_hi is None:
            return 0.0
        lo_m, hi_m = float(offer["econ_low"]), float(offer["econ_high"])
        if suffix == "econlo":
            p = float(p_lo)
        elif suffix == "econhi":
            p = float(p_hi)
        else:
            f = (min(1.0, max(0.0, (tranche_mult - lo_m) / (hi_m - lo_m)))
                 if hi_m > lo_m else 0.5)
            p = float(p_lo) + (float(p_hi) - float(p_lo)) * f
        return max(0.0, tranche_mult - p)
    if suffix.startswith("peak"):
        p = phys.get("phys_peak")
        return max(0.0, tranche_mult - float(p)) if p is not None else 0.0
    return 0.0


def main() -> None:  # noqa: PLR0912, PLR0915
    cfg = keeper_config()
    anchor = float(cfg.gas_offer_margin_anchor)
    curves = dict(cfg.offer_curve_by_group or {})
    raw_cfg = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]

    rep: dict = {
        "charter": "miso-215 phase 0 — the phys_* coverage gap on the intermediate-duty cohorts; zero-solve.",
        "prereg": "results/calibration/PREREG-miso215-intermediate-phys-2026-09-05.md @ cae766ec",
        "keeper": "2026-09-05-miso-213-layering",
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "anchor_usd_mmbtu": anchor,
        "instrument": {
            "model_plant_grain": "PRICE-TAKING STATIC SCREEN on mc_base (no P1 startup adder) at the keeper's own committed P1 zone price — the keeper ships no unit_hourly/ or dispatch/. A BOUND, not the LP (miso-214 §1: 1.41-1.43x the LP's own CT class energy).",
            "backfill_blind": "the screen holds the price FIXED, so cross-class backfill (CT displaced -> CC picks it up) is INVISIBLE to it; the K-1 CC_REGULAR-2024 exposure is an UN-INSTRUMENTED RISK here, never a measurement.",
            "campd": "data/raw/campd-unit-level directly (not load_campd_hourly, which drops opTime), restricted per cohort by _unit_family; model 8760 clock, no timezone shift; GROSS vs the model's NET, unadjusted.",
            "monthly_923": "a MONTHLY ALL-IN delivered print applied to an HOURLY decision — the average-vs-marginal convention (miso-212 §8) is OWNER-COURT and untouched.",
            "no_rule23_rederive": "M-3b fits each cohort's own marginal HR as a DIAGNOSTIC; the frozen miso_campd_marginal_hr_summary.csv is read, never rewritten.",
        },
        "kill_bars": {
            "K_b_marginal_mult_tol": K_B_BAR,
            "K_c_fuel_gap_usd_mmbtu": K_C_FUEL_BAR,
            "K_c_vanish_share": K_C_VANISH_BAR,
            "K_e_capacity_share": K_E_BAR,
        },
        "protective_faces": {
            "C1_CC_REGULAR_2024_pct": C1_CC_2024,
            "C1_band_pct": 8.00,
            "C8_CT_PEAKER_2023_forced_share": C8_CT_2023,
            "C8_peaker_budget": 0.15,
        },
        "years": {},
    }

    # ---- S-1: the coverage census, read verbatim from the keeper's config ----
    rep["S1_phys_coverage"] = {
        "gas_offer_net_revenue_margin": bool(cfg.gas_offer_net_revenue_margin),
        "registered_anchor": GAS_OFFER_MARGIN_ANCHOR_BY_ISO["MISO"],
        "anchor_in_run_config": raw_cfg.get("gas_offer_margin_anchor"),
        "gas_offer_margin_zonal_anchor": raw_cfg.get("gas_offer_margin_zonal_anchor"),
        "splits_armed": {
            f: bool(raw_cfg.get(f))
            for _p, _i, _fn, f, _t in COHORTS
        },
        "curves": {
            k: {
                "bands": {b: curves.get(k, {}).get(b) for b in
                          ("committed", "econ_low", "econ_high", "peak")},
                "phys_keys": sorted(
                    x for x in (curves.get(k) or {}) if x.startswith("phys_")
                ),
            }
            for k in ("CT_PEAKER", "CT_INTERMEDIATE", "CC_REGULAR",
                      "CC_INTERMEDIATE", "ST_GAS", "ST_GAS_INTERMEDIATE",
                      "CC_CHP", "CT_CHP")
        },
    }

    # ---- M-3 (a): the anchor's own basis, reproduced not assumed -------------
    base_series_cfg = ScenarioConfig(
        iso="MISO", mode="backcast", hours=HOURS_PER_YEAR, **ANCHOR_SERIES_FLAGS
    )
    series_means = {}
    for yr, hh in sorted(TRAIN_WINDOW_HH.items()):
        s = _gas_series(
            base_series_cfg.with_overrides(gas_price_override=hh), yr, HOURS_PER_YEAR
        )
        series_means[str(yr)] = _r(float(np.nanmean(s)), 4)
    rep["M3a_anchor_basis"] = {
        "what": "GAS_OFFER_MARGIN_ANCHOR_BY_ISO['MISO'] is the mean of _gas_series under GAS_SERIES_FLAGS['MISO'] — an ISO-level Henry Hub x seasonality x daily-shape series. The fleet is priced by the per-plant EIA-923 PRINT path, which applies on the (n_gen, T) array and is invisible to that series.",
        "gas_series_annual_means": series_means,
        "anchor": anchor,
        "anchor_recomputed": _r(
            float(np.mean([v for v in series_means.values() if v is not None])), 4
        ),
        "measured_annual_henry_hub": TRAIN_WINDOW_HH,
        "series_minus_hh": {
            str(yr): _r(series_means[str(yr)] - TRAIN_WINDOW_HH[yr], 4)
            for yr in TRAIN_WINDOW_HH
        },
        "keeper_fuel_path": {
            k: raw_cfg.get(k) for k in
            ("gas_plant_monthly_fuel_pricing", "gas_monthly_actuals",
             "gas_hub_basis_overlay", "gas_daily_shape", "gas_seasonality",
             "miso_zonal_gas_basis", "miso_zonal_gas_basis_skip_923_priced")
        },
    }

    # ---- M-4 (bundle half): the keeper's own D-2 / D-4 rows -----------------
    diag = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    d2 = diag["diagnostics"]["D2"]["rows"]
    d4 = diag["diagnostics"]["D4"]["rows"]
    rep["M4_census_bundle"] = {
        "D2_rows_gas_classes": [
            r for r in d2
            if str(r.get("class")) in ("CT_PEAKER", "CC_REGULAR", "ST_GAS",
                                       "CC_CHP", "CT_CHP")
        ],
        "D4_window_rows": [r for r in d4 if r.get("check") == "window"],
        "armed_reliability_floor_limbs": [
            {"class": r.plant_class, "driver": getattr(r, "driver", None),
             "zone": getattr(r, "zone", None),
             "window": (f"h{int(r.start_hour)}-{int(r.end_hour)}"
                        if r.start_hour is not None and r.end_hour is not None
                        else "h0-23")}
            for r in RELIABILITY_FLOOR_REGISTRY["MISO"] if r.enabled
        ],
        "startup_amortization_flags": {
            k: raw_cfg.get(k) for k in
            ("tranche_startup_amortization", "tranche_startup_measured_runs",
             "tranche_startup_conditional_runs")
        },
    }

    for year in YEARS:
        y: dict = {}
        raw_fleet, fleet, arrays, fp, mc, zones = build_year(cfg, year)
        gc.collect()
        # The resolved delivered price carries the dual-fuel OIL-PARITY step
        # wherever it binds (`dual_fuel_switching=True` on this keeper), so a
        # cohort's cap-weighted "delivered fuel" is part oil, not a gas print —
        # the confound miso-214 §8(3) disclosed and could not separate. Build
        # the SAME year once more with the switch off and keep only its fuel
        # array, so M-3 can report the pure EIA-923 gas print beside the
        # resolved price. Nothing else uses this fleet; it is dropped at once.
        fp_gas = build_year(
            dataclasses.replace(cfg, dual_fuel_switching=False), year
        )[3]
        gc.collect()

        klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
        uids = np.array([str(g.unit_id) for g in fleet])
        bands = np.array([_band(u) for u in uids])
        pcode = np.asarray(arrays.plant_code)
        zi = np.asarray(arrays.zone_idx)
        pmax = np.asarray(arrays.pmax, float)
        avail = np.asarray(arrays.availability, float)
        hr_all = np.asarray(arrays.heat_rate, float)
        markup = np.array(
            [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet]
        )
        # M-4: the P1 startup amortization the keeper already applies to these
        # tranches. Its ACTUAL value needs the P0 dispatch, which the keeper
        # does not ship — so what is measured here is its v3 MEASURED-HORIZON
        # value, ``_startup_cost(g) / fast_start_run_hours``, with no P0
        # shortening. ``compute_monthly_markup`` lets the endogenous P0 run
        # only SHORTEN the horizon (never lengthen it past the measured
        # ceiling), so this is a strict LOWER BOUND on the markup the keeper's
        # P1 actually charged. $/MWh, not MMBtu/MWh.
        startup_usd = np.array([
            (_startup_cost(g, float(hr_all[i]))
             / max(float(getattr(g, "fast_start_run_hours", 0.0) or 0.0), 1.0))
            for i, g in enumerate(fleet)
        ])
        price = keeper_price(KEEPER, year, zones)  # (Z, T)

        # per-plant raw base heat rate, per parent class (the quantity every
        # band multiplier scales; the cohort curve's committed is 1.00-1.005 so
        # tranche_mult = tranche_HR / base_HR recovers the registered band).
        hr_base: dict[str, dict[int, float]] = {}
        for g in raw_fleet:
            pg = str(getattr(g, "plant_group", "") or "")
            if pg in FAMILY_OF_CLASS:
                hr_base.setdefault(pg, {}).setdefault(
                    int(g.plant_code), float(g.heat_rate)
                )

        gas_classes = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "CC_CHP", "CT_CHP",
                       "ST_CHP")
        gas_cap_total = float(pmax[np.isin(klass, gas_classes)].sum())
        y["N1_footing"] = {
            "n_tranches": int(len(fleet)),
            "assembled_gas_capacity_mw": _r(gas_cap_total, 1),
            "zones": zones,
        }

        cohort_rows: dict[str, dict] = {}
        uncovered_cap = 0.0

        for parent, inter_key, resolver, split_flag, thr_field in COHORTS:
            armed = bool(getattr(cfg, split_flag, False))
            thr = float(getattr(cfg, thr_field, 50.0))
            members = resolver(
                "MISO", thr,
                bool(cfg.campd_per_unit_attribution),
                bool(cfg.campd_outage_merit_order_guard),
            ) if armed else set()
            rows = np.flatnonzero(klass == parent)
            # ST_GAS peaker plants BYPASS offer_curve_by_group entirely
            # (_offer_curve_for_group returns None), so they are in neither
            # cohort and are reported separately rather than silently pooled.
            bypass = np.array([
                parent == "ST_GAS" and int(p) in ST_GAS_PEAKER_PLANTS
                for p in pcode[rows]
            ])
            in_cohort = np.array([int(p) in members for p in pcode[rows]]) & ~bypass
            hb = hr_base.get(parent, {})
            parent_curve = curves.get(parent) or {}
            inter_curve = curves.get(inter_key) or {}
            phys_borrow = {
                k: v for k, v in parent_curve.items() if k.startswith("phys_")
            }
            fam = FAMILY_OF_CLASS[parent]

            def _stats(sel, _rows=rows, _hb=hb):
                idx = _rows[sel]
                if idx.size == 0:
                    return None
                econ = np.array([b.startswith("econ") for b in bands[idx]])
                pk = np.array([b.startswith("peak") for b in bands[idx]])
                cap_e = pmax[idx][econ]
                cap_p = pmax[idx][pk]
                plants = {int(p) for p in np.unique(pcode[idx]) if int(p) > 0}
                phys_leg = hr_all[idx] - markup[idx]
                out = {
                    "n_plants": len(plants),
                    "capacity_mw": _r(float(pmax[idx].sum()), 1),
                    "n_tranches": int(idx.size),
                    "econ_tranches": int(econ.sum()),
                    "peak_tranches": int(pk.sum()),
                    "cap_w_offer_hr_econ": _r(
                        float((hr_all[idx][econ] * cap_e).sum()
                              / max(cap_e.sum(), EPS)), 3) if econ.any() else None,
                    "cap_w_physical_leg_hr_econ": _r(
                        float((phys_leg[econ] * cap_e).sum()
                              / max(cap_e.sum(), EPS)), 3) if econ.any() else None,
                    "cap_w_markup_hr_econ": _r(
                        float((markup[idx][econ] * cap_e).sum()
                              / max(cap_e.sum(), EPS)), 3) if econ.any() else None,
                    "cap_w_startup_amort_usd_mwh_econ_lowerbound": _r(
                        float((startup_usd[idx][econ] * cap_e).sum()
                              / max(cap_e.sum(), EPS)), 3) if econ.any() else None,
                    "cap_w_offer_hr_peak": _r(
                        float((hr_all[idx][pk] * cap_p).sum()
                              / max(cap_p.sum(), EPS)), 3) if pk.any() else None,
                    "cap_w_delivered_fuel_usd_mmbtu": _r(
                        float((fp[idx][econ] * cap_e[:, None]).sum()
                              / max(cap_e.sum() * HOURS, EPS)), 4
                    ) if econ.any() else None,
                    # the SAME quantity with dual-fuel oil parity disarmed:
                    # the cohort's pure EIA-923 gas print (miso-214 §8(3)).
                    "cap_w_gas_print_no_oil_usd_mmbtu": _r(
                        float((fp_gas[idx][econ] * cap_e[:, None]).sum()
                              / max(cap_e.sum() * HOURS, EPS)), 4
                    ) if econ.any() else None,
                    "econ_cap_hour_share_oil_parity_binding": _r(
                        float(((fp[idx][econ] > fp_gas[idx][econ] + 1e-6)
                               * cap_e[:, None]).sum()
                              / max(cap_e.sum() * HOURS, EPS))
                    ) if econ.any() else None,
                    # robust central value + spread of the RESOLVED price over
                    # the cohort's econ capacity-hours (a right-skewed mean is
                    # a winter/oil tail, not the price it usually pays).
                    "delivered_fuel_p25_p50_p75": [
                        _r(float(np.percentile(fp[idx][econ], q)), 4)
                        for q in (25, 50, 75)
                    ] if econ.any() else None,
                    "econ_cap_hour_share_fuel_above_anchor": _r(
                        float(((fp[idx][econ] > anchor) * cap_e[:, None]).sum()
                              / max(cap_e.sum() * HOURS, EPS))
                    ) if econ.any() else None,
                    "plants": sorted(plants),
                }
                return out

            s_int = _stats(in_cohort)
            s_par = _stats(~in_cohort & ~bypass)
            s_byp = _stats(bypass) if bypass.any() else None
            if s_int:
                uncovered_cap += float(s_int["capacity_mw"] or 0.0)

            # ---- CAMPD energy + M-3b own marginal, per cohort ---------------
            all_plants = {int(p) for p in np.unique(pcode[rows]) if int(p) > 0}
            cm = campd_units(year, all_plants, fam)
            cap_by_plant = {
                int(k): float(v)
                for k, v in pd.Series(pmax[rows], index=pcode[rows])
                .groupby(level=0).sum().items()
            }
            base_hr_cls = (
                float((pmax[rows] * np.array([
                    hb.get(int(p), np.nan) for p in pcode[rows]
                ])).sum() / max(pmax[rows].sum(), EPS))
            )

            def _campd(plants_sel, _cm=cm):
                if _cm.empty:
                    return None
                sub = _cm[_cm["plant_id"].isin(plants_sel)]
                return _r(float(sub["gross_mw"].sum()) / 1e6, 3)

            int_plants = {int(p) for p in np.unique(pcode[rows][in_cohort])
                          if int(p) > 0}
            par_plants = {int(p) for p in np.unique(pcode[rows][~in_cohort & ~bypass])
                          if int(p) > 0}
            mult_int = cohort_marginal_mult(cm, int_plants, cap_by_plant, base_hr_cls)
            mult_par = cohort_marginal_mult(cm, par_plants, cap_by_plant, base_hr_cls)

            # ---- M-2 / M-3c: the static reach, per band scope ----------------
            zp = price[zi[rows], :]
            availcap = pmax[rows][:, None] * avail[rows]
            mw_base = availcap * (mc[rows] <= zp)

            def _reach(scope: tuple[str, ...], own_anchor: bool):
                """Reprice the cohort's ``scope`` tranches into the margin form.

                ``own_anchor`` swaps the ISO anchor for this cohort-year's own
                cap-weighted resolved delivered fuel (M-3c's counterfactual —
                a diagnostic, never a field). Returns
                ``(delta_TWh, n_repriced, cap_w_fixed_margin_usd_mwh)``.
                """
                mc_c = mc[rows].copy()
                n = 0
                cap_m: list[tuple[float, float]] = []
                a_use = anchor
                if own_anchor:
                    econ_sel = np.array([b.startswith("econ") for b in bands[rows]])
                    sel = econ_sel & in_cohort
                    if not sel.any():
                        return None, 0, None
                    cw = pmax[rows][sel]
                    a_use = float((fp[rows][sel] * cw[:, None]).sum()
                                  / max(cw.sum() * HOURS, EPS))
                for j in np.flatnonzero(in_cohort):
                    suf = bands[rows][j]
                    if not suf.startswith(scope):
                        continue
                    pc = int(pcode[rows][j])
                    b0 = hb.get(pc)
                    if not b0 or markup[rows][j] > 0.0:
                        continue
                    mult = hr_all[rows][j] / b0
                    mk = markup_mult_for(suf, mult, inter_curve, phys_borrow)
                    if mk <= 0.0:
                        continue
                    mk_hr = mk * b0
                    mc_c[j] = mc[rows][j] + mk_hr * (a_use - fp[rows][j])
                    n += 1
                    cap_m.append((float(pmax[rows][j]), float(mk_hr * a_use)))
                if n == 0:
                    return 0.0, 0, None
                mw_c = availcap * (mc_c <= zp)
                capsum = sum(c for c, _ in cap_m) or EPS
                return (
                    _r(float((mw_c - mw_base).sum()) / 1e6, 4),
                    n,
                    _r(sum(c * m for c, m in cap_m) / capsum, 2),
                )

            def _margin_sizing(sel_mask):
                """M-3d: what the anchor SIZES the fixed margin at, vs the
                cohort's own delivered fuel.

                The mechanism's economic content is a fixed margin
                ``markup_hr x anchor`` ($/MWh). ``markup_hr`` is measured
                physics; ``anchor`` is the identification point. This reports
                the cap-weighted margin at the REGISTERED ISO anchor beside the
                one the SAME markup would carry at the cohort's own cap-weighted
                resolved delivered fuel — the ratio is how far the mechanism's
                central quantity is from the fuel the cohort actually pays.
                Computed for the uncovered cohorts on the BORROWED markup and
                for the ALREADY-ARMED ones on their OWN assembled
                ``offer_markup_hr``, so the armed classes are measured on the
                mechanism as it actually stands in the keeper.
                """
                idx = rows[sel_mask]
                if idx.size == 0:
                    return None
                econ_m = np.array([b.startswith("econ") for b in bands[idx]])
                if not econ_m.any():
                    return None
                cap_e = pmax[idx][econ_m]
                own_fuel = float((fp[idx][econ_m] * cap_e[:, None]).sum()
                                 / max(cap_e.sum() * HOURS, EPS))
                own_gas = float((fp_gas[idx][econ_m] * cap_e[:, None]).sum()
                                / max(cap_e.sum() * HOURS, EPS))
                mk_live = float((markup[idx][econ_m] * cap_e).sum()
                                / max(cap_e.sum(), EPS))
                # the markup the candidate WOULD install (borrowed phys)
                mk_cand = 0.0
                for j in np.flatnonzero(sel_mask):
                    if not bands[rows][j].startswith("econ"):
                        continue
                    b0 = hb.get(int(pcode[rows][j]))
                    if not b0:
                        continue
                    mult = hr_all[rows][j] / b0
                    mk_cand += (markup_mult_for(bands[rows][j], mult,
                                                inter_curve, phys_borrow)
                                * b0 * float(pmax[rows][j]))
                mk_cand = mk_cand / max(cap_e.sum(), EPS)
                mk = mk_live if mk_live > 0.0 else mk_cand
                return {
                    "cap_w_markup_hr_econ": _r(mk, 4),
                    "markup_source": "assembled offer_markup_hr (ARMED)"
                    if mk_live > 0.0 else "borrowed parent phys_* (candidate)",
                    "own_delivered_fuel_usd_mmbtu": _r(own_fuel, 4),
                    "own_gas_print_no_oil_usd_mmbtu": _r(own_gas, 4),
                    "fixed_margin_at_own_gas_print_usd_mwh": _r(mk * own_gas, 3),
                    "margin_ratio_gas_print_over_anchor": _r(
                        own_gas / anchor if anchor > EPS else np.nan, 4),
                    "anchor_usd_mmbtu": anchor,
                    "own_minus_anchor_usd_mmbtu": _r(own_fuel - anchor, 4),
                    "fixed_margin_at_iso_anchor_usd_mwh": _r(mk * anchor, 3),
                    "fixed_margin_at_own_fuel_usd_mwh": _r(mk * own_fuel, 3),
                    "margin_ratio_own_over_anchor": _r(
                        own_fuel / anchor if anchor > EPS else np.nan, 4),
                }

            def _shift_split(sel_mask):
                """Level-vs-form characterization of the ECON reprice.

                An ADDED companion to the frozen M-3c (which the finding
                reports exactly as pre-registered): the cap-weighted mean offer
                shift the reprice applies, and the share of the cohort's econ
                capacity-hours whose offer it RAISES. A pure FORM change with a
                correctly-placed anchor would show a mean shift near zero and a
                raised share near one half; a shift dominated by the anchor's
                LEVEL shows up as a one-sided split.
                """
                idx = rows[sel_mask]
                if idx.size == 0:
                    return None
                econ_m = np.array([b.startswith("econ") for b in bands[idx]])
                if not econ_m.any():
                    return None
                sub = np.flatnonzero(sel_mask)
                mk_hr = np.zeros(idx.size)
                for k, j in enumerate(sub):
                    b0 = hb.get(int(pcode[rows][j]))
                    if not b0 or markup[rows][j] > 0.0:
                        continue
                    mult = hr_all[rows][j] / b0
                    mk_hr[k] = markup_mult_for(
                        bands[rows][j], mult, inter_curve, phys_borrow) * b0
                mk_e = mk_hr[econ_m]
                cap_e = pmax[idx][econ_m]
                shift = mk_e[:, None] * (anchor - fp[idx][econ_m])
                w = np.repeat(cap_e[:, None], HOURS, axis=1)
                live = mk_e > 0.0
                if not live.any():
                    return None
                return {
                    "cap_w_mean_offer_shift_usd_mwh": _r(
                        float((shift[live] * w[live]).sum()
                              / max(w[live].sum(), EPS)), 3),
                    "raised_share_of_econ_cap_hours": _r(
                        float((w[live] * (shift[live] > 0)).sum()
                              / max(w[live].sum(), EPS))),
                }

            d_econ, n_econ, marg_econ = _reach(("econ",), False)
            d_both, n_both, marg_both = _reach(("econ", "peak"), False)
            d_own, n_own, marg_own = _reach(("econ",), True)
            vanish = None
            if d_econ is not None and abs(d_econ) > 1e-6 and d_own is not None:
                vanish = _r(1.0 - abs(d_own) / abs(d_econ))

            # peak-leg offer shift, at the cohort's own delivered fuel
            pk_sel = np.array([b.startswith("peak") for b in bands[rows]]) & in_cohort
            peak_shift = None
            if pk_sel.any():
                cw = pmax[rows][pk_sel]
                sh = []
                for j in np.flatnonzero(pk_sel):
                    pc = int(pcode[rows][j])
                    b0 = hb.get(pc)
                    if not b0:
                        continue
                    mult = hr_all[rows][j] / b0
                    mk = markup_mult_for("peak", mult, inter_curve, phys_borrow)
                    sh.append((float(pmax[rows][j]),
                               float(mk * b0 * (anchor - fp[rows][j].mean()))))
                if sh:
                    cs = sum(c for c, _ in sh) or EPS
                    peak_shift = _r(sum(c * v for c, v in sh) / cs, 2)
                del cw

            cohort_rows[inter_key] = {
                "parent_class": parent,
                "split_armed": armed,
                "cf_threshold": thr,
                "n_plants_in_iso_cohort": len(members),
                "intermediate": s_int,
                "parent_remainder": s_par,
                "curve_bypass_st_gas_peaker": s_byp,
                "campd_twh_intermediate": _campd(int_plants),
                "campd_twh_parent_remainder": _campd(par_plants),
                "class_base_hr": _r(base_hr_cls, 4),
                "phys_borrowed_from_parent": phys_borrow,
                "M3b_own_marginal_mult_intermediate": _r(mult_int[0], 4),
                "M3b_own_marginal_n_units": mult_int[1],
                "M3b_own_marginal_covered_mw": _r(mult_int[2], 1),
                "M3b_own_marginal_mult_parent": _r(mult_par[0], 4),
                "M3b_own_marginal_n_units_parent": mult_par[1],
                "M2_reach_econ_only_twh": d_econ,
                "M2_reach_econ_tranches_repriced": n_econ,
                "M2_cap_w_fixed_margin_econ_usd_mwh": marg_econ,
                "M2_reach_econ_plus_peak_twh": d_both,
                "M2_reach_econ_plus_peak_tranches": n_both,
                "M2_peak_offer_shift_usd_mwh_at_own_fuel": peak_shift,
                "M3c_reach_at_own_anchor_twh": d_own,
                "M3c_vanish_share": vanish,
                "M3d_margin_sizing_intermediate": _margin_sizing(in_cohort),
                "M3d_margin_sizing_parent_remainder": _margin_sizing(
                    ~in_cohort & ~bypass),
                "M3e_shift_split_intermediate": _shift_split(in_cohort),
            }
            del cm
            gc.collect()

        y["M1_M2_M3_cohorts"] = cohort_rows
        y["K_e_uncovered_share_of_gas_capacity"] = _r(
            uncovered_cap / max(gas_cap_total, EPS)
        )

        # ---- C3c exposure: the keeper's own price tail this year ------------
        sysf = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        sysf = sysf[sysf["pass"] == "P1"] if "pass" in sysf else sysf
        pv = sysf.pivot_table(index="hour", columns="zone", values="price")
        dv = sysf.pivot_table(index="hour", columns="zone", values="demand")
        wprice = ((pv * dv).sum(axis=1) / dv.sum(axis=1).replace(0, np.nan)).to_numpy()
        y["C3c_tail_keeper"] = {
            "load_w_price_mean": _r(float(np.nanmean(wprice)), 3),
            "p99": _r(float(np.nanpercentile(wprice, 99)), 2),
            "p999": _r(float(np.nanpercentile(wprice, 99.9)), 2),
            "hours_above_100": int(np.nansum(wprice > 100.0)),
            "hours_above_250": int(np.nansum(wprice > 250.0)),
        }

        rep["years"][str(year)] = y
        del raw_fleet, fleet, arrays, fp, fp_gas, mc, price
        gc.collect()

    # ---- the kill evaluation, against the PREREG's own bars -----------------
    kills: dict = {}
    yrs = [str(v) for v in YEARS]
    for _p, inter_key, _fn, _f, _t in COHORTS:
        rows = [rep["years"][v]["M1_M2_M3_cohorts"][inter_key] for v in yrs]
        fuel_gap = [
            (r["intermediate"] or {}).get("cap_w_delivered_fuel_usd_mmbtu")
            for r in rows
        ]
        gaps = [None if f is None else _r(f - anchor, 4) for f in fuel_gap]
        n_gap = sum(1 for g in gaps if g is not None and g >= K_C_FUEL_BAR)
        vanish = [r["M3c_vanish_share"] for r in rows]
        n_van = sum(1 for v in vanish if v is not None and v >= K_C_VANISH_BAR)
        own = [r["M3b_own_marginal_mult_intermediate"] for r in rows]
        borrowed = rows[0]["phys_borrowed_from_parent"]
        blo = borrowed.get("phys_econ_low")
        bhi = borrowed.get("phys_econ_high")
        bmid = None if blo is None or bhi is None else (float(blo) + float(bhi)) / 2.0
        devs = [None if (o is None or bmid is None) else _r(abs(o - bmid), 4)
                for o in own]
        kills[inter_key] = {
            "anchor_minus_fuel_by_year": gaps,
            "K_c_years_gap_ge_bar": n_gap,
            "M3c_vanish_by_year": vanish,
            "K_c_years_vanish_ge_bar": n_van,
            "K_c_FIRES": bool(n_gap >= 2 and n_van >= 2),
            "own_marginal_mult_by_year": own,
            "borrowed_phys_econ_midpoint": _r(bmid, 4),
            "K_b_abs_dev_by_year": devs,
            "K_b_FIRES": bool(
                any(d is not None and d > K_B_BAR for d in devs)
            ),
            "reach_econ_by_year": [r["M2_reach_econ_only_twh"] for r in rows],
            "reach_econ_plus_peak_by_year": [r["M2_reach_econ_plus_peak_twh"]
                                             for r in rows],
        }
    ke = [rep["years"][v]["K_e_uncovered_share_of_gas_capacity"] for v in yrs]
    kills["K_e"] = {
        "uncovered_share_by_year": ke,
        "K_e_FIRES": bool(all(v is not None and v < K_E_BAR for v in ke)),
    }
    kills["K_a"] = {
        "note": "adjudicated in the finding: is the arm ONE ScenarioConfig field whose values are the parent class's already-frozen p50s?",
    }
    rep["kills"] = kills
    rep["charter"] = rep["charter"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rep, indent=2, sort_keys=False) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for k, v in kills.items():
        if isinstance(v, dict) and any(x.endswith("FIRES") for x in v):
            fires = {x: v[x] for x in v if x.endswith("FIRES")}
            print(f"  {k}: {fires}")


if __name__ == "__main__":
    main()
