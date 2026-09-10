"""Emit the SPP-63 calibration attestation for ``results/calibration/spp63_span``.

SPP-63 is the SPP-62 keeper recipe (``results/calibration/spp62_span``, SPP
keeper 7) plus **exactly one change**: ``spp_curtailment_ceiling`` is armed,
with ``spp_curtail_depth_wind`` left at its declared dataclass default
0.288137.  The mechanism ceilings SPP's wind CF upper bound at
``1 - depth x congestion_share(t)`` and, per rule 19 ``[R-ONE-MECH]`` enforced
in ``data/renewables.py``, SUPERSEDES ``vre_curtailment_oversupply_allocation``
rather than stacking on it.

WHY IT EXISTS AT ALL is rule 14 ``[R-ACCURATE]``, never a residual: measured on
keeper 7's own committed sidecars against the committed EIA-930 benchmark, the
model's wind exceeds actual by +10.708 / +11.407 / +11.586 TWh while the LP
takes only 2.71 / 2.30 / 1.80 % of the 11.01 / 11.68 / 11.80 TWh of curtailment
the measured record implies.  The wind POTENTIAL is right (114.0552 / 120.9925 /
122.2552 TWh); the CURTAILMENT is missing.  Record:
``docs/handoffs/FINDING-spp-63-2026-09-10.md`` and
``docs/handoffs/PRECOMMIT-spp-63-curtailment-ceiling-2026-09-10.md``.

This is NOT the ``replay_keeper --out-dir`` attestation gap being papered over:
that driver does not propagate ``calibration_attestation.json`` into an
``--out-dir`` bundle (SPP-62 §8 routed the shared-path defect), so without this
script the span scores C6 UNATTESTED for a plumbing reason rather than a
governance one.

Usage:
    python scripts/gen_spp63_attestation.py
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp62_span/calibration_attestation.json"
BUNDLE = REPO / "results/calibration/spp63_span"

#: The declared level coefficient. Read from the dataclass default rather than
#: retyped, so this file can never disagree with what the solve used.
DEPTH_FIELD = "spp_curtail_depth_wind"


def _declared_depth() -> float:
    """The dataclass default the arm solved on (never a retyped literal)."""
    import sys

    for p in (REPO, REPO / "src"):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from market_sim.config.scenarios import ScenarioConfig

    return float(ScenarioConfig.__dataclass_fields__[DEPTH_FIELD].default)


def build() -> dict:
    """Return the SPP-63 attestation: keeper 7's ledger plus ONE new entry."""
    att = json.loads(KEEPER.read_text())
    depth = _declared_depth()

    fp = att["free_parameters"]
    fp["inherited_from"] = "spp62_span (SPP keeper 7)"
    fp["inheritance_basis"] = (
        "SPP-63 is the SPP-62 recipe plus ONE armed ScenarioConfig gate, "
        "spp_curtailment_ceiling. Every keeper-7 entry carries over unchanged: "
        "no offer band, structural share, shared default or solve-path code is "
        "touched, and the authorized price-tuning channel declared below is "
        "replayed VERBATIM at 0.93 and NOT re-cut by this lane. What changes is "
        "one ADDED entry, spp_curtail_depth_wind, whose identification source is "
        "MEASURED rather than a residual — so n_entries rises 3 -> 4 while "
        "n_residual stays 2."
    )

    # Rule 21 [R-DOF]: the depth is a free parameter and is ledgered as one.
    # Its identification is a published measured series, NOT the residual — so
    # it does not raise n_residual and rule 20's "open root-cause issue" clause
    # is not engaged.
    fp["entries"].append(
        {
            "name": DEPTH_FIELD,
            "where": "run_config.scenario_config.spp_curtail_depth_wind",
            "identification": "measured-physical",
            "lineage_solves": (
                "Set ex ante at its declared dataclass default and solved ONCE. "
                "This lane ran exactly one screen (2025) and one span at this "
                "value; no other value was ever solved, and the value was never "
                "swept against any gate (rule 1 [R-STRUCT] condition (c))."
            ),
            "value": depth,
            "n_scalars": 1,
            "source": (
                "SPP's published measured wind curtailment MW (SPP Market "
                "Monitoring Unit ASOM, committed at "
                "data/raw/spp-hsl/spp_wind_curtailment_annual.csv). The single "
                "energy-weighted value that centres all three scored years at "
                "once: per-year 0.2565 / 0.3139 / 0.2917, pooled 0.288137. ONE "
                "config across every scored year."
            ),
            "root_cause": (
                "NOT an open root-cause issue. The parameter is the LEVEL of a "
                "measured published series, identified from that series and not "
                "from any model residual; the SHAPE it multiplies is SPP's own "
                "published RTBM binding-constraint incidence "
                "(data/raw/reference/spp_curtailment_share.csv, derived by "
                "scripts/data/derive_spp_curtailment_share.py from binding "
                "INCIDENCE only — never a curtailment volume, never a price, "
                "never a residual). Verified by construction: the ceiling "
                "removes 11.2442 / 12.0931 / 12.3556 TWh from the wind bound "
                "against an implied real curtailment of 11.0062 / 11.6755 / "
                "11.7982 TWh, i.e. it centres within 2.2-4.7 % in every year "
                "without any year being fitted."
            ),
        }
    )
    fp["n_entries"] = len(fp["entries"])
    # n_residual is UNCHANGED: the added entry is measured-identified.
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]
    gov["attested_by"] = (
        "SPP-63 (2026-09-10): SPP keeper 7's recipe "
        "(2026-09-10-spp-62-vintage-census — the R-ay coal supply-class census "
        "repair on keeper 6's eia860_vintage_tracks_solve_year, itself on "
        "SPP-52a's authorized offer-curve level) plus ONE change: "
        "spp_curtailment_ceiling armed, with spp_curtail_depth_wind at its "
        "declared dataclass default 0.288137. ONE --years 2023 2024 2025 "
        "invocation, years sequential (rules 12 / 16). The authorized "
        "price-tuning channel declared above is replayed VERBATIM at 0.93 on all "
        "four bands of the ten registered fossil classes and is NOT re-cut by "
        "this lane; no multiplier and no depth was swept against any gate (rule 1 "
        "[R-STRUCT] condition (c)). Rule 21 [R-DOF]: ledger inherited from keeper "
        "7 plus one MEASURED-identified entry, n_entries 3 -> 4, n_residual "
        "unchanged at 2. The arm was screened on 2025 — the year of the "
        "mechanism's own largest measured footprint, named in the PRECOMMIT "
        "before the solve and deliberately NOT a failing-residual year — against "
        "five structural STOP gates, none of which reads C1."
    )

    gov["measured_input_switches"]["spp_curtailment_ceiling"] = {
        "value": True,
        "depth_wind": depth,
        "where": (
            "ScenarioConfig.spp_curtailment_ceiling / spp_curtail_depth_wind. "
            "Applied on the wind CF upper bound as "
            "ceiling_frac(t) = 1 - depth_wind * congestion_share(t), per "
            "(zone, hour), by data.curtailment_share.spp_curtail_multipliers. "
            "Share table: data/raw/reference/spp_curtailment_share.csv (867 "
            "rows), derived by scripts/data/derive_spp_curtailment_share.py."
        ),
        "identification": "measured-physical",
        "source": (
            "SHAPE from SPP's published RTBM binding-constraint archive "
            "(data/raw/spp-binding-constraints) as measured binding INCIDENCE, "
            "binned on the MODEL'S OWN net-load decile x hour-of-day x season "
            "axis. LEVEL from SPP's published measured curtailment MW (SPP MMU "
            "ASOM). Neither leg reads a curtailment volume the model produced, a "
            "price, or a residual."
        ),
        "warrant": (
            "Rule 14 [R-ACCURATE]. Measured on keeper 7's committed sidecars "
            "against the committed EIA-930 benchmark: model wind exceeds actual "
            "by +10.708 / +11.407 / +11.586 TWh, while scored thermal is short "
            "by -10.196 / -11.605 TWh — the same energy to 4.8 % and 1.7 %, with "
            "solar, hydro and nuclear agreeing inside 0.26 TWh. The wind "
            "POTENTIAL is correct (114.0552 / 120.9925 / 122.2552 TWh, "
            "re-derived from wind_cf x wind_cap); the LP simply declines the "
            "curtailment, taking only 2.71 / 2.30 / 1.80 % of the 11.01 / 11.68 "
            "/ 11.80 TWh the measured record implies. Running without SPP's "
            "published curtailment is the inaccuracy; this input is the repair."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED] admissibility is met. congestion_share is "
            "keyed on the MODEL'S OWN net-load decile x hour-of-day x season, so "
            "the mapping regenerates for a forward year from forward drivers and "
            "responds to changed conditions (more wind -> deeper net-load "
            "troughs -> the high-incidence deciles re-compose). It is not an "
            "observed commitment outcome and it pins no output to an actual — "
            "the distinction on which SPP-46 refused the online-hours state-floor "
            "form of a different mechanism. The forecast leg is live in "
            "runner.py under the same gate, so this is not a backcast-only "
            "overlay."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH], ENFORCED IN CODE. Three mechanisms answer "
            "'where does SPP's measured curtailment land': the flat gross-up, "
            "vre_curtailment_oversupply_allocation (ARMED in keeper 7), and this "
            "ceiling. data/renewables.py skips the oversupply allocation "
            "whenever the ceiling is armed, so the basis reverts to the flat "
            "gross-up and the ceiling alone decides both where the curtailment "
            "falls and how much binds. The two can never both be live in one "
            "solve, whatever a recipe asks for. Nothing else floors, ceilings or "
            "prices SPP wind: there is no wind must-take, and "
            "wind_ptc_vintage_offers / negative_renewable_offers are both INERT "
            "for SPP."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: SPP-only by construction — the field is "
            "SPP-named, the multiplier applies only to SPP_CEILING_ZONES, and "
            "both the share table and the depth are derived from SPP's own "
            "published data. No number is carried from any other ISO, and the "
            "shared dataclass default stays False so every other ISO and every "
            "committed keeper is byte-identical."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: two registered ScenarioConfig fields plus one "
            "registered derived CSV. No env-var knob, no per-plant dict, no "
            "getattr fallback literal."
        ),
        "solar_excluded": (
            "Solar takes NO ceiling. SPP's solar bound is delivered-pinned, so "
            "it carries no gross-up headroom to remove and a solar ceiling would "
            "curtail energy the market actually delivered."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-63 span bundle."""
    att = build()
    out = BUNDLE / "calibration_attestation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")
    print(f"  entries: {[e['name'] for e in fp['entries']]}")


if __name__ == "__main__":
    main()
