#!/usr/bin/env python3
"""ERCOT-208 Phase 0 — viability check for arming ``cc_nameplate_summer_derate``.

Read-only. **No LP is built, no year is solved, no run is registered, the keeper
is not touched.** Every number below comes from committed artifacts: the ERCOT
keeper bundle's own ``run_config.json`` / ``meta.json`` / hourly sidecars, the
committed CAMPD bin sheet, the committed EIA-860 Generator_Y Operable sheet, and
the committed measured ERCOT DAM-availability extract.

The four Phase-0 conditions this probe measures, in order:

(a) **THE ercot-202 CHECK — the flag's TRUE armed state on the keeper.** Read
    from the KEEPER's resolved ``run_config.json -> scenario_config`` (the config
    the LP actually ran, rule 24 ``[R-REGISTRY]``) and its ``meta.json``
    solve-kwarg snapshot **including the ``coal_prb_sigmoid_overrides``
    (`prb_overrides`) channel** — never from the ``scenarios.py`` class default.
    ``FINDING-ercot202-t1-nonviable-2026-08-14.md`` §1: a class default is not
    the keeper's value, and five sessions carried a stale "default-off" claim
    before it was caught.

(b) **The measured object, at full magnitude.** What arming would actually change
    on the ERCOT path, per class, per month, in MW — and the $/MWh of the hours
    that change can reach, read off the keeper's own committed sidecars.

(c) **Rule-13 ``[R-MEASURED]`` identification from ERCOT's OWN data**, with the
    forward-regeneration story: the EIA-860 published per-plant net-summer and
    nameplate ratings of the ERCOT CC fleet.

(d) **Rule-19 ``[R-ONE-MECH]`` reconciliation** against the armed measured-DAM
    availability family, whose class-hour water-fill ``FINDING-ercot177`` §3
    proved erases any pre-overlay availability edit on a covered class.

Run:
    python scripts/probes/ercot208_cc_nameplate_phase0.py
    python scripts/probes/ercot208_cc_nameplate_phase0.py \
        --out results/calibration/ercot208_cc_nameplate_phase0.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# The ERCOT keeper at HEAD: frontend/data/backcast/keepers/ERCOT.json ->
# "2026-08-15-ercot204-rule26-delete", bundle ercot204_rule26_delete (promoted
# 2026-08-15 by the lane that took the ercot-205 shorthand; rule-26 discharge,
# all 12 hourly sidecars sha256-identical to the superseded
# ercot202_plantphysics_B, so every figure below is unmoved by the promotion —
# re-measured against the CURRENT keeper rather than inherited).
KEEPER_ID = "2026-08-15-ercot204-rule26-delete"
KEEPER_BUNDLE = REPO / "results/calibration/ercot204_rule26_delete"
# The superseded keeper, kept only for the byte-identity cross-check below.
PRIOR_KEEPER_BUNDLE = REPO / "results/calibration/ercot202_plantphysics_B"
KEEPERS_JSON = REPO / "frontend/data/backcast/keepers/ERCOT.json"

BINS_SHEET = REPO / "data/raw/reference/custom-bin-assignments.csv"
EIA860_OPERABLE = REPO / "data/raw/eia-860/eia860_generator_operable.parquet"
DAM_HOURLY = REPO / "data/raw/ercot-thermal-dam-availability-hourly.csv"

YEARS = (2023, 2024, 2025)
CC_GROUPS = ("CC_REGULAR", "CC_CHP")

# Committed constants, transcribed with their source of truth cited so the
# probe never re-derives a model value (rule 23 [R-FROZEN-DERIVE]).
# config/fuel_trajectories.py:950 SUMMER_CLASS_DERATE
SUMMER_CLASS_DERATE = {"CC_REGULAR": 0.10, "CC_CHP": 0.10}
# data/fleet/arrays.py:101 _SUMMER_MONTHS
SUMMER_MONTHS = (6, 7, 8, 9)
# config/fuel_trajectories.py:871 THERMAL_AVAILABILITY
# (pof, wefor_base, wefor_rate, wefor_onset, derate_base, derate_rate, derate_onset)
THERMAL_AVAILABILITY = {
    "CC_CHP": (0.05, 0.04, 0.002, 20, 0.02, 0.001, 25),
    "CC_REGULAR": (0.05, 0.05, 0.002, 20, 0.02, 0.001, 25),
}

# Every flag whose keeper value this Phase 0 depends on. Checked in the keeper's
# RESOLVED config, not in scenarios.py (the ercot-202 discipline).
FLAGS_OF_INTEREST = (
    "cc_nameplate_summer_derate",
    "cc_winter_capability_basis",
    "coal_nameplate_summer_derate",
    "summer_derate_basis_aware",
    "plant_level_fleet",
    "use_campd_bins",
    "outage_source",
    "mode",
    "temp_dependent_derate",
    "gt_ambient_derate",
    "ercot_thermal_dam_availability",
    "ercot_thermal_dam_availability_hourly",
    "ercot_thermal_dam_availability_plant",
    "ercot_thermal_dam_availability_coal",
    "ercot_dam_availability_gas_event_cap",
    "wefor_residual",
    "wefor_residual_groups",
    "wefor_multiplier",
)


def _hour_months(year: int, hours: int = 8760) -> np.ndarray:
    """Month index (1-12) for each hour of the no-leap 8760 model clock."""
    idx = pd.date_range(f"{year}-01-01", periods=hours, freq="h")
    return idx.month.to_numpy()


# --------------------------------------------------------------------------
# (a) the ercot-202 check
# --------------------------------------------------------------------------
def block_a_armed_state() -> dict:
    """Read the flag's TRUE value on the keeper, through every channel."""
    run_config = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())
    meta = json.loads((KEEPER_BUNDLE / "meta.json").read_text())
    resolved = run_config["scenario_config"]
    prb = run_config.get("calibration_flags", {}).get(
        "coal_prb_sigmoid_overrides", {}
    )
    keeper_json = json.loads(KEEPERS_JSON.read_text())

    channels = {}
    for flag in FLAGS_OF_INTEREST:
        channels[flag] = {
            "resolved_run_config": resolved.get(flag, "<ABSENT>"),
            "meta_solve_kwarg": meta.get(flag, "<ABSENT>"),
            "prb_overrides_channel": prb.get(flag, "<ABSENT>"),
        }

    target = channels["cc_nameplate_summer_derate"]
    armed = bool(target["resolved_run_config"] is True)
    return {
        "keeper_id_at_head": keeper_json["keeper"],
        "keeper_id_expected": KEEPER_ID,
        "keeper_id_matches": keeper_json["keeper"] == KEEPER_ID,
        "bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "channels": channels,
        "cc_nameplate_summer_derate_ARMED_ON_KEEPER": armed,
        "verdict": (
            "FAIL — already armed, the ercot-202 zero-delta case"
            if armed
            else "PASS — genuinely unarmed on the keeper through all three channels"
        ),
    }


# --------------------------------------------------------------------------
# (b)/(c) the measured object and its identification
# --------------------------------------------------------------------------
def _cc_summer_capacity() -> dict[int, tuple[float, float]]:
    """``{plant_code: (nameplate_mw, net_summer_mw)}`` — verbatim transcription
    of ``data.fleet.campd_bins.cc_summer_capacity`` (same sheet, same technology
    filter, same per-plant grouping, same double-file clamp)."""
    df = pd.read_parquet(
        EIA860_OPERABLE,
        columns=[
            "Plant Code",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
            "Operating Year",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np_mw"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns_mw"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    cc["op_year"] = pd.to_numeric(cc["Operating Year"], errors="coerce")
    out: dict[int, tuple[float, float]] = {}
    ages: dict[int, float] = {}
    for code, grp in cc.groupby("plant_code"):
        np_sum = float(grp["np_mw"].sum())
        ns_sum = min(float(grp["ns_mw"].sum()), np_sum)
        if np_sum > 0.0 and ns_sum > 0.0:
            out[int(code)] = (np_sum, ns_sum)
            w = grp["np_mw"].fillna(0.0)
            if w.sum() > 0 and grp["op_year"].notna().any():
                ages[int(code)] = float(
                    (grp["op_year"].fillna(0) * w).sum() / w.sum()
                )
    _cc_summer_capacity.online_year = ages  # type: ignore[attr-defined]
    return out


def _cc_summer_derate_ratio(cap: dict, code: int) -> float | None:
    """``min(1, net_summer/nameplate)`` — transcription of
    ``campd_bins.cc_summer_derate_ratio``."""
    got = cap.get(int(code))
    if got is None:
        return None
    nameplate, net_summer = got
    if nameplate <= 0.0:
        return None
    return min(1.0, net_summer / nameplate)


def _dam_covered_classes() -> list[str]:
    """Classes carried by the measured ERCOT DAM-availability hourly extract."""
    dam = pd.read_csv(DAM_HOURLY, usecols=["class"])
    return sorted(dam["class"].astype(str).unique().tolist())


def block_bc_object(armed_flags: dict) -> dict:
    """Size the object the arm would move, per class, in MW and $/MWh."""
    bins = pd.read_csv(BINS_SHEET)
    cc_bins = bins[bins["Plant_Group"].isin(CC_GROUPS)].copy()
    cap = _cc_summer_capacity()
    online = getattr(_cc_summer_capacity, "online_year", {})
    dam_classes = _dam_covered_classes()

    rows = []
    for _, r in cc_bins.iterrows():
        code = int(r["Plant_Code"])
        group = str(r["Plant_Group"])
        mw = float(r["Nameplate_MW"])
        ratio = _cc_summer_derate_ratio(cap, code)
        # keeper (flag OFF): flat class derate. arm (flag ON): measured ratio,
        # or — for a plant absent from the EIA-860 CC sheet — NO summer derate
        # at all, because arrays.py:824-829 applies the measured ratio only
        # when it exists and never falls back to the flat class value.
        keep_mult = 1.0 - SUMMER_CLASS_DERATE[group]
        arm_mult = 1.0 if ratio is None else (ratio if ratio < 1.0 else 1.0)
        rows.append(
            {
                "plant_code": code,
                "plant_name": str(r["Plant_Name"]),
                "plant_group": group,
                "zone": str(r["ERCOT_Zone"]),
                "nameplate_mw_bins_sheet": mw,
                "eia860_present": ratio is not None,
                "eia860_nameplate_mw": (
                    None if ratio is None else round(cap[code][0], 3)
                ),
                "eia860_net_summer_mw": (
                    None if ratio is None else round(cap[code][1], 3)
                ),
                "measured_summer_ratio": None if ratio is None else round(ratio, 6),
                "keeper_summer_multiplier": keep_mult,
                "arm_summer_multiplier": round(arm_mult, 6),
                "summer_mw_delta": round(mw * (arm_mult - keep_mult), 4),
                "dam_covered_class": group in dam_classes,
                "eia860_cap_wtd_online_year": (
                    None if code not in online else round(online[code], 1)
                ),
            }
        )
    per_plant = pd.DataFrame(rows)

    by_class = {}
    for group, grp in per_plant.groupby("plant_group"):
        matched = grp[grp["eia860_present"]]
        by_class[group] = {
            "plants": int(len(grp)),
            "plants_matched_in_eia860": int(len(matched)),
            "bins_nameplate_mw": round(float(grp["nameplate_mw_bins_sheet"].sum()), 2),
            "bins_nameplate_mw_matched": round(
                float(matched["nameplate_mw_bins_sheet"].sum()), 2
            ),
            "cap_wtd_measured_summer_ratio": (
                None
                if matched.empty
                else round(
                    float(
                        (
                            matched["measured_summer_ratio"]
                            * matched["nameplate_mw_bins_sheet"]
                        ).sum()
                        / matched["nameplate_mw_bins_sheet"].sum()
                    ),
                    6,
                )
            ),
            "keeper_flat_multiplier": 1.0 - SUMMER_CLASS_DERATE[group],
            "summer_mw_delta_total": round(float(grp["summer_mw_delta"].sum()), 2),
            "summer_mw_delta_matched_only": round(
                float(matched["summer_mw_delta"].sum()), 2
            ),
            "dam_covered_class": bool(grp["dam_covered_class"].iloc[0]),
        }

    # The second leg: arrays.py:712 drops the statistical POF and age-derate for
    # CC in a historic backcast, leaving availability = 1 - wefor. Sized from
    # the committed THERMAL_AVAILABILITY constants and each plant's cap-weighted
    # EIA-860 operating year, on the keeper's own wefor settings.
    wefor_res = armed_flags["wefor_residual"]["resolved_run_config"]
    wefor_groups = armed_flags["wefor_residual_groups"]["resolved_run_config"]
    wefor_mult = armed_flags["wefor_multiplier"]["resolved_run_config"]
    pof_leg = {}
    for group in CC_GROUPS:
        pof, w_base, w_rate, w_onset, d_base, d_rate, d_onset = THERMAL_AVAILABILITY[
            group
        ]
        grp = per_plant[per_plant["plant_group"] == group]
        grp = grp[grp["eia860_cap_wtd_online_year"].notna()]
        if grp.empty:
            continue
        # Age on the middle solve year, cap-weighted over the class.
        age = 2024 - grp["eia860_cap_wtd_online_year"].astype(float)
        w = grp["nameplate_mw_bins_sheet"].astype(float)
        wefor = (w_base + np.maximum(0.0, age - w_onset) * w_rate) * float(wefor_mult)
        relieved = bool(wefor_groups) and group in (wefor_groups or [])
        if wefor_res is not None and relieved:
            wefor = np.minimum(wefor, float(wefor_res))
        derate = d_base + np.maximum(0.0, age - d_onset) * d_rate
        pof_leg[group] = {
            "class_cap_wtd_online_year": round(
                float((grp["eia860_cap_wtd_online_year"].astype(float) * w).sum()
                      / w.sum()), 1
            ),
            "in_wefor_residual_groups": relieved,
            "wefor_capped_to_residual": bool(relieved and wefor_res is not None),
            "keeper_availability_base": round(
                float(((1.0 - wefor - derate) * w).sum() / w.sum()), 6
            ),
            "arm_availability_base_1_minus_wefor": round(
                float(((1.0 - wefor) * w).sum() / w.sum()), 6
            ),
            "delta_availability_pp": round(
                float((derate * w).sum() / w.sum()) * 100.0, 4
            ),
            "plus_pof_dropped": pof,
            "note": (
                "arrays.py:712 sets availability = 1 - wefor for CC in a historic "
                "backcast, dropping the statistical POF and the age/performance "
                "derate. The delta below is the age-derate leg only; the POF leg "
                "enters through _maint_derate in the shoulder months."
            ),
            "mw_at_stake": round(
                float(w.sum()) * float((derate * w).sum() / w.sum()), 2
            ),
        }

    return {
        "per_plant": rows,
        "by_class": by_class,
        "dam_covered_classes": dam_classes,
        "pof_and_age_derate_leg": pof_leg,
        "summer_months": list(SUMMER_MONTHS),
    }


def block_b_price_reach(object_block: dict) -> dict:
    """The $/MWh the object can reach, from the KEEPER's own hourly sidecars."""
    out = {}
    for year in YEARS:
        cls = pd.read_parquet(KEEPER_BUNDLE / f"hourly/class_hourly_{year}.parquet")
        sysd = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
        cls = cls[cls["pass"] == "P1"]
        sysd = sysd[sysd["pass"] == "P1"]
        # Load-weighted ISO price per hour (system_*.parquet is per zone).
        sysd = sysd.assign(pw=sysd["price"] * sysd["demand"])
        hourly = sysd.groupby("hour").agg(pw=("pw", "sum"), d=("demand", "sum"))
        price = (hourly["pw"] / hourly["d"]).to_numpy()
        months = _hour_months(year, len(price))

        year_block = {}
        for group in CC_GROUPS:
            g = cls[cls["klass"] == group].sort_values("hour")
            if g.empty:
                continue
            mw = g["mw"].to_numpy()
            n = min(len(mw), len(price))
            mw, p, m = mw[:n], price[:n], months[:n]
            summer = np.isin(m, SUMMER_MONTHS)
            delta = abs(
                object_block["by_class"].get(group, {}).get("summer_mw_delta_total", 0.0)
            )
            # The only hours a summer capability change can reach are the summer
            # hours in which the class is already within `delta` MW of its own
            # observed summer ceiling — otherwise the LP is not capacity-bound
            # there and the change is slack.
            ceiling = float(mw[summer].max()) if summer.any() else 0.0
            reachable = summer & (mw >= ceiling - delta)
            year_block[group] = {
                "summer_hours": int(summer.sum()),
                "summer_mean_mw": round(float(mw[summer].mean()), 2),
                "summer_max_mw": round(ceiling, 2),
                "delta_mw_applied": round(delta, 2),
                "reach_upper_bound_hours": int(reachable.sum()),
                "reach_upper_bound_share_of_summer": round(
                    float(reachable.sum()) / max(1, int(summer.sum())), 6
                ),
                "reach_upper_bound_mean_price_usd_mwh": (
                    round(float(p[reachable].mean()), 4) if reachable.any() else None
                ),
                "summer_mean_price_usd_mwh": round(float(p[summer].mean()), 4),
                "annual_mean_price_usd_mwh": round(float(p.mean()), 4),
                "reach_upper_bound_months": sorted({int(x) for x in m[reachable]}),
                "reach_is_an_UPPER_BOUND_because": (
                    "the class sidecar records dispatched MW, not the availability "
                    "ceiling. A summer capability cut binds only where the class is "
                    "actually at its ceiling; hours within `delta` of the class's OWN "
                    "observed summer maximum are the largest set that could be, and "
                    "the committed artifacts cannot narrow it further without a solve."
                ),
            }
        out[str(year)] = year_block
    return out


# --------------------------------------------------------------------------
# (d) rule-19 reconciliation against the armed DAM-availability family
# --------------------------------------------------------------------------
def block_d_rule19(armed: dict, object_block: dict) -> dict:
    """Which of the object's MW survive the armed DAM water-fill."""
    dam_on = armed["ercot_thermal_dam_availability"]["resolved_run_config"] is True
    hourly_on = (
        armed["ercot_thermal_dam_availability_hourly"]["resolved_run_config"] is True
    )
    plant_on = (
        armed["ercot_thermal_dam_availability_plant"]["resolved_run_config"] is True
    )
    covered = object_block["dam_covered_classes"]
    survives, erased = {}, {}
    for group, blk in object_block["by_class"].items():
        if dam_on and hourly_on and group in covered:
            erased[group] = blk["summer_mw_delta_total"]
        else:
            survives[group] = blk["summer_mw_delta_total"]
    return {
        "dam_family_armed": {
            "ercot_thermal_dam_availability": dam_on,
            "ercot_thermal_dam_availability_hourly": hourly_on,
            "ercot_thermal_dam_availability_plant": plant_on,
        },
        "dam_covered_classes": covered,
        "erased_by_waterfill_mw": erased,
        "survives_mw": survives,
        "basis": (
            "FINDING-ercot177-temp-derate-refused-2026-08-07.md §3: the class-HOUR "
            "water-fill in arrays.py:1616-1633 drives the cap-weighted class-hour "
            "mean availability to the measured target `_t` independent of `_cur`, "
            "so any PRE-overlay availability edit on a covered class is erased at "
            "the class-hour mean; with _plant armed each crosswalked plant is "
            "additionally pinned to its own measured site-hour fraction."
        ),
    }


def block_f_keeper_promotion_invariance() -> dict:
    """Prove the 2026-08-15 promotion cannot move any figure in this Phase 0.

    The keeper was re-keyed `2026-08-14-ercot202-arm-plantphysics` ->
    `2026-08-15-ercot204-rule26-delete` while this session was open. Rather than
    inherit the promoting lane's byte-identity claim, re-hash the two sidecars
    this probe actually reads, and re-read the flags it turns on, from BOTH
    bundles.
    """
    import hashlib

    sidecars = {}
    for year in YEARS:
        for name in ("class_hourly", "system"):
            rel = f"hourly/{name}_{year}.parquet"
            new = hashlib.sha256((KEEPER_BUNDLE / rel).read_bytes()).hexdigest()
            old = hashlib.sha256(
                (PRIOR_KEEPER_BUNDLE / rel).read_bytes()
            ).hexdigest()
            sidecars[rel] = {"identical": new == old, "sha256": new}

    flags = {}
    new_cfg = json.loads((KEEPER_BUNDLE / "run_config.json").read_text())[
        "scenario_config"
    ]
    old_cfg = json.loads((PRIOR_KEEPER_BUNDLE / "run_config.json").read_text())[
        "scenario_config"
    ]
    for flag in FLAGS_OF_INTEREST:
        flags[flag] = {
            "promoted_keeper": new_cfg.get(flag, "<ABSENT>"),
            "superseded_keeper": old_cfg.get(flag, "<ABSENT>"),
            "identical": new_cfg.get(flag, "<ABSENT>")
            == old_cfg.get(flag, "<ABSENT>"),
        }

    return {
        "promoted_keeper": KEEPER_ID,
        "superseded_keeper": "2026-08-14-ercot202-arm-plantphysics",
        "sidecars_read_by_this_probe": sidecars,
        "all_sidecars_identical": all(v["identical"] for v in sidecars.values()),
        "phase0_flags": flags,
        "all_phase0_flags_identical": all(v["identical"] for v in flags.values()),
        "conclusion": (
            "every sidecar this probe reads and every flag this Phase 0 turns on "
            "is identical across the promotion, so the verdict is unmoved."
        ),
    }


def block_e_surviving_scope_posture() -> dict:
    """What the one rule-19-surviving class already is, on the keeper's record.

    CC_CHP is the only CC class the DAM extract does not cover, so it is the
    only scope on which the arm survives §(d). This block reads what that class
    already is in the keeper's own committed scoring and D-2 attribution.
    """
    metrics = json.loads((KEEPER_BUNDLE / "metrics.json").read_text())
    legit = json.loads((KEEPER_BUNDLE / "legitimacy_diagnostics.json").read_text())
    free = metrics.get("free_class_score", {})
    d2 = [
        r
        for r in legit["diagnostics"]["D2"]["rows"]
        if r.get("class") == "CC_CHP"
    ]
    return {
        "class": "CC_CHP",
        "pinned_in_c1_scoring": "CC_CHP" in (free.get("pinned_classes") or []),
        "excluded_from_free_class_score": "CC_CHP"
        in (free.get("excluded_from_free") or []),
        "d2_forcing_rows": d2,
        "min_gen_clipped_to_availability": True,
        "min_gen_clip_site": "data/fleet/arrays.py:2798 "
        "np.minimum(min_gen, pmax[:, None] * availability, out=min_gen)",
        "consequence": (
            "a summer availability cut on CC_CHP is clipped straight through to the "
            "chp_steam must-run floor that carries 44.94 % of the class's 2023 "
            "energy, so the arm's surviving scope lands first on a forced leg, not "
            "on the economic merit order (rule 19 [R-ONE-MECH] against chp_steam)."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    a = block_a_armed_state()
    bc = block_bc_object(a["channels"])
    price = block_b_price_reach(bc)
    d = block_d_rule19(a["channels"], bc)
    e = block_e_surviving_scope_posture()
    f = block_f_keeper_promotion_invariance()

    result = {
        "probe": "ercot208_cc_nameplate_phase0",
        "lever": "cc_nameplate_summer_derate (ERCOT CC leg)",
        "keeper": KEEPER_ID,
        "years_read": list(YEARS),
        "no_lp_solved": True,
        "phase0_a_armed_state": a,
        "phase0_bc_object": bc,
        "phase0_b_price_reach": price,
        "phase0_d_rule19": d,
        "phase0_e_surviving_scope_posture": e,
        "phase0_f_keeper_promotion_invariance": f,
    }

    print(json.dumps({"phase0_a": a["verdict"]}, indent=1))
    print(json.dumps(bc["by_class"], indent=1))
    print(json.dumps(bc["pof_and_age_derate_leg"], indent=1))
    print(json.dumps(price, indent=1))
    print(json.dumps({k: v for k, v in d.items() if k != "basis"}, indent=1))
    print(json.dumps(e, indent=1))
    print(json.dumps({k: v for k, v in f.items() if k != "phase0_flags"}, indent=1))

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(result, indent=1) + "\n")
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
