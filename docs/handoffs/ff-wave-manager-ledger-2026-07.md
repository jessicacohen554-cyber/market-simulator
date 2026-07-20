# FF Wave-Manager Ledger (Forecast Finalization Program)

**Owner of this file:** the standing FF wave manager (coordinator session). This is
the manager's memory across context summarization — its **status column, not the
manager's recollection, decides what has been sent / landed**. Updated and pushed at
the end of every manager turn.

- **Plan:** `docs/forecast-development-plan-2026-07.md` (THE PLAN; §6 prompt pack, §7
  standing constraints, §1.2 frontier, §2 tier ladder).
- **Last reviewed `origin/main` HEAD:** `5b9e79c2` (2026-07-20, turn 35 — manager session `turn-1-anm4jn`).
- **Plan base SHA:** `c95176e` (amended in place 2026-07-19 — POC-first re-scope, see directive entry below).
- **OWNER DIRECTIVE (2026-07-19, out-of-band — recorded by the directive's executing
  session, not a manager turn): POC-first re-scope of THE PLAN.** The plan is amended in
  place (§0 two-phase framing, new §2.1b full-solve authorization gate, §6 Waves 3–4
  re-cut): **FF-4A/FF-4B/FF-4C prompts WITHDRAWN** — Wave 4 deferred in full; the
  turn-18 "golden freeze HELD" hardens into outright prompt withdrawal (never restore
  from history). **FF-3A (T2) deferred with its tier** (prompt withdrawn). **FF-3B
  re-scoped** — W3-R readiness + a T1-scale (ERCOT 2026–2030) CES POC only; the W4
  2026–2050 campaign is deferred, so the issued turn-14 FF-3B prompt is **SUPERSEDED —
  re-emit from the amended plan §6 before any launch**. **FF-3E [OPUS] ⛔ chartered**
  (full-solve readiness battery + POC close-out; absorbs FF-4B's honest-unfit list;
  adds the run_full_horizon.py >5-solve-year guard). Hard cap: **≤5 solve-years per
  invocation, program-wide**. Long solves reopen per ISO only through §2.1b: backcast
  keeper + calibration-complete marker, T1 POC gates green, crossover input gap +
  readiness battery + projected cost, and an explicit per-campaign owner authorization.
  Status-table rows updated below; active front unchanged (FF-2B).
- **turn 35 (manager `turn-1-anm4jn`, refresh). `15dfe15f→5b9e79c2` (16 merges). FF-2C-rig
  LANDED VERIFIED-PASS (#2654/#2662, branch `ff-2c-net-cone-curve-isos-mhn006`); FF-2D IN FLIGHT
  (branch `claude/t1-gate-scoring-zrc3xa` on origin, unmerged). No new dispatches — the wave is
  FF-2D running.** **FF-2C-rig verification (all 3 items ✓):** (1) `_net_cone_scalar` now
  preserves `demand_curve`/`net_cone_curve_per_kw_yr`/`seasonal_rbdc` and scales the CURVE anchor
  — registry AND per-delivery-year `MARKET_DESIGN_VINTAGES` (the vintage override would have
  silently bypassed a registry-only scale); verified to move the PJM curve price EXACTLY 2.0× at
  2× (old patch: flat fixed-fallback ~1.43×). Bonus second genuine defect found+fixed: all T1.7
  rungs shared one solve cache (scalar is a worker-level patch outside cache_key) pinning every
  dispatch metric to rung 0 — `make_rung_specs` now namespaces per rung (explains §2.2's
  single-lw_price signature). (2) economic-vs-exogenous retirement split via the RC-1B ledger
  reason field. (3) PJM T1.7 re-measured on the fixed rig: economic retirements 0.797→0→0 GW
  across {0,1,2}× — **T1.7a PASS (monotone_down)**; exogenous exactly flat 4.575 GW (control ✓);
  ERCOT negative control byte-identical ✓; findings doc §2.3 supersedes the flat-11.836 artifact.
  Rig repair only, no tuning — rules 1/13 clean. **Out-of-program (13):** #2651 (ledger t34),
  #2652/#2658/#2664 (miso-80 direction-symmetric loss), #2653/#2661 (caiso-belly-evening decomp),
  #2656 (stgas-band-hour-frontier), #2650 (ercot-91), #2655 (nyiso-65 scr-edrp land — archive
  solve script + loader test; marker state unchanged), #2657/#2665 (phase-refactor artifact-io),
  #2663 (test-helpers, branch still open), **#2659/#2660 (secrets remediation: a committed `.env`
  with 5 free data-portal API keys (EIA, MISO×2, ERCOT, data.gov) — leaked since the
  benchmark-corridor era — untracked, keys-only `.env.example` + `env_keys.py` resolver added,
  fetchers ported, and a rotation + no-history-rewrite decision DOCUMENTED. ⚠ Owner flag: verify
  the 5 keys were actually rotated at the portals — the repo can only document the decision, not
  prove rotation; the values remain in git history by explicit decision).** Rule-27 clean
  (4269/8102/7627/2470 — all flat). Next unlock: FF-3E when FF-2D lands verified-pass.
- **turn 34 (manager `turn-1-anm4jn`). `40dde11→15dfe15f` (19 merges). FF-2C LANDED
  VERIFIED-PASS (#2645/#2647/#2649, branch `capacity-market-clearing-flips-mvy7al`) — Wave 2
  CLOSES; FF-2D DISPATCHED; slim FF-2C-rig follow-up dispatched (parallel-safe).**
  **FF-2C verification:** (item 1 ✓) `capacity_market_clearing_by_iso` default →
  {PJM,MISO,CAISO,NEISO: True} via the one `resolve_capacity_market_clearing` seam;
  NYISO/ERCOT deliberately absent; backcast `__post_init__` coercion keeps every keeper
  cache-key byte-identical (hindcast NOT coerced so pairs stay scoreable); R4 re-derived all
  four fixed anchors to published-basis (PJM 77.431 = 212.14 $/MW-day BRA 2026/27; MISO 79.8;
  NEISO 108.94 FCA-18; CAISO 88.08 = exact CPM soft-offer cap ER24-1225), reconciliation tests
  tightened; rule-27 blob attestation in-doc. (item 2 ✓ partial-with-cause) PJM+MISO curve-ON
  hindcast re-scores REGISTERED on the shipping D1=3/R4 config (`{pjm,miso}-2021-2025-curve-ff2c`)
  — both honest band-FAIL: at the current mis-based (too-long) position the curve pays ~$0, so
  the wave lands on wrong classes (PJM 18.2/11.1 GW +63%, nuclear-inversion 4.1 GW false
  PERSISTS; MISO 10.8/15.2 −29%, gas_st 8.6 vs 0) — rule-1 discipline held: routed to
  retirement-rule/BLK-10/BLK-3-position lanes, nothing tuned. T1.7 ladder attempted → found a
  GENUINE RIG DEFECT: `run_driver_battery.py:595` `_net_cone_scalar` patches the bypassed fixed
  anchor and drops `demand_curve`/`net_cone_curve_per_kw_yr`, so the ladder is uninformative
  post-flip (ERCOT negative control byte-identical ✓); fix routed → **FF-2C-rig dispatched this
  turn**. Documented deferrals accepted: CAISO hindcast (flip is a pricing no-op by construction
  — flip memo §1.5), NEISO (FF-2B curve leg reusable — R4 touched only the fixed anchor),
  equilibrium T-R5 25-yr + tornado (correctly NOT run — §2.1b makes a 25-yr leg unschedulable;
  status is gate-blocked, not owed). (item 3 ✓) assessment rows 7-12/14 + gap-register updated
  (#2645); parameter-citations + methodology spec synced (#2647). **PJM position caveat carried
  to FF-2D:** flipped curve prices $0 until the BLK-3 R2/R3 requirement/position half lands.
  **Out-of-program (16):** #2631 (ledger t33); **G-series (owner-launched forecast-input lanes,
  FF-adjacent — ALL are FF-2D baseline-attribution inputs):** FF-G2 #2637 (fuel-forward →
  AEO2026, constants.py), FF-G3 #2633/#2638/#2639/#2641/#2648 (forward net-CONE evolution —
  core + tests + methodology + owner-decision box), FF-G4 #2643/#2644 (load-shape design memo
  only), FF-G5 #2640 (nuclear-license registry + `data/nuclear_license.py` loader +
  owner-decision box); plus #2632/#2634/#2646 (caiso-m1/meve1 execution), #2635 (caiso-dam
  intake), #2636/#2642 (ercot-90/91 stgas-shoulder). G3/G5 carry owner-decision boxes (their
  lanes', not FF's). Rule-27 clean: scenarios.py 7997→8102, constants.py 7604→7627 (growth
  only; 4269/2470 flat). Unmerged branch: ercot-91 (out-of-program lane).
- **turn 33 (manager `turn-1-anm4jn`, refresh). `a615fe3→40dde11` (3 merges). QUIET for FF.**
  t32 ledger on main (#2628). Out-of-program: #2630 (caiso-103/92 rederive), #2629 (ercot-89
  shoulder-online mechanism — scenarios.py +35 gated ERCOT fields). Rule-27 clean
  (4269/7997/7604/2470 — scenarios growth only). FF-2C STILL awaiting launch; re-emitted at
  owner request, drift-checked at `40dde11` (no merged change touches its scope — #2629 is
  ERCOT-only, FF-2C never touches ERCOT). ⚠ NEW unmerged branch on origin:
  `claude/ff-g4-load-shape-design-69133d` — carries an "ff-" prefix but is NOT a manager-
  dispatched id (G-4 = gap-register load-shape item; presumably owner-launched design session).
  Classify when it lands; not verified by this ledger until then.
- **turn 32 (manager `turn-1-anm4jn`, refresh). `cbff148→a615fe3` (10 merges). QUIET for FF —
  FF-2C still awaiting worker launch (no branch on origin); nothing unlocked, no corrections.**
  t31 ledger on main (#2621). Out-of-program (9): #2619/#2624 (calendar-metrics refactor
  continuation), #2620 (caiso-103/caiso-92 rederive — CAISO backcast lane), #2622/#2623
  (MISO/PJM DAM intakes), #2608 (backcast-artifacts refactor, late merge), #2625
  (transmission-expansion data intake — new schema + per-ISO registries + cited source docs;
  FF-adjacent future forecast input, additive-only), #2626 (gasshape §3.7 wrap), **#2627 (NYISO
  recovery progress: keeper → nyiso-65-scr-edrp — SCR/EDRP emergency DR as endogenous
  price-responsive supply at the published $500/MWh EDRP strike, rule-13/17-admissible, ZERO new
  free parameters, LOYO-clean improvement (2025 C3a +4.8→+2.8%); determination STILL NOT-YET on
  2023 C3a/C3b only (cheap-gas-2023 offer-level overshoot), marker stays WITHDRAWN → NYISO flip
  deferral STANDS; two named levers remain: downstate heat-rate/fleet-assignment check vs C1
  bench + hydro/PS reserve eligibility)**. Rule-27 clean (4269/7962/7604/2470 unchanged).
  Active front: FF-2C (sent t31, awaiting launch); FF-2D queued behind it.
- **turn 31 (manager `turn-1-anm4jn`). `0e5983f→cbff148` (3 merges: #2614/#2618 miso-dam
  intakes, #2616 ledger t30 — quiet). OWNER DECISION RECEIVED: FF-2C flip sign-off DELEGATED to
  the manager ("You can flip them all on if you think they're ready so we can move forward"),
  manager call recorded: APPROVED = PJM, MISO, CAISO, NEISO; NYISO DEFERRED — sole ISO whose
  train determination is NOT-YET AND whose flip-gate pair evidence (FF-3D-run) was produced on
  the corrupted pre-re-audit outage envelope (rule-11 taint); it auto-joins the flip queue when
  re-calibration lands + pair regenerates on the corrected envelope, no new charter. NEISO
  approved on rule-1 grounds (FCM is the real market design; its failing pair bands are a
  root-cause item, never a flip blocker — worsened fit routes to root-cause, not revert).
  **FF-2C [OPUS] DISPATCHED** (re-emitted drift-clean from plan §6 at `cbff148`: 4-ISO scope,
  NYISO exclusion + rationale, FF-2B findings as read-first, ≤5-yr cap restated, rule-1 NEISO
  note, push-integrity rules). FF-2D unlocks on FF-2C landing verified-pass (flips-first
  sequencing per manager recommendation, now moot — owner chose flips).
- **turn 30 (manager `turn-1-anm4jn`, refresh). `9fa016b→0e5983f` (8 merges). FF-3B LANDED
  VERIFIED-PASS (#2613) — Wave-3's only active prompt closes; the program is now fully blocked
  on the owner's FF-2C/FF-2D decision.** FF-3B verified against all 3 items: (1) **W3-R verdict =
  NO-GO** for the W4 premium-ladder campaign (`docs/handoffs/ces-w3r-readiness-2026-07.md`) —
  R1 NOT MET (ERCOT hindcast solar entry 0.0 GW vs 25.08 actual; PJM overshoots 19.32 vs 13.07),
  R2 NOT MET (exit magnitude fixed but composition inverts 100% onto gas_st, unit-recall 0.0;
  revenue-basis fix named + open), R3 MET (PJM coal exit 11.54 GW, 76.5% unit-recall, band PASS,
  BLK-9 broken), R4 PARTIAL (PJM I7 passes post-W2-D; NEW multi-year I4 leak "A1" open + golden
  band-test frozen/unverified at HEAD) — blocking list routed to lanes, quarantine-legal method
  (committed-evidence read, no 2026-2050 re-run; §2.1b-compliant by construction); (2) **T1-scale
  CES POC = machinery-proven**: full W4 pipeline (matrix_configs → run_scenario_iso → market-sim
  matrix → report_ces_campaign.py → register_forecast_baseline.py) ran end-to-end on ERCOT
  2026-2030 × {BAU, CES-20, CES-40} — each leg its own 5-solve-year invocation (≤5-yr cap ✓),
  registered `kind="ces-poc"` (`frontend/data/hindcast/ercot-2026-2030-ces-poc-*.json`, meta
  verified), no premium-ladder conclusions drawn; premium demonstrably moves the whole surface
  (clean_share 0.400→0.506, solar captured price $30→$1.4/MWh at CES-40 — the §6 cannibalization
  story reproduced structurally); 3 findings fixed-at-POC-scale or routed (incl. F-3:
  generate_financial_reports.py not runnable on fresh checkout — W4-B prerequisite); (3) wall/RSS
  §2.4 ledger delivered in the findings doc (~132-137 s/yr, 3.7-4.2 GB peak, with the explicit
  NON-LINEAR caution for FF-3E: early years are a firm lower bound, late-horizon LPs grow
  super-linearly — do not extrapolate flat). **Interpretive call (flag, accepted):** the prompt
  nests the POC under "On GO:"; the worker ran it despite NO-GO with a documented decoupling
  rationale (POC = plumbing proof per plan §0 Phase A, independent of screen-fitness for
  conclusions) — consistent with program intent; noting for the record, no correction. Also
  noted: the worker solved on session-start tree `57ed9fc` and rebased onto `415df68` with a
  documented no-touch argument. **Out-of-program (7):** #2605/#2612 (ercot-88/89 lane — #2612
  amends CLAUDE.md rule 15: KEEPER bundles now commit hourly/ sidecars, + run_calibration_full.py
  sidecar writer + tests — governance infra, content-reasonable), #2607/#2610/#2611 (PJM DAM /
  NEISO operable-capacity / MISO outage data intakes), #2609 (phase-refactor calendar-metrics —
  new src/utils/hour_calendar.py + metrics.py touch), #2606 (ledger t29). **Rule-27 clean:** all
  four core counts unchanged (4269/7962/7604/2470). **Nothing dispatchable remains:** FF-2C
  (owner sign-off) → FF-2D → FF-3E → FF-5A is the whole remaining chain; FF-3C stays
  trigger-gated (the POC's I9-adjacent negative-price/degeneracy signals at CES-40 and the A1/I4
  leak are FF-2D-input material, not yet a measured §2.4 budget breach).
- **turn 29 (manager `turn-1-anm4jn`, refresh). `735e302→9fa016b` (10 merges). QUIET for FF —
  nothing FF landed beyond my t28 ledger (#2595 merged), nothing unlocked, no corrections.
  FF-3B still awaiting worker launch — no branch on origin.** Out-of-program (9): #2596 (NYISO
  fuel-mix curation, curate_generation.py +85), #2597/#2602 (ercot-89 shoulder-online probe +
  measurement + ercot86 hourly parquets), #2598 (phase-refactor reserve-req unify — per-ISO
  modules consolidated into shared `data/reserve_requirements.py`, genuine refactor, net +220),
  #2599/#2600/#2603 (backcast-artifacts refactor — new scripts/lib modules + tests incl.
  `holdout_policy.py`), **#2601 (capacity-cost-grounding-complete — constants.py +280/−103:
  Li-ion storage capex/FOM RE-DERIVED from the committed NREL ATB extract via
  derive_cost_benchmark_envelope.py + asserted by test, replacing hand-set values whose
  ATB/BNEF labels matched no published point; cited, rule-15-clean. FF-RELEVANT: moves storage
  entry economics → FF-2D's regression-vs-FF-0B-baseline must name this causal merge for any
  storage-entry metric shift)**, #2604 (NYISO SCR/EDRP demand-response intake + loader —
  FF-adjacent: a future cited NYISO DR supply credit could narrow its I7 hydro-dominated gap).
  Rule-27 clean: constants.py 7514→7604 (+90 net), capacity.py/scenarios.py/runner.py unchanged.
  Active front: FF-3B (sent, awaiting launch); FF-2C sign-off + FF-2D sequencing still on the
  owner's desk (unchanged from t28).
- **turn 28 (manager `turn-1-anm4jn`, first turn of the successor manager). `30f546e→6b5b6c4`
  (30 merges). FF-2B LANDED VERIFIED-PASS — the active Wave-2 front closes; FF-3B dispatched
  (re-emitted from the amended plan §6); FF-2C/FF-2D sequencing decision surfaced to owner.**
  FF-program merges (8): #2560 (t27 ledger), #2581 (plan POC-first amendment — already recorded in
  the directive entry), #2584 (migration-ledger follow-ups: CES + PB plan docs), and the FF-2B set
  #2582 (NEISO bands pre-registered BEFORE the run ✓ merge order verified), #2586/#2588/#2590
  (patch → APPLY-SPEC → superseded-note: large-file transport fallback, resolved), #2589 (main
  deliverable, 16 files). **FF-2B verified against all 4 prompt items:** (1) CAISO/NEISO/NYISO I7
  reconciled on each ISO's own published basis — NEISO FAIL→PASS (I7 AND I12 clear, 0 FAIL/0 WARN),
  CAISO improved +3,371 MW cited DMM firm-RA imports (still FAIL — residual = hydro-exclusion
  ledger-structure gap, routed to FF-1C with a spec), NYISO unchanged (basis already correct via
  FF-3D; gap ≈ hydro, routed to FF-1C) — central finding: §1.2-5's single-basis-mismatch hypothesis
  holds for NEISO only; (2) NEISO Net ICR replaces the 0.157 NERC stand-in — 30,305/27,298−1 =
  0.1102, FERC ER23-405-000 cited in constants.py, + FCA-17 DR 2,940 MW + imports 567 MW; (3)
  Pass-1B re-score (`results/capacity-price-validation/ff2b-neiso-pass1b.md`) + FIRST NEISO
  hindcast pair 2021–2025 (2022 bridged), bands pre-registered in #2582 before the run; (4) T1-F
  base-year re-runs registered (3 adequacy sidecars in `frontend/data/hindcast/`), gap-register
  updated. Source: `_firm_import_mw()` resolver in capacity.py (additive, no double-count vs
  dispatch import nodes) + cited constants + `TestFF2BAdequacyBasis` (test_capacity.py:1843).
  Bonus: latent `UNSET` NameError on EVERY forecast run (miso-76 regression) fixed — the one-line
  runner.py import landed via `de29a45` (#2587). **⚠ Governance note (flag, not stop-the-line):**
  the worker landed the source commit `96eac04` via a small source-only `git push` after
  `push_files` corrupted the 345 KB constants.py on reproduction and the git-data API was
  proxy-blocked; bytes were exact-on-disk and blob-verified byte-identical local↔remote (rule-27
  intent honored; core files GREW — no truncation), but it deviates from the Git § API-only rule —
  owner may want to bless a narrow "small source-only pack + mandatory blob-verify" exception.
  **NEISO pair EVIDENCE (for FF-2C):** base-year adequacy basis now clean, but the pair FAILs
  T-R bands hard — thermal retirements +880% (gas_cc +4552% false-retire), wind +1681%/solar +311%
  additions overshoot; storage PASSes. NEISO flip-gate items 3–4 are now gradeable and grade FAIL.
  **Out-of-program (22):** #2559/#2561/#2567 (docs-index + backcast-artifact-contract), #2563/#2574
  (caiso-102 hourfix keeper), #2564/#2566/#2568/#2572 (refactor consolidation — scripts/lib only),
  #2565 (gas daily-shape interp fix, fuel.py + tests), #2569/#2570/#2575/#2580 (ercot-86/88 —
  #2569 adds gated+cited faststart-pool fields to constants/scenarios), #2571/#2578 (**NYISO
  refix: keeper pointer → nyiso-64 (owner-authorized), determination NOT-YET (2023 C3a/C3b),
  marker + frontier stay WITHDRAWN** — NYISO still NOT flip-ready; root cause was missing eastern
  AC seam landing, real fix in interchange_config.py), #2576 (pjm-dataminer refactor), #2577
  (stale-refs docs incl. CLAUDE.md architecture-tree refresh — content-accurate), #2579
  (environment-block repro recorder in run_calibration_full.py, additive), #2583/#2585/#2587
  (capacity-pricing-review: new-build cost-benchmark corroboration intake; FF-1E's ATB test
  relaxed exact→bracket WITH the invariant preserved (envelope equality asserted in the new
  test_cost_benchmark_envelope.py) — FF-adjacent, clean). **Rule-27 clean:** capacity.py 4241→4269,
  scenarios.py 7930→7962, constants.py 7434→7514, runner.py 2469→2470 — all growth, no shrink.
  **Dispatched this turn: FF-3B [OPUS]** (re-emitted from amended plan §6 — W3-R readiness +
  T1-scale ERCOT 2026–2030 CES POC only; W4 stays deferred). FF-2D still gated: its prereq
  "Wave-1/2 lane merges complete" leaves owner-gated FF-2C outstanding → sequencing decision
  surfaced (sign off flips now → FF-2C then FF-2D; or defer flips → FF-2D unlocks at HEAD).
  **Mid-turn addendum (`6b5b6c4→735e302`, 4 merges):** #2591 (FF-2B follow-up — commits the
  `results/ff2b-after/` base-year evolution ledgers + logs, the item-4 evidence artifacts;
  additive, folds into the verified-pass), #2592 (fable-capabilities-priority — out-of-program
  governance infra: calibration-log split per-ISO, keeper-audit hook/agent, CLAUDE.md refresh;
  core counts unchanged), #2593 (caiso-103 probes/asks, out-of-program), #2594 (NYISO fuel-mix
  raw intake 2018–2026 — out-of-program; spans out-of-training years, rule-22 intake channel —
  authorization log assumed in-session, verify next turn if questioned). Rule-27 re-checked at
  `735e302`: unchanged.
- **turn 27 (manager `turn-24-phaekh`, refresh). `0e5cbbe→30f546e` (3 merges). QUIET for FF —
  nothing FF landed, nothing unlocked, no corrections; but one governance-relevant backcast event.**
  My turn-26 ledger reached main (#2557, merge `0e5cbbe`). All 3 merges out-of-program: #2556
  (ercot-87-midband-basis-measurement — probe + 6.9k-line measurement json + design doc, ERCOT
  trough/spread lane), #2555 (miso-78-m4-congestion-charter — charter doc + probe), **#2558
  (pjm-neiso-nyiso phantom-outage re-audit — ERCOT-79 cross-ISO lane).** **⚠️ #2558 WITHDREW NYISO's
  calibration-complete marker** (2026-07-19): NYISO keeper nyiso-62 was calibrated against a
  stale/under-counted outage extract (1,598 vs 2,641 rows); on the consolidated detector the recipe
  re-solves VERBATIM to NOT-YET (C1/C3a/C3b FAIL) — rule-11 co-dependence on the inaccurate
  availability envelope. NYISO marker now in `withdrawn{}`; CI quarantine re-blocks all NYISO
  out-of-training solve/score; the 2019+H1-2026 locked test was NEVER spent and stays available.
  **NEISO HOLDS** (re-audit reproduced its determination byte-for-byte, TRAIN keeper → neiso-60
  corrected envelope). Current markers: **COMPLETE = {NEISO}; WITHDRAWN = {NYISO}** (CAISO/ERCOT/
  PJM/MISO carry no marker in this file). **Impact on FF:** FF-2B is NOT blocked — its ≤2021
  hindcast pair is NEISO-only (marker present ✓), and its CAISO/NYISO work is base-year forecast
  reconciliation + Pass-1B no-LP (no out-of-training solve). But **FF-2C NYISO flip readiness is now
  gone** — NYISO must re-calibrate before any per-ISO flip sign-off. Rule-27 clean (capacity.py 4241,
  scenarios.py 7930, constants.py 7434, runner.py 2469 — unchanged). **Active front UNCHANGED: FF-2B
  ONLY** (re-emitted drift-clean at HEAD this turn on owner request; still awaiting worker launch —
  no branch on origin).
- **turn 26 (manager `turn-24-phaekh`, refresh). `567ef3c→7544814` (8 merges). QUIET — nothing FF
  landed, nothing unlocked, no corrections.** My turn-25 ledger reached main (#2549). All 8 merges
  out-of-program: #2545 (caiso-charge-economics probes, 2 scripts), #2547 (caiso-100 cycling-cost +
  caiso-101 chp-steam backcast keepers — touches scenarios.py +53 with new **gated/cited** CHP-steam
  fields `p25_allhr_cf` etc, WP-3 rule-23 re-derivation, measured/on-registry, backcast train years —
  governance-clean), #2548 (ercot-86-rt-wall-2025 — ERCOT trough/spread lane, adds 66MB 2025 tail-days
  parquet + condbinned wall json + run bundles, train year), #2550 (miso-77-lane-selection, docs-only:
  calibration-log + M4 AFC-feasibility handoff), #2551 (**phase-refactor/root-cleanup** — deletes
  stray root zips/logs/probe-test file, moves docs, renames egrid file; only 2–4-line path updates in
  egrid.py/ownership.py/zone_assignment.py — no truncation), #2552 (**phase-refactor/retention-sweep**
  — 1982 files, **413,645 deletions**: prunes old calibration bundles run98*/run99* + updates
  dashboard_add_run.py/regen_dashboard.py/check_registry_payload_parity.py; **no src/ deletions, no FF
  frontend/backcast artifacts touched** — verified clean), #2553 (dead-inputs-paths-audit — 18 scripts,
  small path-guard additions, scripts-only), #2554 (caiso-inelastic-evening-merit — 3 probe scripts).
  Phase-refactor (#2551/#2552) + audit (#2553) are the codebase-refactor initiative (#2533 plan) in
  execution — separate from FF; the 413k-deletion retention sweep is large but clean — flag to owner
  for awareness. **Rule-27 clean:** capacity.py 4241 (=), scenarios.py 7930 (+7 vs 7923), constants.py
  7434 (=), runner.py 2469 (=) — no shrink. **Active front UNCHANGED: FF-2B ONLY** (still sent,
  awaiting worker launch — no branch on origin). No FF-2B/2C/2D branch appeared. Nothing to correct
  or unblock; FF-2C stays owner-gated pending FF-2B.
- **turn 25 (manager `turn-24-3lfbsn`, refresh). `48ae665→567ef3c` (12 merges). TWO FF LANES
  LANDED verified-pass; the 3-non-delivery saga on the posture flip is CLOSED.** FF-2A-posture-redo
  (#2539) = verified-pass: scenarios.py:1248 `entry_lookahead_reprice` default False→True +
  `__post_init__` backcast coercion + plan §2.1a **row e** + measured-cache-key byte-identity
  attestation (ERCOT backcast key `c44c3d9b7549de73` unchanged; forecast key shifts as intended) —
  4th attempt on this lineage finally landed the source change. FF-1E-policy (#2535 doc + #2540
  constants.py) = verified-pass, item 2 COMPLETE: IRA/OBBBA verified CURRENT (no-change = correct
  disposition); NEISO ACP `65.0→50.0` the sole runtime delta, cited verbatim (225 CMR 14.08); PJM
  load weights → primary Monitoring Analytics 2024; confirmed-retire re-query → no binding instrument.
  Backcast byte-identical by construction. Rule-27 clean. Out-of-program (8): miso-76, caiso-belly-charge,
  ercot-86-rt-wall, miso-zonal-loss-surface, #2533 codebase-refactor plan.
- **turn 24 (manager `turn-24-3lfbsn`). `270f429→48ae665` (3 merges). QUIET.** t23 ledger on main
  (#2530). #2531 (miso-zonal-loss-surface data-intake, data-only), #2532 (caiso-99 storage-shape
  keeper). Rule-27 clean.
- **turn 23 (manager `yjegie`). `37d3923→270f429` (5 merges). QUIET.** t22 ledger on main (#2525).
  #2526/#2529 (miso-76), #2527 (ercot design memo), #2528 (peer-review doc). Manager-handoff prompt
  emitted at owner request.
- **turn 22 (`→37d3923`).** FF-1E COMPLETION #2518 verified-pass (items 1/3/4). FF-1E-complete
  RETRACTED; genuine non-deliveries corrected 4→3. Only item 2 remained → slim FF-1E-policy [OPUS].
- **turn 21 (`→a57194d`, 7 merges).** FF-0B-redo (#2517) + FF-1D (#2519) verified-pass.
  FF-2A-posture (#2522) 3rd genuine NON-DELIVERY → FF-2A-posture-redo + escalated push-integrity
  pattern to owner.
- **turns 10–20 (collapsed).** t20: FF-1E #2515 read as non-delivery → FF-1E-complete (later
  RETRACTED t22). t19: FF-0E verified-pass (#2514) → FF-1D released. t18: FF-2A measurement landed
  (#2506/#2509); FF-0E launched; posture=ON approved; golden freeze HELD. t17: #2503 stale-patch
  delete + #2505 FF-0F close. t15: FF-2A integration MERGED (#2486); FF-1F defaults live (#2493).
  t14: capacity.py re-truncated (#2474/#2477) → owner-RESTORED (#2481). t13: FF-3D landed (#2463)
  → FF-3D-run. t12: owner decisions (flips all-but-ERCOT, R5a=B, DC=mid, derate=ON). t11: FF-2A
  integrity breach (#2453) → FF-2A-integrate; FF-1A-C2 verified-pass. t10: FF-1A-C landed. t7: main
  restored (#2438).

Status vocabulary: `not-sent` · `sent` · `landed` · `verified-pass` ·
`verified-issues` · `correction-sent`.

---

## Session status table

| FF id | Model | Wave | Lane | Gate | Status | Evidence |
|---|---|---|---|---|---|---|
| FF-0A | FABLE | 0 | L-VAL | ⛔ rubric | **verified-pass** | rubric #2414 + scorer #2419 |
| FF-0A-fix | OPUS | 0 | L-VAL | — | **verified-pass** | #2419: 73 tests pass |
| FF-0B-redo | OPUS | 0 | L-VAL | — | **verified-pass (turn 21)** — #2517 | 6-ISO T1-F baseline 2026-2030: findings doc + 6 real ISO sidecars + register_forecast_baseline.py. #2412 non-delivery FIXED. BEFORE legs for Wave-1/2. |
| FF-0C | FABLE | 0 | L-CAP | — | **verified-pass** | #2418: R-NEW memo + owner box |
| FF-0D | OPUS | 0 | L-INP | — | **verified-pass** | #2413: audit, no source changes |
| FF-0E | OPUS | 0 | L-VAL | — | **verified-pass (turn 19)** — #2514 | Crossover harness + score_crossover.py + 2 tests. ≥2026 reads structurally refused (rule 22), no default changed. |
| FF-0F | OPUS | 0 | L-VAL/L-INP | — | **verified-pass, CLOSED (turn 17)** | #2488 + #2490 + #2505: benchmark-corridor datatype + loader + 13 tests + FC-5 context-only wiring; additive. |
| FF-1A | FABLE | 1 | L-CAP | — | **verified-pass (complete)** | #2438 + #2448/#2451 + #2454. Inversion CLOSED; flip-gate scorecard complete. |
| FF-1A-restore | FABLE | 1 | L-CAP | — | **verified-pass** | #2438: capacity.py byte-exact restore. |
| FF-1A-C | FABLE | 1 | L-CAP | — | **verified-pass (via FF-1A-C2)** | #2448/#2451: 3 R-NEW legs scored. |
| FF-1A-C2 | OPUS | 1 | L-CAP | — | **verified-pass** — #2454 | doc synced, 0 PENDING. FF-1A complete. |
| FF-1B | FABLE | 1 | L-SCAR | — | **verified-pass** | #2423: correlated cold-event derate. |
| FF-1C | OPUS | 1 | L-INP | — | **verified-pass** | #2422: demand/DC currency + hydro. |
| FF-1D | OPUS | 1 | L-VAL | — | **verified-pass (turn 21)** — #2519 | Crossover ERCOT+PJM 2023→2027: input-gap doc + 2 crossover sidecars + 2 run reports. Quarantine holds BY CONSTRUCTION; leakage clean. |
| FF-1E | OPUS | 1 | L-INP | — | **verified-pass, items 1/3/4 (turn 22)** — #2515+#2518 | Two-PR lane: constants.py ATB-derived (cited) + `test_atb_entry_cost_consistency.py` + per-tech WACC option (default-off) + findings. entry_lookahead_reprice untouched; rule-27 clean. |
| FF-1E-complete | OPUS | 1 | L-INP | — | **RETRACTED (turn 22)** | Superseded by #2518. Replaced by slim item-2-only FF-1E-policy. |
| FF-1E-policy | OPUS | 1 | L-INP | — | **verified-pass, item 2 COMPLETE (turn 25)** — #2535+#2540 | IRA CURRENT (no-change = correct); NEISO ACP 65→50 sole runtime delta, cited (225 CMR 14.08); PJM weights refreshed; confirmed-retire no-add. Backcast byte-identical by construction. Closes FF-0D §7.2 P2. |
| FF-1F | OPUS | 1 | L-INP | — | **landed + defaults LIVE** (#2468/#2476/#2480 + #2493) | DC=mid, derate=ON with backcast byte-identity guards; plan §2.1 recorded. Closed. |
| FF-2A | FABLE | 2 | L-CAP | — | **COMPLETE (turn 18) — mechanism + measurement both landed** | Mechanism #2486 (t15); measurement #2506/#2509 (t18). VRE cap-rev near-pivotal → G-20/G-22. Full manager-verify pending (deferred). |
| FF-2A-integrate | FABLE | 2 | L-CAP | — | **verified-pass (turn 15, via #2486 + #2491/#2492)** | 0 fn loss, on-registry, compiles. Lane CLOSED. |
| FF-2A-posture | OPUS | 2 | L-CAP | — | **verified-issues, NON-DELIVERY (turn 21)** — #2522 | Doc-only; scenarios.py UNCHANGED. 3rd genuine non-delivery. → FF-2A-posture-redo. |
| FF-2A-posture-redo | OPUS | 2 | L-CAP | — | **verified-pass (turn 25)** — #2539 | Landed the flip #2522 only described: scenarios.py `entry_lookahead_reprice` False→True + backcast coercion + plan §2.1a row e + measured-cache-key byte-identity attestation. Closes the 3-non-delivery saga. |
| FF-2B | OPUS | 2 | L-CAP | — | **verified-pass (turn 28)** — #2582+#2586/#2588/#2590+#2589+#2591, source `96eac04` | All 4 items: NEISO I7+I12 PASS (Net ICR 0.1102, ER23-405-000), CAISO +3,371 MW cited (residual→FF-1C hydro), NYISO basis-correct (residual→FF-1C); Pass-1B + FIRST NEISO pair (bands pre-registered #2582 before run); T1-F base-year sidecars + gap-register. Bonus UNSET runner.py fix. ⚠ git-push deviation, blob-verified — owner note. |
| FF-2C | OPUS | 2 | L-CAP | — | **verified-pass (turn 34)** — #2645/#2647/#2649 | Flip {PJM,MISO,CAISO,NEISO}=ON + R4 published anchors + byte-identity coercion + tests. PJM/MISO curve hindcasts registered (honest FAILs, routed). T1.7 rig defect found → FF-2C-rig. CAISO no-op / NEISO reuse / T-R5+tornado §2.1b-blocked — documented, accepted. Wave 2 CLOSED (NYISO flip pends re-calibration). |
| FF-2C-rig | OPUS | 2 | L-CAP | — | **verified-pass (turn 35)** — #2654/#2662 | Curve-anchor scaling (registry + vintages) verified exactly 2.0×; bonus rung-cache-namespace defect fixed; econ/exogenous split; PJM T1.7a PASS monotone_down (0.797→0→0 GW econ; exogenous flat 4.575); ERCOT control clean. Findings doc §2.3. |
| FF-2D | OPUS | 2 | L-VAL | — | **sent (turn 34), IN FLIGHT t35** — branch `t1-gate-scoring-zrc3xa` on origin | T1 gate battery at HEAD (record SHA): T1-F 6 ISOs on flipped defaults, T1-X, T1-H probe legs; rubric verdicts + promotion table; regression vs FF-0B naming causal merges (#2601 storage costs, FF-G2 AEO2026 fuel, FF-G3 net-CONE evolution, FF-G5 nuclear registry, FF-2C flip+R4); folds FF-3B A1/I4 leak + frozen-golden + PJM position caveat. Eligibility ≠ scheduling (§2.1b). |
| FF-3A | — | 3 | L-VAL | ⛔ T2 | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | T2 deferred with its tier behind plan §2.1b; prompt re-authored at gate-open. Do not dispatch. |
| FF-3B | OPUS | 3 | L-CES | — | **verified-pass (turn 30)** — #2613 | W3-R = NO-GO (R1/R2 NOT MET, R3 MET, R4 partial; routed). POC = machinery-proven: 3×5yr legs, kind="ces-poc", premium moves full surface; wall/RSS ledger + nonlinear caution for FF-3E. POC-despite-NO-GO decoupling accepted (plan §0 Phase A). L-CES lane CLOSED until §2.1b gate-open. |
| FF-3C | FABLE | 3 | L-PERF | conditional | not-sent | trigger-gated — inactive (only remaining FABLE prompt); trigger re-worded to active-tier breach (plan §6) |
| FF-3D | OPUS | 3 | L-CAP | — | **verified-issues (incomplete)** — LANDED #2463 | Intake + Option-B pairing + pre-registered bands; flip-gate Basis PASSES. Pair run via FF-3D-run. |
| FF-3D-run | OPUS | 3 | L-CAP | — | **landed** (#2471/#2473/#2478 + `5bb0c9b`) | NYISO fixed/curve/realized pair registered. Closed. ⚠ t31: pair evidence rule-11-tainted (pre-re-audit envelope) — regenerate before NYISO flip. |
| FF-3E | OPUS | 3 | L-VAL | ⛔ §2.1b evidence | not-sent | NEW (owner 2026-07-19): full-solve readiness battery + POC close-out (absorbs FF-4B honest-unfit list; adds >5-yr CLI guard). After FF-2D. Wall/RSS anchor now in hand (FF-3B §2.4 table + nonlinear caution). |
| FF-4A | — | 4 | L-VAL | ⛔ | **WITHDRAWN (owner 2026-07-19)** | Prompt withdrawn outright (was HELD t18); Wave 4 deferred behind §2.1b. Do not dispatch, do not restore from history. |
| FF-4B | — | 4 | L-VAL | — | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | Honest-unfit list moved to FF-3E close-out; rest re-authored at gate-open. |
| FF-4C | — | 4 | L-VAL | owner-gated | **WITHDRAWN-DEFERRED (owner 2026-07-19)** | PB-5 deferred with Wave 4 (§2.1b). |
| FF-5A | OPUS | 5 | L-DASH | — | not-sent | blocked: active-wave close-out (deferred Wave 4 NOT a prerequisite — §2.1b) |

Out-of-program / trivial (turn 35): #2652/#2658/#2664 (miso-80), #2653/#2661 (caiso-belly
decomp), #2656 (stgas frontier), #2650 (ercot-91), #2655 (nyiso-65 land), #2657/#2665
(artifact-io), #2663 (test-helpers), #2659/#2660 (secrets remediation — rotation flag to owner),
#2651 (ledger t34). (turn 34): #2631 (ledger t33), FF-G2 #2637 (AEO2026 fuel-forward),
FF-G3 #2633/#2638/#2639/#2641/#2648 (forward net-CONE evolution + owner box), FF-G4
#2643/#2644 (load-shape design memo), FF-G5 #2640 (nuclear-license registry + owner box),
#2632/#2634/#2646 (caiso-m1/meve1), #2635 (caiso-dam intake), #2636/#2642 (ercot-90/91).
(turn 33): #2630 (caiso-103/92 rederive), #2629 (ercot-89
shoulder-online mechanism — gated scenarios.py fields), #2628 (ledger t32). (turn 32):
#2619/#2624 (calendar-metrics), #2620 (caiso-103/92),
#2622/#2623 (DAM intakes), #2608 (backcast-artifacts late merge), #2625 (transmission-expansion
intake), #2626 (gasshape wrap), #2627 (nyiso-65 — NOT-YET, marker stays withdrawn), #2621
(ledger t31). (turn 31): #2614/#2618 (miso-dam intakes), #2616 (ledger t30).
(turn 30): #2605/#2612 (ercot-88/89 — #2612 amends CLAUDE.md rule 15
hourly-sidecar keeper requirement + run_calibration_full.py writer), #2607/#2610/#2611 (PJM DAM /
NEISO operable-capacity / MISO outage intakes), #2609 (calendar-metrics refactor), #2606 (ledger
t29). (turn 29): #2596 (NYISO fuel-mix curation), #2597/#2602 (ercot-89
shoulder-online), #2598 (reserve-req unify refactor), #2599/#2600/#2603 (backcast-artifacts
refactor libs + tests), #2601 (capacity-cost-grounding — cited constants.py storage-cost
re-derivation, FF-relevant for FF-2D baseline attribution), #2604 (NYISO DR intake + loader),
#2595 (ledger t28). (turn 28): #2559/#2561/#2567 (docs-index + artifact-contract docs),
#2563/#2574 (caiso-102 keeper), #2564/#2566/#2568/#2572 (refactor consolidation, scripts/lib),
#2565 (gas daily-shape fuel.py fix), #2569/#2570/#2575/#2580 (ercot-86/88 lanes — gated+cited
constants/scenarios fields), #2571/#2578 (NYISO refix — keeper→nyiso-64, NOT-YET, marker stays
withdrawn), #2576 (pjm-dataminer), #2577 (stale-refs docs incl CLAUDE.md refresh), #2579
(env-block repro recorder), #2583/#2585/#2587 (capacity-pricing-review cost-benchmark
corroboration — FF-adjacent; FF-1E test exact→bracket with invariant preserved; carries the
runner.py UNSET fix `de29a45`), #2592 (fable-capabilities-priority governance infra), #2593
(caiso-103 probes), #2594 (NYISO fuel-mix raw intake 2018–2026), #2560 (ledger t27). (turn 27): #2556 (ercot-87-midband-basis-measurement — probe + measurement
json + design doc), #2555 (miso-78-m4-congestion-charter — doc + probe), #2558 (pjm-neiso-nyiso
phantom-outage re-audit — **WITHDREW NYISO calibration-complete marker**, NEISO HOLDS), #2557 (ledger
t26). (turn 26): #2545 (caiso-charge-economics probes), #2547 (caiso-100/101
backcast keepers — gated/cited scenarios.py CHP-steam fields, train years), #2548 (ercot-86-rt-wall-2025
— ERCOT trough/spread lane + 66MB 2025 tail-days parquet), #2550 (miso-77-lane-selection docs),
#2551 (phase-refactor/root-cleanup), #2552 (phase-refactor/retention-sweep — 413k deletions, no src/,
no FF artifacts), #2553 (dead-inputs-paths-audit scripts), #2554 (caiso-inelastic-evening-merit probes),
#2549 (ledger t25). Earlier: #2536 (ledger t24), #2544/#2542 (miso-76), #2543/#2537
(caiso-belly-charge), #2541/#2534 (ercot-86-rt-wall), #2538 (miso-zonal-loss-surface runner.py kwarg
gated/UNSET-off), #2533 (codebase-refactor-consolidation plan — separate initiative), #2530 (ledger
t23), #2531 (miso-zonal-loss-surface data-intake), #2532 (caiso-99 keeper), #2525 (ledger t22),
#2526/#2529 (miso-76), #2527 (ercot design memo), #2528 (peer-review doc), and earlier caiso/miso/ercot
backcast keepers + ledger commits.

---

## Owner decisions

**Received:**
- **D1 = B (R-NEW), by action** (2026-07-18). Done.
- **Capacity-market flips (turn 12):** ON for all ISOs with a real capacity market =
  PJM/MISO/NYISO/NEISO/CAISO (all but ERCOT). FF-2C executes per-ISO by readiness.
  CAISO = RA-not-auction. Rule 1 governs (worsened fit → root-cause, not revert).
- **NYISO R5a = Option B** (turn 12). FF-3D landed the intake.
- **datacenter_load_path default = mid** (turn 12). FF-1F applies.
- **correlated_forced_outage default = ON** (turn 12). FF-1F applies.
- **Entry-lookahead posture = ON** (turn 18, 2026-07-18). FF-2A-posture-redo LANDED it (turn 25, #2539).
- **Golden freeze HOLDS** (turn 18) — until backcast is calibrated on the testing years.
  FF-4A stays gated. **Superseded 2026-07-19: hardened into full Wave-4 prompt
  withdrawal + the plan §2.1b gate (directive entry above).**
- **POC-first re-scope (2026-07-19, out-of-band):** Wave-4 prompts WITHDRAWN, FF-3A/T2
  deferred, ≤5-solve-year cap, §2.1b gate installed; FF-3B re-scoped (W4 deferred,
  T1-scale CES POC); FF-3E chartered. Plan amended in place.
- **#2439** — owner handled → resolved.
- **FF-2C flip sign-off (turn 31, 2026-07-19):** owner delegated the per-ISO call to the
  manager ("flip them all on if you think they're ready"). Manager call: **APPROVED =
  PJM/MISO/CAISO/NEISO; NYISO DEFERRED** (NOT-YET determination + rule-11-tainted gate
  evidence; auto-joins on re-calibration). FF-2C dispatched turn 31. **EXECUTED + verified-pass
  turn 34 (#2645/#2647/#2649) — Wave 2 closed.**

**AWAITING (each changes what I dispatch next):**
- **§2.1b gate-open per ISO** (replaces the former FF-4A golden-freeze and PB-5 waits —
  both WITHDRAWN-DEFERRED 2026-07-19; conditions: backcast keeper + marker, T1 POC
  gates, crossover gap + FF-3E readiness + projected cost, per-campaign authorization).
  FF-3B's W3-R NO-GO (R1/R2) is now recorded §2.1b(b/c) evidence for any future ask.
- ~~Per-ISO FF-2C sign-off~~ **RESOLVED turn 31** (delegated; approved PJM/MISO/CAISO/NEISO,
  NYISO deferred — see Received above). ~~FF-2D sequencing~~ **RESOLVED turn 31** (flips first;
  FF-2D dispatches after FF-2C lands verified-pass). Critical path is now FF-2C execution →
  FF-2D → FF-3E → FF-5A.
- **Rule-deviation note (FF-2B):** worker used a small source-only `git push` (blob-verified)
  when `push_files` corrupted 345 KB constants.py — bless a narrow documented exception, or
  direct an alternative large-file transport; no action needed on the landed bytes (verified).
- **Key-rotation verification (t35, secrets remediation #2659/#2660):** confirm the 5 leaked
  data-portal keys (EIA, MISO×2, ERCOT, data.gov) were rotated at their portals — the repo
  documents the decision but cannot prove rotation.
- **(Out-of-FF-program, flag only)** NEISO holdout-data-equivalency register sign-off
  (`docs/holdout-data-equivalency-register-2026-07.md` §NEISO, rule-22 exit gate before any
  NEISO one-shot). Also: FF-G3 and FF-G5 landed owner-decision boxes in their own lanes.

---

## Corrections issued

1. **FF-0A-fix [OPUS]** (turn 2) — RESOLVED turn 3 (#2419).
2. **FF-0B-redo [OPUS]** (turn 2) — re-issued turn 14/17. **LANDED verified-pass turn 21 (#2517).**
3. **FF-1A-restore [FABLE]** (turn 5) — **RESOLVED turn 7 (#2438).**
4. **FF-1A-C [FABLE]** (turn 7) — **LANDED turn 10 (#2448/#2451).** Doc-sync gap → FF-1A-C2.
5. **FF-1A-C2 [OPUS]** (turn 10) — **RESOLVED turn 11 (#2454), verified-pass.**
6. **FF-2A-integrate [FABLE]** (turn 11) — breach fix. Re-truncated (#2474/#2477) → owner-reverted
   (#2481). Superseded by round-3 — **RESOLVED turn 15** (#2486 + #2491/#2492).
7. **FF-3D-run [OPUS]** (turn 13) — **LANDED** (#2471/#2473/#2478 + `5bb0c9b`).
8. **runner.py orphan revert** (turn 14) — **RETRACTED turn 15.** #2486 forward-fixed it.
9. **FF-1E-complete [OPUS]** (turn 20) — **RETRACTED turn 22.** #2518 completed FF-1E items 1/3/4.
   Genuine non-deliveries = 3. Replaced by slim FF-1E-policy [OPUS].
10. **FF-2A-posture-redo [OPUS]** (turn 21) — non-delivery fix. **RESOLVED turn 25 (#2539),
    verified-pass.** Genuine non-deliveries stay 3 (FF-0B #2412, FF-2A #2453, FF-2A-posture #2522).
11. **FF-1E-policy [OPUS]** (turn 22) — slim item-2-only follow-up. **RESOLVED turn 25
    (#2535+#2540), verified-pass** — NEISO ACP 65→50 the sole cited runtime delta.
12. **FF-2C-rig [OPUS]** (turn 34) — slim T1.7 rig fix, found by FF-2C. **RESOLVED turn 35
    (#2654/#2662), verified-pass** — T1.7a PASS on the fixed rig; bonus rung-cache defect fixed.

---

## Turn log

- **turns 1–16.** Wave 0/1 dispatch + verify; capacity.py truncation saga (t6/t11/t14) restored;
  FF-2A integration (t15); FF-0F closed (t17). See prior ledger commits for detail.
- **turn 17 (`→9b9b0d4`).** #2503 stale-patch delete + #2505 FF-0F close. Re-emitted 4 [OPUS].
- **turn 18 (`→e5d6f29`).** FF-2A completion landed. FF-0E launched. Posture=ON approved; golden
  freeze HELD.
- **turn 19 (`→37b9136`).** FF-0E verified-pass → FF-1D released.
- **turn 20 (`→cf1531d`).** FF-1E #2515 read as non-delivery → FF-1E-complete (later retracted t22).
- **turn 21 (`→a57194d`).** FF-0B-redo (#2517) + FF-1D (#2519) verified-pass. FF-2A-posture (#2522)
  NON-DELIVERY → FF-2A-posture-redo + escalated push-integrity pattern to owner.
- **turn 22 (`→37d3923`).** FF-1E COMPLETION #2518 verified-pass. FF-1E-complete RETRACTED;
  non-deliveries 4→3. → slim FF-1E-policy [OPUS].
- **turn 23 (`→270f429`).** QUIET. t22 ledger on main (#2525). Manager-handoff prompt emitted.
- **turn 24 (`→48ae665`).** QUIET. t23 ledger on main (#2530). #2531/#2532 out-of-program.
- **turn 25 (`→567ef3c`).** TWO FF LANES verified-pass: FF-2A-posture-redo (#2539) — posture flip
  finally landed, 3-non-delivery saga CLOSED; FF-1E-policy (#2535+#2540) — item 2 complete. Rule-27
  clean. 8 out-of-program.
- **turn 26 (`→7544814`).** QUIET refresh — nothing FF landed, nothing unlocked, no corrections.
  t25 ledger on main (#2549). 8 out-of-program merges: caiso-100/101 keepers (#2547, gated/cited
  scenarios.py), ercot-86-rt-wall-2025 (#2548), miso-77 docs (#2550), phase-refactor root-cleanup +
  retention-sweep (#2551/#2552 — 413k deletions, no src/, no FF artifacts), dead-inputs audit (#2553),
  caiso probes (#2545/#2554). Rule-27 clean (capacity.py 4241, scenarios.py 7930, constants.py 7434,
  runner.py 2469 — no shrink). Active front FF-2B only, awaiting worker launch. FF-2C stays
  owner-gated pending FF-2B.
- **turn 27 (`→30f546e`).** QUIET refresh for FF (3 merges, all out-of-program). t26 ledger on main
  (#2557). ⚠️ #2558 phantom-outage re-audit WITHDREW NYISO's calibration-complete marker (rule-11
  co-dependence on under-counted outages); NEISO HOLDS. Markers now COMPLETE={NEISO}, WITHDRAWN=
  {NYISO}. FF-2B unaffected (NEISO-only ≤2021 hindcast); FF-2C NYISO flip readiness lost pending
  re-calibration. FF-2B re-emitted drift-clean on owner request; still awaiting launch. Rule-27 clean.
- **turn 28 (`→735e302`, successor manager `turn-1-anm4jn`).** 34 merges. **FF-2B LANDED
  verified-pass** (#2582 bands-before-run + #2589 deliverable + source `96eac04`; NEISO I7+I12
  PASS on Net ICR basis, CAISO/NYISO residuals routed to FF-1C hydro-ledger, first NEISO pair
  produced — FAILs T-R bands; ⚠ git-push deviation blob-verified, flagged). Plan amendment #2581 +
  follow-ups #2584 on main. NYISO refix (#2571/#2578): keeper→nyiso-64, NOT-YET, marker stays
  withdrawn. Rule-27 clean (all core files grew). **Dispatched FF-3B** (re-emitted from amended
  plan §6). FF-2C sign-off + FF-2D sequencing surfaced as coupled owner decisions. Wave 2 close-out
  now waits only on FF-2C disposition.
- **turn 29 (`→9fa016b`).** QUIET refresh. t28 ledger on main (#2595). 9 out-of-program merges;
  #2601 (storage-cost re-derivation in constants.py, cited) flagged as an FF-2D baseline-attribution
  input; #2604 (NYISO DR intake) noted as a potential future cited I7 credit. FF-3B still awaiting
  launch (no branch). Rule-27 clean. No dispatches, no corrections; owner decisions unchanged.
- **turn 30 (`→0e5983f`).** **FF-3B verified-pass (#2613):** W3-R NO-GO (R1/R2 blockers routed;
  R3 met; R4 partial — new A1/I4 multi-year leak recorded), CES POC machinery-proven at 3×5yr
  ≤cap, kind="ces-poc", wall/RSS ledger with the nonlinear FF-3E caution. POC-despite-NO-GO
  decoupling accepted as an interpretive call. Rule-27 clean. Wave 3's active prompt closes;
  program now fully blocked on owner FF-2C sign-off / FF-2D sequencing. 7 out-of-program.
- **turn 31 (`→cbff148`).** OWNER DECISION: flip sign-off delegated → approved
  PJM/MISO/CAISO/NEISO, NYISO deferred (NOT-YET + rule-11-tainted gate evidence).
  **FF-2C dispatched** drift-clean at `cbff148`. FF-2D queued behind it. 3 quiet merges.
- **turn 32 (`→a615fe3`).** QUIET refresh — FF-2C awaiting launch. t31 ledger on main (#2621).
  NYISO progress noted (nyiso-65 SCR/EDRP lever, still NOT-YET, marker withdrawn — flip deferral
  stands). Rule-27 clean. 9 out-of-program.
- **turn 33 (`→40dde11`).** QUIET refresh. t32 ledger on main (#2628). FF-2C re-emitted at owner
  request (drift-clean at `40dde11`). New unmerged `ff-g4-load-shape-design` branch flagged for
  classification on landing. Rule-27 clean. 2 out-of-program.
- **turn 34 (`→15dfe15f`).** **FF-2C verified-pass (#2645/#2647/#2649) — Wave 2 CLOSES.** Flip +
  R4 + tests + byte-identity clean; PJM/MISO curve hindcasts honest FAILs (routed, rule 1);
  T1.7 rig defect → **FF-2C-rig dispatched**; CAISO/NEISO/T-R5 deferrals accepted with cause.
  **FF-2D dispatched** (unlocked; runs parallel with FF-2C-rig). G-series (FF-G2/G3/G4/G5)
  classified as owner-launched input lanes → FF-2D attribution list. Rule-27 clean.
- **turn 35 (`→5b9e79c2`).** **FF-2C-rig verified-pass (#2654/#2662)** — T1.7a PASS monotone_down
  on the fixed rig; bonus rung-cache defect fixed; corrections item 12 RESOLVED. **FF-2D in
  flight** (`t1-gate-scoring-zrc3xa`). Secrets remediation (#2659/#2660) noted — key-rotation
  verification flagged to owner. No new dispatches; next unlock FF-3E on FF-2D verified-pass.
