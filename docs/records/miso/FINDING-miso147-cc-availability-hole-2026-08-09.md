# FINDING — miso-147: the high-price-hour composition gap is a STANDING ~5–6 GW CC UNDER-DISPATCH, and its identity is an AVAILABILITY DEFICIT — the model's available CC capability sits BELOW what MISO's real CC fleet demonstrably generated

**Session:** miso-147, 2026-08-09, branch `claude/miso-147-dispatch-diagnosis-6in9hz`.
PREREG pushed at `13ece35` (blob `7089dbd8`, verified against the remote, 481 lines)
BEFORE any adjudicating statistic — merged as PR #3785 —
`results/calibration/PREREG-miso147-highprice-dispatch-composition-2026-08-09.md`.
**Posture held: NO LP. NO KEEPER MOVE. NO `ScenarioConfig` FIELD. NO ARM. NO CELL VERDICT.
The licensed keeper replay was NOT spent** (its pre-committed trigger — P-2 indeterminate
within ±10 pp — did not fire; P-2 resolved decisively; the license lapses).
Committed artifacts: `_miso147_{footing,composition,headroom,marginal,january}.json` +
probes `scripts/probes/_miso147_{strata,footing,composition,headroom,marginal,january}.py`.

**Branch verdict: `BRANCH-AVAILABILITY-OBJECT`** (P-1 PASS + P-2 `availability_deficit`,
consistent across both instruments; §6 of the PREREG). Successor named in §7 — an OWNER
DECISION, not armed here.

---

## 0. Footing — all gates PASS before any reading

* **G-F0:** the charter's 2025 monthly table reproduced from the keeper P1 sidecar + the
  miso-137 hourly actual on the C3a weight: all 12 all-hours deficits and all 12
  ordinary-hours deficits within ≤ $0.005 (max |err| $0.0046), all 12 monthly >$200
  counts exact, summing to **88**. The percentages match on the actual-mean denominator
  (no convention notes fired).
* **G-F1:** the six committed window deficits reproduced to ≤ $0.0003 each
  (−4.750 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435).
* **G-F2:** 2025 RT > $200 count = **88** = the C3c ledger footing.
* **G-F3:** universes registered before any subtraction (strata counts + S1 thresholds
  $43.34 / $44.91 / $61.05; model fleet by klass incl. the **17.2 GW / 32 import
  tranches**; CAMPD MISO unit counts + Σp99-gross by family; per-month reporting
  coverage — **no month excluded**, CAMPD 2025 complete through Q4).
* Structural note, stated as declared: with S1 thresholds below $100, **S2 ⊂ S1** —
  every $100–200 hour is also a top-decile-≤$200 hour; strata were analyzed separately
  as pre-registered, never summed.

## 1. P-1 (GATING) — PASS. The S1-2025 composition gap is material, and it is CC-led

Model vs actual supply in the top-decile-≤$200 hours of 2025 (C3a-weighted MW; both
instruments, universes as registered):

* **Pair A (model vs EIA-930, full universe, NET):** gas_total **−7,539 MW** — the only
  fossil delta far above the stratum's BA-identity noise floor (1,964 MW). The model's
  substitutes: coal **+1,977** (material), net_import +1,568, hydro/PS +1,048,
  other/oil/bio +496, wind +483 (each below the noise floor individually).
* **Pair B (model vs CAMPD families, fossil subset, NET):** **CC −5,616 MW** (floor
  1,245; 144 real CC units ON in-stratum), CT −421 (floor 300), ST_GAS −250 and
  ST_COAL −357 immaterial. Cross-instrument closure: Pair-B gas families sum to −6,287
  vs Pair-A gas −7,539; the ~1.2 GW difference is the BTM-CHP + non-CAMPD-gas boundary,
  named in the PREREG.
* **Instrument dependence, reported against interest:** the coal substitution is
  Pair-A-only (+1,977 material) — Pair B reads ST_COAL −357 immaterial (CAMPD-net coal
  runs 2.3 GW above 930 coal in these hours; population/parasitic boundary). The COAL
  leg is therefore quoted nowhere below as a load-bearing number. The CC gap needs no
  such caveat: it is material on both instruments, same sign, same magnitude order.

## 2. P-4 (GATING, scope only) — FAIL. The gap is STANDING, not 2025-specific

S1 CC delta: **−4,959 (2023) / −4,743 (2024) / −5,616 (2025)**. The 2025-specificity
claim is REFUSED: this is a structural, all-years object. **Reported against interest
and led with: 2023 carries nearly the same CC gap as 2025, and C3a-2023 PASSES at
−0.4 %.** The composition defect alone therefore does NOT predict closing the 2025
−14.1 % — what 2025 adds is (a) a deeper summer availability hole (§4), (b) the coal
substitution appearing at material size, (c) the May availability flip (§6), and (d)
2025's higher actual price level amplifying the $-effect of the same MW hole. Any
successor that quotes this finding as "the 2025 fix" has over-read it; it is a real
structural defect (rule 1: it stays in regardless of what it does to the residual).

## 3. P-2 (GATING) — `availability_deficit`, by the pre-registered negative-Δ rule

The prior's direction (model over-runs coal) did NOT obtain — the largest gap is
NEGATIVE (reality ran what the model didn't), so the PREREG §4.3 negative-Δ rule
adjudicates. For CC in S1-2025:

* Model available capability **AV = 22,276 MW** vs reality's realized CC output
  **A = 24,890 MW (net)**: **AV − A = −2,614 MW**. The same sign in every year
  (−1,226 / −1,608 / −2,614). **The model's available CC capability sits below what the
  real fleet demonstrably GENERATED in the same hours** — no outage statistic can
  justify availability below observed output. On top, the real fleet held ~3.6 GW of
  committed headroom (ON units below their p99 ratings), so demonstrated real CC
  capability ≈ 28.6 GW vs model AV 22.3 GW.
* Fleet-scale context (G-F3): model CC pmax **31.9 GW** vs CAMPD CC demonstrated
  ratings (Σ unit p99 gross) **35.4 GW** — up to ~3.3 GW of the hole may be
  population/rating, the rest availability-take (31.9 → 22.3 in exactly the elevated
  hours).
* Secondary component: **E − M ≈ 2.1 GW** of model CC that is available AND in-merit at
  the real price is still not dispatched (LP displacement — imports/hydro/coal at the
  margin, reserve holding; §5's January reading shows the same at larger size).
* Consistency (PREREG §5 nuisance counter-measures): the verdict is corroborated by
  Pair A (gas material, same direction), survives the p95 rating sensitivity (committed
  in `_miso147_headroom.json`), and does not contradict the outage-CSV bound (aggregate
  grain). ST_COAL 2023/2024 S1 (−2.3 / −2.6 GW with E ≈ AV ≥ A) is
  **displaced-in-merit**, not priced out — the mechanical label in the JSON is
  interpreted here as pre-registered arithmetic requires.

## 4. The month-resolved split — the miso-141 connection

`AV_CC − A_CC` by month (2025): positive or ~zero Oct–Mar (Jan +1,318), **negative
Jun–Sep (−2,506 / −2,647 / −2,374 / −1,783)**; the same summer signature in 2024. The
availability half of the hole is **summer-concentrated** — the dispatch-side expression
of the input-side defect miso-141 already measured (the flat `SUMMER_CLASS_DERATE`
re-applying the nameplate→net-summer gap to an already-net-summer base, ~5.8 GW
double-count; cited, not re-derived). `M_CC − A_CC` is negative in **every month of
every year** (−2.0 to −7.3 GW) — so the summer availability hole sits inside a standing
all-months under-dispatch whose non-summer half is commitment/displacement, not
availability.

## 5. Q3 — January 2025 opened, and it DISSOLVES into the same object

The 16 tail hours: reality surged everything — CC to **26,877 MW gross / 143 units ON**
(vs 22,640 in ordinary January hours), CT +2.4 GW, ST_GAS +2.3 GW, coal +3.4 GW. The
model in the same hours: CC **19,087 MW dispatched of 24,688 available** (5.6 GW of
available CC undispatched, in-merit at any tail price), CT over-run +1.9 GW vs reality,
coal 30,660 vs 33,190. The model's winter reserve products held **5,451 MW at dual
0.000 and shortfall 0** in exactly those hours. The charter's four cold-snap
candidates, each measured (×12 months, both signs, `_miso147_january.json`):

* **Gas deliverability / citygate basis — armed and repricing, NOT the driver:** the
  keeper's winter-citygate overlay is ON (PREREG §2(f)); tail-hour gas mc runs p50 $55 /
  p90 $167 / cap-weighted $73 vs an all-hours p50 of $43. The model's gas is expensive
  AND in-merit at tail prices; the shortfall is dispatch, not fuel price.
* **Dual-fuel switching — NOT SUPPORTED:** zero CAMPD gas+oil dual-listed units ON in
  the tail hours; oil-primary ON = 67 MW / 5 units. Reality met the snap without the
  oil switch (proxy limit stated: CAMPD carries no hourly fuel-switch field).
* **Forced-outage rate — NOT SUPPORTED as a model deficit (P-5 prior refuted):** the
  model's implied thermal outage in the tail (27,771 MW) EXCEEDS reality's
  forced+unplanned (22,071) and sits below reality's all-cause take (32,381 + planned);
  system grain is band-consistent, no gross defect either direction.
* **Winter reserve requirement — holds, never binds:** dual 0.0 / shortfall 0 across
  all three families while withholding 5.4 GW.

**January is not a new physics object.** Its tail is the standing CC under-dispatch
(M−A −6.0 GW in Jan-2025, −7.3 in Jan-2023) — here on the COMMITMENT side, since
January's monthly AV−A is positive — plus the ledgered C3c scarcity-tail representation
limit (1/1 SPENT; not re-opened, per the charter its composition only is read).

## 6. Q4 — the May reversal is the SAME object with the expensive substitute

* Composition (S0, May-2025): CC **−3,414** (the hole persists), and the substitute
  flips to **CT +1,374 MATERIAL** — leg (i), fully coverable by reality's recallable
  capacity: the model runs peakers the real market kept OFF. In summer the substitutes
  are cheap (coal/imports at the margin → under-pricing); in May the substitute is
  expensive (CT at the margin → over-pricing). **One object, both signs** — the
  charter's validation demand on any credible root cause.
* Drivers: May AV_CC − A_CC = **+1,074 (2023) / −50 (2024) / −1,201 (2025)** — May
  flipped to overpriced in exactly the year the model's May CC availability fell below
  reality. P-6 splits honestly: leg 1 PASS (May-2025 ordinary clear sits **+$6.29**
  above actual; May-2023 control −$1.11), leg 2 FAIL (the model's May thermal take is
  0.75× reality's all-cause take, not ≤ 0.5× — the aggregate spring-maintenance
  hypothesis is refuted; the CC-specific availability is the supported driver).
* Marginal census corroboration: COAL marginal in 21 % of May-2025 hours (S0) vs 5 % in
  S1 — the model's May margin is set by a more expensive mix than reality's.

## 7. P-3, P-7, P-8 — and what the census adds

* **P-8 (instrument) PASS in all nine stratum-years** (median |p̂ − P1| $0.90–$2.27,
  r 0.886–0.995, miso-144 corrected construction) — every marginal reading above is
  licensed.
* **P-3 is VACUOUS in S1 — zero quantity-agree hours, all years.** CC quantities agree
  with reality in only 127 (2025) / 221 (2023) / 538 (2024) of 8,760 hours, and NEVER
  in the elevated strata: there is no elevated hour in which the model's composition
  matches reality, so the "deficit independent of composition" conditional cannot be
  evaluated. Neither P-3 verdict fires; the vacuity itself is the reading — composition
  disagreement is universal where prices are high.
* **Descriptive census note (not a P-3 verdict):** the model is already marginal on gas
  in 76 % of S1-2025 hours yet clears **$40.7 below actual RT** — the price shortfall at
  matched-gas-margin is the standing queue-item-9 offer-surface object seen from a new
  instrument; nothing here re-opens the refuted offer-LEVEL family (miso-145) and no
  level statistic from the offer corpus is quoted.
* **P-7 (reported, never gating):** S3-2025 echoes S1 — CC −5,597, same signs for the
  top-two families. The tail's composition is the body's, amplified; read under the
  C3c ledger, motivating nothing.

## 8. Successor — NAMED, not armed (OWNER DECISION)

**A MISO CC capability-and-availability lane** (rule 14 measured-input correction with
a forward story; rule 13 line held — an availability INPUT, never a dispatch pin):

1. **The summer availability hole** — repair the `SUMMER_CLASS_DERATE` double-count
  miso-141 measured (which miso-141 already ruled needs a NEW mechanism —
  `cc_nameplate_summer_derate` without one is DO-NOT-REDO), identified against
  multi-year demonstrated summer capability, regenerable for a forward year.
2. **The CC fleet/rating audit** — model CC pmax 31.9 GW vs 35.4 GW demonstrated p99
  ratings: population and rating vintage, EIA-860-side, before any derate question.
3. **The all-months commitment residual** — after (1)/(2), the non-summer half of
  M−A (with AV−A ≥ 0) is a commitment/displacement question (imports, hydro, reserve
  holding at zero dual); OPEN OBSERVATION for the owner, no candidate named beyond it.

Kill-gate discipline for that lane, restated from the PREREG: May 2025 must not worsen
(+12.4 % over, and §6 shows May is availability-sign-coupled), C3b-2025 headroom 0.009,
C3a 2023/2024 PASS margins carried, fail-set ⊆ {C3a}, and §2's against-interest fact
(2023 same gap, C3a PASS) bounds any effect claim in advance.

## 9. Kill gates — untouched, with the reason

No LP was solved, no mechanism armed, no parameter derived: C3b-2025 ≤ 0.200 (0.191,
headroom 0.009) — untouched; C3a 2023/2024 PASS (−0.4 / −6.0 %) — untouched; May 2025
(+12.4 %) — untouched (measured, §6); C1/C2 gated years — untouched (2025 stayed
descriptive vs EIA-930 throughout, per the preliminary-vintage blocker); C8 forced
shares and D-4 windows — untouched; C3c ledger 1/1 SPENT — untouched (S3 read as
composition only; the 88 used as footing only). Fail set remains ⊆ {C3a}. Each is
stated as *untouched*, not as *passing*.

## 10. Duties discharged

Rule 15 — no LP, no run to register (the miso-131…146 precedent). Rule 28(b) — no cell
verdict minted (nothing tested); the §5.4 queue stamp is written in this session with
item 10 SET AND DISCHARGED; items 8/9 stand unmodified (this finding STRENGTHENS item
9's motivation via §7 and hands item 8's universe discipline its Pair-A statement).
Rule 22 — 2023–2025 only. Rules 13/14 — §3/§8 adjudications; the CAMPD comparison
stayed a diagnosis; no measured outcome enters the model. Rule 25 — nothing crossed an
ISO boundary. Probe hygiene — `_miso143_stack.hygiene()` in every entry point.
DO-NOT-REDO honoured: the 88-hour arithmetic (footing only), the *_lw comparator
(consumed, never re-derived), miso-141's derate number (cited), the offer corpus (not
read), CC committed band (not re-measured), CEMS/dispatch bridging (refused at §9 of
the PREREG). Concurrent-session check at open and close: zero MISO PRs, no other live
MISO branch.
