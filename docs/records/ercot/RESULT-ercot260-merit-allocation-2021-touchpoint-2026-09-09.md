# RESULT — the 2021 touchpoint moves the failing gate the RIGHT way but does NOT close it, and my own P1 was wrong in direction (ercot-260, card 2)

> Scored against `docs/PRECOMMIT-ercot260-merit-allocation-2021-touchpoint-2026-09-09.md`,
> pushed before the LP ran. Every gate, the control basis, the drift evidence,
> the decision rule and all five predictions were registered there, upstream of
> the solve.

## 0. Bottom line

| | |
|---|---|
| **Decision variable — 2021 C8 ST_GAS forced share** | **0.3313 → 0.3204** (−0.0109). **BETTER**, and still **FAIL** (cap 0.30). |
| **Which branch of the registered decision rule?** | The **middle** one: *"falls but stays ≥ 0.30 ⇒ partial … report and put to the owner, no recommendation either way."* §5 |
| **Does it clear the D-4 conviction on 3452?** | **NO.** Forcing −61 % / hours −72 %, but the measured median stays 0.000 MW. **D-4 FAIL rows 20 → 20 — not one cleared.** §3 |
| **Do the gates clear?** | **G-A PASS, G-B PASS, G-C not measurable.** §4 |
| **Predictions** | **4 of 5 correct. P1 — my headline call — was WRONG IN DIRECTION.** §6 |
| **The finding that matters** | **2021 and 2023 move OPPOSITE ways.** 2023: +4.3 pt (worse). 2021: −1.1 pt (better). §7 |

---

## 1. What was solved — one LP, and it is the first honest measurement

The keeper `ercot256_five_year_keeper` replayed on `--year 2021` — its **carve-out**
recipe — plus `--netload-drag-merit-allocation` and nothing else. Verified from
the arm's own `run_config.json`:

```
netload_drag_merit_allocation = True     <- the arm
ercot_offer_swcap_clip        = True     <- the carve-out
CC_REGULAR.peak               = 151.008  <- the carve-out
ercot_zonal_spread_ep_referenced = True  <- 2021's own value
```

**This is the first time this mechanism has been measured on 2021 at all, and
the first ERCOT carve-out replay that solved the right config.** ercot-259 could
only *predict* 2021 from 2023 — and predicted the 2023 C8 direction wrong. Card 1
of this session is what made the solve possible.

Rule 22 authorization: ERCOT holds `complete`; the freeze scope is
`tiers: ["locked_test"]`, so the validation tier is not frozen. The CLI emitted
the rule-22 warning and the run carries `--holdout-authorized`. **Nothing was
identified, fitted or tuned on 2021.**

**Control: the keeper's COMMITTED 2021 leg** (G-CTRL form 4, no control solve —
rule 29(b)). G-DRIFT was **measured, not audited**: card 1's proof replayed the
keeper at HEAD and reproduced its committed 2023 leg **bit-identically**.

---

## 2. THE DECISION VARIABLE

| 2021 ST_GAS | control (keeper) | arm |
|---|---|---|
| forced energy | 3.4905 TWh | **3.3536 TWh** |
| **forced share** | **0.3313** | **0.3204** |
| verdict (cap 0.30) | **FAIL** | **FAIL** |

The gate moves **−0.0109 toward the cap and stops 0.0204 short of it.** It is
about **35 % of the way** from the control to a pass.

---

## 3. THE OBJECTIVE IS STILL NOT MET

**Plant 3452 (Lake Hubbard), the convicted plant, on the year its conviction is
worst:**

| | control | arm |
|---|---|---|
| floored energy | 0.2891 TWh | **0.1133 TWh** (−61 %) |
| binding hours | 2,614 | **724** (−72 %) |
| measured median in binding hours | 0.000 MW | **0.000 MW** |
| **verdict** | **FAIL** | **FAIL** |

The same result ercot-259 got on 2023, harder: the forcing is cut by nearly
three quarters, and every hour that remains is still an hour the plant's meter
reads zero in. **Across the whole fleet, D-4 FAIL rows are 20 before and 20
after — not one conviction cleared.**

**Where the mandate went** (the mechanism working exactly as designed — off the
least-committed plants, onto the workhorses):

| plant | floored TWh, control → arm | binding hours |
|---|---|---|
| 3491 Handley | 0.6709 → **0.2181** | 4,707 → 1,299 |
| 3628 | 0.1967 → **0.0275** | 3,434 → 595 |
| 3452 Lake Hubbard | 0.2891 → **0.1133** | 2,614 → 724 |
| 3612 V H Braunig | 0.2891 → **0.6005** | 3,190 → 3,208 |
| 3460 Cedar Bayou | 0.4309 → **0.8219** | 3,196 → 2,870 |
| 6243 | 0.0841 → **0.2255** | 4,865 → 4,794 |

Aggregate: total D-4 floored energy **25.2599 → 25.0969 TWh (−0.65 %)** while
total binding plant-hours fall **77,750 → 65,256 (−16.1 %)** — the same mandate
carried by fewer, larger, physically-meaningful blocks, which is the mechanism's
whole claim.

---

## 4. THE GATES

| gate | measured | verdict |
|---|---|---|
| **G-A feasibility** | arm slack **1,763.9569 MWh over 5 hours** — **identical to the control**, to 0.0000 MWh; dump 0.0000 both | **PASS** (see below) |
| **G-B footprint confinement** | largest non-target class move **0.0278 TWh** (CC_REGULAR, on 109.8 TWh) against a 0.15 STOP; **44 of 60 plants byte-identical**, and every plant that moved is drag-owned | **PASS** |
| **G-C mandate neutrality** | **NOT MEASURABLE** — see below | **not scored** |

**G-A: I mis-specified my own gate.** The PRECOMMIT wrote it as an absolute
(*"either > 0.0000 TWh ⇒ STOP"*), which is wrong for **2021 — the Uri year**,
where the keeper itself carries 1,763.96 MWh of load shed across 5 hours as a
*real* event. On the absolute form the arm reads STOP; on the differencing form
the gate was actually asking about — arm-induced infeasibility — the delta is
**exactly 0.0000 MWh** and it passes cleanly. I am recording the mis-specification
rather than quietly restating the gate.

**G-C could not be measured and I am not substituting something easier for it.**
It needed the *control's* per-row floor mandate, and the keeper bundle carries no
`floors/` sidecar; reconstructing one from a copy of the bundle produced no rows.
What stands in its place is weaker and stated as such: aggregate neutrality was
verified on **2023** to a max hourly delta of **0.0039 MW** against a 0.01 STOP,
the property is structural (the applier targets the pro-rata path's own delivered
MW hour by hour), and the 2021 plant table above is independent evidence the
footprint is confined — 44 of 60 plants byte-identical.

**Reported, not gated** (C8 is the target; gating on it is the fitted-mechanism
selection rule 1 `[R-STRUCT]` forbids):

| | control | arm |
|---|---|---|
| system LW mean LMP | 187.292 | **187.359** (+$0.0675/MWh) |
| C3a vs actual 148.19 | +26.39 % (**FAIL**) | +26.43 % (**FAIL**, unchanged verdict) |
| ST_GAS class energy | 10.5359 TWh | **10.4657 TWh** (−0.0702) |

No class moved anywhere near enough to flip C1 or C2; C3a already failed in the
keeper and still does.

---

## 5. THE REGISTERED DECISION RULE, APPLIED

The PRECOMMIT registered three branches. The measured outcome —
**falls, but stays ≥ 0.30** — is the middle one, verbatim:

> *"falls but stays ≥ 0.30 ⇒ **partial**: the breach is not closed but the
> direction is right ⇒ report and put to the owner, no recommendation either
> way."*

**So I make no recommendation, by prior commitment.** §7 sets out both sides.

---

## 6. PREDICTION SCORECARD

| # | registered | measured | verdict |
|---|---|---|---|
| **P1** | 2021 C8 share **RISES** from 0.3313, stays FAIL | **FELL** to 0.3204; stays FAIL | **WRONG on direction** (right on the FAIL) |
| **P2** | 3452 forcing/hours fall ≥ 40 %; conviction does **not** clear | −61 % / −72 %; median 0.000 MW; **FAIL** | **CORRECT** |
| **P3** | system LW LMP rises, < $2.00/MWh | **+$0.0675/MWh** | **CORRECT** |
| **P4** | ST_GAS class energy falls, < 1.5 TWh | **−0.0702 TWh** | **CORRECT** |
| **P5** | no non-target load-bearing PASS → FAIL | none | **CORRECT** |

**P1 was the headline call and it was wrong.** I extrapolated 2023's +4.3 pt to
2021 and stated ex ante that the arm was *expected* to make the 2021 gate worse,
which under §5 would have meant recommending against. The opposite happened. The
registered ex-ante statement is why that is legible as a miss rather than
something I can now re-frame.

---

## 7. THE FINDING — the two years move in OPPOSITE directions

| year | tier | C8 ST_GAS forced share, control → arm | direction |
|---|---|---|---|
| **2023** | **train** | 0.1340 → **0.1775** | **worse, +4.3 pt** |
| **2021** | **validation** | 0.3313 → **0.3204** | **better, −1.1 pt** |

This is not noise and it is consistent with the mechanism's own theory. The
uniform allocation's error is largest where the fleet is **least committed** —
2021 is the year the uniform floor holds Lake Hubbard at 1.22 TWh against
0.36 TWh measured (3.4× over) while holding V H Braunig at 1.50 against 3.72
(0.40× under). Replacing the smear with cheapest-first commitment blocks
*relieves* that year. Where the fleet is more committed (2023), flooring a cheap
plant at its full block is a **higher** bar than 15 % of `pmax`, so the floor
binds more and the share rises.

**What this means for a promotion decision — both sides, and they are genuinely
in tension:**

**For.** The structural case is strong and now measured on the year that
actually fails. The defect it repairs is real: a *fleet* capacity factor asserted
as every plant's per-hour commitment, at a level below any boiler's minimum
stable load. It carries **zero free parameters**, is forward-native, moves the
failing gate the right way, cuts the wrong-plant forcing by 61–72 %, and leaves
44 of 60 plants untouched. Rule 1 `[R-STRUCT]` is explicit that a
structurally-correct mechanism stays in **even if the residual doesn't move**,
and is never rejected because the fit got worse.

**Against.** It does not close the breach, it clears **no** D-4 conviction, and
the improvement is in the **validation** tier while the regression is in the
**training** tier. Rule 22 `[R-HOLDOUT]` is emphatic that a validation number is
iterable model-**selection** evidence and never a skill claim; promoting a
mechanism *because* it improves 2021 while degrading 2023 is uncomfortably close
to selecting on the held-out year, which is the one thing the touchpoint loop
exists to prevent. Under rule 30(c) the 2021 rung cannot decertify ERCOT either
way — the ISO's determination is its 2023–2025 train-tier verdict.

---

## 8. Provenance

* One LP: the 2021 arm. No control solve (rule 29(b)).
* **Nothing was registered.** Both probe bundles live outside
  `results/calibration/` and are excluded via `.git/info/exclude`, so the parity
  gate's `iterdir()` sweep cannot see them and they cannot reach `main`
  (rule 29 clause c / rule 31 `[R-RETAIN]`).
* **The keeper is unchanged and untouched** — `git status` on its directory is
  clean; the control diagnostics were run on a copy.
* No keeper, determination, dashboard entry or scored number moved.

---

*Generated by [Claude Code](https://claude.ai/code)*
