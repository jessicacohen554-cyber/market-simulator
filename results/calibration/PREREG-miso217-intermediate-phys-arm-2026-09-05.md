# PREREG miso-217 — THE `phys_*` COVERAGE-GAP ARM: one MISO-gated, zero-DOF `ScenarioConfig` field giving the three intermediate-duty offer curves their PARENT class's already-frozen `phys_econ_*` keys, econ-only, all three cohorts; ONE single-delta A/B against the keeper itself (2026-09-05)

**Pushed BLIND** — before any adjudicating statistic of this session, before the field exists,
and before the scorer runs. Keeper at open `2026-09-05-miso-213-layering` (bundle
`results/calibration/miso213_layering_B`), **NOT-YET on C3a-2025 alone (−11.747 %)**, C3c
ledgered 3/3, C6 attested 41/2. Branch `claude/miso-217-intermediate-phys-arm` from
`origin/main` **`32427f82`**, which contains the miso-215 and miso-216 work. Rule 22
`[R-HOLDOUT]`: **2023–2025 only**. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, **plus one cell
line in EVERY shard** because this session **does** add a `ScenarioConfig` field (rule 28c).

---

## 1. The object, carried in as STATED FACT (F-1 … F-5, not re-measured)

`gas_offer_net_revenue_margin` is armed on the MISO keeper (matrix cell `K`) and
structurally cannot reach the three intermediate-duty cohorts:
`pipeline/backcast_config._neutralize_generic_gas_bands` names exactly five gas classes
(`CC_REGULAR`, `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`) and `_MISO_OFFER_CURVE`
deep-merges `phys_*` onto those same five, so `CT_INTERMEDIATE`, `CC_INTERMEDIATE` and
`ST_GAS_INTERMEDIATE` carry no `phys_*` keys, `offer_curves.gas_offer_margin_markup_mult`
returns its documented rule-24 neutral **0.0**, and `apply_gas_offer_margin` skips them.
**38,501.0 MW = 58.4 % of MISO's assembled gas capacity**, identically in all three years.

* **(F-1) K-a PASSES.** One MISO-gated boolean, default False, **zero free parameters**: it
  merges the parent class's ALREADY-REGISTERED, ALREADY-FROZEN `phys_econ_low` /
  `phys_econ_high` onto the intermediate curve. No new number is minted.
* **(F-2) K-b PASSES 9 of 9 cohort-years.** Each cohort's own measured marginal-HR
  multiplier lands within **0.0344 / 0.0388 / 0.0149** of the borrowed parent midpoint
  against a ±0.06 bar, on 94–100 % of each cohort's capacity (miso-215 §3). The pooled class
  p50 IS the cohort's own physics.
* **(F-3) THE ANCHOR PREREQUISITE IS DISCHARGED.** miso-216: no grain dominates on both L1
  and L2, **87.8–99.5 %** of the distortion is irreducible by any scalar anchor, and the
  registered 3.0492 is within **0.25–1.24 %** of the best scalar that exists on `CT_PEAKER`
  and `ST_GAS` in 2023–2024. Recommendation was NO CHANGE and, absent an owner ruling, that
  is this lane's working assumption. **The anchor grain is not re-opened.**
* **(F-4) THE FORM CARRIES A FOOTPRINT AND THIS ARM EXTENDS IT — a known COST, stated
  here, not a discovery afterwards.** The fixed-margin form's cap-weighted mean absolute
  deviation from the registered multiplier form is **$21.55 / 15.64 / 15.76 per MWh** on
  `CT_PEAKER` — **24–30 % of that class's own $70.65 / 57.97 / 66.04 offer**. The markup this
  arm installs on `CT_INTERMEDIATE` is **4.6574**, LARGER than `CT_PEAKER`'s econ-band
  3.9059, so the same footprint extends to **9.3 GW more capacity**.
* **(F-5) DIRECTION IS YEAR-DEPENDENT AND MOSTLY ADVERSE.** Econ-only static reach at the
  registered anchor: `CT_INTERMEDIATE` **−1.475 / −5.285 / +1.457** TWh, `CC_INTERMEDIATE`
  **+0.458 / +0.029 / +0.900**, `ST_GAS_INTERMEDIATE` **−0.702 / −1.350 / +0.506**.
  **This PREREG predicts NO C1 or C3a improvement and makes no such claim anywhere.**

## 2. SCOPE, decided and defended BEFORE any measurement

**BAND SCOPE: ECON-ONLY. Pre-committed, and held.** Only `phys_econ_low` and
`phys_econ_high` are merged. No `phys_committed`, no `phys_peak`. Reason, measured at
miso-215 §5: the peak leg is inert on the static screen but **not** on price —
`CT_INTERMEDIATE`'s peak 3.00 against a borrowed `phys_peak` 1.00 is a **$73.4/MWh** fixed
margin replacing a fuel-scaled wall and **LOWERS** the cohort's peak offer by
**$29.03 / 8.69 / 23.81**, `ST_GAS_INTERMEDIATE`'s by **$38.96 / −4.25 / 10.23**. C3c is
already ledgered 3/3; lowering a deliberate scarcity wall by $24–29/MWh in the two years the
tail is already the single ledgered caveat is a caveat-budget risk that must not ride along
with a form repair. (`CC_INTERMEDIATE`'s peak 2.25 equals `CC_REGULAR`'s `phys_peak` 2.25 and
would clip to 0 anyway.) The committed band is likewise excluded: `CT_INTERMEDIATE`'s
committed 1.00 sits **below** `CT_PEAKER`'s `phys_committed` 1.025 and would clip to 0, and
`ST_GAS_INTERMEDIATE`'s 1.00 below `ST_GAS`'s 1.079 — so including it would be inert on two
of three cohorts and would silently move only `CC_INTERMEDIATE`. One band family, one
decision.

**COHORT SCOPE: ALL THREE, under ONE field.** Reasons, in order:
1. **The defect is single.** Three curves lack the same keys for one reason — one list names
   five classes and the per-ISO merge follows it. The code's own seam is one function
   (`_offer_curve_for_group`), and the fix is one merge at that seam.
2. **Rule 24 `[R-REGISTRY]` favours the smallest registry surface.** A per-cohort flag trio
   would invent three knobs where the code has one seam, and each would be a tuning channel
   in spirit.
3. **Rule 1 `[R-STRUCT]`.** A CC-only arm is nearly inert (markup 0.4938, a $1.51/MWh margin,
   screen reach +0.03 to +0.90 TWh) and would leave the defect standing on exactly the two
   classes where the mechanism actually bites. Omitting CT and ST **because** they are where
   the residual moves is a fit-preserving choice dressed as caution, and this PREREG refuses
   it in advance.

**THE ARGUMENT AGAINST THIS SCOPE, stated now so it cannot be invented later.** The three
cohorts are not equally well served by one decision: `CC_INTERMEDIATE` is 64.6 % of the
uncovered capacity but carries a markup of only 0.4938 against `CT_INTERMEDIATE`'s 4.6574 and
`ST_GAS_INTERMEDIATE`'s 2.4517, so one field bundles a near-inert correction with two that
carry the full F-4 footprint. A reader who weights F-4 heavily should prefer CC-only. **If
the A/B fails on a protective gate, the finding must report whether a CC-only variant would
have passed — and must NOT then quietly re-scope to it without a fresh prereg** (that would
be selecting scope on the residual, which rule 1 forbids).

## 3. Rule 1 `[R-STRUCT]`, pre-committed both ways

**Closing the gap is structurally right in FORM**, and this PREREG asserts it before the
numbers: there is no market reason for an intermediate-duty gas unit's offer to be fully
fuel-scaled while the same technology's peaking curve is decomposed into measured physics
plus a margin. `_MISO_OFFER_CURVE`'s own comment already accepts that reading for
`CT_PEAKER`'s neutral 1.0 econ bands ("*the neutral 1.0 econ bands decompose to the measured
flat-to-falling marginal (0.687/0.691) + a fixed margin*"), and the cohorts are the same
units physically — the duty split only routes them to a flatter band curve.

* **AN ADVERSE RESIDUAL IS NOT GROUNDS TO REJECT THIS ARM.** C1 moving away from actual, or
  C3a widening, is pre-registered as EXPECTED (F-5) and will be reported at full magnitude
  and **never argued**.
* **WHAT IS GROUNDS TO REJECT IT** — the pre-registered kills of §5: a protective-gate
  regression (a C1 band exit, a C8 failure of rule 20's conditional route, a C3c
  caveat-budget breach, a determination-class worsening), an instrument failure (S-2), or the
  F-4 footprint judged unacceptable on its own terms in §6's explicit test.

## 4. What will be built and how (design frozen here)

* **Field:** `miso_intermediate_gas_offer_margin` — one `ScenarioConfig` boolean, default
  **False**, MISO-gated.
* **Seam, pre-registered:** `data/offer_curves._offer_curve_for_group`. That function is read
  at **fleet-assembly time** (`data/fleet/assembly.py` computes
  `_margin_markup_hr = base_hr * gas_offer_margin_markup_mult(suffix, tr_hr/base_hr, offer)`
  from exactly the dict it returns), so both the CLI and the `replay_keeper` path see it.
  A config-BUILD-time merge would **NOT** fire under a replay, because `--set` rides the
  generic `prb_overrides` channel applied AFTER `backcast_config` merges the per-ISO curves.
* **It must return a COPY.** The function today returns the config's own dict by reference;
  merging in place would mutate `config.offer_curve_by_group` and leak into the recorded
  config and every later read.
* **Gate on `iso == "MISO"` AND the flag** (rule 25 — the same gap exists in kind at PJM and
  CAISO and is their lanes' `U`, never filled from here).
* **Values:** the PARENT class's own registered `phys_econ_low` / `phys_econ_high` only —
  `CT_PEAKER` → `CT_INTERMEDIATE`, `CC_REGULAR` → `CC_INTERMEDIATE`, `ST_GAS` →
  `ST_GAS_INTERMEDIATE`. Nothing is computed, nothing is minted.
* **Tests:** flag-off byte identity of the resolved curve **and** of the assembled
  `offer_markup_hr`; the merged dict is a copy (the config's own dict is unmutated); the
  algebraic identity at `fuel == anchor`; and a rule-25 test that a non-MISO ISO is
  unaffected with the flag on.
* **Matrix:** base row in `docs/codebase-site/data/mechanism-matrix.js` **plus a cell line in
  every one of the six shards** (rule 28c);
  `scripts/check_mechanism_matrix.py` must pass.
* **Solve:** `scripts/replay_keeper.py results/calibration/miso213_layering_B --set
  miso_intermediate_gas_offer_margin=true --out-dir
  results/calibration/miso217_intermphys_B`, years **2023 2024 2025 sequential in ONE
  invocation** (rules 12, 16). **CONTROL is the keeper bundle itself** — S-0 inherited, not
  re-solved.
* **Scorer** on the `_miso213_ab_gates.py` pattern, **committed BEFORE the solve**.

## 5. Gates and kills, pre-registered with their bands

**S-0** control identity inherited from the keeper bundle (not re-solved).
**S-1** exactly one field differs over the RECORDED `scenario_config` blocks; any field new
on `main` since the keeper solved must sit at its default.
**S-2 LIVENESS** — `offer_markup_hr > 0` on the three cohorts' econ tranches in the arm and
`== 0` in the control, and byte identity at flag-off.

Kills. **Any one fires ⇒ NOT promoted**, and the finding says so without renegotiation:

* **K-1 — C1 BAND EXIT.** Any class-year inside ±8.00 in the control that exits it in the
  arm. **The named face: `CC_REGULAR`-2024 at +7.419, 0.58 TWh of headroom.** The static
  screen is **BLIND to cross-class backfill** — CT displaced into CC is exactly the mechanism
  that would consume that headroom and the instrument cannot see it, so this is an
  **UN-INSTRUMENTED RISK**, declared here before the solve.
* **K-2 — C8.** `CT_PEAKER`-2023 forced share is already **0.2044** against the **0.15**
  peaker budget and passes only on rule 20's conditional provenance+shape route. Less
  merchant CT econ energy RAISES it. **Kill if the conditional route stops clearing** — i.e.
  the D-4 off-window binding check fails for a mechanism forcing the class, or D-1's
  `profile_r` / `cv_ratio` gates fail. A rise that still clears both is **not** a kill; it is
  reported.
* **K-3 — C3c / CAVEAT BUDGET.** C3c is the single ledgered caveat (3/3). Kill if the caveat
  budget is breached (>1 ledgered, or >0 protective caveats).
* **K-4 — DETERMINATION CLASS.** Kill if the determination worsens in class — NOT-YET on any
  criterion beyond `{C3a-2025}`.
* **K-5 — INSTRUMENT.** Kill if S-2 fails: no markup appears on the cohorts' econ tranches,
  or flag-off is not byte-identical, or S-1 shows more than one field differing.
* **K-6 — ANY OTHER PASS→FAIL FLIP** on a scored criterion not already covered above.

**Explicitly NOT a kill** (rule 1): a C1 or C3a residual that moves away from actual while
staying in band; a C8 rise that still clears rule 20's conditional route; the F-4 footprint
per se, which is adjudicated in §6 rather than by a threshold.

## 6. The F-4 footprint test — the one judgement this session must make explicitly

The arm extends a form whose measured deviation from the registered multiplier form is
24–30 % of `CT_PEAKER`'s offer, at a **larger** markup (4.6574) on 9.3 GW more capacity.
That is a structural cost, not a gate. The finding must state, on the record:

1. the arm's own measured footprint on each cohort (cap-weighted mean absolute deviation,
   $/MWh, and as a share of the cohort's own offer), computed by the miso-216 instrument;
2. whether that footprint is **larger** than the one already accepted on `CT_PEAKER`; and
3. an explicit verdict — is extending it justified by the consistency gain, or does it
   argue for routing the FORM question to the owner **before** arming?

**Pre-committed disposition:** if the arm's footprint on `CT_INTERMEDIATE` exceeds
`CT_PEAKER`'s **as a share of the cohort's own offer** by more than **5 percentage points**,
this session does **not** promote even on clean gates, and routes the form question to the
owner instead. Below that, consistency governs and the gates decide.

## 7. My prior, stated before the measurement (scored in the finding, against interest)

* **P-1 (S-2 liveness).** Exactly **534** tranches gain `offer_markup_hr > 0` — 264
  `CT_INTERMEDIATE` + 234 `CC_INTERMEDIATE` + 36 `ST_GAS_INTERMEDIATE` econ tranches
  (miso-215's own counts), every one of them positive because each cohort's registered econ
  bands sit strictly above its parent's `phys_econ_*`. The one thing that could reduce it is
  the `ov is None` per-plant tranche-sheet bypass in `assembly.py`, which no cohort plant is
  expected to hit. **Bar: 534 exactly; any shortfall is attributed to `ov` and reported.**
* **P-2 (LP vs the screen bound).** The LP's own class-energy change is **smaller in
  magnitude** than the static screen's cohort reach — the screen runs 1.41–1.43× the LP.
  **Bar: |LP Δ| ≤ 0.75 × |screen Δ| for `CT_PEAKER` in ≥ 2 of 3 years**, and the LP's
  `CT_PEAKER` sign matches the screen's (−, −, +) in **≥ 2 of 3 years**.
* **P-3 (C1, the named risk).** `CC_REGULAR`-2024 lands in **[+7.2, +8.0]** and does **not**
  exit the band. I am predicting the un-instrumented backfill is small relative to 0.58 TWh
  of headroom; if it exits, K-1 fires and the prediction is WRONG.
* **P-4 (C8).** `CT_PEAKER`-2023 forced share RISES into **[0.21, 0.26]** and rule 20's
  conditional route **still clears** (D-4 window pass, D-1 gates pass), so C8 reads PASS with
  the rise reported.
* **P-5 (C3a — reported, never argued).** |ΔC3a-2025| **< 0.5 pp**, because C3a-2025 is
  measured (miso-202/203) to be entirely a missing scarcity tail in the evening net-load ramp
  — 13 of 15 scarce hours in h18–h21 — which no offer-form change on these cohorts reaches.
  |ΔC3a-2023| and |ΔC3a-2024| **< 1.5 pp**.
* **P-6 (F-4).** The arm's footprint on `CT_INTERMEDIATE`, as a share of that cohort's own
  offer, comes in **within ±5 pp of `CT_PEAKER`'s 24–30 %** — i.e. §6's disposition does
  **not** fire, and the decision falls to the gates.
* **P-7 (promotion).** **P(promote) = 0.40.** The arm is structurally right and zero-DOF; the
  live risks are K-1 (backfill into a 0.58 TWh headroom the instrument cannot see) and K-2
  (a C8 route already over budget).

## 8. Standing constraints this lane must not violate

* **The miso-214 standing result stands.** 62–70 % of the CT energy the model misses was
  produced by the real market **below the plant's own delivered cost, at the market's own
  price** — **not reachable by any offer or price mechanism**. This arm addresses at most
  **bucket C** (0.167 / 0.257 / 0.167 of the missed MWh) and part of **bucket A** (0.131 /
  0.130 / 0.215). **No CT C1 movement from this family may be presented as closing the
  class's gap**, and the finding will say so.
* **C3a-2025 is an evening net-load-ramp scarcity-tail object** (miso-202/203). This lane
  does not claim to reach it.
* **DO-NOT-REDO:** `gas_hub_basis_overlay` (R), `miso_offer_level_dispersion` (R),
  `miso_offer_spread_anchored` (I), `miso_rdt_measured_limit` (R),
  `miso_south_gas_delivered_cost_basis` (R), `gas_offer_margin_zonal_anchor` (I — the ZONAL
  grain), `zonal_gas_basis` (K), `measured_offer_surface` (R). **CLOSED BY MEASUREMENT:** the
  CT commitment-bridge / min-load AS family (miso-214); the intermediate-cohort `phys_*`
  borrowing and the dual-fuel oil confound (miso-215); **the anchor's BASIS/CLASS grain
  (miso-216)**; any capability-removal lever keyed to heat or peak load (miso-203).
* **OWNER-COURT, not armed:** the average-vs-marginal delivered-cost convention (miso-212
  §8); the D-2 5(i) seam-response object; and the F-4 FORM question (miso-216) — which §6 may
  route but must not decide.
* **STILL OPEN, the alternative head if this arm is refused:** the South PRICE separation
  (miso-213 O-4 / the miso-211 D-3 object, +$0.16 model vs +$58 measured).
* **Rule 25:** PJM and CAISO carry the same `*_INTERMEDIATE` gap in kind, and miso-216
  counted 5 of 6 ISOs basis-grain exposed. Their cells enter as **`U`** with the new row and
  no verdict here fills them.

## 9. What ends the session

Either (i) every kill silent and §6's disposition not firing ⇒ **promote**, re-key the §5.4
header and the MISO.js keeper/gates stamps, `keeper_store --set` / `build_status --iso MISO`
/ `audit_keepers --iso MISO`, and run the `calibration-keeper-auditor` agent; or (ii) a kill
fires or §6 fires ⇒ **not promoted**, both runs still registered on the dashboard (rule 15),
and the finding reports the refusal at full magnitude. **Either way**: both runs registered,
`FINDING-miso217-…md`, the `docs/calibration-log/miso.md` entry, the §5.4 queue stamp, the
matrix base row + six cell lines, and the miso-218 handoff.

Next shorthand: **miso-217**.
