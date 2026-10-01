# FINDING — capx D76-ARM-B: **the measured hindcast capacity-screen peak is ARMED, variant B. Q58 is DISCHARGED.**

**Lane:** capx D76-ARM-B (director r#55 §0az.3(a), re-emitted r#56), executing **owner ruling Q58**.
Branch `claude/d76-arm-b-capacity-hindcast-ne6yr1`, rebased onto `origin/main` `40b54ce7`
(pre-registration was written and pushed off `1a3901bc`, before the first key was computed).
Pre-registered in `PRECOMMIT-capx-d76-arm-b-2026-09-07.md`. Instrument:
`scripts/probes/capxd76arm_default_flip_key_census.py` + `docs/handoffs/d76armb/*.json`.
**ZERO LP. No solve, no registration, no dashboard byte, no determination moved.**

---

## 0. The result, in the form the house standard requires

> **34 moved, 0 OFF TARGET**, over a denominator of **192** committed `run_config.json`.
> In-scope moves, listed by ISO: **PJM 10, MISO 9, NEISO 6, NYISO 5, ERCOT 3, CAISO 1, SPP 0.**
> **0 backcast moves. 0 non-hindcast forecast moves.** All seven `*-plain-backcast` keys unmoved;
> all seven `*-t1h-bare` recipe keys advance, which is the intended effect and is listed below.
> The persisted-identity pins do **not** move.

`capacity_screen_peak_measured_hindcast` is armed as the default posture for every ISO, in the two
halves Q58 authorized. Every stop gate was checked and none fired.

---

## 1. What was landed, and under whose authority each half sits

**Half 1 — the declared default flip.** `False → True` on the shared `ScenarioConfig` default, the
**FOURTH** entry appended to `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, with the field's frozen entry
in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` left at `"False"` and **not edited** (append-only, guard
check 4). This is the D44 / D60 / D65-B (b′-1) route.

**Half 2 — the `__post_init__` non-hindcast coercion**, explicitly authorized by Q58 and the one act
D76-ARM correctly refused to take on its own. The field is coerced back to its **frozen declaration**
whenever `not self.hindcast`.

**One construction decision this lane had to make, stated rather than buried.** The five sibling
gates coerce to the **dataclass default**, "never a literal". Copying that verbatim here would have
been a **no-op**: after half 1 the dataclass default *is* the armed value. What the coercion has to
reproduce is the value at which `cache_key()` **drops** the field, so it resolves
`_CAPACITY_SCREEN_PEAK_FROZEN_DECLARATION` — the frozen ledger entry, evaluated once at import from
its source text. That is the siblings' "never a literal" discipline pointed at the right object, and
it is asserted by test (`test_the_coercion_target_is_the_frozen_declaration`) so the two can never
drift apart. It is resolved directly rather than through `cache_key_drop_defaults()` because that
function constructs a `ScenarioConfig` on its fallback path and would recurse into `__post_init__`.

**No third variant was invented.** Half 1 + half 2 is variant B as D76-ARM measured it and as Q58
ruled it.

---

## 2. THE CENSUS

### 2.1 The prediction, and that it was pushed first

`PRECOMMIT-capx-d76-arm-b-2026-09-07.md` was committed and pushed **before the first cache key was
computed on this branch** (commit `64dc3818`), carrying the per-ISO breakdown, the total, the
off-target count and the variant-A comparison. Every one of them is reproduced below.

### 2.2 Variant B — measured

| bucket | configs | moved | on target? |
|---|---:|---:|---|
| forecast / **hindcast**, field absent | 34 | **34** | **yes** — the mechanism's own scope |
| forecast / hindcast, explicit `false` | 1 | **0** | — (b′-1) keeps its bundle |
| forecast / not hindcast | 123 | **0** | — coerced |
| backcast | 20 | **0** | — coerced |
| **TOTAL** | **192** | **34** | **0 OFF TARGET** |

| ISO | PJM | MISO | NEISO | NYISO | ERCOT | CAISO | SPP | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **measured moved** | 10 | 9 | 6 | 5 | 3 | 1 | 0 | **34** |
| PRECOMMIT §2.2 predicted | 10 | 9 | 6 | 5 | 3 | 1 | 0 | **34** |
| D76-ARM (173 configs) | 10 | 9 | 6 | 5 | 3 | 1 | 0 | **34** |

**The denominator grew and the census did not.** D76-ARM measured 173 committed run configs on
2026-09-07 morning; this lane measured **190** at its pre-registration base `1a3901bc` and **192**
after rebasing onto `40b54ce7`, and the moved set is **the same 34 configs** at all three. The
nineteen payloads added since are eighteen non-hindcast forecast/backcast rows the coercion holds,
plus **one hindcast row** —
`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm`, the D75-R-ARM registration, which
solved **after** D76 phase 1 registered the field and therefore records it explicitly `false`.
**It does not move.** That is (b′-1)'s stated property — *"an explicit `False` still collapses onto
the pre-flip key and keeps its bundle"* — exercised by a real committed bundle rather than asserted
in a table, and it is why PJM holds eleven hindcast bundles but owes ten re-solves.

### 2.3 Variant A, re-measured at this HEAD for the comparison Q58 ruled on

**127 moved, 93 OFF TARGET** (10 backcast, 83 non-hindcast forecast) — PRECOMMIT §2.3 predicted
exactly this. **Half 2 is the difference between 93 off-target cache misses, ten of them on backcast
keeper configs, and zero.**

### 2.4 The instrument, validated before anything was counted

150 of the 192 payloads reproduce their own recorded `cache_key` under the live drop rules, 27 record
no key to check against, and **15 do not reproduce** — the same 15 D76-ARM found and routed, unchanged
by a denominator 19 larger, which is itself evidence that they are a fixed historical
registration-lag set rather than a growing defect. They are **excluded from the validated counts and
reported again at full population**, because a row's move verdict under (b′-1) is a property of
whether its payload records the field, **not of the hash**. Exactly one of the 34 movers is among them
(`results/hindcast/miso-2021-2025-realized-t1h-d27`); per the charter it is **named and passed over**.
**Reserved as D85; not audited here.**

### 2.5 Ex ante and ex post, by the same code path

The probe applies the flip **arithmetically** rather than reading the live default, so the pre-edit
and post-edit records are produced identically and must agree. They do: **all 190 rows byte-identical
between `key-census-variant-b-preflip.json` (`scenarios.py` untouched) and the post-edit run at the
same base**, recipe legs included, with only `live_dataclass_default` moving `False → True` — which
is the field the `--expect-live-default true` assertion proves the second run read the edited tree by.

**One instrument amendment was required and is disclosed.** The probe read the live default off a
*resolved* `ScenarioConfig()`, which is non-hindcast and therefore **coerced** after half 2 — so
`--expect-live-default true` could never pass however the tree was edited. It now reads
`ScenarioConfig.__dataclass_fields__[FIELD].default`. **The census arithmetic
(`_pre_flip_value` / `_post_flip_value` / `_key`) is untouched**, which is why the ex-ante and ex-post
records still agree to the config. The PRECOMMIT §8 command that named the old flag was written before
this interaction was visible; the interaction is a consequence of half 2, not of the measurement.

### 2.6 The shipped recipe keys, read at THIS HEAD rather than restated

| recipe | pre-flip | post-flip |
|---|---|---|
| `ercot-t1h-bare` | `46d013cbf1f35d27` | **`f238df2e5b1ef838`** |
| `caiso-t1h-bare` | `8f1c3766703a90c4` | **`28f4f62b90e2f74b`** |
| `miso-t1h-bare` | `1f92943f84f42fd0` | **`71156d9eb2ea896d`** |
| `pjm-t1h-bare` | `fb16fda2ddb0a94a` | **`f736025631d0d27e`** |
| `nyiso-t1h-bare` | `ee6a3e764324f28f` | **`ee0d44e7d6f26397`** |
| `neiso-t1h-bare` | `5b292e24dd752ea4` | **`806f31b59b10c911`** |
| `spp-t1h-bare` | `7d1c3f080475310e` | **`8acea51fd756a867`** |
| **all seven `*-plain-backcast`** | `406cb30ad62bc27b` · `efebcc735768c122` · `b10d58628ba3a057` · `3a566deac3a85682` · `cadaba3d344e84b9` · `27e80d27acd995de` · `989da50bbf0f99d8` | **all seven UNMOVED** |

The literals were re-read at this HEAD, not carried over from D76-ARM, because `main` advanced
`59155c2c → 1a3901bc → 40b54ce7` in between and two solve-surface modules (`constants.py`,
`fuel_trajectories.py`) changed on the way. They come back identical, so nothing in that window moved
these recipes and the pre-flip column is this lane's own reading.

`--no-capacity-screen-peak-measured-hindcast` reaches the pre-arm posture and keeps its key.

---

## 3. THE STOP GATES — all four checked, none fired

**(1) Any off-target move.** **PASS — zero.** 0 backcast, 0 non-hindcast forecast, at both bases and
in both the validated and the full-population count.

**(2) Any row proving NOT inert.** **PASS, and asserted by test rather than stated.**
`tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py` — **59 passed, 41 subtests** —
now pins inertness at **both layers**, because half 2 created a hazard that would otherwise have made
the shipped assertion vacuous and this lane names it rather than leaving it to be discovered:

* **the coercion layer** (`TestNonHindcastCoercion`, new): on every non-hindcast config of all seven
  ISOs, in both modes, the field resolves to the frozen declaration; an **explicit `True` does not
  survive** a non-hindcast config (the coercion is unconditional, not a default-only fallback); a
  hindcast config keeps **both** values; and the coercion target **is** `cache_key`'s drop value.
* **the branch layer** (`TestSeamPeakInertWhereThereIsNoMeasuredLoad`, preserved): the flag is now set
  on the **resolved** config, bypassing `__post_init__`, so the forecast byte-identity comparison is
  still a claim about the **runner's own branch** — the seam is inert where there is no measured load
  *even if the flag reaches it* — rather than a tautology about a coerced flag. The
  crossover-forward-year test is untouched and fully live (a crossover is `hindcast=True`, so the
  coercion never sees it).

`TestCacheKeyRegistration` is updated from the pre-flip invariant to the post-flip one, which is
**stronger, not weaker**: the bare hindcast recipe now takes the **armed** key (what stops a post-flip
armed run being served the pre-flip bundle) **and** an explicit `False` keys distinctly and keeps its
bundle. `test_backcast_key_is_untouched` is unchanged and still passes — half 2 is what keeps it true —
and a new `test_non_hindcast_forecast_key_is_untouched` pins half 2's own key claim.

**(3) Any determination flipping anywhere.** **PASS — none, and none can.** Backcast behaviour is
byte-identical by construction (the seam branch requires `config.hindcast`; half 2 additionally puts
the flag out of reach), no backcast key moved, and committed artifacts are files rather than cache
lookups. No keeper, sidecar, determination or dashboard row moves. **No run was solved, scored or
registered.**

**(4) A consumer of the seam not enumerated in `FINDING-capx-d76-2026-09-06.md` §4.2.**
**PASS — re-verified at THIS HEAD, not inherited.** Every `peak_demand` read between the seam
assignment and its rebind onto the LP basis maps 1:1 onto §4.2's six sites (line numbers have shifted
with the file; the sites have not): CR-1 `capacity_reserve_position`; the D59 `locality_peak_by_zone`;
`resolve_adequacy_requirement_mw`; `accredited_firm_capacity_mw`; `evolve_fleet(peak_demand_next=…)`;
and the D52 ledger's `screen_peak_demand_mw`. Downstream, `peak_demand_used` in `evolve.py` reaches
exactly §4.2's 5a–5e. **Zero new consumers.** The one other match in the window
(`peak_demand_mw=None` on the bridge-year ledger) is a literal, not the seam.

### 3.1 Six pinned-key tests moved with the arm — repaired, and one pre-existing failure isolated

The wide run (`tests/unit/pipeline/test_capacity_screen…` + `tests/unit/config` +
`tests/regression/test_persisted_identity.py` + `tests/unit/model/test_capacity.py`) first came back
**7 failed / 1210 passed**. The same set was run **at `origin/main` before diagnosing any of them**:
**one fails there too** — `test_capacity.py::TestGetRPSTarget::test_unregistered_iso_is_none`
(`get_rps_target("SPP", 2030)` now returns `0.0`, because SPP acquired a `STATE_RPS_FLOORS` entry).
**Pre-existing, not this lane's, and not repaired here** — it belongs to the SPP lane. The other six
are the arm's, and every repair below is a **re-baseline or a correction of the object read, never a
relaxation of an invariant**:

* **`test_cache_key_default_flip_guard.py` ×2.** Both read the "live default" off a **resolved**
  `ScenarioConfig()` — which is non-hindcast and therefore **coerced by half 2**, so they became
  unsatisfiable for this field *however the ledger was written*. They now read
  `ScenarioConfig.__dataclass_fields__[name].default`, which is the object a flips ledger is about and
  the object the shipped guard already compares (`check_cache_key_registration.py` check 3 resolves
  the dataclass default's **source text**, never an instance — which is why that guard passed while
  these two failed). The invariants are unchanged: a real drift between a declared flip and the live
  default still fails, and a "synced" frozen entry still fails. **This is the same trap the probe hit
  (§2.5); it is a property of adding a coercion to a flipped field, and it is now handled in all three
  places.**
* **`test_d67arm_pjm_requirement.py::TestQ52ArmingKeys` ×3.** These pin the bare T1-H recipe keys,
  which the arm advances by design. `BARE_PJM_ARMED` and the five non-PJM pins are re-measured
  (`fb16fda2ddb0a94a → f736025631d0d27e`; MISO/NYISO/NEISO/CAISO/ERCOT to the §2.6 literals), each
  with a dated cause block noting what the file's own earlier note understated — this is the first arm
  to move these keys **without touching `_pjm_config`**, because a shared default flip that a hindcast
  recipe resolves moves them too. `BARE_PJM_PRE_ARM` is **deliberately NOT re-pinned**: following the
  precedent that file set for Q55, the *invocation* gained the fourth inverse flag and reaches
  `15a723ba3b6dc856` **exactly**. A new test extends that property to the other five ISOs.
* **`test_capacity.py::TestPjmCapacitySupplyClearing::test_pjm_iso_override_arms_forecast_only`.**
  Fourteen pinned PJM legs, all hindcast, all re-keyed. Re-pinned — and the file's "measured, not
  assumed" discipline is applied to **all fourteen** rather than the customary three: adding
  `capacity_screen_peak_measured_hindcast=False` to each leg **restores its pre-arm literal exactly,
  14 of 14**. The bare inverse is now **asserted** rather than only narrated.

**That 14-of-14 result is the arm's strongest single piece of evidence** and it is worth stating on its
own: the entire key movement across every PJM posture — six previously-armed fields, three control
shapes — decomposes onto **this one field**, invertibly. A moved key here is a one-time cache miss,
never a lost bundle.

**Guards, run green:** `check_cache_key_registration.py --base origin/main` — *no new fields; 275
declared defaults all match HEAD* (check 3 accepting the flip through the FLIPS ledger, check 4
confirming the frozen entry unedited); `check_mechanism_matrix.py` — *integrity OK, 7 ISO shards,
keeper stamps match*, with its 253 anchor warnings **measured identical on `origin/main`** and
therefore pre-existing.

---

## 4. Why it arms — and the two things this document deliberately does NOT argue

**The basis is rule 14 `[R-ACCURATE]`, and only that.** In every hindcast year that is not the weather
year, the capacity screens tested a peak `_scale_demand` had de-grown out of the weather year, while
the same year's LP dispatched the measured load: wrong by **−23.3 % to +15.4 %** across the six ISOs.
Rule 14's misalignment exception cannot apply **because it is the same array**. Zero scalar fields,
zero free parameters (rules 21/24). Nothing is transferred between ISOs (rule 25 `[R-ISO-SCOPE]`) —
one shared seam, one repair, no per-ISO number.

**NOT argued from the residual.** That decisions move in only **2 of 6** ISOs — CAISO −2,532.391 MW of
backstop gas CT, MISO 343.312 MW of coal saved from a 2024 exit outside the scored window — is
**a point for neither side**. The four inert ISOs are evidence the gate is **well-behaved**. Arming
only where it bites was offered to the owner at r#54 and refused as fitted-mechanism selection
(rule 1 `[R-STRUCT]`); it was not revisited.

**NOT re-litigated.** Q58 is a **route** ruling. The mechanism's behavioural case was made by D76
phases 0–3 and this lane spent no LP re-making it.

---

## 5. What now owes a re-solve, and to whom

The **34** bundles below carry the **superseded** screen operand under their own pre-flip keys. Under
Q57's own words, kept by Q58, they are re-solved **by their own ISO's lane on its natural cadence**,
never by a repository-wide sweep — the frontier among them is each ISO's call, not this lane's. This
lane re-ran nothing.

**PJM (10)** `capacity-hindcast/pjm-…-t1h-d67arm`; `hindcast/pjm-…-t1h-{d45, d45r, d45r-fixed,
d57-clearing, d62-pubbar, d74-nodefaultcap, d78-sectorgate}`; `run-config-debt/pjm-…-{realized-ffr3a3,
crossover-ffr3a3}`. *(The eleventh PJM hindcast bundle, `…-t1h-d75rarm`, does **not** move.)*
**MISO (9)** `hindcast/miso-…-t1h-{d27, d31, d33, d46, d53-sectorgate, d53-sectorgate-d51ratio}`;
`hindcast/miso-d33-probe-entrydiag`; `run-config-debt/miso-…-{realized-ffr3a3, crossover-ffr3a4}`.
**NEISO (6)** `hindcast/neiso-…-t1h-{d37-armed, d45r, d46}`; `hindcast/neiso-…-crossover-{capxd14,
rcrepair}`; `run-config-debt/neiso-…-realized-ffr3a3`.
**NYISO (5)** `hindcast/nyiso-…-t1h-{d45r, d45r-curveon, d52-devintage}`;
`hindcast/nyiso-…-crossover-capxd10`; `run-config-debt/nyiso-…-realized-ffr3a3`.
**ERCOT (3)** `hindcast/ercot-…-t1h-{d46, d4m}`; `run-config-debt/ercot-…-crossover-ffr3a3`.
**CAISO (1)** `hindcast/caiso-…-t1h-d46`.
**SPP (0)** — SPP has no committed hindcast bundle and owes nothing, though its bare recipe key moves
like every other.

Full detail: `docs/handoffs/d76armb/key-census-variant-b-postflip.json`, `moved_detail`.

---

## 6. Matrix (rule 28 `[R-MECH-MATRIX]`)

Duty **(c)** was already discharged — the base row and a cell in **all seven** shards exist, SPP
included. This lane discharged duty **(b)**, the verdict stamp: `fc: "O" → "K"` in the **six measured
ISOs**, each cell's prior phase-0/1 measurement preserved beneath the new stamp rather than
overwritten.

**SPP stays `U`, deliberately.** The flip reaches SPP — its bare recipe key advances with everyone
else's — but SPP has no committed hindcast bundle, so nothing there was solved, scored or measured,
and rules 25 `[R-ISO-SCOPE]` / 28(d) forbid filling its cell from the six ISOs whose census earned the
card: **a default that reaches an ISO is not a verdict in it.** The precedent is exact —
`ccs_retrofit_capex_co2_scaling`, the same all-ISO (b′-1) flip, reads `K` in six shards and `U` in
SPP's. SPP's cell says so in place.

---

## 7. Also landed

* **Cache-epoch ledger** (`results/cache.py`): the dated **2026-09-07** entry, marked a **KEY
  ADVANCE**, carrying the census, both halves, the moved and unmoved recipe keys, and why the route
  changed.
* **CLAUDE.md**, Capacity Evolution: the mechanism's bullet beside D50 / D57 / D67 / D75-R / D78.
* **Six pinned-key tests repaired** (§3.1) — three files, all re-baselines or corrected reads, with
  every pre-arm literal proved reachable by the explicit-off inverse.
* **`run_capacity_hindcast.py`'s CLI help and the flag's wiring comment**: the gate's `--help` text
  said *"OMIT to inherit the shipped default (off, owner-armed only)"*, which the arm made false. It
  now says the default is armed, that `--capacity-screen-peak-measured-hindcast` is therefore a no-op
  restating it, and that `--no-…` is the meaningful leg reaching the pre-arm posture and keeping its
  key. (The unrelated `--help` crash routed in §8 is untouched and no new `%` was introduced.)
* **Persisted-identity pins**: **deliberately NOT advanced.** Both pinned configs are non-hindcast, so
  half 2 coerces the field, `cache_key()` drops it, and the keys are unmoved — verified field-by-field
  against `origin/main`'s own resolved payload (zero-diff) and green in
  `tests/regression/test_persisted_identity.py`. **A moved pin here would have been stop gate 1
  firing.**

---

## 8. Routed, not repaired

1. **D85** — the 15 committed run configs whose recorded `cache_key` the current rules cannot
   reproduce. Unchanged in count over a 19-larger denominator. Not audited here (§2.4).
2. **The mechanism has no `model-methodology-spec.md` entry.** Neither
   `capacity_screen_peak_measured_hindcast` nor its D67 sibling
   `capacity_adequacy_requirement_published_by_iso` appears in the spec or under `docs/codebase/`;
   the gap predates this lane (D76 phase 1's own PR did not add one, and neither did the D57 / D67 /
   D75-R / D78 arms, which likewise carry only a CLAUDE.md bullet). It matters more now that the gate
   is **default-ON**: the spec's §5 screens describe an operand the code no longer uses in a hindcast.
   **Not repaired here** — a spec edit for one field, in an arming lane, would leave five siblings
   inconsistent; it is one `/sync-docs` pass over the whole capacity-screen family. Named so it is not
   mistaken for an oversight.
3. **`scripts/run_capacity_hindcast.py --help` still crashes** (`ValueError: unsupported format
   character ','`) — one line, first reported `FINDING-capx-d76-p3` §8.2, still open. Outside this
   lane.

---

## 9. Reproduction

```bash
uv sync
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant b --expect-live-default true --out docs/handoffs/d76armb/key-census-variant-b-postflip.json
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant a --out docs/handoffs/d76armb/key-census-variant-a-postflip.json
.venv/bin/python scripts/check_cache_key_registration.py --base origin/main
.venv/bin/python scripts/check_mechanism_matrix.py
.venv/bin/python -m pytest tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py \
    tests/unit/config tests/regression/test_persisted_identity.py tests/unit/model/test_capacity.py
```

The probe still exits non-zero after printing `FAIL: the instrument does not reproduce 15 recorded
key(s)` — the D85 rows — and after the STOP path it inherited from Q57's now-void route, which counted
**any** move as a failure. Both are printed in full and neither changes a count; the numbers this
FINDING quotes are the ones the JSON records.

---

## 10. THE CARD BACK TO THE OWNER

> **Q58 is DISCHARGED. `capacity_screen_peak_measured_hindcast` is ARMED as variant B, for every ISO.**
>
> **34 moved, 0 off target**, over 192 committed run configs — PJM 10, MISO 9, NEISO 6, NYISO 5,
> ERCOT 3, CAISO 1, SPP 0; **0 backcast moves, 0 non-hindcast forecast moves**; every in-scope move
> listed by name. The house standard, met in the house's own form.
>
> **The census was pre-declared before the first key was computed and reproduced to the config** —
> including D76-ARM's per-ISO breakdown unchanged across three different denominators, and the one new
> hindcast bundle that records the field explicitly and therefore does **not** move, which is (b′-1)
> working on a real artifact.
>
> **All four stop gates checked, none fired.** Inertness is asserted **by test at both layers**, and
> this lane split it that way *because* half 2 would otherwise have made the shipped assertion
> vacuous — a hazard named here rather than left to be found later.
>
> **Nothing was solved, scored or registered, and no determination moved.** The 34 hindcast bundles
> carry the superseded operand under their own keys and are re-solved by their own ISO's lane on its
> natural cadence — §5 names all 34.
>
> **The one judgement call, surfaced rather than buried:** the coercion targets the field's **frozen
> declaration**, not the dataclass default the five sibling gates use, because after the flip the
> dataclass default is the *armed* value and copying the siblings verbatim would have been a no-op.
> Asserted by test so the two cannot drift.
