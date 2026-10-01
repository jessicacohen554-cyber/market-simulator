# ADDENDUM to FINDING-spp-51b-2026-09-09-session-b — **every hour-matched number in that finding was computed on the misaligned SPP price clock.** All of them are recomputed here. **Every conclusion holds, and each one is STRONGER on the corrected clock.**

**Lane** SPP-51b session B · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-09 ·
**Base** `origin/main` `ad197380` · **LP spent: NONE** (this addendum, like the finding, is zero-LP).
**Nothing is landed, re-scored or promoted here**; no keeper, sidecar, bench, status or scoring file
is touched.

---

## 0. Why this exists

`FINDING-spp-51b-2026-09-09-session-b.md` merged to `main` at `334b7b63`. Concurrently, lane
**SPP-51c** found — while validating a different instrument — that
`data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`, the committed SPP actual-price sidecar
that C3a/C3b/C3c all score against, **is indexed on UTC while the model's frame is Central
prevailing time**: a 6 h offset in CST months, 5 h in CDT
(`PRECOMMIT-spp-51c-ADDENDUM-2026-09-09.md` §A, routed as **SPP-51c R-1**, direction fixed by
solar-noon / load-peak / GMT-stamped-GenMix markers before any residual was computed).

That addendum carries the consequence through to the **primary** SPP-51b lane's §2. It does not
reach **session B**, which merged separately and whose every model-vs-measured comparison is
hour-matched. **Correcting my own published record is mine to do, so this does it.**

**What is NOT affected, and why.** My model prices are recovered as
`model = committed_actual + lmpDeltaHr`. Because the payload's delta was itself written against the
same misaligned actual, the recovery returns the **true model price** either way — the misalignment
cancels. So every **model-side** result in the finding stands untouched: the wedge itself, the
marginal-class shares, the startup-markup attribution, the min-gen and congestion legs, and the
model-side steepening ratios. What moves is only the **comparison to the measured surface**.

## 1. Alignment gate — reproduced before anything was recomputed

`rt_lw` (the committed actual weighted by the model's own demand — the pairing rubric v2.4 scores
C3a on), against SPP-51c's published values:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| committed / misaligned — SPP-51c | 24.438 | 24.531 | 27.957 |
| **this addendum, misaligned** | **24.438** | **24.531** | **27.957** |
| corrected — SPP-51c | 25.178 | 25.497 | 28.649 |
| **this addendum, corrected** | **25.177** | **25.498** | **28.648** |

Agreement to **0.001 $/MWh** in all three years, on both clocks. My correction is theirs.

## 2. The corrected tables

### 2.1 The load-band decomposition (finding §0.2) — the rotation is much LARGER

Model err %, by system-load percentile. `mis` = as published; `cor` = corrected clock.

| year | | 0–10 | 10–25 | 25–50 | 50–75 | 75–90 | 90–95 | 95–98 | 98–100 | **LW (C3a)** |
|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | mis | +8.5 | +27.8 | +33.6 | +27.3 | +7.3 | −1.8 | −5.9 | −24.3 | +15.05 |
| 2023 | **cor** | **+59.2** | **+56.8** | **+41.4** | **+18.4** | **+2.2** | **−4.2** | **−29.2** | **−49.4** | **+11.65** |
| 2024 | mis | +3.3 | +37.0 | +39.5 | +31.3 | −0.1 | −30.0 | −11.4 | −11.5 | +12.06 |
| 2024 | **cor** | **+82.2** | **+100.1** | **+43.0** | **+25.3** | **+1.3** | **−40.7** | **−45.7** | **−44.8** | **+7.72** |
| 2025 | mis | +8.6 | +26.2 | +35.4 | +15.1 | +13.1 | −8.3 | −9.5 | −14.4 | +14.21 |
| 2025 | **cor** | **+50.9** | **+45.0** | **+38.1** | **+18.6** | **+3.3** | **−27.0** | **−26.5** | **−34.5** | **+11.44** |

**The finding's central claim — "not a level, a rotation" — is not weakened; it roughly doubles.**
The 2024 span goes from ~70 pp (+37 to −30) to **~145 pp (+100 to −46)**. And the rotation now
extends cleanly into the bottom decile (+59 / +82 / +51 %), which on the misaligned clock read
+8.5 / +3.3 / +8.6 % and looked unremarkable. That bottom-decile leg is **the primary lane's missing
sub-\$0 tail, seen on the load axis** — the two records now agree on the same object from two
directions.

The LW column reproduces SPP-51c's corrected C3a (≈ +11.6 / +7.9 / +11.4 %) to within the int16
payload quantization.

### 2.2 The steepening ratio (finding §0.2) — the deficit is much larger

Model side is model-only and **unmoved**; only the measured side is re-derived.

| | measured (as published) | **measured (corrected)** | model, SPP-50 | model, keeper-3 |
|---|---|---|---|---|
| 2023 | 2.0816 | **2.8913** | 1.3611 | 1.3824 |
| 2024 | 1.8949 | **3.0153** | 1.2459 | 1.3298 |
| 2025 | 1.6765 | **2.1741** | 1.1971 | 1.2528 |

The finding's "the rotation deficit **widened** with the SPP-49/48 repairs" rests on the two
model-side columns and is untouched. What changes is the size of the gap it is measured against.

### 2.3 The merit-order identity (finding §0.5) — this **tightens**, and it is the finding's strongest leg

| mid load (25–75 pct) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **merit order on the model's own `mc_base`** (model-side, unmoved) | $20.89 | $21.46 | $24.37 |
| **the LP's own P1 dual** (model-side, unmoved) | $26.81 | $27.07 | $30.82 |
| **the wedge** (model-side, unmoved) | **+$5.92** | **+$5.61** | **+$6.45** |
| actual, as published (misaligned) | $20.60 | $20.09 | $24.90 |
| **actual, corrected** | **$20.92** | **$20.44** | **$24.27** |
| merit vs actual — as published | +1.4 % | +6.8 % | −2.1 % |
| **merit vs actual — corrected** | **−0.2 %** | **+5.0 %** | **+0.4 %** |

**The model's own base-cost merit order reproduces the measured mid-load price to −0.2 % / +5.0 % /
+0.4 % on the correct clock** — tighter than published in two years of three, and within half a
percent in two. The conclusion it carries is unchanged and better supported: **the cost surface a
band multiplier would scale is not the surface carrying the error.**

### 2.4 The fuel channel (finding §0.4) — the refusal gets much stronger

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model's marginal **gas** vs SPP's state delivered reference (input-side, **unmoved**) | −9.5 % | −14.1 % | −29.0 % |
| fuel-only lever to close **mid** — published / **corrected** | ×0.7375 / **×0.7513** | ×0.7520 / **×0.7678** | ×0.8265 / **×0.8027** |
| fuel-only lever to close **top** — published / **corrected** | ×1.2054 / **×1.7487** | ×1.2779 / **×2.1568** | ×1.1703 / **×1.5096** |
| **R-5 Permian arithmetic ceiling vs the mid gap** | $3.16 of $5.88 | $3.89 of $6.64 | $3.03 of $6.56 |

The opposite-signed requirement — the kill — goes from ×0.74 vs ×1.21 to **×0.75 vs ×1.75** in 2023
and **×0.77 vs ×2.16** in 2024. The R-5 ceiling still reaches only **46–59 %** of the mid gap.

### 2.5 The flat multiplier (finding §0.6) — the lever is much further from being able to work

Applied at the strength that would zero the corrected C3a mean:

| year | ×k | 0–10 | 10–25 | 25–50 | 50–75 | 90–95 | 98–100 |
|---|---|---|---|---|---|---|---|
| 2023 | 0.8956 | +59.2 → **+42.6** | +56.8 → **+40.5** | +41.4 → +26.6 | +18.4 → +6.0 | −4.2 → −14.2 | −49.4 → **−54.7** |
| 2024 | 0.9283 | +82.2 → **+69.1** | +100.1 → **+85.8** | +43.0 → +32.7 | +25.3 → +16.3 | −40.7 → −44.9 | −44.8 → **−48.7** |
| 2025 | 0.8974 | +50.9 → **+35.4** | +45.0 → **+30.1** | +38.1 → +24.0 | +18.6 → +6.4 | −27.0 → −34.5 | −34.5 → **−41.3** |

Published, this table left the middle +10 to +25 % dear and the top at −20 to −38 %. **Corrected, it
leaves the bottom +30 to +86 % dear and the top at −35 to −55 %.** The refusal of the rule-1
carve-out channel is not merely preserved; the lever is now visibly further from the shape of the
residual than the finding claimed.

## 3. What this changes in the record

| finding element | status |
|---|---|
| §0.1 "not a level, a ROTATION" | **holds, roughly doubled in span** |
| §0.2 band table | **superseded by §2.1 here** |
| §0.2 steepening, model side | unmoved; measured side superseded by §2.2 |
| §0.3 marginal-class shares, HR, fuel | model/input side — **unmoved** |
| §0.4 fuel refusal | **holds, stronger** (§2.4) |
| §0.5 the wedge and its attribution (markup, min-gen, congestion) | model-side — **unmoved** |
| §0.5 merit-vs-measured | **superseded by §2.3, and it tightens** |
| §0.6 refusal of channels (A) and (C) | **holds on every ground, each stronger** |
| §0.7 C3a/C3b as reported | those are SPP-50's **committed scored** values on the misaligned basis; SPP-51c R-1 owns whether and how they are re-scored — **not this addendum's** |

**No conclusion in the finding is withdrawn or reversed.**

## 4. Scope discipline

This addendum **does not land the clock repair**. SPP-51c R-1 names the locus
(`scripts/data/build_spp_lmp_reference.py` / the `derive_actual_lmp._STD_TZ` seam) and states why it
is a scoring-basis change needing its own pre-registration — it would re-score every registered SPP
run and both keepers' determinations. Nothing here touches `data/raw`, any sidecar, bench, status,
keeper or scoring file. What is recomputed is this lane's own **diagnostic** tables, on the
alignment SPP-51c established and this addendum independently reproduced to 0.001 $/MWh.

**Instruments:** `docs/handoffs/spp51b/clock_recheck.py` (new; the alignment gate and all five
recomputations). The finding's original five instruments are unchanged and still reproduce the
published numbers on the committed basis, which is what makes the before/after comparison auditable.

---

## Log entry

```
## spp-51b session-b ADDENDUM — 2026-09-09 — every hour-matched number recomputed on the corrected SPP price clock; all conclusions hold and each is STRONGER
SPP-51c found (PRECOMMIT-spp-51c-ADDENDUM 5A, routed SPP-51c R-1) that the committed SPP actual-LMP
sidecar is on UTC while the model frame is Central prevailing -- 6 h CST / 5 h CDT. That addendum
carried the consequence through to the PRIMARY SPP-51b lane but not to SESSION B, whose every
model-vs-measured comparison is hour-matched; this addendum corrects session B's own record.
ALIGNMENT GATE FIRST: rt_lw reproduced against SPP-51c on BOTH clocks to 0.001 $/MWh
(misaligned 24.438/24.531/27.957; corrected 25.177/25.498/28.648 vs their 25.178/25.497/28.649).
WHAT IS UNAFFECTED AND WHY: model prices are recovered as committed_actual + lmpDeltaHr, and the
payload delta was written against the SAME misaligned actual, so the misalignment cancels and the
recovery returns the true model price -- every model-side result stands untouched (the wedge, the
marginal-class shares, the startup-markup attribution, min-gen, congestion, the model-side
steepening). ROTATION ROUGHLY DOUBLES: 2024 spans +100.1 % at load pct 10-25 to -45.7 % at 95-98,
~145 pp against the published ~70 pp, and the bottom decile reads +59.2/+82.2/+50.9 % where it
published +8.5/+3.3/+8.6 -- which is the PRIMARY lane's missing sub-$0 tail seen on the load axis,
so the two records now meet on one object from two directions. STEEPENING: measured
2.8913/3.0153/2.1741 corrected (published 2.0816/1.8949/1.6765) against an unmoved model
1.3611/1.2459/1.1971. THE MERIT-ORDER IDENTITY TIGHTENS -- the finding's strongest leg: the model's
own base-cost arrays cleared on merit at its own thermal residual give $20.89/$21.46/$24.37 against
a CORRECTED measured $20.92/$20.44/$24.27, i.e. -0.2/+5.0/+0.4 % (published +1.4/+6.8/-2.1), while
the LP dual sits $5.92/$5.61/$6.45 above -- so the cost surface a band would scale is even more
clearly not the surface at fault. FUEL REFUSAL STRONGER: the opposite-signed requirement goes from
mid x0.74 vs top x1.21 to mid x0.75 vs top x1.75 (2023) and x0.77 vs x2.16 (2024); R-5's Permian
arithmetic ceiling still reaches only 46-59 % of the mid gap. FLAT-MULTIPLIER CONSEQUENCE WORSE: at
C3a-zeroing strength the bottom stays +30 to +86 % dear and the top goes to -35 to -55 % (published
+10 to +25 and -20 to -38). NO CONCLUSION WITHDRAWN OR REVERSED. Does NOT land the clock repair --
that is SPP-51c R-1, a scoring-basis change needing its own pre-registration; no data/raw, sidecar,
bench, status, keeper or scoring file touched. ZERO LP.
FINDING: docs/handoffs/FINDING-spp-51b-session-b-ADDENDUM-2026-09-09.md
```
