# Scalar remediation program — the ~230 residual-identified scalars (2026-07)

**Date:** 2026-07-04 · **Inputs:** `docs/model-legitimacy-audit-2026-07.md` §3 (C-1…C-18), §5.1
(census), §7 (D-3, D-10…D-14), `docs/legitimacy-scrub-prompts-2026-07.md` S3,
`docs/out-of-sample-results-2026-07.md` §2 (D-8), CLAUDE.md rules 19–26.
**Companion prompt pack:** `docs/handoffs/scalar-remediation-prompts-2026-07.md`.
**This session changed no model value.** This document assigns *dispositions*; every execution
session is in the prompt pack.

Numbering note: CLAUDE.md rule N = audit §8 rule N−1 (CLAUDE.md gained rule 16 after the audit).
"Rule N" below means the CLAUDE.md number.

---

## 0. Status snapshot — what is already done (do not re-plan)

**Update (2026-07-07, verified at HEAD):** past W0, **W1 and W2 are also landed.** W1's
diagnostics: D-10 is built (`scripts/legitimacy_diagnostics.py::run_d10`, condensed into every
bundle's `metrics.json` `free_class_score`); D-3 (zero-forcing ablation twin) is built per-ISO
(`scripts/archive/run_pjm77_ablation_twin.py`, `run_pjm80_ablation_twin.py`, `run_miso41_ablation_twin.py`);
D-11/D-13/D-14 remain unbuilt. W2's neutralizations are landed: C-13 (the NYISO `13.15×`
CT_PEAKER / `1.21` CC_REGULAR cross-ISO leak) is gone from `data/fleet.py`/`offer_curves.py`
(retired via PR #1635, "Retire G-26 residual-identified scalars"); C-7's env-var channel
(`INTERCHANGE_SHAPE_IMPORT_PCT`/`EXPORT_PCT`) is deleted from `transmission.py` (only a historical
comment referencing the old read remains in `scenarios.py`). W3–W5 are still open (see the
per-item table below and CLAUDE.md rules 19–26 for the standing rules that remain live).

Verified against the tree at 2026-07-04 (`main` @ 7b0d150). **W0 closed 2026-07-05** — see
`docs/handoffs/scalar-remediation-w0-closure-2026-07-05.md` for the current C-2/C-11 record
(this table predates that closure and is not re-litigated here):

| Item | Status |
|---|---|
| S1 diagnostics D-1/D-2/D-4/D-5/D-9 | **BUILT** — `scripts/legitimacy_diagnostics.py` (+ `--keepers` CI mode) |
| D-12 DOF ledger | **BUILT** — `scripts/build_dof_ledger.py`; `audit_keepers.py` check E8 fails a keeper without a `free_parameters` attestation section |
| D-8 coefficient stability | **RUN** (ERCOT/PJM/CAISO) — `scripts/archive/d8_coefficient_stability.py`, results in `docs/out-of-sample-results-2026-07.md` §2 |
| S2 CAISO CT scrub | Landed via the caiso-51 lineage; keeper is `2026-07-03-caiso-51-firm-base` |
| C-2 `COAL_MAX_CF_BY_PLANT` | **CLOSED** — re-derived from CAMPD outage-adjusted availability (`scripts/data/derive_coal_max_cf.py`), moved to `constants.py`, the `(6179, 2025)` per-year override deleted |
| C-5 CAISO 7,500 MW WECC cap | **CLOSED** — superseded structurally in caiso-51 (published MIC sum + measured p95 corridor envelopes); verification record `docs/caiso-c5-wecc-cap-closeout-2026-07-03.md` |
| C-4 `CHP_BTM_PCT_BY_SECTOR` | **PARTIAL** — industrial/commercial re-derived from EIA-923 Schedule-8 (70/65); `"merchant": 35.0` remains residual-identified (commented as forecast-risk, flagged for the ledger) |
| C-11 generic fallback leakage | **LARGELY CLOSED** — `data/offer_curves.py` fallbacks are now ISO-neutral per rule 25; `miso_deleak_bands` lineage exists; NEISO-47 keeper carries no 13.15×. **Residual: verify D-9 green for MISO/NEISO** |
| `ordc_reliability_deployment_mw` | **DELETED** 2026-07-04 (rule 26); stale prose remains in `results/scarcity.py:635` |
| Rules 16–26 in CLAUDE.md | Landed (S5 item 1) |
| Holdout quarantine | CI-enforced; `calibration-complete.json` markers exist, none declared |

Still live and in scope: C-1, C-3, C-4 (merchant), C-6, C-7 (band **and** a surviving env-var
channel — `transmission.py:2334-2335` reads `INTERCHANGE_SHAPE_IMPORT_PCT`/`EXPORT_PCT`, a rule-24
violation), C-8, C-9 (relocated — status check needed), C-10, C-12 (status check), **C-13 (the
NYISO keeper `nyiso41_hubprices` still carries `CT_PEAKER peak = 13.15` and
`CC_REGULAR econ_high = 1.21` — the one cross-ISO leak live in a keeper)**, C-14 (static
`CAISO_BIDIR_EXPORT_CAP_MW = 4361.0` fallback, `transmission.py:339`), C-15, C-16, C-17, C-18; the D-8 §2B sign-flip
limbs; the D-8 §2C sigmoid single-year pinning; unbuilt diagnostics D-3, D-10, D-11, D-13, D-14.

---

## 1. The decision rule

Applied to every scalar in scope, in order; the **first matching gate wins**. "Scalar" means one
literal or one coherent parameter family (a sigmoid's 4 params triage together).

> **R0 — scope gate.** Class-A cited physical/market constants are out of scope. Class-B uncited
> structural literals are opportunistic cleanup only (not this program).
>
> **R1 — red-flag override (checked first, beats everything below).** If D-8 evidence shows the
> parameter is *unidentified* — Spearman ρ sign flip out-of-training, or a driver relationship
> that reverses across years — the value may **not** be re-derived from the same fit and may
> **not** be documented-and-kept: its only admissible dispositions are **NEUTRALIZE** (ship the
> limb disabled) or **REPLACE** (a new, physically-identified driver). Keeping an unidentified
> coefficient because the level "looks stable" is residual-fitting with extra steps.
>
> **R2 — RE-DERIVE.** An independent published/measured source exists for the quantity and passes
> the rule-14 admissibility test (reproducible for a forward year, responds to changed
> conditions). Disposition: re-derive from that source, cite it, freeze the derive script
> (rule 23). **The trigger for the re-derivation commit is a source-data change — a new intake,
> a corrected extract, a newly published vintage — never a residual.** If the source is not on
> disk, the `data-intake` session comes first, and that intake commit *is* the citable data
> change. Prefer a reconciled version of real data over a clean estimate even when the boundary
> is misaligned (rule 14's misalignment clause; document the reconciliation).
>
> **R3 — REPLACE with a structural mechanism.** The scalar is a stand-in for market structure the
> model lacks (an exogenous revenue stream the market actually clears, a static cap the real
> system computes hourly, a fitted fraction proxying a published requirement). Disposition:
> build the mechanism (rule #1), score it leave-one-year-out within 2023–2025 before promotion
> (rule 22), expect and record fit regressions as open root-cause items — never re-tune them
> away in the same session.
>
> **R4 — NEUTRALIZE.** The value was fitted on another ISO's residual or inherited through a
> generic fallback (rule 25), or it forces behaviour its own driver evidence contradicts.
> Disposition: set the mechanism's **no-op value** (1.0 band, disabled limb, empty override) —
> *neutral*, not zero-forcing. The resulting regression is logged as an open root-cause item
> with the class/metric it moves.
>
> **R5 — DELETE.** Deprecated, demoted, or dead. Removed so it no longer parses (rule 26),
> including stale doc prose that keeps the knob narratively alive.
>
> **R6 — DOCUMENT-AND-KEEP (the residual disposition, literally and figuratively).** No
> independent source exists, no structure is missing, no red flag — the value is
> residual-identified inside the owner's sanctioned offer-curve scope (rule #1), or is genuinely
> unsourceable today. Disposition: a DOF-ledger entry with `source: "residual"`, an **open
> root-cause issue reference** (audit_keepers E8 enforces this), and a published D-11
> sensitivity row once D-11 exists. A keep is a **debt registration, not an endorsement**: it is
> re-visited whenever a new source lands (→ R2) or its D-11 sensitivity shows it carrying
> headline metrics.

Cross-cutting constraints on every disposition:

- **One mechanism per phenomenon (rule 19):** before any REPLACE/RE-DERIVE that floors or biases a
  class, run D-2 attribution on what already floors that class; reconcile, never stack.
- **No residual-chasing:** no session in this program adjusts any value because a triage change
  moved a residual. Deltas go in the commit message and the root-cause log.
- **Holdout quarantine intact (rule 22):** no solve, score, or intake touches 2022/H1-2026 for any
  ISO without a `calibration-complete.json` marker. All probe solves are 2023–2025, full-span
  bundles (rule 16), registered on the dashboard in-session (rule 15).
- **Off-registry channels are deleted on sight (rule 24)** regardless of the host scalar's
  disposition.

---

## 2. Triage — the complete register

### 2.1 The bulk population (~160–190 scalars): per-ISO offer-band multipliers + coal sigmoids

The audit's ~230 count is dominated by the per-ISO `offer_curve_by_group` /
`offer_hr_multipliers` dicts (~54 ERCOT, ~54 PJM, remainder NYISO/NEISO/MISO/CAISO) and the
`COAL_SIGMOID_DEFAULTS` families (C-1). These are **inside the owner's sanctioned rule-#1 scope**
(offer-curve tuning is the model's calibration layer, not a defect), so the population disposition
is **R6 document-and-keep**, executed mechanically:

- Every band/sigmoid scalar in every keeper's `run_config.json` gets a `free_parameters` ledger
  row (`build_dof_ledger.py` — extend coverage if any dict is missed) with identification source
  and lineage solve count.
- Every keeper publishes a D-11 perturbation Jacobian ranking ∂fit/∂knob (§4.3), so the fitted
  surface is *visible* instead of diffuse.
- **Exceptions pulled out of the population and triaged individually:** cross-ISO inherited values
  (→ C-13, R4), any committed-tranche multiplier < 0.85 without a written physical rationale
  (audit §2 flag — ledger entry must carry the rationale or the multiplier is an R6-with-issue),
  and the C-1 red-flagged identification gaps below.

### 2.2 Class-C item-by-item

Dispositions per §1. "Batch" keys into the prompt pack.

| # | Item (scalars) | Gate | Disposition | Source that licenses R2 (and the citable data change) | Batch |
|---|---|---|---|---|---|
| C-1 | `COAL_SIGMOID_DEFAULTS` (~40) | R6 + **R1 partial** | Keep (sanctioned) with per-parameter ledger rows that record the D-8 §2C finding: `floor` identified by 2024 alone, `gas_mid`/`ceil` by 2025 alone (ERCOT `gas_mid`=2.85 sits above *every* 2023–24 month). Anchor asymptotes to citable coal economics (PRB/lignite take-or-pay contract structure, minemouth cost floors) where literature exists — as *documentation of plausibility*, not a refit. **No refit now** (any refit today would be residual-driven); the re-derive trigger is the next new gas regime landing in F923 (a source-data change per rule 23). | F923 delivered-fuel intakes, future years | B-ERC-1 / B-PJM-1 |
| C-2 | Coal CF ceilings | — | **CLOSED** (verify ledger rows cite `derive_coal_max_cf.py`) | done | B-GOV-1 |
| C-3 | ERCOT AS revenue table + saturation curve (7) | **R3** | Replace the exogenous fitted revenue stream: derive AS revenue for the retirement/entry/storage screens from the model's **own reserve co-optimization duals** (the machinery exists — MISO-39 `reserve_pergen`, ERCOT AS-aware layer) with published ERCOT AS clearing prices (EMIL/ASPRICES) as the validation series, not the fit target. Until built: R6 ledger rows + root-cause issue "exogenous AS revenue fitted to the observed 2023→25 crash drives forecast retirements". | Published ERCOT DAM AS clearing prices (new intake) | B-ERC-2 |
| C-4 | `CHP_BTM_PCT_BY_SECTOR` merchant=35.0 (1) | R6 | Keep + ledger row (`source: residual`, open issue: find an independent merchant-CHP host-load source; NAICS-22 sector data gap is real). Industrial/commercial rows: closed, cite Schedule-8. | none yet (that's the issue) | B-GOV-1 |
| C-5 | WECC 7,500 cap | — | **CLOSED** (caiso-51). Residual action: the `iso_configs.py` literal survives as the non-deliverability *fallback* — add the closeout-doc citation + ledger row so the fallback can't silently re-become the binding path. | done | B-CAI-1 |
| C-6 | `IMPORT_TRANCHES`/`EXPORT_TRANCHES` ladders, `atc_base_fraction`, `ATC_SOLAR_K` (~40) | **R2** (per-ISO) | Re-derive each ISO's seam supply curve from **measured neighbor-hub prices + OASIS/ATC data** — the CAISO precedent (caiso-51 measured Malin/Palo-Verde hubs + p95 ATC envelopes) is the template; fetch workflows already exist (`fetch-neighbor-lmp.yml`, `fetch-caiso-oasis.yml`). NYISO's **per-year** scarcity rungs (68.4/79.7/135.2) are year-keyed outcome tracking — R4 neutralize the year-keying; a single ladder or measured-hub path replaces it. The self-referential CAISO static-ladder fallback: R5 delete once the measured path is default. | neighbor-LMP + OASIS intakes (each ISO's intake commit is the trigger) | B-NYI-1 / B-XISO-2 |
| C-7 | Solar-shape NL band 30/10 + env-var channel (2+2) | **R4/R5 (channel), R2 (band)** | Delete the `INTERCHANGE_SHAPE_IMPORT_PCT`/`EXPORT_PCT` env-var reads outright (rule 24) — promote to `ScenarioConfig` fields so they appear in `run_config.json`. Re-ground the 30/10 percentiles on a net-load duck-belly definition (percentile of the *net-load distribution*, derivable from any year's 930 data); demote the negative-price-prevalence validation to a diagnostic. | EIA-930 net-load (already on disk; the re-ground cites the definitional change) | B-CAI-1 |
| C-8 | Core offer step sizes (committed/econ HR mults, peak penalties, coal tranche shares) (~11) | R6 | Ledger rows (`source: residual`, sanctioned scope), D-11 sensitivity. Any <0.85 committed multiplier needs its physical rationale written into the row. | — | B-GOV-1 |
| C-9 | `_PRB_PRICE_CALIBRATION` (7) | **R2** (after status check) | The symbol no longer greps in `fuel.py` — first verify whether it was renamed, moved, or already superseded by the F923-delivered-fuel path. If any calibrated delivered-coal trajectory survives: re-derive from F923 Schedule-5 delivered coal receipts (on disk, 2023–2025) + EIA Coal Markets spot series; the citable change is the F923 coal-receipt curation. | F923 coal receipts (on disk) | B-ERC-1 |
| C-10 | ERCOT AS-requirement regression coefficients (9) | R6→R2-lite | The fit target is the *published requirement MW* (rule-14 admissible). Keep the values; complete the provenance: a derive script/notebook committed with the fit inputs (ERCOT methodology docs, ASPLANNP433 series), citation rows in `parameter-citations.md`, ledger rows `source: measured-market-design`. Freeze (rule 23). | ERCOT AS methodology + requirement series (cite what was fit) | B-ERC-2 |
| C-11 | Generic fallback bands / buried `getattr` mults | — | **Mostly CLOSED.** Remaining: run D-9 against all six keepers and attach the green report to the closure; sweep `data/offer_curves.py` for any surviving inline fallback literal in the offer path (rule 24) and lift into config. | done (verification only) | B-GOV-1 |
| C-12 | CC peaking-tranche 15 % × 4 plants | R6 (verify first) | Status check (the audit's `fleet.py:4208` block has moved). If the four-plant override survives: keep only with per-plant ledger rows + root-cause issue ("F-class CC over-run — tranche moved to fix it"), or R4 neutralize to the class default if the over-run has since been fixed structurally (check against pjm/ercot CC threads). | CAMPD tranche behaviour (if re-derived) | B-ERC-1 |
| C-13 | **NYISO keeper 13.15× CT peak + 1.21 CC econ_high** (2) | **R4 (priority)** | The last live rule-25 violation. Neutralize the ERCOT-inherited 13.15× in the NYISO config (NEISO-42's 4.0 cap is precedent; NEISO-47 is already clean); the 1.21 econ_high was retained *because* removing it cratered C3a −24 % — that is a residual justification, so it neutralizes too, and the C3a hole becomes an open root-cause item (likely the real mechanism is NYISO scarcity/reserve pricing, not a CC markup). Full 3-year re-solve, dashboard probe, expect regression, do not re-tune. | — (neutralization needs no source) | B-NYI-1 |
| C-14 | `CAISO_BIDIR_EXPORT_CAP_MW = 3500` | R5/R2 | caiso-51's per-hub signed corridors with measured p95 envelopes *are* the successor the code comment names. Retire the static scalar from the default path; if a fallback must survive, re-derive it from the OASIS export-direction envelope (same intake as C-6) and label it fallback-only + ledger row. | CAISO OASIS export ATC (on disk via fetch workflow) | B-CAI-1 |
| C-15 | `wefor_residual` 0.06/0.015, `wefor_multiplier` 0.7 | **R4 + R3** | The names admit residual identification; the 0.7 haircut's stated purpose (coal shoulder-month generation) is a wrong-mechanism fix. Neutralize both to no-op (1.0 / None) in a probe; the coal shoulder residual becomes a root-cause investigation into **seasonal maintenance scheduling** — re-derive thermal seasonal availability from CAMPD outage windows (measured, forward-reproducible: planned-maintenance seasonality) instead of a global wind-EFOR haircut. | CAMPD outage windows (on disk) | B-ERC-1 / B-PJM-1 |
| C-16 | PGE-TAC split 0.86/0.14 | **R2** | Re-derive the NP15/ZP26 split from published TAC-area / planning-area load data (CEC forecast forms, FERC-714 planning-area hourly load). The citable change is the FERC-714/CEC intake. | FERC-714 or CEC load data (new intake) | B-CAI-1 |
| C-17 | `Long_Island 0.45` self-supply floor | **R2** | The audit's own repair: re-ground on the published NYISO Locational Minimum Installed Capacity requirement for Zone K (LCR/LMIC %), not the realized 2023 share. Citable change: the NYISO LCR publication intake (small, one table). | NYISO ICAP LCR filings (new intake) | B-NYI-1 |
| C-18 | Per-ISO gas availability 0.85–0.89 (5) | **R2-lite** | The claimed source (NERC GADS 2019–2023) is right; the "was 0.83"/"TODO: verify" trail is the problem. Verification pass against published GADS/State-of-Reliability EFORd tables; set to the published value **even if the backcast worsens** (rule 14); ledger rows with the table citation. | NERC GADS public reports (new small intake) | B-XISO-1 |

### 2.3 D-8 §2B temperature-CF limbs (the sign-flip register)

| Limb | D-8 evidence | Gate | Disposition |
|---|---|---|---|
| PJM ComEd / CC_REGULAR | ρ +0.35 → **−0.19** | **R1** | Ship disabled (neutralize) pending a physically-identified driver; leave-one-year-out re-score of the PJM keeper without it |
| CAISO SP15 / ST_GAS | ρ +0.41 → **−0.16**, drift +35.7 % | **R1** | Same |
| CAISO SP15 / CC_REGULAR | ρ +0.69 → **−0.10** | **R1** | Same |
| PJM EMAAC / ST_GAS (+35.8 %), SWMAAC / CT (−15.6 %, ρ 0.25), ATSI limbs (ρ decay), ERCOT Houston CT (+13.5 %) | drift > gate but no sign flip | R6 | Keep enabled; ledger rows record the drift + n≥30 pooling caveat; re-derive **only** when 2026 CAMPD publishes (a data change) — the added year either stabilizes or kills the limb |

R1 rationale, written once: a commitment floor whose temperature→commitment correlation *reverses*
out-of-training has no identified driver; under rule 17 it is scaffolding fitted to noise. The D-8
report already established the enable-gate flip is a sample-size artifact — the sign flip is not.
Disabling three limbs is a mechanism change: full-span probe solves, leave-one-year-out, dashboard,
regressions logged (rule #1 — never judged by the residual).

---

## 3. Priorities

1. **P0 — C-13 NYISO de-leak** (rule 25, live in a keeper; no source data needed; smallest
   blast radius).
2. **P0 — rule-24 channel deletion** (C-7 env vars): trivial, closes an off-the-books tuning
   channel that could silently change any interchange solve.
3. **P1 — R1 sign-flip limbs** (§2.3): three limbs across PJM/CAISO; these are the audit-defined
   "unidentified" signature and currently ship in keepers.
4. **P1 — diagnostics build** (§4): D-3 + D-10 + D-11 land before the P2 re-derivations so every
   subsequent probe is scored by the new instruments (the S1-first rationale, again).
5. **P2 — re-derivations** (C-6, C-16, C-17, C-18, C-9, C-15 root-cause), each gated on its
   named intake.
6. **P3 — structural replacements** (C-3 AS endogenization; C-6 measured-hub migration for
   remaining ISOs; C-14 fallback retirement).
7. **P4 — ledger completion + keeper re-gate** with D-10/D-11 published (closes the program).

---

## 4. Unbuilt diagnostics — designs

D-1/2/4/5/9 and D-12 exist; D-6/D-7 are the S4 out-of-sample program (owner-gated). This program
builds the rest.

### 4.1 D-3 — zero-forcing ablation twin (rule 21, standard calibration-report step)

- **Config surface:** one `ScenarioConfig` classmethod `as_zero_forcing_ablation(cfg)` (not an
  env var; rule 24) that returns a copy with every **merchant** floor/bridge off:
  `reliability_floor=False`, `ct_netload_drag=False`, `gas_st_netload_drag=False`,
  `caiso_ra_mustoffer=False` (+ bridge/decommit), temperature-CF limbs off,
  `nyiso_local_selfsupply` off, wefor haircuts neutral — **keeping** nuclear must-run, CHP
  steam-following, coal take-or-pay (the §7 D-3 protected set). The off-list is derived from the
  D-2 mechanism registry, not hand-maintained, so a new floor is ablated by default.
- **Runner surface:** `run_calibration_full.py --zero-forcing-ablation` → solves the twin into
  `<out-dir>-ablation`, full year span, recorded in `run_config.json`
  (`"ablation_of": "<bundle>"`).
- **Calibration-report integration (the rule-21 hook):** the skill gains a step between register
  and commit — when the run being registered is (or becomes) a keeper, the ablation twin must
  exist and be registered alongside (`registry/<id>-ablation.json`, linked from the keeper's
  sidecar `"ablation_twin"` field). The dashboard run page shows keeper-vs-ablation per-class
  delta with the "market story" annotation field.
- **Enforcement:** `audit_keepers.py` gains **E9**: a keeper without a registered ablation twin
  fails (mirror of E8). Twins are solve-expensive: run keeper and twin as *concurrent separate
  invocations* (rule 12; cap 2 for per-plant multi-zone ISOs).
- **Pass condition (per audit):** each keeper-vs-ablation class delta carries a written market
  story; a delta explainable only as "the floor buys the residual" is an open root-cause item.

### 4.2 D-10 — free-class-only rescore

- Extend `scripts/calibration_verdict.py` with a `free_class_score` block: recompute the C1
  class-volume criteria **excluding** the pinned classes, per ISO, from the audit L-rows —
  wind/solar wherever L1 (930-delivered CF bound) applies, nuclear (L3), hydro under monthly
  budgets (L6), CHP classes under the export floor (L4), and NYISO net imports (L2). The
  pinned-class list is a declared per-ISO registry in the verdict script (mirroring the D-5
  overlay registry pattern), not inferred.
- Published on the Calibration Status page next to the headline verdict:
  "C1 pass rate: all classes X/Y · free classes X′/Y′". No gate initially — the number itself is
  the deliverable (audit: "pinned-class gate inflation" becomes visible).

### 4.3 D-11 — knob-perturbation Jacobian, published per keeper

- `scripts/knob_jacobian.py`: for each keeper, read the DOF ledger's `free_parameters`, perturb
  each scalar ±10 % (band mults, sigmoid params, tranche shares, adders), reuse the
  `derive_offer_curve_jacobian.py` solve-and-score machinery, and emit
  `<bundle>/knob_jacobian.json`: ranked |∂headline/∂knob| for C2/C3b/C4 + class TWh.
- Rendered as a bar list on the run page. Advisory gate at first; promotion to a hard gate ("no
  single knob moves a headline metric beyond its physical uncertainty band") once two release
  cycles of data exist. Budget note: this is O(n_knobs) one-year solves — run per-ISO as
  background batches, one year (2024) only, explicitly labelled diagnostic (rule 16's probe
  exemption).

### 4.4 D-13 — bench reproducibility CI

- New workflow `bench-repro.yml` (manual + weekly): for each ISO, rebuild the `bench/` artifacts
  twice from committed code + `data/raw`, byte-compare both builds to each other and to the
  committed files; fail on drift.
- Static half: an AST-walk test (`tests/test_bench_no_circularity.py`) asserting no module under
  the bench-builder path imports from `results/` dispatch outputs or reads
  `results/calibration/**` (the L11 BTM pattern, made structurally impossible).

### 4.5 D-14 — negative-control probes

- `scripts/negative_control.py --iso <ISO> --control {gas_price,outage_shuffle}`: clones the
  keeper config, corrupts exactly one physical input (gas price ×1.5; outage windows permuted
  across units within the year), solves one year, and asserts the verdict **worsens** by more
  than a floor delta on C2/C3b. Insensitivity ⇒ a compensating knob exists (the nyiso-32
  pattern); the failing pair (input, knob) is reported by diffing the D-11 rankings of the two
  runs. Registered as explicitly-labelled diagnostic probes, never keepers; one control per ISO
  per release is the cadence.

---

## 5. Sequencing (rule-23 discipline built in)

Every wave's re-derivation prompts name (a) the source dataset, (b) the intake/curation commit
that is the "source-data change" the derive commit must cite, and (c) the frozen derive script.
**No prompt in the pack motivates a change by a residual**, and every prompt carries the standing
instruction: deltas are recorded, never chased.

| Wave | Content | Gate to start | Solves |
|---|---|---|---|
| **W0** | Closure verification: C-2/C-5/C-11 closed-item checks, D-9 green report, ledger coverage sweep (`build_dof_ledger.py` across all six keepers), rule-26 stale-prose deletions (`scarcity.py:635`, any surviving PS-adder text) | none | none |
| **W1** | Diagnostics: D-3 flag + skill step + E9; D-10 verdict block; D-11 script; D-13 CI; D-14 harness | none (parallel with W0) | trivial-case tests only |
| **W2** | Neutralizations needing no data: C-13 NYISO de-leak; C-7 env-var deletion; R1 limb disablement (PJM ComEd, CAISO SP15 ×2) | W1 (so probes are D-scored) | full-span probes: NYISO, PJM, CAISO |
| **W3** | Intakes, then re-derivations: FERC-714/CEC (C-16), NYISO LCR (C-17), GADS tables (C-18), neighbor-LMP/OASIS per remaining ISO (C-6), F923-coal check (C-9), CAMPD maintenance-seasonality derive (C-15 root cause) | per-item: its intake commit | per-item probes where dispatch-affecting |
| **W4** | Structural: C-3 AS endogenization; C-6 measured-hub migration (NYISO first — pairs with C-13's C3a root-cause); C-14 fallback retirement; replacement drivers for any R1 limb worth rebuilding | W2 results + leave-one-year-out protocol | full-span, LOYO-scored |
| **W5** | Program close: ledger 100 % coverage, all keepers re-gated with D-10/D-11 published, every R6 keep has an open issue, `parameter-citations.md` reconciled (sigmoids visible, stale rows dropped), `/sync-docs` | W2–W4 landed | none |

Keeper promotions coming out of W2/W4 follow the standard flow (most-structurally-faithful wins,
rule #1; `calibration-keeper-auditor` after any `keepers.json` edit).

---

## 6. Execution

The prompt pack (`docs/handoffs/scalar-remediation-prompts-2026-07.md`) batches the above by
ISO/mechanism with model assignments and parallelism notes. Batches: B-GOV-1 (W0), B-DIAG-1/2
(W1), B-NYI-1, B-LIMB-1, B-XISO-2ch (W2), B-CAI-1, B-ERC-1/2, B-PJM-1, B-XISO-1/2 (W3–W4),
B-GOV-2 (W5).
