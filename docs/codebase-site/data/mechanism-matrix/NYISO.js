/* Cross-ISO mechanism matrix — NYISO shard (rule 28 [R-MECH-MATRIX]).
 *
 * This file is NYISO's COLUMN of the matrix: one line per mechanism id
 * (the row set lives in ../mechanism-matrix.js, which carries the
 * mechanism-level id/cat/name/def/mode/note). A session that tests a
 * mechanism in NYISO updates ONLY this file — the cell verdict, the
 * forecast-lane posture (fc), the evidence citation (ev) and any
 * NYISO-specific note — plus the keeper/gates stamps on promotion.
 * Never edit another ISO's shard (rule 25 [R-ISO-SCOPE]): a verdict
 * transfers to no other ISO; candidates enter the target shard as U.
 *
 * Cell codes (same vocabulary as the base header): K keeper, R rejected,
 * I inert, G governance-refused/closed, O open, U untested, . n/a.
 * `fc` is the forecast-lane posture where it DIFFERS from the backcast
 * cell (omitted = same as cell). `ev` is this ISO's evidence citation.
 *
 * Append NYISO column re-stamp history as block comments at the END
 * of this file (the pre-2026-08-11 mixed-ISO stamp log stays frozen in
 * the base file's header).
 */
window.MECH_MATRIX_SHARDS = window.MECH_MATRIX_SHARDS || {};
window.MECH_MATRIX_SHARDS.NYISO = {
  iso: "NYISO",
  updated: "2026-08-18",
  keeper: "2026-08-17-nyiso-142-stackdup",
  gates: "(2026-08-17, session nyiso-calibration-declaration) KEEPER -> 2026-08-17-nyiso-142-stackdup (the ASTORIA STACK-DUPLICATE INTAKE CORRECTION), superseding 2026-08-16-nyiso-140-layup-exclusion. NO CELL VERDICT MOVES ON A MECHANISM BASIS (rule 28b/28d): a DATA CORRECTION is not a lever -- 718/718 scenario_config fields identical, sorted-config sha256 identical, so every armed mechanism stays armed and unchanged; plant_emission_rates_v2 stays K with its nyiso-142 evidence citation. Rule 14 [R-ACCURATE], ZERO free parameters: CAMPD/CEMS reports one Astoria generator twice, and in 2025 that doubled number WAS the benchmark. Determination CALIBRATED, criterion for criterion identical, C3c bit-unchanged at 21 / 3 / 24 h; all six pre-registered gates clean. THE OPEN-GATE SET IS UNCHANGED and so is the lever queue: item 1 (the chartered JOINT Zone-K reconciliation) remains GRANTED-BUT-UNWRITTEN, and the named successor nyiso_incity_commitment_obligation stays U. || PRIOR STAMP, preserved: (2026-08-17, session nyiso-calibration-declaration) DETERMINATION IS NOW CALIBRATED. Owner amendment, rubric v3.3: a ledgered C3c caveat is REPORTED at full magnitude but no longer DOWNGRADES the determination, so this keeper — unchanged, unsolved, criterion-for-criterion identical — reads CALIBRATED rather than the with-caveats reading below. NO MECHANISM WAS TESTED AND NO CELL VERDICT MOVES (rule 28b/28d): this is a scorer-side reclassification on committed artifacts, and the C3c lever queue, the open successor lane and the holdout posture are all untouched. Evidence: docs/calibration-determination-rubric.md §9 (v3.3), docs/governance/rule-history.md §4. || PRIOR STAMP, preserved: ONE blocker as of nyiso-109 (2026-08-01) — determination with-caveats, recovered from NOT-YET by the pre-registration's OWN verdict (every construction gate K1-K6 and every kill gate P1-P5 passed; no owner override was needed or used). (1) CLOSED: C3a mean LMP 2023 +10.21 % -> +7.51 %, inside the +/-10 % band, and C3a now PASSES in all three years. The fix is gas_offer_margin_zonal_anchor — the gas-offer net-revenue margin's identification anchor resolved PER ZONE, ZERO free parameters. apply_gas_offer_margin's own identity (at fuel == anchor the reformed offer reduces exactly to the registered band multiplier) is a statement about a unit's OWN delivered fuel, but the ISO anchor is derived from an ISO-level series that does not carry the per-zone basis the solve applies afterwards; NYISO's zonal basis leaves Capital_Hudson (Iroquois Z2) unchanged and shifts NYC (Transco Z6 NY) and Upstate_West (Tenn Z4 200L) strictly DOWN, so two zones carrying 67.6 % of load priced their markup at a fuel level they never pay. The nyiso-108 successor charter named an offer-stack / fuel-basis root cause and that is exactly what it was — but its '2023-specific' premise was FALSIFIED by measurement and is recorded as corrected, not followed. (2) C3c price tail, UNCHANGED and still the SOLE ledgered caveat — bit-identical across the nyiso-109 arm and its same-HEAD control (model 3/0/7 h vs actual 10/12/42 h >$300), so the nyiso-104b frontier declaration stands on its own evidence and no new caveat slot is spent; its PREMISE (C3c is the sole blocker) is RESTORED. (3) OPEN, not a blocker: the price DISTRIBUTION is compressed in all three years — the model reproduces only 69/49/45 % of the measured trough->peak swing, trough over by +7.3/+5.5/+8.7 $/MWh and peak under in 2024/2025 — so 2023 failed alone only because it is the mild year whose peak error is also positive. nyiso-109 corrects the TROUGH half on measured grounds; the PEAK half stays open and C3a 2025 moves -8.73 % -> -9.64 %, nearer the band edge (reported, not hidden). That is the named successor lane, and it is the same defect PJM diagnosed at pjm-141 — measured here independently on NYISO's own data (rule 25). measured_interface_limits was REFUSED ex-ante for NYISO in the same session on NYISO's own MIS P-32 flow-vs-limit measurement. C1 remains 14/14 all-class, 10/10 free-class. (3, updated by nyiso-110, 2026-08-02): the peak half is now DECOMPOSED, no LP — dominated by missing everyday reserve-price formation (co-opt dual >$0 in 17/6/34 h vs measured DA spin >$1 in 100% of peak hours; reserve differential = 64-89% DA / 97-131% RT of the missing swing, passthrough slope ~1), with the energy side OVER-priced at both ends once the measured spin content is stripped — the C3a PASS is a CANCELLATION (the sharpest input to the open owner amplitude-criterion call). The flag-only nyiso_spin_reserve_online single-delta arm was PRE-REGISTERED and SOLVED the same session: INERT by its own K3 rule (dual hours identical to control 17/6/34; the E4 liveness census tested the per-gen headroom binder while the as-built class-2 row is aggregate rho*output, kept slack by reserve-eligible hydro's own 2-5 GW output every hour — corrected on the record). The class-widening successor is refuted ex-ante by the same arithmetic, reserve offers are unpublished, MIP is forbidden: the in-LP reserve-formation family is EXHAUSTED and diurnal_price_amplitude NYISO moves O -> G (no-build, re-opens behind the owner amplitude-criterion call / a reserve-offer or sub-hourly intake / the item-8 hydro leg). Registered: 2026-08-01-nyiso110-control-zerodelta + 2026-08-02-nyiso110-spin-online-inert. Keeper UNCHANGED. FINDING-nyiso110-peak-half-decomposition-2026-08-02.md (§10). (4, nyiso-117, 2026-08-03): KEEPER -> 2026-08-03-nyiso-117-nyc-rcpf, which COMPOSES the two orthogonal rule 14 corrections that had been split across lanes -- caiso-160's CT heat-rate meter-artifact INPUT fix and nyiso-115's NYC locational RCPF demand-curve SHAPE mechanism. ONE config delta, ZERO free parameters (ledger 30 -> 31, n_residual 6). Every gate PASSES and C3c is UNCHANGED at 3/0/14 -- a null PRE-REGISTERED in advance, since a step and a ramp are both $0 at or above the requirement, so it moves the LEVEL in hours a family already binds and cannot add binding hours; it does NOT touch the (3) reserve-formation gap above. The session also measured that nyiso-115's supersession NEVER HAPPENED (its arms were already post-fix; bit-identical at max|dMW| 0.000000), and screened SENY ex ante as S-OVER without a solve. FINDING-nyiso117-stepcurve-compose-2026-08-03.md.(5, nyiso-118, 2026-08-03): KEEPER -> 2026-08-03-nyiso-118-seny-span, arming nyiso_ordc_measured_step_span -- a CONSTRUCTION-CONSISTENCY fix, not a lever: the ORDC step widths now span the MEASURED hourly reserve requirement the balance row ALREADY enforced, instead of the static published MW (SENY's total step width differed from its own requirement in 6,239/6,249/6,231 hours of 2023/24/25 before, 0/0/0 after). ONE config delta, ZERO free parameters (ledger 31 -> 32, n_residual 6). All six gates PASS, K-A..K-E silent, ALL 18 SCORED NUMERIC FIELDS EQUAL to its same-HEAD control, and C3c UNCHANGED -- a null pre-registered in advance. PROMOTION RESTS ON RULE 1 [R-STRUCT] / RULE 14 [R-ACCURATE] AND THE RESIDUAL DELIBERATELY DID NOT MOVE. The LI double-apply hazard was discharged EX ANTE on CONSTRUCTION (li_30min_total byte-identical in widths, requirement AND penalties), and the same probe corrected the record twice: the blast radius is THREE families not one (the docstring's NYC no-op claim is FALSE -- NYC's measured requirement dips below static in 185/227/120 h), but NYC is RE-REPRESENTED not RE-PRICED (reachable price identical at $0.000), so the rule-23 freeze on the NYC curve holds. THIS IS A PARTIAL AND WAS PRE-REGISTERED AS ONE: SENY's penalties are unchanged and its first rung is still $62.50, above the entire measured $23.92/$30.37/$40.00 envelope, so it does NOT close S-OVER. THE NAMED OPEN SUCCESSOR is the SENY LEVEL/STEP mechanism (published $500 base PLUS a $40 increment vs the model's base-only critical_mw = 0 ramp), which needs its own pre-registration and its own arm (rule 19). FINDING-nyiso118-seny-span-2026-08-03.md.(6, nyiso-119, 2026-08-03): KEEPER -> 2026-08-03-nyiso-119-seny-increment, arming nyiso_seny_rcpf_increment_step -- the named open successor (5) called out and rule 19 [R-ONE-MECH] kept out of it. A PUBLISHED-TIER OMISSION FIX: the SOM states SENY 30-minute as a $500/MW base over 1,300 MW PLUS a $40/MW increment above it (2023 SOM p. A-132 prints the pair as one object, 'SENY $500+$40'), and nyiso_dynamic_reserve_requirements has ALWAYS ENFORCED that increment while NOTHING EVER PRICED IT -- the whole shortfall was charged against the base curve, whose first rung $62.50 already sat above the entire measured $23.92/$30.37/$40.00 envelope. ONE config delta, ZERO free parameters (ledger 32 -> 33, n_residual 6): the $40 is the SAME ASM section 6.8 item 12 already pinned for east_30min_total (its clause names SOUTHEASTERN explicitly), the 1,300 MW breakpoint is READ from NYISO_RCPF_LOCATIONAL, and the hourly requirement was already on the balance row. The $500 base, critical_mw = 0 and n_ramp = 8 are UNTOUCHED -- the posted-price instrument never reaches the base, so its shape stays UNIDENTIFIED and keeps its ramp (nyiso-115's discipline). All EIGHT gates PASS and K-A..K-G are silent, with the blast radius EXACTLY ONE FAMILY (the other eight byte-identical in widths, requirement AND penalties at $0.000 reachable price delta) and nyiso-118's total-width == requirement identity SURVIVING at 0/0/0 violating hours in BOTH arms. G4 AS PRE-REGISTERED FAILED on an ASYMMETRIC BOUNDARY SPEC -- exact $40 demanded on the CLOSED interval (0, band], excluding the lower kink (s > 0) but INCLUDING the upper one (s == band), where the LP is degenerate and the dual legitimately sits between adjacent band prices -- and that is RECORDED and re-specified, not quietly redefined (the nyiso-115 G2 / nyiso-117 G2a lesson, now on a PRICE gate rather than a scope gate). ALL 18 SCORED NUMERIC FIELDS EQUAL to its same-HEAD control and C3c UNCHANGED -- both nulls PRE-REGISTERED, since SENY binds in only 2/0/8 hours and a demand curve can only price where there is a shortfall. S-OVER NARROWED, NOT CLOSED: of 10 binding hours, above-measured-ceiling 8 -> 4 and above-published-$40 8 -> 2, but 2023/2024's REALIZED ceilings $23.92/$30.37 sit BELOW the published $40 cap, so pricing AT the cap is still above them -- an INCIDENCE/DEPTH question belonging with the open peak-half lane in (3), not a curve-construction one. Does NOT reach nyiso-110's everyday reserve-formation gap and is not reported as closing it. FINDING-nyiso119-seny-increment-2026-08-03.md. (6, nyiso-120, 2026-08-04): KEEPER -> 2026-08-04-nyiso-120-c119-scope, and the OPEN-GATE SET GROWS BY ONE -- C3a mean LMP now FAILS on 2025 at -10.1 % where the same-HEAD control reads -9.5 % PASS. This was an OWNER-RULED trade under rule 22 D-5(b), not a silent regression: the promoted run lands a rule 14 [R-ACCURATE] INPUT correction with ZERO free parameters (miso-122 hybrid-cogen dark-fuel scope gate on NYISO chp_power_only_heat_rates), removing a measured DOUBLE-COUNT that had been charging 306 MW of NYC CT_CHP an offer heat rate of 11.8032 against a machine that burns 7.4205. Two independent meters agree to 1.0 % and 0.6 % that eGRID CHPCHTI at ORIS 2493 East River is the plant DIRECT-FIRED BOILER fuel, not a topping-cycle steam credit. C1 does NOT regress (14/14 all, 10/10 free BOTH arms), C3c is bit-unchanged and stays the SOLE ledgered caveat (budget UNSPENT at 1 of 3 -- the C3a FAIL is a criterion failure, deliberately NOT ledgered), 2023 C3a IMPROVES (+7.6 % -> +7.2 %) and 2024 stays inside band. The 2025 move is worth -$0.38/MWh on a $60 mean against a $6.68/MWh gap, so ~94 % of that gap is PRE-EXISTING and is the named open residual for NYISO next session. FINDING-nyiso120-eastriver-scope-gate-2026-08-04.md. (7, nyiso-124, 2026-08-04): THAT ~94 % RESIDUAL IS NOW LOCATED, AND THE ROUTE nyiso-123 CHARTERED FOR IT IS CLOSED WITH CAUSE. No LP, no run, KEEPER UNCHANGED, no cell verdict moved, lever queue still EMPTY. The Capital_Hudson -> Zone-F/Zone-G split FAILS the charter's G0: NYISO publishes no F/G (UPNY-SENY) transfer limit in the MIS P-32 posting, the MIS ATC/TTC posting (all 36 training months) or any of the four Gold Book editions, and ext_G is unchanged from nyiso-101 leg 2 — and INDEPENDENTLY the measured basis is at the WRONG cutset: E|F (Central East) +10.17/+5.09/+11.69 $/MWh against F|G -2.65/-0.36/-1.48, Zone G pricing BELOW Zone F precisely in the charter's own cold-snap months. THE C3a BASIS DEFECT IS THEREFORE DIAGNOSABLE, NOT A FRONTIER: CENTRAL EAST - VC is the ONLY internal interface that binds (>=95 % in 4.4/2.5/3.6 % of hours annually, 22.0/17.2/26.9 % of Januarys; the other six 0.0 % everywhere, CONFIRMING nyiso-122), while the model's own link on that cutset separates prices in 13.4/1.5/1.1 % of hours and reproduces 5.0/6.0/0.3 % of the measured basis — Jan-2025 model TTC 3,175 MW vs posted median 3,205 MW, real 26.9 % binding, model 0.0 %. G1 finds Objects A and B are TWO objects (the session's own mirror-image reading FALSIFIED by its quintile decomposition and recorded as corrected), and Object B is the TROUGH HALF of nyiso-110's compression — rule 19 [R-ONE-MECH], diurnal_price_amplitude NYISO stays G. The successor question is ANSWERED in the same session with NO SOLVE, on the ALREADY-COMMITTED network layer (nyiso116_c3c_unitlayer; the 'unmeasurable from committed sidecars' claim is CORRECTED): the model's external seam delivers the right NET and the wrong DISTRIBUTION — the three downstate border links sit at their bound in 98-100 % of all hours of all three years, a flat 3,800 MW against a measured downstate median of 1,870/1,772/2,040 MW, while external>Upstate_West runs net EXPORT (-1,003/-1,520/-1,689 MW p50) against a measured import of +668/+454/+148 MW, and the net across all four links still reconciles to 2-11 %. So ~1.8-2.0 GW of surplus import lands EAST of the cutset and the CE link carries 722.8 MW at the median (util 0.253) vs the real interface's 0.591. NOTHING ARMED, NO LEVER PROPOSED; nyiso-100's SIL retirement is NOT re-opened; seam_flow_envelopes NYISO moves `.` -> `U` under rule 25 as a transfer candidate only. C3c's stated re-open condition is FALSIFIED AS WRITTEN and FLAGGED for owner disposition, not edited. docs/handoffs/nyiso-124-charter-g0-g1-2026-08-04.md. (8, nyiso-131, 2026-08-07): KEEPER -> 2026-08-07-nyiso-131-taxgs-arm on owner decision D-27 (SIGNED sitting Addendum AA.4). GOVERNANCE PROMOTION, NO SOLVE, NO MECHANISM TESTED, NO CELL VERDICT MOVED, AND THE OPEN-GATE SET IS UNCHANGED: determination stays CALIBRATED-WITH-CAVEATS with all 8 criterion statuses identical, C3c remains the sole non-passing criterion carried as one ledgered caveat (2023 over-produced 22 h vs 10, 2024 under-produced 3 h vs 12; budget 1 of 1), re-verified on committed artifacts per rule 22 D-5(b) so the worse-determination stop does not fire. The promoted run is the incumbent's OWN recipe replayed on the corrected gas_st fuel taxonomy (D-25, rule 14 [R-ACCURATE]) — 693/693 shared scenario_config fields identical and the 5 arm-only fields all default False, nyiso_li_tsl_n11_security (adjudicated R at nyiso-130) confirmed NOT armed. NYISO's whole solve-affecting residue is one synthesized-bin heat rate (RED-Rochester ST_CHP 11.454 -> 10.3 MMBtu/MWh on 119.6 MW), demand-weighted |dLMP| <= 0.023 $/MWh, largest class move 0.052 TWh, no gate approached. The two named levers are UNCHANGED and both still open: the chartered joint Zone-K transfer-bound / downstate ST_GAS min_gen reconciliation (rule 19), and the solar CF LEVEL (RENEWABLE_AVG_CF 0.15 Tier-3 vs a measured 0.1955 on the registered fleet). docs/handoffs/taxonomy-gas-st-2026-08-07.md §4.1, docs/handoffs/nyiso-taxgs-promotion-2026-08-07.md. (9, nyiso-132, 2026-08-08): KEEPER -> 2026-08-08-nyiso-132-cf-arm, arming the MEASURED NYISO solar CF LEVEL (RENEWABLE_AVG_CF['NYISO']['solar'] 0.15 -> 0.1955) — lever-queue item 2, CLOSED-with-keeper. New row vre_avg_cf_level, NYISO O -> K in the same session. An UNGATED constants.py re-level (D-25 / caiso-175 construction; zero ScenarioConfig fields, so the A/B ran on the paired-control TREE harness with an INVERTED config-isolation gate). Rule 14 [R-ACCURATE], ZERO free parameters — it replaces a self-declared TIER-3 approximation carrying 'needs-citation' with the registered fleet's measured mature-year CF (2026 Gold Book Table III-2a: 981.8 GWh over 573.4 MW / 15 units for 2025; 573.4 x 8760 x 0.1955 = 982.0 GWh, to 0.02 %). DOF 35 -> 36 entries, n_residual UNCHANGED at 6. 2025 ONLY and the exclusion IS the identification (measured CF 0.1629/0.1468/0.1955; the swing is commissioning ramps, 2024 mean-month/year-end 0.6800; NOT averaged in). THE OPEN-GATE SET IS UNCHANGED: determination CALIBRATED-WITH-CAVEATS with all 8 criterion statuses identical, C3c still the sole non-passing criterion at budget 1 of 1, re-verified per rule 22 D-5(b) so the worse-determination stop does not fire. NO GATED CRITERION REGRESSES — the standing structure-over-gates clause was offered by the owner and NOT needed. Both pre-registered adverse cases REFUTED BY MEASUREMENT: C3a-2025 did NOT cross -10 % (-3.14 -> -3.45 %; largest mean-LMP move in any year 0.31 %) and C3c-2025 did NOT fall through its 21 h floor (UNCHANGED at 24 h); C3c-2023 improves 22 -> 21 h. The paired control reproduces the superseded keeper BYTE-IDENTICALLY (max |d| 0.000000000 MW over 122,640 hourly P1 rows x 3 years) despite a flagged toolchain drift, so the delta is attributable to the CF alone. REPORTED AGAINST INTEREST: solar vs the published registry goes -7.1/+2.4/-23.3 % -> +20.9/+33.2/-0.1 % — an exact mature year bought with TWO advisory-band breaches instead of one, on a REPORT-ONLY band (calibration_verdict.VRE_TOL) for a class D-10 marks 'PINNED (advisory-only, excluded from skill claims)'. NOT called a clean win. LEVER QUEUE NOW: item 1 (the chartered JOINT Zone-K transfer-bound + downstate ST_GAS min_gen reconciliation, rule 19) REMAINS OPEN, joined by a NEW object this session opened — THE MODEL HAS NO COMMISSIONING CURVE (one CF cannot track a fleet whose realized CF runs 0.1468-0.1955), the declared cause of the solar trade and an open item in the keeper's attestation. ALSO FALSIFIED: the nyiso-130 prereg's 'clipping and the donor profile eat ~11 %' — the distribution sums to 1.000000, the hourly mean cf is 0.150000 EXACTLY and ZERO hours clip; the 'realized 0.133' is a year-end-capacity denominator artifact, and sizing off it would have over-shot the published output by +12.3 %. DECLARED BLAST RADIUS: being ungated, the constant is on main, so the NYISO FORECAST lane's 11 committed nyiso-* hindcast sidecars are stale w.r.t. HEAD (forecast lane's own governance). Rule 25: NEISO carries the identical Tier-3 0.15 and is NOT covered (U). results/calibration/FINDING-nyiso132-solar-cf-level-2026-08-07.md.",
  cells: {
    cc_steam_part_capacity: { cell: "." },
    cc_steam_part_reclass: { cell: "." },
    use_campd_bins: { cell: "K" },
    thermal_tranche_artifact_coverage: { cell: "O", ev: "xiso-5 §1 (47 blank; no online_frac column)" },
    plant_level_fleet: { cell: "K" },
    p1_bidcost_pass: { cell: "K" },
    legacy_p2: { cell: "." },
    priced_interchange: { cell: "K" },
    reference_price_interface: { cell: "G", ev: "nyiso-115 (ex-ante transfer adjudication, 0 solves; scripts/probes/_nyiso115_transfer_queue_adjudication.py -> results/calibration/nyiso115_transfer_queue_adjudication.json)" },
    gas_offer_net_revenue_margin: { cell: "K", ev: "nyiso-72" },
    gas_offer_margin_zonal_anchor: { cell: "K", ev: "nyiso-109 (registered A/B: 2026-08-01-nyiso109-zonal-margin-anchor vs 2026-07-31-nyiso109-control-zerodelta; results/calibration/_nyiso109_zonal_anchor_ab.json; FINDING-nyiso109-zonal-margin-anchor-2026-08-01.md)" },
    diurnal_price_amplitude: { cell: "G", ev: "nyiso-109 (trough half corrected); nyiso-110 (peak half DECOMPOSED — FINDING-nyiso110-peak-half-decomposition-2026-08-02.md + PREREG-nyiso110-spin-online-peak-formation-2026-08-02.md); xiso-1 §2" },
    ordc_scarcity_overlay: { cell: "." },
    dump_cost_full_offer_domain: { cell: "I", ev: "caiso-139 §E ex-ante census" },
    ercot_rtordpa_overlay: { cell: "." },
    maxgen_emergency_tier_pricing: { cell: "I", ev: "nyiso-115 (ex-ante transfer adjudication, 0 solves; scripts/probes/_nyiso115_transfer_queue_adjudication.py -> results/calibration/nyiso115_transfer_queue_adjudication.json)" },
    nyiso_rcpf_family: { cell: "K", ev: "nyiso-84; calibration-best-so-far-nyiso frontier note; nyiso-110 (FINDING-nyiso110-peak-half-decomposition-2026-08-02.md §5-E4/§6.1)" },
    reserve_family_dual_sidecar: { cell: "K", ev: "nyiso-114 (PREREG-nyiso114-reserve-family-sidecar-2026-08-03; FINDING-nyiso114-reserve-family-sidecar-2026-08-03)" },
    unit_network_layer_sidecar: { cell: "K", ev: "nyiso-116 (PREREG/FINDING-nyiso116-c3c-unit-layer-2026-08-03 §4)" },
    matrix_gap_census: { cell: "K", ev: "nyiso-114 (FINDING-nyiso114-reserve-family-sidecar-2026-08-03 section 3)" },
    forecast_xyear_warmstart: { cell: ".", fc: "R" },
    energy_reserve_coopt: { cell: "K" },
    ercot_multiproduct_as: { cell: "." },
    online_capacity_envelope: { cell: "." },
    reserve_pergen: { cell: "." },
    dynamic_reserve_requirements: { cell: "K", ev: "nyiso-70" },
    measured_ramp_capability: { cell: "I", ev: "nyiso-113 (results/calibration/_nyiso113_locational_reserve_screen.json section 4)" },
    reserve_deliverability_scoping: { cell: "." },
    nyiso_li_locational_reserve: { cell: "K", ev: "nyiso-113 (PREREG-nyiso113-li-locational-reserve-2026-08-02; screen results/calibration/_nyiso113_locational_reserve_screen.json)" },
    nyiso_east_reserve_families: { cell: "I", ev: "nyiso-113 (results/calibration/_nyiso113_locational_reserve_screen.json section 1); built nyiso-84" },
    nyiso_synchronised_reserve: { cell: "U", ev: "nyiso-84 (built); nyiso-110 section 10; nyiso-113 (row added); nyiso-143 (results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md, probes scripts/probes/_nyiso143_nyc_spin_liveness.py + _nyiso143_online_rho.py, records _nyiso143_nyc_spin_liveness.json + _nyiso143_online_rho.json)", note: "STAYS U -- and the standing 'inert by construction' ground for closing it is FALSIFIED BY MEASUREMENT at nyiso-143 (2026-08-18, NO SOLVE, no field, no arm, keeper unchanged). Reported against the session's own convenience: nyiso-143 was chartered to close this cell and instead had to re-open it. (1) THE CLASS-2 HEADROOM ROW IS PER-ZONE, NOT AGGREGATE: model/lp/reserve_rows.py writes R[c,z] - rho * sum_{elig g in z} P[g] <= 0 per zone. nyiso-110's INERT arm gated the PUBLISHED nyca_10min_spin / east_10min_spin families, whose zone masks span NYCA/East so upstate hydro's 2-5 GW does enter the row -- the aggregate reading is correct FOR THAT ARM. This flag adds nyc_spin_online, masked to NYC ALONE (reserves/spec.py, nyc_idx), and NYISO has NO NYC HYDRO (154/147/3 hydro rows, none in NYC). The verdict was read across two structurally different zone masks. (2) THE FAMILY IS LIVE on the keeper's own committed dispatch: against the 250 MW static requirement (NYISO_SPIN_FRACTION 0.5 x nyc_10min_total 500), NYC online quick-start output has minimum 79.1/86.3/82.9 MW and median 212/140/249 MW, so the family is slack in every hour ONLY IF rho >= rho* = 3.1588/2.8981/3.0152 -- the top quarter of rho's own [0.5, 4.0] clip band. At the ceiling 4.0 it binds in 0 hours; at 1.0 it binds 7911/7159/4669 h (90.3/81.7/53.3 %) with worst deficits 170.9/163.7/167.1 MW. (3) AND rho IS NEVER IDENTIFIED. Its declared basis -- the fleet's own cap-weighted (pmax-pmin)/pmin, 'a fleet property ... not a tuned coefficient' -- is guarded by valid = (pmin > 0) & (pmax > pmin), and on the keeper's fleet ONLY 4 OF 851/849/705 LP ROWS CARRY pmin > 0 AT ALL (the nuclear block), NONE quick-start eligible. Under plant_level_fleet + use_campd_bins, must-run rides min_gen and pmin is identically zero across the merchant fleet, so the identification path is DEAD CODE for this ISO and the value that decides the mechanism is the literal 1.0 in the else: branch -- every year, in BOTH this branch and the rule-19 sibling's obligation branch (451/443/299 rows, 0 valid). A mechanism provably inert at rho >= 3.16 and binding in 90 % of hours at rho = 1.0, on a coefficient never measured, carries A FREE PARAMETER IN DISGUISE: rule 21 [R-DOF] and rule 5 [R-NO-MAGIC] each bar arming it. THIS IS A ROOT-CAUSE FINDING, NOT A REJECTION -- NYISO's downstate 10-minute requirement genuinely IS an online-gated obligation; what is missing is a measured 10-min-headroom-per-MW-online statistic derived under rule 23 [R-FROZEN-DERIVE] from source data. ONE IDENTIFICATION UNBLOCKS THE PAIR and the hard ValueError means only ONE of the two may ever be armed. NOT closable without a solve, and not closable WITH one until rho is identified. nyiso_spin_reserve_online's I STANDS UNTOUCHED (explained, not contradicted). Nothing here re-opens diurnal_price_amplitude (G). RULE 25: the pmin-based rho identification is NOT NYISO-specific code -- any ISO whose keeper runs a tranche/binned fleet with pmin = 0 hits the same fallback if it ever arms an online-gated reserve class; nyiso-143 measured ONLY NYISO, asserts nothing about the other five, and touched no other shard." },
    nyiso_spin_reserve_online: { cell: "I", ev: "nyiso-110 (FINDING-nyiso110-peak-half-decomposition-2026-08-02.md section 10); nyiso-113 (row added)" },
    nyiso_incity_commitment_obligation: { cell: "U", ev: "nyiso-105 section A (named as the compliant replacement path); nyiso-113 (row added); nyiso-142 (named successor); nyiso-143 (results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md section 4, record _nyiso143_online_rho.json)", note: "STAYS U, and nyiso-143 (2026-08-18, NO SOLVE) adds a SECOND, PRIOR blocker to the one nyiso-142 named. The obligation branch derives the SAME online_rho the path-A sibling does -- cap-weighted (pmax-pmin)/pmin over obligation_elig = quick_elig | ST_GAS steam, guarded by valid = (pmin > 0) & (pmax > pmin) -- and on the keeper's fleet that guard admits 0 OF 451/443/299 ROWS in 2023/2024/2025, so rho falls to the hard-coded else: 1.0 in every year. Since rho is what decides whether an online-gated family binds at all (sibling row: inert at rho >= 3.16, binding in 90 % of hours at rho = 1.0), arming this flag today would put an UNIDENTIFIED scalar on the critical path of a downstate commitment driver -- rule 21 [R-DOF] / rule 5 [R-NO-MAGIC]. So the object nyiso-142 named is real and still open (in-city ST_GAS falls 1.33 TWh over a span the market's rose; Lower-Hudson import rises +2.89 TWh; Ravenswood's steam bin never reaches its 4.49 TWh ceiling; three rival readings already refuted -- plumbing, the Ravenswood _FLEET_GROUP_OVERRIDE, the transfer bound), but the FIRST thing it needs is rho's identification, not a solve. Rule 19 [R-ONE-MECH]: MUTUALLY EXCLUSIVE by hard ValueError with BOTH nyiso_synchronised_reserve and nyiso_spin_reserve_online -- one identification unblocks the family and only one member may ever be armed. This row is the GENERALIZED form (published J/K ladders) and the path-A NYC-spinning family is its hand-scoped special case, so if one is ever built it should be this one." },
    nyiso_hydro_reserve_eligible: { cell: "K", ev: "issue #1344 lever 3; nyiso-110 section 10; nyiso-113 (row added, zonal census)" },
    nyiso_scr_edrp_reserve_eligible: { cell: "K", ev: "issue #1344 lever 3 step 2; nyiso-113 (row added)" },
    nyiso_import_reconciliation: { cell: "K", ev: "nyiso-99 (FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29.md); nyiso-113 (row added)" },
    nyiso_downstate_ct_gas_basis: { cell: "K", ev: "keeper DOF ledger (nyiso_downstate_ct_gas_daily, measured); nyiso-113 (row added)" },
    nyiso_local_selfsupply: { cell: "K", ev: "keeper DOF ledger (residual); caiso-155 (D-4 filing); nyiso-113 (row added)" },
    nyiso_firm_imports: { cell: "K", ev: "caiso-155 stub (D-2/D-4 visibility fix); nyiso-113 (row added)" },
    nyiso_rcpf_postsolve_overlay: { cell: "G", ev: "reserves/spec.py::_nyiso_design rule-19 guard; nyiso-113 (row added)" },
    nyiso_nyc_rcpf_step_curve: { cell: "K", ev: "nyiso-115 (row + field added; ex-ante screen, results/calibration/nyiso115_nyc_rcpf_curve_screen.json); instrument from nyiso-114 (FINDING-nyiso114-reserve-family-sidecar-2026-08-03.md §3)" },
    nyiso_ordc_measured_step_span: { cell: "K", ev: "nyiso-113 (row added); construction documented in reserves/spec.py::_nyiso_design" },
    nyiso_seny_rcpf_increment_step: { cell: "K", ev: "nyiso-119 (row added with the field); PREREG-nyiso119-seny-increment-2026-08-03.md; nyiso119_seny_increment_construction_probe.json; screen evidence nyiso117_seny_rcpf_curve_screen.json" },
    gas_commitment_bridge: { cell: "K", ev: "nyiso-87/90" },
    reliability_floor: { cell: "K", ev: "nyiso-81 re-derive; NYISO_PEAK_WINDOW_FLOORS_OFF" },
    reliability_floor_plant_exclusions: { cell: "K", ev: 'nyiso-140 KEEPER (promoted 2026-08-16, owner ruling). Excludes the economically laid-up Port Jefferson (2517) from the always-on Long_Island ST_GAS limb - a rule-17 [R-FLOOR-WINDOW] MEMBERSHIP correction, never a window change. IDENTIFICATION (source-data trigger, no residual consulted): 2517 median when-available CF EXACTLY 0.000 in every hour block of 2023/2024/2025, 73% of cool hours at zero, ~100% model availability because the 2026-07-26 guard fix (6a8f285) correctly un-booked lay-up from the outage extract; it absorbed 72.6% of everything the limb forced (1.87 of 2.57 TWh over 3 yr) on 7.2% of the fleet output. WINDOW CONFIRMED CORRECT AND UNCHANGED - Barrett (2511) and Northport (2516) run the real persistent baseline (cool-day median CF 0.254/0.313 at h00-05) and are forced only 4-6% of their own output. floor_pct UNCHANGED at 0.262: two CANCELLING basis errors (a daily-mean statistic applied hourly; a fleet aggregate applied per unit) correct to 0.2666, so ZERO free parameters (rule 21, n_residual unchanged at 6). A/B vs same-HEAD control 2026-08-16-nyiso-140-control, 2023 2024 2025 one bundle each, ALL SIX pre-registered kill gates clean; K3 liveness shed 0.602/0.560/0.625 TWh against the ~0.62/yr predicted from CAMPD BEFORE any solve. CALIBRATED-WITH-CAVEATS, C3c the lone ledgered caveat, criterion-for-criterion identical to the superseded keeper. DO-NOT-MISREAD: the fit gets slightly WORSE and was pre-registered to (ST_GAS err +2.679->+2.263 in 2023, -0.595->-0.916 in 2024, -3.379->-3.737 in 2025; summed |err| 6.653->6.916 TWh). Kept on rule 1 [R-STRUCT] and the owner structure-over-gates clause; under rule 14 [R-ACCURATE] the degradation is a DISCOVERED BUG - the manufactured energy was masking a real downstate under-production - and THAT root cause is the successor. Do NOT re-floor the laid-up plant and do NOT reach for this row to buy back volume in any ISO (rules 1/24); rule 28(d) - this verdict transfers to NO other ISO, which must identify any laid-up unit from its OWN CAMPD conduct. FIRST APPLICATION OF K6-PRIME (owner-adopted 2026-08-16): the surviving nyiso_gas_commitment_bridge share ROSE (+0.0045/+0.0118/+0.0051) while doing strictly less work, which bare K6 would have killed. STANDING CAVEAT: K6-prime leg (a) leans on D-4, which is TAUTOLOGICAL for an h0-23 floor (offwindow_share 0.0 by construction), and the adopted D-4 per-unit rider is NOT yet implemented - that leg is unproven rather than passed. Evidence: results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md, PREREG-nyiso140-li-st-floor-membership-2026-08-16.md; probe scripts/probes/_nyiso140_li_st_floor_membership.py' },
    coal_mustrun_per_plant: { cell: "K" },
    coal_takeorpay_committed: { cell: "." },
    coal_prb_committed_dispatchable: { cell: "." },
    coal_prb_committed_split: { cell: "." },
    miso_coal_night_floor: { cell: "." },
    coal_min_load_floor: { cell: "." },
    st_gas_mustrun_p25: { cell: "I", ev: "nyiso-105 (FINDING-nyiso105-stgas-inert-seam-live-2026-07-31 §A, PREREG-nyiso105 §2, probe _nyiso105_seam_recipe_stgas.py §C) — INERT ex ante, no solve" },
    historic_outage_overlay: { cell: "I", ev: "nyiso-115 (row added by the shared-field census; inertness re-verified against src/market_sim); FINDING-ercot79-phantom-outage-2026-07.md" },
    coal_drop_pof: { cell: "K", ev: "nyiso-115 (row added by the shared-field census; scripts/mechanism_matrix_gap_sweep.py shared leg + check_mechanism_matrix.py shared ratchet)" },
    gas_st_startup_spread: { cell: "K", ev: "nyiso-115 (row added by the shared-field census; scripts/mechanism_matrix_gap_sweep.py shared leg + check_mechanism_matrix.py shared ratchet)" },
    cc_duct_peaking: { cell: "K", ev: "nyiso-115 (row added by the shared-field census; scripts/mechanism_matrix_gap_sweep.py shared leg + check_mechanism_matrix.py shared ratchet)" },
    cc_nameplate_summer_derate: { cell: "K", ev: "nyiso-115 (row added by the shared-field census; scripts/mechanism_matrix_gap_sweep.py shared leg + check_mechanism_matrix.py shared ratchet)" },
    summer_derate_basis_aware: { cell: "." },
    commission_year_cod_fallback: { cell: "U", ev: "exposed on the shared assembly.py::_commission_year path (registry hit share 0.0%, miso-158 census; 2025 non-CHP summer capability overstatement censused per ISO) — rule 25/28(d): no verdict transfers, this lane measures its own before arming" },
    summer_wefor_share_override: { cell: "U", ev: "the 0.30 constant's seasonal split stays this lane's live treatment; the per-ISO measured override (miso-160 construction) is unarmed here — rule 25/28(d): no value transfers, this lane derives its own from its own admissible ticket-based record before arming" },
    coal_nameplate_summer_derate: { cell: "." },
    unit_outage_lp_capacity_basis: { cell: "U" },
    wefor_residual: { cell: "U" },
    cc_winter_capability_basis: { cell: "U" },
    cc_capacity_reconcile: { cell: "U" },
    cc_capacity_reconcile_path: { cell: "K", ev: "nyiso-115 (row added by the shared-field census; scripts/mechanism_matrix_gap_sweep.py shared leg + check_mechanism_matrix.py shared ratchet)" },
    cc_mustrun_per_plant: { cell: "." },
    winter_fuelsec_posture: { cell: "." },
    chp_steam_following: { cell: "K" },
    netload_drag_floors: { cell: "R" },
    ramp_envelopes: { cell: "K", ev: "nyiso-111 (own artifact + bound-against-the-bound pre-check + A/B, PROMOTED KEEPER — FINDING-nyiso111-ramp-envelopes-2026-08-02.md §4)" },
    forced_share_d4_census: { cell: "I", ev: "xiso-3 §3 (zero latent gaps — fully windowed; ST_GAS 27.5% the closest sub-cap class anywhere)" },
    reserve_family_sidecar: { cell: "I", ev: "nyiso-114 §1-§2 (built + first use); nyiso-113 §8 (the gap, and the invalid-instrument correction that motivated it); nyiso-115 (zones column + this row)" },
    diagnostics_plant_set: { cell: "I", ev: "caiso-155 §B/§D (7.884 TWh/yr HQ row now visible; nyiso_gas_commitment_bridge 5.31/3.14 pp G-06 false-FAIL averted via BRIDGE_MECHS)" },
    energy_online_capability_cap: { cell: "." },
    offer_curve_by_group: { cell: "K" },
    ercot_faststart_pool_plant_physics: { cell: "." },
    ercot_econ_curve_top_refine: { cell: "." },
    ercot_faststart_pool_offer: { cell: "." },
    ercot_offer_surface_continuous: { cell: "." },
    ercot_offer_surface_top_scoped: { cell: "." },
    ercot_offer_surface_position_tail: { cell: "." },
    ercot_offline_commit_offer: { cell: "." },
    measured_offer_surface: { cell: "G", ev: "nyiso-115 (ex-ante transfer adjudication, 0 solves; scripts/probes/_nyiso115_transfer_queue_adjudication.py -> results/calibration/nyiso115_transfer_queue_adjudication.json)" },
    pjm_midcurve_belt: { cell: "." },
    coal_passthrough_sigmoids: { cell: "K" },
    coal_econ_bound: { cell: "." },
    coal_offer_net_revenue_margin: { cell: "." },
    cc_committed_offer_margin: { cell: "G", ev: "nyiso-115 (ex-ante transfer adjudication, 0 solves; scripts/probes/_nyiso115_transfer_queue_adjudication.py -> results/calibration/nyiso115_transfer_queue_adjudication.json)" },
    coal_peak_offer_margin: { cell: "." },
    coal_perplant_offer_level: { cell: "." },
    coal_offer_level_rebasis: { cell: "." },
    tranche_startup_amortization: { cell: "K", ev: "nyiso-96 (docs/FINDING-nyiso96-ct-start-frequency-2026-07-29.md)" },
    measured_ct_heat_rates: { cell: "K", ev: "nyiso-89; FINDING-nyiso89" },
    measured_chp_heat_rates: { cell: "K", ev: "nyiso-120 (2026-08-04, results/calibration/FINDING-nyiso120-eastriver-scope-gate-2026-08-04.md; prereg PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md pushed BEFORE the derive was re-run and before either solve; probes scripts/probes/_nyiso120_eastriver_boundary.py + _nyiso120_scope_gate_ab.py; records _nyiso120_eastriver_boundary.json, _nyiso120_scope_gate_ab.json, _nyiso120_artifact_A.csv; runs 2026-08-04-nyiso-120a2-control-samehead / 2026-08-04-nyiso-120b-scope-gate). THE CELL STAYS K -- this is miso-122 SCOPE-GATE refinement applied INSIDE the K mechanism (rule 19 [R-ONE-MECH]), not a new verdict, no new ScenarioConfig field, and the derive was shipped UNMODIFIED (this session edited no derive code). IT ANSWERS miso-122 section 7 item 1 open question -- which meter is wrong about East River boundary -- and the answer is NEITHER: THEY AGREE. On NYISO own data (rule 25; MISO verdict filled no NYISO cell): KE1 eGRID CHPCHTI vs the CAMPD dark-boiler fuel = 13,629,047 / 13,493,031 = 1.0101, the SAME OBJECT to 1.0 %; KE2 CAMPD power-train fuel over eGRID PLNGENAN = 7.3763 against eGRID own credited 7.4205, ratio 0.9940 -- two INDEPENDENT meters agreeing to 0.6 % on the power-only rate. So PLHTIAN is ALREADY the power train fuel, PLHTRT = 7.4205 is ALREADY the power-only rate, and the (PLHTIAN + CHPCHTI) add-back DOUBLE-COUNTS the fuel of two Dry bottom wall-fired boilers (units 60 and 70) reporting EXACTLY ZERO gross load in every hour of 2023-2025. KE3 100.0 % of dark fuel is a boiler unitType all three years, share 37.51/30.79/30.64 %, max/min 1.22 -- machinery, not a reporting spike. Corroborated from the GENERATION side: CEMS gross 2,133,488 MWh vs eGRID net 3,078,707 MWh = 0.693, the miso-118 G_gross < 1 physical impossibility, i.e. ~0.95 TWh/yr of HRSG steam-turbine output CEMS never meters -- which is why 7.4 and not the naive CEMS-gross 10.6 is right. EFFECT: East River goes ok -> below_credited and its EFFECTIVE offer heat rate falls 11.8032 -> 7.4205 (-37.1 %) on 306 MW of NYC CT_CHP. KE4 no-op fidelity EXACT: one applied row changes, zero other flag changes, zero other applied-rate changes. DIRECTION is unambiguously DOWNWARD only because NYISO is NOT in CHP_STEAM_CREDIT_HR_CORRECTION_ISOS (CAISO, PJM) -- in a hand-factor ISO the identical exclusion would push the rate UP; asserted in the scorer, not assumed. A/B VERDICT LIVE: all six construction gates PASS, max zonal |dLMP| 0.1287/0.1371/0.3875 $/MWh clearing the 0.10 bar in 3 of 3 years, no zone lambda rises, CT_CHP +0.3113/+0.1921/+0.4214 TWh displacing ST_GAS/CC_REGULAR/CC_CHP. P1 free-class C1 does NOT regress (14/14 all, 10/10 free BOTH arms); P3/P4/P5/P6 pass; C3c bit-unchanged (CAVEAT both arms). P2 FIRES: C3a mean LMP FAILS on 2025 at exactly -10.0 % against a control that reads -9.5 % -- a 0.5 pp knife-edge crossing worth -0.39 $/MWh on a 60 $/MWh mean, while 2023 IMPROVES (+7.6 % -> +7.2 %) and 2024 stays deep inside band. The 2025 C3a gap is 6.68 $/MWh, so this correction is 6 % of it and 94 % is pre-existing. DETERMINATION control CALIBRATED-WITH-CAVEATS -> treatment NOT-YET. THE CORRECTED ARTIFACT SHIPS REGARDLESS (rule 14 [R-ACCURATE]; prereg section 4.1 declared the adverse-gate case IN ADVANCE), and arm B IS the recommended keeper candidate on the owner standing standard -- BUT THE PROMOTION IS STOPPED BY RULE 22 D-5(b): NYISO holds a calibration-complete complete marker, the re-verified determination is WORSE, and D-5(b) says a worse determination stops the promotion and escalates to the owner rather than being silently written. KEEPER UNCHANGED at 2026-08-03-nyiso-118-seny-span pending that call. CONTROL PROVENANCE, reported: the FIRST control (2026-08-04-nyiso-120a-control) solved at a PRE-rebase HEAD and failed KE5 with 3 differing config keys after main added caiso_zonal_loss_surface / ercot_energy_online_capability_cap / pjm_seam_envelope_by_neighbor; it is SUPERSEDED and no number is quoted against it. The re-solved same-HEAD control A2 is BYTE-IDENTICAL to the committed keeper, which is what proves those three fields are inert at NYISO. RULE 25: only NYISO artifact was re-derived; NEISO 1595 Kendall (206 MW, -1.2 %) stays in NEISO lane and NO cell outside NYISO is stamped. KEEPER MOVED MID-SESSION AND THE ARMS WERE RE-SOLVED ON THE RIGHT BASE: NYISO advanced 2026-08-03-nyiso-118-seny-span -> 2026-08-03-nyiso-119-seny-increment AFTER the first arms launched, so the nyiso-118-based treatment would have SILENTLY DISARMED nyiso_seny_rcpf_increment_step. Caught before it landed (the shard edit was made, checked and REVERTED); both arms re-solved on the nyiso-119 recipe as 2026-08-04-nyiso-120-c119-control / 2026-08-04-nyiso-120-c119-scope, and the promoted run carries nyiso_seny_rcpf_increment_step = True (verified). THE RESULT REPLICATES on the correct base -- six gates PASS, LIVE, max zonal |dLMP| 0.1278/0.1379/0.3887, CT_CHP +0.3103/+0.1927/+0.4213 TWh, C1 unchanged, P2 fires on C3a, 2025 -9.5 % -> -10.1 % and 2023 +7.6 % -> +7.2 % -- so the finding is a property of the INPUT, not of the recipe. OWNER RULED PROMOTE on the D-5(b) escalation: NYISO keeper -> 2026-08-04-nyiso-120-c119-scope, determination NOT-YET written explicitly into calibration-complete.json, audit_keepers --iso NYISO PASSES 0 failures / 0 warnings, ledgered-caveat budget UNSPENT at 1 of 3 (the C3a FAIL is a criterion failure, not a ledger entry)." },
    da_virtual_bids: { cell: "G", ev: "nyiso-94 (docs/FINDING-nyiso94-da-virtual-not-identifiable-2026-07-28.md)" },
    negative_renewable_offers: { cell: "." },
    wind_ptc_vintage_offers: { cell: "." },
    gas_offer_curve_tranches: { cell: "K" },
    gas_monthly_actuals: { cell: "K" },
    gas_plant_monthly_pricing: { cell: "K" },
    gas_daily_shape: { cell: "K" },
    zonal_gas_basis: { cell: "K" },
    gas_hub_basis_overlay: { cell: "K" },
    winter_citygate_daily: { cell: "." },
    dual_fuel_switching: { cell: "K" },
    gas_price_override: { cell: "K" },
    coal_plant_monthly_pricing: { cell: "K" },
    campd_outage_windows: { cell: "K" },
    outage_artifact_provenance: { cell: "I", ev: "xiso-2 §3.1 row 3 (nyiso-81 post-guard) + §4" },
    dam_availability_rebasis: { cell: "." },
    pjm_measured_outage_event_cap: { cell: "." },
    ercot_dam_availability_coal_event_cap: { cell: "." },
    ercot_dam_availability_gas_event_cap: { cell: "." },
    ercot_dam_availability_event_cap_reconciliation: { cell: "." },
    ercot_dam_availability_event_cap_unit_scoped: { cell: "." },
    ercot_partial_outage_shaped_derate: { cell: "." },
    unit_outage_short_windows: { cell: "I", ev: "nyiso-93 (docs/FINDING-nyiso93-unit-availability-windows-inert-2026-07-28.md)" },
    nuclear_unit_availability: { cell: "K", ev: "nyiso-98 (docs/FINDING-nyiso98-nuclear-availability-2026-07-29.md; PREREG docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md)" },
    temp_dependent_derate: { cell: "G", ev: "nyiso-111 (ex-ante refusal on NYISO's own conduct, no solve — FINDING-nyiso111-ramp-envelopes-2026-08-02.md §2)" },
    gas_coldsnap_derate: { cell: "." },
    nysdec_peaker_rule_availability: { cell: "K", ev: "nyiso-46 (armed once, stacked, never adjudicated); nyiso-112 (row added + single-delta re-test)" },
    wefor_statistical_stack: { cell: "K" },
    correlated_forced_outage: { cell: ".", fc: "I" },
    retiree_cems_cap: { cell: "." },
    solar_deliverability: { cell: "." },
    vre_avg_cf_level: { cell: "K", ev: "nyiso-132 (FINDING-nyiso132-solar-cf-level-2026-08-07.md); nyiso-130 prereg §2-§3" },
    vre_market_generator_basis: { cell: "K" },
    vre_registry_cod_date_basis: { cell: "K", ev: "nyiso-133 (FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md; PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md; probes _nyiso133_commissioning_ramp.py + _nyiso133_ab_gates.py; records _nyiso133_commissioning_ramp.json + _nyiso133_ab_gates.json); nyiso-135 PROMOTED O -> K on the owner ruling, no solve (ASSESSMENT-nyiso135-promotion-2026-08-15.md); nyiso-136 COLLAPSED THE GATE TO UNCONDITIONAL on a second owner ruling (rule 26 [R-DELETE]), so no fc posture is carried — the ScenarioConfig field is DELETED and BOTH lanes now read the EIA-860 Operating Month basis, at the declared cost of re-staling the forecast lane's 11 committed nyiso-* hindcast sidecars" },
    wtx_curtailment_driver: { cell: "." },
    wtx_curtail_unpooled: { cell: "." },
    hydro_dispatch_envelope: { cell: "K", ev: "nyiso-92 / FINDING-nyiso92-hydro-capability-envelope-2026-07-28.md" },
    hydro_min_flow_floor: { cell: "K", ev: "nyiso-92 / FINDING-nyiso92-hydro-capability-envelope-2026-07-28.md" },
    hydro_ror_split: { cell: "G", ev: "nyiso-111 (classifier review ANSWERED, falsified ex-ante, no solve — FINDING-nyiso111-ramp-envelopes-2026-08-02.md §3)" },
    hydro_budget_nameplate_aware: { cell: "I", ev: "nyiso-106 (basis audit, no solve) / nyiso-107 (I: provably inert, input truncation found — FINDING-nyiso107-hydro-input-truncation-2026-07-31.md)" },
    hydro_level_923_hy: { cell: ".", ev: "neiso-72 (FINDING-neiso72-hydro-ps-window-2026-07-31.md; probe _neiso72_ps_window_audit.py)" },
    hydro_vintage_input_repair: { cell: "K", ev: "nyiso-107 (defect found, chartered) / nyiso-108 (K, promoted — FINDING-nyiso108-hydro-input-repair-2026-07-31.md)" },
    ercot_wind_zone_shape: { cell: "K" },
    battery_dispatch_adder: { cell: "." },
    ercot_storage_rt_offer_surface: { cell: "." },
    storage_measured_base_fleet: { cell: ".", fc: "." },
    caiso_storage_nqc_accreditation: { cell: ".", fc: "." },
    caiso_ra_mpb_capacity_anchor: { cell: ".", fc: "." },
    storage_vintage_ramp: { cell: "I", ev: "nyiso-115 (ex-ante transfer adjudication, 0 solves; scripts/probes/_nyiso115_transfer_queue_adjudication.py -> results/calibration/nyiso115_transfer_queue_adjudication.json)" },
    storage_measured_anchors: { cell: "." },
    storage_daily_cycling: { cell: "." },
    pumped_storage_cycling_depth: { cell: "U" },
    caiso_da_rt_two_settlement: { cell: "." },
    caiso_ps_charge_shape_anchor: { cell: "." },
    caiso_ps_plant_params: { cell: "." },
    measured_interface_limits: { cell: "G", ev: "nyiso-109 (refused ex-ante on NYISO's own MIS P-32 flow-vs-limit measurement; results/calibration/_nyiso109_trough_offer_stack.json)" },
    internal_congestion_split: { cell: "." },
    tsa_transfer_derate: { cell: "G", ev: "nyiso-95 (docs/FINDING-nyiso95-tsa-derate-not-identifiable-2026-07-28.md)" },
    scuc_load_pocket_commitment: { cell: "G", ev: "nyiso-97 (docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md)" },
    pjm_congestion_star: { cell: "." },
    pjm_apsouth_cut: { cell: "." },
    pjm_external_net_position_cut: { cell: "." },
    zonal_loss_surface: { cell: "." },
    rdt_tcdc: { cell: "." },
    seam_flow_envelopes: { cell: "K", ev: "nyiso-125 (2026-08-04) — CELL U -> K, PROMOTED. KEEPER 2026-08-04-nyiso-125-seam-envelope arms nyiso_seam_deliverability_envelope against its own same-HEAD control 2026-08-04-nyiso-125-control, 2023-2025 in one bundle each. THE IDENTIFICATION REFUSAL IS AS LOAD-BEARING AS THE CONSTRUCTION, and it is what makes this NYISO's own cell rather than a transfer of PJM's (rule 25 [R-ISO-SCOPE], binding both ways). Phase 0 (scripts/probes/_nyiso125_seam_envelope.py, record _nyiso125_seam_envelope.json, NO LP) returns FOUR verdicts on NYISO's own MIS P-32 postings. (1) IDENTIFIED and ARMED on the two border links whose external ties land unambiguously in ONE NYISO load zone — NYC (Zone J: SCH - PJM_HTP + SCH - PJM_VFT) and Long_Island (Zone K: SCH - PJM_NEPTUNE + SCH - NPX_CSC + SCH - NPX_1385) — attribution-invariant, ZERO identification freedom; each trades its flat SYMMETRIC time-invariant static rating for the p90 of the directionally-clipped net schedule within each (month x hour-of-day) bin. (2) REFUSED ON IDENTIFICATION on Capital_Hudson and Upstate_West (rule 20 [R-DOF]): SCH - PJ - NY is the one posting row spanning the Central-East cutset (Ramapo/Waldwick into Zone G east; Homer City-Stolle Road/Falconer into Zone A west), NEITHER NYISO's P-32 NOR PJM's own tie file separates the legs (PJM buckets all four NYISO-facing ties as NYIS/NEPT/HUDS/LIND, every AC tie in the single NYIS row), and the split brackets Capital_Hudson's import envelope across 45-955 / 0-916 / 0-1,134 MW in 2023/24/25 — the WHOLE range that matters, on the link carrying the defect. Those links keep their statics; nothing is approximated or parked behind a default-off knob (rule 26 [R-DELETE]). (3) The POSTED-LIMIT envelope — the stronger rule 13 object, and FULLY identified — is REFUTED as the repair: the three AC seams reach 95 % of their posted import limit in 0.0-0.1 % of hours in EVERY year, and a posted-limit cap would LOOSEN exactly the two links that over-deliver (Upstate_West >=3,650 vs the incumbent 3,000; Capital_Hudson 1,400 + the PJ share vs 1,600). A genuine rule 14 exception case: the accurate datum is real but MISALIGNED to what the model's border link represents. (4) The split-INVARIANT joint (Upstate_West + Capital_Hudson) cap is identified WITHOUT any attribution and PROVABLY INERT — the model's joint net import (+597/+80/-89 MW p50) already sits far below the measured envelope (1,818/1,706/1,243). SCH - HQ_IMPORT_EXPORT excluded as an ACCOUNTING DUPLICATE of SCH - HQ - NY (equal within 0.5 MW in 40.7/77.9/90.9 % of hours; the only SCH row carrying the +/-9,999 sentinel). ZERO free parameters, ZERO new numbers, DOF ledger 33 -> 34 entries with n_residual UNCHANGED at 6: the percentile is the repo-wide DEFINITIONAL convention (== MISO_SEAM_FLOW_PERCENTILE == PJM_SEAM_FLOW_PERCENTILE == 90.0, pre-registered NEVER-SWEPT) and the tie->landing-zone map is an identity off NYISO's own tie geography. THE EX-ANTE NUMERIC PREDICTION IS CONFIRMED IN ALL THREE YEARS AND OVERSHOOTS IN NONE: PREREG section 4.2 reasoned before solving that Capital_Hudson, already at its bound in ~100 % of hours, cannot absorb the displaced MW, so the 307/406/369 MW removed downstate must arrive at Upstate_West and reach load through Central East, closing ~30-40 % of the CE utilisation gap — measured CE util p50 0.467/0.197/0.255 -> 0.668/0.335/0.383 against a MEASURED 0.807/0.616/0.591, i.e. +59.1/+33.0/+38.0 % of the gap closed. (The measured CE utilisation is read PER YEAR from NYISO's own posting; nyiso-124's 0.591 is the 2025 value and using it for 2023 would misstate that gap ~2.4x — CORRECTED, not carried.) ALL SIX pre-registered kill gates SILENT (K1 largest zone-mean move +5.76 %; K2 ZERO new unserved energy; K3 C1 does not regress; K4 LIVE not inert at max |dLMP| $265.93/$106.21/$104.79; K5 four-link seam NET moves only +31/-98/+90 MW p50 so the monthly EIA-930 reconciliation band holds; K6 the control reproduces the keeper EXACTLY on C3a). C3c, THE SOLE LEDGERED CAVEAT, IMPROVES MATERIALLY: raw tail hours 3/0/14 -> 18/2/21 against actual 10/12/42, so on identical scoring the gate goes from failing ALL THREE YEARS to failing 2024 alone; no new caveat slot is spent (budget still 1 of 3). REPORTED AGAINST INTEREST: 2023's tail now OVERSHOOTS at 1.80x (18 h vs 10 h), inside the band but over-produced and named as an open item; and C3a-2025 moves -10.1 -> -10.2 %, marginally WORSE, so the C3a FAIL is NOT closed. Determination LABEL unchanged NOT-YET, substance better; rule 22 D-5(b) honoured (marker re-keyed, determination re-verified on committed artifacts before the promotion commit). The control also DISCHARGES nyiso-124's one provenance caveat by reproducing its seam diagnosis on the CURRENT keeper recipe (external>Upstate_West p50 -998/-1,520/-1,702 vs nyiso-124's -1,003/-1,520/-1,689); both arms commit hourly/network_<year>.parquet with git add -f. nyiso-100's SIL retirement is NOT re-opened and NO aggregate cap is introduced. Evidence: FINDING-nyiso125-seam-envelope-2026-08-04.md, PREREG-nyiso125-seam-envelope-2026-08-04.md, _nyiso125_seam_envelope.json, _nyiso125_gate_scores.json." },
    nyiso_seam_par_attribution: { cell: "R", ev: "results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md + PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md + PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md; probe scripts/probes/_nyiso127_par_phase0.py; record results/calibration/_nyiso127_par_phase0.json; intake data/raw/NYISO/par-data/" },
    import_hub_pricing: { cell: "K", ev: "keeper; nyiso-86 §3, nyiso-99 (FINDING-nyiso99 §2)" },
    import_shape_lever: { cell: "G", ev: "nyiso-99 (FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29), nyiso-86 §3" },
    nyiso_import_sil_retire: { cell: "K", ev: "nyiso-100 (FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30, PREREG-nyiso100, probe nyiso100_simultaneous_import_identification.py)" },
    nyiso_li_tsl_n11_security: { cell: "R", ev: "nyiso-130 (PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md; identification results/calibration/_nyiso130_li_tsl_identification.json, probe scripts/probes/_nyiso130_li_tsl_identification.py)" },
    nyiso_central_east_measured_ttc: { cell: "K", fc: "G", ev: "nyiso-104 (FINDING-nyiso104-central-east-ttc-classification-2026-07-30, probe nyiso104_central_east_ttc_classification.py, docs/backcast-measured-data-audit-2026-06.md)" },
    nyiso_gj_locality_tsl: { cell: "G", ev: "nyiso-101 (FINDING-nyiso101-gj-locality-boundary-2026-07-30, probe nyiso101_gj_locality_boundary.py); premise from nyiso-100 (FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30)" },
    caiso_firm_envelope_clip: { cell: "." },
    caiso_firm_selfsched_floor: { cell: "." },
    caiso_firm_selfsched_clip: { cell: "." },
    caiso_seam_loss_surface: { cell: "." },
    caiso_corridor_export_path: { cell: "." },
    caiso_node_export_constraint: { cell: "U", ev: "caiso-143 §G (precondition met: 1 sink + nyiso_firm_imports; sink pinned off today by the bridge, so arming the seam fix would OPEN it)" },
    caiso_p1_export_sink_seam: { cell: "O", fc: ".", ev: "caiso-142 §F measured exposure" },
    wecc_endogenous_node: { cell: "." },
    lcr_tsl_published: { cell: "K", fc: "U", ev: "nyiso-102 (docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md)" },
    demand_repairs: { cell: "." },
    path15_load_split: { cell: "." },
    tac_load_coverage: { cell: "U" },
    demand_dropout_screen: { cell: "K", ev: "nyiso-99 (FINDING-nyiso99, PREREG-nyiso99, probes nyiso99_import_benchmark_provenance / nyiso99_ab_compare)" },
    scr_edrp_dr: { cell: "K", ev: "keeper" },
    td_loss_factor: { cell: "R" },
    demand_growth_vintage: { cell: ".", fc: "O", ev: "FIRST NYISO-ARMED SOLVE: nyiso-2023-2025-t1ff-armk-fh4 (FH-4-NYISO 2026-08-10, docs/handoffs/fh-4-nyiso-leg-2026-08-10.md §1.3/§2; hindcast namespace, runtime key 30eedfd2d38e5b92, meta records demand_growth_vintage 2023) — NYISO 2024/2025 demand grown at the cited as-of-2023 Gold Book Table I-1a 0.54 %/yr instead of the live table 1.22 %/yr. CELL O — MEASURED IN THE ARM-K INSTRUMENT, NOT ADJUDICATED (no shipped default reads the vintage table). PHASE-B MEASURED 2026-08-11 BY FH-5 (docs/handoffs/fh-5-phase-b-2026-08-11.md §4-§5): second armed solve of this field, at base 2021 / vintage 2020 / window 2021-2025 — id nyiso-2021-2025-t1ff-armk-fh5 (hindcast namespace, runtime key cad3a7957dfefb55, meta records demand_growth_vintage 2021), so 2023-2025 demand grows at the cited as-of-2021 rate (-0.38 %/yr) rather than the live table's. Paired against Arm R (nyiso-2021-2025-t1ff-armr-fh5, key 0215407853b63c00). I6 rider PASSED on both arms. CELL STAYS AS-IS — MEASURED, NOT ADJUDICATED (no shipped default reads the vintage table)." },
    confirmed_exits: { cell: "K", fc: "K" },
    economic_retirement_screen: { cell: "R", fc: "R", ev: "FFR-3A-2 (docs/handoffs/ffr-3a2-battery-close-2026-08-03.md §3.7 — run nyiso-2021-2025-ffr3a2: D-1 is PROVABLY INERT in this window. retire.total_gw is 1.036 GW in BOTH arms, per-fuel identical (nuclear 1.036, all else 0.0), and the ledgers book EXACTLY ONE retirement across all five years: 2022, reason announced. Zero economic exits, so the screen never fires and the rule cannot move anything. Derived from the ISO's OWN evidence — rule 25 clean, NOT imported from FFR-3C MISO); FFR-3A-3 (docs/handoffs/ffr-3a3-battery-close-2026-08-04.md §2.3/§5 — run nyiso-2021-2025-realized-ffr3a3 INDEPENDENTLY CONFIRMS that inertness POST-FIX, in the strongest available form. The G3 cap-grain fix 2adfb49 changes the admitted exit set of this very screen, so a provably-inert mechanism PREDICTS the leg must not move — and EVERY band is identical to three decimals (retire.total_gw 1.036, recall PASS, false_retire PASS, wind 0.951 PASS, solar 0.891 FAIL). The ledgers again book EXACTLY ONE retirement across all five years (2022, reason announced) and ZERO economic retirements. §3.7 is therefore not merely un-invalidated by FFR-3A-2's provenance ceiling; it is confirmed by an experiment that had to move it if the claim were false. Rule 25 clean — NYISO's own artifact. CELL UNCHANGED, determination UNMOVED (HOLD))" },
    capacity_market_clearing: { cell: "O", fc: "O", ev: "FFR-2E §5 — WRONG-ARM FC-3 citation: shipped posture is curve-OFF, gate cites the force-ON probe leg" },
    net_cone_forward_vintages: { cell: "O", fc: "O" },
    reserve_margin_backstop: { cell: "K", fc: "K" },
    capacity_deliverability: { cell: ".", fc: "U" },
    storage_entry_value_stack: { cell: "K", fc: "K" },
    ccs_retrofit_screen: { cell: "K", fc: "K" },
    entry_lookahead_reprice: { cell: "K", fc: "K" },
    exit_rate_limits: { cell: "U", fc: "U" },
    entry_dampers: { cell: "U", fc: "U" },
    entry_pipeline_aware_signal: { cell: "U", fc: "U" },
    capacity_screen_unified_lookahead: { cell: "U", fc: "U" },
    capacity_screen_scarcity_restoration: { cell: "U", fc: "U" },
    entry_vre_capacity_revenue: { cell: "U", fc: "U" },
    vre_procurement_additions: { cell: "U", fc: "U" },
    smr_available_year: { cell: "U", fc: "U" },
    elcc_accreditation: { cell: "K", fc: "K" },
    caiso_nqc_accreditation: { cell: ".", fc: "." },
    hydro_accreditation: { cell: "K", fc: "K", ev: "FFR-1C (runs nyiso-2026-2026-ffr1c-i7-{before,after}); origin FF-2B §2.3/§4" },
    datacenter_load_block: { cell: "K", fc: "K" },
    electrification_layers: { cell: ".", fc: "U" },
    transmission_expansion: { cell: ".", fc: "U" },
    t1ff_solve_year_weather: { cell: ".", fc: "U" },
    rps_lp_constraint: { cell: "K", fc: "K" },
    miso_rps_compliance_regions: { cell: ".", fc: "." },
    miso_clean_tier_rows: { cell: ".", fc: "." },
    state_carbon_pricing: { cell: "K", note: "VERDICT UNCHANGED (K). RESOLVED 2026-08-14 (nyiso-134, same session): the coverage gap below is CLOSED — RGGI auctions A39-A58 landed, so STATE_CARBON_PRICE_BY_ISO now spans 2018-2025 for NYISO (2018 4.41 / 2019 5.42 / 2020 6.41 / 2021 9.47 / 2022 13.46 $/short ton) and for NEISO (x1.10231). Recipe verified first: recomputing 2023-2025 reproduces the committed constants EXACTLY. The intake-side blocker was removed too — curate_carbon_auction_results.py hard-coded _QUARANTINED_YEARS={2022,2026} and RAISED, the pre-2026-08-06 regime the owner replaced. CAISO's 2018-2022 CARB block is NOT covered (source blocks automated fetches; open CAISO-lane gap, rule 25), and NEISO's registered 2022 touchpoint is now stale w.r.t. HEAD. ORIGINAL FLAG, retained for the record: STATE_CARBON_PRICE_BY_ISO['NYISO'] carried 2023/2024/2025 ONLY, so any OUT-OF-TRAINING year silently charged $0/tCO2 — policy.carbon.state_carbon_price returns None and the keeper's carbon_price_path='zero' catches it, with no exception and no warning. Measured for 2022: $6.08/MWh omitted at ~$13/tCO2 on the fleet 0.4558 tCO2/MWh-net, 8.1% of the 2022 RT mean, and MERIT-ORDER distorting (CC $5.53 vs dry-bottom-wall steam $15.85, a 2.9x spread). Blocked the 2022 validation touchpoint; CLOSED the same session (see the RESOLVED note above), zero DOF. Evidence: results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md §2 D-1." },
    mass_cap_lp_row: { cell: "U" },
    ira_credits: { cell: "K", fc: "K" },
    federal_ces: { cell: ".", fc: "U" },
    plant_emission_rates_v2: { cell: "K", ev: "armed on every NYISO keeper (use_plant_emission_rates_v2 default True). nyiso-142 REPAIRED its input, not the mechanism -- Astoria (ORIS 8906) files units 30/50 as reheat/superheat stack pairs, repeating one generator's full grossLoad on both rows while splitting heat and masses, so its unit rates read 279-322 kg CO2/MWh against a 520-575 peer band. 18 rows folded onto their primaries across 2018-2026 by scripts/data/repair_v2_stack_duplicate_rows.py (every other row byte-frozen; MATCH vs a fresh emissions-unit-annual on all six rebuildable years). VERDICT UNCHANGED at K -- a data correction with zero DOF, no ScenarioConfig field and no flag; the paired A/B 2026-08-17-nyiso-142-control vs -stackdup differs by 0 of 718 config fields. Evidence FINDING-nyiso141-astoria-stack-duplication-2026-08-17.md, RESULT-nyiso142-astoria-stack-duplication-ab-2026-08-17.md" },
    startup_co2_reporting: { cell: "U" },
  },
};

/* NYISO column re-stamp history (newest last).
 *
 * 2026-08-14 — nyiso-134. NO CELL VERDICT MOVED, keeper UNCHANGED at
 *   2026-08-08-nyiso-132-cf-arm, open-gate set UNCHANGED (C3c still the sole
 *   ledgered caveat), lever queue UNCHANGED. Phase-1-only session: no LP was
 *   constructed or solved, no mechanism was tested, nothing was registered.
 *
 *   The session was the NYISO 2022 validation touchpoint, gated on a written
 *   proof of data readiness. THE PROOF FAILED and the solve was refused on the
 *   merits — three measured inputs the keeper consumes are DEGRADED for 2022
 *   relative to 2023-2025 and ALL THREE FAIL SILENTLY:
 *     D-1 state_carbon_pricing — RGGI table is 2023-2025 only, so 2022 charges
 *         $0/tCO2 (~$6.08/MWh, 8.1% of the 2022 RT mean, merit-order
 *         distorting). Flagged as a note on that cell; verdict unmoved.
 *     D-2 NYISO_INTERFACE_TTC_BY_{YEAR,MONTH} — 2023-2025 only, and BOTH
 *         appliers in pipeline/ttc.py silently return unchanged on a missing
 *         year, so a 2022 solve runs Central-East at the STATIC 2,850 MW
 *         POST-upgrade limit (+1,100 MW / +63% vs the model's own pre-upgrade
 *         1,750 MW) for a year BEFORE the Dec-2023 AC Transmission project
 *         energized, and loses the monthly envelope entirely. Lands directly on
 *         C3c: extra Central-East capability relieves the downstate congestion
 *         that forms the scarcity tail. No matrix row governs the TTC year
 *         tables, so no cell is stamped; the object is carried in the
 *         assessment and the calibration log.
 *     D-3 nyiso_scr_edrp — load_scr_edrp_enrollment clamps 2022 UP to the 2023
 *         Gold Book (2022 edition not on disk); ~1.23 GW of DR at a $500/MWh
 *         strike placed at the wrong vintage, bounded at ~60-190 MW by the
 *         observed +4.9%/+14.9% drift. Bounded, so no cell note.
 *
 *   PASSED, and worth recording because it was the designated highest risk: the
 *   CAMPD unit-outage extract reproduces EXACTLY — committed U layup == the
 *   no-guard re-derivation, disjoint, with ZERO only-in-committed orphans in
 *   every year 2018-2026 — so 2022 came from the SAME uniform detector pass
 *   with the SAME flags as 2023-2025 and the 2026-07-19 stale-vintage defect
 *   (the withdrawn marker) does NOT reproduce. The gas chain likewise passed
 *   the neiso-85 inversion test (2022 W-S +3.650, between 2023 and 2025) with
 *   the SOM anchor ratio 0.944 inside the in-sample band.
 *
 *   Holdout posture UNCHANGED: the spend freeze is ACTIVE and independently
 *   blocks every out-of-training solve; `complete` (validation only) untouched;
 *   NYISO stays ABSENT from `final`; 2018 / 2019 / H1-2026 not touched.
 *   Evidence: results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md,
 *   docs/calibration-log/nyiso.md 2026-08-14.
 */

/* 2026-08-14 (2nd stamp) — nyiso-134, owner directed "go get the data".
 * STILL NO CELL VERDICT MOVED, keeper UNCHANGED, no mechanism tested, no LP
 * solved. All three readiness defects are CLOSED with measured inputs spanning
 * 2018/2019-2022 (not just 2022), each on the incumbent producer + recipe, and
 * in every case the recipe was verified to reproduce the committed 2023-2025
 * values BEFORE the new years were written. Zero free parameters.
 *   D-1 RGGI  — auctions A39-A58 landed; STATE_CARBON_PRICE_BY_ISO now spans
 *       2018-2025 (NYISO + NEISO). The intake-side quarantine that CAUSED the
 *       gap (curate_carbon_auction_results _QUARANTINED_YEARS, the superseded
 *       pre-2026-08-06 regime) was removed. Cell note updated above.
 *   D-2 TTC   — 96 monthly MIS atc_ttc postings fetched; Central-East 2018-2022
 *       landed. WORSE THAN FIRST REPORTED: measured 2022 annual 1,825 MW vs the
 *       2,850 static fallback (+56 %), and Nov-2022 measured 725 MW = 3.9x. The
 *       appliers now FAIL LOUD for a year at/below the table's span while a year
 *       PAST it still no-ops (static == measured post-upgrade mean), so forecast
 *       runs are unaffected. No matrix row governs the TTC year tables, so no
 *       cell is stamped.
 *   D-3 SCR/EDRP — 2019-2022 Gold Book vintages landed (older editions sit under
 *       different Liferay doc IDs; the 2023+ URL pattern 404s). 2018 is
 *       MEASURED-ABSENT — that edition has no per-zone table at all — and was
 *       NOT fabricated from another year's shares (rule 14). A second hidden
 *       defect was found and fixed: nyiso_demand_response hard-coded the Gold
 *       Book bounds, so landing vintages changed nothing until they were derived
 *       from the CSV. 2022 moves 1234.4 -> 1169.8 MW summer DR.
 * Holdout posture UNCHANGED: the freeze is ACTIVE and is now the SOLE blocker on
 * the 2022 touchpoint; `complete` untouched; NYISO still ABSENT from `final`;
 * 2018/2019/H1-2026 not touched. Declared cross-lane effect: NEISO's registered
 * 2026-08-06-neiso-2022-corrected-basis is now stale w.r.t. HEAD (NEISO's call).
 * Evidence: results/calibration/ASSESSMENT-nyiso134-2022-readiness-2026-08-14.md §7.
 */

/* 2026-08-15 — nyiso-135 GOVERNANCE PROMOTION (committed by nyiso-136).
 * KEEPER -> 2026-08-08-nyiso-133-cod-arm, arming the market-solar in-service
 * DATE BASIS (nyiso_solar_registry_cod_dates). EXACTLY ONE CELL VERDICT MOVES:
 * vre_registry_cod_date_basis NYISO O -> K.
 *
 * NO SOLVE RAN and NO NEW MECHANISM WAS TESTED. nyiso-133 built, pre-registered
 * and A/B'd this arm and left it RECOMMENDED PENDING THE OWNER; the owner ruled
 * PROMOTE in session nyiso-135, verbatim: 'Is this a recommended keeper
 * candidate? If so plz promote. If structural integrity improves but gates
 * regress that may still be a keeper.' The structure-over-gates half of that
 * clause is NOT needed — no gated criterion regresses.
 *
 * THE MECHANISM. The Gold Book Table III-2a "In-Service Date" is a REGISTRATION
 * / INTERCONNECTION-SERVICE date that LEADS the plant's metered commercial
 * start; EIA-860's "Operating Month" matches that start. Rule 14 [R-ACCURATE]
 * in its RECONCILED-REAL-DATA form with ZERO free parameters (DOF 36 -> 37,
 * n_residual UNCHANGED at 6, identification "published"): two published
 * registries disagree on one field and a THIRD published series — EIA-923 first
 * metered output — adjudicates, agreeing with EIA-860 in 11 of the 12
 * uncensored plants, with the lead SIGNED BOTH WAYS (Darby -1, Stillwater -3
 * against Morris Ridge +2, High River +1, East Point +1). So it is a BASIS
 * DIFFERENCE, not a one-directional correction toward the residual. Membership
 * and nameplate stay 100 % Gold Book; only the switch-on month moves. The
 * crosswalk is a 15-row identity, each row verified on nameplate agreement and
 * DROPPED — keeping its published Gold Book date — rather than guessed when it
 * fails (Albany County Solar 2 is the one unmatched unit).
 *
 * ALL SEVEN PRE-REGISTERED GATES PASS. K1 exactly ONE differing
 * scenario_config field of 703; K2 zero slack/dump; K3 liveness
 * 1.0118 / 0.8746 / 1.0000 against EX-ANTE predictions of the same; K4 wind
 * identical; K5 no status regression; K6 C3c bit-unchanged; K7 C8 PASS with no
 * forced share rising (ST_GAS-2024 24.5 -> 24.4 %). Determination UNCHANGED at
 * CALIBRATED-WITH-CAVEATS, all 8 statuses identical, C3c the lone ledgered
 * caveat 1 of 1 and BIT-UNCHANGED at 21 / 3 / 24 h against actual 10 / 12 / 42,
 * re-verified per rule 22 D-5(b) so the worse-determination stop does not fire.
 * C3a +8.8 / +0.8 / -3.4 %. Hourly grain at full size: demand-weighted dLMP
 * -0.0023 / +0.0345 / 0.0000 $/MWh, max zonal |dLMP| 4.55 / 5.67 / 0.00. THE
 * CONTROL REPRODUCES THE SUPERSEDED KEEPER EXACTLY (max |class-year delta|
 * 0.000 GWh) on a MATCHING toolchain — no drift excuse available, unlike
 * nyiso-132 — and 2025 is BIT-IDENTICAL, the construction's own prediction
 * since the 2025 registry is flat and the two bases coincide.
 *
 * REPORTED AGAINST INTEREST. Solar vs the published Gold Book Net Energy goes
 * +20.9 / +33.2 / -0.1 % -> +22.3 / +16.5 / -0.1 % — 2024 improves by half and
 * 2023 GETS WORSE. Pre-registered as ADV-1 BEFORE the solve and expressly ruled
 * out as grounds for rejection: the band (calibration_verdict.VRE_TOL) is
 * REPORT-ONLY and D-10 classes NYISO solar "delivered_pinned" (advisory-only,
 * excluded from skill claims), so no gated criterion moves on it (rule 1
 * [R-STRUCT]). THE REPAIR SIGNATURE IS COHERENCE, NOT LEVEL: the implied fleet
 * CF the published energy demands goes from 0.1629 / 0.1473 (adjacent years
 * 10 % apart) to 0.1613 / 0.1641 (1.7 % apart) — a quantity nothing in the
 * construction targets. Disclosed: 2023 year-end registered capacity rises
 * 174.4 -> 194.4 MW (Stillwater meters 745 MWh in Dec-2023), so "year-end
 * capacity is invariant" holds for 2024 and 2025 only.
 *
 * REFUTED AND NOT BUILT (rule 26 [R-DELETE]). nyiso-132's named successor —
 * "the model has no commissioning curve" — was measured NATIONALLY before any
 * mechanism was written: 730 single-vintage EIA-860 OP PV plants >= 5 MW
 * (36.4 GW, COD 2019-2022) against their own EIA-923 monthly history, two-way
 * normalized, give age-0/1/2-month ratios 0.723 / 0.962 / 0.995 on a
 * 36-47-month PLACEBO of 1.0072. A new utility PV plant is at MATURE OUTPUT
 * FROM ITS SECOND MONTH and the entire shortfall is 0.321 month-equivalents
 * ~= 11 % of the effect it was named to explain.
 *
 * DEFERRED, FLAGGED, NOT DONE — and it is why fc stays O. nyiso-133 §9
 * recommends COLLAPSING THE GATE TO UNCONDITIONAL on promotion (a default-off
 * gate whose OFF position is the less accurate basis is a re-armable wrong
 * answer). It is NOT done: it is an OWNER DECISION with a NYISO FORECAST-LANE
 * blast radius — it re-stales that lane's 11 committed nyiso-* hindcast
 * sidecars (rule 15's separate namespace, its own governance). The promoted
 * keeper carries the flag TRUE in its own run_config.json, so the DESIGNATED
 * KEEPER is correct either way; only the DEFAULT is deferred.
 *
 * C3c IS NEITHER CLOSED NOR NARROWED: the tail is bit-unchanged, the diagnosed
 * owner is unchanged (100 % of the modelled tail is Long Island inside HB14-21
 * with both Zone-K import paths at their bound), and the successor remains the
 * CHARTERED JOINT reconciliation of the Zone-K transfer bound and the downstate
 * ST_GAS min_gen floor under rule 19 [R-ONE-MECH] — needing its own owner
 * charter AND pre-registration before any solve. DO NOT RE-TEST THE BARE NUMBER
 * SWAP: nyiso_li_tsl_n11_security is R, killed on gate K6 at nyiso-130.
 * FRONTIER UNCHANGED: cleared 2026-08-06, stays cleared, NOT re-asserted.
 * HOLDOUT POSTURE UNCHANGED: `complete` (validation ONLY), NYISO ABSENT from
 * `final`, ACTIVE spend freeze blocking every out-of-training solve, score and
 * registration. This promotion GRANTS, SPENDS AND RE-ARMS NOTHING.
 *
 * LEVER QUEUE. (1) the chartered JOINT Zone-K transfer-bound + downstate ST_GAS
 * min_gen reconciliation (rule 19), open. (2) the FLEET-CF COMPOSITION object
 * this promotion's own finding opens, REPLACING the refuted commissioning-curve
 * item: after the date repair 2023 and 2024 both imply fleet CF ~0.162 against
 * 2025's 0.1955, while measured mature per-plant CF is 0.174-0.182 for the
 * 2021-22 small fixed-tilt NY8 units and 0.198-0.221 for the 2024 tracking
 * plants (Morris Ridge 0.1998, High River 0.1983, East Point 0.2207) — one
 * ISO-wide RENEWABLE_AVG_CF cannot track a fleet going 100 % fixed-tilt ->
 * 56 % large tracking. Needs its own pre-registration (rule 19).
 *
 * Rule 25 [R-ISO-SCOPE]: NYISO's shard only. Evidence:
 * results/calibration/ASSESSMENT-nyiso135-promotion-2026-08-15.md,
 * FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md,
 * PREREG-nyiso133-market-solar-cod-basis-2026-08-08.md,
 * _nyiso133_ab_gates.json, _nyiso133_commissioning_ramp.json,
 * docs/calibration-log/nyiso.md 2026-08-15.
 */

/* 2026-08-15 (2nd stamp) — nyiso-136 RULE 26 [R-DELETE] COLLAPSE of the
 * market-solar in-service DATE BASIS gate. NO CELL VERDICT MOVES (the cell
 * went O -> K in the 1st stamp above, on the nyiso-135 promotion); what moves
 * is the DEFAULT, and the fc posture is dropped because there is no longer a
 * posture to differ.
 *
 * WHAT CHANGED. `ScenarioConfig.nyiso_solar_registry_cod_dates` is DELETED.
 * data/renewables.py now calls load_market_solar_monthly(..., cod_basis=True)
 * UNCONDITIONALLY, so every NYISO run in BOTH lanes ramps each registered
 * market-solar plant on its EIA-860 "Operating Month" (the metered commercial
 * start) and the Gold Book Table III-2a "In-Service Date" basis is no longer
 * reachable from any solve path. The CLI flags, the config plumbing and the
 * default-off tests go with it.
 *
 * WHY. Owner ruling, session nyiso-136, 2026-08-15, on nyiso-133 §9's own
 * standing recommendation and the gate's own in-code note: a default-off gate
 * whose OFF position is the LESS ACCURATE basis is a re-armable wrong answer
 * (rule 26 [R-DELETE]). nyiso-135 promoted the armed run to keeper; leaving the
 * DEFAULT on the superseded basis left the wrong answer one flag away.
 *
 * DECLARED COST, ACCEPTED BY THE OWNER IN THE SAME RULING. This re-stales the
 * NYISO FORECAST lane's 11 committed nyiso-* hindcast sidecars (rule 15's
 * separate namespace, its own governance — they stand as PRE-EPOCH evidence
 * until that lane re-runs them). This is exactly the cost nyiso-133 and
 * nyiso-135 both flagged and declined to incur without an owner decision.
 *
 * CACHE. SAME-KEY BEHAVIOURAL FLIP, and it is recorded as such: the field was
 * registered in _CACHE_KEY_OPTIONAL_FIELDS and held its False default, so it
 * was ALREADY dropped from the hash — deleting it leaves the pinned default key
 * 603c2498bf71d21d byte-stable (measured both ways). No _CACHE_KEY_RETIRED_FIELDS
 * entry is owed and adding one would be the bug: that dict RE-INSERTS the name
 * and MOVES the key (measured: 6f8050582a752f5a). A pre-2026-08-15 NYISO bundle
 * and a post one therefore hash IDENTICALLY under a changed basis, which is the
 * D-13 / FFR-3A same-key collision in its pure form — see the 2026-08-15
 * cache-epoch entry in market_sim/results/cache.py for exactly what is
 * invalidated and what is not.
 *
 * NOT AFFECTED. The designated keeper 2026-08-08-nyiso-133-cod-arm already
 * solved with the flag True in its own run_config.json, so it is ALREADY on the
 * post-collapse basis and its determination is untouched
 * (CALIBRATED-WITH-CAVEATS, C3c the lone ledgered caveat, bit-unchanged at
 * 21 / 3 / 24 h). Its paired control is pre-epoch by construction and is kept as
 * the A/B baseline, not as a current-basis run. Rule 25 [R-ISO-SCOPE]: NYISO
 * only — the loader returns None for any other ISO, and NEISO carries the
 * identical Tier-3 posture and is explicitly NOT covered (U). Frontier stays
 * CLEARED (2026-08-06). Holdout posture UNCHANGED: `complete` is validation
 * ONLY, NYISO stays ABSENT from `final`, and the ACTIVE spend freeze was
 * re-confirmed HELD by the owner in this same session — 2022 was not solved,
 * scored or registered.
 *
 * NO SOLVE RAN for this collapse. Evidence:
 * results/calibration/ASSESSMENT-nyiso135-promotion-2026-08-15.md §4 item 2,
 * FINDING-nyiso133-market-solar-cod-basis-2026-08-08.md §9,
 * docs/calibration-log/nyiso.md 2026-08-15.
 */

/* 2026-08-15 (3rd stamp) — nyiso-136 REFUTES the FLEET-CF COMPOSITION object.
 * NO LP SOLVED, no run registered, KEEPER UNCHANGED, NO CELL VERDICT MOVED, no
 * pre-registration filed — there is no mechanism to pre-register.
 *
 * The owner chose this lever (nyiso-133's own named successor, carried in the
 * lever queue by ASSESSMENT-nyiso135-promotion-2026-08-15.md §2). The
 * identification a pre-registration would have to rest on was measured FIRST,
 * on published data already committed, and it REFUTED the object on all three
 * of its factual premises. This is the nyiso-133 pattern applied to nyiso-133's
 * own successor: measure the named cause before writing a mechanism for it.
 *
 * THE OBJECT: 'measured mature per-plant CF is 0.174-0.182 (2021-22 small
 * fixed-tilt NY8) vs 0.198-0.221 (2024 tracking: Morris Ridge, High River, East
 * Point), so one ISO-wide RENEWABLE_AVG_CF cannot track a fleet going 100 %
 * fixed-tilt -> 56 % tracking.' The CF LEVELS all reproduce. The TECHNOLOGY
 * LABELS attached to them do not.
 *
 * P1 FALSIFIED IN PART — HIGH RIVER IS FIXED TILT. 90 MW, the second-largest
 * plant and ~16 % of the 2025 fleet, named by the object as one of the three
 * "2024 tracking" plants. EIA-860: Fixed Tilt? = Y, Single-Axis Tracking?
 * blank, Tilt Angle 18 deg (every tracking plant in the fleet reads 0 or blank).
 *
 * P2 FALSIFIED — the span is ~35 % -> ~56 % tracking, not 0 % -> 56 %.
 * Branscomb (COD 2021-12) and Regan (COD 2022-12), two of the units the object
 * calls "small fixed-tilt NY8", are single-axis tracking. Tracking share of
 * capacity-months: 34.8 % (2023) / 41.7 % (2024) / 56.1 % (2025). The end point
 * is right; the start point — the half that makes the swing large — is not.
 *
 * P3 FALSIFIED — the tracking flag has NO explanatory power in this fleet.
 * Over mature (age >= 2, the nyiso-133 threshold) NON-ZERO months: FIXED n=7
 * mean 0.1854 range 0.1639-0.2170; TRACKING n=5 mean 0.1856 range
 * 0.1515-0.2091. The means differ by 0.0002. The HIGHEST-CF plant in the fleet
 * is FIXED TILT (Calverton 0.2170) and the LOWEST is TRACKING (Regan 0.1515).
 * The capacity-weighted gap that does exist is carried entirely by Morris Ridge
 * and East Point being large and recent — a VINTAGE covariate, not a mounting
 * one. What the object grouped was COD vintage, labelled with an assumed
 * technology its own registry contradicts.
 *
 * THE CEILING — 38 %. Granting strictly more than the mechanism asks (EVERY
 * plant carrying its OWN measured mature CF, a superset of any per-technology
 * weighting), the capacity-month-weighted composite runs 0.1794 / 0.1869 /
 * 0.1923 against implied 0.1613 / 0.1641 / 0.1955: a +0.0129 swing against
 * +0.0342, i.e. 38 % of the named effect, while OVER-stating 2023 and 2024 by
 * +11 % and +14 %. The same test retired nyiso-132's commissioning curve at
 * ~11 %.
 *
 * A HYPOTHESIS RAISED AND KILLED IN THE SAME SESSION, recorded because it was
 * tested: the composite sitting ~11 % above the Gold Book's implied CF looks
 * like the benchmark-basis defect chartered for hydro at 5.5 item 11b. FALSE —
 * over the same crosswalked plants the two published series AGREE where both
 * are complete (EIA-923 / Gold Book 1.001x in 2023, 1.028x in 2024). 2025 is a
 * preliminary EIA-923 vintage (4 of 12 online plants filed) and is EXCLUDED,
 * not averaged in.
 *
 * WHAT THE SAME MEASUREMENT FOUND INSTEAD — NAMED, SIZED, NOT BUILT. Against
 * each plant's own mature CF the shortfall is 10.2 % (2023) and 5.5 % (2024),
 * and its largest single IDENTIFIED component is FULL-MONTH ZERO OUTPUT AT A
 * MATURE PLANT: 43 % of 2023 (Regan, five consecutive months Mar-Jul) and 30 %
 * of 2024 (Grissom, three consecutive months Mar-May). The model cannot
 * represent that at all — derive_cf_profile normalizes the EIA-930 shape to a
 * FLAT annual mean CF and applies it to the FULL registered nameplate every
 * hour, with no availability derate anywhere on the VRE path, while the thermal
 * fleet carries THERMAL_AVAILABILITY / WEFOR and a measured CAMPD outage layer.
 * It is a rule 1 [R-STRUCT] structural-fidelity item and NOT a gate instrument,
 * and the finding argues AGAINST spending a solve on it: it is ~11 GWh on a
 * 230 GWh fleet, on a band VRE_TOL marks REPORT-ONLY for a class D-10 marks
 * `delivered_pinned`; deriving an EFOR from two observed plant-outages would be
 * fitting to two events (rule 21); and it leaves most of both residuals
 * unexplained anyway.
 *
 * NO ROW IS ADDED. Rule 28 stamps mechanisms that exist; no mechanism was
 * built, exactly as nyiso-133 added no row for the refuted commissioning curve.
 * RENEWABLE_AVG_CF["NYISO"]["solar"] is UNTOUCHED at 0.1955 — it is the measured
 * MATURE-fleet CF and this finding gives no admissible basis to move it.
 * Frontier stays CLEARED (2026-08-06) and is NOT re-asserted: the queue is not
 * cleared, and this session OPENED an object while retiring another. Holdout
 * posture UNCHANGED, freeze re-confirmed HELD by the owner in session.
 *
 * LEVER QUEUE: (1) the chartered JOINT Zone-K transfer-bound + downstate ST_GAS
 * min_gen reconciliation (rule 19), still open, still needs its own owner
 * charter AND pre-registration — do NOT re-test the bare number swap
 * (nyiso_li_tsl_n11_security is R, killed on K6 at nyiso-130). (2) VRE
 * availability / forced-outage representation, newly named and sized here.
 * (3) FLEET-CF COMPOSITION is RETIRED, joining the commissioning curve.
 *
 * Evidence: results/calibration/FINDING-nyiso136-fleet-cf-composition-refuted-2026-08-15.md,
 * probe scripts/probes/_nyiso136_fleet_cf_composition.py,
 * record results/calibration/_nyiso136_fleet_cf_composition.json,
 * docs/calibration-log/nyiso.md 2026-08-15.
 */

/* 2026-08-15 (4th stamp) — nyiso-136 CARRIES FORWARD the NYISO-RTD-CLOCK
 * DISCLOSURE onto the current keeper. NO CODE CHANGED, no product re-derived,
 * no year re-scored, no cell verdict moved. This stamp exists because the
 * disclosure was recorded in a handoff ADDENDUM and NOWHERE in this lane's
 * governance — not in keepers/NYISO.json, not in calibration-complete.json, not
 * in the calibration log, not in this shard — and because THIS session
 * superseded the only keeper it named.
 *
 * THE DEFECT (adjudicated 2026-08-15, session nyiso-rtd-clock; ADDENDUM to
 * docs/handoffs/d32-f6fix-2026-08-13.md). NYISO's P-24A 'Time Stamp' is
 * interval-ENDING. scripts/data/derive_actual_lmp.py::_nyiso_wide bins it as
 * interval-BEGINNING (plain .floor(h)) and is the producer of the committed
 * data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet. The clean-side
 * curate_lmp.parse_nyiso_zip is already CORRECT. Adjudicated not by prose —
 * NYISO publishes no definition of the column — but by NYISO's OWN arithmetic:
 * P-4A is published as the hourly integration of the P-24A 5-minute prices
 * (Manual 12 p.136, Manual 14 §4, A536 §3.2.2), so binning P-24A under each
 * candidate convention and comparing to P-4A DECIDES it. Over 11 zones and 9
 * months spanning 2022-2025 including both DST transitions: ENDING max |d|
 * 0.0050 with ZERO zone-hours outside 2-decimal rounding; BEGINNING mean 1.1575,
 * max 151.67, 62,598 of 64,889 zone-hours WRONG. Corroborated three ways (the
 * daily file spans 00:05..24:00; ex-post posting is incompatible with
 * beginning-labels; a live 2026-08-14 fetch).
 *
 * WHY IT LANDS ON THIS LANE. The scorer
 * (render_calibration_html._actual_lmp_hourly / _actual_rt_padded) loads that
 * parquet and PREFERS THE `rt` COLUMN. That is the actual series C3a, the
 * demand-weighted monthly MAE and THE C3c SCARCITY TAIL are scored against.
 * Measured movement, read-only, input side only: 2022 97.8 % of hours move,
 * mean |d| $1.98, max $257.21 — but annual mean RT moves only -$0.024 and the
 * top-100-hour mean -$0.49. ALMOST EVERY HOUR MOVES AND THE LEVEL BARELY DOES:
 * one sample in twelve swaps per hour, so LEVEL statistics are near-invariant
 * and what moves is HOUR-BY-HOUR ALIGNMENT — correlation-sensitive metrics and
 * ANY PER-HOUR TAIL COUNT.
 *
 * WHAT IS AND IS NOT AT RISK, stated rather than absorbed:
 *   AT RISK — the ACTUAL side of the C3c ledgered caveat (10 / 12 / 42 h >$300)
 *     is a per-hour tail count taken from this series.
 *   AT RISK — the chartered JOINT Zone-K transfer-bound + downstate ST_GAS
 *     min_gen reconciliation, the lane's remaining lever, is a C3c object whose
 *     nyiso-130 kill gate K6 is itself a per-hour tail count. A future session
 *     must NOT tune that lever against this series without saying so.
 *   NOT AT RISK — the nyiso-133 A/B's C3c finding. It is BIT-UNCHANGED between
 *     arm and control, and both arms score against the SAME actual, so the
 *     comparison is invariant to the binning. The promotion's claim that no C3c
 *     evidence moved stands.
 *   NOT AT RISK — C3a levels (near-invariant, -$0.024 annual mean), and the DA
 *     block, so the spec.py import ladder needs no re-derivation.
 *   NOT AT RISK — nyiso-136's fleet-CF refutation, which is entirely input-side
 *     (EIA-860 registry + EIA-923 metered energy) and touches no LMP series.
 *
 * KEEPER RE-POINTED. The addendum names 2026-08-08-nyiso-132-cf-arm as the
 * keeper scored against the mis-binned series. THIS SESSION SUPERSEDED IT: the
 * disclosure now attaches to 2026-08-08-nyiso-133-cod-arm, which is scored
 * against the same parquet and inherits it unchanged.
 *
 * NOT REPAIRED, AND DELIBERATELY SO. The fix is a one-line change
 * ((idx - 1s).floor(h)) but it is OWNER-GATED and DATA-BLOCKED: re-deriving
 * actual_lmp_hourly_NYISO.parquet needs the NYISO RT source zips re-staged and
 * only 22 monthly zips are on disk against a 2018-2026 parquet. Do NOT
 * re-derive the parquet on partial coverage. The owner decision the addendum
 * requests is unchanged and still outstanding: correct _nyiso_wide, re-derive,
 * then re-score the NYISO keeper and re-verify its determination (rule 22 /
 * D-5(b)). Rule 14 [R-ACCURATE] points at the repair: a worse fit after it
 * would be a discovered bug, not a reason to keep a mis-binned series.
 *
 * Evidence: docs/handoffs/d32-f6fix-2026-08-13.md ADDENDUM §§A.1-A.7,
 * instrument scripts/probes/nyiso_rtd_clock_adjudication.py (read-only),
 * docs/calibration-log/nyiso.md 2026-08-15.
 */

/* 2026-08-16 — nyiso-137 GRADES the NYISO-RTD-CLOCK disclosure against the
 * JOINT Zone-K lever, and CORRECTS the 4th stamp above. NO LP SOLVED, no run
 * registered, no keeper moved, no cell verdict moved, no pre-registration
 * filed, no product re-derived. Identification before mechanism, the nyiso-136
 * shape. Probe scripts/probes/_nyiso137_rtd_clock_c3c_grading.py, record
 * results/calibration/_nyiso137_rtd_clock_c3c_grading.json. Rule 22 -- 2023-2025
 * only; the twelve 2022 zips are on disk and were deliberately NOT read.
 *
 * CORRECTION TO THE 4th STAMP. It asserts that the joint Zone-K lever is at
 * risk because 'its nyiso-130 kill gate K6 is itself a per-hour tail count'.
 * THAT IS FALSE. K6 is the FORCING gate -- its prereg text reads 'any D-2
 * mechanism's forced share rises, or nyiso_local_selfsupply reappears for
 * Long_Island, or C8 flips', and what fired it at nyiso-130 was forced ENERGY
 * in TWh (reliability_floor x ST_GAS 2.784->3.002, 2.797->3.216,
 * 2.371->2.598). The per-hour tail count is C3c, a CRITERION -- and nyiso-130
 * §8 already fixed that the promote test runs on K1-K6 plus
 * C1/C2/C3a/C3b/C4/C6/C8 'whatever C3c does'. The two things sit on opposite
 * sides of the promote rule.
 *
 * ALL SIX KILL GATES ARE MODEL-SIDE AND INVARIANT. K1 config diff, K2
 * slack/dump, K3 in-window limit_up, K4 other links' bounds, K5 control-vs-
 * treatment external-link ENERGY, K6 D-2 forced share + C8 -- every one read
 * from the arms' OWN bundles, none from actual_lmp_hourly_NYISO.parquet. K5
 * was the only candidate and is clean twice over: _nyiso130_ab_gates.k5_seam
 * sums link MW from each arm's network parquet, and the model's import PRICING
 * path (model/interchange/nyiso.py:105-108) reads only the PJM and NEISO
 * neighbour series, never NYISO's own file. SO THE DISCLOSURE DOES NOT BLOCK
 * LEVER (a).
 *
 * THE PROMOTE CRITERIA THAT DO READ THE SERIES ARE MEASURED SAFE. On 6,018
 * whole staged in-training hours, 94.0 % move but the pooled mean shifts
 * -0.0353 % (29.1725 -> 29.1622) and the worst single month -0.5063 %. C3a's
 * band is +/-10 % with a nearest margin of 1.2 pp; C3b's monthly NRMSE ceiling
 * is 0.20. Neither is reachable.
 *
 * WHAT IS AT RISK IS WORSE THAN THE ADDENDUM SAID. ADDENDUM §A.6 concluded
 * 'the C3c tail region moves by cents'. REFUTED. The delta is heteroskedastic
 * in price: mean |d| is $0.4237 over all hours but $17.22 above $100, $30.99
 * above $200 and $35.55 above $300 -- an 84x ratio for the tail's own region.
 * The addendum missed it because every statistic it quoted is a SIGNED mean
 * (-$0.024 annual, -$0.49 top-100), and signed means cancel. Zero staged hours
 * crossed $300, but all three staged tail hours started far from it
 * ($450.22->$377.79, $593.16->$598.10, $392.26->$362.98).
 *
 * C3c VERDICT REACHABILITY, the durable number. Staged months hold only 1 of
 * 10, 3 of 12 and 2 of 42 actual tail hours, so a direct recount is impossible
 * and was not attempted. Instead a CEILING: an hour can only change the count
 * by crossing $300, so the population within +/-$72.43 (the tail region's own
 * measured max) bounds it. Reachable actual counts are [5, 21] / [10, 21] /
 * [34, 82] against committed 10 / 12 / 42. Against the keeper's model
 * 21 / 3 / 24, through calibration_verdict's exact rule:
 *   2023 FAIL (2.10x) -> PASS at actual 11 h. ONE HOUR.
 *   2024 FAIL (0.25x) -> STABLE; PASS needs actual <=9, below the ceiling.
 *   2025 PASS (0.571x) -> FAIL at actual 49 h. SEVEN HOURS.
 * The 2023 edge is doubly sharp -- actual 10 sits exactly ON TAIL_SMALL_COUNT,
 * so one hour DOWN also switches the scoring rule from ratio to absolute
 * difference. DIRECTION NOT CLAIMED: the staged tail moves net downward
 * (1 up / 2 down) which would preserve both verdicts, but n=3 is not a rate
 * (rule 21). The ceiling governs, not the direction.
 *
 * DISPOSITION. The charter request stands and is filed at
 * docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md, carrying a
 * condition: the arm-vs-control C3c DELTA is invariant (both arms score against
 * the same actual) and may be relied on; ABSOLUTE C3c band membership may not,
 * and any C3c-turning claim is reported as CONDITIONAL on the clock repair.
 * The repair itself stays OWNER-GATED and DATA-BLOCKED -- unchanged.
 *
 * Evidence: results/calibration/FINDING-nyiso137-rtd-clock-graded-against-zone-k-gates-2026-08-16.md,
 * docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md,
 * docs/calibration-log/nyiso.md 2026-08-16.
 */
