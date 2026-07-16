# Position calibration — D1=3 curve-ON re-probe, PJM + MISO (RC-1A-D1, 2026-07-16)

**Charter.** RC-2B §5 / `capacity-clearing-flip-memo-2026-07-16.md` §5: re-run the
RC-1A curve-ON probe legs (PJM + MISO) at the D1=3 default
(`retirement_years_coal=3`, RC-D1 / PR #2335, now on `origin/main`), converting every
EXPECTED-under-D1=3 column in the flip memo to **MEASURED**. Findings-first, and the
**LOYO carrier** (RC-2B §0-3 / rule 22): D1 adoption deferred the leave-one-year-out
score, so no D1-driven verdict flip may ship to a `capacity_market_clearing` flip
until this LOYO lands. The **BEFORE legs are D1-INVARIANT** (retire no coal at any
threshold — RC-1A §4.1) and are reused from the committed bundles, not re-solved.
2022 bridged-never-solved (rule 22).

Verified on `origin/main` before the run: `retirement_years_coal == 3`
(`scenarios.py:283`), confirmed live in the run config
(`'retirement_years_coal': 3`). Probe legs solved with `--capacity-market-clearing`
(`capacity_market_clearing_by_iso={iso: True}`, scalar off, D1=3 as shipped,
`staged_oversupply_thinning` off per rule 19, every other default untouched). MISO on
the RC-1C seasonal RBDC grain. **Nothing tuned; no default touched; no holdout year
solved or scored (2022 bridged).**

> **Session note (rule 12 / memory).** The 15 GiB session **cannot** hold two
> multi-zone per-plant LPs concurrently — each peaks ~8.6 GB and the first concurrent
> attempt OOM-killed the MISO leg. The two probe legs were therefore solved
> **sequentially** (years sequential within each), not in parallel. This is the
> rule-12 memory-limit clause in force, not a deviation.

---

## 0. Bottom line first — the honest one

**D1=3 does NOT unblock the flip for either ISO. The EXPECTED-under-D1=3 column in
the flip memo (which hypothesised D1=3 would move the OPEN position/skill items to
PASS) is REFUTED by measurement.** The re-probe measured a *different* outcome than
either the D1=1 overshoot or the memo's expected improvement:

- **PJM: D1=3 ELIMINATES the coal wave in-window** (coal econ exits 9.913 → **0.0
  GW**, recall 76% → **0%**). The position still walks into the priced region
  (2025 = 0.998, T-R4 PASS) — but via the **entry side** (curve relieves the gas_cc
  over-build 12→8 GW) + **load growth**, NOT via retirements. Right price, wrong
  fleet path. BLK-10 backstop over-fire disappears.
- **MISO: D1=3 DESTROYS the D1=1 near-pass by a per-fuel threshold INVERSION.**
  Raising *only* coal to 3 (gas_st/gas_ct stay at 2) makes **gas_st the first-exiting
  fossil**: gas_st econ exits 0 → **8.643 GW** in 2023 (a fuel that retired **zero**
  in reality — pure false-retire), while coal delays 2022→2024 and shrinks 11.809 →
  3.558 GW. false-retire 0.874 GW (PASS) → **8.643 GW (FAIL)**; the 2025 shortage
  position **lengthens** 1.035 → 1.068 (pays $0 vs 24.5, vs the 243.3 cap-clearing).
  **Worse on both position AND skill.**
- **LOYO (rule 22): the D1=3 regressions survive leave-one-year-out** — they are
  structural, not in-sample artifacts. Per the charter's step 4, *LOYO degradation is
  a finding that BLOCKS the flip, not a number to widen.*

**Recommendation: HOLD both ISOs. The D1=3 threshold — correctly identified on the
RC-0B §a.3 lag table, and this doc does not second-guess that identification —
reveals a NEW structural blocker (the per-fuel threshold inversion, §6) that must be
resolved before any flip.** The single-threshold change is not the flip unblocker
RC-2B hoped; it trades one PJM failure mode for another and regresses MISO outright.

---

## 1. The wave-timing question, ANSWERED (RC-2B §0-1)

RC-2B §0-1 asked whether D1=3 DAMPS, merely DELAYS, or RE-TIMES the exit-wave
overshoot. **The measured answer is ISO-dependent, and reveals a fourth mode neither
option anticipated: cross-fuel re-timing / outright elimination.** The threshold
change interacts with the *per-fuel* threshold structure, because raising coal to 3
while every other fossil class stays at 2 changes *which fuel loses its payment and
exits first*.

### PJM — the wave is ELIMINATED in-window (coal margin oscillates, streak never forms)

| cal yr | D1=1 coal econ exit (GW) | D1=3 coal econ exit (GW) |
|---|--:|--:|
| 2022 (bridge) | 3.481 | **0.000** |
| 2023 | 0.000 | 0.000 |
| 2024 | 6.432 | **0.000** |
| 2025 | 0.000 | 0.000 |
| **cum** | **9.913** | **0.000** |

Mechanism: the coal counter needs 3 *consecutive* loss years. PJM's cap-weighted coal
screen net-revenue **oscillates around the GFC bar (58.5 $/kW-yr): 77.0 → 113.3 →
24.1 → 142.1** across the evolution steps — a profitable year resets the counter
before any cohort reaches 3. D1=3 does not *delay* a same-sized wave (RC-2B §0-1
point 1's worry); it *prevents* it: PJM coal's energy margin alone covers GFC in most
years, so the 3-year loss streak never forms. **Verdict: ELIMINATE (in-window
undershoot on the exit side) — RC-2B §5's named T-R1d undershoot risk, confirmed.**

### MISO — the wave is RE-TIMED across fuels (coal→gas_st) and delayed

| cal yr | D1=1 coal (GW) | D1=3 coal (GW) | D1=3 gas_st (GW) |
|---|--:|--:|--:|
| 2022 (bridge) | 8.054 | **0.000** | — |
| 2023 | 0.000 | 0.000 | **8.643 (NEW)** |
| 2024 | 3.755 | **3.558** | — |
| 2025 | 0.000 | 0.000 | — |
| **cum** | **11.809** coal | **3.558** coal | **8.643** gas_st |

MISO coal is at the 1.26 fixed-mode cliff and **genuinely loss-making** (coal screen
net_rev 48.9 → 19 $/kW-yr, both below the 58.5 bar), so its counter *does* accumulate
— reaching 3 at the →2024 step, where coal exits 3.558 GW (the reliability floor
retains the rest). **But gas_st (threshold 2) reaches eligibility one year earlier**
(loss years 2021+2022 → exit 2023) and exits **8.643 GW** first — the 2023 floor log
shows gas_ct 24.0 GW + gas_st 5.3 GW + oil 0.33 GW all flagged at loss_years=2 and
adequacy-retained, with coal *absent from the eligible set* (counter < 3).
**Verdict: RE-TIME, both in time (coal 2022→2024) and across fuels (coal→gas_st) —
total thermal exits ~preserved (12.99 vs 12.59 GW), composition inverted.**

**Direct answer to RC-2B §0-1:** D1=3 neither uniformly damps nor uniformly delays.
On PJM it *eliminates* the wave (oscillating margin); on MISO it *re-times across
fuels* (coal→gas_st). Point 1 of §0-1 ("a higher threshold delays but does not thin")
is refuted on PJM (it thins to zero) and confirmed-plus on MISO (it doesn't thin the
*total*, it moves it to the wrong fuel). The per-fuel threshold structure — not the
coal threshold in isolation — governs the outcome (§6).

---

## 2. PJM — right price, wrong fleet path (T-R1/T-R4)

| leg | coal econ (GW,cum) | thermal (GW,cum) | recall >300MW | false-retire raw / IS-2020 (GW) | gas_cc / gas_ct adds (GW) |
|---|--:|--:|--:|--:|---|
| BEFORE (HEAD, D1-invariant) | 0.0 | 4.106 | 0% | 4.097 / 0.0 | 12.0 / 0.0 |
| D1=1 probe (committed) | 9.913 | 14.02 | 76% | 7.125 / 3.028 | 8.0 / 8.428 |
| **D1=3 probe (this re-probe)** | **0.0** | **4.106** | **0%** | **4.097 / 0.0** | **8.0 / 0.0** |
| actual | 6.885 | 11.121 | — | — | 8.525 / 0.447 |

Pass-2 (adopted basis, per-delivery-year vintage):

| cal yr | D1=1 pos / pays / cleared | D1=3 pos / pays / cleared | zero-cross |
|---|--:|--:|--:|
| 2023 | 1.078 / $0 / 12.5 | 1.091 / $0 / 12.5 | 1.0652 |
| 2024 | **1.006 / 112.0 / 10.6** (+961%) | **1.056 / 13.4 / 10.6** (+27%) | 1.0643 |
| 2025 | 0.977 / 164.8 / 98.5 | **0.998 / 132.1 / 98.5** (+34%) | 1.0673 |

- **The D1=1 2024 overshoot (paid 112 vs the real 10.6) is GONE** — D1=3 pays 13.4,
  a near-exact match to the real low clearing. The 2025 position lands at **0.998**,
  |Δ| = 0.009 from the T-R4 target 1.007 — **inside the ±0.028 band (PASS)**, and on
  the correct (slightly-long) side, where D1=1 overshot to 0.977 (|Δ|=0.030, miss).
- **But this happens with ZERO coal retirements.** The position reaches the region
  because the curve-ON entry screen sees the long position and **relieves the gas_cc
  over-build (12→8 GW)**; less over-building + **load growth** (req 133.9→150.6 GW,
  firm only 146→150 GW) shortens the position. The exit mechanism is inert in-window.
- **BLK-10 resolved:** the 6.428 GW `gas_ct_adequacy_2025` backstop over-fire is gone
  (gas_ct adds 8.428 → 0.0) — no wave → no adequacy deficit → no backstop. The gap-
  register row's "re-measure after D1" requirement (§6, R-2) is now satisfied: BLK-10
  is coupled to the wave and disappears with it; no backstop-sizing charter is needed.

## 3. MISO — the near-pass DESTROYED by threshold inversion (T-R2)

| leg | coal (GW,cum) | gas_st (GW) | thermal (GW,cum) | recall | false-retire raw / IS-2020 (GW) | 2025 CO2 err |
|---|--:|--:|--:|--:|--:|--:|
| BEFORE (HEAD, D1-invariant) | 0.0 | 0.0 | 0.784 | 0% | 0.0 / 0.0 | +14% |
| D1=1 probe (seasonal, committed) | 11.809 | 0.0 | 12.593 | 76% | **0.874 / 0.874 (PASS)** | +5% |
| **D1=3 probe (seasonal, this re-probe)** | **3.558** | **8.643** | **12.986** | **29%** | **8.643 / 8.643 (FAIL)** | **+8.5%** |
| actual | 10.934 | **0.0** | 15.227 | — | — | — |

Pass-2 (seasonal, adopted basis):

| cal yr | D1=1 pos / pays / cleared | D1=3 pos / pays / cleared | grain |
|---|--:|--:|---|
| 2023 | 1.038 / $0 / 3.6 | 1.033 / $0 / 3.6 | vertical-at-CONE |
| 2024 | 1.010 / $0 / 10.9 | 1.007 / $0 / 10.9 | vertical-at-CONE |
| 2025 | 1.035 / 24.5 / 243.3 | **1.068 / $0 / 243.3** | seasonal RBDC |

- **gas_st over-retires 8.643 GW against a reality that retired ZERO gas_st** — a
  pure false-retire, the entire 8.643 GW FAIL. This is the per-fuel threshold
  inversion (§6): coal at 3 lets gas_st at 2 exit first, and the model retires the
  wrong fuel.
- **coal collapses** 11.809 → 3.558 GW (recall 76% → 29%): coal now under-retires
  (−67% vs actual 10.934), where D1=1 was +8%.
- **Position worsens.** The 2025 shortage position **lengthens** 1.035 → 1.068 (gas_st
  exits but gas_cc/gas_ct rebuild 5 GW in 2025, and coal is retained), pushing it
  *past* the seasonal zero-cross so the shortage now pays **$0** (was 24.5) against
  the 243.3 cap-clearing. The one-sidedness RC-1A flagged is *deeper* under D1=3.
- CO2 2025 error +5% → +8.5% (still better than BEFORE's +14%, but worse than D1=1).

### Provenance (RC-2B §3 row M-2 / R-3(i)) — RESOLVED

The MISO probe prices **pre-2025 years on the vertical-at-CONE step**
(2021→2021-22 anchor 91.86, 2023→2023-24 103.04, 2024→2024-25 123.50 $/kW-yr; each
pays exactly **$0 at any long position >1.0** and full gross-CONE when short) and
**only 2025 on the seasonal RBDC**. Confirmed two ways: (a) directly evaluating
`resolve_demand_curve_vintage` + the pricing seam at the probe positions, and (b) the
Pass-2 model-price column above ($0 at 2021/2023/2024 on the vertical step; $0 at 2025
because pos 1.068 sits past the seasonal zero-cross). **The RC-1A §2 prose ("the
PY2025-26 parameter set serves every hindcast year hold-first") was a documentation
error** — the resolver selects each year's era-correct vertical vintage (landed with
the RC-1C merge `ad91468`, an *ancestor* of the probe-registration commits). The
probe's $0 rows at 2023/2024 match the **vertical step**, not a sloped curve near its
zero-cross. Report and tree are now reconciled; the D1=3 re-probe on HEAD is the
era-correct-instrument re-measurement.

---

## 4. T-R scorecard — NOW MEASURED at D1=3 (never widened)

| ID | criterion (pre-registered) | D1=1 measured | **D1=3 measured** | D1=3 verdict |
|---|---|---|---|---|
| T-R1a | PJM coal recall > 0; cum coal ∈ [2,14] GW | 9.913, 76% | **0.0, 0%** | **FAIL** (regression — wave eliminated) |
| T-R1b | PJM thermal ≤ 2× actual (22.2 GW) | 14.02 | 4.106 | PASS |
| T-R1c | zero economic nuclear | 0 | 0 | PASS |
| T-R1d | PJM 2025 position moves ≥ half 1.06→1.007 | 0.977 | **0.998** | PASS (via entry+load, not exits) |
| T-R1e | PJM additions bands not degraded | gas_cc 8, gas_ct 8.43 | gas_cc 8, **gas_ct 0** | PASS (BLK-10 gone) |
| T-R2a | MISO coal recall > 0; cum ∈ [3,22] GW | 11.809, 76%, false 0.874 PASS | **3.558, 29%, false 8.643 FAIL** | **FAIL** (coal cum 3.558 barely in band, but recall collapses + gas_st false-retire) |
| T-R2b | MISO gas_cc AND wind adds fall | gas_cc ↓, wind ✗ | gas_cc ↓ (3.0), wind ✗ (12) | FAIL (wind half, unchanged) |
| T-R2c | MISO 2025 CO2 error → 0 | +5% | +8.5% | PASS (report-only; ↓ from BEFORE +14%, ↑ from D1=1) |
| T-R4 | PJM 2025 within ±0.028 of 1.007; long yrs OUT | 0.977 (miss 0.030); 2024 IN (112 vs 10.6) | **0.998 (|Δ|=0.009 PASS)**; 2024 marginal-in 1.056 (pays 13.4≈real 10.6, no overshoot); 2023 out | **PASS** (2025 in band; 2024 near-real, not an overshoot) |
| T-R5-inv | I5 + I13 PASS on every leg | PASS | **PASS both legs** (I3/I7/I9/I12/I14 = pre-existing artifacts) | PASS |
| T-R7 | nuclear guard | econ 0; Byron/Dresden→IS-2020; Palisades→recall | econ 0 both ISOs; same announced-channel | PASS |

Raw vs IS-2020 (RC-0B §c.5 — both, never one):

| leg | false-retire raw (GW) | false-retire IS-2020 (GW) | reversal exposure (GW) |
|---|--:|--:|--:|
| PJM D1=1 | 7.125 | 3.028 | 4.097 |
| **PJM D1=3** | **4.097** | **0.0 (PASS)** | 4.097 |
| MISO D1=1 (seasonal) | 0.874 (PASS) | 0.874 (PASS) | 0.0 |
| **MISO D1=3 (seasonal)** | **8.643 (FAIL)** | **8.643 (FAIL)** | 0.0 |

The **PJM/MISO false-retire verdicts INVERT under D1=3**: PJM improves (7.1→4.1 raw,
3.0→0.0 IS-2020 — the coal overshoot is gone), MISO degrades (0.874 PASS → 8.643 FAIL
— the gas_st over-retire appears). Neither is a scoring artifact; both are the wave
mechanism (PJM's eliminated, MISO's inverted).

---

## 5. §2.1 flip-gate scorecard — items 3-4 NOW MEASURED at D1=3 (the RC-2B input)

The MEASURED column moves to D1=3; the EXPECTED column retires. Items 1/2/5 are
D1-invariant (unchanged from RC-1A/RC-2B).

| # | Gate item | PJM @ D1=3 | MISO @ D1=3 |
|---|---|---|---|
| 1 | Basis | PASS (N-5, D1-invariant) | PASS (D1-invariant) |
| 2 | Instrument | PASS (published vintages, D1-invariant) | PASS-leaning-OPEN (seasonal; provenance M-2 now RESOLVED — §3) |
| 3 | Position | **MEASURED — improves but via the wrong path.** 2025 0.998 (|Δ|=0.009, T-R4 PASS); 2024 no longer overshoots. **But reached via entry-relief + load growth with 0 coal exits** — the position is right, the fleet path is inert. A qualified PASS on the number, OPEN on the mechanism. | **MEASURED — WORSE.** 2025 lengthens 1.035→1.068, shortage now pays $0 (was 24.5) vs 243.3. The one-sidedness deepens. **FAIL/OPEN, degraded from D1=1.** |
| 4 | Skill | **MEASURED — FAIL.** recall 76%→**0%** (regression); false-retire improves (IS-2020 3.0→0.0). "strictly improve recall AND false-retire" fails on recall. | **MEASURED — FAIL.** recall 76%→29%; false-retire 0.874 PASS→**8.643 FAIL** (gas_st inversion). A large regression from the D1=1 near-pass. |
| 5 | Plumbing | PASS (per-ISO gate, D1-invariant) | PASS (D1-invariant) |

**PJM: item 3 measured-PASS (qualified), item 4 measured-FAIL.** The failure mode
INVERTED vs D1=1 (which had item 3 OPEN-overshoot, item 4 recall-PASS). Neither
threshold passes both 3 and 4.

**MISO: items 3 AND 4 measured-WORSE.** D1=3 moves MISO *away* from the flip. The
D1=1 near-pass (item 4 OPEN-leaning-PASS) is destroyed.

**Neither ISO reaches a measured-PASS on both items 3 and 4 under the shipping
configuration. The flip cannot be measured-justified at D1=3.**

---

## 6. LOYO (rule 22) — D1=3 mechanism, leave-one-year-out within 2023-2025

Scorer-side LOYO on the committed ledgers (a sequential coupled evolution cannot be
truly re-solved leave-one-out; this measures whether the D1=3 verdict is *carried by a
single year* — the rule-22 overfitting test). Each fold drops one scored year's model
AND actual retirements.

**PJM** (recall / false-retire):

| fold | D1=1 recall | D1=3 recall | D1=3 false (GW) |
|---|--:|--:|--:|
| full | 0.765 PASS | **0.0 FAIL** | 4.097 |
| drop 2023 | 1.0 PASS | 0.0 FAIL | 4.097 |
| drop 2024 | 0.312 **FAIL** | 0.0 FAIL | 4.097 |
| drop 2025 | 0.75 PASS | 0.0 FAIL | 4.097 |

The **D1=1** recall PASS was *carried by the 2024 wave* (drop 2024 → 0.312 FAIL) —
fragile. The **D1=3** recall FAIL is **robust across every fold** (0.0 everywhere):
the coal-elimination is structural, not a year-artifact.

**MISO** (recall / false-retire):

| fold | D1=1 recall / false | D1=3 recall / false |
|---|--:|--:|
| full | 0.765 PASS / 0.874 PASS | **0.294 FAIL / 8.643 FAIL** |
| drop 2023 | 0.786 PASS / 3.691 FAIL | 0.429 FAIL / 0.000 PASS |
| drop 2024 | 0.846 PASS / 0.006 PASS | 0.000 FAIL / 8.649 FAIL |
| drop 2025 | 0.765 PASS / 0.889 PASS | 0.294 FAIL / 8.643 FAIL |

The **D1=3** MISO recall FAILs in **all three folds**; false-retire FAILs in **2 of 3**
(only drop-2023 passes, because dropping 2023 removes the gas_st wave). The regression
is **robust, not year-carried**.

**LOYO verdict: D1=3 does NOT improve held-out behaviour. It robustly regresses MISO
(recall + false-retire, ≥2/3 folds) and robustly eliminates PJM coal recall (all
folds). Per rule 22 and the charter's step 4, this LOYO degradation is a finding that
BLOCKS the flip — it is not a number to widen.** In-sample-vs-held-out: there is no
in-sample gain to hold out — D1=3 is worse in-sample *and* out-of-fold. The flip may
not ship on unsplit behaviour, and the split confirms the unsplit reading.

---

## 7. Root cause + blockers

1. **NEW BLOCKER — the per-fuel retirement-threshold INVERSION (the dominant D1=3
   finding).** Raising *only* `retirement_years_coal` to 3 while
   `retirement_years_{gas_st,gas_ct,oil}` stay at 2 makes the lower-threshold classes
   the *first-exiting* fossil. On MISO this puts 8.643 GW of gas_st exit ahead of coal
   (gas_st retired **zero** in reality); on PJM coal's oscillating margin never reaches
   3 so *nothing* exits. The R-5 open DOF-ledger rows
   (`retirement_years_{gas_ct,gas_st,oil,gas_cc,nuclear}`, RC-0B §a.4 "consistent-but-
   unidentified, hold pending data") are hereby shown to be **COUPLED to the coal
   threshold**: they cannot stay at 2 while coal is 3 without inverting the exit
   *composition*. **This is a cited, structural root cause (rule 1). It is NOT fixed
   here** — the data to identify the non-coal thresholds is unavailable (GFC/ACR
   reconciliation is RD-4-pending, RC-0B §b), and choosing values to move the residual
   is forbidden (rules 1/13/14). **Filed as an open blocker.** The forward story:
   until the per-fuel thresholds are jointly identified from the deactivation/lag data
   (RC-0B §a.3 method, extended to gas_st/gas_ct/oil), the D1=3 coal threshold is
   internally inconsistent and cannot ship to a flip.
2. **BLK-10 (PJM backstop over-fire) — RE-MEASURED, resolved by D1=3.** The 6.428 GW
   `gas_ct_adequacy_2025` over-fire is gone (gas_ct adds 8.428→0.0) because the wave —
   whose adequacy breach the backstop over-corrected — is eliminated. The gap-register
   row's "re-measure after D1 before any backstop-sizing charter" is satisfied: **no
   backstop-sizing rework is warranted** (the deficit was wave-coupled).
3. **PJM position via the entry side, not exits.** D1=3's position gain is real
   (curve-ON relieves the gas_cc over-build, load growth does the rest) but exposes
   that PJM's exit screen is inert in-window — coal's energy margin covers GFC, so no
   curve position shortens it. This is the §1.1 "residual length is the fleet error"
   made concrete: at D1=3 the fleet-error is a *non-retirement*, and the price is right
   for the wrong reason. Routes to the same fleet-path lane, unchanged.
4. **MISO wind non-response (T-R2b), solar short** — unchanged from RC-1A (BLK-7 /
   RC-0C); D1 does not touch the entry-side VRE terms.
5. **Pre-existing scorer/invariant artifacts** (PJM I3/I7/I12/I14 base-year placeholder;
   MISO I9 storage ε-degeneracy, I12 band) — identical to the committed sidecars, none
   blocks; small scorer-lane cleanup ticket (RC-1A §4.6), unchanged.

**No fix landed.** Per the charter's step 5, the surfaced root cause (item 1) is
structural and cited but its correcting values are not identifiable without RD-4 data,
so it is written up as an open blocker rather than tuned. No code, default, or
parameter changed this session.

---

## 8. Artifacts

- Runs (forecast-validation dashboard only — **never backcast**):
  `pjm-2021-2025-realized-cmc-probe-d1` / `miso-2021-2025-realized-cmc-probe-d1`
  (sidecars `frontend/data/hindcast/*.json`; bundles `results/hindcast/*-cmc-probe-d1/`).
  BEFORE controls (D1-invariant, reused): `*-cmc-before`; D1=1 counterparts: `*-cmc-probe`.
- Reports: `docs/hindcast-reports/{pjm,miso}-2021-2025-realized-cmc-probe-d1-2026-07-16.md`
  (each with raw + IS-2020 tables and the A/B D1=3 context block).
- Pass-2: `validate_capacity_prices.py --pass2-run <ISO>=<-d1 bundle> --pass2-adopted-basis`.
- This findings doc is the ⛔ input for the RC-2B flip re-grade / RC-3A: the MEASURED
  columns of RC-2B §1 move to D1=3; the EXPECTED column retires; the recommendation
  updates to **HOLD both (D1=3 does not unblock; the per-fuel threshold inversion is a
  new blocker)**.

*Produced 2026-07-16 (RC-1A-D1). Two probe legs re-solved at D1=3 (2021/2023/2024/2025
each; 2022 bridged, never solved — rule 22); BEFORE legs reused (D1-invariant); no
holdout year touched; no backcast artifact touched; no default/parameter changed; LOYO
carried. ⛔ input for the RC-2B flip re-grade.*
