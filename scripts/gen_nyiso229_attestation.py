#!/usr/bin/env python3
"""Generate the nyiso-229 keeper attestation (rule 20 `[R-DOF]`, C6 governance).

The arm is the `2026-09-09-nyiso-221-fuelvintage-span` keeper recipe with ONE
registered field moved — `unit_outage_window_hour_grain` False -> True. It adds
**zero** free parameters, so the keeper's DOF ledger is carried **verbatim** and
`authorized_price_tuning` stays NONE.

Every governance claim that can be checked against the committed artifacts IS
checked here and written into `governance.computed_checks`; the script ABORTS on a
failed premise rather than emitting an attestation that asserts something false.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

CAL = Path("results/calibration")
ARM = CAL / "nyiso229_hourgrain_span"
KEEPER = CAL / "nyiso_fuelvintage_A"
YEARS = (2023, 2024, 2025)
HOUR_SHA = "ee778a87d3739341a7c578078b5e0194545f9231efbef2cd32d72e88e0aa21fa"
DAY_SHA = "58799099037ce48f1cb8014233b365b7199b5fc1384a34dc8435ff073af784ec"
#: Fields that legitimately differ per solve YEAR and are therefore not a
#: per-year RECIPE (rule 1 condition (b)): the year's own measured gas price and
#: its weather year. The committed keeper's own run_config records the FIRST
#: year's values for both, so this bundle follows the keeper's convention.
PER_YEAR_RESOLVED = {"gas_price_override", "weather_year"}


def _p1(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return df[df["pass"] == "P1"] if "pass" in df.columns else df


def main() -> None:
    checks: dict[str, object] = {}

    arm_cfg = json.loads((ARM / "run_config.json").read_text())
    keep_cfg = json.loads((KEEPER / "run_config.json").read_text())
    a_sc, k_sc = arm_cfg["scenario_config"], keep_cfg["scenario_config"]

    # (1) EXACTLY ONE registered field moves.
    from market_sim.config.scenarios import ScenarioConfig

    live = ScenarioConfig()
    differing = sorted(
        k
        for k in set(a_sc) | set(k_sc)
        if json.dumps(a_sc.get(k), sort_keys=True, default=str)
        != json.dumps(k_sc.get(k), sort_keys=True, default=str)
        and k not in PER_YEAR_RESOLVED
    )
    # SCHEMA DRIFT, not a recipe change: a field OTHER lanes added to
    # ScenarioConfig after this keeper solved is absent from the keeper's
    # run_config and, in this arm, sits at exactly the LIVE DEFAULT — i.e. it is
    # present but unarmed. Classified by measurement (absent AND == default), not
    # by an allowlist, so an actually-armed new field would still fail the gate.
    schema_drift = [
        k
        for k in differing
        if k not in k_sc and a_sc.get(k) == getattr(live, k, object())
    ]
    moved = [k for k in differing if k not in schema_drift]
    assert moved == ["unit_outage_window_hour_grain"], f"G-DELTA: {moved}"
    assert a_sc["unit_outage_window_hour_grain"] is True
    checks["single_field_delta"] = {
        "fields_moved": moved,
        "from": k_sc.get("unit_outage_window_hour_grain"),
        "to": a_sc["unit_outage_window_hour_grain"],
        "per_year_resolved_excluded": sorted(PER_YEAR_RESOLVED),
        "schema_drift_absent_in_keeper_and_at_live_default": {
            k: a_sc[k] for k in sorted(schema_drift)
        },
        "schema_drift_note": (
            "Fields other lanes added to ScenarioConfig after this keeper solved. Each is ABSENT "
            "from the keeper's run_config and sits at EXACTLY the live dataclass default in this "
            "arm, i.e. present but UNARMED. Classified by measurement rather than by an allowlist, "
            "so a new field that was actually armed would still fail the single-delta gate. Two are "
            "NYISO-scoped (nyiso_hub_gap_month_level, nyiso_total_east_cutset_ttc) and both read "
            "False — the cells nyiso-223 and nyiso-225 adjudicated shut."
        ),
    }

    # (2) The arm read the HOUR-grain extract; the keeper read the DAY-grain one.
    a_uo = arm_cfg["resolved_inputs"]["campd_unit_outages"]
    k_uo = keep_cfg["resolved_inputs"]["campd_unit_outages"]
    assert a_uo["sha256"] == HOUR_SHA, a_uo["sha256"]
    assert k_uo["sha256"] == DAY_SHA, k_uo["sha256"]
    checks["resolved_outage_extract"] = {
        "arm": {"path": a_uo["path"], "sha256": a_uo["sha256"]},
        "keeper": {"path": k_uo["path"], "sha256": k_uo["sha256"]},
    }

    # (3) No pinning to actuals: served demand is IDENTICAL to the keeper's in
    #     every year, and no firm load is shed and nothing dumped.
    served = {}
    for y in YEARS:
        a = _p1(ARM / "hourly" / f"system_{y}.parquet")
        k = _p1(KEEPER / "hourly" / f"system_{y}.parquet")
        ag = a.groupby("hour").agg(
            d=("demand", "sum"), s=("slack", "sum"), u=("dump", "sum")
        )
        kg = k.groupby("hour").agg(d=("demand", "sum"))
        at, kt = float(ag.d.sum() / 1e6), float(kg.d.sum() / 1e6)
        assert round(at, 4) == round(kt, 4), f"{y}: served {at} vs {kt}"
        assert float(ag.s.sum()) <= 1e-6 and float(ag.u.sum()) <= 1e-6, y
        served[str(y)] = {
            "served_twh_arm": round(at, 4),
            "served_twh_keeper": round(kt, 4),
            "slack_mwh": round(float(ag.s.sum()), 6),
            "dump_mwh": round(float(ag.u.sum()), 6),
        }
    checks["served_demand_identical_and_no_slack"] = served

    # (4) Zero new free parameters: the ledger is the keeper's, byte-for-byte.
    keep_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    ledger = keep_att["free_parameters"]
    checks["dof_ledger_carried_verbatim"] = {
        "source": "results/calibration/nyiso_fuelvintage_A/calibration_attestation.json",
        "n_entries": ledger["n_entries"],
        "n_residual": ledger["n_residual"],
        "new_entries_added_by_this_run": 0,
    }

    att = {
        "schema": "calibration-attestation/v1",
        "governance": {
            "levers_trace_to_measured_input": True,
            "no_fit_to_price_residuals": True,
            "no_pinning_to_actuals": True,
            "outage_filter_exogenous_net_load": True,
            "attested_by": (
                "session nyiso-229 (2026-09-12). PROMOTION UNDER THE OWNER RULING of 2026-09-12 "
                "(verbatim: \"if it's structurally sound let's promote\"). Pre-registration: "
                "results/calibration/PRECOMMIT-nyiso229-outage-window-hour-grain.md, pushed before "
                "any LP, plus three addenda pushed before the arm returned "
                "(docs/ADDENDUM-nyiso229-gdrift-and-the-control-is-solved-in-shard-2026-09-12.md, "
                "-presolve-the-threading-reaches-the-lp-, -the-first-shard-was-OOM-killed-). "
                "Phase 0: docs/FINDING-nyiso229-phase0-the-outage-window-grain-2026-09-12.md. "
                "Screen result: docs/RESULT-nyiso229-the-2022-screen-2026-09-12.md. "
                "ONE registered field moves, unit_outage_window_hour_grain False -> True: the CAMPD "
                "unit-outage window is read at its DETECTED HOUR grain instead of re-expanded to "
                "outage_start 00:00 -> outage_end 23:00. The detector has ALWAYS worked in hours "
                "(start = clock[s], last = clock[e-1]) while the extract stored DATES, so the loader "
                "asserted up to 23 h at EACH EDGE the detector never detected -- exactly where the "
                "event-based contract guarantees the neighbouring hour was RUNNING. That is the "
                "caiso-181 seam; caiso-183 built the optional column carriage and CAISO's own extract "
                "already carries it, NYISO's did not. RULE 14 [R-ACCURATE] is the basis, not the "
                "residual: the same measured input at its own resolution, with the day-grain version "
                "a rounding of it. ZERO free parameters (rule 21) -- no parameter, threshold or "
                "detector constant is involved, and the deriver carries two in-process "
                "stop-the-line assertions proving the grain change cannot MOVE a detected window, "
                "only narrow it (each reconstructed window is a strict SUBSET of its day-granular "
                "parent, and the base-column projection is byte-identical to the flag-absent frame). "
                "Measured on NYISO's own CAMPD, zero LP: the day-grain reconstruction asserts "
                "9,872 / 10,167 / 8,529 / 8,144 unit-hours unavailable in 2022/2023/2024/2025 while "
                "the meter shows grossLoad > 0, carrying 1,376.9 / 1,332.5 / 1,075.9 / 952.7 GWh; "
                "~95 % of those hours lie within 23 h of a window boundary and carry ~99.9 % of the "
                "energy, so the defect is the SCHEMA's rounding and NOT the detector's placement. It "
                "also takes 293 same-unit 24.0 h boundary-day window overlaps to ZERO (the same "
                "single-bin fingerprint MISO measured over 845 pairs for unit_outage_per_unit_clip, "
                "which is deliberately NOT co-armed -- rule 19 [R-ONE-MECH]: this gate removes the "
                "artifact the clip caps). Composed in the parent from three per-year shard legs "
                "(rule 32 [R-SHARD] (b) shards per year, (d) the parent owns the seam); each leg "
                "replayed the keeper's own meta.json through replay_keeper --set, so the recipe is "
                "literally the keeper's object. G-CTRL: rule 29(b) form 4 against the committed "
                "keeper, validated EMPIRICALLY -- a day-grain control leg solved in the same "
                "container class reproduced the committed 2022 touchpoint IDENTICALLY on slack "
                "(360.472 MWh), served demand (152.6817 TWh), annual max ($1,429.99) and the h>$300 "
                "count (8), differing only +0.0355 $/MWh on the mean, which is the single LIVE hunk "
                "the G-DRIFT audit named (reliability_floor_coeffs_NYISO.csv, nyiso-227's re-basing) "
                "in the range nyiso-228 measured for it on the other three years. "
                "REPORTED AT FULL MAGNITUDE AND NOT ABSORBED: C3a-2025 and the 2022 touchpoint both "
                "DEGRADE (prices fall and both years already undershoot), C3b-2025 moves 0.160 -> "
                "0.169 against a 0.20 band, and the 2022 C3c tail goes 8 -> 4 h above $300 with "
                "precision STILL 0.000 -- all four hours on 31 May, the wrong day -- so the arm "
                "removes most of a spurious VOLL event and creates NONE of the market's 101 real "
                "tail hours. It does NOT touch the winter object (Jan/Feb/Dec, 77 % of the 2022 "
                "miss). Against that: C3a improves in 2023 and 2024, C3b IMPROVES in 2024 (0.179 -> "
                "0.174, the tightest-margin year of the three), reserve shortfall falls in ALL four "
                "years (-71 / -59 / -55 / -21 %), served demand is identical to 4 dp in every year "
                "and dump is zero everywhere."
            ),
            "note": (
                "authorized_price_tuning is NONE for this run: the rules 1/13 authorized "
                "price-tuning channel (the offer_curve_by_group band multipliers) is NOT used and "
                "not touched. The keeper's bands are carried forward unchanged."
            ),
            "computed_checks": checks,
        },
        "authorized_price_tuning": None,
        "free_parameters": ledger,
        "exceptions": [],
        "exceptions_note": keep_att.get("exceptions_note", ""),
    }
    (ARM / "calibration_attestation.json").write_text(json.dumps(att, indent=1) + "\n")
    print("wrote", ARM / "calibration_attestation.json")
    for k, v in checks.items():
        print(f"  CHECK OK  {k}")


if __name__ == "__main__":
    main()
