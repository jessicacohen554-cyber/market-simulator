# FINDING — capx D92: D77's named residue, closed

**Lane:** capx **D92** · **Date:** 2026-09-10 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/d77-co2-residue-resolve-fux1gc` · **Authority:** OWNER RULING **Q65** (capx ledger §0bi.3(a))
**Pre-registration:** `PRECOMMIT-capx-d92-2026-09-10.md` + **ADDENDA A / B**, all pushed before any LP
(`aac390a6`, `e89e0d95`, `0b845508`)

---

## 0. THE VERDICT TRANSITION

| | determination | FC-1…FC-8 |
|---|---|---|
| **BEFORE** `neiso-t3` (capx D90-R, 2026-09-09) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |
| **AFTER** (FC-5 + FC-6 re-based onto post-D77 arms) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |

**Every status, every reason, every caveat: unchanged. Prior preserved byte-equal at `neiso-t3-pre-d92`.**

**The one sentence: D77's two named cells were still being scored off pre-D77 bundles on the live
board, they are now scored off post-D77 arms, the numbers behind them move by up to a factor of five
— and not one score moves.** D90-R's lesson repeats on the cells D90-R could not reach: *the scores
can be sound while the numbers are stale.*

**And the finding worth more than the one this lane was chartered for: the CCS emission-rate seam was
SUPPRESSING the model's carbon response, not merely mis-stating its emissions.** The FC-6 paired-P1
base-vs-high margin goes **10.50 → 50.92 Mt** (3.69 % → 32.97 % of base). This lane predicted that
margin would *narrow*; it quintupled. §4.

---

## 1. PART 1(a) — THE SCOPE TABLE, IN / OUT AND WHY

D77 named *"the three NEISO T3 verdicts' co2@2030/2035/2040 FC-5 rows and their FC-6 paired-P1
cumulative-CO2 row … the only SCORED cells mis-stated."* Classification is by a **zero-LP forensic
test**, not a merge timestamp (this clone's history is grafted): D77's own published A/B separates
the two worlds by ~7 Mt at 2029 with nothing in between, so `co2_mt@2029` is a clean discriminator.

| verdict at HEAD | run it names | primary bundle | co2@2029 | carries D77? | FC-5 co2 rows read from | FC-6 P1 read from | IN / OUT |
|---|---|---|---|---|---|---|---|
| **`neiso-t3`** (live) | `…-t3-golden3-d90` | `d90-rescore` | **6.795** | **YES** | `dispositions/neiso-t3.json` → `bau` `706e7ba8e6582d42` (2026-09-01, **15.217**) — **NO** | `bau-d46/fc6` `67678e58b2d0526c` / `56019f3b0850e9f9` (2026-09-03, **15.305**) — **NO** | **IN — the two carried cells ONLY** |
| `neiso-t3-pre-d90r` | `…-t3-golden3-d60` | `bau-d60` | 14.021 | NO | same | same | **OUT — frozen prior** |
| `neiso-t3-pre-d60` | `…-t3-golden3-bau` | epoch `67678e58b2d0526c` | 15.305 | NO | same | same | **OUT — frozen prior** |
| `neiso-t3-pre-d47` | `…-t3-golden3-bau` | epoch `67678e58b2d0526c` | 15.305 | NO | same | same | **OUT — frozen prior** |

**What D90-R closed:** `neiso-t3`'s **primary bundle**. Re-pointed to the d90 run, which the forensic
test puts on the post-D77 side, so FC-1/2/3/4/7/8 are not stale for D77's reason. **Dropped by the
stop gate.**

**What D90-R did not close, and this lane owns:** `bau-d60` and `d90-rescore` carry **no `fc6/`
directory at all**, and the corridor table's own `model_source` names `bau`. So the live board's FC-5
co2 rows and FC-6 paired-P1 row were computed from bundles the forensic test classifies **PRE-D77**.
Two cells, one verdict.

**Why the three `-pre-*` records are OUT even though two of them are on D77's own list:** a `pre-X`
record exists to say what was scored *before* X. Its superseded numbers are the thing it records.
Re-solving one destroys its only function. `-pre-d90r` postdates D77's list and inherits the same
status. **The scope is two cells on one verdict, not four verdicts.**

**Not touched, declared in advance (PRECOMMIT §1.5):** the FC-6 **driver-battery** input (a separate
`--driver-battery` scorer input; D77 named its status as unable to change) is carried byte-identical.

---

## 2. PART 2 — THE `G1_UNKNOWN`: SEVEN, NOT ONE, AND IT IS STRUCTURAL

`check_key_provenance.py` is **EXIT 1** at HEAD with **six** `G1_UNKNOWN` rows (plus the CAISO lane's
`G6`), not the one the charter quotes. **All six reproduce their recorded literal EXACTLY under the
single recipe already committed for the one listed entry** — `{"undrop": ["pjm_seam_neighbour_hourly_ladder"]}`:

| record | recorded | HEAD rules | UNDROP | |
|---|---|---|---|---|
| `scn-ws5b-neiso/REF` *(the one listed)* | `1b452c457ca786a6` | `09b7e61d88f83579` | `1b452c457ca786a6` | MATCH |
| **`results/ff-t3-neiso-golden/d90-rescore`** | `ae317e63263c8eef` | `f04fd06348e1623d` | `ae317e63263c8eef` | **MATCH** |
| `scn-ws5b-neiso/CAP-STATE-TIGHT` | `9bceb08bc291fced` | `31e7090a388d7da7` | `9bceb08bc291fced` | MATCH |
| `scn-ws5b-neiso/ALL-CLEAN` | `1c5c40a4fd011b6b` | `aaecf1bb07355400` | `1c5c40a4fd011b6b` | MATCH |
| `scn-ws5b-neiso/CES-P60` | `bd7de61415f5d950` | `859b3ca99d187974` | `bd7de61415f5d950` | MATCH |
| `scn-ws5b-neiso/CARB-HI` | `0e65d419ef104c54` | `3b6a4671622d909a` | `0e65d419ef104c54` | MATCH |
| `scn-ws5b-neiso/CES-T80` | `e4286b070d08cdcb` | `5d22c3d99d9e8d2e` | `e4286b070d08cdcb` | MATCH |

**DISPOSITION — direction (ii), with a correction to how it is usually told.** This is a listing gap
on understood non-reproduction, and **the gap is structural, not a miscount.** capx D91's registration
merged at **2026-09-09T03:09:30Z** and its census counted **one** orphan — correct *for what was on
`main` at that instant*. But rule 32 `[R-SHARD]`(c)(1) **requires** a shard to pin an immutable SHA
and **forbids** it to rebase, so pre-D91 SHAs kept producing records long after the merge:
`CAP-STATE-TIGHT` at 05:39Z, `ALL-CLEAN` at 07:06Z (its sha `e81c6e61` verified **not** to contain the
registration), `CES-T80` at 11:21Z — **at least 9 h 24 min** past it.

> **D91's orphan set was never a fixed number that could be counted once and listed.** Any repair of
> this shape mints orphans for as long as any lane is still running on a pre-repair SHA.

**This lane appends nothing.** The record's own `what_this_is_not` — *"NOT a place to park a NEW
mismatch … only an owner card adds a class here"* — and the charter both forbid it. **The gate is left
EXIT 1 and reported.** What is owed is an owner card deciding whether a lane may list a `lag` record it
did not create, and whether the recipe should become a **class rule** (any payload carrying
`pjm_seam_neighbour_hourly_ladder` at `False` with a pre-`ee2275d2` solve sha) rather than seven
hand-listed rows. **OWNER: the capx director / the key-provenance desk (capx D85 / D91). Named, not
"routed to a batch."**

**What it said about this lane's own arm, and the measurement that confirmed it.** PRECOMMIT §2.4
predicted the legs would solve at a post-D91 HEAD and therefore reproduce. Measured after the push:
committed run configs **274 → 278**, reproducing **188 → 192**, mismatches **22 → 22**, `G1_UNKNOWN`
**6 → 6**. **All four legs reproduce their own keys and added no G1.**

---

## 3. PART 1(c) — EVERY PRE-DECLARED PREDICTION, GRADED

**10 hits (two of them declared near-certainties and therefore worth nothing), 2 misses.** Graded
against PRECOMMIT §5 as written.

| # | prediction | realized | grade |
|---|---|---|---|
| **D1** | L0 cumulative CO2 in **[140, 175] Mt** | **154.4195** | **HIT** |
| **D2** | P1 stays PASS (high < base) | 103.5042 < 154.4195 | **HIT** |
| **D3** | the P1 margin **NARROWS** below 10.50 Mt | **50.9153 Mt — it QUINTUPLED** | **MISS**, in the opposite direction (§4) |
| **D4** | P1.premise stays PASS | PASS, `min +25.00, max +25.00 $/t` | HIT — **declared a near-certainty; worth nothing** |
| **D5** | FC-6 stays CAVEAT on the two vacuous T1.6 rows | CAVEAT, detail still names T1.6a/T1.6b | **HIT** |
| **D6** | co2@2030 **sign-flips** into **[−45 %, −5 %]** | **+60.6 % → −25.0 %** | **HIT** |
| **D7** | co2@2035 goes below **−40 %** | **−2.0 % → −57.0 %** | **HIT** |
| **D8** | co2@2040 stays in **[−70 %, −50 %]** and moves **least** of the three | **−57.4 % → −60.0 %**; \|Δ\| 2.6 pt vs 85.6 and 55.0 | **HIT** |
| **D9** | **exactly two** IN-CORRIDOR rows become divergent, and they are `capacity:gas_cc@2040` and `generation:total@2040` | exactly those two | **HIT** |
| **D10** | HEAD drift small: L0 within **5 %** of `d90-rescore`'s 154.42 Mt | **0.000 %** — and byte-identical on every cell (§5) | **HIT** |
| **D11** | determination stays HOLD | HOLD | HIT — **declared a near-certainty** |
| **D12** | every leg's wall in **[25, 45] min**, FC-8 PASS | 31.9 / 43.2 / **46.9** / 31.8 min | **MISS on the bracket** (`gasup150` over by 1.9 min); status half hit |
| **D13** | FC-5 stays CAVEAT after re-authoring, no row left UNEXPLAINED | CAVEAT, **0 UNEXPLAINED** | **HIT** |

### 3.1 The one-sentence summary, graded as written — and it is HALF WRONG on the half that carried information

> *"the repaired basis moves D77's named cells a great deal and moves no category status — FC-5 stays
> CAVEAT and FC-6 stays CAVEAT — while the model's CO2 moves decisively AWAY from the AEO2025 anchor
> at 2030 and 2035, so the honest reading is that closing this residue makes the record truer and the
> corridor gap larger."*

| clause | verdict |
|---|---|
| "moves D77's named cells a great deal" | **RIGHT** |
| "moves no category status" | **RIGHT** |
| "FC-5 stays CAVEAT and FC-6 stays CAVEAT" | **RIGHT** |
| "CO2 moves decisively AWAY from the anchor **at 2030** and 2035" | **WRONG at 2030.** The sign reverses but the **magnitude shrinks**: \|60.6 %\| → \|25.0 %\|, i.e. **35.6 points CLOSER** to AEO2025. Right at 2035 (55.0 points further) and 2040 (2.6 further). |
| "the corridor gap larger" | **MIXED, not larger.** Net over the three co2 rows the model is 22.0 points further; but the count of divergent rows **falls 26 → 25**. |

**The three clauses that were nearly certain were right; the one that carried information was half
wrong.** Recorded as this lane's second miss.

---

## 4. THE FINDING THAT MATTERS MOST: THE SEAM WAS SUPPRESSING THE CARBON RESPONSE

D77 wrote that *"the P1 perturbation is a carbon-price increase, and a correctly-rated captured unit
pays one tenth of that adder, so the margin between the arms is exactly what this seam distorts."*
D77 was right that the margin is what the seam distorts. **It did not say the direction, and this lane
guessed it backwards.**

| | base cum CO2 | high (+$25/t) cum CO2 | **margin** | as % of base |
|---|---|---|---|---|
| **PRE-D77** (`bau-d46` arms, 2026-09-03) | 284.42 Mt | 273.92 Mt | **10.50 Mt** | **3.69 %** |
| **POST-D77** (this lane's L0/L1) | **154.42 Mt** | **103.50 Mt** | **50.92 Mt** | **32.97 %** |

**The mechanism, read off the fleets rather than argued.** With the seam defective, a converted unit
was re-booked at its *uncaptured* host rate, so it paid the FULL carbon adder and was nearly
indistinguishable from unabated gas — and the retrofit screen **saturated at ~9 GW in BOTH arms**,
leaving the carbon signal nothing to move:

| year | PRE-D77 base → high `gas_cc_ccs` | POST-D77 base → high `gas_cc_ccs` |
|---|---|---|
| 2030 | 8,942.6 → **8,983.2 MW** (+40.6) | 6,648.3 → **7,821.3 MW** (**+1,173.0**) |
| 2040 | 6,679.8 → 7,399.3 MW (+719.5) | 4,522.0 → **5,636.9 MW** (+1,114.9) |
| 2050 | 4,900.5 → 4,935.5 MW (+35.0) | 2,759.3 → **8,636.9 MW** (**+5,877.6**) |

Two effects compose, and both are D77's: the repair makes the base-case wave **smaller** (its
documented self-limiting effect — cheaper correctly-rated CCS depresses the price that justifies the
next retrofit), which leaves headroom; and it makes the carbon signal **bite**, because an abated unit
now genuinely escapes nine tenths of the adder.

**Consequence for the program, stated because it is not confined to this run: any FC-6 paired-P1
carbon-sensitivity number measured on a pre-D77 bundle understates the model's carbon response by
close to an order of magnitude.** Every T3 golden's FC-6 is carried from such a bundle (§9 item 3).

---

## 5. G-DRIFT: THE CONTROL RETURNED ZERO, AND THAT IS A RESULT THE CONTROL *EARNED*

PRECOMMIT §3 refused form-4 differencing and bought a same-container, same-HEAD control (L0). Against
the committed `d90-rescore` bundle, over the **573-commit** window `09ef52a3` → `aac390a6`:

```
cumulative CO2      154.4195  ->  154.4195     delta +0.0000 Mt  (+0.000 %)
differing trajectory cells, 25 years x every field :  0
invariants block identical                          :  True
```

**Nothing on the NEISO forecast solve path moved.** Two things follow, and the second is the honest
one: (a) the FC-5/FC-6 re-base is on the *same numbers* the verdict's own bundle carries, so the
PRECOMMIT §6.3 "reading (i) vs reading (ii)" fork **collapses — they are the same reading**, and this
FINDING reports one; (b) **form 4 would have reached the right answer here, and could only have
assumed it.** D88 §3 and D90 §5.1 established that a recorded-key audit sees neither derived-input nor
non-config code drift; a zero result is only knowable by measuring it. ~32 minutes bought the right to
say "no drift" instead of "no drift, probably."

---

## 6. THE RE-SCORE, PER LEG, AT FULL MAGNITUDE

**Controlled swap.** The scorer was first shown, in this container and before any leg existed, to
reproduce the standing `neiso-t3` record with **NON-PROVENANCE IDENTICAL = True** (and to reproduce
the registered `ff-verdicts.json` record on every field but `notes`). Only `--corridor` and
`--paired-invariants` were then swapped; summary, run-config, DOF ledger, attestation, hindcast score,
crossover score (**`rcrepair`**, per D90 D.2) and driver battery held byte-identical.

### 6.1 Category map — it does not move

| category | before | after | moved? |
|---|---|---|---|
| FC-1 … FC-4 | FAIL ×4 | FAIL ×4 | no — detail strings byte-identical |
| **FC-5** external corridor | **CAVEAT** | **CAVEAT** | **no — but every underlying number moved (§6.2)** |
| **FC-6** driver response | **CAVEAT** | **CAVEAT** | **no — still the two vacuous T1.6 battery rows, which are carried** |
| FC-7 provenance & DOF | FAIL | FAIL | no — same 2 UNIDENTIFIED entries |
| FC-8 runtime | PASS | PASS | no |
| **DETERMINATION** | **HOLD** | **HOLD** | **no** |

Reasons and caveats compare **identical**. Exactly two rows changed *detail*, and both belong to the
two swapped inputs — which is what makes this a controlled swap rather than a coincidence.

### 6.2 FC-5 — the three named rows, and the six that had to be re-authored

| row | model value | divergence | disposition |
|---|---|---|---|
| **`co2@2030`** | 14.8849 → **6.9545** | **+60.6 % → −25.0 %** | **SIGN REVERSED.** The committed text (*"Model CO2 at 2030 is HIGHER (+60 %)"*) is **falsified**; re-authored. **D77's named cell.** |
| **`co2@2035`** | 10.2669 → **4.5090** | −2.0 % → **−57.0 %** | text falsified — the committed *"level crossing … where the paths cross"* reading is **retired, not refined**; the −2.0 % was an artifact of the mis-booked rate |
| **`co2@2040`** | 4.4883 → **4.2141** | −57.4 % → **−60.0 %** | smallest move; quoted fleet refreshed (the CC fleet is **44 % abated, not the 100 %** the prior text recorded) |
| `capacity:gas_cc@2040` | 13.1354 → **10.2006** | +2.8 % → **−20.2 %** | **newly divergent — NEW explanation**: the self-limiting wave, 5,678.6 unabated + 4,522.0 abated vs AEO's 12,779.7 flat |
| `generation:total@2040` | 109.2832 → **105.6935** | −12.4 % → **−15.3 %** | **newly divergent — NEW explanation**; crosses the 15 % line by 0.3 pt and is reported as divergent rather than argued back inside |
| `generation:gas@2035` | 31.8971 → **28.4324** | +24.7 % → **+11.2 %** | became **IN CORRIDOR** — explanation retired |
| `generation:gas@2040` | 31.9637 → **28.0428** | +28.5 % → **+12.8 %** | became **IN CORRIDOR** — explanation retired |
| `capacity:fossil_peaker_steam@2040` | 6.7467 → **7.5887** | −18.2 % → **−8.0 %** | became **IN CORRIDOR** — explanation retired |
| `generation:gas@2030` | 36.1668 → **34.0442** | +57.0 % → **+47.8 %** | quoted CCS/total split refreshed |

**25 EXPLAINED DIVERGENCE, 29 IN CORRIDOR, ZERO UNEXPLAINED** (was 26 / 28 / 0). Anchors untouched on
every row (rule 13 `[R-MEASURED]`). The prior table is preserved byte-equal at
`dispositions/neiso-t3-pre-d92.json` — the pattern this directory already uses for
`neiso-t3-prera-2026-08-31.json`.

**The instrument, and why 54 rows moved when D77 named 3.** No committed tool recomputes a disposition
cell. `docs/handoffs/d92/corridor_model_values.py` implements each row's own `model_basis` literally and
**reproduces 54/54 of the prior table's cells from the bundle the prior table declares**, so the re-base
is mechanical and checkable. Editing only the 3 named rows would leave a table whose cells are keyed to
two different bundles. **The 51 other rows move as a consequence of closing the 3 named ones — stated as
a cost, not hidden as a tidy-up.** If the narrower edit is wanted, the preserved file is one `git mv` away.

### 6.3 FC-6 — the paired block

| row | before (`bau-d46`, PRE-D77) | after (this lane's arms) |
|---|---|---|
| **P1** | PASS — `base 284.42 Mt vs high 273.92 Mt` | PASS — **`base 154.42 Mt vs high 103.50 Mt`** |
| P1.premise | PASS — `+25.00 $/t in all 25 years` | PASS — **identical** |
| P2 | PASS — `gas-fired 35.01→34.77 TWh, LW price 82.50→91.55` | PASS — `gas-fired 33.83→32.60 TWh, LW price 79.64→92.05` **`[not scored at this grain: objective↑]`** |
| P3 | PASS — `builds moved 0.0 % (42337 → 42319 MW)` | PASS — `builds moved 1.7 % (41149 → 40429 MW)` |

**The P2 row is ONE SUB-CHECK WEAKER than the row it replaces, and it is reported on the row itself.**
A shard ships no dispatch cache, and the summary grain carries no objective value, so `objective↑`
reads not-scored (`coal↑` is unscored on both sides — NEISO holds no coal). Declared in ADDENDUM A §A.3
**before the solve**, together with why it could not be repaired: the shards were already launched and
this session has no channel to a running cloud shard.

**The assembly path was proven before it was used** (ADDENDUM B): pointed at the four committed `bau-d46`
arms — summaries, run_configs and ledgers, **no parquets**, exactly the artifact set the shards return —
it re-emits the committed `paired_invariants.json` with the same four idents in the same order, the same
statuses, and **three of four detail strings byte-identical**. P1's summary-grain route reproduces **both**
committed operands exactly. That proves the path introduces no error; it does **not** prove the summary
grain equals the cache grain in general, and is not upgraded to that claim.

### 6.4 The four legs

| leg | arm | cache_key | cum CO2 | 2028 / 2029 / 2030 | 2035 / 2040 / 2050 | RM 2050 | wall |
|---|---|---|---|---|---|---|---|
| L0 | `base` (**control**) | `dd8203a8bf1546b9` | **154.4195** | 12.9276 / 6.7954 / 6.9545 | 4.5090 / 4.2141 / 7.5166 | 0.06388 | 31.9 min |
| L1 | `carbon_plus25` | `f00aa4b9148bc316` | **103.5042** | 7.8968 / 4.1322 / 4.1596 | 2.7855 / 3.1160 / 1.9316 | 0.06235 | 43.2 min |
| L2 | `gasup150` | `51c20a5583394d8d` | 208.9630 | 12.6778 / 9.5291 / 9.9128 | 6.3576 / 7.1542 / 9.5033 | 0.07996 | 46.9 min |
| L3 | `gaspm5` | `e8bcc0b30e6388b3` | 168.0340 | 12.7428 / 6.7066 / 7.8590 | 4.8221 / 4.9800 / 8.4744 | 0.04737 | 31.8 min |

All four: 25/25 years, no error, `ccs_retrofit_vom_adder=8.0`, `ccs_retrofit_fixed_cost_co2_scaling=false`,
one arm override each, solved at the pinned `aac390a6`.

---

## 7. RULE 32 `[R-SHARD]`, AND THE ONE CLAUSE THAT COULD NOT BE MET

**(a) The parent ran no LP.** Phase 0, composition, scoring and registration only. **(c)** Each shard
got the full 40-character SHA, its own `--out-dir` and branch, self-checkable hard stops on the config
signature, an explicit `git add -f <its path only>`, and the named prohibitions. All four cleared their
hard stops and pushed only their own path.

**(b) COULD NOT BE MET, and is declared rather than evaded.** A leg is an indivisible ~32–47 minute
invocation: the evolution chain links the years and rule 12 `[R-PARALLEL]` already forbids solving them
in parallel inside a run, so 32(b)'s remedy — subdivide and launch children — has nothing to subdivide.
The shards were told to run to completion. **Two of four exceeded the 20-minute clause by more than
double**, and one (L2, 46.9 min) also broke this lane's own D12 bracket.

**An operational note the next orchestrator should have.** All four shards backgrounded the ~45–60 min
`data/clean` build and ended their turns, so none progressed until poked. There is no `send_message` to
a cloud shard from here; the working channel is `create_trigger` with `persistent_session_id` +
`fire_trigger`, which resumed all four. **I also misread the elapsed time and nudged at ~10 minutes
while believing an hour had passed — the shards were healthy and the nudge was premature.** It cost
nothing but should not be repeated: read `created_at`/`updated_at`, do not estimate.

---

## 8. RULE 31 `[R-RETAIN]` — WHAT IS ON DISK, AND THE PROMOTION QUESTION

**Nothing solved in this session has been deleted, and nothing will be.** `results/ff-t3-neiso-golden/d92/`
was added to `.gitignore` in the same commit as the PRECOMMIT — **that, not `rm`, is what discharges rule
29 `[R-SCREEN]`(c)** (the ercot-255 incident). The slim artifacts (summaries, run_configs, config.yaml, the
100 evolution ledgers, 4.2 MB) are force-added and committed; the **dispatch parquets live only on the four
shard containers' disks and this container never held them.**

**THIS CONTAINER IS EPHEMERAL.** Reproducing the four legs costs **~2.6 h of LP** (31.9 + 43.2 + 46.9 +
31.8 min) plus a ~45–60 min `data/clean` build per container — though in parallel shards that is ~1.8 h of
wall clock.

**THE PROMOTION QUESTIONS, ASKED EXPLICITLY:**

1. **Is the FC-5 re-base at the right width?** This lane moved all 54 rows because a 3-row edit leaves a
   two-bundle table. **If you want only D77's 3 named rows changed, say so** — the prior table is preserved
   byte-equal and the revert is one file.
2. **Should the `neiso-t3` record now point at leg L0 instead of `d90-rescore`?** §5 makes this a *pure
   rename*: L0 reproduces that bundle exactly, so no number would move — but L0's `run_config` reproduces
   its own cache key at HEAD and `d90-rescore`'s does not (§2). **Re-pointing would remove one of the six
   `G1_UNKNOWN` rows without touching the exceptions record.** I did not do it unasked: it changes what the
   board's `cache_epoch` names.
3. **Should the FC-6 re-measurement extend beyond this verdict?** §4 says every T3 golden's carried FC-6
   understates the carbon response by ~9×. That is a board sweep, which the owner declined this window; I
   name it rather than begin it.

**Say the word on any of the three and I will act while the artifacts are alive.**

---

## 9. NAMED AND LEFT — AND WHERE THERE IS NO OWNER, IT SAYS SO

Not this lane's, named-and-left per the charter:

1. Four dead ERCOT bundle dirs failing the parity gate — `ercot262_arm_2024/2025`, `ercot264_repro_2023/2025`
   (rule 29(c)). **OWNER: the ERCOT lane.**
2. The SPP mechanism-matrix shard is missing two cells. **OWNER: the SPP lane.**
3. `status/SPP.js` is stale. **OWNER: the SPP lane.**
4. The CAISO marker asserts CALIBRATED on a NOT-YET keeper. **OWNER: the CAISO lane.**
5. `caiso_dsw_lateevening_clean` unregistered — the `G6` red over 273 records. **OWNER: the CAISO lane.**

Opened or carried forward by this lane:

6. **The seven-record `lag` listing gap (§2)**, and the structural point that such a set cannot be counted
   once. **OWNER: the capx director / key-provenance desk.**
7. **FC-7's attestation row cannot detect a false nested assertion** (D90 §4.2). Untouched here; FC-7 was
   carried. **OWNER: the forecast desk / rubric owner** — as D90 routed it.
8. **FC-6 is CARRIED on every T3 golden and has never been measured on its own solve** (D90-R routed item 5).
   This lane re-based the *paired* half for the one verdict in scope. The general problem — every other T3
   golden, plus the driver battery on this one — **HAS NO LIVE OWNER. THERE IS NONE.** §4 raises its stakes:
   those carried rows do not merely lag, they understate the model's carbon response by roughly an order of
   magnitude.
9. **Whether the model's CC fleet should shrink as far as it now does** (`capacity:gas_cc@2040`, −20.2 %) —
   D90-R's *"the CCS retrofit wave's size or economics"*. Still open. **OWNER: the capx CCS lane** (which
   D77 §8.3 already names for the parasitic-uplift question in the same arithmetic).

## 10. BOUNDARIES HONOURED

* **No file under `src/market_sim/` was edited**, and none under `scripts/`. The three helpers under
  `docs/handoffs/d92/` are measurement records and say so in their docstrings.
* Rule 28 `[R-MECH-MATRIX]` **does not fire**: no mechanism proposed, tested or added; no `ScenarioConfig`
  field changed.
* No backcast artifact, keeper, marker, shard or freeze touched. **`program-status.json` untouched** — no
  FC letter moved.
* Rule 27 `[R-PUSH]`: **33 pushed files ≥ 300 lines, every one blob-verified against local after the push —
  all MATCH.**

---

## 11. ADDENDUM — THE PROMOTION, EXECUTED (owner instruction, 2026-09-10)

**Owner:** *"If structural integrity improves but gates regress that may still be a keeper."* **Measured
first. No gate regresses, so the licence was not needed.**

**"Keeper" does not apply here and the answer is not a dodge:** `keeper` is rule 15 `[R-DASHBOARD]`'s
BACKCAST designation, and this is a forecast T3 verdict on the separate FF-2D board, which has
determinations and not keepers. The forecast-side equivalent — registering the re-score — was already
done in §6. What promotion remained was §8 question 2, and it is now executed.

**`neiso-t3` now names `neiso-2026-2050-t3-golden3-d92-base` (`dd8203a8bf1546b9`)**, replacing
`…-d90` / `ae317e63263c8eef`.

| | |
|---|---|
| numbers moved | **none.** L0 reproduces the replaced bundle exactly (§5) — an address change, not a result |
| determination | **HOLD → HOLD** |
| FC-1…FC-8 statuses, reasons, caveats | **all identical** |
| only differences | FC-7 `run_config` row **828 → 837** config keys (schema growth); FC-8 wall **31.1 → 31.9** min — **both PASS either way** |
| FC-7 risk, measured before promoting | L0's DOF ledger, built with the committed instrument, is the **same 9 entries with the same 2 UNIDENTIFIED** — FC-7 **cannot** regress |
| new artifacts | `d92/base/dof_ledger.json` (generated) and `d92/base/forecast_attestation.json` (authored by the producing session per rubric §5; `dof_ledger_complete` recorded **false**, honestly) |

**Why it is an improvement:** the FC-5 disposition is keyed to L0, so the record now names the bundle
its own corridor table is computed from; and L0's `run_config` **reproduces its own cache key at HEAD**
while `d90-rescore`'s does not.

### 11.1 AN OVERCLAIM I CAUGHT BEFORE PUSHING, RECORDED RATHER THAN QUIETLY FIXED

The first draft of the registry note said the re-point *"removes one of the six `G1_UNKNOWN` rows
STRUCTURALLY."* **It does not.** `check_key_provenance.py` scans **committed `run_config.json` files,
not registry references**, and `results/ff-t3-neiso-golden/d90-rescore/run_config.json` is still
committed — capx D90-R's artifact, not this lane's to prune. **The count stays at SIX**, re-measured
after the promotion, and all six remain owned to the key-provenance desk (§9 item 6). The note and the
attestation both say so.

**What was NOT promoted, and why.** §8 question 1 (the FC-5 re-base width) stands as executed — the
owner did not ask for the narrower edit and the prior remains one `git mv` away. §8 question 3 (extending
the FC-6 re-measurement to every T3 golden) is **not** done: it is the board sweep declined this window,
and §4 makes it more urgent rather than more optional. It still **HAS NO LIVE OWNER**.
