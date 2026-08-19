"""Generate miso169_gated_B's calibration attestation from the keeper's.

The arm is the miso-160 keeper recipe plus exactly one zero-DOF mechanism, so
its attestation is the keeper's with: one MEASURED-identified ledger entry for
online_rho (with the RHO_CLIP disclosure), a rewritten governance.attested_by
for the miso-169 A/B, and the session's disclosures. Exceptions carry
unchanged (C5b/C5c benchmark-basis, C3c ledger, C3a downstream).
"""

import json

SRC = "results/calibration/miso160_wefor_B/calibration_attestation.json"
DST = "results/calibration/miso169_gated_B/calibration_attestation.json"

d = json.load(open(SRC))

d["free_parameters"]["entries"].append(
    {
        "name": "online_rho (miso_reserve_online_gated)",
        "where": (
            "data/raw/_processed-legacy/campd_online_reserve_rho_MISO.csv -> "
            "data.online_reserve_rho.load_online_rho('MISO','miso_reg_spin') "
            "-> spec._identified_online_rho"
        ),
        "identification": "measured",
        "lineage_solves": (
            "0 (derived once from the pooled 2023-2025 CAMPD record BEFORE "
            "the arm solved; never touched a residual)"
        ),
        "value": (
            "measured 0.1764 over 5,276,357 online unit-hours, 93.1% CAMPD "
            "coverage (per class coal 0.14 / CC 0.19 / CT 0.31 / ST 0.29; "
            "sensitivities fullhour 0.1705, minload 0.6863). DISCLOSED: the "
            "consumption seam clips to RHO_CLIP=(0.5,4.0), whose 0.5 floor "
            "has NO primary citation (the standing nyiso-144 owner "
            "escalation), so the SOLVED coefficient was 0.5 - CONSERVATIVE "
            "here, because the coupling row ADDS to the pool's joint "
            "headroom row rather than replacing it (unlike NYISO, where rho "
            "is the gated class's sole bound). The measured value is "
            "committed and a re-solve at 0.1764 is one replay_keeper --set "
            "invocation once the owner resolves the band."
        ),
    }
)
d["free_parameters"]["n_entries"] = len(d["free_parameters"]["entries"])

d["governance"]["attested_by"] = (
    "ARM - EXACTLY ONE MECHANISM CHANGES: miso_reserve_online_gated=true. "
    "miso-169, 2026-08-19. PREREG "
    "results/calibration/PREREG-miso167-online-gated-reserve-supply-2026-08-18.md "
    "was pushed by miso-167 BEFORE any construction (its kill thresholds and "
    "decision rule executed verbatim; the pre-registered no-LP pre-check "
    "record _miso169_online_gated_precheck.json was committed BEFORE the "
    "mechanism was built, per the miso-168 corrected order). Both arms are "
    "replay_keeper re-solves of the 2026-08-16-miso-160-wefor-shape keeper's "
    "own meta.json at this session's HEAD, --year 2023 2024 2025 in ONE "
    "invocation each, years sequential (rules 12/16); the arm's single delta "
    "rode the sanctioned replay_keeper --set channel. CONTROL BIT-IDENTITY: "
    "2026-08-19-miso-169-control reproduces the committed keeper with "
    "numeric max|diff|=0 on every scored sidecar of every year. The "
    "mechanism adds ZERO free parameters (the class split is the published "
    "BPM-002 product definition; the requirement is the measured cleared "
    "reg+spin series already in the intake; the curve is the published "
    "Schedule 28 $65/$98 two-step; online_rho is the CAMPD-measured fleet "
    "statistic - see its ledger entry, incl. the RHO_CLIP disclosure). "
    "Every PREREG-miso167 SS6 gate PASSES: K-1 zero record-grain criterion "
    "flips, K-2, K-3 (forced shares unchanged to 4dp), K-5 (2025 price rise "
    "+$10.12 in DA-foreseen scarce hours, $0.00 in RT-only hours). "
    "Promotion by OWNER DIRECTION 2026-08-19 ('If structural integrity "
    "improves but gates regress that may still be a keeper') over the "
    "session's two standing escalations, which remain OPEN and recorded: "
    "the uncited RHO_CLIP 0.5 floor (nyiso-144) and the nyiso-143 D-4 "
    "per-unit conduct rider, which C8-FAILs any MISO artifact regenerated "
    "at HEAD >= 2026-08-18 - the keeper's own committed diagnostics predate "
    "the rider and score PASS; this bundle's freshly-generated diagnostics "
    "score C8 FAIL identically to the bit-identical control, i.e. the "
    "instrument moved, not the dispatch "
    "(RESULT-miso169-online-gated-execution-2026-08-19.md SS4-5). Rule 22: "
    "no year outside 2023-2025 was solved, scored or registered; MISO holds "
    "neither complete nor final and the holdout spend freeze is untouched."
)

d["disclosures"]["miso169_note"] = (
    "miso-169 disclosures, reported rather than patched. (a) THE SOLVED RHO "
    "IS THE CLIP FLOOR, NOT THE MEASUREMENT - see the online_rho ledger "
    "entry; the band is an owner question (nyiso-144), and the floor is "
    "conservative in this construction. (b) THE C8 FAIL ON THIS BUNDLE'S "
    "REGENERATED DIAGNOSTICS IS INSTRUMENT DRIFT: the nyiso-143 D-4 "
    "per-unit conduct rider (2026-08-18) un-grounds ST_GAS on ~4 "
    "sub-materiality plants (1104/1131/1891/8056) whose floors bind in "
    "meter-offline hours - a pre-existing keeper behavior, identical in the "
    "bit-identical control, pointed at the nyiso-140 "
    "reliability_floor_plant_exclusions repair. (c) A REAL INTERACTION: "
    "2023's few DA-foreseen scarce hours get CHEAPER (-$49 mean) - the "
    "regspin binding re-dispatches synchronized capacity and relieves the "
    "Midwest family's $200 step (3 control hours -> 0). (d) The regspin "
    "family's requirement-provenance LOG LABEL misprints 'South "
    "reservation' (cosmetic; the values are the market-wide reg+spin "
    "series)."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    "attestation written;",
    d["free_parameters"]["n_entries"],
    "ledger entries /",
    d["free_parameters"]["n_residual"],
    "residual",
)
