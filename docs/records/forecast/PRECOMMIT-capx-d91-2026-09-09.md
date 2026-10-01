# PRECOMMIT — capx D91: the cache-key registration defect, diagnosed before it is repaired

**Lane:** capx D91 · **Branch:** `claude/capx-d91-cache-key-pins-phrx2p` · **Date:** 2026-09-09
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `code` · **ZERO LP.**
**Authority:** OWNER RULING **Q64** (2026-09-09, capx ledger §0bh.3(a)) — *"Re-emit D91 to diagnose
fully, then repair."*
**Predecessor:** `docs/handoffs/PRECOMMIT-capx-d90-rescore-2026-09-09.md` §3.1 (the attribution).

> **This document is written BEFORE any file is edited.** Everything in §§1–4 is measurement; §5 is
> the repair it authorizes and §6 the cost that repair carries. HEAD is `fc927c2f`.

---

## 0. THE EXACT COMMAND (§0be doctrine: a red inventory is only as wide as the command that made it)

Three instruments, all offline, all in this container:

```
# (i) the standing gate — the PAYLOAD construction
python3 scripts/check_key_provenance.py --no-fetch

# (ii) the DATACLASS construction, over every committed run_config.json
#      for each: ScenarioConfig(**{k:v for k,v in payload.items() if k in LIVE_FIELDS}).cache_key()
#      vs the record's own "cache_key"                     [scratch: census.py]

# (iii) the pinned-literal tests
python3 -m pytest $(grep -rl 547053bdfccd4264 tests/) -q -p no:randomly
```

**A DEPENDENCY NOTE THAT WIDENS D90's DENOMINATOR, AND IT IS NOT A QUIBBLE.** A bare `code`-profile
container has no `numpy`/`pydantic`, and 22 committed payloads carry a carbon program whose
`__post_init__` reaches `policy/cap_and_trade.py` → `config/iso_configs.py` → `pydantic`. Those 22
raise on reconstruction and silently leave the population. **That is exactly how D90's denominator
came to be 173**: 232 committed `run_config.json` − 32 with no recorded key − 22 unreconstructible −
5 outside `results/` = **173**. With `pip install numpy pydantic pyyaml pandas` the same command
reconstructs **200 of 200** records carrying a key, of which **195 are under `results/`**. Every
number below is on the WIDER population, and D90's is quoted beside it wherever they differ.

---

## 1. D90's NUMBERS REPRODUCE AT MY HEAD, AND THE POPULATION IS WIDER

| measurement | D90 (r#63) | **D91 at `fc927c2f`** |
|---|---|---|
| `ScenarioConfig().cache_key()` | `72341e34fd261997` | **`72341e34fd261997`** ✓ |
| `_PINNED_DEFAULT_KEY` | `547053bdfccd4264` | **`547053bdfccd4264`** ✓ |
| committed payloads reproducing (dataclass construction) | 0 / 173 | **0 / 195 `results/`; 1 / 200 all** |
| in-memory registration restores | 0 → 78 / 173 | **fixed 92, newly broken 1** (91/195; 92/200) |
| `bau-d60` | `ae317e63263c8eef` → `f04fd06348e1623d` | not separately re-derived (D90's own target) |
| `bau-d65br` | `4a5f9695eeae815a` → `0fc42cb56c24d544` | **`4a5f9695eeae815a` → `0fc42cb56c24d544`** ✓ |

The one record that reproduces at HEAD as committed is `docs/handoffs/scn-ws5b-neiso/REF/run_config.json`
(`1b452c457ca786a6`) — the only committed payload that CARRIES the field. It is §6's orphan.

The named field and commit stand: **`pjm_seam_neighbour_hourly_ladder`**, added by **`f2a834de`**
(*"Add PJM hourly neighbour-anchored seam ladder + pjm-174 PRECOMMIT"*, 2026-09-08 16:21:53 +0000)
with **no `_CACHE_KEY_OPTIONAL_FIELDS` entry and no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` entry**
(both verified absent at HEAD; 283 fields are registered, this is not one).

---

## 2. QUESTION (1) — THE OTHER 95. **ZERO UNCLASSIFIED, 200 OF 200 DERIVED.**

Not "mostly the one field". Every committed record's recorded literal is **derived** — recomputed
from its own payload under a named recipe — and the derivation is exhaustive: `classify.py` runs a
fixed ladder and a row that no rung reproduces is reported as a finding. **There are none.**

Four causes, all mutually exclusive as labelled, D85's standard met:

| cause | what it is | defect? |
|---|---|---|
| **A** | `pjm_seam_neighbour_hourly_ladder` is absent from the payload (it postdates the solve) and, being unregistered, enters the reconstruction's hash | **YES — this is the defect** |
| **B** | one or more of the four (b′-1) **registered** fields whose LIVE default has been ARMED away from its frozen declaration — `ccs_retrofit_fixed_cost_co2_scaling` (58 rows), `ccs_retrofit_capex_co2_scaling` (47), `capacity_screen_peak_measured_hindcast` (27), `fossil_announced_exits_enabled` (25) — is absent from the payload and materializes at the armed value | **NO — this is owner ruling Q20 / (b′-1) working exactly as designed** |
| **C** | the ISO's D79 solve surface has moved off its declaration, so live `cache_key()` appends a `__solve_surface__` block the bundle never carried. Exactly CAISO (`NUCLEAR_MONTHLY_CF_BY_YEAR`, `STATE_CARBON_PRICE_BY_ISO`) and ERCOT (`NUCLEAR_MONTHLY_CF_BY_YEAR`) | **NO — capx D79's designed re-key** |
| **D** | one of the 15 records already listed in `docs/governance/key-provenance-exceptions.json` (`lag` ×6, `pre-ledger-flip` ×3, `pre-ledger-flip+split-root` ×5, `vintage+resolved` ×1) | **NO — known, cited, recipe-verified** |

**The disposition of all 200:**

| cause profile | rows (all) | rows (`results/`) | action |
|---|---:|---:|---|
| **A** alone | 92 | 91 | **repaired by R1** — the key is RESTORED, not moved |
| **A + B** | 42 | 42 | R1 restores the A half; the B half stays and must |
| **A + C** | 42 | 42 | R1 restores the A half; the C half stays and must |
| **A + B + C** | 8 | 6 | as above |
| **D** | 15 | 14 | none — listed exception |
| reproduces as committed | 1 | 0 | **ORPHANED by R1** (§6) |
| **UNCLASSIFIED** | **0** | **0** | — |

Per ISO (`results/` only): CAISO 19 (all C), ERCOT 29 (all C), MISO 32, NEISO 55, NYISO 27,
PJM 32, SPP 1. C is confined to CAISO+ERCOT and its row count — **50 across all 200** — reconciles
to the character with the standing gate's own *"50 only with the surface AT DECLARATION"*.

**So the answer to "what accounts for the other 95" is: nothing new.** The 95 are not a second
unregistered field waiting to move keys a second time. They are causes **B**, **C** and **D** —
three already-adjudicated, already-designed behaviours — layered *on top of* cause A, which is
present in **199 of 200** records. Registering the field restores every key whose ONLY obstruction
was A; the rest keep keys they are supposed to keep. **The repair cannot produce a second key move,
because there is no second unregistered field.** (Brute force confirms it independently: over the
546 unregistered fields in the default hash payload, **exactly one** single-field drop reproduces the
pin, and it is this one.)

**Two byproducts, reported not repaired.** (i) `tests/golden/ercot_2026_2040.run_config.json` is the
sole record carrying 79 further unregistered-and-absent field names — it is old, and it is already
listed exception `vintage+resolved`; §5 R4 uses that set as a ratchet baseline. (ii) The same record
carries `staged_oversupply_thinning` and `staged_thinning_max_gw_per_year`, two DELETED fields with
no `_CACHE_KEY_RETIRED_FIELDS` entry — a rule-26 `[R-DELETE]` miss of the same family. Neither moves
a key today; both are named here rather than fixed.

---

## 3. QUESTION (2) — WHY THE GATE IS GREEN. **NAMED, AND IT IS NOT ANY OF THE THREE CANDIDATES.**

`scripts/check_key_provenance.py --no-fetch` is **EXIT 0** at `fc927c2f`:

```
232 committed run configs at fc927c2f: 185 reproduce, 32 have no key, 15 mismatch
  15 KNOWN (listed exceptions), 0 UNKNOWN
ok: every mismatch is a known, cited, recipe-verified exception
```

**THE REASON, IN ONE LINE: the census is PAYLOAD-DRIVEN and `cache_key()` is DATACLASS-DRIVEN.**

* `ScenarioConfig.cache_key()` hashes `asdict(self)` — **every live field**, materialized.
* `key_provenance.head_key()` opens with `out = dict(payload)` — **only the fields the record
  actually stored**.

A field added *after* a bundle solved is, by construction, absent from that bundle's payload. It can
therefore **never enter the census's hash**, and can **never make a census row mismatch** — however
unregistered it is. The blind spot is not incidental: it is *exactly* the defect class
`G1_UNKNOWN` was written to catch, and G1 is structurally incapable of seeing it. Measured
corroboration: **1 of 232 committed payloads contains the string `pjm_seam_neighbour_hourly_ladder`**
— the census literally never sees the field.

**The three candidates the charter named, ruled out by reading:**

| candidate | verdict |
|---|---|
| the `key_at_declaration` / `key_live_surface` either-matches rule (D85-R repair 4) insulates it | **NO.** Both legs are payload-driven; `surface=` toggles only the `__solve_surface__` block. It changes nothing about which FIELDS are hashed. |
| the census enumerates a different population than D90's 173 | **NO.** The census enumerates 232 — a strict SUPERSET of D90's 173. A wider population cannot explain a green. |
| the exception list is absorbing them | **NO.** 15 entries, all cause D, all recipe-verified; none names this field. |

**Does the gate need repair — and what would have made it red?** It needs its **scope stated** and
a **sixth gate**, not a weakening. What it must never get is these 199 records appended to the
exception record: that file is for non-reproduction that is UNDERSTOOD AND CITED, and its own
`what_this_is_not` block says so. The gate that would have gone red on 2026-09-08 is §5's **R4**.

**AND THE GUARD THAT DID FIRE WAS MISDIRECTED BY ITS OWN BLAME HELPER — this is the second-order
finding, and it is causal.** `tests/regression/test_persisted_identity.py::_fields_explaining_the_key_move`
exists precisely to name this culprit, and it returned `[]`, so the failure printed *"No SINGLE
field explains the move (several landed at once, or a field's default value changed). Bisect against
the commit that last set the pin"* — a hand-bisect instruction — when in truth **one** field
explained it. The helper drops registered fields at `getattr(ScenarioConfig(), name)`, the **LIVE**
default; since owner ruling Q20 / (b′-1), `cache_key` drops at the **FROZEN declaration**
(`cache_key_drop_defaults()`). For an ARMED field the two differ — `ccs_retrofit_capex_co2_scaling`
is `True` live and `False` frozen — so the helper pops a field `cache_key` KEEPS, its baseline
payload is not the payload being hashed, and no single-field probe can ever reach the pin. The guard
was never silent; it was **loud and wrong about why**.

---

## 4. THE PINNED TESTS, RE-MEASURED (charter: report what I see, not D88's 16)

D88 counted **16 red across fourteen files** at `origin/main` `5e3b6c6a`. At `fc927c2f`, over the
**25 files that reference the literal `547053bdfccd4264`**:

```
39 failed, 915 passed, 25 skipped, 61 subtests passed
```

Wider because the command is wider (25 files, not 14) and because more has landed since. Three
distinct causes are mixed in that 39, and only the first two are mine:

1. **the config pins** (`test_default_scenario_config_cache_key_is_pinned` → `080aed989d20cbda` vs
   `547053bdfccd4264`; `test_backcast_…` → `d2fe33d46d3375ee` vs `f61891696e671969`, and the ~35
   per-arming tests that assert the same literals). These are measured with the surface neutralized
   by the `config_identity_only` fixture, so they are **pure cause A** and **R1 turns them green** —
   verified by construction: dropping the field from the at-declaration payload yields
   `547053bdfccd4264` and `f61891696e671969` **exactly**.
2. **`test_default_cache_key_is_checkout_path_invariant`** — same literal, same cause.
3. **`test_solve_surface_fingerprint_is_pinned[NYISO]`** — `1eefed492204fab7` (209 rows) vs
   `8569b48ab932ed6d` (208 rows). **NOT MINE, NOT CAUSE A**: a registry row was ADDED to NYISO's
   surface. The test's own message prescribes the remedy (advance THAT pin with a dated cause block,
   never re-declare the row). **ROUTED, not repaired** — see §7.

---

## 5. THE REPAIR THIS DOCUMENT AUTHORIZES

**R1 — register the field (the presumptive (b′-1) route, and §2 confirms it is the right one).**
Add `"pjm_seam_neighbour_hourly_ladder"` to `_CACHE_KEY_OPTIONAL_FIELDS` at the END of the PJM
cluster (HOUSE-3 insertion convention) and `"pjm_seam_neighbour_hourly_ladder": "False"` to
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit (membership parity is guarded). The field's
default is **not touched**: it stays `False`, and an armed run still keys distinctly.

**R2 — repair the blame helper** (`_fields_explaining_the_key_move`): drop registered fields at
`cache_key_drop_defaults()`, the frozen declaration, instead of the live default. This is the
instrument that should have named the field on 2026-09-08. It is diagnostic-only code on an
already-failing pin; it moves no key.

**R3 — advance no pin literal.** R1 restores every config pin to the literal already committed. The
one pin that stays red (`[NYISO]` surface fingerprint) is another lane's and is routed, not re-pinned
by me: a pin advanced without its cause named is an answer key.

**R4 — close the census's blind spot without weakening it.** Add a **sixth gate**,
`G6_UNREGISTERED_SCHEMA_DRIFT`, to `check_key_provenance.py` / `key_provenance.check_exceptions`:
for every committed record, compute `S = LIVE_FIELDS − payload_keys` (the fields that did not exist
when the run solved) restricted to those that SURVIVE the drop rules, and fail on any member of `S`
that is neither registered in `_CACHE_KEY_OPTIONAL_FIELDS` nor in a committed **shrink-only ratchet
baseline** — the repo's own `absent_shared` idiom. Measured baseline after R1: **79 names, all from
the single legacy record `tests/golden/ercot_2026_2040.run_config.json`.** Cause **B** fields are
registered and so are never flagged (correct — they are designed). Pre-registered claim, gradeable:
**at `f2a834de` this gate would have been RED naming `pjm_seam_neighbour_hourly_ladder`, and it is
GREEN after R1.** The census also gains a reported (non-gating) dataclass-construction line and a
docstring stating its payload scope, so the "ok:" verdict stops implying coverage it does not have.

---

## 6. THE ORPHAN COUNT, COUNTED BEFORE THE EDIT — **ONE, AND IT IS NOT A BUNDLE**

Registering RESTORES pre-field keys; what it costs is any artifact solved **since `f2a834de`** whose
recorded key was computed WITH the field present at its default. Enumerated, not estimated:

```
committed run_config.json payloads carrying "pjm_seam_neighbour_hourly_ladder": 1 of 232
  docs/handoffs/scn-ws5b-neiso/REF/run_config.json  value=False  key=1b452c457ca786a6
  iso=NEISO  solved 2026-09-09T01:57:16Z  (~33 h after f2a834de)
committed bundle directories named by a 16-hex key                          : 74
  ... of which named by a field-present key                                 : 0
committed frontend/data/forecast/ff-verdicts.json cache_epoch values        : 55
  ... of which a field-present key                                          : 0
uncommitted/ignored bundles in this container                               : 0
```

**Cost, stated plainly.** Exactly one record is orphaned, it is not a keeper, not a dashboard-
registered run, not a key-named bundle directory, and not addressed by key anywhere — it is two JSON
files addressed by path in `docs/handoffs/`. Its sibling `scn-ws5b-nyiso/REF` does not carry the
field at all, so the ws5b pair is *already* internally inconsistent. If that lane re-runs NEISO REF
at HEAD it lands on a different key and re-solves: **one forecast solve**, and the artifact it
compares against is a committed `full_horizon_summary.json` that this repair does not touch.

**This is not large enough to change the recommendation**, so it is executed rather than served as
an owner card — and it is surfaced here, before the edit, exactly as the charter requires. The
inverse cost is the one worth weighing against it: leaving the field unregistered orphans **199 of
200** committed records, all six ISOs' keepers among them, and every future solve compounds it.

---

## 7. BOUNDARIES HONOURED, AND WHAT IS ROUTED RATHER THAN REPAIRED

* `config/solve_surface_declared.py` — **NOT TOUCHED.** Cause C stays; re-declaring a moved row
  would restore the pre-change key and re-serve the pre-change bundle.
* No committed `cache_key` is rewritten. No default is armed, disarmed or moved. No pin is weakened,
  skipped, xfailed or deleted.
* **ROUTED, not mine:** (a) `test_solve_surface_fingerprint_is_pinned[NYISO]` — a NYISO registry row
  was added (209 vs 208); the owning lane advances that pin with a dated cause block. (b) The CAISO /
  ERCOT surface moves behind cause C, already adjudicated as D79's designed re-key. (c)
  `scripts/check_mechanism_matrix.py` is EXIT 1 on `main` — `vre_curtailment_oversupply_allocation`
  is in neither the matrix nor the `absent_shared` ratchet; that is the SPP curtailment-allocation
  lane's rule-28(c) miss. (d) The two deleted fields with no `_CACHE_KEY_RETIRED_FIELDS` entry (§2).
* **Independent of D90-R**, as the director ruled: this repair gives that lane's arm a better
  address, not a different score.
