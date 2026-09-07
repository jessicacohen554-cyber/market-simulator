# PRECOMMIT — capx D76-ARM-B: arming `capacity_screen_peak_measured_hindcast` as **VARIANT B** (owner ruling **Q58**)

**Lane:** capx D76-ARM-B (director r#55 §0az.3(a) / r#56 re-emission, executing **owner ruling Q58**).
Branch `claude/d76-arm-b-capacity-hindcast-ne6yr1`, fresh off `origin/main` `1a3901bc`.
**MODEL:** Opus. **DATA PROFILE:** `code` (no solve is contemplated; §7).
Binding: `FINDING-capx-d76-arm-2026-09-07.md` (**the pre-registration this document reproduces**),
`FINDING-capx-d76-2026-09-06.md` (§4.2 is the rule-19 consumer enumeration), `-p2-`, `-p3-`,
`PRECOMMIT-capx-d76-arm-2026-09-07.md`, and the **D50/Q42 + D60 landing** as the flip-ledger precedent.

**This document is pushed BEFORE any cache key is computed on this branch.** Its numbers are the
lane's prediction, not its measurement; the census that follows either reproduces them or the
divergence is reported rather than patched toward.

---

## 0. The act, exactly, and the authority for each half

**Half 1 — the declared default flip.** `ScenarioConfig.capacity_screen_peak_measured_hindcast`
`False → True`, landed the **D50 (b′-1)** way: the field's frozen entry in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` **stays `"False"`** and is not edited (append-only, guard
check 4); the flip is declared by APPENDING one line to
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`. This is the **fourth** entry in that ledger, after
`fossil_announced_exits_enabled` (D44/Q30), `ccs_retrofit_capex_co2_scaling` (D60/Q42) and
`ccs_retrofit_fixed_cost_co2_scaling` (D65-B/Q47).

**Half 2 — the `__post_init__` non-hindcast coercion.** The field is coerced back to the
**dataclass default** (never a literal) whenever `not self.hindcast` — the one predicate under which
the gate is inert for the WHOLE run rather than year by year, and the LP's own branch predicate with
the year term dropped. **Explicitly authorized by Q58**, verbatim: *"The `__post_init__` coercion is
explicitly authorized by this ruling — that is the one thing D76-ARM correctly refused to land on its
own."*

**Q57's route is VOID and is not being worked around.** Q58 replaces it: *"'Arm the gate' and 'move
no key' are the same sentence with opposite signs … The house standard is **zero OFF-TARGET moves
with in-scope moves listed**."* This lane reports itself in exactly that form and in no other.

**No third variant is invented.** Variant B is the flip + the coercion, as measured by D76-ARM and as
ruled by Q58. Nothing else about the mechanism moves — it was built, tested and registered whole by
D76 phase 1.

---

## 1. The arithmetic, restated so the prediction is derivable rather than asserted

Since Q20 (capx D24, option (b′-1)) `cache_key()` drops a registered field **iff it equals its FROZEN
declaration** — here `"False"` — and `cache_key()` hashes `asdict(self)`, so a live config always
carries the field.

| a config whose resolved value is… | equals the frozen `False`? | in the hash? | key |
|---|---|---|---|
| `False` — explicit, or **coerced by half 2** | yes | dropped | **unmoved** |
| `True` — the new default | no | **enters** | **moves** |

So under variant B the moved set is **exactly** `{payload : hindcast is true AND the payload does not
record an explicit value}`. That is a property of the payload's fields, not of the hash — which is
why the 15 unreproducible-key rows D76-ARM routed to **D85** cannot touch this census (§6).

---

## 2. THE PREDICTION — zero LP, written before any key is computed

### 2.1 The one fact opened before this document was written, disclosed

A **field-PRESENCE census** over the committed `run_config.json` payloads at `1a3901bc` — a
`grep`-class fact about file contents, **not** a key computation, exactly as D76-ARM §2.1 disclosed
for itself:

| `mode` | `hindcast` | records the field | configs | Δ vs D76-ARM (173) |
|---|---|---|---:|---|
| backcast | False | no | 10 | −1 |
| backcast | False | **yes** (`false`) | 10 | +3 |
| forecast | False | no | 83 | 0 |
| forecast | False | **yes** (`false`) | 52 | +14 |
| **forecast** | **True** | **no** | **34** | 0 |
| **forecast** | **True** | **yes** (`false`) | **1** | **+1 — NEW** |
| | | **TOTAL** | **190** | **+17** |

**All 63 explicit values are `false`; not one committed payload carries `true`.**

**THE DENOMINATOR HAS GROWN 173 → 190 and the charter said it would.** The seventeen new payloads
are the r#55 window's registrations. **Exactly one of them is a hindcast payload**, and it is the
first committed hindcast bundle to record the field at all:
`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/run_config.json` (PJM, explicit
`false`) — the D75-R-ARM registration, solved after D76 phase 1 registered the field. **It does not
move**, which is (b′-1)'s stated property working on a real bundle rather than in a table.

### 2.2 Predicted key moves — **variant B**

| bucket | configs | **predicted moves** | on target? |
|---|---:|---:|---|
| forecast / **hindcast**, field absent | 34 | **34** | **yes** — the mechanism's own scope |
| forecast / hindcast, explicit `false` | 1 | **0** | — (b′-1) keeps its bundle |
| forecast / not hindcast | 135 | **0** | — coerced |
| backcast | 20 | **0** | — coerced |
| **TOTAL** | **190** | **34** | **0 OFF TARGET** |

**Predicted per-ISO breakdown of the 34** — the D76-ARM census reproduced **to the config**:

| ISO | PJM | MISO | NEISO | NYISO | ERCOT | CAISO | SPP | total |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **predicted moved** | **10** | **9** | **6** | **5** | **3** | **1** | **0** | **34** |
| D76-ARM (173 configs) | 10 | 9 | 6 | 5 | 3 | 1 | 0 | 34 |

PJM holds **11** committed hindcast bundles now against D76-ARM's 10; the eleventh is the
explicit-`false` `-d75rarm` row above, so PJM's moved count is unchanged at 10 and the whole
breakdown is identical over a denominator 17 larger. **SPP has no committed hindcast bundle** and so
owes nothing, though its bare recipe key moves like every other.

### 2.3 Predicted variant A, recorded only so the ruling's comparison stays live at this HEAD

Not being landed. Every config lacking the field resolves the new default: **127 moved, 93 OFF
TARGET** (10 backcast + 83 non-hindcast forecast), against D76-ARM's 128/94 — the difference is
exactly the one backcast payload that gained an explicit `false` since.

### 2.4 The shipped recipe keys

The seven `*-t1h-bare` recipe keys move (they are hindcast recipes; that IS the intended effect) and
the seven `*-plain-backcast` keys **do not** (coerced). D76-ARM measured the post-flip literals as
identical under variants A and B; this lane will re-read them at ITS HEAD and **name the keys it
reads** rather than restating D76-ARM's — `main` has advanced `59155c2c → 1a3901bc`, so a pre-flip
literal may have moved for reasons that are not this gate's.

---

## 3. STOP GATES (pre-registered, so they cannot be written to fit)

1. **Any OFF-TARGET move at all** — backcast or non-hindcast forecast — **STOP**. Variant B is
   *defined* by having none.
2. **Any forecast, crossover-forward or backcast row proving NOT inert** — **STOP**; the construction
   is wrong. Asserted **by test**, not stated (§4).
3. **Any determination flipping anywhere** — **STOP** and report. Q58's basis is "no determination
   moves in any variant".
4. **A consumer of the seam that `FINDING-capx-d76-2026-09-06.md` §4.2 does not enumerate** —
   **STOP** and route; rule 19 `[R-ONE-MECH]` requires the enumeration complete before the seam
   moves. Re-verified at THIS HEAD, not inherited.

---

## 4. Inertness is ASSERTED BY TEST, and the coercion must not make the assertion vacuous

The shipped `TestSeamPeakInertWhereThereIsNoMeasuredLoad` constructs its armed arm through
`ScenarioConfig(**overrides)`. **After half 2 lands, a `hindcast=False` config can no longer carry
`True` through the constructor** — so the existing forecast byte-identity test would pass
*trivially*, both arms coerced, and would stop being an inertness claim at all. That is a real hazard
this document names before it can be discovered later as a defect.

**The resolution, pre-declared:** the non-hindcast inertness claim is split into the two independent
layers it actually has, and both are asserted:

- **(a) the coercion layer** — a `hindcast=False` config (forecast and backcast alike) resolves the
  field to the dataclass default, in every ISO, so the flag cannot even reach the runner armed;
- **(b) the BRANCH layer** — the flag is set on the resolved config *after* construction (the
  dataclass is not frozen), bypassing the coercion, and the run is still byte-identical to the
  unarmed one. This is the claim that survives even if half 2 were removed, and it is the one that
  proves the *seam* is inert rather than merely unreachable.

The crossover-forward-year test is untouched and stays fully live: a crossover is `hindcast=True`, so
the coercion never sees it, and that test is what discriminates the year-level predicate.

`TestCacheKeyRegistration::test_explicit_off_keeps_the_bare_key_and_armed_moves_it` asserts the
**pre-flip** invariant (`bare == off`, `bare != on`) and is **false by construction after the flip**,
in both variants — D76-ARM §3.5 recorded exactly this. It is updated to the **post-flip** invariant,
which is strictly stronger, not weaker: `bare == on` (the default is armed) **and** `off != bare`
(an explicit `False` still keys distinctly and keeps its pre-flip bundle — the (b′-1) property the
`-d75rarm` payload now exercises for real). `test_backcast_key_is_untouched` is **unchanged and must
still pass**: half 2 is what keeps it true.

---

## 5. What else lands in this PR, and why each is required rather than discretionary

- **Cache-epoch ledger entry** (`src/market_sim/results/cache.py`), dated, as D44/D60/D65-B each did.
- **`tests/regression/test_persisted_identity.py`** pins advanced **only where the flip moves them**,
  each with a dated cause block. A pin that does **not** move is left alone — a moved pin on a
  non-hindcast recipe would be stop gate 1 firing.
- **Matrix (rule 28 `[R-MECH-MATRIX]`)**: duty (c) is already discharged — the base row and a cell in
  all **seven** shards exist (SPP.js is present at `fc: "U"`). This lane owes **duty (b)**: the
  verdict stamp, `fc: "O" → "K"` in the **six measured ISOs**, with the D50 precedent's own
  treatment of SPP — **SPP stays `U`**, never a transferred verdict (rule 25 `[R-ISO-SCOPE]`), with
  its evidence line stating that the flip reaches SPP by default and that no SPP hindcast bundle
  exists to test it.
- **CLAUDE.md**, Capacity Evolution: its own bullet, beside the D50/D57/D67/D75-R/D78 entries.
- **Rule-27 blob verification** for every pushed file ≥300 lines.

---

## 6. Routed, not repaired (restated so a reader does not think it was skipped)

**D85 — the 15 committed run configs carrying a `cache_key` the current rules cannot reproduce.**
D76-ARM established this is registration lag, orthogonal to D76, and that it **cannot touch the
census** because a row's move verdict is a property of whether the payload records the field, not of
the hash (§1). It is reserved as **D85** and is not audited here. If this lane's census trips over
one, it is **named and passed over**.

**`scripts/run_capacity_hindcast.py --help` still crashes** (`ValueError: unsupported format
character ','`) — one line, first reported `FINDING-capx-d76-p3` §8.2, outside this lane.

---

## 7. What this lane will NOT do

- **No solve.** `DATA PROFILE: code`. The arm's *behavioural* case was made by D76 phases 0–3 across
  all six ISOs and is not re-litigated; Q58 is a **route** ruling, and this lane executes the route.
- **No registration, no dashboard byte, no keeper change.** Backcast behaviour is byte-identical, so
  no determination, sidecar or dashboard row can move (stop gate 3 is a check, not an expectation).
- **No arm-where-it-bites.** Offered to the owner at r#54 and refused as fitted-mechanism selection
  (rule 1 `[R-STRUCT]`). The four ISOs in which no decision moves are evidence the gate is
  well-behaved and are **a point for neither side**.
- **No argument from the residual.** The basis is rule 14 `[R-ACCURATE]`: the de-grown estimate is
  wrong by **−23.3 % to +15.4 %** against the *identical array the LP dispatches*, and rule 14's
  misalignment exception does not apply **because it is the same array**.

---

## 8. Reproduction

```bash
uv sync
# ex ante (this document's numbers), scenarios.py untouched:
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant b --expect-live-default false --out docs/handoffs/d76armb/key-census-variant-b-preflip.json
# ex post, after the edit — the SAME arithmetic, now proving it measured the edited tree:
.venv/bin/python scripts/probes/capxd76arm_default_flip_key_census.py \
    --variant b --expect-live-default true --out docs/handoffs/d76armb/key-census-variant-b-postflip.json
.venv/bin/python scripts/check_cache_key_registration.py --base origin/main
.venv/bin/python -m pytest tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py \
    tests/unit/config/test_cache_key_declared_default_drop.py
```

The probe applies the flip **arithmetically** to each payload rather than reading the live default,
so the ex-ante and ex-post records are produced by the same code path and **must agree exactly**;
`--expect-live-default` is what makes the second run prove which tree it read.
