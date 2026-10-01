> Status: ACTIVE — the DOCS-B execution checklist for finalizing `model-methodology-spec.md`.

# Methodology-spec finalization audit — 2026-08

**Lane:** DOCS-A (Wave 1, `docs/model-audit-release-plan-2026-08.md` §3/WS4 + §7.4).
**Head audited:** `origin/main` @ `ce779f9` (2026-08-16). Every P1 finding and
every count below was re-verified at this head; main moved five times during the
session and no cited surface changed across those moves.
**Subject:** [`model-methodology-spec.md`](../../model-methodology-spec.md) — 1,251 lines, read end to end.
**Executor:** DOCS-B, after gate **G2**. The spec is **frozen to DOCS-A** this
session — nothing below has been applied.

**What "finalized" means here.** The spec stops being a *build specification with
as-built patches* and becomes a *methodology reference that describes the shipped
model*. Concretely: no Phase-0 build-agent instructions, no performance targets
the model has never met, no default described that is not the code's default, no
citation that no longer resolves, no rule cited by an ordinal that can drift, and
a delegation boundary that is stated once and honoured.

---

## 0. How to execute this checklist

**Binding constraints on DOCS-B.**

- **`[R-PUSH]` applies.** The spec is ~148 KB / 1,251 lines. **Never
  bulk-rewrite it from regenerated content.** Edit in place, push exact bytes,
  and verify the blob after push.
- **Code is the source of truth.** The spec wins only on genuine *methodological*
  ambiguity — never on a default, a flag name, a file path, or a number.
- **Do not re-absorb the delegated documents.** The calibration/validation
  regime stays in [`../calibration-and-validation-methodology.md`](../calibration-and-validation-methodology.md)
  and the two rubrics. See [§6](#6-what-stays-delegated--do-not-re-absorb).
- **Cite rules by stable `[R-*]` ID**, never by ordinal.
- Every claim re-verified below carries the command or file:line that verified
  it. Re-verify at DOCS-B execution time — main moves.

**Priority classes used in the tables:**

| Class | Meaning |
|---|---|
| **P1 — wrong** | The spec states something the code contradicts. A reader acting on it is misled. Fix first. |
| **P2 — retire** | Phase-0 build-agent content that should not survive finalization. |
| **P3 — stale ref** | Citation/path/number that no longer resolves or no longer holds. Mechanical. |
| **P4 — gap** | A shipped mechanism the spec does not describe at all. |
| **P5 — hygiene** | Structure, numbering, citation style. |

**Suggested execution order:** §1 (P1) → §3 (P2) → §2 (P4) → §4 (P3) → §5 (P5).
The P1 corrections are the ones that change what a reader believes.

---

## 1. P1 — claims the code contradicts

These are the findings that make the current spec actively misleading. All five
were verified by executing the code, not by reading adjacent prose.

### 1.1 §5.2 — coal retirement threshold is stated as 1 year; the code ships 3

The spec states it **twice**:

- L770: "**Coal:** 1 consecutive loss year (faster exit — reflects regulatory risk and carbon liability)"
- L782: "`retirement_years_{coal,gas_ct,gas_cc}` = 1/2/3 … **The defaults above are the as-built values.**"

Verified defaults:

| Field | Spec | Code |
|---|---:|---:|
| `retirement_years_coal` | 1 | **3** |
| `retirement_years_gas_ct` | 2 | 2 |
| `retirement_years_gas_cc` | 3 | 3 |
<!-- verified: ScenarioConfig().retirement_years_coal == 3; src/market_sim/config/scenarios.py:2167 "retirement_years_coal: int = 3  # coal retires after 3 consecutive" -->

**This was already caught and corrected in `CLAUDE.md` and never propagated
here.** CLAUDE.md carries the correction verbatim: *"Corrected 2026-08-02 by
FFR-3B: this read 'coal=1yr', but `scenarios.py` ships `retirement_years_coal:
int = 3`, identified under rule 23 `[R-FROZEN-DERIVE]` to the EIA-860
announced-to-deactivation capacity-weighted / ≥300 MW median of 3 yr. Code is the
source of truth."*
<!-- CLAUDE.md:388 -->

**DOCS-B action.** Correct both sites to 3/2/3, and carry the *identification*
(EIA-860 announced-to-deactivation median) — the number is derived, not chosen,
and the derivation is the part worth keeping. Also drop the now-false rationale
clause "faster exit — reflects regulatory risk and carbon liability"; that
pressure is carried by the **FOM multiplier** (coal 1.3×), which the spec already
states correctly, not by the loss-year count.

### 1.2 §5.2 describes a non-default code path — `retirement_rule` is absent entirely

`ScenarioConfig.retirement_rule` defaults to **`"pipeline"`**; the alternative is
`"legacy"`.
<!-- src/market_sim/config/scenarios.py:2208 `retirement_rule: str = "pipeline"  # "legacy" | "pipeline" (FF-1A, owner…` ; verified ScenarioConfig().retirement_rule == "pipeline" -->

The spec mentions **neither** `retirement_rule` nor `retirement_execution_lag_*`
anywhere in 1,251 lines.
<!-- verified: grep -c "retirement_rule" model-methodology-spec.md == 0; grep -c "retirement_execution_lag" == 0 -->

CLAUDE.md is explicit that the per-fuel thresholds §5.2 is built around **apply
to the legacy rule only**: *"Per-fuel thresholds are `ScenarioConfig` fields, not
hardcoded, and apply to the **legacy** rule only (`retirement_rule="legacy"`;
under the pipeline rule the decision is uniform and the per-fuel physics lives in
`retirement_execution_lag_*`)."*
<!-- CLAUDE.md:388 -->

So §5.2 — the spec's entire economic-retirement section — currently documents
the **non-default** branch as if it were the model's behaviour.

**This is the single largest methodology gap in the document.** It is also the
reason §1.1's number matters less than it looks: under the default rule the
per-fuel loss-year counts are not the operative mechanism at all.

**DOCS-B action.** Restructure §5.2 around the two rules:

1. State `retirement_rule` and its default (`"pipeline"`) at the top of §5.2.
2. Describe the **pipeline** rule as the default path: uniform decision, per-fuel
   physics carried by `retirement_execution_lag_*`.
3. Keep the per-fuel-threshold description explicitly scoped to
   `retirement_rule="legacy"`.
4. Read `model/capacity_evolution/` before writing — do not infer the pipeline
   rule's semantics from CLAUDE.md's one-sentence summary.
5. Note the FF-1A owner decision that flipped the default, with its date.

**Related, already-observed fallout.** The FF-1A default flip is what broke
`test_ercot_thermal_as_endogenous::TestScreenMutualExclusion` — a probe calling
the screen without `year` and reading legacy loss counters. DEBUG-A fixed it by
pinning `retirement_rule="legacy"` in the probe config. That the *tests* needed
this pin and the *spec* never mentioned the field is the shape of the gap.
<!-- docs/handoffs/debug-sweep-2026-08.md, Seed-7 detail table row 1 -->

### 1.3 §6.2 — performance targets the model has never met, by ~1.5 orders of magnitude

| Operation | Spec target | Measured ground truth |
|---|---:|---:|
| LP matrix construction (1 ISO, 1 yr) | < 1 s | — |
| LP solve (HiGHS, 1 ISO-yr, 8760 h) | < 5 s | **P0 alone ≈ 133–209 s** |
| Full scenario-year | < 10 s | **ERCOT 183–272 s; MISO 292–339 s** |
| Single scenario × 1 ISO × 25 years | < 5 min | ≈ **1.3–2.4 hours** at those rates |
| Memory per LP solve | < 2 GB | **~12.7–14.5 GB** on a per-plant ISO |
| 20 scenarios × 2 ISOs on 8 cores | < 30 min | not achievable under `[R-PARALLEL]`'s ≤2-worker cap |
<!-- docs/handoffs/wallclock-baseline-2026-07.md:22-23 (ERCOT 2023 271.7 s / 2024 183.1 s), :26 (solve share 74–83 %), :35,:37 (MISO 339.2 / 292.6 s); memory: docs/PRECOMMIT-ercot192-…-2026-08-12.md:260 (12.71 GB RSS), docs/multi-iso/pjm-reserve-ordc.md Phase-2 EMPIRICAL (13.9–14.5 GB) -->

The "< 2 GB per LP solve" line is the most dangerous: `[R-PARALLEL]`'s ≤2-worker
cap exists *precisely because* a solve uses several GB. A reader sizing a machine
from §6.2 will under-provision by ~7×.

**DOCS-B action.** **Delete the §6.2 target table.** Replace it with a pointer to
`docs/handoffs/wallclock-baseline-2026-07.md` (per-phase measured ground truth)
and a one-paragraph statement of the durable structural facts: the cold P0 solve
is 74–83 % of a year; the obvious solver levers (IPM+crossover, thread scaling,
HiGHS parallel/PAMI, presolve-on) are benched and **rejected on record**; warm-start
levers are shipped. Do **not** re-pin fresh numbers into the spec — measured
wallclock belongs in the baseline doc, which is maintained; a number in the spec
rots and this table is the proof.

### 1.4 CAISO's topology is stated as 4 zones; the code ships 6

Both the Scope paragraph (L5) and the §1.3 topology bullet (L180) say CAISO is
*"3 in-state zones (NP15, ZP26, SP15) split on Path 15 / Path 26, **plus** a WECC
import/export node"* — four columns in the zonal balance. The shipped topology
has **six**:

| | Spec | Code |
|---|---|---|
| CAISO zones | NP15, ZP26, SP15 (+ `WECC_import`) = **4** | NP15, ZP26, **LA_BASIN**, **SDGE**, **SP15_rest** (+ `WECC_import`) = **6** |
<!-- verified at runtime: get_iso_config("CAISO").zones -> 6 entries with load shares NP15 .4079, ZP26 .0536, LA_BASIN .374, SDGE .091, SP15_rest .0735, WECC_import 0.0 -->

SP15 was split three ways. That is a **topology refinement the spec never
absorbed**, not a typo: the zonal energy balance, the price vector, and every
"SP15" claim downstream all change shape. `CLAUDE.md` carries the same stale
"CAISO (3 zones + WECC import node)" string.

Every other ISO's stated topology checks out — ERCOT 7 (6 carry load), PJM 8,
MISO 6, NYISO 5, NEISO 4 load zones + HQ import node.
<!-- all six verified at runtime, 2026-08-16 -->

**DOCS-B action.** Correct L5 and L180 to the six-zone shape, name the three
SP15 children, and state what the split is *for* (read `config/iso_configs.py`'s
CAISO block — do not infer it from the zone names). Flag the matching CLAUDE.md
string to whoever owns that file; it is out of this checklist's scope.

**Provenance.** Independently surfaced as row **D2** of AUDIT-A's gap register
(`docs/audit/third-party-audit-2026-08.md` §8), which routes it to this memo.
D2's phrasing — "CAISO/MISO zone counts" — overstates by one: **MISO's stated 6
is correct**; only CAISO diverges.

### 1.5 §6.1 and §4.4 describe a parallelism model that violates `[R-PARALLEL]`

§6.1's illustrative snippet is `ProcessPoolExecutor(max_workers=N_CORES)` over
`(config, iso)` pairs. That is exactly the uncapped `cpu_count() - 1` default
that was **removed from `run_sweep` as a rule 12 `[R-PARALLEL]` violation**: a forecast member on
a per-plant ISO uses several GB, so more than ~2 concurrent members OOMs.
<!-- src/market_sim/pipeline/members.py:1-39 module docstring names run_sweep's uncapped default as the violation; :61 DEFAULT_MEMBER_CAP = 2 -->

The snippet also calls `load_base_fleet` / `assemble_inputs` / `save_parquet` —
none of which are the shipped names.

**DOCS-B action.** Either delete the snippet (preferred — §6.1's prose statement
"independent work units are `(scenario_config, iso)` pairs; within each unit,
years run sequentially" is correct and sufficient) or rewrite it to name
`pipeline.members.run_pairs` and state the cap. If it stays, it must show
`DEFAULT_MEMBER_CAP = 2`, cite `[R-PARALLEL]`, and note that an explicit
`workers` is honoured as given on `sweep`/`ensemble` and hard-capped only on
`matrix`.

---

## 2. P4 — shipped mechanisms the spec does not describe

Gaps, not errors. Each is a mechanism a reader would need and would not find.

| # | Gap | Where it belongs | Evidence |
|---|---|---|---|
| 2.1 | **The §2.1b solve-window cap.** Every `market-sim` subcommand refuses a forecast window > 5 solve-years without `--full-solve-authorized`; backcast configs are exempt (governed by `[R-HOLDOUT]`). §4.2's `python -m market_sim run --config my_scenario.yaml` is presented as unconditional. | §4.2, and a cross-reference from §5.1's year loop | `src/market_sim/config/schedulable.py:46,121,151`; `runner.py:3792` attaches the flag to all four subparsers |
| 2.2 | **The `matrix` subcommand and cases-mode expansion.** §4.3 documents only cartesian `sweep:`. `SweepDefinition` has two mutually-exclusive modes and the named-`cases:` mode — which preserves case identity for labelled output — is the one the 13-case AEO/IPM matrix uses. | §4.3 | `src/market_sim/config/sweeps.py:29-67`; `configs/scenario_matrix.yaml` (13 cases, verified) |
| 2.2b | **`SweepDefinition.mode` is a dead field.** §4.3 says the generator "supports `mode: factorial` (default), `mode: lhs` (Latin hypercube — future), or `mode: list`". The dataclass declares `mode: str = "factorial"` but **nothing ever reads it** — expansion gates purely on which of `sweep:`/`cases:` is non-empty. So `lhs` and `list` do not exist, and even `configs/scenario_matrix.yaml`'s own `mode: cases` line is decorative. State the two real modes; delete `lhs`/`list` or mark them explicitly unimplemented; decide with the owner whether the dead field is a `[R-DELETE]` candidate. | §4.3 | `sweeps.py:57` declares it; `grep "\.mode"` over `sweeps.py` and repo-wide `sweep_def.mode` return **no read sites** |
| 2.3 | **The `_p1` cached pass file.** §4.4's cache layout shows only `year_YYYY.parquet`; the code also writes `year_YYYY_p1.parquet` when a commitment pass runs. | §4.4 | `results/cache.py:594` `get_cache_path(..., pass_label)` |
| 2.4 | **`MARKET_SIM_DATA_ROOT`.** The whole `data/`+`results/` root is relocatable by env var. Unmentioned. | §4.4 | `src/market_sim/config/paths.py:45` |
| 2.5 | **`retirement_rule` / the pipeline retirement rule.** See [§1.2](#12-52-describes-a-non-default-code-path--retirement_rule-is-absent-entirely). | §5.2 | `scenarios.py:2208` |
| 2.6 | **The real `cache_key` construction.** §4.1's snippet shows `sha256(json.dumps(asdict(self)))[:16]`. The shipped key has drop-at-default semantics over optional fields plus a registration ledger, guarded in CI by `scripts/check_cache_key_registration.py`. The tuple/list coercion repair landed in the 2026-08 debug sweep precisely because a byte-faithful YAML reload hashed to a *different key than its writer*. Cache-key byte-stability is a **frozen surface** (any key move is a declared epoch, per the FFR-9C precedent); the spec should say so. | §4.1, §4.4 | `check_cache_key_registration.py` output at `ce779f9`: *"713 ScenarioConfig fields, 166 registered in `_CACHE_KEY_OPTIONAL_FIELDS`, all resolve; 166 declared defaults all match HEAD"*; default key `603c2498bf71d21d` verified; `docs/handoffs/debug-sweep-2026-08.md` Seed-7 row 2 |
| 2.7 | **Warm-start.** Intra-year, cross-year (`MARKET_SIM_WARMSTART_XYEAR`, default **ON** on the calibration path, ~2.3× on warm years, basis-neutral) and the persisted year-1 basis are shipped and load-bearing. §6 mentions none of them. | §6 | `scripts/run_calibration.py:5730-5766`; `docs/cross-year-warmstart.md` |
| 2.8 | **Byte-identity as a methodological contract.** `capture_keeper_goldens.py` before / `regression_gate.py --mode byte` (atol=rtol=0) after, with "a golden FAIL is a finding, never grounds to regenerate" — this governs what may change about the model. It is reproducibility methodology, not tooling trivia. One paragraph, with the delegation pointer. | §7 successor (see [§3](#3-p2--phase-0-build-agent-content-to-retire)) | `docs/testing.md` "The two golden systems"; `docs/refactor-consolidation-plan-2026-07.md` §8 |

---

## 3. P2 — Phase-0 build-agent content to retire

The spec was written at Phase 0 as instructions **to an agent building the
model**. That model is built. Three surfaces are pure build-agent artifact.

### 3.1 §2.3 "Critical Performance Rules for the Build Agent" (L501–508)

Six numbered imperatives addressed to a builder ("If you find yourself writing
`for t in range(8760):`, **stop and vectorize**"), ending in item 6 — the
performance targets already condemned in [§1.3](#13-62--performance-targets-the-model-has-never-met-by-15-orders-of-magnitude).

**Disposition: RETIRE, but do not simply delete.** Items 1–5 encode two rules
that remain **binding governance**, not advice:

- `[R-VECTOR]` — no Python loops over hours in LP construction.
- `[R-SOA]` — struct-of-arrays before LP construction.

**DOCS-B action.** Replace §2.3 with a short **"Construction invariants"**
subsection stating those two as properties of the shipped builder, cited by
`[R-*]` ID, plus the pre-allocated-CSC / build-pattern-once facts as
*descriptions* rather than instructions. Delete item 6 outright. Retitle: the
words "for the Build Agent" must not survive.

### 3.2 §7 "Build Agent Instructions" (L1222–1251) — the whole section

- **§7.1 "Rules"** — ten imperatives to a builder. All ten now exist as CLAUDE.md
  governance rules with stable IDs (`[R-NO-MAGIC]`, `[R-VECTOR]`, `[R-SOA]`,
  `[R-PARQUET]`, `[R-RENEW-VAR]`, …). Keeping a second, ordinal-free copy in the
  spec is exactly the duplicate-authority failure `[R-ONE-MECH]` exists to
  prevent — and the copies have already drifted (§7.1 item 8 restates the naive
  cache-key hash of [§2.6](#2-p4--shipped-mechanisms-the-spec-does-not-describe)).
- **§7.2 "What NOT to Build"** — a *mixed* section. Half is durable model-scope
  methodology; half is Phase-0 scoping. Split it.

**DOCS-B action.**

| §7.2 line | Disposition |
|---|---|
| "No MIP … pure LP, no binary variables; the commitment layer is a heuristic screen *between* LP solves" | **KEEP** — promote to §1 (near §1.6). This is a load-bearing methodological commitment and an audit-relevant divergence from commercial practice. |
| "Prices are LP duals. Period." | **KEEP** — promote to §1.3, where the energy-balance dual is defined. `[R-DUALS]`. |
| "No representative weeks or days. Full 8760 always." | **KEEP** — promote to §1. `[R-8760]`. |
| "No convergence iteration in capacity evolution. One pass per year." | **KEEP** — already stated in §5.1; delete the duplicate. `[R-ONE-PASS]`. |
| "No inter-hour generator ramp-rate constraints" | **KEEP as a stated limitation**, with the existing parenthetical that reserve *classes* and co-optimized reserve requirements do exist while true MW/min ramp limits do not. |
| "No web framework or API server. CLI + YAML + Parquet files." | **REVISE.** Literally false as written: `tools/launcher.py` is a stdlib `http.server` web UI on port 8765. The *intent* — the model has no service layer; the interface is CLI + YAML + Parquet — is still true. Restate the intent and note the launcher as a local convenience UI that shells out to the same CLI. |
| The `~~struck-through~~` "originally listed here but since built" pair | **RETIRE the strikethrough framing.** Fold both facts into their own sections (§1.6 commitment, §1.7 outages) and drop the meta-narrative. A finalized spec describes the model; it does not narrate its own edit history. |

Then **delete §7** and renumber. If any imperative has no CLAUDE.md home, add
the rule there first — do not keep the spec as its only home.

### 3.3 The as-built note at L11 and the "two-ISO" framing

L11's *"This spec was originally written at Phase 0 as a pure-LP, two-ISO design.
The model has since grown: …"* is a patch note. Its content (commitment layer,
CAMPD binning, CCS retrofit, outage modelling, EAC credits, hydro budgets, five
more ISO topologies) is all now written up in the body.

Residue of the same two-ISO framing survives inline:

- §4.1: `iso: str = "ERCOT"  # or "CAISO"`
- §6.2: "20 scenarios × **2 ISOs** on 8 cores"

**DOCS-B action.** Delete the L11 as-built note; fix the two-ISO residue to the
six supported ISOs (`ERCOT`, `CAISO`, `MISO`, `PJM`, `NYISO`, `NEISO` — the §6.2
row is deleted anyway per [§1.3](#13-62--performance-targets-the-model-has-never-met-by-15-orders-of-magnitude)).
Keep the **Scope** paragraph at L5, which already states all six correctly.

**Sequencing note.** The as-built note is the doc's own admission that it is a
patched build spec. Removing it is the *last* edit, not the first — it is only
honest once §§1–3 of this checklist are done.

---

## 4. P3 — stale citations and references

### 4.1 Test-path citations broken by the Wave-5A tiered reorganization

Five citations name `tests/<file>.py` paths that no longer exist. All five files
were filed into the tiered layout.

| Spec line | Cited as | Actual |
|---|---|---|
| L387 | `tests/test_benchmark_basis_default.py` | `tests/scoring/test_benchmark_basis_default.py` |
| L591 | `tests/test_emission_rates.py` | `tests/unit/data/test_emission_rates.py` |
| L998 | `tests/test_capacity_area_crosswalk.py` | `tests/unit/config/test_capacity_area_crosswalk.py` |
| L999 | `tests/test_capacity_deliverability_wiring.py` | `tests/unit/data/test_capacity_deliverability_wiring.py` |
| L1097, L1158 | `tests/test_capacity_demand_curve.py` | `tests/unit/model/test_capacity_demand_curve.py` |
<!-- verified by `find tests -name "<file>"` for each, 2026-08-15 -->

### 4.2 Module citations predating the `lp/` split

`model/dispatch.py` was split into the `model/lp/` package on 2026-07-22
(layout / costs / rows / reserve_rows / bounds / model). `model/dispatch.py` is
now a **34-line facade** that aliases itself to the package.
<!-- src/market_sim/model/dispatch.py — module docstring + `sys.modules[__name__] = _lp` -->

The spec still points readers at the old location:

| Spec line | Citation |
|---|---|
| L102–103 | `build_variable_bounds(storage_soc_min=…)`, "`dispatch.py`" |
| L112 | `build_cost_vector(storage_discharge_cost=...)`, "`model/dispatch.py`" |
| L145 | `dispatch.build_constraints(link_loss)` |
| L175 | `dispatch._build_interface_rows` |
| L875 | `dispatch._build_reserve_rows` |

**These still resolve** — that is the point of the facade, and the pickle-identity
contract requires it. But as *location pointers* they send a reader to a file
containing none of the named code.

**DOCS-B action.** Repoint each to its physical home in `model/lp/` (read the
package to place each name — `bounds.py`, `costs.py`, `rows.py`,
`reserve_rows.py`, `layout.py`, `model.py`). Add one sentence where the split is
first relevant: `model/dispatch.py` remains a facade whose import path is a
**frozen surface** (pickle/module-path identity), so historical citations and
imports keep working by design.

**Related, and worth stating once:** `model/transmission.py` follows the same
alias pattern onto `model/interchange`.

### 4.3 Other citation checks

- **`data/fleet.py` → `data/fleet/` package.** L589 cites
  `src/market_sim/data/fleet.py::apply_plant_emission_rates_v2` and L809 cites
  `data/fleet.py:load_planned_additions`. `data/fleet` is a **package**
  (`models`, `arrays`, `campd_bins`, `offer_surfaces`, `floors`, `withholding`,
  `eia860`, `legacy_bins`, `assembly`). Repoint to the owning module. L585 already
  correctly cites `fleet/eia860.py::_rows_to_generators`.
- **L1129 `adjudication-2026-07-15.md`** — resolve the bare filename to its real
  path (`docs/handoffs/nyiso-neiso-capacity-pairing-adjudication-2026-07-15.md`)
  or drop it.
- **L349 `claude.md`** — lowercase, twice on one line. The file is `CLAUDE.md`.
- **Bare filenames that do resolve** (`constants.py`, `iso_configs.py`,
  `interchange_config.py`) are unambiguous in context; optionally qualify with
  `config/` for consistency. Low value, do it only if touching the line anyway.
- **Illustrative filenames** (`my_scenario.yaml`, `sweep_gas_carbon.yaml`,
  `sweep_demand_buildout.yaml`, `config.yaml`, `floor_retentions.json`) are
  fine — they are examples, not citations. Prefer replacing the sweep examples
  with the real shipped ones (`configs/scenario_matrix.yaml`, and a real
  `configs/scenarios/*.yaml`) so a reader can run them.
- **No line-number citations into source files.** The spec cites by
  `module::function`, which is the durable form. **Keep it that way** — do not
  "improve" it to `file:line` during finalization.
  <!-- verified: no file.py:NNN citations found in the spec -->

### 4.4 Numbers to re-verify against code at execution time

Not asserted wrong — **unverified by this audit**, and each is the kind of number
that drifts. Re-derive each from code or from its cited artifact before signing
off §5:

- §5.2 FOM multipliers 1.3 / 1.0 / 1.0 — *verified correct at `ce779f9`.*
- §5.5 storage duration-ELCC / saturation-derate / portfolio-dilution stack.
- §5.6 CCS retrofit constants: `ccs_retrofit_hr_penalty` 12 %, `vom_adder` $8/MWh,
  `capture_rate` 90 %, `capex_kw` ≈ $900/kW, `max_gw_per_year` 3, `min_remaining_life` 15,
  `ccs_retrofit_available_year` 2028, `ira_45q_credit_window_years` 12.
- §5.3 IRA expiry years: `ira_wind_solar_last_year` 2027,
  `ira_other_clean_last_full_year` 2028 → `ira_other_clean_phaseout_end` 2033,
  `ira_h2_45v_last_year` 2027, `ira_ccus_45q_last_year` 2032.
- §5.9 `MARKET_DESIGN` / `capacity_price_per_firm_mw_yr` per-ISO coverage and the
  CR-1 default-off state.
- §1.7 `_SUMMER_WEFOR_SHARE = 0.30`, `_CC_SHOULDER_MONTHS = {3,4,5,10,11}`.
- §3.3 per-ISO gas-offer-margin anchors (ERCOT 2.2494, PJM 3.3483, CAISO 4.7964,
  MISO 3.0492, NYISO 3.9046, NEISO 4.0763 $/MMBtu) and
  `CO2_RATE_TRAILING_WINDOW_YEARS = 2`.
- §1.2 storage tiebreaker ε = 0.001 $/MWh — `[R-EPSILON]`, should be trivially confirmable.

**Method.** Prefer executing `ScenarioConfig()` and reading the attribute over
grepping the dataclass — several of these fields have resolver indirection.

---

## 5. P5 — structure, numbering, citation style

### 5.1 Duplicate section number: **two** §1.8 headings

- L362 `### 1.8 Dispatch-Time Reliability Floor — Temperature / Net-Load Commitment`
- L385 `### 1.8 Benchmark basis — backcast scoring actuals (G-21/G-21b, all ISOs)`

Two distinct sections share the number. Any cross-reference to "§1.8" is
ambiguous, and the second is arguably misfiled: **benchmark basis is scoring, not
LP formulation.**

**DOCS-B action.** Renumber the benchmark-basis section to **§1.9**, or — better —
move it out of §1 entirely and leave a pointer, since the determination rubric
§0b already specifies it in full. See [§6](#6-what-stays-delegated--do-not-re-absorb).
Then grep the repo for `§1.8` cross-references and repoint them.
<!-- verified: both headings read exactly "### 1.8 …" at L362 and L385 -->

### 5.2 Rule citations: ~31 bare ordinals, zero `[R-*]` IDs

The spec cites CLAUDE.md rules **~31 times** and uses the stable ID form **zero**
times. Four different spellings are in play: `rule #12`, `rule 24`,
`CLAUDE.md rules 1/13/23`, `claude.md #11`.
<!-- verified: grep -o "\[R-[A-Z-]*\]" model-methodology-spec.md returns nothing; ordinal citations at L112,140,194,252,327(×3),347,349,360,377,387,393,579(×2),591,762,764,777,786(×2),796,853,880,956,959,1008,1081,1087,1120,1155 -->

Ordinals drift; IDs do not. This is a **mechanical, high-value** pass.

**Mapping table** (extracted from CLAUDE.md at `ce779f9` — re-extract at
execution time, do not trust this copy):

| # | ID | # | ID |
|---:|---|---:|---|
| 1 | `[R-STRUCT]` | 15 | `[R-DASHBOARD]` |
| 2 | `[R-VECTOR]` | 16 | `[R-ALLYEARS]` |
| 3 | `[R-RENEW-VAR]` | 17 | `[R-FLOOR-WINDOW]` |
| 4 | `[R-DUALS]` | 18 | `[R-PHYSICS]` |
| 5 | `[R-NO-MAGIC]` | 19 | `[R-ONE-MECH]` |
| 6 | `[R-SOA]` | 20 | `[R-FORCED-BUDGET]` |
| 7 | `[R-PARQUET]` | 21 | `[R-DOF]` |
| 8 | `[R-8760]` | 22 | `[R-HOLDOUT]` |
| 9 | `[R-EPSILON]` | 23 | `[R-FROZEN-DERIVE]` |
| 10 | `[R-ONE-PASS]` | 24 | `[R-REGISTRY]` |
| 11 | `[R-DOCSTRING]` | 25 | `[R-ISO-SCOPE]` |
| 12 | `[R-PARALLEL]` | 26 | `[R-DELETE]` |
| 13 | `[R-MEASURED]` | 27 | `[R-PUSH]` |
| 14 | `[R-ACCURATE]` | 28 | `[R-MECH-MATRIX]` |

**Do not do this blind.** Two traps:

1. **Some ordinals in the spec are not CLAUDE.md rules at all.** §5.8 cites
   "repo rule #1" (L956) and "rule #12" (L959) — *"preferring the published limit
   over a calibrated scalar can move the backcast (rule #12)"*. CLAUDE.md's rule
   12 is `[R-PARALLEL]` (concurrency), which cannot be the referent; this is the
   older non-negotiable / legitimacy-audit numbering. Read each citation's own
   sentence and confirm the referent before substituting. Where an ordinal
   resolves to a numbering that no longer exists, cite the governing `[R-*]` rule
   if there is one, and otherwise name the source document.
2. **`rule 13` appears 7 times** (L252, 764, 786, 880, 1087, 1120, 1155). All
   seven read consistently as `[R-MEASURED]` (measured-data admissibility /
   "never a backcast tuning channel"), so this family is the safest bulk
   substitution — but confirm L252, whose sentence is about a `__post_init__`
   forecast-only guard rather than about a measured input.

**Convention to adopt** (matches CLAUDE.md and this program's other docs):
`rule 19 [R-ONE-MECH]` on first use in a section, bare `[R-ONE-MECH]` after.

### 5.3 Line-anchored structure to check while editing

- §1.5's four sub-sections (`1.5.1`–`1.5.5`) skip nothing but are numbered
  `.1 .2 .3 .4 .5` under a heading whose own prose covers "Emerging
  Technologies" — fine, leave alone.
- The unnumbered `### Calibration & Validation — cross-reference` at L351 sits
  between §1.7 and §1.8. **Keep it unnumbered and keep it exactly where it is** —
  it is the delegation boundary marker and its position (immediately after the
  outage-modelling split, before the scoring-adjacent material) is doing work.
- Horizontal rules (`-----`) delimit top-level sections inconsistently. Low
  priority; normalize only if touching the surrounding lines.

---

## 6. What stays delegated — do NOT re-absorb

The spec already draws this boundary correctly at L351–360, and finalization
must **not** erode it. The temptation during a "finalize the methodology doc"
pass is to pull the scoring regime back in. Resist it.

| Stays in | Owns |
|---|---|
| [`calibration-and-validation-methodology.md`](../calibration-and-validation-methodology.md) | The authoritative narrative: how a backcast run is scored, gated, and declared a keeper. Holdout tiers (train / validation / locked-test), DOF ledgers, ablation twins, the calibration-frontier designation. |
| [`calibration-determination-rubric.md`](../calibration-determination-rubric.md) | The criterion-by-criterion rubric spec (C1–C8) and §0b's benchmark-basis specification. |
| [`forecast-determination-rubric.md`](../forecast-determination-rubric.md) | The forecast (FR) rubric. |
| `CLAUDE.md` | The governance rules themselves. The spec cites `[R-*]` IDs; it does not restate rule text. |
| `docs/codebase/` | What the code does, module by module. The spec states methodology; codebase pages state implementation. |
| `docs/handoffs/wallclock-baseline-2026-07.md` | Measured per-phase wallclock. See [§1.3](#13-62--performance-targets-the-model-has-never-met-by-15-orders-of-magnitude). |
| `docs/user-manual.md` | How to *run* it — install, CLI, configs, outputs, troubleshooting. |

**The one boundary this audit proposes moving** is §1.8-second (benchmark basis,
[§5.1](#51-duplicate-section-number-two-18-headings)): it is scoring-side
material that the determination rubric §0b already specifies in full. Moving it
out is *consistent* with the delegation boundary, not a violation of it. If
DOCS-B prefers to keep it in the spec, it must at minimum be renumbered and
explicitly marked as a pointer-with-summary rather than a second specification.

**Test for any candidate re-absorption:** does removing it from the delegated doc
leave that doc incomplete? If yes, it does not belong in the spec.

---

## 7. Section-by-section verdict

The checklist above, rolled up. **"OK"** means read end to end and found current —
not that every number in it was re-derived (see [§4.4](#44-numbers-to-re-verify-against-code-at-execution-time)).

| § | Title | Verdict | Actions |
|---|---|---|---|
| Header (L1–13) | Purpose / Scope / Runtime / as-built note | **P1 — Edit** | [3.3](#33-the-as-built-note-at-l11-and-the-two-iso-framing) delete the as-built note; [1.4](#14-caisos-topology-is-stated-as-4-zones-the-code-ships-6) the Scope para's CAISO zone count is WRONG (every other ISO checks out) |
| 1.1 | Decision Variables | OK | — |
| 1.2 | Objective Function | OK | ε = 0.001 confirm ([4.4](#44-numbers-to-re-verify-against-code-at-execution-time)); cite `[R-EPSILON]` |
| 1.3 | Constraints | **P1 — Edit** | [1.4](#14-caisos-topology-is-stated-as-4-zones-the-code-ships-6) CAISO six-zone topology (L180 bullet); plus [4.2](#42-module-citations-predating-the-lp-split) repointing; promote `[R-DUALS]` here per [3.2](#32-7-build-agent-instructions-l12221251--the-whole-section) |
| 1.4 | Policy Constraint Extension Point | OK | Current and dense. Ordinal→ID pass only |
| 1.5 (.1–.5) | Emerging Technologies | OK | [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) IRA expiry years |
| 1.6 | Unit Commitment — three-solve heuristic | OK | Already carries the P2-ARCHIVED and "P1 is the MAIN run" corrections. Receive the "no MIP" statement from §7.2 |
| 1.7 | Outage & Availability | OK | [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) WEFOR/shoulder constants |
| *(unnumbered)* | Calibration & Validation cross-reference | **KEEP AS IS** | [6](#6-what-stays-delegated--do-not-re-absorb) — do not renumber, do not move |
| 1.8 (first) | Dispatch-Time Reliability Floor | OK | Keeps the number |
| 1.8 (second) | Benchmark basis (G-21/G-21b) | **Renumber / relocate** | [5.1](#51-duplicate-section-number-two-18-headings), [6](#6-what-stays-delegated--do-not-re-absorb) |
| 2.1 | Matrix Structure | OK | — |
| 2.2 | Construction Algorithm (pseudocode) | **Review** | Pseudocode is labelled as such and still structurally accurate; keep, but drop imperative asides |
| 2.3 | Critical Performance Rules for the Build Agent | **RETIRE → rewrite** | [3.1](#31-23-critical-performance-rules-for-the-build-agent-l501508) |
| 3.1 | Fleet Arrays | OK | — |
| 3.2 | Marginal Cost Assembly | OK | — |
| 3.3 | Fleet Representation & Offer Curves | OK | Longest current section; [4.3](#43-other-citation-checks) `data/fleet.py`, [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) anchors |
| 4.1 | Tiered Parameter System | **Edit** | [2.6](#2-p4--shipped-mechanisms-the-spec-does-not-describe) cache_key; [3.3](#33-the-as-built-note-at-l11-and-the-two-iso-framing) two-ISO residue |
| 4.2 | Single-Run Mode | **Edit** | [2.1](#2-p4--shipped-mechanisms-the-spec-does-not-describe) §2.1b cap |
| 4.3 | Batch Sweep Mode | **Edit** | [2.2](#2-p4--shipped-mechanisms-the-spec-does-not-describe) cases mode; [2.2b](#2-p4--shipped-mechanisms-the-spec-does-not-describe) `mode:` is a dead field — `lhs`/`list` do not exist |
| 4.4 | Caching | **Edit** | [2.3](#2-p4--shipped-mechanisms-the-spec-does-not-describe) `_p1`, [2.4](#2-p4--shipped-mechanisms-the-spec-does-not-describe) `MARKET_SIM_DATA_ROOT`. Layout itself verified correct |
| 5.1 | Architecture (step order 0–7) | OK | Add the §2.1b cross-reference |
| 5.2 | Economic Retirement | **P1 — REWRITE** | [1.1](#11-52--coal-retirement-threshold-is-stated-as-1-year-the-code-ships-3), [1.2](#12-52-describes-a-non-default-code-path--retirement_rule-is-absent-entirely) |
| 5.3 | Economic New Entry | OK | [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) |
| 5.4 | Known Pipeline | OK | [4.3](#43-other-citation-checks) `data/fleet.py` |
| 5.5 | Storage New Entry | OK | [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) |
| 5.6 | CCS Retrofit Screen | OK | Carries its own W2-C redesign note; [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) constants |
| 5.7 | Hydro Energy Budgets | OK | — |
| 5.8 | Locational Capacity Deliverability | OK | [5.2](#52-rule-citations-31-bare-ordinals-zero-r--ids) trap 1 — "repo rule #1"/"rule #12" referents |
| 5.9 | Capacity-Market Revenue (CR-1) | OK | [4.4](#44-numbers-to-re-verify-against-code-at-execution-time) MARKET_DESIGN coverage |
| 6.1 | Parallel Execution | **P1 — Edit** | [1.5](#15-61-and-44-describe-a-parallelism-model-that-violates-r-parallel) |
| 6.2 | Performance Targets | **P1 — DELETE** | [1.3](#13-62--performance-targets-the-model-has-never-met-by-15-orders-of-magnitude) |
| 6.3 | Memory Management | **Edit** | Statement is correct (build/discard per year, fresh HiGHS per solve). Add the measured per-solve envelope and `[R-PARALLEL]`'s ≤2 cap; receive `[R-VECTOR]`/`[R-SOA]` context from [3.1](#31-23-critical-performance-rules-for-the-build-agent-l501508) |
| 7.1 | Build Agent Rules | **RETIRE** | [3.2](#32-7-build-agent-instructions-l12221251--the-whole-section) |
| 7.2 | What NOT to Build | **SPLIT then retire** | [3.2](#32-7-build-agent-instructions-l12221251--the-whole-section) |

---

## 8. Definition of done for DOCS-B

1. All five **P1** findings corrected; §5.2 restructured around `retirement_rule`;
   CAISO's six-zone topology stated at both L5 and L180.
2. §2.3 rewritten as construction invariants; **§7 deleted** and its durable
   content rehomed into §1/§6.
3. No occurrence of "Build Agent" anywhere in the spec.
4. No performance-target table; a pointer to the wallclock baseline instead.
5. Every `tests/` and `model/dispatch.py` citation repointed; the five test paths
   and the `data/fleet` package references resolved.
6. Zero bare-ordinal rule citations; all `rule N [R-ID]` or `[R-ID]`, each
   referent individually verified.
7. Section numbers unique; §1.8 collision resolved and cross-references repointed.
8. §4.4's numbers list re-derived from code, not from prose.
9. The delegation boundary intact — nothing re-absorbed from
   `calibration-and-validation-methodology.md` or either rubric.
10. `[R-PUSH]` honoured: edited in place, exact bytes pushed, **blob verified
    after push** (line count + hash).
11. `/sync-docs` run; `docs/README.md` L2 row for the spec still accurate.
12. CHANGELOG entry.

---

## 9. Relationship to AUDIT-A's gap register

AUDIT-A landed (#3991) while this audit was being written, and its §8 gap
register carries five **DOCS** rows. Reconciliation, so nothing falls between
the two documents:

| AUDIT-A row | Disposition here |
|---|---|
| **D1** — `calibration-and-validation-methodology.md` carries the retracted NEISO locked-test claim as live fact, plus a stale marker/frontier roster and a v2.4 header against rubric v3.2, with no correction notice. | **NOT covered here, by design.** It is a different document, and this checklist's [§6](#6-what-stays-delegated--do-not-re-absorb) exists to keep that document's content *out* of the spec. The audit itself calls it "distinct from the DOCS-A/B manual work". It is the highest-priority DOCS item in the program and needs an owner-assigned executor — flagging it rather than silently absorbing it. |
| **D2** — enumerated doc/code divergences. | **Absorbed.** Retirement coal=1 vs 3 → [§1.1](#11-52--coal-retirement-threshold-is-stated-as-1-year-the-code-ships-3). CAISO zone count → [§1.4](#14-caisos-topology-is-stated-as-4-zones-the-code-ships-6) (independently found; D2 overstates by one — MISO's 6 is correct). `dispatch.py`/`capacity.py` facades → [§4.2](#42-module-citations-predating-the-lp-split). "Three subcommands vs four" → `../user-manual.md` §10. Three-solve wording → [§9.1](#91-two-d2-items-this-checklist-deliberately-does-not-treat-as-spec-errors) below. `retirement_reserve_margin` → not a spec defect: L782 already records it as DELETED. |
| **D3** — unmarked Phase-0 build-agent content. | **Absorbed and expanded** → [§3](#3-p2--phase-0-build-agent-content-to-retire), with a per-line disposition for §7.2's mixed durable/scoping content that the register does not attempt. |
| **D4** — `pipeline/solve.py:38` docstring says forecast cross-year warm-start is "default-OFF" while the dataclass default is `True` and the shipped posture is disarmed via `shipped_forecast_xyear_warmstart()`. | **NOT covered here.** It is a *code docstring*, not the spec, and it is outside this session's brief. One-line fix; needs an owner-assigned executor. |
| **D5** — stale quantitative snapshots. | **Partly absorbed.** `docs/testing.md` recorded in `../user-manual.md` §10 with both denominators (**447** `test_*.py`, **454** `.py` under `tests/` — the register's "454" counts all Python files, including helpers and `conftest`). The July peer review's §5 accuracy table is a frozen RECORD and is out of scope for both this checklist and the manual. |

### 9.1 Two D2 items this checklist deliberately does not treat as spec errors

- **"Three-solve" wording.** §1.6's *heading* still reads "Unit Commitment —
  Three-Solve LP Heuristic", but its **body already carries the correction** in
  two explicit paragraphs ("P2 is ARCHIVED…", "P1 — the no-commitment solve — is
  the model's MAIN run"). So the content is right and the heading is stale.
  Retitle it (e.g. "Unit Commitment — LP Screen Heuristic (P0/P1 production;
  P2 archived)"); do not rewrite the section.
- **`retirement_reserve_margin`.** L782 already states it "was DELETED with the
  floor-accreditation rebuild". The spec is correct; the register's "documented
  live but deleted" applies to a different doc set.

---

## 10. Out of scope for this audit

Recorded so DOCS-B does not treat their absence as an oversight:

- **`docs/codebase/07-runner-and-cli.md` staleness** — enumerated in
  [`../user-manual.md` §10](../user-manual.md#10-known-doc-divergences-found-while-writing-this-manual)
  (wrong subcommand count, six stale line numbers, two unrunnable examples, a
  stray `</content>` tag). Another lane's surface.
- **`docs/testing.md`'s "~355 files"** — actual **447** `test_*.py` (454 `.py`
  including helpers and `conftest`). Same place; also AUDIT-A row D5.
- **`market-sim-build-plan.md`** — the other L1 "spec" row in `docs/README.md`,
  status ACTIVE, is itself Phase-0 build-plan content. Whether it should survive
  finalization is an **owner** question this audit does not answer, but a
  finalized methodology spec sitting beside a live Phase-0 build plan is worth
  the owner's attention.
- **Whether the spec should carry a version/date banner.** It currently has none.
  The repo's status-header convention applies to *new* docs; adding one here is a
  DOCS-B judgment call.
