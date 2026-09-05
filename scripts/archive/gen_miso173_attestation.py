"""Generate miso173_layupmask's calibration attestation from the keeper's.

miso-173: the keeper recipe (2026-08-20-miso-172-p25mw) with ONE new gated
flag, ``mustrun_layup_window_mask``, which confines the per-plant must-run
floors to hours OUTSIDE each plant's own measured lay-up windows (the
merit-order guard's economic-lay-up extract). No new free parameter (windows,
unit shares and the out-of-merit threshold live in the frozen derive layer),
no new mechanism, no membership change, no level change, availability
untouched.
"""

import json

SRC = "results/calibration/miso172_p25mw/calibration_attestation.json"
DST = "results/calibration/miso173_layupmask/calibration_attestation.json"

d = json.load(open(SRC))

d["governance"]["attested_by"] = (
    "miso-173 - THE MEASURED LAY-UP WINDOW MASK ON THE KEEPER'S OWN PER-PLANT "
    "MUST-RUN FLOORS, ZERO NEW FREE PARAMETERS: mustrun_layup_window_mask=true "
    "on top of the keeper recipe (2026-08-20-miso-172-p25mw), solved as "
    "replay_keeper --set, --year 2023 2024 2025 in ONE invocation, years "
    "sequential (rules 12/16). THE DEFECT: the outage pipeline's merit-order "
    "guard (frozen, scripts/lib/outage_detect.py) partitions every detected "
    ">= 5-day full stop into MECHANICAL OUTAGE (enters the availability "
    "envelope) or ECONOMIC LAY-UP (campd-unit-outages-layup-MISO.csv), the "
    "latter kept OUT of the envelope on the express charter that 'an "
    "economically idle unit is AVAILABLE; the LP declines it on its own "
    "economics' - and the must-run floor then FORCED the plant on inside the "
    "very windows the pipeline adjudicated as not-operating (rule 17 "
    "[R-FLOOR-WINDOW]). Chartering case 1402 Little Gypsy 2023 (the keeper's "
    "sole surviving D-4 conduct FAIL): unit 3 in measured lay-up Jan 1 - "
    "Mar 9 at out-of-merit share 1.0, both units Oct 4 / Nov 4 - Dec 31, "
    "meter online share 0.000/0.015 (Jan/Feb) and 0.033/0.058 (Nov/Dec), "
    "floor binding 2,542 h with the meter dark in 71.1 % of them. THE "
    "MECHANISM: the floors' per-hour clip basis becomes pmax x max(0, "
    "availability - layup_share), the share read through the SAME "
    "accumulator, unit->plant routing and model-fleet capacity denominator "
    "as the unit-outage overlay (outages.unit_layup_removed_fractions), so "
    "outage and lay-up shares are additive by construction. AVAILABILITY IS "
    "NOT TOUCHED - reserves, the scarcity cushion and the LP's own economics "
    "keep the full idle capability; only the forcing is confined to hours "
    "the plant's own record says its self-commitment regime was operating. "
    "RULE 21 [R-DOF]: ZERO new free parameters, n_scalars 0 (the 0.90 "
    "out-of-merit threshold is the frozen classifier's, identified there and "
    "recorded not load-bearing). RULE 23: the extract is consumed, never "
    "re-derived. RULE 13: backcast-only, double-gated (the "
    "_BACKCAST_ONLY_OVERLAY_FIELDS construction guard + a mode gate in the "
    "engine); same-year lay-up windows have no forward analogue, exactly "
    "like the CAMPD outage windows produced by the same detector, and the "
    "mask can only REMOVE forcing the record says is spurious - never add "
    "or relocate any. RULE 19 [R-ONE-MECH]: membership "
    "(mustrun_plant_exclusions), window SIZE (online_frac), LEVEL (p25) and "
    "hour-eligibility (this mask) are four orthogonal properties of the ONE "
    "floor; nothing is stacked. CONTROL BIT-IDENTITY: the session's M-0 "
    "control (2026-08-20-miso-173-control), same recipe at HEAD 1aab994 with "
    "the new flag off, reproduces the keeper at max|diff| = 0.0 on 12/12 "
    "scored sidecars of all three years. GATES, ALL KILLS SILENT "
    "(PREREG-miso173-layup-window-mask-2026-08-20.md, committed with the "
    "pre-solve engine-build predictions before any solve; scorer "
    "_miso173_layup_mask_ab.py): M-1 volume exactness PASS (every live "
    "plant-year's floors-npz ST_GAS volume within max(0.005 TWh, 3 %) of the "
    "frozen engine build, control and arm alike); M-2 volume liveness PASS "
    "(every engine-predicted mover DOWN, every engine-flat plant flat, "
    "mechanism-total deltas within +/-15 % of -0.9439/-0.5643/-0.7615 TWh); "
    "M-3 at-floor movement sign PASS all years (D-2 forced "
    "5.5632/5.6112/7.1480 -> 4.6839/5.0515/6.3594 TWh; 2023/2025 in the "
    "+/-50 % reported band, 2024 0.018 TWh beyond it - at-floor-rate drift, "
    "the pre-registered non-kill interpretation); M-4a PASS with ZERO new "
    "conduct failures and BOTH remaining 2023 failures CLEARED - the target "
    "1402 st_gas_mustrun row AND the plant-990 regenerated reliability_floor "
    "row - leaving ZERO D-4 conduct failures in the bundle, a first for any "
    "MISO run; M-4b the pre-registered target: 1402-2023 FAIL -> pass "
    "(predicted at 0.4 % window-grain zero-share vs the 50 % rider, and it "
    "cleared); M-5 C8 PASS no regression (2025 ST_GAS grounded above budget "
    "at 32.2 % forced, profile_r 0.981, all binding mechanisms clear D-4); "
    "M-6 PASS (67 records, ZERO record-grain PASS -> non-PASS flips); M-7 "
    "PASS (ST_GAS D-1 profile_r 0.945/0.959/0.981 within 0.002 of the "
    "control, cv_ratio 1.719/1.249/1.531). RULE 22: no year outside "
    "2023-2025 was solved, scored or registered; MISO holds neither "
    "complete nor final and the holdout spend freeze is untouched."
)

d["disclosures"]["miso173_note"] = (
    "miso-173 disclosures. (a) LEAVE-ONE-YEAR-OUT IS VACUOUS HERE AND THAT IS "
    "ARGUED, NOT ASSUMED: the mechanism has ZERO free parameters - the "
    "windows are each plant's own dated CEMS-derived record, identified per "
    "plant-year and never against any year's residual, so re-deriving on two "
    "of three years would re-read the same CSV rows. The evidence LOO exists "
    "to produce is present directly: every one of the seven live floored "
    "plants moves TOWARD its own meter in every year it carries windows "
    "(window-grain zero-share, e.g. 1402 0.633->0.004 / 0.356->0.096 / "
    "0.273->0.049) and none moves perversely. (b) WHAT THIS DOES NOT CLAIM: "
    "C3a-2025 is UNCHANGED and still FAILS (-11.8 %); the miso-163 owner "
    "ruling and the miso-171 end-to-end decomposition close that lane as a "
    "model-class limit and nothing here is claimed against it - the masked "
    "energy is winter, the miss is summer. C3c stays the single ledgered "
    "caveat. The determination remains NOT-YET on C3a-2025 alone. (c) "
    "REPORTED AGAINST INTEREST: the M-3 2024 at-floor magnitude landed 0.018 "
    "TWh beyond its +/-50 % band (more removal than the fixed-at-floor-rate "
    "prediction) with M-1/M-2 clean - the instrument limitation miso-172 "
    "section 4 identified, pre-registered here as a non-kill and reported. "
    "(d) THE PLANT-990 CLEARANCE IS A SIDE EFFECT, NOT A TARGET: the "
    "regenerated-diagnostics reliability_floor row convicting 990 on 0.0000 "
    "TWh across ONE binding hour (the missing-materiality-floor instance "
    "raised to the owner at miso-171/172) cleared because the mask removed "
    "that single binding hour. The underlying rubric question - a "
    "materiality floor inside the provenance leg - REMAINS OPEN and is "
    "re-raised in this session's close; this bundle simply no longer "
    "instantiates it. (e) THE COMMITTED-VS-REGENERATED DIAGNOSTICS EXPOSURE "
    "is unchanged in kind and disclosed, not created here; every gate "
    "compares regen-control to regen-arm through the same path at the same "
    "HEAD. (f) THE LATENT CC/CT LEG of the miso-172 p25 level-basis defect "
    "is restated, measured and NOT armed: CC_REGULAR max 2.03x (plant 2070), "
    "CT_PEAKER max 1.50x, inert at MISO because cc_mustrun_per_plant=False; "
    "arming it is a different mechanism under a different charter (rule 19) "
    "and the cross-ISO half is a per-ISO hand-off (rule 25). (g) CACHE-KEY "
    "REGISTRATION REPAIR carried in the same implementation commit: "
    "miso-172's two fields were never registered drop-at-default (nine pin "
    "tests failing at HEAD); both are now registered at their merge-time "
    "defaults alongside this session's own field, restoring the pinned "
    "default key 603c2498bf71d21d, and the M-0 control re-proves solve-path "
    "inertness of all three at this HEAD."
)

json.dump(d, open(DST, "w"), indent=1)
print(
    "attestation written;",
    d["free_parameters"]["n_entries"],
    "ledger entries /",
    d["free_parameters"]["n_residual"],
    "residual",
)
