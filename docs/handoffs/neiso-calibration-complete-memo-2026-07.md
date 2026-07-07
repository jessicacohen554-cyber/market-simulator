# NEISO calibration-complete adjudication memo (2026-07-07)

**Decision requested from the owner:** declare NEISO calibration-complete —
writing the first entry into `frontend/data/backcast/calibration-complete.json`
and thereby authorizing the one-shot holdout validation (rule 22) — or hold, or
declare-but-defer-the-solve. This memo records the verified preconditions, how
each prior hold reason resolved, exactly what a declaration authorizes, and the
irreversibility terms. Prepared by the `neiso-calibration-complete-w1c` session;
all checks run at main `102f95f` (2026-07-07). No holdout year was touched to
produce this memo.

## 1. The frozen keeper

`2026-07-07-neiso53-winter-fuelsec-coldsnap` (bundle
`results/calibration/neiso53_winter_coldsnap_ab`), solved full-span 2023–2025 at
`7f968f3` (clean tree, branch `claude/neiso-winter-component-b-012p1j`), with the
registered zero-forcing ablation twin `2026-07-07-neiso53-winter-fuelsec-ablation`
(bundle `…_off`). Recipe = the neiso-50 keeper recipe (`--commitment
--reliability-floor --hydro-backfill-year 2024 --hydro-eia930-monthly
--gas-hub-basis-daily --scarcity-price-overlay --tranche-startup-amortization`)
plus the three NEISO winter fuel-security mechanisms ON
(`neiso_gas_coldsnap_derate` + `neiso_winter_fuel_inventory` +
`neiso_winter_fuel_mustrun`), adopted 2026-07-07 per rule 1 after the G-24 probe
proved the stack DORMANT on 2023–2025 (real, forward-derivable ISO-NE winter
structure — WRP ER14-2407 → IEP ER19-1428 → OFSA; NERC Winter Storm Elliott —
kept although it moves no backcast metric).

## 2. Preconditions verified at HEAD (2026-07-07)

- **Re-score:** `scripts/calibration_verdict.py --run-id
  2026-07-07-neiso53-winter-fuelsec-coldsnap` at HEAD reproduces
  **CALIBRATED-WITH-CAVEATS, zero criterion FAILs** — every per-criterion
  status, caveat list, grade summary, reason line, and the D-10 free-class score
  (C1 all 12/12 · free 8/8) byte-match the committed
  `metrics.json` sidecar. Sole difference: the sidecar is stamped
  `rubric_version: 2.1`, the HEAD scorer emits 2.2 — v2.2 only added the
  C8 above-cap grounded-pass path (rubric §9 / CLAUDE.md rule 20 amendment
  2026-07-07), which this keeper never engages (C8 passes below-cap).
- **Caveat budget (rubric v2.2):** ledgered **2/3** (C3c price tail / C5b
  storage throughput — both classified, same winter scarcity-price-formation
  root), protective **0/1** (C7 SKIPPED-immaterial, see §3), commercial-band
  C2/C3a/C3b (auto caveats, unbudgeted: 2025 gas +2.8%; C3a 2023 −6.0% with
  2024 −4.0% and 2025 +0.8% PASSING; C3b 2024 NRMSE 0.157 with 2023/2025
  passing). C1, C4, C5a, C6 PASS.
- **Gates:** `scripts/build_status.py --check` exit 0 (status.js in sync);
  `scripts/audit_keepers.py --check` exit 0 — **NEISO "all checks passed"**: no
  E7 (the newest NEISO registry entries are the keeper and its own twin), no E9
  (twin registered), sidecar/bundle/verdict text consistent, holdout check
  clean. `scripts/legitimacy_diagnostics.py --keepers` (the CI
  `quarantine-gates` job) exit 0, D-2 shares re-derived from committed bundle
  data with no drift.
- **Attestation** (`calibration_attestation.json`): four governance assertions
  true (levers-trace-to-measured-input, no-fit-to-price-residuals,
  no-pinning-to-actuals, outage-filter-exogenous); DOF ledger
  (`dof-ledger/v1`) 12 entries — 6 residual-identified (offer bands 72 scalars,
  smoothing 2, NEISO coal sigmoid 4, wefor, CC peaking pct, import/export
  tranches), the 3 winter mechanisms **measured-physical** (cited, rule 23
  frozen, n_residual unchanged), reliability-floor coefficients
  measured-physical, GAS_AVAILABILITY published; 12 classified exceptions incl.
  the E9-resolution record.
- **Legitimacy D-gates** (committed `legitimacy_diagnostics.json`): D-2
  passed=true (the only non-exempt class Component B forces is COAL at
  0.02–0.35 share of a class worth <0.3% of ISO load — reported-not-gated),
  D-4 no off-window rows, D-5 forecast/backcast parity all-declared, D-9
  overlay quarantine pass.
- **First ISO:** `calibration-complete.json` reads `"complete": {}` — NEISO
  would be the first marker.

Known text-lag items, disclosed (none gate): attestation exceptions 6–8 quote
the neiso-50-era C3a/C3b magnitudes (−10.4%/−8.6%, NRMSE 0.169); the keeper's
own scored values are better (−6.0%/−4.0%/+0.8%, 0.157) because of disclosed
main drift between the two solves — the `use_plant_emission_rates_v2` default
flip, isolated by the registered `2026-07-06-neiso-52-head-baseline` probe. The
gap-register G-16 row and §4 NEISO row still carry neiso-49-era text (updated on
declaration under this lane's file ownership).

## 3. Prior hold reasons (2026-07-06) and how each resolved

Owner held NEISO on 2026-07-06 (gap-register addendum "calibration-complete
adjudication, NYISO + NEISO") "until the winter-fuel Component-B / C7 ST_GAS
residual is re-examined." Both halves are now closed:

1. **Winter-fuel Component B (G-24) — STRUCK 2026-07-07.** Component B was
   built (`winter_fuel_inventory.apply_winter_fuelsec_mustrun`, rule-17
   window/driver/forward statement, rule-19 replacement of the disabled tmin
   limbs) and solved full-span together with Component A and the gas cold-snap
   derate, against a zero-mechanism ablation twin. Result: decisively DORMANT
   (C3c 0h >$300 in both arms vs 5/5/12 actual DA; C5b 2025 0.697→0.715 TWh vs
   2.08; oil burn ~unchanged; budget never approached). The "one missing winter
   mechanism" hypothesis is REFUTED; the stack was adopted anyway per rule 1,
   and the residual is re-attributed to a NEISO **winter
   capacity-adequacy/scarcity-price-formation** gap — carried as exactly the
   two ledgered caveats (C3c, C5b) inside budget. Nothing further is closable
   by winter-fuel mechanism work on these backcast years.
2. **C7 ST_GAS residual (G-16) — closed immaterial-gated.** Under the rubric
   v2.1 owner amendment (2026-07-06, 2%-of-ISO-load materiality floor), NEISO
   ST_GAS (0.1–0.3% of load; CT_PEAKER 0.5–0.7%) is below the D-1 gate: C7 is
   SKIPPED, reported-not-gated. The L-49 confirmation re-solve verified the
   committed metrics read SKIPPED and quantified the residual shape numbers
   that remain in the diagnostics (profile_r 0.519/0.729/0.853 for 2023/24/25).
   The class is 0.06–0.23 TWh in a ~120 TWh ISO — structural work on its
   diurnal shape is explicitly not worth gating on (rule 20 v2.1 rationale).

## 4. What declaring the marker authorizes (and what it does not)

Writing `"NEISO": {"declared": "2026-07-07", "keeper":
"2026-07-07-neiso53-winter-fuelsec-coldsnap", "by": "<owner/session>"}` into
`frontend/data/backcast/calibration-complete.json` authorizes, per rule 22:

- **NEISO 2022 + H1-2026 data intake** (owner-authorized, session-logged,
  no-LP validation only until the marker commit is pushed): EIA-930 ISNE
  fuel-mix + demand 2022; CAMPD unit-level 2022 for the six New England states
  (fleet bins + bench + outage-window derivation); delivered gas + the daily
  hub-basis series the keeper levers (`--gas-hub-basis-daily`); EIA-930 monthly
  hydro 2022 (`--hydro-eia930-monthly`); NEISO hub/zonal DA+RT LMP 2022 (C3
  bench); eGRID2022 (C5a); F923 2022 coal plant-month pricing + per-plant CO2
  rate overlays; zone daily TMIN/TMAX 2022 coverage check (reliability floor +
  winter mechanisms read `iso_zone_tmax`); scoring-path registration
  (`CALIBRATION_YEARS_BY_ISO["NEISO"] += 2022`, `bench/NEISO/2022.json.gz`,
  actual-tail part). Per the G-19 owner decision (option B) this intake happens
  now, at declaration time.
- **The one-shot 2022 solve** of the FROZEN keeper recipe via
  `scripts/run_calibration_full.py --iso NEISO --year 2022
  --holdout-authorized` + the frozen flags (`enforce_holdout_year_gate`
  requires the pushed marker), years sequential, **scored exactly once**,
  registered on the dashboard clearly labeled as the one-shot holdout score
  (rule 15), recorded in `docs/out-of-sample-results-2026-07.md` §2 **whatever
  the result is**.
- **The H1-2026 half is NOT executable now** — publication-blocked per G-19
  (CAMPD Q2-2026 unposted; delivered gas May-2026+; F3 demand-profile full-8760
  contract; F4 reference-year registration). It executes later under this same
  marker, exactly once, when the data publishes. Only the 2022 half runs today.

Two execution safeguards this session will apply (both in-sample, neither
touches a holdout):

- **Recipe reproduction at HEAD requires the legacy-P2 unlock.** The keeper
  lineage's `--commitment` pass predates the P2 archival (`5b86685`,
  2026-07-07 — one day after the keeper's solve commit); at HEAD the frozen
  recipe is invoked as `--enable-legacy-p2 --commitment …` (the archival kept
  `pipeline.commitment.run_commitment_pass` intact for exactly this). This is
  frozen-recipe reproduction, not a new calibration choice. (CLAUDE.md's "no
  keeper uses it" note is inexact for NEISO's grandfathered recipe; flagged for
  the next doc sync.)
- **In-sample parity precheck before burning the shot.** Main has moved since
  `7f968f3`, and this repo's own history (L-49 drift, G-11, G-12) shows silent
  HEAD drift is real. Before the 2022 solve, the frozen recipe is re-solved on
  2023–2025 at HEAD (unquarantined, throwaway bundle) and compared to the
  committed keeper bundle. Parity → run 2022. Drift → STOP and report; the
  marker stands but the one-shot is not spent against a config that no longer
  reproduces the keeper.

## 5. Irreversibility (rule 22, verbatim terms)

The one-shot result is recorded **whatever it is**, in-sample skill claims gain
out-of-sample evidence or they don't, and **no calibration change may respond
to the result** without designating a new never-touched holdout. There is no
re-tune, no second solve, no "diagnostic" follow-up on 2022 under any
circumstances. 2022 stops being a holdout the moment it is scored; it never
becomes a tuning year. In-sample improvement with held-out degradation is
overfitting, not skill, and will be recorded as such.

## 6. Decision record

- **2026-07-06:** owner HELD (winter-fuel Component-B / C7 ST_GAS re-exam) —
  gap-register addendum + 2026-07-06 calibration-log entry.
- **2026-07-07:** both hold reasons resolved (§3); preconditions re-verified at
  HEAD (§2); decision put to the owner by this session.
- **Owner decision (2026-07-07): DECLARED — "Declare + run one-shot".** The
  owner selected the full path: write+push the marker, intake NEISO 2022 data,
  run the in-sample parity precheck, then solve 2022 once, score once, and
  register the result labeled as the one-shot holdout score, recorded whatever
  it is. Session-logged via `AskUserQuestion` in the
  `neiso-calibration-complete-w1c` session; this memo's §4–§5 terms are in
  force. The H1-2026 half remains publication-blocked and executes later under
  this same marker, exactly once.
- **Owner decision (2026-07-07, later same day): one-shot EXECUTION HELD —
  data-equivalency gate.** After the intake landed, the owner held one-shot
  execution for every ISO: no holdout solve or score may run, and no holdout
  result may be recorded, until a **cross-ISO holdout data-equivalency gap
  register** exists — a series-by-series audit that each holdout year's input
  coverage (drivers, fleet/overlays, bench actuals, and their
  granularity/vintage) matches the keeper years'. The known NEISO
  asymmetries motivating the gate are recorded in the out-of-sample doc §1.2
  (weekly-anchored daily-AGT density; outage-detector vintage). The NEISO
  2022 intake stands; the declaration and the marker stand; §4's execution
  plan and §5's irreversibility terms apply whenever the gate is cleared and
  execution is re-authorized. Tracked in G-19.
