# Calibration & Validation Methodology

Status: **authoritative prose reference** (created 2026-07 documentation
refresh, `docs/codebase-site/UPDATE-PLAN-2026-07.md` D1). This is the single
narrative definition of how the model is calibrated, scored, ablated,
holdout-tested, and — where applicable — declared at its calibration frontier.
Every claim below was verified against source at writing time; each section
carries a `Source:` note so the next reviewer can re-verify. **Code is the
source of truth** — when this document and code disagree, fix this document.

Companion documents: `docs/calibration-determination-rubric.md` (the canonical
criterion-by-criterion rubric spec, RUBRIC VERSION 2.4),
`model-methodology-spec.md` (the LP/market formulation),
`docs/handoffs/holdout-policy-memo-2026-07.md` (the three-tier holdout
amendment), `docs/model-legitimacy-audit-2026-07.md` (the D-1…D-10 diagnostic
program and protective rules).

---

## 1. The calibration rubric (v2.x)

### 1.1 Two files, two roles: the diagnostic MEASURES, the verdict GATES

The rubric is implemented across exactly two scripts, and the division of
labour between them is the most important fact in this section:

| Concern | File | Role |
|---|---|---|
| **Scorer / verdict** | `scripts/calibration_verdict.py` | `RUBRIC_VERSION = 2.4`. Scores C1–C8 per year, applies tiers, two-band tolerances, caveat budgets, and emits one determination: `CALIBRATED`, `CALIBRATED-WITH-CAVEATS`, or `NOT-YET`. Stdlib-only; reads **committed artifacts only** and never re-solves the LP. |
| **Diagnostic suite** | `scripts/legitimacy_diagnostics.py` | Computes the D-1…D-10 legitimacy diagnostics — in particular the D-1 diurnal-shape rows and D-2 per-class forced-share summary — into the bundle artifact `legitimacy_diagnostics.json`, together with a `gates` block recording the gate values in force when it was written. |

The scorer **reads** the committed `legitimacy_diagnostics.json`; it **never
recomputes** the diagnostics (the S1 suite stays the single implementation).
Conversely, the diagnostic's own embedded per-row verdicts do not decide the
determination: for C8 the scorer re-gates the artifact's *measured* forced
share against the rubric's current caps (so bundles written under earlier gate
values re-score correctly without regeneration), and for C7 it applies its own
materiality floor before honouring the artifact's D-1 gate outcome. In one
sentence: **the diagnostic measures, the verdict gates.**

What the scorer reads (the reproducibility contract, rubric §0a): the registry
sidecar (`frontend/data/backcast/registry/<id>.json`), the **committed run
payload** (`frontend/data/backcast/runs/<id>.js`, gzip+base64 — the same
numbers the dashboard renders), the benchmark parts
(`frontend/data/backcast/bench/<ISO>/<year>.json.gz`), the committed DA tail
counts (`frontend/data/backcast/tail/actual_tail.json`), and the bundle's
`run_config.json` / `meta.json` / `calibration_attestation.json` /
`legitimacy_diagnostics.json`.

> **Caution — what the scorer does NOT read.** It never reads
> `dispatch/<year>_P2.parquet` or any solver parquet: P2 is archived and the
> dispatch parquets are gitignored/absent for keepers. The committed run
> payload is the model side of every score.

Source: `scripts/calibration_verdict.py:61-119` (version + status/tier
constants), `docs/calibration-determination-rubric.md` §0a;
`scripts/calibration_verdict.py:1448-1526` (C7 reads the artifact),
`:1626-1748` (C8 re-gates the measured share).

### 1.2 The criteria: C1–C8

Twelve scored criterion ids grouped as C1–C8, each with a tier:
**load-bearing** (certifies the intended uses directly; two-band where a
published commercial comparable exists), **supporting** (sub-annual dynamics;
single wide band), **protective** (the anti-self-deception gates). Any FAIL on
**any** tier forces `NOT-YET`.

| Crit | Name (scorer id) | Tier | Coded threshold |
|---|---|---|---|
| C1 | Fuel-mix by class, grid-delivered (`fuelmix`) | load-bearing | Per class: volume miss ≤ min(2.0 % of ISO load, 8 TWh) **and** generation share within ±3.0 pp (`FUELMIX_VOL_LOAD_FRAC`, `FUELMIX_VOL_CAP_TWH`, `FUELMIX_SHARE_PP`). `CT_CHP`/`OTHER`/`OTHER_FOSSIL` excluded. |
| C2 | System volume, gas/coal families (`sysvol`) | load-bearing | Complete-vintage years: **defers to the per-class C1 gate** (the old ±2.5 % family band is retired for this path). Preliminary-EIA-923 families only: family aggregate vs the EIA-930 grid total, target ±2.5 % (`SYSVOL_TOL`) / commercial ±5 % (`SYSVOL_COMMERCIAL`). Family < 10 TWh (`SYSVOL_MIN_TWH`) → immaterial skip, governed by C1. |
| C3a | Mean LMP (`price_mean`) | load-bearing | ±10 % passes clean (`PRICE_MEAN_TOL = PRICE_MEAN_COMMERCIAL = 0.10`). Scored on the v2.4 load-weighted actual (`rt_lw`→`da_lw`, legacy equal-hour fallback labelled). |
| C3b | Monthly price shape (`price_shape`) | load-bearing | Monthly NRMSE ≤ 0.20 passes clean (`PRICE_SHAPE_NRMSE_MAX = PRICE_SHAPE_NRMSE_COMMERCIAL = 0.20`). |
| C3c | Scarcity tail, DA-expressible (`price_tail`) | supporting | Model tail hours within [0.5×, 2×] of the DA actual (`TAIL_LO`, `TAIL_HI`); if the count is < 10 h, |model−actual| ≤ 10 passes (`TAIL_SMALL_COUNT`). Tail thresholds: $200/MWh ERCOT/PJM/MISO/CAISO, $300/MWh NYISO/NEISO (`TAIL_THRESHOLD`). |
| C4 | Fleet hourly dispatch correlation (`dispatch_corr`) | supporting | Pearson r ≥ 0.70 and NRMSE ≤ 0.30 (gas, coal) (`DISP_R_FLOOR`, `DISP_NRMSE_MAX`); fleet < 5 TWh skipped (`DISP_MIN_TWH`). |
| C5a | CO₂ vs eGRID, full-plant CHP-inclusive (`co2`) | load-bearing | Target ±7 % (`CO2_TOL`) / commercial ±10 % (`CO2_COMMERCIAL`). |
| C5b | Storage throughput (`storage`) | supporting | ±30 % (`STORAGE_TOL`). |
| C5c | Storage dispatch shape (`storage_shape`) | supporting | Monthly-discharge r ≥ 0.50 (`STORAGE_SHAPE_R_FLOOR`); skipped when the actual monthly-discharge CV < 0.25 (`STORAGE_SHAPE_MIN_CV`, degeneracy guard). |
| C6 | Governance gate (`governance`) | **protective**, never caveatable | Pass/fail: machine-clean config (exogenous outage source, no forbidden fitted-mechanism flags) **and** an attestation with all four assertions true (`levers_trace_to_measured_input`, `no_fit_to_price_residuals`, `no_pinning_to_actuals`, `outage_filter_exogenous_net_load`). No attestation → `UNATTESTED` → `NOT-YET`. |
| C7 | Diurnal shape, D-1 (`shape`) | protective | Hour-of-day profile r ≥ 0.8 and off-peak CV ratio ≥ 0.5 (`D1_MIN_PROFILE_R`, `D1_MIN_CV_RATIO` — recorded in the artifact's `gates` block); gated only for classes ≥ 2 % of ISO load (`PROTECTIVE_MIN_LOAD_FRAC`). |
| C8 | Forced-energy share, D-2 (`forced_share`) | protective | < 15 % peaker / < 30 % merchant (`FORCED_SHARE_PEAKER_MAX`, `FORCED_SHARE_MERCHANT_MAX`), classes ≥ 2 % of load; above-cap → grounded-above-budget escalation (§1.4). |

> **Caution — C3a/C3b are single-band in effect.** Since v2.3 the price target
> bands coincide with the commercial bands (0.10 == 0.10, 0.20 == 0.20), so
> there is **no live commercial-band caveat range on the two price criteria**:
> inside the band is a clean PASS, outside is a FAIL (ledgerable only as a
> measured-input limitation). The former ±5 %/0.15 targets survive only as
> reported magnitudes. Do not describe a price caveat range that no longer
> exists.

Source: `scripts/calibration_verdict.py:121-357` (all tolerance constants +
the `CRITERIA` map at 344-357); `:746-777` (C2's complete-vintage deferral to
C1 and preliminary-923 fallback); `:1767-1826` (C6);
`scripts/legitimacy_diagnostics.py:120-121` (D-1 gate values).

### 1.3 Determination logic and caveat budgets

`determine_from_artifacts` scores every criterion-year, applies the exceptions
ledger (FAIL → budgeted `MEASURED_LIMIT` caveat where an explicit ledger entry
documents the actual as the limitation), aggregates per criterion
(FAIL > CAVEAT > PASS > SKIPPED), then decides in order:

1. **C6 not PASS** (FAIL or UNATTESTED) → `NOT-YET`.
2. **Any FAIL on any criterion** → `NOT-YET`.
3. **Caveat budget exceeded** → `NOT-YET`. Budgets: protective ledgered
   caveats ≤ 1 (`MAX_PROTECTIVE_CAVEATS`; C6 itself is never caveatable);
   non-protective ledgered caveats ≤ 3 (`MAX_LEDGERED_CAVEATS`).
   **Auto commercial-band caveats are unbudgeted** — inside the certification
   claim by construction; every one is still listed with its magnitude.
4. Otherwise `CALIBRATED` iff **zero** caveats of any kind, nothing SKIPPED,
   and no data-blocked target years; else `CALIBRATED-WITH-CAVEATS` with the
   reasons enumerated (band caveats, ledgered caveats, unscored criteria —
   protective skips called out explicitly — and data-blocked years).

An unscored criterion is never a silent pass: it caps the determination at
`CALIBRATED-WITH-CAVEATS` and is named in the reasons.

Source: `scripts/calibration_verdict.py:1891-2108`
(`determine_from_artifacts`), `:256-274` (budget constants + rationale).

### 1.4 The C8 grounded-above-budget escalation (v2.2)

A *material* class above its forced-energy cap is **not** an automatic FAIL.
It escalates to a conditional pass requiring **both**:

- **(a) Provenance** — every binding **non-exempt merchant** mechanism forcing
  the class clears **D-4 off-window binding**: it binds only inside its
  driver-justified window. A mechanism with **no declared D-4 window fails
  this leg by definition** (the "no floor without a window" rule — CLAUDE.md
  rule 17, cited as "rule 12" in older comments). Exempt mechanisms
  (structural must-run: `nuclear_mustrun`, `chp_steam`, `coal_mustrun`; and
  the non-thermal boundaries `firm_import`, `nyiso_local_selfsupply` —
  `FORCED_EXEMPT_MECH_NAMES`) are outside the C8 arithmetic entirely.
- **(b) Shape** — the class's D-1 hour-of-day profile clears the artifact's
  own gates (profile r ≥ `d1_min_profile_r`, off-peak CV ratio ≥
  `d1_min_cv_ratio`), applied to **any** escalating class, not only the
  default D-1-gated set.

Both clear → **clean PASS**, classified `GROUNDED_ABOVE_BUDGET` and surfaced
as a **report note, never a caveat** (so the high forcing stays visible and
auditable without counting against any budget). Either leg fails → FAIL,
described as a forcing shape/provenance mismatch — the "forcing variables are
wrong" signal. The escalation is scorer-only: both signals already live in
every committed `legitimacy_diagnostics.json`, so existing keepers re-score in
place with no re-solve and no bundle regeneration, and the change only
*relaxes* C8 (below-cap behaviour is unchanged; above-cap gains a pass path).

**The `D4_WINDOWS` registry** is the driver-window declaration table the
provenance leg reads: a dict mapping `(mechanism id, class-or-None)` →
`[start_hour, end_hour)` — e.g. `reliability_floor × CT_PEAKER` → [14, 22)
(measured downstate CT evening ramp), `ct_netload_drag` → [15, 22),
`st_netload_drag` and `reliability_floor × ST_GAS` → all 24 hours (the CAMPD
evidence shows the gas-steam fleet committed day and night — there is no hour
its own driver evidence says it is offline), `caiso_gas_commitment_floor` →
[9, 17), `cc_mustrun_per_plant × CC_REGULAR` → all hours. Each entry carries a
cited evidence base in the source; grounding a specific keeper's over-budget
class requires a cited `D4_WINDOWS` entry for its mechanism **and** that
bundle's `legitimacy_diagnostics.json` regenerated so the D-4 row exists, and
any mechanism-change-driven verdict flip is scored leave-one-year-out within
2023–2025 before the keeper is promoted (CLAUDE.md rule 20, v2.2 amendment).

Source: `scripts/calibration_verdict.py:299-338` (escalation constants +
exempt set), `:1626-1748` (`score_forced_share`), `:2056-2069` (notes
surfacing); `scripts/legitimacy_diagnostics.py:202-262` (`D4_WINDOWS`).

### 1.5 Version history

| Version | Date | One-line summary |
|---|---|---|
| v1 | 2026-06 → 2026-07-05 | Original machine-enforced rubric; 2026-07-02 re-balance (C1 loosened, C3 tightened, soft budget 3→2); 2026-07-04 C7/C8 protective gates added. |
| v2 | 2026-07-06 | Fitness-for-purpose re-anchor: tiers replace HARD/SOFT, two-band target/commercial tolerances with published anchors, C3c re-scoped to the DA-expressible tail, budgets re-derived (ledgered ≤ 3, commercial-band unbudgeted). |
| v2.1 | 2026-07-06 | C7/C8 materiality floor (≥ 2 % of load); C8 peaker cap 10 % → 15 %; scorer gates D-2's measured shares against the rubric's caps, not the artifact's embedded verdicts. |
| v2.2 | 2026-07-07 | C8 grounded-above-budget escalation (§1.4): above-cap passes clean iff D-4 provenance + D-1 shape clear, surfaced as a note. |
| v2.3 | 2026-07-09 | C3a/C3b target bands set to the commercial values (single-band in effect); C5a re-based to full-plant CHP-inclusive CO₂. |
| v2.4 | 2026-07-09 | C3a/C3b score on the like-for-like **load-weighted** actual (`rt_lw`/`da_lw`), replacing the legacy equal-hour hub mean (legacy fallback explicitly labelled). |

Note: the rubric doc's §9 bullet list currently ends at v2.3; v2.4 is defined
in that document's header, its §1 C3a entry, and
`docs/rubric-v24-price-basis-memo-2026-07.md`.

Source: `docs/calibration-determination-rubric.md:1-7` (header), §9;
`scripts/calibration_verdict.py:61-82` (version comment + constant).

---

## 2. Ablation twins and the DOF ledger

Both are keeper obligations under **CLAUDE.md rule 21** ("Every keeper carries
a DOF ledger and an ablation twin").

> **Caution — rule numbering.** Code comments for both features cite
> **"CLAUDE.md rule 20"**. That is the documented +1 offset: the protective
> rules came from the legitimacy audit's §8 numbering (16–25 there), and
> CLAUDE.md later gained rule 16 (all-years-one-bundle), shifting them to
> 17–26 — audit rule 20 = CLAUDE.md rule 21. Do **not** "fix" the code
> comments; the offset is documented in CLAUDE.md itself.

### 2.1 Ablation twins (audit D-3)

An **ablation twin** is a re-solve of a keeper's exact config with **every
merchant floor/bridge/drag/availability-haircut turned off**, keeping only
structural must-run (nuclear must-run, CHP steam-following, coal take-or-pay)
and the import boundary. The keeper-vs-twin **per-class energy delta**
quantifies what each floor buys; a delta explainable only as "the floor buys
the residual" is an open root-cause item, not a calibrated parameter.

- **Definition:** `ScenarioConfig.as_zero_forcing_ablation(cfg)` — a config
  transform applied *after* all per-ISO defaults and overrides, so
  config-level defaults (e.g. CAISO `ct_netload_drag` / `caiso_ra_mustoffer`)
  are forced off regardless of how they were set.
- **The off-list is derived, not hand-maintained:** it comes from the D-2
  mechanism registry via `floor_mechanisms.zero_forcing_field_overrides()`
  (union of every `MECH_ABLATION_FIELDS` entry plus the
  `EXTRA_ZERO_FORCING_FIELDS` WEFOR haircuts — merchant availability levers
  with no mechanism id). `assert_ablation_coverage()` raises if any mechanism
  id is neither KEPT (`MECH_ABLATION_KEPT` = structural must-run +
  `firm_import` + none) nor ABLATED — so **a newly added merchant floor is
  ablated by default** and cannot silently escape the twin.
- **Production:** `scripts/run_calibration_full.py --zero-forcing-ablation`
  solves the recipe's twin; the bundle lands with an `-ablation` suffix and
  records `ablation_of = <base bundle>` in its `run_config.json`. The twin is
  registered as an ordinary dashboard run
  (`registry/<id>-ablation.json` + `runs/<id>-ablation.js`).
- **Linkage is MANUAL:** the keeper's registry sidecar carries an
  `ablation_twin` field naming the twin. `dashboard_add_run.py` does **not**
  auto-wire it — it is set when the twin is registered.
- **Enforcement — audit_keepers E9:** a keeper without a resolvable
  `ablation_twin` sidecar link FAILs; a *declared-but-broken* link FAILs
  regardless of any grace. The rollout grandfather list
  (`E9_ABLATION_TWIN_GRANDFATHER`) was designed to self-empty as keepers were
  re-registered with twins; today **all six current keepers carry registered
  twins**, so the exemption no longer applies to anything (one stale literal
  remains in the set — dead code awaiting deletion, per its own docstring).

Source: `src/market_sim/config/scenarios.py:4957-4985`
(`as_zero_forcing_ablation`); `src/market_sim/data/floor_mechanisms.py:130-187`
(`MECH_ABLATION_KEPT`, `EXTRA_ZERO_FORCING_FIELDS`,
`assert_ablation_coverage`, `zero_forcing_field_overrides`);
`scripts/run_calibration_full.py:5340-5350, 5759-5800` (CLI + `ablation_of`);
`scripts/audit_keepers.py:106-137, 213-252, 493-501` (grandfather list + E9).

### 2.2 The DOF ledger (degrees-of-freedom ledger, audit D-12)

The **DOF ledger** is the `free_parameters` block written into a bundle's
`calibration_attestation.json` (schema **`dof-ledger/v1`**): an explicit
enumeration of every free parameter the run depends on, with its
identification source.

- **Builder:** `scripts/build_dof_ledger.py <bundle> --iso <ISO>` (or
  `--all-keepers`; `--check` verifies currency).
- **Entry fields:** `{ name, where, identification, lineage_solves, value?,
  source?, root_cause? }`.
- **Identification classes:** `published` (a published market/physical
  quantity) | `measured-physical` (frozen derive script over measured data,
  CLAUDE.md rule 23) | `residual` (moved a backcast residual — sanctioned only
  inside the rule-1 offer-curve scope).
- **A `residual` entry must carry a non-empty `root_cause`** — the builder
  raises otherwise. A residual that can only be closed by a tuned value is an
  open root-cause issue, not a parameter.
- **Enforcement — audit_keepers E8:** FAILs a keeper whose attestation has no
  `free_parameters` section or whose any residual entry lacks a root cause.
  E8 is unconditional (every keeper already carried a ledger when it landed).

Source: `scripts/build_dof_ledger.py:1-10, 118-144, 802` (contract, residual
check, schema tag); `scripts/audit_keepers.py:47-48, 449-491` (E8).

---

## 3. The holdout / validity-testing program

### 3.1 Three tiers (CLAUDE.md rule 22, as amended 2026-07-07)

| Tier | Years | Discipline |
|---|---|---|
| **Train / calibration** | **2023–2025** | The ONLY years ever tuned against. Every keeper is built and scored here, all three years in one bundle (rule 16). |
| **Validation holdout** | **2022**, extensible backward as a ladder (2022 → 2020–2022 → earlier as data lands and is authorized) | **Iterable.** Unlocked by the ISO's calibration-complete marker; a miss MAY send you back to re-tune 2023–2025 and re-solve — that is its purpose (model selection). Because it is iterated against, a 2022 number is **model-selection evidence, never a certified out-of-sample skill number**, and must never be quoted as one. |
| **Locked test** | **2019 and H1-2026** | **Touch once, ever.** Scored exactly once per ISO with the frozen keeper config; the result is recorded whatever it is. No calibration change may respond to a locked-test result without designating a new never-touched year as its replacement. 2019 is the clean-regime test; H1-2026 the forward-edge test. |

**Operational sequence** ("first the 2022 validation, then the 2019 locked
test"): declaring an ISO calibration-complete — adding its marker to
`frontend/data/backcast/calibration-complete.json` — unlocks holdout solves
for that ISO. You first iterate the 2022 validation: solve the frozen keeper
on 2022, score it, and if it misses you may go back, re-tune 2023–2025, and
repeat. Only when satisfied do you fire the **one-shot** 2019 + H1-2026 locked
test: solve the frozen config once, record the number, and never let it
re-enter tuning. 2019 is the honest out-of-sample number precisely because —
unlike 2022 — it is never iterated against.

The **crossover window** (2024–H1-2026 scored in both backcast and forecast
modes against the same actuals) is a policy concept in rule 22 — see §4 for
its implementation status.

### 3.2 Enforcement — what is machine-checked and what is discipline

The in-sample window `{2023, 2024, 2025}` is a hard-coded frozenset in
**three parallel places**, kept as separate stdlib literals by repo convention
with a parity test asserting they agree:

- `scripts/run_calibration_full.py:5217` (`HOLDOUT_CALIBRATION_YEARS`),
- `scripts/audit_keepers.py:185` (`CALIBRATION_YEARS`),
- `scripts/legitimacy_diagnostics.py:319` (`D6_CALIBRATION_YEARS`).

**Solve gate (CLI):** `enforce_holdout_year_gate`
(`run_calibration_full.py:5221`) hard-fails any `--year` outside the window
unless **both** `--holdout-authorized` is passed **and** the target ISO
carries a marker in `calibration-complete.json` — the marker is what turns a
holdout year into an authorized one-shot score, never the flag alone.

**Score/registration gate (CI):** the `quarantine-gates` job
(`.github/workflows/ci.yml:82`) runs `audit_keepers.py --check` (E1–E9 + the
H1 holdout-quarantine check) and `legitimacy_diagnostics.py --keepers` (D-6 +
D-9 + the D-2 recompute-vs-committed staleness check), failing any registered
bundle whose solve years breach the window for an ISO without a marker.

**The code enforces one binary** — year ∈ {2023, 2024, 2025} vs not. The
validation/locked *distinction* is **discipline, not machine-enforced**: the
CI gate is deliberately tier-agnostic, so a locked-test year re-solved after
its one-shot would be a governance breach, not a CI failure.

**Current state:** only **NEISO** carries a complete marker (declared
2026-07-07). Its 2019 + H1-2026 locked-test one-shot was scored **once** with
the then-frozen `neiso-53` config and **stands** — it was deliberately not
re-scored when the train-tier keeper was later promoted (see §5's naming
caution). The other five ISOs remain fully quarantined for holdout solving.

**Data intake is deliberately ungated:** raw data is on disk 2018 → H1-2026.
Intake for any out-of-training year is allowed under explicit, session-logged
owner authorization, validated **no-LP only** (byte-identity /
loader-resolvability checks — never a dispatch solve); each intake is recorded
in the `intake_log` of `calibration-complete.json`. Only *solve, score, and
dashboard registration* are quarantined.

**Known gap:** `scripts/run_calibration.py` (the non-`_full` script) has
**no** year gate. Any claim that "the solve entry points are gated" should
carry this asterisk.

Source: `scripts/run_calibration_full.py:5210-5267`;
`scripts/audit_keepers.py:181-210`;
`scripts/legitimacy_diagnostics.py:313-320`; `.github/workflows/ci.yml:82-115`;
`frontend/data/backcast/calibration-complete.json` (marker + intake_log);
`docs/handoffs/holdout-policy-memo-2026-07.md`.

### 3.3 Forecast-side validation (separate from the dispatch holdout tiers)

- **Capacity hindcast** — `scripts/run_capacity_hindcast.py` (with
  `score_capacity_hindcast.py`, `build_capacity_actuals.py`,
  `register_hindcast.py`): initialize the fleet at a 2020 vintage and run the
  capacity-evolution loop forward, solving `{2021, 2023, 2024, 2025}` only
  (`ALLOWED_SOLVE_YEARS`) — 2021 is solved to seed the price/margin signal but
  not scored, and **2022 is a bridge: evolved but never solved, its data never
  read** (rule 22). Run for **ERCOT and PJM**, in both fuel variants
  (realized-fuel and as-known/AEO2021). Results are diagnostic — registered
  under `results/hindcast/` + `frontend/data/hindcast/`, outside the backcast
  registry — and the current runs are documented bad-misses (e.g. ERCOT builds
  ~0 GW solar vs ~25 GW actual), which is the point: they measure the
  capacity-evolution machinery honestly rather than certifying it.
- **Forecast invariants** — `scripts/check_forecast_invariants.py`: I1–I14
  single-run invariants over one scenario cache plus P1–P3 paired-run
  invariants (two scenarios differing in one driver);
  `.github/workflows/forecast-invariants.yml`,
  `tests/test_forecast_invariants.py`.
- **D-7 statistical-mode gap + D-8 frozen-coefficient stability** — the
  overlay-vs-statistical fail-count gap per keeper (reported next to each
  keeper on the status page, never gating; `statmode_d7.json`) and the
  coefficient-stability probe (`scripts/d8_coefficient_stability.py`). Both
  are computed only on 2023–2025, never on a holdout year.

Source: `scripts/run_capacity_hindcast.py:1-78` (`ALLOWED_SOLVE_YEARS`,
bridge); `frontend/data/hindcast/` (ERCOT + PJM run set);
`scripts/check_forecast_invariants.py:20-23, 228, 668`;
`scripts/build_status.py:43-46, 474-483`; `scripts/d8_coefficient_stability.py:1-12`.

---

## 4. Backcast span vs forecast span

**Implemented today:**

| Span | Years | Meaning |
|---|---|---|
| Data on disk | 2018 → H1-2026 | Raw intake coverage (per `docs/data-register-2026-07.md` Part 2 and the `intake_log`). Intake ≠ solving: most of this range is quarantined for solves (§3). |
| Scored backcast dispatch | **2023–2025 only** | The train window — plus the single authorized NEISO locked-test one-shot. Any "the backcast covers 2018–2025" framing is true of *data intake*, not of what is solved or scored. |
| Forecast horizon | **2026–2050** | `START_YEAR = 2026`, `END_YEAR = 2050`. |

**The 2024–2025 dual-mode overlap is a TARGET DESIGN, NOT IMPLEMENTED.** The
intended crossover — backcast 2018–2025 vs forecast 2024–2030, with 2024–2025
(extending to H1-2026) scored in *both* modes against the same actuals to
measure the backcast→forecast input gap — is **roadmap, not behaviour**. The
forecast horizon starts at 2026, and **no code path today scores 2024–2026
dispatch in both modes**. The closest implemented analogue is the capacity
hindcast (§3.3), which overlaps the 2023–2025 backcast years at the capacity
layer only. Any doc or site page describing the crossover must label it as a
planned design.

Source: `src/market_sim/config/constants.py:3871-3872`;
`docs/codebase-site/UPDATE-PLAN-2026-07.md` §2.4 (validated 2026-07: grepping
`crossover` in `.py` returns only unrelated coal-sigmoid code).

---

## 5. The "frontier achieved" designation

**Definition (as implemented):** an **owner-declared, purely declarative
dashboard designation** meaning: *every named admissible mechanism for the
ISO's residual caveat family has been tried on record, and what remains is
either inadmissible to close (residual-fitting, CLAUDE.md rule 26) or blocked
on data that does not exist publicly.* It is **never gating and never touches
the verdict**: `build_status.py` attaches `verdict["frontier"]` *after*
`determine()` runs, purely for rendering on the Calibration Status page (badge
+ note).

- **Data payload:** the top-level `"frontier"` map in
  `frontend/data/backcast/keepers.json` — `{declared, note}` per ISO.
  Current holders: **NEISO and NYISO**, both declared 2026-07-11.
- **Rendering:** `docs/codebase-site/calibration-status.html` (card badge,
  detail badge, note block); style `.cs-badge.det-frontier` in
  `docs/codebase-site/css/bc-pages.css`.

**Distinct from the calibration-complete marker** — the two are frequently
conflated and must not be:

| | `calibration-complete.json` `complete` marker | `keepers.json` `frontier` map |
|---|---|---|
| Purpose | **Gating** — authorizes the rule-22 holdout solves (2022 validation, then the locked-test one-shot) | **Declarative label only** — "the admissible mechanism space for the residual is exhausted" |
| Enforced by | CI `quarantine-gates` + `run_calibration_full.py` hard-fail | Nothing (pure rendering; never feeds the verdict) |
| Current holders | NEISO only | NEISO + NYISO |

NYISO has a frontier designation but **no** complete marker: frontier does
**not** imply holdout authorization, and complete does not imply frontier.

**Why NEISO and NYISO:** both drove every hard/volume criterion into band;
their entire remaining residual is the **C3c price scarcity tail**, gated by
reserve-requirement dynamics that are either unimplemented by the real ISO or
would need new measured identification — closing them in-model would be
rule-26 residual-fitting.

- **NEISO:** four named mechanisms tried on record — the winter fuel-security
  stack (adopted, dormant), in-LP reserve co-optimization (the keeper
  mechanism, dormant at static requirements), measured dynamic reserve
  requirements (engages 1 of 12 2025 tail hours), and the measured fast-start
  DA offer surface (dormant — the real tail forms while the model still
  carries several GW of cheaper non-fast-start headroom, so no repricing of
  the fast-start band reaches it). Further C3c work needs a new measured
  identification (its own charter); C2 additionally waits on the final 2025
  EIA-923 vintage. (`docs/handoffs/neiso-limb-b-offer-surface-2026-07.md` §5.)
- **NYISO:** the deep >$300 tail's two candidate reserve levers are chased to
  ground — the largest-contingency requirement formula is already in the model
  as the measured NYCA families, and the ORDC/RCPF stack is verified complete
  and SOM-grounded. The sole remaining gap is the net-load
  forecast-uncertainty reserve increment (IMM Recommendation 2021-1), which
  NYISO itself has **not implemented** and which has no published formula —
  adding it would be residual-fitting (rule 26). No admissible mechanism
  exists today. (`docs/calibration-log.md`, 2026-07-11 nyiso-61 follow-up.)

> **Caution — "frontier" is overloaded, and NEISO's run ids diverge.** The
> calibration logs use "frontier" informally all over (e.g. "the reserve-
> scarcity frontier"); only the `keepers.json` `frontier` map is the **formal
> designation**. And for NEISO, three *different* runs are involved: the
> current keeper carrying the frontier note is
> `2026-07-09-neiso-56-reserve-coopt` (also the `keepers.json` NEISO pointer),
> while the complete-*marker* keeper is `2026-07-08-neiso-54-steamgas-ct` and
> the locked-test one-shot was scored on
> `2026-07-07-neiso53-winter-fuelsec-coldsnap`'s frozen config (recorded in
> the marker; the one-shot stands and was not re-scored for neiso-54). Do not
> assume these ids align.

Source: `scripts/build_status.py:458-472`;
`frontend/data/backcast/keepers.json` (`frontier` map + per-ISO pointers);
`frontend/data/backcast/calibration-complete.json` (`complete.NEISO`,
`locked_test_scored_on`, `locked_test_note`).
