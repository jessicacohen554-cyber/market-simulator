# FINDING — SCN-RESOLVE-G1-RECHECK: the sibling G1 identities, re-checked without a replay

**Lane** SCN-RESOLVE-G1-RECHECK · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-07 ·
**Branch** `claude/scn-resolve-g1-recheck-t13bm6` · **DATA PROFILE** `code` · **PRECOMMIT**
`docs/handoffs/PRECOMMIT-scn-resolve-g1-recheck-2026-09-07.md` (pushed before any measurement) ·
**Trigger** `FINDING-scn-ws5a-resolve-ercot-2026-09-07.md` §1.5 and §4 items 2–3.

**ZERO LP.** Every claim below is read from committed source, committed run configs, or the sibling
lanes' own published FINDINGs.

---

## 0. Bottom line

1. **All five sibling ISO caches are ABSENT from this container** (§1). `results/<ISO>/` is
   gitignored and the committed post-fix bundles are slim — `full_horizon_summary.json` +
   `run_config.json`, no `FleetContext`, no `evolution_<year>.json`. So the corrected per-unit G1
   re-measurement, the per-year duplicate counts and a max relative deviation are **NOT COMPUTABLE
   HERE**, and none is estimated. The replay that would compute them costs **≈ 5.3 h of LP across
   the five ISOs** plus a **~39 min** `data/clean` precondition (§5).
2. **The re-check does not need the replay, because the defect is ONE-DIRECTIONAL and the
   sibling gate predicate is two-legged.** `aggregate_fleet` returns `passthrough +
   representatives`; a retrofitted unit (`fuel_type = "gas_cc_ccs"`) is **always** in `passthrough`
   and the colliding unabated `gas_cc` bin representative **always** in `representatives`; nothing
   between there and `FleetContext.unit_ids` reorders the list. So an id-keyed lookup resolves a
   colliding cohort member to the **unabated** twin — whose `emission_rate` is the host rate, not
   `host × 0.10`, and whose `fuel_type` reads `gas_cc`, **not** `gas_cc_ccs`. Both legs of the
   sibling G1 predicate fire. **A masked member cannot pass.**
3. **Therefore the five G1 PASSes SURVIVE, and the false-PASS risk the ERCOT lane routed does not
   exist through this mechanism.** CAISO, MISO, NEISO, NYISO and PJM each reported **zero failures**
   across every retrofitted unit-year of every leg. Under this defect a masked member fails; none
   failed; so no cohort member in any of the five was masked. **This holds under EITHER tie-break**
   (first-occurrence or last-occurrence wins), so it does not depend on the exact resolution code
   in those lanes' session-local scorers — which is the one thing here I cannot inspect (§2.3).
4. **The ERCOT direction was the only direction available.** On ERCOT the defect produced a false
   **FAIL** (resolve FINDING §1.5), and §2 shows that is not luck — it is what the fleet-assembly
   order guarantees. **Prediction P-1 HIT, and it overturns the routing premise as written.**
5. **What the re-check did NOT clear, and this is the more valuable half.** The non-uniqueness is
   not confined to gate scorers. **`unit_id` is used as a join key at ~20 sites in committed code,
   several of them on the live solve path** (§3) — including the economic-retirement screen's
   `unit_id → LP dispatch row` map and its `exit_exempt_unit_ids` set-membership filter, where a
   duplicate makes a converted CCS unit read the **unabated twin's dispatch** and makes one
   retrofit exempt **both** twins from the exit decision. Whether any of those fired in-horizon on
   any ISO is **UNKNOWN without the ledgers** and is stated as unknown, not as safe.
6. **The code question, answered as a recommendation and NOT implemented** (§4): the **fleet builder
   should emit unique ids**, not every consumer qualify by fuel type. Proposed as a two-part card —
   a cheap uniqueness **guard** now, and the narrow **fix** of renaming a retrofitted bin
   representative to match its new `fuel_type` — with the reasons the "qualify every consumer"
   alternative is the wrong shape.

---

## 1. T1-G0 — cache availability, and what a replay costs

**Verdict: ABSENT, all five ISOs, all thirteen legs.** `results/<ISO>/` does not exist at all in
this container for any of the six ISOs; nor does any leg's `results/<ISO>/<cache_key>/`.

| ISO | leg | cache key | solve sha | cache dir |
|---|---|---|---|---|
| CAISO | REF / LOAD-HI / LOAD-HI-ORGANIC | `2d16a246bb372e4a` / `86bfde6ed2896b99` / `ff8c04bc4eef6605` | `c538ecfb` | **absent** |
| MISO | REF / LOAD-HI / LOAD-HI-ORGANIC | `f1b3caa22b3f14ff` / `9688b06c1b0a5a54` / `b87deb7735c242a0` | `95ad76d4` / `b4bbd3c3` / `dcc04801` | **absent** |
| NEISO | REF / LOAD-HI | `8878d29743555b45` / `0d5c394b6c4e5cb6` | `1b95d430` / `61b9cce5` | **absent** |
| NYISO | REF / LOAD-HI / LOAD-HI-ORGANIC | `f10cc93084b4c0db` / `c2ceaefa4afafcda` / `27f19f22105ab6cb` | `931866cc` / `016e2fbe` / `fc2d80ac` | **absent** |
| PJM | REF / LOAD-HI | `67a786980ac38749` / `d1da885b4fdc4e6b` | `86062a0a` / `9ef06cf8` | **absent** |

Every committed r2 leg directory holds exactly two files (`full_horizon_summary.json`,
`run_config.json`). The G1 predicate needs the per-unit `FleetContext.emission_rate` /
`unit_ids` / `fuel_types` **and** the evolution ledger's `ccs_retrofits` rows carrying
`old_emission_rate`; **neither is committed for any ISO**. This is the same limit CAISO's own
FINDING §2.2 and MISO's §2.2 stated for their pre-fix comparisons, arriving now on the post-fix
side.

**Not computable here, and not guessed:** per-ISO / per-year duplicate `unit_id` counts; whether a
duplicate is a retrofit-cohort member; unit-years re-checked under fuel-type-qualified resolution;
max relative deviation. §2 answers the *verdict* question a different way; it does not substitute
for these measurements, and does not pretend to.

---

## 2. T1-G1 / T1-G2 — the mechanism, and its direction

### 2.1 The mechanism is general, not an ERCOT accident — **T1-G1 PASS**

Three facts from committed source:

1. **`evolve_fleet` re-aggregates the whole fleet at the end of every evolution year**
   (`model/capacity_evolution/evolve.py:1125`: `fleet = aggregate_fleet(fleet,
   n_bins=config.heat_rate_bin_count)`), after retirements, retrofits and new entry.
2. **`aggregate_fleet` re-mints `{fuel_type}_{efficiency_bin}_{zone}`** for every aggregatable
   fuel (`data/fleet/legacy_bins.py:269`), where `_AGGREGATABLE_FUELS = {gas_cc, gas_ct, gas_st,
   coal, oil, biomass}`. **`gas_cc_ccs` is not in that set**, so a retrofitted unit takes the
   `passthrough` branch and keeps the id minted under its **pre-retrofit** `fuel_type`.
   `apply_ccs_retrofit` is explicit that it does so: *"The unit keeps its zone, capacity and
   `unit_id`"* while *"`fuel_type` changes to `gas_cc_ccs`"* (`capacity_evolution/ccs.py:193/204`).
3. **New unabated gas-CC entry lands in the same bin.** `_make_new_generator` stamps
   `efficiency_bin` from the best `HEAT_RATE_BINS["gas_cc"]` entry, which for gas-CC is `h_class`
   (`new_entry.py:660-663`), and a new `gas_cc` unit **is** aggregatable — so the next
   `aggregate_fleet` re-mints exactly the id the retrofitted unit already holds.

**The trigger condition, stated so an ISO can be checked against it:** a duplicate arises iff a
**legacy bin representative** is retrofitted **and** any unabated `gas_cc` unit occupies the same
`(efficiency_bin, zone)` group afterwards — which new gas-CC entry in that zone guarantees. That is
precisely ERCOT's `gas_cc_h_class_North` (REF builds 3,000 MW of gas-CC in 2030; resolve FINDING
§1.3), so **P-5 is a HIT**: the collision reproduces from the record alone.

**It is armed identically in all six ISOs.** Read from the six committed r2 `REF/run_config.json`:
`use_campd_bins = True`, `plant_level_fleet = False`, `heat_rate_bin_count = None` in **every** ISO
— so the `n_bins is None` predefined-bin branch that mints these ids is the live path everywhere,
and `ccs_retrofit_available_year = 2028`, `ccs_capture_rate = 0.9`,
`ccs_retrofit_vom_adder = 2.95`, both D50/D65-B scalings `True`, `ccs_retrofit_annual_cap_mw =
None` are identical across the six. **No ISO is structurally immune.**

### 2.2 The direction is fixed by assembly order — **T1-G2, and P-1 HIT**

`aggregate_fleet` returns **`passthrough + representatives`** (`legacy_bins.py:300`). The
retrofitted `gas_cc_ccs` unit is in the first list; the colliding unabated `gas_cc` representative
is in the second. Nothing downstream reorders:

- `build_dispatch_fleet` only **appends** (`dispatch_fleet = fleet + inline_imports`, then
  `+ hydro_units`, then `+ import_generators`; `data/fleet/assembly.py:1881-2049`) — no sort.
- `generators_to_fleet_arrays` builds `unit_ids=[g.unit_id for g in generators]`
  (`data/fleet/arrays.py:3651`) — a positional comprehension, no sort.
- `FleetContext` persists `unit_ids=list(fleet.unit_ids)` (`results/outputs.py:117`).
- There is **no** `sorted(fleet)` / `fleet.sort()` anywhere in `src/market_sim/`.

So **the converted twin always sits at a strictly lower index than the unabated one**. A
last-occurrence-wins map grades the unabated twin — the false **FAIL** ERCOT saw. **P-1 HIT**, and
the ERCOT lane's routed false-**PASS** risk does not exist through this mechanism.

### 2.3 Why the five PASSes survive — and why the argument does not depend on the tie-break

The sibling G1 predicate (parent FINDING §4) tests **two** things per retrofitted unit-year: the
persisted `emission_rate` equals `old_emission_rate × (1 − 0.90)` to rel-tol 1e-9, **and** the
unit's `fuel_type` is `gas_cc_ccs`. The unabated twin fails **both** — it carries the host rate
(ERCOT's measured instance: expected 0.036, got 0.360, `rel dev 9.0`, `fuel_type 'gas_cc'`).

Enumerate what an id-keyed lookup can return for a colliding cohort member:

| resolution | row returned | G1 outcome |
|---|---|---|
| last-occurrence-wins | the unabated representative | **FAIL** (rate and fuel_type) |
| first-occurrence-wins | the converted unit | **PASS** — correct row, correctly graded |
| any other single-row pick | one of the two | PASS iff it is the converted one |

There is no branch in which a masked member silently passes: the wrong row is *always* the
unabated one and it *always* fails. **CAISO reported max rel dev 3.79e-16 with "all `gas_cc_ccs`:
yes" over 10/17/18/22/23-unit cohorts; MISO 0.000e+00 with a "wrong `fuel_type`" column reading 0
in every row; the parent lane reported "Zero failures across every unit-year of every leg" for
NEISO, NYISO and PJM.** Zero failures ⇒ no member resolved to a wrong row ⇒ **no G1 verdict in the
five was produced by grading a twin.**

**The one thing I cannot verify, stated plainly.** The five lanes' G1 scorers were session-local
and are not committed (only two *policy*-lane `score_gates_*.py` are in the repo, and neither does
per-unit work). So "all five keyed on `unit_id`" is the ERCOT lane's report, inherited, not
re-read. **The conclusion above does not rest on it**: the table covers every possible single-row
resolution, so the verdicts survive whatever those scorers did.

**A residual that a replay WOULD close, and this is the honest boundary.** The argument proves no
cohort member was *masked*. It does **not** prove the five fleets carry no duplicate ids — only
that if they do, no retrofit cohort member sat behind one. §3's exposure is therefore **not**
cleared by it.

---

## 3. T1-G3 — exposure, per ISO and per consumer

### 3.1 Per-ISO cohort composition — what the published record can and cannot say

| ISO | cohort ids published? | composition | exposed via the cohort? |
|---|---|---|---|
| **CAISO** | yes — `CC_REGULAR_ZP26_p55182_econ`, `CC_REGULAR_SDGE_p55985_econ`, `CC_REGULAR_NP15_p55333_econ` (FINDING §2.1) | CAMPD per-plant tranches | **no** — `is_campd_bin` units take `aggregate_fleet`'s passthrough branch and carry a `plant_code`; their ids are never re-minted |
| **MISO** | yes — `CC_REGULAR_MISO-Plains_p7985_{econ,committed}`, `CC_REGULAR_MISO-Indiana_p1007_{econ,committed}` (FINDING §2.1) | CAMPD per-plant tranches | **no**, same reason |
| **NEISO** | **no** — only cohort *sizes* (28 units REF / 33 LOAD-HI at 2030) | **UNKNOWN** | **UNKNOWN** |
| **NYISO** | **no** | **UNKNOWN** | **UNKNOWN** |
| **PJM** | **no** | **UNKNOWN** | **UNKNOWN** |

**P-2 HIT on both limbs.** CAISO and MISO are structurally unexposed *through their cohorts*;
NEISO / NYISO / PJM come back UNKNOWN and are reported as UNKNOWN, not assumed clean. Their
**fleet-level** exposure is identical to ERCOT's by §2.1's config reading regardless.

**P-4 HIT.** Every sibling lane reported *units checked* == *cohort size* in every year. That is
**not a detector**: the masking is a cohort member's id resolving to a **non-cohort** row, the
lookup dict still holds exactly one entry per id, and the count is unchanged. No published table
could have settled this either way — which is why §2.3's predicate argument had to do the work.

### 3.2 The exposure that matters — live committed consumers of `unit_id` as a key

This is the part the gate re-check does not clear, and it is the reason the card in §4 exists.
Sites read at HEAD, classified by what a duplicate would do:

**Decision path — a duplicate changes what the model does:**

| site | code | effect of a duplicate |
|---|---|---|
| `capacity_evolution/retirements.py:3318` + `:3403` | `idx_of = {uid: i for i, uid in enumerate(fleet_arrays.unit_ids)}`, then `rows = _dispatch_rows(g, idx_of)` for **every** `g in fleet` | **both twins read the SAME LP dispatch row.** A converted `gas_cc_ccs` unit's pro-forma inframarginal margin is computed from the **unabated** twin's dispatch and availability — the wrong revenue on the wrong unit, inside the economic-exit screen (spec §5.2, step 3). |
| `capacity_evolution/retirements.py:3833` | `margins = [m for m in margins if m[0].unit_id not in exit_exempt_unit_ids]` | one retrofit exempts **both** twins from the exit decision. The same set carries D42's dated exits and D53/D78's sector gate, so the over-exemption is not CCS-specific. |
| `capacity_evolution/evolve.py:686` | `_retrofitted_ids = frozenset(...)`; `loss_tracker.pop(_uid, None)` | clears the consecutive-loss history of **both** twins. |

**Recording path — a duplicate corrupts or drops a ledger row (including the one G1 reads):**

| site | code | effect |
|---|---|---|
| `evolve.py:663` / `:691` | `_pre_ccs = {g.unit_id: g.fuel_type ...}`, `_post_ccs = {g.unit_id: g ...}`, and the `ccs_retrofits` row built from them (`mw`, `from_fuel`, `to_fuel`, plus the D65-B-R scaling fields) | **the artifact the G1 gate itself reads.** With a duplicate, `mw` and `to_fuel` are read off whichever twin the dict kept; in the pathological ordering the emission-shift test `_post[uid].fuel_type != _pre[uid]` can be **false for a retrofit that happened**, dropping the row entirely. |
| `retirements.py:3760` | `margin_detail[g.unit_id] = detail` | last writer wins; one twin's decomposition overwrites the other's in the FFR-5A ledger. |
| `evolve.py:435/473/551`, `900/933/1009/1047`; `retirements.py:333/2711/2761/2768/2806/2827/3915` | `{g.unit_id: ...}` maps and `{g.unit_id}` set-diffs behind the confirmed-exit, announced-retirement, entry and backstop attribution | id-grain attribution collapses or mis-attributes across a duplicate. |

**Benign (performance only):** `model/lp/model.py:1562` `old_index = {uid: i ...}` — the warm-start
basis carry-over. Both new twins inherit one old column's status; a warm start cannot change the
optimum, only the iteration count.

**Reachability, stated as unknown rather than as safe.** ERCOT's measured duplicate sits in the
**2030** `FleetContext` and was created by the **end-of-2030** aggregation — after 2030's screens,
and 2030 is the horizon's last year. Whether an *earlier* year in any ISO carried one (ERCOT's 2029
`gas_cc_h_class_Houston` retrofit is the obvious candidate) is exactly what the absent ledgers would
say. **No in-horizon decision impact is claimed here, and none is ruled out.**

---

## 4. The code question — a recommendation, proposed and NOT implemented

**Answer: the fleet builder should emit unique ids.** Requiring every consumer to qualify by
`fuel_type` is the wrong shape, for three reasons:

1. **It does not cover the sites that matter.** `exit_exempt_unit_ids` is a `frozenset[str]`
   compared against `g.unit_id` — there is no fuel-type to qualify a *set membership* by without
   changing the set's element type everywhere it is produced (three producers: D42 dated exits,
   D53/D78 sector gate, W2-C retrofit). Same for the `{g.unit_id}` set-diffs in `evolve.py`.
2. **It is an unbounded maintenance surface.** ~20 committed sites today, and every new
   per-unit diagnostic adds one. An identifier that is not a key is, in rule 24 `[R-REGISTRY]`'s
   spirit, an unregistered join channel — and the ERCOT lane's own gate-design lesson was that *a
   gate joining two artifacts on an identifier must first establish the identifier is a key*. The
   same is true of the model.
3. **The id is already self-describing and is simply stale.** `{fuel_type}_{efficiency_bin}_{zone}`
   *is* a fuel-type-qualified id. The bug is that a retrofit changes `fuel_type` and leaves the id
   naming the old one.

**Proposed as one card, two parts:**

- **(a) A uniqueness GUARD, now, and cheap.** Assert `len(set(unit_ids)) == len(unit_ids)` where
  the SoA is built (`generators_to_fleet_arrays`) or as a test over an evolved fleet. It would have
  caught this at the source instead of five lanes downstream, it costs one comparison per year, and
  it is a detector — it changes no decision. This is the part worth landing first.
- **(b) The narrow FIX: rename on retrofit.** Have `apply_ccs_retrofit` re-mint a **legacy bin
  representative's** id under its new fuel type (`gas_cc_h_class_North` → `gas_cc_ccs_h_class_North`)
  so an id of that form always names its current `fuel_type`, leaving CAMPD per-plant ids untouched.
  It is the minimal change that removes the collision at its source. **Its known costs, stated so
  the card is decidable and not sold:** it breaks any cross-year join on a retrofitted unit's
  pre-retrofit id (`loss_tracker` is already popped at retrofit, so that one is free; the
  `ccs_retrofits` ledger's `unit_id`, the D42/D53 exempt sets and every registered artifact that
  already names a retrofitted unit are not), and any committed bundle's ledger would use the new id
  going forward. It touches `src/`, so it needs its own lane, its own PRECOMMIT and a byte-identity
  check on an unaffected ISO.
- **Alternative considered and NOT recommended:** suffixing a colliding representative
  (`..._2`). It removes the duplicate but produces an id whose meaning depends on assembly order —
  a worse key than the one we have.

**Not implemented here** — this lane's charter is propose-only, and both parts write `src/`
(rule 27 `[R-PUSH]`: an Opus/Fable lane, which this is, but still its own scope).

---

## 5. T1-G4 — what a replay would cost, from committed artifacts

Per-ISO wall for a full re-solve of the committed r2 legs (`total_wall_s` and
`global_peak_rss_mb` from each leg's own `full_horizon_summary.json`; 5/5 years each):

| ISO | legs | wall | peak RSS | note |
|---|---|---|---|---|
| CAISO | REF 28.4 + LOAD-HI 28.2 + ORGANIC 27.3 min | **83.8 min** | 5.07 GB | |
| MISO | 31.3 + 30.8 + 30.9 | **93.0 min** | **9.98 GB** | rule 12 `[R-PARALLEL]`: ~2 concurrent invocations max |
| NEISO | 5.4 + 5.4 | **10.8 min** | 3.68 GB | cheapest by far |
| NYISO | 18.3 + 20.0 + 20.2 | **58.4 min** | 3.93 GB | |
| PJM | 43.3 + 29.8 | **73.1 min** | 8.97 GB | |
| **five-ISO total** | 13 legs, 65 solve-years | **≈ 319 min (5.3 h)** | | serial |

**Plus the precondition**, which a shard budgeting only for LP will miss: `data/clean` is derived
and gitignored, so `regenerate_clean.py` must build 56 datatypes / 1.5 GB first — **~39 min**, as
the ERCOT lane measured on a fresh container. And the profile is per-ISO
(`hydrate_data.py --profile <iso>`), not `code`.

**Is it worth spending?** On the G1 *verdict* question, **no** — §2.3 settles it at zero LP, and
rule 29 `[R-SCREEN]` clause (0) is explicit that a computable pre-solve gate is spent before an LP
is. On §3.2's live-consumer question, a replay is also the wrong instrument: what is needed there
is the **guard** in §4(a), which answers it for every future run instead of five past ones. The
narrow case for a replay is if the desk wants the *historical* duplicate census in the five
campaign fleets — and NEISO at **10.8 min** would settle whether any duplicate exists at all in a
non-ERCOT evolved fleet for ~4 % of the full cost. **Recommended shape if the desk wants evidence:
NEISO only, as a targeted probe, never the full 5.3 h.**

---

## 6. Predictions, scored as written

| pred | as registered | verdict |
|---|---|---|
| **P-1** | the defect is one-directional (false FAIL only); the routed false-PASS risk does not exist through it | **HIT** — §2.2, from `passthrough + representatives` plus three no-reorder confirmations. The routing premise as written is overturned. |
| **P-2** | CAISO/MISO structurally unexposed via their cohorts; NEISO/NYISO/PJM come back UNKNOWN | **HIT, both limbs** — §3.1. |
| **P-3** | all five caches ABSENT | **HIT** — §1, 13/13 legs. |
| **P-4** | *units checked == cohort size* is not a detector | **HIT** — §3.1. |
| **P-5** | the ERCOT collision reproduces from the record alone | **HIT** — §2.1: REF's 3,000 MW 2030 gas-CC build + `efficiency_bin = "h_class"` re-mints the retrofitted unit's id. |

**Five for five, and the gate-design self-score is where the interest is.** T1-G2 was written to be
able to overturn the premise that sent this lane out, and it did. The lesson is the ERCOT lane's,
sharpened: a gate that joins on an identifier must establish the identifier is a key — **and a
routing that infers a risk *direction* from one observation must establish that the direction is
free.** Here it was not: assembly order fixes it, and one look at `legacy_bins.py:300` was cheaper
than 5.3 hours of LP.

---

## 7. Routed — not executed

1. **The card in §4** — fleet-builder id uniqueness: guard (a) then fix (b). Opened on the desk
   ledger by this commit. Writes `src/`; needs its own lane.
2. **§3.2's live-consumer exposure** is open regardless of the G1 verdicts. The
   `retirements.py:3318/3403` and `:3833` sites are the two with a decision effect.
3. **NEISO-only duplicate census** (~10.8 min LP + the clean precondition), if the desk wants the
   historical answer §1 could not give. Not recommended ahead of the guard.
4. **The ERCOT resolve FINDING §4 item 2's routing** ("their G1 PASSes should be re-run with
   fuel-type-qualified resolution before being relied on") is **discharged by §2.3 without the
   re-run**, on the argument that no masked member could have passed. If the desk prefers the
   measurement to the argument, item 3 above is the cheap version.

---

## 8. Files

- `docs/handoffs/FINDING-scn-resolve-g1-recheck-2026-09-07.md` (this file)
- `docs/handoffs/PRECOMMIT-scn-resolve-g1-recheck-2026-09-07.md` (pushed pre-measurement)
- `docs/handoffs/ADDENDUM-B-scn-ws5a-policy-ercot-2026-09-07.md` (this lane's Task 2)
- `docs/handoffs/scenario-desk-ledger-2026-09.md` — the §4 card, added
- `docs/handoffs/FINDING-scn-ws5a-resolve-ercot-2026-09-07.md` §4 items 2/3 — a one-line pointer

No solve, no bundle, no registry sidecar, no `src/`, no `config/`, no CI. Zero LP.
