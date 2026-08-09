# FINDING — caiso-185: the CC demonstrated-capability reconcile is **REFUSED** on a **measured basis defect**, discovered in P0 and declared as **NOT pre-registered**. The table is **provenance-clean and exactly reproducible**; the hook that reads it writes an availability-**inclusive** realized output into the LP's availability-**exclusive** capacity slot, so arming it would deny six plants output the CEMS record shows they produced. **KILL-BEFORE-SOLVE: zero LP spent, nothing registered, keeper unchanged.**

**Outcome: the chartered lever is REJECTED EX ANTE. Every pre-registered gate that could
be scored PASSES — including the two the charter named as its stop rules — and the
refusal rests on a defect none of them was pointed at.** The CAISO in-model lever queue is
now **empty with every cell adjudicated**, and the remaining named routes are both **owner
acts** (§9).

Keeper **UNCHANGED** at `2026-08-09-caiso-184-c1-lpbasis`. DOF ledger **11 / 8**, untouched.
**No `ScenarioConfig` field added. No file under `src/` modified. No data byte changed.**
`calibration-complete.json` and `holdout-freeze.json` **untouched (owner acts)**.
**C3a WAS NEVER READ** — no arm was solved, so no fit outcome could have influenced this
verdict. That is rule 1 `[R-STRUCT]` in its strongest available form.

**Pre-registration:** `PRECHECK-caiso185-cc-reconcile-2026-08-09.md`, 392 lines, sha256
`890c023ccec67e814ecf08c4ff71f750ba1532af435e8cef54786f6c969a6ccf`, commit `cf034db9`,
pushed and blob-verified (remote tree SHA identical to local) **before any measurement of
this session's object was taken**.

Instruments: `scripts/probes/_caiso185_table_provenance.py`, `_caiso185_seasonal_stack.py`,
`_caiso185_arm_capability.py`, `_caiso185_g358.py`, `_caiso185_be_proof.py`.
Records: `_caiso185_table_provenance.json`, `_caiso185_seasonal_stack.json`,
`_caiso185_arm_capability.json`, `_caiso185_g358.json`, `_caiso185_be_proof.json`.

---

## 1. P0-1 — DO-NOT-REDO, discharged

Discharged in full in PRECHECK §0 and not repeated here. In summary: the object is **not**
the settled envelope depth (caiso-181), **not** the grain seam (caiso-183), **not** the
derate denominator (caiso-184 — `unit_outage_lp_capacity_basis` is carried forward
unchanged and `_iso_plant_capacity` was not re-opened), and **not** any struck lever.
`caiso_dam_outages` stays `U` and was not armed. The positive licence is caiso-184 §9
item 4, which files this exact cell as its named successor.

---

## 2. P0-2 — THE TABLE IS CLEAN. **The refusal is not about the data.**

`data/raw/_processed-legacy/cc_capacity_reconcile_CAISO.csv`, 7 rows (6 `cap` + 1 `raise`),
re-derived read-only at the CAMPD / EIA-860 vintage on disk. Repo history could not settle
provenance — the clone is shallow (235 commits) and every `cc_capacity_reconcile_*.csv`
traces to the single W1 root-collapse merge — so the audit is reproduction, which is the
stronger test.

| leg | bar | result |
|---|---|---|
| **R1 — VALUE** | `campd_p999_mw` reproduces | **PASS** — max rel delta **7.9e-05** (six rows exactly 0) |
| **R2 — MEMBERSHIP + MODE** | same row set, same `mode` | **PASS** — 7 / 7 re-emitted, 0 new rows, 0 mode flips |
| **R3 — CT-ONLY** | exclusion set unchanged | **PASS** — `{10169, 55295, 57564, 57978}`, consistent with the committed table's absences |
| **`current_mw` drift** | recorded, not gating | **0.0 on every row** |

**G-REPRO PASSES on all seven rows**, so **no source-data change is citable** and
**branch P fires**: the table is armed as committed, or not at all. Rule 23
`[R-FROZEN-DERIVE]` therefore **forbids** a re-derive — and **none was made**. Nothing was
written to the committed path; the recomputation lives only in the probe's JSON record.

**The charter's own premise is corrected.** It states the table "was written in cap-ish
mode" and that `--mode both` is only *recommended*. `derive_cc_capacity_reconcile.py`
emits `row_mode = "raise"` **exclusively** inside the branch guarded by
`elif args.mode == "both"`, so the presence of a `raise` row proves the committed table was
already derived on the recommended mode. No mode migration was owed and none was made.

### 2a. G-OVERCARRY — the rule-11 stop rule, and my own hypothesis falsified

PRECHECK §4 registered **H-OVERCARRY**: that a −27.2 % cap at Moss Landing is far too
large to be an ambient rating gap and is likelier a **model over-carry**, which rule 11
says must be root-caused rather than buried in a capacity value. That would have
disqualified the row and the whole table.

**It is falsified.** For **all six** cap rows, `current_mw` equals the plant's own EIA-860
combined-cycle **nameplate** sum to four decimals:

| plant | `current_mw` | EIA-860 CC nameplate | ratio | EIA-860 CC summer | EIA-860 CC winter | CAMPD p999 |
|---:|---:|---:|---:|---:|---:|---:|
| 260 Moss Landing | 1398.0 | 1398.0 | **1.0000** | 1020.0 | 1020.0 | 1017.9 |
| 55345 Otay Mesa | 710.7 | 710.7 | **1.0000** | 592.7 | 602.5 | 600.6 |
| 55151 La Paloma | 1156.0 | 1156.0 | **1.0000** | 1010.0 | 1066.0 | 985.7 |
| 55182 Sunrise | 685.2 | 685.2 | **1.0000** | 561.0 | 608.0 | 587.9 |
| 56532 Colusa | 712.4 | 712.4 | **1.0000** | 640.0 | 668.0 | 633.8 |
| 55518 High Desert | 960.0 | 960.0 | **1.0000** | 889.2 | 942.5 | 854.1 |

**G-OVERCARRY PASSES.** The model is not over-carrying these plants; it is carrying their
published nameplate exactly, which is what `cc_nameplate_summer_derate` is designed to do.
Reported as a falsification of a hypothesis I pre-registered, not smoothed over.

---

## 3. THE GATES THE CHARTER NAMED AS ITS STOP RULES — **both PASS**

### G-XGROUP — the plant-code-only matching hazard

`_reconcile_cc_capacity` zips over `bins["Plant_Code"]` with **no group filter**, so a
plant carrying a non-CC bin beside its CC block would have that bin reconciled too — inert
for a `cap`, but a `raise` would lift a small non-CC bin to 1107.6 MW.

Measured through the shipped path on the keeper's own config: **exactly 7 of 258 bins move,
all `CC_REGULAR`, zero non-CC bins**, net **−871.5 MW**. **G-XGROUP PASSES.** The hazard is
latent in the shared code but does not fire in CAISO.

**H-GUARD** is answered by the same measurement: every moved bin's unarmed capacity equals
the table's `current_mw` exactly, so the always-on merchant-CC summer-capacity clip
(`_reconcile_cc_pmax_to_nameplate`) **did not fire on any of the seven plants**. There is no
composition to disentangle at the clip.

### G-358 — the wiring test

Scored on **exactly caiso-184's definition** (`X = Σ_t (CEMS_net − D2)^+`, `D2` the LP's own
bin capacity, no availability multiplier on either side) so the two sessions' numbers are
commensurable:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| plant 358 `f_CEMS > 1` excess removed | **99.93 %** | **98.08 %** | **99.94 %** |

**G-358 PASSES** against its 80 % bar. As PRECHECK §8 stated in advance, this is a **wiring
test, not corroboration of the capability value** — because `reconciled_mw` *is* the plant's
own p999, `f_CEMS → 1` is close to arithmetic. It confirms the raise row reaches the bin,
that the live bin capacity is the `current_mw` the table assumes, and that group routing
does not miss. **It is not quoted as evidence the number is right.**

---

## 4. THE REFUSAL — a basis defect, **discovered in P0 and declared as NOT pre-registered**

PRECHECK §4 registered H-GUARD, the composition with the *always-on clip*. It did **not**
anticipate the composition the provenance audit surfaced: the reconcile against the
**availability multipliers**, of which `cc_nameplate_summer_derate`'s seasonal ratio is the
largest. This is stated as a hazard **found during P0**, not as a bar moved after the fact,
and its criterion is a **measured contradiction with no free parameter**.

### 4a. The identity

`_reconcile_cc_capacity` writes `reconciled_mw` into the bin's **`capacity_mw`**. What the
LP can dispatch is `pmax × availability(t)`. The demonstrated peak is a **realized output** —
it sits on the availability-**inclusive** side of that product, because whatever derate the
plant actually suffered is already inside the number CEMS recorded.

Since `availability ≤ 1` everywhere,

    max_t ( peak × availability(t) )  ≤  peak

**with equality only if availability reaches 1.** So setting `capacity := demonstrated peak`
makes the plant's achievable output **strictly below its own demonstrated peak, by
construction.** Every multiplier between the two slots — the `cc_nameplate_summer_derate`
seasonal ratio, WEFOR/POF, the temperature-derate curve, the outage overlay — is applied a
**second** time to a quantity that already embodies it. That is rule 19 `[R-ONE-MECH]`: two
mechanisms for one phenomenon.

**This is caiso-184's disease in a different organ.** That session found a numerator and a
denominator on different bases; this is a value and its slot on different bases.

### 4b. Measured through the shipped path, not asserted

`load_or_synthesize_bins` → `bins_to_fleet` → `generators_to_fleet_arrays`, built twice from
the keeper bundle's own `run_config.json`, identical but for `cc_capacity_reconcile`.
Capability is `max_t(Σ tranches pmax × availability)` within each season, against the plant's
own CEMS p999 computed on the model's own summer mask (Jun–Sep) with the deriver's own
gross→net factor.

| plant | mode | **summer** unarmed / **armed** / CEMS | unarmed ÷ CEMS | **armed ÷ CEMS** | **off-summer** armed ÷ CEMS |
|---:|---|---|---:|---:|---:|
| 260 Moss Landing | cap | 1055.2 / **768.3** / 1011.1 | 1.044 | **0.760** | **0.787** |
| 55151 La Paloma | cap | 978.5 / **834.3** / 993.7 | 0.985 | **0.840** | **0.966** |
| 55182 Sunrise | cap | 606.8 / **520.6** / 570.4 | 1.064 | **0.913** | **0.950** |
| 56532 Colusa | cap | 662.1 / **589.0** / 619.1 | 1.069 | **0.951** | **0.965** |
| 55518 High Desert | cap | 926.4 / **824.2** / 854.1 | 1.085 | **0.965** | **0.965** |
| 55345 Otay Mesa | cap | 685.8 / **579.6** / 591.8 | 1.159 | **0.979** | **0.960** |
| 358 Mountainview | raise | 982.4 / **1049.5** / 1082.2 | 0.908 | **0.970** | **0.962** |

**All six cap plants fall below their own demonstrated output in BOTH seasons when armed.**
Moss Landing is the extreme: **768.3 MW armed against 1011.1 MW demonstrated** — the model
would deny **243 MW the plant is recorded as having produced**, in the highest-price season.
Unarmed, only La Paloma is marginally below (0.985).

The raise row behaves as designed and still does not close: Mountainview improves from
0.908 → **0.970** (summer) and 0.900 → **0.962** (off-summer), because the same availability
multipliers eat the raise. Even the leg that works is mis-based.

### 4c. Why this refuses the lever rather than merely qualifying it

Rule 14 `[R-ACCURATE]` prefers accurate measured data over an estimate. It does **not**
license an input whose **application** contradicts the measurement. Arming makes the model
assert an incapability that the CEMS record — the very authority the reconcile invokes —
refutes. Under rule 13 `[R-MEASURED]` the armed state is **less** faithful to measured data
than the unarmed state, so the rule that would normally compel arming compels refusing.

**Rejected whole, not in part.** PRECHECK §5 item 4 pre-registered that arming a subset is a
residual-fitted mechanism and is forbidden, and rule 24 `[R-REGISTRY]` forbids hand-editing
the table (an off-registry tuning channel). Arming only the raise row would have improved
plant 358 — and would have been exactly the move the pre-registration exists to prevent.

**No LP was spent.** PRECHECK §9 fixed in advance that a P0 conclusion of inadmissibility
means *register nothing, spend no LP*. Solving would have cost hours to price a
configuration already established as structurally inadmissible, and registering it would
have put a misleading run on the dashboard. Rule 1 forbids judging a structurally-correct
mechanism by its fit; the converse discipline — not solving a structurally-refuted one in
the hope the fit rescues it — is the same rule.

---

## 5. THE ROOT CAUSE OPENED (rule 14's requirement) — **filed, NOT built**

Rule 14 requires that a rejected accurate input open a root-cause investigation rather than
end the matter. It is opened here and deliberately **not taken as a lever** (the charter is
explicit: do not invent a tenth lever).

**The phantom the caps target is real, and it is OFF-SUMMER.** Unarmed off-summer capability
sits **8–13 % above** each capped plant's demonstrated off-summer output. The cause is
visible in EIA-860's own columns: `cc_nameplate_summer_derate` carries **unpublished
NAMEPLATE** as the off-summer capacity, while EIA-860 publishes a **WINTER** rating that the
CEMS record corroborates and nameplate does not —

| ratio | range across the 7 plants |
|---|---|
| CEMS off-summer p999 ÷ EIA-860 published **winter** | **0.906 – 1.001** |
| CEMS off-summer p999 ÷ EIA-860 **nameplate** | **0.73 – 0.89** |

Mountainview is the mirror image and confirms the reading: its published winter capacity
(1110.0 MW) **exceeds** its nameplate (1036.8 MW), and its demonstrated off-summer peak is
1111.0 MW — the model under-rates it for exactly the same reason it over-rates the other six.

**The named repair is a seasonal, availability-aware capability basis** — off-summer capacity
from the published winter rating, with the demonstrated peak entering on the
availability-inclusive side where it belongs rather than being written into a pre-availability
slot. That is a **different mechanism** requiring its own pre-registration, its own DOF
accounting and its own byte-equivalence proof. **It is filed here, not built.**

---

## 6. P0-4 — BYTE-EQUIVALENCE AND SCOPE

| leg | bar | result |
|---|---|---|
| **BE-1 / G-SIXISO** | no ISO but CAISO reachable | **PASS** — `git diff HEAD -- src/` is **EMPTY** (no source file modified at all this session), and `cc_capacity_reconcile` defaults `False` on a freshly-built config for all six ISOs |
| **BE-2 / rule 25** | CAISO reads only its own table | **PASS** — all six resolved paths carry their own ISO's name, are pairwise distinct, match `paths.cc_capacity_reconcile_path`, and arming CAISO moves none of them. **Now enforced by a test**, `tests/unit/data/test_fleet.py::TestCcCapacityReconcilePathIsoScope` (4 tests / 11 subtests), not merely observed |
| **BE-3** | no data file re-derived or rewritten | **PASS** — sha256 ledger over all six `cc_capacity_reconcile_*.csv`, the CAISO CAMPD unit-outage extract and `eia860_generator_operable.parquet` |
| **cache key** | armed hashes distinctly | **PASS** — CAISO default `51b2892ed6f0d742` → armed `3c4c24ff762b45af`; the flag is a **base** cache-key field, so **no `_CACHE_KEY_OPTIONAL_FIELDS` registration was owed and none was made**. `check_cache_key_registration.py`: ok, 705 fields, 152 registered, all resolve |

---

## 7. GATE TALLY

| gate | verdict |
|---|---|
| **G-REPRO** | **PASS** — 7 / 7 rows, same mode, max rel delta 7.9e-05 (§2) |
| **G-OVERCARRY** | **PASS** — all six caps are ambient-rating gaps; `current_mw` ÷ EIA-860 CC nameplate = 1.0000 (§2a) |
| **G-XGROUP** | **PASS** — 7 of 258 bins move, all CC_REGULAR, 0 non-CC (§3) |
| **G-358** | **PASS** — 99.93 / 98.08 / 99.94 % removed, bar 80 % (§3) |
| **G-DOF** | **PASS** — 11 / 8, unchanged; no parameter added |
| **G-NOFIT** | **PASS** — zero new fitted scalars; `_CAP_MARGIN`, `_MIN_DELTA`, `_CC_NET_OF_GROSS`, `_CAP_FEASIBLE_CF`, `_CT_ONLY_RATIO`, `_PURE_PLAY_CC_SHARE` all unmoved |
| **G-SIXISO / BE-1..3** | **PASS** (§6) |
| **G-C1** | **NOT REACHED** — no arm solved |
| **G-PROT** | **NOT REACHED** — no arm solved; nothing registered, so nothing is unscored on the dashboard |
| **G-LOYO** | **NOT REACHED** — no verdict flipped, no promotion |
| **CONTROL** | **NOT REACHED** — mandatory only "if any arm solves"; none did |
| *(not pre-registered)* **SEASONAL/AVAILABILITY BASIS** | **FIRES** — 6 of 7 plants contradicted in both seasons (§4) |

**No bar was moved.** The three gates that could have licensed the arm all passed; the
refusal comes from a check that did not exist when the bars were set, and it is labelled as
such throughout.

---

## 8. RULE 28(c) — the gap the charter named, CLOSED

`cc_capacity_reconcile` (**the boolean**) had **no verdict-bearing matrix row** — only the
sibling `cc_capacity_reconcile_path` plus prose mentions inside other rows' notes: the exact
"solve-affecting field registered only inside a sibling's prose" class ercot-177 and
nyiso-115 name. Its own row is added in this PR.

* **CAISO = `R`**, from **this session's evidence alone** — rejected ex ante, no solve
  (the `cc_mustrun_per_plant` / caiso-140 kill-before-solve precedent).
* **PJM = `K`, MISO = `K`** — **read from those ISOs' OWN committed keeper configs**
  (`pjm152_collapse_A`, `miso132_ccmin_B`, both `cc_capacity_reconcile=true`). This is
  **registration, not adjudication**, and **no verdict transfers** (rule 25 / 28 duty d).
  **Deviation from the charter, declared:** the charter directed "every other ISO `U` or
  `.`". Writing `U` over a **keeper-armed** mechanism would have been factually false and is
  precisely the concealment rule 28(c) exists to close, so the two armed lanes are recorded
  as armed and the note states explicitly that neither cell carries a verdict.
* **ERCOT / NYISO / NEISO = `U`** — flag `False` on their designated keepers.

**A live unmeasured exposure is flagged for the PJM lane:** PJM arms this flag **together
with** `cc_nameplate_summer_derate` — exactly the composition measured inadmissible here.
MISO arms it with the summer derate **off**, so its exposure is the residual WEFOR/POF leg
only. **No verdict transfers**; each lane must measure its own magnitude on its own fleet.

**Observed, not edited (rule 25):** the sibling `cc_capacity_reconcile_path` row's **NYISO
`K` is stale** — NYISO's current keeper `2026-08-08-nyiso-132-cf-arm` carries the flag
`False`. That cell belongs to the NYISO lane and was left untouched.

`scripts/check_mechanism_matrix.py` exits **0**. The §5.2 header is re-stamped in this
session (keeper id unchanged).

---

## 9. DISPOSITION AND THE OWNER QUESTION

1. **REFUSED.** `cc_capacity_reconcile` is not armed for CAISO. The keeper is unchanged, no
   run was solved, and nothing was registered on the dashboard — there is no completed run
   to register (rule 15 is not engaged).
2. **The table stands and is untouched.** It is provenance-clean; the defect is in the hook's
   basis, not the artifact. It remains correctly consumed by the always-on clip bound.
3. **No existing adjudication is repealed.** caiso-183's two failed gates and caiso-184's
   promotion stand at full magnitude.
4. **THE CAISO IN-MODEL QUEUE IS NOW EMPTY WITH EVERY CELL ADJUDICATED.** Per the charter, a
   tenth lever is **not** invented. The two remaining named routes are **owner acts**:
   * **(a) Fund the hourly pumped-storage water-state intake.** Walled input, no public
     source (`FINDING-caiso140` §B / caiso-141 A2); still C3a's first named contributor.
   * **(b) Rule on whether CAISO may be declared `CALIBRATED-WITH-CAVEATS` on a C3a ledger
     entry.** **Rubric v3.1 currently FORBIDS this** — since the owner amendment of
     2026-08-06, C3c is the *only* ledgerable criterion and C3a is load-bearing, so the
     fail-closed guard refuses it. Granting it would be a rubric amendment, not a session
     act.

## 10. Known-open, carried forward

1. **C3a's residual: 2024 +10.5 %, 2025 +13.1 %** — unchanged; nothing in this session
   touched it, and it was never read.
2. **The seasonal / availability-aware capability basis** (§5) — a named, measured,
   zero-DOF-looking candidate, **filed not built**, needing its own charter.
3. **PJM's live unmeasured exposure** (§8) — `cc_capacity_reconcile` armed together with
   `cc_nameplate_summer_derate` on its designated keeper. No verdict transfers.
4. **The stale NYISO cell** on the `cc_capacity_reconcile_path` row (§8) — for the NYISO
   lane to correct.
5. **`_reconcile_cc_capacity` matches on `plant_code` alone**, not `(plant_code, group)`
   (§3). Inert in CAISO, latent in the five other ISOs that share the code.
6. **Two pre-existing test failures at HEAD** carried over from caiso-184
   (`NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` and its sibling) —
   not this charter's object, reported so they are not attributed here.

---

## 11. Governance

Rule 1 `[R-STRUCT]` — no mechanism judged by its effect on the fit; **C3a was never read**.
Rule 11 — the cap rows were tested for whether they bury a distinct defect (G-OVERCARRY) and
cleared; the defect that *was* found is root-caused in §5, not buried. Rule 13
`[R-MEASURED]` — every value is EIA-860-published or CAMPD-measured; no measured outcome,
price residual or benchmark entered any input or any bar. Rule 14 `[R-ACCURATE]` — the rule
under test: measured capability is preferred over an estimate, but not when its application
contradicts the measurement; the root cause is opened rather than the estimate re-blessed.
Rule 15 / 16 — no run was completed, so none is registered; no single-year bundle exists.
Rule 19 `[R-ONE-MECH]` — the basis for the refusal. Rule 21 `[R-DOF]` — ledger 11 / 8,
unchanged. Rule 22 `[R-HOLDOUT]` — no year was solved at all; spend freeze respected; **both
markers untouched (owner acts)**; CAISO holds no `complete`, so no determination re-key was
owed. Rule 23 `[R-FROZEN-DERIVE]` — **no derive re-run, no data byte written**; the
recomputation is read-only and lives only in the probe record. Rule 24 `[R-REGISTRY]` — no
env knob, no hardcoded dict, **no hand-edited table**; partial arming refused. Rule 25
`[R-ISO-SCOPE]` — CAISO only: no other ISO's extract, keeper shard, registry sidecar, status
part, bench file **or matrix cell** was written; the two `K` cells in the new row are read
from those ISOs' own committed bundles and carry no verdict. Rule 27 `[R-PUSH]` — the
pre-registration was pushed and blob-verified before any measurement; every push verified by
commit-SHA round trip; no existing ≥300-line file rewritten from regenerated content (the
only edits to large files are a single inserted matrix row and a documentation block).
Rule 28 `[R-MECH-MATRIX]` — duty (a) discharged in §1, duty (b) in §8 (the tested cell is
updated in this session, rejection included), duty (c) closed in §8;
`check_mechanism_matrix.py` exit 0.
