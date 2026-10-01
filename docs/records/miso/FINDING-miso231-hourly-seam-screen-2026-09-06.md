# FINDING miso-231 — the HOURLY seam ladder **CLEARS ITS STRUCTURAL GATES AND IS KILLED ON G-1 BY 0.018**. Full span NOT spent. Owner decision requested.

Session miso-231, 2026-09-06, branch `claude/miso-backcast-calibration-a5oogr`.
Pre-registration pushed **before** the screen solve
(`PRECOMMIT-miso231-hourly-seam-ladder-2026-09-06.md`, commit `14ae4d76`); its
two gate corrections and the blind scorer pushed **while the LP was running and
before the arm's bundle was opened** (Addendum A, commit `99091ff5`,
`scripts/probes/_miso231_screen_gates.py`); the G-DRIFT re-audit over main's
later commits pushed with it (Addendum B).

**KEEPER UNCHANGED: `2026-09-06-miso-230-ctdrag-seam`.** Rule 22: 2023–2025.
DOF ledger 41/2. **Nothing is promoted and the remaining years are not spent.**

---

## 0. Verdict

**SCREEN VERDICT: KILLED**, on the pre-registered G-1 responsiveness bar,
**by 0.0183**.

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-1 responsiveness** | `corr(imports, own model hub price)` falls **≥ 0.30** from the keeper's own 2024 **+0.4461** | **+0.4461 → +0.1644, fall 0.2817** | **FAIL** |
| G-3 confinement | no slack increase beyond the keeper's pre-existing 0.0196 TWh; dump 0.0000 | slack **0.0196 → 0.0196**, dump **0.0000 → 0.0000** | **PASS** |
| G-5 cheap-hour direction | solved imports RISE in the frozen G-2 hour set (n = 2,111) | **2,129.3 → 3,321.6 MW, +1,192.3** | **PASS** |
| G-2 volume | — | **WITHDRAWN** before the result (Addendum A.2) | n/a |
| G-4 no collateral flip | — | **NOT SCORABLE** (§3) | n/a |

**The gate is a STOP gate and it is not renegotiated.** I set the 0.30 bar
myself, in Addendum A, before any arm number existed; the arm missed it. Rule 29
`[R-SCREEN]`: *"A screen that kills an arm is reported as the session's result
and the remaining years are never spent."* They are not spent.

**But the miss is 6 % of a bar I chose, and on the mechanism's own published
comparator basis the arm essentially lands on the measured value.** That is
§2, and it is why this goes to the owner rather than to `R`.

## 1. What the mechanism actually did

**On the miso-225/226 published basis — deciles and correlation of the
MEASURED MISO-Indiana hub price, the basis every prior seam comparator on
record uses — the arm reproduces the measured seam's price response:**

| statistic, 2024 | keeper | **arm** | **MEASURED** |
|---|---:|---:|---:|
| corr(imports, measured hub price) | +0.3211 | **−0.0636** | **−0.039** |
| price-decile slope d1−d10 | −3,321.6 MW | **+111.2 MW** | **+1,384 MW** |
| corr(imports, own model price) | +0.4461 | +0.1644 | (−0.101, 2023 ref) |

- The correlation on the measured basis **crosses zero and lands on the measured
  value**, marginally past it (−0.064 vs −0.039).
- **The decile slope changes SIGN**, −3,321.6 → **+111.2 MW**. No arm on record
  has done that: miso-226's annual form moved −3,573 → −3,217, closing 10 % of
  the sign error. This closes **100 %** of the sign and reaches 8 % of the
  measured magnitude.
- Cheap-hour imports **+1,192 MW** against a bar of ≥ +150, and against the
  annual form's +581.

**Phase 0 predicted this and the LP delivered it.** The zero-LP readout A —
measured record only, no model output — put the hourly form at corr +0.271
against the measured flow where both fixed ladders read **negative**
(−0.253 / −0.262). The solved arm converts that into a sign flip on the solved
slope. The conversion is the honest surprise of this screen: the mechanism did
**more** than the static instrument predicted, not less.

## 2. Why G-1 nonetheless reads FAIL, stated against my own interest

G-1 is written on the **own-model-price** basis, which Addendum A.1 chose and
declared, with the measured basis explicitly *"reported beside it, not gated"*.
On that basis the fall is 0.2817 against a required 0.30.

Two things are true at once and both belong in the record:

1. **The bar was mine and it is not a physical constant.** 0.30 came from the
   PRECOMMIT's original magnitude, re-anchored in Addendum A. Nothing external
   fixes it at 0.30 rather than 0.28.
2. **That is exactly why it must not move now.** A bar adjusted after seeing a
   0.2817 is no longer a pre-registration, and rule 1 `[R-STRUCT]`'s whole point
   is that a mechanism is not selected by whether it clears a line drawn around
   its result. **The gate stands, the arm is killed, and the span is not spent.**

## 3. Two of the five gates were never scorable, and that is a defect in my screen

- **G-2 volume** — withdrawn in Addendum A.2, before the result: rule 15's
  keeper-only retention makes the control bundle slim (no unit-level dispatch),
  so the control's imports cannot be decomposed by seam, and the model's gross
  import class is not comparable to the measured net seam total.
- **G-4 no collateral flip** — **discovered unscorable at scoring time**:
  `scripts/calibration_verdict.py` resolves only a **registered** run, and rule
  29(2) forbids registering a screen bundle. The gate as written cannot be run
  on the artifact the rule permits me to have.

So **three of five gates were live**. That is a materially weaker screen than the
PRECOMMIT advertised, and a design defect a future screen should fix by writing
G-4 against the committed sidecars directly rather than against the verdict CLI.

**The collateral reading, computed directly and reported as a NON-GATE:**

| C1 class, 2024 TWh | actual | keeper gap | arm gap | move |
|---|---:|---:|---:|---:|
| CT_PEAKER | 18.13 | −2.21 | **−1.13** | toward |
| COAL_PRB | 126.01 | −14.32 | **−13.20** | toward |
| COAL_BIT | 53.27 | −4.25 | **−3.62** | toward |
| CC_REGULAR | 147.38 | +4.30 | **+2.95** | toward |
| COAL_LIGNITE | 7.16 | −1.45 | −1.42 | toward |
| CT_CHP | 12.41 | −6.70 | −6.70 | flat |
| ST_CHP | 0.87 | +2.04 | +2.01 | toward |
| **ST_GAS** | 16.83 | +1.35 | **+1.78** | **away** |
| **CC_CHP** | 36.53 | −15.70 | **−15.93** | **away** |

**Six of nine fossil cells move toward actual and two move away**, the larger
adverse move being ST_GAS at +0.44 TWh. C3a moves away but stays well inside
band (+2.9 % → +4.2 %, tolerance ±10 %). Imports fall 31.29 → 29.75 TWh
(reported-only per A.2). Wind, solar, nuclear and hydro are unchanged to
0.00 TWh, which is the confinement G-3 asserts, independently confirmed.

**None of this is a gate and none of it promotes anything** (rule 29: a screen
may never promote). It is recorded because a future charter needs it.

## 4. What goes to the owner

The owner's standing steer of 2026-09-06 — *"if structural integrity improves
but gates regress that may still be a keeper"* — is the rule-29(2) owner step,
and the PRECOMMIT pre-registered escalation for a marginal outcome. This is one:

- the mechanism **cleared every gate that measures what it does** (G-3, G-5);
- it **flipped the sign** of the seam's price response on the published
  comparator basis, which is the defect the whole lane exists to fix and which
  no prior arm has moved by more than 10 %;
- six of nine fossil C1 cells improved;
- and it missed **one magnitude bar, of my own choosing, by 6 % of that bar**.

**The question for the owner is whether to re-charter the full span
(2023–2025, one bundle, ~35 min) under a bar set by someone other than the lane
that failed it.** I am not making that call and have not spent the years.

## 5. Governance

Rule 1 `[R-STRUCT]`: the gate is structural and STOP-only, was not gated on the
target residual, and is not moved after the fact. Rule 15 `[R-DASHBOARD]`: the
screen bundle is **not** registered (rule 29(2)) and is **DELETED before merge**
(rule 29(c)) — every number this session will ever cite from it is in this
document and in `_miso231_screen_gates.json`; git history is the record.
Rule 16: not engaged — no full span was solved. Rule 19 `[R-ONE-MECH]`: the
hourly overlay displaces the annual one, never stacks. Rule 21 `[R-DOF]`: no
free parameter; ledger stays 41/2. Rule 22: 2024 only, a training year.
Rule 28(b): the `seam_neighbour_hourly_ladder` MISO cell is updated in this
session with this verdict; it stays **O**, not `R` — `R` means refuted, and the
mechanism demonstrably does what it claims (§1); what it missed is a magnitude
bar. Rule 29: phase 0 ran first, the screen year was named on the mechanism's
own model-free footprint under a measure declared before it was applied, G-DRIFT
was audited twice (Addenda A/B, all inert), the bundle is deleted before merge,
and **the kill is reported as the session's result with the remaining years
unspent**.
