"""Write the calibration attestation for the miso-126 CC steam-part capacity arm.

The arm is a ``replay_keeper`` re-solve of the ``2026-08-04-miso-124-dualfuel-rearm``
keeper's own ``meta.json`` at this session's HEAD with exactly one delta,
``cc_steam_part_capacity=true``. The governance posture, the standing
measured-input ledger entries and the DOF ledger are therefore the keeper's —
carried forward verbatim in *classification and reason*, with this run's **own**
measured magnitudes substituted from its own scored verdict so no number in the
attestation describes a different run (the miso-116 §7 basis discipline, applied
at miso-117 / 119 / 121 / 124 and again here).

It carries one new DOF entry, ``cc_steam_part_capacity``, which adds **zero free
parameters**: the predicate is a conjunction of equalities on published EIA-860
categorical fields plus one vintage inequality, with no coefficient, threshold or
percentile anywhere in it, and the restored generator takes the eGRID plant heat
rate its own block siblings already carry.

Run AFTER the bundle is registered and its legitimacy diagnostics are written,
and BEFORE the final ``calibration_verdict.py --write-metrics`` pass, since C6
reads the attestation and the ledger entries reclassify C3a / C3c.

Usage::

    uv run python scripts/gen_miso126_attestation.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent

KEEPER = REPO / "results/calibration/miso124_dualfuel_B"
BUNDLE = REPO / "results/calibration/miso126_steampart_B"
RUN_ID_ENV = REPO / "results/calibration/_miso126_run_id.txt"
AB_JSON = REPO / "results/calibration/_miso126_steam_part_ab.json"
SCREEN_JSON = REPO / "results/calibration/_miso126_cc_steam_part_screen.json"

_ATTEST = (
    "miso-126, 2026-08-04. This arm is a replay_keeper re-solve of the "
    "2026-08-04-miso-124-dualfuel-rearm keeper's own meta.json at this session's "
    "HEAD, --years 2023 2024 2025 in ONE invocation (rules 12 / 16), years "
    "sequential inside the invocation. EXACTLY ONE DELTA against that keeper, "
    "cc_steam_part_capacity=true, applied through replay_keeper --set and "
    "recorded in run_config.json (rule 26 [R-REGISTRY]); a programmatic diff of "
    "the two scenario blocks returns exactly one differing key, and it is scored "
    "against a SAME-HEAD ZERO-DELTA CONTROL (miso126_steampart_A), never against "
    "the committed keeper — miso-124's DO-NOT-MISREAD is that the price response "
    "is not stable across keepers. "
    "WHAT THE MECHANISM IS. EIA-860's Energy Source 1 on a CA prime-mover row "
    "names the combined-cycle block's SUPPLEMENTARY / DUCT fuel, not its primary "
    "energy input, which arrives as its own combustion turbines' exhaust. So a "
    "duct-fired steam part reports an exotic fuel code (BFG / OG / DFO), "
    "fleet.eia860._map_fuel_type returns None, the row is SKIPPED and its "
    "capacity never reaches the LP at all. This restores it as gas combined "
    "cycle at the eGRID plant heat rate its own block siblings already carry. "
    "It is a rule 14 [R-ACCURATE] capacity-representation repair and NOTHING "
    "ELSE — it was not chartered as a C7, C3a or C3c instrument, and no result "
    "here is quoted as progress on any of them. "
    "THE POPULATION IS VERIFIED, NOT SEARCHED. miso-125 §6 published the census "
    "and deliberately declined to charter it; this session pre-registered the "
    "repair before any adjudicating statistic and admitted exactly ONE machine "
    "in MISO — 55088 Dearborn ST1, 250.0 MW, prime mover CA, Unit Code SINT "
    "shared with the two NG CT turbines whose exhaust drives it, Energy Source 1 "
    "BFG, zone MISO-East. 50973 Motiva GN31/32/33 (40.4 MW) was EXCLUDED by the "
    "pre-registered P2 falsifier and independently by the predicate's own "
    "vintage clause, so the lever is 250.0 MW and not the 290.4 MW miso-125 "
    "named. 1004 Edwardsport matches the predicate but is UNTOUCHED: its "
    "technology string carries 'coal', so it already sits in the fleet as COAL "
    "555.0 MW and the repair only ever restores rows the fuel map DROPS. "
    "THE RATE IS NOT CHANGED, AND THAT IS THE POINT. eGRID's PLNGENAN at 55088 "
    "is 5,259,825 net MWh, which implies an IMPOSSIBLE 116.6 % capacity factor "
    "on the 515.0 MW the LP held and 78.5 % on the repaired 765.0 MW. The "
    "incumbent measured-CHP rate's denominator therefore ALREADY counted the "
    "missing machine — it was already a BLOCK rate applied to two thirds of the "
    "block. Re-deriving chp_power_only_heat_rates_MISO.csv on the repaired fleet "
    "(rule 23 [R-FROZEN-DERIVE], cited to the fleet/denominator change and never "
    "to a residual) moves exactly ONE cell, class_capacity_mw at (55088, CC_CHP) "
    "350.0 -> 600.0; heat_rate 6.9573, flag 'ok', basis_heat_rate, "
    "model_heat_rate, thermal_share and dark_fuel_share are byte-identical on "
    "every row of every plant, and a flag-off control re-derive reproduces the "
    "committed artifact byte-for-byte. Rule 19 [R-ONE-MECH]: the two defects "
    "share one cause and move in one change; nothing is stacked on the "
    "already-armed measured_chp_heat_rates, which keeps its single rate. "
    "Rule 25 [R-ISO-SCOPE]: ISO-gated on "
    "plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS = {MISO}. A same-flag fleet load "
    "returns BYTE-IDENTICAL generator lists for ERCOT, CAISO, PJM, NYISO and "
    "NEISO. CAISO 54912 Martinez STG1 (20.0 MW) and NEISO 6081 Stony Brook CA1 "
    "(96.0 MW) are reported and HANDED OFF UNSTAMPED; no parameter is imported "
    "from or exported to any other ISO. "
    "Rule 22 [R-HOLDOUT]: 2023-2025 only — MISO holds no calibration-complete "
    "marker, so no validation or locked-test year was solved, scored or read, "
    "and no D-5(b) re-key duty arises."
)


def _screen() -> dict:
    return json.loads(SCREEN_JSON.read_text()) if SCREEN_JSON.exists() else {}


def _ab() -> dict:
    return json.loads(AB_JSON.read_text()) if AB_JSON.exists() else {}


def _disclosures() -> str:
    """Disclosures, with THIS run's own measured magnitudes substituted in."""
    ab, sc = _ab(), _screen()
    dl = ab.get("max_zonal_abs_dlmp", {})
    k5 = ab.get("K5_direction_integrity", {})
    k6 = ab.get("K6_energy_conservation", {})
    k7 = ab.get("K7_no_gate_regression", {})
    k0 = ab.get("K0_control_integrity", {})

    def _fmt(d: dict, f: str = "{:.6f}") -> str:
        return " / ".join(f.format(d[y]) for y in sorted(d)) if d else "n/a"

    cc = k5.get("cc_chp_energy_delta_gwh", {})
    net = k6.get("net_class_energy_delta_gwh", {})
    dsys = k5.get("d_system_demand_weighted_lambda", {})
    p2 = (sc.get("P2_one_meter_one_rate") or {}).get("per_plant", {})
    p3 = (sc.get("P3_design_share") or {}).get("per_plant", {}).get("55088", {})
    ke3 = (sc.get("KE3_inert_by_dispatch") or {}).get("per_plant", {}).get("55088", {})

    parts = [
        "miso-126 disclosures, reported rather than patched. ",
        "(a) THE PRE-REGISTERED INERTNESS ROUTES WERE DECLARED AND DID NOT FIRE, "
        "AND THAT WAS SAID IN ADVANCE. The prereg stated plainly that KE3 "
        "(INERT-BY-DISPATCH) was 'expected not to fire' because, unlike "
        "miso-119 / 121 / 122 / 125, this lever ADDS NEW CAPACITY rather than "
        "re-pricing or re-allocating existing capacity, so it has no zero-sum "
        "identity to bound it. Measured: the restored block's marginal cost is "
        f"{_fmt({y: ke3[y]['marginal_cost'] for y in ke3}, '{:.2f}')} $/MWh "
        "against MISO-East median LMPs of "
        f"{_fmt({y: ke3[y]['median_price'] for y in ke3}, '{:.2f}')}, so it "
        "would dispatch in "
        f"{_fmt({y: ke3[y]['dispatch_hour_share'] for y in ke3}, '{:.1%}')} "
        "of hours against a pre-declared 5 % band. KE4 (INERT-BY-BINDING) is "
        "recorded as NOT ANSWERABLE from committed artifacts — the sidecar "
        "schema is (year, pass, klass, hour, mw) at CLASS grain with no bound "
        "flag, so 55088's own binding cannot be read from it, and no `I` was "
        "declared on a class-grain proxy (the same honesty miso-125 applied to "
        "its own KE4 clause (a)). ",
        "(b) THE LEVER IS SMALLER THAN miso-125 NAMED, BECAUSE A PRE-REGISTERED "
        "FALSIFIER FIRED. 50973 Motiva Port Arthur's three CA rows (40.4 MW) are "
        "genuinely absent from the fleet, but property P2's test is that eGRID's "
        "PLNGENAN must imply an IMPOSSIBLE capacity factor on the un-repaired "
        "fleet — the proof that the incumbent rate's denominator already counts "
        "the missing machine. At 50973 the present-fleet implied CF is "
        f"{(p2.get('50973') or {}).get('implied_cf_present', float('nan')):.1%}, "
        "so that evidence is ABSENT. It is stated precisely: absent, NOT "
        "contrary — eGRID is plant-grain, so its denominator very likely does "
        "cover those rows too; what is missing is the proof, and the "
        "pre-registration admits only what is proven. The predicate's vintage "
        "clause excludes 50973 independently and on different data: its CA rows "
        "commissioned 1957 / 1962 / 1978 against NG CT siblings of 1983 and "
        "2011, so three steam turbines predate by up to 26 years every turbine "
        "that supposedly drives them — a refinery steam header sharing a "
        "Unit Code label, not a combined-cycle block. Two independent sources "
        "reaching the same exclusion is why it is reported as settled. THE "
        "VINTAGE CLAUSE IS DECLARED UNREGISTERED: it was not in the "
        "pre-registration, it was added as an IMPLEMENTATION device so the "
        "shipped predicate's population equals the properties' admitted set "
        "without a per-plant list (rule 24 [R-REGISTRY]), it changes no verdict, "
        "and it is strictly NARROWING. Its one known limitation is stated in the "
        "code: a REPOWERED block (an existing steam turbine fitted with new gas "
        "turbines) is also excluded. That direction is safe — the model drops "
        "100 % of these rows today, so the clause can only restore fewer, never "
        "more — and it is named as the successor question rather than buried. ",
        "(c) miso-125's OWN OPEN DOUBT IS CLOSED BY MEASUREMENT, NOT BY "
        "ASSUMPTION. miso-125 §4 could not exclude the hypothesis that ST1 is a "
        "LET-DOWN TURBINE on the plant's three dark boilers (7.3 M MMBtu, "
        "dark_fuel_share 0.166) rather than an HRSG on the CT exhaust — and if "
        "it were, the block-rate claim would fail, because the dark-fuel gate "
        "removes those boilers' fuel while the steam turbine's generation stays "
        "in PLNGENAN. Property P3 made that falsifiable BEFORE measurement, "
        "against the manufacturer's own design split rather than an invented "
        "band: ST1's implied generation share of its block measures "
        f"{p3.get('implied_gen_share', float('nan')):.4f} against its EIA-860 "
        f"NAMEPLATE share of {p3.get('nameplate_share', float('nan')):.4f}, a "
        f"gap of {p3.get('gap', float('nan')):.4f} against a pre-declared 0.10 "
        "band. The implied share is on a gross/net mixed basis and is therefore "
        "a LOWER bound, which makes the falsifier conservative — a gross-basis "
        "correction could only move it UP, toward the falsifier. ",
        "(d) CLASS ENERGY IS THE MAGNITUDE, NOT THE MAX CLASS-HOUR (miso-122's "
        f"DO-NOT-MISREAD). CC_CHP energy rises {_fmt(cc, '{:+.3f}')} GWh in "
        "2023 / 2024 / 2025. Full signed per-class energy deltas are committed "
        "in _miso126_steam_part_ab.json K4; the summed class-energy delta is "
        f"{_fmt(net, '{:+.4f}')} GWh, i.e. ~0 as demand conservation requires — "
        "whatever the restored block generates displaces something, and a "
        "non-zero net would be an accounting leak rather than a result. ",
        "(e) DIRECTION IS CHECKED, NOT ASSUMED. Adding deep-inframarginal "
        "capacity can only lower or leave unchanged the clearing price, so the "
        "system demand-weighted lambda must never rise; measured "
        f"{_fmt(dsys)} $/MWh. Max zonal |dLMP| is {_fmt(dl)} $/MWh. No price "
        "magnitude is carried in from any prior MISO session (miso-124's "
        "DO-NOT-MISREAD), and no liveness claim rests on an offer-delta "
        "percentile (miso-119 / 121's). ",
        "(f) THE CONTROL IS MEASURED, NOT ASSUMED. Arm A is a same-HEAD "
        "zero-delta replay of the incumbent keeper; caiso-146 found exactly such "
        "a control diverging by GW on a class-hour, so K0 checks the scorecard "
        "AND the committed sidecars. Result: "
        f"scorecard_identical={k0.get('scorecard_identical')}, max class-hour "
        "delta vs the incumbent bundle "
        f"{_fmt(k0.get('max_abs_class_hour_mw_vs_incumbent', {}), '{:.4f}')} MW. ",
        "(g) NOTHING IS CLAIMED FOR ANY CRITERION, IN EITHER DIRECTION. "
        f"Determination {k7.get('determination')}; criterion statuses changed: "
        f"{k7.get('criteria_changed') or 'none'}; legitimacy-diagnostic verdict "
        f"changes: {len(k7.get('diagnostic_verdict_changes') or {})} of "
        f"{k7.get('n_diagnostic_rows_compared')} rows. Per the pre-registration, "
        "a regression here would be REPORTED and would NOT be grounds to revert "
        "the capacity repair (rules 1 [R-STRUCT] / 14 [R-ACCURATE]: a worse fit "
        "from a more accurate input is a discovered root-cause item, never a "
        "reason to bury the error back inside an inaccurate input), and an "
        "improvement is equally not the ship criterion — accuracy is. C7 "
        "COAL_PRB is untouched and was never offered as a target; its residual "
        "stays routed to the data-blocked miso-78/79 congestion + sub-hourly-RT "
        "lane, and the contract-tonnage route stays refused (miso-103 / 104) "
        "pending the Form 580 count, which is a DATA ASK and not a solve.",
    ]
    return "".join(parts)


def _run_id() -> str:
    if RUN_ID_ENV.exists():
        return RUN_ID_ENV.read_text().strip()
    raise SystemExit(
        f"{RUN_ID_ENV.relative_to(REPO)} is missing — write the registered run "
        "id there (dashboard_add_run.py prints it) before generating the "
        "attestation"
    )


def _verdict(run_id: str) -> dict:
    """Score a registered run and return its JSON verdict."""
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/calibration_verdict.py"),
            "--run-id",
            run_id,
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    if out.returncode not in (0, 1) or not out.stdout.strip():
        raise SystemExit(
            f"calibration_verdict failed for {run_id}: {out.stderr[-800:]}"
        )
    return json.loads(out.stdout)


def _magnitudes(verdict: dict) -> dict[tuple[str, int], str]:
    """(criterion, year) -> this run's OWN measured magnitude string."""
    out: dict[tuple[str, int], str] = {}
    for name, crit in verdict["criteria"].items():
        for rec in crit.get("records", []):
            year = rec.get("year")
            if year is None or rec.get("key") == "da_diagnostic":
                continue
            mag = rec.get("magnitude") or rec.get("detail")
            if mag:
                out[(name, int(year))] = str(mag)
    return out


def _dof_entry() -> dict:
    """The ``cc_steam_part_capacity`` DOF entry.

    Zero free parameters: the predicate is a conjunction of equalities on
    published EIA-860 categorical fields plus one vintage inequality — no
    coefficient, no threshold, no percentile — and the restored generator takes
    the eGRID plant heat rate its own block siblings already carry, so the
    mechanism introduces no new numeric value of any kind.
    """
    ab = _ab()
    dl = ab.get("max_zonal_abs_dlmp", {})
    measured = ""
    if dl:
        measured = (
            "Measured effect on THIS keeper, against a same-HEAD zero-delta "
            "control: max zonal |dLMP| "
            + " / ".join(f"{dl[y]:.6f}" for y in sorted(dl))
            + " $/MWh. "
        )
    return {
        "name": "cc_steam_part_capacity",
        "identification": "measured",
        "classification": (
            "published EIA-860 generator roster, zero free parameters "
            "(rule 14 [R-ACCURATE] capacity-representation repair)"
        ),
        "value": True,
        "free_parameters_added": 0,
        "source": (
            "EIA-860 operable generator sheet "
            "(data/raw/eia-860/eia860_generator_operable.parquet): Prime Mover, "
            "Energy Source 1, Unit Code, Operating Year, Summer/Nameplate "
            "Capacity. Predicate: data.fleet.eia860.cc_steam_part_generators. "
            "ISO gate: config.plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS. Heat "
            "rate: the eGRID plant rate already joined onto the block's CT "
            f"siblings (6.9573 MMBtu/MWh at 55088 under measured_chp_heat_rates). {measured}"
            "The Phase-0 identification record — the census, the fleet-presence "
            "cross-check against each plant's EIA-860 TOTALS, and the five "
            "pre-registered properties — is committed in "
            "results/calibration/_miso126_cc_steam_part_screen.json and "
            "scripts/probes/_miso126_cc_steam_part_screen.py."
        ),
        "why_zero": (
            "Nothing is chosen, tuned or swept. Every clause of the predicate is "
            "an equality on a published categorical field (Prime Mover == 'CA', "
            "Energy Source 1 != 'NG', non-empty Unit Code, a sibling with "
            "Prime Mover == 'CT' and Energy Source 1 == 'NG') plus one physical "
            "inequality (the steam part is not older than the oldest such "
            "sibling — an HRSG is commissioned with or after the turbines whose "
            "exhaust drives it). The restored capacity is the published Summer "
            "Capacity and the heat rate is the block's existing one, so the "
            "mechanism introduces no new numeric value at all. Rule 13 "
            "[R-MEASURED]: a generator's existence, prime mover, unit code, "
            "vintage and capacity are INPUTS that regenerate for any forward "
            "year and respond to changed conditions (a retirement or re-rate "
            "moves them) — not a measured outcome fed back to close a residual. "
            "Rule 23 [R-FROZEN-DERIVE]: the paired CHP artifact re-derive cites "
            "the fleet/denominator change and moves ONE descriptive cell "
            "(class_capacity_mw 350.0 -> 600.0), leaving every applied rate "
            "byte-identical. Rule 19 [R-ONE-MECH]: nothing is stacked on the "
            "already-armed measured_chp_heat_rates, which keeps its single "
            "plant-grain rate — this changes the capacity that rate applies to, "
            "not the rate. n_residual is unchanged."
        ),
    }


def build() -> Path:
    """Write the arm's attestation; return its path."""
    base = json.loads((KEEPER / "calibration_attestation.json").read_text())
    mags = _magnitudes(_verdict(_run_id()))

    att = {
        "schema": base["schema"],
        "free_parameters": base["free_parameters"],
        "governance": {
            **{
                k: base["governance"][k]
                for k in (
                    "levers_trace_to_measured_input",
                    "no_fit_to_price_residuals",
                    "no_pinning_to_actuals",
                    "outage_filter_exogenous_net_load",
                )
            },
            "attested_by": _ATTEST,
        },
        "disclosures": {"note": _disclosures()},
        "exceptions": [],
    }
    for exc in base["exceptions"]:
        new = dict(exc)
        key = (str(exc.get("criterion")), int(exc.get("year")))
        if key in mags:
            new["magnitude"] = mags[key]
            new["magnitude_basis"] = (
                "this run's own scored value (miso-126); the classification and "
                "reason are the standing MISO adjudication carried forward"
            )
        att["exceptions"].append(new)

    path = BUNDLE / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1) + "\n")
    return path


def main() -> int:
    """Write the attestation, re-seed the DOF ledger, re-attach the entries."""
    path = build()
    print(f"wrote {path.relative_to(REPO)}")
    out = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts/build_dof_ledger.py"),
            str(BUNDLE),
            "--iso",
            "MISO",
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    print(f"  build_dof_ledger rc={out.returncode} {out.stdout.strip()[-300:]}")
    if out.returncode != 0:
        print(f"  stderr: {out.stderr[-500:]}")
    # build_dof_ledger replaces the whole section, so re-attach the entries it
    # cannot know: the keeper's carried-forward dual_fuel_switching entry and
    # this session's own cc_steam_part_capacity entry.
    att = json.loads(path.read_text())
    carried = [
        e
        for e in json.loads((KEEPER / "calibration_attestation.json").read_text())[
            "free_parameters"
        ].get("entries", [])
        if e.get("name") == "dual_fuel_switching"
    ]
    new = _dof_entry()
    keep_names = {new["name"]} | {e["name"] for e in carried}
    entries = [
        e
        for e in att["free_parameters"].get("entries", [])
        if e.get("name") not in keep_names
    ]
    entries.extend(carried)
    entries.append(new)
    att["free_parameters"]["entries"] = entries
    att["free_parameters"]["n_entries"] = len(entries)
    att["free_parameters"]["n_residual"] = sum(
        1 for e in entries if e.get("identification") == "residual"
    )
    path.write_text(json.dumps(att, indent=1) + "\n")
    print(
        f"  re-attached {len(carried)} carried + 1 new DOF entry "
        f"({len(entries)} total, n_residual "
        f"{att['free_parameters']['n_residual']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
