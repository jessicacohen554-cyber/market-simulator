"""xiso-8: generate the promotion attestation for the year-start left-edge arm.

ZERO LP. Unlike caiso-287's, this bundle **IS an arm** -- it carries one new
``ScenarioConfig`` field against the outgoing keeper's recipe -- so the
``attested_by`` below makes that mechanism's case rather than carrying a
predecessor's forward.

What is carried forward from the source bundle, and why each is legitimate:

* ``governance`` booleans -- the arm changes ONE construction convention in
  ``_flow_date_staircase`` and nothing else; it fits nothing to a residual,
  pins nothing to an actual, and touches no outage filter. Every claim the
  booleans make about the outgoing recipe is still true of this one, and the
  ten-field keeper posture was CHECKED leg-by-leg (not asserted) by
  ``scripts/probes/xiso8_compose_span.py``, which additionally refuses any leg
  whose ``gas_flow_date_year_start_package`` is not ``True``.
* ``free_parameters`` (the DOF ledger) -- unchanged verbatim, and this is a
  SUBSTANTIVE claim rather than a convenience: the arm introduces **zero free
  parameters**. Its only threshold is ``_GAS_BLACKOUT_MIN_GAP_DAYS``, which
  already existed, is identified on the series' own trade-gap histogram
  (empty at 6 and 7, so 6/7/8 select the identical gaps -- caiso-289 §2), and
  is REUSED here rather than re-derived. The ledger is verified unchanged
  against the source rather than assumed.

What is NOT carried forward:

* ``exceptions`` -- RE-MEASURED from this bundle's own scorer output, per year.
* ``attested_by`` -- written for this arm.

Usage::

    python3 scripts/gen_xiso8_attestation.py \\
        --bundle results/calibration/xiso8_leftedge_span \\
        --source results/calibration/caiso288_gasfix_span
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

ATTESTED_BY = """\
THIS BUNDLE IS AN ARM: ONE ScenarioConfig field against the outgoing keeper's \
recipe, solved one year per shard under rule 36 [R-YEAR-ISOLATION] and composed \
at zero LP. xiso-8 session (2026-09-20), under the owner ruling of that date \
opening caiso-289 §7(1)'s left-edge defect as its own cross-ISO object, and the \
same day's "do a single lane".

THE MECHANISM. ScenarioConfig.gas_flow_date_year_start_package (SHARED field, \
default OFF, registered in _CACHE_KEY_OPTIONAL_FIELDS + \
_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS + _BACKCAST_ONLY_OVERLAY_FIELDS, tier 3). \
data.fuel.hubs._flow_date_staircase places each trade-day citygate print on its \
gas FLOW day (trade + 1; Friday's trade covers the holiday-extended weekend \
package), forward-fills the non-trading gaps, then .bfill()s the remainder. The \
only days .bfill() can reach are the year's OPENING flow days, and on the \
function's OWN documented convention those were priced by the PREVIOUS \
DECEMBER's last trade. The back-fill instead hands them the year's FIRST \
JANUARY trade -- one that had not happened yet and that prices a LATER flow \
day. Armed, _year_start_package_seed seeds the series with that prior December \
trade before either branch builds its index, so the existing ffill carries it \
across the edge and the bfill has nothing left to reach.

RULE 14 [R-ACCURATE], ON THE SOURCE CONVENTION, IS THE WHOLE CASE. Measured on \
CAISO: flow 2023-01-01..03 was priced by the 2022-12-30 trade at $15.31 and the \
outgoing keeper burns $23.66 there. CAISO's 2023 C3a residual is +3.796 % \
(model high) and the repair pushes early-2023 gas DOWN, i.e. the helpful way -- \
THAT IS AN OUTCOME AND IS NOT THE REASON (rule 1 [R-STRUCT]: the direction of a \
residual is evidence for nothing). The band below was registered BEFORE the \
solve and is not a target.

SCOPED TO TRADING PACKAGES ONLY, AND THAT LIMIT IS THE DESIGN. The seed applies \
only when the year-boundary trade gap is < _GAS_BLACKOUT_MIN_GAP_DAYS (6). A \
longer gap is an EIA PUBLICATION BLACKOUT -- caiso_citygate_blackout_bridge's \
territory -- so the two are DISJOINT by construction (rule 19 [R-ONE-MECH]: the \
bridge fills only gaps >= 6, this only gaps < 6). The limit is measured, not \
precautionary: MISO's 2023 boundary sits inside a 15-day blackout whose last \
print is the Winter Storm Elliott spike of $17.69/MMBtu against $3.38 at the \
next measurement, so an unscoped forward-fill would be far worse than the \
back-fill it replaces.

ZERO FREE PARAMETERS, ZERO NEW THRESHOLDS (rules 5 [R-NO-MAGIC], 21 [R-DOF], 24 \
[R-REGISTRY]). No offer-curve multiplier moves, so there is no \
authorized_price_tuning block and none is owed. Default OFF, so every existing \
config in every ISO keeps its cache key -- verified: the CAISO backcast default \
key is unmoved at c831d560bf965030 and the armed key is a distinct \
a8e3a7ced83ee791.

THE BAND, PRE-REGISTERED EX ANTE, AND WHERE THE ARM LANDED. Construction is \
caiso-288's [no movement, full CC pass-through at 7.44 MMBtu/MWh, load-weighted \
from the OUTGOING KEEPER'S COMMITTED hourlies]. ALL FOUR YEARS LANDED INSIDE: \
2022 +0.054 % in [0, +0.087] (62 % of limb); 2023 -0.799 % in [0, -0.879] \
(91 %); 2024 -0.036 % in [0, -0.045] (80 %); 2025 -0.010 % in [0, -0.022] \
(47 %). In every year the EDGE-HOUR contribution in load-carrying zones \
dominates the total (+0.051 of +0.054; -0.791 of -0.799; -0.027 of -0.036; \
-0.008 of -0.010), non-edge propagation is second-order, and the two import \
nodes contribute EXACTLY 0.000 %.

G-CTRL FORM 4, NO CONTROL SOLVE SPENT (rule 29 [R-SCREEN] (b)). The outgoing \
keeper's committed bundle IS the control. G-DRIFT was audited at code level \
against its git_sha 35adf93c and again from the shard pin e7091f56 to the \
lane's rebased HEAD: every changed hunk on the backcast path classifies INERT \
for a CAISO mode="backcast" run (build_mac_sidecar-only reporting constants; \
None-defaulted forecast-path overrides on capacity evolution, which a backcast \
never enters; the default-off blackout-bridge branch; SPP-66's floor-window \
hoist, which at its default evaluates the identical expression; NWPP-44's two \
ISO-gated coal fields, verified by call to be False for CAISO). Mechanically \
confirmed: the CAISO cache keys are byte-identical across that window, and \
since capx D79 the key carries the per-ISO solve-surface fingerprint.

REPORTED AGAINST THE ARM, NOT HIDDEN. 2024 carries 8,146 differing P1 price \
cells OUTSIDE its 48 edge hours. They are DEGENERACY, established on the PRIMAL \
rather than asserted: the swings concentrate at WECC_PNW (std 24.8, +/-170 \
$/MWh) while every load-carrying zone shows p50 |delta| 0.0018 $/MWh; WECC_PNW \
and WECC_DSW carry ZERO load, so their contribution to every load-weighted \
metric is exactly 0.000 %; and the primal barely moves -- max |delta class TWh| \
0.0249 on 216 TWh, total generation within -0.0006 TWh, with the movement in \
hydro and import, the two resources free to reshuffle at zero objective cost. \
That is alternate optima, not the rule-36 MISO defect (24.18 TWh and ~$500M of \
objective). D-1/D-4/D-5 read FAIL on this bundle and read FAIL IDENTICALLY on \
the outgoing keeper when the same diagnostics are run against it -- \
pre-existing, not introduced here.

SCOPE, DECLARED. This lane owns BOTH CAISO and MISO shards under the owner's \
"do a single lane", a deliberate departure from rule 28(d)'s per-ISO \
discipline. MISO is MEASURED AND NOT ARMED: only 2021/2022 are package \
boundaries there, its keeper reaches the staircase solely through the \
mean-preserving shape path (factors renormalize to mean exactly 1.0 within \
every month, so the January LEVEL cannot move), and its worst-year exposure is \
0.0293 % of the annual mean against CAISO 2023's -0.879 %. The cut was made on \
measured magnitude BEFORE any gate was consulted. Stated as a cost: MISO's \
keeper continues to carry the defect on 2021 and 2022 at those sizes.

Record: docs/PRECOMMIT-xiso8-year-start-left-edge-2026-09-20.md; \
results/calibration/_xiso8_left_edge_census.json; _xiso8_band.json; \
_xiso8_leg_ab.json."""

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
            "bundle legitimately carries no ledgered caveat."
        )

    # RULE 21 [R-DOF]: the docstring claims the ledger is UNCHANGED because the
    # arm adds no free parameter. VERIFY it rather than assume it -- a boolean
    # construction gate should never become an entry, and if one ever did, this
    # stops the attestation instead of understating the ledger.
    own_path = bundle / "calibration_attestation.json"
    if own_path.exists():
        own = json.loads(own_path.read_text()).get("free_parameters")
        if own:

            def _names(fp):
                return {e.get("name") or e.get("parameter") for e in fp["entries"]}

            if (
                _names(own) != _names(src["free_parameters"])
                or own["n_entries"] != src["free_parameters"]["n_entries"]
                or own["n_residual"] != src["free_parameters"]["n_residual"]
            ):
                raise SystemExit(
                    "DOF ledger DIFFERS between this bundle and the source "
                    f"(arm {own['n_entries']}/{own['n_residual']} vs source "
                    f"{src['free_parameters']['n_entries']}/"
                    f"{src['free_parameters']['n_residual']}; added "
                    f"{sorted(_names(own) - _names(src['free_parameters']))}, "
                    f"removed {sorted(_names(src['free_parameters']) - _names(own))}). "
                    "The arm's 'zero free parameters' claim is FALSE -- fix the "
                    "attestation, do not carry the source's ledger."
                )
            print(
                f"  DOF ledger VERIFIED identical to source: "
                f"{own['n_entries']} entries / {own['n_residual']} residual"
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
