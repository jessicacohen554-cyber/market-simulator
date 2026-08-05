"""miso-132 §2 — ex-ante SIZING SCREEN for synchronized-reserve online-gating at MISO.

Pre-registration:
``results/calibration/PREREG-miso132-synchronized-reserve-online-gating-2026-08-05.md``
(pushed at ``9a0033bb`` BEFORE this probe ran). The three bars S-1 / S-2 / S-3 and
their rationales are declared there; nothing here is sized on a measured delta.

NO LP IS SOLVED. Every number is read from committed artifacts:

* the published measured cleared-reserve series
  ``data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet``, sliced by its own
  ``product`` label into the ONLINE portion (``reg + spin`` — MISO BPM-002
  §4.2.1.1.2 / §4.2.1.2.2 make both products synchronized-only) and the TOTAL
  (``reg + spin + supp``, the requirement the keeper already runs);
* the keeper bundle ``results/calibration/miso127_onlinepmin_B`` hourly class
  dispatch sidecars;
* the dispatch fleet assembled at HEAD under the keeper's own committed
  ``ScenarioConfig`` (the miso-130/131 construction).

Two declared conservatism biases, both AGAINST this lane (they inflate
``ONLINE_CAP`` and so make S-2 harder to pass):

1. zones are pooled, so a Midwest MW is allowed to back a South MW;
2. availability is the assembled fleet's EFORd/COD basis without the solve-time
   CAMPD outage overlay, so pool capacity and pool 10-minute ramp are upper
   bounds.

Rule 22 ``[R-HOLDOUT]``: MISO holds no calibration-complete marker — 2023-2025
only; the probe hard-errors on any other year.

Writes ``results/calibration/_miso132_online_gating_sizing.json``.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    FUEL_TYPE_NAMES,
    build_base_fleet,
    build_dispatch_fleet,
    fleet_to_bins,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)
from market_sim.data.reserve_requirements import (  # noqa: E402
    _to_model_hour,
    cleared_mw_path,
)
from market_sim.model.reserves.spec import (  # noqa: E402
    RESERVE_FUEL_TYPES,
)

BUNDLE = REPO / "results/calibration/miso127_onlinepmin_B"
OUT = REPO / "results/calibration/_miso132_online_gating_sizing.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760

# Pre-registered bars (PREREG §2). Declared before measurement.
S1_MIN_REQ_ON_MW = 800.0
S2_MIN_TIGHTNESS = 0.25
S3_MIN_COAL_SHARE = 0.40
S3_MIN_COAL_REACH_MW = 500.0

# Screen window (PREREG §2): July, hours-of-day 0-5.
MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MONTH_OF_HOUR = np.concatenate(
    [np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)]
)
HOD = np.tile(np.arange(24), 365)
JULY_NIGHT = (MONTH_OF_HOUR == 7) & (HOD <= 5)

# ONLINE-headroom ratio band, the physical clip the existing NYISO online-gated
# path uses (model/reserves/spec.py::_nyiso_design).
RHO_CLIP = (0.5, 4.0)

ONLINE_PRODUCTS = ("reg", "spin")
TOTAL_PRODUCTS = ("reg", "spin", "supp")

#: Scoring class (``class_hourly.klass``) -> fleet fuel type. The pergen pools
#: key on (zone, fuel_type_idx), so the dispatch join is on fuel; classes with
#: no thermal upward reserve (nuclear/hydro/wind/solar/import/biomass/OTHER)
#: are absent by design and drop out of the sum.
KLASS_FUEL: dict[str, str] = {
    "COAL_PRB": "coal",
    "COAL_BIT": "coal",
    "COAL_LIGNITE": "coal",
    "CC_REGULAR": "gas_cc",
    "CC_CHP": "gas_cc",
    "CT_PEAKER": "gas_ct",
    "CT_CHP": "gas_ct",
    "ST_GAS": "gas_st",
    "ST_CHP": "gas_st",
    "oil": "oil",
}


def _guard(year: int) -> None:
    if year not in YEARS:
        raise ValueError(
            f"rule 22 [R-HOLDOUT]: MISO holds no calibration-complete marker; "
            f"year {year} must not be read"
        )


def _keeper_config():
    """Rebuild the keeper's own ScenarioConfig from its committed run_config."""
    from market_sim.config.scenarios import ScenarioConfig

    raw = json.loads((BUNDLE / "run_config.json").read_text())
    names = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(
        **{k: v for k, v in raw["scenario_config"].items() if k in names}
    )


def requirement_series(year: int) -> dict[str, np.ndarray]:
    """Market-wide ONLINE (reg+spin) and TOTAL (reg+spin+supp) MW, (8760,).

    Same file, same loader conventions and same hour mapping as the armed
    ``miso_measured_reserve_requirements`` channel; the only difference is the
    product restriction, which is the PUBLISHED §1a qualification boundary.
    """
    _guard(year)
    df = pd.read_parquet(cleared_mw_path(year))
    df["_hour"] = _to_model_hour(df["date"], df["hour_end_est"], year)
    df = df[df["_hour"] >= 0]
    out: dict[str, np.ndarray] = {}
    for key, products in (("online", ONLINE_PRODUCTS), ("total", TOTAL_PRODUCTS)):
        sub = df[df["product"].isin(products)]
        series = np.full(HOURS, np.nan)
        hourly = sub.groupby("_hour")["cleared_mw"].sum()
        idx = hourly.index.to_numpy(dtype=int)
        keep = idx < HOURS
        series[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
        series = pd.Series(series).ffill().bfill().to_numpy(dtype=float)
        out[key] = series
    return out


def assemble_fleet(year: int, cfg):
    """FleetArrays at HEAD under the keeper's committed config."""
    _guard(year)
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    raw = load_fleet_from_csv(
        "MISO",
        iso_config,
        year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity,
    )
    bins = fleet_to_bins(raw, "MISO", cfg)
    base = build_base_fleet(
        bins, "MISO", iso_config, zone_names, cfg, [], [], year, None,
        vintage_year=year, legacy_n_bins=0,
    )
    generators, _fuel_fracs, _a, _b = build_dispatch_fleet(
        base, bins, [], "MISO", year, zone_names, cfg
    )
    arrays = generators_to_fleet_arrays(
        generators, zone_names, hours=HOURS, iso="MISO", config=cfg, year=year
    )
    return arrays


def pergen_members(arrays) -> np.ndarray:
    """The keeper's own pergen member set (spec._miso_design pergen branch)."""
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in arrays.fuel_type_idx])
    eligible = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    ramp10 = np.asarray(arrays.ramp10, dtype=float)
    return np.flatnonzero(eligible & (ramp10 > 0.0))


def rho_candidates(arrays, gidx: np.ndarray) -> dict:
    """The two fleet-property constructions for the online-headroom ratio.

    * ``pmin`` — the PREREG §2 construction, capacity-weighted plant-level
      ``(pmax - pmin)/pmin`` over the pergen member set.
    * ``mlf`` — the same physical quantity expressed through the fleet's
      CEMS-MEASURED min-stable-when-online fraction,
      ``rho = (1 - mlf)/mlf``: a pool loaded at ``mlf x cap`` backs
      ``(1 - mlf) x cap`` of headroom. ``mlf`` per member comes from exactly
      the source ``_posture_pool_params`` reads (``thermal_tranche_overrides``
      CEMS ``committed_pct``, WWSIS-2 ``MIN_STABLE_PCT_PHYSICAL`` class
      gap-fill), so it is measured, not fitted.

    Both are reported; §3 of the finding records which is used and why.
    """
    from market_sim.config.constants import MIN_STABLE_PCT_PHYSICAL
    from market_sim.data.fleet import thermal_tranche_overrides

    pmax = np.asarray(arrays.pmax, dtype=float)[gidx]
    pmin = np.asarray(arrays.pmin, dtype=float)[gidx]
    plants = np.asarray(arrays.plant_code, dtype=int)[gidx]
    groups = np.asarray(arrays.plant_group)[gidx]

    # --- (a) plant-level (pmax - pmin)/pmin, capacity-weighted.
    codes, inv = np.unique(plants, return_inverse=True)
    p_max = np.zeros(codes.size)
    p_min = np.zeros(codes.size)
    np.add.at(p_max, inv, pmax)
    np.add.at(p_min, inv, pmin)
    valid = (p_min > 0.0) & (p_max > p_min)
    if valid.any():
        ratio = (p_max[valid] - p_min[valid]) / p_min[valid]
        rho_pmin = float(np.average(ratio, weights=p_max[valid]))
    else:
        rho_pmin = float("nan")

    # --- (b) measured min-stable-when-online fraction.
    overrides = thermal_tranche_overrides("MISO")
    mlf = np.zeros(gidx.size)
    covered = np.zeros(gidx.size, dtype=bool)
    for j in range(gidx.size):
        row = overrides.get((int(plants[j]), str(groups[j])))
        if row is not None:
            mlf[j] = float(row[0]) / 100.0
            covered[j] = True
        else:
            mlf[j] = float(MIN_STABLE_PCT_PHYSICAL.get(str(groups[j]), 0.0))
    mlf = np.clip(mlf, 0.0, 1.0)
    ok = mlf > 0.0
    mlf_fleet = float(np.average(mlf[ok], weights=pmax[ok])) if ok.any() else 0.0
    rho_mlf = (1.0 - mlf_fleet) / mlf_fleet if mlf_fleet > 0 else float("nan")

    return {
        "n_members": int(gidx.size),
        "member_cap_mw": float(pmax.sum()),
        "plants_with_positive_pmin": int(valid.sum()),
        "plants_total": int(codes.size),
        "cap_share_with_positive_pmin": float(
            p_max[valid].sum() / p_max.sum() if p_max.sum() > 0 else 0.0
        ),
        "rho_pmin_raw": rho_pmin,
        "rho_pmin_clipped": (
            float(np.clip(rho_pmin, *RHO_CLIP)) if np.isfinite(rho_pmin) else None
        ),
        "mlf_cap_weighted": mlf_fleet,
        "mlf_cems_covered_cap_share": float(
            pmax[covered].sum() / pmax.sum() if pmax.sum() > 0 else 0.0
        ),
        "rho_mlf_raw": rho_mlf,
        "rho_mlf_clipped": (
            float(np.clip(rho_mlf, *RHO_CLIP)) if np.isfinite(rho_mlf) else None
        ),
    }


def class_dispatch(year: int) -> pd.DataFrame:
    """Keeper P1 hourly MW by model class, (klass, hour)."""
    _guard(year)
    df = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def online_capability(arrays, gidx: np.ndarray, disp: pd.DataFrame,
                      rho: float) -> dict:
    """``ONLINE_CAP(t) = sum_f min(rho*P_f, ramp10_f, cap_f - P_f)`` at fuel grain.

    Fuel grain with zones pooled (declared conservatism 1). ``P_f`` comes from
    the keeper's own class dispatch restricted to the plant groups that carry
    pergen members; ``cap_f`` / ``ramp10_f`` from the assembled fleet.
    """
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in arrays.fuel_type_idx])
    pmax = np.asarray(arrays.pmax, dtype=float)
    avail = np.asarray(arrays.availability, dtype=float)
    ramp10 = np.asarray(arrays.ramp10, dtype=float)

    # Keeper dispatch by model class -> fuel. The sidecar's ``klass`` is the
    # scoring class (COAL_PRB / COAL_BIT / ...), while FleetArrays.plant_group
    # is the physics group (COAL) — so the join is on FUEL, which is also the
    # pergen pool key (spec._miso_design pools on (zone, fuel_type_idx)).
    member_fuels = set(fuel_names[gidx].tolist())
    p_by_fuel: dict[str, np.ndarray] = {}
    for klass, sub in disp.groupby("klass"):
        f = KLASS_FUEL.get(str(klass))
        if f is None or f not in member_fuels:
            continue  # class carries no reserve-eligible pergen member
        series = sub.sort_values("hour")["mw"].to_numpy(dtype=float)[:HOURS]
        p_by_fuel[f] = p_by_fuel.get(f, np.zeros(HOURS)) + series

    terms: dict[str, np.ndarray] = {}
    ungated: dict[str, np.ndarray] = {}
    clipped: dict[str, float] = {}
    for f, p in p_by_fuel.items():
        sel = gidx[fuel_names[gidx] == f]
        cap_t = (pmax[sel][:, None] * avail[sel]).sum(axis=0)[:HOURS]
        ramp_t = (ramp10[sel][:, None] * avail[sel]).sum(axis=0)[:HOURS]
        p_eff = np.minimum(p, cap_t)
        clipped[f] = float((p > cap_t + 1e-6).mean())
        headroom = np.maximum(cap_t - p_eff, 0.0)
        terms[f] = np.minimum(np.minimum(rho * p_eff, ramp_t), headroom)
        # The pool capability the keeper ALREADY has WITHOUT the gate — idle
        # capacity included. Descriptive: its ratio to ``terms`` is what
        # online-gating removes from the reserve supply.
        ungated[f] = np.minimum(ramp_t, headroom)
    total = np.sum(list(terms.values()), axis=0) if terms else np.zeros(HOURS)
    tot_ung = np.sum(list(ungated.values()), axis=0) if ungated else np.zeros(HOURS)
    return {
        "total": total,
        "by_fuel": terms,
        "ungated_total": tot_ung,
        "ungated_by_fuel": ungated,
        "dispatch_above_capacity_hour_share": clipped,
        "fuels_covered": sorted(p_by_fuel),
    }


def region_robustness(arrays, gidx: np.ndarray, disp: pd.DataFrame, rho: float,
                      year: int) -> dict:
    """Region-resolved S-2 robustness check (DESCRIPTIVE, not a bar).

    Zone pooling is the one declared bias that INFLATES ``ONLINE_CAP`` and so
    could manufacture an S-2 kill. This splits both sides on the published
    Midwest (North+Central) / South boundary the measured series already
    carries: requirement per region from the ASM report's own ``region``
    column, capability from the fleet's zone assignment.

    Approximation, declared: ``class_hourly`` carries no zone, so each fuel's
    hourly dispatch is allocated across regions PRO RATA to that fuel's
    available capacity in the region. Exact for a fuel whose regional loading
    tracks its regional capacity; approximate otherwise.
    """
    from market_sim.model.reserves.spec import MISO_MIDWEST_ZONES

    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    midwest_idx = {zone_names.index(z) for z in MISO_MIDWEST_ZONES}

    df = pd.read_parquet(cleared_mw_path(year))
    df["_hour"] = _to_model_hour(df["date"], df["hour_end_est"], year)
    df = df[(df["_hour"] >= 0) & df["product"].isin(ONLINE_PRODUCTS)]
    req: dict[str, np.ndarray] = {}
    for key, regions in (("Midwest", ("North", "Central")), ("South", ("South",))):
        sub = df[df["region"].isin(regions)]
        s = np.full(HOURS, np.nan)
        hourly = sub.groupby("_hour")["cleared_mw"].sum()
        idx = hourly.index.to_numpy(dtype=int)
        keep = idx < HOURS
        s[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
        req[key] = pd.Series(s).ffill().bfill().to_numpy(dtype=float)

    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in arrays.fuel_type_idx])
    zone_idx = np.asarray(arrays.zone_idx, dtype=int)
    pmax = np.asarray(arrays.pmax, dtype=float)
    avail = np.asarray(arrays.availability, dtype=float)
    ramp10 = np.asarray(arrays.ramp10, dtype=float)
    in_mw = np.array([int(z) in midwest_idx for z in zone_idx])

    p_by_fuel: dict[str, np.ndarray] = {}
    for klass, sub in disp.groupby("klass"):
        f = KLASS_FUEL.get(str(klass))
        if f is None:
            continue
        series = sub.sort_values("hour")["mw"].to_numpy(dtype=float)[:HOURS]
        p_by_fuel[f] = p_by_fuel.get(f, np.zeros(HOURS)) + series

    out: dict[str, dict] = {}
    for key, mask in (("Midwest", in_mw), ("South", ~in_mw)):
        cap_total = np.zeros(HOURS)
        for f, p in p_by_fuel.items():
            sel = gidx[(fuel_names[gidx] == f) & mask[gidx]]
            other = gidx[fuel_names[gidx] == f]
            if sel.size == 0 or other.size == 0:
                continue
            cap_t = (pmax[sel][:, None] * avail[sel]).sum(axis=0)[:HOURS]
            cap_all = (pmax[other][:, None] * avail[other]).sum(axis=0)[:HOURS]
            ramp_t = (ramp10[sel][:, None] * avail[sel]).sum(axis=0)[:HOURS]
            with np.errstate(invalid="ignore", divide="ignore"):
                share = np.where(cap_all > 0, cap_t / cap_all, 0.0)
            p_r = np.minimum(p * share, cap_t)
            cap_total += np.minimum(
                np.minimum(rho * p_r, ramp_t), np.maximum(cap_t - p_r, 0.0)
            )
        night = JULY_NIGHT
        c = float(cap_total[night].mean())
        r = float(req[key][night].mean())
        out[key] = {
            "req_on_july_night_mw": r,
            "online_cap_july_night_mw": c,
            "tightness": (r / c) if c > 0 else float("inf"),
        }
    return out


def main() -> None:
    cfg = _keeper_config()
    rec: dict = {
        "prereg": (
            "results/calibration/"
            "PREREG-miso132-synchronized-reserve-online-gating-2026-08-05.md"
        ),
        "prereg_pushed_at": "9a0033bb",
        "keeper": "2026-08-04-miso-127-onlinepmin",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "bars": {
            "S1_min_req_on_mw": S1_MIN_REQ_ON_MW,
            "S2_min_tightness": S2_MIN_TIGHTNESS,
            "S3_min_coal_share": S3_MIN_COAL_SHARE,
            "S3_min_coal_reach_mw": S3_MIN_COAL_REACH_MW,
        },
        "years": {},
    }

    for year in YEARS:
        req = requirement_series(year)
        arrays = assemble_fleet(year, cfg)
        gidx = pergen_members(arrays)
        rho_info = rho_candidates(arrays, gidx)
        rho = rho_info["rho_mlf_clipped"]
        disp = class_dispatch(year)
        cap = online_capability(arrays, gidx, disp, float(rho))

        on = req["online"]
        tot = req["total"]
        night = JULY_NIGHT
        req_on_night = float(on[night].mean())
        cap_night = float(cap["total"][night].mean())
        coal_night = float(cap["by_fuel"].get("coal", np.zeros(HOURS))[night].mean())
        coal_share = coal_night / cap_night if cap_night > 0 else 0.0

        rec["years"][str(year)] = {
            "rho": rho_info,
            "rho_used": float(rho),
            "requirement": {
                "online_annual_mean_mw": float(on.mean()),
                "total_annual_mean_mw": float(tot.mean()),
                "online_share_annual": float(on.sum() / tot.sum()),
                "online_july_night_mean_mw": req_on_night,
                "total_july_night_mean_mw": float(tot[night].mean()),
                "online_july_night_min_mw": float(on[night].min()),
                "online_july_night_max_mw": float(on[night].max()),
            },
            "online_capability": {
                "july_night_mean_mw": cap_night,
                "annual_mean_mw": float(cap["total"].mean()),
                "july_day_h10_18_mean_mw": float(
                    cap["total"][(MONTH_OF_HOUR == 7) & (HOD >= 10) & (HOD <= 18)].mean()
                ),
                "by_fuel_july_night_mean_mw": {
                    f: float(v[night].mean()) for f, v in cap["by_fuel"].items()
                },
                "fuels_covered": cap["fuels_covered"],
                "dispatch_above_capacity_hour_share": cap[
                    "dispatch_above_capacity_hour_share"
                ],
            },
            # DESCRIPTIVE (no bar): the reserve capability the keeper already
            # carries WITHOUT the gate, and what fraction of it survives
            # gating. Reported so the finding can say what online-gating
            # actually removes from the supply stack.
            "ungated_capability_descriptive": {
                "july_night_mean_mw": float(cap["ungated_total"][night].mean()),
                "annual_mean_mw": float(cap["ungated_total"].mean()),
                "online_share_of_ungated_july_night": float(
                    cap_night / cap["ungated_total"][night].mean()
                    if cap["ungated_total"][night].mean() > 0
                    else 0.0
                ),
                "by_fuel_july_night_mean_mw": {
                    f: float(v[night].mean())
                    for f, v in cap["ungated_by_fuel"].items()
                },
            },
            "S2_region_robustness_descriptive": region_robustness(
                arrays, gidx, disp, float(rho), year
            ),
            "screen": {
                "S1_req_on_july_night_mw": req_on_night,
                "S2_tightness_req_on_over_online_cap": (
                    req_on_night / cap_night if cap_night > 0 else float("inf")
                ),
                "S3a_coal_share_of_online_cap": coal_share,
                "S3b_coal_reach_mw": req_on_night * coal_share,
            },
        }
        del arrays

    # ---- verdicts on the pre-registered bars.
    y = rec["years"]
    s1 = all(y[str(v)]["screen"]["S1_req_on_july_night_mw"] >= S1_MIN_REQ_ON_MW
             for v in YEARS)
    s2 = y["2025"]["screen"]["S2_tightness_req_on_over_online_cap"] >= S2_MIN_TIGHTNESS
    s3a = y["2025"]["screen"]["S3a_coal_share_of_online_cap"] >= S3_MIN_COAL_SHARE
    s3b = y["2025"]["screen"]["S3b_coal_reach_mw"] >= S3_MIN_COAL_REACH_MW
    rec["verdict"] = {
        "S1_pass": bool(s1),
        "S2_pass": bool(s2),
        "S3_pass": bool(s3a and s3b),
        "S3a_pass": bool(s3a),
        "S3b_pass": bool(s3b),
        "screen_pass": bool(s1 and s2 and s3a and s3b),
    }
    OUT.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["verdict"], indent=1))
    for v in YEARS:
        print(v, json.dumps(y[str(v)]["screen"], indent=1))
    print("rho:", json.dumps(y["2025"]["rho"], indent=1))


if __name__ == "__main__":
    main()
