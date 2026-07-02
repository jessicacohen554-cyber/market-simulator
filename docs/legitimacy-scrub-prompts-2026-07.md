# Legitimacy scrub — prompt pack (2026-07)

Companion to `docs/model-legitimacy-audit-2026-07.md`. Five sessions. **S1 first** (it builds the
tests that score everything else), then S2/S3/S4 in parallel on separate branches, S5 last.

Sequencing rationale: without S1's diagnostics, every scrub session would be judged by the same
annual-volume rubric that rewarded the forcing in the first place — the scrub would look like a
regression and calibration pressure would rebuild the floors. Land the measuring stick first.

Shared context to paste into each session is at the bottom.

---

## S1 — Legitimacy diagnostics + CI quarantine (blocking; do this first)

```
Read docs/model-legitimacy-audit-2026-07.md (§7 diagnostic suite) and CLAUDE.md. Build
scripts/legitimacy_diagnostics.py with the following diagnostics, each runnable against a
calibration bundle dir (dispatch/<year>_P2.parquet) plus frontend/data/backcast/bench/<ISO>/:

1. D-1 diurnal shape test: per plant-class, hour-of-day mean profile model vs CAMPD; report
   profile correlation and the model/actual CV ratio over off-peak hours (h0-14 local). Fail a
   peaker/intermediate class when r < 0.8 or model CV < 0.5x actual CV.
2. D-2 forced-energy attribution: tag every min_gen injector (reliability_floor, ct/st netload
   drag, RA must-offer/bridge, CHP steam, coal must-run, nuclear) with a mechanism label on the
   rows it floors — thread a parallel int8 array through FleetArrays (mechanism id per unit-hour,
   maximum-compose keeps the binding mechanism) — and report TWh dispatched AT the binding floor
   by class x mechanism. Gates: forced share < 10% for CT_PEAKER-type classes, < 30% for any
   merchant class (nuclear/CHP/coal-ToP exempt).
3. D-4 off-window binding: for each driver-gated floor, % of floored MWh outside its justified
   hour window; fail > 5%.
4. D-5 forecast/backcast parity: instantiate the mechanism set for the same ScenarioConfig in
   mode="backcast" vs mode="forecast" and diff; every difference must be on the declared
   backcast-overlay list (build the list from docs/backcast-measured-data-audit-2026-06.md).
5. D-9 overlay quarantine: assert every keeper bundle run_config.json has
   ct_deployment_overlay=False, reliability_deployment_overlay=False, ct_mustrun_per_plant=False,
   ordc_reliability_deployment_mw=0, caiso_gas_commitment_floor=False; and assert non-ERCOT ISOs
   resolve no offer band from the ERCOT-fitted generic fallback (offer_curves.py:136-143,535-550)
   — neutral 1.0 bands only.

Wire 1-5 into a pytest module (tests/test_legitimacy_diagnostics.py) with trivial-case fixtures
(1 gen / 1 zone / 24h per the repo testing pattern), plus a CI-friendly entry point
`python scripts/legitimacy_diagnostics.py --bundle <dir> --iso <ISO>` that exits nonzero on gate
failure. Run it against the current CAISO keeper bundle (results/calibration/caiso42_atc_hydro)
and confirm it FAILS D-1/D-2/D-4 for CT_PEAKER (that is the expected result — the audit doc §1
documents the flat-floor signature it must catch). Do not fix the floors in this session; the
failing report is the deliverable. Commit code + tests + the keeper diagnostic report.
```

## S2 — CAISO CT floor scrub (the owner's complaint)

```
Read docs/model-legitimacy-audit-2026-07.md §1-§2 and CLAUDE.md. Three coupled fixes, one branch:

1. Reliability-floor hour window: add start_hour/end_hour to the CAISO CT_PEAKER and CT_CHP
   netload limbs in data/raw/reference/reliability_floor_coeffs_CAISO.csv, windowed to the
   evening ramp (HE15-22, matching ct_drag_ramp_start/end and the empirical finding in
   docs/caiso-ct-netload-drag-2026-06.md that overnight CT CF ~ 0 even at high net load). The
   engine (model/transmission.py:2905-2909) already supports the window — this is data-only.
   THEN decide overlap: with ct_netload_drag=True already covering h15-22 with a net-load-
   proportional floor, the windowed registry limbs are likely redundant (rule: one mechanism per
   phenomenon) — A/B a 2024 probe with limbs windowed vs limbs disabled and keep the single
   mechanism that survives D-2 attribution with the cleaner story. Document the choice.
2. Bridge eligibility by physics: in model/commitment.py replace the hard-coded
   ("CC_REGULAR", "CT_PEAKER") eligibility tuple (L775) with a min_down_hours >= 4 gate read from
   the unit commitment params, so fast-start CTs are never economically bridged. Keep the
   physical gap<min-down bridge unchanged (it never fires for CTs anyway).
3. Verify with S1 diagnostics: re-solve CAISO 2023 2024 2025 in one invocation
   (python scripts/run_calibration_full.py --iso CAISO --year 2023 2024 2025 <keeper flags from
   results/calibration/caiso42_atc_hydro/run_config.json> --out-dir results/calibration/
   caiso49_ct_scrub) and run scripts/legitimacy_diagnostics.py on it. Success = D-1/D-2/D-4 pass
   for CT_PEAKER (profile r >= 0.8, off-peak CV ratio >= 0.5, forced share < 10%). C1 CT annual
   volume will likely get WORSE - that is expected and acceptable (rule #1: never judge a
   structural fix by the residual). If the evening peak is now badly under-dispatched, the root
   cause is the P1 merit order (import tranche prices / CC offers - the caiso-48 next-levers
   thread), NOT a reason to re-add a floor.
Register the run on the dashboard as a probe (calibration-report skill), full 3-year bundle,
commit+push in-session per CLAUDE.md #15/#16.
```

## S3 — Fitted-scalar remediation (C-list)

```
Read docs/model-legitimacy-audit-2026-07.md §3 (class C table). Work the list in this order; for
each item either (a) replace with a measured/published value (rule #14), (b) re-derive from
independent data with a citation and freeze, or (c) explicitly quarantine as a default-off probe:

1. C-5 CAISO 7,500 MW WECC simultaneous import cap (iso_configs.py:321): resume the caiso-46
   reconciled-seam-limit thread — derive the cap from published MIC/path ratings reconciled to
   the model's collapsed-link topology (rule #14 misalignment clause), not from the EIA-930 tail.
2. C-2 COAL_MAX_CF_BY_PLANT (fleet.py:505-521): delete the (6179,2025) per-year override
   outright (no forward analogue). Re-derive per-plant ceilings from CAMPD outage-adjusted
   availability (physics) rather than observed output; move the dict into constants.py with
   derivation citations.
3. C-4 CHP_BTM_PCT_BY_SECTOR (fleet.py:4103): re-derive from EIA-923 Schedule-8 CHP
   sector data (independent source), not the run-61-65 residual; document.
4. C-7 CAISO solar-shape band (transmission.py:1857): remove the env-var override channel
   entirely (audit rule 23); re-ground the 30/10 percentile band on net-load physics (duck-belly
   definition) with the negative-price validation demoted to a diagnostic, not the anchor.
5. C-11/C-13 cross-ISO band leakage: give MISO/NEISO/NYISO neutral (1.0) generic bands or
   ISO-derived values; kill the ERCOT-fitted fallback inheritance and the 13.15x CT peak tail
   inheritance (NEISO-42's 4.0 cap is the precedent). Expect fit regressions; record them as
   open root-cause items per rule #1, do not re-tune in this session.
6. C-9/C-14/C-16/C-17/C-18: move remaining hardcoded per-plant/per-ISO dicts into constants.py
   with source lines; where the value is honestly residual-identified, mark it
   "residual-identified, forecast-risk" in the comment and add it to the DOF ledger (S5).
Each item: separate commit, before/after 1-year probe solve only where dispatch-affecting, tests
where logic changed. Do NOT chase the residuals these changes move; log deltas in the commit.
```

## S4 — Out-of-sample program (measure the overfit)

```
Read docs/model-legitimacy-audit-2026-07.md §5.3 and docs/forecast-validation-plan.md. Execute,
per ISO, in this order (cheapest first):

1. D-7 statistical-mode A/B: run --statistical-mode against all six CURRENT keeper configs
   (the only prior run was ERCOT, 2026-06-16, against a superseded keeper). Publish the
   overlay-vs-statistical fail-count gap per ISO on the dashboard next to each keeper.
2. D-6 holdout scoring: score the designated untrained holdouts — 2022 and H1-2026 — with FROZEN
   keeper configs, one solve each, no re-touch afterward. Requires wiring 2022/2026 demand,
   fuel, and bench data through the existing loaders; where a year's source data is missing,
   intake it via the data-intake skill first (schema-first, per-ISO registry).
3. D-8 coefficient stability: refit the net-load drag hinges and temperature-CF floor
   coefficients on 2023-24 CAMPD only; predict 2025; report drift. Same for the coal sigmoid
   parameters (leave-2024-out, the only cheap-gas year).
Deliverable: docs/out-of-sample-results-2026-07.md with a per-ISO table (in-sample fails vs
statistical-mode fails vs holdout fails) and a one-paragraph per-ISO verdict on forecast-skill
evidence. Run the six statistical-mode solves as concurrent background jobs (separate
invocations, rule #12 concurrency; cap 2 for per-plant multi-zone ISOs); years within an
invocation sequential as always. These results go on the dashboard, not just in chat.
```

## S5 — Governance: rules, rubric, ledger (last)

```
Read docs/model-legitimacy-audit-2026-07.md §7-§8. Three changes:

1. CLAUDE.md: add rules 16-25 from audit §8 verbatim (floor window/driver/forward-story, physics-
   gated eligibility, one-mechanism-per-phenomenon, forced-energy budget, DOF ledger + ablation
   twin, holdout scoring, frozen derive scripts, no off-registry tuning channels, no cross-ISO
   curve leakage, deleted-means-deleted).
2. Rubric: extend scripts/calibration_verdict.py + docs/calibration-determination-rubric.md with
   the D-1 shape criterion and the D-2 forced-energy share as first-class C-criteria (C7 shape,
   C8 forced-share), so a flat floor can never improve a keeper's score. Re-gate the current
   keepers with the extended rubric and record the new verdicts on the dashboard (they will get
   worse; that is the point - truthful attestation).
3. DOF ledger: extend the keeper attestation (calibration_attestation.json) with a
   free_parameters section: every tuned scalar in the run config, its identification source
   (published | measured-physical | residual), and the lineage solve count; have
   scripts/audit_keepers.py fail any keeper with a residual-sourced parameter lacking an open
   root-cause issue reference. Delete (not deprecate) ordc_reliability_deployment_mw and the
   retired-knob stale docs (scenarios.py:2225-2237 PS adder text; parameter-citations.md stale
   rows). Then run /sync-docs.
```

---

## Shared context (paste into each session)

- **Repo:** `jessicacohen554-cyber/market-simulator`. ENV: `uv venv && source .venv/bin/activate
  && uv pip install -e ".[dev]"`.
- **Read first:** `docs/model-legitimacy-audit-2026-07.md` (the audit this pack implements),
  `CLAUDE.md` (non-negotiables — esp. #1 structure-before-fit, #13 measured-outcome ban,
  #15/#16 dashboard discipline).
- **Prime directive for every session:** structural fidelity over backcast fit. If a scrub makes
  the fit worse, that is a *discovered miscalibration elsewhere* — log it as an open root-cause
  item; never re-add a floor, adder, or haircut to win the residual back.
- **Owner's accepted scope (do not scrub):** coal sigmoids and offer-curve tranche customization;
  mine-mouth/take-or-pay coal must-run economics; temperature/net-load-tied reliability
  commitment for CT/steam classes **when windowed to the driver's hours**; measured physical
  inputs (outages, delivered fuel, CEMS rates, published limits).
- **Owner's rejected scope (scrub on sight):** floors sized from the class's observed output;
  floors binding in hours the driver evidence says the class is offline (CT overnight); midday
  forcing to fit an asset class; measured-outcome pins of any kind in keepers.
- **Solve discipline:** all backcast years in one invocation (`--year 2023 2024 2025`), years
  sequential within it; separate invocations may run concurrently (cap ~2 for per-plant
  multi-zone). Every completed run (keeper or probe) goes on the dashboard in-session.
- **Push discipline:** rebase onto latest `origin/main`; dashboard payload commits via
  `mcp__github__push_files` (git push 413s on large packs); source-only commits may use git push.
