# PRECOMMIT — capx D76-ARM: arming `capacity_screen_peak_measured_hindcast` (owner ruling Q57)

**Lane:** capx D76-ARM (director r#54, capx ledger §0ay.3(a), executing **owner ruling Q57**).
Branch `claude/d76-arm-capacity-peak-oxltrr`, fresh off `origin/main` `59155c2c`.
**MODEL:** Opus. **DATA PROFILE:** `code` (no solve is contemplated; see §7).
Binding: `FINDING-capx-d76-2026-09-06.md` (+ `-p2-`, `-p3-`, whose §7 is the card the owner ruled
on), `PRECOMMIT-capx-d76-measured-screen-peak-2026-09-06.md`, and the **D50/Q42 landing as the ROUTE
precedent** (CLAUDE.md, Capacity Evolution, step 2).

**This document is pushed BEFORE any cache key is computed.** It carries the lane's own zero-LP
prediction so the prediction cannot be revised to fit the measurement — the discipline
`FINDING-capx-d76-p3` §12 records for its own PJM leg.

---

## 0. The act, and the STOP that governs it

**The act.** Flip `ScenarioConfig.capacity_screen_peak_measured_hindcast` from `False` to `True`,
landed the **D50 (b′-1)** way: the field's frozen entry in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` stays
`"False"`, and the flip is declared by APPENDING one line to
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`. Nothing else about the mechanism moves — it was built,
tested and registered whole by D76 phase 1; this lane changes a default and nothing else.

**The STOP, verbatim from the ledger** (§0ay.4, D76-ARM row): *"do not COMMIT the flip until zero key
moves is verified; if it cannot be, STOP and return to the owner"*, and §0ay.3(a): *"the route is the
ruling, so a route that does not hold voids the authority rather than being worked around."*

**So the whole lane turns on one measured number**, and this document declares what that number will
be before it is taken.

---

## 1. What (b′-1) does to a key, stated as arithmetic

Since owner ruling Q20 (capx D24), `ScenarioConfig.cache_key()` drops a registered field iff its
value equals the **FROZEN DECLARATION** in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` — not the live
default. `cache_key()` hashes `asdict(self)`, so **every live config always carries the field**; the
drop is what makes an unarmed run hash as though the field did not exist.

The declaration for this field is `"False"` and (b′-1) forbids editing it. Therefore, after the flip:

| a config whose resolved value is… | equals the frozen `False`? | in the hash? | key |
|---|---|---|---|
| `False` (explicit, or coerced) | yes | dropped | **unmoved** |
| `True` (the new default) | no | **enters** | **moves** |

**That is not a defect of the route; it IS the route.** (b′-1) exists precisely so a post-flip
default config cannot be served the pre-flip bundle — D50's own ledger comment says it in terms:
*"a post-flip default config no longer equals the drop value: it ENTERS the hash and takes its own
key."* D44 measured it (`cedadc285f8603b9 → 4c6b03ae098b6e3e`), D60 measured it
(`4c6b03ae098b6e3e → e5ecd4105ada3e58`, bare backcast `8211c72bb1960adc → 6a2845e50951394e`), and
both **recorded moved keys as the intended effect**.

**The consequence, declared here:** a landing in which *no* key moves anywhere is a landing in which
the post-flip armed run re-uses the pre-flip unarmed bundle — the exact same-key collision (b′-1)
was written to prevent. **A literal repository-wide zero is therefore not merely unmeasured, it is
unreachable while the gate is armed at all.** What is reachable, and what the two immediate
precedents (D75-R-ARM, D78-ARM) actually measured and reported, is **zero OFF-TARGET moves**: every
config the mechanism cannot reach keeps its key, and the configs it governs re-key and are listed.

This lane will measure both and will not choose between the two readings on its own authority.

---

## 2. THE PREDICTION — zero LP, written before any key is computed

### 2.1 The one fact opened before this document was written, disclosed

Before drafting, this lane ran a **field-PRESENCE census** over the 173 committed
`run_config.json` payloads at `59155c2c` — a `grep`-class fact about file contents, **not** a key
computation:

| `mode` | `hindcast` | carries `capacity_screen_peak_measured_hindcast` | configs |
|---|---|---|---:|
| backcast | False | no | 11 |
| backcast | False | **yes** (`false`) | 7 |
| forecast | False | no | 83 |
| forecast | False | **yes** (`false`) | 38 |
| **forecast** | **True** | **no** | **34** |

**All 45 explicit values are `false`; not one committed payload carries `true`; and not one of the
34 hindcast payloads carries the field at all** (every committed hindcast bundle predates D76
phase 1). Nothing else was opened. The prediction below follows from this table plus §1's
arithmetic, with no key computed.

### 2.2 Predicted key moves — **the charter's expectation is ZERO; this lane predicts it will NOT be met**

**Variant A — the flip alone (nothing else changed).** Every config lacking the field resolves the
new default `True`, enters the hash, and moves. Every config carrying an explicit `false` equals the
frozen declaration, is dropped, and does not.

| bucket | configs | **predicted moves** | on target? |
|---|---:|---:|---|
| hindcast (forecast-mode, `hindcast=true`) | 34 | **34** | **yes** — the mechanism's own scope; a move here is correct |
| forecast, not hindcast, field absent | 83 | **83** | **no** — behaviour byte-identical, a pure cache miss |
| backcast, field absent | 11 | **11** | **no** — behaviour byte-identical; **this orphans backcast keeper caches** |
| forecast/backcast carrying explicit `false` | 45 | **0** | — |
| **TOTAL** | **173** | **128** | **94 of them OFF TARGET** |

**Variant B — the flip plus the coercion every sibling gate already ships.** `capacity_no_default_cap_convention_by_iso`,
`capacity_market_supply_clearing_by_iso`, `capacity_going_forward_bar_published_by_iso`,
`capacity_adequacy_requirement_published_by_iso` and `retirement_sector_gate` are each *"coerced to
[the frozen default] in a plain backcast"* in `__post_init__`; D78-ARM's own re-key table records the
result as *"PJM plain backcast … **unmoved**, field coerced `False`"*. This field ships **without**
such a coercion, because at a `False` default it never needed one (its docstring says so in terms:
*"a plain bool whose False default needs no backcast coercion"*). Coercing it to the frozen `False`
whenever `not config.hindcast` — the one predicate under which the gate is inert for the **whole**
run rather than year-by-year:

| bucket | configs | **predicted moves** | on target? |
|---|---:|---:|---|
| hindcast | 34 | **34** | **yes** |
| everything else (forecast non-hindcast + backcast) | 139 | **0** | — |
| **TOTAL** | **173** | **34** | **0 off target** |

**Both variants are predicted NON-ZERO on the literal reading.** Variant B is predicted to reproduce
the D75-R-ARM / D78-ARM pattern exactly (zero backcast moves, zero out-of-scope moves, in-scope moves
listed rather than counted). **This lane does not treat variant B as a way to satisfy the STOP** —
it is a second measurement offered to the owner alongside the first, per §6.

### 2.3 The recipe keys that will be quoted

Predicted to move (the flip's own signature), both variants: the bare hindcast recipe key of every ISO that has one. Predicted **unmoved** under variant B and **moved** under variant A: the bare
backcast key `547053bdfccd4264` (measured at `59155c2c` as this document was drafted — the single
key value opened, and it is the pre-flip literal, not a result).

---

## 3. Instrument and method

`scripts/probes/capxd76arm_default_flip_key_census.py` — new, zero-LP, modelled on
`capxd78arm_iso_override_no_op_check.py` and sharing its `_key` construction so both lanes hash a
payload the same way:

1. Enumerate every committed `run_config.json` (`git ls-files`).
2. Take its `scenario_config` payload verbatim.
3. **Validate the instrument first**: for every payload that records its own `cache_key`, the
   payload hashed under the live drop rules must reproduce that recorded literal. A payload that does
   not reproduce is reported and excluded from the move counts rather than silently averaged in.
4. `key_pre` = the payload with the field at the value the **pre-flip** path resolves (its explicit
   value if recorded, else `False`).
5. `key_post` = the payload with the field at the value the **post-flip** path resolves — `--variant a`
   (its explicit value else `True`) or `--variant b` (as `a`, but forced to `False` when the payload
   is not `hindcast`).
6. Report the full partition, and **list** every moved config rather than counting it.

`--simulate-flip` produces the ex-ante record with `scenarios.py` untouched, exactly as D78-ARM's
probe did; the same probe re-run after an edit (flag omitted) must reproduce it.

Cross-checks run alongside, as the charter names: `scripts/check_cache_key_registration.py`
(checks 3 and 4 — the flip must be declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` or check 3
fails, and the frozen entry must be untouched or check 4 fails) and
`scripts/solve_surface_register.py --diff origin/main HEAD`.

---

## 4. The inert set, pre-declared and asserted BY TEST (not by statement)

The gate's predicate is `config.hindcast and not config.is_crossover_forward_year(year)` — the
identical branch the LP itself takes. Pre-declared inert, to be asserted by test rather than argued:

1. **Every backcast run**, every year — `hindcast` is False.
2. **Every pure forecast run**, every year — `hindcast` is False.
3. **Every crossover FORWARD year** of a hindcast run — `is_crossover_forward_year` is True.
4. **Every forecast year of any run**, by construction: a forecast year has no measured load, so the
   growth path remains THE forecast methodology and rule 13 `[R-MEASURED]`'s forward test is met by
   construction, not by assertion.

Recorded expectation: the seam peak in each of (1)–(3) is **bit-identical** with the gate on and off.

---

## 5. Decision movement, pre-declared from the graded record (reported, never gated)

From `FINDING-capx-d76-p3` §7, restated so this lane cannot re-open it: decisions move in **2 of the 6 ISOs D76 measured**
(SPP postdates the card and was not in its scope) — **CAISO** (−2,532.391 MW of backstop gas CT it does not need) and **MISO**
(343.312 MW of coal saved from a 2024 exit, outside the scored window). Four ISOs show **no decision
change**: **PJM** (D67 makes the requirement peak-independent), **NYISO** (D52 likewise), **ERCOT**
(energy-only — nothing reads the position), **NEISO** (fleet long by 5.0–7.6 GW).

**This is not an argument for or against the arm in either direction** (rule 1 `[R-STRUCT]`, and the
owner's own §0ay.3(a) reasoning): the basis is rule 14 `[R-ACCURATE]` — the de-grown estimate is
wrong by −23.3 % to +15.4 % against the *identical array the LP dispatches*, and rule 14's
misalignment exception does not apply because it is the same array. **The four inert ISOs are
evidence the gate is well-behaved, not evidence it is unneeded.** No number in this section is a
gate, and none may be quoted as one.

---

## 6. STOP gates — declared before the measurement, and this lane's standing answer to each

| # | STOP | this lane's act if it fires |
|---|---|---|
| 1 | **Non-zero key moves** | **DO NOT COMMIT THE FLIP.** Report the exact partition and every moved config to the owner. `scenarios.py` is not touched, the matrix is not stamped, CLAUDE.md is not amended — every one of those is part of the arming act. |
| 2 | Any forecast / crossover-forward / backcast row proving **NOT inert** | STOP — the construction is wrong, not the default. |
| 3 | Any **determination** flipping anywhere | STOP and report — the card's basis was "no determination flips anywhere". |
| 4 | A consumer of the seam that `FINDING-capx-d76` §4.2 does not enumerate | STOP and route — rule 19 `[R-ONE-MECH]` requires the enumeration to be complete before the seam moves. |

**STOP 1 is predicted to fire** (§2.2). This lane declares now, before the number exists, that it
will **not** reinterpret "zero" to mean "zero off-target", will **not** land variant B on its own
authority, and will **not** arm only where the mechanism bites — that last being the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids and which the owner already marked NOT
RECOMMENDED. The measurement is delivered; the reading is the owner's.

---

## 7. What this lane will NOT do

- **No solve.** The verification is zero-LP by construction; `DATA PROFILE: code` is sufficient and
  the lane will not widen. Frontier hindcast bundles are re-solved "on their natural cadence"
  (§0ay.3(a)), which is a different lane's act in a different session.
- **No arm-where-it-bites.** The gate arms everywhere or not at all.
- **No residual argument.** Rule 14 is the basis; how much the answer moves settles nothing.
- **No matrix stamp and no CLAUDE.md bullet unless the flip lands.** Rule 28 `[R-MECH-MATRIX]`'s
  duty (c) was discharged by D76 phase 1, which added the base row and all shard cells with the
  field; duty (b)'s verdict stamp belongs to the act that adjudicates the cell, and a STOP is not an
  adjudication.
