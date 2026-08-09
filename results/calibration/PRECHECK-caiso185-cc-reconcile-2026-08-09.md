# PRECHECK — caiso-185: THE CC DEMONSTRATED-CAPABILITY RECONCILE (`cc_capacity_reconcile`)

**Pre-registration. Written and pushed BEFORE any scored metric of this session's object
is read.** Every bar, branch and stop rule below is fixed here and is fail-closed: a
branch that does not fire licenses nothing, and a gate with no measurement is a FAIL, not
a silent pass.

* **Session:** caiso-185. **ISO: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d).
* **Branch:** `claude/caiso-185-cc-reconcile-by1axm`.
* **Incumbent keeper:** `2026-08-09-caiso-184-c1-lpbasis` — **NOT-YET**, C3a the SOLE
  load-bearing FAIL (2023 **+3.7 %** PASS, 2024 **+10.5 %** FAIL, 2025 **+13.1 %** FAIL;
  RT, band ±10 %). **DOF ledger 11 / 8.**
* **Holdout:** CAISO holds **no `complete` marker** (withdrawn by the owner 2026-08-06) and
  the **spend freeze is ACTIVE**. **2023 + 2024 + 2025 ONLY**, one bundle per arm (rule 16),
  years sequential within a run and arms sequential (rule 12).
  `calibration-complete.json` and `holdout-freeze.json` are **OWNER ACTS — neither is
  written by this session.**
* **C3a is REPORTED, never TARGETED, and is NEVER the promotion basis** (rule 1
  `[R-STRUCT]`; rule 13 `[R-MEASURED]` — nothing is tuned to it).

---

## 0. P0-1 — DO-NOT-REDO audit (rule 28 duty a), discharged in advance

The CAISO in-model lever queue (`docs/mechanism-testing-matrix.md` §5.2) is **EMPTY**: all
nine items are struck. This charter therefore had to prove that its object is a
**distinct, un-adjudicated cell** or stop. It is:

* **NOT the settled envelope DEPTH question (caiso-181, SETTLED).** That asked *which
  hours* are asserted unavailable, and answered **zero** interior contradiction over
  599,736 hours. This session touches **no window, no hour, no detector, no threshold and
  no outage artifact of any kind**.
* **NOT the grain seam (caiso-183, CLOSED and promoted).** That repaired the day↔hour
  round trip of the outage extract. Nothing here reads the extract's grain.
* **NOT the denominator basis (caiso-184, CLOSED and promoted).**
  `unit_outage_lp_capacity_basis` is armed on the incumbent keeper and is **carried
  forward unchanged on both arms**. `_iso_plant_capacity` is **NOT re-opened**, not
  re-tested and not modified. caiso-184's object was the *derate denominator*; this
  session's object is the **LP's CC capacity itself**, which no session has moved.
* **NOT any struck lever.** `battery_dispatch_adder` (permanent declared-residual DOF,
  all three exits closed at caiso-176/178/179), the measured-offer-surface coverage
  extension (caiso-182, both identification tests failed), the AS-power-reservation family
  (caiso-74/127/129), every N–S topology lever (caiso-164 §0/§6, **FORBIDDEN**), the
  seam/intertie family (caiso-142/143/167, STRUCK), `caiso_ps_charge_shape_anchor` (`G`,
  input walled), `unit_outage_short_windows` / `unit_partial_outage_windows`
  (caiso-136/180, coal-only detectors against **zero** coal in CAMPD's CAISO population) —
  **none re-opened, re-derived or re-tested.** `caiso_dam_outages` stays `U` and is **NOT
  armed here.**

**Positive licence.** The object was surfaced by caiso-184's own census, which is the
sitting keeper's evidence base: FINDING-caiso184 §2a records that after **both** capacity
bases were corrected, the residual `f_CEMS > 1` did not vanish but **concentrated**, and
§9 item 4 files it verbatim — *"Plant 358 Mountainview carries the entire post-correction
`f_CEMS > 1` residual and is the one `raise` row in `cc_capacity_reconcile_CAISO.csv`.
`cc_capacity_reconcile` (CAISO `U`) is its named mechanism — out of scope here."*
PRECHECK-caiso184 §5 names arming it as **"NOT licensed by this charter"**. This charter is
the successor that **is** licensed to touch it. The CAISO cell of
`cc_capacity_reconcile_path` is **`U`**; the boolean has **no cell at all** (§7 below).

---

## 1. THE OBJECT, at source precision

`data/raw/_processed-legacy/cc_capacity_reconcile_CAISO.csv` — **committed, 7 rows, 6
`cap` + 1 `raise`** — is the repo's own per-plant CAMPD **demonstrated-capability** table
for CAISO combined cycles. It is read by two consumers, and **only one of them is gated**:

| consumer | gate | what it does with the table |
|---|---|---|
| `fleet/eia860.py::_reconcile_cc_pmax_to_nameplate` (the always-on merchant-CC summer-capacity guard) | **UNGATED** | reads `campd_p999_mw` **only as a floor on a clip bound**: `bound = max(nameplate_sum, demonstrated_peak)`. It can only ever **reduce** a plant's pmax, never raise it, and it fires only on an EIA-860 double-file. |
| `fleet/campd_bins.py::_reconcile_cc_capacity`, called from `fleet_to_bins` (the synthesized-bins path CAISO uses) | **`ScenarioConfig.cc_capacity_reconcile`, default `False`** | applies each row per its `mode`: a `raise` row lifts `capacity_mw` to `reconciled_mw`, a `cap` row lowers it. |

**On the CAISO keeper `cc_capacity_reconcile = False`** (verified in
`results/calibration/caiso184_c1_lpbasis/run_config.json`). So the model **already holds
the table on disk and already reads its peaks for the clip bound, while ignoring every one
of its seven capability statements about the LP's own capacity.** That is the rule-14
`[R-ACCURATE]` gap this charter tests: a measured artifact, already committed, already
partially consumed, with the half that states capability switched off.

**The committed table, verbatim:**

| plant | name | `current_mw` | `campd_p999_mw` | `eia860_winter_mw` | `reconciled_mw` | `delta_pct` | mode |
|---:|---|---:|---:|---:|---:|---:|---|
| 260 | Dynegy Moss Landing Power Plant Hybrid | 1398.0 | 1017.9 | 1470.0 | 1017.9 | −27.2 | cap |
| 55345 | Otay Mesa Generating Project | 710.7 | 600.6 | 602.5 | 600.6 | −15.5 | cap |
| 55151 | La Paloma Generating Plant | 1156.0 | 985.7 | 1066.0 | 985.7 | −14.7 | cap |
| 55182 | Sunrise Power LLC | 685.2 | 587.9 | 608.0 | 587.9 | −14.2 | cap |
| 56532 | Colusa Generating Station | 712.4 | 633.8 | 668.0 | 633.8 | −11.0 | cap |
| 55518 | High Desert Power Plant | 960.0 | 854.1 | 942.5 | 854.1 | −11.0 | cap |
| **358** | **Mountainview Generating Station** | **1036.8** | **1107.6** | **1110.0** | **1107.6** | **+6.8** | **raise** |

**Correction to this charter's own premise, made before any measurement.** The charter
states the table "was written in cap-ish mode" and that `--mode both` is only
*recommended*. **The table's own contents refute that:** `derive_cc_capacity_reconcile.py`
emits `row_mode = "raise"` **exclusively** inside the branch guarded by
`elif args.mode == "both"`, so a `raise` row **cannot** be produced by `--mode cap` or by
`--mode raise` (which writes no `mode` column at all). The presence of both a `mode`
column and a `raise` row proves the committed CAISO table was derived with **`--mode
both`** — the recommended mode — already. Recorded here so the audit in §3 tests
reproducibility, not a mode migration that is not owed.

---

## 2. WHAT ARMING CHANGES — the wiring, stated before it is measured

`fleet_to_bins` builds one bin per `(plant_code, plant_group)`. For a CC group under
`cc_nameplate_summer_derate` (armed on the CAISO keeper) the bin's summed net-summer
capacity is divided by the published `cc_summer_derate_ratio` so the LP carries **full
nameplate**; `_reconcile_cc_capacity` is applied **after** that rescale
(`campd_bins.py:1763-1772`). The derive's `_model_cc_capacity` applies the **identical**
transform to produce `current_mw`, so the two sides are on the same basis **by
construction** — with one deliberate difference: the derive measures the **un-guarded**
fleet (`apply_cc_summer_guard=False`) to keep the table from becoming self-referential,
while production runs the **guarded** fleet. The MW actually applied must therefore be
**measured, never assumed equal to `current_mw` − `reconciled_mw`.**

**Zero new `ScenarioConfig` fields.** `cc_capacity_reconcile` and
`cc_capacity_reconcile_path` both already exist, and neither is a
`_CACHE_KEY_OPTIONAL_FIELDS` member — they are base cache-key fields, so arming already
hashes distinctly (measured at this head: CAISO default `51b2892ed6f0d742`, armed
`3c4c24ff762b45af`). **No cache-key registration is owed and none will be made**;
`scripts/check_cache_key_registration.py` is still run before pushing.

---

## 3. P0-2 — THE TABLE PROVENANCE AUDIT (design fixed here)

Rule 23 `[R-FROZEN-DERIVE]` governs: **a re-derive is admissible ONLY on a cited
SOURCE-DATA change, never because a residual moved.** The audit is read-only — it
recomputes the deriver's output to a **scratch path** and **never writes the committed
CSV** unless branch Q fires.

Repo history cannot settle provenance: the clone is shallow (235 commits) and every
`cc_capacity_reconcile_*.csv` traces to the single W1 root-collapse merge, so the
introducing commit and its source vintage are **not recoverable from git**. The audit is
therefore **reproduction against the vintage on disk**, which is the stronger test anyway.

**Three legs, measured per row:**

* **R1 — VALUE.** Re-run `_campd_p999_and_annual` over the CAMPD state extracts on disk
  for 2023–2025 and compare `campd_p999_mw` per row. This is the number the hook actually
  applies (`reconciled_mw` == `campd_p999_mw` on every row of this table).
* **R2 — MEMBERSHIP + MODE.** Re-run the full `--mode both` selection at this head
  (`_model_cc_capacity` on the current fleet, `_CAP_MARGIN`, `_MIN_DELTA`,
  `_CAP_FEASIBLE_CF`, the pure-play screen) and compare the emitted row set and each row's
  `mode` against the committed file.
* **R3 — CT-ONLY EXCLUSION.** Re-run `_ct_only_codes` and compare the excluded set to what
  the committed table's absences imply. The charter asks specifically whether *"the CT-only
  exclusion detector still excludes what it excluded"*.

**G-REPRO (fail-closed).** A committed row PASSES iff it is re-emitted at this head **in
the same mode** with `reconciled_mw` within **0.5 %**. `current_mw` / `delta_pct` drift is
recorded but is **not** a G-REPRO failure on its own: neither field is read by the hook,
and drift there tracks the **code** vintage (the fleet loader), which rule 23 does not
accept as a re-derive trigger.

**Branches, fixed now:**

* **BRANCH P — PROVENANCE-CLEAN.** All 7 rows pass G-REPRO and **no source-data change is
  citable**. → **Arm the table EXACTLY AS COMMITTED.** No re-derive, no rewrite, no byte
  changed. (Rule 23: absent a cited source-data change, re-deriving is forbidden even if
  the recomputation is identical — writing the file would be an unlicensed derive commit.)
* **BRANCH Q — SOURCE-DATA CHANGE.** One or more rows fail G-REPRO **and** a source-data
  change is citable (a CAMPD extract or EIA-860 vintage on disk that post-dates the table).
  → A re-derive **is** admissible; it must **cite the data change in the commit message**
  (rule 23), be run with `--mode both`, and the arm reads the re-derived table.
* **BRANCH S — STOP.** One or more rows fail G-REPRO and **no** source-data change is
  citable. → The committed table **contradicts its own deriver at this head**. Arming it
  would inject a value the repo's own measured pipeline would not now produce. **Do not
  arm. Register nothing. Spend no LP.** File the contradiction as a defect in the table (or
  in the deriver) and escalate.

---

## 4. HAZARDS — named before measurement, each with its own stop rule

### H-OVERCARRY — a cap row may be burying a distinct fleet-loading defect (rule 11)

Plant 260's `current_mw` is **1398.0 MW** of CC_REGULAR. Moss Landing's combined-cycle
block is two units of roughly 510 MW; the demonstrated peak is **1017.9 MW** and EIA-860
winter for the *whole* plant (which since 2020 is a hybrid site carrying Vistra's battery)
is 1470 MW. A −27.2 % cap is **an order of magnitude larger than a cold-weather rating
difference** and is the signature of a **model over-carry**, not of a plant that merely
never ran high.

Rule 11 is explicit that a distinct bug must be **root-caused, not buried in a capacity
value**. The deriver already refuses the mirror-image case (a *raise* more than
`_CAP_MARGIN` above model capacity is skipped and flagged as *"CAMPD contamination or a
fleet-loading under-carry"*) — but it applies **no such ceiling to a cap**. So:

**G-OVERCARRY (fail-closed).** For every `cap` row whose `|delta_pct|` exceeds
`_CAP_MARGIN − 1` (10 %), the session must **identify the source of the excess** —
i.e. reconcile `current_mw` against the plant's EIA-860 CC nameplate sum and net-summer
sum and say which of {a genuine ambient/rating gap, a double-file the guard did not catch,
a plant/technology attribution error, storage or a co-located unit leaking into the CC
group} accounts for it.
* If the excess is a **rating/ambient gap** (model capacity ≈ EIA-860 CC nameplate, and
  the plant simply never delivered nameplate) → the cap is a legitimate measured
  capability bound and the row stands.
* If the excess is a **fleet-loading or attribution defect** (model capacity materially
  exceeds the plant's own EIA-860 CC nameplate sum) → **rule 11 applies: the cap row is
  compensating for a different bug.** That row is **DISQUALIFIED**, the arm is **NOT
  taken on the table as-is**, and the defect is filed for root-cause. Because the hook
  reads the file as a whole, a disqualified row means the table cannot be armed as
  committed at all — the honest outcome is to file the defect and stop, not to hand-edit
  the file (a hand-edited table is an off-registry tuning channel, rule 24).

This gate can refuse the whole charter. That is deliberate.

### H-XGROUP — a row is matched on `plant_code` alone, not `(plant_code, group)`

`_reconcile_cc_capacity` builds `new_cap` by zipping over `bins["Plant_Code"]` with **no
group filter**. A plant carrying more than one bin (a CC block plus a co-located CT or
steam bin) would have **every** one of its bins reconciled. For a `cap` row that is inert
(`min(small, large) = small`); for the **`raise` row at plant 358 it is not** — a small
non-CC bin at 358 would be **raised to 1107.6 MW**, which would be a gross defect.

**G-XGROUP (fail-closed).** Enumerate every CAISO bin whose `Plant_Code` appears in the
table and record its `Plant_Group`. **Bar: no non-CC bin may change capacity.** A
violation is a **stop-the-line** finding: the arm is not solved, and the defect is filed
against `_reconcile_cc_capacity` (which is shared by all six ISOs).

### H-GUARD — double-counting against the always-on clip

The ungated guard already uses `campd_p999_mw` inside `bound = max(nameplate, peak)`.
Arming must **not** stack a second, differently-based capacity adjustment on the same
plant (rule 19 `[R-ONE-MECH]`). The two act at different points (guard: on the fleet's
per-generator `pmax_mw`; reconcile: on the assembled bin `capacity_mw`) and in different
directions, so they are not the same mechanism — but the **composition must be measured**,
not asserted. Recorded as a reported quantity: for each of the 7 plants, whether the guard
fired at this head, and the bin capacity before and after arming.

---

## 5. P0-3 — DIRECTION, pre-registered HONESTLY and as a HAZARD, not a target

**Six of the seven rows are CAPS.** On the committed table's own `current_mw` basis they
remove **−942.3 MW** of CC capability, against **+70.8 MW** added by the single raise —
a **net −871.5 MW**, roughly **−6 %** of a CAISO gas-CC fleet of order 15 GW. (These are
the table's own arithmetic, not the applied delta; §2 requires the applied delta to be
measured.)

**Less CC capability ⇒ a scarcer supply stack ⇒ HIGHER prices.** The incumbent keeper is
already **+10.5 %** (2024) and **+13.1 %** (2025) **OVER** the actual mean LMP. So the
dominant leg of this mechanism pushes **the wrong way for the fit**, and the one leg that
pushes the right way (plant 358) is an order of magnitude smaller.

**Pre-registered, binding:**

1. **A NET PRICE INCREASE IS AN ADMISSIBLE OUTCOME AND DOES NOT REFUTE THE MECHANISM.**
   Rule 1 `[R-STRUCT]`: a structurally-correct measured capability **stays in even if it
   makes the fit worse**, and is never judged by whether the residual moved. Rule 14
   `[R-ACCURATE]`: a worse fit after swapping an estimate for measured data is **a signal
   to open a root cause, never a licence to revert to the estimate**.
2. **A PRICE DECREASE IS EQUALLY NOT CORROBORATION.** The direction is recorded here
   precisely so that neither sign can be presented after the fact as evidence the
   mechanism was right.
3. **C3a IS NOT A GATE IN THIS SESSION AND IS NOT THE PROMOTION BASIS.** The promotion
   basis, if any, is **structural**: that the model's CC capacities stop contradicting the
   demonstrated-capability table the repo has already committed and already half-consumes.
4. **NO PARTIAL ARMING TO CHASE A SIGN.** Arming a subset of rows (e.g. the raise alone)
   to obtain a favourable direction would be a residual-fitted mechanism and is
   **forbidden** (rules 1, 13, 24). The table is armed whole or not at all.

---

## 6. P0-4 — BYTE-EQUIVALENCE (ercot-174 BE-1 / BE-2 / BE-3 discipline)

* **BE-1 / G-SIXISO.** With the arm off, every ISO's assembled bin frame is
  **byte-identical** to the incumbent head. Measured as digests of the assembled bins for
  all six ISOs, off vs the pre-change tree. Since this session adds **no new field**, the
  stronger statement holds and will be asserted: the **only** solve-path difference is the
  value of an existing default-`False` flag, so **five ISOs are untouched by construction**
  and the digest comparison is the proof, not the claim.
* **BE-2 / rule 25.** CAISO must be able to read **only its own table**.
  `cc_capacity_reconcile_path` defaults to `None` and resolves **per-ISO** in
  `ScenarioConfig.__post_init__` to `cc_capacity_reconcile_<ISO>.csv`. Bar: for each of the
  six ISOs, the resolved path basename carries that ISO's own name; and arming CAISO leaves
  every other ISO's resolved path and bin frame unchanged. **A test is added asserting the
  per-ISO resolution** so the property is enforced, not merely observed (rule 28's
  `G-CONSIST` discipline from caiso-184).
* **BE-3.** **No data file is re-derived or rewritten** under branch P. Proven by a sha256
  ledger over `data/raw/_processed-legacy/cc_capacity_reconcile_*.csv` (all six), the CAMPD
  unit-outage extract, and `data/raw/eia-860/eia860_generator_operable.parquet`, taken
  before and after.

---

## 7. RULE 28(c) GAP TO CLOSE IN THIS SESSION

`cc_capacity_reconcile` — **the BOOLEAN** — has **no verdict-bearing matrix row**. The
matrix carries only `cc_capacity_reconcile_path` (cells `UUUUKU`, CAISO = `U`, added by
the nyiso-115 shared-field census) plus prose mentions of the boolean inside other rows'
notes. That is exactly the *"solve-affecting field registered only inside a sibling's
prose"* class that ercot-177 and nyiso-115 name: it passes the mention-anywhere CI gate yet
**can never carry a verdict in any ISO**.

**Binding commitment:** the boolean's own row is added to
`docs/codebase-site/data/mechanism-matrix.js` in the **same PR** as any arm. **The CAISO
cell is scored from THIS session's own evidence only. Every other ISO enters at `U` or
`.` and NO verdict is transferred** (rule 25, rule 28 duty d) — including NYISO's `K` on
the sibling *path* row, which says nothing about this boolean's verdict in any other ISO.
`scripts/check_mechanism_matrix.py` must exit 0.

---

## 8. GATES — pre-registered, fail-closed, each sized on THIS mechanism's own physics

**No gate below is keyed to the caiso-180 regeneration leg** (malformed twice; caiso-183
§5/§7d) **or to caiso-184's `f_CEMS` reduction** (which measured a different quantity —
the derate denominator, not the LP's capacity).

| gate | bar | consequence of failure |
|---|---|---|
| **G-REPRO** | every committed row re-emitted at this head, same `mode`, `reconciled_mw` within **0.5 %** (§3) | branch Q or **branch S** (stop) |
| **G-OVERCARRY** | every `cap` row beyond 10 % is attributed to a rating/ambient gap, **not** a fleet-loading or attribution defect (§4) | row DISQUALIFIED ⇒ **do not arm**, file for root-cause |
| **G-XGROUP** | **zero** non-CC bins change capacity when armed (§4) | **stop-the-line**; no arm; file against `_reconcile_cc_capacity` |
| **G-DOF** | ledger **EXACTLY 11 / 8**. Any increase is an **automatic fail** | fail |
| **G-NOFIT** | **ZERO** new fitted scalars. Every capacity EIA-860-published or a CAMPD demonstrated peak; **no value tuned to a residual**; `_CAP_MARGIN`, `_MIN_DELTA`, `_CC_NET_OF_GROSS`, `_CAP_FEASIBLE_CF`, `_CT_ONLY_RATIO`, `_PURE_PLAY_CC_SHARE` **unmoved** unless a SOURCE-DATA change is cited | fail |
| **G-SIXISO** | the other five ISOs' fleets byte-unchanged; CAISO reads only its own table (§6) | fail |
| **G-358** | arming must **REMOVE ≥ 80 %** of plant 358's `f_CEMS > 1` excess capacity-year, measured on the LP's own basis, in **every** year | if not, **the table is not the right instrument for this residual — say so and STOP** |
| **G-C1** | C1 free-class fuelmix **PASS on every free class, all three years**, both arms | fail |
| **G-PROT** | **C6 and C8 PASS**; C8 stays **SCORED** (`legitimacy_diagnostics.json` registered with every arm) | fail |
| **G-LOYO** | any verdict flip scored **leave-one-year-out within 2023–2025 BEFORE promotion** | no promotion |
| **CONTROL** | **MANDATORY if any arm solves.** Reproduce the incumbent via `--replay-bundle results/calibration/caiso184_c1_lpbasis` — **never a remembered CLI string**. Re-measure the same-head noise floor **hour-by-hour at FULL precision** and quote it **BEFORE** any treated delta is read | see below |

**On G-358, stated honestly rather than oversold.** Because `reconciled_mw` **is** the
p999 of the plant's own CEMS net series, setting the LP capacity to it makes
`f_CEMS ≈ 1` **close to by construction**. G-358 is therefore **not** evidence that the
number is right — it is a **wiring test**: it fails if the raise row does not reach the
bin, if the bin's live capacity is not the `current_mw` the table assumes, if the guard
interferes, or if the group routing misses. Its ≥ 80 % bar is set below the ~99 %
arithmetic maximum precisely so it tests plumbing, not tautology. It is reported as such
and **never quoted as corroboration of the capability value**.

**On CONTROL.** caiso-184 measured the same-head control as **BIT-ZERO in all three years**
(0 of 61,320 zone-hours). That is the incumbent expectation. **If it is no longer bit-zero,
that is a finding about the head and is reported as one** — it is not absorbed into the
treated delta. Arm distinctness is asserted, not trusted, by re-using
`scripts/probes/_caiso184_arm_identity.py` (hourly-signature distinctness; its
single-key-delta predicate already handles a config-field delta). The solve cache is purged
between arms.

---

## 9. STANDING DATA BLOCKER — declared, and NOT a session lever

C3a's first named remaining contributor is the **WALLED hourly pumped-storage water state**
(`FINDING-caiso140` §B / caiso-141 A2). No public source exists; it is an **OWNER-FUNDED
INTAKE decision**. This session will **not** attempt a proxy, a split heuristic, or any PS
mechanism tuned to the level residual.

**If P0 concludes the reconcile cannot be identified or is provably inert** (branch S,
G-OVERCARRY, G-XGROUP or G-358 firing): **register nothing, spend no LP, file the result,
and escalate the PS intake to the owner as the only remaining named route** — together
with the question the charter names: whether CAISO should be declared
`CALIBRATED-WITH-CAVEATS` on a C3a ledger entry, **which the v3.1 rubric currently
FORBIDS** (C3c is the only ledgerable criterion; C3a is load-bearing). That question goes
to the owner; **a tenth lever is not invented.**

---

## 10. GOVERNANCE COMMITMENTS

* **Rule 1 `[R-STRUCT]`** — the mechanism is judged on structural faithfulness, never on
  the fit; a price rise does not refute it and a price fall does not corroborate it.
* **Rule 13 `[R-MEASURED]`** — every value is an EIA-860 publication or a CAMPD
  demonstrated peak. No measured *outcome*, price residual or benchmark enters any input.
* **Rule 14 `[R-ACCURATE]`** — this is the rule under test: measured capability preferred
  over the model's estimate, with a worse fit treated as a discovered root cause.
* **Rule 11** — a cap that is compensating for a distinct defect is root-caused, not
  buried (G-OVERCARRY).
* **Rule 15 / 16** — any arm that solves is registered on the backcast dashboard with its
  `legitimacy_diagnostics.json`, **all three years in ONE bundle**.
* **Rule 19 `[R-ONE-MECH]`** — the composition with the always-on summer-capacity guard is
  measured (H-GUARD), not assumed.
* **Rule 21 `[R-DOF]`** — ledger **11 / 8**, unchanged; G-DOF fails on any increase.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; spend freeze respected; **both markers
  untouched (owner acts)**; CAISO holds no `complete`, so no determination re-key is owed.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive is re-run against a residual; a re-derive
  happens **only** under branch Q with the source-data change cited in the commit.
* **Rule 24 `[R-REGISTRY]`** — no env knob, no hardcoded per-plant dict, **no hand-edited
  table**; the tunable is the existing `ScenarioConfig` field and appears in
  `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — CAISO only: no other ISO's extract, keeper shard, registry
  sidecar, status part or bench file is written, and no verdict transfers.
* **Rule 27 `[R-PUSH]`** — this pre-registration is pushed and blob-verified **before any
  scored metric of the object is read**; every push is verified by commit-SHA round trip;
  no existing ≥300-line file is rewritten from regenerated content.
* **Rule 28 `[R-MECH-MATRIX]`** — the boolean's row lands in the same PR as any arm (§7),
  the CAISO cell is scored from this session's evidence alone, and the §5.2 header is
  re-stamped in this session.
