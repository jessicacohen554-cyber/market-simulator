# RESULT — the merit-allocation arm CLEARS every screen gate, does NOT clear the 2021 objective, and promotion is BLOCKED on a pre-existing defect (ercot-259)

> Scored against `docs/PRECOMMIT-ercot259-drag-merit-allocation-2026-09-08.md`,
> pushed before either LP ran. Every gate, the screen year, the drift audit and
> all seven predictions were registered there, upstream of the arm.
> Bundles are **gitignored, not deleted** (rule 31 `[R-RETAIN]`) and live on
> local disk only — they will **not survive this session**.

## 0. Bottom line

| | |
|---|---|
| **Do the five STOP gates clear?** | **YES, all five.** §2 |
| **Does the mechanism do what its arithmetic says?** | **Yes, to 0.3–5 %.** Every plant's mandate delta reproduces the zero-LP prediction. §2 G2 |
| **Does it clear the D-4 conviction on plant 3452?** | **NO.** Improved 55 %, but the conviction stands. §3 |
| **What does it do to C8, the target?** | **WORSE**: ST_GAS forced share 13.47 % → 17.75 % in 2023 (both still PASS, cap 30 %). §3 |
| **Is it a keeper candidate?** | **My recommendation: NO** — but it is a genuine structural improvement, so the call is the owner's. §5 |
| **Can it be promoted at all right now?** | **NO — blocked**, and not by this mechanism. §4 |
| **Predictions** | 4 of 7 correct, **2 wrong**, 1 mis-specified by me. §6 |

---

## 1. What was solved

Two LPs at this HEAD, sequential (rule 12): a 2023 **control** and a 2023
**arm**, both replaying `results/calibration/ercot256_five_year_keeper`, the arm
adding `--netload-drag-merit-allocation` and nothing else. Screen year 2023 was
named ex ante in the PRECOMMIT on the mechanism's **own largest footprint**
(1.4270 TWh of mandated MW changing hands), never on the residual.

A control solve was spent rather than differencing the committed keeper
(G-CTRL form 4), because `main` advanced 57 commits after the drift audit and
the diff grew to 25 files including `model/lp/rows.py`. The one hunk that could
have moved this mechanism's merit order — SPP-49's unconditional simple-cycle
heat-rate floor, which clamps 4 ERCOT plants **including 3612 V H Braunig, the
head of the fill order** — was separately measured **INERT**: the ERCOT 2023
fleet built twice at HEAD, once with the floor no-op'd, is byte-identical across
every array the LP consumes.

---

## 2. THE GATES — all five clear

| gate | measured | verdict |
|---|---|---|
| **G1** aggregate neutrality survives the solve | mandate **7.0007 TWh** in both arms; **max hourly delta 0.0039 MW** (float32 rounding) against a 0.01 STOP | **PASS** |
| **G2** reallocation lands where the pre-solve delta says | **no sign flips, 11 of 11 plants**; the five largest movers reproduce to ratios **0.994 / 0.997 / 0.998 / 1.000 / 1.015** | **PASS** |
| **G3** footprint confined to the claimed rows | largest non-target mechanism move **0.026 TWh** (CC_CHP `chp_steam`) against a 0.05 STOP; `nuclear_mustrun` bit-identical | **PASS** |
| **G4** no non-target load-bearing PASS → FAIL | none; C3a −39.58 → **−39.36 %**, C3b 0.7300 → **0.7279** — both move the right way | **PASS (weak — see below)** |
| **G5** feasibility | slack **0.0000** and dump **0.0000** in both arms | **PASS** |

**G2 is the headline.** The mandate reallocation per plant, arm vs control,
against the zero-LP census registered in the PRECOMMIT:

| plant | HR | ctrl → arm (TWh) | delta | pre-solve | ratio |
|---|---|---|---|---|---|
| 3612 V H Braunig | 8.49 | 0.9064 → 1.7126 | **+0.8063** | +0.8080 | **0.998** |
| 3491 Handley | 12.58 | 0.9935 → 0.4894 | **−0.5040** | −0.5058 | **0.997** |
| 3452 Lake Hubbard | 11.45 | 0.6910 → 0.3306 | **−0.3605** | −0.3625 | **0.994** |
| 3460 Cedar Bayou | 10.71 | 1.1860 → 1.4969 | **+0.3109** | +0.3062 | **1.015** |
| 3628 R W Miller | 13.02 | 0.3229 → 0.1300 | **−0.1930** | −0.1930 | **1.000** |

**And the structural signature is large**: the same 7.0007 TWh of mandate now
sits on **53,681 floored plant-hours instead of 691,020** — a 92 % reduction —
across **47 rows instead of 132**. That is precisely the "lumpy commitment, not
a sub-min-load smear" repair the mechanism was built for.

**Why G4 is weak, stated rather than glossed.** Both arms replay the keeper's
**forward** config, which is the wrong recipe for 2023 (the keeper's 2023 is the
carve-out: `ercot_offer_swcap_clip=True`, CC_REGULAR `peak` **151.008** against
the forward **4.576**). So C3a reads **−39.6 %** and C3b **0.73** in *both*
arms — a base-recipe artifact, not the mechanism. The A/B is still clean (both
arms share the base, and the PRECOMMIT §4a registered this before the solve),
but G4 cannot detect a flip on criteria that were already failing. Only the
**delta** is meaningful, and it is small and favourable.

---

## 3. THE COST — the objective is NOT met, and C8 moves the wrong way

**Plant 3452's D-4 conduct conviction — the actual target — STANDS.**

| | control | arm |
|---|---|---|
| floored energy | 0.2523 TWh | **0.1145 TWh** (−55 %) |
| binding hours | 2,864 | **1,297** (−55 %) |
| measured median in binding hours | 0.000 MW | **0.000 MW** |
| measured zero-share | 0.5964 | **0.5513** |
| **verdict** | **FAIL** | **FAIL** |

The forcing on the convicted plant is more than halved, but the hours that
remain are still hours its meter reads zero in — the zero-share falls only
0.596 → 0.551, and the median stays 0.000. **Concentrating the mandate into the
plant's highest-net-load hours did not concentrate it into hours the plant was
actually running.**

**And C8, the target criterion, gets worse:**

| 2023 ST_GAS | control | arm |
|---|---|---|
| forced energy | 2.5623 TWh | **3.2684 TWh** |
| class energy | 19.0164 TWh | **18.4117 TWh** |
| **forced share** | **0.1347** | **0.1775** (cap 0.30, both PASS) |

Both terms move against the share. The mechanism is aggregate-neutral in
**mandate**, but not in **realized forcing**: flooring a cheap plant at its full
committed-tranche block is a far higher bar than 15 % of its `pmax`, so the floor
**binds** in hours where the smear did not. This is the direct refutation of
prediction P1, and it matters for the 2021 objective: 2021's C8 sits at **33.1 %
against a 30 % cap**, so a share that rises ~4 points in 2023 would very likely
push 2021 *further* past the cap while leaving 3452 convicted.

*(C8 was deliberately NOT a screen gate — reading the target criterion as a gate
is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids. It is reported
here at full magnitude, which is what the rule requires instead.)*

---

## 4. PROMOTION IS BLOCKED — by a pre-existing defect, not by this arm

Rule 16 `[R-ALLYEARS]` forbids a single-year keeper: promotion needs
`--year 2021 2022 2023 2024 2025` in one bundle, reproducing the keeper's
per-year recipes. **That is not reproducible at this HEAD.**

The keeper's 2021/2022/2023 legs need the carve-out — `ercot_offer_swcap_clip`
and the ×33.0 `offer_curve_by_group` peak bands — and:

* **no `meta.json` records either key** (the keeper's, `ercot236_k33_clip`'s,
  `ercot253_2021_touchpoint`'s and `ercot252_2022_touchpoint_repair`'s metas all
  read `swcap=None`, no `offer_curve_by_group`), so `--replay-bundle` cannot
  reproduce them — **demonstrated**: this session's control replayed the keeper
  and solved `swcap=False`, `peak=4.576`;
* **neither key has a CLI flag** in `run_calibration_full.py`;
* they entered those bundles from the ERCOT ISOConfig at an August sha and are
  not defaults at HEAD.

This is exactly the open item `RESULT-ercot256` §10 recorded and left unfixed —
*"the composite still records neither key, so anything replaying that bundle
still gets the forward config on 2023. The fix is a per-year recipe map in the
composite writer."* **It blocks any ERCOT full-span re-solve, by any lane, for
any mechanism** — it is not specific to this one, and it should be fixed before
the next ERCOT span is attempted.

---

## 5. DISPOSITION — my recommendation is NOT a keeper, and the call is the owner's

**Against promotion:** it does not achieve what it was built for (3452 stays
convicted), and it moves the target criterion the wrong way (C8 13.5 → 17.8 %),
which on 2021 — where C8 already fails at 33.1 % against a 30 % cap — is likely
to make a failing gate fail harder.

**For promotion, under the owner's stated bar** (*"if structural integrity
improves but gates regress that may still be a keeper"*): the structural case is
strong and measured. A floor that asserted every plant was committed at a
sub-minimum-stable-load fraction now commits whole plants at physical blocks;
forced plant-hours fall 92 %; the mandate moves onto V H Braunig, which the meter
says runs 95.4 % of 2023, and off the two plants the D-4 rider convicts; it
carries zero free parameters and is forward-native.

**I record the recommendation and take no action on it** (rule 31
`[R-RETAIN]`): nothing is deleted, and the promotion decision is the owner's.
**The two screen bundles are gitignored and on local disk only — this container
is ephemeral, so they will not survive the session.** Reproducing them costs
~30 minutes of LP; reproducing a full span additionally requires the §4 fix.

---

## 6. Prediction scorecard — hits and misses alike

| # | registered | measured | verdict |
|---|---|---|---|
| **P1** | 2023 ST_GAS C8 forced share **falls** | **rose 0.1347 → 0.1775** | **WRONG** |
| **P2** | 3452's D-4 row improves; clearing is open | improved 55 % (2,864 → 1,297 h) but **did not clear**; zero-share 0.596 → 0.551 | **half right** |
| **P3** | Braunig's forcing rises, D-4 stays `pass` | +0.8063 TWh of mandate, verdict `pass` | **CORRECT** |
| **P4** | 3491 and 3628 shed forcing | −0.5040 / −0.1930 TWh | **CORRECT** |
| **P5** | system LW LMP **falls**, < $1.00 | **rose +$0.1422/MWh** | **WRONG (direction)** |
| **P6** | ST_GAS class energy moves < 1.0 TWh | −0.605 TWh | **CORRECT** |
| **P7** | no PASS → FAIL on C1/C2/C3a/C3b/C4 | none | **CORRECT (weak, §2)** |

**P1 is the important miss and I had the reasoning backwards.** I predicted that
concentrating the mandate onto cheap units the LP commits anyway would make the
floor bind *less*. The opposite is true: the smear floored every plant *below*
the level it would dispatch at, so it rarely bound; the fill floors fewer plants
at a *much higher* per-plant level, so it binds more. The mandate is neutral;
the realized forcing is not. **P5 was wrong the same way** — the arm's forcing
binds harder, so it raises system cost slightly rather than lowering it.

**G2's magnitude leg was mis-specified by me.** The PRECOMMIT said per-plant
deltas should "match §3", but §3 tabulates the **mandate integral** while D-2
reports **realized forced dispatch** — different quantities. Evaluated on the
mandate integral, the apples-to-apples comparison, G2 passes at ratios
0.949–1.023; the sign leg passes on either.

---

*Generated by [Claude Code](https://claude.ai/code)*
