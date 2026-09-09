# RESULT — nyiso-222: the owner-directed +5% offer-curve move

**Session:** nyiso-222 · **ISO:** NYISO · **Date:** 2026-09-09
**Run:** `2026-09-09-nyiso-222-offer-plus5` · bundle `results/calibration/nyiso222_offer_plus5`
**Control:** the committed keeper `2026-09-09-nyiso-221-fuelvintage-span` (G-CTRL form 4; no control solve spent)
**Pre-registration:** `docs/PRECOMMIT-nyiso222-offer-curve-plus5-2026-09-09.md` (pushed before the first LP)

## Headline

**DETERMINATION: CALIBRATED** — grade 7/8, 0 fails, C3c the lone ledgered caveat.
**Identical determination and identical criterion statuses to the keeper: zero PASS→FAIL
flips in either direction, in any year.**

The owner's +5% was applied to the four authorized bands on the 10 router-valid classes
(40 bands, every ratio exactly 1.05). It was set ex ante, declared, and **never swept**.

---

## 1. Scorecard — every criterion at full magnitude

| Criterion | Tier | 2023 | 2024 | 2025 | Verdict |
|---|---|---|---|---|---|
| **C3a** mean LMP | LOAD | +4.3% → **+8.3%** | +5.3% → **+8.9%** | −7.3% → **−4.7%** | **PASS** (±10%) |
| **C3b** price shape (NRMSE) | LOAD | 0.122 → **0.142** | 0.179 → **0.193** | 0.160 → **0.148** | **PASS** (≤0.20) |
| **C3c** hours > $300 | SUPP | 2 vs 10 → **2 vs 10** | 0 vs 13 → **0 vs 13** | 3 vs 42 → **3 vs 42** | **CAVEAT** (ledgered) |
| **C1** fuel-mix | LOAD | in band | in band | 923-preliminary | **PASS** |
| **C2** gas family (TWh) | LOAD | 61.28 → **61.17** | 66.58 → **66.45** | 69.51 → **69.49** | **PASS** |
| **C4** dispatch corr. | SUPP | — | — | — | **PASS** |
| **C6** governance | PROT | — | — | — | **PASS** |
| **C8** forced share (ST_GAS) | PROT | 16.1% → **16.0%** | 20.9% → **20.8%** | 18.1% → **18.3%** | **PASS** (cap 30%) |
| C5a CO2 (reported-only) | — | +1.5% | +0.3% | +4.3% | unchanged |
| D-A diurnal amplitude (reported-only) | — | 61.1 → **63.1%** | 52.5 → **53.8%** | 42.1 → **42.9%** | improved |

**C3a is worse in 2023 and 2024 and better in 2025 — exactly as pre-registered.** The
model was already above actual in two of the three years, so a uniform lift had to hurt
there. That is reported, not repaired.

**C3b's 2024 value (0.193) is the closest any criterion comes to a limit** (0.20). It
still passes; it is the number to watch if this direction is pushed further.

---

## 2. Predictions vs outcome — including the one that missed

| Prediction (PRECOMMIT §5) | Outcome | Verdict |
|---|---|---|
| C3a up in all three years, by **less** than 5% | +4.0 / +3.6 / +2.6 pp of a nominal 5 | ✅ |
| C3a 2023 in **+6.9…+8.8%** | **+8.3%** | ✅ inside band |
| C3a 2024 in **+8.0…+9.8%** (central +8.9%) | **+8.9%** | ✅ dead on central |
| C3a 2025 in **−5.0…−3.3%** | **−4.7%** | ✅ inside band |
| **No PASS→FAIL flip**; 2024 fails only if pass-through > 88.8% | realized 68.2%; no flip | ✅ |
| C3c stays a **ledgered CAVEAT**, not a PASS | ledgered CAVEAT | ✅ |
| C3c **improves** (more hours > $300) | **UNCHANGED at 2 / 0 / 3** | ❌ **MISSED** |
| C1: fossil down, imports up; CC_REGULAR the big class | confirmed (§3) | ✅ |
| C8 forced share ticks **up**, no cap crossed | no cap crossed; share ≈ **flat** (down in 2023/24) | ⚠️ partial |

### 2.1 The C3c miss, stated rather than absorbed

The mechanism reasoning was right and the magnitude was wrong. The tail **did** thicken:

| hours above | 2023 | 2024 | 2025 |
|---|---|---|---|
| > $200 | 10 → **13** | 42 → **46** | 281 → **316** |
| > $150 | 79 → 79 | 287 → **317** | 1278 → **1367** |
| model max $/MWh | 326.4 → 331.2 | 217.9 → **226.8** | 323.5 → 323.5 |

But the **gate counts hours above $300**, and **2024's model maximum is $226.8** — a 5%
lift cannot bridge a 38% gap. 2023 and 2025 need 5 h and 21 h respectively from 2 h and
3 h. The prediction should have checked the distance to the threshold, not just the
direction; it did not, and that is a defect in the prediction, not in the run.

### 2.2 The PRECOMMIT's pass-through *reasoning* is falsified even though its *numbers* held

All three C3a predictions landed inside their bands, but the model behind them — "a
fraction of hours are set by a scaled unit, so the mean rises by that fraction of 5%" —
is **wrong**, and this run's own numbers falsify it:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Δ mean LMP $/MWh | +1.29 | +1.37 | +1.70 |
| **$/MWh per 1% of band** | **0.258** | **0.274** | **0.340** |
| nyiso-218 (3% lift, `peak` frozen) | 0.2389 | 0.2278 | 0.2960 |

A proportional model requires the $/MWh-per-1% to track the **price level**, whose
2025/2023 ratio is **1.83×**. The observed ratio is **1.32×**. Pass-through is
**near-constant in dollars**, because the keeper arms `gas_offer_net_revenue_margin` at a
3.9046 $/MMBtu anchor, which turns a band lift into a fixed $/MWh margin rather than a
proportional cost scaling.

**This independently reproduces nyiso-218's central finding and extends it**: unfreezing
the `peak` band (nyiso-218 froze it) buys only **~8–20% more** pass-through (ratios 1.08 /
1.20 / 1.15). The right forward model for this channel is *dollars per band-point*, and
any future session should size a move that way.

---

## 3. Where the energy went — condition (d)'s intended merit-order move

Model energy, TWh, keeper → arm:

| class | scaled? | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| CC_REGULAR | ✔ | −0.145 | −0.143 | −0.037 |
| CC_CHP | ✔ | −0.085 | −0.044 | −0.053 |
| ST_GAS | ✔ | −0.032 | −0.063 | −0.087 |
| CT_PEAKER | ✔ | +0.024 | +0.021 | +0.061 |
| CT_CHP | ✔ | +0.083 | +0.083 | +0.019 |
| **ST_CHP** | **✘ (no registered band)** | **+0.125** | **+0.095** | **+0.075** |
| **import** | ✘ (no offer band) | **+0.026** | **+0.048** | **+0.018** |
| net system | | −0.004 | −0.005 | −0.005 |

Two structural readings:

1. **The declared exclusion is visible in the dispatch.** `ST_CHP` is router-valid and
   NYISO genuinely dispatches it, but it has **no entry** in the keeper's resolved
   `offer_curve_by_group`, so there was nothing to scale — rule 1(a) forbids inventing a
   band. It therefore gets *cheaper in relative terms* and picks up energy in every year.
   This is **against interest**: `ST_CHP` was already over actual, and the move makes it
   worse (2023 +0.20 → **+0.32 TWh**; 2024 +0.26 → **+0.35**). The PRECOMMIT named this
   limit before the solve; here it is, measured.
2. **A multiplicative move widens spreads**, so the cheapest resources gain — imports
   (priced at fixed measured neighbour DA LMPs, untouched by this channel) rise in all
   three years, and the cheaper CHP tranches gain against the expensive CC fleet.

**C1 improves where it was tightest**: 2024 `CC_REGULAR` +2.91 → **+2.77 TWh**
(share +2.5 → +2.4pp against a ±3pp band) — the pre-registered prediction. It worsens on
`ST_CHP`, per (1). Net system energy is conserved to −0.005 TWh, which is the sanity check
that nothing else moved.

---

## 4. Governance

- **Rule 1 `[R-STRUCT]` conditions (a)–(e): all discharged.** (a) 40 bands, four
  authorized names, every ratio exactly 1.05, `phys_*` / `econ_low_share` / `pct_peaking`
  untouched — violations NONE, verified twice (pre-solve, and again inside the attestation
  generator against the keeper's own curve). (b) ONE config across all three scored years.
  (c) declared in the PRECOMMIT before the first LP; **never swept** — exactly one arm
  exists and no other factor was tried, in this session or before it. (d) the merit-order
  move of §3 is the intended effect. (e) `governance.authorized_price_tuning` is present
  and well-formed; **C6 PASSES**.
- **Rule 21 `[R-DOF]` / rule 20 R-AY.** `offer_curve_by_group` carries a tuned value; its
  ledger row is re-keyed with the identification source **"price residual, authorized
  channel (rules 1/13 amendment 2026-09-05)"** — the ruling, not a measured input —
  reported at full magnitude. Per R-AY its presence does not by itself make the residual
  it closes an open root-cause issue, and **no gate moved** on account of it.
- **Rule 29(b) `[R-SCREEN]` / G-DRIFT.** Keeper `da2e7076` → HEAD: two changed solve-path
  hunks, **both INERT** — `constants.py` is comment-only (zero non-comment changed lines,
  and inside NEISO's sub-dict), and `solve_surface_declared.py` is read only by the
  cache-key fingerprint (`solve_surface.py:330`), never the LP. Form 4 held; **no control
  solve was spent.**
- **Rule 28 `[R-MECH-MATRIX]`.** `docs/codebase-site/data/mechanism-matrix/NYISO.js` only,
  cell `offer_curve_by_group` (letter **K**, unchanged) + the shard's `gates` stamp.
- **Rule 22 / R-AZ.** Years 2023–2025 are train tier; the registration marker gate passed.
  **No marker moved, `final` NOT granted, no locked-test year touched. NYISO's ladder is
  2022 ALONE — 2020 and 2021 remain DATA-BLOCKED with both authorizations UNSPENT.**
- **Rule 30(c).** No held-out year was solved or scored here, and none downgrades NYISO.
- **Rule 31 `[R-RETAIN]`.** The bundle is **gitignored, not deleted**. Nothing is removed
  until the owner rules on promotion.

### Unchanged pre-existing conditions (not introduced by this run)

- The legitimacy-diagnostics gate reads FAIL on **both** the keeper and this arm — 5 D-4
  rows each. C8 scores PASS from the artifact's contents regardless. Pre-existing.
- 2025 C1 per-class rows are SKIPPED on preliminary EIA-923 vintage, on both runs.

---

## 5. Disposition — the promotion question is the OWNER'S

**The lane does NOT self-promote and does NOT withhold.** Reported plainly:

**Against promotion.** It adds **no structure** — it is a level move, not a mechanism. It
makes C3a **worse in 2 of 3 training years** (+4.3 → +8.3, +5.3 → +8.9) and better in one
(−7.3 → −4.7). C3b worsens in 2 of 3, with 2024 at 0.193 against a 0.20 limit. It makes
`ST_CHP` worse, and it moves a **ledgered DOF free parameter** rather than closing a root
cause.

**For promotion.** The determination is **unchanged at CALIBRATED with zero flips**, so
nothing is lost on the gates. It **improves C1 where C1 was tightest** (2024 `CC_REGULAR`),
improves **C2** in all three years, improves the reported **diurnal amplitude** in all
three years (61.1 → 63.1 / 52.5 → 53.8 / 42.1 → 42.9% of measured), and shifts energy from
an over-modelled fossil fleet toward imports — all in the direction the residuals say is
right. And it is what the owner asked for, through the channel the owner authorized.

Under the standing formula — *"if structural integrity improves but gates regress that may
still be a keeper"* — **the call is the owner's.**

**THE BUNDLE IS ON LOCAL DISK AND GITIGNORED. THIS CONTAINER IS EPHEMERAL AND WILL NOT
SURVIVE THE SESSION.** If the owner wants this promoted, say so and the slim set is
committed with `git add -f`; otherwise reproducing it costs a full 3-year NYISO re-solve
(~35 min of LP plus ~30 min of `data/clean` regeneration).
