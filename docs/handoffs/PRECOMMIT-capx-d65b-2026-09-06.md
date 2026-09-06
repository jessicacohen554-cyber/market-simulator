# PRECOMMIT — capx D65-B: the coupled arming (Act A + Act B), one PR, one re-key

**Session:** capx D65-B · **Date:** 2026-09-06 · **Branch:** `claude/capx-d65b-coupled-arming-m4mzgv`
**Authority:** OWNER RULING **Q47** (capx ledger §3, r#42 amendment 2, verbatim option
*"Arm coupled, after D60-R3"*), released by r#46 am.1.
**Charter:** `FINDING-capx-d65-2026-09-05.md` §8.1 (why never Act A alone) and §9 (the six items);
`FINDING-capx-d64-2026-09-05.md` §2.4 (the level) and §4.5 closing clause.

Everything in this document is written **BEFORE the screen solve**. Its purpose is that no key,
no gate threshold and no expected direction can be chosen after seeing a result.

---

## 0. Preconditions, checked

| Precondition | Source | State |
|---|---|---|
| 1 — D60-R3 MERGED (#5038) | `git log origin/main` | **MET** (`15631b8c` closes the finding) |
| 2 — D77 CCS emission-rate seam fix MERGED (r#46 am.1, for item 6 only) | `git log origin/main --grep=D77` | **MET** — `ae8dd2a0`, an ancestor of this branch |

Both preconditions hold at branch creation, so items 1–5 and item 6 are unblocked in one pass.
The branch is cut FRESH off `origin/main` at `6887484f`.

---

## 1. The two acts

**Act B — a VALUE re-identification.** `ccs_retrofit_vom_adder` **8.0 → 2.95 $/MWh (2026$)**.
Read off the SAME ATB 2024 v4.0.0 basis as the screen's other two cost legs (capx D41 §2.3's rule:
host and island on ONE basis):

```
ATB Moderate NG 2-on-1 CC (F-Frame) 95% CCS  Variable O&M @2026 = 4.8
ATB Moderate NG 2-on-1 CC (F-Frame)          Variable O&M @2026 = 2.1
(4.8 − 2.1) × 1.090947  (2022$ → 2026$, constants.INFLATION_RATE) = 2.9456 → 2.95
```

NETL Rev 4a's 2.23 $/MWh (B31A→B31B.90) is the **cross-check**, not the basis. The shipped 8.0 was
`needs-citation`, stated no dollar-year, and cited a document that publishes 2.23.

**Act A — a (b′-1) DECLARED DEFAULT FLIP.** `ccs_retrofit_fixed_cost_co2_scaling` dataclass default
`False → True`; the frozen cache-key drop value stays `"False"`; the flip is declared in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` dated `2026-09-06`.

**Why coupled** (D65 §8.1): Act A multiplies Act B's level by `k`, so arming the shape on an uncited
2.7× level compounds the error on exactly the high-`er` hosts the seam exists to re-price. Neither
half is admissible alone.

**DIRECTION, STATED BEFORE ANY SOLVE (rule 23):** re-identification makes retrofits **EASIER**.
Rule 14 `[R-ACCURATE]` keeps an accurate value whichever way it moves the answer.

---

## 2. Item 1 — the widened extract (D64 STOP 6), completed BEFORE Act B

* Source: OEDI `ATB/electricity/csv/2024/v4.0.0/ATBe.csv`, **102,696,929 B**, sha256
  `567dde9d85caa759bc3f2e42c9aa14a5f85e471ca4133ccc522e7a92e020297a` — **byte-for-byte the pinned
  source the committed extract already came from.** No new source, no new vintage.
* `fetch_nrel_atb.py` gains `EXTRA_PARAMETERS_BY_TECHNOLOGY = {"NaturalGas_FE": ["Variable O&M",
  "Heat Rate"]}` — a **per-technology** scope, so no other technology's row set grows.
* Regenerated `atb_2024v4_electricity_filtered.part{00..11}.csv`: **3,858 → 4,554 rows**.

**The regeneration is a STRICT SUPERSET, verified not asserted:**

| check | result |
|---|---|
| committed keys present in the regeneration | 3,858 / 3,858 |
| old-only keys (dropped) | **0** |
| `value` differing on a common key | **0 / 3,858** |
| `display_name` / `default` / `atb_year` differing | **0** |
| new-only keys | 696 = NaturalGas_FE × {Variable O&M, Heat Rate} (348 each) |

⇒ `NEW_ENTRY_COSTS` and `TECH_COST_MULTIPLIERS` **cannot move**, and
`tests/unit/config/test_atb_entry_cost_consistency.py` passes untouched.

**The asserted derivation** (`tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py
::TestRetrofitVomBasis`) pins `ccs_retrofit_vom_adder == derive_ccs_retrofit_vom_adder()`. It was
written and run BEFORE Act B and **failed for exactly the right reason** (`8.0 != 2.95`), which is
the evidence that item 1 is a precondition and not a rationalisation.

**A cross-check the widening closed as a by-product.** ATB's own unabated NG 2-on-1 CC (F-Frame)
**Heat Rate @2026 = 6.3 MMBtu/MWh**, which is exactly `min(HEAT_RATE_BINS["gas_cc"].values())` —
the `hr_ref` inside `ccs.ccs_retrofit_captured_ref_t_per_mwh` (the D50 seam-1 reference host). The
capex increment's host and the captured-flow reference host are now provably ONE host, from the
pinned bytes rather than by coincidence. Asserted by
`test_atb_host_heat_rate_is_the_seam_reference_host`.

---

## 3. THE RE-KEY, PRE-DECLARED

Act B is not a `_CACHE_KEY_OPTIONAL_FIELDS` member, so it has no drop value and **re-keys every
config unconditionally** (D65 §9 item 3; D41 §6.2's mechanic). Act A's own contribution is the
(b′-1) flip. Measured at HEAD, before any solve:

| ISO | mode | PRE-D65B | POST-D65B |
|---|---|---|---|
| CAISO | forecast | `0b0182cbddaa94af` | `2f3e1df634cae1d8` |
| CAISO | backcast | `0a71eefc01ae72b9` | `efebcc735768c122` |
| ERCOT | forecast | `b5ab30d0fae9f8a3` | `95d789d6dfb98831` |
| ERCOT | backcast | `65b24e52e89a348c` | `406cb30ad62bc27b` |
| MISO | forecast | `91be1877a6594913` | `6808780f515fce63` |
| MISO | backcast | `00263fcf15266128` | `b10d58628ba3a057` |
| NEISO | forecast | `51e4d85962487d16` | `31ca8b9d010f7e7f` |
| NEISO | backcast | `05e95034df140bbc` | `27e80d27acd995de` |
| NYISO | forecast | `20a7d5244dfa70ee` | `8e87bfe58f75212a` |
| NYISO | backcast | `b791330712d6c2fe` | `cadaba3d344e84b9` |
| PJM | forecast | `2c5d56102b3057bb` | `eaa3fbef5ff182c9` |
| PJM | backcast | `6f61207df8f4b398` | `3a566deac3a85682` |
| (global default) | forecast | `e5ecd4105ada3e58` | `547053bdfccd4264` |
| (global default) | backcast | `6a2845e50951394e` | `f61891696e671969` |

The PRE column is reconstructed at HEAD as
`ScenarioConfig(..., ccs_retrofit_vom_adder=8.0, ccs_retrofit_fixed_cost_co2_scaling=False)` — the
explicit `False` drops on the frozen drop value, so the config hashes as a pre-flip one. **It is
faithful**: its ERCOT forecast entry `b5ab30d0fae9f8a3` and the two global entries reproduce the
pins currently committed in `test_ercot_stageb_arming.py` / `test_persisted_identity.py` exactly.

**BACKCAST BEHAVIOUR IS BYTE-IDENTICAL** and so is every hindcast/crossover horizon ending before
2028: `ccs.py::apply_ccs_retrofit` returns at `if year < config.ccs_retrofit_available_year` (2028)
before any read of either field, and that call site is the only consumer of both. The backcast KEY
moves (a one-time cache MISS); no keeper, sidecar, determination or dashboard row does — committed
artifacts are files, not cache lookups. **No backcast keeper is re-solved by this lane.**

### 3.1 The STOP "the explicit-`False` path moving a key" — DOES NOT FIRE, and here is the decomposition

Read literally, that STOP would fire on a consequence the charter itself licenses (D65 §9 item 3:
Act B "re-keys every bare key unconditionally … there is no drop value to hide behind"). The STOP's
real content is that **Act A's drop-value mechanic must be intact**, which is measured by holding
the VOM at its shipped level:

| arm | explicit `seam 4 = False` key |
|---|---|
| **Act A alone** (`vom_adder` held at 8.0) | **`e5ecd4105ada3e58`** |
| pre-flip forecast default (the committed pin) | `e5ecd4105ada3e58` |
| both acts (HEAD) | `910b8cfcb2aa6a36` |

**Act A alone leaves the explicit-`False` path on the pre-flip key exactly.** The movement at HEAD
is Act B's, and it is unconditional by construction. STOP not fired.

---

## 4. A DEFECT THE CHARTER DID NOT ANTICIPATE, found and repaired before the screen

**What happened.** Act A's flip made the pair *(seam 1 EXPLICIT `False`, seam 4 at its default)*
**unconstructible**, because `__post_init__` refused seam 4 without seam 1. That pair is not
hypothetical — it is what the **D50/Q42 CONTROL ARM ITSELF** is
(`ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)`, pinned by `test_d60_arming_batch.py`'s
*"(b′-1)'s useful inverse: a control arm keeps its bundle"*), plus **six committed bundles**:

`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing`,
`…/miso-2021-2025-realized-t1h-d53-sectorgate`, `…-d51ratio`,
`results/calibration/caiso251_arm_nomargin`, `…/nyiso192_astoria_panel`, `…/miso217_intermphys_B`.

All six carry `ccs_retrofit_capex_co2_scaling: false` with seam 4 **absent**. At the charter-literal
flip, reconstructing any of them raises — i.e. **the flip would have made the D50 control
unreachable**, which is the one thing rule 29(b) needs a control to be.

**Why the charter missed it.** Its line *"the validator's seam-1 requirement is satisfied because
Q42 armed seam 1"* is true of the DEFAULT path and says nothing about the explicit-seam-1-off path.

**The repair, and why it is the minimal one.** The distinction the guard actually wants is
**explicitness, not value**, and `__post_init__` provably cannot see it — it runs after binding,
which is the exact defect the repo's own `_scenario_config_init` / `_explicitly_set_fields` record
was built to fix (its docstring says so). So the pair resolution moves to that wrapper
(`_resolve_ccs_retrofit_fixed_cost_pair`):

* **explicit `seam 4 = True` with seam 1 off** → still **RAISES** (the incoherent ask; rule 24).
* **seam 4 at its default with seam 1 off** → **DEMOTED to `False`**: inert by construction
  (`k ≡ 1.0`), so this is the truthful record, and it drops from the hash on the frozen `"False"`
  drop value.
* **provenance unknown** (`dataclasses.replace`, `from_yaml` over a full dump re-pass every field)
  → demote, the same fallback convention `_explicitly_set_fields` already uses.

The dead `if …: raise` block in `__post_init__` is **deleted, not zeroed** (rule 26 `[R-DELETE]`).

**Verified:** all six bundles reconstruct with `seam 4 → False`; the explicit incoherent pair still
raises; and §3.1's decomposition (Act A alone → `e5ecd4105ada3e58`) is measured *through* this
repair, so the drop-value mechanic is intact under it.

**No solve-affecting behaviour changes for any armed config**: the default path is untouched
(seam 1 is on, so no demotion branch is reachable), and the demoted path is the one where seam 4
was inert anyway.

---

## 5. G-DRIFT (rule 29(b) doctrine), audited BEFORE the screen

`git diff <keeper sha> 6887484f -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference`, plus `constants.py` **first** (a matched cache key
is NOT a G-DRIFT verdict — `constants.py` is outside the key).

**Verdict: form 4 is VOID. A LIVE hunk exists, so the screen earns its control solve.**

| named hunk | classification | evidence |
|---|---|---|
| **SCN-LOAD `d14a7ed0`** (`DEMAND_GROWTH_RATES`, all six ISOs) | **LIVE** | Ancestry checked per incumbent: `9e48ff6` (ercot/neiso t1f), `2ef4326e` (miso), `e7412237` (nyiso), `b83e96ca` (caiso) are **PRE-hunk**; only `14f860fb` (pjm) and `e9d8263b` (GOLDEN-3) carry it. `constants.py` is outside the cache key, so a matched key would not have revealed this. |
| **wallclock P1 basis seed #5033** (`pipeline/solve.py`, `lp/model.py`) | INERT for the forecast path — timing/diagnostics accounting only | rule 29(b)'s "pure timing/diagnostics accounting" class |
| **D77 `ae8dd2a0`** (CCS retrofit emission-rate seam) | **LIVE**, and squarely in this seam | it is why r#46 am.1 made D77 a precondition of the batch: a converted unit's captured rate was being re-booked over by `campd_bins.apply_plant_emission_rates{,_v2}` after `evolve_fleet` |

**Consequences, stated at the gate rather than discovered later:**

1. The screen (item 5) uses a **same-HEAD ERCOT t1f control**, exactly as the charter pre-authorised
   — the committed ERCOT t1f is pre-hunk on `d14a7ed0` and cannot serve as form-4 control.
2. The batch's **board-level before/after is confounded by the demand vintage** for the four
   pre-hunk ISOs. This is reported at full magnitude and attributed, never netted. The clean
   comparison in this lane is the screen's arm-vs-same-HEAD-control differencing.
3. **The batch lands the whole T1-F board in ONE demand vintage — that is now one of its
   purposes**, and it is why the confound does not persist past this lane.

A second G-DRIFT re-audit is owed **before the batch** (r#46 doctrine) and will be recorded as an
addendum to this document.

---

## 6. Item 5 — the rule-29 SCREEN, pre-registered

**One leg, one year, on a CARBON-0 ISO.** RGGI ISOs are cap-bound on both constructions and cannot
discriminate (D65 §8.1), so NEISO is uninformative here. **Screen = ERCOT t1f** (~12 min), with a
**same-HEAD ERCOT t1f control** (§5 consequence 1).

**Screen year named before the screen runs:** the screen is the ERCOT t1f horizon's first retrofit
years, where D64 §2.4's census puts the mechanism's own measured footprint largest — **10.19 GW at
the ceiling in 2028 under Act B on the shipped shape, and 5.68 GW in 2029 under Act A + B** — never
the year with the biggest residual.

**The gate is STRUCTURAL and a STOP gate ONLY. It may kill the arm; it may never promote it.**
It is not gated on any residual.

| # | pre-registered structural gate | STOP if |
|---|---|---|
| G1 | every row that clears is an `er/phys` ≥ 1.27 host (D49 §1.3) | a row clears on an `er/phys` < 1.27 host |
| G2 | the identity `uplift/capex ∝ 1/k` holds on the cleared set | it does not |
| G3 | `k = 1` rows are byte-identical to the control | any `k = 1` row moves |
| G4 | no non-target load-bearing FC row flips PASS → FAIL | one does |
| G5 | the dispatch response has the direction and order of magnitude the pre-solve delta implies | it does not |
| G6 | wall/RSS within the leg's D60 envelope | beyond it |

**A carbon-0 ISO GAINING rows is NOT a STOP.** It is the accurate level's **pre-registered
signature** (D64 §4.5's closing clause, D65 §9 item 4). Recording it here, before the solve, is what
stops it being read as a regression afterwards.

Both screen bundles are **DELETED from `results/calibration/` before the PR merges** (rule 29(c),
owner ruling R-AV): every number this lane will ever cite from them lives in this document and in
`FINDING-capx-d65b-2026-09-06.md`, and git history is the record for the bytes.

---

## 7. Item 6 — the batch, pre-declared

Screen cleared **AND** D77 merged (both required). Sequential per rule 12 `[R-PARALLEL]`:

`ercot-t1f` → `neiso-t1f` (~8) → `nyiso-t1f` (~12) → `caiso-t1f` (~23) → `pjm-t1f` (~36) →
`miso-t1f` (~65) → `neiso-t3` GOLDEN-3 (~33 min).

Each: score → verdict → register **in place**, priors preserved at **`-pre-d65b`**. Reported at full
magnitude: FC-map moves against D64 §2.4's census and D65 §4's NEISO reading; the D50 §6.2 blast
radius reconciled; D77's §8 blast radius (retrofit-carrying bundles) reconciled.

**Matrix (six shards, one appended line each, last commit):** the `ccs_retrofit_screen` row's
`def`/`note` carries Act B (**no cell verdict moves** — Act B arms no mechanism); the
`ccs_retrofit_fixed_cost_co2_scaling` row's cells re-stamp `fc: K` where the arm is now the bare leg.

---

## 8. STOPs (the charter's, restated so none is reinterpreted later)

| STOP | state at this writing |
|---|---|
| extract/test absent (STOP 6) | **cleared** — §2 |
| a realized key ≠ its pre-declared value | armed; §3 is the declaration |
| any `k = 1` row moving | armed as screen gate G3 |
| a screen row clearing on any `er/phys` < 1.27 host | armed as screen gate G1 |
| the explicit-`False` path moving a key | **does not fire** — §3.1 decomposition |
| wall/RSS beyond each leg's D60 envelope | armed as screen gate G6 |

## 9. Scope discipline

Rules **22** (forecast mode only — no held-out year is solved, scored or registered by this lane),
**25** (a posture, no ISO's number crosses a boundary), **27** (exact on-disk bytes; blob-verify
every ≥300-line file after every push), **28**, **29**. Collisions: D60-R4 then D63 are the board
writers until they merge — **this batch registers AFTER both**. SCN lanes write the hindcast
namespace only. In `scenarios.py` this lane's lines sit in the D50 block; SCN-WS2a/2b's
`federal_ces_*` block and WS-1a's D34-guard region are not this lane's. Score and register **after
the final rebase**.

---

## ADDENDUM A (2026-09-06, written BEFORE the control leg solves)

### A.1 Bare keys vs t1f SOLVE keys — the two are different objects

§3's table pre-declares the **bare** keys, `ScenarioConfig(iso=…, mode=…)` at its defaults, which is
what the charter asks the batch to re-solve and re-register. A **t1f solve key is not a bare key**:
`run_full_horizon.py` pins `start_year`/`end_year` (2026/2030) and `capacity_market_clearing=False`
onto the resolved config, and those fields are in the hash. The committed pre-D65-B ERCOT t1f
demonstrates the same thing — it sits at `0c3e9cd5b5993bdf`, not at its own bare key
`b5ab30d0fae9f8a3`.

Stated here so the STOP *"a realized key ≠ its pre-declared value"* is read against the right
object. It is checked two ways, both of which hold:

* the ARM's realized bundle key **recomputes to `d0fb7534671b4c91`** from its own written
  `config.yaml`; and
* the §3 bare-key table is re-verified independently at the batch (each leg's bare key is resolved
  before its solve).

### A.2 The CONTROL leg's key, DECLARED BEFORE IT RUNS

Taking the ARM's own resolved config and undoing exactly the two acts
(`ccs_retrofit_fixed_cost_co2_scaling=False`, `ccs_retrofit_vom_adder=8.0`):

> **CONTROL key MUST be `6cfa33538294713c`** — ARM is `d0fb7534671b4c91`.

If the control leg lands on any other key, the two legs differ by something besides the two acts and
the screen's differencing is void. That is a STOP.

### A.3 Independent confirmation that G-DRIFT form 4 was correctly VOIDED

Diffing the committed pre-D65-B ERCOT t1f config against this arm's: **23 fields differ.** Only
**2** are this lane's acts. **20** are `absent → default` schema growth (fields registered since
that bundle was solved). One is a genuine HEAD drift of a solve-path field:
`capacity_market_clearing_by_iso: {CAISO,MISO,NEISO,PJM: True} → None` (inert for ERCOT, which
carries no capacity market and is absent from the dict either way — but it is drift, not identity).

So the committed bundle could not have served as a form-4 control on its config either, quite apart
from the SCN-LOAD `DEMAND_GROWTH_RATES` hunk §5 already found LIVE. **The same-HEAD control leg is
the correct instrument**, and it differs from the arm by exactly the two acts — which A.2's key
declaration is what makes checkable.

---

## ADDENDUM B (2026-09-06) — main moved mid-session; the batch's G-DRIFT re-audit

**What happened.** This lane's PR **merged to `main` as #5112 (`b1f77621`) while the screen was
running**, and fourteen other lanes merged with it. `origin/main` moved `6887484f → d1aa877f`.
Both acts are therefore LIVE on `main`: `ccs_retrofit_vom_adder = 2.95`,
`ccs_retrofit_fixed_cost_co2_scaling = True`. Items 1–4 are complete and merged.

Per the merged-PR rule a merged PR cannot track follow-up work, so items 5–7 continue from a branch
restarted off the new `main`. **D60-R4 (`4baf36ff`) and D63 (`ce1f7ec9`) both merged in the same
window, so the charter's collision constraint — "your batch registers AFTER both" — is satisfied.**

### B.1 The §3 bare-key declaration STILL HOLDS at the new main

Re-measured against an INDEPENDENT extract of `origin/main`'s `src` (`git archive origin/main src`,
imported with the repo's own tree off `sys.path` — the first attempt silently resolved back to the
working tree through the editable install's `.pth`, and was discarded):

| ISO | §3 declared POST-D65B | measured at `d1aa877f` |
|---|---|---|
| CAISO | `2f3e1df634cae1d8` | `2f3e1df634cae1d8` |
| ERCOT | `95d789d6dfb98831` | `95d789d6dfb98831` |
| MISO | `6808780f515fce63` | `6808780f515fce63` |
| NEISO | `31ca8b9d010f7e7f` | `31ca8b9d010f7e7f` |
| NYISO | `8e87bfe58f75212a` | `8e87bfe58f75212a` |
| PJM | `eaa3fbef5ff182c9` | `eaa3fbef5ff182c9` |
| global forecast | `547053bdfccd4264` | `547053bdfccd4264` |
| global backcast | `f61891696e671969` | `f61891696e671969` |

**Fifteen lanes merged and not one moved a bare forecast key.** The STOP *"a realized key ≠ its
pre-declared value"* does not fire, and no re-declaration is owed.

### B.2 The re-audit — every hunk INERT, gate named (r#46 doctrine + D65 §3d's correction)

`a5c30c6a → d1aa877f` over `src/market_sim`, `scripts/run_full_horizon.py`, `scripts/lib`:
**13 files, +630/−7.** A matched cache key is NOT a G-DRIFT verdict, so this is a CODE audit, and
per D65 §3d **every hunk that modifies an EXISTING function names its gate or shows its arithmetic
— a file-level verdict is inadmissible.**

| file | hunk class | verdict | the gate |
|---|---|---|---|
| `config/constants.py` | 2 import lines | INERT | no value changed; imports a symbol |
| `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | `__all__` / re-export | INERT | no call site |
| `capacity_evolution/evolve.py` | +1 additive ledger key in an EXISTING fn | INERT | `if _econ_sink.get("no_default_cap_price_takers")` — the sink is empty off the D74 gate |
| `config/scenarios.py` | 3 NEW fields | INERT | `nyiso_gas_bridge_startup_aware=False`, `miso_gas_marginal_commodity_pricing=False`, `capacity_no_default_cap_convention_by_iso=None`. **No existing field's default moved; no new `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry; `iso_configs.py` is ABSENT from the diff, so none is armed for any ISO** |
| `config/capacity_market.py` | new resolver | INERT | `resolve_capacity_no_default_cap_convention` **measured `False` for all six ISOs** at their resolved forecast defaults |
| `data/avoidable_cost_rate.py` | new fn `no_default_cap_class` | INERT | additive; reached only from the gated retirements limb |
| `capacity_evolution/retirements.py` | **4 hunks in the EXISTING `apply_economic_retirements`** | INERT | every one guarded by `no_default_cap_armed` = `published_bar_armed AND year is not None AND resolve_…(config, iso)`, which is `False`. The `continue` that would skip a unit is inside that guard, so the screen's candidate set is unchanged |
| `model/commitment.py` | new param on the EXISTING `caiso_ra_mustoffer_min_gen` | INERT | `screen_stats: dict \| None = None`; every write guarded `if screen_stats is not None`; its own docstring states it is never read by the floor arithmetic |
| `pipeline/commitment.py` | hunks in the EXISTING `_nyiso_gas_bridge_floor` | INERT | `startup_aware=False` ⇒ `need_econ = startup_bridge` (its prior value) ⇒ `p1_prices`/`base_mc` unchanged; `screen_stats=None`; census block skipped |
| `data/fuel/resolve.py` | **UNCONDITIONAL call added to an EXISTING fn** | INERT | the gate is in the CALLEE, so the call site alone is inadmissible: `apply_miso_gas_marginal_commodity` returns `None` at its first statement (`if not getattr(config, "miso_gas_marginal_commodity_pricing", False): return None`) **before any mutation**, so `if spot_cells is None:` falls through to the pre-existing `apply_miso_winter_citygate_daily` |
| `data/fuel/basis/miso.py` | new fn + helpers | INERT | same gate |
| `scripts/run_full_horizon.py` | new CLI flag | INERT | `--capacity-no-default-cap-convention`, `default=None` ⇒ field stays `None` unless passed |

### B.3 THE CONSEQUENCE: the screen does NOT need re-running

The screen's ARM and CONTROL both solved at `a5c30c6a`, and B.2 shows the delta from there to
`d1aa877f` is **inert for a default forecast run**. So the screen's differencing remains valid at
the new HEAD and its verdict transfers; re-solving both legs would re-measure an established
identity at 30 minutes of LP. (§5's finding is untouched: form 4 against the *keepers* stays VOID —
their shas are pre-SCN-LOAD — which is a different question from this one.)

---

## ADDENDUM C (2026-09-06, session **D65-B-R**) — the batch's PER-ISO structural gates, written BEFORE any leg solves

**Authority.** Director adjudication r#48 §3(a) (`capx-director-ledger-2026-08.md` §0as.3):
D65-B's G1 and G3 were **charter defects** — G1's `er/phys ≥ 1.27` floor is D64 §2.4's **PJM/MISO**
host band transcribed onto an ERCOT screen, and G3's `k = 1` invariance is an **Act-A** property
applied to a coupled arm. The ERCOT screen is **NOT re-run**; its numbers stand as measured
(FINDING-capx-d65b §6). The batch proceeds under gates **re-derived per ISO from D64 §2.4's own
rows**, which were written 2026-09-05 — before any of this lane's solves. *That committed-in-advance
provenance is the entire guard against gaming: every threshold below is a quotation, not a choice.*

**Nothing in this addendum is gated on a residual.** Every gate is STRUCTURAL and **STOP-only**: it
may kill a leg; it may never promote one, and it contributes to no determination (rule 29).

### C.0 What Step 0 and Step 1 established, before the gates

**Step 0 — G2 is now evaluable.** The `retrofit_log` scaling record (`capex_scale`,
`fixed_cost_scale`, `retrofit_capex_per_mw`, `annual_net_savings_per_mw`, `vom_adder_per_mwh`,
`old_hr`, `old_emission_rate`) is persisted onto every `ccs_retrofits` ledger row. D65-B's G2 was
*not evaluable at all* from committed artifacts; it is now read straight off the bundle, and the
`er`/`k` columns no longer need offline CAMPD reconstruction. Asserted cache-neutral: no
`ScenarioConfig` field bears any of these names and none is a `cache_key_drop_defaults()` member.

**Step 1a — THE RE-PIN HOLDS. All 14 bare keys UNMOVED at HEAD** (`2485e611` + step 0), measured
against PRECOMMIT §3's POST-D65B column through `apply_iso_scenario_defaults(ScenarioConfig(iso,
mode))`:

| CAISO | ERCOT | MISO | NEISO | NYISO | PJM | global |
|---|---|---|---|---|---|---|
| fc `2f3e1df634cae1d8` bc `efebcc735768c122` | `95d789d6dfb98831` / `406cb30ad62bc27b` | `6808780f515fce63` / `b10d58628ba3a057` | `31ca8b9d010f7e7f` / `27e80d27acd995de` | `8e87bfe58f75212a` / `cadaba3d344e84b9` | `eaa3fbef5ff182c9` / `3a566deac3a85682` | `547053bdfccd4264` / `f61891696e671969` |

**14 / 14 UNMOVED.** No re-declaration is owed and no moving hunk has to be named.

**Step 1b — G-DRIFT `002cfa8d → 2485e611`, hunk by hunk, `constants.py` FIRST.**
`constants.py`: **ZERO hunks** — the check that a matched cache key cannot make (it is outside the
key). Scope `src/market_sim scripts/run_calibration*.py scripts/run_full_horizon.py scripts/lib
data/raw/_validation-source data/raw/reference` = 13 files, +733/−54. Per D65 §3d, every hunk in an
EXISTING function names its gate or shows its arithmetic; a file-level verdict is inadmissible.

| file | hunk class | verdict | the gate, MEASURED |
|---|---|---|---|
| `config/constants.py` | — | **INERT** | no hunk exists |
| `config/scenarios.py` | 2 NEW fields | **INERT** | `miso_gas_variable_transport=False`, `miso_seam_neighbour_anchored_ladder=False`; both registered `_CACHE_KEY_OPTIONAL_FIELDS` at drop `"False"`; **no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry**, and `iso_configs.py` is ABSENT from the diff, so neither is armed for any ISO |
| `capacity_evolution/retirements.py` | **6 hunks, 4 in the EXISTING `apply_economic_retirements`** | **INERT** | D78's `exit_exempt_unit_ids`. The filter is `if exit_exempt_unit_ids: margins = [...]`; the set is fed from `sector_gated_unit_ids` under `retirement_sector_gate`. **Measured at all six ISOs' resolved forecast configs: the gate is `False` everywhere except MISO, and MISO's `resolve_capacity_market_supply_clearing` is `False`** (PJM is the converse: clearing `True`, gate `False`). **The arming intersection is EMPTY.** With the clearing off the D78 construction is byte-identical to the pre-D78 `exempt_unit_ids` union — not asserted, *executed*: `test_capacity.py::test_exit_exempt_is_byte_identical_to_exempt_when_the_clearing_is_off` passes under both decision rules |
| `results/cache.py` | epoch note only | **INERT** | prose; no code hunk. Its own blast radius states MISO's gate-on bundles are NOT invalidated, for the reason measured above |
| `model/commitment.py` | 2 hunks in the EXISTING `caiso_ra_mustoffer_min_gen` | **INERT** | `screen_stats["per_unit"]` writes, all under `if screen_stats is not None`. The `kept_set`/`drop_h` extraction is the **same sum** hoisted out of the guard — arithmetic-identical, a wasted add, not a behaviour change |
| `pipeline/commitment.py` | 3 hunks in the EXISTING `_nyiso_gas_bridge_floor` | **INERT** | the per-plant census is guarded `if startup_aware and plant_census`; `nyiso_gas_bridge_startup_aware` measured `False` at all six ISOs |
| `model/interchange/spec.py`, `interchange/miso.py` | new param on an EXISTING fn + a new table | **INERT** | `neighbour_anchored: bool = False`, fed only from `miso_seam_neighbour_anchored_ladder` (measured `False` at all six). Off ⇒ `ladder` is the incumbent object unchanged |
| `data/fuel/basis/miso.py` | new fns + 3 call sites in an EXISTING fn | **INERT** | double-gated: each site is `if getattr(config, "miso_gas_variable_transport", False)`, inside `apply_miso_gas_marginal_commodity`, which returns at its own first statement unless `miso_gas_marginal_commodity_pricing` (measured `False` at all six) |
| `scripts/run_calibration.py` | CLI + a validator | **INERT** | backcast entry point; this lane runs `run_full_horizon.py` only. `run_full_horizon.py` has **no hunk in this window** |
| `data/raw/reference/miso_gas_variable_transport{,.pool}.csv` | new data | **INERT** | read only under the gate measured `False` above |
| `capacity_evolution/evolve.py`, `results/evolution_ledger.py` | this lane's own step 0 | **INERT** | additive ledger keys; C.0 above |

**VERDICT: every hunk INERT. Zero LIVE.** No control solve is earned (rule 29(b)) and G-CTRL
**form 4** — differencing against the incumbent's committed numbers — is VALID for this batch.

**Step 1c — an INDEPENDENT confirmation, stronger than the bare-key match.** For all seven legs,
undoing *exactly the two D65-B acts* on the leg's own HEAD-resolved config reproduces its
**committed pre-D65-B bundle key to the digit**:

| leg | committed pre-D65-B | **D65-B-R SOLVE key (pre-declared)** | acts undone at HEAD |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | **`9b9e5a48e3ca5c8e`** | `0c3e9cd5b5993bdf` ✓ |
| `neiso-t1f` | `18515067bf4d2fbe` | **`c3519b861f920bbe`** | `18515067bf4d2fbe` ✓ |
| `nyiso-t1f` | `19a9690bb12c8459` | **`f62431376dd9df03`** | `19a9690bb12c8459` ✓ |
| `caiso-t1f` | `29f8eb372810195f` | **`17770cdad3230938`** | `29f8eb372810195f` ✓ |
| `pjm-t1f` | `09996eca71ee80fd` | **`43cee1c9558ab859`** | `09996eca71ee80fd` ✓ |
| `miso-t1f` | `b1a73a087064ffd8` | **`74359fedbf2eadd6`** | `b1a73a087064ffd8` ✓ |
| `neiso-t3` GOLDEN-3 | `f04fd06348e1623d` | **`0fc42cb56c24d544`** | `f04fd06348e1623d` ✓ |

7/7. So the recipe reconstructed here **is** the incumbents' recipe, and the *only* thing moving
each solve key is the two acts. **A realized bundle key ≠ its pre-declared value above is a STOP.**

### C.1 A DISCREPANCY THIS SESSION FOUND, recorded before it can matter

**D65-B's screen ran WITHOUT `--golden-posture`, so it screened a different config from the one the
batch's ERCOT board row carries.** Measured by rebuilding the screen's own HEAD (`a5c30c6a`) out of
`git archive` and enumerating the recipe grid:

| recipe at `a5c30c6a` | armed key | acts-undone key | |
|---|---|---|---|
| `golden_posture=True,  cmc=False` | `9b9e5a48e3ca5c8e` | `0c3e9cd5b5993bdf` | = **the batch's ERCOT leg** |
| `golden_posture=False, cmc=False` | **`d0fb7534671b4c91`** | **`6cfa33538294713c`** | = **D65-B's ARM and CONTROL exactly** |

Both of the screen's declared keys reproduce on the **shipped**-posture row, neither on the golden
one. Consequences, stated at the gate rather than discovered later:

1. The screen's arm-vs-same-HEAD-control differencing is **valid, for the shipped posture**. Its
   mechanism evidence is untouched: a control of 0 rows in every year reproducing D64 §2.4's ERCOT
   census, an arm of 7 rows at `er/phys` 0.9458–1.0000, the 2030 cap binding exactly.
2. **The ERCOT leg below is therefore the FIRST golden-posture measurement of the coupled arm.** It
   is gated on its own rows through C.2, not on the screen's, and its numbers are reported at full
   magnitude against D64 §2.4 — never netted against the screen's.
3. The ERCOT golden-posture key is **identical at `a5c30c6a` and at HEAD** (`9b9e5a48e3ca5c8e`),
   which independently re-confirms Step 1b across the whole window rather than only from `002cfa8d`.

This changes no adjudication and re-opens no gate. It is recorded because a screen that screened a
neighbouring config is a fact about the evidence, and the place for it is before the batch, not in
the write-up.

### C.2 THE PER-ISO GATES — each threshold QUOTED from D64 §2.4's own row

D64 §2.4's census is evaluated **at the hour ceiling** (every hour in merit), so its GW figures are
an **upper bound** on what a solve converts, never a target. G5' is written accordingly, and the
one direction that is *not* bounded — a ceiling of 0 — is a hard structural STOP, because nothing
can clear a bar the ceiling arithmetic says nothing clears.

**Common to every leg (structural, ISO-independent):**

| # | gate | STOP if |
|---|---|---|
| **G0'** | retrofits are inert below `ccs_retrofit_available_year` = 2028 | any `ccs_retrofits` row in 2026 or 2027 |
| **G2'** | the identity holds on the **persisted** fields: `fixed_cost_scale == capex_scale` on every row, and `retrofit_capex_per_mw / capex_scale` is host-invariant (⇒ uplift per unit of capex falls as `1/k`) | either fails on any row |
| **G3'** | `k = 1` invariance is an **Act-A-only** property, **discharged at ZERO LP** by the existing `test_ccs_retrofit.py::test_reference_host_is_invariant_on_and_off` | that test fails at HEAD |
| **G4'** | no non-target **load-bearing** FC row flips PASS → FAIL against the leg's `-pre-d65b` prior | one does |
| **G6'** | wall ≤ 2× the leg estimate AND peak RSS < 14 GB (this box is 15 GB; D60's recorded worst case is 13.27 GB) | beyond either |

**G3' is not re-measured by a solve.** Per the adjudication it is an Act-A property, a coupled arm
moves `k = 1` rows by Act B's design, and spending an LP to re-measure arithmetic that is already
proven and tested would be the defect, not the discipline.

**Per ISO — G1' (host band) and G5' (window total), quoted:**

| leg | D64 §2.4 `er/phys` band | **G1' STOP if** | D64 §2.4 predicted 2028/29/30 @ ceiling | **G5' STOP if** |
|---|---|---|---|---|
| `ercot-t1f` | **0.95–1.05** (D64's own ERCOT row) | a clearing row sits outside 0.95–1.05, at the table's two-decimal precision | **0 / 5.68 / 3.80 GW** | any 2028 row; or 2029/2030 above their ceilings |
| `pjm-t1f` | **1.27–1.49** | a clearing row outside 1.27–1.49 | **0.41 / 2.48 / 2.48 GW** | any year above its ceiling |
| `miso-t1f` | **1.26–1.39** | a clearing row outside 1.26–1.39 | **0.48 / 0.72 / 0.72 GW** | any year above its ceiling |
| `neiso-t1f` | none published (§2.4 reads **cap-bound**); §2.3 `k` 0.95–1.87 | — (no band to quote ⇒ **not gated**, reported only) | **cap-bound** | the 3 GW/yr cap does NOT bind in a year |
| `nyiso-t1f` | none published (**cap-bound**); §2.3 `k` 0.97–2.04 | — | **cap-bound** | the cap does NOT bind in a year |
| `caiso-t1f` | none published (**cap-bound**) | — | **cap-bound** | the cap does NOT bind in a year |
| `neiso-t3` GOLDEN-3 | none published | — | §2.3: *"per-tonne-dominant on both sides and NOT expected to move in kind"* | the converted set moves **in kind** (a class the RGGI ladder does not price) |

Two readings recorded so neither can be improvised afterwards:

* **A carbon-0 ISO GAINING rows is NOT a STOP** — it is the accurate level's pre-registered
  signature (D64 §4.5's closing clause; D65 §9 item 4), restated here because G1 as originally
  transcribed pointed the other way on the very same page.
* **`er/phys` > 1 flags a CAMPD-rate-above-physical tranche** (D49 §1.3's artifact). ERCOT's hosts
  sit *below* physical, so the artifact is absent there; that is why 0.95–1.05 is ERCOT's band and
  1.27–1.49 is PJM/MISO's. A band is a **window**, never a floor — the D65-B defect exactly.
* **A cap-bound ISO is expected to RE-RANK, not re-select** (D64 §2.3, D65 §4.2): MW-weighted `er`
  and `hr` fall as efficient hosts win. Reported; not gated, because the cap sets the volume.

### C.3 Execution discipline

Sequential per rule 12, one leg at a time, in charter order: `ercot-t1f` → `neiso-t1f` →
`nyiso-t1f` → `caiso-t1f` → `pjm-t1f` → `miso-t1f` → `neiso-t3` GOLDEN-3.

**HEAD guard around every leg**, so no leg can silently straddle a rebase:

```
H0=$(git rev-parse HEAD); <solve>; [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
```

Rebase **between** legs only, and re-audit each rebase delta hunk by hunk before the next leg.
Registration is the single `scripts/register_forecast_run.py` path, in place, each incumbent
preserved at **`-pre-d65b`**. Rules 12, 22 (forecast mode only — no held-out year is solved, scored
or registered), 24, 25, 27, 28, 29. This lane is the **sole writer** of
`frontend/data/forecast/ff-verdicts.json` and `program-status.json` until its last leg registers.

---

## ADDENDUM D (2026-09-06, session **D65-B-R**) — the REBASE re-audit, BEFORE the first leg

Addendum C's G-DRIFT basis was `2485e611`. **This lane's own PR merged as #5161 (`40adcbba`)
while the clean tree was rebuilding**, so steps 0–2 are on `main`, the branch was restarted from
the merged default per the merged-PR rule, and `main` moved `2485e611 → 13ee0c89` (42 commits).
**No leg had solved**, so the re-audit lands here rather than between legs. Charter duty:
*"re-audit each rebase delta hunk by hunk before the next leg."*

### D.1 `constants.py` FIRST — it HAS hunks this time, and they are label-only

+32 / −23, all inside the SCN voluntary-market region. Not classified by eye — **parsed**: every
module-level assignment (`Assign` **and** `AnnAssign`) literal-evaluated on both sides.

| | old | new |
|---|---|---|
| module-level constants | 145 | 145 |
| ADDED / REMOVED | none | none |
| **VALUE-MOVED** | — | **NONE** |

The diff is the SCN-FIX2 label move under **owner ruling S9** (*"Take the placeholders as
committed"*) and **S10** (card D-3c, *"Ratify the default as built"*): `VOLUNTARY_COMMITTED_DC_
FRACTION["mid"] = {2026: 0.5}` and the WTP ceiling `"mid": 4.5` lose the word ILLUSTRATIVE and keep
their values. **INERT** — and this is exactly the check a matched cache key cannot make.

### D.2 The rest of the delta, hunk by hunk

| file | hunk class | verdict | the gate, MEASURED |
|---|---|---|---|
| `config/scenarios.py` | 1 NEW field + a backcast coercion | **INERT** | `mass_cap_tons_by_year: dict \| None = None` (SCN-CAP, owner ruling S12). **`iso_configs.py` is ABSENT from the delta**, so no ISO arms it; measured `None` at all six resolved forecast configs |
| `policy/cap_and_trade.py` | new fn + **2 hunks in the EXISTING `_power_sector_cap` / `_published_power_sector_budget`** — and this is the RGGI/CARB path, which three of my legs enter | **INERT** | the new precedence step is `cap_tons = scheduled_power_sector_budget(config, year)` then `if cap_tons is None: cap_tons = getattr(config, "mass_cap_tons", None)` — the pre-existing line. `scheduled_power_sector_budget` returns at its first statement (`if not schedule: return None`). **Measured, not argued: it returns `None` for all six ISOs at 2026 / 2028 / 2030**, so the scalar → published → inert order is untouched |
| `data/fuel/basis/miso.py`, `scripts/run_calibration.py` | small follow-ons | **INERT** | same `miso_gas_variable_transport` / `miso_gas_marginal_commodity_pricing` gates as Addendum C, both measured `False`; `run_calibration.py` is the backcast entry point and this lane runs `run_full_horizon.py` only |
| `data/raw/reference/caiso_offer_*` (3 files) | CAISO backcast offer surfaces | **INERT** | read only under `caiso_offer_surface_*`, all `False` in the forecast recipe; a backcast calibration artifact |
| `results/cache.py`, `evolution_ledger.py`, part of `evolve.py` | epoch note + this lane's own step 0 | **INERT** | already on `main` as #5161 |
| **`capacity_evolution/retirements.py` + `evolve.py`'s exemption call site** | **capx D81 — 4 hunks in the EXISTING `apply_economic_retirements` and its caller** | **LIVE — for PJM ALONE** | see D.3 |

### D.3 THE ONE LIVE HUNK: D81, and it is live for exactly one leg

D81 re-routes **every** exemption channel through the D78 seam:
`exempt_unit_ids=frozenset()` and
`exit_exempt_unit_ids=(_retrofitted_ids | _dated_exempt | _sector_exempt)`.
Before it, the retrofit and dated-plant sets rode `exempt_unit_ids` (skipped entirely ⇒ a $0 price
taker under the D57 clearing) while only the sector-gated set rode `exit_exempt_unit_ids`.

**With the D57 clearing OFF the two are byte-identical** — not asserted, executed, by D78's own
`test_exit_exempt_is_byte_identical_to_exempt_when_the_clearing_is_off` under both decision rules.
So liveness is decided by one measured predicate, `resolve_capacity_market_supply_clearing`:

| leg | D57 clearing | D81 |
|---|---|---|
| `ercot-t1f` · `neiso-t1f` · `nyiso-t1f` · `caiso-t1f` · `miso-t1f` · `neiso-t3` | **False** | **INERT** (D78 T2) |
| **`pjm-t1f`** | **True** | **LIVE** |

**Consequences, stated at the gate rather than discovered in the write-up:**

1. **The PJM leg's before/after against `pjm-t1f-pre-d65b` is CONFOUNDED by D81** — it carries the
   two acts *and* D81's must-offer re-routing of the retrofit and dated-plant sets. It is
   **reported at full magnitude and attributed, never netted**, exactly as D65-B handled the
   SCN-LOAD demand vintage.
2. **G-CTRL form 4 stays valid for the other six legs** and is VOID for PJM alone.
3. **No control solve is spent.** Rule 29(b) earns one only "for the years the screen needs", and
   this batch is not a screen: it is the board's re-solve at one HEAD. The PJM confound is
   *disclosed*, not differenced — and it is separable on the artifact, because D81's signature is
   confined to the ledger's `offer_stack` rows (a formerly $0 price taker now carrying a net-ACR
   sell offer) while the two acts' signature is confined to `ccs_retrofits`. **Addendum C's gates
   G0'–G5' read only `ccs_retrofits`, so the PJM leg's gate table is unaffected by D81.**
4. D81 is charter-ordered to *register* after this batch; it landed as **code** before it. That is
   not a collision — it is a G-DRIFT fact, and this is where it is recorded.

### D.4 Every key re-verified at `13ee0c89`

* **14 / 14 bare keys UNMOVED** against PRECOMMIT §3's POST-D65B column.
* **7 / 7 SOLVE keys** match Addendum C's pre-declaration exactly — **and** each still reproduces
  its committed pre-D65-B bundle key when the two acts are undone. The declaration written before
  the rebase survives the rebase unchanged, so no re-declaration is owed and the STOP *"a realized
  key ≠ its pre-declared value"* is unchanged.

---

## ADDENDUM E (2026-09-06, session **D65-B-R**) — second rebase re-audit; the PJM key is RE-DECLARED

Addendum D merged to `main` (`f4cf9c96`) and `main` moved `13ee0c89 → c3988c73` (32 commits).
**Still no leg had solved.** Charter Step 1: *"every key must resolve unmoved or the moved ones are
re-declared with the moving hunk named."* One moved. It is re-declared here, with its hunk named.

### E.1 `constants.py` FIRST: ZERO hunks. Solve-path scope: 2 files

`src/market_sim/config/iso_configs.py` (+36) and `src/market_sim/results/cache.py` (+50).
**`iso_configs.py` is no longer absent** — and Addenda C and D both leaned on its absence to
conclude "no ISO arms it". That inference is now retired and replaced by measurement.

### E.2 THE MOVING HUNK: capx **D67-ARM** (owner ruling Q52, *"ARM for PJM"*)

`_pjm_config`'s `default_scenario_overrides` gains
**`"capacity_adequacy_requirement_published_by_iso": {"PJM": True}"`** — the adequacy
requirement's OPERAND becomes PJM's own published whole-RTO Reliability Requirement in place of the
model's `screen peak × FPR` reconstruction, at the one seam
(`gross_adequacy_requirement_mw`) the reliability floor, the reserve-margin build backstop and the
CR-1 position all reach through. Armed the D57/Q44 way — through the ISOConfig override, with the
shared `ScenarioConfig` default left `None` — so no other ISO's key moves.

**Decomposed, single cause, measured:**

| PJM object | value | |
|---|---|---|
| t1f SOLVE key at HEAD | `542eeedadab83ee1` | **the RE-DECLARED key** |
| undo **D67-ARM only** | `43cee1c9558ab859` | **= Addendum C's declared PJM solve key, exactly** |
| undo D67-ARM **+ the two D65-B acts** | `09996eca71ee80fd` | **= the committed pre-D65-B bundle key, exactly** |
| bare PJM forecast at HEAD | `748a1cfaecd3acef` | the re-declared bare key |
| bare PJM forecast, undo D67-ARM | `eaa3fbef5ff182c9` | **= PRECOMMIT §3's declared value, exactly** |
| bare PJM **backcast** | `3a566deac3a85682` | **unmoved** — the backcast coercion is intact |

So the whole move is D67-ARM's and nothing else's, and Addendum C's declaration is recovered
exactly by undoing it. **The other 13 bare keys and the other 6 solve keys are UNMOVED**, each
still reproducing its committed pre-D65-B key with the two acts undone.

**RE-DECLARATION (this supersedes Addendum C's PJM row ONLY):**

> **`pjm-t1f` SOLVE key = `542eeedadab83ee1`; bare PJM forecast = `748a1cfaecd3acef`.**
> A realized PJM bundle on any other key is a STOP.

### E.3 PJM now carries TWO live hunks, and that is a disclosure, not a difference

| leg | live hunks | form 4 |
|---|---|---|
| `ercot-t1f` · `neiso-t1f` · `nyiso-t1f` · `caiso-t1f` · `miso-t1f` · `neiso-t3` | none | **VALID** |
| **`pjm-t1f`** | **D81** (Addendum D.3) **+ D67-ARM** | **VOID** |

The PJM leg's before/after against `pjm-t1f-pre-d65b` therefore carries **three** distinct causes —
the two D65-B acts, D81's must-offer re-routing, and D67-ARM's operand swap. It is **reported at
full magnitude and attributed to all three, never netted**, and PJM's row is the one row on this
lane's board table that is not a clean two-act reading.

**No control solve is spent, and the gate table is still clean.** Addendum C's gates G0'–G5' read
**only** the `ccs_retrofits` ledger rows. D81's signature is confined to `offer_stack` rows and
D67-ARM's to the adequacy requirement (`I7` / `I12` / the floor). Neither writes a `ccs_retrofits`
row, so **PJM's G0'–G5' verdict remains a clean reading of the two acts**; what the two live hunks
confound is the FC-map delta, which is disclosed rather than differenced. A retrofit set that moves
*because* the reliability floor moved is the one coupling to watch, and it is visible on the
gate table itself (G5' against D64 §2.4's PJM ceiling 0.41 / 2.48 / 2.48 GW).

### E.4 `results/cache.py` (+50)

Epoch notes only — prose, no code hunk. **INERT.**
