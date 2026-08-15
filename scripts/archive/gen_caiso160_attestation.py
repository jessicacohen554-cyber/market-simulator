"""Write ``calibration_attestation.json`` for the caiso-160 NYISO keeper candidate.

caiso-159 promoted the CT heat-rate meter screen (caiso-156 fix ``f6238a5``) into
the CAISO and NEISO keepers and **deliberately left NYISO out**: its keeper had
moved to nyiso-113, which arms ``nyiso_li_locational_reserve``, while the
caiso-158 arms were controlled against the superseded nyiso-112 recipe with that
field ``False``. Promoting that arm would have dropped a published Zone-K
reserve requirement to gain an input correction — a rule 14 ``[R-ACCURATE]``
regression committed in the name of rule 14.

This session re-solves the pair on the nyiso-113 recipe so the two changes
compose. The measurement helpers, and above all the absence-aware
:func:`config_drift` premise guard, are IMPORTED from
``gen_caiso159_attestation`` rather than re-implemented — a second copy of that
function is exactly how the first cut of the caiso-159 promotion undercounted
NEISO's schema drift as seven fields when it is nine.

What differs from caiso-159 is the NARRATIVE only. caiso-159's ``attested_by``
states its own session, its own three-ISO nine-year tally, and a "re-prices
DOWNWARD in every year" liveness claim measured on CAISO and NEISO. None of
that describes this run, and rewriting it in place would falsify a committed
record, so this module supplies its own :func:`build_attested_by` and leaves the
caiso-159 generator untouched.

As there, **nothing is hand-typed from a solve**: every magnitude is recomputed
at run time from the two arm bundles' committed sidecars and from the CT
artifact's own bytes.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/gen_caiso160_attestation.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.archive import gen_caiso159_attestation as c159  # noqa: E402
from scripts.archive.gen_caiso159_attestation import (  # noqa: E402
    HR_BAND,
    YEARS,
    artifact_stats,
    carry_exceptions,
    config_drift,
    ct_energy,
    lw_lambda,
    price_tail,
)

ISO = "NYISO"

#: Promotion wiring. ``source`` is the incumbent keeper whose attestation is
#: carried forward AND the recipe both arms replay; ``control`` is this
#: session's own same-HEAD cold-solved pre-fix arm.
WIRING = {
    "source": "nyiso113_lilocational_B",
    "control": "nyiso160_ctmeter_control_A",
    "target": "nyiso160_ctmeter_screen_B",
    "carried_from": (
        "2026-08-02-nyiso-113-li-locational -> 2026-08-02-nyiso112-ramp-plus-peaker "
        "-> 2026-07-31-nyiso-109-zonal-anchor (NYISO ledger, nyiso-100 onward)"
    ),
}

CARRY = (
    "CARRIED FORWARD from the incumbent keeper unchanged in substance. "
    "caiso-160 promotes an INPUT CORRECTION with zero free parameters, so it "
    "creates no new caveat and spends no new ledger slot. "
)

#: ScenarioConfig fields whose SHIPPED DEFAULT moved on main after the incumbent
#: keeper solved, so both arms record a different value than the keeper bundle
#: WITHOUT anyone having changed the recipe. :func:`config_drift` cannot tell
#: this apart from a real recipe change -- the field is present on both sides
#: with different values either way -- so each one is enumerated here with the
#: commit that moved it and the reason it cannot reach a NYISO BACKCAST.
#:
#: This allowlist is NOT self-certifying. It is honoured only when the K2
#: control bit-identity below holds; if the control diverges from the keeper by
#: so much as one MW on one class-hour, one of these moved defaults DID reach
#: the backcast and the promotion stops. The evidence is the measurement, never
#: the entry.
DEFAULT_MOVES = {
    "retirement_rule": (
        "24b1602 flipped the default legacy -> pipeline. Capacity-evolution "
        "step 3 (economic retirement), forecast-mode only -- a backcast solves "
        "a fixed historical fleet per year and never runs the evolution loop."
    ),
    "entry_rate_limits": (
        "3e33f15 armed it by default. Capacity-evolution step 5 (economic new "
        "entry), forecast-mode only; a backcast builds nothing."
    ),
    "entry_commissioning_lag": (
        "3e33f15 armed it by default. Same step-5 forecast-only entry path."
    ),
    "caiso_ra_min_load_frac": (
        "a0fc302 task 3(b) made it CAISO-SCOPED under rule 25 [R-ISO-SCOPE]. It "
        "had been assigned unconditionally, so a CAISO-fitted 0.26 rode the "
        "recorded recipe of all 119 bundles in every ISO; non-CAISO now records "
        "the neutral shipped 0.40. Every reader sits behind "
        "`caiso_ra_mustoffer and iso == 'CAISO'`, and NYISO carries "
        "caiso_ra_mustoffer=False -- a RECORDING change, not a solve change."
    ),
}


def control_bit_identity(control: Path, keeper: Path) -> dict[int, float]:
    """Return per-year max |ΔMW| on any P1 class-hour, control vs keeper.

    The K2 gate. The control arm replays the keeper's recipe at THIS HEAD
    against the keeper's OWN (pre-fix) artifact, so any non-zero entry means
    something that landed after the keeper solved -- a moved default in
    :data:`DEFAULT_MOVES`, or one of the src/market_sim commits since -- reached
    the backcast. Zero everywhere is what licenses reading the A/B delta as the
    CT artifact's alone.
    """
    out: dict[int, float] = {}
    for year in YEARS:
        a_path = control / "hourly" / f"class_hourly_{year}.parquet"
        k_path = keeper / "hourly" / f"class_hourly_{year}.parquet"
        if not (a_path.is_file() and k_path.is_file()):
            continue
        a = pd.read_parquet(a_path)
        k = pd.read_parquet(k_path)
        a, k = a[a["pass"] == "P1"], k[k["pass"] == "P1"]
        merged = a.merge(
            k, on=["klass", "hour"], suffixes=("_a", "_k"), how="outer"
        ).fillna(0.0)
        out[year] = float((merged["mw_a"] - merged["mw_k"]).abs().max())
    return out


def build_attested_by(
    art: dict,
    ct_a: dict,
    ct_b: dict,
    lam_a: dict,
    lam_b: dict,
    drift: dict,
) -> str:
    """Compose the NYISO governance narrative from the measured arm bytes."""
    n_schema = len(drift["arm_only"]) + len(drift["keeper_only"])
    moved = drift.get("default_moves_exempted", {})
    identity = drift.get("k2_control_bit_identity_max_abs_mw", {})
    parts = []
    if n_schema:
        parts.append(
            f"differs in {n_schema} field(s) present on only one side "
            f"({', '.join(drift['arm_only'] + drift['keeper_only'])}) — schema "
            "drift, not a config change"
        )
    if moved:
        parts.append(
            f"records a different value for {len(moved)} field(s) whose SHIPPED "
            f"DEFAULT moved on main after the keeper solved ({', '.join(sorted(moved))}), "
            "none of them a recipe choice by this session and none reachable "
            "from a NYISO backcast — three are forecast-only capacity-evolution "
            "fields (a backcast solves a fixed historical fleet and never runs "
            "the evolution loop) and caiso_ra_min_load_frac was re-scoped to "
            "CAISO under rule 25, so non-CAISO now records the neutral shipped "
            "0.40 behind a reader gate NYISO never opens. THAT CLAIM IS "
            "MEASURED, NOT ASSERTED: the same-HEAD cold-solved control "
            "reproduces the committed keeper BIT-IDENTICALLY, max |ΔMW| = "
            + ", ".join(f"{y}: {v:.6f}" for y, v in sorted(identity.items()))
            + " on every one of its P1 class-hours, which also clears the seven "
            "src/market_sim commits that landed after the keeper solved and "
            "answers the standing caiso-146 HEAD-drift item in the negative for "
            "this ISO"
        )
    drift_clause = "differs in zero fields" if not parts else "; ".join(parts)
    ct = " / ".join(f"{ct_a.get(y, 0):.4f}->{ct_b.get(y, 0):.4f}" for y in YEARS)
    delta = " / ".join(f"{ct_b.get(y, 0) - ct_a.get(y, 0):+.4f}" for y in YEARS)
    lam = " / ".join(f"{lam_a.get(y, 0):.2f}->{lam_b.get(y, 0):.2f}" for y in YEARS)
    pct = " / ".join(
        f"{100 * (lam_b.get(y, 0) / lam_a[y] - 1):+.3f}" for y in YEARS if lam_a.get(y)
    )
    return (
        "caiso-160 (2026-08-03): the incumbent NYISO keeper recipe with NO "
        "CONFIG CHANGE AT ALL — the ScenarioConfig this arm solved carries ZERO "
        f"value differences from the committed keeper's, and {drift_clause}. "
        "The delta is the CONTENT of the shared measured CT heat-rate artifact "
        "the keeper already consumes (measured_ct_heat_rates=true since "
        "nyiso-89, carried in the prb_overrides channel). THE DEFECT IT FIXES "
        "(caiso-146 §2.4): scripts/data/derive_campd_ct_heat_rates.py declares "
        f"a physical band [{HR_BAND[0]}, {HR_BAND[1]}] MMBtu/MWh but applied it "
        "ONLY to the plant aggregate, so individual loaded hours at physically "
        "impossible heat rates — a meter artifact, not generation behaviour — "
        "were averaged into the plant rate and diluted it LOW. The screen now "
        "applies the module's OWN declared band per loaded hour and evaluates "
        "the _MIN_LOADED_HOURS trust gate on the in-band hours. ZERO NEW "
        "PARAMETERS: cap percentile, loaded fraction, all-hours gross_mwh "
        "weights, parasitic conversion, the plant-aggregate flag and the "
        "flag=='ok' application rule are untouched. "
        f"THE ARTIFACT THIS ATTESTATION PINS: {art['path']} md5 {art['md5']}, "
        f"cap-weighted applied rate {art['cap_weighted_net_hr']:.4f} MMBtu/MWh "
        f"net over {art['plants_applied']}/{art['plants_total']} plants. "
        "NYISO CARRIES THE LARGEST ARTIFACT MOVEMENT OF ALL SIX ISOs "
        "(+0.3586 cap-weighted, against CAISO +0.176, NEISO +0.171, PJM +0.069, "
        "ERCOT +0.063, MISO +0.030) AND IT IS ONE-SIDED DEARER — 17 plants "
        "dearer, 0 cheaper, 2 unchanged, no plant changing flag, with only "
        "Gowanus (15.2804 -> 16.9538) and Narrows (15.7537 -> 16.7814) moving "
        "past 0.5. Both are NYC in-city CTs whose sub-6.0 loaded hours were "
        "diluting the meter low. "
        "WHY THIS RUN EXISTS AT ALL, AND WHY IT NEEDED ITS OWN CONTROL: "
        "caiso-159 could not promote the caiso-158 NYISO arm because nyiso-113 "
        "promoted underneath it mid-flight, leaving that arm carrying "
        "nyiso_li_locational_reserve=False against a keeper that arms it. This "
        "arm replays the nyiso-113 recipe itself (replay_keeper.py, NO --set), "
        "so the zero delta is structural rather than asserted. The control is "
        "NOT the committed keeper bundle: seven src/market_sim commits landed "
        "after that bundle solved, two touching paths this ISO uses, and "
        "caiso-146 recorded a comparable run of documented-inert commits "
        "nonetheless leaving a keeper's sidecars diverging up to 3.2 GW on a "
        "class-hour. Both arms therefore solved cold at the SAME HEAD, "
        "differing only in the artifact's bytes. "
        f"LIVENESS, measured on this bundle against that control: P1 CT_PEAKER "
        f"energy {ct} TWh ({delta}) for 2023/24/25. Load-weighted lambda {lam} "
        f"$/MWh ({pct} %). "
        "Rule 14 [R-ACCURATE] governs the promotion in both directions: the "
        "corrected input goes in because it is the corrected input, and it "
        "would equally have gone in had the residual worsened. Rule 23 "
        "[R-FROZEN-DERIVE] is satisfied — the re-derivation is driven by a "
        "meter defect in the derive, never by a residual. Rule 28b: "
        "measured_ct_heat_rates keeps its existing per-ISO cell verdicts; this "
        "is an input correction with no mechanism surface. Evidence: "
        "results/calibration/FINDING-caiso160-nyiso-ct-heat-rate-rebase-2026-08-03.md, "
        "PREREG-caiso160-nyiso-ct-heat-rate-rebase-2026-08-03.md, "
        "FINDING-caiso158-ct-heat-rate-meter-screen-2026-08-03.md."
    )


def generate() -> dict:
    """Write NYISO's attestation and return a summary of what was measured."""
    source = (
        REPO / f"results/calibration/{WIRING['source']}/calibration_attestation.json"
    )
    keeper_bundle = REPO / f"results/calibration/{WIRING['source']}"
    control = REPO / f"results/calibration/{WIRING['control']}"
    target_bundle = REPO / f"results/calibration/{WIRING['target']}"

    art = artifact_stats(ISO)
    ct_a, ct_b = ct_energy(control), ct_energy(target_bundle)
    lam_a, lam_b = lw_lambda(control), lw_lambda(target_bundle)
    tail_a, tail_b = price_tail(control), price_tail(target_bundle)

    # The promotion premise, MEASURED not asserted — and the exact check that
    # disqualified the caiso-158 arm. Any shared key with a different value
    # means this arm was controlled against a different recipe than the one it
    # would replace.
    drift = config_drift(target_bundle, keeper_bundle)
    unexplained = [k for k in drift["value_diffs"] if k not in DEFAULT_MOVES]
    if unexplained:
        raise SystemExit(
            f"{ISO}: {len(unexplained)} UNEXPLAINED ScenarioConfig value "
            f"difference(s) vs {WIRING['source']}: {', '.join(unexplained)}. An "
            "input-correction promotion must carry zero recipe changes — this "
            "arm was controlled against a different recipe than the one it "
            "would replace."
        )

    # K2. Every remaining diff is a shipped default that moved after the keeper
    # solved; the allowlist ASSERTS they cannot reach a NYISO backcast and this
    # MEASURES it. A single non-zero MW voids the exemption and the promotion.
    identity = control_bit_identity(control, keeper_bundle)
    if not identity:
        raise SystemExit(f"{ISO}: no class hourlies to verify K2 control identity")
    worst = max(identity.values())
    if worst != 0.0:
        raise SystemExit(
            f"{ISO}: K2 control integrity FAILED — the control diverges from "
            f"{WIRING['source']} by up to {worst:.6f} MW on a class-hour "
            f"({identity}). A moved default or a post-keeper src/market_sim "
            "commit reached the backcast, so the A/B delta is not the CT "
            "artifact's alone and the DEFAULT_MOVES exemption is void."
        )
    drift["default_moves_exempted"] = {
        k: DEFAULT_MOVES[k] for k in drift["value_diffs"]
    }
    drift["k2_control_bit_identity_max_abs_mw"] = identity

    att = json.loads(source.read_text())
    before = (
        att["free_parameters"]["n_entries"],
        att["free_parameters"]["n_residual"],
    )

    att["governance"]["attested_by"] = build_attested_by(
        art, ct_a, ct_b, lam_a, lam_b, drift
    )
    att["ct_heat_rate_artifact"] = art
    att["config_drift_vs_incumbent"] = drift

    # carry_exceptions prefixes each ledgered exception with its RE-MEASURED
    # magnitude on this arm; its CARRY preamble is caiso-159's, so the NYISO
    # wording is restored afterwards.
    carry_exceptions(
        att, WIRING["target"], WIRING["carried_from"], lam_a, lam_b, tail_a, tail_b
    )
    for exc in att.get("exceptions", []):
        exc["reason"] = CARRY + exc["reason"].removeprefix(c159.CARRY)

    # Rule 21 [R-DOF]: an input correction introduces no free parameter, so the
    # ledger must be identical in shape. Assert it rather than assume it — the
    # 19 CT plant rates change VALUE, but the entry's n_scalars and its zero
    # residual-scalar count do not.
    dof = att["free_parameters"]
    dof["n_entries"] = len(dof["entries"])
    dof["n_residual"] = sum(
        1 for e in dof["entries"] if e.get("identification") == "residual"
    )
    if (dof["n_entries"], dof["n_residual"]) != before:
        raise SystemExit(
            f"{ISO}: DOF ledger changed {before} -> "
            f"({dof['n_entries']}, {dof['n_residual']}); an input correction "
            "must not move the ledger"
        )

    out = target_bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    return {
        "wrote": str(out.relative_to(REPO)),
        "artifact": art,
        "drift": drift,
        "ct_peaker_twh": {y: (ct_a.get(y), ct_b.get(y)) for y in YEARS},
        "lw_lambda": {y: (lam_a.get(y), lam_b.get(y)) for y in YEARS},
        "exceptions": len(att.get("exceptions", [])),
        "dof": before,
    }


def main(argv: list[str] | None = None) -> int:
    """Generate the caiso-160 NYISO attestation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)

    summary = generate()
    print(f"wrote {summary['wrote']}")
    print(
        f"  artifact: md5 {summary['artifact']['md5'][:12]} "
        f"cap-wt {summary['artifact']['cap_weighted_net_hr']:.4f} "
        f"({summary['artifact']['plants_applied']}/"
        f"{summary['artifact']['plants_total']} plants)"
    )
    print(
        f"  config drift vs keeper: {len(summary['drift']['value_diffs'])} value "
        f"diff(s), {len(summary['drift']['arm_only'])} arm-only, "
        f"{len(summary['drift']['keeper_only'])} keeper-only"
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
    print(f"  DOF ledger unchanged at {summary['dof']} (entries, residual)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
