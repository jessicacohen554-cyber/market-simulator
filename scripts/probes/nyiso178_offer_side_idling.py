"""nyiso-178 phase 0 — is the NYISO ``ST_GAS`` over-booking an OFFER-side object?

Discharges gates G1, G2, G3, G4' and G5 of
``results/calibration/PREREG-nyiso178-offer-side-idling.md`` (with its §5
amendment, committed with this file BEFORE either ran). **Zero solves.** Every
number comes from committed artifacts plus the keeper's own P1 sidecars.

THE OBJECT. nyiso-177 §7.1 sized, and did not repair, a NYISO ``ST_GAS`` outage
overlay booking 0.50-0.56 of the bin-capacity-year as mechanical outage against a
0.10-0.15 EFOR+planned norm, and handed it forward with a STATED TYPE: an
offer-side object. This probe TESTS that type rather than inheriting it.

* **G1** — is the composed availability envelope BINDING? (the type test)
* **G2** — why does the keeper-armed merit-order guard remove almost no NYISO
  steam? Attribution across the three fail-safe exits its own code defines.
* **G3** — is the defect the offer's SHAPE or its LEVEL?
* **G4'** — rule 19 ``[R-ONE-MECH]``: any armed ``ST_GAS`` forcing channel that
  the keeper's committed D-2 attribution does not account for?
* **G5** — the rule-19 availability STACK the §5.3 code reading forced into view.

Run: PYTHONPATH=.:src python scripts/probes/nyiso178_offer_side_idling.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import THERMAL_AVAILABILITY  # noqa: E402
from market_sim.config.fuel_trajectories import SUMMER_WEFOR_SHARE  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    _iso_plant_capacity,
    unit_outage_derate_factors,
)
from scripts.data.derive_actual_lmp import _std_hour_index  # noqa: E402
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)
from scripts.lib.outage_detect import (  # noqa: E402
    MERIT_OOM_FRAC,
    MERIT_RCC_PCTL,
    build_merit_order_panel,
)

ISO = "NYISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KLASS = "ST_GAS"

KEEPER = REPO / "results/calibration/nyiso177_vintage_B1p"
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
#: The keeper's own basis: per-unit crosswalk + merit-order guard.
KEPT_CSV = RAW_DATA_DIR / "campd-unit-outages-perunitmerit-NYISO.csv"
LAYUP_CSV = RAW_DATA_DIR / "campd-unit-outages-layup-perunitmerit-NYISO.csv"
OUT = REPO / "results/calibration/_nyiso178_offer_side_idling.json"

#: Fixed standard-time clock — America/New_York raises a DST nonexistent-time
#: error on 2023-03-12 02:00 (nyiso-169b/170/171/172/173 all use this).
STD_TZ = "Etc/GMT+5"

#: G1 branch thresholds, from PREREG §1 G1. Both stated, neither movable.
G1_OFFER_MAX_SHARE = 0.01
G1_AVAIL_MIN_SHARE = 0.05
#: "At the envelope" means within 1 % of it.
G1_AT_FRAC = 0.99

#: G2 single-cause bar (PREREG §1 G2).
G2_SINGLE_CAUSE_BAR = 0.80

#: G3 bars (PREREG §1 G3).
G3_SHAPE_RATIO = 2.0
G3_LEVEL_UNIFORM_TOL = 0.25
G3_N_BANDS = 10

#: G4' candidate list — FIXED in PREREG §5.1 before this cross-check ran.
G4_CANDIDATES = (
    "reliability_floor",
    "reliability_floor_plant_exclusions",
    "nyiso_gas_commitment_bridge",
    "nyiso_gas_bridge_min_run",
    "nyiso_gas_bridge_state_floor_min_run",
    "nyiso_gas_bridge_online_hours",
    "nyiso_gas_bridge_startup",
    "nyiso_gas_bridge_plant_exclusions",
    "nyiso_gas_bridge_reserve_duty_exclusions",
    "st_gas_mustrun_per_plant",
    "st_gas_mustrun_p25_level",
    "st_gas_mustrun_p25_measured_level",
    "st_gas_mustrun_oom_level",
    "st_gas_intermediate_split",
    "mustrun_online_frac_per_year",
    "mustrun_plant_exclusions",
    "mustrun_layup_window_mask",
    "nyiso_incity_commitment_obligation",
    "chp_steam_following",
    "chp_layup_duty_curve",
    "commitment_enabled",
    "gas_st_netload_drag",
    "historic_outage_overlay",
)
#: Candidates that cannot reach an ``ST_GAS`` bin whatever their value — the
#: (b) leg of G4'. Each carries its committed-bytes reason.
G4_INERT_REASON = {
    "chp_steam_following": "CHP classes only (ST_CHP/CC_CHP/CT_CHP); ST_GAS is not a CHP class",
    "chp_layup_duty_curve": "_CHP_GROUPS scope only (campd_bins.fleet_to_bins); ST_GAS excluded by class",
    "reliability_floor_plant_exclusions": "modifier of reliability_floor, not an independent channel",
    "nyiso_gas_bridge_min_run": "leg of nyiso_gas_commitment_bridge, attributed under its D-2 id",
    "nyiso_gas_bridge_state_floor_min_run": "leg of nyiso_gas_commitment_bridge",
    "nyiso_gas_bridge_online_hours": "leg of nyiso_gas_commitment_bridge",
    "nyiso_gas_bridge_startup": "leg of nyiso_gas_commitment_bridge",
    "nyiso_gas_bridge_plant_exclusions": "leg of nyiso_gas_commitment_bridge",
    "nyiso_gas_bridge_reserve_duty_exclusions": "leg of nyiso_gas_commitment_bridge",
}
#: Which D-2 mechanism id each independent candidate must appear under.
G4_D2_ID = {
    "reliability_floor": "reliability_floor",
    "nyiso_gas_commitment_bridge": "nyiso_gas_commitment_bridge",
}


# ------------------------------------------------------------------ loaders --


def scenario_config() -> dict:
    return json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]


def model_hourly(year: int, klass: str) -> np.ndarray:
    """Model P1 hourly MW for one class, on the 8760 clock."""
    d = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    d = d[(d["pass"] == "P1") & (d["klass"] == klass)]
    s = d.groupby("hour")["mw"].sum().reindex(range(HOURS)).fillna(0.0)
    return s.to_numpy(dtype=float)


def actual_class_twh(year: int, klass: str) -> float:
    import gzip

    b = json.load(gzip.open(BENCH / f"{year}.json.gz"))
    return float(b["bench"]["classFull"].get(klass, 0.0))


def actual_price(year: int, basis: str = "rt") -> np.ndarray:
    d = pd.read_parquet(ACTUAL_HOURLY)
    d = d[d["year"] == year]
    s = d.set_index("hour")[basis].reindex(range(HOURS))
    return s.ffill().bfill().to_numpy(dtype=float)


def chp_plants() -> set[int]:
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def plant_model_groups() -> dict[int, set[str]]:
    """``{plant_code: {model plant_group}}`` from the EIA-860 fleet."""
    out: dict[int, set[str]] = {}
    for (code, grp) in _iso_plant_capacity(ISO, False, False):
        out.setdefault(int(code), set()).add(str(grp))
    return out


def measured_hourly(year: int, klass: str) -> np.ndarray:
    """Measured CAMPD gross MW for one model class on the REPAIRED crosswalk.

    Uses ``campd_measured_classes.corrected_unit_class`` (nyiso-174/175b), the
    same per-unit routing the keeper's own artifacts are derived on — NOT the
    raw ``unitType`` construction nyiso-169b..173 used, which mis-seats East
    River and S A Carlson.
    """
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitId", "unitType", "date", "hour", "grossLoad"],
    )
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    d = d.assign(
        _h=_std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ),
        _fid=d["facilityId"].astype(int),
    )
    d = d[d["_h"].between(0, HOURS - 1)].copy()
    chps, groups = chp_plants(), plant_model_groups()
    raw = [
        campd_unittype_class(ut, fid in chps)
        for ut, fid in zip(d["unitType"].fillna(""), d["_fid"])
    ]
    fixed = [
        corrected_unit_class(r, groups.get(int(f))) for r, f in zip(raw, d["_fid"])
    ]
    d["_cls"] = fixed
    d = d[d["_cls"] == klass]
    # CAMPD reports grossLoad NULL for a non-operating unit-hour (nyiso-173's
    # repaired reading): a null is ZERO output, never a propagated NaN.
    g = np.zeros(HOURS)
    np.add.at(
        g,
        d["_h"].to_numpy(dtype=int),
        d["grossLoad"].fillna(0.0).to_numpy(dtype=float),
    )
    return g


# ------------------------------------------------------------------- G1 / G5 --


def eia860_bin_vintages() -> dict[tuple[int, str], int]:
    """``{(plant_code, group): capacity-weighted EIA-860 online_year}``.

    The EIA-860 fleet's TRUE vintages, used only for the G1 robustness leg —
    the LP's own CAMPD bins carry a stamped year instead.
    """
    gens = load_fleet_from_csv(ISO)
    num: dict[tuple[int, str], float] = {}
    den: dict[tuple[int, str], float] = {}
    for g in gens:
        grp = getattr(g, "plant_group", None)
        oy = getattr(g, "online_year", None)
        cap = float(getattr(g, "pmax_mw", 0.0) or 0.0)
        if not grp or not oy or cap <= 0.0:
            continue
        k = (int(g.plant_code), str(grp))
        num[k] = num.get(k, 0.0) + cap * float(oy)
        den[k] = den.get(k, 0.0) + cap
    return {k: int(round(num[k] / den[k])) for k in num if den[k] > 0}


def lp_fleet(year: int, cfg_obj):
    """Build the EXACT LP fleet arrays the keeper's own config produces.

    PROBE-CONSTRUCTION REPAIR, disclosed (PREREG §5.3 reconstructed the envelope
    by hand and the reconstruction was INVALID: the model's ``ST_GAS`` dispatch
    EXCEEDED it at p99, which a ceiling cannot do). This calls the engine's own
    ``bins_to_fleet`` -> ``generators_to_fleet_arrays`` on the keeper's exact
    ``ScenarioConfig``, so the envelope is the LP's, not an approximation of it.
    The exact envelope is TIGHTER than the overlay-only upper bound, i.e. the
    swap makes the OFFER-SIDE branch HARDER to reach, never easier.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import generators_to_fleet_arrays
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    ic = get_iso_config(ISO)
    zones = [z.name for z in ic.zones]
    cfg_y = cfg_obj.with_overrides(weather_year=year)
    bins = load_or_synthesize_bins(cfg_y, ISO, ic, [])
    gens, _ = bins_to_fleet(bins, zones, cfg_y)
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    load_shape = (
        s.groupby("hour")["demand"].sum().reindex(range(HOURS)).ffill().bfill().to_numpy()
    )
    fa = generators_to_fleet_arrays(
        gens, zones, hours=HOURS, iso=ISO, config=cfg_y,
        load_shape=load_shape, year=year,
    )
    return gens, fa


def g1_and_g5(cfg: dict) -> tuple[dict, dict]:
    from market_sim.config.scenarios import ScenarioConfig

    cfg_obj = ScenarioConfig(**cfg)
    per_year, g5_bins = {}, {}
    for year in YEARS:
        gens, fa = lp_fleet(year, cfg_obj)
        grp = np.array([str(getattr(g, "plant_group", "") or "") for g in gens])
        sel = grp == KLASS
        pmax = fa.pmax[sel]
        env = (pmax[:, None] * fa.availability[sel, :]).sum(axis=0)
        tot = float(pmax.sum())
        mo = model_hourly(year, KLASS)
        util = mo / np.maximum(env, 1e-9)
        at = int((util >= G1_AT_FRAC).sum())

        # Report-only: utilisation by ACTUAL-price decile. The gate is on all
        # hours, exactly as pre-registered; this only says WHERE the headroom is.
        px = actual_price(year, "rt")
        order = np.argsort(px)
        decs = np.array_split(order, 10)
        by_decile = [
            {
                "decile": i,
                "mean_price": round(float(px[d].mean()), 2),
                "mean_envelope_mw": round(float(env[d].mean()), 1),
                "mean_model_mw": round(float(mo[d].mean()), 1),
                "mean_utilisation": round(float(util[d].mean()), 4),
                "p95_utilisation": round(float(np.percentile(util[d], 95)), 4),
                "hours_at_envelope": int((util[d] >= G1_AT_FRAC).sum()),
            }
            for i, d in enumerate(decs)
        ]

        # G5 decomposition: composed = statistical x ufac, so the statistical
        # layer is recoverable exactly from the LP's own availability array.
        ufac = unit_outage_derate_factors(
            year, iso=ISO, per_unit_crosswalk=True, merit_order_guard=True
        )
        codes = np.array([int(getattr(g, "plant_code", 0) or 0) for g in gens])[sel]
        rows = []
        for code in sorted(set(codes.tolist())):
            m = codes == code
            cap_c = float(pmax[m].sum())
            if cap_c <= 0:
                continue
            comp = float(
                (pmax[m][:, None] * fa.availability[sel][m, :]).sum() / (cap_c * HOURS)
            )
            u = ufac.get((code, KLASS))
            u_mean = float(np.mean(u)) if u is not None else 1.0
            oy = [
                int(getattr(g, "online_year", 0) or 0)
                for g, s_ in zip(gens, sel)
                if s_ and int(getattr(g, "plant_code", 0) or 0) == code
            ]
            rows.append(
                {
                    "plant_code": int(code),
                    "lp_pmax_mw": round(cap_c, 1),
                    "online_year_min_max": [min(oy), max(oy)] if oy else None,
                    "mean_overlay_ufac": round(u_mean, 4),
                    "mean_composed_availability": round(comp, 4),
                    "implied_statistical_layer": (
                        round(comp / u_mean, 4) if u_mean > 1e-6 else None
                    ),
                }
            )
        g5_bins[year] = rows

        # G1 ROBUSTNESS, reported: the LP's ST_GAS bins carry a STAMPED
        # online_year (the CAMPD bin synthesis), not their EIA-860 vintages, so
        # THERMAL_AVAILABILITY's age escalation past its 30-year onset never
        # fires for a NY steamer built in 1951-1977. Re-scale the statistical
        # layer to each plant's true capacity-weighted EIA-860 vintage and
        # re-test the gate. This can only TIGHTEN the envelope, i.e. it is the
        # sensitivity that could FLIP G1 to AVAILABILITY-SIDE.
        _, w_base, w_rate, w_onset, d_base, d_rate, d_onset = THERMAL_AVAILABILITY[
            KLASS
        ]
        true_oy = eia860_bin_vintages()
        scale = np.ones(int(sel.sum()))
        stamped = max(0.0, 1.0 - w_base - d_base)
        for i, code in enumerate(codes.tolist()):
            oy = true_oy.get((int(code), KLASS))
            if not oy:
                continue
            age = year - oy
            st = max(
                0.0,
                1.0
                - (w_base + max(0.0, age - w_onset) * w_rate)
                - (d_base + max(0.0, age - d_onset) * d_rate),
            )
            scale[i] = st / stamped if stamped > 0 else 1.0
        env_aged = ((pmax * scale)[:, None] * fa.availability[sel, :]).sum(axis=0)
        util_aged = mo / np.maximum(env_aged, 1e-9)
        aged = {
            "note": "statistical layer re-scaled to true EIA-860 vintages",
            "mean_availability": round(float(env_aged.mean() / tot), 4),
            "envelope_twh": round(float(env_aged.sum()) / 1e6, 4),
            "hours_at_envelope": int((util_aged >= G1_AT_FRAC).sum()),
            "share_hours_at_envelope": round(
                float((util_aged >= G1_AT_FRAC).sum()) / HOURS, 5
            ),
            "mean_utilisation": round(float(util_aged.mean()), 4),
            "p99_utilisation": round(float(np.percentile(util_aged, 99)), 4),
            "top_decile_mean_utilisation": round(
                float(util_aged[decs[-1]].mean()), 4
            ),
            "true_vintages": {
                str(int(c)): true_oy.get((int(c), KLASS))
                for c in sorted(set(codes.tolist()))
            },
        }

        per_year[year] = {
            "capacity_mw": round(tot, 1),
            "robustness_true_vintage_envelope": aged,
            "envelope_twh": round(float(env.sum()) / 1e6, 4),
            "mean_availability": round(float(env.mean() / tot), 4),
            "model_twh": round(float(mo.sum()) / 1e6, 4),
            "actual_twh": round(actual_class_twh(year, KLASS), 4),
            "hours_at_envelope": at,
            "share_hours_at_envelope": round(at / HOURS, 5),
            "mean_utilisation": round(float(util.mean()), 4),
            "p95_utilisation": round(float(np.percentile(util, 95)), 4),
            "p99_utilisation": round(float(np.percentile(util, 99)), 4),
            "max_utilisation": round(float(util.max()), 4),
            "min_headroom_mw": round(float((env - mo).min()), 1),
            "utilisation_by_actual_price_decile": by_decile,
        }

    shares = [per_year[y]["share_hours_at_envelope"] for y in YEARS]
    if max(shares) >= G1_AVAIL_MIN_SHARE:
        verdict = "AVAILABILITY-SIDE"
    elif max(shares) < G1_OFFER_MAX_SHARE:
        verdict = "OFFER-SIDE"
    else:
        verdict = "MIXED"

    g1 = {
        "gate": "G1 — is the composed ST_GAS availability envelope BINDING?",
        "gated_on": "the EXACT LP envelope (probe repair, see lp_fleet docstring)",
        "verdict": verdict,
        "thresholds": {
            "offer_side_max_share_hours_at_envelope": G1_OFFER_MAX_SHARE,
            "availability_side_min_share": G1_AVAIL_MIN_SHARE,
            "at_envelope_frac": G1_AT_FRAC,
        },
        "per_year": per_year,
    }
    relief = {
        k: cfg.get(k)
        for k in ("wefor_residual", "gas_st_wefor_base_override", "wefor_residual_groups")
    }
    stacked = all(v in (None, False, [], {}) for v in relief.values())
    g5 = {
        "gate": "G5 — rule 19 [R-ONE-MECH]: the ST_GAS availability STACK (report)",
        "verdict": "RULE-19 STACK FLAGGED" if stacked else "CLEAN",
        "statistical_layer": {
            "table": "THERMAL_AVAILABILITY['ST_GAS']",
            "value": list(THERMAL_AVAILABILITY[KLASS]),
            "summer_wefor_share": SUMMER_WEFOR_SHARE,
        },
        "measured_layer": "outages.unit_outage_derate_factors (perunitmerit basis)",
        "composition": (
            "PRODUCT (fleet/arrays.py:1097 'Multiplies the statistical "
            "availability already set above')"
        ),
        "relief_fields": relief,
        "per_bin": g5_bins,
    }
    return g1, g5


# ------------------------------------------------------------------------ G2 --


def _year_overlap(start: pd.Timestamp, end: pd.Timestamp, year: int) -> tuple[int, int] | None:
    """Clip one outage window to ``year`` and return ``(start_hour, stop_hour)``."""
    y0 = pd.Timestamp(f"{year}-01-01")
    y1 = pd.Timestamp(f"{year+1}-01-01")
    s, e = max(start, y0), min(end, y1)
    if e <= s:
        return None
    return int((s - y0).total_seconds() // 3600), int((e - y0).total_seconds() // 3600)


def g2_guard_attribution() -> dict:
    """Why did the armed merit-order guard KEEP these ST_GAS window-hours?

    Each kept window is clipped to each scored year and attributed there, so a
    window spanning a year boundary is counted against both years' panels
    rather than being assigned wholly to the year its start falls in.
    """
    kept = pd.read_csv(KEPT_CSV)
    kept = kept[
        (kept["plant_group"] == KLASS)
        & (kept["duration_days"] >= UNIT_OUTAGE_MIN_DAYS)
    ]
    layup = (
        pd.read_csv(LAYUP_CSV)
        if LAYUP_CSV.exists()
        else pd.DataFrame(columns=list(kept.columns) + ["out_of_merit_share"])
    )
    if len(layup):
        layup = layup[layup["plant_group"] == KLASS]

    states = campd.merit_panel_states_for_iso(ISO)
    panels, panel_ok = {}, {}
    for year in YEARS:
        n = len(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))
        p = build_merit_order_panel(ISO, year, n, states, MERIT_RCC_PCTL)
        panels[year] = p
        panel_ok[year] = p is not None

    buckets = {"no_panel": 0.0, "unidentified": 0.0, "unpriceable": 0.0, "below_frac": 0.0}
    oom_kept: list[float] = []
    n_windows = 0
    units_unidentified: set[str] = set()
    units_seen: set[str] = set()
    for r in kept.itertuples(index=False):
        start = pd.Timestamp(str(r.outage_start))
        end = pd.Timestamp(str(r.outage_end))
        touched = False
        for year in YEARS:
            span = _year_overlap(start, end, year)
            if span is None:
                continue
            touched = True
            s, e = span
            h = float(e - s)
            key = (int(r.facility_id), str(r.unit_id))
            units_seen.add(f"{key[0]}:{key[1]}")
            panel = panels[year]
            if panel is None:
                buckets["no_panel"] += h
                continue
            if key not in panel.srmc:
                buckets["unidentified"] += h
                units_unidentified.add(f"{key[0]}:{key[1]}")
                continue
            share = panel.out_of_merit_share(key, s, min(e, len(panel.rcc)))
            if share is None:
                buckets["unpriceable"] += h
            else:
                oom_kept.append(float(share))
                buckets["below_frac"] += h
        if touched:
            n_windows += 1

    total_h = sum(buckets.values())
    shares = {k: (v / total_h if total_h else 0.0) for k, v in buckets.items()}
    top = max(shares, key=shares.get) if total_h else None

    layup_h = 0.0
    for r in layup.itertuples(index=False):
        start, end = pd.Timestamp(str(r.outage_start)), pd.Timestamp(str(r.outage_end))
        for year in YEARS:
            span = _year_overlap(start, end, year)
            if span:
                layup_h += float(span[1] - span[0])

    return {
        "gate": "G2 — why does the armed merit-order guard keep NYISO ST_GAS windows?",
        "verdict": (
            "DISCHARGED" if total_h and shares[top] >= G2_SINGLE_CAUSE_BAR else "FAILED"
        ),
        "single_cause_bar": G2_SINGLE_CAUSE_BAR,
        "dominant_cause": top,
        "dominant_share": round(shares.get(top, 0.0), 4) if top else None,
        "panel_built_by_year": panel_ok,
        "kept_st_gas_windows_touching_2023_2025": int(n_windows),
        "kept_window_hours_in_scored_years": round(total_h, 1),
        "attribution_share": {k: round(v, 4) for k, v in shares.items()},
        "attribution_hours": {k: round(v, 1) for k, v in buckets.items()},
        "st_gas_units_in_kept_windows": len(units_seen),
        "st_gas_units_unidentified_by_panel": sorted(units_unidentified),
        "layup_st_gas_windows_removed_total": int(len(layup)),
        "layup_st_gas_window_hours_removed_in_scored_years": round(layup_h, 1),
        "layup_out_of_merit_share": (
            {
                "n": int(len(layup)),
                "mean": round(float(layup["out_of_merit_share"].mean()), 4),
            }
            if len(layup) and "out_of_merit_share" in layup.columns
            else None
        ),
        "merit_oom_frac": MERIT_OOM_FRAC,
        "merit_rcc_pctl": MERIT_RCC_PCTL,
        "out_of_merit_share_of_kept_priced": {
            "n": len(oom_kept),
            "mean": round(float(np.mean(oom_kept)), 4) if oom_kept else None,
            "p50": round(float(np.median(oom_kept)), 4) if oom_kept else None,
            "p90": round(float(np.percentile(oom_kept, 90)), 4) if oom_kept else None,
        },
    }


# ------------------------------------------------------------------------ G3 --


def g3_shape_or_level() -> dict:
    per_year = {}
    for year in YEARS:
        px = actual_price(year, "rt")
        mo, me = model_hourly(year, KLASS), measured_hourly(year, KLASS)
        order = np.argsort(px)
        half = HOURS // 2
        bottom, top10 = order[:half], order[int(HOURS * 0.9) :]
        m_tot, x_tot = float(mo.sum()), float(me.sum())
        m_bot = float(mo[bottom].sum()) / m_tot if m_tot else 0.0
        x_bot = float(me[bottom].sum()) / x_tot if x_tot else 0.0
        m_top = float(mo[top10].sum()) / m_tot if m_tot else 0.0
        x_top = float(me[top10].sum()) / x_tot if x_tot else 0.0
        # Per-band model/measured ratio against the annual ratio (LEVEL branch).
        ann = (m_tot / x_tot) if x_tot else float("nan")
        bands = np.array_split(order, G3_N_BANDS)
        band_rows = []
        for i, b in enumerate(bands):
            mb, xb = float(mo[b].sum()), float(me[b].sum())
            r = (mb / xb) if xb > 0 else None
            band_rows.append(
                {
                    "band": i,
                    "mean_price": round(float(px[b].mean()), 2),
                    "model_gwh": round(mb / 1e3, 1),
                    "measured_gwh": round(xb / 1e3, 1),
                    "ratio": (round(r, 3) if r is not None else None),
                    "rel_departure_from_annual": (
                        round(abs(r - ann) / ann, 3) if r is not None and ann else None
                    ),
                }
            )
        deps = [b["rel_departure_from_annual"] for b in band_rows if b["rel_departure_from_annual"] is not None]
        per_year[year] = {
            "annual_model_over_measured": round(ann, 4),
            "model_bottom_half_share": round(m_bot, 4),
            "measured_bottom_half_share": round(x_bot, 4),
            "bottom_half_share_ratio": round(m_bot / x_bot, 4) if x_bot else None,
            "model_top_decile_share": round(m_top, 4),
            "measured_top_decile_share": round(x_top, 4),
            "max_rel_band_departure": round(max(deps), 3) if deps else None,
            "bands": band_rows,
        }
    ratios = [per_year[y]["bottom_half_share_ratio"] or 0.0 for y in YEARS]
    tops_ok = all(
        per_year[y]["model_top_decile_share"] <= per_year[y]["measured_top_decile_share"]
        for y in YEARS
    )
    shape = min(ratios) >= G3_SHAPE_RATIO and tops_ok
    uniform = all(
        (per_year[y]["max_rel_band_departure"] or 1.0) <= G3_LEVEL_UNIFORM_TOL
        for y in YEARS
    )
    top_heavy = all(
        per_year[y]["model_top_decile_share"] > per_year[y]["measured_top_decile_share"]
        for y in YEARS
    )
    verdict = "SHAPE" if shape else ("LEVEL" if (uniform or top_heavy) else "NEITHER")
    return {
        "gate": "G3 — is the ST_GAS defect the offer's SHAPE or its LEVEL?",
        "verdict": verdict,
        "price_basis": "actual NYISO RT LBMP (data/raw/_validation-source)",
        "thresholds": {
            "shape_bottom_half_ratio": G3_SHAPE_RATIO,
            "level_uniform_tol": G3_LEVEL_UNIFORM_TOL,
        },
        "shape_branch_met": bool(shape),
        "level_branch_uniform": bool(uniform),
        "level_branch_top_heavy": bool(top_heavy),
        "per_year": per_year,
    }


# ----------------------------------------------------------------------- G4' --


def g4_enumeration(cfg: dict) -> dict:
    diag = json.loads((KEEPER / "legitimacy_diagnostics.json").read_text())
    d2 = [r for r in diag["diagnostics"]["D2"]["rows"] if r.get("class") == KLASS]
    d2_ids = {r["mechanism"] for r in d2}
    armed, rows, unattributed = [], [], []
    for name in G4_CANDIDATES:
        val = cfg.get(name, "<absent from run_config>")
        is_armed = bool(val) and val != "<absent from run_config>"
        row = {"field": name, "value": val, "armed": is_armed}
        if not is_armed:
            row["status"] = "not armed"
        elif name in G4_INERT_REASON:
            row["status"] = "armed, INERT for ST_GAS"
            row["reason"] = G4_INERT_REASON[name]
        elif G4_D2_ID.get(name) in d2_ids:
            row["status"] = "armed, ATTRIBUTED in D-2"
            row["d2_mechanism"] = G4_D2_ID[name]
        else:
            row["status"] = "armed, UNATTRIBUTED"
            unattributed.append(name)
        if is_armed:
            armed.append(name)
        rows.append(row)
    # The D-2 forced/economic split — a REPORT line, never a gate (PREREG §5.1).
    split = {}
    for year in YEARS:
        yr = [r for r in d2 if r["year"] == year]
        tot = yr[0]["class_total_twh"] if yr else None
        forced = sum(r["forced_twh"] for r in yr)
        split[year] = {
            "class_total_twh_d2_basis": tot,
            "forced_twh": round(forced, 4),
            "forced_share": round(forced / tot, 4) if tot else None,
            "economic_residual_twh": round(tot - forced, 4) if tot else None,
            "by_mechanism": {r["mechanism"]: r["forced_twh"] for r in yr},
        }
    # Any D-2 ST_GAS mechanism the fixed candidate list failed to anticipate.
    missed = sorted(d2_ids - set(G4_D2_ID.values()))
    return {
        "gate": "G4' — rule 19 [R-ONE-MECH]: any UNATTRIBUTED armed ST_GAS forcing channel?",
        "verdict": "DISCHARGED" if not unattributed and not missed else "FAILED",
        "unattributed_channels": unattributed,
        "d2_mechanisms_absent_from_the_fixed_candidate_list": missed,
        "armed_candidates": armed,
        "candidates": rows,
        "forced_vs_economic_REPORT_ONLY": split,
    }


# ----------------------------------------------------------------------- main --


def main() -> None:
    cfg = scenario_config()
    g1, g5 = g1_and_g5(cfg)
    rec = {
        "session": "nyiso-178",
        "prereg": "results/calibration/PREREG-nyiso178-offer-side-idling.md",
        "keeper_control": "2026-09-02-nyiso-177-vintage-matched",
        "bundle": str(KEEPER.relative_to(REPO)),
        "years": list(YEARS),
        "klass": KLASS,
        "G1": g1,
        "G2": g2_guard_attribution(),
        "G3": g3_shape_or_level(),
        "G4p": g4_enumeration(cfg),
        "G5": g5,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1, default=float))

    print(f"\n=== nyiso-178 phase 0 — {KLASS}, keeper {rec['keeper_control']}")
    print(f"\nG1 {g1['verdict']}   (gated on the EXACT LP envelope)")
    for y in YEARS:
        r = g1["per_year"][y]
        print(
            f"  {y}  cap {r['capacity_mw']:.0f} MW  avail {r['mean_availability']:.3f}"
            f"  envelope {r['envelope_twh']:.2f} TWh   model {r['model_twh']:.2f}"
            f"  actual {r['actual_twh']:.2f}"
            f"   hours AT envelope {r['hours_at_envelope']}"
            f" ({r['share_hours_at_envelope']*100:.2f} %)"
            f"  util mean {r['mean_utilisation']:.3f} p99 {r['p99_utilisation']:.3f}"
            f" max {r['max_utilisation']:.3f}"
        )
        a = r["robustness_true_vintage_envelope"]
        print(
            f"        true-vintage robustness: avail {a['mean_availability']:.3f}"
            f"  hours AT envelope {a['hours_at_envelope']}"
            f" ({a['share_hours_at_envelope']*100:.2f} %)"
            f"  util mean {a['mean_utilisation']:.3f}"
            f"  top-decile {a['top_decile_mean_utilisation']:.3f}"
        )
        d9 = r["utilisation_by_actual_price_decile"][-1]
        print(
            f"        top price decile (${d9['mean_price']:.0f}): envelope "
            f"{d9['mean_envelope_mw']:.0f} MW  model {d9['mean_model_mw']:.0f} MW"
            f"  util {d9['mean_utilisation']:.3f}  p95 {d9['p95_utilisation']:.3f}"
            f"  hours at envelope {d9['hours_at_envelope']}"
        )
    g2 = rec["G2"]
    print(f"\nG2 {g2['verdict']}  dominant {g2['dominant_cause']} "
          f"{g2['dominant_share']}  kept "
          f"{g2['kept_st_gas_windows_touching_2023_2025']} windows / "
          f"{g2['kept_window_hours_in_scored_years']:.0f} h; guard removed "
          f"{g2['layup_st_gas_windows_removed_total']} windows / "
          f"{g2['layup_st_gas_window_hours_removed_in_scored_years']:.0f} h")
    print(f"  attribution {g2['attribution_share']}")
    g3 = rec["G3"]
    print(f"\nG3 {g3['verdict']}")
    for y in YEARS:
        r = g3["per_year"][y]
        print(
            f"  {y}  bottom-half share model {r['model_bottom_half_share']:.3f} vs "
            f"measured {r['measured_bottom_half_share']:.3f} "
            f"(ratio {r['bottom_half_share_ratio']})  top-decile "
            f"{r['model_top_decile_share']:.3f} vs {r['measured_top_decile_share']:.3f}"
            f"  annual m/x {r['annual_model_over_measured']:.3f}"
        )
    g4 = rec["G4p"]
    print(f"\nG4' {g4['verdict']}  unattributed {g4['unattributed_channels']}"
          f"  missed-from-list {g4['d2_mechanisms_absent_from_the_fixed_candidate_list']}")
    for y in YEARS:
        s = g4["forced_vs_economic_REPORT_ONLY"][y]
        print(f"  {y}  forced {s['forced_twh']} TWh ({s['forced_share']}) of "
              f"{s['class_total_twh_d2_basis']}")
    print(f"\nG5 {g5['verdict']}  relief {g5['relief_fields']}")
    for b in g5["per_bin"][2023]:
        print(
            f"  {b['plant_code']:>6}  {b['lp_pmax_mw']:>7.1f} MW  online "
            f"{b['online_year_min_max']}  overlay {b['mean_overlay_ufac']:.3f}"
            f"  x statistical {b['implied_statistical_layer']}"
            f"  = composed {b['mean_composed_availability']:.3f}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
