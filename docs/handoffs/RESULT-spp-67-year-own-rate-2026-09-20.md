# RESULT — SPP-67. The chartered card died at phase 0. What replaced it is the **FOURTEENTH SPP KEEPER**: a measured input the model applies **6.1× too high in 2019**, excluded by a rule the owner removed.

**Lane** SPP-67 · **Mechanism** `vre_reference_rate_year_own` (NEW, shared gate, dataclass default
`False`, SPP-wind-only provider) · **Pin** `40eeb43adf013114fccc23a90518a3683d5bf377` · **Control**
keeper 13's and its rung's **committed** bundles, differenced, **no control solve** (rule 29(b)
form 4) · **Seven shards, one per year 2019–2025** (rule 36), all pushing full bundles · the parent
ran **no LP**.

**PROMOTED IN-SESSION BY OWNER RULING**, verbatim: *"Is this a recommended keeper candidate? If so
plz promote. If structural integrity improves but gates regress that may still be a keeper."*
Keeper `2026-09-20-spp-67-yearown-rate` + rung `2026-09-20-spp-67-rung-yearown` (stamped to it).
Keeper 13 and its rung pruned in this session (rule 35 `[R-PROMOTE]`).

---

## 1. THE HEADLINE, stated against the lane's own charter

The charter asked whether SPP's modelled wind CF is too high **at source**. On the keeper's own
2023–2025 span the answer is **no**, and that is a falsification, not a hedge: the in-force rate is
within **1.3 %** of each of those years' own published rate, and using each year's own rate makes
**two of the three years worse**.

What phase 0 found instead is in a different place and is larger:

> `_SPP_REFERENCE_RATE_YEARS` is frozen at `{2023, 2024, 2025}` and its own comment gives the entire
> reason — *"the structural rate must never read a validation or locked-test year (SPP's table also
> carries 2019 and 2022 rows, both holdout years, and both are excluded here by construction rather
> than by discipline)"*. **Rule 22 `[R-HOLDOUT]` was REMOVED by owner instruction on 2026-09-09.**

The exclusion now rests on nothing, and it was still suppressing SPP MMU ASOM measurements sitting
**in the same committed table, from the same source documents, on the same average-MW basis**.
SPP's own published 2019 wind curtailment rate is **1.591 %** against the **9.650 %** the model
applied to that year — a factor of **6.1**.

## 2. THE DECOMPOSITION (charter step 1). It closes exactly, and it has one term.

Benchmark basis reproduced first: the scored C1 wind benchmark **is** EIA-930 SWPP `WND` on a
fixed-CST 8760 index with the 2023 corrupt hour screened and Feb 29 dropped — max |diff| **0.013
TWh**, the payload's own 2-dp rounding. Traps (e) and (f) discharged by measurement.

| year | model | bench | **EXCESS** | CAPACITY | **CF LEVEL** | SHAPE | −SPENT | sum-chk |
|---|---|---|---|---|---|---|---|---|
| 2019 | 85.2609 | 77.0300 | **+8.2309** | +0.0000 | **+8.2277** | +0.0000 | +0.0007 | +0.0024 |
| 2020 | 90.6257 | 82.0300 | **+8.5957** | +0.0000 | **+8.7627** | +0.0000 | −0.1787 | +0.0116 |
| 2021 | 101.8115 | 92.8600 | **+8.9515** | +0.0000 | **+9.9177** | +0.0000 | −0.9608 | −0.0053 |
| 2022 | 117.7457 | 107.4400 | **+10.3057** | +0.0000 | **+11.4756** | +0.0000 | −1.1713 | +0.0014 |
| 2023 | 113.2333 | 103.0500 | **+10.1833** | +0.0000 | **+11.0066** | +0.0000 | −0.8227 | −0.0006 |
| 2024 | 120.3667 | 109.3200 | **+11.0467** | +0.0000 | **+11.6750** | +0.0000 | −0.6156 | −0.0126 |
| 2025 | 121.6983 | 110.4600 | **+11.2383** | +0.0000 | **+11.7974** | +0.0000 | −0.5529 | −0.0062 |

**CAPACITY is identically zero** (the bound is `delivered_cf/(1−r) × capacity` and `delivered_cf` is
`delivered_MWh/capacity`, so capacity cancels). **SHAPE is zero on energy** (a scalar factor
preserves the delivered shape; hourly r 0.953–0.973). **CF LEVEL is 100 % of the residual.** The
sum-check — the residual of both claims — is ≤ the benchmark's own rounding in every year.

Mean excess is **+9.7932 TWh**. The charter quotes +10.144, which is SPP-50's number on a
**different keeper**; keeper 13's sync floor spends slightly more headroom. That is the keeper, not
a disagreement.

## 3. THE RATE, per year, with the delivered leg validated before it was extended

Both legs measured, from two independent SPP publications. The delivered leg is re-derived here from
the committed GenMix CSVs and **reproduces SPP-32's committed 2023–2025 rows exactly** (11818.9002 /
12559.0281 / 12583.4630 against 11818.9 / 12559.0 / 12583.5) — that reproduction is what licenses
extending the identical construction to the years it never covered.

| year | ASOM MW | GenMix MW | own rate | own 1/(1−r) | in force | ratio | source |
|---|---|---|---|---|---|---|---|
| 2019 | 137 | 8474.9 | **0.015908** | **1.016165** | 1.106808 | **0.9181** | published |
| 2020 | — | 9337.1 | — | — | 1.106808 | 1.0000 | **NOT published** → reference mean |
| 2021 | — | 10656.2 | — | — | 1.106808 | 1.0000 | **NOT published** → reference mean |
| 2022 | 1260 | 12206.1 | 0.093568 | 1.103227 | 1.106808 | 0.9968 | published |
| 2023 | 1097 | 11818.9 | 0.084934 | 1.092817 | 1.106808 | 0.9874 | published |
| 2024 | 1483 | 12559.0 | 0.105612 | 1.118083 | 1.106808 | 1.0102 | published |
| 2025 | 1382 | 12583.5 | 0.098958 | 1.109826 | 1.106808 | 1.0027 | published |

## 4. WHAT THE ARM MEASURED — against keeper 13's COMMITTED bundle, no control solved

| year | Δwind TWh | Δprice $/MWh (LW) | Δthermal | max \|Δclass\| | max hourly \|Δprice\| |
|---|---|---|---|---|---|
| 2019 | **−6.9825** | +0.3571 | +6.9690 | 6.9825 | 13.4005 |
| 2020 | **+0.0000** | +0.0000 | +0.0000 | **0.0000** | **0.0000** |
| 2021 | **+0.0000** | +0.0000 | +0.0000 | **0.0000** | **0.0000** |
| 2022 | −0.3231 | +0.1492 | +0.3220 | 0.3231 | 42.5805 |
| 2023 | −1.2548 | +0.4801 | +1.2493 | 1.2548 | 43.7320 |
| 2024 | **+1.0920** | −0.2912 | −1.0878 | 1.0920 | 40.9320 |
| 2025 | **+0.2963** | −0.0933 | −0.2927 | 0.2963 | 39.4033 |

Energy is conserved: thermal absorbs the wind one-for-one to ≤ 0.014 TWh in every year.

2019's class split: COAL_PRB **+2.8388**, CC_REGULAR **+3.0032**, COAL_LIGNITE **+0.8052**,
CT_PEAKER **+0.1538**, ST_GAS **+0.0364**, CC_CHP +0.133.

C1 fuel rows where it matters (bench / control / arm):

| year | fuel | bench | control miss | **arm miss** | |
|---|---|---|---|---|---|
| 2019 | wind | 77.030 | +8.231 | **+1.248** | closes 85 % |
| 2019 | coal | 94.120 | −11.272 | **−7.626** | closes 32 % |
| 2019 | gas | 67.500 | +2.441 | **+5.766** | **OVERSHOOTS** |
| 2022 | wind | 107.440 | +10.306 | +9.983 | closes |
| 2022 | gas | 58.610 | −15.290 | −15.215 | closes |
| 2022 | coal | 96.840 | +3.970 | +4.217 | worse |

## 5. THE GATES — they do NOT improve, and that is the honest headline

| criterion | keeper 13 span | **SPP-67 span** | keeper 13 rung | **SPP-67 rung** |
|---|---|---|---|---|
| fuelmix (C1) | PASS | **PASS** | FAIL | **FAIL** |
| sysvol (C2) | PASS | **PASS** | PASS | **PASS** |
| price_mean (C3a) | PASS | **PASS** | FAIL | **FAIL** |
| price_shape (C3b) | PASS | **PASS** | FAIL | **FAIL** |
| price_tail (C3c) | CAVEAT | **CAVEAT** | CAVEAT | **CAVEAT** |
| dispatch_corr (C4) | PASS | **PASS** | FAIL | **FAIL** |
| governance (C6) | PASS | **PASS** | PASS | **PASS** |
| forced_share (C8) | PASS | **PASS** | PASS | **PASS** |
| **determination** | CALIBRATED | **CALIBRATED** | NOT-YET | **NOT-YET** |

Grade 7 of 8, 0 FAILS, 1 ledgered C3c, 0 protective, C1 all 16/16 · free 12/12 — **identical on
both sides**. The rung's failing set is identical member-for-member. **The input improves; the
score does not.** The owner's test — *"structural integrity improves but gates regress may still be
a keeper"* — is met on its easier limb: nothing regresses at the determination level.

## 6. MY PRE-REGISTERED PREDICTIONS, SCORED HONESTLY

From `PRECOMMIT-spp-67-year-own-rate-2026-09-20.md` §5, written and pushed before any shard launched.

| # | prediction | outcome | verdict |
|---|---|---|---|
| P1 | Δwind −6.98 / 0 / 0 / −0.37 / −1.39 / +1.20 / +0.33, band ±20 % | −6.9825 / 0.0000 / 0.0000 / −0.3231 / −1.2548 / +1.0920 / +0.2963 | **RIGHT, 7/7, all inside the band; 2019 to 0.003 TWh** |
| P2 | 2020 & 2021 byte-identical — HARD STOP | every class +0.0000, max hourly \|Δprice\| **0.0000** | **RIGHT, exactly** |
| P3 | Δprice opposite in sign to Δwind, every year | +0.357 / 0 / 0 / +0.149 / +0.480 / −0.291 / −0.093 | **RIGHT on sign, 7/7** |
| P3 | 2019 magnitude **+1.0 to +6.0 $/MWh** | **+0.357** | **WRONG — 3× below my own band** |
| P4 | 2019 split: COAL_PRB +2.0…4.0, CC_REG +1.5…3.5, CT_PEAK +0.2…1.0, COAL_LIG +0.1…0.8, ST_GAS 0…0.5 | +2.839 / +3.003 / **+0.154** / +0.805 / +0.036 | **5 of 6 right; CT_PEAKER missed low** |
| P4 | thermal sum +6.98 ± 0.3 | +6.9690 | **RIGHT** |
| P5 | no C1/C3a/C3b status flip in any keeper year; rung stays NOT-YET | none flipped; rung NOT-YET | **RIGHT** |
| P6 | failure triggers (2020/2021 move; 2019 wind < −5.5; energy to slack/dump) | none fired | **none fired** |

**Two misses, both named.** The price-elasticity band was the bigger one: I assumed a steep stack
near the margin, and 2019 has **zero** negative-price hours (min $4.50), so the displaced wind was
absorbed by coal and CC at low marginal cost and the price barely moved. I also flagged P4's split
as the likeliest to be wrong, and it was the weakest — CT_PEAKER picked up a fifth of my floor.

## 7. WHY IT IS NOT A FITTED LEVER

- It moves **two of the keeper's three years adversely** (+1.0920 TWh 2024, +0.2963 2025).
- **A better-looking arm was available and was refused.** A widened five-year cross-year mean
  (0.0797962 → ×1.086711) moves **every** year favourably and removes ≈13 TWh against this
  mechanism's ≈7.2. It is refused under rule 1 `[R-STRUCT]`: one constant is less accurate than each
  year's own published measurement in every year, and it is the arm that looks better.
- **Rule 21 `[R-DOF]`: zero new free parameters.** DOF ledger **5 entries / 3 residual**, the same
  five names as keeper 13's, machine-confirmed by `build_dof_ledger.py --check`.
  `offer_curve_by_group` SHA-256 **090abd793b5fa5a7**, byte-identical — the rule-1 authorized channel
  was not touched, re-cut or swept.
- **Rule 25 `[R-ISO-SCOPE]`:** `_YEAR_OWN_RATE_PROVIDERS` carries `("SPP","wind")` alone; **0 of 46**
  committed run configs re-key across 9 ISOs, and the armed key is distinct.
- **Rule 13 `[R-MEASURED]`:** forward-native. A forecast year has no published rate, so the provider
  returns `None` and the reference-rate path — unchanged, still *the* forecast methodology — serves
  it. The reader can only fire in a year already published. The objection (a curtailment rate is
  closer to an outcome than a fuel price is) is **real and is answered, not waved away**, in the
  attestation's disclosures.

## 8. G-DRIFT, and why 2020/2021 are worth more than an audit

Nine solve-path files changed between SPP-66's already-validated pin and mine; all classified INERT
for SPP (PRECOMMIT §6 — the one non-comment change is
`coal_takeorpay_from_data=(iso.upper() in ("MISO","NWPP"))`, and SPP is neither). **The measurement
settles it:** 2020 and 2021 — the two years the gate cannot reach — reproduce a control solved at
`f80de3e1` **byte-for-byte**, every class at +0.0000 TWh and max hourly |Δprice| **0.0000**. Form 4
is valid by measurement, not by argument, and it cost nothing.

Reported rather than smoothed: SPP's `solve_surface` fingerprint moved
`7ab7e3b0c4741dc3 → 12114955918da369` on a **182 → 184** row count, with `moved: {}` — zero existing
values changed; the two added rows are names neither recipe consults.

The benchmark side is byte-identical to the control's: `--rebuild-benchmark` reconciles both
composites' `shared_inputs` to `eia930-017f3b3531c0` / `eia923-bfe9ba3670b2` / `campd-85eb94dac24b`,
which are keeper 13's own captures. Every C1 comparison above is like-for-like.

## 9. WHAT THIS DOES NOT CLOSE — carried at promotion, absorbed nowhere

1. **97 % of the benefit is 2019 alone.** The keeper's own 2023–2025 span nets **+0.13 TWh worse**
   on wind. A reader must not take this as a repair of the keeper's C1.
2. **2019's GAS row overshoots**, +2.441 → **+5.766 TWh** against bench. The displaced wind lands
   partly on a class already long.
3. **2020 and 2021 are untouched** — SPP published no curtailment MW for them (verified by grep over
   all three ASOM transcriptions: only the 2019 and 2022 endpoints are printed). Their +8.60 / +8.95
   TWh excess is not addressed, and interpolating would be a free parameter (rule 21) and is refused.
4. **R-bc is not closed.** This changes HOW MUCH headroom exists, never whether the LP spends it.
   SPP still re-curtails a small fraction of its potential; that remains the object SPP-51c
   root-caused.
5. **R-ba (ST_GAS), R-be (the −26.000 floor) and C3c** are untouched.
6. **MISO carries the identical residue.** `_MISO_REFERENCE_RATE_YEARS` is frozen for the same
   stated reason. **Reported, not acted on** (rule 25 / 28(d)) — SPP-67 registers no MISO provider,
   so the flag is inert there even when armed, and whether MISO's own table has pre-2023 paired rows
   is MISO's lane's measurement.

## 10. RETRIEVABILITY AND RETENTION (rules 31 / 33 / 34)

All seven shards pushed **complete** bundles — 16 files each, `dispatch/<y>_P1.parquet` included,
`git ls-tree` verified > 0 before anything was archived.

**What survives is on `main`** (rule 33(f)(4)(ii)): both registered composites
`results/calibration/spp67_yearown_{span,rung}` in their rule-15 slim shape, their registry sidecars
and run payloads, committed on this lane's branch before its PR merges. The **per-year leg dirs are
gitignored and NOT deleted** (rules 32(d) / 31): they stay on this session's disk, and their leg SHAs
are recorded in `.gitignore` as **provenance only** — a shard branch is transport, not storage, so
any leg recovery is costed as a **re-solve** (~5 min/year).

`check_registry_payload_parity.py` is RED locally on exactly those seven gitignored dirs and nothing
else — trap (l), expected, and green in CI, which checks out only what is committed.

One shard (the first 2021) stopped mid-solve with its container unreachable and no message tool
available to nudge it; 2021 was re-solved in a fresh shard (`claude/spp67-2021b`) at the same pin.

## 11. WHAT A SUCCESSOR SHOULD TAKE FROM THIS

**Search the codebase for other constraints justified by `[R-HOLDOUT]`.** This defect was not a
modelling error — it was a governance rule's footprint left behind after the rule was deleted, still
narrowing what a measured input was allowed to read. `_MISO_REFERENCE_RATE_YEARS` is one more; a
grep for "training-window", "holdout" and "`#22`" under `src/` finds others, and each is a rule-14
question its own ISO's lane should ask.

**And the SPP wind object is now correctly named.** It is not the rate and not the shape: it is that
**nothing in the LP refuses wind bid at −$26/MWh below every thermal offer**. That is R-bc, it
survived this lane intact, and it is where SPP's remaining ~8–12 TWh/yr lives.
