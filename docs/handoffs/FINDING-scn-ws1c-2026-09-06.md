# FINDING — SCN-WS1c: the D-1 federal-carbon FLOOR (owner ruling S2), executed

**Lane:** SCN-WS1c (desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#5 am.1,
§2 ruling S2, §5), plan §7 "WS-1a" **item 1** — the one item SCN-WS1a's card gate withheld,
released by the ruling. Model Fable. Branch `claude/scn-ws1c-carbon-floor-tmlmjl` (the harness
assigned this stem in place of the ledger's nominal `claude/scn-ws1c-carbon-floor-v2rk`).
Branched off `origin/main` at `fca3b656`.

**DATA PROFILE: neiso — not hydrated, because this lane spends no LP.** The change is a
resolver; its evidence is arithmetic over committed trajectories plus a cache-key census.
Rule 29 `[R-SCREEN]` clause (0) is satisfied with nothing left over, so no screen bundle exists
and clause (c) DELETE-BEFORE-MERGE has nothing to reach.

**PRECOMMIT:** `docs/handoffs/PRECOMMIT-scn-ws1c-2026-09-06.md`, pushed at `2c1f34dc` **before
any code change**, carrying the three edits, the predicted trajectory, the cache-key list and
the STOP gate.

---

## 0. Bottom line

**The floor is in, and all three pre-registered STOP gates pass on the nose.**

| gate | result |
|---|---|
| **G1** direction + magnitude | **PASS** — 450/450 (ISO × bundle × year) cells equal SCN-WS1a's committed `floor` prediction, to the cent |
| **G2** footprint | **PASS** — exactly 75 cells move (3 series × 25 yr: CAISO/NYISO/NEISO × `tight`); 375/450 bit-unchanged; **every delta strictly positive**, +$15.98 to +$102.29/tCO2 — no cell anywhere falls |
| **G3** byte identity | **PASS** — 0 cache keys moved, default `e5ecd4105ada3e58` stable, **0 of 90** committed `run_config.json` files on the changed branch, backcast 2023–25 trajectories identical in all six ISOs |

Tests: `tests/unit/policy/` **311 passed**, and the **full `tests/unit` suite is at exact parity
with clean `HEAD`** — 244 failed / 4319 passed against a 244 failed / 4276 passed baseline, the
same 244 failures test-for-test (all pre-existing, from the unhydrated `data/raw` tree), +43
passing from this lane's new tests. Blast radius, measured rather than asserted: **exactly two
assertions in the repository asserted the old REPLACE semantics**, and both are flipped — the
one the charter names (`test_cap_and_trade.py:135`) and a **second copy the charter did not
know about**, `tests/unit/model/test_capacity.py::TestStateCarbonProgram::
test_caiso_forward_years_use_projected_program_price` (§3.1).

**`policy_bundle="tight"` is now an exact NO-OP on CAISO, NYISO and NEISO.** It stops being a
cut; it does not become an increase. That is the ruled outcome (§2), stated here plainly because
it was on the record when S2 was made. **This lane does not reach for a construction that makes
`tight` "do something" on those three ISOs — that is sub-box D-1(b), open and the owner's; and
it does not answer D-1(c) either** (§5).

---

## 1. What changed

Three edits, in one direction: `resolve_carbon_program` becomes the answer to exactly one
question — *what does the program itself charge* — and the composition of the two exogenous
carbon channels happens at exactly one place, one level up (rule 19 `[R-ONE-MECH]`).

**(a) `policy/cap_and_trade.py::resolve_carbon_program`, forecast branch.** The nulling is
deleted:

```python
# BEFORE — replace semantics
if getattr(config, "carbon_price_path", "zero") not in ("zero", None):
    price = None                       # a named federal path SUPPRESSED the state program
else:
    ... projected_price(...) ...

# AFTER — the program price, unconditionally, exactly as the backcast branch already did
named_path = getattr(config, "carbon_program_price_path", None)
price = (named_program_price(...) if named_path is not None
         else projected_price(program, config.iso, year))
```

**(b) `policy/carbon.py::resolved_base_trajectory_price` — the one composition point.** It
returned the program adder when truthy and only otherwise consulted the path (an early return
that made the two channels mutually exclusive). It now returns the max:

```python
program = float(resolution.price_adder) if resolution is not None else 0.0
return max(program, rff_path_price(config.carbon_price_path, year))
```

The path interpolation is extracted to a public `rff_path_price(path_name, year)` — same
arithmetic, same `0.0` fallback for an unregistered name — so the floor and the new guard read
**one** implementation of the path (rule 19). `_base_carbon_price`'s stage-(1) `carbon_price`
replace and `resolve_carbon_price`'s final `carbon_price_delta` stage are untouched.

*Why "the path alone elsewhere" needs no branch:* a non-program ISO's adder is `0.0` and no
registered RFF path is ever negative (`zero` 0/0/0/0 … `high` 0/30/70/110), so `max(0.0, path)`
**is** the path. One expression covers both halves of the ruling.

**(c) The D34 guard, extended to the path branch** — `carbon_path_below_program_warning` in
`policy/carbon.py`, wired into `ScenarioConfig.__post_init__` beside the Q26 guard, gated on a
non-default path so a default construction pays one string comparison.

The Q26 guard watches `carbon_price` and *could not see* a cut delivered through
`carbon_price_path` — which is exactly how G-C1 went unobserved for as long as it did. Under the
floor the new guard **can never fire**: `max(program, path) ≥ program` by construction. That is
its design, and it is what WS-1a §6.4 specified ("the guard becomes an assertion of the
invariant rather than a warning"). It is a **regression tripwire**, not an expected condition —
the day an edit reintroduces a replace path or a consumer recomposes the channels itself, it
speaks. It is deliberately a warning and not an `assert`, so `python -O` cannot silence it and a
deliberate below-program study stays runnable: the same observe-only posture Q26 fixed for the
scalar guard.

It does **not** warn that `tight` resolves to the program trajectory rather than the mid path.
That is the ruled S2 outcome, not a defect, and warning on it would put a message on every
program-ISO `tight` run.

**Also:** `config/scenario_resolvers.py`'s `tight` / `rollback` bundle definitions re-read
against the repaired semantics — **no field value changes**; what changed is what `"mid"` means
downstream, and the comment now carries that, the measured no-op, and a "do not redefine this
leg to answer D-1(b)" note. `results/cache.py` gains one epoch entry (§4).

---

## 2. The resolved trajectory under the repaired semantics

Resolved $/tCO2 through the live chain a solve uses (`resolve_policy_bundle` →
`apply_iso_scenario_defaults` → `resolve_carbon_price`). **Bold = moved by this repair.**

| ISO | bundle | path | 2026 | 2027 | 2028 | 2030 | 2035 | 2040 | 2045 | 2050 |
|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | current | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| ERCOT | tight | mid | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| ERCOT | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| CAISO | current | zero | 30.02 | 32.13 | 34.37 | 39.36 | 55.20 | 77.42 | 108.58 | 152.29 |
| CAISO | **tight** | mid | **30.02** | **32.13** | **34.37** | **39.36** | **55.20** | **77.42** | **108.58** | **152.29** |
| CAISO | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| PJM | current | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| PJM | tight | mid | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| PJM | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MISO | current | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| MISO | tight | mid | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 |
| MISO | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| NYISO | current | zero | 23.64 | 25.29 | 27.06 | 30.98 | 43.45 | 60.95 | 85.48 | 119.89 |
| NYISO | **tight** | mid | **23.64** | **25.29** | **27.06** | **30.98** | **43.45** | **60.95** | **85.48** | **119.89** |
| NYISO | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| NEISO | current | zero | 26.05 | 27.88 | 29.83 | 34.15 | 47.90 | 67.18 | 94.23 | 132.16 |
| NEISO | **tight** | mid | **26.05** | **27.88** | **29.83** | **34.15** | **47.90** | **67.18** | **94.23** | **132.16** |
| NEISO | rollback | zero | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

**Read the three bold rows against their own `current` row: they are the same numbers.**

The correction's magnitude is the cut it removes, relative to HEAD before the repair, over all
25 horizon years:

| ISO | smallest correction | largest correction | years corrected |
|---|---|---|---|
| CAISO | +$24.36 (2030) | +$102.29 (2050) | 25 / 25 |
| NYISO | +$15.98 (2030) | +$69.89 (2050) | 25 / 25 |
| NEISO | +$19.15 (2030) | +$82.16 (2050) | 25 / 25 |

**Sign law rather than a table:** `max(a, b) ≥ a`, so no config's resolved carbon can decrease
in any ISO in any year. The repair is monotone by construction, and G2 measured it — all 75
moving cells positive.

**G1's form is worth naming.** The prediction was not written by this lane. SCN-WS1a's
`docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json` already carried a `floor`
column computed as `max(path, program)`, committed to `main` **before this branch existed and
before the ruling was made**. G1 asked whether the live resolver reproduces that column, cell by
cell: **450/450**. The prediction could not have been fitted to the result.

### 2.1 `tight` is now an exact no-op on the three program ISOs — the ruled outcome, stated plainly

The RFF **mid** path never once exceeds a program trajectory in any horizon year, so on CAISO,
NYISO and NEISO the state program is the binding instrument in every year and `tight` resolves
to exactly what `current` resolves to. Its carbon leg bites only on ERCOT / PJM / MISO. (Its
IRA leg, +5 yr, is unaffected and still bites in every ISO — `tight` is not inert, its *carbon*
leg is.)

This is not a defect discovered after the fact. Ruling S2 was made **with this consequence on
the record** — WS-1a measured it and put it in the memo the owner ruled on. It is the honest
reading of a federal price that a state program already exceeds. **This lane does not reach for
a construction that makes `tight` "do something" on those three ISOs.** Whether it should mean
something else there — e.g. an increment via `carbon_price_delta` so it bites everywhere — is
**open owner card D-1(b)**, and the `_POLICY_BUNDLES` comment now says so in place, so a later
lane does not quietly redefine the leg to close it.

The floor is *not* "the program always wins": it is a `max`, and where the federal path does
exceed the program trajectory the path binds. RFF **high** crosses mid-horizon on the two RGGI
ISOs and never on CAISO, and a test asserts the identity `resolved == max(path, program)` rather
than a hard-coded crossing window.

---

## 3. The test-assertion change, and why it is legitimate

The charter asked for "the NEISO-tight **strict-increase** test over 2026–2050". **That test as
written would fail, and it would be right to fail.** Under the floor `tight` equals `current` on
NEISO in every year, so the increase is weak (`≥`), not strict.

What `TestFederalCarbonFloor` asserts instead — what the repaired semantics actually claim:

* `tight ≥ current` in **every** horizon year on **every** ISO — the monotonicity law of `max`,
  which is what "strict increase" was reaching for and is the property that matters (naming a
  federal path can never lower anyone's carbon price);
* **equality** on CAISO / NYISO / NEISO in all 25 years — the ruled no-op, pinned so it cannot
  drift silently;
* a **strict** increase on ERCOT / PJM / MISO from 2027 on, where the path applies alone (2026
  is excluded because the RFF mid knot at 2026 is $0 — the path's own shape, not the floor's
  doing);
* plus `rollback` unchanged, backcast untouched at any path, `carbon_price` keeping Q26 replace,
  `carbon_price_delta` still riding on top of the floored base, and the `high`-path crossing
  identity.

**A test rewritten to match a result is normally the thing to refuse.** The reason this one is
legitimate is that **the ruling moved the predicate before any code ran**. The charter sentence
was written while D-1 was open; S2 was then recorded *with* its measured consequence ("the RFF
mid path never exceeds a program trajectory in any year, so the floor makes `tight` an exact
no-op"). The assertion follows the ruling, not the output — and the ordering is checkable in the
record: the prediction is in WS-1a's committed JSON (2026-09-05), the ruling in ledger §2
(2026-09-06), and this lane's PRECOMMIT declared the changed assertion in its §5 **before** the
code was written. The test class docstring carries the same explanation, so a reader of the test
alone is not left to wonder.

The tripwire test is what stops this from being self-serving: it monkeypatches the pre-S2
replace semantics back into the resolver and requires the guard to fire, reproducing the G-C1
defect message verbatim — *"resolved $50.00/tCO2 vs program $132.16/tCO2 (a $82.16/tCO2 CUT)"*,
matching WS-1a's independently-measured NEISO 2050 cut of −$82.16. Without it, "silent
everywhere" would also pass on a guard that is simply broken.

### 3.1 A second copy of the old assertion, found by the full-suite parity check

The charter names one test to flip. A full `tests/unit` run against a clean-`HEAD` baseline
surfaced a **second** assertion of the same REPLACE predicate, in a file the charter does not
list: `tests/unit/model/test_capacity.py::TestStateCarbonProgram::
test_caiso_forward_years_use_projected_program_price`, whose second half read

```python
# An explicit RFF exogenous path still wins over the program projection.
config = ScenarioConfig(iso="CAISO", carbon_price_path="mid")
self.assertAlmostEqual(resolve_carbon_price(config, 2030), 15.0)   # CARB is $39.36/t
```

That is the G-C1 defect asserted as intended behaviour, and it is the same charter item ("update
the test to the floor") applied to a copy the charter did not know existed. It is flipped to
`max(program, path)` = the CARB projection, with the same rationale comment and a cross-reference
to `TestFederalCarbonFloor`; the test's **first** half (the EM-6 zero-path assertion) is
untouched and still passes.

**Disclosed because the file is outside the charter's FILES-YOU-OWN list.** The edit is two
assertion lines inside a test class whose subject *is* this lane's resolver, and leaving it
would have left the branch red on a test that asserts a deleted branch. Flagged here for
SCN-DESK; nothing else in the diff depends on it.

**This is also why the full-suite parity check was worth running.** The policy-suite result
alone (311 passed) would have looked complete and shipped a red branch.

---

## 4. Byte identity — measured, by name

**No cache key moves, and the reason is structural:** no `ScenarioConfig` field is added,
removed, re-defaulted or re-registered, and `cache_key()` is a pure function of those fields.
Measured before → after: **0 of 24** probed keys moved (six ISOs × three bundles × the backcast
keeper posture), and the pinned default `e5ecd4105ada3e58` is unmoved.

**Census over every tracked `run_config.json` in the repository** (90 files,
`git ls-files '*run_config.json'`):

| posture | count |
|---|---|
| `mode=forecast`, path `"zero"`, bundle `current`, `state_carbon_pricing=True` | 73 |
| `mode=backcast`, path `"zero"`, bundle `current`, `state_carbon_pricing=True` | 17 |
| **carrying a non-`"zero"` `carbon_price_path`** | **0** |

**Zero of ninety committed bundles reach the changed branch.** It is entered only when
`mode != "backcast"` **and** `carbon_price_path not in ("zero", None)` **and** the ISO has a
program **and** `state_carbon_pricing` is on; no committed config satisfies the second conjunct.

The **66 keys recorded** in committed `run_config.json` files, asserted unchanged **by name**
(24 further bundles record no `cache_key` field — the six backcast keeper bundles among them;
for those the claim is the same structural one, that no key-bearing field changed):

`706eec14f63096e8` `f129fd3720e3e874` (scn-ws1a T0 base / carbon_plus25) · `8d8bc63a0d4378a9`
`cc7d1050a8090c76` `321f04e9060787f0` (ff-t1f-d45r miso / nyiso / pjm) · `772b1e5abc7fc80c`
`873d8c0e6cab52ae` `6690e4d6d66bc819` (ff-t1f-d46 caiso / ercot / neiso) · `0c3e9cd5b5993bdf`
`18515067bf4d2fbe` `167e65187f32056b` (ff-t1f-d50 ercot / neiso / pjm) · `b1a73a087064ffd8`
`19a9690bb12c8459` (ff-t1f-d60 miso / nyiso) · `8ebed20ae90ec0e7` (ff-t1f-d65-a1/neiso) ·
`18515067bf4d2fbe` (ff-t1f-d65-ctl/neiso) · `587dc5b32ba71ceb` (ff-t1f-s123/verify) ·
`9a7f68fc7dcac931` (ff-t1f-s4hydro/neiso + control) · `31a19d815fa319a7` (ff-t1f-s6-pjm/ledger) ·
`67678e58b2d0526c` `56019f3b0850e9f9` `e84079053b581a9e` `96984c538320d6d6` (ff-t3-neiso-golden
bau-d46 + its fc6 arms) · `0365174ab16cc318` `7924eccc695c0168` `7784d408fc955785`
`1de43201e2040f7f` `13f9357712250600` `a4b11ef4aaa1be35` (bau-prera-2026-08-31 + arms) ·
`706e7ba8e6582d42` `f7cced798488ddac` `2d017ed9675aa386` `65662ca117959ee5` (bau + arms) ·
`2c8cc7d19ccaed4c` (hindcast caiso t1h-d46) · `67d5dcc1ada2e2df` `f061b2646bfaac8b` (ercot
t1h-d46 / d4m) · `501b5f64b8adf8d4` `3649264ca98a1fb4` `40173304213d39cd` `eff2c890746ec966`
`6ea92547eaa62559` `c306ddc6d28c60c2` `1b0f1a5e75719b92` (miso t1h-d27 / d31 / d33 / d46 /
d53×2 / d33-probe) · `313ba0612435b963` `d6c0137e37bf3200` `da19b85495178949` `07e416f3f8072e7c`
(neiso t1h-d37-armed / d45r / d46 + both crossovers) · `cad77112c804881d` `91686abe7a744a88`
`911371a8cf23d5c3` `7323dc2ddabc95c7` (nyiso t1h-d45r-curveon / d45r / d52-devintage +
crossover) · `ea767a6254b8e4af` `896da48960560a29` `c6091bd5b62bbc3f` `f0e050e820c1159a` (pjm
t1h-d45 / d45r-fixed / d45r / d57-clearing) · `c3592c1adbc8ac17` `277e96c45549a70e` (scn-ws2a
NEISO T0 ref / target) · `eed460b6ddfaab1c` `c3592c1adbc8ac17` (scn-ws0-smoke neiso CARB / REF) ·
`d88c8585e76f2935` `075e6aa30813f061` `383509581661faba` (scn-ws2-ladder ercot BAU / CES-20 /
CES-40) · `0d6f2710f8dedf56` (tests/golden ercot_2026_2040).

**The six keeper bundles, by name**, all `mode=backcast` / path `"zero"`: CAISO
`caiso251_arm_nomargin`, ERCOT `ercot248_two_config_keeper`, MISO `miso217_intermphys_B`,
NEISO `neiso99_joint_B`, NYISO `nyiso192_astoria_panel`, PJM `pjm_debugb_inputclock_A`.

**Backcast is untouched on a second, independent ground**, not merely because every keeper
carries path `"zero"`: the changed branch is the `else` arm of `if config.mode == "backcast"`,
so even a hypothetical backcast config with a non-`"zero"` path never entered it and still does
not. G3 measured the 2023–25 resolved trajectories identical in all six ISOs, and a test pins it.

**Cache-epoch entry** (`results/cache.py`, top of the ledger): "Epoch 2026-09-06 — SCN-WS1c /
owner ruling S2: the federal carbon FLOOR". Same-key, **invalidated set EMPTY at this commit**.
It is recorded anyway, because the ledger's job is to make a same-key semantic change visible
even when — especially when — nothing is currently stale: the next non-`"zero"`-path bundle
solved on either side of this commit is not comparable to one solved on the other.

---

## 5. What this lane deliberately did NOT do

**D-1(b) — what `tight` should mean on a program ISO now that it is a no-op there — is OPEN and
the owner's.** Not answered, not pre-empted. The `_POLICY_BUNDLES` comment names the card so the
next lane to touch that leg sees it.

**D-1(c) — how a federal floor composes with PJM's partial RGGI footprint — is OPEN and the
owner's, and this repair is inert on that seam by construction.** `carbon_mc_column` is the only
per-generator membership seam; it is gated on `program.zone_share is not None`, which is PJM
alone, and it reads `resolution.price_adder`. PJM's forecast `price_adder` is
`projected_price(...)` over a `STATE_CARBON_PRICE_BY_ISO` with no PJM key
(`['CAISO','NYISO','NEISO']`), i.e. `0.0` before and after this change — so the seam returns the
scalar, **the identical object**, exactly as it did pre-floor. A test pins that, named for the
card. WS-1a already built the membership-weighted column that makes D-1(c) answerable; the
answer is not built here.

`policy/constraints.py` reads only `resolution.cap_spec`, and the mass-cap row path returns
before the adder branch — untouched, and no mass-cap run's behaviour changes.

**No default moves beyond the ruled semantics.** No `ScenarioConfig` field is added, removed or
re-defaulted; no bundle's field values change; no flag flips.

**No file outside the lane's declared regions was touched** apart from the two matrix base rows
disclosed in §6.

### 5.1 ROUTED TO SCN-DESK — a rule-28(c) breach on `main`, not this lane's

`scripts/check_mechanism_matrix.py` **fails on pristine `origin/main`** at `bc77b189`
(reproduced by checking out `origin/main` clean and running the checker):

> `::error … absent-shared ratchet: shared field capacity_going_forward_bar_published_by_iso is
> in neither the mechanism matrix … nor the mechanism-matrix-gaps.json absent_shared ratchet
> (rule 28c). Add its row (plus a cell line in each mechanism-matrix/<ISO>.js shard), or name it
> in the owning family row's def/note.`

That field is the **capacity-expansion track's** (it landed with the capx D60-R3 merge), it is
outside this lane's file regions, and rule 28(d) makes the cell the owning lane's to write —
so SCN-WS1c does **not** fix it. It is reported here because it will turn the
`mechanism-matrix-guard` CI job red on **every** open PR until that lane discharges the duty,
including this one, and a reader of a red gate on this PR should not spend time looking in this
diff for the cause. **This lane's own matrix state is clean:** with that one pre-existing error
set aside, the checker reports integrity OK, keeper stamps matching, both ratchets OK, and all
seven matrix files pass `node --check`.

---

## 6. Records

**Code:** `src/market_sim/policy/cap_and_trade.py` (forecast branch + docstring),
`src/market_sim/policy/carbon.py` (the floor, `rff_path_price`,
`carbon_path_below_program_warning`, three docstrings),
`src/market_sim/config/scenarios.py` (the guard wired into `__post_init__`, D34 guard region
only), `src/market_sim/config/scenario_resolvers.py` (bundle comments; no value change),
`src/market_sim/results/cache.py` (one epoch entry).

**Tests:** `tests/unit/policy/test_cap_and_trade.py` (`:135` flipped +
`TestFederalCarbonFloor`, 10 cases), `tests/unit/policy/test_carbon_price_below_base_guard.py`
(`TestPathBranchInvariantGuard` + `TestFloorResolverOutputIsByteUnchanged`),
`tests/unit/model/test_capacity.py` (the second copy of the old assertion, §3.1).
`tests/unit/policy/` **311 passed**; full `tests/unit` at exact parity with clean `HEAD`
(244 failures, the same ones test-for-test; +43 passing).

**Instruments (zero LP, committed):** `docs/handoffs/scn-ws1c/verify-floor-2026-09-06.py` (runs
identically before and after; `--tag before|after` → the two JSON snapshots),
`verify-floor-{before,after}.json`, `score-gates-2026-09-06.py` + `.txt` (the G1/G2/G3 scorer
and its output). The prediction they are scored against is SCN-WS1a's committed
`docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json`, not re-derived here.

**Docs:** plan `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §5.1 Carbon rows 1
and 4, plus a **STATUS** stamp on §7's WS-1a prompt (item 1 executed here; it read "gated on
D-1", which is now stale); desk ledger §3 Carbon rows 1 and 4.

**Matrix** — the last commit, after `git fetch origin main` + rebase: the **existing**
`carbon_price_path` and `policy_bundle` cells re-stamped in all six shards. The base rows are
**not re-minted** — same `id` / `cat` / `name` / `mode`, row count unchanged, and
`scripts/check_mechanism_matrix.py` exits 0.

**One disclosure on scope.** The charter's FILES-YOU-OWN names the two mechanisms' *cells*. This
lane also corrected those two **base rows'** `def` and `note` strings in
`docs/codebase-site/data/mechanism-matrix.js`, because they described the code path this commit
deletes — verbatim, `"an explicit non-'zero' path SUPPRESSES the projected state-program adder
… REPLACE semantics, the G-C1 defect"` — and a mechanism definition that documents a deleted
branch actively misleads the next lane (CLAUDE.md: when docs and code disagree, fix the docs).
The row's own note anticipated it: *"Cells move to the ruled semantics at the item-1 lane."*
The edit is confined to those two rows' prose; no row is added, removed, renamed or re-anchored.
**Flagged here rather than assumed** — if SCN-DESK reads base-row prose as desk-owned, this is
the edit to reassign; nothing else in the diff depends on it.

*Anchor warnings:* `check_mechanism_matrix.py` emits 244 line-number anchor warnings. They are
**pre-existing drift, none of them this lane's** — measured by re-running the checker with this
lane's `scenarios.py` edit reverted: still 244. Every warned row anchors below line 15100 and
this lane's only `scenarios.py` insertion is at ~15783, so no anchor it could shift is warned.

**No LP was spent, so no bundle exists to delete under rule 29(c).**

---

**What this releases: Stage A's carbon cases can now be written path-form rather than
delta-form.** `CARB-LO / -MID / -HI` can be expressed as `carbon_price_path="low"/"mid"/"high"`
— a federal-policy statement that reads as one — instead of the reduced `carbon_price_delta=25`
form SCN-WS1b had to run while D-1 was open, because a named path is no longer a cut on any ISO
and is a floor on every one. The one thing the campaign author must carry with it, and state in
the case comment, is §2.1: on CAISO, NYISO and NEISO the `low` and `mid` rows resolve to the
program trajectory and are therefore identical to `current`, so a program-ISO carbon *response*
still needs the delta instrument or D-1(b)'s answer.
