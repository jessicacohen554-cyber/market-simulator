# FINDING (pjm-h8) — the ~22 TWh is NAMED: PJM coal's min-load block is the only part of
# its own offer stack that PJM's own published offers do not govern, and the band two
# screens were spent on is the SMALLER half of it

**Session** `pjm-h8` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main` @ `8b9b32e4`
**ZERO LP. No shard was launched, no bundle was written, no keeper was touched.**
Every number below is `run_year(fleet_only=True)` on the keeper's own `meta.json` recipes plus
reads of two artifacts already committed to this repo — the rule 29 `[R-SCREEN]` clause-0 path.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED, and
re-verified at HEAD this session (§4).**

Probe `scripts/probes/_pjm_h8_offer_ladder.py` · output `results/calibration/_pjm_h8_offer_ladder.json`.

---

## 1. RESULT

> **pjm-h6 and pjm-h7 adjudicated a BID parameter against a COST measurement.** The CAMPD
> `avg_committed_p50` 0.916 that both sessions treated as the committed band's true value is a
> measured *operating heat rate* — what a coal unit BURNS at min load. The band is a **bid** by
> its own declaration. **PJM publishes the bid**, the repo already carries it derived, and this
> keeper already prices coal's upper bands with it — but the mechanism that does so **excludes
> the min-load block by construction**, and no session in this chain has read it there.
>
> Measured against PJM's own offers at each row's own within-plant capacity share, all three
> measured years:
>
> | band | MW | 2023 | 2024 | 2025 | governed by the measured surface? |
> |---|---:|---:|---:|---:|:--|
> | **mustrun** | **14,062** | **0.180** | **0.207** | **0.205** | **NO — excluded** |
> | **committed** | **12,550** | **0.721** | **0.774** | **0.792** | **NO — excluded** |
> | econ | 20,643 | 0.934 | 1.016 | 1.035 | YES |
> | peak | 992 | 0.984 | 1.065 | 1.078 | YES |
>
> *(model bid ÷ measured offer, implied gas heat rate)*
>
> **Both excluded bands are un-governed; the DISPATCH-relevant one is `committed`.**
> `mustrun` carries the larger *price* gap — 12 % more MW, 4× further from PJM's offers, 3.4×
> the footprint — and no session in the h-chain has looked at it. **But see the CORRECTION in
> §2a: it is 84-86 % floored by `min_gen`, so most of that gap is inert to dispatch.** The
> band that actually moves energy is `committed`, at **0.7-3.1 %** floored.

## 2. THE FOOTPRINT — why the two spent screens could not have closed this

Mean $-MW of the model-vs-measured-offer gap, 2023-2025:

| band | mean gap $-MW | |
|---|---:|:--|
| **mustrun** | **269,727** | never examined |
| committed | 79,845 | pjm-h6 + pjm-h7 spent here |
| econ | 3,164 | governed |
| peak | −1,378 | governed |

For scale, **the entire pjm-h6 arm was 221,584 $-MW** (+17.6561 $/MWh × 12,550 MW). The
untouched band's gap is **22 % larger than the whole arm that was screened twice.**

### 2a. CORRECTION TO THIS DOCUMENT, measured after it was first written

**Most of the `mustrun` footprint is INERT, and the first version of §1-§2 overstated what it
buys.** Measured from the keeper's own `min_gen` array (2023 / 2024 / 2025):

| band | floored share of available MWh |
|---|---:|
| COAL `mustrun` | **84.4 % / 86.2 % / 85.7 %** |
| COAL `committed` | **0.7 % / 3.1 % / 2.4 %** |

Energy forced by `min_gen` cannot leave dispatch however it is priced — repricing it is close
to adding a constant to the objective. So the 269,727 $-MW `mustrun` gap is roughly **84 %
inert**, and its effective share is ~44,180 $-MW. The **`committed` band is the dispatch-
relevant one**, essentially fully economic, and PJM's own offers size its correction at
**+6.72 $/MWh** against the **+17.66** pjm-h6 applied.

This **sharpens** the conclusion rather than weakening it: h6 had the right band and the right
direction and applied **2.32×** too much. It also makes a falsifiable prediction, which the
screen chartered in `docs/PRECOMMIT-pjm-h8-minload-measured-offer-2026-09-16.md` tests as its
gate **G-5**: the `mustrun` band carries 77 % of the arm's coal footprint but should produce
**less than 25 %** of its coal energy change. Stated here because a reader of §1-§2 alone
would otherwise carry the wrong object forward.

**And h6 overshot the band it did move, by a factor the offer data pins exactly.** PJM's own
offers put the `committed` gap at **+7.59 $/MWh** (2023). h6 applied **+17.6561** — **2.32×
the measured correction**. That is not a retrospective rationalisation: it predicts the sign,
the class and the rough size of h6's kill (COAL_BIT +2.13 → **−24.19** TWh, overshooting
*through* zero) from an artifact that was already committed before h6 ran.

Where the two screened values actually sit against PJM's own offers:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| registered **0.548** | 0.721 | 0.774 | 0.792 |
| pjm-h6 arm **0.916** | **1.205** | **1.294** | **1.324** |

**Neither is the offer basis. It lies between them** — the control is 21-28 % too cheap, the arm
21-32 % too dear. Two screens have bracketed a measurement that was on disk the whole time.

Taking the min-load region whole (`mustrun` + `committed` = **26,612 MW, 54 % of PJM's coal
fleet**): the model bids it at **$11.63/MWh** against a measured **$26.11** in 2023 — **44.5 %**
of the measured level, and 48.8 % / 50.6 % in 2024 / 2025. Total gap **385,579 $-MW**, i.e.
**1.74× the whole h6 arm**, of which h6 addressed the upper half and overshot it 2.3×.

## 3. WHY THIS IS A MEASUREMENT AND NOT A SIXTH PASS AT THE SAME SURFACE

The handoff's binding instruction was: do not propose a third variant of *"make coal's offer
curve cheaper/dearer somewhere"*. This is not one, on four counts, each checkable:

1. **The operand is PJM's own published offers, not a new number.**
   `data/raw/_validation-source/pjm_offer_midcurve_condbinned.json`, derived by
   `scripts/data/derive_pjm_offer_midcurve.py` from PJM DataMiner2's `energy_market_offers`
   feed — 36 month-files, 2023-2025, capacity-weighted medians, multipliers only (the prices
   carry a redistribution restriction). Frozen against residuals under rule 23
   `[R-FROZEN-DERIVE]`. **Nothing was swept and no value is proposed.**
2. **The keeper already trusts this artifact one tranche up.**
   `pjm_offer_midcurve_conditional: true`, `pjm_offer_midcurve_segments: ["LONG_RUN","CC_LIKE"]`
   is armed on `2026-09-11-pjm-d4-4-gasoutage`. Coal's `econ` and `peak` rows are already
   priced at this measured level. The finding is about the rows the same mechanism skips.
3. **The exclusion is explicit, in the mechanism's own docstring**
   (`src/market_sim/data/fleet/offer_surfaces.py`, `build_pjm_offer_midcurve_conditional_markup`):
   > *"Committed / must-run / sync tranches are never touched (their pricing is owned by the
   > coal take-or-pay/passthrough sigmoids and the commitment scaffolding)."*
   That sentence is the defect statement. The min-load block's price is owned by a **cost**
   construction (take-or-pay: the fuel is already bought, so marginal cost ≈ VOM) inside a
   model whose every other coal band bids a **measured offer**.
4. **The comparison uses the model's OWN targeting code.** The probe calls
   `_pjm_midcurve_context` and `_pjm_midcurve_row_target` directly, so the "measured" column is
   byte-for-byte the target the armed mechanism would apply if the row were in scope — not a
   construction this probe invented.

**Sigmoid-invariant, so the whole pjm-170 / pjm-h7 dispute is out of scope here.** The
bituminous passthrough multiplies every coal band by the same hourly scalar, so it cancels in a
within-unit comparison. Nothing below depends on `gas_mid` being 3.40, 4.58 or 7.08.

## 4. THE CONTROLS — including the one that could have manufactured this

**(a) The ST_GAS / CC_REGULAR admixture control.** The measured `LONG_RUN` segment is coal PLUS
gas-steam, and gas-steam bids dearer, so a coal-only comparison against a blended ladder is
biased high. If that admixture were producing the result, it would bias every share of the
segment the same way — it cannot bend two bands and leave two at ~1.0. Measured separately
(2023): **ST_GAS** committed **1.217**, econ 1.336, peak 1.689; **CC_REGULAR** committed
**1.237**, econ 1.314, peak 3.126. **Both sit ABOVE their measured offers in the excluded
committed band.** The gap is not "excluded bands are cheap" — **only coal's are.**

**(b) The raise-only-floor control.** The mechanism is a floor, so it can only guarantee a
governed band is *not below* measured. That is exactly what holds: across all four classes and
three years, **no `LONG_RUN`/`CC_LIKE` band in the armed scope sits materially below measured.**
CT_PEAKER reads 0.34-0.52 — and `CT_FAST` is deliberately **outside** the armed scope (rule 19,
the fast-start rows are owned by the startup amortization), which is the predicted reading, not
an anomaly.

**(c) The share-mapping validity check.** The measured ladder returns each unit's **first offer
block** at low shares — confirmed by the step-function signature in the artifact itself
(2023 bin0 reads 7.875 / 7.875 / 7.825 at shares 0.05 / 0.15 / 0.25, i.e. one breakpoint
serving all three). That first block is the correct comparator for the model's min-load
tranches, and it means PJM's coal units price their whole min-load region as **one** block
where the model splits it into two at $4.52 and $19.59.

**(d) The forcing control (rule 19 `[R-ONE-MECH]` D-2 attribution — item 1 of the handoff, answered).**
Every mechanism touching PJM coal, from the keeper's own committed `legitimacy_diagnostics.json`
(2023, class total 113.5256 TWh):

| mechanism | forced TWh | share of class |
|---|---:|---:|
| `coal_mustrun` | 4.3000 | 3.79 % |
| `reliability_floor` | 0.2083 | 0.18 % |
| `chp_steam` | 0.0296 | 0.03 % |
| **total forced** | **4.538** | **4.00 %** |

**96 % of PJM's coal generation is economic dispatch.** There is no fourth mechanism and no
hidden floor: the enumeration is complete and it is small. So the ~22 TWh cannot be another
floor — **it is the offer curve, and specifically the 26.6 GW of it that no measured artifact
governs.** The `mustrun` BAND is 14,062 MW but the `coal_mustrun` MECHANISM forces only
3.79 % of coal's output, so that band is overwhelmingly **economic capacity priced at 18-21 %
of what PJM's coal fleet actually offers there** — not forced energy.

## 5. THE C8 LATENT CONDITION IS **NOT** LIVE — de-chartered by measurement

The handoff routed a third open item: *"PJM's designated keeper REGENERATED AT HEAD fails D-4
more than the arm did (38 vs 35) and re-scores CALIBRATED → NOT-YET / C8 FAIL."* That was
measured by `pjm-fuelvintage-1` (2026-09-09, `docs/RESULT-pjm-fuelvintage-2026-09-09.md` §8c)
against the **then-incumbent** keeper `2026-08-15-pjm-162-inputclock`.

**It does not apply to the designated keeper, which was promoted two days later.** Measured this
session at HEAD:

* `results/calibration/pjm_d4_4_A/legitimacy_diagnostics.json` was generated by the **HEAD-era**
  generator — D-4 carries **197 rows** (the old generator produced ~12), so the keeper is
  already scored under the generator that produced the condition.
* `scripts/calibration_verdict.py --run-id 2026-09-11-pjm-d4-4-gasoutage` → **CALIBRATED**,
  **C8 PASS**, 8/8, zero caveats, `determination basis: all criteria pass, governance attested`.

The condition was real on the run it was measured on and is **closed by supersession**, not by
argument. **No charter is needed.** The touchpoint `2026-09-11-pjm-holdout-gasoutage-touchpoint`
(2020-2022) reads NOT-YET with C8 **PASS** and a ledgered C3c — and under rule 30(c) a held-out
year never touches PJM's determination, so PJM's headline stands at **CALIBRATED**.

## 6. WHAT THIS DOES **NOT** ADJUDICATE — read before proposing anything

* **No arm is proposed and none is screened.** This is a rule 29 clause-0 measurement. It kills
  nothing and promotes nothing.
* **It does not vindicate 0.548**, and it does not revive 0.916. It says both are off the
  measured offer basis in opposite directions, which is a *third* statement, not a vote for
  either. Reverting anything remains refused under rule 14 `[R-ACCURATE]`.
* **It does not price the min-load block.** The obvious successor — extending the armed measured
  surface to the excluded tranches — is a real candidate but it is **NOT free**, and three
  things must be settled before it is a charter, not after:
  1. **Rule 19 `[R-ONE-MECH]`**: those rows are currently owned by the coal take-or-pay
     construction. A measured surface there must **REPLACE** it (the existing `level_segments`
     form), never stack — and replacing take-or-pay is a substantive claim about PJM coal
     contracting that needs its own argument, not just a scope flag.
  2. **It needs one new `ScenarioConfig` field** (the analogue of the existing
     `pjm_offer_midcurve_peak_segments` scope-extension precedent), hence a cache-key
     registration and a matrix row in the same PR (rule 28 (c), rule 24 `[R-REGISTRY]`).
  3. **It sits inside the owner-declared-closed pjm-142 frontier**, whose re-opening condition
     is *"a NEW defect or a NEW measured identification with its own charter"*. §1-§4 are
     offered as that identification. **The ruling is the owner's** — see §8.
* **The measured artifact covers 2023-2025 only.** PJM's registered span is six years
  (2020-2025, rule 35 `[R-PROMOTE]` (c)); 2020-2022 would read the surface's pooled fallback and
  were deliberately not run here.
* **`mc_base` is the P0 array.** The mid-curve mechanism is P1-only, so the `econ`/`peak` rows
  are shown BEFORE it prices them — which is why they already read ≈1.0 and why only the
  excluded rows carry a gap that survives into P1. Stated, not buried.

## 7. TWO REPO DEFECTS — DISCHARGED, not rediscovered

* **Rule 31 `[R-RETAIN]`'s parity-gate claim was FALSE and is now CORRECTED in `CLAUDE.md`.**
  The rule read *"the parity gate only ever sees committed dirs"*;
  `check_registry_payload_parity.py:437` sweeps `calib_root.iterdir()`, a **filesystem** walk, so
  a gitignored bundle in a working tree turns the gate RED locally while CI stays green. Verified
  at the line, corrected in place with the incident cited. The rule's substance is untouched —
  `.gitignore` still discharges the duty and `rm` is still never required — but a lane must not
  "fix" that local RED by deleting a result rule 31 protects.
* **The fixed-output-path clobber is pre-empted in this session's probe.** `_pjm_h8_offer_ladder.py`
  merges its `years` block into any prior artifact rather than overwriting, the same pattern
  pjm-h7 installed after hitting it.

## 8. THE OWNER QUESTIONS — asked, not pre-empted

1. **The pjm-h7 joint arm's promotion is still UNDECIDED and is carried forward unchanged.**
   Bundle retrievable at `claude/pjm-h7-screen-2023` sha
   `9be0e032e8f3832779b70472ae93813d63e2229a` (17 files, per-plant layer included). It is a
   ONE-YEAR SCREEN bundle, so it cannot be registered as-is (rules 16/29/34); a promotion means a
   fresh SIX-year span solve, ~90-105 min. **This session deleted nothing and touched that branch
   not at all.** h7's own recommendation was DO NOT PROMOTE; §2 here is new evidence *for* that
   recommendation (the arm overshoots PJM's own offers by 21-32 %), not against it.
2. **`gas_mid` → 4.58 as a STANDALONE rule-14 accuracy repair remains unchartered** (h7 §4/§5).
   Untouched here and still needing its own charter, its own footprint-named screen year and an
   owner ruling. **§3's sigmoid-invariance means this finding neither supports nor weakens it.**
3. **NEW: does the pjm-142 frontier re-open for the min-load offer basis?** §1-§4 are offered as
   the "NEW measured identification with its own charter" the frontier's own closure note
   requires. If it opens, the charter owes a rule-19 replacement argument against take-or-pay
   (§6), one registered field, and a footprint-named screen year — **which on this evidence is
   2023** (the largest min-load gap footprint, 385,579 $-MW), pre-registered here before any solve.

## 9. MATRIX (rule 28 `[R-MECH-MATRIX]` (b))

No mechanism was tested, so no cell verdict moves. The `pjm_offer_midcurve_conditional` and
`committed_band_measured_basis` cells in `docs/codebase-site/data/mechanism-matrix/PJM.js` carry
this document as evidence: the `committed_band_measured_basis` **R** verdict stands, with its
premise now measured to have been a **cost** basis, and the un-governed min-load tranches
recorded as the named open object.

## 10. RULES

Rule 1 `[R-STRUCT]` (a measurement, not a selection; no residual chose anything and no value is
proposed) · rule 13 `[R-MEASURED]` (the operand is PJM's own published offers, a formulaic input
with a forward analogue) · rule 14 `[R-ACCURATE]` (§6 — nothing is reverted; the accurate input
is preferred and the gap is opened as a root cause) · rule 19 `[R-ONE-MECH]` (§4d the complete
D-2 enumeration; §6 the replacement duty any successor owes) · rule 21 `[R-DOF]` (zero free
parameters, zero swept values, zero proposed) · rule 23 `[R-FROZEN-DERIVE]` (the measured surface
is frozen; this session re-derived nothing) · rule 24 `[R-REGISTRY]` (§6 the field a successor
would owe) · rule 25 `[R-ISO-SCOPE]` (PJM's own offers, PJM's own fleet; nothing transfers) ·
rule 28 `[R-MECH-MATRIX]` (§9) · rule 29 `[R-SCREEN]` (clause 0 — this whole document; the screen
year is pre-registered in §8.3 against a footprint, never a residual) · rule 30(c) (§5 — the
held-out touchpoint does not touch PJM's determination) · rule 31 `[R-RETAIN]` (§7, §8.1 — nothing
deleted, the open promotion carried forward) · rule 32 `[R-SHARD]` (a) (the parent ran no LP, and
no shard was needed because nothing here requires one).
