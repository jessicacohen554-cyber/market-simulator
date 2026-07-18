# Scalar remediation — prompt pack (2026-07)

Companion to `docs/handoffs/scalar-remediation-plan-2026-07.md`. Each batch is one session prompt.
Batches map to the plan's waves (§5). **Standing rules pasted into every session are at the
bottom — every prompt inherits them.**

**Model assignment key.** `opus` = Claude Opus 4.8 (judgment-heavy: structural replacements,
red-flag adjudication, ledger/root-cause reasoning). `sonnet` = Claude Sonnet 5 (mechanical
re-derivation from a named source, CI wiring, config lifts, verification sweeps). Assignment is a
default, not a constraint.

**Parallelism.** Waves run in order (W0/W1 concurrent). Within a wave, batches on **different
ISOs** run concurrently as separate sessions; batches touching the **same keeper config** or the
**same shared module** (`offer_curves.py`, `constants.py`, `calibration_verdict.py`) serialize to
avoid merge churn. Solve concurrency obeys CLAUDE.md rule 12 (cap 2 for per-plant multi-zone ISOs;
years sequential within an invocation).

---

## Wave 0 / Wave 1 (start together)

### B-GOV-1 — closure verification + ledger sweep  ·  model: `sonnet`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §0, §2.2 (C-2/C-4/C-5/C-8/C-11), §5 W0.
This session VERIFIES and DOCUMENTS closed items and completes the DOF ledger — it changes no
dispatch-affecting value.

1. Confirm C-2 closed: COAL_MAX_CF_BY_PLANT lives in constants.py, is derived by
   scripts/data/derive_coal_max_cf.py, and the (6179,2025) override is gone. Grep to prove it.
2. Confirm C-11 closed: run `python scripts/legitimacy_diagnostics.py --keepers` and attach the
   D-9 output. It must show non-ERCOT keepers resolve NO ERCOT-fitted band via the generic
   fallback. If any keeper fails D-9, STOP and file it as the top C-13/B-NYI-1 input — do not fix
   here.
3. Sweep src/market_sim/data/offer_curves.py for any inline numeric fallback literal in the offer
   path (rule 24). List each; lift into ScenarioConfig/constants only if it is a *neutral* default
   (1.0-band / structural share) — flag any that isn't as a finding, do not neutralize here.
4. Run `python scripts/build_dof_ledger.py` for all six keepers. Every band/sigmoid/adder scalar
   in each run_config gets a free_parameters row. For C-1 sigmoids add the D-8 §2C identification
   note (floor↔2024, gas_mid/ceil↔2025). For C-4 merchant=35.0, C-8 offer steps, and any
   committed-tranche multiplier < 0.85: source="residual", and each MUST carry an open root-cause
   issue reference (create the issues; audit_keepers E8 enforces it).
5. Delete rule-26 stale prose: the ordc_reliability_deployment_mw narrative at
   src/market_sim/results/scarcity.py:635 and any surviving retired-PS-adder text
   (scenarios.py ~2225). Deleted means deleted — remove, don't comment out.
6. Run scripts/audit_keepers.py; it must pass E8. Commit code+docs (git push ok, source-only).
```

### B-DIAG-1 — D-3 ablation twin + D-10 free-class rescore  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §4.1, §4.2 and audit §7 D-3/D-10. Build two
diagnostics; wire both into the promotion path. No keeper values change.

D-3 zero-forcing ablation twin:
 - Add ScenarioConfig.as_zero_forcing_ablation(cfg): returns a copy with every MERCHANT floor/
   bridge OFF (reliability_floor, ct/gas_st_netload_drag, caiso_ra_mustoffer+bridge+decommit,
   temperature-CF limbs, nyiso_local_selfsupply, wefor haircuts→neutral), KEEPING nuclear must-run,
   CHP steam-following, coal take-or-pay. Derive the off-list from the D-2 mechanism registry in
   legitimacy_diagnostics.py so a new floor is ablated by default — do NOT hand-maintain a tuple.
 - run_calibration_full.py: --zero-forcing-ablation solves into <out-dir>-ablation, full year span,
   records "ablation_of" in run_config.json.
 - calibration-report skill: add a step (between register and commit) requiring a keeper to have a
   registered ablation twin (registry/<id>-ablation.json, linked via the keeper sidecar
   "ablation_twin"). Run page shows keeper-vs-ablation per-class delta + a "market_story" field.
 - audit_keepers.py E9: keeper without a registered ablation twin FAILS (mirror E8).

D-10 free-class rescore:
 - calibration_verdict.py: add free_class_score recomputing C1 excluding pinned classes per a
   declared per-ISO registry (wind/solar under L1, nuclear L3, hydro L6, CHP L4, NYISO imports L2 —
   from audit §4). Publish "C1 all X/Y · free X'/Y'" on the Status page. No gate yet.

Trivial-case fixtures per the repo pattern (1 gen/1 zone/24h). Do NOT solve keepers here — the
twins get solved when their keepers are next re-registered (W2+). Tests + code; git push ok.
```

### B-DIAG-2 — D-11 knob Jacobian + D-13 bench-repro + D-14 negative control  ·  model: `sonnet`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §4.3/§4.4/§4.5. Build three diagnostics.

D-11 scripts/knob_jacobian.py: for a keeper, read free_parameters from the DOF ledger, perturb
each ±10%, reuse derive_offer_curve_jacobian.py's solve+score machinery, emit
<bundle>/knob_jacobian.json (ranked |∂headline/∂knob| for C2/C3b/C4 + class TWh). One year (2024)
only, labelled diagnostic. Render as a bar list on the run page. Advisory only.

D-13 .github/workflows/bench-repro.yml (manual + weekly): per ISO rebuild bench/ twice from
committed code + data/raw, assert byte-identity across both builds and the committed files. Plus
tests/test_bench_no_circularity.py: AST-walk asserting no bench-builder module imports results/
dispatch outputs or reads results/calibration/** (the L11 BTM pattern).

D-14 scripts/negative_control.py --iso --control {gas_price,outage_shuffle}: clone keeper config,
corrupt one physical input (gas ×1.5 / outages permuted within-year), solve one year, assert the
verdict WORSENS beyond a floor delta on C2/C3b. Insensitivity ⇒ compensating knob; report the
(input, knob) pair by diffing D-11 rankings. Labelled probes, never keepers.

Tests with trivial fixtures. Do not run the full per-ISO batches here (that's a release cadence
task) — land the harness + one smoke run. git push ok.
```

---

## Wave 2 — neutralizations needing no new data (run after W1 lands)

### B-NYI-1 — NYISO de-leak (C-13) + LI floor re-ground (C-17)  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-13, C-17), §2.3. NYISO keeper is
2026-07-03-nyiso-41-hub-prices (results/calibration/nyiso41_hubprices). Two changes, one branch.

1. C-13 de-leak (rule 25): the config carries offer_curve_by_group/CT_PEAKER/peak = 13.15 and
   CC_REGULAR/econ_high = 1.21 — both ERCOT-inherited/residual-identified. Neutralize:
   CT peak → the NEISO-42 precedent cap (4.0) or a NYISO-derived value; econ_high 1.21 → 1.0.
   The 1.21 was retained because removing it cratered C3a −24% — that C3a hole is now an OPEN
   ROOT-CAUSE ITEM (file it: likely NYISO scarcity/reserve pricing, not a CC markup). Do NOT
   re-tune it back.
2. C-17: re-ground constants.py Long_Island 0.45 on the published NYISO Zone-K LCR/LMIC
   requirement %, not the realized 2023 share. This needs the NYISO ICAP LCR table — intake it
   first via the data-intake skill (schema-first, per-ISO registry); that intake commit is the
   rule-23 source-data change the re-derive commit cites.
Re-solve NYISO 2023 2024 2025 in one invocation with the keeper flags, register as a probe
(calibration-report, full 3-year bundle), solve+register its D-3 ablation twin alongside. Expect
C3a/price regressions — record them in the commit and the root-cause log, do NOT chase.
```

### B-LIMB-1 — R1 sign-flip temperature-CF limbs  ·  model: `opus`

```
Read docs/out-of-sample-results-2026-07.md §2B and docs/handoffs/scalar-remediation-plan-2026-07.md
§2.3. Three limbs are UNIDENTIFIED (Spearman ρ sign-flip out-of-training) and must ship DISABLED
(decision rule R1 — an unidentified floor is scaffolding fitted to noise, rule 17):
 - PJM ComEd / CC_REGULAR (ρ +0.35 → −0.19)
 - CAISO SP15 / ST_GAS (ρ +0.41 → −0.16)
 - CAISO SP15 / CC_REGULAR (ρ +0.69 → −0.10)
Disable exactly these three limbs in the reliability-floor coefficient CSVs (do not touch the
non-sign-flip limbs — those are R6-keep with drift caveats in the ledger). Re-solve PJM and CAISO
(2023 2024 2025 each, separate concurrent invocations, keeper flags), leave-one-year-out score
within 2023–2025 before any promotion recommendation, register both as probes + ablation twins.
This is a mechanism change judged on structure, never the residual — regressions are expected and
logged. Two different keepers (pjm-76, caiso-51): separate branches if solving concurrently.
```

### B-XISO-2ch — off-registry channel deletion (C-7)  ·  model: `sonnet`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-7). transmission.py:2334-2335 reads
os.environ INTERCHANGE_SHAPE_IMPORT_PCT / INTERCHANGE_SHAPE_EXPORT_PCT — an off-registry tuning
channel (rule 24). Delete the env-var reads; promote the two percentiles to ScenarioConfig fields
(so they appear in run_config.json) with the current 30/10 as defaults. Separately: re-ground the
30/10 on a net-load duck-belly percentile definition (percentile of the net-load distribution from
930 data, ISO-generic) and demote the negative-price-prevalence "~100% precision" claim to a
diagnostic comment, not the anchor. A/B one CAISO year to confirm the config path reproduces the
env-var path bit-for-bit at 30/10; then the re-grounded percentiles are a separate probe. Register
the CAISO probe + ablation twin. Source-only push ok for the channel deletion.
```

---

## Wave 3 — intakes then re-derivations (each gated on its own intake commit)

### B-CAI-1 — CAISO scalars: PGE-TAC (C-16), export cap (C-14), sigmoid n/a, C-5 fallback cite  ·  model: `sonnet`→`opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-14, C-16, C-5). CAISO keeper is
caiso-51-firm-base. Per item, INTAKE THE SOURCE FIRST (that commit is the rule-23 trigger), then
re-derive:
 1. C-16 PGE-TAC 0.86/0.14 (iso_configs.py): re-derive the NP15/ZP26 split from published
    planning-area load (FERC-714 hourly planning-area, or CEC forecast forms). data-intake skill
    for the load table; then derive + freeze + cite.
 2. C-14 CAISO_BIDIR_EXPORT_CAP_MW 3500 (transmission.py:319): caiso-51's per-hub signed corridors
    with measured p95 envelopes are the successor. Retire the static scalar from the default path;
    if a fallback must remain, re-derive from the OASIS export-direction ATC envelope (fetch
    workflow exists) and label fallback-only + ledger row.
 3. C-5: the 7,500 literal survives as the non-deliverability fallback only — add the
    caiso-c5-wecc-cap-closeout-2026-07-03.md citation + a ledger row so it can't silently re-become
    binding. No solve for this sub-item.
Where dispatch-affecting (C-16, C-14), one probe solve + ablation twin, full 3-year, dashboard.
Regressions logged not chased.
```

### B-ERC-1 — ERCOT scalars: sigmoid anchors (C-1), coal price (C-9), CC peaking (C-12), wefor root-cause (C-15)  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-1, C-9, C-12, C-15) and §2.1. ERCOT
keeper is ercot-32. Sanctioned offer-curve scope (rule #1) — do NOT scrub the sigmoids/bands; the
work is documentation, status checks, and one root-cause replacement:
 1. C-1: anchor COAL_SIGMOID_DEFAULTS asymptotes to citable coal economics (take-or-pay/minemouth
    literature) as plausibility documentation + ledger rows recording the D-8 §2C single-year
    identification. NO REFIT (a refit today is residual-driven; the trigger is the next F923 gas
    regime).
 2. C-9 _PRB_PRICE_CALIBRATION: the symbol no longer greps in fuel.py — first establish whether it
    was renamed/superseded by the F923 delivered-fuel path. If any calibrated coal trajectory
    survives, re-derive from F923 Schedule-5 delivered coal receipts (on disk) + EIA Coal Markets;
    the F923-coal curation commit is the citable change.
 3. C-12: locate the CC peaking-tranche 15%×4-plant override (moved from fleet.py:4208). If it
    survives, per-plant ledger rows + root-cause issue; if the F-class over-run is fixed
    structurally, neutralize to the class default.
 4. C-15 (root cause): wefor_residual 0.06 / wefor_multiplier 0.7 neutralize to no-op (R4); the
    coal shoulder-month residual the 0.7 haircut targeted becomes a root-cause investigation into
    seasonal maintenance — re-derive thermal seasonal availability from CAMPD outage-window
    seasonality (on disk, forward-reproducible) instead of a global wind haircut. Probe + twin.
Deltas logged. ercot-32 branch.
```

### B-ERC-2 — ERCOT AS: endogenize revenue (C-3) + document requirement coefs (C-10)  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-3, C-10). Two ERCOT AS items:
 1. C-10 (document, don't change): the AS-requirement regression coefficients (reserve_config.py)
    fit the PUBLISHED requirement MW (rule-14 admissible). Commit the derive script/notebook with
    its inputs (ERCOT methodology + ASPLANNP433/requirement series), add parameter-citations.md
    rows, ledger rows source="measured-market-design", freeze (rule 23).
 2. C-3 (structural replacement, R3): the exogenous AS revenue table + saturation curve
    (constants.py 169/22/15/8 $/kW-yr, REF_GW 4.0, EXPONENT 2.5) is fitted to the observed 2023→25
    AS crash and drives forecast retirement/entry/storage. Replace with AS revenue derived from the
    model's OWN reserve co-optimization duals (MISO-39 reserve_pergen / ERCOT AS-aware machinery),
    using published ERCOT DAM AS clearing prices as the VALIDATION series, not the fit target.
    Intake the clearing prices first (data-intake). Score leave-one-year-out before recommending
    promotion; this changes capacity evolution so a multi-year forecast smoke-check is part of
    acceptance. Until built, leave C-3 as R6 ledger rows + the open issue. Deltas logged.
```

### B-PJM-1 — PJM scalars: sigmoid anchors (C-1), wefor (C-15), seam ladders (C-6)  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-1, C-6, C-15). PJM keeper is
pjm-76-outage-fix. Same shape as B-ERC-1 for the PJM sigmoids (C-1: document + ledger, no refit)
and wefor (C-15: neutralize 0.015 residual, root-cause the shoulder residual to maintenance
seasonality). Plus C-6 for PJM: re-derive the IMPORT/EXPORT seam ladders from measured neighbor-hub
prices + ATC (fetch-neighbor-lmp.yml exists; the CAISO caiso-51 measured-hub approach is the
template) — intake first, then derive. One probe + ablation twin, full 3-year. Coordinate with
B-LIMB-1 if both touch pjm-76 concurrently (serialize the config edits). Deltas logged.
```

### B-XISO-1 — gas availability factors (C-18), all ISOs  ·  model: `sonnet`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-18). GAS_AVAILABILITY_FACTOR
(constants.py:421) carries 0.85–0.89 with a "was 0.83"/"TODO: verify" nudge trail under a NERC GADS
label. Verify each against the published NERC GADS / State-of-Reliability EFORd tables for the
fleet; set to the published value EVEN IF the backcast worsens (rule 14 — a worse fit is a
discovered miscalibration elsewhere, logged as a root-cause item, never buried back in the input).
Ledger rows with the table citation, remove the TODOs. Small intake (published GADS tables). This
touches every ISO's MC — run one probe per affected ISO only if the change is material (>0.5%);
otherwise document the value change with the D-8-style note. Deltas logged.
```

### B-XISO-2 — seam ladders for remaining ISOs (C-6): NYISO, NEISO, MISO  ·  model: `opus`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §2.2 (C-6). Migrate the fitted
IMPORT_TRANCHES/EXPORT_TRANCHES + atc_base_fraction + ATC_SOLAR_K (interchange_config.py) for
NYISO/NEISO/MISO to measured neighbor-hub-price + ATC paths (CAISO caiso-51 is the template; PJM is
B-PJM-1). NYISO's PER-YEAR scarcity rungs (68.4/79.7/135.2) are outcome-tracking — neutralize the
year-keying (R4). Intake each ISO's neighbor-LMP/OASIS series first (that commit is the rule-23
trigger); the self-referential CAISO static-ladder fallback is deleted (R5) once measured is
default. Per-ISO probe + ablation twin, full 3-year, separate concurrent invocations (cap 2 for
per-plant multi-zone). NYISO here pairs with B-NYI-1's C3a root-cause. Deltas logged.
```

---

## Wave 5 — program close

### B-GOV-2 — ledger completion, keeper re-gate, docs  ·  model: `sonnet`

```
Read docs/handoffs/scalar-remediation-plan-2026-07.md §5 W5. Final governance pass:
 1. build_dof_ledger.py: 100% coverage across all (possibly re-promoted) keepers; every R6-keep
    scalar has an open root-cause issue reference (audit_keepers E8 green).
 2. Re-gate all six keepers with D-10 free-class + D-11 published in each bundle; record the new
    verdicts on the Calibration Status page (they may worsen — truthful attestation is the point).
    Run calibration-keeper-auditor after any keepers.json edit.
 3. parameter-citations.md: add the COAL_SIGMOID_DEFAULTS rows (make the largest fitted table
    visible), drop stale retired-knob rows.
 4. Confirm no rule-26 re-armable knobs parse (ordc offset gone, no zeroed deprecated params).
 5. /sync-docs. Commit; dashboard payloads via mcp__github__push_files (git push 413s on large
    packs — CLAUDE.md Git section), source-only via git push.
```

---

## Standing rules (paste into every session)

- **Repo:** `jessicacohen554-cyber/market-simulator`. ENV:
  `uv venv && source .venv/bin/activate && uv pip install -e ".[dev]"`.
- **Read first:** `docs/handoffs/scalar-remediation-plan-2026-07.md` (the decision rule §1 governs
  every disposition), `docs/model-legitimacy-audit-2026-07.md`, `CLAUDE.md` (rules 1, 11, 13,
  15/16, 19–26).
- **Prime directive:** structural fidelity over backcast fit (rule #1). If a scrub/re-derivation
  makes the fit worse, that is a *discovered miscalibration elsewhere* — log an open root-cause
  item; never re-add a floor, adder, haircut, or fitted value to win the residual back.
- **Rule 23 is load-bearing here:** every re-derivation commit must cite a **source-data change**
  (a new intake, corrected extract, or newly published vintage) — never a residual. If the source
  isn't on disk, the `data-intake` session precedes the derive session, and its commit is the
  citable change.
- **Rule 14:** prefer accurate/measured data over estimates even when it worsens the fit; prefer a
  *reconciled* version of real data (document the boundary misalignment) over a clean guess.
- **Holdout quarantine (rule 22):** no solve/score/intake touches 2022 or H1-2026 for any ISO
  without a `calibration-complete.json` marker. All probes are 2023–2025, full-span single-
  invocation bundles (rule 16), years sequential within an invocation.
- **Dashboard discipline (rule 15):** every completed run (keeper or probe) is registered
  (`calibration-report`) and committed in-session, with its D-3 ablation twin (once B-DIAG-1
  lands). Lead with the dashboard result; keep prose minimal.
- **Solve concurrency (rule 12):** separate invocations may run concurrently, cap ~2 for per-plant
  multi-zone ISOs; years within an invocation are always sequential.
- **Push discipline:** rebase onto latest `origin/main`; dashboard payloads via
  `mcp__github__push_files`; source-only commits may use `git push`.
- **This program retunes nothing to a residual.** Deltas are recorded in commit messages and the
  root-cause log, never chased.
```
