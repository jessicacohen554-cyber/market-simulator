"""miso-139 — G-0 / G-1 / G-2 gates for the ambient capability-derate CLASS SCOPE.

PREREG: ``results/calibration/PREREG-miso139-ambient-derate-class-scope-2026-08-06.md``
(pushed at ``6263f43d`` before any adjudicating statistic).

Three gates, all measured on MISO's OWN committed inputs, no LP solved here:

**G-0 anchoring / double-count.** Builds the model's real availability matrix
(``generators_to_fleet_arrays`` -> ``_availability_matrix``) under the keeper
config and under each candidate convention, so the clip at ``availability <= 1``
and every other overlay are the code's own, not a reimplementation.  Reports the
per-window multipliers, the summer-mean capability against the net-summer basis
(the pre-registered decision rule) and the annual capability integral (Trap 1).

**G-1 identification.** The EIA-860 MISO two-point ambient slope, on the model's
own ``plant_group`` taxonomy and the model's own MISO fleet membership, with the
peak-hour definition varied over the pre-registered robustness set.

**G-2 binding.** Left to the companion probe once G-0/G-1 resolve.

Governance: rule 13 ``[R-MEASURED]`` — every input is a physical/registration
quantity, forward-reproducible; no price, benchmark or model output enters any
estimator.  Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.

Usage::

    .venv/bin/python scripts/probes/_miso139_derate_gates.py
"""

from __future__ import annotations

import dataclasses
import json
import sys
import typing
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.fuel_trajectories import SUMMER_CLASS_DERATE  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import iso_zone_hourly_drybulb  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso139_derate_gates.json"

# Candidate merchant classes.  COAL is carried through G-1 so its exclusion is a
# MEASUREMENT (miso-138 re-verification), never a scope assumption.
CANDIDATES = ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL")
COMMITTED_SCOPE = ("CT_CHP", "ST_CHP")

# miso-137's two windows.  Localisation only — never a magnitude (rules 1/21/24).
W_AFT = tuple(range(12, 18))  # h12-17
W_NIGHT = tuple(range(0, 6))  # h00-05
SUMMER_MONTHS = (6, 7, 8, 9)  # arrays.py::_SUMMER_MONTHS


def _hour_month(hours: int) -> np.ndarray:
    """Calendar month (1-12) per hour of a non-leap 8760 year."""
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    out = np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(lens)])
    return out[:hours]


def _hour_of_day(hours: int) -> np.ndarray:
    return np.arange(hours) % 24


def keeper_config(year: int) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config dump.

    Only fields the dataclass actually carries are passed; list dumps are
    coerced back to frozenset / tuple where the annotation says so, and str
    dumps back to Path.  ``weather_year``/``mode`` are pinned to the solve year
    exactly as the calibration driver does for a backcast.
    """
    dump = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    hints = typing.get_type_hints(ScenarioConfig)
    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.name not in dump:
            continue
        val = dump[f.name]
        ann = str(hints.get(f.name, ""))
        if val is None:
            out[f.name] = None
            continue
        if "frozenset" in ann and isinstance(val, list):
            val = frozenset(val)
        elif "tuple" in ann and isinstance(val, list):
            val = tuple(val)
        elif "Path" in ann and isinstance(val, str):
            val = Path(val)
        out[f.name] = val
    out["mode"] = "backcast"
    out["weather_year"] = year
    return ScenarioConfig(**out)  # type: ignore[arg-type]


def with_scope(cfg: ScenarioConfig, scope, anchored: bool, slopes: dict[str, float]):
    """Copy ``cfg`` with a new temp-derate class scope / anchor / slopes."""
    kw = {"temp_derate_classes": frozenset(scope), "temp_derate_mean_anchored": anchored}
    for cls, s in slopes.items():
        key = {
            "CT_PEAKER": "temp_derate_slope_ct",
            "CC_REGULAR": "temp_derate_slope_cc",
            "CC_CHP": "temp_derate_slope_cc",
            "ST_GAS": "temp_derate_slope_st_gas",
            "COAL": "temp_derate_slope_coal",
        }[cls]
        kw[key] = float(s)
    return dataclasses.replace(cfg, **kw)


# ---------------------------------------------------------------- G-0(a) weather


def weather_table() -> dict:
    """Per-zone, per-year dry-bulb anchors and window means (deg C)."""
    zones = [z.name for z in get_iso_config(ISO).zones]
    hod, mon = _hour_of_day(8760), _hour_month(8760)
    summer = np.isin(mon, SUMMER_MONTHS)
    rows = []
    for y in YEARS:
        for z in zones:
            t = iso_zone_hourly_drybulb(ISO, y, 8760, zone=z)
            if t is None:
                rows.append({"year": y, "zone": z, "series": None})
                continue
            t = np.asarray(t, float)
            rows.append(
                {
                    "year": y,
                    "zone": z,
                    "series": "hourly_drybulb",
                    "annual_mean_c": float(t.mean()),
                    "summer_mean_c": float(t[summer].mean()),
                    "summer_aft_mean_c": float(t[summer & np.isin(hod, W_AFT)].mean()),
                    "summer_night_mean_c": float(
                        t[summer & np.isin(hod, W_NIGHT)].mean()
                    ),
                    "winter_mean_c": float(t[np.isin(mon, (12, 1, 2))].mean()),
                    # P1: does the summer NIGHT sit above the ANNUAL anchor?
                    "night_minus_annual_c": float(
                        t[summer & np.isin(hod, W_NIGHT)].mean() - t.mean()
                    ),
                    "aft_minus_annual_c": float(
                        t[summer & np.isin(hod, W_AFT)].mean() - t.mean()
                    ),
                    "aft_minus_summer_c": float(
                        t[summer & np.isin(hod, W_AFT)].mean() - t[summer].mean()
                    ),
                    "night_minus_summer_c": float(
                        t[summer & np.isin(hod, W_NIGHT)].mean() - t[summer].mean()
                    ),
                }
            )
    return {"zones": zones, "rows": rows}


# ------------------------------------------------- G-0(b,c,d) capability integrals


def capability_integrals(year: int, conventions: dict) -> dict:
    """Class capability (MWh) by window, control vs each convention.

    Uses the model's OWN availability matrix, so the trailing
    ``np.clip(availability, 0, 1)`` (F3) and every other overlay are the code's.
    """
    cfg = keeper_config(year)
    gens = load_fleet_from_csv(
        ISO,
        get_iso_config(ISO),
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in get_iso_config(ISO).zones]
    groups = np.array([g.plant_group for g in gens])
    hod, mon = _hour_of_day(8760), _hour_month(8760)
    summer = np.isin(mon, SUMMER_MONTHS)
    masks = {
        "annual": np.ones(8760, bool),
        "summer": summer,
        "summer_aft": summer & np.isin(hod, W_AFT),
        "summer_night": summer & np.isin(hod, W_NIGHT),
        "nonsummer": ~summer,
    }

    def cap(fa) -> np.ndarray:
        return fa.pmax[:, None] * fa.availability

    base = cap(
        generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    )
    out: dict[str, dict] = {}
    for name, cfg_v in conventions.items():
        arm = cap(
            generators_to_fleet_arrays(
                gens, zones, 8760, iso=ISO, config=cfg_v, year=year
            )
        )
        per_class = {}
        for cls in sorted(set(groups)):
            if not cls:
                continue
            sel = groups == cls
            if not sel.any():
                continue
            b, a = base[sel], arm[sel]
            rec = {"n_units": int(sel.sum()), "pmax_mw": float(b[:, 0].sum() and 0.0)}
            rec["nameplate_basis_mw"] = float(
                np.array([g.pmax_mw for g in gens])[sel].sum()
            )
            for wname, m in masks.items():
                bs, as_ = float(b[:, m].sum()), float(a[:, m].sum())
                rec[f"{wname}_ctrl_gwh"] = bs / 1000.0
                rec[f"{wname}_arm_gwh"] = as_ / 1000.0
                rec[f"{wname}_rel"] = (as_ / bs) if bs > 0 else None
            per_class[cls] = rec
        out[name] = per_class
    return out


# ------------------------------------------------------------------ G-1 EIA-860


def eia860_two_point(year: int) -> dict:
    """MISO's OWN ambient slope from EIA-860 Summer/Winter capability.

    slope_k = (C_winter - C_summer) / (C_summer * (T_sum_peak - T_win_peak))

    Class membership and fleet scope come from the model's own loader, so the
    aggregate is the same population the LP dispatches.  The peak-hour dry-bulb
    pair is measured on the SAME hourly series the LP consumes, load-weighted
    with the SAME committed MISO demand, over the pre-registered robustness set.
    """
    from market_sim.data.eia_loader import load_demand

    gens = load_fleet_from_csv(ISO, get_iso_config(ISO), year=year)
    fleet = pd.DataFrame(
        [
            {
                "plant_code": int(g.plant_code),
                "unit_id": g.unit_id,
                "plant_group": g.plant_group,
                "zone": g.zone,
                "pmax_mw": float(g.pmax_mw),
            }
            for g in gens
            if g.plant_group
        ]
    )
    fleet["gen_id"] = fleet["unit_id"].str.split("_", n=1).str[1]

    raw = pd.read_parquet(REPO / "data/raw/eia-860/eia860_generator_operable.parquet")
    raw = raw.rename(
        columns={
            "Plant Code": "plant_code",
            "Generator ID": "gen_id",
            "Summer Capacity (MW)": "summer_mw",
            "Winter Capacity (MW)": "winter_mw",
        }
    )
    raw["plant_code"] = pd.to_numeric(raw["plant_code"], errors="coerce")
    for c in ("summer_mw", "winter_mw"):
        raw[c] = pd.to_numeric(raw[c], errors="coerce")
    raw["gen_id"] = raw["gen_id"].astype(str).str.strip()
    j = fleet.merge(
        raw[["plant_code", "gen_id", "summer_mw", "winter_mw"]],
        on=["plant_code", "gen_id"],
        how="left",
    )
    j = j[(j["summer_mw"] > 0) & (j["winter_mw"] > 0)]

    # ---- measured peak-hour dry-bulb pair, load-weighted over MISO's zones
    ic = get_iso_config(ISO)
    dem = np.asarray(load_demand(ISO, year, ic), float)
    znames = list(ic.zone_names)
    dz = {z: dem[i, :8760] for i, z in enumerate(znames) if dem[i].sum() > 0}
    tz = {}
    for z in dz:
        t = iso_zone_hourly_drybulb(ISO, year, 8760, zone=z)
        if t is not None:
            tz[z] = np.asarray(t, float)
    zz = [z for z in dz if z in tz]
    load = np.sum([dz[z] for z in zz], axis=0)
    tload = np.sum([dz[z] * tz[z] for z in zz], axis=0) / np.maximum(load, 1e-9)

    mon = _hour_month(8760)
    win_s = np.isin(mon, (6, 7, 8, 9))  # EIA-860 summer-rating window
    win_w = np.isin(mon, (12, 1, 2))  # EIA-860 winter-rating window

    def peak_t(mask: np.ndarray, spec: str) -> float:
        idx = np.flatnonzero(mask)
        lo = load[idx]
        if spec == "peakday":
            day = idx[int(np.argmax(lo))] // 24
            sel = idx[(idx // 24) == day]
        else:
            frac = {"top0.5": 0.005, "top1": 0.01, "top5": 0.05}[spec]
            k = max(1, int(round(frac * idx.size)))
            sel = idx[np.argsort(lo)[-k:]]
        return float(np.average(tload[sel], weights=load[sel]))

    specs = ("top0.5", "top1", "top5", "peakday")
    tpair = {s: (peak_t(win_s, s), peak_t(win_w, s)) for s in specs}

    res = {"year": year, "peak_drybulb_c": {s: list(v) for s, v in tpair.items()}}
    classes = {}
    for cls in sorted(set(j["plant_group"])):
        g = j[j["plant_group"] == cls]
        cs, cw = float(g["summer_mw"].sum()), float(g["winter_mw"].sum())
        ratio = (g["winter_mw"] - g["summer_mw"]) / g["summer_mw"]
        rec = {
            "n_units": int(len(g)),
            "summer_mw": cs,
            "winter_mw": cw,
            "agg_spread": (cw - cs) / cs if cs > 0 else None,
            "unit_spread_p50": float(ratio.median()),
            "unit_spread_p90": float(ratio.quantile(0.90)),
            "share_exactly_flat": float((ratio.abs() < 1e-9).mean()),
            "slope_per_c": {},
        }
        for s, (ts, tw) in tpair.items():
            dt = ts - tw
            rec["slope_per_c"][s] = ((cw - cs) / cs / dt) if (cs > 0 and dt > 0) else None
            rec["slope_per_c"][s + "_unitp50"] = (
                float(ratio.median()) / dt if dt > 0 else None
            )
        vals = [v for k, v in rec["slope_per_c"].items() if not k.endswith("_unitp50")]
        vals = [v for v in vals if v is not None]
        if vals:
            lo, hi, mid = min(vals), max(vals), float(np.median(vals))
            rec["robust_rel_spread"] = (hi - lo) / abs(mid) if mid else None
            rec["slope_primary"] = rec["slope_per_c"]["top1"]
        classes[cls] = rec
    res["classes"] = classes
    return res


def main() -> None:
    out: dict = {
        "prereg": "PREREG-miso139-ambient-derate-class-scope-2026-08-06.md @ 6263f43d",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "years": list(YEARS),
        "summer_class_derate": dict(SUMMER_CLASS_DERATE),
    }
    print("G-0(a) weather anchors ...")
    out["g0a_weather"] = weather_table()
    print("G-1 EIA-860 two-point ...")
    out["g1_eia860"] = {str(y): eia860_two_point(y) for y in YEARS}

    # MISO-OWN slopes: the 3-year mean of the pre-registered primary (top-1 %)
    # EIA-860 two-point estimate.  Pooling across the three measured peak pairs
    # is the only choice made here and it is not a fit — the class capability
    # ratings are identical across the vintage, so the year-to-year variation is
    # purely the measured peak-temperature pair.
    miso_slopes: dict[str, float] = {}
    for cls in ("CT_PEAKER", "CC_REGULAR", "ST_GAS", "COAL"):
        vals = [
            out["g1_eia860"][str(y)]["classes"][cls]["slope_primary"] for y in YEARS
        ]
        miso_slopes[cls] = float(np.mean(vals))
    out["g1_miso_own_slopes"] = miso_slopes
    out["committed_literature_slopes"] = {
        "CT_PEAKER": 0.0126,
        "CC_REGULAR": 0.0076,
        "ST_GAS": 0.0054,
        "COAL": 0.0040,
    }

    print("G-0(b,c,d) capability integrals ...")
    ARMED = ("CT_PEAKER", "CC_REGULAR")  # COAL/ST_GAS excluded by G-1 measurement
    g0 = {}
    for y in YEARS:
        base = keeper_config(y)
        convs = {
            # (A) as chartered: annual-mean anchor, flat summer derate retained
            "A_misoslope": with_scope(
                base, COMMITTED_SCOPE + ARMED, True, {c: miso_slopes[c] for c in ARMED}
            ),
            # (A) with the committed literature slopes — DIAGNOSTIC ONLY, never
            # armable for MISO (rule 25); shows what "just re-scope it" does.
            "A_literature": with_scope(
                base,
                COMMITTED_SCOPE + ARMED,
                True,
                {"CT_PEAKER": 0.0126, "CC_REGULAR": 0.0076},
            ),
            # (B) hinge + net-summer anchor.  NOTE: the anchor bool is global, so
            # this ALSO moves the committed CHP classes off their identified
            # convention — measured here so that cost is explicit, never hidden.
            "B_misoslope": with_scope(
                base, COMMITTED_SCOPE + ARMED, False, {c: miso_slopes[c] for c in ARMED}
            ),
            # (B) with literature slopes — DIAGNOSTIC ONLY (rule 25 forbids
            # arming them for MISO).  Tests whether the non-anchored branch's
            # unconditional rescale, _anchor / mean(raw[summer]), is calibrated
            # in FORM to literature-sized slopes: at those slopes the summer mean
            # of the hinge curve already sits near 1 - SUMMER_CLASS_DERATE, so
            # the rescale is ~1 and the non-summer year is left alone.
            "B_literature": with_scope(
                base,
                COMMITTED_SCOPE + ARMED,
                False,
                {"CT_PEAKER": 0.0126, "CC_REGULAR": 0.0076},
            ),
        }
        g0[str(y)] = capability_integrals(y, convs)
    out["g0_capability"] = g0

    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
