"""Generate the ercot-253 2021 VALIDATION RUNG attestation.

The run is a rule-22 ``[R-HOLDOUT]`` **validation-tier rung on 2021**, never a
keeper and never a keeper candidate: the 2023 CARVE-OUT config of the two-config
ERCOT keeper replayed on 2021 from the committed ercot-252 bundle, under owner
rulings taken 2026-09-06 on the ercot-253 decision cards and fixed BEFORE the
solve in ``docs/PRECOMMIT-ercot253-2021-rung-2026-09-06.md`` and its
``docs/ADDENDUM-ercot253-as-requirement-2026-09-06.md``.

Why a per-run generator rather than ``gen_touchpoint_attestation.py``: the
generic one's recipe-identity check refuses a declared delta by design, and this
rung carries several. They are declared here, in the disclosures, rather than
laundered through a "verbatim" claim — the same reason ercot-252 has its own.

None of the deltas mints or moves a free parameter, so the rule 20 ``[R-DOF]``
ledger is the source keeper's own, carried over unchanged. The published ORDC
order parameters are PUCT order values; the ``from_year`` gates are
data-availability gates at the measured series' own first year; the AS
requirement is a measured cleared quantity with NO offset added back precisely
so that no un-validatable constant enters.

Usage:
    python3 scripts/gen_ercot253_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ARM = "ercot253_2021_touchpoint"
SRC = "ercot252_2022_touchpoint_repair"  # the carve-out recipe, as run on 2022

DISCLOSURE = (
    "THIS RUN IS A RULE-22 [R-HOLDOUT] VALIDATION-TIER RUNG ON 2021 AND IS NOT A "
    "KEEPER OR A KEEPER CANDIDATE. ERCOT holds a 'complete' marker (validation "
    "ladder 2020-2022 authorized, iterable); the locked test (2019 / H1-2026) is "
    "untouched and remains frozen for every ISO. "
    "(1) WHAT WAS RUN: the 2023 CARVE-OUT config (ercot_offer_swcap_clip + k_peak "
    "33) of the two-config keeper 2026-09-05-ercot248-two-config-keeper, replayed "
    "on 2021 from the committed bundle ercot252_2022_touchpoint_repair via "
    "--replay-bundle --holdout-authorized --no-p1-basis-seed. The config was NAMED "
    "IN THE PRECOMMIT BEFORE THE SOLVE and no second config was solved, so no arm "
    "was chosen after a result was seen. "
    "(2) THE OWNER-RULED DELTAS, all fixed before the solve: (D1) "
    "ercot_reserve_supply_cap_from_year and ercot_load_resource_reserve_from_year "
    "are now DECLARED IN THE KEEPER'S OWN RECIPE at 2020 rather than carried as "
    "per-rung replay overrides - byte-identical in every training year by "
    "construction, since both gates are monotone 'year >= from_year' comparisons "
    "and every training year is >= 2023 >= 2020, so NO re-solve of the keeper was "
    "performed or needed; (D3) ERCOT's ORDC price-formation order parameters are "
    "year-vintaged to their PUBLISHED values - 2021 solves at the system-wide "
    "offer cap HCAP $9,000/MWh and minimum contingency level 2,000 MW, the figures "
    "in force before the PUCT moved them to $5,000 / 3,000 MW effective 2022-01-01 "
    "(16 TAC 25.509, PUCT Project 52631; OBDRR038, PUCT Project 52373). Zero DOF: "
    "every value is a regulatory order figure, and the new table lists 2022-2025 at "
    "exactly the shipped defaults so every training year, the 2022 rung and every "
    "forecast year are BYTE-IDENTICAL. "
    "(3) THE MEASURED-INPUT EXTENSIONS (rule 22: what is held out is the SCORE, "
    "never the DATA) - all applied to 2021 before the solve, none tuned: 60-Day DAM "
    "thermal availability derived for 2021 with the committed 2022-2025 rows kept "
    "byte-identical to HEAD (the joint re-derive's 100.0 MW rating move REPORTED, "
    "NOT APPLIED); NUCLEAR_MONTHLY_CF_BY_YEAR ERCOT 2021 derived from EIA-923 with "
    "2022/2023 re-derived byte-identically as the producer re-proof; the "
    "gtc-limits 2021 clean partition curated from the committed NP6-86 raws (13,538 "
    "rows / 14 GTCs), so ercot_gtc_limits_measured arms instead of falling back to "
    "static TTC; and the NP3-565-CD native-load reader extended to the report's CSV "
    "container (2018-2021 are published as CSV, .xlsx tried first so training years "
    "are byte-identical), without which 2021 would silently drop to the static "
    "per-zone load_share and lose every ERCOT zone's measured diurnal shape. "
    "(4) THE AS REQUIREMENT, AND THE DEFECT IT REPLACES: the first 2021 solve was "
    "STOPPED ~5 minutes in and its partial bundle DELETED after its log read "
    "'per-product req means [0, 0, 0, 0] MW'. ERCOT's published AS Plan "
    "(ASPLANNP433) is on disk for 2022 onward only, and the loader's contract for a "
    "missing file is all-zero - which fails loud in forecast and is SILENT in "
    "backcast - so 2021 had procured no reserve at all and every price criterion "
    "would have measured the missing input rather than the model. It is replaced by "
    "the MEASURED cleared DAM ancillary quantity: the system sum of the 60-Day DAM "
    "Disclosure's per-resource Gen + Load awards "
    "(scripts/data/build_ercot_as_cleared_requirement.py), consumed through "
    "scarcity.ercot_as_measured_requirement_mw, which prefers the published plan and "
    "falls back only when it is absent - 2022 and 2023 verified identical to the "
    "plan-only path, so every training year and the 2022 rung are unchanged. "
    "(5) KNOWN 2021 GAPS, STATED AT THE GATE AND DELIBERATELY NOT PATCHED, all four "
    "biasing price and the price tail LOW and all four pre-registered before the "
    "solve: (a) the AS requirement is UNDERSTATED because self-arranged AS counts "
    "toward the requirement and never appears as a DAM award - measured on the 7,319 "
    "hours of 2022 where both sources exist (the only such year) the gap is RRS "
    "-753.1 MW (-26.6%), NSPIN -269.7 (-6.8%), RegUp -14.9 (-4.1%), and NO offset is "
    "added back because it is identifiable on 2022 alone and would have to be "
    "transported across the post-Uri reform boundary with no second year to validate "
    "the transport (rule 21 [R-DOF]); (b) DEMAND IS METERED LOAD, so the ~20 GW of "
    "firm load shed during Uri (2021-02-13..20) is absent from what the LP must "
    "serve and the model faces a materially easier Uri than the market did; (c) the "
    "60-Day DAM availability view is a DAY-AHEAD declaration that reads CC_REGULAR "
    "0.886 -> 0.691 across Feb 14-18, far above the real-time freeze-off, so the "
    "depth of the model's Uri outage is set by the CAMPD measured-event precedence "
    "cap rather than by that overlay; (d) only the ORDC cap and MCL are vintaged by "
    "D3, NOT the LOLP curve shape (ordc_lolp_params_path), so 2021 prices on the "
    "keeper's curve with the published 2021 anchors. Also unextendable and "
    "unchanged: there is no measured ERCOT HSL for 2021 (owner: 'I can't do it now "
    "but eventually'), so renewables ride the reference-rate grossed-up bound "
    "re-curtailed by the armed ceilings; and the year-scoped SCED conduct tables "
    "carry 2023-2025 only (fast-start pool inert, cleared-share boundary pooled, "
    "coal peak yearly level static) because the 2021 60-day disclosures are past MIS "
    "retention. "
    "(6) WHAT THE NUMBER IS: model-SELECTION evidence for the rule-22 touchpoint "
    "loop, NEVER quotable as a certified out-of-sample skill number (2019 alone is "
    "that, still frozen and never granted). Rule 30(c): a held-out year never "
    "downgrades the ISO - ERCOT's determination is the train-tier 2023-2025 verdict, "
    "CALIBRATED, and this rung neither certifies nor decertifies it. "
    "(7) NOTHING WAS FITTED TO 2021: no parameter was identified on it, the frozen "
    "depths and reference curtailment rates were not re-chosen, no offer-curve "
    "multiplier was swept, and the PRECOMMIT fixed every prediction - C3a FAIL LOW "
    "at a central -40%, C3c 60-160 h vs 258, C3b 0.25-0.60, C1 -3 to -9 TWh, "
    "determination NOT-YET on {C3a, C3b} - before the solve, so the report could not "
    "be written to fit the result."
)


def build() -> None:
    """Write the rung's attestation from the source touchpoint's, deltas declared."""
    src = REPO / "results/calibration" / SRC / "calibration_attestation.json"
    dst = REPO / "results/calibration" / ARM / "calibration_attestation.json"
    d = json.loads(src.read_text())
    prior = d["governance"].get("attested_by", "")
    d["governance"]["attested_by"] = (
        "ercot-253 2021 VALIDATION RUNG (2026-09-06), NOT A KEEPER (rule 22 "
        "[R-HOLDOUT]): the 2023 CARVE-OUT config of the two-config ERCOT keeper "
        "2026-09-05-ercot248-two-config-keeper replayed on 2021 from the committed "
        f"bundle {SRC} via --replay-bundle --holdout-authorized, plus the "
        "OWNER-RULED deltas declared in the disclosures (D1 the from_year gates "
        "declared in the keeper recipe, byte-identical in every training year; D3 "
        "the PUBLISHED pre-Uri ORDC order parameters, PUCT order values at zero "
        "DOF; the measured cleared-DAM AS requirement with NO offset added back) "
        "and the four measured-input extensions rule 22 requires. Zero parameters "
        "fitted, zero fields minted; the DOF ledger is the source keeper's own and "
        "is carried over unchanged. Every lever still traces to a measured or "
        "published input, nothing is fit to a price residual and no output is "
        "pinned to actuals. Solved in-session, never on CI. Source attestation "
        "preserved below in lineage. || LINEAGE: " + prior
    )
    d.setdefault("disclosures", {})["ercot-253_2021_rung"] = DISCLOSURE
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']}, inherited from {SRC})"
    )


if __name__ == "__main__":
    if (REPO / "results/calibration" / ARM).is_dir():
        build()
    else:
        print(f"skip {ARM} (bundle not present yet)")
