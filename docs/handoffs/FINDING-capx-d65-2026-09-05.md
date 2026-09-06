# FINDING — capx D65 (Act A): the CCS retrofit's fourth seam BUILT — both fixed-cost legs now scale with the capture island, the k = 1 host is invariant to the digit, and the NEISO A/B measures what the cap does when the ranking flattens

**Lane:** capx D65 — **Act A only** (D64 §4). **Branch** `claude/capx-d65-ccs-scaling-gfzp6c`.
**Written 2026-09-05.** One gated `ScenarioConfig` field, default OFF; **nothing arms in this lane**.
Charter: prompt pack §D65 + `FINDING-capx-d64-2026-09-05.md` §4. Pre-registration:
`PRECOMMIT-capx-d65-ccs-fixedcost-shape-2026-09-05.md` (written before any code edit and before
any solve, and carrying the whole G-DRIFT audit).

**Act B is NOT in this lane and was not touched.** Ledger §3 read at session start:
**Q47 is `PRESENTED (r#41)`, not RULED**, so the charter stood as issued and was not re-cut.
`ccs_retrofit_vom_adder` stays at its shipped `8.0`; the ATB extract was not widened; no A2 arm
was solved. §9 states the exact re-cut D65-B would need if Q47 rules (A).

---

## 0. The verdicts

| # | question | answer |
|---|---|---|
| 1 | Does the seam build clean? | **Yes.** One field, one validator, one `ccs.py` change, one CLI pair, six pre-solve tests. Zero DOF — no new constant, no new reference host, no ISO's fitted number. Both pinned keys unmoved with the field absent AND explicitly `False`. |
| 2 | Phase 0 (zero LP) | **REPRODUCED, to the MW and to 5e-12 on the per-unit clearing ratio**, on all six ISOs × 2028–2030 through the CODE path (§2). |
| 3 | G-DRIFT | **58 files, +4,867/−574 since the control's `git_sha`; EVERY hunk INERT.** Config-level drift measured at **0 field diffs across all 784 fields**. G-CTRL form 4 valid — **no control solve spent** (§3). |
| 4 | A1 (NEISO t1f, seam 4 alone) | *(§4)* |
| 5 | The STOPs | *(§5)* |
| 6 | ARM / DO-NOT-ARM | *(§8)* |

---

## 1. What was built

### 1.1 The basis, restated in one paragraph (D64 §1.2 — the reason this is a construction repair)

D50 sized the capture island's **capex** to the host's captured CO2
(`retrofit_capex_per_mw = capex_ref × k`, `k = captured / captured_ref`, `captured_ref` =
0.32319 t/MWh) and left both **fixed-cost** legs at the reference host's per-MW / per-MWh values:
`ΔFOM` ($/MW-yr) and `ccs_retrofit_vom_adder` ($/MWh). §45Q is credited on the host's OWN tonnes,
so both legs **diluted per captured tonne** as `er` rose and the carbon-0 clearing threshold merely
**moved** (er ≳ 0.46 → ≳ 0.58–0.63 t/MWh) instead of vanishing. ATB 2024's fossil methodology page
says the legs are TPC fractions in so many words — *"property taxes and insurance (FOM component)
as well as maintenance labor (FOM component) and maintenance materials (VOM component) are
calculated as a percentage of TPC"*, and out-year O&M *"are adjusted for the CAPEX reductions"* —
and NETL Rev 4a's B31A→B31B.90 exhibits decompose the capture increment to **95.5 %**
TPC-proportional for the fixed leg and **100 %** island-proportional for the variable leg, with
**nothing** in either proportional to the *host's* MW or MWh. Under seam 1 the island's TPC is
`capex_ref × k`, so both legs carry that same `k`.

### 1.2 The field, the seam and the harness

| item | detail |
|---|---|
| field | `ccs_retrofit_fixed_cost_co2_scaling: bool = False` (`scenarios.py`, beside the D50 field) |
| validator | `__post_init__` **REQUIRES** `ccs_retrofit_capex_co2_scaling` — without seam 1, `k` is 1.0 for every host, so arming this alone would be a silent no-op that nonetheless keys distinctly. Refused loudly (rule 24) |
| registration | `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[…] = "False"` + the tier-2 registry, **in the same commit as the field** (the nyiso-119 discipline) |
| CLI | `--ccs-retrofit-fixed-cost-co2-scaling` / `--no-…` on `run_full_horizon.py`, `default=None` None-sentinel; recorded in `run_config.json` through the resolved config |
| seam | `ccs.py::apply_ccs_retrofit`: `delta_fom_per_mw_yr_ref` is computed **once**; per host `delta_fom = ref × fixed_cost_scale`, `vom_adder_per_mwh = ccs_retrofit_vom_adder × fixed_cost_scale`, `fixed_cost_scale = capex_scale if armed else 1.0`; `mc_post` pays the scaled adder; **the conversion adds that SAME scaled adder to `gen.vom`**, read back off the candidate's own log row, so a converted unit's dispatch VOM is the VOM its own screen priced |
| log | gains `fixed_cost_scale` and `vom_adder_per_mwh`; `delta_fom_per_mw_yr` becomes per host |

**Zero DOF.** Every factor is an existing cited constant and the reference host is unchanged. The
one approximation, stated at the definition: folding the 3.6 % operating-labor headcount step into
the TPC-proportional part costs `0.036 × ΔFOM_ref × (k − 1)` ≈ **$1,300/MW-yr at k = 2** against a
~$200,000/MW-yr bar (**0.6 %**), below the cap-packing unit. Splitting it out would add a constant
to remove a 0.6 % effect and is **not** recommended.

**Outside the seam, stated so nobody re-opens it:** `co2_transport_storage_cost` is already per
tonne and charged on `captured` (ATB excludes beyond-the-fence CO2 costs from its FOM/VOM — no
double count); the HR-penalty leg is D30 §5 row 5's; and the **level** of `ccs_retrofit_vom_adder`
is Act B / card C-15.

### 1.3 The keys — measured, not asserted

| config | key | reading |
|---|---|---|
| `ScenarioConfig()` (field absent) | `e5ecd4105ada3e58` | **unmoved** |
| `ScenarioConfig(…=False)` (explicit) | `e5ecd4105ada3e58` | **unmoved** — the frozen `"False"` drop |
| `ScenarioConfig(mode="backcast")` | `6a2845e50951394e` | **unmoved** |
| `ScenarioConfig(…=True)` | `2186aa915ad19c59` | keys distinctly |
| NEISO t1f bare + explicit `False` | `18515067bf4d2fbe` | **the control's own key** |
| **NEISO t1f bare + `True` (arm A1)** | **`8ebed20ae90ec0e7`** | pre-declared before the solve; collision-checked against every committed artifact (clean) |

### 1.4 The deferred disclosure (director ruling r#41 = D64 §4.2 option (i))

`retirements.py::_THERMAL_FOM` reads FOM by **fuel type** (`fixed_om_gas_cc_ccs` = 65 $/kW-yr for
every `gas_cc_ccs` unit; `Generator` carries no per-unit FOM), so a host converted here at
`k = 1.8` is screened for retirement in **later** years at the **reference** island's FOM, not its
own. It is second-order (the going-forward bar moves by ≤ $28,000/MW-yr on a unit whose margin is
§45Q-dominated) and it is a **routed successor** — option (ii), a `Generator.fom_adder_per_kw_yr`
set at conversion to `ΔFOM_ref × (k − 1)` and added in the retirement FOM lookup — **not this
lane's**, because it touches the retirement screen and D65 stays one seam. It is written into the
`ccs.py` docstring, the matrix row and this finding rather than silently absorbed.

### 1.5 Tests (six, all pre-solve; `tests/unit/model/test_ccs_retrofit.py`)

1. **`test_off_is_byte_identical_and_cache_neutral`** — field absent vs explicit `False`: identical
   logs, `fixed_cost_scale == 1.0`, `delta_fom_per_mw_yr == ΔFOM_ref`, `vom_adder_per_mwh ==
   ccs_retrofit_vom_adder`, identical converted-unit `(fuel_type, vom)`; both pinned keys asserted.
2. **`test_reference_host_is_invariant_on_and_off`** — a `k = 1` host (er = 6.3 × 0.057) produces
   an identical log over **every field**, not a chosen subset, plus identical converted attributes.
   This is **STOP 1 as a test**.
3. **`test_legs_scale_with_captured_co2`** — a 2× host pays 2× the island **and** 2× ΔFOM **and**
   2× the VOM adder; `capex_scale` untouched at 2.0.
4. **`test_converted_unit_vom_carries_the_scaled_adder`** — the converted `gen.vom` is
   `base + vom_adder × k`, identical to the value in its own log row.
5. **`test_per_tonne_invariance_at_carbon_zero`** — two hosts, equal `hr`, `er` ratio 2:1, carbon 0:
   the uplift-to-capex gap equals the **HR-penalty term's** per-tonne difference **analytically**
   and nothing else, and is strictly **smaller** than the same gap off the seam.
6. **`test_validator_rejects_the_field_without_seam_1`.**

`tests/unit/model/test_ccs_retrofit.py` **53 passed**; `tests/regression/test_persisted_identity.py`
**14 passed**; `ruff` clean; `scripts/check_mechanism_matrix.py` **green** (integrity OK, 0 anchors
left in the ratchet, keeper stamps and §5.x prose headers match).

---

## 2. Zero-LP Phase 0 (rule 29 step 0) — REPRODUCED

The D64 census rows were replayed as a synthetic fleet and driven through the **shipped
`apply_ccs_retrofit`** at the census's own hour ceiling (every hour in merit, cap lifted), once with
the seam-4 gate OFF and once ON, and the clearing set read off the code's own log rows with the
census criterion `window_years × uplift_window ≥ retrofit_capex_per_mw`. Per-unit inputs (`hr`,
`er`, `mw`, `chp`) come from the census and the per-year context (`gas`, `carbon`, `capex_kw`) from
its summary, so nothing is re-derived: what is under test is **the seam's arithmetic**.

| ISO · year | shipped, census → code | seam 4, census → code |
|---|---|---|
| ERCOT 2028 / 29 / 30 | 0 / 0 / 0 → **0 / 0 / 0** | 0 / 0 / 0 → **0 / 0 / 0** |
| PJM 2028 | 0 → **0** | 0 → **0** |
| PJM 2029 | 5 / 1,675.478 MW → **5 / 1,675.478** | 0 → **0** |
| PJM 2030 | 5 / 1,675.478 → **5 / 1,675.478** | 0 → **0** |
| MISO 2028 / 29 / 30 | 2 / 45.540, 3 / 379.997, 4 / 529.685 → **identical** | 0 / 0 / 0 → **0 / 0 / 0** |
| NEISO 2028 | 86 / 12,375.660 → **86 / 12,375.660** | 87 / 12,391.990 → **87 / 12,391.990** |
| NEISO 2029 / 30 | 87 / 12,391.990 → **identical** | 87 / 12,391.990 → **identical** |
| NYISO 2028 | 67 / 6,858.410 → **67 / 6,858.410** | 65 / 6,795.340 → **65 / 6,795.340** |
| NYISO 2029 / 30 | 67 / 6,858.410 → **identical** | 67 / 6,858.410 → **identical** |
| CAISO 2028 / 29 / 30 | 82 / 13,676.720 → **identical** | 82 / 13,676.720 → **identical** |

**Max `|ratio(code) − ratio(census)|` = 5.28e-12 (shipped) / 4.61e-12 (seam 4)** over every eligible
tranche of all six ISOs — floating-point identity, not agreement to a tolerance. **PHASE 0:
REPRODUCED**; the charter's named targets (PJM 2029 1.68 GW → 0, MISO 0.53 → 0, NEISO / NYISO /
CAISO 12.39 / 6.80 / 13.68 GW) all land exactly.

**One convention worth recording**, because it looked like a mismatch on the first pass and is not:
the census **reports** a `clears_*` boolean for `CC_CHP` rows too, while its `ship_*` / `s4_*`
**summary** counts the no-CHP set (seam 1 drops cogeneration hosts from the candidate list). The
code produces the no-CHP set, which is what the summary — and therefore the charter's MW targets —
is denominated in. Comparing the code against the raw boolean column flags every ISO's one or two
CHP plants and nothing else; comparing it against the summary's own convention reproduces exactly.

---

## 3. G-DRIFT — the control is the committed bundle, and no control solve was spent

Rule 29 clause (b): the control is the committed `results/ff-t1f-d50/neiso/` bundle at
`18515067bf4d2fbe` (the D50 arm = the post-Q42 bare key; 39 committed converters — 2028 15 rows /
2,982.2 MW, 2029 12 / 2,996.7, 2030 12 / 2,982.6). Its `run_config.json` records `git.sha
= 9e48ff6`, `dirty: false`, `changed_files: []`.

**Config-level drift: NIL, measured twice.** (a) The control's own stored `config.yaml` re-resolves
at HEAD to `18515067bf4d2fbe`, unmoved. (b) A freshly built golden-posture NEISO t1f recipe at HEAD
— `apply_iso_scenario_defaults(reference_config("NEISO", 2026, 2030, cmc, golden_posture=True,
ccs_retrofit_capex_co2_scaling=True), "NEISO")` — is **field-identical to the stored config across
all 784 fields (0 diffs)** and hashes to the same key. Every config-gated hunk below is therefore
provably at the control's value.

**Code-level drift: 58 files, +4,867 / −574, EVERY hunk INERT, ZERO LIVE.** The full
classification table (20 rows, each with its reason) is in
`PRECOMMIT-capx-d65-ccs-fixedcost-shape-2026-09-05.md` §3.2 and is not repeated here. The classes
it resolves to: docstring/comment-only (6 files); dead-code removal with **0 live references
grepped** for every removed symbol (12 files); another ISO's branch — MISO's `skip_cells`, CAISO's
`spot_coverage` and WECC border corridors, PJM's RGGI `zone_share` footprint, NYISO's locality
curves (8 files); a default-off gate absent from the recipe — D53's sector gate, D51's dated-net
ratio, D57's supply clearing, D59's locality, the duty-split offer families, `federal_ces`/MISO
clean tiers (10 files); a per-ISO artifact this ISO does not have (only
`egrid_steam_collapse_heat_rates_NYISO.csv` exists); backcast-only paths — the PERF-B
`reuse_p0_from` is passed by `run_calibration.py` alone, `runner.py` never passes it; and pure
timing/diagnostics accounting.

**One INERT-with-note**, recorded so the differencing is honest: `results/export.py` +
`results/emissions.py` add **two new reported keys** to the year summary — `import_co2_t` and
`unserved_mwh` — declared in their own comment as *"Reported-only … beside `emissions_mt` and NEVER
inside it."* No existing metric moves; the arm's summary simply carries two keys the control's does
not, and those two are not differenced.

**Conclusion: all hunks INERT ⇒ G-CTRL form 4 is VALID.** The audit cost seconds; a control solve
would have cost ~8 minutes and told us only that two numbers differ, not which line did it.

---

## 6. Governance

- **Rule 5 [R-NO-MAGIC] / rule 21 [R-DOF]:** zero free parameters. `k` is the D50 factor unchanged;
  `ΔFOM_ref` and `vom_adder_ref` are the constants already registered. No value was fitted, swept,
  or selected against any residual, and no gate was chosen by whether a criterion passed.
- **Rule 13 [R-MEASURED] / rule 14 [R-ACCURATE]:** the legs' composition is read off ATB 2024 and
  NETL Rev 4a, and the construction regenerates for a forward year from forward drivers. Its
  direction is stated in advance and is the *unhelpful* one for high-`er` hosts — a faithful island
  makes those retrofits **harder**, which is the expected signature, never a target.
- **Rule 19 [R-ONE-MECH]:** one factor prices the island and both of its O&M legs. No second
  scaling mechanism was added, and `co2_transport_storage_cost` (already per tonne) is untouched.
- **Rule 22:** forecast mode only, horizon 2026–2030. **No holdout year is touched** — no solve,
  no scoring, no registration outside 2023–2025 in the backcast lane and nothing before 2026 here.
- **Rule 24 [R-REGISTRY]:** the field is in `ScenarioConfig`, in both cache-key tables, in the
  tier registry, on the CLI, and in `run_config.json`. No env-var knob, no `getattr` literal.
- **Rule 25 [R-ISO-SCOPE]:** a **posture**, not a transfer — no ISO's fitted number is carried, the
  reference host is the one `new_entry._emerging_lcoe` already charges the ATB increment against,
  and NEISO's matrix cell comes from NEISO's own arm while the other five ship `U`.
- **Rule 27 [R-PUSH]:** every file edited locally with the Edit path and pushed as exact on-disk
  bytes; the ≥300-line files were blob-verified after push (§7).
- **Rule 28 [R-MECH-MATRIX]:** the base row `ccs_retrofit_fixed_cost_co2_scaling` plus one appended
  cell line in **all six** shards, in this PR, as the last commit. `check_mechanism_matrix.py`
  green.
- **Rule 29 [R-SCREEN]:** clause (0) zero-LP phase 0 ran first and had to pass before the arm was
  solved; clause (b) G-CTRL form 4 with a G-DRIFT audit recorded in the PRECOMMIT **before** the
  arm launched, so no control solve was spent.
- **Collision care:** the field sits in the D50 block of `scenarios.py` and the validator is
  appended at the very **end** of `__post_init__`, so SCN-WS1a's D34-guard region and SCN-WS2a's
  `federal_ces_*` block were never touched. `ccs.py` was this lane's alone this window.
  `program-status.json` and `ff-verdicts.json` are D60-R2's and were **not** written.
- **`data/clean` note (not a finding, recorded so the next lane does not re-diagnose it):** the
  first A1 launch aborted at `load_confirmed_exits` because `data/clean/confirmed-retirements` is
  derived and gitignored and a fresh checkout has none. `scripts/data/curate_confirmed_retirements.py`
  regenerates it (5 partitions; NEISO 16 rows, 16 live). The refusal is correct behaviour — it
  refuses to silently degrade to the economic screen — and no config or code was changed for it.

---

## 9. The exact re-cut D65-B would need if Q47 rules (A)

Act B is a **value** change (`ccs_retrofit_vom_adder` 8.0 → 2.95 $/MWh 2026$) and re-keys **every**
bare key unconditionally — the field is not a `_CACHE_KEY_OPTIONAL_FIELDS` member, so D41 §6.2's
mechanic applies and there is no drop value to hide behind. Nothing in Act A anticipates it: the
gate built here scales **whatever level is registered**, so the two acts compose without either
being rewritten. What a D65-B lane would need, stated now so it is not improvised later:

1. **The widened pinned extract, first, and its source-consistency test.** The committed
   `data/raw/nrel-atb/atb_2024v4_electricity_filtered.*` carries only `CAPEX` and `Fixed O&M` for
   `NaturalGas_FE` (348 rows each) — which is precisely why the VOM leg was never read off the
   pinned basis. `fetch_nrel_atb.py`'s filter widens to carry `Variable O&M` and `Heat Rate` from
   the **same source bytes** (OEDI `ATBe.csv` v4.0.0, sha256 `567dde9d…`), and a test asserts
   `ccs_retrofit_vom_adder == (ATB gas_cc_ccs VOM − ATB gas_cc VOM) × inflation_factor()` in the
   shape of `tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py`. **D64 STOP 6 makes this the
   precondition, not a follow-up**: a value with no asserted derivation is the defect D41 removed.
2. **The dollar-year stated and `needs-citation` cleared** in `docs/parameter-citations.md`
   (line 1606 today), with NETL Rev 4a's 2.23 $/MWh per host-MWh 2026$ recorded as the
   cross-check and ATB as the basis (host and island on one basis — D41 §2.3's rule).
3. **The re-key declared before the solve**, every bare key pre-declared and the priors preserved
   at a `-pre-d65b` suffix, and the cache-epoch ledger in `src/market_sim/results/cache.py` given
   its entry plus the two pinned-key cause blocks in `tests/regression/test_persisted_identity.py`.
4. **The A2 arm is NOT a repeat of A1.** Act B alone re-opens the carbon-0 screen on the *shipped*
   shape (D64 §2.4: ERCOT 10.2 / PJM 11.2 / MISO 6.7 GW at the ceiling), and Act A + Act B together
   put it on a knife-edge (0.4–5.7 GW per ISO-year clearing **by 0.1–4 %**, needing ≥ 8,100 in-merit
   hours). So the informative arm is a **carbon-0 ISO**, not NEISO — the RGGI ISOs are cap-bound on
   both constructions and cannot discriminate. **A carbon-0 ISO gaining rows under A2 is NOT a
   STOP**; it is the accurate level's pre-registered signature (D64 §4.5's closing clause), and the
   surviving PJM/MISO rows are the `er/phys` 1.27–1.49 hosts, which are D49 §1.3's business.
5. **The direction is stated before the measurement, as rule 23 requires:** re-identification makes
   retrofits **easier**. Rule 14 keeps an accurate value whichever way it moves the answer, and a
   per-tonne-correct model landing 1–6 % short of §45Q at the hour ceiling is a more faithful
   market than one held shut by a 2.7× VOM.
6. **The matrix touch is the existing `ccs_retrofit_screen` row's `def`/`note`** (the D41 §6.3
   remedy for a costed-parameter change), **no cell verdict moved** — Act B arms no mechanism.
   The row added by this lane is Act A's and does not change.

If Q47 rules **(B)** the same six items apply with the coupling dropped. If it rules **(C)**, the
shipped 8.0 stays and the only obligation is that D64 §2.4's disclosure — that the carbon-0 closure
D50 reported **rests on an uncited number** — stays on the record and on the `ccs_retrofit_screen`
row, which it now does.

---

## 7. What was pushed, and what is OWED

### 7.1 Rule 27 blob verification

Every file ≥ 300 lines was edited locally with the Edit path and pushed as the exact on-disk bytes;
each was fetched back and compared on **line count and blob hash** immediately after its push,
before the next commit. Verified: `src/market_sim/config/scenarios.py` (17,795 lines),
`src/market_sim/model/capacity_evolution/ccs.py` (584), `scripts/run_full_horizon.py` (1,313),
`tests/unit/model/test_ccs_retrofit.py` (1,259), `docs/codebase-site/data/mechanism-matrix.js`
(2,595) and the six ISO shards. Every one **IDENTICAL**. No file was rewritten from regenerated
response content and no placeholder or partial version was ever committed.

### 7.2 OWED — registration and the artifact-only re-score

**D60-R2's finding has NOT merged** at this HEAD: `git log origin/main --grep=D60-R2` returns only
its PREDECL Addendum D (`342c7593`) and its STATE AT START (`f7aecae3`), with the director's r#41
line recording *"D60-R2: nothing landed since #4824 — status ASKED, not graded lost."* Per the
charter, **registration and the artifact-only re-score therefore wait**, and this lane lands as a
**CHECKPOINT**. What is owed, in order, once D60-R2's finding merges:

1. **Register A1** through the single `scripts/register_forecast_run.py` path into the
   `frontend/data/forecast/` namespace, under a **suffixed** key with the incumbent's record
   preserved at **`neiso-t1f-pre-d65`** — the bare `neiso-t1f` (`18515067bf4d2fbe`) stays the
   designated forecast leg, because **nothing arms in this lane**.
2. **Re-score artifact-only** after the final rebase (no re-solve), so `scored_at_sha` is stamped
   against the merged HEAD.
3. **Do NOT write** `frontend/data/forecast/program-status.json` or `ff-verdicts.json` — those are
   D60-R2's this window, and the namespace's `registry/`, `runs/`, `manifest.js` and
   `program-status.js` are generated by the Pages deploy, not committed.

The A1 bundle is committed with the finding so the numbers above are re-readable without a replay.

---

## 3b. CORRECTION — the G-DRIFT audit was WRONG, and the arm caught it

**Report this before the A/B numbers, because it changes which control they are measured against.**

The A1 solve's ledger differs from the committed control's in **2027** — a year in which
`apply_ccs_retrofit` returns at its first statement (`year < ccs_retrofit_available_year`, 2028)
and this lane's field is never read. A pre-2028 difference is therefore **impossible for the seam**
and can only be drift. The §3 conclusion "every hunk INERT, zero LIVE" was **wrong**.

**What the drift is, measured.** A HEAD control was solved on the same recipe with an explicit
`--no-ccs-retrofit-fixed-cost-co2-scaling` (rule 29(b): a LIVE hunk is the one thing that earns a
control solve). It resolved to the control's own key `18515067bf4d2fbe` — end-to-end confirmation
of STOP 5 through the real CLI. Three-way, on 2027:

| | committed control (`9e48ff6`) | HEAD control | arm A1 |
|---|---|---|---|
| `retirements` | **33 rows / 2,369.81 MW** | **40 rows / 2,244.89 MW** | 40 rows / 2,244.89 MW |
| `reserve_margin` | 0.045867 | 0.050821 | 0.050821 |
| `fleet_by_fuel_after` gas_cc | 10,713.80 MW | 10,838.72 MW | 10,838.72 MW |

**HEAD control ≡ arm A1 on every 2027 ledger key**, and the 2026 result parquet is **byte-identical
across all 12 columns**. So the seam is byte-inert before 2028 exactly as designed, and the entire
pre-2028 difference is HEAD drift between `9e48ff6` and this HEAD. It is not solver
non-determinism (the two HEAD runs agree bit-for-bit) and it is not the environment (the control's
recorded stack — python 3.11.15, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3, pyarrow
24.0.0, pydantic 2.13.4 — is this session's stack exactly), and nothing on the path reads a
wall clock (`datetime.now()` / `date.today()` grep over `src/market_sim/`: **zero hits**).

**How the audit missed it — the honest mechanism, so the protocol can be fixed.** I classified
`retirements.py` (+758/−27, the largest file in the diff) by its **new functions and their gates**
— D53's sector gate, D51's dated-net ratio, D57's supply clearing, D59's locality — verified each
predicate fails for NEISO, and called the file inert. But the diff also modifies **existing,
ungated helpers inside it**. Rule 29(b) says *"classify every changed hunk"*, and on the one file
where that mattered I classified the file instead. The specific ungated existing-code change the
re-read found is **capx D55's `_floor_retention_merit`** (2026-09-05), which deliberately replaces
key 1 of the reliability-floor retention sort with a class-constant form because the per-unit
quotient put same-fuel units on 4–5 distinct floats at the 1e-11 level — an intentional
**ordering** change. (`floor_retained` is `[]` in NEISO 2027 on both sides, so D55 is a candidate
rather than a demonstrated cause; the bisect against the pre-drift source is in §3c.) The other
in-function hunks — D57's `supply_clearing_armed` short-circuit, D59's `locality_price` max, the
`_screen_stack` diagnostic move — are gated or diagnostic and do reduce to the pre-existing path.

**What this does and does not invalidate.**
- **Does not** touch the build, the tests, the keys, or Phase 0: Phase 0 is a zero-LP arithmetic
  reproduction against a committed census, independent of any drift.
- **Does not** weaken the seam's inertness claim — it *strengthens* it: the seam is now measured
  byte-inert pre-2028 on real solves, not merely argued from the year gate.
- **Does** invalidate G-CTRL form 4 for this A/B. Every A/B number in §4 is therefore measured
  against the **HEAD control**, which is a true one-field pair, and the committed bundle is quoted
  only where it is the right reference (the D50 composition baseline).

---

## 5. The STOPs, each read against the evidence

| # | STOP | reading |
|---|---|---|
| 1 | a `k = 1` row moving in any ledger or log field | **NOT FIRED.** Three independent proofs. (a) `test_reference_host_is_invariant_on_and_off` asserts a `k = 1` host produces an identical log over **every field**, and identical converted attributes. (b) The seam's own arithmetic: `fixed_cost_scale = capex_scale`, which is exactly 1.0 when `captured == captured_ref`. (c) Measured across the whole census — **2,590 eligible tranches of all six ISOs × 2028–2030, 0 violations**: every `k = 1` row's clearing ratio moves by < 1e-9, every `k > 1` row's strictly falls, every `k < 1` row's strictly rises. |
| 2 | seam 4 alone making a carbon-0 row clear that the keeper did not, **or** a `k > 1` host converting under A1 that did not convert in the control **in a non-cap-bound year** | **NOT FIRED, and reported rather than waved through.** Carbon-0 limb: NEISO is an RGGI ISO, and Phase 0 shows the carbon-0 ISOs go 5 → 0 (PJM), 2–4 → 0 (MISO), 0 → 0 (ERCOT) under seam 4 — the direction is *closing*, never opening. `k > 1` limb: **every year of A1 is cap-bound**, so the clause's own precondition is never met. Within the cap the arm does gain hosts at `k` 1.00–1.06 (2028: p55048 1.03, p55107 1.02, p55042 1.04, p56798 1.00, p55100 1.06) — but the 2,590-row check above proves seam 4 can only make a `k > 1` host **harder in absolute terms**, so a gain under a binding cap is necessarily a **ranking** effect: those near-reference hosts rose because the `k` 1.55–1.71 hosts above them got much harder. That is the mechanism's purpose, not the rule-14-wrong direction. |
| 3 | any NEISO/NYISO year converting more than the cap, or ERCOT/MISO gaining a row | **NOT FIRED.** No A1 year exceeds 3,000 MW (§4). NYISO was not solved (the cap did not move — see §4). ERCOT and MISO are not arms in this lane, and Phase 0 reads **0 rows for both under seam 4**, so neither can gain one. |
| 4 | key drift — a realized key ≠ its pre-declared value, or a collision with a committed key | **NOT FIRED.** A1's realized bundle key is **`8ebed20ae90ec0e7`**, exactly the value pre-declared in the PRECOMMIT before the solve, and a repo-wide grep found no committed artifact carrying it. |
| 5 | byte-inertness failing on the committed `neiso-t1f` recipe with the field absent / `False` | **NOT FIRED — and now measured on real solves rather than argued.** The explicit-`False` CLI path resolves to the control's own key `18515067bf4d2fbe`; the ScenarioConfig default and bare-backcast pins are unmoved; and the HEAD control's 2026 result parquet is **byte-identical to A1's across all 12 columns**, with its 2027 ledger identical to A1's on **every key**. |
