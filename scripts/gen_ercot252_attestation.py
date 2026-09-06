"""Generate the ercot-252 2022 VALIDATION TOUCHPOINT attestation (repair + gates).

The run is a rule-22 ``[R-HOLDOUT]`` **validation-tier touchpoint on 2022**,
never a keeper and never a keeper candidate: the 2023 CARVE-OUT config of the
two-config ERCOT keeper replayed on 2022 (the ercot-250 recipe) under TWO
owner rulings taken 2026-09-06 on the ercot-252 decision card
(``docs/PRECOMMIT-ercot252-2022-repair-resolve-2026-09-06.md`` §1):

* **R2** — the ercot-251 provenance-predicate repair is ADMITTED as a
  correctness fix: the two ERCOT curtailment gates skip their ceiling only
  when the renewable bound is ``delivered_pinned``, never merely because no
  HSL parquet exists. A predicate with ZERO degrees of freedom — no field,
  no threshold, no fitted value — byte-identical in every training year.
* **R4** — ``ercot_reserve_supply_cap_from_year`` and
  ``ercot_load_resource_reserve_from_year`` move 2023 -> 2020 as one paired
  recipe change. A ``from_year`` is a data-availability gate whose value is
  the first year the measured series exists (RTOLCAP 2020, LR awards 2018),
  not a number identified against any residual.

So the rule 20 ``[R-DOF]`` ledger is the source keeper's own, carried over
unchanged (``n_entries`` / ``n_residual`` identical): neither ruling mints or
moves a free parameter. The generic ``gen_touchpoint_attestation.py`` refuses
this bundle by design (its recipe-identity check fails on the two from_year
keys), which is why this per-run generator exists — the deltas are declared
here, in the disclosures, rather than laundered through a "verbatim" claim.

The attestation exists so the run can be SCORED (an UNATTESTED C6 forces
NOT-YET and blocks the C3c standing rule). It is NOT a certification that the
run is promotable: rule 22 forecloses that for any held-out year.

Usage:
    python3 scripts/gen_ercot252_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

ARM = "ercot252_2022_touchpoint_repair"
SRC = "ercot250_2022_touchpoint_carveout"  # the verbatim carve-out replay on 2022

DISCLOSURE = (
    "THIS RUN IS A RULE-22 [R-HOLDOUT] VALIDATION-TIER TOUCHPOINT ON 2022 AND IS "
    "NOT A KEEPER OR A KEEPER CANDIDATE. ERCOT holds a 'complete' marker (validation "
    "ladder authorized); the locked test (2019 / H1-2026) is untouched and frozen. "
    "(1) WHAT WAS RUN: the 2023 CARVE-OUT config (ercot_offer_swcap_clip + k_peak 33) "
    "of the two-config keeper 2026-09-05-ercot248-two-config-keeper, replayed on 2022 "
    "from the committed bundle ercot250_2022_touchpoint_carveout via --replay-bundle "
    "--holdout-authorized, with EXACTLY TWO owner-ruled deltas (2026-09-06, "
    "docs/PRECOMMIT-ercot252-2022-repair-resolve-2026-09-06.md, committed before the "
    "solve): (R2) the curtailment-gate provenance-predicate repair, admitted as a "
    "correctness fix - ercot_gtc_limits_measured and ercot_wtx_curtailment_driver "
    "skip their ceiling only when the renewable bound is delivered_pinned, so on this "
    "no-HSL year the reference-rate grossed-up bound is re-curtailed by the ceilings "
    "the forecast leg already pairs with it (zero DOF; byte-identical in 2023-2025); "
    "(R4) ercot_reserve_supply_cap_from_year and ercot_load_resource_reserve_from_year "
    "2023 -> 2020 as one paired change (the ercot-212 net_credits construction nets the "
    "LR series off the cap rows), arming the measured RTOLCAP cap "
    "(ercot_2022_ordc_reserves_hourly.parquet) and the measured 2022 load-resource RRS "
    "credit (ercot_2022_as_up_mw.parquet, built from the 60-Day Load Resource awards "
    "by scripts/data/build_ercot_as_backyear.py). No other parameter changed, no "
    "ScenarioConfig field minted; the DOF ledger is the source keeper's own, "
    "unchanged. (2) WHAT THE NUMBER IS: model-SELECTION evidence for the touchpoint "
    "loop, NEVER quotable as a certified out-of-sample skill number (2019 alone is "
    "that). (3) NOTHING WAS FITTED TO 2022: the predicate carries no value; each "
    "from_year is the measured series' own first year; the frozen depths, reference "
    "curtailment rates and every other tunable were not re-chosen, and the PRECOMMIT "
    "predicted the C1/C3a trade before the solve so the report could not be written "
    "to fit the result. (4) KNOWN 2022 GAPS, stated at the gate and NOT patched: the "
    "measured HSL 2022 archive is still absent (owner: 'I can't do it now but "
    "eventually'), so the bound is the delivered profile grossed up by the 2025 "
    "reference rate rather than a measured potential; the 2022 LR series' Nov 2 - "
    "Dec 31 tail (1,441 h) is a within-year residual reconstruction (metadata-flagged); "
    "ercot_storage_as_deployment / ercot_storage_as_reserve stay at from_year 2023 "
    "(no 2022 product parquet; not part of the ruling); year-scoped SCED conduct "
    "tables carry 2023-2025 only (fast-start pool inert, cleared-share boundary "
    "pooled, coal peak yearly level static; 2022 60-day disclosures are past MIS "
    "retention). (5) SUPERSEDES 2026-09-05-run250-2022-touchpoint-carveout on the "
    "site (owner ruling 2026-09-06: ONE 2022 run); run250's numbers stand in "
    "docs/FINDING-ercot249-250-2022-touchpoint-2026-09-05.md and git history."
)


def build() -> None:
    """Write the arm's attestation from the source touchpoint's, deltas declared."""
    src = REPO / "results/calibration" / SRC / "calibration_attestation.json"
    dst = REPO / "results/calibration" / ARM / "calibration_attestation.json"
    d = json.loads(src.read_text())
    prior = d["governance"].get("attested_by", "")
    d["governance"]["attested_by"] = (
        "ercot-252 2022 VALIDATION TOUCHPOINT (2026-09-06), NOT A KEEPER (rule 22 "
        "[R-HOLDOUT]): the 2023 CARVE-OUT config of the two-config ERCOT keeper "
        "2026-09-05-ercot248-two-config-keeper replayed on 2022 from the committed "
        f"bundle {SRC} via --replay-bundle --holdout-authorized, plus exactly two "
        "OWNER-RULED deltas declared in the disclosures (R2 provenance-predicate "
        "repair, zero DOF; R4 reserve from_year gates 2023 -> 2020, data-availability "
        "gates on measured series). Zero parameters fitted, zero fields minted; the "
        "DOF ledger is the source keeper's own and is carried over unchanged. Every "
        "lever still traces to a measured input, nothing is fit to a price residual "
        "and no output is pinned to actuals. Solved in-session, never on CI. Source "
        "attestation preserved below in lineage. || LINEAGE: " + prior
    )
    d.setdefault("disclosures", {})["ercot-252_2022_touchpoint_repair"] = DISCLOSURE
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
