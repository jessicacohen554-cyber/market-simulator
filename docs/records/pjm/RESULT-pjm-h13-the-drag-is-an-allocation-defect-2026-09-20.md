# RESULT — pjm-h13: PJM's ST_GAS net-load drag is an ALLOCATION defect, and `netload_drag_merit_allocation` repairs it. D-4 drag failures 12 → 5, determination unchanged at CALIBRATED (2026-09-20)

**Session:** pjm-h13 · **Branch:** `claude/pjm-h13-mustrun-exclusions-0yud3j` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)) — six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)), all at
pinned SHA `ed3f5efdbcdd20a6317eb05add357f1909a736d6`.
**CHARTER:** `docs/handoffs/PRECOMMIT-pjm-h13-2026-09-20.md` + `ADDENDUM-…-presolve` +
`ADDENDUM2-…-g2-disambiguation`, all three pushed **before any arm result existed**.
**KEEPER UNCHANGED PENDING THE OWNER'S RULING:** `2026-09-19-pjm-h11-c1seam-span` still stands.
Nothing promoted, nothing pruned.

---

## 1. Verdict

**The mechanism works, four of five gates pass, and the fifth fails on MY OWN GATE'S SCOPING rather
than on the model.** Registered, scored, retained — **promotion is the owner's call** (rule 31
`[R-RETAIN]`, §8).

| gate | bar | result |
|---|---|---|
| **G1** — the arm fires | allocation differs every year | **PASS** |
| **G2** — rule 19 integrity | pre-solve mandate within ±1 % | **PASS — exactly 0.0000 TWh, all six years** |
| **G3** — RULE 17 IS SERVED | D-4 `st_netload_drag` FAIL rows do not increase in ANY year **and** the six-year total falls below 12 | **PASS — 12 → 5, no year increases** |
| **G4** — the NAMED plants | ≥1 of {3131, 3138} flips FAIL → pass in ≥3 of its failing years | **PASS on BOTH** — 3131 in 3 of 5, 3138 in 3 of 6 |
| **G5** — nothing stacked | no OTHER mechanism's D-2 share moves > 0.5 % | **FAIL — and the gate is wrong, not the model. §5** |

**Determination, composed and scored:** span 2023–2025 **`CALIBRATED`**, **all eight criteria PASS,
zero caveats**, determination basis *"all criteria pass, governance attested"* — the incumbent's
headline, held. Touchpoint 2020–2022 **`NOT-YET`** with C1/C3a/C3b FAIL and a ledgered C3c —
**criterion-for-criterion identical to the incumbent's touchpoint**, so rule 30
`[R-TOUCHPOINT-FOLD]` (c) is not even engaged.

## 2. The defect, and why it is a rule-17 finding rather than a residual observation

Read off the **incumbent keeper's own committed** `legitimacy_diagnostics.json`, never off a price
or volume residual. PJM's ST_GAS drag mandate is spread pro-rata across every non-peak tranche,
asserting one fleet capacity factor on every plant in every hour. Over an **8.95 GW** ST_GAS fleet:

- It floors **exactly four plants** (per-plant rows sum to the mechanism total: 2024
  0.1279 + 0.1867 + 0.1097 + 0.3930 = 0.8173 vs the window row's 0.8352).
- **3131 Shawville** (596 MW) and **3138 New Castle** (326 MW) carry a measured median of **exactly
  0.000 MW** over the hours the floor says they must be online. Rule 17 `[R-FLOOR-WINDOW]`: *a bug
  by definition.*
- **3148 Martins Creek (1700 MW)** and **3149 Montour (1504 MW)** — the population's two **largest**
  plants, ST_GAS in the model fleet, genuinely part-time (online 0.382 / 0.456) — carry **no drag
  floor at all**, and appear in **no D-4 skip list**, so this is absence of floor, not absence of meter.

0.92 GW floored where the meter reads zero, 3.2 GW unfloored. **The error runs both ways** — an
**allocation** defect, ercot-259's object, which pjm-177 measured from the hour axis and recorded
as *"a real second defect … recorded not taken."*

## 3. The six-year result (composed vs composed)

| year | D-4 drag FAIL ctl → arm | all-mechanism D-4 FAIL ctl → arm | `cc_mustrun` ctl → arm |
|---|---|---|---|
| 2020 | 3 → **1** | 5 → **3** | 2 → 2 |
| 2021 | 2 → 2 | 7 → 7 | 5 → 5 |
| 2022 | 2 → **1** | 7 → **6** | 5 → 5 |
| 2023 | 1 → **0** | 6 → **5** | 5 → 5 |
| 2024 | 2 → **0** | 10 → **8** | 8 → 8 |
| 2025 | 2 → **1** | 10 → **9** | 8 → 8 |
| **total** | **12 → 5** | **45 → 38** | **33 → 33** |

**`cc_mustrun_per_plant` is unchanged in every single year** — nothing is traded away to buy the
drag's repair.

**The cleanest single statement of what the mechanism does.** Across **24 of 24** per-plant-year
rows, the share of floored hours in which the plant's own meter reads **zero FALLS**; the measured
median over those hours **RISES in 19** and **never falls**. The floor moves into hours the plants
are actually running. Examples: 3131 2022 median 0.000 → 170.733 (zero-share 0.667 → 0.352);
3138 2025 0.000 → 92.170 (0.597 → 0.423); 3140 2020 0.000 → 145.417 (0.574 → 0.462).

**Class energy moves are small**: max |Δ class TWh| per year **0.69–0.96**, the largest being
CT_PEAKER −0.70 to −0.96 every year, CC_REGULAR +0.01 to +0.36, COAL_BIT +0.05 to +0.33.

## 4. T1 tripwire TRIPPED, explained mechanically rather than waved through

D-2 delivered forced energy rises: `st_netload_drag` **+12.0 % to +111.5 %**, `ct_netload_drag`
**+21.9 % to +44.3 %** — outside ADDENDUM 2's ±15 % band in five of six years, so T1's explanation
duty is owed and is discharged here.

**The mandate is provably unchanged** (0.0000 TWh pre-solve, all six years), so this is not a level
change. Pro-rata smears the mandate thinly across plants at a level **below any boiler's minimum
stable load**, where much of it never binds; merit fill concentrates the **same MW** into physically
meaningful commitment blocks, which do bind. **Measured, the extra forced energy lands on plants
D-4 scores as metered ON: 14 of 17 gaining plant-years PASS D-4 on the arm side**, the gainers'
median arm-side measured output is 145.4 MW, and the three failing gainers are all 3138 (§6).
Forcing rises because the floor now lands where it actually constrains — and the plants it
constrains are, by D-4's own test, running.

## 5. G5 FAILS — and it is a charter-scoping error by this lane, disclosed, not amended

`ct_netload_drag`'s D-2 forced share moves **+0.0697 / +0.0725 / +0.0817 / +0.0307 / +0.0410 /
+0.0472** against a 0.005 bar. **Why:** `netload_drag_merit_allocation` is read by **both** drag
appliers — `data/fleet/floors.py:570` (ST_GAS) and **`:646` (CT_PEAKER)** — because it is registered
as *"the ALLOCATION sub-gate inside this same family"*, and the family has two mechanism ids. I
wrote G5 to scope "other mechanism" by **D-2 id** when I should have scoped it by **family**. The
documentation I had already read says so; the error is mine.

**I did not amend G5.** I amended G2 once, before any result existed, and said in that commit that
it could only loosen the gate. Amending a second gate *after* numbers are on the table is exactly
the gate-softening the charter exists to prevent, so **G5 stands as FAILED**.

**What G5 was actually trying to measure — that nothing outside the tested mechanism moved — passes
comfortably: outside the drag family the largest D-2 share move in any year is 0.0007.**

## 6. Reported at full magnitude, not buried

- **3138 New Castle is the mechanism's named residual defect.** It still FAILS D-4 in 2020, 2021 and
  2022, and it *gains* floor energy (+0.19 to +0.36 TWh). The cause is the weakness the mechanism
  was **registered with**: heat rate is an imperfect proxy for commitment order, so a plant cheap on
  paper and idle in fact is filled early. Its zero-share still falls in all three years
  (0.660 → 0.532, 0.706 → 0.619, 0.696 → 0.538) — better, not fixed.
- **3131 Shawville still FAILS in 2021 and 2025.**
- **My own ex-ante prediction was WRONG, and in the mechanism's favour.** ADDENDUM 1 said 3138
  "will very likely not" flip. It flipped in 3 of 6 years. The pre-solve floor array does not
  predict D-4, exactly as PRECOMMIT §2.1(a) warned — I flagged the limit and then mis-predicted
  through it anyway.
- **Martins Creek and Montour are still unfloored.** Merit fill cannot reach them (no commitment
  tranches), so half the two-way error stands. Predicted in PRECOMMIT §2.1(b).
- **The defect is invisible to every gate.** PJM ST_GAS is 1.4–1.8 % of load, so C8 skips it on
  materiality — even in 2021, where the drag forces **30.8 %** of the class, above rule 20's budget.
  Only D-4 catches it. This card can therefore only be judged on rules 17/1, never on a band.

## 7. Method notes that a successor should not have to rediscover

- **NO CONTROL SOLVES — six shards, not twelve.** G-DRIFT over `65ab6205..HEAD` classified every
  hunk INERT for PJM (constants.py = NWPP rows; scenarios.py = **zero executable lines**; hubs.py =
  one hunk inside the `caiso_citygate_blackout_bridge` branch, flag absent on both PJM bundles), so
  form 4 held. pjm-h12's correction #1 was right.
- **PER-YEAR LEG DIAGNOSTICS ARE NOT COMPARABLE TO A COMPOSED SPAN — this nearly produced a wrong
  verdict.** D-4's `ct_only` vintage guard borrows flags across **sibling years in the bundle**. The
  control span's 2021 extended flags to **11** plants; a single-year leg extended to **8**. The
  three it could not extend include 2393 and 7153, which then read as *new* `cc_mustrun` failures
  the mechanism did not cause. On the composite they vanish and `cc_mustrun` is unchanged. **Always
  compose, regenerate `legitimacy_diagnostics.json` over the composite, and compare like with like.**
- The lay-up census this lane built (`campd_bridge_layup_exclusions_PJM.csv`) is committed and
  unblocks `mustrun_plant_exclusions` and `mustrun_layup_window_mask` for any successor.

## 8. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — the owner's call, and the bundles do not survive this session

**This lane's recommendation: PROMOTE, on the structural merits — with G5's failure disclosed above
rather than argued away.** The case is rule 1 `[R-STRUCT]` and rule 17: it repairs a real
floor-window defect (12 → 5 D-4 failures, 24/24 zero-share improvement), costs **zero free
parameters**, is **exactly aggregate-neutral**, trades nothing away (`cc_mustrun` unchanged), holds
the determination at **CALIBRATED with zero caveats**, and is **forward-native** so the repair
carries into the forecast. I am not claiming a clean sweep: G5 failed as I wrote it, and 3138
remains unrepaired in three years.

**What promotion would take:** re-key `frontend/data/backcast/keepers/PJM.json` to
`2026-09-20-pjm-h13-meritalloc-span`, stamp the touchpoint to it (rule 30(a)), rebuild
`status/PJM.js`, re-key `calibration-complete.json`, then `audit_keepers --iso PJM` and only then
prune the outgoing keeper (rule 35 `[R-PROMOTE]` (e), order: promote → verify → delete). PJM's year
union is **{2020, 2021, 2022, 2023, 2024, 2025}** and the incoming pair covers it exactly (35(b)/(c)).

**Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e)), stated honestly.** Both composites are
**registered and committed on this branch**, so they reach `main` when this PR merges — that is the
durable copy. The six per-year legs are gitignored on the parent's disk and their shard branches are
**transport, not storage** (rule 33(f)(1)): those refs are cut when this PR merges, so **any leg not
landed on `main` costs a re-solve (~13 min/year), not a checkout.** The composites are what matter
and they are safe.

