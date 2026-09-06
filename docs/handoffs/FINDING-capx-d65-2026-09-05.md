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
| 3 | G-DRIFT | **WRONG, and the arm caught it (§3b).** The audit read all 58 files' hunks as INERT; A1's ledger then differed from the committed control in **2027**, a year the seam cannot reach. A HEAD control was solved under rule 29(b)'s LIVE clause and is **byte-identical to A1 before 2028**, so the seam is inert as designed and the difference is HEAD drift. **Root-caused, not just detected:** a one-hunk revert of capx D55's `_floor_retention_merit` reproduces the pre-drift 2027 exactly (§3c–§3d) — and the reason its own diagnostic showed nothing is a second finding: the reliability floor has **three call sites and only two are logged**. |
| 4 | A1 (NEISO t1f, seam 4 alone) | **The seam RE-ORDERS; it does not re-select.** 2028: every host lost is `k` 1.55–1.71, every host gained is `k` 0.95–1.06 — no exceptions — with MW-weighted `er` **0.5752 → 0.3912** and `hr` 7.305 → 7.029. But the 3 GW/yr cap binds in every year on both arms, so the **cumulative** 2028–30 set is 34 rows either way and differs by **one swap** (`er` 0.4385 → 0.4353, −0.7 %). Quoting 2028 alone overstates the mechanism by an order of magnitude (§4.2). |
| 5 | The STOPs | **None fired**, each read against evidence rather than asserted — including a 2,590-row census check that every `k = 1` row is invariant and every `k > 1` row strictly harder (§5). |
| 6 | ARM / DO-NOT-ARM | **ARM, but ONLY COUPLED WITH ACT B — do not arm Act A alone**: seam 4 multiplies an uncited 2.7× VOM level by `k`, compounding the error on exactly the hosts it re-prices. Card C-17 / Q49 drafted (§8). |

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

**Conclusion as written at the time: all hunks INERT ⇒ G-CTRL form 4 is VALID, no control solve
spent.** **THIS CONCLUSION IS WRONG AND IS SUPERSEDED BY §3b**, which the arm itself surfaced. It is
left standing above, unedited, because a pre-registration that is quietly corrected after the fact
is worth nothing — the audit as actually recorded is what §3b grades.

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

---

## 3c. The drift bisected — it is CODE, and it reproduces

The pre-drift source tree (`git archive 9e48ff6 src scripts configs`, run against the same
`data/` through `MARKET_SIM_DATA_ROOT`) was solved for NEISO 2026–2027 on the same recipe:

| 2027 | `retirements` | `reserve_margin` | `fleet_by_fuel_after` gas_cc |
|---|---|---|---|
| **old source `9e48ff6`** | **33 rows / 2,369.81 MW** | 0.045867 | 10,713.803 |
| **committed control** | **33 rows / 2,369.81 MW** | 0.045867 | 10,713.803 |
| HEAD control | 40 rows / 2,244.89 MW | 0.050821 | 10,838.721 |

**The old source reproduces the committed control's 2027 with ZERO differing ledger keys**, and
its 2026 likewise (0 diff keys, against HEAD's 2 additive-key diffs). So the probe is faithful, the
committed bundle is reproducible at its own sha, and the divergence is **entirely inside
`src/` + `scripts/` + `configs/`** — the only trees the archive replaced. It is code drift, it is
deterministic, and it reproduces on demand.

**Magnitude, for whoever owns it:** NEISO's 2027 economic-retirement set changes by **7 rows and
−124.92 MW of gas_cc**, with an almost disjoint membership in the gas-CC economic channel — the
plants that retire at HEAD (p3236, p51030, p54324, p10726, p55068, p10307) are largely the
high-`er` hosts the pre-drift run instead kept alive to convert in 2028, and vice versa. That is a
material change to a forecast leg, and it is silent: the committed `neiso-t1f` ledger no longer
describes what HEAD produces from its own recipe.

**The hunk is PINNED, not merely suspected** — a one-hunk revert reproduces the pre-drift result
exactly, and the reason its own diagnostic showed nothing is itself a finding. See §3d.

---

## 4. Arm A1 — NEISO t1f, seam 4 alone, against the HEAD control

**One field, one difference.** `--ccs-retrofit-fixed-cost-co2-scaling` vs
`--no-ccs-retrofit-fixed-cost-co2-scaling`, same HEAD, same recipe, same machine. Arm
`8ebed20ae90ec0e7` (10.4 min); control `18515067bf4d2fbe` (10.9 min, 3.38 GB). **Both: 5/5 years
solved, 14 invariants scored, 0 FAIL, 0 WARN.**

### 4.1 What converts

| year | HEAD control (seam 4 OFF) | arm A1 (seam 4 ON) | % of the 3 GW/yr cap |
|---|---|---|---|
| 2028 | 11 rows / 2,974.9 MW · MW-wtd `er` 0.5752 · `hr` 7.305 | **12 / 2,950.4 MW · `er` 0.3912 · `hr` 7.029** | 99.2 % → 98.3 % |
| 2029 | 14 / 2,922.4 · `er` 0.3725 · `hr` 7.170 | **9 / 2,962.7 · `er` 0.4477 · `hr` 7.333** | 97.4 % → 98.8 % |
| 2030 | 9 / 2,905.3 · `er` 0.3650 · `hr` 7.551 | **13 / 2,913.5 · `er` 0.4675 · `hr` 7.670** | 96.8 % → 97.1 % |
| **cumulative 2028–30** | **34 / 8,802.6 MW · `er` 0.4385 · `hr` 7.341** | **34 / 8,826.6 MW · `er` 0.4353 · `hr` 7.342** | — |

### 4.2 The result, stated plainly — the seam RE-ORDERS, it does not re-select

**In 2028 the effect is exactly the seam's signature and it is total.** Against the HEAD control the
2028 set loses **9 hosts, every one of them `k` 1.55–1.71** (`er` 0.557–0.613), and gains **10, every
one of them `k` 0.95–1.06** (`er` 0.340–0.380). Not one exception in either direction. MW-weighted
`er` falls **0.5752 → 0.3912** and MW-weighted `hr` **7.305 → 7.029**: the docstring's
"efficient hosts win" ordering, which D49 §1.4 found inverted, is restored outright.

**Over the whole window it very nearly cancels.** The cap binds in every year on both arms
(96.8–99.2 % of 3,000 MW), so the annual budget — not the screen — sets how much converts. The
cumulative converted set is **34 rows on both sides**, differing by exactly **one swap**: a 130.0 MW
`k` 1.61 host out, a 154.0 MW `k` 1.04 host in. Cumulative MW-weighted `er` moves **0.4385 → 0.4353
(−0.7 %)** and cumulative `hr` is unchanged to three decimals (7.341 vs 7.342).

That is the honest headline, and it is not what a per-year reading suggests: **under a binding
annual cap, seam 4's NEISO effect is almost entirely a re-ordering of which hosts convert first,
not a change in which hosts convert at all.** The per-year composition swings hard (2028 `er`
0.575 → 0.391, then 2029 and 2030 swing back as each arm draws from the residual its own 2028 left
behind) precisely *because* the totals are pinned by the cap. Anyone quoting the 2028 number alone
would overstate the mechanism by an order of magnitude.

### 4.3 The pre-registered expectations, graded

| # | expectation (PRECOMMIT §5 / D64 §4.4) | reading |
|---|---|---|
| 1 | NEISO conversions cap-bound **2,940–3,000 MW every year** | **HIT in mechanism, MISSED on the band in 2030.** The cap binds in all three years (98.3 / 98.8 / 97.1 % of 3,000), but 2030 lands at **2,913.5 MW, 26.5 MW below the band's floor**. Reported as a miss, not rounded into a pass — though the band was calibrated on the *committed* control's numbers and the **HEAD control is itself outside it** in 2029 (2,922.4) and 2030 (2,905.3), so the band describes the pre-drift baseline rather than the seam. |
| 2 | the MW-weighted `er` of the **2028** set falls below D50's 0.550 | **HIT, decisively: 0.3912** (and 0.5752 → 0.3912 against the HEAD control's own 2028). |
| 3 | every year's set ranks by `hr` within the in-merit hosts | **PARTIAL.** Clean in 2028 (`hr` 7.305 → 7.029, and the lost/gained split is perfectly separated on `k`). Not in 2029–30, where each arm draws from the residual pool its own 2028 created — an artifact of the binding cap, not of the ranking. Cumulative `hr` is flat (7.341 vs 7.342). |
| 4 | ERCOT / MISO, if solved: 0 rows, byte-identical | **NOT SOLVED — not needed.** Phase 0's code-path census reads **0 rows for both under seam 4** (and for ERCOT under the shipped construction too), so there is nothing for a solve to find. |

### 4.4 Conditional arms — neither triggered, and why

- **NYISO (the second RGGI witness)** was to be solved **only if A1 moved the cap.** It did not:
  the cap binds in every year on both arms and the cumulative totals differ by 24 MW (0.3 %).
  **Not solved.**
- **GOLDEN-3** was to be solved **only if the cap unbound or the composition moved by more than the
  cap-packing unit.** The cap did not unbind, and the cumulative composition moved by a single
  swap. The per-year composition does move by more than one packing unit — but that is the
  re-ordering §4.2 describes, inside a window whose totals are cap-pinned, and the GOLDEN-3
  horizon (RGGI to $67/t by 2040, §45Q ending 2032) is per-tonne-dominant on both sides where
  D64 §2.3 already expected no change in kind. **Not solved**, and the judgement is recorded here
  rather than left implicit.

---

## 8. ARM / DO-NOT-ARM — the recommendation, and the owner card

### 8.1 The recommendation: **ARM, but ONLY COUPLED WITH ACT B. Do NOT arm Act A alone.**

The seam itself is sound and this lane recommends it on the merits: it is a construction repair
with a published basis (ATB 2024's own methodology sentence; NETL Rev 4a's 95.5 % / 100 %
decomposition), it carries **zero DOF**, it introduces no constant and no reference host, it is a
posture rather than a transfer (rule 25 intact), and it is byte-inert off — measured, not argued.
Rule 14 keeps an accurate construction whichever way it moves the answer, and this one moves it the
*unhelpful* way for high-`er` hosts, which is the signature of a repair rather than a fit.

**But arming it ALONE would build a faithful shape on an unfaithful level, and the compounding runs
the wrong way.** `ccs_retrofit_vom_adder` = 8.0 $/MWh is `needs-citation` and **2.7–3.6× every
published basis** (ATB 2024: 2.95 $/MWh 2026$; NETL Rev 4a: 2.23). Seam 4 multiplies that level by
`k`, so a `k` = 1.8 host is charged 2.7× too much **and then 1.8× again** — the error compounds
precisely on the hosts the seam exists to re-price. The measured consequence is not marginal: on
D64 §2.4's census, seam 4 at the shipped 8.0 closes the carbon-0 screen **completely** (ERCOT / PJM
/ MISO all to 0 rows), while seam 4 at the published level leaves **0.4–5.7 GW per ISO-year
clearing by 0.1–4 %**. Arming Act A alone would therefore commit the model to the claim that *no
merchant NGCC retrofit ever clears on §45Q at carbon 0* — a stronger claim than the evidence
supports, resting on an uncited number, and pointing the opposite way from the market D64 §2.4
describes (every announced project close enough to need something else).

**The NEISO evidence supports the coupling too, from the other side.** Under a binding cap the
shape change is nearly free: cumulative composition moves 0.7 % and the converted set differs by a
single swap (§4.2). So arming Act A alone buys very little where the cap binds, while spending the
whole carbon-0 closure where it does not. The two acts are not independent, exactly as D64 §2.4
said; the level decides *how much* the shape closes.

### 8.2 Owner card — drafted for the director

> **Card C-17 / Q49 — capx D65 Act A: arm the CCS retrofit fixed-cost shape gate?**
>
> **What it is.** `ccs_retrofit_fixed_cost_co2_scaling` (built, GATED default off, requires the D50
> gate): scale `ΔFOM` and the capture VOM adder by the same `k = captured / captured_ref` seam 1
> already applies to the island's capex, because both legs are TPC fractions in their own sources
> (ATB 2024 fossil methodology; NETL Rev 4a B31A→B31B.90 at 95.5 % / 100 %). Zero DOF, no constant
> changed, a posture not a transfer, byte-inert off and byte-inert on every horizon ending before
> 2028.
>
> **What it measures (NEISO t1f A/B vs a same-HEAD one-field control, both 0 FAIL / 0 WARN on 14
> invariants).** 2028: every host lost is `k` 1.55–1.71, every host gained is `k` 0.95–1.06, with
> MW-weighted `er` 0.575 → 0.391 and `hr` 7.305 → 7.029 — the inverted ordering D49 §1.4 named is
> restored outright. Over 2028–2030 the 3 GW/yr cap binds in every year on both arms and the
> cumulative set is 34 rows either way, differing by one swap (cumulative `er` 0.4385 → 0.4353).
> At zero LP the seam closes PJM's 2029 residual (5 rows / 1.68 GW → 0) and MISO's (up to
> 4 / 0.53 GW → 0), and leaves ERCOT at 0 throughout.
>
> **Options.**
> **(A) ARM COUPLED — recommended.** Flip Act A's default together with Act B's re-identification
> (card C-15 / Q47 option A), in one PR and one re-key event, after D60-R2's finding lands. The
> shape and the level are coupled: seam 4 on an uncited 2.7× level compounds the error on exactly
> the hosts it re-prices, and it is that pairing — not either half — that D64 §2.4 measured.
> **(B) ARM ALONE now.** Buys the ordering repair, but commits the carbon-0 closure to the uncited
> 8.0 and would need re-solving again when Q47 lands. **Not recommended.**
> **(C) HOLD both.** The field stays built and off; D64 §2.4's disclosure — that D50's carbon-0
> closure rests on an uncited number — stays on the record and on the `ccs_retrofit_screen` matrix
> row, where this lane has now put it. Defensible, and strictly better than (B).
>
> **Precondition on any arming path:** the widened ATB extract and its source-consistency test
> (D64 STOP 6), because Act B is the half that carries a value.
>
> **Blast radius if armed:** every forecast bare key re-keys (the (b′-1) declared-flip pattern, the
> frozen drop value staying `"False"`); backcast and every horizon ending before 2028 are
> byte-identical by construction. Solve cost, per D64 §3: NEISO 8 min, NYISO 12, GOLDEN-3 33, with
> PJM and CAISO owed anyway under Q42.

### 8.3 What this lane did NOT do, stated so it is not assumed

Nothing is armed. No default moved. No constant changed. No keeper, sidecar, determination or
dashboard row moved. NYISO and GOLDEN-3 were not solved (their triggers did not fire, §4.4), PJM
was never this lane's arm, and Act B was not touched in any form.

---

## 3d. The LIVE hunk, pinned by a one-hunk revert — and the diagnostics gap that hid it

**The hunk.** `retirements.py::_floor_retention_merit`, changed by **capx D55 (2026-09-05)**. It
replaces key 1 of the reliability-floor retention sort — the per-unit quotient
`(FOM × multiplier × pmax × 1000) / (pmax × accreditation_fraction)` — with the class-constant
`(FOM × multiplier × 1000) / accreditation_fraction`. The two are equal in exact arithmetic and
**not** in IEEE-754: the quotient form put same-fuel units on 4–5 distinct floats at the 1e-11
level, so the tuple sort consulted the CO2 and heat-rate keys only inside a rounding bucket. D55 is
a deliberate, correct repair of that; what it also does, necessarily, is **change the sort order**.

**The proof.** A copy of the exact tree the HEAD control ran on, with **only** that hunk reverted
(verified: `diff -r` over `src/` reports exactly one differing file, and within it exactly this
hunk), re-solved NEISO 2026–2027:

| 2027 | `retirements` | `reserve_margin` | gas_cc after |
|---|---|---|---|
| old source `9e48ff6` | 33 rows / 2,369.81 MW | 0.045867 | 10,713.803 |
| committed control | 33 rows / 2,369.81 MW | 0.045867 | 10,713.803 |
| **HEAD minus D55** | **33 rows / 2,369.81 MW** | **0.045867** | **10,713.803** |
| HEAD control | 40 rows / 2,244.89 MW | 0.050821 | 10,838.721 |

Reverting one hunk restores the pre-drift result exactly. 2026 is identical across **all** of them
— ledger *and* the full dispatch parquet, all 12 columns — so the hunk first bites in 2027's
`evolve_fleet`, and nothing else in the 58-file diff contributes.

**Why `floor_retained` shows nothing — a second finding, independent of this lane.**
`floor_retained` (and its `year_YYYY_floor_retentions.json` sidecar) is `[]` in **every** year on
**both** sides, which is what made the sort key look inert and is a large part of why the audit
missed it. The reason is that `_apply_reliability_floor` has **three call sites and only two are
logged**: the returns at `retirements.py:2565` and `:3486` become `floor_retention_log`, but the
call at **`:2517` discards its return**. That third call is the pipeline **admission-cap** screen —
it is invoked for its side effect (it mutates the `scheduled` set in place) against a look-ahead
`cap_fleet` at `cap_year`. So the floor *does* un-retire units there, D55's ordering decides
**which**, and none of it appears in the ledger or the sidecar.

That is the causal chain, end to end: D55 re-orders the retention sort → the un-logged
admission-cap floor pass un-retires a different set → a different set of 2027 retirements is
admitted (7 rows, −124.92 MW of gas_cc) → the 2028 retrofit screen sees a different fleet.

**Two items routed to the director, neither of them this lane's to fix:**
1. **Every forecast bundle solved before D55 is stale against HEAD.** The committed `neiso-t1f`
   ledger no longer describes what HEAD produces from its own recipe, and the change is material
   (an almost disjoint gas-CC economic-exit set in 2027). This is a blast-radius question of
   exactly the kind D60-R2 is already handling; this finding hands it a **reproducible instrument**
   (the `git archive <sha> src scripts configs` + `MARKET_SIM_DATA_ROOT` probe used here) and a
   measured magnitude rather than a suspicion.
2. **The reliability floor under-reports itself.** One of its three call sites — the one that
   decides admission-cap retentions — writes nothing to `floor_retained`, so the diagnostic that
   exists to make floor behaviour visible is blind to it (rules 17 `[R-FLOOR-WINDOW]` and 19
   `[R-ONE-MECH]` both depend on that visibility). Capturing that return would have made this drift
   self-evident.

**And one correction to the G-DRIFT protocol itself, earned here.** Rule 29(b) already says
*classify every changed **hunk***. The failure mode this lane demonstrates is the tempting
shortcut: on a large file whose *new* functions are all gated, concluding the *file* is inert. The
audit checklist needs one more explicit line — **"for every changed hunk that modifies an EXISTING
function, name the gate or show the arithmetic; a file-level verdict is not admissible"** — because
that is precisely the hunk class that produced a LIVE change here.
