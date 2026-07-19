# Capacity-cost-grounding — new-build cost audit, benchmark intake & envelope (2026-07-19)

**Session.** Owner ask: deep review of new-build capacity costs in the
capacity-expansion component; ground every resource's cost in respected
third-party sources; build low/mid/high ranges off published costs where they
differ; survey how commercial-grade capacity-expansion models source these;
audit what already exists (FF workstream) and fill the gaps; methodology doc
with explicit citations and links; PDFs downloaded and converted to markdown
for QA/QC. Branch `claude/capacity-pricing-review-x3qn9s`.

**The standing deliverable is `docs/new-build-cost-methodology-2026-07.md`** —
methodology, per-tech grounding tables, the commercial-model survey, the delta
ledger, gaps. This handoff records the session audit trail and verification.

---

## 1. Audit of the existing state (what FF already covered)

- **FF-1E (verified-pass, ledger turn 22/25)** had already derivation-locked
  `NEW_ENTRY_COSTS` capex/FOM (7 entry techs) and `CCUS_PARAMS` onto the
  committed NREL ATB 2024 extract, with `TECH_COST_MULTIPLIERS` low/high as
  ATB's internal Advanced/Conservative ratios, all test-asserted
  (`test_atb_entry_cost_consistency.py`). Net-CONE / demand-curve capacity
  prices were already ISO-published auction parameters (out of scope here).
- **Gaps found** (none chartered in an open FF lane; FF-1E itself flagged two):
  1. `STORAGE_TECHS` li-ion was hand-set ($1,140/kW 4-hr, "was 1380" comment
     history) with decorative "NREL ATB 2024 / BNEF 2025" labels — the
     committed ATB battery rows (2-10 hr) were on disk but never read.
  2. `OFFSHORE_WIND_PARAMS` sat below every published fixed-bottom point
     (FF-1E's own flagged follow-up).
  3. `GEOTHERMAL_PARAMS` EGS: "NREL ATB 2024" label decorative (ATB EGS
     classes absent from the extract), FOM 0.0 indefensible.
  4. `HYDROGEN_TURBINE_PARAMS`: decorative citations (ATB has no H2 class).
  5. Single-source anchoring: no cross-source triangulation, no literature
     envelope; ATB's internal near-year case spread is degenerate for mature
     techs (gas_ct multipliers literally 1.0/1.0 — an inert PB-1 lever).
  6. `docs/parameter-citations.md` stale vs FF-1E (pre-FF-1E values still
     listed).
- **ATB currency finding:** ATB 2024 v3.0.0 is the **final ATB edition** — no
  2025/2026 edition exists (OEDI listing ends at `csv/2024/`; the ATB site,
  now published by the renamed National Laboratory of the Rockies, still
  headlines 2024; `nrel.gov` itself no longer resolves from this
  environment). The FF-1E pin is therefore *current*; newer market information
  enters via the benchmark envelope instead of an edition bump.

## 2. What was built

See the methodology doc §3-4 and CHANGELOG 2026-07-19. Summary:
`data/raw/new-build-cost-benchmarks/` (5 sources downloaded → markdown-
converted → QA'd → transcribed with page refs; sha256-pinned fetch script);
ATB extract extended with the 4 EGS classes (append parts 11-12, FF-1E parts
byte-untouched; OEDI source's float serialization drifted 9/3,162 rows at
1 ulp since FF-1E — values verified identical at rtol 1e-12, attested bytes
kept); `derive_cost_benchmark_envelope.py` + `test_cost_benchmark_envelope.py`
derivation-lock the envelope multipliers, li-ion storage, offshore, EGS FOM,
and H2 costs; constants updated per the delta ledger; parameter registry
regenerated (clears the stale FF-1E rows); data register + READMEs updated.

## 3. Scope guard (rules 13/23 compliance)

Every changed number is a source-driven derivation from committed raw data or
a documented published ratio — none is residual-tuned. The entry screens are
forecast-only (`runner.py` gates evolution on `mode=="forecast"`), so no
backcast keeper changes. The PB-1 mid path is 1.0 by construction → default
forecast configs see the level changes (storage/offshore/EGS-FOM/H2) but no
multiplier change. `verified=0` benchmark rows (DOE Liftoff, PNNL — primaries
unreachable from this environment) never enforce the envelope (test-asserted)
and are flagged for browser re-verification, same convention as FF-1E §4.2.

## 4. Verification record

- **Consistency tests:** `test_cost_benchmark_envelope.py` (12 new) +
  `test_atb_entry_cost_consistency.py` (re-pointed multiplier test to
  bracketing; NEW_ENTRY_COSTS/CCUS equality untouched) — 19 passed.
- **Affected suites:** `test_storage.py` + `test_capacity.py` +
  `test_emerging_tech.py` 323 passed; `test_config.py` + `test_uncertainty.py`
  64 passed. `test_matrix.py` 3 failures **pre-existing** (missing gitignored
  `data/clean/confirmed-retirements` in this environment; identical on the
  base tree with this session's changes stashed).
- **Backcast byte-identity (NEISO 2024, 168 h, `run_calibration.py`):**
  PROVEN — the full diagnostics report (zonal prices, class volumes, duals,
  every metric line) is identical between the session's `constants.py` and
  the base tree's (git-stash A/B, same command, in-memory solve — no result
  cache in the loop). The only differing lines are the fleet-cache
  rebuilt-vs-loaded INFO line and wall-clock timings. Confirms the structural
  gate: every changed constant is consumed only by forecast-mode capacity
  evolution / entry screens.
- **Forecast smoke (NEISO 2026-2028, T0 convention,
  `run_full_horizon.py`):** result in §4a below.

### 4a. T0 smoke result (final rebased tree, 2026-07-19)

3/3 years solved (median 81 s/yr, peak RSS 3.3 GB). Invariants: the **identical
pre-existing trio** FF-1E's smoke documented in this degraded-data env, same
numbers — I4 (2028 coal accounting 54.0 MW), I7 (2026 accredited firm 27,171 <
28,797 MW requirement), I12 (2026 reserve margin 9.2%) — all three are
base-year artifacts (2026 has zero entry deltas, so that fleet is identical
before/after any cost change; the env lacks the NEISO zonal-load file and
reconciles two corrupt summer-capacity plants). All physics invariants green
(I1 energy balance, I2 no-NaN, I3 unserved, I5 no retire-and-reenter, I8
planned-additions gating, I9 storage, I10 RPS dual, I11 one-pass, I13 cobweb,
I14 price sanity). Entry ledger on the new costs: 2027 decides gas_ct
1,064.9 + gas_cc 1,000 + solar 2,000 + wind 1,000 MW (VRE arrives with the
FF-2A COD lag); 2028 executes the 3,000 MW CCS-retrofit cap displacing
unabated gas_cc, coal −54 MW, wind 1,000 MW decided. No storage entry —
consistent with the all-in ATB storage basis (the prior $1,140/kW EPC-scope
number was the outlier vs S&L/AEO26/Brattle all-in bases).

## 4b. Collateral main-bug fix riding this branch: runner.py `UNSET` NameError

The T0 forecast smoke exposed a **latent main breakage unrelated to costs**:
`runner.py` line ~1416 references the `UNSET` sentinel (miso-76 B,
`2ad50aa`, merged 2026-07-19 05:10Z) without importing it, so **every
forecast-mode run on main dies with `NameError: name 'UNSET' is not defined`**
(backcasts don't traverse `run_scenario_iso`, which is why calibration CI
missed it). One-line fix on this branch: add `UNSET` to the
`market_sim.pipeline` import block. Verified: the NEISO 2026-2028 smoke runs
to completion with the fix and reproduces the NameError without it (also
reproduced on clean origin/main).

## 4c. Parameter-registry regen: executed locally, push deferred

`generate_parameter_registry.py --check` was run against the final tree (also
clears the stale pre-FF-1E rows), but the regenerated pair
(`docs/parameter-citations.md` + `frontend/data/parameters.json`, 1.5 MB) is
**not pushed on this branch**: the session's API push path carries file
content inline and the 1.5 MB registry JSON exceeds a safe single-call
payload. This is safe to defer because this session adds **no new top-level
constants** (only values within existing dicts), so
`scripts/validate_parameters.py` stays green against main's registry —
verified on the final tree. Registry catch-up is an established standalone
chore (same-day precedent: PR #2577 / commit `55b4ea0`, a dedicated
registry-reconcile session); the next such pass picks these values up by
construction (the generator refreshes values from code).

## 4d. Transport state — constants.py + CHANGELOG land via a committed patch

A fast-moving `main` partially merged this work (PR #2587: benchmark data +
derive script + tests + the `runner.py` UNSET fix), then a later session
changed `constants.py` concurrently (+80/−11 in the reserve-margin /
adequacy-DR region, disjoint from every cost region this session edits). Net
effect and resolution:

- **Everything except `constants.py` and `CHANGELOG.md` lands directly via the
  `push_files` API** (all ≤40 KB): the ATB EGS extract (`part11`/`part12` +
  `fetch_nrel_atb.py` + `nrel-atb/README.md`), the methodology doc, this
  handoff, the data-register rows.
- **`constants.py` (7,604 lines / ~350 KB after the 3-way merge) and
  `CHANGELOG.md` (~300 KB) exceed what a single `push_files` call can carry**
  — the same hard limit the repo's FF-2B commit (`1450e2c`, same day)
  documented ("200-345 KB source files exceed reliable reproduction"); a
  delegated push subagent confirmed it stalls before landing the file, and
  `git push` is repo-forbidden (413). They are therefore shipped as a
  **mechanical, verified patch**:
  `docs/handoffs/patches/capacity-cost-constants-changelog.patch`.
- The patch is `git diff origin/main → (3-way-merged constants + CHANGELOG)`.
  **Verified**: applies cleanly onto a pristine `origin/main` checkout and
  reproduces the merged files byte-for-byte; the merged tree passes all 19
  cost tests (`test_cost_benchmark_envelope.py` +
  `test_atb_entry_cost_consistency.py`). The cost edits are textually disjoint
  from main's concurrent constants change, so the merge is clean, not forced.

**To complete (one command after the branch merges, or applied by any
large-file-capable mechanism):**
```
git apply docs/handoffs/patches/capacity-cost-constants-changelog.patch
```
Until `constants.py` lands, **main CI is red**: the merged tests assert the new
constant values and read the EGS rows. The EGS rows land via API in this
branch; the constant values land via the patch. (Alternative if the patch
route is declined: revert the cost-test additions from `main` to green it, and
re-land the whole set when a large-file transport is available — but the patch
is the low-risk path and is byte-verified.)

## 5. Follow-ups (owner-visible)

1. Regional capital-cost multipliers (AEO2026 EMM Table 4 now on disk) —
   wiring would align with EIA/IPM/ReEDS practice; owner call.
2. Browser re-verification of the `verified=0` primaries (DOE Liftoff
   next-gen-geothermal & LDES; PNNL-33283).
3. Storage capex PB lever (envelope published, not wired).
4. Per-tech WACC stays the FF-2D gate decision (unchanged).
