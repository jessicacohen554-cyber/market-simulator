"""Emit the NWPP-42 calibration attestation for ``results/calibration/nwpp42_coalhr_span``.

NWPP-42 is NWPP-41's frozen recipe plus **exactly one** solve-affecting change:
``measured_coal_heat_rates=True``. Everything else — the five whole-BA zones, the
WECC-catalogue TTC tiers, served measured EIA-930 interchange, the 0.144 PRM
scalar, legacy heat-rate bins, ``coal_prb_proxy_own_iso``,
``--hydro-backfill-year 2024`` and ``--hydro-cascade-coupling`` — is NWPP-41's,
unchanged. Verified mechanically rather than asserted: the composer
``scripts/probes/_nwpp42_compose_span.py`` refuses any leg whose
``scenario_config`` differs from its siblings outside the two year-carried
fields, and ``_check_recipe`` below re-checks the arm and the inherited recipe
against the composite's own ``run_config.json``.

**What the lane fixed, and why it is not tuning (rules 1 / 13 / 14).** NWPP's one
remaining rubric failure is C4 coal, and the diagnosis routed to this lane by
NWPP-41 was a merit-order defect rather than a shape defect: model coal falls
from 39.61 TWh (2023) to 27.01 / 27.21 (2024 / 2025) against a measured
42.27 / 38.30 / 42.26, because model gas-CC marginal cost collapses across the
span while model coal marginal cost stays flat. Fuel prices were measured and
inside EIA's published state ranges, so they were not the defect. The **coal
heat rate** was: the legacy-bin fleet path takes eGRID's ANNUAL PLANT AVERAGE
(``PLHTIAN / PLNGENAN``), which is above the plant's own metered operating rate
at **every one of the 12 covered plants**, cap-weighted 11.868 against a
measured 11.066 MMBtu/MWh (−6.8 %). The arm replaces that estimate with the
plant's own CAMPD-metered steady-state rate — rule 14 ``[R-ACCURATE]``, not the
residual.

**Rule 36 ``[R-YEAR-ISOLATION]`` landed mid-lane** (owner ruling 2026-09-19,
miso-262), so this run is three single-year shards composed by the parent, and
the lane also solved a **paired control** — NWPP-41's own recipe re-solved under
year isolation — because the incumbent keeper was solved with the cross-year
warm start now defaulted off. The control is what the arm is differenced
against; the control-minus-keeper difference is NWPP's own measurement of the
artifact rule 36(f) records as unmeasured outside MISO, and it is disclosed
below.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from scripts.build_dof_ledger import update_attestation  # noqa: E402
from scripts.gen_nwpp41_attestation import (  # noqa: E402
    _BANDS,
    _INHERITED_DISCLOSURES,
    _INHERITED_SWITCHES,
    _UNIT_BAND_CLASSES,
    _dispatched_classes,
)

DEFAULT_BUNDLE = REPO / "results/calibration/nwpp42_coalhr_span"

#: The derived measured-heat-rate table this arm reads, pinned by content hash so
#: a silently-regenerated file cannot ride this attestation.
_HR_TABLE = "data/raw/_processed-legacy/campd_coal_heat_rates_NWPP.csv"
_HR_TABLE_MD5 = "8dd65f9e73352bcd73ef4f4ea11f35fd"

#: NWPP-41's own arm, which NWPP-42 inherits. Reproduced from the NWPP-41
#: generator's ``build()`` (it is assembled there rather than in the module-level
#: map, so it cannot be imported); the text is NWPP-41's, unchanged.
_NWPP41_ARM = {
    "value": True,
    "where": (
        "ScenarioConfig.coal_prb_proxy_own_iso, armed for NWPP alone at "
        "pipeline/backcast_config.py"
    ),
    "identification": "measured-physical",
    "source": (
        "EIA-923 Schedule-2 delivered PRB prices filed by NWPP's OWN reporters — Dave "
        "Johnston, Naughton, Wyodak and Jim Bridger — read through data.coal."
        "coal_supply_by_iso over data/raw/_processed-legacy/coal_supply_NWPP.csv. "
        "Inherited unchanged from NWPP-41; see that lane's attestation for the full entry."
    ),
    "why_not_a_free_parameter": (
        "Rule 21 [R-DOF]: a boolean that swaps one measured input for a better-aligned "
        "measured input is not a tuned value. Inherited from NWPP-41, unchanged."
    ),
}


def _check_recipe(bundle: Path) -> dict:
    """Refuse a bundle whose recipe contradicts this attestation's claims."""
    rc = json.loads((bundle / "run_config.json").read_text())
    sc = rc.get("scenario_config", {})
    meta = json.loads((bundle / "meta.json").read_text())
    problems: list[str] = []
    if sc.get("iso") != "NWPP" and meta.get("iso") != "NWPP":
        problems.append(f"iso is {sc.get('iso')!r} / {meta.get('iso')!r}, not NWPP")
    if sc.get("mode") != "backcast":
        problems.append(f"mode is {sc.get('mode')!r}, not backcast")
    # This lane's one arm.
    if sc.get("measured_coal_heat_rates") is not True:
        problems.append(
            "measured_coal_heat_rates is not true — this is NOT the NWPP-42 arm"
        )
    # NWPP-41's recipe, which this run inherits unchanged.
    if sc.get("coal_prb_proxy_own_iso") is not True:
        problems.append("coal_prb_proxy_own_iso is not true (NWPP-41's arm is missing)")
    if sc.get("hydro_cascade_coupling") is not True:
        problems.append("hydro_cascade_coupling is not true")
    if meta.get("hydro_backfill_year") != 2024:
        problems.append(f"hydro_backfill_year is {meta.get('hydro_backfill_year')!r}")
    if meta.get("hydro_eia930_monthly"):
        problems.append("hydro_eia930_monthly is armed (REFUSED, card R-f)")
    # Rule 36: this bundle must be composed from ONE shard per year.
    composed = meta.get("composed_from") or {}
    if not composed:
        problems.append(
            "meta.composed_from is absent — not a rule-36 per-year composite"
        )
    for name, years in composed.items():
        if len(years) != 1:
            problems.append(
                f"leg {name} carries {years}; rule 36 allows one year per leg"
            )
    # Gate G5's band check (rule 1's authorized channel is declared NONE below).
    groups = sc.get("offer_curve_by_group") or {}
    for cls in _UNIT_BAND_CLASSES:
        bands = groups.get(cls)
        if bands is None:
            continue
        for b in _BANDS:
            if float(bands.get(b, 1.0)) != 1.0:
                problems.append(f"offer band {cls}.{b} = {bands.get(b)} != 1.0")
        for k in bands:
            if str(k).startswith("phys_"):
                problems.append(f"phys_* field present on {cls}: {k}")
    # The arm's input table, pinned by content.
    import hashlib

    table = REPO / _HR_TABLE
    if not table.is_file():
        problems.append(f"{_HR_TABLE} is absent — the arm has no input")
    else:
        got = hashlib.md5(table.read_bytes()).hexdigest()  # noqa: S324 - identity, not security
        if got != _HR_TABLE_MD5:
            problems.append(f"{_HR_TABLE} md5 {got} != attested {_HR_TABLE_MD5}")
    if problems:
        raise SystemExit(
            "gen_nwpp42_attestation refuses this bundle:\n  " + "\n  ".join(problems)
        )
    return {"scenario_config": sc, "meta": meta}


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the NWPP-42 attestation (after seeding the canonical DOF ledger)."""
    rec = _check_recipe(bundle)
    sc, meta = rec["scenario_config"], rec["meta"]

    # Gate G5, measured rather than asserted.
    dispatched = _dispatched_classes(bundle)
    groups = sc.get("offer_curve_by_group") or {}
    live_nonunity = sorted(
        g
        for g, b in groups.items()
        if isinstance(b, dict)
        and g in dispatched
        and any(float(b.get(k, 1.0)) != 1.0 for k in _BANDS)
    )
    if live_nonunity:
        raise SystemExit(
            "gen_nwpp42_attestation refuses this bundle: non-unity bands on classes "
            f"NWPP actually dispatches: {live_nonunity}"
        )

    update_attestation(bundle, "NWPP")
    att = json.loads((bundle / "calibration_attestation.json").read_text())
    att["schema"] = "calibration-attestation/v1"

    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")

    fp = att["free_parameters"]
    residual_names = [
        e["name"] for e in fp["entries"] if e.get("identification") == "residual"
    ]

    switches = dict(_INHERITED_SWITCHES)
    switches["coal_prb_proxy_own_iso"] = dict(_NWPP41_ARM)
    switches["measured_coal_heat_rates"] = {
        "value": True,
        "where": (
            "ScenarioConfig.measured_coal_heat_rates via "
            "run_calibration_full.py --measured-coal-heat-rates; resolved in "
            "data/fleet/campd_bins.measured_coal_heat_rates(iso) and applied in "
            'data/fleet/eia860._rows_to_generators under a `group == "COAL"` gate'
        ),
        "identification": "measured-physical",
        "source": (
            f"{_HR_TABLE} (md5 {_HR_TABLE_MD5}; 12 plants, 7,956.4 of 8,104.4 MW = 98.2 % "
            "of NWPP COAL capacity), derived by scripts/data/derive_campd_coal_heat_rates.py "
            "from EPA CAMPD unit-level hourly opTime / grossLoad / heatInput "
            "(data/raw/campd-unit-level, 2023-2024-2025). Per unit: "
            "heat_rate = sum(heatInput) / sum(grossLoad) over hours with opTime >= 0.99 "
            "whose OWN implied rate is inside the physical band [8.0, 25.0] MMBtu per gross "
            "MWh, at least 200 such hours; converted to a NET basis by the committed "
            "parasitic_load_factors.parquet (the SAME map the benchmark's net actual uses; "
            "COAL default 0.07); plant value is the generation-weighted mean over its units. "
            "The near-HSL (>= p90) window heat_rate_gross_hsl is computed and REPORTED but "
            "never applied. Only flag=='ok' rows are read by the loader."
        ),
        "two_declared_departures_from_the_CT_DERIVER": (
            "This is the COAL sibling of scripts/data/derive_campd_ct_heat_rates.py "
            "(nyiso-89), and it departs from it in exactly two places, BOTH on physics and "
            "BOTH fixed ex ante in PRECOMMIT-nwpp-42 §4 before any solve: (1) the loaded "
            "window is a steady-state screen opTime >= 0.99 rather than the CT deriver's "
            ">= 0.8 x p95 load screen, because a coal unit's NORMAL operating range includes "
            "part load and a near-peak screen would measure only its best hours; (2) fuel "
            "identification reads CAMPD primaryFuelInfo rather than unitType, because at "
            "Jim Bridger, Naughton and North Valmy the coal units and the gas-converted "
            "units are BOTH boilers and unitType cannot separate them. Neither choice was "
            "selected by looking at a result."
        ),
        "why_not_a_free_parameter": (
            "Rule 21 [R-DOF]: this is a measured physical input replacing an ESTIMATE, with "
            "no value of its own. The legacy-bin fleet path prices coal on eGRID's ANNUAL "
            "PLANT AVERAGE PLHTIAN / PLNGENAN — an average over every hour the plant ran, "
            "including starts, shutdowns and deep part load, on a basis that mixes the "
            "plant's non-coal units where it has them. The plant's own metered steady-state "
            "rate is the physically correct operand and is LOWER at every one of the 12 "
            "covered plants (cap-weighted 11.868 -> 11.066 MMBtu/MWh, -6.8 %). Rule 14 "
            "[R-ACCURATE] is the reason it arms: the estimate was silently compensating for "
            "nothing, it was simply wrong, and its error is not uniform - Hunter 13.3303 -> "
            "10.9688 (ratio 1.2153) against Colstrip 10.5702 -> 10.3342 (1.0228). Nothing "
            "here is selectable: there is no scalar, no band, no offset and no sweep. "
            "Declared ex ante in PRECOMMIT-nwpp-42 §4 and never swept against a gate."
        ),
        "structural_signature_not_a_residual_fit": (
            "Rule 1 [R-STRUCT]: the correction is near-ZERO exactly where the model already "
            "reproduces the measured shape, and largest where it does not. Colstrip's "
            "correction is 1.023x and its MEASURED diurnal peak/trough is 1.07 - a flat "
            "plant the model already reads flat. Hunter's correction is 1.2153x and its "
            "measured peak/trough is 1.62 against a model 1.00. A residual-fitted multiplier "
            "would have no reason to line up that way; a real heat rate does."
        ),
        "reach": (
            "Class-gated to COAL in the fleet row loop, so the arm cannot reach a gas, "
            "hydro, nuclear or renewable unit even at a plant that has both: Jim Bridger "
            "(8066) contributes COAL rows and ST_GAS rows from the same plant_code and only "
            "the COAL rows take the measured value (guarded by "
            "tests/unit/data/test_measured_coal_heat_rates.py). Measured in the solve: every "
            "non-coal class moves only through re-dispatch, hydro is EXACTLY flat in all "
            "three years (monthly budgets bind), and the footprint total is unchanged to "
            "0.002 TWh."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: the same quantity regenerates for a forward year from the "
            "then-current CAMPD feed and responds to changed conditions (a plant that "
            "degrades or is retrofitted files a different metered rate). It is a unit "
            "physical property entering as a cost operand, never an outcome pinned to an "
            "actual: no unit is pinned to its observed CEMS generation and no offset, "
            "haircut or rescaling is applied."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: it REPLACES the eGRID heat rate for the covered plants "
            "rather than stacking on it. A coal plant absent from the table, or flagged "
            "out-of-band, keeps its eGRID value unchanged - no fallback value is invented. "
            "No second coal-cost mechanism is introduced and no floor, bridge or adder is "
            "touched."
        ),
    }

    gov: dict = {
        "levers_trace_to_measured_input": True,
        "no_fit_to_price_residuals": True,
        "no_pinning_to_actuals": True,
        "outage_filter_exogenous_net_load": True,
        "authorized_price_tuning_declared": (
            "NONE — no rule-1 [R-STRUCT] / rule-13 [R-MEASURED] authorized price-tuning "
            "channel is in use. Every committed / econ_low / econ_high / peak band on every "
            "class NWPP dispatches is exactly 1.0, verified from the bundle's own dispatch "
            "rather than asserted: the groups in the shared config that DO carry non-unity "
            "bands (CC_INTERMEDIATE, CT_INTERMEDIATE, ST_GAS_INTERMEDIATE) carry ZERO NWPP "
            "energy in all three solved years, machine-checked by "
            "scripts/gen_nwpp42_attestation.py against hourly/class_hourly_<year>.parquet "
            "before this file was written. econ_low_share 0.55 is a STRUCTURAL SHARE, which "
            "rule 1 excludes from the band channel by name. The delta JSON is {}; no phys_* "
            "field exists; no --offer-curve-json, --set, adder, offset, haircut or "
            "proxy-on-a-residual was passed. NWPP is PRICE UNSCORED (rubric v3.8) and no "
            "admissible NWPP price series exists, so the channel could not have been used "
            "even in principle."
        ),
        "attested_by": (
            "NWPP-42 (2026-09-20): NWPP-41's frozen recipe plus ONE arm, "
            "measured_coal_heat_rates=True. Rule 36 [R-YEAR-ISOLATION] landed mid-lane, so "
            "the run is THREE single-year shards composed by the parent (rule 32(d)); the "
            "parent ran no LP (rule 32(a)) and each shard pushed its FULL bundle including "
            "dispatch/<year>_P1.parquet (rule 34(a)). Every shard was pinned to the "
            "immutable SHA b68673a9, and the composer "
            "scripts/probes/_nwpp42_compose_span.py verified that all 855 non-year-carried "
            "scenario_config fields agree across the three legs and that each leg's "
            "gas_price_override matches its OWN calibration_flags.gas_prices entry, before "
            "anything was written. The rule-29(b) control is NOT the committed keeper: "
            "because rule 36 flipped MARKET_SIM_WARMSTART_XYEAR and "
            "MARKET_SIM_P1_BASIS_SEED to default OFF and rule 36(e) WITHDREW the neutrality "
            "claims that justified them, the keeper's 2024/2025 numbers carry a solve-path "
            "artifact of unmeasured size (rule 36(f)); so this lane solved a PAIRED "
            "PER-YEAR CONTROL on NWPP-41's own recipe and differenced arm(year) MINUS "
            "ctl(year). The control-minus-keeper difference is reported separately as "
            "NWPP's own measurement of that artifact "
            "(see disclosures.rule36_year_isolation_artifact_measured). Rule 21 [R-DOF]: "
            f"the ledger's residual-tagged entries are {residual_names} — every one an "
            "inherited generic default carried unchanged from NWPP-40/41, none chosen on an "
            "NWPP residual; the arm is measured-identified, not residual. A KILL CONDITION "
            "was pre-registered in PRECOMMIT-nwpp-42 §6 (a 2025 coal move below 0.5 TWh "
            "would have made the verdict I/inert) and is reported honestly in "
            "disclosures.pre_registered_predictions_scored. Nothing was swept against any "
            "gate."
        ),
        "cross_iso_defect_reported_not_fixed": (
            "Rules 25 [R-ISO-SCOPE] / 28(d) [R-MECH-MATRIX]: NWPP-41's pooled-PRB-proxy "
            "defect still reaches MISO (12 affected plants), PJM (2) and SPP (3-5) and is "
            "NOT fixed here. Separately, the eGRID-annual-average heat-rate estimate this "
            "lane replaces is the DEFAULT for every legacy-bin ISO, so the same defect is "
            "present wherever use_campd_bins is inert; measured_coal_heat_rates is "
            "registered as U (untested) in all eight other ISO shards of the mechanism "
            "matrix with NOTHING transferred — each target lane must derive its own table "
            "from its own market's CAMPD data."
        ),
        "measured_input_switches": switches,
    }
    att["governance"] = gov

    disc = dict(_INHERITED_DISCLOSURES)
    disc["note"] = (
        "NWPP-42 disclosures — the determination basis, reported at full magnitude and "
        "absorbed nowhere. Every NWPP-40 / NWPP-41 disclosure is inherited VERBATIM and "
        "still applies (the C1 taxonomy repair and the PRB proxy are NWPP-41's and ride "
        "unchanged); the entries below are this lane's own."
    )
    disc["coal_heat_rate_was_an_estimate"] = (
        "The lane's headline. NWPP takes the legacy aggregate-fleet path (it is absent from "
        "CAMPD_BINNING_ISOS by owner ruling N8), and that path prices coal on eGRID's ANNUAL "
        "PLANT AVERAGE PLHTIAN / PLNGENAN. Measured against the plants' own CAMPD-metered "
        "steady-state rates, the estimate is HIGH at every one of the 12 covered plants "
        "(98.2 % of NWPP COAL capacity), cap-weighted 11.868 -> 11.066 MMBtu/MWh (-6.8 %), "
        "and the error is far from uniform: Hunter 13.3303 -> 10.9688 (1.2153x), North Valmy "
        "13.1105 -> 11.3634 (1.1537x), Hardin 15.8428 -> 14.3005 (1.1078x), Wyodak 13.1065 -> "
        "12.0467 (1.0880x) against Colstrip 10.5702 -> 10.3342 (1.0228x) and Jim Bridger "
        "11.2457 -> 11.1511 (1.0085x). Rule 14 [R-ACCURATE] is why the accurate input is "
        "kept whatever it does to the residual."
    )
    disc["gates_differenced_against_the_paired_control"] = (
        "Every scored criterion, arm MINUS the lane's own per-year control (not the committed "
        "keeper — see rule36_year_isolation_artifact_measured). NOTHING REGRESSES AND THE "
        "DETERMINATION DOES NOT MOVE: C1 fuel-mix PASS -> PASS (18/18 all, 14/14 free), C2 "
        "system volume PASS -> PASS, C6 governance PASS -> PASS, C8 forced-energy share "
        "PASS -> PASS (D-2 reads 0.0 % forced on every class in every year), C4 dispatch "
        "correlation FAIL -> FAIL, determination NOT-YET -> NOT-YET on {dispatch_corr} alone. "
        "Every C4 coal number moves toward the measured fleet: r 0.539 / 0.547 / 0.502 -> "
        "0.570 / 0.559 / 0.524 and NRMSE 0.301 / 0.397 / 0.432 -> 0.292 / 0.387 / 0.408 in "
        "2023 / 2024 / 2025 — 2023's NRMSE crosses INSIDE the 0.30 gate, and C4 coal now "
        "fails on the correlation floor alone in that year. C4 gas passes in all three years "
        "in both legs and is untouched. Coal volume rises 39.613 -> 41.549 (2023), 27.008 -> "
        "27.390 (2024) and 27.207 -> 28.317 TWh (2025) against a measured 42.27 / 38.30 / "
        "42.26; the C2 2025 coal row improves from -29.3 % to -26.4 % (SKIPPED on the "
        "preliminary EIA-923 vintage, so it did not gate either way). The reported-only C5a "
        "CO2 error improves -16.0 / -23.8 / -21.5 % -> -14.4 / -23.5 / -20.6 %, which changes "
        "no determination (rubric v2.9). Rule 1 [R-STRUCT]: the residual move is NOT why this "
        "arm is kept — rule 14 [R-ACCURATE] is, and the arm would stay in even had the "
        "residual worsened."
    )
    disc["pre_registered_predictions_scored"] = (
        "PRECOMMIT-nwpp-42 §6, scored honestly including the miss. (1) 'Coal volume rises "
        "materially but does NOT close the gap' — HELD: +1.936 / +0.382 / +1.110 TWh against "
        "a remaining deficit of 0.7 / 10.9 / 13.9 TWh. (2) 'r improves; I do NOT predict it "
        "reaches 0.70' — HELD in both halves: +0.031 / +0.012 / +0.022, still far below the "
        "0.70 floor. (3) '2023 is the RISK year and may push a C1 row out of band' — DID NOT "
        "HAPPEN: C1 stays 18/18 despite 2023 carrying the largest coal move. (4) 'zero "
        "movement outside coal' — HELD as intended: hydro is EXACTLY flat in all three years "
        "and the footprint total moves 0.000 / -0.001 / -0.002 TWh; the non-coal classes that "
        "do move (CC_REGULAR, CT_PEAKER, ST_GAS) move only as displaced merit order, which is "
        "the arm's intended effect and not reach. (5) 'DOF unchanged at 3/3' — HELD, "
        "build_dof_ledger emits 3 entries / 3 residual, identical to NWPP-40 and NWPP-41. "
        "THE KILL CONDITION WAS PRE-REGISTERED AND IS REPORTED AT FULL MAGNITUDE: a 2025 coal "
        "move below 0.5 TWh would have made the verdict I (inert). 2025 moved +1.110 TWh, so "
        "the condition did not fire — but 2024 moved only +0.382 TWh, which is BELOW that "
        "line, and had 2024 been the pre-registered kill year this arm would have read inert. "
        "Named rather than glossed."
    )
    disc["what_it_does_not_close"] = (
        "Stated at the gate, not absorbed. The arm moves coal in the right direction and "
        "does NOT close the volume gap: model coal remains far below the measured "
        "42.27 / 38.30 / 42.26 TWh. The residual driver is the one NWPP-41 routed and this "
        "lane did not attempt — the coal offer stack is BIMODAL (a must-run tranche in the "
        "money essentially every hour, versus a much dearer economic tranche), so the fleet "
        "is largely price-insensitive and a uniform heat-rate correction cannot produce the "
        "measured diurnal amplitude. The structural successor is per-plant CAMPD binning, "
        "which is blocked on bin_assignments_NWPP.csv being absent for every legacy-bin ISO "
        "(PRECOMMIT-nwpp-42 §1, fork (b)). C4 coal is expected to remain FAIL and is "
        "reported as such rather than pursued by tuning (rule 1 [R-STRUCT])."
    )
    disc["rule36_year_isolation_artifact_measured"] = (
        "NWPP's own measurement of the artifact rule 36(f) records as UNMEASURED outside "
        "MISO, obtained from this lane's paired per-year control (NWPP-41's recipe, "
        "re-solved one year per container) against NWPP-41's committed span bundle. The "
        "result is a clean split: ANNUAL CLASS VOLUME IS UNCHANGED — control minus keeper is "
        "0.000 TWh for EVERY class in EVERY year, including coal — while the HOURLY "
        "allocation moves materially: max |delta| 765.2 / 817.1 / 817.9 MW and "
        "sum |delta| 1.516 / 0.915 / 0.698 TWh in 2023 / 2024 / 2025, concentrated in HYDRO "
        "and CC_REGULAR (2023: hydro 690.3 GWh, CC_REGULAR 516.6 GWh, COAL_PRB 271.5 GWh) - "
        "the flexible resources whose monthly energy budgets bind the annual total while "
        "leaving the within-year placement free. That is exactly the shape of a degenerate "
        "re-optimisation, and it is why this lane did not difference the arm against the "
        "committed keeper: the artifact is invisible in C1/C2 (annual volume) and lands "
        "squarely on C4 (hourly correlation), the criterion at issue. MISO measured up to "
        "24.18 TWh of ANNUAL class movement; NWPP measures 0.000. The two are not "
        "comparable and neither generalises - each lane owes its own measurement."
    )
    disc["solved_years"] = solved_years
    disc["recorded_signature"] = {
        "measured_coal_heat_rates": sc.get("measured_coal_heat_rates"),
        "coal_prb_proxy_own_iso": sc.get("coal_prb_proxy_own_iso"),
        "hydro_cascade_coupling": sc.get("hydro_cascade_coupling"),
        "hydro_backfill_year": meta.get("hydro_backfill_year"),
        "hydro_eia930_monthly": bool(meta.get("hydro_eia930_monthly")),
        "plant_level_fleet": sc.get("plant_level_fleet"),
        "use_campd_bins": sc.get("use_campd_bins"),
        "use_campd_bins_note": (
            "reads True in the config and is INERT: NWPP is absent from CAMPD_BINNING_ISOS "
            "(card N8), so the fleet takes the legacy aggregate_fleet path with "
            "plant_level_fleet=True. Identical to the NWPP-41 control."
        ),
        "composed_from": meta.get("composed_from"),
        "control_diff": (
            "scenario_config differs from the lane's own per-year control "
            "(results/calibration/nwpp42_mer_span, NWPP-41's recipe under rule-36 year "
            "isolation) in exactly ONE field: measured_coal_heat_rates (False -> True). "
            "Machine-checked per year by scripts/probes/_nwpp42_leg_check.py, which "
            "CLASSIFIES each delta rather than counting it: the two year-carried fields "
            "(gas_price_override, weather_year) are verified against the keeper's own "
            "meta.json gas_prices map and the leg's year, and four fields that did not "
            "exist when NWPP-41 solved (measured_st_heat_rates, mid_vintage_exit_carry, "
            "nyiso_ct_peaker_committed_measured, soco_gas_st_campaign_commitment) are "
            "admitted only because each sits at its dataclass default AND is registered in "
            "_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS as dropped at that value, i.e. the repo "
            "itself declares they cannot move a solve."
        ),
        "dispatched_classes": sorted(dispatched),
    }
    att["disclosures"] = disc
    att["exceptions"] = []
    return att


def main() -> None:
    """Write the attestation into the NWPP-42 span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help="bundle directory to write calibration_attestation.json into",
    )
    args = ap.parse_args()
    att = build(Path(args.bundle))
    out = Path(args.bundle) / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")
    print(f"  entries: {[e['name'] for e in fp['entries']]}")
    print("  gate G5: authorized_price_tuning = NONE (verified from dispatch)")


if __name__ == "__main__":
    main()
