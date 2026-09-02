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


def bin_ages() -> dict[tuple[int, str], float]:
    """Capacity-weighted age basis: ``{(code, group): online_year}``."""
    gens = load_fleet_from_csv(ISO)
    num: dict[tuple[int, str], float] = {}
    den: dict[tuple[int, str], float] = {}
    for g in gens:
        grp = getattr(g, "plant_group", None)
        oy = getattr(g, "online_year", None)
        cap = float(getattr(g, "capacity_mw", 0.0) or 0.0)
        if grp is None or oy is None or cap <= 0.0:
            continue
        k = (int(g.plant_code), str(grp))
        num[k] = num.get(k, 0.0) + cap * float(oy)
        den[k] = den.get(k, 0.0) + cap
    return {k: num[k] / den[k] for k in num if den[k] > 0}


def envelopes(year: int) -> dict:
    """The three PREREG §5.3 ``ST_GAS`` envelopes, plus the G5 decomposition."""
    cap = _iso_plant_capacity(ISO, False, False)
    ufac = unit_outage_derate_factors(
        year, iso=ISO, per_unit_crosswalk=True, merit_order_guard=True
    )
    ages = bin_ages()
    _, w_base, w_rate, w_onset, d_base, d_rate, d_onset = THERMAL_AVAILABILITY[KLASS]

    summer = np.zeros(HOURS, dtype=bool)
    months = np.repeat(
        pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D").month.to_numpy()[:365],
        24,
    )[:HOURS]
    summer[np.isin(months, (6, 7, 8, 9))] = True

    env_overlay = np.zeros(HOURS)
    env_stat = np.zeros(HOURS)
    env_stat_summer = np.zeros(HOURS)
    total = 0.0
    per_bin = []
    for (code, grp), mw in sorted(cap.items()):
        if grp != KLASS:
            continue
        total += mw
        u = ufac.get((code, grp), np.ones(HOURS))
        oy = ages.get((code, grp))
        age = (year - oy) if oy else 0.0
        wefor = w_base + max(0.0, age - w_onset) * w_rate
        derate = d_base + max(0.0, age - d_onset) * d_rate
        stat = max(0.0, 1.0 - wefor - derate)
        s_wefor = SUMMER_WEFOR_SHARE * wefor
        stat_s = np.full(HOURS, stat)
        stat_s[summer] = max(0.0, 1.0 - s_wefor - derate)
        env_overlay += mw * u
        env_stat += mw * stat * u
        env_stat_summer += mw * stat_s * u
        per_bin.append(
            {
                "plant_code": int(code),
                "nameplate_mw": round(float(mw), 1),
                "online_year": (int(oy) if oy else None),
                "age": round(float(age), 1),
                "wefor_age": round(float(wefor), 4),
                "derate_age": round(float(derate), 4),
                "statistical_availability": round(float(stat), 4),
                "mean_overlay_ufac": round(float(np.mean(u)), 4),
                "mean_composed_availability": round(float(stat * np.mean(u)), 4),
            }
        )
    return {
        "total_capacity_mw": round(total, 1),
        "env_overlay": env_overlay,
        "env_stat": env_stat,
        "env_stat_summer": env_stat_summer,
        "per_bin": per_bin,
    }


def g1_and_g5(cfg: dict) -> tuple[dict, dict]:
    per_year, g5_bins = {}, {}
    for year in YEARS:
        e = envelopes(year)
        mo = model_hourly(year, KLASS)
        tot = e["total_capacity_mw"]
        row = {"capacity_mw": tot}
        for name in ("env_overlay", "env_stat", "env_stat_summer"):
            env = e[name]
            at = int((mo >= G1_AT_FRAC * env).sum())
            row[name] = {
                "mean_availability": round(float(env.mean() / tot), 4),
                "envelope_twh": round(float(env.sum()) / 1e6, 4),
                "hours_at_envelope": at,
                "share_hours_at_envelope": round(at / HOURS, 5),
                "mean_utilisation": round(float((mo / np.maximum(env, 1e-9)).mean()), 4),
                "p99_utilisation": round(
                    float(np.percentile(mo / np.maximum(env, 1e-9), 99)), 4
                ),
                "max_utilisation": round(float((mo / np.maximum(env, 1e-9)).max()), 4),
                "min_headroom_mw": round(float((env - mo).min()), 1),
            }
        row["model_twh"] = round(float(mo.sum()) / 1e6, 4)
        row["actual_twh"] = round(actual_class_twh(year, KLASS), 4)
        per_year[year] = row
        g5_bins[year] = e["per_bin"]

    def verdict(name: str) -> str:
        shares = [per_year[y][name]["share_hours_at_envelope"] for y in YEARS]
        if max(shares) >= G1_AVAIL_MIN_SHARE:
            return "AVAILABILITY-SIDE"
        if max(shares) < G1_OFFER_MAX_SHARE:
            return "OFFER-SIDE"
        return "MIXED"

    v_gated = verdict("env_stat")
    v_loose = verdict("env_overlay")
    g1 = {
        "gate": "G1 — is the composed ST_GAS availability envelope BINDING?",
        "gated_on": "env_stat (PREREG §5.3)",
        "verdict": v_gated if v_gated == v_loose else "MIXED",
        "verdict_env_stat": v_gated,
        "verdict_env_overlay": v_loose,
        "bounds_agree": v_gated == v_loose,
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
        "composition": "PRODUCT (fleet/arrays.py:1097 'Multiplies the statistical availability already set above')",
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
    print(f"\nG1 {g1['verdict']}  (env_stat {g1['verdict_env_stat']} / "
          f"env_overlay {g1['verdict_env_overlay']})")
    for y in YEARS:
        r = g1["per_year"][y]
        e = r["env_stat"]
        print(
            f"  {y}  cap {r['capacity_mw']:.0f} MW  composed avail "
            f"{e['mean_availability']:.3f}  envelope {e['envelope_twh']:.2f} TWh"
            f"  model {r['model_twh']:.2f}  actual {r['actual_twh']:.2f}"
            f"  hours AT envelope {e['hours_at_envelope']}"
            f" ({e['share_hours_at_envelope']*100:.2f} %)"
            f"  mean util {e['mean_utilisation']:.3f}  p99 {e['p99_utilisation']:.3f}"
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
            f"  {b['plant_code']:>6}  {b['nameplate_mw']:>7.1f} MW  online "
            f"{b['online_year']}  WEFOR {b['wefor_age']:.3f}  derate "
            f"{b['derate_age']:.3f}  stat {b['statistical_availability']:.3f}"
            f"  x overlay {b['mean_overlay_ufac']:.3f}  = "
            f"{b['mean_composed_availability']:.3f}"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
