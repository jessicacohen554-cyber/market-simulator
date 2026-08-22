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
  updated: "2026-08-22",
  keeper: "2026-08-22-nyiso-149-duty-curve",
  gates: "(2026-08-22, session nyiso-149) KEEPER PROMOTED: 2026-08-22-nyiso-149-duty-curve — the FIRST NYISO run to read CALIBRATED on the AUTHORITATIVE benchmark (C1 14/14 incl. CC_REGULAR-2024, the criterion that made 146c NOT-YET; C2/C3a/C3b/C4/C6/C8 PASS; C3c the single ledgered caveat, 1/0/0 h vs RT 10/13/42 h). TWO measured zero-DOF fields over the 146c lineage: nyiso_chp_btm_measured (nyiso-147) + chp_layup_duty_curve (nyiso-149). audit_keepers --iso NYISO PASS 0/0; rule-22 D-5(b) marker re-key executed (determination IMPROVES NOT-YET -> CALIBRATED, stop does not fire; marker_reexamination_open premise noted RESOLVED, owner closure pending). THE BENCHMARK ROOT CAUSE IS CLOSED this session (Job 1, owner-chartered): FINDING-nyiso149-bench-root-cause-2026-08-22.md — the 2026-08-17->08-21 classFull drift was commit 01db36d's flag-dependent BTM subtrahend re-arming the ±3% EIA-930 family reconcile (x1.069/x1.117/x1.189 on the gas classes; the EIA-923/CAMPD-backfill frame NEVER MOVED, content-hash 920c8b8bc1b1 identical at both ends); the regenerated (measured-BTM) reconciliation is ruled CORRECT on mechanism evidence (the plants' own meters; EIA-923+CAMPD agrees with EIA-930 unscaled only under it) and PINNED flag-independent (btm_bench_twh), so the shared bench part can no longer flip with a registering run's config. nyiso-148 §2's 'none of it is the flag' is corrected by addendum (its flag-flip test was blind to btm.parquet, which rebuild_benchmark does not rebuild). WHAT REMAINS OPEN: the 2025 offer-level object ($6.57 of the base's $8.07 gap — owner card DECISION-CARD-nyiso148-2025-level-remainder, Q1 pending); C3c; the zonal gradient (ASSESSMENT-nyiso148 §2.3); Flynn start counts; RHO_CLIP / Iroquois / D-4 vintage guard / Astoria (out of lane). Holdout: complete (validation only), ABSENT from final, spend freeze ACTIVE and untouched — every year solved this session is 2023/2024/2025. Evidence: FINDING-nyiso149-bench-root-cause-2026-08-22.md, PREREG-nyiso149-chp-duty-curve-2026-08-22.md (+§7), RESULT-nyiso149-duty-curve-keeper-2026-08-22.md, _nyiso149_bench_reconcile_closure.json, _nyiso149_chp_duty_curve_phase0.json, _nyiso149_duty_curve_gates.json (+_basis)",
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
    ercot_artificial_shortage_pricing: { cell: "." },
    ercot_storage_adaptive_expectation: { cell: "." },
    ercot_as_held_requirement: { cell: "." },
    ercot_as_held_location: { cell: "." },
    ercot_load_forecast_margin: { cell: "." },
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
    nyiso_synchronised_reserve: { cell: "U", ev: "nyiso-84 (built); nyiso-110 section 10; nyiso-113 (row added); nyiso-143 (results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md, probes scripts/probes/_nyiso143_nyc_spin_liveness.py + _nyiso143_online_rho.py, records _nyiso143_nyc_spin_liveness.json + _nyiso143_online_rho.json). nyiso-145: stays U, and the blocker is now QUANTIFIED rather than named. The RHO_CLIP escalation is prepared as an owner decision card (docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md): ALL THREE measured online_rho rows in the repo (NYISO's two + MISO's, 5.8 M online unit-hours, 80-96 % coverage) fall BELOW the uncited 0.5 floor while ALL THREE rho_minload counterparts fall INSIDE the band -- identifying [0.5, 4.0] as the LEGACY min-load estimand's band, inherited onto the as-operated one. On the keeper's own committed per-plant hourlies this family binds 8,739/8,740/8,714 h at the measured 0.2011 vs 8,608/8,572/7,845 h at the 0.5 floor, i.e. the band changes HOW HARD, never WHETHER. NOT armed and NOT re-banded -- owner D-5(b)", note: "STAYS U -- and the standing 'inert by construction' ground for closing it is FALSIFIED BY MEASUREMENT at nyiso-143 (2026-08-18, NO SOLVE, no field, no arm, keeper unchanged). Reported against the session's own convenience: nyiso-143 was chartered to close this cell and instead had to re-open it. (1) THE CLASS-2 HEADROOM ROW IS PER-ZONE, NOT AGGREGATE: model/lp/reserve_rows.py writes R[c,z] - rho * sum_{elig g in z} P[g] <= 0 per zone. nyiso-110's INERT arm gated the PUBLISHED nyca_10min_spin / east_10min_spin families, whose zone masks span NYCA/East so upstate hydro's 2-5 GW does enter the row -- the aggregate reading is correct FOR THAT ARM. This flag adds nyc_spin_online, masked to NYC ALONE (reserves/spec.py, nyc_idx), and NYISO has NO NYC HYDRO (154/147/3 hydro rows, none in NYC). The verdict was read across two structurally different zone masks. (2) THE FAMILY IS LIVE on the keeper's own committed dispatch: against the 250 MW static requirement (NYISO_SPIN_FRACTION 0.5 x nyc_10min_total 500), NYC online quick-start output has minimum 79.1/86.3/82.9 MW and median 212/140/249 MW, so the family is slack in every hour ONLY IF rho >= rho* = 3.1588/2.8981/3.0152 -- the top quarter of rho's own [0.5, 4.0] clip band. At the ceiling 4.0 it binds in 0 hours; at 1.0 it binds 7911/7159/4669 h (90.3/81.7/53.3 %) with worst deficits 170.9/163.7/167.1 MW. (3) AND rho IS NEVER IDENTIFIED. Its declared basis -- the fleet's own cap-weighted (pmax-pmin)/pmin, 'a fleet property ... not a tuned coefficient' -- is guarded by valid = (pmin > 0) & (pmax > pmin), and on the keeper's fleet ONLY 4 OF 851/849/705 LP ROWS CARRY pmin > 0 AT ALL (the nuclear block), NONE quick-start eligible. Under plant_level_fleet + use_campd_bins, must-run rides min_gen and pmin is identically zero across the merchant fleet, so the identification path is DEAD CODE for this ISO and the value that decides the mechanism is the literal 1.0 in the else: branch -- every year, in BOTH this branch and the rule-19 sibling's obligation branch (451/443/299 rows, 0 valid). A mechanism provably inert at rho >= 3.16 and binding in 90 % of hours at rho = 1.0, on a coefficient never measured, carries A FREE PARAMETER IN DISGUISE: rule 21 [R-DOF] and rule 5 [R-NO-MAGIC] each bar arming it. THIS IS A ROOT-CAUSE FINDING, NOT A REJECTION -- NYISO's downstate 10-minute requirement genuinely IS an online-gated obligation; what is missing is a measured 10-min-headroom-per-MW-online statistic derived under rule 23 [R-FROZEN-DERIVE] from source data. ONE IDENTIFICATION UNBLOCKS THE PAIR and the hard ValueError means only ONE of the two may ever be armed. NOT closable without a solve, and not closable WITH one until rho is identified. nyiso_spin_reserve_online's I STANDS UNTOUCHED (explained, not contradicted). Nothing here re-opens diurnal_price_amplitude (G). RULE 25: the pmin-based rho identification is NOT NYISO-specific code -- any ISO whose keeper runs a tranche/binned fleet with pmin = 0 hits the same fallback if it ever arms an online-gated reserve class; nyiso-143 measured ONLY NYISO, asserts nothing about the other five, and touched no other shard.. nyiso-144 (results/calibration/FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md): online_rho MEASURED for the first time and the flag STAYS U on a SHARPER blocker. scripts/data/derive_campd_online_reserve_rho.py measures the aggregate 10-minute deliverable headroom per MW on-line over the eligible fleet's own CAMPD record - rho = sum min(HSL-P, ramp10_frac x HSL) / sum P over online unit-hours, ramp10_frac being the model's OWN RAMP10_FRAC_BY_GROUP/BY_FUEL lookup so the statistic and FleetArrays.ramp10 read one source (rule 19). Basis-neutral: both HSL and P come from the same meter and ramp10 is a fraction, so the MW basis cancels and no plant/unit basis flag is needed. MEASURED: incity_obligation 0.3014 (min-load sensitivity 1.2462, full-hour 0.2864) over 401,361 online unit-hours at 95.5% CAMPD coverage; nyc_spin 0.2011 (min-load 1.1247) at 80.5%. WHAT THIS SETTLES: the downstate gated family is LIVE - rho* for inertness is ~3.0 and the ENTIRE admissible band 0.20-1.25 sits far below it, so rho decides how HARD the row binds, never WHETHER, answering nyiso-143's open question. WHAT IT DOES NOT SETTLE, and why the cell stays U: BOTH measured values fall BELOW the code's own RHO_CLIP floor of 0.5, a band inherited from the legacy pmin path that carries NO primary citation anywhere in the repo (both call sites described it only as 'the same [0.5, 4.0] physical band the path-A family uses' - self-referential). rho_used therefore returns the FLOOR, not the measurement, so arming a gated family today still sets its only reserve bound from a guardrail rather than from data - the same rule 21 [R-DOF] defect moved one level out. The band was left UNCHANGED rather than widened to fit the measurement, because re-banding a coefficient in the same change that re-identifies it would make the two indistinguishable. Resolving it is an owner rule-22 D-5(b) call. Seam: src/market_sim/data/online_reserve_rho.py; the dead (pmax-pmin)/pmin path is retained as tier 2 and the 1.0 fallback now logs that it is unidentified. STRUCTURAL NOTE recorded ex ante for the obligation specifically: arming it moves nyc_10min_total and li_10min_total from class 1 to class 2, and the gated row REPLACES the capability row sum P + R <= sum cap rather than joining it (model/lp/reserve_rows.py ends that branch in `continue`), so the arm would REMOVE a constraint that is currently live - nyc_10min_total binds 28/28/62 h at $25 precisely because NYC quick-start capacity is short - and replace it with a row imposing no energy/reserve capacity trade-off at all. With the families' $25 RCPF ceiling that makes the obligation a COMMITMENT driver, not a scarcity-price channel. Rule 25/28(d): every measured value is NYISO's own and transfers to no other ISO." },
    nyiso_spin_reserve_online: { cell: "I", ev: "nyiso-110 (FINDING-nyiso110-peak-half-decomposition-2026-08-02.md section 10); nyiso-113 (row added). nyiso-144 (FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md section 1.4): I CONFIRMED, not overturned, with a sharper reason and a NAMED re-open condition. The gated row is R[c,z] <= rho * sum_g P[g], so the family is inert whenever rho >= rho* = 655 / min_t sum P_eligible. Measured on the keeper's OWN committed class_hourly sidecars, rho* = 0.3426 / 0.3635 / 0.4619 - which sits BELOW nyiso-110's own stated 'hydro's 2-5 GW x rho >= 0.5 keeps it slack' floor. The rho=1.0 column reproduces nyiso-110's zero-delta result exactly (0 binding hours in all three years), so that solve is confirmed; but the verdict turns on where rho actually is, and hydro supplies almost all the eligible output (min sum P 1,912 MW with hydro vs 59 MW without). NO NYCA-wide rho row was derived, DELIBERATELY: hydro has no CEMS and carries NO entry in fleet.RAMP10_FRAC_* at all, so its 10-minute headroom in the model is a COVERAGE GAP rather than a measured zero, and measuring through it would manufacture a binding constraint out of missing data - exactly what nyiso-110 section 10 forbade. The spin_online branch in reserves/spec.py is therefore wired to look up a `nyca_spin` row that does not exist, fall through to the legacy identification, and LOG that rho is unidentified. WHY THIS MATTERS: this is the family the tail measurement points at - in NYISO's actual C3c tail hours the NYCA-wide reserve price averages $306.74/$31.74/$393.31 and clears $50 in 100%/15%/95% of them, against a Long-Island locational adder averaging $116.00/$5.36/$152.12, so the real tail is a SYSTEM-WIDE reserve-shortage pricing event and nyca_10min_spin (655 MW, $775 RCPF) is the instrument that would price it. It binds in ZERO hours of all three years because the class is idle-allowed. RE-OPEN CONDITION, now a single purchasable object: a defensible 10-minute deliverable-ramp capability for NYISO hydro, from NYISO's own AS certification / capability data. Nothing here re-opens diurnal_price_amplitude (G) and nothing is a price-amplitude claim. Probe: scripts/probes/_nyiso144_tail_anatomy.py.. nyiso-145: keeps its I, unchanged -- but its re-open condition is NARROWER than nyiso-144 recorded. The hydro RAMP10 coverage gap is real and re-confirmed at HEAD, yet its MACHINE-CAPABILITY half is already on disk: EIA-860 Schedule 3.1 flags 331 New York hydro generators / 5,689.9 MW -- 96.1 % of NY hydro nameplate -- as '10M' (full load from cold shutdown within 10 minutes), the same field the ramp-capability datatype already curates as fast_start_mw. Two obstacles are LANE-SIZED CODE SEAMS, not a purchase: fleet.withholding._ramp10_capability applies the measured reconciliation only `if measured and frac > 0.0` (hydro's class fraction is 0.0, so no measured row could ever lift it), and scripts/lib/ramp_capability/ carries caiso/miso/pjm and no NYISO module. What remains a genuine owner-funded intake is NYISO's own AS CERTIFICATION of that capability plus the hour-by-hour water limit. NO rho row derived, NO RAMP10 entry added, nothing armed -- nyiso-110 section 10 respected (results/calibration/ASSESSMENT-nyiso145-frontier-and-complete-2026-08-19.md section 5)" },
    nyiso_incity_commitment_obligation: { cell: "U", ev: "nyiso-105 section A (named as the compliant replacement path); nyiso-113 (row added); nyiso-142 (named successor); nyiso-143 (results/calibration/FINDING-nyiso143-online-rho-unidentified-2026-08-18.md section 4, record _nyiso143_online_rho.json). nyiso-145: stays U on the same RHO_CLIP block (docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md), and here the band is MATERIAL rather than marginal: on the keeper's own committed hourlies the gated row binds NYC 7,117/7,912/7,493 h at the measured 0.3014 against 4,858/6,717/5,596 h at the 0.5 floor (-26/-14/-22 pp) and Long Island 7,471/6,679/5,483 h against 5,346/4,488/4,086 h (-24/-25/-16 pp). Arming today would size a commitment driver from a guardrail. The nyiso-144 section 2.4 structural objection (the arm REMOVES the class-1 capability row that currently binds 28/28/62 h at $25) is carried unchanged and is independent of the band. NOT armed", note: "STAYS U, and nyiso-143 (2026-08-18, NO SOLVE) adds a SECOND, PRIOR blocker to the one nyiso-142 named. The obligation branch derives the SAME online_rho the path-A sibling does -- cap-weighted (pmax-pmin)/pmin over obligation_elig = quick_elig | ST_GAS steam, guarded by valid = (pmin > 0) & (pmax > pmin) -- and on the keeper's fleet that guard admits 0 OF 451/443/299 ROWS in 2023/2024/2025, so rho falls to the hard-coded else: 1.0 in every year. Since rho is what decides whether an online-gated family binds at all (sibling row: inert at rho >= 3.16, binding in 90 % of hours at rho = 1.0), arming this flag today would put an UNIDENTIFIED scalar on the critical path of a downstate commitment driver -- rule 21 [R-DOF] / rule 5 [R-NO-MAGIC]. So the object nyiso-142 named is real and still open (in-city ST_GAS falls 1.33 TWh over a span the market's rose; Lower-Hudson import rises +2.89 TWh; Ravenswood's steam bin never reaches its 4.49 TWh ceiling; three rival readings already refuted -- plumbing, the Ravenswood _FLEET_GROUP_OVERRIDE, the transfer bound), but the FIRST thing it needs is rho's identification, not a solve. Rule 19 [R-ONE-MECH]: MUTUALLY EXCLUSIVE by hard ValueError with BOTH nyiso_synchronised_reserve and nyiso_spin_reserve_online -- one identification unblocks the family and only one member may ever be armed. This row is the GENERALIZED form (published J/K ladders) and the path-A NYC-spinning family is its hand-scoped special case, so if one is ever built it should be this one.. nyiso-144 (results/calibration/FINDING-nyiso144-downstate-scarcity-and-rho-2026-08-18.md): online_rho MEASURED for the first time and the flag STAYS U on a SHARPER blocker. scripts/data/derive_campd_online_reserve_rho.py measures the aggregate 10-minute deliverable headroom per MW on-line over the eligible fleet's own CAMPD record - rho = sum min(HSL-P, ramp10_frac x HSL) / sum P over online unit-hours, ramp10_frac being the model's OWN RAMP10_FRAC_BY_GROUP/BY_FUEL lookup so the statistic and FleetArrays.ramp10 read one source (rule 19). Basis-neutral: both HSL and P come from the same meter and ramp10 is a fraction, so the MW basis cancels and no plant/unit basis flag is needed. MEASURED: incity_obligation 0.3014 (min-load sensitivity 1.2462, full-hour 0.2864) over 401,361 online unit-hours at 95.5% CAMPD coverage; nyc_spin 0.2011 (min-load 1.1247) at 80.5%. WHAT THIS SETTLES: the downstate gated family is LIVE - rho* for inertness is ~3.0 and the ENTIRE admissible band 0.20-1.25 sits far below it, so rho decides how HARD the row binds, never WHETHER, answering nyiso-143's open question. WHAT IT DOES NOT SETTLE, and why the cell stays U: BOTH measured values fall BELOW the code's own RHO_CLIP floor of 0.5, a band inherited from the legacy pmin path that carries NO primary citation anywhere in the repo (both call sites described it only as 'the same [0.5, 4.0] physical band the path-A family uses' - self-referential). rho_used therefore returns the FLOOR, not the measurement, so arming a gated family today still sets its only reserve bound from a guardrail rather than from data - the same rule 21 [R-DOF] defect moved one level out. The band was left UNCHANGED rather than widened to fit the measurement, because re-banding a coefficient in the same change that re-identifies it would make the two indistinguishable. Resolving it is an owner rule-22 D-5(b) call. Seam: src/market_sim/data/online_reserve_rho.py; the dead (pmax-pmin)/pmin path is retained as tier 2 and the 1.0 fallback now logs that it is unidentified. STRUCTURAL NOTE recorded ex ante for the obligation specifically: arming it moves nyc_10min_total and li_10min_total from class 1 to class 2, and the gated row REPLACES the capability row sum P + R <= sum cap rather than joining it (model/lp/reserve_rows.py ends that branch in `continue`), so the arm would REMOVE a constraint that is currently live - nyc_10min_total binds 28/28/62 h at $25 precisely because NYC quick-start capacity is short - and replace it with a row imposing no energy/reserve capacity trade-off at all. With the families' $25 RCPF ceiling that makes the obligation a COMMITMENT driver, not a scarcity-price channel. Rule 25/28(d): every measured value is NYISO's own and transfers to no other ISO." },
    nyiso_hydro_reserve_eligible: { cell: "K", ev: "issue #1344 lever 3; nyiso-110 section 10; nyiso-113 (row added, zonal census)" },
    nyiso_scr_edrp_reserve_eligible: { cell: "K", ev: "issue #1344 lever 3 step 2; nyiso-113 (row added)" },
    nyiso_import_reconciliation: { cell: "K", ev: "nyiso-99 (FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29.md); nyiso-113 (row added)" },
    nyiso_downstate_ct_gas_basis: { cell: "K", ev: "keeper DOF ledger (nyiso_downstate_ct_gas_daily, measured); nyiso-113 (row added). nyiso-145: the CLASS SCOPE of the armed daily leg (CT_PEAKER only) was TESTED as an extension to the Long Island CC/ST fleet and is REFUTED ex ante, NO SOLVE SPENT -- three LI gas plants report actual delivered cost to EIA-923 Schedule 5 for all 36 months of 2023-2025 (2511 Barrett / 2516 Northport / 2517 Port Jefferson: 3.70 / 2.83 / 4.74 $/MMBtu), and the model already tracks that to -11 % / -2 % / +7 % (7314: 3.28 / 2.77 / 5.06) while the LDC non-firm delivered index the CT leg uses is 53 % ABOVE it in 2025 (7.24). Rule 14 [R-ACCURATE] cuts AGAINST the extension: applying the index to the LI CC/ST fleet would make its fuel price materially WORSE. The CT scope is therefore GROUNDED, not an unexamined limitation -- interruptible peakers do buy on the daily non-firm index and the steam/CC fleet demonstrably does not. Do not re-propose without new data (results/calibration/FINDING-nyiso145-cc-overcycling-and-d4-vintage-2026-08-19.md section 4a)" },
    nyiso_local_selfsupply: { cell: "K", ev: "keeper DOF ledger (residual); caiso-155 (D-4 filing); nyiso-113 (row added)" },
    nyiso_firm_imports: { cell: "K", ev: "caiso-155 stub (D-2/D-4 visibility fix); nyiso-113 (row added)" },
    nyiso_rcpf_postsolve_overlay: { cell: "G", ev: "reserves/spec.py::_nyiso_design rule-19 guard; nyiso-113 (row added)" },
    nyiso_nyc_rcpf_step_curve: { cell: "K", ev: "nyiso-115 (row + field added; ex-ante screen, results/calibration/nyiso115_nyc_rcpf_curve_screen.json); instrument from nyiso-114 (FINDING-nyiso114-reserve-family-sidecar-2026-08-03.md §3)" },
    nyiso_ordc_measured_step_span: { cell: "K", ev: "nyiso-113 (row added); construction documented in reserves/spec.py::_nyiso_design" },
    nyiso_seny_rcpf_increment_step: { cell: "K", ev: "nyiso-119 (row added with the field); PREREG-nyiso119-seny-increment-2026-08-03.md; nyiso119_seny_increment_construction_probe.json; screen evidence nyiso117_seny_rcpf_curve_screen.json" },
    gas_commitment_bridge: { cell: "K", ev: "nyiso-87/90. nyiso-144 KEEPER (promoted 2026-08-18): the bridge gains the laid-up plant MEMBERSHIP channel nyiso_gas_bridge_plant_exclusions, the half of reliability_floor_plant_exclusions that never reached it - nyiso-140 repaired one MECHANISM, not the plant, so the same mothballed stations stayed floored by the other mechanism that floors the same class (rule 19 [R-ONE-MECH]). ONE differing scenario_config field. IDENTIFICATION (rules 13/23, source data only): median CAMPD plant gross load ZERO in every (year, 4h-block) cell of 2023-2025 - the nyiso-140 criterion VERBATIM. The per-cell quantifier is what makes it a lay-up test and not a low-capacity-factor test: a POOLED median of zero also catches ordinary CYCLERS (Saranac P(on)=0.426, Port Jefferson P(on)=0.375), the population a commitment bridge exists to hold together; the qualifying set stops at 18/18 zero cells and the nearest non-qualifier sits at 16/18. 12 plants, 98 fleet rows. NOT CIRCULAR: computed BLIND to the mechanism's floor pattern and to every D-4 verdict, and it then selects 7 of the bridge's 8 D-4 unit-conduct FAILURES - agreement as evidence, not fitting. ZERO free parameters (DOF ledger 39 -> 40, n_residual UNCHANGED at 6; the entry is a plant-code SET, n_scalars 0). ALL SIX pre-registered kill gates PASS. K2's shed prediction, computed from the CONTROL's own D-4 rows BEFORE either solve, was 0.1186/0.1396/0.3089 TWh against a +/-50% band; measured 0.1201/0.1406/0.3099 - within 1.3% every year. K3: zero stray losses, zero residuals. K4: D-4 unit-conduct failures 17 -> 3, ZERO new. K6' never escalated - every material class's forced share FALLS (ST_GAS 20.2->19.7/24.9->23.9/16.7->14.7%; CC_REGULAR 4.8->4.4/2.6->2.4/1.9->1.8%), unlike nyiso-140 where the surviving share rose. DO-NOT-MISREAD: it buys NO fit improvement and was not expected to - across both full calibration_verdict reports the ONLY difference is a SKIPPED, non-gated day-ahead diagnostic line, and C3c is BIT-UNCHANGED at 2/0/5 h vs actuals 10/13/42. What it buys is legitimacy (rule 1 [R-STRUCT]): ~0.57 TWh over three years no longer manufactured at plants whose own meter says they were mothballed. TWO PLANTS DELIBERATELY LEFT IN, named in the prereg BEFORE the solve: 7314 (8th D-4 FAIL, 77.1% of floored hours at zero) fails the lay-up test - it is a cycler the model's own P0 over-runs, so its forcing is an offer/economics defect and excluding it would bury that error in a membership list (rules 1/14); it is the NAMED SUCCESSOR. And 2517 Port Jefferson stays in the BRIDGE population (D-4 verdict `pass` all three years) though correctly excluded from the reliability FLOOR. RECORD CORRECTION: the nyiso-144 handoff's 2517 figures (0.1495 TWh / 4,623 h / 0.000 MW / 71.2% in 2024) do not match the keeper's own committed legitimacy_diagnostics.json (0.0616 TWh / 1,716 h / 45.222 MW / 44.7% / PASS); Roseton's row matches exactly, 2517's and 7314's do not. Rule 28(d): transfers to NO other ISO. Evidence: results/calibration/RESULT-nyiso144-bridge-layup-membership-2026-08-18.md, PREREG-nyiso144-bridge-layup-membership-2026-08-18.md, gates results/calibration/_nyiso144_layup_ab.json; probe scripts/probes/_nyiso144_layup_ab.py. nyiso-145 (diagnostic only, cell UNCHANGED at K): the named successor 'plant 7314's bridge over-run' is DIAGNOSED and dissolves. (i) Its 2025-ONLY D-4 unit-conduct FAIL is a MEASUREMENT-VINTAGE ARTIFACT -- 7314 is a CT-only CEMS reporter (e_ann/c_ann 1.46/1.47) whose protective ct_only rider skip CANNOT FIRE in 2025 because the preliminary EIA-923 vintage supplies no e_ann, so the ratio computes to exactly 1.00. C1 guards that vintage by name; D-4's conduct rider has NO vintage guard, so the keeper's 17 -> 3 headline is partly a function of which plants the vintage un-protects. (ii) On the COMPLETE vintages the plant is right: model P1 / EIA-923 net = 1.01x (2023), 1.18x (2024). (iii) The bridge is SCAFFOLDING, not the cause -- it supplies 79.9 GWh of 7314's 884.7 GWh 2025 dispatch (9 %). The real objects are fleet-wide and NEW to the queue: CC OVER-CYCLING (Bethlehem 262-302 model starts/yr in runs of median 5-9 h against 5-7 real starts in runs of median 487-1,217 h; largest bridge-floor consumer at 779/490/485 GWh; still 0.34x of its 923 net at P1 in 2023) and a MERIT-ORDER INVERSION on mothballed small CCs (Sterling 225x/130x, Batavia 69x/114x, Allegany 43x/33x, Massena 27x/46x, with ZERO bridge floor -- the nyiso-144 lay-up correction removed the FORCING and left the DISPATCH, so the energy moved from forced to economic where D-2/D-4 do not look). Neither is armed or tested here; both need their own pre-registration (results/calibration/FINDING-nyiso145-cc-overcycling-and-d4-vintage-2026-08-19.md). nyiso-146 (2026-08-19): the PER-PLANT MEASURED MIN-RUN leg (nyiso_gas_bridge_plant_min_run, new gated field, default off) is TESTED AND REJECTED on its own pre-registered gates -- verdict R for this leg; the bridge cell stays K on the keeper's class-scalar form. Phase 0 stands: the CC class is NOT one run-length population (plant-summed-series p25 spans 7-646 h, 92x, vs the 21 h class scalar; Bethlehem 2539 p25 = 134.75 h, Flynn 7314 = 15 h), percentile p25 pre-registered from the ct_min_run_hours constraint-side reasoning BEFORE any solve, artifact campd_perplant_min_run_NYISO.csv frozen (rule 23), Astoria campus pair excluded as boundary-misaligned. THE A/B: floors delivered EXACTLY (all 15 per-plant arm/control ratios inside +/-25% of the control-side capture's prediction; Bethlehem 685->1,329 GWh in 2023) and the OBJECT DID NOT MOVE -- P1 starts 327->302 / 526->476 / 262->250 (-7.6/-9.5/-4.6% vs bars of >=50/>=10/>=10%), median run flat, ONE new D-4 conviction (54574 Saranac 2024: its 14 h measured value SHRINKS its floor and the redistributed binding hours land on zero-metered hours). K5 clean: the two arms' production verdicts are line-identical (C3c bit-identical 2/0/5), so the rejection is NOT on fit (rule 1) -- it is that the mechanism cannot reach the defect: every gap/extension floor covers only P0-OFF hours, while Bethlehem's fragmentation lives in P1's bid-cost pass shutting the plant INSIDE P0-committed hours. NAMED SUCCESSOR with NYISO's own evidence: the ercot141 floor_online_hours detector leg (LSL must-take in every online hour), never tested on NYISO (rule 25). Both arms registered: 2026-08-19-nyiso-146-control / 2026-08-19-nyiso-146-perplant-minrun. Evidence: results/calibration/RESULT-nyiso146-perplant-min-run-ab-2026-08-19.md, PREREG-nyiso146-perplant-min-run-2026-08-19.md, _nyiso146_ab_gates.json, _nyiso146_perplant_minrun_phase0.json, _nyiso146_k2_prediction.json. nyiso-146b/c (SAME SESSION, 2026-08-19) -- KEEPER PROMOTED ON THIS ROW: 2026-08-19-nyiso-146c-state-scoped, the ONLINE-HOURS LSL STATE FLOOR duty-scoped by the measured run-length gap (nyiso_gas_bridge_online_hours gas_cc-scoped + nyiso_gas_bridge_state_floor_min_run over constants.NYISO_STATE_FLOOR_MIN_RUN_HOURS=100h and the frozen campd_perplant_min_run_NYISO.csv; effective membership {2539,56234,56196} at p25 130-646h). CLOSES THE nyiso-145 CC OVER-CYCLING OBJECT: Bethlehem 327/526/262 P1 starts (6-7 metered) -> 41/10/15 with median runs 12/7/14h -> 68/144/319h; Caithness -> 3/2/4 vs 4/6/8 metered. Determination CALIBRATED, C3c the lone ledgered caveat BIT-IDENTICAL 2/0/5; zero new D-4/D-1; zero new fitted scalars; all C2-K gates PASS; complete marker re-keyed with D-5(b) re-verification (superseded keeper re-scores CALIBRATED); keeper auditor PASS. THE UNSCOPED ARM (2026-08-19-nyiso-146b-online-hours) is REJECTED-AS-ARMED and is the measurement that identified the scope: it repaired the same cohort AND over-glued the 7-20h-p25 cyclers (Athens-2025 9 vs 63 metered; one new D-4 at Saranac) -- the two cohorts are exactly the phase-0 gap's two sides. Evidence: RESULT-nyiso146bc-state-floor-keeper-2026-08-19.md, PREREG-nyiso146b-online-hours-and-reserve-duty-2026-08-19.md, PREREG-nyiso146c-state-floor-duty-scoping-2026-08-19.md, _nyiso146bc_gates.json" },
    reliability_floor: { cell: "K", ev: "nyiso-81 re-derive; NYISO_PEAK_WINDOW_FLOORS_OFF" },
    reliability_floor_plant_exclusions: { cell: "K", ev: 'nyiso-140 KEEPER (promoted 2026-08-16, owner ruling). Excludes the economically laid-up Port Jefferson (2517) from the always-on Long_Island ST_GAS limb - a rule-17 [R-FLOOR-WINDOW] MEMBERSHIP correction, never a window change. IDENTIFICATION (source-data trigger, no residual consulted): 2517 median when-available CF EXACTLY 0.000 in every hour block of 2023/2024/2025, 73% of cool hours at zero, ~100% model availability because the 2026-07-26 guard fix (6a8f285) correctly un-booked lay-up from the outage extract; it absorbed 72.6% of everything the limb forced (1.87 of 2.57 TWh over 3 yr) on 7.2% of the fleet output. WINDOW CONFIRMED CORRECT AND UNCHANGED - Barrett (2511) and Northport (2516) run the real persistent baseline (cool-day median CF 0.254/0.313 at h00-05) and are forced only 4-6% of their own output. floor_pct UNCHANGED at 0.262: two CANCELLING basis errors (a daily-mean statistic applied hourly; a fleet aggregate applied per unit) correct to 0.2666, so ZERO free parameters (rule 21, n_residual unchanged at 6). A/B vs same-HEAD control 2026-08-16-nyiso-140-control, 2023 2024 2025 one bundle each, ALL SIX pre-registered kill gates clean; K3 liveness shed 0.602/0.560/0.625 TWh against the ~0.62/yr predicted from CAMPD BEFORE any solve. CALIBRATED-WITH-CAVEATS, C3c the lone ledgered caveat, criterion-for-criterion identical to the superseded keeper. DO-NOT-MISREAD: the fit gets slightly WORSE and was pre-registered to (ST_GAS err +2.679->+2.263 in 2023, -0.595->-0.916 in 2024, -3.379->-3.737 in 2025; summed |err| 6.653->6.916 TWh). Kept on rule 1 [R-STRUCT] and the owner structure-over-gates clause; under rule 14 [R-ACCURATE] the degradation is a DISCOVERED BUG - the manufactured energy was masking a real downstate under-production - and THAT root cause is the successor. Do NOT re-floor the laid-up plant and do NOT reach for this row to buy back volume in any ISO (rules 1/24); rule 28(d) - this verdict transfers to NO other ISO, which must identify any laid-up unit from its OWN CAMPD conduct. FIRST APPLICATION OF K6-PRIME (owner-adopted 2026-08-16): the surviving nyiso_gas_commitment_bridge share ROSE (+0.0045/+0.0118/+0.0051) while doing strictly less work, which bare K6 would have killed. STANDING CAVEAT: K6-prime leg (a) leans on D-4, which is TAUTOLOGICAL for an h0-23 floor (offwindow_share 0.0 by construction), and the adopted D-4 per-unit rider is NOT yet implemented - that leg is unproven rather than passed. Evidence: results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md, PREREG-nyiso140-li-st-floor-membership-2026-08-16.md; probe scripts/probes/_nyiso140_li_st_floor_membership.py' },
    mustrun_online_frac_per_year: { cell: "U", ev: "row added with the field 2026-08-20 (miso-172, rule 28c); never armed here. Entering as U per rule 28(d) — the MISO identification is per-ISO (its own thermal_tranches_online_frac_by_year_<ISO>.csv, derived from this ISO's own CEMS), and no verdict transfers. PREREQUISITE for any lane that wants it: this ISO must first HAVE the per-year artifact (only MISO does today), and its keeper must arm a per-plant must-run floor at all — cc_mustrun_per_plant or st_gas_mustrun_per_plant — or the flag solves a bit-identical control." },
    st_gas_mustrun_p25_measured_level: { cell: "U", ev: "row added with the field 2026-08-20 (miso-172, rule 28c); never armed here. Entering as U per rule 28(d). The DEFECT is code-generic (thermal_tranche_p25_level reconstructs p25_cf x nameplate and drops the avail_mult the statistic was divided by), but the VERDICT is per-ISO (rule 25) and the repair is inert wherever st_gas_mustrun_p25_level is not armed — MISO is the only ISO that arms it today. A lane taking this up needs its own thermal_tranches_p25_level_mw_<ISO>.csv and its own A/B." },
    mustrun_layup_window_mask: { cell: "U", ev: "row added with the field 2026-08-20 (miso-173, rule 28c); never armed here. Entering as U per rule 28(d). The DEFECT is code-generic (the merit-order guard writes an economic-lay-up companion extract for every ISO and the per-plant must-run floors ignore it, so a floor can bind inside a measured lay-up window), but the VERDICT is per-ISO (rule 25) and the mask is inert wherever no per-plant must-run floor is armed. A lane taking this up scores its own lay-up census against its own floored plants and runs its own A/B." },
    mustrun_plant_exclusions: { cell: "U", ev: "row added with the field 2026-08-19 (miso-170, rule 28c); never armed here. Entering as U per rule 28(d) — the MISO identification transfers nothing; this ISO must identify any laid-up unit from its OWN CAMPD conduct before arming" },
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
    chp_btm_measured: { cell: "K", ev: "nyiso-149 (2026-08-22): ARMED IN THE KEEPER 2026-08-22-nyiso-149-duty-curve. The R below was 'REJECTED-AS-ARMED ... held with a named successor', and the successor lineage is now complete: nyiso-148 rejected the single-band chp_layup_duty_split (bang-bang) and named the price-conditional duty curve; nyiso-149 built it (chp_layup_duty_curve — graded, envelope-conditional, MW contract, zero DOF), and the pair passes every pre-registered gate: the three failures that rejected THIS field standalone are each closed (A-K4 Selkirk 7.9x -> 0.54/1.76/0.85x of its own meter; A-K5 C1 CC_CHP now PASSES all years on the corrected bench; C3a-2025 -12.2% -> -8.8% PASS). Also the Job-1 benchmark ruling (FINDING-nyiso149-bench-root-cause-2026-08-22.md): the classFull subtrahend this field changes is ruled the CORRECT benchmark basis and is now PINNED flag-independent (btm_bench_twh), so the bench part no longer follows any run's flag. ORIGINAL R RECORD (nyiso-147, preserved verbatim): nyiso-147 (2026-08-20): TESTED AND REJECTED-AS-ARMED on its own pre-registered gates (A-K3 2023 leg -32% vs >=40%; A-K4 Selkirk 7.9x its meter; A-K5 C1/C3a-2025/C3b-2025 PASS->FAIL) — and the REJECTION IS THE SESSION'S FINDING WORKING: the single measured delta proves the 2023 upstate price object. Phase 0 located C3a-2023's +9.2% entirely in Upstate_West (+9.46pp; +30.8% zone, year-round, present all three years but cancelled by downstate under-pricing in 2024/25), refuted the upstate fuel-basis candidate (west marginal gas $1.79-1.96 at SOM Z4 $1.82), split the $8.1 'markup' into RGGI (~$7.4) vs offer, and identified the root cause: the chp_steam_following merchant 35% BTM carve ('residual-identified ... no independent source yet') is refuted by the plants' own market meters — Gold Book net energy = 100.3% of EIA-923 net for Sithe Independence 54547 three years running (BTM ~0, not 35%), BNY's carved capacity implies CF 1.07 (impossible), Independence-2024's 6.16 TWh needs CF 0.93 of its carved 753 MW. ARMED, the one field moves lw C3a +8.7->+1.5% (2023), upstate eqh err +3.54->+0.89 (2024) and +5.79->-0.38 (2025) — the object CONFIRMED — and simultaneously EXPOSES what the carve was masking: (1) Selkirk-class idle-cogen phantom dispatch (730 vs 92 GWh metered, the merit-order-inversion class on the CHP side, out of cc_reserve_duty_split's CC_REGULAR scope); (2) CC_CHP conduct — the LP runs restored plants at offer-implied CF (Independence 1.36x/1.19x/1.26x of meter; C1 CC_CHP +5.0 TWh vs its OWN corrected bench); (3) 2025's control 'pass' (-2.2%) was ~$6/MWh of masked under-pricing (arm -12.2%). Owner structure-over-gates clause considered and NOT applied — the regressions are unmasked defects, not scorer noise; promoting would swap CALIBRATED for NOT-YET. THE ARTIFACT AND WIRING SHIP default-off (rule 14, the pjm-146 disposition). Arm B (cc_reserve_duty_split re-arm) did NOT solve — conditioned on arm A passing. NAMED SUCCESSORS: (a) CHP idle/lay-up membership + CC_CHP conduct (offers/maintenance) so the measured capacities can arm; (b) the 2025 dear-gas-year level object. Runs 2026-08-20-nyiso-147-control (byte-identical keeper replay) / 2026-08-20-nyiso-147a-chp-btm; evidence RESULT-nyiso147-chp-btm-ab-2026-08-20.md, FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md, _nyiso147_ab_gates.json; probes _nyiso147_upstate_price_phase0.py / _nyiso147_upstate_offer_anatomy.py / _nyiso147_chp_grid_capacity.py / _nyiso147_ab_gates.py" },
    netload_drag_floors: { cell: "R" },
    ramp_envelopes: { cell: "K", ev: "nyiso-111 (own artifact + bound-against-the-bound pre-check + A/B, PROMOTED KEEPER — FINDING-nyiso111-ramp-envelopes-2026-08-02.md §4)" },
    forced_share_d4_census: { cell: "I", ev: "xiso-3 §3 (zero latent gaps — fully windowed; ST_GAS 27.5% the closest sub-cap class anywhere)" },
    reserve_family_sidecar: { cell: "I", ev: "nyiso-114 §1-§2 (built + first use); nyiso-113 §8 (the gap, and the invalid-instrument correction that motivated it); nyiso-115 (zones column + this row)" },
    diagnostics_plant_set: { cell: "I", ev: "caiso-155 §B/§D (7.884 TWh/yr HQ row now visible; nyiso_gas_commitment_bridge 5.31/3.14 pp G-06 false-FAIL averted via BRIDGE_MECHS)" },
    energy_online_capability_cap: { cell: "." },
    offer_curve_by_group: { cell: "K", ev: "nyiso-150 (2026-08-22) — THE cc_reserve_duty_split LEG RE-ARMED per the standing prereg (queue item 3, unblocked when the CHP capacity+conduct repair landed) AND REJECTED AGAIN, now on leg (a) ALONE: run 2026-08-22-nyiso-150-reserve-rearm vs the bit-identical keeper-replay control; C-K2 fails on Allegany 7784 (falls 70%/60% vs the >=80% bar in 2023/2024) while Sterling/Batavia/50744 collapse 93-98% and every other gate passes — C-K1 exact, C-K3 no-degrade PASS, C-K4 zero new D-4, C-K5 C1/C2/C3a/C3b/C4/C8 all PASS with C3a-2023 +5.2% IN BAND, so the nyiso-146b rejection leg (b) is RESOLVED by the CHP repair exactly as conditioned. The mechanism-as-specified (whole cohort to the class peak band) is insufficient for the cohort's most efficient member; NAMED SUCCESSOR RE-SPECIFIED SAME SESSION (FINDING-nyiso150-allegany-hr-identity-2026-08-22.md): Allegany's hr 7.5 is the HEAT_RATE_BINS gas_cc 'older' CLASS DEFAULT reached through an ORISPL registry split — eGRID carries the plant as 10619 with a stable measured rate 7.99-8.68 across SEVEN vintages (pooled 8.42), identity proven by exact PLNGENAN==EIA-923-7784 netgen equality in all seven years — so the successor is (1) the identity heat-rate repair (measured artifact at the existing heat_rate preference seam, default-off, NYISO-scoped) then (2) re-gate this split on the repaired control; the graded-duty build returns only if Allegany still misses the bar after both. A general CAMPD-less eGRID-HR channel was sized and REFUTED on its own population (57 NY plants, mostly BTM cogens/micro-peakers with realized rates 5.7-118). 2025 reported not gated (preliminary vintage): the cohort floats 295-495 GWh even at the peak band in the dear year. PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md; _nyiso150_ab_gates.json || nyiso-146 (2026-08-19): the cc_reserve_duty_split leg (duty-role MIRROR of the intermediate splits; measured 7-plant capacity-only cohort {50744,54592,54593,7784,10620,10621,54034} at a 2.7x population-gap on-share separator, routed whole to the class peak band 2.25x as the recipe resolves it) is TESTED AND REJECTED on its own pre-registered gates -- verdict R for that leg; the row's NYISO cell stays K on the recipe's standing curves. THE OBJECT MOSTLY REPAIRS: Sterling -88/-90%, Massena -89/-90%, Batavia -93/-94% of their 25-225x phantom energy in the gated years, Bethlehem's underrun improves (3,224->3,484 GWh vs 3,639 metered, 2024), zero new D-4/D-1. REJECTED because (a) Allegany 7784 (hr 7.5, the cohort's most efficient) falls only -64/-50% vs the >=80% bar and (b) C3a-2023 +9.0% -> +11.3% -- the ~1.4 TWh of phantom cheap upstate energy was PRICE-RELEVANT and 2023 held 1 pp of band headroom, so the defect-B repair is now a JOINT object with the 2023 upstate price level (either its root cause moves first, or the owner rules the +11.3% with the phantom capacity REMOVED is the truer 2023 under rule 14's discovered-bug reading). Its FIRST solve was INERT (frame seam clobbered by pct_peaking/cc_duct_peaking; fixed -- the override now applies LAST in bins_to_fleet -- and disclosed in the prereg before the valid solve; both solves registered: 2026-08-19-nyiso-146b-reserve-inert / -reserve-duty). Membership artifact reserve_duty_cc_NYISO.csv frozen (rule 23). Evidence: RESULT-nyiso146bc-state-floor-keeper-2026-08-19.md, PREREG-nyiso146b-online-hours-and-reserve-duty-2026-08-19.md, _nyiso146bc_gates.json || nyiso-148 (2026-08-21) — SECOND leg of this row tested and REJECTED, chp_layup_duty_split (the cogeneration sibling of the cc_reserve_duty_split leg above, DISJOINT from it by class scope): nyiso-148 (2026-08-21): BUILT, TESTED AND REJECTED-AS-ARMED on its own pre-registered gates. The named successor to chp_btm_measured: a 7-plant measured CHP lay-up census (the nyiso-140/144 zero-cell criterion applied for the first time BEYOND the commitment bridge's (CC_REGULAR, ST_GAS) population) routed to the class peak band, chained single-delta on top of nyiso_chp_btm_measured. D-K1 (exactness) / D-K2 (liveness) / D-K4 (conduct) PASS; D-K3 (overkill), D-K5 (C1-2024 CC_REGULAR PASS->FAIL at share +3.04 pp vs +/-3 pp; the TWh leg still passes at +3.22 of +/-3.98) and D-K6 (2025 recovers 18.9% of the base -12.2%, bar >=40%) FAIL. WHAT IT BUYS, and it is substantial: CC_CHP volume lands +0.23 TWh (2023) and +0.03 TWh (2024) against a base of +1.52/+1.53; CC_REGULAR-2023 share goes to -0.0 pp; vs the base C3a-2025 FAIL->PASS, C3b-2025 FAIL->PASS and C8 FAIL->PASS (the base D-2 ST_GAS-2024 30.4% forced-share failure is CLEARED); C3a-2023 +3.4% against the keeper's +8.7%, i.e. the nyiso-147 upstate repair carried. THE TWO FINDINGS THAT REJECT IT. (1) ENERGY IS CONSERVED: removing 1.29/1.50/1.68 TWh of CC_CHP moves the gas family total by -0.01/-0.11/-0.02 TWh (CC_REGULAR +0.60/+0.76/+0.76, ST_GAS +0.46/+0.48/+0.61, CT_PEAKER, imports), so the price moves only +$0.63/+$0.79/+$1.50 and THE 2025 -12.2% SURVIVES REMOVING THE ENTIRE CHP PHANTOM. The 2025 dear-gas level is therefore an OFFER-LEVEL object, NOT a capacity or membership one — $1.50 of the $8.07 gap is recoverable here and $6.57 is a different object (owner card docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md). Do not scope CHP membership work against the 2025 level. (2) ONE BAND CANNOT MAKE A GRADED RESPONSE: the cohort goes bang-bang — essentially OFF in 2023/2024 (Selkirk 2.01x/6.78x -> 0.03x/0.04x of its own meter) and STILL OVER in the dear year (Lockport 3.96x, Yerkes 2.15x, Oswego 1.92x in 2025) — while the real plants run 1.6-18.6% of hours in 10-43 h runs and scale WITH price (Selkirk metered gross 156.9 -> 107.7 -> 384.8 GWh). The successor identification is a PRICE-CONDITIONAL ON-SHARE (a duty curve), not a band level; the MEMBERSHIP is sound and must not be re-derived (rule 23). A GUARD THE MEASUREMENT FORCED, recorded because it generalises: the census ABSTAINS where the meter is silent (p99.5 HSL > 0) — RED-Rochester 10025, Ticonderoga 54099 and Cornell 50368 carry identically-zero CAMPD series against 439-950 GWh of EIA-923 net, so a naive extension would convict plants CAMPD cannot see; a degeneracy test, not a threshold, so the leg stays zero-DOF. SEAM LESSON, second lane in a row: the first solve was INERT-BY-HALF because the leg was wired at fleet_to_bins and not at assembly.py::bins_to_fleet (pct_peak clobbered back by the tranche artifact / duct-burner map — verbatim the nyiso-146b defect); caught by the arm's own D-K2 anti-inert gate, disclosed in PREREG section 9 before the corrected solve, and registered. THE ARTIFACT AND WIRING SHIP default-off (rule 14). ARM E (cc_reserve_duty_split re-arm) did NOT solve — conditioned on ARM D passing; PREREG-nyiso146b ARM C bars untouched. Runs 2026-08-21-nyiso-148-chp-layup / 2026-08-21-nyiso-148-inert-plumbing; evidence RESULT-nyiso148-chp-layup-duty-2026-08-21.md, PREREG-nyiso148-chp-layup-duty-2026-08-21.md, _nyiso148_ab_gates.json, _nyiso148_chp_conduct_phase0.json; probes scripts/probes/_nyiso148_chp_conduct_phase0.py + _nyiso148_ab_gates.py; derive scripts/data/derive_campd_chp_layup_census.py The row's NYISO cell STAYS K on the recipe's standing curves — both duty-split legs are R, the curves themselves are untouched. || nyiso-149 (2026-08-22) — THIRD leg of this row: chp_layup_duty_curve, BUILT, TESTED AND PROMOTED TO KEEPER (2026-08-22-nyiso-149-duty-curve). The successor the second leg named: the same FROZEN 7-plant census, offer shape = the measured PRICE-CONDITIONAL ON-SHARE (own-model-zone MIS RT LBMP quantile bands p40-p80/>=p80, x loading-when-on x HSL, measured CONDITIONAL ON ENVELOPE-LIVE HOURS from the frozen campd-unit-outages extract so the availability envelope and the offer never double-count the same mothball spells — rule 19; phase 0 measured envelope availability tracking metered live share within ~0.02 for six of seven plants, Lockport the exception whose lay-up the offer carries whole), offered as MW at the class curve's EXISTING band multipliers with the remainder WITHHELD from energy and reserves. Zero new price constants (rule 21); statistics regenerate per vintage (rule 13). ALL PRE-REGISTERED GATES PASS (PREREG-nyiso149 §4, record _nyiso149_duty_curve_gates.json): F-K1 single delta on a base replay BIT-IDENTICAL to registered 147a (max |dprice| 0.0, doubling as default-inertness proof); F-K2 LP-entry composition exact to 0.01 MW; F-K3 graded conduct in-band on all 21 plant-years (cohort 291->413->988 GWh matching the metered climb into dear 2025; Selkirk 0.54/1.76/0.85x vs the split's 0.03-0.05x bang-bang); F-K4 zero new D-rows AND the base's D2 ST_GAS-2024 30.4% failure CLEARED; F-K5 C1 14/14. SEAM LESSON #4 OF THE CLASS, caught BEFORE scoring this time: the first solve applied pct-of-census-pmax fractions to the BIN nameplate (offered 1.01-1.35x intended) — gate F-K2 caught it, PREREG §7 disclosed it before the corrected solve, the MW contract fixed it (artifact econ_mw/peak_mw consumed directly at the CAP level so the econ residual cannot re-absorb the withhold), and the mis-based solve is registered as 2026-08-22-nyiso-149-basis-probe. Runs 2026-08-22-nyiso-149-duty-curve (KEEPER) / -basis-probe; evidence RESULT-nyiso149-duty-curve-keeper-2026-08-22.md, PREREG-nyiso149-chp-duty-curve-2026-08-22.md, _nyiso149_duty_curve_gates.json (+_basis), _nyiso149_chp_duty_curve_phase0.json; derive scripts/data/derive_nyiso_chp_duty_curve.py; artifact chp_duty_curve_NYISO.csv (frozen, rule 23)." },
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
    nyiso_iroquois_winter_spread: { cell: "R", ev: "nyiso-150 (2026-08-22): TESTED BY SOLVE FOR THE FIRST TIME AND REJECTED-AS-ARMED on its own pre-registered gates (PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md, Amendment 1 mapping the nyiso-122 refusal grounds to kill gates; run 2026-08-22-nyiso-150-winter-spread; gates _nyiso150_ab_gates.json). THE REJECTION IS THE DECISIVE MEASUREMENT THE nyiso-122 EX-ANTE READ COULD NOT MAKE: armed, the whole state rises TOGETHER in the winter event months — Dec-24 47.8->61.9 statewide with Upstate_West landing ~exact on its actual (60.9); Feb-25 UW exact (87.4 vs 87.1) — while the downstate-upstate spread stays <=$1.1 against $11-27 actual. An $8-13/MMBtu measured zonal gas spread produces <$1 of zonal price spread: the LP prices the four mainland zones as ONE COUPLED BLOCK (the internal west->east cutset never binds), so no fuel-side mechanism can create the winter downstate premium — the gradient object is LOCATIONAL, proven at the LP, confirming nyiso-122 and nyiso-124 from the price side. Gate record: W-K3a spread recovery 0-4% vs >=30%; W-K3b the annual gradient FALLS (1.47->1.27, 0.80->0.69); W-K3c UW-2023 worsens (+23.6->+23.8% — the eastern winter premium leaks upstate through the coupling); W-K3d anti-relocation fires (2023, 2025); W-K4 two NEW D-4 conduct rows (54574-2023, 2500-2025); W-K5 C1-2024 CC_REGULAR +3.63 TWh PASS->FAIL. Also measured: the flag-off construction gives UW PHANTOM gas at both ends (Jan-2025 $11.01/MMBtu vs the ~$3.5 measured Tenn Z4 world; summer-2025 $0.16-0.64) and NYC gas is bit-identical on/off (_nyiso150_gradient_phase0.json) — so the rule-14 standalone case is real but the accurate monthly input is MISALIGNED to the coupled-block representation (rule 14 misalignment clause): armed alone it relocates error instead of removing it. RE-OPEN CONDITION: a locational mechanism that lets the west->east cutset bind (the downstate-premium object of nyiso-122 BLOCKER-A/B); re-test this flag as its companion, never alone. Prior O record preserved: construction gates PASS at nyiso-122 (annual conservation Delta=0.00000 x3; NYC delivered gas bit-identical); refused ex ante AS THE C3a-2025 WINTER LEVER on reach (stands, on the overlay row)." },
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
    miso_seam_envelope_hour_ending_key: { cell: ".", ev: "MISO-only field (the seam-DIBA gate returns None for every other ISO — byte-identical; verified miso-175 V-3). Whether this ISO's own seam-envelope analogue carries the same hour-key convention is this lane's call, handed forward by FINDING-miso174 §4/§7 — not inspected or stamped by miso-175 (rule 25)." },
    nyiso_seam_par_attribution: { cell: "R", ev: "results/calibration/PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md + PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md + PREREG-nyiso127-addendum2-full-seam-attribution-2026-08-05.md; probe scripts/probes/_nyiso127_par_phase0.py; record results/calibration/_nyiso127_par_phase0.json; intake data/raw/NYISO/par-data/" },
    import_hub_pricing: { cell: "K", ev: "keeper; nyiso-86 §3, nyiso-99 (FINDING-nyiso99 §2)" },
    import_shape_lever: { cell: "G", ev: "nyiso-99 (FINDING-nyiso99-import-shape-attributed-to-c3c-2026-07-29), nyiso-86 §3" },
    nyiso_import_sil_retire: { cell: "K", ev: "nyiso-100 (FINDING-nyiso100-simultaneous-import-misattribution-2026-07-30, PREREG-nyiso100, probe nyiso100_simultaneous_import_identification.py)" },
    nyiso_li_tsl_n11_security: { cell: "K", ev: "nyiso-130 (PREREG-nyiso130-li-transfer-security-limit-2026-08-06.md; identification results/calibration/_nyiso130_li_tsl_identification.json); nyiso-143 (PREREG-nyiso143-zone-k-transfer-bound-2026-08-18.md, RESULT-nyiso143-zone-k-transfer-bound-ab-2026-08-18.md, gates results/calibration/_nyiso143_ab_gates.json, probe scripts/probes/_nyiso143_ab_gates.py; runs 2026-08-18-nyiso-143-control + 2026-08-18-nyiso-143-n11tsl-arm)", note: "R -> O -> K 2026-08-18 (nyiso-143): PROMOTED TO KEEPER on the owner ruling \"Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper.\" The keeper is 2026-08-18-nyiso-143-n11tsl-arm, superseding 2026-08-17-nyiso-142-stackdup; determination CALIBRATED under rubric v3.4 with C3c the lone ledgered caveat, and the superseded keeper re-scores CALIBRATED on the same rubric so the D-5(b) worse-determination stop does not fire. THE STRUCTURE-OVER-GATES CLAUSE IS THE OPERATIVE ONE AND WAS NEEDED: C3c REGRESSES 21/3/24 h -> 2/0/5 h against actuals 10/13/42 (a two-year miss becomes three, 2025 goes PASS -> FAIL, direction flips from over- to under-production), bought for a PUBLISHED input replacing a netted estimate that double-counted a 660 MW loss-of-source. No other gated criterion regresses; 2023 C3a improves +9.6 -> +9.0 %. DOF ledger 38 -> 39 entries with n_residual UNCHANGED at 6 (published entry, n_scalars 0). The NAMED SUCCESSOR is THE DOWNSTATE SCARCITY MECHANISM. Prior adjudication record follows. R -> O 2026-08-18 (nyiso-143). THE nyiso-130 REJECTION IS SUPERSEDED, NOT OVERTURNED ON A WHIM: it was killed on K6, and the OWNER REPLACED K6 with K6' at nyiso-140 s6.3 PRECISELY BECAUSE 'K6 cannot adjudicate any import-relief lever' (a share-based gate is structurally biased against a lever that relieves a constraint -- nyiso-139b s5). Rule 28(a) is satisfied by three independent pieces of new evidence: the CONTROL changed (nyiso-140 removed the plant absorbing 72.6 % of the very floor K6 fired on; nyiso-142 corrected the 2025 benchmark), the GATE changed (K6 -> K6'), and K6' leg (a) became NON-VACUOUS for the first time (the D-4 per-unit conduct rider, shipped nyiso-143). PRE-REGISTERED BEFORE EITHER SOLVE, A/B over 2023+2024+2025 in one bundle, BOTH ARMS REGISTERED. RESULT: ALL SIX GATES SILENT, K6' INCLUDED -- it escalated on the pre-registered forced-share rise (downstate reliability_floor x ST_GAS 0.169->0.185 / 0.190->0.222 / 0.123->0.138) and CLEARED BOTH LEGS: ZERO new D-4 failures in the arm (it REMOVES three, incl. Port Jefferson from the gas bridge in 2024+2025) and ZERO new D-1 misses; energy-normalised dforced +0.207/+0.378/+0.194 TWh reported, not gated. K1 one differing field, K2 slack/dump 0.0, K3 in-window 940.0 MW vs control 325/275/275, K4 only NYC>Long_Island moves, K5 seam inside +/-2 %. CORRECTED 2026-08-18, SAME SESSION -- THE ARM PASSES ITS OWN PRE-REGISTRATION AND THE DETERMINATION WOULD NOT MOVE. Prereg s6 set promotion as K1-K5 silent + K6' clean + C1/C2/C3a/C3b/C4/C6/C8 no worse than control, 'whatever C3c does' (charter D2 / nyiso-130 s8 -- the OWNER had already ruled C3c is not this lever's deciding criterion); all of it holds, 2023 C3a IMPROVES, and NO pre-registered adverse case fired. Measured: price_tail is the LONE failing criterion in BOTH arms with C6 UNATTESTED the only other non-PASS (the absent keeper attestation every probe carries), so attested BOTH would hit rubric v3.3's C3c standing rule and read CALIBRATED with one ledgered caveat -- the SAME label the designated keeper carries. The '2-of-3 -> 3-of-3' below is the per-year criterion RECORD at full magnitude, NOT a determination change. This note's first version said 'not promotable' and used the discovery below as the reason; that inverted the nyiso-119 G4 precedent (a gate that passes AS WRITTEN is not overridden by a consideration invented after the result) and is WITHDRAWN. WHAT THE ARM EXPOSES, standing entirely on its own merits and the most valuable thing in the bundle: 100 % OF THE MODEL'S C3c TAIL HOURS ARE Long_Island, IN BOTH ARMS AND EVERY YEAR. NYISO's modelled scarcity pricing IS this bound binding in 84.5/87.6/71.1 % of its design-condition hours; swap in the published 940 and occupancy falls to 24.8/21.3/6.8 % and C3c goes 21->2 / 3->0 / 24->5 h against actuals 10/13/42 -- a 2-of-3 miss becomes 3-of-3 and 2025 goes PASS -> FAIL. C1/C2/C3a/C3b/C4/C8 PASS in BOTH arms, mean LMP moves <= $0.26/MWh, and 2023 C3a IMPROVES +9.6 -> +9.0 %. The control reproduces the designated keeper's C3c BIT-IDENTICALLY at 21/3/24. THIS IS NOT A REJECTION ON FIT -- rule 1 [R-STRUCT] forbids that and the identification is published with ZERO DOF (the N-1-1 TSL minus a 660 MW loss-of-source the model already carries twice). THE DEFAULT IS PROMOTE, because that is what the pre-registration and the owner's own D2 ruling specify and the arm met them (reading A: rule 14 [R-ACCURATE] / rule 1 [R-STRUCT] both say keep the accurate input and treat the C3c collapse as a DISCOVERED BUG, with the downstate scarcity mechanism as the named successor). The alternative (reading B: build the scarcity mechanism FIRST so the accurate input does not land on a representation left emptier than it started) is POST-HOC -- not a pre-registered criterion and not one of the charter's -- and needs the owner to adopt it affirmatively. CORRECTED session recommendation: follow the pre-registration, READING A, unless the owner adopts B. DO NOT RE-SOLVE THIS A/B: it is done, registered and committed; what is open is the ruling. The named root-cause successor is THE DOWNSTATE SCARCITY MECHANISM -- the same object nyiso-110 named from the reserve side and nyiso-124 located as a downstate/in-city price-formation gap." },
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
    hindcast_verified_announced_exits: { cell: ".", fc: "U" },
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
