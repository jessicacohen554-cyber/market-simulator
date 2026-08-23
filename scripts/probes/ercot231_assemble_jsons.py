#!/usr/bin/env python3
"""Assemble the ercot-231 per-factor probe JSONs (PRECOMMIT §5.9).

Documentation-verdict factors (N1b, N2, N3, N4, N5) get ``arm: null`` JSONs
carrying their Phase-0 blocks and the §5.4 kill id that fired. The solved
factor (N1a) gets its full-schema JSON from the A/B outputs once the control
and arm exist — written by this same script when invoked with ``--n1a``
after the solves and the gates wrapper have run.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

CHARTER = (
    "ercot-231: the non-AS energy/tightness factor program "
    "(PRECOMMIT-ercot231-nonas-tightness-2026-08-23, blob 526401e, pushed + "
    "blob-verified before any measurement)"
)


def _env() -> dict:
    import numpy
    import pandas
    import pyarrow
    import scipy

    try:
        import highspy

        hv = getattr(highspy, "__version__", "1.15.1")
    except Exception:
        hv = None
    return {
        "python": sys.version.split()[0],
        "highspy": hv,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pandas": pandas.__version__,
        "pyarrow": pyarrow.__version__,
    }


def _sha() -> str:
    return (
        subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=REPO,
        ).stdout.strip()
    )


def _base(factor: str, phase0: dict, verdict: dict, extra: dict) -> dict:
    out = {
        "probe": "ercot231",
        "factor": factor,
        "charter": CHARTER,
        "session": "hub",
        "branch_sha": _sha(),
        "env": _env(),
        "control": None,
        "arm": None,
        "official": None,
        "probe_basis": None,
        "gates": None,
        "phase0": phase0,
        "verdict": verdict,
    }
    out.update(extra)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n1a", action="store_true", help="also write the N1a solved JSON")
    args = ap.parse_args()

    p0 = json.loads((REPO / "results/calibration/ercot231_phase0.json").read_text())
    dest = REPO / "results/calibration"

    records = {
        "n1b": _base(
            "N1b — priced/elastic DC ties",
            {"n1_interchange": p0["n1_interchange"], "miss_set": p0["miss_set"]},
            {
                "adoption_pass": False,
                "failed_criteria": ["N1b-K"],
                "disposition": "NO-WINDOW + DATA-ABSENT (documentation row, no build, no solve)",
            },
            {
                "reading": (
                    "All 114 keeper 2023 missed hours were net IMPORTS, p50 "
                    "-814 MW = 64.8% of the 1,256 MW DC-tie capability (max "
                    "76.8%), zero export hours - the >=50%-of-capability kill "
                    "fires. An elastic tie could only WITHDRAW "
                    "measured-delivered supply (contradicting measured flows, "
                    "rule 14) to manufacture tightness reality did not have "
                    "(rule 1). And the identification data is absent: no SPP "
                    "or CFE price series on disk (lmp-data holds the six "
                    "modeled ISOs only); neighbor_price.py is the "
                    "forecast-grade seam construction, not wired for ERCOT "
                    "(priced_interchange ERCOT cell '.'). The netting identity "
                    "closes to <=1 MW at the miss set."
                )
            },
        ),
        "n2": _base(
            "N2 — outage/derate residual beyond the armed measured channels",
            {"n2_coverage": p0["n2_coverage"]},
            {
                "adoption_pass": False,
                "failed_criteria": ["N2-K", "N2a-K"],
                "disposition": (
                    "ALREADY-CARRIED (family) + DATA-ABSENT (N2a battery "
                    "outages) + REFUTED-BY-OWN-MEASUREMENT (N2b CHP, item-20 "
                    "record)"
                ),
            },
            {
                "reading": (
                    "The 62-GW covered core (CC_REGULAR/COAL/CT_PEAKER/"
                    "ST_GAS) has its class-hour availability PINNED to "
                    "measured 60-Day DAM HSL by construction; nuclear and "
                    "non-CAMPD plants carry their own measured channels; "
                    "partial outages carry item 24; item 20 (temp derate) is "
                    "R with the physics measured absent. No reachable "
                    "measured physical outage series exists that the armed "
                    "channels do not carry: the per-unit Unplanned Resource "
                    "Outages report and the system-grain HROC both sit on "
                    "~30-day rolling public retention (attempt log, no 2023 "
                    "vintage), the MIS archive is the F4 certificate wall, "
                    "and the data.ercot.com key is the owner's standing "
                    "decline. Battery availability is bounded by G-BAT and "
                    "the n5 battery wedge (model 188.6 vs actual 0.0 MW p50 "
                    "at the miss set - the model has MORE battery supply at "
                    "the missed hours, not less)."
                )
            },
        ),
        "n3": _base(
            "N3 — renewable delivery basis at the missed hours",
            {"n3_renewables": p0["n3_renewables"], "miss_set": p0["miss_set"]},
            {
                "adoption_pass": False,
                "failed_criteria": ["N3-K (leg 2)"],
                "disposition": (
                    "DOCUMENTATION - the wedge is the reduced-network "
                    "topology-class residual; the GTC map completion branch "
                    "has no representable uncarried limit to add"
                ),
            },
            {
                "reading": (
                    "The wedge is real and above the magnitude screen: model "
                    "renewables exceed EIA-930 actuals by p50 +396 MW at the "
                    "miss set (wind +411, solar -13; p90 +1,370, max +2,195), "
                    "0.962-correlated with the MEASURED curtailment (HSL - "
                    "gen, p50 703 MW) - the model redelivers what reality "
                    "curtailed. But leg 2 kills the build: the curtailment is "
                    "SPREAD (west-family 46.5%, coastal 285 MW, south 193 MW "
                    "mean at the miss set), and every unmapped 2023 GTC "
                    "(NELRIO, VALEXP, VALIMP, RV_RH, EASTEX, MCCAMY, ... 14 "
                    "of 17) is adjudicated in ERCOT_GTC_LINK_MAP's own "
                    "comment as unrepresentable in the 7-zone reduction "
                    "(intra-zone pockets; N_TO_H deliberately absent as one "
                    "of several parallel paths). An actual-generation UB pin "
                    "is the rule-13 forbidden outcome form. Bound: fully "
                    "closing the 0.4-0.5 GW wedge is worth ~$0.6-0.8/MWh at "
                    "the measured 1.6 $/MWh/GW stack slope - under every "
                    "bar. The West/Panhandle topology split stays CLOSED."
                )
            },
        ),
        "n4": _base(
            "N4 — demand-side representation residuals",
            {"n4_demand": p0["n4_demand"], "miss_set": p0["miss_set"]},
            {
                "adoption_pass": False,
                "failed_criteria": ["N4-K (sign-consistency leg)"],
                "disposition": (
                    "MEASURED-FAITHFUL (P0a clean; P0b wedge marginal, "
                    "mixed-sign, comparator-noise order; P0c measured shares "
                    "active) - N4a not built"
                ),
            },
            {
                "reading": (
                    "P0a: ZERO interpolated/screened demand hours at the "
                    "miss set (0 NaN in the whole 2023 raw series). P0b: the "
                    "two publications of ERCOT's own load agree to p50 "
                    "-106.9 MW (0.14% of ~75 GW) at the DST-aligned lag -1, "
                    "with sign consistency only 73.7% and the comparison's "
                    "own prevailing-vs-fixed clock residual of the same "
                    "order (p90|wedge| 321 MW; parse verified to 3e-6 "
                    "against the file's own ERCOT total column). The "
                    "pre-registered build condition (>=100 MW p50 WITH "
                    "consistent sign) does not robustly fire - 6.9 MW over "
                    "the floor on a 73.7% sign share is the comparator's "
                    "noise, not a meter wedge - and the pinned disclosures "
                    "adjudicate the literal swap rule-14-misaligned anyway "
                    "(it breaks the supply-consistent identity demand + ix = "
                    "netgen that closes to <=1 MW at the miss set, and "
                    "desynchronizes the renewables/benchmark clock). P0c: "
                    "the measured native-load zonal shares ARE active for "
                    "2023 (miss-set-vs-annual share deltas <=3.6 pp). DR/ERS "
                    "as priced demand: excluded-for-doctrine (measured load "
                    "nets the response; PRC 5.7-7.7 GW, 0 EEA hours)."
                )
            },
        ),
        "n5": _base(
            "N5 — measured supply the model does not carry",
            {"n5_small_classes": p0["n5_small_classes"], "miss_set": p0["miss_set"]},
            {
                "adoption_pass": False,
                "failed_criteria": ["N5-K"],
                "disposition": "ALL CLASSES CARRIED / BELOW-MATERIALITY - no build",
            },
            {
                "reading": (
                    "Every EIA-930 fuel class is carried by the fleet "
                    "(hydro, biomass, oil, OTHER are model classes). At the "
                    "miss set the 'uncarried' quantity max(0, actual - "
                    "model) is p50 0.0 MW for hydro (model 226 vs actual "
                    "147 - the model OVER-dispatches hydro), p50 6.0 MW for "
                    "other+biomass+oil (p90 301), p50 0.0 for battery "
                    "(model 188.6 vs actual 0.0). The N5-K <100 MW p50 "
                    "screen fires for every class. Closure context at the "
                    "miss set (model - actual): gas -1,207, coal +414, "
                    "nuclear -15 - the ercot-216 anatomy reproduced on this "
                    "keeper's miss set. The model's EXTRA supply at the "
                    "missed hours (renewables +396, battery +189, hydro "
                    "+79, coal +414) is the counterparty of its gas "
                    "shortness; none of it is missing-supply tightness."
                )
            },
        ),
    }

    for key, rec in records.items():
        path = dest / f"ercot231_probe_{key}.json"
        path.write_text(json.dumps(rec, indent=1))
        print("wrote", path.name)

    if args.n1a:
        # Assembled after the solves: control/arm official + gates files.
        gates = json.loads((dest / "ercot231_n1a_gates.json").read_text())
        rec = _base(
            "N1a — tie-zone interchange attribution (ercot_tie_zonal_interchange)",
            {
                "n1_interchange": p0["n1_interchange"],
                "miss_set": p0["miss_set"],
            },
            gates.get("verdict", {"adoption_pass": False}),
            {"reading": gates.get("reading", "")},
        )
        rec["control"] = gates.get("control")
        rec["arm"] = gates.get("arm")
        rec["official"] = gates.get("official")
        rec["probe_basis"] = gates.get("probe_basis")
        rec["gates"] = gates.get("gates")
        rec["family_diagnostics"] = gates.get("family_diagnostics")
        rec["summer"] = gates.get("summer")
        rec["adaptive"] = gates.get("adaptive")
        path = dest / "ercot231_probe_n1a.json"
        path.write_text(json.dumps(rec, indent=1))
        print("wrote", path.name)


if __name__ == "__main__":
    main()
