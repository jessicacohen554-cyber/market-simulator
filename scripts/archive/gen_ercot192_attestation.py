"""Write the ercot-192 A/B pair's ``calibration_attestation.json`` files.

Derived from the run191 keeper's attestation, which is the correct base because
the ercot-192 arm is a **single measured-level delta on that recipe** and adds
**ZERO FITTED scalars** — so the DOF ledger is carried and *extended*, never
re-fitted, which is itself the G-DOF evidence.

Two things are written on top of the keeper's ledger:

1. **The three margin-constant DOF entries card B filed and did not act on.**
   ``COAL_OFFER_MARGIN_LEVEL_BY_ISO`` (ERCOT-137, limb A),
   ``CC_COMMITTED_OFFER_LEVEL_BY_ISO`` (ERCOT-139, limb B) and
   ``COAL_PEAK_OFFER_LEVEL_BY_ISO`` + ``COAL_PEAK_OFFER_GAS_HR_BY_ISO``
   (ERCOT-140, limb C) are armed on the keeper and carry **no dedicated ledger
   entries**. Zero fitted scalars each, so this is bookkeeping rather than
   hidden freedom — but rule 23 ``[R-DOF]`` says *every* free parameter is
   listed with its identification source, and an armed identification constant
   that is absent from the ledger is exactly what the rule exists to surface.
   Card B: *"the next ERCOT keeper-promoting session should add them and carry
   limb B's verification into that ledger."* **This is written to BOTH arms**,
   because it is true of both and is owed independently of this lane's outcome.

2. **The arm's own entry**, ``coal_peak_offer_yearly_level`` — the year-keyed
   2023 level, on the arm only.

Everything else — ``governance`` (bar ``attested_by``) and the C3c
``exceptions`` carry — follows the ercot-188/191 pattern: the tail magnitudes
are RE-MEASURED on each bundle's own ``hourly/system_<year>.parquet`` and
reported at full magnitude, never re-scored.

Usage::

    python scripts/gen_ercot192_attestation.py \
        --base results/calibration/ercot192_ctl_A \
        --arm  results/calibration/ercot192_arm_B
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
ACTUAL_TAIL = {2023: 181, 2024: 53, 2025: 31}

_CONTROL_ATTEST = (
    "ercot-192 2026-08-12 — the A/B CONTROL: a same-HEAD byte-faithful replay "
    "of the 2026-08-12-run191-dam-deriver-regate keeper recipe "
    "(scripts/replay_keeper.py off the committed meta.json — the sanctioned "
    "recipe channel) with the ercot-192 gate at its DEFAULT "
    "(coal_peak_offer_yearly_level=false), i.e. the coal `_peak` tranche still "
    "priced at the static COAL_PEAK_OFFER_LEVEL_BY_ISO 35.1989 in every year. "
    "It exists because the ERCOT keeper is known not to reproduce byte-for-byte "
    "at current main (ercot-173 §5, carried through ercot-174/185/186/188/191), "
    "so every ercot-192 gate is scored on a same-HEAD pair rather than against "
    "the committed keeper's ledgered numbers. No mechanism is armed and no free "
    "parameter is added by the control itself. "
    "docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md"
)

_ARM_ATTEST = (
    "ercot-192 2026-08-12 — the control plus ONE delta: "
    "coal_peak_offer_yearly_level=true (scripts/replay_keeper.py --set), the "
    "year-keyed 2023 coal `_peak` LEVEL 71.3378 $/MWh from "
    "constants.COAL_PEAK_OFFER_LEVEL_YEARLY_BY_ISO. Built under owner "
    "signature B1 (DECISION-CARD-ercot188 card B, 2026-08-11: 're-adjudicate "
    "under a fresh precommit before any arm'), and ONLY because the "
    "pre-registered Phase 0 returned REFUTED. *** THE OBJECT is a rule-1 / "
    "rule-23 MIS-IDENTIFICATION, not a price residual: ERCOT-140 identified "
    "the level on the 2024/25 disclosure subsets and declared its 2023 "
    "application an extrapolation ('no 2023 SCED disclosure exists'); the "
    "ercot-157 delivery-2023 corpus dissolved that premise, and the "
    "constant's OWN instrument reads p90 = 75.00 $/MWh on the 2023 rows — "
    "level_2023 71.3378 after removing its own gas response, i.e. +36.1389 = "
    "14.42x the ±$2.5062 identification band, the armed constant being roughly "
    "HALF the measured 2023 top. *** THE COVERAGE OBJECTION IS CLOSED BY "
    "BOUND, NOT BY REPAIR: ercot-169 could not license the read (curve_share "
    "0.9702 vs the 0.9876 floor) and ercot-171 showed the resource-drop route "
    "cannot reach a p90 of the curve TOP (G-NEUT +19.17 = 7.6x band). This "
    "lane takes the route needing no repair at all — the missing rows carry "
    "ZERO weight in a weighted quantile, so the weight is given the most "
    "extreme admissible price in each direction and the SAME statistic "
    "recomputed, yielding an exact identification interval under ANY "
    "imputation whatsoever. Its LOWER edge is 71.3378 in all three windows "
    "(matched-CST, full-day, raw-CPT), so the 2023 level is at least 14.42 "
    "band-widths above the armed constant no matter what the missing rows "
    "would have said. Nothing is dropped, nothing imputed, no licensing "
    "quantity swapped, and the 0.9876 floor is NOT lowered. *** ZERO FITTED "
    "SCALARS (rule 23): the value is the constant's own statistic on the "
    "constant's own window with the constant's own fuel response removed, and "
    "no residual is consulted anywhere in the derivation. The SLOPE 10.4100 "
    "and the SHARED gas anchor 2.2494 are untouched (rule 19) — one year "
    "cannot identify a slope. 2024 and 2025 fall through to the static level "
    "BIT-IDENTICALLY (the precommit's G-BIT kill). *** NOT C3a-2023 SPEND "
    "(card Q, ruling Q-B, final at ercot-191): any 2023 price movement is "
    "reported at full magnitude, never targeted, never a gate and never the "
    "promotion basis. "
    "docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md; "
    "results/calibration/ercot192_coal_limbs_bound.json"
)

#: The three armed ERCOT margin identifications card B filed as ledger-absent.
#: Written to BOTH arms — the omission is the keeper's, not this lane's.
_MARGIN_ENTRIES: list[dict] = [
    {
        "name": (
            "coal_offer_margin_level / coal_offer_margin_anchor (ERCOT-137, "
            "limb A) — the coal `_mustrun` net-revenue margin's identification "
            "level 15.8807 $/MWh and delivered-coal anchor 1.7387 $/MMBtu"
        ),
        "where": "run_config.scenario_config.coal_offer_margin_level / _anchor",
        "identification": "measured-physical",
        "n_scalars": 0,
        "source": (
            "60-Day SCED `Submitted TPO-Price1` HSL-capacity-weighted p50 curve "
            "bottom, res-hours-pooled over the four 2024-25 disclosure subsets "
            "(16.86 / 16.37 / 15.00 / 15.00), against a training-window "
            "capacity-weighted delivered-coal anchor. Zero fitted scalars; "
            "frozen against residuals (rule 23), re-derives only with its "
            "source disclosure via derive_coal_offer_margin_anchor.py"
        ),
        "root_cause": (
            "2023 APPLICATION CONFIRMED at ercot-171 (restricted delivery-2023 "
            "read level_2023 16.0111 = +0.14x the ±0.9300 band) — the declared "
            "extrapolation is retired BY VERIFICATION. ercot-192 re-read it "
            "through an independent coverage-BOUND instrument and could not "
            "sharpen it (G-WINDOW disagrees: STRADDLES on the matched window, "
            "REFUTED full-day), so the bound does NOT contradict ercot-171 and "
            "no change follows. OPEN, reported not buried: this identification "
            "pools the four subsets' bot_p50 RAW, with no fuel anchoring, while "
            "its registered anchor 1.7387 is the THREE-year mean and the pool "
            "sits at the 2024/25 res-hours mean fuel ~1.7040 — anchoring it "
            "consistently would move the level +0.38 = 0.41x its own band. "
            "Inside the band, so not a defect that changes arming; it is a "
            "convention inconsistency in the committed ERCOT-137 derivation, "
            "first measured at ercot-192 (results/calibration/"
            "ercot192_coal_limbs_bound.json, G_NEUT.coal_mustrun)"
        ),
    },
    {
        "name": (
            "cc_committed_offer_level (ERCOT-139, limb B) — the gas-CC "
            "`_committed` block offer level 10.354 $/MWh at the SHARED gas "
            "anchor 2.2494 $/MMBtu"
        ),
        "where": "run_config.scenario_config.cc_committed_offer_level",
        "identification": "measured-physical",
        "n_scalars": 0,
        "source": (
            "60-Day SCED `Submitted TPO-Price1` capacity-weighted p50 curve "
            "bottom on the CC rows, res-hours-pooled over the same four "
            "2024-25 subsets, with the corpus's OWN measured fuel response "
            "removed (HR_implied 7.8521 $/MMBtu — no model heat rate, no fitted "
            "slope). Cross-subset dispersion ±42.98 % raw -> ±6.47 % anchored; "
            "the independent `Min Gen Cost` p50 instrument lands 3.02 % away. "
            "The anchor is NOT a second constant (rule 19)"
        ),
        "root_cause": (
            "2023 APPLICATION RETIRED BY VERIFICATION at ercot-169 — the "
            "delivery-2023 corpus reads level_2023 10.6276, +0.2736 = 0.41 of "
            "the ±$0.6699 band, with the full-day read agreeing (10.7076) and "
            "±$0.01 clock sensitivity. CAVEAT CARRIED: the coverage licence "
            "passes essentially AT the boundary (2023 CC curve_share 0.95084 vs "
            "the 0.95054 floor; the full-day window's 0.95051 is 0.00003 BELOW "
            "it), so this is a real but not wide-margin confirmation"
        ),
    },
    {
        "name": (
            "coal_peak_offer_level / coal_peak_offer_gas_hr (ERCOT-140, limb C) "
            "— the coal `_peak` gas-anchored top-of-curve level 35.1989 $/MWh "
            "and GAS slope 10.4100 MMBtu/MWh"
        ),
        "where": "run_config.scenario_config.coal_peak_offer_level / _gas_hr",
        "identification": "measured-physical",
        "n_scalars": 0,
        "source": (
            "60-Day SCED incremental-MW-weighted p90 of above-min-load "
            "submitted steps over the four 2024-25 subsets (34.82 / 34.82 / "
            "43.00 / 48.01), anchored on the corpus's own GAS response — the "
            "slope basis is gas because the measured top ROSE while delivered "
            "coal FELL (a coal-fuel form has slope -89.9, wrong sign, refuted), "
            "and GAS_HR lands within ~5 % of the fleet's own measured offer "
            "heat rate 10.905. Cross-subset dispersion ±18.74 % raw -> ±7.12 % "
            "anchored. The anchor is the SHARED gas anchor (rule 19)"
        ),
        "root_cause": (
            "2023 APPLICATION REFUTED at ercot-192 and REPLACED by a measured "
            "year-keyed level (see the coal_peak_offer_yearly_level entry); the "
            "2024/2025 identification above is UNCHANGED and is what the "
            "ercot-192 neutrality gate protects (footing +2.6e-5, and the "
            "lower bound displaces the pooled level by 0.000x band on the "
            "licensed subsets). REPORTED, not buried: on those same licensed "
            "subsets the OPPOSITE bound edge displaces by 2.635x band, because "
            "a p90 of a steep curve top admits a large upward excursion from "
            "even 0.3-0.7 % missing weight"
        ),
    },
]

#: The arm's own entry.
_ARM_ENTRY: dict = {
    "name": (
        "coal_peak_offer_yearly_level (ercot-192) — the year-keyed coal `_peak` "
        "offer LEVEL, 2023 = 71.3378 $/MWh"
    ),
    "where": "run_config.scenario_config.coal_peak_offer_level_yearly",
    "identification": "measured-physical",
    "n_scalars": 0,
    "source": (
        "The ERCOT-140 constant's OWN instrument (ERCOT-138 incremental-MW-"
        "weighted p90 of above-min-load submitted steps, same row filters, same "
        "cap-weighting, CPT->CST at derivation) on the delivery-2023 NP3-965 "
        "SCED corpus: p90 = 75.00 $/MWh (flat at $75 in 9 of 12 months; the "
        "corpus's two most common submitted TOP steps are $78.00 on 21,677 "
        "intervals and $75.01 on 17,869, with the 2024/25 level $34.82 a "
        "distant tenth), minus this form's own gas response 10.4100 x (2.6012 - "
        "2.2494) = 3.6622, giving 71.3378 at the SHARED anchor. The point "
        "estimate is window-invariant (matched h11-22 CST and full-day both "
        "71.3378). ZERO FITTED SCALARS: no residual is consulted anywhere in "
        "the derivation. Slope and anchor untouched (rule 19); 2024/2025 fall "
        "through to the static constant bit-identically. Rule-23 frozen — "
        "re-derives only with its source disclosure. Harness: "
        "scripts/probes/ercot192_coal_limbs_bound_phase0.py; artifacts "
        "results/calibration/ercot192_coal_limbs_bound.json + "
        "ercot192_coal_peak_structure.json"
    ),
    "root_cause": (
        "NONE OPEN on the value. The coverage objection that blocked ercot-169 "
        "and ercot-171 is closed by an exact identification BOUND rather than "
        "by any repair: the no-curve rows carry zero weight in a weighted "
        "quantile, so giving that weight the most extreme admissible price in "
        "each direction brackets the true quantile under ANY imputation "
        "whatsoever, and the LOWER edge is 71.3378 in all three windows — at "
        "least 14.42 band-widths above the armed 35.1989. Two alternative "
        "repairs were REFUSED in the precommit BEFORE any level was read, on "
        "the Phase-0a structure measurement: own-conduct imputation (98.8 % of "
        "the missing headroom is ERCOT-123 bucket (b) price-taking at 98 % "
        "loading, so imputing a curve would invent an offer that was never "
        "submitted — rule 13) and re-expressing the licence on the "
        "exposure-matched a_offered (measured 0.94775 on 2023, i.e. WORSE than "
        "curve_share; a licensing quantity may never be chosen after seeing "
        "which one passes). CARRIED LIMITATION: the level is identified on ONE "
        "year, so it has no within-2023 dispersion band of its own; the "
        "±$2.5062 band quoted throughout is the 2024/25 identification's, used "
        "only to size the deviation"
    ),
}

_CARRY = (
    " CARRIED ONTO THE ercot-192 {TAG}: the year-keyed 2023 `_peak` level "
    "raises the price at which the model's coal TOP tranche is willing to "
    "clear, which is a supply-curve LEVEL correction and not a scarcity-"
    "formation mechanism — the accepted model-class limitation is that an LP "
    "on competitive/measured offers cannot form ERCOT's realized RT tail "
    "equilibrium, and nothing in a measured offer level changes that. The "
    "counts are re-measured on this run and reported at full magnitude."
)


def _tail_counts(bundle: Path) -> dict[int, int]:
    """Model hours > $200 per year, on the SCORER'S OWN basis.

    **This must reproduce ``ordc.hoursGt200.model``**, the quantity
    ``calibration_verdict.score_price_tail`` gates C3c on: *"count of hours the
    LP's MAX ZONAL DUAL exceeds the per-ISO threshold"* — the energy-only P1
    dual, maxed across zones within the hour.

    Written as a demand-weighted mean at ercot-192 and CAUGHT BY THE
    KEEPER-TEXT AUDITOR: the two bases disagree (2023 max-zonal 58 h vs
    demand-weighted 57 h on the arm, 56 h on the control), so the attestation's
    exceptions ledger quoted a magnitude the scored record contradicted. An
    attestation that re-derives a gated quantity on its own basis is a second
    source of truth for a number that already has one; it re-derives the
    scorer's basis here, and nothing else.
    """
    out: dict[int, int] = {}
    for year in YEARS:
        p = bundle / "hourly" / f"system_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["year"] == year) & (df["pass"] == "P1")]
        out[year] = int((df.groupby("hour")["price"].max() > 200.0).sum())
    return out


def _write(bundle: Path, keeper_attest: dict, attested_by: str, tag: str) -> None:
    """Write ``bundle``'s attestation from the keeper's, re-measuring C3c."""
    att = json.loads(json.dumps(keeper_attest))  # deep copy
    att["governance"]["attested_by"] = attested_by

    fp = att["free_parameters"]
    have = {e["name"] for e in fp["entries"]}
    added = [e for e in _MARGIN_ENTRIES if e["name"] not in have]
    if tag == "arm" and _ARM_ENTRY["name"] not in have:
        added.append(_ARM_ENTRY)
    fp["entries"].extend(json.loads(json.dumps(added)))
    fp["n_entries"] = len(fp["entries"])
    # n_residual counts RESIDUAL-identified entries only; every entry added
    # here is measured-physical with zero fitted scalars, so it is unchanged
    # by construction — recompute rather than assert it.
    fp["n_residual"] = sum(
        1 for e in fp["entries"] if e.get("identification") == "residual"
    )

    counts = _tail_counts(bundle)
    for exc in att.get("exceptions", []):
        year = int(exc.get("year", 0))
        if exc.get("criterion") == "price_tail" and year in counts:
            exc["magnitude"] = (
                f"model {counts[year]} h vs actual RT {ACTUAL_TAIL[year]} h "
                f"> $200/MWh (re-measured on the ercot-192 {tag})"
            )
            exc["reason"] = re.sub(
                r"\s*CARRIED ONTO THE ercot-19[128].*$", "", exc.get("reason", "")
            ) + _CARRY.replace("{TAG}", tag.upper())

    path = bundle / "calibration_attestation.json"
    path.write_text(json.dumps(att, indent=1))
    print(
        f"wrote {path} (tail counts {counts}; +{len(added)} DOF entries -> "
        f"n_entries {fp['n_entries']}, n_residual {fp['n_residual']})"
    )


def main() -> None:
    """Write both bundles' attestations from the run191 keeper's."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument(
        "--keeper",
        type=Path,
        default=REPO / "results/calibration/ercot191_dam_rederive_regate",
    )
    args = ap.parse_args()

    keeper_attest = json.loads(
        (args.keeper / "calibration_attestation.json").read_text()
    )
    _write(args.base, keeper_attest, _CONTROL_ATTEST, "control")
    _write(args.arm, keeper_attest, _ARM_ATTEST, "arm")


if __name__ == "__main__":
    main()
