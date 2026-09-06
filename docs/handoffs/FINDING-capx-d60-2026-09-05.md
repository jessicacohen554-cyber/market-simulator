# FINDING — capx D60: the three-ruling arming batch executed (Q40 · Q41 · Q42), the pre-declaration graded at full magnitude, one STOP fired on PJM and one pre-declaration miss recorded against myself

**Lane:** capx D60 — the EXECUTION of three owner rulings given 2026-09-05 at director
sitting r#37 (capx ledger §0ah.3 / §3). A ruled, mechanical lane: **no new mechanism, no new
field, no new parameter value, no keeper, no shard promotion field, no `complete` / `final`
marker, no freeze, nothing against measured H1-2026.** Everything below is what the three
armings made true, and what they made false that the pre-declaration had claimed.

**Pre-declaration:** `PREDECL-capx-d60-2026-09-05.md`, pushed **before any code change on
the branch**, with **Addendum A** (every bare key re-resolved through the real harness path,
before any solve) and **Addendum B** (the T3 attestation's six assertions fixed before the
GOLDEN-3 solve was launched).

---

## 0. Verdict (one paragraph)

All three rulings are armed, flip-first, in one commit: `adequacy_accounting_ratio_dated_net`
for MISO and both NYISO requirement gates through their ISOs' `default_scenario_overrides`
(rule 25 — both dataclass defaults stay `False`), and `ccs_retrofit_capex_co2_scaling` as the
dataclass default for all six ISOs through a **(b′-1) declared flip** whose frozen drop value
stays `"False"`. Both pinned default keys advance —
`4c6b03ae098b6e3e` → `e5ecd4105ada3e58`, bare backcast `8211c72bb1960adc` →
`6a2845e50951394e` — which is the designed behaviour of (b′-1), pre-authorised in terms by
D50 §6.4, and **no committed artifact moves at all**. Twelve of the thirteen bare forecast
keys landed exactly on their pre-declared post-arm values; the thirteenth is a defect in my
own pre-declaration, graded in §3. Four bare keys were RENAMED onto committed legs at zero
solve, with byte-identity established field-by-field first and every prior preserved at
`-pre-d60`; a fifth rename — PJM's — was **reversed before it was pushed** when capx D57
merged mid-lane and moved PJM's bare t1f recipe, which is D60's **STOP 1 firing exactly as
written** (§4). The four re-solves the flip owes are in §5.

---

## 1. What was armed, and in what form

| ruling | field(s) | form | record it executes |
|---|---|---|---|
| **Q40** | `adequacy_accounting_ratio_dated_net` | `_miso_config` `default_scenario_overrides` | `FINDING-capx-d51-2026-09-04.md` §7 |
| **Q41** | `nyiso_requirement_forecast_peak` + `nyiso_requirement_vintage_factors` | `_nyiso_config` `default_scenario_overrides` — **NYISO's first ISO-level overrides** | `FINDING-capx-d52-2026-09-04.md` §8(1) |
| **Q42** | `ccs_retrofit_capex_co2_scaling` | dataclass default `True` + a dated (b′-1) line, frozen drop value untouched | `FINDING-capx-d50-2026-09-04.md` §8 |

Rule 21 holds by inspection: **no value was chosen here.** The ratio IS D51's 0.893436, and
`captured_ref` IS D50's 0.90 × 6.3 × 0.057 = 0.32319 t/MWh. Rule 25 holds in both directions:
the two ISO armings are per-ISO by construction (and the dated-net registry falls through to
D31's value for any ISO absent from it, even when armed), and Q42 is a **posture, not a
transfer** — it carries no ISO's fitted number, every term is an already-cited constant, and
the reference host is the same one `new_entry._emerging_lcoe` charges the ATB increment
against. That is the same admissibility class as Q30.

**Nothing beyond the three rulings armed**, asserted by test: the NYCA ICAP demand curve
stays OFF (D52 §8(2), re-affirmed D59), `locality_capacity_curves` stays OFF (D59), and
`capacity_deliverability_limits` stays OFF everywhere.

## 2. Step 0 (hygiene) was already satisfied at HEAD — no commit

The director's §0ah.4 routing named three files for `ruff format`. At the lane's base
`ee7754c1` all three were **already formatted** — `ruff format` reported *"3 files left
unchanged"*, `ruff check` *"All checks passed!"*, and `git log -1` on each names commit
`0b51f28e` ("Y-7 item 2: ruff format the six files the check named"), which landed the same
work before this lane opened. **There was nothing to commit and no no-op commit was made.**
Stated rather than silently skipped.

---

## 3. The pre-declaration graded at full magnitude — every key

Twelve of thirteen HIT. The thirteenth is mine to own.

| bare key | §2 pre-declared | harness-resolved | verdict |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | `0c3e9cd5b5993bdf` | **HIT** |
| `neiso-t1f` | `18515067bf4d2fbe` | `18515067bf4d2fbe` | **HIT** |
| `pjm-t1f` | `167e65187f32056b` | `09996eca71ee80fd` | **STOP 1 — §4** |
| `caiso-t1f` | `29f8eb372810195f` | `29f8eb372810195f` | **HIT** |
| `nyiso-t1f` | `19a9690bb12c8459` | `19a9690bb12c8459` | **HIT** |
| `neiso-t3` | `f04fd06348e1623d` | `f04fd06348e1623d` | **HIT** |
| `ercot-t1h` | `82b27751be747552` | `82b27751be747552` | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` | `7da58199acd362ee` | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` | `f3988df3068020d1` | **HIT** |
| `pjm-t1h` | `7297dcb3b92be3fb` | `aef81c84c4609c76` | moved by D57, not by D60 — §4 |
| `miso-t1h` | `687bd75f2828bea1` | `687bd75f2828bea1` | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` | `6e70a637b3465542` | **HIT** |
| `miso-t1f` | `3f85ecc45d90c248` | **`b1a73a087064ffd8`** | **MISS — §3.2** |

### 3.1 The three required cross-checks, all HIT to the digit

1. **D50 §6.1's right-hand column.** For the four ISOs where CCS is D60's only arm the
   post-D60 key **is** D50's column: ERCOT `0c3e9cd5b5993bdf`, NEISO `18515067bf4d2fbe`,
   PJM `167e65187f32056b` (as it stood before D57), CAISO `29f8eb372810195f`. For MISO and
   NYISO, where D60 arms more, removing the extra arms reproduces D50's column exactly —
   MISO CCS-only `f3f96e14bb75c9d9`, NYISO CCS-only `b9e4c79e188ab01e`.
2. **`miso-t1h`, the `c306ddc6…`-successor, and its exact relation to the D53 rider.**
   `c306ddc6d28c60c2` (bare at HEAD = sector gate via MISO's own override) **+ ratio** =
   **`6ea92547eaa62559`**, which IS the committed D53 rider key — reproduced to the digit;
   **+ the flipped CCS default** = **`687bd75f2828bea1`**, the post-D60 bare key. The
   post-D60 recipe therefore differs from the committed rider in **exactly one field**.
3. **`nyiso-t1h` and the D52 arm key.** `91686abe7a744a88` **+ the two gates** =
   **`911371a8cf23d5c3`**, the committed D52 arm — to the digit; **+ the flipped CCS
   default** = **`6e70a637b3465542`**. Same one-field relation.

### 3.2 The MISS, graded against myself

`miso-t1f`'s post-D60 key is **`b1a73a087064ffd8`**, not the `3f85ecc45d90c248` §2 declared.

**Cause, measured:** MISO's `default_scenario_overrides` already carry
`retirement_sector_gate: True`, landed at HEAD by **capx D53 earlier the same day**. The
committed control `miso-2026-2030-d45r-remeasure` predates D53 and records the field absent,
so §2's method — reconstruct the control's own `run_config.json` and set the armed fields —
understated the recipe by exactly one field. **Forcing the sector gate back off returns
`3f85ecc45d90c248`**, which confirms the diagnosis to the digit and confirms nothing else
moved.

**It is a defect in my method, not a surprise in the rulings.** §2's emulation is exact only
when the committed control's resolved posture already equals the bare recipe's — true for
twelve keys, false for this one. D53 §6.1 had stated the consequence in terms when it armed
the gate: *"the MISO t1f leg (2026–2030) was not re-solved here — its next solve resolves the
gated screen by construction."* D60's MISO t1f re-solve **is** that next solve. The
correction was published as **Addendum A §A.1 before any solve and before the flip commit**,
not retrofitted here, and Addendum A §A.5 added P17–P19 for the third mechanism the leg now
carries.

### 3.3 What Addendum A discharged: STOP 2, field-by-field

The harness-resolved bare recipe was diffed field-by-field against each rename target's own
committed `run_config.json`, ignoring only fields ABSENT from the older config that resolve
to a cache-neutral `False`/`None` (schema growth, not posture):

- **`miso-t1h` ← `…-d53-sectorgate-d51ratio`**: the ONLY substantive difference is
  `ccs_retrofit_capex_co2_scaling: False → True`. The committed rider records it
  **explicitly `False`** (solved after D50 built it), so the pair is a clean one-field A/B.
- **`nyiso-t1h` ← `…-d52-devintage`**: the ONLY difference is
  `ccs_retrofit_capex_co2_scaling: <absent> → True`.

**Why that is byte-identical rather than merely small, proved in code:**
`ccs.py::apply_ccs_retrofit` opens with `if year < config.ccs_retrofit_available_year: return
fleet, []` (line 305, default 2028), which precedes **every** read of the flag
(`scale_capex`, line 330) — and `ccs.py:330` is the field's **only consumer in the whole
source tree**. A horizon ending at 2025 (t1h) or 2027 (t1x) cannot reach it on any path. So
every SCORED row of both targets is identical to what the bare recipe would produce, STOP 2
does not fire, and neither leg is re-solved.

---

## 4. STOP 1 FIRED ON PJM — and the rename was reversed before it was pushed

**What happened.** §5 pre-declared `pjm-t1f` ← `pjm-2026-2030-d50-ccscapex` on the ground
that the D50 arm had been solved AT the key the flip would make bare (`167e65187f32056b`).
Between the pre-declaration and D60's rebase, **capx D57 merged** (PR #4786) and armed three
PJM gates by its own owner ruling — `pjm_accreditation_design_vintage`,
`pjm_demand_response_supply` and `capacity_market_supply_clearing_by_iso[PJM]`. PJM's bare
t1f recipe therefore now resolves through the harness path to **`09996eca71ee80fd`**, and the
D50 arm is no longer at it.

**What was done.** The rename was **reversed in the working tree before the commit was
pushed**: `pjm-t1f` keeps its D45-R record (`pjm-2026-2030-d45r-remeasure`,
`321f04e9060787f0`), the D50 arm keeps its suffixed key `pjm-t1f-d50-ccscapex`, and the
VERDICT_MAP rows carry the reversal with its reason. This is a wrong *rename* being undone,
never a mechanism being reverted — Q42 stands unchanged for PJM as for every other ISO.

**What it leaves open, stated plainly rather than buried.** PJM's bare t1f row is now stale
on **two postures at once** — D57's three gates and Q42's CCS default — and only a re-solve
at `09996eca71ee80fd` can make it truthful. **D60 did not run it**, for one reason stated as
a boundary rather than an excuse: PJM forecast surfaces are D57's this window, and the leg is
~28 min. It is **ROUTED to the director with the key it must land on** (§8 item 1).

**`pjm-t1h` likewise moved** — to `aef81c84c4609c76` — and that movement is **D57's, not
D60's**: D57's own arming note records the bare `pjm-t1h` recipe becoming its arm A's
`f0e050e820c1159a`, and D60's CCS flip is inert on a 2021–2025 horizon by §3.3. D60 neither
renamed nor re-stamped anything on PJM t1h.

**The test surface records D57's arming rather than asserting it away.**
`test_d60_arming_batch.TestNothingElseArmed` gains `test_the_d57_pjm_gates_stay_pjm_only`,
which pins those two gates ON for PJM and OFF for the other five — so a future lane that
widened them would fail here, and D60's own claim ("nothing else armed") stays honest about
what a *different* lane armed.

---

## 5. The re-solves

*(legs 1-2 landed with D60; legs 3-5 are D60-R3's and are filled below as each lands)*

### 5.0 D60-R3's state at start — the pins re-measured, and the environment repaired first

D60 died after legs 1-2; D60-R never launched; D60-R2 landed its state-at-start commit and
Addendum D and went silent (owner ruled it dead, director r#42 am.2). **D60-R3** is the third
issue and it re-established the pins from the committed record before spending an LP.
Pre-declaration: `PREDECL-capx-d60-2026-09-05.md` **Addendum R3**, pushed before any solve.

**Seventeen of seventeen keys unmoved** — thirteen bare forecast keys plus the four pinned
defaults, all resolved through the real harness path (§R3.2). STOP 1 therefore stands for all
three remaining legs, reading against `29f8eb372810195f`, `09996eca71ee80fd` and
`f04fd06348e1623d`. The three charter assertions were **measured, not argued** (§R3.3): D65
Act A's `ccs_retrofit_fixed_cost_co2_scaling` is key-neutral at its default (default and
explicit `False` collide on `e5ecd4105ada3e58`; explicit `True` keys distinctly to
`2186aa915ad19c59`); the R-AZ registration-time marker gate touches `dashboard_add_run.py` and
`lib/holdout_policy.py`, neither of which `register_forecast_run.py` imports, so this lane's
registration path is untouched; and the SCN sidecars live in `frontend/data/hindcast/`, never
the board.

**Two environment defects were found and repaired before the first solve**, both invisible in
a bundle afterwards (§R3.5). The container's `pip install -r requirements.txt` failed on a
Debian-owned PyYAML and left **highspy 1.15.1 / pandas 3.0.5 / pydantic 2.13.5** against pins
of **1.14.0 / 3.0.3 / 2.13.4** — a different HiGHS build is a different LP solver, and D65
§3b's entire drift argument rests on the stack matching the committed control's. Forced to the
pins. And the clone was **shallow**, so `9e48ff6` was not a resolvable revision; deepened
183 -> 1,049 first-parent commits.

Three further gates, all green at HEAD before any solve: `test_d60_arming_batch.py` **17
passed**, `check_cache_key_registration.py --base origin/main` **ok (798 fields, 253
registered, all resolve)**, `test_persisted_identity.py` **14 passed**. And each leg's
**mechanism delta was verified field-by-field against its own control's committed
`scenario_config`** before it was launched, confirming Addenda A.4 / C.2 exactly: `caiso-t1f`
and `neiso-t3` differ from their controls in **one** substantive field
(`ccs_retrofit_capex_co2_scaling` absent -> `True`); `pjm-t1f` in **four** (that plus
`pjm_accreditation_design_vintage`, `pjm_demand_response_supply` and
`capacity_market_supply_clearing_by_iso={'PJM': True}`). Everything else that differs is
schema growth resolving to a cache-neutral `False`/`None`, or list-vs-tuple serialization.

### 5.0b Control first — all three legs' controls reproduce at HEAD with ZERO non-provenance diffs

D47 §1 established that a claim of "N rows moved" is worthless without first proving the
control reproduces under the scorer you are about to use. Done here for **all three** legs
before any of them was launched, at zero LP: each control bundle was re-scored from its own
committed inputs by the HEAD scorer and diffed row-by-row against its committed verdict.

| control | determination | reasons / caveats | rubric | non-provenance diffs |
|---|---|---|---|---|
| `caiso-2026-2030-d46-remeasure` (`772b1e5abc7fc80c`) | HOLD → HOLD | identical | 1.0 → 1.1 | **0** |
| `pjm-2026-2030-d45r-remeasure` (`321f04e9060787f0`) | HOLD → HOLD | identical | 1.0 → 1.1 | **0** |
| `neiso-2026-2050-t3-golden3-bau` (`67678e58b2d0526c`) | HOLD → HOLD | identical | 1.0 → 1.1 | **0** |

**The rubric advanced 1.0 → 1.1 between the controls' scoring and this HEAD, and it is measured
INERT on all three** — every category status, every row's `row` / `status` / `detail` /
`gating`, both derived surfaces. So an FC row that moves on a leg below is attributable to
**the run**, never to the scorer version. That is the whole purpose of running the control
first, and it is the reason the legs' gradings can be read at face value.

**One input was pinned by this exercise rather than assumed.** GOLDEN-3's FC-4 consumes a
committed T1-X crossover score, and NEISO has *two* candidates on disk. Scoring with
`neiso-2023-2027-crossover-capxd14` reproduces five of the control's FC-4 metrics and misses
three (`price 2025` 21.3 → 21.8 %, `gas_twh 2024` 13.2 → 12.6 %, `coal_twh 2024` 84.0 →
66.4 %); **`neiso-2023-2027-crossover-rcrepair` matches every one**. This is the same trap
D47 §1 documented for FC-3 (GOLDEN-3 consumes D46's re-solved T1-H, not GOLDEN-2's leg) — the
obvious guess is the wrong artifact, and it would have manufactured a false FC-4 movement on
leg 5. The golden's full committed input set is therefore:

```
--hindcast-score  results/hindcast/neiso-2021-2025-realized-t1h-d46/NEISO/da19b85495178949/score.json
--crossover-score results/hindcast/neiso-2023-2027-crossover-rcrepair/NEISO/07e416f3f8072e7c/crossover_score.json
--corridor        results/ff-corridor/dispositions/neiso-t3.json
--benchmark-corridor results/ff-corridor/benchmark-corridor-anchors.json
--paired-invariants  <bundle>/fc6/paired_invariants.json
--driver-battery     <bundle>/fc6/driver-battery-neiso-<date>.json
--attestation        <bundle>/forecast_attestation.json
```

### 5.0c A correction to Addendum B's premise, recorded before leg 5 runs

Addendum B pre-declared that GOLDEN-3's FC-5 and FC-6 "were `SKIPPED` on `bau-d46` … they stay
SKIPPED and are reported as such". **That premise is false against the committed record.** Both
the bundle verdict and the board's `neiso-t3` entry read **FC-5 CAVEAT** and **FC-6 CAVEAT**,
carried in `caveats` as `["FC-5 external corridor", "FC-6 driver response"]` — 54 authored
disposition rows (28 IN CORRIDOR / 26 EXPLAINED / 0 UNEXPLAINED) and a four-arm driver battery
with two vacuous gate rows. Addendum B contradicts itself in the same paragraph, saying both
"SKIPPED" and "`neiso-t3` carries them as caveats today"; the second half is the true one.

This matters because it changes what leg 5's outcome means. `score_fc5` and `score_fc6` read
the **authored** verdicts and statuses in those artifacts and never recompute them against the
run, so scoring the new golden *without* them yields FC-5 SKIPPED / FC-6 SKIPPED — an **FC-map
move where §6.4 P16 pre-declared none**, i.e. the charter's STOP, caused by Addendum B's own
false premise rather than by anything the model did. Scoring *with* them reproduces CAVEAT
mechanically, but the FC-5 table carries run-specific `model_value`s (e.g.
`capacity:total@2030` = 33.5307 GW) measured on the pre-flip, pre-D55-hunk run.

**Neither branch is taken on assertion.** Leg 5 is scored both ways, and the carried table is
reconciled row-by-row against the new run's own 2030/2035/2040 values before anything is
registered. Where the two agree the carry is honest and is disclosed as a carry; where they
diverge the disposition is not this lane's to re-author and the registration is a STOP, routed
per the charter — *report, do not register as bare*.

### 5.0d The second-hunk probe — NO second hunk, measured on a real solve

D65's instrument gives the drift exactly two sides. Between D65's basis (`e5ac39f1b2a6`) and
this lane's HEAD, **40 files changed under `src/` + `scripts/`** — D65 Act A's own seam-4 field
among them — so "my HEAD is on D65's side" was an assumption worth **3.6 minutes** to retire.
The charter's own test: *a probe matches the committed side or the HEAD side; anything else is a
second hunk and a STOP-and-report.*

The committed `neiso-t1f` recipe was re-solved for **NEISO 2026–2027** at this HEAD (D65 §3c's
exact instrument, 3.6 min / 3.28 GB, 2/2 years, 14 invariants scored, 0 FAIL / 0 WARN):

| 2027 ledger | `retirements` | total MW | `reserve_margin` | `fleet_by_fuel_after.gas_cc` |
|---|---|---|---|---|
| PRE-hunk (committed `9e48ff6`) | 33 rows | 2,369.81 | 0.045867 | 10,713.80312 |
| POST-hunk (D65's HEAD control) | 40 rows | 2,244.89 | 0.050821 | 10,838.72120 |
| **D60-R3 probe (this HEAD)** | **40 rows** | **2,244.89** | **0.050821** | **10,838.72120** |

**Identical to the POST-hunk side on every ledger key.** So there is no second hunk: the whole
divergence between the committed `neiso-t1f` and HEAD remains capx D55's
`_floor_retention_merit`, and nothing in the 40-file delta since D65 moved this path. **The
STOP does not fire**, and the three legs below are post-hunk by *measurement* rather than by
construction alone — which is what makes their gradings comparable to their PRE-hunk controls
in the first place. The probe bundle is a throwaway diagnostic under rule 29 and was written
outside `results/`; it never reaches `main` (rule 29(c)), and these four numbers are the whole
record of it.

### 5.0e A process defect against myself: I rebased under a running solve, and killed the leg for it

**What happened.** Leg 3 (CAISO) launched at 01:54:41 on HEAD `81022b2d`+this lane's commits.
Four minutes in, a routine `git fetch && git rebase origin/main` — the discipline this program
requires *before every push* — replayed the branch onto `bc77b189`, which had just taken capx
D62's build. `git rebase` checks out the new tree, so **four solve-path files were rewritten on
disk at 01:59:11 while the LP was running**: `config/scenarios.py`,
`config/capacity_market.py`, `model/capacity_evolution/retirements.py` and
`data/avoidable_cost_rate.py` (measured by mtime against the solve's own start time).

**Why that is fatal to the run rather than merely untidy.** Two independent reasons, and either
one alone is disqualifying:

1. **Provenance.** `write_run_config` stamps `git.sha` when it writes, i.e. at the *end* of the
   run. The bundle would have recorded `bc77b189` for a run whose capacity-evolution code was
   `81022b2d`'s for its first four minutes. Every blast-radius classification in the section
   above is computed from exactly that field — a lane that spent this session measuring which
   side of a code boundary each committed bundle sits on cannot then commit a bundle whose own
   stamp is false.
2. **Code mixing.** CPython caches modules after import, so already-imported code is safe; a
   module imported *lazily* later is not. `data/avoidable_cost_rate.py` is precisely that kind
   of on-demand import inside the capacity-evolution path, and D62 changed it. The run could
   have been a genuine mixture of two source trees, undetectably.

**What was done.** The leg was killed, the partial bundle deleted, and the leg re-run from zero
at the settled HEAD `bc77b189`. **Cost: ~5 minutes.** No partial artifact reached `results/` and
none reached `main`.

**The re-check the restart required, and its result.** capx D62 added a `ScenarioConfig` field
(the PJM published-ACR bar, gated default-off), so STOP 1 had to be re-read at the new HEAD
rather than assumed to carry. Re-resolved through the harness path: **17 of 17 keys unmoved**,
including all three legs' targets (`29f8eb372810195f`, `09996eca71ee80fd`,
`f04fd06348e1623d`) and both pinned defaults. D62's field is measured key-neutral, exactly as a
gated default-off field should be.

**The general lesson, worth more than the five minutes.** *"Rebase before every push"* and
*"never mutate the working tree under a running solve"* are both correct and they conflict
whenever a solve outlives a fetch. The resolution is ordering, not judgement: **rebase between
legs, never during one.** This lane now enforces it mechanically — the leg driver records
`HEAD` before the solve and refuses to score or register if `HEAD` moved during it
(`exit 90`), so the failure mode cannot recur silently even if the discipline lapses again.


---

## 6. The pins, and what a moved key does and does not cost

| config | before | after |
|---|---|---|
| `ScenarioConfig()` (forecast default) | `4c6b03ae098b6e3e` | **`e5ecd4105ada3e58`** |
| `ScenarioConfig(mode="backcast")` | `8211c72bb1960adc` | **`6a2845e50951394e`** |
| `ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)` | `4c6b03ae098b6e3e` | `4c6b03ae098b6e3e` (**unmoved**) |
| same, backcast | `8211c72bb1960adc` | `8211c72bb1960adc` (**unmoved**) |

Rows 3–4 are the protection and they are asserted by test: an explicit `False` still equals
the frozen declaration, is still dropped from the hash, and still addresses its pre-flip
bundle — one committed artifact already relies on it
(`results/hindcast/miso-2021-2025-realized-t1h-d55-keyfix`).

**This is not the STOP the charter's "no keeper / backcast key moving" clause names.** That
clause is the D53 **ISO-override** test — an override must never move `ScenarioConfig()`, the
bare backcast key, or another ISO's forecast key — and D60 asserts it unchanged for Q40 and
Q41 (four tests). Q42 is a *default* flip, whose entire mechanism is that the armed default
separates from the frozen drop value; D50 §6.4, the record ruling Q42 was given on,
pre-authorises the consequence in terms. The pre-declaration said so in §3 before the flip
landed, so this was declared, not discovered.

**Cost, exactly:** a one-time cache MISS per config, never a wrong answer — a key that moved
cannot mis-serve. **No committed artifact moves**: no keeper, sidecar, determination or
dashboard row, because those are files rather than cache lookups. Behaviour is byte-identical
for every backcast (which runs no capacity evolution at all, and whose years never reach 2028
and whose measured fleets contain no `gas_cc_ccs` unit) and for every hindcast/crossover
horizon ending before 2028, by §3.3.

Both pins were advanced with dated cause blocks across **26 files**: the two literals in
`tests/regression/test_persisted_identity.py`, a new 2026-09-05 cache-epoch ledger entry in
`src/market_sim/results/cache.py`, the live-pin comment in `scenarios.py`, 21 unit-test pins,
and `CHANGELOG.md`. Where a literal is a **dated historical measurement in prose** it was
left as written, per those files' own convention; the three ERCOT poles in
`test_ercot_stageb_arming.py` / `test_iso_override_precedence.py` moved together by the same
delta and their advance is recorded in each file's own docstring
(`1e1002d480fc180d` → `b5ab30d0fae9f8a3`, `ef70a350ac15fd0f` → `2c3496db2252da1d`,
`11a94474a0c824e3` → `2286402c91a65cf5`).

## 7. The t1x keys — a pre-existing staleness D60 discloses and does not repair

`neiso-t1x` and `nyiso-t1x` **already failed to re-resolve at HEAD before D60 touched
anything**: their committed configs carry two fields deleted under rule 26
(`caiso_bidir_intertie`, `renewable_buildout_pace`) and predate D44's own flip.
`ercot-t1x`, `miso-t1x` and `pjm-t1x` carry **no hex epoch at all** — their provenance blocks
hold the text *"Epoch 2026-08-03 — FFR Wave-2 constants + the D-1/D-2 owner default flips."*
D60's CCS flip is inert on all five (2023–2027 horizons, §3.3), so it neither causes nor cures
this. Repairing the t1x stamps is a different lane's question and is **routed**, not absorbed.

---

---

## 8-blast-radius. The HEAD drift D65 found, its hunk named, and every committed forecast bundle placed on one side of it

Director r#43 folded D65 §3b/§3c into this lane (capx D71): the committed `neiso-t1f`
(`18515067bf4d2fbe`, `git.sha` `9e48ff6`) **no longer reproduces at HEAD from its own
recipe** — NEISO 2027 economic retirements read 33 rows / 2,369.81 MW on the committed side
and 40 rows / 2,244.89 MW at HEAD, deterministically, on an identical stack. The charter asked
for a `git bisect` over `9e48ff6..HEAD` to name the responsible hunk.

**No bisect was spent, and the object was still delivered — by a stronger instrument.** D65
§3d had already pinned the hunk with a **one-hunk revert**: a copy of the exact HEAD tree with
only that hunk reverted (`diff -r` verified: one differing file, one hunk) reproduces the
pre-drift 2027 ledger exactly. A bisect names a *commit*; the revert names the *lines* and
proves them causal. What the bisect would still have supplied is the **commit boundary**, and
that is a content question rather than a solve question — a binary search over `main`'s
first-parent chain for the hunk's own docstring marker returns it in ten `git show | grep`
probes and seconds:

| | commit | date | role |
|---|---|---|---|
| last PRE-hunk commit on `main` | `3e9f191a` (PR #4746, capx D54) | 2026-09-04 19:06:34 −0700 | the boundary's left edge |
| **first POST-hunk commit on `main`** | **`da007e0f`** (PR #4747, `capx-d55-retention-key-fix`) | **2026-09-04 19:06:53 −0700** | the boundary |
| the hunk's own commit | `32f9628c` | — | *"capx D55: floor-retention key 1 as the class constant (D32 §3.2 / R2)"* |

**The hunk, in words.** `src/market_sim/model/capacity_evolution/retirements.py::_floor_retention_merit`
— key 1 of the reliability-floor retention sort. capx D55 replaced the per-unit quotient
`(FOM × multiplier × pmax × 1000) / (pmax × accreditation_fraction)` with the class constant
`(FOM × multiplier × 1000) / accreditation_fraction`. The two are equal in exact arithmetic and
**not** in IEEE-754: the quotient form put same-fuel units on 4–5 distinct floats at the 1e-11
level, so Python's tuple sort consulted the CO2 and heat-rate keys only *inside a rounding
bucket* and the designed three-key ordering was reproduced only piecewise. **It is an
intentional repair** of the defect recorded at D32 §3.2 — and what it also does, necessarily,
is change the retention **sort order**. Under the charter's own clause, *"if it is an
intentional repair (D55's is), the committed bundles are stale and the re-solves you run ARE
the remedy"*: this lane **names it and does not touch it**.

**Why the staleness is silent** (D65 §3d, restated because it is what makes this hard to see):
`_apply_reliability_floor` has three call sites and only two are logged — the returns at
`retirements.py:2565` and `:3486` become `floor_retention_log`, while the call at `:2517`, the
pipeline **admission-cap** screen invoked for its in-place mutation of the `scheduled` set,
**discards its return**. So `floor_retained` is `[]` on both sides of the hunk and the
diagnostic that exists to make floor behaviour visible is blind to exactly the pass D55
re-orders. That is D65's second routed item, not this lane's.

### Every committed forecast bundle, placed — 28 PRE-hunk, 5 POST-hunk

Classified by ancestry of each bundle's own `git.basis_sha` against `da007e0f`. **"PRE-hunk"
means the bundle was solved on the other side of the ordering change, so its reproduction at
HEAD is not established** — it does not by itself mean the numbers move.

| bundle (`results/ff-*/…`) | ISO | cache key | basis | date | side |
|---|---|---|---|---|---|
| `ff-t1f-d45r/miso` | MISO | `8d8bc63a0d4378a9` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d45r/nyiso` | NYISO | `cc7d1050a8090c76` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d45r/pjm` | PJM | `321f04e9060787f0` | `334be8c2a322` | 2026-09-04 | PRE |
| `ff-t1f-d46/caiso` | CAISO | `772b1e5abc7fc80c` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d46/ercot` | ERCOT | `873d8c0e6cab52ae` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d46/neiso` | NEISO | `6690e4d6d66bc819` | `d375bde39a32` | 2026-09-03 | PRE |
| `ff-t1f-d50/ercot` | ERCOT | `0c3e9cd5b5993bdf` | `a35c9f9bc0d1` | 2026-09-04 | **PRE** |
| `ff-t1f-d50/neiso` | NEISO | `18515067bf4d2fbe` | `a35c9f9bc0d1` | 2026-09-04 | **PRE** |
| `ff-t1f-d50/pjm` | PJM | `167e65187f32056b` | `c9f1d26e3463` | 2026-09-04 | POST |
| `ff-t1f-d60/miso` | MISO | `b1a73a087064ffd8` | `b87c057ae4bb` | 2026-09-05 | POST |
| `ff-t1f-d60/nyiso` | NYISO | `19a9690bb12c8459` | `b87c057ae4bb` | 2026-09-05 | POST |
| `ff-t1f-d65-a1/neiso` | NEISO | `8ebed20ae90ec0e7` | `e5ac39f1b2a6` | 2026-09-05 | POST |
| `ff-t1f-d65-ctl/neiso` | NEISO | `18515067bf4d2fbe` | `e5ac39f1b2a6` | 2026-09-05 | POST |
| `ff-t1f-s123/verify` | MISO | `587dc5b32ba71ceb` | `54ca19ae0782` | 2026-08-30 | PRE |
| `ff-t1f-s4hydro/neiso-control` | NEISO | `9a7f68fc7dcac931` | `6136a2964264` | 2026-08-30 | PRE |
| `ff-t1f-s4hydro/neiso` | NEISO | `9a7f68fc7dcac931` | `6136a2964264` | 2026-08-30 | PRE |
| `ff-t1f-s6-pjm/ledger` | PJM | `31a19d815fa319a7` | `54ca19ae0782` | 2026-08-30 | PRE |
| `ff-t3-neiso-golden/bau-d46` + 4 FC-6 arms | NEISO | `67678e58b2d0526c` +4 | `d375bde39a32` | 2026-09-03 | PRE (×5) |
| `ff-t3-neiso-golden/bau-prera-2026-08-31` + 5 FC-6 arms | NEISO | `a4b11ef4aaa1be35` +5 | `9e56f0fecd86` | 2026-08-30 | PRE (×6) |
| `ff-t3-neiso-golden/bau` + 4 FC-6 arms | NEISO | `706e7ba8e6582d42` +4 | `a5523fac1b18` / `5083e29e2562` | 2026-09-01 | PRE (×5) |

**Two measured counter-examples keep "PRE" from being read as "wrong".** capx D55's own A/B
measured `miso-t1h` **byte-identical** across the hunk (retirements and `pipeline_events` every
year, 21/21 FC-3 rows — commit `8181bc64`); D65 measured `neiso-t1f` **materially changed**
(7 rows, −124.92 MW of gas_cc in 2027, with an almost disjoint gas-CC economic-exit set). The
hunk is a **tie-break ordering** change: it bites only where the reliability floor has ties to
break and headroom to spend. Every other PRE-hunk bundle is **unmeasured**, and this finding
says so rather than guessing.

### The bare keys, by side — and D60-R3's routed residue

| bare key | registered run | side today | after this lane |
|---|---|---|---|
| `caiso-t1f` | `caiso-2026-2030-d46-remeasure` | PRE | **POST** (leg 3) |
| `pjm-t1f` | `pjm-2026-2030-d45r-remeasure` | PRE | **POST** (leg 4) |
| `neiso-t3` | `neiso-2026-2050-t3-golden3-bau` | PRE | **POST** (leg 5) |
| `miso-t1f` | `miso-2026-2030-d60-arm` | POST | POST |
| `nyiso-t1f` | `nyiso-2026-2030-d60-arm` | POST | POST |
| `pjm-t1h` | `pjm-2021-2025-realized-t1h-d57-clearing` | POST | POST |
| `ercot-t1f` | `ercot-2026-2030-d50-ccscapex` | PRE | **PRE — residue** |
| `neiso-t1f` | `neiso-2026-2030-d50-ccscapex` | PRE | **PRE — residue** (the D65 case, magnitude measured) |
| `ercot-t1h` | `ercot-2021-2025-realized-t1h-d46` | PRE | **PRE — residue** |
| `caiso-t1h` | `caiso-2021-2025-realized-t1h-d46` | PRE | **PRE — residue** |
| `miso-t1h` | `miso-…-t1h-d53-sectorgate-d51ratio` | PRE | **PRE — residue** (measured INERT by D55) |
| `nyiso-t1h` | `nyiso-…-t1h-d52-devintage` | PRE | **PRE — residue** |
| `neiso-t1h` | `neiso-2021-2025-realized-t1h-d45r` | PRE | **PRE — residue** |

**Seven bare keys remain PRE-hunk after this lane lands.** They are D60-R3's *routed residue*,
not its scope — the charter's owed list is three legs, and re-solving seven more keys is a
separate campaign for the director to charter. `neiso-t1f` is the rung with a measured
magnitude already attached and is the obvious first.

**Board staleness, read before the legs** (`check_forecast_staleness.py`, HEAD `75a5500fdd89`):
155 stamped / 129 scored, newest verdicts evidence `e7412237e4e1` @ 2026-09-05T20:47:38Z, with
**29 solve-affecting commits landed since** against a threshold of 10 — the FR-21 WARN. That
WARN is the same fact this section measures, from the other end.

