# Documentation & Codebase-Site Update Plan — 2026-07

> Status: ARCHIVED — executed via docs/codebase-site/UPDATE-PROMPT-PACK-2026-07.md (site refresh shipped).

> **Status:** Blueprint for a documentation + code-explorer-site refresh. No
> content written yet — this is the plan and the code-grounded fact base that
> the follow-on prompt pack (`UPDATE-PROMPT-PACK-2026-07.md`) executes against.
>
> **Scope:** bring both the prose model documentation (`docs/*.md`) and the
> code-explorer site (`docs/codebase-site/`) up to the current state of the
> repo for five topics: (1) the **calibration rubric v2.x**, (2) **ablation
> twins + the DOF ledger**, (3) the **model-validity / holdout-testing
> program** (2022 validation → 2019 locked test), (4) **backcast vs forecast
> year spans** (2018–2025 data / 2023–2025 scored vs 2026–2050 forecast, and
> the 2024–2025 overlap as a *target* design), and (5) the **"frontier
> achieved"** calibration-limit designation (NEISO + NYISO).

---

## 0. Governing principle — validate against code, then update

**Code is the source of truth (CLAUDE.md).** Neither the current site nor the
current prose docs may be trusted as correct: this refresh exists precisely
because several of them are stale. Every prompt in the pack therefore follows
the same three-step contract:

1. **Read the authoritative code** for its slice (the files named in §2 below).
2. **Validate** the existing doc/site claim against that code — record what is
   correct, stale, or missing.
3. **Update** the prose/site to match code, citing the authoritative
   `file:line` in a source comment so the next reviewer can re-verify.

When code and a doc disagree, the doc is wrong — fix the doc, never bend the
description to match stale prose. Where the code does **not** implement
something a doc/site claims (the 2024–2025 crossover is the live example),
label it explicitly as *planned / not-yet-implemented*, never as behaviour.

---

## 1. What is stale today (the case for this refresh)

Verified against source during the 2026-07 research pass:

| Surface | Stale claim | Reality in code |
|---|---|---|
| `docs/codebase-site/results-calibration.html` §Calibration Diagnostics | Teaches the **old ±5% binary single-`DEFAULT_TOLERANCE` PASS/FAIL** rubric with a hardcoded 13/14 scorecard | Rubric is **v2.4**, C1–C8 tiered (load-bearing / supporting / protective), two-band, forced-energy budgets, D-4 windows, commercial-grade benchmark |
| Site (all pages) | **No mention** of ablation twins, the DOF ledger, the three-tier holdout program, or "frontier achieved" in any *narrative* prose | All four exist in code + on the two dashboard pages, but are never *explained* |
| `docs/calibration-best-so-far-neiso.md` | Keeper = `neiso-49-stgas-netload`, determination **"NOT-YET"** | Keeper = `2026-07-09-neiso-56-reserve-coopt`, **CALIBRATED-WITH-CAVEATS**, calibration-complete + **frontier achieved** |
| `docs/forecast-validation-plan.md` | 2018→2025 hindcast, AEO2018 fuel | Superseded — live design is `forecast-validation-program-2026-07.md`: 2020-vintage → 2021–2025, AEO2021, 2022 bridge |
| `docs/handoffs/holdout-policy-memo-2026-07.md:9-10`; `forecast-validation-program-2026-07.md:30,266` | `complete: {}` / "none declared yet" | **NEISO declared complete 2026-07-07**; locked-test one-shot already scored |
| `model-methodology-spec.md` | — | Contains **no** section on the calibration rubric, holdout tiers, ablation twins, or frontier — a genuine gap in the primary spec |

There is **no authoritative prose definition** of the rubric-as-scored, the
holdout tiers, ablation twins, or the frontier concept. They live only in code
comments, `keepers.json` notes, and scattered handoff memos. Creating that
authoritative prose is the core documentation deliverable.

---

## 2. Code-grounded fact base (hand this to every writer)

This is the validated reference. Every number/name below was read from source
in 2026-07; a writer should still re-open the cited file to confirm before
publishing (the contract in §0), but this is the map.

### 2.1 Calibration rubric v2.x — where it lives

The rubric is implemented across **two** files; getting this split right is the
single most important thing for the writer:

| Concern | File | Role |
|---|---|---|
| **Scorer / verdict** (C1–C8, two-band logic, determination, budgets) | `scripts/calibration_verdict.py` | `RUBRIC_VERSION = 2.4` (line 82). Reads committed artifacts only; emits PASS/CAVEAT/FAIL per criterion + one determination. Stdlib-only. |
| **Diagnostic suite** (D-1…D-10) that C7/C8 read | `scripts/legitimacy_diagnostics.py` | Computes D-1 diurnal-shape rows + D-2 forced-share summary + the `gates` block → `<bundle>/legitimacy_diagnostics.json`. The scorer **reads this artifact, never recomputes it**. |
| Prose spec | `docs/calibration-determination-rubric.md` | Canonical narrative; header "RUBRIC VERSION 2.4". |

**The criteria and coded thresholds** (`CRITERIA` at `calibration_verdict.py:344-357`;
tolerances 139-338):

| Crit | Name | Tier | Coded threshold |
|---|---|---|---|
| **C1** | Fuel-mix by class, grid-delivered | load-bearing | `|model−actual|` ≤ min(2.0% ISO load, 8 TWh) AND share within ±3.0 pp |
| **C2** | Gas/coal family system volume | load-bearing (two-band on prelim-923 fallback) | complete vintage → defers to C1; prelim fallback vs EIA-930 target ±2.5% / commercial ±5%; immaterial < 10 TWh |
| **C3a** | Mean LMP | load-bearing | ±10% passes clean (target == commercial as of v2.3) |
| **C3b** | Monthly price shape (NRMSE) | load-bearing | NRMSE ≤ 0.20 passes clean |
| **C3c** | Scarcity tail, DA-expressible | **supporting** | model within [0.5×, 2.0×] of DA actual; if actual < 10 h, `|model−actual| ≤ 10`. Per-ISO tail thresholds: ERCOT/PJM/MISO/CAISO $200, NYISO/NEISO $300 |
| **C4** | Fleet hourly dispatch correlation | supporting | r ≥ 0.70 AND NRMSE ≤ 0.30 (gas, coal); skip fleet < 5 TWh |
| **C5a** | CO2 vs eGRID (full-plant, CHP-inclusive) | load-bearing | target ±7% / commercial ±10% |
| **C5b** | Storage throughput | supporting | ±30% |
| **C5c** | Storage dispatch shape (monthly discharge r) | supporting | r ≥ 0.50; skip if actual CV < 0.25 |
| **C6** | Governance gate | **protective**, pass/fail, never caveatable | 4 attestation assertions + machine-clean outage source; UNATTESTED → NOT-YET |
| **C7** | Diurnal shape (D-1) | protective | profile r ≥ 0.8 AND off-peak CV ratio ≥ 0.5; gated only if class ≥ 2% load |
| **C8** | Forced-energy share (D-2) | protective | < 15% peaker / < 30% merchant; ≥ 2%-load materiality; above-cap → grounded-escalation |

**Determination logic** (`determine_from_artifacts`, 1891-2113): C6 not PASS →
NOT-YET; any FAIL → NOT-YET; caveat budget exceeded → NOT-YET; else CALIBRATED
(zero caveats/skips/data-blocks) or CALIBRATED-WITH-CAVEATS. Budgets:
`MAX_PROTECTIVE_CAVEATS = 1`, `MAX_LEDGERED_CAVEATS = 3`; commercial-band
caveats are unbudgeted.

**C8 grounded-above-budget escalation (v2.2)** (`score_forced_share`,
1626-1748): a *material* class above its forced-energy cap is not an automatic
fail — it escalates to a conditional pass requiring BOTH (a) **provenance**:
every binding non-exempt merchant mechanism has a declared, passing **D-4
window** (no declared window → fail, per CLAUDE.md rule 12), AND (b) **shape**:
the class's D-1 profile clears r/CV gates. Both clear → clean PASS classified
`GROUNDED_ABOVE_BUDGET`, surfaced as a report note (never a caveat). Either
fails → FAIL as "forcing shape/provenance mismatch." The driver-window registry
is `D4_WINDOWS` (`legitimacy_diagnostics.py:202-262`).

**Version history as coded** (rubric §9): v1 → **v2** (2026-07-06: tiers replace
HARD/SOFT, two-band, DA-expressible C3c) → **v2.1** (C7/C8 materiality floor 2%
of load; **peaker cap 10%→15%**) → **v2.2** (C8 grounded-above-budget
escalation) → **v2.3** (C3a/C3b target bands set to commercial; C5a re-based to
full-plant CHP-inclusive CO2) → **v2.4** (C3a/C3b score on load-weighted
actual; `RUBRIC_VERSION = 2.4`).

**Writer cautions (code-vs-doc):**
- The diagnostic **measures**, the verdict **gates** — the scorer ignores the
  artifact's embedded verdict and re-gates the measured share against its own
  caps (so old bundles re-score correctly). Do not write "the diagnostic
  decides pass/fail."
- C3a/C3b two-band is now **single-band in effect** (0.10==0.10, 0.20==0.20).
  Do not imply a live price caveat range that no longer exists.
- The scorer reads the **committed run payload**, not `dispatch/<year>_P2.parquet`
  (P2 is archived; the parquet is gitignored/absent for keepers). Lead with the
  payload path.

### 2.2 Ablation twins + DOF ledger

**Ablation twin** = a re-solve of a keeper's exact config with **every merchant
floor/bridge/drag/haircut turned off**, structural must-run kept (nuclear
must-run, CHP steam-following, coal take-or-pay, import boundaries).
- Definition: `ScenarioConfig.as_zero_forcing_ablation` (`src/market_sim/config/scenarios.py:4803-4831`).
  The off-list is **derived from the D-2 mechanism registry**
  (`floor_mechanisms.zero_forcing_field_overrides()`,
  `src/market_sim/data/floor_mechanisms.py:171-187`), with
  `assert_ablation_coverage()` raising if the registry is incomplete — so a
  newly-added merchant floor is ablated by default.
- Production: `scripts/run_calibration_full.py --zero-forcing-ablation` →
  bundle lands with an `-ablation` suffix and records `ablation_of = <base>` in
  its `run_config.json`. Per-keeper twin scripts exist as a pattern
  (`run_pjm94_ablation_twin.py`, `run_nyiso56_ablation_twin.py`, …).
- Storage + linkage: the twin is registered as an ordinary run
  (`frontend/data/backcast/registry/<id>-ablation.json` + `runs/<id>-ablation.js`);
  the **keeper's** sidecar carries an `ablation_twin` field naming the twin.
  Linkage is **manual** (set when the twin is registered), NOT auto-wired by
  `dashboard_add_run.py`. Enforced by **audit_keepers E9**
  (`scripts/audit_keepers.py:213-252, 493-501`). All six current keepers carry
  twins; the grandfather grace list has self-emptied.
- Purpose: the keeper-vs-twin **per-class energy delta** shows what each floor
  buys; a delta explainable only as "the floor buys the residual" is an open
  root-cause item.

**DOF ledger** = the `free_parameters` block written into a bundle's
`calibration_attestation.json` (schema `dof-ledger/v1`).
- Builder: `scripts/build_dof_ledger.py` (`build_dof_ledger.py <bundle> --iso <ISO>`
  or `--all-keepers`; `--check` verifies currency).
- Each entry: `{ name, where, identification, lineage_solves, value?, source?, root_cause? }`.
  `identification` ∈ **`published`** | **`measured-physical`** (frozen derive
  script, rule 23) | **`residual`** (moved a backcast residual — only sanctioned
  inside the rule-#1 offer-curve scope). **A `residual` entry must carry a
  non-empty `root_cause`** or the builder raises.
- Enforced by **audit_keepers E8**: FAILs a keeper whose attestation has no
  `free_parameters` section, or whose any residual entry has a blank
  `root_cause`.

**Writer caution:** the requirement is **CLAUDE.md rule 21** ("Every keeper
carries a DOF ledger and an ablation twin"), but every code comment cites
**"rule 20"** (the audit's own numbering + the documented +1 offset). Note the
offset; do not "correct" the code comments.

### 2.3 Model-validity / holdout-testing program

**Three tiers (CLAUDE.md rule 22 — the discipline):**
- **Train / calibration = 2023–2025.** The only years tuned against; every
  keeper built + scored here, all three in one bundle (rule 16).
- **Validation holdout = 2022**, extensible backward as a ladder
  (2022 → 2020–2022 → earlier). **Iterable** — a miss may send you back to
  re-tune 2023–2025. A 2022 number is *model-selection* evidence, **not**
  certified out-of-sample skill.
- **Locked test = 2019 and H1-2026.** **Touch once, ever.** Scored exactly once
  per ISO with the frozen keeper config; the result stands; no calibration may
  respond to it without designating a fresh never-touched year. (2019 =
  clean-regime; H1-2026 = forward-edge.)

**Operational meaning of "first the 2022 holdout, then the true 2019 holdout
test":** declaring an ISO calibration-complete (adding its marker to
`calibration-complete.json`) unlocks holdout solves for that ISO. You first run
the **iterable 2022 validation** — solve the frozen keeper on 2022, score it,
and *if it misses you may go back and re-tune 2023–2025 and repeat.* Only when
satisfied do you fire the **one-shot 2019 (+ H1-2026) locked test**: solve the
now-frozen config **once**, record the number, never let it re-enter tuning.
2019 is the honest out-of-sample number precisely because — unlike 2022 — it is
never iterated against.

**Enforcement (what is actually machine-checked):**
- The in-sample window `{2023, 2024, 2025}` is a hard-coded frozenset in
  **three** parallel places: `run_calibration_full.py:5025`,
  `audit_keepers.py:185`, `legitimacy_diagnostics.py:319`.
- **CLI solve gate:** `enforce_holdout_year_gate` (`run_calibration_full.py:5029-5073`)
  hard-fails a `--year` outside the window unless **both** `--holdout-authorized`
  **and** the ISO carries a marker in `calibration-complete.json`.
- **CI score/registration gate:** `.github/workflows/ci.yml` job `quarantine-gates`
  runs `audit_keepers.py --check` + `legitimacy_diagnostics.py --keepers`
  (`run_d6_quarantine`), failing any registered bundle whose years breach the
  window without a marker.
- **The code enforces a single binary** (year ∈ {2023,2024,2025} vs not); the
  validation/locked *distinction* is discipline, not machine-enforced — the CI
  gate is deliberately tier-agnostic.
- **Only NEISO is marked complete** (`calibration-complete.json`, declared
  2026-07-07); its 2019 + H1-2026 one-shot was scored once and stands. The other
  five ISOs remain fully quarantined for holdout solving.
- **Data intake is deliberately ungated:** raw data is on disk 2018→H1-2026;
  intake for any year is allowed under owner authorization with no-LP validation
  only (see the `intake_log`). Only *solve/score/register* is quarantined.
- Known residual gap: `scripts/run_calibration.py` (the non-`_full` script) has
  **no** year gate — state this wherever a doc claims "the solve entry points
  are gated."

**Forecast-side validation** (separate from the dispatch holdout tiers):
- **Capacity hindcast** — `scripts/run_capacity_hindcast.py` /
  `score_capacity_hindcast.py` / `build_capacity_actuals.py` /
  `register_hindcast.py`: 2020-vintage init → solve {2021, 2023, 2024, 2025},
  bridge 2022. ERCOT + PJM run, both fuel variants; results are diagnostic
  "bad-miss" runs (e.g. ERCOT 0 GW solar vs 25 GW actual), registered outside
  the backcast registry under `results/hindcast/` + `frontend/data/hindcast/`.
- **Forecast invariants** — `scripts/check_forecast_invariants.py` (I1–I14
  single-run + P1–P3 paired), `.github/workflows/forecast-invariants.yml`,
  `tests/test_forecast_invariants.py`.
- **D-7 statmode / D-8 frozen-coefficient stability** — computed only on
  2023–2025, never a holdout year.

### 2.4 Backcast span vs forecast span (and the 2024–2025 overlap)

**Implemented today:**
- **Data on disk:** 2018 → H1-2026 (per `docs/data-register-2026-07.md` Part 2;
  CAMPD unit-level 2018–2021 for every state, 2022 + H1-2026 where intaken).
- **Scored backcast dispatch:** **2023–2025 only** (plus the single NEISO
  one-shot). The "backcast covers 2018–2025" framing is true of *data intake*,
  not of what is solved/scored.
- **Forecast horizon:** `constants.py:3292-3293` `START_YEAR = 2026`,
  `END_YEAR = 2050`. There is **no 2024–2025 overlap** in the default forecast
  horizon.

**The 2024–2025 crossover overlap — ROADMAP, not code.** The intended design
(backcast 2018–2025 vs forecast 2024–2030, scored in both modes over 2024–2025)
is **not** implemented: forecast starts 2026, and no code path scores 2024–2026
dispatch in both backcast and forecast modes (the rule-22 "crossover window
scored in both modes" is a policy concept; grepping `crossover` in `.py` returns
only unrelated coal-sigmoid gas-price code). **Document it as a labelled target
design**, never as behaviour. The closest *implemented* analogue is the
capacity hindcast (§2.3), which overlaps the 2023–2025 backcast years at the
capacity layer.

> **Owner decision pending (flagged in the delivering session):** whether this
> plan should later be extended to add the code work for a 2024-start forecast +
> dual-mode crossover scoring. Until then, all site/doc content treats it as
> roadmap.

### 2.5 "Frontier achieved" designation

**Definition (as implemented):** an **owner-declared, purely declarative
dashboard designation** meaning *every named admissible mechanism for the ISO's
residual caveat family has been tried on record, and what remains is either
inadmissible to close (residual-fitting, CLAUDE.md rule 26) or blocked on data
that does not exist publicly.* It is **never gating and never touches the
verdict.**
- Canonical gloss: `scripts/build_status.py:458-463` (code comment).
- Data payload: `frontend/data/backcast/keepers.json` top-level `"frontier"`
  map (`{declared, note}` per ISO). Currently **NEISO + NYISO**, both
  2026-07-11.
- Threading: `build_status.py` attaches `verdict["frontier"]` **after**
  `determine()` → written into `status.js`; never feeds the verdict.
- Rendering: `docs/codebase-site/calibration-status.html` (card badge line ~176,
  detail badge ~282, note block ~291-298); style `.cs-badge.det-frontier`
  (indigo `#4c5fd5`) in `css/bc-pages.css:685-686`.

**Distinct from `calibration-complete.json`** — do not conflate:

| | `calibration-complete.json` `complete` marker | `keepers.json` `frontier` map |
|---|---|---|
| Purpose | **Gating** — authorizes the rule-22 holdout one-shot | **Declarative label only** |
| Enforced by | CI + `run_calibration_full.py` hard-fail | nothing (pure rendering) |
| Current holders | NEISO only | NEISO + NYISO |

(NYISO has a frontier designation but **no** complete marker — frontier does not
imply holdout authorization.)

**Why NEISO + NYISO:** both drove every hard/volume criterion into band; their
entire remaining residual is the **price scarcity tail (C3c)**, gated by
reserve-requirement dynamics that are either unimplemented by the real ISO or
need new measured identification.
- **NEISO** (`neiso-limb-b-offer-surface-2026-07.md` §5): four named mechanisms
  tried (winter fuel-security stack, in-LP reserve co-opt, measured dynamic
  reserve requirements engaging 1/12 tail hours, measured fast-start DA offer
  surface). Root limit: the real tail forms while the model still carries
  several GW of cheaper non-fast-start headroom, so no repricing of the
  fast-start band reaches it. C2 also waits on the final 2025 EIA-923 vintage.
- **NYISO** (`calibration-log.md:173-210`): the deep >$300 tail's two candidate
  reserve levers are chased to ground; the sole remaining gap is the net-load
  forecast-uncertainty reserve increment (IMM Recommendation 2021-1), which
  NYISO has not implemented and which has no published formula — adding it would
  be residual-fitting (rule 26).

**Writer cautions:** (1) no prose/spec definition exists — this refresh creates
it; (2) `calibration-best-so-far-neiso.md` is badly stale and carries no
frontier note; (3) the word "frontier" is overloaded (older informal usage all
over the calibration logs) — name the **formal** designation unambiguously; (4)
for NEISO the frontier-note keeper (`neiso-56`), the `keepers.json` pointer
(`neiso-56`), and the complete-marker keeper (`neiso-54`/locked-test `neiso-53`)
are **different runs** — don't assume they align.

---

## 3. Deliverables

### 3.1 Documentation surface (`docs/*.md`)

| # | Deliverable | Action |
|---|---|---|
| D1 | **`docs/calibration-and-validation-methodology.md`** (NEW) | The authoritative prose the repo currently lacks: rubric v2.x (C1–C8, tiers, budgets, D-4 escalation, version history), ablation twins + DOF ledger, the three-tier holdout program + quarantine enforcement, backcast/forecast spans, and the frontier designation. Each section points back to the canonical `file:line` (§2). This becomes the doc the site pages cite. |
| D2 | `docs/calibration-best-so-far-neiso.md` | Fix: keeper `neiso-56-reserve-coopt`, CALIBRATED-WITH-CAVEATS, calibration-complete + frontier note. Reconcile the three divergent keeper pointers (§2.5). |
| D3 | `docs/calibration-best-so-far-nyiso.md` | Add the formal frontier-achieved note; disambiguate from older informal "frontier" phrasing. |
| D4 | `docs/forecast-validation-plan.md` | Mark **superseded** by `forecast-validation-program-2026-07.md` (2020→2025 / AEO2021 / 2022-bridge). |
| D5 | `docs/handoffs/holdout-policy-memo-2026-07.md`, `docs/handoffs/forecast-validation-program-2026-07.md` | Correct the stale `complete: {}` / "none declared" claims (NEISO complete since 2026-07-07). |
| D6 | `model-methodology-spec.md` | Add a short cross-reference section pointing to D1 (the spec has no calibration/validation methodology today); note P2 archived where the three-solve section still implies it is live. |
| D7 | `CHANGELOG` + `/sync-docs` pass | Run `/sync-docs` at the end to catch any remaining drift and log the doc changes. |

### 3.2 Code-explorer site (`docs/codebase-site/`)

| # | Deliverable | Action |
|---|---|---|
| S1 | **`calibration-rubric.html`** (NEW narrative page) | Teaches rubric v2.x (C1–C8, tiers, two-band, forced-energy budgets, D-4 windows, commercial-grade benchmark, version history) **and** the frontier-achieved designation (topics b + e). Links to the live `calibration-status.html` dashboard. |
| S2 | **`model-validity.html`** (NEW narrative page) | Teaches the three-tier train/validation/locked-test program, the touch-once discipline, the quarantine gates (CLI + CI), the capacity hindcast + forecast invariants, and the backcast-data(2018–H1-2026) / scored(2023–2025) / forecast(2026–2050) spans — with the **2024–2025 overlap presented as a labelled roadmap target** (topics c + d). |
| S3 | `results-calibration.html` | Rewrite §Calibration Diagnostics + replace the stale 13/14 ±5% scorecard with a v2.x C1–C8 tiered example; add a narrative subsection on **ablation twins + the DOF ledger** (topic a). Cross-link to S1/S2. |
| S4 | `data/*.json` (illustrative) | New/updated static JSON backing S1–S3 charts (e.g. a C1–C8 tiered scorecard, an ablation keeper-vs-twin delta bar, a three-tier timeline). **Illustrative + `_meta`-tagged**, never raw solver output. |
| S5 | `js/nav.js` | Add S1 + S2 to `NAV_ITEMS` (Backcast dropdown group). One-line insertions; covers desktop + mobile. |
| S6 | `forecast-validation.html` (optional) | Add a short "where these fit in the holdout program" note linking to S2; otherwise fold the crossover framing entirely into S2. |

**Deploy guardrails (MUST NOT touch):** `frontend/data/backcast/manifest.js`,
`benchmark.js`, `completeness.js`, `status.js`; anything under
`docs/codebase-site/data/backcast/` (generated at deploy, gitignored); per-run
`frontend/data/backcast/{registry,runs,bench}/` and `keepers.json` (written by
the calibration-report skill, not by hand). Editable: any `.html`, `js/*.js`,
and the static narrative `data/*.json`. New pages are added purely by dropping
the HTML + one `NAV_ITEMS` entry — no build step.

---

## 4. Sequencing & parallelism

```
Phase 0 — VALIDATE (shared, blocking)
  0A  Write D1 (authoritative methodology doc) — the single source the site
      pages cite. Re-verifies §2 against code. Blocks S1/S2/S3.
        │
        ├───────────────┬───────────────┐
        ▼               ▼               ▼
Phase 1 — DOCS (parallel with Phase 2 scaffold)
  D2  D3  D4  D5  D6   (stale-doc fixes; independent files, all parallel)

Phase 2 — SITE SCAFFOLD (blocking gate before Phase 3 pages)
  2A  S5 nav entries + S4 illustrative data JSON + empty S1/S2 page shells
      (touches shared js/nav.js and data/ — must land before parallel pages)
        │
        ├───────┬───────┐
        ▼       ▼       ▼
Phase 3 — SITE PAGES (parallel; separate HTML files, no shared-file writes)
  S1 (calibration-rubric)   S2 (model-validity)   S3 (results-calibration edit)
        │
        ▼
Phase 4 — INTEGRATION & QA (sequential)
  4A  Cross-link audit + nav consistency + responsive/section-rhythm pass
  4B  Accuracy audit against code (every claim vs §2 file:line) + keeper-text
      audit (calibration-keeper-auditor agent) + D7 /sync-docs
```

**Critical path:** max(0A, 2A) → any Phase 3 page → 4A → 4B (4 sequential
steps). **Max parallelism:** 6 — wave 1 runs 0A ∥ 1A–1D ∥ 2A concurrently
(they touch disjoint files; only 1E — which cross-references the file 0A
creates — and the Phase 3 pages wait on 0A). *Amended 2026-07-11 after review:
0A does not block the Phase 1 fixes or the Phase 2 scaffold.*

## 5. Model assignments (rationale)

| Work | Model | Why |
|---|---|---|
| 0A (D1 methodology doc) | **Fable 5** | The single source every site page cites — highest-stakes accuracy; must reconcile subtle code-vs-doc distinctions (scorer-vs-diagnostic, complete-marker-vs-frontier, roadmap-vs-implemented). |
| S1, S2 (new narrative pages) | **Opus** | High-accuracy teaching pages, built from the 0A doc plus re-verified code. |
| S3 (results-calibration rewrite) | **Opus** | Replaces a materially-wrong rubric explanation; must not reintroduce the old ±5% framing. |
| D2–D6 stale-doc fixes | **Sonnet** | Targeted edits with unambiguous correct values from §2; low reasoning load. |
| S4 illustrative data JSON, S5 nav entries | **Sonnet** | Mechanical, spec-complete. |
| 4A integration/responsive | **Sonnet** | Pattern-matching against existing pages. |
| 4B accuracy + keeper-text audit | **Fable 5** + `calibration-keeper-auditor` agent | Final truth gate; the auditor agent verifies keeper/frontier text matches actual run results. |

## 6. Non-goals

- No code changes to the model, scorer, or solve gates (docs + site only). The
  2024-start forecast / dual-mode crossover is explicitly **out of scope** as a
  code change — documented as roadmap only unless the owner extends scope.
- No touching deploy-owned generated data (§3.2 guardrails).
- No new backcast runs, no dashboard registrations, no holdout solves.
- No duplication of the live dashboard — the new narrative pages *explain* and
  *link to* `calibration-status.html` / `backcast-runs.html`, they do not
  replicate them.
