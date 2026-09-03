"""miso-203 — phase 0 for the ambient capability derate anchored at the NET-SUMMER RATING CONDITION.

PREREG: ``results/calibration/PREREG-miso203-summer-peak-anchor-2026-09-03.md``
(pushed at ``011b2420`` before any adjudicating statistic).

The charter re-opens MISO's merchant ambient-derate cell, which miso-139 left at
``REFUSED-AT-G0``.  Rule 28(a)'s new evidence is (i) the miso-202 anatomy, which
re-aims the object from the mean-LMP LEVEL to a 15-hour TAIL, and (ii) the
primary-source reference condition for the EIA-860 net-summer rating — *"at the
time of summer peak demand"* — which is neither of the two anchoring conventions
miso-139 tested.

Gates, all measured on committed inputs with **no LP solved**:

**G-B summer-level neutrality (GATING).**  miso-139's +/-1 % basis rule inherited
verbatim: the candidate hinge must not move an armed class's summer-hours mean
capability.  Measured on the model's OWN ``generators_to_fleet_arrays`` ->
``_availability_matrix``, so every overlay and the trailing clip are the code's.

**G-C tail reach.**  Capability removed, MW, in the 15 top-1 %-of-actual-price
Jun-Jul hours — the anatomy's own scarce-hour set, same hub series, same
definition.

**G-D does it make reserves bind (GATING).**  The G-C removal against the model's
own scarce-hour reserve margin (reserve-eligible idle capability minus the four
families' requirement), from the keeper's committed sidecars.  Licensed only at
>= 25 %.

**N-0 REPRODUCTION.**  The hinge is applied here as a multiplicative overlay on
the model's own control availability matrix, because production's
``gt_ambient_derate`` block is unreachable under the keeper (its guard is
``and not _td_on``, and the keeper sets ``temp_dependent_derate=True``).  N-0
asserts that overlay reproduces the production block EXACTLY on a
``temp_dependent_derate=False`` pair, so the reconstruction is production's, not
a reimplementation.  A reconstruction that does not reproduce production measures
nothing.

Governance: rule 13 ``[R-MEASURED]`` — every input is a registration rating, a
measured dry-bulb or metered load, entering as a forward-reproducible formula;
the keeper's committed sidecars are read for dispatch/requirement only and never
fed back.  Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only.  Rule 25
``[R-ISO-SCOPE]`` — only MISO's own identified slopes are armable; the committed
literature and ``gt_ambient_derate`` defaults are carried DIAGNOSTIC ONLY.

Usage::

    python3 scripts/probes/_miso203_summer_peak_anchor_phase0.py
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

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.eia_loader import iso_zone_hourly_drybulb  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
KEEPER = REPO / "results/calibration/miso202_unitclip_B"
HUB_LMP = REPO / "data/raw/lmp-data/MISO"
OUT = REPO / "results/calibration/_miso203_summer_peak_anchor_phase0.json"

# Armed scope, fixed by miso-139's G-1 identification (inherited verbatim, NOT
# re-derived): COAL (0.00025/degC) and ST_GAS (0.00033) are excluded BY
# MEASUREMENT; the CHP classes already carry the committed mean-anchored curve
# and stacking a second treatment on them would breach rule 19 [R-ONE-MECH].
ARMED = ("CT_PEAKER", "CC_REGULAR")
MISO_SLOPES = {"CT_PEAKER": 0.00363, "CC_REGULAR": 0.00192}
# DIAGNOSTIC ONLY (rule 25 / TRAP 3) — never used to license.
LIT_SLOPES = {"CT_PEAKER": 0.0126, "CC_REGULAR": 0.0076}
GT_DEFAULT_SLOPES = {"CT_PEAKER": 0.006, "CC_REGULAR": 0.004}
GT_DEFAULT_REF_C = 35.0  # docs/parameter-citations.md:1314 "needs-citation"

# EIA-860's summer window, verbatim from the glossary definition quoted in the
# PREREG: "period of June 1 through September 30".
SUMMER_MONTHS = (6, 7, 8, 9)
# The rating is demonstrated at "the time of summer peak demand": the anchor is
# the load-weighted mean dry-bulb over the top PEAK_FRAC of in-window load
# hours.  Same construction miso-139 G-1 used for its dT denominator.
PEAK_FRAC = 0.01
# Reserve-eligible classes for the G-D margin (the online thermal + hydro set).
RESERVE_ELIGIBLE = (
    "COAL",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_LIGNITE",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "hydro",
)
G_B_TOL = 0.01  # miso-139's +/-1 % basis rule, inherited verbatim
G_D_LICENSE = 0.25  # removal must be >= 25 % of the smallest scarce-hour margin


def _hour_month(hours: int = HOURS) -> np.ndarray:
    """Calendar month (1-12) per hour of the model's FIXED non-leap 8760 clock.

    ``outages._hour_of_year`` uses a 28-day February in every year; hour-of-year
    arithmetic that counts Feb as 29 in 2024 is a silent 24-hour offset.
    """
    lens = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return np.concatenate([np.full(n * 24, m + 1) for m, n in enumerate(lens)])[:hours]


def keeper_config(year: int) -> ScenarioConfig:
    """Rebuild the keeper's ScenarioConfig from its committed run_config dump."""
    dump = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    hints = typing.get_type_hints(ScenarioConfig)
    out: dict[str, object] = {}
    for f in dataclasses.fields(ScenarioConfig):
        if f.name not in dump:
            continue
        val, ann = dump[f.name], str(hints.get(f.name, ""))
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


def hub_hourly_rt(year: int) -> np.ndarray | None:
    """Hub-average hourly RT LMP — the anatomy's own series, same construction."""
    path = HUB_LMP / f"miso_hub_lmp_{year}_rt.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path)
    df = df[df["value"] == "LMP"]
    he = [f"he{i:02d}" for i in range(1, 25)]
    df["date"] = pd.to_datetime(df["date"])
    arr = df.groupby("date")[he].mean().sort_index().to_numpy().ravel()
    return arr[:HOURS] if len(arr) >= HOURS else None


# ------------------------------------------------------------------ G-A anchor


def zone_weather(year: int) -> dict[str, np.ndarray]:
    """The identical hourly zone dry-bulb series the LP consumes."""
    out = {}
    for z in [z.name for z in get_iso_config(ISO).zones]:
        t = iso_zone_hourly_drybulb(ISO, year, HOURS, zone=z)
        if t is not None:
            out[z] = np.asarray(t, float)
    return out


def summer_peak_anchor(year: int, temps: dict[str, np.ndarray]) -> dict:
    """T_ref per zone: load-weighted mean dry-bulb over the top-1 % Jun-Sep load hours.

    This IS the EIA-860 net-summer rating's reference condition, stated in the
    glossary as "the time of summer peak demand (period of June 1 through
    September 30)".  Zero free parameters; regenerates for a forward year from
    forward drivers (rule 13 [R-MEASURED]).
    """
    mon = _hour_month()
    summer = np.isin(mon, SUMMER_MONTHS)
    # Zone demand from the keeper's own committed P1 system sidecar — the
    # metered load the LP actually consumed, at the model's own 8760 clock.
    sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    zdem = {
        z: g.sort_values("hour")["demand"].to_numpy() for z, g in sysd.groupby("zone")
    }
    out = {}
    for z, t in temps.items():
        d = zdem.get(z)
        if d is None or len(d) < HOURS:
            continue
        d = np.asarray(d, float)[:HOURS]
        idx = np.where(summer)[0]
        k = max(1, int(round(PEAK_FRAC * idx.size)))
        top = idx[np.argsort(d[idx])[-k:]]
        out[z] = {
            "t_ref_c": float(np.average(t[top], weights=d[top])),
            "n_peak_hours": int(k),
            "peak_load_mw_mean": float(d[top].mean()),
            "summer_mean_c": float(t[summer].mean()),
            "annual_mean_c": float(t.mean()),
        }
    return out


# ------------------------------------------------- capability, control and arm


def control_capability(year: int, cfg: ScenarioConfig):
    """The model's own (pmax x availability) matrix under the keeper config."""
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
    fa = generators_to_fleet_arrays(gens, zones, HOURS, iso=ISO, config=cfg, year=year)
    return gens, fa


def hinge_factor(gens, temps, t_ref, slopes) -> np.ndarray:
    """(n_gen, 8760) multiplier 1 - slope x max(0, T_zone - T_ref_zone).

    Exactly production's ``gt_ambient_derate`` form:
        extra(t) = slope_class x max(0, tmax_zone(t) - ref_c);  avail *= 1 - extra
    ``t_ref`` may be per-zone (the physically correct, per-zone rating condition)
    or a scalar (what the committed scalar field can express today).
    """
    f = np.ones((len(gens), HOURS), float)
    over_cache: dict[tuple[str, float], np.ndarray] = {}
    for i, g in enumerate(gens):
        s = slopes.get(g.plant_group)
        t = temps.get(g.zone)
        if s is None or t is None:
            continue
        if isinstance(t_ref, dict):
            if g.zone not in t_ref:
                continue
            ref = float(t_ref[g.zone])
        else:
            ref = float(t_ref)
        key = (g.zone, ref)
        if key not in over_cache:
            over_cache[key] = np.maximum(0.0, t - ref)
        f[i] = 1.0 - s * over_cache[key]
    return f


def n0_reproduction(year: int, cfg: ScenarioConfig, temps) -> dict:
    """Assert the overlay reproduces production's ``gt_ambient_derate`` EXACTLY.

    Production's block is unreachable under the keeper (guard ``and not _td_on``),
    so it is exercised on a ``temp_dependent_derate=False`` pair at the committed
    scalar ref/slopes, and the overlay is applied to the SAME control.
    """
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
    c0 = dataclasses.replace(cfg, temp_dependent_derate=False, gt_ambient_derate=False)
    c1 = dataclasses.replace(cfg, temp_dependent_derate=False, gt_ambient_derate=True)
    a0 = generators_to_fleet_arrays(
        gens, zones, HOURS, iso=ISO, config=c0, year=year
    ).availability
    a1 = generators_to_fleet_arrays(
        gens, zones, HOURS, iso=ISO, config=c1, year=year
    ).availability
    # Production's gt block reads the day-flat zone TMAX, not the hourly
    # reconstruction, so N-0 rebuilds the overlay on that same series.
    from market_sim.data.eia_loader import iso_zone_tmax

    tmax = {}
    for z in zones:
        t = iso_zone_tmax(ISO, year, HOURS, zone=z)
        if t is not None and t[0] is not None:
            tmax[z] = np.asarray(t[0], float)
    gt_scope = dict(GT_DEFAULT_SLOPES)
    gt_scope["CC_CHP"] = GT_DEFAULT_SLOPES["CC_REGULAR"]
    gt_scope["CT_CHP"] = GT_DEFAULT_SLOPES["CT_PEAKER"]
    recon = np.clip(a0 * hinge_factor(gens, tmax, GT_DEFAULT_REF_C, gt_scope), 0.0, 1.0)
    d = recon - a1
    diff = float(np.abs(d).max())
    return {
        "max_abs_diff": diff,
        "reproduces_exactly": bool(diff < 1e-12),
        "cells_overlay_removes_MORE": int((d < -1e-12).sum()),
        "cells_overlay_removes_LESS": int((d > 1e-12).sum()),
        "is_upper_bound": bool((d > 1e-12).sum() == 0),
        "n_units": int(len(gens)),
        "n_units_differing": int((np.abs(d).max(axis=1) > 1e-12).sum()),
        "production_block_moved": bool(float(np.abs(a1 - a0).max()) > 0),
        "note": (
            "Production composes the derate with the LATER retiree CEMS "
            "availability cap (arrays.py:1407, an np.minimum) as min(a*f, cap); "
            "the overlay computes min(a, cap)*f. The two differ only where that "
            "cap binds, and since f <= 1 the overlay can then only remove MORE. "
            "Every reach number below is therefore an UPPER BOUND on the "
            "mechanism's real reach, which is the conservative direction for a "
            "refusal."
        ),
    }


def main() -> None:
    report: dict = {
        "charter": (
            "miso-203 queue item 1 — the merchant ambient capability derate, "
            "re-opened on a MECHANISM change (the anchor) and judged against the "
            "TAIL object the miso-202 anatomy measured, not the level object "
            "miso-139 refused it for. No LP solved."
        ),
        "keeper": "2026-09-03-miso-202-unitclip",
        "prereg": "PREREG-miso203-summer-peak-anchor-2026-09-03.md @ 011b2420",
        "g_a_reference_condition": {
            "source": "EIA glossary, 'Net summer capacity', retrieved 2026-09-03",
            "quote": (
                "The maximum output, commonly expressed in megawatts (MW), that "
                "generating equipment can supply to system load, as demonstrated "
                "by a multi-hour test, at the time of summer peak demand (period "
                "of June 1 through September 30.)"
            ),
            "consequence": (
                "EIA-860 states NO nominal reference temperature. The reference "
                "condition is the ambient at the time of summer peak demand, so "
                "the admissible anchor is MISO's own load-weighted top-1 % "
                "Jun-Sep dry-bulb — measured, per zone, below."
            ),
            "committed_gt_ambient_ref_c": GT_DEFAULT_REF_C,
            "committed_ref_c_citation_status": (
                "docs/parameter-citations.md:1314 — 'auto-generated, "
                "needs-citation'. Unsourced; carried DIAGNOSTIC ONLY (TRAP 5)."
            ),
        },
        "structural_finding": {
            "mechanism_already_exists": "ScenarioConfig.gt_ambient_derate",
            "form": "extra(t) = slope x max(0, tmax_zone(t) - ref_c); avail *= 1 - extra",
            "unreachable_on_keeper": (
                "arrays.py guards the block with 'and not _td_on'; the keeper sets "
                "temp_dependent_derate=True (scope CT_CHP/ST_CHP only), so the "
                "guard is GLOBAL while the scope is PER-CLASS and arming "
                "gt_ambient_derate for MISO's merchant classes would change "
                "nothing today."
            ),
        },
        "n0_reproduction": {},
        "g_a_anchor": {},
        "g_b_summer_neutrality": {},
        "g_c_tail_reach": {},
        "g_d_reserve_binding": {},
    }

    mon = _hour_month()
    summer = np.isin(mon, SUMMER_MONTHS)
    jun_jul = np.isin(mon, (6, 7))

    for year in YEARS:
        cfg = keeper_config(year)
        temps = zone_weather(year)
        report["n0_reproduction"][str(year)] = n0_reproduction(year, cfg, temps)

        anchors = summer_peak_anchor(year, temps)
        report["g_a_anchor"][str(year)] = {
            z: {k: round(v, 3) if isinstance(v, float) else v for k, v in a.items()}
            for z, a in anchors.items()
        }
        t_ref = {z: a["t_ref_c"] for z, a in anchors.items()}

        gens, fa = control_capability(year, cfg)
        groups = np.array([g.plant_group for g in gens])
        base_avail = fa.availability
        cap_ctrl = fa.pmax[:, None] * base_avail

        variants = {
            "measured_anchor_miso_slopes": (t_ref, MISO_SLOPES),
            "measured_anchor_literature_slopes__DIAGNOSTIC": (t_ref, LIT_SLOPES),
            "ref35_miso_slopes__DIAGNOSTIC": (GT_DEFAULT_REF_C, MISO_SLOPES),
            "ref35_gt_default_slopes__DIAGNOSTIC": (
                GT_DEFAULT_REF_C,
                GT_DEFAULT_SLOPES,
            ),
        }

        # ---------------------------------------------------------- G-B
        gb: dict = {}
        cap_arm_store: dict[str, np.ndarray] = {}
        for name, (ref, slopes) in variants.items():
            arm_avail = np.clip(
                base_avail * hinge_factor(gens, temps, ref, slopes), 0, 1
            )
            cap_arm = fa.pmax[:, None] * arm_avail
            cap_arm_store[name] = cap_arm
            per_class = {}
            for cls in ARMED:
                sel = groups == cls
                if not sel.any():
                    continue
                b = float(cap_ctrl[sel][:, summer].sum())
                a = float(cap_arm[sel][:, summer].sum())
                rel = a / b if b > 0 else None
                per_class[cls] = {
                    "summer_mean_rel": round(rel, 6) if rel else None,
                    "summer_delta_pct": round(100.0 * (rel - 1.0), 4) if rel else None,
                    "annual_rel": round(
                        float(cap_arm[sel].sum()) / float(cap_ctrl[sel].sum()), 6
                    ),
                    "within_1pct": bool(rel is not None and abs(rel - 1.0) < G_B_TOL),
                }
            gb[name] = per_class
        report["g_b_summer_neutrality"][str(year)] = gb

        # ---------------------------------------------------------- G-C
        act = hub_hourly_rt(year)
        if act is None:
            report["g_c_tail_reach"][str(year)] = {"error": "no committed hub RT file"}
            continue
        jj = np.where(jun_jul)[0]
        thr = float(np.percentile(act[jj], 99.0))
        scarce = jj[act[jj] >= thr]
        gc: dict = {
            "scarce_hours_definition": (
                f"Jun-Jul hours whose ACTUAL hub RT price is in the top 1 % of "
                f"Jun-Jul ({thr:.2f} $/MWh and above) — the anatomy's own set"
            ),
            "n_scarce_hours": int(scarce.size),
            "threshold_usd_per_mwh": round(thr, 2),
        }
        # P1: how far is the scarce-hour ambient from the rating condition?
        p1 = {}
        for z, t in temps.items():
            if z not in t_ref:
                continue
            p1[z] = {
                "t_ref_c": round(t_ref[z], 2),
                "scarce_hour_mean_c": round(float(t[scarce].mean()), 2),
                "scarce_hour_max_c": round(float(t[scarce].max()), 2),
                "scarce_minus_ref_c": round(float(t[scarce].mean() - t_ref[z]), 2),
            }
        gc["p1_scarce_vs_rating_condition"] = p1
        for name, cap_arm in cap_arm_store.items():
            removal = {}
            tot = 0.0
            for cls in ARMED:
                sel = groups == cls
                if not sel.any():
                    continue
                d = float(
                    (cap_ctrl[sel][:, scarce] - cap_arm[sel][:, scarce]).sum()
                ) / max(1, scarce.size)
                removal[cls] = round(d, 1)
                tot += d
            removal["TOTAL_MW"] = round(tot, 1)
            # miso-139's 732-hour comparison window, reported beside it (TRAP 2)
            aft = summer & np.isin(np.arange(HOURS) % 24, tuple(range(12, 18)))
            tot_aft = 0.0
            for cls in ARMED:
                sel = groups == cls
                if sel.any():
                    tot_aft += float(
                        (cap_ctrl[sel][:, aft] - cap_arm[sel][:, aft]).sum()
                    ) / int(aft.sum())
            removal["summer_aft_732h_TOTAL_MW"] = round(tot_aft, 1)
            gc[name] = removal
        report["g_c_tail_reach"][str(year)] = gc

        # ---------------------------------------------------------- G-D
        ch = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            k: g.sort_values("hour")["mw"].to_numpy() for k, g in ch.groupby("klass")
        }
        rf = pd.read_parquet(KEEPER / "hourly" / f"reserve_family_{year}.parquet")
        rf = rf[rf["pass"] == "P1"]
        req = rf.groupby("hour")["requirement_mw"].sum().sort_index().to_numpy()

        idle_broad = np.zeros(HOURS)
        idle_armed = np.zeros(HOURS)
        for cls in sorted(set(groups)):
            if not cls:
                continue
            sel = groups == cls
            capc = cap_ctrl[sel].sum(axis=0)
            d = disp.get(cls)
            d = np.zeros(HOURS) if d is None else np.asarray(d, float)[:HOURS]
            gap = np.maximum(0.0, capc - d)
            if cls in RESERVE_ELIGIBLE:
                idle_broad += gap
            if cls in ARMED:
                idle_armed += gap

        margin_broad = idle_broad - req
        margin_armed = idle_armed - req
        rem = gc["measured_anchor_miso_slopes"]["TOTAL_MW"]
        sm_broad = float(margin_broad[scarce].min())
        sm_armed = float(margin_armed[scarce].min())
        report["g_d_reserve_binding"][str(year)] = {
            "basis": (
                "reserve-eligible idle capability (model's own capability matrix "
                "minus its committed P1 class dispatch) minus the four families' "
                "summed requirement, in the G-C scarce hours."
            ),
            "reserve_requirement_mw_mean_scarce": round(float(req[scarce].mean()), 1),
            "idle_reserve_eligible_mw_mean_scarce": round(
                float(idle_broad[scarce].mean()), 1
            ),
            "idle_armed_classes_mw_mean_scarce": round(
                float(idle_armed[scarce].mean()), 1
            ),
            "margin_broad_mw_min_scarce": round(sm_broad, 1),
            "margin_broad_mw_mean_scarce": round(float(margin_broad[scarce].mean()), 1),
            "margin_armed_only_mw_min_scarce": round(sm_armed, 1),
            "removal_mw_measured_anchor": rem,
            "removal_share_of_broad_margin": round(rem / sm_broad, 4)
            if sm_broad > 0
            else None,
            "removal_share_of_armed_margin": round(rem / sm_armed, 4)
            if sm_armed > 0
            else None,
            "license_threshold": G_D_LICENSE,
            "G_D_PASS": bool(sm_broad > 0 and (rem / sm_broad) >= G_D_LICENSE),
            # TRAP 2: miso-139's 732-hour cushion, reported side by side
            "miso139_summer_aft_732h_idle_mw_mean": round(
                float(
                    idle_broad[
                        summer & np.isin(np.arange(HOURS) % 24, tuple(range(12, 18)))
                    ].mean()
                ),
                1,
            ),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=1))
    print(f"wrote {OUT}")
    for y in YEARS:
        d = report["g_d_reserve_binding"].get(str(y))
        if d:
            print(
                f"{y}: removal {d['removal_mw_measured_anchor']} MW vs broad margin "
                f"min {d['margin_broad_mw_min_scarce']} MW "
                f"({d['removal_share_of_broad_margin']}) -> G-D "
                f"{'PASS' if d['G_D_PASS'] else 'FAIL'}"
            )


if __name__ == "__main__":
    main()
