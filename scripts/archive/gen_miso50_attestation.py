"""Generate the miso-50 coal-sigmoid-re-derive probe calibration_attestation.json.

miso-50 carries the miso-49 keeper recipe verbatim (temp_dependent_derate and
all) with ONE change: COAL_SIGMOID_DEFAULTS[MISO] re-derived from the #1803 EIA
Annual Coal Report region f.o.b. + BLS PPI series by
scripts/data/derive_coal_sigmoid.py — converting the MISO coal passthrough sigmoid
from a residual-tuned DOF (the ERCOT byte-copy, issue #1347/G-26) into a
measured-physical parameter. This builds miso-50's attestation by taking
miso-49's governance/exceptions/disclosures scaffolding and layering the
re-derive on top of the freshly-rebuilt DOF ledger (build_dof_ledger.py, which
now classifies COAL_SIGMOID_DEFAULTS[MISO] as measured-physical).

Run AFTER `python scripts/build_dof_ledger.py results/calibration/miso50_coalsigmoid
--iso MISO` and after the bundle is scored, so the residuals_note reflects the
committed legitimacy numbers.
"""

from __future__ import annotations

import json
from pathlib import Path

SRC49 = Path("results/calibration/miso49_tempderate/calibration_attestation.json")
DST = Path("results/calibration/miso50_coalsigmoid/calibration_attestation.json")


def main() -> None:
    att49 = json.loads(SRC49.read_text())
    # DST already carries the freshly-rebuilt free_parameters (coal sigmoid now
    # measured-physical). Keep it; graft miso-49's governance scaffolding.
    att = json.loads(DST.read_text())
    att["schema"] = att49.get("schema", att.get("schema"))

    g = dict(att49["governance"])
    g["attested_by"] = (
        "miso-50 coal-sigmoid re-derive probe 2026-07-09: miso-49 keeper recipe "
        "with COAL_SIGMOID_DEFAULTS[MISO] re-derived from #1803 region f.o.b./PPI"
    )
    g["note"] = (
        "miso-49 keeper recipe verbatim (temp_dependent_derate and all) with ONE "
        "change: the MISO coal-vs-gas passthrough sigmoid (prb / prb_follower / "
        "bituminous) re-derived by scripts/data/derive_coal_sigmoid.py from the EIA "
        "Annual Coal Report region f.o.b.-mine price + BLS PPI coal-mining series "
        "intaked in #1803 — a rule-23 source-data trigger, retiring the ERCOT "
        "byte-copy gas_mid 2.85 / gas_slope 2.5 (issue #1347 / gap G-26). Each "
        "parameter is grounded in measured coal commodity data (gas_mid = "
        "coal-vs-gas-CC merit crossover from region delivered cost; ceil = 1.0 "
        "cost-tracking; floor = gas-trough / crossover; gas_slope = 1 / "
        "cross-region delivered-cost dispersion). Registered as a PROBE "
        "(2026-07-09-miso-50-coalsigmoid) with its rule-20 zero-forcing ablation "
        "twin; NOT promoted — keepers.json untouched. See "
        "docs/handoffs/coal-sigmoid-rederive-2026-07.md."
    )
    g["residuals_note"] = (
        "DISCOVERED RESULT (honest, not tuned away): grounding the MISO coal "
        "offer in measured region f.o.b. makes MISO coal (cheap PRB + cheap "
        "Interior/Appalachian bituminous, whose delivered cost crosses gas-CC "
        "only at $3.19/$4.12 gas — at/above the observed 2.19-3.52 window) MORE "
        "inframarginal, so it dispatches MORE: the pre-existing coal-for-gas "
        "over-substitution WORSENS (C1 2023 COAL_PRB +8.8->+30.6 TWh, COAL_BIT "
        "->+13.9 TWh; C2 2025 coal +16.3%->+24.5%, gas -14.7%->-16.5%; C1 free "
        "10/12->5/12). Per CLAUDE.md rules 1/10/11 this is NOT reverted and NOT "
        "tuned to the residual: the measured f.o.b. is the accurate input, and a "
        "worse fit is the signal that the ERCOT byte-copy's shallower discount "
        "was silently COMPENSATING for a root cause elsewhere — the coal over-run "
        "is a gas-side / daily-basin-spot-granularity gap (the annual ACR f.o.b. "
        "cannot resolve the daily gas troughs where gas decisively out-competes "
        "coal; the daily basin spot indices are S&P/Argus-paywalled — rule-23 "
        "granularity caveat), NOT a coal-offer-level artifact. Root-cause fix "
        "(gas daily shape / seam imports / commitment), not an offer re-tune, is "
        "the open item. All other miso-49 residuals carry over unchanged."
    )
    g["coal_sigmoid_rederive"] = {
        "trigger": "#1803 intake (EIA ACR region f.o.b. + BLS PPI); rule-23 "
        "source-data update, not a moved residual",
        "mechanism": "gas-keyed coal passthrough sigmoid (kept; G-26 R6 "
        "DOCUMENT-AND-KEEP) — only its four numbers re-grounded per (ISO, supply)",
        "identification": "measured-physical",
        "honesty_gate": "fit to measured region f.o.b./PPI movement, never to "
        "the MISO price/volume residual",
        "miso_before_after": {
            "prb": {
                "before": [0.78, 0.98, 2.85, 2.5],
                "after": [0.687, 1.0, 3.187, 2.5],
            },
            "prb_follower": {
                "before": [0.68, 0.92, 2.85, 2.5],
                "after": [0.598, 1.0, 3.187, 2.5],
            },
            "bituminous": {
                "before": [0.55, 0.95, 2.85, 2.5],
                "after": [0.532, 1.0, 4.115, 1.092],
            },
            "order": "[floor, ceil, gas_mid, gas_slope]",
        },
        "scope": "MISO only wired/re-solved; ERCOT/PJM/NEISO params derived to "
        "the provenance CSV but their live literals left unchanged (their "
        "re-solves are separate owner lanes)",
    }
    att["governance"] = g

    # Disclosures: the coal over-run is the open MODEL MISS grounding NOT-YET.
    disc = dict(att49.get("disclosures") or {})
    disc["note"] = (
        "NOT-YET determination: the coal-for-gas over-substitution (C1/C2/C3) is "
        "the dominant open MODEL MISS, and the measured coal-sigmoid re-derive "
        "worsens it — the honest signal that the residual is a gas-side / "
        "daily-basin-spot-granularity root cause, not a coal-offer-level "
        "artifact. The re-derive is kept (accurate measured input, rule 11); the "
        "root-cause investigation is the open item, not an offer re-tune. "
        "Recommendation to owner: HOLD (do not promote miso-50 as a fit "
        "improvement); keep the measured params in-tree; keeper stays miso-49 "
        "pending the gas-side/daily-spot root-cause fix — or promote on "
        "structural-faithfulness grounds (rule 1) accepting the worse fit."
    )
    att["disclosures"] = disc
    att["exceptions"] = att49.get("exceptions")

    DST.write_text(json.dumps(att, indent=2) + "\n")
    fp = att["free_parameters"]
    print(
        f"wrote {DST} (n_entries={fp.get('n_entries')}, n_residual={fp.get('n_residual')})"
    )


if __name__ == "__main__":
    main()
