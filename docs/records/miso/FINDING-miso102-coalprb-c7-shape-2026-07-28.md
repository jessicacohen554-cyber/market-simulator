# FINDING miso-102 — C7 COAL_PRB is owned by the regulated committed-band take-or-pay discount, PROVEN by A/B (2/3 years flip to PASS); the arm is REJECTED as structurally incomplete; and my own pre-registered mechanism test P5 is FALSIFIED IN DIRECTION — removing the discount fixes the dispatch wave while making the PRICE wave WORSE

**Determination: DIAGNOSIS CONFIRMED; ARM REJECTED (pre-registered as
non-keeper before the solve). KEEPER UNCHANGED — `2026-07-28-miso-101b-tempgrain`.**

Pre-registration: `PREREG-miso102-coalprb-c7-shape-2026-07-28.md`, committed
before either arm was solved (`5200d16`, re-authored `141597f`).
Runs: `2026-07-28-miso-102a-control` (`miso102_control_A`) /
`2026-07-29-miso-102b-sunkfixed` (`miso102_sunkfixed_B`), both 2023–2025 in one
bundle (rule 16 `[R-ALLYEARS]`).
Diagnosis reproduction: `scripts/probes/miso102_c7_coalprb_diagnosis.py`.

---

## 0. Summary

1. **The C7 COAL_PRB failure is owned by `coal_committed_takeorpay_regulated`,
   and the A/B proves it.** Suppressing the committed-band discount flips
   `cv_ratio` **0.467 → 0.727** (2023) and **0.476 → 0.931** (2024), both from
   FAIL to PASS. 2025 stays FAIL at 0.364.
2. **Four candidate hypotheses are refuted from committed artifacts alone** — a
   floor, a mix effect, the benchmark basis, and the miso-101 §5 cancellation
   mechanism. The failure is also **separable from miso-89**.
3. **My own pre-registered mechanism test P5 is FALSIFIED, in direction.** I
   predicted the arm must widen the off-peak *price* wave. It **narrows** it in
   all three years (ratio 0.460 → 0.377, 0.530 → 0.418, 0.331 → 0.311) and moves
   the night price *further* from actual. §2's price→dispatch causal reading is
   dead; the discount acts on the dispatch wave **directly**, not through price
   formation.
4. **The arm is REJECTED**, as pre-registered — not on the gates, but because it
   deletes a real behaviour (regulated self-commitment) along with the category
   error. C1 goes PASS → FAIL (16/16 → 11/16).
5. **The lever space for C7 is now narrower, not wider**, and §6 records exactly
   which branches are closed and why.

## 1. The diagnosis (committed artifacts only, NO LP re-solve)

Full detail and numbers: pre-registration §1–§3, reproduced by
`scripts/probes/miso102_c7_coalprb_diagnosis.py`. Headlines:

| hypothesis | verdict | evidence |
|---|---|---|
| held flat by a **floor** | **REFUTED** | D-2: MISO coal carries exactly ONE mechanism, `reliability_floor`, at **0.31 / 0.35 / 0.19 %** of class energy. Rule 17 has nothing to bite on. |
| **mix effect** (wrong overnight unit SET) | **REFUTED** | D-1 pairs model and bench on the same keys; **0 dropped** (31/31/30). |
| **benchmark basis** | **REFUTED** | same CAMPD plant set, bench's own class labels; class energy ratio 0.91/0.91/0.95. |
| miso-101 §5 **cancellation** | **REFUTED** | off-peak coherence `std(Σ)/Σstd` = **0.984/0.981/0.939** (model), **0.971/0.972/0.922** (actual) — both in phase. Phase coherence *matches* (0.68/0.62/0.55 vs 0.67/0.62/0.53); only amplitude misses. |
| same as **miso-89** | **SEPARABLE** | seasonal `cv_ratio` winter/shoulder/summer = 0.416/0.457/0.488, 0.453/0.411/0.526, 0.374/**0.274**/0.384 — present every season, **worst in winter/shoulder**, in h0–h14. miso-89's instrument is summer HE16–18. |

**Which units.** 100 % of the byte-flat PRB plants are **REGULATED**, all three
years (9/8/10 plants, **46/44/50 %** of class energy). Pooled over 2023–25, all
MISO coal ranks: ACTUAL within-day CV **regulated 0.197 vs merchant 0.134**;
MODEL **regulated 0.073 vs merchant 0.351**. **The model inverts the measured
flexibility ordering by 4.8×.** Within COAL_PRB the two groups are measured
statistically indistinguishable (0.262 vs 0.231) — there is no support in MISO's
own conduct for the claim the discount encodes.

*(Denominator note: the pre-registration quoted the flat-set energy share as
47/46/50 % from a `dropna`-filtered denominator; the committed probe uses all
paired keys and gives 46/44/50 %. Same plants, same conclusion.)*

## 2. The A/B result

**C7 D-1 `COAL_PRB` (gate `cv_ratio` ≥ 0.50):**

| year | profile r A → B | model off-peak CV A → B | actual | **cv_ratio A → B** | verdict |
|---|---|---|--:|---|---|
| 2023 | 0.987 → 0.991 | 0.072 → 0.112 | 0.155 | **0.467 → 0.727** | FAIL → **PASS** |
| 2024 | 0.977 → 0.992 | 0.058 → 0.113 | 0.121 | **0.476 → 0.931** | FAIL → **PASS** |
| 2025 | 0.970 → 0.969 | 0.023 → 0.027 | 0.074 | **0.318 → 0.364** | FAIL → FAIL |

**Every other gated class** (`cv_ratio` A → B): COAL_BIT 0.712→2.800,
0.589→2.582, 1.131→1.937; COAL_LIGNITE 2.365→2.941, 1.034→2.863, 0.804→0.782;
CT_PEAKER 0.979→0.787, 0.847→0.540, 0.805→0.734; ST_GAS 1.555→1.497,
1.282→1.018, 1.497→1.490. All still pass — but note COAL_BIT overshoots to
**2.6–2.8×** the measured off-peak variability, i.e. the arm does not land BIT
on its meter, it throws it past.

**C-series rubric (v2.9), the only status change:**

| criterion | tier | control | arm |
|---|---|---|---|
| **C1 fuel-mix by class** | load-bearing | **PASS** (16/16 · free 12/12) | **FAIL** (11/16 · free 7/12) |
| C2 system volume | load-bearing | PASS | PASS |
| C3a mean LMP | load-bearing | FAIL | FAIL |
| C3b price duration/shape | load-bearing | PASS | PASS |
| C3c price tail | supporting | FAIL | FAIL |
| C4 dispatch correlation | supporting | PASS | PASS |
| C7 diurnal shape (D-1) | protective | FAIL | FAIL (2025 only) |
| C8 forced share (D-2) | protective | PASS | PASS |

`grade_summary`: scored 8 / target 5 / fails **3** → scored 8 / target 4 /
fails **4**. Determination **NOT-YET** in both (both read `UNATTESTED` — a
replayed bundle carries no governance attestation; identical for both arms, not
a difference between them).

**Coal volume:** 182.09 → 163.62 (**−18.47**), 173.37 → 146.15 (**−27.22**),
211.79 → 204.11 (**−7.68**) TWh. Displaced (2023) by CC_REGULAR +5.30, imports
+5.05, CT_PEAKER +3.91, CC_CHP +2.00, ST_GAS +1.58 TWh.

## 3. P5 is FALSIFIED, in direction — and it kills a lane

The pre-registration made P5 the mechanism test and said explicitly: *"If
dispatch amplitude rises while the price wave does not, §2's attribution is
WRONG."* It did.

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| off-peak **price** CV ratio, control | 0.460 | 0.530 | 0.331 |
| off-peak **price** CV ratio, **arm** | **0.377** | **0.418** | **0.311** |
| predicted | ≥ +0.05 | ≥ +0.05 | ≥ +0.05 |
| actual Δ | **−0.083** | **−0.112** | **−0.020** |
| night HE0–3 $ control → arm (actual) | 27.81 → **29.96** (19.42) | 25.35 → **28.08** (18.46) | 34.40 → **35.25** (26.87) |

**What was wrong.** §2 observed that the COAL_PRB dispatch amplitude ratio and
the off-peak price amplitude ratio coincide year by year (0.467/0.476/0.318 vs
0.460/0.530/0.331) and I read that as *price wave → dispatch wave*. The arm shows
the co-movement is **not** that causal chain: both ratios are joint consequences
of the same discount. Removing it raises coal's offer from ~VOM to full delivered
cost, so PRB becomes marginal and its **dispatch** wave widens — while the
**clearing price** overnight *rises* (coal now bids ~$25 instead of ~$3), so the
off-peak price spread *narrows* and the night price moves further from the meter.

**Consequence for the lever space.** A price-formation lever (the MISO lever
queue's item 3, DA virtual depth) is **not** the route to C7 — C7 is reachable
directly through the offer path, and the price wave is a *separate* miss that the
C7 fix makes worse. The two must not be treated as one phenomenon.

The *observational* content of §2 stands and is still useful: the model's coal
fleet is **not** under-responsive to price (slopes 372/151/248 vs the real
fleet's 157/167/88 MW per $), so no offer-**steepening** lever is admissible.

## 4. Pre-registration scorecard — 5 hit, 1 missed, 1 falsified, 1 unscoreable

| id | prediction | outcome |
|---|---|---|
| **P1** | `cv_ratio` rises all three years | **✓ HIT** — 0.467→0.727, 0.476→0.931, 0.318→0.364 |
| **P2** | 2023+2024 PASS, 2025 FAIL | **✓ HIT** exactly |
| **P3** | COAL falls 20–30 TWh in 2023 and 2024 | **✗ MISSED (magnitude)** — 2024 −27.22 in band, **2023 −18.47 below**, 2025 −7.68 far below. The miso-101b keeper is materially **less** discount-sensitive than miso-96's miso-88 base (−26.6 TWh); I over-predicted from the older base. |
| **P4** | C5a CO2 vs eGRID falls 8–12 % → FAIL | **UNSCOREABLE** — C5a is **not in rubric v2.9's MISO criterion set** (8 scored criteria, no emissions gate). My direct CO2 recompute failed on a plant-code join dtype and **is not reported rather than guessed**. Direction (coal→gas displacement lowers CO2) is certain; the magnitude is not established here. |
| **P5** | off-peak PRICE CV ratio rises ≥ 0.05 each year | **✗ FALSIFIED, IN DIRECTION** — falls 0.083/0.112/0.020. See §3. |
| **P6** | regulated within-day CV rises; reg:merch ratio → ≥ 0.50 | **✓ HIT** — regulated 0.076→0.154, 0.074→0.190, 0.062→0.107 (roughly doubles, against a measured 0.197); ratio 0.57→0.63, 1.05→1.21, 0.42→0.58 |
| **P7** | determination stays NOT-YET | **✓ HIT** — both arms NOT-YET |
| **P8** | control reproduces the keeper < 0.01 % | **✓ HIT** — **0.00000000 %** on every class in every year, mean price bit-identical |

## 5. Why the arm is REJECTED (decided before the solve, and unchanged by it)

The pre-registration stated: *"this arm is structurally incomplete by
construction and is NOT a keeper candidate whatever the gates do."* That holds.

Removing the committed-band discount removes **two** jobs at once (miso-96 §7):

1. **The category error** — an annual/monthly contracted-tonnage obligation
   priced as a per-hour marginal subsidy, binding in all 8760 h including the
   hours its own driver evidence says the plant de-loads. Rule 17
   `[R-FLOOR-WINDOW]`: a discount with no window. **Removing this is correct.**
2. **A real behaviour** — regulated self-commitment (SOM Table 7: regulated
   utilities self-commit 53–56 % of coal starts). **Removing this is a
   regression.**

Rule 1 `[R-STRUCT]` cuts both ways: it forbids rejecting a structurally-correct
mechanism because a gate moved the wrong way, and it equally forbids *promoting*
one that deletes a real market behaviour because a gate moved the right way.
This arm is on the second side of that line, which is why the C1 PASS → FAIL is
a *symptom* of the structural incompleteness, not the reason for rejection. The
corroborating structural tell is in §2: COAL_BIT's `cv_ratio` overshoots to
2.6–2.8×, so the arm does not restore measured conduct — it overcorrects.

`coal_committed_takeorpay_sunk_fixed` therefore stays **default-off,
probe-refuted-alone**, on the footing miso-96 §7 set. It is the control arm the
successor lane needs, now re-taken on a keeper four revisions newer.

## 6. What is now closed, and what remains

**CLOSED by this session:**

* C7 COAL_PRB is **not** a floor, **not** a mix effect, **not** a benchmark
  basis, **not** the miso-101 §5 cancellation, and **not** the miso-89
  summer under-derate. All five refuted from committed artifacts.
* **No offer-steepening lever** is admissible — the model's coal is already
  0.9–2.8× the real fleet's price-responsiveness.
* **Price formation is not the route to C7** (§3, P5) — and the C7 fix makes the
  price wave *worse*, so the two are separate misses and must not be pursued as
  one (rule 19 `[R-ONE-MECH]` in reverse).
* **Blunt removal is settled**, now on the current keeper: it fixes 2/3 years and
  costs C1.

**STILL OPEN — the one identified route, and its one blocker.** The
**minimum-take LP constraint** (MISO lever queue item 1): a contract-period
tonnage constraint priced by its dual, which separates job 1 from job 2 — the
unit stays committed, but chooses *when* within the period to burn. Its blocker
is unchanged and was verified here rather than assumed: the constraint needs a
tonnage that is **not** the same year's measured receipts, and **EIA-923
publishes deliveries, not contract terms**. `share × measured annual receipts`
would pin the model's annual coal energy to ≈ actual — a measured *outcome* fed
back to force the backcast, which rule 13 `[R-MEASURED]` forbids outright. A
lagged / multi-year-mean construction is the only candidate that is
forward-regenerable, and it needs its own charter and a pin-strength test before
anything is built.

**2025 is a separate question.** Even with the discount gone 2025 reaches only
0.364, with a model off-peak CV of 0.027 against a measured 0.074 — the fleet
barely cycles whatever its offer says. That is the already-adjudicated,
data-blocked outage-grain gap (FINDING-miso89 §7; the standing data ask), not a
new phenomenon, and it is **not** re-attacked with a second mechanism.

**NOT LICENSED:** a PRB-only or residual-scoped variant of the discount (rule 13/24
— scoping to the failing class is fitting); a second overnight coal floor stacked on
the discount (rule 19); widening the C3c/C3b ledger to absorb C7 (C7 is protective
and hard, and MISO's ledgered budget is 3/3 saturated regardless).

## 7. Governance

* Rule 22 `[R-HOLDOUT]` honoured — 2023–2025 only, MISO freeze active, no
  calibration-complete marker, P1 only.
* Rule 12 `[R-PARALLEL]` — one process per year per arm (11.5–12.4 GB peak on a
  15 GB box), arms staged serially, merged with
  `scripts/probes/pjm119_merge_year_chain.py`, `--rebuild-benchmark` per arm.
  No `--reuse-solved`: all six year-solves fresh.
* Rule 15 `[R-DASHBOARD]` — both arms registered.
* Rule 26 `[R-MECH-MATRIX]` duty (b) — `coal_takeorpay_committed` MISO cell
  updated this session.
* **Keeper unchanged.** No keeper shard was edited, no attestation authored.
