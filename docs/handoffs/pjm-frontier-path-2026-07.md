# HANDOFF — the path from PJM CALIBRATED to PJM FRONTIER (2026-07-26)

**Status going in:** PJM keeper `2026-07-25-pjm-121-cc-belt` is **CALIBRATED,
10/10** — PJM's first all-pass determination. It carries **no frontier block**
(`frontend/data/backcast/keepers/PJM.json` has `keeper` / `promotion_note` /
`note` only). Frontier holders today: **NEISO** and **NYISO** (both 2026-07-11).
ERCOT's stale block was removed 2026-07-26 (declared and withdrawn the same day
by the ERCOT-79 audit; lineage preserved in its `promotion_note`).

**Frontier is owner-declared and purely declarative.** No session may set it.
`build_status.py:494–501` attaches `verdict["frontier"]` *after* `determine()`
runs, for a badge and note on the Calibration Status page — it never gates and
never touches the verdict.

---

## 1. The bar, stated exactly

From `docs/codebase-site/calibration-rubric.html` §frontier:

> Every named admissible mechanism for the ISO's residual caveat family has
> been tried **on record**, and what remains is either **inadmissible to close**
> (residual-fitting, rule 26) or **blocked on data that does not exist
> publicly**.

Both current holders earned it the same way: every hard and volume criterion in
band, the entire remaining residual is the C3c price scarcity tail, and the
tail is gated by reserve dynamics the real ISO either has not implemented or
that would need new measured identification.

* **NEISO** — four named mechanisms tried on record; the real tail forms while
  the model still carries GW of cheaper non-fast-start headroom, so no
  repricing of the fast-start band reaches it.
* **NYISO** — the deep >$300 tail's two candidate reserve levers chased to
  ground; the sole remaining gap (IMM Rec. 2021-1 net-load forecast-uncertainty
  reserve) has no published formula, so adding it would be residual-fitting.

PJM clears the first half of that bar already (10/10). What frontier needs is
the **ledger**: the enumeration, tried on record, of what owns the remaining
residual.

## 2. PJM's ledger — what is already closed

Reserve/scarcity lanes (`docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3):

| lane | result | disposition |
|---|---|---|
| Post-solve two-step ORDC overlay (arch. A) | fires 8/20/5 h, overshoots ($850-class vs the $75–200 need), cannot make the sub-shortage $50–105 component | retired to diagnostic; **inadmissible** in the keeper line (would stack on the live co-opt, rule 19) |
| Zone-aggregate co-opt scoping | reserve price $0 in all 26,280 h (deliverable cap ~50 GW ≫ 3.4 GW req) | empirically refuted |
| Per-gen class-tier co-opt, measured ramp (arch. B) | fires 1 h / 3 yr ($46.47) | **live in the keeper — the sole reserve-price owner** (rule 19) |
| SYNC product / size split | duals in the correct regime but $0–10 vs the $75–200 need | **owner-CLOSED 2026-07-11** |
| Commitment posture (Phase 1) | G-P1 FAIL all years, model online headroom 2.66–3.14× the measured target; tail unchanged | REJECTED — root cause is **LP-vs-MIP**, a representation boundary under the no-MIP mandate |
| DA demand depth + measured offer levels (G-22) | moved 2025 C3c 0 → 17 h, fixed C1/C3a/C3b/C7 | **in the keeper** |
| **`ramp10` scoped to committed-and-online (Lane 1 framing 2)** | **no-LP pre-check, all 3 years: rigorous lower bound stays 9.7–10.5× the requirement; reduction only 13.6–15.9 %, and smallest (8–10 %) in the TIGHTEST net-load quartile** | **CLOSED pjm-124 — INERT, no solve spent** (`docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`) |
| **constrained commitment before the reserve bound (Lane 1 framing 1)** | **no-LP pre-check, all 3 years: DOES bite — 51–53 % reduction, and hardest (40–43 pp) in the TIGHTEST quartile — but the commitment-invariant floor stays 5.0–5.6× the requirement** | **CLOSED pjm-125 — PARTIAL (effective but insufficient), no solve spent** (`docs/FINDING-pjm125-commitment-constraint-precheck-2026-07.md`) |

Offer/energy-stack lanes:

* **`pjm_reserve_pergen_sync`** — settled on **direct evidence**, not by the
  A/B arm (which OOM-killed in the P1 warm-start at ~15 GB). pjm-120 §6.1 reads
  the keeper's own persisted reserve dual: **22 nonzero hours of 8,759, 0 hours
  ≥ $300, 0 ≥ $850, max $210.99**. At the worst hour (h4193, PJM printed
  $1,722, 896 MW short on Synchronized) the model's dual is $210.99. The
  balance never leaves the sub-shortage regime, so a second ORDC curve over
  ~10× slack cannot move C3a. **Closed on merit — the OOM is irrelevant.**
* **B.4 leg A (`gas_daily_shape`)** and **leg B (`CC_LIKE` mid-curve)** — both
  now **live in the keeper** (leg B is the pjm-121 promotion itself).
* **`gas_offer_margin_anchor`** — refuted, pjm-120 §1.
* **The entire measured-offer-surface family as a dispersion lever** — refuted
  pjm-123 (`docs/FINDING-pjm123-composite-precheck-2026-07.md`), **but that
  generalization is NARROWED by pjm-126 (2026-07-26) and the family is a live
  lever again.** pjm-123's legs 1/2/3 A/B results stand. What does not stand is
  the basis for generalizing them: the "every segment cheapest in the tightest
  bin" inversion is a **conditioning artifact**, reversing sign under
  within-season net-load ranking (CT_FAST +10.00 → −0.85, CC_LIKE +0.35 →
  −0.20). See `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md`
  and the Lane 2 update in §3. **CONFIRMED multi-year by pjm-127 (2026-07-26):
  ARTIFACT in 2023 (3/3 segments flip), 2024 (2/3), 2025 (reproduced
  identically), and pooled 3-yr with the fidelity hard-guard (3/3 flip,
  9.2e-13)** — `docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`. The
  hypothesis's other half — the tight-bin offer population being
  disproportionately already-committed — is **CLOSED terminal by pjm-128
  (2026-07-26): no public unit-level DA award/commitment feed exists**, and
  the masked offer corpus cannot be joined to any external one
  (`docs/FINDING-pjm128-da-award-feed-scope-2026-07.md`).

**Read that list against the bar.** PJM's remaining residual is already
characterized the way NEISO's and NYISO's are: the >$200 tail is owned by the
reserve *supply* side, and pjm-82/B.4 name it a **disclosed representation
boundary under the no-MIP mandate** — a continuous `U` holds fractional online
capacity at near-zero cost, so the perfect-foresight LP carries 2.66–3.14× the
measured online reserve. That is a structural boundary, not a tuning gap.

## 3. What still blocks the declaration — two lanes, both admissible, neither tried

### Lane 1 (primary) — G-20b reserve SUPPLY side, the two unvalidated framings

> ## LANE 1 IS COMPLETE (2026-07-26). Both framings tried on record, neither solved.
>
> | framing | mechanism | result |
> |---|---|---|
> | 2 (pjm-124) | scope `ramp10` to committed-and-online | **INERT** — 13.6–15.9 % reduction, *least* bite in tight hours, floor ~10×R |
> | 1 (pjm-125) | constrain commitment before the reserve bound | **PARTIAL** — 51–53 % reduction, *most* bite in tight hours (40–43 pp), floor ~5×R |
>
> **The floor they share is not a modelling choice.** 17.5 GW — 45 % of the
> deliverable ramp — is offline fast-start iron, which is Non-Synchronized
> **Primary** reserve by Manual 11 §4.2 and therefore untouchable by any
> commitment mechanism. That floor alone is **5.0–5.6× the requirement**, so even
> a maximally aggressive, perfectly-informed commitment constraint leaves the
> balance five times oversupplied and no ORDC step can fire.
>
> **This sharpens and partly qualifies pjm-82's LP-vs-MIP attribution.** pjm-82 is
> right that commitment is where the surplus comes from (framing 1's 51–53 % bite
> confirms it), but **a MIP would not close this gate either** — the 5×R floor
> survives any commitment representation. The binding fact is that PJM's ~3.4 GW
> requirement is small relative to the fast-ramping fleet that serves it (30.6 GW
> nameplate / 17.5 GW of 10-min deliverable ramp). That is a real system property.
>
> **Consequence: the remaining >$200 residual is not on the reserve supply side.**
> Whatever set PJM's $1,722 at h4193 (model dual $210.99, model any-zone energy
> $675.3) is not a Primary-reserve shortage the model could reproduce by
> tightening supply. Lane 1 has no admissible mechanism left.
>
> New ledger measurement (pjm-125 §2): the **ramp** family binds 81 % / 70 % /
> 60 % of hours in 2023 / 2024 / 2025 — the joint capacity row is progressively
> becoming the binding family. Framing 1 was aimed at a live constraint.
>
> ---
>
> **UPDATE 2026-07-26 (pjm-124): framing 2 is CLOSED, no solve spent.**
> `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`. Three results the
> rest of this section should be read against:
>
> 1. **45 % of the deliverable ramp is tariff-protected.** The keeper's balance
>    families are **Primary** = Synchronized + **Non-Synchronized**, and
>    Non-Sync reserve *is* offline 10-min-startable iron (Manual 11 §4.2). The
>    fast-start term — 1,411 members, 30.6 GW nameplate, **F = 17.6 GW mean, 45 %
>    of the 38.9 GW cap** — counts in either commitment state, so no
>    commitment-state scoping may remove it. F alone is **5.2× the requirement**.
> 2. **The rigorous lower bound stays 9.7–10.5× the requirement** in 2023/2024/
>    2025 (`F + max(MG, DISP)` = 32.6 / 33.2 / 33.6 GW). The mechanism does not
>    reach even the PARTIAL band. Its bite is *smallest* (8–10 %) in the tightest
>    net-load quartile — where the residual lives.
> 3. **The strict online-only variant is closed too**, on both grounds: it prices
>    Synchronized while calling it Primary (a product mismatch, rule 1), and its
>    own lower bound is still **4.6–4.9× the requirement**.
>
> **Consequence for the ledger — this qualifies pjm-82's LP-vs-MIP attribution.**
> Even with commitment state read exactly, and counting only iron the tariff
> permits, the balance stays ~10× slack. **A MIP would not close this gate
> either.** The slack is the size of PJM's reserve-eligible fast-ramping fleet
> against a ~3.4 GW requirement — a real fleet property, not a representation
> artifact. That is a strong prior that **framing 1 (pjm-125) will land the same
> way**, since it addresses the same online/offline distinction just measured to
> be worth 13.6–15.9 % of a 10× surplus. Framing 1 is still worth running for
> the record; it should not be expected to move the tail.
>
> Corroboration, free of any solve: the keeper's persisted reserve dual is now
> read across **all three** years — **0 hours ≥ $300 in 26,280**, and in 2023 and
> 2024 the dual is *identically zero all year* (2025's 22 nonzero hours, max
> $210.99, is the tightest of the three, not a representative one).

`docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §7 names two candidate
framings and explicitly marks them **"none validated here"**:

1. **Constrain perfect-foresight all-online commitment before the reserve bound
   is read.** The LP reads reserve headroom off a fleet it has already
   committed with perfect foresight; the question is whether that commitment
   should be constrained first.
2. **Scope `ramp10` deliverability to genuinely committed-and-online capacity**
   rather than the availability-scaled fleet.

The measurement that motivates both: **38.1 GW of deliverable 10-min ramp
against a ~3.7 GW requirement**, while PJM actually cleared 1.6 GW against 2.5
GW. Until that headroom is realistic no demand curve can price scarcity.

Until these two are on record — implemented and measured, or shown
inadmissible — PJM has a *named admissible mechanism not yet tried*, which is
exactly what the bar excludes. **This is the critical path.**

**Session charter.** Both framings are P1-native and read the model's own P0
run pattern, so neither needs new data and neither is residual-fitting; both
change *which capacity counts as deliverable reserve*, a structural question.
Precedent wiring exists: `build_pjm_reserve_p1_prep` (path B) already zeroes
non-fast-start reserve-eligible units' availability in their plant's P0-offline
hours and recomputes the supply cap on the masked fleet — framing 2 is a
tightening of that scope, framing 1 is its commitment-side analogue.

**Pre-register the kill criteria before solving** (the pjm-121 §5 / pjm-123
pattern, which has now killed two candidates without spending a solve):
* the deliverable-ramp aggregate must fall toward the ~3.7 GW requirement from
  38.1 GW — state the target band before the run;
* the reserve dual must cross **$300** in a nonzero number of hours (today: 0
  of 8,759, max $210.99) — this is the single most diagnostic number in the
  lane and it is readable from `hourly/system_<year>.parquet::reserve_price`
  **without a re-solve** on any bundle that has one;
* C1 fuel-mix must stay 16/16 — tightening reserve supply moves energy dispatch;
* rule 1: a framing that closes the tail by making reserve artificially scarce
  is not a repair. The headroom must be wrong *for a stated physical reason*.

**Honest expectation, stated up front.** pjm-82's finding is that the binding
constraint is LP-vs-MIP. Both framings may well land as *partial* — narrowing
the headroom without crossing $300 — which would itself be the frontier
evidence: it would demonstrate on record that the supply side cannot be closed
within the no-MIP mandate. **A negative result here advances the declaration
just as much as a positive one.** Do not chase the number.

### Lane 2 (secondary) — the pjm-123 derive-conditioning question

> **UPDATE 2026-07-26 (pjm-126): ANSWERED — the inversion is an ARTIFACT.
> Lane 2 STAYS OPEN; a frontier declaration would be premature.**
> `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md` (2025,
> fidelity-exact: arm A reproduces the committed surface to 8.5e-13).
>
> Under within-**season** net-load ranking the inversion **reverses sign** in the
> two segments that carry it — CT_FAST **+10.00 → −0.85**, CC_LIKE **+0.35 →
> −0.20** (LONG_RUN holds, but at +0.10 on a base of ~8.1, a 1 % effect).
>
> **The mechanism is the OPPOSITE of the hypothesis below.** It is not
> co-mingling — it is **segregation**. PJM is summer-peaking, so winter's own
> tight hours never reach the annual top-3 % of net load: bin3 is **87 % summer
> (229 of 263 h, only 34 winter)** while bins 1–2 are winter-enriched (477 / 249
> winter hours). Winter is when CT offers are most expensive (oil parity, gas
> basis, cold snaps), so the middle bins are inflated and the tightest bin is a
> summer-only sample. The lower bin3 gas ($4.03 vs $4.53) is a *symptom* of the
> same segregation, not an independent check.
>
> **Consequence.** pjm-123 §3 narrows to "the surface **as conditioned in the
> 2026-07 vintage**" — its legs 1/2/3 A/B results stand, the generalization to
> the whole measured-offer-surface family does not. The measured surface is a
> **live candidate dispersion lever again**, aimed at exactly the residual
> pjm-125 left standing (pjm-121's caveat: the dispersion compression is
> untouched). The open lane and the un-repaired residual are the same object.
>
> **Limitation, stated:** arm C (fixed population) is **vacuous** — 711 of 711
> units offer in all four bins, since PJM units submit offers regardless of
> commitment. So the **commitment-status** half of the hypothesis below is NOT
> tested; it needs the DA *awards* side, which the offer corpus does not carry.
> Still open.
>
> **This is not authority to re-derive.** Rule 20: a season-conditioned surface
> IS a definitional change and admissible on that basis, but adopting it is a
> separate owner-authorized step with its own admissibility memo — and the edges
> are **shared with the frozen pjm-99 top-of-curve surface**, so re-conditioning
> one raises the scope question for the other.
>
> ~~Scope: 2025 only; 2023/2024 corpus fetching for confirmation.~~
>
> **UPDATE 2026-07-26 (pjm-127): the multi-year confirmation is DONE and the
> owner memo is WRITTEN — the lane now waits on the owner.**
> `docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`: ARTIFACT in 2023
> (**3/3 segments flip**), 2024 (2/3 — CC_LIKE flips, CT_FAST narrows 77%),
> 2025 (pjm-126's run reproduced **identically** on the re-fetched corpus),
> and the pooled 3-year hard-guard run (**3/3 flip**, worst fidelity
> deviation 9.2e-13). The mechanism is starker in the confirmation years:
> the annual top-3% bin holds 3 winter hours in 2023 and **1** in 2024.
> The admissibility memo
> (`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`) was
> pre-registered in git before the 2023/2024 numbers were seen; it argues
> the definitional case from market structure only, settles scope for BOTH
> surfaces (one definitional vintage, coherent solve-time seam change,
> vintage guard), keeps the pjm-126 season boundaries verbatim, and
> pre-registers the staged A/B (no-LP K1-gradient pre-check before any
> solve) with the level-shift refutation signature that would close the
> family for good. Arm C stayed vacuous in every year (≥99.2% of units
> offer in all four bins) — the commitment-status half is still pjm-128.
>
> **UPDATE 2026-07-26 (pjm-128): the commitment-status half is CLOSED —
> TERMINAL, blocked on data that does not exist publicly.**
> `docs/FINDING-pjm128-da-award-feed-scope-2026-07.md`; census
> `scripts/probes/pjm128_da_award_feed_scope.py` +
> `results/calibration/pjm128_da_award_feed_scope.json` (no LP, no solve, no
> intake). PJM's public DataMiner2 catalog was enumerated from the API itself
> — **119 feeds**, 26 tripping a commitment/award keyword net — against an
> admissibility test committed before the census: **unit identity (A1) ×
> hourly time key (A2) × cleared/awarded/committed quantity (A3)**, all three
> required. **No feed satisfies all three.** The only unit-resolved hourly
> feed is the offer corpus itself (`energy_market_offers`, 90.6 M rows),
> which fails A3 — offers, never awards. The near misses fail on grain:
> `ops_init_commit` is **zone**-level (20 zones, out-of-market commitments
> only), `rt_and_self_ecomax` and `day_gen_capacity` are **system** totals,
> `gen_specific_uplift_credit` is per-generator but **monthly dollars**.
>
> Two supporting measurements, both from the committed JSON:
> (a) even the *system* RT-committed series is redacted under PJM's own
> `"Confidentiality Rules Prohibit Display"` flag in **35.9 %** of hours
> (Jul 2025) and **49.7 %** (Jan 2023) — a quantity withheld at system level
> is not published per unit; (b) an **independent** blocker — the offer
> corpus's masked `unit_code` space is **completely disjoint across years**
> (1,219 codes on 2023-07-15, 1,252 on 2024-07-15, **0 in common, Jaccard
> 0.0000**, no published crosswalk), so *no* external award source could be
> joined to the offer population even if one existed. De-anonymising the
> masked units by ecomax/start-cost fingerprinting is recorded as **refused,
> not untried**.
>
> **Untested, not refuted, and no aggregate proxy** — `ops_init_commit` /
> `day_gen_capacity` could manufacture a committed-share number and the
> charter and rule 1 both forbid it. The season half is unaffected:
> pjm-126/127's ARTIFACT verdict never rested on arm C.

Is the tightest-bin inversion in `pjm_offer_midcurve_condbinned.json` a real
property of PJM offers, or an artifact of the derive's conditioning? Evidence
(2025 tables, × delivered gas, surface's own edges `[0.80, 0.90, 0.97]`):

| segment | bin0 | bin1 | bin2 | **bin3 (tightest)** |
|---|---|---|---|---|
| CT_FAST (s0.05–0.85) | 26.5–30.9 | 32.0–33.9 | 32.7–34.5 | **22.5–25.2** |
| CC_LIKE (body) | ~4.9–5.1 | 5.17–5.42 | 5.08–5.53 | **4.83–4.92** |
| LONG_RUN (top) | 8.57–8.97 | 8.28–8.62 | 8.18–8.62 | **8.07–8.47** |

Not a gas artifact: bin3's mean delivered gas is itself the lowest ($4.03 vs
$4.53 in bin1), so a constant dollar offer would read as a *higher* multiplier.

**Hypothesis to test (not a claim):** within-*year* net-load percentile puts
winter evening peaks and summer scarcity in the same bin3, and fast-start units
in those hours are largely already committed — so the offers *submitted* in
bin3 come from a different population than the offers that *set* the price.

**Constraint — read before touching anything.** This is a rule-20 review of
`scripts/data/derive_pjm_offer_midcurve.py`. Derive scripts are **frozen
against residuals**: a re-derivation commit must cite a **data or
conditioning-definition change**, never a residual movement. A season-split or
committed/uncommitted-split conditioning is a *definitional* change and is
admissible on that basis alone; re-deriving because C3a moved is not. Owner-gated.

If the inversion proves to be an artifact, the measured surface may re-enter as
a dispersion lever and pjm-123's §3 generalization narrows to "the surface *as
conditioned in the 2026-07 vintage*". If it proves real, §3 stands as written
and this lane closes — **either outcome is ledger progress.**

## 4. Suggested sequence

1. ~~**pjm-124 — Lane 1, framing 2**~~ — **DONE 2026-07-26, CLOSED on the no-LP
   pre-check, no solve spent.** See the Lane 1 update above and
   `docs/FINDING-pjm124-ramp10-scoping-precheck-2026-07.md`. The §5 housekeeping
   item is also done: `scripts/lib/bundle_fleet.py` is the shared widened
   reconstruction helper.
2. ~~**pjm-125 — Lane 1, framing 1**~~ — **DONE 2026-07-26, PARTIAL on the no-LP
   pre-check, no solve spent.** See the Lane 1 completion block above and
   `docs/FINDING-pjm125-commitment-constraint-precheck-2026-07.md`. Run after
   124 as prescribed; separability held trivially, since **neither framing was
   ever armed in a solve** (rule 19's concern is arming both and reading one
   number, which did not occur).
3. **pjm-126 — Lane 2 diagnostic: DONE 2026-07-26, verdict ARTIFACT** (see the
   Lane 2 update above). The conditioning question is answered; the *lane* is
   NOT closed by answering it — the opposite. The measured surface is a live
   dispersion lever again, so the remaining work is:
   a. ~~**pjm-127 — multi-year confirmation**~~ — **DONE 2026-07-26, ARTIFACT
      confirmed in all three years and pooled (no solve spent).** See the Lane
      2 update above and
      `docs/FINDING-pjm127-conditioning-multiyear-2026-07.md`.
   b. ~~**pjm-128 — the commitment-status half**~~ — **DONE 2026-07-26,
      CLOSED as blocked on non-public data (no solve, no intake).** PJM
      publishes no unit-level DA award/commitment feed: the whole 119-feed
      DataMiner2 catalog was censused against a pre-committed
      identity × hourly × award test and nothing satisfies it, and the offer
      corpus's masked unit codes are fully disjoint across years (Jaccard
      0.0000) so no external award source could be joined to it either. The
      half is **untested, not refuted**, and no aggregate proxy was taken.
      See the Lane 2 update above and
      `docs/FINDING-pjm128-da-award-feed-scope-2026-07.md`.
   c. **The re-derive decision itself — owner-gated, and the memo now exists:**
      `docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md` (pjm-127b,
      pre-registered before the confirmation numbers landed). It settles the
      definitional case, scope for BOTH surfaces, the fixed season
      definition, the staged pre-registered A/B, and the refutation
      signature. **The lane waits on this decision.** If authorized, the
      staged sequence in memo §4 runs (no-LP pre-check first, then the A/B
      chain, rules 12/14/16); if declined, the lever is formally blocked on
      an owner decision and the ledger records it as such.
3d. **pjm-130 (2026-07-27) — the re-tune opened; no solve spent.** Gate 1
   (C1-2023 CC_REGULAR) is **displacement, with a real lever**: 99.6 % of
   CC_REGULAR's gross hourly loss lands in hours the guard-returned supply rose
   (r = −0.369), and the returned classes now overshoot the **meter** —
   2023 CC_CHP **+2.54 TWh (+41 %)**, ST_GAS **+1.72 TWh (+19 %)** — while
   CT_PEAKER *improves* to +0.12. That is the same merit-ownership miss pjm-122
   named, so **gates 1 and 2 are one stratum** and gate 1 cannot be closed
   independently while gate 2's measured route is owner-blocked. Gate 3 is
   ledgered, root cause out of reach (both framings closed; the 5.0–5.6×R floor
   is 45 % tariff-protected Non-Sync Primary reserve, so a MIP would not close
   it). Shipped instead: gate 1's **prerequisite** — pjm-129 §6's negative
   committed metered volume (`classFull.CT_CHP = −0.3726 TWh`) reproduced,
   localized and fixed (`03e105f`); `--btm-backfill-year` had repaired the
   subtrahend only. 2023/2024 byte no-ops, 2025 CT_CHP → **+1.4653**, no C1
   verdict change.
   `results/calibration/FINDING-pjm130-gate1-and-bench-symmetry-2026-07.md`,
   `docs/handoffs/pjm-130-retune-charter-2026-07.md`.
3e. **pjm-131 (2026-07-27) — gate 1 has NO admissible arm; no solve spent.**
   Memo re-checked and **still undecided** (`f1070d4`), so priority 1 stayed
   blocked and gate 1 was attempted. Both halves close on pre-registered rules:
   * **CC_CHP half — REFUTED, and re-classified.** On the `pjm129_meritguard_a1`
     fleet reconstructed with no LP, **κ = 0.023** of CC_CHP's 2023 energy is
     produced at its available grid-capacity ceiling (mean utilization 72.7 %),
     so the class is **economically dispatched, not capacity-bound** and the
     host-share capacity lever is inert — a capacity cut is absorbed while the
     bench actual falls in full, which *enlarges* the overshoot. The probe
     reproduces pjm-130 §2 exactly (8.653 / 6.1148 / **+2.538 TWh**). This
     **upgrades 3d's "one stratum" from analogy to a measured dependency**: the
     +2.54 TWh is a merit-ownership miss, so it is closed by whatever re-owns
     the $40–150 region — gate 2's owner-blocked route. Do **not** open a
     separate CC_CHP lane.
   * **ST_GAS half — GROUNDED, ledgered.** `st_netload_drag` is over the D-2
     budget (54.6 % of the class in 2023) but carries a cited `D4_WINDOWS`
     declaration and scores **D-4 pass, 0.000 off-window** with D-1 shape
     passing every year — rule 18's over-budget escalation satisfied, i.e. a
     clean pass. Not a floor-window artifact, so no mechanism was invented
     (rules 1 / 19).
   * **New defect found — `chp-btm-share` is globally degenerate.**
     `btm_share ≡ 1.0` on **62/62 rows across 5 ISOs** (CAISO curates none),
     root-caused upstream: of 2,915 steam-reporting unit-years in
     `plant_emission_rates_v2`, **2,914 carry `net_mwh = 0`** — at CEMS the
     steam load and the electrical output sit on different units, so the cogen
     filter removes the rows holding the electricity. A plant-level repair
     recovers only **24 of 134** cogen plants, a CEMS-visibility-biased sample,
     so **no repair was shipped** and the sector estimate correctly stands
     (rule 14's misalignment exception). **Latent forecast exposure:**
     `runner.py` resolves the artifact for forecast years, so a curated
     partition would pull every covered CHP plant 100 % behind the meter.
   * pjm-130 §6's `test_persisted_identity` failure is **not reproducible** at
     `8e5053e` — `cache_key()` returns the pinned `edbc1b103207170a`, the pin is
     unedited, it is not data-dependent, and there are no live env knobs.
     `--reuse-solved` unaffected.
   `results/calibration/FINDING-pjm131-gate1-no-admissible-arm-2026-07.md`,
   `docs/handoffs/pjm-131-gate1-arm-charter-2026-07.md`.

3f. **pjm-132 (2026-07-27) — the memo was AUTHORIZED, executed, and REFUTED.
   Lane 2 ends.** The owner authorized the within-season re-conditioning with a
   "keep the current config as default" amendment; memo §4 ran exactly as
   pre-registered. **Stage 1 K1 PASSED 3/3** on bids (gradient +0.997 / +0.437 /
   +0.125) but the honesty bound fired in every year, worst in 2025 (tight-bin
   rise **$0.152/MWh** vs a ~$1 noise floor) — reported to the owner before the
   chain was spent. **Stage 2 (6 solve-years, both arms registered) refutes it:**
   C3a-2025 moves **−0.011 $/MWh** against a −4.54 gap and dispersion NARROWS in
   2023 (−0.045) and 2024 (−0.144). The PASS signature needed the 2025 gain
   carried by the tight strata AND dispersion widening toward actual; neither
   holds. The measured-offer-surface family has now been tried as a dispersion
   lever under **BOTH** conditioning definitions and fails on prices both times.
   The control arm validates itself: 2025 at **40.932**, reproducing pjm-129's
   guard-corrected A1 (40.93), not the keeper's pre-guard 41.53.
   *Kept, at zero cost:* the seasonal vintage is real and **ISO-wide** — MISO and
   NYISO carry **zero winter hours** in their annual tight bin (PJM 95.2 %
   summer, mid-pack), so the definitional case is not PJM-specific; the gate
   stays **default-off** (2.85 ms/solve-year) and the owner's "default if it
   helps the forecast" condition is **unverified**, so it did not fire.
   *Also shipped:* pjm-130's bench fix was **inert** — it recovered its trigger
   from `run_config.json`, but `btm_backfill_year` lives in `meta.json` on every
   bundle, so the one-sided repair persisted. Fixed; PJM 2025
   `classFull.CT_CHP` **−0.3726 → +1.3724**.
   `results/calibration/FINDING-pjm132-withinseason-refuted-2026-07.md`,
   `docs/handoffs/pjm-132-midcurve-reconditioning-charter-2026-07.md`.

4. **Frontier is NOT ready — and as of 2026-07-27 the blocking half has CHANGED.**
   The **mechanism-ledger half is now essentially complete**: Lane 1 closed
   (pjm-124/125), Lane 2's commitment half terminal (pjm-128), the season half
   settled (pjm-126/127) and now tried-and-refuted (3f), gate 1 closed
   (pjm-131), gate 3 ledgered. **No named admissible mechanism remains untried.**
   What blocks frontier is now the **calibration half**, and §1's claim that
   "PJM clears the first half of that bar already (10/10)" is **no longer true on
   corrected data**. The keeper scores CALIBRATED only on the **pre-guard
   inflated outage envelope**; the same recipe on the corrected envelope
   (`pjm129_meritguard_a1`, reproduced by pjm-132's control) is **NOT-YET** with
   **C1 FAIL (15/16, free 11/12), C3a FAIL, C3c FAIL**. Frontier requires every
   hard **and volume** criterion in band with the residual confined to the C3c
   tail; PJM fails a volume criterion AND a price-level one. **Recommendation:
   do NOT declare frontier** — declaring on the committed 10/10 would be
   declaring on an envelope the project has superseded. The real open item is
   upstream and owner-only (miso-88 precedent): what to do about the keeper
   designation on the corrected envelope. See the finding §5 for the three
   routes.

5. **(superseded numbering — the original §4 text follows for lineage)**
   **Frontier is NOT ready — and as of 2026-07-27 for exactly one reason.**
   Lane 1 is complete (pjm-124/125), Lane 2's commitment-status half is
   terminal (pjm-128, blocked on non-public data — the bar's own second
   clause), and the season half is measured and settled (pjm-126/127). What
   remains is **the owner's decision on the re-conditioning memo** (3c): the
   last named admissible mechanism that is neither tried nor formally blocked.
   pjm-131 (3e) **widened what that decision gates** — gate 1's CC_CHP half is
   now measured to be the same merit-ownership question, so the memo blocks
   gates 1 *and* 2, not gate 2 alone.
   Authorize-and-run memo §4, or decline and record the block — the ledger is
   whole either way, and no session may proceed without that decision.

Rule 16 binds throughout: any registered bundle is `--year 2023 2024 2025` in
one invocation. Rule 22: PJM has **no calibration-complete marker**, so no
out-of-training year (2022, 2019, ≤2021, H1-2026) may be solved or scored.
Frontier and calibration-complete are independent — NYISO holds frontier with
no marker.

## 5. Two housekeeping items this session surfaced

* ~~**`derive_pjm_ordc_overlay._run_year_kwargs` drops 38 non-default `run_year`
  flags**~~ — **DONE (pjm-124)**: promoted to `scripts/lib/bundle_fleet.py`
  (`full_run_year_kwargs`, `reconstruct_bundle_fleet`, the year-chain gas-price
  fallback and a generalized fidelity guard covering the offer-path *and*
  reserve gates). `pjm123_composite_precheck.full_run_year_kwargs` now delegates
  to it. Original description follows.

  **`derive_pjm_ordc_overlay._run_year_kwargs` drops 38 non-default `run_year`
  flags** the pjm-121 keeper records — including all three `tranche_startup_*`
  gates, `ct_netload_drag` / `gas_st_netload_drag` and their overrides, and the
  `pjm_offer_midcurve_conditional` master gate. Every PJM no-LP probe that uses
  it measures a fleet the keeper never solved.
  `scripts/probes/pjm123_composite_precheck.py::full_run_year_kwargs` is the
  widened replacement, with fidelity guards that hard-fail on a dropped gate.
  **Promoting it to the shared helper is a small unblocked task** and should
  happen before Lane 1's pre-check, which will want the same reconstruction.
* **pjm-121 §5's level-form magnitudes** (−8.76 $/MWh MW-weighted; the CC econ
  spread table) were measured on the partial reconstruction. Its *conclusion*
  is unaffected and is independently reconfirmed by pjm-123 §2, but those
  specific numbers should not be quoted as the keeper fleet's.

## 6. Environment (container starts empty)

```
uv sync                                        # use .venv/bin/python throughout
python scripts/regenerate_clean.py transfer-interface-limits ramp-capability lmp
python scripts/data/fetch_pjm_da_virtuals.py --years 2023 2024 2025 --feeds hrl_da_incs_decs
```

The virtuals fetch is **required** (`pjm_da_virtual_bids` hard-fails without the
gitignored raw) and takes ~10 min/yr. Solves ~15 min/yr, peak ~14.8 GB on a
15 GB box — one solve process at a time, years sequential. The container
suspends between turns: `nohup` the solve and hold awake in bounded blocks.

Fidelity anchor, **no solve needed** (the keeper hourlies are committed):
`pjm120_c3a_stratum_readout.py results/calibration/pjm121_ccbelt --year 2025`
must read model_lw 41.53 / actual 46.07 / gap −4.54.

The reserve-dual readout that Lane 1 turns on is likewise no-solve:
`hourly/system_<year>.parquet::reserve_price` on any bundle carrying sidecars.

## Pointers

* `docs/FINDING-pjm123-composite-precheck-2026-07.md` — the offer-surface family closure
* `docs/FINDING-pjm120-c3a-extreme-tail-depth-2026-07.md` §6–§7 — the reserve-dual evidence and the two unvalidated framings
* `docs/DIAGNOSIS-pjm-dof-scarcity-tail-2026-07.md` §B.3–B.4 — the lever ledger and the LP-vs-MIP boundary
* `docs/FINDING-pjm121-ccbelt-c3a-close-2026-07.md` §4 — the honest-scope caveat carried with the keeper
* `docs/codebase-site/calibration-rubric.html` §frontier — the bar, and how NEISO/NYISO met it
