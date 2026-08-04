"""Write the caiso-172 governance attestation for BOTH A/B arms.

caiso-172 replaces the LAST residual-identified member of
``constants.CAISO_TAC_ZONE_WEIGHTS`` — the ``PGE-TAC`` Path-15 split — with a
MEASURED value derived from published CAISO OASIS bytes
(``scripts/data/derive_caiso_path15_load_split.py``). This generator writes the
attestation both arms carry, and **fails closed** on every claim the finding
makes that a machine can check:

* the two arms' ``scenario_config`` must be IDENTICAL — the A/B delta is a
  ``constants.py`` table, not a config field, so any config difference means the
  A/B was not clean (the caiso-166 precedent, and the caiso-162 lesson);
* the arm's own weights must be the derived artifact's values, to 6 dp — so the
  attestation cannot claim "measured" over a hand-typed number;
* the DOF ledger must show the entry as ``measured`` with ``n_residual`` DOWN
  by exactly one from the incumbent keeper's 9;
* the incumbent keeper's ledgered exceptions are carried VERBATIM — this session
  creates no new caveat and spends no new ledger slot.

Usage::

    uv run python scripts/gen_caiso172_attestation.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.build_dof_ledger import build_ledger  # noqa: E402

KEEPER = REPO / "results/calibration/caiso166_measured_loss_zones"
CONTROL = REPO / "results/calibration/caiso172_control_pge_estimate"
ARM = REPO / "results/calibration/caiso172_measured_path15_split"
SPLIT_JSON = REPO / "data/raw/zone-specific-demand/CAISO/CAISO_path15_load_split.json"

#: The incumbent keeper's ledger position, which this session must not worsen.
KEEPER_N_ENTRIES, KEEPER_N_RESIDUAL = 11, 9

ATTESTED_ARM = (
    "caiso-172 (2026-08-04): the PG&E TAC-area load split across PATH 15 — "
    "CAISO_TAC_ZONE_WEIGHTS['PGE-TAC'], the LAST residual-identified member of "
    "that table (audit C-16, issue #1372) — moves from the 0.86/0.14 estimate "
    "of 'unverified provenance' to a MEASURED 0.883951/0.116049, derived by "
    "scripts/data/derive_caiso_path15_load_split.py from two PUBLISHED CAISO "
    "OASIS Atlas reports: ATL_LDF's per-pnode load distribution factors inside "
    "DLAP_PGAE-APND (1,668 load pnodes summing to exactly 100.000 — CAISO's own "
    "weighting for distributing PG&E LAP load onto nodes) joined by substation "
    "to ATL_PNODE_MAP's authoritative TH_NP15_GEN / TH_ZP26_GEN membership, "
    "which IS the Path-15 geography as CAISO defines it for its own hubs. "
    "RULE 14 [R-ACCURATE]: the status quo was NOT a rival measurement — it was "
    "an assumed ratio, and the misalignment exception the constants comment "
    "invoked ('no TAC boundary exists at Path 15 to measure the split "
    "directly') is TRUE AND IRRELEVANT, because that exception licenses an "
    "estimate only where the real data is misaligned to our representation, "
    "and ATL_PNODE_MAP is the very boundary the model's NP15<->ZP26 link "
    "represents. RULE 23 [R-FROZEN-DERIVE]: the derive re-runs only when its "
    "SOURCE bytes change; it reads no model output and no residual, and the "
    "source snapshots are committed under data/raw/caiso-atlas/ so it runs "
    "with no network. ZERO free parameters and ZERO ScenarioConfig fields — "
    "the delta is a constants.py TABLE, and this generator FAILS on any "
    "scenario_config difference against the same-HEAD control. RULE 13 "
    "[R-MEASURED] admissibility: the quantity regenerates for a forward year "
    "from published forward bytes and responds to changed conditions. "
    "RECONCILIATION, NOT IDENTITY: an LDF is a *typical* distribution factor, "
    "so this is a measured STATIC scalar replacing an assumed static scalar — "
    "the same KIND of object, identified instead of guessed; it is NOT an "
    "hourly NP15/ZP26 load series, and no source publishes one (five walled "
    "routes, re-checkable in scripts/probes/_caiso172_subtac_load_survey.py). "
    "The pre-registration PRECHECK-caiso172-path15-load-split-2026-08-04.md "
    "was pushed BEFORE any solve and fixes the rule-14 disposition ahead of "
    "the numbers: the measured input is KEPT REGARDLESS of what it does to the "
    "backcast, because rule 14 makes a worse fit a DISCOVERED BUG, not a "
    "reason to revert. The DOF ledger consequence is a CLOSURE (rule 20 "
    "[R-DOF]): this entry moves residual -> measured and n_residual 9 -> 8."
)

ATTESTED_CONTROL = (
    "caiso-172 Arm A CONTROL (2026-08-04): a SAME-HEAD, freshly solved baseline "
    "carrying the INCUMBENT residual-identified CAISO_TAC_ZONE_WEIGHTS"
    "['PGE-TAC'] = {NP15 0.86, ZP26 0.14}, so that the measured arm's delta is "
    "attributable to the weight change and to nothing else. It reproduces the "
    "incumbent keeper 2026-08-04-caiso-166-measured-dlap BIT-IDENTICALLY "
    "(max |dprice| = 0.000000 and max |ddemand| = 0.000000 over all P1 "
    "zone-hours of 2023, 2024 and 2025), which is what licenses reading the "
    "A/B delta as the mechanism's own effect. REGISTERED AS A CONTROL, NOT A "
    "CANDIDATE — it is not proposed as a keeper and its ledger still carries "
    "the PGE-TAC entry as residual."
)


def _cfg(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    )


def main() -> int:
    keeper_att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    exceptions = keeper_att["exceptions"]

    # --- fail-closed check 1: the arms' ScenarioConfigs must be identical -----
    c_cfg, a_cfg = _cfg(CONTROL), _cfg(ARM)
    diff = {k for k in set(c_cfg) | set(a_cfg) if c_cfg.get(k) != a_cfg.get(k)}
    if diff:
        raise SystemExit(
            f"A/B NOT CLEAN: scenario_config differs between arms on {sorted(diff)}. "
            "The caiso-172 delta is a constants.py table; any config difference "
            "means the arms are not comparable."
        )

    # --- fail-closed check 2: the arm carries the DERIVED value --------------
    derived = json.loads(SPLIT_JSON.read_text())
    want = {
        "NP15": round(derived["np15_weight"], 6),
        "ZP26": round(derived["zp26_weight"], 6),
    }
    from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS

    have = {k: round(v, 6) for k, v in CAISO_TAC_ZONE_WEIGHTS["PGE-TAC"].items()}
    if have != want:
        raise SystemExit(
            f"constants.py PGE-TAC {have} != derived artifact {want} — the "
            "attestation may not claim 'measured' over a hand-typed number."
        )

    for bundle, attested in ((CONTROL, ATTESTED_CONTROL), (ARM, ATTESTED_ARM)):
        ledger = build_ledger(bundle, "CAISO")
        if bundle is CONTROL:
            # build_ledger reads the CURRENT constants.py, but the control was
            # SOLVED with the incumbent estimate — the weights are a constants
            # table, so the bundle's run_config does not record them and the
            # ledger cannot infer them. Restore the entry the control actually
            # ran, so its attestation describes its own solve rather than the
            # arm's. (The control is a baseline, never a keeper candidate.)
            ledger = json.loads(json.dumps(ledger))
            for e in ledger["entries"]:
                if e["name"] == "CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']":
                    e["identification"] = "residual"
                    e["value"] = {"NP15": 0.86, "ZP26": 0.14}
                    e["source"] = (
                        "PG&E TAC load split across Path 15 — the INCUMBENT "
                        "estimate of unverified provenance (audit C-16), which "
                        "this CONTROL arm was solved with. Superseded in Arm B "
                        "by the caiso-172 measurement; see that bundle."
                    )
                    e["root_cause"] = (
                        "audit C-16 / issue #1372 — CLOSED by caiso-172 in Arm B "
                        "(measured from OASIS ATL_LDF x ATL_PNODE_MAP); this "
                        "control arm predates the substitution by construction."
                    )
            ledger["n_residual"] = sum(
                1 for e in ledger["entries"] if e["identification"] == "residual"
            )
        att = {
            "schema": "calibration-attestation/v1",
            "governance": {
                "levers_trace_to_measured_input": True,
                "no_fit_to_price_residuals": True,
                "no_pinning_to_actuals": True,
                "outage_filter_exogenous_net_load": True,
                "attested_by": attested,
                "note": keeper_att["governance"].get("note", ""),
            },
            "exceptions": exceptions,
            "free_parameters": ledger,
        }
        (bundle / "calibration_attestation.json").write_text(
            json.dumps(att, indent=2) + "\n"
        )
        print(
            f"wrote {bundle.name}/calibration_attestation.json  "
            f"n_entries={ledger['n_entries']} n_residual={ledger['n_residual']}"
        )

    # --- fail-closed check 3: the ARM's ledger must show the closure ---------
    arm_ledger = build_ledger(ARM, "CAISO")
    entry = next(
        e
        for e in arm_ledger["entries"]
        if e["name"] == "CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']"
    )
    if entry["identification"] != "measured":
        raise SystemExit(
            f"PGE-TAC entry is {entry['identification']!r}, expected 'measured'"
        )
    if arm_ledger["n_residual"] != KEEPER_N_RESIDUAL - 1:
        raise SystemExit(
            f"n_residual {arm_ledger['n_residual']} != {KEEPER_N_RESIDUAL - 1} "
            "— the closure must reduce the residual count by exactly one"
        )
    if arm_ledger["n_entries"] != KEEPER_N_ENTRIES:
        raise SystemExit(
            f"n_entries {arm_ledger['n_entries']} != {KEEPER_N_ENTRIES} — a closure "
            "re-identifies an entry, it does not add or remove one"
        )
    print(
        f"OK: DOF closure verified — PGE-TAC measured, "
        f"n_entries {arm_ledger['n_entries']}, n_residual {arm_ledger['n_residual']} "
        f"(was {KEEPER_N_RESIDUAL})"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
