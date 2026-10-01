# PREREG miso-246 — **THE MISO BACKCAST LEVER-QUEUE CENSUS.** Zero LP. The enumeration source, the adjudication rule, the cross-ISO calibration bar and the three named items' decision rules are all fixed HERE, before any adjudicating quantity, and pushed with the probe before either runs

**Keeper: `2026-09-08-miso-245-ladderfix`** (bundle `results/calibration/miso245_ladderfix_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered non-downgrading caveat, DOF ledger **41/2**.
**Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY.** MISO holds no `complete` marker, none is sought here, and
**no out-of-training year will be solved, scored or registered.** **Zero LP: this session runs no
solve of any kind**, screens nothing and promotes nothing.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — the MISO lever-queue census, the
PJM-standard artifact `ASSESSMENT-miso245-complete-declaration-2026-09-08.md` **§6** names as the one
respect in which MISO's `complete` case is weaker than PJM's. PJM was granted on a **formal census**
(*"Structural lever queue measured EMPTY at pjm-142"*, `calibration-complete.json` → `complete.PJM
.frontier_basis`); MISO has only a **pattern**. This session builds the census.

**WHAT THIS SESSION DOES NOT DO.** It does **not** grant, infer, imply or recommend-by-construction
MISO's `complete` marker — that is an explicit owner act under rule 22, every time. It does not solve
2022. It does not build, screen or arm anything it finds. **If the census surfaces a LIVE lever it
NAMES it and STOPS.**

---

## 0. DISCLOSED FIRST, AGAINST INTEREST — one measurement was taken BEFORE this PREREG existed

**MISO's own shard cell census was computed during reconnaissance, BEFORE this document was
written.** It is therefore **NOT a pre-registered measurement** and is labelled **PRE-PREREG**
wherever it appears:

```
MISO shard (docs/codebase-site/data/mechanism-matrix/MISO.js), 312 cells:
   K 80 · U 50 · R 17 · I 14 · O 8 · G 7 · "." 136
   O/U partitioned by the BASE row's `mode`:  B 19 · BF 24 · F 15   (58 total)
   => 43 backcast-lane-reachable O/U cells
```

**Why this is disclosed rather than quietly reused, and what it costs me.** §3's cross-ISO bar is a
bar I am setting while already knowing the quantity it will be applied to (43). I therefore fix the
bar **relative to a comparator I have not measured and cannot see** — the five `complete`-holding
ISOs' own counts — so the bar cannot be chosen to clear 43. **I have measured no other ISO's shard.**
If the bar is missed, it is missed, and §3's decision rule says what follows.

**A second pre-PREREG reading, also disclosed:** `G-DRIFT` on the backcast solve path since the
keeper's own sha is **NOT empty** (§6). This is reported, not used — a zero-LP census earns and
spends no control solve — but it is stated because a successor lane **cannot** assume rule 29(b)
form 4 without classifying those hunks.

---

## 1. THE INSTRUMENT AND ITS GATES — each can end the census

The probe is `scripts/probes/_miso246_lever_queue_census_phase0.py`, pushed **before it runs**. Every
bar below is a **literal in the probe**. `FAILED_LEGS` non-empty ⇒ the census's verdict is
**VOID** and this session publishes that first, at full magnitude.

| leg | what it asserts | bar |
|---|---|---|
| **G-PARSE** | the shard parser recovers **exactly 312** cells, and **every** one maps to a base row in `mechanism-matrix.js` carrying a `mode` in {B, BF, F} | exact; 0 unmapped |
| **G-MODE** | the base parser's `mode` counts over ALL rows partition the row set with no row missing a mode except rows carrying none in the committed file, whose count is reported | 0 silently-defaulted modes |
| **G-ISO** | the same parser, run on each of the six ISO shards, recovers each shard's own cell count and 0 unmapped cells | 0 unmapped, all six |
| **G-BUS** | the p_bus series is read from `system_<year>.parquet`, `pass == "P1"`, `zone == "MISO_external"`, 8,760 rows per year, and the South bands' bus `MISO_external_South` is **present and distinct** | exact |
| **G-RECON** | `build_recons` is imported from `_miso241_spp_quantity_side_charter_phase0.py` (the REPAIRED instrument), never miso-235 line 237; and for **Manitoba** the incumbent and repaired export legs are proven **identical arrays** (`np.array_equal`) in all three years | exact |
| **G-BASIS** | every price series carries a declared basis string in the JSON record, and the two Indiana-hub series (`da`, `rt`) are asserted **distinct** (`corr < 0.60` in every year, the lane's published +0.402/+0.424/+0.553) | corr < 0.60 |

**G-RECON's second limb can end the Manitoba leg**: miso-241 repaired the four-seam instrument's
**export** pricing. If Manitoba's export leg moved, then miso-236's published Manitoba template
numbers were measured on a superseded instrument and **§5(b) reports that FIRST** rather than
comparing against them.

## 2. THE ENUMERATION SOURCE — CLOSED, MECHANICAL WHERE POSSIBLE, FIXED HERE

A route enters the census from exactly one of three sources. **The enumeration is closed at these
three; anything outside them is out of scope and §7 says what that costs.**

* **E1 — SHARD CELLS (mechanical).** Every cell of `mechanism-matrix/MISO.js` whose code is **`O`**
  or **`U`** AND whose base row's `mode` is **`B`** or **`BF`**. *`mode: "F"` rows are
  forecast-lane and are OUT OF SCOPE by the handoff's own words — "every remaining **BACKCAST**-lane
  route" — and their count is reported so the exclusion is visible.*
* **E2 — CURATED NAMED ITEMS.** Every item recorded as *handed forward*, *named not chartered*,
  *named successor* or *open* in (i) `docs/mechanism-testing-matrix.md` §5.4's queue stamps and
  (ii) the "what is handed forward" / "non-claims" sections of the miso-232 … miso-245 FINDINGs.
  Enumerated by hand from those committed documents and **listed exhaustively in the FINDING** so a
  reader can check the list against the sources.
* **E3 — THE THREE HANDOFF ITEMS.** (a) model bus-price compression (miso-242 Q-B); (b) Manitoba
  determinism (miso-236 §3 / §5.3); (c) CC_REGULAR 2024→2025 shape emergence (miso-234).

## 3. THE ADJUDICATION RULE — fixed BEFORE the enumeration runs

Each enumerated route lands in **exactly one** class. The classes are exhaustive and ordered: the
**first** matching class wins, so the classification is deterministic and not a choice.

1. **`A` — ALREADY ADJUDICATED IN MISO.** The MISO shard cell is `R`, `I` or `G`, **or** the lane
   record carries a MISO-specific R/I/G adjudication for the route. **Never re-tested** (the
   DO-NOT-REDO discipline, rule 28(a)). *Not LIVE.*
2. **`G` — REFUSED BY A STANDING RULE OR OWNER RULING**, cited per route: rule 13 `[R-MEASURED]`
   (the input is a measured *outcome*); rule 14 `[R-ACCURATE]` **and the lane's standing
   envelope/ladder/K freeze** (*"NO re-derive, NO damping factor, NO change of K, NO re-spacing of
   δ_k, NO envelope or interface-limit change. It binds."*); rule 19 `[R-ONE-MECH]` (the phenomenon
   already carries a mechanism); rule 25 `[R-ISO-SCOPE]`; rule 1 `[R-STRUCT]` (the only available
   form is a level fitted to a residual). *Not LIVE.*
3. **`D` — NO DOF-FREE FORM.** Judged on **miso-241 PREREG §5's rule, quoted verbatim and not
   re-worded**: *a candidate is DOF-FREE iff every constant it introduces is either produced by an
   estimator already in the codebase reading a committed measured source, or fixed by an identity or
   a published external definition — and none is selected by, or selectable against, any residual,
   gate or criterion.* *Not LIVE.*
4. **`B` — DATA-BLOCKED.** No admissible measured series for the route exists in this repository and
   none is fetchable (the allowlist blocks it, or the publisher does not publish it). *Not LIVE.*
5. **`S` — STRUCTURALLY BLOCKED.** A measured series exists but **MISO's own corpus cannot meet a
   precondition the mechanism requires** — the named instance is MISO's offer corpus, masked with no
   fuel/technology attribute, with the class bridge REFUTED at miso-138 (miso-192). *Not LIVE.*
6. **`LIVE`** — none of 1–5 applies: a backcast-lane MISO route with a DOF-free form, an admissible
   measured series, and no standing refusal. **This is the class the census exists to find.**

**THE CENSUS VERDICT.** **`QUEUE EMPTY`** iff the `LIVE` set is empty. **`QUEUE NON-EMPTY`**
otherwise, and the census **names every LIVE member** and stops. **A NON-EMPTY verdict means the
assessment's §6 gap is NOT closed** and MISO's `complete` case rests on the pattern alone — that
outcome is fully available to this census and is not disfavoured by any rule above.

**PREDICTION, RECORDED SO THE FINDING CANNOT BE WRITTEN TO ITS OWN CONCLUSION.** I expect the census
to read **NON-EMPTY at the E1 (shard) grain** and **EMPTY at the E2 (curated) grain**. The prediction
decides nothing; the rule decides.

### 3a. THE CROSS-ISO CALIBRATION — what "EMPTY" could possibly have meant when PJM was granted

Because §3's classification of a `U` cell is *by the matrix's own header* the definition of the lever
queue (*"U untested — plausibly applicable but never tested in this ISO (**the lever queue**)"*), a
NON-EMPTY E1 verdict is only interpretable against what the **granted** ISOs carry at the same grain.

* **PRIMARY, GATED:** `N_bc(ISO)` = the count of backcast-lane-reachable (`mode` ∈ {B, BF}) `O`/`U`
  cells in each ISO's shard, measured with the **identical parser** (G-ISO).
  **BAR, fixed here and NOT measurable by me at the time of writing:** MISO's `N_bc` is **≤ the
  median** of `N_bc` over the five ISOs that hold `complete` (ERCOT, NEISO, PJM, CAISO, NYISO).
  * **CLEARS ⇒** MISO's untested-cell census sits at or below the standard the granted ISOs were
    granted at, so "lever queue EMPTY" in the granting sense **demonstrably never meant zero shard
    cells**, and MISO is not held to a bar no ISO has met.
  * **MISSES ⇒** MISO carries materially more untested backcast surface than the ISOs already
    granted, the §6 gap stands on its own terms, and the census says so.
* **SECONDARY, REPORTED AND NOT GATED:** the same count as a **share** of each ISO's non-`.`
  backcast-reachable cells. It is reported because raw counts are sensitive to how many cells an ISO
  marks n/a. **It is declared secondary HERE, before either number exists, so it cannot be promoted
  to primary after the fact.**
* **This measurement calibrates the standard. It grants nothing and refuses nothing.**

## 4. THE THREE NAMED ITEMS — measurements and decision rules, fixed before any number

**BASIS DISCIPLINE (binding on every line below).** The lane's published price-decile column is on
the Indiana-hub **RT** (`_miso224_floor_anatomy_phase0.actual_zone_price`); every seam ladder and
every seam regressor is on the Indiana-hub **DA** (`actual_lmp_hourly_MISO.parquet` `da`, stored
**float32**). They correlate only +0.402/+0.424/+0.553. **Every statistic below names its basis, and
G-BASIS gates that they are distinct.**

### 4(a) MODEL BUS-PRICE COMPRESSION — `p_bus` = the keeper's committed **P1** price at **`MISO_external`**

**M-a1 — REPRODUCTION (reported, not gated).** σ(`p_bus`) and σ(measured Indiana-hub **DA**) per
year, on the common finite row set. miso-242 §6 published **6.09 / 16.51 / 15.22** against
**12.81 / 19.89 / 26.12**, measured on the **miso-233** keeper. **Two promotions have intervened
(miso-243, miso-245), so exact reproduction is NOT expected and is NOT required**; any difference is
attributed to those promotions and reported at full magnitude. *If the object itself does not
reproduce — i.e. σ(`p_bus`) is no longer materially below σ(DA) — item (a) is reported as
**NOT REPRODUCED AT HEAD** first, before anything else.*

**M-a2 — THE RUNG TEST (GATED; this is the adjudicating measurement).** Enumerate, per hour, the
candidate prices that can set the dual at `MISO_external`: for every seam hosted on that bus and
every band `k`, the import offer and the export bid the keeper's **armed** ladder set applies
(hourly-anchored where armed, the incumbent flat ladder otherwise); **plus** the five border zones'
own committed **P1** prices, because an unconstrained border link equalises the two duals — that
addition is structural, it is declared **here** before the number, and it is reported separately so
its contribution is visible.
`R_rung(year)` = the share of hours in which `p_bus(t)` is within **$0.01** of at least one candidate.
* **DECISION RULE:** `R_rung ≥ 0.90` in **all three** years ⇒ `p_bus` is **RUNG-DETERMINED**: its
  dispersion is a mechanical consequence of the frozen ladders, the measured anchors and the merit
  position, every one of which is frozen under rule 14 / rule 23 and the standing freeze. Item (a)
  is then class **`G`** and NOT LIVE.
* `R_rung < 0.90` in any year ⇒ `p_bus` carries dispersion those frozen objects do not explain, the
  test does **not** dispose of (a), and M-a3 decides it.
* **THE $0.01 IS A TOLERANCE, NOT A TUNABLE.** If it is missed on rounding I publish the
  **min-distance distribution** at full magnitude and **do not widen it**.

**M-a3 — THE LEVER ENUMERATION (GATED; it can fail by not closing).** Every object that can change
`p_bus`, enumerated **here** before it is checked: (i) the seam ladders `δ_k`; (ii) the measured
`(month × hod)` deliverability envelope; (iii) the interface limits; (iv) the band count `K` and
width; (v) the hourly neighbour anchors; (vi) the `MISO_external` border-link TTCs; (vii) the seam
topology (which bus hosts which seam); (viii) the firm-import blocks. **The enumeration is verified
against the code, not asserted.** If the code reveals a ninth object, **the enumeration has NOT
closed, the gate FAILS, and item (a) is reported UNRESOLVED** — it is not patched by adding the
object after the fact. If it closes, each member's standing status is cited and (a) is classified on
§3.

### 4(b) MANITOBA DETERMINISM

**Definition, taken verbatim from miso-236 and not re-derived:** `r = ` the OLS residual of the seam's
**net** flow on that seam's price regressor (Manitoba's is the Indiana-hub **DA**); `R²_tmpl` = the
**DOF-adjusted** between-cell variance share of the 12 × 24 = 288-cell (month × hod) block.

**M-b1 — REPRODUCTION (reported, not gated).** `R²_tmpl(r_measured)` and `R²_tmpl(r_model)` for
Manitoba, per year, on the CURRENT keeper. miso-236 published **0.7380 / 0.7205 / 0.6594** measured
against **0.6036 / 0.5207 / 0.2869** model, on the **miso-233** keeper. Again: **two promotions have
intervened, exact reproduction is not expected and not required.** The measured side should be
essentially unchanged (it reads no model artifact) — **and that agreement is EXPECTED, not
corroboration.**

**M-b2 — THE DECOMPOSITION (GATED; adjudicating).** Partition the model's Manitoba hours with the
lane's own committed classifier `_miso241…::classify_leg` into **CEILING-SET** (`env^eff ≤ n·w`,
`n ≥ 1`) and **MERIT-SET**. Compute `R²_tmpl` for `r_model` and `r_measured` **restricted to each
subset** (the block is re-fitted within the subset; cells with fewer than 8 samples are dropped and
the dropped-cell count reported). Define the subset's **determinism gap**
`Γ_sub = R²_tmpl(r_measured|sub) − R²_tmpl(r_model|sub)`.
* **DECISION RULE:** if `Γ_merit > Γ_ceiling` in **≥ 2 of 3** years, the object is the **merit test on
  `p_bus`** — the SAME object as item (a) — and rule 19 `[R-ONE-MECH]` makes it one phenomenon,
  disposed of by (a)'s classification. If `Γ_ceiling > Γ_merit` in ≥ 2 of 3 years, the object is the
  **envelope**, which the standing freeze refuses ⇒ class **`G`**. **If neither holds** (a 2–1 split
  the other way, or exact ties), item (b) is reported **UNRESOLVED**, classified on §3 by whether any
  DOF-free mechanism attaches to it, and **the failure of my own decomposition to separate is
  published as such.**
* **POWER, DECLARED BEFORE THE NUMBER:** this test compares two differences of two R²s on subsets
  whose sizes are set by `ceiling_active_share` (miso-241 §3 published **0.4279 / 0.4152 / 0.2492**
  for Manitoba). In 2025 the ceiling subset is ~25 % of hours, so its 288-cell block is fitted on
  ~7.6 samples/cell and its DOF adjustment is severe. **A 2025 `Γ_ceiling` is therefore the weakest
  number in this leg and I will say so rather than lean on it.**

### 4(c) CC_REGULAR 2024→2025 SHAPE EMERGENCE

**M-c1 — REPRODUCTION (reported, not gated).** miso-234's construction, re-run on the CURRENT
keeper's payload (`frontend/data/backcast/runs/2026-09-08-miso-245-ladderfix.js`, `plants[*].m`) and
the committed bench (`plants[*].campd`), CC_REGULAR only, **shape-normalised** (the model series
rescaled to the measured annual total, which cancels every level/coverage term — the C1 grid-delivered
basis is a different object and no C1 claim is made). Price deciles on the Indiana-hub **RT**.
Published values to reproduce: 2023 a pure LEVEL object (deficit 9.2–10.7 % in every decile,
shape-normalised span ±0.9 %); 2024 a monotone shape −44 → +336 MW; 2025 −813 → +464 MW; min h0 / max
h18–19. **Agreement is EXPECTED, not corroboration** — the two intervening promotions moved nothing
scored, so a reproduction is a check on the instrument, not evidence for anything.

**M-c2 — THE ADJUDICATION (GATED).** The object is a **diurnal / price-decile shape deficit of a
thermal class**. The candidate mechanisms are enumerated **here**, before any is examined, and each
is classified on §3: `gas_commitment_bridge`, `cc_committed_offer_margin`,
`cc_duct_peaking_row_scoped`, `cc_nameplate_summer_derate`, `cc_summer_derate_reconciled_basis`,
`cc_capacity_reconcile_path`, `cc_winter_capability_basis`, `cc_steam_part_reclass`. **If any is
LIVE, item (c) is LIVE and the census is NON-EMPTY.** *(These are E1 members too; (c) is where their
adjudication is argued, and the E1 table cites it rather than repeating it.)*

## 5. WHAT IS GATED AND WHAT IS REPORTED

**GATED** (a failure ends or voids the thing it governs): G-PARSE, G-MODE, G-ISO, G-BUS, G-RECON,
G-BASIS (§1); the §3a **primary** cross-ISO bar; M-a2's rung rule; M-a3's enumeration closure;
M-b2's decomposition rule; M-c2's candidate classification.

**REPORTED, NEVER GATED:** everything in §0; M-a1, M-b1, M-c1; the §3a secondary share; the
forecast-lane cell count; the G-DRIFT hunk inventory (§6); and every band, criterion and residual of
the keeper — **no scored criterion, no residual and no band comparison appears in ANY bar in this
document, in either direction** (rule 1 `[R-STRUCT]`).

## 6. G-DRIFT — reported, and it is NOT empty

`git diff <keeper git.sha> origin/main -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`.
The keeper's `run_config.json` records `git.sha = d059fcf7`; **verified, not trusted**:
`git cat-file -t` → `commit`, and `git merge-base --is-ancestor d059fcf7 origin/main` → **YES**
(after `git fetch origin main`; the check FAILS against a stale `origin/main` and that is why it is
run after a fetch). The diff is **NOT empty** — 25 files, +1,817/−36. **This session spends no
control solve and needs none** (it runs no LP at all), so the drift is reported rather than
classified. **It is stated because a successor lane cannot assume rule 29(b) form 4 without doing
that classification**, and `data/raw/_validation-source/actual_lmp.json` is in the changed set —
measured, its **MISO block is byte-identical** and only CAISO's moved, so **no MISO scored band is
exposed**; the other 24 files are unclassified here.

## 7. POWER AND SCOPE — what this census CANNOT do, said before it runs

1. **A census certifies RECORDED routes. It cannot prove no unrecorded mechanism exists.** A
   genuinely novel idea appears in no matrix row and in no handoff record, so E1 ∪ E2 ∪ E3 cannot
   reach it. **PJM's census had the identical limitation**, and this is the honest ceiling on what
   either artifact establishes.
2. **A `U` cell's classification is a judgement over the record, not a measurement**, except where
   §4 attaches a measurement. Where a classification rests on reading rather than measuring, the
   FINDING says so per route.
3. **The §3a bar is a comparison, not a standard.** It says where MISO sits relative to the ISOs
   already granted; it does not say that any of them should have been.
4. **Forecast-lane routes are out of scope by construction** and their count is reported. A census
   that silently dropped them would be measuring a smaller queue than it claimed.

## 8. NON-CLAIMS

1. **This session grants, infers and recommends no marker.** `complete` is an explicit owner act.
2. **Zero LP.** Nothing is solved, screened, registered or promoted; no bundle is produced; the
   keeper is unchanged at `2026-09-08-miso-245-ladderfix`.
3. **No `ScenarioConfig` field is created or changed**, and the DOF ledger stays **41/2**.
4. **No out-of-training year is solved, scored or registered.**
5. **MISO has no failing gate**, this session does not invent one, and **C3c is untouched** — it
   stays the designated frontier and opens only by a new admissible measured identification under
   its own charter **plus an owner ruling**, never by an offer adder, ORDC offset, scarcity
   multiplier or any level tuned to the tail. **None is proposed, computed or armed here.**
6. **No cell verdict moves on the strength of a classification alone.** A census classification is
   recorded in the FINDING; a shard cell moves only where this session's own measurement adjudicates
   it, and each such move is named.
7. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage** and no 2025 C1 pass is read as
   evidence anywhere.
