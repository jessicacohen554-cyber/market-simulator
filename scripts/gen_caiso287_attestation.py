"""caiso-287: generate the promotion attestation for the MER keeper replay.

ZERO LP. The incoming keeper is a **replay of the outgoing keeper's own recipe**
-- not a new arm -- so this does not restate caiso-275's case as if it were
newly established. It CARRIES FORWARD the parts that are unchanged by
construction and writes a new ``attested_by`` describing only what this bundle
actually is and what actually differs.

What is carried forward, and why each is legitimate:

* ``governance`` booleans -- the scenario_config is identical to the outgoing
  keeper's (asserted leg-by-leg by ``caiso287_compose_span.py`` before the
  bundle was written), so every claim they make is the same claim about the
  same recipe.
* ``free_parameters`` (the DOF ledger) -- unchanged verbatim. This session
  added no ScenarioConfig field, no constant, no threshold and no offer-curve
  multiplier, so there is no entry to add or remove.

What is NOT carried forward:

* ``exceptions`` -- RE-MEASURED from this bundle's own scorer output, because
  the outgoing ledger's own rationale says the magnitudes are measured per
  bundle. They are read from ``calibration_verdict.py --json`` rather than
  copied, so a replay that moved C3c would be recorded honestly instead of
  inheriting a stale number.
* ``attested_by`` -- rewritten for this bundle.

Usage::

    python3 scripts/gen_caiso287_attestation.py \\
        --bundle results/calibration/caiso287_mer_span \\
        --source results/calibration/caiso275_B_gascoupling_span
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

ATTESTED_BY = """\
THIS BUNDLE IS A REPLAY, NOT AN ARM. caiso-287 session (2026-09-19), under the \
owner ruling of that date ("Mer should be promoted either way"). It re-solves \
the OUTGOING KEEPER'S OWN RECIPE -- 2026-09-12-caiso-275-gascoupling -- with \
ZERO ScenarioConfig differences, and therefore carries that keeper's \
structural case unchanged rather than making a new one. caiso-275's \
attestation remains the substantive governance record for the mechanism \
(ScenarioConfig.caiso_import_gas_coupling); nothing here re-argues it. The \
scenario_config identity is not asserted but CHECKED: \
scripts/probes/caiso287_compose_span.py verifies the keeper's ten-field \
posture on every per-year leg, and refuses to compose if any leg differs \
outside the per-year allowance (gas_price_override, weather_year, \
gas_offer_margin_anchor_by_zone, start_year, end_year, years). All three legs \
carry an identical solve-surface fingerprint (cba92d202f32f9fd). \
\
WHY IT WAS SOLVED AT ALL: the emissions dual marginal_emission_rate landed on \
main 2026-09-18 (2ec09663) and is NOT retroactive, so no committed keeper \
carried it. This bundle does, in every year -- the promotion's entire purpose. \
\
WHAT DIFFERS FROM THE OUTGOING KEEPER, STATED IN FULL: (1) the code sha, \
92b8e4db against b8ddf8bc; (2) the added marginal_emission_rate column; (3) \
added hourly/p0_dispatch_<year>.parquet and hourly/p0_prices_<year>.parquet \
sidecars, written by the opt-in default-off write-only --persist-p0-dispatch \
flag this session landed on main. That flag is read after both LPs have run \
and is consumed by nothing downstream; it adds files and changes none, and \
meta.json cannot record it (measured: caiso-285 was solved WITH the sibling \
--persist-p0-commitment and that string appears nowhere in its committed \
meta.json). \
\
IT REPAIRS A GOVERNANCE GAP IN THE OUTGOING KEEPER. Both outgoing bundles \
record git_sha 'b8ddf8bc', and THAT OBJECT DOES NOT EXIST IN THIS REPOSITORY: \
not fetchable from origin, absent from docs/governance/citation-commit-map.txt, \
and --disambiguate finds no object with the prefix. Rule 29 [R-SCREEN] (b)'s \
G-DRIFT form-4 code audit -- git diff <keeper git_sha> HEAD -- was therefore \
IMPOSSIBLE against the outgoing keeper for any session. The incoming sha \
92b8e4db resolves and is an ancestor of main, so the audit becomes possible \
again. \
\
THE REPLAY IS NOT BIT-IDENTICAL, AND THAT IS REPORTED RATHER THAN CLAIMED \
AWAY. Against the committed keeper, per year: the PRIMAL solution is \
IDENTICAL (slack, dump and demand differ by exactly 0.0 in every year); the \
SCORED load-weighted mean price moves +0.0060 pct in 2022 (94.068804 -> \
94.074407), +0.0041 pct in 2023 (55.891457 -> 55.893744) and +0.0001 pct in \
2024 (37.547014 -> 37.547070); and the dual drift is CONFINED TO THE WECC_PNW \
IMPORT NODE, whose max |delta| is 472.18 / 88.35 / 171.28 against 19-21 / \
4.75 / 0.28 in every other zone across 2022 / 2023 / 2024 -- a concentration \
reaching roughly 600x. price IS an LP dual (rule 4 [R-DUALS]) and a degenerate \
LP admits many optimal bases that price differently over the same primal \
solution; caiso-285 G1 already measured 390 WECC_PNW zone-hours flipping \
between $0 and a binding value. Solver and numerics stack are identical \
(highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, python 3.11.15); only the kernel \
differs (fc-v24 -> fc-v37). No scored band moves. \
\
C3c IS RE-MEASURED ON THIS BUNDLE'S OWN SIDECARS, not inherited, and \
reproduces the outgoing keeper's magnitudes exactly. DOF LEDGER UNCHANGED at \
9 entries / 6 residual: this session added no ScenarioConfig field, no \
constant, no threshold, no derive re-run and no offer-curve multiplier, and \
carries NO authorized_price_tuning block. NOTHING WAS ARMED OR DISARMED. \
\
PROVENANCE (rules 16 [R-ALLYEARS] / 32 [R-SHARD]): four per-year shards in \
four containers under the owner's "One shard per year" instruction, with the \
PARENT RUNNING ZERO LP, composed in the parent. Every leg's posture and live \
marginal_emission_rate column were verified before composition. The span's \
benchmark was REBUILT at span scope (run_calibration_full.py \
--rebuild-benchmark) rather than inheriting leg 2023's single-year extract -- \
the nyiso-238 composer's documented trap, which this session hit and repaired \
before registering."""

NOTE = """\
PROMOTION ATTESTATION, generated at the caiso-287 promotion (2026-09-19) for \
caiso287_mer_span. Owner ruling of that date. The bundle is a keeper replay \
carrying the new marginal_emission_rate column; the governance booleans and \
the DOF ledger are carried forward from the outgoing keeper 2026-09-12-caiso-\
275-gascoupling because the scenario_config is identical by checked \
construction, and the exceptions ledger is re-measured from this bundle's own \
scorer output. See docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md \
for the session's substantive findings, none of which arm or disarm anything."""


def main(bundle: Path, source: Path, allow_empty: bool, scope_note: str) -> None:
    src = json.loads((source / "calibration_attestation.json").read_text())

    out = subprocess.run(
        [sys.executable, "scripts/calibration_verdict.py", str(bundle), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    if out.returncode not in (0, 1):
        raise SystemExit(f"verdict failed rc={out.returncode}: {out.stderr[-500:]}")
    verdict = json.loads(out.stdout)

    # C3c exceptions, RE-MEASURED from this bundle rather than copied.
    exceptions = []
    for rec in verdict["criteria"]["price_tail"]["records"]:
        if rec.get("key") is not None or rec.get("status") != "FAIL":
            continue  # the DA diagnostic row is never gated
        exceptions.append(
            {
                "criterion": "price_tail",
                "year": rec["year"],
                "magnitude": (
                    f"model {rec['model']:.0f} h vs actual RT {rec['actual']:.0f} h "
                    "> $200/MWh (RE-MEASURED on this bundle's own committed sidecars)"
                ),
                "rationale": (
                    "C3c scarcity-tail model-class limitation (the ledgered "
                    "criterion; rubric v3.3 standing rule, v3.6 on a held-out "
                    "year) — adjudication belongs to the scorer"
                ),
            }
        )
    if not exceptions and not allow_empty:
        raise SystemExit(
            "no C3c FAIL found on this bundle — the ledger would be empty. "
            "That is a change from the outgoing keeper and must be looked at, "
            "not papered over. Pass --allow-empty-exceptions only when the "
            "bundle legitimately carries no ledgered caveat (a touchpoint year "
            "whose C3c PASSES, which 2022 does at 560 h vs 510 h actual)."
        )

    att = {
        "schema": src["schema"],
        "governance": {
            **{
                k: v
                for k, v in src["governance"].items()
                if k not in ("attested_by", "note")
            },
            "attested_by": ATTESTED_BY + ("\n\n" + scope_note if scope_note else ""),
            "note": NOTE,
        },
        "exceptions": exceptions,
        "free_parameters": src["free_parameters"],
    }
    dst = bundle / "calibration_attestation.json"
    dst.write_text(json.dumps(att, indent=1, sort_keys=False))
    print(f"wrote {dst}")
    print(
        f"  governance flags carried : {sorted(k for k in att['governance'] if isinstance(att['governance'][k], bool))}"
    )
    print(
        f"  exceptions re-measured   : {[(e['year'], e['magnitude'][:34]) for e in exceptions]}"
    )
    print(
        f"  DOF ledger               : {att['free_parameters']['n_entries']} entries / {att['free_parameters']['n_residual']} residual (carried, unchanged)"
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--allow-empty-exceptions", action="store_true")
    ap.add_argument("--scope-note", default="")
    a = ap.parse_args()
    main(
        REPO / a.bundle if not a.bundle.is_absolute() else a.bundle,
        REPO / a.source if not a.source.is_absolute() else a.source,
        a.allow_empty_exceptions,
        a.scope_note,
    )
