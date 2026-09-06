# FINDING neiso-104 — the offer-level screen KILLED the arm on its own gate; the sizing model is refuted, the mechanism is not

**Session.** neiso-104, NEISO lane. Branch `claude/neiso-2020-lmp-miss-gr899x`. 2026-09-06.
**DATA PROFILE: neiso.** Pre-registration:
`PREREG-neiso104-fossil-offer-level-2026-09-06.md`; drift audit:
`ADDENDUM-neiso104-gdrift-2026-09-06.md`.

**LP spent: 2 single-year solves (2025 arm + 2025 control). The full span was NOT spent.**
Nothing registered on the dashboard (rule 29(2): a screen bundle is never registered). No keeper
change, no `ScenarioConfig` default moved, no holdout year touched. Both bundles are **deleted
before merge** (rule 29(c)); every number below is the record.

---

## 0. Headline

**The screen STOPPED the arm on gate G1, and the stop is reported as the session's result exactly
as rule 29 `[R-SCREEN]` requires.** The declared 4.53 % cut delivered a **−2.38 %** price move
against a pre-registered **−3.47 %**, missing the ±1.0 pp tolerance by **0.09 pp**.

**What is refuted is the SIZING MODEL, not the mechanism.** G2 and G3 both PASS: the response is
confined to the four scoped groups, and exactly the 12 declared bands moved with every `phys_*`,
`peak`, `econ_low_share` and `pct_peaking` bit-identical. The band multipliers do precisely what
they claim. What was wrong is §3.2's identification of how much price a given cut buys.

**Realized pass-through 0.525**, against the declared 0.765. That is **below** even the
within-year elasticity (0.593) this lane explicitly argued against, and it trips PREREG §7's
pre-committed trigger verbatim: *"If the screen shows delivered pass-through materially below 0.6,
the §3.2 identification is wrong … the honest move is to **stop and re-derive**, not to raise the
scalar."* **The scalar is not being raised.** Back-solving 4.53 % × 0.765/0.525 ≈ 6.6 % from this
screen is the sweep condition (c) forbids, and it is not done here or proposed.

**Second result, independent of the arm and arguably worth more: NEISO's keeper is NOT stale.**
The same-HEAD control reproduces the committed keeper **bit-identically** — $71.3866/MWh against
$71.3866/MWh, and **0.0000 TWh** summed absolute class-energy difference — despite 111
live-candidate files and 28,119 changed lines on the NEISO backcast path.

---

## 1. The gates, as pre-registered

| gate | pre-registered test | measured | verdict |
|---|---|---|---|
| **G1 direction + magnitude** | move negative, within ±1.0 pp of −3.47 % | **−2.38 %** (off by **1.09 pp**) | **STOP** |
| G2 footprint confinement | response confined to the 4 scoped groups; must-run/free classes unmoved | largest out-of-scope move **0.0050 TWh** (CT_CHP); nuclear/wind/solar/hydro/interchange **0.0000** | PASS |
| G3 identity | exactly 12 bands move; `phys_*`, `peak`, shares, `pct_peaking` bit-identical | **12** moved, all four `peak` bands and every `phys_*` unchanged | PASS |
| G4 non-target load-bearing flip (C1/C2/C3b) | not PASS → FAIL | **NOT EVALUABLE** — see §4 | — |

G1 alone is dispositive; the screen is a STOP gate and one stop kills the arm.

### 1.1 G2 detail (TWh, arm − control, 2025)

| class | Δ TWh | in scope? |
|---|---:|---|
| CC_REGULAR | +0.0398 | yes |
| CC_CHP | −0.0275 | yes |
| ST_GAS | −0.0060 | yes |
| CT_PEAKER | +0.0037 | yes |
| CT_CHP | −0.0050 | no — but CT_CHP is a *declared-neutral* group the scalar deliberately did not touch (PREREG §2.1 (iii)); this is second-order re-dispatch, not a direct reprice |
| oil | +0.0015 | no — second-order |
| COAL_BIT | −0.0009 | no — second-order |
| ST_CHP | −0.0003 | no — second-order |

Every out-of-scope move is ≤ 0.005 TWh against ~114 TWh of annual NEISO load — 4 parts in
100,000. The mechanism's footprint is where it says it is.

## 2. What the screen measured about pass-through

| basis | elasticity | status after the screen |
|---|---:|---|
| across-year, all 5 solved years (**declared** in PREREG §3.2) | 0.765 | **REFUTED** — over-predicts by 46 % |
| across-year, in-sample 3 years | 0.742 | refuted with it |
| within-year pooled, in-sample (argued *against* in §3.2) | 0.593 | closer, still high |
| **realized, measured directly by this screen** | **0.525** | the number |

The §3.2 argument — that a multiplier change is a *level shift of the whole fossil cost surface*
and therefore best measured by the across-year gas contrast — is wrong in the direction that
matters. The plausible reason, stated as a hypothesis and **not** acted on: an across-year gas
move carries the *whole* delivered fuel surface including the four physically-pinned `peak` bands
and the non-scaled VOM, whereas the declared scalar deliberately excludes the `peak` bands
(PREREG §2.1) and cannot move VOM at all — so the arm reprices strictly less of the stack than a
gas move of the same proportion. **That is a hypothesis this screen does not test**, and any
re-derivation owes its own identification rather than adopting it.

## 3. Where the years land, and what it means for 2020

Re-projected on the **measured** −2.38 % rather than the predicted −3.47 %:

| year | tier | now | PREREG predicted | on measured move | C3a |
|---|---|---:|---:|---:|---|
| **2020** | validation | +13.71 % | +9.76 % | **+11.00 %** | **FAIL** |
| 2021 | validation | +9.08 % | +5.29 % | +6.49 % | PASS |
| 2022 | validation | −0.60 % | −4.05 % | −2.97 % | PASS |
| 2023 | train | +3.13 % | −0.45 % | +0.68 % | PASS |
| 2024 | train | +5.66 % | +2.00 % | +3.15 % | PASS |
| 2025 | train | +1.65 % | −1.88 % | **−0.77 %** (solved, not projected) | PASS |

2025 is the only *solved* row; the rest are projections at the measured proportional move and are
labelled as such. **The arm as declared does not close 2020** — it lands at +11.00 %, still
outside the ±10 % band. PREREG §3.3 pre-registered 2020's verdict as **undetermined** at the
declared value, and the screen resolves it to the failing side. That is the pre-registration
working, not a surprise to be engineered around.

**Rule 30(c) `[R-TOUCHPOINT-FOLD]` is untouched and governs**: NEISO's determination is its
train-tier verdict, still **CALIBRATED**, and 2020 neither certifies nor decertifies it.

## 4. Two rule-mechanics collisions found, filed and not worked around

**(a) G4 is not evaluable on a screen bundle.** `scripts/calibration_verdict.py` resolves only a
**registered** run ("could not resolve a registered run … no registry sidecar and no bundle
match"), and rule 29(2) forbids registering a screen bundle. So a screen gate written as "no
non-target load-bearing criterion flips PASS → FAIL" — which is rule 29's own language for the
fourth structural gate — cannot be scored by the repo's scorer on the artifact the rule permits
to exist. This lane did **not** register the bundle to get a score, and did **not** hand-roll a
substitute verdict. What can be said from measured deltas alone: the largest class-energy move is
0.0398 TWh against ~114 TWh, so a C1/C2 flip is not physically reachable; C3b is unquantified.

**(b) G-DRIFT's path triage over-flags, and the control proved it.** The addendum classified 111
files / 28,119 lines as live candidates and, unable to hand-classify them, took the stricter
branch and spent a control. **The control then reproduced the committed keeper bit-identically**,
which means every one of those hunks was in fact INERT for NEISO's backcast and **G-CTRL form 4
would have been valid** — the keeper's committed bundle *was* the control all along, and the
control solve was unnecessary in hindsight.

Recorded honestly rather than as a win: **spending it was the right call ex ante** (a path-name
heuristic is not a hunk audit, and `data/offer_curves.py` — the mechanism's own consumption path
— had genuinely moved 391 lines), and it bought a stronger statement than the audit could have.
But it is evidence that **rule 29(b)'s cost premise degrades with keeper age in a way the rule
does not anticipate**: at three weeks' staleness the audit is not "seconds", and the fallback it
names is the very solve it exists to avoid. **A cheap empirical form-4 validity check — replay one
year of the keeper recipe and compare to its committed numbers — answers the question the audit
asks, at one solve, with no classification at all.** Offered as an observation for the owner; this
lane proposes no rule change.

## 5. What is NOT concluded

- **Not a refutation of the channel.** `offer_curve_by_group` remains cell **K** for NEISO. G2/G3
  show the bands behave exactly as specified. Nothing here adjudicates the mechanism `R`.
- **Not a re-sized arm.** No successor scalar is proposed, and the screen's own coefficient is
  deliberately **not** back-solved into one (PREREG §7; rule 1 condition (c)).
- **Not a 2020 conclusion.** 2020 was never this lane's object (PREREG §0); it remains what
  neiso-103 found — a readout of an in-sample bias magnified by the smallest denominator in the
  record.
- **Not a keeper change.** NEISO's keeper is `2026-08-17-neiso-99-joint-p1`, unchanged, and now
  additionally shown to reproduce at HEAD.

## 6. The open question this leaves for the owner

The in-sample bias (+3.47 %) is real and unaddressed. Closing it through this channel needs a
pass-through coefficient, and the only trustworthy measurement of one now in existence **came from
this screen**. That creates a genuine governance question this lane will not answer for itself:

> Is re-deriving the cut from the screen's **measured physical response coefficient**
> (dPrice/dMultiplier = 0.525) legitimate identification — the target having been declared ex ante
> and never moved — or is it the first iteration of a sweep toward the band?

It is arguably the former: the *target* (in-sample geometric-mean bias) was fixed before any
solve and does not move, and a measured response coefficient is not a criterion outcome. It is
arguably the latter: the coefficient was obtained by solving an arm and reading how far the price
went, which is one step of exactly the loop condition (c) exists to stop. **Both readings are
defensible and the difference is not mine to settle.** Until it is settled, the honest position is
the one PREREG §7 pre-committed to: stopped, re-derivation not attempted.

## 7. Session ledger

- **LP: 2 single-year solves** (2025 arm, 2025 control), run concurrently per rule 12.
- **Bundles `neiso104_arm_2025` and `neiso104_ctrl_2025` DELETED before merge** (rule 29(c)).
- **No dashboard registration** (rule 29(2)); no prune triggered.
- **Mechanism matrix**: `offer_curve_by_group` NEISO cell stays **K**; evidence citation appended
  for the screen outcome (rule 32(b) — a tested mechanism is stamped even when the arm dies).
- **Holdout tiers untouched**: 2025 is train tier; no validation or locked-test year was solved,
  scored or registered. The locked-test freeze is untouched.
- **Keeper unchanged**; `frontend/data/backcast/keepers/NEISO.json` and
  `calibration-complete.json` not edited.

**Next shorthand: `neiso-105`** — and it has no mandate until §6 is answered.
