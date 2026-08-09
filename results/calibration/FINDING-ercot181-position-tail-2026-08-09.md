# FINDING — ercot-181: the QUANTITY-POSITION lane — the position-tail completion is BUILT, PROVEN, and PROMOTED-INERT; the offer-side mechanism space for C3a-2023 is EXHAUSTED, matrix §5.1 item 23

**Session ercot-181, 2026-08-09.** Charter:
`FINDING-ercot180-topscoped-exhausted-2026-08-08.md` §4/§5 (item 22's `==>`
clause) — reality's marginal price forms at a POSITION far up a cliff-shaped
submitted curve, which no LEVEL statistic can see. Object: **C3a-2023**
(−32.4 % on keeper `2026-08-07-run176-control-offline-increment`, NOT-YET,
fail set {C3a, C3b}); owner standing instruction: under 10 % without
disturbing 2024/2025.

Pre-registration: `docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md`,
pushed BEFORE any corpus measurement, derive, build, or solve, + its
pre-solve Amendment 1 (tail years 2023-only). It fixed the instrument and its
bars, the mechanism-form election with three ex-ante refusals, the build-free
M-0/M-1 inertness tree, the kill gates verbatim (G-SHED PRIMARY), and the
FILED-REFUSED terminus — all before anything was looked at.

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `ercot_offer_surface_position_tail` — the position-tail completion of the wall (RT/SCED leg) and fast-start pool ladders' p90-truncated position axes |
| **Verdict** | **BUILT, SEAM-PROVEN, SOLVED, and PROMOTED AS KEEPER on structural fidelity — with the honest measured outcome INERT-ON-THE-OBJECT** (cell `K`). The arm moves 22 spring 2023 hours by +$0.006..+$0.57 (annual lw **+$0.0004/MWh**); the summer object hours, tail counts, shed counts, and every scored criterion are IDENTICAL to control |
| **Runs** | control `2026-08-09-run181-control-positiontail-pair` (reproduces the run176 keeper ARRAY-EQUAL, all 3 years); arm `2026-08-09-run181-position-tail` (**PROMOTED KEEPER**), both registered |
| **Keeper** | `2026-08-07-run176-control-offline-increment` → **`2026-08-09-run181-position-tail`**; determination NOT-YET, fail set {C3a, C3b} — UNCHANGED |
| **Matrix** | row + field in the same PR (rule 28(c)); cell `O → K`; §5.1 item 23; both keeper headers re-stamped |
| **THE LANE'S CONCLUSION** | **The offer-side mechanism space for C3a-2023 is EXHAUSTED** (items 21–23) — **ESCALATED to an owner sitting on C3a-2023 reachability within this model class** (the C3c-caveat path), per the precommit's pre-registered terminus |

## 1. The DO-NOT-REDO check (rule 28(a), run before pre-registration)

No ERCOT cell adjudicated a quantity-position mechanism; item 22's `==>`
clause charters exactly this lane. The conditioning-grain family (items
21–22, both `R`) was NOT re-opened — the grain forms conditioned the HOUR
axis; this lane completes the POSITION axis, with the frozen bins and every
hour-axis statistic inherited byte-identical. Every fence in the handoff
stayed closed; the frozen ceiling lane was not entered.

## 2. M-0/M-1 — the build-free reach adjudication (LIVE, so Route B)

`scripts/probes/ercot181_positiontail_reach.py` reproduced both members' row
geometry BYTE-IDENTICALLY from the keeper bundle state (wall + pool markups
array-equal to the `_compose` mirror; gate-off compose shas equal the
ercot-178 record at this HEAD), then adjudicated the pre-registered M-1
criterion on every rel > 0.9 row-hour: **LIVE in all three years** (598 /
528 / 48 row-hours at/below control price + $1) — P-2's central
provably-inert expectation was **FALSIFIED at the formal criterion**, so per
the tree the mechanism was built and solved, no discretion applied. (The
live rows: 2023/2024 dominated by shed-hour rows — every bid sits below a
$5,000 price — plus genuinely near-marginal moderate-bin rows in 2025;
record: `ercot181_positiontail_reach.json`.)

## 3. The build and the seam proof (SP-α1..α8 ALL PASS)

One default-off ERCOT-only gate (`scenarios.py`), cache-key registered
dropped-at-default in both registries in the same commit (default key
`603c2498bf71d21d` verified unmoved; armed key distinct). Artifacts:
`ercot_sced_offer_wall_positiontail.json` + `ercot_faststart_pool_positiontail.json`
derived by `--position-tail` modes — each bin's tail = the SAME MW-weighted
quantile statistic on the population's own measured support above p90
(`scripts/lib/positiontail.py`; CC top bin: 202× delivered gas rising to the
HCAP wall 2659.6× at x = 1.0, 158 points; CT 596×→HCAP; pool 570×→HCAP),
with the re-derived ladders asserted to REPRODUCE the frozen artifacts
before any tail is appended.

**Amendment 1 (pre-solve): tails are 2023-ONLY.** The reproduction assert
STOPPED on 2024 — the frozen 2024/2025 RT-wall blocks came from the
2026-07-21 full-corpus intake that the 2026-07-22 large-blob history rewrite
PURGED, so their populations cannot be reconstructed; a tail on an
unreproducible anchor would be inconsistent by construction. The
pre-registered zero-support rule composed at year grain: 2024/2025 keep
their frozen ladders byte-identical (the RT wall's own year-scoping
pattern), making the arm byte-identical to control there — G-BIT re-armed in
substance for the out-of-object years.

Seam proof (`ercot181_positiontail_seamproof.json`, ALL_ASSERTIONS_PASS):
SP-α1 the 2023 arm delta confined to rel > 0.9 row-hours (263,966; ZERO
outside; pool `own_mask` byte-identical); SP-α2 null encoding (tail points
carrying the frozen p90 value) composes byte-identical EVERYWHERE — the
appended axis is POSITION, never level; SP-α3 gate-off shas equal the
ercot-178 record; SP-α4 non-ERCOT builders return None; SP-α5 all seven
frozen artifacts byte-identical to HEAD after the derives; SP-α6
no-markdown + monotone tails; SP-α7 thirteen forbidden combinations raise;
SP-α8 artifact conformance (sub-p90 byte-equal frozen, x strictly
increasing in (0.9, 1], vintage tags, coverage disclosed).

## 4. The A/B (pre-registered §9: control + arm, 2023–2025, strictly sequential, same HEAD)

* **The CONTROL reproduces the run176 keeper ARRAY-EQUAL in all three
  years** — the keeper's next consecutive reproduction at a new HEAD.
* **The ARM, at solve grain:**

| year | arm vs control | lw | tails >$200 | shed |
|---|---|---|---|---|
| 2023 | differs in **22 hours**, all spring, +$0.006..+$0.57 | 43.453 → 43.453 (+$0.0004) | 61 → 61 | 4 → 4 |
| 2024 | **byte-identical** (array-equal) | 31.762 | 25 | 2 |
| 2025 | **byte-identical** (array-equal) | 33.378 | 3 | 0 |

* Max class-energy delta (2023): **0.0017 %** (CC_CHP); COAL_PRB
  +0.0005 TWh. Determinations: both runs NOT-YET, fail set {C3a, C3b},
  every magnitude identical to the keeper (C3a-2023 −32.4 %, C3b-2023
  0.602, C3b-2024 0.205, C3c CAVEAT ×3 at 61/181, 25/53, 3/31; C1/C2/C4/
  C6/C8 PASS).

**The structural reading (rule 1).** The model's marginal rows in the object
hours read the p50–p70 region of the measured ladders (control prices
$100–360 ≈ multipliers 40–140), BELOW the completed decile — exactly the
geometry P-2 predicted. Completing the truncated top reprices only
supramarginal rows there; the quantity-position wedge is a
**CLEARING-POSITION phenomenon, not a bid-truncation one**: the LP's
aggregate clearing position in those hours simply never reaches the cliff
face where reality's lambda forms.

## 5. Kill gates (pre-registered §7, adjudicated at full magnitude) — ALL PASS

| gate | reading | verdict |
|---|---|---|
| **G-SHED (PRIMARY)** | 4/2/0 → 4/2/0, unchanged | **PASS** |
| **G-OWNER** | 2024 C3a PASS kept (byte-identical); 2025 unchanged; max class energy 0.0017 % vs 0.5 % cap | **PASS** |
| G-SPAN′ / G-SPUR | no tail-hour count moves in any year | PASS |
| G-C3c | 61/181, 25/53, 3/31 identical | PASS |
| G-COAL148 | +0.0005 TWh vs +0.5 cap | PASS |
| G-DOF | ONE measured ledger entry added (n_scalars 0, free_parameters_added 0); n_residual 6 unchanged | PASS |
| G-D2 / C8 | no bound touched; C8 PASS both bundles | PASS |
| Rule 22 LOYO | zero identified parameters; the held-out 2024/2025 arms are byte-identical to control — no in-sample gain bought with held-out degradation | CLEARS |

## 6. The promotion (owner-instructed structural standard)

Promoted under rule 1 [R-STRUCT] + rule 14 [R-ACCURATE] and the session
owner instruction ("if structural integrity improves but gates regress that
may still be a keeper" — here integrity improves and NO gate regresses): the
completion replaces a silent truncation of measured conduct with the
measured distribution itself, at zero gate cost and zero DOF. It is
supramarginal in today's backcast top hours; it binds wherever a class
position crosses p90 of its within-plant span — today 22 cheap spring hours,
forward wherever load growth pushes class positions into the measured cliff.
Keeper re-key + `build_status.py --iso ERCOT` + `calibration-keeper-auditor
--iso ERCOT` (PASS, zero repairs). No `calibration-complete.json` re-key
(ERCOT holds no marker).

## 7. The instrument (precommit §1) — REFUSED-AS-MEASURED, and the refusal is the measurement

* **I-B1 coverage 0.999 PASS; I-B2 relative IQR 0.0 PASS; I-B3 FAIL at
  full magnitude:** λ̂ hour-median **$5,000** vs actual RT **$144**
  (median relative error 27.2 vs the 0.25 bar). The interior resources'
  price-at-BP clusters PERFECTLY — at the WRONG value: SCED2 curves are
  piecewise-LINEAR, and the step-lookup convention (the wall derive's own,
  inherited deliberately) reads the cliff segment's UPPER breakpoint (HCAP)
  for every resource dispatched onto the face. **The saturation IS the
  phenomenon**: the marginal resources sit on the near-vertical cliff
  segment where lambda is the interpolated height and tiny position
  differences swing price enormously. Per the precommit the instrument is
  REFUSED-AS-MEASURED; the ercot-180 envelope + containment statistic remain
  the lane's sizing; the instrument was NOT redesigned after seeing the
  answer (rule 20/23) — a linear-interpolated price-at-BP instrument is
  admissible only under a new precommit.
* **I-2** consequently reproduces the envelope statistics unchanged (q_act
  0.9977, share-of-gap saturating).
* **I-3 — the wedge sized from the corpus side, the sitting's key number:**
  at the top-bin hours, reality's ON merchant-gas fleet held only
  **269 / 555 / 926 MW (p25/p50/p75) of unaccepted spare priced below λ̂**
  (and λ̂ is saturated HIGH, so the true sub-lambda spare is smaller still),
  at fleet position p50 0.884. **The several-GW of $100–600-bid headroom
  that pins the model's top-hour price does not exist in real conduct.**

## 8. Predictions adjudicated (precommit §8, at full magnitude)

* **P-1 (instrument):** PARTIALLY — I-B1/I-B2 passed, I-B3 FAILED; the
  refusal path fired exactly as pre-registered and is itself informative
  (§7).
* **P-2 (THE CENTRAL PREDICTION):** the GEOMETRY was right (marginal rows
  below every truncation; the completion cannot reach the object-hour
  formation — confirmed at solve grain: zero object-hour movement) but the
  FORMAL M-1 verdict was LIVE, not provably-inert — the conservative
  criterion (shed-hour rows, moderate-bin near-marginal rows) forced the
  honest build/solve. Adjudicated: falsified as stated, vindicated in
  substance.
* **P-3:** CONFIRMED beyond its own bound — movement +$0.0004/MWh (vs the
  ≤ ~$2 prediction), and in cheap spring hours, not the model's high hours.
* **P-4 (shed):** the risk never materialized — shed 4/2/0 unchanged;
  G-SHED never fired.
* **P-5 (out-of-object years):** CONFIRMED at the strongest possible level —
  byte-identical (Amendment 1).
* **P-6 (D-2/D-4):** CONFIRMED — no bound touched; C8 PASS; the D-4
  `reliability_floor × CT_PEAKER` rows are the keeper's own standing state,
  inherited unchanged.
* **P-7 (the wedge):** CONFIRMED with a sharpening — the cheap-but-unaccepted
  ON-gas mass is SMALL (~0.3–0.9 GW), meaning the wedge is not "reality left
  cheap MW unaccepted" but "reality's ON fleet genuinely exhausts its cheap
  body and the price forms on the thin cliff face" — which the LP's
  class-aggregate clearing never reaches at backcast loads.

## 9. What remains — the owner sitting (the pre-registered terminus)

With this session the offer-side mechanism space for C3a-2023 is
**EXHAUSTED**: conditioning grain `R`×2 (items 21–22, hour axis), the
position completion `K`-but-inert (item 23, position axis), every
quantity/capability face closed on measurement, ramp/unit-scoped `R`,
outcome pins rule-13-forbidden. The C3a-2023 miss (−32.4 %, Aug+Sep 81.3 %
of the gap, ~50–180 summer-afternoon hours) is a **model-class limitation of
an hourly class-aggregate LP against a 5-minute cliff-face price formation**
— the same object the C3c ledger already accepts for the tail COUNT, now
measured to own the tail LEVEL too. **ESCALATED: an owner sitting on
C3a-2023 reachability within this model class (the C3c-caveat path)**,
sized by: the containment statistic (actual RT inside the position band in
94/100 top-gap hours), I-3 (sub-λ̂ ON-gas spare 0.3–0.9 GW), and the three
independent exhaustion records. The sitting's question: whether C3a-2023
joins the C3c ledger as an accepted model-class limitation (rubric
constraints: C3a is LOAD-BEARING tier, where `model-class` ledgering is
v3.0-refused — so the sitting must either amend the rubric, accept NOT-YET
as ERCOT's standing state, or authorize a model-class change such as
sub-hourly/cliff-resolving price formation). Until the sitting, ERCOT's
determination remains NOT-YET {C3a, C3b} and no further offer-side lever
should be chartered against C3a-2023 (DO-NOT-REDO: items 21–23).

## 10. Governance

* **Rules 15/16:** BOTH runs registered, all three years each
  (`2026-08-09-run181-control-positiontail-pair`,
  `2026-08-09-run181-position-tail`); the two 2026-08-04-159 runs evicted at
  the 15-cap exactly as pre-registered; determinations scored on committed
  artifacts with attestations + legitimacy diagnostics present (C6 PASS
  both).
* **Rule 22:** every tool invocation stayed in {2023, 2024, 2025}; the
  instrument read delivery-2023 only; no out-of-training year solved,
  scored, read, or registered. LOYO for the promotion: cleared (zero
  identified parameters; held-out years byte-identical).
* **Rule 23:** all seven frozen artifacts byte-identical to HEAD (SP-α5);
  the positiontail vintages are a NEW artifact family for a NEW
  pre-registered gate, with frozen-ladder reproduction asserted before any
  tail was appended; the trigger is the ercot-180 §5 structural charter.
  Zero fitted scalars anywhere.
* **Rule 24:** ONE ScenarioConfig field, in `run_config.json`, cache-key
  registered dropped-at-default (default key `603c2498bf71d21d` unmoved,
  armed key distinct — SP-α7).
* **Rule 25:** ERCOT-gated everywhere (SP-α4); no other ISO's files or
  matrix column touched.
* **Rule 26:** nothing deleted, nothing zeroed; the stepped form remains the
  default; grain scaffolding stays merged default-off.
* **Rule 27:** every push touching a ≥300-line file blob-verified against
  the REMOTE; mid-session the branch was merged and auto-deleted FOUR times
  (PRs #3756/#3768/#3770 + the Amendment-1 merge) — the merged-PR protocol
  was followed each time (rebase of unmerged commits onto the new main,
  branch recreated, force-with-lease, re-verify). The formatter-hook
  import-pruning incident (top-level lib imports removed as unused before
  their usages existed) was caught by the derive's own NameError and fixed
  to the house function-local convention.
* **Rule 28:** duty (a) the DO-NOT-REDO check preceded pre-registration;
  duty (b) the cell verdict `O → K` + citation landed in-session; duty (c)
  the row landed in the same PR as the field; duty (d) no cross-ISO verdict
  minted. §5.1 item 23 added; both keeper headers re-stamped
  (`check_mechanism_matrix.py` exit 0, zero warnings).
* **Owner item carried, not touched:** the rule-18 grain defect
  (`min_down = min_run = 0` on econ*/peak* tranche rows) — enumerated in the
  precommit §4, unchanged.
* **GitHub Actions:** nothing offloaded; every derive, probe, solve, score,
  and registration ran in-session.

**Next shorthand: ercot-182 (only after the owner sitting; no offer-side
C3a-2023 lever without new evidence).**
