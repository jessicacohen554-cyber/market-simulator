# FINDING — capx D90-R: the `neiso-t3` re-score on D88-repaired code

**Lane:** capx **D90-R** · **Date:** 2026-09-09 · **Model:** Opus · **Data profile:** `neiso`
**Session branch:** `claude/zen-volta-qo9avm` *(the charter names the lane
`claude/capx-d90r-neiso-t3-rescore`; the harness-designated branch is the one above and is where the
work landed — naming only)*
**Authority:** OWNER RULING **Q63** (2026-09-08, capx ledger §0bg.3(a)).
**Predecessor / parallel lane:** capx **D90**, which pushed its full pre-registration
(`docs/handoffs/PRECOMMIT-capx-d90-rescore-2026-09-09.md`, + ADDENDA A, B) and stopped without
solving. This lane **completed** D90; it did not redo it. ADDENDA **C, D, E** were pushed by this
lane *before* the solve and are part of that document.

---

## THE VERDICT TRANSITION — lead

**capx D90 LANDED CONCURRENTLY** (`5c0539af`, merged while this lane was solving). It solved the
same re-score and correctly cleared D88's flag. This lane's solve is therefore an **independent
replication**, and its additive contributions are three: the replication itself, an **arithmetic
correction to the D90 record** (§2.3), and **registering the re-score's own verdict on the board**,
which D90 did not do.

| | |
|---|---|
| **BEFORE this lane** | `neiso-t3` → `neiso-2026-2050-t3-golden3-d60`, **HOLD**, 4 reasons, scored **2026-09-06 on PRE-repair code**, session `capx-D60-R3`. D90 had removed `provenance.known_defect` but left d60's verdict in place. |
| **AFTER this lane** | `neiso-t3` → `neiso-2026-2050-t3-golden3-d90`, **HOLD**, 5 reasons (FC-7 added), the **re-score's own verdict**. Prior preserved byte-equal at `neiso-t3-pre-d90r`. |

**The one sentence: the D88 repair moved the trajectory a great deal and the score not at all —
no scored category status changed on the solve's account, so on this instrument the repair neither
helped nor hurt, while against the one external anchor readable from it (the FC-5 AEO2025 co2@2040
corridor) it is clearly WORSE, moving the gap −18.7 % → −60.0 %.**

FC-7 is the single category that moves, and it is **not this run's**: it moves identically when
`bau-d60`'s OWN committed `run_config.json` is re-run through the instrument at this HEAD (§3.4).

### The replication, stated as a measurement

D90 solved at `09ef52a3` (**pre-D91**, so its bundle landed at the drifted key
`ae317e63263c8eef`); D90-R solved at `44de83bc` (**post-D91**, realizing the **scored** key
`f04fd06348e1623d`). Two containers, two heads, same recipe:

| | capx D90 | capx D90-R | |
|---|---|---|---|
| determination | HOLD | HOLD | **match** |
| every FC-1…FC-8 status | — | — | **all match** |
| `co2@2040` | 4.2141 Mt | 4.2141 Mt | **match to 4 d.p.** |
| terminal reserve margin | 0.063877 | 0.063877 | **match to 6 d.p.** |
| cobweb row | `gas_ct(4); gas_cc(7)` | `gas_cc(7); gas_ct(4)` | same content, list order |
| `run_config` keys | 828 | 830 | two days of schema growth |
| wall | 31.1 min | 30.8 min | container timing |

**No substantive delta.** The three cosmetic differences are named rather than smoothed over.

---

## 1. EVERY D90 PREDICTION, GRADED

Graded against §5 as written, with A.3's correction to P6 and ADDENDUM B's pre-grading of P9 applied
exactly as they were fixed — before the solve, not after.

| # | leg | predicted | **realized** | grade |
|---|---|---|---|---|
| **P1** | FC-2 row2 terminal RM | **FLIPS to FAIL**, final RM in [0.5 %, 4.5 %] | **PASS → PASS**, final RM **5.3 % → 6.4 %** | **MISS** — and in the *opposite direction*: RM ROSE |
| **P2** | FC-2 row1 I12 band | degrades to CAVEAT or FAIL (~50/50) | **PASS → PASS**, detail byte-identical | **MISS** |
| **P3** | FC-2 row3 cobweb | stays FAIL, gas_cc count **≥ 13** | stays FAIL; gas_cc **13 → 7**, plus a new **gas_ct(4)** | **MISS** on the count (the binding half); status half hit |
| **P4** | FC-2 row4 backstop share | stays PASS, share rises, < 10 % | **0.5 % → 1.0 %**, PASS | **HIT** (all three legs) |
| **P5** | FC-1 I3 dump | stays FAIL; magnitudes move **< 2 pp**; sign declined | stays FAIL; **7 of 8 years byte-identical**, 2049 7.27 % → **8.03 %** (+0.76 pp) | **HIT** |
| **P6** | FC-5 `co2@2040` | A.3's test: **HIT iff co2@2040 < 8.559 Mt** | **4.2141 Mt** | **HIT on the letter — PREMISE FALSIFIED**, see §2.3 |
| **P7** | FC-5 category | stays CAVEAT; divergence count moves **≤ 2** | CAVEAT; **26 → 26**, set identical | **HIT, but trivially** — the rows are frozen dispositions and could not move (§2.3) |
| **P8** | FC-3 / FC-4 | **UNCHANGED — provably** | detail strings byte-identical | **HIT** |
| **P9** | FC-7 | PASS, 8–9 entries, all IDENTIFIED | **9 entries** (bracket hit), **2 UNIDENTIFIED**, FC-7 **FAIL** | **MISS** — pre-graded as such in ADDENDUM B/E *before* the solve |
| **P10** | FC-8 | PASS, wall **5–25 min** | PASS; wall **30.8 min** | **MISS on the bracket**; status half hit |
| **P11** | DETERMINATION | HOLD → HOLD | **HOLD → HOLD** | **HIT** |

**Tally: 6 hits (two of them weak — P6 on the letter only, P7 unfalsifiable), 5 misses.**

### 1.1 D90's own one-sentence summary, graded as written

> *"the repair will not move the determination; it will most likely make FC-2 strictly WORSE at row
> level (P1) while nudging FC-5's CO2 toward its corridor (P6) — i.e. the corrected trajectory scores
> somewhat worse on adequacy and somewhat better on emissions, and stays HOLD."*

| clause | verdict |
|---|---|
| "will not move the determination" | **RIGHT** |
| "FC-2 strictly WORSE at row level" | **WRONG.** No FC-2 row degraded. Two rows improved *within* their status (terminal RM 5.3 → 6.4 %, cobweb gas_cc 13 → 7); one worsened within PASS (backstop 0.5 → 1.0 %); row1 identical. |
| "nudging FC-5's CO2 toward its corridor" | **WRONG, and backwards.** Against the AEO2025 anchor the gap goes **−18.7 % → −60.0 %** (§2.3). |
| "somewhat worse on adequacy and somewhat better on emissions" | **INVERTED on both halves.** |

**The summary was right only on the half that was nearly certain and wrong on both halves that
carried information.** Recorded as the lane's principal miss, in the spirit of D87's missed bracket.

### 1.2 A prediction the PRE-REGISTRATION itself got wrong, already booked

ADDENDUM B predicted the FC-7 artifact would push **PASS → CAVEAT**. Realized: **PASS → FAIL**
("unattested skeleton"). B's *mechanism* was exactly right and its *severity* understated. This was
measured and booked in ADDENDUM E **before the solve**, not reinterpreted afterwards.

---

## 2. THE RE-SCORE, PER LEG, AT FULL MAGNITUDE

Scorer: `forecast_verdict.py --tier t3`, rubric **v1.1** — the same instrument ADDENDUM D re-validated
in this container (it reproduces the committed d60 verdict with **zero non-provenance diffs**). The
re-score is a **controlled swap**: only `full_horizon_summary.json` + `run_config.json` (+ the DOF
ledger) are the arm's; every other input is held byte-identical. Carried-input set: ADDENDUM D §D.2.

### 2.1 Category map — the headline is that it does not move

| category | committed d60 | **D90-R arm** | moved? |
|---|---|---|---|
| FC-1 structural integrity | **FAIL** (I3) | **FAIL** (I3) | no |
| FC-2 adequacy & equilibrium | **FAIL** (row3) | **FAIL** (row3) | no |
| FC-3 capacity-evolution skill | **FAIL** | **FAIL** | no — carried, provably (P8) |
| FC-4 crossover dispatch skill | **FAIL** | **FAIL** | no — carried, provably (P8) |
| FC-5 external corridor | **CAVEAT** | **CAVEAT** | no |
| FC-6 driver response | **CAVEAT** | **CAVEAT** | no — carried from `bau-d46` (A.2) |
| FC-7 provenance & DOF | **PASS** | **FAIL** | **YES — instrumentation, not the solve (§3.4)** |
| FC-8 runtime feasibility | PASS (6.7 min) | PASS (**30.8 min**) | no |
| **DETERMINATION** | **HOLD** | **HOLD** | no |

### 2.2 FC-1 / FC-2 — the legs that COULD move, row by row

These are computed from the arm's own summary (ADDENDUM D §D.3), so they are the real test.

| row | committed | **arm** | direction |
|---|---|---|---|
| FC-1 I3 dump 2043–2048 | 2.36 / 2.79 / 3.96 / 4.54 / 5.89 / 6.57 % | **identical, all six** | — |
| FC-1 I3 dump 2049 | 7.27 % | **8.03 %** | **worse** (+0.76 pp) |
| FC-1 I3 dump 2050 | 7.97 % | **7.97 %** | — |
| FC-2 row1 I12 band | PASS | PASS (identical) | — |
| FC-2 row2 terminal RM | 5.3 % in [3.8 %, 38.8 %] | **6.4 %** in band | **better** (+1.1 pp of headroom) |
| FC-2 row3 cobweb | `gas_cc(13)` | **`gas_cc(7); gas_ct(4)`** | **mixed** — gas_cc oscillation nearly halves; a gas_ct chain appears where there was none |
| FC-2 row4 backstop share | 0.5 % ≤ 10 % | **1.0 %** ≤ 10 % | **worse** (doubles, two orders of headroom left) |

**Better or worse, stated plainly: on the two gating categories that could move, the corrected
trajectory is neither better nor worse — both stay FAIL for the same named reason.** Underneath the
statuses it is mildly *better* on adequacy (terminal RM up, gas_cc cobweb halved) and mildly *worse*
on dumping and backstop reliance. Nothing here is close to a status boundary in either direction.

### 2.3 FC-5 — where the repair is clearly WORSE, and a D90 arithmetic error corrected

**The corridor row's own fields settle it.** `results/ff-corridor/dispositions/neiso-t3.json` is keyed
to the `bau` run (`model_source.cache_key 706e7ba8e6582d42`) and its co2@2040 row reads
`model_value = 4.4883`, `anchor_value = 10.5331`, `divergence_pct = -57.4`.

**So 4.4883 Mt is a MODEL value, not the table.** D90 §5's P6 ("model 9.5792 vs table 4.4883,
**+113.4 %**") and A.3's correction of it ("the control gap is **+90.7 %**") both treated 4.4883 as the
anchor and divided by it. Both numbers are **model-to-model ratios mislabelled as corridor gaps**. The
true anchor is **10.5331 Mt**, and my reading of it reproduces the committed row's −57.4 % exactly.

| run | co2@2040 | gap vs anchor 10.5331 Mt |
|---|---|---|
| `bau` (the corridor's model_source) | 4.4883 | −57.4 % *(reproduces the committed row)* |
| `bau-d46` | 9.5792 | −9.1 % |
| **`bau-d60` — the control** | **8.5590** | **−18.7 %** |
| **D90-R arm** | **4.2141** | **−60.0 %** |

**The arm moves co2@2040 AWAY from the external anchor by 41.3 points.** P6 called this "the one leg
where I expect D88 to help"; on the anchor it is the one leg where D88 measurably hurts. P6 still
scores a HIT because A.3 pre-registered it as **direction-only against 8.559 Mt** and the arm is below
that — the letter is met and the premise is falsified, and both are reported.

**Why the CATEGORY nonetheless does not move.** FC-5's rows are hand-authored dispositions carrying
frozen `model_value`s keyed to `bau`; the scorer reads their verdicts, not a fresh comparison. So the
26 "explained divergences" are byte-identical and **P7 could not have failed** — a non-informative
hit, reported as such. **FC-5's scored leg is effectively carried; only its underlying number moved.**

### 2.4 The trajectory — large, coherent, and in one direction

| year | reserve margin C → A | co2 Mt C → A | lw_price C → A | thermal MW C → A |
|---|---|---|---|---|
| 2028 | 0.0394 → 0.0394 | 15.856 → **12.928** (−2.93) | 55.66 → 51.97 (−3.69) | 20143.8 → 20143.8 |
| 2029 | 0.0440 → 0.0440 | 14.021 → **6.795** (−7.23) | 60.43 → 53.78 (−6.65) | 20142.1 → 20142.1 |
| 2035 | 0.0404 → 0.0901 | 8.912 → **4.509** (−4.40) | 69.35 → 61.28 (−8.07) | 20326.3 → 21665.2 |
| 2040 | 0.0706 → 0.0458 | 8.559 → **4.214** (−4.34) | 70.25 → 66.95 (−3.30) | 21858.2 → 21144.7 |
| 2048 | 0.0360 → 0.0536 | 9.798 → **7.093** (−2.71) | 77.05 → 75.92 (−1.14) | 22107.9 → 22669.4 |
| 2050 | 0.0533 → 0.0639 | 10.196 → **7.517** (−2.68) | 80.62 → 79.64 (−0.98) | 22320.6 → 22669.4 |

**CO2 falls in every year from 2028 and prices fall in every year from 2028** — the signature of CCS
capacity that is now correctly *represented* in the LP rather than collapsed by colliding ids. Wall
402.4 s → **1850.5 s**; peak RSS 3454.6 → 3604.7 MB.

**2028 is the tell.** Its capacity *decisions* are byte-identical to the control (same fleet before and
after, same 12 retrofits, same 2984.409 MW, same reserve margin, same peak) — yet its **dispatch**
moves 2.93 Mt. Identical capacity, different dispatch, is exactly what a duplicate-`unit_id` collapse
in the fleet arrays produces and what D88's vintage-stamped re-mint repairs.

---

## 3. ATTRIBUTION, GOVERNANCE, AND WHAT IS *NOT* CLAIMED

### 3.1 T-REPRO (pre-registered A.5) — FAILS on the letter, PASSES on the substance

| year | bytes | **decisions** |
|---|---|---|
| 2026 | **IDENTICAL** | identical |
| 2027 | differs | **identical** — four economics diagnostics on ONE 1.5 MW capped-entry row (`64378_EG1`); `mc_mean` 179.559 → 188.325 $/MWh, `net_revenue` $233.81 → $198.31. Event `entry_capped` in both; `fleet_by_fuel_before/after`, `retirements`, `ccs_retrofits`, `reserve_margin` and every other top-level field identical |
| 2028 | differs | **identical** — `ccs_retrofits` **row schema** only (the arm's rows carry `capex_scale`, `fixed_cost_scale`, … added by later capx work); all 12 retrofits, all unit_ids, 2984.409 MW identical |
| **2029** | differs | **FIRST DIFFERING DECISION** |

**§3.5's CHANNEL E is therefore closed as decision-free.** The container's derived-input drift is real
but confined to one 1.5 MW unit's economics diagnostics, and it has a **named cause the arm's own log
prints**: `eGRID plant 64378 heat rate 8.500 MMBtu/MWh is below the simple-cycle physical floor 9.000
— clamped to the floor (SPP-49)`. Because **every year in which D88 is provably inert is
decision-identical**, the committed bundle is a valid control *for decisions and trajectory*, and
§3.5's FAIL branch (a same-container pre-D88 control solve) is **not needed**. The first differing
decision, 2029, is the second retrofit vintage — the first year a same-(bin, zone) id collision can
exist — which is D88's mechanism, arriving exactly where it should.

*Stated rather than buried:* T-REPRO as written is a **byte** test and it FAILED. I am reporting a
**decision-level** pass, which is a weaker claim than the one pre-registered, and I am not upgrading it.

### 3.2 The key situation, re-measured at this head (ADDENDUM C)

D91 **had landed** (PR #5720): `pjm_seam_neighbour_hourly_ladder` is registered at a frozen `"False"`,
so the arm realized **`f04fd06348e1623d` — the scored key** — the charter's "better address, not a
different score" branch. Pre-solve STOP re-verified: **0 real field diffs** against the committed
`config.yaml`; 6 apparent diffs are `yaml` list↔tuple round-trip artifacts; 31 fields absent from the
committed payload (D90's 29 + two of schema growth), **all at their dataclass default**.

### 3.3 What this lane does NOT claim

* **Rule 1 `[R-STRUCT]` governs, and it governed here.** The D88 repair is in because duplicate-free
  fleet identity is structurally correct. It stays in **whatever this re-score says** — including the
  41.3-point corridor degradation of §2.3, which is routed as an exposed root cause (the model's
  co2@2040 was already 18.7 % below the AEO anchor; correcting the fleet identity takes it to 60 %
  below, which says the CCS retrofit wave's *size or economics* is the real open question), never as
  grounds to revert.
* **No FC-6 reading here is evidence about D88.** FC-6 is carried from `bau-d46` and is structurally
  incapable of moving (A.2). The pre-existing staleness — d60's and now the arm's FC-6 rows are d46's
  numbers — is **reported, not absorbed**. Re-measuring it is another lane's work.
* **FC-3 / FC-4 likewise carried**, and provably inert (both windows end before
  `ccs_retrofit_available_year = 2028`).
* **One ISO's one run cannot support "D88 makes the model more accurate."** It does not, here, on the
  one external anchor available; and that too is one run.

### 3.4 FC-7 — reported under ADDENDUM B, whose clauses were followed literally

* **Clause 1** — the ledger was generated with the standard instrument and FC-7 scored on it. It read
  **FAIL**, so clause 1 did not end the matter.
* **Clause 2** — it reads other than PASS **solely** because the two restoration pins appear
  non-default/UNIDENTIFIED. Both readings are reported, neither hidden:
  * **(i) as-generated — the HEADLINE and what is registered:** FC-7 **FAIL**, determination **HOLD**,
    basis FC-1 · FC-2 · FC-3 · FC-4 · **FC-7**.
  * **(ii) secondary, d60's committed `dof_ledger.json` carried:** FC-7 **PASS**, determination
    **HOLD**, basis **identical to the standing verdict**.
* **Clause 3** — checked and **does not fire**: the arm's ledger is 9 entries / 2 UNIDENTIFIED and its
  field set is **identical** to the set measured pre-solve on d60's own run_config. No other
  UNIDENTIFIED entry, no change among the 7 identified, no `run_config`/attestation row movement.
* **Clause 4** — the DOF-ledger instrument was **not edited**.

**The decisive evidence that this is not the arm's** (ADDENDUM E, recorded pre-solve): regenerating
**`bau-d60`'s OWN committed `run_config.json`** through `build_forecast_dof_ledger.py` at this HEAD
yields the same **9 entries / 2 UNIDENTIFIED** — `ccs_retrofit_fixed_cost_co2_scaling` and
`ccs_retrofit_vom_adder` — and swapping only that ledger moves the *committed* d60 verdict's FC-7
PASS → FAIL. **This is a program-wide desynchronization between moved dataclass defaults and
`CURATED_IDENTIFICATIONS`, and it will hit every T3 verdict re-scored at this HEAD**, not just this
one. **Routed, not repaired here** — adding curated identifications changes the ledger for every run
in the program, which is not this lane's to do (clause 4).

---

## 4. THE FLAG

`provenance.known_defect` was D88's placeholder for this moment, and §6 of the pre-registration made
the outcome non-discretionary once the re-score completed.

* **capx D90 removed the flag** — correctly, and this lane did not touch that decision.
* **What D90 left undone, and this lane completed:** the board still carried **d60's verdict**
  (scored 2026-09-06, session `capx-D60-R3`, on pre-repair code) under the now-cleared flag. A
  cleared flag over a pre-repair scoring asserts that the defect is resolved *and* shows the number
  that was scored before the repair. This lane replaces that record with the **re-score's own
  verdict**, so the two now agree.
* **Asserted and verified** on both committed inputs: in `ff-verdicts.json` exactly one key moved
  (`neiso-t3`), exactly one was added (`neiso-t3-pre-d90r`), none removed, 106 → 107; the prior
  record is preserved **byte-equal**, and it retains D90's already-cleared provenance. In
  `program-status.json` exactly one ISO block moved (`NEISO`): `t3_provenance` restamped (the
  superseded stamp quoted inline) and `fc.FC-7` PASS → FAIL, consistent with the registered reading.

---

## 5. RULE 31 `[R-RETAIN]` — WHAT IS ON DISK, AND THE PROMOTION QUESTION

**Nothing was deleted.** Both solved bundles are on this container's disk —
`results/ff-t3-neiso-golden/d90-rescore/NEISO/` holds **`ae317e63263c8eef`** (D90's, whose
top-level evidence set is already committed on `main`) and **`f04fd06348e1623d`** (D90-R's, the
scored key). The duty rule 29 `[R-SCREEN]`(c) imposes is discharged by `.gitignore`, not by `rm`.

**This lane commits no second copy of the bundle.** D90's evidence set is already on `main` and the
two solves are numerically identical, so committing a duplicate would add ~1 MB and no information.
D90-R's bundle — including the 42 MB of `year_*.parquet` — therefore lives **only on this session
container's disk and will not survive the session.** That is the right trade *because* the
replication is recorded here in full; if the scored-key bundle is wanted as an artifact, say so
while the session is alive.

**On promotion.** The board now points at the re-score, which is the substantive promotion. What
remains open for the owner:

1. **Should the `results/ff-t3-neiso-golden/` designated golden directory move from `bau-d60` to the
   re-score?** The verdict record now names the re-score; the *bundle* layout still treats `bau-d60`
   as the golden. My reading: yes, and it is a rename rather than a re-solve — but it touches the
   corridor `model_source` chain, so it is a deliberate act, not a tidy-up.
2. **Is the −41.3-point corridor movement (§2.3) grounds to re-open the CCS retrofit wave's size or
   economics?** My reading: yes, and that is the single most useful thing the re-score surfaced.
   Rule 1 `[R-STRUCT]` keeps the repair in regardless; this is a root cause to route, not a reason to
   revert.

Reproduction cost if a scored-key bundle is later wanted: **one indivisible ~31 min NEISO 2026–2050
LP**, plus ~30 min of `data/clean` rebuild in a cold container.

## 6. BOUNDARIES HONOURED

* **No file under `src/market_sim/` was edited.** D91's `_CACHE_KEY_OPTIONAL_FIELDS` declarations and
  pin tests were left to D91, which had already landed them.
* `scripts/check_mechanism_matrix.py` is **EXIT 1 on `main`** over another desk's
  `vre_curtailment_oversupply_allocation` row — noted at the outset, not this lane's, stepped past.
* **Rule 28 `[R-MECH-MATRIX]` does not fire:** no mechanism was proposed, tested or added — this lane
  re-scored an existing run on already-merged code, changing no `ScenarioConfig` field.
* `regenerate_clean.py` reports **`[FAIL] lmp: exit 1`** (`KeyError: 'MGHG'` in `parse_caiso_file`, a
  CAISO raw-file defect that aborts the datatype). It **cannot reach this solve**: the clean `lmp`
  partition's only consumer is `data/neighbor_price.py` behind the `MARKET_SIM_USE_CLEAN` gate, which
  this lane does not set. Reported for its owner, not repaired here.
