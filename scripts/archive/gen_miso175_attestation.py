"""Generate miso175_hourkey's calibration attestation from the keeper's.

miso-175: the keeper recipe (2026-08-20-miso-173-layup-mask) with ONE new
gated flag, ``miso_seam_envelope_hour_ending_key``, which reads the EIA-930
DIBA parquet's ``local_time`` stamp as hour-ENDING (its measured convention,
solved at r = 1.0000 against the BALANCE ``TI`` series) when bucketing the
armed seam deliverability envelopes — un-rotating the (month × hour-of-day)
cap profile one hour back onto the model's hour-beginning clock. Zero new
free parameters (a key-convention selector; cap values, percentile, ladder
rungs and band grid byte-unchanged), no new mechanism, no membership change.
"""

import json

SRC = "results/calibration/miso173_layupmask/calibration_attestation.json"
DST = "results/calibration/miso175_hourkey/calibration_attestation.json"

d = json.load(open(SRC))

d["governance"]["attested_by"] = (
    "miso-175 - THE SEAM-ENVELOPE HOUR-KEY ROTATION REPAIR, ZERO NEW FREE "
    "PARAMETERS: miso_seam_envelope_hour_ending_key=true on top of the keeper "
    "recipe (2026-08-20-miso-173-layup-mask), solved as replay_keeper --set, "
    "--year 2023 2024 2025 in ONE invocation, years sequential (rules 12/16). "
    "THE DEFECT (found miso-174 §4, INDEPENDENTLY RE-VERIFIED by this "
    "session's scope 1 BEFORE anything was built - probe "
    "scripts/probes/_miso175_rotation_verify.py, record "
    "_miso175_rotation_verify.json): measured_seam_import_envelope bucketed "
    "the EIA-930 DIBA series on its raw local_time stamp and applied the "
    "bucket to the model's hour-BEGINNING clock, but local_time is "
    "hour-ENDING on MISO's local standard clock - SOLVED, not assumed: the "
    "-1 h key reproduces the independently-derived BALANCE TI series at "
    "r = 1.0000 in 2023 AND 2025 (2024 r = 0.8286, the disclosed EIA-930 "
    "internal inconsistency). So the ARMED p90 cap applied at model hour h "
    "was built from the measured population of hour h-1 - an exact +1 h "
    "rotation of the whole diurnal cap profile (PJM-seam import mean |d| "
    "240.9/251.1/241.4 MW across 2023/24/25; rolling the corrected profile "
    "+1 h reproduces the legacy cap to mean |d| 1.8/1.4/2.4 MW; annual mean "
    "level unchanged, PJM 6.232 vs 6.231 GW). INTERNALLY INCONSISTENT with "
    "the repo's own conventions - the seam LADDER derivation reads the SAME "
    "parquet with the conversion applied (derive_miso_seam_ladders.py:141) - "
    "so a correctly keyed price ladder was applied against a mis-keyed cap. "
    "RULE 14 [R-ACCURATE]: a measured-input accuracy repair inside an armed "
    "keeper mechanism, kept on that ground ALONE. RULE 21 [R-DOF]: ZERO new "
    "free parameters (a key-convention selector; cap values, p90, ladder "
    "rungs and band grid byte-unchanged; ledger 33/2 unchanged). RULE 19 "
    "[R-ONE-MECH]: the KEY of the one existing envelope mechanism changes; "
    "nothing stacked, nothing added. RULE 25: MISO-only by the seam-DIBA "
    "gate (verified V-3: every other ISO returns None). CONTROL "
    "BIT-IDENTITY: the session's M-0 control (2026-08-22-miso-175-control), "
    "same recipe at HEAD with the new flag off, reproduces the keeper at "
    "max|diff| = 0.0 on 12/12 scored sidecars of all three years, and its "
    "regenerated legitimacy_diagnostics matches the keeper's committed "
    "artifact gate-for-gate. GATES, ALL KILLS SILENT "
    "(PREREG-miso175-seam-envelope-hour-key-2026-08-22.md, committed with "
    "the ENGINE-FROZEN per-seam cap arrays - 48 sha256 digests + signed "
    "window deltas, _miso175_hour_key_instrument.json - BEFORE any solve; "
    "scorer _miso175_hour_key_ab.py, record _miso175_hour_key_ab.json): "
    "M-0 PASS; M-1a PASS (all 48 regenerated cap arrays digest-identical to "
    "the frozen instrument - the solve consumed exactly the frozen object); "
    "M-1b PASS (the arm never exceeds a corrected cap by more than 1 MW, "
    "any seam, any hour, either direction); M-2a LIVE (95,828 differing P1 "
    "zone-hour price cells over the three years vs the 1,000 bar); M-2b "
    "DIRECTION PASS all three years (over B_loose - Jun-Sep control-binding "
    "hours whose corrected PJM import cap is >= +20 MW looser - mean "
    "arm-control gross import +113.8/+220.9/+272.1 MW, the frozen sign); "
    "M-3 PASS (ZERO D-4 conduct failures on the arm, zero new non-pass rows "
    "vs the regenerated control - the miso-173 headline is preserved); M-6 "
    "AGAINST-INTEREST PASS (C3a-2023 +1.219 -> +1.230 % within the +/-3.0 "
    "band; C3a-2024 -4.068 -> -4.064 %, adverse move 0.00 pp). M-4 (C8) and "
    "M-5 (record flips over the 67-record grid) scored via "
    "calibration_verdict on the registered run and recorded in the RESULT. "
    "RULE 22: no year outside 2023-2025 was solved, scored or registered; "
    "MISO holds neither complete nor final and the holdout spend freeze is "
    "untouched."
)

d["disclosures"]["miso175_note"] = (
    "miso-175 disclosures. (a) LEAVE-ONE-YEAR-OUT IS VACUOUS HERE AND THAT "
    "IS ARGUED, NOT ASSUMED: the mechanism has ZERO free parameters - it is "
    "a key-convention selector whose correct value was solved against the "
    "independently-keyed BALANCE TI series (r = 1.0000), never against any "
    "year's residual; there is nothing to identify, so no year can have "
    "identified it. (b) WHAT THIS DOES NOT CLAIM: C3a-2025 is UNCHANGED in "
    "kind and still FAILS, and it moved AGAINST the model - -11.648 -> "
    "-11.795 % - exactly the direction the prereg's frozen instrument "
    "predicted (the corrected key LOOSENS the summer-evening PJM import cap "
    "+74/+168/+283 MW, admitting MORE import in the hours MISO is tight), "
    "which is why this repair could only ever be kept on rule-14 grounds "
    "and never as scarcity progress. The miso-163 owner ruling and the "
    "miso-171 decomposition close that lane as a model-class limit and "
    "nothing here is claimed against it. C3c stays the single ledgered "
    "caveat. The determination remains NOT-YET on C3a-2025 alone. (c) THE "
    "2024 EIA-930 INTERNAL INCONSISTENCY (DIBA vs BALANCE TI r = 0.8286 at "
    "the solved key vs 1.0000 in 2023/2025, complete DIBA coverage - a "
    "value disagreement inside EIA's own publication, miso-174 §5) is "
    "disclosed on every 2024-specific number; the DIBA product is the "
    "envelope's own source series under BOTH key conventions, so the key "
    "repair is orthogonal to it. (d) THE COMMITTED-VS-REGENERATED "
    "DIAGNOSTICS EXPOSURE is unchanged in kind and disclosed, not created "
    "here; every gate compares regen-control to regen-arm through the same "
    "path at the same HEAD, and this session's regen-control additionally "
    "reproduced the keeper's committed artifact gate-for-gate. (e) THE "
    "CROSS-ISO STALE-BENCHMARK STAMP-ABSENCE FLAG (check_bench_freshness; "
    "five ISOs' bench parts predate the builder-fingerprint stamp) is "
    "disclosed: the A/B compares both arms against the SAME committed "
    "bench, so no gate depends on the stamp; the registration re-renders "
    "MISO's parts through the builder at HEAD. (f) THE PJM ANALOGUE is "
    "handed forward, not inspected: whether pjm_seam_flow_limit's envelope "
    "(a DIFFERENT measured source, the PJM tie-line file) carries the same "
    "hour-key convention is PJM's lane's call (rule 25)."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    "attestation written;",
    d["free_parameters"]["n_entries"],
    "ledger entries /",
    d["free_parameters"]["n_residual"],
    "residual",
)
