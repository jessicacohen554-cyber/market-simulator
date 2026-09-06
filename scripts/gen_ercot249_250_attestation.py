"""Generate the ercot-249 / ercot-250 2022 VALIDATION TOUCHPOINT attestations.

Both arms are rule-22 ``[R-HOLDOUT]`` **validation-tier touchpoints on 2022**,
never keepers and never keeper candidates. Each is a REPLAY of a frozen,
already-attested ERCOT keeper recipe on a held-out year: **zero** parameters
changed, zero ScenarioConfig fields minted, zero mechanisms tested. The DOF
ledger is therefore the source keeper's own, carried over unchanged
(``n_entries`` / ``n_residual`` identical) — a replay cannot mint a degree of
freedom it does not set.

The attestation exists so the arms can be SCORED. Without it the C6 governance
gate reads UNATTESTED, which both forces NOT-YET and blocks guard (b) of the
C3c standing rule — scoring C3c FAIL on values that may be identical to the
keeper's own (the miso-200 vacuous-pass trap). It is NOT a certification that
either arm is promotable: rule 22 forecloses that for any held-out year, whose
number is model-SELECTION evidence and never a certified out-of-sample skill
number.

Usage:
    python3 scripts/gen_ercot249_250_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ARMS = {
    "ercot249_2022_touchpoint_forward": {
        "src": "ercot234_eastex_identity",
        "shorthand": "ercot-249",
        "config": "FORWARD config (2024-2025 half of the two-config keeper)",
    },
    "ercot250_2022_touchpoint_carveout": {
        "src": "ercot236_k33_clip",
        "shorthand": "ercot-250",
        "config": "2023 CARVE-OUT config (ercot_offer_swcap_clip + k_peak 33)",
    },
}

DISCLOSURE = (
    "THIS RUN IS A RULE-22 [R-HOLDOUT] VALIDATION-TIER TOUCHPOINT ON 2022 AND IS "
    "NOT A KEEPER OR A KEEPER CANDIDATE. ERCOT holds a 'complete' marker, which "
    "authorizes the validation ladder (2020-2022) to be solved, scored and "
    "registered; the locked test (2019 / H1-2026) is untouched and stays frozen "
    "for every ISO. (1) WHAT WAS RUN: the designated keeper recipe replayed "
    "VERBATIM on 2022 via --replay-bundle, which takes every flag from the source "
    "bundle's meta.json. No parameter was changed, no ScenarioConfig field minted, "
    "no mechanism armed, disarmed or tested, and no mechanism-matrix cell touched. "
    "The DOF ledger below is the source keeper's own, unchanged. (2) WHAT THE "
    "NUMBER IS: model-SELECTION evidence for the touchpoint loop (run the frozen "
    "recipe -> diagnose the OBJECT it surfaces -> re-train on 2023-2025 around "
    "that object -> re-test). Because the validation tier is iterated against, it "
    "is NEVER quotable as a certified out-of-sample skill number; only 2019, spent "
    "once at the end, is that. (3) NOTHING WAS FITTED TO 2022. No parameter is "
    "identified against this year; any repair the touchpoint motivates is derived "
    "in a later 2023-2025 session, which is the discipline that keeps the "
    "touchpoint honest. (4) KNOWN 2022 INPUT/RECIPE GAPS, stated at the gate and "
    "NOT patched in this session: ERCOT HSL 2022 is absent (owner manual upload "
    "only), so 2022 renewables ride the RENEWABLE_BOUND_FORECAST_UNCURTAILED "
    "construction and both ercot_gtc_limits_measured and "
    "ercot_wtx_curtailment_driver self-disable for the year; the *_from_year=2023 "
    "gates leave ercot_reserve_supply_cap, ercot_load_resource_reserve and "
    "ercot_storage_as_deployment UNARMED in 2022 (ercot_ecrs_requirement is "
    "correctly zero - ECRS launched June 2023); year-scoped SCED conduct tables "
    "carry 2023-2025 only, so the fast-start pool is inert, the cleared-share "
    "boundary pooled and the coal peak yearly level static (2022 SCED 60-day "
    "disclosures are past MIS retention and cannot be extended); and the storage "
    "AS product parquets are absent, reading zeros. These are recipe semantics and "
    "owner-side uploads, not this session's to change - arming them in 2022 is an "
    "owner recipe decision raised in the finding."
)


def build(arm_dir: str, spec: dict) -> None:
    src = REPO / "results/calibration" / spec["src"] / "calibration_attestation.json"
    dst = REPO / "results/calibration" / arm_dir / "calibration_attestation.json"
    d = json.loads(src.read_text())
    prior = d["governance"].get("attested_by", "")
    d["governance"]["attested_by"] = (
        f"{spec['shorthand']} 2022 VALIDATION TOUCHPOINT (2026-09-05), NOT A KEEPER "
        f"(rule 22 [R-HOLDOUT]): the {spec['config']} of the two-config ERCOT keeper "
        f"2026-09-05-ercot248-two-config-keeper, replayed VERBATIM on 2022 from the "
        f"committed bundle {spec['src']} via --replay-bundle --holdout-authorized. "
        "Zero parameters changed, zero fields minted, zero mechanisms tested; the "
        "DOF ledger is the source keeper's own and is carried over unchanged. Every "
        "lever still traces to a measured input, nothing is fit to a price residual "
        "and no output is pinned to actuals - the replay cannot do otherwise, since "
        "it sets nothing. Solved in-session, never on CI (CLAUDE.md GitHub Actions "
        "rule). Source keeper attestation preserved below in lineage. || LINEAGE: "
        + prior
    )
    d.setdefault("disclosures", {})[f"{spec['shorthand']}_2022_touchpoint"] = DISCLOSURE
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']}, "
        f"inherited from {spec['src']})"
    )


if __name__ == "__main__":
    for arm, spec in ARMS.items():
        if (REPO / "results/calibration" / arm).is_dir():
            build(arm, spec)
        else:
            print(f"skip {arm} (bundle not present yet)")
