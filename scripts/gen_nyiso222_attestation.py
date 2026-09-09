"""Write the nyiso-222 bundle's attestation — the owner-directed +5% offer-band move.

The bundle needs a C6 attestation (an unattested C6 makes C3c FAIL outright
instead of reclassifying to a ledgered CAVEAT), and this arm additionally needs
the rule 1 ``[R-STRUCT]`` carve-out declaration: it uses the AUTHORIZED
PRICE-TUNING CHANNEL, so ``governance.authorized_price_tuning`` must be present
and well-formed or ``calibration_verdict.score_governance`` fails C6 outright
(``AUTHORIZED_TUNING_FIELDS``).

Pattern carried from ``gen_caiso267_attestation.py`` (E10: generated AT the
promotion, never typed): the incumbent keeper's committed attestation is the
base, ``attested_by`` is re-stamped with THIS bundle's narrative, and the
``value.applied_to`` map is READ BACK OFF THE OVERRIDE FILE the solve consumed
rather than restated by hand, so the declaration cannot drift from what was
actually applied. ``free_parameters`` is rebuilt afterwards by
``scripts/build_dof_ledger.py`` and its ``offer_curve_by_group`` entry re-keyed
to the ruling (rule 21 ``[R-DOF]`` / rule 20's R-AY cross-reference).

Usage::

    PYTHONPATH=.:src uv run python scripts/gen_nyiso222_attestation.py \
        --bundle results/calibration/nyiso222_offer_plus5
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/nyiso_fuelvintage_A"
CURVE = REPO / "results/calibration/nyiso222_offer_curve_plus5.json"
SCALE = 1.05

_ATTEST = (
    "THIS BUNDLE IS THE ARM: the nyiso-221-fuelvintage-span keeper recipe with "
    "the FOUR authorized offer_curve_by_group band multipliers scaled by 1.05, "
    "and NOTHING ELSE. Session nyiso-222 (2026-09-09). OWNER INSTRUCTION, "
    "verbatim: 'Ok offer curve should be moved +5%'. THIS IS THE RULE 1 "
    "[R-STRUCT] / RULE 13 [R-MEASURED] AUTHORIZED PRICE-TUNING CHANNEL (owner "
    "amendment 2026-09-05) and it is DECLARED as such in "
    "governance.authorized_price_tuning below — it is NOT a rule 14 "
    "[R-ACCURATE] measured-input repair and is never described as one. "
    "PRE-REGISTERED BEFORE THE FIRST LP in "
    "docs/PRECOMMIT-nyiso222-offer-curve-plus5-2026-09-09.md, which carries the "
    "channel, the scope, the zero-LP confinement proof, the G-DRIFT audit and "
    "the numeric predictions — including the explicit pre-solve call that 2024 "
    "C3a would flip PASS -> FAIL if the marginal-hour pass-through exceeded "
    "88.8%. NO CONTROL SOLVE was spent (rule 29(b) [R-SCREEN]): G-DRIFT from "
    "the keeper's git_sha da2e7076 to HEAD found exactly two changed solve-path "
    "hunks and classified BOTH INERT — constants.py is comment-only (filtering "
    "the diff to non-comment changed lines returns zero lines, and the edit is "
    "inside NEISO's NUCLEAR_MONTHLY_CF_BY_YEAR sub-dict, which a NYISO solve "
    "never reads), and the solve_surface_declared.py line is a frozen-drop "
    "declaration read at exactly one site (solve_surface.py:330) whose "
    "consumers are cache_key / persist / export — it selects a result-reuse "
    "directory, never the LP matrix — so G-CTRL form 4 is valid and the "
    "COMMITTED keeper is the control."
)

_NOTE = (
    "REPORTED AT THE GATE, not absorbed. (a) The direction of this move FIGHTS "
    "TWO OF THE THREE SCORED YEARS and that was stated before the solve: the "
    "keeper is already ABOVE actual on C3a in 2023 (+4.3%) and 2024 (+5.3%) and "
    "below only in 2025 (-7.3%), so a uniform +5% necessarily makes 2023 and "
    "2024 worse and 2025 better. (b) The +5% is the OWNER'S EX ANTE VALUE and "
    "was NEVER SWEPT: no factor was tried, compared or resized against any "
    "gate, in this session or before it. Condition (c) of the rule 1 carve-out "
    "forbids selecting a multiplier because it makes a criterion pass, so the "
    "value is not re-tuned in either direction whatever the scorecard says — a "
    "worse gate is reported, not repaired. There is exactly one arm. (c) The "
    "channel's REACH IS LIMITED and the limit is declared rather than hidden: "
    "ST_CHP is router-valid and NYISO genuinely dispatches it (1.447 TWh model "
    "in 2025) but has NO entry in the keeper's resolved offer_curve_by_group, "
    "so there is no registered band to scale; adding one would be a NEW "
    "parameter rather than a move of an existing one, which rule 1(a) forbids. "
    "Imports, hydro and nuclear likewise carry no offer band, which is why the "
    "realized mean-price pass-through is strictly below the nominal 5%."
)

_EXCLUDED = (
    "every phys_* key (phys_committed, phys_econ_low, phys_econ_high, "
    "phys_peak — MEASURED PHYSICS, never a tuning surface) and the structural "
    "shares econ_low_share and pct_peaking. The three *_INTERMEDIATE classes "
    "(CC_INTERMEDIATE, CT_INTERMEDIATE, ST_GAS_INTERMEDIATE) are excluded "
    "because the offer-curve router does not read them AND they are dead for "
    "NYISO regardless — the keeper carries cc_intermediate_split=False, "
    "ct_intermediate_split=False and st_gas_intermediate=False, so excluding "
    "them costs nothing. ST_CHP is excluded because the keeper's resolved "
    "curve has no entry for it, so adding one would be a new parameter rather "
    "than a move of an existing one (rule 1(a))."
)

_IDENTIFICATION = (
    "NONE — and that is the point. 1.05 is an owner-supplied ex-ante constant, "
    "not a value identified against anything. No gate, no residual and no "
    "criterion was consulted to choose it, in this session or before it. Under "
    "rule 21 [R-DOF] and rule 20's R-AY cross-reference the resulting free "
    "parameter's identification source is THE RULING ITSELF — 'price residual, "
    "authorized channel (rules 1/13 amendment 2026-09-05)' — not a measured "
    "input; it is reported at full magnitude on the determination basis, and "
    "its presence does not by itself make the residual it closes an open "
    "root-cause issue."
)

_DISCLOSURE = (
    "AGAINST INTEREST: this run moves NYISO's mean price UP in all three "
    "scored years, and in two of them (2023, 2024) the keeper was ALREADY "
    "ABOVE actual — so on C3a the move is expected to be harmful in 2/3 years "
    "and helpful in 1/3. That was computed and written down BEFORE the solve "
    "(PRECOMMIT §5.1), together with the exact pass-through fraction (88.8%) "
    "beyond which 2024 C3a fails. It is recorded so a later reader judges the "
    "owner's ruling against a stated prior rather than against a silence. "
    "Rule 25 [R-ISO-SCOPE]: the move is a CLI override on a NYISO invocation "
    "and touches no shared default, no constants.py value and no other ISO's "
    "curve."
)


def build(bundle: Path) -> dict:
    """Return the arm's attestation, based on the incumbent keeper's.

    ``years_held`` is derived from THIS bundle's own ``meta.json``, never
    hardcoded: ``calibration_verdict._authorized_tuning_finding`` requires it to
    equal the bundle's scored years exactly, so the train-span bundle declares
    [2023, 2024, 2025] and the 2022 validation touchpoint declares [2022]. The
    rule 1 (b) "ONE config across every scored year" duty is satisfied by the
    override file being byte-identical across both, which ``declaration`` below
    states in words and the shared ``CURVE`` path proves.
    """
    att = json.loads((KEEPER / "calibration_attestation.json").read_text())
    years = sorted(json.loads((bundle / "meta.json").read_text())["years"])
    override = json.loads(CURVE.read_text())
    base = json.loads((KEEPER / "run_config.json").read_text())
    base_curve = base["scenario_config"]["offer_curve_by_group"]

    # Read the applied map BACK OFF the file the solve consumed, and re-verify
    # every ratio here rather than trusting the generator that wrote it.
    applied = {c: sorted(bands) for c, bands in sorted(override.items())}
    bad = [
        f"{c}.{b}"
        for c, bands in override.items()
        for b, v in bands.items()
        if abs(v / base_curve[c][b] - SCALE) > 1e-9
    ]
    if bad:
        raise SystemExit(f"ratio drift vs the keeper curve: {bad}")

    gov = att["governance"]
    gov["attested_by"] = _ATTEST
    gov["note"] = _NOTE
    gov["authorized_price_tuning"] = {
        "channel": "offer_curve_by_group",
        "ruling": (
            "Owner instruction 2026-09-09, verbatim: 'Ok offer curve should be "
            "moved +5%'. Authorized by the rules 1 [R-STRUCT] / 13 "
            "[R-MEASURED] carve-out of 2026-09-05."
        ),
        "value": {
            "scalar": SCALE,
            "move_pct": +5.0,
            "bands": sum(len(b) for b in override.values()),
            "applied_to": applied,
            "excluded": _EXCLUDED,
            "file": str(CURVE.relative_to(REPO)),
        },
        "years_held": years,
        "set_ex_ante": True,
        "not_swept": True,
        "identification": _IDENTIFICATION,
        "prereg": (
            "docs/PRECOMMIT-nyiso222-offer-curve-plus5-2026-09-09.md "
            "(pushed BEFORE the first LP)"
            + (
                " + docs/ADDENDUM-nyiso222-2022-touchpoint-2026-09-09.md "
                "(pushed BEFORE the 2022 solve)"
                if years == [2022]
                else ""
            )
        ),
        "declaration": (
            "ONE CONFIG, held across 2022-2025. This bundle's years_held names "
            f"its own scored years ({years}) because that is what the C6 check "
            "compares against; the SAME override file "
            f"({CURVE.relative_to(REPO)}) is consumed byte-identically by the "
            "train-span bundle (2023-2025) and by the 2022 validation "
            "touchpoint, so rule 1 condition (b) holds across the pair. 2022 is "
            "an ITERABLE validation-tier touchpoint under rule 22: it is "
            "model-selection evidence, never a certified out-of-sample skill "
            "number, it never downgrades NYISO (rule 30(c)), and NOTHING is "
            "fitted to it -- the 1.05 was fixed before 2022 was solved and is "
            "not resized by whatever 2022 returns."
        ),
        "disclosure": _DISCLOSURE,
    }
    return att


_LEDGER_NOTE = (
    "RE-KEYED BY nyiso-222 (2026-09-09) UNDER RULE 21 [R-DOF] AND RULE 20's "
    "R-AY CROSS-REFERENCE. This row now carries a value TUNED ON PRICE through "
    "the rule 1 [R-STRUCT] / rule 13 [R-MEASURED] AUTHORIZED CHANNEL: the four "
    "band multipliers (committed, econ_low, econ_high, peak) on the 10 "
    "router-valid classes were multiplied by 1.05 on the owner's instruction of "
    "2026-09-09 ('Ok offer curve should be moved +5%'). ITS IDENTIFICATION "
    "SOURCE IS THEREFORE THE RULING, NOT A MEASURED INPUT: 'price residual, "
    "authorized channel (rules 1/13 amendment 2026-09-05)'. The generator's "
    "identification: 'residual' is kept because it remains literally true and "
    "the row's scalar census is unchanged (the same 88 scalars, 40 of them "
    "moved), but the SOURCE of the move is the ruling and it is reported at "
    "full magnitude on the determination basis. Per R-AY the presence of this "
    "authorized-channel value does NOT by itself make the residual it closes an "
    "open root-cause issue, and no gate moves on account of it; every OTHER "
    "tuned value in this ledger still does. The value was set ex ante and NEVER "
    "SWEPT — see governance.authorized_price_tuning and "
    "docs/PRECOMMIT-nyiso222-offer-curve-plus5-2026-09-09.md."
)


def rekey_ledger(bundle: Path) -> None:
    """Stamp the rule-21 note onto the rebuilt offer_curve_by_group row.

    Run AFTER ``scripts/build_dof_ledger.py``, whose ``_carry_hand_notes``
    then preserves this text across any later rebuild.
    """
    path = bundle / "calibration_attestation.json"
    att = json.loads(path.read_text())
    rows = [
        e
        for e in att.get("free_parameters", {}).get("entries", [])
        if e.get("name") == "offer_curve_by_group"
    ]
    if not rows:
        raise SystemExit(
            "no offer_curve_by_group row in the ledger — run build_dof_ledger first"
        )
    rows[0]["note"] = _LEDGER_NOTE
    path.write_text(json.dumps(att, indent=2) + "\n")
    print(f"  ledger row re-keyed to the ruling (rule 21) in {path}")


def main() -> None:
    """CLI: write the arm bundle's attestation, or re-key its rebuilt ledger."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument(
        "--rekey-ledger",
        action="store_true",
        help="stamp the rule-21 note onto the rebuilt DOF row (post build_dof_ledger)",
    )
    args = ap.parse_args()
    if args.rekey_ledger:
        rekey_ledger(args.bundle)
        return
    att = build(args.bundle)
    out = args.bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=1) + "\n")
    dec = att["governance"]["authorized_price_tuning"]
    print(f"wrote {out}")
    print(
        f"  authorized_price_tuning: {dec['channel']} x {dec['value']['scalar']} "
        f"over {dec['value']['bands']} bands / {len(dec['value']['applied_to'])} "
        f"classes, years_held={dec['years_held']}"
    )


if __name__ == "__main__":
    main()
