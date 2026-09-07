# FINDING — capx D76-ARM: **the (b′-1) route cannot land at zero key moves, and the STOP fires.** Nothing is armed.

**Lane:** capx D76-ARM (director r#54, capx ledger §0ay.3(a)), executing **owner ruling Q57**.
Branch `claude/d76-arm-capacity-peak-oxltrr`, fresh off `origin/main` `59155c2c`.
Pre-registered in `PRECOMMIT-capx-d76-arm-2026-09-07.md`, **pushed before any cache key was
computed**. Instruments: `scripts/probes/capxd76arm_default_flip_key_census.py` +
`docs/handoffs/d76arm/key-census-variant-{a,b}.json`. **ZERO LP. `src/market_sim/` is untouched.**

---

## 0. Verdict in one paragraph

**The flip's key-move count is not zero, it cannot be made zero while the gate is armed at all, and
the lane therefore STOPS and returns the card to the owner exactly as Q57 instructs.** Measured over
all 173 committed `run_config.json` payloads: **the flip alone moves 128 keys (94 of them off
target)**; the flip plus the non-hindcast coercion every sibling gate already ships moves **34 (0 off
target)**. The reason is not a defect in this lane's execution and not a property of this field — it
is the (b′-1) mechanism itself. `cache_key()` drops a registered field **iff it equals its FROZEN
declaration**, and that declaration stays `"False"`; so a post-flip config resolving the new default
`True` necessarily **enters** the hash and takes a new key. **A landing in which no key moves anywhere
is precisely a landing in which the post-flip armed run is served the pre-flip unarmed bundle** — the
same-key collision option (b′-1) exists to prevent (D24 §4.1/§4.2), and the collision both prior flips
(D44 `cedadc285f8603b9 → 4c6b03ae098b6e3e`; D60 `4c6b03ae098b6e3e → e5ecd4105ada3e58`) recorded as
their intended effect. This lane predicted **128 / 94** and **34 / 0** in a document pushed before the
first key was computed, and the census reproduced both to the config. **Nothing is armed:
`scenarios.py` is untouched, no matrix cell is stamped, CLAUDE.md is not amended.**

---

## 1. The act that was NOT taken, and why

Q57: *"Land it as a declared default flip with the frozen cache-key drop value left at the old default
(the D50/Q42 pattern), so existing bundles keep their keys … **The arming lane must verify zero key
moves before committing; if it cannot, it stops and returns to the owner** — the route is part of the
ruling, so a route that does not hold voids the authority rather than being worked around."*

The verification was performed and **failed**. Under the ruling's own terms that ends the lane's
authority to arm, so the flip was not committed. What follows is the measurement, at full magnitude,
plus the two readings of "zero key moves" the number admits — **served to the owner, not chosen
here**.

---

## 2. The arithmetic — why zero is unreachable, stated before the numbers

`ScenarioConfig.cache_key()` hashes `asdict(self)`, so **a live config always carries every field**.
Since owner ruling Q20 (capx D24, option (b′-1)) a registered field is dropped from that hash iff it
equals its **frozen** entry in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` — for this field, `"False"`, and
(b′-1) makes that entry append-only and un-editable (guard check 4).

| a config whose resolved value is… | equals the frozen `False`? | in the hash? | key |
|---|---|---|---|
| `False` — explicit, or coerced | yes | dropped | **unmoved** |
| `True` — the new default | **no** | **enters** | **moves** |

So the set of configs that keep their keys after the flip is exactly the set that **resolve the OLD
value**, and the set that arms is exactly the set that moves. **"Arm the gate" and "move no key" are
the same sentence with opposite signs.** The route's real guarantee — the one D50's own ledger
comment states — is narrower and it does hold here: *"an EXPLICIT `False` still collapses onto the
pre-flip key and keeps its bundle."* Every one of the 45 committed payloads carrying an explicit
`false` is measured unmoved in both variants, and `--no-capacity-screen-peak-measured-hindcast`
(`run_capacity_hindcast.py:1848`) reaches that posture from the CLI.

---

## 3. THE MEASUREMENT

### 3.1 Instrument validation, first and on the record

The probe hashes each committed `scenario_config` payload under the live drop rules — the
construction `capxd78arm_iso_override_no_op_check._key` uses, so the two lanes' censuses are
comparable — and **validates itself against the payloads' own recorded `cache_key`** before counting
anything:

| | configs |
|---|---:|
| reproduce their recorded key exactly | **133** |
| carry no recorded key to check against | 25 |
| **do NOT reproduce — excluded from the validated counts** | **15** |
| total | **173** |

The split is clean and it is diagnostic: **all 133 reproducing payloads have ZERO "unregistered
missing" fields** — every current `ScenarioConfig` field they lack is a registered optional one,
dropped at default and therefore invisible to the hash either way. The 15 that fail carry two
**retired** fields explicitly (`caiso_bidir_intertie`, `renewable_buildout_pace`) and lack 53–55
current fields; a single-field search reconciles **6 of the 15** by un-dropping
`caiso_offer_surface_measured_ungrounded`, i.e. a field **registered after those bundles were
solved**, so their recorded keys are not reproducible under today's rules at all. **This is a
pre-existing registration-lag artifact, orthogonal to D76, and it is ROUTED, not repaired here** (§6).

**It does not touch the census conclusion**, and the reason is structural rather than convenient:
under (b′-1) a row moves **iff** its resolved value stops equalling the frozen drop value, which is a
property of whether the payload records the field — **not of the hash**. The probe therefore reports
both populations and the FINDING quotes both.

### 3.2 Variant A — the flip alone

`capxd76arm_default_flip_key_census.py --variant a` (`docs/handoffs/d76arm/key-census-variant-a.json`):

| bucket | configs (validated) | moved | configs (all) | moved (all) | on target? |
|---|---:|---:|---:|---:|---|
| `backcast` / not hindcast | 18 | **11** | 18 | **11** | **NO** — behaviour byte-identical |
| `forecast` / not hindcast | 107 | **69** | 121 | **83** | **NO** — behaviour byte-identical |
| `forecast` / **hindcast** | 33 | **33** | 34 | **34** | yes — the mechanism's own scope |
| **TOTAL** | **158** | **113** | **173** | **128** | **94 OFF TARGET** |

**Eleven backcast configs re-key for a run in which the gate is inert on its own predicate.** That is
the outcome D78-ARM's probe names in terms as *"the variant that orphans all six backcast keepers and
was never licensed"*.

### 3.3 Variant B — the flip plus the coercion every sibling gate already ships

`capacity_no_default_cap_convention_by_iso`, `capacity_market_supply_clearing_by_iso`,
`capacity_going_forward_bar_published_by_iso`, `capacity_adequacy_requirement_published_by_iso` and
`retirement_sector_gate` are each coerced back to their frozen default in `__post_init__` outside
their own lane; D78-ARM's re-key table records the result as *"PJM plain backcast … **unmoved**, field
coerced `False`"*. This field ships **without** such a coercion because at a `False` default it never
needed one (its own docstring: *"a plain bool whose False default needs no backcast coercion"* — true
pre-flip, false after). Coercing it to the frozen `False` whenever `not config.hindcast` — the one
predicate under which the gate is inert for the **whole** run rather than year by year:

| bucket | configs (all) | moved (all) | on target? |
|---|---:|---:|---|
| `backcast` / not hindcast | 18 | **0** | — |
| `forecast` / not hindcast | 121 | **0** | — |
| `forecast` / **hindcast** | 34 | **34** | yes |
| **TOTAL** | **173** | **34** | **0 OFF TARGET** |

### 3.4 The shipped recipe keys, both variants

| recipe | pre-flip | variant A | variant B |
|---|---|---|---|
| `ercot-t1h-bare` | `46d013cbf1f35d27` | **`f238df2e5b1ef838`** | **`f238df2e5b1ef838`** |
| `caiso-t1h-bare` | `8f1c3766703a90c4` | **`28f4f62b90e2f74b`** | **`28f4f62b90e2f74b`** |
| `miso-t1h-bare` | `1f92943f84f42fd0` | **`71156d9eb2ea896d`** | **`71156d9eb2ea896d`** |
| `pjm-t1h-bare` | `fb16fda2ddb0a94a` | **`f736025631d0d27e`** | **`f736025631d0d27e`** |
| `nyiso-t1h-bare` | `ee6a3e764324f28f` | **`ee0d44e7d6f26397`** | **`ee0d44e7d6f26397`** |
| `neiso-t1h-bare` | `5b292e24dd752ea4` | **`806f31b59b10c911`** | **`806f31b59b10c911`** |
| `spp-t1h-bare` | `7d1c3f080475310e` | **`8acea51fd756a867`** | **`8acea51fd756a867`** |
| `ercot`/`caiso`/`miso`/`pjm`/`nyiso`/`neiso`/`spp` **plain backcast** | `406cb30ad62bc27b` · `efebcc735768c122` · `b10d58628ba3a057` · `3a566deac3a85682` · `cadaba3d344e84b9` · `27e80d27acd995de` · `989da50bbf0f99d8` | **all seven MOVE** | **all seven unmoved** |

**The `pjm-t1h-bare` pre-flip literal is `fb16fda2ddb0a94a`** — the post-Q56 vintage, i.e. D78-ARM is
on `main` at `59155c2c`. Per r#54's collision map this lane **names the key it read** and registers
nothing.

### 3.5 The field's own shipped test suite already asserts the property the flip breaks

`tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py` — **9 passed, 14 subtests, green
at `59155c2c`** (2 m 59 s) — contains, in `TestCacheKeyRegistration`:

* `test_explicit_off_keeps_the_bare_key_and_armed_moves_it`: asserts `bare == explicit-off` and
  `armed != bare` in all six ISOs. **After the flip the bare key IS the armed key**, so the first
  assertion is false by construction — in **both** variants.
* `test_backcast_key_is_untouched`: asserts a resolved backcast config's key does not move when the
  field is explicitly set `False`. Under **variant A that assertion is false too** — the resolved
  base now carries `True` (in the hash) while the explicit-`False` copy is dropped, so the two
  diverge. **Only variant B preserves the property the test's own docstring claims** — *"a backcast
  runs no capacity evolution; its key must not move."*

That the mechanism's own test file encodes the invariant the flip violates is not a reason against
the arm — it is the STOP being visible in a second, independent place.

---

## 4. The two readings, served rather than chosen

**Reading 1 — literal.** "Zero key moves" means zero, repository-wide. **Unreachable while arming**
(§2); the only configuration satisfying it is the same-key collision (b′-1) forbids. On this reading
Q57's route does not hold and the authority is void, which is what this FINDING reports.

**Reading 2 — the precedent's own standard.** "Existing bundles keep their keys" means every config
the mechanism **cannot reach** keeps its key, and the configs it governs re-key and are **listed**.
This is verbatim how the two immediate arms reported themselves — D78-ARM: *"zero non-PJM moves, zero
backcast moves … PJM forecast moves and is listed, because a moved key is the intended effect and must
be inspectable"*; D75-R-ARM: *"21 of 153 configs move, ALL PJM FORECAST, 132 byte-identical"*. On this
reading **variant A still FAILS** (94 off-target moves, 11 of them backcast) and **variant B PASSES
exactly** (34 in-scope moves, 0 off-target) — but variant B is **not the flip alone**: it adds a
`__post_init__` coercion, which is a construction change this lane has no authority to land under a
ruling whose route it must not reinterpret.

**This lane makes no recommendation between them, and takes neither.** Rule 29 `[R-SCREEN]`'s
doctrine — a screen may kill an arm and may never promote one — applies with more force to a route
question than to a mechanism: choosing the reading that makes the STOP pass is the same act, one layer
up, as choosing the multiplier that makes a criterion pass.

---

## 5. What the arm would still buy, restated so the STOP is not read as a verdict on the mechanism

**Nothing in §§2–4 is an argument about whether the gate should be armed.** Q57's basis is
rule 14 `[R-ACCURATE]` and it is untouched by any of this: the de-grown estimate is wrong by
**−23.3 % to +15.4 %** against the *identical array the LP dispatches*, and rule 14's misalignment
exception does not apply because it is the same array. Zero scalar fields, zero free parameters
(rules 21/24). Rule 13's forward test is met by construction and **the inert set was re-verified by
test at this HEAD, not asserted**: `TestSeamPeakInertWhereThereIsNoMeasuredLoad` shows a forecast run
and a crossover **forward** year byte-identical armed and unarmed, and a backcast never enters the
branch at all (`config.hindcast` is False) — the same predicate the LP itself takes. Decisions move in
2 of the 6 ISOs D76 measured (**CAISO** −2,532.391 MW of backstop gas CT it does not need; **MISO**
343.312 MW of coal saved from a 2024 exit, outside the scored window) and four ISOs are inert for
three structural reasons — **which is evidence the gate is well-behaved, not evidence it is
unneeded**, and is a point for neither side (rule 1 `[R-STRUCT]`).

**The blast radius, measured rather than enumerated.** The 34 hindcast configs whose keys move — the
bundles that would owe a re-solve on their natural cadence — are, by ISO: **PJM 10, MISO 9, NEISO 6,
NYISO 5, ERCOT 3, CAISO 1** (full list in `key-census-variant-b.json`, `moved_detail`; the
per-ISO frontier among them is that ISO's own lane's call, not this one's). **SPP has no committed
hindcast bundle** and so owes nothing, though its bare recipe key moves like every other.

---

## 6. Routed, not repaired

1. **Fifteen committed `run_config.json` records carry a `cache_key` the current rules cannot
   reproduce** (§3.1) — 14 forecast bundles plus the `tests/golden/ercot_2026_2040` fixture. Six are
   explained by `caiso_offer_surface_measured_ungrounded` having been registered **after** they were
   solved; the remaining nine need a second such field and were not chased, being outside this lane.
   The general defect is **registration lag**: registering a field drops it from the hash, which
   silently orphans the key of any bundle solved while it was still hashed. CLAUDE.md's own
   "registered IN THE SAME COMMIT as the field (the nyiso-119 discipline)" is the rule that prevents
   it; these predate its consistent application. Worth a guard, in whichever lane next owns
   `check_cache_key_registration.py`.
2. **`scripts/run_capacity_hindcast.py --help` still crashes** with `ValueError: unsupported format
   character ','` — an unescaped `%` in an argparse help string, first reported at
   `FINDING-capx-d76-p3` §8.2 and still open at `59155c2c`. One line, outside this lane.

---

## 7. What this lane did NOT do, listed so a successor does not have to check

* **`src/market_sim/` is untouched** — no default flipped, no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`
  entry appended, no coercion added, no cache-epoch entry.
* **No matrix stamp** (rule 28 `[R-MECH-MATRIX]`). Duty (c) — the base row plus a cell line in every
  ISO shard — was discharged by D76 phase 1 in the PR that added the field; duty (b)'s verdict stamp
  belongs to the act that adjudicates the cell, and a STOP is not an adjudication. The `fc` letter
  stays **`O`** in all shards.
* **No CLAUDE.md bullet.** The Capacity Evolution section's bullet is part of the arming act.
* **No solve, no registration, no dashboard byte.** `DATA PROFILE: code` was sufficient throughout.
* **No arm-where-it-bites.** Offered to the owner at r#54 and marked NOT RECOMMENDED as
  fitted-mechanism selection; not revisited here.

---

## 8. Reproduction

```bash
uv sync
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant a --expect-live-default false --out docs/handoffs/d76arm/key-census-variant-a.json
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant b --expect-live-default false --out docs/handoffs/d76arm/key-census-variant-b.json
.venv/bin/python scripts/check_cache_key_registration.py --base origin/main   # ok, 273 declared defaults match
.venv/bin/python scripts/solve_surface_register.py --diff origin/main HEAD    # 0 values moved
.venv/bin/python -m pytest tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py
```

Both probe runs exit **2** — the STOP the ruling names — after printing `FAIL: the instrument does not
reproduce 15 recorded key(s)`, which returns 1 first; the counts are printed in full either way and
the JSON records both populations.

---

## 9. THE CARD BACK TO THE OWNER

> **Q57 execution HALTED at its own STOP. `capacity_screen_peak_measured_hindcast` is NOT armed.**
>
> **What was verified.** The flip's key-move count, over all 173 committed run configs, pre-registered
> before measurement and reproduced to the config: **the flip alone — 128 moved, 94 of them in configs
> the gate cannot reach (11 backcast, 83 non-hindcast forecast); the flip plus the non-hindcast
> coercion the five sibling gates already ship — 34 moved, all in the hindcast configs the gate
> governs, 0 off target.**
>
> **Why zero is not reachable.** (b′-1) drops a registered field iff it equals its frozen declaration.
> Arming moves the resolved value off that declaration, so the armed configs enter the hash **by
> design** — that is the mechanism that stops a post-flip run being served the pre-flip bundle. A
> repository-wide zero and an armed gate are mutually exclusive.
>
> **The three ways forward, none taken here.**
> **(i)** Read "zero key moves" as the two immediate precedents report their own arms — zero
> **off-target** moves, in-scope moves listed — and authorize **variant B** (the flip plus the
> non-hindcast coercion): 0 backcast moves, 0 non-hindcast forecast moves, 34 hindcast bundles owed a
> re-solve on their natural cadence, matching Q57's own "frontier bundles re-solved on their natural
> cadence rather than a repository-wide sweep".
> **(ii)** Authorize **variant A** as-is and accept 94 off-target cache misses, 11 of them on backcast
> keeper configs whose behaviour is byte-identical.
> **(iii)** Withdraw or re-route the arm.
>
> **What is NOT in question.** The mechanism's correctness basis (rule 14) is untouched, the inert set
> is re-verified by test at this HEAD, and no determination moves in any variant. This is a **route**
> question, not a correctness one, which is why the lane returns it rather than resolving it.
