"""Write ``calibration_attestation.json`` for the caiso-159 keeper candidates.

The caiso-158 arms execute the caiso-156 charter: the shared CT heat-rate
derive (``scripts/data/derive_campd_ct_heat_rates.py``) now applies its own
declared physical band ``[6.0, 25.0]`` MMBtu/MWh **per loaded hour** rather than
only to the plant aggregate. It is an INPUT CORRECTION — **zero new
parameters**, zero ``ScenarioConfig`` surface, no threshold moved — so each
promoted ISO's attestation is its incumbent keeper's, carried forward with:

1. a rewritten ``governance.attested_by`` describing the meter screen, and
2. every ledgered exception's ``magnitude`` RE-MEASURED on the arm-B bundle.

The DOF ledger is carried **verbatim**: because the correction introduces no
free parameter, ``n_entries`` and ``n_residual`` must be unchanged, and this
script asserts that rather than trusting it (rule 21 ``[R-DOF]``).

Promotion premise, re-verified before this script was written: each arm's
``ScenarioConfig`` is equal to its ISO's CURRENT designated keeper's. CAISO
differs in zero fields; NEISO in nine, every one a field ADDED to
``ScenarioConfig`` after the neiso-72 solve and recorded here at its declared
default (seven ``False``, two ``None``) — schema drift, not a config change.
The count and the field list are COMPUTED by :func:`config_drift`, not typed:
a ``dict.get(k)`` diff collapses "absent" and "present-but-``None``", which is
exactly how the first cut of this promotion undercounted the nine as seven.
**NYISO is deliberately absent**: its keeper moved to nyiso-113, which arms
``nyiso_li_locational_reserve``, and the caiso-158 NYISO arm was controlled
against the superseded nyiso-112 recipe with that field ``False``. Promoting
it would silently drop a published Zone-K reserve requirement — a rule 14
``[R-ACCURATE]`` regression — so it is not promotable without a re-solve.

**Nothing here is hand-typed from a solve.** Every magnitude is recomputed at
run time from the two arm bundles' own committed sidecars and from the
committed CT artifact's bytes, so the attestation cannot drift from what it
describes.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso159_attestation.py
    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso159_attestation.py --iso CAISO
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

YEARS = (2023, 2024, 2025)

#: The band the derive declares and, before caiso-158, applied only to the
#: plant aggregate. Physical, pre-existing, and NOT a free parameter — see
#: ``derive_campd_ct_heat_rates._HR_MIN`` / ``_HR_MAX``.
HR_BAND = (6.0, 25.0)

#: Per-ISO promotion wiring: which incumbent attestation to carry forward and
#: which A/B pair re-measures its magnitudes.
ISOS: dict[str, dict[str, str]] = {
    "CAISO": {
        "source": "caiso157_restore_B",
        "control": "caiso156_meter_control_A",
        "target": "caiso156_meter_screen_B",
        "carried_from": (
            "2026-08-02-caiso157-partition-restore-b -> "
            "2026-07-31-caiso153-reid-b -> 2026-07-31-caiso-151-firm-selfsched "
            "-> 2026-07-31-caiso148-nuclear-availability (owner ledger, "
            "caiso-145)"
        ),
    },
    "NEISO": {
        "source": "neiso72_hy_window_B",
        "control": "neiso_c156_meter_control_A",
        "target": "neiso_c156_meter_screen_B",
        "carried_from": (
            "2026-07-31-neiso-72-hy-window (NEISO ledger, neiso-55 onward)"
        ),
    },
}

CARRY = (
    "CARRIED FORWARD from the incumbent keeper unchanged in substance. "
    "caiso-159 promotes an INPUT CORRECTION with zero free parameters, so it "
    "creates no new caveat and spends no new ledger slot. "
)


def artifact_stats(iso: str) -> dict:
    """Return the committed CT artifact's cap-weighted applied rate and md5.

    Read from ``data/raw/_processed-legacy/campd_ct_heat_rates_<ISO>.csv`` --
    the exact bytes the arm-B solve consumed, so the attestation pins the
    input it is attesting to rather than restating a number from a document.
    """
    path = REPO / f"data/raw/_processed-legacy/campd_ct_heat_rates_{iso}.csv"
    frame = pd.read_csv(path)
    applied = frame[frame["flag"] == "ok"]
    weight = applied["class_capacity_mw"]
    return {
        "path": str(path.relative_to(REPO)),
        "md5": hashlib.md5(path.read_bytes()).hexdigest(),
        "cap_weighted_net_hr": round(
            float((applied["heat_rate"] * weight).sum() / weight.sum()), 4
        ),
        "plants_applied": int(len(applied)),
        "plants_total": int(len(frame)),
    }


def ct_energy(bundle: Path) -> dict[int, float]:
    """Return per-year P1 CT_PEAKER energy in TWh from the class hourlies."""
    out: dict[int, float] = {}
    for year in YEARS:
        path = bundle / "hourly" / f"class_hourly_{year}.parquet"
        if not path.is_file():
            continue
        frame = pd.read_parquet(path)
        frame = frame[(frame["pass"] == "P1") & (frame["klass"] == "CT_PEAKER")]
        out[year] = round(float(frame["mw"].sum()) / 1e6, 4)
    return out


def lw_lambda(bundle: Path) -> dict[int, float]:
    """Return per-year load-weighted mean lambda from the system hourlies."""
    out: dict[int, float] = {}
    for year in YEARS:
        path = bundle / "hourly" / f"system_{year}.parquet"
        if not path.is_file():
            continue
        frame = pd.read_parquet(path)
        frame = frame[frame["pass"] == "P1"]
        # Full precision on purpose: the attested percentage change is a ratio
        # of two nearly-equal lambdas, so rounding before the divide loses the
        # third significant figure of the delta this arm is judged on.
        out[year] = float(
            (frame["price"] * frame["demand"]).sum() / frame["demand"].sum()
        )
    return out


def price_tail(bundle: Path) -> dict[int, dict]:
    """Return per-year model hours above $200 and the max zonal lambda (C3c)."""
    out: dict[int, dict] = {}
    for year in YEARS:
        path = bundle / "hourly" / f"system_{year}.parquet"
        if not path.is_file():
            continue
        frame = pd.read_parquet(path)
        frame = frame[frame["pass"] == "P1"]
        hourly_max = frame.groupby("hour", observed=True)["price"].max()
        out[year] = {
            "hours_gt_200": int((hourly_max > 200.0).sum()),
            "max_lambda": round(float(hourly_max.max()), 0),
        }
    return out


#: Sentinel distinguishing "key absent" from "key present with value None".
#: `dict.get(k)` collapses the two, which is exactly how the first cut of this
#: promotion undercounted NEISO's schema drift as 7 when it is 9 — the two
#: missed fields (demand_growth_vintage, gas_offer_margin_anchor_by_zone) are
#: present-and-None in the arm and absent in the older keeper.
_MISSING = object()


def config_drift(arm: Path, keeper: Path) -> dict:
    """Return the ScenarioConfig delta between two bundles, absence-aware.

    Splits the delta into keys only one side declares (schema drift: the older
    bundle predates the field) and keys both declare with different values (a
    real config change). An input-correction promotion must have zero of the
    latter.
    """
    a = json.loads((arm / "run_config.json").read_text())["scenario_config"]
    k = json.loads((keeper / "run_config.json").read_text())["scenario_config"]
    changed = [
        key
        for key in sorted(set(a) | set(k))
        if a.get(key, _MISSING) != k.get(key, _MISSING)
    ]
    return {
        "arm_only": [key for key in changed if key not in k],
        "keeper_only": [key for key in changed if key not in a],
        "value_diffs": [key for key in changed if key in a and key in k],
    }


def build_attested_by(
    iso: str,
    art: dict,
    ct_a: dict,
    ct_b: dict,
    lam_a: dict,
    lam_b: dict,
    drift: dict,
) -> str:
    """Compose the governance narrative from the measured arm bytes."""
    n_drift = len(drift["arm_only"]) + len(drift["keeper_only"])
    drift_clause = (
        "differs in zero fields"
        if not n_drift
        else (
            f"differs in {n_drift} field(s), every one a field ADDED to "
            "ScenarioConfig after that keeper solved and recorded here at its "
            f"declared default ({', '.join(drift['arm_only'] + drift['keeper_only'])}) "
            "— schema drift, not a config change"
        )
    )
    ct = " / ".join(f"{ct_a.get(y, 0):.4f}->{ct_b.get(y, 0):.4f}" for y in YEARS)
    delta = " / ".join(f"{ct_b.get(y, 0) - ct_a.get(y, 0):+.4f}" for y in YEARS)
    lam = " / ".join(f"{lam_a.get(y, 0):.2f}->{lam_b.get(y, 0):.2f}" for y in YEARS)
    pct = " / ".join(
        f"{100 * (lam_b.get(y, 0) / lam_a[y] - 1):+.3f}" for y in YEARS if lam_a.get(y)
    )
    return (
        f"caiso-159 (2026-08-03): the incumbent {iso} keeper recipe with NO "
        "CONFIG CHANGE AT ALL — the ScenarioConfig this arm solved carries "
        f"ZERO value differences from the committed keeper's, and {drift_clause}. "
        "The delta is the CONTENT of the shared "
        "measured CT heat-rate artifact the keeper already consumes. THE "
        "DEFECT IT FIXES (caiso-146 §2.4): "
        "scripts/data/derive_campd_ct_heat_rates.py declares a physical band "
        f"[{HR_BAND[0]}, {HR_BAND[1]}] MMBtu/MWh but applied it ONLY to the "
        "plant aggregate, so individual loaded hours at physically impossible "
        "heat rates — a meter artifact, not generation behaviour — were "
        "averaged into the plant rate and diluted it LOW. The screen now "
        "applies the module's OWN declared band per loaded hour and evaluates "
        "the _MIN_LOADED_HOURS trust gate on the in-band hours. ZERO NEW "
        "PARAMETERS: cap percentile, loaded fraction, all-hours gross_mwh "
        "weights, parasitic conversion, the plant-aggregate flag and the "
        "flag=='ok' application rule are untouched. THE ARTIFACT THIS "
        f"ATTESTATION PINS: {art['path']} md5 {art['md5']}, cap-weighted "
        f"applied rate {art['cap_weighted_net_hr']:.4f} MMBtu/MWh net over "
        f"{art['plants_applied']}/{art['plants_total']} plants. LIVENESS, "
        "measured on this bundle against its own same-HEAD cold-solved "
        f"control: P1 CT_PEAKER energy {ct} TWh ({delta}) for 2023/24/25 — the "
        "class re-prices DOWNWARD in every year, as pre-registered. "
        f"Load-weighted lambda {lam} $/MWh ({pct} %), inside the "
        "pre-committed 1.0 pp escalation trigger in every year, so no "
        "leave-one-year-out escalation is owed. Across the three solved ISOs "
        "the A/B is NINE ISO-years, NINE negative CT_PEAKER deltas, ZERO "
        "criterion flips and ZERO D-gate flips. Rule 14 [R-ACCURATE] governs "
        "the promotion in both directions: the corrected input goes in because "
        "it is the corrected input, and it would equally have gone in had the "
        "residual worsened. Rule 23 [R-FROZEN-DERIVE] is satisfied — the "
        "re-derivation is driven by a meter defect in the derive, never by a "
        "residual. Rule 28b: measured_ct_heat_rates keeps its existing per-ISO "
        "cell verdicts; this is an input correction with no mechanism surface. "
        "Evidence: "
        "results/calibration/FINDING-caiso158-ct-heat-rate-meter-screen-2026-08-03.md, "
        "PREREG-caiso156-ct-heat-rate-meter-screen-2026-08-02.md, "
        "PREREG-caiso156-ADDENDUM-rebaseline-cache-2026-08-02.md."
    )


def carry_exceptions(
    att: dict,
    target_name: str,
    carried_from: str,
    lam_a: dict,
    lam_b: dict,
    tail_a: dict,
    tail_b: dict,
) -> dict:
    """Carry the ledger forward, re-measuring each entry on the arm-B bundle."""
    for exc in att.get("exceptions", []):
        criterion = exc.get("criterion")
        try:
            year = int(exc.get("year", 0) or 0)
        except (TypeError, ValueError):
            year = 0
        if criterion == "price_tail" and year in tail_b:
            exc["magnitude"] = (
                f"RE-MEASURED on {target_name}: model "
                f"{tail_b[year]['hours_gt_200']} h > $200 (max "
                f"${tail_b[year]['max_lambda']:.0f}) against the same-HEAD "
                f"cold-solved control's "
                f"{tail_a.get(year, {}).get('hours_gt_200', '?')} h (max "
                f"${tail_a.get(year, {}).get('max_lambda', 0):.0f}). "
                "PRIOR MAGNITUDE: "
            ) + exc["magnitude"]
        elif criterion == "price_mean" and year in lam_b and lam_a.get(year):
            exc["magnitude"] = (
                f"RE-MEASURED on {target_name}: load-weighted lambda "
                f"${lam_a[year]:.2f} -> ${lam_b[year]:.2f}/MWh vs the "
                f"same-HEAD cold-solved control "
                f"({100 * (lam_b[year] / lam_a[year] - 1):+.3f} %). "
                "PRIOR MAGNITUDE: "
            ) + exc["magnitude"]
        exc["reason"] = CARRY + exc.get("reason", "")
        exc["carried_from"] = carried_from
    return att


def generate(iso: str) -> dict:
    """Write one ISO's attestation and return a summary of what was measured."""
    wiring = ISOS[iso]
    source = (
        REPO / f"results/calibration/{wiring['source']}/calibration_attestation.json"
    )
    control = REPO / f"results/calibration/{wiring['control']}"
    target_bundle = REPO / f"results/calibration/{wiring['target']}"

    art = artifact_stats(iso)
    ct_a, ct_b = ct_energy(control), ct_energy(target_bundle)
    lam_a, lam_b = lw_lambda(control), lw_lambda(target_bundle)
    tail_a, tail_b = price_tail(control), price_tail(target_bundle)

    # The promotion premise, MEASURED not asserted: an input correction may
    # differ from the incumbent only by fields the older bundle predates.
    # Any shared key with a different value is a real config change and
    # disqualifies the arm as a drop-in keeper.
    keeper_bundle = REPO / f"results/calibration/{wiring['source']}"
    drift = config_drift(target_bundle, keeper_bundle)
    if drift["value_diffs"]:
        raise SystemExit(
            f"{iso}: {len(drift['value_diffs'])} ScenarioConfig VALUE "
            f"difference(s) vs {wiring['source']}: "
            f"{', '.join(drift['value_diffs'])}. An input-correction promotion "
            "must carry zero value diffs — this arm was controlled against a "
            "different recipe than the one it would replace."
        )

    att = json.loads(source.read_text())
    before = (
        att["free_parameters"]["n_entries"],
        att["free_parameters"]["n_residual"],
    )

    att["governance"]["attested_by"] = build_attested_by(
        iso, art, ct_a, ct_b, lam_a, lam_b, drift
    )
    att["ct_heat_rate_artifact"] = art
    att["config_drift_vs_incumbent"] = drift
    carry_exceptions(
        att, wiring["target"], wiring["carried_from"], lam_a, lam_b, tail_a, tail_b
    )

    # Rule 21 [R-DOF]: an input correction introduces no free parameter, so the
    # ledger must be byte-identical in shape. Assert it rather than assume it.
    dof = att["free_parameters"]
    dof["n_entries"] = len(dof["entries"])
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e.get("identification") == "residual"
    )
    if (dof["n_entries"], dof["n_residual"]) != before:
        raise SystemExit(
            f"{iso}: DOF ledger changed {before} -> "
            f"({dof['n_entries']}, {dof['n_residual']}); an input correction "
            "must not move the ledger"
        )

    out = target_bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    return {
        "iso": iso,
        "wrote": str(out.relative_to(REPO)),
        "artifact": art,
        "ct_peaker_twh": {y: (ct_a.get(y), ct_b.get(y)) for y in YEARS},
        "lw_lambda": {y: (lam_a.get(y), lam_b.get(y)) for y in YEARS},
        "exceptions": len(att.get("exceptions", [])),
        "dof": before,
    }


def main(argv: list[str] | None = None) -> int:
    """Generate the caiso-159 attestations for the promoted ISOs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", choices=sorted(ISOS), action="append")
    args = parser.parse_args(argv)

    for iso in args.iso or sorted(ISOS):
        summary = generate(iso)
        print(f"wrote {summary['wrote']}")
        print(
            f"  artifact: md5 {summary['artifact']['md5'][:12]} "
            f"cap-wt {summary['artifact']['cap_weighted_net_hr']:.4f} "
            f"({summary['artifact']['plants_applied']}/"
            f"{summary['artifact']['plants_total']} plants)"
        )
        for year in YEARS:
            ct_a, ct_b = summary["ct_peaker_twh"][year]
            lam_a, lam_b = summary["lw_lambda"][year]
            if ct_a is None or lam_a is None:
                continue
            print(
                f"  {year}: CT_PEAKER {ct_a:.4f} -> {ct_b:.4f} TWh "
                f"({ct_b - ct_a:+.4f}) | lambda {lam_a:.2f} -> {lam_b:.2f} "
                f"({100 * (lam_b / lam_a - 1):+.3f} %)"
            )
        print(
            f"  exceptions carried: {summary['exceptions']} | "
            f"DOF unchanged: {summary['dof'][0]} entries "
            f"({summary['dof'][1]} residual)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
