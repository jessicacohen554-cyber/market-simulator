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

### 5.0f The hunk the rebase admitted — dated, and what it voids (D60-R4, 2026-09-06)

**§5.0d above was TRUE when it was written at 01:55 UTC and FALSE by the time leg 3 was
committed at 02:26.** This section dates that transition. It is written by the successor lane
D60-R4 and appended in place; §5.0d's own sentences are left exactly as they were, because the
record has to show what was believed and when.

**A naming caution first, because this file now carries two different "hunks."** §8-blast-radius
below names the **D55 `_floor_retention_merit` hunk** — a code change in
`model/capacity_evolution/retirements.py`. §5.0d's probe asked whether a *second* code hunk sat
between D65's basis and this lane's HEAD, and answered no. The object of THIS section is a
different thing entirely: the **SCN-LOAD demand-table hunk**, a change to
`config/constants.py`. It is not a second code hunk on the retirement path, which is why the
probe could be right and the legs still be affected.

**The commit, verified from the trees rather than asserted.**

| | sha | UTC | what |
|---|---|---|---|
| the demand hunk | `d14a7ed0` | **2026-09-06T02:18:26Z** | *SCN-LOAD: curate the six published ISO load forecasts as the load-forecast datatype* |
| its merge to `main` | `ad45b0e4` (PR #4970) | **2026-09-06T02:19:32Z** | — |
| §5.0d's probe commit | `19473c82` | **2026-09-06T01:55:00Z** | *"NO second hunk, and the STOP does not fire"* |

The probe therefore pre-dates the hunk's own commit by **23 min 26 s** and its merge by
**24 min 32 s**. That is not an inference from timestamps: `19473c82`'s
`src/market_sim/config/constants.py` blob is `cc4d9d49`, **byte-identical to `d14a7ed0^`'s**,
so the tree the probe solved on carried the PRE-hunk demand table. `14f860fb`'s blob is
`1437f798` — `d14a7ed0`'s. The lane's own integration of `origin/main` between those two
commits is what admitted it.

**Which rebase.** The AM.1 charter attributes the admission to the lane's *final* rebase
(X-6b, onto `05968ab9`, 03:55:23Z). Measured, that is **too late by ninety minutes**:
`19473c82`'s parent is `09e1092f` (PRE-hunk) and `14f860fb`'s parent is `c2b13cc7` (a `main`
merge POST-`ad45b0e4`), and `19473c82` is an ancestor of `14f860fb`. The hunk entered at the
rebase taken **between the probe and leg 3** — before leg 3 was solved, not after leg 5.
X-6b was POST-hunk too, but it inherited the condition rather than creating it. The
consequence is the wider one: **all three re-solved legs are POST-hunk**, not only legs 4 and 5.

**Each leg's own `run_config.json` `git.sha`, placed by `git merge-base --is-ancestor`:**

| leg | bundle | `git.sha` | side |
|---|---|---|---|
| 4 arm | `results/ff-t1f-d60/pjm` (`09996eca71ee80fd`) | `14f860fb` | **POST-hunk** |
| 4 control | `results/ff-t1f-d45r/pjm` (`321f04e9060787f0`) | `bf54a4ad` | **PRE-hunk** † |
| 5 arm | `results/ff-t3-neiso-golden/bau-d60` (`f04fd06348e1623d`) | `e9d8263b` | **POST-hunk** |
| 5 control | `results/ff-t3-neiso-golden/bau-d46` (`67678e58b2d0526c`) | `012ec403` | **PRE-hunk** |
| 3 arm | `caiso-t1f` (`29f8eb372810195f`) | `14f860fb` | **POST-hunk** |

† `bf54a4ad` is **not resolvable in this clone** — its branch is deleted and
`git fetch origin bf54a4ad` returns *"couldn't find remote ref"* — so its side is established
from its bundle's own `timestamp` (2026-09-04T10:46:10Z, ~40 h before the hunk) and, decisively,
from the ledger arithmetic in §5.4's correction block: its 2027 peak of 163,626.576 MW is the
`mid.near = 0.036` world, and the arm's 174,653.562 MW is the `0.064645` one.

**What moved.** `d14a7ed0` re-derived `DEMAND_GROWTH_RATES` for all six ISOs, plus
`DATACENTER_ADDITIONS_MW` and `ELECTRIFICATION_LAYERS`. The two rows that matter here, read
off `d14a7ed0^` and HEAD:

| ISO | `mid.near` | `mid.long` |
|---|---|---|
| PJM | 0.036 → **0.064645** | 0.024 → 0.023830 |
| NEISO | 0.013 → **0.007446** | 0.012 → 0.013301 |

**A correction to the AM.1 charter itself, recorded because the numbers are load-bearing.**
The charter states *"NEISO 0.031 → 0.054816 and long 0.020 → 0.014850."* Measured, that pair is
**MISO's** row, not NEISO's. NEISO's near rate went **DOWN**, 0.013 → 0.007446 — which is the
only reading consistent with leg 5's own ledger, where every arm peak is *lower* than its
control's (§5.5's correction block). The arithmetic closes independently: at a 2024 weather
year, `(1.007446/1.013)^3 = 0.98365` against a measured 2027 peak ratio of
24,800.853 / 25,213.296 = **0.983644**, and the same construction at 2030 gives 0.967566
against a measured 0.967556.

**The demand table is stable from `14f860fb` to HEAD.** `DEMAND_GROWTH_RATES` and
`DATACENTER_ADDITIONS_MW` compare equal across `14f860fb`, `e9d8263b` and HEAD (the only
`constants.py` movement in that span is two re-export lines), so there is exactly ONE demand
move in this window, and today's HEAD still carries it.

**What this voids.** Under rule 29(b) the incumbent keeper's committed bundle is the control
only when the arm and the control answer the same question. They do not here: the arm carries
a re-derived demand table and the `-pre-d60` prior does not, so **form-4 differencing against
`pjm-t1f-pre-d60` and against `bau-d46` is VOID for legs 4 and 5.** It is *not* void because
the numbers are wrong — every number in §5.4 and §5.5 reproduces exactly — but because their
**attribution** does. §5.4 and §5.5 carry dated correction blocks re-attributing them; the
STOP in §5.4 is untouched and still fired as written.

**Leg 3 is unaffected on the merits** and was already known to be: CAISO's 2030 peak reads
54,820.591 MW on both sides of the hunk, so the CAISO differencing is inert regardless of side.

**Why the pre-declared keys matching proved nothing about this.** `constants.py` is **outside
the cache key**. A matched key says the *config* was the one declared; it is silent on whether
the *constants* the config reads moved underneath it. A matched key is a config audit, never a
G-DRIFT verdict — and this section is the case that shows the difference.

### 5.3 Leg 3 — `caiso-t1f` on `29f8eb372810195f`: every scored row identical, the flip is composition-only

Run `caiso-2026-2030-d60-arm`, `--golden-posture` 2026–2030, **5/5 years, 22.0 min, 4.81 GB**.
The key was matched on the **realized bundle directory**, not merely on the resolved config.
ONE substantive mechanism against the control, verified field-by-field before the solve:
`ccs_retrofit_capex_co2_scaling` absent → `True` — Addendum A.4's "one", confirmed.

**Determination HOLD → HOLD and EVERY SCORED ROW IS IDENTICAL** — FC-1 `FAIL ['I12','I7']` on
the same three years with the same MW, FC-2 row1 FAIL / row3 PASS / **row4 FAIL at 52.6 % in
both arms**, FC-5 and FC-6 SKIPPED in both, FC-7 CAVEAT in both, FC-8 PASS in both. **P13 HIT.**

Where the flip *does* show is the retrofit ledger, composition-only exactly as §6.3 pre-declared:

| year | control rows / MW (CHP rows / MW) | arm rows / MW (CHP) |
|---|---|---|
| 2028 | 37 / 2,997.1 (26 / 843.1) | 10 / 2,903.1 (**0 / 0.0**) |
| 2029 | 12 / 2,997.9 (5 / 632.4) | 9 / 2,932.1 (**0 / 0.0**) |
| 2030 | 11 / 2,857.3 (8 / 567.6) | 3 / 2,787.0 (**0 / 0.0**) |
| **window** | **60 rows / 8,852.4 MW** (2,043.2 CHP) | **22 rows / 8,622.2 MW** (0 CHP) |

- **P12 HIT on both limbs** — every year inside the pre-declared 2,850–3,000 MW band; window
  8,622.2 MW inside the pre-declared 8.6–9.0 GW. Falsifier (*any CHP row converting, or a year
  below 2.5 GW*) does not fire.
- **P11 HIT** — seam 1, the scaled bar, is **inert on CAISO**: the 3 GW/yr cap still binds in
  every eligible year, so the entire change is seam 2, the CC_CHP host exclusion, and the cap is
  refilled by fewer, larger non-CHP hosts (60 rows → 22 for nearly the same MW).

**No STOP fires.** FC-2 row4 did not rise; no CHP row converted; every year's conversion count
*fell*. FC-7 stays CAVEAT on one **pre-existing** UNIDENTIFIED entry, `negative_renewable_offers`
— a CAISO override outside this batch that Addendum D.2 pre-declared the Q37 rows would not
repair. Left untouched and **routed**: writing an identification row this lane holds no
pre-declaration for is exactly what Q37's limb is narrow to prevent.

### 5.4 Leg 4 — `pjm-t1f` on `09996eca71ee80fd`: a pre-declared STOP fired, and the cause is a requirement P23 assumed would not move

Run `pjm-2026-2030-d60-arm`, **5/5 years, 36.2 min, 8.81 GB**. FOUR mechanisms against the
control (Addendum C.2's "four"), verified field-by-field before the solve. **Determination
HOLD → HOLD** (P24 HIT).

**THE STOP.** Addendum C.4 declared *"any I12 year more negative than the control's"* a STOP.
Every comparable year is:

| I12 | 2027 | 2028 | 2029 | 2030 |
|---|---|---|---|---|
| control | −11.2 % | −13.5 % | −13.1 % | −13.0 % |
| **arm** | **−11.6 %** | **−15.6 %** | **−15.8 %** | **−16.5 %** |

**P23's direction held; its premise did not.** Accredited firm rose exactly as pre-declared —
**+9,092 / +10,276 / +14,303 / +18,000 MW** in 2027–2030 — but P23 assumed *"an unchanged
requirement"*, and the requirement is not unchanged: it rose by **more**, +16,220 / +21,607 /
+27,272 / +33,504 MW. Supply lengthened and the position still worsened.

**Attributed, not inferred** (Amendment 1 item 3). The requirement is **byte-identical between
the control and the committed D50 arm** (145,509 / 150,263 / 153,001 / 155,946 in both), so Q42
moves it not at all and the entire rise belongs to the D48 + D57 gates. The mechanism is D48's
own construction: `pjm_demand_response_supply` counts offered DR UCAP as supply **with the peak
un-netted**, so both sides rise, and `pjm_accreditation_design_vintage` applies the post-CIFP FPR
from DY 2025/26. **2026–2030 is the first horizon on which that FPR is in force for every
delivery year**, and this is its first measurement: *D48's accounting is not position-neutral
forward — it lengthens the requirement faster than it lengthens counted supply.* **Routed to the
director**; nothing reverted, no gate moved.

- **P21 HIT to the digit** — CCS window 3,584.7 → **909.8 MW**, reproducing the committed D50
  arm exactly (2029: 2 rows / 909.8 MW; 2028 to zero).
- **P22 HIT decisively**, mechanism confirmed at ledger grain — FC-2 row4: control **43.9 % FAIL**
  → D50-arm-alone **48.9 % FAIL** (the CCS half pushes *up*, as pre-declared) → this arm
  **25.6 % CAVEAT**. The halves oppose and the clearing half dominates, because economic gas_ct
  entry rises 11,014 → **12,642 MW** (+1,628) and displaces administrative backstop build.
- **P25 is VACUOUS, and is graded that way.** Every PJM exit on this horizon is **exogenous** —
  16 announced + 2 confirmed, **zero economic**, `pipeline_events` empty in all five years — and
  the exit set is byte-identical across the control, the D50 arm and this arm. No mechanism could
  move the composition: the falsifier's condition is met but its premise is void.

**Two misses against my own pre-declaration**, recorded rather than smoothed: wall **36.2 min**
against Addendum C's ~28; and Addendum D.2 pre-declared "4 entries, 3 unattested" where the
ledger emits **3 entries, 2 unattested** — `capacity_market_supply_clearing_by_iso = {"PJM": True}`
carries no numeric leaf, so `_is_parameterish` skips it entirely and its Q37 row is dormant, as
row 7's already is.

**Correction, D60-R4 2026-09-06: the +16,220 / +21,607 / +27,272 / +33,504 MW requirement rise
is MOSTLY THE DEMAND TABLE, not the gates.** Nothing above is withdrawn and no number above is
wrong; what is corrected is the sentence *"the entire rise belongs to the D48 + D57 gates."*
§5.0f dates the cause: the arm was solved POST-`d14a7ed0`, on a re-derived `DEMAND_GROWTH_RATES`
where PJM's `mid.near` reads **0.064645** against the `-pre-d60` control's **0.036**, so the
control and the arm are not standing on the same peak. Rule 29(b) form-4 differencing against
`pjm-t1f-pre-d60` is VOID for this leg (§5.0f), and the attribution below replaces it.

**Read from the two committed `evolution_<year>.json` ledgers, zero LP.** With `P` the ledger's
`peak_demand_mw`, `R` its `adequacy_requirement_mw` and `r = R/P`:

`ΔR = (P_arm − P_ctl)·r_ctl  +  P_arm·(r_arm − r_ctl)` — the **peak leg** and the **ratio leg**.

| yr | P ctl | P arm | R ctl | R arm | r ctl | r arm | ΔR | peak leg | ratio leg | peak share | r_ctl/r_arm |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026 | 161,027.171 | 167,211.957 | 141,805.164 | 153,333.365 | 0.880629 | 0.917000 | +11,528.2 | +5,446.5 | +6,081.7 | 47.2 % | 0.9603367 |
| 2027 | 163,626.576 | 174,653.562 | 145,508.504 | 161,729.198 | 0.889272 | 0.926000 | +16,220.7 | **+9,806.0** | **+6,414.7** | **60.5 %** | 0.9603367 |
| 2028 | 166,438.970 | 182,820.460 | 150,263.195 | 171,869.515 | 0.902813 | 0.940100 | +21,606.3 | **+14,789.4** | **+6,816.9** | **68.4 %** | 0.9603367 |
| 2029 | 169,472.022 | 191,759.540 | 153,001.472 | 180,273.143 | 0.902813 | 0.940100 | +27,271.7 | **+20,121.5** | **+7,150.2** | **73.8 %** | 0.9603367 |
| 2030 | 172,733.675 | 201,520.718 | 155,946.134 | 189,449.627 | 0.902813 | 0.940100 | +33,503.5 | **+25,989.3** | **+7,514.2** | **77.6 %** | 0.9603367 |

Residual `ΔR − peak − ratio` is ≤ 6.4e-12 MW in every year — the decomposition is exact, not
approximate, because `r` is provably peak-INDEPENDENT here: for PJM every branch of
`resolve_adequacy_requirement_mw` is multiplicative in the peak (`firm_peak × FPR`, or the
`(1+PRM) × icap_to_ucap` fallback, times `(1 − dr_fraction)`), so `r` is a pure function of
`(config, iso, year)` and the split cannot leak between legs.

**The peak leg is 60–78 % of the rise in every comparable year and it is the SCN-LOAD hunk.**
It is nobody's gate. **The ratio leg — +6,415 / +6,817 / +7,150 / +7,514 MW — is the only part
the Q44 gates own.**

**And within the gates the attribution is sharper than §5.4 assumed.** `r_ctl / r_arm` is
**0.9603367 in every year, to seven figures**, and
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"] = 0.03966325587762226`, i.e. `1 − f =
0.9603367441`. The arm's requirement is exactly the control's divided by `(1 − f)`. So:

* the **entire** ratio leg is `pjm_demand_response_supply` — D48's DR-as-supply limb declining
  to net DR out of the peak (`resolve_adequacy_requirement_mw` returns `gross_mw` un-netted when
  `resolve_demand_response_supply_mw` returns a MW);
* `pjm_accreditation_design_vintage` moved the requirement by **ZERO** on 2026–2030. `gross_mw`
  is identical on both sides, so the FPR the devintage selects is the one the control's path
  already resolved. §5.4's *"and `pjm_accreditation_design_vintage` applies the post-CIFP FPR
  from DY 2025/26"* is true as a description of the mechanism and **not** a description of
  anything that moved this requirement;
* D57's supply clearing does not enter `resolve_adequacy_requirement_mw` at all.

**THE STOP IS NOT SOFTENED. It fired as written and it stands.** Every comparable I12 year is
more negative than the control's, exactly as Addendum C.4 declared, and P23's premise
("an unchanged requirement") was still false. What changes is only *why*: most of the
requirement rise was a demand re-derivation the leg did not control for, so the sentence
*"D48's accounting is not position-neutral forward"* is **NOT ESTABLISHED by this pair** — it is
a claim the pair cannot separate from the demand table. Whether it is true is what D60-R4's one
earned same-HEAD control (Addendum E) is spent to decide. Supply rose +9,092 / +10,276 /
+14,303 / +18,000 MW against a ratio leg of +6,415 / +6,817 / +7,150 / +7,514 — supply exceeds
the gate-owned rise in every year — so the pre-declared reading is that the same-HEAD control
will show D48 lengthening the position, not shortening it; the falsifier is any year where it
does not.

### 5.5 Leg 5 — `neiso-t3` GOLDEN-3 on `f04fd06348e1623d`: the FC map does not move, and the carried FC-5 table is measured for the first time

Run `neiso-2026-2050-t3-golden3-d60`, `--golden-posture --full-solve-authorized`, **25/25 years,
3.37 GB**. ONE substantive mechanism against the control. **P16 HIT exactly: determination
HOLD → HOLD, identical reasons and caveats, and ZERO of the 19 scored rows changes status.**
One within-row improvement worth naming inside a still-failing row: the FC-2 row3 cobweb goes
`gas_ct(7); gas_cc(11)` → `gas_cc(13)` — the gas_ct cobweb disappears entirely.

**P14 / P15 on the 25-year retrofit ledger.** Control converts **11,208.9 MW** over 2028–2031
(17 / 23 / 10 / 10 rows, 377.1 MW of it CHP); the arm converts **10,423.6 MW** over the same four
years (12 / 11 / 10 / 6 rows) with **zero CHP MW**. **The P15 falsifier does not fire on either
limb** — 10.42 GW is inside the pre-declared 10.4–11.3 GW band, and conversion still ends in
**2031**, before the pre-declared 2032 bound. **A miss recorded against myself:** P15 said the
window would lose *"at most ~0.4 GW"* and it loses **785.3 MW**. The band held; the point
estimate did not — the same class of miss leg 1 recorded against its own §6.1 upper bound.

**FC-7 PASS on all four rows including the §5 attestation. P20 HIT exactly:** 7 entries, 7
IDENTIFIED, 0 UNIDENTIFIED, 0 unattested, and **no CCS entry** — Q42 made the field the dataclass
default and the ledger enumerates non-default fields. The attestation is authored by the
**producing session** (rubric §5's default author, unlike D47's disclosed deviation) on six
assertions fixed in advance in Addendum B and pushed before this bundle existed; all six read
TRUE from committed bytes.

**What the attestation does not claim, stated rather than buried.** FC-5's dispositions and
FC-6's battery are **carried, not re-measured**. Carrying is the committed practice — D25 authored
the FC-5 table against `results/ff-t3-neiso-golden/bau`, and D46/D47 carried it unre-authored onto
`bau-d46`. What this lane adds is the **measurement of the carry that no prior lane took**:

- The carried table is **already stale against the bundle it is attached to**, on **6 of 42
  computable rows** past the corridor memo's own 15 % explanation threshold. Worst: `co2@2040`,
  table 4.4883 vs `bau-d46` 9.5792 (**+113.4 %**); `capacity:pumped_storage` **+41.3 %** in all
  three anchor years.
- This lane's own marginal movement `bau-d46 → bau-d60` is **smaller than that pre-existing gap**
  and clears the memo's threshold on every real quantity: 10 rows move > 5 %, the largest being
  `co2` −9.1 / −12.8 / −10.7 % and `generation:gas` −10.1 / −11.8 / −10.2 % across 2030 / 2035 /
  2040. The `co2@2040` movement **reduces** the pre-existing table gap rather than widening it.

**Re-authoring the table is routed, not absorbed** — D25 was a dedicated lane for it and this one
holds no pre-declaration to re-author 54 verdicts. **Addendum B's own premise was wrong** and is
corrected in §5.0c: it pre-declared FC-5 / FC-6 "SKIPPED", where the committed record reads
CAVEAT on both.

**Correction, D60-R4 2026-09-06: "ONE substantive mechanism against the control" is FALSE as a
description of the difference between these two bundles.** It is true of the *config* — the
field-by-field verification above stands, `ccs_retrofit_capex_co2_scaling` really is the only
`ScenarioConfig` field that moved — but `constants.py` is outside the cache key and outside the
config diff, and the arm was solved POST-`d14a7ed0` while `bau-d46` is PRE (§5.0f). NEISO's
`mid.near` went **0.013 → 0.007446** and `mid.long` **0.012 → 0.013301**: the arm is a
**LOWER-demand world**. Rule 29(b) form-4 differencing against `bau-d46` is VOID for this leg.

**The peaks, read from the committed ledgers (zero LP):**

| yr | peak ctl | peak arm | Δ | Δ % | requirement ctl | arm | `r` both sides |
|---|---|---|---|---|---|---|---|
| 2027 | 25,213.296 | 24,800.853 | −412.4 | **−1.64 %** | 25,934.571 | 25,510.329 | 1.028607 |
| 2030 | 26,209.453 | 25,358.989 | −850.5 | **−3.24 %** | 26,959.225 | 26,084.433 | 1.028607 |
| 2035 | 27,847.707 | 26,934.418 | −913.3 | **−3.28 %** | 28,644.345 | 27,704.930 | 1.028607 |
| 2040 | 29,559.155 | 28,773.981 | −785.2 | **−2.66 %** | 30,404.752 | 29,597.117 | 1.028607 |
| 2050 | 33,304.056 | 32,838.603 | −465.5 | **−1.40 %** | 34,256.784 | 33,778.015 | 1.028607 |

`r = R/P` is **identical to six decimals on both sides in every year**, so the §5.4-style
decomposition gives a ratio leg of ≤ 0.001 MW and a peak leg of 100.0 %: unlike PJM, NEISO has
**no gate contribution at all** here. The entire requirement difference is the demand table.

**The >5 % movements carry the sign of a lower-demand world, not of fewer retrofits.** Total
generation moves in lockstep with the peak — **−3.24 / −3.30 / −2.64 %** at 2030 / 2035 / 2040
against peak **−3.24 / −3.28 / −2.66 %** — and on that base the gas-family and CO2 movements
this section reported are what a ~3 % demand cut does to the marginal fuel:

| | 2030 | 2035 | 2040 |
|---|---|---|---|
| `co2_mt` | 14.710 → 13.368 (**−9.12 %**) | 10.221 → 8.912 (**−12.81 %**) | 9.579 → 8.559 (**−10.65 %**) |
| gas-family TWh | 36.457 → 32.762 (**−10.14 %**) | 31.891 → 28.118 (**−11.83 %**) | 31.001 → 27.839 (**−10.20 %**) |

These reproduce the −9.1 / −12.8 / −10.7 % and −10.1 / −11.8 / −10.2 % reported above to the
decimal; what changes is that they are **not** attributable to Q42.

**P16 STANDS, as a STATUS reading.** Determination HOLD → HOLD with zero of 19 scored rows
moving is a fact about the two bundles and is unaffected: it says the FC map is insensitive to
*everything* that separates them, which is now known to include a demand re-derivation as well
as the Q42 flip. As a claim about Q42 alone it is not established by this pair.

**P14 / P15 stand as written** — 11,208.9 → 10,423.6 MW over 2028–2031, inside the pre-declared
10.4–11.3 GW band, conversion still ending in 2031, and the recorded miss against P15's
"at most ~0.4 GW" point estimate is kept at full magnitude. **What is added: the retrofit window
now carries a demand co-movement, and it is where the −785.3 MW actually sits.**

| yr | ctl rows / MW | arm rows / MW | Δ MW | peak Δ |
|---|---|---|---|---|
| 2028 | 17 / 2,999.6 | 12 / 2,984.4 | −15.2 | −2.18 % |
| 2029 | 23 / 2,994.4 | 11 / 2,912.0 | −82.4 | −2.71 % |
| 2030 | 10 / 2,948.6 | 10 / 2,936.5 | −12.1 | −3.24 % |
| **2031** | 10 / 2,266.3 | 6 / **1,590.7** | **−675.6** | **−3.78 %** |

**86.0 % of the window's entire loss is 2031**, the one year of the four in which the 3 GW/yr
cap does not bind on either side — and the year in which the two demand worlds are furthest
apart. In 2028–2030 the cap binds and the arm tracks the control to within 0.5 %. So the
window's shortfall reads as the cap ceasing to bind in a lower-demand world, not as the capex
repair closing a screen. Q42's own signature in this leg remains the **composition** change
(zero CHP MW), which is a within-cap effect and is unaffected by the peak.

**Nothing here is re-solved and nothing is routed differently.** The re-authoring of the carried
FC-5 table stays routed as §5.5 left it, and the pre-existing staleness measured above
(6 of 42 rows past the 15 % threshold, worst `co2@2040` +113.4 %) is untouched.

---

## 8. Instrument repair — the Q37 rows, and what they did and did not move

D60 Amendment 2 resolved leg 2's P10 STOP under **owner ruling Q37** (r#34, rubric §5 second
limb): *a follow-up lane may author an attestation iff pre-declared before authoring, attestation
row only, artifact-only re-score.* The pre-declaration is **Addendum D**, on `main` before a
single row was written and before any of the three outstanding legs' FC-7 rows had been read.

**Six new rows** in `CURATED_IDENTIFICATIONS`, all keyed `(ISO, field)` — never `("*", field)` —
so each is rule 25 `[R-ISO-SCOPE]`-scoped by construction, and all carrying
`requires: "iso-registry"` so a run carrying the field from anywhere but the live registered
override stays UNIDENTIFIED and the artifact records the refusal:

| ISO | field |
|---|---|
| NYISO | `nyiso_requirement_forecast_peak`, `nyiso_requirement_vintage_factors` |
| MISO | `adequacy_accounting_ratio_dated_net` |
| PJM | `pjm_accreditation_design_vintage`, `pjm_demand_response_supply`, `capacity_market_supply_clearing_by_iso` |

Row 7 (`ccs_retrofit_capex_co2_scaling`) needed no edit and got none: D50 committed it, and Q42
made it the dataclass default, so it no longer appears in any post-flip bundle's ledger and its
curated row is **dormant** — exactly the mechanism P20 pre-declared for GOLDEN-3.

**The five artifact-only re-scores — same bundle, same bytes, same key, only the ledger's LABELS
changed. Every Addendum D.2 prediction HIT:**

| bare key | ledger after | FC-7 | determination |
|---|---|---|---|
| `nyiso-t1f` | 3 entries, **3 identified** | **CAVEAT → PASS** | **PROMOTE-WITH-CAVEATS → PROMOTE** |
| `miso-t1f` | 7 entries, **5 unattested** | CAVEAT → CAVEAT | HOLD → HOLD |
| `caiso-t1f` | 2 entries, **1 unattested** | CAVEAT → CAVEAT | HOLD → HOLD |
| `pjm-t1f` | 3 entries, **3 identified** | **CAVEAT → PASS** | HOLD → HOLD |
| `neiso-t3` | 7 entries, **7 identified** | PASS → PASS | HOLD → HOLD |

**FC-7 was the ONLY row that moved on any of the five — zero non-FC-7 movements**, measured
row-by-row across all eight categories of all five bundles. That is what Addendum D.3 required
and what makes the re-score honest: a `CURATED_IDENTIFICATIONS` row is read by one consumer,
`_apply_curation`, and cannot reach a `ScenarioConfig` field, a cache key, a solve, a trajectory
or any other FC category. **The model rows are unmoved.**

**The one determination that moves** is `nyiso-t1f` **PROMOTE-WITH-CAVEATS → PROMOTE** — the
repair of leg 2's P10 STOP, and the entire reason Amendment 2 exists. Nothing else moves.

**Two blunt negatives, pre-declared and honoured rather than quietly widened.** MISO's FC-7 does
**not** clear: the ratio row is written and MISO still reads CAVEAT, because five MISO overrides
outside this batch (`entry_vre_capacity_revenue`, `entry_vre_zone_selection`,
`miso_rps_compliance_regions`, `miso_clean_tier_rows`, `retirement_sector_gate`) remain
unattested. CAISO's FC-7 is untouched — `negative_renewable_offers` is a pre-existing override
this batch does not reach. Both are **routed**, not absorbed; widening the scope to make a row
read PASS is precisely what Q37's limb is narrow to prevent.

### 8.1 The D57 interaction (Amendment 1 item 3)

Two legs carry more than one mechanism, and each moved row is attributed to **one**, from a
committed single-mechanism record rather than by inference:

- **`miso-t1f`** (leg 1, D60): three mechanisms — D53's sector gate (measured to move nothing:
  every retirement row byte-identical), Q40's ratio (what moves the board), Q42 (a measured null,
  0 MW converted).
- **`pjm-t1f`** (leg 4): four mechanisms. Q42's half is isolated by the committed D50 arm and
  reproduces it to the digit (909.8 MW); the D48 + D57 half owns the entire requirement rise,
  established by the requirement being **byte-identical** between the control and that D50 arm.

### 8.2 The board's per-ISO rows, before and after this lane

| ISO · key | before | after |
|---|---|---|
| CAISO `t1f` | HOLD (FC-7 CAVEAT) | HOLD (FC-7 CAVEAT — unchanged, routed) |
| PJM `t1f` | HOLD (FC-7 PASS, 1-entry ledger) | HOLD (FC-7 PASS on a 3-entry ledger; FC-8 CAVEAT) |
| NEISO `t3` | HOLD (FC-7 PASS) | HOLD (FC-7 PASS) |
| MISO `t1f` | HOLD (FC-7 CAVEAT) | HOLD (FC-7 CAVEAT — five overrides still unattested) |
| **NYISO `t1f`** | **PROMOTE-WITH-CAVEATS** | **PROMOTE** |

**One determination moved across the entire lane**, and it is the one Addendum D.3 named in
advance.


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

---

## 9. Close — what D60 is, and what it is not

D60's own close condition: *"D60 is COMPLETE when every bare key named in Addendum A §A.2 carries
a post-D60 `scored_at_sha` and every `-pre-d60` prior exists."*

**All nine `-pre-d60` priors exist** — `ercot-t1f`, `neiso-t1f`, `miso-t1f`, `nyiso-t1f`,
`miso-t1h`, `nyiso-t1h` from D60 itself, plus `caiso-t1f`, `pjm-t1f` and `neiso-t3` from this
lane. No earlier preserved baseline (`-pre-d53`, `-pre-d46`, `-pre-d45r`, `-pre-d47` …) was
overwritten.

**The `scored_at_sha` half is met for eleven of thirteen keys, and the two exceptions are named
rather than waved through.** `ercot-t1f` and `neiso-t1f` still carry `9e48ff6820b0` — the sha of
the D50 bundle each was *renamed onto*, which is pre-D60 by construction, because a Class-A
rename points a key at a committed bundle and does not re-score it.

Those are **the same two keys §8-blast-radius identifies as PRE-hunk residue**, and the
coincidence is not one: a key that was never re-solved after D60 is exactly a key that was never
re-solved after capx D55's `_floor_retention_merit` hunk either. So the honest reading of the
close is:

> **D60's five re-solves are complete and its instrument repair is complete. Its rename half is
> complete as a rename and incomplete as a re-measure** — and the residue is `ercot-t1f`,
> `neiso-t1f` and the five t1h keys, seven in total, all routed to the director as a separate
> campaign rather than absorbed here.

`neiso-t1f` is the rung with a measured magnitude already attached (D65 §3c: 7 rows, −124.92 MW
of gas_cc in 2027) and is the obvious first.

**What this lane did not do, stated so it is not assumed.** No keeper, no shard promotion field,
no `complete` / `final` marker, no freeze, no default, no new `ScenarioConfig` field, no
parameter value, no mechanism-matrix cell (rule 28: this lane tested no mechanism — the bisect
names a hunk, it does not adjudicate one), and nothing against measured H1-2026 (rule 22: t1f
2026–2030, t3 2026–2050, all forecast mode). The D55 hunk was **named and not touched**; the
FC-5 disposition table was **carried and measured, not re-authored**; the five unattested MISO
overrides and CAISO's one were **routed, not absorbed**.

### 9.1 Governance attestation

| gate | reading |
|---|---|
| rule 22 quarantine | every solved year in 2026–2050, forecast mode, no measured actual touched |
| rule 24 off-registry knobs | zero — every solve-affecting field in all three `run_config.json` is a declared `ScenarioConfig` field |
| rule 25 ISO scope | all six new curated rows keyed `(ISO, field)`, none `("*", field)`; no ISO's value can identify another's |
| rule 21 DOF | no parameter value chosen anywhere in this lane |
| rule 28 matrix | no cell moved; no mechanism tested |
| `check_cache_key_registration.py --base origin/main` | **ok** — 798 fields, 253 registered, all resolve |
| `tests/unit/config/test_d60_arming_batch.py` | **17 passed** |
| `tests/regression/test_persisted_identity.py` | **14 passed** |
| `ruff format` / `ruff check` on the edited scorer file | clean |
| rule 27 blob verification | every push verified: `ff-verdicts.json` (13,175 lines), `program-status.json`, `register_forecast_run.py`, and each bundle's `run_config.json` + `full_horizon_summary.json` — byte-identical local vs remote on all three legs |
| STOP 1 (key drift) | re-read at **four** separate HEADs as `main` moved under the lane; **17/17 unmoved every time** |

### 9.2 Every prediction, graded

| id | prediction | verdict |
|---|---|---|
| P11 | CAISO seam 1 inert, whole change is seam 2 | **HIT** |
| P12 | CAISO 2,850–3,000 MW/yr, zero CHP, window 8.6–9.0 GW | **HIT** (both limbs) |
| P13 | CAISO HOLD → HOLD, gated rows capacity-identical | **HIT** |
| P14 | GOLDEN-3 cap-bound, CHP only 3.4 % of the pool | **HIT** |
| P15 | window loses "at most ~0.4 GW", ends by 2032, total 10.4–11.3 GW | **falsifier does not fire** (10.42 GW, ends 2031); **point-estimate MISS** — 785.3 MW lost |
| P16 | GOLDEN-3's FC map does not move | **HIT** (0 of 19 rows) |
| P20 | GOLDEN-3 ledger 7 IDENTIFIED / 0 UNIDENTIFIED, no CCS entry | **HIT** |
| P21 | PJM CCS window → 909.8 MW, reproducing the D50 arm | **HIT to the digit** |
| P22 | PJM FC-2 row4 DOWN against 43.9 %, clearing half dominates | **HIT** (25.6 %) |
| P23 | PJM I7/I12 improve but do not clear, requirement unchanged | **direction HIT, premise MISS, falsifier FIRES → STOP** |
| P24 | PJM HOLD → HOLD, FC-8 CAVEAT ~9 GB | **HIT** (FC-7 CAVEAT → PASS via the Q37 rows, as D.2 pre-declared) |
| P25 | PJM exit composition follows D57's t1h signature | **VACUOUS** — the screen decides nothing on this horizon |
| D.2 ×5 | the five FC-7 / determination outcomes | **HIT, all five** |

**Four misses recorded against myself**, none smoothed: the leg-4 wall estimate (36.2 vs ~28
min); P15's "at most ~0.4 GW"; Addendum D.2's "4 entries / 3 unattested" for PJM; and Addendum
B's false premise that GOLDEN-3's FC-5 / FC-6 were SKIPPED (§5.0c). Plus one **process** defect,
§5.0e: I rebased under a running solve and killed the leg for it.

---

## Addendum E — D60-R4's one earned control: the drift audit, a defect found on the way, and the pre-declaration (2026-09-06)

§5.0f voids form-4 differencing for legs 4 and 5. Rule 29(b) says a **LIVE** hunk is the only
thing that earns a control solve, and then only for the years the screen needs. This addendum
is the audit that earns it, the pre-declaration that fixes its reading before it runs, and
(E.4) its result. **E.1–E.3 were pushed before the solve was launched**, so nothing here can be
written to fit an outcome.

### E.1 G-DRIFT — the window `15631b8c..HEAD`, hunk by hunk

`git diff 15631b8c HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib` → **9 files, +697 / −58**. Every hunk classified,
for a **PJM `mode="forecast"` solve launched through `scripts/run_full_horizon.py`**:

| # | file | hunk | verdict | why |
|---|---|---|---|---|
| 1 | `config/constants.py` | +1 re-export, `resolve_capacity_adequacy_requirement_published` | **INERT** | import surface only; the resolver is reached through the gated `capacity_adequacy_requirement_published`, default-OFF and absent from both recipes |
| 2 | `config/scenarios.py` | `nyiso_ct_peaker_bands_measured: bool = False` + its two cache-key registry rows | **INERT** | another ISO's branch (arming it on a non-NYISO ISO raises), default-off, absent from the recipe; registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `"False"` so the bare key does not move |
| 3 | `pipeline/backcast_config.py` | the `if nyiso_ct_peaker_bands_measured:` block | **INERT** | same field, same guard; and `backcast_config` is not on the forecast path |
| 4 | `model/lp/model.py` | simplex-iteration + objective read-back folded into the log line | **INERT** | a diagnostic read AFTER `h.run()`, inside `try/except`; it consumes the solved model and writes nothing back |
| 5 | `pipeline/solve.py` | the same-year **P1 basis seed** (#5054) | **INERT — verified from code** | see below |
| 6 | `pipeline/solve.py` + `utils/heap.py` (deleted) | the **P1-seam `malloc_trim` removal** (`9440f17d`) | **INERT on every solved value** | see below |
| 7 | `pipeline/solve.py` | `model is not None` guard + `getattr` tolerance on the pre-rebuild basis export | **INERT** | with `_p1_seed` false the condition `(xyear_cache is not None or _p1_seed)` reduces to the original `xyear_cache is not None`, and the guard only converts a `None` dereference into a no-op; the `elif _p1_seed and _reuse_p0` branch is unreachable |
| 8 | `scripts/lib/invariant_ledger.py` | new module, +268 | **INERT** | reached (via `check_forecast_invariants`) but used only at lines 1250–1350, the `--sidecar-dir` audit and the registration ratchet; it reads a committed JSON ledger and cannot touch the LP or the in-run I1–I14 scoring |
| 9 | `scripts/run_calibration.py` | +111, incl. `resolve_p1_basis_seed_default` | **INERT** | backcast CLI; **not imported** on this path (measured: `sys.modules` after `import scripts.run_full_horizon` → absent) |
| 10 | `scripts/run_calibration_full.py` | +55 | **INERT** | same; also not imported |

**Hunk 5, verified from the code rather than its docstring** (the charter's explicit ask). The
gate is

```
_p1_seed = (_xwarm and xyear_warmstart is None
            and os.environ.get("MARKET_SIM_P1_BASIS_SEED", "0") != "0")
```

and `runner.py:3551` passes `xyear_warmstart=config.forecast_xyear_warmstart` on every forecast
solve. That field is a **`bool` with default `True`** (`dataclasses.fields(ScenarioConfig)`),
never `None`, so `xyear_warmstart is None` is False and `_p1_seed` is False **unconditionally on
the forecast path** — no env var can reach it. `_seed_basis` therefore stays `None`, the seeded
branch is not entered, and control falls to the `else:` that calls the identical
`solve_dispatch(p1_fleet_arrays, demand, mc=mc_bid, **p1_dispatch_kwargs)` the pre-hunk tree
called. Independently and redundantly: `run_full_horizon.py` does not import
`scripts.run_calibration` (measured above), so `resolve_p1_basis_seed_default` never runs and
`MARKET_SIM_P1_BASIS_SEED` is unset in this process (measured: `None`).

**Hunk 6, stated at full magnitude rather than waved through.** `malloc_trim` frees only heap
the allocator already considers free, so it cannot touch a live object and **cannot move a
number** — INERT on every solved value, in both directions. It is *not* inert on memory, and
this box is 15 GB against an arm that peaked at 8.81 GB, so the honest statement is the measured
one from the removing commit `9440f17d`: on the ERCOT carve-out replay the trim moved process
peak **13.28 → 13.27 GB** and cost `p1_post` +0.1–0.5 s, i.e. it was reclaiming essentially
nothing (the ~1.15 GB seam step is live payload, not glibc retention). Its removal is therefore
not expected to raise this leg's peak materially. That is an ERCOT-grain measurement carried to
PJM; it is recorded as a carried measurement, not as a PJM one.

**ALL TEN HUNKS INERT.** Under rule 29(b) that makes form 4 valid *for the code*. It is the
**demand table** — outside every one of these files, and outside the cache key — that is LIVE
between the arm and its `-pre-d60` prior, and that is what earns the control.

**A cross-check the audit produced for free:** `reference_config("PJM", 2026, 2030,
golden_posture=True)` resolved at HEAD gives cache key **`09996eca71ee80fd`** — bit-for-bit the
committed arm's key. The drift did not move the arm's recipe either.

### E.1b The charter's drift window is TOO NARROW, and the extra span audited

**Found while building the control, and recorded before it ran.** The AM.1 charter names the
window `15631b8c..HEAD`. But `15631b8c` is D60-R3's *finding-close* commit (04:02:45Z), and the
**arm was solved an hour earlier at `14f860fb`** (03:02:42Z). The falsifier compares the arm's
committed I12 against a control solved at HEAD, so the window that governs their comparability
is `14f860fb..HEAD`, not `15631b8c..HEAD`. The charter's window misses **18 files, +810 / −44** —
including `model/capacity_evolution/retirements.py` (+60), squarely on the forecast
capacity-evolution path. Auditing only the named window would have declared comparability on a
span that excludes the most solve-relevant file in it.

`git diff 14f860fb 15631b8c -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/run_full_horizon.py scripts/lib`, classified:

| file(s) | hunk | verdict | why |
|---|---|---|---|
| `model/capacity_evolution/retirements.py` (+60), `config/capacity_market.py` (+156), `config/scenarios.py` (+118), `config/constants.py` (+2), `scripts/run_full_horizon.py` (+41) | **capx D67** — `resolve_published_reliability_requirement_mw` + the `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO` table + the CLI flag | **INERT** | one gated mechanism, `capacity_adequacy_requirement_published_by_iso`, dataclass default `None`. First statement of the resolver is `if year is None or not resolve_capacity_adequacy_requirement_published(config, iso): return None`, and `gross_adequacy_requirement_mw` falls straight through to the unchanged ladder on `None`. **Measured on the control's own resolved config: the field is `None`.** |
| `data/fleet/campd_bins.py` (+33), `data/fleet/assembly.py` (+4), `data/offer_curves.py` (+4) | **nyiso-198** — `cc_duct_peaking_pct(row_scoped)` | **INERT — algebraically, not merely by gate** | with `row_scoped=False`, `src = grp`, so `gap = float(grp["np"].sum()) − float(grp["ns"].sum())`, and `np_sum` two lines above is `float(grp["np"].sum())`: the same two sums, in the same order, i.e. IEEE-identical to the prior `np_sum − ns_sum`, not just equal in exact arithmetic. Both call sites pass `bool(getattr(config, "cc_duct_peaking_row_scoped", False))`; **measured on the control: `False`.** |
| `data/eia860.py` (+48), `data/disk_memo.py` (+249, new), `data/egrid_sheets.py` (+27) | **wallclock A-4** — a cross-process JSON memo for `_egrid_boundary_hr_repairs` | **INERT** | the memoized function is pure in its two source files' bytes and the memo is content-addressed by sha256 over exactly those bytes, so a hit and a miss return the same mapping. This container holds **no prior memo**, so this leg takes the compute path — the identical `_egrid_boundary_hr_repairs_compute` the pre-hunk tree called — and merely writes one afterwards. (A *stale* memo would be a live channel; that hazard cannot arise on a first run.) |
| `policy/carbon.py` (+27) | **y21** — restores the `or 0.0` row-path guard on `price_adder` | **INERT, and one-directional** | `float(x or 0.0)` differs from `float(x)` only at `x is None`, where the prior form **raised**. It can convert an exception into a value; it cannot silently move a number on a path that previously worked. Unreachable here regardless: **measured on the control, `mass_cap_enabled=False` and `carbon_price_path='zero'`.** |
| `pipeline/backcast_config.py` (+11) | D67's kwarg | **INERT** | not on the forecast path |
| `scripts/run_calibration_full.py` (+15) | D67's backcast CLI flag | **INERT** | not imported by `run_full_horizon` (measured) |
| `scripts/lib/load_forecast/*` (4 files, +59) | SCN-LOAD curation registry | **INERT** | offline curation for `curate_load_forecast.py`; **measured: no `load_forecast` module is in `run_full_horizon`'s import closure**, and `constants.py` carries the derived numbers as literals |

**Every hunk in the extra span is INERT too**, so the full `14f860fb..HEAD` window is clean and
the arm's committed I12 is comparable to a control solved at HEAD. The point stands anyway: the
window a G-DRIFT audit is run over has to be the one that actually separates the two numbers
being differenced, and a charter-supplied window is a starting point, not the answer.

### E.2 A defect found while building the control: `--set` could not express it

**`--set FIELD=false` on an ISO-armed flag was silently ignored.**
`run_full_horizon.apply_set_overrides` used a bare `dataclasses.replace`, which re-invokes
`__init__` with every field and so destroys the explicitly-set-field record;
`explicitly_set_fields` then returns `None`, and `iso_configs.apply_iso_scenario_defaults` —
which runs LATER, inside `runner.run_scenario_iso` — falls back to its pre-OVERRIDE-FIX value
comparison. An explicit `False` equals the ScenarioConfig field default, reads as "unset", and
the ISO default re-arms it. This is exactly the condition the OVERRIDE-FIX of 2026-08-13 was
written to end ("a control arm for any ISO-armed flag was inexpressible"), reopened through the
`--set` seam.

**Measured at HEAD, before the repair:** a PJM leg passing all three of that ISO's
`default_scenario_overrides` OFF resolved to cache key **`09996eca71ee80fd`** — the ARM's own
key, with all three gates back ON. **After the repair** (`config.with_overrides(**overrides)`,
the documented supported copy path, which unions the named fields into the record) the same leg
resolves to **`167e65187f32056b`** with the three gates OFF.

**Blast radius: EMPTY.** Of the 14 committed `run_config.json` files carrying a non-empty
`set_overrides`, **none** names a field any ISO arms — every one sets `demand_growth_path`,
`datacenter_load_path`, `carbon_price_path` or `carbon_price_delta`, and none of those four
appears in any of the six ISOs' `default_scenario_overrides`. No committed run was silently
re-armed; the defect was latent and this control is the first thing to ask the question.

Repair + guard: one line in `apply_set_overrides` (plus the docstring recording the trap) and
`tests/scoring/test_set_override_beats_iso_default.py` — 6 assertions, of which **4 fail on the
pre-repair tree and all 6 pass on the post-repair tree** (a test that passed both ways would be
worth nothing). The repair is a strict narrowing: an *unset* field still takes its ISO default,
and one gate turned off does not disarm the other two, both asserted.

### E.3 The control, pre-declared

**Recipe** — the D45-R posture on today's demand table, isolating the Q44 gates and nothing else:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
PYTHONPATH=. uv run python scripts/run_full_horizon.py --iso PJM \
    --start-year 2026 --end-year 2030 --golden-posture \
    --set pjm_demand_response_supply=false \
    --set pjm_accreditation_design_vintage=false \
    --set capacity_market_supply_clearing_by_iso=null \
    --out-dir results/ff-t1f-d60r4-control/pjm
```

`ccs_retrofit_capex_co2_scaling` is left at its **dataclass default (`True`)** — the same value
the arm carries — so Q42 is common to both sides and cancels. **Field-by-field, the control
differs from the committed arm's resolved config in exactly the three Q44 gate fields and
nothing else.**

**CACHE KEY, PRE-DECLARED: `167e65187f32056b`.** Resolved through the harness path
(`reference_config` → `apply_set_overrides` → `apply_iso_scenario_defaults` → `cache_key()`)
before the solve, as Addendum A did. The realized bundle directory is the match to check.

**PRE-DECLARED READING (the director's).** The arm's I12 reads **LESS negative** than this
control's in every year 2027–2030 — because the arm's accredited-firm rise
(+9,092 / +10,276 / +14,303 / +18,000 MW) exceeds the gate-owned ratio leg
(+6,415 / +6,817 / +7,150 / +7,514 MW) in every year, and the peak leg is now held common.

**FALSIFIER.** Any year in which the same-HEAD control's I12 is **less negative** than the
arm's. Then, and only then, does *"D48 is not position-neutral forward"* stand — it goes in the
PR title and the director serves the owner card on those rows. Reported at full magnitude either
way.

**STATUS.** Throwaway diagnostic under rule 29: registered NOWHERE, and its bundle is **deleted
before the PR merges** (rule 29(c)). Every number this session will ever cite from it lives in
E.4 below. Expected ~36 min / ~8.8 GB, wrapped in the mandatory `exit 90` HEAD guard.

### E.4 The control's result

*(Written after the solve; empty at pre-declaration time.)*
