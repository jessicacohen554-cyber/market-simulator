# FINDING — caiso-170: **S2 IS REFUTED FOR ITS OWN OBJECT, BY MEASUREMENT.** The real CAISO battery fleet already captures **90.7–92.2 %** of the perfect-foresight ceiling, the model beats it by **+0.002/+0.024/+0.016** — so there is essentially **no foresight rent for a second settlement to remove**. Lever-queue **item 3 is SPENT**, and with it the **CAISO in-model lever queue is EMPTY**. The over-position is re-pointed to a **within-day PLACEMENT** object that is neither a bound (the armed anchor is slack ~20×) nor a foresight one. Separately: the prompt's stated **PRECONDITION was AHEAD OF THE REPOSITORY, not wrong** — the caiso-166 promotion landed mid-session at PR #3514 with the owner ledgering C3a-2024, and the verdict is re-measured on the new keeper and **UNCHANGED**. NO LP, NO SOLVE, NO DERIVE, keeper not changed BY THIS SESSION (2026-08-04)

**Session** caiso-170 · **Date** 2026-08-04 · **Branch**
`claude/caiso168-calibration-continuation-adaqwy` · **Base** `bd9795ca`

> **Lane numbering.** This lane opened as **caiso-169** and its pre-registration
> was pushed and merged under that id (PR #3517). A **parallel session** took the
> same queue item concurrently and landed first (PR #3525,
> `FINDING-caiso169-storage-foresight-horizon-2026-08-04.md`, whose own
> calibration-log entry signs off *"Next number: caiso-170"*), so `caiso-169` is
> **SPENT** and this lane renumbers to **caiso-170** — the caiso-167 precedent.
> The precheck file is renamed with it; its content is unchanged and its push
> still predates every value in it.
>
> **THE TWO SESSIONS AGREE AND ARE COMPLEMENTARY — read them together.** They
> attacked item 3 from opposite ends and neither result depends on the other:
> * **caiso-169 refused S2's CHEAP SUBSTITUTE** — the already-built
>   `storage_daily_cycling` 24 h SOC pin — on *reach* (its only ν-break is local
>   midnight, and 0 of 365 touched SOC hours fall inside the caiso-127 pinned-day
>   coupling) and on *premise* (the measured fleet banks across days at sd
>   2,482/3,685/4,029 MWh/day, so a hard 24 h cycle is "a different wrong of the
>   same size"). It concluded S2 **proper** is an owner charter and left item 3
>   **LIVE**.
> * **caiso-170 (this session) measures whether that charter has anything to
>   buy**, and it does not: the real fleet already captures 90.7–92.2 % of the
>   perfect-foresight ceiling and the model beats it by ~2 pp.
>
> caiso-169 established that the horizon family's only two non-fitted values are
> 24 h and ∞ with the fleet strictly between them, reachable "only with an
> explicit uncertainty representation". **This session prices that
> representation's upside at ≤ 2 pp of a ceiling the fleet is already at**, which
> is what closes item 3 rather than merely bounding it. Neither session alone
> does: caiso-169 left the charter standing, and caiso-170 alone would not have
> refuted the cheap substitute on its own reach.
**Prereg** `results/calibration/PRECHECK-caiso170-s2-foresight-phase0-2026-08-04.md`,
pushed **before any value in it existed**.

**CAISO keeper** `2026-08-04-caiso-166-measured-dlap` (CALIBRATED-WITH-CAVEATS,
2 of 3 ledgered non-protective slots, 0 FAILs) — **promoted independently
mid-session** by the caiso-166/167 continuation lane (PR #3514), **not by this
session**. Measurement began on the then-incumbent
`2026-08-04-caiso164-zonal-loss-surface` and was **re-run on the new keeper**;
the verdict is identical (§3a). No mechanism was armed, no `ScenarioConfig` field
was added, no derive was run, nothing was registered on the dashboard.

**Method** one command, committed artifacts only, no LP anywhere in it:

```
python scripts/probes/caiso170_s2_foresight_phase0.py
```

Artifact: `results/calibration/_caiso170_s2_foresight_phase0.json`.

---

## §0 — the one-paragraph result

`FINDING-caiso129` §5 named **S2 — the DA/RT two-settlement separation, "the
LP's single-market perfect-foresight arbitrage itself"** — as the last surviving
candidate for the evening/overnight storage over-position, and required it be
chartered separately rather than approximated. This session measured the prior
question that charter rests on and **it does not hold**. Scoring the model's
battery dispatch and the **measured** battery fleet's dispatch on the **same**
measured price series, the model's discharge-MWh-weighted within-day price
percentile beats the real fleet's by **−0.014 / +0.019 / +0.007** on RT — 0 of 3
years clear the pre-registered **0.10**, and the largest value is an order of
magnitude short. The energy-neutral form agrees: against each series' **own**
perfect-foresight ceiling (same energy, same power profile, only the order of
hours changed), the **measured** fleet already achieves **0.922 / 0.917 / 0.907**
and the model **0.924 / 0.941 / 0.923** — a gap of **+0.002 / +0.024 / +0.016**.
**The real fleet, which does face a DA/RT split, already behaves within ~2 pp of
perfect foresight**, so removing the model's foresight cannot recover a rent that
is not being paid. F1 is IMMATERIAL and **item 3 is SPENT**. F2 *is* material
(mean within-day DA/RT Spearman **0.813**, so the two settlements genuinely do
order the day differently) — and that is precisely what makes the refutation
strong rather than a null: the separation the mechanism would represent **is
real, and the fleet is not losing anything to it.**

---

## §1 — THE PRECONDITION WAS AHEAD OF THE REPOSITORY, AND IT RESOLVED MID-SESSION

**What this session found at open** (recorded in PRECHECK §0 *before* any
measurement, and left on the record unaltered). The dispatching prompt asserted
the CAISO keeper was `2026-08-04-caiso-166-measured-dlap` at
CALIBRATED-WITH-CAVEATS / 0 FAILs, that `AMENDMENT-caiso166-S3-recharter` existed
and that the caiso-166 branch might still be open. None of it was in the
repository: the keeper was `2026-08-04-caiso164-zonal-loss-surface`, the
amendment was absent, the branch was deleted, and PR #3506 had merged only the
finding, the registration and the matrix cell. Re-verified from committed
artifacts with `scripts/calibration_verdict.py` (no solve), Arm A scored
**NOT-YET** — "undocumented out-of-tolerance (FAIL) criteria: `price_mean`"
(C3a 2024 **+11.5 %** against ±10 %; the then-ledgered exception covered **2025
only**).

**So this session did not promote**, on rule 22 D-5(b): a re-verified
determination that is *worse* stops a promotion and escalates to the owner.
`FINDING-caiso166` §4 had pre-stated the same blocker, and named the only
resolution — ledger the 2024 miss, an explicit **owner act on its own evidence**
(the caiso-145 pattern).

**And that is exactly what happened, independently and in parallel.** The
caiso-166/167 continuation lane landed the owner's decision on `main` while this
session was measuring:

* `89be6559` — `AMENDMENT-caiso166-S3-recharter-2026-08-04.md`, the owner's
  gate-S3′ re-charter, **pushed before the attestation generator was re-run**;
  its §4 **ledgers the 2024 `price_mean`** on measured grounds (losses consume
  MWh so λ *must* rise; CAISO was already +9.5 % hot with the control 0.5 pp
  inside the band; on CAISO's own **day-ahead** basis — the basis the surface is
  *derived* on — the arm sits **+1.8 %** in 2024);
* `7141ae46` — the promotion; `e7955858` — the calibration-log entry; merged as
  **PR #3514**.

**Re-verified here after rebasing onto that main**, from committed artifacts
only: `2026-08-04-caiso-166-measured-dlap` → **CALIBRATED-WITH-CAVEATS**, C3a
2024 **+11.5 %** and 2025 **+14.4 %** both `[ledgered]`, C3c ledgered, **0
FAILs**, C1/C2/C3b/C4 and protective C6/C7/C8 all PASS; `audit_keepers --iso
CAISO` **PASS, 0 failures / 0 warnings**. The prompt was describing a state that
had not yet landed, not a state that was wrong.

**This session's own S3′ amendment draft is WITHDRAWN.** It was written from the
prompt's description as a reconstruction; the owner's own document is the real
act, was pushed before the generator re-ran, and covers the 2024 ledger the
reconstruction did not. On rebase the reconstruction was dropped and the owner's
retained — there is exactly one amendment document.

**`FINDING-caiso166` §5 is CLOSED by the promotion.** The inconsistency that
session flagged — `CAISO_loss_surface.csv` is a shared LP input, so an unpromoted
Arm A left the designated keeper unable to reproduce from the repository — is
resolved in the way §5 itself named as natural: Arm A *is* that keeper's recipe
re-solved on the corrected data, and it is now the keeper.

## §2 — the object, and the statistic

The object is `FINDING-caiso127` §2's storage pin (192/197/276 of 365 days),
which that lane calls "the whole compression" of the evening/overnight price
shape. caiso-129 closed every *shaped-floor* instrument against it and left S2.
caiso-168 shut the **belly** route into item 3 and left S2 standing here.

**The statistic is a within-day price percentile**, `(rank − 0.5)/24` on each
local day's own 24 hourly prices, weighted by that fleet's dispatch MWh. It is
level- and scale-free by construction: a fleet gets no credit for a dear day,
only for placing energy in *its own day's* dear hours. Both fleets are scored on
**the same measured prices**, so the comparison carries no endogenous-price
confound.

**Basis, and it is like-for-like.** The model limb is `li_ion` only; the measured
comparator is EIA-930 CISO `NG: OTH`, which **excludes pumped storage by
construction** — the same re-basing caiso-168 §H had to apply to caiso-121's
storage row. Pumped storage is kept strictly separate throughout (§6).

**The volume confound is measured, not assumed away.** Annual discharge energy,
model vs measured: **4,023 / 4,024**, **7,637 / 7,586**, **11,308 / 11,255** GWh
— ratios **1.00 / 1.01 / 1.00**. The two fleets cycle the same energy, so a
percentile comparison between them is not diluted by one reaching further into
mid-priced hours than the other.

**The statistic is self-checked before it is used** (stage A). The model's own
dispatch scored on the model's **own** dual must sit near its ceiling, because
the LP put it there with perfect foresight over all 8,760 hours. It does:
capture efficiency **0.978 / 0.983 / 0.981**. A statistic that failed this would
be measuring nothing.

---

## §3 — F1: THE FORESIGHT ADVANTAGE IS NOT THERE

Discharge-MWh-weighted within-day price percentile, both fleets, same prices:

| year | settlement | model | measured | **advantage** |
|---|---|---:|---:|---:|
| 2023 | RT | 0.785 | 0.799 | **−0.014** |
| 2024 | RT | 0.777 | 0.758 | **+0.019** |
| 2025 | RT | 0.733 | 0.727 | **+0.007** |
| 2023 | DA | 0.852 | 0.844 | +0.007 |
| 2024 | DA | 0.854 | 0.814 | +0.040 |
| 2025 | DA | 0.828 | 0.798 | +0.030 |

Pre-registered gate: **≥ 0.10 on RT in ≥ 2 of 3 years**. Realised: **0 of 3**,
maximum **+0.019**. In 2023 the model is *worse* timed than the real fleet.

**The energy-neutral form agrees, and it is the stronger statement.** Capture
efficiency `(achieved − floor)/(ceiling − floor)`, where the ceiling re-places
each series' **own** hourly dispatch magnitudes into its own day's best-ordered
hours and the floor into the worst — same energy, same power profile, only the
order changes:

| year | settlement | model eff | **measured eff** | gap |
|---|---|---:|---:|---:|
| 2023 | RT | 0.924 | **0.922** | +0.002 |
| 2024 | RT | 0.941 | **0.917** | +0.024 |
| 2025 | RT | 0.923 | **0.907** | +0.016 |
| 2023 | DA | 0.972 | **0.970** | +0.001 |
| 2024 | DA | 0.987 | **0.942** | +0.046 |
| 2025 | DA | 0.984 | **0.962** | +0.022 |

**This is the finding.** The real CAISO battery fleet — which faces exactly the
DA/RT two-settlement structure S2 would represent — already captures **90.7–
97.0 %** of what a perfect-foresight operator would capture with the same energy
and the same power profile. **The foresight rent S2 exists to remove is
2 percentage points wide on RT.** A structural second settlement in the LP
cannot recover a loss the real fleet is not incurring.

---

### §3a — the verdict is ROBUST to the keeper change, and this is measured, not asserted

The measurement opened on `caiso164_zonal_loss_surface` and was re-run on the
promoted `caiso166_measured_loss_zones` bundle after rebasing (§1). Both runs
are reproducible from the committed probe:

```
python scripts/probes/caiso170_s2_foresight_phase0.py                       # current keeper
python scripts/probes/caiso170_s2_foresight_phase0.py \
    --bundle results/calibration/caiso164_zonal_loss_surface/hourly         # prior keeper
```

**Both verdicts are identical — F1 IMMATERIAL, F2 MATERIAL.** The F1 RT
discharge advantage moves by **≤ 0.0004** (2023 −0.0141 → −0.0141, 2024 +0.0192
→ +0.0194, 2025 +0.0066 → +0.0070); **F2 does not move at all**, because it is
computed entirely from measured DA/RT prices and never touches model output.
2023 is **bit-identical** between the two bundles — the caiso-166 placebo year,
whose surface rows are the same in both arms. What does move is the model's
storage volume in the two later years (li_ion discharge −0.4 % / −1.0 %), which
is the loss surface's own level effect and is far too small to approach either
gate. **The refutation does not depend on which keeper carries it.**

## §4 — F2: the separation IS real — which is what makes §3 a refutation and not a null

| year | mean within-day DA/RT Spearman | p25 | p50 | p75 | mean DA spread | mean RT spread | RT/DA |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | **0.849** | 0.831 | 0.894 | 0.930 | $91.21 | $90.87 | 1.00 |
| 2024 | **0.822** | 0.768 | 0.870 | 0.917 | $65.51 | $65.97 | 1.01 |
| 2025 | **0.769** | 0.734 | 0.804 | 0.875 | $44.63 | $55.71 | 1.25 |

Mean **0.813**, inside the pre-registered `≤ 0.90`. **F2 is MATERIAL**: CAISO's
two settlements really do rank the day's hours differently, and increasingly so
(0.849 → 0.769 across the window, with RT offering 25 % more within-day spread
than DA by 2025).

So the refutation is not "there is no two-settlement structure to represent" —
there plainly is. It is the sharper statement: **the structure exists, and the
real fleet is nonetheless landing its energy within ~2 pp of the ceiling.**
Whatever CAISO's storage operators are doing about DA/RT divergence, they are
not paying a timing penalty a perfect-foresight LP would avoid.

---

## §5 — WHERE THE DEFECT ACTUALLY IS: a within-day PLACEMENT object, and it is neither a bound nor foresight

Mean MW/h by window, model `li_ion` vs measured battery:

| year | window | model dis | meas dis | excess | model chg | meas chg | excess |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | belly | 3 | 22 | −19 | 1,564 | 1,205 | **+359** |
| 2023 | evening | 1,785 | 1,655 | **+130** | 0 | 4 | −4 |
| 2023 | overnight | 165 | 140 | +25 | 23 | 190 | **−167** |
| 2024 | belly | 1 | 10 | −8 | 3,111 | 2,931 | **+179** |
| 2024 | evening | 3,382 | 2,704 | **+678** | 5 | 78 | −73 |
| 2024 | overnight | 407 | 635 | **−227** | 36 | 195 | **−159** |
| 2025 | belly | 1 | 12 | −12 | 4,687 | 4,425 | **+262** |
| 2025 | evening | 4,600 | 3,698 | **+902** | 9 | 147 | −138 |
| 2025 | overnight | 823 | 1,129 | **−306** | 16 | 165 | **−149** |

Two things to record, both corrections to how this object has been framed.

**(a) The "overnight OVER-position" reverses sign in 2024 and 2025.** On a
like-for-like battery basis the model is **UNDER** overnight discharge by
**−227 / −306 MW/h** in the two later years, and over only in 2023 (**+25**).
Adding the PS limb does not change the direction (2024: 586 vs 635; 2025: 985
vs 1,129 — still under). *This does not refute `FINDING-caiso127` §2, which
measured a **pin** statistic (days on which storage is pinned), not a window
volume; it is a different measurement and is reported as one.* But any successor
scoping itself to "remove overnight discharge" should read this table first.

**(b) The real shape is a CONCENTRATION.** The model buys too much in the belly
(**+179…+359 MW/h**), buys almost nothing overnight (**−149…−167**), and sells
too much in the evening (**+130…+902**). Same annual energy (§2), different
placement within the day.

**And that placement is NOT a bound.** The armed `caiso_storage_shape_anchor`
caps a battery row's charge at `env_p95_chg[hod] × power_cap`, so the rule-19
question is whether the anchor already owns this. Measured on the keeper's own
bytes:

* the anchor's p95 charge fraction is **exactly 0.00** in hod 17–21 (2023),
  18–22 (2024), 18–23 (2025) — a hard prohibition — **but that is not where the
  deficit is**: the measured fleet places only **0.2 / 0.3 / 0.4 %** of its
  annual charge in those hours, and **0.0 / 0.0 / 1.3 %** of its *overnight*
  charge;
* in the **2,920 / 2,555 / 2,190** overnight hours whose cap is **live**, the
  model charges **23.3 / 40.8 / 21.8 MW** against a bound of
  **632 / 803 / 833 MW**, and is at that bound in **1.4 / 0.7 / 0.6 %** of them.

**The bound is slack by more than an order of magnitude.** The model is not
forbidden to charge overnight — it *chooses* the belly. Combined with §3, the
object is therefore neither a foresight defect nor a bound defect: it is a
**within-day price-shape / representation** object. The pointer this session
hands forward, explicitly **as a pointer and not a verdict** (the caiso-167 §7
discipline), is that the model carries the battery fleet as a small number of
**aggregated** columns with pooled power and energy, so nothing forces it to
spread charge the way a fleet of individually duration-limited resources must.
**That is untested here and is not claimed.**

---

## §6 — the PS limb, kept separate

| year | limb | annual dis GWh | annual chg GWh | evening MW | overnight MW |
|---|---|---:|---:|---:|---:|
| 2023 | li_ion | 4,023 | 4,733 | 1,785 | 165 |
| 2023 | pumped_storage | 1,898 | 2,372 | 734 | 112 |
| 2024 | li_ion | 7,637 | 8,984 | 3,373 | 406 |
| 2024 | pumped_storage | 2,085 | 2,606 | 765 | 179 |
| 2025 | li_ion | 11,308 | 13,304 | 4,588 | 822 |
| 2025 | pumped_storage | 2,055 | 2,569 | 786 | 162 |

Pumped storage has **no measured hourly comparator** — EIA-930 `WAT` mixes it
with conventional hydro (caiso-141) and `NG: OTH` excludes it outright. It is
the owner-ledgered **C3a-2025 wall** (accepted caiso-145). **Reported, never
approximated**, and no PS statistic in this document is compared to an actual.

---

## §7 — matrix repairs made this session (rule 28 duty b)

* **`caiso_da_rt_two_settlement` CAISO → `R`** — new row, this finding. Refused
  on **measured reach**, the caiso-167 `caiso_seam_loss_surface` pattern: the
  mechanism is real and its structure is real (F2), but the rent it targets is
  ~2 pp wide (F1/§3). **Item 3 is STRUCK.**
* **Lever-queue item 9's stale text — struck by the concurrent caiso-169 lane,
  independently found here, and this lane defers to their (fuller) strike.
  The cost is recorded because only this lane paid it:** caiso-170 started the
  ~2 h OASIS corpus fetch to redo the closed work before reading
  `FINDING-caiso153`; the fetch was abandoned and the partial corpus deleted.
  A stale queue entry cost a session most of an hour — exactly what rule 28's
  DO-NOT-REDO discipline exists to prevent. What caiso-153 had found: it is
  **SPENT AND PROMOTED at caiso-153** (`FINDING-caiso153-offer-classifier-reid-2026-08-02.md`: the
  gas-coupling classifier was re-identified — the defect was the **estimator**
  (OLS leverage on the Jan-2023 citygate spike), not the body probe; all four
  frozen gates PASS, reproducibility restored, and the re-derived surface became
  the keeper). Left standing it would have sent a session to redo closed work —
  and this session began by starting the ~2 h OASIS corpus fetch to do exactly
  that before reading caiso-153. **Established by reading, before any
  measurement.**

**With item 3 closed by the two concurrent sessions together and item 9 struck,
the CAISO in-model lever queue is EMPTY.** Items 1/4/5/6/7/8 were already discharged, refused or promoted; item 2
was closed on both halves at caiso-167. This is stated plainly because it is the
lane's actual status, and the honest successor is a **data-blocker or owner
decision**, not another lever:

* **Arm B (intra-SP15 transfer limit)** — no published physical limit in
  `data/raw`. **FILED, not approximated**; caiso-165/166 measured the corridor's
  separation precisely, which binds the prohibition **harder** (rule 13).
* **C3a-2025** — non-public hourly pumped-storage data (caiso-141 A2 wall).
* **C3c-2023/24** — the SoCalGas OFO declaration record.
* ~~The `FINDING-caiso166` §5 keeper-reproducibility inconsistency~~ —
  **CLOSED** by the caiso-166 promotion (§1).

---

## §8 — DO-NOT-REDO (new, binding)

* **Re-testing S2 / a DA-RT two-settlement separation against the
  evening/overnight storage object.** §3 measures the rent at 2 pp on a fleet
  that already sits at 0.907–0.922 of its own ceiling. Re-scoping the window,
  re-cutting the percentile statistic, or re-running it on the PS limb does not
  change the arithmetic; a *new* object (not this one) would be new evidence.
* **Re-cutting F1's 0.10 or F2's 0.90 after the fact.** Both were pushed before
  any value existed. `FINDING-caiso166` §3's lesson is inherited: a gate re-cut
  after it fires is an answer key.
* **Quoting the "overnight over-position" without §5(a).** On a like-for-like
  battery basis the model is *under* overnight discharge in 2024 and 2025.
* **Proposing a second charge-side cap for the belly over-charge.** The channel
  is the armed `caiso_storage_shape_anchor` (rule 19), and §5 shows its
  overnight limb is *slack*, so the defect is not reachable by tightening it —
  and re-picking its percentile against this residual is barred by rules 13/23
  (caiso-168's standing ruling, unchanged).
* **Re-deriving `caiso-storage-shape-envelope.csv`.** Read here, never
  re-derived; rule 23 licences re-derivation only on a source-data change.

Carried forward unchanged: every DO-NOT-REDO in `FINDING-caiso129` §6,
`FINDING-caiso152` §H, `FINDING-caiso167`, `FINDING-caiso168`, and the caiso-166
Arm B prohibition.

---

## §9 — governance

* **No solve, nothing registered.** No LP was built and no year was solved, so
  there is no bundle and no dashboard registration (the
  caiso-136/143/144/149/150/167/168 pattern). Rule 15 is not engaged.
* **This session changed no keeper and made no promotion.** The keeper advanced
  `2026-08-04-caiso164-zonal-loss-surface` →
  **`2026-08-04-caiso-166-measured-dlap`** independently, by the caiso-166/167
  continuation lane's owner-authorised promotion (PR #3514), while this session
  was measuring; caiso-170 rebased onto it, **re-verified its determination from
  committed artifacts** (CALIBRATED-WITH-CAVEATS, 0 FAILs, `audit_keepers` PASS)
  and re-ran the probe against it (§3a).
* **No `ScenarioConfig` field, no flag, no derive, no re-derive.**
  `CAISO_loss_surface.csv` was not touched; the caiso-153 offer surface was not
  re-derived; the partial OASIS corpus fetched before caiso-153 was read was
  deleted unused.
* **Rule 22.** CAISO holds **no** `complete` marker and the holdout spend freeze
  is ACTIVE. Only 2023 / 2024 / 2025 were read; **no marker was written** and no
  out-of-training year was solved, scored or touched.
* **Rule 25 `[R-ISO-SCOPE]`.** Every number here is CAISO's own, from CAISO's own
  disclosures; nothing is transferred to or from another ISO's cell.
