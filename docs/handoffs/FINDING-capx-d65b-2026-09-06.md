# FINDING — capx D65-B: the coupled arming (Act A + Act B) executed

**Session:** capx D65-B · **Date:** 2026-09-06 · **Branch:** `claude/capx-d65b-coupled-arming-m4mzgv`
**Authority:** OWNER RULING **Q47** (capx ledger §3, r#42 amendment 2, verbatim *"Arm coupled, after
D60-R3"*), released by r#46 am.1.
**Pre-registration:** `PRECOMMIT-capx-d65b-2026-09-06.md` — every key, gate and direction in this
document was declared there **before** the corresponding solve.

---

## 0. The verdicts

| # | verdict |
|---|---|
| V1 | **Both acts are LANDED, in one PR and one re-key event**, as Q47 requires. `ccs_retrofit_vom_adder` 8.0 → **2.95 $/MWh (2026$)**, dollar-year stated and derivation asserted; `ccs_retrofit_fixed_cost_co2_scaling` default **False → True** as a declared (b′-1) flip with the frozen drop value left at `"False"`. |
| V2 | **D64 STOP 6 is discharged, and it was a real precondition rather than a formality.** The widened ATB extract came first, and the new `TestRetrofitVomBasis` was committed FAILING against the shipped 8.0 — the evidence that the value change follows a derivation instead of the derivation being written around a chosen value. |
| V3 | **The widening cannot move any other constant, and that is measured, not argued.** The regeneration is a verified STRICT SUPERSET of the committed extract: 3,858/3,858 keys present, **0 dropped**, `value` differing on **0**. |
| V4 | **A cross-check closed as a by-product.** ATB's own unabated NG 2-on-1 CC (F-Frame) heat rate @2026 is **6.3 MMBtu/MWh** = `min(HEAT_RATE_BINS["gas_cc"].values())`, the `hr_ref` inside `ccs_retrofit_captured_ref_t_per_mwh`. The D50 capex seam's host and the captured-flow reference host are provably ONE host, from the pinned bytes. |
| V5 | **The STOP "the explicit-`False` path moving a key" DOES NOT FIRE.** Decomposed: Act A alone leaves that path on `e5ecd4105ada3e58`, exactly the pre-flip forecast default. The movement at HEAD is Act B's unconditional re-key, which D65 §9 item 3 predicts and licenses. |
| V6 | **A DEFECT THE CHARTER DID NOT ANTICIPATE was found and repaired before the screen** — Act A's flip made the D50/Q42 CONTROL ARM, and six committed bundles, unconstructible. §4 below. This is the finding of this lane that was not on its list. |
| V7 | **THE SCREEN FIRES TWO PRE-REGISTERED STOPs — G1 and G3 — so per rule 29 THE BATCH DOES NOT RUN and the remaining years are not spent.** The mechanism evidence is nonetheless favourable and is reported at full magnitude (§6): the same-HEAD control produces **0 retrofit rows in every year**, reproducing D64 §2.4's shipped-level ERCOT census exactly, so the arm's 7 rows are attributable to the two acts and nothing else; G4/G5/G6 pass. |
| V8 | **Both fired gates appear UNSATISFIABLE by the arm the charter itself specifies**, and this session does NOT reinterpret them to pass (§6.5). G1's `er/phys ≥ 1.27` is, in both source documents, **PJM/MISO's** host band — D64 §2.4's own ERCOT row reads **0.95–1.05**, and the measurement is 0.9458/1.0000, i.e. the arm did exactly what D64 predicted for this ISO. G3's `k = 1` invariance is an **Act-A** property, while Act B moves every host's VOM by design. Routed to the director for adjudication, not resolved here. |
| V9 | **G2 could not be evaluated at all**, because the evolution ledger persists `ccs_retrofits` as `{unit_id, mw, from_fuel, to_fuel}` and drops the `retrofit_log` that carries `capex_scale` / `fixed_cost_scale` / uplift. A charter gate is unreadable from the artifacts the runner writes — the same defect class D65 §3d found in `floor_retained` (§6.4). |

---

## 1. What landed

### 1.1 Act B — the value, and why it needed the extract first

`ccs_retrofit_vom_adder` **8.0 → 2.95 $/MWh (2026$)**:

```
ATB 2024 v4.0.0, Moderate, @2026:
  NG 2-on-1 Combined Cycle (F-Frame) 95% CCS  Variable O&M = 4.8   (2022$/MWh)
  NG 2-on-1 Combined Cycle (F-Frame)          Variable O&M = 2.1
  (4.8 − 2.1) × 1.090947  [2022$→2026$, constants.INFLATION_RATE] = 2.9456 → 2.95
```

The shipped 8.0 was `needs-citation`, stated no dollar-year, and cited *"NETL Cost & Performance
Baseline Rev 4"* — **a source that publishes 2.23 $/MWh per host MWh (2026$) for this increment**.
The cited document did not support the cited number. At 24.8 $/t captured against ATB's 9.1 and
NETL's 6.9, it was 2.7–3.6× every published basis.

**Why it could not simply have been fixed earlier**, which is the substantive content of D64
STOP 6: the committed ATB extract carried only `CAPEX` and `Fixed O&M` for `NaturalGas_FE`, so this
leg **could not be read off the pinned basis at all**. That absence is not incidental to how the
field came to ship uncited — it is the mechanism. Item 1 removes it.

### 1.2 Act A — the (b′-1) declared flip

`ccs_retrofit_fixed_cost_co2_scaling` default `False → True`; frozen drop value stays `"False"`;
declared as the third `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry, dated 2026-09-06. A
**posture, not a transfer** (rule 25 intact): `k` is D50's own factor, every other term an
already-cited constant, no new constant and no new reference host.

### 1.3 Why they are one PR

D65 §8.1, restated because it is the whole reason this lane exists: Act A multiplies Act B's level
by `k`, so arming the shape on an uncited 2.7× level compounds the error **on exactly the
high-emitting hosts the seam exists to re-price** — and commits the model to *"no merchant NGCC
retrofit ever clears on §45Q at carbon 0"*, a stronger claim than the evidence carries.

**Direction, stated before any solve (rule 23):** re-identification makes retrofits **EASIER**.
Rule 14 `[R-ACCURATE]` keeps an accurate value whichever way it moves the answer.

---

## 2. Item 1 — the widened extract, measured

Source: OEDI `ATB/electricity/csv/2024/v4.0.0/ATBe.csv`, **102,696,929 B**, sha256
`567dde9d85caa759bc3f2e42c9aa14a5f85e471ca4133ccc522e7a92e020297a` — **byte-for-byte the pinned
source the committed extract already came from.** No new source, no new vintage, no re-download of
a different object.

`fetch_nrel_atb.py` gains `EXTRA_PARAMETERS_BY_TECHNOLOGY = {"NaturalGas_FE": ["Variable O&M",
"Heat Rate"]}` — a **per-technology** scope, so no other technology's row set grows.

| check | result |
|---|---|
| committed keys present in the regeneration | **3,858 / 3,858** |
| old-only keys (dropped) | **0** |
| `value` differing on a common key | **0 / 3,858** |
| `display_name` / `default` / `atb_year` differing | **0** |
| new-only keys | **696** = NaturalGas_FE × {Variable O&M, Heat Rate} (348 each) |
| total | 3,858 → **4,554** rows, 12 parts |

⇒ `NEW_ENTRY_COSTS` and `TECH_COST_MULTIPLIERS` **cannot move**; the existing rule-23 consistency
test passes untouched. The parts were rewritten from a fresh fetch rather than appended, so **row
order again equals a from-scratch run** — the property the 2026-07-19 EGS append had given up.

**The test was committed failing.** `TestRetrofitVomBasis` asserts
`ccs_retrofit_vom_adder == derive_ccs_retrofit_vom_adder()` and failed `8.0 != 2.95` at the item-1
commit. That ordering is the evidence that the derivation is the reason for the value, not a
justification found for it.

---

## 3. The re-key, declared before the solve

Full table: PRECOMMIT §3. Headline: forecast default `e5ecd4105ada3e58` → `547053bdfccd4264`;
bare backcast `6a2845e50951394e` → `f61891696e671969`. **Every** per-ISO bare key moves, because
Act B is not a `_CACHE_KEY_OPTIONAL_FIELDS` member and has no drop value.

**Backcast behaviour is byte-identical**, by a stronger argument than either earlier flip had,
because it now covers both fields at once: the sole consumer of *either* field in the source tree
is `ccs.py::apply_ccs_retrofit`, which returns at `if year < config.ccs_retrofit_available_year`
(2028) before reading either. Keys move; answers do not. No keeper, sidecar, determination or
dashboard row moves, and **no backcast keeper is re-solved by this lane**.

### 3.1 The STOP, decomposed

| arm | explicit `seam 4 = False` key |
|---|---|
| **Act A alone** (`vom_adder` held at 8.0) | **`e5ecd4105ada3e58`** |
| the pre-flip forecast default (committed pin) | `e5ecd4105ada3e58` |
| both acts (HEAD) | `910b8cfcb2aa6a36` |

Act A's drop-value mechanic is intact. The movement is Act B's, and it is unconditional by
construction. **STOP not fired.** This decomposition is now a standing test
(`test_q42s_own_drop_mechanic_survives_the_d65b_coupling`), so the next lane to re-key does not have
to reconstruct the argument.

---

## 4. THE DEFECT THIS LANE DID NOT GO LOOKING FOR

**Act A's flip made the D50/Q42 control arm unconstructible.**

`__post_init__` refused seam 4 without seam 1. Before the flip that was a guard on a deliberate
mis-declaration. After it, the pair *(seam 1 EXPLICIT `False`, seam 4 at its default)* — which had
been perfectly coherent — started raising. That pair is:

* **`ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)`** — the D50/Q42 CONTROL ARM ITSELF,
  pinned by `test_d60_arming_batch.py`'s *"(b′-1)'s useful inverse: a control arm keeps its
  bundle"*; and
* **six committed bundles**: `results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing`,
  `…/miso-2021-2025-realized-t1h-d53-sectorgate`, `…-d51ratio`,
  `results/calibration/caiso251_arm_nomargin`, `…/nyiso192_astoria_panel`, `…/miso217_intermphys_B`.

All six carry `ccs_retrofit_capex_co2_scaling: false` with seam 4 absent, and all six failed to
reconstruct at the charter-literal flip. **The flip would have made the D50 control unreachable —
the one thing rule 29(b) needs a control to be.**

**Why the charter missed it.** Its line *"the validator's seam-1 requirement is satisfied because
Q42 armed seam 1"* is true of the DEFAULT path and silent on the explicit-seam-1-off path.

**The repair.** The distinction the guard actually wants is **explicitness, not value**, and
`__post_init__` provably cannot see it — it runs after binding, which is the exact defect the
repo's own `_scenario_config_init` / `_explicitly_set_fields` record was built to fix (its docstring
says so in as many words). The pair resolution therefore moves to that wrapper,
`_resolve_ccs_retrofit_fixed_cost_pair`:

* explicit `seam 4 = True` with seam 1 off → **still RAISES** (rule 24);
* seam 4 at its default with seam 1 off → **DEMOTED to `False`** — inert by construction
  (`k ≡ 1.0`), so this is the truthful record, and it drops from the hash on the frozen `"False"`
  drop value;
* provenance unknown (`replace`, `from_yaml` over a full dump) → demote, the same fallback
  convention `_explicitly_set_fields` already uses.

The dead branch in `__post_init__` is **deleted, not zeroed** (rule 26 `[R-DELETE]`).

**Verified:** all six bundles reconstruct with seam 4 → `False`; the explicit incoherent pair still
raises; §3.1's decomposition is measured *through* the repair. **No armed config reaches the
demoting branch, so the repair moves no key.**

**A second-order benefit, worth stating because it is why the legacy fixtures survived.**
`tests/unit/model/test_ccs_retrofit.py::_fixture_config` pins seam 1 explicitly `False` for every
pre-D50 fixture. Under the repair those fixtures now demote seam 4 automatically, so each keeps
testing what it was written to test without a single fixture edit.

---

## 5. G-DRIFT — form 4 is VOID, and the control solve is earned

Audited before the screen (PRECOMMIT §5), `constants.py` first, because **a matched cache key is
not a G-DRIFT verdict — `constants.py` is outside the key.**

| named hunk | verdict | evidence |
|---|---|---|
| **SCN-LOAD `d14a7ed0`** (`DEMAND_GROWTH_RATES`, six ISOs) | **LIVE** | Ancestry per incumbent: `9e48ff6` (ercot/neiso t1f), `2ef4326e` (miso), `e7412237` (nyiso), `b83e96ca` (caiso) are **PRE-hunk**; only `14f860fb` (pjm) and `e9d8263b` (GOLDEN-3) carry it |
| **wallclock P1 basis seed #5033** | INERT on the forecast path | rule 29(b)'s "pure timing/diagnostics accounting" class |
| **D77 `ae8dd2a0`** (CCS retrofit emission-rate seam) | **LIVE**, and inside this seam | why r#46 am.1 made it a precondition of the batch |

**Consequences, recorded at the gate:**

1. The screen uses a **same-HEAD ERCOT t1f control** — the committed ERCOT t1f is pre-hunk and
   cannot serve as a form-4 control.
2. The batch's **board-level before/after is confounded by the demand vintage** for the four
   pre-hunk ISOs. Reported at full magnitude and attributed, never netted.
3. **The batch lands the whole T1-F board in ONE demand vintage — that is now one of its
   purposes**, and it is why the confound does not survive this lane.

---

## 6. The screen — RUN, and it FIRES TWO PRE-REGISTERED STOPs

**Both legs solved, same HEAD (`a5c30c6a`), 5/5 years each.** ARM `d0fb7534671b4c91`
(14.8 min, 4.04 GB peak RSS); CONTROL `6cfa33538294713c` (15.0 min, 3.77 GB) — and the control
landed on **exactly** the key Addendum A.2 declared for it before it ran. `CTL EXIT=0` with the HEAD
guard clean.

### 6.1 What the screen measured

| year | CONTROL (same HEAD, both acts off) | ARM (both acts) |
|---|---|---|
| 2026 / 2027 / 2028 | 0 rows | 0 rows |
| 2029 | **0 rows** | **6 rows / 2,763.8 MW** |
| 2030 | **0 rows** | **1 row / 3,000.0 MW** (the 3 GW/yr cap, binding exactly) |

The control reproduces D64 §2.4's shipped-level ERCOT census (**0 / 0 / 0**) exactly, so **the entire
retrofit set is attributable to the two acts** and to nothing else on the HEAD.

Per-host, from CAMPD 2024 (`er` = ΣCO2/Σgross MWh, `phys` = `hr` × 0.057, `k` = 0.9·`er`/0.32319):

| host | hr | er | phys | **er/phys** | k |
|---|---:|---:|---:|---:|---:|
| `CC_REGULAR_South_Central_p7900` | 7.579 | 0.4086 | 0.4320 | **0.9458** | 1.138 |
| `CC_REGULAR_North_p55320` | 6.767 | 0.3648 | 0.3857 | **0.9458** | 1.016 |
| `CC_REGULAR_West_p56349` | 8.515 | 0.4591 | 0.4854 | **0.9458** | 1.278 |
| `CC_REGULAR_North_p58001` | 7.797 | 0.4204 | 0.4444 | **0.9458** | 1.171 |
| `CC_REGULAR_West_p56233` | — | — | — | absent from CAMPD 2022–24 (planned unit) | — |
| `gas_cc_h_class_Houston` / `_North` | 6.300 | 0.3591 | 0.3591 | **1.0000** | **1.0000** |

### 6.2 The gate table

| gate | verdict |
|---|---|
| **G1** — every clearing row is an `er/phys` ≥ 1.27 host | **FIRES.** Every row is 0.9458–1.0000 |
| **G2** — the identity `uplift/capex ∝ 1/k` holds | **NOT EVALUABLE** from committed artifacts (§6.4) |
| **G3** — `k = 1` rows byte-identical | **FIRES.** Both `gas_cc_h_class` rows are `k` = 1.0000 exactly and appear in the ARM only |
| **G4** — no non-target load-bearing row flips PASS → FAIL | **PASS** (§6.3) |
| **G5** — direction and order of magnitude match the pre-solve delta | **PASS.** 0 → 7 rows, and 2030 pins the 3 GW cap |
| **G6** — wall/RSS inside the D60 envelope | **PASS.** 14.8 / 15.0 min, 4.04 / 3.77 GB |

**Per rule 29, a fired STOP is the session's result and the remaining years are not spent. THE BATCH
DOES NOT RUN.** What follows is why both fired gates are, in this lane's reading, **unsatisfiable by
the arm the charter itself specifies** — which is a question for the director, not one this session
may resolve by reinterpreting its own STOP.

### 6.3 G4, measured — and why the same-HEAD control earned its 15 minutes

The 14 forecast invariants are **identical between ARM and CONTROL**, detail strings included:
2 FAIL (I3 unserved/dump, I12 reserve-margin band), 2 WARN (I13 cobweb `wind(3)`, I14 price sanity).
Both FAILs are **pre-existing** — the committed pre-D65-B ERCOT t1f carries I3 and I12 FAIL too.

I13 reads PASS on the committed bundle and WARN on both of this lane's legs. Because it moves on
**both** legs at one HEAD, it is attributable to the HEAD delta (the SCN-LOAD `DEMAND_GROWTH_RATES`
hunk §5 found LIVE) and **not to either act**. A form-4 comparison against the committed bundle
would have charged that WARN to this seam.

### 6.4 G2 is not evaluable, and that is a defect in the artifacts, not in the arm

`results/evolution_ledger.py` persists `ccs_retrofits` as `{unit_id, mw, from_fuel, to_fuel}` only.
The rich `retrofit_log` — carrying `capex_scale`, `fixed_cost_scale`, `vom_adder_per_mwh`,
`delta_fom_per_mw_yr`, `annual_net_savings_per_mw`, `payback_years`, `old_emission_rate` — is
computed by `apply_ccs_retrofit`, handed forward to the next year's screen, and then **dropped**.
So the `uplift/capex ∝ 1/k` identity, which D65's own charter names as a screen gate, **cannot be
read from the bundle the runner writes**; §6.1's `er`/`k` column had to be reconstructed offline
from CAMPD.

This is the same class of defect D65 §3d found in `floor_retained`: *a diagnostic that exists to make
a mechanism visible is blind to the mechanism.* **Routed:** persist the retrofit log (or its
per-row `capex_scale` / `fixed_cost_scale` / `vom_adder_per_mwh` / uplift columns) in the evolution
ledger, so a retrofit-seam gate is checkable from committed artifacts rather than by replay.

### 6.5 Why G1 and G3 appear unsatisfiable by a COUPLED arm on a CARBON-0 ISO

Stated as an escalation, not as a reinterpretation. **This session does not treat either gate as
passed.**

**G1 — the 1.27 threshold is another ISO's host population.** Both source documents attribute that
band to PJM and MISO, never to ERCOT:

* D64 §2.4: *"The PJM and MISO rows that survive are the `er/phys` 1.27–1.49 hosts … which are D49
  §1.3's business"* — and the SAME table's ERCOT row reads **`er/phys` 0.95–1.05**.
* D65 §9 item 4 repeats it verbatim: *"the surviving PJM/MISO rows are the `er/phys` 1.27–1.49
  hosts"*.

The measurement — 0.9458 on all four CAMPD hosts, 1.0000 on the two synthetic h-class builds — is
**inside D64's own pre-registered ERCOT band of 0.95–1.05**, to two decimal places. So the arm did
exactly what D64 predicted for this ISO, and the gate as transcribed demands the opposite.

It also inverts the gate's evident purpose. `er/phys` > 1 flags a **CAMPD-rate-above-physical**
tranche — a measured rate exceeding what the heat rate implies, i.e. the artifact D49 §1.3 is about.
ERCOT's hosts sit at 0.9458, *below* physical, so that artifact is absent. Read as a floor, G1 does
not screen the artifact out; it **requires** it.

**G3 — `k = 1` invariance is an ACT-A property, and this arm is coupled.** At `k` = 1,
`fixed_cost_scale` = `capex_scale` = 1.0, so Act A multiplies both fixed-cost legs by exactly 1.0 —
identity by construction, already asserted by
`test_ccs_retrofit.py::test_reference_host_is_invariant_on_and_off`. But **Act B changes the VOM
level for every host, `k` = 1 included, by design**; that is the same mechanic §3.1 uses to show the
explicit-`False` path moves on Act B and not Act A. So a coupled arm necessarily moves `k` = 1 rows,
and G3 can only be evaluated against an Act-A-only leg — which the charter did not commission and
which would spend an LP to re-measure arithmetic that is already proven and tested.

**The common root.** The gate set reads as written for an **Act-A-only** screen, while §8.1 of D65
then required the arm to be **coupled**, and §9 item 4 required the screen ISO to be **carbon-0**.
Under those two constraints together, G1 and G3 are not merely unmet — they are unmeetable: any row
a carbon-0 ISO gains will be `er/phys` ≈ 0.95–1.05, and any coupled arm moves `k` = 1 rows. The
charter's own clause *"a carbon-0 ISO GAINING rows is NOT a STOP — it is the accurate level's
pre-registered signature"* points the other way from G1 on the very same page.

### 6.6 What this session did NOT do

It did not reinterpret, relax, re-scope or re-baseline either fired gate to reach a pass — selecting
a criterion because it lets a result through is the fitted-mechanism selection rules 1 `[R-STRUCT]`
and 29 forbid, and a STOP the session wrote for itself is not a STOP if the session may edit it on
seeing the number. It did not run the batch. It did not register anything.

**For the director.** The mechanism evidence is favourable and is reported at full magnitude: the
control's 0/0/0 reproduces D64's census exactly, the arm's rows match D64's ERCOT prediction on
`er/phys` to two decimals, G4/G5/G6 pass, and the 2030 row pins the 3 GW cap. What is needed is an
adjudication on the gate set, not more solving:

1. **Is G1 ISO-parameterized?** If the ERCOT band is D64 §2.4's own 0.95–1.05, the arm passes it as
   measured. If 1.27 is meant literally for every ISO, the screen ISO was mis-chosen and the screen
   belongs on PJM or MISO — where D64 predicts 1.27–1.49 hosts, and where the cap-bound RGGI
   objection does not apply.
2. **Is G3 to be evaluated Act-A-only?** If so it is already discharged by construction plus a
   passing test, at zero LP. If it is meant to bind the coupled arm, it cannot be satisfied and
   should be withdrawn or restated.
3. **G2 needs the artifact fix in §6.4 before any future screen can evaluate it at all.**


## 7. The batch — NOT RUN

Rule 29: *"A screen that kills an arm is reported as the session's result and the remaining years are
never spent."* Two pre-registered STOPs fired, so the seven batch legs (ercot / neiso / nyiso /
caiso / pjm / miso t1f + the neiso-t3 GOLDEN-3) were **not solved, not scored, not registered**, and
no matrix cell verdict was stamped. Nothing this lane produced reached the dashboard.

**Everything the batch needs is nonetheless prepared and durable**, so an adjudication is the only
blocker — not re-work:

* the §3 bare-key declaration **still holds at the post-merge `main`** (PRECOMMIT Addendum B.1:
  fifteen lanes merged, not one moved a bare forecast key);
* the batch's G-DRIFT re-audit is **complete and all-INERT**, hunk by hunk with each gate named and
  two of them measured (Addendum B.2);
* the screen therefore **does not need re-running** after a rebase (Addendum B.3);
* D60-R4 and D63 have both merged, so the collision constraint is discharged.

---

## 8. Governance

### 8.1 Rule 27 blob verification

Every pushed file ≥300 lines was fetched back and compared to local (line count + `git hash-object`
vs the remote blob sha) immediately after each push, before the next commit.

| file | lines | verdict |
|---|---|---|
| `src/market_sim/config/scenarios.py` | 18,529 | OK |
| `src/market_sim/results/cache.py` | 1,243 | OK |
| `tests/unit/model/test_ccs_retrofit.py` | 1,355 | OK |
| `tests/regression/test_persisted_identity.py` | 765 | OK |
| `docs/codebase-site/data/mechanism-matrix.js` | 2,624 | OK |
| `scripts/data/fetch_nrel_atb.py` | 297 | (below the threshold; verified anyway) OK |
| `scripts/data/derive_entry_costs_from_atb.py` | 279 | OK |
| `tests/unit/config/test_d60_arming_batch.py` | 254 | OK |
| `tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py` | 254 | OK |

No file shrank. `scenarios.py` grew (+210/−22).

### 8.2 Scope discipline

Rule **22** — forecast mode only; **no held-out year was solved, scored or registered.**
Rule **25** — a posture; no ISO's fitted number crosses a boundary.
Rule **26** — the superseded `__post_init__` branch is deleted, not zeroed.
Rule **12** — batch legs sequential within each invocation.

### 8.3 ROUTED — two pre-existing reds this lane did NOT absorb

Both were measured on clean `main` and found identical there, so neither is caused by this lane,
and fixing either would have swept other lanes' territory into this PR.

1. **`scripts/validate_parameters.py` FAILS with 43 missing citation entries on clean `main`.**
   They are SCN-lane constants (`demand_growth_rates.*`, `datacenter_additions_mw.*`,
   `datacenter_zone_share.MISO.*`, `rto_reliability_requirement_mw_by_iso.PJM.*`,
   `electrification_layers.*`) — the lanes that landed the constants did not regenerate the
   registry. Running the generator here would have swept **43 new + 54 value-refreshed** entries
   into this PR, colliding with the `federal_ces_*` and D34-guard regions the charter fences off,
   so the sweep was reverted and only `scenario.ccs_retrofit_vom_adder` applied (9 insertions /
   12 deletions). **The owning lanes should run `scripts/generate_parameter_registry.py`.**
2. **`check_mechanism_matrix.py` emits 249 anchor warnings** (line-number drift). Measured **249 on
   clean `main` and 249 with this lane's changes** — this lane adds none. Exit code is 0; the
   remedy is `--fix-anchors`, which belongs to whichever lane wants to spend the churn.

### 8.4 DOF ledger (D8 curated rows, Q37's limb)

`ccs_retrofit_vom_adder` is a **value identified to a published source**, so under Q37's limb it is
**NOT an unattested free parameter**: its identification source is NREL ATB 2024 v4.0.0 Variable O&M
@2026, Moderate case, asserted by a committed test against the pinned bytes. It is the third leg of
the retrofit screen's cost side to be moved off `needs-citation` onto that one basis (after capx
D41's `ccs_retrofit_capex_kw` and `fixed_om_gas_cc_ccs`), and it closes the last of them.

`ccs_retrofit_fixed_cost_co2_scaling` carries **zero DOF** — no constant, no reference host, `k` is
D50's own factor.
