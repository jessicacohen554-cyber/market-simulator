"""Generate the miso-227 seam-arm candidate's calibration attestation from the keeper's.

miso-227 is a **KEEPER CANDIDATE** built on the designated keeper's own recipe
(``2026-09-05-miso-220-nonsteam-lift``) with **one** added ``ScenarioConfig``
field, ``miso_seam_neighbour_anchored_ladder=true`` — the PJM seam's import and
export band prices re-anchored on the EXPORTING market's own measured border DA
instead of on quantiles of MISO's own hub. It is the one form the owner ruled
admissible for the D-2 5(i) seam object (2026-09-06), and it is armed here under
the owner's rule-1 ``[R-STRUCT]`` steer of the same day (PREREG §0).

The attestation exists so the arm can be SCORED: ``replay_keeper`` writes none,
and without one the C6 governance gate reads UNATTESTED, guard (b) of the C3c
standing rule blocks reclassification, and C3c scores FAIL on values identical
to the keeper's — the miso-200 vacuous-pass trap, hit at miso-217 §5 and closed
in advance at miso-220. Closing it here is what makes the run's criterion table
readable: it separates the failures the ARM caused from an artifact of a missing
file.

**Everything the keeper attested about ITS OWN levers is carried forward
unchanged**, because this candidate IS the keeper recipe plus one field: the
miso-220 x1.10 non-steam offer lift is still in it, so the keeper's
``authorized_price_tuning`` block and its two FALSE governance assertions are
copied verbatim rather than re-litigated or quietly improved.

**No new ledger entry and no new parameter.** The neighbour ladder is a MEASURED
table from a frozen derive (``derive_miso_seam_ladders.py::derive_pjm_neighbour``,
the identical Q-Q duration coupling the incumbent ladder uses, read off the PJM
western-border DA), with ZERO fitted scalars. ``n_entries`` stays 41 and
``n_residual`` 2.

Usage:
    python3 scripts/gen_miso227_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "results/calibration/miso220_nonsteamlift_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso227_seamneighbour_K"

DISCLOSURE = (
    "THE ARM: ONE ScenarioConfig field, miso_seam_neighbour_anchored_ladder=true, "
    "applied to the designated keeper's own recipe via replay_keeper --set. It "
    "overlays MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR on the PJM seam's per-year band "
    "ladder: band k is priced at the quantile of the PJM WESTERN-BORDER DA whose "
    "exceedance duration equals the measured duration of the seam flowing deeper "
    "than the band's midpoint - byte-for-byte the incumbent Q-Q construction, with "
    "the ONLY change being which measured price series the coupling reads. "
    "WHY IT IS STRUCTURAL AND NOT A TUNING CHANNEL (rule 1 [R-STRUCT], rule 13 "
    "[R-MEASURED]): the incumbent anchors MISO's IMPORT offers on quantiles of "
    "MISO's OWN hub, i.e. a seller pricing off the buyer's clearing price. The "
    "owner ruled on 2026-09-06 that an import is offered at the exporting market's "
    "own measured price, and that this is the ONE admissible form of the D-2 5(i) "
    "object - not the miso-181 coincident-peak envelope (adjudicated R) and not "
    "flow-pinning. ZERO fitted scalars: the ladder is a measured table from a "
    "frozen derive with the same rule-23 re-derive trigger as the incumbent, and it "
    "regenerates for a forward year from the extending EIA-930 + border-LMP record "
    "(pooled 2023-2025 ladder = the forward story). No offer-curve multiplier is "
    "touched, no adder/offset/haircut exists, and no output is pinned to an actual. "
    "PJM SEAM ONLY, and that is a DATA boundary stated at the gate (rule 14's "
    "misalignment clause), not a choice: no measured SPP or SOCO/TVA price series "
    "is held under data/raw, so those two seams keep the incumbent MISO-hub anchor. "
    "MEASURED, NOT ASSERTED (miso-226, the rule-29 screen this candidate follows): "
    "cheap-hour imports 3,043 -> 3,624 MW (+581, 0.829x the zero-LP static of "
    "+700.7), footprint confined 277x to the hours a band actually crosses merit "
    "(+527.2 MW vs +1.9 MW), export leg structurally inert (0 hours in merit under "
    "either ladder), five of five pre-registered screen gates PASS. "
    "AND THE NON-CLAIM, pre-committed (PREREG §1 and §5): this form repairs the "
    "ladder's ANCHOR and leaves its FROZEN-ANNUAL-QUANTILE shape, so it moves the "
    "seam's LEVEL and not its RESPONSIVENESS. Measured: corr(imports, own price) "
    "+0.750 -> +0.725 against a MEASURED -0.101, i.e. 3 % of the distance, and the "
    "price-decile slope closes 10 % of its sign error. NO CLAIM is made that the "
    "seam is repaired, and the annual import total moves FURTHER from every measured "
    "comparator on record."
)


def build(dst: Path) -> None:
    """Copy the keeper's attestation onto the candidate, restamped and disclosed."""
    d = json.loads(SRC.read_text())
    d["governance"]["attested_by"] = (
        "miso-227 KEEPER CANDIDATE (2026-09-06) under the OWNER's rule-1 [R-STRUCT] "
        "steer of the same day ('if structural integrity improves but gates regress "
        "that may still be a keeper'), which is also the rule-29(2) owner step the "
        "miso-226 PRECOMMIT pre-registered between a cleared screen and a full span: "
        "control = the miso-220 keeper bundle miso220_nonsteamlift_B itself (already "
        "attested, never re-solved, rule 29(b) form 4, G-DRIFT 47e306d3..13ee0c89 ALL "
        "INERT) vs arm miso227_seamneighbour_K, MISO 2023+2024+2025 in ONE invocation, "
        "years sequential, solved in-session and never on CI (rules 12/16), from the "
        "SAME committed keeper recipe via replay_keeper --set on ONE ScenarioConfig "
        "field. No new ScenarioConfig field minted (the field was minted by miso-225), "
        "no new matrix row, ledger 41/2 unchanged. This attestation certifies the "
        "run's PROVENANCE, NOT that its gates pass — and they do not: the run scores "
        "NOT-YET on a load-bearing C1 cell (CT_PEAKER-2023, -8.29 TWh against a "
        "+/-8.00 band, from 0.015 TWh of keeper headroom), which the PREREG named "
        "before the solve as the likeliest outcome and whose consequence it "
        "pre-registered as ESCALATE-DO-NOT-PROMOTE."
    )
    # CARRIED FORWARD UNCHANGED from the keeper, and deliberately not re-litigated:
    # this candidate IS the miso-220 recipe plus one field, so miso-220's x1.10
    # non-steam offer lift is still in it. Its authorized_price_tuning block, and
    # the two FALSE governance assertions that block scopes, describe levers this
    # run still carries. Copying them verbatim is the honest act; "improving" them
    # to true because THIS session's own delta is measured would launder the
    # inherited lift, which is exactly what C6 exists to catch.
    #
    # What this session's own delta would assert on its own is stronger than what
    # is recorded here — the neighbour ladder is a measured table with zero fitted
    # scalars — and that claim is made in DISCLOSURE, scoped to the delta, rather
    # than by flipping an inherited flag that is about a different lever.
    d.setdefault("disclosures", {})["miso227_seam_neighbour_anchor"] = DISCLOSURE
    d["disclosures"]["miso227_inherited_governance_scope"] = (
        "governance.no_fit_to_price_residuals and levers_trace_to_measured_input are "
        "carried forward FALSE from the miso-220 keeper WITHOUT change. They describe "
        "the INHERITED x1.10 non-steam offer lift, which this candidate still carries "
        "unmodified, not this session's delta. THIS SESSION'S OWN DELTA asserts both "
        "positively and is the reason the arm was run at all: the neighbour-anchored "
        "ladder is a measured table from a frozen derive with zero fitted scalars, "
        "selected by an owner ruling on market structure and by the miso-225/226 "
        "queue - never against a residual, and never swept. The two flags are not "
        "flipped to true because the run as a whole does not earn that claim while "
        "the inherited lift is in it. authorized_price_tuning is likewise copied "
        "verbatim: same channel, same x1.10, same three years, same PREREG citation."
    )
    dst.write_text(json.dumps(d, indent=1))
    print(
        f"wrote {dst.relative_to(REPO)} "
        f"(n_entries={d['free_parameters']['n_entries']}, "
        f"n_residual={d['free_parameters']['n_residual']})"
    )


if __name__ == "__main__":
    build(ARM / "calibration_attestation.json")
