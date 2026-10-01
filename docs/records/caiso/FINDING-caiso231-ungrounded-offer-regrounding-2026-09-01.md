# FINDING — caiso-231: CAISO's THREE UN-GROUNDED gas offer classes are RE-GROUNDED on their own measured bid buckets and **PROMOTED TO KEEPER**. Nine ERCOT-inherited multipliers retire to measured, zero free parameters are added, and the pre-registered adverse C3a cost lands at **+0.062 / +0.037 / +0.031 $/MWh — 4-13× SMALLER than the first-order bound**. Every pre-registered gate PASSES, no falsifier fires, and the determination is UNCHANGED: **NOT-YET on C3a alone**

**Session:** caiso-231 · **Date:** 2026-09-01 · **Keeper:**
`2026-08-26-caiso-220-c1-crosswalk` → **`2026-09-01-caiso-231-b1-ungrounded`**

**Promotion basis:** the owner's standing in-session standard, given verbatim
this session — *"Is this a recommended keeper candidate? If so plz promote. If
structural integrity improves but gates regress that may still be a keeper.."*
— applied to the filed item caiso-230 §8 raised and explicitly could not decide
on its own.

---

## §1 — the defect, in the model's own words

`src/market_sim/pipeline/backcast_config.py::_CAISO_OFFER_CURVE`:

> *"CC_CHP / CT_CHP / ST_GAS below are PINNED to the values CAISO previously
> inherited from the generic ERCOT-lineage `else` branch. **They are NOT
> CAISO-grounded** — they are preserved verbatim ONLY so the neutral generic
> fallback (rule #24 …) does not silently change the caiso-51 keeper … CT_CHP's
> inherited 1.20 econ vs the measured 0.594 marginal is the largest such
> margin — surfaced for A/B, not asserted good."*

Three ERCOT-fitted band blocks on CAISO's binding path. Rule 25
`[R-ISO-SCOPE]`: *"Tuned curves never cross ISO boundaries."* caiso-230 §4/§7
sized what they price on the 2025 annual load-weighted above-floor term:
`CC_CHP:econ` **+1.23**, `CT_CHP:committed` **+0.36**, `CC_CHP:committed`
**+0.27** $/MWh.

## §2 — the measured repair (rule 13 / rule 14 admissible, zero DOF)

`derive_caiso_offer_surface.py` classifies masked OASIS public bids by the
Theil–Sen slope of body bid price on the measured citygate, and **discloses its
own bucket membership**: *"the three OTC/RMR steamers (ST_GAS …) and priced
CT_CHP curves land in the CT bucket … CC_CHP (HR 6.90) lands in the CC
bucket."* The measured CC bucket therefore **is** pooled CC_REGULAR+CC_CHP
conduct and the CT bucket **is** pooled CT_PEAKER+CT_CHP+ST_GAS conduct, so
re-grounding each class on the bucket it is measured inside is a measured-input
substitution, not a new fitted lever.

`caiso_offer_surface_measured_ungrounded` (default off, CAISO-gated,
hard-requires the incumbent flag) arms **exactly the three bands the incumbent
arms** — `econ_low`, `econ_high`, `peak` — and leaves **every `committed` band
unarmed for every CAISO gas class** (the Lever-A inversion lesson applied
uniformly, rule 19). Verified pre-solve and re-verified on the solved
`run_config`: **exactly 9 bands change, 0 committed bands, 0 non-target
classes.**

| class | band | armed | measured | move |
|---|---|--:|--:|--:|
| CC_CHP | econ_low | 0.960 | 1.066 | **+11.0 %** |
| CC_CHP | econ_high | 1.120 | 1.072 | −4.3 % |
| CC_CHP | peak | 2.250 | 1.386 | −38.4 % |
| CT_CHP | econ_low / econ_high / peak | 1.200 / 1.200 / 1.400 | 1.145 / 1.166 / 1.166 | −4.6 / −2.8 / −16.7 % |
| ST_GAS | econ_low / econ_high / peak | 1.050 / 1.400 / 4.200 | 1.145 / 1.166 / 1.166 | +9.0 / −16.7 / −72.2 % |

**The rejected alternative is named so it is not re-proposed:** rescaling each
multiplier by `base_HR_bucket / base_HR_class` to reproduce the bucket's $/MWh
band price. That is a new modelling choice rather than a transfer, and it moves
C3a further the wrong way (CC_CHP `econ_low` → 1.150, +19.7 %).

## §3 — THE PREDICTION WAS PUSHED BEFORE THE SOLVE, AND IT WAS WRONG IN THE SAFE DIRECTION

`PRECOMMIT-caiso231-ungrounded-offer-regrounding-2026-09-01.md` was committed
and pushed to the remote **before either arm started**, carrying §4's
pre-registered adverse prediction and §6/§7's gates and falsifiers.

| year | **predicted** C3a cost | **measured** | ratio | required move |
|---|--:|--:|--:|--:|
| 2023 | +0.235 | **+0.062** | 0.26× | 0.00 |
| 2024 | +0.344 | **+0.037** | 0.11× | −0.848 |
| 2025 | +0.421 | **+0.031** | 0.07× | −1.893 |

**Why the bound over-predicted, and it is not luck.** caiso-230 §H's estimator
weighted each band's move by the zone-hours in which that class-band is the
marginal rung, at the clearing price — a strict first-order UPPER bound that
assumes λ follows the repriced rung one-for-one. In an LP it does not: when
CC_CHP's econ ramp gets dearer the margin moves to the next-cheapest rung
instead, so the price rises far less than the offer did. The measured
re-dispatch confirms it — **CT_CHP −0.30 TWh/yr displaced by CC_REGULAR
(+0.12…+0.19) and CC_CHP** — real substitution, not a level shift. The bound
behaved exactly as a bound should.

## §4 — every pre-registered gate, scored

| gate | result | verdict |
|---|---|---|
| **G-CTRL** | control 56.31 / 38.96 / 39.76 vs the superseded keeper's 56.31 / 38.96 / 39.76; drift −0.04 / −0.05 / +0.00 pp on a ±0.30 bar | **PASS (exact)** |
| **G-STRUCT** (bands) | exactly 9 bands moved, 0 committed, 0 non-target | **PASS** |
| **G-STRUCT** (DOF count) | predicted 112 → 103; **did not move** | **GATE-SPEC DEFECT — see §6** |
| **G-LIVE** | max \|Δ\| class-hour 1,225 / 3,368 / 1,911 MW | **PASS** |
| **G-C3a** | +0.062 / +0.037 / +0.031, inside [0, 3×] every year; 2023 stays PASS at +4.1 % | **PASS** |
| **G-C1** | 12/12, free 8/8 — unchanged | **PASS** |
| **G-C3b** | 0.100 / 0.178 / 0.181 vs control 0.100 / 0.177 / 0.180; 2025 margin **0.019** | **PASS** |
| **G-C2 / G-C4 / G-C8** | no flip | **PASS** |
| **G-CAVEAT** | ledgered budget 1 of 1, no protective caveat | **PASS** |
| **G-C6** | attestation generated at promotion (`gen_caiso231_attestation.py`) | **PASS** |

**Falsifiers F1–F6: none fires.** Determination **NOT-YET, C3a the sole
load-bearing FAIL** — identical to the superseded keeper.

`audit_keepers.py --iso CAISO`: **PASS, 0 failures, 0 warnings, no repairs.**

## §5 — the honest cost, stated plainly

C3a moves **+4.0 → +4.1 % (2023, still PASS)**, **+12.45 → +12.55 % (2024)**,
**+15.50 → +15.59 % (2025)**. That is ~0.1 pp, and it is a **real regression on
the sole failing gate**, not a rounding artifact — it is reported at full
magnitude here, in the keeper shard, in the attestation and on the dashboard.
It is accepted under rule 14 `[R-ACCURATE]` (*"never revert to an estimate just
because it fits the backcast better"*) and rule 1 `[R-STRUCT]` (*"a real market
behaviour stays in even if it makes the fit worse"*), on the owner's standing
promotion standard. **caiso-230 DO-NOT-REDO item 3 stands unamended: this is
never to be proposed as a C3a lever, and nothing here claims it is one.**

## §6 — A PRE-REGISTERED GATE THAT COULD NOT BE SATISFIED, DISCLOSED NOT DROPPED

G-STRUCT had two legs. The band leg passed. **The DOF leg — "the ledger's
`offer_curve_by_group` residual scalar count must FALL by 9 (112 → 103)" — did
not move, and could never have moved.** `build_dof_ledger._count_scalars`
counts every numeric leaf in the offer surface; it is **provenance-blind**, so
it measures the surface's SIZE, not its fitted content. Re-grounding a
multiplier changes what the number means, not how many numbers there are.

This is a defect in **my gate specification**, not in the mechanism, and it is
recorded rather than quietly dropped. The structural claim is verified on the
`run_config` bands instead (§2), and the ledger's CAISO provenance note — which
already recorded that CC_REGULAR and CT_PEAKER are measured — is **extended to
record that five CAISO groups, not two, are now measured**, leaving only the
five `committed` bands fitted by deliberate design.

**Filed:** making the DOF ledger provenance-aware would let it state CAISO's
true fitted count. It touches a cross-ISO counter shared by every keeper's
ledger, so it is an owner-scoped cross-ISO item, not a CAISO lane change.

## §7 — STANDING OWNER DIRECTIVE RECORDED (2026-09-01)

**No control arms.** The owner's instruction this session, on being shown that
the caiso-231 control cost a full solve and returned zero drift: *"that's one in
like 1000 runs that have been done so I don't care and I don't want to measure
drift."*

**Binding, going forward:** a single-delta calibration arm is solved **once**
and scored against the **committed keeper**. Do not solve a paired control, and
do not spend a solve measuring HEAD drift. The empirical warrant is on the
record — this session's G-CTRL reproduced the committed keeper **to the cent**
in all three years across 25+ intervening merges to main. Where a session
genuinely needs assurance that main moved under a recipe, diff the ISO-affecting
source paths; never spend an LP run on it.

## §8 — DO-NOT-REDO (new, binding)

1. **Never re-test the three un-grounded classes' band level.** They are now
   measured and armed. The remaining fitted values on CAISO's gas surface are
   the five `committed` bands, held unarmed by deliberate design (rule 19).
2. **Never propose this mechanism as a C3a lever** (caiso-230 DO-NOT-REDO item
   3, carried). It COSTS C3a +0.06 / +0.04 / +0.03; it is a rule-14/25
   structural repair and nothing else.
3. **Never re-derive the caiso-230 §A–§H decomposition** on this keeper without
   re-running it against the NEW keeper first — the above-floor attribution was
   measured on the caiso-220 bundle.
4. **Never quote the DOF ledger's `offer_curve_by_group` count as a measure of
   CAISO's fitted offer content** — it is provenance-blind (§6). Read the row's
   note.
5. **No control arms** (§7).

Carried forward unchanged: caiso-230 §9 entire, caiso-229 §10, caiso-227 §K,
caiso-228 §6, caiso-131 §10, caiso-222 §9 Q1 terminal rest, and every
`R`/`I`/`G` cell in `docs/codebase-site/data/mechanism-matrix/CAISO.js`.

Next number: caiso-232.
